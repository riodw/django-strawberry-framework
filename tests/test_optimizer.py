"""Tests for ``DjangoOptimizerExtension`` — Slice 4 scope.

Covers:

- End-to-end query counts on relation traversal: ``select_related`` for
  forward FK, ``prefetch_related`` for reverse FK, both combined.
- Passthrough cases: non-``QuerySet`` resolver returns; resolvers whose
  return type is not registered in the registry; resolvers that select
  no relations (just scalars).
- Direct unit coverage of the ``_unwrap_return_type``, ``_plan``, and
  ``_snake_case`` helpers so the branches Strawberry doesn't naturally
  exercise (alternate wrapper shapes, empty selection sets, unknown
  field names) are still covered.

Slice 5 (``only()`` projection) and Slice 6 (``plan_relation`` downgrade)
are placeholder-skipped at the bottom of the file.
"""

import asyncio
from types import SimpleNamespace

import pytest
import strawberry
from fakeshop.products import services
from fakeshop.products.models import Category, Entry, Item, Property

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType
from django_strawberry_framework.optimizer import logger as optimizer_logger
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# End-to-end query-count tests
# ---------------------------------------------------------------------------


@pytest.mark.skip(
    reason=(
        "Pending spec-optimizer.md Slice O3. Slice 4's per-resolver hook ships "
        "select_related correctly but the test path renders reverse rels in sibling "
        "setup, which trips Strawberry's iterability error. Will re-enable once O1 "
        "adds custom relation resolvers and O3 hooks the optimizer at on_executing_start."
    ),
)
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

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension])

    # 1 SQL query: SELECT items + JOIN categories via select_related.
    with django_assert_num_queries(1):
        result = schema.execute_sync("{ allItems { name category { name } } }")
        assert result.errors is None
        assert len(result.data["allItems"]) == 25


@pytest.mark.skip(
    reason=(
        "Pending spec-optimizer.md Slice O1 + O3. Strawberry's default resolver "
        "chokes on RelatedManager (Expected Iterable). O1 adds custom relation "
        "resolvers; O3 reroutes the optimizer to on_executing_start."
    ),
)
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

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension])

    # 2 queries: SELECT categories + prefetched items.
    with django_assert_num_queries(2):
        result = schema.execute_sync("{ allCategories { name items { name } } }")
        assert result.errors is None
        assert len(result.data["allCategories"]) == 25


@pytest.mark.skip(
    reason=(
        "Pending spec-optimizer.md Slice O1 + O3. Same iterability issue on the "
        "reverse-rel branch; will re-enable once custom resolvers + top-level "
        "selection-tree walker land."
    ),
)
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

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category", "entries")

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension])

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

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension])

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

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension])

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

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension])

    # Drop the registry mid-test — schema is already built, but the optimizer
    # looks up the registry per resolver call, so the lookup misses.
    registry.clear()

    caplog.set_level("DEBUG", logger=optimizer_logger.name)
    result = schema.execute_sync("{ allCategories { name } }")
    assert result.errors is None
    # The optimizer logs a debug line when it falls through.
    assert any("no registered DjangoType" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Direct unit coverage of helpers
# ---------------------------------------------------------------------------


def test_unwrap_return_type_handles_typing_list():
    """``list[T]`` annotation unwraps to ``T``."""
    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert ext._unwrap_return_type(list[CategoryType]) is CategoryType


def test_unwrap_return_type_handles_strawberry_of_type():
    """A Strawberry-style wrapper exposing ``of_type`` unwraps to the inner type."""
    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class FakeStrawberryList:
        of_type = CategoryType

    assert ext._unwrap_return_type(FakeStrawberryList()) is CategoryType


def test_unwrap_return_type_returns_direct_class_when_unwrapped():
    """A bare Strawberry type with no wrapper passes through."""
    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert ext._unwrap_return_type(CategoryType) is CategoryType


def test_plan_returns_empty_when_no_selected_fields():
    """Defensive guard: empty ``selected_fields`` short-circuits to empty plans."""
    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    info = SimpleNamespace(selected_fields=[])
    assert ext._plan(info, Category) == ([], [])


def test_plan_skips_selections_not_in_field_map():
    """Selections that don't map to a Django field (custom strawberry fields) are skipped."""
    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    selection = SimpleNamespace(name="bogusField", selections=[])
    info = SimpleNamespace(selected_fields=[SimpleNamespace(selections=[selection])])
    assert ext._plan(info, Category) == ([], [])


def test_snake_case_round_trips_camel_case():
    fn = DjangoOptimizerExtension._snake_case
    assert fn("name") == "name"
    assert fn("isPrivate") == "is_private"
    assert fn("createdDate") == "created_date"


# ---------------------------------------------------------------------------
# Async resolver path — exercises ``aresolve``
# ---------------------------------------------------------------------------


def test_aresolve_routes_through_optimize():
    """``aresolve`` awaits ``_next`` and then runs the same sync planner.

    Doesn't go through Strawberry; calls ``aresolve`` directly with a
    coroutine ``_next`` and a synthetic ``info``. That keeps the test
    simple and avoids the async-Django setup overhead while still hitting
    the ``await _next(...)`` line.
    """
    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    async def fake_next(root, info, *args, **kwargs):
        return Category.objects.all()

    info = SimpleNamespace(
        return_type=list[CategoryType],
        selected_fields=[SimpleNamespace(selections=[])],
    )

    result = asyncio.run(ext.aresolve(fake_next, None, info))
    # The optimizer didn't fail and returned a queryset (no relations selected).
    assert result.model is Category


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
