"""The WebSocket Host boundary, the GraphQL consumer, and its two revalidation checkpoints.

This is the package's WebSocket-transport module, and it owns two independent
things: the handshake-time **Host** boundary
(``DjangoWebSocketHostValidator``, spec-046 Decision 19) and the package's
**consumer** with its two actor-revalidation checkpoints (Decisions 11 and 16).
The consumer is described first; the Host boundary's own section is at the end of
this docstring.

``build_revalidating_consumer_class(GraphQLWSConsumer)`` returns
``GraphQLWebSocketConsumer`` - a thin ``strawberry.channels.GraphQLWSConsumer``
subclass that revalidates the session actor at **two** security checkpoints and
writes the refreshed actor back onto ``scope["user"]`` (spec-046 Decision 11):

1. **operation admission** - the two protocol handlers' per-operation entry
   points (``handle_subscribe`` for ``graphql-transport-ws``, ``handle_start``
   for legacy ``graphql-ws``), which decide whether a NEW operation may start;
2. **the outbound information-bearing frame** - the protocol-neutral
   ``websocket_adapter_class`` seam, which decides whether an ALREADY-ADMITTED
   operation may still put ``next`` / ``data`` / an operation-scoped ``error``
   on the wire.

The second checkpoint is what makes the contract true for a **running**
subscription. Admission alone can never see one again: both protocols park an
admitted operation in their own ``async for result in result_source`` loop
(upstream's ``run_operation`` / ``handle_async_results``) and keep sending from
there without returning through the admission method, so an operation admitted
one second before a logout kept emitting results for as long as it lived.

**The seam, and why it is the right one.** ``AsyncBaseHTTPView.run`` instantiates
``self.websocket_adapter_class(self, request, websocket_response)`` **by name**
off the class attribute, and every frame both protocols emit funnels through that
instance's ``send_json`` (``Operation.send_next`` -> ``handler.send_message`` on
graphql-transport-ws, ``send_data_message`` -> ``handler.send_message`` on legacy
graphql-ws, and both protocols' operation-scoped errors on the same path). It is a
designed class-level extension seam, so the factory derives ONE private adapter
from the base consumer's own attribute and installs it on the generated consumer
exactly as it already installs the two handler classes - never a per-instance
patch, and never an import of upstream's adapter module.

**What is gated, and what is deliberately not.** ``next``, ``data``, and
operation-scoped ``error`` frames. Runtime resolver errors normally ride inside
``next`` / ``data``, but pre-execution and other operation errors travel as
``error`` frames and can still disclose schema, validation, extension, or
consumer-authored information, so gating them avoids an unnecessary disclosure
distinction. ``complete``, ``connection_ack``, ``ping`` / ``pong``, the legacy
keep-alive ``ka``, and every other connection-control frame use upstream's own
payload and protocol semantics: they carry no operation information, and one of
them (``complete``) is what upstream emits at the end of every operation. Their
writes still pass through the adapter's revocation latch and shared actor lease,
so a control frame cannot overtake a concurrent revocation decision.

Delegation is not unconditional, though, and the condition is the connection's
own state rather than the frame's type: **once the revocation is DECIDED the
adapter writes nothing further to the socket at all**, delegated frames included.
Ending a revoked operation's result loop normally means upstream proceeds to its
own ``complete``, which would otherwise be delegated straight through and land
AFTER this module's ``4403`` - a control frame on a socket the package says it
terminated. The adapter's ``send_json`` carries the whole ruling, including why
the cut-off is the decision rather than the committed close. The information-bearing
path performs the actor validation; the delegated control path only uses the same
lease to serialize its state check with the asynchronous write.

**Revocation is connection-scoped.** The first failed validation - at either
checkpoint - atomically marks the connection revoked, suppresses the pending
frame, closes the whole socket with upstream's own ``4403`` / ``"Forbidden"``,
ends the revoked operation's own result loop through the stop-aware result source
described below, and lets upstream's existing disconnect / shutdown path cancel
and await every remaining registered operation.
No protocol-specific operation error is sent first, at EITHER checkpoint: the
actor is connection-scoped so the close IS the rejection, an error-then-close
sequence would only add protocol asymmetry and another race, and - decisively -
an admission-time error frame is itself one of the gated frame types, so it would
be validated against the same already-revoked actor, suppressed, and replaced by
this close anyway. Exempting that one frame from the gate to let it through would
be precisely the disclosure distinction the gated set exists to avoid.
``scope["user"]`` is never downgraded to anonymous - a revoked session must not
quietly become an anonymous one.

**How a revoked operation stops: the stop-aware result source.**
``_StopAwareSchema`` wraps the ONE object both protocol handlers reach an
operation's results through - their own ``self.schema`` - and is installed
per connection by the two handler subclasses the factory below already generates,
so a single mechanism serves both protocols. Its ``subscribe`` and ``stream`` both
delegate to the real schema and return ``_stop_aware_results``, a generator that
consults the connection's revocation state before pulling each value and simply
RETURNS once the connection is revoked. Upstream's ``async for result in
result_source`` loop therefore ends NORMALLY, at its own next iteration, and the
wrapper closes the inner source when it exposes the optional ``aclose`` hook - so
the subscription generator's ``finally`` runs deterministically, at the revocation,
rather than whenever the interpreter's asyncgen finalizer gets to it. Async
iterators without that hook remain valid on the legacy upstream path.

Termination is the mechanism, and cancellation is deliberately not: a revoked
operation must be stopped even when every subsequent value is already available.
``asyncio.Task.cancel()`` only requests cancellation, and the request is consumed
when the task is next rescheduled - which needs an await that actually yields to
the loop. The whole suppressed-frame path has none: an uncontended
``asyncio.Lock.acquire()`` does not suspend, the revoked short-circuit takes no
session read, a completed close returns immediately, and an immediate-yield
generator supplies the next value without suspending either. A cancel request
issued from there is never delivered, so the operation keeps producing values the
gate keeps suppressing, monopolizing the loop at exactly the moment revocation
should be unwinding it. Nothing is disclosed - the frames stay suppressed - but
the socket's teardown is starved, and on the legacy protocol
``cleanup_operation`` *awaits* the operation task, so the teardown deadlocks
outright. Neither an ``await asyncio.sleep(0)`` after the request nor a repeated
request fixes that: a cancellation delivered in the ``async for`` BODY unwinds
the body and leaves the generator suspended, which is the opposite of closing it.

**Two names, because the seam is one attribute read and the package supports a
RANGE of upstream releases.** The name a handler dispatches an operation's results
through is not stable across ``strawberry-graphql>=0.316.0``: the legacy
``graphql-ws`` handler reads ``schema.subscribe`` throughout, while the
``graphql-transport-ws`` handler read ``schema.subscribe`` (plus ``schema.execute``
for a query or mutation) up to and including 0.318.1 and reads ``schema.stream``
for EVERY operation from 0.319.0 on. Covering only one of the two names does not
degrade the wrapper - it removes it, silently and for one whole protocol, because
an uncovered name resolves through ``__getattr__`` straight to the real schema and
every frame it produces then reaches the wire unmasked and unstoppable. Both names
are therefore wrapped unconditionally, so an install anywhere in the supported
range gets the same seam on both protocols; the name a given release does not read
is simply never called. A version test would be the wrong shape here - it would
have to be revised on an upstream rename it cannot detect - and an upper bound in
``pyproject.toml`` would refuse the whole transport rather than serve it.

``stream`` is WIDER than ``subscribe``: it also runs queries and mutations, and it
yields their single result from INSIDE the extension lifecycle, so the wrapper
covers those operations on the newer releases and must. They are not free-riding
on a subscription mechanism - masking at the operation teardown has not run when
that result is yielded, exactly as it has not run for a subscription's events, so
the result source is the only seam their errors pass through as well. ``execute``,
the older releases' non-subscription path, still needs nothing and still gets
nothing: it returns one already-torn-down result and never loops, so it stays
upstream's own call through ``__getattr__``.

**The same result source is where the production error policy reaches a
subscription** (spec-048 Decision 11). A query's errors are masked by
``extensions/error_policy.py::DjangoErrorPolicyExtension`` at operation teardown,
which is the whole response for a single-result operation - but a subscription
delivers one ``ExecutionResult`` per EVENT and that teardown runs only when the
operation ends, so every event's raw exception message would already be on the
wire. ``_stop_aware_results`` therefore masks each result it yields, through the
extension module's own ``mask_execution_result``, which returns a masked COPY and
leaves the engine's result object holding its originals for the extensions that
read them. A query or mutation that arrives here over ``stream`` is masked by the
same pass and for the same reason (above); one that upstream ran through
``schema.execute`` needs nothing, because that call runs the extension teardown
before returning.

Masking is applied only to a value of execution-result SHAPE, gated on the
extension module's own ``is_maskable_result`` so the two seams cannot drift on the
question. ``stream``'s third element type is a raw graphql-core incremental-delivery
frame (``@defer`` / ``@stream``), which carries its errors nested inside incremental
payloads rather than on an ``errors`` attribute. Masking one would degrade it - the
policy fails closed on a result whose errors it cannot read - and the degraded value
IS an ``ExecutionResult``, which is precisely the test upstream's transport uses to
decide that a frame has no wire representation and the operation must be rejected. So
a frame this policy cannot mask passes through untouched and meets that rejection
instead of defeating it: nothing unmasked reaches the wire either way, because
upstream refuses to render the shape at all.

**The substitution is transparent by the only measure that matters.** ONLY the
handler's own ``self.schema`` is replaced, and only ever with the connection's
wrapper - ``AsyncBaseHTTPView.run`` reads the CONSUMER's ``self.schema``, passes
it to the handler as an ordinary keyword, and never sees the wrapper at all. Across
the supported range the two handler modules read exactly three attributes off the
schema they were handed - ``subscribe``, ``stream``, and ``execute`` - and perform
no ``isinstance`` or ``type`` test on it; ``subscribe`` and ``stream`` are the ones
the wrapper defines, ``execute`` and every other name resolve through
``__getattr__`` to the real schema by identity. The wrapper is therefore invisible
to execution itself: the real schema builds the execution context, so
``info.schema`` and every extension see the real object.

A FOURTH name would be a new seam this wrapper does not cover, and it would be
invisible: delegation keeps the protocol working, minus the masking and the stop. So
the read set is re-derived from the INSTALLED handler modules by
``tests/test_routers.py::test_the_stop_aware_schema_passes_every_upstream_schema_read_through``
rather than trusted, and that row is what turns the next upstream rename into a
failing test instead of a silently unwrapped protocol.

**The close is a state machine, not a flag** (``_ConnectionRevocation``). Three
facts have to stay separable - that revocation was DECIDED, that a close is IN
FLIGHT, and that a close COMPLETED - because one boolean standing for all three
records a close that raised, or one that was abandoned, as a close that was
committed, and then no later checkpoint ever tries again. Information-bearing
frames stay fail-closed either way, but the promised ``4403`` would silently
never reach the client, leaving it holding a socket this module has stopped
writing to and will never explain. The states and the transitions between them are on
``_ConnectionRevocation``; the two properties worth naming here are that the
DECIDED transition is published before any await (so every checkpoint refuses on
it read-free) and that the close attempt is a task the CONNECTION owns, so
cancelling whichever operation first observed the revocation - which both
protocols let a client do, with ``complete`` / ``stop`` - cannot abandon the
close. Ownership binds at both ends: the connection's ``disconnect`` settles that
task from a ``finally``, and settlement is its TERMINAL owner, so a cancelled or
failing teardown can neither skip it nor leave it running past the connection.

**A same-connection ``logout`` is a revocation event, and the socket ends.** The
package's own ``auth/mutations.py::logout_mutation`` mutation runs on the connection it is
sent over, and it both flushes the durable session and replaces ``scope["user"]``
with ``AnonymousUser``. That is an actor transition, not a downgrade to an
anonymous socket, so the connection's next protected checkpoint - which is
normally the ``logout`` payload's own ``next`` / ``data`` frame - refuses and the
socket closes with the same ``4403`` / ``"Forbidden"``. The pinned consequences,
stated because a client observes them: the ``logout`` mutation's own reply is
suppressed like every other post-revocation frame (the teardown has already
completed durably, so the close is the answer, and exempting that one frame would
be exactly the disclosure distinction the gated set exists to avoid), and every
operation admitted before the logout is cancelled and awaited by upstream's own
disconnect path rather than left emitting against an anonymous scope. A client
that wants to keep working after logging out opens a new socket, which is also
the only way it can present a different session.

Two properties make that true (see ``utils/sessions.py``'s connection-actor-lease
section for both, and for the order the two locks involved observe).
**Provenance**: the anonymous carve-out below is keyed on whether the connection
has EVER carried an authenticated actor, not on whether it carries one now, so an
authenticated -> anonymous change cannot buy the read-free path a genuinely
anonymous socket gets - which is also what makes the refusal after a logout cost
no session read at all. **The shared actor lease**: a transition and a
checkpoint's whole critical section are mutually exclusive, so a stale read cannot
be overtaken by a logout, a logout cannot complete underneath a protected send
that was authorized before it, and no checkpoint can authorize anything while a
transition owns the connection.

**One lease, held through the send, shared with the auth layer.** The connection's
actor lease (``utils/sessions.py::actor_lease``) spans the validation / cache
decision, the revoked-state transition, AND the actual information-bearing send.
Releasing it after validation would let one sibling task pass validation, another
detect revocation and begin closing, and the first then emit its previously
authorized payload - and, because an ASGI send is asynchronous, it would equally
let a same-connection ``logout`` run to completion inside the window between
"authorized" and "written". The lease is deliberately NOT private to this module
for exactly that second reason: a lock the auth layer cannot acquire gives no
ordering against the one revocation the package itself performs.

The cost is stated rather than hidden: this is a per-connection serialization
point on the outbound hot path, so when a validation needs a session-store read
every concurrent operation waiting to emit on that socket waits for that read,
and a same-connection ``logout`` waits behind an in-flight protected frame (as
that frame's successor waits behind the ``logout``). That head-of-line behavior is
accepted because it is the mechanism that makes "no payload escapes after
revocation is observed" true, and THE LEASE serializes exactly one connection -
never a keep-alive, never a frame on an unrelated connection.

**The lock's scope is not the whole blocking story**, which matters when sizing a
deployment. ``channels.auth.get_user`` is thread-sensitive, so every connection's
actor read in a process runs on ONE shared executor thread: the revalidated-frame
ceiling is per PROCESS rather than per connection, and a session store that stalls
one connection's read stalls every other connection's protected frames behind it.
A positive ``websocket_revalidation_window`` is the lever that removes the read,
and with it both the shared-thread ceiling and that coupling; a faster session
backend is not, because the actor read is the shared cost. The bound on a stalled
read is the session database's own connect / statement timeouts, and this module
deliberately imposes none of its own: abandoning a half-read executor thread would
queue the next frame behind that same thread, making a stalled store worse rather
than bounded. Spec-046 Decision 16 carries the measured budget.

**The window's meaning, expanded consistently.** ``websocket_revalidation_window``
is the maximum age of a successful actor validation that may authorize a new
operation **or** an information-bearing outbound operation frame. ``0.0`` (the
default) therefore revalidates at every operation admission and every ``next`` /
``data`` / operation-scoped ``error`` frame; a positive value permits reuse only
while the last successful validation is younger than it. There is no artificial
minimum interval, no second setting, and no background task, so an idle
authenticated socket performs ZERO database reads.

**What that costs, stated as a consequence rather than left emergent.** Detection
is event-boundary-driven. A revoked subscription that produces no further events
may stay physically open indefinitely, holding its socket, its subscription task,
its session object, and a stale actor reference - because nothing polls. That is
accepted: while idle it has no authorization capability at all, and its next
operation or information-bearing frame must pass the gate, fail validation, and
close the connection. Idle timeout, maximum socket lifetime, and aggregate
connection limits are transport-resource policy owned by the ASGI server, the
reverse proxy, or a deliberately injected consumer (Decision 12).

The class is built by ``routers.py::_build_router_class`` inside the same
soft-``channels`` guard and the same ``_ROUTER_CLASS`` cache the router itself
lives in, so its lifetime is exactly the router class's; this module caches
nothing. It is deliberately **not** exported, and unreachable by import rather
than merely absent from ``__all__``: the class statement is FUNCTION-LOCAL to
``build_revalidating_consumer_class``, so ``from
django_strawberry_framework.consumers import GraphQLWebSocketConsumer`` raises
``ImportError`` and there is no module attribute for a consumer to bind (the same
is true of the three private classes beside it). The supported choices are the
package default or an injected consumer of your own, passed as
``DjangoGraphQLProtocolRouter(..., websocket_consumer_class=...)``.

Importing this module is ``channels``-free, which is what lets ``routers.py``
import it above its own guard: the module level reaches only for the standard
library, Django's own ``HttpRequest`` / ``DisallowedHost`` (a HARD dependency, and
the whole point of the Host boundary below), this package's logger,
``exceptions.ConfigurationError`` / ``exceptions.describe_value``, and the
connection-actor-lease helpers from ``utils/sessions.py`` - a module whose own
imports are ``__future__``, ``asyncio``, ``contextlib`` and typing names, so it
adds nothing to the import graph.
``channels.auth.get_user`` and the package's session-store resolver are imported
**inside** the revalidation coroutine (the
``auth/mutations.py::_channels_http_login_establish`` precedent), the error-policy
masking helpers **inside** the result source that applies them (that module
imports ``strawberry`` and ``graphql``, so a module-level import here would put
both above ``routers.py``'s guard),
``channels.security.websocket.WebsocketDenier`` **inside** the Host validator's
denial arm, and neither the two protocol handler base classes nor upstream's
WebSocket adapter are imported at all - all three are read off the base consumer
class the factory is handed, so an upstream re-point is tracked for free.
``views.py`` does not import this module, so the package's Django GraphQL view
stays adoptable without the soft dependency.

The session-store resolver the revalidation reaches - like the connection actor
lease it shares with the auth layer - is
``utils/sessions.py``'s and deliberately NOT
``auth/sessions.py``'s re-export of it: ``auth`` is structurally opt-in
(spec-040 Decision 3) and its ``__init__`` eagerly imports ``.mutations`` /
``.queries``, so importing that submodule would register the whole GraphQL auth
subsystem on the event loop the first time an authenticated socket ran an
operation - for a resolver that only reads ``SESSION_ENGINE``. Nothing on this module's
revalidation path imports ``django_strawberry_framework.auth``, and a test asserts exactly
that.

**The Host boundary** (spec-046 Decision 19). ``DjangoWebSocketHostValidator`` is
the outermost WebSocket wrapper ``routers.py`` composes, and it exists because
``channels.security.websocket.OriginValidator.__call__`` reads the ``Origin``
header and NOTHING else - ``AllowedHostsOriginValidator`` is only a factory for
``OriginValidator(settings.ALLOWED_HOSTS)``, so its name was never evidence that a
``Host`` was checked. Django never sees the handshake at all, so unlike HTTP there
was no other owner for the question: a handshake carrying an allowed ``Origin`` and
a hostile ``Host`` connected.

It is a boundary that **calls Django** rather than a second implementation of one.
``_host_validation_request`` projects the handshake's Host-related metadata into a
minimal ``HttpRequest`` and the validator calls the public
``HttpRequest.get_host()``; syntax checking, port removal, IPv4 / IPv6 handling,
trailing-dot behavior, ``ALLOWED_HOSTS`` matching, wildcards and the
``DEBUG``-with-empty-``ALLOWED_HOSTS`` localhost defaults all stay exclusively
Django's. The package parses and matches no hostnames, adds no setting, and leaves
Channels' validator untouched - WebSocket simply follows the same Django
configuration HTTP already follows.

Host and Origin stay **two separate checks**, in that order: Host answers which
server authority the client addressed, Origin answers which browser origin
initiated the socket, and passing one never substitutes for passing the other.
Only Django's ``DisallowedHost`` becomes a denial, and the denial is Channels' own
``WebsocketDenier`` so a refused ``Host`` is byte-identical on the wire to a
refused ``Origin``. Every other exception propagates: a projection bug that
silently denied every handshake would be indistinguishable from correct
``ALLOWED_HOSTS`` enforcement, which is the worst available failure mode for a
check whose entire value is that it rejects.
"""

from __future__ import annotations

import asyncio
import contextlib
import math
import time
from collections.abc import Awaitable, Callable
from typing import Any

from django.core.exceptions import DisallowedHost
from django.http import HttpRequest

from . import logger
from .exceptions import ConfigurationError, describe_value
from .utils.sessions import (
    actor_lease,
    connection_was_authenticated,
    note_authenticated_actor,
)

#: The default revalidation window, in seconds: ``0.0`` revalidates at every
#: security checkpoint. Spelled ONCE here and imported by ``routers.py`` for its
#: ``websocket_revalidation_window=`` keyword default, so the number cannot
#: drift between the constructor and the consumer (spec-046 Decision 11).
_DEFAULT_REVALIDATION_WINDOW = 0.0

#: The ONE close the package uses for a revoked connection, at BOTH checkpoints
#: and on both protocols: upstream's own ``4403`` / ``"Forbidden"``, byte-identical
#: to what ``handle_connection_init`` sends when ``on_ws_connect`` raises
#: ``ConnectionRejectionError``. Reusing it verbatim is the non-disclosure
#: property, by construction: a revocation close is indistinguishable from every
#: other refusal to authorize this socket, so the wire cannot tell "your session
#: was revoked" from "your session was flushed", from "the user was disabled",
#: from "the revalidation read failed", or from a connect-time rejection. The
#: neighbouring codes upstream spends (4400 invalid message, 4401 unauthorized,
#: 4408 init timeout, 4409 duplicate id, 4429 too many subscriptions) all describe
#: something else, and a bespoke code was considered and rejected: it would be a
#: package-specific signal announcing exactly which refusal fired.
_REVOCATION_CLOSE_CODE = 4403
_REVOCATION_CLOSE_REASON = "Forbidden"

#: The bounded number of close attempts one connection's revocation may spend:
#: the first attempt plus exactly ONE retry. Checkpoints are client-driven, so an
#: unbounded retry would hand a client an amplification lever - one attempted
#: close per frame it chooses to provoke - and the realistic raise set is not
#: transient (a disconnected transport, a server state assertion, an ``OSError``),
#: so a third attempt cannot succeed where the first two did not. Past the bound
#: the connection is ABANDONED: no further attempt, and the outbound gate stays
#: fail-closed for every information-bearing frame, which is the property that
#: does not depend on the close reaching the wire.
_MAX_REVOCATION_CLOSE_ATTEMPTS = 2

#: The five states of one connection's revocation. ``PERMITTED`` is the only one
#: in which a checkpoint may authorize anything; the other four all deny, and
#: differ only in what they say about the close. Spelled as module constants
#: rather than derived from a set of booleans so that "revoked but no close in
#: flight and a retry permitted" is a state with a name instead of a conjunction
#: a future reader has to reconstruct.
_REVOCATION_PERMITTED = "permitted"
_REVOCATION_DECIDED = "decided"
_REVOCATION_CLOSING = "closing"
_REVOCATION_CLOSED = "closed"
_REVOCATION_ABANDONED = "abandoned"

#: The frame types that carry operation information, and therefore the ones the
#: outbound checkpoint gates: ``next`` (graphql-transport-ws), ``data`` (legacy
#: graphql-ws), and the operation-scoped ``error`` both protocols use for
#: pre-execution and other operation errors. Every other frame type either belongs
#: to connection control (``connection_ack``, ``connection_error``, ``ping``,
#: ``pong``, ``ka``) or announces an ending rather than a payload (``complete``).
#: Their payloads remain upstream-owned; the adapter still serializes their writes
#: with the connection's revocation decision.
_INFORMATION_BEARING_FRAME_TYPES = frozenset({"next", "data", "error"})

#: The private scope key holding the last successful revalidation's monotonic
#: timestamp, written only when a window is configured. Namespaced with the
#: distribution name exactly like ``auth/sessions.py::_SCOPE_LOCK_KEY``, so it
#: can never collide with an ASGI key set by Channels, Django, or consumer
#: middleware.
_REVALIDATED_AT_SCOPE_KEY = "__django_strawberry_framework_ws_revalidated_at__"


def _monotonic() -> float:
    """Return the monotonic clock, in seconds.

    A monotonic reading, never a wall clock: a system clock step must not be
    able to widen or collapse a revalidation window. It is a named module-level
    function because it is also the documented test seam - the window tests
    advance the clock by monkeypatching this name rather than sleeping through a
    real interval, which keeps them deterministic under ``-W error`` / ``-n
    auto``.
    """
    return time.monotonic()


def _unusable_window_error(value: object) -> ConfigurationError:
    """Build the ONE rejection every unusable-window arm raises.

    A single message for a single domain: the arms below differ in *how* they
    detect an unusable value, not in what the deployment has to change. The
    value's tail goes through ``exceptions.py::describe_value`` because this
    message is formatted while rejecting a value the package does not trust -
    including an integer too large for CPython to render (see
    ``resolved_revalidation_window``).
    """
    return ConfigurationError(
        "websocket_revalidation_window must be a finite number of seconds >= 0.0 that "
        "converts to a float (0.0 revalidates the session actor at every operation "
        "admission and before every information-bearing operation frame); got "
        f"{describe_value(value)}.",
    )


def resolved_revalidation_window(value: object) -> float:
    """Validate ``websocket_revalidation_window`` and return it as a ``float``.

    Shaped after ``views.py::_resolved_max_request_body_bytes``: the same typed
    ``ConfigurationError``, the same EXACT-type admission, and the same
    ``got {type} {value!r}`` tail. Only the built-in ``int`` and ``float``
    themselves are admitted - never a subclass, and therefore never ``bool``
    (``isinstance(True, int)`` is ``True``, so an ``isinstance`` gate needed a
    second clause to say so; an exact-type gate says it once). The exactness is
    what makes the arithmetic below trustworthy: a subclass may override
    ``__float__`` to raise or to return an unrelated number, so an admitted
    subclass would evaluate consumer code INSIDE this boundary and escape it with
    a raw exception in place of the promised ``ConfigurationError``.

    A non-finite value (``nan`` / ``inf``) is rejected too, and the reason
    is unusability rather than a ceiling: ``nan`` loses every comparison, so a
    window spelled that way would silently never expire and never say why, and
    ``inf`` is the saturation sentinel a failed computation produces rather than
    a number of seconds any deployment chose. Both are far better as a loud
    construction-time failure. The router calls this, so an unusable window is a
    construction error and never a per-operation one.

    What is deliberately NOT rejected, so that rationale is not read as more than
    it is: a finite but astronomical window. ``10**300`` and ``1e308`` are
    accepted, and a window that large is operationally "never revalidate again". The package
    imposes no upper bound, for the same reason ``GraphQLWebSocketConsumer`` imposes no
    maximum connection lifetime (Decision 12): there is no correct default, any constant would
    be invented here rather than derived from anything, and a positive window is a deliberate
    consumer trade-off - one session read per authenticated checkpoint against a named
    revocation delay - that the deployment can compute and this function has no standing to
    second-guess. The guard is about values the package cannot
    *use*, not about values it disapproves of.

    The ``float`` conversion is a GUARDED step of its own, and it happens BEFORE
    any numeric predicate runs. A sufficiently large ``int`` (``10**10000``) is a
    perfectly ordinary Python object that no ``isinstance`` check rejects, yet it
    has no ``float`` image: ``math.isfinite`` and ``float()`` both raise
    ``OverflowError`` on it. Reading the domain first would therefore have let a
    hostile or fat-fingered configuration escape the typed boundary with a raw
    ``OverflowError`` instead of the promised ``ConfigurationError``. Converting first also means the sign and
    finiteness checks below run on a real ``float``, which is the value the
    consumer will actually compare against.
    """
    if type(value) not in (int, float):
        raise _unusable_window_error(value)
    try:
        window = float(value)
    except OverflowError as exc:
        # Chained, not swallowed: the cause names WHY the number is unusable
        # ("int too large to convert to float") under the package's own error.
        raise _unusable_window_error(value) from exc
    if window < 0 or not math.isfinite(window):
        raise _unusable_window_error(value)
    return window


class _ConnectionRevocation:
    """One connection's revocation decision and the state of its ``4403`` close.

    Five states, and every transition between them:

    * ``PERMITTED`` - nothing has failed validation. The ONLY state in which a
      checkpoint may authorize an operation or a frame. ``decide()`` moves it to
      ``DECIDED``.
    * ``DECIDED`` - revocation is published and no close attempt is in flight, and
      one is still permitted. Reached from ``PERMITTED`` by ``decide()``, and from
      ``CLOSING`` when an attempt RAISED with the attempt bound not yet spent.
      ``close()`` moves it to ``CLOSING``.
    * ``CLOSING`` - a connection-owned attempt is in flight. Every checkpoint that
      arrives here awaits THAT attempt rather than starting its own. The attempt
      itself moves it to ``CLOSED``, ``DECIDED`` or ``ABANDONED``.
    * ``CLOSED`` - terminal. An attempt's own ``await`` on the adapter's ``close``
      returned, so a ``4403`` was committed to the transport.
    * ``ABANDONED`` - terminal. No close ever completed and none ever will: either
      the attempt bound (``_MAX_REVOCATION_CLOSE_ATTEMPTS``) is spent, or the
      connection's final teardown cancelled the attempt in flight.

    ``decide()`` is synchronous and runs before any await, which is what lets every
    checkpoint refuse on ``revoked`` **read-free** - the refusal costs no session
    read at all, at either checkpoint, however many frames a client pipelines
    behind the close.

    The outcome is recorded by the task that awaited ``close`` to completion, after
    its own await returned - never before it, and never by a bystander. That is
    the whole correction: an ASGI ``send`` is asynchronous and unacknowledged, so
    "a close was decided" and "a close reached the transport" are different facts,
    and a single flag set before the await records the first as the second. An
    attempt that raised is not a success: the state returns to ``DECIDED`` and the
    next permitted checkpoint starts exactly one new attempt.

    **Mid-connection, a cancellation delivered to whichever checkpoint is waiting
    never touches the attempt; at final teardown it ENDS it.** The two are
    different questions, and only the first one is about the close's outcome. While
    the connection is live, ASGI's ``send`` returns ``None`` and offers no
    acknowledgement, so a cancellation arriving while the close is suspended says
    nothing about whether the frame was committed: the attempt is shielded, the
    cancelled waiter goes away, and some later waiter records the outcome. That is
    why the ordinary success path can never put two ``4403`` frames on the wire -
    exactly one attempt is ever in flight, and only a RAISE reopens the door.

    ``settle()`` is the other question. It runs once, from the connection's
    ``disconnect``, and it is the attempt's LAST owner rather than one more waiter,
    so a cancellation delivered there (an ASGI server shutting the application
    down, or an application-close timeout) cannot be answered by leaving the task
    running: an attempt that outlived its connection would hold the adapter, the
    consumer, the scope and a stale actor, possibly suspended on a ``send`` after
    the ASGI application had already returned. So the terminal owner cancels the
    attempt, awaits it to completion, and re-raises the cancellation it was given.
    The socket is being disconnected at that point, so the retry ambiguity above
    has nothing left to protect - a cancelled attempt therefore ends ``ABANDONED``
    rather than resting in ``CLOSING``, and ``ABANDONED`` permits no further
    attempt.
    """

    __slots__ = ("attempt", "attempts", "state")

    def __init__(self) -> None:
        self.state = _REVOCATION_PERMITTED
        self.attempt: Any = None
        self.attempts = 0

    @property
    def revoked(self) -> bool:
        """Whether this connection has been revoked, whatever its close has done.

        The read-free denial every checkpoint - and the stop-aware result source -
        consults. It is a latch in meaning: ``PERMITTED`` is never re-entered.
        """
        return self.state != _REVOCATION_PERMITTED

    def decide(self) -> None:
        """Publish the revocation decision, synchronously and before any await."""
        if self.state == _REVOCATION_PERMITTED:
            self.state = _REVOCATION_DECIDED

    async def close(self, websocket: Any) -> None:
        """Start the one permitted close attempt, or await the one already in flight.

        Callers hold the connection's actor lease, so the state read and the task
        creation below cannot interleave with another checkpoint's - which is what
        makes "at most one attempt in flight" true by construction rather than by
        a second lock.

        The attempt is a task the CONNECTION owns, and ``asyncio.shield`` is what
        makes that ownership real rather than nominal: a plain ``await`` on a task
        installs it as the awaiter's ``_fut_waiter``, so cancelling the awaiter
        cancels the awaited task too, and the close a client-cancellable operation
        happened to start would die with that operation. Shielding costs a future
        per acquisition on a path taken once per connection, and it takes nothing
        away from the outcome record: ``_attempt_close`` is the task that awaits
        the transport, so it is the one that records what happened.
        """
        if self.state == _REVOCATION_DECIDED:
            self.attempts += 1
            self.state = _REVOCATION_CLOSING
            self.attempt = asyncio.create_task(self._attempt_close(websocket))
        if self.state == _REVOCATION_CLOSING:
            if self.attempt.done() and self.attempt.cancelled():
                self.state = _REVOCATION_ABANDONED
                return
            await asyncio.shield(self.attempt)

    async def settle(self) -> None:
        """End this connection's close attempt, if it ever started one.

        The connection's own teardown hook, so an attempt whose starting checkpoint
        was cancelled is still finished by somebody before the ASGI application
        returns - a task the connection owns must not outlive the connection. It
        never STARTS an attempt: teardown is not a security checkpoint, and a
        socket that is already being disconnected has nothing left to refuse.

        This is the attempt's TERMINAL owner, which is what makes the ownership
        claim true rather than nominal. The wait is shielded for the reason ``close``
        shields - a bystander's cancellation must not kill a close that is nearly
        committed - but a cancellation delivered HERE is not a bystander's: nobody
        comes after. Shielding alone would let the caller return while the task it
        was settling stayed suspended on a transport that is going away, so the
        cancellation is instead answered by cancelling the attempt, awaiting it to
        completion, and re-raising - the caller's cancellation is honoured, and no
        task retains this connection past it.
        """
        if self.attempt is None:
            return
        if self.attempt.done():
            if self.attempt.cancelled():
                self.state = _REVOCATION_ABANDONED
            return
        try:
            await asyncio.shield(self.attempt)
        except asyncio.CancelledError:
            self.attempt.cancel()
            # Suppressed, not swallowed: the attempt answers a cancellation it was
            # handed with ``CancelledError`` of its own, and re-raising the caller's
            # below is what propagates the one that matters.
            with contextlib.suppress(asyncio.CancelledError):
                await self.attempt
            raise

    async def _attempt_close(self, websocket: Any) -> None:
        """Commit one ``4403`` close, and record what actually happened.

        Runs as the connection's own task, and records the outcome AFTER its own
        await returns. The close goes through the adapter (upstream's own
        ``ChannelsWebSocketAdapter.close`` -> ``consumer.close``) rather than
        around it, so a consumer that derives its own adapter keeps owning the
        write.

        A cancellation is a separate arm from ``Exception``, and it is terminal: only
        the connection's final teardown cancels this task, so the socket is already
        going away and no later attempt can reach a client. The state moves to
        ``ABANDONED`` before the ``CancelledError`` is re-raised, which is what keeps
        a cancelled attempt from resting in ``CLOSING`` - a state that claims an
        attempt is in flight. Recorded by the task itself rather than by its awaiter
        because the task is the only party that knows whether the cancellation
        arrived before or after its own ``await`` returned.

        ``Exception`` and not ``BaseException`` for the other arm: the realistic raise
        set is a disconnected transport, a server state assertion and an ``OSError``,
        all of which are failures this connection can still answer for. The failure
        itself is recorded and NOT re-raised out of the task: an awaiting
        checkpoint's job is to know the attempt finished, not to inherit its
        exception, and an attempt whose awaiter was cancelled must not leave an
        unretrieved one behind either.
        """
        try:
            await websocket.close(
                code=_REVOCATION_CLOSE_CODE,
                reason=_REVOCATION_CLOSE_REASON,
            )
        except asyncio.CancelledError:
            self.state = _REVOCATION_ABANDONED
            raise
        except Exception:
            self.state = (
                _REVOCATION_DECIDED
                if self.attempts < _MAX_REVOCATION_CLOSE_ATTEMPTS
                else _REVOCATION_ABANDONED
            )
            logger.exception(
                "GraphQLWebSocketConsumer: the revoked connection's close could not be "
                "committed to the transport (attempt %s of %s). Information-bearing frames "
                "stay refused on this connection either way; the next security checkpoint "
                "retries the close while the attempt bound allows it.",
                self.attempts,
                _MAX_REVOCATION_CLOSE_ATTEMPTS,
            )
            return
        self.state = _REVOCATION_CLOSED


async def revalidate_operation_actor(handler: Any) -> bool:
    """Admission checkpoint: may a NEW operation start on this connection?

    Returns ``True`` to let upstream run the operation. Returns ``False`` after
    revoking the connection - which closes the socket - so the caller's only job
    is to skip its ``super()`` delegation. Nothing is sent on the way out: the
    close IS the rejection, and it is byte-identical to the outbound checkpoint's.
    That symmetry is forced rather than chosen - an admission-time operation
    ``error`` frame would be gated by the outbound checkpoint, validated against
    the same already-revoked actor, and suppressed - which is why this function has
    no operation id, no per-protocol payload shape, and no error message left to
    format (see the module docstring).

    Why here and not elsewhere (spec-046 Decision 11's rejected alternatives):
    ``get_context`` runs once per connection, before either protocol's message
    loop, so it is not a per-operation seam; the consumer's ``receive()`` sees
    every frame including keep-alives and can only close the socket rather than
    decide about one operation.

    ``handler`` is duck-typed on purpose - all this needs is upstream's
    ``connection_acknowledged`` flag (both handlers set it in ``__init__`` and
    flip it in ``handle_connection_init``), ``view`` (which IS the consumer, so
    the ASGI scope is ``handler.view.scope``), and ``websocket`` (the adapter
    instance, which is where the close lives).

    The read is alias-explicit **by delegation** (spec-046 Edge cases): the
    session load and the user load both resolve their alias through Django's own
    ``router.db_for_read`` - the deployment's explicit routing decision, never a
    hardcoded ``"default"`` - which is the same authority
    ``utils/permissions.py::resolve_auth_aliases`` reads. It takes no *session*
    lock: ``auth/sessions.py::scope_session_lock`` serializes session
    *mutations*, while this is a read of a private store. What it does take is the
    connection's shared actor lease, which serves both purposes at once - it makes
    the validate-transition-send sequence atomic against sibling operations on the
    same socket, AND, because ``utils/sessions.py::actor_transition`` holds the
    same lease, against the one revocation the package performs itself. A read that
    suspends inside the lease can no longer be overtaken by a same-connection
    ``logout``, because that ``logout`` is waiting for it.

    One caveat worth stating: with ``SESSION_ENGINE`` set to Django's
    signed-cookie engine there is no server-side record, so a flush is not
    observable server-side at all - which is why
    ``auth/sessions.py::logout_supported`` already refuses logout on that
    combination. The disabled-user and password-rotation shapes remain
    observable there, because both are read off the user row.
    """
    # The handshake is not complete, so upstream's own ``4401 Unauthorized``
    # close must be what the client sees. No session read.
    if not handler.connection_acknowledged:
        return True

    consumer = handler.view
    async with actor_lease(consumer.scope):
        # The left arm short-circuits, so an already-revoked connection denies
        # without a session read of its own. A client can still have pipelined
        # this frame before the close reached it, so that arm is reachable rather
        # than defensive - and it must stay read-free, which is what makes the
        # denial stable at no further database cost. It still routes through
        # ``_revoke_connection``, because "revoked" does not imply "closed": an
        # earlier attempt may have raised, and this checkpoint is the next
        # permitted one.
        if not consumer._revocation.revoked and await _actor_is_current(consumer):
            return True
        await _revoke_connection(handler.websocket)
        return False


async def send_revalidated_operation_frame(
    websocket: Any,
    message: Any,
    send: Callable[[Any], Awaitable[None]],
) -> None:
    """Outbound checkpoint: send one information-bearing frame, or revoke.

    The ENTIRE critical section lives here rather than in the adapter, which is
    what lets the derived adapter stay a two-line delegation (the shape the two
    handler subclasses already have) and what puts the lock discipline in one
    place: the connection's actor lease spans the validation / cache decision, the
    revoked-state transition, and ``send`` itself. See the module docstring for why
    holding it through the send - and the per-connection head-of-line blocking that
    buys - is the point rather than an oversight. ``send`` is the LAST thing inside
    the lease deliberately: it is asynchronous, so any window left open after the
    authorization and before the bytes are committed is a window a
    same-connection ``logout`` can complete inside, and a generation compared
    after ``send`` returns would be checked against a frame that has already gone
    out.

    ``send`` is the adapter's own ``super().send_json`` bound method, so the
    delegation is upstream's serialize-and-write path, unchanged.

    This function suppresses and revokes; it does NOT unwind the operation, and
    adds no suspension point of its own on the way out. The revoked operation ends
    itself, deterministically, at its result loop's next iteration - see the
    module docstring's stop-aware-result-source section for why termination rather
    than cancellation is the mechanism, and why an operation whose next value is
    already available could never be stopped by a cancellation request issued from
    here. The one path that arrives with no operation of the package's to end at
    all is the protocols' subscription-limit ``error`` frame, which both handlers
    emit from the connection's own message-loop task; the close alone is the whole
    rejection there, and it needs no carve-out now that nothing is cancelled.
    Upstream's own ``shutdown()`` / ``cleanup()`` still cancels and awaits every
    sibling operation on disconnect.
    """
    consumer = websocket.ws_consumer
    async with actor_lease(consumer.scope):
        if not consumer._revocation.revoked and await _actor_is_current(consumer):
            await send(message)
            return
        await _revoke_connection(websocket)


async def _actor_is_current(consumer: Any) -> bool:
    """Return whether the connection's scope actor is valid **now**.

    The ONE decision both checkpoints await (spec-046 Helper-reuse: "every
    decision - window expiry, session reload, actor write-back - lives in the
    shared function"). It never sends, never closes, and never cancels: the two
    callers own the response to a ``False``, which is what keeps admission and
    the outbound gate from drifting apart.

    Callers hold the connection's actor lease, so the provenance test, the window
    comparison, the reload, and the cache write below are atomic against every
    sibling checkpoint on the same socket AND against a package-owned actor
    transition on the same connection - ``utils/sessions.py::actor_transition``
    holds that same lease for the whole teardown. Every arm below therefore runs
    on a connection whose actor identity cannot change underneath it, which is
    what licenses the one arm that authorizes without reading anything: the
    positive-window cache hit is an authorization decision, so it must not be
    reachable outside the lease that every other arm holds.
    """
    scope = consumer.scope
    actor = scope.get("user")
    # The anonymous carve-out, keyed on PROVENANCE rather than on the current
    # actor: a connection that has never carried an authenticated actor has no
    # session actor to revalidate, so only an authenticated connection pays the
    # cost. An authenticated -> anonymous change is the opposite of a free pass:
    # it is the package's own ``logout`` having replaced the scope actor, which
    # is a connection-scoped revocation event, so it is refused here and the
    # caller closes the socket.
    #
    # The authenticated predicate itself is the one
    # ``auth/mutations.py::_authenticated_actor_or_none`` applies, deliberately
    # spelled rather than imported - that helper is private to the auth-mutation
    # surface, and importing it would pull the whole ``auth`` package (and the
    # Strawberry type stack behind it) into a transport-layer coroutine. If a
    # THIRD site ever needs this predicate, promote it to
    # ``utils/permissions.py`` beside ``ChannelsRequestAdapter`` instead.
    if actor is None or not actor.is_authenticated:
        return not connection_was_authenticated(scope)
    note_authenticated_actor(scope)

    # Plain attribute access, deliberately: ``GraphQLWebSocketConsumer.__init__``
    # always assigns ``revalidation_window`` BEFORE ``super().__init__``, and the
    # class is function-local to the factory, so no third party can construct one
    # without it. A ``getattr`` default here would be unreachable defensiveness on
    # the one line that decides whether a session read happens - and if a future
    # refactor did drop the attribute, the default would silently switch the
    # deployment to "revalidate at every checkpoint" (a performance cliff that
    # lives in an expression, where statement coverage cannot see it) instead of
    # failing loudly.
    window = consumer.revalidation_window
    # ``-inf`` reads as "never revalidated, i.e. infinitely long ago", which
    # keeps the expiry test one comparison with no sentinel branch of its own.
    # With the default window of ``0.0`` the left arm short-circuits, so nothing
    # is ever written to the scope.
    if window > 0.0 and _monotonic() - scope.get(_REVALIDATED_AT_SCOPE_KEY, -math.inf) < window:
        return True

    try:
        refreshed = await _refreshed_actor(scope)
    except Exception:
        # Fail closed (spec-046 Edge cases #"A revalidation database error must
        # fail closed"): a store or auth failure denies the checkpoint - and so
        # terminates the connection - and is never a fall back to the cached
        # actor. ``Exception``, not ``BaseException`` - an
        # ``asyncio.CancelledError`` from task teardown must propagate rather
        # than be converted into a denial.
        logger.exception(
            "GraphQLWebSocketConsumer: the WebSocket session revalidation failed; the "
            "connection is revoked and closed (fail-closed) rather than continuing on "
            "the connection's cached actor.",
        )
        refreshed = None

    if refreshed is None or not refreshed.is_authenticated:
        # The stale actor stays on the scope. Downgrading it to ``AnonymousUser``
        # would let anything still holding this scope read an anonymous session
        # instead of a revoked one (spec-046 Decision 11); the connection is
        # about to be closed either way.
        return False

    # The write-back (spec-046 Decision 11): ``channels.auth``'s own ``login`` /
    # ``logout`` replace ``scope["user"]`` the same way, and the Channels request
    # adapter reads that key - so every surface reached through
    # ``request_from_info`` observes the fresh actor with no new plumbing.
    scope["user"] = refreshed
    if window > 0.0:
        scope[_REVALIDATED_AT_SCOPE_KEY] = _monotonic()
    return True


async def _revoke_connection(websocket: Any) -> None:
    """Publish the revocation decision, then drive the connection's close.

    The ONE entry point both checkpoints take into
    ``_ConnectionRevocation``, so the decision and the close can never be
    published out of order or by different rules: the transition is set BEFORE any
    await, so a sibling task that acquires the connection's actor lease next
    observes "revoked" immediately and takes neither a second session read nor a
    second close attempt, and the close itself is the connection's own bounded
    attempt. Both halves are idempotent, which is not a nicety: both checkpoints
    call this, on every frame a client pipelines behind the close, and a socket
    closed twice would put a second ``websocket.close`` on the wire after the
    first.
    """
    revocation = websocket.ws_consumer._revocation
    revocation.decide()
    await revocation.close(websocket)


async def _stop_aware_results(source: Any, consumer: Any, schema: Any) -> Any:
    """Yield ``source``'s masked results until the connection is revoked, then end.

    **This is also where the error policy reaches a subscription** (spec-048
    Decision 11). A subscription's errors do not arrive on one completed result -
    each event carries its own ``ExecutionResult``, and the schema extension's
    teardown runs only when the operation ENDS, so a per-event error would be on
    the wire long before it. This generator is the one seam every event of every
    subscription passes through on both protocols, so each result is masked here,
    immediately before the transport renders it. The policy object and the
    masking are the extension module's, not re-stated: one classifier, one
    replacement builder, two application sites - including the shape gate,
    ``is_maskable_result``, which is what lets a value the policy cannot rewrite
    (a raw incremental-delivery frame, on the upstream releases that stream one)
    reach the transport's own refusal to render it rather than be degraded into a
    shape that refusal no longer recognizes.

    The masked value is a COPY when anything was masked, so the engine's own
    result object - the one ``execution_context.result`` holds and the one an
    extension reading ``GraphQLError.original_error`` sees - is left untouched.
    That preserves the LIFO teardown ordering property for the debug extension
    exactly as the query path does.

    The policy object is resolved ONCE per subscription - it is immutable and its
    schema outlives the socket - while the ``DEBUG`` pass-through gate is read per
    event, which is the same granularity the query path's teardown reads it at.

    The masking import is function-local, deliberately: this module's import
    graph is ``channels``-free AND ``strawberry``-free so ``routers.py`` can
    import it above its own soft-dependency guard (see the module docstring), and
    the extension module imports both ``strawberry`` and ``graphql``. By the time
    a subscription produces a result, both are long since imported.

    The rest is the package-owned half of the operation-stop protocol. Upstream's
    two result loops (``run_operation`` / ``handle_async_results``) iterate whatever
    ``schema.subscribe`` / ``schema.stream`` handed back, so ending THIS generator
    ends that loop - normally, at its own next iteration, with no cancellation
    involved and no suppressed payload produced. The revocation state is read before
    each pull rather than after it, which is what makes the number of values a
    revoked subscription still produces bounded and deterministic: the suppressed
    frame's own value is the last one the resolver is ever asked for.

    The state read needs no lease. It is a latch, and reading a stale ``False``
    costs exactly one more value - which the outbound checkpoint then refuses
    under the lease, like any other frame. Taking the lease here would instead
    serialize the connection's result production behind its own sends.

    ``finally`` closes the inner source when it exposes the async-generator
    ``aclose`` hook, so the subscription's own ``finally`` runs at the revocation and
    before teardown rather than whenever the interpreter's asyncgen finalizer reaches
    it. An async iterator without that optional hook remains valid on the legacy
    handler's older upstream path, which never required one. That is the package's
    own guarantee rather than a restatement of upstream's, and it has to be: transport-ws
    did not close its result source at all up to 0.318.1 (no ``finally``, no
    ``aclosing``, and the local went out of scope) and wraps the loop in
    ``aclosing`` from 0.319.0 on. Legacy's ``cleanup_operation`` closes whatever is
    registered - which is now this generator, so closing it closes the real one
    underneath - and the newer transport-ws ``aclosing`` closes this generator
    exactly the same way, an already-finished generator's ``aclose`` being a no-op.
    """
    from .extensions.error_policy import (
        is_maskable_result,
        mask_execution_result,
        masking_is_active,
        schema_error_policy,
    )

    policy = schema_error_policy(schema)
    try:
        while not consumer._revocation.revoked:
            try:
                result = await anext(source)
            except StopAsyncIteration:
                return
            if masking_is_active(policy) and is_maskable_result(result):
                result = mask_execution_result(result, policy)
            yield result
    finally:
        # ``Schema.subscribe`` / ``stream`` are typed as async generators,
        # but the upstream legacy handler accepts any async iterator. Keep
        # that compatibility on the package's older Strawberry range too:
        # the newer transport handler closes its source with ``aclosing``,
        # while older handlers do not require an ``aclose`` method at all.
        aclose = getattr(source, "aclose", None)
        if aclose is not None:
            await aclose()


class _StopAwareSchema:
    """One connection's schema, with subscription results made stoppable and masked.

    Installed on the two handler subclasses' own ``self.schema`` by
    ``_install_stop_aware_schema``, never on the consumer's, so the substitution
    reaches exactly the two upstream call sites that build an operation's result
    source and nothing else. See the module docstring for the transparency
    argument, and for why the wrapper is invisible to execution itself.

    BOTH result-source names are defined, because which one a handler reads depends
    on the installed upstream release and covering only one silently unwraps a whole
    protocol - see the module docstring for the range and for why this is not a
    version test. ``__getattr__`` forwards every other name to the wrapped schema
    object by identity, which is what keeps ``execute`` - the older releases'
    non-subscription path, whose single already-torn-down result never loops and
    needs no stopping - upstream's own call. ``__slots__`` keeps the two fields off
    that forwarding path, so a misspelled internal name is an ``AttributeError``
    here rather than a silent delegation to the real schema.
    """

    __slots__ = ("_consumer", "_schema")

    def __init__(self, schema: Any, consumer: Any) -> None:
        self._schema = schema
        self._consumer = consumer

    def __getattr__(self, name: str) -> Any:
        """Forward every name but the two result-source calls to the real schema."""
        return getattr(self._schema, name)

    async def subscribe(self, *args: Any, **kwargs: Any) -> Any:
        """Return the real schema's subscription results, wrapped so they can stop.

        The seam both protocols read up to 0.318.1, and the one the legacy
        ``graphql-ws`` handler reads throughout the supported range.
        """
        return self._stoppable(await self._schema.subscribe(*args, **kwargs))

    async def stream(self, *args: Any, **kwargs: Any) -> Any:
        """Return the real schema's streamed results, wrapped so they can stop.

        The seam ``graphql-transport-ws`` reads from 0.319.0 on, for EVERY operation
        type rather than subscriptions alone. Defined unconditionally rather than
        behind a version test: an install below 0.319.0 has no ``Schema.stream`` to
        delegate to and no handler that reads the name, so this method is simply
        never called there.
        """
        return self._stoppable(await self._schema.stream(*args, **kwargs))

    def _stoppable(self, source: Any) -> Any:
        """Wrap one upstream result source in the connection's stop-and-mask seam.

        Shared by both entry points so the two cannot diverge on what a result
        source is wrapped WITH. The REAL schema is handed to the result source,
        because that is where the operation's error policy lives
        (``schema.error_policy``): the per-result masking has to read the policy of
        the schema that executed the operation, never a wrapper attribute of this
        object.

        Both callers' signatures are deliberately positional-and-keyword
        pass-through: the arguments are upstream's, and re-spelling them here would
        be a second declaration of two upstream parameter lists to keep in step.
        Neither call awaits anything before returning its generator, so the ``await``
        in each adds no suspension point to an operation's start.
        """
        return _stop_aware_results(source, self._consumer, self._schema)


def _install_stop_aware_schema(handler: Any) -> None:
    """Give one protocol handler the connection's stop-aware schema.

    Called by both handler subclasses after ``super().__init__`` has stored
    upstream's ``schema=`` keyword, so the wrapper wraps whatever the view handed
    over. ``handler.view`` IS the consumer under the Channels integration, which
    is where the revocation state lives.
    """
    handler.schema = _StopAwareSchema(handler.schema, handler.view)


async def _refreshed_actor(scope: Any) -> Any:
    """Reload the connection's session and resolve its actor, or ``AnonymousUser``.

    ``channels.auth.get_user`` is reused verbatim rather than reimplemented: it
    owns the ``AUTHENTICATION_BACKENDS`` allow-list check, the
    ``backend.get_user()`` load (where ``ModelBackend.user_can_authenticate``
    rejects a disabled user), and the constant-time ``get_session_auth_hash``
    comparison, and it answers ``AnonymousUser()`` for every invalid shape - one
    call therefore covers the revoked, flushed, disabled, and password-rotated
    cases together.

    It is already decorated ``@database_sync_to_async``, so this crosses
    **exactly one** sync boundary and must not be wrapped again
    (``utils/querysets.py::run_in_one_sync_boundary`` would add a second one and
    discard ``database_sync_to_async``'s ``close_old_connections``). The store is
    constructed outside that boundary, which is IO-free - a session store defers
    ``load()`` to first item access, and that access happens inside ``get_user``.

    The synthetic one-key mapping is deliberate: ``get_user`` reads
    ``scope["session"]`` and nothing else, and handing it the connection's own
    session object would let its hash-mismatch ``session.flush()`` land on the
    live store the Channels session middleware re-reads at send time. The
    connection's scope contributes only ``session_key``, an attribute read.
    """
    from channels.auth import get_user

    from .utils.sessions import session_store_class

    store = session_store_class()(scope["session"].session_key)
    return await get_user({"session": store})


def build_revalidating_consumer_class(base_consumer_cls: type) -> type:
    """Return a ``base_consumer_cls`` subclass that revalidates at both checkpoints.

    A pure factory: no cache, no soft-dependency guard, and no import of
    ``channels`` or ``strawberry``. ``routers.py`` calls it once inside the
    ``try: from strawberry.channels import GraphQLWSConsumer`` block that already
    owns both, so a degraded install still raises that module's single
    ``_STRAWBERRY_CHANNELS_BROKEN_HINT`` and this module needs no guard of its
    own.

    All three bases are read off ``base_consumer_cls`` - the two handler classes
    from ``graphql_transport_ws_handler_class`` / ``graphql_ws_handler_class``,
    and the adapter from ``websocket_adapter_class``, the attribute upstream's
    ``AsyncBaseHTTPView.run`` instantiates by name. The two handler attributes
    are *subscripted generic aliases* (``BaseGraphQLTransportWSHandler[Context,
    RootValue]``), not plain classes; deriving from them works through
    ``__mro_entries__`` and is the correct shape here - it imports none of the
    three modules and tracks an upstream re-point automatically.
    """

    class _RevalidatingTransportWSHandler(base_consumer_cls.graphql_transport_ws_handler_class):
        """``graphql-transport-ws``: revalidated admission, stoppable results."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            _install_stop_aware_schema(self)

        # ``message`` is upstream's ``SubscribeMessage`` TypedDict; annotated
        # ``Any`` deliberately, so the factory keeps importing nothing from
        # upstream's deep protocol-types modules.
        async def handle_subscribe(self, message: Any) -> None:
            if not await revalidate_operation_actor(self):
                return
            await super().handle_subscribe(message)

    class _RevalidatingGraphQLWSHandler(base_consumer_cls.graphql_ws_handler_class):
        """Legacy ``graphql-ws``: revalidated admission, stoppable results."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            _install_stop_aware_schema(self)

        # ``message`` is upstream's ``StartMessage`` TypedDict; see above.
        async def handle_start(self, message: Any) -> None:
            if not await revalidate_operation_actor(self):
                return
            await super().handle_start(message)

    class _RevocationGatedWebSocketAdapter(base_consumer_cls.websocket_adapter_class):
        """The outbound checkpoint, on the seam both protocols share.

        One class-level ``send_json`` override, installed on the generated
        consumer by the factory - the same mechanism as the two handler classes
        above, and never a rebound instance attribute, so there is no per-socket
        patching step that a future refactor could forget to perform.
        """

        # ``message`` is a protocol frame mapping on either protocol; ``Any``
        # for the same reason the handler hooks above use it.
        async def send_json(self, message: Any) -> None:
            """Revalidate an information-bearing frame; write nothing once revoked.

            Two arms, and only the first is an authorization decision. An
            information-bearing frame goes to the outbound checkpoint, which
            validates the connection's actor under its lease. Every other frame is
            upstream's own to write - until this connection's revocation has been
            DECIDED, after which this adapter writes nothing at all.

            **The invariant the second arm enforces: once the revocation is
            decided, the package puts no further frame on this socket.** A revoked
            operation's result loop ends NORMALLY (the stop-aware result source
            returns rather than cancelling), so upstream proceeds to its own
            end-of-operation frame - ``run_operation``'s ``complete`` on
            graphql-transport-ws, ``handle_async_results``' ``complete`` on legacy
            graphql-ws. That frame is not information-bearing, so without this arm
            it would be delegated straight through and committed AFTER the
            ``4403``: a control frame arriving on a socket this module says it
            terminated, which is the connection contract the revocation close
            exists to provide. It is also not merely untidy on a real server - an
            ASGI send past the protocol's open state raises, and the raise
            surfaces inside upstream's own operation task, which logs it and
            re-raises - so every revoked subscription would report a worker-task
            error.

            **DECIDED, not "close committed"**, deliberately. Between the decision
            and the commit the socket is still physically open, so a frame written
            in that window is a frame written to a connection the package has
            already refused; and the close is not guaranteed to commit at all - an
            attempt may raise, and a connection whose attempt bound is spent stays
            ``ABANDONED`` - so a cut-off keyed on the commit would leave exactly
            the connections that could not be closed still emitting. ``revoked``
            is the latch that covers all four post-decision states.

            The close itself is unaffected: ``_ConnectionRevocation`` reaches the
            transport through the adapter's ``close``, never through ``send_json``.

            **Delegated control frames use the same lease as protected sends.** The
            revoked read and the actual ``send_json`` must be one critical section:
            without the lease, a control frame can pass the read, suspend in
            upstream's asynchronous send, and then commit after another task has
            published the revocation decision. That violates the connection-wide
            cut-off even though control frames carry no operation payload. The
            lease makes the decision and the send mutually exclusive; a ping or
            keep-alive can therefore wait behind one session read or protected
            send, which is the deliberate head-of-line cost of the stronger
            "nothing after revocation" invariant.
            """
            if message.get("type") not in _INFORMATION_BEARING_FRAME_TYPES:
                async with actor_lease(self.ws_consumer.scope):
                    if self.ws_consumer._revocation.revoked:
                        return
                    await super().send_json(message)
                return
            await send_revalidated_operation_frame(self, message, super().send_json)

    class GraphQLWebSocketConsumer(base_consumer_cls):
        """The package's WebSocket GraphQL consumer: upstream plus revalidation.

        Three ``super()``-delegating hooks - one per protocol for operation
        admission, one on the shared adapter seam for outbound
        information-bearing frames - all resolving through the module's shared
        decision function. Everything else (the handshake, the subprotocol
        negotiation, the message loop, the operation lifecycle, the teardown) is
        upstream's, unchanged. This is deliberately not a second GraphQL protocol
        engine (spec-046 Decision 11).

        ``revalidation_window`` rides as an ``as_asgi()`` initkwarg rather than a
        class attribute, so one cached consumer class serves every router
        instance and two routers may carry two different windows. The revocation
        state machine is per-INSTANCE for the same structural reason: revocation
        is connection-scoped, and one consumer instance is exactly one connection
        - which is also what makes the close attempt it owns a connection-lifetime
        task rather than an operation-lifetime one. The lock that guards it is NOT
        an instance attribute, and the asymmetry is the point: exclusion has to
        reach a second state machine this class cannot see, so it lives on the ASGI
        scope (``utils/sessions.py::actor_lease``) - which is the same
        one-object-per-connection lifetime, reachable from the auth layer's own
        ``logout`` without either layer importing the other.

        **Maximum connection lifetime** (spec-046 Decision 12). The package
        imposes none, and that is a decision rather than an omission: there is no
        correct default - the right lifetime for a dashboard subscription and for
        a short-lived request-response socket differ by orders of magnitude - and
        a framework-imposed disconnect would be a visible behavior change for
        every subscription consumer. The enforcement seam is
        ``DjangoGraphQLProtocolRouter(..., websocket_consumer_class=...)``: an
        injected class can set upstream's ``connection_init_wait_timeout`` and
        ``keep_alive`` constructor knobs and can close the socket on its own
        schedule. A hard lifetime bound belongs to the ASGI server or the
        reverse proxy, which own the connection.

        What revalidation does and does not buy, stated precisely because the
        weaker reading of it was wrong: **a revoked actor cannot admit another
        operation or emit another information-bearing operation frame**.
        Detection is event-boundary-driven, not an asynchronous promise to
        interrupt an idle resolver at the instant an external logout occurs - so
        the security-relevant bound is the revalidation window plus the wait for
        the connection's next protected checkpoint, while socket lifetime, idle
        timeout, and connection count stay transport-resource policy the layers
        above own.
        """

        graphql_transport_ws_handler_class = _RevalidatingTransportWSHandler
        graphql_ws_handler_class = _RevalidatingGraphQLWSHandler
        websocket_adapter_class = _RevocationGatedWebSocketAdapter

        def __init__(
            self,
            *args: Any,
            revalidation_window: float = _DEFAULT_REVALIDATION_WINDOW,
            **kwargs: Any,
        ) -> None:
            # Stored BEFORE ``super().__init__``: upstream's initializer starts
            # the consumer's own machinery, and the checkpoints read both of these
            # off the view / adapter's consumer.
            self.revalidation_window = revalidation_window
            self._revocation = _ConnectionRevocation()
            super().__init__(*args, **kwargs)

        async def disconnect(self, code: int) -> None:
            """Let upstream tear the connection down, then settle its close attempt.

            After ``super()``, deliberately: upstream's own ``disconnect`` awaits
            the connection's message-loop task, which is what cancels and awaits
            every registered operation, and this connection's close attempt is a
            task it owns and must not outlive. Settling it here is what makes the
            attempt survivable in the first place - a client may cancel the
            operation that started it (``complete`` / ``stop``) at any point,
            including while the transport has the close back-pressured, and the
            close must still be finished and recorded by somebody.

            ``finally`` and not a second statement: upstream's teardown is the part
            that can be cancelled (an ASGI server shutting the application down) or
            raise, and settlement is the connection's last chance to end a task it
            owns. Sequencing it after an unguarded ``await`` would skip it in exactly
            the cases that produce an orphan.
            """
            try:
                await super().disconnect(code)
            finally:
                await self._revocation.settle()

    return GraphQLWebSocketConsumer


# ---------------------------------------------------------------------------
# The WebSocket Host boundary (spec-046 Decision 19). Independent of everything
# above: it runs once per handshake, before authentication and before any
# consumer exists, and knows nothing about GraphQL, sessions or revalidation.
# ---------------------------------------------------------------------------

#: The ASGI header names that participate in Django's Host decision, mapped to the
#: ``META`` keys ``HttpRequest._get_raw_host`` reads them under. Both are projected
#: unconditionally; which one WINS is ``USE_X_FORWARDED_HOST``'s decision, made by
#: Django inside ``_get_raw_host`` - never by this projection - which is exactly
#: what makes the WebSocket answer follow the HTTP one for free.
_HOST_META_KEYS_BY_HEADER = {"host": "HTTP_HOST", "x-forwarded-host": "HTTP_X_FORWARDED_HOST"}


def _host_validation_request(scope: Any) -> HttpRequest:
    """Project one handshake scope's Host metadata into a minimal Django request.

    The whole package-owned half of the Host boundary: everything after this is
    ``HttpRequest.get_host()``. The projection reproduces
    ``django/core/handlers/asgi.py::ASGIRequest.__init__``'s treatment of the
    headers it covers, item by item, so that a WebSocket handshake and an HTTP
    request carrying the same bytes get the same verdict:

    - **casing is normalized, not trusted.** ASGI says header names arrive as
      lowercase bytes; Django's own adapter still calls ``.upper()`` rather than
      relying on it, and so does this (via ``.lower()`` on the decoded name).
    - **duplicates are comma-joined**, the same reduction Django's adapter applies
      (#"join(value) for name"). That is the load-bearing choice for an ambiguous
      handshake: two ``Host`` headers become ``"a,b"``, which is not a valid host,
      so ``get_host()`` refuses it instead of one of the two being silently picked.
    - **header bytes are decoded Latin-1**, the Django/ASGI transport convention
      that Django's adapter and Channels' ``OriginValidator`` both use.
    - **``scope["server"]`` supplies ``SERVER_NAME`` / ``SERVER_PORT``**, with
      Django's own ``"unknown"`` / ``"0"`` fallback when the scope carries no
      server, because that pair is what ``_get_raw_host`` reconstructs the host
      from when no host header is present at all.

    A minimal ``HttpRequest`` rather than an ``ASGIRequest`` (Decision 19's
    rejected alternative): ``ASGIRequest.__init__`` expects an HTTP scope - method,
    path, query string, a body file - and does work this question does not need.
    What ``get_host()`` reads is a handful of ``META`` keys, so those are what get
    projected.

    Two ``META`` keys are deliberately NOT projected, and the omission is provably
    verdict-neutral rather than merely small:

    - ``HTTP_X_FORWARDED_PORT`` (``USE_X_FORWARDED_PORT``), which
      ``HttpRequest.get_port`` consults; and
    - the header named by ``SECURE_PROXY_SSL_HEADER``, which ``HttpRequest.scheme``
      consults and ``is_secure()`` answers from.

    Both feed **only** the no-host-header branch of ``_get_raw_host``, and there
    they decide one thing: whether the reconstructed host gets a ``":port"`` suffix.
    ``get_host()`` then splits that suffix straight back off
    (``split_domain_port``) and matches ``ALLOWED_HOSTS`` against the **domain**
    alone, so neither setting can change the allow/deny outcome - only the string a
    caller would have got back, which this boundary discards. Projecting them would
    add surface for no behavior, and the reason is recorded here so a later reader
    does not "complete" the projection on symmetry grounds.
    """
    request = HttpRequest()
    collected: dict[str, list[str]] = {}
    for raw_name, raw_value in scope.get("headers", ()):
        meta_key = _HOST_META_KEYS_BY_HEADER.get(raw_name.decode("latin1").lower())
        if meta_key is not None:
            collected.setdefault(meta_key, []).append(raw_value.decode("latin1"))
    request.META.update({key: ",".join(values) for key, values in collected.items()})
    if server := scope.get("server"):
        request.META["SERVER_NAME"] = server[0]
        request.META["SERVER_PORT"] = str(server[1])
    else:
        request.META["SERVER_NAME"] = "unknown"
        request.META["SERVER_PORT"] = "0"
    return request


class DjangoWebSocketHostValidator:
    """Deny a WebSocket handshake whose ``Host`` Django's own boundary refuses.

    A package-owned, UNSUPPORTED-to-import ASGI middleware (spec-046 Decision 19),
    composed by
    ``routers.py`` as the OUTERMOST WebSocket wrapper:
    ``DjangoWebSocketHostValidator(AllowedHostsOriginValidator(AuthMiddlewareStack(
    URLRouter(...))))``. Outermost is what makes the denial land before the session
    middleware runs, before ``scope["user"]`` is resolved, and before any consumer
    is constructed - a handshake addressed to a host this deployment never allowed
    must not reach the machinery that authenticates it.

    Its contract is "adapt the ASGI handshake and invoke Django's Host boundary",
    never "reimplement Django Host validation": the projection is
    ``_host_validation_request`` and the decision is ``HttpRequest.get_host()``. A
    consumer who wants a different Host policy configures ``ALLOWED_HOSTS``,
    exactly as they would for HTTP; there is no package setting to learn.

    Not exported (no ``__all__`` entry here, and neither ``routers.py::__all__``
    nor the package root names it). The name is deliberately NOT
    underscore-prefixed the way this module's other new classes are, and the
    difference is worth stating rather than leaving as an inconsistency: it is
    named in the router's own construction-time hint text
    (``routers.py::_UNUSABLE_WEBSOCKET_CONSUMER_HINT`` /
    ``_FACTORY_CONTRACT_HINT``) and in ``routers.py``'s composition docstrings, so a
    consumer reads this exact spelling in an error message and must be able to grep
    for it. "Private" here therefore means **unsupported to import or subclass** -
    an ``__all__`` and documentation contract, not an import-time one - and an
    absent underscore is not a promise of stability.

    It is applied by the router, so an injected ``websocket_consumer_class`` sits
    inside it by construction - which is what finally makes Decision 11's "an
    injected consumer cannot escape Host/Origin validation" true rather than
    aspirational.
    """

    def __init__(self, application: Any) -> None:
        self.application = application

    async def __call__(
        self,
        scope: Any,
        receive: Any,
        send: Any,
    ) -> None:
        """Validate the handshake's ``Host`` through Django, then delegate or deny."""
        try:
            _host_validation_request(scope).get_host()
        except DisallowedHost:
            # The ONLY exception normalized into a denial, and the denial is
            # Channels' own consumer rather than a package-authored close, so a
            # refused ``Host`` is byte-identical on the wire to a refused
            # ``Origin`` - the wire cannot tell which of the two checks fired.
            # Imported here, in the arm that needs it: this module stays
            # ``channels``-free at import time so ``routers.py`` can import it
            # above its own soft-dependency guard, and by the time any handshake
            # arrives ``routers.py`` has already imported this very module
            # (``AllowedHostsOriginValidator`` lives in it) to build the router.
            from channels.security.websocket import WebsocketDenier

            await WebsocketDenier()(scope, receive, send)
            return
        # Every other exception propagates deliberately (spec-046 Edge cases
        # #"The Host projection must not swallow its own bugs"): a projection bug
        # that denied every handshake would be indistinguishable from correct
        # ``ALLOWED_HOSTS`` enforcement.
        await self.application(scope, receive, send)
