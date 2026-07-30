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
one second before a logout kept emitting results for as long as it lived
(spec-046 review round 2, Blocker 1).

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
keep-alive ``ka``, and every other connection-control frame are delegated
untouched: they carry no operation information, and one of them (``complete``) is
what upstream's own cancellation path emits while a socket is being torn down.

**Revocation is connection-scoped.** The first failed validation - at either
checkpoint - atomically marks the connection revoked, suppresses the pending
frame, closes the whole socket with upstream's own ``4403`` / ``"Forbidden"``,
unwinds the current operation through cancellation, and lets upstream's existing
disconnect / shutdown path cancel and await every remaining registered operation.
No protocol-specific operation error is sent first, at EITHER checkpoint: the
actor is connection-scoped so the close IS the rejection, an error-then-close
sequence would only add protocol asymmetry and another race, and - decisively -
an admission-time error frame is itself one of the gated frame types, so it would
be validated against the same already-revoked actor, suppressed, and replaced by
this close anyway. Exempting that one frame from the gate to let it through would
be precisely the disclosure distinction the gated set exists to avoid.
``scope["user"]`` is never downgraded to anonymous - a revoked session must not
quietly become an anonymous one.

**One lock, held through the send.** A single connection-local ``asyncio.Lock``
spans the validation / cache decision, the revoked-state transition, AND the
actual information-bearing send. Releasing it after validation would let one
sibling task pass validation, another detect revocation and begin closing, and the
first then emit its previously authorized payload. The cost is stated rather than
hidden: this is a per-connection serialization point on the outbound hot path, so
when a validation needs a session-store read every concurrent operation waiting to
emit on that socket waits for that read. That head-of-line behavior is accepted
because it is the mechanism that makes "no sibling payload escapes after
revocation is observed" true, and it serializes exactly one connection's protected
frames - never unrelated connections.

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
the whole point of the Host boundary below), this package's logger, and
``exceptions.ConfigurationError`` / ``exceptions.describe_value``.
``channels.auth.get_user`` and the package's session-store resolver are imported
**inside** the revalidation coroutine (the
``auth/mutations.py::_channels_http_login_establish`` precedent),
``channels.security.websocket.WebsocketDenier`` **inside** the Host validator's
denial arm, and neither the two protocol handler base classes nor upstream's
WebSocket adapter are imported at all - all three are read off the base consumer
class the factory is handed, so an upstream re-point is tracked for free.
``views.py`` does not import this module, so the package's Django GraphQL view
stays adoptable without the soft dependency.

The session-store resolver the revalidation reaches is
``utils/sessions.py::session_store_class`` and deliberately NOT
``auth/sessions.py``'s re-export of it: ``auth`` is structurally opt-in
(spec-040 Decision 3) and its ``__init__`` eagerly imports ``.mutations`` /
``.queries``, so importing that submodule would register the whole GraphQL auth
subsystem on the event loop the first time an authenticated socket ran an
operation - for a resolver that only reads ``SESSION_ENGINE`` (spec-046 review,
the import-boundary finding). Nothing on this module's revalidation path imports
``django_strawberry_framework.auth``, and a test asserts exactly that.

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
import math
import time
from collections.abc import Awaitable, Callable
from typing import Any

from django.core.exceptions import DisallowedHost
from django.http import HttpRequest

from . import logger
from .exceptions import ConfigurationError, describe_value

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

#: The frame types that carry operation information, and therefore the ones the
#: outbound checkpoint gates: ``next`` (graphql-transport-ws), ``data`` (legacy
#: graphql-ws), and the operation-scoped ``error`` both protocols use for
#: pre-execution and other operation errors. Every other frame type either belongs
#: to connection control (``connection_ack``, ``connection_error``, ``ping``,
#: ``pong``, ``ka``) or announces an ending rather than a payload (``complete``),
#: and is delegated to upstream unchanged.
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
    ``ConfigurationError``, the same explicit ``bool`` rejection (because
    ``isinstance(True, int)`` is ``True``), and the same ``got {type} {value!r}``
    tail. A non-finite value (``nan`` / ``inf``) is rejected too, and the reason
    is unusability rather than a ceiling: ``nan`` loses every comparison, so a
    window spelled that way would silently never expire and never say why, and
    ``inf`` is the saturation sentinel a failed computation produces rather than
    a number of seconds any deployment chose. Both are far better as a loud
    construction-time failure. The router calls this, so an unusable window is a
    construction error and never a per-operation one.

    What is deliberately NOT rejected, so that rationale is not read as more than
    it is: a finite but astronomical window. ``10**300`` and ``1e308`` are
    accepted, and a window that large is operationally "never revalidate again"
    (spec-046 review W3-4). The package imposes no upper bound, for the same
    reason ``GraphQLWebSocketConsumer`` imposes no maximum connection lifetime
    (Decision 12): there is no correct default, any constant would be invented
    here rather than derived from anything, and a positive window is a deliberate
    consumer trade-off - one session read per authenticated checkpoint against a
    named revocation delay - that the deployment can compute and this function
    has no standing to second-guess. The guard is about values the package cannot
    *use*, not about values it disapproves of.

    The ``float`` conversion is a GUARDED step of its own, and it happens BEFORE
    any numeric predicate runs. A sufficiently large ``int`` (``10**10000``) is a
    perfectly ordinary Python object that no ``isinstance`` check rejects, yet it
    has no ``float`` image: ``math.isfinite`` and ``float()`` both raise
    ``OverflowError`` on it. Reading the domain first would therefore have let a
    hostile or fat-fingered configuration escape the typed boundary with a raw
    ``OverflowError`` instead of the promised ``ConfigurationError`` (spec-046
    review, the enormous-window finding). Converting first also means the sign and
    finiteness checks below run on a real ``float``, which is the value the
    consumer will actually compare against.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
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
    *mutations*, while this is a read of a private store, and both interleavings
    with a concurrent ``logout`` are safe (either the actor is still valid, or it
    is already gone and the connection is revoked). The lock it does take is the
    connection's own revocation lock, which exists for a different reason
    entirely: it makes the validate-transition-send sequence atomic against
    sibling operations on the same socket.

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
    async with consumer._revocation_lock:
        if consumer._revocation_observed:
            # Already revoked and already closed by whichever checkpoint saw it
            # first. A client can still have pipelined this frame before the
            # close reached it, so the arm is reachable rather than defensive -
            # and it must stay read-free, which is what makes the denial stable
            # at no further database cost.
            return False
        if await _actor_is_current(consumer):
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
    place: the lock spans the validation / cache decision, the revoked-state
    transition, and ``send`` itself. See the module docstring for why holding it
    through the send - and the per-connection head-of-line blocking that buys -
    is the point rather than an oversight.

    ``send`` is the adapter's own ``super().send_json`` bound method, so the
    delegation is upstream's serialize-and-write path, unchanged.

    The current operation is then unwound through **cancellation** rather than by
    raising ``asyncio.CancelledError`` from this frame. The difference matters:
    cancelling delivers the error at the operation's next suspension point, which
    is inside ``result_source.__anext__()`` - so the subscription generator's own
    ``finally`` runs and the generator is closed. Raising here instead would
    unwind the ``async for`` *body*, leaving the generator suspended for the
    interpreter's asyncgen finalizer to close at an unrelated moment. Upstream's
    two loops then diverge exactly as their own code says: legacy
    ``handle_async_results`` catches ``asyncio.CancelledError`` and sends
    ``complete``, transport-ws ``run_operation`` does not and emits nothing.
    Either way no suppressed payload leaves and no task leaks, because the
    surviving registrations are cleaned up by upstream's own
    ``shutdown()`` / ``cleanup()`` on disconnect.
    """
    consumer = websocket.ws_consumer
    async with consumer._revocation_lock:
        if not consumer._revocation_observed and await _actor_is_current(consumer):
            await send(message)
            return
        await _revoke_connection(websocket)

    # Outside the lock, and only ever the OPERATION task: cancelling the
    # connection's own message-loop task (upstream's ``run_task``) would abort
    # the very disconnect/shutdown path that has to cancel and await the
    # remaining operations. The main task reaches this function for the
    # protocols' subscription-limit ``error`` frame, where the close alone is
    # the whole rejection and there is no operation of ours to unwind.
    task = asyncio.current_task()
    if task is not consumer.run_task:
        task.cancel()


async def _actor_is_current(consumer: Any) -> bool:
    """Return whether the connection's scope actor is valid **now**.

    The ONE decision both checkpoints await (spec-046 Helper-reuse: "every
    decision - window expiry, session reload, actor write-back - lives in the
    shared function"). It never sends, never closes, and never cancels: the two
    callers own the response to a ``False``, which is what keeps admission and
    the outbound gate from drifting apart.

    Callers hold the connection's revocation lock, so the window comparison, the
    reload, and the cache write below are atomic against every sibling
    checkpoint on the same socket.
    """
    scope = consumer.scope
    actor = scope.get("user")
    # The anonymous carve-out: no session actor to revalidate, so only an
    # authenticated socket pays the cost. Same predicate as
    # ``auth/mutations.py::_authenticated_actor_or_none``, deliberately spelled
    # rather than imported - that helper is private to the auth-mutation
    # surface, and importing it would pull the whole ``auth`` package (and the
    # Strawberry type stack behind it) into a transport-layer coroutine. If a
    # THIRD site ever needs this predicate, promote it to
    # ``utils/permissions.py`` beside ``ChannelsRequestAdapter`` instead.
    if actor is None or not actor.is_authenticated:
        return True

    # Plain attribute access, deliberately: ``GraphQLWebSocketConsumer.__init__``
    # always assigns ``revalidation_window`` BEFORE ``super().__init__``, and the
    # class is function-local to the factory, so no third party can construct one
    # without it. A ``getattr`` default here would be unreachable defensiveness on
    # the one line that decides whether a session read happens - and if a future
    # refactor did drop the attribute, the default would silently switch the
    # deployment to "revalidate at every checkpoint" (a performance cliff that
    # lives in an expression, where statement coverage cannot see it) instead of
    # failing loudly (spec-046 review round 2, L4).
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
    """Mark the connection revoked and close the socket - exactly once.

    The transition is set BEFORE the close is awaited, so a sibling task that
    acquires the revocation lock next observes "revoked" immediately and takes
    neither a second session read nor a second close. Idempotence is not a
    nicety here: both checkpoints call this, and a socket that is closed twice
    would make upstream emit a second ``websocket.close`` after the first.

    The close goes through the adapter (upstream's own
    ``ChannelsWebSocketAdapter.close`` -> ``consumer.close``) rather than around
    it, so a consumer that derives its own adapter keeps owning the write.
    """
    consumer = websocket.ws_consumer
    if consumer._revocation_observed:
        return
    consumer._revocation_observed = True
    await websocket.close(code=_REVOCATION_CLOSE_CODE, reason=_REVOCATION_CLOSE_REASON)


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
        """``graphql-transport-ws`` admission: revalidate, then delegate to upstream."""

        # ``message`` is upstream's ``SubscribeMessage`` TypedDict; annotated
        # ``Any`` deliberately, so the factory keeps importing nothing from
        # upstream's deep protocol-types modules.
        async def handle_subscribe(self, message: Any) -> None:
            if not await revalidate_operation_actor(self):
                return
            await super().handle_subscribe(message)

    class _RevalidatingGraphQLWSHandler(base_consumer_cls.graphql_ws_handler_class):
        """Legacy ``graphql-ws`` admission: revalidate, then delegate to upstream."""

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
            if message.get("type") not in _INFORMATION_BEARING_FRAME_TYPES:
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
        lock and the revoked flag are per-INSTANCE for the same structural
        reason: revocation is connection-scoped, and one consumer instance is
        exactly one connection.

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
            # the consumer's own machinery, and the checkpoints read all three of
            # these off the view / adapter's consumer. ``asyncio.Lock()`` binds
            # its loop lazily on first use (Python 3.10+), and Channels builds one
            # consumer instance per connection inside the serving loop, so the
            # lock is always this connection's.
            self.revalidation_window = revalidation_window
            self._revocation_lock = asyncio.Lock()
            self._revocation_observed = False
            super().__init__(*args, **kwargs)

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
    absent underscore is not a promise of stability (spec-046 review round 2, L6).

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
