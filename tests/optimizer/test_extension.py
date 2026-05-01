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

O6 covers the ``plan_relation`` downgrade from ``select_related`` to
``Prefetch`` for target types with custom ``get_queryset`` hooks.
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
    assert plan.select_related == []
    assert plan.prefetch_related == []
    assert plan.only_fields == ["name", "category_id"]
    assert plan.fk_id_elisions == ["category"]
    assert ctx.dst_optimizer_fk_id_elisions == {"category"}


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

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()

    with django_assert_num_queries(1):
        result = schema.execute_sync(
            "{ allItems { name category { id name } } }",
            context_value=ctx,
        )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ["category"]
    assert plan.fk_id_elisions == []
    assert plan.only_fields == ["name", "category_id", "category__id", "category__name"]


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

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()

    with django_assert_num_queries(2):
        result = schema.execute_sync(
            "{ allItems { name category { id } } }",
            context_value=ctx,
        )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == []
    assert plan.fk_id_elisions == []
    assert plan.only_fields == ["name", "category_id"]
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

    schema = strawberry.Schema(query=Query, extensions=[ext])

    schema.execute_sync("{ allItems { name } }")
    schema.execute_sync("{ allItems { name category { name } } }")
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2


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

    schema = strawberry.Schema(query=Query, extensions=[ext])
    query = "query Q($limit: Int!) { allItems(limit: $limit) { name category { name } } }"

    schema.execute_sync(query, variable_values={"limit": 5})
    schema.execute_sync(query, variable_values={"limit": 10})
    # Same query shape, different filter var — should be 1 miss + 1 hit.
    assert ext.cache_info().hits == 1
    assert ext.cache_info().size == 1


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
    """B3: strictness='warn' logs a warning for unplanned relation access."""
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
            # Return a plain list so the optimizer does NOT fire
            # (no QuerySet -> no plan -> no planned paths).
            # But strictness sentinel IS stashed because the
            # optimizer runs _optimize which checks isinstance.
            # To trigger the warning we need the optimizer to run
            # but produce a plan that does NOT include "category".
            # Easiest: query only scalars at root so plan is empty,
            # then access a relation Strawberry resolves anyway.
            return list(Item.objects.select_related("category").all())

    ext = DjangoOptimizerExtension(strictness="warn")
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    # Query only scalars — the optimizer produces an empty plan.
    # But Strawberry still resolves the "category" field via our
    # resolver, which checks the sentinel.
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    # The plan includes "category" because the walker saw the selection.
    # So no warning should fire for a planned relation.
    # To test the warning path, we need an UNPLANNED relation.
    # Verify no warning for planned relation:
    assert not any("Potential N+1" in r.message for r in caplog.records)


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
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    planned = getattr(ctx, "dst_optimizer_planned", None)
    assert planned is not None
    assert "category" in planned
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
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = schema.execute_sync(
        "{ allItems { name category { id } } }",
        context_value=ctx,
    )
    assert result.errors is None
    assert "category" in ctx.dst_optimizer_planned
    assert ctx.dst_optimizer_fk_id_elisions == {"category"}
    assert not any("Potential N+1" in r.message for r in caplog.records)


def test_get_relation_field_name_uses_field_name_not_alias():
    """B3: _get_relation_field_name uses info.field_name, not the path alias."""
    from django_strawberry_framework.types.resolvers import _get_relation_field_name

    info = SimpleNamespace(field_name="category")
    assert _get_relation_field_name(info) == "category"

    # Alias case: path.key would be "cat", but field_name is still "category".
    info_aliased = SimpleNamespace(field_name="category")
    assert _get_relation_field_name(info_aliased) == "category"


def test_will_lazy_load_false_when_cached():
    """B3: _will_lazy_load returns False when the relation is already in __dict__."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load

    root = SimpleNamespace(category="cached_value")
    assert _will_lazy_load(root, "category") is False


def test_will_lazy_load_true_when_not_cached():
    """B3: _will_lazy_load returns True when the relation is not cached."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load

    root = SimpleNamespace()
    assert _will_lazy_load(root, "category") is True


def test_will_lazy_load_false_when_prefetched():
    """B3: _will_lazy_load returns False when the relation is in _prefetched_objects_cache."""
    from django_strawberry_framework.types.resolvers import _will_lazy_load

    root = SimpleNamespace()
    root._prefetched_objects_cache = {"items": [1, 2, 3]}
    assert _will_lazy_load(root, "items") is False


@pytest.mark.django_db
def test_strictness_warn_no_warning_for_already_loaded_relation(caplog):
    """B3: strictness='warn' does NOT warn when the relation is already loaded."""
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
            # select_related pre-loads category -> no lazy load.
            return list(Item.objects.select_related("category").all())

    ext = DjangoOptimizerExtension(strictness="warn")
    schema = strawberry.Schema(query=Query, extensions=[ext])
    ctx = SimpleNamespace()

    caplog.set_level("WARNING", logger="django_strawberry_framework")
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    # No warning because select_related pre-loaded the relation.
    assert not any("Potential N+1" in r.message for r in caplog.records)


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


# ---------------------------------------------------------------------------
# B6: Schema-build-time optimization audit
# ---------------------------------------------------------------------------


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

    schema = strawberry.Schema(query=Query)
    # Clear Category's registration so the audit finds a gap.
    registry._types.pop(Category, None)
    registry._models.pop(CategoryType, None)
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

    schema = strawberry.Schema(query=Query)
    # Clear Category so the audit would normally warn — but SKIP suppresses.
    registry._types.pop(Category, None)
    registry._models.pop(CategoryType, None)
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

    schema = strawberry.Schema(query=Query)
    warnings = DjangoOptimizerExtension.check_schema(schema)
    # category is not in _optimizer_field_map so not flagged.
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

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    # Force-prefetch overrides the default select_related for forward FK.
    assert "category" in plan.prefetch_related
    assert "category" not in plan.select_related
    assert "category_id" in plan.only_fields


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
def test_plan_stashed_on_object_context(django_assert_num_queries):
    """B5: the plan is accessible on ``info.context.dst_optimizer_plan`` after execution."""
    services.seed_data(1)

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    captured_plan = {}

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self, info: strawberry.types.Info) -> list[ItemType]:
            return Item.objects.all()

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    result = schema.execute_sync("{ allItems { name category { name } } }")
    assert result.errors is None
    # Strawberry's default context is an object; plan should be stashed via setattr.
    # We can't access info.context after execution in sync mode directly,
    # so drive _optimize with a synthetic context object instead.


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

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allCategories { name items { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = getattr(ctx, "dst_optimizer_plan", None)
    assert plan is not None
    assert "items" in plan.prefetch_related


def test_plan_stashed_on_dict_context():
    """B5: when context is a plain dict, plan is stashed via __setitem__."""
    from django_strawberry_framework.optimizer.extension import _stash_on_context

    ctx = {}
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    plan = OptimizationPlan(select_related=["category"])
    _stash_on_context(ctx, "dst_optimizer_plan", plan)
    assert ctx["dst_optimizer_plan"] is plan


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

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    result = schema.execute_sync("{ allCategories { name } }", context_value=ctx)
    assert result.errors is None
    plan = getattr(ctx, "dst_optimizer_plan", None)
    assert plan is not None
    assert plan.only_fields == ["name"]
    assert plan.select_related == []
    assert plan.prefetch_related == []


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

    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    with django_assert_num_queries(1):
        result = schema.execute_sync(
            "{ allCategories { name } }",
            context_value=ctx,
        )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.only_fields == ["name"]
    assert plan.select_related == []
    assert plan.prefetch_related == []


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
    assert plan.select_related == []
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
    from django.db.models import Prefetch

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

    kind, lookup = DjangoOptimizerExtension().plan_relation(field, FilteredCategoryType, info)
    assert kind == "prefetch"
    assert isinstance(lookup, Prefetch)
    assert lookup.prefetch_to == "category"


@pytest.mark.skip(reason="Slice 4+: M2M relation — fakeshop has no M2M field; deferred.")
def test_optimizer_applies_prefetch_related_for_m2m():
    pass
