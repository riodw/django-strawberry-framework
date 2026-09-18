"""Optimizer tests for Relay GlobalID projection when the pk attname is not ``id``.

The default-pk half is live at
``examples/fakeshop/test_query/test_products_visibility_api.py::test_relay_id_only_connection_page_costs_one_query_and_emits_decodable_ids``
and
``examples/fakeshop/test_query/test_products_visibility_api.py::test_relay_id_and_name_selection_is_clean_under_strictness_raise_over_http``.
Every fakeshop model uses the default ``id`` pk, so no live query can put a
custom pk attname in front of the walker (rung 1 refused: retargeting a shipped
pk would change every GlobalID). The ``managed=False`` + ``schema_editor``
pattern stands in.
"""

from types import SimpleNamespace

import pytest
import strawberry
from django.db import connection, models
from strawberry import relay

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


@pytest.mark.django_db(transaction=True)
def test_relay_id_with_custom_pk_attname_avoids_lazy_load(django_assert_num_queries):
    """A Relay type whose pk attname is not ``id`` still answers ``{ id name }`` in one query.

    The walker resolves the configured ``id_attr``, projects the real pk column
    into ``only()``, and ``_resolve_id_default`` reads the loaded value from
    ``root.__dict__`` instead of falling back to ``getattr`` (spec-015 Decision
    7).
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
                fields = ("uuid", "name")
                interfaces = (relay.Node,)

        @strawberry.type
        class Query:
            @strawberry.field
            def all_items(self) -> list[CustomPKItemNode]:
                return CustomPKItem.objects.all()

        finalize_django_types()
        ext = DjangoOptimizerExtension()
        schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
        ctx = SimpleNamespace()
        with django_assert_num_queries(1):
            result = schema.execute_sync("{ allItems { id name } }", context_value=ctx)

        assert result.errors is None
        plan = ctx.dst_optimizer_plan
        assert "uuid" in plan.only_fields
        assert "id" not in plan.only_fields
        assert result.data == {
            "allItems": [{"id": result.data["allItems"][0]["id"], "name": "widget"}],
        }
        node_id = relay.GlobalID.from_id(result.data["allItems"][0]["id"])
        assert node_id.type_name == CustomPKItem._meta.label_lower
        assert node_id.node_id == "abc-123"
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(CustomPKItem)
