# Review: `django_strawberry_framework/rest_framework/hook_context.py`

Status: verified

## Understanding

`SerializerHookContext` is the immutable operation/alias/authorized-pk snapshot passed to serializer hooks. `UploadMetadata` is the immutable descriptor exposed for uploads so hooks cannot consume or mutate the authoritative file stream. `resolvers.py` constructs these values inside the shared write pipeline after authorization and before consumer hooks.

## Verification

Read the hook construction and all three hook call sites in `rest_framework/resolvers.py`, plus the frozen-view tests covering nested mappings, cycles, sharing, opaque leaves, bytearrays, sets, datetimes, and `SimpleUploadedFile`. The focused rest_framework suite and live fakeshop serializer suite passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The context and upload descriptor have clear ownership and are frozen at the consumer boundary. No source change was needed in this file.

## Implementation (Worker 1)

No change to `hook_context.py`; the accepted schema/runtime-shape fix is owned by input-shape generation and resolver agreement validation instead. Permanent coverage already exercises the frozen hook-data contract. Validation: `uv run pytest tests/rest_framework --no-cov` (405 passed); `uv run pytest examples/fakeshop/test_query/test_products_api.py -k 'serializer' --no-cov` (19 passed). Formatter/linter passed. No changelog entry is warranted.

## Independent verification (Worker 2)

Status: verified. Re-traced `SerializerHookContext` and `UploadMetadata` construction through all injected-data, constructor-kwargs, and save-kwargs hooks. The frozen context carries only operation/alias/pk snapshots; uploaded streams are replaced by immutable metadata, while authoritative files remain on serializer data. Existing nested/cyclic/deep freeze and upload tests plus live serializer requests passed without finding a bypass.

Evidence:
- `uv run pytest tests/rest_framework/test_resolvers.py -k 'hook or frozen or upload or async or alias or transaction' --no-cov` — included in the focused resolver run; 78 selected tests passed.
- `uv run pytest examples/fakeshop/test_query/test_products_api.py -k 'serializer' --no-cov` — 19 passed.
- Full package run `uv run pytest tests/rest_framework/test_soft_dependency.py tests/rest_framework/test_inputs.py tests/rest_framework/test_sets.py tests/rest_framework/test_converter.py tests/rest_framework/test_resolvers.py --no-cov` — 405 passed.

No revision is needed.
