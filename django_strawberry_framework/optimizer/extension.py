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

Load-bearing rule (O6, not yet shipped): when a related field's target
``DjangoType`` defines a non-default ``get_queryset``, generate a
``Prefetch(...)`` keyed on the filtered queryset instead of a
``select_related``. This is the visibility-leak fix from
strawberry-graphql-django #572 / #583. We copy the behaviour, not the
API.

Architecture modeled on ``strawberry_django/optimizer.py`` — same
root-gate pattern, same ``ContextVar`` lifecycle, same recursive
type-tracing through graphql-core wrappers.
"""

import inspect
import logging
from contextvars import ContextVar
from typing import Any, NamedTuple

from django.db import models
from graphql.language.ast import (
    DirectiveNode,
    FragmentSpreadNode,
    VariableNode,
)
from graphql.language.printer import print_ast
from strawberry.extensions import SchemaExtension

from ..registry import registry
from .hints import OptimizerHint
from .walker import plan_optimizations

_MAX_PLAN_CACHE_SIZE = 256


def _stash_on_context(context: Any, key: str, value: Any) -> None:
    """Stash ``value`` on ``context`` under ``key``.

    Strawberry's default context is an object, so ``setattr`` is the
    primary path. Consumers sometimes pass a plain ``dict`` as context,
    so we fall back to ``__setitem__`` when ``setattr`` raises.
    When ``context`` is ``None`` (Strawberry's default when no
    ``context_value`` is provided), the stash is silently skipped.

    Shared by B5 (plan stashing) and future B3 (sentinel stashing).
    """
    if context is None:
        return
    try:
        setattr(context, key, value)
    except AttributeError:
        context[key] = value


logger = logging.getLogger("django_strawberry_framework")


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
    _walk_directives(node, names, fragments or {})
    return frozenset(names)


def _walk_directives(
    node: Any,
    names: set[str],
    fragments: dict[str, Any],
) -> None:
    """Recursive helper: descend into selections and collect directive var names."""
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
    selection_set = getattr(node, "selection_set", None)
    if selection_set is not None:
        for child in selection_set.selections or ():
            if isinstance(child, FragmentSpreadNode):
                frag_name = child.name.value if child.name else None
                frag_def = fragments.get(frag_name) if frag_name else None
                if frag_def is not None:
                    _walk_directives(frag_def, names, fragments)
            else:
                _walk_directives(child, names, fragments)


class CacheInfo(NamedTuple):
    """Plan-cache statistics, modeled on ``functools.lru_cache``."""

    hits: int
    misses: int
    size: int


_optimizer_active: ContextVar[bool] = ContextVar(
    "django_strawberry_framework_optimizer_active",
    default=False,
)


def _collect_schema_reachable_types(schema: Any) -> set[type]:
    """Return the set of ``DjangoType`` classes reachable from the schema's root types.

    Traverses from ``query_type``, ``mutation_type``, and
    ``subscription_type`` through their field return types recursively.
    Only types reachable from a root operation are included; orphan
    types passed via ``types=[]`` at schema construction are excluded
    to avoid false-positive audit warnings.
    """
    reachable: set[type] = set()
    gql_schema = getattr(schema, "_schema", None)
    if gql_schema is None:
        return reachable
    strawberry_schema = getattr(schema, "_strawberry_schema", schema)
    visited_type_names: set[str] = set()

    def _walk_gql_type(gql_type: Any) -> None:
        """Recursively collect DjangoType origins from a graphql-core type."""
        # Unwrap NonNull / List wrappers.
        while hasattr(gql_type, "of_type"):
            gql_type = gql_type.of_type
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
            if origin is not None and hasattr(origin, "_optimizer_field_map"):
                reachable.add(origin)
        # Recurse into fields.
        fields = getattr(gql_type, "fields", None)
        if fields is not None:
            for field_obj in fields.values():
                _walk_gql_type(getattr(field_obj, "type", None))

    for root_type in (gql_schema.query_type, gql_schema.mutation_type, gql_schema.subscription_type):
        if root_type is not None:
            _walk_gql_type(root_type)
    return reachable


def _resolve_model_from_return_type(info: Any) -> type[models.Model] | None:
    """Trace ``info.return_type`` through graphql-core wrappers to a Django model.

    graphql-core wraps resolver return types in layers of
    ``GraphQLNonNull`` and ``GraphQLList``. This function recursively
    peels ``.of_type`` until it reaches a leaf carrying a ``.name``
    attribute (a ``GraphQLObjectType``), then looks up the corresponding
    Strawberry type definition via the schema and reverse-maps to the
    Django model through the registry.

    Returns ``None`` when any step fails (unregistered type, non-object
    leaf, missing schema backref). The caller treats ``None`` as
    "nothing to optimize" and passes the queryset through unchanged.
    """
    rt = info.return_type
    while hasattr(rt, "of_type"):
        rt = rt.of_type
    type_name = getattr(rt, "name", None)
    if type_name is None:
        return None
    strawberry_schema = getattr(
        getattr(info, "schema", None),
        "_strawberry_schema",
        None,
    )
    if strawberry_schema is None:
        return None
    definition = strawberry_schema.get_type_by_name(type_name)
    if definition is None:
        return None
    origin = getattr(definition, "origin", None)
    return registry.model_for_type(origin)


class DjangoOptimizerExtension(SchemaExtension):
    """Strawberry schema extension that optimizes Django querysets per request.

    Pass an **instance** (not the bare class) to benefit from plan
    caching in async mode::

        schema = strawberry.Schema(
            query=Query,
            extensions=[DjangoOptimizerExtension()],  # instance!
        )

    Hooks:

    - ``on_execute`` — sets a ``ContextVar`` marking the optimizer as
      active for the operation's lifetime.
    - ``resolve`` — gates on ``info.path.prev is None`` (root resolver
      only). Calls ``_next``, checks ``isinstance(QuerySet)``, traces
      the Django model from the graphql-core return type, runs the O2
      walker, applies the plan.
    """

    def __init__(
        self,
        strictness: str = "off",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if strictness not in ("off", "warn", "raise"):
            msg = f"strictness must be 'off', 'warn', or 'raise', got {strictness!r}"
            raise ValueError(msg)
        self.strictness = strictness
        self._plan_cache: dict[tuple[int, frozenset[tuple[str, Any]], type], Any] = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def cache_info(self) -> CacheInfo:
        """Return plan-cache statistics (hits, misses, current size)."""
        return CacheInfo(
            hits=self._cache_hits,
            misses=self._cache_misses,
            size=len(self._plan_cache),
        )

    def on_execute(self) -> Any:  # type: ignore[override]
        """Mark the optimizer as active for the duration of execution."""
        token = _optimizer_active.set(True)
        yield
        _optimizer_active.reset(token)

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

        1. Non-``QuerySet`` results pass through unchanged.
        2. Trace the graphql-core return type to a Django model.
        3. Run the O2 walker to build an ``OptimizationPlan``.
        4. Apply the plan to the queryset.
        """
        if not isinstance(result, models.QuerySet):
            return result
        target_model = _resolve_model_from_return_type(info)
        if target_model is None:
            logger.debug(
                "Optimizer: return type for %s has no registered DjangoType; "
                "passing queryset through unchanged.",
                info.field_name,
            )
            return result
        if not info.field_nodes:
            return result
        # Strawberry's Info.selected_fields peels from field_nodes;
        # at the raw GraphQLResolveInfo level we use the walker's
        # convert_selections to get the same shape, or we can access
        # the selections directly from the field node's selection set.
        # The O2 walker expects the children of the root field, so we
        # build the Strawberry-shaped selection list from field_nodes.
        from strawberry.types.nodes import convert_selections

        selections = convert_selections(info, info.field_nodes)
        # selections[0] is the root field; its .selections are the
        # children the walker needs.
        # B1: plan cache — check before running the walker.
        cache_key = self._build_cache_key(info, target_model)
        cached_plan = self._plan_cache.get(cache_key)
        if cached_plan is not None:
            self._cache_hits += 1
            plan = cached_plan
        else:
            plan = plan_optimizations(selections[0].selections, target_model)
            # Evict oldest entries if cache is full.
            if len(self._plan_cache) >= _MAX_PLAN_CACHE_SIZE:
                # Remove the oldest quarter to amortize eviction cost.
                to_remove = _MAX_PLAN_CACHE_SIZE // 4
                for _ in range(to_remove):
                    self._plan_cache.pop(next(iter(self._plan_cache)))
            self._plan_cache[cache_key] = plan
            self._cache_misses += 1
        # B5: stash the plan on info.context so consumers and tests
        # can introspect the optimizer's decisions.
        _stash_on_context(info.context, "dst_optimizer_plan", plan)
        # B3: when strictness is active, stash the sentinel so resolvers
        # can detect unplanned lazy loads.
        if self.strictness != "off":
            paths: set[str] = set(plan.select_related)
            paths |= {getattr(e, "prefetch_to", e) for e in plan.prefetch_related}
            _stash_on_context(info.context, "dst_optimizer_planned", paths)
            _stash_on_context(info.context, "dst_optimizer_strictness", self.strictness)
        if plan.is_empty:
            return result
        # TODO(spec-optimizer_beyond.md B8): diff the plan against the
        # queryset's existing ``query.select_related`` and
        # ``_prefetch_related_lookups``; apply only the delta so
        # consumer-applied optimizations are not duplicated.
        #
        # Pseudo:
        #   sr = result.query.select_related
        #   already_sel = _flatten(sr) if sr is not False else set()
        #   already_pf = {getattr(p, "prefetch_to", p)
        #                 for p in result._prefetch_related_lookups}
        #   plan.select_related = [
        #       p for p in plan.select_related
        #       if p not in already_sel]
        #   plan.prefetch_related = [
        #       p for p in plan.prefetch_related
        #       if (getattr(p, "prefetch_to", p)
        #           not in already_pf)]
        return plan.apply(result)

    @classmethod
    def check_schema(cls, schema: Any) -> list[str]:
        """Audit schema-reachable types for unoptimized relations.

        Walks only the ``DjangoType``s reachable from the schema's root
        types (not the entire registry) and checks each **exposed**
        relation field (i.e., present in ``_optimizer_field_map``, not
        hidden by ``Meta.fields``/``Meta.exclude`` or
        ``OptimizerHint.SKIP``). Returns a list of warning strings for
        relations whose target model has no registered ``DjangoType``.

        Always returns warnings — never raises. The caller decides
        whether to raise based on the extension's ``strictness``.
        """
        reachable = _collect_schema_reachable_types(schema)
        warnings: list[str] = []
        for _model, type_cls in registry.iter_types():
            if type_cls not in reachable:
                continue
            field_map = getattr(type_cls, "_optimizer_field_map", None)
            if field_map is None:
                continue
            hints = getattr(type_cls, "_optimizer_hints", {})
            for field_name, meta in field_map.items():
                if not meta.is_relation:
                    continue
                # Skip fields opted out via OptimizerHint.SKIP.
                hint = hints.get(field_name)
                if hint is not None and (hint is OptimizerHint.SKIP or hint.skip):
                    continue
                if meta.related_model is not None and registry.get(meta.related_model) is None:
                    warnings.append(
                        f"{_model.__name__}.{field_name} has no registered target DjangoType",
                    )
        return warnings

    @staticmethod
    def _build_cache_key(
        info: Any,
        target_model: type[models.Model],
    ) -> tuple[int, frozenset[tuple[str, Any]], type]:
        """Build the plan-cache key from resolver info and target model.

        Key components:
        1. Hash of the operation source text (stable across requests
           for the same query string).
        2. Frozenset of ``(var_name, var_value)`` for only the
           variables referenced in ``@skip``/``@include`` directives.
        3. The target Django model class (different root fields in the
           same operation can return different models).
        """
        # Document hash: use the source body when available (cheap),
        # fall back to print_ast (expensive but correct).
        operation = info.operation
        loc = getattr(operation, "loc", None)
        if loc is not None and getattr(loc, "source", None) is not None:
            doc_hash = hash(loc.source.body)
        else:
            doc_hash = hash(print_ast(operation))
        # Directive-variable extraction.
        directive_var_names = _collect_directive_var_names(
            operation,
            fragments=info.fragments,
        )
        variable_values = info.variable_values or {}
        relevant_vars = frozenset(
            (k, variable_values[k]) for k in directive_var_names if k in variable_values
        )
        return (doc_hash, relevant_vars, target_model)

    def plan_relation(
        self,
        field: Any,
        target_type: type,
        info: Any,
    ) -> tuple[str, Any]:
        """Plan a single relation traversal (O6 entry point).

        Returns ``("select", field_name)`` or
        ``("prefetch", Prefetch(...))`` describing how the optimizer
        should materialize this relation on the parent queryset.
        """
        # TODO(spec-optimizer.md O6): implement. Log every downgrade
        # decision via ``logger.debug``. Wire into the O2 walker so
        # the planner delegates to ``plan_relation`` per relation
        # rather than dispatching on cardinality directly.
        raise NotImplementedError("plan_relation pending spec-optimizer.md O6")
