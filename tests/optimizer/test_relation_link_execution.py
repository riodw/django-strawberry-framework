"""Optimizer execution over relations whose link is not a plain pk ``ForeignKey``.

A child joins its parent through a ``ForeignObject`` (one or two carrier
columns), a ``ForeignKey`` bound on a non-pk ``to_field``, or an M2M whose
through model's foreign keys bind on non-pk ``to_field`` columns. The optimizer
derives every column of such a link from
``django_strawberry_framework/utils/relations.py::relation_link``: the child's
carrier columns load under the prefetch ``.only()`` and partition the window
when there is exactly one, and the parent's non-pk target columns load under the
parent ``.only()``, so no row refetches a deferred link column. A two-column link
has no single partition expression and resolves per parent. A forward hop loads
its own carriers and, on the Prefetch path, every target column of the link.

Fakeshop carries no ``ForeignObject`` and exposes no reverse relation over a
``to_field`` link, so the test-local models of
``tests/optimizer/_link_models.py`` stand in. Each row compares the optimized
wire against the optimizer-off wire and pins the optimized query count.
"""

from collections.abc import Callable, Iterator
from typing import Any

import pytest
import strawberry
from django.db import connection
from django.db.models import QuerySet
from django.test.utils import CaptureQueriesContext
from strategy_schemas import make_django_type
from strawberry import relay

from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoListField,
    DjangoOptimizerExtension,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.connection import _connection_type_cache
from django_strawberry_framework.registry import registry

from ._link_models import (
    LnkColumnChild,
    LnkOptionalPairChild,
    LnkPairChild,
    LnkParent,
    LnkSlugChild,
    LnkTag,
    link_fixture_tables,
)


@pytest.fixture(autouse=True)
def _isolate_global_registry(isolate_global_registry: None) -> None:
    """Every row declares fresh ``DjangoType`` classes."""


@pytest.fixture
def link_tables() -> Iterator[None]:
    """Materialize and seed the link fixture tables for one row."""
    with link_fixture_tables(connection):
        yield


def _parent_visibility(
    cls: type,
    queryset: QuerySet[LnkParent],
    info: object,
    **kwargs: object,
):
    """An identity ``get_queryset`` hook: forces every hop onto the parent into a ``Prefetch``."""
    return queryset


def _schema(*, optimizer: bool, parent_hook: bool) -> strawberry.Schema:
    registry.clear()
    _connection_type_cache.clear()
    make_django_type("LnkPairChildType", LnkPairChild, ("id", "name"))
    column_type = make_django_type("LnkColumnChildType", LnkColumnChild, ("id", "name", "parent"))
    slug_type = make_django_type("LnkSlugChildType", LnkSlugChild, ("id", "name", "parent"))
    tag_type = make_django_type(
        "LnkTagType",
        LnkTag,
        ("id", "name", "parents"),
        meta_extra={"relation_shapes": {"parents": "both"}},
    )
    relations = (
        "pair_children",
        "column_children",
        "slug_children",
        "tags",
    )
    parent_type = make_django_type(
        "LnkParentType",
        LnkParent,
        ("id", "label", *relations),
        meta_extra={"relation_shapes": dict.fromkeys(relations, "both")},
        namespace_extra=(
            {"get_queryset": classmethod(_parent_visibility)} if parent_hook else None
        ),
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {
                    "parents": list[parent_type],
                    "parents_connection": DjangoConnection[parent_type],
                    "column_children": list[column_type],
                    "slug_children": list[slug_type],
                    "tags": list[tag_type],
                },
                "parents": DjangoListField(parent_type),
                "parents_connection": DjangoConnectionField(parent_type),
                "column_children": DjangoListField(column_type),
                "slug_children": DjangoListField(slug_type),
                "tags": DjangoListField(tag_type),
            },
        ),
    )
    extensions = []
    if optimizer:
        extension = DjangoOptimizerExtension()
        extensions = [lambda: extension]
    return strawberry.Schema(query=query_cls, config=strawberry_config(), extensions=extensions)


def _run(query: str, *, parent_hook: bool = False):
    """Execute ``query`` optimized; return its data and query count after the oracle agrees."""
    expected = _schema(optimizer=False, parent_hook=parent_hook).execute_sync(query)
    assert expected.errors is None, expected.errors
    schema = _schema(optimizer=True, parent_hook=parent_hook)
    with CaptureQueriesContext(connection) as ctx:
        result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    assert result.data is not None
    assert result.data == expected.data
    return result.data, len(ctx.captured_queries)


# basedpyright: ExecutionResult.data is dict[str, Any]; the rows read nested wire values by key
_WireData = dict[str, Any]  # pyright: ignore[reportExplicitAny]


def _names(rows: list[_WireData], key: str) -> list[list[str]]:
    return [[child["name"] for child in row[key]] for row in rows]


def _edge_names(rows: list[_WireData], key: str) -> list[list[str]]:
    return [[edge["node"]["name"] for edge in row[key]["edges"]] for row in rows]


_EXPECTED_ROWS = [["a1", "a2", "a3"], ["b1"], []]
_EXPECTED_PAGE = [["a1", "a2"], ["b1"], []]


@pytest.mark.django_db(transaction=True)
def test_two_column_link_list_prefetch_loads_every_carrier(link_tables: None):
    """A plain list over the two-column link is one parent query plus one prefetch.

    The prefetch ``.only()`` carries both ``p_tenant`` and ``p_code`` (the
    attach key), and the parent ``.only()`` carries ``tenant`` and ``code`` (the
    link targets the selection never names), so no row refetches either.
    """
    data, queries = _run("{ parents { label pairChildren { name } } }")
    assert _names(data["parents"], "pairChildren") == _EXPECTED_ROWS
    assert queries == 2


_LINK_CONNECTION_ROOT_ROWS: list[tuple[str, Callable[[_WireData], list[_WireData]]]] = [
    (
        "{ parents { label pairChildrenConnection(first: 2) { edges { node { name } } } } }",
        lambda data: data["parents"],
    ),
    (
        "{ parentsConnection(first: 10) { edges { node { label "
        "pairChildrenConnection(first: 2) { edges { node { name } } } } } } }",
        lambda data: [edge["node"] for edge in data["parentsConnection"]["edges"]],
    ),
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("query", "rows_of"),
    _LINK_CONNECTION_ROOT_ROWS,
    ids=["list_root", "connection_root"],
)
def test_two_column_link_connection_resolves_per_parent(
    link_tables: None,
    query: str,
    rows_of: Callable[[_WireData], list[_WireData]],
):
    """A nested connection over the two-column link has no partition and resolves per parent.

    The window is left unplanned (one page query per parent after the root
    query), the parent rows still carry the link targets, and the pages match
    the optimizer-off wire exactly.
    """
    data, queries = _run(query)
    assert _edge_names(rows_of(data), "pairChildrenConnection") == _EXPECTED_PAGE
    assert queries == 1 + 3


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("relation", "query"),
    [
        ("columnChildren", "{ parents { label columnChildren { name } } }"),
        ("slugChildren", "{ parents { label slugChildren { name } } }"),
    ],
    ids=["one_column_foreign_object", "to_field_foreign_key"],
)
def test_one_column_link_list_prefetch_is_batched(link_tables: None, relation: str, query: str):
    """A plain list over a one-column link is one parent query plus one prefetch.

    The child carrier (``p_id`` / the ``slug`` FK column) and, for the
    ``to_field`` link, the parent's ``slug`` load in the projections, so
    neither side refetches per row.
    """
    data, queries = _run(query)
    assert _names(data["parents"], relation) == _EXPECTED_ROWS
    assert queries == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("relation", "query"),
    [
        (
            "columnChildrenConnection",
            "{ parents { label columnChildrenConnection(first: 2) { edges { node { name } } } } }",
        ),
        (
            "slugChildrenConnection",
            "{ parents { label slugChildrenConnection(first: 2) { edges { node { name } } } } }",
        ),
    ],
    ids=["one_column_foreign_object", "to_field_foreign_key"],
)
def test_one_column_link_connection_is_one_window(link_tables: None, relation: str, query: str):
    """A nested connection over a one-column link is one root query plus one window.

    The window partitions by the lone carrier column, and both projections load
    the link columns, so no page row and no parent refetches a deferred column.
    """
    data, queries = _run(query)
    assert _edge_names(data["parents"], relation) == _EXPECTED_PAGE
    assert queries == 2


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "root",
    ["columnChildren", "slugChildren"],
    ids=["one_column_foreign_object", "to_field_foreign_key"],
)
def test_forward_link_prefetch_loads_the_child_carrier(link_tables: None, root: str):
    """A forward hop downgraded to a ``Prefetch`` is one child query plus one parent query.

    The parent type's ``get_queryset`` forces the ``Prefetch``, whose attach reads
    the child row's carrier (``p_id``, or the ``slug`` FK column): the child
    ``.only()`` carries it, so no child row refetches it.
    """
    data, queries = _run(f"{{ {root} {{ name parent {{ label }} }} }}", parent_hook=True)
    assert [row["parent"]["label"] for row in data[root]] == [
        "pa",
        "pa",
        "pa",
        "pb",
    ]
    assert queries == 2


@pytest.mark.django_db(transaction=True)
def test_conflicting_alias_connection_loads_the_parent_link_columns(link_tables: None):
    """A connection refused for conflicting alias arguments still loads the parent ``slug``.

    Two aliases of one parent hop select the nested connection with different
    ``first:`` under one response key, so the planner leaves it to per-parent
    resolution; that resolution reads each parent's ``slug``, which the
    ``select_related`` projection (``parent__label`` selected, ``slug`` not)
    still carries, so no parent row refetches it: one root query plus one page
    query per child row and alias.
    """
    query = (
        "{ slugChildren { name "
        "a: parent { label slugChildrenConnection(first: 1) { edges { node { name } } } } "
        "b: parent { label slugChildrenConnection(first: 2) { edges { node { name } } } } } }"
    )
    data, queries = _run(query)
    first_child = data["slugChildren"][0]
    assert [
        edge["node"]["name"] for edge in first_child["a"]["slugChildrenConnection"]["edges"]
    ] == [
        "a1",
    ]
    assert [
        edge["node"]["name"] for edge in first_child["b"]["slugChildrenConnection"]["edges"]
    ] == ["a1", "a2"]
    assert queries == 1 + 4 * 2


def _leaf(node: _WireData) -> str:
    leaf = node.get("name", node.get("label"))
    assert isinstance(leaf, str)
    return leaf


def _m2m_rows(data: _WireData) -> list[list[str]]:
    """Each root row's related leaves, from a list field or a connection's edges."""
    root = data.get("parents", data.get("tags"))
    assert root is not None
    rows = []
    for row in root:
        related = next(value for key, value in row.items() if key not in {"label", "name"})
        nodes = related if isinstance(related, list) else [e["node"] for e in related["edges"]]
        rows.append([_leaf(node) for node in nodes])
    return rows


_M2M_ROWS = {
    "forward_list": ("{ parents { label tags { name } } }", [["t1", "t2", "t3"], ["t1"], []]),
    "forward_connection": (
        "{ parents { label tagsConnection(first: 2) { edges { node { name } } } } }",
        [["t1", "t2"], ["t1"], []],
    ),
    "reverse_list": ("{ tags { name parents { label } } }", [["pa", "pb"], ["pa"], ["pa"]]),
    "reverse_connection": (
        "{ tags { name parentsConnection(first: 1) { edges { node { label } } } } }",
        [["pa"], ["pa"], ["pa"]],
    ),
}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("row", list(_M2M_ROWS), ids=list(_M2M_ROWS))
def test_m2m_through_to_field_link_loads_the_source_key(link_tables: None, row: str):
    """An M2M hop whose through FK targets a non-pk column loads that column on the source.

    Django matches through rows to source rows by the through FK's target
    (``LnkParent.slug`` forward, ``LnkTag.code`` reverse), reading it off every
    source row; the source ``.only()`` carries it, so a list or a window is one
    root query plus one batched query, with the optimizer-off wire's rows.
    """
    query, expected_rows = _M2M_ROWS[row]
    data, queries = _run(query)
    assert _m2m_rows(data) == expected_rows
    assert queries == 2


def _pair_parent_schema(*, optimizer: bool, route: str) -> strawberry.Schema:
    """Expose the two-column forward ``ForeignObject`` through a consumer-authored field.

    ``"annotation"`` annotates ``parent`` over a target whose ``get_queryset``
    forces a ``Prefetch``; ``"hint"`` assigns a resolver and opts back into
    planning with ``OptimizerHint.prefetch_related()``.
    """
    from django_strawberry_framework import DjangoType, OptimizerHint

    registry.clear()
    _connection_type_cache.clear()
    parent_namespace: dict[str, object] = {
        "Meta": type("Meta", (), {"model": LnkParent, "fields": ("id", "label")}),
    }
    if route == "annotation":
        parent_namespace["get_queryset"] = classmethod(_parent_visibility)
    parent_type = type("LnkParentType", (DjangoType,), parent_namespace)
    child_meta: dict[str, object] = {"model": LnkPairChild, "fields": ("id", "name", "parent")}
    child_namespace: dict[str, object] = {"__annotations__": {"parent": parent_type | None}}
    if route == "hint":
        child_meta["optimizer_hints"] = {"parent": OptimizerHint.prefetch_related()}

        def _parent(root: LnkPairChild) -> parent_type | None:
            return root.parent

        child_namespace["parent"] = strawberry.field(resolver=_parent)
    child_namespace["Meta"] = type("Meta", (), child_meta)
    child_type = type("LnkPairChildType", (DjangoType,), child_namespace)
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {"__annotations__": {"pairs": list[child_type]}, "pairs": DjangoListField(child_type)},
        ),
    )
    extensions = []
    if optimizer:
        extension = DjangoOptimizerExtension()
        extensions = [lambda: extension]
    return strawberry.Schema(query=query_cls, config=strawberry_config(), extensions=extensions)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("route", ["annotation", "hint"], ids=["visibility_hook", "prefetch_hint"])
def test_consumer_authored_two_column_forward_link_prefetch_loads_every_target(
    link_tables: None,
    route: str,
):
    """A prefetched two-column forward link is one child query plus one parent query.

    Django attaches each prefetched parent by the link's targets (``tenant``,
    ``code``), which ``relation_link`` names and the parent ``.only()`` carries,
    alongside the child's two carriers, so no row on either side refetches.
    """
    query = "{ pairs { name parent { label } } }"
    expected = _pair_parent_schema(optimizer=False, route=route).execute_sync(query)
    assert expected.errors is None, expected.errors
    schema = _pair_parent_schema(optimizer=True, route=route)
    with CaptureQueriesContext(connection) as ctx:
        result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    assert result.data == expected.data
    assert result.data is not None
    assert [(row["name"], row["parent"]["label"]) for row in result.data["pairs"]] == [
        ("a1", "pa"),
        ("a2", "pa"),
        ("a3", "pa"),
        ("b1", "pb"),
    ]
    assert len(ctx.captured_queries) == 2


def _generated_pair_schema(
    *,
    optimizer: bool,
    parent_hook: bool,
    child_model: type = LnkPairChild,
) -> strawberry.Schema:
    """Expose a two-column forward ``ForeignObject`` as the generated ``parent`` field.

    The child type names ``parent`` in ``Meta.fields``; the parent type exposes
    the reverse ``pair_children`` of ``LnkPairChild`` as a list and a
    connection, so a selection can walk the link forward and back. ``parent_hook`` gives the
    parent type an identity ``get_queryset``, which turns the forward hop into a
    ``Prefetch``.
    """
    registry.clear()
    _connection_type_cache.clear()
    reverse = ("pair_children",) if child_model is LnkPairChild else ()
    make_django_type(
        "LnkParentType",
        LnkParent,
        ("id", "label", *reverse),
        meta_extra={"relation_shapes": dict.fromkeys(reverse, "both")} if reverse else None,
        namespace_extra=(
            {"get_queryset": classmethod(_parent_visibility)} if parent_hook else None
        ),
    )
    child_type = make_django_type(
        f"{child_model.__name__}Type",
        child_model,
        ("id", "name", "parent"),
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {
                    "pairs": list[child_type],
                    "pairs_connection": DjangoConnection[child_type],
                },
                "pairs": DjangoListField(child_type),
                "pairs_connection": DjangoConnectionField(child_type),
            },
        ),
    )
    extensions = []
    if optimizer:
        extension = DjangoOptimizerExtension()
        extensions = [lambda: extension]
    return strawberry.Schema(query=query_cls, config=strawberry_config(), extensions=extensions)


def _run_generated(query: str, *, parent_hook: bool = False, child_model: type = LnkPairChild):
    """Execute ``query`` optimized over the generated link; return its data and SQL.

    The optimizer-off wire is the oracle: the optimized data must equal it.
    """
    expected = _generated_pair_schema(
        optimizer=False,
        parent_hook=parent_hook,
        child_model=child_model,
    ).execute_sync(query)
    assert expected.errors is None, expected.errors
    schema = _generated_pair_schema(
        optimizer=True,
        parent_hook=parent_hook,
        child_model=child_model,
    )
    with CaptureQueriesContext(connection) as ctx:
        result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    assert result.data is not None
    assert result.data == expected.data
    return result.data, [captured["sql"] for captured in ctx.captured_queries]


def _pair_rows(data: _WireData) -> list[_WireData]:
    """The child rows of a ``pairs`` list or a ``pairsConnection`` page."""
    if "pairs" in data:
        return data["pairs"]
    return [edge["node"] for edge in data["pairsConnection"]["edges"]]


_PAIR_PARENTS = [
    ("a1", "pa"),
    ("a2", "pa"),
    ("a3", "pa"),
    ("b1", "pb"),
]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "query",
    [
        "{ pairs { name parent { label } } }",
        "{ pairsConnection(first: 10) { edges { node { name parent { label } } } } }",
    ],
    ids=["list_root", "connection_root"],
)
@pytest.mark.parametrize(
    ("parent_hook", "queries"),
    [(False, 1), (True, 2)],
    ids=["select_related", "prefetch"],
)
def test_generated_two_column_forward_link_resolves_every_parent(
    link_tables: None,
    query: str,
    parent_hook: bool,
    queries: int,
):
    """The generated forward field over a two-column link joins on both columns.

    ``pa`` and ``pb`` share ``code="A"`` under different tenants, so a link that
    joined on one column would hand ``b1`` the wrong parent. Without a parent
    ``get_queryset`` the hop is one ``select_related`` join; with one it is a
    ``Prefetch`` matched on ``(tenant, code)``, one query more.
    """
    data, sql = _run_generated(query, parent_hook=parent_hook)
    assert [(row["name"], row["parent"]["label"]) for row in _pair_rows(data)] == _PAIR_PARENTS
    assert len(sql) == queries


@pytest.mark.django_db(transaction=True)
def test_generated_two_column_forward_link_id_selection_joins_the_parent(link_tables: None):
    """An id-only selection over the link reads the parent row, never one carrier column.

    FK-id elision answers an id-only hop from the source row's one link column;
    a two-column link has no such column, so the hop stays a join and every
    child gets its own parent's pk.
    """
    data, sql = _run_generated("{ pairs { name parent { id } } }")
    parent_ids = dict(LnkParent.objects.values_list("label", "id"))
    assert [
        (row["name"], int(relay.from_base64(row["parent"]["id"])[1])) for row in data["pairs"]
    ] == [(name, parent_ids[label]) for name, label in _PAIR_PARENTS]
    assert len(sql) == 1
    assert 'JOIN "products_lnkparent"' in sql[0]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("relation", "queries"),
    [
        ("pairChildren { name }", 2),
        ("pairChildrenConnection(first: 2) { edges { node { name } } }", 1 + 4),
    ],
    ids=["reverse_list", "reverse_connection"],
)
def test_generated_two_column_forward_link_round_trips_through_the_reverse_side(
    link_tables: None,
    relation: str,
    queries: int,
):
    """Forward over the link and back through its reverse side returns each parent's children.

    The reverse list prefetches on both carriers (one query after the join);
    the reverse connection has no single partition column and pages per
    parent row.
    """
    data, sql = _run_generated(f"{{ pairs {{ name parent {{ label {relation} }} }} }}")
    siblings = {"pa": ["a1", "a2", "a3"], "pb": ["b1"]}
    for row in data["pairs"]:
        related = next(value for key, value in row["parent"].items() if key != "label")
        nodes = related if isinstance(related, list) else [e["node"] for e in related["edges"]]
        expected = siblings[row["parent"]["label"]]
        if not isinstance(related, list):
            expected = expected[:2]
        assert [node["name"] for node in nodes] == expected
    assert len(sql) == queries


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("parent_hook", "queries"),
    [(False, 1), (True, 2)],
    ids=["select_related", "prefetch"],
)
def test_generated_nullable_two_column_forward_link_resolves_absent_parents_to_null(
    link_tables: None,
    parent_hook: bool,
    queries: int,
):
    """A ``null=True`` link over nullable carriers is null wherever no parent matches.

    Both carriers ``NULL``, one carrier ``NULL`` and carriers matching no parent
    all resolve ``null`` and keep their row: the join is an outer join, and the
    prefetch leaves the unmatched rows without a parent.
    """
    data, sql = _run_generated(
        "{ pairs { name parent { label } } }",
        parent_hook=parent_hook,
        child_model=LnkOptionalPairChild,
    )
    assert [(row["name"], row["parent"] and row["parent"]["label"]) for row in data["pairs"]] == [
        ("o1", "pa"),
        ("o2", None),
        ("o3", None),
        ("o4", None),
    ]
    assert len(sql) == queries
    if not parent_hook:
        assert 'LEFT OUTER JOIN "products_lnkparent"' in sql[0]
