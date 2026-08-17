# Review: `django_strawberry_framework/auth/sessions.py`

Status: verified

## Understanding

`auth/sessions.py` is the transport-owned session boundary. It classifies a resolved
request by explicit type (`HttpRequest` versus `ChannelsRequestAdapter`) and Channels
scope type, lazily imports the optional Channels dependency only after an adapter is
recognized, and raises actionable configuration errors for unknown transports or missing
session middleware.

It owns the per-scope `asyncio.Lock` used to serialize Channels session mutation. The
lock is stored in the mutable ASGI scope, created without an intervening await, and
released by the async context manager on success or cancellation. It also resolves the
configured session-store class through `utils/sessions.py` so signed-cookie WebSocket
logout can be rejected where no server-side record exists. Login is rejected for every
WebSocket because key rotation cannot return a replacement cookie.

## Verification

- Traced classification and session access through `utils/permissions.py`,
  `auth/mutations.py`, `routers.py`, `consumers.py`, `utils/sessions.py`, and the
  Channels HTTP/WebSocket harness.
- Reviewed the soft-dependency absence path, unknown scope types, missing/present sessions,
  mutable-scope guard, same-scope lock contention, cancellation release, cross-scope
  independence, no-process-global-storage assertion, session-engine subclass detection,
  and transport capability matrix.
- `uv run pytest tests/auth/test_sessions.py --no-cov` passed as part of the complete
  auth run; the explicit per-module command passed all 132 auth tests.
- `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov` passed 20 live
  tests. `python -m py_compile` and targeted Ruff checks passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

Transport classification, optional dependency behavior, session-middleware diagnostics,
scope-owned lock lifecycle, signed-cookie capability detection, and login/logout capability
answers are coherent. No new production or test edit was justified in this cycle.

## Implementation (Worker 1)

- No new code change was required. The existing scope-owned lock and explicit capability
  boundary are already the correct owners for the reviewed invariants.
- No changelog entry was requested.

## Independent verification (Worker 2)

- Replayed the transport matrix and lock lifecycle from the current implementation,
  including cancellation and immutable-scope failure behavior.
- Confirmed Channels remains absent from ordinary auth import paths and is required only
  after a Channels adapter is classified.
- Re-ran focused and live auth validation; no additional finding remains.
