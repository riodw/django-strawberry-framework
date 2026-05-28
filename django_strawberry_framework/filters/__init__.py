"""Filter subsystem entry point.

Re-exports the foundational primitives from `base.py`, the `FilterSet`
+ `FilterSetMetaclass` pair from `sets.py`, and the Decision-11
consumer helper `filter_input_type` (Slice 2). Slice 3 will wire the
finalizer-phase-2.5 orphan check that compares
`_helper_referenced_filtersets` against the set of `Meta.filterset_class`-
wired filtersets.
"""

from __future__ import annotations

from typing import Annotated

import strawberry

from .base import (
    ArrayFilter,
    ArrayFilterMethod,
    Filter,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    LazyRelatedClassMixin,
    ListFilter,
    ListFilterMethod,
    RangeField,
    RangeFilter,
    RelatedFilter,
    TypedFilter,
    validate_range,
)
from .inputs import INPUTS_MODULE_PATH, _input_type_name_for
from .sets import FilterSet, FilterSetMetaclass

# Ledger of `FilterSet`s referenced through the Decision-11
# `filter_input_type(...)` consumer helper. `registry.clear()` clears
# this set via a cycle-safe local import per spec-021 Decision 9.
# Slice 3's finalizer phase 2.5 subpass 4 compares this set against the
# set of `Meta.filterset_class`-wired filtersets and raises
# `ConfigurationError` for orphans.
_helper_referenced_filtersets: set[type[FilterSet]] = set()


def filter_input_type(filterset_class: type[FilterSet]) -> object:
    """Return the `Annotated[...]` forward-reference for a filterset's input class.

    The returned annotation is the canonical Strawberry forward-reference
    idiom:
    ``Annotated["<Name>FilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]``.
    Consumer resolvers use it as the type annotation for a ``filter:``
    argument; Strawberry collects the annotation at ``@strawberry.type``
    decoration time, defers resolution, and resolves it via
    ``LazyType.resolve_type`` at schema-build time -- by which point
    ``finalize_django_types()`` (Slice 3) has materialized the input
    class as a module global of ``django_strawberry_framework.filters.inputs``.

    Args:
        filterset_class: A ``FilterSet`` subclass. Validated eagerly --
            the call raises ``TypeError`` for any non-``FilterSet``
            argument so consumers catch misuse at the resolver-declaration
            site instead of at schema-build time.

    Raises:
        TypeError: ``filterset_class`` is not a ``FilterSet`` subclass.
    """
    if not (isinstance(filterset_class, type) and issubclass(filterset_class, FilterSet)):
        raise TypeError(
            f"filter_input_type() requires a FilterSet subclass; got {filterset_class!r}",
        )
    _helper_referenced_filtersets.add(filterset_class)
    name = _input_type_name_for(filterset_class)
    # `Annotated[<str_variable>, ...]` wraps the runtime-computed string
    # as a `typing.ForwardRef` in the first `__args__` position; the
    # test plan pins this against future Python typing regressions
    # (`test_filter_input_type_returns_forwardref_in_annotation_args`,
    # spec-021 L7 of rev5). Do NOT refactor this into a literal-string
    # interpolation outside the Annotated call -- Strawberry's
    # `LazyType.resolve_type` requires the ForwardRef-wrapped form to
    # resolve via `module.__dict__` at schema build.
    return Annotated[name, strawberry.lazy(INPUTS_MODULE_PATH)]


__all__: tuple[str, ...] = (
    "ArrayFilter",
    "ArrayFilterMethod",
    "Filter",
    "FilterSet",
    "FilterSetMetaclass",
    "GlobalIDFilter",
    "GlobalIDMultipleChoiceFilter",
    "LazyRelatedClassMixin",
    "ListFilter",
    "ListFilterMethod",
    "RangeField",
    "RangeFilter",
    "RelatedFilter",
    "TypedFilter",
    "filter_input_type",
    "validate_range",
)
