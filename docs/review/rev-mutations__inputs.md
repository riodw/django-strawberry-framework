# Review: `django_strawberry_framework/mutations/inputs.py`

Status: verified

## Understanding

`django_strawberry_framework/mutations/inputs.py` provides the input generation substrate and payload wrapper for write-side mutations (spec-036, spec-037, spec-038, spec-039, spec-040, spec-051):

1. **Input Namespace & Parked Globals Lifecycle**: Owns the `INPUTS_MODULE_PATH` (`"django_strawberry_framework.mutations.inputs"`) ledger via `make_input_namespace`, materializing generated input dataclasses as module globals for lazy forward resolution, and registering `clear_mutation_input_namespace` with `register_subsystem_clear` for pre-bind cache invalidation.
2. **Field Selection & Filtering**: `editable_input_fields` selects concrete editable model columns and forward `ManyToManyField`s, dropping the primary key, auto-timestamp (`editable=False`) columns, and reverse relations. It narrows by `fields` or `exclude` sequences and rejects unknown/non-editable names via `ConfigurationError`.
3. **Requiredness & Typing**: `input_field_required` defines the create-input requiredness rule (required only when `null=False`, `blank=False`, and `has_default()=False`). `relation_id_scalar` and `relation_id_annotation` map relations to `relay.GlobalID` when the related model's primary `DjangoType` implements `relay.Node`, or to raw pk scalars otherwise. `model_column_write_kind` and `model_column_input_annotation` classify columns (`SCALAR`, `RELATION_SINGLE`, `RELATION_MULTI`, `FILE` -> `Upload`).
4. **Collision Detection & Deduplication**: Employs `iter_input_field_collisions` to detect and reject collisions between generated Python input attributes and GraphQL camelCase names (e.g. `category` FK mapping to `category_id` vs an explicit `category_id` M2M, or `foo_bar` vs `fooBar`). `mutation_input_shape` and `mutation_input_type_name` produce deterministic type names with injectivity over token boundaries.
5. **Reverse Map Specs & Decoders**: `mutation_input_field_specs` constructs `InputFieldSpec` records and Django field mappings for bind-time decoding, handling `EXCLUDED` capture attributes (spec-040 D6).
6. **Payload Envelope**: Defines the public `FieldError` `@strawberry.type` (`field`, `messages`, `codes`, `path`) and `build_payload_type` to build `<Name>Payload` types for both model-backed (`node` / `result` slot + `errors`) and model-less (`ok: bool` + `errors`) mutations.

## Verification

1. **Existing Test Suite**: Ran `tests/mutations/test_inputs.py` (64 tests) covering field selection, create/partial input generation, FK/O2O/M2M typing, Relay GlobalID resolution, consumer overrides, collision guards, file/upload mapping, and `FieldError` public exports.
2. **Cross-Subsystem Verification**: Ran 1,153 tests across `tests/mutations/`, `tests/forms/`, `tests/auth/`, and `tests/rest_framework/` verifying that shared relation typing, column classification, and payload generation work harmoniously.
3. **Scratch Experiment**: Executed `docs/review/temp-tests/mutations_inputs/test_scratch.py` verifying model-less payload construction (`object_type=None` -> `ok: bool`, `errors: list[FieldError]`) and automatic `object_slot` derivation from `object_type`.

## Improvements

### High

None.

### Medium

None.

### Low

#### 1. Optional `object_slot` default in `build_payload_type`

- **Observation:** `build_payload_type` required caller to pass `object_slot` explicitly when `object_type` is non-`None`, even though `payload_object_slot(object_type)` is the deterministic, canonical derivation for all model-backed payloads.
- **Evidence:** Callers in `mutations/sets.py` and `auth/mutations.py` repeatedly invoked `object_slot=payload_object_slot(...)`. If `object_slot` was omitted, the namespace was constructed with a `None` key.
- **Impact:** Minor caller ergonomics and safety risk if `object_slot` was omitted with a non-`None` `object_type`.
- **Recommendation:** Default `object_slot: str | None = None` in `build_payload_type` and fall back to `payload_object_slot(object_type)` when `object_type is not None`.
- **Proof:** Permanent tests `test_payload_model_less_shape` and `test_payload_slot_defaults_from_object_type` verify both model-less and auto-slotted model payloads.

#### 2. Direct unit test coverage for model-less payloads in `test_inputs.py`

- **Observation:** While `tests/auth/test_mutations.py` and `tests/forms/test_sets.py` indirectly exercised model-less payloads (e.g. `LogoutPayload`), `tests/mutations/test_inputs.py` lacked a direct unit test for `build_payload_type(..., object_type=None)`.
- **Evidence:** `tests/mutations/test_inputs.py` only tested Relay `node` and non-Relay `result` model-backed payloads.
- **Impact:** Gaps in unit-level contract assertions for the shared payload builder.
- **Recommendation:** Add dedicated unit tests in `tests/mutations/test_inputs.py` asserting `ok: bool` and `errors: list[FieldError]` on model-less payloads.
- **Proof:** `test_payload_model_less_shape` passes in `tests/mutations/test_inputs.py`.

## Summary

`django_strawberry_framework/mutations/inputs.py` is a robust, well-factored generation engine with solid collision detection, type mapping, and namespace lifecycle management. The `build_payload_type` helper now safely defaults `object_slot` when omitted, and direct unit coverage covers all payload shapes.

## Implementation (Worker 1)

- **Changed files**:
  - `django_strawberry_framework/mutations/inputs.py`: Defaulted `object_slot: str | None = None` in `build_payload_type` with fallback to `payload_object_slot(object_type)` when `object_type` is provided; fixed comment typo in pre-bind clear registration.
  - `tests/mutations/test_inputs.py`: Added permanent unit tests `test_payload_model_less_shape` and `test_payload_slot_defaults_from_object_type`.
- **Permanent tests**:
  - `tests/mutations/test_inputs.py::test_payload_model_less_shape`: Pins model-less `{ ok: bool, errors: list[FieldError] }` payload structure.
  - `tests/mutations/test_inputs.py::test_payload_slot_defaults_from_object_type`: Pins automatic uniform slot resolution (`node` vs `result`) when `object_slot` is omitted.
- **Verification**: Focused test runs of `tests/mutations/test_inputs.py` (66 passed) and all related suites across `mutations`, `forms`, `auth`, `rest_framework` (1,153 passed). Scratch test executed under `docs/review/temp-tests/mutations_inputs/test_scratch.py`.
- **Formatter and linter**: `uv run ruff format .` and `uv run ruff check --fix .` passed cleanly with 0 errors.
- **Rejected findings**: None.
- **Changelog**: Does not merit a separate changelog entry (internal ergonomics/safety refinement within unreleased cycle).

## Independent verification (Worker 2)

- **Trace Analysis**:
  - Re-traced the generation pipeline across `editable_input_fields`, `input_field_required`, `relation_id_scalar`, `relation_id_annotation`, `model_column_write_kind`, `mutation_input_field_specs`, and `build_mutation_input`.
  - Verified that `materialize_mutation_input_class` audits GraphQL field collisions across merged input definitions and delegates to `make_input_namespace`.
  - Verified that `clear_mutation_input_namespace` cleanly resets the ledger and is registered with `register_subsystem_clear(owner="mutations.input_namespace", before_bind=True)`.
  - Verified `build_payload_type` default slot behavior: when `object_slot` is omitted, it correctly routes through `payload_object_slot(object_type)`, returning `"node"` for Relay Node types and `"result"` for plain types, while preserving `{ ok: bool, errors: list[FieldError] }` for `object_type=None`.
- **Findings Evaluation**:
  - Low 1 & Low 2 are verified: the implementation in `django_strawberry_framework/mutations/inputs.py` and the corresponding unit tests in `tests/mutations/test_inputs.py` are concise, robust, and correctly placed.
- **Test Execution**:
  - Ran `tests/mutations/test_inputs.py` (66 passed).
  - Ran cross-subsystem test suite `tests/mutations/`, `tests/forms/`, `tests/auth/`, `tests/rest_framework/` (1,153 passed).
  - Authored and ran independent scratch test in `docs/review/temp-tests/mutations_inputs/test_independent_scratch.py` (7 tests passed) testing field filtering edge cases, requiredness logic, Relay/plain relation annotations, column kind classification, specs extraction with `EXCLUDED`, and payload shapes.
- **Conclusion**:
  - `django_strawberry_framework/mutations/inputs.py` satisfies all design and specification constraints with high quality. No outstanding defects or gaps found.
