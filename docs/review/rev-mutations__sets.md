# Review: `django_strawberry_framework/mutations/sets.py`

Status: verified

## Understanding

`sets.py` owns mutation declaration validation, the model declaration ledger,
metaclass lifecycle, Meta snapshots, operation/input-shape validation, consumer
input merging and relation-shape checks, and phase-2.5 binding. Its shared
helpers are consumed by form and serializer flavors, while plain forms retain a
disjoint declaration ledger and bind because they have no model/object payload.
The model shape cache and generated namespace clear are lifecycle-owned and
coordinated by registry/finalizer callbacks.

## Verification

Read the complete metaclass, Meta matrix, shape/cache, merge, relation override,
payload binding, and finalizer entry paths. Traced `forms/sets.py`,
`rest_framework/sets.py`, auth register's rider, `types/finalizer.py`, and
`registry.py`. `tests/mutations/test_sets.py` covers declaration lifecycle,
operation/field validation, cache clearing, merge collisions, relation shape
locks, binding, and metaclass identity. Focused validation:
`uv run pytest --no-cov tests/mutations` — 290 passed; live fakeshop mutation
schemas finalized and executed in the 57 passing HTTP tests.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Declaration, validation, caching, and binding have clear ownership and the
model/form distinction is intentional. No sets-owned edit is justified.

## Implementation (Worker 1)

Zero-edit proof. No production or test source changed. Existing package and live
schema tests prove the bind lifecycle; status is `fix-implemented` for a
verified zero-edit cycle. No changelog entry is warranted.

## Independent verification (Worker 2)

Status: verified

Re-read declaration validation, metaclass/ledger ownership, phase-2.5 binding,
consumer-input merge/type locks, registry clear/reload, and lazy namespace
materialization. Evidence:

- `uv run pytest --no-cov tests/mutations/test_sets.py tests/mutations/test_inputs.py`
  — 134 passed.
- `uv run pytest --no-cov tests/mutations` — 290 passed.
- `uv run pytest --no-cov tests/forms tests/rest_framework` — 595 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py` —
  118 passed.

No sets-owned lifecycle or generated-input binding defect was found. The
revision in `rev-mutations__resolvers.md` is a runtime alias-resolution defect,
not a declaration/bind defect.
