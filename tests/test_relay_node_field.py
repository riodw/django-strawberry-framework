"""Tests for the spec-032 Slice-2 root refetch fields (``DjangoNodeField`` / ``DjangoNodesField``).

Mirrors the top-level ``django_strawberry_framework/relay.py`` (the card-named
two-file split over a strict ``docs/TREE.md`` mirror -
``docs/spec-032-full_relay-0_0_9.md`` Decision 11). These are the package
twins that keep the per-slice ``fail_under = 100`` gate green until the
Slice-6 fakeshop activation makes the live copies the canonical surface
(spec Test plan "Package twins"). The Slice-4 permission-integration
contract is satisfied by the Slice-2 tests below.
"""

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category, Item
from asgiref.sync import sync_to_async
from strawberry import relay

import django_strawberry_framework
from django_strawberry_framework import (
    DjangoNodeField,
    DjangoNodesField,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.relay import SyncMisuseError


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state (and the co-cleared node-field ledger) around each test."""
    registry.clear()
    yield
    registry.clear()


def _gid(type_name: str, node_id) -> str:
    """Encode a ``GlobalID`` payload string the way the framework emits it."""
    return str(relay.GlobalID(type_name, str(node_id)))


def _make_node_type(name: str, *, model=Category, strategy: str | None = None) -> type:
    """Build a Relay-Node-shaped ``DjangoType`` over ``model`` for a test."""
    meta_attrs = {
        "model": model,
        "fields": ("id", "name"),
        "interfaces": (relay.Node,),
        "name": name,
    }
    if strategy is not None:
        meta_attrs["globalid_strategy"] = strategy
    return type(name, (DjangoType,), {"Meta": type("Meta", (), meta_attrs)})


def _schema_with(
    field_name: str,
    annotation,
    field_value,
    *,
    extra_types=(),
) -> strawberry.Schema:
    """Build an in-process schema exposing one root field built by a factory.

    ``extra_types`` feeds ``strawberry.Schema(types=[...])`` - the documented
    engine constraint for a schema whose only root field is interface-typed
    (concrete types are otherwise unreachable from the schema walk).
    """
    namespace = {"__annotations__": {field_name: annotation}, field_name: field_value}
    query_cls = strawberry.type(type("Query", (), namespace))
    finalize_django_types()
    return strawberry.Schema(query=query_cls, config=strawberry_config(), types=list(extra_types))


_NODE_QUERY = "query ($id: ID!) { node(id: $id) { __typename ... on CategoryNode { name } } }"
_CATEGORY_QUERY = "query ($id: ID!) { category(id: $id) { name } }"
_CATEGORIES_QUERY = "query ($ids: [ID!]!) { categories(ids: $ids) { name } }"


# ---------------------------------------------------------------------------
# Bare + typed single-node form
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_bare_node_field_resolves_model_label_id():
    """Bare ``node(id:)`` decodes a model-label payload (default strategy) to the right type."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with(
        "node",
        relay.Node | None,
        DjangoNodeField(),
        extra_types=(category_node,),
    )
    row = Category.objects.order_by("pk").first()
    result = schema.execute_sync(
        _NODE_QUERY,
        variable_values={"id": _gid("products.category", row.pk)},
    )
    assert result.errors is None
    assert result.data["node"] == {"__typename": "CategoryNode", "name": row.name}


@pytest.mark.django_db
def test_bare_node_field_resolves_type_name_id():
    """Bare ``node(id:)`` decodes a type-name payload under ``Meta.globalid_strategy = "type"``."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode", strategy="type")
    schema = _schema_with(
        "node",
        relay.Node | None,
        DjangoNodeField(),
        extra_types=(category_node,),
    )
    row = Category.objects.order_by("pk").first()
    result = schema.execute_sync(
        _NODE_QUERY,
        variable_values={"id": _gid("CategoryNode", row.pk)},
    )
    assert result.errors is None
    assert result.data["node"] == {"__typename": "CategoryNode", "name": row.name}


@pytest.mark.django_db
def test_typed_node_field_resolves_target():
    """``DjangoNodeField(CategoryNode)`` returns the row for a matching id."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with(
        "category",
        category_node | None,
        DjangoNodeField(category_node),
    )
    row = Category.objects.order_by("pk").first()
    result = schema.execute_sync(
        _CATEGORY_QUERY,
        variable_values={"id": _gid("products.category", row.pk)},
    )
    assert result.errors is None
    assert result.data["category"] == {"name": row.name}


@pytest.mark.django_db
def test_typed_node_field_mismatch_raises():
    """An ItemNode id at a CategoryNode-typed field raises naming expected/received types."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode")
    _make_node_type("ItemNode", model=Item)
    schema = _schema_with(
        "category",
        category_node | None,
        DjangoNodeField(category_node),
    )
    item = Item.objects.order_by("pk").first()
    result = schema.execute_sync(
        _CATEGORY_QUERY,
        variable_values={"id": _gid("products.item", item.pk)},
    )
    assert result.errors is not None
    message = str(result.errors[0])
    assert "CategoryNode" in message
    assert "ItemNode" in message
    # The mismatch error carries NO extensions code (only GLOBALID_INVALID is
    # spec-assigned); the nullable field carries null under the error.
    assert (result.errors[0].extensions or {}).get("code") is None
    assert result.data == {"category": None}


# ---------------------------------------------------------------------------
# Typed batch form
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_typed_nodes_field_resolves_targets():
    """``DjangoNodesField(CategoryNode)`` resolves a list of matching ids in order."""
    services.seed_data(2)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with(
        "categories",
        list[category_node | None],
        DjangoNodesField(category_node),
    )
    first, second = Category.objects.order_by("pk")[:2]
    result = schema.execute_sync(
        _CATEGORIES_QUERY,
        variable_values={
            "ids": [_gid("products.category", second.pk), _gid("products.category", first.pk)],
        },
    )
    assert result.errors is None
    assert result.data["categories"] == [{"name": second.name}, {"name": first.name}]


@pytest.mark.django_db
def test_typed_nodes_field_mismatch_raises():
    """One ItemNode id mid-batch fails the WHOLE field, never a per-position null."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode")
    _make_node_type("ItemNode", model=Item)
    schema = _schema_with(
        "categories",
        list[category_node | None],
        DjangoNodesField(category_node),
    )
    row = Category.objects.order_by("pk").first()
    item = Item.objects.order_by("pk").first()
    result = schema.execute_sync(
        _CATEGORIES_QUERY,
        variable_values={
            "ids": [_gid("products.category", row.pk), _gid("products.item", item.pk)],
        },
    )
    assert result.errors is not None
    message = str(result.errors[0])
    assert "CategoryNode" in message
    assert "ItemNode" in message
    # The `[CategoryNode]!` non-null propagates the error and nulls the
    # enclosing data - the whole field fails, no positional null hole.
    assert result.data is None


# ---------------------------------------------------------------------------
# Hidden / missing rows - the Relay null contract
# ---------------------------------------------------------------------------


def _make_hidden_category_node() -> type:
    """Relay-Node-shaped Category type whose ``get_queryset`` hides private rows."""

    class HiddenCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    return HiddenCategoryNode


@pytest.mark.django_db
def test_node_hidden_row_returns_null():
    """A ``get_queryset``-hidden row resolves to null with NO error."""
    services.seed_data(1)
    hidden_node = _make_hidden_category_node()
    schema = _schema_with("category", hidden_node | None, DjangoNodeField(hidden_node))
    private_row = Category.objects.filter(is_private=True).order_by("pk").first()
    result = schema.execute_sync(
        _CATEGORY_QUERY,
        variable_values={"id": _gid("products.category", private_row.pk)},
    )
    assert result.errors is None
    assert result.data == {"category": None}


@pytest.mark.django_db
def test_node_missing_row_returns_null():
    """A well-formed id for a nonexistent row resolves to null with NO error."""
    services.seed_data(1)
    hidden_node = _make_hidden_category_node()
    schema = _schema_with("category", hidden_node | None, DjangoNodeField(hidden_node))
    missing_pk = Category.objects.order_by("-pk").first().pk + 1
    result = schema.execute_sync(
        _CATEGORY_QUERY,
        variable_values={"id": _gid("products.category", missing_pk)},
    )
    assert result.errors is None
    assert result.data == {"category": None}


@pytest.mark.django_db
def test_node_null_paths_issue_equal_queries(django_assert_num_queries):
    """Hidden and missing refetches issue the SAME query count (no existence oracle)."""
    services.seed_data(1)
    hidden_node = _make_hidden_category_node()
    schema = _schema_with("category", hidden_node | None, DjangoNodeField(hidden_node))
    private_row = Category.objects.filter(is_private=True).order_by("pk").first()
    missing_pk = Category.objects.order_by("-pk").first().pk + 1
    query = _CATEGORY_QUERY
    # Both null paths run the one shared filtered-queryset code path
    # (``qs.first()`` under ``required=False``): exactly one query each.
    with django_assert_num_queries(1):
        hidden = schema.execute_sync(
            query,
            variable_values={"id": _gid("products.category", private_row.pk)},
        )
    with django_assert_num_queries(1):
        missing = schema.execute_sync(
            query,
            variable_values={"id": _gid("products.category", missing_pk)},
        )
    assert hidden.data == missing.data == {"category": None}


# ---------------------------------------------------------------------------
# Malformed ids -> GLOBALID_INVALID; uncoercible pks -> null
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "bad_id",
    [
        # Malformed base64 / non-`type:id` payload. Reachable ONLY because the
        # argument is ``strawberry.ID`` (Revision 7 P1): a ``relay.GlobalID``
        # argument would be parsed upstream by Strawberry's convert_argument
        # and surface the engine's error with no GLOBALID_INVALID code.
        "this-is-not-base64",
        # Unresolvable model label.
        _gid("nosuchapp.nosuchmodel", "1"),
        # Strategy-forbidden shape: a type-name payload at a "model"-strategy type.
        _gid("CategoryNode", "1"),
    ],
)
def test_node_malformed_id_graphql_error(bad_id):
    """Each malformed/forbidden shape surfaces GLOBALID_INVALID, never a raw ConfigurationError."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with(
        "node",
        relay.Node | None,
        DjangoNodeField(),
        extra_types=(category_node,),
    )
    result = schema.execute_sync(_NODE_QUERY, variable_values={"id": bad_id})
    assert result.errors is not None
    assert result.errors[0].extensions["code"] == "GLOBALID_INVALID"
    assert str(result.errors[0]).startswith("Invalid GlobalID: ")
    assert result.data == {"node": None}


@pytest.mark.django_db
def test_node_uncoercible_pk_returns_null(django_assert_num_queries):
    """A well-formed id with an uncoercible pk literal -> null, no error, ZERO queries."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with(
        "node",
        relay.Node | None,
        DjangoNodeField(),
        extra_types=(category_node,),
    )
    with django_assert_num_queries(0):
        result = schema.execute_sync(
            _NODE_QUERY,
            variable_values={"id": _gid("products.category", "abc")},
        )
    assert result.errors is None
    assert result.data == {"node": None}


@pytest.mark.django_db
def test_nodes_uncoercible_pk_null_hole():
    """An uncoercible pk mid-batch becomes a positional null hole; the rest still resolve."""
    services.seed_data(2)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with(
        "categories",
        list[category_node | None],
        DjangoNodesField(category_node),
    )
    first, second = Category.objects.order_by("pk")[:2]
    result = schema.execute_sync(
        _CATEGORIES_QUERY,
        variable_values={
            "ids": [
                _gid("products.category", first.pk),
                _gid("products.category", "abc"),
                _gid("products.category", second.pk),
            ],
        },
    )
    assert result.errors is None
    # The garbage literal never poisons the batch ``pk__in``.
    assert result.data["categories"] == [{"name": first.name}, None, {"name": second.name}]


# ---------------------------------------------------------------------------
# Batch semantics - order, batching, duplicates, empty list, mid-batch errors
# ---------------------------------------------------------------------------

_NODES_QUERY = (
    "query ($ids: [ID!]!) { nodes(ids: $ids) { __typename"
    " ... on CategoryNode { name } ... on ItemNode { name } } }"
)


@pytest.mark.django_db
def test_nodes_preserves_input_order_with_null_holes():
    """Visible / hidden / missing ids interleave with nulls at the right indexes."""
    services.seed_data(1)
    hidden_node = _make_hidden_category_node()
    schema = _schema_with(
        "categories",
        list[hidden_node | None],
        DjangoNodesField(hidden_node),
    )
    visible = Category.objects.filter(is_private=False).order_by("pk").first()
    hidden = Category.objects.filter(is_private=True).order_by("pk").first()
    missing_pk = Category.objects.order_by("-pk").first().pk + 1
    result = schema.execute_sync(
        _CATEGORIES_QUERY,
        variable_values={
            "ids": [
                _gid("products.category", hidden.pk),
                _gid("products.category", visible.pk),
                _gid("products.category", missing_pk),
            ],
        },
    )
    assert result.errors is None
    assert result.data["categories"] == [None, {"name": visible.name}, None]


@pytest.mark.django_db
def test_nodes_batches_per_type(django_assert_num_queries):
    """Ids spanning two types issue exactly one query per distinct type."""
    services.seed_data(2)
    category_node = _make_node_type("CategoryNode")
    item_node = _make_node_type("ItemNode", model=Item)
    schema = _schema_with(
        "nodes",
        list[relay.Node | None],
        DjangoNodesField(),
        extra_types=(category_node, item_node),
    )
    categories = list(Category.objects.order_by("pk")[:2])
    item = Item.objects.order_by("pk").first()
    with django_assert_num_queries(2):
        result = schema.execute_sync(
            _NODES_QUERY,
            variable_values={
                "ids": [
                    _gid("products.category", categories[0].pk),
                    _gid("products.item", item.pk),
                    _gid("products.category", categories[1].pk),
                ],
            },
        )
    assert result.errors is None
    assert result.data["nodes"] == [
        {"__typename": "CategoryNode", "name": categories[0].name},
        {"__typename": "ItemNode", "name": item.name},
        {"__typename": "CategoryNode", "name": categories[1].name},
    ]


@pytest.mark.django_db
def test_nodes_duplicate_ids():
    """The same id twice resolves per position - two equal entries."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with(
        "categories",
        list[category_node | None],
        DjangoNodesField(category_node),
    )
    row = Category.objects.order_by("pk").first()
    gid = _gid("products.category", row.pk)
    result = schema.execute_sync(
        _CATEGORIES_QUERY,
        variable_values={"ids": [gid, gid]},
    )
    assert result.errors is None
    assert result.data["categories"] == [{"name": row.name}, {"name": row.name}]


@pytest.mark.django_db
def test_nodes_empty_list(django_assert_num_queries):
    """``ids: []`` returns ``[]`` without touching the database."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with(
        "categories",
        list[category_node | None],
        DjangoNodesField(category_node),
    )
    with django_assert_num_queries(0):
        result = schema.execute_sync(
            _CATEGORIES_QUERY,
            variable_values={"ids": []},
        )
    assert result.errors is None
    assert result.data["categories"] == []


@pytest.mark.django_db
def test_nodes_malformed_id_mid_batch():
    """A malformed id among well-formed ones fails the WHOLE field with GLOBALID_INVALID."""
    services.seed_data(1)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with(
        "categories",
        list[category_node | None],
        DjangoNodesField(category_node),
    )
    row = Category.objects.order_by("pk").first()
    result = schema.execute_sync(
        _CATEGORIES_QUERY,
        variable_values={"ids": [_gid("products.category", row.pk), "this-is-not-base64"]},
    )
    assert result.errors is not None
    assert result.errors[0].extensions["code"] == "GLOBALID_INVALID"
    # Whole-field failure: the non-null list nulls the enclosing data - the
    # malformed id is never absorbed into a positional null hole.
    assert result.data is None


# ---------------------------------------------------------------------------
# Construction-time guards + finalize-time ledger check
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("factory", [DjangoNodeField, DjangoNodesField])
def test_node_field_target_guards(factory):
    """The typed form runs the four shared guards plus the Relay-Node-shaped fifth."""
    with pytest.raises(
        ConfigurationError,
        match=rf"{factory.__name__} requires a DjangoType class",
    ):
        factory(42)

    class NotADjangoType:
        pass

    with pytest.raises(
        ConfigurationError,
        match=rf"{factory.__name__} requires a DjangoType subclass",
    ):
        factory(NotADjangoType)

    class NoMetaType(DjangoType):
        pass

    with pytest.raises(ConfigurationError, match="is not a registered DjangoType"):
        factory(NoMetaType)

    class PlainCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    with pytest.raises(
        ConfigurationError,
        match=rf"{factory.__name__} requires a Relay-Node-shaped DjangoType target",
    ):
        factory(PlainCategoryType)


def test_node_field_without_node_types_raises_at_finalize():
    """The ledger check fires with the documented message; ``registry.clear()`` resets it."""

    class PlainCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    DjangoNodeField()  # bare declaration appends the ledger
    with pytest.raises(
        ConfigurationError,
        match=r"node lookup configured but no Node types registered\.",
    ):
        finalize_django_types()

    # The ledger-reset half: clear() co-clears the ledger, and a Node-shaped
    # registration with a fresh declaration finalizes cleanly.
    registry.clear()
    _make_node_type("CategoryNode")
    DjangoNodesField()
    finalize_django_types()


# ---------------------------------------------------------------------------
# Async execution contexts + SyncMisuseError pass-through
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_node_async_context():
    """``await schema.execute`` happy path - the resolver passes the coroutine through."""
    await sync_to_async(services.seed_data)(1)
    category_node = _make_node_type("CategoryNode")
    schema = _schema_with(
        "node",
        relay.Node | None,
        DjangoNodeField(),
        extra_types=(category_node,),
    )
    row = await Category.objects.order_by("pk").afirst()
    result = await schema.execute(
        _NODE_QUERY,
        variable_values={"id": _gid("products.category", row.pk)},
    )
    assert result.errors is None
    assert result.data["node"] == {"__typename": "CategoryNode", "name": row.name}


@pytest.mark.django_db(transaction=True)
async def test_nodes_async_context():
    """``nodes`` returns ONE gathering coroutine - gather + interleave across two types."""
    await sync_to_async(services.seed_data)(1)
    category_node = _make_node_type("CategoryNode")
    item_node = _make_node_type("ItemNode", model=Item)
    schema = _schema_with(
        "nodes",
        list[relay.Node | None],
        DjangoNodesField(),
        extra_types=(category_node, item_node),
    )
    row = await Category.objects.order_by("pk").afirst()
    item = await Item.objects.order_by("pk").afirst()
    result = await schema.execute(
        _NODES_QUERY,
        variable_values={
            "ids": [_gid("products.item", item.pk), _gid("products.category", row.pk)],
        },
    )
    assert result.errors is None
    assert result.data["nodes"] == [
        {"__typename": "ItemNode", "name": item.name},
        {"__typename": "CategoryNode", "name": row.name},
    ]


@pytest.mark.django_db
def test_node_sync_async_get_queryset_raises_sync_misuse():
    """An async ``get_queryset`` under sync execution surfaces SyncMisuseError, NOT GLOBALID_INVALID.

    Discriminating (Revision 7 P2): ``SyncMisuseError`` IS-A
    ``ConfigurationError``, so a blanket catch-convert around the resolver
    body would mislabel this server misconfiguration a client id error; the
    boundary scopes the decode call only.
    """
    services.seed_data(1)

    class AsyncCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        async def get_queryset(cls, queryset, info, **kwargs):
            return queryset

    schema = _schema_with(
        "category",
        AsyncCategoryNode | None,
        DjangoNodeField(AsyncCategoryNode),
    )
    row = Category.objects.order_by("pk").first()
    result = schema.execute_sync(
        _CATEGORY_QUERY,
        variable_values={"id": _gid("products.category", row.pk)},
    )
    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert (result.errors[0].extensions or {}).get("code") != "GLOBALID_INVALID"
    assert "Invalid GlobalID" not in str(result.errors[0])


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


def test_public_exports():
    """``DjangoNodeField`` / ``DjangoNodesField`` are importable package-root exports."""
    assert django_strawberry_framework.DjangoNodeField is DjangoNodeField
    assert django_strawberry_framework.DjangoNodesField is DjangoNodesField
    assert "DjangoNodeField" in django_strawberry_framework.__all__
    assert "DjangoNodesField" in django_strawberry_framework.__all__
