"""Tests for `django_strawberry_framework/filters/base.py` (Slice 1).

Covers the five parity-floor primitives (`TypedFilter`, `ArrayFilter`,
`RangeFilter`, `ListFilter`, `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter`),
the lazy-resolution mixin, and `RelatedFilter`.
"""

from __future__ import annotations

import pytest
from apps.library import models
from django.core.exceptions import ValidationError
from strawberry import relay

from django_strawberry_framework.filters import (
    ArrayFilter,
    ArrayFilterMethod,
    Filter,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    LazyRelatedClassMixin,
    ListFilter,
    RangeField,
    RangeFilter,
    RelatedFilter,
    TypedFilter,
    validate_range,
)
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# TypedFilter
# ---------------------------------------------------------------------------


def test_typed_filter_drops_input_type_property():
    """The Graphene-port `input_type` property is intentionally dropped.

    The Strawberry-side annotation derives from the resolved filter
    instance at materialization time via `convert_filter_to_input_annotation`
    (Slice 2), so the Graphene-only property has no role here.
    """
    f = TypedFilter()
    assert not hasattr(f, "input_type")


def test_typed_filter_does_not_carry_graphene_input_type_attribute():
    """The Graphene-port `_input_type` private slot is also gone."""
    f = TypedFilter()
    assert not hasattr(f, "_input_type")


def test_typed_filter_is_a_django_filter_filter():
    assert issubclass(TypedFilter, Filter)


# ---------------------------------------------------------------------------
# ArrayFilter
# ---------------------------------------------------------------------------


def test_array_filter_treats_empty_list_as_value():
    """`[]` is a real value for `ArrayField`; default filter must run."""
    captured = {}

    class _Qs:
        def distinct(self):
            return self

        def filter(self, **kwargs):
            captured.update(kwargs)
            return self

    f = ArrayFilter(field_name="tags", lookup_expr="exact")
    result = f.filter(_Qs(), [])
    assert isinstance(result, _Qs)
    assert captured == {"tags__exact": []}


def test_array_filter_passes_through_none():
    """`None` is `EMPTY_VALUES`-ish and short-circuits."""
    sentinel = object()
    f = ArrayFilter(field_name="tags")
    # The cookbook returns the original queryset untouched for `None`.
    assert f.filter(sentinel, None) is sentinel


def test_array_filter_method_setter_swaps_in_array_filter_method():
    """A consumer-supplied `method=` callable plugs in `ArrayFilterMethod`."""

    def custom(qs, name, value):
        return ("custom", name, value)

    f = ArrayFilter(field_name="tags", method=custom)
    assert isinstance(f.filter, ArrayFilterMethod)


# ---------------------------------------------------------------------------
# RangeField / RangeFilter
# ---------------------------------------------------------------------------


def test_validate_range_accepts_two_values():
    assert validate_range([1, 2]) is None


def test_validate_range_rejects_single_value():
    with pytest.raises(ValidationError) as excinfo:
        validate_range([1])
    assert excinfo.value.code == "invalid"


def test_validate_range_rejects_three_values():
    with pytest.raises(ValidationError):
        validate_range([1, 2, 3])


def test_range_filter_uses_range_field_class():
    assert RangeFilter.field_class is RangeField


# ---------------------------------------------------------------------------
# ListFilter
# ---------------------------------------------------------------------------


def test_list_filter_returns_qs_none_on_empty_list():
    class _Qs:
        def none(self):
            return "none-sentinel"

    f = ListFilter(field_name="ids")
    assert f.filter(_Qs(), []) == "none-sentinel"


def test_list_filter_returns_qs_when_excluding_on_empty_list():
    class _Qs:
        pass

    qs = _Qs()
    f = ListFilter(field_name="ids", exclude=True)
    assert f.filter(qs, []) is qs


def test_list_filter_defers_to_super_for_nonempty_lists():
    captured = {}

    class _Qs:
        def distinct(self):
            return self

        def filter(self, **kwargs):
            captured.update(kwargs)
            return self

    f = ListFilter(field_name="ids", lookup_expr="in")
    f.filter(_Qs(), [1, 2])
    assert captured == {"ids__in": [1, 2]}


# ---------------------------------------------------------------------------
# GlobalIDFilter
# ---------------------------------------------------------------------------


def test_global_id_filter_decodes_via_strawberry_relay():
    """The decoded `node_id` reaches the underlying `Filter.filter` call."""
    captured = {}

    class _Qs:
        def filter(self, **kwargs):
            captured.update(kwargs)
            return self

    encoded = relay.to_base64("BookType", "42")
    f = GlobalIDFilter(field_name="id", lookup_expr="exact")
    f.filter(_Qs(), encoded)
    assert captured == {"id__exact": "42"}


def test_global_id_filter_passes_through_none():
    captured = {}

    class _Qs:
        def filter(self, **kwargs):
            captured.update(kwargs)
            return self

    f = GlobalIDFilter(field_name="id", lookup_expr="exact")
    # `None` falls through to `Filter.filter`, which short-circuits on EMPTY_VALUES.
    result = f.filter(_Qs(), None)
    assert captured == {}
    assert isinstance(result, _Qs)


def test_global_id_multiple_choice_filter_decodes_every_element():
    """Decoded `node_id`s reach the underlying `MultipleChoiceFilter.filter`."""
    captured: list[list[str]] = []
    real_super_filter = GlobalIDMultipleChoiceFilter.__mro__[1].filter

    def spy(self, qs, value):
        captured.append(list(value))
        return qs

    encoded_one = relay.to_base64("BookType", "1")
    encoded_two = relay.to_base64("BookType", "2")
    GlobalIDMultipleChoiceFilter.__mro__[1].filter = spy
    try:
        f = GlobalIDMultipleChoiceFilter(field_name="id")
        f.filter(object(), [encoded_one, encoded_two])
    finally:
        GlobalIDMultipleChoiceFilter.__mro__[1].filter = real_super_filter
    assert captured == [["1", "2"]]


# ---------------------------------------------------------------------------
# LazyRelatedClassMixin
# ---------------------------------------------------------------------------


class _SampleClass:
    """Throw-away target for the lazy-resolution callable branch."""


def test_lazy_related_class_mixin_resolves_absolute_path():
    mixin = LazyRelatedClassMixin()
    resolved = mixin.resolve_lazy_class(
        "tests.filters.fixtures.filtersets.ShelfFilter",
        None,
    )
    from tests.filters.fixtures.filtersets import ShelfFilter

    assert resolved is ShelfFilter


def test_lazy_related_class_mixin_falls_back_to_bound_module():
    mixin = LazyRelatedClassMixin()
    from tests.filters.fixtures.filtersets import BranchFilter, ShelfFilter

    resolved = mixin.resolve_lazy_class("ShelfFilter", BranchFilter)
    assert resolved is ShelfFilter


def test_lazy_related_class_mixin_returns_class_as_is():
    mixin = LazyRelatedClassMixin()
    assert mixin.resolve_lazy_class(_SampleClass, None) is _SampleClass


def test_lazy_related_class_mixin_invokes_callable_factory():
    mixin = LazyRelatedClassMixin()
    instance = mixin.resolve_lazy_class(lambda: _SampleClass(), None)
    assert isinstance(instance, _SampleClass)


def test_lazy_related_class_mixin_raises_when_unresolved_string_has_no_bound_class():
    mixin = LazyRelatedClassMixin()
    with pytest.raises(ImportError):
        mixin.resolve_lazy_class("definitely.not.a.module.ClassName", None)


# ---------------------------------------------------------------------------
# RelatedFilter
# ---------------------------------------------------------------------------


def test_related_filter_accepts_class_argument():
    from tests.filters.fixtures.filtersets import ShelfFilter

    f = RelatedFilter(ShelfFilter)
    assert f._filterset is ShelfFilter


def test_related_filter_accepts_absolute_path_argument():
    f = RelatedFilter("tests.filters.fixtures.filtersets.ShelfFilter")
    assert f._filterset == "tests.filters.fixtures.filtersets.ShelfFilter"


def test_related_filter_accepts_unqualified_name_argument():
    f = RelatedFilter("ShelfFilter")
    assert f._filterset == "ShelfFilter"


def test_related_filter_bind_filterset_sets_bound_filterset():
    f = RelatedFilter("ShelfFilter")

    class _A:
        pass

    class _B:
        pass

    f.bind_filterset(_A)
    assert f.bound_filterset is _A
    f.bind_filterset(_B)
    # Idempotent: a second `bind_filterset` is a no-op.
    assert f.bound_filterset is _A


def test_related_filter_filterset_property_resolves_lazy_string():
    from tests.filters.fixtures.filtersets import BranchFilterByString, ShelfFilter

    rel = BranchFilterByString.related_filters["shelves"]
    assert rel.filterset is ShelfFilter


def test_related_filter_filterset_property_resolves_absolute_path():
    from tests.filters.fixtures.filtersets import BranchFilterByPath, ShelfFilter

    rel = BranchFilterByPath.related_filters["shelves"]
    assert rel.filterset is ShelfFilter


def test_related_filter_get_queryset_auto_derives_from_target_model():
    from tests.filters.fixtures.filtersets import BranchFilter

    rel = BranchFilter.related_filters["shelves"]
    qs = rel.get_queryset(request=None)
    assert qs.model is models.Shelf


def test_related_filter_get_queryset_honors_explicit_queryset():
    from tests.filters.fixtures.filtersets import ShelfFilter

    explicit_qs = models.Shelf.objects.filter(code="topic-A")
    f = RelatedFilter(ShelfFilter, queryset=explicit_qs)
    # Constructor records the explicit-queryset ledger entry.
    assert f._has_explicit_queryset is True
    assert f.get_queryset(request=None) is explicit_qs


def test_related_filter_explicit_queryset_ledger_defaults_false_when_absent():
    f = RelatedFilter("ShelfFilter")
    assert f._has_explicit_queryset is False
