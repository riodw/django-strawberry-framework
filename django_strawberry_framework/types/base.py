"""``DjangoType`` — Meta-class-driven Django-model-to-Strawberry-type adapter.

Consumer surface::

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = "__all__"

A nested ``Meta`` class declares the model and (optionally) ``fields``,
``exclude``, ``name``, and ``description``. Subclassing
triggers the collection pipeline, which:

1. Detects whether the subclass declares its own ``Meta``. Intermediate
   abstract subclasses without ``Meta`` are skipped so consumers can
   layer their own bases on top of ``DjangoType``.
2. Validates ``Meta`` (required ``model``, ``fields``/``exclude``
   exclusivity, deferred-key rejection).
3. Selects Django fields and builds a ``DjangoTypeDefinition``.
4. Synthesizes scalar annotations and records unresolved relations as
   pending records.
5. Registers the model/type pair for a later ``finalize_django_types()``
   pass.
"""

from typing import Any, ClassVar

from django.db import models
from strawberry.types.field import StrawberryField

from ..exceptions import ConfigurationError
from ..optimizer.field_meta import FieldMeta
from ..optimizer.hints import OptimizerHint
from ..registry import registry
from ..utils.relations import relation_kind
from ..utils.strings import snake_case
from .converters import convert_scalar, resolved_relation_annotation
from .definition import DjangoTypeDefinition
from .relations import PendingRelation, PendingRelationAnnotation

DEFERRED_META_KEYS: frozenset[str] = frozenset(
    {
        "filterset_class",
        "orderset_class",
        "aggregate_class",
        "fields_class",
        "search_fields",
        # ``interfaces`` is in the deferred set rather than the allowed
        # set because the relay-interface application pass
        # (``cls.__bases__`` injection before ``strawberry.type``) has
        # not landed yet. Accepting the key without applying it would
        # silently produce types that look interface-bearing but are
        # not, which is exactly the alpha posture we want to avoid.
        # TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
        # move ``interfaces`` to ALLOWED_META_KEYS only after validation,
        # storage, base injection, Relay resolver defaults, id suppression,
        # tests, docs, and the version bump all land.
        "interfaces",
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
    },
)


class DjangoType:
    """Base class for Django-model-backed Strawberry GraphQL types."""

    _is_default_get_queryset: ClassVar[bool] = True
    _optimizer_field_map: ClassVar[dict[str, FieldMeta]] = {}
    _optimizer_hints: ClassVar[dict[str, OptimizerHint]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Collect model/type metadata without finalizing the Strawberry type."""
        super().__init_subclass__(**kwargs)
        # TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
        # call ``types.relay.install_is_type_of(cls)`` here for every
        # DjangoType subclass while preserving consumer-declared ``is_type_of``.
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
        consumer_annotations = dict(getattr(cls, "__annotations__", {}))
        consumer_annotated_relation_fields = frozenset(
            field.name for field in fields if field.is_relation and field.name in consumer_annotations
        )
        consumer_assigned_relation_fields, consumer_assigned_scalar_fields = _consumer_assigned_fields(
            cls.__dict__,
            fields,
        )
        consumer_authored_fields = frozenset(
            {
                *consumer_annotated_relation_fields,
                *consumer_assigned_relation_fields,
                *consumer_assigned_scalar_fields,
            },
        )
        synthesized, pending = _build_annotations(
            cls,
            fields,
            source_model=meta.model,
            consumer_authored_fields=consumer_authored_fields,
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
            consumer_assigned_relation_fields=consumer_assigned_relation_fields,
            consumer_assigned_scalar_fields=consumer_assigned_scalar_fields,
            interfaces=interfaces,
        )
        registry.register_with_definition(meta.model, cls, definition)
        for pending_relation in pending:
            registry.add_pending_relation(pending_relation)
        cls.__annotations__ = {**synthesized, **consumer_annotations}
        cls.__django_strawberry_definition__ = definition
        # TODO(spec-fieldmeta-mirror-retirement): retire these class-attribute
        # mirrors; the optimizer should read ``DjangoTypeDefinition.field_map`` /
        # ``optimizer_hints`` directly. Reader sites in ``optimizer/walker.py``
        # and ``optimizer/field_meta.py`` carry the matching anchor.
        cls._optimizer_field_map = field_map
        cls._optimizer_hints = optimizer_hints

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
    return tuple(value)


def _normalize_sequence_spec(value: Any) -> tuple[str, ...] | None:
    """Normalize optional sequence specs for storage on ``DjangoTypeDefinition``."""
    if value is None:
        return None
    return tuple(value)


def _consumer_assigned_fields(
    class_dict: dict[str, Any],
    fields: tuple[Any, ...],
) -> tuple[frozenset[str], frozenset[str]]:
    """Return (relation, scalar) names assigned to explicit Strawberry field objects.

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
    """Return ``meta.optimizer_hints`` as a dict, or ``{}`` when unset/empty.

    Centralizes the ``getattr(meta, "optimizer_hints", None) or {}`` pattern
    used across ``__init_subclass__`` and the validators so the Meta key
    name only appears once at the read site.
    """
    return getattr(meta, "optimizer_hints", None) or {}


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

    1. ``Meta.model`` is required.
    2. ``fields`` and ``exclude`` are mutually exclusive.
    3. Any key in ``DEFERRED_META_KEYS`` raises with a clear message.
    4. Any non-dunder key on ``meta`` not in ``ALLOWED_META_KEYS |
       DEFERRED_META_KEYS`` raises (typo guard).
    5. If ``Meta.interfaces`` is declared, validate it per
       ``_validate_interfaces`` (Decision 4) and return the normalized
       tuple. The deferred-key check above runs first while
       ``"interfaces"`` remains in ``DEFERRED_META_KEYS``, so this step
       only executes end-to-end once Slice 5 promotes the key.

    Returns:
        The normalized ``Meta.interfaces`` tuple, or ``()`` when the key
        is absent or empty. The caller threads this through to
        ``DjangoTypeDefinition.interfaces``.

    Raises:
        ConfigurationError: any of the above violations.
    """
    if getattr(meta, "model", None) is None:
        raise ConfigurationError("Meta.model is required")

    declared = {k for k in meta.__dict__ if not k.startswith("_")}

    if "fields" in declared and "exclude" in declared:
        raise ConfigurationError("Meta.fields and Meta.exclude are mutually exclusive")

    deferred = sorted(declared & DEFERRED_META_KEYS)
    if deferred:
        raise ConfigurationError(
            f"Meta keys not supported yet: {deferred}. The feature that owns them has not shipped.",
        )

    unknown = sorted(declared - ALLOWED_META_KEYS - DEFERRED_META_KEYS)
    if unknown:
        raise ConfigurationError(f"Unknown Meta keys: {unknown}")

    return _validate_interfaces(meta)


def _validate_optimizer_hints(meta: type, fields: tuple[Any, ...]) -> None:
    """Validate ``Meta.optimizer_hints`` keys and values in one pass.

    Combines the three checks that previously lived in two helpers:

    1. Every hint key names a field on ``meta.model`` (typo guard).
    2. Every hint key is in the type's *selected* field set (excluded
       fields silently drop optimizer intent otherwise — the walker
       never visits them).
    3. Every hint value is an ``OptimizerHint`` instance.

    All three error sites route through ``_format_unknown_fields_error``
    so the consumer-visible shape is identical to ``Meta.fields`` /
    ``Meta.exclude`` typo guards.
    """
    hints = _meta_optimizer_hints(meta)
    if not hints:
        return
    model = meta.model
    valid_field_names = {f.name for f in model._meta.get_fields()}
    selected_names = {f.name for f in fields}

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
    excluded_hint_fields = sorted(set(hints) - selected_names)
    if excluded_hint_fields:
        raise ConfigurationError(
            _format_unknown_fields_error(
                model=model,
                attr="optimizer_hints",
                unknown=excluded_hint_fields,
                available=selected_names,
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
    fields_spec = getattr(meta, "fields", None)
    exclude_spec = getattr(meta, "exclude", None)

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
    consumer_authored_fields: frozenset[str] = frozenset(),
) -> tuple[dict[str, Any], list[PendingRelation]]:
    """Build the annotation dict the Strawberry type decorator consumes.

    Field-by-field dispatch: every entry in ``fields`` is routed through
    ``convert_relation`` if ``field.is_relation`` is true, or
    ``convert_scalar`` otherwise. The caller pre-computes the list with
    ``_select_fields(meta)`` so this function does not need ``meta``.

    Args:
        cls: The consumer-facing ``DjangoType`` subclass (its ``__name__``
            threads into ``convert_scalar`` so generated choice enums
            carry a stable name).
        fields: The Meta-filtered list of Django field objects.

    Returns:
        A tuple of ``(annotations, pending_relations)``.

    Raises:
        ConfigurationError: an unsupported scalar field type is encountered
            (raised by ``convert_scalar``), or a selected relation has no
            concrete related model to map to a GraphQL type.
    """
    annotations: dict[str, Any] = {}
    pending: list[PendingRelation] = []
    for field in fields:
        if field.is_relation:
            if field.name in consumer_authored_fields:
                continue
            if getattr(field, "related_model", None) is None:
                raise ConfigurationError(
                    f"{source_model.__name__}.{field.name} is a GenericForeignKey or other "
                    "relation without a concrete related model. It cannot be auto-mapped to "
                    "a single GraphQL type. Exclude it via Meta.exclude, or supply an "
                    "explicit annotation or resolver.",
                )
            target_type = registry.get(field.related_model)
            if target_type is None:
                pending.append(_record_pending_relation(cls, source_model, field))
                annotations[field.name] = PendingRelationAnnotation
            else:
                annotations[field.name] = resolved_relation_annotation(field, target_type)
        else:
            if field.name in consumer_authored_fields:
                # A consumer-assigned ``StrawberryField`` (or annotation) on a
                # scalar column wins over the auto-synthesized annotation so
                # ``strawberry.field(resolver=...)`` overrides survive
                # collection. Relation override symmetry: see the
                # ``field.is_relation`` branch above.
                continue
            # TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
            # when ``relay.Node`` is declared in ``Meta.interfaces``, suppress
            # the synthesized Django ``id`` annotation while preserving the pk
            # field in ``DjangoTypeDefinition.field_map`` for optimizer use.
            annotations[field.name] = convert_scalar(field, cls.__name__)
    return annotations, pending


def _record_pending_relation(
    cls: type,
    source_model: type[models.Model],
    field: Any,
) -> PendingRelation:
    """Build a pending relation record from a selected Django relation field."""
    # TODO(spec-fieldmeta-ssot): the ``nullable`` derivation inlines
    # ``kind == "reverse_one_to_one" or bool(getattr(field, "null",
    # False))`` instead of reading from a ``FieldMeta`` already built
    # for ``field`` at the call site. ``FieldMeta`` is the canonical
    # SSoT for relation shape — see ``optimizer/field_meta.py``
    # module docstring.
    kind = relation_kind(field)
    return PendingRelation(
        source_type=cls,
        source_model=source_model,
        field_name=field.name,
        django_field=field,
        related_model=field.related_model,
        relation_kind=kind,
        nullable=kind == "reverse_one_to_one" or bool(getattr(field, "null", False)),
    )
