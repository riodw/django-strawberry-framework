"""Order input-class BFS factory.

Layer 5 of the spec-028 six-layer pipeline (the BFS that builds every
reachable Strawberry input class via ``_build_input_fields`` +
``build_input_class`` from ``orders/inputs.py``). The factory consumes
resolved ``OrderSet.get_fields()`` results -- NOT a parallel
``OrderSet.Meta.fields`` map -- so the runtime order shape and the
GraphQL input shape stay downstream of one decision site (mirror of
``filters/factories.py``'s Layer 5 + spec-027 Decision 4).

The finalizer materializes the built classes as module globals at
finalize time; this module owns build-only.
``connection.py::DjangoConnectionField`` resolves ordering from the
already-resolved ``Meta.orderset_class`` sidecar; auto-generation of an
``OrderSet`` from ``Meta.fields`` without an explicit class remains a
standing deferred Non-goal (spec-028 Decision 12).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import override

from ..utils.inputs import GeneratedInputArgumentsFactory
from .inputs import _build_input_fields
from .sets import OrderSet

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from ..types.definition import DjangoTypeDefinition


class OrderArgumentsFactory(GeneratedInputArgumentsFactory[OrderSet]):
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

    input_object_types: ClassVar[dict[str, type[object]]] = {}
    _type_orderset_registry: ClassVar[dict[str, type[OrderSet]]] = {}

    _collision_registry_attr = "_type_orderset_registry"
    _factory_label = "OrderArgumentsFactory"
    _family_label = "OrderSet"
    _rename_noun = "orderset"
    _related_attr = "related_orders"
    _related_target_attr = "orderset"

    @override
    def _build_input_triples(
        self,
        set_cls: type[OrderSet],
        type_name: str,
        owner_definition: DjangoTypeDefinition | None,
    ) -> list[tuple[str, object, dict[str, object]]]:
        """Order input triples -- no operator bag (spec-028 Decision 8)."""
        del type_name  # the order side has no ``and_`` / ``or_`` / ``not_`` bag.
        return _build_input_fields(set_cls, owner_definition)
