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

from django.db import models

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
        # TODO(slice 2): _validate_meta(meta)
        # TODO(slice 2): annotations = _build_annotations(cls, meta)
        # TODO(slice 2): cls.__annotations__.update(annotations)
        # TODO(slice 2): registry.register(meta.model, cls)
        # TODO(slice 2): apply Meta.interfaces (e.g., relay.Node) when set.
        # TODO(slice 2): wrap with @strawberry.type carrying Meta.name and
        #                Meta.description.
        # TODO(slice 6): when ``"get_queryset"`` is present in
        # ``cls.__dict__``, flip ``cls._is_default_get_queryset`` to
        # False so ``has_custom_get_queryset`` collapses to a
        # constant-time attribute read.

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
        # TODO(slice 6): implement via the sentinel approach (see step 7
        # in __init_subclass__'s pipeline). Returns
        # ``not cls._is_default_get_queryset`` once the sentinel is wired.
        raise NotImplementedError("has_custom_get_queryset pending Slice 6")


def _validate_meta(meta: type) -> None:
    """Validate a ``DjangoType`` subclass's nested ``Meta`` class.

    Validation order:

    1. ``getattr(meta, "model", None) is None`` -> ``ConfigurationError``
       ("Meta.model is required").
    2. Both ``fields`` and ``exclude`` declared -> ``ConfigurationError``
       ("fields and exclude are mutually exclusive").
    3. For each key in ``DEFERRED_META_KEYS`` declared on ``meta``,
       ``ConfigurationError`` naming the key (e.g. "filterset_class is
       not supported yet; the FilterSet spec has not shipped").
    4. (Optional) For each non-dunder attribute on ``meta`` that is not
       in ``ALLOWED_META_KEYS | DEFERRED_META_KEYS``, raise
       ``ConfigurationError`` to fail fast on typos.

    Raises:
        ConfigurationError: any of the above violations.
    """
    # TODO(slice 2): implement the four-step validation above. Use the
    # ``DEFERRED_META_KEYS`` and ``ALLOWED_META_KEYS`` module constants
    # as the source of truth for accept / reject. Re-import
    # ``ConfigurationError`` from ``.exceptions`` once this body is wired.
    raise NotImplementedError("Meta validation pending Slice 2")


def _build_annotations(cls: type, meta: type) -> dict[str, Any]:
    """Build the annotation dict the Strawberry type decorator expects.

    Algorithm:

    1. Resolve the field list from ``Meta.fields`` (``"__all__"`` expands
       to every concrete field) or by subtracting ``Meta.exclude`` from
       the full set.
    2. Iterate ``meta.model._meta.get_fields()``, filter by the resolved
       list, and dispatch each field through:
       - ``converters.convert_scalar(field, cls.__name__)`` for scalar
         columns.
       - ``converters.convert_relation(field)`` for FK / OneToOne /
         reverse / M2M relations.
    3. Return a ``{field_name: synthesized_type}`` mapping suitable for
       merging into ``cls.__annotations__``.

    Args:
        cls: The consumer-facing ``DjangoType`` subclass (used for
            naming generated choice enums).
        meta: The validated ``Meta`` inner class.

    Returns:
        A dict suitable for ``cls.__annotations__.update(...)``.
    """
    # TODO(slice 2 + slice 3): implement scalar dispatch in slice 2,
    # extend with relation dispatch in slice 3. The ``"__all__"``
    # expansion must respect the model's concrete-field order so the
    # generated GraphQL type's field order is deterministic.
    raise NotImplementedError("Annotation synthesis pending Slice 2 / Slice 3")
