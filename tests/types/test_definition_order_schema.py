"""Schema-level tests for definition-order-independent DjangoType finalization."""

import pytest
import strawberry
from fakeshop.products import services
from fakeshop.products.models import Category, Item

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.registry import registry
from tests.fixtures.cardinality_models import Book, Tag


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


def test_m2m_schema_shape_builds_without_database_tables():
    """Unmanaged M2M fixtures are schema-shape-only in the foundation slice."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "tags")

    class TagType(DjangoType):
        class Meta:
            model = Tag
            fields = ("id", "name")

    @strawberry.type
    class Query:
        @strawberry.field
        def all_books(self) -> list[BookType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    tags_field = schema._schema.type_map["BookType"].fields["tags"]
    assert str(tags_field.type) == "[TagType!]!"


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
