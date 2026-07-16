"""``DjangoOptimizerExtension`` - Strawberry schema extension solving N+1 via queryset plans.

Opt-in at schema construction::

    _optimizer = DjangoOptimizerExtension()
    schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: _optimizer],
    )

The extension hooks Strawberry's ``resolve`` middleware. At the
operation's **root resolver** (detected via ``info.path.prev is None``)
it walks the entire selection tree once using the O2 walker, builds an
``OptimizationPlan``, and applies ``select_related`` /
``prefetch_related`` to the root queryset. Non-root resolvers pass
through untouched - Django's ``prefetch_related`` with ``__``-chained
paths handles nested optimization in a single pass.

Load-bearing rule (O6): when a related field's target ``DjangoType``
defines a non-default ``get_queryset``, generate a
``Prefetch(...)`` keyed on the filtered queryset instead of a
``select_related``. This is the visibility-leak fix from
strawberry-graphql-django #572 / #583. We copy the behaviour, not the
API.

Architecture modeled on ``strawberry_django/optimizer.py`` - same
root-gate pattern, same ``ContextVar`` lifecycle, same recursive
type-tracing through graphql-core wrappers.
"""

import inspect
from collections import OrderedDict
from collections.abc import Callable, Mapping, Set
from contextlib import suppress
from contextvars import ContextVar
from typing import Any, NamedTuple

from django.db import models
from graphql.language.ast import (
    FieldNode,
    FragmentSpreadNode,
    VariableNode,
)
from graphql.language.printer import print_ast
from graphql.type.definition import GraphQLInterfaceType
from strawberry.extensions import SchemaExtension

from ..registry import registry
from ..utils.querysets import normalize_query_source
from ..utils.typing import unwrap_graphql_type
from . import logger
from ._context import (
    DST_OPTIMIZER_FK_ID_ELISIONS,
    DST_OPTIMIZER_LOOKUP_PATHS,
    DST_OPTIMIZER_PLAN,
    DST_OPTIMIZER_PLANNED,
    DST_OPTIMIZER_STRICTNESS,
)
from ._context import (
    clear_optimizer_context as _clear_optimizer_context,
)
from ._context import (
    get_context_value as _get_context_value,
)
from ._context import (
    stash_on_context as _stash_on_context,
)
from .hints import hint_is_skip
from .nested_fetch import _active_strategy as _active_nested_strategy
from .nested_fetch import resolve_strategy
from .plans import (
    diff_plan_for_queryset,
    lookup_paths,
    prune_unsupportable_select_related,
    runtime_path_from_info,
)
from .selections import (
    ast_child_selections,
    ast_to_converted_selections,
    converted_selections_cache,
    directive_variable_names,
    named_children,
    node_children_with_runtime_prefix,
    resolve_unvisited_fragment,
    response_key,
)
from .walker import plan_optimizations, plan_relation

# The selection-traversal primitives moved to ``optimizer/selections.py`` in the
# 0.0.9 DRY pass (``docs/feedback.md`` Major 2). The underscore aliases keep this
# module's bodies - and the tests that import ``_named_children`` /
# ``_node_children_with_runtime_prefix`` from ``optimizer.extension`` - working
# unchanged. ``extension`` no longer imports the converted-selection helpers back
# from ``walker`` (the reverse dependency the substrate removes); both modules now
# source them from ``selections``.
_child_selections = ast_child_selections
_unvisited_fragment_definition = resolve_unvisited_fragment
_named_children = named_children
_node_children_with_runtime_prefix = node_children_with_runtime_prefix
_response_key = response_key

_MAX_PLAN_CACHE_SIZE = 256

# The Relay pagination argument names whose variable-supplied values must key
# the plan cache when they appear on a NON-ROOT field node (Slice 1 bakes those
# resolved values into windowed prefetch querysets, so two requests differing
# only in a nested ``first: $n`` value need distinct cached plans -- Decision 7).
# Single source of truth for the four argument names; a future ``search:``
# extension (``0.1.2``) would extend the family here, not re-spell it inline.
_PAGINATION_ARG_NAMES = frozenset(
    {
        "first",
        "last",
        "before",
        "after",
    },
)

# Re-export the stash helper under its original underscore-prefixed name so
# existing tests that import ``from ...extension import _stash_on_context``
# keep working without a churn pass.  Canonical implementation lives in
# ``optimizer/_context.py`` for cross-subpackage reuse with the read-side
# ``get_context_value`` (consumed by ``types/resolvers.py``).
__all__ = (
    "CacheInfo",
    "DjangoOptimizerExtension",
    "_stash_on_context",
    "apply_connection_optimization",
)


def _walk_cache_relevant_vars(
    node: Any,
    fragments: dict[str, Any],
    visited_fragments: set[tuple[str, int]],
    depth: int,
    directive_names: set[str],
    pagination_names: set[str],
) -> None:
    """The single AST traversal collecting BOTH cache-relevant variable families.

    One descent collects two families on different axes:

    * **Directive variables** - ``@skip`` / ``@include`` variable references on
      EVERY node, independent of depth.
    * **Nested pagination variables** - ``first`` / ``last`` / ``before`` /
      ``after`` variable references only when the current node is a ``FieldNode``
      at response-path depth >= 1 (root-field pagination stays out: a root
      connection's slicing happens post-plan in ``ConnectionExtension`` and plan
      content is invariant in those, so hashing them would fragment the cache
      across every page of a pagination loop).

    Depth increments only when descending into a **field** node's selection set;
    descending into a resolved fragment definition keeps the SPREAD-SITE depth (a
    fragment is a transparent wrapper at its spread site -- Decision 7's "depth at
    the spread SITE, not raw fragment-definition nesting"), so a spread at the
    root contributes root-depth fields and a spread inside a nested node
    contributes nested-depth fields. The cycle guard keys ``visited_fragments``
    on ``(fragment_name, spread-site depth)`` so a fragment spread twice at the
    SAME depth is walked once, while the SAME fragment spread at two DIFFERENT
    depths is walked once per depth: pagination collection is depth-sensitive, so
    a name-only guard would let the first-visited spread site (e.g. a root spread,
    where pagination is excluded) suppress a later nested spread of the same
    fragment and silently drop its nested pagination variable from the cache key
    -- a correctness bug (Decision 7: "under-collection would serve wrong data").
    Termination still holds: graphql-core rejects fragment cycles before the
    optimizer runs, and a defensive cycle that does not cross a field node keeps
    depth constant, so ``(name, depth)`` repeats and the descent stops.

    Replaces the previously separate ``_walk_directives`` / ``_walk_pagination_vars``
    walkers: the two collection RULES differ but the child-traversal,
    fragment-spread descent, and cycle-guard plumbing were identical, and keeping
    them apart risked a future fragment-depth or cycle fix landing on only one
    path.
    """
    # Directive variables: collected on every node, depth-independent. The
    # ``@skip`` / ``@include`` variable extraction is the shared AST-adapter
    # primitive (``optimizer/selections.py::directive_variable_names``).
    directive_names.update(directive_variable_names(node))
    # Nested pagination variables: only on a field node at depth >= 1.
    if depth >= 1 and isinstance(node, FieldNode):
        for arg in node.arguments or ():
            if arg.name.value in _PAGINATION_ARG_NAMES and isinstance(arg.value, VariableNode):
                pagination_names.add(arg.value.name.value)
    # A field node deepens the response path for its children; a fragment
    # wrapper does not, so its body inherits the field node's depth here.
    child_depth = depth + 1 if isinstance(node, FieldNode) else depth
    for child in _child_selections(node):
        # Recurse into the child first so directives attached to the child
        # itself are collected (a FragmentSpreadNode has no ``selection_set``,
        # so this tail is just the directive sweep for spread-node directives).
        _walk_cache_relevant_vars(
            child,
            fragments,
            visited_fragments,
            child_depth,
            directive_names,
            pagination_names,
        )
        # Resolve the fragment spread depth-aware: the generic name-only
        # ``resolve_unvisited_fragment`` guard would suppress a second spread of
        # the same fragment regardless of depth, dropping nested pagination
        # variables when an earlier root-depth spread visited the fragment first.
        # Key the visited set on ``(name, child_depth)`` so the same fragment is
        # walked once per distinct spread-site depth.
        frag_def = _unvisited_fragment_at_depth(
            child,
            fragments,
            visited_fragments,
            child_depth,
        )
        if frag_def is not None:
            _walk_cache_relevant_vars(
                frag_def,
                fragments,
                visited_fragments,
                child_depth,
                directive_names,
                pagination_names,
            )


def _unvisited_fragment_at_depth(
    node: Any,
    fragments: dict[str, Any],
    visited_fragments: set[tuple[str, int]],
    depth: int,
) -> Any | None:
    """Resolve a ``FragmentSpreadNode`` to its definition, once per ``(name, depth)``.

    The depth-aware sibling of ``selections.resolve_unvisited_fragment``: it dedupes
    on ``(fragment_name, spread-site depth)`` instead of name alone so the
    depth-sensitive pagination-variable walk can revisit a fragment spread at a
    different response-path depth. Returns ``None`` when ``node`` is not a fragment
    spread, has no name, names an undefined fragment, or has already been visited at
    this depth; mutates ``visited_fragments`` on success.
    """
    if not isinstance(node, FragmentSpreadNode):
        return None
    frag_name = node.name.value if node.name else None
    key = (frag_name, depth)
    if frag_name is None or key in visited_fragments:
        return None
    frag_def = fragments.get(frag_name)
    if frag_def is None:
        return None
    visited_fragments.add(key)
    return frag_def


def _collect_cache_var_families(node: Any, fragments: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Run the unified traversal and return ``(directive_names, pagination_names)``.

    The single entry the thin family wrappers and the union collector share, so
    the AST is walked once per call regardless of which family the caller wants.
    """
    directive_names: set[str] = set()
    pagination_names: set[str] = set()
    _walk_cache_relevant_vars(node, fragments, set(), 0, directive_names, pagination_names)
    return directive_names, pagination_names


def _collect_directive_var_names(
    node: Any,
    fragments: dict[str, Any] | None = None,
) -> frozenset[str]:
    """Return variable names used in ``@skip`` / ``@include`` directives.

    Thin wrapper over the unified ``_collect_cache_var_families`` traversal,
    returning only the directive family. Only variables referenced inside the
    ``if`` argument of ``@skip`` / ``@include`` matter for plan caching; all
    other variables do not affect the selection tree and must be excluded from
    the cache key to avoid cardinality explosion. ``fragments`` follows
    ``FragmentSpreadNode`` references into their definitions so directives inside
    named fragments are included in the cache key.
    """
    directive_names, _ = _collect_cache_var_families(node, fragments or {})
    return frozenset(directive_names)


def _collect_nested_pagination_var_names(
    node: Any,
    fragments: dict[str, Any] | None = None,
) -> frozenset[str]:
    """Return variable names used in pagination args on **non-root** field nodes.

    Thin wrapper over the unified ``_collect_cache_var_families`` traversal,
    returning only the pagination family (``first`` / ``last`` / ``before`` /
    ``after`` variables on a field node at response-path depth >= 1). Slice 1
    bakes those resolved pagination values into windowed prefetch querysets, so
    two requests sharing a printed AST (``booksConnection(first: $n)``) but
    differing in ``$n`` must NOT share a cached plan -- a correctness rule
    (Decision 7). The collection is a syntactic SUPERSET by design: any non-root
    field's pagination-named variable is collected; over-collection costs cheap
    duplicate cache entries, under-collection would serve wrong data.
    """
    _, pagination_names = _collect_cache_var_families(node, fragments or {})
    return frozenset(pagination_names)


def _collect_cache_relevant_var_names(operation: Any, fragments: dict[str, Any]) -> frozenset[str]:
    """Union of the cache-relevant variable names for one operation.

    Combines the ``@skip`` / ``@include`` directive variable names with the
    non-root pagination variable names -- in ONE AST traversal
    (``_collect_cache_var_families``) -- so ``_build_cache_key`` folds one name
    set through its single ``(name, value)`` comprehension. The result is what
    ``_doc_cache_entry`` memoizes cross-request alongside the rendered document
    key (both are pure functions of the document text).
    """
    directive_names, pagination_names = _collect_cache_var_families(operation, fragments)
    return frozenset(directive_names | pagination_names)


def _hashable_variable_value(value: Any) -> Any:
    """Return a hashable, collision-resistant cache identity for a variable value.

    ``_build_cache_key`` stores cache-relevant ``(name, value)`` pairs in a
    ``frozenset``. GraphQL lists and input objects arrive as unhashable Python
    containers, and custom scalar parsers may legally return any Python value,
    including sets or user-defined unhashable objects. This matters even when a
    value cannot affect a plan: the nested-pagination collector deliberately
    over-collects by argument name, so a plain nested field such as
    ``logs(after: $values)`` can put any input type on this cache boundary.

    Standard containers receive tagged structural identities. Tags preserve
    distinctions such as list versus tuple and bool versus int; unordered
    containers sort by ``repr`` so mixed, mutually-unorderable values remain
    deterministic. An opaque unhashable object has no generally correct
    structural identity, so it receives a fresh token: that request may miss the
    cross-request plan cache, but it cannot collide with another value and serve
    the wrong plan. The same fallback terminates a custom scalar that returns a
    cyclic container.
    """
    return _freeze_variable_value(value, set())


def _freeze_variable_value(value: Any, active_containers: set[int]) -> Any:
    """Recursive implementation for ``_hashable_variable_value``."""
    try:
        hash(value)
    except TypeError:
        pass
    else:
        return ("scalar", type(value), value)

    is_container = isinstance(
        value,
        (
            Mapping,
            list,
            tuple,
            Set,
        ),
    )
    if not is_container:
        return ("opaque", type(value), object())

    container_id = id(value)
    if container_id in active_containers:
        return ("cycle", type(value), object())
    active_containers.add(container_id)
    try:
        if isinstance(value, Mapping):
            items = (
                (
                    _freeze_variable_value(key, active_containers),
                    _freeze_variable_value(item, active_containers),
                )
                for key, item in value.items()
            )
            return ("mapping", type(value), tuple(sorted(items, key=repr)))
        if isinstance(value, Set):
            items = (_freeze_variable_value(item, active_containers) for item in value)
            return ("set", type(value), tuple(sorted(items, key=repr)))
        return (
            "list" if isinstance(value, list) else "tuple",
            type(value),
            tuple(_freeze_variable_value(item, active_containers) for item in value),
        )
    finally:
        active_containers.remove(container_id)


def _collect_reachable_fragment_definitions(
    node: Any,
    fragments: dict[str, Any],
) -> tuple[Any, ...]:
    """Return every named fragment definition reachable from ``node``.

    Walks the AST in selection-set order, deterministically, so the
    same operation + fragment map produces the same tuple on every
    call. Each fragment definition is included once (via the
    visited-fragments cycle guard inside
    ``_unvisited_fragment_definition``). The returned tuple feeds
    ``_print_operation_with_reachable_fragments`` so the plan-cache
    key includes the fragment bodies the planner will actually expand,
    closing the ``query Q { ...F } fragment F { ... }`` cache-key gap
    flagged in this module's review artifact.
    """
    reachable: list[Any] = []
    _walk_reachable_fragment_definitions(node, fragments, set(), reachable)
    return tuple(reachable)


def _walk_reachable_fragment_definitions(
    node: Any,
    fragments: dict[str, Any],
    visited_fragments: set[str],
    reachable: list[Any],
) -> None:
    """Recursive workhorse for ``_collect_reachable_fragment_definitions``.

    For each child selection: if the child is an unvisited fragment
    spread, append its definition to ``reachable`` and recurse into
    the definition so transitively-spread fragments are also
    collected; then recurse into the child itself so inline-fragment
    children and regular field children contribute their nested
    spreads. The "always recurse into child" tail is a no-op for
    ``FragmentSpreadNode`` children because ``_child_selections``
    returns ``()`` for them, so the duplicate recursion is harmless
    rather than worth a special-case branch.
    """
    for child in _child_selections(node):
        frag_def = _unvisited_fragment_definition(child, fragments, visited_fragments)
        if frag_def is not None:
            reachable.append(frag_def)
            _walk_reachable_fragment_definitions(
                frag_def,
                fragments,
                visited_fragments,
                reachable,
            )
        _walk_reachable_fragment_definitions(child, fragments, visited_fragments, reachable)


def _print_operation_with_reachable_fragments(operation: Any, fragments: dict[str, Any]) -> str:
    """Render the plan-cache document key.

    Concatenates ``print_ast(operation)`` with the printed AST of
    every fragment definition reachable from the operation, joined by
    newlines. This is the load-bearing distinction from a bare
    ``print_ast(operation)``: two operations with identical bodies
    but different reachable fragment bodies render to different
    strings, so they no longer share a cached plan that was built for
    the wrong fragment shape. Order is deterministic (selection-set
    order with a visited guard), so the same operation + fragments
    always produce the same string and the cache key is stable across
    requests.
    """
    parts = [print_ast(operation)]
    parts.extend(
        print_ast(fragment)
        for fragment in _collect_reachable_fragment_definitions(operation, fragments)
    )
    return "\n".join(parts)


_MAX_DOC_KEY_CACHE_SIZE = 256

# Cross-request memo for the two document-derived cache-key ingredients - the
# rendered document key AND the cache-relevant variable-NAME frozenset - keyed by
# the operation's raw source text plus its name. Both values are pure functions
# of the document text: two requests with byte-identical document text parse to
# structurally identical ASTs, so the printed key and the ``@skip``/``@include``
# plus nested-pagination name set are identical. Caching them together means a
# hot query neither ``print_ast``s NOR re-walks its full operation AST
# (``_collect_cache_relevant_var_names`` was the last remaining per-request AST
# descent on the plan-cache-hit path) after first sight. The per-execution
# ``_cache_key_parts_cache`` only dedupes within ONE request (keyed on
# ``id(operation)``); this module-level LRU carries the far more valuable
# cross-request reuse. Correctness-neutral under concurrency exactly like
# ``_plan_cache`` - the cached value is deterministic, so a dropped or double
# insert only changes hit rate. Bounded LRU so a long-lived process with many
# distinct documents does not grow without limit.
_doc_key_cache: "OrderedDict[tuple[str, str | None], tuple[str, frozenset[str]]]" = OrderedDict()


def _doc_cache_entry(operation: Any, fragments: dict[str, Any]) -> tuple[str, frozenset[str]]:
    """Return ``(doc_key, cache_relevant_var_names)``, memoized cross-request by source text.

    Keys on ``(operation.loc.source.body, operation_name)``: the source body is
    the WHOLE document text (every operation and fragment definition), so any
    difference in a reachable fragment body is already reflected in it, and the
    operation name disambiguates the operations of a multi-operation document
    (which share one body). Falls back to computing directly - never caching -
    for a programmatically built AST that carries no source ``loc`` (the cache
    would have no stable text key); the per-execution ``id(operation)`` memo in
    ``_build_cache_key`` still dedupes those within one execution.

    ``_collect_cache_relevant_var_names`` is called through the module global
    (not captured) so a test spy patched onto the module still intercepts the
    miss-path collection.
    """
    loc = getattr(operation, "loc", None)
    source = getattr(loc, "source", None)
    body = getattr(source, "body", None)
    if body is None:
        return (
            _print_operation_with_reachable_fragments(operation, fragments),
            _collect_cache_relevant_var_names(operation, fragments),
        )
    name_node = getattr(operation, "name", None)
    key = (body, getattr(name_node, "value", None))
    cached = _doc_key_cache.get(key)
    if cached is not None:
        # ``move_to_end`` is the LRU promotion; guard the concurrent-eviction
        # race the same way the plan cache does (one module cache is shared
        # across all extension instances and threads).
        with suppress(KeyError):
            _doc_key_cache.move_to_end(key)
        return cached
    entry = (
        _print_operation_with_reachable_fragments(operation, fragments),
        _collect_cache_relevant_var_names(operation, fragments),
    )
    _doc_key_cache[key] = entry
    if len(_doc_key_cache) > _MAX_DOC_KEY_CACHE_SIZE:
        with suppress(KeyError):
            _doc_key_cache.popitem(last=False)
    return entry


SelectionExtractor = Callable[[list[Any], Any], list[Any]]


def _root_child_selections(selections: list[Any], info: Any) -> list[Any]:  # noqa: ARG001
    """Flatten children from every converted root field node.

    GraphQL merges repeated root fields with the same response key
    into one resolver call but exposes every contributing ``FieldNode``
    in ``info.field_nodes``. After ``convert_selections``, the returned
    list has one entry per field node, and the walker needs the union
    of their children. The previous shape (``selections[0].selections``)
    silently dropped relations selected by the second node, so
    ``{ allItems { name } allItems { category { name } } }`` would
    skip planning ``category``. The walker's existing alias merging
    (``_merge_aliased_selections``) deduplicates within the flattened
    list, so the order in which we flatten does not matter for plan
    correctness.
    """
    children: list[Any] = []
    for selection in selections:
        children.extend(selection.selections)
    return children


def _connection_node_child_selections(selections: list[Any], info: Any) -> list[Any]:
    """Return node-level selections from a Relay connection wrapper.

    Connection resolvers optimize the pre-slice node queryset, so the ORM walker
    must see the same child selection list it would receive for a list field over
    the node type. The GraphQL runtime path still includes ``edges`` and
    ``node``, though, so node children carry selection-specific prefixes for
    strictness and FK-id-elision resolver keys.
    """
    node_children: list[Any] = []
    root_path = runtime_path_from_info(info)
    for connection_selection in selections:
        for edge_selection in _named_children(connection_selection, "edges"):
            edge_path = (*root_path, _response_key(edge_selection))
            for node_selection in _named_children(edge_selection, "node"):
                node_path = (*edge_path, _response_key(node_selection))
                node_children.extend(
                    _node_children_with_runtime_prefix(
                        node_selection,
                        runtime_prefixes=(node_path,),
                    ),
                )
    return node_children


def mutation_payload_child_selections(slot: str) -> SelectionExtractor:
    """Build a selection extractor for a mutation payload's object slot (spec-036 Decision 9).

    A mutation field returns ``<field> { <slot> { ...children } errors { ... } }``
    where ``<slot>`` is ``node`` (Relay-Node target) or ``result`` (non-Node). The
    post-write re-fetch must plan the SAME child-selection list a list field over
    the node type would, so the walker sees the response selection rooted at the
    node type - exactly the connection extractor's job, but navigating one
    ``<slot>`` level instead of ``edges { node }``. Returns a closure over ``slot``
    so the resolver passes ``mutation_payload_child_selections(slot)`` to
    ``apply_connection_optimization``.
    """

    def _extract(selections: list[Any], info: Any) -> list[Any]:
        node_children: list[Any] = []
        root_path = runtime_path_from_info(info)
        for field_selection in selections:
            for slot_selection in _named_children(field_selection, slot):
                slot_path = (*root_path, _response_key(slot_selection))
                node_children.extend(
                    _node_children_with_runtime_prefix(
                        slot_selection,
                        runtime_prefixes=(slot_path,),
                    ),
                )
        return node_children

    return _extract


class CacheInfo(NamedTuple):
    """Plan-cache statistics (hits, misses, current size)."""

    hits: int
    misses: int
    size: int


_optimizer_active: ContextVar[bool] = ContextVar(
    "django_strawberry_framework_optimizer_active",
    default=False,
)


# The active ``DjangoOptimizerExtension`` instance for the operation's
# lifetime, published by ``on_execute`` so the connection field's
# ``apply_connection_optimization`` helper can discover it and SHARE the
# instance-bound plan cache (Decision 11). ``None`` (the default) means
# either no optimizer is installed for this execution or the helper is being
# called outside an ``on_execute`` lifecycle; the helper then falls back to a
# cache-less plan build + apply, which is correctness-safe (the plan cache is
# a hit-rate optimization, not a correctness requirement - see
# ``DjangoOptimizerExtension.cache_info``).
_active_optimizer: "ContextVar[DjangoOptimizerExtension | None]" = ContextVar(
    "django_strawberry_framework_active_optimizer",
    default=None,
)


# Per-execution memo for the operation-constant cache-key PARTS: the rendered
# document key plus the fully RESOLVED ``(name, value)`` variable frozenset,
# keyed by ``id(operation)``.  Both are constants within one execution (the
# document and ``info.variable_values`` are fixed for the operation), so a
# nested fallback connection pipeline that calls ``apply_connection_optimization``
# -> ``_build_cache_key`` once per parent row pays one dict hit per row instead
# of re-walking the operation AST and rebuilding the value frozenset.  Reusing
# ONE frozenset object across rows also means its hash is computed once
# (``frozenset`` memoizes its hash), so the per-row ``_plan_cache`` key hash
# stays cheap.  This merges the formerly separate printed-AST and
# variable-names memos: both were consulted on every ``_build_cache_key`` call
# with the same ``id(operation)`` key, so keeping them apart bought nothing but
# a second ``ContextVar`` read + dict get per row.  Same per-execution
# ``ContextVar`` lifecycle as the plan memo below: set to an empty dict in
# ``on_execute`` and reset on the way out, ``None`` (the default) when
# ``_build_cache_key`` is called outside an ``on_execute`` lifecycle so the
# lookup falls back to recomputing -- Decision 7.
_cache_key_parts_cache: ContextVar[dict[int, tuple[str, frozenset[tuple[str, Any]]]] | None] = (
    ContextVar(
        "django_strawberry_framework_optimizer_cache_key_parts_cache",
        default=None,
    )
)


# Per-execution memo for BUILT plans, keyed by the same tuple as ``_plan_cache``.
# Its job is the plans the cross-request ``_plan_cache`` deliberately refuses:
# ``cacheable = False`` plans (those baking a request-scoped ``get_queryset``
# queryset or a consumer ``Prefetch`` hint). A nested FALLBACK connection pipeline
# calls ``apply_connection_optimization`` -> ``_get_or_build_plan`` once per parent
# row with an IDENTICAL cache key (``runtime_path_from_info`` strips list indices,
# so every parent shares one key), and because those plans are uncacheable the
# cross-request cache never serves them - so without this memo each parent row
# re-ran the full walker pass (and rebuilt the child queryset). Reusing the plan
# built earlier in THIS execution collapses those N per-parent walks to one. Safe
# because one execution has a single fixed ``info.context``, so a request-scoped
# ``get_queryset`` baked into the plan filters identically for every parent (the
# same reason a list field's single root walk reuses one child queryset across
# all parents). Same per-execution ``ContextVar`` lifecycle as the memos above:
# set to an empty dict in ``on_execute``, reset on the way out; ``None`` (the
# default) outside an ``on_execute`` lifecycle disables the memo entirely, so
# direct / test callers of ``_get_or_build_plan`` see unchanged behavior.
_execution_plan_cache: ContextVar[dict[Any, Any] | None] = ContextVar(
    "django_strawberry_framework_optimizer_execution_plan_cache",
    default=None,
)


def _strawberry_schema_from_schema(schema: Any) -> Any:
    """Unwrap a Strawberry Schema to its inner schema; return ``schema`` if already unwrapped.

    Centralizes the brittle Strawberry-private ``_strawberry_schema``
    contract.  Test fixtures sometimes pass the inner schema directly,
    so the fallback is the input itself.
    """
    return getattr(schema, "_strawberry_schema", schema)


def _strawberry_schema_from_info(info: Any) -> Any | None:
    """Walk ``info.schema._strawberry_schema``; return ``None`` if any step is missing.

    Centralizes the brittle Strawberry-private ``_strawberry_schema``
    contract for the resolver-info path.  Caller treats ``None`` as
    "no schema available, nothing to look up."
    """
    return getattr(getattr(info, "schema", None), "_strawberry_schema", None)


def _collect_schema_reachable_types(schema: Any) -> set[type]:
    """Return the set of ``DjangoType`` classes reachable from the schema's root types.

    Traverses from ``query_type``, ``mutation_type``, and
    ``subscription_type`` through their field return types recursively,
    descending into object fields, union members, and the concrete
    implementations of any interface type encountered (so a
    ``DjangoType`` reachable only via an interface-typed root field -
    e.g. ``relay.Node`` implementers - still participates in the
    ``check_schema`` audit).  Only types reachable from a root
    operation are included; orphan types passed via ``types=[]`` at
    schema construction are excluded to avoid false-positive audit
    warnings.
    """
    reachable: set[type] = set()
    gql_schema = getattr(schema, "_schema", None)
    if gql_schema is None:
        return reachable
    strawberry_schema = _strawberry_schema_from_schema(schema)
    visited_type_names: set[str] = set()

    def _walk_gql_type(gql_type: Any) -> None:
        """Recursively collect DjangoType origins from a graphql-core type."""
        gql_type = unwrap_graphql_type(gql_type)
        type_name = getattr(gql_type, "name", None)
        if type_name is None or type_name in visited_type_names:
            return
        visited_type_names.add(type_name)
        # Check if this type is a DjangoType.
        definition = (
            strawberry_schema.get_type_by_name(type_name)
            if hasattr(strawberry_schema, "get_type_by_name")
            else None
        )
        if definition is not None:
            origin = getattr(definition, "origin", None)
            if origin is not None and registry.get_definition(origin) is not None:
                reachable.add(origin)
        # Recurse into fields.
        fields = getattr(gql_type, "fields", None)
        if fields is not None:
            for field_obj in fields.values():
                _walk_gql_type(getattr(field_obj, "type", None))

        # Recurse into union types.
        union_types = getattr(gql_type, "types", None)
        if union_types is not None:
            for u_type in union_types:
                _walk_gql_type(u_type)

        # Recurse into interface implementations so a ``DjangoType``
        # reachable only via an interface-typed root field still
        # participates in the audit. graphql-core 3.x exposes
        # ``schema.get_implementations(interface_type) -> InterfaceImplementations``
        # with an ``.objects`` tuple of concrete implementers. The
        # ``hasattr`` guard keeps the call safe across graphql-core
        # versions.
        if isinstance(gql_type, GraphQLInterfaceType) and hasattr(
            gql_schema,
            "get_implementations",
        ):
            impls = gql_schema.get_implementations(gql_type)
            impl_objects = getattr(impls, "objects", None)
            if impl_objects is not None:
                for impl_type in impl_objects:
                    _walk_gql_type(impl_type)

    for root_type in (
        gql_schema.query_type,
        gql_schema.mutation_type,
        gql_schema.subscription_type,
    ):
        if root_type is not None:
            _walk_gql_type(root_type)
    return reachable


class _OriginAndModel(NamedTuple):
    """Pair of resolved Strawberry origin type and underlying Django model.

    Returned by :func:`_resolve_model_from_return_type` so the extension's
    ``_optimize`` hook can feed the origin into ``_get_or_build_plan``
    (for root field-map lookup and plan-cache identity) while still
    using the model for the walker's root-level relation traversal.

    Pair-or-``None`` contract: the helper returns ``None`` whenever
    EITHER origin or model is unresolvable; the pair is returned ONLY
    when both are resolved. Callers branch on ``resolved is None``
    rather than dereferencing individual legs.
    """

    origin: type
    model: type[models.Model]


def _resolve_model_from_return_type(info: Any) -> _OriginAndModel | None:
    """Trace ``info.return_type`` through graphql-core wrappers to ``(origin, model)``.

    graphql-core wraps resolver return types in layers of
    ``GraphQLNonNull`` and ``GraphQLList``. This function recursively
    peels ``.of_type`` until it reaches a leaf carrying a ``.name``
    attribute (a ``GraphQLObjectType``), then looks up the corresponding
    Strawberry type definition via the schema and reverse-maps to the
    Django model through the registry.

    Returns ``None`` when any step fails (non-object leaf, missing
    schema backref, missing schema type, unregistered origin). The
    caller treats ``None`` as "nothing to optimize" and passes the
    queryset through unchanged.
    """
    rt = unwrap_graphql_type(info.return_type)
    type_name = getattr(rt, "name", None)
    if type_name is None:
        return None
    strawberry_schema = _strawberry_schema_from_info(info)
    if strawberry_schema is None:
        return None
    definition = strawberry_schema.get_type_by_name(type_name)
    if definition is None:
        return None
    origin = getattr(definition, "origin", None)
    if origin is None:
        return None
    model = registry.model_for_type(origin)
    if model is None:
        return None
    return _OriginAndModel(origin=origin, model=model)


class DjangoOptimizerExtension(SchemaExtension):
    """Strawberry schema extension that optimizes Django querysets per request.

    Pass a module-level singleton wrapped in a factory - that preserves
    the instance-bound plan cache (Strawberry runs the callable per
    request and gets the same instance back) and emits no deprecation
    warning (the entry is a callable, not an instance)::

        _optimizer = DjangoOptimizerExtension()
        schema = strawberry.Schema(
            query=Query,
            extensions=[lambda: _optimizer],  # singleton wrapped in a factory
        )

    The plan cache is correctness-safe under concurrent / async access
    (a missed insert or a double-evict only reduces hit rate; it cannot
    return wrong data), but the hit-rate and counter introspection
    exposed via ``cache_info()`` is best-effort - see ``cache_info``
    for the full caveat.

    Hooks:

    - ``on_execute`` - sets a ``ContextVar`` marking the optimizer as
      active for the operation's lifetime.
    - ``resolve`` - gates on ``info.path.prev is None`` (root resolver
      only). Calls ``_next``, checks ``isinstance(QuerySet)``, traces
      the Django model from the graphql-core return type, runs the O2
      walker, applies the plan.

    Resolver-shape contract: a root resolver that returns a Django
    ``Manager`` (e.g. ``Model.objects`` shorthand) is coerced to a
    ``QuerySet`` via ``.all()`` before the ``isinstance(QuerySet)`` gate
    in ``_optimize``, so the optimizer is applied uniformly whether the
    consumer wrote ``Model.objects`` or ``Model.objects.all()``.
    """

    def __init__(
        self,
        strictness: str = "off",
        *,
        execution_context: Any = None,
        nested_connection_strategy: Any = None,
    ) -> None:
        # ``execution_context`` stays accepted for direct-construction
        # compatibility only: at the ``strawberry-graphql>=0.316.0`` floor the
        # engine invokes class/factory entries in ``extensions=[...]`` with
        # ZERO arguments and assigns ``extension.execution_context`` afterward,
        # so Strawberry itself never passes this keyword (spec-044 Decision 6
        # migration notes). Unknown consumer kwargs still raise ``TypeError``
        # at construction so typos (``strict=True``) surface at the call site
        # rather than being silently absorbed.
        super().__init__(execution_context=execution_context)
        if strictness not in ("off", "warn", "raise"):
            msg = f"strictness must be 'off', 'warn', or 'raise', got {strictness!r}"
            raise ValueError(msg)
        self.strictness = strictness
        # The nested-connection fetch strategy is fixed per extension INSTANCE
        # at construction (``None`` reads the ``NESTED_CONNECTION_STRATEGY``
        # setting, defaulting to windowed). The plan cache below is
        # instance-bound, so pinning the strategy here guarantees one cache
        # never mixes plans from two strategies. ``"auto"`` itself is one
        # backend-neutral strategy whose lateral-capable windowed queryset
        # selects by its fetch-time alias (``optimizer/nested_fetch.py``);
        # cached plans therefore remain valid across router decisions. Unknown
        # names raise ``ConfigurationError`` at construction, not at query time.
        self.nested_connection_strategy = resolve_strategy(nested_connection_strategy)
        self._plan_cache: OrderedDict[
            tuple[str, frozenset[tuple[str, Any]], type, tuple[str, ...], type | None],
            Any,
        ] = OrderedDict()
        self._cache_hits = 0
        self._cache_misses = 0

    def cache_info(self) -> CacheInfo:
        """Return plan-cache statistics (hits, misses, current size).

        The extension instance is shared across requests, and the plan
        cache and counters are mutated without a lock. Under concurrent
        or async access the hit/miss counters and the reported ``size``
        are best-effort: two threads racing ``+= 1`` can drop a count,
        and two concurrent inserts at the eviction threshold can evict
        twice. The cache itself is correctness-neutral - a missed insert
        or a double-evict only reduces hit rate; it cannot return wrong
        data.
        """
        return CacheInfo(
            hits=self._cache_hits,
            misses=self._cache_misses,
            size=len(self._plan_cache),
        )

    def on_execute(self) -> Any:  # type: ignore[override]
        """Mark the optimizer as active and seed the per-execution AST memo."""
        # Drop any optimizer stashes left on a reused ``context_value`` before
        # this operation publishes. ``_stash_union`` is intentionally
        # accumulative *within* one execution (parent + nested connection);
        # without a start-of-execution clear, sequential ``execute_sync``
        # calls sharing one context object leak FK-id elisions (wrong stub
        # data) and planned-resolver keys (masked N+1 under strictness).
        # ``execution_context.context`` is the same object resolvers see as
        # ``info.context`` (Strawberry wires both to ``context_value``).
        # ``getattr(self, "execution_context", None)`` covers direct/test
        # callers that invoke ``on_execute`` before Strawberry assigns the
        # execution context (the engine sets it after constructing the
        # extension entry).
        execution_context = getattr(self, "execution_context", None)
        _clear_optimizer_context(getattr(execution_context, "context", None))
        active_token = _optimizer_active.set(True)
        # Publish this instance so ``apply_connection_optimization`` can
        # discover it and share the instance-bound plan cache (Decision 11).
        instance_token = _active_optimizer.set(self)
        # Publish the instance's nested-connection fetch strategy for the
        # walker (which cannot import this module - the dependency points the
        # other way; see ``nested_fetch.py::active_strategy``).
        strategy_token = _active_nested_strategy.set(self.nested_connection_strategy)
        key_parts_token = _cache_key_parts_cache.set({})
        plan_memo_token = _execution_plan_cache.set({})
        converted_token = converted_selections_cache.set({})
        try:
            yield
        finally:
            converted_selections_cache.reset(converted_token)
            _execution_plan_cache.reset(plan_memo_token)
            _cache_key_parts_cache.reset(key_parts_token)
            _active_nested_strategy.reset(strategy_token)
            _active_optimizer.reset(instance_token)
            _optimizer_active.reset(active_token)

    def resolve(
        self,
        _next: Any,
        root: Any,
        info: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Root-gated resolver hook.

        Only root-level resolvers (``info.path.prev is None``) trigger
        the optimization pass. All other resolvers pass through
        unchanged - the prefetch chain applied at the root handles
        nested relations via Django's ``__``-chain support.

        Handles both sync and async resolvers: when ``_next`` returns a
        coroutine (async resolver), returns an async wrapper that awaits
        the result before running ``_optimize``. Strawberry's
        ``SchemaExtension.resolve`` returns ``AwaitableOrValue`` for
        exactly this reason.
        """
        result = _next(root, info, *args, **kwargs)
        if info.path.prev is not None:
            return result
        if inspect.isawaitable(result):

            async def _async_optimize() -> Any:
                return self._optimize(await result, info)

            return _async_optimize()
        return self._optimize(result, info)

    def _optimize(self, result: Any, info: Any) -> Any:
        """Apply the O2 walker's plan to a root-level ``QuerySet`` (middleware path).

        Steps:

        1. ``Manager`` results are coerced via ``.all()`` so a resolver
           returning ``Model.objects`` (the Django shorthand) is
           optimized instead of being silently passed through. The
           manager's ``.all()`` returns a fresh unevaluated ``QuerySet``;
           no rows are fetched at this step.
        2. Non-``QuerySet`` results pass through unchanged.

           Steps 1-2 are the shared ``utils/querysets.py::normalize_query_source``
           contract - the same Manager-coercion + is-queryset decision the
           list / connection field consumer paths use, so the middleware never
           decides it independently (``docs/feedback.md`` Major 1).
        3. An already-evaluated queryset (``_result_cache`` populated) is
           returned unchanged (G1, ``spec-035`` Decision 3). The consumer's
           root resolver already ran the SQL (a ``len(qs)`` guard, a
           ``bool(qs)`` branch, a slice for a log line); past this point
           :meth:`apply_to` clones the queryset to attach ``.only()`` /
           ``select_related``, and a clone of an evaluated queryset silently
           re-executes that SQL - a doubled query invisible to the consumer.
           This extends the B8 "respect what the consumer already did" posture
           from optimization state to execution state.
        4. Trace the graphql-core return type to a Django ``(origin, model)``.
        5. Delegate the plan-build-and-apply tail to :meth:`apply_to`, passing
           the resolved ``origin`` / ``model`` explicitly - the SAME helper
           the connection field's ``apply_connection_optimization`` calls, so
           the two share one plan-application implementation (Decision 11).
           The middleware path is behavior-identical: ``_optimize`` only adds
           the return-type resolution the connection field does NOT need
           (the connection field's return type is the connection type, not the
           node type).
        """
        result, is_queryset = normalize_query_source(result)
        if not is_queryset:
            return result
        # G1 (spec-035 Decision 3): a consumer-evaluated root queryset passes
        # through unchanged. Placement is load-bearing in both directions - it
        # sits AFTER the Manager coercion (a coerced ``.all()`` is always a
        # fresh unevaluated queryset, so a ``Model.objects``-returning resolver
        # still optimizes) and BEFORE the return-type resolution / ``apply_to``
        # clone (which would re-execute the SQL). ``is not None`` is the exact,
        # allocation-free signal upstream uses: ``_result_cache`` is ``None``
        # until evaluated and a (possibly empty) list after, so truthiness would
        # mis-handle an evaluated-but-empty queryset. ``getattr`` is defensive
        # per the package posture - a non-queryset that slipped the gate above
        # simply lacks the attribute and falls through.
        if getattr(result, "_result_cache", None) is not None:
            return result
        resolved = _resolve_model_from_return_type(info)
        if resolved is None:
            logger.debug(
                "Optimizer: return type for %s has no registered DjangoType; "
                "passing queryset through unchanged.",
                info.field_name,
            )
            return result
        return self.apply_to(resolved.origin, resolved.model, result, info)

    def apply_to(
        self,
        target_type: type | None,
        target_model: type,
        queryset: models.QuerySet,
        info: Any,
        *,
        selection_extractor: SelectionExtractor = _root_child_selections,
    ) -> models.QuerySet:
        """Build and apply the O2 plan to ``queryset`` given ``target_type`` / ``target_model``.

        The plan-build-and-apply tail extracted from ``_optimize`` (Decision
        11). Takes the node type / model **directly** rather than inferring
        them from ``info.return_type`` - the connection field's root return
        type is the connection type, not the node type, so the inference the
        middleware path uses would resolve the wrong model.

        Steps:

        1. Build (or fetch from cache) an ``OptimizationPlan`` via
           ``_get_or_build_plan`` (passing ``target_type`` as ``origin`` so
           plans cache-separate by node type exactly as middleware plans do).
        2. Publish the plan + strictness sentinels to ``info.context`` via
           ``_publish_plan_to_context``.
        3. Reconcile against the consumer's existing queryset optimizations
           and apply.

        Returns ``queryset`` unchanged when there are no root field nodes or
        the plan is empty.
        """
        if not info.field_nodes:
            return queryset

        # The O2 walker expects the children of the root field, so we build
        # the Strawberry-shaped selection list from ``field_nodes`` via the
        # package-owned ``ast_to_converted_selections`` adapter rather than
        # Strawberry's ``convert_selections``: the latter's
        # ``InlineFragment.from_node`` reads ``type_condition.name.value`` and
        # crashes on a valid anonymous inline fragment (``... { f }``,
        # ``type_condition=None``). The adapter mirrors the conversion but
        # builds a ``type_condition=None`` shell the fragment-aware substrate
        # in ``selections.py`` flows through unchanged.
        #
        # Deferred behind a thunk: the conversion + extraction allocate a
        # per-node ``SelectedField`` tree (with ``convert_arguments`` /
        # ``convert_directives``), yet on a plan-cache HIT - the steady-state
        # production path - that list is used for nothing. ``_get_or_build_plan``
        # invokes the thunk ONLY when it actually has to build a plan, so a cache
        # hit never pays the conversion.
        def _node_selections() -> list[Any]:
            selections = ast_to_converted_selections(info, info.field_nodes)
            return selection_extractor(selections, info)

        plan = self._get_or_build_plan(
            _node_selections,
            target_model,
            info,
            target_type,
        )
        # B8 pre-publish prune: a consumer projection - an ``.only`` or
        # ``.defer`` call on the returned queryset - can make a planned
        # ``select_related`` path Django-invalid (a field cannot be both
        # deferred and traversed). The prune drops those paths AND their
        # resolver keys so strictness accounts for the relation as the
        # per-row fallback it now is. Same-object return on the common
        # no-projection shape; the cached plan is never mutated.
        plan = prune_unsupportable_select_related(plan, queryset)
        # B8: reconcile against consumer queryset optimizations BEFORE
        # publishing sentinels. Consumer-wins prefetch drops must strip
        # coupled ``planned_resolver_keys`` / FK-id elisions (via
        # ``prefetch_path_resolver_keys``) before ``_publish_plan_to_context``;
        # publishing first left nested N+1s masked under strictness.
        # Returns a fresh plan and (when an upgrade was applied) a
        # rewritten queryset; B1's cached plan is never mutated.
        if not plan.is_empty:
            plan, queryset = diff_plan_for_queryset(plan, queryset)
        self._publish_plan_to_context(plan, info)
        if plan.is_empty:
            return queryset
        return plan.apply(queryset)

    def _get_or_build_plan(
        self,
        selections: "list[Any] | Callable[[], list[Any]]",
        target_model: type,
        info: Any,
        origin: type | None,
    ) -> Any:
        """Return the cached plan for ``(info, target_model, origin)`` or build a new one.

        B1: plan cache.  Cache hits increment ``_cache_hits`` and refresh
        recency; misses run the walker, evict the least-recently-used quarter
        when full, insert iff the plan is ``cacheable``, and increment
        ``_cache_misses``.

        ``selections`` is either the converted selection list or a zero-arg
        callable that produces it. The callable form lets the caller defer the
        AST -> converted-selection conversion until a build is actually needed,
        so a cache hit never pays for it; it is invoked at most once, only on the
        build path. Direct/test callers may still pass a plain list.

        A second, per-execution memo (``_execution_plan_cache``) sits between the
        cross-request cache and the walker for ``cacheable = False`` plans: those
        never enter ``_plan_cache``, so a nested fallback connection pipeline that
        calls this once per parent row (identical cache key each time) would
        otherwise rebuild the same plan for every parent. An intra-execution memo
        hit reuses that plan and does NOT touch the ``_cache_hits`` /
        ``_cache_misses`` counters - those stay a report on the cross-request
        instance cache alone (``cache_info``); the miss counter therefore counts
        actual walker builds, one per distinct plan per execution.

        ``origin`` carries the resolver's actual Strawberry return type
        so primary-return and secondary-return resolvers on the same
        model do not share a cached plan. The extension's ``_plan_cache``
        is root-only - this helper is the sole insertion site, so
        ``origin`` always receives the concrete root origin in
        production; ``None`` is reserved for direct/test-only callers
        that deliberately build a plan without an origin.
        """
        cache_key = self._build_cache_key(info, target_model, origin)
        cached_plan = self._plan_cache.get(cache_key)
        if cached_plan is not None:
            # ``move_to_end`` is the LRU promotion. Guard the rare race where a
            # concurrent request's eviction sweep drops this key between the
            # ``get`` above and here (one extension instance is shared across an
            # ASGI/threaded execution). A lost promotion is harmless - the plan
            # we already hold is still the correct, cacheable plan. The
            # ``suppress`` context-manager overhead is once-per-request
            # (root-only cache), not per-row, so it stays off the row-scaled
            # hot path.
            with suppress(KeyError):
                self._plan_cache.move_to_end(cache_key)
            self._cache_hits += 1
            return cached_plan
        # Per-execution reuse of an uncacheable plan already built this execution
        # (the nested-fallback per-parent-row case). ``None`` outside an
        # ``on_execute`` lifecycle, so direct/test callers skip this entirely.
        exec_memo = _execution_plan_cache.get()
        if exec_memo is not None:
            memoized_plan = exec_memo.get(cache_key)
            if memoized_plan is not None:
                return memoized_plan
        # Both caches missed: resolve the selections now (calling the thunk if the
        # caller deferred conversion) and run the walker.
        resolved_selections = selections() if callable(selections) else selections
        plan = plan_optimizations(resolved_selections, target_model, info=info, source_type=origin)
        if plan.cacheable and len(self._plan_cache) >= _MAX_PLAN_CACHE_SIZE:
            # LRU eviction: drop the least-recently-used quarter at once to
            # amortise eviction cost across many subsequent inserts. Cache hits
            # move entries to the most-recent end above, so hot plans survive a
            # sweep even when they were inserted early.
            to_remove = max(1, _MAX_PLAN_CACHE_SIZE // 4)
            for _ in range(min(to_remove, len(self._plan_cache))):
                self._plan_cache.popitem(last=False)
        if plan.cacheable:
            self._plan_cache[cache_key] = plan
        elif exec_memo is not None:
            # Uncacheable across requests, but reusable within THIS execution: a
            # nested fallback connection re-entering per parent row gets the plan
            # (and its already-built child queryset) back instead of re-walking.
            exec_memo[cache_key] = plan
        self._cache_misses += 1
        return plan

    def _publish_plan_to_context(self, plan: Any, info: Any) -> None:
        """Stash the plan and (when strictness is active) the strictness sentinels on ``info.context``.

        B5: introspection stash so consumers and tests can inspect the
        optimizer's decisions.  B3: when ``strictness != "off"``, also
        stash the planned-resolver sentinel set, the lookup paths, and
        the strictness mode so per-relation resolvers can detect
        unplanned lazy loads.
        """
        # UNION the correctness sentinels into any existing frozenset stash
        # rather than overwriting (spec-033 Decision 8). Nested FALLBACK
        # connection pipelines are real optimizer runs that re-enter this
        # publish per parent; they must NOT destroy the parent plan's
        # planned / FK-id-elision / lookup-path sets (especially under
        # ``"warn"``, where execution continues after the nested connection
        # returns). Resolver keys and FK-id-elision keys embed runtime paths, so
        # parent and nested-connection plans coexist without collision.
        # ``DST_OPTIMIZER_PLAN`` stays LAST-WINS introspection data (not a
        # correctness sentinel - do not union it).
        _stash_on_context(info.context, DST_OPTIMIZER_PLAN, plan)
        fk_id_elisions = plan.finalized_fk_id_elisions
        if fk_id_elisions is None:
            fk_id_elisions = frozenset(plan.fk_id_elisions)
        self._stash_union(info.context, DST_OPTIMIZER_FK_ID_ELISIONS, fk_id_elisions)
        if self.strictness != "off":
            planned_resolver_keys = plan.finalized_planned_resolver_keys
            if planned_resolver_keys is None:
                planned_resolver_keys = frozenset(plan.planned_resolver_keys)
            plan_lookup_paths = plan.finalized_lookup_paths
            if plan_lookup_paths is None:
                plan_lookup_paths = frozenset(lookup_paths(plan))
            self._stash_union(info.context, DST_OPTIMIZER_PLANNED, planned_resolver_keys)
            self._stash_union(info.context, DST_OPTIMIZER_LOOKUP_PATHS, plan_lookup_paths)
            _stash_on_context(info.context, DST_OPTIMIZER_STRICTNESS, self.strictness)

    @staticmethod
    def _stash_union(context: Any, key: str, new: frozenset) -> None:
        """Stash ``new`` unioned with any existing frozenset under ``key``.

        Reads the current stash via the read-side ``get_context_value`` helper
        and unions it with ``new`` when the existing value is a ``frozenset`` /
        ``set``; otherwise stashes ``new`` alone (defensive: a non-set existing
        value, the empty/absent case, matches the file's defensive-coerce
        stance). This is the foundation that lets a nested fallback connection
        pipeline's publish coexist with the parent's planned set rather than
        overwriting it (spec-033 Decision 8).
        """
        existing = _get_context_value(context, key)
        if isinstance(existing, (frozenset, set)):
            # Subset early-out: a nested fallback connection re-publishes the
            # SAME plan once per parent row, so after the first row ``new`` is
            # already contained in the stash. Skipping the union avoids
            # reallocating a growing frozenset per row - membership is
            # observably identical either way.
            if new <= existing:
                return
            merged = existing | new
        else:
            merged = new
        _stash_on_context(context, key, merged)

    @staticmethod
    def check_schema(schema: Any) -> list[str]:
        """Audit schema-reachable types for unoptimized relations.

        Walks only the ``DjangoType``s reachable from the schema's root
        types (not the entire registry) and checks each **exposed**
        relation field (i.e., present in its registered definition's
        field map, not hidden by ``Meta.fields``/``Meta.exclude`` or
        ``OptimizerHint.SKIP``). Returns a list of warning strings for
        relations whose target model has no registered ``DjangoType``.

        Always returns warnings - never raises. The caller decides
        whether to raise based on the extension's ``strictness``.
        """
        reachable = _collect_schema_reachable_types(schema)
        # Dedupe (source_model, field_name) so multi-type models do not
        # double-warn: registry.iter_types() yields one entry per registered
        # type after spec-018 Slice 1, so a model with multiple types whose
        # field maps overlap on the same unregistered-target relation would
        # otherwise produce one identical warning per registered type. The
        # dedupe is a multi-type artifact, not generic defensiveness - every
        # reachable type is still audited (we cannot skip secondaries, since
        # a secondary may expose a relation the primary hides).
        seen: set[tuple[type[models.Model], str]] = set()
        warnings: list[str] = []
        for _model, type_cls in registry.iter_types():
            if type_cls not in reachable:
                continue
            definition = registry.get_definition(type_cls)
            if definition is None:
                continue
            field_map = definition.field_map
            hints = definition.optimizer_hints or {}
            for field_name, meta in field_map.items():
                if not meta.is_relation:
                    continue
                # Skip fields opted out via OptimizerHint.SKIP.
                if hint_is_skip(hints.get(field_name)):
                    continue
                if meta.related_model is not None and registry.get(meta.related_model) is None:
                    key = (_model, field_name)
                    if key in seen:
                        continue
                    seen.add(key)
                    warnings.append(
                        f"{type_cls.__name__} ({_model.__name__}.{field_name}) "
                        "has no registered target DjangoType",
                    )
        return warnings

    @staticmethod
    def _build_cache_key(
        info: Any,
        target_model: type[models.Model],
        origin: type | None = None,
    ) -> tuple[str, frozenset[tuple[str, Any]], type, tuple[str, ...], type | None]:
        """Build the plan-cache key from resolver info, target model, and origin type.

        Key components:
        1. The selected operation's printed AST plus the printed definitions
           of any named fragments reachable from it.  ``print_ast(operation)``
           includes the operation name and its own selection set only, so
           reachable fragment definitions are appended to keep same-shaped
           operation bodies with different fragment bodies from sharing a
           plan.  Multi-operation documents (``query A {...} query B {...}``)
           still never collide - using the raw source body would, because
           ``loc.source.body`` is the entire document.  We store the printed
           string (not its ``hash``) to eliminate the rare-but-real chance of
           two distinct document shapes sharing a 64-bit hash and silently
           sharing a cached plan.
        2. Frozenset of ``(var_name, var_value)`` for the variables
           referenced in ``@skip``/``@include`` directives and in
           ``first``/``last``/``before``/``after`` arguments on non-root
           field nodes (nested pagination values are baked into windowed
           prefetch plans by Slice 1, so they must key the cache; root
           pagination variables stay out -- root slicing is post-plan).
        3. The target Django model class (different root fields in the
           same operation can return different models).
        4. The root response path, so multiple root fields returning the
           same model do not share a plan within one operation.
        5. The resolver's origin Strawberry type so primary-return and
           secondary-return resolvers for the same model do not share a
           cached plan. Direct/test-only callers may pass ``None``.
        """
        operation = info.operation
        fragments = info.fragments or {}
        # Memoize the operation-constant key parts per execution: the rendered
        # document key AND the resolved ``(name, value)`` variable frozenset.
        # Many root resolvers in one operation share the same operation node,
        # and a nested fallback connection pipeline calls this once per parent
        # row - both the document rendering and the variable resolution are
        # constants for the operation (``info.variable_values`` is fixed per
        # execution), so one dict hit replaces the AST work and the per-row
        # frozenset rebuild.  On a memo miss the document-derived halves come
        # from the cross-request ``_doc_cache_entry`` LRU (so a hot query pays
        # neither ``print_ast`` nor the variable-name AST walk after first
        # sight); only the value resolution runs per execution.  The memo is a
        # per-execution ``ContextVar`` dict installed by ``on_execute``; if the
        # extension is invoked outside an ``on_execute`` lifecycle (some test
        # fixtures call ``_build_cache_key`` directly), fall back to
        # recomputing -- Decision 7.
        memo = _cache_key_parts_cache.get()
        parts = memo.get(id(operation)) if memo is not None else None
        if parts is None:
            doc_key, relevant_var_names = _doc_cache_entry(operation, fragments)
            variable_values = info.variable_values or {}
            # The name-keyed pagination collector deliberately over-collects, so
            # any GraphQL input shape (including an arbitrary custom-scalar
            # result) can reach this frozenset through a same-named argument on a
            # non-connection field. Normalize every value at the cache boundary.
            relevant_vars = frozenset(
                (k, _hashable_variable_value(variable_values[k]))
                for k in relevant_var_names
                if k in variable_values
            )
            parts = (doc_key, relevant_vars)
            if memo is not None:
                memo[id(operation)] = parts
        doc_key, relevant_vars = parts
        return (
            doc_key,
            relevant_vars,
            target_model,
            runtime_path_from_info(info),
            origin,
        )

    def plan_relation(
        self,
        field: Any,
        target_type: type,
        info: Any,
    ) -> tuple[str, str]:
        """Plan a single relation traversal (O6 entry point).

        Thin instance-method delegate to the module-level ``plan_relation``
        in ``walker.py``.  Kept on the class as a deliberate override seam:
        subclasses can replace per-relation planning without monkey-patching
        the walker module, and tests can swap an instance method for
        custom strategies.

        Returns ``("select", reason)`` or ``("prefetch", reason)`` describing how
        the walker should materialize this relation on the parent queryset.
        """
        return plan_relation(field, target_type, info)


def apply_connection_optimization(
    target_type: type,
    queryset: models.QuerySet,
    info: Any,
    *,
    selection_extractor: SelectionExtractor = _connection_node_child_selections,
) -> models.QuerySet:
    """Apply the optimizer plan to a connection field's pre-slice queryset.

    The connection field's own optimizer cooperation point (Decision 11), also
    reused by the mutation re-fetch (spec-036 Decision 9). Strawberry's
    ``ConnectionExtension`` returns a connection object, so the schema middleware
    (``DjangoOptimizerExtension.resolve``) never sees the pre-slice queryset and
    cannot optimize it; the connection resolver calls this helper as the last
    pipeline step before handing the queryset to ``ConnectionExtension`` for
    slicing.

    Resolves ``target_model`` from ``target_type``'s registered definition
    (NOT from ``info.return_type``, which is the connection type) and delegates
    to ``DjangoOptimizerExtension.apply_to``. The active extension instance is
    discovered from the ``_active_optimizer`` ``ContextVar`` published by
    ``on_execute`` so the connection field shares the instance-bound plan
    cache. When no optimizer extension is installed for this execution (the
    ``ContextVar`` is ``None``), the helper short-circuits and returns the
    queryset unoptimized - the connection field does NOT fabricate a throwaway
    optimizer to self-optimize. This keeps the connection consistent with the
    rest of the schema: the middleware path only optimizes when the extension is
    installed, and connection fields follow the same opt-in contract.

    ``selection_extractor`` defaults to the connection ``edges { node { ... } }``
    navigator; a caller whose response selection nests the node type under a
    different slot passes its own (the mutation re-fetch passes a
    ``<payload>.node`` / ``<payload>.result`` extractor - spec-036 Decision 9), so
    the walker sees the same child-selection list a list field over the node type
    would. ``apply_to`` already accepts the extractor; this helper just forwards
    it instead of hardcoding the connection shape.

    Returns ``queryset`` unchanged when ``target_type`` has no registered
    model (nothing to plan) or when no optimizer extension is installed.
    """
    target_model = registry.model_for_type(target_type)
    if target_model is None:
        return queryset
    optimizer = _active_optimizer.get()
    if optimizer is None:
        return queryset
    # The connection resolver receives Strawberry's wrapped ``Info``; the plan
    # machinery (``_build_cache_key`` / ``convert_selections`` / the
    # ``info.context`` stash) expects the raw graphql-core ``GraphQLResolveInfo``
    # the middleware path uses. ``Info._raw_info`` is that object; the
    # ``getattr`` fallback keeps the helper usable when a caller already passes
    # a raw info (e.g. a direct test).
    raw_info = getattr(info, "_raw_info", info)
    return optimizer.apply_to(
        target_type,
        target_model,
        queryset,
        raw_info,
        selection_extractor=selection_extractor,
    )
