# Review: `django_strawberry_framework/consumers.py`

Status: verified

## Understanding

`consumers.py` owns the Channels WebSocket transport boundary that the router composes: the Django-backed Host validator and the generated `GraphQLWebSocketConsumer`. The generated consumer derives both Strawberry protocol handlers and the upstream adapter, revalidates the session actor at operation admission and before information-bearing frames, refreshes `scope["user"]`, stops result sources after revocation, applies per-event error masking, and owns a bounded `4403` close state machine. The Host validator projects only Host-related ASGI metadata into `HttpRequest.META`, delegates matching to `HttpRequest.get_host()`, and uses Channels' `WebsocketDenier` for a denied handshake.

The call graph was traced through `routers.py` (lazy `channels` guard, Host > Origin > AuthMiddlewareStack > URLRouter composition, injected-consumer seam), Strawberry's installed `GraphQLWSConsumer` and both protocol handler implementations, `utils/sessions.py` (shared actor lease and provenance), `auth/mutations.py` (same-connection Channels logout and lock order), `utils/permissions.py` (Channels request adapter), the production error-policy mask, Django's `HttpRequest.get_host()` / ASGI header projection, and the fakeshop package view/URLconf. The assigned baseline had no target diff for `consumers.py`; the initial focused router suite was green before edits.

## Verification

- `uv run pytest tests/test_routers.py --no-cov` passed 149 tests before edits.
- `docs/review/temp-tests/consumers/control_frame_race.py` used a fake adapter whose `send_json` parked after the production adapter's revoked check. Publishing `revoked=True` during that await still committed the control frame, proving the check/send race.
- `docs/review/temp-tests/consumers/prestart_close_cancel.py` cancelled the connection-owned close task after creation but before `_attempt_close()` ran. The task finished cancelled while `_ConnectionRevocation.state` remained `closing`; `settle()` returned without normalizing it.
- Installed Strawberry source inspection confirmed `GraphQLWSConsumer.run` constructs the class-level adapter by name, transport-ws uses `schema.stream`, legacy graphql-ws uses `schema.subscribe`, and both operation result loops reach the adapter. Installed Channels inspection confirmed `AsyncWebsocketConsumer.close`, `OriginValidator`, `AllowedHostsOriginValidator`, `WebsocketDenier`, and `channels.auth.get_user` behavior.
- `tests/test_routers.py` already exercises malformed JSON/non-text dispatch through upstream handlers, both subprotocols, Host/Origin independence and Django verdict delegation, AuthMiddlewareStack sessions, URL exact matching, soft-dependency eviction, sync/async session reload, logout transitions, error masking, stop-aware teardown, close retries, and transport ordering.
- Fakeshop live transport tests in `examples/fakeshop/test_query/test_transport_api.py` exercise the package GraphQL HTTP view over Django's real middleware/URL lifecycle. The fakeshop has no ASGI entry point, so the Channels router itself is genuinely unreachable live and remains package-tier tested.

## Improvements

### High

None.

### Medium

- **Observation:** Delegated connection-control frames (`complete`, `ping`/`pong`, `connection_ack`, and keep-alive frames) checked `revoked` and then awaited upstream `send_json` without the connection actor lease. A concurrent admission/frame checkpoint or same-connection logout could publish the revocation during that await, allowing the control frame to commit after the package's documented connection-wide cut-off.
- **Evidence:** The scratch fake adapter in `docs/review/temp-tests/consumers/control_frame_race.py` produced `[{"type": "complete"}]` after the revocation flag was published while the send was parked. The production lease is the synchronization owner used by `_revoke_connection()` and `auth/mutations.py::_channels_logout`; the control branch was the only write path outside it.
- **Impact:** A revoked socket could receive a post-revocation control frame, contradicting the stated “nothing further” invariant and risking protocol writes after the `4403` close on a real transport. Although control frames carry no operation payload, the resulting race weakens close/error lifecycle correctness and can surface upstream worker-task errors.
- **Recommendation:** Hold `utils/sessions.py::actor_lease` across the delegated frame's revoked-state check and asynchronous upstream send. Preserve upstream payload and protocol semantics, but serialize every write with the same connection-scoped transition owner.
- **Proof:** `tests/test_routers.py::test_control_frame_send_serializes_with_a_concurrent_revocation` parks a real adapter-shaped control send, starts a revocation that acquires the production actor lease, and proves the revocation waits until the send completes.

- **Observation:** `_ConnectionRevocation` could remain in `CLOSING` forever when its connection-owned close task was cancelled before `_attempt_close()` started. `settle()` returned immediately for any done task and assumed the task had recorded its outcome, but a pre-start cancellation gives the task no opportunity to set `ABANDONED`.
- **Evidence:** `docs/review/temp-tests/consumers/prestart_close_cancel.py` reproduced `before cancellation closing False`, `after cancellation closing True True`, and `after settle closing True True`.
- **Impact:** The state machine could claim a close was still in flight after its task was finished, making later checkpoint awaits target an already-cancelled task and violating the terminal ownership contract described by the module.
- **Recommendation:** When `close()` or terminal `settle()` observes a done-and-cancelled attempt, transition it to terminal `ABANDONED` before returning. This covers the only cancellation ordering in which `_attempt_close()` cannot record its own state.
- **Proof:** `tests/test_routers.py::test_a_prestart_cancelled_close_task_becomes_abandoned` cancels the attempt before its body starts, runs `settle()`, and asserts the task is done/cancelled and the state is `ABANDONED`.

### Low

None.

## Summary

The Host/Origin boundary, AuthMiddlewareStack composition, protocol handler lifecycle, session revalidation, error masking, malformed-frame delegation, soft dependency imports, URL routing, and live HTTP ownership are coherent. Two medium lifecycle races were confirmed and fixed: delegated control writes now serialize with revocation, and pre-start close cancellation reaches the terminal abandoned state.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/consumers.py`: delegated non-information-bearing adapter writes now hold the shared actor lease through the revoked check and upstream send; `_ConnectionRevocation.close()` and `.settle()` normalize a pre-start cancelled close task to `ABANDONED`; surrounding docstrings/comments now state the stronger serialization contract.
- Changed `tests/test_routers.py`: added a production-seam race regression for control-frame/revocation ordering and a state-machine regression for pre-start close-task cancellation.
- Scratch verification: `uv run python docs/review/temp-tests/consumers/control_frame_race.py` reproduced the original post-revocation control write; `uv run python docs/review/temp-tests/consumers/prestart_close_cancel.py` reproduced the original stuck `CLOSING` state. Both experiments were rerun conceptually against the permanent regressions.
- Focused post-edit validation: `uv run pytest tests/test_routers.py --no-cov -k 'control_frame_send_serializes_with_a_concurrent_revocation or connection_control_frames_never_reach_the_outbound_checkpoint or delegated_control_frame_is_suppressed_once_the_revocation_is_decided or nothing_is_written_to_the_socket_after_the_revocation_close'` — 6 passed; `uv run pytest tests/test_routers.py --no-cov -k 'prestart_cancelled_close_task or control_frame_send_serializes_with_a_concurrent_revocation or cancelling_the_teardown_ends_the_close_attempt or cancelled_disconnect_leaves_no_task or teardown_cancelled_before_it_returns or teardown_that_raises_still_settles'` — 6 passed.
- Formatter/linter: `uv run ruff format .` and `uv run ruff check --fix .` passed.
- Rejected findings: no additional Host parsing or Channels protocol reimplementation was added; Django's `HttpRequest.get_host()`, Channels' Origin validator/denier, Strawberry's handler dispatch, and the existing live/package tests already own and verify those contracts. The unconditional `source.aclose()` follows Strawberry's `Schema.stream` async-generator contract and was not changed.
- Changelog: no entry added; these are bounded alpha transport lifecycle corrections.

## Independent verification (Worker 2)

- Re-traced the complete Channels lifecycle against the installed upstream sources: `GraphQLWSConsumer.receive()` queues text or a non-text sentinel; `ChannelsWebSocketAdapter.iter_json()` raises the upstream `NonTextMessageReceived` / `NonJsonMessageReceived` signals; the transport-ws handler converts malformed frames to its `4400` close, while the legacy handler preserves its own binary/JSON handling; both protocol handlers route admission through `handle_subscribe` / `handle_start`, stream results through `schema.stream` / `schema.subscribe`, and emit operation/control frames through the adapter's `send_json`. No package protocol reimplementation or malformed-frame bypass was found.
- Re-traced router callers and ordering: `routers.py::_build_router_class` composes `DjangoWebSocketHostValidator` outside `AllowedHostsOriginValidator`, `AuthMiddlewareStack`, and the exact `URLRouter` route; HTTP is the supplied Django ASGI application by identity. The Host projection delegates matching to `HttpRequest.get_host()` and normalizes only `DisallowedHost` through Channels' `WebsocketDenier`. `utils/permissions.py::request_from_info` reads the scope-backed actor used by resolvers.
- Re-traced revocation and actor ownership: `consumers.py::send_revalidated_operation_frame` and the delegated adapter branch both hold `utils/sessions.py::actor_lease` through the state decision and asynchronous send; `auth/mutations.py::_channels_logout` takes `scope_session_lock` outermost and `actor_transition`/the same actor lease inside it. `_refreshed_actor` keeps the `channels.auth.get_user` and session-store imports inside the async revalidation path, crossing the existing `database_sync_to_async` boundary once. The scope provenance latch keeps an authenticated-to-anonymous logout read-free and fail-closed.
- Re-traced close/retry/teardown: `_ConnectionRevocation` permits one close plus one retry after a transport exception, shields live waiters, and lets terminal `disconnect()` settlement cancel and await the connection-owned attempt. The new done-and-cancelled checks normalize a pre-start-cancelled attempt to terminal `_REVOCATION_ABANDONED`; no subsequent checkpoint can restart it.
- Baseline failability proof (without modifying tracked files): loading `consumers.py` from `4c85560f77b6b15e41c40eb4e7da35bdffd80bb1` into a temporary module showed the old delegated send allowed revocation to complete while the send was parked and then committed `{'type': 'pong'}` after revocation; the old pre-start cancellation sequence left the attempt `done/cancelled` while state remained `closing`. These are the exact invariants asserted by the two permanent tests in `tests/test_routers.py`, which are correctly package-tier tests because the fakeshop has no ASGI router entry point.
- Focused validation: `uv run pytest tests/test_routers.py --no-cov -k 'control_frame_send_serializes_with_a_concurrent_revocation or prestart_cancelled_close_task or connection_control_frames_never_reach_the_outbound_checkpoint or delegated_control_frame_is_suppressed_once_the_revocation_is_decided or nothing_is_written_to_the_socket_after_the_revocation_close or cancelling_the_teardown_ends_the_close_attempt or cancelled_disconnect_leaves_no_task or teardown_cancelled_before_it_returns or teardown_that_raises_still_settles'` — 11 passed; complete router-focused validation `uv run pytest tests/test_routers.py --no-cov` — 151 passed. No additional finding remains.
