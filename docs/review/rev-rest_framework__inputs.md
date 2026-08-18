# Review: `django_strawberry_framework/rest_framework/inputs.py`

Status: verified

## Understanding

This module discovers stable DRF schema-time fields, applies writable-field narrowing, builds create/partial Strawberry inputs, recursively handles explicitly opted-in nested serializers, records reverse-map specs, and materializes generated classes in the lazy namespace. `sets.py` invokes this machinery during mutation binding; `resolvers.py` consumes the stashed specs at runtime.

## Verification

Reviewed namespace clearing, shape-cache identity, required/default/nullability handling, source and GraphQL-name collision checks, relation target resolution, nested cycle/depth guards, and all input-generation tests. A focused probe showed that the runtime agreement layer had no generated scalar annotation to compare against.

## Improvements

### High

None.

### Medium

**Observation:** Generated reverse-map specs did not retain the emitted annotation or effective requiredness, and injected-field specs retained neither.  
**Evidence:** The resolver agreement guard could inspect only `kind`, source, and relation target. A probe passed a schema scalar spec alongside a runtime `IntegerField` without raising.  
**Impact:** A schema could advertise one scalar/nullability shape while the runtime DRF serializer validated another, producing a misleading public contract and late validation failures.  
**Recommendation:** Record the post-nullability annotation representation and effective requiredness on `InputFieldSpec` during input generation; record the base annotation for injected fields. Let the runtime agreement owner compare those immutable descriptors before validation.  
**Proof:** `tests/rest_framework/test_resolvers.py::test_agreement_guard_rejects_scalar_annotation_drift` and `::test_agreement_guard_rejects_injected_scalar_annotation_drift`, plus the 405-test focused suite.

### Low

None.

## Summary

The input generator now carries enough immutable shape metadata for the runtime agreement guard to enforce the schema contract without rediscovering GraphQL annotations.

## Implementation (Worker 1)

Changed `utils/inputs.py::InputFieldSpec` to carry optional `annotation_repr` and `required` metadata. Changed `rest_framework/inputs.py::_walk_serializer_fields` to record emitted annotations/effective requiredness and `resolve_injected_field_specs` to record injected base annotations. Added permanent resolver regressions for generated and injected scalar drift. Validation: `uv run ruff format .`; `uv run ruff check --fix .`; `uv run pytest tests/rest_framework --no-cov` (405 passed); live serializer tests (19 passed). No changelog entry is warranted.

## Independent verification (Worker 2)

Status: verified. Re-traced input discovery, field narrowing, source and GraphQL-name collision checks, required/default/nullability emission, descriptor/cache identity, injected-field specs, nested opt-in recursion, cycle/depth guards, and namespace clearing. Direct adversarial probes showed scalar choice-member and registered-custom converter annotation drift is rejected; `registry.clear()` empties the serializer ledger while intentionally preserving parked module globals for lazy references.

Evidence:
- `uv run pytest tests/rest_framework/test_converter.py tests/rest_framework/test_inputs.py -k 'choice or custom or required or nullable or null or source or injected or nested or cycle or depth or namespace or materializ or cache' --no-cov` — 62 passed.
- Full package run `uv run pytest tests/rest_framework/test_soft_dependency.py tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py tests/rest_framework/test_converter.py tests/rest_framework/test_resolvers.py --no-cov` — 405 passed.
- Scratch probes under `docs/review/temp-tests/rest_framework/` — 4 passed.

No revision is needed.
