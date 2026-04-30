# Spec: Optimizer — Beyond strawberry-graphql-django

## Problem statement

`spec-optimizer.md` O1–O6 rebuild the N+1 optimizer on the same architecture strawberry-graphql-django pioneered: root-gated resolve hook, selection-tree walker, cardinality-based `select_related`/`prefetch_related` dispatch, `Prefetch` downgrade for visibility-aware target types. That foundation is correct and battle-tested. But strawberry-graphql-django stopped there — every request re-walks the tree, every forward FK emits a JOIN even when the parent row already carries the answer, and the optimizer's behavior is invisible to consumers outside of raw SQL logs.

This spec covers six improvements that the existing libraries do not ship. Each is independent; they can land in any order after O3 (the root-gated hook) is effective. The numbering is priority order, not dependency order.

## Current state

O1 (custom relation resolvers), O2 (selection-tree walker), and O3 (root-gated resolve hook with async parity and type-tracing) have shipped. The optimizer is effective end-to-end for depth-1 queries. O4 (nested prefetch chains), O5 (`only()` projection), and O6 (`Prefetch` downgrade) are specified in `spec-optimizer.md` but not yet implemented. This spec's items layer on top of O3 and are independent of O4–O6 unless noted.

## Proposed improvements

### B1 — AST-cached plans

**The win.** strawberry-graphql-django walks the selection tree on every request. For a production endpoint serving the same query 10,000 times/second, that is 10,000 identical tree walks producing the identical `OptimizationPlan`. An LRU cache keyed on `(document_hash, skip_include_variable_values)` turns 99% of repeated queries into a dictionary lookup. Production apps live on a handful of hot queries — this is the single biggest performance improvement on the table.

**Mechanism.** The plan is a function of two inputs: the GraphQL document AST (which determines the selection tree structure) and the variable values that affect `@skip`/`@include` evaluation (which determine which branches the walker includes). Everything else — the Django model, the registry, the field metadata — is static for the lifetime of the schema. So the cache key is `(hash(document), frozenset(skip_include_vars))` and the cache value is the `OptimizationPlan`.

Implementation site: `_optimize` in `optimizer/extension.py`, before the `plan_optimizations` call. Check the cache first; on miss, run the walker and store. The cache lives on the extension instance (one per schema in sync mode, fresh per request in async mode — matches Strawberry's extension lifecycle). Use `functools.lru_cache` or a simple dict with bounded size.

**Cache invalidation.** The plan is immutable once built — no invalidation needed within a schema lifetime. Schema rebuild (e.g., hot-reload in dev) creates fresh extension instances, which start with empty caches. The `@skip`/`@include` variable values are the only runtime input; static queries (no conditional directives) collapse to a single cache entry per document.

**Test surface.** Cache hit/miss counts via a `_cache_info()` method (mirrors `lru_cache.cache_info()`). End-to-end test: execute the same query twice, assert the walker ran once (mock or count). Edge case: same document with different `@skip` variable values produces different plans and both are cached.

**Depends on.** O3 (shipped). Independent of O4–O6.

### B2 — Forward-FK-id elision

**The win.** `{ items { name category { id } } }` does not need a JOIN. The `category_id` column is already on the `Item` row — Django stores FK values as `<field>_id` on the source model. strawberry-graphql-django emits `select_related("category")` anyway, pulling the entire `Category` row across a JOIN for nothing. We can detect "the only fields selected on the FK target are columns the source model already has" and skip the JOIN entirely.

**Mechanism.** In the walker's relation dispatch (currently in `_walk_selections`), before emitting a `select_related` entry for a forward FK: inspect the child selections on the FK target. If every selected scalar on the target is a field whose value is already available on the source row (specifically: `id` is always available as `<fk_name>_id` on the source), elide the `select_related` and instead ensure the `<fk_name>_id` column is in the `only()` set (O5). The resolver for the FK field can then return a stub object or resolve from the cached `_id` value.

The common case is `{ category { id } }` — consumers select the FK target's `id` to pass to the frontend as a reference. The parent row's `category_id` is the same value. No JOIN needed.

**Edge cases.** If the selection includes any scalar beyond `id` on the target (e.g., `{ category { id name } }`), the JOIN is required — fall through to the existing `select_related` path. If the target type has a custom `get_queryset` (O6), the elision cannot fire because the visibility filter needs the JOIN. This is a pure performance optimization with a clean fallback.

**Test surface.** Query-count assertion: `{ items { category { id } } }` issues 1 query (no JOIN) vs. 2 without elision. Negative case: `{ items { category { id name } } }` still JOINs. Edge case: nullable FK with `category { id }` returns `None` when the FK is null.

**Depends on.** O5 (`only()` projection) for the `<fk_name>_id` inclusion in the column set. O6 (visibility downgrade) for the `has_custom_get_queryset` guard. Can be spec'd now, implemented after O5+O6.

### B3 — N+1 detection in dev mode

**The win.** A `DjangoOptimizerExtension(strict=True)` flag that emits a loud warning every time a resolver accesses a relation that was not covered by the optimization plan. strawberry-graphql-django assumes consumers will notice N+1 via SQL logs or django-debug-toolbar. We hand them a smoke alarm instead of a smoke detector.

**Mechanism.** When `strict=True`, after applying the plan to the root queryset, attach a sentinel to `info.context` listing the planned relations. The O1 relation resolvers (in `types/resolvers.py`) check the sentinel: if a relation is accessed that is not in the plan, log a warning naming the field, the parent type, and the query path. In dev mode this surfaces immediately in the console; in production it is a standard Python `logging.warning` that monitoring can alert on.

The sentinel is a `set[str]` of planned relation paths (e.g., `{"category", "items", "items__entries"}`). The resolver checks `f"{prefix}{field_name}" in sentinel`. If not present and the queryset is not already prefetched (i.e., the access will trigger a lazy load), emit the warning.

**Strictness levels.** `strict=True` warns. A future `strict="raise"` could raise `OptimizerError` to fail-fast in tests. Default is `False` (current behavior — silent).

**Test surface.** End-to-end: schema with `strict=True`, query that accesses an unplanned relation, assert warning logged with the field path. Negative: planned relation does not warn. Unit: sentinel is populated correctly from the plan.

**Depends on.** O3 (shipped). Independent of O4–O6.

### B4 — `Meta.optimizer_hints`

**The win.** strawberry-graphql-django's optimization hints live on per-field decorators (`@strawberry_django.field(select_related="...")`) — fine for their decorator API, awkward for ours. Meta-class hints are a free win because we already have the surface. DRF teams will reach for this without asking.

**Mechanism.** Add an optional `Meta.optimizer_hints` dict to `DjangoType`. Keys are field names; values are optimization directives that override the walker's automatic dispatch for that field.

Supported hint values (initial set):
- `"skip"` — exclude this relation from the plan entirely (consumer manages it manually).
- `Prefetch(...)` — use this specific `Prefetch` object instead of the auto-generated one.
- `{"select_related": True}` / `{"prefetch_related": True}` — force cardinality override.

The walker consults `optimizer_hints` before its default cardinality dispatch. If a hint exists for the current field, it takes precedence. This is the DRF-shaped analog of strawberry-graphql-django's `disable_optimization=True` per-field marker, but richer because it allows positive overrides (force a specific `Prefetch`), not just opt-out.

**Validation.** `_validate_meta` rejects unknown field names in `optimizer_hints` (same as `fields`/`exclude` validation). Hint values are validated at schema-build time so typos surface early.

**Test surface.** `"skip"` suppresses a relation from the plan. `Prefetch(...)` appears in the plan instead of a plain string. Unknown field name raises `ConfigurationError`.

**Depends on.** O3 (shipped). The `"skip"` hint is independent of O4–O6. The `Prefetch(...)` hint composes naturally with O4 (nested chains) and O6 (downgrade rule) once those land.

### B5 — Plan introspection via context

**The win.** Stash the computed `OptimizationPlan` on `info.context` so consumers can write tests like `assert plan.select_related == ["category"]` instead of grepping `connection.queries`. Makes the optimizer's behavior observable instead of magic.

**Mechanism.** After `plan_optimizations` returns in `_optimize`, set `info.context.dst_optimizer_plan = plan` (or use a `ContextVar` if the context object is not a dict). Consumers and test code access it directly. The plan is a frozen snapshot — mutating it after the fact has no effect on the already-applied queryset.

The key name is `dst_optimizer_plan` (short for django-strawberry-framework) to avoid collision with consumer keys.

**Test surface.** End-to-end: execute a query, assert `result.extensions` or `info.context` carries the plan with the expected `select_related` / `prefetch_related` entries. Unit: `_optimize` sets the context key.

**Depends on.** O3 (shipped). Independent of everything else. This is an afternoon project.

### B6 — Schema-build-time optimization audit

**The win.** A `DjangoOptimizerExtension.check_schema(schema)` classmethod that walks every registered `DjangoType`, inspects its relation fields, and surfaces any relation with no optimization story — relations that will silently N+1 in production because the optimizer cannot reach them (e.g., custom resolvers that return unoptimized querysets, or types not registered in the registry). Fail-fast at startup instead of N+1-fast in production. None of the existing libraries ship this.

**Mechanism.** At schema build time (callable from `ready()` or a management command), iterate `registry._types`. For each registered model, walk `model._meta.get_fields()` and check:
- Every relation field has a corresponding `DjangoType` registered for its target model.
- Every relation field is reachable by the walker (not excluded by `Meta.exclude`, not hidden behind a custom resolver that bypasses the optimizer).
- Forward FKs to unregistered types are flagged as "will lazy-load on every access."

Output is a list of warnings, one per unoptimized relation, with the field path and a suggested fix. In `strict` mode (see B3), these become errors at startup.

**Test surface.** Schema with an unregistered FK target triggers a warning. Schema with all relations covered produces no warnings. Management command `check_optimizer` runs the audit and exits 0/1.

**Depends on.** O3 (shipped) + the type registry. Independent of O4–O6. The audit is static analysis — it runs at build time, not request time.

## Priority and ordering

B1 (plan caching) and B2 (FK-id elision) are where the genuine "we are better" performance wins sit. B1 can land immediately after O3. B2 depends on O5+O6 for full effectiveness but can be spec'd and partially implemented now.

B3 (strict mode) and B5 (plan introspection) are developer-experience wins that make the optimizer observable. Both are small, independent, and can land at any time.

B4 (`Meta.optimizer_hints`) is the DRF-shaped API surface win. It is the natural home for `disable_optimization` and positive `Prefetch` overrides once consumers start needing them.

B6 (schema audit) is the most ambitious but also the most unique — no existing library does static N+1 analysis at schema build time. It is the "we are better" story for the README.

B7 (precomputed field metadata) and B8 (queryset diffing) are pure implementation refinements that reduce per-request overhead. B7 pairs naturally with B1 (together they eliminate all per-request introspection). B8 makes the optimizer a better citizen when composed with consumer code that already optimizes.

### B7 — Precomputed optimizer field metadata

**The win.** The O2 walker rebuilds `{f.name: f for f in model._meta.get_fields()}` on every walk, then checks `is_relation`, `many_to_many`, `one_to_many` per field per request. Since `DjangoType.__init_subclass__` already knows the model and its fields at class-creation time, we can precompute a `{snake_name: FieldMeta(is_relation, cardinality, target_model)}` mapping once and stash it on the class. The walker reads the cached map instead of rebuilding it.

This is complementary to B1: B1 caches the *plan output* (the finished `OptimizationPlan`), this caches the *field metadata input* (the Django field introspection the walker consumes). Both together mean the hot path is: dict lookup for cached plan → cache hit → return. On cache miss: dict lookup for cached field metadata → run walker → cache plan → return. No `_meta.get_fields()` call ever appears in the request path.

**Mechanism.** In `DjangoType.__init_subclass__`, after `_select_fields(meta)` computes the field list, build a `dict[str, FieldMeta]` where `FieldMeta` is a lightweight namedtuple or dataclass holding `is_relation`, `many_to_many`, `one_to_many`, `one_to_one`, `related_model`, and `attname` (the FK column name for forward FKs). Stash it as `cls._optimizer_field_map`. The walker reads `target_type._optimizer_field_map` instead of calling `model._meta.get_fields()`.

**Test surface.** Assert `_optimizer_field_map` is populated after `DjangoType` subclass creation. Assert the walker produces the same plan whether it reads the cached map or rebuilds from `_meta`. Benchmark (optional): measure walk time with and without the cached map on a model with 20+ fields.

**Depends on.** O2 (shipped). Independent of O4–O6 and B1.

### B8 — Queryset optimization diffing

**The win.** When a consumer's `get_queryset` or root resolver already calls `.select_related("category")`, the optimizer blindly stacks another `.select_related("category")` on top. Django handles the duplicate gracefully (it is a dict merge internally), but it is wasted work, makes debug logging harder to read, and masks the consumer's intentional optimization under the framework's automatic one.

**Mechanism.** Before applying the plan in `_optimize`, inspect the queryset's existing optimization state:
- `queryset.query.select_related` — a `dict` (when populated) or `False` (when empty). If a key is already present, skip it in the plan.
- `queryset._prefetch_related_lookups` — a tuple of strings and `Prefetch` objects. If a lookup is already present, skip it.

The diff is a simple set subtraction: `plan.select_related - already_selected`, `plan.prefetch_related - already_prefetched`. Apply only the delta.

**Edge cases.** `Prefetch` objects are compared by `prefetch_to` attribute (the lookup path), not by identity. A consumer's `Prefetch("items", queryset=custom_qs)` should suppress the optimizer's plain `"items"` string — the consumer's version is more specific.

**Test surface.** Resolver returns a queryset with `.select_related("category")` already applied; optimizer does not add a duplicate. Consumer's `Prefetch("items", queryset=...)` suppresses the optimizer's plain `"items"`. Empty diff (everything already applied) → queryset returned unchanged.

**Depends on.** O3 (shipped). Independent of O4–O6.

## Non-goals

This spec does not revisit the O2 walker's core algorithm, the O3 hook architecture, or the O1 relation resolver shapes. Those are settled. It also does not cover Layer-3 features (filters, orders, aggregates, permissions) — those have their own specs.

## References

strawberry-graphql-django optimizer source: `strawberry_django/optimizer.py` — the baseline we improve on.

Django's `select_related` / `prefetch_related` internals: `django/db/models/query.py` — understanding the `query.select_related` dict merge and `_prefetch_related_lookups` dedup behavior is load-bearing for B1's cache correctness and B2's elision safety.

graphql-core AST node types: `graphql/language/ast.py` — `FieldNode`, `InlineFragmentNode`, `FragmentSpreadNode` carry the same information as Strawberry's wrapper dataclasses, relevant for the "skip Strawberry conversion" optimization noted in B1's implementation.
