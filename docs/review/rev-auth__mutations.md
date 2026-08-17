# Review: `django_strawberry_framework/auth/mutations.py`

Status: verified

## Understanding

`auth/mutations.py` owns the opt-in session-auth mutation factories and their phase-2.5
binding. `login_mutation()` and `logout_mutation()` use the shared auth declaration ledger,
fixed permission-holder shape, lazy payload references, and the common sync/async field
dispatcher. `register_mutation()` synthesizes a cached `Register` `DjangoMutation` rider
whose password-aware decode/write pair rides `mutations/resolvers.py::run_write_pipeline_sync`.

The login state machine resolves and classifies the request before authorization or
credential work, rejects unsupported WebSocket login, preflights unencodable credentials,
calls Django's backend chain once, builds the payload before session mutation, and then
persists through either Django HTTP or Channels HTTP. Establishment compensates after any
partial failure, preserving the primary exception when cleanup also fails. Logout captures
the pre-teardown actor observation, builds its payload before native teardown, and uses the
scope session lock plus the shared connection actor lease for Channels logout. Registration
delegates authorization, transaction, visibility, validation, rollback, and optimized
refetch to the shared mutation pipeline while keeping the raw password outside model
construction and hashing it before `full_clean()`.

`bind_auth_mutations()` runs after pre-bind emit resets and before `bind_mutations()`. It
resolves a primary user type only for user-typed surfaces, materializes only declared fixed
payloads/aliases, and leaves the register rider to the ordinary mutation binder.

## Verification

- Traced callers and lifecycle through `types/finalizer.py`, `registry.py`,
  `mutations/fields.py`, `mutations/inputs.py`, `mutations/permissions.py`,
  `mutations/resolvers.py`, `utils/permissions.py`, `utils/sessions.py`, and
  `consumers.py`.
- Reviewed the existing declaration conflict, reload, partial-surface, permission,
  malformed-credential, session-failure, cancellation, compensation, password-hashing,
  sync/async, Channels HTTP, WebSocket logout, and actor-lease tests.
- `uv run pytest tests/auth/test_mutations.py --no-cov` passed as part of the complete
  auth run; the explicit per-module command passed all 132 auth tests.
- `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov` passed 20 live
  tests, covering the reachable HTTP auth surface and its real session lifecycle.
- `python -m py_compile` passed for all auth modules; `uv run ruff check
  django_strawberry_framework/auth tests/auth --output-format concise` passed.
- The working tree already contained a concurrent `BaseException` cleanup change and
  its cancellation regressions in this target/test family. They were inspected and
  preserved, not re-attributed or reverted by this review.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The mutation declaration/bind lifecycle, permission-holder reuse, transport capability
checks, credential enumeration posture, session persistence/compensation, Channels actor
serialization, and password-safe registration are coherent and covered at the strongest
available package/live tiers. No new production or test edit was justified in this cycle.

## Implementation (Worker 1)

- No new code change was required. The current implementation already places each rule at
  its owning boundary and the permanent auth tests exercise the important failure and
  reload paths.
- Preserved unrelated concurrent changes in `auth/mutations.py` and
  `tests/auth/test_mutations.py`; no formatter/linter mutation was run because this cycle
  made no edits.
- No changelog entry was requested.

## Independent verification (Worker 2)

- Re-read the current source and independently checked the fixed-field declaration ledger,
  register rider cache/re-registration, phase-2.5 ordering, payload-before-mutation
  ordering, fail-closed compensation, cancellation chaining, and Channels lock order.
- Re-ran `uv run pytest tests/auth/test_sessions.py tests/auth/test_queries.py
  tests/auth/test_mutations.py --no-cov -q` — 132 passed — and the 20-test live auth
  suite.
- Confirmed the target and tests compile and pass Ruff; no additional finding remains.
