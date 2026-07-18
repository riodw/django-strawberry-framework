"""Tests for the selection-traversal substrate (``optimizer/selections.py``).

The 0.0.9 DRY pass (``docs/feedback.md`` Major 2) single-sited the
selection-tree rules the optimizer had split between the AST cache-key walk
(``optimizer/extension.py``), the converted-selection plan walker
(``optimizer/walker.py``), and the connection ``totalCount`` detection
(``connection.py``). The plan cache and nested-connection windows depend on
those rules being aligned, so a fragment/directive fix landing on one traversal
but not the others is a real bug class. These tests pin the shared primitives
directly; the deep behavioral coverage lives in ``tests/optimizer/test_walker.py``
/ ``test_extension.py`` and ``tests/test_connection.py`` (which reach these same
functions through the underscore aliases the two modules re-bind).
"""

import copy
from types import SimpleNamespace

from graphql import parse
from graphql.language.ast import FragmentDefinitionNode, FragmentSpreadNode

from django_strawberry_framework.optimizer.selections import (
    ast_child_selections,
    connection_count_required,
    connection_node_children,
    direct_child_selected,
    directive_variable_names,
    included_field_selections,
    is_fragment,
    named_children,
    node_children_with_runtime_prefix,
    resolve_unvisited_fragment,
    response_key,
    response_keys,
    should_include,
)


def _field(
    name,
    selections=None,
    directives=None,
    alias=None,
):
    return SimpleNamespace(
        name=name,
        alias=alias,
        directives=directives or {},
        arguments={},
        selections=selections or [],
    )


def _fragment(selections=None, directives=None):
    return SimpleNamespace(
        type_condition="T",
        directives=directives or {},
        selections=selections or [],
    )


# ---------------------------------------------------------------------------
# AST adapter
# ---------------------------------------------------------------------------


def test_ast_child_selections_returns_children_or_empty():
    """A field with a selection set yields its children; a leaf yields ``()``."""
    doc = parse("{ a { b c } d }")
    operation = doc.definitions[0]
    field_a, field_d = ast_child_selections(operation)
    assert {c.name.value for c in ast_child_selections(field_a)} == {"b", "c"}
    assert ast_child_selections(field_d) == ()  # scalar leaf, no selection_set.


def test_resolve_unvisited_fragment_resolves_once_then_dedups():
    """A spread resolves to its definition once; a second visit and misses return ``None``."""
    doc = parse("query { ...F } fragment F on T { x }")
    operation, fragment_def = doc.definitions
    spread = operation.selection_set.selections[0]
    fragments = {"F": fragment_def}
    visited: set[str] = set()

    assert isinstance(fragment_def, FragmentDefinitionNode)
    assert resolve_unvisited_fragment(spread, fragments, visited) is fragment_def
    assert visited == {"F"}
    # Already visited -> None (the cycle / sibling-spread guard).
    assert resolve_unvisited_fragment(spread, fragments, visited) is None
    # A non-spread node -> None.
    field = fragment_def.selection_set.selections[0]
    assert resolve_unvisited_fragment(field, fragments, set()) is None
    # A spread for an undefined fragment -> None (defensive).
    assert resolve_unvisited_fragment(spread, {}, set()) is None
    # A spread whose ``name`` is falsy -> None (defensive; graphql-core
    # validation would normally reject a nameless spread before the optimizer).
    nameless = copy.copy(spread)
    nameless.name = None
    assert isinstance(nameless, FragmentSpreadNode)
    assert resolve_unvisited_fragment(nameless, fragments, set()) is None


def test_resolve_unvisited_fragment_depth_keys_visits_per_spread_site():
    """With ``depth=``, the visit key is ``(name, depth)`` so each depth resolves once.

    The cache-relevant-variable walk needs this: a fragment spread at root depth
    must not suppress a later nested spread of the same fragment (Decision 7
    nested pagination variables). Name-only visits stay independent of depth
    keys - the two keying modes do not share a visited set in production, but
    the pin here proves the depth axis is ``(name, depth)`` not name alone.
    """
    doc = parse("query { ...F } fragment F on T { x }")
    operation, fragment_def = doc.definitions
    spread = operation.selection_set.selections[0]
    fragments = {"F": fragment_def}
    visited: set[tuple[str, int]] = set()

    assert resolve_unvisited_fragment(spread, fragments, visited, depth=0) is fragment_def
    assert visited == {("F", 0)}
    # Same depth again -> suppressed.
    assert resolve_unvisited_fragment(spread, fragments, visited, depth=0) is None
    # Different depth -> resolves again (nested spread site).
    assert resolve_unvisited_fragment(spread, fragments, visited, depth=1) is fragment_def
    assert visited == {("F", 0), ("F", 1)}


def test_directive_variable_names_collects_skip_include_vars_only():
    """Only ``@skip`` / ``@include`` ``if`` variables are collected."""
    doc = parse(
        "query Q($x: Boolean!, $y: Boolean!, $z: Boolean!) { a @skip(if: $x) @other(if: $z) }",
    )
    field_a = doc.definitions[0].selection_set.selections[0]
    assert directive_variable_names(field_a) == {"x"}

    doc2 = parse("query Q($y: Boolean!) { b @include(if: $y) }")
    field_b = doc2.definitions[0].selection_set.selections[0]
    assert directive_variable_names(field_b) == {"y"}


def test_directive_variable_names_ignores_non_directive_objects():
    """A ``directives`` collection carrying a non-``DirectiveNode`` is skipped."""
    node = SimpleNamespace(directives=[object()])
    assert directive_variable_names(node) == set()


# ---------------------------------------------------------------------------
# Converted-selection adapter
# ---------------------------------------------------------------------------


def test_is_fragment_discriminates_on_type_condition():
    """A selection with ``type_condition`` is a fragment; a field is not."""
    assert is_fragment(_fragment()) is True
    assert is_fragment(_field("a")) is False


def test_should_include_honors_skip_and_include():
    """``@skip(if: true)`` and ``@include(if: false)`` both exclude."""
    assert should_include(_field("a")) is True
    assert should_include(_field("a", directives={"skip": {"if": True}})) is False
    assert should_include(_field("a", directives={"skip": {"if": False}})) is True
    assert should_include(_field("a", directives={"include": {"if": False}})) is False
    assert should_include(_field("a", directives={"include": {"if": True}})) is True


def test_response_key_prefers_alias():
    """``response_key`` returns the alias when present, else the field name."""
    assert response_key(_field("a")) == "a"
    assert response_key(_field("a", alias="b")) == "b"


def test_response_keys_reads_merged_marker_or_falls_back():
    """``response_keys`` reads the optimizer marker, else falls back to the single key."""
    assert response_keys(_field("a", alias="b")) == ("b",)
    merged = _field("a")
    merged._optimizer_response_keys = ["b", "c"]
    assert response_keys(merged) == ("b", "c")


def test_included_field_selections_inlines_fragments_and_filters_directives():
    """Fragment bodies are inlined and ``@skip``-ped fields dropped, flat."""
    selections = [
        _field("keep"),
        _field("dropped", directives={"skip": {"if": True}}),
        _fragment(selections=[_field("from_fragment")]),
    ]
    names = [s.name for s in included_field_selections(selections)]
    assert names == ["keep", "from_fragment"]


def test_named_children_recurses_through_fragments():
    """``named_children`` finds direct children of ``name`` through fragment wrappers."""
    connection = _field(
        "booksConnection",
        selections=[
            _field("edges", selections=[_field("node")]),
            _fragment(selections=[_field("edges", selections=[_field("node")])]),
            _field("pageInfo"),
        ],
    )
    edges = named_children(connection, "edges")
    assert len(edges) == 2  # the direct edges + the fragment-wrapped edges.


def test_node_children_with_runtime_prefix_clones_with_prefix():
    """Node children are cloned carrying the connection-aware runtime prefix."""
    node = _field("node", selections=[_field("title"), _field("author")])
    children = node_children_with_runtime_prefix(node, runtime_prefixes=(("booksConnection",),))
    assert {c.name for c in children} == {"title", "author"}
    assert all(c._optimizer_runtime_prefixes == [("booksConnection",)] for c in children)


def test_connection_node_children_unwraps_edges_node_with_prefixes():
    """``connection_node_children`` owns the edges->node composition + prefix walk."""
    connection = _field(
        "booksConnection",
        selections=[
            _field(
                "edges",
                selections=[
                    _field("node", selections=[_field("title"), _field("author")]),
                ],
            ),
            _field("totalCount"),
            _fragment(
                selections=[
                    _field(
                        "edges",
                        alias="more",
                        selections=[
                            _field("node", selections=[_field("isbn")]),
                        ],
                    ),
                ],
            ),
        ],
    )
    children = connection_node_children(
        connection,
        runtime_prefixes=(("booksConnection",),),
    )
    by_name = {c.name: c for c in children}
    assert set(by_name) == {"title", "author", "isbn"}
    assert by_name["title"]._optimizer_runtime_prefixes == [
        ("booksConnection", "edges", "node"),
    ]
    assert by_name["isbn"]._optimizer_runtime_prefixes == [
        ("booksConnection", "more", "node"),
    ]


def test_connection_node_children_empty_without_edges_node():
    """Scalar-only connection selections yield no node children."""
    connection = _field(
        "booksConnection",
        selections=[_field("totalCount"), _field("pageInfo")],
    )
    assert connection_node_children(connection, runtime_prefixes=(("booksConnection",),)) == []


# ---------------------------------------------------------------------------
# direct_child_selected -- the connection totalCount detection
# ---------------------------------------------------------------------------


def test_direct_child_selected_matches_direct_and_fragment_wrapped():
    """A direct ``totalCount`` and a fragment-wrapped one both match."""
    direct = [_field("edges"), _field("totalCount")]
    assert direct_child_selected(direct, "totalCount") is True

    wrapped = [_field("edges"), _fragment(selections=[_field("totalCount")])]
    assert direct_child_selected(wrapped, "totalCount") is True


def test_direct_child_selected_honors_skip_include():
    """A directive-excluded ``totalCount`` does NOT match, direct or fragment-wrapped.

    ``direct_child_selected`` is a converted-selection walk and must apply the same
    ``should_include`` gate as ``included_field_selections`` / ``named_children``:
    Strawberry's ``convert_selections`` carries live ``@skip`` / ``@include`` args on
    the selection (it does not pre-drop the node), so a ``totalCount @skip(if: true)``
    that reaches the connection resolver would otherwise fire a spurious ``COUNT``.
    The ``@skip(if: false)`` / ``@include(if: true)`` cases still match.
    """
    # Direct field excluded by @skip(if: true) / @include(if: false).
    assert (
        direct_child_selected(
            [_field("edges"), _field("totalCount", directives={"skip": {"if": True}})],
            "totalCount",
        )
        is False
    )
    assert (
        direct_child_selected(
            [_field("totalCount", directives={"include": {"if": False}})],
            "totalCount",
        )
        is False
    )
    # A @skip(if: true) fragment shell prunes its whole subtree, hiding totalCount.
    assert (
        direct_child_selected(
            [_fragment(selections=[_field("totalCount")], directives={"skip": {"if": True}})],
            "totalCount",
        )
        is False
    )
    # Directives that resolve to "keep" still match (no over-pruning).
    assert (
        direct_child_selected(
            [_field("totalCount", directives={"skip": {"if": False}})],
            "totalCount",
        )
        is True
    )
    assert (
        direct_child_selected(
            [_fragment(selections=[_field("totalCount")], directives={"include": {"if": True}})],
            "totalCount",
        )
        is True
    )


def test_direct_child_selected_ignores_nested_field_selections():
    """A ``totalCount`` nested inside a regular field's selections does NOT match.

    The load-bearing contract for nested connections: a node-level ``totalCount``
    deep inside ``edges { node { ... } }`` must not trip the OUTER connection's
    count predicate (only fragment wrappers are descended, not regular fields).
    """
    roots = [
        _field("edges", selections=[_field("node", selections=[_field("totalCount")])]),
        _field("pageInfo"),
    ]
    assert direct_child_selected(roots, "totalCount") is False


def test_ast_to_converted_selections_memoized_per_execution():
    """The converted-selection tree is reused within one installed memo lifecycle.

    A nested fallback connection primes ``info.selected_fields`` once per parent
    row, each time with the SAME field-node group (graphql-core's subfields
    cache guarantees identity across rows). With the per-execution memo
    installed (``on_execute`` does this in production), the conversion runs once
    and later calls return the same list - keyed on the node ids, so a rebuilt
    wrapper list of the same nodes still hits. Outside a lifecycle the memo is
    disabled and every call converts fresh (unchanged direct-caller behavior).
    """
    from django_strawberry_framework.optimizer.selections import (
        ast_to_converted_selections,
        converted_selections_cache,
    )

    doc = parse("{ items { name } books { title } }")
    field_nodes = list(doc.definitions[0].selection_set.selections)
    info = SimpleNamespace(fragments={}, variable_values={})
    single = field_nodes[:1]

    token = converted_selections_cache.set({})
    try:
        first = ast_to_converted_selections(info, single)
        assert ast_to_converted_selections(info, single) is first  # single-node id key
        pair = ast_to_converted_selections(info, field_nodes)
        # A rebuilt wrapper list of the same nodes hits too: keys are the node
        # ids (the graphql-core subfields-cache shape), not the list id.
        assert ast_to_converted_selections(info, list(field_nodes)) is pair
    finally:
        converted_selections_cache.reset(token)

    # No memo installed: every call converts fresh.
    assert ast_to_converted_selections(info, single) is not first


def test_included_field_selections_returns_input_list_when_already_flat():
    """The fragment-free, fully-included shape passes through without a rebuild.

    The common query shape (no fragments, nothing directive-excluded) would
    flatten to an identical list, so the helper returns the INPUT list object -
    the walker calls this once per level, and both callers only iterate the
    result. A fragment or a directive-excluded field anywhere forces the
    rebuild path (asserted via identity: the result is a fresh list).
    """
    flat = [_field("a"), _field("b")]
    assert included_field_selections(flat) is flat

    # ``@include(if: False)``-excluded field: rebuild (a fresh, filtered list).
    with_excluded = [_field("a"), _field("b", directives={"include": {"if": False}})]
    rebuilt = included_field_selections(with_excluded)
    assert rebuilt is not with_excluded
    assert [s.name for s in rebuilt] == ["a"]

    # Fragment present: rebuild with the fragment body inlined.
    with_fragment = [_field("a"), _fragment(selections=[_field("c")])]
    inlined = included_field_selections(with_fragment)
    assert inlined is not with_fragment
    assert [s.name for s in inlined] == ["a", "c"]


def test_connection_count_required_matrix():
    """``connection_count_required`` fires on ``totalCount`` / ``pageInfo.hasNextPage`` only.

    The plan-time half of the conditional ``_dst_total_count`` contract
    (workstream B): cursors and ``hasPreviousPage`` derive from the row number
    alone, so neither keeps the count; fragment wrappers are descended at both
    levels; directive-excluded observers do not fire (live ``@skip`` args are
    already evaluated on converted selections).
    """
    edges_only = _field("conn", selections=[_field("edges", selections=[_field("node")])])
    assert connection_count_required(edges_only) is False

    total = _field("conn", selections=[_field("edges"), _field("totalCount")])
    assert connection_count_required(total) is True

    has_next = _field(
        "conn",
        selections=[_field("pageInfo", selections=[_field("hasNextPage")])],
    )
    assert connection_count_required(has_next) is True

    previous_only = _field(
        "conn",
        selections=[
            _field("pageInfo", selections=[_field("hasPreviousPage"), _field("endCursor")]),
        ],
    )
    assert connection_count_required(previous_only) is False

    # Fragment wrappers descend at the connection level AND inside pageInfo.
    fragment_wrapped = _field(
        "conn",
        selections=[
            _fragment(
                selections=[
                    _field("pageInfo", selections=[_fragment(selections=[_field("hasNextPage")])]),
                ],
            ),
        ],
    )
    assert connection_count_required(fragment_wrapped) is True

    # Directive-excluded observers do not fire.
    skipped = _field(
        "conn",
        selections=[_field("totalCount", directives={"skip": {"if": True}})],
    )
    assert connection_count_required(skipped) is False

    # A node-level totalCount deep inside edges { node { ... } } is the INNER
    # connection's business, not this one's.
    nested_only = _field(
        "conn",
        selections=[
            _field(
                "edges",
                selections=[_field("node", selections=[_field("totalCount")])],
            ),
        ],
    )
    assert connection_count_required(nested_only) is False
