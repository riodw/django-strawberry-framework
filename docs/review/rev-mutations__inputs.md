# Review: `django_strawberry_framework/mutations/inputs.py`

Status: verified

## Understanding

This module owns model mutation input generation and the shared public
`FieldError` / payload types. `editable_input_fields` selects writable model
columns and forward M2M fields; relation and scalar converters preserve the
read-side GraphQL contract; `mutation_input_shape` owns shape identity, naming,
and cache keys; and the namespace materializer parks generated classes for lazy
resolution. The payload builder intentionally has model-backed (`node` / `result`)
and model-less (`ok`) shapes for the different write flavors.

## Verification

Read all generation, collision, lifecycle, relation, Upload, and payload paths,
then traced bind consumers in `mutations/sets.py`, form/serializer input builders,
`utils/inputs.py`, and resolver decoders in `utils/write_values.py`. The mutation
input tests cover defaults, narrowing, one-shot iterables, relation id strategy,
M2M semantics, file inputs, consumer overrides, collisions, empty shapes, name
injectivity, materialization, and payload slots. Focused validation:
`uv run pytest --no-cov tests/mutations` — 290 passed; live HTTP mutation
validation and Upload paths are included in the 57 passing fakeshop mutation
tests.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Input selection, naming, materialization, collision auditing, and payload
construction are separated at the correct lifecycle boundaries. No confirmed
inputs-owned defect or worthwhile improvement remains in this pass.

## Implementation (Worker 1)

Zero-edit proof. No production or test source changed. Existing package and live
fakeshop tests provide permanent coverage; status is `fix-implemented` for the
verified zero-edit cycle. No changelog entry is warranted.

## Independent verification (Worker 2)

Status: verified

Re-read generated model input selection, requiredness, relation-id typing,
narrowing/name collision checks, materialization, payload slots, and the form /
serializer reverse-map consumers. Evidence:

- `uv run pytest --no-cov tests/mutations/test_inputs.py tests/mutations/test_sets.py` —
  134 passed.
- `uv run pytest --no-cov tests/mutations` — 290 passed.
- `uv run pytest --no-cov tests/forms tests/rest_framework` — 595 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py` — 118 passed.

Malformed, wrong-model, hidden, M2M omitted/empty/null, requiredness, narrowed
shape, collision, registry-clear, and lazy-reference paths remained green. The
NodeID issue found in `resolvers.py` is an alias-routing defect after input
generation, not an inputs-owned defect.
