# Review: `django_strawberry_framework/rest_framework/sets.py`

Status: verified

## Understanding

`SerializerMutation` validates the DRF `ModelSerializer` contract, normalizes operation/field/injection/nested metadata, captures schema fingerprints, binds generated inputs and reverse maps, and delegates sync/async execution to the resolver module. It rides the shared mutation registry, permission defaults, payload binding, and write pipeline.

## Verification

Traced class creation through `DjangoMutation` metaclass registration, finalization, input materialization, `DjangoMutationField`, and the fakeshop products schema. Reviewed runtime hook contracts, injected/nested ownership, selector normalization, shape-cache lifecycle, and the complete sets test module. No sets-local defect was confirmed; the fix belongs in the generated descriptor and runtime agreement owner.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The mutation declaration and bind lifecycle correctly establish the schema-time contract consumed by the resolver. No source change was needed in this file.

## Implementation (Worker 1)

No change to `sets.py`; its existing bind path now benefits from the metadata emitted by `inputs.py` and the agreement enforcement in `resolvers.py`. Validation: `uv run pytest tests/rest_framework --no-cov` (405 passed); live serializer tests (19 passed); formatter/linter passed. No changelog entry is warranted.

## Independent verification (Worker 2)

Status: verified. Re-traced declaration validation and registry binding through `DjangoMutation` metaclass registration, schema-hook fingerprinting, input materialization, injected/nested metadata, permission defaults, selector normalization, shape-cache lifecycle, and fakeshop schema integration. The bind path preserves soft dependency behavior and invokes the agreement guard before DRF validation; no sets-local defect was found.

Evidence:
- Full package run `uv run pytest tests/rest_framework/test_soft_dependency.py tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py tests/rest_framework/test_converter.py tests/rest_framework/test_resolvers.py --no-cov` — 405 passed.
- `uv run pytest examples/fakeshop/test_query/test_products_api.py -k 'serializer' --no-cov` — 19 passed.
- `uv run pytest tests/rest_framework/test_converter.py tests/rest_framework/test_inputs.py -k 'choice or custom or required or nullable or null or source or injected or nested or cycle or depth or namespace or materializ or cache' --no-cov` — 62 passed.

No revision is needed.
