"""Tests for ``DjangoOptimizerExtension``.

Covers, by topic code:

- **O3** — end-to-end relation traversal (forward FK ``select_related``,
  reverse FK ``prefetch_related``, combined), root-field gate,
  ``GraphQLNonNull`` / ``GraphQLList`` type tracing, passthrough cases,
  ``on_execute`` ContextVar lifecycle, async resolver parity.
- **O4** — nested prefetch chains and nested select-related chains.
- **O5** — ``only()`` projection collection.
- **O6** — ``plan_relation`` downgrade from ``select_related`` to
  ``Prefetch`` for target types with custom ``get_queryset`` hooks.
- **B1** — plan cache: hits, misses, eviction, named-fragment
  differentiation, directive-variable cache splitting, runtime-path
  inclusion.
- **B2** — forward FK-id elision (and the guards that disable it).
- **B3** — strictness API (``off`` / ``warn`` / ``raise``).
- **B4** — ``Meta.optimizer_hints`` (SKIP, force_select, force_prefetch,
  explicit ``Prefetch``).
- **B5** — plan introspection via ``info.context`` and the read/write
  symmetry of the ``_context`` helpers (dict, dict-subclass, non-dict
  mapping, frozen mapping, immutable ``dict`` subclass, ``None``).
- **B6** — schema-build-time optimization audit (``check_schema``,
  ``_collect_schema_reachable_types`` including union-type descent).
- **B8** — consumer-queryset-aware plan diffing.
- Extension construction surface (unknown-kwarg rejection, Strawberry
  ``execution_context`` keyword).
- ``hint_is_skip`` dispatch shapes.

Every test uses the autouse ``_isolate_registry`` fixture so the
global ``registry`` is cleared on entry and exit.
"""

import contextlib
from types import SimpleNamespace

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Entry, Item, Property

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types
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

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])

    # 1 SQL query: SELECT items + JOIN categories via select_related.
    with django_assert_num_queries(1):
        result = schema.execute_sync("{ allItems { name category { name } } }")
        assert result.errors is None
        assert len(result.data["allItems"]) == 25


@pytest.mark.django_db
def test_optimizer_plans_merged_duplicate_root_field_nodes(django_assert_num_queries):
    """Merged duplicate root fields contribute all child selections to one plan."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension(strictness="raise")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()

    with django_assert_num_queries(1):
        result = schema.execute_sync(
            "{ allItems { name } allItems { category { name } } }",
            context_value=ctx,
        )

    assert result.errors is None
    assert result.data["allItems"][0]["name"]
    assert result.data["allItems"][0]["category"]["name"]
    assert ctx.dst_optimizer_plan.select_related == ("category",)
    assert "ItemType.category@allItems.category" in ctx.dst_optimizer_planned


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

    finalize_django_types()
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

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])

    # 2 queries: SELECT items+categories (JOIN) + prefetched entries.
    with django_assert_num_queries(2):
        result = schema.execute_sync(
            "{ allItems { name category { name } entries { value } } }",
        )
        assert result.errors is None


@pytest.mark.django_db
def test_optimizer_elides_forward_fk_id_only_selection(django_assert_num_queries):
    """B2: ``category { id }`` is served from ``Item.category_id`` with no JOIN."""
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

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()

    with django_assert_num_queries(1):
        result = schema.execute_sync(
            "{ allItems { name category { id } } }",
            context_value=ctx,
        )
    assert result.errors is None
    assert len(result.data["allItems"]) == 25
    assert all(item["category"]["id"] for item in result.data["allItems"])
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("name", "category_id")
    assert plan.fk_id_elisions == ("ItemType.category@allItems.category",)
    assert ctx.dst_optimizer_fk_id_elisions == {"ItemType.category@allItems.category"}


@pytest.mark.django_db
def test_optimizer_elides_forward_fk_id_only_selection_for_each_alias(django_assert_num_queries):
    """B2/O4: duplicate aliases are both served from the source FK column."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()

    with django_assert_num_queries(1):
        result = schema.execute_sync(
            "{ allItems { first: category { id } second: category { id } } }",
            context_value=ctx,
        )
    assert result.errors is None
    assert all(item["first"]["id"] == item["second"]["id"] for item in result.data["allItems"])
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert plan.prefetch_related == ()
    assert plan.only_fields == ("category_id",)
    assert plan.fk_id_elisions == (
        "ItemType.category@allItems.first",
        "ItemType.category@allItems.second",
    )
    assert ctx.dst_optimizer_fk_id_elisions == {
        "ItemType.category@allItems.first",
        "ItemType.category@allItems.second",
    }


@pytest.mark.django_db
def test_optimizer_does_not_elide_forward_fk_when_extra_scalar_selected(django_assert_num_queries):
    """B2: selecting any target scalar beyond ``id`` keeps the normal JOIN path."""
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

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()

    with django_assert_num_queries(1):
        result = schema.execute_sync(
            "{ allItems { name category { id name } } }",
            context_value=ctx,
        )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ("category",)
    assert plan.fk_id_elisions == ()
    assert plan.only_fields == ("name", "category_id", "category__id", "category__name")


@pytest.mark.django_db
def test_optimizer_does_not_elide_forward_fk_when_target_has_custom_get_queryset(
    django_assert_num_queries,
):
    """B2: a custom target ``get_queryset`` uses O6 Prefetch even for ``id`` only."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()

    with django_assert_num_queries(2):
        result = schema.execute_sync(
            "{ allItems { name category { id } } }",
            context_value=ctx,
        )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert plan.fk_id_elisions == ()
    assert plan.only_fields == ("name", "category_id")
    assert len(plan.prefetch_related) == 1


@pytest.mark.django_db
def test_optimizer_skips_when_no_relations_selected(django_assert_num_queries):
    """If the selection contains only scalars, only projection is applied."""
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

    finalize_django_types()
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

    finalize_django_types()
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

    finalize_django_types()
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
    """Recursive unwrap through NonNull(List(NonNull(ObjectType))) -> (origin, Django model)."""
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

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    # Simulate the graphql-core wrapper stack the resolve hook sees.
    inner = schema._schema.type_map["CategoryType"]
    wrapped = GraphQLNonNull(GraphQLList(GraphQLNonNull(inner)))

    info = SimpleNamespace(
        return_type=wrapped,
        schema=schema._schema,
    )
    result = _resolve_model_from_return_type(info)
    assert result is not None
    assert result.model is Category
    assert result.origin is CategoryType


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

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    info = SimpleNamespace(
        return_type=SimpleNamespace(name="NonExistentType"),
        schema=schema._schema,
    )
    assert _resolve_model_from_return_type(info) is None


def test_resolve_model_returns_none_when_definition_has_no_origin():
    """When the schema's type definition lacks an ``origin`` (e.g. a scalar / interface), returns None."""
    fake_strawberry_schema = SimpleNamespace(
        get_type_by_name=lambda _name: SimpleNamespace(),  # definition without `origin`
    )
    info = SimpleNamespace(
        return_type=SimpleNamespace(name="SomeType"),
        schema=SimpleNamespace(_strawberry_schema=fake_strawberry_schema),
    )
    assert _resolve_model_from_return_type(info) is None


# ---------------------------------------------------------------------------
# O3: root-field gate
# ---------------------------------------------------------------------------


def test_resolve_passes_through_non_root_resolvers():
    """Non-root resolvers (info.path.prev is not None) bypass _optimize entirely."""
    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    # Simulate a non-root resolver: path.prev is not None.
    qs = Category.objects.all()
    called_with = {}

    def fake_next(root, info, *args, **kwargs):
        called_with["fired"] = True
        return qs

    info = SimpleNamespace(
        path=SimpleNamespace(prev=SimpleNamespace(key="parent", prev=None, typename="Query")),
    )
    result = ext.resolve(fake_next, None, info)
    # _next was called and result passed through unchanged (no _optimize).
    assert called_with["fired"] is True
    assert result is qs


# ---------------------------------------------------------------------------
# O3: async resolver parity
# ---------------------------------------------------------------------------


def test_resolve_handles_async_root_resolver():
    """An async root resolver's coroutine is awaited before optimization."""
    import asyncio

    ext = DjangoOptimizerExtension()

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    qs = Category.objects.all()

    async def fake_next(root, info, *args, **kwargs):
        return qs

    # Root resolver: path.prev is None.
    info = SimpleNamespace(
        path=SimpleNamespace(prev=None, key="allCategories", typename="Query"),
        return_type=SimpleNamespace(),  # no name -> _resolve_model returns None
        schema=None,
        field_name="allCategories",
        field_nodes=[],
    )
    result = ext.resolve(fake_next, None, info)
    # result should be a coroutine (async wrapper)
    assert asyncio.iscoroutine(result)
    # Await it — _optimize will pass through because return_type has no name.
    resolved = asyncio.run(result)
    assert resolved is qs


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

    finalize_django_types()
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


@pytest.mark.django_db
def test_optimize_returns_original_queryset_for_empty_plan(monkeypatch):
    """If the walker produces an empty plan, _optimize returns the original queryset."""
    import django_strawberry_framework.optimizer.extension as extension_module
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

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

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    monkeypatch.setattr(
        extension_module,
        "plan_optimizations",
        lambda selected_fields, model, info=None, *, source_type=None: OptimizationPlan(),
    )
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    assert result.errors is None
    assert ctx.dst_optimizer_plan.is_empty


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
# B1: plan cache
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cache_hit_on_repeated_query(django_assert_num_queries):
    """B1: executing the same query twice produces a cache hit on the second call."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    query = "{ allItems { name category { name } } }"

    schema.execute_sync(query)
    assert ext.cache_info().misses == 1
    assert ext.cache_info().hits == 0

    schema.execute_sync(query)
    assert ext.cache_info().hits == 1
    assert ext.cache_info().misses == 1
    assert ext.cache_info().size == 1


@pytest.mark.django_db
def test_cache_differentiates_queries(django_assert_num_queries):
    """B1: different queries produce different cache entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])

    schema.execute_sync("{ allItems { name } }")
    schema.execute_sync("{ allItems { name category { name } } }")
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


@pytest.mark.django_db
def test_cache_differentiates_reachable_named_fragment_bodies():
    """B1: matching operation text with different fragment bodies gets distinct plans."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    query_prefix = "query Q { allItems { ...ItemBits } }"
    ctx_scalar = SimpleNamespace()
    ctx_relation = SimpleNamespace()

    result_scalar = schema.execute_sync(
        f"{query_prefix} fragment ItemBits on ItemType {{ name }}",
        context_value=ctx_scalar,
    )
    result_relation = schema.execute_sync(
        f"{query_prefix} fragment ItemBits on ItemType {{ category {{ name }} }}",
        context_value=ctx_relation,
    )

    assert result_scalar.errors is None
    assert result_relation.errors is None
    assert ctx_scalar.dst_optimizer_plan.select_related == ()
    assert ctx_relation.dst_optimizer_plan.select_related == ("category",)
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


@pytest.mark.django_db
def test_cache_differentiates_same_model_root_fields(django_assert_num_queries):
    """B1/O4: root fields returning the same model do not share one cached plan."""
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

        @strawberry.field
        def featured_categories(self) -> list[CategoryType]:
            return Category.objects.filter(is_private=False)

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()
    query = "{ allCategories { name items { name } } featuredCategories { name } }"

    with django_assert_num_queries(3):
        result = schema.execute_sync(query, context_value=ctx)

    assert result.errors is None
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2
    assert ctx.dst_optimizer_plan.prefetch_related == ()


def test_cache_key_includes_root_runtime_path_for_same_model_fields():
    """B1/O4: cache keys differ for root fields returning the same model."""
    from graphql import parse

    operation = parse("{ allCategories { name } featured { name } }").definitions[0]
    info_a = SimpleNamespace(
        operation=operation,
        fragments={},
        variable_values={},
        path=SimpleNamespace(key="allCategories", prev=None),
    )
    info_b = SimpleNamespace(
        operation=operation,
        fragments={},
        variable_values={},
        path=SimpleNamespace(key="featured", prev=None),
    )

    assert DjangoOptimizerExtension._build_cache_key(
        info_a,
        Category,
    ) != DjangoOptimizerExtension._build_cache_key(info_b, Category)


def test_cache_key_differs_for_named_operations_in_same_document():
    """B1: two named operations in one document must not share a plan cache entry."""
    from graphql import parse

    doc = parse("query A { allItems { name } } query B { allItems { category { name } } }")
    operation_a = next(d for d in doc.definitions if getattr(d.name, "value", None) == "A")
    operation_b = next(d for d in doc.definitions if getattr(d.name, "value", None) == "B")
    info_a = SimpleNamespace(
        operation=operation_a,
        fragments={},
        variable_values={},
        path=SimpleNamespace(key="allItems", prev=None),
    )
    info_b = SimpleNamespace(
        operation=operation_b,
        fragments={},
        variable_values={},
        path=SimpleNamespace(key="allItems", prev=None),
    )

    assert DjangoOptimizerExtension._build_cache_key(
        info_a,
        Item,
    ) != DjangoOptimizerExtension._build_cache_key(info_b, Item)


@pytest.mark.django_db
def test_cache_eviction_removes_old_entries(monkeypatch):
    """B1: the plan cache evicts old entries when it reaches capacity."""
    import django_strawberry_framework.optimizer.extension as extension_module

    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    ext = DjangoOptimizerExtension()
    monkeypatch.setattr(extension_module, "_MAX_PLAN_CACHE_SIZE", 4)
    ext._plan_cache = {(idx, frozenset(), Category, (f"root{idx}",), None): object() for idx in range(4)}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    result = schema.execute_sync("{ allCategories { name } }")

    assert result.errors is None
    assert ext.cache_info().misses == 1
    assert ext.cache_info().size == 4
    assert (0, frozenset(), Category, ("root0",), None) not in ext._plan_cache


@pytest.mark.django_db
def test_filter_vars_do_not_affect_cache():
    """B1: variables not used in @skip/@include don't split cache entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self, limit: int = 10) -> list[ItemType]:
            return Item.objects.all()[:limit]

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    query = "query Q($limit: Int!) { allItems(limit: $limit) { name category { name } } }"

    schema.execute_sync(query, variable_values={"limit": 5})
    schema.execute_sync(query, variable_values={"limit": 10})
    # Same query shape, different filter var — should be 1 miss + 1 hit.
    assert ext.cache_info().hits == 1
    assert ext.cache_info().size == 1


@pytest.mark.django_db
def test_cache_separates_operation_names_in_same_document():
    """B1: executing two named operations in one document yields two cache entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    document = "query A { allItems { name } } query B { allItems { name category { name } } }"

    result_a = schema.execute_sync(document, operation_name="A")
    result_b = schema.execute_sync(document, operation_name="B")

    assert result_a.errors is None
    assert result_b.errors is None
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


def test_build_cache_key_is_stable_when_source_location_missing():
    """B1: cache key still works when the operation has no source body."""
    from graphql import parse

    operation = parse("{ allCategories { name } }", no_location=True).definitions[0]
    info = SimpleNamespace(
        operation=operation,
        fragments={},
        variable_values={},
        path=None,
    )

    key = DjangoOptimizerExtension._build_cache_key(info, Category)

    assert key[2] is Category
    assert isinstance(key[3], tuple)


def test_collect_directive_var_names_with_skip():
    """B1: _collect_directive_var_names finds vars in @skip directives."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse("query Q($show: Boolean!) { items @skip(if: $show) { name } }")
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset({"show"})


def test_collect_directive_var_names_with_include():
    """B1: _collect_directive_var_names finds vars in @include directives."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse("query Q($v: Boolean!) { items @include(if: $v) { name } }")
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset({"v"})


def test_collect_directive_var_names_ignores_non_directive_vars():
    """B1: variables in field arguments (not directives) are not collected."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse("query Q($limit: Int!) { items(limit: $limit) { name } }")
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset()


def test_walk_directives_ignores_non_directive_objects():
    """B1: directive collection skips defensive non-DirectiveNode entries."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _walk_directives

    operation = parse("query Q($v: Boolean!) { items @skip(if: $v) { name } }").definitions[0]
    field = operation.selection_set.selections[0]

    names: set[str] = set()
    node = SimpleNamespace(directives=[object(), *field.directives], selection_set=None)
    _walk_directives(node, names, fragments={}, visited_fragments=set())
    assert names == {"v"}


def test_walk_directives_visits_each_fragment_once_across_sibling_spreads():
    """Sibling spreads of the same fragment do not re-walk the fragment subtree."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _walk_directives

    doc = parse(
        "query Q($v: Boolean!) { "
        "a: items { ...F } "
        "b: items { ...F } "
        "} "
        "fragment F on Item { name @skip(if: $v) }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions[1:]}
    names: set[str] = set()
    visited: set[str] = set()
    _walk_directives(operation, names, fragments, visited)
    assert names == {"v"}
    # Fragment F was descended exactly once even though it was spread twice.
    assert visited == {"F"}


def test_walk_directives_handles_unresolved_fragment_name():
    """A spread referencing an unknown fragment name is skipped silently."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _walk_directives

    doc = parse("query Q { items { ...Missing } }")
    operation = doc.definitions[0]
    names: set[str] = set()
    visited: set[str] = set()
    _walk_directives(operation, names, fragments={}, visited_fragments=visited)
    assert names == set()
    assert visited == set()


def test_collect_directive_var_names_ignores_other_directives():
    """B1: only @skip and @include directives split the plan cache."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse("query Q($v: Boolean!) { items @custom(if: $v) { name } }")
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset()


def test_collect_directive_var_names_nested_fragments():
    """B1: vars in directives on nested fields are collected."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse(
        "query Q($a: Boolean!, $b: Boolean!) { "
        "items { name @skip(if: $a) entries @include(if: $b) { value } } }",
    )
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset({"a", "b"})


def test_collect_directive_var_names_no_directives():
    """B1: a query with no directives returns an empty frozenset."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse("{ items { name } }")
    names = _collect_directive_var_names(doc.definitions[0])
    assert names == frozenset()


# ---------------------------------------------------------------------------
# B3: N+1 detection (strictness API)
# ---------------------------------------------------------------------------


def test_strictness_invalid_value_raises():
    """B3: passing an invalid strictness value raises ValueError."""
    with pytest.raises(ValueError, match="strictness must be"):
        DjangoOptimizerExtension(strictness="invalid")


@pytest.mark.django_db
def test_strictness_warn_logs_unplanned_relation(caplog):
    """B3: strictness='warn' logs a warning for unplanned uncached relation access."""
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
            return list(Item.objects.all()[:1])

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    ctx = SimpleNamespace(
        dst_optimizer_planned=set(),
        dst_optimizer_strictness="warn",
    )

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert any("Potential N+1 on category" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_strictness_off_does_not_stash_sentinel():
    """B3: strictness='off' does not stash the sentinel on context."""
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

    ext = DjangoOptimizerExtension(strictness="off")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    assert result.errors is None
    # No sentinel stashed when strictness is off.
    assert not hasattr(ctx, "dst_optimizer_planned")


@pytest.mark.django_db
def test_strictness_warn_stashes_sentinel():
    """B3: strictness='warn' stashes the sentinel on context."""
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

    ext = DjangoOptimizerExtension(strictness="warn")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    planned = getattr(ctx, "dst_optimizer_planned", None)
    assert planned is not None
    assert "ItemType.category@allItems.category" in planned
    assert getattr(ctx, "dst_optimizer_strictness") == "warn"


@pytest.mark.django_db
def test_strictness_includes_fk_id_elision_in_planned_paths(caplog):
    """B2+B3: FK-id-elided relations are planned and do not warn."""
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

    ext = DjangoOptimizerExtension(strictness="warn")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = schema.execute_sync(
        "{ allItems { name category { id } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert "ItemType.category@allItems.category" in ctx.dst_optimizer_planned
    assert ctx.dst_optimizer_fk_id_elisions == {"ItemType.category@allItems.category"}
    assert not any("Potential N+1" in r.message for r in caplog.records)


def test_will_lazy_load_false_when_cached():
    """B3: pin the __dict__ compatibility seam used by synthetic test doubles."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load_single

    root = SimpleNamespace(category="cached_value")
    assert _will_lazy_load_single(root, "category") is False


def test_will_lazy_load_false_when_in_fields_cache():
    """B3: _will_lazy_load_single returns False when a relation is in _state.fields_cache."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load_single

    root = SimpleNamespace(_state=SimpleNamespace(fields_cache={"card": "cached"}))
    assert _will_lazy_load_single(root, "card") is False


@pytest.mark.django_db
def test_will_lazy_load_false_for_real_forward_fk_in_fields_cache():
    """B3: real forward FKs cache in _state.fields_cache, not __dict__."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load_single

    services.seed_data(1)
    item = Item.objects.select_related("category").first()

    assert item is not None
    assert "category" not in item.__dict__
    assert "category" in item._state.fields_cache
    assert _will_lazy_load_single(item, "category") is False


@pytest.mark.django_db
def test_will_lazy_load_false_for_real_reverse_one_to_one_in_fields_cache():
    """B3: real reverse OneToOne relations also cache in _state.fields_cache."""
    from apps.library.models import MembershipCard, Patron

    from django_strawberry_framework.types.resolvers import _will_lazy_load_single

    patron = Patron.objects.create(name="Rio")
    MembershipCard.objects.create(patron=patron, barcode="1234")
    cached_patron = Patron.objects.select_related("card").get(pk=patron.pk)

    assert "card" not in cached_patron.__dict__
    assert "card" in cached_patron._state.fields_cache
    assert _will_lazy_load_single(cached_patron, "card") is False


def test_will_lazy_load_true_when_not_cached():
    """B3: _will_lazy_load_single returns True when the relation is not cached."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load_single

    root = SimpleNamespace()
    assert _will_lazy_load_single(root, "category") is True


def test_will_lazy_load_false_when_prefetched():
    """B3: _will_lazy_load_many returns False when relation is in _prefetched_objects_cache."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load_many

    root = SimpleNamespace()
    root._prefetched_objects_cache = {"items": [1, 2, 3]}
    assert _will_lazy_load_many(root, "items") is False


@pytest.mark.django_db
def test_strictness_raise_accepts_unplanned_cached_forward_fk():
    """B3: strictness='raise' accepts an unplanned forward FK that is already loaded."""
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
            return list(Item.objects.select_related("category").all()[:1])

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    ctx = SimpleNamespace(
        dst_optimizer_planned=set(),
        dst_optimizer_strictness="raise",
    )

    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert result.data["allItems"][0]["category"]["name"]


@pytest.mark.django_db
def test_strictness_raise_accepts_unplanned_cached_reverse_one_to_one():
    """B3: strictness='raise' accepts an unplanned reverse OneToOne already loaded."""
    from apps.library.models import MembershipCard, Patron

    patron = Patron.objects.create(name="Rio")
    MembershipCard.objects.create(patron=patron, barcode="1234")

    class CardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode")

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name", "card")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_patrons(self) -> list[PatronType]:
            return list(Patron.objects.select_related("card").all())

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    ctx = SimpleNamespace(
        dst_optimizer_planned=set(),
        dst_optimizer_strictness="raise",
    )

    result = schema.execute_sync(
        "{ allPatrons { name card { barcode } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert result.data == {
        "allPatrons": [
            {
                "name": "Rio",
                "card": {"barcode": "1234"},
            },
        ],
    }


@pytest.mark.django_db
def test_strictness_warn_planned_alias_no_warning(caplog):
    """B3: aliased relation that IS planned does not trigger a warning."""
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

    ext = DjangoOptimizerExtension(strictness="warn")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    # Use an alias "cat" for the planned "category" relation.
    result = schema.execute_sync(
        "{ allItems { name cat: category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    # The plan includes "category" and the resolver uses field_name
    # (not the alias), so no false-positive warning.
    assert not any("Potential N+1" in r.message for r in caplog.records)


@pytest.mark.django_db
def test_optimizer_prefetches_nested_reverse_fk_depth_2(django_assert_num_queries):
    """O4: nested reverse-FK traversal is optimized from the root queryset."""
    services.seed_data(1)

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "entries")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])

    with django_assert_num_queries(3):
        result = schema.execute_sync("{ allCategories { items { entries { value } } } }")
    assert result.errors is None


@pytest.mark.django_db
def test_optimizer_selects_nested_forward_fk_depth_2(django_assert_num_queries):
    """O4: nested forward-FK traversal stays in a single joined query."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "category")

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "item")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_entries(self) -> list[EntryType]:
            return Entry.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])

    with django_assert_num_queries(1):
        result = schema.execute_sync("{ allEntries { item { category { name } } } }")
    assert result.errors is None


@pytest.mark.django_db
def test_optimizer_strictness_accepts_nested_planned_relation():
    """O4+B3: strictness accepts resolver keys from nested plans."""
    services.seed_data(1)

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "entries")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    ext = DjangoOptimizerExtension(strictness="raise")
    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allCategories { items { entries { value } } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert "ItemType.entries@allCategories.items.entries" in ctx.dst_optimizer_planned


@pytest.mark.django_db
def test_optimizer_nested_fk_id_elision_does_not_leak_to_sibling_branch(django_assert_num_queries):
    """O4+B2: FK-id elision on one root branch does not leak to another."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "category")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

        @strawberry.field
        def all_properties(self) -> list[PropertyType]:
            return Property.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()

    with django_assert_num_queries(2):
        result = schema.execute_sync(
            "{ allItems { category { id } } allProperties { category { name } } }",
            context_value=ctx,
        )
    assert result.errors is None
    assert result.data["allItems"][0]["category"]["id"]
    assert result.data["allProperties"][0]["category"]["name"]


@pytest.mark.django_db
def test_optimizer_nested_prefetch_with_custom_get_queryset_marks_uncacheable():
    """O4+O6: nested request-dependent prefetch plans are not cached."""
    services.seed_data(1)
    calls = []

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            calls.append(info)
            return queryset

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "entries")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "items")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    query = "{ allCategories { items { entries { value } } } }"

    assert schema.execute_sync(query).errors is None
    assert schema.execute_sync(query).errors is None
    assert len(calls) == 2
    assert ext.cache_info().size == 0


def test_collect_directive_var_names_in_named_fragment():
    """B1: _collect_directive_var_names follows named fragment spreads."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse(
        "query Q($show: Boolean!) { allItems { ...ItemBits } } "
        "fragment ItemBits on ItemType { category @include(if: $show) { name } }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions if hasattr(d, "type_condition")}
    names = _collect_directive_var_names(operation, fragments=fragments)
    assert names == frozenset({"show"})


def test_collect_directive_var_names_includes_fragment_spread_directives():
    """B1: directives on a ``...Spread`` itself feed the cache key, not just the body."""
    from graphql import parse

    from django_strawberry_framework.optimizer.extension import _collect_directive_var_names

    doc = parse(
        "query Q($show: Boolean!) { allItems { ...ItemBits @include(if: $show) } } "
        "fragment ItemBits on ItemType { category { name } }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions if hasattr(d, "type_condition")}
    names = _collect_directive_var_names(operation, fragments=fragments)
    assert names == frozenset({"show"})


def test_cache_key_includes_fragment_spread_directive_variable_value():
    """B1: a variable on a fragment-spread ``@include`` splits the cache."""
    from graphql import parse

    doc = parse(
        "query Q($show: Boolean!) { allItems { ...ItemBits @include(if: $show) } } "
        "fragment ItemBits on ItemType { category { name } }",
    )
    operation = doc.definitions[0]
    fragments = {d.name.value: d for d in doc.definitions if hasattr(d, "type_condition")}
    info_false = SimpleNamespace(
        operation=operation,
        fragments=fragments,
        variable_values={"show": False},
        path=SimpleNamespace(key="allItems", prev=None),
    )
    info_true = SimpleNamespace(
        operation=operation,
        fragments=fragments,
        variable_values={"show": True},
        path=SimpleNamespace(key="allItems", prev=None),
    )

    assert DjangoOptimizerExtension._build_cache_key(
        info_false,
        Item,
    ) != DjangoOptimizerExtension._build_cache_key(info_true, Item)


# ---------------------------------------------------------------------------
# B6: Schema-build-time optimization audit
# ---------------------------------------------------------------------------


def test_collect_schema_reachable_types_returns_empty_without_graphql_schema():
    """B6: schemas without a graphql-core schema expose no reachable types."""
    from django_strawberry_framework.optimizer.extension import _collect_schema_reachable_types

    assert _collect_schema_reachable_types(SimpleNamespace()) == set()


def test_check_schema_skips_unreachable_and_missing_field_map(monkeypatch):
    """B6: check_schema skips orphan types and types without optimizer metadata."""
    import django_strawberry_framework.optimizer.extension as extension_module

    class ReachableWithoutFieldMap:
        pass

    class UnreachableType:
        pass

    registry.register(Category, ReachableWithoutFieldMap)
    registry.register(Item, UnreachableType)
    monkeypatch.setattr(
        extension_module,
        "_collect_schema_reachable_types",
        lambda schema: {ReachableWithoutFieldMap},
    )

    assert DjangoOptimizerExtension.check_schema(SimpleNamespace()) == []


def test_check_schema_warns_unregistered_target():
    """B6: check_schema warns when a relation's target has no registered DjangoType."""

    # Must register CategoryType first so convert_relation succeeds,
    # then clear it from the registry so check_schema sees the gap.
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
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    # Clear Category's registration so the audit finds a gap.
    registry.unregister(CategoryType)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    assert any("category" in w and "no registered target" in w for w in warnings)


def test_check_schema_descends_into_union_types():
    """B6: union members are reachable in check_schema's audit walk.

    GraphQL unions expose their constituent object types via ``.types``,
    not ``.fields``. The schema walker must descend into ``.types`` so a
    ``DjangoType`` reachable only through a union (e.g.
    ``list[ItemType | CategoryType]``) still participates in the audit.
    Without that, ``check_schema`` silently skips missing-target warnings
    for any relation that lives on a union-member type.
    """
    from django_strawberry_framework.optimizer.extension import _collect_schema_reachable_types

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
        def search(self) -> list[ItemType | CategoryType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    # Internal reachable set must include both union members.
    reachable = _collect_schema_reachable_types(schema)
    assert ItemType in reachable
    assert CategoryType in reachable

    # User-visible consequence: drop Category's registration and check_schema
    # must still surface the gap on ItemType.category. Without the union walk
    # ItemType is unreachable from the root, the audit skips it, and the
    # warning is silently lost.
    registry.unregister(CategoryType)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    assert any("category" in w and "no registered target" in w for w in warnings)


def test_check_schema_no_warnings_when_all_covered():
    """B6: check_schema returns no warnings when all relations have registered targets."""

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
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    # category's target (Category) is registered, so no warnings for it.
    assert not any("category" in w for w in warnings)


def test_check_schema_skip_hint_suppresses_warning():
    """B6: relations with OptimizerHint.SKIP are not flagged."""
    from django_strawberry_framework import OptimizerHint

    # Register CategoryType so convert_relation succeeds.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.SKIP}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    # Clear Category so the audit would normally warn — but SKIP suppresses.
    registry.unregister(CategoryType)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    # SKIP means category is intentionally unoptimized — no warning.
    assert not any("category" in w for w in warnings)


def test_check_schema_hidden_fields_not_flagged():
    """B6: relations excluded by Meta.fields are not flagged."""

    # ItemType excludes "category" from Meta.fields.
    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    # category is not in the definition field map, so it is not flagged.
    assert not any("category" in w for w in warnings)


# ---------------------------------------------------------------------------
# B4: Meta.optimizer_hints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_hint_skip_suppresses_relation(django_assert_num_queries):
    """B4: OptimizerHint.SKIP excludes a relation from the plan."""
    from django_strawberry_framework import OptimizerHint

    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.SKIP}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    # SKIP means category is NOT in select_related.
    assert "category" not in plan.select_related


@pytest.mark.django_db
def test_optimizer_hint_skip_routes_through_hint_is_skip():
    """Pins ``rev-optimizer__hints.md`` Medium: the walker dispatches
    skip directives through ``hint_is_skip`` rather than open-coding the
    ``hint is SKIP or hint.skip`` test. A non-sentinel ``skip=True``
    instance must still be honoured.
    """
    from django_strawberry_framework import OptimizerHint

    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            # Construct a fresh skip-shaped hint instead of OptimizerHint.SKIP
            # so the dispatch path cannot rely on identity-equality alone.
            optimizer_hints = {"category": OptimizerHint(skip=True)}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert "category" not in plan.select_related


@pytest.mark.django_db
def test_optimizer_hint_force_prefetch(django_assert_num_queries):
    """B4: OptimizerHint.prefetch_related() forces prefetch on a forward FK."""
    from django_strawberry_framework import OptimizerHint

    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.prefetch_related()}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    # Force-prefetch overrides the default select_related for forward FK.
    assert [lookup.prefetch_to for lookup in plan.prefetch_related] == ["category"]
    assert "category" not in plan.select_related
    assert "category_id" in plan.only_fields


@pytest.mark.django_db
def test_optimizer_hint_force_select_does_not_bypass_custom_get_queryset(
    django_assert_num_queries,
):
    """B4+O6: ``force_select`` downgrades when the target type filters visibility."""
    from django.db.models import Prefetch

    from django_strawberry_framework import OptimizerHint

    services.seed_data(1)
    calls = []

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            calls.append(info)
            return queryset.filter(is_private=False)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            optimizer_hints = {"category": OptimizerHint.select_related()}

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def public_category_items(self) -> list[ItemType]:
            return Item.objects.filter(category__is_private=False)

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()

    with django_assert_num_queries(2):
        result = schema.execute_sync(
            "{ publicCategoryItems { name category { name } } }",
            context_value=ctx,
        )

    assert result.errors is None
    assert calls
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert plan.cacheable is False
    assert ext.cache_info().size == 0
    assert len(plan.prefetch_related) == 1
    assert isinstance(plan.prefetch_related[0], Prefetch)
    assert plan.prefetch_related[0].prefetch_to == "category"
    assert plan.prefetch_related[0].queryset.query.where


def test_optimizer_hints_unknown_field_raises():
    """B4: unknown field name in optimizer_hints raises ConfigurationError."""
    from django_strawberry_framework import OptimizerHint
    from django_strawberry_framework.exceptions import ConfigurationError

    with pytest.raises(ConfigurationError, match="optimizer_hints names unknown fields"):

        class ItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name")
                optimizer_hints = {"nonexistent": OptimizerHint.SKIP}


def test_optimizer_hints_non_hint_value_raises():
    """B4: non-OptimizerHint value in optimizer_hints raises ConfigurationError."""
    from django_strawberry_framework.exceptions import ConfigurationError

    with pytest.raises(ConfigurationError, match="OptimizerHint instances"):

        class ItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name", "category")
                optimizer_hints = {"category": "skip"}  # string, not OptimizerHint


def test_optimizer_hint_importable_from_top_level():
    """B4: OptimizerHint is importable from the top-level package."""
    from django_strawberry_framework import OptimizerHint

    assert OptimizerHint.SKIP is not None
    assert OptimizerHint.select_related() is not None


# ---------------------------------------------------------------------------
# B5: plan introspection via context
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_plan_stashed_with_select_related(django_assert_num_queries):
    """B5: the stashed plan contains the expected select_related entries."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    # Build a synthetic info to drive _optimize directly.
    from graphql import GraphQLList, GraphQLNonNull

    inner = schema._schema.type_map["ItemType"]
    wrapped = GraphQLNonNull(GraphQLList(GraphQLNonNull(inner)))

    # We need a real field_nodes to convert selections from.
    # Execute the query to get a real result, but use a custom context
    # to capture the plan.
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = getattr(ctx, "dst_optimizer_plan", None)
    assert plan is not None
    assert "category" in plan.select_related


@pytest.mark.django_db
def test_plan_stashed_with_prefetch_related(django_assert_num_queries):
    """B5: the stashed plan contains the expected prefetch_related entries."""
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

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allCategories { name items { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = getattr(ctx, "dst_optimizer_plan", None)
    assert plan is not None
    assert [lookup.prefetch_to for lookup in plan.prefetch_related] == ["items"]


def test_plan_stashed_on_dict_context():
    """B5: when context is a plain dict, plan is stashed via __setitem__."""
    from django_strawberry_framework.optimizer.extension import _stash_on_context

    ctx = {}
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    plan = OptimizationPlan(select_related=["category"])
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert ctx["dst_optimizer_plan"] is plan


def test_stash_on_dict_subclass_writes_mapping_before_attributes():
    """rev-optimizer__context: dict-like contexts must use the mapping branch."""
    from django_strawberry_framework.optimizer._context import get_context_value, stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    class AttributeBackedDict(dict):
        def __init__(self) -> None:
            super().__init__()
            super().__setattr__("attributes", {})

        def __setattr__(self, key: str, value: object) -> None:
            self.attributes[key] = value

    ctx = AttributeBackedDict()
    plan = OptimizationPlan(select_related=["category"])
    stash_on_context(ctx, "dst_optimizer_plan", plan)

    assert ctx["dst_optimizer_plan"] is plan
    assert ctx.attributes == {}
    assert get_context_value(ctx, "dst_optimizer_plan") is plan


def test_stash_on_non_dict_mapping_reads_correctly():
    """get_context_value retrieves stashes from non-dict mappings via item access fallback."""
    from django_strawberry_framework.optimizer._context import get_context_value, stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    class NonDictMapping:
        __slots__ = ("_data",)

        def __init__(self):
            self._data = {}

        def __setitem__(self, key, value):
            self._data[key] = value

        def __getitem__(self, key):
            return self._data[key]

    ctx = NonDictMapping()
    plan = OptimizationPlan()
    stash_on_context(ctx, "dst_optimizer_plan", plan)

    # Assert stash bypassed setattr (because of __slots__) and populated _data
    assert ctx._data["dst_optimizer_plan"] is plan

    # Assert get_context_value safely falls back to item access and retrieves it
    assert get_context_value(ctx, "dst_optimizer_plan") is plan


def test_get_context_value_swallows_attribute_error_from_getitem():
    """rev-optimizer__context: ``__getitem__`` raising ``AttributeError`` on a missing key returns ``default``.

    ``strawberry-graphql-django``'s ``StrawberryDjangoContext`` bridges
    ``__getitem__`` to ``__getattribute__``, so reading a key that was never
    stashed raises ``AttributeError`` out of the item access path. The read
    helper's ``except`` tuple must catch ``AttributeError`` alongside
    ``KeyError`` / ``TypeError`` so the resolver chain sees ``default`` rather
    than a leaking ``AttributeError`` from deep inside item lookup.
    """
    from django_strawberry_framework.optimizer._context import get_context_value

    class BridgedItemAccess:
        """Mimics ``StrawberryDjangoContext.__getitem__`` shape."""

        def __getitem__(self, key):
            raise AttributeError(f"missing attribute {key!r}")

    sentinel = object()
    ctx = BridgedItemAccess()
    assert get_context_value(ctx, "dst_optimizer_plan", sentinel) is sentinel


def test_stash_on_none_context_is_silent():
    """B5: when context is None (Strawberry default), stash is silently skipped."""
    from django_strawberry_framework.optimizer.extension import _stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    plan = OptimizationPlan()
    # Should not raise.
    _stash_on_context(None, "dst_optimizer_plan", plan)


def test_plan_stashed_on_object_context_unit():
    """B5: when context is an object, plan is stashed via setattr."""
    from django_strawberry_framework.optimizer.extension import _stash_on_context

    ctx = SimpleNamespace()
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    plan = OptimizationPlan(prefetch_related=["items"])
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert ctx.dst_optimizer_plan is plan


def test_stash_on_read_only_mapping_is_silent():
    """B5: a read-only ``MappingProxyType`` context must not abort the resolver chain.

    Pins the Medium fix from rev-optimizer__extension.md: ``setattr`` on a
    ``MappingProxyType`` raises ``TypeError`` (not ``AttributeError``), and
    ``__setitem__`` then raises ``TypeError`` again. Both must be swallowed
    so the optimizer's introspection-stash failure never crashes the
    request.
    """
    from types import MappingProxyType

    from django_strawberry_framework.optimizer.extension import _stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    ctx = MappingProxyType({})
    plan = OptimizationPlan(prefetch_related=["items"])
    # Should not raise.
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert "dst_optimizer_plan" not in ctx


def test_stash_falls_back_to_setitem_on_typeerror():
    """B5: a ``dict`` subclass is still stashed through ``__setitem__``.

    Dict-like context objects take the mapping branch before attribute
    writes, so a subclass with hostile attribute assignment still stores
    the optimizer plan where ``get_context_value`` will read it.
    """
    from django_strawberry_framework.optimizer.extension import _stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    class TypeErrorOnSetattr(dict):
        def __setattr__(self, _key: str, _value: object) -> None:
            raise TypeError("read-only attribute access")

    ctx = TypeErrorOnSetattr()
    plan = OptimizationPlan(prefetch_related=["items"])
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert ctx["dst_optimizer_plan"] is plan


def test_stash_on_immutable_dict_subclass_is_silent():
    """rev-optimizer__context: ``AttributeError`` from a frozen ``dict`` subclass is silently skipped.

    Django's ``QueryDict`` is a ``dict`` subclass that raises
    ``AttributeError("This QueryDict instance is immutable")`` from
    ``__setitem__`` when locked. The dict-first dispatch in
    ``stash_on_context`` routes subclasses through the mapping write
    path, so the trailing ``except`` must catch ``AttributeError`` in
    addition to ``TypeError`` — otherwise an immutable-``QueryDict``
    context would crash the resolver chain instead of being silently
    skipped, contradicting the docstring contract ("Frozen contexts ...
    raise on assignment; those stashes are silently skipped").
    """
    from django_strawberry_framework.optimizer._context import stash_on_context
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    class ImmutableDictSubclass(dict):
        def __setitem__(self, _key: str, _value: object) -> None:
            raise AttributeError("this dict is immutable")

    ctx = ImmutableDictSubclass()
    plan = OptimizationPlan(prefetch_related=["items"])
    stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert "dst_optimizer_plan" not in ctx


def test_stash_does_not_swallow_unexpected_exceptions_from_setitem():
    """rev-optimizer__context: keep the mapping-write ``except`` narrow.

    Read-only mapping failures are intentionally limited to ``TypeError``
    and ``AttributeError``. A guarded mapping that raises a different
    exception from ``__setitem__`` must surface the error rather than
    silently losing the optimizer stash.
    """
    from django_strawberry_framework.optimizer._context import stash_on_context

    class GuardedMapping(dict):
        def __setattr__(self, _key: str, _value: object) -> None:
            raise TypeError("no attribute writes")

        def __setitem__(self, _key: str, _value: object) -> None:
            raise RuntimeError("guarded write rejected")

    ctx = GuardedMapping()
    with pytest.raises(RuntimeError, match="guarded write rejected"):
        stash_on_context(ctx, "dst_optimizer_plan", object())


@pytest.mark.django_db
def test_empty_plan_still_stashed():
    """B5/O5: even when no relations are selected, the scalar-only plan is stashed."""
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

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    assert result.errors is None
    plan = getattr(ctx, "dst_optimizer_plan", None)
    assert plan is not None
    assert plan.only_fields == ("name",)
    assert plan.select_related == ()
    assert plan.prefetch_related == ()


# ---------------------------------------------------------------------------
# O5 — only() projection
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_applies_only_for_selected_scalars(django_assert_num_queries):
    """O5: selected scalar fields are collected into the stashed plan."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "description")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    with django_assert_num_queries(1):
        result = schema.execute_sync(
            "{ allCategories { name } }",
            context_value=ctx,
        )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.only_fields == ("name",)
    assert plan.select_related == ()
    assert plan.prefetch_related == ()


# ---------------------------------------------------------------------------
# O6 — get_queryset + Prefetch downgrade
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_optimizer_downgrades_select_related_for_custom_get_queryset(django_assert_num_queries):
    """O6: custom target ``get_queryset`` downgrades forward FK traversal to ``Prefetch``."""
    from django.db.models import Prefetch

    services.seed_data(1)
    calls = []

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            calls.append(info)
            return queryset

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()

    with django_assert_num_queries(2):
        result = schema.execute_sync(
            "{ allItems { name category { name } } }",
            context_value=ctx,
        )
    assert result.errors is None
    assert calls
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert "category_id" in plan.only_fields
    assert "category__name" not in plan.only_fields
    assert plan.cacheable is False
    assert ext.cache_info().size == 0
    assert len(plan.prefetch_related) == 1
    assert isinstance(plan.prefetch_related[0], Prefetch)
    assert plan.prefetch_related[0].prefetch_to == "category"


@pytest.mark.django_db
def test_optimizer_does_not_cache_custom_get_queryset_prefetch_plans():
    """O6: request-dependent ``Prefetch`` querysets are rebuilt instead of cached."""
    services.seed_data(1)
    calls = []

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            calls.append(info)
            return queryset

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    query = "{ allItems { name category { name } } }"

    assert schema.execute_sync(query).errors is None
    assert schema.execute_sync(query).errors is None

    assert len(calls) == 2
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 0


def test_plan_relation_returns_prefetch_for_custom_get_queryset():
    """O6: the extension exposes the relation planner entry point."""

    field = Item._meta.get_field("category")
    info = SimpleNamespace()

    class FilteredCategoryType:
        @classmethod
        def has_custom_get_queryset(cls):
            return True

        @classmethod
        def get_queryset(cls, queryset, passed_info, **kwargs):
            assert passed_info is info
            return queryset

    kind, reason = DjangoOptimizerExtension().plan_relation(field, FilteredCategoryType, info)
    assert kind == "prefetch"
    assert reason == "custom_get_queryset"


# ---------------------------------------------------------------------------
# B8: queryset optimization diffing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_b8_consumer_select_related_does_not_mutate_cached_plan():
    """B8: a consumer's pre-applied ``select_related`` must not mutate B1's cached plan."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.select_related("category")

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])

    # First request warms the plan cache. The plan is stashed pre-diff.
    ctx1 = SimpleNamespace()
    result1 = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx1,
    )
    assert result1.errors is None
    cached_plan = ctx1.dst_optimizer_plan
    assert cached_plan.select_related == ("category",)
    assert ext.cache_info().hits == 0
    assert ext.cache_info().misses == 1

    # Second request hits the cache. The cached plan must still carry
    # ["category"] — the diff must not have mutated it during request 1.
    ctx2 = SimpleNamespace()
    result2 = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx2,
    )
    assert result2.errors is None
    assert ctx2.dst_optimizer_plan is cached_plan
    assert cached_plan.select_related == ("category",)
    assert ext.cache_info().hits == 1


@pytest.mark.django_db
def test_b8_consumer_prefetch_object_suppresses_optimizer_entry():
    """B8: a consumer ``Prefetch("items", queryset=Item.objects.all())`` keeps its slot."""
    from django.db.models import Prefetch

    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    consumer_pf = Prefetch("items", queryset=Item.objects.all())
    captured: list[object] = []

    class _CaptureExt(DjangoOptimizerExtension):
        def _optimize(self, result, info):
            optimized = super()._optimize(result, info)
            captured.append(optimized)
            return optimized

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.prefetch_related(consumer_pf)

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[_CaptureExt()])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allCategories { name items { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    # Stashed plan still records the optimizer's intended ``items``
    # entry (B5 stashes the pre-diff plan).
    plan = ctx.dst_optimizer_plan
    assert [getattr(entry, "prefetch_to", entry) for entry in plan.prefetch_related] == ["items"]
    # The queryset that came out of ``_optimize`` carries exactly the
    # consumer's ``Prefetch`` — the optimizer entry was diffed away.
    optimized_qs = captured[0]
    lookups = optimized_qs._prefetch_related_lookups
    assert lookups == (consumer_pf,)


@pytest.mark.django_db
def test_b8_consumer_descendant_prefetch_does_not_raise(django_assert_num_queries):
    """B8 P1: consumer ``prefetch_related("items__entries")`` must not collide with the optimizer."""
    services.seed_data(1)

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
            fields = ("id", "name", "entries")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.prefetch_related("items__entries")

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    # Query must succeed instead of raising ``'items' lookup was already
    # seen with a different queryset``.
    result = schema.execute_sync(
        "{ allCategories { name items { name entries { value } } } }",
    )
    assert result.errors is None
    assert result.data["allCategories"]


@pytest.mark.django_db
def test_b8_consumer_exact_plus_descendant_prefetch_does_not_raise():
    """B8 P1 follow-up: ``prefetch_related("items", "items__entries")`` must not collide."""
    services.seed_data(1)

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "entries")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.prefetch_related("items", "items__entries")

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    result = schema.execute_sync(
        "{ allCategories { name items { name entries { value } } } }",
    )
    assert result.errors is None
    assert result.data["allCategories"]


@pytest.mark.django_db
def test_b8_consumer_plain_string_upgraded_to_optimizer_prefetch():
    """B8 P1: a consumer's plain ``"items"`` string is replaced by the optimizer's nested ``Prefetch``."""
    from django.db.models import Prefetch

    services.seed_data(1)

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "entries")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    captured: list[object] = []

    class _CaptureExt(DjangoOptimizerExtension):
        def _optimize(self, result, info):
            optimized = super()._optimize(result, info)
            captured.append(optimized)
            return optimized

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryType]:
            return Category.objects.prefetch_related("items")

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[_CaptureExt()])
    result = schema.execute_sync(
        "{ allCategories { name items { name entries { value } } } }",
    )
    assert result.errors is None
    optimized_qs = captured[0]
    lookups = optimized_qs._prefetch_related_lookups
    # Exactly one ``items`` lookup — the optimizer's ``Prefetch`` —
    # carrying the nested ``entries`` chain. The consumer's plain
    # ``"items"`` string was stripped.
    assert len(lookups) == 1
    items_pf = lookups[0]
    assert isinstance(items_pf, Prefetch)
    assert items_pf.prefetch_to == "items"
    nested = items_pf.queryset._prefetch_related_lookups
    assert any(getattr(entry, "prefetch_to", entry) == "entries" for entry in nested)


# ---------------------------------------------------------------------------
# Construction surface — unknown kwargs raise loudly
# ---------------------------------------------------------------------------


def test_extension_rejects_unknown_kwargs_at_construction():
    """Misspelled config (e.g. ``strict=`` instead of ``strictness=``) raises TypeError."""
    with pytest.raises(TypeError):
        DjangoOptimizerExtension(strict=True)  # type: ignore[call-arg]


def test_extension_accepts_strawberry_execution_context_kwarg():
    """Strawberry instantiates extension *classes* with ``execution_context=...``.

    ``strawberry.Schema(..., extensions=[DjangoOptimizerExtension])`` (note:
    class, not instance) calls ``ext(execution_context=None)`` internally.
    The extension must accept that keyword without ``TypeError``.
    """
    ext = DjangoOptimizerExtension(execution_context=None)
    assert ext.strictness == "off"


# ---------------------------------------------------------------------------
# hint_is_skip — centralised hint-shape dispatch
# ---------------------------------------------------------------------------


def test_hint_is_skip_handles_sentinel_record_and_unknown_shapes():
    """``hint_is_skip`` returns the documented bool for every supported shape."""
    from django_strawberry_framework.optimizer.hints import OptimizerHint, hint_is_skip

    assert hint_is_skip(None) is False
    assert hint_is_skip(OptimizerHint.SKIP) is True
    assert hint_is_skip(OptimizerHint(skip=True)) is True
    assert hint_is_skip(OptimizerHint.select_related()) is False
    # Unknown shape with no ``.skip`` attribute must not raise — the
    # schema audit's "never raises" contract depends on this.
    assert hint_is_skip(object()) is False


# ---------------------------------------------------------------------------
# Slice 4 — H2 plan-cache origin separation + H3 multi-type audit dedupe
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model():
    """H2: a primary-return resolver and a secondary-return resolver do not collide.

    Two root fields on the same schema return ``list[ItemType]`` and
    ``list[AdminItemType]`` respectively. Both target ``Item`` but
    carry different origin types, so the plan cache must hold two
    distinct entries. Without the origin component of the cache key
    the two queries would share one cached plan keyed by ``Item``
    alone.
    """
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    ext = DjangoOptimizerExtension()

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return Item.objects.all()

        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return Item.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[ext])
    # Run the same selection through both root fields. Same response shape
    # so doc_key + relevant_vars + target_model agree; only response_path
    # and origin differ. With the new cache key both fields produce
    # distinct entries.
    schema.execute_sync("{ allItems { name } }")
    schema.execute_sync("{ allAdminItems { name } }")
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


def test_schema_audit_warns_on_relation_field_exposed_only_on_secondary_type():
    """H3: a relation field only present on a secondary still surfaces a warning.

    ``ItemType`` (primary) excludes ``category``; ``AdminItemType``
    (secondary) includes ``category`` with an unregistered target. The
    audit must walk every reachable type so the secondary's relation is
    audited and the missing-target warning is produced. Switching to a
    primary-only iterator would silently drop this warning.
    """

    # Register CategoryType first so AdminItemType.category can resolve
    # during __init_subclass__, then clear it before check_schema runs.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query, types=[ItemType])
    # Clear Category's registration so the audit sees the gap.
    registry.unregister(CategoryType)

    warnings = DjangoOptimizerExtension.check_schema(schema)
    # Item.category is the secondary-only relation; the audit must surface it.
    assert any("Item.category" in w and "no registered target" in w for w in warnings)


def test_schema_audit_dedupes_when_same_relation_field_visited_via_multiple_types():
    """H3: identical (source_model, field_name) warnings collapse to one.

    Both ``ItemType`` (primary) and ``AdminItemType`` (secondary) expose
    ``category`` whose target ``Category`` has no registered
    ``DjangoType``. Without dedupe, ``registry.iter_types()`` (one
    yield per registered type) would produce two identical warnings.
    """

    # Register CategoryType so the type declarations succeed, then drop
    # its registration before check_schema runs.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    registry.unregister(CategoryType)

    warnings = DjangoOptimizerExtension.check_schema(schema)
    item_category_warnings = [w for w in warnings if "Item.category" in w]
    assert len(item_category_warnings) == 1


def test_model_for_type_reverse_lookup_works_for_secondary_type():
    """Secondary types remain discoverable for the optimizer's reverse lookup.

    Both ``ItemType`` and ``AdminItemType`` are registered against
    ``Item``; ``registry.model_for_type`` returns the same ``Item`` for
    either origin. The optimizer's ``_resolve_model_from_return_type``
    composition surfaces both legs of the pair: ``origin`` is the
    secondary, ``model`` is the underlying Django model.
    """
    from graphql import GraphQLList, GraphQLNonNull

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.model_for_type(AdminItemType) is Item

    @strawberry.type
    class Query:
        @strawberry.field
        def all_admin_items(self) -> list[AdminItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query, types=[ItemType])
    inner = schema._schema.type_map["AdminItemType"]
    wrapped = GraphQLNonNull(GraphQLList(GraphQLNonNull(inner)))
    info = SimpleNamespace(return_type=wrapped, schema=schema._schema)
    resolved = _resolve_model_from_return_type(info)
    assert resolved is not None
    assert resolved.origin is AdminItemType
    assert resolved.model is Item
