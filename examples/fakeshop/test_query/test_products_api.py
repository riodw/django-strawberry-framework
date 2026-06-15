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

    Runs as ``staff_1`` so the first item is visible regardless of its
    (``seed_data``-randomized) ``is_private`` / category privacy under the
    activated cascade hooks (spec-034 Slice 4); the GlobalID emit/decode subject
    is orthogonal to visibility.
    """
    seed_data(1)
    client = _staff_client()
    item = models.Item.objects.order_by("id").first()
    response = _post_graphql(
        "query { allItems { edges { node { id name } } } }",
        client=client,
    )
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

    Runs as ``staff_1`` so the target item is visible for both the emit and the
    filter-round-trip under the activated cascade hooks (spec-034 Slice 4); the
    emit -> filter symmetry subject is orthogonal to visibility.
    """
    seed_data(1)
    client = _staff_client()
    target = models.Item.objects.order_by("id").first()
    emit_response = _post_graphql(
        "query { allItems { edges { node { id name } } } }",
        client=client,
    )
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
        client=client,
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

    Runs as ``staff_1`` so the first item is visible regardless of its
    (``seed_data``-randomized) privacy under the activated cascade hooks
    (spec-034 Slice 4); the strategy opt-out subject is orthogonal to visibility.
    """
    seed_data(1)
    client = _staff_client()
    item = models.Item.objects.order_by("id").first()
    with override_settings(
        DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"},
    ):
        _reload_products_project_schema()
        response = _post_graphql(
            "query { allItems { edges { node { id name } } } }",
            client=client,
        )
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

    The two `allItems` connection selections still merge into one node set (each
    `node` carries both `name` and `category { name }`) issuing exactly ONE
    `allItems` slice query, and NO COUNT runs (products declare no
    `Meta.connection`). Under the activated cascade hooks (spec-034 Slice 4) the
    forward FK `item.category` no longer plans `select_related` - `CategoryType`
    now defines a custom `get_queryset`, so the optimizer downgrades it to a
    windowed `Prefetch` (the shipped `get_queryset` -> `Prefetch` rule). The
    merged shape is therefore a deterministic 2 products queries - one `allItems`
    slice + one `category` prefetch, no inter-products JOIN - and an unmerged
    shape would issue two item slices instead of one. Run anonymously (no auth
    queries pollute the count); the cascade narrows rows to the anonymously
    visible set (public items under public categories), so the expected rows are
    derived from the equivalent post-cascade ORM query (API == ORM), keeping the
    pin robust across `seed_data`'s random Item privacy. The appended
    deterministic `ORDER BY pk` matches `.order_by("id")` (`id` IS the pk).
    """
    seed_data(1)
    expected = [
        {"node": {"name": item.name, "category": {"name": item.category.name}}}
        for item in models.Item.objects.select_related("category")
        .filter(is_private=False, category__is_private=False)
        .order_by("id")
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
    # One allItems slice (the merge) + one category Prefetch (the hook downgrade),
    # no COUNT, no inter-products JOIN.
    assert len(captured) == 2, [query["sql"] for query in captured]
    item_slices = [q for q in captured if "products_item" in q["sql"].lower()]
    assert len(item_slices) == 1, [q["sql"] for q in captured]
    assert any("products_category" in q["sql"].lower() for q in captured)
    assert not any(
        "products_item" in q["sql"].lower()
        and "products_category" in q["sql"].lower()
        and "join" in q["sql"].lower()
        for q in captured
    )


@pytest.mark.django_db
def test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http():
    """Re-pinned through the connection wrapper: depth-2 reverse-FK prefetch holds.

    `allCategories` is a connection (one planned categories slice query), and
    `items` / `entries` stay LIST relations (`{ name }`, not `itemsConnection`)
    - the depth-2 reverse-FK prefetch chain the test pins is structurally
    unchanged: 1 categories slice + 1 `items` prefetch + 1 `entries` prefetch =
    3 queries, no COUNT. The activated cascade hooks (spec-034 Slice 4) do NOT
    add per-row queries - their `__in` subqueries compile inline (Decision 7) -
    so the count stays a fixed 3.

    What the cascade DOES change is row VISIBILITY: run anonymously, the three
    levels narrow to the cascade-visible set (public categories; non-private
    items under them; entries passing the full Entry -> Item -> Category /
    Entry -> Property -> Category chain). Counts are therefore derived from the
    equivalent post-cascade ORM queries (API == ORM), keeping the pin robust
    across `seed_data`'s random Item/Entry privacy. The deterministic Category
    `% 2` split keeps the public-category count well under the
    `relay_max_results` cap.
    """
    seed_data(1)
    visible_categories = models.Category.objects.filter(is_private=False)
    visible_items = models.Item.objects.filter(is_private=False, category__is_private=False)
    visible_entries = models.Entry.objects.filter(
        is_private=False,
        item__is_private=False,
        item__category__is_private=False,
        property__is_private=False,
        property__category__is_private=False,
    )
    assert visible_categories.count() < _RELAY_MAX_RESULTS, (
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
    assert len(categories) == visible_categories.count()
    assert len(items) == visible_items.count()
    assert len(entries) == visible_entries.count()
    assert len(captured) == 3, [query["sql"] for query in captured]
    assert "products_category" in captured[0]["sql"]
    assert "products_item" in captured[1]["sql"]
    assert "products_entry" in captured[2]["sql"]


# The connection caps an un-paginated default page (and any explicit ``first:``)
# at ``relay_max_results``; Strawberry rejects a ``first:`` above it outright.
# 100 is Strawberry's default ``StrawberryConfig.relay_max_results``; the fakeshop
# schema sets no override. Used by the staff full-set cascade pin (staff sees all
# rows, capped at 100) and the reverse-FK depth-2 pin's under-cap precondition.
# The forward-FK depth-2 pin below runs anonymously under the activated cascade
# (spec-034 Slice 4): the cascade narrows the visible entry set well under the
# cap, so that pin no longer exercises the cap boundary.
_RELAY_MAX_RESULTS = 100


@pytest.mark.django_db
def test_products_optimizer_selects_nested_forward_fk_depth_2_over_http():
    """Re-pinned for the activated cascade: depth-2 forward-FK plans a Prefetch chain.

    Before spec-034 Slice 4 this query planned a single `select_related(
    "item__category")` JOIN. With the cascade hooks active, `ItemType` and
    `CategoryType` both define a custom `get_queryset`, so the optimizer
    downgrades each forward FK in the `item -> category` chain to a windowed
    `Prefetch` (the shipped `get_queryset` -> `Prefetch` rule). The traversal is
    therefore a deterministic 3 products queries - one `allEntries` slice + one
    `item` prefetch + one `category` prefetch - with NO inter-products JOIN, and
    the cascade adds zero round-trips (its `__in` subqueries compile inline,
    Decision 7). Run anonymously (no auth queries pollute the count); the cascade
    narrows the visible entries to those passing the full
    Entry -> Item -> Category / Entry -> Property -> Category chain, well under the
    `relay_max_results` cap, so the expected page is the entire visible set in pk
    order, derived from the equivalent post-cascade ORM query (API == ORM, robust
    across `seed_data`'s random Item/Entry/Property privacy). The appended
    `ORDER BY pk` matches `.order_by("id")` (`id` IS the pk).
    """
    seed_data(1)
    visible_entries = (
        models.Entry.objects.select_related("item__category")
        .filter(
            is_private=False,
            item__is_private=False,
            item__category__is_private=False,
            property__is_private=False,
            property__category__is_private=False,
        )
        .order_by("id")
    )
    assert visible_entries.count() <= _RELAY_MAX_RESULTS, (
        "cascade-narrowed visible set must stay under the cap for the full-set assertion"
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
        for entry in visible_entries
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
    # Prefetch chain: entry slice + item prefetch + category prefetch, no COUNT.
    assert len(captured) == 3, [query["sql"] for query in captured]
    assert "products_entry" in captured[0]["sql"]
    assert "products_item" in captured[1]["sql"]
    assert "products_category" in captured[2]["sql"]
    # The cascade composed inline (zero added round-trips) and the forward FK
    # downgraded to a Prefetch chain rather than a select_related JOIN.
    all_sql = " ".join(query["sql"] for query in captured)
    assert "IN (SELECT" in all_sql
    assert not any(
        "products_entry" in q["sql"].lower()
        and "products_item" in q["sql"].lower()
        and "join" in q["sql"].lower()
        for q in captured
    )


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

    Picks two PUBLIC categories so they are visible under the activated cascade
    (spec-034 Slice 4) - anonymous sees only `is_private=False` categories (the
    deterministic `% 2` split makes ~half private), and the GlobalID `in`-decode
    subject is orthogonal to which specific rows are chosen.
    """
    seed_data(1)
    categories = list(models.Category.objects.filter(is_private=False).order_by("id")[:2])
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
    """``Item.category`` ``RelatedFilter`` traversal via the nested GlobalID input.

    Filters to a PUBLIC category (visible anonymously under the activated cascade,
    spec-034 Slice 4). The cascade narrows the anonymous result to that category's
    ``is_private=False`` items, so the expected rows are derived from the
    equivalent post-cascade ORM query (API == ORM) - the ``RelatedFilter`` content
    subject composed with the cascade's row narrowing.
    """
    seed_data(1)
    category = models.Category.objects.filter(is_private=False).order_by("id").first()
    gid = str(
        relay.GlobalID(type_name=models.Category._meta.label_lower, node_id=str(category.pk)),
    )
    expected = [
        {"node": {"name": name}}
        for name in models.Item.objects.filter(category=category, is_private=False)
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
    """``orderBy: [{ name: ASC }]`` sorts items by name ascending (Item has no order gate).

    Runs anonymously, so the activated cascade (spec-034 Slice 4) narrows to
    non-private items under non-private categories before ordering; the expected
    rows are derived from the equivalent post-cascade ORM query (API == ORM), the
    ordering subject composed with the cascade's row narrowing.
    """
    seed_data(1)
    expected = [
        {"node": {"name": name}}
        for name in models.Item.objects.filter(is_private=False, category__is_private=False)
        .order_by("name")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        "query { allItems(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
        {"allItems": {"edges": expected}},
    )


@pytest.mark.django_db
def test_products_items_order_by_name_desc():
    """``orderBy: [{ name: DESC }]`` sorts items by name descending.

    Anonymous, so the cascade-narrowed visible set (non-private items under
    non-private categories) is ordered; expected rows come from the equivalent
    post-cascade ORM query (spec-034 Slice 4).
    """
    seed_data(1)
    expected = [
        {"node": {"name": name}}
        for name in models.Item.objects.filter(is_private=False, category__is_private=False)
        .order_by("-name")
        .values_list("name", flat=True)
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

    Uses a PUBLIC category (visible anonymously) and derives the expected rows
    from the equivalent post-cascade ORM query - the activated cascade (spec-034
    Slice 4) narrows the anonymous result to that category's ``is_private=False``
    items, on top of which the filter -> order chain runs.
    """
    seed_data(1)
    category = models.Category.objects.filter(is_private=False).order_by("id").first()
    gid = str(
        relay.GlobalID(type_name=models.Category._meta.label_lower, node_id=str(category.pk)),
    )
    expected = [
        {"node": {"name": name}}
        for name in models.Item.objects.filter(category=category, is_private=False)
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
    with the number of ITEMS under ``first: 2``, so it neither stays equal across
    the two seedings nor lands at 2. Both seedings hold the parent-category count
    fixed and grow items-per-category, so the equality rules out a per-child N+1
    and the absolute ``== 2`` rules out the item-scaling fallback.

    Under the activated cascade (spec-034 Slice 4) this query runs anonymously,
    so the cascade narrows the result to the public categories (the deterministic
    ``% 2`` split, ~half of the seeded providers) and the windowed
    ``itemsConnection`` prefetch child carries ``ItemType``'s cascade too (only
    non-private items). That is exactly the interaction this pin must prove
    query-stable: the cascade's ``__in`` subqueries compile inline (Decision 7),
    so the count stays a FIXED 2 even with the hooks active. The membership check
    confirms each returned ``itemsConnection`` page is its own parent's window
    (every returned item belongs to that category, ``first: 2`` honoured).

    ``itemsConnection`` carries only ``first:`` (no sidecars) so it window-plans
    rather than falling back (Decision 6). Both seedings stay well under the
    ``relay_max_results`` cap.
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


# =============================================================================
# Live cascade-permission HTTP coverage (spec-034 Slice 4). The four products
# get_queryset hooks are now active in apps/products/schema.py. Real permission
# users only - every test's FIRST line is `create_users(1)` (per AGENTS.md / card
# DoD: never mock info.context.user). Exercises the 2-deep
# Entry -> Item -> Category / Entry -> Property -> Category chain.
#
# Each test seeds the private/public split it needs as a dedicated ORM chain
# AFTER `create_users(1)` / `seed_data(N)`, so the assertions are deterministic
# regardless of `seed_data`'s random Item/Entry `is_private` assignment (the
# Category/Property split is the deterministic `% 2` alternation; Item/Entry are
# `random.choice`). The hooks resolve the user from `info.context.request.user`
# (the Strawberry-Django context shape; see schema.py), so these run real logins.
# =============================================================================


def _login(username: str) -> Client:
    """Log in a seeded ``create_users(1)`` user by username."""
    client = Client()
    client.force_login(get_user_model().objects.get(username=username))
    return client


def _seed_cascade_split():
    """Build a deterministic private/public 2-deep chain and return the key rows.

    Two parallel chains so the cascade's per-edge narrowing is observable:

    * a PRIVATE category holding a PUBLIC item carrying a PUBLIC entry (via a
      PUBLIC property under the same private category) - everything below the
      category is public, so only the category's privacy can hide the entry;
    * a PUBLIC category holding a PUBLIC item carrying a PUBLIC entry (a fully
      visible control chain).

    Hand-created (not ``seed_data``) so Item/Entry privacy is fixed, not random.
    """
    private_cat = models.Category.objects.create(name="zzz_private_cat", is_private=True)
    public_cat = models.Category.objects.create(name="zzz_public_cat", is_private=False)

    priv_prop = models.Property.objects.create(
        name="priv_prop",
        category=private_cat,
        is_private=False,
    )
    pub_prop = models.Property.objects.create(
        name="pub_prop",
        category=public_cat,
        is_private=False,
    )

    item_under_private = models.Item.objects.create(
        name="zzz_item_under_private",
        category=private_cat,
        is_private=False,
    )
    item_under_public = models.Item.objects.create(
        name="zzz_item_under_public",
        category=public_cat,
        is_private=False,
    )

    entry_under_private = models.Entry.objects.create(
        value="zzz_entry_under_private",
        property=priv_prop,
        item=item_under_private,
        is_private=False,
    )
    entry_under_public = models.Entry.objects.create(
        value="zzz_entry_under_public",
        property=pub_prop,
        item=item_under_public,
        is_private=False,
    )
    return {
        "private_cat": private_cat,
        "public_cat": public_cat,
        "priv_prop": priv_prop,
        "pub_prop": pub_prop,
        "item_under_private": item_under_private,
        "item_under_public": item_under_public,
        "entry_under_private": entry_under_private,
        "entry_under_public": entry_under_public,
    }


@pytest.mark.django_db
def test_cascade_anonymous_sees_no_entries_under_private_categories():
    """The 2-deep live pin: a private Category hides its Items' Entries from anonymous.

    Seeds a private Category with a public Item carrying a public Entry (via a
    public Property under that same private Category); an anonymous
    ``allEntries`` request returns no entry whose item's category is private -
    the cascade reaches Entry -> Item -> Category. The fully-public control entry
    IS returned, proving narrowing (not a blanket empty result).
    """
    create_users(1)
    chain = _seed_cascade_split()

    response = _post_graphql(
        """
        query {
          allEntries {
            edges { node { value item { name category { name } } } }
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    nodes = [edge["node"] for edge in payload["data"]["allEntries"]["edges"]]
    category_names = {node["item"]["category"]["name"] for node in nodes}
    values = {node["value"] for node in nodes}
    # The cascade hides the entry whose item's category is private...
    assert chain["private_cat"].name not in category_names
    assert chain["entry_under_private"].value not in values
    # ...but the fully-public control entry is still visible (narrowing, not empty).
    assert chain["entry_under_public"].value in values


@pytest.mark.django_db
def test_cascade_view_item_user_matrix():
    """The ``view_item`` user keeps non-private items; the entry drop is via ``property``, not ``item``.

    Per-edge composition. ``ItemType``'s ``view_item`` branch returns all
    non-private items with NO cascade, so the ``Entry -> item -> Category`` path
    is short-circuited for this user: an entry is never dropped by its ``item``
    edge, even when that item sits under a private category. The drop the user
    still sees comes from the ``property`` edge - holding no ``view_property``
    perm, ``PropertyType``'s cascade hides the property under the private
    category, so ``Q(property__in=visible) | Q(property__isnull=True)`` excludes
    ``entry_under_private`` (whose property is the private-category ``priv_prop``).
    The isolating ``entry_item_private`` below - a public item under the private
    category, paired with the fully public ``pub_prop`` - SURVIVES, pinning that
    the live drop is through ``property`` and the ``item`` edge does not cascade
    for this user (the two root fields disagree by design). Both edges of
    ``entry_under_private`` point at the private category, so it alone cannot
    distinguish the two paths - the isolating entry is what makes the claim testable.
    """
    create_users(1)
    chain = _seed_cascade_split()
    client = _login("view_item_1")

    # Isolating fixture for the per-edge claim: an entry whose ONLY private
    # linkage is its item's category (the item itself is public, just under the
    # private category), paired with a fully public property. For a view_item
    # user the item edge does not cascade into Category and the property edge
    # keeps it, so this entry must SURVIVE - which entry_under_private (private on
    # both edges) cannot prove.
    entry_item_private = models.Entry.objects.create(
        value="zzz_entry_item_private_prop_public",
        item=chain["item_under_private"],
        property=chain["pub_prop"],
        is_private=False,
    )

    # allItems: the view_item rule shows the (public) item even under a private cat.
    items_response = _post_graphql(
        "query { allItems { edges { node { name } } } }",
        client=client,
    )
    assert items_response.status_code == 200
    items_payload = items_response.json()
    assert "errors" not in items_payload, items_payload
    item_names = {edge["node"]["name"] for edge in items_payload["data"]["allItems"]["edges"]}
    assert chain["item_under_private"].name in item_names
    assert chain["item_under_public"].name in item_names

    # allEntries: the root-field cascade still drops the entry under the hidden cat.
    # Select only `value` - this test pins which entries the root field returns
    # (the per-edge drop), not nested traversal. (A surviving entry's item can sit
    # under a hidden category, and `item { category }` on a non-null FK to a
    # hidden target raises - an orthogonal nested-resolution concern, not M1's.)
    entries_response = _post_graphql(
        "query { allEntries { edges { node { value } } } }",
        client=client,
    )
    assert entries_response.status_code == 200
    entries_payload = entries_response.json()
    assert "errors" not in entries_payload, entries_payload
    entry_nodes = [edge["node"] for edge in entries_payload["data"]["allEntries"]["edges"]]
    entry_values = {node["value"] for node in entry_nodes}
    assert chain["entry_under_private"].value not in entry_values
    assert chain["entry_under_public"].value in entry_values
    # The isolating entry survives: its item is public (the view_item branch does
    # not cascade the item edge into Category) and its property is public, so no
    # edge can drop it. This is the per-edge contract the "through item" docstring
    # could not actually pin.
    assert entry_item_private.value in entry_values


@pytest.mark.django_db
def test_cascade_staff_sees_everything():
    """A staff user (``create_users`` makes ``staff_<n>`` is_staff, NOT is_superuser) bypasses the cascade.

    Staff hits the ``user.is_staff`` short-circuit in every hook, so the visible
    counts equal the full ORM counts (capped at ``_RELAY_MAX_RESULTS`` for the
    connection page). Asserts against the seeded full set, including the private
    rows the cascade would hide for anyone else.
    """
    create_users(1)
    seed_data(1)
    _seed_cascade_split()
    client = _login("staff_1")

    for field, model in (("allCategories", models.Category), ("allItems", models.Item)):
        response = _post_graphql(
            f"query {{ {field} {{ edges {{ node {{ id }} }} }} }}",
            client=client,
        )
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        returned = len(payload["data"][field]["edges"])
        expected = min(model.objects.count(), _RELAY_MAX_RESULTS)
        assert returned == expected, (field, returned, expected)

    # Sanity: staff sees the private-chain rows that the cascade hides for others.
    assert models.Category.objects.filter(is_private=True).exists()
    assert models.Category.objects.count() <= _RELAY_MAX_RESULTS


@pytest.mark.django_db
def test_cascade_query_count_fixed():
    """``allEntries { value item { name category { name } } }`` runs in a FIXED query count.

    The cascade adds zero round-trips - the ``__in`` subqueries compile inline as
    nested ``SELECT``s (Decision 7). Because ``EntryType`` cascades through
    ``item`` to the custom-hooked ``ItemType`` / ``CategoryType``, the optimizer
    downgrades the forward-FK ``select_related`` to a windowed ``Prefetch`` chain
    (the shipped ``get_queryset`` -> ``Prefetch`` rule; spec-034 Slice 2). The
    anonymous request issues no auth queries, so the products query count is a
    deterministic 3 (one entry slice + one ``item`` prefetch + one ``category``
    prefetch), independent of how ``seed_data`` randomized row privacy. The
    cascade's nested ``IN (SELECT`` subqueries appear in the SQL, so the test
    cannot pass on a fall-through that skipped the cascade.
    """
    create_users(1)
    seed_data(1)
    _seed_cascade_split()

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            "query { allEntries { edges { node { value item { name category { name } } } } } }",
        )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    # Fixed, structurally deterministic: entry slice + item prefetch + category
    # prefetch (forward-FK select_related downgraded to Prefetch by the hooks).
    assert len(captured) == 3, [query["sql"] for query in captured]
    all_sql = " ".join(query["sql"] for query in captured)
    # Cascade composed its subqueries inline (zero added round-trips), not a
    # fall-through that skipped the cascade.
    assert "IN (SELECT" in all_sql
    # The forward chain plans as a Prefetch chain, NOT a select_related JOIN
    # across products tables (the hook-presence downgrade).
    assert not any(
        "products_entry" in query["sql"]
        and "products_item" in query["sql"]
        and "JOIN" in query["sql"].upper()
        for query in captured
    )


@pytest.mark.django_db
def test_cascade_composes_with_filter_and_order_live():
    """``filter:`` + ``orderBy:`` + cascade in one request; ``check_name_permission`` keeps firing.

    Two shapes per Decision 11 (cascade narrows rows, gates judge input):

    (a) a gated-field input (anonymous ``allCategories(orderBy: [{ name: ASC }])``)
        still raises the ``check_name_permission`` "staff user" error - the gate
        fires on input shape, independent of the cascade;
    (b) a non-gated anonymous composing request
        (``allItems(filter: { category: { id: { exact: <public-cat> } } }, orderBy: [{ name: ASC }])``)
        narrows first to the cascade-visible set (anonymous sees only non-private
        items under non-private categories) then filters + orders the survivors,
        matching the equivalent post-cascade ORM query.
    """
    create_users(1)
    seed_data(1)

    # (a) the gate fires on the gated order input, regardless of cascade.
    gated = _post_graphql(
        "query { allCategories(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
    )
    gated_payload = gated.json()
    assert "errors" in gated_payload, gated_payload
    assert "staff user" in gated_payload["errors"][0]["message"]

    # (b) anonymous filter (no gate on `id`) + order (no gate on Item.name) on top
    # of the cascade-narrowed set: the public category's non-private items, ordered
    # by name. Derived from the equivalent post-cascade ORM query (API == ORM).
    category = models.Category.objects.filter(is_private=False).order_by("id").first()
    gid = str(
        relay.GlobalID(type_name=models.Category._meta.label_lower, node_id=str(category.pk)),
    )
    expected = [
        {"node": {"name": name}}
        for name in models.Item.objects.filter(category=category, is_private=False)
        .order_by("name")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allItems(filter: {{ category: {{ id: {{ exact: "{gid}" }} }} }}, '
        "orderBy: [{ name: ASC }]) { edges { node { name } } } }",
        {"allItems": {"edges": expected}},
    )
