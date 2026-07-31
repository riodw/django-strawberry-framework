# Adversarial review: spec-046 transport security

This pass reviewed [spec-046][spec-046] from a cross-feature angle: the default
revalidating WebSocket consumer composed with the package's own authentication
mutations, rather than revalidation exercised only through an external HTTP
logout. The isolated external-revocation path is well covered. The combined
same-connection path is not, and it breaks the connection-scoped revocation
invariant in two ways.

## Findings

### [P1] Same-socket logout turns off revalidation for already-running authenticated operations

`django_strawberry_framework/auth/mutations.py::_channels_logout` delegates to
Channels' logout, which flushes the durable session and replaces
`scope["user"]` with `AnonymousUser`. The next protected frame reaches
`django_strawberry_framework/consumers.py::_actor_is_current`, whose first
decision is:

```python
actor = scope.get("user")
if actor is None or not actor.is_authenticated:
    return True
```

That carve-out is correct only for a connection that was anonymous before it
admitted work. It is not correct after an authenticated connection changes
identity. A deterministic exploit is:

1. open an authenticated socket and admit a long-running subscription;
2. execute the package's `logout` mutation on the same socket;
3. let logout flush the session and replace the scope actor with
   `AnonymousUser`;
4. release another result from the already-authorized subscription.

The outbound gate now classifies the connection as an anonymous socket, performs
no session read, and sends the old subscription's `next` / `data` frame. This is
the exact state the spec says must never occur: a revoked session has quietly
become an anonymous actor that keeps executing. A subscription may also have
captured its authenticated principal or completed its visibility/permission
checks at admission, so reading the now-anonymous scope later does not make its
result anonymous-safe.

The test split hides the composition bug.
`tests/auth/test_mutations.py::test_websocket_server_side_logout_invalidates_and_survives_reconnect`
proves that same-socket logout makes a later `me` query anonymous, but it has no
operation admitted before logout.
`tests/test_routers.py::test_a_running_subscription_cannot_emit_a_result_after_revocation`
does have a running operation, but revokes through a second HTTP request; that
leaves the socket's cached actor authenticated, so `_actor_is_current` takes the
database-read branch and closes correctly. Neither row exercises both halves
together.

The root fix is to stop using the mutable current actor as proof that the
connection has always been anonymous. Track immutable connection authentication
provenance or an actor generation, and make an authenticated-to-anonymous
transition a connection-scoped revocation event. If the public contract must
keep the socket open after logout, the consumer must atomically cancel and await
every pre-logout operation before admitting anonymous work; otherwise, close the
socket after the logout transition. In either design, the logout response
semantics must be explicit rather than obtained by letting the anonymous
carve-out authorize every pending frame.

Add communicator regressions for both WebSocket protocols: start a controlled
authenticated subscription, receive one result, run the package logout mutation
on that socket, release the next result, and prove that the old result is
suppressed and the operation generator is finalized. A control should then pin
whichever post-logout socket behavior the chosen transition contract promises.

### [P1] Revalidation and logout use disjoint locks, so a stale read can resurrect the logged-out actor

The same integration has a separate race.
`django_strawberry_framework/consumers.py::revalidate_operation_actor` and
`django_strawberry_framework/consumers.py::send_revalidated_operation_frame`
serialize through the consumer's `_revocation_lock`.
`django_strawberry_framework/auth/mutations.py::_channels_logout` serializes
through `django_strawberry_framework/auth/sessions.py::scope_session_lock`.
Neither lock participates in the other state machine.

The lock held through `send` is therefore atomic only against another
revalidation checkpoint, not against the revocation operation itself. Logout
can flush the session while a frame that already passed `_actor_is_current` is
still inside `_revocation_lock`, and that frame can then be sent after logout
has completed.

The asynchronous refresh also permits a stronger stale-write ordering:

1. `_actor_is_current` observes the authenticated scope actor and starts
   `_refreshed_actor`;
2. the session/user read obtains the still-valid actor;
3. same-socket logout flushes the session and writes `AnonymousUser` to the
   scope;
4. the suspended revalidation resumes, unconditionally writes its stale actor
   back to `scope["user"]`, records a fresh window timestamp when configured,
   and authorizes the pending frame.

The connection is therefore re-authenticated in memory after durable logout and
can emit a protected frame after revocation. With a positive revalidation
window, the stale write also refreshes the cache timestamp, allowing subsequent
checkpoints to reuse the resurrected actor until the window expires.

The root fix is one actor-state synchronization contract shared by session
mutation and revalidation, not another local lock. A connection-owned actor
generation is one viable shape: capture the generation before the asynchronous
session read, increment it during logout under the shared state lock, and refuse
to commit the refreshed actor or timestamp when the generation changed. The
validate/commit/send sequence and the logout transition must have a documented
lock order so neither a stale write-back nor a pre-transition payload can cross
the boundary.

Add a deterministic race test that pauses revalidation after it has obtained the
old actor, completes same-socket logout, then resumes revalidation. The assertions
must prove that the old actor is not written back, the pending frame is not sent,
the connection takes the chosen revocation transition, and a positive window is
not refreshed from the stale read.

## Non-findings from this review angle

- External logout, session deletion, user disabling, and password rotation are
  correctly detected while the scope still carries its authenticated actor.
  The defect is the package-owned mutation of that scope and its missing
  synchronization with the revalidation state machine.
- Allowing a socket that was anonymous from its initial authenticated-middleware
  state to avoid session reads is still a valid performance carve-out. The fix
  needs provenance, not unconditional database reads for genuinely anonymous
  connections.

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
