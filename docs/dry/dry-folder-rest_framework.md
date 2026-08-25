# DRY folder integration: `django_strawberry_framework/rest_framework/`

Status: verified

## System trace

The `django_strawberry_framework/rest_framework/` subsystem integrates Django REST Framework `serializers.ModelSerializer` instances into Strawberry GraphQL write operations via `SerializerMutation` ([spec-039][spec-039]).

It consists of 6 modular components:

1. **Soft-Dependency Guard & Root Entrypoint ([`django_strawberry_framework/rest_framework/__init__.py`][rf-init]):**
   - [`_DRF_INSTALL_HINT`][rf-init] (`django_strawberry_framework/rest_framework/__init__.py::_DRF_INSTALL_HINT`): Single-sited install diagnostic.
   - [`require_drf`][rf-init] (`django_strawberry_framework/rest_framework/__init__.py::require_drf`): Centralized feature gate checking `rest_framework` availability.

2. **Hook Context & Upload Introspection Primitives ([`django_strawberry_framework/rest_framework/hook_context.py`][rf-hook-context]):**
   - [`SerializerHookContext`][rf-hook-context] (`django_strawberry_framework/rest_framework/hook_context.py::SerializerHookContext`): Frozen dataclass delivering execution context (`operation`, `write_alias`, `instance_pk`).
   - [`UploadMetadata`][rf-hook-context] (`django_strawberry_framework/rest_framework/hook_context.py::UploadMetadata`): Immutable upload file descriptor.

3. **Schema-Time Input Synthesis & Namespace Lifecycle ([`django_strawberry_framework/rest_framework/inputs.py`][rf-inputs]):**
   - [`SERIALIZER_INPUTS_MODULE_PATH`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::SERIALIZER_INPUTS_MODULE_PATH`): Dynamic input namespace identifier.
   - Constants & recursion limits: [`_NESTED_MAX_DEPTH`][rf-inputs], [`_SERIALIZER_SHAPE_REGISTRY`][rf-inputs].
   - Configuration descriptors: [`NestedSerializerConfig`][rf-inputs], [`SerializerInputShape`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::SerializerInputShape`, [`SerializerInputShape.cache_key`][rf-inputs]).
   - Input compilation & deduplication: [`build_serializer_input_class`][rf-inputs], [`build_serializer_inputs`][rf-inputs], [`dedupe_serializer_input_shape`][rf-inputs], [`materialize_serializer_input_class`][rf-inputs], [`get_serializer_input_class`][rf-inputs], [`clear_serializer_input_namespace`][rf-inputs], [`describe_serializer_input`][rf-inputs], [`serializer_input_type_name`][rf-inputs], [`_related_model_token`][rf-inputs], [`_shape_token`][rf-inputs], [`_default_full_shape_identity`][rf-inputs].
   - Field filtering, source validation & fingerprinting: [`writable_serializer_fields`][rf-inputs], [`resolve_effective_serializer_fields`][rf-inputs], [`resolve_optional_fields`][rf-inputs], [`resolve_injected_field_specs`][rf-inputs], [`guard_create_required_serializer_fields`][rf-inputs], [`guard_nested_recursion`][rf-inputs], [`raise_writable_source_ownership_errors`][rf-inputs], [`writable_source_collisions`][rf-inputs], [`writable_star_sources`][rf-inputs], [`runtime_validated_data_fields`][rf-inputs], [`serializer_schema_fingerprint`][rf-inputs], [`_fingerprint_relation_target`][rf-inputs], [`_fingerprint_choices`][rf-inputs], [`_fingerprint_converter_extra`][rf-inputs], [`_fingerprint_nested`][rf-inputs], [`_fingerprint_field_map`][rf-inputs], [`_serializer_meta_value`][rf-inputs], [`_serializer_model`][rf-inputs], [`validate_nested_config_keys`][rf-inputs], [`normalize_nested_serializer_configs`][rf-inputs], [`_required_writable_field_names`][rf-inputs], [`_collect_input_attr_collision_messages`][rf-inputs], [`_aggregate_field_problems`][rf-inputs], [`_walk_serializer_fields`][rf-inputs], [`_dedupe_and_materialize_nested`][rf-inputs], [`_resolve_nested_field`][rf-inputs].
   - Schema field reflection: [`_default_serializer_fields`][rf-inputs], [`get_serializer_for_schema`][rf-inputs].

4. **Sync & Async Write Pipeline & Security Controls ([`django_strawberry_framework/rest_framework/resolvers.py`][rf-resolvers]):**
   - Shared pipeline delegation: [`_OMITTED`][rf-resolvers], [`_SERIALIZER_ASYNC_RECOURSE`][rf-resolvers], [`_run_serializer_pipeline_sync`][rf-resolvers], [`resolve_serializer_sync`][rf-resolvers], [`resolve_serializer_async`][rf-resolvers] via [`make_resolver_entries`][mutations-resolvers] and [`run_write_pipeline_sync`][mutations-resolvers].
   - Decoding & error flattening: [`_decode_serializer_data`][rf-resolvers], [`_decode_input_object`][rf-resolvers], [`_decode_nested`][rf-resolvers], [`_decode_relation_single`][rf-resolvers], [`_decode_relation_multi`][rf-resolvers], [`serializer_errors_to_field_errors`][rf-resolvers], [`_DRF_NON_FIELD_KEY`][rf-resolvers], [`_ERROR_FLATTEN_NODE_BUDGET`][rf-resolvers], [`_error_node_children`][rf-resolvers], [`_error_leaf`][rf-resolvers], [`_error_detail_codes`][rf-resolvers], [`_rekey_segment`][rf-resolvers], [`_build_reverse_map`][rf-resolvers].
   - Hook safety & data freezing: [`_upload_metadata`][rf-resolvers], [`_hook_mapping`][rf-resolvers], [`_frozen_hook_view`][rf-resolvers], [`_injected_serializer_data`][rf-resolvers], [`_merged_serializer_kwargs`][rf-resolvers], [`_IMMUTABLE_LEAF_TYPES`][rf-resolvers], [`_FROZEN_VIEW_CONTAINERS`][rf-resolvers].
   - Runtime agreement & visibility scoping: [`_relation_model_of`][rf-resolvers], [`_assert_schema_runtime_agreement`][rf-resolvers], [`_assert_runtime_write_source_ownership`][rf-resolvers], [`_assert_field_agreement`][rf-resolvers], [`_assert_relation_agreement`][rf-resolvers], [`_assert_nested_agreement`][rf-resolvers], [`_scope_relation_querysets_to_visibility`][rf-resolvers], [`_pin_validator_querysets`][rf-resolvers], [`_scope_specs_over_serializer`][rf-resolvers], [`_assert_save_kwargs_no_shadow`][rf-resolvers], [`_assert_save_kwargs_not_model_fields`][rf-resolvers], [`_write_surface_specs`][rf-resolvers].
   - Relation intent ledger & post-save attestation: [`_RelationIntentLedger`][rf-resolvers] ([`_RelationIntentLedger.__init__`][rf-resolvers], [`_RelationIntentLedger.record`][rf-resolvers], [`_RelationIntentLedger.consume`][rf-resolvers], [`_RelationIntentLedger.assert_fully_consumed`][rf-resolvers]), [`_relation_object_identity`][rf-resolvers], [`_relation_intent_snapshot`][rf-resolvers], [`_relation_identity_intact`][rf-resolvers], [`_instrument_relation_intent`][rf-resolvers], [`_instrument_intent_specs`][rf-resolvers], [`_record_field_intent`][rf-resolvers], [`_assert_relation_intent`][rf-resolvers], [`_assert_intent_specs`][rf-resolvers], [`_m2m_membership_snapshot`][rf-resolvers], [`_attestable_m2m_fields`][rf-resolvers], [`_attest_saved_relations`][rf-resolvers].
   - Savepoint execution & ORM witnessing: [`_write_witness`][rf-resolvers], [`_checked_saved_result`][rf-resolvers], [`_serializer_write_step`][rf-resolvers], [`_guarded_serializer_write`][rf-resolvers], [`_serializer_decode_step`][rf-resolvers].

5. **DRF Field Converter Registry & GraphQL Type Mapping ([`django_strawberry_framework/rest_framework/serializer_converter.py`][rf-converter]):**
   - Conversion primitives & types: [`SerializerFieldConversion`][rf-converter], [`SerializerFieldConverter`][rf-converter], [`NESTED_SINGLE`][rf-converter], [`NESTED_MULTI`][rf-converter], [`_scalar_converter`][rf-converter], [`_model_field_converter`][rf-converter], [`_CONVERT_RELATION_MULTI`][rf-converter], [`_CONVERT_RELATION_SINGLE`][rf-converter], [`_CONVERT_FILE`][rf-converter], [`_CONVERT_MULTIPLE_CHOICE`][rf-converter], [`_BUILTIN_SCALAR_CONVERTERS`][rf-converter], [`_SERIALIZER_FIELD_CONVERTERS`][rf-converter], [`register_serializer_field_converter`][rf-converter], [`_SERIALIZER_CHOICE_ENUMS`][rf-converter], [`clear_serializer_choice_enums`][rf-converter].
   - Nested inspection: [`is_nested_serializer_field`][rf-converter], [`nested_serializer_child`][rf-converter], [`_reject_nested_serializer`][rf-converter].
   - Validation & dispatch: [`_reject_unsupported_relation_field`][rf-converter], [`_list_child_conversion`][rf-converter], [`_finish_serializer_conversion`][rf-converter], [`convert_serializer_field`][rf-converter], [`_unsupported_serializer_field`][rf-converter], [`_relation_cardinality`][rf-converter], [`_model_relation_cardinality`][rf-converter], [`_reject_relation_cardinality_mismatch`][rf-converter].
   - Metadata & naming: [`serializer_field_graphql_name`][rf-converter], [`serializer_field_description`][rf-converter], [`require_one_segment_source`][rf-converter], [`backing_model_field`][rf-converter], [`_require_relation_primary`][rf-converter], [`serializer_only_relation_annotation`][rf-converter].
   - Model-backed & Choice enums: [`_is_consumer_declared`][rf-converter], [`_scalar_name`][rf-converter], [`_model_backed_scalar_annotation`][rf-converter], [`_is_enumerable_serializer_choice`][rf-converter], [`_enum_member_map`][rf-converter], [`_serializer_choice_enum`][rf-converter], [`_serializer_choice_annotation`][rf-converter], [`_serializer_only_scalar_annotation`][rf-converter], [`resolve_serializer_field`][rf-converter].

6. **Serializer Mutation Base & Declaration Seams ([`django_strawberry_framework/rest_framework/sets.py`][rf-sets]):**
   - Meta validation: [`_ALLOWED_SERIALIZER_META_KEYS`][rf-sets], [`_SERIALIZER_OPERATION_NESTED_WRITE_METHOD`][rf-sets], [`_validate_schema_field_map`][rf-sets], [`_checked_schema_field_map`][rf-sets], [`_validate_serializer_nested_fields`][rf-sets], [`_assert_schema_source_ownership`][rf-sets], [`_serializer_input_shape_for`][rf-sets].
   - Foundation class: [`SerializerMutation`][rf-sets] (`django_strawberry_framework/rest_framework/sets.py::SerializerMutation`) subclassing [`DjangoMutation`][mutations-sets] with attributes [`SerializerMutation.input_module_path`][rf-sets], [`SerializerMutation._input_field_specs`][rf-sets], [`SerializerMutation._injected_field_specs`][rf-sets], [`SerializerMutation._input_type_name`][rf-sets], overrides [`SerializerMutation._resolve_model`][rf-sets], [`SerializerMutation._validate_meta`][rf-sets], [`SerializerMutation.get_serializer_for_schema`][rf-sets], [`SerializerMutation.build_input`][rf-sets], [`SerializerMutation.input_type_name`][rf-sets], and hooks [`SerializerMutation.get_serializer_kwargs`][rf-sets], [`SerializerMutation.get_serializer_injected_data`][rf-sets], [`SerializerMutation.get_serializer_save_kwargs`][rf-sets], [`SerializerMutation.resolve_sync`][rf-sets], [`SerializerMutation.resolve_async`][rf-sets].

Connected behavior examined:
- [`django_strawberry_framework/mutations/`][mutations-sets]: Core mutation foundation, transaction execution pipeline, and shared input resolution.
- [`django_strawberry_framework/utils/write_transaction.py`][utils-write-tx]: Shared atomic savepoint and cross-alias enforcement.
- [`django_strawberry_framework/utils/write_values.py`][utils-write-values]: Shared decoding and visibility validation primitives.
- [`django_strawberry_framework/utils/converters.py`][utils-converters]: Shared `convert_with_mro` skeleton.
- [`django_strawberry_framework/types/converters.py`][types-converters]: Read-side scalar and choice enum conversion.
- [`tests/rest_framework/`][tests-rf]: Comprehensive test suite covering serializer converters, inputs, resolvers, sets, and error handling.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/rest_framework/ --include-constants`):
- Parsed 6 target files across `django_strawberry_framework/rest_framework/`.
- Total symbols covered across all 6 files.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   The `rest_framework/` subsystem integrates cleanly with the package's unified mutation framework. Transaction handling, pre-auth execution, and re-fetching delegate to `mutations/resolvers.py`. Declaration registration, metaclass validation, and payload binding subclass `DjangoMutation` in `mutations/sets.py`. Field conversion utilizes `utils/converters.py` and `types/converters.py`. DRF-specific behaviors (such as recursive error flattening, frozen hook data isolation, relation intent tracking, and nested serializer recursion) are single-sited in `rest_framework/`.

2. **Sync and async twins:**
   Resolver execution and registration are paired via `make_resolver_entries` and `resolver_seams` from `mutations/`. Field conversion and input compilation run synchronously at schema bind time. Zero duplication between sync and async execution paths.

3. **Derived rather than repeated knowledge:**
   Schema-time discovery is fingerprinted via `serializer_schema_fingerprint` to prevent drift between validation and bind. Write source ownership and relation metadata are derived once and passed to runtime resolvers without re-introspecting serializers.

4. **Inverse and round-trip pairs:**
   `_write_witness` manages symmetrical signal registration/teardown. `_RelationIntentLedger` enforces exact parity between recorded validation outputs and consumed write intent. Choice enum caches are reset symmetrically via registered subsystem clear callbacks.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: `django_strawberry_framework/rest_framework/`, `django_strawberry_framework/mutations/`, `django_strawberry_framework/utils/`;
   - Specifications: [`docs/SPECS/spec-039-serializer_mutation-0_0_11.md`][spec-039];
   - Test suites: [`tests/rest_framework/`][tests-rf];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Modifying the DRF error flattening node budget or non-field error key mapping):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/rest_framework/resolvers.py`][rf-resolvers] ([`_ERROR_FLATTEN_NODE_BUDGET`][rf-resolvers] / [`_DRF_NON_FIELD_KEY`][rf-resolvers]).
  - *Propagation count:* 0 in other modules.
- **Posited change 2 (Adjusting the shared write transaction lifecycle or authorization pre-auth ordering):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/mutations/resolvers.py`][mutations-resolvers] ([`run_write_pipeline_sync`][mutations-resolvers]).
  - *Propagation count:* 0 in `rest_framework/`.
- **Posited change 3 (Adding a new built-in DRF serializer field conversion):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/rest_framework/serializer_converter.py`][rf-converter] ([`_BUILTIN_SCALAR_CONVERTERS`][rf-converter]).
  - *Propagation count:* 0 in other modules.

### Rejected candidates

1. **Re-implementing the write transaction skeleton independently for serializers:**
   - Disproved per [spec-039][spec-039]. Using `run_write_pipeline_sync` ensures uniform authorization and transaction safety across form, model, and serializer mutations.
2. **Re-implementing field conversion dispatch independently:**
   - Disproved per [spec-039][spec-039]. Using `convert_with_mro` ensures consistent MRO lookup and error reporting.

## Opportunities

None — the `django_strawberry_framework/rest_framework/` subsystem is completely integrated and consolidated at root owners.

## Judgment

Verified. `rest_framework/` exhibits zero duplicate code and complete policy consolidation through shared mutation, transaction, and converter infrastructure. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/ --review docs/dry/dry-folder-rest_framework.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of the `django_strawberry_framework/rest_framework/` subsystem and Worker 1's DRY review.

1. **Subsystem Architecture & Shared Foundation Integration:**
   - Verified that all 6 files in `django_strawberry_framework/rest_framework/` cleanly separate DRF-specific requirements from general mutation mechanics.
   - Verified that `mutations/sets.py`, `mutations/resolvers.py`, `utils/write_transaction.py`, `utils/write_values.py`, and `utils/converters.py` own all shared mutation primitives.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes across the subsystem and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/ --review docs/dry/dry-folder-rest_framework.md --include-constants`. 100% coverage across all target definitions in the folder.

Confirmed: `django_strawberry_framework/rest_framework/` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-039]: ../SPECS/spec-039-serializer_mutation-0_0_11.md

<!-- package source -->
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[rf-hook-context]: ../../django_strawberry_framework/rest_framework/hook_context.py
[rf-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rf-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py
[utils-write-tx]: ../../django_strawberry_framework/utils/write_transaction.py
[utils-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests -->
[tests-rf]: ../../tests/rest_framework/
