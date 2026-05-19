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

    # Pre-finalize: every auto-synthesized relation is the pending sentinel
    # under spec-014 Slice 4's always-defer contract, regardless of whether
    # the target type happens to already be registered.
    assert CategoryType.__annotations__["items"].__name__ == "PendingRelationAnnotation"
    assert ItemType.__annotations__["category"].__name__ == "PendingRelationAnnotation"

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

    # Pre-finalize: every auto-synthesized relation is the pending sentinel
    # under spec-014 Slice 4's always-defer contract.
    assert ItemType.__annotations__["category"].__name__ == "PendingRelationAnnotation"
    assert CategoryType.__annotations__["items"].__name__ == "PendingRelationAnnotation"

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


def test_assigned_scalar_field_override_keeps_consumer_resolver():
    """A ``strawberry.field(resolver=...)`` assigned to a scalar column wins.

    Pins the Medium fix from ``rev-types__base.md``: previously
    ``_consumer_assigned_relation_fields`` only collected relation
    names, so a consumer assigning a ``StrawberryField`` to a scalar
    column (e.g. ``name``) was silently overwritten by the auto-
    synthesized ``str`` annotation. The widened guard collects scalar
    assignments too and ``_build_annotations`` skips them.
    """

    class CategoryType(DjangoType):
        @strawberry.field
        def name(self) -> str:
            return "overridden"

        class Meta:
            model = Category
            fields = ("id", "name")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_assigned_scalar_fields == frozenset({"name"})
    assert "name" in definition.consumer_authored_fields
    # The synthesized scalar annotation must not shadow the consumer
    # assignment — the field name does not appear in the generated
    # annotations dict.
    assert "name" not in CategoryType.__annotations__

    finalize_django_types()
    name_field = _strawberry_field(CategoryType, "name")
    assert name_field.base_resolver is not None
    assert name_field.base_resolver.wrapped_func.__qualname__.endswith("CategoryType.name")


# TODO(docs/spec-015-consumer_overrides_scalar-0_0_6.md Slice 1):
# Add the scalar annotation override, converter-bypass, enum-cache, and Relay
# collision tests beside the existing four-corner override matrix.
# Pseudo:
# - description: int on a selected CharField wins before and after finalize.
# - definition.consumer_annotated_scalar_fields contains the overridden name.
# - _build_annotations omits the overridden scalar from synthesized output.
# - unsupported scalar, grouped choices, and co-resident enum cache cases obey
#   the consumer-authoritative bypass contract.
# - Relay id annotations reject non-NodeID shapes, accept NodeID shapes, and
#   keep inherited id annotations on the pk-suppression path.
def test_scalar_field_class_attribute_shadowing_raises():
    """Unsupported class attributes cannot silently shadow scalar fields either."""
    with pytest.raises(ConfigurationError, match="shadows a Django scalar field"):

        class CategoryType(DjangoType):
            name = 42

            class Meta:
                model = Category
                fields = ("id", "name")


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


# ---------------------------------------------------------------------------
# Slice 3 (spec-014-meta_primary-0_0_6.md) — ambiguity-audit interaction
# with relation resolution. The raise-at-finalize and once-per-build
# regression tests live in ``tests/test_registry.py``; this file hosts the
# audit-success paths and the audit-vs-unresolved-target ordering test.
# ---------------------------------------------------------------------------


def test_finalize_succeeds_when_model_has_multiple_types_one_primary():
    """``finalize_django_types`` succeeds when one of the multi-type entries is primary."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    finalize_django_types()

    assert registry.is_finalized() is True
    assert registry.primary_for(Item) is AdminItemType


def test_finalize_succeeds_when_model_has_single_type_no_primary():
    """Backward-compat: a single registered type with no primary still finalizes cleanly."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    finalize_django_types()

    assert registry.is_finalized() is True
    assert registry.primary_for(Item) is None
    assert registry.get(Item) is ItemType


def test_finalize_ambiguity_error_fires_before_unresolved_target_error():
    """The ambiguity audit runs before pending-relation resolution.

    Sets up both conditions in one test: two ``DjangoType`` subclasses on
    ``Item`` (neither primary) AND a relation to ``Category`` whose
    ``DjangoType`` is not registered (would otherwise raise the
    unresolved-target error). The audit MUST raise first.
    """

    class ItemTypeA(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    class ItemTypeB(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "Models with multiple registered DjangoType subclasses and no primary" in msg
    assert "Cannot finalize Django types" not in msg
    assert "no registered DjangoType" not in msg
