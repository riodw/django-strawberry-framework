"""In-process schema tests for the products app.

Exercised via the composed project schema with ``schema.execute_sync`` and a real
GraphQL query string (per AGENTS.md), never by calling resolver methods directly.
The live HTTP counterpart lives in ``examples/fakeshop/test_query``.

Per AGENTS.md, catalog tests seed via ``services.seed_data`` and never hand-roll
``Category`` / ``Item`` rows; assertions are data-driven off the seeded set so
they hold regardless of the exact Faker provider list.
"""

from collections import defaultdict

import pytest
from config.schema import schema as project_schema

from apps.products import models as products_models
from apps.products.services import seed_data


@pytest.mark.django_db
def test_project_schema_executes_products_categories_list():
    """The composed project schema exposes the products app's `all_categories` root field."""
    seed_data(1)

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
    assert names == set(products_models.Category.objects.values_list("name", flat=True))


@pytest.mark.django_db
def test_project_schema_traverses_products_relations():
    """Forward + reverse relation traversal works through the products schema."""
    seed_data(1)

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

    # Forward FK: each item reports its real category name.
    expected_item_category = dict(
        products_models.Item.objects.values_list("name", "category__name"),
    )
    got_item_category = {row["name"]: row["category"]["name"] for row in result.data["allItems"]}
    assert got_item_category == expected_item_category

    # Reverse FK: each category lists exactly its own items.
    expected_category_items: dict[str, list[str]] = defaultdict(list)
    for name in products_models.Category.objects.values_list("name", flat=True):
        expected_category_items[name] = []
    for category_name, item_name in products_models.Item.objects.values_list(
        "category__name",
        "name",
    ):
        expected_category_items[category_name].append(item_name)
    got_category_items = {
        row["name"]: sorted(i["name"] for i in row["items"]) for row in result.data["allCategories"]
    }
    assert got_category_items == {
        name: sorted(items) for name, items in expected_category_items.items()
    }


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
