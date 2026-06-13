"""Order input-class BFS factory; dynamic ``OrderSet`` generation is deferred.

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

from typing import TYPE_CHECKING, Any, ClassVar

from ..utils.inputs import GeneratedInputArgumentsFactory
from .inputs import _build_input_fields

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from django.db import models  # noqa: F401 - kept for filter-side parity.


class OrderArgumentsFactory(GeneratedInputArgumentsFactory):
    """BFS-build every reachable Strawberry input class for an ``OrderSet``.

    The BFS walk, per-class collision check, idempotent cache, and
    subclass-rejection guard live in
    ``utils/inputs.py::GeneratedInputArgumentsFactory`` (single-sited with
    ``filters/factories.py::FilterArgumentsFactory`` and the cookbook's
    ``order_arguments_factory.py`` BFS); this subclass supplies the order-family
    caches and hooks. The two class-level caches keep their spec-028 Decision 9
    names so ``registry.clear()`` and the test suite address them directly:

    - ``input_object_types`` -- class-name -> built input class, shared across
      factory instances so repeated builds of the same orderset converge on the
      same input class.
    - ``_type_orderset_registry`` -- source-class collision detection: a
      ``ConfigurationError`` fires when two distinct ordersets claim the same
      class-derived name (distinct from the materialization ledger's ``name ->
      input class`` keying in ``orders/inputs.py::_materialized_names``).

    The factory does NOT materialize built classes as module globals; that is
    the finalizer's phase-2.5 contract. ``arguments`` returns the built input
    class for the root orderset.

    The shared base uses a FIFO queue (deterministic breadth-first build order
    aligned with the filter side), where the cookbook's order factory used
    LIFO; both reach the same set of classes for a finite graph.

    Subclassing is rejected at class-creation time; extend by composition (wrap
    an instance), not inheritance.
    """

    input_object_types: ClassVar[dict[str, type]] = {}
    _type_orderset_registry: ClassVar[dict[str, type]] = {}

    _collision_registry_attr = "_type_orderset_registry"
    _factory_label = "OrderArgumentsFactory"
    _family_label = "OrderSet"
    _rename_noun = "orderset"
    _related_attr = "related_orders"
    _related_target_attr = "orderset"

    def _build_input_triples(
        self,
        set_cls: type,
        type_name: str,
        owner_definition: Any,
    ) -> list[tuple[str, Any, dict[str, Any]]]:
        """Order input triples -- no operator bag (Spec Decision 8)."""
        del type_name  # the order side has no ``and_`` / ``or_`` / ``not_`` bag.
        return _build_input_fields(set_cls, owner_definition)


# TODO(spec-028-orders-0_0_8 Decision 12; deferred to 0.0.9): Layer 6 of
# the six-layer pipeline -- the dynamic ``OrderSet`` cache keyed by
# ``(model, fields, extra_meta)`` for connection fields that target the
# same model without an explicit ``orderset_class``. The forward-reserved
# symbols are ``_dynamic_orderset_cache: dict[tuple, type[OrderSet]]``
# and ``get_orderset_class(orderset_class, **meta) -> type[OrderSet]``
# (mirrors ``filters/factories.py::get_filterset_class`` /
# ``_dynamic_filterset_cache``). Slice 2 ships only the BFS layer; the
# dynamic factory lands with the connection-field surface in ``0.0.9``.
