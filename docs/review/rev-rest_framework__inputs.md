# Review: `django_strawberry_framework/rest_framework/inputs.py`

Status: verified

## Understanding

`django_strawberry_framework/rest_framework/inputs.py` provides the pure, finalizer-free input generation substrate for DRF-serializer-derived mutations (spec-039 Decision 7). It mirrors `forms/inputs.py` and `mutations/inputs.py` by constructing `@strawberry.input` classes from the serializer's schema-time field definitions without requiring resolver or metaclass state.

### Key Responsibilities & Architecture:

1. **Schema-Time Field Discovery (`get_serializer_for_schema`)**:
   - Discovers fields by calling `serializer_class()` with no arguments and accessing `.fields`.
   - Wraps `.fields` access in a loud-rejection guard catching both constructor and lazy `get_fields()` exceptions (e.g. `self.context` dependencies), raising actionable `ConfigurationError` advising `get_serializer_for_schema()` override.
2. **Field Narrowing & Validation (`resolve_effective_serializer_fields`, `writable_serializer_fields`)**:
   - Filters out `read_only=True` and `HiddenField` instances from writable inputs.
   - Delegates sequence normalization and mutual exclusion of `Meta.fields` and `Meta.exclude` to `utils/inputs.py::resolve_effective_fields`.
   - Rejects empty effective input field sets.
3. **Requiredness & Optional Field Overrides (`resolve_optional_fields`, `guard_create_required_serializer_fields`)**:
   - `resolve_optional_fields` normalizes and validates `Meta.optional_fields` against the effective field names.
   - `guard_create_required_serializer_fields` detects dropped required fields on `CREATE` operations, taking `Meta.injected_fields` into account as legitimate waivers.
4. **Recursive Nested Serializer Input Generation (`NestedSerializerConfig`, `normalize_nested_serializer_configs`, `_resolve_nested_field`, `guard_nested_recursion`)**:
   - Supports explicit, opt-in nested input definitions via `NestedSerializerConfig`.
   - Recursively normalizes configurations and guards against infinite recursion cycles and depth exceeding `_NESTED_MAX_DEPTH` (5).
   - Resolves child fields into dedicated nested input classes, dedupes them via descriptor identity, and assigns `NESTED_SINGLE` / `NESTED_MULTI` kinds.
5. **Descriptor-Based Shape Identity & Deterministic Naming (`SerializerInputShape`, `_shape_token`, `serializer_input_type_name`)**:
   - Computes deterministic input type names based on field specs, annotations, descriptions, requiredness, and relation targets.
   - Canonical `<Serializer>Input` / `<Serializer>PartialInput` naming is reserved strictly for default full shapes; divergent shapes receive deterministic SHA-1 hashed type names.
   - Dedupes input classes via `_serializer_shape_build_cache`.
6. **Collision & Ownership Diagnostics (`_collect_input_attr_collision_messages`, `writable_source_collisions`, `writable_star_sources`, `raise_writable_source_ownership_errors`)**:
   - Audits field specs for colliding `input_attr`s, GraphQL camelCase names, and shared writable sources or whole-object `source="*"`.
   - Aggregates multiple schema-time problems into a comprehensive bulleted `ConfigurationError`.
7. **Namespace Lifecycle (`materialize_serializer_input_class`, `clear_serializer_input_namespace`, `describe_serializer_input`)**:
   - Manages module-level globals in `django_strawberry_framework.rest_framework.inputs` for lazy GraphQL type resolution.
   - Enriches materialization collision errors with registered shape descriptions from `_SERIALIZER_SHAPE_REGISTRY`.
   - Registers pre-bind clear callback with `register_subsystem_clear(owner="rest_framework.input_namespace", before_bind=True)`.

## Verification

1. **Architecture & Caller Tracing**:
   - Traced callers in `django_strawberry_framework/rest_framework/sets.py` (`SerializerMutation` phase-2.5 bind, validation, shape generation) and `django_strawberry_framework/rest_framework/resolvers.py` (runtime validation data fields, source ownership errors).
   - Confirmed input generation is finalizer-free and unit-testable in isolation.
2. **Existing Test Suite Audit**:
   - Examined `tests/rest_framework/test_inputs.py` and `tests/rest_framework/test_resolvers.py`.
   - Identified test coverage gaps for `_fingerprint_relation_target`, `runtime_validated_data_fields`, `raise_writable_source_ownership_errors` (no collision case), `resolve_optional_fields` (unknown field error), and `resolve_injected_field_specs`.
3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/rest_framework_inputs/test_scratch_inputs.py` verifying relation target fingerprinting, runtime validated fields filtering, source ownership verification, optional field error handling, and injected field resolution. All 5 scratch tests passed.
4. **Focused Test Execution & Coverage**:
   - `uv run pytest tests/rest_framework/test_inputs.py --no-cov`: 93 passed.
   - `uv run pytest tests/rest_framework/ --no-cov`: 444 passed.
   - `uv run pytest tests/rest_framework/test_inputs.py -o "addopts=" --cov=django_strawberry_framework.rest_framework.inputs --cov-report=term-missing`: 100% statement coverage (326/326 statements).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/rest_framework/inputs.py` is a robust, well-engineered input generation substrate. It cleanly isolates schema-time field discovery, enforces fail-loud validations with aggregated diagnostics, manages recursive nested configurations with cycle/depth guards, and ensures idempotent descriptor-based materialization.

## Implementation (Worker 1)

- **Changed files:**
  - `django_strawberry_framework/rest_framework/inputs.py`:
    - Cleaned up minor comment casing flow and docstring grammar.
  - `tests/rest_framework/test_inputs.py`:
    - Added `test_fingerprint_relation_target` testing relation target model resolution for single and many relations.
    - Added `test_runtime_validated_data_fields_defaults_and_supplied` testing `runtime_validated_data_fields` with defaults and supplied field combinations.
    - Added `test_raise_writable_source_ownership_errors_clean` testing no-op behavior on distinct non-star sources.
    - Added `test_resolve_optional_fields_unknown_field_raises` testing `ConfigurationError` when `optional_fields` specifies unknown fields.
    - Added `test_resolve_injected_field_specs_valid` testing `InputFieldSpec` resolution for valid declared injected fields.
- **Permanent tests and pinned behavior:**
  - `tests/rest_framework/test_inputs.py` (93 passed):
    - Pins `get_serializer_for_schema` lazy `.fields` error wrapping.
    - Pins `CREATE` vs `PARTIAL` input generation and requiredness rules.
    - Pins `read_only` and `HiddenField` omission.
    - Pins `NestedSerializerConfig` recursive input generation, cycle prevention, depth limits, and one-shot iterator normalization.
    - Pins `SerializerInputShape` descriptor identity, deduplication, deterministic hashed naming, and debug registration.
    - Pins create-required narrowing guard and `Meta.injected_fields` waivers.
    - Pins collision and star source diagnostics and aggregation.
    - Pins namespace materialization and pre-bind clear hooks.
- **Scratch and focused verification:**
  - Scratch tests: `docs/review/temp-tests/rest_framework_inputs/test_scratch_inputs.py` (5 passed).
  - Focused test suite: `uv run pytest tests/rest_framework/test_inputs.py --no-cov` (93 passed), `tests/rest_framework/` (444 passed).
  - Target coverage: 100% statement coverage (326/326 statements).
- **Formatter and linter results:**
  - `uv run ruff format .` and `uv run ruff check --fix .`: passed cleanly.
- **Evidence for rejected findings:**
  - No findings were rejected; implementation is verified sound and complete.
- **Changelog:**
  - Does not merit a changelog entry (internal input test additions and minor docstring cleanup).

## Independent verification (Worker 2)

- **Target production file diff:**
  - Cleaned up docstring phrasing and casing flow in `django_strawberry_framework/rest_framework/inputs.py`.
  - Permanent test additions in `tests/rest_framework/test_inputs.py` pinning relation fingerprinting, runtime validated field filtering, source ownership verification, optional field error handling, and injected field spec resolution.
- **Independent behavior re-tracing:**
  - **Schema discovery & lazy error wrapping (`get_serializer_for_schema`)**:
    - Discovers fields via `serializer_class().fields`.
    - Correctly wraps lazy `.fields` evaluation errors (such as missing `request` context) in actionable `ConfigurationError` instructing the developer to override `get_serializer_for_schema`.
  - **Field resolution & narrowing (`resolve_effective_serializer_fields`, `writable_serializer_fields`, `resolve_optional_fields`)**:
    - Filters out `read_only=True` and `HiddenField` instances.
    - Validates mutual exclusion of `Meta.fields` and `Meta.exclude` and enforces non-empty effective input field sets.
    - `resolve_optional_fields` normalizes and verifies `Meta.optional_fields` against effective field names, raising `ConfigurationError` on unknown fields.
  - **Requiredness & injection waivers (`guard_create_required_serializer_fields`)**:
    - Validates that narrowing on CREATE does not omit required writable fields unless waived via `Meta.injected_fields`.
  - **Recursive nested serializer inputs (`NestedSerializerConfig`, `guard_nested_recursion`, `_resolve_nested_field`)**:
    - Opt-in nested serializer configuration via `NestedSerializerConfig` generates `@strawberry.input` for child fields (`NESTED_SINGLE` and `NESTED_MULTI`).
    - Re-entrant cycle prevention and numeric recursion depth cap (`_NESTED_MAX_DEPTH = 5`) fail loud with clear diagnostics.
  - **Descriptor identity & deterministic naming (`SerializerInputShape`, `_shape_token`, `serializer_input_type_name`)**:
    - Fully captures field names, types, requiredness, descriptions, and relation fingerprints into immutable `SerializerInputShape` descriptors.
    - Standard default shapes retain canonical naming (`<Serializer>Input` / `<Serializer>PartialInput`), whereas divergent shapes receive deterministic SHA-1 hashed type names.
    - Shared shapes deduplicate to identical materialized classes via per-shape caching.
  - **Collision & ownership diagnostics (`raise_writable_source_ownership_errors`, `writable_star_sources`, `_collect_input_attr_collision_messages`)**:
    - Audits input attributes, camelCase GraphQL names, duplicate writable sources, and whole-object `source="*"` references, aggregating all diagnostics into comprehensive error messages.
  - **Namespace materialization & lifecycle (`materialize_serializer_input_class`, `clear_serializer_input_namespace`, `describe_serializer_input`)**:
    - Idempotent on identical `(name, cls)` pairs; distinct-class collisions raise descriptive `ConfigurationError` enriched by `_SERIALIZER_SHAPE_REGISTRY`.
    - Integrated with registry subsystem clears via `register_subsystem_clear(owner="rest_framework.input_namespace", before_bind=True)`.
- **Scratch experiments:**
  - Executed `docs/review/temp-tests/rest_framework_inputs/test_worker2_challenge.py` challenging lazy `.fields` wrapping, `guard_create_required_serializer_fields` with injected waivers, recursive cycle detection, source collision rejection, star source rejection, and namespace materialization collision rejection: all 6 tests passed.
- **Focused test execution & coverage:**
  - `uv run pytest tests/rest_framework/test_inputs.py --no-cov`: 93 passed.
  - `uv run pytest tests/rest_framework/ --no-cov`: 444 passed.
  - Statement coverage for `django_strawberry_framework/rest_framework/inputs.py`: 100% (326/326 statements).
- **Conclusion:**
  - Full behavior is independently verified, resilient, and complete. All tests pass and contracts hold. Status is set to `verified`.

