"""``DjangoType`` — Meta-class-driven Django-model-to-Strawberry-type adapter.

Consumer surface::

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = "__all__"

A nested ``Meta`` class declares the model and (optionally) ``fields``,
``exclude``, ``interfaces``, ``name``, and ``description``. Subclassing
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

from .converters import convert_relation, convert_scalar
from .exceptions import ConfigurationError
from .registry import registry

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
        "interfaces",
    },
)


class DjangoType:
    """Base class for Django-model-backed Strawberry GraphQL types."""

    # Sentinel so ``has_custom_get_queryset`` can detect overrides.
    _is_default_get_queryset: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate ``Meta`` and assemble the Strawberry type.

        Pipeline order (each step is TODO-stubbed below so the seven
        slices land independently):

        1. Resolve ``cls.Meta``. If absent, skip — intermediate abstract
           subclasses without ``Meta`` are allowed.
        2. ``_validate_meta(meta)`` — raises ``ConfigurationError`` for
           missing model, ``fields``/``exclude`` collision, or any key
           in ``DEFERRED_META_KEYS``.
        3. ``_build_annotations(cls, meta)`` — synthesizes the
           ``{name: type}`` mapping by walking
           ``meta.model._meta.get_fields()`` and dispatching through
           ``converters.convert_scalar`` / ``converters.convert_relation``.
        4. ``cls.__annotations__.update(annotations)`` — merges synthesized
           annotations with any consumer-provided overrides.
        5. ``registry.register(meta.model, cls)`` — claims the model.
        6. ``strawberry.type(cls)`` — finalizes the class as a Strawberry
           type with ``Meta.name`` / ``Meta.description`` /
           ``Meta.interfaces``.
        7. If the subclass defines its own ``get_queryset``, flip
           ``cls._is_default_get_queryset`` to ``False`` so the optimizer
           can detect the override cheaply (see
           ``has_custom_get_queryset`` below).
        """
        super().__init_subclass__(**kwargs)
        meta = cls.__dict__.get("Meta")
        if meta is None:
            # Intermediate abstract subclasses (no ``Meta``) opt out of
            # the pipeline. Concrete consumer types must declare ``Meta``.
            return
        _validate_meta(meta)
        synthesized = _build_annotations(cls, meta)
        # Consumer-declared annotations override synthesized ones so a
        # subclass can opt out of the auto-generated type for any field
        # by re-annotating it (e.g. ``description: str = strawberry.field(...)``).
        existing = dict(cls.__dict__.get("__annotations__", {}))
        cls.__annotations__ = {**synthesized, **existing}
        registry.register(meta.model, cls)
        # TODO(spec-optimizer.md O1): generate one custom resolver per
        # relation field so Strawberry's default ``getattr(source,
        # attname)`` does not trip on Django's ``RelatedManager``.
        # Per-cardinality shape: forward FK / OneToOne -> ``getattr(source,
        # attname)``; reverse FK / reverse OneToOne / M2M -> return the
        # prefetch cache when present, else ``manager.all()``. Iterate
        # the same ``model._meta.get_fields()`` ``_build_annotations``
        # walked, find relation entries, and inject ``cls.<field_name>
        # = strawberry.field(resolver=...)`` before the
        # ``strawberry.type(...)`` call below. Without this, every
        # reverse rel raises "Expected Iterable" at GraphQL execution.
        # TODO(future): apply ``Meta.interfaces`` (e.g., ``relay.Node``)
        # by injecting them into ``cls.__bases__`` before strawberry.type
        # processes the class. For now consumers wanting a Strawberry
        # interface should subclass it directly:
        # ``class CategoryType(DjangoType, relay.Node): ...``.
        name = getattr(meta, "name", None)
        description = getattr(meta, "description", None)
        strawberry.type(cls, name=name, description=description)
        # TODO(spec-optimizer.md O6): when ``"get_queryset"`` is present
        # in ``cls.__dict__``, flip ``cls._is_default_get_queryset`` to
        # False so ``has_custom_get_queryset`` collapses to a
        # constant-time attribute read. The sentinel itself stays in
        # this file (it is type-system surface); the flip is wired here
        # because ``__init_subclass__`` is the only place that knows,
        # at class-creation time, whether the subclass declared its own
        # ``get_queryset``.

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
        """Return ``True`` if this subclass overrides ``get_queryset``.

        Used by ``DjangoOptimizerExtension`` to decide whether a related-
        field traversal should be downgraded to a ``Prefetch`` (see the
        N+1 strategy section of the spec).

        Detection options:

        - Compare ``cls.__dict__.get("get_queryset")`` against the base
          class's classmethod descriptor; any subclass that defines its
          own ``get_queryset`` ends up with a distinct descriptor in its
          own ``__dict__``.
        - Walk ``cls.__mro__`` until hitting ``DjangoType``; return
          ``True`` if any intermediate class declared ``get_queryset``.
        - Use the ``_is_default_get_queryset`` sentinel:
          ``__init_subclass__`` flips it to ``False`` when the subclass
          declares ``get_queryset``; this method just returns the
          negated flag. This is the planned approach because the check
          collapses to a constant-time attribute read.
        """
        # TODO(spec-optimizer.md O6): implement via the sentinel
        # approach (paired with the ``__init_subclass__`` flip above).
        # Returns ``not cls._is_default_get_queryset`` once the
        # sentinel flip is wired.
        raise NotImplementedError("has_custom_get_queryset pending spec-optimizer.md O6")


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


def _build_annotations(cls: type, meta: type) -> dict[str, Any]:
    """Build the annotation dict the Strawberry type decorator consumes.

    Field-by-field dispatch: every entry in ``model._meta.get_fields()`` is
    routed through ``convert_relation`` if ``field.is_relation`` is true,
    or ``convert_scalar`` otherwise. The Slice 2 "scalars only" filter has
    been removed; relations now appear in the synthesized annotations as
    long as the target's ``DjangoType`` is already registered.

    Field selection follows ``Meta.fields`` / ``Meta.exclude``:

    - ``fields == "__all__"`` (or both unset) -> every concrete + relation field.
    - ``fields`` as a sequence -> only those names.
    - ``exclude`` as a sequence -> everything except those names.

    Iteration order follows ``model._meta.get_fields()`` so the generated
    GraphQL type's field order matches Django's declared order with
    reverse-side relations appended at the end.

    Args:
        cls: The consumer-facing ``DjangoType`` subclass (its ``__name__``
            threads into ``convert_scalar`` so generated choice enums
            (Slice 7) carry a stable name).
        meta: The validated ``Meta`` inner class.

    Returns:
        A dict suitable for ``cls.__annotations__.update(...)``.

    Raises:
        ConfigurationError: a relation field's target ``DjangoType`` is not
            yet registered (raised by ``convert_relation``); or an
            unsupported scalar field type is encountered (raised by
            ``convert_scalar``).
    """
    model = meta.model
    fields_spec = getattr(meta, "fields", None)
    exclude_spec = getattr(meta, "exclude", None)

    all_fields = list(model._meta.get_fields())
    all_names = [f.name for f in all_fields]

    if fields_spec == "__all__" or (fields_spec is None and exclude_spec is None):
        selected_names = set(all_names)
    elif fields_spec is not None:
        selected_names = set(fields_spec)
    else:
        selected_names = set(all_names) - set(exclude_spec)

    annotations: dict[str, Any] = {}
    for field in all_fields:
        if field.name not in selected_names:
            continue
        if field.is_relation:
            annotations[field.name] = convert_relation(field)
        else:
            annotations[field.name] = convert_scalar(field, cls.__name__)
    return annotations
