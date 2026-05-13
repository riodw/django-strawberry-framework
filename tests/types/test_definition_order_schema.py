"""Schema-level tests for definition-order-independent DjangoType finalization."""

import pytest
import strawberry
from apps.library.models import Book, Genre
from apps.products import services
from apps.products.models import Category, Item

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.registry import registry
from tests._relay_bypass import stage_relay_definition


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


@pytest.mark.django_db
def test_schema_executes_nested_query_when_query_declared_before_finalization():
    """Query decoration can happen before finalization as long as schema construction waits."""
    services.seed_data(1)

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return list(Item.objects.order_by("id")[:3])

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ allItems { name category { name } } }")

    assert result.errors is None
    assert len(result.data["allItems"]) == 3
    assert all(item["category"]["name"] for item in result.data["allItems"])


def test_m2m_schema_shape_builds_with_real_library_models():
    """The real library app provides schema-shape coverage for M2M fields."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "genres")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_books(self) -> list[BookType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    genres_field = schema._schema.type_map["BookType"].fields["genres"]
    assert str(genres_field.type) == "[GenreType!]!"


def test_manual_strawberry_type_before_finalization_surfaces_sentinel_repr():
    """If Strawberry sees an unresolved relation sentinel, the error names the finalizer."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    strawberry.type(ItemType)

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    with pytest.raises(TypeError) as exc_info:
        strawberry.Schema(query=Query)

    msg = str(exc_info.value)
    assert "Unexpected type" in msg
    assert "finalize_django_types()" in msg


def test_relay_declared_type_emits_node_interface_and_global_id():
    """A Relay-declared ``DjangoType`` exposes ``id: GlobalID!`` via the ``Node`` interface."""

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    stage_relay_definition(CategoryNode)

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryNode]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    gql_type = schema._schema.type_map["CategoryNode"]
    interface_names = {iface.name for iface in gql_type.interfaces}
    assert "Node" in interface_names
    id_field = gql_type.fields["id"]
    assert str(id_field.type) == "ID!"


def test_mixed_relay_and_non_relay_types_introspect_cleanly():
    """A non-Relay ``DjangoType`` does NOT implement ``Node`` (no interface bleed)."""

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    stage_relay_definition(CategoryNode)

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[CategoryNode]:
            return []

        @strawberry.field
        def all_items(self) -> list[ItemType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    relay_gql_type = schema._schema.type_map["CategoryNode"]
    plain_gql_type = schema._schema.type_map["ItemType"]
    relay_interfaces = {iface.name for iface in relay_gql_type.interfaces}
    plain_interfaces = {iface.name for iface in plain_gql_type.interfaces}
    assert "Node" in relay_interfaces
    assert "Node" not in plain_interfaces
    # The plain type's id is still the synthesized ``Int!`` field, not a GlobalID.
    assert str(plain_gql_type.fields["id"].type) == "Int!"
