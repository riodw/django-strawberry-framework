"""BFS factory for the ordering subsystem.

Layer 5 of the spec-028 six-layer pipeline (the BFS that builds every
reachable Strawberry input class via ``_build_input_fields`` +
``build_input_class`` from ``orders/inputs.py``). The factory consumes
resolved ``OrderSet.get_fields()`` results -- NOT a parallel
``OrderSet.Meta.fields`` map -- so the runtime order shape and the
GraphQL input shape stay downstream of one decision site (mirror of
``filters/factories.py``'s Layer 5 + Decision 4 H1).

The finalizer materializes the built classes as module globals at
finalize time; this module owns build-only. Layer 6 (dynamic
``OrderSet`` generation against a connection-field meta dict) is
deferred to ``0.0.9`` per spec-028 Decision 12; the forward-reserved
symbols ``_dynamic_orderset_cache`` and ``get_orderset_class`` are NOT
shipped in this slice (see the TODO anchor at the bottom of the file).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from ..exceptions import ConfigurationError
from .inputs import _build_input_fields, _input_type_name_for, build_input_class
from .sets import OrderSet

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from django.db import models  # noqa: F401 - kept for filter-side parity.


class OrderArgumentsFactory:
    """BFS-build every reachable Strawberry input class for an ``OrderSet``.

    Mirror of
    ``django_strawberry_framework/filters/factories.py::FilterArgumentsFactory``
    and of the cookbook's
    ``django_graphene_filters/order_arguments_factory.py::OrderArgumentsFactory``.
    Two class-level caches mirror both prior sources:

    - ``input_object_types: dict[str, type]`` -- class-name -> built input
      class. Shared across factory instances so repeated builds of the
      same orderset converge on the same input class.
    - ``_type_orderset_registry: dict[str, type]`` -- collision detection.
      The factory raises ``ConfigurationError`` when two distinct
      ordersets claim the same class-derived name.

    The factory does NOT materialize built classes as module globals;
    that is Slice 3's finalizer-phase-2.5 contract. The factory's
    ``arguments`` property returns the built input class for the root
    orderset (parallel to the filter side's
    ``FilterArgumentsFactory.arguments``).

    Subclassing is not supported, and is rejected at class-creation time
    by ``__init_subclass__`` (raises ``TypeError``). The class-level
    caches above are mutable dicts SHARED with the base; a subclass would
    inherit the same dict instances rather than getting its own, so a
    subclass cache would silently cross-contaminate with the base. The
    factory is a leaf class by contract -- extend the cookbook's flow by
    composition (wrap an instance), not by subclassing.
    """

    # Cache for storing input object types, keyed by class-derived name.
    input_object_types: ClassVar[dict[str, type]] = {}

    # Tracks which orderset class built each cached type name. Under
    # class-based naming, a collision means two distinct classes share a
    # ``__name__`` -- always a bug. Strict raise, not warn. Spec-028
    # Decision 9 names this map's role explicitly (source-class collision
    # detection vs the materialization ledger's ``name -> input class``
    # keying in ``orders/inputs.py::_materialized_names``).
    _type_orderset_registry: ClassVar[dict[str, type]] = {}

    def __init_subclass__(cls) -> None:
        """Reject subclassing -- the class-level caches are not subclass-safe.

        ``input_object_types`` / ``_type_orderset_registry`` are mutable
        dicts SHARED with the base: a subclass inherits the same instances
        rather than isolating its own, so its builds would silently
        cross-contaminate the base's. Subclassing is therefore an
        unsupported design path; extend by composition (wrap an
        instance), not inheritance.
        """
        raise TypeError(
            f"{OrderArgumentsFactory.__name__} does not support subclassing "
            f"(attempted by {cls.__name__!r}): its class-level caches are shared "
            "mutable dicts a subclass would inherit rather than isolate, silently "
            "cross-contaminating builds. Extend it by composition (wrap an "
            "instance), not inheritance.",
        )

    def __init__(self, orderset_class: type[OrderSet]) -> None:
        """Initialize the factory.

        Args:
            orderset_class: The root ``OrderSet`` subclass to convert.
                The generated GraphQL type name is
                ``f"{orderset_class.__name__}InputType"`` (Decision 9).
        """
        self.orderset_class = orderset_class
        self.order_input_type_name = _input_type_name_for(orderset_class)

    @property
    def arguments(self) -> type:
        """BFS-build the root orderset and return its input class.

        Idempotent: subsequent property reads against the same orderset
        hit the cache. Spec Decision 3 Layer 5 names the input class
        itself as the factory's deliverable -- the consumer-facing
        argument shape (``list[<T>InputType!]``) is wrapped by the
        ``order_input_type`` helper at the resolver site.
        """
        self._ensure_built()
        return self.input_object_types[self.order_input_type_name]

    def _ensure_built(self) -> None:
        """BFS-walk ``self.orderset_class`` + every reachable ``RelatedOrder`` target.

        Cycles (``A -> B -> A``) are handled naturally: the enqueue-time
        ``target not in seen`` gate stops cycles from looping. Builds
        each orderset exactly once; subsequent visits hit the cache.
        Collision detection raises when two distinct ordersets claim
        the same name.

        FIFO queue (``pending.pop(0)``) mirrors the filter side at
        ``filters/factories.py::FilterArgumentsFactory._ensure_built``;
        the cookbook uses LIFO at
        ``order_arguments_factory.py::OrderArgumentsFactory._ensure_built``
        (``pending.pop()``). Both yield the same set of reachable classes
        for a finite graph, but FIFO produces a deterministic
        breadth-first build order that keeps the two subsystems aligned
        for cross-slice review.
        """
        pending: list[type[OrderSet]] = [self.orderset_class]
        seen: set[type[OrderSet]] = set()
        while pending:
            os_class = pending.pop(0)
            if os_class in seen:
                continue
            seen.add(os_class)

            target_name = _input_type_name_for(os_class)
            existing_owner = self._type_orderset_registry.get(target_name)
            if existing_owner is not None and existing_owner is not os_class:
                raise ConfigurationError(
                    f"OrderArgumentsFactory: input type name {target_name!r} is claimed "
                    f"by two distinct OrderSet classes: "
                    f"{existing_owner.__module__}.{existing_owner.__qualname__} vs "
                    f"{os_class.__module__}.{os_class.__qualname__}. Rename one orderset "
                    "so its class-derived input type name is unique.",
                )

            if target_name not in self.input_object_types:
                self._build_class_type(os_class)

            for rel_order in getattr(os_class, "related_orders", {}).values():
                target = rel_order.orderset
                # ``RelatedOrder(None, ...)`` placeholder -- skip silently
                # (cookbook lines 124-130).
                if target is not None and target not in seen:
                    pending.append(target)

    def _build_class_type(self, os_class: type[OrderSet]) -> None:
        """Build the root input class for ``os_class`` and stash it in the cache.

        The order side has NO operator-bag layer (Spec Decision 8 -- no
        ``and_`` / ``or_`` / ``not_``), so the filter side's
        ``_build_logic_fields`` call has no analogue here.
        """
        type_name = _input_type_name_for(os_class)
        owner_definition = getattr(os_class, "_owner_definition", None)
        input_field_triples = _build_input_fields(os_class, owner_definition)
        input_cls = build_input_class(type_name, input_field_triples)
        self.input_object_types[type_name] = input_cls
        self._type_orderset_registry[type_name] = os_class


# TODO(spec-028-orders-0_0_8 Decision 12; deferred to 0.0.9): Layer 6 of
# the six-layer pipeline -- the dynamic ``OrderSet`` cache keyed by
# ``(model, fields, extra_meta)`` for connection fields that target the
# same model without an explicit ``orderset_class``. The forward-reserved
# symbols are ``_dynamic_orderset_cache: dict[tuple, type[OrderSet]]``
# and ``get_orderset_class(orderset_class, **meta) -> type[OrderSet]``
# (mirrors ``filters/factories.py::get_filterset_class`` /
# ``_dynamic_filterset_cache``). Slice 2 ships only the BFS layer; the
# dynamic factory lands with the connection-field surface in ``0.0.9``.
