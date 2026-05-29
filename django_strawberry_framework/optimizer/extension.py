"""``DjangoOptimizerExtension`` — Strawberry schema extension solving N+1.

Opt-in at schema construction::

    schema = strawberry.Schema(
        query=Query,
        extensions=[DjangoOptimizerExtension()],
    )

The extension hooks Strawberry's ``resolve`` middleware. At the
operation's **root resolver** (detected via ``info.path.prev is None``)
it walks the entire selection tree once using the O2 walker, builds an
``OptimizationPlan``, and applies ``select_related`` /
``prefetch_related`` to the root queryset. Non-root resolvers pass
through untouched — Django's ``prefetch_related`` with ``__``-chained
paths handles nested optimization in a single pass.

Load-bearing rule (O6): when a related field's target ``DjangoType``
defines a non-default ``get_queryset``, generate a
``Prefetch(...)`` keyed on the filtered queryset instead of a
``select_related``. This is the visibility-leak fix from
strawberry-graphql-django #572 / #583. We copy the behaviour, not the
API.

Architecture modeled on ``strawberry_django/optimizer.py`` — same
root-gate pattern, same ``ContextVar`` lifecycle, same recursive
type-tracing through graphql-core wrappers.
"""

import inspect
from contextvars import ContextVar
from typing import Any, NamedTuple

from django.db import models
from graphql.language.ast import (
    DirectiveNode,
    FragmentSpreadNode,
    VariableNode,
)
from graphql.language.printer import print_ast
from graphql.type.definition import GraphQLInterfaceType
from strawberry.extensions import SchemaExtension

from ..registry import registry
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
    stash_on_context as _stash_on_context,
)
from .hints import hint_is_skip
from .plans import diff_plan_for_queryset, lookup_paths, runtime_path_from_info
from .walker import plan_optimizations, plan_relation

_MAX_PLAN_CACHE_SIZE = 256

# Re-export the stash helper under its original underscore-prefixed name so
# existing tests that import ``from ...extension import _stash_on_context``
# keep working without a churn pass.  Canonical implementation lives in
# ``optimizer/_context.py`` for cross-subpackage reuse with the read-side
# ``get_context_value`` (consumed by ``types/resolvers.py``).
__all__ = (
    "CacheInfo",
    "DjangoOptimizerExtension",
    "_stash_on_context",
)


def _collect_directive_var_names(
    node: Any,
    fragments: dict[str, Any] | None = None,
) -> frozenset[str]:
    """Walk an AST node tree and return variable names used in ``@skip``/``@include``.

    Only variables referenced inside the ``if`` argument of ``@skip`` or
    ``@include`` directives matter for plan caching. All other variables
    (e.g., filter arguments) do not affect the selection tree and must be
    excluded from the cache key to avoid cardinality explosion.

    ``fragments`` is the document's fragment definitions map
    (``info.fragments``). When provided, ``FragmentSpreadNode``
    references are followed into their definitions so directives inside
    named fragments are included in the cache key.
    """
    names: set[str] = set()
    _walk_directives(node, names, fragments or {}, set())
    return frozenset(names)


def _walk_directives(
    node: Any,
    names: set[str],
    fragments: dict[str, Any],
    visited_fragments: set[str],
) -> None:
    """Recursive helper: descend into selections and collect directive var names.

    Handles four AST shapes:
    1. **Directives on the current node** — collect ``@skip``/``@include``
       variable references.
    2. **Selection-set children** — recurse so directives on inner fields
       are collected.
    3. **FragmentSpreadNode children** — also recurse into the named
       fragment's definition (looked up in ``fragments``) so directives
       inside the spread fragment are included in the cache key.
    4. **InlineFragmentNode / regular field children** — handled by the
       same selection-set recursion in shape 2.
    """
    for directive in getattr(node, "directives", ()) or ():
        if not isinstance(directive, DirectiveNode):
            continue
        d_name = directive.name.value if directive.name else None
        if d_name not in ("skip", "include"):
            continue
        for arg in directive.arguments or ():
            if isinstance(arg.value, VariableNode):
                names.add(arg.value.name.value)
    # Recurse into child selections.
    for child in _child_selections(node):
        # Always recurse into the child first so directives attached
        # to the child itself are collected (FragmentSpreadNode has
        # no ``selection_set`` so this is just the directive sweep).
        _walk_directives(child, names, fragments, visited_fragments)
        frag_def = _unvisited_fragment_definition(child, fragments, visited_fragments)
        if frag_def is not None:
            _walk_directives(frag_def, names, fragments, visited_fragments)


def _child_selections(node: Any) -> tuple[Any, ...]:
    """Return the AST node's selection-set children as a tuple, or ``()``.

    Centralizes the ``getattr(node, "selection_set", None)`` plus
    ``selections or ()`` shape so the three AST walkers in this module
    (``_walk_directives``, ``_walk_reachable_fragment_definitions``,
    and by extension ``_collect_reachable_fragment_definitions``) share
    one "iterate children" implementation. ``FragmentSpreadNode`` has
    no ``selection_set``, so this returns ``()`` and the caller's
    per-child loop becomes a no-op.
    """
    selection_set = getattr(node, "selection_set", None)
    if selection_set is None:
        return ()
    return tuple(selection_set.selections or ())


def _unvisited_fragment_definition(
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
    does not define the named fragment (defensive — graphql-core's
    validation would normally reject the operation before the optimizer
    sees it). Mutates ``visited_fragments`` on success so callers share
    the same cycle-detection set across recursive descents in both the
    directive-variable walk and the reachable-fragment walk.
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


def _root_child_selections(selections: list[Any]) -> list[Any]:
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


class CacheInfo(NamedTuple):
    """Plan-cache statistics (hits, misses, current size)."""

    hits: int
    misses: int
    size: int


_optimizer_active: ContextVar[bool] = ContextVar(
    "django_strawberry_framework_optimizer_active",
    default=False,
)


# Per-execution memo for the rendered document key: the selected operation
# plus reachable named fragment definitions.  Set in ``on_execute`` and
# reset on its way out so each execution gets its own dict; the ``ContextVar``
# shape keeps async executions isolated even when they share the same
# extension instance.  ``_build_cache_key`` reads from this dict before
# recomputing, keyed by ``id(operation)``.
_printed_ast_cache: ContextVar[dict[int, str] | None] = ContextVar(
    "django_strawberry_framework_optimizer_printed_ast_cache",
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
    ``DjangoType`` reachable only via an interface-typed root field —
    e.g. ``relay.Node`` implementers — still participates in the
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

    Pass an **instance** (not the bare class) to benefit from plan
    caching in async mode::

        schema = strawberry.Schema(
            query=Query,
            extensions=[DjangoOptimizerExtension()],  # instance!
        )

    The plan cache is correctness-safe under concurrent / async access
    (a missed insert or a double-evict only reduces hit rate; it cannot
    return wrong data), but the hit-rate and counter introspection
    exposed via ``cache_info()`` is best-effort — see ``cache_info``
    for the full caveat.

    Hooks:

    - ``on_execute`` — sets a ``ContextVar`` marking the optimizer as
      active for the operation's lifetime.
    - ``resolve`` — gates on ``info.path.prev is None`` (root resolver
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
    ) -> None:
        # Explicitly accept ``execution_context`` because Strawberry
        # instantiates extension classes with that keyword when an
        # extension *class* (not an instance) is passed in
        # ``extensions=[...]``. Unknown consumer kwargs still raise
        # ``TypeError`` at construction so typos (``strict=True``) surface
        # at the call site rather than being silently absorbed.
        super().__init__(execution_context=execution_context)
        if strictness not in ("off", "warn", "raise"):
            msg = f"strictness must be 'off', 'warn', or 'raise', got {strictness!r}"
            raise ValueError(msg)
        self.strictness = strictness
        self._plan_cache: dict[
            tuple[str, frozenset[tuple[str, Any]], type, tuple[str, ...], type | None],
            Any,
        ] = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def cache_info(self) -> CacheInfo:
        """Return plan-cache statistics (hits, misses, current size).

        The extension instance is shared across requests, and the plan
        cache and counters are mutated without a lock. Under concurrent
        or async access the hit/miss counters and the reported ``size``
        are best-effort: two threads racing ``+= 1`` can drop a count,
        and two concurrent inserts at the eviction threshold can evict
        twice. The cache itself is correctness-neutral — a missed insert
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
        active_token = _optimizer_active.set(True)
        ast_token = _printed_ast_cache.set({})
        try:
            yield
        finally:
            _printed_ast_cache.reset(ast_token)
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
        unchanged — the prefetch chain applied at the root handles
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
        """Apply the O2 walker's plan to a root-level ``QuerySet``.

        Steps:

        1. ``Manager`` results are coerced via ``.all()`` so a resolver
           returning ``Model.objects`` (the Django shorthand) is
           optimized instead of being silently passed through. The
           manager's ``.all()`` returns a fresh unevaluated ``QuerySet``;
           no rows are fetched at this step.
        2. Non-``QuerySet`` results pass through unchanged.
        3. Trace the graphql-core return type to a Django model.
        4. Build (or fetch from cache) an ``OptimizationPlan`` via
           ``_get_or_build_plan``.
        5. Publish the plan + strictness sentinels to ``info.context``
           via ``_publish_plan_to_context``.
        6. Reconcile against the consumer's existing queryset
           optimizations and apply.
        """
        if isinstance(result, models.Manager):
            result = result.all()
        if not isinstance(result, models.QuerySet):
            return result
        resolved = _resolve_model_from_return_type(info)
        if resolved is None:
            logger.debug(
                "Optimizer: return type for %s has no registered DjangoType; "
                "passing queryset through unchanged.",
                info.field_name,
            )
            return result
        origin, target_model = resolved.origin, resolved.model
        if not info.field_nodes:
            return result
        # The O2 walker expects the children of the root field, so we
        # build the Strawberry-shaped selection list from field_nodes
        # via ``convert_selections``.  Imported lazily because Strawberry
        # marks ``strawberry.types.nodes`` as an internal surface and we
        # do not want a hard import-time dependency on it from any
        # caller that imports the extension only to instantiate it.
        from strawberry.types.nodes import convert_selections

        selections = convert_selections(info, info.field_nodes)
        plan = self._get_or_build_plan(
            _root_child_selections(selections),
            target_model,
            info,
            origin,
        )
        self._publish_plan_to_context(plan, info)
        if plan.is_empty:
            return result
        # B8: reconcile the plan against optimizations the consumer has
        # already applied to ``result``. Drops exact-match entries,
        # avoids "lookup already seen" errors when the consumer's
        # prefetch chain descends past the optimizer's path, and
        # losslessly upgrades a consumer's plain ``"items"`` string to
        # the optimizer's richer ``Prefetch("items", queryset=...)``.
        # Returns a fresh plan and (when an upgrade was applied) a
        # rewritten queryset; B1's cached plan is never mutated.
        plan, result = diff_plan_for_queryset(plan, result)
        return plan.apply(result)

    def _get_or_build_plan(
        self,
        selections: list[Any],
        target_model: type,
        info: Any,
        origin: type | None,
    ) -> Any:
        """Return the cached plan for ``(info, target_model, origin)`` or build a new one.

        B1: plan cache.  Cache hits increment ``_cache_hits``; misses run
        the walker, evict the oldest quarter when full, insert iff the
        plan is ``cacheable``, and increment ``_cache_misses``.

        ``origin`` carries the resolver's actual Strawberry return type
        so primary-return and secondary-return resolvers on the same
        model do not share a cached plan. The extension's ``_plan_cache``
        is root-only — this helper is the sole insertion site, so
        ``origin`` always receives the concrete root origin in
        production; ``None`` is reserved for direct/test-only callers
        that deliberately build a plan without an origin.
        """
        cache_key = self._build_cache_key(info, target_model, origin)
        cached_plan = self._plan_cache.get(cache_key)
        if cached_plan is not None:
            self._cache_hits += 1
            return cached_plan
        plan = plan_optimizations(selections, target_model, info=info, source_type=origin)
        if plan.cacheable and len(self._plan_cache) >= _MAX_PLAN_CACHE_SIZE:
            # FIFO eviction: drop the oldest quarter at once to amortise
            # eviction cost across many subsequent inserts.  A cache hit
            # does *not* refresh recency (no LRU promotion), so a hot
            # plan that survives an eviction sweep continues to age out
            # naturally on the next sweep.
            to_remove = _MAX_PLAN_CACHE_SIZE // 4
            for _ in range(to_remove):
                self._plan_cache.pop(next(iter(self._plan_cache)))
        if plan.cacheable:
            self._plan_cache[cache_key] = plan
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
        _stash_on_context(info.context, DST_OPTIMIZER_PLAN, plan)
        _stash_on_context(info.context, DST_OPTIMIZER_FK_ID_ELISIONS, set(plan.fk_id_elisions))
        if self.strictness != "off":
            _stash_on_context(
                info.context,
                DST_OPTIMIZER_PLANNED,
                set(plan.planned_resolver_keys),
            )
            _stash_on_context(info.context, DST_OPTIMIZER_LOOKUP_PATHS, lookup_paths(plan))
            _stash_on_context(info.context, DST_OPTIMIZER_STRICTNESS, self.strictness)

    @staticmethod
    def check_schema(schema: Any) -> list[str]:
        """Audit schema-reachable types for unoptimized relations.

        Walks only the ``DjangoType``s reachable from the schema's root
        types (not the entire registry) and checks each **exposed**
        relation field (i.e., present in its registered definition's
        field map, not hidden by ``Meta.fields``/``Meta.exclude`` or
        ``OptimizerHint.SKIP``). Returns a list of warning strings for
        relations whose target model has no registered ``DjangoType``.

        Always returns warnings — never raises. The caller decides
        whether to raise based on the extension's ``strictness``.
        """
        reachable = _collect_schema_reachable_types(schema)
        # Dedupe (source_model, field_name) so multi-type models do not
        # double-warn: registry.iter_types() yields one entry per registered
        # type after spec-014 Slice 1, so a model with multiple types whose
        # field maps overlap on the same unregistered-target relation would
        # otherwise produce one identical warning per registered type. The
        # dedupe is a multi-type artifact, not generic defensiveness — every
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
           still never collide — using the raw source body would, because
           ``loc.source.body`` is the entire document.  We store the printed
           string (not its ``hash``) to eliminate the rare-but-real chance of
           two distinct document shapes sharing a 64-bit hash and silently
           sharing a cached plan.
        2. Frozenset of ``(var_name, var_value)`` for only the
           variables referenced in ``@skip``/``@include`` directives.
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
        # Memoize the rendered operation-plus-reachable-fragments document
        # key per execution: many root resolvers in one operation share the
        # same operation node, and ``print_ast`` is the heaviest step of
        # cache-key construction.  The memo is a per-execution ``ContextVar``
        # dict installed by ``on_execute``; if the extension is invoked
        # outside an ``on_execute`` lifecycle (some test fixtures call
        # ``_build_cache_key`` directly), fall back to recomputing.
        memo = _printed_ast_cache.get()
        if memo is None:
            doc_key = _print_operation_with_reachable_fragments(operation, fragments)
        else:
            op_id = id(operation)
            doc_key = memo.get(op_id)
            if doc_key is None:
                doc_key = _print_operation_with_reachable_fragments(operation, fragments)
                memo[op_id] = doc_key
        # Directive-variable extraction.
        directive_var_names = _collect_directive_var_names(
            operation,
            fragments=fragments,
        )
        variable_values = info.variable_values or {}
        relevant_vars = frozenset(
            (k, variable_values[k]) for k in directive_var_names if k in variable_values
        )
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
