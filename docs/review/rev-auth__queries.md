# Review: `django_strawberry_framework/auth/queries.py`

Status: verified

## Understanding

`auth/queries.py` owns the `current_user()` field factory and the bind-materialized
`CurrentUserAlias` namespace. The factory shares the auth declaration ledger, permission
holder, request resolver, and sync/async dispatch machinery with the mutation fields. Its
return annotation is a nullable lazy reference, materialized to the consumer's primary
user `DjangoType` during `bind_auth_mutations()`.

The resolver resolves the request, computes the authenticated actor once, runs the
permission gate with that actor as its instance, and returns the actor directly. It does
not re-run `get_queryset()` or refetch the user, preserving the actor-not-lookup
contract. Anonymous-but-authorized requests return `null`; a permission gate can instead
reject the anonymous actor. Async execution forces lazy user loading inside the one
thread-sensitive sync boundary.

The alias namespace uses `make_input_namespace()` and registers only its generated-state
clear callback as a pre-bind row. `registry.clear()` and the finalizer reset it before
each bind, while the auth declaration ledger remains available for the bind itself.

## Verification

- Traced `current_user()` through `auth/__init__.py`, `auth/mutations.py`,
  `types/finalizer.py`, `utils/inputs.py`, `utils/permissions.py`, and Strawberry's
  lazy return-type resolution.
- Reviewed alias materialization/reload tests, current-user-only bind tests,
  missing/ambiguous primary errors, anonymous and authenticated actor behavior, mapping
  and bare-request contexts, permission denial, async lazy-user forcing, and visibility
  bypass tests.
- `uv run pytest tests/auth/test_queries.py --no-cov` passed as part of the complete
  auth run; the explicit per-module command passed all 132 auth tests.
- `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov` passed 20 live
  tests, including authenticated/anonymous `me` behavior.
- `python -m py_compile` passed for all auth modules; targeted Ruff checks passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The nullable actor contract, permission ordering, async lazy-user boundary, lazy alias
typing, partial-schema behavior, and reload lifecycle are coherent. No new production or
test edit was justified in this cycle.

## Implementation (Worker 1)

- No new code change was required. The shared request resolver's normal mapping-context
  support and the existing alias lifecycle tests cover the reachable edge cases.
- Preserved the pre-existing concurrent additions in `tests/auth/test_queries.py`.
- No changelog entry was requested.

## Independent verification (Worker 2)

- Re-traced the resolver's context precedence: direct Django request, mapping-held Django
  request, and Channels adapter remain distinct and do not allow a missing actor to become
  an exception.
- Re-ran the complete focused auth suite and live auth suite, plus compile and Ruff checks.
- No additional finding remains.
