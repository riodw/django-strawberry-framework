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

from ..exceptions import ConfigurationError
from ..optimizer.field_meta import FieldMeta
from ..optimizer.hints import OptimizerHint
from ..registry import registry
from ..utils.relations import relation_kind
from ..utils.strings import snake_case
from .converters import convert_relation, convert_scalar
from .definition import DjangoTypeDefinition
from .relations import PendingRelation

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
        _validate_meta(meta)
        fields = _select_fields(meta)
        _validate_optimizer_hints_against_selected_fields(meta, fields)

        field_map = {snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}
        optimizer_hints = _meta_optimizer_hints(meta)
        consumer_annotations = dict(cls.__dict__.get("__annotations__", {}))
        consumer_authored_fields = frozenset(
            field.name
            for field in fields
            if field.is_relation
            and (
                field.name in consumer_annotations
                or _is_consumer_authored_class_attr(cls.__dict__, field.name)
            )
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
        )
        registry.register(meta.model, cls)
        registry.register_definition(cls, definition)
        for pending_relation in pending:
            registry.add_pending_relation(pending_relation)
        cls.__annotations__ = {**synthesized, **consumer_annotations}
        cls.__django_strawberry_definition__ = definition
        cls._optimizer_field_map = field_map
        cls._optimizer_hints = optimizer_hints
        cls._is_default_get_queryset = not has_custom_get_queryset

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


def _is_consumer_authored_class_attr(class_dict: dict[str, Any], field_name: str) -> bool:
    """Return whether ``field_name`` has a consumer-authored class attribute."""
    return field_name in class_dict


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


def _validate_meta(meta: type) -> None:
    """Validate a ``DjangoType`` subclass's nested ``Meta`` class.

    Validation order:

    1. ``Meta.model`` is required.
    2. ``fields`` and ``exclude`` are mutually exclusive.
    3. Any key in ``DEFERRED_META_KEYS`` raises with a clear message.
    4. Any non-dunder key on ``meta`` not in ``ALLOWED_META_KEYS |
       DEFERRED_META_KEYS`` raises (typo guard).

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

    # B4: validate optimizer_hints field names and value types.
    hints = _meta_optimizer_hints(meta)
    if hints:
        model = meta.model
        valid_field_names = {f.name for f in model._meta.get_fields()}
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
        bad_values = sorted(k for k, v in hints.items() if not isinstance(v, OptimizerHint))
        if bad_values:
            raise ConfigurationError(
                f"optimizer_hints values must be OptimizerHint instances, "
                f"got non-OptimizerHint for: {bad_values}",
            )


def _validate_optimizer_hints_against_selected_fields(meta: type, fields: list[Any]) -> None:
    """Reject ``optimizer_hints`` keys that are not in the type's selected fields.

    ``_validate_meta`` already checks that hint keys name real Django fields
    on ``meta.model``.  This second check catches the silent-dead-code
    case where the field is real but excluded from the GraphQL type via
    ``Meta.fields`` / ``Meta.exclude`` — the walker never visits it, so
    the consumer's optimization intent is lost.
    """
    hints = _meta_optimizer_hints(meta)
    if not hints:
        return
    selected_names = {f.name for f in fields}
    excluded_hint_fields = sorted(set(hints) - selected_names)
    if excluded_hint_fields:
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.optimizer_hints names fields not in the type's "
            f"selected fields: {excluded_hint_fields}.  Selected: {sorted(selected_names)}.",
        )


def _select_fields(meta: type) -> list[Any]:
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

    return [f for f in all_fields if f.name in selected_names]


def _build_annotations(
    cls: type,
    fields: list[Any],
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
            (raised by ``convert_scalar``).
    """
    annotations: dict[str, Any] = {}
    pending: list[PendingRelation] = []
    for field in fields:
        if field.is_relation:
            if field.name in consumer_authored_fields:
                continue
            if registry.get(field.related_model) is None:
                pending.append(_record_pending_relation(cls, source_model, field))
            annotations[field.name] = convert_relation(field)
        else:
            annotations[field.name] = convert_scalar(field, cls.__name__)
    return annotations, pending


def _record_pending_relation(
    cls: type,
    source_model: type[models.Model],
    field: Any,
) -> PendingRelation:
    """Build a pending relation record from a selected Django relation field."""
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
