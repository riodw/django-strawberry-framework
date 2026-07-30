# Builder artifact — review round 2, Blocker 1: WebSocket revocation of a running operation

Cohort: **WS revocation**. Files touched: `django_strawberry_framework/consumers.py`,
`tests/test_routers.py`. Nothing else was edited (see [Files I did not touch](#files-i-did-not-touch)).

Result: `uv run pytest tests/test_routers.py --no-cov` → **84 passed**. Full suite
`uv run pytest --no-cov` → **5051 passed, 40 skipped**. `ruff format` / `ruff check` /
`scripts/check_trailing_commas.py --check` clean on both files.

## 1. What was wrong

`consumers.py::build_revalidating_consumer_class` overrode only the two operation-**admission**
methods, `BaseGraphQLTransportWSHandler.handle_subscribe` and `BaseGraphQLWSHandler.handle_start`.
An admitted operation then lives inside upstream's own result loop —
`BaseGraphQLTransportWSHandler.run_operation` #"async for result in result_source" and
`BaseGraphQLWSHandler.handle_async_results` #"async for result in result_source" — and sends every
later result without ever returning through the admission method. A subscription admitted one
second before a logout kept emitting for as long as it lived, so `GraphQLWebSocketConsumer`'s "a
revoked session stops executing" was false. No shipped row could detect it: `Subscription.tick`
yielded exactly once, and every revocation row let operation 1 finish before revoking.

## 2. What I built

Three hooks, one shared decision, one connection-scoped response.

| Site | Kind | Decides |
| --- | --- | --- |
| `_RevalidatingTransportWSHandler.handle_subscribe` | admission | may a new `graphql-transport-ws` operation start |
| `_RevalidatingGraphQLWSHandler.handle_start` | admission | may a new legacy `graphql-ws` operation start |
| `_RevocationGatedWebSocketAdapter.send_json` | outbound | may this `next` / `data` / operation `error` frame be written |

- **The seam is `websocket_adapter_class`**, read off `base_consumer_cls` and installed on the
  generated consumer exactly as the two handler classes already are. Upstream instantiates it by
  name, once per connection, in `strawberry/http/async_base_view.py::AsyncBaseHTTPView.run`
  #"self.websocket_adapter_class(self, request, websocket_response)", and both protocols funnel
  every frame through that instance's `send_json`. No upstream module is imported and no instance
  is patched.
- **`consumers.py::send_revalidated_operation_frame(websocket, message, send)`** owns the whole
  critical section, so the derived adapter is a two-line delegate like the handler subclasses. The
  `send` argument is the adapter's own `super().send_json` bound method.
- **`consumers.py::revalidate_operation_actor(handler)`** is the admission checkpoint. It lost its
  `operation_id` and `errors_as_list` parameters (see §4).
- **`consumers.py::_actor_is_current(consumer)`** is the ONE decision both checkpoints await: the
  anonymous carve-out, the window comparison, the `channels.auth.get_user` reload, the fail-closed
  degrade, and the `scope["user"]` write-back. It never sends, closes, or cancels.
- **`consumers.py::_revoke_connection(websocket)`** is the ONE response: set the flag, then close
  through the adapter, idempotently.
- **Connection-local state** lives on the consumer instance: `_revocation_lock` (`asyncio.Lock`),
  `_revocation_observed` (`bool`). Channels constructs one consumer per connection, so
  "connection-local" is structural. See amendment **A5** — the spec currently says the adapter
  instance owns it.
- **Gated frame types** are the frozen set `_INFORMATION_BEARING_FRAME_TYPES = {"next", "data",
  "error"}`. `complete`, `connection_ack`, `connection_error`, `ping`, `pong`, `ka` delegate
  untouched.
- **Cancellation, not a raise.** After a suppressed frame the checkpoint calls
  `asyncio.current_task().cancel()`, and only when the current task is not the connection's own
  `run_task`. Rationale in §3.

## 3. Decisions inside the brief, and their reasons

### 3.1 Close code and reason: `4403` / `"Forbidden"`

Pinned by the coordinator's amendment 3, and it is the right pin. `4403` / `"Forbidden"` is
byte-identical to what upstream's own `handle_connection_init` sends when `on_ws_connect` raises
`ConnectionRejectionError`. Reusing it verbatim **is** the non-disclosure property: a revocation
close cannot be told apart from any other refusal to authorize the socket, so the wire cannot
distinguish "session revoked" from "session flushed" from "user disabled" from "the revalidation
read failed" from a connect-time rejection. The neighbouring codes upstream spends (4400 invalid
message, 4401 unauthorized, 4408 init timeout, 4409 duplicate id, 4429 too many subscriptions) all
describe something else, and a bespoke code would be a package-specific signal announcing exactly
which refusal fired. `tests/test_routers.py::_assert_revoked_close` asserts the exact reason
string for that reason — a package-flavoured reason is the regression it catches.

Consequence: the previous per-operation rejection message is **deleted** (§4). The wire now carries
no revocation prose at all, so nothing is left to leak — and nothing is left for a client to
branch on beyond "reconnect with a current session".

### 3.2 Both checkpoints produce the same response

Forced rather than chosen, and the derivation is worth keeping: an admission denial would have to
ride an operation-scoped `error` frame, which is a **gated** type, so the outbound checkpoint would
validate it against the same already-revoked actor, suppress it, and close. The client would never
receive it. Exempting that one frame to let it through would be precisely the disclosure
distinction the gated set exists to avoid.

### 3.3 The head-of-line-blocking tradeoff

One `asyncio.Lock` per connection spans **the window/cache decision, the session read, the
revoked-state transition, and the send**. Releasing it after validation admits exactly this
interleaving: sibling A passes validation; sibling B detects revocation and starts closing; A —
already authorized — emits its payload anyway. Holding it through the send closes that window.

The accepted cost, stated as a cost: a per-connection serialization point on the outbound hot path.
When a validation needs a session-store read, every concurrent operation waiting to emit **on that
socket** waits for that read. It is bounded three ways, and each bound is pinned by a row:

| Bound | Row |
| --- | --- |
| One connection only — a second socket is never serialized | `test_the_connection_lock_never_serializes_a_second_connection` |
| Protected frames only — never `complete`, ack, ping/pong, keep-alive | `test_connection_control_frames_never_reach_the_outbound_checkpoint` |
| Priced by the window — a positive window reuses one read across frames | `test_a_positive_window_defers_the_close_on_a_running_subscription` |

An anonymous socket takes the lock but never reads (the carve-out returns before the read); an idle
socket never takes it at all.

**One honest gap, and how I closed it.** The mutation "release the lock after validation instead of
after the send" is **not** observable on the wire in this test harness:
`channels.testing`'s `base_send` puts onto an unbounded `asyncio.Queue` and never suspends, so no
sibling can interleave into the window that mutation opens (a real ASGI server's socket write does
suspend, which is why the window is real in production). I verified this by building the mutant: it
passed all 81 rows. So `_record_outbound_gate` now wraps the checkpoint's own `send` argument and
records `consumer._revocation_lock.locked()` at the instant the production code calls it;
`test_a_valid_session_keeps_a_running_subscription_emitting_every_result` asserts
`sends_under_lock == [True, True]`. That measures the production lock at the production call site
rather than a stand-in for either. With the assertion in place the mutant fails.

### 3.4 Cancellation: `task.cancel()`, and never the connection's own task

`asyncio.current_task().cancel()` rather than `raise asyncio.CancelledError`. Cancelling delivers
the error at the operation's next suspension point, which is inside `result_source.__anext__()`, so
the subscription generator's own `finally` runs and the generator is closed. Raising from the send
would unwind the `async for` **body**, leaving the generator suspended for the interpreter's
asyncgen finalizer to close at an unrelated moment — a "Task was destroyed but it is pending" or an
unraisable warning under `-W error`, attributed to whatever test happened to be running.
`test_a_running_subscription_cannot_emit_a_result_after_revocation` asserts
`controller.finalized`, which is exactly that generator's `finally`.

The task guard is load-bearing, not defensive. Both protocols send their **subscription-limit**
`error` frame from the connection's own message-loop task (`handle_subscribe` /`handle_start`, after
our admission hook has already passed). Cancelling `run_task` there would abort the very
disconnect/shutdown path that has to cancel and await the remaining operations, and would surface a
`CancelledError` out of the ASGI application. In that case the close alone is the whole rejection
and there is no operation of ours to unwind.

Upstream's cancellation asymmetry is left alone and documented: legacy `handle_async_results`
catches `asyncio.CancelledError` and sends `complete`; transport-ws `run_operation` does not and
emits nothing. Both `complete`s land after the close — which is upstream's existing behavior on
every one of its own close paths (`cleanup()` runs from `handle()`'s `finally`, after any close).
`_drain_until_close` therefore stops at the close and asserts nothing about the tail. I checked for
fallout: no unraisable exception, no `RuntimeWarning`, no `ResourceWarning`, nothing in stderr,
across three repeat runs of the module and two full-suite runs. Nothing is silenced anywhere — there
is no new `except` in this change.

### 3.5 Teardown is upstream's

`BaseGraphQLTransportWSHandler.shutdown` and `BaseGraphQLWSHandler.cleanup` /
`::cleanup_operation` already walk every registered operation, cancel it, and await it from their
own `handle` loop's `finally`. The package adds no teardown. Pinned by
`assert [task for task in asyncio.all_tasks() if task is not asyncio.current_task()] == []`.

## 4. Code deleted as unreachable (coordinator amendment 2)

Verified by `grep -rn` across `django_strawberry_framework/` and `tests/`, not by assumption. All
three were reachable only from the per-operation error send:

| Removed | Was |
| --- | --- |
| `consumers.py::_REVOKED_SESSION_MESSAGE` | the rejection message text |
| `from graphql import GraphQLError` in `consumers.py` | formatted that message into a wire payload |
| `revalidate_operation_actor`'s `errors_as_list` keyword | the ONE per-protocol difference (a list for transport-ws, a bare object for legacy) |
| `revalidate_operation_actor`'s `operation_id` positional | the `error` frame's `id` |

`consumers.py` now imports **no** third-party module at module level — stdlib, this package's
logger, and `exceptions` only. The module docstring's claim about `graphql` was corrected
accordingly (amendment **B4**).

Test-side: `tests/test_routers.py::_assert_rejected` (the per-protocol error-payload assertion) and
`_REVOKED_SUBSTRING` were removed. **No coverage was dropped** — every row that used them was
rewritten to assert the close, and each grew assertions it did not have before (read counts, and
for the pipelined-frame rows, positive proof the operation never started).

## 5. Tests

Rewritten (existing subjects preserved, response changed to the close):

| Row | Change |
| --- | --- |
| 26 `..._closes_the_socket_on_the_next_operation_without_reconnecting` | 3 revocation shapes; asserts the close, `reads == 2` for one operation (one per checkpoint), and that a pipelined operation 3 is refused free (`not started.is_set()`, no extra read) |
| 28 `..._window_defers_the_denial_until_it_expires` | asserts the close, and `reads == 1` for two complete operations — four checkpoints on one read, which is the window's expanded meaning |
| 29 `..._legacy_graphql_ws_protocol_is_revalidated_at_handle_start` | asserts the close; notes the per-protocol payload asymmetry is gone |
| 30 `..._revalidation_store_failure_denies...` | asserts the close and **exactly one** log record — the revoked flag prevents a read storm behind it |
| 34 `..._real_second_request_logout...` | asserts the close; its request block extracted to `_logout_through_a_real_second_request` and reused by row 35 |
| 19 `..._default_websocket_consumer...` | unchanged, plus two new structural rows beside it |

New:

| Row | Proves |
| --- | --- |
| 19b `..._installs_a_derived_websocket_adapter_class` | derived **class** on the generated consumer, subclass of the base read off `base_consumer_cls`, `send_json` in its own `vars()`, upstream's attribute untouched |
| 19c `..._only_information_bearing_frames_reach_the_outbound_checkpoint` | the gated set is exactly `{next, data, error}`; the six control frames named individually (`ka` has no behavioral row — the router exposes no `keep_alive` knob) |
| 35 `..._running_subscription_cannot_emit_a_result_after_revocation` (×2 protocols) | **the finding**: multi-yield subscription, result 1 received, real second-request logout, result 2 produced (`emitted`) and never delivered, `4403`/`"Forbidden"`, generator `finally` ran, no task left |
| 36 `..._valid_session_keeps_a_running_subscription_emitting_every_result` (×2) | the control: both results delivered, socket open, `reads == 3`, and `sends_under_lock == [True, True]` |
| 37 `..._delayed_query_revoked_after_admission_never_sends_its_response` | the gate covers non-subscription operations (transport-ws only — legacy cannot execute a query) |
| 38 `..._operation_error_produced_after_revocation_is_suppressed_by_the_close` (×2) | an operation-scoped `error` frame is gated and replaced by the close, not preceded by it |
| 39 `..._connection_lock_stops_a_sibling_payload_escaping_after_revocation` | sibling `b` queues at the lock (recorded gate entry + `locked()` + zero reads of its own) and never emits; `reads == 3` catches dropping the lock entirely |
| 40 `..._revoked_but_idle_socket_stays_open_until_its_next_protected_checkpoint` | the accepted idle consequence: zero reads while idle (rules out a background monitor), ping/pong still works, the next checkpoint closes it |
| 41 `..._connection_lock_never_serializes_a_second_connection` | blast radius: socket 2 completes a full operation while socket 1 is parked inside its critical section; two distinct consumers, two distinct locks |
| 42 `..._positive_window_defers_the_close_on_a_running_subscription` | the window at the **frame** checkpoint: a revoked subscription still emits inside the window, closes at the first frame after it, one read per window not per frame |
| 43 `..._connection_control_frames_never_reach_the_outbound_checkpoint` | the negative census on a **valid** socket: ack, `complete` and three ping/pongs travel while exactly one frame (`next`) is gated; `reads` stays at 2 |

Test machinery added: `_OperationController` (+ `_CONTROLLERS`, an autouse clear) driving a
controlled multi-yield subscription, a controlled query, and a gated `SchemaExtension` on a second
schema; `_drain_until_close`; `_assert_revoked_close`; `_instrument_revalidation` (read counter,
optional per-session hold); `_record_outbound_gate` (gate entries, consumer identity,
`sends_under_lock`); `_reached` / `_wait_until` (bounded waits); `_send_operation`;
`_logout_through_a_real_second_request`.

Why the gated extension exists: `Schema.execute` and `Schema._subscribe` both wrap parsing and
validation in `extensions_runner.operation()`, so an async `on_operation` that awaits before
yielding is the only seam that can hold an operation which will **fail validation** — and a
validation failure is the only way to produce an operation-scoped `error` frame with controllable
timing.

### 5.1 Mutation testing (how I know the rows bite)

| Mutant | Result |
| --- | --- |
| `websocket_adapter_class = ...` removed from the generated consumer | **13 failed** |
| both admission hooks reduced to a bare `super()` call | **14 failed** |
| lock released after validation, before the send | **2 failed** (rows 36) |
| lock removed from the outbound checkpoint entirely | **3 failed** (rows 36 + 39) |

The first mutant initially **hung** rather than failed, because several rows awaited a controller
`Event` with no bound. That is now `_reached(...)`, a failure bound rather than a timing assumption
— the same role `timeout=10` plays on every communicator read in the module. All four mutants now
fail in under a minute. All were reverted; `git diff` shows only the two intended files from me.

## 6. Coverage

I did not run `--cov` (per the brief). Statically, every statement added to `consumers.py` is
exercised, including the two arms that look defensive:

- `revalidate_operation_actor`'s `if consumer._revocation_observed: return False` — rows 26 and 30
  (a frame pipelined behind the close).
- `_revoke_connection`'s idempotent early return — row 39 (sibling `b` reaching it second).
- `send_revalidated_operation_frame`'s `task = asyncio.current_task()` / `if task is not
  consumer.run_task:` / `task.cancel()` — all three statements execute on every operation-task
  suppression. `[tool.coverage.run]` sets no `branch = true`, so the untaken main-task direction
  costs nothing; **the only production path that reaches the checkpoint from `run_task` is the
  protocols' subscription-limit `error` frame**, which needs `max_subscriptions_per_connection`
  operations in flight and cannot be reached through the router (it exposes no such knob). Flagged
  here rather than worked around: if a future slice wants that direction covered, the honest way is
  an injected-consumer row, not a lowered limit.

## Required spec amendments

`docs/spec-046-transport_security-0_0_15.md` was rewritten by the custodian **in parallel with this
build** and already carries Decision 16, so most of what would have been listed here is already
correct. Everything below is what I found still false, incomplete, or divergent from what I
actually built, checked against the file as of this writing. I edited none of it.

### A. `docs/spec-046-transport_security-0_0_15.md`

**A1 — the lock's owner is the consumer instance, not the adapter instance.** This is a real
divergence, not wording.

- Current, `docs/spec-046-transport_security-0_0_15.md:2158`:
  > "**One connection-local lock, held through the send.** A single `asyncio.Lock`, owned by the
  > connection's adapter instance (upstream constructs exactly one per connection, which is what
  > makes "connection-local" structural rather than conventional), spans the whole critical
  > section"
- Recommended: > "A single `asyncio.Lock`, owned by the connection's **consumer instance** (Channels
  constructs exactly one consumer per connection, which is what makes "connection-local" structural
  rather than conventional), spans the whole critical section"
- Why: the consumer already owns `scope`, `revalidation_window` and `run_task`, all three of which
  the checkpoints read; the adapter reaches the consumer as `self.ws_consumer` and the admission
  handler reaches it as `handler.view`, so one home serves both checkpoints with no extra hop. My
  brief specified the consumer explicitly. Both objects are one-per-connection, so nothing about
  the argument changes — only the noun.

**A2 — same divergence in the DRY obligations.**

- Current, `docs/spec-046-transport_security-0_0_15.md:2564`:
  > "The connection-local lock, the revoked flag and the last-validated timestamp are **one** set of
  > state on the adapter instance upstream already creates per connection — not three parallel
  > caches keyed by protocol."
- Recommended: > "... are **one** set of state on the consumer instance Channels already creates per
  > connection — the lock and the revoked flag as instance attributes, the last-validated timestamp
  > on the ASGI `scope` where `_REVALIDATED_AT_SCOPE_KEY` already put it — not three parallel caches
  > keyed by protocol."
- Why: the timestamp is **not** on the same object as the other two. It lives on the scope under
  `consumers.py::_REVALIDATED_AT_SCOPE_KEY`, unchanged from Slice 4, because that is what
  `channels.auth`-style scope state looks like and it is what the existing window rows read. The
  sentence as written would send a reader looking for a third instance attribute.

**A3 — name the two module-level entry points, so Helper-reuse is checkable.**

- Current, `docs/spec-046-transport_security-0_0_15.md:2556`:
  > "**The WebSocket revalidation is one function, called from all three seams.**"
- Recommended: keep the sentence and add the names as shipped:
  `consumers.py::revalidate_operation_actor(handler)` (admission),
  `consumers.py::send_revalidated_operation_frame(websocket, message, send)` (outbound),
  `consumers.py::_actor_is_current(consumer)` (the shared decision) and
  `consumers.py::_revoke_connection(websocket)` (the shared response).
- Why: the paragraph promises one decision function and one response coroutine but names neither, so
  nothing in the spec pins the shape a later reader is supposed to preserve. Note the outbound
  entry point takes `send` (the adapter's own `super().send_json`) precisely so the lock can span
  the send while the adapter stays a two-line delegate; that is the fact most at risk of being
  "simplified" away.

**A4 — the gated-set constant has a name worth pinning.**

- Current, `docs/spec-046-transport_security-0_0_15.md:2108`:
  > "The gated frame types are deliberately `next` (`graphql-transport-ws`), `data` (legacy
  > `graphql-ws`), and operation-scoped `error` frames."
- Recommended: add "spelled once as `consumers.py::_INFORMATION_BEARING_FRAME_TYPES`, which
  `tests/test_routers.py` asserts against a re-typed literal set".
- Why: `ka` and the other control frames have no behavioral row available (the router exposes no
  `keep_alive` knob), so the constant *is* their contract.

**A5 — Test-plan row 27's "idle authenticated socket" clause needs its fixture named, or it reads as
uncovered.**

- Current, `docs/spec-046-transport_security-0_0_15.md:2947`:
  > "Plus the property the window exists to buy: an **idle** authenticated socket performs zero
  > session reads however long it sits."
- Recommended: > "... performs zero session reads however long it sits — measured on a **revoked**
  > idle socket, the strictly stronger fixture, since a socket with something to find that still
  > performs no read cannot be running a background monitor."
- Why: that is where I put it (`test_a_revoked_but_idle_socket_...`). An idle *valid* socket's zero
  reads is also asserted, incidentally, by row 36's `reads == 3` across two gated results with an
  idle gap between them. Stating the fixture keeps a later reader from adding a duplicate row.

**A6 — Test-plan row 37's serialization half cannot be earned the way the row implies, and the spec
should say why.**

- Current, `docs/spec-046-transport_security-0_0_15.md:2996`:
  > "37. Serialization: two concurrent operations on one socket cannot interleave a passed validation
  > with a sibling's revocation — the losing task's payload is never emitted."
- Recommended: add: > "The *placement* of the lock release is asserted directly, not inferred from
  > the wire: `channels.testing`'s `base_send` puts onto an unbounded queue and never suspends, so
  > releasing the lock after validation instead of after the send is invisible in-process. The row
  > therefore observes the connection's lock at the instant the checkpoint calls `send`."
- Why: I built the "release early" mutant and it passed the entire suite before this assertion
  existed. Without the note, a future reader deletes the assertion as redundant with the wire
  checks.

**A7 — Test-plan row 34's "cancelled or completed" should name the observable.**

- Current, `docs/spec-046-transport_security-0_0_15.md:2984`:
  > "prove result 2 is **never delivered**, that the operation is cancelled or completed, and that
  > the connection is closed with `4403` / `"Forbidden"` and no operation `error` frame"
- Recommended: > "... prove result 2 was **produced by the resolver and never delivered**, that the
  > subscription generator's `finally` ran (which is what distinguishes cancellation that unwinds
  > the operation from a send that was merely skipped), and that the connection is closed with
  > `4403` / `"Forbidden"` and no operation `error` frame"
- Why: "never delivered" alone is satisfied by an implementation that never generated the result;
  and "cancelled or completed" has no wire signature on transport-ws (a cancelled `run_operation`
  emits nothing at all). The two observables that exist are the resolver-side record and the
  generator's `finally`.

**A8 — `docs/README.md` still carries the old per-operation claim** (Slice 5's file, listed here so
the custodian's sweep has it):

- Current, `docs/README.md:360`:
  > "The package's default WebSocket consumer revalidates the session actor **before every
  > operation** and writes the refreshed actor back onto `scope["user"]`, so a revoked, flushed, or
  > disabled session cannot keep executing on an already-established socket. That costs one session
  > read per authenticated operation"
- Recommended: > "... revalidates the session actor at two checkpoints — before admitting any
  > operation **and** immediately before sending any information-bearing operation frame (`next`,
  > `data`, or an operation-scoped `error`) — and writes the refreshed actor back onto
  > `scope["user"]`. A revoked actor can therefore neither admit another operation nor emit another
  > information-bearing frame; the failure closes the whole socket with `4403` / `"Forbidden"`. That
  > costs one session read per authorized event (admission or information-bearing frame)"
- And `docs/README.md:390`:
  > "With revalidation on, the freshness bound is the revalidation window rather than the connection
  > lifetime."
- Recommended: > "With revalidation on, the freshness bound is the revalidation window plus the wait
  > for the connection's next protected checkpoint — detection is event-boundary-driven, so an idle
  > revoked socket stays open until it next tries to admit an operation or emit a frame. Socket
  > lifetime, idle timeout and connection count remain transport-resource policy for the ASGI server
  > or reverse proxy."

### B. `consumers.py` docstrings — false or incomplete sentences, all FIXED in this change

Recorded with their previous wording so the custodian can confirm the replacements read the way
Decision 16 requires.

**B1 — the false production claim** (the one the review named).

- Was, `consumers.py::GraphQLWebSocketConsumer` (Decision 12 paragraph):
  > "And with per-operation revalidation on, the security-relevant bound is the revalidation window
  > rather than the connection lifetime, because a revoked session stops executing without the
  > socket having to end."
- Now: > "What revalidation does and does not buy, stated precisely because the weaker reading of it
  > was wrong: **a revoked actor cannot admit another operation or emit another information-bearing
  > operation frame**. Detection is event-boundary-driven, not an asynchronous promise to interrupt
  > an idle resolver at the instant an external logout occurs - so the security-relevant bound is the
  > revalidation window plus the wait for the connection's next protected checkpoint, while socket
  > lifetime, idle timeout, and connection count stay transport-resource policy the layers above
  > own."
- Note both halves were false: the socket **does** end now.

**B2 — the module docstring's "before every operation" framing.**

- Was: > "a thin `strawberry.channels.GraphQLWSConsumer` subclass that revalidates the session actor
  > **before every operation** ... An established socket therefore cannot keep executing on a
  > session that was revoked, flushed, or whose user was disabled after the handshake."
- Now: the two-checkpoint enumeration, the seam, the gated set, the connection-scoped response, the
  lock and its head-of-line cost, the window's expanded meaning, and the idle-socket consequence.

**B3 — the per-operation rejection contract.**

- Was, `revalidate_operation_actor`: > "It returns `True` to let upstream run the operation, or sends
  > the operation's own `error` message and returns `False`. The socket is never closed: both
  > protocols carry a per-operation error channel, and this mirrors their own pre-execution
  > refusals."
- Now: > "Returns `True` to let upstream run the operation. Returns `False` after revoking the
  > connection - which closes the socket - so the caller's only job is to skip its `super()`
  > delegation. Nothing is sent on the way out: the close IS the rejection, and it is byte-identical
  > to the outbound checkpoint's. That symmetry is forced rather than chosen ..."

**B4 — the module's dependency inventory.**

- Was: > "the module level reaches only for the standard library, `graphql` (the hard dependency
  > Strawberry already carries, for the rejection's wire shape), this package's logger, and
  > `exceptions.ConfigurationError` / `exceptions.describe_value`" and "the two protocol handler base
  > classes are never imported at all".
- Now: no `graphql` (the import is deleted), and all **three** bases — both handlers and the adapter
  — are named as read off `base_consumer_cls`.

**B5 — the "no lock" claim.**

- Was, `revalidate_operation_actor`: > "It takes **no** lock: `auth/sessions.py::scope_session_lock`
  > serializes session *mutations*, while this is a read of a private store ... and taking a mutation
  > lock on the socket's critical path would add contention for nothing."
- Now: the same argument scoped to the *session* lock, plus "The lock it does take is the
  connection's own revocation lock, which exists for a different reason entirely: it makes the
  validate-transition-send sequence atomic against sibling operations on the same socket." The old
  sentence is now simply false as a blanket statement.

**B6 — `resolved_revalidation_window`'s two references to per-operation cost.**

- Was: the `_unusable_window_error` message's "(0.0 revalidates the session actor on every
  operation)" and the docstring's "one session read per authenticated operation against a named
  revocation delay".
- Now: "(0.0 revalidates the session actor at every operation admission and before every
  information-bearing operation frame)" and "one session read per authenticated **checkpoint**". No
  test asserted that message beyond `match="websocket_revalidation_window"`, so the reword is safe.

**B7 — the fail-closed log message.**

- Was: > "the per-operation session revalidation failed; the operation is denied (fail-closed) rather
  > than executing on the connection's cached actor."
- Now: > "the WebSocket session revalidation failed; the connection is revoked and closed
  > (fail-closed) rather than continuing on the connection's cached actor."
- The `"fail-closed"` substring is still what `tests/test_routers.py` asserts, deliberately.

**B8 — the stale-actor rationale moved.** The "the stale actor stays on the scope … so every later
operation on that socket is denied identically" comment lived in the send branch; the "denied
identically" mechanism is now the connection-local revoked flag, so the comment says
> "Downgrading it to `AnonymousUser` would let anything still holding this scope read an anonymous
> session instead of a revoked one (spec-046 Decision 11); the connection is about to be closed
> either way."

## Files I did not touch

Confirmed by `git diff --stat`: the other dirty paths in the tree
(`_request_body.py`, `views.py`, `conf.py`, `auth/*`, `README.md`, `docs/README.md`,
the incoming review, `docs/spec-046-*`, `docs/builder/build-046-*`, `TODAY.md`,
`tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py`) are concurrent
maintainer / other-worker work and carry none of my edits.

## Things the review did not mention that I found

1. **The admission checkpoint's own error frame is gated by the new checkpoint.** This is what makes
   the unified response mandatory rather than tasteful — the coordinator's amendment 1 states it,
   and it is worth keeping in the spec because it converts a style question into a proof.
2. **The "release the lock after validation" mutation is invisible in this harness** (§3.3). Any
   future review that tries to verify the lock's placement from wire assertions alone will conclude,
   wrongly, that the placement does not matter.
3. **Suppressing a transport-ws `error` frame de-registers the operation before the suppression.**
   `Operation.send_operation_message` sets `completed = True` and calls `forget_id()` *before*
   sending, so a suppressed `error` frame leaves `handler.operations` already clean and
   `shutdown()` has nothing to cancel for it. Harmless, but it is why the error-frame rows cannot
   assert on the operation registry the way the subscription rows can.
4. **Upstream abandons the `_subscribe` async generator after `send_initial_errors`.**
   `run_operation` `break`s out of the loop without closing `result_source`, so a validation-failing
   subscription over transport-ws leaves an async generator for the interpreter's finalizer —
   upstream's behavior, unchanged by this build, and it produced no warning in any run. Noted so a
   future `-W error` flake in that area is not misattributed to the gate.
5. **Only the subscription-limit `error` frame reaches the outbound checkpoint from the connection's
   own task**, and the router cannot reach it (§6). That is the one production path in this change
   with no test, and the reason is a missing seam rather than a missing row.

---

# Build report (Worker 2, pass 2) — W3 review remediation: M2, M4 (fail-closed degrade), M5, L3, L4

Cohort: **WS revocation**, second pass. Input: `docs/builder/bld-review-2-w3_review.md` (Worker 3
adversarial review, `revision-needed`). Files touched this pass:
`django_strawberry_framework/consumers.py`, `tests/test_routers.py`, and this artifact.

Result: `uv run pytest tests/test_routers.py --no-cov` -> **122 passed** (104 at review time; +18
rows across both WS cohorts this pass). Full suite -> **5099 passed, 40 skipped**. Counts, the
delta attribution, the validation commands and the floor evidence are recorded once, in
`bld-review-2-ws_host_boundary.md`'s pass-2 report §7-§8 — both cohorts share one test module and one
focused command, so duplicating them here would be two numbers that can drift apart.

## 1. Findings closed in this pass

| Finding | Verdict | What landed |
| --- | --- | --- |
| **M2** — the `run_task` guard is untested and the recorded reason is FALSE | accepted in full; the review is right and pass 1 §6 / note 5 were wrong | `test_the_subscription_limit_error_frame_is_gated_from_the_connections_own_task`, both protocols. Mutant now fails **2** rows (was 0) — **including the guard's direction**, which the review believed unobservable |
| **M4** (my half) — the fail-closed revalidation degrade rests on one injection point | accepted | `test_a_failing_auth_backend_load_also_fails_closed` — the OTHER half of `_refreshed_actor`. Mutant now fails **2** rows (was 1) |
| **M5** — a per-outbound-message serialization point landed with no number | accepted | numbers in [§3](#3-hot-path-budget), captured over a stated iteration count against upstream's own consumer as the baseline. No design change |
| **L3** — `sends_under_lock` measures a whole-lock property | accepted as the review framed it (option b) | the limit is now written into `_record_outbound_gate`'s docstring, including what a future contended row would have to add. See [§4.1](#41-l3-why-i-took-the-documentation-option) |
| **L4** — `getattr(consumer, "revalidation_window", ...)` is dead defensiveness | accepted | plain attribute access, with the reason for NOT being defensive stated at the line |
| the review's note 2 to Worker 1 — pass 1 §6 must be corrected before it becomes spec prose | accepted | corrected here in [§2](#2-correcting-pass-1s-false-claim), and the corrected fact is amendment **A9** |

## 2. Correcting pass 1's false claim

Pass 1 §6 and "Things the review did not mention" #5 recorded the outbound checkpoint's main-task
direction as unreachable:

> "the only production path that reaches the checkpoint from `run_task` is the protocols'
> subscription-limit `error` frame, which needs `max_subscriptions_per_connection` operations in
> flight and cannot be reached through the router (it exposes no such knob)."

**The second half of that sentence is false, and the conclusion drawn from it was wrong.** No knob is
needed, because upstream does not default the limit to `None`:
`strawberry/channels/handlers/ws_handler.py::GraphQLWSConsumer.__init__` #"max_subscriptions_per_connection: int | None = 100"
— and the same `100` on `strawberry/http/async_base_view.py::AsyncBaseHTTPView`. So the shipped
router reaches the limit frame with 101 in-flight operations and the shipped consumer, and both
protocols send it from the connection's own message loop
(`graphql_transport_ws/handlers.py::BaseGraphQLTransportWSHandler.handle_subscribe` #"Subscription limit reached"
and `graphql_ws/handlers.py::BaseGraphQLWSHandler.handle_start` #"Subscription limit reached").

The error was not an arithmetic slip; it was **not checking the fixture**. Pass 1 asserted a property
of the router ("it exposes no such knob") and inferred a property of the path, without asking what
upstream's default actually was — one grep. That is exactly the failure mode
`docs/builder/worker-2.md` "Suspect the fixture before calling a boundary untestable" names, and it
is now recorded here so the next reader does not inherit the claim. The proposed remedy (an injected
consumer row) was also wrong: an injected consumer opts out of the gate entirely, so it could not
have exercised this path at all.

## 3. Hot-path budget

The plan (`docs/builder/build-046-transport_security-0_0_15.md`) predates `BUILD.md`'s
`## Hot-path budget` and carries no hot-path declaration, so this number is captured under the
review's M5 escalation rather than under a plan declaration. `send_revalidated_operation_frame` runs
**per outbound information-bearing frame** and takes a connection-local lock **held across a
session-store read**, which is the definition twice over ("per connection", "per outbound message").

**Instrument:** `docs/builder/temp-tests/review-2-w2/test_hotpath_budget.py` (gitignored scratch,
outside `pytest.ini`'s `testpaths`). Run as
`uv run pytest docs/builder/temp-tests/review-2-w2/test_hotpath_budget.py --no-cov -n0 -s`.

**Method.** One authenticated socket; one subscription yielding `FRAMES = 50` values with no gating
of its own, so the measured work is `1` admission + `50` information-bearing frames. Wall clock
(`time.perf_counter`) from sending the subscribe frame to receiving the 50th `next`, **median of 9
iterations**, min and max recorded. The "before" arm is not a reverted tree — it is upstream's own
consumer mounted through the shipped injection seam
(`_router(schema, websocket_consumer_class=GraphQLWSConsumer)`), which has neither checkpoint, so the
same harness measures both sides and no `git` state is touched. Three arms:

- **A** upstream `GraphQLWSConsumer` — no gate, no lock, no read;
- **B** package consumer, `websocket_revalidation_window = 0.0` — gate + lock + one session read per
  frame;
- **C** package consumer, `websocket_revalidation_window = 3600.0` — gate + lock, **read reused**.

Environment: Python 3.14.2, Django 6.0.5, in-memory SQLite session store (`db` session engine),
single-threaded (`-n0`), Apple Silicon.

### 3.1 One operation, 50 information-bearing frames (median of 9)

| Arm | median total | per frame | min | max | delta vs A (per frame) |
| --- | --- | --- | --- | --- | --- |
| A upstream consumer (no gate) | 4.377 ms | 0.0875 ms | 4.233 | 5.991 | — |
| B package, window 0.0 | 22.511 ms | 0.4502 ms | 21.507 | 34.782 | **+0.3627 ms** |
| C package, window 3600.0 | 5.106 ms | 0.1021 ms | 4.670 | 5.939 | **+0.0146 ms** |

### 3.2 Two concurrent operations on ONE socket, 100 frames total (median of 9)

| Arm | median total | per frame | delta vs A (per frame) |
| --- | --- | --- | --- |
| A upstream consumer (no gate) | 7.372 ms | 0.0737 ms | — |
| B package, window 0.0 | 43.036 ms | 0.4304 ms | **+0.3566 ms** |
| C package, window 3600.0 | 7.511 ms | 0.0751 ms | **+0.0014 ms** |

### 3.3 The second, harness-independent statement of the same cost

Session reads for `1` admission + `50` frames, counted at `consumers.py::_refreshed_actor`:

| Arm | reads |
| --- | --- |
| B package, window 0.0 | **51** |
| C package, window 3600.0 | **1** |

### 3.4 What the numbers say, stated without judging the trade

Judging acceptability is the maintainer's call and I take no position. Four facts the numbers
establish, which are what the maintainer needs:

1. **The lock is not the cost; the read inside it is.** Arm C takes the lock on every frame and
   performs one read for the whole socket: **+0.015 ms per frame**, ~17% over a bare frame. Arm B
   differs from C only by performing the read, and costs **+0.363 ms per frame** — 96% of the added
   cost is the session read, ~4% is the serialization point itself.
2. **Two concurrent operations do not compound.** 100 frames across two simultaneous operations cost
   0.430 ms/frame against 0.450 ms/frame for 50 frames on one operation — the per-frame cost is flat,
   so the second operation pays its own reads and **no additional serialization penalty**. The
   head-of-line behavior is real (arm B's max, 104.9 ms, is a tail where one read parks the socket)
   but it does not scale super-linearly with concurrency on one socket.
3. **The window is the price control, and it works as documented.** Turning it on removes 50 of 51
   reads and 96% of the added cost.
4. **This measurement is a floor, not a ceiling, and the direction is knowable.** The session store
   here is in-memory SQLite. A Redis- or database-backed store on a real deployment makes the read
   the dominant term by a wider margin, so arm B's `+0.363 ms/frame` is the most favourable number
   this cost will ever show. That does not change any conclusion above — it strengthens (1) and (3).

**No design change was made to improve any of these numbers**, per the brief.

## 4. Failability proofs

Same procedure as the host cohort's pass-2 report §2: pristine copy taken **before** any mutation,
exact-string mutation applied from that copy, focused suite run, restore by copying the pristine file
back, restore proved by `cmp` (rc=0, no output). One boundary at a time. **No `git` write command was
run**, and no revert was verified by an "empty `git diff`".

Counts against `uv run pytest tests/test_routers.py --no-cov` (122 rows).

| Boundary (symbol-qualified) | Mutation applied | Rows failed | Was | Revert |
| --- | --- | --- | --- | --- |
| `consumers.py::send_revalidated_operation_frame` #"if task is not consumer.run_task:" | the whole guard removed: `task = asyncio.current_task()` / `if ...` / `task.cancel()` replaced by `asyncio.current_task().cancel()` (the review's own mutation) | **2** (`..._subscription_limit_error_frame_is_gated_from_the_connections_own_task[graphql-transport-ws]`, `[graphql-ws]`) | **0** | `cmp` rc=0 |
| `consumers.py::_actor_is_current` #"refreshed = None" (the fail-closed degrade) | `refreshed = actor` — fail OPEN onto the connection's cached actor | **2** (`..._revalidation_store_failure_denies_the_operation_and_is_logged`, `..._failing_auth_backend_load_also_fails_closed`) | 1 | `cmp` rc=0 |

### 4.1 The guard's DIRECTION is observable after all — the review's secondary ruling is wrong

The review's Q2 records that "a row on that path pins the *path*, not the guard's *direction*",
because mutant `no-runtask-guard` passed all 104 rows and its own probe: `channels.testing`'s app
future absorbs the self-cancellation of `run_task`. That is true of the **wire**, and true of the
review's probe, but it is not true of the harness.

The connection's task is reachable and its final state is inspectable:
`consumer.run_task` is a plain `asyncio.Task` on the consumer instance, `gate.consumers[0]` already
hands the row that consumer, and the communicator's `disconnect()` drives
`GraphQLWSConsumer.disconnect` -> `await self.run_task` to completion. So the row asserts

```python
assert consumer.run_task.done()
assert not consumer.run_task.cancelled()
```

and under the mutant that second assertion fails with
`<Task cancelled name='Task-1037' coro=<AsyncBaseHTTPView.run() ...>>`. The guard's direction — that
the connection's own message-loop task is left to unwind normally rather than cancelled out from
under the disconnect/shutdown path that must cancel and await 100 remaining operations — is therefore
pinned, on both protocols, not merely documented.

This is the "assert the invariant at the production call site rather than at the wire" rule applied
one step further out: the invariant is about a production **object's** final state, and that object
is reachable. I have recorded it here rather than silently, because the review's ruling would
otherwise stand as the reason a future reader believes the direction cannot be tested.

### 4.2 L3: why I took the documentation option

The review offered two remedies for `sends_under_lock`: (a) a sibling-cannot-enter assertion on the
same row, or (b) an explicit docstring line naming the limit. I took **(b)**, and the reason is that
(a) is not available on the row that reads it.

`test_a_valid_session_keeps_a_running_subscription_emitting_every_result` runs **one** operation —
there is no sibling to exclude, which is precisely why `locked()` discriminates there. Manufacturing
a sibling would turn the control row into a second copy of the sibling row (Test 39) and would
reintroduce the very ambiguity the review names: with a contender present, `locked()` can be
satisfied by the contender holding it. And `asyncio.Lock` exposes no holder, so "held by THIS task"
has no observable in the standard library short of wrapping the lock in production, which would be
adding machinery to production code to make a test assertion easier.

So `_record_outbound_gate`'s docstring now states the limit, why the rows that read it
discriminate anyway (single operation; the blast-radius row's second socket holds a *different* lock,
asserted by identity), and — the part that matters for the next reader — **what a future contended
row would have to add** instead of relying on `locked()`: the sibling's exclusion, via recorded gate
entry plus zero reads of its own, the way Test 39 does it. The recorded mutation count for lock
placement is unchanged at 4 rows, which passes the weakly-pinned rule on rows while resting on one
assertion class; that is now written down rather than latent.

### 4.3 Changes that are NOT boundaries

- `consumers.py::_actor_is_current` #"window = consumer.revalidation_window" (L4) — the removal of an
  unreachable `getattr` default. There is no new boundary to mutate; the mutation that would matter
  (dropping the attribute assignment in `__init__`) now raises `AttributeError` loudly instead of
  silently switching the deployment to "revalidate at every checkpoint", which was the entire point
  of the finding. Every window row still passes, which is what proves the default was unreachable.
- `tests/test_routers.py::_RevalidationProbe.invalidate_after` and `_OutboundGateProbe.frame_types` /
  `.from_run_task` — test instrumentation.

## 5. Implementation notes

- **`invalidate_after` on the existing probe, not a new fixture.** The limit row needs a revocation
  that lands between two checkpoints *inside one upstream call* (`handle_subscribe` performs the
  admission and then sends the limit frame), which no out-of-band mutator can interleave with. Rather
  than a second instrument, `_instrument_revalidation` grew one attribute: read `N + 1` and later
  answer `AnonymousUser` without touching the database. Its docstring states when to reach for it and
  when the out-of-band mutators remain the right tool, because the counting form is the weaker
  fixture and should not spread.
- **`_UPSTREAM_SUBSCRIPTION_LIMIT = 100` is a RE-TYPED literal**, matching this module's discipline
  for every upstream floor it depends on. If upstream changes the default, the row stops reaching the
  limit frame and says so (the `gate.frame_types == ["error"]` assertion fails) instead of silently
  pinning nothing. The limit is deliberately not lowered: the router exposes no knob for it, so a
  configured stand-in would be testing a path the deployment cannot produce.
- **Both protocols, not one.** The legacy `handle_start` has its own limit branch and its own
  `ErrorMessage` shape, and the guard is in shared code — one protocol would have left the other's
  path unexercised for 0.09 s of call time.
- **The second fail-closed row patches `channels.auth.get_user`, not a package seam.**
  `_refreshed_actor` imports that name per call, so patching the attribute on `channels.auth` is what
  the production code resolves — the row injects a failure into the third-party call the production
  code makes, rather than into a package-owned indirection. That is what makes it a genuinely
  independent second injection point rather than a second spelling of the first.

## 6. Notes for Worker 3

- The limit rows open 100 real subscriptions each and are cheaper than they look: **0.12 s** and
  **0.09 s** of call time (`--durations`, `-n0`), against the review probe's 1.62 s wall clock, because
  the 100 admissions are pipelined and the controlled subscriptions never produce a result. They are
  bounded by `_wait_until` / `_reached`, not by sleeps. If either ever *hangs* rather than fails, the
  cause is upstream's limit default having changed - check `GraphQLWSConsumer.__init__` before
  anything else.
- `test_a_failing_auth_backend_load_also_fails_closed` patches `channels.auth.get_user` **after** a
  successful operation, deliberately: the socket must already be authenticated and warm, so the
  failure is a degrade rather than a connect-time refusal.
- The M5 instrument is a gitignored scratch file and is NOT part of the permanent suite. It is not a
  timing assertion and must not become one — it prints numbers and asserts nothing about them.
- I did not re-run the four pass-1 mutants (the adapter class, the two admission hooks, the lock
  placement, the lock removal); the review re-ran all four independently and its counts stand.

## Required spec amendments (pass 2)

Pass 1's A1-A8 still stand and are not restated. I edited no spec.

**A9 — the spec's test plan must NOT inherit pass 1's "cannot be reached through the router" claim,
and the reachable path deserves its own row.** (Review M2 and its note 2 to Worker 1.)

- Where it lives: `## Test plan`, the Decision 16 block (the outbound-checkpoint rows, 34-43).
- Current wording: there is no row for this path, and the only prose describing it is pass 1 §6 of
  this artifact — quoted verbatim in §2 above — which is factually wrong about upstream and must not
  be lifted into spec prose.
- Recommended replacement — add a row:
  > "43b. The outbound checkpoint reached from the connection's OWN task. Upstream defaults
  > `max_subscriptions_per_connection` to **100**, not `None`
  > (`strawberry/channels/handlers/ws_handler.py::GraphQLWSConsumer.__init__`), so both protocols'
  > subscription-limit `error` frame is a reachable production path through the shipped router with no
  > knob and no injected consumer: 100 in-flight operations plus one more. With the revalidation
  > invalidating on the read that 101st operation's OUTBOUND checkpoint takes, assert that the limit
  > frame never reaches the wire, that the socket closes `4403` / `\"Forbidden\"`, that the checkpoint
  > was entered from `consumer.run_task`, and - the guard's direction - that `consumer.run_task`
  > completed WITHOUT being cancelled. One row per protocol. The direction is observable through the
  > task object even though it is invisible on the wire, because `channels.testing`'s app future
  > absorbs a self-cancelled `run_task`."
- Why: the guard is a security path whose only recorded justification for having no test was a false
  premise about a dependency's default. A spec row is what stops the premise being re-derived.

**A10 — Decision 16's hot-path cost should carry the measured number, not only the qualitative
statement.** (Review M5.)

- Where it lives: `## Decision 16`, the connection-local-lock paragraph.
- Current wording, `docs/spec-046-transport_security-0_0_15.md:2166` region:
  > "a per-connection serialization point on the outbound hot path"
- Recommended replacement:
  > "a per-connection serialization point on the outbound hot path. Measured, so the trade is priced
  > rather than asserted: against upstream's own consumer over the same harness, 50
  > information-bearing frames on one authenticated socket (median of 9, in-memory SQLite session
  > store) cost **+0.363 ms per frame** at `websocket_revalidation_window = 0.0` and **+0.015 ms per
  > frame** at a positive window - so ~96% of the added cost is the session READ and ~4% is the lock
  > itself, and the window is the control for it (51 reads become 1). Two concurrent operations on one
  > socket cost the same per frame as one (0.430 vs 0.450 ms), so the second operation pays its own
  > reads and no additional serialization penalty. The in-memory store makes these the most
  > favourable numbers the cost will show; a Redis- or database-backed session store widens the read
  > term and does not change the shape."
- Why: `BUILD.md` `## Hot-path budget` requires the number to sit next to the change that caused it
  and reach the maintainer. The spec is the durable half of "next to".

**A11 — Decision 11's `revalidation_window` read should be documented as a plain attribute, because
the defensive spelling was a silent performance cliff.** (Review L4.)

- Where it lives: `## Decision 11`, the window-resolution paragraph.
- Current wording: the decision describes `websocket_revalidation_window` as an `as_asgi()` initkwarg
  and does not say how the checkpoint reads it.
- Recommended replacement — append:
  > "The checkpoint reads it as a plain attribute (`consumer.revalidation_window`), never through a
  > `getattr` default. The consumer's `__init__` assigns it before `super().__init__`, and the class is
  > function-local to the factory, so no third party can construct one without it - a default would be
  > unreachable, and if a future refactor did drop the assignment the default would silently switch the
  > deployment to \"revalidate at every checkpoint\" (a performance cliff living in an expression, which
  > `fail_under = 100` cannot see) instead of failing loudly."
- Why: the shipped `getattr` was a fail-*safe* default on the one line that decides whether a session
  read happens. Recording the rule in the decision is what stops it being reintroduced as
  defensiveness.

## 7. The remaining single-row boundaries in this cohort: reasoned dispositions

The review's weakly-pinned census lists three further single-row boundaries in `consumers.py` and
grades each "acceptable on merit". I re-checked each against the diff rather than accepting the grade,
and **agree with all three** — with one clarification the review did not make.

| Boundary | Sole pinning row | Disposition |
| --- | --- | --- |
| `consumers.py::_actor_is_current` #"scope[\"user\"] = refreshed" (the write-back) | `..._valid_session_keeps_executing_and_the_next_operation_sees_the_refreshed_actor` | **Accept.** One contract, and the row's freshness probe (`Query.actor_identity`) reads TWO independent identity fields off whatever `scope["user"]` holds, so the single row carries two discriminators. A second row would have to change the same two fields a second way. |
| `consumers.py::revalidate_operation_actor` #"if not handler.connection_acknowledged:" | `..._subscribe_before_connection_init_is_closed_by_upstream_without_revalidating` | **Accept.** It is the only row that can exist: the contract is "a pre-init client sees UPSTREAM's `4401`", and there is exactly one pre-init state. A second row would be the same handshake with a different query string. |
| `consumers.py::send_revalidated_operation_frame` #"if not consumer._revocation_observed" (the outbound short-circuit) | `..._connection_lock_stops_a_sibling_payload_escaping_after_revocation`, via `probe.reads == 3` | **Accept, and the review's reasoning is exactly right**: dropping it changes the read COUNT and never the verdict, because `_actor_is_current` would independently fail. It is a read-storm guard, not a bound, so a second row would be pinning the same count twice. |

The clarification: the same census lists `consumers.py::_actor_is_current`'s fail-closed degrade as
"needs a second row" — that one I did build ([§1](#1-findings-closed-in-this-pass)), because unlike
the three above its property genuinely has more than one shape (a store failure and a backend
failure), and only one of them was known to the suite.
