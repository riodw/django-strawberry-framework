"""Tests for `django_strawberry_framework/filters/inputs.py` (Slice 2).

Covers the lookup-name table, the `_build_logic_fields` /
`_build_input_fields` operator-bag builders, `construct_search`,
`convert_filter_to_input_annotation` / `normalize_input_value` table
cases, `FieldSpec` source-path mapping, and the `filter_input_type`
consumer helper (Decision 11).
"""

from __future__ import annotations

import typing
from dataclasses import dataclass
from enum import Enum
from typing import get_args, get_origin

import pytest
import strawberry
from apps.library import models as library_models
from apps.products.models import Category, Item
from django.db import models
from strawberry import relay

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    FilterSet,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    ListFilter,
    RangeFilter,
    _helper_referenced_filtersets,
    filter_input_type,
)
from django_strawberry_framework.filters.inputs import (
    INPUTS_MODULE_PATH,
    LOOKUP_NAME_MAP,
    _build_input_fields,
    _build_logic_fields,
    _field_specs,
    build_input_class,
    construct_search,
    convert_filter_to_input_annotation,
    normalize_input_value,
)
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    _field_specs.clear()
    _helper_referenced_filtersets.clear()
    yield
    registry.clear()
    _field_specs.clear()
    _helper_referenced_filtersets.clear()


# ---------------------------------------------------------------------------
# LOOKUP_NAME_MAP table
# ---------------------------------------------------------------------------


def test_lookup_name_map_full_table_matches_spec():
    """Pin the Decision-3 Layer-5 table verbatim against accidental drift."""
    expected = {
        "exact": ("exact", "exact"),
        "iexact": ("i_exact", "iExact"),
        "contains": ("contains", "contains"),
        "icontains": ("i_contains", "iContains"),
        "startswith": ("starts_with", "startsWith"),
        "istartswith": ("i_starts_with", "iStartsWith"),
        "endswith": ("ends_with", "endsWith"),
        "iendswith": ("i_ends_with", "iEndsWith"),
        "regex": ("regex", "regex"),
        "iregex": ("i_regex", "iRegex"),
        "gt": ("gt", "gt"),
        "gte": ("gte", "gte"),
        "lt": ("lt", "lt"),
        "lte": ("lte", "lte"),
        "isnull": ("is_null", "isNull"),
        "in": ("in_", "in"),
        "range": ("range", "range"),
        "date": ("date", "date"),
        "year": ("year", "year"),
        "month": ("month", "month"),
        "day": ("day", "day"),
        "week_day": ("week_day", "weekDay"),
        "quarter": ("quarter", "quarter"),
        "hour": ("hour", "hour"),
        "minute": ("minute", "minute"),
        "second": ("second", "second"),
    }
    assert expected == LOOKUP_NAME_MAP


# ---------------------------------------------------------------------------
# _build_logic_fields
# ---------------------------------------------------------------------------


def test_build_logic_fields_uses_inside_list_annotated_for_and_or():
    """H2-of-rev4: `Annotated[...]` lives INSIDE the `list[...]`, not outside."""
    triples = _build_logic_fields("DemoFilterInputType")
    by_attr = {python_attr: (annotation, kwargs) for python_attr, annotation, kwargs in triples}

    # `and_` / `or_` -> `list[Annotated["X", strawberry.lazy(...)]] | None`
    for attr in ("and_", "or_"):
        annotation, _ = by_attr[attr]
        # Strip the `| None` to inspect the list shape.
        non_none_args = [arg for arg in get_args(annotation) if arg is not type(None)]
        assert len(non_none_args) == 1
        list_type = non_none_args[0]
        assert get_origin(list_type) is list
        inner = get_args(list_type)[0]
        # The inner type must be Annotated with a string forward ref.
        assert get_origin(inner) is typing.Annotated or hasattr(inner, "__metadata__")
        inner_args = get_args(inner)
        assert inner_args[0] == "DemoFilterInputType" or (
            hasattr(inner_args[0], "__forward_arg__")
            and inner_args[0].__forward_arg__ == "DemoFilterInputType"
        )

    # `not_` -> `Annotated["X", strawberry.lazy(...)] | None`
    annotation, _ = by_attr["not_"]
    non_none_args = [arg for arg in get_args(annotation) if arg is not type(None)]
    assert len(non_none_args) == 1
    not_inner = non_none_args[0]
    assert hasattr(not_inner, "__metadata__")
    not_inner_args = get_args(not_inner)
    assert not_inner_args[0] == "DemoFilterInputType" or (
        hasattr(not_inner_args[0], "__forward_arg__")
        and not_inner_args[0].__forward_arg__ == "DemoFilterInputType"
    )


def test_build_logic_fields_emits_strawberry_field_name_for_python_keywords():
    """`and` / `or` / `not` are Python keywords -- they ride through `strawberry.field(name=...)`."""
    triples = _build_logic_fields("X")
    by_attr = {python_attr: kwargs for python_attr, _, kwargs in triples}
    assert by_attr["and_"] == {"name": "and"}
    assert by_attr["or_"] == {"name": "or"}
    assert by_attr["not_"] == {"name": "not"}


# ---------------------------------------------------------------------------
# build_input_class
# ---------------------------------------------------------------------------


def test_build_input_class_returns_strawberry_input_decorated_dataclass():
    """The constructed class is a Strawberry input AND a dataclass."""
    cls = build_input_class(
        "ScratchInput",
        [("name", str | None, {"default": None}), ("count", int | None, {"default": None})],
    )
    instance = cls(name="hi", count=3)
    assert instance.name == "hi"
    assert instance.count == 3
    assert hasattr(cls, "__strawberry_definition__")


def test_build_input_class_emits_strawberry_field_name_alias():
    """`name=...` field kwarg lands as the Strawberry field's GraphQL alias."""
    cls = build_input_class(
        "AliasedInput",
        [("in_", list[int] | None, {"name": "in", "default": None})],
    )
    # Walk the Strawberry definition to find the field named `in`.
    fields = cls.__strawberry_definition__.fields
    assert any(field.graphql_name == "in" for field in fields)


# ---------------------------------------------------------------------------
# _build_input_fields
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_build_input_fields_populates_field_specs_table():
    class GalaxyFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    _build_input_fields(GalaxyFilter)
    spec = _field_specs[(GalaxyFilter, "name")]
    assert spec.python_attr == "name"
    assert spec.graphql_name == "name"
    assert spec.django_source_path == "name"


@pytest.mark.django_db
def test_field_spec_maps_galaxy_name_flat_field_to_django_source_path():
    """M5 of rev8: a flat ``galaxy__name`` field carries the source path verbatim."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            # Use the `branch__name` relation traversal: same shape as
            # the spec's `galaxy__name` example.
            fields = {"branch__name": ["exact"]}

    _build_input_fields(ShelfFilter)
    spec = _field_specs[(ShelfFilter, "branch_name")]
    assert spec.python_attr == "branch_name"
    assert spec.graphql_name == "branchName"
    assert spec.django_source_path == "branch__name"


@pytest.mark.django_db
def test_build_input_fields_emits_lookup_name_override_only_when_python_attr_differs():
    """`name=...` is emitted ONLY when the python attr and the GraphQL name differ."""

    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"name": ["exact", "icontains", "isnull"], "id": ["in"]}

    triples = _build_input_fields(ItemFilter)
    by_attr = {python_attr: (annotation, kwargs) for python_attr, annotation, kwargs in triples}
    # Find the `name` field's bag class and walk its Strawberry fields.
    name_annotation = by_attr["name"][0]
    # `bag_class | None` -> strip None to get the bag class.
    bag = [arg for arg in get_args(name_annotation) if arg is not type(None)][0]
    bag_fields = {field.python_name: field.graphql_name for field in bag.__strawberry_definition__.fields}
    # `exact` -> attr `exact`, NO alias emitted (python_attr == graphql_name).
    # Strawberry returns `None` for `graphql_name` when no explicit alias is set.
    assert bag_fields["exact"] is None
    # `icontains` -> attr `i_contains`, alias `iContains`.
    assert bag_fields["i_contains"] == "iContains"
    # `isnull` -> attr `is_null`, alias `isNull`.
    assert bag_fields["is_null"] == "isNull"

    id_annotation = by_attr["id"][0]
    id_bag = [arg for arg in get_args(id_annotation) if arg is not type(None)][0]
    id_fields = {field.python_name: field.graphql_name for field in id_bag.__strawberry_definition__.fields}
    # `in_` -> alias `in`.
    assert id_fields["in_"] == "in"


@pytest.mark.django_db
def test_build_input_fields_handles_field_name_in_lookup_name_map():
    """Verify that when a traversed relation field has a name that matches a key in LOOKUP_NAME_MAP,
    e.g. `branch__year`, but the filter lookup expression is different, e.g. `exact`,
    we don't incorrectly group it as field `branch` with lookup `year`.
    """

    class YearFilter(FilterSet):
        branch__year = GlobalIDFilter(field_name="branch__name", lookup_expr="exact")

        class Meta:
            model = library_models.Shelf
            fields = []

    triples = _build_input_fields(YearFilter)
    by_attr = {python_attr: (annotation, kwargs) for python_attr, annotation, kwargs in triples}

    # Under correct behavior, the top-level field is `branch_year`, NOT `branch`!
    assert "branch_year" in by_attr
    assert "branch" not in by_attr


# ---------------------------------------------------------------------------
# convert_filter_to_input_annotation
# ---------------------------------------------------------------------------


def test_convert_filter_to_input_annotation_handles_globalid_filter():
    f = GlobalIDFilter()
    assert convert_filter_to_input_annotation(f, None) == str | None


def test_convert_filter_to_input_annotation_handles_globalid_multiple_choice_filter():
    f = GlobalIDMultipleChoiceFilter()
    assert convert_filter_to_input_annotation(f, None) == list[str] | None


def test_convert_filter_to_input_annotation_handles_range_filter():
    f = RangeFilter(field_name="value")
    model_field = models.IntegerField()
    annotation = convert_filter_to_input_annotation(f, model_field)
    non_none = [arg for arg in get_args(annotation) if arg is not type(None)]
    assert len(non_none) == 1
    range_cls = non_none[0]
    assert hasattr(range_cls, "__strawberry_definition__")
    fields = {field.python_name for field in range_cls.__strawberry_definition__.fields}
    assert fields == {"start", "end"}


def test_convert_filter_to_input_annotation_handles_list_filter():
    f = ListFilter(field_name="value")
    model_field = models.IntegerField()
    annotation = convert_filter_to_input_annotation(f, model_field)
    assert annotation == list[int] | None


def test_convert_filter_to_input_annotation_handles_choice_filter_via_converter_pipeline():
    """`ChoiceFilter` reaches into ``convert_choices_to_enum`` via the model field."""
    # ``Book.circulation_status`` is a TextChoices field on the example model.
    from django_filters import ChoiceFilter

    f = ChoiceFilter()
    model_field = library_models.Book._meta.get_field("circulation_status")
    annotation = convert_filter_to_input_annotation(f, model_field)
    non_none = [arg for arg in get_args(annotation) if arg is not type(None)]
    assert len(non_none) == 1
    enum_cls = non_none[0]
    # The converter pipeline yields a Strawberry-decorated enum.
    assert issubclass(enum_cls, Enum)


def test_convert_filter_to_input_annotation_rejects_non_choices_derived_enum():
    from django_filters import ChoiceFilter

    f = ChoiceFilter()
    model_field = models.CharField()  # No `choices` attribute set.
    with pytest.raises(ConfigurationError):
        convert_filter_to_input_annotation(f, model_field)


def test_convert_filter_to_input_annotation_rejects_unknown_method_filter():
    """A `Filter(method=...)` with no exposed form field raises ConfigurationError."""

    # Construct a minimal stub that mimics a `django_filters.Filter` whose
    # `method` is set but whose `field` is `None` (the unknown-form-shape
    # case). Mutating `Filter.field` globally would leak the override
    # across tests, so we build a per-test subclass instead.
    class _NoFieldFilter:
        extra = {}
        method = staticmethod(lambda qs, name, value: qs)
        field = None
        lookup_expr = "exact"

    f = _NoFieldFilter()
    # Patch isinstance check chain by intercepting `__class__`-keyed
    # converter dispatch is not feasible without bigger plumbing; the
    # converter walks `isinstance(f, ...)` against the package's
    # ``ListFilter`` / ``ArrayFilter`` / ``TypedFilter`` / ``ChoiceFilter``,
    # and falls through to the catch-all branch when none match. Since
    # `_NoFieldFilter` is not a subclass of any of those, it hits the
    # catch-all where `method is not None and form_field is None`
    # raises.
    with pytest.raises(ConfigurationError):
        convert_filter_to_input_annotation(f, None)


def test_convert_filter_to_input_annotation_wraps_nullable():
    """``extra['required']=False`` (the default) wraps the annotation in `T | None`."""
    from django_filters import CharFilter

    f = CharFilter()
    annotation = convert_filter_to_input_annotation(f, models.CharField())
    assert annotation == str | None


def test_convert_filter_to_input_annotation_does_not_wrap_required():
    from django_filters import CharFilter

    f = CharFilter(required=True)
    annotation = convert_filter_to_input_annotation(f, models.CharField())
    # Required filters return the scalar without the `| None` wrap.
    assert annotation is str


# ---------------------------------------------------------------------------
# normalize_input_value
# ---------------------------------------------------------------------------


def test_normalize_input_value_decodes_globalid():
    """``relay.GlobalID(type_name, node_id)`` -> ``node_id`` (string)."""
    f = GlobalIDFilter()
    gid = relay.GlobalID(type_name="X", node_id="42")
    assert normalize_input_value(f, gid) == "42"


def test_normalize_input_value_passes_string_globalid_through():
    f = GlobalIDFilter()
    assert normalize_input_value(f, "42") == "42"


def test_normalize_input_value_unwraps_enum_member():
    """A Strawberry-enum-member input becomes its `.value`."""

    @strawberry.enum
    class Color(Enum):
        RED = "red"
        BLUE = "blue"

    from django_filters import ChoiceFilter

    f = ChoiceFilter()
    assert normalize_input_value(f, Color.RED) == "red"


def test_normalize_input_value_range_filter_emits_positional_keys():
    """RangeFilter -> `{<field>_0: start, <field>_1: end}` positional patch."""
    f = RangeFilter(field_name="lifetime_fines_cents")

    @dataclass
    class _RangeInput:
        start: int | None = 1
        end: int | None = 10

    patch = normalize_input_value(f, _RangeInput(), field_name="lifetime_fines_cents")
    assert patch == {"lifetime_fines_cents_0": 1, "lifetime_fines_cents_1": 10}


def test_normalize_input_value_global_id_list():
    f = GlobalIDMultipleChoiceFilter()
    gid_a = relay.GlobalID(type_name="X", node_id="1")
    gid_b = relay.GlobalID(type_name="X", node_id="2")
    assert normalize_input_value(f, [gid_a, gid_b]) == ["1", "2"]


def test_normalize_input_value_none_returns_none():
    f = GlobalIDFilter()
    assert normalize_input_value(f, None) is None


# ---------------------------------------------------------------------------
# construct_search
# ---------------------------------------------------------------------------


def test_construct_search_translates_lookup_prefixes():
    """Each `^` / `=` / `@` / `$` prefix maps to its `LOOKUP_PREFIXES` lookup."""
    result = construct_search(
        {
            "^name": object(),
            "=code": object(),
            "@title": object(),
            "$pattern": object(),
            "no_prefix": object(),
        },
    )
    assert result == {
        "name": "istartswith",
        "code": "iexact",
        "title": "search",
        "pattern": "iregex",
    }
    # `no_prefix` (no prefix character) -> not in the result.
    assert "no_prefix" not in result


def test_construct_search_empty_input_returns_empty_dict():
    assert construct_search({}) == {}


# ---------------------------------------------------------------------------
# filter_input_type (Decision 11)
# ---------------------------------------------------------------------------


def test_filter_input_type_returns_annotated_with_lazy_module_path():
    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    result = filter_input_type(MyFilter)
    metadata = result.__metadata__
    # The strawberry.lazy marker is a `StrawberryLazyReference` whose
    # `module` attr carries the module path.
    assert any(getattr(marker, "module", None) == INPUTS_MODULE_PATH for marker in metadata)


def test_filter_input_type_returns_forwardref_in_annotation_args():
    """M4 of rev5: `Annotated[<str_variable>, ...]` wraps the string as a `ForwardRef`."""

    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    result = filter_input_type(MyFilter)
    inner = result.__args__[0]
    assert isinstance(inner, typing.ForwardRef)
    assert inner.__forward_arg__ == "MyFilterInputType"


def test_filter_input_type_records_filterset_into_helper_referenced_set():
    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    filter_input_type(MyFilter)
    assert MyFilter in _helper_referenced_filtersets


def test_filter_input_type_is_idempotent_under_repeated_calls():
    """M6 of rev5: repeated calls converge on one entry and equivalent ForwardRef args."""

    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    first = filter_input_type(MyFilter)
    second = filter_input_type(MyFilter)
    third = filter_input_type(MyFilter)
    assert len(_helper_referenced_filtersets) == 1
    assert first.__args__[0].__forward_arg__ == second.__args__[0].__forward_arg__
    assert second.__args__[0].__forward_arg__ == third.__args__[0].__forward_arg__


def test_filter_input_type_rejects_non_filterset():
    """`int` / non-FilterSet class / `None` all raise TypeError naming the bad value."""
    with pytest.raises(TypeError) as excinfo:
        filter_input_type(42)
    assert "42" in str(excinfo.value)

    class NotAFilter:
        pass

    with pytest.raises(TypeError):
        filter_input_type(NotAFilter)

    with pytest.raises(TypeError):
        filter_input_type(None)
