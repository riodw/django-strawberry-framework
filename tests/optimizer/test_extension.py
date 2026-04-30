"""Tests for ``DjangoOptimizerExtension`` — O3 scope.

Covers:

- End-to-end query counts on relation traversal: ``select_related`` for
  forward FK, ``prefetch_related`` for reverse FK, both combined.
- Root-field gate: only root resolvers trigger optimization; inner
  resolvers pass through.
- Type-tracing: recursive unwrap of graphql-core's ``GraphQLNonNull`` /
  ``GraphQLList`` wrappers to reach the ``DjangoType`` class.
- Passthrough cases: non-``QuerySet`` resolver returns; resolvers whose
  return type is not registered in the registry; resolvers that select
  no relations (just scalars).
- ``on_execute`` ContextVar lifecycle.

Slice 5 (``only()`` projection) and Slice 6 (``plan_relation`` downgrade)
are placeholder-skipped at the bottom of the file.
"""

import contextlib
from types import SimpleNamespace

import pytest
import strawberry
from fakeshop.products import services
from fakeshop.products.models import Category, Entry, Item, Property

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType
from django_strawberry_framework.optimizer import logger as optimizer_logger
from django_strawberry_framework.optimizer.extension import (
    _optimizer_active,
    _resolve_model_from_return_type,
)
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# End-to-end query-count tests (O3 unskips the first two)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_applies_select_related_for_forward_fk(django_assert_num_queries):
    """A forward FK selection collapses to one SQL query via ``select_related``."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])

    # 1 SQL query: SELECT items + JOIN categories via select_related.
    with django_assert_num_queries(1):
        result = schema.execute_sync("{ allItems { name category { name } } }")
        assert result.errors is None
        assert len(result.data["allItems"]) == 25


@pytest.mark.django_db
def test_optimizer_applies_prefetch_related_for_reverse_fk(django_assert_num_queries):
    """A reverse FK selection collapses to two SQL queries via ``prefetch_related``."""
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])

    # 2 queries: SELECT categories + prefetched items.
    with django_assert_num_queries(2):
        result = schema.execute_sync("{ allCategories { name items { name } } }")
        assert result.errors is None
        assert len(result.data["allCategories"]) == 25


@pytest.mark.django_db
def test_optimizer_combines_select_related_and_prefetch_related(django_assert_num_queries):
    """A query selecting both a forward FK and a reverse rel issues 2 queries total."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category", "entries")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])

    # 2 queries: SELECT items+categories (JOIN) + prefetched entries.
    with django_assert_num_queries(2):
        result = schema.execute_sync(
            "{ allItems { name category { name } entries { value } } }",
        )
        assert result.errors is None


@pytest.mark.django_db
def test_optimizer_skips_when_no_relations_selected(django_assert_num_queries):
    """If the selection contains only scalars, the queryset is unchanged."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])

    # 1 query, no select_related / prefetch_related applied.
    with django_assert_num_queries(1):
        result = schema.execute_sync("{ allCategories { name } }")
        assert result.errors is None


@pytest.mark.django_db
def test_optimizer_passes_through_non_queryset(django_assert_num_queries):
    """A resolver returning a plain ``list`` (not a ``QuerySet``) skips the optimizer."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def categories_as_list(self) -> list[CategoryType]:
            # Materializing the queryset turns it into a Python list, so the
            # optimizer's ``isinstance(result, QuerySet)`` check returns False.
            return list(Category.objects.all())

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])

    # The materialization issues 1 query; nothing else fires because
    # the optimizer hands the list straight back to Strawberry.
    with django_assert_num_queries(1):
        result = schema.execute_sync("{ categoriesAsList { name } }")
        assert result.errors is None


@pytest.mark.django_db
def test_optimizer_passes_through_unregistered_return_type(caplog):
    """If the return type isn't in the registry, the queryset is unchanged."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])

    # Drop the registry mid-test — schema is already built, but the optimizer
    # looks up the registry per resolver call, so the lookup misses.
    registry.clear()

    caplog.set_level("DEBUG", logger=optimizer_logger.name)
    result = schema.execute_sync("{ allCategories { name } }")
    assert result.errors is None
    # The optimizer logs a debug line when it falls through.
    assert any("no registered DjangoType" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# O3: type-tracing through graphql-core wrappers
# ---------------------------------------------------------------------------


def test_resolve_model_from_return_type_unwraps_nested_wrappers():
    """Recursive unwrap through NonNull(List(NonNull(ObjectType))) -> Django model."""
    from graphql import GraphQLList, GraphQLNonNull

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    # Build a minimal schema so get_type_by_name works.
    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    schema = strawberry.Schema(query=Query)

    # Simulate the graphql-core wrapper stack the resolve hook sees.
    inner = schema._schema.type_map["CategoryType"]
    wrapped = GraphQLNonNull(GraphQLList(GraphQLNonNull(inner)))

    info = SimpleNamespace(
        return_type=wrapped,
        schema=schema._schema,
    )
    assert _resolve_model_from_return_type(info) is Category


def test_resolve_model_returns_none_for_non_object_leaf():
    """When the leaf type has no name (e.g. a scalar), returns None."""
    info = SimpleNamespace(
        return_type=SimpleNamespace(),  # no of_type, no name
        schema=None,
    )
    assert _resolve_model_from_return_type(info) is None


def test_resolve_model_returns_none_when_no_strawberry_schema():
    """When schema._strawberry_schema is missing, returns None."""
    info = SimpleNamespace(
        return_type=SimpleNamespace(name="SomeType"),
        schema=SimpleNamespace(),  # no _strawberry_schema
    )
    assert _resolve_model_from_return_type(info) is None


def test_resolve_model_returns_none_when_type_not_in_schema():
    """When get_type_by_name returns None (type not in schema), returns None."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    schema = strawberry.Schema(query=Query)

    info = SimpleNamespace(
        return_type=SimpleNamespace(name="NonExistentType"),
        schema=schema._schema,
    )
    assert _resolve_model_from_return_type(info) is None


# ---------------------------------------------------------------------------
# O3: defensive branches in _optimize
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimize_handles_empty_field_nodes(django_assert_num_queries):
    """If field_nodes is empty, _optimize returns the queryset unchanged."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])

    # Drive _optimize directly with a synthetic info that has empty field_nodes.
    ext = DjangoOptimizerExtension()

    info = SimpleNamespace(
        return_type=schema._schema.type_map["CategoryType"],
        schema=schema._schema,
        field_name="allCategories",
        field_nodes=[],
    )
    qs = Category.objects.all()
    result = ext._optimize(qs, info)
    # Should return the queryset unchanged (no field_nodes to plan from).
    assert result.query.select_related is False


# ---------------------------------------------------------------------------
# O3: on_execute ContextVar lifecycle
# ---------------------------------------------------------------------------


def test_on_execute_sets_and_resets_context_var():
    """on_execute sets _optimizer_active to True, then resets on exit."""
    ext = DjangoOptimizerExtension()
    assert _optimizer_active.get() is False
    gen = ext.on_execute()
    next(gen)  # enter
    assert _optimizer_active.get() is True
    with contextlib.suppress(StopIteration):
        next(gen)
    assert _optimizer_active.get() is False


# ---------------------------------------------------------------------------
# Slice 5 / 6 placeholders
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="Slice 5: only() projection pending")
def test_optimizer_applies_only_for_selected_scalars():
    pass


@pytest.mark.skip(reason="Slice 6: plan_relation downgrade-to-Prefetch pending")
def test_optimizer_downgrades_select_related_for_custom_get_queryset():
    pass


@pytest.mark.skip(reason="Slice 4+: M2M relation — fakeshop has no M2M field; deferred.")
def test_optimizer_applies_prefetch_related_for_m2m():
    pass
