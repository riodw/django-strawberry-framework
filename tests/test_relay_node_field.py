"""Root Relay refetch tests for DjangoNodeField and DjangoNodesField.

Mirrors the top-level ``django_strawberry_framework/relay.py`` (the card-named
two-file split over a strict ``docs/TREE.md`` mirror -
``docs/spec-032-full_relay-0_0_9.md`` Decision 11). The fakeshop ``library`` app
now ships the live root-node surface (``node`` / ``nodes`` over ``/graphql/`` in
``examples/fakeshop/test_query/test_library_api.py``), so the consumer refetch
contract is carried there. The tests here stay package-side because they assert
what a live query cannot per the ``examples/fakeshop/test_query/README.md``
live-HTTP-first rule: synthetic model-label / type-strategy routing,
multi-type-over-one-model dispatch, custom ``relay.NodeID`` attributes, exact
query-count side channels, ``GLOBALID_INVALID`` error-code shapes,
construction- / finalize-time guards, ``SyncMisuseError`` discrimination, and
the public-export surface. Behavior-only twins whose contract the live suite
now carries are migration candidates (``docs/feedback.md`` /
``examples/fakeshop/test_query/README.md``).
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
from django_strawberry_framework.permissions import apply_cascade_permissions
from django_strawberry_framework.registry import registry
from django_strawberry_framework.relay import (
    GlobalIDDecode,
    _coerce_pk_or_none,
    _stamp_node_type,
    decode_model_global_id,
)
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


def _make_multi_type_category_nodes() -> tuple[type, type]:
    """Two Relay-Node types over ``Category`` - the Round-4 S2 multi-type shape.

    Both carry ``globalid_strategy = "type"`` so each type is addressable by
    its own GraphQL-type-name gid (under the default model-label strategy a
    secondary type's gid would decode to the primary).
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            primary = True
            globalid_strategy = "type"

    class CategoryAdminNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = "type"

    return CategoryNode, CategoryAdminNode


@pytest.mark.django_db
def test_bare_node_field_multi_type_model_typename_follows_gid():
    """``__typename`` matches the type the GlobalID named, not candidate order.

    Round-4 review S2: the bare ``node`` hands graphql-core a raw model
    instance, and with two registered types over one model both installed
    ``is_type_of`` hooks answered ``True`` - whichever candidate graphql-core
    tested first won, so a ``CategoryAdminNode`` gid came back
    ``__typename: "CategoryNode"``. The ``_stamp_node_type`` hint carries the
    decode-routing decision into type resolution.
    """
    services.seed_data(1)
    primary, secondary = _make_multi_type_category_nodes()
    schema = _schema_with(
        "node",
        relay.Node | None,
        DjangoNodeField(),
        extra_types=(primary, secondary),
    )
    row = Category.objects.order_by("pk").first()
    for type_name in ("CategoryNode", "CategoryAdminNode"):
        result = schema.execute_sync(
            "query ($id: ID!) { node(id: $id) { __typename } }",
            variable_values={"id": _gid(type_name, row.pk)},
        )
        assert result.errors is None
        assert result.data["node"]["__typename"] == type_name


@pytest.mark.django_db
def test_bare_nodes_field_multi_type_model_typenames_follow_gids():
    """Batch sibling of the S2 regression: per-position ``__typename`` routing."""
    services.seed_data(1)
    primary, secondary = _make_multi_type_category_nodes()
    schema = _schema_with(
        "nodes",
        list[relay.Node | None],
        DjangoNodesField(),
        extra_types=(primary, secondary),
    )
    row = Category.objects.order_by("pk").first()
    result = schema.execute_sync(
        "query ($ids: [ID!]!) { nodes(ids: $ids) { __typename } }",
        variable_values={
            "ids": [_gid("CategoryAdminNode", row.pk), _gid("CategoryNode", row.pk)],
        },
    )
    assert result.errors is None
    assert [node["__typename"] for node in result.data["nodes"]] == [
        "CategoryAdminNode",
        "CategoryNode",
    ]


def test_stamp_node_type_passes_through_none_and_unstampable_objects():
    """``None`` rides through; an attribute-rejecting return stays unstamped.

    ``None`` is the hidden/missing/uncoercible -> ``null`` contract; a bare
    ``object()`` stands in for a consumer ``resolve_node(s)`` override
    returning a ``__slots__``-style object that rejects attribute writes -
    the stamp is best-effort and such returns keep the isinstance fallback.
    """
    assert _stamp_node_type(object, None) is None
    unstampable = object()
    assert _stamp_node_type(object, unstampable) is unstampable
    assert not hasattr(unstampable, "_dsf_node_type_hint")


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
# Custom relay.NodeID[...] id attribute (coercion must key on resolve_id_attr())
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_node_custom_node_id_attr_resolves():
    """A consumer ``id: relay.NodeID[str]`` over a non-pk column resolves correctly.

    Coercion must key on ``resolve_id_attr()`` (here ``name``), not
    ``model._meta.pk``: a non-numeric name coerced against the int pk becomes
    ``None`` -> a spurious ``null`` for a row that exists (the P2 bug). The
    NodeID column is consumed as the ``id`` slot, so the query selects ``id`` /
    ``__typename``, not the column itself.
    """
    services.seed_data(1)

    class CategoryNode(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

    schema = _schema_with(
        "node",
        relay.Node | None,
        DjangoNodeField(),
        extra_types=(CategoryNode,),
    )
    row = Category.objects.order_by("pk").first()
    gid = _gid("products.category", row.name)
    result = schema.execute_sync(
        "query ($id: ID!) { node(id: $id) { __typename id } }",
        variable_values={"id": gid},
    )
    assert result.errors is None
    assert result.data["node"] == {"__typename": "CategoryNode", "id": gid}


@pytest.mark.django_db
def test_node_custom_node_id_attr_uncoercible_returns_null():
    """An uncoercible literal for a TYPED custom NodeID column returns null (no ORM leak).

    ``created_date`` is a ``DateTimeField``; an id its ``to_python`` rejects
    coerces to ``None`` -> ``null`` with no query issued (the default-pk
    uncoercible path's contract, now keyed on the real resolution field), and
    no Django ``ValidationError`` leaks to the client.
    """
    services.seed_data(1)

    class CategoryNode(DjangoType):
        created_date: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

    schema = _schema_with(
        "node",
        relay.Node | None,
        DjangoNodeField(),
        extra_types=(CategoryNode,),
    )
    result = schema.execute_sync(
        "query ($id: ID!) { node(id: $id) { __typename } }",
        variable_values={"id": _gid("products.category", "not-a-datetime")},
    )
    assert result.errors is None
    assert result.data == {"node": None}


@pytest.mark.django_db
def test_decode_model_global_id_resolves_custom_node_id_to_real_pk():
    """Write-side decode maps a custom NodeID value to the REAL pk, not the attr value (feedback #1).

    ``decode_model_global_id`` feeds every WRITE consumer (update/delete
    ``locate_instance``'s ``get(pk=...)``, the relation ``pk__in`` visibility query,
    and FK / M2M assignment), all of which treat ``result.pk`` as an actual primary
    key. For a consumer ``id: relay.NodeID[str]`` over the non-pk ``name`` column,
    the decoded value is the ``name`` string; handing that to a ``pk=`` lookup
    targets the wrong column (the P1 bug). The fix resolves it to ``row.pk`` here.
    """
    services.seed_data(1)

    class CategoryNode(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

    finalize_django_types()
    row = Category.objects.order_by("pk").first()
    result = decode_model_global_id(_gid("products.category", row.name), Category)
    assert result.status is GlobalIDDecode.OK
    # The REAL integer pk, NOT the ``name`` string the GlobalID carried.
    assert result.pk == row.pk
    assert result.pk != row.name


@pytest.mark.django_db
def test_decode_model_global_id_custom_node_id_no_row_is_uncoercible():
    """A custom NodeID value matching no row decodes as UNCOERCIBLE_PK, never a phantom pk (feedback #1).

    A ``name`` that exists on no row resolves to ``None`` in ``_resolve_real_pk``,
    which the caller maps to the same not-found surface a hidden row yields (no
    existence leak) - rather than passing the literal through as a fake pk.
    """
    services.seed_data(1)

    class CategoryNode(DjangoType):
        name: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

    finalize_django_types()
    result = decode_model_global_id(_gid("products.category", "no-such-category-name"), Category)
    assert result.status is GlobalIDDecode.UNCOERCIBLE_PK
    assert result.pk is None


@pytest.mark.django_db
def test_decode_model_global_id_passes_raw_value_for_non_field_node_id():
    """A NodeID over a non-concrete attr has no column to resolve, so the value passes through (feedback #1).

    ``_resolve_real_pk`` mirrors ``_coerce_pk_or_none``'s ``FieldDoesNotExist``
    fall-through: with no concrete column to map to a pk, the coerced literal is
    returned unchanged rather than crashing on ``get_field`` (a downstream
    ``pk=<literal>`` lookup then fails as not-found, the pre-032 behavior).
    """
    services.seed_data(1)

    class SlugNode(DjangoType):
        slug: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "SlugNode"

    finalize_django_types()
    result = decode_model_global_id(_gid("products.category", "abc-123"), Category)
    assert result.status is GlobalIDDecode.OK
    assert result.pk == "abc-123"


def test_coerce_pk_or_none_passes_raw_string_for_non_field_node_id():
    """A NodeID over a non-model-field attr skips coercion and passes the raw string.

    ``_coerce_pk_or_none`` keys on ``resolve_id_attr()``; when that names no
    concrete model field (``FieldDoesNotExist``) it cannot coerce, so it
    returns the literal unchanged (pre-032 behavior) rather than crashing.
    """

    class SlugNode(DjangoType):
        slug: relay.NodeID[str]

        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "SlugNode"

    finalize_django_types()
    assert _coerce_pk_or_none(SlugNode, "abc-123") == "abc-123"


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


@pytest.mark.django_db(transaction=True)
async def test_nodes_async_with_sync_consumer_resolve_nodes_override():
    """A SYNCHRONOUS consumer ``resolve_nodes`` override works under async execution.

    The batch gatherer must treat ``resolve_nodes`` as AwaitableOrValue: the
    framework default returns a coroutine in async context, but a valid sync
    consumer override returns the list directly. Awaiting it unconditionally
    raised ``TypeError: 'list' object can't be awaited`` (spec-032 feedback P1).
    """
    await sync_to_async(services.seed_data)(1)
    rows = {str(obj.pk): obj async for obj in Category.objects.order_by("pk")}

    class SyncCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info,
            node_ids,
            required=False,
        ):
            # Synchronous list return (no coroutine); closes over pre-fetched
            # rows so it issues no ORM query inside the event loop.
            return [rows.get(str(node_id)) for node_id in node_ids]

    schema = _schema_with(
        "nodes",
        list[relay.Node | None],
        DjangoNodesField(),
        extra_types=(SyncCategoryNode,),
    )
    target = next(iter(rows.values()))
    query = "query ($ids: [ID!]!) { nodes(ids: $ids) { __typename ... on CategoryNode { name } } }"
    result = await schema.execute(
        query,
        variable_values={"ids": [_gid("products.category", target.pk)]},
    )
    assert result.errors is None
    assert result.data["nodes"] == [{"__typename": "CategoryNode", "name": target.name}]


@pytest.mark.django_db
def test_nodes_consumer_resolve_nodes_wrong_length_raises():
    """A consumer ``resolve_nodes`` override returning a wrong-length list fails loudly.

    ``_interleave`` indexes by within-group position, so a shrunk /
    duplicate-collapsed return (the obvious ``filter(pk__in=node_ids)``
    spelling) is rejected with a ``ConfigurationError`` naming the type instead
    of yielding silently wrong rows or an ``IndexError``.
    """
    services.seed_data(2)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info,
            node_ids,
            required=False,
        ):
            return []  # wrong length: 0 rows for the requested ids.

    schema = _schema_with(
        "categories",
        list[CategoryNode | None],
        DjangoNodesField(CategoryNode),
    )
    first, second = Category.objects.order_by("pk")[:2]
    result = schema.execute_sync(
        _CATEGORIES_QUERY,
        variable_values={
            "ids": [_gid("products.category", first.pk), _gid("products.category", second.pk)],
        },
    )
    assert result.errors is not None
    message = str(result.errors[0])
    assert "CategoryNode" in message
    assert "resolve_nodes returned 0 row(s) for 2 requested id(s)" in message


@pytest.mark.django_db
def test_nodes_consumer_resolve_nodes_generator_return_accepted():
    """A consumer ``resolve_nodes`` override may return a generator (Round-4 minor).

    ``_check_nodes_result`` materializes a no-``__len__`` return before the
    length check, so a correctly-ordered generator resolves rather than dying
    on a bare ``len()`` ``TypeError`` (and a wrong-length generator still gets
    the named ``ConfigurationError``).
    """
    services.seed_data(2)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info,
            node_ids,
            required=False,
        ):
            rows = {str(obj.pk): obj for obj in Category.objects.filter(pk__in=node_ids)}
            return (rows.get(str(node_id)) for node_id in node_ids)

    schema = _schema_with(
        "categories",
        list[CategoryNode | None],
        DjangoNodesField(CategoryNode),
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


# =============================================================================
# STAGED SEAM (spec-034 Slice 3): node refetch <-> cascade composition pins.
# NO relay.py source change - node/nodes defaults already route through
# get_queryset (Decision 12), so a cascade-hidden row refetches as null with no
# existence leak. Fill in + drop the skips in Slice 3.
# =============================================================================


def _make_cascading_item_node() -> type:
    """Relay-Node ``Item`` type whose ``get_queryset`` cascades + a hiding ``Category``.

    The cascade analogue of ``_make_hidden_category_node``: an item is hidden not by
    its own column but by its FK target (``category``) being cascade-hidden. The
    ``Item`` hook calls ``apply_cascade_permissions`` (composing
    ``category__in (SELECT visible)``); the registered ``Category`` type hides
    private rows. Returns the ``Item`` node (the refetch target).
    """

    class _HidingCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return queryset.filter(is_private=False)

    class HiddenViaCascadeItemNode(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            return apply_cascade_permissions(cls, queryset, info)

    return HiddenViaCascadeItemNode


_ITEM_QUERY = "query ($id: ID!) { item(id: $id) { name } }"
_ITEMS_QUERY = "query ($ids: [ID!]!) { items(ids: $ids) { name } }"


@pytest.mark.django_db
def test_node_refetch_of_cascade_hidden_row_returns_null():
    """``node(id:)`` of a cascade-hidden row returns ``null`` - no existence leak (Decision 12).

    The refetch routes through ``Item.get_queryset`` -> ``apply_cascade_permissions``,
    so an item whose ``category`` is private is invisible and refetches as ``null``
    with no error - the no-existence-leak contract extended across the FK edge.
    """
    item_node = _make_cascading_item_node()
    schema = _schema_with("item", item_node | None, DjangoNodeField(item_node))

    public_cat = Category.objects.create(name="public_cat", is_private=False)
    private_cat = Category.objects.create(name="private_cat", is_private=True)
    Item.objects.create(name="visible_item", category=public_cat)
    hidden_item = Item.objects.create(name="hidden_item", category=private_cat)

    result = schema.execute_sync(
        _ITEM_QUERY,
        variable_values={"id": _gid("products.item", hidden_item.pk)},
    )
    assert result.errors is None
    assert result.data == {"item": None}


@pytest.mark.django_db
def test_nodes_batch_holes_for_cascade_hidden_rows():
    """``nodes(ids:)`` returns positional ``null`` holes for cascade-hidden rows (Decision 12).

    A batch interleaving a visible item and a cascade-hidden item resolves the
    visible id and leaves a positional ``null`` hole for the hidden one - the batch
    refetch honors the cascade per id, leaking no existence.
    """
    item_node = _make_cascading_item_node()
    schema = _schema_with("items", list[item_node | None], DjangoNodesField(item_node))

    public_cat = Category.objects.create(name="public_cat", is_private=False)
    private_cat = Category.objects.create(name="private_cat", is_private=True)
    visible_item = Item.objects.create(name="visible_item", category=public_cat)
    hidden_item = Item.objects.create(name="hidden_item", category=private_cat)

    result = schema.execute_sync(
        _ITEMS_QUERY,
        variable_values={
            "ids": [_gid("products.item", hidden_item.pk), _gid("products.item", visible_item.pk)],
        },
    )
    assert result.errors is None
    assert result.data["items"] == [None, {"name": visible_item.name}]
