"""Optimizer regressions for definition-order-independent DjangoType graphs."""

import pytest
import strawberry
from apps.library.models import Book, Genre, MembershipCard, Patron
from apps.products.models import Category, Item

from django_strawberry_framework import DjangoOptimizerExtension, DjangoType, finalize_django_types
from django_strawberry_framework.optimizer.walker import plan_optimizations, plan_relation
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


def _sel(name, selections=None):
    """Build a synthetic selected field."""
    from types import SimpleNamespace

    return SimpleNamespace(
        name=name,
        alias=None,
        directives={},
        arguments={},
        selections=selections or [],
    )


def _model_field(model: type, name: str):
    """Return a Django field by name, including reverse relations."""
    return next(field for field in model._meta.get_fields() if field.name == name)


def test_plan_relation_decisions_match_cardinality_after_finalization():
    """Cyclic finalization preserves select/prefetch planning decisions."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    class MembershipCardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode", "patron")

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name", "card")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "genres")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name", "books")

    finalize_django_types()

    assert plan_relation(_model_field(Item, "category"), CategoryType, info=None) == ("select", "default")
    assert plan_relation(_model_field(Category, "items"), ItemType, info=None) == ("prefetch", "default")
    assert plan_relation(_model_field(MembershipCard, "patron"), PatronType, info=None) == (
        "select",
        "default",
    )
    assert plan_relation(_model_field(Patron, "card"), MembershipCardType, info=None) == ("select", "default")
    assert plan_relation(_model_field(Book, "genres"), GenreType, info=None) == ("prefetch", "default")
    assert plan_relation(_model_field(Genre, "books"), BookType, info=None) == ("prefetch", "default")


def test_plan_relation_downgrades_custom_get_queryset_target_after_finalization():
    """A custom target get_queryset still forces Prefetch after finalization."""

    class MembershipCardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode", "patron")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name", "card")

    finalize_django_types()
    assert plan_relation(_model_field(Patron, "card"), MembershipCardType, info=None) == (
        "prefetch",
        "custom_get_queryset",
    )


def test_check_schema_returns_no_warnings_for_registered_cyclic_targets():
    """The schema audit accepts reachable cyclic relations when every target is registered."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    finalize_django_types()
    schema = strawberry.Schema(query=Query)

    assert DjangoOptimizerExtension.check_schema(schema) == []


def test_definition_field_map_matches_legacy_optimizer_mirror():
    """Definition-owned field metadata mirrors the legacy optimizer class attribute."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = registry.get_definition(CategoryType)

    assert definition is not None
    assert definition.field_map == CategoryType._optimizer_field_map


def test_annotation_only_relation_override_still_plans_prefetch():
    """Annotation-only relation overrides keep optimizer-visible relation metadata."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        items: list[ItemType]

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    finalize_django_types()

    plan = plan_optimizations([_sel("items", selections=[_sel("name")])], Category)

    assert plan.select_related == []
    assert getattr(plan.prefetch_related[0], "prefetch_to", None) == "items"
    assert plan.planned_resolver_keys == ["CategoryType.items@items"]
