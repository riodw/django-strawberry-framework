"""Filter input-generation tests for lookup naming, field construction, normalization, references, and reset.

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
    RelatedFilter,
    TypedFilter,
    _helper_referenced_filtersets,
    filter_input_type,
)
from django_strawberry_framework.filters.inputs import (
    INPUTS_MODULE_PATH,
    LOOKUP_NAME_MAP,
    _build_input_fields,
    _build_logic_fields,
    _build_range_input_class,
    _camel_case,
    _field_specs,
    _iter_filterset_subclasses,
    _model_field_for_filter,
    _pascal_case,
    _scalar_from_form_field,
    _scalar_from_model_field,
    build_input_class,
    clear_filter_input_namespace,
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
    """`and` / `or` / `not` are Python keywords -- they ride through `strawberry.field(name=...)`.

    Each carries an explicit ``default=None`` so it stays OPTIONAL under the
    Finding 2 rule that an omitted ``default`` now builds a REQUIRED field.
    """
    triples = _build_logic_fields("X")
    by_attr = {python_attr: kwargs for python_attr, _, kwargs in triples}
    assert by_attr["and_"] == {"name": "and", "default": None}
    assert by_attr["or_"] == {"name": "or", "default": None}
    assert by_attr["not_"] == {"name": "not", "default": None}


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
        [
            ("in_", list[int] | None, {"name": "in", "default": None}),
        ],
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
def test_build_input_fields_pins_every_lookup_name_to_its_camel_name():
    """The operator-bag wire name is pinned to ``graphql_camel_name`` for EVERY lookup.

    The shared input builder pins ``exact`` -> ``exact`` even though the optional-field
    helper does not need to carry an identity alias. Strawberry's converter therefore
    cannot re-derive generated names or collapse a digit-adjacent underscore.
    """

    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"name": ["exact", "icontains", "isnull"], "id": ["in"]}

    triples = _build_input_fields(ItemFilter)
    by_attr = {python_attr: (annotation, kwargs) for python_attr, annotation, kwargs in triples}
    # Find the `name` field's bag class and walk its Strawberry fields.
    name_annotation = by_attr["name"][0]
    # `bag_class | None` -> strip None to get the bag class.
    bag = next(arg for arg in get_args(name_annotation) if arg is not type(None))
    bag_fields = {
        field.python_name: field.graphql_name for field in bag.__strawberry_definition__.fields
    }
    # `exact` -> attr `exact`, pinned by the shared builder rather than Strawberry.
    assert bag_fields["exact"] == "exact"
    # `icontains` -> attr `i_contains`, alias `iContains`.
    assert bag_fields["i_contains"] == "iContains"
    # `isnull` -> attr `is_null`, alias `isNull`.
    assert bag_fields["is_null"] == "isNull"

    id_annotation = by_attr["id"][0]
    id_bag = next(arg for arg in get_args(id_annotation) if arg is not type(None))
    id_fields = {
        field.python_name: field.graphql_name for field in id_bag.__strawberry_definition__.fields
    }
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


def test_normalize_input_value_encodes_globalid_object_to_wire_form():
    """``relay.GlobalID`` OBJECT -> base64 wire string (``type_name`` preserved).

    The object keeps its type through normalization (M1 fix) so the bound
    ``GlobalIDFilter.filter`` can validate it before decoding; the value
    round-trips back to the original ``(type_name, node_id)``.
    """
    f = GlobalIDFilter()
    gid = relay.GlobalID(type_name="X", node_id="42")
    encoded = normalize_input_value(f, gid)
    assert encoded == str(gid)
    round_tripped = relay.GlobalID.from_id(encoded)
    assert (round_tripped.type_name, round_tripped.node_id) == ("X", "42")


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


def test_normalize_input_value_unwraps_enum_member_with_none_value():
    """An enum member whose ``.value`` is ``None`` unwraps to ``None`` (feedback2 #4).

    The structural ``isinstance(value, enum.Enum)`` check unwraps it; the prior
    value-truthiness guard returned the member object un-unwrapped instead.
    """

    class Tri(Enum):
        YES = "yes"
        UNKNOWN = None

    from django_filters import ChoiceFilter

    assert normalize_input_value(ChoiceFilter(), Tri.UNKNOWN) is None


def test_normalize_input_value_range_filter_emits_positional_keys():
    """RangeFilter -> `{<field>_0: start, <field>_1: end}` positional patch."""
    f = RangeFilter(field_name="lifetime_fines_cents")

    @dataclass
    class _RangeInput:
        start: int | None = 1
        end: int | None = 10

    patch = normalize_input_value(f, _RangeInput(), field_name="lifetime_fines_cents")
    assert patch == {"lifetime_fines_cents_0": 1, "lifetime_fines_cents_1": 10}


def test_normalize_input_value_range_filter_drops_none_axes_partial_range():
    """Partial-range inputs surface only the supplied positional key.

    A ``None``-valued axis is "axis not supplied"; emitting ``{<name>_0: None}``
    to the form-data dict surfaces "axis supplied, value is None" to any
    caller walking ``data.keys()``. The normalizer drops ``None``-valued
    axes so the patch shape matches django-filter's form-data convention
    for partial ranges.
    """
    f = RangeFilter(field_name="lifetime_fines_cents")

    @dataclass
    class _RangeInput:
        start: int | None = None
        end: int | None = None

    # Only ``start`` supplied -> single-key patch.
    only_start = normalize_input_value(
        f,
        _RangeInput(start=5),
        field_name="lifetime_fines_cents",
    )
    assert only_start == {"lifetime_fines_cents_0": 5}

    # Only ``end`` supplied -> single-key patch.
    only_end = normalize_input_value(
        f,
        _RangeInput(end=10),
        field_name="lifetime_fines_cents",
    )
    assert only_end == {"lifetime_fines_cents_1": 10}

    # Both supplied -> both-key patch (existing both-axes contract preserved).
    both = normalize_input_value(
        f,
        _RangeInput(start=5, end=10),
        field_name="lifetime_fines_cents",
    )
    assert both == {"lifetime_fines_cents_0": 5, "lifetime_fines_cents_1": 10}

    # Neither supplied -> empty patch (no positional keys at all).
    neither = normalize_input_value(
        f,
        _RangeInput(),
        field_name="lifetime_fines_cents",
    )
    assert neither == {}


def test_normalize_input_value_global_id_list():
    """GlobalID OBJECTS keep their ``type_name`` (wire form), not bare node_ids.

    Pre-decoding to a bare ``node_id`` here stripped the type *before*
    the bound filter could validate it (M1 of the implementation review),
    so a wrong-type GlobalID object passed silently. The normalizer now
    re-encodes objects to the base64 wire string so
    ``GlobalIDMultipleChoiceFilter.filter`` runs the type-name check;
    the value still round-trips to the original ``(type_name, node_id)``.
    """
    f = GlobalIDMultipleChoiceFilter()
    gid_a = relay.GlobalID(type_name="X", node_id="1")
    gid_b = relay.GlobalID(type_name="X", node_id="2")
    encoded = normalize_input_value(f, [gid_a, gid_b])
    assert encoded == [str(gid_a), str(gid_b)]
    decoded = [relay.GlobalID.from_id(value) for value in encoded]
    assert [(g.type_name, g.node_id) for g in decoded] == [("X", "1"), ("X", "2")]


def test_normalize_input_value_none_returns_none():
    f = GlobalIDFilter()
    assert normalize_input_value(f, None) is None


def test_normalize_input_value_unset_returns_none():
    """``strawberry.UNSET`` is treated as "not supplied", same as ``None``.

    Defensive short-circuit at the entry to ``normalize_input_value``:
    every branch below either iterates / indexes / coerces ``raw_value``
    and would either raise ``TypeError`` (list-shaped branches) or
    silently pass the UNSET sentinel into the form-data dict
    (scalar branches). UNSET must be skipped here so every call site
    benefits, including the operator-bag inner loop and the
    ``_q_for_branch`` recursion.
    """
    import strawberry

    for f in (GlobalIDFilter(), GlobalIDMultipleChoiceFilter()):
        assert normalize_input_value(f, strawberry.UNSET) is None


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


# ---------------------------------------------------------------------------
# _pascal_case / _camel_case naming helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "_",
        "__",
        "___",
    ],
)
def test_pascal_case_raises_for_no_word_character_input(bad):
    """`_pascal_case` raises rather than silently returning `""` (round-4 fix)."""
    with pytest.raises(ConfigurationError) as excinfo:
        _pascal_case(bad)
    assert repr(bad) in str(excinfo.value)


def test_pascal_case_converts_separators():
    assert _pascal_case("galaxy__name") == "GalaxyName"
    assert _pascal_case("email_must_have_at_sign") == "EmailMustHaveAtSign"


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "_",
        "__",
        "___",
    ],
)
def test_type_name_for_raises_for_no_word_character_field_path(bad):
    """``type_name_for`` raises rather than silently collapsing to the root name.

    The guard is hoisted from ``_pascal_case`` (the direct
    ``_build_range_input_class`` consumer) into the shared
    ``ClassBasedTypeNameMixin`` so the bag-class naming path in
    ``_build_input_fields`` -- which routes through ``type_name_for`` /
    ``utils.strings.pascal_case`` rather than the inputs-local
    ``_pascal_case`` -- also surfaces the no-word-character collision
    loudly instead of producing a generic ``f"{cls.__name__}InputType"``
    that silently collides with the root input type's own name.
    """
    from django_strawberry_framework.sets_mixins import ClassBasedTypeNameMixin

    class _Probe(ClassBasedTypeNameMixin):
        pass

    with pytest.raises(ConfigurationError) as excinfo:
        _Probe.type_name_for(bad)
    assert repr(bad) in str(excinfo.value)


def test_camel_case_returns_input_when_no_word_characters():
    """`_camel_case` returns the raw string when it has no word tokens."""
    assert _camel_case("") == ""
    assert _camel_case("_") == "_"


def test_camel_case_lowercases_head_and_pascals_rest():
    assert _camel_case("galaxy_name") == "galaxyName"


# ---------------------------------------------------------------------------
# _scalar_from_form_field - form-field -> Python scalar mapping
# ---------------------------------------------------------------------------


def test_scalar_from_form_field_maps_each_recognized_shape():
    """Every recognized form-field shape maps to its Python scalar.

    Regression pin for the ``django.forms`` hierarchy trap: ``FloatField``
    and ``DecimalField`` BOTH subclass ``IntegerField``, so they must be
    matched before the ``IntegerField`` catch - otherwise a float/decimal
    filter mis-maps to ``int``.
    """
    import datetime
    import decimal
    import uuid

    from django import forms

    assert _scalar_from_form_field(forms.NullBooleanField()) is bool
    assert _scalar_from_form_field(forms.BooleanField()) is bool
    assert _scalar_from_form_field(forms.IntegerField()) is int
    assert _scalar_from_form_field(forms.FloatField()) is float
    assert _scalar_from_form_field(forms.DecimalField()) is decimal.Decimal
    assert _scalar_from_form_field(forms.DateTimeField()) is datetime.datetime
    assert _scalar_from_form_field(forms.DateField()) is datetime.date
    assert _scalar_from_form_field(forms.TimeField()) is datetime.time
    assert _scalar_from_form_field(forms.UUIDField()) is uuid.UUID
    assert _scalar_from_form_field(forms.CharField()) is str
    # Unknown shape falls through to the ``str`` catch-all.
    assert _scalar_from_form_field(forms.Field()) is str


# ---------------------------------------------------------------------------
# _scalar_from_model_field - model-field -> Python scalar mapping
# ---------------------------------------------------------------------------


def test_scalar_from_model_field_none_falls_back_to_str():
    assert _scalar_from_model_field(None) is str


def test_scalar_from_model_field_maps_each_recognized_shape():
    import datetime
    import decimal
    import uuid

    assert _scalar_from_model_field(models.BooleanField()) is bool
    assert _scalar_from_model_field(models.IntegerField()) is int
    assert _scalar_from_model_field(models.FloatField()) is float
    assert _scalar_from_model_field(models.DecimalField()) is decimal.Decimal
    assert _scalar_from_model_field(models.DateTimeField()) is datetime.datetime
    assert _scalar_from_model_field(models.DateField()) is datetime.date
    assert _scalar_from_model_field(models.TimeField()) is datetime.time
    assert _scalar_from_model_field(models.UUIDField()) is uuid.UUID
    # Unknown shape falls through to the ``str`` catch-all.
    assert _scalar_from_model_field(models.TextField()) is str


# ---------------------------------------------------------------------------
# convert_filter_to_input_annotation / normalize_input_value edge branches
# ---------------------------------------------------------------------------


def test_convert_filter_to_input_annotation_typed_filter_uses_model_scalar():
    """A bare ``TypedFilter`` resolves its scalar from the model field."""
    annotation = convert_filter_to_input_annotation(
        TypedFilter(field_name="lifetime_fines_cents"),
        models.IntegerField(),
        None,
    )
    # Optional wrapper around the resolved scalar.
    assert annotation == (int | None)


def test_normalize_input_value_list_filter_unwraps_each_element():
    """``ListFilter`` / ``ArrayFilter`` values normalize element-by-element."""
    f = ListFilter(field_name="ids")
    assert normalize_input_value(
        f,
        [1, 2, 3],
        field_name="ids",
    ) == [1, 2, 3]


def test_build_range_input_class_is_cached_on_the_filter_instance():
    """The same generation identity returns one cached class."""
    f = RangeFilter(field_name="price")
    first = _build_range_input_class(f, int)
    second = _build_range_input_class(f, int)
    assert first is second


def test_build_range_input_class_cache_is_keyed_by_owner_field_and_scalar():
    """One filter instance never reuses a class across generation identities."""

    class FirstFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = []

    class SecondFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = []

    f = RangeFilter(field_name="price")
    direct = _build_range_input_class(f, int)
    owned = _build_range_input_class(f, int, FirstFilter)
    other_owner = _build_range_input_class(f, int, SecondFilter)
    other_scalar = _build_range_input_class(f, str, FirstFilter)
    f.field_name = "cost"
    other_field = _build_range_input_class(f, int, FirstFilter)

    assert (
        len(
            {
                direct,
                owned,
                other_owner,
                other_scalar,
                other_field,
            },
        )
        == 5
    )
    assert owned.__name__ == "FirstFilterPriceRangeInputType"
    assert other_scalar.__annotations__["start"] == (str | None)
    assert other_field.__name__ == "FirstFilterCostRangeInputType"


def test_build_range_input_class_name_unqualified_without_filterset():
    """No owning filterset -> the historical ``<Field>RangeInputType`` name is preserved."""
    f = RangeFilter(field_name="price")
    assert _build_range_input_class(f, int).__name__ == "PriceRangeInputType"


@pytest.mark.django_db
def test_range_input_type_name_is_scoped_per_filterset():
    """Two filtersets sharing a ``field_name`` mint DISTINCT range sub-input classes.

    Regression pin for the spec-027 Slice-2 collision hazard. The nested
    ``RangeFilter`` sub-input class name derived from ``field_name`` alone, so two
    filtersets that each declare a ``RangeFilter`` for a same-named column both
    stamped one GraphQL name (``PriceRangeInputType``). These nested classes are
    embedded directly in the annotation (NOT run through the Decision-9
    materialization ledger nor the arguments-factory collision registry), so
    Strawberry does NOT raise on the clash -- it silently keeps whichever class it
    registers first and drops the other, advertising the wrong axis scalar for the
    loser. The name is now qualified by the owning filterset so the two are
    distinct and both survive in the schema.
    """
    import re

    from apps.scalars import models as scalar_models

    class ScalarPriceFilter(FilterSet):
        price = RangeFilter(field_name="price")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    class TextPriceFilter(FilterSet):
        # Same generated top-level ``price`` field, but a text-backed source:
        # this proves the two scoped nested types retain different axis scalars.
        price = RangeFilter(field_name="price")

        class Meta:
            model = library_models.Branch
            fields = []

    def _range_cls_of(bag):
        for annotation in bag.__annotations__.values():
            for arg in get_args(annotation):
                if getattr(arg, "__name__", "").endswith("RangeInputType"):
                    return arg
        raise AssertionError("no RangeInputType found in operator bag")

    def _bag(triples):
        by_attr = {p: a for p, a, _ in triples}
        return next(x for x in get_args(by_attr["price"]) if x is not type(None))

    bag1 = _bag(_build_input_fields(ScalarPriceFilter))
    bag2 = _bag(_build_input_fields(TextPriceFilter))
    r1 = _range_cls_of(bag1)
    r2 = _range_cls_of(bag2)

    # Owning-filterset qualifier makes the two names distinct (pre-fix: both
    # were ``PriceRangeInputType``).
    assert r1.__name__ == "ScalarPriceFilterPriceRangeInputType"
    assert r2.__name__ == "TextPriceFilterPriceRangeInputType"
    assert r1.__name__ != r2.__name__
    assert r1.__annotations__["start"] != r2.__annotations__["start"]

    # Both nested range types survive when both operator bags land in one schema;
    # pre-fix the name clash silently collapsed the two into a single input type
    # (Strawberry keeps whichever it registers first and drops the other).
    @strawberry.type
    class Query:
        ok: int

    sdl = str(strawberry.Schema(query=Query, types=[bag1, bag2]))
    range_defs = set(re.findall(r"input (\w*RangeInputType)", sdl))
    assert range_defs == {
        "ScalarPriceFilterPriceRangeInputType",
        "TextPriceFilterPriceRangeInputType",
    }


@pytest.mark.django_db
def test_direct_range_conversion_does_not_poison_owned_input_build():
    """An earlier unowned conversion cannot defeat owner-qualified generation."""
    from apps.scalars import models as scalar_models

    class OwnedPriceFilter(FilterSet):
        price = RangeFilter(field_name="price")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    declared_filter = OwnedPriceFilter.base_filters["price"]
    model_field = scalar_models.ScalarSpecimen._meta.get_field("price")
    direct = convert_filter_to_input_annotation(declared_filter, model_field)
    direct_cls = next(arg for arg in get_args(direct) if arg is not type(None))
    assert direct_cls.__name__ == "PriceRangeInputType"

    triples = _build_input_fields(OwnedPriceFilter)
    price_annotation = next(
        annotation for python_attr, annotation, _kwargs in triples if python_attr == "price"
    )
    bag = next(arg for arg in get_args(price_annotation) if arg is not type(None))
    owned_cls = next(
        arg
        for annotation in bag.__annotations__.values()
        for arg in get_args(annotation)
        if getattr(arg, "__name__", "").endswith("RangeInputType")
    )
    assert owned_cls.__name__ == "OwnedPriceFilterPriceRangeInputType"
    assert owned_cls is not direct_cls


def test_build_input_class_threads_description_into_strawberry_field():
    """A ``description`` kwarg is forwarded to ``strawberry.field``."""
    cls = build_input_class(
        "DescribedInputType",
        [
            ("note", str | None, {"default": None, "description": "a note"}),
        ],
    )
    # The strawberry field carries the description through decoration.
    field = next(f for f in cls.__strawberry_definition__.fields if f.python_name == "note")
    assert field.description == "a note"


# ---------------------------------------------------------------------------
# _model_field_for_filter
# ---------------------------------------------------------------------------


def test_model_field_for_filter_returns_none_without_model():
    """A filterset-shaped object with no ``_meta.model`` yields ``None``."""

    class _NoMeta:
        pass

    assert _model_field_for_filter(_NoMeta, GlobalIDFilter(field_name="id")) is None


def test_model_field_for_filter_returns_none_without_field_name():
    """A filter with no ``field_name`` yields ``None`` even on a real model."""
    from tests.filters.fixtures.filtersets import ShelfFilter

    f = GlobalIDFilter()
    f.field_name = ""
    assert _model_field_for_filter(ShelfFilter, f) is None


def test_model_field_for_filter_returns_none_for_unknown_field_name():
    """A typo in ``Filter(field_name=...)`` surfaces as ``None``, not a crash.

    The narrowed ``except FieldDoesNotExist`` catches Django's documented
    "unknown name" signal at ``_meta.get_field`` so any other failure
    surfaces loudly. Previously the broad ``except Exception`` (with a
    ``# pragma: no cover``) masked the same reachable path.
    """
    from tests.filters.fixtures.filtersets import ShelfFilter

    f = GlobalIDFilter(field_name="nonexistent_field")
    assert _model_field_for_filter(ShelfFilter, f) is None


# ---------------------------------------------------------------------------
# _build_input_fields - RelatedFilter with an unresolved (None) target
# ---------------------------------------------------------------------------


def test_build_input_fields_skips_related_filter_with_none_target():
    """A ``RelatedFilter(None, ...)`` placeholder is skipped, not materialized."""

    class PlaceholderFilter(FilterSet):
        rel = RelatedFilter(None, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    # The None-target branch contributes no input triple but does not raise.
    triples = _build_input_fields(PlaceholderFilter)
    names = {python_attr for python_attr, _annotation, _kwargs in triples}
    assert "rel" not in names
    assert "code" in names


# ---------------------------------------------------------------------------
# _build_input_fields - HIDE_FLAT_FILTERS toggle (django-graphene-filters parity)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_build_input_fields_shows_flat_relational_when_hide_flat_filters_false(settings):
    """Default (``HIDE_FLAT_FILTERS=False``) exposes BOTH shapes for a relation.

    The nested ``RelatedFilter`` branch (``shelves`` -- the strawberry-django
    shape) AND the flat relational traversal field (``shelves_code`` -- the
    django-graphene-filters shape) are both emitted, matching the upstream
    default at ``django_graphene_filters/conf.py`` (``HIDE_FLAT_FILTERS: False``).
    """
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"HIDE_FLAT_FILTERS": False}

    class HffShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact", "icontains"]}

    class HffBranchFilter(FilterSet):
        shelves = RelatedFilter(HffShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    names = {
        python_attr for python_attr, _annotation, _kwargs in _build_input_fields(HffBranchFilter)
    }
    assert "shelves" in names  # nested branch (strawberry-django shape)
    assert "shelves_code" in names  # flat relational traversal (graphene-django shape)
    assert "name" in names  # scalar own field


@pytest.mark.django_db
def test_build_input_fields_hides_flat_relational_when_hide_flat_filters_true(settings):
    """``HIDE_FLAT_FILTERS=True`` drops only the flat relational traversal fields.

    The relation is then reachable solely through its nested branch
    (``shelves``); the nested branch and scalar own fields are untouched, so
    strawberry-django parity is preserved in either toggle position.
    """
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"HIDE_FLAT_FILTERS": True}

    class HffShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact", "icontains"]}

    class HffBranchFilter(FilterSet):
        shelves = RelatedFilter(HffShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    names = {
        python_attr for python_attr, _annotation, _kwargs in _build_input_fields(HffBranchFilter)
    }
    assert "shelves" in names  # nested branch still present
    assert "name" in names  # scalar own field still present
    assert "shelves_code" not in names  # flat relational traversal hidden


@pytest.mark.django_db
def test_build_input_fields_hides_deep_multi_hop_flat_relational_when_true(settings):
    """``HIDE_FLAT_FILTERS=True`` hides flat traversal at EVERY depth, not just one hop.

    A two-hop chain (Branch -> shelves -> books -> title) produces a flat
    ``shelves_books_title`` field when shown; the ``is_expanded_child`` guard keys on
    the first path segment, so it drops the path at any depth. The relation stays
    reachable through the chained nested branches.
    """
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"HIDE_FLAT_FILTERS": True}

    class DeepBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    class DeepShelfFilter(FilterSet):
        books = RelatedFilter(DeepBookFilter, field_name="books")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class DeepBranchFilter(FilterSet):
        shelves = RelatedFilter(DeepShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    names = {
        python_attr for python_attr, _annotation, _kwargs in _build_input_fields(DeepBranchFilter)
    }
    assert "shelves" in names  # nested branch (reach the chain through here)
    assert "shelves_code" not in names  # one-hop flat hidden
    assert "shelves_books_title" not in names  # two-hop flat hidden


@pytest.mark.django_db
def test_build_input_fields_keeps_non_relatedfilter_flat_traversal_visible_when_true(settings):
    """A flat ``<rel>__<field>`` whose root is NOT a declared ``RelatedFilter`` survives.

    The guard only trims expansions of declared ``RelatedFilter`` relations; an explicit
    ``Meta.fields`` traversal with no nested alternative (spec-021 L1's intentional flat
    shape) stays visible even when ``HIDE_FLAT_FILTERS=True``.
    """
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"HIDE_FLAT_FILTERS": True}

    class PlainTraversalShelfFilter(FilterSet):
        # ``branch`` is a real FK but is NOT declared as a RelatedFilter here.
        class Meta:
            model = library_models.Shelf
            fields = {"branch__name": ["exact"], "code": ["exact"]}

    names = {
        python_attr
        for python_attr, _annotation, _kwargs in _build_input_fields(PlainTraversalShelfFilter)
    }
    assert "branch_name" in names  # non-RelatedFilter flat traversal stays visible
    assert "code" in names


# ---------------------------------------------------------------------------
# Digit-boundary operator-bag / range type names
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_build_input_fields_keeps_digit_boundary_operator_bags_distinct():
    """``field_2`` / ``field2`` mint DISTINCT operator-bag GraphQL type names.

    ``ClassBasedTypeNameMixin.type_name_for`` routes through ``pascal_case``. A
    non-injective Pascal collapse (``field_2`` / ``field2`` both -> ``Field2``)
    made both bags claim ``<FilterSet>Field2FilterInputType``. Those nested
    classes are embedded in annotations (not the Decision-9 ledger), so
    Strawberry silently kept one bag and dropped the other -- wrong lookups on
    the wire. Top-level field attrs stay distinct via ``graphql_camel_name``;
    the type-name stem must preserve the same digit boundary.
    """
    import re

    from django_filters import CharFilter

    class DigitBoundaryFilter(FilterSet):
        field_2 = CharFilter(field_name="name", lookup_expr="exact")
        field2 = CharFilter(field_name="name", lookup_expr="icontains")

        class Meta:
            model = library_models.Branch
            fields = []

    assert DigitBoundaryFilter.type_name_for("field_2") == (
        "DigitBoundaryFilterField_2FilterInputType"
    )
    assert DigitBoundaryFilter.type_name_for("field2") == (
        "DigitBoundaryFilterField2FilterInputType"
    )

    triples = _build_input_fields(DigitBoundaryFilter)
    by_attr = {python_attr: annotation for python_attr, annotation, _kwargs in triples}

    def _bag(attr: str):
        return next(arg for arg in get_args(by_attr[attr]) if arg is not type(None))

    bag_underscore = _bag("field_2")
    bag_plain = _bag("field2")
    assert bag_underscore.__name__ == "DigitBoundaryFilterField_2FilterInputType"
    assert bag_plain.__name__ == "DigitBoundaryFilterField2FilterInputType"
    assert bag_underscore is not bag_plain
    assert "exact" in bag_underscore.__annotations__
    assert "i_contains" in bag_plain.__annotations__

    @strawberry.type
    class Query:
        ok: int

    # Register the bags directly (same pattern as the scoped-range collision pin);
    # a root input with ``strawberry.lazy`` self-refs needs Decision-9 materialization.
    sdl = str(strawberry.Schema(query=Query, types=[bag_underscore, bag_plain]))
    bag_defs = set(re.findall(r"input (DigitBoundaryFilterField_?2FilterInputType)", sdl))
    assert bag_defs == {
        "DigitBoundaryFilterField_2FilterInputType",
        "DigitBoundaryFilterField2FilterInputType",
    }


@pytest.mark.django_db
def test_range_input_type_name_preserves_digit_boundary_in_field_name():
    """Range sub-input names keep ``price_2`` distinct from ``price2``."""
    from apps.scalars import models as scalar_models

    class PriceDigitFilter(FilterSet):
        price_2 = RangeFilter(field_name="price_2")
        price2 = RangeFilter(field_name="price2")

        class Meta:
            model = scalar_models.ScalarSpecimen
            fields = []

    # field_name drives ``_pascal_case`` inside ``_build_range_input_class``.
    underscored = RangeFilter(field_name="price_2")
    plain = RangeFilter(field_name="price2")
    assert (
        _build_range_input_class(underscored, int, PriceDigitFilter).__name__
        == "PriceDigitFilterPrice_2RangeInputType"
    )
    assert (
        _build_range_input_class(plain, int, PriceDigitFilter).__name__
        == "PriceDigitFilterPrice2RangeInputType"
    )


# ---------------------------------------------------------------------------
# clear_filter_input_namespace - cycle-safe import guards
# ---------------------------------------------------------------------------


def test_clear_filter_input_namespace_tolerates_unimportable_submodules():
    """Both ImportError guards are best-effort: a broken import is skipped."""
    import sys

    factories_name = "django_strawberry_framework.filters.factories"
    sets_name = "django_strawberry_framework.filters.sets"
    saved = {name: sys.modules.get(name) for name in (factories_name, sets_name)}
    try:
        # Setting the module entry to ``None`` makes ``from ... import ...``
        # raise ImportError, exercising both ``except ImportError`` guards.
        sys.modules[factories_name] = None
        sys.modules[sets_name] = None
        # Must not raise even though neither submodule can be imported.
        clear_filter_input_namespace()
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


# ---------------------------------------------------------------------------
# _iter_filterset_subclasses - diamond dedup
# ---------------------------------------------------------------------------


def test_iter_filterset_subclasses_dedupes_diamond_inheritance():
    """A diamond hierarchy surfaces each subclass once (the dedup `continue`)."""

    class A(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    class B(A):
        pass

    class C(A):
        pass

    class D(B, C):
        pass

    found = _iter_filterset_subclasses(A)
    # ``D`` is reachable through both ``B`` and ``C`` but appears once.
    assert found.count(D) == 1
    assert {B, C, D}.issubset(set(found))
