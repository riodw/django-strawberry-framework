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
    ListFilterMethod,
    RangeField,
    RangeFilter,
    RelatedFilter,
    TypedFilter,
    validate_range,
)
from django_strawberry_framework.filters.base import (
    _expected_global_id_type_name,
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
        validate_range(
            [1, 2, 3],
        )


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


def test_global_id_multiple_choice_filter_decodes_every_element(monkeypatch):
    """Decoded `node_id`s reach the underlying `MultipleChoiceFilter.filter`."""
    captured: list[list[str]] = []

    def spy(self, qs, value):
        captured.append(list(value))
        return qs

    encoded_one = relay.to_base64("BookType", "1")
    encoded_two = relay.to_base64("BookType", "2")
    # Spy on the upstream ``MultipleChoiceFilter.filter`` via the bound
    # parent class. ``monkeypatch`` auto-restores on teardown (xdist-safe
    # and exception-safe) instead of the prior manual try/finally that
    # wrote through to the upstream class.
    monkeypatch.setattr(GlobalIDMultipleChoiceFilter.__mro__[1], "filter", spy)
    f = GlobalIDMultipleChoiceFilter(field_name="id")
    f.filter(object(), [encoded_one, encoded_two])
    assert captured == [["1", "2"]]


def test_global_id_multiple_choice_filter_passes_through_none():
    captured = {}

    class _Qs:
        def filter(self, **kwargs):
            captured.update(kwargs)
            return self

    f = GlobalIDMultipleChoiceFilter(field_name="id")
    result = f.filter(_Qs(), None)
    assert captured == {}
    assert isinstance(result, _Qs)


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


def test_related_filter_rejects_lookups_kwarg():
    """The cookbook-port `lookups=` kwarg is dropped; nothing read it.

    Pinning: passing `lookups=` to `RelatedFilter.__init__` must raise
    `TypeError` (unexpected keyword argument). Equivalent shape would be to
    confirm `"lookups"` is absent from `inspect.signature(RelatedFilter)`,
    but the runtime call is the consumer-facing contract.
    """
    with pytest.raises(TypeError):
        RelatedFilter("ShelfFilter", lookups=["exact", "in"])


def test_related_filter_filterset_setter_substitutes_target():
    """The `filterset` setter swaps the resolved target class in place."""
    from tests.filters.fixtures.filtersets import BranchFilter, ShelfFilter

    rel = RelatedFilter("ShelfFilter")
    # Setter stores the substituted class on `_filterset`.
    rel.filterset = BranchFilter
    assert rel._filterset is BranchFilter
    # Getter resolves the (already-concrete) class as-is and re-stores it.
    assert rel.filterset is BranchFilter
    # A second substitution is honored.
    rel.filterset = ShelfFilter
    assert rel.filterset is ShelfFilter


# ---------------------------------------------------------------------------
# ArrayFilterMethod / ListFilterMethod __call__ dispatch
# ---------------------------------------------------------------------------


def test_array_filter_method_call_passes_through_none():
    """`ArrayFilterMethod.__call__` returns the queryset untouched for `None`."""

    def custom(qs, name, value):
        return ("custom", name, value)

    sentinel = object()
    f = ArrayFilter(field_name="tags", method=custom)
    assert isinstance(f.filter, ArrayFilterMethod)
    assert f.filter(sentinel, None) is sentinel


def test_array_filter_method_call_dispatches_to_custom_method():
    """A non-`None` value reaches the consumer callable with `(qs, field_name, value)`."""

    def custom(qs, name, value):
        return ("custom", name, value)

    f = ArrayFilter(field_name="tags", method=custom)
    assert f.filter("qs-sentinel", [1, 2]) == ("custom", "tags", [1, 2])


def test_list_filter_method_setter_swaps_in_list_filter_method():
    """A consumer-supplied `method=` callable plugs in `ListFilterMethod`."""

    def custom(qs, name, value):
        return qs

    f = ListFilter(field_name="ids", method=custom)
    assert isinstance(f.filter, ListFilterMethod)


def test_list_filter_method_call_passes_through_none():
    """`ListFilterMethod.__call__` returns the queryset untouched for `None`."""

    def custom(qs, name, value):
        return ("custom", name, value)

    sentinel = object()
    f = ListFilter(field_name="ids", method=custom)
    assert f.filter(sentinel, None) is sentinel


def test_list_filter_method_call_dispatches_to_custom_method():
    """A non-`None` value reaches the consumer callable with `(qs, field_name, value)`."""

    def custom(qs, name, value):
        return ("custom", name, value)

    f = ListFilter(field_name="ids", method=custom)
    assert f.filter("qs-sentinel", [1, 2]) == ("custom", "ids", [1, 2])


def test_array_filter_applies_distinct_when_flagged():
    """`ArrayFilter.filter` calls `.distinct()` when the filter is `distinct=True`."""
    calls = {"distinct": 0}

    class _Qs:
        def distinct(self):
            calls["distinct"] += 1
            return self

        def filter(self, **kwargs):
            calls["filter_kwargs"] = kwargs
            return self

    f = ArrayFilter(field_name="tags", lookup_expr="exact", distinct=True)
    result = f.filter(_Qs(), [1])
    assert isinstance(result, _Qs)
    assert calls["distinct"] == 1
    assert calls["filter_kwargs"] == {"tags__exact": [1]}


# ---------------------------------------------------------------------------
# _expected_global_id_type_name — owner-aware GlobalID type-name resolution
# ---------------------------------------------------------------------------


class _FakePk:
    name = "id"


class _FakeMeta:
    pk = _FakePk()


class _FakeModel:
    _meta = _FakeMeta()


class _FakeTargetDefinition:
    graphql_type_name = "GenreType"


class _FakeOwnerDefinition:
    model = _FakeModel()
    graphql_type_name = "OwnerType"

    def __init__(self, target):
        self._target = target

    def related_target_for(self, head):
        return self._target


class _FakeParent:
    def __init__(self, owner):
        self._owner_definition = owner


def _global_id_filter_with_owner(field_name, owner):
    f = GlobalIDFilter(field_name=field_name)
    f.parent = _FakeParent(owner)
    return f


def test_expected_global_id_type_name_returns_none_without_owner():
    """No bound owner → no type-name validation (Slice-1/2 unit contexts)."""
    f = GlobalIDFilter(field_name="id")
    f.parent = _FakeParent(None)
    assert _expected_global_id_type_name(f) is None


def test_expected_global_id_type_name_own_pk_branch():
    """When the field is the owner's PK, the owner's own type name is returned."""
    owner = _FakeOwnerDefinition(target=None)
    f = _global_id_filter_with_owner("id", owner)
    assert _expected_global_id_type_name(f) == "OwnerType"


def test_expected_global_id_type_name_relation_branch():
    """A relation head resolves through `related_target_for` to the target's type name."""
    owner = _FakeOwnerDefinition(target=(_FakeTargetDefinition(), object()))
    f = _global_id_filter_with_owner("genres__id", owner)
    assert _expected_global_id_type_name(f) == "GenreType"


def test_expected_global_id_type_name_relation_branch_unresolved_target():
    """An unresolvable relation head returns `None` (decode without validation)."""
    owner = _FakeOwnerDefinition(target=None)
    f = _global_id_filter_with_owner("genres__id", owner)
    assert _expected_global_id_type_name(f) is None
