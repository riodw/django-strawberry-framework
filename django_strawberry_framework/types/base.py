"""``DjangoType`` — Meta-class-driven Django-model-to-Strawberry-type adapter.

Consumer surface::

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = "__all__"

A nested ``Meta`` class declares the model and (optionally) ``fields``,
``exclude``, ``name``, ``description``, ``optimizer_hints``, and
``interfaces``. Subclassing
triggers the collection pipeline, which:

1. Detects whether the subclass declares its own ``Meta``. Intermediate
   abstract subclasses without ``Meta`` are skipped so consumers can
   layer their own bases on top of ``DjangoType``.
2. Validates ``Meta`` (required Django model class, supported option
   shapes, ``fields``/``exclude`` exclusivity, deferred-key rejection,
   relation-only optimizer hints, and interfaces).
3. Selects Django fields and builds a ``DjangoTypeDefinition``.
4. Synthesizes scalar annotations and records unresolved relations as
   pending records.
5. Registers the model/type pair for a later ``finalize_django_types()``
   pass.
"""

import re
import typing
from collections.abc import Mapping, Sequence
from typing import Annotated, Any, ClassVar

from django.db import models
from strawberry import relay
from strawberry.relay.types import NodeIDPrivate
from strawberry.types.field import StrawberryField

from ..exceptions import ConfigurationError
from ..optimizer.field_meta import FieldMeta
from ..optimizer.hints import OptimizerHint
from ..registry import registry
from ..utils.strings import snake_case
from .converters import convert_scalar
from .definition import DjangoTypeDefinition
from .relations import PendingRelation, PendingRelationAnnotation
from .relay import install_is_type_of

DEFERRED_META_KEYS: frozenset[str] = frozenset(
    {
        "filterset_class",
        "orderset_class",
        "aggregate_class",
        "fields_class",
        "search_fields",
    },
)

ALLOWED_META_KEYS: frozenset[str] = frozenset(
    {
        "model",
        "fields",
        "exclude",
        "name",
        "description",
        "optimizer_hints",
        "interfaces",
        "primary",
    },
)


_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")


def _has_node_id_marker(hint: object) -> bool:
    """Return True when ``hint`` is ``Annotated[T, NodeIDPrivate()]``.

    In the installed Strawberry, ``relay.NodeID[T]`` IS
    ``typing.Annotated[T, NodeIDPrivate()]`` — the explicit ``Annotated``
    form and the ``relay.NodeID`` sugar collapse to the same shape, so
    ``typing.get_origin`` returns ``typing.Annotated`` for both and the
    ``NodeIDPrivate`` instance lives in ``typing.get_args(...)``'s
    metadata slot.
    """
    return typing.get_origin(hint) is Annotated and any(
        isinstance(arg, NodeIDPrivate) for arg in typing.get_args(hint)
    )


def _id_annotation_is_relay_node_id(cls: type) -> bool:
    r"""Return True when ``cls.__annotations__['id']`` resolves to ``relay.NodeID[...]``.

    Uses ``typing.get_type_hints(cls, include_extras=True)`` so
    stringified annotations (``from __future__ import annotations`` or
    explicit string annotations like ``id: "relay.NodeID[int]"``)
    evaluate against the consumer's module globals; ``include_extras``
    preserves the ``Annotated[T, NodeIDPrivate]`` marker.

    Fail-soft: ``typing.get_type_hints`` evaluates every annotation on
    ``cls`` and walks the MRO. A single unresolved string annotation
    anywhere on the class trips ``NameError``/``AttributeError`` even
    when ``id`` itself resolves cleanly. Two fail-soft sub-cases:

    1. ``id`` itself failed to resolve. ``cls.__annotations__["id"]``
       is the raw string the consumer wrote. Accept only when the
       string matches ``(?:^|\.)NodeID\[`` — qualified
       (``"relay.NodeID[int]"``) and unqualified (``"NodeID[int]"``)
       forms pass; prefixed-substring lookalikes (``"NotNodeID[int]"``,
       ``"MyNodeID[int]"``) and non-NodeID typos
       (``"MissingType"``) are rejected.
    2. Some other annotation tripped the exception but ``id`` is
       directly resolved. ``cls.__annotations__["id"]`` is the
       ``Annotated[int, NodeIDPrivate]`` object, not a string; fall
       back to ``_has_node_id_marker(raw)`` on the resolved object.
    """
    try:
        hints = typing.get_type_hints(cls, include_extras=True)
    except (NameError, AttributeError):
        raw = cls.__annotations__.get("id")
        if isinstance(raw, str):
            return bool(_NODEID_STRING_RE.search(raw))
        return _has_node_id_marker(raw)
    id_hint = hints.get("id")
    if id_hint is None:
        return False
    return _has_node_id_marker(id_hint)


def _is_relay_shaped(cls: type, interfaces: tuple[type, ...]) -> bool:
    """Return True when ``cls`` or any entry in ``interfaces`` is a Relay-Node-shaped type.

    Single source of truth for the predicate that drives both the H1
    Relay ``id`` collision guard at ``DjangoType.__init_subclass__`` and
    the synthesized-``id``-annotation suppression branch in
    ``_build_annotations``. Both call sites compute the same boolean
    from the same inputs at different timings (class-creation-time vs.
    annotation-synthesis-time); centralizing the predicate keeps the
    Relay-shape contract single-sited.
    """
    return any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)


class DjangoType:
    """Base class for Django-model-backed Strawberry GraphQL types."""

    _is_default_get_queryset: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Collect model/type metadata without finalizing the Strawberry type."""
        super().__init_subclass__(**kwargs)
        has_custom_get_queryset = _detect_custom_get_queryset(cls)
        cls._is_default_get_queryset = not has_custom_get_queryset
        meta = cls.__dict__.get("Meta")
        if meta is None:
            return
        if registry.is_finalized():
            raise ConfigurationError(
                f"finalize_django_types() already ran; cannot register {cls.__name__} "
                "after finalization. Call registry.clear() first if this is a test.",
            )
        interfaces = _validate_meta(meta)
        fields = _select_fields(meta)
        _validate_optimizer_hints(meta, fields)

        field_map = {snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}
        optimizer_hints = _meta_optimizer_hints(meta)
        primary = getattr(meta, "primary", False)
        consumer_annotations = dict(getattr(cls, "__annotations__", {}))
        consumer_annotated_relation_fields = frozenset(
            field.name for field in fields if field.is_relation and field.name in consumer_annotations
        )
        consumer_annotated_scalar_fields = frozenset(
            field.name for field in fields if not field.is_relation and field.name in consumer_annotations
        )
        consumer_assigned_relation_fields, consumer_assigned_scalar_fields = _consumer_assigned_fields(
            cls.__dict__,
            fields,
        )
        consumer_authored_fields = frozenset(
            {
                *consumer_annotated_relation_fields,
                *consumer_annotated_scalar_fields,
                *consumer_assigned_relation_fields,
                *consumer_assigned_scalar_fields,
            },
        )
        relay_shaped = _is_relay_shaped(cls, interfaces)
        if relay_shaped:
            has_id_assignment = isinstance(cls.__dict__.get("id"), StrawberryField)
            has_id_annotation = "id" in cls.__annotations__
            if has_id_assignment:
                raise ConfigurationError(
                    f"{cls.__name__}: cannot override the id field on a "
                    "relay.Node-shaped type with an assigned strawberry.field. "
                    "Use @classmethod resolve_id for a custom id resolver, "
                    "id: relay.NodeID[<pk_type>] for a custom id annotation, "
                    "or declare a resolver-backed sibling field — e.g., "
                    "`@strawberry.field(description=...) def display_id(self) -> "
                    "strawberry.ID: return str(self.pk)` — if you only need "
                    "GraphQL field-level metadata on a custom identifier "
                    "(a metadata-only sibling without a resolver builds but "
                    "fails at query time); "
                    "or remove relay.Node from Meta.interfaces.",
                )
            if has_id_annotation and not _id_annotation_is_relay_node_id(cls):
                raise ConfigurationError(
                    f"{cls.__name__}: cannot override the id field on a "
                    "relay.Node-shaped type without using strawberry.relay.NodeID[...]. "
                    "The Relay interface supplies id: GlobalID! — declare the id "
                    "field via relay.NodeID[<pk_type>] if you need a different id "
                    "shape, or remove relay.Node from Meta.interfaces.",
                )
        synthesized, pending = _build_annotations(
            cls,
            fields,
            source_model=meta.model,
            field_map=field_map,
            consumer_authored_fields=consumer_authored_fields,
            interfaces=interfaces,
        )
        definition = DjangoTypeDefinition(
            origin=cls,
            model=meta.model,
            name=getattr(meta, "name", None),
            description=getattr(meta, "description", None),
            fields_spec=_normalize_fields_spec(getattr(meta, "fields", None)),
            exclude_spec=_normalize_sequence_spec(getattr(meta, "exclude", None)),
            selected_fields=tuple(fields),
            field_map=field_map,
            optimizer_hints=optimizer_hints,
            has_custom_get_queryset=has_custom_get_queryset,
            consumer_authored_fields=consumer_authored_fields,
            consumer_annotated_relation_fields=consumer_annotated_relation_fields,
            consumer_annotated_scalar_fields=consumer_annotated_scalar_fields,
            consumer_assigned_relation_fields=consumer_assigned_relation_fields,
            consumer_assigned_scalar_fields=consumer_assigned_scalar_fields,
            interfaces=interfaces,
            primary=primary,
        )
        registry.register_with_definition(meta.model, cls, definition, primary=primary)
        for pending_relation in pending:
            registry.add_pending_relation(pending_relation)
        cls.__annotations__ = {**synthesized, **consumer_annotations}
        cls.__django_strawberry_definition__ = definition
        install_is_type_of(cls)

    @classmethod
    def get_queryset(
        cls,
        queryset: models.QuerySet,
        info: Any,
        **kwargs: Any,
    ) -> models.QuerySet:
        """Default identity hook.

        Subclasses override this to scope visibility (permissions,
        multi-tenancy, soft-delete). The optimizer detects overrides via
        ``has_custom_get_queryset`` and downgrades ``select_related`` to
        ``Prefetch`` so visibility filters apply across joins.
        """
        return queryset

    @classmethod
    def has_custom_get_queryset(cls) -> bool:
        """Return ``True`` if this subclass (or any intermediate base) overrides ``get_queryset``.

        Used by ``DjangoOptimizerExtension`` to decide whether a related-
        field traversal should be downgraded to a ``Prefetch``.

        Implementation: ``__init_subclass__`` flips
        ``_is_default_get_queryset`` to ``False`` at class-creation time
        when the subclass declares its own ``get_queryset``; this method
        returns the negated flag for a constant-time attribute read.
        Inheritance walks naturally — a subclass without its own
        ``get_queryset`` whose parent declared one inherits the parent's
        ``False`` sentinel through the class hierarchy.
        """
        definition = getattr(cls, "__django_strawberry_definition__", None)
        if definition is None:
            return not cls._is_default_get_queryset
        return definition.has_custom_get_queryset


def _detect_custom_get_queryset(cls: type) -> bool:
    """Return whether ``cls`` or an intermediate base overrides ``get_queryset``."""
    for base in cls.__mro__:
        if base is DjangoType:
            return False
        if "get_queryset" in base.__dict__:
            return True
    return False


def _normalize_fields_spec(value: Any) -> tuple[str, ...] | str | None:
    """Normalize ``Meta.fields`` for storage on ``DjangoTypeDefinition``."""
    if value is None or value == "__all__":
        return value
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ConfigurationError("Meta.fields must be '__all__' or a non-string sequence of field names")
    return tuple(value)


def _normalize_sequence_spec(value: Any) -> tuple[str, ...] | None:
    """Normalize optional sequence specs for storage on ``DjangoTypeDefinition``."""
    if value is None:
        return None
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ConfigurationError("Meta.exclude must be a non-string sequence of field names")
    return tuple(value)


def _consumer_assigned_fields(
    class_dict: dict[str, Any],
    fields: tuple[Any, ...],
) -> tuple[frozenset[str], frozenset[str]]:
    """Return (relation, scalar) names assigned to explicit Strawberry field objects.

    One of four collection sites that together pin the consumer-override
    contract for ``DjangoType``. The four corners are:

    - **relation × annotation** — ``consumer_annotated_relation_fields``,
      collected at ``DjangoType.__init_subclass__`` by walking
      ``cls.__annotations__`` for names that match a selected relation
      field. Honours a consumer-written ``items: list["AdminItemType"]``-
      style annotation.
    - **relation × assigned** — ``consumer_assigned_relation_fields``,
      this function's first return value. Honours a consumer-written
      ``items = strawberry.field(resolver=...)`` assignment on a relation
      column.
    - **scalar × annotation** — ``consumer_annotated_scalar_fields``,
      collected in the same ``__init_subclass__`` walk. Honours a
      consumer-written ``description: int``-style annotation override on
      a scalar column.
    - **scalar × assigned** — ``consumer_assigned_scalar_fields``, this
      function's second return value. Honours a consumer-written
      ``description = strawberry.field(resolver=...)`` assignment on a
      scalar column.

    The four sets are stored on ``DjangoTypeDefinition`` as the
    introspection surface. Their union, ``consumer_authored_fields``, is
    the single short-circuit input that ``_build_annotations`` reads at
    its relation branch and its scalar branch to skip auto-synthesis for
    any name the consumer authored.

    Walks every selected Django field, not just relations. A consumer
    who writes ``name = strawberry.field(resolver=...)`` on a scalar
    column gets the same treatment as the relation case: their
    Strawberry field object is preserved and ``_build_annotations``
    skips synthesizing an annotation for that name. Any non-
    ``StrawberryField`` shadow of a Django field name raises the same
    ``ConfigurationError`` shape so the failure mode is consistent
    across scalar and relation columns.
    """
    relation_assigned: set[str] = set()
    scalar_assigned: set[str] = set()
    for field in fields:
        if field.name not in class_dict:
            continue
        value = class_dict[field.name]
        if isinstance(value, StrawberryField):
            if field.is_relation:
                relation_assigned.add(field.name)
            else:
                scalar_assigned.add(field.name)
            continue
        kind = "relation" if field.is_relation else "scalar"
        raise ConfigurationError(
            f"{field.model.__name__}.{field.name} shadows a Django {kind} field with an unsupported "
            "class attribute. Use a type annotation for type overrides, or use "
            "strawberry.field(resolver=...) / @strawberry.field for resolver overrides.",
        )
    return frozenset(relation_assigned), frozenset(scalar_assigned)


def _meta_optimizer_hints(meta: type) -> dict[str, Any]:
    """Return ``meta.optimizer_hints`` as a dict, or ``{}`` when unset.

    Centralizes the shape guard used across ``__init_subclass__`` and the
    validators so non-mapping declarations fail before hint keys or
    values are inspected.
    """
    value = getattr(meta, "optimizer_hints", None)
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.optimizer_hints must be a mapping of field names to OptimizerHint "
            f"instances, got {type(value).__name__}.",
        )
    return dict(value)


def _format_unknown_fields_error(*, model: type, attr: str, unknown: list[str], available: set[str]) -> str:
    """Return the standard "unknown fields … Available: …" error message.

    Used by every validator that points at a typo in ``Meta.fields``,
    ``Meta.exclude``, or ``Meta.optimizer_hints``.  Centralizing the
    format keeps the consumer-visible error shape consistent across
    typo-guard sites.
    """
    return f"{model.__name__}.Meta.{attr} names unknown fields: {unknown}. Available: {sorted(available)}."


_INTERFACES_SHAPE_ERROR_LEAD_IN = (
    "Meta.interfaces must be a tuple/list of Strawberry interface classes or a single interface class"
)


def _interfaces_shape_error(meta: type, got_suffix: str) -> str:
    """Format the top-level ``Meta.interfaces`` shape-rejection message.

    Both raise sites (string-typed raw, other non-sequence raw) share the
    long lead-in defined in ``_INTERFACES_SHAPE_ERROR_LEAD_IN``; this
    helper localizes the wording so the two sites cannot drift.
    """
    return f"{meta.model.__name__}.{_INTERFACES_SHAPE_ERROR_LEAD_IN}, got {got_suffix}."


def _validate_interfaces(meta: type) -> tuple[type, ...]:
    """Validate and normalize ``Meta.interfaces`` per Decision 4.

    Returns a normalized ``tuple[type, ...]`` ready to pass through to
    ``DjangoTypeDefinition.interfaces``. Returns ``()`` when the key is
    absent or set to an empty tuple/list (Decision 4 line 324).

    Validation rules (spec lines 322-330):

    - Accepts a tuple/list of interface classes, or a single real
      Strawberry interface class (e.g. ``interfaces = relay.Node``).
    - Rejects strings, sets, generators, dicts, ints, and other
      non-sequence values.
    - Each entry must satisfy
      ``hasattr(entry, "__strawberry_definition__") and
      entry.__strawberry_definition__.is_interface``.
    - Rejects string entries (no lazy/forward-reference lookup).
    - Rejects ``DjangoType`` self-reference and other ``DjangoType``
      subclasses.
    - Rejects duplicates.

    The composite-pk constraint and ``relay.Node`` MRO inspection live
    in Slice 4's Phase 2.5; this helper only validates the shape and
    contents of the ``Meta.interfaces`` tuple itself.
    """
    raw = getattr(meta, "interfaces", None)
    if raw is None:
        return ()
    if isinstance(raw, str):
        raise ConfigurationError(_interfaces_shape_error(meta, "a string"))
    if isinstance(raw, type):
        entries: tuple[type, ...] = (raw,)
    elif isinstance(raw, (tuple, list)):
        entries = tuple(raw)
    else:
        raise ConfigurationError(_interfaces_shape_error(meta, type(raw).__name__))
    if entries == ():
        return ()
    seen_ids: set[int] = set()
    duplicates: list[str] = []
    for entry in entries:
        if isinstance(entry, str):
            raise ConfigurationError(
                f"{meta.model.__name__}.Meta.interfaces must contain interface classes, "
                f"not strings (got {entry!r}). Lazy/forward-reference interface lookup is "
                "out of scope for 0.0.5.",
            )
        if not isinstance(entry, type):
            raise ConfigurationError(
                f"{meta.model.__name__}.Meta.interfaces must contain interface classes, got {entry!r}.",
            )
        if issubclass(entry, DjangoType):
            raise ConfigurationError(
                f"{meta.model.__name__}.Meta.interfaces may not contain DjangoType or "
                f"DjangoType subclasses (got {entry.__name__}). DjangoType is not a "
                "Strawberry interface.",
            )
        definition = getattr(entry, "__strawberry_definition__", None)
        if definition is None or not getattr(definition, "is_interface", False):
            raise ConfigurationError(
                f"{meta.model.__name__}.Meta.interfaces entry {entry.__name__} is not a "
                "Strawberry interface. Use @strawberry.interface or one of the "
                "strawberry.relay interface classes.",
            )
        entry_id = id(entry)
        if entry_id in seen_ids:
            duplicates.append(entry.__name__)
        else:
            seen_ids.add(entry_id)
    if duplicates:
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.interfaces contains duplicate entries: {sorted(duplicates)}.",
        )
    return entries


def _validate_meta(meta: type) -> tuple[type, ...]:
    """Validate a ``DjangoType`` subclass's nested ``Meta`` class.

    Validation order:

    1. ``Meta.model`` is required and must be a Django model class.
    2. ``fields`` and ``exclude`` are mutually exclusive.
    3. Any key in ``DEFERRED_META_KEYS`` raises with a clear message.
    4. Any non-dunder key on ``meta`` not in ``ALLOWED_META_KEYS |
       DEFERRED_META_KEYS`` raises (typo guard).
    5. ``fields``, ``exclude``, and ``optimizer_hints`` have supported
       declaration shapes before field selection or hint validation uses
       them.
    6. If ``Meta.interfaces`` is declared, validate it per
       ``_validate_interfaces`` (Decision 4) and return the normalized
       tuple.

    Returns:
        The normalized ``Meta.interfaces`` tuple, or ``()`` when the key
        is absent or empty. The caller threads this through to
        ``DjangoTypeDefinition.interfaces``.

    Raises:
        ConfigurationError: any of the above violations.
    """
    model = getattr(meta, "model", None)
    if model is None:
        raise ConfigurationError("Meta.model is required")
    if not isinstance(model, type) or not issubclass(model, models.Model):
        raise ConfigurationError("Meta.model must be a Django model class")

    declared = {k for k in meta.__dict__ if not k.startswith("_")}

    if "fields" in declared and "exclude" in declared:
        raise ConfigurationError("Meta.fields and Meta.exclude are mutually exclusive")

    primary = getattr(meta, "primary", False)
    if not isinstance(primary, bool):
        raise ConfigurationError("Meta.primary must be a bool")

    deferred = sorted(declared & DEFERRED_META_KEYS)
    if deferred:
        raise ConfigurationError(
            f"Meta keys not supported yet: {deferred}. The feature that owns them has not shipped.",
        )

    unknown = sorted(declared - ALLOWED_META_KEYS - DEFERRED_META_KEYS)
    if unknown:
        raise ConfigurationError(f"Unknown Meta keys: {unknown}")

    _normalize_fields_spec(getattr(meta, "fields", None))
    _normalize_sequence_spec(getattr(meta, "exclude", None))
    _meta_optimizer_hints(meta)

    return _validate_interfaces(meta)


def _validate_optimizer_hints(meta: type, fields: tuple[Any, ...]) -> None:
    """Validate ``Meta.optimizer_hints`` keys and values in one pass.

    Combines the field-surface and value checks in one place:

    1. Every hint key names a field on ``meta.model`` (typo guard).
    2. Every hint key is in the type's selected relation field set.
       Excluded fields and selected scalar fields would silently drop
       optimizer intent otherwise — the walker only reads hints after
       entering the relation branch.
    3. Every hint value is an ``OptimizerHint`` instance.

    Field-name error sites route through ``_format_unknown_fields_error``
    so the consumer-visible shape matches ``Meta.fields`` /
    ``Meta.exclude`` typo guards; value errors use a dedicated
    ``OptimizerHint`` message.
    """
    hints = _meta_optimizer_hints(meta)
    if not hints:
        return
    model = meta.model
    valid_field_names = {f.name for f in model._meta.get_fields()}
    selected_relation_names = {f.name for f in fields if f.is_relation}

    unknown_hint_fields = sorted(set(hints) - valid_field_names)
    if unknown_hint_fields:
        raise ConfigurationError(
            _format_unknown_fields_error(
                model=model,
                attr="optimizer_hints",
                unknown=unknown_hint_fields,
                available=valid_field_names,
            ),
        )
    excluded_hint_fields = sorted(set(hints) - selected_relation_names)
    if excluded_hint_fields:
        raise ConfigurationError(
            _format_unknown_fields_error(
                model=model,
                attr="optimizer_hints",
                unknown=excluded_hint_fields,
                available=selected_relation_names,
            ),
        )
    bad_values = sorted(k for k, v in hints.items() if not isinstance(v, OptimizerHint))
    if bad_values:
        raise ConfigurationError(
            f"optimizer_hints values must be OptimizerHint instances, "
            f"got non-OptimizerHint for: {bad_values}",
        )


def _select_fields(meta: type) -> tuple[Any, ...]:
    """Filter ``meta.model._meta.get_fields()`` per ``Meta.fields`` / ``Meta.exclude``.

    Called once from ``DjangoType.__init_subclass__`` and the resulting
    list is reused by ``_build_annotations`` (in this module) and
    ``_attach_relation_resolvers`` (in ``types.resolvers``) so the field
    walk does not happen twice. Iteration order follows
    Django's ``_meta.get_fields()`` so the generated GraphQL type's field
    order matches Django's declared order, with reverse-side relations
    appended at the end.

    Selection rules:

    - ``fields == "__all__"`` (or both ``fields``/``exclude`` unset) ->
      every concrete + relation field.
    - ``fields`` as a sequence -> only those names; unknown names raise.
    - ``exclude`` as a sequence -> every field except those names;
      unknown names raise.

    Raises:
        ConfigurationError: ``Meta.fields`` or ``Meta.exclude`` names a
            field that does not exist on ``Meta.model``. The error names
            the model, the unknown values, and the available field set
            so typos surface loudly instead of silently dropping.
    """
    model = meta.model
    fields_spec = _normalize_fields_spec(getattr(meta, "fields", None))
    exclude_spec = _normalize_sequence_spec(getattr(meta, "exclude", None))

    all_fields = list(model._meta.get_fields())
    all_names = [f.name for f in all_fields]
    valid_names = set(all_names)

    if fields_spec == "__all__" or (fields_spec is None and exclude_spec is None):
        selected_names = valid_names
    elif fields_spec is not None:
        unknown = sorted(set(fields_spec) - valid_names)
        if unknown:
            raise ConfigurationError(
                _format_unknown_fields_error(
                    model=model,
                    attr="fields",
                    unknown=unknown,
                    available=valid_names,
                ),
            )
        selected_names = set(fields_spec)
    else:
        unknown = sorted(set(exclude_spec) - valid_names)
        if unknown:
            raise ConfigurationError(
                _format_unknown_fields_error(
                    model=model,
                    attr="exclude",
                    unknown=unknown,
                    available=valid_names,
                ),
            )
        selected_names = valid_names - set(exclude_spec)

    return tuple(f for f in all_fields if f.name in selected_names)


def _build_annotations(
    cls: type,
    fields: tuple[Any, ...],
    *,
    source_model: type[models.Model],
    field_map: dict[str, FieldMeta],
    consumer_authored_fields: frozenset[str] = frozenset(),
    interfaces: tuple[type, ...] = (),
) -> tuple[dict[str, Any], list[PendingRelation]]:
    """Build the annotation dict the Strawberry type decorator consumes.

    Field-by-field dispatch: scalar entries in ``fields`` are routed
    through ``convert_scalar``. Auto-synthesized relation entries always
    record a ``PendingRelation`` and set the annotation to
    ``PendingRelationAnnotation``; ``finalize_django_types()`` resolves
    them through ``registry.get(...)`` after every type has registered
    so multi-type / primary semantics apply uniformly. Consumer-authored
    fields short-circuit out of the synthesis loop on both branches: a
    name in ``consumer_authored_fields`` skips relation deferral at the
    ``field.is_relation`` branch and skips ``convert_scalar`` at the
    scalar branch. See ``_consumer_assigned_fields`` for the four-corner
    override contract that populates ``consumer_authored_fields``. The
    caller pre-computes the field list with ``_select_fields(meta)`` so
    this function does not need ``meta``.

    When ``relay.Node`` appears in ``interfaces``, the primary-key field's
    synthesized scalar annotation is dropped from the returned dict so
    Strawberry's interface-supplied ``id: GlobalID!`` is not shadowed by a
    Django ``int`` field. The pk field stays in ``fields`` so the
    optimizer's ``DjangoTypeDefinition.field_map`` continues to see it as a
    connector column (spec Decision 7, line 361).

    Args:
        cls: The consumer-facing ``DjangoType`` subclass (its ``__name__``
            threads into ``convert_scalar`` so generated choice enums
            carry a stable name).
        fields: The Meta-filtered list of Django field objects.
        source_model: The Django model the type wraps. Used to resolve the
            primary-key attname when ``relay.Node`` suppression is active.
        consumer_authored_fields: Names of fields whose annotation /
            ``StrawberryField`` assignment is owned by the consumer. The
            synthesized annotation is skipped for these names so consumer
            overrides survive collection.
        interfaces: The validated ``Meta.interfaces`` tuple. When
            ``relay.Node`` is among them, the primary-key field's
            synthesized scalar annotation is suppressed so Strawberry's
            interface-supplied ``id: GlobalID!`` is not shadowed.

    Returns:
        A tuple of ``(annotations, pending_relations)``.

    Raises:
        ConfigurationError: an unsupported scalar field type is encountered
            (raised by ``convert_scalar``), or a selected relation has no
            concrete related model to map to a GraphQL type.
    """
    annotations: dict[str, Any] = {}
    pending: list[PendingRelation] = []
    # Suppress the synthesized scalar ``id`` annotation whenever the type will
    # participate in the Relay ``Node`` interface — either through
    # ``Meta.interfaces`` (the canonical path; includes both ``relay.Node``
    # directly and any ``@strawberry.interface`` that subclasses it) or
    # through direct inheritance (``class Foo(DjangoType, relay.Node)``).
    # Without these branches a Strawberry-native consumer would land in
    # Phase 3 ``strawberry.type(...)`` decoration with both the synthesized
    # ``id: int`` and the interface-supplied ``id: GlobalID!`` and the schema
    # build would blow up with ``NodeIDAnnotationError`` (review feedback
    # ``feedback.md`` § High "Direct relay.Node inheritance bypasses Relay
    # finalization" and § "Extended Node interfaces").
    #
    # The interfaces tuple is checked with ``issubclass`` per entry rather
    # than an exact ``relay.Node in interfaces`` membership test:
    # ``_validate_interfaces`` guarantees every entry is a Strawberry
    # interface class, and a consumer subclass like
    # ``@strawberry.interface class CustomNode(relay.Node)`` is the
    # canonical way to extend Relay-Node behavior.
    suppress_pk_annotation = _is_relay_shaped(cls, interfaces)
    # ``pk_name`` (not ``pk_attname``): ``_meta.pk.name`` is the Django
    # field NAME, not the column attname. For a relation primary key
    # (``OneToOneField(primary_key=True)``) those differ — ``name="user"``
    # vs. ``attname="user_id"`` — and the comparison below is against
    # ``field.name`` so the NAME is what's needed. Naming it ``pk_attname``
    # would invite a future maintainer to reuse it in a
    # ``getattr(root, pk_attname)`` context, which would lazy-load the
    # related row for a relation pk.
    pk_name = source_model._meta.pk.name if suppress_pk_annotation else None
    for field in fields:
        if field.is_relation:
            if field.name in consumer_authored_fields:
                continue
            field_meta = field_map[snake_case(field.name)]
            if getattr(field, "related_model", None) is None:
                raise ConfigurationError(
                    f"{source_model.__name__}.{field.name} is a GenericForeignKey or other "
                    "relation without a concrete related model. It cannot be auto-mapped to "
                    "a single GraphQL type. Exclude it via Meta.exclude, or supply an "
                    "explicit annotation or resolver.",
                )
            # Always defer auto-synthesized relation annotations: the
            # consumer_authored short-circuit above leaves consumer overrides
            # alone, and every other relation field becomes a pending record
            # that ``finalize_django_types()`` resolves through
            # ``registry.get(...)`` (which returns the primary post-finalize,
            # or the single registered type when no primary was declared).
            # The earlier eager-bind branch froze the relation against
            # whichever type was already registered at ``__init_subclass__``
            # time, which mis-bound when a secondary was registered before
            # the primary (the import-order trap closed by spec-014 H1).
            pending.append(_record_pending_relation(cls, source_model, field, field_meta))
            annotations[field.name] = PendingRelationAnnotation
        else:
            if field.name in consumer_authored_fields:
                # A consumer-assigned ``StrawberryField`` (or annotation) on a
                # scalar column wins over the auto-synthesized annotation so
                # ``strawberry.field(resolver=...)`` overrides survive
                # collection. Relation override symmetry: see the
                # ``field.is_relation`` branch above.
                continue
            if suppress_pk_annotation and field.name == pk_name:
                # ``relay.Node`` supplies ``id: GlobalID!`` via the interface;
                # dropping the synthesized scalar annotation here keeps the
                # Strawberry surface clean. The pk field stays in ``fields``
                # so the optimizer's field map still sees it as a connector
                # column (spec Decision 7, line 361).
                continue
            annotations[field.name] = convert_scalar(field, cls.__name__)
    return annotations, pending


def _record_pending_relation(
    cls: type,
    source_model: type[models.Model],
    field: Any,
    field_meta: FieldMeta,
) -> PendingRelation:
    """Build a pending relation record from a selected Django relation field."""
    return PendingRelation(
        source_type=cls,
        source_model=source_model,
        field_name=field.name,
        django_field=field,
        related_model=field.related_model,
        relation_kind=field_meta.relation_kind,
        nullable=field_meta.nullable,
    )
