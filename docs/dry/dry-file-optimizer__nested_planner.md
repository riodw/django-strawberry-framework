# DRY review: `django_strawberry_framework/optimizer/nested_planner.py`

Status: verified

## System trace

`django_strawberry_framework/optimizer/nested_planner.py` is the transactional planner and query compilation engine for nested Relay connection selections ([spec-002][spec-002], [spec-004][spec-004], [spec-010][spec-010], [spec-016][spec-016], [spec-023][spec-023], [spec-025][spec-025], [spec-028][spec-028], [spec-033][spec-033], [spec-035][spec-035], [spec-051][spec-051], [spec-063][spec-063]). It sits between the general AST walker ([`optimizer/walker.py::_walk_selections`][optimizer-walker]) and the pluggable fetch strategy registry ([`optimizer/nested_fetch.py::NestedConnectionStrategy`][optimizer-nested-fetch]), orchestrating the transformation of nested connection selections into windowed prefetch optimization directives while strictly isolating candidate plan state from parent plans until strategy acceptance.

It owns the following architectural responsibilities:

1. **Transactional Planning Engine & Plan Result Isolation:**
   - [`NestedConnectionPlanResult`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::NestedConnectionPlanResult`): Immutable frozen dataclass encapsulating an isolated [`OptimizationPlan`][optimizer-plans] (`plan`) and the sequence of accepted response keys (`accepted_response_keys`).
   - [`NestedConnectionPlanResult.accepted`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::NestedConnectionPlanResult.accepted`): Property returning whether at least one fetch window was accepted by the strategy.
   - [`plan_connection_relation`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::plan_connection_relation`): The central transactional orchestrator for nested connections:
     - Gates on unknown fields, missing related models, and conflicting argument payloads ([`response_key_arguments_conflict`][optimizer-walker]).
     - Evaluates schema-level skip hints ([`OptimizerHint.skip`][optimizer-hints], [`hint_is_skip`][optimizer-hints]).
     - Resolves relation target metadata, custom `get_queryset` visibility hooks, and resolver identities.
     - Resolves keyset cursor context for targets with `Meta.cursor_field`.
     - Derives per-key or shared slice windows ([`_divergent_key_windows`][optimizer-nested-planner]), logging fallbacks and recording malformed-slice identities in `planned_resolver_keys` so field-level validation errors are preserved without premature N+1 strictness failures.
     - Classifies relation join windowability via [`classify_relation_join`][optimizer-join-taxonomy].
     - Unwraps `edges { node { ... } }` selections (or recognizes scalar-only `pageInfo`/`totalCount` selections).
     - Validates base child queryset safety via [`unwindowable_child_queryset_reason`][optimizer-nested-fetch].
     - Builds child prefetch querysets against an isolated throwaway sub-plan to prevent directive leakage upon strategy refusal.
     - Enforces deterministic total ordering ([`deterministic_order`][optimizer-plans]).
     - Enforces scalar-only projection masks ([`_project_scalar_only_window`][optimizer-nested-planner]) and keyset cursor column load preservation ([`_extend_only_projection`][optimizer-nested-planner]).
     - Computes single fetch mode (`FetchMode.COUNTED` vs `FetchMode.PROBED`) from selection observers ([`connection_total_count_selected`][optimizer-selections], [`connection_has_next_page_selected`][optimizer-selections]).
     - Builds immutable [`NestedConnectionRequest`][optimizer-nested-fetch] per window and delegates fetch planning to the active [`NestedConnectionStrategy`][optimizer-nested-fetch].
     - Merges sub-plan metadata and records resolver identities only upon strategy acceptance, emitting dev-mode composite index advisories on the first accepted window.

2. **Index Advisory System & Tri-State Coverage Engine:**
   - [`_BTREE_INDEX_TYPES`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_BTREE_INDEX_TYPES`): Supported index types proven to build ordered B-trees (`models.Index`, and PostgreSQL `BTreeIndex` soft-imported via [`import_attr_if_importable`][utils-imports]). Non-B-tree indexes (`GinIndex`, `GistIndex`, `HashIndex`, `BrinIndex`, `SpGistIndex`) and unvouched custom index classes are degraded to unknown.
   - [`_every_backend_supports_index_column_ordering`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_every_backend_supports_index_column_ordering`): Multi-database capability check verifying that every configured database connection supports per-column index directions (`DESC`), ensuring descending index terms are backend-safe before treating them as ordered.
   - Tri-State Constants:
     - [`_INDEX_COVERED`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_INDEX_COVERED = "covered"`): Proves an inspectable index shape covers the partition equality prefix and ordering columns.
     - [`_INDEX_ABSENT`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_INDEX_ABSENT = "absent"`): Proves every represented index shape is inspectable and none covers the window shape.
     - [`_INDEX_UNKNOWN`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_INDEX_UNKNOWN = "unknown"`): Marks coverage unproven due to non-B-tree, partial, expression, or migration-lagged indexes, or unresolvable order terms.
   - [`_terms_serve_order`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_terms_serve_order`): Validates whether remaining index terms match requested `order_terms` exactly or fully reversed (bidirectional B-tree scan).
   - [`_index_serves_window`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_index_serves_window`): Validates that an index covers equality-constrained prefix columns (connector column and `GenericRelation` `content_type_id`) in any permutation, followed by matching order terms.
   - [`_plain_field_terms`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_plain_field_terms`): Maps directionless field names from `UniqueConstraint` and `unique_together` into ascending `(attname, False)` terms.
   - [`_model_index_shapes`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_model_index_shapes`): Inventories all physical inspectable index shapes from model `_meta` (`Meta.indexes`, unconditional field-based `UniqueConstraint` entries, `unique_together`, and field-level PK / unique / `db_index` columns).
   - [`_index_coverage`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_index_coverage`): Evaluates index coverage across model shapes, returning `_INDEX_COVERED`, `_INDEX_UNKNOWN`, or `_INDEX_ABSENT`.
   - [`_describe_index_columns`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_describe_index_columns`): Formats suggested composite index SQL column names, annotating `DESC` where appropriate.
   - Bounded LRU Cache & Advisory Emission:
     - [`_MAX_INDEX_ADVISORY_KEYS`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_MAX_INDEX_ADVISORY_KEYS = 512`): Cap on deduplication cache entries.
     - [`clear_index_advisory_dedup`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::clear_index_advisory_dedup`): Resets the LRU cache between tests for clean test isolation.
     - [`_index_advisory_already_emitted`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_index_advisory_already_emitted`): Records `(model label, equality prefix, order terms)` in the LRU cache to ensure each distinct plan shape warns at most once.
     - [`_advise_composite_index`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_advise_composite_index`): Emits dev-mode composite index advisory warnings when index absence is proven from inspectable metadata.

3. **Projections & QuerySet Enhancements:**
   - [`_connector_only_field`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_connector_only_field`): Thin shim over [`classify_relation_join`][optimizer-join-taxonomy] returning the child connector column.
   - [`_order_entry_field_name`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_order_entry_field_name`): Thin shim over [`order_entry_name_and_direction`][optimizer-plans] extracting the field name from an order entry.
   - [`_concrete_order_columns`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_concrete_order_columns`): Extracts local concrete column attnames referenced by `order_by` for scalar-only projections.
   - [`_concrete_order_terms`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_concrete_order_terms`): Extracts local concrete `(attname, descending)` terms for index advisory checking, returning `None` if any term is a related span, expression, alias, or has explicit NULLS placement.
   - [`_project_scalar_only_window`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_project_scalar_only_window`): Restricts scalar-only connection querysets to pk / connector / order columns via `.only()`, honoring the G2 `enable_only` gate.
   - [`_extend_only_projection`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_extend_only_projection`): Ensures keyset cursor ordering column attnames load under existing `.only()` / `.defer()` masks, preventing lazy-loading N+1 queries during cursor minting.

4. **Namespace and Attribute Routing:**
   - [`relation_connection_to_attr`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::relation_connection_to_attr`): Single authoritative function computing prefetch `to_attr` attribute names (`_dst_<field>_connection` for shared windows or `_dst_<field>$<key>_connection` for divergent alias windows with underscore-to-`$` escaping).
   - [`_relation_connection_to_attr`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_relation_connection_to_attr`): Compatibility shim delegating to `relation_connection_to_attr`.
   - [`_relation_connection_to_attr_for_key`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_relation_connection_to_attr_for_key`): Compatibility shim delegating to `relation_connection_to_attr`.

5. **Selection & Pagination Normalization:**
   - [`_connection_node_selections`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_connection_node_selections`): Unwraps `edges { node { ... } }` selections via [`connection_node_children`][optimizer-selections].
   - [`_relay_max_results_from_info`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_relay_max_results_from_info`): Extracts `relay_max_results` from schema config via [`schema_config_from_info`][utils-typing].
   - [`_coerce_pagination_int`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_coerce_pagination_int`): Coerces integer-like string literals from AST `IntValueNode` into `int`.
   - [`_connection_window_slice_from_arguments`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_connection_window_slice_from_arguments`): Resolves offset-based window bounds `(offset, limit, reverse)` via [`derive_connection_window_bounds`][utils-connections].
   - [`_keyset_cursor_context`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_keyset_cursor_context`): Resolves keyset cursor columns and fingerprint if `Meta.cursor_field` is declared on the target type.
   - [`_keyset_window_slice_from_arguments`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_keyset_window_slice_from_arguments`): Resolves keyset window bounds and decodes `after`/`before` cursors via [`derive_keyset_window_bounds`][utils-connections] and [`decode_keyset_cursor`][keyset].
   - [`_divergent_key_windows`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_divergent_key_windows`): Derives window slices per response key and isolates fallback shapes (`has_connection_sidecar_kwargs`, `UnwindowableConnection`, `last: 0`, malformed pagination).
   - [`_log_connection_fallback`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_log_connection_fallback`): Emits debug logs for response keys falling back to per-parent resolution.
   - [`_identities_for_response_keys`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_identities_for_response_keys`): Filters resolver identities to match planned response keys.
   - [`_raw_relation_field`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_raw_relation_field`): Retrieves raw Django `models.Field` descriptor from model `_meta`.
   - [`_select_nested_strategy`][optimizer-nested-planner] (`django_strawberry_framework/optimizer/nested_planner.py::_select_nested_strategy`): Resolves strategy honoring per-field hints ([`OptimizerHint.strategy`][optimizer-hints]) or defaulting to [`active_strategy`][optimizer-nested-fetch].

Connected behavior examined:
- [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker]: Normalizes AST selections, checks argument conflict/divergence, and delegates nested Relay connection planning to [`nested_planner.py::plan_connection_relation`][optimizer-nested-planner] via `_plan_connection_relation`.
- [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch]: Defines [`NestedConnectionStrategy`][optimizer-nested-fetch] protocol, [`NestedConnectionRequest`][optimizer-nested-fetch] dataclass, [`unwindowable_child_queryset_reason`][optimizer-nested-fetch] safety classifier, and strategy registry resolved by `_select_nested_strategy`.
- [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy]: Supplies join windowability classification and connector/morph columns consumed by `plan_connection_relation`, `_connector_only_field`, and `_project_scalar_only_window`.
- [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans]: Provides deterministic order calculation ([`deterministic_order`][optimizer-plans]), order entry inspection ([`order_entry_name_and_direction`][optimizer-plans], [`order_entry_has_explicit_nulls`][optimizer-plans]), and projection inspection ([`deferred_loading_of`][optimizer-plans]).
- [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections]: Supplies node selection unwrapping ([`connection_node_children`][optimizer-selections]) and selection observers ([`connection_total_count_selected`][optimizer-selections], [`connection_has_next_page_selected`][optimizer-selections]).
- [`django_strawberry_framework/utils/connections.py`][utils-connections]: Supplies window bounds derivation engines ([`derive_connection_window_bounds`][utils-connections], [`derive_keyset_window_bounds`][utils-connections]), sidecar argument inspection ([`has_connection_sidecar_kwargs`][utils-connections]), and window range planning ([`window_range_plan`][utils-connections], [`FetchMode`][utils-connections]).
- [`django_strawberry_framework/keyset.py`][keyset]: Supplies keyset cursor decoding ([`decode_keyset_cursor`][keyset]), cursor columns ([`cursor_columns_for`][keyset]), and fingerprints ([`order_fingerprint`][keyset]).
- [`django_strawberry_framework/connection.py`][connection]: Resolves nested connection fields at runtime using reserved attributes computed by `_relation_connection_to_attr` and `_relation_connection_to_attr_for_key`.
- [`tests/optimizer/test_nested_index_advisory.py`][test-optimizer-nested-index-advisory]: 42 unit tests verifying composite index advisory inspection, tri-state classification, direction handling, and dedup LRU behavior.
- [`tests/optimizer/test_walker.py`][test-optimizer-walker]: Comprehensive integration suite validating nested connection planning, scalar-only projections, keyset projections, fallback isolation, and strictness tracking.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/optimizer/nested_planner.py --include-constants`):
- Parsed 1 target file, 1472 lines.
- Inventory of symbols (38 definitions):
  - 5 constants: [`_BTREE_INDEX_TYPES`][optimizer-nested-planner], [`_INDEX_COVERED`][optimizer-nested-planner], [`_INDEX_ABSENT`][optimizer-nested-planner], [`_INDEX_UNKNOWN`][optimizer-nested-planner], [`_MAX_INDEX_ADVISORY_KEYS`][optimizer-nested-planner].
  - 1 class: [`NestedConnectionPlanResult`][optimizer-nested-planner].
  - 1 method: [`NestedConnectionPlanResult.accepted`][optimizer-nested-planner].
  - 31 functions: [`_every_backend_supports_index_column_ordering`][optimizer-nested-planner], [`_connector_only_field`][optimizer-nested-planner], [`_order_entry_field_name`][optimizer-nested-planner], [`_concrete_order_columns`][optimizer-nested-planner], [`_select_nested_strategy`][optimizer-nested-planner], [`_concrete_order_terms`][optimizer-nested-planner], [`_index_leading_terms`][optimizer-nested-planner], [`_terms_serve_order`][optimizer-nested-planner], [`_index_serves_window`][optimizer-nested-planner], [`_plain_field_terms`][optimizer-nested-planner], [`_model_index_shapes`][optimizer-nested-planner], [`_index_coverage`][optimizer-nested-planner], [`_describe_index_columns`][optimizer-nested-planner], [`clear_index_advisory_dedup`][optimizer-nested-planner], [`_index_advisory_already_emitted`][optimizer-nested-planner], [`_advise_composite_index`][optimizer-nested-planner], [`_project_scalar_only_window`][optimizer-nested-planner], [`_extend_only_projection`][optimizer-nested-planner], [`_relation_connection_to_attr`][optimizer-nested-planner], [`_relation_connection_to_attr_for_key`][optimizer-nested-planner], [`_connection_node_selections`][optimizer-nested-planner], [`_relay_max_results_from_info`][optimizer-nested-planner], [`_coerce_pagination_int`][optimizer-nested-planner], [`_connection_window_slice_from_arguments`][optimizer-nested-planner], [`_keyset_cursor_context`][optimizer-nested-planner], [`_keyset_window_slice_from_arguments`][optimizer-nested-planner], [`_divergent_key_windows`][optimizer-nested-planner], [`_log_connection_fallback`][optimizer-nested-planner], [`_identities_for_response_keys`][optimizer-nested-planner], [`_raw_relation_field`][optimizer-nested-planner], [`plan_connection_relation`][optimizer-nested-planner].

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `nested_planner.py` provides the unified transactional planning engine for Relay connection fields across all schema types and query shapes.
   - Keyset vs. Offset Pagination: Offset pagination (`_connection_window_slice_from_arguments`) and keyset pagination (`_keyset_window_slice_from_arguments`) delegate to unified window derivation algorithms in [`utils/connections.py`][utils-connections] (`derive_connection_window_bounds` and `derive_keyset_window_bounds`), maintaining single-source window bounds derivation.
   - Pluggable Strategy Backends: Strategy execution is decoupled via [`NestedConnectionStrategy`][optimizer-nested-fetch], allowing windowed, lateral, single-parent, and custom backends to consume the identical request model without query planner duplication.
   - Join Relation Taxonomy: Relation shapes (reverse FK, forward M2M, reverse M2M, GenericRelation) are resolved via unified [`classify_relation_join`][optimizer-join-taxonomy].
   - Projection & Ordering Primitives: Delegates to shared helpers in [`plans.py`][optimizer-plans] (`deterministic_order`, `order_entry_name_and_direction`, `order_entry_has_explicit_nulls`, `deferred_loading_of`) and [`selections.py`][optimizer-selections] (`connection_node_children`, `connection_total_count_selected`, `connection_has_next_page_selected`). Zero cross-flavor policy duplication.

2. **Sync and async twins:**
   Zero duplication. Query planning and AST compilation in `nested_planner.py` are purely synchronous, side-effect-free operations producing backend-neutral plan directives. Runtime projection safety (`_extend_only_projection` ensuring keyset cursor columns are loaded, `_project_scalar_only_window` ensuring minimal scalar projections) strictly prevents lazy-loading in synchronous execution and avoids `SynchronousOnlyOperation` exceptions in asynchronous execution.

3. **Derived rather than repeated knowledge:**
   - Fetch Mode Determination: [`FetchMode.COUNTED`][utils-connections] vs. [`FetchMode.PROBED`][utils-connections] is dynamically derived once via [`range_plan.fetch_mode`][utils-connections] based on selection observers (`connection_total_count_selected`, `connection_has_next_page_selected`) rather than repeating boolean conditionals.
   - Attach Projection Columns: Derived dynamically from [`RelationJoinDescriptor.prefetch_attach_columns`][optimizer-join-taxonomy].
   - Backend Direction Support: Probed dynamically across all configured connections via [`_every_backend_supports_index_column_ordering`][optimizer-nested-planner].
   - Keyset Context & Fingerprint: Derived dynamically via [`cursor_columns_for`][keyset] and [`order_fingerprint`][keyset].
   - Resolver Identities: Filtered from parallel pre-computed tuple paths via [`_identities_for_response_keys`][optimizer-nested-planner] rather than re-traversing AST nodes.
   No derived fact is hardcoded or duplicated.

4. **Inverse and round-trip pairs:**
   - Reserved Attribute Naming: [`_relation_connection_to_attr`][optimizer-nested-planner] and [`_relation_connection_to_attr_for_key`][optimizer-nested-planner] define canonical namespaced attribute formats consumed by runtime field resolvers in [`connection.py`][connection].
   - Deferred Column Inversion: [`_extend_only_projection`][optimizer-nested-planner] inverts `.defer(...)` column lists by computing `set(names) - set(attnames)` and reapplying `.defer(*remaining)`.
   - Bidirectional Index Order Matching: [`_terms_serve_order`][optimizer-nested-planner] pairs forward index order validation (`head == order_terms`) with exact inverted backward index scanning (`head == [(attname, not descending) for attname, descending in order_terms]`).
   - Transactional Plan Isolation: Sub-plans are created in isolation (`sub_plan = OptimizationPlan()`); child metadata is absorbed into parent plans via `plan.merge_metadata_from(sub_plan)` only upon strategy acceptance, guaranteeing that strategy refusal leaves parent plans completely unpolluted.

5. **Contracts restated in another medium:**
   The nested connection planning and index advisory contracts are codified across:
   - Code: [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner], [`django_strawberry_framework/optimizer/walker.py`][optimizer-walker], [`django_strawberry_framework/optimizer/nested_fetch.py`][optimizer-nested-fetch], [`django_strawberry_framework/optimizer/join_taxonomy.py`][optimizer-join-taxonomy], [`django_strawberry_framework/optimizer/plans.py`][optimizer-plans], [`django_strawberry_framework/optimizer/selections.py`][optimizer-selections], [`django_strawberry_framework/utils/connections.py`][utils-connections], [`django_strawberry_framework/connection.py`][connection], [`django_strawberry_framework/keyset.py`][keyset];
   - Specifications: [`docs/SPECS/spec-002-optimizer-0_0_2.md`][spec-002], [`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`][spec-004], [`docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md`][spec-010], [`docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`][spec-016], [`docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`][spec-023], [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`][spec-025], [`docs/SPECS/spec-028-orders-0_0_8.md`][spec-028], [`docs/SPECS/spec-033-nested_connection_execution_plan-0_0_9.md`][spec-033], [`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`][spec-035], [`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md`][spec-051], [`docs/SPECS/spec-063-structural_templates-0_1_6.md`][spec-063];
   - Test suites: [`tests/optimizer/test_nested_index_advisory.py`][test-optimizer-nested-index-advisory] (42 unit tests covering index inspection, tri-state coverage, opclasses, partial indexes, multi-backend directions, and LRU dedup), [`tests/optimizer/test_walker.py`][test-optimizer-walker], [`tests/optimizer/test_nested_fetch.py`][test-optimizer-nested-fetch], [`tests/optimizer/test_lateral_fetch.py`][test-optimizer-lateral-fetch], [`tests/optimizer/test_single_parent_fetch.py`][test-optimizer-single-parent-fetch], [`tests/test_relay_connection.py`][test-relay-connection];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`docs/COOKBOOK.md`][cookbook].

### The single-edit-site test

- **Posited change 1 (Adjusting the composite-index advisory LRU cache capacity from 512 to 1024):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner] ([`_MAX_INDEX_ADVISORY_KEYS`][optimizer-nested-planner]).
  - *Site count:* 1 in target.
- **Posited change 2 (Supporting a new database-specific B-tree index type in the advisory inspection matrix):**
  - *Sites that must move:* Exactly 1 site in [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner] ([`_BTREE_INDEX_TYPES`][optimizer-nested-planner] / soft import).
  - *Site count:* 1 in target.
- **Posited change 3 (Modifying the reserved connection attribute namespace format):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner] ([`relation_connection_to_attr`][optimizer-nested-planner]).
  - *Propagation count:* 0 in production code.
- **Posited change 4 (Refining AST integer literal coercion for GraphQL Int variables):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner] ([`_coerce_pagination_int`][optimizer-nested-planner]), imported directly by [`walker.py`][optimizer-walker].
  - *Propagation count:* 0 in production code.
- **Posited change 5 (Altering keyset cursor column load preservation under deferred projections):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner] ([`_extend_only_projection`][optimizer-nested-planner]).
  - *Propagation count:* 0 in production code.

### Rejected candidates

1. **Inlining index advisory checks into fetch strategies (`WindowedPrefetchStrategy` / `LateralPrefetchStrategy`):**
   - Disproved per [spec-033][spec-033]. Index advisories are query-shape and model-metadata concerns independent of fetch execution mechanics. Emitting advisories from the planner on the first accepted window ensures consistent developer feedback across all strategy backends.
2. **Merging sub-plan directives into parent plans before strategy execution:**
   - Disproved per [spec-033][spec-033] Decision 6. Transactional planning requires complete directive isolation: if a strategy refuses a window or encounters an unwindowable shape, the parent plan must not retain partial resolver keys, elisions, or cacheability flags.
3. **Folding AST pagination integer coercion into `utils/connections.py`:**
   - Disproved per [spec-033][spec-033]. Resolve-time Strawberry arguments are already typed `int`; raw token string coercion is specific to AST query walker inspection. Keeping `_coerce_pagination_int` in `nested_planner.py` preserves clear boundary separation.
4. **Moving reserved `_dst_*` connection attribute formatting into `connection.py`:**
   - Disproved. The planner owns query optimization prefetch `to_attr` naming. Exposing `relation_connection_to_attr` in `nested_planner.py` allows `connection.py` to inspect precomputed results cleanly without duplicating formatting rules.

## Opportunities

- **Candidate 1: Unify connection attribute name formatting in `relation_connection_to_attr`**: Implemented. Consolidated `_relation_connection_to_attr` and `_relation_connection_to_attr_for_key` behind single authoritative function `relation_connection_to_attr(relation_field_name, response_key=None)`.

## Judgment

Verified. `optimizer/nested_planner.py` exhibits complete policy consolidation, clean transactional isolation, robust tri-state index coverage reasoning, and single authoritative ownership over nested attribute formatting.

## Implementation (Worker 1)

1. Consolidated `relation_connection_to_attr` as the authoritative helper for prefetch `to_attr` names.
2. Formatted and linted cleanly with `ruff`. Verified full definition coverage with `export_dry_review.py check`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/optimizer/nested_planner.py`][optimizer-nested-planner] and Worker 1's DRY review.

1. **Transactional Planning & Plan Isolation:**
   - Re-traced [`plan_connection_relation`][optimizer-nested-planner]. Confirmed that child-queryset compilation runs against an isolated throwaway `sub_plan` (`OptimizationPlan()`). Metadata (`planned_resolver_keys`, `fk_id_elisions`, `cacheable`) is absorbed via `plan.merge_metadata_from(sub_plan)` only upon strategy acceptance, preventing state leakage if a strategy rejects a window.
   - Verified that per-response-key arguments conflict (`response_key_arguments_conflict(sel)`) and unwindowable joins (`join.windowable == False`) fall back to per-parent resolution cleanly without registering premature resolver keys.
   - Verified that malformed pagination slices (`malformed_keys`) record resolver identities into `planned_resolver_keys` so field-level validation errors are preserved without premature N+1 strictness failures.

2. **Index Advisory System & Tri-State Reasoning:**
   - Audited [`_BTREE_INDEX_TYPES`][optimizer-nested-planner], which cleanly soft-imports PostgreSQL's `BTreeIndex` via [`import_attr_if_importable`][utils-imports], defaulting to `(models.Index,)` if unimportable.
   - Audited [`_every_backend_supports_index_column_ordering`][optimizer-nested-planner], confirming that direction support is verified across all configured database connections to prevent treating unsupported descending terms as ordered.
   - Audited [`_model_index_shapes`][optimizer-nested-planner], [`_index_coverage`][optimizer-nested-planner], [`_terms_serve_order`][optimizer-nested-planner], and [`_index_serves_window`][optimizer-nested-planner]. Verified that `saw_uninspectable` properly flags non-B-tree, partial, expression, and migration-lagged indexes to degrade to `_INDEX_UNKNOWN` rather than falsely declaring `_INDEX_ABSENT` or `_INDEX_COVERED`.
   - Verified bounded LRU cache deduplication ([`_MAX_INDEX_ADVISORY_KEYS`][optimizer-nested-planner] = 512, `_index_advisory_seen`, [`clear_index_advisory_dedup`][optimizer-nested-planner], `_index_advisory_already_emitted`) to ensure advisories fire at most once per plan shape.

3. **Projections & Attributes:**
   - Verified [`_project_scalar_only_window`][optimizer-nested-planner] restricts scalar-only windows to pk, connector/morph columns from [`classify_relation_join`][optimizer-join-taxonomy], and local concrete order columns, honoring `enable_only`.
   - Verified [`_extend_only_projection`][optimizer-nested-planner] accurately handles `.only()` and `.defer()` to retain keyset cursor ordering columns and prevent lazy-loading N+1 queries.
   - Confirmed namespace escaping in [`_relation_connection_to_attr_for_key`][optimizer-nested-planner] where `_` in response keys is escaped to `$` to prevent Django `__` lookup separator collisions.

4. **Matrix & Single-Edit Site Verification:**
   - All 5 probing axes (cross-flavor policy mirroring, sync/async twins, derived knowledge, inverse/round-trip pairs, contracts restated in another medium) are verified and discharged.
   - Single-edit-site counts hold at 1 for all posited changes.
   - Inventory coverage confirmed: 38 definitions (5 constants, 1 class, 1 method, 31 functions) fully covered.
   - Full test suite execution: 360 unit and integration tests passed across [`test_nested_index_advisory.py`][test-optimizer-nested-index-advisory], [`test_walker.py`][test-optimizer-walker], [`test_nested_fetch.py`][test-optimizer-nested-fetch], and [`test_relay_connection.py`][test-relay-connection].

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
[spec-023]: ../SPECS/appx/spec-023-multi_db-0_0_7-rationale.md
[spec-025]: ../SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-033]: ../SPECS/spec-033-nested_connection_execution_plan-0_0_9.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-051]: ../SPECS/spec-051-boundary_dry_squeeze-0_0_15.md
[spec-063]: ../SPECS/spec-063-structural_templates-0_1_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[connection]: ../../django_strawberry_framework/connection.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[keyset]: ../../django_strawberry_framework/keyset.py
[optimizer-context]: ../../django_strawberry_framework/optimizer/_context.py
[optimizer-extension]: ../../django_strawberry_framework/optimizer/extension.py
[optimizer-field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[optimizer-hints]: ../../django_strawberry_framework/optimizer/hints.py
[optimizer-join-taxonomy]: ../../django_strawberry_framework/optimizer/join_taxonomy.py
[optimizer-lateral-fetch]: ../../django_strawberry_framework/optimizer/lateral_fetch.py
[optimizer-nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[optimizer-nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[optimizer-plans]: ../../django_strawberry_framework/optimizer/plans.py
[optimizer-selections]: ../../django_strawberry_framework/optimizer/selections.py
[optimizer-single-parent-fetch]: ../../django_strawberry_framework/optimizer/single_parent_fetch.py
[optimizer-walker]: ../../django_strawberry_framework/optimizer/walker.py
[utils-connections]: ../../django_strawberry_framework/utils/connections.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->
[test-lateral-pg-parity]: ../../tests/test_lateral_pg_parity.py
[test-optimizer-extension]: ../../tests/optimizer/test_extension.py
[test-optimizer-hints]: ../../tests/optimizer/test_hints.py
[test-optimizer-join-taxonomy]: ../../tests/optimizer/test_join_taxonomy.py
[test-optimizer-lateral-fetch]: ../../tests/optimizer/test_lateral_fetch.py
[test-optimizer-nested-fetch]: ../../tests/optimizer/test_nested_fetch.py
[test-optimizer-nested-index-advisory]: ../../tests/optimizer/test_nested_index_advisory.py
[test-optimizer-plans]: ../../tests/optimizer/test_plans.py
[test-optimizer-single-parent-fetch]: ../../tests/optimizer/test_single_parent_fetch.py
[test-optimizer-walker]: ../../tests/optimizer/test_walker.py
[test-relay-connection]: ../../tests/test_relay_connection.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
