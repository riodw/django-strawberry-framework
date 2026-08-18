# Spec: Optimizer — Beyond strawberry-graphql-django

Deliberation for this spec lives in its companion [rationale file][spec-004-rationale]: the per-slice `**The win.**` arguments, the eight fenced implementation proposals and where the shipped code departed from each, the whole recommended-build-sequence argument the former `## Priority and ordering` section carried, the 2026-04-30 extension-lifecycle spike and the consumer recommendation it reached, the shapes each decision rejected and why each lost, and every claim the spec once made and may no longer make. Read the spec for what holds; read that file for why it holds. Why the optimizer became a family of documents at all is `docs/SPECS/spec-002-optimizer-0_0_2.md`'s own deliberation, recorded in its rationale file and not restated here.

## Problem statement

`spec-002-optimizer-0_0_2.md` O1–O6 rebuild the N+1 optimizer on the same architecture strawberry-graphql-django pioneered: root-gated resolve hook, selection-tree walker, cardinality-based `select_related`/`prefetch_related` dispatch, `Prefetch` downgrade for visibility-aware target types. That foundation is correct and battle-tested. But strawberry-graphql-django stopped there — every request re-walks the tree, every forward FK emits a JOIN even when the parent row already carries the answer, and the optimizer's behavior is invisible to consumers outside of raw SQL logs.

This spec covers eight improvements that the existing libraries do not ship. Each rests on O3 (the root-gated hook) plus the cross-dependencies its own `**Depends on.**` paragraph names. The numbering is priority order, not dependency order; the recommended build sequence and the reasoning behind it are in the [rationale file][spec-004-rationale].

## Current state

O1 (custom relation resolvers), O2 (selection-tree walker), O3 (root-gated resolve hook with async parity and type-tracing), O4 (nested prefetch chains), O5 ([`only()`][glossary-only-projection] projection), and O6 (`Prefetch` downgrade) are the foundation the eight improvements extend; `docs/SPECS/spec-002-optimizer-0_0_2.md` and `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` own them. On top of that foundation the optimizer is effective end-to-end for nested relation queries, including B2 forward-[FK-id elision][glossary-fk-id-elision] for `id`-only target selections and B3 strictness keys that remain branch-sensitive under aliases.

## The eight improvements

### B1 — AST-cached plans

**Mechanism.** The plan is a function of the GraphQL document AST (which determines the selection tree structure), the variable values that affect which branches the walker includes, and the target Django model (which determines which fields exist and their cardinalities). Everything else — the registry, the field metadata — is static for the lifetime of the schema. The cache value is the `OptimizationPlan`; the cache key carries five components:

- The **printed** AST of the selected operation, with the printed definitions of every named fragment reachable from it appended. The printed string is stored rather than a hash of it: a hash admits a collision, and a collision here serves one document's plan to a structurally different document, silently and with no failure mode a test can catch. Printing the selected operation rather than the raw source body is also what keeps a multi-operation document (`query A {...} query B {...}`) from collapsing to one key.
- The frozenset of variable `(name, value)` pairs that affect the selection tree (see `**Directive-variable extraction.**`).
- The target Django model. This component is essential: `_optimize` runs once per root resolver, and a single operation can have multiple root fields returning different models (e.g., `{ categories { ... } items { ... } }`). Without the model in the key, a cache hit from one root field would return the wrong plan for another.
- The root response path, so two root fields returning the *same* model do not share a plan — the collision the model component closes, one level further in.
- The resolver's origin Strawberry type, so a primary-return and a secondary-return resolver over one model do not share a plan. Several `DjangoType`s over one model is `docs/SPECS/spec-018-meta_primary-0_0_6.md`'s surface.

Converted selections reach the cache behind a zero-arg callable rather than as a list, so a cache hit never pays for the AST-to-selection conversion; the callable is invoked at most once, and only on the build path.

**Directive-variable extraction.** The variable component requires knowing *which* variables affect the selection tree. Including all operation variables would cause cardinality explosion (a query with 10 filter variables would produce 2^10 cache entries even though none of them affect the selection tree). The document AST is pre-walked once during cache-key construction to collect two families of variable name: those referenced inside `@skip`/`@include` directive arguments, and those supplying `first`/`last`/`before`/`after` on a **non-root** field node — nested pagination values bake into windowed prefetch querysets and so must key the cache, while root pagination stays out because root slicing happens after the plan is applied. The nested-connection windows those values feed belong to `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`.

Collection is by variable name and deliberately over-collects: a duplicate cache entry is the cost of over-collecting, a wrong plan is the cost of under-collecting. The collected values are then read out of `info.variable_values` and normalized to a hashable form. The frozenset holds `(name, value)` **pairs**, not bare names — the name alone does not distinguish two executions of the same document that resolved the same directive variable differently — and a collected name the operation did not supply a value for is omitted rather than defaulted. For queries with no conditional directives and no nested pagination variables (the common production case), the set is empty and the cache collapses to one entry per document per model per root path per origin.

**Cache storage.** The cache is `self._plan_cache` — an ordered dict on the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] instance, bounded at 256 entries, which evicts its **least-recently-used** entries when it reaches that bound and drops a quarter of them at once so the eviction cost amortises. The LRU is hand-rolled rather than reached for through `functools.lru_cache` because that decorator caches a *function* and this cache is bound to the extension instance; it also evicts one entry at a time where this cache drops a quarter in one sweep. Because the cache is bound to the instance, the supported way to install the extension is a module-level singleton wrapped in a factory; `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` Decision 3 owns that construction contract.

**Cache invalidation.** The plan is immutable once built, so no invalidation is needed within a schema lifetime — and the immutability is structural rather than a convention: a plan is finalized at handoff (`optimizer/plans.py::OptimizationPlan.finalize`) and a later mutation of it raises (`::_assert_under_construction`). No sibling spec states that enforcement; it and the requirement are both this slice's. Schema rebuild (e.g., hot-reload in dev) creates fresh extension instances, which start with empty caches.

The plan cache is not the optimizer's only memo. Two per-execution memos are established and reset inside `on_execute` — one for built plans the cross-request cache refuses (a plan a nested fallback rebuilds once per parent row is not cacheable), one for the operation-constant cache-key parts — and a cross-request memo holds the printed-document key so a hot query does not re-print its AST. The nested-connection fallback that makes the per-execution memos load-bearing belongs to `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`.

**Test surface.** `cache_info()` is public API, not underscore-prefixed, because consumers want it for benchmarks; it returns a named tuple of `hits`, `misses`, and `size`. The counters are best-effort — they are incremented without a lock, and an execution-memo hit touches neither — so `misses` counts actual walker builds rather than key misses. End-to-end test: execute the same query twice, assert the walker ran once (mock or count). Edge case: same document with different `@skip` variable values produces different plans and both are cached. Edge case: query with filter variables but no `@skip`/`@include` — all executions share a single cache entry regardless of filter values.

The competitive argument for this slice, the extension-lifecycle spike behind the cache-storage decision together with the consumer recommendation it reached, and the key-construction shape this section proposed are in the [rationale file][spec-004-rationale].

**Depends on.** O3 (shipped). Independent of O4–O6.

### B2 — Forward-FK-id elision

**Mechanism.** In the walker's relation dispatch (`optimizer/walker.py::_plan_select_relation`), before emitting a `select_related` entry for a forward FK: inspect the child selections on the FK target. If the only selected scalar on the target is the target model's concrete primary-key field, and the FK points at that primary key, elide the `select_related` and instead ensure the `<fk_name>_id` column reaches the `only()` set (O5). The resolver for the FK field then serves the selection from that column without loading the related row.

The column append is the shared first step of both the select and the prefetch branch, and it is gated by the operation-wide projection gate that suppresses `.only(...)` outside `QUERY` operations — `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` owns that gate. It must run **ahead** of the elision short-circuit; `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` states that ordering invariant and what reversing it costs. The order is pinned by assertion, not by statement position alone — see the query-count row in **Test surface** below.

The common case is `{ category { id } }` — consumers select the FK target's primary key to pass to the frontend as a reference. The parent row's `category_id` is the same value when the FK targets the related model's primary key. No JOIN needed.

**Applicability.** The elision applies to both forward `ForeignKey` (`many_to_one`) and forward `OneToOneField` (non-auto-created `one_to_one`) when the relation targets the related model's primary key. Both store the target primary-key value on the source row. Reverse OneToOne (`auto_created=True`) does not have an `_id` column on the source and is excluded. Foreign keys using `to_field` against a non-PK target are also excluded because the source column stores the target field value, not the related instance's primary key. A target with a composite primary key is excluded too — one source column cannot carry a composite key.

**Resolver change required.** When the JOIN is elided, a plain forward resolver (`getattr(root, field_name)`) would trigger a lazy load because Django has no cached related object. The resolver instead returns a lightweight stub — `target_model(pk=getattr(root, field.attname))` — marked as a loaded row (`_state.adding = False`) rather than a new unsaved instance, with the stub's database alias set from the read router for the target model so it is routed like any other loaded instance (`docs/SPECS/spec-023-multi_db-0_0_7.md` owns multi-database routing). The elision flag is keyed by the **branch-sensitive resolver key** (parent type, field name, and GraphQL runtime response path) to avoid leaking elision state between aliases, sibling branches, or root fields in the same query. A query like `{ a: allItems { category { id } } b: allItems { category { id name } } }` elides in branch `a` and not in branch `b`; a flat `field_name`-keyed flag would incorrectly apply to both. A selection reachable under more than one response key therefore records one identity per key rather than one identity for the merged node — `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` owns that fan-out rule, and `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` multiplies it over nested-connection runtime prefixes. The flag is stashed on `info.context` (via B5's mechanism) and the resolver consults the same resolver-key identity the optimizer used when planning.

The stub cannot be built when a consumer projection has deferred the FK column on the parent row. That case does not fall back to a silent per-row lazy load: the resolver falls back **loudly**, so B3 strictness sees the access. `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` owns that fallback.

**Edge cases.** If the selection includes any scalar beyond the target primary key (e.g., `{ category { id name } }`), the JOIN is required — fall through to the existing `select_related` path. If the target type has a custom `get_queryset` (O6), the elision cannot fire because the visibility filter needs the JOIN. If the target type customizes resolution of the selected id/PK field, elision must also fall back to the JOIN because the custom resolver may depend on non-stubbed columns. Every fallback is explicit: a JOIN where the selection needs one, a strictness-visible relation access where the source row cannot serve the id. None of them degrades silently.

**Test surface.** Query-count assertion: `{ items { category { id } } }` issues 1 query (no JOIN) vs. 2 without elision. Negative case: `{ items { category { id name } } }` still JOINs. Edge case: nullable FK with `category { id }` returns `None` when the FK is null. Ordering invariant: the same document run at two parent cardinalities issues an equal, absolute query count — the assertion that fails if the FK-column append is ever moved behind the elision short-circuit, since the wire result is identical either way and only the count distinguishes an elided read from a per-row lazy load.

The competitive argument for this slice and the elision predicate this section proposed are in the [rationale file][spec-004-rationale].

**Depends on.** O5 (`only()` projection) for the `<fk_name>_id` inclusion in the column set. O6 (visibility downgrade) for the `has_custom_get_queryset` guard. B5 (plan introspection via context) for the elision-flag stashing mechanism — the resolver reads the elision flag from `info.context` at call time, which is B5's stashing pattern.

### B3 — N+1 detection in dev mode

**Mechanism.** A `DjangoOptimizerExtension(strictness="warn")` flag emits a loud warning every time a resolver accesses a relation that was not covered by the optimization plan. When `strictness != "off"`, after applying the plan to the root queryset, a sentinel listing the planned resolver keys is attached to `info.context` under the key `dst_optimizer_planned` (uses B5's context-stashing mechanism). The O1 relation resolvers (in `types/resolvers.py`) check the sentinel: a relation accessed that is not in the plan is reported naming the field, plus an optional reason the calling site supplies for an access it can characterise further. In dev mode this surfaces immediately in the console; in production it is a standard Python `logging.warning` that monitoring can alert on.

The sentinel is a `set[str]` of planned resolver keys, e.g. `ItemType.category@allItems.category` or `ItemType.category@allItems.cat`. The resolver key combines the parent type, the underlying field name (`info.field_name`, snake_cased), and the GraphQL runtime response path (`info.path` with list indexes stripped). This keeps aliases branch-sensitive without accepting bare field-name fallbacks that could leak across branches. Before warning or raising, the resolver also checks whether the access would actually lazy-load (via Django's `__dict__` cache for forward FK and `_prefetched_objects_cache` for many-side relations) — already-loaded relations are silently skipped even if not in the plan.

**Prerequisite: resolver signature change.** The O1 resolvers (`_make_relation_resolver` in `types/resolvers.py`) take `info` alongside `root` so they can read the sentinel from `info.context`. Strawberry supports `info` in resolver signatures via type detection (`strawberry.types.Info`), so it is a backward-compatible parameter — Strawberry injects it automatically. The signature belongs to B3.

**Prerequisite: nested relation path construction.** A nested resolver for `entries` on an `Item` instance needs to know it is at path `items__entries`, not just `entries`. The resolver does not inherently know its depth in the tree, so it reconstructs the path from `info.path` — graphql-core's `Path` linked list, walked back through `.prev` and snake-cased segment by segment. The walk is depth-bounded rather than unbounded, so a pathological `info.path` chain raises instead of looping.

**One further probe, and one override.** A nested connection served by a windowed prefetch is probed on its `to_attr` — a present attribute means the window already served the page, so the access is not a lazy load; that shape belongs to `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`. And the loud fallback B2 takes when a consumer projection defers an elided FK column bypasses the "key is planned, therefore silent" short-circuit, so a planned key cannot mask a genuine lazy load (`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`).

**Strictness API.** The constructor parameter is `strictness` with three named levels — `"off"`, `"warn"`, `"raise"` — validated at construction, so an unrecognised value raises at the call site rather than at query time. `"off"` is the silent default. `"warn"` logs via `logger.warning`. `"raise"` raises `OptimizerError` to fail-fast in tests.

The competitive argument for this slice, the second path-construction approach this section considered, the kwarg shape it rejected, and the detection loop it proposed are in the [rationale file][spec-004-rationale].

**Test surface.** End-to-end: schema with `strictness="warn"`, query that accesses an unplanned relation, assert the warning is logged naming the field. `strictness="raise"` raises `OptimizerError`. Negative: planned relation does not warn. Alias: `{ cat: category { name } }` does not warn when `category` is planned. Already-loaded: consumer `select_related` pre-loads the relation → no warning even if absent from the plan. Unit: sentinel is populated correctly from the plan.

**Depends on.** O3 (shipped). B5 (context stashing mechanism). Independent of O4–O6.

### B4 — [`Meta.optimizer_hints`][glossary-metaoptimizer-hints]

**Mechanism.** [`DjangoType`][glossary-djangotype] accepts an optional `Meta.optimizer_hints` dict. Keys are field names; values are [`OptimizerHint`][glossary-optimizerhint] instances that override the walker's automatic dispatch for that field.

**`OptimizerHint` typed wrapper.** A small typed class gives every hint a uniform shape and one validation path:

- `OptimizerHint.SKIP` — exclude this relation from the plan entirely (consumer manages it manually).
- `OptimizerHint.select_related()` — force `select_related` regardless of cardinality.
- `OptimizerHint.prefetch_related()` — force `prefetch_related` regardless of cardinality.
- `OptimizerHint.prefetch(Prefetch(...))` — use this specific `Prefetch` object instead of the auto-generated one.
- `OptimizerHint.strategy(...)` — select the fetch backend for one nested Relay connection. The backends and their selection rules belong to the nested-connection fetch seam, documented under "Nested connection indexing" in `docs/README.md`; this slice owns only the hint that carries the override.

`OptimizerHint` is a frozen dataclass in the optimizer subpackage (`optimizer/hints.py`), re-exported from the top-level `__init__.py`. The API surface is one import: `from django_strawberry_framework import OptimizerHint`.

The walker consults `optimizer_hints` before its default cardinality dispatch. If a hint exists for the current field, it takes precedence.

**Walker needs registry lookup.** The walker receives `model` (a Django model class), not the registered `DjangoType`. It resolves the model's registered type definition and reads `optimizer_hints` from it — `optimizer/walker.py::_resolve_field_map` performs the lookup, `::_resolve_optimizer_hints` reads the hints. When no `DjangoType` is registered for the model (e.g., an unregistered intermediate model), the walker skips the hints check and falls through to default cardinality dispatch. The same lookup serves B7's field map.

**Validation.** `Meta.optimizer_hints` is shape-checked while the rest of `Meta` is validated (`types/base.py::_validate_meta`), and its contents by the sibling `types/base.py::_validate_optimizer_hints`, called from the same `__init_subclass__`. A key naming no field on the model is rejected the way an unknown `fields`/`exclude` entry is. A key naming a field the type does not expose as a relation — excluded by `Meta.fields`/`Meta.exclude`, or selected but scalar — is rejected too: the walker only reads hints after entering the relation branch, so such a hint would silently drop the consumer's intent. Hint values must be `OptimizerHint` instances. Every rejection raises [`ConfigurationError`][glossary-configurationerror] at schema-build time so typos and shape errors surface early, and `OptimizerHint` itself rejects incompatible flag combinations at construction, so no hint can carry two directives at once.

**Test surface.** `SKIP` suppresses a relation from the plan. `.prefetch(Prefetch(...))` appears in the plan instead of a plain string. `.select_related()` forces select_related on a many-side relation. Unknown field name raises `ConfigurationError`; so does a hint on an excluded or scalar field. Non-`OptimizerHint` value raises `ConfigurationError`.

The competitive argument for this slice, the untyped hint-value shapes the typed wrapper was chosen over, and the hint-dispatch order this section proposed are in the [rationale file][spec-004-rationale].

**Depends on.** O3 (shipped). The `SKIP` hint is independent of O4–O6. The `.prefetch(Prefetch(...))` hint composes naturally with O4 (nested chains) and O6 (downgrade rule).

### B5 — Plan introspection via context

**Mechanism.** After `plan_optimizations` returns in `_optimize`, the plan is stashed on `info.context`. The stash is shape-defensive, because consumers pass different context shapes: a `dict` (or `dict` subclass) is written through the mapping path so it round-trips to the same read, and any other context — Strawberry's default context is an object, not a dict — is written with `setattr` first and `__setitem__` as the fallback. A context that refuses assignment (a frozen mapping, a locked `QueryDict`) is skipped rather than aborting the resolver chain. That shape-agnostic read/write dispatch is a shared utility rather than optimizer-private; `docs/SPECS/spec-047-resource_policy-0_0_14.md` is its other consumer. Consumers and test code read the key directly. The plan is a frozen snapshot — mutating it after the fact has no effect on the already-applied queryset.

The key name is `dst_optimizer_plan` (short for django-strawberry-framework) to avoid collision with consumer keys. B3 and B2 ride on this same stashing mechanism for their sentinel and elision flags respectively, so the optimizer's context keys are a family rather than one key. The whole family is cleared at the start of each execution, so a reused `context_value` cannot leak one operation's elisions or planned keys into the next. The set-valued keys accumulate across stashes rather than clobbering — `dst_optimizer_plan` alone stays last-wins — because a nested-connection fallback stashes a second batch for the same execution; that fallback belongs to `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`.

The opening argument for this slice, the ordering argument for landing it before its dependents, and the stash sequence it proposed are in the [rationale file][spec-004-rationale].

**Test surface.** End-to-end: execute a query, assert `info.context.dst_optimizer_plan` carries the plan with the expected `select_related` / `prefetch_related` entries. Unit: `_optimize` sets the context key. Dict-context variant: pass a plain dict as context, assert the plan is stashed through the mapping path and read back from it.

**Depends on.** O3 (shipped). Independent of everything else.

### B6 — Schema-build-time optimization audit

**Public API.** `DjangoOptimizerExtension.check_schema(schema)` is a static method that walks every schema-reachable `DjangoType`, inspects its exposed relation fields, and surfaces every relation the optimizer cannot reach — a relation whose target model has no registered `DjangoType`, and which therefore lazy-loads on every access.

**Mechanism.** At schema build time (callable from `ready()` or a management command), walk only the types reachable from the schema's root types — not the entire registry. Walking all registered types would produce false positives for types that are registered but not exposed in the schema (e.g., types used only in tests or internal helpers). The `schema` argument provides the root; the audit traverses the type graph from there, descending into object fields, union members, and the concrete implementations of every interface it meets. The interface arm is load-bearing rather than incidental: a `DjangoType` reachable only through an interface-typed root field would otherwise be skipped silently, which is exactly the failure the audit exists to prevent. The Relay interface surface it must not skip is `docs/SPECS/spec-015-relay_interfaces-0_0_5.md`'s foundation, which `docs/SPECS/spec-032-full_relay-0_0_9.md` later extended.

For each reachable registered type, walk only the relation fields **exposed by the `DjangoType`** — those that passed [`Meta.fields`][glossary-metafields] / [`Meta.exclude`][glossary-metaexclude] filtering and are present in its registered definition's field map — not the full set from `model._meta.get_fields()`. Relations hidden by Meta-level filtering, or opted out via `OptimizerHint.SKIP` (B4), are intentionally invisible to the optimizer and are not flagged. Every remaining relation field whose target model has no registered `DjangoType` produces one warning.

Warnings are deduped by `(model, field name)`. One model can carry several registered types, and without the dedupe a relation exposed by two of them warns twice for one defect; the walk still visits every reachable type, because a secondary type may expose a relation the primary hides. Several types over one model is `docs/SPECS/spec-018-meta_primary-0_0_6.md`'s surface.

Output is a list of warnings, one per unoptimized relation, naming the type, the model, and the field. `check_schema` always returns warnings — it does not raise. The caller (e.g., `AppConfig.ready()` or management command) decides whether to raise based on the extension's `strictness` setting. When `strictness == "raise"`, the caller converts warnings to `OptimizerError`.

**`registry.iter_types()` public method.** B6 and B7's walker do not reach into `registry._types` directly: `registry.iter_types() -> Iterator[tuple[type[Model], type]]` yields `(model, type_cls)` pairs, once per registered type, so a model with several registered types appears once per type and a per-model action dedupes by model. This keeps the registry's internal dict shape private and gives a clean extension point for future filtering (e.g., schema-scoped registries).

The competitive argument for this slice and the audit loop it proposed are in the [rationale file][spec-004-rationale].

**Test surface.** Schema with an unregistered FK target triggers a warning. Schema with all relations covered produces no warnings. Orphan types not reachable from root fields are ignored. SKIP-hinted and Meta-hidden relations are not flagged. A relation exposed by two registered types over one model warns once.

**Depends on.** O3 (shipped) + the type registry. Independent of O4–O6. The audit is static analysis — it runs at build time, not request time.

### B7 — Precomputed optimizer field metadata

**Mechanism.** In `DjangoType.__init_subclass__`, after `_select_fields(...)` computes the field list, a `dict[str, FieldMeta]` is built **keyed by the snake-cased field name** — the vocabulary the walker resolves a selection against — where `FieldMeta` (`optimizer/field_meta.py::FieldMeta`) is a frozen dataclass snapshot of a Django field's optimizer-relevant attributes: `is_relation`, the cardinality flags, `related_model`, and `attname` (the FK column name for forward FKs), plus the further slots the later relation work needed. The map is stored on the type's registered `DjangoTypeDefinition` as `field_map` — one canonical store, no class-attribute mirror of it anywhere — and the walker reads it from there instead of calling `model._meta.get_fields()`.

**Walker needs registry lookup.** Same as B4: the walker receives `model`, not `type_cls`, so it resolves the registered definition and reads its `field_map` (`optimizer/walker.py::_resolve_field_map`). When no type is registered (unregistered model), the walker falls back to a fresh `model._meta.get_fields()` walk and stamps each descriptor with `FieldMeta.from_django_field`, keyed by raw `f.name`. Both paths yield `FieldMeta` values.

The opening argument for this slice, its relationship to B1's plan cache, and the map construction and lookup it proposed are in the [rationale file][spec-004-rationale].

**Test surface.** Assert the definition's `field_map` is populated after `DjangoType` subclass creation. Assert the walker produces the same plan whether it reads the cached map or rebuilds from `_meta`. Benchmark (optional): measure walk time with and without the cached map on a model with 20+ fields.

**Depends on.** O2 (shipped). Independent of O4–O6 and B1.

### B8 — [Queryset optimization diffing][glossary-queryset-diffing]

A consumer's `get_queryset` or root resolver may already have called `.select_related("category")`. Stacking the optimizer's own `.select_related("category")` on top of it is wasted work: Django handles the duplicate gracefully (it is a dict merge internally), but the duplicate makes debug logging harder to read and masks the consumer's intentional optimization under the framework's automatic one. B8 reconciles the plan against what the queryset already carries before applying it.

**Mechanism.** Before applying the plan in `_optimize`, inspect the queryset's existing optimization state:
- `queryset.query.select_related` — three possible states: `False` (the Django default, no `select_related` called), `True` (wildcard `select_related()` with no arguments — all forward relations selected), or a nested `dict` mapping field names to sub-dicts (specific fields selected). When the value is `True`, treat all `select_related` entries in the plan as already satisfied and skip the select-related delta entirely. When `False`, treat as empty. When a `dict`, flatten its keys for the set subtraction.
- `queryset._prefetch_related_lookups` — a tuple of strings and `Prefetch` objects. If a lookup is already present, skip it.

Reconciliation starts as a set subtraction over lookup paths — `plan.select_related - already_selected`, `plan.prefetch_related - already_prefetched` — and only the delta is applied. It returns two things rather than one: the delta plan **and** the queryset to apply it against. The queryset is part of the return because reconciliation can also **upgrade** a consumer's plain string lookup to the optimizer's `Prefetch` object, which rewrites the queryset side; a one-sided `apply()` cannot express that.

A companion step drops planned `select_related` paths the queryset cannot traverse — a consumer projection that defers a column on the path makes Django refuse the join — and the dropped paths stay visible to strictness through the plan's per-path resolver-key ledgers, so a de-planned subtree is never silently treated as covered. Consumer-wins precedence is a deliberate permission-boundary stance rather than an oversight; `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` records that stance. The ancestry-aware absorption a nested chain's prefetches ride is this slice's own.

**Cache-safety: the cached plan is never mutated.** With B1's cache, the same `OptimizationPlan` object is reused across requests, so modifying `plan.select_related` or `plan.prefetch_related` in place would corrupt the cache for every subsequent request. The reconciliation copies rather than mutates. The requirement is enforced structurally rather than left to discipline — a plan is finalized at handoff, its directive lists become tuples so a later append raises, and a merge onto a finalized plan is rejected outright (`optimizer/plans.py::OptimizationPlan.finalize` and `::_assert_under_construction`). No sibling spec states that enforcement; it and the requirement are both this slice's.

The ordering argument that put this slice last, and the delta construction it proposed, are in the [rationale file][spec-004-rationale].

**Edge cases.** `Prefetch` objects are compared by `prefetch_to` attribute (the lookup path), not by identity. A consumer's `Prefetch("items", queryset=custom_qs)` should suppress the optimizer's plain `"items"` string — the consumer's version is more specific.

**Test surface.** Resolver returns a queryset with `.select_related("category")` already applied; optimizer does not add a duplicate. Consumer's `Prefetch("items", queryset=...)` suppresses the optimizer's plain `"items"`. Empty diff (everything already applied) → queryset returned unchanged.

**Depends on.** O3 (shipped). Independent of O4–O6.

## Non-goals

This spec does not revisit the O2 walker's core algorithm, the O3 hook architecture, or the O1 relation resolver shapes. Those are settled. It also does not cover Layer-3 features (filters, orders, aggregates, permissions) — those have their own specs.

## References

strawberry-graphql-django optimizer source: `strawberry_django/optimizer.py` — the baseline we improve on.

Django's `select_related` / `prefetch_related` internals: `django/db/models/query.py` — understanding the `query.select_related` dict merge and `_prefetch_related_lookups` dedup behavior is load-bearing for B8's reconciliation and B2's elision safety.

graphql-core AST node types: `graphql/language/ast.py` — `FieldNode`, `InlineFragmentNode`, `FragmentSpreadNode` carry the same information as Strawberry's wrapper dataclasses, which is what lets B1 key its cache on the printed operation AST and defer the conversion into Strawberry's wrappers behind a callable a cache hit never invokes.

## Implementation checklist

- [x] `registry.iter_types()` public method (prerequisite for B6/B7)
- [x] B1 cache-lifetime spike
- [x] `OptimizerHint` class skeleton in `optimizer/` (prerequisite for B4)
- [x] B5 — Plan introspection via context
- [x] B1 — AST-cached plans
- [x] B7 — Precomputed optimizer field metadata
- [x] B3 — N+1 detection (`strictness` API)
- [x] B4 — `Meta.optimizer_hints` + `OptimizerHint` wiring
- [x] B2 — Forward-FK-id elision
- [x] B6 — Schema-build-time optimization audit
- [x] B8 — Queryset optimization diffing

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metaoptimizer-hints]: ../GLOSSARY.md#metaoptimizer_hints
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-queryset-diffing]: ../GLOSSARY.md#queryset-diffing

<!-- docs/SPECS/ -->
[spec-004-rationale]: appx/spec-004-optimizer_beyond-0_0_3-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
