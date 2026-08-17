"""Order input-class BFS factory + the (currently unconsumed) dynamic-OrderSet cache.

Layer 5 of the spec-028 six-layer pipeline (the BFS that builds every
reachable Strawberry input class via ``_build_input_fields`` +
``build_input_class`` from ``orders/inputs.py``). The factory consumes
resolved ``OrderSet.get_fields()`` results -- NOT a parallel
``OrderSet.Meta.fields`` map -- so the runtime order shape and the
GraphQL input shape stay downstream of one decision site (mirror of
``filters/factories.py``'s Layer 5 + Decision 4 H1).

The finalizer materializes the built classes as module globals at
finalize time; this module owns build-only. Layer 6 (dynamic
``OrderSet`` generation against a connection-field meta dict) has no
source consumer: ``connection.py::DjangoConnectionField`` resolves
ordering from the already-resolved ``Meta.orderset_class`` sidecar
directly rather than auto-generating an ``OrderSet``. The cache
plumbing ships as the filter-side twin (build-and-test-only) so hashing
and ``type(...)`` construction stay in
``utils/inputs.py::make_dynamic_set_getter`` instead of being copied the
day a consumer lands. Auto-generation of an ``OrderSet`` from
``Meta.fields`` without an explicit class remains a standing deferred
Non-goal (spec-028 Decision 12).
"""

from __future__ import annotations

from typing import Any, ClassVar

from ..utils.inputs import GeneratedInputArgumentsFactory, make_dynamic_set_getter
from .inputs import _build_input_fields
from .sets import OrderSet

# Module-level dynamic-OrderSet cache per Layer 6. Keys are produced by
# ``utils/inputs.py::make_set_meta_cache_key`` so dict / list / scalar
# shapes for ``Meta.fields`` collapse onto stable tuple keys. The cache
# is the duplicate-``__name__`` collision break-glass for the (deferred,
# unconsumed) auto-OrderSet surface. No source path exercises this yet --
# see the module docstring; the cache is build-and-test-only. The hashing
# / ``type(...)`` skeleton is shared with ``filters/factories.py`` via
# ``make_dynamic_set_getter``; this dict stays family-owned so an order
# clear cannot drop a filter class (and the reverse). Class-Meta expansion
# in ``orders/sets.py`` reads the same fingerprint through
# ``utils/inputs.py::read_set_meta_fields``.
#
# Lifecycle: this cache has NO clear hook, matching the filter-side
# Layer-6 dict. Keys embed the model identity, so a rebuilt model gets a
# fresh key rather than a wrong hit.
_dynamic_orderset_cache: dict[tuple, type[OrderSet]] = {}


# Reserved kwargs stripped from ``get_orderset_class``'s meta input to
# prevent keyword collisions with the dynamic-class factory below.
_RESERVED_FACTORY_KEYS: frozenset[str] = frozenset({"orderset_base_class"})


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


# ---------------------------------------------------------------------------
# Layer 6 -- dynamic-OrderSet cache (filter-side twin; no cookbook counterpart)
# ---------------------------------------------------------------------------


_get_orderset_class = make_dynamic_set_getter(
    cache=_dynamic_orderset_cache,
    set_base_class=OrderSet,
    auto_name_suffix="AutoOrder",
    getter_name="get_orderset_class",
    reserved_keys=_RESERVED_FACTORY_KEYS,
    explicit_param="orderset_class",
    fields_alias=None,
)


def get_orderset_class(orderset_class: type[OrderSet] | None, **meta: Any) -> type[OrderSet]:
    """Return an ``OrderSet`` class for use against a connection / list field.

    Filter-side twin of ``filters/factories.py::get_filterset_class``. The
    function trusts its caller. It has no source consumer yet: the
    auto-OrderSet surface that would call it (a field targeting a model
    without an explicit ``orderset_class``) is a standing deferred Non-goal
    (spec-028 Decision 12). ``DjangoConnectionField`` consumes the
    already-resolved ``Meta.orderset_class`` sidecar directly and does not
    route through here. Built-and-tested ahead of that consumer so the
    hashing / ``type(...)`` skeleton stays single-sited with the filter
    twin.

    Args:
        orderset_class: An optional pre-declared ``OrderSet`` subclass.
            When provided, returned unchanged.
        **meta: ``Meta``-shaped keys (``model``, ``fields``, ``exclude``,
            ...) for the synthetic ``OrderSet`` subclass. Required when
            ``orderset_class is None``.

    Returns:
        An ``OrderSet`` class. The dynamic-cache path collapses equivalent
        meta into a shared class so two callers with equivalent
        declarations get the same ``__name__`` (preventing the BFS
        factory's duplicate-name collision check from firing). Two callers
        with **distinct** Meta declarations against the same model will
        land at the same generated ``__name__`` and so collide through the
        BFS factory's ``_type_orderset_registry`` collision check; resolve
        by declaring an explicit ``orderset_class=`` at one of the two
        call sites.
    """
    return _get_orderset_class(orderset_class, **meta)
