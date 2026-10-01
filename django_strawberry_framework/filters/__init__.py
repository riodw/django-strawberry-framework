"""Filtering subsystem - declarative ``FilterSet`` classes that become GraphQL ``filter:`` arguments.

Re-exports the foundational primitives from `base.py`, the `FilterSet`
+ `FilterSetMetaclass` pair from `sets.py`, and the spec-027 Decision 11
consumer helper in its two spellings: the type-checkable annotation
`FilterInput[MyFilter]` and the call `filter_input_type(MyFilter)`. The
finalizer's phase 2.5 wires the orphan check that compares
`_helper_referenced_filtersets` against the set of
`Meta.filterset_class`-wired filtersets.

Note: `Filter` re-exported here IS `django_filters.Filter` itself (a
plain re-export, not a subclass), surfaced under this package's namespace
so consumers writing a custom `method=` filter import one base class from
`django_strawberry_framework.filters`. It deliberately shadows the
upstream name; reach for `django_filters.Filter` directly only if you
need to distinguish the two.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from django_filters import Filter

from ..registry import register_subsystem_clear
from ..utils.inputs import build_lazy_input_annotation
from .base import (
    ArrayFilter,
    ArrayFilterMethod,
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

# Ledger of `FilterSet`s referenced through the spec-027 Decision 11
# consumer helper (`FilterInput[...]` or `filter_input_type(...)`). Cleared via the
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


def _filter_input_annotation(filterset_class: object, *, helper_spelling: str) -> object:
    """Validate, ledger-record and annotate ``filterset_class`` for either helper spelling."""
    # spec-027 Decision 11 consumer-helper body shared with ``orders/__init__.py::
    # _order_input_annotation`` via ``utils/inputs.py::build_lazy_input_annotation``
    # The ForwardRef-wrapped ``Annotated[<runtime str>,
    # strawberry.lazy(...)]`` form is pinned by
    # ``test_filter_input_type_returns_forwardref_in_annotation_args`` -- the
    # shared helper preserves it.
    return build_lazy_input_annotation(
        filterset_class,
        expected_base=FilterSet,
        helper_spelling=helper_spelling,
        expected_label="a FilterSet",
        ledger=_helper_referenced_filtersets,
        input_type_name_for=_input_type_name_for,
        module_path=INPUTS_MODULE_PATH,
    )


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
    return _filter_input_annotation(filterset_class, helper_spelling="filter_input_type()")


_FilterSetT = TypeVar("_FilterSetT", bound=FilterSet)


class FilterInput(Generic[_FilterSetT]):
    """Type-checkable annotation for a resolver's ``filter:`` argument.

    ``FilterInput[MyFilter]`` evaluates to exactly what
    ``filter_input_type(MyFilter)`` returns (same ``TypeError`` for a
    non-``FilterSet``, same ledger entry for the finalizer's orphan check),
    so Strawberry builds the identical ``filter: MyFilterInputType``
    argument. A call is not a valid type expression, so a type checker
    rejects ``filter_input_type(MyFilter)`` in an annotation; it reads this
    spelling as a generic class whose parameter is bound to ``FilterSet``,
    and rejects ``FilterInput[NotAFilterSet]`` statically::

        def books(
            self,
            info: strawberry.Info,
            filter: FilterInput[BookFilter] | None = None,
        ) -> ...: ...

    The value the resolver receives is the generated Strawberry input
    object, not a ``FilterInput`` instance. To the type checker it is an
    opaque handle whose one use is ``BookFilter.apply_sync(filter, queryset,
    info)`` / ``apply_async`` (their ``input_value`` parameter is
    ``object``); read no attributes from it. The class is never instantiated.
    """

    def __class_getitem__(cls, filterset_class: object) -> object:
        """Return the ``filter_input_type(filterset_class)`` annotation.

        Raises:
            TypeError: ``filterset_class`` is not a ``FilterSet`` subclass.
        """
        return _filter_input_annotation(filterset_class, helper_spelling="FilterInput[...]")


__all__: tuple[str, ...] = (
    "ArrayFilter",
    "ArrayFilterMethod",
    "Filter",
    "FilterInput",
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
