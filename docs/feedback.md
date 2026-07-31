# Adversarial review: spec-046 transport security

This pass reviewed [spec-046][spec-046] from a cancellation and task-lifecycle
angle: whether revocation deterministically stops an operation, whether the
documented connection close survives cancellation and adapter failure, and whether
the new actor lease remains sound when either side of an `await` does not complete
normally. The lease fixes the previously reported same-connection logout
orderings, but the teardown built on top of it is not failure-atomic.

## Findings

### [P1] Self-cancellation does not stop a subscription whose next result is immediately ready

`django_strawberry_framework/consumers.py::send_revalidated_operation_frame`
tries to unwind a revoked operation by calling `asyncio.current_task().cancel()`
immediately before it returns. The function's commentary assumes that the
`CancelledError` will be delivered at the subscription's next suspension point,
inside `result_source.__anext__()`. That assumption is false for an async generator
whose next value is already available: executing an `await` does not necessarily
return control to the event loop.

After the first revocation, the whole suppressed-frame path can complete
synchronously from the task's perspective:

1. the connection's actor lease is uncontended, so `asyncio.Lock.acquire()`
   returns without suspending;
2. `_revocation_observed` short-circuits before `_actor_is_current` performs a
   session read;
3. `::_revoke_connection` returns immediately because the flag is already set;
4. the helper requests cancellation again and returns to upstream's `async for`;
5. an immediate-yield async generator supplies another result without yielding to
   the event loop, and the cycle repeats.

A direct harness around the production helper processed 100,000 suppressed
`next` frames without one cancellation being delivered and left the current task
with 100,000 pending cancellation requests. The frames remain suppressed, so this
is not an authorization disclosure. It is still a process-level availability
failure at the security boundary: a buffered or otherwise immediate-yield
subscription can monopolize the event loop precisely when revocation is supposed
to unwind it, its generator cleanup is not deterministic, and the documented
disconnect path never gets a chance to cancel the connection's other operations.
The existing controlled subscription always waits on an event between yields, so
its next `__anext__()` genuinely suspends and hides this case.

The root fix is to make operation termination part of an owned lifecycle protocol,
not a request set on the task that happens to be running the adapter. The package
needs a seam that can stop the upstream result loop and explicitly close/await its
result source even when every subsequent value is immediately ready. Merely adding
`await asyncio.sleep(0)` after `task.cancel()` is not the root fix: it injects
`CancelledError` inside the `async for` body, the exact location the current
commentary correctly says does not synchronously close the generator. Likewise,
repeating `task.cancel()` cannot force a task to yield.

Add a regression on both protocols with an async generator that yields a bounded
but large sequence without awaiting between yields. Revoke on its first outbound
checkpoint and assert that only a small, deterministic number of results are
pulled, the generator's `finally` runs before teardown completes, the operation
task finishes, sibling operations are cancelled and awaited, and the event loop
remains responsive to an independently scheduled sentinel task.

### [P2] A failed or cancelled close is permanently recorded as a completed close

`django_strawberry_framework/consumers.py::_revoke_connection` sets
`consumer._revocation_observed = True` before awaiting `websocket.close(...)`.
That ordering publishes the authorization decision promptly, but the same boolean
is also used as proof that the transport close was already sent. If the adapter's
close raises or the operation task is cancelled while the close is suspended, the
flag remains true and every later checkpoint returns without another close attempt.

The failure is directly reproducible against the production helper: an adapter
whose first `close` raises `OSError` leaves `_revocation_observed` true, and a
second call to `_revoke_connection` returns normally with the close-call count
still equal to one. Cancellation is the more adversarial real-protocol shape. Both
upstream protocols let a client cancel its operation with `complete` / `stop`; if
that cancellation lands while the revocation close is back-pressured, the operation
unwinds through `CancelledError`, no `4403` is committed, and the connection's
message loop remains alive with a latch that forbids any retry.

Information-bearing frames remain fail-closed because later checkpoints see the
flag. The observable connection contract does not: the promised non-disclosing
`4403` close can disappear, retained operations and connection state may remain
allocated, and control frames can continue on a socket the package claims it
terminated. Treating "revocation was decided", "a close is in progress", and "the
close completed" as one bit is the root cause.

The root fix is a connection-owned revocation/close state machine. Publish the
revoked state immediately so no later authorization can pass, but represent the
single shared close attempt separately and shield its ownership from cancellation
of whichever operation first observed revocation. Concurrent and later
checkpoints should await that same completion; an adapter failure needs an explicit
retry or connection-loop escalation policy rather than being mistaken for success.
The design must also handle the ambiguous case where an ASGI send commits and its
awaiter is then cancelled, so simply moving the boolean assignment after the
`await` is not sufficient.

Add deterministic regressions for both protocols. Park the adapter close, cancel
the detecting operation through the protocol's own `complete` / `stop` message,
then prove the shared close still commits exactly one `4403` and the connection
teardown finishes. Pair that with an adapter that raises on its first close and
succeeds on the next permitted attempt, proving a later checkpoint cannot silently
inherit a false "already closed" result.

## Non-findings from this review angle

- The shared actor lease now covers positive-window cache hits, session reads,
  write-back, protected sends, and the package-owned logout transition. The two
  logout orderings from the preceding review no longer reproduce.
- The bounded HTTP read now converts ordinary foreign-stream read, sizing, close,
  and replacement failures into the documented fail-closed body-limit response.
- Neither lifecycle finding lets another information-bearing frame reach the
  client after revocation. They concern deterministic task and connection teardown,
  not a restatement of the fixed authorization race.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[spec-046]: spec-046-transport_security-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
