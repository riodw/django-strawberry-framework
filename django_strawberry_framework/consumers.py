"""The package's WebSocket GraphQL consumer and its per-operation actor revalidation.

``build_revalidating_consumer_class(GraphQLWSConsumer)`` returns
``GraphQLWebSocketConsumer`` - a thin ``strawberry.channels.GraphQLWSConsumer``
subclass that revalidates the session actor **before every operation** and
writes the refreshed actor back onto ``scope["user"]`` (spec-065 Decision 11).
An established socket therefore cannot keep executing on a session that was
revoked, flushed, or whose user was disabled after the handshake.

The class is built by ``routers.py::_build_router_class`` inside the same
soft-``channels`` guard and the same ``_ROUTER_CLASS`` cache the router itself
lives in, so its lifetime is exactly the router class's; this module caches
nothing. It is deliberately **not** exported (no ``__all__`` here, and neither
``routers.py::__all__`` nor the package root names it): the supported choices
are the package default or an injected consumer of your own, passed as
``DjangoGraphQLProtocolRouter(..., websocket_consumer_class=...)``.

Importing this module is ``channels``-free, which is what lets ``routers.py``
import it above its own guard: the module level reaches only for the standard
library, ``graphql`` (the hard dependency Strawberry already carries, for the
rejection's wire shape), this package's logger, and
``exceptions.ConfigurationError`` / ``exceptions.describe_value``.
``channels.auth.get_user`` and the package's session-store resolver are imported
**inside** the revalidation coroutine (the
``auth/mutations.py::_channels_http_login_establish`` precedent), and the two
protocol handler base classes are never imported at all - they are read off the
base consumer class the factory is handed, so an upstream re-point is tracked
for free. ``views.py`` does not import this module, so the package's Django
GraphQL view stays adoptable without the soft dependency.

The session-store resolver the revalidation reaches is
``utils/sessions.py::session_store_class`` and deliberately NOT
``auth/sessions.py``'s re-export of it: ``auth`` is structurally opt-in
(spec-040 Decision 3) and its ``__init__`` eagerly imports ``.mutations`` /
``.queries``, so importing that submodule would register the whole GraphQL auth
subsystem on the event loop the first time an authenticated socket ran an
operation - for a resolver that only reads ``SESSION_ENGINE`` (spec-065 review,
the import-boundary finding). Nothing on this module's revalidation path imports
``django_strawberry_framework.auth``, and a test asserts exactly that.
"""

from __future__ import annotations

import math
import time
from typing import Any

from graphql import GraphQLError

from . import logger
from .exceptions import ConfigurationError, describe_value

#: The default revalidation window, in seconds: ``0.0`` revalidates every
#: operation. Spelled ONCE here and imported by ``routers.py`` for its
#: ``websocket_revalidation_window=`` keyword default, so the number cannot
#: drift between the constructor and the consumer (spec-065 Decision 11).
_DEFAULT_REVALIDATION_WINDOW = 0.0

#: The single rejection message, shared by both protocols and by the fail-closed
#: degrade. A transport-capability statement in the same family as the shipped
#: WebSocket auth-mutation rejections - deliberately NOT the undifferentiated
#: failed-login envelope, and deliberately identical for "the session is gone"
#: and "the revalidation read failed" so the wire discloses nothing about which
#: (spec-065 #"Error shapes").
_REVOKED_SESSION_MESSAGE = (
    "The session for this WebSocket connection is no longer valid. Reconnect with a "
    "current session to continue."
)

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
        "converts to a float (0.0 revalidates the session actor on every operation); got "
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
    (spec-065 review W3-4). The package imposes no upper bound, for the same
    reason ``GraphQLWebSocketConsumer`` imposes no maximum connection lifetime
    (Decision 12): there is no correct default, any constant would be invented
    here rather than derived from anything, and a positive window is a deliberate
    consumer trade-off - one session read per authenticated operation against a
    named revocation delay - that the deployment can compute and this function
    has no standing to second-guess. The guard is about values the package cannot
    *use*, not about values it disapproves of.

    The ``float`` conversion is a GUARDED step of its own, and it happens BEFORE
    any numeric predicate runs. A sufficiently large ``int`` (``10**10000``) is a
    perfectly ordinary Python object that no ``isinstance`` check rejects, yet it
    has no ``float`` image: ``math.isfinite`` and ``float()`` both raise
    ``OverflowError`` on it. Reading the domain first would therefore have let a
    hostile or fat-fingered configuration escape the typed boundary with a raw
    ``OverflowError`` instead of the promised ``ConfigurationError`` (spec-065
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


async def revalidate_operation_actor(
    handler: Any,
    operation_id: str,
    *,
    errors_as_list: bool,
) -> bool:
    """Revalidate the scope actor for one operation; return whether it may proceed.

    The ONE decision function both protocol pre-hooks await (spec-065
    Helper-reuse: "every decision - window expiry, session reload, actor
    write-back, reject-or-continue - lives in the shared function"). It returns
    ``True`` to let upstream run the operation, or sends the operation's own
    ``error`` message and returns ``False``. The socket is never closed: both
    protocols carry a per-operation error channel, and this mirrors their own
    pre-execution refusals.

    Why here and not elsewhere (spec-065 Decision 11's rejected alternatives):
    ``get_context`` runs once per connection, before either protocol's message
    loop, so it is not a per-operation seam; the consumer's ``receive()`` sees
    every frame including keep-alives and can only close the socket rather than
    fail one operation.

    ``handler`` is duck-typed on purpose - all this needs is upstream's
    ``connection_acknowledged`` flag (both handlers set it in ``__init__`` and
    flip it in ``handle_connection_init``), ``view`` (which IS the consumer, so
    the ASGI scope is ``handler.view.scope``), and ``send_message``.

    The read is alias-explicit **by delegation** (spec-065 Edge cases): the
    session load and the user load both resolve their alias through Django's own
    ``router.db_for_read`` - the deployment's explicit routing decision, never a
    hardcoded ``"default"`` - which is the same authority
    ``utils/permissions.py::resolve_auth_aliases`` reads. It takes **no** lock:
    ``auth/sessions.py::scope_session_lock`` serializes session *mutations*,
    while this is a read of a private store, both interleavings with a
    concurrent ``logout`` are safe (either the actor is still valid, or it is
    already gone and the operation is denied), and taking a mutation lock on the
    socket's critical path would add contention for nothing.

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

    scope = handler.view.scope
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

    window = getattr(handler.view, "revalidation_window", _DEFAULT_REVALIDATION_WINDOW)
    # ``-inf`` reads as "never revalidated, i.e. infinitely long ago", which
    # keeps the expiry test one comparison with no sentinel branch of its own.
    # With the default window of ``0.0`` the left arm short-circuits, so nothing
    # is ever written to the scope.
    if window > 0.0 and _monotonic() - scope.get(_REVALIDATED_AT_SCOPE_KEY, -math.inf) < window:
        return True

    try:
        refreshed = await _refreshed_actor(scope)
    except Exception:
        # Fail closed (spec-065 Edge cases #"A revalidation database error must
        # fail closed"): a store or auth failure denies the operation and is
        # never a fall back to the cached actor. ``Exception``, not
        # ``BaseException`` - an ``asyncio.CancelledError`` from task teardown
        # must propagate rather than be converted into a denial.
        logger.exception(
            "GraphQLWebSocketConsumer: the per-operation session revalidation failed; "
            "the operation is denied (fail-closed) rather than executing on the "
            "connection's cached actor.",
        )
        refreshed = None

    if refreshed is None or not refreshed.is_authenticated:
        # The stale actor stays on the scope. Downgrading it to ``AnonymousUser``
        # would let every later operation execute as an anonymous session; leaving
        # it makes them all take this same path and be denied identically
        # (spec-065 Decision 11).
        formatted = GraphQLError(_REVOKED_SESSION_MESSAGE).formatted
        await handler.send_message(
            {
                "id": operation_id,
                "type": "error",
                # The one irreducible per-protocol difference: graphql-transport-ws
                # carries a LIST of formatted errors, legacy graphql-ws a single one.
                "payload": [formatted] if errors_as_list else formatted,
            },
        )
        return False

    # The write-back (spec-065 Decision 11): ``channels.auth``'s own ``login`` /
    # ``logout`` replace ``scope["user"]`` the same way, and the Channels request
    # adapter reads that key - so every surface reached through
    # ``request_from_info`` observes the fresh actor with no new plumbing.
    scope["user"] = refreshed
    if window > 0.0:
        scope[_REVALIDATED_AT_SCOPE_KEY] = _monotonic()
    return True


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
    """Return a ``base_consumer_cls`` subclass that revalidates per operation.

    A pure factory: no cache, no soft-dependency guard, and no import of
    ``channels`` or ``strawberry``. ``routers.py`` calls it once inside the
    ``try: from strawberry.channels import GraphQLWSConsumer`` block that already
    owns both, so a degraded install still raises that module's single
    ``_STRAWBERRY_CHANNELS_BROKEN_HINT`` and this module needs no guard of its
    own.

    The two handler bases are read off ``base_consumer_cls``'s
    ``graphql_transport_ws_handler_class`` / ``graphql_ws_handler_class``
    attributes, which the view resolves at dispatch time. Those attributes are
    *subscripted generic aliases* (``BaseGraphQLTransportWSHandler[Context,
    RootValue]``), not plain classes; deriving from them works through
    ``__mro_entries__`` and is the correct shape here - it imports neither
    handler module and tracks an upstream re-point automatically.
    """

    class _RevalidatingTransportWSHandler(base_consumer_cls.graphql_transport_ws_handler_class):
        """``graphql-transport-ws``: revalidate, then delegate to upstream."""

        # ``message`` is upstream's ``SubscribeMessage`` TypedDict; annotated
        # ``Any`` deliberately, so the factory keeps importing nothing from
        # upstream's deep protocol-types modules.
        async def handle_subscribe(self, message: Any) -> None:
            if not await revalidate_operation_actor(
                self,
                message["id"],
                errors_as_list=True,
            ):
                return
            await super().handle_subscribe(message)

    class _RevalidatingGraphQLWSHandler(base_consumer_cls.graphql_ws_handler_class):
        """Legacy ``graphql-ws``: revalidate, then delegate to upstream."""

        # ``message`` is upstream's ``StartMessage`` TypedDict; see above.
        async def handle_start(self, message: Any) -> None:
            if not await revalidate_operation_actor(
                self,
                message["id"],
                errors_as_list=False,
            ):
                return
            await super().handle_start(message)

    class GraphQLWebSocketConsumer(base_consumer_cls):
        """The package's WebSocket GraphQL consumer: upstream plus revalidation.

        Two ``super()``-delegating pre-hooks, one per protocol, both awaiting
        ``revalidate_operation_actor``. Everything else - the handshake, the
        subprotocol negotiation, the message loop, the operation lifecycle - is
        upstream's, unchanged. This is deliberately not a second GraphQL
        protocol engine (spec-065 Decision 11).

        ``revalidation_window`` rides as an ``as_asgi()`` initkwarg rather than a
        class attribute, so one cached consumer class serves every router
        instance and two routers may carry two different windows.

        **Maximum connection lifetime** (spec-065 Decision 12). The package
        imposes none, and that is a decision rather than an omission: there is no
        correct default - the right lifetime for a dashboard subscription and for
        a short-lived request-response socket differ by orders of magnitude - and
        a framework-imposed disconnect would be a visible behavior change for
        every subscription consumer. The enforcement seam is
        ``DjangoGraphQLProtocolRouter(..., websocket_consumer_class=...)``: an
        injected class can set upstream's ``connection_init_wait_timeout`` and
        ``keep_alive`` constructor knobs and can close the socket on its own
        schedule. A hard lifetime bound belongs to the ASGI server or the
        reverse proxy, which own the connection. And with per-operation
        revalidation on, the security-relevant bound is the revalidation window
        rather than the connection lifetime, because a revoked session stops
        executing without the socket having to end.
        """

        graphql_transport_ws_handler_class = _RevalidatingTransportWSHandler
        graphql_ws_handler_class = _RevalidatingGraphQLWSHandler

        def __init__(
            self,
            *args: Any,
            revalidation_window: float = _DEFAULT_REVALIDATION_WINDOW,
            **kwargs: Any,
        ) -> None:
            # Stored BEFORE ``super().__init__``: upstream's initializer starts
            # the consumer's own machinery, and the pre-hooks read this attribute
            # off the view.
            self.revalidation_window = revalidation_window
            super().__init__(*args, **kwargs)

    return GraphQLWebSocketConsumer
