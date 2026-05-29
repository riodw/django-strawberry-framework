"""Optimizer invariants for Relay-declared ``DjangoType`` classes.

Pins Decision 7 (spec #"Decision 7: optimizer and projection invariants"): when a Relay-declared type selects
``id`` the optimizer's ``only()`` projection must still include the
concrete pk attname; ``_resolve_id_default`` must read from the loaded
``__dict__`` cache without triggering a lazy load; and relation traversal
across Relay-declared targets must remain unchanged.
"""

from types import SimpleNamespace

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from django.db import connection, models
from django.test.utils import CaptureQueriesContext
from strawberry import relay

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types
from django_strawberry_framework.registry import registry


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
            interfaces = (relay.Node,)

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
            interfaces = (relay.Node,)

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
            interfaces = (relay.Node,)

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
            interfaces = (relay.Node,)

    finalize_django_types()

    row = Category.objects.only("id", "name").first()
    assert row is not None
    expected = str(row.id)
    with CaptureQueriesContext(connection) as captured:
        assert CategoryNode.resolve_id(row, info=None) == expected
    # The dict-cache hit on the loaded pk avoids any additional query.
    assert len(captured) == 0


@pytest.mark.django_db(transaction=True)
def test_relay_id_with_custom_pk_attname_avoids_lazy_load(django_assert_num_queries):
    """End-to-end regression for ``docs/feedback.md`` § custom-pk Relay projection.

    A Relay-declared ``DjangoType`` backed by a model whose pk attname is
    not ``"id"`` must produce exactly one query for ``{ id name }`` —
    the walker resolves the configured ``id_attr``, projects the real
    pk column into ``only()``, and ``_resolve_id_default`` reads the
    loaded value from ``root.__dict__`` instead of falling back to
    ``getattr`` and triggering a per-row pk fetch (Decision 7).

    Uses the ``managed=False`` + manual ``schema_editor`` pattern from
    ``test_walker.py::test_plan_elides_forward_fk_when_target_pk_is_not_named_id``
    so the model exists for ``_meta.pk.attname`` introspection AND the
    table exists for a real query — no fakeshop model addition needed.
    """

    class CustomPKItem(models.Model):
        uuid = models.CharField(max_length=32, primary_key=True)
        name = models.CharField(max_length=32)

        class Meta:
            app_label = "tests"
            managed = False

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(CustomPKItem)
    try:
        CustomPKItem.objects.create(uuid="abc-123", name="widget")

        class CustomPKItemNode(DjangoType):
            class Meta:
                model = CustomPKItem
                # ``Meta.fields`` lists Django field names; the model's pk
                # is ``uuid`` (not ``id``), so the user must include
                # ``"uuid"`` here. Slice 3's id-suppression then strips
                # the synthesized ``uuid`` annotation so the schema
                # surface is ``id: GlobalID!`` (from ``relay.Node``)
                # plus ``name``, without leaking ``uuid: str!``.
                fields = ("uuid", "name")
                interfaces = (relay.Node,)

        @strawberry.type
        class Query:
            @strawberry.field
            def all_items(self) -> list[CustomPKItemNode]:
                return CustomPKItem.objects.all()

        finalize_django_types()
        schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
        ctx = SimpleNamespace()
        with django_assert_num_queries(1):
            result = schema.execute_sync("{ allItems { id name } }", context_value=ctx)

        assert result.errors is None
        plan = ctx.dst_optimizer_plan
        # The walker projected the real pk attname (``uuid``), not the
        # GraphQL literal ``id`` — this is the fix from
        # ``docs/feedback.md`` § High "Optimizer misses projecting custom
        # primary keys for Relay nodes".
        assert "uuid" in plan.only_fields
        assert "id" not in plan.only_fields
        assert result.data == {
            "allItems": [{"id": result.data["allItems"][0]["id"], "name": "widget"}],
        }
        # The Relay GlobalID round-trip carries the custom-pk value.
        node_id = relay.GlobalID.from_id(result.data["allItems"][0]["id"])
        assert node_id.type_name == "CustomPKItemNode"
        assert node_id.node_id == "abc-123"
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(CustomPKItem)
