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

        Pipeline order:

        1. Resolve ``cls.Meta``. If absent, skip — intermediate abstract
           subclasses without ``Meta`` are allowed.
        2. ``_validate_meta(meta)`` — raises ``ConfigurationError`` for
           missing model, ``fields``/``exclude`` collision, or any key
           in ``DEFERRED_META_KEYS``.
        3. ``_select_fields(meta)`` — produce the Meta-filtered Django
           field list once and reuse it for steps 4 and 6 below.
        4. ``_build_annotations(cls, fields)`` — synthesizes the
           ``{name: type}`` mapping by dispatching each field through
           ``converters.convert_scalar`` / ``converters.convert_relation``.
        5. ``cls.__annotations__ = {**synthesized, **existing}`` — merges
           synthesized annotations with any consumer-provided overrides.
        6. ``registry.register(meta.model, cls)`` — claims the model.
        7. ``_attach_relation_resolvers(cls, fields)`` — ``spec-optimizer.md``
           O1: attaches a cardinality-aware resolver per relation field
           (forward FK / OneToOne, reverse FK / M2M, reverse OneToOne)
           so Strawberry's default ``getattr`` resolver does not see a
           Django ``RelatedManager``. Lives in ``types.resolvers``;
           caller passes the pre-computed field list to keep the field
           walk single-pass and the dependency direction one-way
           (``base`` -> ``resolvers``, never the reverse).
        8. ``strawberry.type(cls)`` — finalizes the class as a Strawberry
           type with ``Meta.name`` / ``Meta.description`` /
           ``Meta.interfaces``.
        9. (TODO ``spec-optimizer.md`` O6) If the subclass defines its
           own ``get_queryset``, flip ``cls._is_default_get_queryset``
           to ``False`` so the optimizer can detect the override cheaply
           (see ``has_custom_get_queryset`` below).
        """
        super().__init_subclass__(**kwargs)
        meta = cls.__dict__.get("Meta")
        if meta is None:
            # Intermediate abstract subclasses (no ``Meta``) opt out of
            # the pipeline. Concrete consumer types must declare ``Meta``.
            return
        _validate_meta(meta)
        # Compute the Meta-selected field list once and reuse it for both
        # annotation synthesis and resolver attachment so the field walk
        # is not duplicated and ``types.resolvers`` does not need to
        # import back into ``types.base``.
        fields = _select_fields(meta)
        synthesized = _build_annotations(cls, fields)
        # Consumer-declared annotations override synthesized ones so a
        # subclass can opt out of the auto-generated type for any field
        # by re-annotating it (e.g. ``description: str = strawberry.field(...)``).
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
    - ``fields`` as a sequence -> only those names.
    - ``exclude`` as a sequence -> every field except those names.
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
