"""BFS factory + dynamic-FilterSet cache (Slice 2).

Layer 5 of the spec-021 six-layer pipeline (the BFS that builds every
reachable Strawberry input class via the named converter
``convert_filter_to_input_annotation``) plus Layer 6 (the dynamic-class
cache keyed by ``(model, fields, extra_meta)`` for connection fields
that target the same model without an explicit ``filterset_class``).

The BFS factory consumes resolved ``django-filter`` filter instances --
NOT a parallel ``FILTER_DEFAULTS`` map -- so the runtime filter shape
and the GraphQL input shape stay downstream of one decision site
(Decision 4 H1 / spec-021 lines 579-584). Slice 3's finalizer materializes
the built classes as module globals; Slice 2 only builds them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..exceptions import ConfigurationError
from .inputs import _build_input_fields, _build_logic_fields, _input_type_name_for, build_input_class
from .sets import FilterSet

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from django.db import models


# Module-level dynamic-FilterSet cache per Layer 6 of Decision 3. Keys
# are produced by ``_make_cache_key`` so dict / list / scalar shapes for
# ``Meta.fields`` collapse onto stable tuple keys. The cache is the
# duplicate-``__name__`` collision break-glass: two connection fields
# targeting the same model without an explicit ``filterset_class``
# resolve to the same generated class.
_dynamic_filterset_cache: dict[tuple, type[FilterSet]] = {}


# Reserved kwargs stripped from ``get_filterset_class``'s meta input to
# prevent keyword collisions with the dynamic-class factory below.
_RESERVED_FACTORY_KEYS: frozenset[str] = frozenset({"filterset_base_class"})


class FilterArgumentsFactory:
    """BFS-build every reachable Strawberry input class for a ``FilterSet``.

    Verbatim port of the cookbook's
    ``django_graphene_filters/filter_arguments_factory.py::FilterArgumentsFactory``
    BFS algorithm. Two class-level caches mirror the cookbook contract:

    - ``input_object_types: dict[str, type]`` -- class-name -> built
      input class. Shared across factory instances so repeated builds
      of the same filterset converge on the same input class.
    - ``_type_filterset_registry: dict[str, type]`` -- collision
      detection. The factory raises ``ConfigurationError`` when two
      distinct filtersets claim the same class-derived name.

    The factory does NOT materialize built classes as module globals;
    that is Slice 3's finalizer-phase-2.5 contract. The factory's
    ``arguments`` property returns the built input class for the root
    filterset (per Implementation discretion item 5).

    Subclassing is not supported. The class-level caches above are
    mutable dicts; a subclass would inherit the SAME dict instances
    rather than getting its own, so a subclass cache would silently
    cross-contaminate with the base. The factory is a leaf class by
    contract — extend the cookbook's flow by composition (wrap an
    instance), not by subclassing.
    """

    # Cache for storing input object types, keyed by class-derived name.
    input_object_types: dict[str, type] = {}

    # Tracks which filterset class built each cached type name. Under
    # class-based naming, a collision means two distinct classes share a
    # ``__name__`` -- always a bug. Strict raise, not warn.
    _type_filterset_registry: dict[str, type] = {}

    def __init__(self, filterset_class: type[FilterSet]) -> None:
        """Initialize the factory.

        Args:
            filterset_class: The root ``FilterSet`` subclass to convert.
                The generated GraphQL type name is
                ``f"{filterset_class.__name__}InputType"`` (Decision 9).
        """
        self.filterset_class = filterset_class
        self.filter_input_type_name = _input_type_name_for(filterset_class)

    @property
    def arguments(self) -> type:
        """BFS-build the root filterset and return its input class.

        Idempotent: subsequent property reads against the same filterset
        hit the cache. Spec Decision 3 Layer 5 line 477 names the input
        class itself as the factory's deliverable -- consumer-facing
        argument shape is provided separately by ``filter_input_type``.
        """
        self._ensure_built()
        return self.input_object_types[self.filter_input_type_name]

    def _ensure_built(self) -> None:
        """BFS-walk ``self.filterset_class`` + every reachable ``RelatedFilter`` target.

        Cycles (``A -> B -> A``) are handled naturally: the enqueue-time
        ``target not in seen`` gate stops cycles from looping. Builds
        each filterset exactly once; subsequent visits hit the cache.
        Collision detection raises when two distinct filtersets claim
        the same name.
        """
        pending: list[type[FilterSet]] = [self.filterset_class]
        seen: set[type[FilterSet]] = set()
        while pending:
            fs_class = pending.pop(0)
            if fs_class in seen:
                continue
            seen.add(fs_class)

            target_name = _input_type_name_for(fs_class)
            existing_owner = self._type_filterset_registry.get(target_name)
            if existing_owner is not None and existing_owner is not fs_class:
                raise ConfigurationError(
                    f"FilterArgumentsFactory: input type name {target_name!r} is claimed "
                    f"by two distinct FilterSet classes: "
                    f"{existing_owner.__module__}.{existing_owner.__qualname__} vs "
                    f"{fs_class.__module__}.{fs_class.__qualname__}. Rename one filterset "
                    "so its class-derived input type name is unique.",
                )

            if target_name not in self.input_object_types:
                self._build_class_type(fs_class)

            for rel_filter in getattr(fs_class, "related_filters", {}).values():
                target = rel_filter.filterset
                # ``RelatedFilter(None, ...)`` placeholder -- skip silently
                # (cookbook lines 124-130).
                if target is not None and target not in seen:
                    pending.append(target)

    def _build_class_type(self, fs_class: type[FilterSet]) -> None:
        """Build the root input class for ``fs_class`` and stash it in the cache."""
        type_name = _input_type_name_for(fs_class)
        owner_definition = getattr(fs_class, "_owner_definition", None)
        input_field_triples = _build_input_fields(fs_class, owner_definition)
        logic_field_triples = _build_logic_fields(type_name)
        field_specs: list[tuple[str, Any, dict[str, Any] | None]] = [
            (python_attr, annotation, kwargs)
            for python_attr, annotation, kwargs in (*input_field_triples, *logic_field_triples)
        ]
        input_cls = build_input_class(type_name, field_specs)
        self.input_object_types[type_name] = input_cls
        self._type_filterset_registry[type_name] = fs_class


# ---------------------------------------------------------------------------
# Layer 6 -- dynamic-FilterSet cache (cookbook ``filterset_factories.py``)
# ---------------------------------------------------------------------------


def _make_cache_key(safe_meta: dict[str, Any]) -> tuple:
    """Build a hashable cache key from a ``Meta``-shaped dict.

    ``model`` is the primary discriminator. ``fields`` may be
    ``"__all__"``, a list of field names, or a dict mapping field ->
    list of lookups -- all serialised into a hashable form so identical
    declarations share a class. Any extra meta keys are included
    verbatim. Verbatim port of the cookbook's same-named helper.
    """
    model = safe_meta.get("model")
    fields = safe_meta.get("fields")
    if isinstance(fields, dict):
        fields_key: tuple = (
            "dict",
            tuple(sorted((k, tuple(v) if isinstance(v, list) else v) for k, v in fields.items())),
        )
    elif isinstance(fields, (list, tuple)):
        fields_key = ("seq", tuple(fields))
    else:
        fields_key = ("raw", fields)
    extra = tuple(sorted((k, v) for k, v in safe_meta.items() if k not in {"model", "fields"}))
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


def get_filterset_class(
    filterset_class: type[FilterSet] | None,
    **meta: Any,
) -> type[FilterSet]:
    """Return a ``FilterSet`` class for use against a connection / list field.

    Mirrors the cookbook's same-named helper at
    ``django_graphene_filters/filterset_factories.py::get_filterset_class``
    (NOT graphene-django's same-named function -- spec Decision 4
    name-collision note). The function trusts its caller; the
    connection-field surface owning this entry point lands in ``0.0.9``.

    Args:
        filterset_class: An optional pre-declared ``FilterSet`` subclass.
            When provided, returned unchanged.
        **meta: ``Meta``-shaped keys (``model``, ``fields``, ``exclude``,
            ...) for the synthetic ``FilterSet`` subclass. Required when
            ``filterset_class is None``.

    Returns:
        A ``FilterSet`` class. The dynamic-cache path collapses
        equivalent meta into a shared class so two callers with
        equivalent declarations get the same ``__name__`` (preventing
        the BFS factory's duplicate-name collision check from firing).
    """
    if filterset_class is not None:
        return filterset_class
    safe_meta = {k: v for k, v in meta.items() if k not in _RESERVED_FACTORY_KEYS}
    cache_key = _make_cache_key(safe_meta)
    cached = _dynamic_filterset_cache.get(cache_key)
    if cached is not None:
        return cached
    generated = _create_dynamic_filterset_class(safe_meta)
    _dynamic_filterset_cache[cache_key] = generated
    return generated
