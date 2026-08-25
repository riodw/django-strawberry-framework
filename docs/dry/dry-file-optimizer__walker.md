# DRY review: `django_strawberry_framework/optimizer/walker.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/walker.py` is the AST selection tree walker and query plan compiler for GraphQL operations ([spec-002][spec-002], [spec-004][spec-004], [spec-010][spec-010], [spec-016][spec-016], [spec-018][spec-018], [spec-023][spec-023], [spec-025][spec-025], [spec-028][spec-028], [spec-033][spec-033], [spec-035][spec-035], [spec-045][spec-045], [spec-051][spec-051], [spec-063][spec-063]). It traverses parsed GraphQL selection ASTs against Django ORM models and registered `DjangoType` definitions, transforming hierarchical selection trees into flat and nested ORM optimization directives encapsulated in an immutable [`OptimizationPlan`][optimizer-plans].

It owns the following architectural responsibilities:

1. **Root Planning Entry Point & G2 Operation-Wide Projection Gating:**
   - [`plan_optimizations`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::plan_optimizations`): The public planning entry point invoked by the execution extension ([`DjangoOptimizerExtension`][optimizer-extension]). It derives the G2 operation-wide projection gate ([`_enable_only_for_operation`][optimizer-walker]), instantiates a mutable [`OptimizationPlan`][optimizer-plans], initiates the recursive descent via [`_walk_selections`][optimizer-walker], and seals the plan via [`OptimizationPlan.finalize`][optimizer-plans] so subsequent post-handoff mutation raises `AttributeError`.
   - [`_enable_only_for_operation`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_enable_only_for_operation`): Evaluates the G2 projection gate ([spec-035][spec-035] Decision 4). Only `OperationType.QUERY` operations enable `.only(...)` column projections; `MUTATION` and `SUBSCRIPTION` operations suppress projection across the entire plan tree to eliminate deferred-field refetch and deferred-`save()` hazards on mutation return instances.

2. **GraphQL Selection Resolution & Lossy Reversal Mitigation:**
   - [`_schema_name_converter`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_schema_name_converter`): Extracts the active Strawberry `NameConverter` from GraphQL execution `info` via [`schema_config_from_info`][utils-typing].
   - [`_graphql_names_by_python_name`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_graphql_names_by_python_name`): Builds authoritative GraphQL field names for a `DjangoType` subclass, honoring custom name converters or defaulting to `to_camel_case`.
   - [`_field_by_graphql_name`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_field_by_graphql_name`): Performs forward-resolution of GraphQL selection names to real Django field names when reverse `snake_case` mapping is lossy (e.g. digit boundaries such as `address_2` $\rightarrow$ `address2` $\rightarrow$ `address2` $\neq$ `address_2`, or custom schema converters).
   - [`_resolve_selection_target`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_resolve_selection_target`): Dispatches incoming selection names across synthesized nested connection attributes (`relation_connections`) and physical model fields (`field_map`).
   - [`_resolve_field_map`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_resolve_field_map`): Retrieves `(type_cls, definition, field_map)` for a model, preferring canonical definition metadata (`DjangoTypeDefinition.field_map`) and falling back to [`FieldMeta.from_django_field`][optimizer-field-meta] over `model._meta.get_fields()`. Supports root `source_type` overrides for secondary types while routing nested relations through primary types ([spec-018][spec-018]).
   - [`_resolve_relation_target`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_resolve_relation_target`): Resolves the relation target type, preferring `definition.related_target_for` before falling back to [`registry.get(related_model)`][registry].
   - [`_resolve_optimizer_hints`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_resolve_optimizer_hints`): Extracts schema-level [`OptimizerHint`][optimizer-hints] declarations from definition metadata.

3. **AST Recursive Descent & Node Processing:**
   - [`_walk_selections`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_walk_selections`): Recursive workhorse traversing normalized selections ([`included_field_selections`][optimizer-selections], [`_merge_aliased_selections`][optimizer-walker]). It projects scalar fields into `plan.only_fields`, resolves custom PK columns for Relay Node types (`id_attr`), ignores unhinted consumer-assigned relation fields, applies optimizer hints via [`_apply_hint`][optimizer-walker], delegates nested connections via [`_plan_connection_relation`][optimizer-walker], and dispatches single/multi-valued relations via [`_dispatch_single_relation`][optimizer-walker].
   - [`plan_relation`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::plan_relation`): Pure classification helper determining relation traversal kind (`"prefetch"` vs `"select"`) based on custom `get_queryset` hooks (`_target_has_custom_get_queryset`) and relation cardinality (`is_many_side_relation_kind`).
   - [`_target_has_custom_get_queryset`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_target_has_custom_get_queryset`): Checks if the target type overrides `get_queryset`.
   - [`_dispatch_single_relation`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_dispatch_single_relation`): Unified dispatcher routing relation selections to [`_plan_prefetch_relation`][optimizer-walker] or [`_plan_select_relation`][optimizer-walker].

4. **Relation Directives, Prefetch Compilation & Child Plan Absorption:**
   - [`_plan_select_relation`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_plan_select_relation`): Plans same-query `select_related` paths, evaluates FK-id JOIN elisions ([`_selected_scalar_names`][optimizer-walker], [`_has_custom_id_resolver`][optimizer-walker]), records ledger keys ([`_record_select_path_keys`][optimizer-walker]), and recurses for child selections with double-underscore (`__`) query prefixes.
   - [`_plan_prefetch_relation`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_plan_prefetch_relation`): Plans multi-valued/custom-queryset relation traversals with `prefetch_related(Prefetch(...))`, resolves instance accessors via [`instance_accessor`][utils-relations], marks plans non-cacheable on custom `get_queryset`, builds child querysets via [`_build_prefetch_child_queryset`][optimizer-walker], and tracks ledger resolver keys ([`_record_prefetch_path_keys`][optimizer-walker]).
   - [`_record_relation_access`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_record_relation_access`): Records relation FK column attnames into `plan.only_fields` (gated by `enable_only`) and appends resolver identities into `plan.planned_resolver_keys`.
   - [`_build_child_queryset`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_build_child_queryset`): Constructs the base child queryset on `related_model._default_manager.all()` and applies type visibility synchronously via [`apply_type_visibility_sync`][utils-querysets].
   - [`_build_prefetch_child_queryset`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_build_prefetch_child_queryset`): Builds base queryset and forwards to child compilation.
   - [`_build_prefetch_child_queryset_from_base`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_build_prefetch_child_queryset_from_base`): Executes isolated child selection walking (`child_plan = OptimizationPlan()`), ensures connector columns ([`_ensure_connector_only_fields`][optimizer-walker]), absorbs child metadata into parent plan ([`_absorb_child_plan`][optimizer-walker]), and applies child directives via `child_plan.apply(base_queryset)`.
   - [`_absorb_child_plan`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_absorb_child_plan`): Merges child plan metadata (`merge_metadata_from`) into the parent plan, propagating non-cacheability and resolver keys.
   - [`_ensure_connector_only_fields`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_ensure_connector_only_fields`): Injects foreign key connector and generic foreign key morph columns (`prefetch_attach_columns`) from [`classify_relation_join`][optimizer-join-taxonomy] into `child_plan.only_fields`.

5. **Optimizer Hint Engine & Consumer Prefetch Rebasing:**
   - [`_apply_hint`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_apply_hint`): Evaluates Meta-level [`OptimizerHint`][optimizer-hints] declarations (`SKIP`, `prefetch_obj`, `force_select`, `force_prefetch`). Validates consumer prefetches, forbids unsupported `to_attr` usage on generated resolvers, marks plans non-cacheable, binds resolver keys, and raises descriptive [`ConfigurationError`][exceptions] on misconfigurations.
   - [`_prefetch_hint_for_path`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_prefetch_hint_for_path`): Validates and rebases type-relative consumer `Prefetch` lookup paths to absolute nested query paths.

6. **FK-ID Elision Optimization:**
   - [`_selected_scalar_names`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_selected_scalar_names`): Inspects single-valued relation child selections to determine if only the target PK scalar is requested, allowing JOIN elision.
   - [`_has_custom_id_resolver`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_has_custom_id_resolver`): Checks if the target type defines a custom resolver for the target PK field (via `definition.has_custom_id_resolver_for` or [`origin_has_custom_id_resolver`][types-definition]), ensuring elision only occurs when safe.

7. **Aliased Selection Merging & Nested Connection Delegation:**
   - [`_merge_aliased_selections`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_merge_aliased_selections`): Combines duplicate field selections while preserving distinct response keys (`_optimizer_response_keys`), runtime prefixes (`_optimizer_runtime_prefixes`), and per-response-key argument payloads (`_optimizer_response_key_arguments`). Features a fast-path zero-copy passthrough when all field names are unique.
   - [`_record_response_key_arguments`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_record_response_key_arguments`): Records arguments under response keys and detects argument conflicts (`_optimizer_response_key_argument_conflict`) across merged parent aliases.
   - [`_normalized_alias_payload`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_normalized_alias_payload`): Normalizes integer pagination bounds (`first`, `last`) via [`_coerce_pagination_int`][optimizer-nested-planner] for accurate payload equality comparison.
   - [`_response_key_arguments_conflict`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_response_key_arguments_conflict`): Predicate testing whether conflicting arguments exist under a single response key.
   - [`_aliased_arguments_diverge`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_aliased_arguments_diverge`): Predicate testing whether aliases carry divergent arguments to trigger per-key window planning.
   - [`_selection_runtime_prefixes`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_selection_runtime_prefixes`) & [`_merge_runtime_prefixes`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_merge_runtime_prefixes`): Manages selection-specific runtime prefix sets.
   - [`_plan_connection_relation`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_plan_connection_relation`): Delegates nested Relay connection planning to [`nested_planner.py::plan_connection_relation`][optimizer-nested-planner] and atomically merges results into the parent plan.

8. **Resolver Key Path Ledgers:**
   - [`_record_path_resolver_keys`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_record_path_resolver_keys`): Appends unique resolver identities onto path ledgers.
   - [`_record_prefetch_path_keys`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_record_prefetch_path_keys`): Associates resolver keys with prefetch lookup paths.
   - [`_record_select_path_keys`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_record_select_path_keys`): Associates resolver keys with select lookup paths.
   - [`_resolver_identities_for`][optimizer-walker] (`django_strawberry_framework/optimizer/walker.py::_resolver_identities_for`): Computes cartesian product of runtime prefixes and response keys to generate canonical [`resolver_key`][optimizer-plans] identities.

Connected behavior examined:
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]: Invokes [`plan_optimizations`][optimizer-walker] and [`plan_relation`][optimizer-walker] during query execution and plan caching.
- [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans]: Receives directive appends ([`append_unique`][optimizer-plans], [`append_unique_many`][optimizer-plans], [`append_prefetch_unique`][optimizer-plans]), metadata merging ([`OptimizationPlan.merge_metadata_from`][optimizer-plans], [`OptimizationPlan.merge_from`][optimizer-plans]), and finalization ([`OptimizationPlan.finalize`][optimizer-plans]).
- [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner]: Consumes connection delegation from [`_plan_connection_relation`][optimizer-walker] and supplies pagination coercion ([`_coerce_pagination_int`][optimizer-nested-planner]).
- [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections]: Supplies fragment filtering ([`included_field_selections`][optimizer-selections]), response key extraction ([`response_key`][optimizer-selections], [`response_keys`][optimizer-selections]), and fragment inspection ([`is_fragment`][optimizer-selections]).
- [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy]: Classifies relation join taxonomy and provides prefetch connector attach columns consumed by [`_ensure_connector_only_fields`][optimizer-walker].
- [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta]: Provides normalized [`FieldMeta`][optimizer-field-meta] descriptors for fallback field maps.
- [`django_strawberry_framework/optimizer/hints.py`][optimizer-hints]: Supplies [`OptimizerHint`][optimizer-hints] definitions and [`hint_is_skip`][optimizer-hints].
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Provides synchronous type visibility enforcement ([`apply_type_visibility_sync`][utils-querysets]).
- [`django_strawberry_framework/utils/relations.py`][utils-relations]: Provides instance accessor and relation kind resolution ([`instance_accessor`][utils-relations], [`relation_kind`][utils-relations], [`is_many_side_relation_kind`][utils-relations]).
- [`tests/optimizer/test_walker.py`][test-optimizer-walker]: Comprehensive integration and unit test suite verifying AST walking, aliases, G2 gates, hints, FK-id elision, custom ID resolvers, and prefetch compilation.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/walker.py --include-constants`):
- Parsed 1 target file, 1443 lines.
- Inventory of 37 definitions:
  - 37 functions: [`_record_path_resolver_keys`][optimizer-walker], [`_record_prefetch_path_keys`][optimizer-walker], [`_record_select_path_keys`][optimizer-walker], [`_enable_only_for_operation`][optimizer-walker], [`plan_optimizations`][optimizer-walker], [`plan_relation`][optimizer-walker], [`_target_has_custom_get_queryset`][optimizer-walker], [`_schema_name_converter`][optimizer-walker], [`_graphql_names_by_python_name`][optimizer-walker], [`_field_by_graphql_name`][optimizer-walker], [`_resolve_selection_target`][optimizer-walker], [`_resolve_field_map`][optimizer-walker], [`_resolve_relation_target`][optimizer-walker], [`_resolve_optimizer_hints`][optimizer-walker], [`_build_child_queryset`][optimizer-walker], [`_resolver_identities_for`][optimizer-walker], [`_walk_selections`][optimizer-walker], [`_dispatch_single_relation`][optimizer-walker], [`_plan_select_relation`][optimizer-walker], [`_plan_prefetch_relation`][optimizer-walker], [`_record_relation_access`][optimizer-walker], [`_build_prefetch_child_queryset`][optimizer-walker], [`_build_prefetch_child_queryset_from_base`][optimizer-walker], [`_apply_hint`][optimizer-walker], [`_prefetch_hint_for_path`][optimizer-walker], [`_absorb_child_plan`][optimizer-walker], [`_selected_scalar_names`][optimizer-walker], [`_has_custom_id_resolver`][optimizer-walker], [`_ensure_connector_only_fields`][optimizer-walker], [`_merge_aliased_selections`][optimizer-walker], [`_record_response_key_arguments`][optimizer-walker], [`_normalized_alias_payload`][optimizer-walker], [`_response_key_arguments_conflict`][optimizer-walker], [`_aliased_arguments_diverge`][optimizer-walker], [`_selection_runtime_prefixes`][optimizer-walker], [`_merge_runtime_prefixes`][optimizer-walker], [`_plan_connection_relation`][optimizer-walker].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `walker.py` provides unified selection walking and plan generation across all field flavors:
   - Scalar and Relation Fields: Uniformly projected and traversed across standard models, abstract inheritance hierarchies, and multi-table models.
   - Single-valued vs. Multi-valued Relations: Distinctly planned via [`plan_relation`][optimizer-walker] and [`_dispatch_single_relation`][optimizer-walker] while sharing connector column projection ([`_record_relation_access`][optimizer-walker]) and resolver identity attribution ([`_resolver_identities_for`][optimizer-walker]).
   - Nested Connections: Delegated to [`nested_planner.py::plan_connection_relation`][optimizer-nested-planner] via [`_plan_connection_relation`][optimizer-walker], maintaining a single transactional nested connection engine.
   - Relay Custom PK ID: Custom ID attribute resolution (`id_attr`) in [`_walk_selections`][optimizer-walker] mirrors [`types/resolvers.py`][types-resolvers] logic for custom node IDs, avoiding N+1 lazy loads.
   - Name Conversion: Authoritative GraphQL names are resolved via [`_schema_name_converter`][optimizer-walker] and [`_graphql_names_by_python_name`][optimizer-walker], mirroring Strawberry's schema conversion rules.
   - Type Visibility: Prefetch child querysets apply [`apply_type_visibility_sync`][utils-querysets], sharing the exact visibility policy enforced at resolver execution.

2. **Sync and async twins:**
   Zero duplication. Selection walking and query plan compilation in `walker.py` are strictly synchronous and side-effect-free AST evaluations producing backend-neutral [`OptimizationPlan`][optimizer-plans] instances. Plan-time prefetch visibility routing via [`apply_type_visibility_sync`][utils-querysets] enforces clean failure (`SyncMisuseError`) when an async-only `get_queryset` is encountered in synchronous walker compilation, preventing coroutines from leaking into plan directives.

3. **Derived rather than repeated knowledge:**
   - G2 Operation Projection Gate: Derived once at root in [`plan_optimizations`][optimizer-walker] via [`_enable_only_for_operation`][optimizer-walker] and threaded as `enable_only: bool` through all recursive calls ([`_walk_selections`][optimizer-walker], [`_dispatch_single_relation`][optimizer-walker], [`_plan_select_relation`][optimizer-walker], [`_plan_prefetch_relation`][optimizer-walker], [`_build_prefetch_child_queryset`][optimizer-walker], [`_ensure_connector_only_fields`][optimizer-walker], [`_apply_hint`][optimizer-walker], [`_plan_connection_relation`][optimizer-walker]), preventing repeated `info.operation` inspections.
   - Attach Projection Columns: Derived dynamically from [`RelationJoinDescriptor.prefetch_attach_columns`][optimizer-join-taxonomy] via [`_ensure_connector_only_fields`][optimizer-walker].
   - Instance Accessors: Dynamically computed via [`instance_accessor`][utils-relations] for prefetch lookups.
   - Relation Target Types: Derived from definition metadata (`definition.related_target_for`) before falling back to [`registry.get(related_model)`][registry].
   - Resolver Identities: Computed dynamically via [`resolver_key`][optimizer-plans] across the cartesian product of runtime prefixes and response keys in [`_resolver_identities_for`][optimizer-walker].

4. **Inverse and round-trip pairs:**
   - Forward Name Resolution: [`_field_by_graphql_name`][optimizer-walker] inverts lossy `snake_case` reversals (e.g. digit boundaries) by forward-matching GraphQL candidate names against `field_map`.
   - Consumer Prefetch Rebasing: [`_prefetch_hint_for_path`][optimizer-walker] transforms type-relative lookups into absolute nested query paths.
   - Transactional Child Plan Absorption: Isolated child plans are constructed via `child_plan = OptimizationPlan()` and merged into parent plans via [`_absorb_child_plan`][optimizer-walker] / [`OptimizationPlan.merge_metadata_from`][optimizer-plans].
   - Path Ledgers: Directives and resolver keys are coupled via [`_record_select_path_keys`][optimizer-walker] and [`_record_prefetch_path_keys`][optimizer-walker] so downstream pruning ([`prune_unsupportable_select_related`][optimizer-plans]) can cleanly strip corresponding keys.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker], [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension], [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner], [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans], [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections], [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy], [`django_strawberry_framework/optimizer/field_meta.py`][optimizer-field-meta], [`django_strawberry_framework/optimizer/hints.py`][optimizer-hints], [`django_strawberry_framework/utils/querysets.py`][utils-querysets], [`django_strawberry_framework/utils/relations.py`][utils-relations];
   - Specifications: [spec-002][spec-002], [spec-004][spec-004], [spec-010][spec-010], [spec-016][spec-016], [spec-018][spec-018], [spec-023][spec-023], [spec-025][spec-025], [spec-028][spec-028], [spec-033][spec-033], [spec-035][spec-035], [spec-045][spec-045], [spec-051][spec-051], [spec-063][spec-063];
   - Test suites: [`tests/optimizer/test_walker.py`][test-optimizer-walker] (extensive suite validating walker execution, aliased selections, hint dispatch, FK-id elision, G2 gate, digit boundaries, consumer-assigned relations, and custom ID resolvers), [`tests/optimizer/test_definition_order.py`][test-optimizer-definition-order], [`tests/optimizer/test_multi_db.py`][test-optimizer-multi-db], [`tests/optimizer/test_nested_fetch.py`][test-optimizer-nested-fetch], [`tests/optimizer/test_extension.py`][test-optimizer-extension];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Modifying the G2 projection gate to disable `.only()` projection for a new custom operation type):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker] ([`_enable_only_for_operation`][optimizer-walker]).
  - *Site count:* 1 in target.
- **Posited change 2 (Adjusting the digit-boundary / lossy name reversal fallback policy):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker] ([`_field_by_graphql_name`][optimizer-walker]).
  - *Site count:* 1 in target.
- **Posited change 3 (Modifying the FK-id JOIN elision criteria to require additional safety checks):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker] ([`_plan_select_relation`][optimizer-walker] / [`_selected_scalar_names`][optimizer-walker]).
  - *Site count:* 1 in target.
- **Posited change 4 (Changing how consumer-assigned relation hints are validated or handled):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker] ([`_apply_hint`][optimizer-walker]).
  - *Site count:* 1 in target.
- **Posited change 5 (Adjusting the fast-path selection deduplication check for aliased selections):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker] ([`_merge_aliased_selections`][optimizer-walker]).
  - *Site count:* 1 in target.

### Rejected candidates

1. **Inlining nested connection planning logic directly into `_walk_selections`:**
   - Disproved per [spec-033][spec-033]. Nested connection planning entails complex window derivation, strategy selection, keyset cursor context, and composite index advisories. Delegating to [`nested_planner.py::plan_connection_relation`][optimizer-nested-planner] isolates connection complexity and keeps `walker.py` focused on AST traversal.
2. **Re-reading `info.operation` independently at every scalar and relation projection site:**
   - Disproved per [spec-035][spec-035] Decision 4. The operation type is an invariant of the GraphQL execution. Deriving `enable_only` once in [`plan_optimizations`][optimizer-walker] and threading it ensures root plans, child plans, and nested connection windows share a single consistent projection gate.
3. **Guessing model field names from camelCase without forward schema verification:**
   - Disproved per [spec-035][spec-035]. Digit boundaries (`address_2` $\rightarrow$ `address2`) break naive snake_case inversion. Using [`_field_by_graphql_name`][optimizer-walker] with schema name converter matching prevents unresolvable fields and phantom lazy loads.
4. **Planning consumer-assigned relation fields without explicit optimizer hints:**
   - Disproved per [spec-033][spec-033] Decision 6 (the strawberry-django #697 bug class). Speculative prefetching on consumer-assigned resolvers risks executing unconsumed queries and silences strictness checks for per-parent lazy loads. Leaving consumer-assigned relations unplanned by default enforces strictness discipline.

## Opportunities

None — `django_strawberry_framework/optimizer/walker.py` is a mature, highly refined, and strictly factored AST query planner (1443 lines). It delegates relational taxonomy to `join_taxonomy.py`, nested connection window compilation to `nested_planner.py`, directive collection and lifecycle to `plans.py`, selection parsing to `selections.py`, and type visibility to `utils/querysets.py`, with zero duplicated policy.

## Judgment

Zero-edit review. `optimizer/walker.py` exhibits complete policy consolidation, robust lossy name reversal handling, unified G2 projection gating, and clean transactional delegation. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/walker.py --review docs/dry/dry-file-optimizer__walker.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 independently audited `django_strawberry_framework/optimizer/walker.py` and traced all connected behavior across the optimizer, selection normalization, relation planning, and test suites.

### Connected behavior & contract verification

1. **AST Selection Traversal & G2 Projection Gate:**
   - Traced [`plan_optimizations`][optimizer-walker] and [`_walk_selections`][optimizer-walker]. Verified that [`_enable_only_for_operation`][optimizer-walker] derives `enable_only` once at the root and threads it through all recursive walks. Under `MUTATION` or `SUBSCRIPTION`, `.only(...)` column appends are bypassed across root and child plans, preventing deferred-field hazards.
   - Verified that finalization (`plan.finalize()`) freezes directive lists into immutable tuples, preventing post-walker mutation.

2. **GraphQL Field Resolution & Digit Boundaries:**
   - Traced [`_resolve_selection_target`][optimizer-walker], [`_graphql_names_by_python_name`][optimizer-walker], and [`_field_by_graphql_name`][optimizer-walker]. Confirmed that when `snake_case(sel.name)` misses (e.g. `address_2` $\rightarrow$ `address2`), forward matching against schema converter names reliably resolves the real Django field descriptor.
   - Verified custom PK `id` projection for Relay `Node` types, confirming that custom `id_attr` values (e.g. `uuid` or `user_id` on OneToOne PKs) are projected as column attnames, preventing avoidable lazy loads on `resolve_id`.

3. **Relation Planning & Cardinality Dispatch:**
   - Inspected [`plan_relation`][optimizer-walker] and [`_dispatch_single_relation`][optimizer-walker]. Confirmed that relations with custom `get_queryset` hooks (`_target_has_custom_get_queryset`) or many-side cardinalities (`is_many_side_relation_kind`) correctly route to [`_plan_prefetch_relation`][optimizer-walker], while clean single-valued relations route to [`_plan_select_relation`][optimizer-walker].
   - Verified FK-id JOIN elision in [`_plan_select_relation`][optimizer-walker], ensuring that when only the target PK scalar is selected and no custom ID resolver exists ([`_has_custom_id_resolver`][optimizer-walker]), the JOIN is elided into `fk_id_elisions` while still loading the parent FK column via [`_record_relation_access`][optimizer-walker].

4. **Prefetch Compilation & Child Plan Isolation:**
   - Verified [`_build_prefetch_child_queryset_from_base`][optimizer-walker]. Child selections are walked using an isolated `child_plan = OptimizationPlan()`. Connector columns (`prefetch_attach_columns`) are injected via [`_ensure_connector_only_fields`][optimizer-walker], and child metadata is absorbed via [`_absorb_child_plan`][optimizer-walker].
   - Verified that custom `get_queryset` targets mark the plan non-cacheable (`plan.cacheable = False`), and child type visibility runs synchronously via [`apply_type_visibility_sync`][utils-querysets].

5. **Aliased Selection Merging & Connection Delegation:**
   - Verified [`_merge_aliased_selections`][optimizer-walker] fast-path optimization (zero-copy when names are distinct) and slow-path argument/prefix tracking.
   - Verified that conflicting argument payloads under the same response key ([`_response_key_arguments_conflict`][optimizer-walker]) fall back to per-parent resolution, while divergent arguments across aliases ([`_aliased_arguments_diverge`][optimizer-walker]) trigger per-response-key window planning.
   - Verified that nested Relay connections delegate cleanly to [`nested_planner.py::plan_connection_relation`][optimizer-nested-planner] via [`_plan_connection_relation`][optimizer-walker].

6. **Matrix & Single-Edit Site Verification:**
   - All 5 probing axes (cross-flavor policy mirroring, sync/async twins, derived knowledge, inverse/round-trip pairs, contracts restated in another medium) are verified and discharged.
   - Single-edit-site counts hold at 1 for all posited changes.
   - Inventory coverage confirmed: 37 definitions (37 functions) fully covered.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-002]: ../SPECS/spec-002-optimizer-0_0_2.md
[spec-004]: ../SPECS/spec-004-optimizer_beyond-0_0_3.md
[spec-010]: ../SPECS/appx/spec-010-foundation-0_0_4-rationale.md
[spec-016]: ../SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md
[spec-018]: ../SPECS/appx/spec-018-nested_type_resolution-0_0_6-rationale.md
[spec-023]: ../SPECS/appx/spec-023-multi_db-0_0_7-rationale.md
[spec-025]: ../SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-033]: ../SPECS/spec-033-nested_connection_execution_plan-0_0_9.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-045]: ../SPECS/appx/spec-045-visibility_boundary-0_0_14-rationale.md
[spec-051]: ../SPECS/spec-051-boundary_dry_squeeze-0_0_15.md
[spec-063]: ../SPECS/spec-063-structural_templates-0_1_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[optimizer-hints]: ../../django_strawberry_framework/optimizer/hints.py
[optimizer-join-taxonomy]: ../../django_strawberry_framework/optimizer/join_taxonomy.py
[optimizer-nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[optimizer-nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py
[optimizer-selections]: ../../django_strawberry_framework/optimizer/selections.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[registry]: ../../django_strawberry_framework/registry.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[test-optimizer-definition-order]: ../../tests/optimizer/test_definition_order.py
[test-optimizer-extension]: ../../tests/optimizer/test_extension.py
[test-optimizer-field-meta]: ../../tests/optimizer/test_field_meta.py
[test-optimizer-hints]: ../../tests/optimizer/test_hints.py
[test-optimizer-join-taxonomy]: ../../tests/optimizer/test_join_taxonomy.py
[test-optimizer-multi-db]: ../../tests/optimizer/test_multi_db.py
[test-optimizer-nested-fetch]: ../../tests/optimizer/test_nested_fetch.py
[test-optimizer-nested-planner]: ../../tests/optimizer/test_nested_planner.py
[test-optimizer-plans]: ../../tests/optimizer/test_plans.py
[test-optimizer-walker]: ../../tests/optimizer/test_walker.py
[test-relay-connection]: ../../tests/test_relay_connection.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
