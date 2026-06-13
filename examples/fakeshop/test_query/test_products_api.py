"""Live GraphQL HTTP tests for the products catalog API surface.

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
from apps.products.services import create_users, delete_data, seed_data
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
    response = _post_graphql("query { allItems { edges { node { id name } } } }")
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    nodes = [edge["node"] for edge in payload["data"]["allItems"]["edges"]]
    emitted = next(node for node in nodes if node["name"] == item.name)
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
    emit_response = _post_graphql("query { allItems { edges { node { id name } } } }")
    assert emit_response.status_code == 200
    emit_payload = emit_response.json()
    assert "errors" not in emit_payload, emit_payload
    emitted_nodes = [edge["node"] for edge in emit_payload["data"]["allItems"]["edges"]]
    emitted = next(node for node in emitted_nodes if node["name"] == target.name)
    emitted_id = emitted["id"]

    _assert_graphql_data(
        f'query {{ allItems(filter: {{ id: {{ exact: "{emitted_id}" }} }}) '
        "{ edges { node { id name } } } }",
        {"allItems": {"edges": [{"node": {"id": emitted_id, "name": target.name}}]}},
    )


@pytest.mark.django_db
def test_type_strategy_opt_out_reproduces_type_name():
    """``RELAY_GLOBALID_STRATEGY = "type"`` opts back into the GraphQL-type-name payload.

    Ordering matters here: the override is applied *before*
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
        response = _post_graphql("query { allItems { edges { node { id name } } } }")
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        nodes = [edge["node"] for edge in payload["data"]["allItems"]["edges"]]
        emitted = next(node for node in nodes if node["name"] == item.name)
        parsed = relay.GlobalID.from_id(emitted["id"])
        assert parsed.type_name == "ItemType"
        assert parsed.node_id == str(item.pk)


@pytest.mark.django_db
def test_products_optimizer_merges_duplicate_root_field_nodes_over_http():
    """Re-pinned through the connection wrapper: duplicate-root-field merge holds.

    The two `allItems` connection selections still merge into one node set
    (each `node` carries both `name` and `category { name }`), the root
    connection issues exactly ONE planned slice query carrying the
    `select_related("category")` JOIN, and NO COUNT runs (products declare no
    `Meta.connection`, so no `totalCount` field gates one). The appended
    deterministic `ORDER BY pk` is a no-op vs the old `.order_by("id")`
    (`id` IS the pk). Items = 25 at `seed_data(1)`, well under the default
    `relay_max_results` cap of 100.
    """
    seed_data(1)
    expected = [
        {"node": {"name": item.name, "category": {"name": item.category.name}}}
        for item in models.Item.objects.select_related("category").order_by("id")
    ]

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allItems { edges { node { name } } }
              allItems { edges { node { category { name } } } }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"] == {"allItems": {"edges": expected}}
    assert len(captured) == 1, [query["sql"] for query in captured]
    sql = captured[0]["sql"].lower()
    assert "products_item" in sql
    assert "join" in sql
    assert "products_category" in sql


@pytest.mark.django_db
def test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http():
    """Re-pinned through the connection wrapper: depth-2 reverse-FK prefetch holds.

    `allCategories` is now a connection (one planned categories slice query),
    but `items` and `entries` stay LIST relations (`{ name }`, not
    `itemsConnection`) - the depth-2 reverse-FK prefetch chain the test pins
    is unchanged: 1 categories slice + 1 `items` prefetch + 1 `entries`
    prefetch = 3 queries, no COUNT. List relations are not capped, so the
    full 25 categories / 25 items / 177 entries still come back; categories
    (25) is under the default `relay_max_results` cap of 100.
    """
    seed_data(1)
    assert models.Category.objects.count() < _RELAY_MAX_RESULTS, (
        "fixture must stay under the cap so the full-set assertion is not silently truncated"
    )

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allCategories {
                edges {
                  node {
                    name
                    items {
                      name
                      entries { value }
                    }
                  }
                }
              }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    categories = [edge["node"] for edge in payload["data"]["allCategories"]["edges"]]
    items = [item for category in categories for item in category["items"]]
    entries = [entry for item in items for entry in item["entries"]]
    assert len(categories) == models.Category.objects.count()
    assert len(items) == models.Item.objects.count()
    assert len(entries) == models.Entry.objects.count()
    assert len(captured) == 3, [query["sql"] for query in captured]
    assert "products_category" in captured[0]["sql"]
    assert "products_item" in captured[1]["sql"]
    assert "products_entry" in captured[2]["sql"]


# The connection caps an un-paginated default page (and any explicit ``first:``)
# at ``relay_max_results``; Strawberry rejects a ``first:`` above it outright.
# ``seed_data(1)`` produces 177 entries, OVER this cap, so the forward-FK
# depth-2 pin asserts the capped default page (the first ``RELAY_MAX_RESULTS``
# rows in deterministic pk order) rather than the full set (Decision 10's cap
# boundary). 100 is Strawberry's default ``StrawberryConfig.relay_max_results``;
# the fakeshop schema sets no override.
_RELAY_MAX_RESULTS = 100


@pytest.mark.django_db
def test_products_optimizer_selects_nested_forward_fk_depth_2_over_http():
    """Re-pinned through the connection wrapper: depth-2 forward-FK select_related holds.

    `allEntries` is now a connection: one planned slice query carrying
    `select_related("item__category")`, no COUNT. `seed_data(1)` produces 177
    entries - OVER the `relay_max_results` cap of 100 - and Strawberry rejects
    a `first:` above the cap, so the connection cannot return the full set.
    The pin therefore asserts the capped default page: the first
    `_RELAY_MAX_RESULTS` entries in deterministic pk order. The appended
    `ORDER BY pk` matches the ORM `.order_by("id")` (`id` IS the pk), so the
    emitted node order equals the expected ORM order; the SQL-shape contract
    (the depth-2 `select_related` JOIN in one query) is what this test fences.
    """
    seed_data(1)
    assert models.Entry.objects.count() > _RELAY_MAX_RESULTS, (
        "fixture must exceed the cap to exercise the capped-default-page boundary"
    )
    expected = [
        {
            "node": {
                "id": _global_id(models.Entry._meta.label_lower, entry.pk),
                "value": entry.value,
                "item": {
                    "id": _global_id(models.Item._meta.label_lower, entry.item_id),
                    "name": entry.item.name,
                    "category": {
                        "id": _global_id(
                            models.Category._meta.label_lower,
                            entry.item.category_id,
                        ),
                        "name": entry.item.category.name,
                    },
                },
            },
        }
        for entry in models.Entry.objects.select_related("item__category").order_by("id")[
            :_RELAY_MAX_RESULTS
        ]
    ]

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allEntries {
                edges {
                  node {
                    id
                    value
                    item {
                      id
                      name
                      category { id name }
                    }
                  }
                }
              }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"] == {"allEntries": {"edges": expected}}
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
        f"query {{ allCategories(filter: {{ name: {{ exact: {json.dumps(category.name)} }} }}) "
        "{ edges { node { name } } } }",
        {"allCategories": {"edges": [{"node": {"name": category.name}}]}},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_categories_filter_by_name_denied_for_anonymous():
    """An anonymous user filtering by ``Category.name`` (exact) is rejected by the gate."""
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    response = _post_graphql(
        f"query {{ allCategories(filter: {{ name: {{ exact: {json.dumps(category.name)} }} }}) "
        "{ edges { node { name } } } }",
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
        f"query {{ allCategories(filter: {{ name: {{ iContains: {json.dumps(category.name[:2])} }} }}) "
        "{ edges { node { name } } } }",
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
        f"query {{ allItems(filter: {{ category: {{ name: {{ exact: {json.dumps(category.name)} }} }} }}) "
        "{ edges { node { name } } } }",
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
        f"query {{ allCategories(filter: {{ id: {{ in: [{gids}] }} }}) "
        "{ edges { node { name } } } }",
        {
            "allCategories": {
                "edges": [{"node": {"name": category.name}} for category in categories],
            },
        },
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
        {"node": {"name": name}}
        for name in models.Category.objects.filter(name__startswith=prefix)
        .order_by("id")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allCategories(filter: {{ name: {{ startsWith: "{prefix}" }} }}) '
        "{ edges { node { name } } } }",
        {"allCategories": {"edges": expected}},
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
        {"node": {"name": name}}
        for name in models.Item.objects.filter(category=category)
        .order_by("id")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allItems(filter: {{ category: {{ id: {{ exact: "{gid}" }} }} }}) '
        "{ edges { node { name } } } }",
        {"allItems": {"edges": expected}},
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
        {"node": {"name": name}}
        for name in models.Item.objects.order_by("name").values_list("name", flat=True)
    ]
    _assert_graphql_data(
        "query { allItems(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
        {"allItems": {"edges": expected}},
    )


@pytest.mark.django_db
def test_products_items_order_by_name_desc():
    """``orderBy: [{ name: DESC }]`` sorts items by name descending."""
    seed_data(1)
    expected = [
        {"node": {"name": name}}
        for name in models.Item.objects.order_by("-name").values_list("name", flat=True)
    ]
    _assert_graphql_data(
        "query { allItems(orderBy: [{ name: DESC }]) { edges { node { name } } } }",
        {"allItems": {"edges": expected}},
    )


@pytest.mark.django_db
def test_products_categories_order_by_name_denied_for_anonymous():
    """``CategoryOrder.check_name_permission`` rejects an anonymous order-by-name.

    Active-input-only: the gate fires because the ``orderBy`` input names the
    gated ``name`` field - mirroring ``CategoryFilter.check_name_permission``
    on the filter side.
    """
    seed_data(1)
    response = _post_graphql(
        "query { allCategories(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_categories_order_by_name_as_staff():
    """A staff user clears the order-by-name gate and gets categories sorted by name."""
    seed_data(1)
    expected = [
        {"node": {"name": name}}
        for name in models.Category.objects.order_by("name").values_list("name", flat=True)
    ]
    _assert_graphql_data(
        "query { allCategories(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
        {"allCategories": {"edges": expected}},
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
            edges { node { name } }
          }
        }
        """,
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_items_order_by_related_category_name_as_staff():
    """Nested ``RelatedOrder`` input sorts by the child order field.

    Each item's category is distinct (one item per category at
    ``seed_data(1)``) and category names are unique provider names, so
    ``category__name`` is a total order and the connection's appended
    deterministic ``ORDER BY pk`` tiebreaker is a no-op against the ORM
    ``order_by("category__name")`` expectation.
    """
    seed_data(1)
    expected = [
        {"node": {"name": item.name, "category": {"name": item.category.name}}}
        for item in models.Item.objects.select_related("category").order_by("category__name")
    ]
    _assert_graphql_data(
        """
        query {
          allItems(orderBy: [{ category: { name: ASC } }]) {
            edges { node { name category { name } } }
          }
        }
        """,
        {"allItems": {"edges": expected}},
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
        {"node": {"name": name}}
        for name in models.Item.objects.filter(category=category)
        .order_by("name")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allItems(filter: {{ category: {{ id: {{ exact: "{gid}" }} }} }}, '
        "orderBy: [{ name: ASC }]) { edges { node { name } } } }",
        {"allItems": {"edges": expected}},
    )


# ---------------------------------------------------------------------------
# Nested relation-connection windowed-prefetch coverage (spec-033 Slice 6,
# DoD item 10). The reverse-FK windowed nested-connection shape the M2M-only
# library graph cannot express live: ``Category.items`` synthesizes an
# ``itemsConnection`` sibling (both ``CategoryType`` and ``ItemType`` are
# Relay-Node-shaped, so the ``DONE-032-0.0.9`` implicit ``"both"`` default made
# it), and Slices 1-2 plan it as a single windowed ``Prefetch``.
# ---------------------------------------------------------------------------

# itemsConnection carries ONLY ``first:`` -- a ``filter:`` / ``orderBy:`` sidecar
# on a NESTED connection diverts it to the per-parent fallback (Decision 6),
# which would issue one query per parent category (count scaling with parent
# cardinality) instead of the single windowed prefetch. Selecting only ``first:``
# pins the windowed path.
_CATEGORIES_ITEMS_CONNECTION_QUERY = """
query {
  allCategories {
    edges {
      node {
        name
        itemsConnection(first: 2) {
          edges { node { name } }
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
def test_products_categories_items_connection_fixed_query_count():
    """The nested reverse-FK ``itemsConnection`` resolves in a FIXED query count.

    Runs the same ``allCategories { edges { node { itemsConnection(first: 2)
    { edges { node } } } } }`` query under two seed cardinalities and asserts
    the captured query count is EQUAL (and absolutely small) across both -- the
    N+1 disproof. The windowed path is a FIXED 2 queries (one ``allCategories``
    slice + one windowed ``itemsConnection`` prefetch covering every category's
    page). A per-parent fallback issues at least one query per parent and scales
    with the number of ITEMS under ``first: 2`` (measured ~52 queries at
    ``seed_data(1)`` and ~102 at ``seed_data(3)``), so it neither stays equal
    across the two seedings nor lands at 2. Both seedings hold 25 parent
    categories fixed and grow items-per-category, so the equality rules out a
    per-child N+1 and the absolute ``== 2`` rules out the item-scaling fallback.

    ``itemsConnection`` carries only ``first:`` (no sidecars) so it window-plans
    rather than falling back (Decision 6). At ``seed_data(3)`` each category has
    3 items and ``first: 2`` returns a true 2-item sub-page, proving the window
    is per-parent-correct rather than one shared slice. Both seedings stay well
    under the ``relay_max_results`` cap (25 categories).
    """

    def _run(seed_count: int) -> int:
        delete_data("everything")
        seed_data(seed_count)
        with CaptureQueriesContext(connection) as captured:
            response = _post_graphql(_CATEGORIES_ITEMS_CONNECTION_QUERY)
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        edges = payload["data"]["allCategories"]["edges"]
        # Each category node's itemsConnection is its OWN windowed page: every
        # returned item belongs to that category and the page honours first: 2.
        for edge in edges:
            node = edge["node"]
            category = models.Category.objects.get(name=node["name"])
            item_names = {ie["node"]["name"] for ie in node["itemsConnection"]["edges"]}
            assert len(item_names) <= 2
            assert item_names <= set(
                category.items.values_list("name", flat=True),
            )
        return len(captured)

    one_item_each = _run(1)
    three_items_each = _run(3)

    # Load-bearing: count is equal across the two parent cardinalities (no N+1).
    assert one_item_each == three_items_each
    # Strengthening: the empirically-derived windowed fixed count (1 allCategories
    # slice query + 1 windowed itemsConnection prefetch); a fallback issues at
    # least one query per parent and scales with items (measured ~52 / ~102 here).
    assert three_items_each == 2


# Slice 6 (spec-033) deliberately adds NO Meta.connection opt-in on the four
# products types (no totalCount; minimal cookbook-mirror conversion) and NO root
# node(id:) / nodes(ids:) entry points (those stay TODO-BETA-051-0.1.5).
