"""Filter input-class BFS factory + the (currently unconsumed) dynamic-FilterSet cache.

Layer 5 of the spec-027 six-layer pipeline (the BFS that builds every
reachable Strawberry input class via the named converter
``convert_filter_to_input_annotation``) plus Layer 6 (the dynamic-class
cache keyed by ``(model, fields, extra_meta)`` for an auto-FilterSet
surface that would let a field target a model without an explicit
``filterset_class``).

Layer 6 has no source consumer: ``DjangoConnectionField`` (spec-030,
shipped ``0.0.9``) reads the wrapped type's already-resolved
``Meta.filterset_class`` sidecar directly and never builds a FilterSet
from ``model`` / ``fields``. Auto-generation of a ``FilterSet`` from
``Meta.fields`` without an explicit class is a standing deferred
Non-goal (``spec-027`` Non-goals #"Auto-generation of `FilterSet`");
the cache plumbing was landed ahead of that consumer, which is not yet
built. Layer 6 stays build-and-test-only until that surface ships.

The BFS factory consumes resolved ``django-filter`` filter instances --
NOT a parallel ``FILTER_DEFAULTS`` map -- so the runtime filter shape
and the GraphQL input shape stay downstream of one decision site
(spec-027 Decision 4). The finalizer materializes the BFS factory's
built input classes as module globals at finalize time;
this module owns build-only. (Layer 6's dynamic FilterSet classes are
plain ``type(...)`` products cached below, never materialized as module
globals.) Hashing, Meta canonicalize, and the ``type(...)`` skeleton live
in ``utils/inputs.py::make_dynamic_set_getter``; this module keeps the
family cache and passes ``FILTERSET_FIELDS_ALIAS``. The synonym rule itself
is ``utils/inputs.py::resolve_set_meta_fields``; class-Meta write-back is
``promote_set_meta_fields`` (shared with ``FilterSetMetaclass`` /
``OrderSetMetaclass``).
"""

from __future__ import annotations

from typing import Any, ClassVar

from ..utils.inputs import (
    FILTERSET_FIELDS_ALIAS,
    GeneratedInputArgumentsFactory,
    make_dynamic_set_getter,
)
from .inputs import _build_input_fields, _build_logic_fields
from .sets import FilterSet

# Module-level dynamic-FilterSet cache per Layer 6 of Decision 3. Keys
# are produced by ``utils/inputs.py::make_set_meta_cache_key`` so dict /
# list / scalar shapes for ``Meta.fields`` collapse onto stable tuple
# keys. The cache is the duplicate-``__name__`` collision break-glass for
# the (deferred, unconsumed) auto-FilterSet surface: two fields that
# auto-derive a FilterSet against the same model from equivalent ``Meta``
# would resolve to the same generated class. No source path exercises
# this yet -- see the module docstring; the cache is build-and-test-only.
# The hashing / ``type(...)`` skeleton is shared with
# ``orders/factories.py`` via ``make_dynamic_set_getter``; this dict stays
# family-owned so a filter clear cannot drop an order class (and the
# reverse).
#
# Lifecycle: this cache has NO clear
# hook, so after ``registry.clear()`` rebuilds model classes a dynamic
# FilterSet built against the prior model class remains parked here. That
# is a test-isolation nicety only -- the keys embed the model identity, so
# a rebuilt model gets a fresh key rather than a wrong hit -- and carries
# no real-world cost in a normal (non-reloading) process. Add a clear hook
# here only if a consumer reload path ever demands it.
_dynamic_filterset_cache: dict[tuple, type[FilterSet]] = {}


# Reserved kwargs stripped from ``get_filterset_class``'s meta input to
# prevent keyword collisions with the dynamic-class factory below.
_RESERVED_FACTORY_KEYS: frozenset[str] = frozenset({"filterset_base_class"})


class FilterArgumentsFactory(GeneratedInputArgumentsFactory):
    """BFS-build every reachable Strawberry input class for a ``FilterSet``.

    The BFS walk, per-class collision check, idempotent cache, and
    subclass-rejection guard live in
    ``utils/inputs.py::GeneratedInputArgumentsFactory`` (the cookbook's
    ``filter_arguments_factory.py`` BFS algorithm, single-sited with the order
    side); this subclass supplies the filter-family caches and hooks. The two
    class-level caches keep their spec-027 Decision 9 names so
    ``registry.clear()`` and the test suite address them directly:

    - ``input_object_types`` -- class-name -> built input class, shared across
      factory instances so repeated builds of the same filterset converge on
      the same input class.
    - ``_type_filterset_registry`` -- collision detection: a
      ``ConfigurationError`` fires when two distinct filtersets claim the same
      class-derived name.

    The factory does NOT materialize built classes as module globals; that is
    the finalizer's phase-2.5 contract. ``arguments`` returns the built input
    class for the root filterset (per spec-027 Decision 6 subpass 4).

    Subclassing is rejected at class-creation time (the caches are shared
    mutable dicts a subclass would inherit rather than isolate, silently
    cross-contaminating builds); extend by composition (wrap an instance),
    not inheritance.
    """

    input_object_types: ClassVar[dict[str, type]] = {}
    _type_filterset_registry: ClassVar[dict[str, type]] = {}

    _collision_registry_attr = "_type_filterset_registry"
    _factory_label = "FilterArgumentsFactory"
    _family_label = "FilterSet"
    _rename_noun = "filterset"
    _related_attr = "related_filters"
    _related_target_attr = "filterset"

    def _build_input_triples(
        self,
        set_cls: type,
        type_name: str,
        owner_definition: Any,
    ) -> list[tuple[str, Any, dict[str, Any]]]:
        """Filter input triples plus the ``and_`` / ``or_`` / ``not_`` operator bag."""
        return [*_build_input_fields(set_cls, owner_definition), *_build_logic_fields(type_name)]


# ---------------------------------------------------------------------------
# Layer 6 -- dynamic-FilterSet cache (cookbook ``filterset_factories.py``)
# ---------------------------------------------------------------------------


_get_filterset_class = make_dynamic_set_getter(
    cache=_dynamic_filterset_cache,
    set_base_class=FilterSet,
    auto_name_suffix="AutoFilter",
    getter_name="get_filterset_class",
    reserved_keys=_RESERVED_FACTORY_KEYS,
    explicit_param="filterset_class",
    fields_alias=FILTERSET_FIELDS_ALIAS,
)


def get_filterset_class(filterset_class: type[FilterSet] | None, **meta: Any) -> type[FilterSet]:
    """Return a ``FilterSet`` class for use against a connection / list field.

    Mirrors the cookbook's same-named helper at
    ``django_graphene_filters/filterset_factories.py::get_filterset_class``
    (NOT graphene-django's same-named function -- spec Decision 4
    name-collision note). The function trusts its caller. It has no source
    consumer yet: the auto-FilterSet surface that would call it (a field
    targeting a model without an explicit ``filterset_class``) is a
    standing deferred Non-goal
    (``spec-027`` Non-goals #"Auto-generation of `FilterSet`").
    ``DjangoConnectionField`` (spec-030, ``0.0.9``) consumes the
    already-resolved ``Meta.filterset_class`` sidecar directly and does not
    route through here. Built-and-tested ahead of that consumer.

    Args:
        filterset_class: An optional pre-declared ``FilterSet`` subclass.
            When provided, returned unchanged.
        **meta: ``Meta``-shaped keys (``model``, ``fields``, ``exclude``,
            ...) for the synthetic ``FilterSet`` subclass. Required when
            ``filterset_class is None``. ``filter_fields`` is accepted as the
            metaclass synonym for ``fields`` and normalized before caching.

    Returns:
        A ``FilterSet`` class. The dynamic-cache path collapses
        equivalent meta into a shared class so two callers with
        equivalent declarations get the same ``__name__`` (preventing
        the BFS factory's duplicate-name collision check from firing).
        Two callers with **distinct** Meta declarations against the same model
        will land at the same generated ``__name__`` and so collide through the
        BFS factory's ``_type_filterset_registry`` collision check; resolve by
        declaring an explicit ``filterset_class=`` at one of the two call sites.
    """
    return _get_filterset_class(filterset_class, **meta)
