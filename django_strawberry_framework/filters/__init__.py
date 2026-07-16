"""Filtering subsystem - declarative ``FilterSet`` classes that become GraphQL ``filter:`` arguments.

Re-exports the foundational primitives from `base.py`, the `FilterSet`
+ `FilterSetMetaclass` pair from `sets.py`, and the Decision-11
consumer helper `filter_input_type`. The finalizer's phase 2.5 wires
the orphan check that compares `_helper_referenced_filtersets` against
the set of `Meta.filterset_class`-wired filtersets.

Note: `Filter` re-exported here IS `django_filters.Filter` itself (a
plain re-export, not a subclass), surfaced under this package's namespace
so consumers writing a custom `method=` filter import one base class from
`django_strawberry_framework.filters`. It deliberately shadows the
upstream name; reach for `django_filters.Filter` directly only if you
need to distinguish the two.
"""

from __future__ import annotations

from ..registry import register_subsystem_clear
from ..utils.inputs import build_lazy_input_annotation
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
# `filter_input_type(...)` consumer helper. Cleared via the
# `register_subsystem_clear` row below (owner
# ``filters.helper_references``) so ``registry.clear()`` replays
# the callback -- not via a cycle-safe local import inside
# ``TypeRegistry.clear`` (that shape predates the registration
# seam). The finalizer's phase 2.5 subpass 4 compares this set
# against the set of `Meta.filterset_class`-wired filtersets and
# raises `ConfigurationError` for orphans.
_helper_referenced_filtersets: set[type[FilterSet]] = set()


def _clear_helper_referenced_filtersets() -> None:
    _helper_referenced_filtersets.clear()


register_subsystem_clear(_clear_helper_referenced_filtersets, owner="filters.helper_references")


def filter_input_type(filterset_class: type[FilterSet]) -> object:
    """Return the `Annotated[...]` forward-reference for a filterset's input class.

    The returned annotation is the canonical Strawberry forward-reference
    idiom:
    ``Annotated["<Name>FilterInputType", strawberry.lazy("django_strawberry_framework.filters.inputs")]``.
    Consumer resolvers use it as the type annotation for a ``filter:``
    argument; Strawberry collects the annotation at ``@strawberry.type``
    decoration time, defers resolution, and resolves it via
    ``LazyType.resolve_type`` at schema-build time -- by which point
    ``finalize_django_types()`` has materialized the input class as a
    module global of ``django_strawberry_framework.filters.inputs``.

    Args:
        filterset_class: A ``FilterSet`` subclass. Validated eagerly --
            the call raises ``TypeError`` for any non-``FilterSet``
            argument so consumers catch misuse at the resolver-declaration
            site instead of at schema-build time.

    Raises:
        TypeError: ``filterset_class`` is not a ``FilterSet`` subclass.
    """
    # Decision-11 consumer-helper body shared with ``orders/__init__.py::
    # order_input_type`` via ``utils/inputs.py::build_lazy_input_annotation``
    # (the 0.0.9 DRY pass). The ForwardRef-wrapped ``Annotated[<runtime str>,
    # strawberry.lazy(...)]`` form is pinned by
    # ``test_filter_input_type_returns_forwardref_in_annotation_args`` (spec-027
    # L7 of rev5) -- the shared helper preserves it.
    return build_lazy_input_annotation(
        filterset_class,
        expected_base=FilterSet,
        family_name="filter_input_type",
        expected_label="a FilterSet",
        ledger=_helper_referenced_filtersets,
        input_type_name_for=_input_type_name_for,
        module_path=INPUTS_MODULE_PATH,
    )


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
