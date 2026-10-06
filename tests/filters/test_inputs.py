"""Filter input-generation tests for lookup naming, field construction, normalization, references, and reset.

Covers the lookup-name table, the `_build_logic_fields` /
`_build_input_fields` operator-bag builders, `construct_search`,
`convert_filter_to_input_annotation` / `normalize_input_value` table
cases, `FieldSpec` source-path mapping, and the `filter_input_type`
consumer helper (Decision 11).

``HIDE_FLAT_FILTERS`` wire shape lives in
``test_library_api.py`` / ``test_products_api.py``. Scoped ``RangeFilter``
type names live in ``test_scalars_filter_api.py``. This file keeps
converter dispatch, namespace lifecycle, and digit-boundary type-name
injectivity -- construction and private helpers a request cannot name.
"""

from __future__ import annotations

import typing
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, get_args, get_origin, runtime_checkable

import pytest
import strawberry
from apps.library import models as library_models
from apps.products.models import Category, Item
from django.db import models
from django.db.models import QuerySet
from django_filters import BaseInFilter, BooleanFilter, CharFilter, ChoiceFilter
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    FilterInput,
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
from django_strawberry_framework.filters.base import RelationPkFilter, RelationPkMultipleFilter
from django_strawberry_framework.filters.inputs import (
    _FILTER_INPUT_KIND_TYPES,
    INPUTS_MODULE_PATH,
    LOGIC_OP_AND,
    LOGIC_OP_NOT,
    LOGIC_OP_OR,
    LOGIC_OPERATORS,
    LOGIC_OPERATORS_BY_PYTHON_ATTR,
    LOGIC_OPERATORS_BY_WIRE,
    LOOKUP_NAME_MAP,
    _build_input_fields,
    _build_logic_fields,
    _build_range_input_class,
    _camel_case,
    _field_specs,
    _filter_input_prechecks,
    _iter_filterset_subclasses,
    _model_field_for_filter,
    _pascal_case,
    _scalar_from_form_field,
    _scalar_from_model_field,
    _unexpected_filter_dispatch,
    build_input_class,
    clear_filter_input_namespace,
    construct_search,
    convert_filter_to_input_annotation,
    filter_lookup_table,
    materialize_input_class,
    normalize_input_value,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.relay import apply_interfaces
from tests._generated_inputs import keyword_constructor as _keyword_constructor


@runtime_checkable
class _ScratchInput(Protocol):
    """The two fields the scratch ``build_input_class`` call generates."""

    name: str | None
    count: int | None


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
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
    """Pin the spec-027 Decision 3 Layer-5 table verbatim against accidental drift."""
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
    """`Annotated[...]` lives INSIDE the `list[...]`, not outside."""
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

    Each carries an explicit ``default=None`` so it stays OPTIONAL: an
    omitted ``default`` builds a REQUIRED field.
    """
    triples = _build_logic_fields("X")
    by_attr = {python_attr: kwargs for python_attr, _, kwargs in triples}
    assert by_attr["and_"] == {"name": "and", "default": None}
    assert by_attr["or_"] == {"name": "or", "default": None}
    assert by_attr["not_"] == {"name": "not", "default": None}


def test_build_logic_fields_tracks_logic_operators():
    """Emission order and ``(python_attr, wire_name)`` pairs must match ``LOGIC_OPERATORS``.

    ``FilterSet._normalize_input`` maps the same constant onto django-filter
    wire keys; re-spelling the pairs in ``_build_logic_fields`` would let the
    input surface and the runtime normalizer diverge.
    """
    triples = _build_logic_fields("X")
    assert [(python_attr, kwargs["name"]) for python_attr, _, kwargs in triples] == [
        (op.python_attr, op.wire_name) for op in LOGIC_OPERATORS
    ]


def test_logic_operator_descriptors_and_mappings():
    """Descriptors encapsulate python attr, wire name, sequence cardinality, and Q compose."""
    from types import MappingProxyType

    assert LOGIC_OPERATORS == (LOGIC_OP_AND, LOGIC_OP_OR, LOGIC_OP_NOT)
    assert LOGIC_OPERATORS_BY_WIRE == {"and": LOGIC_OP_AND, "or": LOGIC_OP_OR, "not": LOGIC_OP_NOT}
    assert LOGIC_OPERATORS_BY_PYTHON_ATTR == {
        "and_": LOGIC_OP_AND,
        "or_": LOGIC_OP_OR,
        "not_": LOGIC_OP_NOT,
    }
    assert isinstance(LOGIC_OPERATORS_BY_WIRE, MappingProxyType)
    assert isinstance(LOGIC_OPERATORS_BY_PYTHON_ATTR, MappingProxyType)
    with pytest.raises(TypeError):
        # basedpyright: the table is a read-only MappingProxyType; the test proves item assignment
        # raises TypeError
        LOGIC_OPERATORS_BY_WIRE["custom"] = LOGIC_OP_AND  # pyright: ignore[reportIndexIssue]
    with pytest.raises(TypeError):
        # basedpyright: the table is a read-only MappingProxyType; the test proves item assignment
        # raises TypeError
        LOGIC_OPERATORS_BY_PYTHON_ATTR["custom_"] = LOGIC_OP_AND  # pyright: ignore[reportIndexIssue]
    assert LOGIC_OP_AND.is_sequence is True
    assert LOGIC_OP_OR.is_sequence is True
    assert LOGIC_OP_NOT.is_sequence is False


def test_logic_operator_composition_semantics():
    """Each operator compose function builds the expected Django Q structure."""
    q1 = models.Q(name="a")
    q2 = models.Q(name="b")

    # and_ compose
    assert LOGIC_OP_AND.compose([]) == models.Q()
    assert LOGIC_OP_AND.compose([q1]) == models.Q(name="a")
    assert LOGIC_OP_AND.compose([q1, q2]) == (models.Q(name="a") & models.Q(name="b"))

    # or_ compose
    assert LOGIC_OP_OR.compose([]) == models.Q()
    assert LOGIC_OP_OR.compose([q1, q2]) == (models.Q(name="a") | models.Q(name="b"))

    # not_ compose
    assert LOGIC_OP_NOT.compose([]) == models.Q()
    assert LOGIC_OP_NOT.compose([q1]) == ~models.Q(name="a")


# ---------------------------------------------------------------------------
# build_input_class
# ---------------------------------------------------------------------------


def test_build_input_class_returns_strawberry_input_decorated_dataclass():
    """The constructed class is a Strawberry input AND a dataclass."""
    cls = build_input_class(
        "ScratchInput",
        [("name", str | None, {"default": None}), ("count", int | None, {"default": None})],
    )
    instance = _keyword_constructor(cls)(name="hi", count=3)
    assert isinstance(instance, _ScratchInput)
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
    """A flat ``galaxy__name`` field carries the source path verbatim."""

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


def test_declared_filter_name_ending_in_lookup_keeps_its_form_key():
    """A declared ``name__exact`` filter must not collapse onto the ``name`` field.

    The declaration name is the django-filter form key. If grouping treats its
    final ``exact`` token as an auto-generated lookup, input generation emits a
    ``name`` bag and normalization writes ``name``; the bound form only reads
    ``name__exact`` and silently drops the supplied predicate.
    """

    class DeclaredLookupNameFilter(FilterSet):
        name__exact = CharFilter(field_name="name", lookup_expr="exact")

        class Meta:
            model = Category
            fields = []

    triples = _build_input_fields(DeclaredLookupNameFilter)
    by_attr = {python_attr: annotation for python_attr, annotation, _kwargs in triples}
    assert "name_exact" in by_attr
    assert "name" not in by_attr
    assert _field_specs[(DeclaredLookupNameFilter, "name_exact")].django_source_path == (
        "name__exact"
    )
    assert DeclaredLookupNameFilter._normalize_input(
        {"name_exact": {"exact": "alpha"}},
    ) == {"name__exact": "alpha"}


def test_declared_non_exact_filter_keeps_its_form_key():
    """A declared non-``exact`` filter must not gain a generated lookup suffix.

    django-filter registers a class-body declaration under its attribute name
    (``custom``), even when ``lookup_expr="icontains"``. Emitting
    ``custom__icontains`` in ``data`` is an unknown form key, so the form drops
    the value and the declared filter silently applies nothing.
    """

    class DeclaredContainsFilter(FilterSet):
        custom = CharFilter(field_name="name", lookup_expr="icontains")

        class Meta:
            model = Category
            fields = []

    _build_input_fields(DeclaredContainsFilter)
    assert DeclaredContainsFilter._normalize_input(
        {"custom": {"i_contains": "alpha"}},
    ) == {"custom": "alpha"}


def _bag_lookup_attrs(filterset_cls: type[FilterSet], python_attr: str) -> list[str]:
    """Return the lookup attrs of one generated operator-bag field, in emission order."""
    triples = _build_input_fields(filterset_cls)
    annotation = {attr: annotation for attr, annotation, _kwargs in triples}[python_attr]
    (bag_class,) = (arg for arg in get_args(annotation) if arg is not type(None))
    return list(bag_class.__dataclass_fields__)


def test_overlap_head_emits_one_bag_with_each_lookup_keeping_its_own_form_key():
    """A declared head that is also a ``Meta.fields`` head emits one bag, two form keys.

    The declared ``name`` (``iexact``) and the generated ``name__icontains`` share
    the ``name`` head; the table keeps each lookup's own ``get_filters()`` name.
    """

    class OverlapBranchFilter(FilterSet):
        name = CharFilter(lookup_expr="iexact")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["icontains"]}

    assert _bag_lookup_attrs(OverlapBranchFilter, "name") == ["i_contains", "i_exact"]
    lookups = filter_lookup_table(OverlapBranchFilter).by_input_attr["name"]
    assert {attr: form_key for attr, (form_key, _filter) in lookups.items()} == {
        "i_contains": "name__icontains",
        "i_exact": "name",
    }


def _normalize_name_mapping(cls: type[FilterSet]) -> object:
    return cls._normalize_input({"name": {"i_contains": "x"}})


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_build_input_fields, id="input-build"),
        pytest.param(_normalize_name_mapping, id="direct-mapping"),
    ],
)
def test_two_filters_on_one_head_lookup_slot_raise(build: Callable[[type[FilterSet]], object]):
    """A declared filter and a generated one claiming one ``(head, lookup)`` slot raise.

    The declared ``name`` (``icontains`` over ``city``) and the generated
    ``name__icontains`` both land on ``name`` / ``icontains``; one would vanish from
    the generated input, so the table refuses the class wherever it is first read.
    """

    class SameSlotBranchFilter(FilterSet):
        name = CharFilter(field_name="city", lookup_expr="icontains")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["icontains"]}

    with pytest.raises(ConfigurationError) as excinfo:
        build(SameSlotBranchFilter)
    assert str(excinfo.value) == (
        "test_two_filters_on_one_head_lookup_slot_raise.<locals>.SameSlotBranchFilter: "
        "filters 'name__icontains' and 'name' both bind the 'icontains' lookup of input "
        "field 'name', so one would be unreachable from the generated input. Rename one "
        "filter or drop one via Meta.fields / Meta.exclude."
    )


def test_two_heads_flattening_to_one_input_attr_raise():
    """Two ``__`` heads sharing one flattened input attr raise; neither is reachable alone."""

    class AliasCollisionBranchFilter(FilterSet):
        a__b_c = CharFilter(field_name="name")
        a_b__c = CharFilter(field_name="city")

        class Meta:
            model = library_models.Branch
            fields = []

    with pytest.raises(ConfigurationError) as excinfo:
        filter_lookup_table(AliasCollisionBranchFilter)
    assert str(excinfo.value) == (
        "test_two_heads_flattening_to_one_input_attr_raise.<locals>.AliasCollisionBranchFilter: "
        "filters 'a__b_c' and 'a_b__c' both generate the input attribute 'a_b_c' (Django "
        "path separators flatten to '_'), so one would be unreachable. Rename one filter or "
        "drop one via Meta.fields / Meta.exclude."
    )


def test_expanded_declared_child_filter_is_its_own_head():
    """A ``RelatedFilter`` expansion of a child's declared filter keeps its own head.

    The child declares ``title`` (``field_name="name"``) and ``name__exact`` beside a
    generated ``name``. Expanded under ``branch``, ``branch__name__exact`` is its own
    head (it would otherwise shadow the generated ``branch__name`` exact), and every
    flat head binds its own expanded form key.
    """

    class ChildBranchFilter(FilterSet):
        title = CharFilter(field_name="name", lookup_expr="icontains")
        name__exact = CharFilter(field_name="name", lookup_expr="exact")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    class ParentShelfFilter(FilterSet):
        branch = RelatedFilter(ChildBranchFilter, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = []

    table = filter_lookup_table(ParentShelfFilter)
    flat = {
        head: {token: form_key for token, (form_key, _filter) in bag.items()}
        for head, bag in table.heads.items()
        if head != "branch"
    }
    assert flat == {
        "branch__name": {"exact": "branch__name"},
        "branch__title": {"icontains": "branch__title"},
        "branch__name__exact": {"exact": "branch__name__exact"},
    }
    assert table.by_input_attr["branch_name_exact"] is table.by_input_attr["branch__name__exact"]
    # An expanded declared child keeps its declared name as its gate path; the
    # generated ``branch__name`` gates on the ORM path it is named after.
    assert table.gate_paths["branch_title"] == "branch__title"
    assert table.gate_paths["branch__name"] == "branch__name"


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
    f = ChoiceFilter()
    model_field = library_models.Book._meta.get_field("circulation_status")
    annotation = convert_filter_to_input_annotation(f, model_field)
    non_none = [arg for arg in get_args(annotation) if arg is not type(None)]
    assert len(non_none) == 1
    enum_cls = non_none[0]
    # The converter pipeline yields a Strawberry-decorated enum.
    assert issubclass(enum_cls, Enum)


def test_convert_filter_to_input_annotation_rejects_non_choices_derived_enum():
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
    def _passthrough_method(qs: object, name: str, value: object) -> object:
        return qs

    class _NoFieldFilter:
        extra = {}
        method = staticmethod(_passthrough_method)
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
        # basedpyright: a stand-in filter carrying only the slots the code under test reads;
        # convert_filter_to_input_annotation types the parameter as Filter
        convert_filter_to_input_annotation(f, None)  # pyright: ignore[reportArgumentType]


def test_convert_filter_to_input_annotation_keeps_hostile_diagnostics_typed():
    """Malformed filters with raising ``__repr__`` still raise ConfigurationError."""

    class BadRepr:
        @override
        def __repr__(self):
            raise RuntimeError("repr exploded")

    class NoFieldFilter:
        extra = {}
        method = BadRepr()
        field = None
        lookup_expr = "exact"

    with pytest.raises(ConfigurationError, match="unprintable"):
        # basedpyright: the filter whose method repr raises is the hostile input under test;
        # convert_filter_to_input_annotation types the parameter as Filter
        convert_filter_to_input_annotation(NoFieldFilter(), None)  # pyright: ignore[reportArgumentType]

    class BadChoiceFilter(ChoiceFilter):
        @override
        def __repr__(self):
            raise RuntimeError("repr exploded")

    # A model field with no ``choices`` is what drives the ChoiceFilter branch to
    # its rejection, which is the diagnostic under test.
    with pytest.raises(ConfigurationError, match="unprintable"):
        convert_filter_to_input_annotation(BadChoiceFilter(), models.CharField())


def test_convert_filter_to_input_annotation_wraps_nullable():
    """``extra['required']=False`` (the default) wraps the annotation in `T | None`."""
    f = CharFilter()
    annotation = convert_filter_to_input_annotation(f, models.CharField())
    assert annotation == str | None


def test_convert_filter_to_input_annotation_does_not_wrap_required():
    f = CharFilter(required=True)
    annotation = convert_filter_to_input_annotation(f, models.CharField())
    # Required filters return the scalar without the `| None` wrap.
    assert annotation is str


# ---------------------------------------------------------------------------
# normalize_input_value
# ---------------------------------------------------------------------------


def test_normalize_input_value_encodes_globalid_object_to_wire_form():
    """``relay.GlobalID`` OBJECT -> base64 wire string (``type_name`` preserved).

    The object keeps its type through normalization so the bound
    ``GlobalIDFilter.filter`` can validate it before decoding; the value
    round-trips back to the original ``(type_name, node_id)``.
    """
    f = GlobalIDFilter()
    gid = relay.GlobalID(type_name="X", node_id="42")
    encoded = normalize_input_value(f, gid)
    assert encoded == str(gid)
    assert isinstance(encoded, str)
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

    f = ChoiceFilter()
    assert normalize_input_value(f, Color.RED) == "red"


def test_normalize_input_value_unwraps_enum_member_with_none_value():
    """An enum member whose ``.value`` is ``None`` unwraps to ``None``.

    The structural ``isinstance(value, enum.Enum)`` check unwraps it; the prior
    value-truthiness guard returned the member object un-unwrapped instead.
    """

    class Tri(Enum):
        YES = "yes"
        UNKNOWN = None

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


def test_normalize_input_value_range_filter_drops_unset_axes_partial_range():
    """Partial-range inputs drop ``UNSET``-valued axes identically to ``None``."""
    f = RangeFilter(field_name="lifetime_fines_cents")

    @dataclass
    class _RangeInput:
        start: object = strawberry.UNSET
        end: object = strawberry.UNSET

    # Dataclass inputs with UNSET
    assert normalize_input_value(
        f,
        _RangeInput(start=5, end=strawberry.UNSET),
        field_name="lifetime_fines_cents",
    ) == {"lifetime_fines_cents_0": 5}

    assert normalize_input_value(
        f,
        _RangeInput(start=strawberry.UNSET, end=10),
        field_name="lifetime_fines_cents",
    ) == {"lifetime_fines_cents_1": 10}

    assert (
        normalize_input_value(
            f,
            _RangeInput(start=strawberry.UNSET, end=strawberry.UNSET),
            field_name="lifetime_fines_cents",
        )
        == {}
    )

    # Dict inputs with UNSET
    assert normalize_input_value(
        f,
        {"start": 5, "end": strawberry.UNSET},
        field_name="lifetime_fines_cents",
    ) == {"lifetime_fines_cents_0": 5}

    assert normalize_input_value(
        f,
        {"start": strawberry.UNSET, "end": 10},
        field_name="lifetime_fines_cents",
    ) == {"lifetime_fines_cents_1": 10}

    assert (
        normalize_input_value(
            f,
            {"start": strawberry.UNSET, "end": strawberry.UNSET},
            field_name="lifetime_fines_cents",
        )
        == {}
    )


def test_normalize_input_value_range_filter_unwraps_enum_members():
    """RangeFilter unwraps enum members on start and end axes."""
    f = RangeFilter(field_name="status_range")

    class StatusEnum(Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    assert normalize_input_value(
        f,
        {"start": StatusEnum.ACTIVE, "end": StatusEnum.INACTIVE},
        field_name="status_range",
    ) == {"status_range_0": "active", "status_range_1": "inactive"}


def test_normalize_input_value_global_id_list():
    """GlobalID OBJECTS keep their ``type_name`` (wire form), not bare node_ids.

    Pre-decoding to a bare ``node_id`` here stripped the type *before*
    the bound filter could validate it, so a wrong-type GlobalID object
    passed silently. The normalizer now
    re-encodes objects to the base64 wire string so
    ``GlobalIDMultipleChoiceFilter.filter`` runs the type-name check;
    the value still round-trips to the original ``(type_name, node_id)``.
    """
    f = GlobalIDMultipleChoiceFilter()
    gid_a = relay.GlobalID(type_name="X", node_id="1")
    gid_b = relay.GlobalID(type_name="X", node_id="2")
    encoded = normalize_input_value(f, [gid_a, gid_b])
    assert encoded == [str(gid_a), str(gid_b)]
    assert isinstance(encoded, list)
    decoded = [relay.GlobalID.from_id(value) for value in encoded]
    assert [(g.type_name, g.node_id) for g in decoded] == [("X", "1"), ("X", "2")]


def test_normalize_input_value_none_returns_none():
    f = GlobalIDFilter()
    assert normalize_input_value(f, None) is None


def test_normalize_input_value_rejects_dict_on_csv_filter():
    """A mapping into a CSV filter fails loud instead of leaking its KEYS.

    The ``in`` / ``range`` arms iterate ``raw_value`` element-by-element;
    the pre-guard arms SPLATTED a mapping container into its keys -- a direct
    ``apply_sync`` patch like ``{'start': 1, 'end': 5}`` on a ``__range`` CSV
    leaf normalized to ``['start', 'end']``, silently swapping the caller's
    values for the mapping's keys in the form-data dict. The shape is invalid
    (the schema declares these inputs as GraphQL lists), so the normalizer
    fails loud with the typed error instead of guessing an element source.
    """

    class CharInFilter(BaseInFilter, CharFilter):
        pass

    f = CharInFilter(field_name="code", lookup_expr="in")
    with pytest.raises(ConfigurationError, match="non-list container"):
        normalize_input_value(f, {"start": 1, "end": 5})


def test_normalize_input_value_rejects_scalar_on_list_filter():
    """A scalar (string / int) into a list-consuming arm fails loud.

    A ``str`` container previously iterated its CHARACTERS -- ``"abc"``
    became ``['a', 'b', 'c']`` -- the same silent shape-coercion defect class
    as the dict-keys leak, so the guard rejects every non-list container.
    """
    with pytest.raises(ConfigurationError, match="non-list container"):
        normalize_input_value(ListFilter(), "abc")
    with pytest.raises(ConfigurationError, match="non-list container"):
        normalize_input_value(GlobalIDMultipleChoiceFilter(), 42)


def test_normalize_input_value_rejects_dict_on_expanded_range_csv():
    """The expanded ``__range`` CSV leaf rejects a {start, end} patch shape.

    The expanded ``__range`` filter is a ``BaseCSVFilter`` (element-binding
    ``[start, end]`` list over the wire); only the package's own
    ``RangeFilter`` primitive owns the ``{start, end}`` mapping shape through
    its ``RangeField`` patch. A dict into the CSV branch must fail loud,
    never normalize its keys into the membership list.
    """
    from django_filters import BaseRangeFilter, NumberFilter

    class IntRange(BaseRangeFilter, NumberFilter):
        pass

    with pytest.raises(ConfigurationError, match="non-list container"):
        normalize_input_value(IntRange(), {"start": 1, "end": 5}, field_name="code__range")


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
    metadata = get_args(result)[1:]
    # The strawberry.lazy marker is a `StrawberryLazyReference` whose
    # `module` attr carries the module path.
    assert any(getattr(marker, "module", None) == INPUTS_MODULE_PATH for marker in metadata)


def test_filter_input_type_returns_forwardref_in_annotation_args():
    """`Annotated[<str_variable>, ...]` wraps the string as a `ForwardRef`."""

    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    result = filter_input_type(MyFilter)
    inner = get_args(result)[0]
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
    """Repeated calls converge on one entry and equivalent ForwardRef args."""

    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    first = filter_input_type(MyFilter)
    second = filter_input_type(MyFilter)
    third = filter_input_type(MyFilter)
    assert len(_helper_referenced_filtersets) == 1
    assert get_args(first)[0].__forward_arg__ == get_args(second)[0].__forward_arg__
    assert get_args(second)[0].__forward_arg__ == get_args(third)[0].__forward_arg__


def test_filter_input_type_rejects_non_filterset():
    """`int` / non-FilterSet class / `None` all raise TypeError naming the bad value."""
    with pytest.raises(TypeError) as excinfo:
        # basedpyright: the non-class value is the hostile input under test; filter_input_type
        # types the parameter as type[FilterSet]
        filter_input_type(42)  # pyright: ignore[reportArgumentType]
    assert "42" in str(excinfo.value)

    class NotAFilter:
        pass

    with pytest.raises(TypeError):
        # basedpyright: the non-FilterSet class is the hostile input under test; filter_input_type
        # types the parameter as type[FilterSet]
        filter_input_type(NotAFilter)  # pyright: ignore[reportArgumentType]

    with pytest.raises(TypeError):
        # basedpyright: the None target is the hostile input under test; filter_input_type types
        # the parameter as type[FilterSet]
        filter_input_type(None)  # pyright: ignore[reportArgumentType]


# ---------------------------------------------------------------------------
# FilterInput[...] (the type-checkable spelling of filter_input_type)
# ---------------------------------------------------------------------------


def test_filter_input_subscript_returns_the_filter_input_type_annotation():
    """`FilterInput[MyFilter]` is the same lazy `Annotated` the call form returns."""

    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    subscripted = FilterInput[MyFilter]
    called = filter_input_type(MyFilter)
    assert get_origin(subscripted) is typing.Annotated
    inner = get_args(subscripted)[0]
    assert isinstance(inner, typing.ForwardRef)
    assert inner.__forward_arg__ == "MyFilterInputType"
    assert inner == get_args(called)[0]
    assert [getattr(marker, "module", None) for marker in get_args(subscripted)[1:]] == [
        INPUTS_MODULE_PATH,
    ]


def test_filter_input_subscript_records_filterset_into_helper_referenced_set():
    """The subscript feeds the one ledger the finalizer's orphan check reads."""

    class MyFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    FilterInput[MyFilter]
    assert _helper_referenced_filtersets == {MyFilter}
    filter_input_type(MyFilter)
    assert _helper_referenced_filtersets == {MyFilter}


def test_filter_input_subscript_rejects_non_filterset_naming_the_subscript():
    """A non-FilterSet raises TypeError worded with the spelling the consumer wrote."""

    class NotAFilter:
        pass

    with pytest.raises(TypeError) as excinfo:
        # basedpyright: a non-FilterSet subscript is the bad input this test proves is rejected
        FilterInput[NotAFilter]  # pyright: ignore[reportInvalidTypeArguments]
    assert str(excinfo.value).startswith("FilterInput[...] requires a FilterSet subclass; got ")
    assert "NotAFilter" in str(excinfo.value)
    with pytest.raises(TypeError, match=r"^filter_input_type\(\) requires a FilterSet subclass"):
        # basedpyright: the non-FilterSet class is the hostile input under test; filter_input_type
        # types the parameter as type[FilterSet]
        filter_input_type(NotAFilter)  # pyright: ignore[reportArgumentType]
    assert _helper_referenced_filtersets == set()


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
def test_pascal_case_raises_for_no_word_character_input(bad: str):
    """`_pascal_case` raises rather than silently returning `""`."""
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
def test_type_name_for_raises_for_no_word_character_field_path(bad: str):
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


def test_filter_convert_and_normalize_ride_shared_kind_table():
    """Convert and normalize walk one most-specific-first filter-class table.

    The two ladders used to be independent ``isinstance`` chains (spec-053 C3
    drift hazard). Both now zip ``_FILTER_INPUT_KIND_TYPES`` into
    ``convert_with_mro`` prechecks; ``object`` is last (the original ``else``).
    """
    from django_strawberry_framework.filters import inputs as inputs_mod

    for fn in (inputs_mod.convert_filter_to_input_annotation, inputs_mod.normalize_input_value):
        assert "convert_with_mro" in fn.__code__.co_names
        assert "_filter_input_prechecks" in fn.__code__.co_names
    assert _FILTER_INPUT_KIND_TYPES[-1] is object
    assert _FILTER_INPUT_KIND_TYPES[-3] is TypedFilter
    with pytest.raises(ValueError, match="argument"):
        _filter_input_prechecks(lambda _f: None)
    exc = _unexpected_filter_dispatch(object())
    assert isinstance(exc, ConfigurationError)
    assert "internal: filter input dispatch" in str(exc)


def test_convert_raw_pk_relation_filters_type_from_the_target_key_column():
    """The raw-pk pair types from the target key column, through a one-to-one primary key.

    ``Annotation.profile`` targets ``PatronProfile``, whose key is its ``patron``
    one-to-one: the input is ``Patron.id``'s ``Int`` (a list for the multi-valued class).
    """
    relation = library_models.Annotation._meta.get_field("profile")
    single = RelationPkFilter(field_name="profile", lookup_expr="exact")
    many = RelationPkMultipleFilter(field_name="profile", lookup_expr="in")
    assert convert_filter_to_input_annotation(single, relation) == (int | None)
    assert convert_filter_to_input_annotation(many, relation) == (list[int] | None)
    assert normalize_input_value(many, (3, 4)) == [3, 4]
    with pytest.raises(ConfigurationError, match="primary-key list"):
        normalize_input_value(many, 3)


def test_convert_raw_pk_filter_on_a_non_relation_names_the_leaf_and_related_filter():
    """A raw-pk filter whose ``field_name`` is not a relation fails at input build.

    The message names the leaf and points at ``RelatedFilter``, never at ``SCALAR_MAP``.
    """
    leaf = RelationPkFilter(field_name="title", lookup_expr="exact")
    with pytest.raises(ConfigurationError) as exc_info:
        convert_filter_to_input_annotation(leaf, library_models.Book._meta.get_field("title"))
    message = str(exc_info.value)
    assert "RelationPkFilter" in message
    assert "'title'" in message
    assert "RelatedFilter" in message
    assert "SCALAR_MAP" not in message


def test_filter_overrides_model_choice_keys_keep_their_class_and_type_from_the_target_key():
    """A ``filter_overrides``-selected model-choice key stays the consumer's, typed from its column.

    ``exact`` keeps django-filter's ``ModelChoiceFilter`` and ``in`` its
    ``ConcreteInFilter(BaseInFilter, ModelChoiceFilter)`` wrapper, both still holding
    their ``queryset`` (so the form still validates) and stamped ``override_generated``,
    which keeps them out of the optimizer's candidate rows. The input is the category
    pk: one ``Int`` for ``exact``, a list for ``in``.
    """
    import django_filters
    from django_filters.filters import BaseInFilter as DjangoBaseInFilter

    from django_strawberry_framework.filters.sets import filter_generation_provenance

    def _category_queryset_extra(_field: object) -> dict[str, object]:
        return {"queryset": Category.objects.all()}

    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"category": ["exact", "in"]}
            filter_overrides = {
                models.ForeignKey: {
                    "filter_class": django_filters.ModelChoiceFilter,
                    "extra": _category_queryset_extra,
                },
            }

    relation = Item._meta.get_field("category")
    exact = ItemFilter.get_filters()["category"]
    in_ = ItemFilter.get_filters()["category__in"]
    assert type(exact) is django_filters.ModelChoiceFilter
    assert isinstance(in_, DjangoBaseInFilter)
    assert isinstance(in_, django_filters.ModelChoiceFilter)
    for leaf in (exact, in_):
        assert leaf.queryset is not None
        assert leaf.queryset.model is Category
        record = filter_generation_provenance(leaf)
        assert record is not None
        assert record.origin == "override_generated"
    snapshot = ItemFilter._expansion_snapshot()
    assert snapshot is not None
    assert not {"category", "category__in"} & set(snapshot.candidates)
    assert convert_filter_to_input_annotation(exact, relation) == (int | None)
    assert convert_filter_to_input_annotation(in_, relation) == (list[int] | None)
    assert normalize_input_value(exact, 3) == 3
    assert normalize_input_value(in_, (3, 4)) == [3, 4]
    with pytest.raises(ConfigurationError, match="model-choice list"):
        normalize_input_value(in_, 3)


def test_declared_model_choice_filter_follows_a_relation_valued_primary_key():
    """A queryset whose model's key is a one-to-one types from the column that key stores.

    ``PatronProfile``'s primary key is its ``patron`` one-to-one, so the value the form
    cleans is ``Patron.id``: an ``Int``. A declared filter stays ``origin="declared"``.
    """
    import django_filters

    from django_strawberry_framework.filters.sets import filter_generation_provenance

    class AnnotationFilter(FilterSet):
        profile = django_filters.ModelChoiceFilter(
            queryset=library_models.PatronProfile.objects.all(),
        )

        class Meta:
            model = library_models.Annotation
            fields = ["id"]

    leaf = AnnotationFilter.get_filters()["profile"]
    record = filter_generation_provenance(leaf)
    assert record is not None
    assert record.origin == "declared"
    relation = library_models.Annotation._meta.get_field("profile")
    assert convert_filter_to_input_annotation(leaf, relation) == (int | None)


def test_model_choice_filter_with_no_column_source_names_the_filterset_and_the_fix():
    """A callable queryset on a ``method=`` filter naming no relation fails at input build.

    Neither source names a model: the callable queryset has none until a request
    arrives and ``field_name`` (``owner``) is no relation on ``Item``. The message names
    the FilterSet, the filter and both fixes, never ``SCALAR_MAP`` / ``Meta.exclude``.
    """
    import django_filters

    def _request_categories(_request: object) -> QuerySet[Category]:
        return Category.objects.all()

    class ItemFilter(FilterSet):
        owner = django_filters.ModelChoiceFilter(
            # basedpyright: types-django-filter types ``queryset`` as a ``QuerySet``;
            # ``QuerySetRequestMixin.get_queryset`` calls a callable one with the request
            queryset=_request_categories,  # pyright: ignore[reportArgumentType]
            method="filter_owner",
        )

        class Meta:
            model = Item
            fields = ["name"]

        def filter_owner(
            self,
            queryset: QuerySet[Item],
            _name: str,
            _value: object,
        ) -> QuerySet[Item]:
            return queryset

    with pytest.raises(ConfigurationError) as exc_info:
        _build_input_fields(ItemFilter)
    message = str(exc_info.value)
    assert message.startswith("ItemFilter: ModelChoiceFilter on 'owner'")
    assert "Pass a model queryset, or point field_name at a relation." in message
    assert "SCALAR_MAP" not in message
    assert "Meta.exclude" not in message


def test_normalize_input_value_typed_filter_unwraps_none_enum_value():
    """``TypedFilter`` is convert-only; normalize continues and may return ``None``."""

    class Tri(Enum):
        UNKNOWN = None

    assert normalize_input_value(TypedFilter(), Tri.UNKNOWN) is None


def test_normalize_input_value_list_filter_unwraps_each_element():
    """``ListFilter`` / ``ArrayFilter`` values normalize element-by-element."""
    f = ListFilter(field_name="ids")
    assert normalize_input_value(
        f,
        [1, 2, 3],
        field_name="ids",
    ) == [1, 2, 3]


def test_normalize_input_value_base_csv_filter_unwraps_elements():
    """``BaseCSVFilter`` normalizes element-by-element unwrapping enum members."""

    class StatusEnum(Enum):
        A = "a"
        B = "b"

    class CSVFilter(BaseInFilter, CharFilter):
        pass

    f = CSVFilter(field_name="status")
    assert normalize_input_value(
        f,
        [StatusEnum.A, StatusEnum.B],
        field_name="status",
    ) == ["a", "b"]


def test_convert_filter_to_input_annotation_derives_enum_for_choice_fields_on_list_and_csv_filters():
    """`_element_annotation` resolves choice enum for TypedFilter, ListFilter, and BaseCSVFilter."""
    model_field = library_models.Book._meta.get_field("circulation_status")

    # TypedFilter
    tf = TypedFilter(field_name="circulation_status")
    tf_anno = convert_filter_to_input_annotation(tf, model_field)
    tf_cls = next(arg for arg in get_args(tf_anno) if arg is not type(None))
    assert issubclass(tf_cls, Enum)

    # ListFilter
    lf = ListFilter(field_name="circulation_status")
    lf_anno = convert_filter_to_input_annotation(lf, model_field)
    lf_list = next(arg for arg in get_args(lf_anno) if arg is not type(None))
    assert get_origin(lf_list) is list
    assert issubclass(get_args(lf_list)[0], Enum)

    # BaseCSVFilter
    class CSVFilter(BaseInFilter, CharFilter):
        pass

    csv_f = CSVFilter(field_name="circulation_status")
    csv_anno = convert_filter_to_input_annotation(csv_f, model_field)
    csv_list = next(arg for arg in get_args(csv_anno) if arg is not type(None))
    assert get_origin(csv_list) is list
    assert issubclass(get_args(csv_list)[0], Enum)


def test_element_annotation_fallback_branches_when_model_field_is_none():
    """`_element_annotation` checks form field when model_field is None, fallback to str."""
    from django import forms

    class IntTypedFilter(TypedFilter):
        field_class = forms.IntegerField

    class NoFieldTypedFilter(TypedFilter):
        @property
        @override
        # basedpyright: deliberately a filter with no form field, the input that takes the fallback
        def field(self):  # pyright: ignore[reportIncompatibleMethodOverride]
            return None

    # Form field present -> resolved via `_scalar_from_form_field`
    assert convert_filter_to_input_annotation(IntTypedFilter(), None) == int | None

    # Neither model field nor form field -> fallback to `_scalar_from_model_field(None)` (`str`)
    assert convert_filter_to_input_annotation(NoFieldTypedFilter(), None) == str | None


def test_materialize_input_class_registers_in_module_globals():
    """`materialize_input_class` registers input classes into the module namespace."""
    from django_strawberry_framework.filters import inputs as inputs_mod

    class ScratchCustomInput:
        pass

    materialize_input_class("ScratchCustomInput", ScratchCustomInput)
    assert inputs_mod._materialized_names["ScratchCustomInput"] is ScratchCustomInput
    assert getattr(inputs_mod, "ScratchCustomInput", None) is ScratchCustomInput


def test_build_range_input_class_is_cached_on_the_filter_instance():
    """The same generation identity returns one cached class.

    Owned names over HTTP:
    ``test_scalars_filter_api.py::test_range_input_types_are_scoped_per_filterset``.
    """
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
    """No owning filterset -> the historical ``<Field>RangeInputType`` name is preserved.

    Live scoping of owned names:
    ``examples/fakeshop/test_query/test_scalars_filter_api.py::test_range_input_types_are_scoped_per_filterset``.
    """
    f = RangeFilter(field_name="price")
    assert _build_range_input_class(f, int).__name__ == "PriceRangeInputType"


@pytest.mark.django_db
def test_range_input_type_name_is_scoped_per_filterset():
    """Two filtersets sharing a ``field_name`` mint DISTINCT range sub-input classes.

    Pin for the spec-027 collision hazard. Shipped filtersets share one axis
    scalar, so the differing-axis claim is package-only. The nested
    ``RangeFilter`` sub-input class name derived from
    ``field_name`` alone, so two filtersets that each declare a ``RangeFilter``
    for a same-named column both stamped one GraphQL name
    (``PriceRangeInputType``). These nested classes are embedded directly in the
    annotation (NOT run through the Decision-9 materialization ledger nor the
    arguments-factory collision registry), so Strawberry does NOT raise on the
    clash -- it silently keeps whichever class it registers first and drops the
    other, advertising the wrong axis scalar for the loser. The name is now
    qualified by the owning filterset so the two are distinct and both survive in
    the schema.
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

    def _range_cls_of(bag: type):
        for annotation in bag.__annotations__.values():
            for arg in get_args(annotation):
                if getattr(arg, "__name__", "").endswith("RangeInputType"):
                    return arg
        raise AssertionError("no RangeInputType found in operator bag")

    def _bag(triples: list[tuple[str, object, dict[str, object]]]):
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

    # basedpyright: the class without _meta is the hostile input under test;
    # _model_field_for_filter types the parameter as type[FilterSet]
    assert _model_field_for_filter(_NoMeta, GlobalIDFilter(field_name="id")) is None  # pyright: ignore[reportArgumentType]


def test_model_field_for_filter_returns_none_without_field_name():
    """A filter with no ``field_name`` yields ``None`` even on a real model."""
    from tests.filters.fixtures.filtersets import ShelfFilter

    f = GlobalIDFilter()
    f.field_name = ""
    assert _model_field_for_filter(ShelfFilter, f) is None


def test_model_field_for_filter_returns_none_for_unknown_field_name():
    """A typo in ``Filter(field_name=...)`` surfaces as ``None``, not a crash.

    Path resolution is ``django_filters.utils.get_model_field`` (shared with
    ``filters/base.py`` / ``filters/sets.py``); an unknown hop returns ``None``.
    """
    from tests.filters.fixtures.filtersets import ShelfFilter

    f = GlobalIDFilter(field_name="nonexistent_field")
    assert _model_field_for_filter(ShelfFilter, f) is None


def test_model_field_for_filter_walks_related_path():
    """A ``__``-separated ``field_name`` resolves to the terminal model field."""
    from apps.library import models as library_models

    from tests.filters.fixtures.filtersets import ShelfFilter

    f = GlobalIDFilter(field_name="branch__name")
    field = _model_field_for_filter(ShelfFilter, f)
    assert field is library_models.Branch._meta.get_field("name")


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
# Digit-boundary operator-bag / range type names
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_build_input_fields_keeps_digit_boundary_operator_bags_distinct():
    """``field_2`` / ``field2`` mint DISTINCT operator-bag GraphQL type names.

    ``ClassBasedTypeNameMixin.type_name_for`` routes through ``pascal_case``. A
    non-injective Pascal collapse (``field_2`` / ``field2`` both -> ``Field2``)
    made both bags claim ``<FilterSet>Field2FilterInputType``. Those nested
    classes are embedded in annotations (not the spec-027 Decision 9 ledger), so
    Strawberry silently kept one bag and dropped the other -- wrong lookups on
    the wire. Top-level field attrs stay distinct via ``graphql_camel_name``;
    the type-name stem must preserve the same digit boundary.
    """
    import re

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
    # a root input with ``strawberry.lazy`` self-refs needs spec-027 Decision 9 materialization.
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


@pytest.mark.django_db
def test_build_input_fields_keeps_underscore_edge_operator_bags_distinct():
    """``price`` / ``price_`` mint DISTINCT operator-bag GraphQL type names.

    ``pascal_case`` used to drop leading / trailing underscore runs, so two
    members whose names differ only at the edges collapsed to one type-name
    stem even though BOTH emission guards passed (the Python attrs and the
    camel GraphQL field names stay distinct for edge variants). The two bag
    classes are embedded in annotations (not the spec-027 Decision 9 ledger),
    so Strawberry silently kept whichever registered first and dropped the
    other -- a ``CharFilter`` bag and a ``RangeFilter`` bag shared one wire
    type and one member's lookups vanished from the schema. The stem now
    preserves the edge runs (the Pascal dual of ``graphql_camel_name``).
    """
    import re

    class UnderscoreEdgeFilter(FilterSet):
        price = CharFilter(field_name="name", lookup_expr="exact")
        price_ = RangeFilter(field_name="city", lookup_expr="exact")

        class Meta:
            model = library_models.Branch
            fields = []

    triples = _build_input_fields(UnderscoreEdgeFilter)
    by_attr = {python_attr: annotation for python_attr, annotation, _kwargs in triples}

    def _bag(attr: str):
        return next(arg for arg in get_args(by_attr[attr]) if arg is not type(None))

    bag_plain = _bag("price")
    bag_under = _bag("price_")
    assert bag_plain.__name__ == "UnderscoreEdgeFilterPriceFilterInputType"
    assert bag_under.__name__ == "UnderscoreEdgeFilterPrice_FilterInputType"
    assert bag_plain is not bag_under
    # The two bags carry DIFFERENT shapes: the CharFilter bag's ``exact`` is a
    # scalar, the RangeFilter bag's ``exact`` embeds the range sub-input.
    assert "RangeInputType" not in str(bag_plain.__annotations__["exact"])
    assert "RangeInputType" in str(bag_under.__annotations__["exact"])

    @strawberry.type
    class Query:
        ok: int

    sdl = str(strawberry.Schema(query=Query, types=[bag_plain, bag_under]))
    bag_defs = set(re.findall(r"input (UnderscoreEdgeFilterPrice_?FilterInputType)", sdl))
    assert bag_defs == {
        "UnderscoreEdgeFilterPriceFilterInputType",
        "UnderscoreEdgeFilterPrice_FilterInputType",
    }
    # The range sub-input of the trailing-underscore member survives too
    # (pre-fix the whole bag was silently dropped at registration).
    assert "UnderscoreEdgeFilterCityRangeInputType" in sdl


@pytest.mark.django_db
def test_range_input_type_name_preserves_leading_underscore_run_in_field_name():
    """Range sub-input names keep ``_price`` distinct from ``price``."""

    class LeadingEdgeRangeFilter(FilterSet):
        price = RangeFilter(field_name="name")
        _price = RangeFilter(field_name="city")

        class Meta:
            model = library_models.Branch
            fields = []

    assert (
        _build_range_input_class(
            RangeFilter(field_name="name"),
            int,
            LeadingEdgeRangeFilter,
        ).__name__
        == "LeadingEdgeRangeFilterNameRangeInputType"
    )
    assert (
        _build_range_input_class(
            RangeFilter(field_name="city"),
            int,
            LeadingEdgeRangeFilter,
        ).__name__
        == "LeadingEdgeRangeFilterCityRangeInputType"
    )
    # The naming rule itself: the leading run survives into the stem.
    assert LeadingEdgeRangeFilter.type_name_for("_price") == (
        "LeadingEdgeRangeFilter_PriceFilterInputType"
    )
    assert LeadingEdgeRangeFilter.type_name_for("price") == (
        "LeadingEdgeRangeFilterPriceFilterInputType"
    )


# ---------------------------------------------------------------------------
# clear_filter_input_namespace - cycle-safe import guards
# ---------------------------------------------------------------------------


def test_clear_filter_input_namespace_tolerates_unimportable_submodules():
    """Both submodule lookups on the clear path are best-effort: skip, never raise.

    The heavy clear reaches ``FilterArgumentsFactory`` and ``FilterSet``
    through ``utils/inputs.py::_safe_import``, so an unimportable module
    yields ``None`` and only its dependent reset is skipped; the reachable
    ledger reset still completes (spec-027 Decision 9).
    """
    import sys

    factories_name = "django_strawberry_framework.filters.factories"
    sets_name = "django_strawberry_framework.filters.sets"
    saved = {name: sys.modules.get(name) for name in (factories_name, sets_name)}
    try:
        # Setting the module entry to ``None`` makes the best-effort lookup of
        # each module raise ImportError internally, exercising both skips.
        # basedpyright: typeshed types sys.modules values as ModuleType; the runtime accepts None
        # as the blocked-import sentinel
        sys.modules[factories_name] = None  # pyright: ignore[reportArgumentType]
        sys.modules[sets_name] = None  # pyright: ignore[reportArgumentType]
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


# ---------------------------------------------------------------------------
# Relay-RELATION ``isnull`` -> Boolean input
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_relay_relation_isnull_generates_boolean_input_not_globalid_list():
    """A framework-owned Relay-RELATION ``isnull`` lookup generates a Boolean input.

    An ``isnull`` lookup on a relation whose target is a Relay node
    (``Book.genres`` -> the Relay ``GenreType``) must stay an upstream
    ``BooleanFilter`` -- a null test is never a GlobalID -- while the SAME
    relation's ``exact`` still converts to the GlobalID list wire shape.

    Justified in-process fallback: NO live fakeshop ``/graphql/``
    surface exposes a DIRECT Relay-relation ``isnull``. Every fakeshop relation is
    declared as a ``RelatedFilter`` (a separate traversal mechanism, not a
    ``Meta.fields`` relation lookup), and the only ``Meta.fields`` ``isnull`` is
    ``Book.subtitle`` (a ``CharField``); ``test_kanban_api.py`` covers only the
    OWN-PK ``id`` ``isnull`` branch, not the relation branch corrected here.
    Adding a relation ``isnull`` to a shipped fakeshop filterset would mutate the
    live schema surface, so the schema-level annotation + coercion assertion is
    earned in-process instead. The low-level Python predicate shape stays in
    ``tests/filters/test_base.py``; this test pins the generated GraphQL INPUT.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class RelayRelationIsnullBookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"genres": ["isnull", "exact"]}

    genres_field = library_models.Book._meta.get_field("genres")

    # Routing: the Relay relation's ``isnull`` stays an upstream Boolean filter,
    # while the SAME relation's ``exact`` converts to the GlobalID list primitive.
    isnull_cls, _ = RelayRelationIsnullBookFilter.filter_for_lookup(genres_field, "isnull")
    exact_cls, _ = RelayRelationIsnullBookFilter.filter_for_lookup(genres_field, "exact")
    assert isnull_cls is BooleanFilter
    assert not issubclass(isnull_cls, (GlobalIDFilter, GlobalIDMultipleChoiceFilter))
    assert exact_cls is GlobalIDMultipleChoiceFilter

    # Generated input annotations: the ``isNull`` sub-field is a Boolean scalar;
    # the ``exact`` sub-field keeps the ``list[str]`` GlobalID list wire shape.
    triples = _build_input_fields(RelayRelationIsnullBookFilter)
    by_attr = {python_attr: annotation for python_attr, annotation, _kwargs in triples}
    genres_bag = next(arg for arg in get_args(by_attr["genres"]) if arg is not type(None))
    bag_annotations = {
        field.graphql_name: field.type_annotation.annotation
        for field in genres_bag.__strawberry_definition__.fields
    }
    assert bag_annotations["isNull"] == (bool | None)
    assert bag_annotations["exact"] == (list[str] | None)

    # Schema-level annotation + coercion: introspection reports ``isNull:
    # Boolean``, and the resolver ACCEPTS ``true`` / ``false`` while REJECTING a
    # non-Boolean. The former GlobalID/list coercion would instead accept a
    # String and reject the Boolean. The resolver's annotations are assigned as
    # real objects (not strings) so this module's ``from __future__ import
    # annotations`` cannot stringify the per-test bag class out of scope.
    # basedpyright: the resolver's GraphQL argument type is assigned through __annotations__ below
    def _probe(genres=None) -> str:  # pyright: ignore[reportMissingParameterType, reportUnknownParameterType]
        if genres is None:
            return "omitted"
        return f"isNull={genres.is_null!r}"

    _probe.__annotations__ = {"genres": genres_bag | None, "return": str}

    @strawberry.type
    class Query:
        probe: str = strawberry.field(resolver=_probe)

    schema = strawberry.Schema(query=Query)

    introspection = schema.execute_sync(
        """
        {
          __type(name: "RelayRelationIsnullBookFilterGenresFilterInputType") {
            inputFields { name type { kind name } }
          }
        }
        """,
    )
    assert introspection.errors is None, introspection.errors
    assert introspection.data is not None
    input_fields = {
        field["name"]: field["type"] for field in introspection.data["__type"]["inputFields"]
    }
    assert input_fields["isNull"] == {"kind": "SCALAR", "name": "Boolean"}
    # ``exact`` is the GlobalID membership list, NOT a Boolean scalar.
    assert input_fields["exact"]["kind"] == "LIST"

    accepted_true = schema.execute_sync("{ probe(genres: { isNull: true }) }")
    assert accepted_true.errors is None, accepted_true.errors
    assert accepted_true.data == {"probe": "isNull=True"}

    accepted_false = schema.execute_sync("{ probe(genres: { isNull: false }) }")
    assert accepted_false.errors is None, accepted_false.errors
    assert accepted_false.data == {"probe": "isNull=False"}

    rejected_string = schema.execute_sync('{ probe(genres: { isNull: "not-a-bool" }) }')
    assert rejected_string.errors, rejected_string
    assert "Boolean cannot represent" in str(rejected_string.errors[0])
