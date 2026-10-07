"""Live GraphQL proof that a consumer JOIN never outranks a planned visibility ``Prefetch``.

When a relation's target type overrides ``get_queryset``, the walker plans that
relation as a ``Prefetch`` whose child queryset is the hook's output, and the
generated resolver stands down for it
(``django_strawberry_framework/types/resolvers.py::_optimizer_scoped_relation``).
The root queryset the plan is applied to can already carry the consumer's own
``select_related`` for the same path. Django skips a prefetch for every instance
whose relation cache is already populated, so a surviving JOIN would hand the
resolver the unscoped row the hook excludes. These rows pin that the planned
``Prefetch`` is the only source of the target rows: at depth one
(``select_related("category")`` beside a planned ``Prefetch("category")``) and at
depth two (``select_related("item__category")`` beside a planned
``Prefetch("item")`` whose child plans ``Prefetch("category")``), each for an
anonymous viewer the hook refuses and a staff viewer it admits, over sync and
async requests.
"""

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Entry, Item
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, post_graphql
from strategy_schemas import make_django_type
from strawberry.django.views import GraphQLView

from django_strawberry_framework import (
    DjangoListField,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing import AsyncTestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView

_CURRENT: dict[str, strawberry.Schema | None] = {"schema": None}


def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return GraphQLView.as_view(schema=schema)(request)


async def _async_graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql/", _graphql_view), path("graphql-async/", _async_graphql_view)]

#: Depth one: the root JOINs the item's category, which the plan prefetches.
_DEPTH_ONE_QUERY = "{ items { name category { name } } }"

#: Depth two: the root JOINs ``item__category`` through the planned ``item`` prefetch.
_DEPTH_TWO_QUERY = "{ entries { value item { name category { name } } } }"


def _hide_one_items_category() -> tuple[Item, Entry]:
    """Pin one public item and entry whose category alone is private; return both."""
    entry = Entry.objects.select_related("item").order_by("pk").first()
    assert entry is not None
    Entry.objects.filter(pk=entry.pk).update(is_private=False)
    Item.objects.filter(pk=entry.item_id).update(is_private=False)
    Category.objects.filter(pk=entry.item.category_id).update(is_private=True)
    entry.refresh_from_db()
    return Item.objects.get(pk=entry.item_id), entry


def _joined_schema(item_pk: int, entry_pk: int) -> strawberry.Schema:
    """Holder whose QuerySet roots JOIN the relations the optimizer plans as prefetches."""
    from apps.products.schema import EntryType, ItemType

    @strawberry.type
    class Query:
        @strawberry.field(graphql_type=list[ItemType])
        def items(self) -> QuerySet[Item]:
            return Item.objects.filter(pk=item_pk).select_related("category")

        @strawberry.field(graphql_type=list[ItemType])
        def items_wildcard(self) -> QuerySet[Item]:
            # The wildcard query state is set directly: that state, not the call
            # spelling Django now deprecates, is what a consumer queryset can carry.
            queryset = Item.objects.filter(pk=item_pk)
            queryset.query.select_related = True
            return queryset

        @strawberry.field(graphql_type=list[EntryType])
        def entries(self) -> QuerySet[Entry]:
            return Entry.objects.filter(pk=entry_pk).select_related("item__category")

    optimizer = DjangoOptimizerExtension()
    return strawberry.Schema(query=Query, extensions=[lambda: optimizer])


def _post(schema: strawberry.Schema, query: str, *, client: Client | None = None) -> JSONObject:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            response = post_graphql(query, client=client, url="/graphql/")
        assert response.status_code == 200
        return response.json()
    finally:
        _CURRENT["schema"] = None


def _staff_client() -> Client:
    services.create_users(1)
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))
    return client


def _assert_refused(payload: JSONObject, message: str, hidden_name: str) -> None:
    assert payload["data"] is None, payload
    assert [error["message"] for error in payload["errors"]] == [message]
    assert hidden_name not in str(payload)


def test_anonymous_depth_one_join_does_not_serve_the_planned_targets_hidden_row(
    db: None,
) -> None:
    """``select_related("category")`` beside the planned prefetch serves no hidden row."""
    services.seed_data(1)
    item, entry = _hide_one_items_category()

    payload = _post(_joined_schema(item.pk, entry.pk), _DEPTH_ONE_QUERY)

    _assert_refused(
        payload,
        "Cannot return null for non-nullable field ItemType.category.",
        item.category.name,
    )


def test_staff_depth_one_join_is_served_the_category(db: None) -> None:
    """The control: the hook admits staff, so the same row is served."""
    services.seed_data(1)
    item, entry = _hide_one_items_category()

    payload = _post(_joined_schema(item.pk, entry.pk), _DEPTH_ONE_QUERY, client=_staff_client())

    assert payload.get("errors") is None, payload
    assert payload["data"] == {
        "items": [{"name": item.name, "category": {"name": item.category.name}}],
    }


def test_anonymous_wildcard_join_does_not_serve_the_planned_targets_hidden_row(
    db: None,
) -> None:
    """The wildcard ``select_related()`` follows the non-null key the plan prefetches."""
    services.seed_data(1)
    item, entry = _hide_one_items_category()

    payload = _post(
        _joined_schema(item.pk, entry.pk),
        "{ itemsWildcard { name category { name } } }",
    )

    _assert_refused(
        payload,
        "Cannot return null for non-nullable field ItemType.category.",
        item.category.name,
    )


def test_anonymous_depth_two_join_does_not_serve_the_planned_targets_hidden_row(
    db: None,
) -> None:
    """``select_related("item__category")`` through a planned ``item`` prefetch serves no hidden row.

    ``ItemType.get_queryset`` cascades onto its category, so the planned ``item``
    prefetch is what refuses here: the item under a hidden category is itself
    hidden, and the non-null ``item`` fails rather than carrying the JOINed rows.
    """
    services.seed_data(1)
    item, entry = _hide_one_items_category()

    payload = _post(_joined_schema(item.pk, entry.pk), _DEPTH_TWO_QUERY)

    _assert_refused(
        payload,
        "Cannot return null for non-nullable field EntryType.item.",
        item.category.name,
    )


def test_staff_depth_two_join_is_served_the_category(db: None) -> None:
    """The control: the hook admits staff, so the nested category is served."""
    services.seed_data(1)
    item, entry = _hide_one_items_category()

    payload = _post(_joined_schema(item.pk, entry.pk), _DEPTH_TWO_QUERY, client=_staff_client())

    assert payload.get("errors") is None, payload
    assert payload["data"] == {
        "entries": [
            {
                "value": entry.value,
                "item": {"name": item.name, "category": {"name": item.category.name}},
            },
        ],
    }


def _holder_schema(
    item_pk: int,
    entry_pk: int,
    *,
    item_hook: bool = True,
    entries_join: str = "item__category",
) -> strawberry.Schema:
    """Holder whose JOINs come from a ROOT TYPE'S hook and a consumer resolver.

    ``HolderItemType.get_queryset`` adds ``select_related("category")`` and hides
    nothing, so its rows reach the relation; ``HolderCategoryType`` hides private
    categories. The JOIN therefore sits on the hook output twice over: on the
    ``items`` root, and on the child queryset of the planned ``item`` prefetch
    under ``entries``, whose resolver also JOINs ``item__category``.

    ``item_hook=False`` declares ``HolderItemType`` without a hook, so ``item``
    plans as a JOIN and only ``item__category`` as a prefetch: the resolver's
    ``item`` JOIN stays while the ``category`` hop beneath it is released.
    ``entries_join`` is the ``select_related`` path the ``entries`` resolver adds.
    """

    def join_category(
        cls: type[DjangoType],
        queryset: QuerySet[Item],
        info: strawberry.Info[object, object],
    ) -> QuerySet[Item]:
        return queryset.select_related("category")

    def hide_private(
        cls: type[DjangoType],
        queryset: QuerySet[Category],
        info: strawberry.Info[object, object],
    ) -> QuerySet[Category]:
        return queryset.filter(is_private=False)

    registry.clear()
    make_django_type(
        "HolderCategoryType",
        Category,
        ("id", "name"),
        node=False,
        namespace_extra={"get_queryset": classmethod(hide_private)},
    )
    item_type = make_django_type(
        "HolderItemType",
        Item,
        ("id", "name", "category"),
        node=False,
        namespace_extra={"get_queryset": classmethod(join_category)} if item_hook else None,
    )
    entry_type = make_django_type("HolderEntryType", Entry, ("id", "value", "item"), node=False)
    finalize_django_types()

    def resolve_items(_root: object, _info: object) -> QuerySet[Item]:
        return Item.objects.filter(pk=item_pk)

    def resolve_entries(_root: object, _info: object) -> QuerySet[Entry]:
        return Entry.objects.filter(pk=entry_pk).select_related(entries_join)

    # The holder types exist only at run time, so the field annotations a
    # ``DjangoListField`` reads its outer type from are supplied as data.
    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"items": list[item_type], "entries": list[entry_type]},
                "items": DjangoListField(item_type, resolver=resolve_items),
                "entries": DjangoListField(entry_type, resolver=resolve_entries),
            },
        ),
    )

    optimizer = DjangoOptimizerExtension()
    return strawberry.Schema(
        query=query,
        extensions=[lambda: optimizer],
        config=strawberry_config(),
    )


_HOLDER_REFUSAL = "Cannot return null for non-nullable field HolderItemType.category."


@pytest.mark.parametrize("query", [_DEPTH_ONE_QUERY, _DEPTH_TWO_QUERY])
def test_hook_join_does_not_serve_the_planned_targets_hidden_row(db: None, query: str) -> None:
    """A JOIN the hook itself adds, at the root and inside a planned child, serves no hidden row."""
    services.seed_data(1)
    item, entry = _hide_one_items_category()

    payload = _post(_holder_schema(item.pk, entry.pk), query)

    _assert_refused(payload, _HOLDER_REFUSAL, item.category.name)


def test_hookless_intermediate_join_does_not_serve_the_planned_targets_hidden_row(
    db: None,
) -> None:
    """A JOINed ``item`` hop survives while the prefetched ``category`` hop under it is released."""
    services.seed_data(1)
    item, entry = _hide_one_items_category()

    payload = _post(_holder_schema(item.pk, entry.pk, item_hook=False), _DEPTH_TWO_QUERY)

    _assert_refused(payload, _HOLDER_REFUSAL, item.category.name)


def test_join_off_the_planned_prefetch_path_is_kept(db: None) -> None:
    """A JOIN no planned prefetch covers survives: ``item`` comes in with the entry row.

    Only ``item__category`` is planned as a prefetch here, so the resolver's ``item``
    JOIN is not released and no separate item read runs, while the hidden category
    is still refused.
    """
    services.seed_data(1)
    item, entry = _hide_one_items_category()
    schema = _holder_schema(item.pk, entry.pk, item_hook=False, entries_join="item")

    with CaptureQueriesContext(connection) as captured:
        payload = _post(schema, _DEPTH_TWO_QUERY)

    _assert_refused(payload, _HOLDER_REFUSAL, item.category.name)
    assert not [
        entry["sql"]
        for entry in captured.captured_queries
        if entry["sql"].startswith('SELECT "products_item"')
    ], captured.captured_queries


def _async_holder_schema() -> tuple[strawberry.Schema, str]:
    services.seed_data(1)
    item, entry = _hide_one_items_category()
    return _holder_schema(item.pk, entry.pk), item.category.name


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("query", [_DEPTH_ONE_QUERY, _DEPTH_TWO_QUERY])
async def test_async_hook_join_does_not_serve_the_planned_targets_hidden_row(query: str) -> None:
    """The same refusal on an async request, at both depths."""
    schema, hidden_name = await sync_to_async(_async_holder_schema)()
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            res = await AsyncTestClient().query(
                query,
                assert_no_errors=False,
                url="/graphql-async/",
            )
            response = res.response
    finally:
        _CURRENT["schema"] = None
    assert response.status_code == 200
    _assert_refused(response.json(), _HOLDER_REFUSAL, hidden_name)
