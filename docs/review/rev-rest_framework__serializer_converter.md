# Review: `django_strawberry_framework/rest_framework/serializer_converter.py`

Status: verified

## Understanding

The converter owns DRF-field dispatch, strict relation/file/nested handling, scalar extension registration, source-to-model-column resolution, relation cardinality checks, serializer-only relation targets, choice-enum generation, and reverse-map `InputFieldSpec` construction. `inputs.py` supplies operation/nullability context; `resolvers.py` uses the resulting kind/source/target metadata.

## Verification

Reviewed the full dispatch order and MRO registry, model-backed versus serializer-only paths, id-like naming, dotted/star source rejection, choice/file/list handling, relation-primary enforcement, and converter tests. No converter-local defect was confirmed; the scalar-shape issue was owned by descriptor generation plus runtime agreement.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Strict conversion and source/cardinality policy are coherent with the runtime decoder; no source change was needed in this file.

## Implementation (Worker 1)

No change to `serializer_converter.py`. Existing converter behavior and tests provide the base annotation/kind contract consumed by the new resolver agreement check. Validation: `uv run pytest tests/rest_framework --no-cov` (405 passed), including converter coverage; formatter/linter passed. No changelog entry is warranted.

## Independent verification (Worker 2)

Status: verified. Re-traced precheck/MRO dispatch, custom registration, model-backed source resolution, scalar override agreement, relation cardinality/primary enforcement, file/list handling, serializer-only choices, and nested rejection. Choice-member drift and a custom registered converter changing `str` to `int` were independently exercised through the runtime agreement guard and both failed closed as required.

Evidence:
- `uv run pytest tests/rest_framework/test_converter.py tests/rest_framework/test_inputs.py -k 'choice or custom or required or nullable or null or source or injected or nested or cycle or depth or namespace or materializ or cache' --no-cov` — 62 passed.
- Full package run `uv run pytest tests/rest_framework/test_soft_dependency.py tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py tests/rest_framework/test_converter.py tests/rest_framework/test_resolvers.py --no-cov` — 405 passed.
- Scratch custom/choice drift probes — 4 passed.

No revision is needed.
