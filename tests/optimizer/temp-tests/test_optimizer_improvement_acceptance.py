"""Temporary acceptance probes for optimizer-improvement work.

These tests describe desired optimizer behavior from ``feedback2.md``. They are
intentionally parked under ``tests/optimizer/temp-tests/`` so a developer can
run them while implementing the optimizer changes without treating them as
settled package coverage yet.
"""

from types import SimpleNamespace

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Entry, Item
from graphql import parse
from strawberry import relay

from django_strawberry_framework import (
    DjangoConnectionField,
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import _connection_type_cache, _connection_type_for
from django_strawberry_framework.optimizer import extension as extension_module
from django_strawberry_framework.optimizer.plans import OptimizationPlan
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry_and_connection_cache():
    """Keep temporary dynamically declared DjangoTypes isolated per test."""
    registry.clear()
    _connection_type_cache.clear()
    yield
    registry.clear()
    _connection_type_cache.clear()


def _relay_node_type(name: str, model: type, fields: tuple[str, ...]) -> type:
    return type(
        name,
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": model,
                    "fields": fields,
                    "interfaces": (relay.Node,),
                    "name": name,
                },
            ),
        },
    )


def _connection_schema(
    target_type: type,
    optimizer: DjangoOptimizerExtension,
    *,
    field_name: str,
) -> strawberry.Schema:
    connection_type = _connection_type_for(target_type)
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {field_name: connection_type},
                field_name: DjangoConnectionField(target_type),
            },
        ),
    )
    finalize_django_types()
    return strawberry.Schema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


@pytest.mark.django_db
def test_connection_edges_node_forward_fk_selection_builds_node_plan():
    """A connection field should plan ``edges.node`` like an equivalent list field."""
    services.seed_data(2)
    _relay_node_type("TempConnectionCategoryNode", Category, ("id", "name"))
    item_node = _relay_node_type(
        "TempConnectionItemNode",
        Item,
        ("id", "name", "category"),
    )
    ext = DjangoOptimizerExtension()
    schema = _connection_schema(item_node, ext, field_name="items")
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ items { edges { node { name category { id name } } } } }",
        context_value=ctx,
    )

    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ("category",)
    assert plan.prefetch_related == ()
    assert plan.only_fields == (
        "name",
        "category_id",
        "category__id",
        "category__name",
    )


@pytest.mark.django_db
def test_connection_edges_node_many_relation_selection_builds_prefetch_plan():
    """A connection field should prefetch many-side relations selected on ``edges.node``."""
    services.seed_data(2)
    _relay_node_type("TempConnectionItemNode", Item, ("id", "name"))
    category_node = _relay_node_type(
        "TempConnectionCategoryWithItemsNode",
        Category,
        ("id", "name", "items"),
    )
    ext = DjangoOptimizerExtension()
    schema = _connection_schema(category_node, ext, field_name="categories")
    ctx = SimpleNamespace()

    result = schema.execute_sync(
        "{ categories { edges { node { name items { name } } } } }",
        context_value=ctx,
    )

    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert plan.select_related == ()
    assert [getattr(entry, "prefetch_to", entry) for entry in plan.prefetch_related] == ["items"]
    assert plan.only_fields == ("name",)


def _cache_info_for(root_field: str) -> SimpleNamespace:
    operation = parse(f"query {root_field} {{ {root_field} {{ name }} }}").definitions[0]
    return SimpleNamespace(
        operation=operation,
        fragments={},
        variable_values={},
        path=SimpleNamespace(key=root_field, prev=None),
    )


def test_plan_cache_hit_promotes_entry_before_eviction(monkeypatch):
    """A hot cache entry should survive the next eviction sweep under LRU semantics."""
    monkeypatch.setattr(extension_module, "_MAX_PLAN_CACHE_SIZE", 4)
    ext = DjangoOptimizerExtension()
    infos = [_cache_info_for(f"root{idx}") for idx in range(4)]
    keys = [DjangoOptimizerExtension._build_cache_key(info, Category, None) for info in infos]
    plans = [OptimizationPlan(only_fields=[f"field_{idx}"]).finalize() for idx in range(4)]
    ext._plan_cache = dict(zip(keys, plans, strict=True))

    assert ext._get_or_build_plan([], Category, infos[0], None) is plans[0]

    ext._get_or_build_plan([], Category, _cache_info_for("root4"), None)

    assert keys[0] in ext._plan_cache
    assert keys[1] not in ext._plan_cache


@pytest.mark.django_db
def test_dynamic_child_queryset_keeps_structural_plan_cache_entry():
    """Request-scoped child querysets should be hydrated per request without disabling the structural cache."""
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
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    query = "{ allCategories { items { entries { value } } } }"

    assert schema.execute_sync(query, context_value=SimpleNamespace()).errors is None
    assert schema.execute_sync(query, context_value=SimpleNamespace()).errors is None

    assert len(calls) == 2
    assert ext.cache_info().misses == 1
    assert ext.cache_info().hits == 1
    assert ext.cache_info().size == 1
