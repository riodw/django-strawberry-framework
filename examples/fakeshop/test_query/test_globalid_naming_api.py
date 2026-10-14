"""Live GraphQL HTTP tests for type-strategy GlobalIDs under a type-renaming name converter.

Under ``globalid_strategy = "type"`` a GlobalID's type-name slot is the name the
EXECUTING schema published for the type - Strawberry's ``info.path.typename``,
the client's ``__typename`` - so a consumer ``NameConverter`` that renames object
types (passed through ``strawberry_config(name_converter=...)``) renames the slot
too. Every surface that reads such an id back resolves it through the same
schema's published names: ``node`` / ``nodes`` and a typed node field, the
mutation ``id:`` lookup and its relation ids (forward key and many-to-many) across
the model, form and serializer flavors, and the GlobalID filters (own id and
relation keys, flat and through a ``RelatedFilter`` hop).

The main surface is fakeshop's own composed ``Query`` / ``Mutation``, re-finalized
under ``RELAY_GLOBALID_STRATEGY = "type"`` and served by a second ``DjangoSchema``
whose converter prefixes every object type name with ``Api`` (the shipped schema
cannot carry a renaming converter without changing fakeshop's public contract, so
the renaming schema is a holder mounted on this module's own URLconf). Two holder
schemas over the products models cover what the composed one cannot: the
``Meta.globalid_strategy = "type"`` spelling with a converted name equal to another
real type's own name (the id resolves to the type the schema publishes under that
name, never the other one; a registered Relay type the schema does not publish
keeps its own spelling), and a ``type`` child of a concrete ``model``-strategy
Relay parent, whose shadowing closure emits the published name like every other
``type`` type.
"""

import sys
from collections.abc import Callable, Iterator, Mapping

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models
from apps.products.services import create_users, seed_data
from django.contrib.auth.models import Permission, User
from django.db import connection
from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, post_graphql
from strawberry import relay
from strawberry.schema.name_converter import NameConverter
from strawberry.types.base import StrawberryObjectDefinition
from typing_extensions import override

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoNodeField,
    DjangoNodesField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.registry import registry
from django_strawberry_framework.views import DjangoGraphQLView

_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


def _graphql_view(request: HttpRequest) -> HttpResponseBase:
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql/", _graphql_view)]


class _ApiPrefix(NameConverter):
    """Publish every output object type and interface as ``Api<name>``; inputs keep theirs."""

    @override
    def from_object(self, object_type: StrawberryObjectDefinition) -> str:
        name = super().from_object(object_type)
        return name if object_type.is_input else f"Api{name}"


def _gid(type_name: str, pk: object) -> str:
    return str(relay.GlobalID(type_name=type_name, node_id=str(pk)))


@pytest.fixture
def renaming_schema(project_schema_override: Callable[[], None]) -> Iterator[DjangoSchema]:
    """Serve fakeshop's composed schema on ``type`` ids under the ``Api`` prefix converter.

    The setting is applied before the full rebuild re-finalizes every app's types
    (the strategy is stamped at finalization); the autouse guard restores the
    default-strategy registry after the test.
    """
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"}):
        project_schema_override()
        project = sys.modules["config.schema"]
        optimizer = DjangoOptimizerExtension()
        schema = DjangoSchema(
            query=project.Query,
            mutation=project.Mutation,
            config=strawberry_config(name_converter=_ApiPrefix()),
            extensions=[lambda: optimizer],
        )
        _CURRENT["schema"] = schema
        try:
            with override_settings(ROOT_URLCONF=__name__):
                yield schema
        finally:
            _CURRENT["schema"] = None


def _mount(schema: DjangoSchema) -> Iterator[DjangoSchema]:
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            yield schema
    finally:
        _CURRENT["schema"] = None


def _payload(
    query: str,
    variables: Mapping[str, object] | None = None,
    *,
    client: Client | None = None,
) -> JSONObject:
    response = post_graphql(query, variables=variables, client=client, url="/graphql/")
    assert response.status_code == 200
    payload: JSONObject = response.json()
    return payload


def _data(
    query: str,
    variables: Mapping[str, object] | None = None,
    *,
    client: Client | None = None,
) -> JSONObject:
    payload = _payload(query, variables, client=client)
    assert "errors" not in payload, payload
    data: JSONObject = payload["data"]
    return data


def _staff(*codenames: str) -> Client:
    """Log in ``staff_1`` (bypasses every products visibility hook) holding ``codenames``."""
    user = User.objects.get(username="staff_1")
    for codename in codenames:
        app_label, name = codename.split(".")
        user.user_permissions.add(
            Permission.objects.get(codename=name, content_type__app_label=app_label),
        )
    client = Client()
    client.force_login(User.objects.get(pk=user.pk))
    return client


def _table_queries(captured: CaptureQueriesContext, table: str) -> list[str]:
    return [
        query["sql"] for query in captured.captured_queries if f'FROM "{table}"' in query["sql"]
    ]


def _first_item() -> models.Item:
    return models.Item.objects.select_related("category").earliest("pk")


# ---------------------------------------------------------------------------
# Emission: the slot is the published name, i.e. the client's ``__typename``
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.usefixtures("renaming_schema")
def test_connection_edge_and_nested_relation_ids_carry_the_published_name() -> None:
    """A root connection edge and its nested forward relation both emit ``Api<Type>:<pk>``."""
    seed_data(1)
    create_users(1)
    item = _first_item()

    data = _data(
        "query($id: String!) { allItems(filter: { id: { exact: $id } }) { edges { node { "
        "__typename id category { __typename id } } } } }",
        {"id": _gid("ApiItemType", item.pk)},
        client=_staff(),
    )

    assert data == {
        "allItems": {
            "edges": [
                {
                    "node": {
                        "__typename": "ApiItemType",
                        "id": _gid("ApiItemType", item.pk),
                        "category": {
                            "__typename": "ApiCategoryType",
                            "id": _gid("ApiCategoryType", item.category_id),
                        },
                    },
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# Refetch: node / nodes / typed node field decode the published name
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.usefixtures("renaming_schema")
def test_bare_node_refetches_an_emitted_item_id_in_one_item_query() -> None:
    """``node(id:)`` resolves ``ApiItemType:<pk>`` to the item through one ``products_item`` read."""
    seed_data(1)
    create_users(1)
    item = _first_item()
    client = _staff()

    with CaptureQueriesContext(connection) as captured:
        data = _data(
            "query($id: ID!) { node(id: $id) { __typename id ... on ApiItemType { name } } }",
            {"id": _gid("ApiItemType", item.pk)},
            client=client,
        )

    assert data == {
        "node": {
            "__typename": "ApiItemType",
            "id": _gid("ApiItemType", item.pk),
            "name": item.name,
        },
    }
    assert len(_table_queries(captured, "products_item")) == 1


@pytest.mark.django_db
@pytest.mark.usefixtures("renaming_schema")
def test_nodes_refetches_emitted_ids_of_two_types_in_input_order() -> None:
    """``nodes(ids:)`` decodes each published name, one read per decoded type, input order kept."""
    seed_data(1)
    create_users(1)
    item = _first_item()
    client = _staff()

    with CaptureQueriesContext(connection) as captured:
        data = _data(
            "query($ids: [ID!]!) { nodes(ids: $ids) { __typename "
            "... on ApiItemType { name } ... on ApiCategoryType { name } } }",
            {"ids": [_gid("ApiCategoryType", item.category_id), _gid("ApiItemType", item.pk)]},
            client=client,
        )

    assert data == {
        "nodes": [
            {"__typename": "ApiCategoryType", "name": item.category.name},
            {"__typename": "ApiItemType", "name": item.name},
        ],
    }
    assert len(_table_queries(captured, "products_item")) == 1
    assert len(_table_queries(captured, "products_category")) == 1


@pytest.mark.django_db
@pytest.mark.usefixtures("renaming_schema")
def test_typed_node_field_refetches_an_emitted_genre_id() -> None:
    """The typed ``genre(id:)`` field accepts the ``ApiGenreType`` id its own type emits."""
    seed_data(1)
    genre = library_models.Genre.objects.create(name="Renamed")

    with CaptureQueriesContext(connection) as captured:
        data = _data(
            "query($id: ID!) { genre(id: $id) { __typename id name } }",
            {"id": _gid("ApiGenreType", genre.pk)},
        )

    assert data == {
        "genre": {
            "__typename": "ApiGenreType",
            "id": _gid("ApiGenreType", genre.pk),
            "name": "Renamed",
        },
    }
    assert len(_table_queries(captured, "library_genre")) == 1


@pytest.mark.django_db
@pytest.mark.usefixtures("renaming_schema")
def test_typed_node_field_names_published_types_in_the_mismatch_error() -> None:
    """A typed field fed another type's emitted id names both types as the client sees them."""
    seed_data(1)
    create_users(1)
    item = _first_item()

    payload = _payload(
        "query($id: ID!) { genre(id: $id) { name } }",
        {"id": _gid("ApiItemType", item.pk)},
        client=_staff(),
    )

    assert payload["data"] == {"genre": None}
    assert [error["message"] for error in payload["errors"]] == [
        "Wrong node type: expected a ApiGenreType id, received a ApiItemType id.",
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "expected_data"),
    [
        ("query($id: ID!) { node(id: $id) { id } }", {"node": None}),
        # ``nodes`` is a non-null list, so its field error nulls ``data`` itself.
        ("query($id: ID!) { nodes(ids: [$id]) { id } }", None),
    ],
    ids=["node", "nodes"],
)
@pytest.mark.usefixtures("renaming_schema")
def test_default_spelling_of_a_renamed_type_is_rejected(
    query: str,
    expected_data: JSONObject | None,
) -> None:
    """``ItemType:<pk>`` names nothing this schema publishes: ``GLOBALID_INVALID``, no row read."""
    seed_data(1)
    create_users(1)
    item = _first_item()
    client = _staff()

    with CaptureQueriesContext(connection) as captured:
        payload = _payload(query, {"id": _gid("ItemType", item.pk)}, client=client)

    assert payload["data"] == expected_data
    assert [(error["message"], error["extensions"]["code"]) for error in payload["errors"]] == [
        (
            (
                "Invalid GlobalID: No Relay-Node DjangoType is published as GraphQL type "
                "'ItemType' in this schema"
            ),
            "GLOBALID_INVALID",
        ),
    ]
    assert _table_queries(captured, "products_item") == []


# ---------------------------------------------------------------------------
# Mutations: lookup id and relation ids decode the published name
# ---------------------------------------------------------------------------

_ITEM_WRITES: dict[
    str,
    tuple[str, str, Callable[[models.Item, models.Category], JSONObject]],
] = {
    "model-create": (
        "mutation($d: ItemInput!) { createItem(data: $d) { errors { field messages } } }",
        "products.add_item",
        lambda item, target: {
            "d": {"name": "RenamedWidget", "categoryId": _gid("ApiCategoryType", target.pk)},
        },
    ),
    "model-update": (
        (
            "mutation($id: ID!, $d: ItemPartialInput!) { updateItem(id: $id, data: $d) { "
            "errors { field messages } } }"
        ),
        "products.change_item",
        lambda item, target: {
            "id": _gid("ApiItemType", item.pk),
            "d": {"name": "RenamedWidget", "categoryId": _gid("ApiCategoryType", target.pk)},
        },
    ),
    "form-create": (
        (
            "mutation($d: ItemModelFormInput!) { createItemViaForm(data: $d) { "
            "errors { field messages } } }"
        ),
        "products.add_item",
        lambda item, target: {
            "d": {"name": "RenamedWidget", "categoryId": _gid("ApiCategoryType", target.pk)},
        },
    ),
    "form-update": (
        (
            "mutation($id: ID!, $d: ItemModelFormPartialInput!) { updateItemViaForm(id: $id, "
            "data: $d) { errors { field messages } } }"
        ),
        "products.change_item",
        lambda item, target: {
            "id": _gid("ApiItemType", item.pk),
            "d": {"name": "RenamedWidget", "categoryId": _gid("ApiCategoryType", target.pk)},
        },
    ),
    "serializer-create": (
        (
            "mutation($d: ItemSerializerInput!) { createItemViaSerializer(data: $d) { "
            "errors { field messages } } }"
        ),
        "products.add_item",
        lambda item, target: {
            "d": {"name": "RenamedWidget", "categoryId": _gid("ApiCategoryType", target.pk)},
        },
    ),
    "serializer-update": (
        (
            "mutation($id: ID!, $d: ItemSerializerPartialInput!) { updateItemViaSerializer(id: $id, "
            "data: $d) { errors { field messages } } }"
        ),
        "products.change_item",
        lambda item, target: {
            "id": _gid("ApiItemType", item.pk),
            "d": {"name": "RenamedWidget", "categoryId": _gid("ApiCategoryType", target.pk)},
        },
    ),
}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("flavor", list(_ITEM_WRITES), ids=list(_ITEM_WRITES))
@pytest.mark.usefixtures("renaming_schema")
def test_item_write_by_emitted_ids_targets_the_named_rows(
    flavor: str,
) -> None:
    """Each flavor writes ``RenamedWidget`` under the category its ``ApiCategoryType`` id names."""
    seed_data(1)
    create_users(1)
    item = _first_item()
    target = models.Category.objects.exclude(pk=item.category_id).earliest("pk")
    document, codename, variables = _ITEM_WRITES[flavor]

    data = _data(document, variables(item, target), client=_staff(codename))

    assert data == {next(iter(data)): {"errors": []}}
    written = models.Item.objects.get(name="RenamedWidget")
    assert written.category_id == target.pk
    if flavor.endswith("-update"):
        assert written.pk == item.pk


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("renaming_schema")
def test_delete_by_emitted_id_removes_the_named_item() -> None:
    """``deleteItem(id: "ApiItemType:<pk>")`` deletes exactly that row."""
    seed_data(1)
    create_users(1)
    item = _first_item()
    survivors = set(models.Item.objects.exclude(pk=item.pk).values_list("pk", flat=True))

    data = _data(
        "mutation($id: ID!) { deleteItem(id: $id) { errors { field messages } } }",
        {"id": _gid("ApiItemType", item.pk)},
        client=_staff("products.delete_item"),
    )

    assert data == {"deleteItem": {"errors": []}}
    assert set(models.Item.objects.values_list("pk", flat=True)) == survivors


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("renaming_schema")
def test_many_to_many_ids_by_emitted_genre_ids_attach_the_named_genres() -> None:
    """``createBookViaCustomInput(genres:)`` attaches the genres its ``ApiGenreType`` ids name."""
    seed_data(1)
    branch = library_models.Branch.objects.create(name="Central", city="Boston")
    shelf = library_models.Shelf.objects.create(code="A-1", topic="Fiction", branch=branch)
    first = library_models.Genre.objects.create(name="First")
    second = library_models.Genre.objects.create(name="Second")
    library_models.Genre.objects.create(name="Unnamed")

    data = _data(
        "mutation($d: BookInput!) { createBookViaCustomInput(data: $d) { "
        "errors { field messages } } }",
        {
            "d": {
                "title": "RenamedBook",
                "subtitle": "renamed",
                "shelfId": shelf.pk,
                "genres": [_gid("ApiGenreType", first.pk), _gid("ApiGenreType", second.pk)],
            },
        },
    )

    assert data == {"createBookViaCustomInput": {"errors": []}}
    book = library_models.Book.objects.get(title="RenamedBook")
    assert set(book.genres.values_list("name", flat=True)) == {"First", "Second"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("renaming_schema")
def test_serializer_many_to_many_update_by_emitted_ids() -> None:
    """``updateBookGenresViaSerializer`` locates the ``ApiBookType`` id and sets the named genres."""
    seed_data(1)
    branch = library_models.Branch.objects.create(name="Central", city="Boston")
    shelf = library_models.Shelf.objects.create(code="A-1", topic="Fiction", branch=branch)
    book = library_models.Book.objects.create(title="Kindred", shelf=shelf)
    kept = library_models.Genre.objects.create(name="Kept")
    library_models.Genre.objects.create(name="Unnamed")

    data = _data(
        "mutation($id: ID!, $d: BookGenresSerializerPartialInput!) { "
        "updateBookGenresViaSerializer(id: $id, data: $d) { errors { field messages } } }",
        {"id": _gid("ApiBookType", book.pk), "d": {"genres": [_gid("ApiGenreType", kept.pk)]}},
    )

    assert data == {"updateBookGenresViaSerializer": {"errors": []}}
    assert list(book.genres.values_list("name", flat=True)) == ["Kept"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.usefixtures("renaming_schema")
def test_default_spelling_relation_id_is_an_invalid_relation_error() -> None:
    """``categoryId: "CategoryType:<pk>"`` names nothing this schema publishes: no row written."""
    seed_data(1)
    create_users(1)
    category = models.Category.objects.earliest("pk")

    data = _data(
        "mutation($d: ItemInput!) { createItem(data: $d) { errors { field messages } } }",
        {"d": {"name": "RenamedWidget", "categoryId": _gid("CategoryType", category.pk)}},
        client=_staff("products.add_item"),
    )

    assert data == {
        "createItem": {
            "errors": [
                {"field": "categoryId", "messages": ["Invalid id for relation 'categoryId'."]},
            ],
        },
    }
    assert not models.Item.objects.filter(name="RenamedWidget").exists()


# ---------------------------------------------------------------------------
# Filters: GlobalID filter inputs accept the published name
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("variable", "filter_input"),
    [
        ("$a: String!", "{ id: { exact: $a } }"),
        ("$a: [String!]!", "{ id: { in: $a } }"),
        ("$a: String!", "{ category: { id: { exact: $a } } }"),
        ("$a: [String!]!", "{ entriesId: { in: $a } }"),
    ],
    ids=[
        "own-id-exact",
        "own-id-in",
        "related-filter-hop",
        "relation-key-in",
    ],
)
@pytest.mark.usefixtures("renaming_schema")
def test_globalid_filters_accept_emitted_ids(variable: str, filter_input: str) -> None:
    """Own-id, ``RelatedFilter``-hop and relation-key GlobalID filters select the rows named."""
    seed_data(1)
    create_users(1)
    item = _first_item()
    other = models.Item.objects.exclude(category_id=item.category_id).earliest("pk")
    entry = models.Entry.objects.filter(item=item).earliest("pk")
    value, expected = {
        "{ id: { exact: $a } }": (_gid("ApiItemType", item.pk), [item.name]),
        "{ id: { in: $a } }": (
            [_gid("ApiItemType", item.pk), _gid("ApiItemType", other.pk)],
            sorted([item.name, other.name]),
        ),
        "{ category: { id: { exact: $a } } }": (
            _gid("ApiCategoryType", item.category_id),
            sorted(
                models.Item.objects.filter(category_id=item.category_id).values_list(
                    "name",
                    flat=True,
                ),
            ),
        ),
        "{ entriesId: { in: $a } }": ([_gid("ApiEntryType", entry.pk)], [item.name]),
    }[filter_input]

    data = _data(
        f"query({variable}) {{ allItems(filter: {filter_input}, orderBy: [{{ name: ASC }}]) "
        "{ edges { node { name } } } }",
        {"a": value},
        client=_staff(),
    )

    assert [edge["node"]["name"] for edge in data["allItems"]["edges"]] == expected


@pytest.mark.django_db
@pytest.mark.usefixtures("renaming_schema")
def test_relation_key_exact_filter_accepts_an_emitted_property_id() -> None:
    """``allEntries(filter: { propertyId: { exact } })`` selects the entries of that property."""
    seed_data(1)
    create_users(1)
    prop = models.Property.objects.exclude(name="Secret").earliest("pk")

    data = _data(
        "query($p: String!) { allEntries(filter: { propertyId: { exact: $p } }) { "
        "edges { node { id } } } }",
        {"p": _gid("ApiPropertyType", prop.pk)},
        client=_staff(),
    )

    assert sorted(edge["node"]["id"] for edge in data["allEntries"]["edges"]) == sorted(
        _gid("ApiEntryType", pk)
        for pk in models.Entry.objects.filter(property=prop).values_list("pk", flat=True)
    )


@pytest.mark.django_db
@pytest.mark.usefixtures("renaming_schema")
def test_globalid_filter_rejects_the_default_spelling_of_a_renamed_type() -> None:
    """The filter expects the published name and says so; the default spelling selects nothing."""
    seed_data(1)
    create_users(1)
    item = _first_item()

    payload = _payload(
        "query($a: String!) { allItems(filter: { id: { exact: $a } }) { edges { node { name } } } }",
        {"a": _gid("ItemType", item.pk)},
        client=_staff(),
    )

    # ``allItems`` is a non-null connection, so its field error nulls ``data`` itself.
    assert payload["data"] is None
    assert [error["message"] for error in payload["errors"]] == [
        "GlobalID type mismatch: filter expects ApiItemType but received ItemType",
    ]


# ---------------------------------------------------------------------------
# Holder schemas: Meta spelling with a name collision, and the shadowing child
# ---------------------------------------------------------------------------


@pytest.fixture
def collision_schema() -> Iterator[DjangoSchema]:
    """``CategoryNode`` publishes as ``ApiCategoryNode``, the very name another real type declares.

    Every type uses ``Meta.globalid_strategy = "type"`` under the default setting. The
    item type is literally named ``ApiCategoryNode`` and publishes as
    ``ApiApiCategoryNode``, so the slot ``ApiCategoryNode`` is the category's in this
    schema and the item type's own default spelling. ``PropertyNode`` is registered
    but reachable from no root, so this schema publishes nothing for it.
    """
    registry.clear()

    class CategoryNode(DjangoType):
        class Meta:
            model = models.Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = "type"

    class ApiCategoryNode(DjangoType):
        class Meta:
            model = models.Item
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = "type"

    class PropertyNode(DjangoType):
        class Meta:
            model = models.Property
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = "type"

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        item: ApiCategoryNode | None = DjangoNodeField(ApiCategoryNode)
        items: list[ApiCategoryNode | None] = DjangoNodesField(ApiCategoryNode)
        categories: DjangoConnection[CategoryNode] = DjangoConnectionField(CategoryNode)

    finalize_django_types()
    assert registry.get_definition(PropertyNode) is not None
    yield from _mount(
        DjangoSchema(query=Query, config=strawberry_config(name_converter=_ApiPrefix())),
    )


@pytest.mark.django_db
@pytest.mark.usefixtures("collision_schema")
def test_converted_name_equal_to_another_types_name_resolves_the_published_type() -> None:
    """``node(id: "ApiCategoryNode:<pk>")`` returns the category, never the item of that pk."""
    seed_data(1)
    category = models.Category.objects.earliest("pk")

    data = _data(
        "query($id: ID!) { node(id: $id) { __typename ... on ApiCategoryNode { name } } }",
        {"id": _gid("ApiCategoryNode", category.pk)},
    )

    assert data == {"node": {"__typename": "ApiCategoryNode", "name": category.name}}


@pytest.mark.django_db
@pytest.mark.usefixtures("collision_schema")
def test_converted_name_collision_is_a_typed_mismatch_not_a_wrong_row() -> None:
    """The typed ``item(id:)`` field refuses the category's id by both published names."""
    seed_data(1)
    category = models.Category.objects.earliest("pk")

    payload = _payload(
        "query($id: ID!) { item(id: $id) { name } }",
        {"id": _gid("ApiCategoryNode", category.pk)},
    )

    assert payload["data"] == {"item": None}
    assert [error["message"] for error in payload["errors"]] == [
        "Wrong node type: expected a ApiApiCategoryNode id, received a ApiCategoryNode id.",
    ]


@pytest.mark.django_db
@pytest.mark.usefixtures("collision_schema")
def test_typed_nodes_field_names_published_types_in_the_mismatch_error() -> None:
    """The typed ``items(ids:)`` batch refuses the category's id by both published names."""
    seed_data(1)
    category = models.Category.objects.earliest("pk")

    payload = _payload(
        "query($ids: [ID!]!) { items(ids: $ids) { name } }",
        {"ids": [_gid("ApiCategoryNode", category.pk)]},
    )

    # ``items`` is a non-null list, so its field error nulls ``data`` itself.
    assert payload["data"] is None
    assert [error["message"] for error in payload["errors"]] == [
        "Wrong node type: expected a ApiApiCategoryNode id, received a ApiCategoryNode id.",
    ]


@pytest.mark.django_db
@pytest.mark.usefixtures("collision_schema")
def test_typed_mismatch_names_an_unpublished_type_by_its_own_spelling() -> None:
    """A Relay type this schema does not publish keeps its own spelling, and its own name.

    ``PropertyNode:<pk>`` names no type the schema publishes, and the registered
    ``PropertyNode`` is published under no other name here, so it decodes as it does
    with no schema; the typed field then refuses it as a ``PropertyNode`` id.
    """
    seed_data(1)
    prop = models.Property.objects.earliest("pk")

    payload = _payload(
        "query($id: ID!) { item(id: $id) { name } }",
        {"id": _gid("PropertyNode", prop.pk)},
    )

    assert payload["data"] == {"item": None}
    assert [error["message"] for error in payload["errors"]] == [
        "Wrong node type: expected a ApiApiCategoryNode id, received a PropertyNode id.",
    ]


class _PropertyAsCategory(NameConverter):
    """Publish ``PropertyNode`` under the name ``CategoryNode`` and nothing else renamed."""

    @override
    def from_object(self, object_type: StrawberryObjectDefinition) -> str:
        name = super().from_object(object_type)
        return "CategoryNode" if name == "PropertyNode" else name


@pytest.fixture
def filter_authority_schema() -> Iterator[DjangoSchema]:
    """An item filter on ``category`` in a schema that publishes ``PropertyNode`` as ``CategoryNode``.

    ``CategoryNode`` is registered (the filter's target) but reachable from no root,
    so the only type this schema publishes under the name ``CategoryNode`` is the
    property type.
    """
    registry.clear()

    class CategoryNode(DjangoType):
        class Meta:
            model = models.Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = "type"

    class PropertyNode(DjangoType):
        class Meta:
            model = models.Property
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = "type"

    class ItemByCategoryFilter(FilterSet):
        class Meta:
            model = models.Item
            fields = {"category": ["exact"]}

    class ItemNode(DjangoType):
        class Meta:
            model = models.Item
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = "type"
            filterset_class = ItemByCategoryFilter

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        items: DjangoConnection[ItemNode] = DjangoConnectionField(ItemNode)
        properties: DjangoConnection[PropertyNode] = DjangoConnectionField(PropertyNode)

    finalize_django_types()
    assert registry.get_definition(CategoryNode) is not None
    yield from _mount(
        DjangoSchema(query=Query, config=strawberry_config(name_converter=_PropertyAsCategory())),
    )


@pytest.mark.django_db
@pytest.mark.usefixtures("filter_authority_schema")
def test_relation_filter_refuses_a_slot_this_schema_publishes_for_another_type() -> None:
    """``CategoryNode:<pk>`` is this schema's property id, so the category filter refuses it.

    The slot equals the target type's own default spelling, but ``node(id:)`` in
    this schema resolves it to the property; the filter validates through the
    same resolution and never filters items by a property's primary key.
    """
    seed_data(1)
    category = models.Item.objects.earliest("pk").category
    # Primary keys drift with whatever ran earlier in the process, so pin the collision:
    # a property whose pk equals a category that owns items.
    prop, _ = models.Property.objects.get_or_create(
        pk=category.pk,
        defaults={"name": "collision", "category": category},
    )
    assert models.Item.objects.filter(category_id=prop.pk).exists()

    refetched = _data(
        "query($id: ID!) { node(id: $id) { __typename ... on CategoryNode { name } } }",
        {"id": _gid("CategoryNode", prop.pk)},
    )
    payload = _payload(
        "query($v: String!) { items(filter: { category: { exact: $v } }) { edges { node { name } } } }",
        {"v": _gid("CategoryNode", prop.pk)},
    )

    assert refetched == {"node": {"__typename": "CategoryNode", "name": prop.name}}
    assert payload["data"] is None
    assert [error["message"] for error in payload["errors"]] == [
        (
            "GlobalID type mismatch: filter expects CategoryNode but received CategoryNode, "
            "which this schema publishes for another type"
        ),
    ]


@pytest.fixture
def shadowing_child_schema() -> Iterator[DjangoSchema]:
    """A ``type`` child of a concrete ``model``-strategy Relay parent, under the prefix converter."""
    registry.clear()

    class ParentCategoryNode(DjangoType):
        class Meta:
            model = models.Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            primary = True
            globalid_strategy = "model"

    class ChildCategoryNode(ParentCategoryNode):
        # basedpyright: DjangoType reads only the class's own ``Meta`` (``cls.__dict__``); the
        # child declares a fresh one, never a subclass of the parent's
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = models.Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = "type"

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        children: DjangoConnection[ChildCategoryNode] = DjangoConnectionField(ChildCategoryNode)
        parents: DjangoConnection[ParentCategoryNode] = DjangoConnectionField(ParentCategoryNode)

    finalize_django_types()
    yield from _mount(
        DjangoSchema(query=Query, config=strawberry_config(name_converter=_ApiPrefix())),
    )


@pytest.mark.django_db
@pytest.mark.usefixtures("shadowing_child_schema")
def test_shadowing_type_child_emits_its_published_name() -> None:
    """The child's slot is ``ApiChildCategoryNode`` (its ``__typename``); the parent keeps its label."""
    seed_data(1)
    category = models.Category.objects.earliest("pk")

    listed = _data(
        "query { children(first: 1) { edges { node { __typename id } } } "
        "parents(first: 1) { edges { node { __typename id } } } }",
    )

    assert listed == {
        "children": {
            "edges": [
                {
                    "node": {
                        "__typename": "ApiChildCategoryNode",
                        "id": _gid("ApiChildCategoryNode", category.pk),
                    },
                },
            ],
        },
        "parents": {
            "edges": [
                {
                    "node": {
                        "__typename": "ApiParentCategoryNode",
                        "id": _gid("products.category", category.pk),
                    },
                },
            ],
        },
    }


@pytest.mark.django_db
@pytest.mark.usefixtures("shadowing_child_schema")
def test_shadowing_type_child_refetches_the_id_it_emitted() -> None:
    """The id the child's connection put on the wire refetches through ``node`` as the child."""
    seed_data(1)
    category = models.Category.objects.earliest("pk")
    emitted = _data("query { children(first: 1) { edges { node { id } } } }")["children"]["edges"][
        0
    ]["node"]["id"]

    refetched = _data(
        "query($id: ID!) { node(id: $id) { __typename ... on ApiChildCategoryNode { name } } }",
        {"id": emitted},
    )

    assert refetched == {"node": {"__typename": "ApiChildCategoryNode", "name": category.name}}
