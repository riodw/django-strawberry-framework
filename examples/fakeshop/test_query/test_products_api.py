"""Live GraphQL HTTP tests for the products app API surface.

Mirrors ``test_library_api.py``'s harness. Exercises the products schema
wired in ``apps.products.schema`` end to end:

* optimizer SQL-shape contracts that are reachable through the real
  products GraphQL API;
* the per-field ``check_name_permission`` gate on ``CategoryFilter`` (a
  ``DONE-021-0.0.8`` filter permission hook) -- including the regression
  guard that the gate now fires for NON-``exact`` lookups (``iContains``),
  not just ``exact``;
* own-PK Relay ``GlobalID`` filtering (``id: { in: [...] }``) now that the
  products types declare ``interfaces = (relay.Node,)``;
* ``RelatedFilter`` traversal (``Item.category``) via the nested
  GlobalID input.

Per AGENTS.md, the catalog is seeded via ``services.seed_data`` and the auth
user via ``services.create_users`` -- never hand-rolled. Faker-generated names
vary per provider set, so assertions are data-driven: the expected rows are
derived from the seeded data (or from the equivalent ORM query) and compared
against the GraphQL result, which both pins the filter behaviour and stays
robust across Faker versions.
"""

import importlib
import json
import sys

import pytest
from apps.products import models
from apps.products.services import create_users, seed_data
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches
from strawberry import relay

from django_strawberry_framework.registry import registry


def _reload_products_project_schema() -> None:
    """Recreate imported DjangoType classes if package tests cleared the registry.

    Mirrors ``test_library_api.py::_reload_library_project_schema``: package
    tests clear the global registry, while the example schema finalizes
    import-time ``DjangoType`` classes. Reload only schema modules (not
    ``apps.products.models``) so Django model classes stay stable.

    Lifted out of the autouse fixture so a test can drive the reload itself
    after applying ``override_settings`` (e.g. the ``type``-strategy opt-out),
    ensuring the override is active *before* the schema finalizes.
    """
    registry.clear()
    products_schema = sys.modules.get("apps.products.schema")
    if products_schema is None:
        importlib.import_module("apps.products.schema")
    else:
        importlib.reload(products_schema)

    project_schema = sys.modules.get("config.schema")
    if project_schema is None:
        importlib.import_module("config.schema")
    else:
        importlib.reload(project_schema)

    urls = sys.modules.get("config.urls")
    if urls is not None:
        importlib.reload(urls)
        clear_url_caches()


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests():
    """Recreate the project schema around package-test registry clears."""
    _reload_products_project_schema()


def _post_graphql(query: str, *, client: Client | None = None):
    graphql_client = client or Client()
    return graphql_client.post(
        "/graphql/",
        data={"query": query},
        content_type="application/json",
    )


def _assert_graphql_data(query: str, expected: dict, *, client: Client | None = None):
    response = _post_graphql(query, client=client)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"] == expected
    return response


def _staff_client() -> Client:
    """Log in the seeded ``staff_1`` user (``is_staff=True``) created by ``create_users``."""
    create_users(1)
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))
    return client


def _global_id(type_name: str, pk: int) -> str:
    return str(relay.GlobalID(type_name=type_name, node_id=str(pk)))


@pytest.mark.django_db
def test_emitted_globalid_is_model_anchored():
    """An emitted ``node { id }`` decodes to the Django model label, not the type name.

    Under the ``0.0.9`` model-label default, ``ItemType``'s ``GlobalID``
    carries ``products.item:<pk>`` (``models.Item._meta.label_lower``), not the
    GraphQL type name ``ItemType``. Decode the API-emitted ``id`` via
    ``relay.GlobalID.from_id`` and assert the model-label payload.
    """
    seed_data(1)
    item = models.Item.objects.order_by("id").first()
    response = _post_graphql("query { allItems { id name } }")
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    emitted = next(row for row in payload["data"]["allItems"] if row["name"] == item.name)
    parsed = relay.GlobalID.from_id(emitted["id"])
    assert parsed.type_name == models.Item._meta.label_lower
    assert parsed.node_id == str(item.pk)


@pytest.mark.django_db
def test_globalid_filter_round_trip():
    """THE headline ``0.0.9`` workflow: feed an emitted GlobalID straight back as a filter.

    Take the model-label ``id`` the products API just emitted for one item and
    feed it back verbatim as ``filter: { id: { exact: "<that id>" } }``; the
    strategy-aware filter ([Decision 13]) accepts the model-label payload it now
    emits and returns exactly that one row. Uses the API-emitted id (not a
    reconstructed one) so the test proves true emit -> filter symmetry.
    """
    seed_data(1)
    target = models.Item.objects.order_by("id").first()
    emit_response = _post_graphql("query { allItems { id name } }")
    assert emit_response.status_code == 200
    emit_payload = emit_response.json()
    assert "errors" not in emit_payload, emit_payload
    emitted = next(row for row in emit_payload["data"]["allItems"] if row["name"] == target.name)
    emitted_id = emitted["id"]

    _assert_graphql_data(
        f'query {{ allItems(filter: {{ id: {{ exact: "{emitted_id}" }} }}) {{ id name }} }}',
        {"allItems": [{"id": emitted_id, "name": target.name}]},
    )


@pytest.mark.django_db
def test_type_strategy_opt_out_reproduces_type_name():
    """``RELAY_GLOBALID_STRATEGY = "type"`` opts back into the GraphQL-type-name payload.

    Deterministic per ``docs/feedback.md`` P3: the override is applied *before*
    ``_reload_products_project_schema()`` finalizes the schema (the fakeshop
    fixtures reload at finalization, so a strategy override must precede the
    reload or the test silently exercises the default schema). Under the ``type``
    strategy ``ItemType``'s ``id`` reproduces the GraphQL type name ``ItemType``
    (== ``ItemType.__name__``, no ``Meta.name``), NOT the model label. The
    per-test autouse fixture re-reloads the default-strategy schema for siblings.
    """
    seed_data(1)
    item = models.Item.objects.order_by("id").first()
    with override_settings(
        DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"},
    ):
        _reload_products_project_schema()
        response = _post_graphql("query { allItems { id name } }")
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        emitted = next(row for row in payload["data"]["allItems"] if row["name"] == item.name)
        parsed = relay.GlobalID.from_id(emitted["id"])
        assert parsed.type_name == "ItemType"
        assert parsed.node_id == str(item.pk)


@pytest.mark.django_db
def test_products_optimizer_merges_duplicate_root_field_nodes_over_http():
    seed_data(1)
    expected = [
        {"name": item.name, "category": {"name": item.category.name}}
        for item in models.Item.objects.select_related("category").order_by("id")
    ]

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allItems { name }
              allItems { category { name } }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"] == {"allItems": expected}
    assert len(captured) == 1, [query["sql"] for query in captured]
    sql = captured[0]["sql"].lower()
    assert "products_item" in sql
    assert "join" in sql
    assert "products_category" in sql


@pytest.mark.django_db
def test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http():
    seed_data(1)

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allCategories {
                name
                items {
                  name
                  entries { value }
                }
              }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    categories = payload["data"]["allCategories"]
    items = [item for category in categories for item in category["items"]]
    entries = [entry for item in items for entry in item["entries"]]
    assert len(categories) == models.Category.objects.count()
    assert len(items) == models.Item.objects.count()
    assert len(entries) == models.Entry.objects.count()
    assert len(captured) == 3, [query["sql"] for query in captured]
    assert "products_category" in captured[0]["sql"]
    assert "products_item" in captured[1]["sql"]
    assert "products_entry" in captured[2]["sql"]


@pytest.mark.django_db
def test_products_optimizer_selects_nested_forward_fk_depth_2_over_http():
    seed_data(1)
    expected = [
        {
            "id": _global_id(models.Entry._meta.label_lower, entry.pk),
            "value": entry.value,
            "item": {
                "id": _global_id(models.Item._meta.label_lower, entry.item_id),
                "name": entry.item.name,
                "category": {
                    "id": _global_id(models.Category._meta.label_lower, entry.item.category_id),
                    "name": entry.item.category.name,
                },
            },
        }
        for entry in models.Entry.objects.select_related("item__category").order_by("id")
    ]

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allEntries {
                id
                value
                item {
                  id
                  name
                  category { id name }
                }
              }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"] == {"allEntries": expected}
    assert len(captured) == 1, [query["sql"] for query in captured]
    sql = captured[0]["sql"].lower()
    assert "products_entry" in sql
    assert "products_item" in sql
    assert "products_category" in sql
    assert "join" in sql


@pytest.mark.django_db
def test_products_categories_filter_by_name_exact_as_staff():
    """A staff user clears ``CategoryFilter.check_name_permission`` and filters by name."""
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    _assert_graphql_data(
        f"query {{ allCategories(filter: {{ name: {{ exact: {json.dumps(category.name)} }} }}) {{ name }} }}",
        {"allCategories": [{"name": category.name}]},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_categories_filter_by_name_denied_for_anonymous():
    """An anonymous user filtering by ``Category.name`` (exact) is rejected by the gate."""
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    response = _post_graphql(
        f"query {{ allCategories(filter: {{ name: {{ exact: {json.dumps(category.name)} }} }}) {{ name }} }}",
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_categories_name_permission_fires_for_non_exact_lookup():
    """The gate fires for a NON-``exact`` lookup too (regression guard).

    Before the fix, ``check_<field>_permission`` was dispatched on the
    lookup-expanded form key, so only ``exact`` (the suffix-free key)
    triggered it; ``iContains`` slipped past ungated. The gate now keys on
    the source field, so an anonymous ``name: { iContains: ... }`` filter
    is rejected exactly like the ``exact`` form.
    """
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    response = _post_graphql(
        f"query {{ allCategories(filter: {{ name: {{ iContains: {json.dumps(category.name[:2])} }} }}) {{ name }} }}",
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_items_related_category_name_permission_fires_for_anonymous():
    """A child ``RelatedFilter`` permission gate fires through the live API."""
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    response = _post_graphql(
        f"query {{ allItems(filter: {{ category: {{ name: {{ exact: {json.dumps(category.name)} }} }} }}) {{ name }} }}",
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_categories_filter_by_relay_own_pk_global_id_in():
    """Own-PK Relay ``id: { in: [...] }`` accepts a list of GlobalIDs.

    ``CategoryType`` is a Relay node, so ``id`` is a GlobalID; the ``in``
    lookup resolves to ``GlobalIDMultipleChoiceFilter`` and each element is
    decoded + type-validated before the ``id__in`` clause runs. No
    permission gate guards ``id``, so this works anonymously.
    """
    seed_data(1)
    categories = list(models.Category.objects.order_by("id")[:2])
    gids = ", ".join(
        f'"{relay.GlobalID(type_name=models.Category._meta.label_lower, node_id=str(category.pk))}"'
        for category in categories
    )
    _assert_graphql_data(
        f"query {{ allCategories(filter: {{ id: {{ in: [{gids}] }} }}) {{ name }} }}",
        {"allCategories": [{"name": category.name} for category in categories]},
    )


@pytest.mark.django_db
def test_products_categories_filter_by_starts_with_via_all_lookups():
    """``Meta.fields = {"name": "__all__"}`` exposes lookups beyond the explicit set.

    ``startsWith`` is in none of the hand-listed lookup sets -- it exists only
    because ``CategoryFilter.name`` uses the per-field ``"__all__"`` shorthand,
    which expands to every concrete (non-transform) lookup for the field. The
    expected rows are computed with the equivalent ORM ``startswith`` so the
    assertion pins API == ORM rather than a Faker-specific name.
    """
    seed_data(1)
    prefix = models.Category.objects.order_by("id").first().name[:2]
    expected = [
        {"name": name}
        for name in models.Category.objects.filter(name__startswith=prefix)
        .order_by("id")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allCategories(filter: {{ name: {{ startsWith: "{prefix}" }} }}) {{ name }} }}',
        {"allCategories": expected},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_items_filter_by_related_category_global_id():
    """``Item.category`` ``RelatedFilter`` traversal via the nested GlobalID input."""
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    gid = str(
        relay.GlobalID(type_name=models.Category._meta.label_lower, node_id=str(category.pk)),
    )
    expected = [
        {"name": name}
        for name in models.Item.objects.filter(category=category)
        .order_by("id")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allItems(filter: {{ category: {{ id: {{ exact: "{gid}" }} }} }}) {{ name }} }}',
        {"allItems": expected},
    )


# ---------------------------------------------------------------------------
# Ordering (DONE-028-0.0.8) - wired in ``apps.products.schema`` via the
# ``orderset_class`` Meta key and the ``order_input_type(...)`` resolver
# arguments. Expectations compare against the equivalent ORM ``order_by`` so
# the GraphQL ``ORDER BY`` and the expected sequence share one DB collation
# (robust across Faker-generated values and name ties).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_products_items_order_by_name_asc():
    """``orderBy: [{ name: ASC }]`` sorts items by name ascending (Item has no order gate)."""
    seed_data(1)
    expected = [
        {"name": name}
        for name in models.Item.objects.order_by("name").values_list("name", flat=True)
    ]
    _assert_graphql_data(
        "query { allItems(orderBy: [{ name: ASC }]) { name } }",
        {"allItems": expected},
    )


@pytest.mark.django_db
def test_products_items_order_by_name_desc():
    """``orderBy: [{ name: DESC }]`` sorts items by name descending."""
    seed_data(1)
    expected = [
        {"name": name}
        for name in models.Item.objects.order_by("-name").values_list("name", flat=True)
    ]
    _assert_graphql_data(
        "query { allItems(orderBy: [{ name: DESC }]) { name } }",
        {"allItems": expected},
    )


@pytest.mark.django_db
def test_products_categories_order_by_name_denied_for_anonymous():
    """``CategoryOrder.check_name_permission`` rejects an anonymous order-by-name.

    Active-input-only: the gate fires because the ``orderBy`` input names the
    gated ``name`` field - mirroring ``CategoryFilter.check_name_permission``
    on the filter side.
    """
    seed_data(1)
    response = _post_graphql("query { allCategories(orderBy: [{ name: ASC }]) { name } }")
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_categories_order_by_name_as_staff():
    """A staff user clears the order-by-name gate and gets categories sorted by name."""
    seed_data(1)
    expected = [
        {"name": name}
        for name in models.Category.objects.order_by("name").values_list("name", flat=True)
    ]
    _assert_graphql_data(
        "query { allCategories(orderBy: [{ name: ASC }]) { name } }",
        {"allCategories": expected},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_items_order_by_related_category_name_denied_for_anonymous():
    """A child ``RelatedOrder`` permission gate fires through the live API."""
    seed_data(1)
    response = _post_graphql(
        """
        query {
          allItems(orderBy: [{ category: { name: ASC } }]) {
            name
          }
        }
        """,
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_items_order_by_related_category_name_as_staff():
    """Nested ``RelatedOrder`` input sorts by the child order field."""
    seed_data(1)
    expected = [
        {"name": item.name, "category": {"name": item.category.name}}
        for item in models.Item.objects.select_related("category").order_by("category__name")
    ]
    _assert_graphql_data(
        """
        query {
          allItems(orderBy: [{ category: { name: ASC } }]) {
            name
            category { name }
          }
        }
        """,
        {"allItems": expected},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_items_filter_and_order_compose():
    """``filter:`` narrows rows then ``orderBy:`` arranges them (filter -> order chain).

    Filters items to one category via the own-PK GlobalID ``RelatedFilter``
    (no gate on ``id``) and orders the survivors by ``name`` (no gate on
    ``Item.name``), so the whole query runs anonymously.
    """
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    gid = str(
        relay.GlobalID(type_name=models.Category._meta.label_lower, node_id=str(category.pk)),
    )
    expected = [
        {"name": name}
        for name in models.Item.objects.filter(category=category)
        .order_by("name")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allItems(filter: {{ category: {{ id: {{ exact: "{gid}" }} }} }}, '
        "orderBy: [{ name: ASC }]) { name } }",
        {"allItems": expected},
    )
