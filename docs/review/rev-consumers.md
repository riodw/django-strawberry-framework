# Review: `django_strawberry_framework/consumers.py`

Status: verified

## Understanding

`django_strawberry_framework/consumers.py` implements the WebSocket transport security subsystem for `django-strawberry-framework`. It owns the handshake-time Host boundary (`DjangoWebSocketHostValidator`) and the dynamic revalidating WebSocket consumer factory (`build_revalidating_consumer_class`) with dual security revalidation checkpoints.

It owns:
1. **WebSocket Host boundary (`DjangoWebSocketHostValidator`, `_host_validation_request`)**:
   - Serves as the outermost WebSocket ASGI middleware composed by `routers.py`.
   - Projects handshake metadata (`headers`, `server`) into a minimal `HttpRequest` via `_host_validation_request`, replicating Django's ASGI adapter treatment (Latin-1 decoding, lower-cased header normalization, comma-joined duplicate headers, `SERVER_NAME`/`SERVER_PORT` fallback).
   - Invokes Django's standard `HttpRequest.get_host()` without re-implementing hostname matching or `ALLOWED_HOSTS` parsing.
   - Normalizes `DisallowedHost` into Channels' `WebsocketDenier` for byte-identical rejection to origin denial; allows unexpected projection exceptions to propagate fail-closed.
2. **Revalidating consumer factory (`build_revalidating_consumer_class`)**:
   - Returns `GraphQLWebSocketConsumer` deriving from `base_consumer_cls` (`strawberry.channels.GraphQLWSConsumer`).
   - Dynamically derives and installs revalidating handler subclasses (`_RevalidatingTransportWSHandler`, `_RevalidatingGraphQLWSHandler`) and a revocation-gated WebSocket adapter (`_RevocationGatedWebSocketAdapter`).
   - Keeps class construction function-local and unexported to prevent stale class caching or direct consumer import.
3. **Dual security checkpoints & actor revalidation (`revalidate_operation_actor`, `send_revalidated_operation_frame`, `_actor_is_current`)**:
   - **Checkpoint 1 (Operation admission):** `revalidate_operation_actor` hooks `handle_subscribe` (`graphql-transport-ws`) and `handle_start` (legacy `graphql-ws`), checking if a new operation may begin.
   - **Checkpoint 2 (Outbound information-bearing frames):** `send_revalidated_operation_frame` hooks `_RevocationGatedWebSocketAdapter.send_json` for `next`, `data`, and operation-scoped `error` frames, ensuring already-admitted long-running subscriptions do not emit payloads after actor invalidation.
   - Evaluates actor freshness under the connection's `actor_lease` using `_refreshed_actor` (delegating to `channels.auth.get_user`), updating `scope["user"]`.
   - Revalidates against monotonic cache timestamps when `websocket_revalidation_window > 0.0`.
   - Enforces fail-closed semantics: exceptions during revalidation revoke the connection immediately.
4. **Revocation state machine & teardown lifecycle (`_ConnectionRevocation`, `_revoke_connection`)**:
   - Manages connection lifecycle across 5 states: `PERMITTED`, `DECIDED`, `CLOSING`, `CLOSED`, and `ABANDONED`.
   - Exposes a read-free `revoked` latch to reject pipelined frames without further database reads.
   - Spawns a connection-owned, shielded close task sending `4403` / `"Forbidden"`.
   - Caps close attempts to `_MAX_REVOCATION_CLOSE_ATTEMPTS = 2` to prevent amplification attacks.
   - Settles active close tasks during `consumer.disconnect()` within a `finally` block to prevent orphan background tasks.
5. **Stop-aware result source & per-event error masking (`_StopAwareSchema`, `_stop_aware_results`)**:
   - Wraps handler `schema.subscribe` and `schema.stream` calls.
   - Terminates the async generator cleanly upon revocation so upstream loops exit naturally without task cancellation deadlocks.
   - Invokes `aclose()` deterministically on the inner generator when supported.
   - Applies per-event GraphQL error masking via `extensions/error_policy.py` (`mask_execution_result`) before frames reach the wire.
6. **Window configuration & dependency hygiene (`resolved_revalidation_window`)**:
   - Validates and coerces `websocket_revalidation_window` ensuring strictly non-negative finite floats/ints and rejecting booleans, subclasses, and non-finite values.
   - Zero module-level imports of `channels`, `daphne`, or `strawberry`, keeping `routers.py` importable without soft dependencies.

## Verification

1. Traced connections across the codebase:
   - `routers.py`: middleware wrapping order (`DjangoWebSocketHostValidator` -> `AllowedHostsOriginValidator` -> `AuthMiddlewareStack` -> `URLRouter`), consumer factory invocation, and window parsing.
   - `utils/sessions.py`: shared `actor_lease` locking discipline and provenance tracking (`connection_was_authenticated`, `note_authenticated_actor`).
   - `extensions/error_policy.py`: per-event result masking and shape validation.
   - `auth/mutations.py`: same-connection logout revocation and lock coordination.
2. Examined test suites:
   - `tests/test_routers.py` (166 tests): covers router protocol mapping, Host validation, revalidation windows, revocation state transitions, control frame serialization, stop-aware schemas, and error policy masking on subscriptions.
3. Test executions:
   - `uv run pytest tests/test_routers.py --no-cov` (166 passed).
4. Scratch tests:
   - `docs/review/temp-tests/consumers/test_consumers_scratch.py`: verified revalidation window validation matrix, host metadata projection, revocation state machine transitions, retry/abandon bounds, host validator denial delegation, and stop-aware result generator termination with `aclose` execution (6 passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/consumers.py` is exceptionally well-crafted, robust, and cleanly isolated. It strictly enforces security boundaries (outbound frame gating, monotonic window caching, fail-closed revalidation, shared actor lease serialization with auth mutations, and Django-delegated Host validation). Test coverage is comprehensive with 0 defects or design improvements identified.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/consumers.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/test_routers.py` (166 tests) thoroughly pins WebSocket Host validation, consumer factory synthesis, admission and outbound frame revalidation, monotonic window caching, revocation state machine transitions, close shielding, and error policy masking on subscriptions.
- **Scratch verification:**
  - `docs/review/temp-tests/consumers/test_consumers_scratch.py` passed (6/6 tests), verifying window validation, host header projection, revocation retry bounds, host denial delegation, and stop-aware result stream termination.
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/consumers.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/consumers.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

Independently traced and verified the WebSocket transport security subsystem, Host boundary, consumer factory, actor revalidation checkpoints, revocation state machine, and stop-aware result streaming in `django_strawberry_framework/consumers.py`.

### 1. Scoped diff and zero-edit confirmation
- Target: `django_strawberry_framework/consumers.py`
- Baseline: `HEAD` (`12779c99`)
- Scoped diff: `git diff 12779c99 -- django_strawberry_framework/consumers.py` is empty.

### 2. Behavioral re-trace and contracts verified
- **WebSocket Host boundary (`DjangoWebSocketHostValidator`, `_host_validation_request`)**:
  - Re-traced handshake metadata projection into Django `HttpRequest`. Replicated exact Django ASGI adapter semantics (Latin-1 decoding, lower-cased header normalization, duplicate header comma-joining, `SERVER_NAME`/`SERVER_PORT` fallback).
  - Verified `HttpRequest.get_host()` invocation and confirmed that only `DisallowedHost` is mapped to `channels.security.websocket.WebsocketDenier` (returning close code 1000 byte-identical to origin denial), while non-matching exceptions fail closed.
- **Revalidating consumer factory (`build_revalidating_consumer_class`)**:
  - Verified dynamic class generation for `_RevalidatingTransportWSHandler`, `_RevalidatingGraphQLWSHandler`, and `_RevocationGatedWebSocketAdapter`.
  - Confirmed class construction is purely function-local and unexported from the module, keeping `django_strawberry_framework.consumers` clean of soft dependencies (`channels`, `strawberry`).
- **Dual security revalidation checkpoints (`revalidate_operation_actor`, `send_revalidated_operation_frame`, `_actor_is_current`)**:
  - Verified Checkpoint 1 (operation admission) intercepts new operations and suppresses execution if actor is revoked/stale.
  - Verified Checkpoint 2 (outbound frames) intercepts `next`, `data`, and operation-scoped `error` frames, preventing post-revocation data leakage on running subscriptions.
  - Confirmed `actor_lease` locking discipline serializes validation, state transition, and frame dispatch atomically with `auth/mutations.py` same-connection logout mutations.
  - Confirmed actor freshness validation via `_refreshed_actor` (calling `channels.auth.get_user`), write-back to `scope["user"]`, and monotonic window caching (`_REVALIDATED_AT_SCOPE_KEY`).
  - Confirmed fail-closed semantics on revalidation exceptions (connection revoked immediately).
- **Revocation state machine (`_ConnectionRevocation`, `_revoke_connection`)**:
  - Verified 5-state lifecycle (`PERMITTED`, `DECIDED`, `CLOSING`, `CLOSED`, `ABANDONED`).
  - Verified `decide()` sets read-free `revoked` latch synchronously before any await.
  - Verified retry bounding (`_MAX_REVOCATION_CLOSE_ATTEMPTS = 2`) and shielded close task execution sending `4403` / `"Forbidden"`.
  - Verified `disconnect()` settles active close tasks within a `finally` block to prevent orphan background tasks.
- **Stop-aware result source & error policy masking (`_StopAwareSchema`, `_stop_aware_results`)**:
  - Verified wrapper on `subscribe` and `stream` methods cleanly terminates async generator iteration upon connection revocation.
  - Verified `aclose()` invocation on inner generator when supported.
  - Verified per-event GraphQL error masking via `extensions.error_policy.mask_execution_result` before frames reach the wire.
- **Revalidation window validation (`resolved_revalidation_window`)**:
  - Verified strict type checking (only exact `int` and `float`, rejecting booleans and numeric subclasses).
  - Verified rejection of negative and non-finite (`inf`, `-inf`, `nan`) values.
  - Verified chained `OverflowError` handling for astronomical integer values.

### 3. Test executions and scratch tests
- **Permanent tests**:
  - `uv run pytest tests/test_routers.py --no-cov` (166 passed).
- **Scratch tests**:
  - `docs/review/temp-tests/consumers/test_consumers_scratch.py` (6 passed).
  - `docs/review/temp-tests/consumers/test_worker2_scratch.py` (6 passed): independently challenged window validation matrix, host projection, host validator middleware with `WebsocketCommunicator`, revocation state machine transitions/retries/cancellations, and stop-aware result generator termination with `aclose`.

### 4. Disposition of findings
- High / Medium / Low findings: None.
- All contracts, boundaries, and safety invariants are fully upheld.
- Review complete; verified.
