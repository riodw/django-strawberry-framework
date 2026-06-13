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

from types import SimpleNamespace

from graphql import parse
from graphql.language.ast import FragmentDefinitionNode

from django_strawberry_framework.optimizer.selections import (
    ast_child_selections,
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


# ---------------------------------------------------------------------------
# direct_child_selected -- the connection totalCount detection
# ---------------------------------------------------------------------------


def test_direct_child_selected_matches_direct_and_fragment_wrapped():
    """A direct ``totalCount`` and a fragment-wrapped one both match."""
    direct = [_field("edges"), _field("totalCount")]
    assert direct_child_selected(direct, "totalCount") is True

    wrapped = [_field("edges"), _fragment(selections=[_field("totalCount")])]
    assert direct_child_selected(wrapped, "totalCount") is True


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
