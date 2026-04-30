# Spec: Optimizer — Beyond strawberry-graphql-django

## Problem statement

`spec-optimizer.md` O1–O6 rebuild the N+1 optimizer on the same architecture strawberry-graphql-django pioneered: root-gated resolve hook, selection-tree walker, cardinality-based `select_related`/`prefetch_related` dispatch, `Prefetch` downgrade for visibility-aware target types. That foundation is correct and battle-tested. But strawberry-graphql-django stopped there — every request re-walks the tree, every forward FK emits a JOIN even when the parent row already carries the answer, and the optimizer's behavior is invisible to consumers outside of raw SQL logs.

This spec covers eight improvements that the existing libraries do not ship. Each is independent; they can land in any order after O3 (the root-gated hook) is effective. The numbering is priority order, not dependency order.

## Current state

O1 (custom relation resolvers), O2 (selection-tree walker), and O3 (root-gated resolve hook with async parity and type-tracing) have shipped. The optimizer is effective end-to-end for depth-1 queries. O4 (nested prefetch chains), O5 (`only()` projection), and O6 (`Prefetch` downgrade) are specified in `spec-optimizer.md` but not yet implemented. This spec's items layer on top of O3 and are independent of O4–O6 unless noted.

## Proposed improvements

### B1 — AST-cached plans

**The win.** strawberry-graphql-django walks the selection tree on every request. For a production endpoint serving the same query 10,000 times/second, that is 10,000 identical tree walks producing the identical `OptimizationPlan`. An LRU cache keyed on `(document_hash, skip_include_variable_values)` turns 99% of repeated queries into a dictionary lookup. Production apps live on a handful of hot queries — this is the single biggest performance improvement on the table.

**Mechanism.** The plan is a function of three inputs: the GraphQL document AST (which determines the selection tree structure), the variable values that affect `@skip`/`@include` evaluation (which determine which branches the walker includes), and the target Django model (which determines which fields exist and their cardinalities). Everything else — the registry, the field metadata — is static for the lifetime of the schema. So the cache key is `(hash(document), frozenset(skip_include_vars), target_model)` and the cache value is the `OptimizationPlan`. The `target_model` component is essential: `_optimize` runs once per root resolver, and a single operation can have multiple root fields returning different models (e.g., `{ categories { ... } items { ... } }`). Without the model in the key, a cache hit from one root field would return the wrong plan for another.

**Directive-variable extraction.** `frozenset(skip_include_vars)` requires knowing *which* variables affect `@skip`/`@include` directives. Including all operation variables would cause cardinality explosion (a query with 10 filter variables would produce 2^10 cache entries even though none of them affect the selection tree). The correct approach: pre-walk the document AST once during cache-key construction to collect only the variable names referenced inside `@skip`/`@include` directive arguments, then extract just those values from `info.variable_values`. For queries with no conditional directives (the common production case), the directive-var set is empty and the cache collapses to `(document_hash, frozenset(), target_model)` — one entry per document per model.

**Cache lifetime.** Before implementing, verify Strawberry's `SchemaExtension` instantiation pattern. If extensions are instantiated once per schema and reused across requests, the cache lives on `self` and works as described. If extensions are recreated per request (the `on_execute` hook firing per operation hints at this), a `self`-attached cache resets every request and the hit rate is zero. In that case the cache must live at module level — a `dict` keyed as above, gated on a `weakref` to the schema for cleanup on schema rebuild. A 10-minute spike confirming the lifecycle should precede writing the cache code; document the finding in a code comment at the implementation site. Use `functools.lru_cache` or a simple bounded-size dict.

Pseudo code:

```text
# directive-var extraction (runs once per cache-key construction):
skip_include_var_names = collect_directive_vars(info.operation)  # pre-walk AST
relevant_vars = frozenset(
    (k, info.variable_values[k]) for k in skip_include_var_names
    if k in info.variable_values
)
cache_key = (document_hash(info), relevant_vars, target_model)
plan = _plan_cache.get(cache_key)  # module-level or self, per lifecycle spike
if plan is None:
    plan = plan_optimizations(selected_fields, target_model)
    _plan_cache[cache_key] = plan
return plan.apply(queryset)
```

**Cache invalidation.** The plan is immutable once built — no invalidation needed within a schema lifetime. Schema rebuild (e.g., hot-reload in dev) creates fresh extension instances (or resets the module-level cache via `weakref` callback), which start with empty caches. Static queries (no conditional directives) collapse to a single cache entry per document per model.

**Test surface.** Cache hit/miss counts via a `cache_info()` method (mirrors `lru_cache.cache_info()`; public, not underscore-prefixed — consumers will want it for benchmarks). End-to-end test: execute the same query twice, assert the walker ran once (mock or count). Edge case: same document with different `@skip` variable values produces different plans and both are cached. Edge case: query with filter variables but no `@skip`/`@include` — all executions share a single cache entry regardless of filter values.

**Depends on.** O3 (shipped). Independent of O4–O6.

### B2 — Forward-FK-id elision

**The win.** `{ items { name category { id } } }` does not need a JOIN. The `category_id` column is already on the `Item` row — Django stores FK values as `<field>_id` on the source model. strawberry-graphql-django emits `select_related("category")` anyway, pulling the entire `Category` row across a JOIN for nothing. We can detect "the only fields selected on the FK target are columns the source model already has" and skip the JOIN entirely.

**Mechanism.** In the walker's relation dispatch (currently in `_walk_selections`), before emitting a `select_related` entry for a forward FK: inspect the child selections on the FK target. If every selected scalar on the target is a field whose value is already available on the source row (specifically: `id` is always available as `<fk_name>_id` on the source), elide the `select_related` and instead ensure the `<fk_name>_id` column is in the `only()` set (O5). The resolver for the FK field can then return a stub object or resolve from the cached `_id` value.

The common case is `{ category { id } }` — consumers select the FK target's `id` to pass to the frontend as a reference. The parent row's `category_id` is the same value. No JOIN needed.

Pseudo code:

```text
if (field.many_to_one or field.one_to_one) and selected_child_scalars == {"id"}:
    plan.only_fields.add(field.attname)  # "category_id"
    mark_fk_id_elided(field.name)
    return
plan.select_related.add(field.name)
```

**Applicability.** The elision applies to both forward `ForeignKey` (`many_to_one`) and forward `OneToOneField` (non-auto-created `one_to_one`). Both store the `_id` column on the source row. Reverse OneToOne (`auto_created=True`) does not have an `_id` column on the source and is excluded.

**Resolver change required.** When the JOIN is elided, the existing forward resolver (`getattr(root, field_name)`) would trigger a lazy load because Django has no cached related object. The resolver must be swapped to return a lightweight stub — e.g., `target_model(pk=getattr(root, field.attname))` — or resolve the raw ID value directly into the GraphQL `id` field. The elision flag (`mark_fk_id_elided`) signals `_make_relation_resolver` (or a B2-specific resolver factory) to use the stub path instead of the default `getattr` path.

**Edge cases.** If the selection includes any scalar beyond `id` on the target (e.g., `{ category { id name } }`), the JOIN is required — fall through to the existing `select_related` path. If the target type has a custom `get_queryset` (O6), the elision cannot fire because the visibility filter needs the JOIN. This is a pure performance optimization with a clean fallback.

**Test surface.** Query-count assertion: `{ items { category { id } } }` issues 1 query (no JOIN) vs. 2 without elision. Negative case: `{ items { category { id name } } }` still JOINs. Edge case: nullable FK with `category { id }` returns `None` when the FK is null.

**Depends on.** O5 (`only()` projection) for the `<fk_name>_id` inclusion in the column set. O6 (visibility downgrade) for the `has_custom_get_queryset` guard. B5 (plan introspection via context) for the elision-flag stashing mechanism — the resolver reads the elision flag from `info.context` at call time, which is B5's stashing pattern. Can be spec'd now, implemented after O5+O6+B5.

### B3 — N+1 detection in dev mode

**The win.** A `DjangoOptimizerExtension(strictness="warn")` flag that emits a loud warning every time a resolver accesses a relation that was not covered by the optimization plan. strawberry-graphql-django assumes consumers will notice N+1 via SQL logs or django-debug-toolbar. We hand them a smoke alarm instead of a smoke detector.

**Mechanism.** When `strictness != "off"`, after applying the plan to the root queryset, attach a sentinel to `info.context` listing the planned relations (uses B5's context-stashing mechanism). The O1 relation resolvers (in `types/resolvers.py`) check the sentinel: if a relation is accessed that is not in the plan, log a warning naming the field, the parent type, and the query path. In dev mode this surfaces immediately in the console; in production it is a standard Python `logging.warning` that monitoring can alert on.

The sentinel is a `set[str]` of planned relation paths (e.g., `{"category", "items", "items__entries"}`). The resolver checks `f"{prefix}{field_name}" in sentinel`. If not present and the queryset is not already prefetched (i.e., the access will trigger a lazy load), emit the warning.

**Prerequisite: resolver signature change.** The current O1 resolvers (`_make_relation_resolver` in `types/resolvers.py`) take only `root`. To read the sentinel from `info.context`, they need `info` as a parameter. Strawberry supports `info` in resolver signatures via type detection (`strawberry.types.Info`), so this is a backward-compatible addition — existing resolvers gain the parameter, Strawberry injects it automatically. The signature change ships as part of B3, not before.

**Prerequisite: nested relation path construction.** A nested resolver for `entries` on an `Item` instance needs to know it is at path `items__entries`, not just `entries`. The resolver does not inherently know its depth in the tree. Two viable approaches: (a) reconstruct the dotted path from `info.path` (graphql-core's `Path` linked list — walk `.prev` to build the full path, then `snake_case` each segment), or (b) have the extension stash a mapping of `(parent_type, field_name) → full_path` on `info.context` alongside the sentinel so the resolver can look up its path in O(1). Approach (a) is simpler and requires no extra bookkeeping; approach (b) is faster for deep trees. The implementation should start with (a) and optimize to (b) only if profiling shows `info.path` traversal is measurable.

Pseudo code:

```text
# strictness: Literal["off", "warn", "raise"] = "off"
info.context.dst_optimizer_planned = planned_relation_paths(plan)

# In the relation resolver (B3 adds `info` parameter):
relation_path = build_dotted_path(info.path)  # walk info.path.prev chain
if relation_path not in info.context.dst_optimizer_planned:
    if will_lazy_load(root, field_name):
        if strictness == "raise":
            raise OptimizerError(f"Unplanned N+1: {relation_path}")
        logger.warning("Potential N+1 on %s", relation_path)
```

**Strictness API.** The constructor parameter is `strictness: Literal["off", "warn", "raise"] = "off"` — a single keyword with three named levels. `"off"` is the current silent behavior. `"warn"` logs via `logger.warning`. `"raise"` raises `OptimizerError` to fail-fast in tests. Mixing a boolean (`strict=True`) with a future string (`strict="raise"`) in the same kwarg was rejected to avoid a deprecation cycle when the third level lands.

**Test surface.** End-to-end: schema with `strictness="warn"`, query that accesses an unplanned relation, assert warning logged with the field path. `strictness="raise"` raises `OptimizerError`. Negative: planned relation does not warn. Unit: sentinel is populated correctly from the plan.

**Depends on.** O3 (shipped). B5 (context stashing mechanism). Independent of O4–O6.

### B4 — `Meta.optimizer_hints`

**The win.** strawberry-graphql-django's optimization hints live on per-field decorators (`@strawberry_django.field(select_related="...")`) — fine for their decorator API, awkward for ours. Meta-class hints are a free win because we already have the surface. DRF teams will reach for this without asking.

**Mechanism.** Add an optional `Meta.optimizer_hints` dict to `DjangoType`. Keys are field names; values are `OptimizerHint` instances that override the walker's automatic dispatch for that field.

**`OptimizerHint` typed wrapper.** Mixing raw strings (`"skip"`), `Prefetch` objects, and dicts (`{"select_related": True}`) in the same field-value position works but reads awkwardly and makes `_validate_meta` validation ad-hoc. Instead, a small typed class provides uniform shape and clean validation:

- `OptimizerHint.SKIP` — exclude this relation from the plan entirely (consumer manages it manually).
- `OptimizerHint.select_related()` — force `select_related` regardless of cardinality.
- `OptimizerHint.prefetch_related()` — force `prefetch_related` regardless of cardinality.
- `OptimizerHint.prefetch(Prefetch(...))` — use this specific `Prefetch` object instead of the auto-generated one.

`OptimizerHint` is a small class (or `enum` + factory methods) living in the optimizer subpackage and re-exported from the top-level `__init__.py` when B4 ships. The API surface is one import: `from django_strawberry_framework import OptimizerHint`.

The walker consults `optimizer_hints` before its default cardinality dispatch. If a hint exists for the current field, it takes precedence. This is the DRF-shaped analog of strawberry-graphql-django's `disable_optimization=True` per-field marker, but richer because it allows positive overrides (force a specific `Prefetch`), not just opt-out.

**Walker needs registry lookup.** The walker currently receives `model` (a Django model class), not the registered `DjangoType`. To read `_optimizer_hints`, it must look up the type class via `registry.get(model)`. The registry already exposes this method. When no `DjangoType` is registered for the model (e.g., an unregistered intermediate model), the walker skips the hints check and falls through to default cardinality dispatch. This same lookup is shared with B7 (`_optimizer_field_map`).

Pseudo code:

```text
type_cls = registry.get(model)
hint = getattr(type_cls, "_optimizer_hints", {}).get(field_name)
if hint is OptimizerHint.SKIP:
    return
if hint and hint.prefetch_obj is not None:
    plan.prefetch_related.add(hint.prefetch_obj)
    return
if hint and hint.force_select:
    plan.select_related.add(field_name)
    return
if hint and hint.force_prefetch:
    plan.prefetch_related.add(field_name)
    return
```

**Validation.** `_validate_meta` rejects unknown field names in `optimizer_hints` (same as `fields`/`exclude` validation). Hint values must be `OptimizerHint` instances — anything else raises `ConfigurationError` at schema-build time so typos and shape errors surface early.

**Test surface.** `SKIP` suppresses a relation from the plan. `.prefetch(Prefetch(...))` appears in the plan instead of a plain string. `.select_related()` forces select_related on a many-side relation. Unknown field name raises `ConfigurationError`. Non-`OptimizerHint` value raises `ConfigurationError`.

**Depends on.** O3 (shipped). The `"skip"` hint is independent of O4–O6. The `Prefetch(...)` hint composes naturally with O4 (nested chains) and O6 (downgrade rule) once those land.

### B5 — Plan introspection via context

**The win.** Stash the computed `OptimizationPlan` on `info.context` so consumers can write tests like `assert plan.select_related == ["category"]` instead of grepping `connection.queries`. Makes the optimizer's behavior observable instead of magic.

**Mechanism.** After `plan_optimizations` returns in `_optimize`, stash the plan on `info.context`. Strawberry's default context is an object (not a dict), so `setattr` is the primary approach. Consumers sometimes pass a plain dict as context, so the stash is defensive: try `setattr` first, fall back to `__setitem__`. Consumers and test code access it directly. The plan is a frozen snapshot — mutating it after the fact has no effect on the already-applied queryset.

The key name is `dst_optimizer_plan` (short for django-strawberry-framework) to avoid collision with consumer keys. B3 and B2 ride on this same stashing mechanism for their sentinel and elision flags respectively — B5 should land first so the context-stash pattern is proven before dependents ship.

Pseudo code:

```text
plan = plan_optimizations(selected_fields, target_model)
try:
    setattr(info.context, "dst_optimizer_plan", plan)
except AttributeError:
    info.context["dst_optimizer_plan"] = plan
return plan.apply(queryset)
```

**Test surface.** End-to-end: execute a query, assert `result.extensions` or `info.context` carries the plan with the expected `select_related` / `prefetch_related` entries. Unit: `_optimize` sets the context key.

**Depends on.** O3 (shipped). Independent of everything else. This is an afternoon project.

### B6 — Schema-build-time optimization audit

**The win.** A `DjangoOptimizerExtension.check_schema(schema)` classmethod that walks every registered `DjangoType`, inspects its relation fields, and surfaces any relation with no optimization story — relations that will silently N+1 in production because the optimizer cannot reach them (e.g., custom resolvers that return unoptimized querysets, or types not registered in the registry). Fail-fast at startup instead of N+1-fast in production. None of the existing libraries ship this.

**Mechanism.** At schema build time (callable from `ready()` or a management command), walk only the types reachable from the schema's root types — not the entire registry. Walking all registered types would produce false positives for types that are registered but not exposed in the schema (e.g., types used only in tests or internal helpers). The `schema` argument provides the root; the audit traverses the type graph from there.

For each reachable registered model, walk `model._meta.get_fields()` and check:
- Every relation field has a corresponding `DjangoType` registered for its target model.
- Every relation field is reachable by the walker (not excluded by `Meta.exclude`, not hidden behind a custom resolver that bypasses the optimizer).
- Forward FKs to unregistered types are flagged as "will lazy-load on every access."

Output is a list of warnings, one per unoptimized relation, with the field path and a suggested fix. When the extension's `strictness == "raise"` (see B3), these become errors at startup.

**`registry.iter_types()` public method.** B6 (and B7's walker) should not reach into `registry._types` directly. Add a `registry.iter_types() -> Iterator[tuple[type[Model], type]]` public method that yields `(model, type_cls)` pairs. This keeps the registry's internal dict shape private and gives a clean extension point for future filtering (e.g., schema-scoped registries).

Pseudo code:

```text
def check_schema(cls, schema):
    reachable = _collect_reachable_types(schema)  # walk schema root types
    warnings = []
    for model, type_cls in registry.iter_types():
        if type_cls not in reachable:
            continue
        for field in model._meta.get_fields():
            if not field.is_relation:
                continue
            if registry.get(field.related_model) is None:
                warnings.append(
                    f"{model.__name__}.{field.name} "
                    "has no registered target type")
    return warnings
```

**Test surface.** Schema with an unregistered FK target triggers a warning. Schema with all relations covered produces no warnings. Management command `check_optimizer` runs the audit and exits 0/1.

**Depends on.** O3 (shipped) + the type registry. Independent of O4–O6. The audit is static analysis — it runs at build time, not request time.

## Priority and ordering

**Recommended sequence:** B5 → B1 → B7 → B3 → B4 → B2 → B6 → B8.

**B5 first** because B3's sentinel-on-context and B2's elision-flag-on-context both ride on B5's stashing mechanism. Landing B5 first proves the pattern and gives the other two a tested foundation to build on. It is also the smallest slice — an afternoon project.

**B1 next** because it is the single biggest performance win and depends only on O3 (shipped). The cache-lifetime spike (see B1 "Cache lifetime") should precede implementation.

**B7 after B1** because together they eliminate all per-request introspection: B1 caches plan output, B7 caches field-metadata input. On cache miss the hot path is still fast; on cache hit it is a dict lookup.

**B3 after B5** because it consumes B5's context-stashing pattern for the sentinel. The `strictness` API should be designed before implementation so the kwarg shape is stable from day one.

**B4 after B3** because the `OptimizerHint` type and `_validate_meta` integration are API-surface work that benefits from the walker being well-exercised by B1/B7/B3 first.

**B2 last among the perf items** because it is the most subtle — resolver-stub trickery, `only()` column interaction, `has_custom_get_queryset` guard, and potential GlobalID interaction all need O5+O6+B5 to be settled first.

**B6 late** because the schema-build-time audit is ambitious and independent — it does not block any other slice and benefits from B4's `optimizer_hints` being available (hints affect which relations are flagged as unoptimized).

**B8 last** because queryset diffing is a pure polish item. Django handles duplicates gracefully, so B8 is about debug-log clarity and principle rather than correctness.

### B7 — Precomputed optimizer field metadata

**The win.** The O2 walker rebuilds `{f.name: f for f in model._meta.get_fields()}` on every walk, then checks `is_relation`, `many_to_many`, `one_to_many` per field per request. Since `DjangoType.__init_subclass__` already knows the model and its fields at class-creation time, we can precompute a `{snake_name: FieldMeta(is_relation, cardinality, target_model)}` mapping once and stash it on the class. The walker reads the cached map instead of rebuilding it.

This is complementary to B1: B1 caches the *plan output* (the finished `OptimizationPlan`), this caches the *field metadata input* (the Django field introspection the walker consumes). Both together mean the hot path is: dict lookup for cached plan → cache hit → return. On cache miss: dict lookup for cached field metadata → run walker → cache plan → return. No `_meta.get_fields()` call ever appears in the request path.

**Mechanism.** In `DjangoType.__init_subclass__`, after `_select_fields(meta)` computes the field list, build a `dict[str, FieldMeta]` where `FieldMeta` is a lightweight namedtuple or dataclass holding `is_relation`, `many_to_many`, `one_to_many`, `one_to_one`, `related_model`, and `attname` (the FK column name for forward FKs). Stash it as `cls._optimizer_field_map`. The walker reads `target_type._optimizer_field_map` instead of calling `model._meta.get_fields()`.

**Walker needs registry lookup.** Same as B4: the walker receives `model`, not `type_cls`. It must call `registry.get(model)` to obtain the `DjangoType` and read `_optimizer_field_map`. When no type is registered (unregistered model), the walker falls back to `model._meta.get_fields()` — the current behavior.

Pseudo code:

```text
cls._optimizer_field_map = {
    snake_case(field.name): FieldMeta.from_django_field(field)
    for field in selected_fields
}

# In the walker:
type_cls = registry.get(model)
cached_map = getattr(type_cls, "_optimizer_field_map", None)
field_map = cached_map or {f.name: f for f in model._meta.get_fields()}

field_meta = type_cls._optimizer_field_map.get(selection_name)
if field_meta and field_meta.is_relation:
    dispatch(field_meta)
```

**Test surface.** Assert `_optimizer_field_map` is populated after `DjangoType` subclass creation. Assert the walker produces the same plan whether it reads the cached map or rebuilds from `_meta`. Benchmark (optional): measure walk time with and without the cached map on a model with 20+ fields.

**Depends on.** O2 (shipped). Independent of O4–O6 and B1.

### B8 — Queryset optimization diffing

**The win.** When a consumer's `get_queryset` or root resolver already calls `.select_related("category")`, the optimizer blindly stacks another `.select_related("category")` on top. Django handles the duplicate gracefully (it is a dict merge internally), but it is wasted work, makes debug logging harder to read, and masks the consumer's intentional optimization under the framework's automatic one.

**Mechanism.** Before applying the plan in `_optimize`, inspect the queryset's existing optimization state:
- `queryset.query.select_related` — `False` when no `select_related` has been called (the Django default), or a `dict` mapping field names to nested dicts when populated. `flatten_select_related` must handle the `False` case by treating it as an empty set.
- `queryset._prefetch_related_lookups` — a tuple of strings and `Prefetch` objects. If a lookup is already present, skip it.

The diff is a simple set subtraction: `plan.select_related - already_selected`, `plan.prefetch_related - already_prefetched`. Apply only the delta.

Pseudo code:

```text
sr = queryset.query.select_related
already_selected = flatten_select_related(sr) if sr is not False else set()
already_prefetched = normalize_prefetches(queryset._prefetch_related_lookups)

plan.select_related = [p for p in plan.select_related if p not in already_selected]
plan.prefetch_related = [p for p in plan.prefetch_related if key(p) not in already_prefetched]

return plan.apply(queryset)
```

**Edge cases.** `Prefetch` objects are compared by `prefetch_to` attribute (the lookup path), not by identity. A consumer's `Prefetch("items", queryset=custom_qs)` should suppress the optimizer's plain `"items"` string — the consumer's version is more specific.

**Test surface.** Resolver returns a queryset with `.select_related("category")` already applied; optimizer does not add a duplicate. Consumer's `Prefetch("items", queryset=...)` suppresses the optimizer's plain `"items"`. Empty diff (everything already applied) → queryset returned unchanged.

**Depends on.** O3 (shipped). Independent of O4–O6.

## Non-goals

This spec does not revisit the O2 walker's core algorithm, the O3 hook architecture, or the O1 relation resolver shapes. Those are settled. It also does not cover Layer-3 features (filters, orders, aggregates, permissions) — those have their own specs.

## References

strawberry-graphql-django optimizer source: `strawberry_django/optimizer.py` — the baseline we improve on.

Django's `select_related` / `prefetch_related` internals: `django/db/models/query.py` — understanding the `query.select_related` dict merge and `_prefetch_related_lookups` dedup behavior is load-bearing for B1's cache correctness and B2's elision safety.

graphql-core AST node types: `graphql/language/ast.py` — `FieldNode`, `InlineFragmentNode`, `FragmentSpreadNode` carry the same information as Strawberry's wrapper dataclasses, relevant for the "skip Strawberry conversion" optimization noted in B1's implementation.
