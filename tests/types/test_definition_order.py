"""Acceptance tests for definition-order-independent DjangoType relations."""

import pytest
import strawberry
from apps.library.models import Book, Genre, MembershipCard, Patron, Shelf
from apps.products.models import Category, Entry, Item, Property

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def _strawberry_field(type_cls: type, field_name: str):
    """Return a finalized Strawberry field by Python name.

    Tests intentionally inspect Strawberry internals such as
    ``base_resolver.wrapped_func`` to pin resolver attachment; if Strawberry
    changes this field shape, these tests should fail loudly.
    """
    return next(
        field for field in type_cls.__strawberry_definition__.fields if field.python_name == field_name
    )


def test_reverse_fk_resolves_when_parent_declared_before_child():
    """Category.items starts pending and resolves to list[ItemType] at finalization."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    assert CategoryType.__annotations__["items"].__name__ == "PendingRelationAnnotation"
    assert ItemType.__annotations__["category"] is CategoryType

    finalize_django_types()

    assert CategoryType.__annotations__["items"] == list[ItemType]
    assert ItemType.__annotations__["category"] is CategoryType


def test_reverse_fk_resolves_when_child_declared_before_parent():
    """Item.category starts pending and resolves once CategoryType exists."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    assert ItemType.__annotations__["category"].__name__ == "PendingRelationAnnotation"
    assert CategoryType.__annotations__["items"] == list[ItemType]

    finalize_django_types()

    assert ItemType.__annotations__["category"] is CategoryType
    assert CategoryType.__annotations__["items"] == list[ItemType]


def test_one_to_one_forward_and_reverse_relations_resolve():
    """Forward OneToOne and reverse OneToOne get concrete final annotations."""

    class MembershipCardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode", "patron")

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name", "card")

    finalize_django_types()

    assert MembershipCardType.__annotations__["patron"] is PatronType
    assert PatronType.__annotations__["card"] == (MembershipCardType | None)


def test_many_to_many_forward_and_reverse_relations_resolve():
    """Forward/reverse M2M and an adjacent FK resolve across declaration order."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf", "genres")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name", "books")

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code", "books")

    finalize_django_types()

    assert BookType.__annotations__["shelf"] is ShelfType
    assert BookType.__annotations__["genres"] == list[GenreType]
    assert GenreType.__annotations__["books"] == list[BookType]
    assert ShelfType.__annotations__["books"] == list[BookType]


def test_multi_cycle_finalizes_every_edge():
    """A fakeshop multi-cycle resolves every pending FK and reverse FK edge."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items", "properties")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category", "entries")

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = ("id", "value", "item", "property")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name", "category", "entries")

    finalize_django_types()

    assert CategoryType.__annotations__["items"] == list[ItemType]
    assert CategoryType.__annotations__["properties"] == list[PropertyType]
    assert ItemType.__annotations__["category"] is CategoryType
    assert ItemType.__annotations__["entries"] == list[EntryType]
    assert EntryType.__annotations__["item"] is ItemType
    assert EntryType.__annotations__["property"] is PropertyType
    assert PropertyType.__annotations__["category"] is CategoryType
    assert PropertyType.__annotations__["entries"] == list[EntryType]


def test_unresolved_target_raises_with_source_field_and_target():
    """Finalization fails loudly when a selected relation target was never registered."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "Cannot finalize Django types" in msg
    assert "Item.category -> Category" in msg
    assert "no registered DjangoType" in msg


def test_annotation_only_relation_override_keeps_generated_resolver():
    """Annotation-only overrides keep the generated many-side resolver."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        items: list[ItemType]

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_authored_fields == frozenset({"items"})
    assert definition.consumer_annotated_relation_fields == frozenset({"items"})
    assert definition.consumer_assigned_relation_fields == frozenset()

    finalize_django_types()

    items_field = _strawberry_field(CategoryType, "items")
    assert items_field.base_resolver is not None
    assert items_field.base_resolver.wrapped_func.__name__ == "resolve_items"


def test_assigned_relation_field_override_keeps_consumer_resolver():
    """Assigned Strawberry relation fields suppress generated relation resolvers."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        @strawberry.field
        def items(self) -> list[ItemType]:
            return []

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_authored_fields == frozenset({"items"})
    assert definition.consumer_annotated_relation_fields == frozenset()
    assert definition.consumer_assigned_relation_fields == frozenset({"items"})

    finalize_django_types()

    items_field = _strawberry_field(CategoryType, "items")
    assert items_field.base_resolver is not None
    assert items_field.base_resolver.wrapped_func.__qualname__.endswith("CategoryType.items")


def test_decorator_relation_field_override_routes_schema_query_through_consumer_resolver():
    """A decorator override survives finalization and executes inside a schema query."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        @strawberry.field
        def items(self) -> list[ItemType]:
            return [Item(id=1, name="manual")]

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return [Category(id=1, name="category")]

    finalize_django_types()
    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ categories { items { name } } }")

    assert result.errors is None
    assert result.data == {"categories": [{"items": [{"name": "manual"}]}]}


def test_relation_field_class_attribute_shadowing_raises():
    """Unsupported class attributes cannot silently shadow relation fields."""
    with pytest.raises(ConfigurationError, match="shadows a Django relation field"):

        class CategoryType(DjangoType):
            items = None

            class Meta:
                model = Category
                fields = ("id", "name", "items")


def test_same_module_string_forward_reference_annotation_survives_finalization():
    """A same-module string relation override is resolved by Strawberry after finalization."""

    class StringItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    globals()["StringItemType"] = StringItemType
    try:

        class StringCategoryType(DjangoType):
            items: list["StringItemType"]

            class Meta:
                model = Category
                fields = ("id", "name", "items")

        globals()["StringCategoryType"] = StringCategoryType
        finalize_django_types()

        items_field = _strawberry_field(StringCategoryType, "items")
        assert items_field.base_resolver is not None
        assert items_field.base_resolver.wrapped_func.__name__ == "resolve_items"
    finally:
        globals().pop("StringCategoryType", None)
        globals().pop("StringItemType", None)
