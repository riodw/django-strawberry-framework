# DRY review: `django_strawberry_framework/optimizer/plans.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/plans.py` is the canonical definition and execution engine for query optimization directives, metadata tracking, plan merging, consumer-queryset reconciliation, total ordering determinism, and SQL window pagination ([spec-002][spec-002], [spec-003][spec-003], [spec-004][spec-004], [spec-028][spec-028], [spec-033][spec-033], [spec-035][spec-035], [spec-051][spec-051]). It defines the [`OptimizationPlan`][optimizer-plans] data carrier constructed during AST walking ([`optimizer/walker.py`][optimizer-walker] and [`optimizer/nested_planner.py`][optimizer-nested-planner]) and consumed by the execution middleware ([`optimizer/extension.py`][optimizer-extension]) and connection pipeline ([`connection.py`][connection]).

It owns the following architectural responsibilities:

1. **Directive Collection & Deduplication Infrastructure:**
   - [`_lookup_path`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_lookup_path`): Centralizes extraction of Django's internal `prefetch_to` lookup path from plain string or `Prefetch` instances so a future Django rename has exactly one site to update.
   - [`_IndexedList`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_IndexedList`): Custom `list` subclass maintaining an internal `_seen: set` sidecar for $O(1)$ membership checks during directive accumulation:
     - [`_IndexedList.__init__`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_IndexedList.__init__`): Initializes list and sidecar index, accepting an optional `key` extractor (e.g. `_lookup_path`).
     - [`_IndexedList.append_unique`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_IndexedList.append_unique`): Inlined single-`try` unique append helper running $O(1)$ on hashable keys with graceful linear membership fallback on unhashable types.
     - [`_IndexedList.append`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_IndexedList.append`): Standard append updating the sidecar index.
     - [`_IndexedList.extend`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_IndexedList.extend`): Standard extend maintaining sidecar index integrity.
   - [`_indexed_list`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_indexed_list`): Factory producing an identity-indexed [`_IndexedList`][optimizer-plans].
   - [`_prefetch_indexed_list`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_prefetch_indexed_list`): Factory producing a [`_lookup_path`][optimizer-plans]-keyed [`_IndexedList`][optimizer-plans].
   - [`append_unique`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::append_unique`): Fast deduplicated append dispatching to [`_IndexedList.append_unique`][optimizer-plans] or sequence membership check.
   - [`append_unique_many`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::append_unique_many`): Iterative sequence append helper.
   - [`append_prefetch_unique`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::append_prefetch_unique`): Prefetch deduplication helper keying on lookup path while allowing distinct `to_attr` aliases on identical paths to coexist.

2. **Core Optimization Plan Dataclass & Lifecycle:**
   - [`OptimizationPlan`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::OptimizationPlan`): Immutable-after-handoff plan container holding optimization directives (`select_related`, `prefetch_related`, `only_fields`), strictness and elision metadata (`fk_id_elisions`, `planned_resolver_keys`, `select_path_resolver_keys`, `prefetch_path_resolver_keys`), cacheability flags (`cacheable`), and finalized immutable membership sets:
     - [`OptimizationPlan.is_empty`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::OptimizationPlan.is_empty`): Property returning `True` when no optimization directives or resolver keys were collected, isolating the `cacheable` metadata flag.
     - [`OptimizationPlan.finalize`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::OptimizationPlan.finalize`): Swaps mutable lists for immutable tuples and precomputes frozen sets (`finalized_fk_id_elisions`, `finalized_planned_resolver_keys`, `finalized_lookup_paths`) so post-handoff mutation raises `AttributeError`.
     - [`OptimizationPlan.apply`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::OptimizationPlan.apply`): Applies collected directives to a Django `QuerySet` in strict canonical order: `only()` $\rightarrow$ `select_related()` $\rightarrow$ `prefetch_related()`.
     - [`OptimizationPlan.merge_from`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::OptimizationPlan.merge_from`): Commits all directives and coupled metadata from a construction-time sub-plan into the parent plan at transactional planner boundaries.
     - [`OptimizationPlan.merge_metadata_from`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::OptimizationPlan.merge_metadata_from`): Merges accepted child-queryset metadata (`fk_id_elisions`, `planned_resolver_keys`, `cacheable`) without merging child-scoped query directives.
     - [`OptimizationPlan._assert_under_construction`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::OptimizationPlan._assert_under_construction`): Rejection guard preventing plan mutations or merges once [`OptimizationPlan.finalize`][optimizer-plans] has published immutable metadata.
     - [`OptimizationPlan._assert_merge_field_inventory`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::OptimizationPlan._assert_merge_field_inventory`): Class-level self-audit ensuring every dataclass field is explicitly classified into `_FULL_MERGE_FIELDS`, `_METADATA_MERGE_FIELDS`, or `_DERIVED_FINALIZED_FIELDS`.

3. **Resolver Identity & GraphQL Path Utilities:**
   - [`resolver_key`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::resolver_key`): Constructs canonical branch-sensitive resolver identity strings (`"Type.field@path"` or `"field@path"`).
   - [`runtime_path_from_info`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::runtime_path_from_info`): Extracts GraphQL runtime path from `info.path` with `None` safety.
   - [`_MAX_PATH_DEPTH`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_MAX_PATH_DEPTH`): Constant (1024) bounding AST path traversal against cyclic or corrupted linked-list structures.
   - [`runtime_path_from_path`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::runtime_path_from_path`): Walks `path.prev` linked-lists while stripping integer list indices to yield stable structural path tuples.

4. **Django Deferred Loading & QuerySet Projection Inspection:**
   - [`deferred_loading_of`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::deferred_loading_of`): The singular reader of Django's private `QuerySet.query.deferred_loading` tuple `(field_set, defer_flag)`, normalizing `.only()` vs `.defer()` mode with exception safety.
   - [`_consumer_only_fields`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_consumer_only_fields`): Extracts the consumer's restricted column set when `.only()` is active.
   - [`_consumer_projection`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_consumer_projection`): Extracts `(names, defer_mode)` projection state for both `.only()` and `.defer()` querysets.
   - [`_select_path_traversable`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_select_path_traversable`): Verifies whether each segment of a `select_related` path is traversable under the consumer's `.only()` / `.defer()` projection.
   - [`prune_unsupportable_select_related`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::prune_unsupportable_select_related`): B8 reconciliation dropping `select_related` paths blocked by consumer column projections (preventing `FieldError: Field cannot be both deferred and traversed`) along with coupled resolver keys and nested only fields.
   - [`_flatten_select_related`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_flatten_select_related`): Flattens Django's `query.select_related` dict into dotted path strings, treating wildcard `True` as non-overlapping.
   - [`_consumer_prefetch_lookups`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_consumer_prefetch_lookups`): Safely reads `_prefetch_related_lookups` from querysets.
   - [`_optimizer_can_absorb`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_optimizer_can_absorb`): Determines if an optimizer `Prefetch` can losslessly replace consumer bare string prefetch lookups.

5. **Deterministic Total Ordering & Keyset Invariants:**
   - [`order_entry_name_and_direction`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::order_entry_name_and_direction`): Single parser for `order_by` vocabulary (strings with leading `-`, `OrderBy` expressions, bare `F` expressions) into `(field_name, descending)`.
   - [`order_entry_has_explicit_nulls`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::order_entry_has_explicit_nulls`): Predicate testing whether an `OrderBy` expression specifies explicit `nulls_first` or `nulls_last`.
   - [`ends_in_unique_column`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::ends_in_unique_column`): Determines whether an ordering ends in a unique, non-nullable column (pk or non-nullable `unique=True` field).
   - [`deterministic_order`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::deterministic_order`): Appends model primary key as a terminal tiebreaker if not already unique, ensuring SQL ordering is a total order to guarantee cursor parity across window and fallback paths.
   - [`_reverse_order_by`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_reverse_order_by`): Inverts ordering directions and swaps explicit NULLS placement for backward connection pagination without re-invoking the Django SQL compiler.

6. **SQL Window Pagination & Partition Generation:**
   - Package-reserved window annotation constants:
     - [`WINDOW_ROW_NUMBER`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::WINDOW_ROW_NUMBER`): `"_dst_row_number"`.
     - [`WINDOW_TOTAL_COUNT`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::WINDOW_TOTAL_COUNT`): `"_dst_total_count"`.
     - [`WINDOW_ROW_NUMBER_REVERSED`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::WINDOW_ROW_NUMBER_REVERSED`): `"_dst_row_number_reversed"`.
     - [`WINDOW_ROW_NUMBER_ABS`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::WINDOW_ROW_NUMBER_ABS`): `"_dst_row_number_abs"`.
     - [`WINDOW_KEYSET_SEEK_COUNT`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::WINDOW_KEYSET_SEEK_COUNT`): `"_dst_keyset_seek_count"`.
   - [`window_partition_for_prefetch`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::window_partition_for_prefetch`): Shims over [`classify_relation_join`][optimizer-join-taxonomy] to resolve the parent-side partition attribute for reverse FK, reverse M2M, and forward M2M relations.
   - [`apply_window_pagination`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::apply_window_pagination`): Constructs window annotations (`RowNumber()`, `Count(1)`), applies deterministic order, and filters row-number ranges with support for count-free seek, counted seek, count-free `hasNextPage` probes, and disambiguating marker rows.
   - [`_apply_keyset_counted_window`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_apply_keyset_counted_window`): Renders filtered running count windows (`Count("pk", filter=seek_q)`) so pre-seek counts remain accurate in subqueries.

7. **Reconciliation & Diff Pipeline:**
   - [`diff_plan_for_queryset`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::diff_plan_for_queryset`): Reconciles plan directives against optimizations already present on the target queryset (dropping duplicate `select_related`, dropping `only_fields` when consumer `.only()` is present, absorbing or dropping `prefetch_related` subtrees, and stripping dropped resolver keys).
   - [`_diff_select_related`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_diff_select_related`): Drops `select_related` paths already selected on the queryset.
   - [`_diff_prefetch_related`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_diff_prefetch_related`): Reconciles optimizer prefetches against consumer prefetches.
   - [`lookup_paths`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::lookup_paths`): Returns relation lookup paths covered by the plan for debugging and inspection.
   - [`_lookup_paths_from_parts`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_lookup_paths_from_parts`): Merges `select_related` paths with flattened `prefetch_related` lookup paths.
   - [`_prefetch_lookup_paths`][optimizer-plans] (`django_strawberry_framework/optimizer/plans.py::_prefetch_lookup_paths`): Recursively flattens nested `Prefetch` querysets and string lookups into dotted path strings.

Connected behavior examined:
- [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]: Consumes [`OptimizationPlan`][optimizer-plans], runs [`diff_plan_for_queryset`][optimizer-plans] and [`prune_unsupportable_select_related`][optimizer-plans], and applies optimizations to root querysets via [`OptimizationPlan.apply`][optimizer-plans].
- [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: Constructs root [`OptimizationPlan`][optimizer-plans], invokes [`resolver_key`][optimizer-plans], [`runtime_path_from_info`][optimizer-plans], and [`append_unique`][optimizer-plans], and finalizes plans via [`OptimizationPlan.finalize`][optimizer-plans].
- [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner]: Builds transactional sub-plans, merges metadata via [`OptimizationPlan.merge_metadata_from`][optimizer-plans] and [`OptimizationPlan.merge_from`][optimizer-plans], derives ordering via [`deterministic_order`][optimizer-plans], and builds window querysets via [`apply_window_pagination`][optimizer-plans].
- [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch]: Reads [`order_entry_name_and_direction`][optimizer-plans], [`deferred_loading_of`][optimizer-plans], and window constants.
- [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy]: Serves as the join classification engine consumed by [`window_partition_for_prefetch`][optimizer-plans].
- [`django_strawberry_framework/connection.py`][connection]: Re-exports [`ends_in_unique_column`][optimizer-plans] (as `_ends_in_unique_column`), applies [`deterministic_order`][optimizer-plans], and reads `_dst_*` window annotations.
- [`django_strawberry_framework/utils/connections.py`][utils-connections]: Provides [`window_range_plan`][utils-connections] and [`assert_window_fetch_mode`][utils-connections] consumed by [`apply_window_pagination`][optimizer-plans].
- [`tests/optimizer/test_plans.py`][test-optimizer-plans]: Comprehensive unit tests covering plan lifecycle, immutability, ORM diffing, window pagination, deterministic ordering, and select pruning.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/plans.py --include-constants`):
- Parsed 1 target file, 1443 lines.
- Inventory of 50 symbols:
  - 6 constants: [`_MAX_PATH_DEPTH`][optimizer-plans], [`WINDOW_ROW_NUMBER`][optimizer-plans], [`WINDOW_TOTAL_COUNT`][optimizer-plans], [`WINDOW_ROW_NUMBER_REVERSED`][optimizer-plans], [`WINDOW_ROW_NUMBER_ABS`][optimizer-plans], [`WINDOW_KEYSET_SEEK_COUNT`][optimizer-plans].
  - 2 classes: [`_IndexedList`][optimizer-plans], [`OptimizationPlan`][optimizer-plans].
  - 10 methods / class methods / properties: [`_IndexedList.__init__`][optimizer-plans], [`_IndexedList.append_unique`][optimizer-plans], [`_IndexedList.append`][optimizer-plans], [`_IndexedList.extend`][optimizer-plans], [`OptimizationPlan.is_empty`][optimizer-plans], [`OptimizationPlan.finalize`][optimizer-plans], [`OptimizationPlan.apply`][optimizer-plans], [`OptimizationPlan.merge_from`][optimizer-plans], [`OptimizationPlan.merge_metadata_from`][optimizer-plans], [`OptimizationPlan._assert_under_construction`][optimizer-plans], [`OptimizationPlan._assert_merge_field_inventory`][optimizer-plans].
  - 32 functions: [`_lookup_path`][optimizer-plans], [`_indexed_list`][optimizer-plans], [`_prefetch_indexed_list`][optimizer-plans], [`resolver_key`][optimizer-plans], [`runtime_path_from_info`][optimizer-plans], [`runtime_path_from_path`][optimizer-plans], [`_flatten_select_related`][optimizer-plans], [`append_unique`][optimizer-plans], [`append_unique_many`][optimizer-plans], [`append_prefetch_unique`][optimizer-plans], [`_consumer_prefetch_lookups`][optimizer-plans], [`deferred_loading_of`][optimizer-plans], [`_consumer_only_fields`][optimizer-plans], [`prune_unsupportable_select_related`][optimizer-plans], [`_consumer_projection`][optimizer-plans], [`_select_path_traversable`][optimizer-plans], [`_optimizer_can_absorb`][optimizer-plans], [`order_entry_name_and_direction`][optimizer-plans], [`order_entry_has_explicit_nulls`][optimizer-plans], [`ends_in_unique_column`][optimizer-plans], [`deterministic_order`][optimizer-plans], [`window_partition_for_prefetch`][optimizer-plans], [`apply_window_pagination`][optimizer-plans], [`_apply_keyset_counted_window`][optimizer-plans], [`_reverse_order_by`][optimizer-plans], [`diff_plan_for_queryset`][optimizer-plans], [`_diff_select_related`][optimizer-plans], [`_diff_prefetch_related`][optimizer-plans], [`lookup_paths`][optimizer-plans], [`_lookup_paths_from_parts`][optimizer-plans], [`_prefetch_lookup_paths`][optimizer-plans].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   [`OptimizationPlan`][optimizer-plans] is the single universal optimization container across all framework flavors (GraphQL queries, nested connections, windowed prefetches, PostgreSQL LATERAL joins, single-parent fast paths, mutations, and REST framework bridges).
   - [`deferred_loading_of`][optimizer-plans] is the sole reader of Django's internal `QuerySet.query.deferred_loading` contract, serving [`_consumer_only_fields`][optimizer-plans], [`_consumer_projection`][optimizer-plans], and lateral fetch AST compilation without duplicated dictionary or tuple unpacking.
   - [`order_entry_name_and_direction`][optimizer-plans] and [`order_entry_has_explicit_nulls`][optimizer-plans] unify order entry parsing across [`nested_planner.py`][optimizer-nested-planner], [`lateral_fetch.py`][optimizer-lateral-fetch], and [`connection.py`][connection], guaranteeing that string prefixes (`-`) and `OrderBy` expressions are evaluated identically everywhere.
   - [`deterministic_order`][optimizer-plans] and [`ends_in_unique_column`][optimizer-plans] enforce cursor-parity by guaranteeing identical deterministic tiebreaking across plan-time window queries and resolve-time connection slicing.
   - [`window_partition_for_prefetch`][optimizer-plans] delegates to [`classify_relation_join`][optimizer-join-taxonomy], preventing duplicate join partition derivations.
   There is zero duplicate plan policy across flavors.

2. **Sync and async twins:**
   Zero duplication. Plan construction, deduplication, finalization, merging, ORM diffing, and window annotation in `plans.py` are purely synchronous in-memory data structures and Django QuerySet transforms. Both sync and async resolvers/extensions share identical plan objects and execution pipelines without parallel codebases.

3. **Derived rather than repeated knowledge:**
   - [`OptimizationPlan.is_empty`][optimizer-plans] dynamically evaluates presence of directives across `select_related`, `prefetch_related`, `only_fields`, `fk_id_elisions`, and `planned_resolver_keys`.
   - [`OptimizationPlan.finalize`][optimizer-plans] precomputes derived immutable frozensets (`finalized_fk_id_elisions`, `finalized_planned_resolver_keys`, `finalized_lookup_paths`) directly from the collected lists.
   - [`OptimizationPlan._assert_merge_field_inventory`][optimizer-plans] reflects on dataclass fields at module load time to enforce explicit categorization against `_FULL_MERGE_FIELDS`, `_METADATA_MERGE_FIELDS`, and `_DERIVED_FINALIZED_FIELDS`.
   - [`deterministic_order`][optimizer-plans] dynamically checks whether the terminal column is unique via [`ends_in_unique_column`][optimizer-plans], appending `pk.attname` only when non-unique.
   - [`_reverse_order_by`][optimizer-plans] inverts ordering direction and swaps NULLS placement directly on expression ASTs without compiling SQL.

4. **Inverse and round-trip pairs:**
   - Plan construction vs. finalization: [`OptimizationPlan`][optimizer-plans] starts mutable during walker descent and freezes into immutable tuples upon [`OptimizationPlan.finalize`][optimizer-plans].
   - Forward vs. reverse ordering: [`_reverse_order_by`][optimizer-plans] cleanly inverts order specifications (toggling `-` and swapping `nulls_first` / `nulls_last`) for backward connection slicing.
   - Plan reconciliation: [`diff_plan_for_queryset`][optimizer-plans] round-trips plan directives against queryset state, dropping redundant paths and absorbing bare strings.
   - Path encoding: [`resolver_key`][optimizer-plans] generates canonical path strings, and [`runtime_path_from_path`][optimizer-plans] parses linked-list AST nodes into stable path tuples.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans], [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker], [`django_strawberry_framework/optimizer/extension.py`][optimizer-extension], [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner], [`django_strawberry_framework/optimizer/lateral_fetch.py`][optimizer-lateral-fetch], [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy], [`django_strawberry_framework/connection.py`][connection], [`django_strawberry_framework/utils/connections.py`][utils-connections];
   - Specifications: [spec-002][spec-002], [spec-003][spec-003], [spec-004][spec-004], [spec-028][spec-028], [spec-033][spec-033], [spec-035][spec-035], [spec-051][spec-051];
   - Test suites: [`tests/optimizer/test_plans.py`][test-optimizer-plans] (dedicated tests for plan emptiness, finalization, merging, diffing, window pagination, deterministic ordering, and select pruning), [`tests/optimizer/test_walker.py`][test-optimizer-walker], [`tests/optimizer/test_extension.py`][test-optimizer-extension], [`tests/optimizer/test_nested_planner.py`][test-optimizer-nested-planner], [`tests/optimizer/test_lateral_fetch.py`][test-optimizer-lateral-fetch], [`tests/test_relay_connection.py`][test-relay-connection];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adding a new directive field to `OptimizationPlan`, e.g. `defer_fields` for explicit column deferrals):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans] (declaring the field on [`OptimizationPlan`][optimizer-plans], categorizing it in `_FULL_MERGE_FIELDS`, and applying it in [`OptimizationPlan.finalize`][optimizer-plans] and [`OptimizationPlan.apply`][optimizer-plans]; caught by [`OptimizationPlan._assert_merge_field_inventory`][optimizer-plans] if merge categorization is missed).
  - *Site count:* 1 in target.
- **Posited change 2 (Optimizing the deduplication indexing in `_IndexedList`):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans] ([`_IndexedList`][optimizer-plans]).
  - *Site count:* 1 in target.
- **Posited change 3 (Adapting to Django internal `QuerySet.query.deferred_loading` restructuring):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans] ([`deferred_loading_of`][optimizer-plans]).
  - *Site count:* 1 in target.
- **Posited change 4 (Extending order entry parsing for custom database functions or expressions):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans] ([`order_entry_name_and_direction`][optimizer-plans]).
  - *Site count:* 1 in target.
- **Posited change 5 (Updating window pagination SQL annotation naming or namespaces):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans] (updating the `WINDOW_*` module constants).
  - *Site count:* 1 in target.
- **Posited change 6 (Enhancing backward connection ordering reversal for newly supported expression types):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans] ([`_reverse_order_by`][optimizer-plans]).
  - *Site count:* 1 in target.

### Rejected candidates

1. **Re-parsing order expressions independently in `nested_planner.py`, `lateral_fetch.py`, and `connection.py`:**
   - Disproved per [spec-028][spec-028] and [spec-033][spec-033]. Historical implementations had subtle disagreements on dash-stripping and nulls positioning. Centralizing all order parsing in [`order_entry_name_and_direction`][optimizer-plans], [`order_entry_has_explicit_nulls`][optimizer-plans], and [`ends_in_unique_column`][optimizer-plans] ensures total order stability and cursor parity across windowed and fallback connection paths.
2. **Merging sub-plan query directives directly into parent plans during child AST descent:**
   - Disproved per [spec-033][spec-033] Decision 6. Transactional sub-plans must isolate query directives until strategy acceptance. Merging query directives into parent plans prematurely would corrupt parent SQL if the nested window is subsequently rejected.
3. **Allowing post-finalization mutation on cached `OptimizationPlan` instances:**
   - Disproved per [spec-002][spec-002] and [spec-035][spec-035]. Plan instances are cached across requests. Swapping sequence fields to immutable tuples in [`OptimizationPlan.finalize`][optimizer-plans] guarantees that accidental post-handoff mutation fails loudly with `AttributeError` rather than silently corrupting cached plans.
4. **Duplicating Django `QuerySet.query.deferred_loading` tuple unpacking across consumers:**
   - Disproved per [spec-051][spec-051]. Centralizing all deferred loading inspection in [`deferred_loading_of`][optimizer-plans] guarantees consistent error handling across non-QuerySet test doubles and protects against future Django internal attribute renames.

## Opportunities

None — `django_strawberry_framework/optimizer/plans.py` is a clean, robust, highly consolidated, and strictly structured query optimization engine. It serves as the single source of truth for plan representation, immutable lifecycle transitions, merge inventories, ORM reconciliation, deterministic total ordering, and SQL window pagination, with zero redundant logic.

## Judgment

Zero-edit review. `optimizer/plans.py` exhibits complete policy consolidation, rigorous merge ownership self-auditing, and robust failure containment. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/plans.py --review docs/dry/dry-file-optimizer__plans.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Worker 2 independently inspected `django_strawberry_framework/optimizer/plans.py` and traced all connected behavior across the optimizer, connection pipeline, lateral fetch dialect, and test suites.

### Connected behavior & contract verification

1. **Plan Lifecycle & Immutability Enforcement:**
   - Evaluated the mutable-to-immutable transition in [`OptimizationPlan`][optimizer-plans]. During walker descent in [`walker.py`][optimizer-walker] and [`nested_planner.py`][optimizer-nested-planner], directive sequences use [`_IndexedList`][optimizer-plans] with $O(1)$ deduplication index maintenance.
   - Calling [`OptimizationPlan.finalize`][optimizer-plans] freezes directives into tuples and precomputes derived frozensets (`finalized_fk_id_elisions`, `finalized_planned_resolver_keys`, `finalized_lookup_paths`). Any post-handoff mutation on cached plans immediately raises `AttributeError`.
   - Verified the load-time reflection guard [`OptimizationPlan._assert_merge_field_inventory`][optimizer-plans]. It asserts that the union of `_FULL_MERGE_FIELDS`, `_METADATA_MERGE_FIELDS`, and `_DERIVED_FINALIZED_FIELDS` matches all dataclass fields, guaranteeing that future field additions cannot silently drift from merge logic.

2. **Single-Reader Django Deferred Loading Boundary:**
   - Inspected [`deferred_loading_of`][optimizer-plans]. It is the sole reader of Django's internal `QuerySet.query.deferred_loading` tuple `(names, defer_flag)`.
   - Verified that [`_consumer_only_fields`][optimizer-plans], [`_consumer_projection`][optimizer-plans], and lateral fetch column selection all consume this normalized boundary with graceful fallback on test doubles or non-QuerySet objects, insulating the codebase against future Django internal attribute alterations.

3. **Deterministic Total Ordering & Cursor Parity:**
   - Traced [`deterministic_order`][optimizer-plans] and [`ends_in_unique_column`][optimizer-plans] shared between plan-time window generation in [`nested_planner.py`][optimizer-nested-planner] and resolve-time connection slicing in [`connection.py`][connection].
   - Verified that unique non-nullable fields (or `pk`) terminate the ordering, and ties are deterministically broken by appending `pk.attname`, preventing cursor drift across paginated requests.
   - Evaluated [`_reverse_order_by`][optimizer-plans], which correctly reverses both string order refs and `OrderBy` expressions (inverting direction and swapping `nulls_first` / `nulls_last`), rejecting un-reversible expressions with loud [`OptimizerError`][optimizer-plans].

4. **SQL Window Pagination Mechanics:**
   - Verified [`apply_window_pagination`][optimizer-plans] integration with [`window_range_plan`][utils-connections] and [`assert_window_fetch_mode`][utils-connections].
   - Confirmed that windowed pagination strictly filters via `.filter()` on `_dst_*` annotations and never Python-slices the child queryset, preventing duplicate-through-join hazards on many-to-many and reverse relations.

5. **B8 Plan Reconciliation & Strictness Integrity:**
   - Evaluated [`prune_unsupportable_select_related`][optimizer-plans] and [`diff_plan_for_queryset`][optimizer-plans].
   - Confirmed that dropped `select_related` paths and overridden `prefetch_related` lookups strip their coupled keys from `planned_resolver_keys`, ensuring strictness checks detect genuine lazy loads.

### Probing matrix verification

- **Cross-flavor policy mirroring:** Fully discharged. Universal optimization plan and ordering contracts are shared across standard queries, connections, lateral fetches, and mutations with zero flavor-specific duplicate logic.
- **Sync and async twins:** Fully discharged. Pure synchronous AST manipulation and QuerySet transform pipeline, shared without async divergence.
- **Derived rather than repeated knowledge:** Fully discharged. Emptiness, finalized frozensets, field classification inventories, and deterministic order adjustments are derived dynamically from root definitions.
- **Inverse and round-trip pairs:** Fully discharged. Construction vs. finalization, forward vs. reverse ordering, and plan vs. queryset diffing are clean inverse pairs.
- **Contracts restated in another medium:** Fully discharged. Specifications ([spec-002][spec-002], [spec-003][spec-003], [spec-004][spec-004], [spec-028][spec-028], [spec-033][spec-033], [spec-035][spec-035], [spec-051][spec-051]), tests (`test_plans.py`, `test_walker.py`, `test_extension.py`), and documentation are aligned.

### Single-edit-site test

All 6 posited change scenarios hold with a single-edit-site count of 1 in `django_strawberry_framework/optimizer/plans.py`.

### Verification commands executed

- `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/optimizer/plans.py --review docs/dry/dry-file-optimizer__plans.md --include-constants`: PASSED (50 symbols covered).
- `uv run pytest tests/optimizer/test_plans.py --no-cov`: PASSED (117 tests).
- `uv run pytest tests/optimizer/ --no-cov`: PASSED (813 tests).

Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[cookbook]: ../COOKBOOK.md
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-002]: ../SPECS/spec-002-optimizer-0_0_2.md
[spec-003]: ../SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md
[spec-004]: ../SPECS/spec-004-optimizer_beyond-0_0_3.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-033]: ../SPECS/spec-033-nested_connection_execution_plan-0_0_9.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-051]: ../SPECS/spec-051-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-join-taxonomy]: ../../django_strawberry_framework/optimizer/join_taxonomy.py
[optimizer-lateral-fetch]: ../../django_strawberry_framework/optimizer/lateral_fetch.py
[optimizer-nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[utils-connections]: ../../django_strawberry_framework/utils/connections.py

<!-- tests/ -->
[test-optimizer-extension]: ../../tests/optimizer/test_extension.py
[test-optimizer-lateral-fetch]: ../../tests/optimizer/test_lateral_fetch.py
[test-optimizer-nested-planner]: ../../tests/optimizer/test_nested_planner.py
[test-optimizer-plans]: ../../tests/optimizer/test_plans.py
[test-optimizer-walker]: ../../tests/optimizer/test_walker.py
[test-relay-connection]: ../../tests/test_relay_connection.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
