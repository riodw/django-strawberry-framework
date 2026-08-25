# DRY review: `django_strawberry_framework/rest_framework/resolvers.py`

Status: verified

## System trace

`django_strawberry_framework/rest_framework/resolvers.py` is the sync and async resolver pipeline for `SerializerMutation` write operations ([spec-039][spec-039]).

It owns the following architectural responsibilities:

1. **Pipeline Delegation & Shared Skeleton Integration:**
   - [`_OMITTED`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_OMITTED`): Identity omission sentinel.
   - [`_SERIALIZER_ASYNC_RECOURSE`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_SERIALIZER_ASYNC_RECOURSE`): Async recourse message derived via [`sync_pipeline_recourse`][utils-querysets].
   - [`_run_serializer_pipeline_sync`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_run_serializer_pipeline_sync`): Delegates locate, authorize, and re-fetch stages to [`run_write_pipeline_sync`][mutations-resolvers].
   - [`resolve_serializer_sync`][rf-resolvers] & [`resolve_serializer_async`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::resolve_serializer_sync`, `django_strawberry_framework/rest_framework/resolvers.py::resolve_serializer_async`): Materialized as a sync/async pair via [`make_resolver_entries`][mutations-resolvers].

2. **Serializer Data Decoding & Nested Dispatch:**
   - [`_decode_relation_single`][rf-resolvers] & [`_decode_relation_multi`][rf-resolvers]: Single and batched relation decoders wrapping [`decode_visible_relation`][utils-write-values] and [`decode_visible_relation_ids`][utils-write-values].
   - [`_decode_serializer_data`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_decode_serializer_data`): Top-level decode entry point.
   - [`_decode_input_object`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_decode_input_object`): Iterates over field specs using [`decode_field_handlers`][utils-write-values] and [`decode_provided_fields`][utils-write-values].
   - [`_decode_nested`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_decode_nested`): Recursive decode for nested single and multi input dataclasses.

3. **DRF Error Flattening & Path Normalization:**
   - [`_DRF_NON_FIELD_KEY`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_DRF_NON_FIELD_KEY`): Dynamically introspected from `serializers.api_settings.NON_FIELD_ERRORS_KEY`.
   - [`_ERROR_FLATTEN_NODE_BUDGET`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_ERROR_FLATTEN_NODE_BUDGET`): Recursion budget guard (10,000 nodes).
   - [`serializer_errors_to_field_errors`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::serializer_errors_to_field_errors`): Iterative, cycle-safe, depth-first flattener for DRF error detail structures.
   - Helper routines: [`_error_node_children`][rf-resolvers], [`_error_leaf`][rf-resolvers], [`_error_detail_codes`][rf-resolvers], [`_rekey_segment`][rf-resolvers], and [`_build_reverse_map`][rf-resolvers].

4. **Hook Boundary Defense & Immutability:**
   - [`_upload_metadata`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_upload_metadata`): Builds frozen [`UploadMetadata`][rf-hook-context] descriptors.
   - [`_hook_mapping`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_hook_mapping`): Validates mapping returns from consumer hooks.
   - Type sets: [`_IMMUTABLE_LEAF_TYPES`][rf-resolvers] and [`_FROZEN_VIEW_CONTAINERS`][rf-resolvers].
   - [`_frozen_hook_view`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_frozen_hook_view`): Deep-freezes provided data into immutable views for consumer hooks.
   - Injected data & kwargs merge: [`_injected_serializer_data`][rf-resolvers] and [`_merged_serializer_kwargs`][rf-resolvers].

5. **Schema vs Runtime Consistency & Queryset Visibility Scoping:**
   - Agreement guards: [`_relation_model_of`][rf-resolvers], [`_assert_schema_runtime_agreement`][rf-resolvers], [`_assert_runtime_write_source_ownership`][rf-resolvers], [`_assert_field_agreement`][rf-resolvers], [`_assert_relation_agreement`][rf-resolvers], and [`_assert_nested_agreement`][rf-resolvers].
   - Queryset scoping & validator pinning: [`_scope_relation_querysets_to_visibility`][rf-resolvers], [`_pin_validator_querysets`][rf-resolvers], and [`_scope_specs_over_serializer`][rf-resolvers] (using [`pin_write_queryset`][utils-write-tx], [`related_visibility_queryset`][utils-querysets], and [`base_locked_queryset`][utils-write-tx]).
   - Save kwargs validation: [`_assert_save_kwargs_no_shadow`][rf-resolvers] and [`_assert_save_kwargs_not_model_fields`][rf-resolvers].
   - [`_write_surface_specs`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_write_surface_specs`): Aggregates input specs and injected field specs.

6. **Relation Intent Tracking & Post-Save Attestation:**
   - [`_RelationIntentLedger`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_RelationIntentLedger`): FIFO ledger for resolved relation rows ([`_RelationIntentLedger.__init__`][rf-resolvers], [`_RelationIntentLedger.record`][rf-resolvers], [`_RelationIntentLedger.consume`][rf-resolvers], [`_RelationIntentLedger.assert_fully_consumed`][rf-resolvers]).
   - Identity primitives: [`_relation_object_identity`][rf-resolvers], [`_relation_intent_snapshot`][rf-resolvers], [`_relation_identity_intact`][rf-resolvers].
   - Instrumentation & validation: [`_instrument_relation_intent`][rf-resolvers], [`_instrument_intent_specs`][rf-resolvers], [`_record_field_intent`][rf-resolvers], [`_assert_relation_intent`][rf-resolvers], [`_assert_intent_specs`][rf-resolvers].
   - M2M snapshot & attestation: [`_m2m_membership_snapshot`][rf-resolvers], [`_attestable_m2m_fields`][rf-resolvers], [`_attest_saved_relations`][rf-resolvers].

7. **Save Isolation, ORM Witness & Step Dispatch:**
   - [`_write_witness`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_write_witness`): Thread-local `pre_save` and `post_save` guard leveraging [`make_cross_alias_save_guard`][utils-write-tx].
   - [`_checked_saved_result`][rf-resolvers] (`django_strawberry_framework/rest_framework/resolvers.py::_checked_saved_result`): Validates model instance, identity, PK, alias, and insertion witness.
   - Core step callbacks: [`_serializer_write_step`][rf-resolvers], [`_guarded_serializer_write`][rf-resolvers], and [`_serializer_decode_step`][rf-resolvers].

Connected behavior examined:
- [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]: Promoted generic write pipeline skeleton (`run_write_pipeline_sync`, `make_resolver_entries`).
- [`django_strawberry_framework/rest_framework/hook_context.py`][rf-hook-context]: Defines `SerializerHookContext` and `UploadMetadata`.
- [`django_strawberry_framework/rest_framework/inputs.py`][rf-inputs]: Supplies `raise_writable_source_ownership_errors` and `runtime_validated_data_fields`.
- [`django_strawberry_framework/rest_framework/serializer_converter.py`][rf-converter]: Supplies kind constants and `nested_serializer_child`.
- [`django_strawberry_framework/utils/write_transaction.py`][utils-write-tx]: Atomic savepoint, locked queryset, and cross-alias guard helpers.
- [`django_strawberry_framework/utils/write_values.py`][utils-write-values]: Shared decoding factories.
- [`tests/rest_framework/test_resolvers.py`][tests-rf-resolvers]: Full suite testing execution, isolation, and security assertions.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/rest_framework/resolvers.py --include-constants`):
- Parsed 1 target file, 2,411 lines.
- Complete inventory across all 52 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `rest_framework/resolvers.py` delegates transaction lifecycle, locating, authorization preambles, and re-fetching to [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers]. Shared decoding spines and transaction pinning are sourced directly from [`utils/write_values.py`][utils-write-values] and [`utils/write_transaction.py`][utils-write-tx]. DRF-specific requirements (such as recursive error flattening with `_DRF_NON_FIELD_KEY`, frozen hook views, relation intent ledgers, and save-result witnessing) are isolated single-site implementations.

2. **Sync and async twins:**
   Zero duplication. Both `resolve_serializer_sync` and `resolve_serializer_async` are generated concurrently from the shared `_run_serializer_pipeline_sync` via [`make_resolver_entries`][mutations-resolvers].

3. **Derived rather than repeated knowledge:**
   Runtime write checks and visibility scoping derive all model, relation, and nested metadata directly from the pre-computed input specs (`mutation_cls._input_field_specs` and `mutation_cls._injected_field_specs`).

4. **Inverse and round-trip pairs:**
   `_write_witness` context manager ensures strict symmetrical setup and teardown of signal handlers. `_RelationIntentLedger` enforces exact parity between recorded validation results and consumed intent.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/rest_framework/resolvers.py`][rf-resolvers], [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers], [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers], [`django_strawberry_framework/utils/write_transaction.py`][utils-write-tx], [`django_strawberry_framework/utils/write_values.py`][utils-write-values];
   - Specifications: [`docs/SPECS/spec-039-serializer_mutation-0_0_11.md`][spec-039];
   - Test suites: [`tests/rest_framework/test_resolvers.py`][tests-rf-resolvers];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adjusting DRF error flattening node budget `_ERROR_FLATTEN_NODE_BUDGET`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/rest_framework/resolvers.py`][rf-resolvers] ([`_ERROR_FLATTEN_NODE_BUDGET`][rf-resolvers]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying write pipeline pre-auth stage ordering across all mutation flavors):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers] ([`run_write_pipeline_sync`][mutations-resolvers]).
  - *Propagation count:* 0 in `rest_framework/resolvers.py`.
- **Posited change 3 (Modifying DRF non-field error normalization lookup):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/rest_framework/resolvers.py`][rf-resolvers] ([`_DRF_NON_FIELD_KEY`][rf-resolvers]).
  - *Propagation count:* 0 in other files.

### Rejected candidates

1. **Re-implementing the write transaction skeleton independently:**
   - Disproved per [spec-039][spec-039]. Using `run_write_pipeline_sync` guarantees uniform authorization-before-decode and transactional security.
2. **Re-implementing relation visibility decoding independently:**
   - Disproved per [spec-039][spec-039]. Using `decode_visible_relation` and `decode_visible_relation_ids` ensures consistent object-level visibility guarantees.

## Opportunities

None — `django_strawberry_framework/rest_framework/resolvers.py` is fully consolidated with shared infrastructure in `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/utils/write_transaction.py`, and `django_strawberry_framework/utils/write_values.py`.

## Judgment

Verified. `rest_framework/resolvers.py` exhibits zero duplicate code and complete policy consolidation through shared mutation and transaction infrastructure. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/resolvers.py --review docs/dry/dry-file-rest_framework__resolvers.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/rest_framework/resolvers.py`][rf-resolvers] and Worker 1's DRY review.

1. **Resolver Pipeline & Security Infrastructure:**
   - Confirmed `_run_serializer_pipeline_sync` delegates directly to the promoted `run_write_pipeline_sync` skeleton.
   - Confirmed recursive DRF error flattening, frozen hook data isolation, relation intent tracking, and post-save attestations are cleanly implemented without duplicating general pipeline mechanics.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/resolvers.py --review docs/dry/dry-file-rest_framework__resolvers.md --include-constants`. 100% coverage across all 52 definitions.

Confirmed: `django_strawberry_framework/rest_framework/resolvers.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-039]: ../SPECS/spec-039-serializer_mutation-0_0_11.md

<!-- package source -->
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[rf-hook-context]: ../../django_strawberry_framework/rest_framework/hook_context.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rf-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-write-tx]: ../../django_strawberry_framework/utils/write_transaction.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests -->
[tests-rf-resolvers]: ../../tests/rest_framework/test_resolvers.py
