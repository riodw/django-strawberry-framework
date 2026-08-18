# Review: `django_strawberry_framework/rest_framework/resolvers.py`

Status: verified

## Understanding

The resolver delegates orchestration to `mutations/resolvers.py::run_write_pipeline_sync`, preserving authorize-before-decode, managed transaction/alias pinning, sync/async parity, and optimizer re-fetch. Its own responsibilities are serializer-field-keyed decode, recursive DRF error flattening, frozen hook boundaries, runtime serializer construction, relation queryset scoping, validator pinning, save-result/relationship attestation, and schema/runtime agreement.

## Verification

Read every resolver phase and the shared write transaction/queryset helpers. Existing tests cover relation visibility, authorization ordering, aliases, uploads, nested errors, save rollback, hook freezing, async execution, and live GraphQL mutation behavior. A direct probe demonstrated that `_assert_schema_runtime_agreement` accepted a scalar-to-scalar type drift because it checked only broad kind.

## Improvements

### High

None.

### Medium

**Observation:** `_assert_schema_runtime_agreement` rejected scalar→relation/file/nested changes but accepted scalar→scalar annotation and requiredness changes.  
**Evidence:** A runtime `serializers.IntegerField` passed for a schema `InputFieldSpec(kind="scalar")` representing `str`; before the fix there was no annotation/requiredness comparison.  
**Impact:** The GraphQL input schema and DRF validation engine could disagree while the request still reached `is_valid()`, causing a late, opaque field error or accepting a different scalar contract than clients introspected.  
**Recommendation:** Before `is_valid()`, resolve the runtime field through the same serializer converter, apply operation-aware nullability/requiredness, and compare against the bind-time descriptor. Apply the annotation check to injected fields as well, while retaining compatibility for metadata-free internal test doubles.  
**Proof:** `tests/rest_framework/test_resolvers.py::test_agreement_guard_rejects_scalar_annotation_drift`, `::test_agreement_guard_rejects_injected_scalar_annotation_drift`, existing agreement tests, and 19 live serializer tests.

### Low

None.

## Summary

The resolver now fails closed at the schema/runtime boundary instead of allowing scalar or requiredness drift to reach DRF validation.

## Implementation (Worker 1)

Changed `rest_framework/resolvers.py::_assert_field_agreement` to compare runtime effective requiredness and converter-derived emitted annotation against the bind-stashed spec, including injected fields and operation-aware partial semantics. Added two permanent regressions while preserving metadata-free helper tests. Validation: `uv run ruff format .`; `uv run ruff check --fix .`; `uv run pytest tests/rest_framework --no-cov` (405 passed); `uv run pytest examples/fakeshop/test_query/test_products_api.py -k 'serializer' --no-cov` (19 passed). No changelog entry is warranted.

## Independent verification (Worker 2)

Status: verified. Re-traced the full serializer resolver from serializer-field-keyed decode through runtime agreement, relation visibility/queryset scoping, validation/error flattening, hook boundaries, savepoint/write witness, relation attestation, optimized refetch, and sync/async dispatch. The shared pipeline confirms locate → authorize → decode ordering and one pinned transaction/alias; no authorization, rollback, custom/choice annotation, injected-field, or nested agreement bypass was reproduced.

Evidence:
- `uv run pytest tests/rest_framework/test_resolvers.py -k 'async or alias or transaction or authorization or authorize or decode or upload or hook or frozen or source or relation_queryset or save_result or attestation or validator' --no-cov` — 78 passed.
- Full package run `uv run pytest tests/rest_framework/test_soft_dependency.py tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py tests/rest_framework/test_converter.py tests/rest_framework/test_resolvers.py --no-cov` — 405 passed.
- `uv run pytest examples/fakeshop/test_query/test_products_api.py -k 'serializer' --no-cov` — 19 passed.
- Scratch custom/choice agreement and namespace probes — 4 passed.

No revision is needed; the resolver checklist can be checked.
