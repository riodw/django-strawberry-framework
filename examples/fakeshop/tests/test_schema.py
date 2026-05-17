"""Tests for the example schemas — both products and project schemas exercised via GraphQL execution.

Per AGENTS.md: schema is tested via ``schema.execute_sync`` with a real
GraphQL query string, never by calling resolver methods directly.
"""

import pytest
from apps.library import schema as library_schema
from apps.products import models as products_models
from config.schema import schema as project_schema

from django_strawberry_framework import DjangoType


@pytest.mark.django_db
def test_project_schema_executes_products_categories_list():
    """The composed project schema exposes the products app's `all_categories` root field."""
    products_models.Category.objects.create(name="Books", description="Reading material", is_private=False)
    products_models.Category.objects.create(name="Tools", description="Hardware", is_private=False)

    result = project_schema.execute_sync(
        """
        query {
          allCategories {
            id
            name
            description
          }
        }
        """,
    )

    assert result.errors is None
    names = {row["name"] for row in result.data["allCategories"]}
    assert {"Books", "Tools"} <= names


@pytest.mark.django_db
def test_project_schema_traverses_products_relations():
    """Forward + reverse relation traversal works through the products schema."""
    category = products_models.Category.objects.create(name="Books", description="", is_private=False)
    products_models.Item.objects.create(name="Dune", description="", category=category, is_private=False)
    products_models.Item.objects.create(
        name="Foundation",
        description="",
        category=category,
        is_private=False,
    )

    result = project_schema.execute_sync(
        """
        query {
          allItems {
            name
            category { name }
          }
          allCategories {
            name
            items { name }
          }
        }
        """,
    )

    assert result.errors is None
    item_category_names = {row["category"]["name"] for row in result.data["allItems"]}
    assert item_category_names == {"Books"}
    category_item_lists = {
        row["name"]: sorted(i["name"] for i in row["items"]) for row in result.data["allCategories"]
    }
    assert category_item_lists["Books"] == ["Dune", "Foundation"]


def test_project_schema_includes_products_types():
    """The composed project schema exposes the products app's DjangoTypes."""
    result = project_schema.execute_sync(
        """
        query {
          __type(name: "ItemType") {
            name
            fields { name }
          }
        }
        """,
    )

    assert result.errors is None
    assert result.data["__type"]["name"] == "ItemType"
    assert {"name", "category", "entries"} <= {field["name"] for field in result.data["__type"]["fields"]}


def test_project_schema_includes_library_types():
    """The composed project schema exposes the library app's DjangoTypes."""
    result = project_schema.execute_sync(
        """
        query {
          __type(name: "BookType") {
            name
            fields { name }
          }
        }
        """,
    )

    assert result.errors is None
    assert result.data["__type"]["name"] == "BookType"
    assert {"title", "shelf", "genres"} <= {field["name"] for field in result.data["__type"]["fields"]}


def test_library_djangotype_declaration_order_stays_awkward():
    """Pin the real app's intentionally cross-referenced declaration order."""
    declaration_order = [
        name
        for name, value in vars(library_schema).items()
        if isinstance(value, type) and issubclass(value, DjangoType) and value is not DjangoType
    ]

    assert declaration_order.index("LoanType") < declaration_order.index("BookType")
    assert declaration_order.index("LoanType") < declaration_order.index("PatronType")
    assert declaration_order.index("ShelfType") < declaration_order.index("BranchType")
    assert declaration_order.index("MembershipCardType") < declaration_order.index("PatronType")
