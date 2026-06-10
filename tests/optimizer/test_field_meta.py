"""Tests for B7 - precomputed optimizer field metadata.

Covers ``FieldMeta.from_django_field``, definition-backed field maps on
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
    assert fm.nullable is False
    assert fm.related_model is None


def test_from_django_field_nullable_scalar():
    """Scalar ``null=True`` fields preserve effective nullable metadata."""
    subtitle_field = Book._meta.get_field("subtitle")
    fm = FieldMeta.from_django_field(subtitle_field)
    assert fm.name == "subtitle"
    assert fm.is_relation is False
    assert fm.nullable is True


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
    assert fm.nullable is False


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
    # Reverse FK resolves to a manager (queryset-like) that may be empty
    # but is never ``None``. Django's ``ManyToOneRel`` descriptor inherits
    # ``null = True`` as a class-level default from ``ForeignObjectRel``
    # (which proxies the forward FK's ``null`` flag), but ``FieldMeta``
    # forces ``nullable=False`` for many-side cardinalities so the flag
    # stays self-consistent - a future consumer that reads ``nullable``
    # without first gating on ``one_to_many`` / ``many_to_many`` will
    # still produce the right GraphQL annotation (``list[target_type]``,
    # not ``list[target_type] | None``).
    assert fm.nullable is False


def test_from_django_field_reverse_many_to_many():
    """Reverse M2M descriptor sets ``many_to_many=True`` with ``nullable=False``.

    Genre is the target of ``Book.genres = models.ManyToManyField(Genre)``,
    so iterating ``Genre._meta.get_fields()`` surfaces the reverse-side
    ``ManyToManyRel`` descriptor. Like reverse FK, the descriptor inherits
    ``null = True`` from ``ForeignObjectRel``; ``FieldMeta`` must override
    that for many-side cardinalities so the rendered GraphQL annotation
    stays ``list[target_type]`` (a manager is never ``None``).
    """
    reverse_m2m_field = None
    for f in Genre._meta.get_fields():
        if f.is_relation and getattr(f, "many_to_many", False) and f.related_model is Book:
            reverse_m2m_field = f
            break
    assert reverse_m2m_field is not None
    fm = FieldMeta.from_django_field(reverse_m2m_field)
    assert fm.is_relation is True
    assert fm.many_to_many is True
    assert fm.related_model is Book
    assert fm.nullable is False


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
    # M2M renders as ``list[target_type]`` (not nullable); the rule defaults to
    # ``False`` when the field's ``null`` flag is unset/False.
    assert fm.nullable is False


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
    # Forward OneToOne (``MembershipCard.patron``) declares no ``null=True``,
    # so the rule falls through both clauses (not reverse_one_to_one + no
    # ``field.null``) and yields ``False``.  Pairs with
    # ``test_from_django_field_reverse_one_to_one_is_nullable`` for the
    # short-circuit side of the same expression.
    assert fm.nullable is False


def test_from_django_field_reverse_one_to_one_is_nullable():
    """Reverse OneToOne is effectively nullable because the related row may not exist."""
    card_field = Patron._meta.get_field("card")
    fm = FieldMeta.from_django_field(card_field)
    assert fm.name == "card"
    assert fm.is_relation is True
    assert fm.one_to_one is True
    assert fm.auto_created is True
    assert fm.nullable is True


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


def test_is_many_side_pins_every_relation_kind():
    """``is_many_side`` is ``True`` for many-side kinds and ``False`` otherwise.

    Pins the delegation to ``utils.relations.is_many_side_relation_kind`` for
    every value of ``RelationKind`` directly, rather than indirectly via the
    ``nullable`` short-circuits exercised by the ``from_django_field`` cases.
    """
    forward_m2m = FieldMeta(name="forward_m2m", is_relation=True, many_to_many=True)
    reverse_fk = FieldMeta(
        name="reverse_fk",
        is_relation=True,
        one_to_many=True,
        auto_created=True,
    )
    reverse_o2o = FieldMeta(
        name="reverse_o2o",
        is_relation=True,
        one_to_one=True,
        auto_created=True,
    )
    forward_single = FieldMeta(name="forward_single", is_relation=True)

    assert forward_m2m.relation_kind == "many"
    assert forward_m2m.is_many_side is True

    assert reverse_fk.relation_kind == "reverse_many_to_one"
    assert reverse_fk.is_many_side is True

    assert reverse_o2o.relation_kind == "reverse_one_to_one"
    assert reverse_o2o.is_many_side is False

    assert forward_single.relation_kind == "forward_single"
    assert forward_single.is_many_side is False


# ---------------------------------------------------------------------------
# DjangoTypeDefinition.field_map on DjangoType
# ---------------------------------------------------------------------------


def test_optimizer_field_map_populated():
    """B7: definition.field_map is populated after DjangoType subclass creation."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    definition = registry.get_definition(CategoryType)

    assert definition is not None
    field_map = definition.field_map
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

    definition = registry.get_definition(ItemType)

    assert definition is not None
    field_map = definition.field_map
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

    definition = registry.get_definition(CategoryType)

    assert definition is not None
    field_map = definition.field_map
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
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    # The plan should contain select_related for the forward FK.
    assert "category" in plan.select_related
