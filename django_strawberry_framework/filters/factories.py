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
Non-goal (``spec-027`` Non-goals #"Auto-generation of ``FilterSet`` from
``Meta.fields``"); the cache plumbing was landed ahead of that consumer,
which is not yet built. Layer 6 stays build-and-test-only until that
surface ships.

The BFS factory consumes resolved ``django-filter`` filter instances --
NOT a parallel ``FILTER_DEFAULTS`` map -- so the runtime filter shape
and the GraphQL input shape stay downstream of one decision site
(Decision 4 H1 / spec-027 lines 579-584). The finalizer materializes the
BFS factory's built input classes as module globals at finalize time;
this module owns build-only. (Layer 6's dynamic FilterSet classes are
plain ``type(...)`` products cached below, never materialized as module
globals.)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..exceptions import ConfigurationError
from ..utils.inputs import GeneratedInputArgumentsFactory
from .inputs import _build_input_fields, _build_logic_fields
from .sets import FilterSet

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from django.db import models


# Module-level dynamic-FilterSet cache per Layer 6 of Decision 3. Keys
# are produced by ``_make_cache_key`` so dict / list / scalar shapes for
# ``Meta.fields`` collapse onto stable tuple keys. The cache is the
# duplicate-``__name__`` collision break-glass for the (deferred,
# unconsumed) auto-FilterSet surface: two fields that auto-derive a
# FilterSet against the same model from equivalent ``Meta`` would resolve
# to the same generated class. No source path exercises this yet -- see
# the module docstring; the cache is build-and-test-only at ``0.0.9``.
#
# Lifecycle (M-filters-3 review, accepted as-is): this cache has NO clear
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
    class for the root filterset (per Implementation discretion item 5).

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


def _make_hashable(v: Any) -> Any:
    """Recursively convert unhashable objects into hashable equivalents.

    ``dict`` and ``set`` / ``frozenset`` are *unordered* containers, so their
    hashable form is sorted - two structurally-equal inputs must collapse to one
    cache key regardless of source iteration order. ``list`` / ``tuple`` are
    *ordered* (a list-shaped ``Meta.fields`` defines filter order), so their order
    is preserved. Both unordered branches sort by ``repr`` rather than by the
    values themselves so they stay total-ordered even for mixed,
    mutually-unorderable member or key types (e.g. ``{1, "a"}`` or
    ``{"a": 1, 0: 2}``); equal members produce equal reprs, so the canonical
    order is stable.
    """
    if isinstance(v, dict):
        return tuple(
            sorted(((k, _make_hashable(val)) for k, val in v.items()), key=repr),
        )
    if isinstance(v, (set, frozenset)):
        return tuple(sorted((_make_hashable(item) for item in v), key=repr))
    if isinstance(v, (list, tuple)):
        return tuple(_make_hashable(item) for item in v)
    return v


def _normalize_meta_for_factory(meta: dict[str, Any]) -> dict[str, Any]:
    """Normalize Meta kwargs before cache keying and dynamic class creation.

    Two equivalences must collapse onto one cache slot (and one generated
    ``FilterSet`` class) or the BFS factory's duplicate-``__name__`` check
    fires against two ``<Model>AutoFilter`` classes that are the same
    declaration arrived via different surface shapes:

    - ``filter_fields`` is the ``FilterSetMetaclass`` synonym for ``fields``;
      promote it (or drop it when ``fields`` is already present) so the alias
      is not an extras discriminator.
    - Top-level ``set`` / ``frozenset`` ``fields`` (and set-valued lookup
      bags under a dict-shaped ``fields``) are unordered; canonicalize them to
      ``repr``-sorted lists so cache keys and generated filter order are stable
      across ``PYTHONHASHSEED``. Ordered ``list`` / ``tuple`` ``fields`` keep
      their declaration order.
    """
    safe_meta = {k: v for k, v in meta.items() if k not in _RESERVED_FACTORY_KEYS}
    if "filter_fields" in safe_meta:
        if "fields" not in safe_meta:
            safe_meta["fields"] = safe_meta.pop("filter_fields")
        else:
            # ``fields`` wins (metaclass alias rule); drop the synonym so it
            # cannot split an otherwise-identical cache slot via extras.
            safe_meta.pop("filter_fields")
    fields = safe_meta.get("fields")
    if isinstance(fields, (set, frozenset)):
        safe_meta["fields"] = sorted(fields, key=repr)
    elif isinstance(fields, dict):
        safe_meta["fields"] = {
            key: (sorted(value, key=repr) if isinstance(value, (set, frozenset)) else value)
            for key, value in fields.items()
        }
    return safe_meta


def _make_cache_key(safe_meta: dict[str, Any]) -> tuple:
    """Build a hashable cache key from a ``Meta``-shaped dict.

    ``model`` is the primary discriminator. ``fields`` may be
    ``"__all__"``, a list of field names, or a dict mapping field ->
    list of lookups -- all serialised into a hashable form so identical
    declarations share a class. Any extra meta keys are included
    via ``_make_hashable``. Callers should pass meta already run through
    ``_normalize_meta_for_factory`` so ``filter_fields`` and unordered
    ``set`` / ``frozenset`` shapes have been canonicalized; the branches
    below still accept those shapes directly as defense in depth.

    ``set`` / ``frozenset`` (top-level or nested under dict-shaped
    ``fields``) are sorted into a canonical form by ``_make_hashable`` /
    ``_normalize_meta_for_factory``. Ordered ``list`` / ``tuple``
    ``fields`` preserve declaration order -- prefer those when filter
    order matters. Dict-shaped ``fields`` keys sort via ``key=repr`` so
    mixed, mutually-unorderable key types cannot ``TypeError`` the key.
    """
    model = safe_meta.get("model")
    fields = safe_meta.get("fields")
    if isinstance(fields, dict):
        fields_key: tuple = ("dict", _make_hashable(fields))
    elif isinstance(fields, (list, tuple)):
        fields_key = ("seq", tuple(_make_hashable(item) for item in fields))
    elif isinstance(fields, (set, frozenset)):
        fields_key = ("seq", tuple(sorted((_make_hashable(item) for item in fields), key=repr)))
    else:
        fields_key = ("raw", fields)
    extra = _make_hashable(
        {k: v for k, v in safe_meta.items() if k not in {"model", "fields"}},
    )
    return (model, fields_key, extra)


def _create_dynamic_filterset_class(safe_meta: dict[str, Any]) -> type[FilterSet]:
    """Build a synthetic ``FilterSet`` subclass from a ``Meta`` dict.

    Replaces graphene-django's ``custom_filterset_factory`` (which the
    cookbook reaches for) with a plain ``type(name, (FilterSet,),
    {"Meta": meta})`` call. Spec line 247 explicitly drops the
    ``replace_csv_filters`` rewrap -- Strawberry's typed input handles
    ``list[T]`` natively.
    """
    model: type[models.Model] | None = safe_meta.get("model")
    if model is None:
        raise ConfigurationError(
            "get_filterset_class requires `model` when called without an explicit "
            "filterset_class; received meta without a `model` key.",
        )
    meta_attrs = dict(safe_meta)
    name = f"{model.__name__}AutoFilter"
    meta_class = type("Meta", (object,), meta_attrs)
    return type(name, (FilterSet,), {"Meta": meta_class})


def get_filterset_class(filterset_class: type[FilterSet] | None, **meta: Any) -> type[FilterSet]:
    """Return a ``FilterSet`` class for use against a connection / list field.

    Mirrors the cookbook's same-named helper at
    ``django_graphene_filters/filterset_factories.py::get_filterset_class``
    (NOT graphene-django's same-named function -- spec Decision 4
    name-collision note). The function trusts its caller. It has no source
    consumer yet: the auto-FilterSet surface that would call it (a field
    targeting a model without an explicit ``filterset_class``) is a
    standing deferred Non-goal (``spec-027`` Non-goals #"Auto-generation of
    ``FilterSet`` from ``Meta.fields``"). ``DjangoConnectionField``
    (spec-030, ``0.0.9``) consumes the already-resolved
    ``Meta.filterset_class`` sidecar directly and does not route through
    here. Built-and-tested ahead of that consumer.

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
    if filterset_class is not None:
        return filterset_class
    safe_meta = _normalize_meta_for_factory(meta)
    cache_key = _make_cache_key(safe_meta)
    cached = _dynamic_filterset_cache.get(cache_key)
    if cached is not None:
        return cached
    generated = _create_dynamic_filterset_class(safe_meta)
    _dynamic_filterset_cache[cache_key] = generated
    return generated
