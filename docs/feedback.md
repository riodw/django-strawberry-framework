# Adversarial review: spec-046 transport security

This pass reviewed [spec-046][spec-046] from a hostile-boundary angle: whether the
new connection actor state linearizes every protected WebSocket send with an
in-process identity transition, and whether failures of the foreign request stream
remain inside the HTTP boundary's controlled error contract. The stale actor
write-back and authenticated-to-anonymous provenance defects from the previous pass
are fixed, but the transition state still does not cover two other orderings.

## Findings

### [P1] A fresh revalidation window bypasses an actor transition already in progress

`django_strawberry_framework/consumers.py::_actor_is_current` consults the positive
revalidation-window cache before it captures or validates an actor-state token:

```python
if window > 0.0 and _monotonic() - scope.get(_REVALIDATED_AT_SCOPE_KEY, -math.inf) < window:
    return True

token = actor_read_token(scope)
```

Consequently, `utils/sessions.py::actor_transition` may already report
`transitions_in_flight == 1` and the checkpoint still returns `True`. The condition
is directly reproducible with an authenticated actor, a fresh
`_REVALIDATED_AT_SCOPE_KEY`, and `_actor_is_current` called inside
`actor_transition`: the checkpoint authorizes without reading or checking the
transition state.

A real same-socket ordering is:

1. an authenticated operation successfully revalidates and records a positive
   window timestamp;
2. the package's `logout` mutation enters `actor_transition` and suspends inside
   Channels' thread-backed logout, before Channels replaces `scope["user"]` with
   `AnonymousUser`;
3. a sibling operation reaches admission, or a running subscription reaches its
   outbound gate, while the cached scope actor is still authenticated;
4. the fresh-window branch returns `True` despite the published transition, so the
   operation is admitted or its protected frame is sent.

The configured window intentionally delays detection of an *external* session
revocation. It must not erase the package-owned transition's stronger contract:
the code and tests now promise that same-connection logout is a connection-scoped
revocation and that the next protected checkpoint refuses it. The current tests
miss the combination. The same-socket subscription row uses the default zero
window, while the stale-read row advances time beyond its positive window before
starting logout, forcing the token-bearing database-read branch.

The root fix is for every authorization path, including a cache hit, to participate
in the connection actor-state protocol. Checking only
`transitions_in_flight` at the top is not sufficient on its own, because a
transition can begin immediately after that check; the transition and the complete
validate/send critical section need the shared exclusion described in the next
finding. Once that exists, the window shortcut may run only while holding the same
stable actor-state lease as an uncached validation.

Add deterministic admission and outbound regressions with a positive window. Park
same-socket logout after it opens `actor_transition` but before it changes the scope
actor, then attempt a new operation and release a running subscription result. Both
checkpoints must wait for or refuse the transition, perform no cached authorization,
and end in the documented connection close.

### [P1] A protected send can complete after logout because transitions do not share its lock

`django_strawberry_framework/consumers.py::send_revalidated_operation_frame`
holds `_revocation_lock` through `await send(message)`, but
`django_strawberry_framework/auth/mutations.py::_channels_logout` never acquires
that lock. It holds `scope_session_lock` and publishes `actor_transition`, while
the outbound path merely samples actor state before entering `send`. The new read
token therefore prevents a transition that overlaps the asynchronous *session
read* from committing stale data, but it cannot detect a transition that starts
after `_actor_is_current` returns.

The remaining ordering is deterministic:

1. an outbound checkpoint validates the authenticated actor and calls the
   adapter's underlying asynchronous send;
2. that send suspends before committing the frame to the ASGI channel;
3. same-socket logout runs under its independent lock, flushes the durable session,
   replaces the scope actor, closes `actor_transition`, and returns;
4. the send resumes and emits the already-authorized protected frame after logout
   completed.

This is not hypothetical behavior hidden behind an artificial await. ASGI sends
are asynchronous, and the existing test helper's own commentary acknowledges that
a real socket write can suspend. A direct delayed-send harness against the
production helper emits the `next` frame after a completed actor transition. Holding
`_revocation_lock` through the send only excludes sibling checkpoints; it provides
no ordering at all against the logout transition.

The root fix is one shared, connection-owned synchronization primitive or lease
that linearizes actor transitions against the entire validate/commit/send sequence.
Logout must not complete while a pre-transition protected send is still pending,
and no checkpoint may begin sending while logout owns the transition. A generation
check after `send` is too late because bytes may already be committed. The lock
order must remain explicit with `scope_session_lock`; replacing or integrating the
revocation lock is preferable to adding a third independent lock.

Add a deterministic regression that parks the real outbound delegate before it
writes. Start same-socket logout while the send is parked and prove logout cannot
complete across it; after releasing the pre-transition send, let logout linearize,
then prove every later protected frame is suppressed and the operation is finalized.
Pair it with the transition-first positive-window test above, which proves the
opposite ordering cannot enter the send at all.

### [P2] A request-stream read failure escapes the bounded body gate as a 500

`django_strawberry_framework/_request_body.py::_measured_remaining` guards every
capability probe, but the fallback it selects does not provide the same error
boundary. `::_bounded_read_exceeds_limit` calls `request.read(...)` without
handling its failure. Django converts an underlying stream `OSError` into
`django.http.request.UnreadablePostError`; that exception propagates through
`views.py::_RequestBodyBoundaryMixin._enforce_request_body_limit`, and Strawberry's
Django dispatch catches only `cross_web.HTTPException`.

The result is reproducible with an otherwise ordinary POST whose declared length is
below the package cap and whose non-seekable WSGI input raises `OSError` from
`read()`: invoking `DjangoGraphQLView` raises `UnreadablePostError` instead of
returning a controlled client response. Under Django's handler this becomes a `500`
and error log. The body is not executed, so this is not a cap bypass, but a broken or
aborted client stream can turn the security boundary into an avoidable server-error
and logging path. It also contradicts `_request_body.py`'s module contract that a
foreign stream failure is reported in the fail-closed direction rather than escaping
as an unrelated `500`.

The root fix is to make the bounded-read phase as total as the capability probe.
Failures while reading, measuring returned chunks, closing the consumed stream, or
installing the replacement stream need an explicit fail-closed outcome that the view
maps to one controlled response, with an operator-side record if the wire response is
deliberately indistinguishable from an ordinary size rejection. Do not catch
`BaseException`; cancellation and process-control exceptions must still propagate.

Add sync and async view regressions backed by a non-seekable input whose `read`
raises after zero bytes and after a partial prefix. Assert the selected controlled
status and reason, no schema execution, no unbounded retry, and no partial body handed
to Strawberry.

## Non-findings from this review angle

- The new provenance latch correctly prevents an authenticated socket changed to
  `AnonymousUser` from taking the genuinely-anonymous read-free carve-out.
- The generation token correctly refuses a stale actor loaded before a completed
  same-socket logout, and it does not refresh the positive-window timestamp from
  that stale read. The two P1 findings are orderings outside that token's present
  lifetime, not restatements of the fixed stale-write defect.
- Host projection, strict JSON UTF-8 decoding, multipart control-field loss
  detection, and the exact built-in numeric configuration gates remained
  fail-closed under the hostile inputs reviewed in this pass.

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
