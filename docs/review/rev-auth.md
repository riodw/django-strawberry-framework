# Review: `django_strawberry_framework/auth/`

Status: verified

## Understanding

The auth package is an explicit opt-in surface. `auth/__init__.py` re-exports only the
four consumer factories (`current_user`, `login_mutation`, `logout_mutation`, and
`register_mutation`); transport internals remain private and the package root does not
import auth. Importing auth stays Channels-free until a real Channels request reaches
`auth/sessions.py`.

The package's lifecycle has two coordinated ledgers. Auth declarations survive the
finalizer's pre-bind generated-state reset and are cleared with `registry.clear()`;
generated payload/input/alias namespaces are reset before each bind. Finalization invokes
`bind_auth_mutations()` before `bind_mutations()`, allowing surface-keyed auth validation
and materialization without orphan payloads or a register-rider generic error pre-empting
the auth-specific message.

The runtime boundaries compose across modules: `utils.permissions` resolves Django and
Channels contexts; `auth.sessions` classifies and serializes transport session work;
`auth.mutations` performs login/logout/register transitions; `auth.queries` returns the
session actor; `utils.sessions` coordinates the Channels actor lease; and `consumers.py`
revalidates the same connection. The fakeshop accounts schema provides the reachable live
GraphQL surface.

## Verification

- Re-read all three auth modules plus `auth/__init__.py` as an integrated component.
- Traced finalizer ordering, registry clear ownership, lazy namespace materialization,
  request context decoding, optional Channels import boundaries, session-engine capability,
  actor-lease ordering, and live schema wiring.
- `uv run pytest tests/auth --no-cov` — 132 passed.
- `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov` — 20 passed.
- `python -m py_compile` passed for all auth modules.
- `uv run ruff check django_strawberry_framework/auth tests/auth --output-format concise`
  passed.
- No full repository test gate was run; it remains owned by the final review-plan item.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The auth package's public exports, declaration/emit lifecycle, sync/async dispatch,
request transport boundary, session durability, actor serialization, nullable current-user
contract, and live fakeshop integration agree across module boundaries. No new integrated
finding remains.

## Implementation (Worker 1)

- No new package or test edit was required during the folder pass.
- Existing concurrent auth source/test changes were preserved and are covered by the
  focused and live validation above.
- No changelog entry was requested.

## Independent verification (Worker 2)

- Re-ran the complete auth and live auth suites and checked the package import/export
  surface against the finalizer and registry lifecycle.
- Confirmed logout-only schemas do not require a user type, user-typed surfaces do require
  a primary user type, and reload clears generated artifacts without erasing declarations
  before binding.
- No additional cross-file finding remains.
