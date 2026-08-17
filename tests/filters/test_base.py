"""Filter primitive tests for typed, list, range, global-ID, and related filters.

Covers the five parity-floor primitives (`TypedFilter`, `ArrayFilter`,
`RangeFilter`, `ListFilter`, `GlobalIDFilter` / `GlobalIDMultipleChoiceFilter`),
the lazy-resolution mixin, and `RelatedFilter`.
"""

from __future__ import annotations

import pytest
from apps.library import models
from django.core.exceptions import ValidationError
from django.db import connection
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
    _GLOBALID_RELATION_PK_ATTR,
    IntegerRangeFilter,
    _accepted_globalid_type_names,
    _decode_and_validate_global_id,
    _relation_uses_non_pk_to_field,
    _target_definition_for,
)
from django_strawberry_framework.registry import registry
from tests._relation_fixtures import (
    RpToFieldChild,
    RpToFieldTarget,
    relation_fixture_tables,
)


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
    instance at materialization time via `convert_filter_to_input_annotation`,
    so the Graphene-only property has no role here.
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


@pytest.mark.parametrize("value", [iter(["not-a-global-id"]), object(), "not-a-list"])
def test_global_id_multiple_choice_filter_rejects_malformed_container(value):
    """Malformed direct inputs fail as coded GraphQL errors, not leaked ``TypeError``."""
    f = GlobalIDMultipleChoiceFilter(field_name="id", lookup_expr="in")

    with pytest.raises(GraphQLError, match="expected a list of GlobalIDs") as exc_info:
        f.filter(object(), value)

    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


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
# A crafted empty-id GlobalID (well-typed, empty node part) is a REJECTED input,
# not a silent no-op. ``to_base64(type, "")`` decodes to ``node_id == ""``
# and clears decode + strategy + type-name validation, but an empty identifier is
# not a valid resource id: the shared ``_decode_and_validate_global_id`` boundary
# raises ``GLOBALID_INVALID`` (naming the list index when present) so a client can
# no longer widen a restrictive membership predicate by supplying ``type:``. An
# explicit ``[]`` (match-none) and a ``None`` value (omission) remain non-error
# paths and are asserted separately.
# ---------------------------------------------------------------------------


class _CapturingQs:
    """Predicate-capturing stub: records ``filter`` kwargs, no database needed."""

    def __init__(self):
        self.captured = {}

    def distinct(self):
        return self

    def filter(self, **kwargs):
        self.captured.update(kwargs)
        return self


def test_global_id_multiple_choice_filter_all_empty_node_id_list_rejects():
    """An all-vacuous ``in`` list rejects with ``GLOBALID_INVALID`` (no silent widen)."""
    f = GlobalIDMultipleChoiceFilter(field_name="genres", lookup_expr="in")
    with pytest.raises(GraphQLError, match="empty node id") as exc_info:
        f.filter(object(), [relay.to_base64("GenreType", "")])
    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}
    assert "at index 0" in str(exc_info.value)


def test_global_id_multiple_choice_filter_empty_node_id_exact_path_rejects():
    """The same reject covers the non-``in`` (per-element) path."""
    f = GlobalIDMultipleChoiceFilter(field_name="genres", lookup_expr="exact")
    with pytest.raises(GraphQLError, match="empty node id") as exc_info:
        f.filter(object(), [relay.to_base64("GenreType", "")])
    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


def test_global_id_multiple_choice_filter_mixed_empty_and_real_rejects_naming_index():
    """A vacuous element alongside a real id rejects the WHOLE input, naming its index.

    A mixed list must reject like malformed / wrong-type inputs do -- never
    silently ignore the empty element while accepting the rest -- and the offending
    index is named so the client can identify it.
    """
    f = GlobalIDMultipleChoiceFilter(field_name="genres", lookup_expr="in")
    encoded = [relay.to_base64("GenreType", "5"), relay.to_base64("GenreType", "")]
    with pytest.raises(GraphQLError, match="at index 1") as exc_info:
        f.filter(object(), encoded)
    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


def test_global_id_multiple_choice_filter_well_formed_list_still_applies_predicate():
    """Regression: a well-formed non-empty ``in`` list still yields the whole-list predicate.

    Removing the empty-stripping block must not disturb the normal path -- a list
    of real ids compiles the byte-identical ``{field__in: node_ids}`` predicate.
    """
    qs = _CapturingQs()
    f = GlobalIDMultipleChoiceFilter(field_name="genres", lookup_expr="in")
    encoded = [relay.to_base64("GenreType", "5"), relay.to_base64("GenreType", "9")]
    f.filter(qs, encoded)
    assert qs.captured == {"genres__in": ["5", "9"]}


# ---------------------------------------------------------------------------
# GlobalID relation filtering against a non-pk ``to_field``
# ---------------------------------------------------------------------------


def test_relation_uses_non_pk_to_field_true_for_to_field_fk():
    """A forward FK bound on a non-pk ``to_field`` (``target`` -> ``code``) is flagged."""
    field = RpToFieldChild._meta.get_field("target")
    assert _relation_uses_non_pk_to_field(field) is True


def test_relation_uses_non_pk_to_field_false_for_ordinary_fk_to_pk():
    """An ordinary FK whose target field IS the related pk is not flagged."""
    field = models.Book._meta.get_field("shelf")
    assert _relation_uses_non_pk_to_field(field) is False


def test_relation_uses_non_pk_to_field_false_for_m2m():
    """A ``ManyToManyField`` (non-concrete) is not flagged."""
    field = models.Book._meta.get_field("genres")
    assert _relation_uses_non_pk_to_field(field) is False


def test_relation_uses_non_pk_to_field_false_for_reverse_relation():
    """A reverse relation object (non-concrete) is not flagged."""
    field = models.Book._meta.get_field("loans")
    assert _relation_uses_non_pk_to_field(field) is False


def test_relation_uses_non_pk_to_field_false_for_non_relation():
    """A plain scalar column is not flagged."""
    field = models.Book._meta.get_field("title")
    assert _relation_uses_non_pk_to_field(field) is False


@pytest.mark.django_db(transaction=True)
def test_global_id_filter_non_pk_to_field_matches_by_target_pk():
    """A marked forward-FK GlobalID filter compiles against the target's pk.

    The Relay GlobalID carries the target's PRIMARY KEY, but the FK stores /
    joins on ``code``. The pk-qualified predicate (``target__pk``) returns
    exactly the children of the encoded target, whereas the OLD unqualified
    predicate (``target=<pk>``) compares the PK value against the stored
    ``code`` column and matches nothing -- the red->green proof that
    ``pk != code`` matters.
    """
    with relation_fixture_tables(connection):
        alpha = RpToFieldTarget.objects.create(code="ALPHA", label="A")
        beta = RpToFieldTarget.objects.create(code="BETA", label="B")
        RpToFieldChild.objects.create(target=alpha, name="a-child")
        RpToFieldChild.objects.create(target=beta, name="b-child")

        assert alpha.pk != alpha.code
        encoded = relay.to_base64("RpToFieldTargetType", str(alpha.pk))

        f = GlobalIDFilter(field_name="target", lookup_expr="exact")
        # Boolean flag: ``filter`` derives ``f"{field_name}__pk"`` == "target__pk".
        setattr(f, _GLOBALID_RELATION_PK_ATTR, True)
        result = f.filter(RpToFieldChild.objects.all(), encoded)
        assert set(result.values_list("name", flat=True)) == {"a-child"}

        # The old/unqualified predicate compared the pk value against the stored
        # ``code`` column and returned the WRONG (empty) result.
        wrong = RpToFieldChild.objects.filter(target__exact=str(alpha.pk))
        assert wrong.count() == 0


@pytest.mark.django_db(transaction=True)
def test_global_id_multiple_choice_filter_non_pk_to_field_union_by_pk():
    """A marked multi-choice ``in`` filter unions both targets' children by pk."""
    with relation_fixture_tables(connection):
        alpha = RpToFieldTarget.objects.create(code="ALPHA", label="A")
        beta = RpToFieldTarget.objects.create(code="BETA", label="B")
        gamma = RpToFieldTarget.objects.create(code="GAMMA", label="G")
        RpToFieldChild.objects.create(target=alpha, name="a-child")
        RpToFieldChild.objects.create(target=beta, name="b-child")
        RpToFieldChild.objects.create(target=gamma, name="g-child")

        encoded = [
            relay.to_base64("RpToFieldTargetType", str(alpha.pk)),
            relay.to_base64("RpToFieldTargetType", str(beta.pk)),
        ]
        f = GlobalIDMultipleChoiceFilter(field_name="target", lookup_expr="in")
        # Boolean flag: ``filter`` derives ``f"{field_name}__pk"`` == "target__pk".
        setattr(f, _GLOBALID_RELATION_PK_ATTR, True)
        result = f.filter(RpToFieldChild.objects.all(), encoded)
        assert set(result.values_list("name", flat=True)) == {"a-child", "b-child"}

        # The old/unqualified ``target__in`` compared the pk values against the
        # stored ``code`` column and matched nothing.
        wrong = RpToFieldChild.objects.filter(target__in=[str(alpha.pk), str(beta.pk)])
        assert wrong.count() == 0


def test_global_id_filter_fk_to_pk_predicate_is_byte_identical():
    """Without the marker, the predicate is the unchanged ``{field__lookup: node_id}``."""
    captured = {}

    class _Qs:
        def filter(self, **kwargs):
            captured.update(kwargs)
            return self

    encoded = relay.to_base64("ShelfType", "7")
    f = GlobalIDFilter(field_name="shelf", lookup_expr="exact")
    assert getattr(f, _GLOBALID_RELATION_PK_ATTR, False) is not True
    f.filter(_Qs(), encoded)
    assert captured == {"shelf__exact": "7"}


def test_global_id_multiple_choice_filter_in_predicate_is_byte_identical():
    """Without the marker, the ``in`` predicate keeps the raw whole-list form."""
    captured = {}

    class _Qs:
        def distinct(self):
            return self

        def filter(self, **kwargs):
            captured.update(kwargs)
            return self

    encoded = [relay.to_base64("GenreType", "1"), relay.to_base64("GenreType", "2")]
    f = GlobalIDMultipleChoiceFilter(field_name="genres", lookup_expr="in")
    assert getattr(f, _GLOBALID_RELATION_PK_ATTR, False) is not True
    # ``MultipleChoiceFilter`` defaults ``distinct=True``; the stub must accept it.
    f.filter(_Qs(), encoded)
    assert captured == {"genres__in": ["1", "2"]}


def test_global_id_filter_empty_node_id_rejects():
    """A scalar well-typed empty-id GlobalID rejects with ``GLOBALID_INVALID``.

    ``to_base64(<accepted type>, "")`` decodes to ``node_id == ""``, which clears
    decode + strategy + type-name validation (an unbound owner falls back to
    node-id-only), but an empty identifier is not a filter value. The old scalar
    ``EMPTY_VALUES`` no-op silently widened the restrictive filter to the whole
    queryset; the shared boundary now raises before any queryset clause runs.
    """
    f = GlobalIDFilter(field_name="id", lookup_expr="exact")
    with pytest.raises(GraphQLError, match="empty node id") as exc_info:
        f.filter(object(), relay.to_base64("GenreType", ""))
    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


def test_global_id_filter_marked_empty_node_id_rejects_before_query():
    """The marked non-pk-``to_field`` path also rejects an empty id -- never a 500.

    Previously a MARKED leaf compiled ``<relation>__pk__exact=""`` (a 500
    ``ValueError`` on the integer target pk) whenever the empty id slipped past the
    scalar no-op. Because the reject now happens inside
    ``_decode_and_validate_global_id`` -- before the marked/unmarked branch and
    before any queryset access -- the marked path raises the same clean
    ``GLOBALID_INVALID`` and never touches the database.
    """
    f = GlobalIDFilter(field_name="target", lookup_expr="exact")
    setattr(f, _GLOBALID_RELATION_PK_ATTR, True)
    with pytest.raises(GraphQLError, match="empty node id") as exc_info:
        f.filter(object(), relay.to_base64("RpToFieldTargetType", ""))
    assert exc_info.value.extensions == {"code": "GLOBALID_INVALID"}


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
def test_accepted_globalid_type_names_non_framework_strategies(strategy):
    """`callable` / `custom` / absent strategy -> `None` accepted set (defensive belt).

    `_decode_and_validate_global_id` fail-closes on these before reaching this
    helper (see `test_filter_encode_only_strategy_rejects_fail_closed` /
    `test_filter_known_definition_none_strategy_rejects_fail_closed`); the helper
    keeps returning `None` as a defensive belt only.
    """
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


@pytest.mark.parametrize("strategy", ["callable", "custom"])
def test_filter_encode_only_strategy_rejects_fail_closed(strategy):
    """`callable` / `custom` targets fail closed: the strategy is encode-only.

    These strategies have no decode path, so a typed filter input for the
    target's GlobalID could never validly consume the IDs it emits. The runtime
    backstop (behind the build-time audit) rejects with a coded GraphQLError.
    """
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy=strategy)
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("AnythingAtAll", "99")
    with pytest.raises(GraphQLError, match="encode-only") as exc_info:
        _decode_and_validate_global_id(encoded, f)
    assert exc_info.value.extensions == {"code": "GLOBALID_UNVALIDATABLE"}
    assert strategy in str(exc_info.value)


def test_filter_known_definition_none_strategy_rejects_fail_closed():
    """A known target whose recorded strategy is `None` is a lifecycle defect.

    An unfinalized / non-Relay target should never reach a GlobalID filter; the
    backstop rejects with a coded GraphQLError distinct from the encode-only
    message rather than silently falling back to node-id-only.
    """
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy=None)
    f = _global_id_filter_with_owner("id", owner)
    encoded = relay.to_base64("AnythingAtAll", "99")
    with pytest.raises(GraphQLError, match="no .*recorded globalid strategy") as exc_info:
        _decode_and_validate_global_id(encoded, f)
    assert exc_info.value.extensions == {"code": "GLOBALID_UNVALIDATABLE"}


def test_multi_value_filter_encode_only_reject_names_index():
    """`GlobalIDMultipleChoiceFilter` names the offending index on a fail-closed reject."""
    owner = _FakeOwnerDefinition(target=None, effective_globalid_strategy="callable")
    f = GlobalIDMultipleChoiceFilter(field_name="id")
    f.parent = _FakeParent(owner)
    with pytest.raises(GraphQLError, match="at index 0") as exc_info:
        f.filter(object(), [relay.to_base64("AnythingAtAll", "99")])
    assert exc_info.value.extensions == {"code": "GLOBALID_UNVALIDATABLE"}


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
