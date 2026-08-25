# DRY review: `django_strawberry_framework/utils/querysets.py`

Status: verified

## System trace

`django_strawberry_framework/utils/querysets.py` implements the centralized query-source normalization, field coercion, single sync-worker boundary, sealed-execution-queryset security boundary, and colored visibility runners ([spec-036][spec-036], [spec-038][spec-038], [spec-039][spec-039], [spec-040][spec-040], [spec-045][spec-045]).

It owns the following architectural responsibilities:

1. **Query-Source Normalization, Field Coercion, and Sync/Async Primitives:**
   - Error marker & class label: [`SyncMisuseError`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::SyncMisuseError`) and [`_safe_class_name`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_safe_class_name`).
   - Async-in-sync guards & worker: [`reject_async_in_sync_context`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`), [`_dispose_sync_awaitable`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_dispose_sync_awaitable`), [`_RELAY_ASYNC_RECOURSE`][utils-querysets], [`sync_pipeline_recourse`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::sync_pipeline_recourse`), and [`run_in_one_sync_boundary`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`).
   - Query source & model lookups: [`model_for`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::model_for`), [`initial_queryset`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::initial_queryset`), and [`normalize_query_source`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::normalize_query_source`).
   - Field coercion: [`coerce_field_value_or_none`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::coerce_field_value_or_none`).

2. **Sealed Boundary Validation & AST Inspection:**
   - Concrete model & base table checks: [`_concrete_or_none`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_concrete_or_none`) and [`_base_table_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_base_table_defect`).
   - AST provenance & inert checks: [`_type_is_genuinely_django`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_type_is_genuinely_django`), [`_INERT_VALUE_TYPES`][utils-querysets], [`_is_inert_value`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_is_inert_value`), [`_shadow_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_shadow_defect`), and [`_genuine_node_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_genuine_node_defect`).
   - SQL templates & raw SQL defects: [`_SQL_TEMPLATE_ATTRS`][utils-querysets], [`_TEMPLATE_PARAM_VALUE_TYPES`][utils-querysets], [`_template_params_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_template_params_defect`), [`_node_metadata_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_node_metadata_defect`), [`_raw_sql_params_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_raw_sql_params_defect`), and [`_raw_sql_node_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_raw_sql_node_defect`).
   - Graph walker & states: [`_WalkState`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_WalkState` with `django_strawberry_framework/utils/querysets.py::_WalkState.VALIDATED`, `django_strawberry_framework/utils/querysets.py::_WalkState.CYCLE`, `django_strawberry_framework/utils/querysets.py::_WalkState.ENTERED`), [`_GraphWalk`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_GraphWalk` with `django_strawberry_framework/utils/querysets.py::_GraphWalk.__init__`, `django_strawberry_framework/utils/querysets.py::_GraphWalk.enter`, `django_strawberry_framework/utils/querysets.py::_GraphWalk.begin`, `django_strawberry_framework/utils/querysets.py::_GraphWalk.leave`), and [`_walk_short_circuit`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_walk_short_circuit`).
   - Expression state & sequence containers: [`_EXPRESSION_SEQUENCE_STATE_ATTRS`][utils-querysets], [`_expression_state_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_expression_state_defect`), [`_WALKED_SEQUENCE_TYPES`][utils-querysets], [`_expr_mapping_key_detail`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_expr_mapping_key_detail`), [`_deferred_mapping_key_detail`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_deferred_mapping_key_detail`), and [`_container_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_container_defect`).
   - Direct RHS & lookup inspection: [`_RHS_ATTRIBUTE_HOOKS`][utils-querysets], [`_DIRECT_RHS_DATA_BASES`][utils-querysets], [`_DIRECT_RHS_TRUSTED_MRO`][utils-querysets], [`_ATTR_MISSING`][utils-querysets], [`_static_attr_present`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_static_attr_present`), [`_rhs_hook_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_rhs_hook_defect`), [`_direct_rhs_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_direct_rhs_defect`), and [`_lookup_operands_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_lookup_operands_defect`).
   - AST & query container validation: [`_expr_graph_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_expr_graph_defect`), [`_expr_sequence_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_expr_sequence_defect`), [`_raw_sql_sequence_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_raw_sql_sequence_defect`), [`_join_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_join_defect`), [`_where_tree_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_where_tree_defect`), [`_select_related_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_select_related_defect`), [`_EXACT_DICT_QUERY_ATTRS`][utils-querysets], [`_EXACT_SET_QUERY_ATTRS`][utils-querysets], [`_query_payload_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_query_payload_defect`), [`_query_container_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_query_container_defect`), [`_query_ast_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_query_ast_defect`), [`_query_genuineness_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_query_genuineness_defect`), and [`_combined_query_table_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_combined_query_table_defect`).

3. **Canonical Reconstruction & Bound Value Normalization:**
   - Retained types & node provenance: [`_RETAINED_LEAF_TYPES`][utils-querysets], [`_RETAINED_SCHEMA_BASES`][utils-querysets], [`_RETAINED_TYPES`][utils-querysets], [`_RECONSTRUCTABLE_NODE_TYPES`][utils-querysets], and [`_is_reconstructable_node`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_is_reconstructable_node`).
   - Normalizer primitives: [`_normalized_str`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_str`), [`_normalized_bytes`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_bytes`), [`_normalized_bytearray`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_bytearray`), [`_normalized_int`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_int`), [`_normalized_float`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_float`), [`_normalized_complex`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_complex`), [`_normalized_decimal`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_decimal`), [`_normalized_date`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_date`), [`_normalized_datetime`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_datetime`), [`_normalized_time`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_time`), [`_normalized_timedelta`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_timedelta`), [`_normalized_uuid`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_uuid`), and [`_BOUND_VALUE_NORMALIZERS`][utils-querysets].
   - Bound value refusal & reconstruction traversal: [`_UntrustedBoundValueError`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_UntrustedBoundValueError`), [`_normalized_bound_value`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_bound_value`), [`_reconstructed_value`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_reconstructed_value`), [`_rebuild_query_payloads`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_rebuild_query_payloads`), and [`_reconstruction_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_reconstruction_defect`).

4. **Prefetches, Deferred Filters, and Sealed Sealing Execution:**
   - Prefetch reconstruction: [`_DJANGO_ITERABLE_CLASSES`][utils-querysets], [`_rebuilt_prefetch_or_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_rebuilt_prefetch_or_defect`), and [`_sealed_prefetch_related_lookups`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_sealed_prefetch_related_lookups`).
   - Deferred filter resolution: [`PROHIBITED_FILTER_KWARGS`][utils-querysets], [`_deferred_value_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_deferred_value_defect`), [`_bake_deferred_filter_or_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_bake_deferred_filter_or_defect`), and [`_queryset_state_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_queryset_state_defect`).
   - Sealing primitive & manager coercion: [`_seal_or_defect`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_seal_or_defect`) and [`_coerced_manager_queryset`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_coerced_manager_queryset`).

5. **Visibility Runners & Relation Lookup Utilities:**
   - Visibility result errors & preparation: [`_visibility_result_error`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_visibility_result_error`), [`_prepared_visibility_source`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_prepared_visibility_source`), and [`_normalized_visibility_result`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_normalized_visibility_result`).
   - Colored runners: [`apply_type_visibility_sync`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`) and [`apply_type_visibility_async`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::apply_type_visibility_async`).
   - Scoped related querysets: [`visibility_scoped_related_queryset`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::visibility_scoped_related_queryset`), [`related_visibility_queryset`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::related_visibility_queryset`), and [`related_visibility_queryset_or_default`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::related_visibility_queryset_or_default`).
   - Present pk queries: [`_stringified`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::_stringified`), [`stringified_pks_present`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::stringified_pks_present`), [`pks_all_present`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::pks_all_present`), [`visible_related_object`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::visible_related_object`), and [`visible_related_objects`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::visible_related_objects`).
   - Consumer resolver pipelines: [`reject_awaitable_sync_source`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::reject_awaitable_sync_source`), [`reject_residual_async_source`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::reject_residual_async_source`), [`post_process_queryset_result_sync`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::post_process_queryset_result_sync`), and [`post_process_queryset_result_async`][utils-querysets] (`django_strawberry_framework/utils/querysets.py::post_process_queryset_result_async`).

Connected behavior examined:
- [`django_strawberry_framework/types/base.py`][types-base]: `initial_queryset`, `apply_type_visibility_sync`, and `apply_type_visibility_async`.
- [`django_strawberry_framework/types/relay.py`][types-relay]: Relay node resolution and `coerce_field_value_or_none`.
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Mutation input decoding and `visibility_scoped_related_queryset`.
- [`django_strawberry_framework/utils/permissions.py`][utils-permissions]: Flat relation path gating and cascade permission scoping.
- [`tests/utils/`][tests-utils]: Tests covering the sealed boundary, query graph walkers, and visibility runners.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/querysets.py --include-constants`):
- Parsed 1 target file, 3337 lines.
- Complete inventory across all 110 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/querysets.py` enforces identical sealed-execution-queryset validation across all GraphQL entry points (Relay nodes, list fields, connection fields, nested prefetching, form mutations, model mutations, serializer mutations, and cascade permissions):
   - `_seal_or_defect` strips consumer class identity and canonically reconstructs fresh framework-owned `QuerySet` objects from validated AST state.
   - `_prepared_visibility_source` and `_normalized_visibility_result` ensure source querysets and hook results pass identical concrete-table, alias-pinning, and AST provenance proofs.
   - `stringified_pks_present` and `pks_all_present` unify batched relation existence checks across model, form, and serializer mutation decoders.

2. **Sync and async twins:**
   - `apply_type_visibility_sync` and `apply_type_visibility_async` share exact source preparation (`_prepared_visibility_source`) and result normalization (`_normalized_visibility_result`).
   - `reject_awaitable_sync_source` and `reject_residual_async_source` provide symmetric fail-closed boundaries for consumer resolver returns.
   - `post_process_queryset_result_sync` and `post_process_queryset_result_async` share `normalize_query_source` routing.

3. **Derived rather than repeated knowledge:**
   - `_is_reconstructable_node` derives AST rebuild eligibility from genuine Django provenance memos, preventing foreign class injection.
   - `_normalized_bound_value` derives exact inert parameter values using descriptor-level slot reads rather than instance-dispatched coercions.
   - `_base_table_defect` reads the first key of `alias_map` directly, bypassing vulnerable instance-cached properties.

4. **Inverse and round-trip pairs:**
   - `_GraphWalk` tracks recursion state (`visiting` vs `validated`) to distinguish legitimate diamond graphs from circular references.
   - `_reconstructed_value` rebuilds query AST structures while preserving identity sharing via its traversal memo.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/querysets.py`][utils-querysets], [`django_strawberry_framework/types/base.py`][types-base], [`django_strawberry_framework/types/relay.py`][types-relay], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers];
   - Specifications: [`docs/SPECS/spec-036-mutation_visibility_contracts-0_0_10.md`][spec-036], [`docs/SPECS/spec-038-form_mutations-0_0_11.md`][spec-038], [`docs/SPECS/spec-039-serializer_mutations-0_0_11.md`][spec-039], [`docs/SPECS/spec-040-bulk_mutations-0_0_12.md`][spec-040], [`docs/SPECS/spec-045-visibility_boundary-0_0_14.md`][spec-045];
   - Test suites: [`tests/utils/`][tests-utils], [`tests/types/`][tests-types], [`tests/mutations/`][tests-mutations];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new admitted inert bound parameter type to canonical reconstruction):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/querysets.py`][utils-querysets] ([`_INERT_VALUE_TYPES`][utils-querysets], [`_RETAINED_LEAF_TYPES`][utils-querysets], or [`_BOUND_VALUE_NORMALIZERS`][utils-querysets]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying the sealed queryset construction or state copying discipline):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/querysets.py`][utils-querysets] ([`_seal_or_defect`][utils-querysets]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Updating the sync-misuse error formatting or recourse message across write flavors):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/querysets.py`][utils-querysets] ([`sync_pipeline_recourse`][utils-querysets]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Class-level method inspection instead of sealed execution querysets:**
   - Disproved per [spec-045][spec-045]. Instance-shadowed attributes and monkeypatched methods easily bypass class-level inventories. State extraction and canonical reconstruction provide the sole sound boundary.

## Opportunities

None — `django_strawberry_framework/utils/querysets.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/querysets.py` exhibits zero duplicate code and complete policy consolidation across query-source normalization, sealed boundary validation, AST reconstruction, and visibility runners. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/querysets.py --review docs/dry/dry-file-utils__querysets.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/querysets.py`][utils-querysets] and Worker 1's DRY review.

1. **Sealed Boundary Security & AST Inspection:**
   - Confirmed `_seal_or_defect` extracts query state via `object.__getattribute__` on `__dict__`, neutralising custom property and method overrides.
   - Confirmed `_type_is_genuinely_django` proves class identity against `sys.modules`, rejecting spoofed `__module__` declarations.
   - Confirmed `_rebuild_query_payloads` and `_reconstructed_value` produce a clean, framework-owned `django.db.models.QuerySet` free from mutable references to consumer state.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/querysets.py --review docs/dry/dry-file-utils__querysets.md --include-constants`. 100% coverage across all 110 definitions / constants.

Confirmed: `django_strawberry_framework/utils/querysets.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutation_visibility_contracts-0_0_10.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_11.md
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_11.md
[spec-040]: ../SPECS/spec-040-bulk_mutations-0_0_12.md
[spec-045]: ../SPECS/spec-045-visibility_boundary-0_0_14.md

<!-- package source -->
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py

<!-- tests -->
[tests-mutations]: ../../tests/mutations/
[tests-types]: ../../tests/types/
[tests-utils]: ../../tests/utils/
