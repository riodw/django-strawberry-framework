# Review: `django_strawberry_framework/mutations/fields.py`

Status: verified

## Understanding

`DjangoMutationField` is the write-side root-field factory. It validates a concrete,
currently registered mutation declaration, synthesizes the operation-specific `id` /
`data` signature through `input_type_name` and `input_module_path`, dispatches sync or
async resolution at call time, and stamps `MUTATION_CLASS_MARKER` for
`schema.py::DjangoMutationExecutionContext`. `_lazy_ref` and
`build_lazy_field_signature` are shared by the auth fixed-field factories. The
construction-time guard intentionally accepts model, ModelForm, plain Form, and
serializer flavors through their protocol and lifecycle ledgers.

## Verification

Read the complete factory and traced its callers through `mutations/sets.py`,
`mutations/inputs.py`, `forms/sets.py`, `rest_framework/sets.py`,
`auth/mutations.py`, and `schema.py`. `tests/mutations/test_fields.py` covers
signatures, lazy payload resolution, sync/async dispatch, abstract and stale
declarations, form/serializer targets, and marker-compatible schema construction.
Focused validation: `uv run pytest --no-cov tests/mutations` — 290 passed;
live fakeshop mutation coverage: 57 passed in
`examples/fakeshop/test_query/test_products_api.py` with the requested mutation
keywords.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The factory has one clear owner for field construction, lazy signature injection,
runtime dispatch, and transaction marking. Its name and payload dependencies remain
behind the mutation flavor seams; no fields-owned edit is justified.

## Implementation (Worker 1)

Zero-edit proof. No production or test source changed. Existing focused and live
tests demonstrate the accepted contract; status is `fix-implemented` for a
verified zero-edit cycle. No changelog entry is warranted.

## Independent verification (Worker 2)

Status: verified

Re-read `fields.py` with the mutation/form/serializer/auth field factories and
confirmed that construction-time protocol validation, lazy input/payload
signatures, marker stamping, and sync/async dispatch remain sound. Evidence:

- `uv run pytest --no-cov tests/mutations` — 290 passed.
- `uv run pytest --no-cov tests/forms tests/rest_framework` — 595 passed.
- `uv run pytest --no-cov tests/auth/test_mutations.py` — 93 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py` — 118 passed.

The shard-specific NodeID lookup defect recorded in the resolver artifact occurs
after this factory's marker/signature work and does not implicate field
construction. No fields-owned revision is requested.
