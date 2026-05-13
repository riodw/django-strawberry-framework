"""Optimizer invariants for Relay-declared ``DjangoType`` classes (Slice 4).

Pins Decision 7 (spec lines 352-361): when a Relay-declared type selects
``id`` the optimizer's ``only()`` projection must still include the
concrete pk attname; ``_resolve_id_default`` must read from the loaded
``__dict__`` cache without triggering a lazy load; and relation traversal
across Relay-declared targets must remain unchanged.

Slice 4 cannot declare ``Meta.interfaces = (relay.Node,)`` end-to-end —
``"interfaces"`` is still in ``DEFERRED_META_KEYS`` until Slice 5
promotes it — so these tests stage the interfaces tuple directly on
``DjangoTypeDefinition.interfaces`` after registration (and strip the
synthesized ``id`` annotation Slice 3 would have stripped).
"""

from types import SimpleNamespace

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from django.db import connection
from django.test.utils import CaptureQueriesContext

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types
from django_strawberry_framework.registry import registry
from tests._relay_bypass import stage_relay_definition


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


@pytest.mark.django_db
def test_relay_id_only_projection_includes_pk_attname(django_assert_num_queries):
    """Selecting Relay ``id`` keeps the concrete pk attname in the optimizer's ``only()``."""
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    stage_relay_definition(CategoryNode)

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryNode]:
            return Category.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    with django_assert_num_queries(1):
        result = schema.execute_sync("{ allCategories { id } }", context_value=ctx)
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    assert "id" in plan.only_fields


@pytest.mark.django_db
def test_relay_id_does_not_trigger_lazy_load():
    """Selecting ``{ id name }`` on a Relay-declared type is clean under ``strictness="raise"``."""
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    stage_relay_definition(CategoryNode)

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryNode]:
            return Category.objects.all()

    finalize_django_types()
    schema = strawberry.Schema(
        query=Query,
        extensions=[DjangoOptimizerExtension(strictness="raise")],
    )
    result = schema.execute_sync("{ allCategories { id name } }")
    assert result.errors is None


@pytest.mark.django_db
def test_relay_target_relation_planning_unchanged(django_assert_num_queries):
    """Forward FK traversal whose target is a Relay-declared type still plans ``select_related``."""
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    stage_relay_definition(CategoryNode)

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
            "{ allItems { name category { name } } }",
            context_value=ctx,
        )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    # ``select_related`` plans the forward FK even though the target is Relay-declared.
    assert "category" in plan.select_related


@pytest.mark.django_db
def test_relay_resolve_id_uses_loaded_pk():
    """``CategoryNode.resolve_id`` reads the loaded pk via ``__dict__`` (no extra query)."""
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    stage_relay_definition(CategoryNode)
    finalize_django_types()

    row = Category.objects.only("id", "name").first()
    assert row is not None
    expected = str(row.id)
    with CaptureQueriesContext(connection) as captured:
        assert CategoryNode.resolve_id(row, info=None) == expected
    # The dict-cache hit on the loaded pk avoids any additional query.
    assert len(captured) == 0
