"""``DjangoType`` — Meta-class-driven Django-model-to-Strawberry-type adapter.

Consumer surface::

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = "__all__"

A nested ``Meta`` class declares the model and (optionally) ``fields``,
``exclude``, ``name``, and ``description``. Subclassing
triggers the ``__init_subclass__`` pipeline, which:

1. Detects whether the subclass declares its own ``Meta``. Intermediate
   abstract subclasses without ``Meta`` are skipped so consumers can
   layer their own bases on top of ``DjangoType``.
2. Validates ``Meta`` (required ``model``, ``fields``/``exclude``
   exclusivity, deferred-key rejection).
3. Synthesizes Strawberry annotations via ``converters.convert_scalar``
   and ``converters.convert_relation``.
4. Registers the resulting type with ``registry``.
5. Finalizes the class via ``@strawberry.type``.
"""

from typing import Any, ClassVar

import strawberry
from django.db import models

from ..exceptions import ConfigurationError
from ..registry import registry
from .converters import convert_relation, convert_scalar
from .resolvers import _attach_relation_resolvers

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
        # TODO(spec-optimizer_beyond.md B4): add "optimizer_hints" here
        # when the feature ships. Validation in ``_validate_meta`` should
        # reject unknown field names (same as ``fields``/``exclude``) and
        # validate hint values at schema-build time.
    },
)


class DjangoType:
    """Base class for Django-model-backed Strawberry GraphQL types."""

    # Sentinel so ``has_custom_get_queryset`` can detect overrides.
    _is_default_get_queryset: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate ``Meta`` and assemble the Strawberry type.

        Pipeline order:

        1. ``spec-optimizer.md`` O6 sentinel: if the subclass declares
           its own ``get_queryset``, flip ``cls._is_default_get_queryset``
           to ``False``. Runs **unconditionally** — before the
           ``meta is None`` early return — so an intermediate abstract
           base (no ``Meta``, but its own ``get_queryset``) still flips
           the flag, and any concrete subclass that inherits from such
           a base reports ``has_custom_get_queryset()`` correctly.
        2. Resolve ``cls.Meta``. If absent, skip the rest of the
           pipeline — intermediate abstract subclasses without ``Meta``
           are allowed.
        3. ``_validate_meta(meta)`` — raises ``ConfigurationError`` for
           missing model, ``fields``/``exclude`` collision, or any key
           in ``DEFERRED_META_KEYS``.
        4. ``_select_fields(meta)`` — produce the Meta-filtered Django
           field list once and reuse it for steps 5 and 8 below.
        5. ``_build_annotations(cls, fields)`` — synthesizes the
           ``{name: type}`` mapping by dispatching each field through
           ``converters.convert_scalar`` / ``converters.convert_relation``.
        6. ``cls.__annotations__ = {**synthesized, **existing}`` —
           installs the synthesized annotation map. Consumer-declared
           annotations are merged on top as an implementation detail,
           but ``@strawberry.type`` rewrites ``cls.__annotations__``
           from its own field metadata downstream, so the merge is
           **not** a reliable consumer-override contract in 0.0.3
           (see ``docs/spec-django_type_contract.md`` "Consumer
           override semantics" and the skipped
           ``test_consumer_annotation_overrides_synthesized``).
        7. ``registry.register(meta.model, cls)`` — claims the model.
        8. ``_attach_relation_resolvers(cls, fields)`` —
           ``spec-optimizer.md`` O1: attaches a cardinality-aware
           resolver per relation field (forward FK / OneToOne, reverse
           FK / M2M, reverse OneToOne) so Strawberry's default
           ``getattr`` resolver does not see a Django
           ``RelatedManager``. Lives in ``types.resolvers``; caller
           passes the pre-computed field list to keep the field walk
           single-pass and the dependency direction one-way
           (``base`` -> ``resolvers``, never the reverse).
        9. ``strawberry.type(cls)`` — finalizes the class as a
           Strawberry type with ``Meta.name`` and ``Meta.description``.
           (``Meta.interfaces`` is reserved by ``DEFERRED_META_KEYS``
           pending a future relay spec.)
        """
        super().__init_subclass__(**kwargs)
        # spec-optimizer.md O6 sentinel: flip the class-level flag if
        # *this* class declared its own ``get_queryset``. Runs
        # unconditionally — before the ``meta is None`` early return —
        # so an intermediate abstract base (no ``Meta``, but its own
        # ``get_queryset``) still flips the flag for any concrete
        # subclass that inherits from it. The optimizer's
        # downgrade-to-Prefetch rule consumes this once the rebuild
        # lands; the type-system half of the contract ships now.
        if "get_queryset" in cls.__dict__:
            cls._is_default_get_queryset = False
        meta = cls.__dict__.get("Meta")
        if meta is None:
            # Intermediate abstract subclasses (no ``Meta``) opt out of
            # the rest of the pipeline. Concrete consumer types must
            # declare ``Meta``.
            return
        _validate_meta(meta)
        # Compute the Meta-selected field list once and reuse it for both
        # annotation synthesis and resolver attachment so the field walk
        # is not duplicated and ``types.resolvers`` does not need to
        # import back into ``types.base``.
        fields = _select_fields(meta)
        # TODO(spec-optimizer_beyond.md B7): after _select_fields,
        # build ``cls._optimizer_field_map`` — a
        # ``dict[str, FieldMeta]`` precomputing is_relation,
        # cardinality, related_model, and attname per field. The O2
        # walker reads this instead of calling _meta.get_fields().
        synthesized = _build_annotations(cls, fields)
        # Implementation detail (NOT a stable consumer-override contract
        # in 0.0.3): consumer-declared annotations are merged on top of
        # the synthesized ones in the dict literal below, but
        # ``@strawberry.type`` rewrites ``cls.__annotations__`` from
        # its own field metadata downstream, so the merge does not
        # reliably preserve the override. Documented in
        # ``docs/spec-django_type_contract.md`` "Consumer override
        # semantics"; pinned by the skipped
        # ``test_consumer_annotation_overrides_synthesized``. The
        # eventual stable mechanism lives in a future
        # ``spec-consumer_overrides.md``.
        existing = dict(cls.__dict__.get("__annotations__", {}))
        cls.__annotations__ = {**synthesized, **existing}
        registry.register(meta.model, cls)
        # spec-optimizer.md O1: attach cardinality-aware resolvers per
        # relation field. Without this, Strawberry's default ``getattr``
        # resolver returns a Django ``RelatedManager`` for reverse rels
        # / M2M and Strawberry rejects with "Expected Iterable". Must
        # run before ``strawberry.type(cls)`` so the field metadata is
        # in place when Strawberry processes the class.
        _attach_relation_resolvers(cls, fields)
        # TODO(future relay spec): when relay support lands, the
        # implementation will inject ``Meta.interfaces`` (e.g.,
        # ``relay.Node``) into ``cls.__bases__`` before strawberry.type
        # processes the class, and ``"interfaces"`` will move from
        # ``DEFERRED_META_KEYS`` back into ``ALLOWED_META_KEYS``.
        # Until then the key is rejected by ``_validate_meta`` so it
        # cannot be set silently. Consumers wanting a Strawberry
        # interface today should subclass it directly:
        # ``class CategoryType(DjangoType, relay.Node): ...``.
        name = getattr(meta, "name", None)
        description = getattr(meta, "description", None)
        strawberry.type(cls, name=name, description=description)

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
        field traversal should be downgraded to a ``Prefetch`` (see the
        N+1 strategy section of the spec).

        Implementation: ``__init_subclass__`` flips
        ``_is_default_get_queryset`` to ``False`` at class-creation time
        when the subclass declares its own ``get_queryset``; this method
        returns the negated flag for a constant-time attribute read.
        Inheritance walks naturally — a subclass without its own
        ``get_queryset`` whose parent declared one inherits the parent's
        ``False`` sentinel through the class hierarchy.
        """
        return not cls._is_default_get_queryset


def _validate_meta(meta: type) -> None:
    """Validate a ``DjangoType`` subclass's nested ``Meta`` class.

    Validation order:

    1. ``Meta.model`` is required.
    2. ``fields`` and ``exclude`` are mutually exclusive.
    3. Any key in ``DEFERRED_META_KEYS`` raises with a clear message
       pointing at the spec that owns the feature.
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
            f"Meta keys not supported yet: {deferred}. The spec that owns them has not shipped.",
        )

    unknown = sorted(declared - ALLOWED_META_KEYS - DEFERRED_META_KEYS)
    if unknown:
        raise ConfigurationError(f"Unknown Meta keys: {unknown}")


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
                f"{model.__name__}.Meta.fields names unknown fields: {unknown}. "
                f"Available: {sorted(valid_names)}.",
            )
        selected_names = set(fields_spec)
    else:
        unknown = sorted(set(exclude_spec) - valid_names)
        if unknown:
            raise ConfigurationError(
                f"{model.__name__}.Meta.exclude names unknown fields: {unknown}. "
                f"Available: {sorted(valid_names)}.",
            )
        selected_names = valid_names - set(exclude_spec)

    return [f for f in all_fields if f.name in selected_names]


def _build_annotations(cls: type, fields: list[Any]) -> dict[str, Any]:
    """Build the annotation dict the Strawberry type decorator consumes.

    Field-by-field dispatch: every entry in ``fields`` is routed through
    ``convert_relation`` if ``field.is_relation`` is true, or
    ``convert_scalar`` otherwise. The caller pre-computes the list with
    ``_select_fields(meta)`` so this function does not need ``meta``.

    Args:
        cls: The consumer-facing ``DjangoType`` subclass (its ``__name__``
            threads into ``convert_scalar`` so generated choice enums
            (Slice 7) carry a stable name).
        fields: The Meta-filtered list of Django field objects.

    Returns:
        A dict suitable for ``cls.__annotations__.update(...)``.

    Raises:
        ConfigurationError: a relation field's target ``DjangoType`` is not
            yet registered (raised by ``convert_relation``); or an
            unsupported scalar field type is encountered (raised by
            ``convert_scalar``).
    """
    annotations: dict[str, Any] = {}
    for field in fields:
        if field.is_relation:
            annotations[field.name] = convert_relation(field)
        else:
            annotations[field.name] = convert_scalar(field, cls.__name__)
    return annotations
