"""Products schema tests for in-process GraphQL execution without HTTP.

Exercised via the composed project schema with ``schema.execute_sync`` and a real
GraphQL query string (per AGENTS.md), never by calling resolver methods directly.
The live HTTP counterpart lives in ``examples/fakeshop/test_query``.

Per AGENTS.md, catalog tests seed via ``services.seed_data`` and never hand-roll
``Category`` / ``Item`` rows; assertions are data-driven off the seeded set so
they hold regardless of the exact Faker provider list.
"""

import sys
from collections import defaultdict

import pytest

from apps.products import models as products_models
from apps.products.services import seed_data


@pytest.fixture
def project_schema(reload_all_project_app_schemas):
    """Recompose ``config.schema.schema`` against a fully re-registered registry.

    The sibling live HTTP suites under ``test_query/`` clear the global registry
    and reload ``config.schema`` between tests, and worker-sharing package tests
    (e.g. ``examples/fakeshop/tests/test_inspect_django_type.py``) evict the schema
    modules from ``sys.modules`` without restoring them. A products-only partial
    reload here would leave the *non-products* apps either unregistered (cascade
    hooks missing, items under private categories leaking) or duplicated (a
    re-imported ``apps.library.schema`` colliding at the aggregate build ->
    ``DuplicatedTypeName: BookInputCirculationStatusEnum``).

    So this fixture rebuilds the WHOLE project schema via the shared
    ``schema_reload.reload_all_project_schemas`` complete-reload discipline (the
    same single-sited helper every ``test_query/`` acceptance file uses, exposed
    here through the ``apps.products.tests`` conftest's
    ``reload_all_project_app_schemas`` fixture): clear the registry and re-register
    ALL five apps in dependency-safe order before reloading ``config.schema``, so
    the composed schema binds the activated products types and resolves every app's
    inputs exactly once - regardless of which suite ran before this one. Model
    modules are never reloaded so Django model classes stay stable.
    """
    reload_all_project_app_schemas()
    return sys.modules["config.schema"].schema


@pytest.mark.django_db
def test_project_schema_executes_products_categories_list(project_schema):
    """The composed project schema exposes the products app's `all_categories` root field.

    Executed in-process (no HTTP request), so the activated cascade hooks
    (spec-034 Slice 4) resolve no user from `info.context.request` and apply the
    anonymous visibility rule: only non-private categories are returned. The
    expected set is therefore the equivalent post-cascade ORM query.
    """
    seed_data(1)

    result = project_schema.execute_sync(
        """
        query {
          allCategories {
            edges {
              node {
                id
                name
                description
              }
            }
          }
        }
        """,
    )

    assert result.errors is None
    names = {edge["node"]["name"] for edge in result.data["allCategories"]["edges"]}
    assert names == set(
        products_models.Category.objects.filter(is_private=False).values_list("name", flat=True),
    )


@pytest.mark.django_db
def test_project_schema_traverses_products_relations(project_schema):
    """Forward + reverse relation traversal works through the products schema.

    Executed in-process (no HTTP request), so the activated cascade hooks
    (spec-034 Slice 4) apply the anonymous visibility rule throughout: the root
    `allItems` returns non-private items under non-private categories, the root
    `allCategories` returns non-private categories, and each category's nested
    `items` list narrows to that category's non-private items. The expected maps
    are derived from the equivalent post-cascade ORM queries (API == ORM).
    """
    seed_data(1)

    result = project_schema.execute_sync(
        """
        query {
          allItems {
            edges {
              node {
                name
                category { name }
              }
            }
          }
          allCategories {
            edges {
              node {
                name
                items { name }
              }
            }
          }
        }
        """,
    )

    assert result.errors is None

    # Forward FK: each visible item reports its real category name. Anonymous sees
    # only non-private items under non-private categories.
    visible_items = products_models.Item.objects.filter(
        is_private=False,
        category__is_private=False,
    )
    expected_item_category = dict(visible_items.values_list("name", "category__name"))
    got_item_category = {
        edge["node"]["name"]: edge["node"]["category"]["name"]
        for edge in result.data["allItems"]["edges"]
    }
    assert got_item_category == expected_item_category

    # Reverse FK: each visible (non-private) category lists exactly its own
    # non-private items (the nested ItemType cascade narrows the list).
    expected_category_items: dict[str, list[str]] = defaultdict(list)
    for name in products_models.Category.objects.filter(is_private=False).values_list(
        "name",
        flat=True,
    ):
        expected_category_items[name] = []
    for category_name, item_name in products_models.Item.objects.filter(
        is_private=False,
        category__is_private=False,
    ).values_list("category__name", "name"):
        expected_category_items[category_name].append(item_name)
    got_category_items = {
        edge["node"]["name"]: sorted(i["name"] for i in edge["node"]["items"])
        for edge in result.data["allCategories"]["edges"]
    }
    assert got_category_items == {
        name: sorted(items) for name, items in expected_category_items.items()
    }


def test_project_schema_includes_products_types(project_schema):
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
