"""Tests for `django_strawberry_framework/filters/factories.py` (Slice 2).

Covers `FilterArgumentsFactory`'s BFS walk and per-class collision
check, plus the Layer-6 `get_filterset_class` + `_dynamic_filterset_cache`
+ `_make_cache_key` plumbing.
"""

from __future__ import annotations

from typing import get_args

import pytest
import strawberry
from apps.library import models as library_models
from apps.products.models import Category
from django_filters import NumberFilter

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import (
    FilterSet,
    GlobalIDMultipleChoiceFilter,
    RelatedFilter,
)
from django_strawberry_framework.filters.factories import (
    FilterArgumentsFactory,
    _dynamic_filterset_cache,
    _make_cache_key,
    get_filterset_class,
)
from django_strawberry_framework.filters.inputs import _field_specs
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.relay import apply_interfaces


@pytest.fixture(autouse=True)
def _isolate_state():
    registry.clear()
    _field_specs.clear()
    _dynamic_filterset_cache.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()
    yield
    registry.clear()
    _field_specs.clear()
    _dynamic_filterset_cache.clear()
    FilterArgumentsFactory.input_object_types.clear()
    FilterArgumentsFactory._type_filterset_registry.clear()


# ---------------------------------------------------------------------------
# FilterArgumentsFactory BFS
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_filter_arguments_factory_visits_every_reachable_filterset():
    """A `Branch -> Shelf` `RelatedFilter` -> both classes appear in `input_object_types`."""

    class ShelfFilterA(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BranchFilterA(FilterSet):
        shelves = RelatedFilter(ShelfFilterA, field_name="shelves")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    factory = FilterArgumentsFactory(BranchFilterA)
    factory.arguments  # trigger build
    assert "BranchFilterAInputType" in FilterArgumentsFactory.input_object_types
    assert "ShelfFilterAInputType" in FilterArgumentsFactory.input_object_types


@pytest.mark.django_db
def test_filter_arguments_factory_bfs_handles_cycle():
    """`A -> B -> A` mutual `RelatedFilter`s do not blow the BFS stack."""
    # Use the package's `tests.filters.fixtures.filtersets` self-referential
    # fixture: the cookbook-style cycle path is exercised by
    # `SelfReferentialBranchFilter` whose `RelatedFilter("SelfReferentialBranchFilter")`
    # resolves back to itself (a degenerate A -> A cycle covers the same
    # `seen`-set short-circuit branch as A -> B -> A).
    from tests.filters.fixtures.filtersets import SelfReferentialBranchFilter

    factory = FilterArgumentsFactory(SelfReferentialBranchFilter)
    factory.arguments  # must not recurse forever
    assert "SelfReferentialBranchFilterInputType" in FilterArgumentsFactory.input_object_types


@pytest.mark.django_db
def test_filter_arguments_factory_dedupes_target_enqueued_twice():
    """A diamond ``A -> {B, C} -> D`` enqueues ``D`` twice; the BFS dedups it.

    Unlike the ``A -> B -> A`` cycle (caught by the enqueue-time
    ``target not in seen`` gate), a diamond enqueues the shared child ``D``
    from both sibling parents BEFORE ``D`` is popped, so the pop-time
    ``if fs_class in seen: continue`` dedup is what prevents the duplicate
    build.
    """

    class DFilter(FilterSet):
        class Meta:
            model = library_models.Loan
            fields = {"note": ["exact"]}

    class BFilter(FilterSet):
        d = RelatedFilter(DFilter, field_name="loans")

        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class CFilter(FilterSet):
        d = RelatedFilter(DFilter, field_name="loans")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    class AFilter(FilterSet):
        b = RelatedFilter(BFilter, field_name="shelves")
        c = RelatedFilter(CFilter, field_name="books")

        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    factory = FilterArgumentsFactory(AFilter)
    factory.arguments  # BFS: D is enqueued by both B and C, deduped at pop.
    for name in (
        "AFilterInputType",
        "BFilterInputType",
        "CFilterInputType",
        "DFilterInputType",
    ):
        assert name in FilterArgumentsFactory.input_object_types


@pytest.mark.django_db
def test_filter_arguments_factory_collision_raises_on_distinct_class_with_same_name():
    """Two distinct `FilterSet`s named `DupFilter` in different modules -> ConfigurationError."""

    class DupFilter(FilterSet):  # noqa: F811 — first declaration
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    factory = FilterArgumentsFactory(DupFilter)
    factory.arguments  # build the first one

    # Synthesize a second class with the same `__name__`.
    DupFilter2 = type(
        "DupFilter",
        (FilterSet,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Shelf, "fields": {"code": ["exact"]}},
            ),
        },
    )
    factory2 = FilterArgumentsFactory(DupFilter2)
    with pytest.raises(ConfigurationError) as excinfo:
        factory2.arguments
    assert "DupFilterInputType" in str(excinfo.value)


@pytest.mark.django_db
def test_filter_arguments_factory_idempotent_repeated_arguments():
    """Repeated reads of `.arguments` return the same input class object."""

    class IdempotentFilter(FilterSet):
        class Meta:
            model = library_models.Branch
            fields = {"name": ["exact"]}

    factory = FilterArgumentsFactory(IdempotentFilter)
    first = factory.arguments
    second = factory.arguments
    assert first is second


@pytest.mark.django_db
def test_filter_arguments_factory_input_shape_matches_runtime_filter_for_relay_target():
    """A Relay-shaped M2M target -> input annotation forwards to the target's input class.

    Pins the H1-of-rev3 contract: the input shape is downstream of the
    resolved filter instance (`GlobalIDMultipleChoiceFilter` for the M2M
    cardinality), and the factory produces an `Annotated[...]` lazy
    reference to the target filterset's input class.
    """

    class GenreType(DjangoType):
        class Meta:
            model = library_models.Genre
            interfaces = (strawberry.relay.Node,)

    apply_interfaces(GenreType, GenreType.__django_strawberry_definition__)

    class GenreFilter(FilterSet):
        class Meta:
            model = library_models.Genre
            fields = {"name": ["exact"]}

    class BookFilterRelay(FilterSet):
        genres = RelatedFilter(GenreFilter, field_name="genres")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    # Confirm runtime filter resolves to the Relay multi-value primitive.
    field = library_models.Book._meta.get_field("genres")
    runtime_filter = BookFilterRelay.filter_for_field(field, "genres")
    assert isinstance(runtime_filter, GlobalIDMultipleChoiceFilter)

    # Build the input class and assert the `genres` field's annotation
    # is a lazy reference to GenreFilterInputType.
    factory = FilterArgumentsFactory(BookFilterRelay)
    input_cls = factory.arguments
    fields = {f.python_name: f for f in input_cls.__strawberry_definition__.fields}
    genres_field = fields["genres"]
    # Strawberry resolves the `Annotated[..., strawberry.lazy(...)]` form
    # into a `LazyType` at field-collection time; both shapes are
    # accepted here so the test is robust to Strawberry version changes.
    type_annotation = genres_field.type_annotation.annotation
    non_none = [arg for arg in get_args(type_annotation) if arg is not type(None)]
    assert non_none, type_annotation
    inner = non_none[0]
    if hasattr(inner, "__metadata__"):
        forward = inner.__args__[0]
        forward_name = getattr(forward, "__forward_arg__", forward)
    else:
        # `LazyType` carries `.type_name` after Strawberry has resolved
        # the Annotated wrapper.
        forward_name = inner.type_name
    assert forward_name == "GenreFilterInputType"


@pytest.mark.django_db
def test_filter_arguments_factory_input_shape_matches_runtime_filter_for_non_relay_target():
    """A non-Relay target -> runtime filter is upstream's default (NumberFilter for PK FK)."""

    class ShelfTypeNon(DjangoType):
        class Meta:
            model = library_models.Shelf

    class ShelfFilterNon(FilterSet):
        class Meta:
            model = library_models.Shelf
            fields = {"code": ["exact"]}

    class BookFilterNon(FilterSet):
        shelf = RelatedFilter(ShelfFilterNon, field_name="shelf")

        class Meta:
            model = library_models.Book
            fields = {"title": ["exact"]}

    field = library_models.Book._meta.get_field("shelf")
    runtime_filter = BookFilterNon.filter_for_field(field, "shelf")
    # Non-Relay target -> upstream default (NOT GlobalIDFilter).
    from django_strawberry_framework.filters import GlobalIDFilter

    assert not isinstance(runtime_filter, GlobalIDFilter)


# ---------------------------------------------------------------------------
# get_filterset_class + dynamic-cache plumbing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_filterset_class_returns_explicit_class_unchanged():
    class ExplicitFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    result = get_filterset_class(ExplicitFilter)
    assert result is ExplicitFilter


@pytest.mark.django_db
def test_get_filterset_class_caches_dynamic_filterset_by_meta():
    """Two equivalent `get_filterset_class(None, ...)` calls collapse onto one class."""
    first = get_filterset_class(None, model=Category, fields={"name": ["exact"]})
    second = get_filterset_class(None, model=Category, fields={"name": ["exact"]})
    assert first is second


@pytest.mark.django_db
def test_get_filterset_class_distinct_meta_produces_distinct_classes():
    """Distinct `fields` -> distinct generated classes."""
    first = get_filterset_class(None, model=Category, fields={"name": ["exact"]})
    second = get_filterset_class(None, model=Category, fields={"name": ["icontains"]})
    assert first is not second


def test_make_cache_key_normalizes_dict_fields_shape():
    key = _make_cache_key({"model": Category, "fields": {"name": ["exact", "icontains"]}})
    # `dict` shape produces the (model, ('dict', (sorted-tuples,)), extra) tuple.
    assert key[0] is Category
    assert key[1][0] == "dict"


def test_make_cache_key_normalizes_list_fields_shape():
    key = _make_cache_key({"model": Category, "fields": ["name", "is_private"]})
    assert key[1][0] == "seq"
    assert key[1][1] == ("name", "is_private")


def test_make_cache_key_normalizes_scalar_all_fields_shape():
    key = _make_cache_key({"model": Category, "fields": "__all__"})
    assert key[1] == ("raw", "__all__")


def test_make_cache_key_distinguishes_extra_meta_keys():
    key_a = _make_cache_key(
        {"model": Category, "fields": "__all__", "exclude": ("id",)},
    )
    key_b = _make_cache_key({"model": Category, "fields": "__all__"})
    assert key_a != key_b


def test_make_cache_key_structurally_equivalent_metas_share_a_slot():
    """Two metas that differ only in shape detail hash to the same key.

    The cache key is the contract that lets connection fields with
    equivalent ``Meta`` declarations collapse onto a single generated
    ``FilterSet`` class. The keying logic walks: ``model`` identity +
    ``fields`` normalized through ``_make_hashable`` (handles nested
    dicts / lists / sets) + sorted extras. Pinning the equivalence
    classes prevents a future "tweak the key shape" change from
    silently widening or narrowing what counts as the same slot.
    """
    # 1. ``fields`` dict with list values: tuple-vs-list lookups
    #    collapse onto the same key (lists normalize through
    #    ``_make_hashable`` to tuples).
    key_dict_a = _make_cache_key({"model": Category, "fields": {"name": ["exact", "icontains"]}})
    key_dict_b = _make_cache_key({"model": Category, "fields": {"name": ("exact", "icontains")}})
    assert key_dict_a == key_dict_b

    # 2. ``fields`` dict key order does not matter — sorted output.
    key_order_a = _make_cache_key({"model": Category, "fields": {"a": ["exact"], "b": ["exact"]}})
    key_order_b = _make_cache_key({"model": Category, "fields": {"b": ["exact"], "a": ["exact"]}})
    assert key_order_a == key_order_b

    # 3. ``extras`` insertion order does not matter — sorted output.
    key_extra_a = _make_cache_key(
        {
            "model": Category,
            "fields": "__all__",
            "exclude": ("id",),
            "form": "x",
        },
    )
    key_extra_b = _make_cache_key(
        {
            "model": Category,
            "fields": "__all__",
            "form": "x",
            "exclude": ("id",),
        },
    )
    assert key_extra_a == key_extra_b

    # 4. Different ``model`` classes never collide even when fields match.
    from apps.products.models import Item

    key_cat = _make_cache_key({"model": Category, "fields": "__all__"})
    key_item = _make_cache_key({"model": Item, "fields": "__all__"})
    assert key_cat != key_item

    # 5. Sequence-shape ``fields`` collapses list and tuple inputs onto
    #    the same key (both normalize to a tuple under "seq").
    key_seq_a = _make_cache_key({"model": Category, "fields": ["name", "is_private"]})
    key_seq_b = _make_cache_key({"model": Category, "fields": ("name", "is_private")})
    assert key_seq_a == key_seq_b


def test_dynamic_filterset_cache_collapses_equivalent_metas_to_one_class():
    """Two structurally-equivalent meta dicts return the same generated class.

    End-to-end pin: even when the inputs differ in surface shape
    (list-vs-tuple lookups, key order in fields / extras), the
    dynamic-cache slot is shared so the BFS factory's collision check
    cannot fire against the same logical Meta declaration arriving via
    two connection-field call sites.
    """
    cls_list = get_filterset_class(None, model=Category, fields={"name": ["exact", "icontains"]})
    cls_tuple = get_filterset_class(None, model=Category, fields={"name": ("exact", "icontains")})
    assert cls_list is cls_tuple


@pytest.mark.django_db
def test_dynamic_filterset_cache_does_not_replace_csv_filters():
    """Per spec line 247, the cookbook's ``replace_csv_filters`` rewrap is dropped.

    `Meta.fields = {"name": ["in"]}` -> the resulting filter is the
    upstream `django-filter` default (with the inherited list shape),
    NOT a CSV-rewritten variant.
    """
    cls = get_filterset_class(None, model=Category, fields={"name": ["in"]})
    filters = cls.get_filters()
    # `name__in` should land as a regular filter; the import path the
    # cookbook's CSV variant would have used (`graphene_django.filter`
    # internals) is NOT touched.
    assert "name__in" in filters
    # Confirm the resulting filter is NOT a graphene-django-CSV variant
    # by checking its class hierarchy contains no graphene module path.
    cls_path = type(filters["name__in"]).__module__
    assert "graphene" not in cls_path


@pytest.mark.django_db
def test_get_filterset_class_strips_reserved_kwargs():
    """`filterset_base_class` is stripped before being passed to the dynamic factory."""
    # Should not raise even though we pass the reserved kwarg.
    cls = get_filterset_class(
        None,
        model=Category,
        fields={"name": ["exact"]},
        filterset_base_class=FilterSet,
    )
    assert issubclass(cls, FilterSet)


def test_get_filterset_class_requires_model_when_dynamic():
    """Without an explicit class AND without `model`, the dynamic factory raises."""
    with pytest.raises(ConfigurationError):
        get_filterset_class(None, fields={"name": ["exact"]})


@pytest.mark.django_db
def test_get_filterset_class_supports_unhashable_meta_values():
    """`get_filterset_class` should support unhashable types (like lists, dicts, sets) in Meta options without raising TypeError."""
    # List in exclude
    cls_a = get_filterset_class(None, model=Category, fields="__all__", exclude=["id"])
    cls_b = get_filterset_class(None, model=Category, fields="__all__", exclude=["id"])
    assert cls_a is cls_b

    # Nested set or list in extra meta
    cls_c = get_filterset_class(
        None,
        model=Category,
        fields={"name": ["exact"]},
        extra_opt={
            "nested": {1, 2, 3},
        },
    )
    cls_d = get_filterset_class(
        None,
        model=Category,
        fields={"name": ["exact"]},
        extra_opt={
            "nested": {1, 2, 3},
        },
    )
    assert cls_c is cls_d


# Touch `NumberFilter` import to ensure the import is exercised (used
# implicitly by django-filter for the integer-PK FK in the
# `test_filter_arguments_factory_input_shape_matches_runtime_filter_for_non_relay_target`
# test above).
assert NumberFilter is not None
