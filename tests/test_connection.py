"""DjangoConnection and DjangoConnectionField tests for Relay pagination behavior.

Spec: ``docs/spec-030-connection_field-0_0_9.md`` (Slice 1 / Slice 2 checklists;
Test plan Slice 1 / Slice 2 sections). Package tests; system-under-test is
``django_strawberry_framework`` itself. The flat file mirrors the flat
``connection.py`` module per ``docs/TREE.md`` and the ``tests/test_list_field.py``
precedent.

``DjangoConnectionField`` IS now reachable from a live ``/graphql/`` query
(the fakeshop ``library`` app ships
``all_library_genres_connection: DjangoConnection[GenreType] = DjangoConnectionField(GenreType)``,
and the products app is connections-only), and the live suite carries the
consumer round-trips (filter + orderBy + cursor + totalCount). The tests here
stay package-side because they assert what a live query cannot: the
``resolve_connection`` ``first`` + ``last`` guard driven at the classmethod
directly (the guard runs before any ``info`` use), generated-connection-type
caching, the concrete-subclass specialization regression, and the
non-queryset-iterable guards - per the ``examples/fakeshop/test_query/README.md``
live-HTTP-first rule's "keep when it asserts internal state / construction-time
validation" clause.
"""

import asyncio
import gc
import warnings
from collections.abc import Iterable
from types import SimpleNamespace

import pytest
import strawberry
from apps.kanban.models import Status
from apps.products import services
from apps.products.models import Category, Item
from django.db.models import F
from django.http import HttpRequest
from graphql import GraphQLError
from strawberry import relay

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import (
    DjangoConnection,
    DjangoConnectionField,
    _attach_count_async,
    _connection_type_cache,
    _connection_type_for,
    _ends_in_unique_column,
    _finalize_queryset,
    _total_count_requested,
    clear_connection_type_cache,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet, _helper_referenced_filtersets
from django_strawberry_framework.orders import OrderSet, _helper_referenced_ordersets
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.relay import SyncMisuseError


@pytest.fixture(autouse=True)
def _isolate_global_registry():
    """Clear the global registry and the connection-type cache around each test.

    Connection classes are cached on ``target_type`` identity; function-scope
    ``DjangoType`` fixtures are recreated fresh each test, so clearing the cache
    keeps a discarded class from leaking into a later test's identity check.
    """
    registry.clear()
    _connection_type_cache.clear()
    yield
    registry.clear()
    _connection_type_cache.clear()


def _make_node_type(name: str, *, total_count: bool | None) -> type:
    """Build a Relay-Node-shaped ``DjangoType`` over ``Category`` for a test.

    ``total_count`` controls the opt-in: ``True`` / ``False`` declares
    ``Meta.connection = {"total_count": ...}``; ``None`` omits the key.
    """
    meta_attrs = {
        "model": Category,
        "fields": ("id", "name"),
        "interfaces": (relay.Node,),
        "name": name,
    }
    if total_count is not None:
        meta_attrs["connection"] = {"total_count": total_count}
    return type(name, (DjangoType,), {"Meta": type("Meta", (), meta_attrs)})


def _schema_for(node_type: type) -> strawberry.Schema:
    """Build an in-process schema exposing ``items`` as a connection over ``node_type``.

    The connection type comes from ``_connection_type_for`` so the schema
    exercises whichever generated ``<TypeName>Connection`` shape (with or
    without ``totalCount``) the node type's ``Meta.connection`` selects,
    through the real Strawberry relay slicing / ``info`` path.
    """
    connection_type = _connection_type_for(node_type)

    def items_resolver() -> Iterable[node_type]:
        return Category.objects.all().order_by("pk")

    query_namespace = {
        "__annotations__": {"items": connection_type},
        "items": relay.connection(connection_type, resolver=items_resolver),
    }
    query_cls = strawberry.type(type("Query", (), query_namespace))
    finalize_django_types()
    return strawberry.Schema(query=query_cls, config=strawberry_config())


# =============================================================================
# DjangoConnection base shape + first/last guard
# =============================================================================


def test_django_connection_is_listconnection_subclass():
    """``DjangoConnection`` is a ``ListConnection`` subclass with no ``total_count`` field."""
    assert issubclass(DjangoConnection, relay.ListConnection)
    assert "total_count" not in getattr(DjangoConnection, "__annotations__", {})

    # The parametrized form is a generic alias whose origin is ``DjangoConnection``.
    node_type = _make_node_type("GuardNode", total_count=None)
    specialized = DjangoConnection[node_type]
    assert specialized.__origin__ is DjangoConnection


def test_first_and_last_raises_graphql_error():
    """``resolve_connection`` with both ``first`` and ``last`` raises ``GraphQLError``.

    The package's own guard - Strawberry's ``SliceMetadata.from_arguments`` does
    not reject the combination. Driven at the classmethod directly with a
    sentinel ``info`` (the guard runs before any ``info`` use).
    """
    with pytest.raises(GraphQLError, match="mutually exclusive"):
        DjangoConnection.resolve_connection([], info=object(), first=1, last=1)


def test_first_and_last_guard_on_generated_subclass():
    """The generated ``<TypeName>Connection`` shares the ``first`` + ``last`` guard."""
    node_type = _make_node_type("GuardCountNode", total_count=True)
    connection_type = _connection_type_for(node_type)

    with pytest.raises(GraphQLError, match="mutually exclusive"):
        connection_type.resolve_connection([], info=object(), first=1, last=1)


# =============================================================================
# _connection_type_for: generation + caching + presence-by-opt-in
# =============================================================================


def test_connection_type_for_caches_per_target():
    """``_connection_type_for`` returns one cached class object per node type."""
    node_type = _make_node_type("CacheNode", total_count=True)

    first = _connection_type_for(node_type)
    second = _connection_type_for(node_type)
    assert first is second


def test_connection_type_for_generates_named_subclass_when_opted_in():
    """A ``total_count``-enabled type yields ``<TypeName>Connection`` declaring ``total_count``."""
    node_type = _make_node_type("OptedNode", total_count=True)

    connection_type = _connection_type_for(node_type)
    assert connection_type.__name__ == "OptedNodeConnection"
    assert "total_count" in connection_type.__annotations__
    assert issubclass(connection_type, DjangoConnection)


def test_generated_connection_name_uses_graphql_type_name_not_python_name():
    """Generated ``<Type>Connection`` names derive from ``graphql_type_name``, not ``__name__``.

    P1 (``docs/feedback.md``): two DjangoType classes can share a Python
    ``__name__`` while declaring distinct ``Meta.name`` values. Naming the
    generated connection from ``__name__`` produces two classes with the SAME
    SDL type name, which Strawberry collapses into one - corrupting both root
    fields' ``edges`` / node types. Deriving from ``graphql_type_name`` (the
    canonical surface name, ``Meta.name`` when set) keeps them distinct.
    """

    def _dup_named_node(meta_name: str, model: type) -> type:
        # Identical Python ``__name__`` ("NodeType") for BOTH; distinct Meta.name.
        return type(
            "NodeType",
            (DjangoType,),
            {
                "Meta": type(
                    "Meta",
                    (),
                    {
                        "model": model,
                        "fields": ("id", "name"),
                        "interfaces": (relay.Node,),
                        "name": meta_name,
                        "connection": {"total_count": True},
                    },
                ),
            },
        )

    category_node = _dup_named_node("PublicCategory", Category)
    item_node = _dup_named_node("PublicItem", Item)

    cat_conn = _connection_type_for(category_node)
    item_conn = _connection_type_for(item_node)

    # Distinct classes, each named from its ``graphql_type_name`` (Meta.name) -
    # not a single colliding ``NodeTypeConnection``.
    assert cat_conn.__name__ == "PublicCategoryConnection"
    assert item_conn.__name__ == "PublicItemConnection"
    assert cat_conn is not item_conn

    def _categories() -> Iterable[category_node]:
        return Category.objects.all().order_by("pk")

    def _items() -> Iterable[item_node]:
        return Item.objects.all().order_by("pk")

    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"categories": cat_conn, "items": item_conn},
                "categories": relay.connection(cat_conn, resolver=_categories),
                "items": relay.connection(item_conn, resolver=_items),
            },
        ),
    )
    finalize_django_types()
    sdl = str(strawberry.Schema(query=query_cls, config=strawberry_config()))

    # Both connection types present and distinct; no collapsed collision.
    assert "PublicCategoryConnection" in sdl
    assert "PublicItemConnection" in sdl
    assert "NodeTypeConnection" not in sdl
    # Each connection exposes its own edge type - no cross-wiring of node edges.
    assert "PublicCategoryEdge" in sdl
    assert "PublicItemEdge" in sdl


def test_connection_type_for_returns_concrete_subclass_without_opt_in():
    """A non-opted Relay-Node type yields a generated concrete subclass without ``total_count``.

    Never the ``DjangoConnection[T]`` generic alias: a generic alias handed to
    the schema loses the ``resolve_connection`` override (and with it the
    ``first`` + ``last`` guard) at Strawberry's generic specialization - the
    spec-032 Slice-4 discovered bug. The non-opted path must be a concrete
    class too, just with no ``total_count`` members.
    """
    node_type = _make_node_type("BareNode", total_count=None)

    connection_type = _connection_type_for(node_type)
    assert issubclass(connection_type, DjangoConnection)
    assert connection_type is not DjangoConnection
    assert connection_type.__name__ == "BareNodeConnection"
    assert "total_count" not in getattr(connection_type, "__annotations__", {})


def test_connection_type_for_returns_concrete_subclass_when_total_count_false():
    """``connection = {"total_count": False}`` yields the concrete subclass, no ``totalCount`` variant."""
    node_type = _make_node_type("FalseNode", total_count=False)

    connection_type = _connection_type_for(node_type)
    assert issubclass(connection_type, DjangoConnection)
    assert connection_type is not DjangoConnection
    assert connection_type.__name__ == "FalseNodeConnection"
    assert "total_count" not in getattr(connection_type, "__annotations__", {})


def test_total_count_present_only_when_opted_in():
    """``totalCount`` is in the SDL for an opted-in type and absent for a bare one."""
    opted_schema = _schema_for(_make_node_type("PresentOpted", total_count=True))
    assert "totalCount" in str(opted_schema)

    registry.clear()
    _connection_type_cache.clear()

    bare_schema = _schema_for(_make_node_type("PresentBare", total_count=None))
    assert "totalCount" not in str(bare_schema)
    # SDL description parity (spec-032 Slice-4 amendment): the always-concrete
    # non-opted ``<TypeName>Connection`` must preserve the description the bare
    # ``DjangoConnection[T]`` alias inherited from Strawberry's ``Connection``
    # base - the production code reads it from the parent strawberry definition;
    # the literal is pinned here so a silent drop regresses loudly.
    assert "A connection to a list of items." in str(bare_schema)


# =============================================================================
# _total_count_requested selection-gating (unit)
# =============================================================================


def _selection(name: str, selections=()):
    """A minimal selection double exposing ``.name`` / ``.selections``."""
    return SimpleNamespace(name=name, selections=list(selections))


def _info_with_selection(*field_names: str):
    """An ``info`` double whose connection selection set carries ``field_names``."""
    inner = [_selection(name) for name in field_names]
    return SimpleNamespace(selected_fields=[_selection("connectionField", inner)])


def test_total_count_requested_true_when_selected():
    """``_total_count_requested`` is True when ``totalCount`` is in the selection set."""
    assert _total_count_requested(_info_with_selection("edges", "totalCount")) is True


def test_total_count_requested_false_when_absent():
    """``_total_count_requested`` is False when ``totalCount`` is not selected."""
    assert _total_count_requested(_info_with_selection("edges", "pageInfo")) is False


def test_total_count_requested_scoped_to_direct_children():
    """A ``totalCount`` nested in ``edges { node { ... } }`` does NOT fire the predicate (P2).

    ``_total_count_requested`` checks only the connection's DIRECT children, so a
    (future) node-level ``totalCount`` deep in the subtree must not make the
    OUTER connection count spuriously (``docs/feedback.md`` P2). A direct-child
    ``totalCount`` still counts.
    """
    # Direct-child ``totalCount`` still counts.
    assert _total_count_requested(_info_with_selection("edges", "totalCount")) is True
    # ``totalCount`` ONLY nested inside ``edges { node { ... } }`` must NOT count:
    # the predicate does not descend into a regular field's selections.
    nested = SimpleNamespace(
        selected_fields=[
            _selection(
                "connectionField",
                [
                    _selection("edges", [_selection("node", [_selection("totalCount")])]),
                    _selection("pageInfo"),
                ],
            ),
        ],
    )
    assert _total_count_requested(nested) is False


def test_total_count_requested_recurses_through_fragments():
    """``_total_count_requested`` recurses THROUGH fragment wrappers to find ``totalCount`` (P2).

    A ``totalCount`` reached only via a ``FragmentSpread`` / ``InlineFragment`` on
    the connection's direct selection set still counts -- the predicate descends
    into fragment ``.selections`` (but not into regular fields).
    """
    from strawberry.types.nodes import FragmentSpread, InlineFragment

    # ``totalCount`` reached only via a FragmentSpread on the connection's selections.
    spread = FragmentSpread(
        name="ConnFields",
        type_condition="XConnection",
        directives={},
        selections=[_selection("totalCount")],
    )
    info = SimpleNamespace(
        selected_fields=[_selection("connectionField", [_selection("edges"), spread])],
    )
    assert _total_count_requested(info) is True

    # An InlineFragment WITHOUT totalCount stays False (recursion returns nothing).
    inline = InlineFragment(
        type_condition="XConnection",
        selections=[_selection("pageInfo")],
        directives={},
    )
    info_no_count = SimpleNamespace(
        selected_fields=[_selection("connectionField", [inline])],
    )
    assert _total_count_requested(info_no_count) is False


# =============================================================================
# totalCount counting + selection-gating through a real schema query
# =============================================================================


@pytest.mark.django_db
def test_first_and_last_graphql_error_through_schema_without_opt_in():
    """The ``first`` + ``last`` guard fires through-schema with NO ``totalCount`` opt-in.

    Deliberate near-twin of the opted sibling above: the two dispatch shapes
    (opted ``totalCount`` subclass vs the non-opted generated subclass) are
    exactly the contract under test. Before the spec-032 Slice-4 fix the
    non-opted path handed the schema the bare ``DjangoConnection[T]`` alias,
    whose ``resolve_connection`` override Strawberry's generic specialization
    dropped - ``first: 1, last: 1`` resolved silently. This is the ROOT-level
    pin of the fixed dispatch (the synthesized-relation pin lives in
    ``tests/test_relay_connection.py::test_relation_connection_first_and_last_rejected``).
    """
    services.seed_data(2)
    schema = _schema_for(_make_node_type("BareBothArgsNode", total_count=None))

    result = schema.execute_sync(
        "{ items(first: 1, last: 1) { edges { node { id } } } }",
    )
    assert result.errors is not None
    assert any("mutually exclusive" in str(err.message) for err in result.errors)


@pytest.mark.django_db(transaction=True)
async def test_total_count_async_path_counts_via_acount():
    """The async execution path counts via ``.acount()`` and attaches it to the instance."""
    from asgiref.sync import sync_to_async

    await sync_to_async(services.seed_data)(2)
    expected = await Category.objects.acount()

    schema = await sync_to_async(_schema_for)(_make_node_type("AsyncCountNode", total_count=True))
    result = await schema.execute(
        "{ items(first: 1) { edges { node { id } } totalCount } }",
    )
    assert result.errors is None
    assert result.data["items"]["totalCount"] == expected


# =============================================================================
# Slice 2 - DjangoConnectionField factory + pipeline + sidecar args
# =============================================================================


class _CategoryFilter(FilterSet):
    class Meta:
        model = Category
        fields = {"name": ["exact", "icontains"]}


class _CategoryOrder(OrderSet):
    class Meta:
        model = Category
        fields = ["name"]


def _make_sidecar_node_type(
    name: str,
    *,
    total_count: bool = False,
    filterset: type | None = _CategoryFilter,
    orderset: type | None = _CategoryOrder,
    get_queryset=None,
) -> type:
    """Build a Relay-Node ``DjangoType`` over ``Category`` with optional sidecars.

    ``filterset`` / ``orderset`` default to the module fixtures; pass ``None`` to
    omit a sidecar. ``get_queryset`` (when given) is installed as a method so the
    visibility hook / ``SyncMisuseError`` paths can be exercised.
    """
    meta_attrs: dict = {
        "model": Category,
        "fields": ("id", "name"),
        "interfaces": (relay.Node,),
        "name": name,
    }
    if filterset is not None:
        meta_attrs["filterset_class"] = filterset
    if orderset is not None:
        meta_attrs["orderset_class"] = orderset
    if total_count:
        meta_attrs["connection"] = {"total_count": True}
    namespace: dict = {"Meta": type("Meta", (), meta_attrs)}
    if get_queryset is not None:
        namespace["get_queryset"] = classmethod(get_queryset)
    return type(name, (DjangoType,), namespace)


def _field_schema(
    node_type: type,
    *,
    resolver=None,
    optimizer=None,
    config=None,
) -> strawberry.Schema:
    """Build an in-process schema exposing ``items`` via ``DjangoConnectionField``.

    ``config`` overrides the default ``strawberry_config()`` (e.g. a
    ``relay_max_results`` passthrough); ``None`` keeps the default.
    """
    conn_type = _connection_type_for(node_type)
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"items": conn_type},
                "items": DjangoConnectionField(node_type, resolver=resolver),
            },
        ),
    )
    finalize_django_types()
    extensions = [lambda: optimizer] if optimizer is not None else []
    return strawberry.Schema(
        query=query_cls,
        config=config or strawberry_config(),
        extensions=extensions,
    )


def _capture_info(node_type: type):
    """Return a real resolver ``Info`` captured from an in-process execution.

    The composition-pipeline helpers (``_pipeline_sync`` / ``_finalize_queryset``)
    need a real ``Info`` (the optimizer plan reads ``info._raw_info`` for
    ``field_nodes`` / ``operation`` / ``fragments``); a ``SimpleNamespace`` double
    is insufficient. A hand-written ``relay.connection`` resolver stashes the
    ``Info`` it is handed during a throwaway query.
    """
    conn_type = _connection_type_for(node_type)
    captured: dict = {}

    def capture(root, info: strawberry.types.Info) -> Iterable[node_type]:
        captured["info"] = info
        return Category.objects.all()

    query_cls = strawberry.type(
        type(
            "CaptureQuery",
            (),
            {
                "__annotations__": {"items": conn_type},
                "items": relay.connection(conn_type, resolver=capture),
            },
        ),
    )
    finalize_django_types()
    schema = strawberry.Schema(query=query_cls, config=strawberry_config())
    schema.execute_sync("{ items { edges { node { id } } } }")
    return captured["info"]


# --- Constructor guards ------------------------------------------------------


def test_connection_field_requires_djangotype():
    """A non-class target raises ``ConfigurationError``."""
    with pytest.raises(ConfigurationError, match="requires a DjangoType class"):
        DjangoConnectionField(42)


def test_connection_field_requires_djangotype_subclass():
    """A non-``DjangoType`` class raises ``ConfigurationError``."""

    class Plain:
        pass

    with pytest.raises(ConfigurationError, match="requires a DjangoType subclass"):
        DjangoConnectionField(Plain)


def test_connection_field_requires_own_class_definition():
    """A subclass without its own ``Meta`` (inherited definition) is rejected."""
    parent = _make_sidecar_node_type("OwnClassParent")

    class Child(parent):
        pass

    with pytest.raises(ConfigurationError, match="not a registered DjangoType"):
        DjangoConnectionField(Child)


def test_connection_field_rejects_non_callable_resolver():
    """A non-callable ``resolver=`` raises ``ConfigurationError``."""
    node_type = _make_sidecar_node_type("NonCallableResolverNode")
    with pytest.raises(ConfigurationError, match="resolver must be callable"):
        DjangoConnectionField(node_type, resolver="not callable")


def test_connection_field_requires_relay_node():
    """A non-Relay ``DjangoType`` raises ``ConfigurationError`` naming ``relay.Node``."""
    non_relay = type(
        "NonRelayNode",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": Category, "fields": ("id", "name"), "name": "NRN"})},
    )
    with pytest.raises(ConfigurationError, match="relay.Node"):
        DjangoConnectionField(non_relay)


def test_connection_field_accepts_direct_relay_node_inheritance():
    """A direct ``class Foo(DjangoType, relay.Node)`` (no ``Meta.interfaces``) is accepted.

    ``docs/feedback.md`` Open Question: direct ``relay.Node`` inheritance is a
    supported, fully-finalizable Relay shape (the finalizer keys Relay wiring off
    ``implements_relay_node``, not a non-empty ``Meta.interfaces``). The
    connection guard reuses the canonical ``_is_relay_shaped`` predicate, so it
    accepts this Strawberry-native spelling without a ``ConfigurationError`` -
    even though ``definition.interfaces`` is empty.
    """

    class DirectRelayNode(DjangoType, relay.Node):
        class Meta:
            model = Category
            fields = ("id", "name")
            name = "DirectRelayNode"

    # ``relay.Node`` is NOT in the declared Meta-tuple; acceptance comes purely
    # from the direct MRO inheritance (``issubclass(target_type, relay.Node)``).
    assert relay.Node not in DirectRelayNode.__django_strawberry_definition__.interfaces
    # Does not raise; produces a connection field over the bare connection shape.
    field = DjangoConnectionField(DirectRelayNode)
    assert field is not None


def test_connection_type_for_generates_total_count_for_direct_relay_inheritance():
    """Direct ``relay.Node`` inheritance can use the per-type ``totalCount`` opt-in (P2).

    ``docs/feedback.md`` P2: once ``Meta.connection`` validation accepts direct
    inheritance, the ``totalCount`` surface works for it too -
    ``_connection_type_for`` generates the concrete ``<Name>Connection`` carrying
    ``total_count`` exactly as it does for the ``Meta.interfaces`` spelling.
    """

    class DirectCountNode(DjangoType, relay.Node):
        class Meta:
            model = Category
            fields = ("id", "name")
            name = "DirectCount"
            connection = {"total_count": True}

    assert relay.Node not in DirectCountNode.__django_strawberry_definition__.interfaces
    connection_type = _connection_type_for(DirectCountNode)
    assert connection_type.__name__ == "DirectCountConnection"
    assert "total_count" in connection_type.__annotations__

    # Schema-level: ``totalCount`` is exposed in the SDL for the direct-inheritance type.
    sdl = str(_schema_for(DirectCountNode))
    assert "totalCount" in sdl


# --- Argument presence / absence by sidecar declaration ----------------------


def test_connection_field_derives_filter_arg_from_filterset():
    """A type with ``filterset_class`` emits a ``filter:`` argument in the SDL."""
    schema = _field_schema(_make_sidecar_node_type("FilterArgNode", orderset=None))
    sdl = str(schema)
    assert "filter:" in sdl
    assert "orderBy:" not in sdl


def test_connection_field_derives_orderby_arg_from_orderset():
    """A type with ``orderset_class`` emits an ``orderBy:`` argument in the SDL."""
    schema = _field_schema(_make_sidecar_node_type("OrderArgNode", filterset=None))
    sdl = str(schema)
    assert "orderBy:" in sdl
    assert "filter:" not in sdl


def test_connection_field_omits_args_without_sidecars():
    """A type with neither sidecar emits only the four Relay pagination args."""
    schema = _field_schema(
        _make_sidecar_node_type("NoSidecarNode", filterset=None, orderset=None),
    )
    sdl = str(schema)
    assert "filter:" not in sdl
    assert "orderBy:" not in sdl
    # The four Relay pagination args are still present.
    for arg in (
        "before:",
        "after:",
        "first:",
        "last:",
    ):
        assert arg in sdl


# --- Orphan-ledger registration ----------------------------------------------


def test_connection_field_registers_sidecars_against_orphan_ledgers():
    """Constructing the field records the FilterSet / OrderSet in the orphan ledgers."""
    node_type = _make_sidecar_node_type("LedgerNode")
    _helper_referenced_filtersets.discard(_CategoryFilter)
    _helper_referenced_ordersets.discard(_CategoryOrder)

    DjangoConnectionField(node_type)

    assert _CategoryFilter in _helper_referenced_filtersets
    assert _CategoryOrder in _helper_referenced_ordersets


# --- Four consumer-resolver cases --------------------------------------------


@pytest.mark.django_db
def test_consumer_resolver_manager_coerced():
    """A ``Manager`` return is coerced to a ``QuerySet`` and runs the full pipeline."""
    services.seed_data(2)

    def resolver(root, info) -> Iterable:
        return Category.objects  # a Manager, not a QuerySet

    schema = _field_schema(_make_sidecar_node_type("ManagerNode"), resolver=resolver)
    result = schema.execute_sync("{ items { edges { node { id } } } }")
    assert result.errors is None
    assert len(result.data["items"]["edges"]) == Category.objects.count()


@pytest.mark.django_db
def test_consumer_resolver_queryset_full_pipeline():
    """A ``QuerySet`` return runs visibility / filter / order / default-order / optimizer."""
    services.seed_data(2)

    def resolver(root, info) -> Iterable:
        return Category.objects.all()

    schema = _field_schema(_make_sidecar_node_type("QuerySetNode"), resolver=resolver)
    result = schema.execute_sync(
        '{ items(filter: {name: {iContains: ""}}, orderBy: [{name: ASC}]) '
        "{ edges { node { name } } } }",
        context_value=HttpRequest(),
    )
    assert result.errors is None
    names = [edge["node"]["name"] for edge in result.data["items"]["edges"]]
    assert names == sorted(names)


@pytest.mark.django_db
def test_consumer_resolver_iterable_without_sidecar_input_paginates():
    """A non-queryset iterable with NO sidecar input paginates normally."""
    services.seed_data(1)
    rows = list(Category.objects.all())

    def resolver(root, info) -> Iterable:
        return list(rows)  # a plain list

    schema = _field_schema(_make_sidecar_node_type("IterableOkNode"), resolver=resolver)
    result = schema.execute_sync("{ items(first: 1) { edges { node { id } } } }")
    assert result.errors is None
    assert len(result.data["items"]["edges"]) == 1


@pytest.mark.django_db
def test_consumer_resolver_iterable_with_sidecar_input_raises():
    """A non-queryset iterable WITH ``filter:`` / ``orderBy:`` input raises a package error."""
    services.seed_data(1)
    rows = list(Category.objects.all())

    def resolver(root, info) -> Iterable:
        return list(rows)

    schema = _field_schema(_make_sidecar_node_type("IterableBadNode"), resolver=resolver)
    result = schema.execute_sync(
        '{ items(filter: {name: {exact: "x"}}) { edges { node { id } } } }',
    )
    assert result.errors is not None
    assert any("non-queryset iterable" in str(err.message) for err in result.errors)


@pytest.mark.django_db
def test_consumer_resolver_iterable_with_total_count_selected_raises():
    """M1: selecting ``totalCount`` over a non-queryset consumer return raises a package error.

    NOT the engine's ``Cannot return null for non-nullable field ...totalCount``
    violation - the count helper raises a clear ``GraphQLError`` because a plain
    iterable cannot be ``.count()``-ed into the non-null ``totalCount: Int!``.
    """
    services.seed_data(1)
    rows = list(Category.objects.all())

    def resolver(root, info) -> Iterable:
        return list(rows)

    schema = _field_schema(
        _make_sidecar_node_type("IterableTotalCountNode", total_count=True),
        resolver=resolver,
    )
    result = schema.execute_sync("{ items { edges { node { id } } totalCount } }")
    assert result.errors is not None
    messages = [str(err.message) for err in result.errors]
    assert any("totalCount" in m and "non-queryset iterable" in m for m in messages)
    assert not any("Cannot return null for non-nullable field" in m for m in messages)


async def test_attach_count_async_awaits_before_guard_raises():
    """``_attach_count_async`` awaits the connection coroutine BEFORE the M1 guard can raise.

    Regression guard for the await-before-raise discipline (Decision 10, mirroring
    ``utils/querysets.py::apply_type_visibility_sync``'s close-before-raise). With the
    pre-fix ordering (guard first), a guard-raise on the non-queryset + ``totalCount``
    path left the queued connection coroutine unawaited -> ``RuntimeWarning: coroutine
    ... was never awaited`` (a hard failure under ``-W error``). Deterministic: assert
    the coroutine was actually awaited (``consumed``) AND that no unawaited-coroutine
    ``RuntimeWarning`` leaks even after a forced GC.
    """
    consumed = {"flag": False}

    async def make_conn():
        consumed["flag"] = True
        return SimpleNamespace()

    coro = make_conn()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(GraphQLError, match="totalCount"):
            await _attach_count_async(coro, ["not", "a", "queryset"], want_count=True)
        gc.collect()
        leaked = [
            w
            for w in caught
            if issubclass(w.category, RuntimeWarning) and "never awaited" in str(w.message)
        ]

    assert consumed["flag"], "the connection coroutine must be awaited before the guard raises"
    assert not leaked, (
        f"unawaited-coroutine RuntimeWarning leaked: {[str(w.message) for w in leaked]}"
    )


@pytest.mark.django_db(transaction=True)
async def test_async_consumer_resolver_iterable_with_total_count_selected_raises():
    """M1 end-to-end on the async path: a clear package error, NOT the engine non-null violation.

    An ``async def`` consumer ``resolver=`` returning a non-queryset iterable while
    ``totalCount`` is selected drives ``_attach_count_async`` through the real
    ``resolve_connection`` async path. The guard's ``GraphQLError`` surfaces (NOT the
    engine ``Cannot return null for non-nullable field ...totalCount`` violation). The
    deterministic no-leak assertion lives in
    ``test_attach_count_async_awaits_before_guard_raises``.
    """
    from asgiref.sync import sync_to_async

    await sync_to_async(services.seed_data)(1)
    rows = await sync_to_async(lambda: list(Category.objects.all()))()

    async def resolver(root, info) -> Iterable:
        return list(rows)

    schema = await sync_to_async(_field_schema)(
        _make_sidecar_node_type("AsyncIterableTotalCountNode", total_count=True),
        resolver=resolver,
    )
    result = await schema.execute("{ items { edges { node { id } } totalCount } }")

    assert result.errors is not None
    messages = [str(err.message) for err in result.errors]
    assert any("totalCount" in m and "non-queryset iterable" in m for m in messages)
    assert not any("Cannot return null for non-nullable field" in m for m in messages)


# --- Default deterministic ordering ------------------------------------------


@pytest.mark.django_db
def test_default_ordering_applied_when_unordered():
    """An unordered base + no ``orderBy`` gets ``order_by(pk)`` applied."""
    from django_strawberry_framework.connection import _pipeline_sync

    services.seed_data(1)
    node_type = _make_sidecar_node_type("DefaultOrderNode")
    info = _capture_info(node_type)

    qs = _pipeline_sync(
        node_type,
        Category.objects.all(),
        info,
        filter_input=None,
        order_by_input=None,
    )
    assert qs.ordered
    assert qs.query.order_by == (Category._meta.pk.attname,)


@pytest.mark.django_db
def test_default_ordering_preserves_supplied_orderby():
    """A queryset already ordered (e.g. by a supplied ``orderBy``) is NOT pk-overridden."""
    from django_strawberry_framework.connection import _pipeline_sync

    services.seed_data(1)
    node_type = _make_sidecar_node_type("PreservedOrderNode")
    info = _capture_info(node_type)

    # A pre-ordered source stands in for a supplied ``orderBy`` / model
    # ``Meta.ordering`` - both mark ``qs.ordered`` True before the default step.
    qs = _pipeline_sync(
        node_type,
        Category.objects.order_by("name"),
        info,
        filter_input=None,
        order_by_input=None,
    )
    assert qs.query.order_by == ("name",)


@pytest.mark.django_db
def test_default_ordering_preserves_meta_ordering():
    """A queryset that is already ``ordered`` keeps its ordering (the ``Meta.ordering`` shape).

    ``qs.ordered`` is the property the default-ordering step branches on; a
    descending pre-order stands in for a model ``Meta.ordering`` - the pk default
    must not fire because ``qs.ordered`` is already True.
    """
    from django_strawberry_framework.connection import _pipeline_sync

    services.seed_data(1)
    node_type = _make_sidecar_node_type("MetaOrderNode")
    info = _capture_info(node_type)

    qs = _pipeline_sync(
        node_type,
        Category.objects.order_by("-name"),
        info,
        filter_input=None,
        order_by_input=None,
    )
    assert qs.query.order_by == ("-name",)


# --- Composition order -------------------------------------------------------


@pytest.mark.django_db
def test_connection_resolver_composition_order():
    """Visibility runs before filter before order before default-order before slice.

    An instrumented ``get_queryset`` + filterset + orderset record their call
    order; the query slices to ``first: 1`` while ``totalCount`` reflects the
    full post-filter pre-slice count (so the count is captured pre-slice).
    """
    services.seed_data(3)
    calls: list[str] = []

    def get_queryset(cls, qs, info):
        calls.append("visibility")
        return qs

    class _OrderedFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["icontains"]}

        @classmethod
        def apply_sync(
            cls,
            input_value,
            queryset,
            info,
        ):
            calls.append("filter")
            return super().apply_sync(input_value, queryset, info)

    class _OrderedOrder(OrderSet):
        class Meta:
            model = Category
            fields = ["name"]

        @classmethod
        def apply_sync(
            cls,
            input_value,
            queryset,
            info,
        ):
            calls.append("order")
            return super().apply_sync(input_value, queryset, info)

    node_type = _make_sidecar_node_type(
        "CompositionNode",
        total_count=True,
        filterset=_OrderedFilter,
        orderset=_OrderedOrder,
        get_queryset=get_queryset,
    )
    schema = _field_schema(node_type)
    total = Category.objects.count()
    result = schema.execute_sync(
        '{ items(first: 1, filter: {name: {iContains: ""}}, orderBy: [{name: ASC}]) '
        "{ edges { node { id } } totalCount } }",
        context_value=HttpRequest(),
    )
    assert result.errors is None
    assert calls == ["visibility", "filter", "order"]
    assert len(result.data["items"]["edges"]) == 1
    # totalCount counts the full post-filter pre-slice set, not the sliced page.
    assert result.data["items"]["totalCount"] == total


# --- Sync + async dispatch + SyncMisuseError ---------------------------------


@pytest.mark.django_db
def test_relay_max_results_cap():
    """``strawberry_config(relay_max_results=N)`` caps any single page (spec-032 Slice 4).

    The one conformance-matrix entry a live fakeshop query cannot reach
    (the project schema uses the default ``StrawberryConfig``): ``first``
    over the cap surfaces Strawberry's own error before any row math, and
    ``first`` at the cap succeeds. Error text source-verified against the
    locked engine (``strawberry/relay/utils.py::SliceMetadata.from_arguments``).
    """
    services.seed_data(2)
    schema = _field_schema(
        _make_node_type("MaxResultsNode", total_count=None),
        config=strawberry_config(relay_max_results=2),
    )

    over_cap = schema.execute_sync("{ items(first: 3) { edges { node { id } } } }")
    assert over_cap.errors is not None
    assert "Argument 'first' cannot be higher than 2." in str(over_cap.errors[0])

    at_cap = schema.execute_sync("{ items(first: 2) { edges { node { id } } } }")
    assert at_cap.errors is None
    assert len(at_cap.data["items"]["edges"]) == 2


@pytest.mark.django_db(transaction=True)
async def test_connection_resolver_async_dispatch():
    """The default resolver dispatches correctly on the async ``execute`` path (incl. ``.acount()``)."""
    from asgiref.sync import sync_to_async

    await sync_to_async(services.seed_data)(2)
    expected = await Category.objects.acount()
    schema = await sync_to_async(_field_schema)(
        _make_sidecar_node_type("AsyncDispatchNode", total_count=True),
    )
    result = await schema.execute("{ items(first: 1) { edges { node { id } } totalCount } }")
    assert result.errors is None
    assert len(result.data["items"]["edges"]) == 1
    assert result.data["items"]["totalCount"] == expected


@pytest.mark.django_db
def test_sync_context_async_get_queryset_raises_sync_misuse():
    """An async ``get_queryset`` invoked from the sync resolver path raises ``SyncMisuseError``."""
    services.seed_data(1)

    async def get_queryset(cls, qs, info):
        return qs

    node_type = _make_sidecar_node_type(
        "AsyncVisibilitySyncNode",
        get_queryset=get_queryset,
    )
    schema = _field_schema(node_type)
    result = schema.execute_sync("{ items { edges { node { id } } } }")
    assert result.errors is not None
    assert any(isinstance(err.original_error, SyncMisuseError) for err in result.errors)


# =============================================================================
# Slice 3 - optimizer cooperation point + connection-aware-planning gap guard
# =============================================================================


def _make_relation_node_type(name: str, *, fields: tuple[str, ...], model=Category) -> type:
    """Build a bare Relay-Node ``DjangoType`` (no sidecars) exposing ``fields``.

    Slice 3's optimizer tests reach a relation under ``edges { node }``; the
    sidecar machinery (``_make_sidecar_node_type``) is irrelevant noise here, so
    this builds the minimal Relay-Node shape with the relation field exposed.
    """
    return type(
        name,
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": model,
                    "fields": fields,
                    "interfaces": (relay.Node,),
                    "name": name,
                },
            ),
        },
    )


@pytest.mark.django_db
def test_root_connection_field_queryset_is_planned():
    """The field's helper plans ``edges.node`` selections on the pre-slice queryset.

    A root ``DjangoConnectionField`` self-optimizes by calling
    ``apply_connection_optimization`` before ``ConnectionExtension`` slices -
    the schema middleware (``DjangoOptimizerExtension.resolve``) cannot reach the
    pre-slice queryset behind the connection result, so any published plan over
    the connection IS the field's own cooperation point running (per the spec's
    "the cooperation point the field now owns, NOT the middleware" framing).

    The published plan is asserted via ``info.context.dst_optimizer_plan`` (the
    B5 plan-introspection shape from ``tests/optimizer/test_extension.py``): its
    presence on the context proves ``apply_to`` -> ``_publish_plan_to_context``
    ran for the connection field, which it does ONLY through the field's helper.
    """
    services.seed_data(2)
    # ``ItemNode`` exposes the forward FK ``category`` - the relation a plain
    # ``DjangoListField`` over the same type plans as ``select_related``.
    _make_relation_node_type("PlanCatNode", fields=("id", "name"))
    item_node = _make_relation_node_type(
        "PlanItemNode",
        fields=("id", "name", "category"),
        model=Item,
    )
    schema = _field_schema(item_node, optimizer=DjangoOptimizerExtension(strictness="raise"))

    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ items { edges { node { id name category { id name } } } } }",
        context_value=ctx,
    )
    assert result.errors is None
    # The cooperation point ran: the field's helper published a plan to context.
    # (The middleware never sees the pre-slice queryset behind ConnectionExtension,
    # so this plan can only have come from the field's own helper.)
    plan = getattr(ctx, "dst_optimizer_plan", None)
    assert plan is not None
    assert plan.select_related == ("category",)
    assert plan.prefetch_related == ()
    assert plan.only_fields == (
        "id",
        "name",
        "category_id",
        "category__id",
        "category__name",
    )
    assert "PlanItemNode.category@items.edges.node.category" in ctx.dst_optimizer_planned


@pytest.mark.django_db
def test_root_connection_field_queryset_prefetches_node_many_relation():
    """A many-side relation under ``edges.node`` is planned as a prefetch."""
    services.seed_data(2)
    _make_relation_node_type("PlanPrefetchItemNode", fields=("id", "name"), model=Item)
    category_node = _make_relation_node_type(
        "PlanPrefetchCatNode",
        fields=("id", "name", "items"),
    )
    schema = _field_schema(category_node, optimizer=DjangoOptimizerExtension(strictness="raise"))

    ctx = SimpleNamespace()
    result = schema.execute_sync(
        "{ items { edges { node { id name items { id name } } } } }",
        context_value=ctx,
    )

    assert result.errors is None
    plan = getattr(ctx, "dst_optimizer_plan", None)
    assert plan is not None
    assert plan.select_related == ()
    assert [getattr(entry, "prefetch_to", entry) for entry in plan.prefetch_related] == ["items"]
    assert plan.only_fields == ("id", "name")
    assert "PlanPrefetchCatNode.items@items.edges.node.items" in ctx.dst_optimizer_planned


@pytest.mark.django_db
def test_nested_connection_unplanned_raises_under_strictness():
    """Strictness ``"raise"`` still surfaces an unplanned connection relation access.

    A root ``DjangoConnectionField`` over ``CategoryNode`` reaches the reverse-FK
    many-side relation ``items`` under ``edges { node { items { ... } } }``.
    This test intentionally installs no optimizer extension and seeds an empty
    strictness context, so the unplanned relation access trips
    ``types/resolvers.py::_check_n1`` and surfaces as an
    ``OptimizerError("Unplanned N+1: items")`` in ``result.errors``.

    Reuses the ``tests/optimizer/test_extension.py::test_strictness_raise_*``
    context shape (``dst_optimizer_planned=set()`` /
    ``dst_optimizer_strictness="raise"``); no optimizer extension is installed so
    the gap is genuine (the access really would lazy-load).
    """
    services.seed_data(2)
    # ``CategoryNode`` exposes the reverse-FK ``items``; ``ItemNode`` is the leaf.
    _make_relation_node_type("NestedGapItemNode", fields=("id", "name"), model=Item)
    category_node = _make_relation_node_type("NestedGapCatNode", fields=("id", "name", "items"))
    schema = _field_schema(category_node)

    ctx = SimpleNamespace(dst_optimizer_planned=set(), dst_optimizer_strictness="raise")
    result = schema.execute_sync(
        "{ items { edges { node { id name items { id name } } } } }",
        context_value=ctx,
    )
    assert result.errors is not None
    assert any("Unplanned N+1: items" in err.message for err in result.errors)


# =============================================================================
# Deterministic-total-order tiebreaker (P1 - docs/feedback.md)
# =============================================================================


def _node_over(model: type, name: str, *, fields: tuple[str, ...] = ("id", "name")) -> type:
    """Build a minimal registered ``DjangoType`` over ``model`` (no Relay needed)."""
    return type(
        name,
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model, "fields": fields, "name": name})},
    )


def test_ends_in_unique_column_recognizes_unique_and_non_unique_terminals():
    """Pin ``_ends_in_unique_column`` across ref shapes (P1)."""
    # Unique-by-pk and unique-field string refs.
    assert _ends_in_unique_column(("id",), Category) is True
    assert _ends_in_unique_column(("pk",), Category) is True
    assert _ends_in_unique_column(("name",), Category) is True  # Category.name unique=True
    assert _ends_in_unique_column(("-name",), Category) is True  # leading '-' stripped
    # Non-unique terminal -> needs the pk tiebreaker.
    assert _ends_in_unique_column(("name",), Item) is False  # Item.name unique=False
    # A relation path is not the model's own unique column.
    assert _ends_in_unique_column(("category__name",), Item) is False
    # An aggregate-annotation alias (no such model field) is non-unique.
    assert _ends_in_unique_column(("_dst_order_0_books_title",), Category) is False
    # Empty ordering.
    assert _ends_in_unique_column((), Category) is False
    # OrderBy / F expression terminal resolves via ``.expression.name``.
    assert _ends_in_unique_column((F("name").asc(),), Category) is True  # unique
    assert _ends_in_unique_column((F("name").asc(),), Item) is False  # non-unique


def test_finalize_queryset_appends_pk_tiebreaker_to_non_unique_ordering():
    """A queryset ordered by a NON-UNIQUE column gets the pk appended (P1).

    Otherwise the connection's positional offset cursors are unstable across
    requests when ties exist (rows silently skipped / duplicated across pages).
    No DB query runs - ``_finalize_queryset`` only shapes the lazy queryset and
    the optimizer cooperation point short-circuits with no optimizer installed.
    """
    node = _node_over(Item, "P1ItemNode")
    result = _finalize_queryset(node, Item.objects.order_by("name"), SimpleNamespace())
    assert tuple(result.query.order_by) == ("name", "id")


def test_finalize_queryset_skips_pk_when_terminal_already_unique():
    """An ordering already ending in a UNIQUE column is left alone (no double pk, P1)."""
    node = _node_over(Category, "P1CatNode")
    # Category.name is unique=True -> already a deterministic total order.
    by_name = _finalize_queryset(node, Category.objects.order_by("name"), SimpleNamespace())
    assert tuple(by_name.query.order_by) == ("name",)
    # Ordering by the pk itself is not doubled into ``("id", "id")``.
    by_pk = _finalize_queryset(node, Category.objects.order_by("id"), SimpleNamespace())
    assert tuple(by_pk.query.order_by) == ("id",)


def test_finalize_queryset_preserves_meta_ordering_and_appends_pk():
    """A model ``Meta.ordering`` is PRESERVED + pk appended, not clobbered to pk-only (P1).

    ``qs.query.order_by`` is empty when the order comes from ``Meta.ordering``
    even though ``qs.ordered`` is True; ``_finalize_queryset`` resolves the
    effective ordering from ``_meta.ordering`` so ``ORDER BY order`` becomes
    ``ORDER BY order, pk`` rather than dropping to ``ORDER BY pk``
    (``docs/feedback.md`` P1 correction). ``Status`` (kanban) declares
    ``Meta.ordering = ["order"]`` over a non-unique ``PositiveIntegerField``.
    """
    node = _node_over(Status, "P1StatusNode", fields=("id",))
    qs = Status.objects.all()
    assert qs.ordered is True
    assert tuple(qs.query.order_by) == ()  # order comes implicitly from Meta.ordering
    result = _finalize_queryset(node, qs, SimpleNamespace())
    assert tuple(result.query.order_by) == ("order", "id")


# =============================================================================
# Optimizer cooperation short-circuit (P3a) + connection-type-cache reset (P3b)
# =============================================================================


def test_apply_connection_optimization_short_circuits_without_optimizer():
    """With no optimizer installed, the cooperation point returns the qs unchanged (P3a).

    The connection field does NOT fabricate a throwaway optimizer to
    self-optimize; outside an execution the ``_active_optimizer`` ``ContextVar``
    is ``None`` so the helper short-circuits (``docs/feedback.md`` P3a).
    """
    from django_strawberry_framework.optimizer.extension import apply_connection_optimization

    node = _make_node_type("P3aNode", total_count=None)
    qs = Category.objects.all()
    assert apply_connection_optimization(node, qs, SimpleNamespace()) is qs


def test_apply_connection_optimization_short_circuits_when_target_has_no_model():
    """An unregistered target type has no model to plan, so the qs is returned (P3a).

    Hits the ``target_model is None`` guard before the optimizer lookup: a type the
    registry does not know maps to no Django model, so there is nothing to optimize.
    """
    from django_strawberry_framework.optimizer.extension import apply_connection_optimization

    class _UnregisteredNode:  # never registered -> registry.model_for_type(...) is None
        pass

    qs = Category.objects.all()
    assert apply_connection_optimization(_UnregisteredNode, qs, SimpleNamespace()) is qs


def test_ends_in_unique_column_false_for_unnameable_terminal():
    """A terminal order expression with no resolvable column name is treated as non-unique (P1).

    ``_ends_in_unique_column`` can only certify uniqueness when it can read a column
    name (a string ref or an ``OrderBy(F(...))``). A bare function expression (e.g.
    ``Lower("name")``) exposes no ``.expression.name``, so the helper conservatively
    reports False and ``_finalize_queryset`` appends the pk tiebreaker.
    """
    from django.db.models.functions import Lower

    assert _ends_in_unique_column((Lower("name"),), Category) is False


@pytest.mark.django_db
def test_pipeline_async_coerces_manager_source_and_finalizes():
    """``_pipeline_async`` coerces a Manager to a queryset and applies the default pk ordering.

    Async twin of the sync default-ordering path: a ``Manager`` source is run through
    ``.all()``, the async ``get_queryset`` hook, then ``_finalize_queryset`` (which
    appends the pk tiebreaker to the otherwise-unordered base).
    """
    from django_strawberry_framework.connection import _pipeline_async

    node_type = _make_sidecar_node_type("AsyncManagerNode")
    info = _capture_info(node_type)
    qs = asyncio.run(
        _pipeline_async(node_type, Category.objects, info, filter_input=None, order_by_input=None),
    )
    assert qs.ordered
    assert qs.query.order_by == (Category._meta.pk.attname,)


@pytest.mark.django_db(transaction=True)
async def test_connection_async_pipeline_applies_filter_and_order():
    """The async resolver runs the filter -> order -> finalize branches of ``_pipeline_async``.

    A live async execution carrying both ``filter:`` and ``orderBy:`` args drives the
    async sidecar-apply branches (``filterset_class.apply_async`` /
    ``orderset_class.apply_async``) that the sync path covers via HTTP. ``_CategoryFilter``
    / ``_CategoryOrder`` carry no permission gate, so an anonymous request runs through.
    """
    from asgiref.sync import sync_to_async

    async def resolver(root, info):
        # An async resolver forces the connection through the ASYNC pipeline; the
        # sidecar filter:/orderBy: args are then applied to its result via *_async.
        return Category.objects.all()

    node_type = _make_sidecar_node_type("AsyncFilterOrderNode")
    schema = await sync_to_async(_field_schema)(node_type, resolver=resolver)
    await sync_to_async(services.seed_data)(1)
    request = HttpRequest()
    request.user = SimpleNamespace(is_anonymous=True, is_staff=False)
    result = await schema.execute(
        '{ items(filter: { name: { exact: "no-such-name" } }, '
        "orderBy: [{ name: ASC }]) { edges { node { name } } } }",
        context_value=SimpleNamespace(request=request),
    )
    assert result.errors is None, result.errors
    assert result.data["items"]["edges"] == []


def test_clear_connection_type_cache_empties_the_cache():
    """``clear_connection_type_cache`` drops the generated-connection-class cache (P3b)."""
    _connection_type_for(_make_node_type("P3bDirectNode", total_count=True))
    assert _connection_type_cache
    clear_connection_type_cache()
    assert not _connection_type_cache


def test_registry_clear_also_clears_connection_type_cache():
    """``registry.clear()`` resets the connection-type cache too (P3b wiring)."""
    _connection_type_for(_make_node_type("P3bRegistryNode", total_count=True))
    assert _connection_type_cache
    registry.clear()
    assert not _connection_type_cache


# TODO(spec-033 Slice 1-2): root-connection no-regression fence. The shipped
# root-connection planning pins here (edges { node } extraction -> select_related
# / Prefetch on the pre-slice queryset) must stay GREEN UNMODIFIED through the
# helper consolidation (Decision 9) and the fast-path addition (Decision 5) --
# this card touches only the NESTED half. No new tests required here; this marker
# records the fence (DoD item 12 / "No B1-B8 regression").
