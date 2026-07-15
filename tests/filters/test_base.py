"""Filter primitive tests for typed, list, range, global-ID, and related filters.

Covers the five parity-floor primitives (`TypedFilter`, `ArrayFilter`,
`RangeFilter`, `ListFilter`, `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter`),
the lazy-resolution mixin, and `RelatedFilter`.
"""

from __future__ import annotations

import pytest
from apps.library import models
from django.core.exceptions import ValidationError
from django.http import QueryDict
from graphql import GraphQLError
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
    IntegerRangeFilter,
    _accepted_globalid_type_names,
    _decode_and_validate_global_id,
    _target_definition_for,
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
# IntegerRangeFilter
# ---------------------------------------------------------------------------


def test_integer_range_filter_decomposes_range_into_gte_lte():
    """A two-bound range applies a single ``gte`` + ``lte`` predicate, never a raw
    ``__range`` (``BETWEEN``) bind - so each bound flows through Django's range-aware
    integer lookup instead of overflowing the backend on an out-of-range value.
    """
    captured = {}

    class _Qs:
        def filter(self, **kwargs):
            captured.update(kwargs)
            return self

    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range")
    result = f.filter(_Qs(), [1, 100])
    assert isinstance(result, _Qs)
    assert captured == {"signed_big__gte": 1, "signed_big__lte": 100}


def test_integer_range_filter_excludes_via_negated_conjunction():
    """Under ``exclude=True`` the decomposed pair is applied through ``qs.exclude`` -
    the exact complement of ``NOT (col BETWEEN a AND b)``.
    """
    captured = {}

    class _Qs:
        def exclude(self, **kwargs):
            captured.update(kwargs)
            return self

    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range", exclude=True)
    f.filter(_Qs(), [1, 100])
    assert captured == {"signed_big__gte": 1, "signed_big__lte": 100}


def test_integer_range_filter_passes_through_empty_value():
    """An empty / ``None`` range keeps django-filter's skip (no bounds supplied)."""
    sentinel = object()
    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range")
    assert f.filter(sentinel, None) is sentinel


def test_integer_range_filter_applies_distinct_when_flagged():
    """``IntegerRangeFilter.filter`` calls ``.distinct()`` when ``distinct=True``."""
    calls = {"distinct": 0}

    class _Qs:
        def distinct(self):
            calls["distinct"] += 1
            return self

        def filter(self, **kwargs):
            calls["filter_kwargs"] = kwargs
            return self

    f = IntegerRangeFilter(field_name="signed_big", lookup_expr="range", distinct=True)
    result = f.filter(_Qs(), [1, 100])
    assert isinstance(result, _Qs)
    assert calls["distinct"] == 1
    assert calls["filter_kwargs"] == {"signed_big__gte": 1, "signed_big__lte": 100}


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


def test_global_id_multiple_choice_field_distinguishes_absent_from_explicit_empty():
    """Form cleaning keeps omission as ``None`` and a supplied empty list as ``[]``."""
    field = GlobalIDMultipleChoiceFilter(field_name="id").field

    absent = field.widget.value_from_datadict(QueryDict(), {}, "id")
    explicit_empty = field.widget.value_from_datadict({"id": []}, {}, "id")

    assert field.clean(absent) is None
    assert field.clean(explicit_empty) == []


def test_global_id_multiple_choice_field_omission_still_enforces_required():
    """Preserving ``None`` must not bypass Django's required-field validation."""
    field = GlobalIDMultipleChoiceFilter(field_name="id", required=True).field
    absent = field.widget.value_from_datadict(QueryDict(), {}, "id")

    with pytest.raises(ValidationError, match="required"):
        field.clean(absent)


def test_global_id_multiple_choice_filter_empty_in_matches_nothing_like_list_filter():
    class _Qs:
        def none(self):
            return "none-sentinel"

    qs = _Qs()
    global_ids = GlobalIDMultipleChoiceFilter(field_name="id", lookup_expr="in")
    list_filter = ListFilter(field_name="id", lookup_expr="in")

    assert global_ids.filter(qs, []) == "none-sentinel"
    assert list_filter.filter(qs, []) == "none-sentinel"


def test_global_id_multiple_choice_filter_empty_exact_matches_nothing_like_list_filter():
    """Empty membership is match-nothing for non-``in`` lookups too.

    Many-side Relay relations resolve to ``GlobalIDMultipleChoiceFilter`` with
    ``lookup_expr="exact"`` (django-filter's default). Upstream
    ``MultipleChoiceFilter.filter`` short-circuits ``if not value: return qs``,
    which would silently widen ``exact: []`` to no constraint. The empty-set
    contract must not be ``in``-only.
    """

    class _Qs:
        def none(self):
            return "none-sentinel"

    qs = _Qs()
    # Default lookup_expr is ``exact`` (settings.DEFAULT_LOOKUP_EXPR).
    global_ids = GlobalIDMultipleChoiceFilter(field_name="genres")
    list_filter = ListFilter(field_name="genres", lookup_expr="exact")

    assert global_ids.lookup_expr == "exact"
    assert global_ids.filter(qs, []) == "none-sentinel"
    assert list_filter.filter(qs, []) == "none-sentinel"


def test_global_id_multiple_choice_filter_empty_excluded_in_matches_everything():
    class _Qs:
        pass

    qs = _Qs()
    f = GlobalIDMultipleChoiceFilter(field_name="id", lookup_expr="in", exclude=True)

    assert f.filter(qs, []) is qs


def test_global_id_multiple_choice_filter_empty_excluded_exact_matches_everything():
    """Exclude + empty membership is the complement of match-nothing: every row."""

    class _Qs:
        pass

    qs = _Qs()
    f = GlobalIDMultipleChoiceFilter(field_name="genres", lookup_expr="exact", exclude=True)

    assert f.filter(qs, []) is qs


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
# Strategy-aware GlobalID validation (spec-031 Decision 13) - owner/target
# definition resolution + per-strategy accepted-type-name set.
# ---------------------------------------------------------------------------


class _FakePk:
    name = "id"


class _FakeMeta:
    pk = _FakePk()
    label_lower = "owner.ownermodel"


class _FakeModel:
    _meta = _FakeMeta()


class _FakeTargetMeta:
    pk = _FakePk()
    label_lower = "library.genre"


class _FakeTargetModel:
    _meta = _FakeTargetMeta()


class _FakeTargetDefinition:
    graphql_type_name = "GenreType"
    model = _FakeTargetModel()

    def __init__(self, effective_globalid_strategy="model"):
        self.effective_globalid_strategy = effective_globalid_strategy


class _FakeOwnerDefinition:
    model = _FakeModel()
    graphql_type_name = "OwnerType"

    def __init__(self, target, effective_globalid_strategy="model"):
        self._target = target
        self.effective_globalid_strategy = effective_globalid_strategy

    def related_target_for(self, head):
        return self._target


class _FakeParent:
    def __init__(self, owner):
        self._owner_definition = owner


def _global_id_filter_with_owner(field_name, owner):
    f = GlobalIDFilter(field_name=field_name)
    f.parent = _FakeParent(owner)
    return f


def test_target_definition_for_returns_none_without_owner():
    """No bound owner -> no definition (node-id-only fallback in unit contexts)."""
    f = GlobalIDFilter(field_name="id")
    f.parent = _FakeParent(None)
    assert _target_definition_for(f) is None


def test_target_definition_for_own_pk_branch():
    """When the field is the owner's PK, the owner definition itself is returned."""
    owner = _FakeOwnerDefinition(target=None)
    f = _global_id_filter_with_owner("id", owner)
    assert _target_definition_for(f) is owner


def test_target_definition_for_relation_branch():
    """A relation head resolves through `related_target_for` to the target definition."""
    target_def = _FakeTargetDefinition()
    owner = _FakeOwnerDefinition(target=(target_def, object()))
    f = _global_id_filter_with_owner("genres__id", owner)
    assert _target_definition_for(f) is target_def


def test_target_definition_for_relation_branch_unresolved_target():
    """An unresolvable relation head returns `None` (decode without validation)."""
    owner = _FakeOwnerDefinition(target=None)
    f = _global_id_filter_with_owner("genres__id", owner)
    assert _target_definition_for(f) is None


def test_accepted_globalid_type_names_none_definition():
    """No definition -> `None` (node-id-only fallback)."""
    assert _accepted_globalid_type_names(None) is None


def test_accepted_globalid_type_names_per_strategy():
    """Each framework strategy maps to its accepted `type_name` payload set."""
    model_owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy="model")
    type_owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy="type")
    both_owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy="type+model")
    assert _accepted_globalid_type_names(model_owner) == {"owner.ownermodel"}
    assert _accepted_globalid_type_names(type_owner) == {"OwnerType"}
    assert _accepted_globalid_type_names(both_owner) == {"owner.ownermodel", "OwnerType"}


@pytest.mark.parametrize("strategy", ["callable", "custom", None])
def test_accepted_globalid_type_names_node_id_only_strategies(strategy):
    """`callable` / `custom` / absent strategy -> `None` (node-id-only fallback)."""
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy=strategy)
    assert _accepted_globalid_type_names(owner) is None


def test_filter_model_strategy_accepts_model_label():
    """Under `model`, an own-PK filter accepts the model-label payload."""
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy="model")
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("owner.ownermodel", "42")
    assert _decode_and_validate_global_id(encoded, f) == "42"


def test_filter_model_strategy_accepts_predecoded_global_id():
    """The filter accepts Strawberry's already-coerced ``GlobalID`` value unchanged."""
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy="model")
    f = _global_id_filter_with_owner("id", owner)

    assert _decode_and_validate_global_id(relay.GlobalID("owner.ownermodel", "42"), f) == "42"


def test_filter_model_strategy_rejects_type_name():
    """Under `model`, the old bare GraphQL type name is rejected."""
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy="model")
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("OwnerType", "42")
    with pytest.raises(GraphQLError, match="GlobalID type mismatch"):
        _decode_and_validate_global_id(encoded, f)


def test_filter_type_strategy_accepts_graphql_name():
    """`type` preserves the pre-0.0.9 `graphql_type_name` acceptance."""
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy="type")
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("OwnerType", "7")
    assert _decode_and_validate_global_id(encoded, f) == "7"
    # And rejects a model-label payload under `type`.
    with pytest.raises(GraphQLError, match="GlobalID type mismatch"):
        _decode_and_validate_global_id(relay.to_base64("owner.ownermodel", "7"), f)


def test_filter_type_plus_model_accepts_both():
    """`type+model` accepts model-label AND type-name inputs."""
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy="type+model")
    f = _global_id_filter_with_owner("id", owner)
    assert _decode_and_validate_global_id(relay.to_base64("owner.ownermodel", "1"), f) == "1"
    assert _decode_and_validate_global_id(relay.to_base64("OwnerType", "2"), f) == "2"


@pytest.mark.parametrize("strategy", ["callable", "custom", None])
def test_filter_callable_custom_node_id_only(strategy):
    """`callable` / `custom` / absent-strategy types fall back to node-id-only.

    The `type_name` guard is skipped, so even a payload that matches no
    framework shape decodes to its `node_id` without raising.
    """
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy=strategy)
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("AnythingAtAll", "99")
    assert _decode_and_validate_global_id(encoded, f) == "99"


def test_filter_unbound_owner_node_id_only():
    """No bound owner -> node-id-only fallback (the existing `None`-definition path)."""
    f = GlobalIDFilter(field_name="id")
    f.parent = _FakeParent(None)
    encoded = relay.to_base64("WhateverType", "5")
    assert _decode_and_validate_global_id(encoded, f) == "5"


def test_filter_wrong_model_rejected():
    """A wrong-model GlobalID is still rejected for a framework strategy."""
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy="model")
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("other.thing", "42")
    with pytest.raises(GraphQLError, match="GlobalID type mismatch"):
        _decode_and_validate_global_id(encoded, f)


def test_related_filter_relation_branch_strategy_aware():
    """A relation-branch (target-definition) filter applies the target's strategy."""
    target_def = _FakeTargetDefinition(effective_globalid_strategy="model")
    owner = _FakeOwnerDefinition(target=(target_def, object()))
    f = _global_id_filter_with_owner("genres__id", owner)
    # The target's model label is accepted; the target's type name is rejected.
    assert _decode_and_validate_global_id(relay.to_base64("library.genre", "3"), f) == "3"
    with pytest.raises(GraphQLError, match="GlobalID type mismatch"):
        _decode_and_validate_global_id(relay.to_base64("GenreType", "3"), f)


def test_multi_value_filter_strategy_aware_indexes_rejection(monkeypatch):
    """`GlobalIDMultipleChoiceFilter` routes through the strategy-aware check.

    A wrong-shape element names its index in the rejection message; a
    well-shaped batch decodes the model-label payloads through to the upstream
    filter. Spies on the upstream ``MultipleChoiceFilter.filter`` (same pattern
    as ``test_global_id_multiple_choice_filter_decodes_every_element``) so the
    real ``Q``-object filter machinery does not run.
    """
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy="model")
    captured: list[list[str]] = []

    def spy(self, qs, value):
        captured.append(list(value))
        return qs

    monkeypatch.setattr(GlobalIDMultipleChoiceFilter.__mro__[1], "filter", spy)

    accepted = GlobalIDMultipleChoiceFilter(field_name="id")
    accepted.parent = _FakeParent(owner)
    accepted.filter(
        object(),
        [relay.to_base64("owner.ownermodel", "1"), relay.to_base64("owner.ownermodel", "2")],
    )
    assert captured == [["1", "2"]]

    rejected = GlobalIDMultipleChoiceFilter(field_name="id")
    rejected.parent = _FakeParent(owner)
    with pytest.raises(GraphQLError, match="at index 1"):
        rejected.filter(
            object(),
            [relay.to_base64("owner.ownermodel", "1"), relay.to_base64("OwnerType", "2")],
        )
