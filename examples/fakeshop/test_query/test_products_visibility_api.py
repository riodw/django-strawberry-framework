"""Live GraphQL proof that generated relations enforce target visibility themselves."""

import json

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import AsyncClient, Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches, path
from graphql_client import assert_graphql_success
from strawberry import relay
from strawberry.django.views import GraphQLView

from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.views import AsyncDjangoGraphQLView

_CURRENT: dict[str, object | None] = {"schema": None}


def _graphql_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    return GraphQLView.as_view(schema=schema)(request)


async def _async_graphql_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql/", _graphql_view), path("graphql-async/", _async_graphql_view)]


def test_unoptimized_relation_hides_private_child_over_http(db):
    services.seed_data(1)
    category = Category.objects.first()
    assert category is not None
    item = Item.objects.filter(category=category).first()
    assert item is not None
    Item.objects.filter(pk=item.pk).update(is_private=True)

    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return Category.objects.filter(pk=category.pk)

    _CURRENT["schema"] = strawberry.Schema(query=Query)
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            response = Client().post(
                "/graphql/",
                data='{"query":"{ categories { items { name } } }"}',
                content_type="application/json",
            )
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("errors") is None, payload
        assert payload["data"] == {"categories": [{"items": []}]}
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


def _build_async_visibility_schema():
    category = Category.objects.first()
    assert category is not None
    item = Item.objects.filter(category=category).first()
    assert item is not None
    Item.objects.filter(pk=item.pk).update(is_private=True)

    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        async def categories(self) -> list[CategoryType]:
            return await sync_to_async(list)(
                Category.objects.filter(pk=category.pk),
            )

    return strawberry.Schema(query=Query)


async def _post_async_visibility_query():
    schema = await sync_to_async(_build_async_visibility_schema)()
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            return await AsyncClient().post(
                "/graphql-async/",
                data='{"query":"{ categories { items { name } } }"}',
                content_type="application/json",
            )
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


@pytest.mark.django_db(transaction=True)
async def test_async_unoptimized_relation_hides_private_child_over_http():
    await sync_to_async(services.seed_data)(1)
    response = await _post_async_visibility_query()
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("errors") is None, payload
    assert payload["data"] == {"categories": [{"items": []}]}


def _post_visibility_query(schema, query):
    """POST ``query`` against ``schema`` over live HTTP and return the JSON payload."""
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            response = Client().post(
                "/graphql/",
                data=json.dumps({"query": query}),
                content_type="application/json",
            )
        assert response.status_code == 200
        return response.json()
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


def test_consumer_prefetch_cache_is_rescoped_with_the_optimizer_installed(db):
    """A cache the CONSUMER prefetched is unscoped even while the optimizer runs.

    ``prefetch_related`` on a consumer-owned root queryset never passes through
    the target type's ``get_queryset``, and an installed optimizer says nothing
    about a relation it did not plan. Trusting the request-wide presence of an
    optimizer served the private row here; the per-relation planned-key check
    re-reads it through the visibility boundary. Asserted as parity against the
    same schema with no optimizer, which is the reference behavior.
    """
    services.seed_data(1)
    category = Category.objects.first()
    assert category is not None
    item = Item.objects.filter(category=category).first()
    assert item is not None
    Item.objects.filter(pk=item.pk).update(is_private=True)

    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return list(Category.objects.filter(pk=category.pk).prefetch_related("items"))

    query = "{ categories { items { name isPrivate } } }"
    optimizer = DjangoOptimizerExtension()
    optimized = _post_visibility_query(
        strawberry.Schema(query=Query, extensions=[lambda: optimizer]),
        query,
    )
    unoptimized = _post_visibility_query(strawberry.Schema(query=Query), query)
    assert optimized.get("errors") is None, optimized
    assert optimized["data"] == {"categories": [{"items": []}]}
    assert optimized["data"] == unoptimized["data"]


def test_forward_fk_target_visibility_holds_with_the_optimizer_installed(db):
    """A hidden forward-FK target stays hidden for a relation the walker never planned.

    The optimizer cannot plan a root that hands back a plain list, so the FK
    below lazy-loads unscoped. The non-null ``category`` field then fails loudly
    rather than emitting a row ``CategoryType.get_queryset`` excludes - the same
    outcome the no-optimizer schema produces.
    """
    services.seed_data(1)
    item = Item.objects.first()
    assert item is not None
    Category.objects.filter(pk=item.category_id).update(is_private=True)

    from apps.products.schema import ItemType

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self) -> list[ItemType]:
            return list(Item.objects.filter(pk=item.pk))

    query = "{ items { name category { name } } }"
    optimizer = DjangoOptimizerExtension()
    optimized = _post_visibility_query(
        strawberry.Schema(query=Query, extensions=[lambda: optimizer]),
        query,
    )
    unoptimized = _post_visibility_query(strawberry.Schema(query=Query), query)
    assert optimized["data"] is None
    assert [error["message"] for error in optimized["errors"]] == [
        "Cannot return null for non-nullable field ItemType.category.",
    ]
    assert optimized["errors"] == unoptimized["errors"]


def _build_async_forward_fk_schema():
    """Schema whose async root select_relateds the FK, so it loads WITHOUT a query.

    The visibility re-check needs the related object in hand, and a forward-FK
    lazy load is a ``SynchronousOnlyOperation`` inside an async execution - so a
    consumer ``select_related`` is what puts an UNSCOPED target on this path:
    the JOIN never consulted ``CategoryType.get_queryset``.
    """
    item = Item.objects.first()
    assert item is not None
    Category.objects.filter(pk=item.category_id).update(is_private=True)

    from apps.products.schema import ItemType

    @strawberry.type
    class Query:
        @strawberry.field
        async def items(self) -> list[ItemType]:
            return await sync_to_async(list)(
                Item.objects.filter(pk=item.pk).select_related("category"),
            )

    return strawberry.Schema(query=Query)


@pytest.mark.django_db(transaction=True)
async def test_async_forward_fk_target_visibility_hides_a_private_target_over_http():
    """The async single-object visibility re-check runs on a real async request.

    ``_visible_related_object`` takes its ``await``-ing branch here, and a hidden
    non-null ``category`` fails loudly rather than resolving the excluded row a
    consumer JOIN pulled in.
    """
    await sync_to_async(services.seed_data)(1)
    schema = await sync_to_async(_build_async_forward_fk_schema)()
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            response = await AsyncClient().post(
                "/graphql-async/",
                data=json.dumps({"query": "{ items { name category { name } } }"}),
                content_type="application/json",
            )
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] is None
    assert [error["message"] for error in payload["errors"]] == [
        "Cannot return null for non-nullable field ItemType.category.",
    ]


#: One nested-connection document, posted against holder schemas that differ only
#: in how many parent rows their root resolver hands back.
_NESTED_CONNECTION_QUERY = (
    "{ categories { itemsConnection(first: 2) { edges { node { name } } } } }"
)


def _nested_connection_item_queries(parent_count):
    """Post ``_NESTED_CONNECTION_QUERY`` at ``parent_count`` parents; return the item SQL.

    The holder schema installs NO ``DjangoOptimizerExtension``, so the nested
    connection runs off the relation manager rather than a planned window.
    """
    parent_pks = list(
        Category.objects.order_by("pk").values_list("pk", flat=True)[:parent_count],
    )
    assert len(parent_pks) == parent_count

    from apps.products.schema import CategoryType

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return list(Category.objects.filter(pk__in=parent_pks).order_by("pk"))

    with CaptureQueriesContext(connection) as captured:
        payload = _post_visibility_query(strawberry.Schema(query=Query), _NESTED_CONNECTION_QUERY)
    assert payload.get("errors") is None, payload
    assert len(payload["data"]["categories"]) == parent_count
    return [entry["sql"] for entry in captured.captured_queries if "products_item" in entry["sql"]]


def test_nested_connection_costs_one_query_per_parent_without_the_optimizer(db):
    """With no optimizer installed a nested connection costs one window query per parent.

    A relation-seeded connection is served from each parent's own relation
    manager, so the cost grows with the parent count: N parents pay N window
    queries. A schema that mounts no ``DjangoOptimizerExtension`` is a supported
    consumer configuration, and this is what it pays there - measured at two
    cardinalities so a fixed count cannot satisfy it, and so a regression toward
    per-EDGE loading (which would overshoot N) is visible.
    """
    services.seed_data(1)

    assert len(_nested_connection_item_queries(2)) == 2
    assert len(_nested_connection_item_queries(5)) == 5


@pytest.mark.django_db
def test_relay_id_only_connection_page_costs_one_query_and_emits_decodable_ids():
    """An id-only connection page reads the table once and every id decodes to its row.

    ``{ allCategories(first: 5) { edges { node { id } } } }`` selects nothing but
    the Relay ``id``, so the optimizer's projection must still carry the concrete
    pk column: if it did not, each edge would pay a lazy pk fetch and the single
    ``products_category`` query would become one per row. Staff is the viewer so
    ``CategoryType.get_queryset`` narrows nothing and the page is the raw table
    order. Each emitted id is checked against the one the package's own helper
    mints for that row, and decoded back to its ``products.category`` payload.
    """
    services.create_users(1)
    services.seed_data(1)
    from apps.products.schema import CategoryType

    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))
    expected_rows = list(Category.objects.order_by("pk")[:5])
    assert len(expected_rows) == 5

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allCategories(first: 5) { edges { node { id } } } }",
            client=client,
        )

    emitted = [edge["node"]["id"] for edge in data["allCategories"]["edges"]]
    assert emitted == [global_id_for(CategoryType, row.pk) for row in expected_rows]
    decoded = [relay.GlobalID.from_id(node_id) for node_id in emitted]
    assert [global_id.type_name for global_id in decoded] == ["products.category"] * 5
    assert [global_id.node_id for global_id in decoded] == [str(row.pk) for row in expected_rows]
    category_queries = [
        entry["sql"] for entry in captured.captured_queries if "products_category" in entry["sql"]
    ]
    assert len(category_queries) == 1, category_queries


@pytest.mark.django_db
def test_cascading_target_hook_blocks_fk_id_elision_over_http():
    """A cascading target hook costs a second query rather than eliding the FK read.

    An id-only forward-FK selection would normally round-trip the source row's FK
    column with no relation read at all. ``ItemType``'s target here is
    ``CategoryType``, whose ``get_queryset`` cascades, and a target hook must run
    over real rows - so the elision is off and the relation is fetched by a
    separate query instead. The root item read therefore carries no join to
    ``products_category``, and the category read is a second query.
    """
    services.seed_data(1)

    with CaptureQueriesContext(connection) as captured:
        data = assert_graphql_success(
            "{ allItems { edges { node { category { id } } } } }",
        )

    edges = data["allItems"]["edges"]
    assert edges, data
    assert all(edge["node"]["category"]["id"] for edge in edges)
    item_queries = [
        entry["sql"] for entry in captured.captured_queries if "products_item" in entry["sql"]
    ]
    assert len(item_queries) == 1, item_queries
    # No elision, but no join either: the target hook's rows arrive on their own
    # query, so the count is 2 and never 1 + one-per-row.
    assert " JOIN " not in item_queries[0].upper()
    assert len(captured.captured_queries) == 2, [
        entry["sql"] for entry in captured.captured_queries
    ]
