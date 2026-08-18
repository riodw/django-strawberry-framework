# Review: `django_strawberry_framework/mutations/permissions.py`

Status: verified

## Understanding

The write authorization contract is separate from row visibility. `run_permission_classes`
is the shared class-based gate for model and plain-form mutations;
`DjangoModelPermission` maps create/update/delete to Django add/change/delete
permissions; and `DenyAll` is the safe default for model-less forms. The strict
sync-bool result guard rejects awaitables and non-bools across permission classes,
mutation overrides, and `user.has_perm`, preventing truthiness-based authorization
bypasses.

## Verification

Traced defaults from `mutations/sets.py` and `forms/sets.py` through
`mutations/resolvers.py::authorize_or_raise`, request extraction in
`utils/permissions.py`, and the auth-alias phase in
`utils/write_transaction.py`. `tests/mutations/test_permissions.py` and
`tests/mutations/test_write_transaction.py` cover anonymous, model-permission,
override, hidden-row ordering, async, awaitable, non-bool, and hostile-result
cases. Focused validation: `uv run pytest --no-cov tests/mutations` — 290
passed; live fakeshop authorization paths are included in the 57 passing
mutation tests.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Authorization owns only write permission policy, with one shared result contract
and no accidental coupling to read visibility or session actor classification.
No permissions-owned edit is justified.

## Implementation (Worker 1)

Zero-edit proof. No production or test source changed. Existing strict-bool and
live authorization coverage demonstrates the contract; status is
`fix-implemented` for a verified zero-edit cycle. No changelog entry is
warranted.

## Independent verification (Worker 2)

Status: verified

Re-read permission extraction, model-permission mapping, deny-by-default plain
forms, authorization ordering, and strict bool/awaitable guards. Evidence:

- `uv run pytest --no-cov tests/mutations/test_permissions.py` (included in
  `uv run pytest --no-cov tests/mutations`) — 290 mutation tests passed.
- `uv run pytest --no-cov tests/auth/test_mutations.py` — 93 passed.
- `uv run pytest --no-cov tests/forms tests/rest_framework` — 595 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py` —
  118 passed.

Anonymous/under-privileged denial, hidden-row no-existence behavior,
authorization-before-decode, non-bool results, awaitables, sync/async form and
serializer authorization, and auth payload integration remained green. No
permissions-owned revision is requested.
