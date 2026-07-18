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
  ``optimizer/extension.py``. ``resolve_unvisited_fragment`` accepts optional
  ``depth`` so the reachable-fragment walk (name key) and the
  cache-relevant-variable walk (``(name, depth)`` key) share one resolve
  guard.
- **Converted-selection adapter** (``should_include`` / ``is_fragment`` /
  ``response_key`` / ``response_keys`` / ``included_field_selections`` /
  ``named_children`` / ``with_runtime_prefix`` /
  ``node_children_with_runtime_prefix`` / ``connection_node_children`` /
  ``direct_child_selected``) - operates on Strawberry converted selections
  (and the ``SimpleNamespace`` shapes the walker synthesizes) for three
  consumers: ``optimizer/walker.py`` / ``nested_planner.py`` (nested
  connection windows), ``optimizer/extension.py``'s root-connection seam
  (both call ``connection_node_children`` for the ``edges { node }`` unwrap),
  and ``connection.py``'s ``totalCount`` detection (``direct_child_selected``
  only).

Cycle-safe: ``walker.py`` and ``extension.py`` both import from here; this
module imports neither (it previously lived split between them, with
``extension`` importing the edge-node helpers back from ``walker`` - the reverse
dependency this consolidation removes). It depends only on graphql-core AST node
types and the stdlib.
"""

from __future__ import annotations

from contextvars import ContextVar
from types import SimpleNamespace
from typing import Any

from graphql.language.ast import (
    DirectiveNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    VariableNode,
)

# ---------------------------------------------------------------------------
# AST -> converted-selection adapter - the package-owned ``convert_selections``
# ---------------------------------------------------------------------------


# Per-execution memo for the converted-selection tree, keyed by the field
# nodes' ids. ``prime_selected_fields`` runs the full AST -> ``SelectedField``
# conversion on every connection resolution, and a nested FALLBACK connection
# resolves once per parent row with a fresh Strawberry ``Info`` each time - but
# graphql-core's executor caches collected sub-fields per execution
# (``ExecutionContext._subfields_cache``), so every row's ``info.field_nodes``
# is the SAME node group, and the conversion depends only on per-execution
# constants (``info.fragments`` / ``info.variable_values``). Reusing the first
# row's converted list collapses N per-row conversions to one. The key mirrors
# graphql-core's own subfields-cache shape (the ids of the individual field
# nodes, NOT the id of the wrapping list, which may be rebuilt or reused): AST
# node ids are stable for the memo's whole lifetime because the document is
# owned by the execution context that spans the same ``on_execute`` lifecycle.
# Set to an empty dict / reset by ``DjangoOptimizerExtension.on_execute``
# (``extension.py`` imports this name; this module stays stdlib +
# graphql-core only). ``None`` (the default) outside an ``on_execute``
# lifecycle disables the memo, so direct / test callers see unchanged behavior.
# Consumers treat the converted list as read-only (the walker clones before
# mutating; Strawberry's ``selected_fields`` readers only iterate), so sharing
# one list across rows is safe.
converted_selections_cache: ContextVar[dict[Any, list[Any]] | None] = ContextVar(
    "django_strawberry_framework_converted_selections_cache",
    default=None,
)


def ast_to_converted_selections(info: Any, field_nodes: Any) -> list[Any]:
    """Convert graphql-core ``field_nodes`` to converted selections, anonymous-safe.

    Mirrors Strawberry's ``strawberry.types.nodes.convert_selections`` but builds
    every inline-fragment shell with ``type_condition = None`` when the node has no
    ``on TypeName`` condition, instead of unguardedly reading
    ``node.type_condition.name.value`` (Strawberry's ``InlineFragment.from_node``
    raises ``AttributeError: 'NoneType' object has no attribute 'name'`` on a valid
    anonymous inline fragment ``... { f }``). The optimizer routes
    ``info.field_nodes`` through here so its own fragment-aware substrate
    (``is_fragment`` duck-types on ``type_condition``, which a ``None`` shell still
    satisfies, so the shell flows through ``included_field_selections`` /
    ``named_children`` / ``with_runtime_prefix``) handles the shape Strawberry
    cannot represent - rather than depending on a Strawberry internal that
    mishandles a spec-valid query.

    The whole recursion is reimplemented (not just the top-level inline branch)
    because an anonymous inline fragment can sit at any depth - e.g.
    ``{ items { edges { node { ... { name } } } } }`` - and Strawberry's
    ``SelectedField.from_node`` / ``FragmentSpread.from_node`` recurse back into
    its own crashing ``convert_selections``. ``FragmentSpread`` definitions still
    come from ``info.fragments`` (a named spread always carries a type condition);
    only its body selections are re-converted here.

    The result is built from Strawberry's own ``SelectedField`` / ``FragmentSpread``
    / ``InlineFragment`` dataclasses (not ad-hoc shells) so the converted list is
    drop-in compatible with BOTH the package's duck-typed substrate AND Strawberry's
    own consumers that ``isinstance``-check against those classes (e.g.
    ``strawberry.relay.utils.should_resolve_list_connection_edges`` reached via
    ``ListConnection.resolve_connection`` when the package primes
    ``info.selected_fields`` with this list). The only deviation from Strawberry is
    that the anonymous inline-fragment branch passes ``type_condition=None`` instead
    of dereferencing the missing condition.

    This is a FAITHFUL MIRROR and must stay one: for every non-anonymous query
    shape the output is byte-identical to ``convert_selections`` (verified
    field-by-field, including nested argument and directive values, against the
    stock converter). That identity is load-bearing because ``prime_selected_fields``
    seeds this list into ``info.selected_fields``; any divergence here would corrupt
    ``info.selected_fields`` for normal (non-anonymous) queries the moment a
    connection primes it. Keep it a mirror - if Strawberry's ``convert_selections``
    gains a field or changes a shape, mirror the change here rather than diverging.

    Memoized per execution via ``converted_selections_cache`` (see the
    ``ContextVar`` comment above): within one ``on_execute`` lifecycle the same
    field-node group converts once, so the per-parent-row
    ``prime_selected_fields`` calls of a fallback connection pipeline reuse the
    first row's list instead of re-running the conversion for every parent.
    """
    memo = converted_selections_cache.get()
    memo_key: Any = None
    if memo is not None:
        # One-node groups are the overwhelmingly common shape; key on the single
        # node's id directly to skip the tuple build (graphql-core's own
        # subfields cache makes the same trade).
        memo_key = id(field_nodes[0]) if len(field_nodes) == 1 else tuple(map(id, field_nodes))
        converted = memo.get(memo_key)
        if converted is not None:
            return converted

    from strawberry.types.nodes import (
        FragmentSpread,
        InlineFragment,
        SelectedField,
        convert_arguments,
        convert_directives,
    )

    def _convert(nodes: Any) -> list[Any]:
        out: list[Any] = []
        for node in nodes:
            if isinstance(node, InlineFragmentNode):
                condition = node.type_condition
                out.append(
                    InlineFragment(
                        type_condition=(condition.name.value if condition is not None else None),
                        directives=convert_directives(info, node.directives),
                        selections=_convert(ast_child_selections(node)),
                    ),
                )
            elif isinstance(node, FragmentSpreadNode):
                fragment = info.fragments[node.name.value]
                out.append(
                    FragmentSpread(
                        name=node.name.value,
                        type_condition=fragment.type_condition.name.value,
                        directives=convert_directives(info, node.directives),
                        selections=_convert(ast_child_selections(fragment)),
                    ),
                )
            else:
                out.append(
                    SelectedField(
                        name=node.name.value,
                        alias=getattr(node.alias, "value", None),
                        directives=convert_directives(info, node.directives),
                        arguments=convert_arguments(info, node.arguments),
                        selections=_convert(ast_child_selections(node)),
                    ),
                )
        return out

    converted = _convert(field_nodes)
    if memo is not None:
        memo[memo_key] = converted
    return converted


def prime_selected_fields(info: Any) -> None:
    """Pre-seed Strawberry ``Info.selected_fields`` with the anonymous-safe conversion.

    ``Info.selected_fields`` is a ``functools.cached_property`` that lazily calls
    Strawberry's crashing ``convert_selections`` on first read. Several consumers
    on the connection resolve path read it - the package's own
    ``connection.py::_total_count_requested`` AND Strawberry's own
    ``relay.utils.should_resolve_list_connection_edges`` (reached via
    ``ListConnection.resolve_connection``) - so an anonymous inline fragment on a
    connection query crashes inside Strawberry's resolver before the package can
    intervene. Computing the conversion through ``ast_to_converted_selections`` and
    storing it in the cached-property slot makes every later read return the
    package's anonymous-safe list (built from Strawberry's own ``SelectedField`` /
    ``FragmentSpread`` / ``InlineFragment`` dataclasses, so Strawberry's
    ``isinstance``-based consumers keep working). Idempotent and a no-op when the
    info has no field nodes or the cache is already populated (so a consumer that
    legitimately read ``selected_fields`` first is never overwritten).

    Must run BEFORE any ``info.selected_fields`` read on the connection path - the
    cached property computes once on first read, so priming only wins if it lands
    first. ``connection.py::_resolve_connection_fast_path`` calls this immediately
    after the ``first`` + ``last`` guard, ahead of both the ``_total_count_requested``
    inspection and ``super().resolve_connection``.

    NOTE - this COUPLES to two Strawberry internals: the raw info living at
    ``Info._raw_info`` and ``Info.selected_fields`` being a ``functools.cached_property``
    backed by the ``info.__dict__["selected_fields"]`` slot. Both hold at the pinned
    Strawberry version. If a future Strawberry renames ``_raw_info`` (or stops using
    the dict-slot cache), this SILENTLY no-ops - ``getattr(info, "_raw_info", None)``
    returns ``None``, nothing is seeded, and the connection-path crash returns rather
    than failing loudly. The live anonymous-inline-fragment tests
    (``test_anonymous_inline_fragment_*`` in the fakeshop ``test_query`` suite) are
    the regression net that would catch such a Strawberry-internals rename on a
    version bump.
    """
    raw_info = getattr(info, "_raw_info", None)
    field_nodes = getattr(raw_info, "field_nodes", None)
    if not field_nodes or "selected_fields" in info.__dict__:
        return
    info.__dict__["selected_fields"] = ast_to_converted_selections(raw_info, field_nodes)


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
    visited_fragments: set[Any],
    *,
    depth: int | None = None,
) -> Any | None:
    """Resolve a ``FragmentSpreadNode`` to its definition, once per visit key.

    Returns the matching ``FragmentDefinitionNode`` and marks the visit key
    so a sibling or cyclic spread in the same walk is a no-op. The visit key
    is the fragment name when ``depth`` is omitted (reachable-fragment
    collection for the plan-cache document key) and ``(name, depth)`` when
    ``depth`` is supplied (depth-sensitive cache-relevant-variable walk: the
    same fragment spread at two response-path depths must be walked once per
    depth so nested pagination variables are not dropped). Returns ``None``
    when ``node`` is not a fragment spread, when the spread has no name, when
    the visit key is already present, or when the document does not define
    the named fragment (defensive - graphql-core's validation would normally
    reject the operation before the optimizer sees it). Mutates
    ``visited_fragments`` on success so callers share one cycle-detection set
    across recursive descents.
    """
    if not isinstance(node, FragmentSpreadNode):
        return None
    frag_name = node.name.value if node.name else None
    if frag_name is None:
        return None
    visit_key: Any = frag_name if depth is None else (frag_name, depth)
    if visit_key in visited_fragments:
        return None
    frag_def = fragments.get(frag_name)
    if frag_def is None:
        return None
    visited_fragments.add(visit_key)
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
    directives = getattr(selection, "directives", None)
    # Directive-free selections are the overwhelmingly common shape, and this
    # predicate runs once per selection per walk level; skip the two dict
    # probes when there is nothing to evaluate.
    if not directives:
        return True
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


# TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer
# entry card): add a tri-state fragment classifier to this converted selection
# inliner, but keep the default path byte-for-byte unconditional. Reachability:
# an abstract (interface/union) root field never reaches the walker today -
# registry.model_for_type returns None for the abstract origin, so _optimize
# passes the queryset through before this inliner runs; the classifier therefore
# ships nothing until that card first builds the abstract-return production-entry
# contract (R1). Pseudocode: no classifier means INLINE-all for extension
# cache-key and connection extraction callers; a walker-supplied classifier
# returns INLINE, SKIP, or RECURSE_FRAGMENTS_ONLY. The recursion mode drops
# direct fields for an unknown composite/union condition while still re-checking
# nested fragments.
def included_field_selections(selections: list[Any]) -> list[Any]:
    """Return included fields with fragment bodies inlined before field merging.

    Directive filtering happens on both fragment nodes and their nested field
    selections. Returning a flat field list lets alias/relation merging combine
    duplicate relation branches before generated child ``Prefetch`` querysets
    are built.

    Fast path: when no selection is a fragment and none is directive-excluded
    (the overwhelmingly common query shape), the flatten/filter loop would
    rebuild an identical list - so the input list is returned unchanged
    instead, mirroring ``walker._merge_aliased_selections``'s passthrough.
    Both callers (the walker's level descent and the FK-id-elision scalar
    scan) only iterate the result, so sharing the caller's list is safe.
    """
    for selection in selections:
        if is_fragment(selection) or not should_include(selection):
            break
    else:
        return selections
    result: list[Any] = []
    for selection in selections:
        if not should_include(selection):
            continue
        if is_fragment(selection):
            # No defensive ``list(...)`` copy: the recursion only iterates the
            # child collection, so any sequence shape passes through as-is.
            result.extend(
                included_field_selections(getattr(selection, "selections", None) or []),
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
            # Recurse into the fragment directly: its own ``selections`` are the
            # children to search, so re-entering ``named_children`` on the
            # fragment iterates them (and descends nested fragments) with the
            # same ``should_include`` / name-match rules. This avoids allocating
            # a throwaway single-child ``SimpleNamespace`` shell per fragment
            # child - the former shape, which wrapped each child only to give the
            # recursion a ``.selections`` to walk.
            children.extend(named_children(child, name))
            continue
        if getattr(child, "name", None) == name:
            children.append(child)
    return children


def with_runtime_prefix(selection: Any, runtime_prefixes: tuple[tuple[str, ...], ...]) -> Any:
    """Clone a node-level selection carrying runtime prefixes for the walker.

    Fragments are descended, never marked; the ``_optimizer_runtime_prefixes``
    marker lands on field leaves only. A fragment shell carrying the prefix
    would be meaningless - prefixes belong on the field selections the walker
    eventually plans.
    """
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


def connection_node_children(
    selection: Any,
    *,
    runtime_prefixes: tuple[tuple[str, ...], ...],
) -> list[Any]:
    """Unwrap a Relay connection's ``edges { node { ... } }`` child selections.

    Single owner of the edges->node composition that accumulates response-key
    prefixes and clones node children for the walker. Shared by the root
    connection apply seam (``extension.py``) and nested-connection planning
    (``nested_planner.py``) so fragment / directive / prefix semantics cannot
    drift between those call sites. Returns an empty list when the selection
    has no ``edges { node }`` (e.g. ``pageInfo`` / ``totalCount`` only).
    """
    node_children: list[Any] = []
    for edge_selection in named_children(selection, "edges"):
        edge_path_prefixes = tuple((*rp, response_key(edge_selection)) for rp in runtime_prefixes)
        for node_selection in named_children(edge_selection, "node"):
            node_path_prefixes = tuple(
                (*ep, response_key(node_selection)) for ep in edge_path_prefixes
            )
            node_children.extend(
                node_children_with_runtime_prefix(
                    node_selection,
                    runtime_prefixes=node_path_prefixes,
                ),
            )
    return node_children


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

    Gated on ``should_include`` like ``included_field_selections`` and
    ``named_children``: converted selections carry live, already-evaluated
    ``@skip`` / ``@include`` args, so a ``totalCount @skip(if: true)`` (or a
    ``@skip``-ped fragment wrapping it) must NOT fire the connection ``COUNT``.
    A directive-excluded field returns ``False`` even on a name match, and an
    excluded fragment shell prunes its whole subtree.
    """

    def _check(selection: Any) -> bool:
        if not should_include(selection):
            return False
        if is_fragment(selection):
            return any(_check(child) for child in getattr(selection, "selections", None) or [])
        return getattr(selection, "name", None) == name

    return any(_check(child) for child in selection_roots)


def connection_total_count_selected(selection: Any) -> bool:
    """Return whether ``selection`` (a connection field) selects ``totalCount``.

    ``totalCount`` as a DIRECT child of the connection, through fragment
    wrappers only (``direct_child_selected``). The single implementation of
    the count-observability walk: the plan-time
    ``connection_count_required`` and the resolve-time
    ``connection.py::_total_count_requested`` both call it, so the two
    halves of the conditional ``_dst_total_count`` contract share one walk
    by construction.
    """
    children = getattr(selection, "selections", None) or []
    return direct_child_selected(children, "totalCount")


def connection_has_next_page_selected(selection: Any) -> bool:
    """Return whether ``selection`` selects ``pageInfo { hasNextPage }``.

    The ``hasNextPage`` sibling of ``connection_total_count_selected``: a
    direct ``pageInfo`` child (through fragment wrappers, alias-merged via
    ``named_children``), then a direct ``hasNextPage`` under it. Shared by
    the plan-time ``connection_count_required`` and the resolve-time
    ``connection.py::_has_next_page_requested``.
    """
    return any(
        direct_child_selected(getattr(page_info, "selections", None) or [], "hasNextPage")
        for page_info in named_children(selection, "pageInfo")
    )


def connection_count_required(selection: Any) -> bool:
    """Return whether a connection selection can OBSERVE the partition total count.

    The count-OBSERVABILITY predicate (connection window rigor, workstream B):
    ``True`` when the selection carries ``totalCount`` as a direct child of the
    connection, or ``hasNextPage`` under a direct ``pageInfo`` child - the two
    fields a per-partition ``Count(1) OVER (PARTITION BY ...)`` can serve
    (cursors and ``hasPreviousPage`` need only ``_dst_row_number``). Both walks
    live in the two per-selection primitives above, which the resolve-time
    predicates (``connection.py::_total_count_requested`` and its ``hasNextPage``
    sibling) call too, so plan-time and resolve-time share ONE implementation of
    each walk - and the resolve-time defensive fallback covers even a drift here.

    This is the generic observability gate, NOT the planner's final count
    decision. The planner computes the ``totalCount`` and ``hasNextPage``
    observers SEPARATELY
    (``optimizer/nested_planner.py::plan_connection_relation``) and feeds them to
    the single ``WindowRangePlan.fetch_mode`` decision: a plain ``first: N`` page
    that selects ``hasNextPage`` but NOT ``totalCount`` resolves to
    ``FetchMode.PROBED``, served by the n+1 overfetch probe with NO
    ``_dst_total_count`` annotation (``utils/connections.py::FetchMode``), its
    ``hasNextPage`` read from the sentinel's presence rather than
    ``row_number < total``. Nor does every count-observable shape annotate the
    count: an unbounded forward or reversed ``last``-only page with
    ``hasNextPage`` selected resolves to ``FetchMode.CONSTANT_FALSE`` and serves
    ``hasNextPage`` as a constant ``False`` with NO ``_dst_total_count`` either.
    So ``True`` here means "the count is observable"; the fetch mode
    then chooses count vs probe vs constant-false.

    Alias-merged selections carry the UNION of every alias's children
    (``walker.py::_merge_aliased_selections``), so one alias selecting
    ``totalCount`` conservatively keeps the count for the shared window.
    """
    return connection_total_count_selected(selection) or connection_has_next_page_selected(
        selection,
    )
