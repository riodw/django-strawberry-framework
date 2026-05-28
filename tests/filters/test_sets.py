"""Tests for `django_strawberry_framework/filters/sets.py` (Slice 1).

Covers the metaclass (`FilterSetMetaclass`), `FilterSet`'s class-creation
behavior (cycle-safe `get_filters` expansion + `_get_fields` narrowing),
the Decision-4 owner-aware Relay-vs-scalar conditional in
`filter_for_field`, and the Decision-8 / M1-of-rev5 apply pipeline
(`apply_sync` / `apply_async` / `apply` + the five named helpers).
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

import pytest
import strawberry
from apps.library import models as library_models
from apps.products.models import Category, Item
from django.http import HttpRequest
from graphql import GraphQLError

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    FilterSet,
    FilterSetMetaclass,
    GlobalIDFilter,
    GlobalIDMultipleChoiceFilter,
    RelatedFilter,
)
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.relay import SyncMisuseError, apply_interfaces


class ShelfProxy(library_models.Shelf):
    """Module-scope proxy of ``Shelf`` for the model-mismatch precheck test.

    Declared at module scope (not inside the test body) so Django's app
    registry sees it during normal app loading; late-bound model
    registration inside a function body has shifting tolerance across
    Django releases.
    """

    class Meta:
        proxy = True
        app_label = "library"


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    yield
    registry.clear()


def _make_info(request: HttpRequest | None = None) -> Any:
    """Return a minimal `info`-shaped object carrying `info.context.request`."""

    class _Context:
        def __init__(self, req: HttpRequest):
            self.request = req

    class _Info:
        def __init__(self, ctx):
            self.context = ctx

    return _Info(_Context(request or HttpRequest()))


# ---------------------------------------------------------------------------
# Metaclass behavior
# ---------------------------------------------------------------------------


def test_filterset_metaclass_is_django_filter_metaclass_subclass():
    from django_filters.filterset import FilterSetMetaclass as DjangoFilterMetaclass

    assert issubclass(FilterSetMetaclass, DjangoFilterMetaclass)


def test_filterset_metaclass_collects_related_filters():
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    assert isinstance(BranchFilter.related_filters, OrderedDict)
    assert "shelves" in BranchFilter.related_filters
    assert BranchFilter.related_filters["shelves"].bound_filterset is BranchFilter


def test_filterset_metaclass_aliases_filter_fields_to_fields():
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            filter_fields = {"code": ["exact"]}

    # Aliasing happens at metaclass time; the `Meta.fields` attribute lands.
    assert ShelfFilter._meta.fields == {"code": ["exact"]}


def test_filterset_metaclass_does_not_expand_at_class_creation():
    class ShelfFilter(FilterSet):
        # `RelatedFilter("SiblingFilter")` references a class declared LATER.
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter("ShelfFilter", field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # Class creation succeeded with a string forward reference; nothing cached yet.
    assert BranchFilter.__dict__.get("_expanded_filters") is None


# ---------------------------------------------------------------------------
# get_filters expansion
# ---------------------------------------------------------------------------


def test_filterset_get_filters_triggers_expansion():
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact", "icontains"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    filters = BranchFilter.get_filters()
    # Same-class filter plus expanded `<rel>__<child_lookup>` keys.
    assert "name" in filters
    assert "shelves__code" in filters
    assert "shelves__code__icontains" in filters


def test_filterset_get_filters_caches_after_full_resolution():
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    first = BranchFilter.get_filters()
    second = BranchFilter.get_filters()
    assert first is second
    assert BranchFilter.__dict__.get("_expanded_filters") is first


def test_filterset_get_filters_resets_expansion_guard():
    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    BranchFilter.get_filters()
    assert BranchFilter._is_expanding_filters is False


def test_filterset_get_filters_does_not_cache_when_string_filterset_remains():
    class BranchFilter(FilterSet):
        # Reference to a non-existent class — `expand_related_filter` raises.
        bogus = RelatedFilter("DefinitelyDoesNotExistFilter", field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    with pytest.raises(ImportError):
        BranchFilter.get_filters()
    assert BranchFilter.__dict__.get("_expanded_filters") is None


# ---------------------------------------------------------------------------
# _get_fields override
# ---------------------------------------------------------------------------


def test_filterset_get_fields_includes_pk_for_all_fields_shorthand():
    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = "__all__"

    fields = ItemFilter.get_fields()
    pk_name = Item._meta.pk.name
    assert pk_name in fields


def test_filterset_get_fields_excludes_m2m_for_all_fields_shorthand():
    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = "__all__"

    fields = BookFilter.get_fields()
    # `Book.genres` is an M2M relation; it must be excluded.
    assert "genres" not in fields


def test_filterset_get_fields_does_not_alter_explicit_dict_meta():
    class ItemFilter(FilterSet):
        class Meta:
            model = Item
            fields = {"name": ["exact"]}

    fields = ItemFilter.get_fields()
    # Explicit dict is returned by `super().get_fields()` unchanged.
    assert set(fields.keys()) == {"name"}


# ---------------------------------------------------------------------------
# Decision-4 owner-aware filter_for_field
# ---------------------------------------------------------------------------


def test_filter_for_field_picks_global_id_multiple_choice_filter_for_relay_m2m_target():
    """An M2M to a Relay-Node-shaped target maps to `GlobalIDMultipleChoiceFilter`.

    Decision 4 ports BOTH `GlobalIDFilter` (single-valued) and
    `GlobalIDMultipleChoiceFilter` (multi-valued); the runtime override
    has to pick the multi-valued primitive for `ManyToManyField` so the
    underlying queryset semantics match the field's cardinality.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    # The finalizer's owner-binding pass lands in Slice 3; here we just need
    # `GenreType` to be a subclass of `relay.Node` so `implements_relay_node`
    # returns `True`. `apply_interfaces` is the existing Slice-4-of-spec-011
    # helper that injects bases.
    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    class BookFilter(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("genres")
    resolved = BookFilter.filter_for_field(field, "genres")
    assert isinstance(resolved, GlobalIDMultipleChoiceFilter)


def test_filter_for_field_picks_global_id_filter_for_relay_forward_fk_target():
    """A forward FK to a Relay-Node-shaped target maps to `GlobalIDFilter`.

    Complement of the M2M case above — single-valued relations pick the
    single-value Relay primitive.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(ShelfType, ShelfType.__django_strawberry_definition__)

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(field, "shelf")
    assert isinstance(resolved, GlobalIDFilter)
    assert not isinstance(resolved, GlobalIDMultipleChoiceFilter)


def test_filter_for_field_picks_scalar_filter_for_non_relay_target():
    """A non-Relay `DjangoType` target returns whatever upstream produced (not GlobalIDFilter)."""

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BookFilter(FilterSet):
        shelf = RelatedFilter(ShelfFilter, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(field, "shelf")
    assert not isinstance(resolved, GlobalIDFilter)


def test_filter_for_field_returns_default_when_target_model_not_registered():
    """No registered `DjangoType` for the target -> upstream default unchanged."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    resolved = BookFilter.filter_for_field(field, "shelf")
    assert not isinstance(resolved, GlobalIDFilter)


# ---------------------------------------------------------------------------
# Apply pipeline — request extraction
# ---------------------------------------------------------------------------


def test_request_from_info_uses_context_request_attribute():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    request = HttpRequest()
    info = _make_info(request)
    assert CategoryFilter._request_from_info(info) is request


def test_request_from_info_falls_back_to_bare_http_request():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    class _Info:
        def __init__(self):
            self.context = HttpRequest()

    info = _Info()
    assert CategoryFilter._request_from_info(info) is info.context


def test_request_from_info_raises_for_unsupported_context_shape():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    class _Info:
        context = object()

    with pytest.raises(ConfigurationError):
        CategoryFilter._request_from_info(_Info())


# ---------------------------------------------------------------------------
# Apply pipeline — normalize_input
# ---------------------------------------------------------------------------


def test_normalize_input_returns_empty_dict_for_none():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._normalize_input(None) == {}


def test_normalize_input_skips_none_valued_attrs():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input({"name": None, "i_contains": "foo"})
    assert "name" not in data
    assert data == {"icontains": "foo"}


def test_normalize_input_maps_in_python_attr_to_in_form_data_key():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["in"]}

    data = CategoryFilter._normalize_input({"in_": [1, 2, 3]})
    assert "in" in data
    assert data["in"] == [1, 2, 3]


def test_normalize_input_maps_logic_keys_to_short_form():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input(
        {
            "and_": [{"name": "foo"}],
            "or_": [{"name": "bar"}],
            "not_": {"name": "baz"},
        },
    )
    assert data["and"] == [{"name": "foo"}]
    assert data["or"] == [{"name": "bar"}]
    assert data["not"] == {"name": "baz"}


def test_normalize_input_signature_takes_only_input_value():
    """``_normalize_input`` accepts only ``input_value``; no dead owner parameter.

    GlobalID type-name validation happens at queryset-evaluation time
    inside the filter's ``filter()`` method, reading the owner via
    ``filter_instance.parent._owner_definition``. The normalize step
    therefore does not need an owner parameter — passing one is dead
    plumbing that suggests an unfinished wiring path.
    """
    import inspect

    sig = inspect.signature(FilterSet._normalize_input)
    # `cls` is bound on a classmethod's underlying function, so the public
    # signature carries `input_value` only.
    assert list(sig.parameters) == ["input_value"]


def test_normalize_input_walks_strawberry_dataclass():
    """A dataclass-shaped input (Strawberry input) is walked via `__dataclass_fields__`."""

    @strawberry.input
    class _Input:
        name: str | None = strawberry.UNSET

    value = _Input(name="hello")
    # `__dataclass_fields__` carries the declared field names.

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input(value)
    assert data.get("name") == "hello"


def test_normalize_input_inner_bag_loop_skips_unset_lookups():
    """Partial operator bags don't leak ``UNSET`` into form data.

    Strawberry input dataclasses default every operator-bag lookup
    (``exact``, ``i_contains``, ``in_``, ...) to ``UNSET`` rather than
    ``None``. The inner loop in ``_normalize_input`` must skip UNSET
    the same way the outer loop does; otherwise the UNSET sentinel
    reaches ``normalize_input_value`` and either raises
    ``TypeError: argument of type 'UNSET' is not iterable`` (list-like
    filters) or lands in ``data[form_key]`` as a bogus value (scalar
    filters). The common case is a consumer who supplies one lookup
    but not the others — partially-supplied bags must not break.
    """

    @strawberry.input
    class _Bag:
        exact: str | None = strawberry.UNSET
        i_contains: str | None = strawberry.UNSET

    @strawberry.input
    class _Input:
        name: _Bag | None = strawberry.UNSET

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    # Bag with only ``i_contains`` supplied; ``exact`` defaults to UNSET.
    bag = _Bag(i_contains="foo")
    data = CategoryFilter._normalize_input(_Input(name=bag))
    # The UNSET ``exact`` does NOT pollute form-data as ``name=UNSET``.
    assert "name" not in data
    # The supplied ``i_contains`` lands at its django-filter form key.
    assert data.get("name__icontains") == "foo"


def test_normalize_input_skips_strawberry_unset_attrs():
    """``strawberry.UNSET`` attrs are skipped the same as ``None``.

    Strawberry input dataclasses default unsupplied fields to ``UNSET``
    rather than ``None``. Leaving them in ``data`` would route them
    through the parent form and surface as a spurious "missing /
    invalid" form error for fields the consumer never sent.
    """

    @strawberry.input
    class _Input:
        name: str | None = strawberry.UNSET

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input(_Input())
    assert "name" not in data


# ---------------------------------------------------------------------------
# Apply pipeline — validate_form_or_raise
# ---------------------------------------------------------------------------


def test_validate_form_or_raise_raises_on_invalid_form():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"id": ["exact"]}

    instance = CategoryFilter(data={"id": "not-an-integer"}, queryset=Category.objects.all())
    with pytest.raises(GraphQLError) as excinfo:
        CategoryFilter._validate_form_or_raise(instance)
    error = excinfo.value
    assert error.extensions["code"] == "FILTER_INVALID"
    # `errors` is the structured dict per `ErrorDict.get_json_data()`.
    assert "id" in error.extensions["errors"]


def test_validate_form_or_raise_passes_for_valid_form():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    instance = CategoryFilter(data={"name": "anything"}, queryset=Category.objects.all())
    # No raise expected.
    CategoryFilter._validate_form_or_raise(instance)


# ---------------------------------------------------------------------------
# Apply pipeline — permission checks
# ---------------------------------------------------------------------------


def test_run_permission_checks_fires_only_for_active_input_fields():
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            fired.append("name")

    CategoryFilter._run_permission_checks({}, request=HttpRequest())
    assert fired == []

    CategoryFilter._run_permission_checks({"name": "anything"}, request=HttpRequest())
    assert fired == ["name"]


def test_run_permission_checks_skips_unset_related_branch():
    """``strawberry.UNSET`` on a related branch is treated as "not supplied".

    Strawberry input dataclasses default unsupplied fields to ``UNSET``
    rather than ``None``. The active-branch detection in
    ``_iter_active_related_branches`` must collapse UNSET so the parent
    per-branch permission gate does not fire for fields the consumer
    never sent.
    """
    fired: list[str] = []

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    @strawberry.input
    class BranchInput:
        name: str | None = strawberry.UNSET
        shelves: Any = strawberry.UNSET

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def check_shelves_permission(self, request):
            fired.append("shelves")

    BranchFilter._run_permission_checks(BranchInput(), request=HttpRequest())
    assert fired == []


def test_run_permission_checks_recurses_into_active_related_branch():
    fired: list[str] = []

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def check_code_permission(self, request):
            fired.append("shelf.code")

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    BranchFilter._run_permission_checks({"name": "x"}, request=HttpRequest())
    assert fired == []

    BranchFilter._run_permission_checks(
        {"shelves": {"code": "anything"}},
        request=HttpRequest(),
    )
    assert "shelf.code" in fired


def test_run_permission_checks_recurses_into_logical_branches():
    """Per-call dedup: a gate fires once even when the field appears in many branches.

    The recursion correctly walks ``and`` / ``or`` / ``not`` sub-trees
    so a nested field is gated the same as a top-level one. The dedup
    keys on ``check_<field>_permission`` method names for the lifetime
    of one top-level call; a field appearing in multiple ``or`` arms
    fires its gate ONCE per call (the gate's logic is idempotent, so
    multi-firing is functionally harmless but produces duplicate audit
    log entries — the R4 contract dedupes to avoid that).
    """
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            fired.append("name")

    # ``and`` with the same field in two arms fires the gate ONCE.
    CategoryFilter._run_permission_checks(
        {"and_": [{"name": "foo"}, {"name": "bar"}]},
        request=HttpRequest(),
    )
    assert fired == ["name"]
    fired.clear()

    # ``or`` with the same field fires ONCE.
    CategoryFilter._run_permission_checks(
        {"or_": [{"name": "foo"}]},
        request=HttpRequest(),
    )
    assert fired == ["name"]
    fired.clear()

    # ``not`` with the field fires ONCE.
    CategoryFilter._run_permission_checks(
        {"not_": {"name": "baz"}},
        request=HttpRequest(),
    )
    assert fired == ["name"]
    fired.clear()

    # A fresh top-level call gets a fresh dedup set; the gate fires
    # again because it's a new call.
    CategoryFilter._run_permission_checks({"name": "x"}, request=HttpRequest())
    assert fired == ["name"]


def test_run_permission_checks_dedups_child_gate_across_sibling_branches():
    """A child filterset gate fires once even when entered from sibling ``or`` arms.

    The ``_fired`` map is keyed by ``FilterSet`` class and shared across
    BOTH the logical-branch recursion and the child-filterset recursion.
    So ``or: [{shelves: {...}}, {shelves: {...}}]`` enters ``ShelfFilter``
    twice (once per arm) but its ``check_code_permission`` fires only
    once — the per-class set keyed on ``ShelfFilter`` dedups the second
    entry. The parent's per-branch ``check_shelves_permission`` likewise
    fires once (deduped on the parent's per-class set).
    """
    fired: list[str] = []

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

        def check_code_permission(self, request):
            fired.append("shelf.code")

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

        def check_shelves_permission(self, request):
            fired.append("branch.shelves")

    BranchFilter._run_permission_checks(
        {
            "or_": [
                {"shelves": {"code": "a"}},
                {"shelves": {"code": "b"}},
            ],
        },
        request=HttpRequest(),
    )
    # Parent per-branch gate fires once; child class gate fires once —
    # NOT once per arm.
    assert fired.count("branch.shelves") == 1
    assert fired.count("shelf.code") == 1


def test_run_permission_checks_caps_logical_branch_nesting():
    """Pathologically-deep nesting raises ``ConfigurationError`` instead of stack-overflow.

    ``_MAX_LOGIC_DEPTH`` caps the recursion so a malicious or
    accidental ``{and: [{and: [{and: [...]}]}]}`` shape surfaces a
    typed error at the source instead of a Python ``RecursionError``.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    # Build a 20-deep ``and`` chain — well past the 8-level cap.
    deep: dict = {"name": "leaf"}
    for _ in range(20):
        deep = {"and_": [deep]}

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter._run_permission_checks(deep, request=HttpRequest())
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)


def test_max_logic_depth_is_overridable_classvar():
    """A subclass can raise ``_MAX_LOGIC_DEPTH`` without monkey-patching.

    The cap is a ``ClassVar`` on ``FilterSet`` so a consumer with a
    legitimate deeper-nesting case (machine-generated queries) can
    subclass and override it. A 12-deep chain that trips the default
    cap of 8 is accepted under an override of 32.
    """

    class DeepCategoryFilter(FilterSet):
        _MAX_LOGIC_DEPTH = 32

        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    deep: dict = {"name": "leaf"}
    for _ in range(12):
        deep = {"and_": [deep]}

    # No raise: 12 levels is under the subclass's raised cap of 32.
    DeepCategoryFilter._run_permission_checks(deep, request=HttpRequest())

    # The base class still caps at 8 — the override is subclass-local.
    class ShallowCategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError):
        ShallowCategoryFilter._run_permission_checks(deep, request=HttpRequest())


@pytest.mark.django_db
def test_evaluate_logic_tree_preserves_request_context():
    captured_requests: list[Any] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def filter_queryset(self, queryset):
            captured_requests.append(self.request)
            return super().filter_queryset(queryset)

    request = HttpRequest()
    info = _make_info(request)
    CategoryFilter.apply_sync(
        {"and_": [{"name": "alpha"}]},
        Category.objects.all(),
        info,
    )
    assert len(captured_requests) > 0
    # First entry in captured_requests is from the parent category filter,
    # and subsequent are from the nested logic branch evaluation.
    # All of them must preserve the same HttpRequest object.
    for req in captured_requests:
        assert req is request


# ---------------------------------------------------------------------------
# Apply pipeline — full apply_sync path
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_apply_sync_filters_against_simple_scalar_input():
    Category.objects.create(name="alpha")
    Category.objects.create(name="beta")

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    info = _make_info()
    qs = CategoryFilter.apply_sync({"name": "alpha"}, Category.objects.all(), info)
    assert list(qs.values_list("name", flat=True)) == ["alpha"]


@pytest.mark.django_db
def test_apply_sync_passes_through_empty_filter_input():
    Category.objects.create(name="alpha")
    Category.objects.create(name="beta")

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    info = _make_info()
    qs = CategoryFilter.apply_sync({}, Category.objects.all(), info)
    assert qs.count() == 2


@pytest.mark.django_db
def test_apply_sync_raises_graphql_error_on_invalid_input():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"id": ["exact"]}

    info = _make_info()
    with pytest.raises(GraphQLError):
        CategoryFilter.apply_sync({"id": "not-an-integer"}, Category.objects.all(), info)


# ---------------------------------------------------------------------------
# Apply pipeline — dispatcher catch-and-rethrow
# ---------------------------------------------------------------------------


def test_apply_dispatcher_rethrows_sync_misuse_with_clearer_message():
    """A ``SyncMisuseError`` from ``apply_sync`` becomes ``RuntimeError``.

    Class-based dispatch: the dispatcher catches the typed subclass
    directly (no substring match) and rethrows with the actionable
    "use apply_async instead" message.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        @classmethod
        def apply_sync(cls, *args, **kwargs):
            raise SyncMisuseError("FakeType.get_queryset returned a coroutine.")

    with pytest.raises(RuntimeError) as excinfo:
        CategoryFilter.apply(None, Category.objects.all(), _make_info())
    assert "apply_async" in str(excinfo.value)


def test_apply_dispatcher_propagates_other_configuration_errors():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        @classmethod
        def apply_sync(cls, *args, **kwargs):
            raise ConfigurationError("totally unrelated configuration problem")

    with pytest.raises(ConfigurationError):
        CategoryFilter.apply(None, Category.objects.all(), _make_info())


def test_apply_dispatcher_propagates_other_runtime_errors():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        @classmethod
        def apply_sync(cls, *args, **kwargs):
            raise RuntimeError("not a sync-misuse error")

    with pytest.raises(RuntimeError) as excinfo:
        CategoryFilter.apply(None, Category.objects.all(), _make_info())
    assert "not a sync-misuse error" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Apply pipeline — _apply_related_constraints active-branch scoping
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_apply_related_constraints_runs_active_branch_only():
    branch = library_models.Branch.objects.create(name="alpha")
    library_models.Shelf.objects.create(branch=branch, code="active")
    library_models.Shelf.objects.create(branch=branch, code="hidden")
    other = library_models.Branch.objects.create(name="beta")
    library_models.Shelf.objects.create(branch=other, code="other-shelf")

    explicit_qs = library_models.Shelf.objects.filter(code="active")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves", queryset=explicit_qs)

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # Inactive branch: no constraint applied.
    parent_qs = library_models.Branch.objects.all()
    constrained = BranchFilter._apply_related_constraints({"name": "alpha"}, parent_qs, {})
    assert "shelves__in" not in str(constrained.query)

    # Active branch: constraint applied.
    constrained_active = BranchFilter._apply_related_constraints(
        {"shelves": {"code": "active"}},
        parent_qs,
        {},
    )
    # The active branch must restrict the parent count to branches whose
    # shelves intersect the explicit `code="active"` queryset.
    sql = str(constrained_active.query).lower()
    assert "library_shelf" in sql
    assert "active" in sql
    # And materializing the queryset returns only the branch with an active shelf.
    assert list(constrained_active.values_list("name", flat=True)) == ["alpha"]


@pytest.mark.django_db
def test_apply_related_constraints_model_mismatch_raises_configuration_error():
    """A divergent-model ``RelatedFilter(queryset=...)`` surfaces ``ConfigurationError``.

    Django raises ``AssertionError: Cannot combine queries on two
    different base models`` when ``explicit & child_qs`` is called
    against mismatched base models. The opaque assertion is replaced
    with a typed ``ConfigurationError`` naming the offending filter
    and both models, so a GraphQL consumer sees an actionable message
    instead of a raw Django assertion.
    """
    # Branch has shelves; the consumer accidentally passes a Book qs as
    # the explicit constraint for the ``shelves`` branch.
    library_models.Branch.objects.create(name="alpha")
    wrong_model_qs = library_models.Book.objects.all()

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves", queryset=wrong_model_qs)

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # The child_qs_by_branch dict carries the correctly-modeled child qs
    # (Shelf); the explicit constraint is the wrong model (Book). The
    # precheck must surface ConfigurationError.
    child_shelf_qs = library_models.Shelf.objects.all()
    with pytest.raises(ConfigurationError) as excinfo:
        BranchFilter._apply_related_constraints(
            {"shelves": {"code": "active"}},
            library_models.Branch.objects.all(),
            {"shelves": child_shelf_qs},
        )
    msg = str(excinfo.value)
    assert "Book" in msg
    assert "Shelf" in msg
    assert "shelves" in msg


@pytest.mark.django_db
def test_apply_related_constraints_proxy_model_is_rejected():
    """Proxy models are rejected because Django's ``&`` rejects them.

    Django's ``Query.combine`` compares ``self.model != rhs.model``
    via identity, so a proxy and its concrete parent (which share a
    database table) are still rejected by ``&``. The precheck
    surfaces a typed ``ConfigurationError`` BEFORE the consumer hits
    the raw ``TypeError`` so the failure mode is actionable. The
    docstring on ``_apply_related_constraints`` explicitly carves
    proxy / MTI out of the accepted shapes.

    ``ShelfProxy`` is defined at module scope (see top of file) so the
    app registry registers it at import time.
    """
    library_models.Branch.objects.create(name="alpha")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        # Explicit queryset is keyed on the proxy; the target filterset
        # is keyed on the concrete model. Django's combine rejects
        # this; the precheck surfaces ConfigurationError instead.
        shelves = RelatedFilter(
            ShelfFilter,
            field_name="shelves",
            queryset=ShelfProxy.objects.all(),
        )

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    child_shelf_qs = library_models.Shelf.objects.all()
    with pytest.raises(ConfigurationError) as excinfo:
        BranchFilter._apply_related_constraints(
            {"shelves": {"code": "active"}},
            library_models.Branch.objects.all(),
            {"shelves": child_shelf_qs},
        )
    assert "ShelfProxy" in str(excinfo.value)
    assert "Shelf" in str(excinfo.value)


@pytest.mark.django_db
def test_apply_sync_passes_constrained_queryset_to_filterset_instance():
    """H3-of-rev8 pipeline ordering — constraints land in `self.queryset`.

    `apply_sync` must apply `_apply_related_constraints` BEFORE
    constructing the `FilterSet` instance so the explicit
    `RelatedFilter(queryset=...)` ledger and the visibility queryset
    propagate through to `.qs` via `self.queryset`. A future refactor
    that instantiates first and mutates `self._queryset` afterwards
    would not carry the constraint through `BaseFilterSet`'s internal
    `filter_queryset` path; this test pins the order.
    """
    branch = library_models.Branch.objects.create(name="alpha")
    library_models.Shelf.objects.create(branch=branch, code="active")

    explicit_qs = library_models.Shelf.objects.filter(code="active")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    captured: dict[str, Any] = {}
    real_init = FilterSet.__init__

    def spy_init(self, *args, **kwargs):
        # Record the `queryset` kwarg every consumer-`FilterSet` subclass
        # receives during this call; the test asserts the kwarg carries
        # the `<rel>__in=<intersected>` clause when the spy fires for
        # the parent class.
        captured.setdefault("calls", []).append(kwargs.get("queryset"))
        real_init(self, *args, **kwargs)

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves", queryset=explicit_qs)

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    FilterSet.__init__ = spy_init
    try:
        # Slice 2 strips related-branch keys from the form-data dict
        # before form validation (`shelves` is owned by
        # `_apply_related_constraints`, not the parent's form), so
        # `apply_sync` now returns normally. The contract this test
        # pins is unchanged: the constructor's `queryset=` kwarg must
        # carry the `<rel>__in=<intersected>` clause already baked in.
        # See `docs/builder/bld-slice-2-factories.md` for the
        # carry-forward rationale from Slice 1's spy-test fragility.
        BranchFilter.apply_sync(
            {"shelves": {"code": "active"}},
            library_models.Branch.objects.all(),
            _make_info(),
        )
    finally:
        FilterSet.__init__ = real_init

    parent_queryset = captured["calls"][0]
    assert parent_queryset is not None
    # The constrained queryset reached `BranchFilter.__init__` BEFORE the
    # filterset was constructed; the SQL carries the `<rel>__in=...`
    # clause that `_apply_related_constraints` baked in.
    sql = str(parent_queryset.query).lower()
    assert "library_shelf" in sql
    assert "active" in sql


# ---------------------------------------------------------------------------
# Apply pipeline — filter_queryset tree-form logic (Slice 4a)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_filter_queryset_intersects_and_branch():
    """``and: [{X}, {Y}]`` ANDs the leaf clauses (intersection)."""
    # Seed three branches: one matching both (name=match, city=match), one
    # matching only the name leaf, one matching only the city leaf.
    library_models.Branch.objects.create(name="match", city="match")
    library_models.Branch.objects.create(name="match-name-only", city="other")
    library_models.Branch.objects.create(name="match-city-only", city="match")

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"], "city": ["exact"]}

    qs = BranchFilter.apply_sync(
        {
            "and_": [
                {"name": "match"},
                {"city": "match"},
            ],
        },
        library_models.Branch.objects.all(),
        _make_info(),
    )
    assert list(qs.values_list("name", flat=True)) == ["match"]


@pytest.mark.django_db
def test_filter_queryset_unions_or_branch():
    """``or: [{X}, {Y}]`` ORs the leaf clauses (union, deduplicated)."""
    # Seed three branches: one matching X only, one matching Y only, one
    # matching neither. The union returns the first two.
    library_models.Branch.objects.create(name="x-row", city="ignored")
    library_models.Branch.objects.create(name="ignored", city="y-row")
    library_models.Branch.objects.create(name="other", city="other")

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"], "city": ["exact"]}

    qs = BranchFilter.apply_sync(
        {
            "or_": [
                {"name": "x-row"},
                {"city": "y-row"},
            ],
        },
        library_models.Branch.objects.all(),
        _make_info(),
    )
    # Order is not guaranteed by OR; assert the set.
    assert set(qs.values_list("name", flat=True)) == {"x-row", "ignored"}


@pytest.mark.django_db
def test_q_for_branch_validates_child_form_and_raises_on_malformed_subbranch():
    """A malformed nested ``and`` / ``or`` / ``not`` branch raises ``GraphQLError``.

    Without per-branch form validation, ``BaseFilterSet.qs`` silently
    falls through to ``filter_queryset`` on an invalid child form,
    producing an empty ``pk__in`` set instead of surfacing the input
    error. ``_q_for_branch`` must call ``_validate_form_or_raise`` on
    every nested instance so a typo or wrong-typed scalar in a deeper
    branch is rejected the same way a top-level malformed input is.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"id": ["exact"]}

    with pytest.raises(GraphQLError) as excinfo:
        CategoryFilter.apply_sync(
            {"and_": [{"id": "not-an-integer"}]},
            Category.objects.all(),
            _make_info(),
        )
    assert excinfo.value.extensions["code"] == "FILTER_INVALID"
    assert "id" in excinfo.value.extensions["errors"]


@pytest.mark.django_db
def test_filter_queryset_negates_not_branch():
    """``not: {X}`` negates against the parent queryset, not the bare manager.

    Visibility-before-filter contract: ``filter_queryset`` runs against
    the parent queryset the override receives; ``~Q(...)`` therefore
    excludes only rows inside that scope, not rows the parent already
    hid.
    """
    # Seed five branches; pre-filter the parent queryset to a four-row
    # scope (excluding "hidden"); the not-branch then excludes "x-row"
    # from inside that four-row scope, leaving three rows.
    library_models.Branch.objects.create(name="x-row")
    library_models.Branch.objects.create(name="keep-1")
    library_models.Branch.objects.create(name="keep-2")
    library_models.Branch.objects.create(name="keep-3")
    library_models.Branch.objects.create(name="hidden")

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    pre_scoped = library_models.Branch.objects.exclude(name="hidden")
    qs = BranchFilter.apply_sync(
        {"not_": {"name": "x-row"}},
        pre_scoped,
        _make_info(),
    )
    names = set(qs.values_list("name", flat=True))
    assert names == {"keep-1", "keep-2", "keep-3"}
    # The pre-scoped exclusion still applies — ``hidden`` is NOT in the
    # result even though the not-branch only mentions ``x-row``.
    assert "hidden" not in names
