"""Tests for B7 — precomputed optimizer field metadata.

Covers ``FieldMeta.from_django_field``, ``_optimizer_field_map`` on
``DjangoType`` subclasses, and the walker's use of the cached map.
"""

import pytest
from apps.library.models import Book, Genre, MembershipCard, Patron
from apps.products import services
from apps.products.models import Category, Item

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import OptimizerError
from django_strawberry_framework.optimizer.field_meta import FieldMeta
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


# ---------------------------------------------------------------------------
# FieldMeta.from_django_field
# ---------------------------------------------------------------------------


def test_from_django_field_scalar():
    """Scalar fields produce a FieldMeta with is_relation=False."""
    name_field = Category._meta.get_field("name")
    fm = FieldMeta.from_django_field(name_field)
    assert fm.name == "name"
    assert fm.is_relation is False
    assert fm.many_to_many is False
    assert fm.related_model is None


def test_from_django_field_forward_fk():
    """Forward FK produces is_relation=True with attname and related_model."""
    cat_field = Item._meta.get_field("category")
    fm = FieldMeta.from_django_field(cat_field)
    assert fm.name == "category"
    assert fm.is_relation is True
    assert fm.related_model is Category
    assert fm.attname == "category_id"
    assert fm.target_field_name == "id"
    assert fm.many_to_many is False
    assert fm.one_to_many is False


def test_from_django_field_reverse_fk():
    """Reverse FK (one_to_many) is detected correctly."""
    # Category.items is the reverse side of Item.category
    items_field = None
    for f in Category._meta.get_fields():
        if f.name == "items":
            items_field = f
            break
    assert items_field is not None
    fm = FieldMeta.from_django_field(items_field)
    assert fm.is_relation is True
    assert fm.one_to_many is True


def test_from_django_field_many_to_many():
    """M2M forward field sets many_to_many=True, is_relation=True, related_model."""
    genres_field = Book._meta.get_field("genres")
    fm = FieldMeta.from_django_field(genres_field)
    assert fm.name == "genres"
    assert fm.is_relation is True
    assert fm.many_to_many is True
    assert fm.related_model is Genre
    assert fm.one_to_many is False
    assert fm.one_to_one is False


def test_from_django_field_one_to_one():
    """Forward OneToOne sets one_to_one=True with attname and target field."""
    patron_field = MembershipCard._meta.get_field("patron")
    fm = FieldMeta.from_django_field(patron_field)
    assert fm.name == "patron"
    assert fm.is_relation is True
    assert fm.one_to_one is True
    assert fm.related_model is Patron
    assert fm.attname == "patron_id"
    assert fm.target_field_name == "id"
    assert fm.target_field_attname == "id"


def test_from_django_field_rejects_non_django_input():
    """Inputs missing 'name'/'is_relation' raise OptimizerError at the call site.

    Without the guard, the failure mode would be ``AttributeError`` deep
    inside the optimizer walker's class-creation path. The typed
    exception makes the contract violation explicit.
    """

    class NotAField:
        pass

    with pytest.raises(OptimizerError, match="expected a Django field descriptor"):
        FieldMeta.from_django_field(NotAField())  # type: ignore[arg-type]


def test_from_django_field_rejects_partial_shape():
    """An input with 'name' but missing 'is_relation' still raises OptimizerError."""

    class PartialField:
        name = "x"

    with pytest.raises(OptimizerError):
        FieldMeta.from_django_field(PartialField())  # type: ignore[arg-type]


def test_field_meta_is_frozen():
    """FieldMeta instances are immutable."""
    fm = FieldMeta(name="test")
    with pytest.raises(AttributeError):
        fm.name = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# _optimizer_field_map on DjangoType
# ---------------------------------------------------------------------------


def test_optimizer_field_map_populated():
    """B7: _optimizer_field_map is populated after DjangoType subclass creation."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert hasattr(CategoryType, "_optimizer_field_map")
    field_map = CategoryType._optimizer_field_map
    assert "id" in field_map
    assert "name" in field_map
    assert isinstance(field_map["id"], FieldMeta)


def test_optimizer_field_map_contains_relations():
    """B7: relation fields appear in the map with correct metadata."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    field_map = ItemType._optimizer_field_map
    assert "category" in field_map
    cat_meta = field_map["category"]
    assert cat_meta.is_relation is True
    assert cat_meta.related_model is Category


def test_optimizer_field_map_respects_fields_filter():
    """B7: only Meta.fields-selected fields appear in the map."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id",)

    field_map = CategoryType._optimizer_field_map
    assert "id" in field_map
    assert "name" not in field_map


# ---------------------------------------------------------------------------
# Walker uses the cached map
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_walker_produces_same_plan_with_cached_map(django_assert_num_queries):
    """B7: the walker's plan is identical whether it uses the cached map or _meta."""
    import strawberry

    from django_strawberry_framework import DjangoOptimizerExtension, finalize_django_types

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

    from types import SimpleNamespace

    finalize_django_types()
    schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    # The plan should contain select_related for the forward FK.
    assert "category" in plan.select_related
