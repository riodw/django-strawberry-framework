# DRY review: `django_strawberry_framework/rest_framework/inputs.py`

Status: verified

## System trace

`django_strawberry_framework/rest_framework/inputs.py` is the pure schema-time `@strawberry.input` generation engine for DRF serializers and model serializers ([spec-039][spec-039]).

It owns the following architectural responsibilities:

1. **Namespace & Cache Lifecycle Management:**
   - [`SERIALIZER_INPUTS_MODULE_PATH`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::SERIALIZER_INPUTS_MODULE_PATH`): Module string for `strawberry.lazy(...)` resolution.
   - Namespace trio ([`_materialized_names`][rf-inputs], [`_materialize_input`][rf-inputs], [`_clear_input_namespace`][rf-inputs]): Produced via [`make_input_namespace`][utils-inputs].
   - [`materialize_serializer_input_class`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::materialize_serializer_input_class`): Sets input classes as module globals and attaches shape debug metadata on collision.
   - [`clear_serializer_input_namespace`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::clear_serializer_input_namespace`): Resets materialized ledger and debug registry via [`register_subsystem_clear`][registry].
   - Shape build cache ([`_serializer_shape_build_cache`][rf-inputs], [`clear_serializer_shape_build_cache`][rf-inputs]): Created via [`make_shape_build_cache`][utils-inputs] and registered via [`register_subsystem_clear`][registry].

2. **Nested Serializer Configuration & Validation:**
   - [`_NESTED_MAX_DEPTH`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::_NESTED_MAX_DEPTH`): Pinned nesting recursion cap (5).
   - [`NestedSerializerConfig`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::NestedSerializerConfig`): Frozen dataclass specifying explicit opt-in configuration for nested input generation ([`NestedSerializerConfig.fields`][rf-inputs], [`NestedSerializerConfig.exclude`][rf-inputs], [`NestedSerializerConfig.optional_fields`][rf-inputs], [`NestedSerializerConfig.nested_fields`][rf-inputs]).
   - [`normalize_nested_serializer_configs`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::normalize_nested_serializer_configs`): Materializes sequence selectors across config trees.
   - [`validate_nested_config_keys`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::validate_nested_config_keys`): Verifies nested config keys correspond to effective nested serializer fields.
   - [`guard_nested_recursion`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::guard_nested_recursion`): Enforces cycle detection and maximum recursion depth limits.

3. **Schema Field Discovery & Determinism Fingerprinting:**
   - [`get_serializer_for_schema`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::get_serializer_for_schema`): Default discovery constructing no-arg serializer instances and reading `.fields`.
   - Fingerprint helpers: [`_fingerprint_relation_target`][rf-inputs], [`_fingerprint_choices`][rf-inputs], [`_fingerprint_converter_extra`][rf-inputs], [`_fingerprint_nested`][rf-inputs], [`_fingerprint_field_map`][rf-inputs].
   - [`serializer_schema_fingerprint`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::serializer_schema_fingerprint`): Generates stable, request-independent fingerprints of schema-time field maps to enforce declaration-time vs bind-time determinism.

4. **Field Introspection & Collision Detection:**
   - [`_serializer_meta_value`][rf-inputs] & [`_serializer_model`][rf-inputs]: Extracts `Meta.model` from serializers.
   - [`writable_serializer_fields`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::writable_serializer_fields`): Drops `read_only` and `HiddenField` instances.
   - [`runtime_validated_data_fields`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::runtime_validated_data_fields`): Resolves runtime fields contributing to validated data.
   - Collision checks: [`writable_source_collisions`][rf-inputs], [`writable_star_sources`][rf-inputs], [`raise_writable_source_ownership_errors`][rf-inputs].
   - [`resolve_effective_serializer_fields`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::resolve_effective_serializer_fields`): Applies `Meta.fields` / `Meta.exclude` narrowing via [`resolve_effective_fields`][utils-inputs].
   - [`resolve_optional_fields`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::resolve_optional_fields`): Normalizes and validates `Meta.optional_fields`.
   - [`resolve_injected_field_specs`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::resolve_injected_field_specs`): Computes specs for fields supplied via `get_serializer_injected_data`.

5. **Shape Identity, Debug Registry & Type Name Resolution:**
   - [`SerializerInputShape`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::SerializerInputShape`): Comprehensive frozen descriptor capturing [`SerializerInputShape.serializer_class`][rf-inputs], [`SerializerInputShape.operation_kind`][rf-inputs], [`SerializerInputShape.field_specs`][rf-inputs], [`SerializerInputShape.annotations`][rf-inputs], [`SerializerInputShape.descriptions`][rf-inputs], [`SerializerInputShape.required_state`][rf-inputs], [`SerializerInputShape.optional_fields`][rf-inputs], [`SerializerInputShape.type_name`][rf-inputs], and property [`SerializerInputShape.cache_key`][rf-inputs].
   - [`_SERIALIZER_SHAPE_REGISTRY`][rf-inputs] & [`describe_serializer_input`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::describe_serializer_input`): Diagnostic debug registry providing multi-line descriptions of registered input shapes.
   - Naming helpers: [`_related_model_token`][rf-inputs], [`_shape_token`][rf-inputs], [`serializer_input_type_name`][rf-inputs].

6. **Input Construction & AST Generation:**
   - [`_required_writable_field_names`][rf-inputs] & [`guard_create_required_serializer_fields`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::guard_create_required_serializer_fields`): Enforces presence of required writable fields on create operations via [`guard_dropped_required`][utils-inputs].
   - [`_collect_input_attr_collision_messages`][rf-inputs] & [`_aggregate_field_problems`][rf-inputs]: Aggregates conversion and collision diagnostics.
   - [`_walk_serializer_fields`][rf-inputs] (`django_strawberry_framework/rest_framework/inputs.py::_walk_serializer_fields`): Iterates over effective fields, converts AST types, applies widening via [`optional_input_field`][utils-inputs], and gathers triples.
   - [`_resolve_nested_field`][rf-inputs], [`_dedupe_and_materialize_nested`][rf-inputs], [`dedupe_serializer_input_shape`][rf-inputs]: Manages recursive resolution and deduplication via [`get_or_store_shape_build`][utils-inputs].
   - [`_default_full_shape_identity`][rf-inputs]: Determines default full shape for canonical name reservation.
   - Public generators: [`build_serializer_input_class`][rf-inputs] and [`build_serializer_inputs`][rf-inputs].

Connected behavior examined:
- [`django_strawberry_framework/rest_framework/serializer_converter.py`][rf-converter]: Implements per-field conversion logic (`resolve_serializer_field`, `serializer_field_description`, `require_one_segment_source`).
- [`django_strawberry_framework/rest_framework/sets.py`][rf-sets]: Binds generated inputs to `SerializerMutation` classes during phase 2.5 finalization.
- [`django_strawberry_framework/rest_framework/resolvers.py`][rf-resolvers]: Consumes reverse-map specs from input shapes during request execution.
- [`django_strawberry_framework/utils/inputs.py`][utils-inputs]: Central repository for shared input generation algorithms and data structures.
- [`tests/rest_framework/`][tests-rf]: Verifies serializer input generation, nested structures, collisions, and error reporting.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/rest_framework/inputs.py --include-constants`):
- Parsed 1 target file, 1,796 lines.
- Complete inventory across all 46 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `rest_framework/inputs.py` delegates common input-building patterns to [`django_strawberry_framework/utils/inputs.py`][utils-inputs] (`make_input_namespace`, `make_shape_build_cache`, `resolve_effective_fields`, `normalize_field_name_sequence`, `guard_dropped_required`, `iter_input_field_collisions`, `optional_input_field`, `pascalize_token`, `generated_input_type_name`, `build_strawberry_input_class`). Logic specific to DRF serializers (`writable_serializer_fields`, `runtime_validated_data_fields`, `writable_source_collisions`, `writable_star_sources`, `serializer_schema_fingerprint`, `_walk_serializer_fields`, `NestedSerializerConfig`, `_resolve_nested_field`, `describe_serializer_input`, `SerializerInputShape`) is single-sited here.

2. **Sync and async twins:**
   Zero duplication. Schema-time AST and type synthesis is strictly synchronous.

3. **Derived rather than repeated knowledge:**
   `SerializerInputShape` acts as the single source of truth for shape attributes and reverse-mapping specs. `serializer_schema_fingerprint` derives its hashable structure directly from the schema-time field map.

4. **Inverse and round-trip pairs:**
   `materialize_serializer_input_class` and `clear_serializer_input_namespace` form a clean lifecycle pair wired into framework resets.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/rest_framework/inputs.py`][rf-inputs], [`django_strawberry_framework/rest_framework/sets.py`][rf-sets], [`django_strawberry_framework/rest_framework/resolvers.py`][rf-resolvers], [`django_strawberry_framework/utils/inputs.py`][utils-inputs];
   - Specifications: [`docs/SPECS/spec-039-serializer_mutation-0_0_11.md`][spec-039];
   - Test suites: [`tests/rest_framework/`][tests-rf];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Modifying shared input namespace or cache behavior):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/inputs.py`][utils-inputs].
  - *Propagation count:* 0 in `rest_framework/inputs.py`.
- **Posited change 2 (Altering nested serializer maximum recursion depth `_NESTED_MAX_DEPTH`):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/rest_framework/inputs.py`][rf-inputs] ([`_NESTED_MAX_DEPTH`][rf-inputs]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying the writable field filter predicate for DRF serializers):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/rest_framework/inputs.py`][rf-inputs] ([`writable_serializer_fields`][rf-inputs]).
  - *Propagation count:* 0 in other files.

### Rejected candidates

1. **Re-implementing namespace ledgers and shape caching independently:**
   - Disproved per [spec-039][spec-039]. Using `make_input_namespace` and `make_shape_build_cache` from `utils/inputs.py` ensures consistency across mutations, forms, and serializers.
2. **Duplicating field collision and dropped required checks:**
   - Disproved per [spec-039][spec-039]. Reusing `iter_input_field_collisions` and `guard_dropped_required` guarantees consistent validation semantics.

## Opportunities

None — `django_strawberry_framework/rest_framework/inputs.py` is fully consolidated with shared infrastructure in `django_strawberry_framework/utils/inputs.py`.

## Judgment

Verified. `rest_framework/inputs.py` exhibits zero duplicate code and complete policy consolidation through `utils/inputs.py` and `rest_framework/serializer_converter.py`. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/inputs.py --review docs/dry/dry-file-rest_framework__inputs.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/rest_framework/inputs.py`][rf-inputs] and Worker 1's DRY review.

1. **DRF Input Generation & Subsystem Consolidation:**
   - Confirmed `build_serializer_input_class` and `build_serializer_inputs` leverage shared input builders and namespace ledgers from `utils/inputs.py`.
   - Confirmed recursive nested serializer input resolution and determinism fingerprinting are robustly implemented.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/rest_framework/inputs.py --review docs/dry/dry-file-rest_framework__inputs.md --include-constants`. 100% coverage across all 46 definitions.

Confirmed: `django_strawberry_framework/rest_framework/inputs.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-039]: ../SPECS/spec-039-serializer_mutation-0_0_11.md

<!-- package source -->
[registry]: ../../django_strawberry_framework/registry.py
[rf-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests -->
[tests-rf]: ../../tests/rest_framework/
