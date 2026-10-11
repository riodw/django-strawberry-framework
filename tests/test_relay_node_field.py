"""Root Relay refetch tests for DjangoNodeField and DjangoNodesField.

Mirrors the top-level ``django_strawberry_framework/relay.py`` (the card-named
two-file split over a strict ``docs/TREE.md`` mirror -
``docs/SPECS/spec-032-full_relay-0_0_9.md`` Decision 11). Consumer refetch over
HTTP lives in ``examples/fakeshop/test_query/test_library_api.py`` (shipped
``node`` / ``nodes`` / typed ``genre(id:)``, plus a ``/graphql-test/`` holder
for typed ``DjangoNodesField`` and ``/graphql-async/`` for async colour). Rows
here stay package-side because no live request can express them: type-name
``globalid_strategy`` routing, multi-type-over-one-model ``__typename``
dispatch, ``_stamp_node_type`` isolation, custom ``relay.NodeID`` internals,
construction- / finalize-time guards, consumer ``resolve_nodes`` override
contracts, ``SyncMisuseError`` discrimination (``original_error`` is not a wire
field), and the public-export surface.
"""

from collections.abc import Awaitable, Callable, Iterable, Iterator
from typing import SupportsIndex

import pytest
import strawberry
from apps.products import services
from apps.products.models import Category
from asgiref.sync import sync_to_async
from django.db.models import Model, QuerySet
from strawberry import relay
from strawberry.schema_directive import Location as DirectiveLocation
from strawberry.schema_directive import schema_directive
from typing_extensions import Self, override

import django_strawberry_framework
from django_strawberry_framework import (
    DjangoNodeField,
    DjangoNodesField,
    DjangoSchema,
    DjangoType,
    ErrorPolicy,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.relay import (
    GlobalIDDecode,
    _coerce_pk_or_none,
    _node_fields_declared,
    _stamp_node_type,
    decode_model_global_id,
)
from django_strawberry_framework.types.relay import SyncMisuseError, implements_relay_node


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Drop registry state (and the co-cleared node-field ledger) around each test."""
    registry.clear()
    yield
    registry.clear()


def _gid(type_name: str, node_id: object) -> str:
    """Encode a ``GlobalID`` payload string the way the framework emits it."""
    return str(relay.GlobalID(type_name, str(node_id)))


def _make_node_type(
    name: str,
    *,
    model: type[Model] = Category,
    strategy: str | None = None,
) -> type:
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
    annotation: object,
    field_value: object,
    *,
    extra_types: Iterable[type] = (),
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
# Type-name strategy + multi-type-over-one-model routing
# ---------------------------------------------------------------------------


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
    assert row is not None
    result = schema.execute_sync(
        _NODE_QUERY,
        variable_values={"id": _gid("CategoryNode", row.pk)},
    )
    assert result.errors is None
    assert result.data is not None
    assert result.data["node"] == {"__typename": "CategoryNode", "name": row.name}


def _make_multi_type_category_nodes() -> tuple[type, type]:
    """Two Relay-Node types over ``Category`` - the multi-type-over-one-model shape.

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

    The bare ``node`` hands graphql-core a raw model instance, and with two
    registered types over one model both installed
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
        assert row is not None
        result = schema.execute_sync(
            "query ($id: ID!) { node(id: $id) { __typename } }",
            variable_values={"id": _gid(type_name, row.pk)},
        )
        assert result.errors is None
        assert result.data is not None
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
    assert row is not None
    result = schema.execute_sync(
        "query ($ids: [ID!]!) { nodes(ids: $ids) { __typename } }",
        variable_values={
            "ids": [_gid("CategoryAdminNode", row.pk), _gid("CategoryNode", row.pk)],
        },
    )
    assert result.errors is None
    assert result.data is not None
    assert [node["__typename"] for node in result.data["nodes"]] == [
        "CategoryAdminNode",
        "CategoryNode",
    ]


@pytest.mark.django_db
def test_node_type_hint_does_not_poison_reused_model_instance():
    """A refetch hint is isolated when a consumer reuses one ORM instance.

    The bare node field must route a secondary GlobalID to its named concrete
    type without mutating the model object a consumer may return from another
    field in the same operation. Before ``_stamp_node_type`` copied model
    instances, the later concrete ``PrimaryNode`` field rejected that reused
    object because its stale ``SecondaryNode`` hint made ``is_type_of`` return
    false.
    """
    services.seed_data(1)
    row = Category.objects.order_by("pk").first()

    class PrimaryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            primary = True
            globalid_strategy = "type"

    class SecondaryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            globalid_strategy = "type"

        @classmethod
        def resolve_node(
            cls,
            node_id: str,
            *,
            info: strawberry.Info,
            required: bool = False,
        ):
            del cls, node_id, info, required
            return row

    class Query:
        node: relay.Node | None = DjangoNodeField()
        # basedpyright: a DjangoType field resolves to its model row; the checker cannot see
        # that ``PrimaryNode`` wraps ``Category``
        primary: PrimaryNode = strawberry.field(resolver=lambda: row)  # pyright: ignore[reportAssignmentType]

    Query = strawberry.type(Query)
    finalize_django_types()
    schema = strawberry.Schema(
        query=Query,
        config=strawberry_config(),
        types=[PrimaryNode, SecondaryNode],
    )
    assert row is not None
    gid = _gid("SecondaryNode", row.pk)
    result = schema.execute_sync(
        "query($id: ID!) { node(id: $id) { __typename } primary { name } }",
        variable_values={"id": gid},
    )
    assert result.errors is None, result.errors
    assert result.data == {"node": {"__typename": "SecondaryNode"}, "primary": {"name": row.name}}
    assert not hasattr(row, "_dsf_node_type_hint")


def test_stamp_node_type_passes_through_none_and_unstampable_objects():
    """``None`` rides through; an attribute-rejecting return stays unstamped.

    ``None`` is the hidden/missing/uncoercible -> ``null`` contract; a bare
    ``object()`` stands in for a consumer ``resolve_node(s)`` override
    returning a ``__slots__``-style object that rejects attribute writes -
    the stamp is best-effort and such returns keep the isinstance fallback.
    """

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)

    finalize_django_types()
    assert implements_relay_node(CategoryNode)
    assert _stamp_node_type(CategoryNode, None) is None
    unstampable = object()
    # basedpyright: a plain stand-in class carrying no definition, which the code under test
    # reads through getattr; _stamp_node_type types the parameter as type[_RelayDjangoType]
    assert _stamp_node_type(object, unstampable) is unstampable  # pyright: ignore[reportArgumentType]
    assert not hasattr(unstampable, "_dsf_node_type_hint")


def test_stamp_node_type_returns_a_model_instance_that_rejects_copying():
    class Model:
        pass

    class UncopyableNode(Model):
        @override
        def __reduce_ex__(self, protocol: SupportsIndex):
            raise TypeError("copy unavailable")

    resolved_type = type(
        "ResolvedType",
        (),
        {"__django_strawberry_definition__": type("Definition", (), {"model": Model})()},
    )
    node = UncopyableNode()
    # basedpyright: a type()-built class whose definition names a plain (non-Django) model, so
    # the node is an instance that refuses copying; _stamp_node_type types the parameter as
    # type[_RelayDjangoType]
    assert _stamp_node_type(resolved_type, node) is node  # pyright: ignore[reportArgumentType]
    assert not hasattr(node, "_dsf_node_type_hint")


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
    assert row is not None
    gid = _gid("products.category", row.name)
    result = schema.execute_sync(
        "query ($id: ID!) { node(id: $id) { __typename id } }",
        variable_values={"id": gid},
    )
    assert result.errors is None
    assert result.data is not None
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
    """Write-side decode maps a custom NodeID value to the REAL pk, not the attr value.

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

    assert registry.get(Category) is CategoryNode

    finalize_django_types()
    row = Category.objects.order_by("pk").first()
    assert row is not None
    result = decode_model_global_id(_gid("products.category", row.name), Category)
    assert result.status is GlobalIDDecode.OK
    # The REAL integer pk, NOT the ``name`` string the GlobalID carried.
    assert result.pk == row.pk
    assert result.pk != row.name


@pytest.mark.django_db
def test_decode_model_global_id_custom_node_id_no_row_is_uncoercible():
    """A custom NodeID value matching no row decodes as UNCOERCIBLE_PK, never a phantom pk.

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

    assert registry.get(Category) is CategoryNode

    finalize_django_types()
    result = decode_model_global_id(_gid("products.category", "no-such-category-name"), Category)
    assert result.status is GlobalIDDecode.UNCOERCIBLE_PK
    assert result.pk is None


@pytest.mark.django_db
def test_decode_model_global_id_passes_raw_value_for_non_field_node_id():
    """A NodeID over a non-concrete attr has no column to resolve, so the value passes through.

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

    assert registry.get(Category) is SlugNode

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
    assert implements_relay_node(SlugNode)
    assert _coerce_pk_or_none(SlugNode, "abc-123") == "abc-123"


# ---------------------------------------------------------------------------
# resolve_node(s) receive the decoded node_id string (Strawberry's contract)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_consumer_overrides_receive_the_decoded_node_id_string():
    """Both root fields hand a consumer override the ``node_id`` string, as Strawberry does.

    Strawberry's ``Node.resolve_node(node_id: str)`` / ``resolve_nodes(node_ids:
    Iterable[str])`` is the override contract, and its own ``relay.node()`` field
    passes the decoded string. The id-slot coercion only gates an uncoercible
    literal to ``null``; handing the override the coerced ``int`` instead broke a
    ``str``-typed override (``'int' object has no attribute 'startswith'``) and
    made the same override see two types depending on which field called it.
    """
    services.seed_data(1)
    row = Category.objects.order_by("pk").first()
    received = []

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        def resolve_node(
            cls,
            node_id: str,
            *,
            info: strawberry.Info,
            required: bool = False,
        ):
            received.append(node_id)
            return None if node_id.startswith("legacy-") else row

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info: strawberry.Info,
            node_ids: Iterable[str],
            required: bool = False,
        ):
            node_ids = list(node_ids)
            received.append(node_ids)
            return [row for _ in node_ids]

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        nodes: list[relay.Node | None] = DjangoNodesField()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, config=strawberry_config(), types=[CategoryNode])
    assert row is not None
    gid = _gid("products.category", row.pk)
    result = schema.execute_sync(
        "query ($id: ID!) { node(id: $id) { __typename } nodes(ids: [$id, $id]) { __typename } }",
        variable_values={"id": gid},
    )

    assert result.errors is None
    assert received == [str(row.pk), [str(row.pk), str(row.pk)]]


@pytest.mark.django_db
def test_default_resolvers_find_a_row_whose_id_literal_spells_its_pk_differently():
    """The defaults coerce the ``node_id`` string themselves, so ``"07"`` finds pk ``7``.

    The batch default reorders rows by the coerced key; keying on the raw string
    would miss the row and hand back a ``null`` hole for an id that names it.
    """
    services.seed_data(1)

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

    @strawberry.type
    class Query:
        node: relay.Node | None = DjangoNodeField()
        nodes: list[relay.Node | None] = DjangoNodesField()

    finalize_django_types()
    schema = strawberry.Schema(query=Query, config=strawberry_config(), types=[CategoryNode])
    row = Category.objects.order_by("pk").first()
    assert row is not None
    padded = _gid("products.category", f"0{row.pk}")
    result = schema.execute_sync(
        "query ($id: ID!) { node(id: $id) { ... on CategoryNode { name } }"
        " nodes(ids: [$id]) { ... on CategoryNode { name } } }",
        variable_values={"id": padded},
    )

    assert result.errors is None
    assert result.data == {"node": {"name": row.name}, "nodes": [{"name": row.name}]}


def _strawberry_node_schema():
    """A schema whose root fields are Strawberry's own ``relay.node()`` over the defaults."""

    class CategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"
            globalid_strategy = "type"

    @strawberry.type
    class Query:
        node: relay.Node | None = relay.node()
        required_node: relay.Node = relay.node()
        nodes: list[relay.Node | None] = relay.node()

    finalize_django_types()
    return strawberry.Schema(query=Query, config=strawberry_config(), types=[CategoryNode])


_STRAWBERRY_NODE_QUERY = (
    "query ($bad: ID!, $good: ID!) { node(id: $bad) { __typename }"
    " nodes(ids: [$bad, $good]) { ... on CategoryNode { name } } }"
)


@pytest.mark.django_db
def test_default_resolvers_read_an_uncoercible_id_as_no_row_under_strawberrys_node_field():
    """``library.genre:abc``-shaped ids reach the defaults raw through ``relay.node()``.

    Strawberry's own field has no id-slot gate, so the default resolvers own the
    coercion: an uncoercible literal identifies no row (``null`` / a positional
    ``null`` hole) instead of leaking Django's ``ValueError`` from
    ``filter(pk="abc")``, and a required field raises the model's
    ``DoesNotExist``, homogeneous with a missing row.
    """
    services.seed_data(1)
    schema = _strawberry_node_schema()
    row = Category.objects.order_by("pk").first()
    assert row is not None
    bad, good = _gid("CategoryNode", "abc"), _gid("CategoryNode", row.pk)

    result = schema.execute_sync(
        _STRAWBERRY_NODE_QUERY,
        variable_values={"bad": bad, "good": good},
    )
    assert result.errors is None
    assert result.data == {"node": None, "nodes": [None, {"name": row.name}]}

    required = schema.execute_sync(
        "query ($bad: ID!) { requiredNode(id: $bad) { __typename } }",
        variable_values={"bad": bad},
    )
    assert required.errors is not None
    assert isinstance(required.errors[0].original_error, Category.DoesNotExist)
    assert "no row matching pk='abc'" in str(required.errors[0])


@pytest.mark.django_db(transaction=True)
async def test_async_default_resolvers_read_an_uncoercible_id_as_no_row():
    """The async defaults take the same no-row reading of an uncoercible id."""
    await sync_to_async(services.seed_data)(1)
    schema = _strawberry_node_schema()
    row = await Category.objects.order_by("pk").afirst()
    assert row is not None
    bad, good = _gid("CategoryNode", "abc"), _gid("CategoryNode", row.pk)

    result = await schema.execute(
        _STRAWBERRY_NODE_QUERY,
        variable_values={"bad": bad, "good": good},
    )

    assert result.errors is None
    assert result.data == {"node": None, "nodes": [None, {"name": row.name}]}


# ---------------------------------------------------------------------------
# Construction-time guards + finalize-time ledger check
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("factory", [DjangoNodeField, DjangoNodesField])
def test_node_field_target_guards(factory: Callable[..., object]):
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


@pytest.mark.parametrize("factory", [DjangoNodeField, DjangoNodesField])
@pytest.mark.parametrize("bare", ["@deprecated", b"@deprecated"])
def test_node_field_rejects_bare_string_directives(
    factory: Callable[..., object],
    bare: str | bytes,
):
    """A bare str / bytes ``directives`` is rejected at the construction line.

    Both root Relay factories forwarded ``directives`` to ``strawberry.field()``
    unvalidated, so a bare string was iterated character-wise into a field whose
    "directives" are chars without ``__strawberry_directive__`` (raw
    AttributeError at schema build) and a bytes built silently then crashed SDL
    render. The containment is
    ``utils/directives.py::validated_field_directives``.
    """
    with pytest.raises(
        ConfigurationError,
        match=rf"{factory.__name__} directives must be a sequence of directive instances",
    ):
        factory(directives=bare)


@pytest.mark.parametrize("factory", [DjangoNodeField, DjangoNodesField])
def test_node_field_rejects_hostile_directives_iterator(factory: Callable[..., object]):
    """A hostile iterator escaped raw pre-fix; a non-iterable detonated as TypeError.

    The rejection also runs BEFORE the ``_node_fields_declared`` ledger append,
    so a refused construction leaves no phantom entry behind the finalize-time
    no-Node-types check.
    """

    class HostileDirectives:
        def __iter__(self):
            raise RuntimeError("hostile iterator detonated")

    with pytest.raises(
        ConfigurationError,
        match=rf"{factory.__name__} directives could not be read",
    ) as exc:
        factory(directives=HostileDirectives())
    assert isinstance(exc.value.__cause__, RuntimeError)

    with pytest.raises(
        ConfigurationError,
        match=rf"{factory.__name__} directives could not be read",
    ) as exc:
        factory(directives=42)
    assert isinstance(exc.value.__cause__, TypeError)

    assert _node_fields_declared == []


@pytest.mark.parametrize("factory", [DjangoNodeField, DjangoNodesField])
def test_node_field_passes_real_directive_instances_through(factory: Callable[..., object]):
    """Positive control: a genuine directive instance still constructs and declares."""

    @schema_directive(locations=[DirectiveLocation.FIELD_DEFINITION], name="probeTag")
    class ProbeTag:
        marker: str = "probe"

    assert factory(directives=(ProbeTag(),)) is not None
    assert _node_fields_declared == [factory.__name__]


def test_node_field_without_node_types_raises_at_finalize():
    """The ledger check fires with the documented message; ``registry.clear()`` resets it."""

    class PlainCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is PlainCategoryType

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
# Consumer resolve_nodes override + SyncMisuseError pass-through
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_nodes_async_with_sync_consumer_resolve_nodes_override():
    """A SYNCHRONOUS consumer ``resolve_nodes`` override works under async execution.

    The batch gatherer must treat ``resolve_nodes`` as AwaitableOrValue: the
    framework default returns a coroutine in async context, but a valid sync
    consumer override returns the list directly. Awaiting it unconditionally
    raised ``TypeError: 'list' object can't be awaited``.
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
            info: strawberry.Info,
            node_ids: Iterable[str],
            required: bool = False,
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
    assert result.data is not None
    assert result.data["nodes"] == [{"__typename": "CategoryNode", "name": target.name}]


@pytest.mark.django_db
def test_node_sync_with_async_consumer_resolve_node_raises_sync_misuse():
    """Sync node refetch rejects an async consumer ``resolve_node`` explicitly."""
    services.seed_data(1)

    class AsyncCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        async def resolve_node(
            cls,
            node_id: str,
            *,
            info: strawberry.Info,
            required: bool = False,
        ):
            del cls, node_id, info, required
            return None

    schema = _schema_with(
        "category",
        AsyncCategoryNode | None,
        DjangoNodeField(AsyncCategoryNode),
    )
    row = Category.objects.order_by("pk").first()
    assert row is not None
    result = schema.execute_sync(
        _CATEGORY_QUERY,
        variable_values={"id": _gid("products.category", row.pk)},
    )
    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "resolve_node" in str(result.errors[0])
    assert result.data == {"category": None}


@pytest.mark.django_db(transaction=True)
async def test_node_sync_operation_inside_an_event_loop_never_calls_async_resolve_node():
    """``execute_sync`` under a running loop refuses before the override is called.

    Masking is off because the subject is the typed error itself.
    """
    await sync_to_async(services.seed_data)(1)
    calls: list[str] = []

    async def _no_row() -> None:
        return None

    class AsyncCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        def resolve_node(
            cls,
            node_id: str,
            *,
            info: strawberry.Info,
            required: bool = False,
        ) -> Awaitable[None]:
            del cls, info, required
            calls.append(node_id)
            return _no_row()

    @strawberry.type
    class Query:
        category: AsyncCategoryNode | None = DjangoNodeField(AsyncCategoryNode)

    await sync_to_async(finalize_django_types)()
    schema = DjangoSchema(query=Query, error_policy=ErrorPolicy(enabled=False))
    row = await Category.objects.order_by("pk").afirst()
    assert row is not None

    result = schema.execute_sync(
        _CATEGORY_QUERY,
        variable_values={"id": _gid("products.category", row.pk)},
    )

    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "await schema.execute" in str(result.errors[0])
    assert result.data == {"category": None}
    assert calls == []


@pytest.mark.django_db
def test_nodes_sync_with_async_consumer_resolve_nodes_raises_sync_misuse():
    """Sync batch refetch rejects an async consumer ``resolve_nodes`` explicitly."""
    services.seed_data(1)

    class AsyncCategoryNode(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")
            interfaces = (relay.Node,)
            name = "CategoryNode"

        @classmethod
        async def resolve_nodes(
            cls,
            *,
            info: strawberry.Info,
            node_ids: Iterable[str],
            required: bool = False,
        ):
            del cls, info, required
            return [None for _ in node_ids]

    schema = _schema_with(
        "categories",
        list[AsyncCategoryNode | None],
        DjangoNodesField(AsyncCategoryNode),
    )
    row = Category.objects.order_by("pk").first()
    assert row is not None
    result = schema.execute_sync(
        _CATEGORIES_QUERY,
        variable_values={"ids": [_gid("products.category", row.pk)]},
    )
    assert result.errors is not None
    assert isinstance(result.errors[0].original_error, SyncMisuseError)
    assert "resolve_nodes" in str(result.errors[0])
    assert result.data is None


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
            info: strawberry.Info,
            node_ids: Iterable[str],
            required: bool = False,
        ) -> list[Self]:
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
    """A consumer ``resolve_nodes`` override may return a generator.

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
            info: strawberry.Info,
            node_ids: Iterable[str],
            required: bool = False,
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
    assert result.data is not None
    assert result.data["categories"] == [{"name": second.name}, {"name": first.name}]


@pytest.mark.django_db
def test_node_sync_async_get_queryset_raises_sync_misuse():
    """An async ``get_queryset`` under sync execution surfaces SyncMisuseError, NOT GLOBALID_INVALID.

    Discriminating (spec-032 Decision 5): ``SyncMisuseError`` IS-A
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
        @override
        # basedpyright: deliberately async on the sync path: the coroutine is the input the guard refuses
        async def get_queryset(cls, queryset: QuerySet[Category], info: object, **kwargs: object):  # pyright: ignore[reportIncompatibleMethodOverride]
            return queryset

    schema = _schema_with(
        "category",
        AsyncCategoryNode | None,
        DjangoNodeField(AsyncCategoryNode),
    )
    row = Category.objects.order_by("pk").first()
    assert row is not None
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
