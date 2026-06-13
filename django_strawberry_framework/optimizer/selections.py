"""Selection-tree traversal substrate - the AST and converted-selection adapters.

The optimizer reads GraphQL selections in two shapes: graphql-core **AST** nodes
(``optimizer/extension.py`` - plan-cache key construction, reachable-fragment
collection, cache-relevant variable extraction) and Strawberry's **converted**
selection objects (``optimizer/walker.py`` + the connection optimizer seam -
plan building, nested connection windows). Both shapes repeat the same
concepts: child-selection iteration, fragment descent, ``@skip`` / ``@include``
directive handling, response-key preservation, and ``edges { node { ... } }``
unwrapping. The plan cache and nested-connection windows depend on those rules
being aligned across the two shapes; a directive or fragment fix landing on one
traversal but not the other produces wrong cached plans, missed nested
prefetches, false strictness warnings, or extra ``COUNT`` work
(``docs/feedback.md`` Major 2).

This module is the single home for both, deliberately split into two explicit
adapters rather than one over-generic polymorphic walker (per the review:
"Keep the adapters explicit, but share the recursion and directive/fragment
policies so the contracts cannot drift"):

- **AST adapter** (``ast_child_selections`` / ``resolve_unvisited_fragment`` /
  ``directive_variable_names``) - operates on graphql-core AST nodes for
  ``optimizer/extension.py``.
- **Converted-selection adapter** (``should_include`` / ``is_fragment`` /
  ``response_key`` / ``response_keys`` / ``included_field_selections`` /
  ``named_children`` / ``with_runtime_prefix`` /
  ``node_children_with_runtime_prefix`` / ``direct_child_selected``) - operates
  on Strawberry converted selections (and the ``SimpleNamespace`` shapes the
  walker synthesizes) for ``optimizer/walker.py`` and the connection seam.

Cycle-safe: ``walker.py`` and ``extension.py`` both import from here; this
module imports neither (it previously lived split between them, with
``extension`` importing the edge-node helpers back from ``walker`` - the reverse
dependency this consolidation removes). It depends only on graphql-core AST node
types and the stdlib.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from graphql.language.ast import DirectiveNode, FragmentSpreadNode, VariableNode

# ---------------------------------------------------------------------------
# AST adapter - graphql-core nodes (``optimizer/extension.py``)
# ---------------------------------------------------------------------------


def ast_child_selections(node: Any) -> tuple[Any, ...]:
    """Return the AST node's selection-set children as a tuple, or ``()``.

    Centralizes the ``getattr(node, "selection_set", None)`` plus
    ``selections or ()`` shape so the AST walkers
    (``_walk_cache_relevant_vars``, ``_walk_reachable_fragment_definitions``,
    and by extension ``_collect_reachable_fragment_definitions``) share
    one "iterate children" implementation. ``FragmentSpreadNode`` has
    no ``selection_set``, so this returns ``()`` and the caller's
    per-child loop becomes a no-op.
    """
    selection_set = getattr(node, "selection_set", None)
    if selection_set is None:
        return ()
    return tuple(selection_set.selections or ())


def resolve_unvisited_fragment(
    node: Any,
    fragments: dict[str, Any],
    visited_fragments: set[str],
) -> Any | None:
    """Resolve a ``FragmentSpreadNode`` to its definition, once.

    Returns the matching ``FragmentDefinitionNode`` and marks the
    fragment name as visited so a sibling or cyclic spread of the same
    fragment in the same walk is a no-op. Returns ``None`` when
    ``node`` is not a fragment spread, when the spread has no name,
    when the fragment name is already visited, or when the document
    does not define the named fragment (defensive - graphql-core's
    validation would normally reject the operation before the optimizer
    sees it). Mutates ``visited_fragments`` on success so callers share
    the same cycle-detection set across recursive descents in both the
    cache-relevant-variable walk and the reachable-fragment walk.
    """
    if not isinstance(node, FragmentSpreadNode):
        return None
    frag_name = node.name.value if node.name else None
    if frag_name is None or frag_name in visited_fragments:
        return None
    frag_def = fragments.get(frag_name)
    if frag_def is None:
        return None
    visited_fragments.add(frag_name)
    return frag_def


def directive_variable_names(node: Any) -> set[str]:
    """Return the variable names referenced in ``@skip`` / ``@include`` on ``node``.

    Only variables inside the ``if`` argument of ``@skip`` / ``@include`` affect
    the selection tree (and therefore the plan cache); every other variable is
    excluded. Defensive against a ``directives`` collection carrying a
    non-``DirectiveNode`` object (pinned by
    ``test_walk_cache_relevant_vars_ignores_non_directive_objects``). The single
    directive-variable extraction the AST cache-key walk shares, so the
    ``("skip", "include")`` membership and the ``VariableNode`` check live once.
    """
    names: set[str] = set()
    for directive in getattr(node, "directives", ()) or ():
        if not isinstance(directive, DirectiveNode):
            continue
        d_name = directive.name.value if directive.name else None
        if d_name not in ("skip", "include"):
            continue
        for arg in directive.arguments or ():
            if isinstance(arg.value, VariableNode):
                names.add(arg.value.name.value)
    return names


# ---------------------------------------------------------------------------
# Converted-selection adapter - Strawberry converted selections + the
# ``SimpleNamespace`` shapes the walker synthesizes (``optimizer/walker.py`` +
# the connection optimizer seam).
# ---------------------------------------------------------------------------


def is_fragment(selection: Any) -> bool:
    """Return ``True`` if the selection is a fragment spread or inline fragment.

    Duck-typed on ``type_condition`` so it matches both Strawberry's
    ``InlineFragment`` / ``FragmentSpread`` and the ``SimpleNamespace`` fragment
    shells the walker clones - a regular field selection has no
    ``type_condition``. This is the SINGLE fragment-vs-field discriminator for
    converted selections, shared by the walker, the connection ``edges { node }``
    unwrap, and the connection ``totalCount`` detection (``direct_child_selected``)
    so the three cannot drift on what counts as a fragment.
    """
    return hasattr(selection, "type_condition")


def should_include(selection: Any) -> bool:
    """Evaluate ``@skip`` / ``@include`` directives on a converted selection."""
    directives = getattr(selection, "directives", None) or {}
    skip = directives.get("skip")
    if skip is not None:
        value = skip.get("if")
        if value is True:
            return False
    include = directives.get("include")
    if include is not None:
        value = include.get("if")
        if value is False:
            return False
    return True


def response_key(selection: Any) -> str:
    """Return the GraphQL response key for a field selection."""
    return getattr(selection, "alias", None) or selection.name


def response_keys(selection: Any) -> tuple[str, ...]:
    """Return all response keys represented by a possibly merged selection."""
    return tuple(
        getattr(selection, "_optimizer_response_keys", None) or (response_key(selection),),
    )


def included_field_selections(selections: list[Any]) -> list[Any]:
    """Return included fields with fragment bodies inlined before field merging.

    Directive filtering happens on both fragment nodes and their nested field
    selections. Returning a flat field list lets alias/relation merging combine
    duplicate relation branches before generated child ``Prefetch`` querysets
    are built.
    """
    result: list[Any] = []
    for selection in selections:
        if not should_include(selection):
            continue
        if is_fragment(selection):
            result.extend(
                included_field_selections(list(getattr(selection, "selections", None) or [])),
            )
            continue
        result.append(selection)
    return result


def named_children(selection: Any, name: str) -> list[Any]:
    """Return included direct children named ``name``, recursing through fragments."""
    children: list[Any] = []
    for child in getattr(selection, "selections", None) or []:
        if not should_include(child):
            continue
        if is_fragment(child):
            for fragment_child in getattr(child, "selections", None) or []:
                fragment_shell = SimpleNamespace(selections=[fragment_child])
                children.extend(named_children(fragment_shell, name))
            continue
        if getattr(child, "name", None) == name:
            children.append(child)
    return children


def with_runtime_prefix(selection: Any, runtime_prefixes: tuple[tuple[str, ...], ...]) -> Any:
    """Clone a node-level selection carrying runtime prefixes for the walker."""
    if is_fragment(selection):
        return SimpleNamespace(
            name=getattr(selection, "name", None),
            type_condition=selection.type_condition,
            directives=getattr(selection, "directives", None) or {},
            selections=[
                with_runtime_prefix(child, runtime_prefixes)
                for child in getattr(selection, "selections", None) or []
            ],
        )
    return SimpleNamespace(
        name=selection.name,
        alias=getattr(selection, "alias", None),
        directives=getattr(selection, "directives", None) or {},
        arguments=getattr(selection, "arguments", None) or {},
        selections=list(getattr(selection, "selections", None) or []),
        _optimizer_runtime_prefixes=list(runtime_prefixes),
    )


def node_children_with_runtime_prefix(
    node_selection: Any,
    *,
    runtime_prefixes: tuple[tuple[str, ...], ...],
) -> list[Any]:
    """Clone node children with a connection-aware runtime prefix."""
    children: list[Any] = []
    for child in getattr(node_selection, "selections", None) or []:
        if not should_include(child):
            continue
        children.append(with_runtime_prefix(child, runtime_prefixes))
    return children


def direct_child_selected(selection_roots: Any, name: str) -> bool:
    """Return whether ``name`` is a direct child of ``selection_roots``, through fragments only.

    Recurses ONLY through fragment wrappers (``is_fragment``), NOT into a regular
    field's sub-selections, so a field named ``name`` nested deeper in the tree
    does NOT count. The connection field's ``totalCount`` detection
    (``connection.py::_total_count_requested``) uses this so a fragment-wrapped
    direct ``totalCount`` still fires the count while a node-level nested
    connection's ``totalCount`` deep inside ``edges { node { ... } }`` does not
    trip the OUTER connection's predicate. Sharing the ``is_fragment``
    discriminator with the walker / edge-node unwrap keeps the "recurse through
    fragments only" rule from drifting between the count detection and the
    selection planning.
    """

    def _check(selection: Any) -> bool:
        if is_fragment(selection):
            return any(_check(child) for child in getattr(selection, "selections", None) or [])
        return getattr(selection, "name", None) == name

    return any(_check(child) for child in selection_roots)
