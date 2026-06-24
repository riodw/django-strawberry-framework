"""FilterSet tests for Meta collection, validation, sync/async apply, and tree overrides.

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
from django_strawberry_framework.filters.sets import _lookups_for_field, _read_qs
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
        # Reference to a non-existent class - `expand_related_filter` raises.
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
            # ``Item.attachment`` is a ``FileField`` (spec-038 Slice 4) that
            # ``django-filter`` has no default filter for; the ``"__all__"``
            # sweep would otherwise raise on it. Excluding it keeps this test
            # focused on its intent: the shorthand adds the PK column.
            exclude = ("attachment",)

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

    Complement of the M2M case above - single-valued relations pick the
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
# Apply pipeline - request extraction
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
# Apply pipeline - normalize_input
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

    data = CategoryFilter._normalize_input(
        {
            "in_": [1, 2, 3],
        },
    )
    assert "in" in data
    assert data["in"] == [1, 2, 3]


def test_normalize_input_maps_logic_keys_to_short_form():
    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    data = CategoryFilter._normalize_input(
        {"and_": [{"name": "foo"}], "or_": [{"name": "bar"}], "not_": {"name": "baz"}},
    )
    assert data["and"] == [{"name": "foo"}]
    assert data["or"] == [{"name": "bar"}]
    assert data["not"] == {"name": "baz"}


def test_normalize_input_signature_takes_only_input_value():
    """``_normalize_input`` accepts only ``input_value``; no dead owner parameter.

    GlobalID type-name validation happens at queryset-evaluation time
    inside the filter's ``filter()`` method, reading the owner via
    ``filter_instance.parent._owner_definition``. The normalize step
    therefore does not need an owner parameter - passing one is dead
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
    but not the others - partially-supplied bags must not break.
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
# Apply pipeline - validate_form_or_raise
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
# Apply pipeline - permission checks
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
    log entries - the R4 contract dedupes to avoid that).
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
    once - the per-class set keyed on ``ShelfFilter`` dedups the second
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
            "or_": [{"shelves": {"code": "a"}}, {"shelves": {"code": "b"}}],
        },
        request=HttpRequest(),
    )
    # Parent per-branch gate fires once; child class gate fires once -
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

    # Build a 20-deep ``and`` chain - well past the 8-level cap.
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

    # The base class still caps at 8 - the override is subclass-local.
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
# Apply pipeline - full apply_sync path
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
def test_permission_checks_run_only_through_apply_entrypoint():
    """``apply_*`` is the sole permission-aware entry; the bare ``.qs`` path does not gate.

    Permission hooks fire from ``_run_permission_checks``, which
    ``apply_sync`` / ``apply_async`` invoke up-front (recursing into nested
    branches). The tree-composition path
    (``filter_queryset`` -> ``_q_for_branch`` -> ``.qs``) deliberately does
    NOT re-run permission checks -- it relies on that up-front call. This
    pins the contract (H-filters-7 of the pre-merge review): bypassing
    ``apply_*`` by constructing the filterset and reading ``.qs`` directly
    skips the gate, so ``apply_*`` must remain the only permission-aware
    entry point. If a future refactor moves filtering off ``apply_*`` this
    test fails loudly, so permissions are re-wired rather than silently lost.
    """
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            fired.append("name")

    Category.objects.create(name="alpha")

    # Through ``apply_sync`` (the legal entry): the gate fires.
    CategoryFilter.apply_sync({"name": "alpha"}, Category.objects.all(), _make_info())
    assert fired == ["name"]

    # Bypassing ``apply_*`` (direct construction + ``.qs``): the gate does NOT fire.
    fired.clear()
    bare = CategoryFilter(
        data={"name": "alpha"},
        queryset=Category.objects.all(),
        request=HttpRequest(),
    )
    list(bare.qs)
    assert fired == []


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
# Apply pipeline - dispatcher catch-and-rethrow
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
# Apply pipeline - _apply_related_constraints active-branch scoping
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
def test_active_related_branch_without_registered_target_raises():
    """An active related branch with no registered target type fails loud.

    ``_iter_visibility_steps`` raises ``ConfigurationError`` instead of
    skipping: the branch is active (the consumer supplied input for it),
    so skipping would drop the constraint entirely and return unfiltered
    parent rows - a filter the consumer believes is applied doing
    nothing. The same misconfiguration is caught at finalize time for
    schema-wired filtersets (``_bind_filtersets`` subpass 2.5); this
    pins the runtime guard for direct ``apply_*`` callers. An INACTIVE
    branch must not raise - declaring a ``RelatedFilter`` is fine until
    input activates it.
    """
    library_models.Branch.objects.create(name="alpha")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # No ShelfType registered: the active branch raises.
    with pytest.raises(ConfigurationError) as excinfo:
        BranchFilter.apply_sync(
            {"shelves": {"code": {"exact": "x"}}},
            library_models.Branch.objects.all(),
            _make_info(),
        )
    msg = str(excinfo.value)
    assert "shelves" in msg
    assert "no DjangoType is registered" in msg

    # Inactive branch: same filterset applies cleanly without the target.
    qs = BranchFilter.apply_sync(
        {"name": "alpha"},
        library_models.Branch.objects.all(),
        _make_info(),
    )
    assert list(qs.values_list("name", flat=True)) == ["alpha"]


@pytest.mark.django_db
def test_dict_operator_bag_filters_through_apply_sync():
    """A dict-shaped operator bag filters end-to-end via ``apply_sync``.

    Pins the ``_operator_bag_items`` dict-walk: before it, a dict bag
    fell through to the scalar branch and the filter silently applied
    nothing (every row returned).
    """
    Category.objects.create(name="alpha-match")
    Category.objects.create(name="beta")

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    qs = CategoryFilter.apply_sync(
        {"name": {"i_contains": "match"}},
        Category.objects.all(),
        _make_info(),
    )
    assert list(qs.values_list("name", flat=True)) == ["alpha-match"]


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
    """H3-of-rev8 pipeline ordering - constraints land in `self.queryset`.

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

    class ShelfType(DjangoType):
        """Registered target so the active ``shelves`` branch resolves."""

        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    captured: dict[str, Any] = {}
    real_init = FilterSet.__init__

    def spy_init(self, *args, **kwargs):
        # Record the `queryset` kwarg every consumer-`FilterSet` subclass
        # receives during this call. The active `shelves` branch's
        # visibility scoping now constructs the child `ShelfFilter` first
        # (its `apply_sync` runs during `_derive_related_visibility_*`),
        # so the calls list interleaves child + parent constructions; the
        # test selects the parent (Branch-model) call by queryset model
        # rather than assuming a position.
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

    # Select the parent (Branch-model) construction; child ShelfFilter
    # constructions from the visibility-scoping pass also land in `calls`.
    parent_querysets = [
        qs for qs in captured["calls"] if qs is not None and qs.model is library_models.Branch
    ]
    assert parent_querysets, "BranchFilter was never constructed with a queryset kwarg"
    parent_queryset = parent_querysets[0]
    # The constrained queryset reached `BranchFilter.__init__` BEFORE the
    # filterset was constructed; the SQL carries the parent-pk
    # `pk__in=<subquery over <rel>__in>` restriction that
    # `_apply_related_constraints` baked in.
    sql = str(parent_queryset.query).lower()
    assert "library_shelf" in sql
    assert "active" in sql


# ---------------------------------------------------------------------------
# Apply pipeline - filter_queryset tree-form logic (Slice 4a)
#
# The scalar ``and``/``or`` union/intersection contracts and the nested
# malformed-subbranch validation contract moved to the live library API suite
# (``examples/fakeshop/test_query/test_library_api.py``) per feedback3.md: those
# behaviors are reachable through the real ``BranchFilter``/``PatronFilter`` over
# ``/graphql/``, where the replacements also prove GraphQL input coercion, root
# visibility, and the HTTP error/data envelope.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Round-5 coverage: helper / config / async / depth-cap branches
# ---------------------------------------------------------------------------


def test_get_filters_skips_none_target_related_filter():
    """A ``RelatedFilter(None, ...)`` placeholder expands to nothing.

    ``_expand_related_filter`` returns an empty mapping when the target
    filterset is unresolved (``None``), so no ``<rel>__<lookup>`` keys
    leak into ``get_filters()``.
    """

    class PlaceholderFilter(FilterSet):
        rel = RelatedFilter(None, field_name="branch")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    filters = PlaceholderFilter.get_filters()
    assert not any(name.startswith("rel__") for name in filters)


def test_normalize_input_returns_empty_for_non_dataclass_non_dict():
    """A value that is neither a dict nor a dataclass normalizes to ``{}``."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._normalize_input(object()) == {}


def test_operator_bag_items_walks_lookup_attr_dict():
    """``_operator_bag_items`` walks a dict whose keys are all lookup attrs.

    The old dict rejection routed a dict-shaped bag down the scalar
    branch, where the range-patch ``data.update(...)`` splatted its keys
    into the form data as unknown fields the form silently ignores - an
    explicit filter input applying NO filtering for direct ``apply_*``
    callers. A dict whose keys are all recognized lookup attrs is now
    walked like a dataclass bag.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact", "icontains"]}

    assert CategoryFilter._operator_bag_items({"exact": "x"}) == [("exact", "x")]
    assert CategoryFilter._operator_bag_items({"i_contains": "y"}) == [("i_contains", "y")]


def test_operator_bag_items_returns_none_for_non_lookup_key_dict():
    """A multi-key filter VALUE (e.g. a range ``{start, end}``) is not a bag.

    ``start`` / ``end`` are not lookup attrs, so the dict must fall
    through to the scalar branch where ``normalize_input_value`` produces
    the positional ``{<field>_0, <field>_1}`` range patch. Treating it as
    a bag would emit bogus ``<field>__start`` / ``<field>__end`` keys.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._operator_bag_items({"start": 1, "end": 5}) is None
    # A mixed dict (some lookup attrs, some not) is also not a bag - all
    # keys must be lookup attrs.
    assert CategoryFilter._operator_bag_items({"exact": "x", "start": 1}) is None


def test_operator_bag_items_still_returns_none_for_scalars():
    """Scalar and sequence values are not operator bags."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._operator_bag_items("x") is None
    assert CategoryFilter._operator_bag_items(["x"]) is None


def test_extract_branch_value_returns_none_for_none_input():
    """``_extract_branch_value(None, ...)`` short-circuits to ``None``."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._extract_branch_value(None, "shelves") is None


def test_request_from_info_raises_when_context_missing():
    """``_request_from_info`` raises when ``info.context`` is ``None``."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    class _Info:
        context = None

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter._request_from_info(_Info())
    assert "info.context" in str(excinfo.value)


def test_run_permission_checks_short_circuits_on_none_and_unset():
    """A ``None`` / ``UNSET`` input is a no-op (no gate fires, no crash)."""
    import strawberry

    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            fired.append("name")

    CategoryFilter._run_permission_checks(None, request=HttpRequest())
    CategoryFilter._run_permission_checks(strawberry.UNSET, request=HttpRequest())
    assert fired == []


@pytest.mark.django_db
def test_check_permissions_walks_explicit_requested_fields():
    """The explicit-``requested_fields`` path fires each named gate directly."""
    fired: list[str] = []

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            fired.append("name")

    instance = CategoryFilter(data={}, queryset=Category.objects.all())
    instance.check_permissions(HttpRequest(), requested_fields={"name", "unknown_field"})
    # Only the declared gate fires; the unknown field has no ``check_*`` method.
    assert fired == ["name"]


def test_evaluate_logic_tree_caps_recursion_depth():
    """``_evaluate_logic_tree`` raises past ``_MAX_LOGIC_DEPTH``.

    The round-4 depth guard is independent of the ``_run_permission_checks``
    cap; this pins the ``_evaluate_logic_tree`` / ``_q_for_branch`` arm.
    """

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter._evaluate_logic_tree(
            Category.objects.all(),
            {"and": [{"name": "x"}]},
            _depth=CategoryFilter._MAX_LOGIC_DEPTH + 1,
        )
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)


def test_collect_nested_visibility_querysets_async_caps_recursion_depth():
    """``_collect_nested_visibility_querysets_async`` raises past ``_MAX_LOGIC_DEPTH``.

    Third site of the shared ``_raise_logic_depth_exceeded`` helper -- the async
    pre-walker enforces the same depth cap as ``_run_permission_checks`` and
    ``_evaluate_logic_tree``, surfacing the identical typed error rather than
    silently bottoming out into a Python ``RecursionError``.
    """
    import asyncio

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    with pytest.raises(ConfigurationError) as excinfo:
        asyncio.run(
            CategoryFilter._collect_nested_visibility_querysets_async(
                {"and_": [{"name": "x"}]},
                _make_info(),
                _depth=CategoryFilter._MAX_LOGIC_DEPTH + 1,
            ),
        )
    assert "_MAX_LOGIC_DEPTH" in str(excinfo.value)
    # Pin the qualname-prefixed shape that the shared helper preserves.
    assert "CategoryFilter" in str(excinfo.value)


def test_target_type_for_related_filter_returns_none_without_child_model():
    """A ``RelatedFilter`` whose filterset has no model resolves to ``None``."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    assert CategoryFilter._target_type_for_related_filter(RelatedFilter(None)) is None


def test_is_own_pk_under_relay_owner_false_for_relation_field():
    """An ``is_relation`` field never takes the own-PK Relay branch."""

    class BookFilter(FilterSet):
        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    # Bind an owner directly on the throwaway local class so the early
    # ``owner is None`` guard is passed; ``registry.clear()`` (autouse
    # teardown) strips the binding afterward.
    BookFilter._owner_definition = object()
    relation_field = library_models.Book._meta.get_field("genres")
    assert BookFilter._is_own_pk_under_relay_owner(relation_field) is False


def test_is_own_pk_under_relay_owner_false_when_model_missing():
    """A non-relation field with a model-less filterset returns ``False``."""
    from types import SimpleNamespace

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._owner_definition = object()
    # The local class is discarded after the test, so nulling its own
    # ``_meta.model`` does not leak into other tests.
    CategoryFilter._meta.model = None
    non_relation = SimpleNamespace(is_relation=False)
    assert CategoryFilter._is_own_pk_under_relay_owner(non_relation) is False


def test_filter_for_lookup_rejects_unsupported_lookup_on_relay_owner_pk():
    """Spec-021 H1: an explicit unsupported lookup on a Relay owner's PK raises.

    The ``get_fields`` ``"__all__"`` narrowing only covers the generated
    surface; an explicit ``Meta.fields`` list naming ``range`` / ``gt`` / a
    pattern lookup still reaches ``filter_for_lookup``. A Relay node's wire id
    has no ordering / pattern semantics, so those lookups are rejected with a
    ``ConfigurationError`` (naming the lookup) instead of silently becoming a
    GlobalID-shaped ``String``. Only ``exact`` / ``in`` / ``isnull`` are allowed.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(CategoryType, CategoryType.__django_strawberry_definition__)

    class _Owner:
        origin = CategoryType

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._owner_definition = _Owner()
    pk_field = Category._meta.pk

    with pytest.raises(ConfigurationError) as excinfo:
        CategoryFilter.filter_for_lookup(pk_field, "range")
    assert "range" in str(excinfo.value)
    # The same rejection holds via the per-field entry point (which routes
    # through ``filter_for_lookup`` in ``super().filter_for_field``).
    with pytest.raises(ConfigurationError):
        CategoryFilter.filter_for_field(pk_field, "id", "range")

    # The three supported lookups resolve without raising.
    exact_class, _ = CategoryFilter.filter_for_lookup(pk_field, "exact")
    assert exact_class is GlobalIDFilter
    in_class, _ = CategoryFilter.filter_for_lookup(pk_field, "in")
    assert in_class is GlobalIDMultipleChoiceFilter
    isnull_class, _ = CategoryFilter.filter_for_lookup(pk_field, "isnull")
    assert isnull_class is not GlobalIDFilter


def test_resolve_relation_target_type_uses_owner_related_target_for():
    """When the owner resolves the relation, its target type is returned."""
    from types import SimpleNamespace

    target_type = type("ResolvedTargetType", (), {})

    class _Owner:
        def related_target_for(self, field_name):
            # The pair's first member is a ``DjangoTypeDefinition``, whose
            # registered ``DjangoType`` class is ``.origin`` -- NOT ``.type``
            # / ``.type_cls`` (the H3 bug read those nonexistent attrs and
            # dropped every owner-aware resolution to the registry fallback).
            return (SimpleNamespace(origin=target_type), object())

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    CategoryFilter._owner_definition = _Owner()
    relation_field = SimpleNamespace(is_relation=True, related_model=Category)
    resolved = CategoryFilter._resolve_relation_target_type(relation_field, "category")
    assert resolved is target_type


def test_resolve_relation_target_type_returns_none_without_related_model():
    """A relation field with no ``related_model`` and no owner resolves to ``None``."""
    from types import SimpleNamespace

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    field = SimpleNamespace(is_relation=True, related_model=None)
    assert CategoryFilter._resolve_relation_target_type(field, None) is None


@pytest.mark.django_db
def test_apply_related_constraints_skips_branch_without_qs_or_explicit():
    """An active branch with neither child qs nor explicit qs is skipped."""

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        # No explicit ``queryset=`` on the RelatedFilter.
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    parent_qs = library_models.Branch.objects.all()
    # Active ``shelves`` branch, but the child-qs map is empty AND the
    # RelatedFilter has no explicit queryset -> the branch is skipped.
    constrained = BranchFilter._apply_related_constraints(
        {"shelves": {"code": "x"}},
        parent_qs,
        {},
    )
    assert "shelves__in" not in str(constrained.query)


@pytest.mark.django_db
def test_apply_async_filters_against_scalar_input():
    """``apply_async`` builds the filtered queryset (no related branches)."""
    import asyncio

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    qs = asyncio.run(
        CategoryFilter.apply_async({"name": "alpha"}, Category.objects.all(), _make_info()),
    )
    sql = str(qs.query).lower()
    assert "alpha" in sql


@pytest.mark.django_db
def test_derive_related_visibility_querysets_async_scopes_active_branch():
    """The async visibility derive runs the target ``get_queryset`` per active branch."""
    import asyncio

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    result = asyncio.run(
        BranchFilter._derive_related_visibility_querysets_async(
            {"shelves": {"code": "A"}},
            _make_info(),
        ),
    )
    assert "shelves" in result
    assert result["shelves"].model is library_models.Shelf


def test_normalize_input_operator_bag_passes_unmatched_lookup_through():
    """An operator-bag lookup with no backing filter is written verbatim."""
    import dataclasses

    @dataclasses.dataclass
    class _NameBag:
        gt: Any = None

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    # ``gt`` is not a declared lookup for ``name`` -> no filter instance ->
    # the value lands under the raw ``name__gt`` form key.
    data = CategoryFilter._normalize_input({"name": _NameBag(gt=5)})
    assert data == {"name__gt": 5}


@pytest.mark.django_db
def test_normalize_input_operator_bag_dict_value_merges_into_form_data():
    """A dict-valued operator-bag lookup is merged into the form data via ``update``.

    Exercises the operator-bag ``isinstance(normalized, dict)`` ->
    ``data.update(normalized)`` branch. The framework ``RangeFilter``
    declared at a ``<field>__range`` name groups under the ``<field>``
    operator bag; its ``{start, end}`` value normalizes to the positional
    ``<key>_0`` / ``<key>_1`` patch that the loop merges in. (django-filter's
    own ``range`` lookup instead produces a CSV ``BaseRangeFilter`` whose
    value is a *list*, not a dict -- see
    ``test_convert_filter_to_input_annotation_csv_in_filter_is_list`` -- so
    the framework ``RangeFilter`` is the primitive that drives this
    dict-merge path.)
    """
    import dataclasses

    from django_strawberry_framework.filters import RangeFilter

    @dataclasses.dataclass
    class _FinesBag:
        range: Any = None

    class PatronFilter(FilterSet):
        lifetime_fines_cents__range = RangeFilter(
            field_name="lifetime_fines_cents",
            lookup_expr="range",
        )

        class Meta:
            model = library_models.Patron
            fields = []

    data = PatronFilter._normalize_input(
        {"lifetime_fines_cents": _FinesBag(range={"start": 1, "end": 5})},
    )
    # The dict-valued normalization result is merged key-by-key.
    assert data == {"lifetime_fines_cents__range_0": 1, "lifetime_fines_cents__range_1": 5}


@pytest.mark.django_db
def test_normalize_input_operator_bag_exact_resolves_explicit_suffixed_key():
    """An ``exact`` operator-bag lookup resolves a filter declared under ``<field>__exact``.

    ``exact`` is the only lookup whose form key (the bare ``base_path``) can
    differ from its ``<base_path>__exact`` suffixed key, so it is the one case
    where ``_normalize_input`` probes a second key. ``django-filter`` strips the
    ``__exact`` suffix from *generated* exact filters (they register under the
    bare field name), but a filter declared explicitly under the
    ``<field>__exact`` attribute name is merged into ``get_filters()`` under that
    literal key (``BaseFilterSet.get_filters``'s trailing
    ``filters.update(cls.declared_filters)``). With no bare-``name`` autogen
    filter (``Meta.fields = []``), ``all_filters`` carries only ``name__exact``,
    so the bare-key probe misses and the suffixed-key fallback must resolve the
    declared ``CharFilter`` -- the genuine two-key-differ path.
    """
    import dataclasses

    import django_filters

    @dataclasses.dataclass
    class _NameBag:
        exact: Any = None

    class WeirdCategoryFilter(FilterSet):
        name__exact = django_filters.CharFilter(field_name="name", lookup_expr="exact")

        class Meta:
            model = Category
            fields = []

    assert list(WeirdCategoryFilter.get_filters()) == ["name__exact"]
    # ``base_path`` resolves to the bare ``name`` (from the field python attr),
    # ``form_key`` is the bare ``name`` (exact), ``suffixed_key`` is
    # ``name__exact``; the bare probe misses, the suffixed probe resolves the
    # declared filter and normalizes to the bare ``name`` form-data key.
    data = WeirdCategoryFilter._normalize_input({"name": _NameBag(exact="foo")})
    assert data == {"name": "foo"}


@pytest.mark.django_db
def test_normalize_input_top_level_range_filter_merges_positional_keys():
    """A top-level ``RangeFilter`` attribute expands to positional keys."""
    from django_strawberry_framework.filters import RangeFilter

    class FinesRangeFilter(FilterSet):
        fines = RangeFilter(field_name="lifetime_fines_cents")

        class Meta:
            model = library_models.Patron
            fields = {"id": ["exact"]}

    data = FinesRangeFilter._normalize_input({"fines": {"start": 1, "end": 5}})
    assert data == {"fines_0": 1, "fines_1": 5}


@pytest.mark.django_db
def test_check_permissions_falls_back_to_active_input_when_no_requested_fields():
    """``check_permissions`` with no explicit set routes through the active-input path."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    instance = CategoryFilter(data={}, queryset=Category.objects.all())
    # No ``requested_fields`` -> the active-input ``_run_permission_checks``
    # branch runs (and is a no-op for a gate-less filterset).
    instance.check_permissions(HttpRequest())


def test_derive_related_visibility_querysets_async_raises_for_unregistered_target():
    """The async derive raises for an active branch whose target type is unregistered.

    The old contract skipped the branch (``result == {}``), which dropped
    the constraint entirely: a filter the consumer supplied input for
    silently returned unfiltered parent rows. Both derive methods route
    through ``_iter_visibility_steps``, which now raises
    ``ConfigurationError`` for the active-but-unresolvable branch.
    """
    import asyncio

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # No ShelfType registered -> ``_target_type_for_related_filter`` is
    # ``None`` -> the active branch raises instead of silently dropping.
    with pytest.raises(ConfigurationError) as excinfo:
        asyncio.run(
            BranchFilter._derive_related_visibility_querysets_async(
                {"shelves": {"code": "A"}},
                _make_info(),
            ),
        )
    assert "no DjangoType is registered" in str(excinfo.value)


@pytest.mark.django_db
def test_iter_visibility_steps_yields_pre_await_tuple_for_active_branches():
    """``_iter_visibility_steps`` yields the shared pre-await state both derive methods consume.

    Pins the DRY-0_0_7 consolidation: both
    ``_derive_related_visibility_querysets_sync`` and
    ``_derive_related_visibility_querysets_async`` route through the
    single ``_iter_visibility_steps`` classmethod, so the helper's
    five-tuple shape (``field_name, target_type, child_filterset,
    child_input, child_base``) is the load-bearing contract. Branches
    missing ``target_type`` or ``child_filterset`` raise (see the
    sibling fail-loud test) so the derive methods carry only the two
    awaits / calls per step.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    steps = list(
        BranchFilter._iter_visibility_steps({"shelves": {"code": "A"}}),
    )
    assert len(steps) == 1
    field_name, target_type, child_filterset, child_input, child_base = steps[0]
    assert field_name == "shelves"
    assert target_type is ShelfType
    assert child_filterset is ShelfFilter
    assert child_input == {"code": "A"}
    assert child_base.model is library_models.Shelf


@pytest.mark.django_db
def test_iter_visibility_steps_raises_for_branch_without_resolved_target():
    """``_iter_visibility_steps`` fails loud for an active-but-unresolvable branch.

    The guard lives in the helper so each derive method stays a tight
    loop carrying only the two awaits / calls per step. An active branch
    (the consumer supplied input for it) whose ``target_type`` cannot be
    resolved raises ``ConfigurationError`` - the old skip contract
    dropped the constraint and silently returned unfiltered parent rows
    (mirrors the sibling async test, but pins the helper directly).
    """

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # No ShelfType registered -> ``_target_type_for_related_filter`` is
    # ``None`` -> the helper raises before yielding.
    with pytest.raises(ConfigurationError) as excinfo:
        list(BranchFilter._iter_visibility_steps({"shelves": {"code": "A"}}))
    msg = str(excinfo.value)
    assert "'shelves'" in msg
    assert "no DjangoType is registered" in msg


@pytest.mark.django_db
def test_apply_async_nested_or_branch_with_async_get_queryset_does_not_raise_sync_misuse():
    """``apply_async`` pre-derives nested visibility so an async-only ``get_queryset`` hook
    does not raise ``SyncMisuseError`` mid-``.qs`` from a nested ``or_`` branch.

    Before the Medium-#2 fix, ``_q_for_branch`` called
    ``_derive_related_visibility_querysets_sync`` unconditionally, which
    invokes ``apply_type_visibility_sync`` on the target type. A target whose
    ``get_queryset`` is ``async def`` returns a coroutine that
    ``apply_type_visibility_sync`` flags as ``SyncMisuseError``. The pre-walk
    in ``apply_async`` (``_collect_nested_visibility_querysets_async``)
    now awaits every nested branch's visibility BEFORE the ``.qs`` read,
    and ``_q_for_branch`` consults the stash keyed by ``id(child_input)``
    instead of re-deriving sync.
    """
    import asyncio

    from asgiref.sync import sync_to_async

    alpha = library_models.Branch.objects.create(name="alpha")
    library_models.Shelf.objects.create(branch=alpha, code="match")
    beta = library_models.Branch.objects.create(name="beta")
    library_models.Shelf.objects.create(branch=beta, code="other")

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

        @classmethod
        async def get_queryset(cls, queryset, info, **kwargs):
            # Async-only hook: pre-merge ``_q_for_branch`` would raise
            # ``SyncMisuseError`` when its sync derive walked into this.
            return await sync_to_async(lambda: queryset)()

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    qs = asyncio.run(
        BranchFilter.apply_async(
            {"or_": [{"shelves": {"code": "match"}}]},
            library_models.Branch.objects.all(),
            _make_info(),
        ),
    )
    # The async-only ``get_queryset`` ran, the nested branch constrained
    # the parent, and only ``alpha`` (which owns the matching shelf) leaks
    # through. Before the fix, ``.qs`` would raise ``SyncMisuseError``
    # before this assertion could run.
    assert list(qs.values_list("name", flat=True)) == ["alpha"]


@pytest.mark.django_db
def test_apply_async_runs_permission_checks_off_event_loop_thread():
    """``apply_async`` routes ``_run_permission_checks`` through ``sync_to_async``
    so a blocking ``check_*_permission`` hook does not block the event loop.

    Asserts the permission method observed a thread ident DIFFERENT from
    the event-loop thread ident -- which is what
    ``sync_to_async(thread_sensitive=True)`` guarantees. Before the
    Medium-#1 fix, ``_run_permission_checks`` ran inline on the event-loop
    thread, so the two ident reads would have matched.
    """
    import asyncio
    import threading

    captured: dict[str, int] = {}

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

        def check_name_permission(self, request):
            captured["permission_thread"] = threading.get_ident()

    async def _run() -> int:
        captured["event_loop_thread"] = threading.get_ident()
        await CategoryFilter.apply_async(
            {"name": "alpha"},
            Category.objects.all(),
            _make_info(),
        )
        return captured["event_loop_thread"]

    event_loop_thread = asyncio.run(_run())
    assert captured["permission_thread"] != event_loop_thread


@pytest.mark.django_db
def test_apply_async_collect_nested_visibility_querysets_pre_derives_or_branch():
    """``_collect_nested_visibility_querysets_async`` keys the awaited map on
    ``id(child_input)`` for every nested ``or`` arm.

    Unit-level pin on the new helper -- given an ``or_`` input shape with
    one inner branch carrying an active ``RelatedFilter``, the helper
    returns a map whose only key is ``id`` of that nested child dict, and
    whose value carries the ``shelves`` queryset derived via the async
    path.
    """
    import asyncio

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    inner = {"shelves": {"code": "A"}}
    result = asyncio.run(
        BranchFilter._collect_nested_visibility_querysets_async(
            {"or_": [inner]},
            _make_info(),
        ),
    )
    assert id(inner) in result
    assert "shelves" in result[id(inner)]
    assert result[id(inner)]["shelves"].model is library_models.Shelf
    # Silence the unused ShelfType registration (registry isolation handles it).
    assert ShelfType is not None


# ---------------------------------------------------------------------------
# Permission gate dispatch keys on the field, not the lookup (H2)
# ---------------------------------------------------------------------------


def test_active_permission_field_paths_covers_input_shapes():
    """``_active_permission_field_paths`` resolves source paths, skips the rest (H2)."""
    import dataclasses

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    # None / UNSET / non-(dict-or-dataclass) -> empty.
    assert BranchFilter._active_permission_field_paths(None) == []
    assert BranchFilter._active_permission_field_paths(strawberry.UNSET) == []
    assert BranchFilter._active_permission_field_paths(42) == []

    @dataclasses.dataclass
    class _Input:
        name: Any = None
        shelves: Any = None
        and_: Any = None

    # Active scalar resolves to its source path; the related branch and the
    # logical-operator key are excluded (gated elsewhere); ``None`` skipped.
    paths = BranchFilter._active_permission_field_paths(
        _Input(name="x", shelves={"code": "y"}, and_=[{"name": "z"}]),
    )
    assert paths == ["name"]
    # A raw dict resolves via the form-key fallback.
    assert BranchFilter._active_permission_field_paths({"name": "x"}) == ["name"]


# ---------------------------------------------------------------------------
# Per-field ``Meta.fields = {"<field>": "__all__"}`` lookup expansion
# ---------------------------------------------------------------------------


def test_lookups_for_field_returns_concrete_lookups_and_excludes_transforms():
    """`_lookups_for_field` returns concrete lookups and drops Transforms."""
    name_field = Category._meta.get_field("name")  # TextField
    date_field = Category._meta.get_field("created_date")  # DateTimeField

    name_lookups = _lookups_for_field(name_field)
    assert {
        "exact",
        "icontains",
        "gt",
        "lt",
        "in",
        "range",
        "isnull",
        "startswith",
    } <= set(name_lookups)

    date_lookups = _lookups_for_field(date_field)
    assert {"exact", "gt", "lt"} <= set(date_lookups)
    # Temporal transforms (year / month / date / time / ...) are excluded:
    # the per-field operator-bag input shape has no nested-transform form.
    assert {
        "year",
        "month",
        "day",
        "date",
        "time",
        "week",
    }.isdisjoint(date_lookups)

    # A missing field resolves to an empty list (defensive).
    assert _lookups_for_field(None) == []


# ---------------------------------------------------------------------
# DRY consolidation pins (dry-0_0_7): ``FilterSet._iter_input_items``
# ---------------------------------------------------------------------
#
# Three sites (``_normalize_input``, ``_operator_bag_items``,
# ``_active_permission_field_paths``) route through a single shared
# staticmethod that walks dicts AND Strawberry-input dataclasses into
# ``(name, value)`` pairs. The helper returns ``None`` for non-walkable
# shapes and ``[]`` for walkable-but-empty inputs. Site 2
# (``_operator_bag_items``) keeps its scalar/collection/dict pre-rejection
# above the helper call so operator bags remain dataclass-only at the
# call boundary while sites 1 / 3 accept both dict and dataclass shapes.


def test_iter_input_items_returns_pairs_for_plain_dict():
    """Dict input walks to ``list(input.items())`` verbatim."""

    assert FilterSet._iter_input_items({"name": "x", "id": 1}) == [("name", "x"), ("id", 1)]


def test_iter_input_items_returns_empty_list_for_empty_dict():
    """Walkable-but-empty dict returns ``[]`` (sentinel-distinct from None)."""

    assert FilterSet._iter_input_items({}) == []


def test_iter_input_items_walks_strawberry_input_dataclass_via_attribute_sniff():
    """``__dataclass_fields__`` sniff unpacks Strawberry-input shapes."""

    @strawberry.input
    class FooInput:
        name: str = "x"
        count: int = 3

    items = FilterSet._iter_input_items(FooInput(name="y", count=7))
    assert items == [("name", "y"), ("count", 7)]


def test_iter_input_items_returns_none_for_non_walkable_shapes():
    """Non-dict / non-dataclass shapes return ``None`` (not ``[]``)."""

    assert FilterSet._iter_input_items(object()) is None
    assert FilterSet._iter_input_items("scalar") is None
    assert FilterSet._iter_input_items(42) is None
    assert FilterSet._iter_input_items([1, 2, 3]) is None
    assert FilterSet._iter_input_items(None) is None


# ---------------------------------------------------------------------------
# Async-path coverage. These four branches live in the apply_async pipeline
# (the sync_to_async qs read, the nested-visibility pre-walk, and the
# _q_for_branch stash-miss fallback). The fakeshop live HTTP suites drive
# Django's SYNC test Client -> sync views -> apply_sync, so per
# examples/fakeshop/test_query/README.md these lines are genuinely
# unreachable from a live /graphql/ request and are earned here as unit
# tests (the README's documented fallback for live-unreachable code).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_read_qs_returns_filterset_qs():
    """``_read_qs`` returns the instance's ``.qs`` (the ``sync_to_async`` callable wrapper).

    ``apply_async`` routes the synchronous ``.qs`` read through
    ``sync_to_async(_read_qs)`` to keep the ORM work off the event-loop
    thread; the wrapper exists only because ``sync_to_async`` wants a
    callable rather than an attribute read. The threaded call site is not
    reachable from the sync live HTTP Client, so it is covered directly here.
    """

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    fs = BranchFilter(data={}, queryset=library_models.Branch.objects.all())
    # ``.qs`` is a cached_property, so the helper's read returns the same
    # object the direct attribute read does.
    assert _read_qs(fs) is fs.qs


def test_collect_nested_visibility_querysets_async_returns_empty_for_none_input():
    """``_collect_nested_visibility_querysets_async(None, ...)`` short-circuits to ``{}``.

    The ``input_value is None or input_value is UNSET`` guard returns the
    empty map before any branch walk -- the apply_async pre-pass over a
    branch with no nested logical input does no work.
    """
    import asyncio

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    result = asyncio.run(
        BranchFilter._collect_nested_visibility_querysets_async(None, _make_info()),
    )
    assert result == {}


def test_collect_nested_visibility_querysets_async_skips_none_child_branch():
    """A ``None`` child inside a logical branch is skipped without a derive.

    ``{"or": [None]}`` yields a single ``None`` child; the child loop's
    ``if child_input is None or child_input is UNSET: continue`` skips it, so
    no visibility derive runs and the result stays empty.
    """
    import asyncio

    class BranchFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    result = asyncio.run(
        BranchFilter._collect_nested_visibility_querysets_async({"or": [None]}, _make_info()),
    )
    assert result == {}


@pytest.mark.django_db
def test_q_for_branch_falls_back_to_sync_derive_on_stash_miss():
    """``_q_for_branch`` with a present-but-missing stash uses the sync-derive fallback.

    Under ``apply_async`` the nested visibility map is pre-derived and threaded
    through ``_nested_qs_by_branch_id`` keyed by ``id(child_input)``. A consumer
    who short-circuits past the async pre-pass (modeled here by an empty stash
    dict, so ``.get(id(child_input))`` misses) still gets a correct result via
    the defensive sync-derive fallback rather than a ``None`` map.
    """
    from django.db.models import Q

    class ShelfType(DjangoType):
        class Meta:
            model = library_models.Shelf

    class ShelfFilter(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilter(FilterSet):
        shelves = RelatedFilter(ShelfFilter, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    child_input = {"shelves": {"code": "A"}}
    q = BranchFilter._q_for_branch(
        library_models.Branch.objects.all(),
        child_input,
        info=_make_info(),
        _nested_qs_by_branch_id={},  # present but empty -> stash miss -> sync fallback
    )
    assert isinstance(q, Q)
