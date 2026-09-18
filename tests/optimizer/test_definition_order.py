"""Optimizer tests for definition-order-independent DjangoType relation graphs.

``plan_relation`` return tuples after cyclic finalize, ``check_schema`` warning
absence, definition ``field_map`` identity, and annotation-only relation
metadata have no wire shape. Reverse-O2O JOIN SQL is
``examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_reverse_o2o_card_joins_in_root_sql``;
hooked-target Prefetch SQL is
``examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_o6_downgrade_to_prefetch_for_custom_get_queryset_in_http_query``.
"""

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
    """Cyclic finalization still returns the cardinality ``plan_relation`` tuples.

    The callable's return pair is not a wire value. Reverse-O2O JOIN SQL is
    ``examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_reverse_o2o_card_joins_in_root_sql``.
    """

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

    assert plan_relation(_model_field(Item, "category"), CategoryType, info=None) == (
        "select",
        "default",
    )
    assert plan_relation(_model_field(Category, "items"), ItemType, info=None) == (
        "prefetch",
        "default",
    )
    assert plan_relation(_model_field(MembershipCard, "patron"), PatronType, info=None) == (
        "select",
        "default",
    )
    assert plan_relation(_model_field(Patron, "card"), MembershipCardType, info=None) == (
        "select",
        "default",
    )
    assert plan_relation(_model_field(Book, "genres"), GenreType, info=None) == (
        "prefetch",
        "default",
    )
    assert plan_relation(_model_field(Genre, "books"), BookType, info=None) == (
        "prefetch",
        "default",
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


def test_definition_field_map_carries_optimizer_metadata():
    """Definition-owned field metadata is the optimizer's canonical source."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = registry.get_definition(CategoryType)

    assert definition is not None
    assert sorted(definition.field_map) == ["id", "items", "name"]


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

    assert plan.select_related == ()
    assert getattr(plan.prefetch_related[0], "prefetch_to", None) == "items"
    assert plan.planned_resolver_keys == ("CategoryType.items@items",)
