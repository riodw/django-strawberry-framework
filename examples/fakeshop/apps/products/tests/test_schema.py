"""In-process schema tests for the products app.

Exercised via the composed project schema with ``schema.execute_sync`` and a real
GraphQL query string (per AGENTS.md), never by calling resolver methods directly.
The live HTTP counterpart lives in ``examples/fakeshop/test_query``.
"""

import pytest
from config.schema import schema as project_schema

from apps.products import models as products_models


@pytest.mark.django_db
def test_project_schema_executes_products_categories_list():
    """The composed project schema exposes the products app's `all_categories` root field."""
    products_models.Category.objects.create(
        name="Books",
        description="Reading material",
        is_private=False,
    )
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
    category = products_models.Category.objects.create(
        name="Books",
        description="",
        is_private=False,
    )
    products_models.Item.objects.create(
        name="Dune",
        description="",
        category=category,
        is_private=False,
    )
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
    assert {"name", "category", "entries"} <= {
        field["name"] for field in result.data["__type"]["fields"]
    }
