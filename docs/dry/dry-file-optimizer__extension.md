# DRY review: `django_strawberry_framework/optimizer/extension.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/extension.py` is the central orchestration engine and runtime execution coordinator of the framework's GraphQL query optimization subsystem ([spec-002][spec-002], [spec-004][spec-004], [spec-030][spec-030], [spec-033][spec-033], [spec-035][spec-035], [spec-036][spec-036], [spec-044][spec-044], [spec-051][spec-051]). It defines the primary consumer-facing Strawberry `SchemaExtension` ([`DjangoOptimizerExtension`][optimizer-extension]), implements root-gated query plan execution, manages multi-tiered plan and AST memoization caches, coordinates AST variable and fragment analysis, enforces N+1 strictness and foreign-key ID elision stashes, and provides external cooperation points for Relay connection fields and mutation payload refetching.

It owns the following architectural responsibilities:

1. **SchemaExtension Lifecycle Hooks & Execution Coordination:**
   - [`DjangoOptimizerExtension.on_execute`][optimizer-extension]: Bracketed generator lifecycle hook invoked at the start of each GraphQL operation execution.
     - Cleans any leftover optimizer context keys from previous executions via [`clear_optimizer_context`][optimizer-context] on the operation's context.
     - Sets the active extension instance in [`_active_optimizer`][optimizer-extension] (`ContextVar`) so external entry points ([`apply_connection_optimization`][optimizer-extension]) share the instance-bound plan cache.
     - Publishes the instance's configured nested-connection fetch strategy to [`_active_nested_strategy`][optimizer-nested-fetch] (`ContextVar`) for the walker.
     - Seeds per-execution task-local dictionary caches: [`_cache_key_parts_cache`][optimizer-extension] for AST key parts, [`_execution_plan_cache`][optimizer-extension] for intra-execution uncacheable plan reuse, and [`converted_selections_cache`][optimizer-selections] for AST selection conversion reuse.
     - Initializes task-local scoped relation tracking via [`begin_scoped_relations`][optimizer-context] and arms N+1 strictness via [`begin_strictness`][optimizer-context].
     - In the `finally` block, tears down all task-local state in exact reverse order via [`end_strictness`][optimizer-context], [`end_scoped_relations`][optimizer-context], and `ContextVar.reset` calls.
   - [`DjangoOptimizerExtension.resolve`][optimizer-extension]: Root-gated resolver hook intercepting GraphQL field resolution.
     - Gates execution on `info.path.prev is None`: only root resolvers initiate the AST traversal and query planning pass, while nested resolvers pass through untouched because Django's ORM handles nested relation traversal through `__`-chained `select_related` and `prefetch_related` paths attached at the root.
     - Handles both synchronous and asynchronous resolvers: if `_next` returns an awaitable coroutine, returns an async closure `_async_optimize` that awaits the result before passing it to [`_optimize`][optimizer-extension]; synchronous results are passed to `_optimize` directly.
   - [`DjangoOptimizerExtension.execution_context`][optimizer-extension] (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.execution_context`): Property with getter and setter backed by [`_execution_context_var`][optimizer-extension] (`ContextVar[Any]`). Ensures Strawberry's per-operation execution context remains strictly task-local even when the extension instance is shared across concurrent operations in a singleton factory configuration (`extensions=[lambda: _optimizer]`).

2. **Root Query Optimization & Plan Application:**
   - [`DjangoOptimizerExtension._optimize`][optimizer-extension]: Root-level optimization workflow for schema middleware.
     - Coerces Django `models.Manager` instances (such as `Model.objects` shorthand) to unevaluated `models.QuerySet` via `normalize_query_source(result)` from [`django_strawberry_framework.utils.querysets`][utils-querysets], passing non-queryset results through unchanged.
     - Enforces evaluated queryset guard G1 ([spec-035][spec-035] Decision 3): if `getattr(result, "_result_cache", None) is not None`, returns the queryset unchanged without cloning or planning to avoid re-executing SQL queries that consumer resolver code already ran.
     - Traces the GraphQL return type to a Django model and Strawberry origin via [`_resolve_model_from_return_type`][optimizer-extension]. If unresolvable, logs a debug message and passes the queryset through unchanged.
     - Delegates the plan construction and execution tail to [`DjangoOptimizerExtension.apply_to`][optimizer-extension].
   - [`DjangoOptimizerExtension.apply_to`][optimizer-extension]: The universal plan-build-and-apply engine shared by middleware, Relay connection fields, and mutation payload refetching.
     - Takes `target_type`, `target_model`, `queryset`, `info`, and an optional `selection_extractor`.
     - Defers AST conversion behind a zero-argument thunk `_node_selections` to avoid allocating `SelectedField` trees on plan-cache hits.
     - Builds or retrieves the plan via [`_get_or_build_plan`][optimizer-extension].
     - Prunes unsupportable `select_related` paths against consumer `.only()` / `.defer()` projections via [`prune_unsupportable_select_related`][optimizer-plans] (B8).
     - Reconciles plan prefetches against existing consumer queryset optimizations via [`diff_plan_for_queryset`][optimizer-plans] (B8).
     - Publishes plan and strictness sentinels to `info.context` via [`_publish_plan_to_context`][optimizer-extension].
     - If the plan is not empty, applies optimizations to the queryset via `plan.apply(queryset)`.

3. **Multi-Tier Plan & Document Caching Architecture:**
   - [`DjangoOptimizerExtension._get_or_build_plan`][optimizer-extension]: Coordinates the two-tier plan cache.
     - Tier 1 (Cross-Request Instance Cache): Looks up `cache_key` in `self._plan_cache` (an `OrderedDict` bounded by [`_MAX_PLAN_CACHE_SIZE = 256`][optimizer-extension]). On hit, promotes LRU recency with `move_to_end(cache_key)`, increments `_cache_hits`, and returns the cached plan.
     - Tier 2 (Intra-Execution Memo): If Tier 1 misses, checks [`_execution_plan_cache`][optimizer-extension] (`ContextVar`). Allows uncacheable plans (`plan.cacheable == False`, e.g., with request-scoped `get_queryset` or consumer `Prefetch` hints) to be reused across parent rows during nested fallback connection execution within the same operation without polluting the cross-request cache.
     - Miss Path: Invokes the selection thunk, runs the O2 AST walker [`plan_optimizations`][optimizer-walker], evicts the least-recently-used quarter (`_MAX_PLAN_CACHE_SIZE // 4`) if full, stores cacheable plans in `_plan_cache` or uncacheable plans in `_execution_plan_cache`, increments `_cache_misses`, and returns the plan.
   - [`DjangoOptimizerExtension._build_cache_key`][optimizer-extension]: Constructs a deterministic cache key tuple `(doc_key, relevant_vars, target_model, runtime_path_from_info(info), origin)`.
     - Memoizes operation-constant parts `(doc_key, relevant_vars)` in [`_cache_key_parts_cache`][optimizer-extension] keyed by `id(operation)`.
     - Uses [`_doc_cache_entry`][optimizer-extension] for cross-request document text and variable-name memoization.
     - Freezes variable values into hashable, collision-resistant tokens via [`_hashable_variable_value`][optimizer-extension].
   - [`_doc_cache_entry`][optimizer-extension]: Cross-request LRU cache [`_doc_key_cache`][optimizer-extension] (bounded by [`_MAX_DOC_KEY_CACHE_SIZE = 256`][optimizer-extension]) mapping `(source_body, operation_name)` to `(doc_key, cache_relevant_var_names)`.

4. **AST Variable & Fragment Analysis Primitives:**
   - [`_walk_cache_relevant_vars`][optimizer-extension] & [`_collect_cache_var_families`][optimizer-extension]: Unified single-descent AST traversal collecting both directive variables (`@skip` / `@include` on any node via [`directive_variable_names`][optimizer-selections]) and nested Relay pagination variables (`first`, `last`, `before`, `after` defined in [`_PAGINATION_ARG_NAMES`][optimizer-extension] on `FieldNode` at spread-site depth >= 1). Cycle guard tracks `(fragment_name, spread_depth)`.
   - Thin wrappers: [`_collect_directive_var_names`][optimizer-extension], [`_collect_nested_pagination_var_names`][optimizer-extension], and [`_collect_cache_relevant_var_names`][optimizer-extension].
   - Variable Value Freezing: [`_hashable_variable_value`][optimizer-extension] and recursive [`_freeze_variable_value`][optimizer-extension] convert lists, dicts, sets, tuples, and custom scalar values into tagged structural tuples. Retains exact stdlib/built-in scalar types ([`_SAFE_CACHE_SCALAR_TYPES`][optimizer-extension]) structurally while safely degrading custom, unhashable, or cyclic values to opaque tokens with cycle detection.
   - Fragment Definition Resolution: [`_collect_reachable_fragment_definitions`][optimizer-extension], [`_walk_reachable_fragment_definitions`][optimizer-extension], and [`_print_operation_with_reachable_fragments`][optimizer-extension] deterministically gather and render printed ASTs of reachable fragments alongside the operation AST.

5. **Context Sentinels, Strictness & Set Unions:**
   - [`DjangoOptimizerExtension._publish_plan_to_context`][optimizer-extension]: Stashes [`DST_OPTIMIZER_PLAN`][optimizer-context] on `info.context`, unions [`DST_OPTIMIZER_FK_ID_ELISIONS`][optimizer-context], publishes planned resolver keys to task-local scoped relations via [`_publish_scoped_relations`][optimizer-context], and if strictness is not `"off"`, unions [`DST_OPTIMIZER_PLANNED`][optimizer-context] and [`DST_OPTIMIZER_LOOKUP_PATHS`][optimizer-context] and stashes [`DST_OPTIMIZER_STRICTNESS`][optimizer-context].
   - [`DjangoOptimizerExtension._stash_union`][optimizer-extension]: Implements set union on request context values with subset early-out (`new <= existing`) to eliminate redundant frozenset reallocations during repeated parent row executions.

6. **Schema Audit & Override Seams:**
   - [`DjangoOptimizerExtension.check_schema`][optimizer-extension]: Static audit method inspecting exposed relations on `DjangoType` definitions reachable from schema root operations via [`_collect_schema_reachable_types`][optimizer-extension], returning warnings for relations whose target models have no registered `DjangoType`, respecting [`hint_is_skip`][optimizer-hints] overrides.
   - [`DjangoOptimizerExtension.plan_relation`][optimizer-extension]: Instance method delegating to [`plan_relation`][optimizer-walker] in `walker.py`, serving as a clean override seam for custom relation planning subclasses and test fixtures.
   - [`DjangoOptimizerExtension.cache_info`][optimizer-extension]: Returns a [`CacheInfo`][optimizer-extension] (`hits`, `misses`, `size`) snapshot.
   - [`DjangoOptimizerExtension.__init__`][optimizer-extension]: Configures strictness validation (`"off"`, `"warn"`, `"raise"`), resolves nested connection fetch strategy via [`resolve_strategy`][optimizer-nested-fetch], and initializes instance-bound caches and counters.

7. **External Cooperation Points & Selection Extractors:**
   - [`apply_connection_optimization`][optimizer-extension]: Public cooperation helper for Relay connection fields ([`DjangoConnectionField`][connection-fields]) and mutation resolvers ([`django_strawberry_framework.mutations.resolvers`][mutations-resolvers]). Discovers the active optimizer via `_active_optimizer.get()`, resolves target model, unboxes raw info, and calls `optimizer.apply_to`.
   - Selection Extractors:
     - [`_root_child_selections`][optimizer-extension]: Flattens child selections across multiple root field nodes (handling merged root fields with the same response key).
     - [`_connection_node_child_selections`][optimizer-extension]: Extracts node-level child selections from Relay connection wrappers (`edges { node { ... } }`) using [`connection_node_children`][optimizer-selections] and [`connection_field_names`][optimizer-selections].
     - [`mutation_payload_child_selections`][optimizer-extension]: Builds a closure navigating mutation payload object slots (`node` or `result`) with runtime prefix paths ([spec-036][spec-036] Decision 9).
   - Data Structures:
     - [`CacheInfo`][optimizer-extension]: NamedTuple containing `hits: int`, `misses: int`, `size: int`.
     - [`_OriginAndModel`][optimizer-extension]: NamedTuple containing `origin: type`, `model: type[models.Model]`.
   - Type Resolution:
     - [`_resolve_model_from_return_type`][optimizer-extension]: Resolves `(origin, model)` by unwrapping graphql-core type wrappers via [`unwrap_graphql_type`][utils-typing], looking up Strawberry schema type definition via [`strawberry_schema_from_info`][utils-typing], and resolving model through [`registry.model_for_type`][registry].

Connected behavior examined:
- [`django_strawberry_framework/optimizer/_context.py`][optimizer-context]: Stash key constants, start-of-execution clearing, task-local scoped relations and strictness `ContextVar` management.
- [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans]: `OptimizationPlan`, `diff_plan_for_queryset`, `prune_unsupportable_select_related`, `runtime_path_from_info`, `lookup_paths`.
- [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: Selection AST walker producing `OptimizationPlan` instances and per-relation planner `plan_relation`.
- [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections]: Selection-traversal AST primitives, converted selections cache, connection node extractors, directive variable extractors.
- [`django_strawberry_framework/optimizer/hints.py`][optimizer-hints]: Optimizer hints and `hint_is_skip` check.
- [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch]: Nested connection fetch strategies and active strategy ContextVar.
- [`django_strawberry_framework/connection/fields.py`][connection-fields]: Relay connection fields delegating pre-slice optimization to `apply_connection_optimization`.
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Mutation post-write refetch delegating to `apply_connection_optimization` with `mutation_payload_child_selections`.
- [`django_strawberry_framework/types/resolvers.py`][types-resolvers]: Model relation resolvers querying `relation_is_optimizer_scoped` and `active_strictness`.
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Centralized `normalize_query_source` for Manager coercion and QuerySet detection.
- [`django_strawberry_framework/utils/context.py`][utils-context]: Shape-agnostic request context access.
- [`django_strawberry_framework/registry.py`][registry]: Global model and type definition registry.
- [`tests/optimizer/test_extension.py`][test-optimizer-extension]: Comprehensive test suites verifying root gating, caching tiers, LRU eviction, strictness, schema audit, and variable hashing.
- [`tests/test_connection.py`][test-connection]: Integration tests verifying connection field cooperation with `apply_connection_optimization`.
- [`tests/mutations/test_resolvers.py`][test-mutations-resolvers]: Integration tests verifying mutation payload child selection extraction and refetch optimization.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/extension.py --include-constants`):
- Parsed 1 target file, 1550 lines.
- Inventory of symbols:
  - 4 module constants: [`_MAX_PLAN_CACHE_SIZE`][optimizer-extension], [`_PAGINATION_ARG_NAMES`][optimizer-extension], [`_SAFE_CACHE_SCALAR_TYPES`][optimizer-extension], [`_MAX_DOC_KEY_CACHE_SIZE`][optimizer-extension].
  - 3 class definitions: [`CacheInfo`][optimizer-extension], [`_OriginAndModel`][optimizer-extension], [`DjangoOptimizerExtension`][optimizer-extension].
  - 13 methods on `DjangoOptimizerExtension`: [`DjangoOptimizerExtension.__init__`][optimizer-extension], [`DjangoOptimizerExtension.execution_context`][optimizer-extension] (getter/setter), [`DjangoOptimizerExtension.cache_info`][optimizer-extension], [`DjangoOptimizerExtension.on_execute`][optimizer-extension], [`DjangoOptimizerExtension.resolve`][optimizer-extension], [`DjangoOptimizerExtension._optimize`][optimizer-extension], [`DjangoOptimizerExtension.apply_to`][optimizer-extension], [`DjangoOptimizerExtension._get_or_build_plan`][optimizer-extension], [`DjangoOptimizerExtension._publish_plan_to_context`][optimizer-extension], [`DjangoOptimizerExtension._stash_union`][optimizer-extension], [`DjangoOptimizerExtension.check_schema`][optimizer-extension], [`DjangoOptimizerExtension._build_cache_key`][optimizer-extension], [`DjangoOptimizerExtension.plan_relation`][optimizer-extension].
  - 17 module-level functions: [`_walk_cache_relevant_vars`][optimizer-extension], [`_collect_cache_var_families`][optimizer-extension], [`_collect_directive_var_names`][optimizer-extension], [`_collect_nested_pagination_var_names`][optimizer-extension], [`_collect_cache_relevant_var_names`][optimizer-extension], [`_hashable_variable_value`][optimizer-extension], [`_freeze_variable_value`][optimizer-extension], [`_collect_reachable_fragment_definitions`][optimizer-extension], [`_walk_reachable_fragment_definitions`][optimizer-extension], [`_print_operation_with_reachable_fragments`][optimizer-extension], [`_doc_cache_entry`][optimizer-extension], [`_root_child_selections`][optimizer-extension], [`_connection_node_child_selections`][optimizer-extension], [`mutation_payload_child_selections`][optimizer-extension], [`_collect_schema_reachable_types`][optimizer-extension], [`_resolve_model_from_return_type`][optimizer-extension], [`apply_connection_optimization`][optimizer-extension].
  - Re-exported backward-compatibility aliases: `_child_selections`, `_unvisited_fragment_definition`, `_named_children`, `_node_children_with_runtime_prefix`, `_response_key`, `_stash_on_context`.
  - Public export tuple: `__all__ = ("CacheInfo", "DjangoOptimizerExtension", "_stash_on_context", "apply_connection_optimization")`.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `DjangoOptimizerExtension` is the singular root coordinator for GraphQL query optimization across the entire repository. Sibling subsystems do not reimplement query planning or AST traversal; instead, they integrate cleanly through explicit public cooperation seams:
   - Relay connection fields ([`django_strawberry_framework/connection/fields.py`][connection-fields]) call [`apply_connection_optimization`][optimizer-extension] directly on pre-slice querysets with [`_connection_node_child_selections`][optimizer-extension].
   - Mutation resolvers ([`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]) call [`apply_connection_optimization`][optimizer-extension] on post-write refetch querysets with [`mutation_payload_child_selections`][optimizer-extension].
   - Generated model relation resolvers ([`django_strawberry_framework/types/resolvers.py`][types-resolvers]) read strictness and relation visibility sentinels managed by `_publish_plan_to_context` via `optimizer/_context.py`.
   - Queryset normalization is centralized in [`django_strawberry_framework/utils/querysets.py`][utils-querysets] and consumed identically by `_optimize` and resolver helpers.
   - AST selection conversions and traversal are centralized in [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections].
   - Strategy resolution is centralized in [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch].
   - Plan reconciliation and projection pruning are centralized in [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans].
   There is zero duplicate query planning or AST walking logic across flavors.

2. **Sync and async twins:**
   Zero duplication. In [`DjangoOptimizerExtension.resolve`][optimizer-extension], synchronous and asynchronous resolvers are handled in a single unified entry point: when `_next` returns an awaitable coroutine (`inspect.isawaitable(result)`), `resolve` returns a lightweight `_async_optimize` wrapper that awaits the coroutine before executing [`_optimize`][optimizer-extension]; synchronous results branch directly to `_optimize`. `on_execute` utilizes standard synchronous generator semantics (`yield`) paired with Python `contextvars.ContextVar`, which natively maintains execution isolation across synchronous threads and asyncio event loops alike. `apply_connection_optimization`, cache lookups, AST variable collection, and schema checking are purely synchronous and identical for both sync and async query execution.

3. **Derived rather than repeated knowledge:**
   - [`_collect_cache_relevant_var_names`][optimizer-extension] derives its result as the union of directive variables and non-root pagination variables produced by a single AST traversal in [`_collect_cache_var_families`][optimizer-extension].
   - [`_doc_cache_entry`][optimizer-extension] derives and caches both the printed document key and the relevant variable names together keyed by `(source_body, operation_name)`.
   - [`_cache_key_parts_cache`][optimizer-extension] combines `(doc_key, relevant_vars)` into a single tuple memoized per execution by `id(operation)`.
   - [`CacheInfo`][optimizer-extension] fields (`hits`, `misses`, `size`) derive directly from internal counters `_cache_hits`, `_cache_misses`, and `len(self._plan_cache)`.
   - [`_OriginAndModel`][optimizer-extension] bundles resolved Strawberry origin and Django model into a validated pair.
   - [`_PAGINATION_ARG_NAMES`][optimizer-extension] is the single authoritative set pinning Relay pagination argument names (`"first"`, `"last"`, `"before"`, `"after"`).
   - [`_SAFE_CACHE_SCALAR_TYPES`][optimizer-extension] is the single source of truth defining exact immutable scalar types safe for structural cache key hashing.

4. **Inverse and round-trip pairs:**
   - [`DjangoOptimizerExtension.on_execute`][optimizer-extension] manages symmetric bracketed state setup and teardown within a strict `try/finally` block:
     - [`begin_strictness`][optimizer-context] paired with [`end_strictness`][optimizer-context].
     - [`begin_scoped_relations`][optimizer-context] paired with [`end_scoped_relations`][optimizer-context].
     - `ContextVar.set` tokens paired with `ContextVar.reset` for `converted_selections_cache`, `_execution_plan_cache`, `_cache_key_parts_cache`, `_active_nested_strategy`, and `_active_optimizer`.
   - [`_freeze_variable_value`][optimizer-extension] maintains active container IDs in `active_containers` set with symmetric `add` and `remove` within a `try/finally` block for cycle detection.
   - Plan cache LRU eviction enforces bounded capacity invariant (`len(self._plan_cache) <= _MAX_PLAN_CACHE_SIZE`).

5. **Contracts restated in another medium:**
   The architectural, caching, and lifecycle contracts of `DjangoOptimizerExtension` are codified across:
   - Code: [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension], [`django_strawberry_framework/optimizer/_context.py`][optimizer-context], [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans], [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker], [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections], [`django_strawberry_framework/connection/fields.py`][connection-fields], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/types/resolvers.py`][types-resolvers];
   - Specifications: [`docs/SPECS/spec-002-optimizer-0_0_2.md`][spec-002] (O1–O6), [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004] (B1–B8), [`docs/SPECS/spec-030-connection_field-0_0_9.md`][spec-030], [`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`][spec-033], [`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`][spec-035], [`docs/SPECS/spec-036-mutations-0_0_10.md`][spec-036], [`docs/SPECS/spec-044-debug_extension-0_0_14.md`][spec-044], [`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`][spec-051];
   - Test suites: [`tests/optimizer/test_extension.py`][test-optimizer-extension] (5,658 lines covering root gating, sync/async parity, plan cache hits/misses/eviction, variable freezing, directive/pagination variable isolation, context clearing, re-entrant nested executions, strictness, schema audit, evaluated queryset bypass), [`tests/test_connection.py`][test-connection], [`tests/mutations/test_resolvers.py`][test-mutations-resolvers], [`tests/types/test_resolvers.py`][test-types-resolvers];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook], [`LIFECYCLE.html`][lifecycle-html].

### The single-edit-site test

- **Posited change 1 (Extending Relay pagination argument names for plan caching):** Add a new pagination argument name (e.g. `"search"` in 0.1.2) whose variable values must key the plan cache when present on non-root field nodes.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension] (adding `"search"` to [`_PAGINATION_ARG_NAMES`][optimizer-extension]).
  - *Site count:* 1.
- **Posited change 2 (Adjusting default cache capacity):** Increase the maximum size of the plan cache or the document key cache.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension] (updating [`_MAX_PLAN_CACHE_SIZE`][optimizer-extension] or [`_MAX_DOC_KEY_CACHE_SIZE`][optimizer-extension]).
  - *Site count:* 1.
- **Posited change 3 (Adding a standard immutable scalar type to safe cache scalar types):** Add a stdlib scalar (e.g. `ipaddress.IPv4Address`) to the safe scalar set so values are retained structurally rather than tokenized opaquely.
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension] (adding the type to [`_SAFE_CACHE_SCALAR_TYPES`][optimizer-extension]).
  - *Site count:* 1.
- **Posited change 4 (Modifying QuerySet/Manager normalization behavior):** Update Manager coercion or QuerySet detection rules.
  - *Sites that must move:* Exactly 1 site at root owner: [`django_strawberry_framework/utils/querysets.py`][utils-querysets] (`normalize_query_source`). Exactly 0 sites in `extension.py`.
  - *Site count:* 1 (0 in target).
- **Posited change 5 (Introducing a new mutation payload slot navigation wrapper):** Add support for a new custom mutation payload wrapper slot.
  - *Sites that must move:* Exactly 1 site at caller in [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers] (or in `mutation_payload_child_selections` in `extension.py`).
  - *Site count:* 1.

### Rejected candidates

1. **Merging `optimizer/extension.py` and `optimizer/walker.py` into a monolithic module:**
   - Disproved per [spec-002][spec-002] and [spec-051][spec-051]. `extension.py` owns the Strawberry middleware lifecycle, plan caching, context management, and external resolver integration, whereas `walker.py` owns the O2 selection AST traversal algorithm and Django ORM queryset modification logic. Separating them prevents circular dependencies and allows unit testing of query planning algorithms in isolation from GraphQL execution contexts.
2. **Keying the plan cache solely by raw document text `loc.source.body`:**
   - Disproved per [spec-004][spec-004] (B1). Multi-operation documents (`query A { ... } query B { ... }`) share identical `source.body` text across operations; caching on raw document text would cause operation A to erroneously reuse a plan built for operation B. `_build_cache_key` keys on the printed AST of the specific operation plus reachable fragment definitions.
3. **Evaluating variable values without the `_hashable_variable_value` boundary:**
   - Disproved per [spec-033][spec-033] (Decision 7) and [spec-035][spec-035]. Custom scalar parsers can return unhashable containers, cyclic structures, or objects whose `__eq__` or `__hash__` methods execute arbitrary user code. Normalizing variable values with tagged structural tokens and opaque fallbacks protects the cache boundary against cardinality explosions, crashes, and denial-of-service vulnerabilities.
4. **Optimizing evaluated querysets (`_result_cache is not None`):**
   - Disproved per [spec-035][spec-035] (Decision 3, G1). If a consumer's root resolver already evaluated a queryset (e.g., via `len(qs)` or `bool(qs)`), attaching `.only()` or `select_related` clones the queryset and forces Django to re-execute the SQL query, silently doubling database queries. Returning evaluated querysets unchanged respects consumer execution state.

## Opportunities

None — `django_strawberry_framework/optimizer/extension.py` is an exceptionally well-structured, robust, and clean implementation. It cleanly separates middleware orchestration from AST traversal primitives, implements multi-tiered caching with fail-closed safety, provides transparent sync and async execution support, and exhibits zero redundant logic.

## Judgment

Zero-edit review. `optimizer/extension.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/extension.py --review docs/dry/dry-file-optimizer__extension.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independently traced and verified `django_strawberry_framework/optimizer/extension.py` against all callers, sibling modules, test suites, and specifications.

1. **Behavioral Trace & Boundary Analysis:**
   - **Lifecycle Coordination & Thread Safety:** Re-verified [`DjangoOptimizerExtension.on_execute`][optimizer-extension] and [`DjangoOptimizerExtension.resolve`][optimizer-extension]. Confirmed that `_execution_context_var` guarantees task-local isolation for Strawberry execution contexts when `DjangoOptimizerExtension` is shared across concurrent requests in singleton factory configurations. Verified that `on_execute` clears context stashes via [`clear_optimizer_context`][optimizer-context], sets active optimizer and strategy ContextVars, initializes per-execution dictionary caches (`_cache_key_parts_cache`, `_execution_plan_cache`, `converted_selections_cache`), arms strictness and relation tracking, and tears down all state in exact reverse order in `finally`.
   - **Root Gating & Sync/Async Resolver Parity:** Re-verified that `resolve` gates planning strictly on `info.path.prev is None` and handles awaitables via `_async_optimize` without duplicating planning logic. Re-verified `_optimize` Manager coercion via [`normalize_query_source`][utils-querysets] and evaluated queryset bypass (G1 guard on `_result_cache is not None`).
   - **Plan Construction, Cache Tiers & AST Analysis:** Re-verified `apply_to`, `_get_or_build_plan`, and `_build_cache_key`. Confirmed Tier 1 cross-request LRU caching with bounded capacity (`_MAX_PLAN_CACHE_SIZE = 256`), Tier 2 per-execution memoization (`_execution_plan_cache`) for uncacheable plans during nested fallback connections, cross-request document text/variable-name memoization (`_doc_key_cache`), and single-pass AST traversal in `_walk_cache_relevant_vars` for directive and nested pagination variables. Re-verified structural freezing in `_freeze_variable_value` against [`_SAFE_CACHE_SCALAR_TYPES`][optimizer-extension] and opaque token fallbacks with cycle detection.
   - **Context Stashes & External Cooperation:** Re-verified sentinel stashing in `_publish_plan_to_context` and set unioning via `_stash_union` with subset early-out (`new <= existing`). Re-verified public cooperation point [`apply_connection_optimization`][optimizer-extension] and selection extractors ([`_root_child_selections`][optimizer-extension], [`_connection_node_child_selections`][optimizer-extension], [`mutation_payload_child_selections`][optimizer-extension]).

2. **Mandatory 5-Axis Matrix Discharge:**
   - *Cross-flavor policy mirroring:* Verified. `DjangoOptimizerExtension` is the singular root planner; connection fields, mutation resolvers, and list fields all reuse `apply_connection_optimization` or `_optimize`/`apply_to` without duplicate AST walkers or plan caches.
   - *Sync and async twins:* Verified. `resolve` transparently unifies sync and async resolver execution via `inspect.isawaitable`; `on_execute` and helper functions operate synchronously and identically across sync and async engines.
   - *Derived rather than repeated knowledge:* Verified. `_walk_cache_relevant_vars` derives directive and pagination variables in a single AST descent; `_doc_cache_entry` pairs document key and variable names; `_PAGINATION_ARG_NAMES` and `_SAFE_CACHE_SCALAR_TYPES` serve as authoritative sources of truth.
   - *Inverse and round-trip pairs:* Verified. Symmetric setup and teardown in `on_execute` (`begin_*` / `end_*`, `ContextVar.set` / `reset`), and cycle tracking in `_freeze_variable_value` (`add` / `remove`).
   - *Contracts restated in another medium:* Verified. Aligned across code, specifications ([spec-002][spec-002], [spec-004][spec-004], [spec-030][spec-030], [spec-033][spec-033], [spec-035][spec-035], [spec-036][spec-036], [spec-044][spec-044], [spec-051][spec-051]), tests ([`tests/optimizer/test_extension.py`][test-optimizer-extension], [`tests/test_connection.py`][test-connection], [`tests/mutations/test_resolvers.py`][test-mutations-resolvers], [`tests/types/test_resolvers.py`][test-types-resolvers]), and documentation ([`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook]).

3. **Single-Edit-Site Counts:**
   - Posited changes 1–5 confirmed with single-edit-site counts of 1 at their authoritative root owners.

4. **Tooling & Test Gate:**
   - Executed `export_dry_review.py check --target django_strawberry_framework/optimizer/extension.py --review docs/dry/dry-file-optimizer__extension.md --include-constants` (38 target definitions covered).
   - Test suites in `tests/optimizer/test_extension.py`, `tests/test_connection.py`, and `tests/mutations/test_resolvers.py` pass cleanly (311 tests passing).

Status verified.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[lifecycle-html]: ../../LIFECYCLE.html

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-002]: ../SPECS/spec-002-optimizer-0_0_2.md
[spec-004]: ../SPECS/spec-004-optimizer_beyond-0_0_3.md
[spec-030]: ../SPECS/spec-030-connection_field-0_0_9.md
[spec-033]: ../SPECS/spec-033-connection_optimizer-0_0_9.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-036]: ../SPECS/spec-036-mutations-0_0_10.md
[spec-044]: ../SPECS/spec-044-debug_extension-0_0_14.md
[spec-051]: ../SPECS/spec-051-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection-fields]: ../../django_strawberry_framework/connection/fields.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[optimizer-context]: ../../django_strawberry_framework/optimizer/_context.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-hints]: ../../django_strawberry_framework/optimizer/hints.py
[optimizer-nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py
[optimizer-selections]: ../../django_strawberry_framework/optimizer/selections.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[registry]: ../../django_strawberry_framework/registry.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[utils-context]: ../../django_strawberry_framework/utils/context.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[test-connection]: ../../tests/test_connection.py
[test-mutations-resolvers]: ../../tests/mutations/test_resolvers.py
[test-optimizer-extension]: ../../tests/optimizer/test_extension.py
[test-types-resolvers]: ../../tests/types/test_resolvers.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
