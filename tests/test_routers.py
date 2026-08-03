"""Channels router tests: the protocol split, WebSocket wrappers and consumer seam, lazy imports.

Both dependency states are exercised (spec-041 Decision 8, as amended by
spec-046 Decision 2):

- **channels-present** - construction / composition (the WebSocket middleware
  wrapping order behind intent-named unwrap helpers, and the ``"http"`` value's
  object identity with the supplied Django application), real execution through
  Channels' in-process communicators, the package-realistic request contract (a
  resolver reading the actor through ``request_from_info()``), and the
  authenticated-session round trip;
- **channels-absent** - simulated via the shared ``sys.modules[...] = None``
  sentinel (``tests/_soft_dependency.py``) + strict ``sys.modules`` eviction with
  the TWO-SIDED restore (the parent package's ``routers`` attribute is
  saved/restored alongside the module entries, so the attribute path and the
  import path never end up holding two live module objects with independent class
  caches);
- **channels-present-but-degraded** - the same eviction discipline with one
  builder submodule set to a ``None`` sentinel, pinning the split actionable error
  shapes.

Transport ownership after spec-046: the router no longer serves GraphQL over
HTTP, so ``HttpCommunicator`` here proves *delegation* - every HTTP path reaches
the supplied Django ASGI application untouched. The request contract, the
schema pass-through with extensions intact, and the authenticated-session round
trip are all proven over the **WebSocket** branch, which is where the package's
own Channels composition (and therefore ``AuthMiddlewareStack``) still lives.
The live HTTP boundary itself is earned over fakeshop's real ``/graphql/`` in
``examples/fakeshop/test_query/test_transport_api.py``.

The WebSocket consumer-injection seam and the actor revalidation matrix (spec-046
Decision 11, Test plan rows 25-30) also live here: the composition rows are
structural, and the revalidation rows drive real sockets through
``WebsocketCommunicator`` on BOTH subprotocols. Decision 13 #"Placement" pins
them at this tier - fakeshop has no ``asgi.py``, so the router half keeps the
documented genuinely-unreachable-live exemption.

Revalidation has **two** checkpoints, and the rows are organized around that
split:

- **admission** - a NEW operation on a revoked session never starts; and
- **the outbound information-bearing frame** - an ALREADY-ADMITTED operation
  (a running subscription, and equally a slow query) can no longer put ``next``
  / ``data`` / an operation-scoped ``error`` on the wire.

Both failures are connection-scoped: the socket is CLOSED with ``4403`` and one
non-disclosing reason, no operation-level error frame is emitted first, and the
rows assert the close rather than a rejection frame.

A third group composes the revalidation with the package's OWN ``logout``
mutation, run on the socket it is sent over rather than through a separate
request. That is the only revocation shape which also replaces ``scope["user"]``
with ``AnonymousUser``, and the only one that runs IN this process against the
very connection a checkpoint is validating, so it is the only one that can
exercise the two things a separate request cannot reach: the connection's
authentication provenance, and the actor lease that keeps a transition and a
checkpoint's whole validate/commit/send sequence mutually exclusive - in both
directions, which is why the group carries a parked-send row and a
parked-transition row rather than one of them. Those rows build their schema per
test, behind a registry-clearing fixture and with every auth import
function-local, so this module's own import stays auth-free.

The execution schema is module-local and ORM-free: the async consumers execute
on the event loop, where sync ORM would raise ``SynchronousOnlyOperation`` -
router behavior is schema-agnostic, so deterministic scalar fields (plus one
one-shot subscription, the only operation type the legacy ``graphql-ws``
protocol can execute) are sufficient (spec-041 Test plan). Every out-of-band
session / user mutation the revalidation rows need therefore rides
``database_sync_to_async``, as the authenticated-session round trip's session
mint already did.

The outbound-checkpoint rows additionally need an operation whose *timeline* the
test body owns - one that has been admitted, has produced a payload, and is
holding it - so the schema carries a controlled multi-yield subscription, a
controlled query, and (on a second schema) a gated ``SchemaExtension``. All three
are driven through ``_OperationController``: no wall-clock sleeps, no polling on
real time, and every release is an explicit ``asyncio.Event``.

The WebSocket **Host** boundary (spec-046 Decision 19, Test plan rows 43-47) is
the module's third subject, and it is deliberately proven by DELEGATION: every
row that asks "which hosts are allowed" asserts the socket's verdict against
Django's own answer for the same value over HTTP - ``_django_http_host_verdict``
builds a real ``WSGIRequest`` through ``RequestFactory`` and calls
``HttpRequest.get_host()`` on it - rather than against a second expectation typed
out here. A hand-written expectation would pass just as happily against a
package-local reimplementation of ``ALLOWED_HOSTS`` matching, which is the exact
thing Decision 19 refuses to write.

One row - the real-second-request logout - additionally needs a *real second
HTTP request* against the socket's own session, so this module doubles as a
probe URLConf: a single
logout view plus ``urlpatterns``, reached through
``override_settings(ROOT_URLCONF=__name__)`` and ``django.test.AsyncClient``.
The socket stays package-tier on the router either way - the probe serves no
GraphQL and exists only to run Django's session lifecycle.
"""

import asyncio
import contextlib
import importlib
import inspect
import json
import logging
import re
import sys
import time
from collections import defaultdict
from collections.abc import AsyncIterator
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import pytest
import strawberry
from channels.auth import AuthMiddleware
from channels.db import database_sync_to_async
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from channels.sessions import CookieMiddleware, SessionMiddleware
from channels.testing import HttpCommunicator, WebsocketCommunicator
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import DisallowedHost
from django.core.handlers.asgi import ASGIRequest
from django.http import HttpRequest, JsonResponse
from django.test import AsyncClient, RequestFactory, override_settings
from django.urls import path

import django_strawberry_framework
import django_strawberry_framework.consumers as consumers_module
import django_strawberry_framework.routers as routers_module
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils import sessions as session_store_module
from django_strawberry_framework.utils.permissions import request_from_info
from tests._soft_dependency import evicted_modules, simulated_absence

# The hint floors are deliberately RE-TYPED literals, matching
# ``tests/rest_framework/test_soft_dependency.py``'s ``_HINT_SUBSTRING``
# discipline: importing the router constants and asserting them against
# themselves could never catch the hint drifting from the dev-group floor.
_HINT_SUBSTRING = "channels>=4.3.2"
# The Strawberry floor the hint recommends must be the floor the package METADATA
# accepts: ``pyproject.toml`` requires ``strawberry-graphql>=0.316.0`` and the
# minimum CI matrix node pins exactly ``0.316.0``, so an older floor here would be
# advice to install a version the install would reject.
_STRAWBERRY_FLOOR_SUBSTRING = "strawberry-graphql>=0.316.0"

# Same discipline for the revocation close and the two new construction hints: a
# RE-TYPED literal, never the imported constant, so a drift fails a test instead
# of asserting itself. ``4403`` / ``"Forbidden"`` is upstream's own
# authorization-refusal close, reused verbatim so a revocation is indistinguishable
# from any other refusal to authorize the socket.
_REVOKED_CLOSE_CODE = 4403
_REVOKED_CLOSE_REASON = "Forbidden"
_UNUSABLE_CONSUMER_SUBSTRING = "GraphQLWSConsumer"
_WINDOW_WITH_CLASS_SUBSTRING = "injected consumer class owns its own revalidation policy"
_FACTORY_CONTRACT_SUBSTRING = "factory(schema=schema)"
_FACTORY_CONVENTION_SUBSTRING = "cannot accept that call"
_ASYNC_FACTORY_SUBSTRING = "make it a plain `def`"

# The two opt-in auth submodules ``auth/__init__`` imports eagerly (spec-040
# Decision 3). The WebSocket revalidation must resolve its session store without
# either of them entering ``sys.modules``, which the import-boundary row asserts.
_AUTH_SUBSYSTEM_PREFIX = "django_strawberry_framework.auth"
_AUTH_SUBSYSTEM_MODULES = (
    f"{_AUTH_SUBSYSTEM_PREFIX}.mutations",
    f"{_AUTH_SUBSYSTEM_PREFIX}.queries",
)

# The two subprotocols the package's mount negotiates, and the per-protocol
# frame names one operation round trip uses: (client operation frame, server
# success frame). The rejection frame is ``"error"`` on both - only its payload
# shape differs, which is what the two rejection rows measure.
_TRANSPORT_WS = "graphql-transport-ws"
_LEGACY_WS = "graphql-ws"
_PROTOCOL_FRAMES = {_TRANSPORT_WS: ("subscribe", "next"), _LEGACY_WS: ("start", "data")}

#: The frame types the outbound checkpoint gates. RE-TYPED, like every other
#: contract literal in this module, so a drift fails a row instead of asserting
#: itself; the structural row that pins the production set against these same three
#: names reads the constant itself.
_GATED_FRAME_TYPES = frozenset({"next", "data", "error"})

#: The frame each protocol gives a CLIENT to cancel one of its own operations
#: (``handle_complete`` / ``handle_stop``, both reaching ``cleanup_operation``).
#: A client can therefore cancel the operation that happened to observe a
#: revocation, at any moment including while the close is still being written -
#: which is why the close attempt is owned by the connection rather than by that
#: operation.
_PROTOCOL_CANCEL_FRAMES = {_TRANSPORT_WS: "complete", _LEGACY_WS: "stop"}

#: Per protocol, a client frame that provokes a DELEGATED (non-information-bearing)
#: reply on an open socket, and the type of the reply upstream writes for it.
#:
#: ``graphql-transport-ws`` has ``ping`` -> ``pong`` (``handle_ping``). The legacy
#: protocol has no ping this router can reach - its ``ka`` keep-alive needs a
#: ``keep_alive`` knob the router does not expose - so the equivalent there is
#: ``stop``, which cancels the named operation's task, whose own
#: ``except asyncio.CancelledError`` answers with ``complete``. Both replies take
#: the adapter's delegated path, which is the one the suppression rows are about;
#: an ``id`` rides both frames because the legacy one needs it and neither
#: protocol's dispatcher rejects an extra key.
_PROTOCOL_PROVOKED_CONTROL = {_TRANSPORT_WS: ("ping", "pong"), _LEGACY_WS: ("stop", "complete")}


# ---------------------------------------------------------------------------
# Module-local execution schema (ORM-free; see module docstring)
# ---------------------------------------------------------------------------


class _OperationController:
    """Own one in-flight operation's timeline from the test body.

    The outbound-checkpoint rows all need the same three-step shape: admit an
    operation while the session is valid, hold it while the session is revoked
    out of band, then release it and watch what the socket does with the payload
    it now holds. That is impossible with a resolver that returns immediately,
    and unreliable with a resolver that sleeps, so the controlled resolvers below
    take every step from an ``asyncio.Event`` this object hands them.

    ``emitted`` is the load-bearing half of the proof: it records what the
    RESOLVER produced. A row asserting only "the wire stayed quiet" cannot tell a
    suppressed payload from a payload that was never generated; asserting that
    result 2 exists in ``emitted`` and never appeared on the wire is what pins the
    gate. ``finalized`` records that the subscription generator's ``finally`` ran,
    i.e. that the operation was really unwound rather than abandoned to the
    interpreter's asyncgen finalizer.

    There is deliberately no operation-task handle here. ``asyncio.current_task()``
    inside a subscription resolver is NOT the operation's task - graphql-core drives
    each value through its own short-lived ``asend`` task, so a handle captured in
    the resolver is already ``done()`` by the time the value reaches the wire, and a
    row waiting on it would prove nothing. ``_OutboundGateProbe.tasks`` is where the
    operation's real task is observable.
    """

    def __init__(self):
        self.started = asyncio.Event()
        self.gates = defaultdict(asyncio.Event)
        self.emitted = []
        self.finalized = False

    def release(self, index):
        """Let the operation produce its ``index``-th (0-based) result."""
        self.gates[index].set()


#: How many results the burst subscription below offers. Large enough that an
#: implementation which cannot stop a revoked operation whose next value is already
#: available drives thousands of suppressed frames instead of one, and small enough
#: that the row stays under a second either way. The number itself pins nothing -
#: the rows assert that exactly ONE value was ever produced.
_BURST_RESULTS = 2000

#: Live controllers, keyed by the ``channel`` argument the controlled resolvers
#: receive. A module-level registry rather than a resolver closure because the
#: schema is built once at import time; every row uses its own channel name, and
#: the autouse fixture clears the registry so no Event outlives its event loop.
_CONTROLLERS = {}


@pytest.fixture(autouse=True)
def _clear_operation_controllers():
    yield
    _CONTROLLERS.clear()


def _controller(channel):
    """Register and return a fresh controller for ``channel``."""
    controller = _OperationController()
    _CONTROLLERS[channel] = controller
    return controller


def _controlled_subscription(channel):
    return f'subscription {{ controlled(channel: "{channel}") }}'


def _burst_subscription(channel, count=_BURST_RESULTS):
    return f'subscription {{ burst(channel: "{channel}", count: {count}) }}'


def _controlled_query(channel):
    return f'{{ controlledPing(channel: "{channel}") }}'


@strawberry.type
class Query:
    @strawberry.field
    def ping(self) -> str:
        return "pong"

    @strawberry.field
    def username(self, info: strawberry.Info) -> str:
        """The authenticated-session probe: the session actor's username."""
        request = request_from_info(info, family_label="FilterSet")
        return request.user.username

    @strawberry.field
    def actor(self, info: strawberry.Info) -> str:
        """Read the scope-backed actor without requiring HTTP-only attributes."""
        request = request_from_info(info, family_label="FilterSet")
        return f"{type(request).__name__}|{request.user.is_anonymous}"

    @strawberry.field
    def actor_identity(self, info: strawberry.Info) -> str:
        """The revalidation-freshness probe (spec-046 row 26): two identity reads.

        A field of its own rather than an extension of ``actor`` (whose exact
        string the request-contract row asserts). Both values are attribute reads
        off whatever object ``scope["user"]`` currently holds, so a stale
        connect-time actor and a revalidation-refreshed one are distinguishable
        without any ORM work in the resolver.
        """
        request = request_from_info(info, family_label="FilterSet")
        return f"{request.user.username}|{request.user.is_staff}"

    @strawberry.field
    async def controlled_ping(self, channel: str) -> str:
        """A query whose RESPONSE is held until the test body releases it.

        The non-subscription half of the outbound checkpoint: upstream's
        ``run_operation`` sends a query's single result through the very same
        ``Operation.send_next`` a subscription's results take, so a slow query
        revoked between admission and response must be gated identically. Only
        ``graphql-transport-ws`` can execute it (see ``Subscription.tick``).
        """
        controller = _CONTROLLERS[channel]
        controller.started.set()
        await controller.gates[0].wait()
        controller.emitted.append(f"{channel}-1")
        return "pong"


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def tick(self) -> AsyncIterator[str]:
        """One value, then completion.

        The legacy ``graphql-ws`` protocol reaches Strawberry through
        ``Schema.subscribe``, whose ``allowed_operation_types`` is
        ``(SUBSCRIPTION,)`` - a query sent as ``start`` raises
        ``InvalidOperationTypeError`` inside the operation task and emits no
        frame at all. So the legacy protocol's success baseline has to be a real
        subscription; this is the smallest ORM-free one.
        """
        yield "tock"

    @strawberry.subscription
    async def controlled(self, channel: str) -> AsyncIterator[str]:
        """An unbounded subscription whose every result is released by the test.

        The shape ``tick`` could not be: it stays inside upstream's
        ``async for result in result_source`` loop across several results, which
        is exactly the state the admission checkpoint cannot see again. The loop
        is deliberately unbounded rather than two-shot - after the last released
        result the generator parks on the NEXT gate, so a row can prove the
        ``finally`` ran because the operation was unwound and not because the
        generator happened to be exhausted.
        """
        controller = _CONTROLLERS[channel]
        controller.started.set()
        index = 0
        try:
            while True:
                await controller.gates[index].wait()
                index += 1
                value = f"{channel}-{index}"
                controller.emitted.append(value)
                yield value
        finally:
            controller.finalized = True

    @strawberry.subscription
    async def burst(self, channel: str, count: int) -> AsyncIterator[str]:
        """A subscription whose every later result is ALREADY available.

        The shape ``controlled`` cannot be. Every gate in ``controlled`` is an
        ``await`` that suspends, so a revoked operation there always reaches a
        suspension point on its own. This resolver has none between its yields, so
        the whole loop - resolve, gate, suppress, ask for the next value - can run
        without ever handing control back to the event loop. That is the state a
        revoked operation has to be stopped in, and the one a cancellation REQUEST
        can never reach: the request is only consumed when the task is rescheduled.

        Bounded rather than infinite so that a regressed implementation reports the
        defect instead of hanging the suite.
        """
        controller = _CONTROLLERS[channel]
        controller.started.set()
        try:
            for index in range(1, count + 1):
                value = f"{channel}-{index}"
                controller.emitted.append(value)
                yield value
        finally:
            controller.finalized = True


SCHEMA = strawberry.Schema(query=Query, subscription=Subscription)
_TICK_SUBSCRIPTION = "subscription { tick }"

#: The one channel the gated extension below watches, and the operation it holds.
#: An unknown field, so the operation fails VALIDATION - which is what makes
#: Strawberry answer with a ``PreExecutionError`` and both protocols emit an
#: operation-scoped ``error`` frame rather than a ``next`` / ``data`` payload.
_GATED_EXTENSION_CHANNEL = "extension-gate"
_INVALID_SUBSCRIPTION = "subscription { nope }"


class _GatedOperationExtension(strawberry.extensions.SchemaExtension):
    """Hold every operation on its schema between admission and its first frame.

    Both ``Schema.execute`` and ``Schema._subscribe`` wrap parsing and validation
    inside ``extensions_runner.operation()``, so an async ``on_operation`` that
    awaits before yielding delays even an operation that will FAIL validation.
    That is the only seam a test can use to put a real revocation between an
    operation's admission and the operation-scoped ``error`` frame it is about to
    emit: a validation error is otherwise produced with no await the test body
    could interleave with.
    """

    async def on_operation(self):
        controller = _CONTROLLERS.get(_GATED_EXTENSION_CHANNEL)
        if controller is not None:
            controller.started.set()
            await controller.gates[0].wait()
        yield


GATED_SCHEMA = strawberry.Schema(
    query=Query,
    subscription=Subscription,
    extensions=[_GatedOperationExtension],
)


# ---------------------------------------------------------------------------
# Probe URLConf for the real secondary-request revocation row.
#
# The holder-free variant of the ``override_settings(ROOT_URLCONF=__name__)``
# pattern ``examples/fakeshop/test_query/test_multi_db.py`` established: this
# module IS the URLConf, so a second REAL HTTP request can run Django's own
# session lifecycle - ``SessionMiddleware`` load, ``django.contrib.auth.logout``,
# the flush, and the ``Set-Cookie`` expiry - against the same session the open
# socket is holding. Nothing GraphQL is served here; the socket stays
# package-tier on the router (spec-046 Decision 13 #"Placement").
# ---------------------------------------------------------------------------

_LOGOUT_PROBE_PATH = "probe/logout/"


def _logout_probe(request):
    """Log the request's session out, reporting what it saw before and after.

    Django's own ``logout`` - not an ORM stand-in: it flushes the session record
    through the configured engine, rotates ``request.session`` to a fresh empty
    store, and lets ``SessionMiddleware`` expire the cookie on the response. The
    before-values are returned so the caller can prove this request really
    resolved the SAME session key and the SAME actor as the open socket, which is
    what makes it a *separate request* rather than a second fixture.
    """
    session_key_before = request.session.session_key
    username_before = request.user.get_username()
    authenticated_before = request.user.is_authenticated
    logout(request)
    return JsonResponse(
        {
            "session_key_before": session_key_before,
            "username_before": username_before,
            "authenticated_before": authenticated_before,
            "session_key_after": request.session.session_key,
        },
    )


urlpatterns = [path(_LOGOUT_PROBE_PATH, _logout_probe)]


def _router_class():
    from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

    return DjangoGraphQLProtocolRouter


# ---------------------------------------------------------------------------
# Construction seam: ``django_application`` is REQUIRED (spec-046 Decision 3),
# so exactly ONE place in this module supplies it. Every test whose subject is
# something else keeps its assertions byte-identical instead of growing the same
# keyword eight times.
# ---------------------------------------------------------------------------


class _RecordingDjangoApplication:
    """A stand-in for Django's ASGI handler: records paths, answers ``418``.

    ``418`` is deliberately un-Django-like, so a response carrying it proves the
    router delegated the request rather than answering it from a package route.
    An instance (not a function) so a test can assert both object identity on the
    ``"http"`` value and, separately, which paths reached it.
    """

    def __init__(self) -> None:
        self.paths: list[str] = []

    async def __call__(
        self,
        scope,
        receive,
        send,
    ) -> None:
        self.paths.append(scope["path"])
        await send({"type": "http.response.start", "status": 418, "headers": []})
        await send({"type": "http.response.body", "body": b"django-application"})


def _router(schema=SCHEMA, **kwargs):
    """Build the router, supplying the required ``django_application`` once.

    A caller that cares about the HTTP value passes its own instance; a caller
    testing the failure matrix passes the unusable value explicitly.
    """
    kwargs.setdefault("django_application", _RecordingDjangoApplication())
    return _router_class()(schema, **kwargs)


# ---------------------------------------------------------------------------
# Structural unwrap helpers (spec-041 Test plan): the Channels internals walk
# lives behind these two intent names so a future Channels reshape changes one
# helper, not several tests.
# ---------------------------------------------------------------------------


def unwrap_host_validator(ws_app):
    """Assert the OUTERMOST WS layer is the package's Host validator; return its child.

    The layer spec-046 Decision 19 adds outside Channels' origin check. Asserted by
    class identity against ``consumers.py``'s own object, because the whole
    composition claim is that this specific package-owned middleware - not merely
    "something" - owns the handshake before authentication can start.
    """
    assert isinstance(ws_app, consumers_module.DjangoWebSocketHostValidator)
    return ws_app.application


def unwrap_origin_validator(ws_app):
    """Assert the WS layer is the ``OriginValidator`` instance; return its child.

    ``AllowedHostsOriginValidator`` is a factory FUNCTION - the isinstance
    target is the ``OriginValidator`` it returns, whose wrapped app is
    ``.application``.
    """
    assert isinstance(ws_app, OriginValidator)
    return ws_app.application


def unwrap_auth_stack(app):
    """Assert the ``AuthMiddlewareStack`` layers in order; return the inner application.

    The stack is ``CookieMiddleware(SessionMiddleware(AuthMiddleware(inner)))``;
    only ``AuthMiddleware`` subclasses ``BaseMiddleware``, so the walk names the
    three layers explicitly (each carries ``.inner``).
    """
    assert isinstance(app, CookieMiddleware)
    assert isinstance(app.inner, SessionMiddleware)
    assert isinstance(app.inner.inner, AuthMiddleware)
    return app.inner.inner.inner


def _route_patterns(url_router):
    assert isinstance(url_router, URLRouter)
    return [route.pattern.regex.pattern for route in url_router.routes]


def _ws_url_router(router):
    """Walk all three router-applied WS wrappers, in order; return the ``URLRouter``.

    Host outside Origin outside the auth stack (spec-046 Decision 19). One walk, so
    the composition's shape is spelled once; the three unwrap helpers stay
    separately callable for the rows whose subject IS the nesting.
    """
    return unwrap_auth_stack(
        unwrap_origin_validator(unwrap_host_validator(router.application_mapping["websocket"])),
    )


# ---------------------------------------------------------------------------
# Communicator plumbing
# ---------------------------------------------------------------------------


def _graphql_post(application, query):
    """A well-formed GraphQL POST envelope aimed at ``/graphql`` over HTTP.

    The envelope is still spelled in full because the HTTP delegation test's
    subject is that a *GraphQL-shaped* request reaches the supplied Django
    application unintercepted - a bare GET would not distinguish that from a
    router with no GraphQL route left.
    """
    body = json.dumps({"query": query}).encode()
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
        (b"host", b"testserver"),
    ]
    return HttpCommunicator(application, "POST", "/graphql", body=body, headers=headers)


def _ws_communicator(
    application,
    *,
    cookie=None,
    subprotocol=_TRANSPORT_WS,
    path="/graphql",
):
    """Build a handshake-ready ``WebsocketCommunicator`` for the WS branch.

    An optional ``cookie`` rides the handshake headers, which is how a real
    session reaches ``AuthMiddlewareStack`` now that the HTTP branch no longer
    carries one. Separate from ``_open_ws`` because the pre-``connection_init``
    row must drive the socket without the init/ack exchange.

    Both a ``Host`` and an ``Origin`` header are supplied, because the branch now
    carries two independent handshake checks (spec-046 Decision 19) and
    ``WebsocketCommunicator`` synthesizes neither header nor a ``scope["server"]``.
    ``testserver`` satisfies both: pytest-django's test environment appends it to
    ``ALLOWED_HOSTS``, which is the one list ``HttpRequest.get_host()`` and
    ``AllowedHostsOriginValidator`` both read.
    """
    headers = [(b"host", b"testserver"), (b"origin", b"http://testserver")]
    if cookie is not None:
        headers.append((b"cookie", cookie.encode()))
    return WebsocketCommunicator(application, path, headers=headers, subprotocols=[subprotocol])


@contextlib.asynccontextmanager
async def _open_ws(application, *, cookie=None, subprotocol=_TRANSPORT_WS):
    """Open ONE acknowledged GraphQL socket and yield the communicator.

    handshake -> connection_init -> connection_ack, then the caller runs as many
    operations as it likes on the SAME socket (which is what the revalidation
    rows need: "denied without reconnecting" is only provable if nothing
    reconnects). Disconnects in ``finally`` so a failing assertion still tears
    the application task down.
    """
    communicator = _ws_communicator(application, cookie=cookie, subprotocol=subprotocol)
    connected, protocol = await communicator.connect(timeout=10)
    try:
        assert connected, "websocket handshake failed"
        assert protocol == subprotocol
        await communicator.send_json_to({"type": "connection_init"})
        ack = await communicator.receive_json_from(timeout=10)
        assert ack["type"] == "connection_ack", ack
        yield communicator
    finally:
        await communicator.disconnect()


async def _send_operation(communicator, query, *, op_id="1"):
    """Send ONE operation frame and return without reading anything back.

    The half of ``_ws_operation`` the outbound-checkpoint rows need: their
    operations are deliberately still in flight when the test body does its next
    step, so nothing may be read yet.
    """
    protocol = communicator.scope["subprotocols"][0]
    operation_frame, _success_frame = _PROTOCOL_FRAMES[protocol]
    await communicator.send_json_to(
        {"type": operation_frame, "id": op_id, "payload": {"query": query}},
    )


async def _ws_operation(communicator, query, *, op_id="1"):
    """Run ONE operation round trip on an open socket; return its first frame.

    The protocol is read back off the communicator's own scope, so a caller
    never spells it twice. A successful single-result operation is followed by
    ``complete`` on both protocols, and that frame is drained here: leaving it
    queued would make the NEXT operation read the PREVIOUS operation's tail.
    Draining it is also the only safe shape - ``receive_output``'s timeout
    CANCELS the application task, so a speculative "is anything left?" read
    would destroy the socket under test.
    """
    protocol = communicator.scope["subprotocols"][0]
    operation_frame, success_frame = _PROTOCOL_FRAMES[protocol]
    await communicator.send_json_to(
        {"type": operation_frame, "id": op_id, "payload": {"query": query}},
    )
    message = await communicator.receive_json_from(timeout=10)
    if message["type"] == success_frame:
        completion = await communicator.receive_json_from(timeout=10)
        assert completion == {"type": "complete", "id": op_id}, completion
    return message


async def _ws_graphql_data(application, query, cookie=None):
    """Run one graphql-transport-ws operation on its own socket; return ``data``.

    The single-operation shape (open, one operation, close) three tests still
    want, expressed over ``_open_ws`` + ``_ws_operation`` so there is exactly one
    handshake site in this module.
    """
    async with _open_ws(application, cookie=cookie) as communicator:
        message = await _ws_operation(communicator, query)
    assert message["type"] == "next", message
    payload = message["payload"]
    assert payload.get("errors") is None, payload
    return payload["data"]


async def _drain_until_close(communicator, *, timeout=10):
    """Read raw output until the socket closes; return (close message, JSON frames).

    Raw ``receive_output`` rather than ``receive_json_from``, because the frame
    under test is a ``websocket.close`` - which ``receive_json_from`` would reject
    as a non-``websocket.send`` message. Everything the socket emitted before the
    close is decoded and handed back so a row can assert what did *not* appear
    there, which is the actual security property.

    Draining stops AT the close, so this helper says nothing about what came after
    it - and something always tries to: a revoked operation's result loop ends
    normally, so both protocols carry on to their own ``complete``. That nothing is
    written for it is a separate contract, measured against the ordered transport
    log by ``_record_the_transport``'s rows rather than from this queue.
    """
    frames = []
    while True:
        message = await communicator.receive_output(timeout=timeout)
        if message["type"] == "websocket.close":
            return message, frames
        assert message["type"] == "websocket.send", message
        frames.append(json.loads(message["text"]))


def _assert_revoked_close(closed):
    """Assert the ONE documented connection-level revocation close.

    Connection-scoped revocation means there is no per-protocol rejection shape
    left to measure: both protocols get upstream's own ``4403`` / ``"Forbidden"``,
    and no operation-level ``error`` frame precedes it. Asserting the exact reason
    is asserting the non-disclosure property itself - a revocation close must be
    byte-identical to every other refusal to authorize this socket, so a
    package-specific reason string (which is what this row would catch) would be a
    signal announcing which refusal fired. Both values are RE-TYPED rather than
    imported, the discipline the hint constants at the top of this module follow.
    """
    assert closed["type"] == "websocket.close", closed
    assert closed["code"] == _REVOKED_CLOSE_CODE, closed
    assert closed["reason"] == _REVOKED_CLOSE_REASON, closed


# ---------------------------------------------------------------------------
# Session / actor fixtures-as-functions for the revalidation rows. Every ORM
# touch rides ``database_sync_to_async`` (the resolver side runs on the event
# loop, where sync ORM raises ``SynchronousOnlyOperation``), and every row that
# needs the executor thread to SEE these writes carries
# ``django_db(transaction=True)`` - the authenticated round trip's shape.
# ---------------------------------------------------------------------------


@database_sync_to_async
def _make_user_and_session(username, password="pw-9x-strong"):
    """Create a user plus a real logged-in session row; return (user, cookie, key).

    Lifted verbatim out of the authenticated-session round trip's local
    ``make_user_and_session_cookie`` when the revalidation rows needed a fifth
    copy of it: same three session keys,
    same ``session.save()``, same cookie spelling. The session key is returned
    too, because the revocation rows revoke the row out of band.
    """
    from django.conf import settings
    from django.contrib.auth import (
        BACKEND_SESSION_KEY,
        HASH_SESSION_KEY,
        SESSION_KEY,
        get_user_model,
    )

    user = get_user_model().objects.create_user(username=username, password=password)
    engine = importlib.import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore()
    session[SESSION_KEY] = str(user.pk)
    session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()
    return user, f"{settings.SESSION_COOKIE_NAME}={session.session_key}", session.session_key


@database_sync_to_async
def _flush_the_session(user, session_key):
    """Revoke the session out of band: clear it and DELETE its row.

    What ``logout`` does on any server-side engine, so this single mutator covers
    both of the spec's "revoke" and "flush" shapes - the stored record is gone,
    and ``channels.auth.get_user`` then finds no ``_auth_user_id``.
    """
    from django.conf import settings

    importlib.import_module(settings.SESSION_ENGINE).SessionStore(session_key).flush()


@database_sync_to_async
def _session_row_still_exists(session_key):
    """Whether the configured engine still holds a record for ``session_key``.

    The durability half of the same-socket logout rows: they assert what the wire
    did NOT carry, which is only meaningful alongside proof that the teardown
    itself completed. Asked through the engine's own ``exists`` rather than the
    ``Session`` model, so the question stays true for any server-side engine.
    """
    from django.conf import settings

    return importlib.import_module(settings.SESSION_ENGINE).SessionStore().exists(session_key)


@database_sync_to_async
def _disable_the_user(user, session_key):
    """Disable the actor out of band; the session row itself stays valid.

    ``ModelBackend.user_can_authenticate`` then rejects the load, so
    ``get_user`` answers ``AnonymousUser`` even though the session is intact.
    """
    user.is_active = False
    user.save(update_fields=["is_active"])


@database_sync_to_async
def _rotate_the_password(user, session_key):
    """Rotate the actor's password out of band, invalidating the session auth hash.

    The shape a password change (or a ``logout`` elsewhere) produces:
    ``get_session_auth_hash`` no longer matches the value stored in the session,
    which ``get_user`` compares in constant time.
    """
    user.set_password("pw-rotated-4k-strong")
    user.save(update_fields=["password"])


@database_sync_to_async
def _rename_and_promote_the_user(user, username):
    """Change two identity fields the next operation can read back.

    Neither field feeds ``get_session_auth_hash`` (that is derived from the
    password), so the session stays VALID - which is what makes this a freshness
    probe rather than a second revocation.
    """
    user.username = username
    user.is_staff = True
    user.save(update_fields=["username", "is_staff"])


def _poison_the_session_store(monkeypatch):
    """Make the revalidation's fresh-store resolver raise on every call.

    One poisoning target for three rows: it proves the fail-closed degrade when
    the revalidation DOES run (spec-046 row 30), and it proves the two early
    returns skipped the session read entirely when they do NOT - a swallowed
    exception would surface as a denied operation, so "the operation succeeded"
    is only possible if the read never happened.

    The target is ``utils/sessions.py``, the resolver's home: it lives outside the
    eagerly-importing ``auth`` package;
    ``consumers.py::_refreshed_actor`` imports the name from there per call, so
    patching the module attribute is what the coroutine reads.
    """

    def _raise():
        raise RuntimeError("poisoned session store")

    monkeypatch.setattr(session_store_module, "session_store_class", _raise)


def _package_logger_records(caplog):
    return [record for record in caplog.records if record.name == "django_strawberry_framework"]


def _actor_lease(consumer):
    """The ``asyncio.Lock`` object serving as this connection's actor lease.

    Literally the expression the production checkpoints acquire, not a second one
    spelled here from a scope key and an attribute name: a row asserting "these
    two sockets hold two different leases", or "the lease is held right now", is
    then asserting it about the object the production code locks, and cannot drift
    from it.
    """
    return session_store_module.actor_lease(consumer.scope)


def _actor_lease_held(consumer):
    """Whether ANYONE holds this connection's shared actor lease.

    The lease lives on the ASGI scope rather than on the consumer instance, which
    is the structural point of it: the auth layer's own ``logout`` has to be able
    to acquire the very lock the revalidation checkpoints hold, and it can only
    reach the scope. Which object that is comes from :func:`_actor_lease`.

    Its ONE stated limit, recorded so it is never "strengthened" into something
    weaker: ``asyncio.Lock.locked()`` is a property of the LOCK, not of the holder,
    so this reads "someone holds this connection's lease" rather than "this task
    does". It discriminates in the rows that read it because those rows have no
    contender at that instant, or because they name the contender independently.
    """
    return _actor_lease(consumer).locked()


class _RevalidationProbe:
    """Count the revalidation's session reads, and optionally hold or poison one."""

    def __init__(self):
        self.reads = 0
        self.entered = asyncio.Event()
        self.hold = None
        self.hold_key = None
        self.invalidate_after = None


def _instrument_revalidation(monkeypatch):
    """Count every session read the revalidation performs; return the probe.

    The read is the whole cost of the feature, so several rows assert its exact
    count rather than its consequences: "one read per security checkpoint" at
    window ``0.0``, "zero reads" for an anonymous or idle socket, and "no second
    read" once the connection is revoked. ``_refreshed_actor`` is the narrowest
    seam that counts a read and nothing else - it is the single coroutine that
    crosses into the database - and patching the module attribute is what the
    production code resolves, because ``_actor_is_current`` looks the name up as a
    module global per call (the ``_monotonic`` seam's discipline).

    ``probe.hold``, when set to an ``Event``, additionally parks the read inside
    the critical section, which is how the sibling-payload row gets a validation
    boundary it can hold a task at. ``probe.hold_key`` narrows that to ONE
    connection's session key, which is what lets the blast-radius row hold socket 1
    inside its critical section while socket 2 runs to completion - the probe is a
    module-level patch, so without the narrowing it would park every connection's
    reads and prove the opposite of what the row is for.

    ``probe.invalidate_after = N`` makes read ``N + 1`` and every later read answer
    ``AnonymousUser`` without touching the database, which is how a row revokes
    between two *specific* checkpoints rather than out of band. The out-of-band
    mutators (``_flush_the_session`` and friends) are the right tool whenever the
    revocation can land between two things the test body itself sequences; counting is
    the only tool when the two checkpoints belong to ONE upstream call the test body
    cannot interleave with - the subscription-limit row's admission and its
    ``error`` frame both happen inside a single ``handle_subscribe``.
    """
    probe = _RevalidationProbe()
    original = consumers_module._refreshed_actor

    async def counting_refreshed_actor(scope):
        probe.reads += 1
        probe.entered.set()
        if probe.hold is not None and probe.hold_key in (None, scope["session"].session_key):
            await probe.hold.wait()
        if probe.invalidate_after is not None and probe.reads > probe.invalidate_after:
            return AnonymousUser()
        return await original(scope)

    monkeypatch.setattr(consumers_module, "_refreshed_actor", counting_refreshed_actor)
    return probe


class _CloseProbe:
    """What reached the transport's own close, and whether it may complete.

    ``calls`` records every ``(code, reason)`` that reached Channels' own
    ``AsyncWebsocketConsumer.close`` - the call the adapter's ``close`` delegates
    to, and the last package-visible point before the ASGI ``send``. Nothing
    upstream records that a close was sent (not the consumer, not the adapter,
    not either handler), so this list is the only place "how many closes actually
    reached the transport" is observable, and it is what separates "a close was
    decided" from "a close was committed".

    ``park``, when set to an ``Event``, holds the close open with its bytes
    uncommitted - the state a back-pressured socket write occupies and the one an
    in-process queue otherwise never produces. ``failures`` makes the first N
    attempts raise ``OSError`` instead, which is the realistic transport failure
    (beside a disconnected socket and a server state assertion) and the shape that
    must not be recorded as a completed close.
    """

    def __init__(self):
        self.calls = []
        self.entered = asyncio.Event()
        self.park = None
        self.failures = 0


def _instrument_consumer_close(monkeypatch):
    """Observe - and optionally park or break - the close the revocation performs.

    Patched on Channels' own ``AsyncWebsocketConsumer.close`` rather than on any
    package seam: the package's close path is
    ``_ConnectionRevocation`` -> the adapter's ``close`` -> ``consumer.close``, so
    this is the real production chain with only its final ASGI hop replaced. The
    rows that use it are about what the package does when that hop misbehaves,
    which is unobservable from any other vantage point - a second close is a
    silent no-op under a real server and a second output message under
    ``channels.testing``, and neither tells the caller anything.
    """
    from channels.generic.websocket import AsyncWebsocketConsumer

    probe = _CloseProbe()
    native = AsyncWebsocketConsumer.close

    async def recording_close(consumer, code=None, reason=None):
        probe.calls.append((code, reason))
        probe.entered.set()
        if probe.park is not None:
            await probe.park.wait()
        if len(probe.calls) <= probe.failures:
            raise OSError("the transport refused the close frame")
        await native(consumer, code=code, reason=reason)

    monkeypatch.setattr(AsyncWebsocketConsumer, "close", recording_close)
    return probe


class _TransportLog:
    """Every ASGI message this connection committed to the transport, in order.

    ``_CloseProbe`` records the closes and the communicator's own queue can be
    drained up to one; neither can answer what the package wrote AFTER a close.
    A frame committed past the ``4403`` is invisible to any assertion that stops
    draining at the close, and ``receive_nothing`` cannot say whether what it found
    arrived before the close or after it. This is the ordered log, so the close's
    position in it is the only reference point the rows need.
    """

    def __init__(self):
        self.messages = []

    @property
    def frame_types(self):
        """The type of every JSON frame committed, in order."""
        return [
            json.loads(message["text"])["type"]
            for message in self.messages
            if message["type"] == "websocket.send"
        ]

    def after_the_revocation_close(self):
        """Every message committed AFTER the ``4403``; fails if there was no close.

        Failing loudly is the point: "nothing followed the close" is trivially
        true of a connection that never closed, which is the one way an assertion
        on this tail could pass while proving nothing at all.
        """
        for index, message in enumerate(self.messages):
            if message["type"] == "websocket.close" and message.get("code") == (
                _REVOKED_CLOSE_CODE
            ):
                return self.messages[index + 1 :]
        raise AssertionError(
            f"no {_REVOKED_CLOSE_CODE} close reached the transport at all: {self.messages}",
        )


def _record_the_transport(monkeypatch):
    """Record every ASGI message the consumer commits; return the log.

    Patched on Channels' own ``AsyncConsumer.send`` - the one call every outbound
    message funnels through whatever wrote it, since
    ``AsyncWebsocketConsumer.send`` (where upstream's serialized frames arrive)
    and ``AsyncWebsocketConsumer.close`` both delegate to it. One seam therefore
    yields the frames and the closes interleaved in the order the transport saw
    them, which is what a contract about "after the close" is measured against;
    ``_instrument_consumer_close``'s narrower seam is the right one whenever the
    subject is the close alone.
    """
    from channels.consumer import AsyncConsumer

    log = _TransportLog()
    native = AsyncConsumer.send

    async def recording_send(consumer, message):
        log.messages.append(message)
        await native(consumer, message)

    monkeypatch.setattr(AsyncConsumer, "send", recording_send)
    return log


class _LoopSentinel:
    """A tick count from a task nobody involved in the operation under test knows about."""

    def __init__(self):
        self.ticks = 0


@contextlib.asynccontextmanager
async def _loop_sentinel():
    """Run an independent ticking task for the duration of the block.

    The liveness half of the stop-protocol rows. A revoked operation that cannot be
    stopped does not merely misbehave locally - it holds the event loop, so nothing
    else on that loop runs, including the connection's own teardown. A task that
    only ever ``await asyncio.sleep(0)``s advances once per loop pass, so a nonzero
    count means the loop kept scheduling while the revoked operation was being
    stopped. Cancelled and awaited on the way out, so it cannot outlive the block
    under a suite that treats a lingering task as an error.
    """
    sentinel = _LoopSentinel()

    async def tick():
        while True:
            await asyncio.sleep(0)
            sentinel.ticks += 1

    task = asyncio.create_task(tick())
    try:
        yield sentinel
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


class _OutboundGateProbe:
    """What the outbound checkpoint did: who entered, whose lease, and when it sent."""

    def __init__(self):
        self.entries = []
        self.frame_types = []
        self.from_run_task = []
        self.tasks = []
        self.consumers = []
        self.sends_under_lease = []
        self.reached_send = asyncio.Event()
        self.hold_before_send = None


def _record_outbound_gate(monkeypatch):
    """Observe the outbound checkpoint from the outside; return the probe.

    Every observation is of the real production objects at the real moments the
    production code reaches them.

    ``entries`` records gate entry. The gate's first act is to acquire the
    connection's actor lease, so "operation B entered the gate while operation
    A holds the lease" is exactly the observation "B is queued at the lease" - the
    contention the design accepts, and otherwise invisible from outside.

    ``sends_under_lease`` records whether the lease was still held at the instant
    the checkpoint called ``send``. That is the one thing no wire assertion can
    show: releasing the lease after validation instead of after the send is
    indistinguishable in-process here, because ``channels.testing``'s ``base_send``
    puts onto an unbounded queue and never suspends, so no sibling can interleave
    into the window that mutation opens (a real ASGI server's socket write does
    suspend, which is precisely why the design closes the window). The wrapper
    delegates to the checkpoint's own ``send`` argument, so what is measured is the
    production lease at the production call site, not a stand-in for either. See
    ``_actor_lease_held`` for what ``locked()`` can and cannot say.

    ``probe.hold_before_send``, when set to an ``Event``, additionally parks the
    checkpoint's own send delegate at exactly that point - authorization granted,
    bytes not yet committed - which is the state a real socket write occupies and
    the state the ``base_send`` queue otherwise never leaves the process in. It is
    the only park point from which "a same-connection logout cannot complete
    across an authorized send" is observable at all, and ``reached_send`` is how
    the row knows the park was reached rather than skipped.

    ``frame_types`` and ``from_run_task`` record which frame reached the checkpoint
    and whether it arrived on the connection's own message-loop task - the two facts
    the subscription-limit row needs, and the only place either is observable.

    ``tasks`` records the task each frame arrived ON, which for every frame but the
    subscription-limit one IS the operation's own task: upstream awaits
    ``send_next`` / ``send_data_message`` directly inside ``run_operation`` /
    ``handle_async_results``, i.e. inside the task it created for that operation. It
    is the only handle on that object a test can get - the one place a resolver
    could look is misleading (see ``_OperationController``) - and the rows that need
    it are asserting that a revoked operation FINISHED rather than merely fell
    silent.
    """
    probe = _OutboundGateProbe()
    original = consumers_module.send_revalidated_operation_frame

    async def recording_send(websocket, message, send):
        consumer = websocket.ws_consumer
        probe.entries.append(message["id"])
        probe.frame_types.append(message.get("type"))
        probe.from_run_task.append(asyncio.current_task() is consumer.run_task)
        probe.tasks.append(asyncio.current_task())
        probe.consumers.append(consumer)

        async def observing_send(payload):
            probe.sends_under_lease.append(_actor_lease_held(consumer))
            probe.reached_send.set()
            if probe.hold_before_send is not None:
                await probe.hold_before_send.wait()
            await send(payload)

        return await original(websocket, message, observing_send)

    monkeypatch.setattr(consumers_module, "send_revalidated_operation_frame", recording_send)
    return probe


async def _reached(event, message, *, timeout=10):
    """Await one controller/probe ``Event``, failing loudly instead of hanging.

    Every wait in these rows is for a state the production code is about to
    produce, so the timeout is a FAILURE BOUND rather than a timing assumption -
    the same role ``timeout=10`` plays on every communicator read in this module.
    Bare ``await event.wait()`` would be correct on a green tree and a hang on a
    regressed one: if the outbound checkpoint stopped running, the probe's event
    would simply never be set, and the suite would sit there forever instead of
    reporting which contract broke.
    """
    try:
        await asyncio.wait_for(event.wait(), timeout)
    except asyncio.TimeoutError as exc:
        raise AssertionError(message) from exc


async def _wait_until(
    predicate,
    describe,
    *,
    tries=2500,
    delay=0.002,
):
    """Yield to the event loop until ``predicate()`` holds, or fail loudly.

    Used only where the awaited state is something the production code appends to
    or counts up (gate entries, admission reads), which carries no Event of its
    own. The awaited state is one the production code is about to produce, so
    ``tries * delay`` is a FAILURE BOUND: it only bounds how long a genuinely
    stuck run takes to report which contract broke, and a run that satisfies the
    predicate returns as soon as it does. The bound is not free of real time
    though - a predicate over session reads waits on one database round trip per
    read through an executor thread, which on a networked vendor costs ~0.65s for
    a hundred reads against ~0.1s on local SQLite, so the 5s ceiling here keeps
    an order of magnitude of headroom over the slowest measured vendor.

    ``describe`` is called only on failure, and must therefore be a callable so
    the message reports the state AT failure time; an eagerly formatted string
    would report the state before the wait began.
    """
    for _ in range(tries):
        if predicate():
            return
        await asyncio.sleep(delay)
    raise AssertionError(describe())


async def _logout_through_a_real_second_request(session_key, username):
    """Revoke the socket's session through a REAL second HTTP request.

    Django's own ``logout``, reached over ``AsyncClient`` against this module's
    probe URLConf, asserting on the way that the request resolved the SAME session
    key and the SAME actor as the open socket - which is what makes it a separate
    request rather than a second fixture. Lifted out of the real-second-request
    logout row when the running-subscription rows needed the same revocation.
    """
    cookie_name = settings.SESSION_COOKIE_NAME
    with override_settings(ROOT_URLCONF=__name__):
        client = AsyncClient()
        client.cookies[cookie_name] = session_key
        response = await client.post(f"/{_LOGOUT_PROBE_PATH}")

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["session_key_before"] == session_key
    assert body["username_before"] == username
    assert body["authenticated_before"] is True
    # Django's logout flushed the record and expired the browser cookie, so the
    # credential the socket is still holding no longer resolves.
    assert body["session_key_after"] is None
    assert response.cookies[cookie_name].value == ""


# ---------------------------------------------------------------------------
# Channels-present: construction and composition
# ---------------------------------------------------------------------------


def test_router_is_a_protocol_type_router_mapping_exactly_http_and_websocket():
    """A true ``ProtocolTypeRouter`` whose mapping carries exactly the two protocols.

    Framed as a current-shape parity assertion (upstream maps exactly these
    two); the behavior tests below are what the mapping must actually deliver.
    """
    router = _router()
    assert isinstance(router, ProtocolTypeRouter)
    assert set(router.application_mapping) == {"http", "websocket"}


def test_http_branch_is_the_supplied_django_application_by_identity():
    """Spec-046 row 8: ``"http"`` IS the supplied object, with no wrapper.

    Object identity, not structural equality: after the protocol split there is
    nothing left to introspect on the HTTP branch, which is the point. The
    negative assertions name the three wrappers the ``0.0.14`` composition used
    to interpose (``AuthMiddlewareStack``'s outermost layer, the ``URLRouter``
    that held the GraphQL route, and the origin validator WS still carries).
    """
    django_application = _RecordingDjangoApplication()
    router = _router(django_application=django_application)
    http_branch = router.application_mapping["http"]

    assert http_branch is django_application
    assert not isinstance(http_branch, (CookieMiddleware, URLRouter, OriginValidator))


def test_construction_rejects_an_omitted_or_unusable_django_application():
    """Spec-046 row 10: omission is ``TypeError``; unusable is ``ConfigurationError``.

    Omission fails as a required parameter should - Python's own signature
    binding, naming the parameter. Explicit ``None`` (the shape a ``0.0.14``
    migrant carries over) and any non-callable get the prose instead, naming all
    three facts Error shapes requires: the security reason the old mode was
    unsafe, that the mode is REMOVED rather than flagged, and both halves of the
    two-place repair. The message substrings are
    deliberately RE-TYPED rather than imported from the module: asserting the
    constant against itself could never catch the hint drifting.
    """
    with pytest.raises(TypeError, match="django_application"):
        _router_class()(SCHEMA)

    for unusable in (None, object()):
        with pytest.raises(ConfigurationError) as exc_info:
            _router(django_application=unusable)
        message = str(exc_info.value)
        assert "ALLOWED_HOSTS" in message
        assert "REMOVED" in message
        assert "get_asgi_application" in message
        assert "DjangoGraphQLView" in message


def test_graphql_http_consumer_left_the_router_module_entirely():
    """Spec-046 row 9: ``GraphQLHTTPConsumer`` is nowhere in ``routers.py``.

    Read the module's own SOURCE, not ``dir(routers_module)``: an unimported name
    is absent from ``dir()`` whether or not the module still references it, so
    only the source text proves the import left in the same change as the
    composition (Decision 2).
    """
    source = Path(routers_module.__file__).read_text(encoding="utf-8")
    assert "GraphQLHTTPConsumer" not in source


def test_websocket_branch_wraps_origin_validator_outside_the_auth_stack():
    """``AllowedHostsOriginValidator`` OUTSIDE ``AuthMiddlewareStack`` on WS only.

    Both original assertions are preserved verbatim (the origin validator sits
    outside the auth stack; the ``"http"`` value is no ``OriginValidator``); the
    walk gains ONE outer layer, the package's own Host validator (spec-046
    Decision 19, Decision 13 #"gains an outer layer"). Nothing is weakened: the
    origin validator's position relative to the auth stack is still what the
    middle unwrap asserts.
    """
    router = _router()
    inner = unwrap_origin_validator(
        unwrap_host_validator(router.application_mapping["websocket"]),
    )
    ws_router = unwrap_auth_stack(inner)
    assert _route_patterns(ws_router) == [r"^graphql/?$"]
    # The HTTP branch carries no origin validator - it is the bare Django
    # application, which is not an ``OriginValidator``.
    assert not isinstance(router.application_mapping["http"], OriginValidator)


def test_custom_websocket_url_pattern_reaches_only_the_websocket_re_path():
    """Spec-046 row 11, structural half: the pattern is WebSocket-only now.

    ``websocket_url_pattern=`` governs one branch; the HTTP value stays the
    identical supplied object, because HTTP path matching belongs entirely to
    the consumer's Django URLconf (Decision 4).
    """
    django_application = _RecordingDjangoApplication()
    router = _router(
        django_application=django_application,
        websocket_url_pattern="^api/graphql",
    )
    ws_router = _ws_url_router(router)
    assert _route_patterns(ws_router) == ["^api/graphql"]
    assert router.application_mapping["http"] is django_application


def test_the_websocket_pattern_is_keyword_only_with_no_legacy_url_pattern_alias():
    """Spec-046 Decision 4: both NEGATIVE halves of the rename.

    Decision 4 renames rather than aliases - "a single parameter that no longer
    affects HTTP would be a name that lies" - and makes the replacement
    keyword-only. The revalidation keywords reopen this exact signature to add
    two more keywords, so both halves of the rename are pinned
    here: a compatibility alias or a relaxed positional boundary has to fail
    loudly instead of arriving as a convenience edit.
    """
    with pytest.raises(TypeError, match="url_pattern"):
        _router(url_pattern="^graphql")

    with pytest.raises(TypeError, match="positional"):
        _router_class()(SCHEMA, _RecordingDjangoApplication(), "^graphql")


def test_repeated_access_returns_the_cached_class_which_is_subclassable():
    """The builder memoizes into ``_ROUTER_CLASS``; the class is a real base."""
    first = _router_class()
    second = _router_class()
    assert first is second
    assert first is routers_module.DjangoGraphQLProtocolRouter

    class Extended(first):
        pass

    assert issubclass(Extended, ProtocolTypeRouter)
    # The star surface is pinned to the one public symbol (Decision 3).
    assert routers_module.__all__ == ("DjangoGraphQLProtocolRouter",)


# ---------------------------------------------------------------------------
# Channels-present: the WebSocket consumer-injection seam and the window's
# construction-time validation (spec-046 Decision 11, rows 28-29).
# Structural only - no socket, no database.
# ---------------------------------------------------------------------------


def _graphql_ws_consumer():
    """Resolve upstream's consumer class at CALL time, not at collection time.

    The eviction-simulated-absence tests replace and restore
    ``sys.modules["strawberry.channels"]``; resolving through ``sys.modules`` per
    call keeps ``issubclass`` comparisons in these rows against the same class
    object the cached router closure holds, whatever ran before.
    """
    from strawberry.channels import GraphQLWSConsumer

    return GraphQLWSConsumer


def _mounted_ws_callback(router):
    """The single WS route's callback, after asserting all three wrappers are in place."""
    ws_router = _ws_url_router(router)
    assert _route_patterns(ws_router) == [r"^graphql/?$"]
    return ws_router.routes[0].callback


def test_the_default_websocket_consumer_is_the_packages_revalidating_subclass():
    """Spec-046 checklist boxes 2-3: the default mount is the package consumer.

    ``websocket_consumer_class=None`` selects ``consumers.py``'s revalidating
    subclass - a real ``GraphQLWSConsumer`` subclass that is NOT
    ``GraphQLWSConsumer`` itself (which is what the ``0.0.14`` mount was) - and
    it is handed the exact schema object plus the default window of ``0.0``,
    which is the "revalidate every operation" spelling.
    """
    callback = _mounted_ws_callback(_router())

    assert issubclass(callback.consumer_class, _graphql_ws_consumer())
    assert callback.consumer_class is not _graphql_ws_consumer()
    assert callback.consumer_initkwargs == {"schema": SCHEMA, "revalidation_window": 0.0}
    assert callback.consumer_initkwargs["schema"] is SCHEMA
    # Both protocol pre-hooks are in place, each one level below upstream's.
    for attribute in ("graphql_transport_ws_handler_class", "graphql_ws_handler_class"):
        installed = getattr(callback.consumer_class, attribute)
        assert installed is not getattr(_graphql_ws_consumer(), attribute)
        assert installed.__mro__[1].__name__.startswith("BaseGraphQL")


def test_the_generated_consumer_installs_a_derived_websocket_adapter_class():
    """The outbound checkpoint is a CLASS seam.

    ``AsyncBaseHTTPView.run`` instantiates ``self.websocket_adapter_class(...)`` by
    name, per connection, so deriving one adapter and installing it on the
    generated consumer is a class-level extension - the same mechanism the two
    handler classes above already use. The alternative shapes are what this row
    exists to refuse: rebinding an adapter *instance* attribute after the fact
    (there is no seam that runs between the adapter's construction and its first
    frame), and mutating upstream's own class attribute (process-wide, and it would
    gate an injected consumer that opted out).
    """
    upstream_consumer = _graphql_ws_consumer()
    upstream_adapter = upstream_consumer.websocket_adapter_class
    consumer_class = _mounted_ws_callback(_router()).consumer_class
    installed = consumer_class.websocket_adapter_class

    assert isinstance(installed, type), installed
    assert issubclass(installed, upstream_adapter)
    assert installed is not upstream_adapter
    # Installed by the factory on the generated class, and overriding exactly the
    # one method both protocols funnel every frame through.
    assert "websocket_adapter_class" in vars(consumer_class)
    assert "send_json" in vars(installed)
    # Upstream's own attribute is untouched: nothing here monkeypatches a shared
    # class, so an injected consumer keeps upstream's adapter.
    assert upstream_consumer.websocket_adapter_class is upstream_adapter


def test_only_information_bearing_frames_reach_the_outbound_checkpoint():
    """The gated frame set is exactly the payload-carrying frames.

    The structural half of "connection-control frames retain upstream behavior".
    ``next`` / ``data`` carry results, and an operation-scoped ``error`` can still
    disclose schema, validation, extension, or consumer-authored detail - so all
    three are gated, and nothing else is. The control frames are named
    individually rather than left implied by the equality: ``ka`` in particular has
    no behavioral row, because the router exposes no ``keep_alive`` knob for the
    legacy protocol's keep-alive loop to be switched on with.
    """
    gated = consumers_module._INFORMATION_BEARING_FRAME_TYPES
    assert gated == frozenset({"next", "data", "error"})
    for control_frame in (
        "connection_ack",
        "connection_error",
        "complete",
        "ping",
        "pong",
        "ka",
    ):
        assert control_frame not in consumers_module._INFORMATION_BEARING_FRAME_TYPES


def test_an_injected_consumer_class_still_sits_inside_all_three_wrappers():
    """Spec-046 row 28: injection opts out of revalidation, not of the wrappers.

    ``DjangoWebSocketHostValidator``, ``AllowedHostsOriginValidator`` and
    ``AuthMiddlewareStack`` are applied by the ROUTER around whatever is injected,
    so the unwrap walk and the route pattern are identical to the default mount's -
    that structural guarantee is Decision 11's whole safety argument, and Decision
    19 is what makes its Host half real rather than nominal. The HTTP branch is
    unaffected. The behavioral half - a hostile ``Host`` and a hostile ``Origin``
    each denying an injected consumer's handshake - is
    ``test_an_injected_consumer_is_denied_by_both_handshake_boundaries``.
    """

    class Injected(_graphql_ws_consumer()):
        pass

    django_application = _RecordingDjangoApplication()
    router = _router(
        django_application=django_application,
        websocket_consumer_class=Injected,
    )

    callback = _mounted_ws_callback(router)
    assert callback.consumer_class is Injected
    # The window is the PACKAGE consumer's knob, so an injected class is mounted
    # through its own plain ``as_asgi(schema=schema)``.
    assert callback.consumer_initkwargs == {"schema": SCHEMA}
    assert router.application_mapping["http"] is django_application


async def _valid_asgi_application(scope, receive, send):
    """The ASGI application a CORRECT factory returns: an async callable.

    Module-level so the four factory rows below mount the same object and assert
    identity against it. Never driven - every row that mounts it asserts identity
    or the wrapper nesting - so reaching the body would itself be the bug.
    """
    raise AssertionError("no row drives the injected ASGI application")


def test_an_injected_consumer_factory_is_called_with_the_schema_and_mounted():
    """Spec-046 Decision 11: the factory shape's calling convention.

    A non-class callable is a factory, invoked as ``factory(schema=schema)``, and
    whatever it returns is what gets mounted - by identity, so the router adds no
    ``as_asgi`` hop of its own.

    Also the ACCEPTED half of the validation matrix: a synchronous
    factory returning an async ASGI callable still passes, and it passes
    *unwrapped* - ``_mounted_ws_callback`` asserts ``AllowedHostsOriginValidator``
    and ``AuthMiddlewareStack`` are still the two layers above the route, so the
    new validation neither moves nor unwraps them.
    """
    received = {}

    def factory(**kwargs):
        received.update(kwargs)
        return _valid_asgi_application

    callback = _mounted_ws_callback(_router(websocket_consumer_class=factory))

    assert callback is _valid_asgi_application
    assert inspect.iscoroutinefunction(callback)
    assert list(received) == ["schema"]
    assert received["schema"] is SCHEMA


@pytest.mark.parametrize(
    ("returned", "expected_tail"),
    [
        pytest.param(None, "NoneType None", id="none"),
        pytest.param(7, "int 7", id="non-callable-scalar"),
        pytest.param({"asgi": True}, "dict {'asgi': True}", id="mapping"),
        pytest.param(10**10000, "an unprintable int", id="int-too-large-to-render"),
    ],
)
def test_a_factory_returning_a_non_application_fails_at_construction(returned, expected_tail):
    """The factory's RESULT is validated before mounting.

    Before this row the router mounted whatever the factory handed back, so a
    ``None`` or a scalar became a URL route callback and the first matching
    handshake failed deep inside Channels' routing with no mention of the seam.
    The rejection now happens at construction and names both the factory and the
    received value, which are the two things a migrant needs.

    The last row is a value whose ``repr`` cannot be rendered at all: CPython
    refuses to convert an integer of more than 4300 digits to a string, so an
    f-string tail would have raised ``ValueError`` from inside the rejection and
    replaced the promised ``ConfigurationError``. The message degrades to the
    type instead (``exceptions.py::describe_value``).
    """

    def factory(*, schema):
        return returned

    with pytest.raises(ConfigurationError) as exc_info:
        _router(websocket_consumer_class=factory)

    message = str(exc_info.value)
    assert _FACTORY_CONTRACT_SUBSTRING in message
    assert "AllowedHostsOriginValidator" in message
    assert f"returned {expected_tail}" in message


def test_an_async_factory_is_rejected_and_the_refused_coroutine_is_closed():
    """A coroutine is not an ASGI application.

    An ``async def`` factory returns a coroutine object, which is not callable and
    can never serve a handshake. Two shapes are covered: the literal one (an
    ``async def`` passed straight in), and a synchronous wrapper
    that hands the SAME coroutine object to the router while keeping a reference
    to it - the only way a test can inspect what the router did with it.

    ``cr_frame is None`` is the proof that the router CLOSED the coroutine it
    refused. That is not a nicety: an un-awaited coroutine makes CPython emit an
    unraisable ``RuntimeWarning`` from the garbage collector at an unrelated
    moment, which is noise pointing at the package in a normal consumer process
    and a hard error under this suite's own ``-W error`` policy.
    """

    async def async_factory(*, schema):
        return _valid_asgi_application

    with pytest.raises(ConfigurationError) as exc_info:
        _router(websocket_consumer_class=async_factory)
    message = str(exc_info.value)
    assert _ASYNC_FACTORY_SUBSTRING in message
    assert "returned coroutine" in message

    coroutines = []

    def wrapping_factory(*, schema):
        coroutine = async_factory(schema=schema)
        coroutines.append(coroutine)
        return coroutine

    with pytest.raises(ConfigurationError):
        _router(websocket_consumer_class=wrapping_factory)

    [refused] = coroutines
    assert refused.cr_frame is None, "the router must close the coroutine it refuses"


def test_a_factory_that_cannot_accept_the_schema_keyword_fails_at_construction():
    """The calling convention is a construction error too.

    ``factory(schema=schema)`` is the seam's one calling convention, so a factory
    that cannot bind it is a configuration error naming the convention, with the
    binding ``TypeError`` preserved as ``__cause__`` rather than surfacing bare.
    """

    def factory():
        return _valid_asgi_application

    with pytest.raises(ConfigurationError) as exc_info:
        _router(websocket_consumer_class=factory)

    message = str(exc_info.value)
    assert _FACTORY_CONTRACT_SUBSTRING in message
    assert _FACTORY_CONVENTION_SUBSTRING in message
    assert isinstance(exc_info.value.__cause__, TypeError)


def test_a_factory_that_raises_from_its_body_is_not_normalized():
    """Only the CONVENTION is normalized, never the body.

    The convention check binds the call with ``inspect.signature`` *before*
    invoking the factory, precisely so that a ``TypeError`` raised inside a
    correct factory's body stays a ``TypeError`` with its own traceback. Catching
    ``TypeError`` around the call instead would have collapsed a consumer bug into
    "your factory has the wrong signature", which is the wrong diagnosis.
    """

    def factory(*, schema):
        raise TypeError("the factory's own bug")

    with pytest.raises(TypeError, match="the factory's own bug"):
        _router(websocket_consumer_class=factory)


def test_a_factory_whose_signature_cannot_be_read_is_judged_by_the_call():
    """An un-introspectable callable is not pre-rejected.

    ``inspect.signature`` raises for a callable it cannot describe (a C callable,
    or - as here - an object carrying a lying ``__signature__``). That is not
    evidence the call would fail, so the pre-check skips and the factory is
    judged by its result, which mounts normally.
    """

    class _Unintrospectable:
        __signature__ = "not a signature"

        def __call__(self, **kwargs):
            return _valid_asgi_application

    callback = _mounted_ws_callback(_router(websocket_consumer_class=_Unintrospectable()))

    assert callback is _valid_asgi_application


@pytest.mark.parametrize(
    "unusable",
    [
        pytest.param(dict, id="class-that-is-not-a-consumer"),
        pytest.param(ProtocolTypeRouter, id="unrelated-channels-class"),
        pytest.param(object(), id="non-callable-instance"),
        pytest.param(7, id="non-callable-scalar"),
    ],
)
def test_an_unusable_websocket_consumer_class_is_a_construction_error(unusable):
    """Spec-046 Decision 11: neither accepted shape, so ConfigurationError.

    A class that is not a ``GraphQLWSConsumer`` subclass must NOT be quietly
    routed into the factory branch (a class is callable, so the ordering is
    load-bearing), and a non-callable is not a factory. Both name the accepted
    shapes and the value received; the substrings are RE-TYPED.
    """
    with pytest.raises(ConfigurationError) as exc_info:
        _router(websocket_consumer_class=unusable)

    message = str(exc_info.value)
    assert _UNUSABLE_CONSUMER_SUBSTRING in message
    assert "factory(schema=schema)" in message
    assert repr(unusable) in message


@pytest.mark.parametrize(
    "unusable",
    [
        pytest.param(-1.0, id="negative"),
        pytest.param(True, id="bool-is-not-a-number"),
        pytest.param("1.0", id="string"),
        pytest.param(float("nan"), id="nan"),
        pytest.param(float("inf"), id="inf"),
        pytest.param(10**10000, id="int-with-no-float-image"),
        pytest.param(-(10**10000), id="negative-int-with-no-float-image"),
    ],
)
def test_the_revalidation_window_rejects_unusable_values(unusable):
    """Spec-046 Decision 11: the window's construction-time domain.

    ``bool`` is rejected because the gate admits the built-in ``int`` and
    ``float`` exactly - ``bool`` is a subclass of ``int``, so an ``isinstance``
    gate would have let it through - and
    both non-finite values are rejected because neither is a usable number of
    seconds: ``nan`` loses every comparison, so it would silently never expire
    and never say why, and ``inf`` is a saturation sentinel rather than a value a
    deployment chose. Note what that reasoning does NOT claim - a ceiling; the
    sibling row below accepts a finite but astronomical window on purpose. The
    failure is ``ConfigurationError`` at construction, never a per-operation
    surprise.

    The two huge-integer rows cover the enormous-window case. An ``int``
    with no ``float`` image passes every ``isinstance`` check, so the validator
    used to hand it to ``math.isfinite`` and escape the typed boundary with a raw
    ``OverflowError``; rendering it into the rejection then raised ``ValueError``
    from CPython's 4300-digit integer-to-string guard. Both arms are now inside
    the boundary, and the negative twin is here because its ``value < 0`` check
    could never run either.
    """
    with pytest.raises(ConfigurationError, match="websocket_revalidation_window"):
        _router(websocket_revalidation_window=unusable)


def test_the_huge_window_rejection_chains_its_cause_and_still_renders():
    """The enormous-window rejection is complete, not just typed.

    Two properties the parametrized rejection row's ``pytest.raises`` cannot
    infer: the ``OverflowError`` that detected the value survives as ``__cause__``
    (so the
    traceback still says *why* the number is unusable), and the message renders at
    all - the value degrades to its type instead of raising ``ValueError`` while
    the rejection is being formatted.
    """
    with pytest.raises(ConfigurationError) as exc_info:
        _router(websocket_revalidation_window=10**10000)

    assert isinstance(exc_info.value.__cause__, OverflowError)
    assert "an unprintable int" in str(exc_info.value)


class _HostileFloat(float):
    """A ``float`` whose conversion raises - the numeric dunder is overridable."""

    def __float__(self):
        raise RuntimeError("hostile conversion")


class _WellBehavedInt(int):
    """An ``int`` subclass that behaves perfectly and is still not an ``int``."""


@pytest.mark.parametrize(
    "subclass_value",
    [
        pytest.param(_HostileFloat(1.0), id="float-subclass-whose-conversion-raises"),
        pytest.param(_WellBehavedInt(30), id="well-behaved-int-subclass"),
    ],
)
def test_the_revalidation_window_admits_the_builtin_numbers_exactly(subclass_value):
    """The window's type gate is exact: a subclass of ``int`` or ``float`` is not one.

    A subclass may override ``__float__``, so admitting one would run consumer
    code inside the validator and let a raw exception replace the typed
    ``ConfigurationError`` the construction boundary promises. The well-behaved
    row states the resulting contract without hedging: the rejection is about the
    TYPE, not about whether a particular instance happens to misbehave, because
    only the type is knowable before the conversion runs.
    """
    with pytest.raises(ConfigurationError, match="websocket_revalidation_window"):
        _router(websocket_revalidation_window=subclass_value)


@pytest.mark.parametrize(
    ("accepted", "expected"),
    [
        pytest.param(0, 0.0, id="int-zero-is-coerced"),
        pytest.param(0.0, 0.0, id="explicit-default"),
        pytest.param(30, 30.0, id="int-seconds-are-coerced"),
        pytest.param(2.5, 2.5, id="fractional-seconds"),
        pytest.param(10**300, 1e300, id="astronomical-int-with-a-float-image"),
        pytest.param(1e308, 1e308, id="largest-order-of-magnitude-float"),
    ],
)
def test_the_revalidation_window_accepts_and_coerces_numbers(accepted, expected):
    """The accepted half, including the int -> float coercion.

    The consumer receives a ``float`` whatever the caller passed, so the window
    comparison never mixes numeric types.

    The last two rows are the honest boundary of the rejection above. A
    ``1e300``-second window is operationally "never revalidate
    again", and it is **accepted**: the package rejects values it cannot *use*, not
    values it disapproves of, and it imposes no ceiling for the same reason it
    imposes no maximum connection lifetime (Decision 12) - there is no correct
    default and any constant would be invented rather than derived. They also mark
    where ``int`` stops having a ``float`` image: these convert, and the
    ``10**10000`` row above does not, which is the whole distinction the guarded
    ``float()`` step exists to draw.
    """
    callback = _mounted_ws_callback(_router(websocket_revalidation_window=accepted))

    window = callback.consumer_initkwargs["revalidation_window"]
    assert window == expected
    assert isinstance(window, float)


def test_injecting_a_consumer_class_with_a_window_is_a_construction_error():
    """Spec-046 row 29: a knob that does nothing is worse than an error.

    The window configures the PACKAGE consumer, so a positive value alongside an
    injected class is rejected instead of silently ignored. An explicit ``0.0``
    stays legal - it configures nothing either way - which is the corner that
    keeps the rule about the window's EFFECT rather than about its presence.
    """

    class Injected(_graphql_ws_consumer()):
        pass

    with pytest.raises(ConfigurationError) as exc_info:
        _router(websocket_consumer_class=Injected, websocket_revalidation_window=5.0)
    assert _WINDOW_WITH_CLASS_SUBSTRING in str(exc_info.value)

    router = _router(websocket_consumer_class=Injected, websocket_revalidation_window=0.0)
    assert _mounted_ws_callback(router).consumer_class is Injected


def test_the_two_new_websocket_keywords_are_keyword_only():
    """All three WebSocket keywords are KEYWORD_ONLY, with their defaults.

    The sibling of the row whose subject is the ``url_pattern`` rename: this one
    extends the keyword-only contract to the two revalidation parameters, so a
    later convenience edit that relaxes one of them into a positional has to fail
    loudly. Read off ``inspect.signature`` rather than probed with a call, so the
    contract is asserted on the signature itself.
    """
    parameters = inspect.signature(_router_class().__init__).parameters

    keyword_only = {
        "websocket_url_pattern": r"^graphql/?$",
        "websocket_consumer_class": None,
        "websocket_revalidation_window": 0.0,
    }
    for name, default in keyword_only.items():
        assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY, name
        assert parameters[name].default == default, name
    # The two required transport arguments stay positional-or-keyword, in order.
    positional = [
        name
        for name, parameter in parameters.items()
        if parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]
    assert positional == ["self", "schema", "django_application"]


# ---------------------------------------------------------------------------
# Channels-present: execution through communicators
# ---------------------------------------------------------------------------


# The communicator tests carry ``django_db``: the WebSocket branch's
# ``AuthMiddlewareStack`` is DB-coupled (``get_user`` rides
# ``database_sync_to_async``), and Channels' consumer dispatch runs
# ``aclose_old_connections()`` outside the windows ``channels.testing``
# no-op-patches - under pytest-django's blocker an unmarked test would trip
# ``Database access not allowed`` whenever another test's executor-thread
# connection lingers (in-memory sqlite ``close()`` is a no-op).


@pytest.mark.django_db
async def test_http_branch_delegates_every_path_to_the_supplied_application():
    """Spec-046 Decision 13: HTTP is delegation, for GraphQL paths too.

    The merge of the old GraphQL-round-trip and non-GraphQL-fallback tests. Both
    a well-formed GraphQL POST at ``/graphql`` and an unrelated ``/admin/login/``
    GET reach the supplied application, which records each path and answers its
    own ``418``. No package route intercepts either - which is the whole content
    of Decision 2 on the HTTP side.
    """
    django_application = _RecordingDjangoApplication()
    router = _router(django_application=django_application)

    graphql_response = await _graphql_post(router, "{ ping }").get_response(timeout=10)
    assert graphql_response["status"] == 418
    assert graphql_response["body"] == b"django-application"

    other = HttpCommunicator(router, "GET", "/admin/login/")
    other_response = await other.get_response(timeout=10)
    assert other_response["status"] == 418

    assert django_application.paths == ["/graphql", "/admin/login/"]


@pytest.mark.parametrize(
    ("headers", "expected_connected"),
    [
        pytest.param([(b"origin", b"http://testserver")], True, id="matching-origin"),
        pytest.param([(b"origin", b"http://evil.example.com")], False, id="mismatched-origin"),
        pytest.param([], False, id="missing-origin"),
    ],
)
@pytest.mark.django_db
async def test_websocket_handshake_origin_directions(headers, expected_connected):
    """The three origin directions (match / mismatch / missing) on the WS branch.

    pytest-django's environment appends ``"testserver"`` to ``ALLOWED_HOSTS``,
    so ``http://testserver`` is the matching origin; a handshake with NO
    ``Origin`` header is denied exactly like a mismatched one
    (``ALLOWED_HOSTS`` never contains ``"*"`` in this suite).

    The parametrized headers carry the ORIGIN directions only, and an allowed
    ``Host`` is appended to each: this row's subject is Channels' origin check on
    its own, so the outer Host check (spec-046 Decision 19) must be satisfied for
    every direction rather than becoming a second reason for the denial. The
    Host directions, and the cross matrix that proves neither check does the
    other's work, are ``test_the_websocket_host_and_origin_checks_are_independent``.
    """
    router = _router()
    communicator = WebsocketCommunicator(
        router,
        "/graphql",
        headers=[*headers, (b"host", b"testserver")],
        subprotocols=["graphql-transport-ws"],
    )
    connected, detail = await communicator.connect(timeout=10)
    assert connected is expected_connected
    if connected:
        assert detail == "graphql-transport-ws"
    await communicator.disconnect()


@pytest.mark.parametrize(
    ("path", "expected_connected"),
    [
        pytest.param("/graphql", True, id="bare"),
        pytest.param("/graphql/", True, id="trailing-slash"),
        pytest.param("/graphql-admin", False, id="suffix-extension"),
        pytest.param("/graphqlanything", False, id="prefix-extension"),
        pytest.param("/graphql/extra", False, id="path-extension"),
    ],
)
@pytest.mark.django_db
async def test_default_websocket_url_pattern_matches_exactly(path, expected_connected):
    """Spec-046 row 11, behavioral half: the default pattern is exact.

    ``r"^graphql/?$"`` is anchored at both ends, so - with Channels' leading-slash
    strip - only ``/graphql`` and ``/graphql/`` reach the consumer; every prefix
    extension raises ``ValueError("No route found")`` out of the ``URLRouter``.
    The reject direction uses ``send_input`` + ``wait()`` rather than
    ``connect()``: ``connect()`` would sit out its whole timeout before
    re-raising the application task's exception.
    """
    router = _router()
    communicator = WebsocketCommunicator(
        router,
        path,
        headers=[(b"host", b"testserver"), (b"origin", b"http://testserver")],
        subprotocols=["graphql-transport-ws"],
    )
    if expected_connected:
        connected, detail = await communicator.connect(timeout=10)
        assert connected is True
        assert detail == "graphql-transport-ws"
        await communicator.disconnect()
        return

    await communicator.send_input({"type": "websocket.connect"})
    with pytest.raises(ValueError, match="No route found"):
        await communicator.wait(timeout=10)


@pytest.mark.django_db
async def test_schema_object_passes_through_unchanged_with_extensions_intact():
    """Spec-046 row 12: the consumer holds the exact schema; extensions execute.

    Subject preserved from the ``0.0.14`` test, transport moved: the HTTP
    consumer no longer exists to interrogate, so the structural half reads the
    WebSocket consumer's ``initkwargs`` and the execution half drives the
    operation over the WebSocket branch. Still the async-safe shape (no ORM, no
    ``DjangoType``): a recording Strawberry extension fires through the router.
    """
    fired = []

    class RecordingExtension(strawberry.extensions.SchemaExtension):
        def on_operation(self):
            fired.append("operation")
            yield

    recording_schema = strawberry.Schema(query=Query, extensions=[RecordingExtension])
    router = _router(recording_schema)

    ws_router = _ws_url_router(router)
    assert ws_router.routes[0].callback.consumer_initkwargs["schema"] is recording_schema

    data = await _ws_graphql_data(router, "{ ping }")
    assert data == {"ping": "pong"}
    assert fired == ["operation"]


# ---------------------------------------------------------------------------
# Channels-present: the WebSocket Host boundary (spec-046 Decision 19, Test plan
# rows 43-47). Channels'
# ``OriginValidator.__call__`` reads the ``Origin`` header and nothing else, so a
# handshake with an allowed ``Origin`` and a hostile ``Host`` connected - while
# ``routers.py`` promised an injected consumer "cannot escape Host/Origin
# validation". These rows own the Host half of that promise, and they prove it by
# DELEGATION to Django rather than by re-asserting a matching algorithm.
# ---------------------------------------------------------------------------

#: Channels' ``WebsocketDenier`` closes with the default ``1000``, and BOTH
#: handshake denials go through it - a refused ``Host`` is byte-identical on the
#: wire to a refused ``Origin``, which is why the package's validator reuses
#: Channels' consumer instead of closing the socket itself. RE-TYPED rather than
#: imported, the discipline every constant at the top of this module follows.
_DENIED_HANDSHAKE_CLOSE_CODE = 1000

#: Every ``META`` key the Host projection is allowed to produce, and the only ones
#: ``HttpRequest.get_host`` / ``get_port`` / ``_get_raw_host`` read. RE-TYPED rather
#: than derived from ``consumers.py::_HOST_META_KEYS_BY_HEADER``, so a projection
#: that started collecting a fifth key fails a test instead of widening the
#: expectation along with itself.
_HOST_META_KEYS = frozenset(
    {
        "HTTP_HOST",
        "HTTP_X_FORWARDED_HOST",
        "SERVER_NAME",
        "SERVER_PORT",
    },
)

#: A ``Host`` whose bytes are decodable as Latin-1 and NOT as UTF-8: ``0xe9`` alone
#: is a valid Latin-1 ``e-acute`` and an invalid UTF-8 sequence. That asymmetry is
#: what makes the projection's codec observable at all - every other header value in
#: this module is pure ASCII, where the two codecs agree.
_LATIN_1_ONLY_HOST_BYTES = b"caf\xe9.example"
_LATIN_1_ONLY_HOST = "caf\xe9.example"


def _django_http_host_verdict(*, host=None, forwarded_host=None, server=None):
    """Ask DJANGO the same Host question over HTTP; return its host or ``None``.

    The oracle for every delegation row. A real ``WSGIRequest``, built by Django's
    own ``RequestFactory``, answering the public ``HttpRequest.get_host()`` under
    whatever settings the calling row has overridden - never a second expectation
    typed out here. That distinction is the whole point of Decision 19: a
    hand-written expectation would pass just as happily against a package-local
    reimplementation of ``ALLOWED_HOSTS`` matching, so it could not prove the
    package delegates. ``None`` means ``DisallowedHost``, i.e. "Django refuses this
    host", which is the exact condition the WebSocket validator turns into a denial.
    """
    headers = {}
    if host is not None:
        headers["host"] = host
    if forwarded_host is not None:
        headers["x-forwarded-host"] = forwarded_host
    environ = {}
    if server is not None:
        environ["SERVER_NAME"], environ["SERVER_PORT"] = server[0], str(server[1])
    request = RequestFactory().get("/", headers=headers, **environ)
    try:
        return request.get_host()
    except DisallowedHost:
        return None


def _handshake_scope(headers, server=None):
    """The two ASGI keys the Host projection reads, plus what ``ASGIRequest`` demands.

    One scope builder feeding BOTH oracles below, so the projection and Django's own
    adapter can never be handed subtly different inputs. The four HTTP-only keys
    (``method`` / ``path`` / ``query_string`` / ``type``) exist solely because
    ``ASGIRequest.__init__`` reads them; ``_host_validation_request`` reads neither,
    which is the asymmetry Decision 19 cites for projecting into a plain
    ``HttpRequest`` instead.
    """
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": list(headers),
    }
    if server is not None:
        scope["server"] = server
    return scope


def _django_asgi_host_meta(headers, server=None):
    """Ask DJANGO's own ASGI adapter what ``META`` this handshake produces.

    The ``META`` oracle, standing beside ``_django_http_host_verdict``'s *verdict*
    oracle: ``django/core/handlers/asgi.py::ASGIRequest.__init__`` is the code
    ``consumers.py::_host_validation_request`` promises to reproduce "item by item",
    so the honest assertion for each item is equality against that constructor's own
    output for the same bytes - never a hand-typed table, which would agree with a
    projection that had quietly reinvented header casing, duplicate reduction, the
    transport codec, or Django's no-server literals.

    Narrowed to ``_HOST_META_KEYS`` because Django's adapter also projects the
    request line, the cookie header, ``REMOTE_ADDR`` and every other header - none of
    which participates in the Host decision, and none of which this boundary has any
    business carrying.
    """
    meta = ASGIRequest(_handshake_scope(headers, server), BytesIO()).META
    return {key: value for key, value in meta.items() if key in _HOST_META_KEYS}


def _django_asgi_host_verdict(headers, server=None):
    """Django's Host verdict for a handshake, with Django supplying the projection too.

    ``_django_http_host_verdict`` cannot express "this request carries no server
    information": ``RequestFactory`` unconditionally installs
    ``SERVER_NAME = "testserver"``, so its no-host leg silently answers a DIFFERENT
    question than the no-host-and-no-``server`` handshake. This oracle closes that
    hole by taking the ``META`` from Django's own ASGI adapter - including its
    ``"unknown"`` / ``"0"`` reconstruction - and asking the public
    ``HttpRequest.get_host()`` about it.

    Nothing from the package participates, which is what keeps it an oracle: the ONLY
    difference from the production path is where the four ``META`` keys came from, and
    that is precisely the thing under test.
    """
    request = HttpRequest()
    request.META.update(_django_asgi_host_meta(headers, server))
    try:
        return request.get_host()
    except DisallowedHost:
        return None


async def _ws_handshake(
    router,
    *,
    host=None,
    origin=None,
    extra_headers=(),
    server=None,
):
    """Drive ONE handshake through the router's WS branch; return ``(connected, detail)``.

    ``host`` / ``origin`` are spelled as optional str so a row can omit either
    header entirely (the missing-``Origin`` and no-host-header directions are both
    real cases), and ``server`` writes ``scope["server"]`` - the ASGI key Django's
    request adapter reads ``SERVER_NAME`` / ``SERVER_PORT`` from, which
    ``WebsocketCommunicator`` never synthesizes. Mutating ``communicator.scope``
    after construction is safe and deliberate: the communicator hands that very
    dict to the application, and nothing has run yet.
    """
    headers = list(extra_headers)
    if host is not None:
        headers.append((b"host", host.encode("latin1")))
    if origin is not None:
        headers.append((b"origin", origin.encode("latin1")))
    communicator = WebsocketCommunicator(
        router,
        "/graphql",
        headers=headers,
        subprotocols=[_TRANSPORT_WS],
    )
    if server is not None:
        communicator.scope["server"] = server
    try:
        return await communicator.connect(timeout=10)
    finally:
        await communicator.disconnect()


@pytest.mark.parametrize(
    ("headers", "server"),
    [
        pytest.param([(b"host", b"testserver")], ("testserver", 80), id="host-and-server"),
        pytest.param([(b"Host", b"testserver")], None, id="odd-cased-header-name"),
        pytest.param(
            [(b"host", b"a.example"), (b"host", b"b.example")],
            None,
            id="duplicate-host-headers",
        ),
        pytest.param([(b"x-forwarded-host", b"proxy.example")], None, id="forwarded-host-only"),
        pytest.param([(b"host", _LATIN_1_ONLY_HOST_BYTES)], None, id="latin-1-only-host-bytes"),
        pytest.param([], None, id="no-host-and-no-server"),
        pytest.param([], ("srv.example", 8000), id="server-only"),
        pytest.param(
            [(b"cookie", b"sessionid=x"), (b"origin", b"http://testserver")],
            None,
            id="only-headers-that-do-not-participate",
        ),
    ],
)
def test_the_host_projection_matches_djangos_asgi_adapter_key_for_key(headers, server):
    """Each projection item, its own row.

    ``consumers.py::_host_validation_request`` promises to reproduce
    ``ASGIRequest.__init__`` item by item, and the items are separable, so they get
    separable rows. Five of them were previously pinned by three behavioral rows
    between them - two items sharing one row, and the no-``server`` fallback pinned
    by nothing at all - which is the shape the weakly-pinned rule exists to refuse.

    One param per item, each asserted against Django's OWN constructor rather than a
    typed-out expectation:

    - ``odd-cased-header-name`` - the ``.lower()`` on the decoded name. ASGI says
      names arrive lowercase; Django's adapter normalizes anyway, so this does too,
      and dropping the normalization loses the header entirely.
    - ``duplicate-host-headers`` - the comma-join. Two values become ``"a,b"``, which
      is not a host, so ambiguity fails closed instead of one value being picked.
    - ``forwarded-host-only`` - the ``x-forwarded-host`` entry in the key map.
      Projected unconditionally; whether it WINS stays ``USE_X_FORWARDED_HOST``'s
      decision, made inside Django.
    - ``latin-1-only-host-bytes`` - the transport codec. ``0xe9`` decodes under
      Latin-1 and raises under UTF-8, so this is the one input that can tell them
      apart.
    - ``no-host-and-no-server`` - the ``"unknown"`` / ``"0"`` fallback, whose value is
      Django's literal and not the package's invention. This param is what makes that
      arm *consulted* rather than merely executed.
    - ``server-only`` / ``host-and-server`` - the ``scope["server"]`` arm, including
      the ``str()`` on the port.

    The subset assertion is the other half of the "item by item" promise, in the
    negative direction: the projection must produce NOTHING beyond the four keys
    ``get_host()`` reads, so a later edit that "completes" it with
    ``HTTP_X_FORWARDED_PORT`` or the ``SECURE_PROXY_SSL_HEADER`` header - both
    provably verdict-neutral - fails here rather than silently widening a security
    boundary's input surface.
    """
    projected = consumers_module._host_validation_request(_handshake_scope(headers, server)).META

    assert set(projected) <= _HOST_META_KEYS, projected
    assert projected == _django_asgi_host_meta(headers, server)


@pytest.mark.parametrize(
    ("host", "origin", "expected_connected"),
    [
        pytest.param("testserver", "http://testserver", True, id="both-allowed"),
        pytest.param("evil.example", "http://testserver", False, id="hostile-host"),
        pytest.param("testserver", "http://evil.example.com", False, id="hostile-origin"),
        pytest.param("testserver", None, False, id="missing-origin"),
        pytest.param("evil.example", "http://evil.example.com", False, id="both-hostile"),
    ],
)
@pytest.mark.django_db
async def test_the_websocket_host_and_origin_checks_are_independent(
    host,
    origin,
    expected_connected,
):
    """The direction the shipped suite never supplied.

    An allowed ``Origin`` with a hostile ``Host`` is the row that was missing, and
    it is the row that failed before Decision 19: ``OriginValidator`` loops the
    scope headers for ``b"origin"`` and never looks at ``Host``, so the handshake
    connected. Its converse (allowed ``Host``, hostile or missing ``Origin``) and
    the both-allowed control are here too, so neither check can be shown to be
    doing the other's work - passing one has never substituted for passing the
    other.

    The denial's shape is asserted as well as its existence: every refusal closes
    with the SAME code, because both validators deny through Channels'
    ``WebsocketDenier``. A ``Host`` refusal is therefore indistinguishable on the
    wire from an ``Origin`` refusal, which is the non-disclosure property the
    package gets for free by reusing Channels' consumer.
    """
    router = _router()
    connected, detail = await _ws_handshake(router, host=host, origin=origin)

    assert connected is expected_connected
    assert detail == (_TRANSPORT_WS if connected else _DENIED_HANDSHAKE_CLOSE_CODE)


@pytest.mark.parametrize(
    ("allowed_hosts", "host", "origin"),
    [
        pytest.param(["*"], "anything.example", "http://anything.example", id="wildcard"),
        pytest.param([".example.com"], "api.example.com", "http://api.example.com", id="dot"),
        pytest.param(["testserver"], "testserver:8000", "http://testserver:8000", id="port"),
        pytest.param(["[::1]"], "[::1]", "http://[::1]", id="ipv6"),
        pytest.param(["example.com"], "example.com.", "http://example.com", id="trailing-dot"),
        pytest.param(["testserver"], "bad_host", "http://testserver", id="malformed"),
        pytest.param(["testserver"], "", "http://testserver", id="empty"),
    ],
)
@pytest.mark.django_db
async def test_django_owns_the_websocket_host_matching(allowed_hosts, host, origin):
    """The verdict IS Django's verdict, asserted by delegation.

    Wildcards, leading-dot subdomain patterns, an explicit port, an IPv6 literal, a
    trailing dot, an underscore that RFC 1034/1035 forbids, and an empty header -
    seven behaviors the package would otherwise have had to implement, and
    implement identically to Django forever. None of them is asserted against a
    hardcoded expectation: each row asks ``HttpRequest.get_host()`` the same
    question over HTTP and requires the socket to agree. A future edit that
    "optimizes" the projection into a hostname comparison fails here even if its
    author's own expectation is internally consistent.

    The ``Origin`` of each row is chosen to PASS, so the only variable is the Host
    decision. ``AllowedHostsOriginValidator`` reads ``ALLOWED_HOSTS`` at
    CONSTRUCTION, so the router is built inside the override.
    """
    with override_settings(ALLOWED_HOSTS=allowed_hosts):
        router = _router()
        connected, _detail = await _ws_handshake(router, host=host, origin=origin)
        django_verdict = _django_http_host_verdict(host=host)

    assert connected is (django_verdict is not None)


@pytest.mark.django_db
async def test_the_debug_localhost_default_matches_djangos_own_websocket_side():
    """``DEBUG`` + empty ``ALLOWED_HOSTS`` is Django's decision too.

    The one arm of ``get_host()`` that consults a setting other than
    ``ALLOWED_HOSTS``, and the shape fakeshop itself ships (``DEBUG = True``,
    ``ALLOWED_HOSTS = []``). Delegating means the package neither knows nor spells
    Django's ``[".localhost", "127.0.0.1", "[::1]"]`` default - note it is not even
    the same list Channels uses for origins - and a hostile host is still refused
    under ``DEBUG``, which is what stops "development convenience" from reading as
    "no boundary".
    """
    with override_settings(DEBUG=True, ALLOWED_HOSTS=[]):
        router = _router()
        allowed, _ = await _ws_handshake(router, host="localhost", origin="http://localhost")
        hostile, _ = await _ws_handshake(router, host="evil.example", origin="http://localhost")

        assert allowed is (_django_http_host_verdict(host="localhost") is not None)
        assert hostile is (_django_http_host_verdict(host="evil.example") is not None)

    assert allowed is True
    assert hostile is False


@pytest.mark.django_db
async def test_duplicate_host_headers_fail_closed_in_djangos_comma_joined_form():
    """Ambiguity fails closed, in Django's own comma-joined form.

    Two ``Host`` headers are not a host, and the projection must not silently pick
    one. The joined form is not invented here either: Django's ASGI request adapter
    reduces duplicate headers with ``",".join(...)``, and this row reads that
    adapter's own ``META`` to prove the form matches before showing that Django
    refuses the joined value and that the socket is denied.

    Both duplicated values are ALLOWED on their own (``testserver`` is the one host
    this test environment permits), so nothing but the reduction can be producing the
    denial: a last-value-wins or first-value-wins projection connects here.
    """
    duplicated = [(b"host", b"testserver"), (b"host", b"testserver")]
    joined = ASGIRequest(_handshake_scope(duplicated), BytesIO()).META["HTTP_HOST"]
    assert joined == "testserver,testserver"
    assert _django_http_host_verdict(host=joined) is None
    assert _django_http_host_verdict(host="testserver") is not None

    duplicate, _ = await _ws_handshake(
        _router(),
        origin="http://testserver",
        extra_headers=duplicated,
    )
    assert duplicate is False


@pytest.mark.django_db
async def test_an_odd_cased_host_header_still_reaches_the_boundary():
    """Header-name casing is normalized, not trusted.

    Its own row rather than a tail on the duplicate-header row, which is where it
    used to live: casing normalization and duplicate reduction are two independent
    projection items, and one row cannot fail for two reasons and still say which.

    ASGI specifies lowercase header names, and Django's own adapter normalizes
    anyway. Dropping the normalization here does not raise or mismatch - the header
    simply never matches the key map, the handshake falls through to the
    ``"unknown"`` reconstruction, and a perfectly legitimate client is refused. So
    the assertion is that this handshake CONNECTS.
    """
    odd_cased, detail = await _ws_handshake(
        _router(),
        origin="http://testserver",
        extra_headers=[(b"Host", b"testserver")],
    )

    assert odd_cased is True
    assert detail == _TRANSPORT_WS


@pytest.mark.django_db
async def test_a_handshake_carrying_no_host_information_at_all_is_denied():
    """The fallback arm's verdict, pinned behaviorally.

    No ``Host``, no ``X-Forwarded-Host``, no ``scope["server"]`` - which is exactly
    what ``channels.testing.WebsocketCommunicator`` synthesizes by default, and what
    a non-conformant ASGI server can produce. Every other WebSocket row in this
    module EXECUTES the ``"unknown"`` / ``"0"`` arm and CONSULTS none of it, because
    every one of them also supplies an allowed ``Host`` and so takes
    ``_get_raw_host``'s ``HTTP_HOST`` branch. That is statement coverage without
    behavioral coverage - the shape a fail-open expression hides in - so this row
    exists to make the fallback decide a verdict.

    The verdict is a denial, and it is Django's denial rather than the package's:
    ``"unknown"`` reconstructs to ``"unknown:0"`` (port ``0`` is not ``80``), which
    ``get_host()`` refuses under any ``ALLOWED_HOSTS`` that does not contain
    ``"unknown"`` or ``"*"``. Asserted against ``_django_asgi_host_verdict`` rather
    than the ``RequestFactory`` oracle every other delegation row uses, because that
    one CANNOT express this input: ``RequestFactory`` always installs
    ``SERVER_NAME = "testserver"``, so its no-host leg answers a different question.
    The control leg is what stops this from passing on a router that denies
    everything.
    """
    assert _django_asgi_host_verdict([]) is None

    router = _router()
    no_host_information, _ = await _ws_handshake(router, origin="http://testserver")
    control, detail = await _ws_handshake(router, host="testserver", origin="http://testserver")

    assert no_host_information is False
    assert (control, detail) == (True, _TRANSPORT_WS)


@pytest.mark.django_db
async def test_a_latin_1_only_host_header_is_decoded_rather_than_crashing():
    """The transport codec, on the one input that shows it.

    ``b"caf\\xe9.example"`` is valid Latin-1 and invalid UTF-8, so it is the only
    kind of value that can tell the projection's codec apart from a plausible
    alternative. Latin-1 is Django's and Channels' ASGI transport convention
    (``ASGIRequest.__init__`` and ``OriginValidator`` both use it), and the
    consequence of getting it wrong is not a different verdict but a raised
    ``UnicodeDecodeError`` - which the validator deliberately does NOT convert into a
    denial - only a disallowed host becomes one - so the handshake would fail with
    a traceback out of the ASGI application instead of a verdict.

    The verdict itself is a denial either way, because ``split_domain_port``'s
    ``host_validation_re`` admits only ``[a-z0-9.-]`` - so this row's subject is that
    the boundary reached a DECISION at all, agreeing with Django's HTTP answer for
    the same decoded value.
    """
    assert _django_http_host_verdict(host=_LATIN_1_ONLY_HOST) is None

    denied, detail = await _ws_handshake(
        _router(),
        origin="http://testserver",
        extra_headers=[(b"host", _LATIN_1_ONLY_HOST_BYTES)],
    )

    assert denied is False
    assert detail == _DENIED_HANDSHAKE_CLOSE_CODE


@pytest.mark.parametrize("use_x_forwarded_host", [True, False])
@pytest.mark.django_db
async def test_x_forwarded_host_is_honoured_only_under_the_django_setting(use_x_forwarded_host):
    """``USE_X_FORWARDED_HOST`` behaves identically to HTTP.

    ``X-Forwarded-Host`` is projected unconditionally and consulted only by
    ``HttpRequest._get_raw_host``, so the setting stays Django's decision and the
    WebSocket answer follows the HTTP one with no package-side branch. The row is
    built so the two headers DISAGREE - a hostile ``Host`` and an allowed
    ``X-Forwarded-Host`` - because that is the only shape in which the precedence
    is observable at all.

    Both assertions are load-bearing: the first is the delegation proof, the second
    rules out the degenerate case where the oracle and the socket agree because
    NEITHER honours the forwarded header.
    """
    with override_settings(
        ALLOWED_HOSTS=["testserver"],
        USE_X_FORWARDED_HOST=use_x_forwarded_host,
    ):
        router = _router()
        connected, _ = await _ws_handshake(
            router,
            host="evil.example",
            origin="http://testserver",
            extra_headers=[(b"x-forwarded-host", b"testserver")],
        )
        django_verdict = _django_http_host_verdict(
            host="evil.example",
            forwarded_host="testserver",
        )

    assert connected is (django_verdict is not None)
    assert connected is use_x_forwarded_host


@pytest.mark.django_db
async def test_a_hostile_x_forwarded_host_is_refused_even_behind_an_allowed_host():
    """The forwarded header's DENY direction.

    The row above proves ``X-Forwarded-Host`` can rescue a hostile ``Host`` when the
    setting is on. This one proves the converse, which is the security-relevant half:
    with the setting on, an allowed ``Host`` does NOT rescue a hostile
    ``X-Forwarded-Host``, because ``_get_raw_host`` consults the forwarded value
    FIRST and never looks at the other. A projection that stopped collecting the
    forwarded key would connect here - the deny direction and the allow direction
    therefore fail independently, rather than the whole header resting on one row.
    """
    with override_settings(ALLOWED_HOSTS=["testserver"], USE_X_FORWARDED_HOST=True):
        router = _router()
        connected, detail = await _ws_handshake(
            router,
            host="testserver",
            origin="http://testserver",
            extra_headers=[(b"x-forwarded-host", b"evil.example")],
        )
        django_verdict = _django_http_host_verdict(
            host="testserver",
            forwarded_host="evil.example",
        )

    assert django_verdict is None
    assert connected is False
    assert detail == _DENIED_HANDSHAKE_CLOSE_CODE


@pytest.mark.django_db
async def test_with_no_host_header_the_scope_server_supplies_djangos_fallback():
    """``scope["server"]`` is Django's normal no-host-header fallback.

    ``_get_raw_host``'s third option reconstructs the host from ``SERVER_NAME`` /
    ``SERVER_PORT``, so the projection supplies them from the ASGI ``server`` key
    exactly as Django's request adapter does - including its ``"unknown"`` / ``"0"``
    default, which is what every other row in this module exercises by carrying no
    ``server`` at all. Without this the boundary would raise ``KeyError`` on a
    handshake that omits ``Host``, and an unexpected exception is deliberately NOT
    a denial - only a disallowed host becomes one - so the socket would fail with
    a traceback instead of a
    verdict.
    """
    with override_settings(ALLOWED_HOSTS=["fallback.example"]):
        router = _router()
        allowed, _ = await _ws_handshake(
            router,
            origin="http://fallback.example",
            server=["fallback.example", 80],
        )
        hostile, _ = await _ws_handshake(
            router,
            origin="http://fallback.example",
            server=["evil.example", 80],
        )

        assert allowed is (_django_http_host_verdict(server=["fallback.example", 80]) is not None)
        assert hostile is (_django_http_host_verdict(server=["evil.example", 80]) is not None)

    assert allowed is True
    assert hostile is False


@pytest.mark.django_db
async def test_only_disallowed_host_becomes_a_websocket_denial(monkeypatch):
    """An unexpected exception propagates instead of being reported as a host.

    The worst available failure mode for a check whose whole value is that it
    rejects: a projection bug that denied every handshake would be
    indistinguishable from correct ``ALLOWED_HOSTS`` enforcement, so nobody would
    ever find it. Only ``DisallowedHost`` is normalized into a denial; everything
    else is left to surface out of the ASGI application.

    ``send_input`` + ``wait()`` rather than ``connect()``, the shape the
    no-route-found row already uses: ``connect()`` would sit out its whole timeout
    before re-raising the application task's exception.
    """
    router = _router()

    def exploding_projection(scope):
        raise RuntimeError("projection bug")

    monkeypatch.setattr(consumers_module, "_host_validation_request", exploding_projection)
    communicator = WebsocketCommunicator(
        router,
        "/graphql",
        headers=[(b"host", b"testserver"), (b"origin", b"http://testserver")],
        subprotocols=[_TRANSPORT_WS],
    )
    await communicator.send_input({"type": "websocket.connect"})
    with pytest.raises(RuntimeError, match="projection bug"):
        await communicator.wait(timeout=10)


@pytest.mark.django_db
async def test_a_non_conformant_header_shape_propagates_instead_of_denying():
    """The same contract, with nothing monkeypatched.

    The row above injects the failure; this one is the naturally occurring shape, and
    the two fail independently. ASGI requires ``scope["headers"]`` to be a sequence
    of ``(bytes, bytes)`` pairs, so a server that hands over ``str`` names is
    non-conformant - and the projection's ``raw_name.decode(...)`` raises
    ``AttributeError`` on it from inside the real production call, no patch involved.

    That must surface, not deny. Widening the ``except DisallowedHost`` to
    ``except Exception`` would turn every such handshake into a well-formed
    ``ALLOWED_HOSTS`` refusal, which is indistinguishable from the boundary working
    correctly - the one failure mode nobody would ever find. So the assertion is
    that the exception reaches the caller.
    """
    communicator = WebsocketCommunicator(
        _router(),
        "/graphql",
        headers=[("host", "testserver")],
        subprotocols=[_TRANSPORT_WS],
    )
    await communicator.send_input({"type": "websocket.connect"})
    with pytest.raises(AttributeError, match="decode"):
        await communicator.wait(timeout=10)


@pytest.mark.parametrize("subdomain", ["sub.localhost", "deep.sub.localhost"])
@pytest.mark.django_db
async def test_the_debug_host_and_origin_defaults_diverge_on_a_localhost_subdomain(subdomain):
    """The one configuration where the two lists differ.

    ``DEBUG`` with an empty ``ALLOWED_HOSTS`` is the only case where either check
    consults a list other than ``ALLOWED_HOSTS``, and the two lists are NOT the same:
    Django's Host fallback is ``[".localhost", "127.0.0.1", "[::1]"]`` - dot-prefixed,
    so ``is_same_domain`` matches every subdomain at any depth - while
    ``AllowedHostsOriginValidator``'s is ``["localhost", "127.0.0.1", "[::1]"]``, with
    no dot, so it matches ``localhost`` exactly. Any ``*.localhost`` name is therefore
    an acceptable **Host** and an unacceptable **Origin** in a development
    configuration.

    Delegating means the package inherits both behaviors rather than reconciling them,
    and the net verdict is the stricter of the two - so the divergence never opens
    anything. It is pinned precisely because the Host check is the PERMISSIVE one
    here: without these rows a change to the Origin side that adopted Django's
    dot-prefixed list would open every ``*.localhost`` origin under ``DEBUG`` with
    nothing failing. That mutation is invisible to every other row in this module,
    which all use ``evil.example.com`` or a missing ``Origin``, so the two depths are
    parametrized deliberately - dot-prefixed matching is depth-independent, and one
    row per depth means the property does not rest on a single assertion.

    All three legs are asserted (Host accepts, Origin refuses, socket denied) so a
    regression on either side is attributable rather than only visible in the net
    answer.
    """
    origin = f"http://{subdomain}"
    with override_settings(DEBUG=True, ALLOWED_HOSTS=[]):
        assert _django_http_host_verdict(host=subdomain) == subdomain
        assert AllowedHostsOriginValidator(None).valid_origin(urlparse(origin)) is False

        router = _router()
        divergent, detail = await _ws_handshake(router, host=subdomain, origin=origin)
        control, _ = await _ws_handshake(router, host="localhost", origin="http://localhost")

    assert divergent is False
    assert detail == _DENIED_HANDSHAKE_CLOSE_CODE
    assert control is True


def _recording_websocket_application(reached):
    """An ASGI app that RECORDS being reached, then accepts the socket.

    The consumer-side sentinel for the ordering rows: it is mounted through the
    ``websocket_consumer_class`` factory seam, so reaching it means the handshake
    got all the way past every router-applied wrapper. It accepts rather than
    returning immediately so the allowed-``Host`` control leg completes a normal
    ``connect()`` instead of waiting out a timeout.
    """

    async def application(scope, receive, send):
        reached.append(scope["path"])
        assert (await receive())["type"] == "websocket.connect"
        await send({"type": "websocket.accept", "subprotocol": scope["subprotocols"][0]})

    return application


@pytest.mark.django_db
async def test_a_hostile_host_is_denied_before_the_auth_stack_and_the_consumer(monkeypatch):
    """Decision 19 #"before authentication": the ordering, with two sentinels.

    "Outermost" is a structural claim; this is the behavioral one. Two sentinels
    that MUST fire on an allowed ``Host`` and MUST NOT fire on a hostile one:

    - ``CookieMiddleware.__call__`` - the outermost layer of the router's own
      ``AuthMiddlewareStack``, so it is the first thing authentication does at all;
      patched to record and DELEGATE, which keeps the real stack running for the
      control leg; and
    - an injected ASGI application, standing in for the consumer, whose
      construction and dispatch are what the denial has to precede.

    A denial that fired after the session middleware had already loaded a session
    would still look like a denial on the wire, which is exactly why the wire is
    not what this row reads.
    """
    reached = []
    auth_stack_entries = []
    original_call = CookieMiddleware.__call__

    async def recording_call(
        self,
        scope,
        receive,
        send,
    ):
        auth_stack_entries.append(scope["path"])
        await original_call(self, scope, receive, send)

    monkeypatch.setattr(CookieMiddleware, "__call__", recording_call)
    router = _router(
        websocket_consumer_class=lambda schema: _recording_websocket_application(reached),
    )

    hostile, _ = await _ws_handshake(router, host="evil.example", origin="http://testserver")
    assert hostile is False
    assert auth_stack_entries == []
    assert reached == []

    allowed, _ = await _ws_handshake(router, host="testserver", origin="http://testserver")
    assert allowed is True
    assert auth_stack_entries == ["/graphql"]
    assert reached == ["/graphql"]


@pytest.mark.django_db
async def test_an_injected_consumer_is_denied_by_both_handshake_boundaries():
    """Spec-046 row 28 + Decision 19: injection opts out of neither check.

    The behavioral half of the structural row above. Both wrappers are the ROUTER's,
    so a consumer injected through the seam is inside both by construction - and
    "by construction" is worth measuring once, because the seam's entire safety
    argument is that a project cannot mount its own consumer outside the handshake
    boundaries even by accident.
    """
    reached = []
    router = _router(
        websocket_consumer_class=lambda schema: _recording_websocket_application(reached),
    )

    hostile_host, _ = await _ws_handshake(router, host="evil.example", origin="http://testserver")
    hostile_origin, _ = await _ws_handshake(
        router,
        host="testserver",
        origin="http://evil.example",
    )
    allowed, detail = await _ws_handshake(router, host="testserver", origin="http://testserver")

    assert (hostile_host, hostile_origin, allowed) == (False, False, True)
    assert detail == _TRANSPORT_WS
    assert reached == ["/graphql"]


# ---------------------------------------------------------------------------
# Channels-absent + degraded installs: the eviction-simulated states
# Absence is SIMULATED with the shared ``None`` sentinel +
# strict ``sys.modules`` eviction/restore, two-sided (the parent package's
# ``routers`` attribute is restored to the SAME original module object as
# ``sys.modules``, because a retried import re-executes ``routers.py`` and rebinds
# the attribute to a fresh module with its own empty ``_ROUTER_CLASS`` cache).
# Evicting ``django_strawberry_framework.routers`` drops that cache so the guard
# actually re-fires (``routers.py::_build_router_class`` short-circuits on a warm
# cache without calling ``require_channels``).
# ---------------------------------------------------------------------------

_CHANNELS_PREFIXES = (
    "channels",
    "strawberry.channels",
    "daphne",
    "django_strawberry_framework.routers",
)


@pytest.fixture
def _simulate_channels_absent():
    with simulated_absence(
        "channels",
        *_CHANNELS_PREFIXES,
        parent=django_strawberry_framework,
        attr="routers",
    ):
        yield


def test_root_package_and_star_import_stay_channels_free(_simulate_channels_absent):
    """The root package never touches the guard; the SUBMODULE star opts in."""
    mod = importlib.import_module("django_strawberry_framework")
    assert mod is django_strawberry_framework
    namespace = {}
    exec("from django_strawberry_framework import *", namespace)
    assert "DjangoGraphQLProtocolRouter" not in namespace
    # ``__all__`` names the lazy symbol, so ``import *`` reaches for it and
    # fires the guard (Decision 3).
    with pytest.raises(ImportError, match=_HINT_SUBSTRING):
        exec("from django_strawberry_framework.routers import *", {})


def test_routers_module_import_succeeds_without_channels(_simulate_channels_absent):
    """``import django_strawberry_framework.routers`` itself pays no import."""
    mod = importlib.import_module("django_strawberry_framework.routers")
    assert mod.__name__ == "django_strawberry_framework.routers"


def test_symbol_access_raises_the_install_hint_without_channels(_simulate_channels_absent):
    """The ``from ... import`` line raises ``ImportError`` naming the floor."""
    with pytest.raises(ImportError, match=_HINT_SUBSTRING) as exc_info:
        exec("from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter", {})
    assert isinstance(exc_info.value.__cause__, ImportError)


def test_restore_is_two_sided_and_the_present_path_works_again():
    """After teardown the attribute path and import path hold ONE module object.

    The blocked-then-retried import re-executes ``routers.py`` and rebinds the
    parent attribute to a fresh module; a one-sided restore would leave two live
    modules with independent ``_ROUTER_CLASS`` caches - the order-dependent
    Test-6 identity flake under ``pytest-xdist``.
    """
    with simulated_absence(
        "channels",
        *_CHANNELS_PREFIXES,
        parent=django_strawberry_framework,
        attr="routers",
    ):
        # Re-execute the module under absence (the rebinding the restore must undo).
        importlib.import_module("django_strawberry_framework.routers")
        with pytest.raises(ImportError, match=_HINT_SUBSTRING):
            exec("from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter", {})

    assert (
        django_strawberry_framework.routers is sys.modules["django_strawberry_framework.routers"]
    )
    assert django_strawberry_framework.routers is routers_module
    # No stale negative caching (Helper-reuse D3): the present path works again
    # in the same process, through both access paths, yielding one class.
    assert _router_class() is routers_module.DjangoGraphQLProtocolRouter


def test_consumers_module_imports_with_channels_absent():
    """Spec-046 Decision 11: ``consumers.py`` is channels-free at import.

    Load-bearing rather than incidental: ``routers.py`` imports ``consumers.py``
    at MODULE level, above its own ``require_channels()`` guard, and that is only
    safe while the new module reaches for ``channels`` exclusively inside a
    coroutine body. If a module-level ``channels`` import ever appeared there,
    every consumer's ``import django_strawberry_framework.routers`` would raise
    the raw ``ImportError`` instead of the install hint, and the absence rows
    above would NOT catch it (they leave ``consumers`` in the module cache, so its
    body never re-runs).

    The identity assertion is what makes this a real proof: a re-executed module
    body produces a NEW module object, so ``is not`` against the module-scope
    import is direct evidence the body ran under the sentinel rather than
    answering from the cache. Same shape as
    ``tests/test_views.py::test_views_module_imports_with_channels_absent``, and
    the same two-sided ``(parent, attr)`` restore.
    """
    with simulated_absence(
        "channels",
        "strawberry.channels",
        "daphne",
        "django_strawberry_framework.consumers",
        parent=django_strawberry_framework,
        attr="consumers",
    ):
        assert sys.modules["channels"] is None
        assert "django_strawberry_framework.consumers" not in sys.modules

        module = importlib.import_module("django_strawberry_framework.consumers")

        assert module is not consumers_module
        assert callable(module.build_revalidating_consumer_class)
        assert module._DEFAULT_REVALIDATION_WINDOW == 0.0
        assert "strawberry.channels" not in sys.modules


def test_unrelated_attribute_miss_stays_a_plain_attribute_error(_simulate_channels_absent):
    """A non-router attribute miss raises ``AttributeError``, never the hint."""
    mod = importlib.import_module("django_strawberry_framework.routers")
    with pytest.raises(AttributeError, match="DefinitelyNotARouter"):
        _ = mod.DefinitelyNotARouter


@pytest.mark.parametrize(
    ("broken_submodule", "expected_substrings"),
    [
        pytest.param(
            "channels.security.websocket",
            [_HINT_SUBSTRING],
            id="channels-half",
        ),
        pytest.param(
            "strawberry.channels",
            [_HINT_SUBSTRING, _STRAWBERRY_FLOOR_SUBSTRING],
            id="strawberry-half",
        ),
    ],
)
def test_degraded_partial_install_raises_the_split_actionable_errors(
    broken_submodule,
    expected_substrings,
):
    """Present-but-incompatible installs name WHICH half is broken.

    Same eviction + two-sided-restore discipline as the absent path (so the
    re-executed module has no cached ``_ROUTER_CLASS`` and the builder import
    actually fires), but here the top-level
    ``channels`` re-imports cleanly and only one builder SUBMODULE is a ``None``
    sentinel: a failing ``channels.*`` import names the channels floor; a failing
    ``strawberry.channels`` consumer import names BOTH halves, so a broken
    Strawberry install is never misreported as a Channels problem. Both chain the
    original ``ImportError``.
    """
    with evicted_modules(
        *_CHANNELS_PREFIXES,
        parent=django_strawberry_framework,
        attr="routers",
    ):
        sys.modules[broken_submodule] = None
        with pytest.raises(ImportError) as exc_info:
            exec("from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter", {})
        message = str(exc_info.value)
        for substring in expected_substrings:
            assert substring in message
        assert isinstance(exc_info.value.__cause__, ImportError)


# ---------------------------------------------------------------------------
# Channels-present: the package request contract over WebSocket
#
# The HTTP colour of the request-adapter contract is gone with the transport
# (spec-046 Decision 2 - "the Channels request adapter is now a WebSocket-only
# shape"). ``ChannelsRequestAdapter.__getattr__``'s delegated read and
# ``_channels_scope``'s ``consumer.scope`` HTTP duck shape stay covered at the
# package tier by ``tests/utils/test_permissions.py``.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
async def test_request_contract_resolves_over_the_websocket_branch():
    """A framework-shaped resolver works under the Channels context.

    The WebSocket consumer is the context request, with scope directly on it.
    The router's ``AuthMiddlewareStack`` populates that scope, so
    ``request_from_info()`` resolves the Strawberry-Channels dict context to the
    wrapping adapter instead of raising ``ConfigurationError``, and the
    ``AuthMiddlewareStack``-populated ``scope["user"]`` is the (anonymous) actor.
    """
    router = _router()
    data = await _ws_graphql_data(router, "{ actor }")
    assert data == {"actor": "ChannelsRequestAdapter|True"}


@pytest.mark.django_db(transaction=True)
async def test_authenticated_session_round_trip_reaches_the_resolver():
    """A real session cookie flows through ``AuthMiddlewareStack`` to the actor.

    Subject preserved from the ``0.0.14`` test, transport moved: the cookie used
    to traverse the HTTP branch's ``AuthMiddlewareStack``, which the protocol
    split removed, so it now rides the WebSocket handshake headers into the one
    stack the package still composes.

    The user + session rows are created async-safely (``database_sync_to_async``,
    since ``AuthMiddlewareStack`` resolves the user on the event loop's executor
    thread); the resolver then sees the AUTHENTICATED user, not ``AnonymousUser``
    - what actually earns the "session user on the scope" claim.
    The mint itself now lives at module level (``_make_user_and_session``), where
    the revalidation rows share it; the assertions are unchanged.
    """
    _user, cookie, _session_key = await _make_user_and_session("channels_probe")
    router = _router()
    data = await _ws_graphql_data(router, "{ username }", cookie=cookie)
    assert data == {"username": "channels_probe"}


# ---------------------------------------------------------------------------
# Channels-present: per-operation actor revalidation (spec-046 Decision 11,
# Test plan rows 25-27 and 30). Every row drives a REAL socket through the
# package's own mount.
#
# The spec's "separate request" is covered from both directions. The out-of-band
# mutators are precise unit controls - one revocation shape each, no HTTP
# lifecycle in the way - and the logout row is the real thing: a second HTTP
# request, made while the socket stays open, that runs Django's own logout
# against the same session. Neither subsumes the other: the mutators would stay
# green if the logout path broke, and the logout row alone could not isolate the
# disabled-user or password-rotation shapes.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "revoke",
    [
        pytest.param(_flush_the_session, id="session-flushed"),
        pytest.param(_disable_the_user, id="user-disabled"),
        pytest.param(_rotate_the_password, id="password-rotated"),
    ],
)
@pytest.mark.django_db(transaction=True)
async def test_a_revoked_session_closes_the_socket_on_the_next_operation_without_reconnecting(
    revoke,
    monkeypatch,
):
    """Spec-046 row 25: one socket, three revocation shapes, no reconnect.

    Operation 1 executes as the authenticated actor. The session is then revoked
    out of band - its row deleted, the user disabled, or the password rotated,
    the three shapes ``channels.auth.get_user`` collapses to ``AnonymousUser`` -
    and operation 2 on the SAME communicator gets the connection-level close.
    Nothing reconnects: the socket is opened exactly once, by ``_open_ws``, and
    every later frame rides it.

    Two properties beyond the close. The read accounting pins window ``0.0`` as
    **one read per security checkpoint** - operation 1 pays two, admission plus
    its ``next`` frame - which is the price the window exists to let a deployment
    change. And operation 3 pins that the denial is stable *and free*: a client
    can have pipelined a frame behind the close, and the revoked connection
    refuses it from the connection-local flag with no further session read and
    nothing emitted. That operation is a controlled subscription precisely so the
    refusal is observable: its resolver never runs, so upstream's
    ``handle_subscribe`` was never reached.
    """
    user, cookie, session_key = await _make_user_and_session("revalidation_probe")
    probe = _instrument_revalidation(monkeypatch)
    router = _router()

    async with _open_ws(router, cookie=cookie) as communicator:
        first = await _ws_operation(communicator, "{ username }", op_id="1")
        assert first["type"] == "next", first
        assert first["payload"]["data"] == {"username": "revalidation_probe"}
        assert probe.reads == 2

        await revoke(user, session_key)

        await _send_operation(communicator, "{ username }", op_id="2")
        closed, frames = await _drain_until_close(communicator)
        assert frames == [], frames
        _assert_revoked_close(closed)
        assert probe.reads == 3

        refused = _controller("stable-denial")
        await _send_operation(
            communicator,
            _controlled_subscription("stable-denial"),
            op_id="3",
        )
        assert await communicator.receive_nothing(timeout=0.2)
        assert not refused.started.is_set(), "a revoked connection admitted another operation"
        assert probe.reads == 3


@pytest.mark.django_db(transaction=True)
async def test_a_valid_session_keeps_executing_and_the_next_operation_sees_the_refreshed_actor():
    """Spec-046 row 26: the refreshed actor is what the next operation observes.

    A valid session keeps executing, and the actor the second operation reads at
    ``request_from_info`` is the REFRESHED one, not the connect-time object: two
    identity fields are changed out of band between the operations and read back.
    That read is the single one the ``get_queryset`` visibility hook and
    ``DjangoModelPermission`` both resolve their actor through, so proving
    freshness there proves both layers - and only a genuine re-read can produce
    the new values, because the connect-time actor object holds the old ones.
    """
    user, cookie, _session_key = await _make_user_and_session("freshness_probe")
    router = _router()

    async with _open_ws(router, cookie=cookie) as communicator:
        first = await _ws_operation(communicator, "{ actorIdentity }", op_id="1")
        assert first["type"] == "next", first
        assert first["payload"]["data"] == {"actorIdentity": "freshness_probe|False"}

        await _rename_and_promote_the_user(user, "freshness_probe_renamed")

        second = await _ws_operation(communicator, "{ actorIdentity }", op_id="2")
        assert second["type"] == "next", second
        assert second["payload"]["data"] == {"actorIdentity": "freshness_probe_renamed|True"}


@pytest.mark.django_db(transaction=True)
async def test_the_revalidation_window_defers_the_denial_until_it_expires(monkeypatch):
    """Spec-046 row 27: inside the window a revoked session still executes.

    With ``websocket_revalidation_window=3600.0`` the accepted revocation delay
    is an hour, so operation 2 executes on the cached actor even though the
    session was already flushed. Advancing the clock past the window then closes
    the connection on operation 3 - proving the window defers the denial rather
    than disabling it.

    The read count is the other half, and it is what pins the window's *expanded*
    meaning: one read authorizes BOTH checkpoints while it is young enough, so two
    complete operations - four checkpoints - cost exactly one session read. A
    window that only covered admission would show three.

    The clock is advanced by monkeypatching ``consumers._monotonic``, the seam
    that exists for exactly this: an ``asyncio.sleep`` would make the row
    wall-clock dependent, and this suite runs under ``-W error`` with
    ``-n auto``.
    """
    user, cookie, session_key = await _make_user_and_session("window_probe")
    probe = _instrument_revalidation(monkeypatch)
    router = _router(websocket_revalidation_window=3600.0)

    async with _open_ws(router, cookie=cookie) as communicator:
        first = await _ws_operation(communicator, "{ username }", op_id="1")
        assert first["type"] == "next", first
        assert first["payload"]["data"] == {"username": "window_probe"}

        await _flush_the_session(user, session_key)

        inside = await _ws_operation(communicator, "{ username }", op_id="2")
        assert inside["type"] == "next", inside
        assert inside["payload"]["data"] == {"username": "window_probe"}
        assert probe.reads == 1

        advanced = time.monotonic() + 7200.0
        monkeypatch.setattr(consumers_module, "_monotonic", lambda: advanced)

        await _send_operation(communicator, "{ username }", op_id="3")
        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    assert probe.reads == 2


@pytest.mark.django_db(transaction=True)
async def test_the_legacy_graphql_ws_protocol_is_revalidated_at_handle_start():
    """The SECOND protocol's admission is revalidated too.

    ``graphql-ws`` is live on the package's mount (upstream's default
    ``subscription_protocols`` carries both), so its per-operation entry -
    ``handle_start`` - needs the same pre-hook. The response is now the same
    connection-level close ``graphql-transport-ws`` gets: with revocation
    connection-scoped there is no per-protocol rejection payload left to differ,
    which removed the one asymmetry the two call sites used to carry.

    The success baseline is a subscription because a query cannot execute on this
    protocol at all (see ``Subscription.tick``).
    """
    user, cookie, session_key = await _make_user_and_session("legacy_probe")
    router = _router()

    async with _open_ws(router, cookie=cookie, subprotocol=_LEGACY_WS) as communicator:
        first = await _ws_operation(communicator, _TICK_SUBSCRIPTION, op_id="1")
        assert first["type"] == "data", first
        assert first["payload"]["data"] == {"tick": "tock"}

        await _flush_the_session(user, session_key)

        await _send_operation(communicator, _TICK_SUBSCRIPTION, op_id="2")
        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)


@pytest.mark.django_db(transaction=True)
async def test_a_revalidation_store_failure_denies_the_operation_and_is_logged(
    monkeypatch,
    caplog,
):
    """Spec-046 row 30: a failed revalidation read fails CLOSED, and is logged.

    The fresh-store resolver raises, so the revalidation cannot answer. The
    connection is revoked and closed with the same reason a revoked session gets
    (no information disclosure about which happened), and the failure is reported
    through the package logger at ``ERROR`` with its traceback rather than
    swallowed. There is no fall back to the connection's cached actor, which is the
    property Edge cases requires.

    Operation 3 is what pins that the degrade does not *retry* into a read storm:
    once the connection is revoked, a pipelined frame is refused from the
    connection-local flag, so exactly ONE failure is logged however many
    operations arrive behind it.
    """
    _user, cookie, _session_key = await _make_user_and_session("failclosed_probe")
    router = _router()

    async with _open_ws(router, cookie=cookie) as communicator:
        first = await _ws_operation(communicator, "{ username }", op_id="1")
        assert first["type"] == "next", first

        _poison_the_session_store(monkeypatch)
        with caplog.at_level(logging.ERROR, logger="django_strawberry_framework"):
            await _send_operation(communicator, "{ username }", op_id="2")
            closed, frames = await _drain_until_close(communicator)

            refused = _controller("failclosed-denial")
            await _send_operation(
                communicator,
                _controlled_subscription("failclosed-denial"),
                op_id="3",
            )
            assert await communicator.receive_nothing(timeout=0.2)
            assert not refused.started.is_set()

    assert frames == [], frames
    _assert_revoked_close(closed)
    records = _package_logger_records(caplog)
    assert [record.levelname for record in records] == ["ERROR"]
    assert all(record.exc_info is not None for record in records)
    assert "fail-closed" in records[0].getMessage()


@pytest.mark.django_db(transaction=True)
async def test_a_failing_auth_backend_load_also_fails_closed(monkeypatch, caplog):
    """The same degrade, a second failure shape.

    The row above is the whole fail-closed contract resting on ONE injection point -
    ``utils/sessions.py::session_store_class``. The property is not "that resolver
    raising is handled"; it is "a revalidation that cannot answer denies". So this row
    breaks the OTHER half of ``_refreshed_actor``: ``channels.auth.get_user``, the
    call that performs the backend load, the ``user_can_authenticate`` check and the
    session-auth-hash comparison. It is imported per call inside the coroutine, so
    patching the attribute on ``channels.auth`` is what the production code resolves -
    no package seam is monkeypatched at all here.

    An operational read of the difference: the first row is "the session store is
    unreachable", this one is "the auth backend or user table is". Both must close the
    socket rather than continue on the cached actor, and neither may be the only shape
    the suite knows about.
    """
    import channels.auth

    _user, cookie, _session_key = await _make_user_and_session("backend_failure_probe")
    router = _router()

    async def exploding_get_user(scope):
        raise RuntimeError("auth backend unavailable")

    async with _open_ws(router, cookie=cookie) as communicator:
        first = await _ws_operation(communicator, "{ username }", op_id="1")
        assert first["type"] == "next", first

        monkeypatch.setattr(channels.auth, "get_user", exploding_get_user)
        with caplog.at_level(logging.ERROR, logger="django_strawberry_framework"):
            await _send_operation(communicator, "{ username }", op_id="2")
            closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    records = _package_logger_records(caplog)
    assert [record.levelname for record in records] == ["ERROR"]
    assert "fail-closed" in records[0].getMessage()


@pytest.mark.django_db
async def test_an_anonymous_socket_is_not_revalidated(monkeypatch, caplog):
    """The anonymous carve-out really skips the session read.

    No cookie, so ``scope["user"]`` is anonymous and there is no session actor to
    revalidate. The fresh-store resolver is poisoned for the whole row: if the
    early return did not happen the read would raise, the operation would be
    denied fail-closed, and this row would fail - so the successful operation
    plus the empty log is a positive proof that no read occurred, not merely that
    one was tolerated.
    """
    _poison_the_session_store(monkeypatch)
    router = _router()

    with caplog.at_level(logging.ERROR, logger="django_strawberry_framework"):
        data = await _ws_graphql_data(router, "{ actor }")

    assert data == {"actor": "ChannelsRequestAdapter|True"}
    assert _package_logger_records(caplog) == []


@pytest.mark.django_db(transaction=True)
async def test_a_subscribe_before_connection_init_is_closed_by_upstream_without_revalidating(
    monkeypatch,
    caplog,
):
    """An unacknowledged connection is upstream's 4401, not our rejection.

    The pre-hook's first decision is to pass an unacknowledged connection
    straight through, so what the client sees is upstream's own
    ``4401 Unauthorized`` close - identical to the un-patched package. The socket
    carries a REAL session cookie here, so the actor on the scope IS
    authenticated: only the acknowledged carve-out can be what skipped the read,
    and the poisoned resolver proves it was skipped.
    """
    _user, cookie, _session_key = await _make_user_and_session("unacked_probe")
    _poison_the_session_store(monkeypatch)
    router = _router()

    communicator = _ws_communicator(router, cookie=cookie)
    connected, _protocol = await communicator.connect(timeout=10)
    try:
        assert connected, "websocket handshake failed"
        with caplog.at_level(logging.ERROR, logger="django_strawberry_framework"):
            await communicator.send_json_to(
                {"type": "subscribe", "id": "1", "payload": {"query": "{ ping }"}},
            )
            closed = await communicator.receive_output(timeout=10)
    finally:
        await communicator.disconnect()

    assert closed == {"type": "websocket.close", "code": 4401, "reason": "Unauthorized"}
    assert _package_logger_records(caplog) == []


@pytest.mark.django_db(transaction=True)
async def test_revalidation_resolves_its_session_store_outside_the_opt_in_auth_package():
    """The revalidation does not import the auth subsystem.

    ``auth/__init__.py`` eagerly imports ``.mutations`` and ``.queries``, so the
    old ``from .auth.sessions import session_store_class`` made the FIRST
    authenticated operation on ANY socket import and register the whole opt-in
    GraphQL auth surface on the event loop - to read one settings string. The
    resolver now lives in ``utils/sessions.py``.

    Strict eviction is what makes the row provable rather than incidental: under
    ``--dist loadscope`` a worker that already ran ``tests/auth/`` has those
    modules cached, so a plain ``not in sys.modules`` assertion would pass no
    matter what the production import does - the exact masking this module used
    to suffer when it imported ``auth.sessions`` at collection time. Evicting
    the whole ``django_strawberry_framework.auth`` prefix - with the shared
    two-sided restore - means a re-pointed import would have to re-import it,
    which the assertion then sees.

    The operation round trip is the other half of the proof. Window ``0.0`` and an
    authenticated actor mean the revalidation MUST run, and a failed resolver
    fails closed, so ``next`` with the real username is only reachable
    if the store resolved through the new module - which the positive assertion on
    ``utils.sessions`` pins by name.
    """
    _user, cookie, _session_key = await _make_user_and_session("import_boundary_probe")
    router = _router()

    with evicted_modules(
        _AUTH_SUBSYSTEM_PREFIX,
        parent=django_strawberry_framework,
        attr="auth",
    ):
        async with _open_ws(router, cookie=cookie) as communicator:
            message = await _ws_operation(communicator, "{ username }", op_id="1")

        assert message["type"] == "next", message
        assert message["payload"]["data"] == {"username": "import_boundary_probe"}

        assert session_store_module.__name__ in sys.modules
        imported_auth = sorted(
            name for name in sys.modules if name.startswith(_AUTH_SUBSYSTEM_PREFIX)
        )
        assert imported_auth == [], (
            "the WebSocket revalidation imported the opt-in auth subsystem "
            f"({_AUTH_SUBSYSTEM_MODULES} must stay absent): {imported_auth}"
        )


@pytest.mark.django_db(transaction=True)
async def test_a_real_second_request_logout_denies_the_next_operation_on_the_open_socket():
    """Spec-046 row 25: the separate request is a REAL request.

    The direct-ORM revocation rows - session flushed, user disabled, password
    rotated - mutate the store in place: precise unit controls that stay, but none
    of them exercises a second HTTP request's own session lifecycle. This row does: while the socket stays open, an
    ``AsyncClient`` posts to a probe URLConf view that calls Django's own
    ``django.contrib.auth.logout``, so ``SessionMiddleware`` loads the session
    from the cookie, the engine flushes the record, and the response expires the
    cookie - the real revocation path a logout view, a cookie change, or a session
    backend swap would break while every direct-mutation row stayed green.

    The helper it delegates the request to is what makes it a proof rather than a
    coincidence: the second request reports the session key and actor it resolved,
    and the helper asserts it targeted the SAME session as the socket before this
    row asserts the denial. Only then is operation 2 on the ORIGINAL communicator -
    no reconnect, same handshake - refused, by the connection-level close.
    """
    _user, cookie, session_key = await _make_user_and_session("logout_probe")
    router = _router()

    async with _open_ws(router, cookie=cookie) as communicator:
        first = await _ws_operation(communicator, "{ username }", op_id="1")
        assert first["type"] == "next", first
        assert first["payload"]["data"] == {"username": "logout_probe"}

        await _logout_through_a_real_second_request(session_key, "logout_probe")

        await _send_operation(communicator, "{ username }", op_id="2")
        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)


# ---------------------------------------------------------------------------
# Channels-present: the OUTBOUND checkpoint. Admission cannot see an operation
# twice - both protocols park an admitted operation in their own result loop - so these rows drive operations
# that are still in flight when the session is revoked, and assert what the
# socket refuses to emit.
#
# Every row below owns its operation's timeline through ``_OperationController``
# and asserts three things a "no frame arrived" check cannot: that the payload
# really was produced (``emitted``), that the connection closed with the one
# documented code, and that the operation was unwound rather than abandoned
# (``finalized``).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("subprotocol", [_TRANSPORT_WS, _LEGACY_WS])
@pytest.mark.django_db(transaction=True)
async def test_a_running_subscription_cannot_emit_a_result_after_revocation(
    subprotocol,
    monkeypatch,
):
    """A revoked session cannot emit a result on an already-running
    subscription, on both protocols.

    The sequence: authenticate, start a multi-yield subscription while the
    session is valid, receive result 1, log out through a
    **real second HTTP request** while the subscription stays open, then release
    result 2. Result 2 is produced by the resolver and never reaches the wire;
    the whole socket closes with ``4403`` instead.

    Before the outbound checkpoint existed this row's ``frames`` would carry
    result 2 - upstream's ``run_operation`` / ``handle_async_results`` loop sends
    every later result without returning through the admission method, which is
    why ``Subscription.tick`` (one yield, then completion) could not detect it.

    The three tail assertions are the rest of the contract. ``emitted`` proves the
    payload existed and was suppressed rather than never generated. ``finalized``
    proves the operation was unwound - the generator's ``finally`` ran, because the
    stop-aware result source ended the loop and closed it - rather than left
    suspended for the interpreter's asyncgen finalizer. And the empty task set
    proves upstream's own disconnect / shutdown path finished the teardown: no
    operation task, no close attempt still in flight, no unawaited coroutine, no
    lingering async generator, under a suite that treats every warning as an error.
    """
    _user, cookie, session_key = await _make_user_and_session("running_probe")
    controller = _controller("running")
    probe = _instrument_revalidation(monkeypatch)
    router = _router()
    _operation_frame, success_frame = _PROTOCOL_FRAMES[subprotocol]

    async with _open_ws(router, cookie=cookie, subprotocol=subprotocol) as communicator:
        await _send_operation(communicator, _controlled_subscription("running"), op_id="1")
        await _reached(controller.started, "the operation was never admitted")

        controller.release(0)
        first = await communicator.receive_json_from(timeout=10)
        assert first["type"] == success_frame, first
        assert first["payload"]["data"] == {"controlled": "running-1"}
        # One read per checkpoint: this operation's admission, then its result.
        assert probe.reads == 2

        await _logout_through_a_real_second_request(session_key, "running_probe")

        controller.release(1)
        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    assert controller.emitted == ["running-1", "running-2"]
    assert probe.reads == 3
    assert controller.finalized, "the subscription generator was never unwound"
    assert [task for task in asyncio.all_tasks() if task is not asyncio.current_task()] == []


@pytest.mark.parametrize("subprotocol", [_TRANSPORT_WS, _LEGACY_WS])
@pytest.mark.django_db(transaction=True)
async def test_a_valid_session_keeps_a_running_subscription_emitting_every_result(
    subprotocol,
    monkeypatch,
):
    """The required control: the gate is not a mute button.

    The same socket, the same controlled subscription, and no revocation: both
    results arrive, in order, and the connection stays open. Without this row the
    suppression row above would be satisfied by an implementation that simply
    stopped emitting subscription results, and the read accounting would be
    satisfied by one that never revalidated at all - here it is one read per
    checkpoint, so admission plus two results is three.

    This is also the only row where information-bearing frames actually go out, so
    it is where the lease's placement is pinned: both sends happened while the
    connection's actor lease was still HELD. Releasing the lease after
    validation instead - the mutation the design explicitly rules out - changes
    nothing observable on the wire in this harness (see ``_record_outbound_gate``),
    so without this assertion that mutation would pass the whole suite.
    """
    _user, cookie, _session_key = await _make_user_and_session("control_probe")
    controller = _controller("control")
    gate = _record_outbound_gate(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    router = _router()
    _operation_frame, success_frame = _PROTOCOL_FRAMES[subprotocol]

    async with _open_ws(router, cookie=cookie, subprotocol=subprotocol) as communicator:
        await _send_operation(communicator, _controlled_subscription("control"), op_id="1")
        await _reached(controller.started, "the operation was never admitted")

        received = []
        for index in range(2):
            controller.release(index)
            message = await communicator.receive_json_from(timeout=10)
            assert message["type"] == success_frame, message
            received.append(message["payload"]["data"]["controlled"])

        assert received == ["control-1", "control-2"]
        # Still open: nothing closed the socket, and nothing else is queued.
        assert await communicator.receive_nothing(timeout=0.2)

    assert probe.reads == 3
    assert controller.emitted == ["control-1", "control-2"]
    # Every frame that DID go out went out under the connection's actor lease.
    assert gate.entries == ["1", "1"]
    assert gate.sends_under_lease == [True, True]
    # Upstream's teardown cancelled the still-running subscription on disconnect.
    assert controller.finalized


@pytest.mark.django_db(transaction=True)
async def test_a_delayed_query_revoked_after_admission_never_sends_its_response(monkeypatch):
    """The outbound checkpoint covers non-subscription operations too.

    A query is admitted, its resolver holds, the session is revoked, and the
    resolver then returns a perfectly good value. Upstream sends a query's single
    result through the very same ``Operation.send_next`` a subscription's results
    take, so the gate must refuse it identically - and ``emitted`` records that the
    resolver did run to completion, so this is a suppressed response rather than an
    aborted one.

    ``graphql-transport-ws`` only: the legacy protocol reaches Strawberry through
    ``Schema.subscribe`` and cannot execute a query at all (see
    ``Subscription.tick``).
    """
    user, cookie, session_key = await _make_user_and_session("delayed_query_probe")
    controller = _controller("delayed")
    probe = _instrument_revalidation(monkeypatch)
    router = _router()

    async with _open_ws(router, cookie=cookie) as communicator:
        await _send_operation(communicator, _controlled_query("delayed"), op_id="1")
        await _reached(controller.started, "the operation was never admitted")
        assert probe.reads == 1

        await _flush_the_session(user, session_key)

        controller.release(0)
        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    assert controller.emitted == ["delayed-1"]
    assert probe.reads == 2


@pytest.mark.parametrize("subprotocol", [_TRANSPORT_WS, _LEGACY_WS])
@pytest.mark.django_db(transaction=True)
async def test_an_operation_error_produced_after_revocation_is_suppressed_by_the_close(
    subprotocol,
    monkeypatch,
):
    """An operation-scoped ``error`` frame is gated like a payload.

    Runtime resolver errors ride inside ``next`` / ``data``, but a pre-execution
    error travels as its own ``error`` frame - ``Operation.send_initial_errors`` on
    ``graphql-transport-ws``, the first-result branch of ``handle_async_results`` on
    legacy ``graphql-ws`` - and it can still disclose schema, validation,
    extension, or consumer-authored detail. So it is gated too, and the connection
    closure replaces it rather than following it: no ``error`` frame precedes the
    close, which is the whole point of not sending one (protocol asymmetry plus a
    second race, for a rejection the close already delivers).

    The gated extension is what makes the timing real rather than hopeful: a
    validation error is otherwise produced with no ``await`` the test body could
    interleave a revocation with.
    """
    user, cookie, session_key = await _make_user_and_session("error_frame_probe")
    controller = _controller(_GATED_EXTENSION_CHANNEL)
    probe = _instrument_revalidation(monkeypatch)
    router = _router(GATED_SCHEMA)

    async with _open_ws(router, cookie=cookie, subprotocol=subprotocol) as communicator:
        await _send_operation(communicator, _INVALID_SUBSCRIPTION, op_id="1")
        await _reached(controller.started, "the operation was never admitted")
        assert probe.reads == 1

        await _flush_the_session(user, session_key)

        controller.release(0)
        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    assert probe.reads == 2


@pytest.mark.django_db(transaction=True)
async def test_the_connection_lock_stops_a_sibling_payload_escaping_after_revocation(
    monkeypatch,
):
    """Decision 11, the lease held through the send: the sibling race.

    The race the design exists to close: two operations on one socket, both
    authorized when they started. Operation ``a`` reaches the outbound checkpoint
    first and is held INSIDE its validation read; operation ``b`` produces its own
    result and queues at the connection's lease behind it; the session is then revoked
    while ``a`` is still holding. If the lease were released after validation rather
    than after the send, ``b`` could pass validation, ``a`` could observe the
    revocation and begin closing, and ``b``'s previously authorized payload would
    still go out.

    "``b`` is queued at the lease" is asserted rather than assumed: the recorded
    gate entries show ``b`` inside the checkpoint while ``a`` holds the lease, and
    the read count shows ``b`` performed no read of its own - it cannot have got
    past the lease. After the release, ``a`` fails, the connection closes, and
    ``b``'s frame is refused from the connection-local flag with no extra read at
    all: three reads for two admissions and one validated result. Dropping the lease
    altogether is what that count catches - ``b`` would then validate concurrently
    and the row would see four reads - while the *placement* of the release is
    pinned by the control row's ``sends_under_lease``.
    """
    user, cookie, session_key = await _make_user_and_session("sibling_probe")
    first_controller = _controller("sibling-a")
    second_controller = _controller("sibling-b")
    gate = _record_outbound_gate(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    router = _router()

    async with _open_ws(router, cookie=cookie) as communicator:
        for op_id, channel in (("a", "sibling-a"), ("b", "sibling-b")):
            await _send_operation(communicator, _controlled_subscription(channel), op_id=op_id)
        await _reached(first_controller.started, "operation a was never admitted")
        await _reached(second_controller.started, "operation b was never admitted")
        assert probe.reads == 2

        # ``a`` enters the checkpoint and parks inside the validation read.
        probe.hold = asyncio.Event()
        probe.entered.clear()
        first_controller.release(0)
        await _reached(
            probe.entered,
            "operation a never reached the outbound checkpoint's validation read",
        )
        assert gate.entries == ["a"], gate.entries
        assert probe.reads == 3
        consumer = gate.consumers[0]
        assert _actor_lease_held(consumer)

        # ``b`` produces its result and can only wait for the lease.
        second_controller.release(0)
        await _wait_until(
            lambda: gate.entries == ["a", "b"],
            lambda: f"the sibling never reached the outbound checkpoint: {gate.entries}",
        )
        assert probe.reads == 3

        # The session is revoked while ``a`` still holds the lease.
        await _flush_the_session(user, session_key)
        probe.hold.set()

        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    assert probe.reads == 3
    assert first_controller.emitted == ["sibling-a-1"]
    assert second_controller.emitted == ["sibling-b-1"]
    assert first_controller.finalized
    assert second_controller.finalized


@pytest.mark.django_db(transaction=True)
async def test_a_revoked_but_idle_socket_stays_open_until_its_next_protected_checkpoint(
    monkeypatch,
):
    """Decision 11, the accepted idle consequence: event-driven, not polled.

    The contract's honest limit, pinned so it stays a decision rather than an
    accident. Detection is event-boundary-driven: nothing polls, so a revoked
    socket that produces no further events performs **zero** database reads and
    stays physically open. That is accepted because it has no authorization
    capability while idle - which this row demonstrates in both directions:
    connection-control traffic (``ping`` -> ``pong``) keeps working and costs
    nothing, and the very next protected checkpoint closes the connection.

    A row asserting only the close would be satisfied by a background monitor,
    which Decision 11 rejects (it makes freshness a function of a detection
    interval and multiplies reads by idle connection count); the ``reads`` assertion
    across the idle window is what rules one out.
    """
    user, cookie, session_key = await _make_user_and_session("idle_probe")
    probe = _instrument_revalidation(monkeypatch)
    router = _router()

    async with _open_ws(router, cookie=cookie) as communicator:
        first = await _ws_operation(communicator, "{ username }", op_id="1")
        assert first["type"] == "next", first
        assert probe.reads == 2

        await _flush_the_session(user, session_key)

        # Idle and revoked: no background read, no close of its own.
        assert await communicator.receive_nothing(timeout=0.2)
        assert probe.reads == 2

        # Connection control is delegated to upstream unchanged, and pays nothing.
        await communicator.send_json_to({"type": "ping"})
        assert await communicator.receive_json_from(timeout=10) == {"type": "pong"}
        assert probe.reads == 2

        await _send_operation(communicator, "{ username }", op_id="2")
        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    assert probe.reads == 3


@pytest.mark.django_db(transaction=True)
async def test_the_connection_lock_never_serializes_a_second_connection(monkeypatch):
    """Decision 16, the lease's blast radius: one socket, not the process.

    The other half of the head-of-line tradeoff, and the half that makes it
    acceptable. While socket 1 is parked INSIDE its critical section - holding its
    own actor lease across a session read - socket 2 runs a complete operation
    to a delivered result. A lock at module or class scope (the shape a "simpler"
    implementation reaches for) would have made socket 2 wait on a stranger's
    database read; a per-connection lease cannot, and the two distinct scopes
    holding two distinct leases are what that rests on.

    ``probe.hold_key`` is why socket 2's own reads are not parked by the same probe:
    only socket 1's session key is held.
    """
    _first_user, first_cookie, first_key = await _make_user_and_session("blast_radius_one")
    _second_user, second_cookie, _second_key = await _make_user_and_session("blast_radius_two")
    controller = _controller("blast-radius")
    gate = _record_outbound_gate(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    router = _router()

    async with _open_ws(router, cookie=first_cookie) as first_socket:
        await _send_operation(
            first_socket,
            _controlled_subscription("blast-radius"),
            op_id="1",
        )
        await _reached(controller.started, "the operation was never admitted")

        # Park socket 1 inside its critical section, holding its own lock.
        probe.hold = asyncio.Event()
        probe.hold_key = first_key
        probe.entered.clear()
        controller.release(0)
        await _reached(probe.entered, "socket 1 never reached its validation read")
        first_consumer = gate.consumers[0]
        assert _actor_lease_held(first_consumer)

        # A DIFFERENT connection is unaffected: full round trip, its own lease.
        async with _open_ws(router, cookie=second_cookie) as second_socket:
            message = await _ws_operation(second_socket, "{ username }", op_id="1")
            assert message["type"] == "next", message
            assert message["payload"]["data"] == {"username": "blast_radius_two"}
            second_consumer = gate.consumers[-1]
            assert second_consumer is not first_consumer
            assert _actor_lease(second_consumer) is not _actor_lease(first_consumer)
            # Socket 1 is still parked, and its lease is still the only one held.
            assert _actor_lease_held(first_consumer)
            assert not _actor_lease_held(second_consumer)

        # Socket 1 then finishes normally - it was never revoked, only slow.
        probe.hold.set()
        first = await first_socket.receive_json_from(timeout=10)
        assert first["type"] == "next", first
        assert first["payload"]["data"] == {"controlled": "blast-radius-1"}

    assert gate.sends_under_lease == [True, True]


@pytest.mark.django_db(transaction=True)
async def test_a_positive_window_defers_the_close_on_a_running_subscription(monkeypatch):
    """Decision 16, the window at the frame checkpoint: one read per window.

    The window's expanded meaning, measured where it is hardest to get right - a
    subscription that is already running. Result 1 goes out on the read its
    admission performed. The session is then revoked, and result 2 **still goes
    out**, because the window has not elapsed and the window is an explicit,
    documented revocation delay rather than a bug. Advancing the clock past it makes
    the next frame revalidate, fail, and close the connection.

    The read count is the point of the row: two delivered frames and a third
    refused one cost exactly ONE read while the window held, not one per frame. A
    positive window that only cached across admissions would show three.
    """
    user, cookie, session_key = await _make_user_and_session("window_frame_probe")
    controller = _controller("window-frame")
    probe = _instrument_revalidation(monkeypatch)
    router = _router(websocket_revalidation_window=3600.0)

    async with _open_ws(router, cookie=cookie) as communicator:
        await _send_operation(communicator, _controlled_subscription("window-frame"), op_id="1")
        await _reached(controller.started, "the operation was never admitted")

        controller.release(0)
        first = await communicator.receive_json_from(timeout=10)
        assert first["payload"]["data"] == {"controlled": "window-frame-1"}
        assert probe.reads == 1

        await _flush_the_session(user, session_key)

        # Inside the accepted delay: the revoked session still emits.
        controller.release(1)
        inside = await communicator.receive_json_from(timeout=10)
        assert inside["payload"]["data"] == {"controlled": "window-frame-2"}
        assert probe.reads == 1

        advanced = time.monotonic() + 7200.0
        monkeypatch.setattr(consumers_module, "_monotonic", lambda: advanced)

        controller.release(2)
        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    assert controller.emitted == ["window-frame-1", "window-frame-2", "window-frame-3"]
    assert probe.reads == 2
    assert controller.finalized


@pytest.mark.django_db(transaction=True)
async def test_connection_control_frames_never_reach_the_outbound_checkpoint(monkeypatch):
    """Decision 16, frame-type discrimination: the negative half, on a valid socket.

    The fixture is deliberately a **valid** connection with a read counter, not a
    revoked one: on a revoked connection every frame is refused for a reason that
    has nothing to do with its type, which would prove nothing about the gated set.
    Here the socket is authorized throughout, so the recorded checkpoint entries are
    a direct census of which frames were gated.

    ``connection_ack`` (from ``_open_ws``), ``complete`` (from ``_ws_operation``),
    and ``pong`` all travel while exactly ONE frame - the operation's ``next`` -
    reaches the checkpoint, and the read count stays at the two the operation's own
    two checkpoints paid. Gating a control frame would price a keep-alive as an
    authorization event: the same socket would perform a session read per ping.
    """
    _user, cookie, _session_key = await _make_user_and_session("control_frame_probe")
    gate = _record_outbound_gate(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    router = _router()

    async with _open_ws(router, cookie=cookie) as communicator:
        # The acknowledgement is already behind us (``_open_ws`` asserts it) and it
        # cost nothing: no operation has run yet.
        assert probe.reads == 0
        assert gate.entries == []

        message = await _ws_operation(communicator, "{ username }", op_id="1")
        assert message["type"] == "next", message
        assert probe.reads == 2
        # The ``next`` frame was gated; the ``complete`` that followed it was not.
        assert gate.entries == ["1"]

        for _ in range(3):
            await communicator.send_json_to({"type": "ping"})
            assert await communicator.receive_json_from(timeout=10) == {"type": "pong"}

        assert probe.reads == 2
        assert gate.entries == ["1"]
        assert gate.sends_under_lease == [True]


#: Upstream's OWN default for ``max_subscriptions_per_connection``
#: (``strawberry/channels/handlers/ws_handler.py::GraphQLWSConsumer.__init__``, and
#: the same value on ``AsyncBaseHTTPView``). RE-TYPED, like every other floor
#: constant in this module: if upstream changes the default the row below stops
#: reaching the limit frame and says so, instead of silently pinning nothing. The
#: router exposes no knob for it, which is exactly why the number matters - and why
#: the guard it makes reachable was once recorded as untestable.
_UPSTREAM_SUBSCRIPTION_LIMIT = 100


@pytest.mark.parametrize("subprotocol", [_TRANSPORT_WS, _LEGACY_WS])
@pytest.mark.django_db(transaction=True)
async def test_the_subscription_limit_error_frame_is_gated_from_the_connections_own_task(
    subprotocol,
    monkeypatch,
):
    """The outbound checkpoint reached from ``run_task``.

    The ONE production path that reaches the outbound checkpoint from the
    connection's own message-loop task rather than from an operation task: both
    protocols emit their subscription-limit ``error`` frame from inside
    ``handle_subscribe`` / ``handle_start``, i.e. from the message loop itself,
    after the package's admission hook has already passed. There is no operation of
    the package's to stop here, so the close alone is the whole rejection - and the
    message loop must be left to unwind normally, because it is what cancels and
    awaits the hundred operations still registered.

    Reaching it needs no new seam and no injected consumer - only upstream's own
    default limit, which is ``100`` rather than ``None``. So the row opens
    ``_UPSTREAM_SUBSCRIPTION_LIMIT`` controlled operations that never complete, sends
    one more, and lets the revalidation invalidate on the read the 101st operation's
    OUTBOUND checkpoint takes (its admission read, number 101, still succeeds). The
    frame is then suppressed, the connection revoked, and the socket closed.

    What the four assertions pin, separately:

    - ``frame_types`` / ``entries`` - exactly one frame reached the checkpoint, it was
      the ``error`` frame, and it belonged to the over-limit operation. Nothing else on
      a 101-operation socket is information-bearing.
    - ``from_run_task`` - it arrived on ``consumer.run_task``, which is the branch
      condition itself.
    - ``frames == []`` plus the ``4403`` close - the limit message never reached the
      wire, and the client's answer is the same non-disclosing close every other
      revocation produces. Upstream would have sent ``"Subscription limit reached"``.
    - ``run_task`` finished normally rather than cancelled. Aborting the connection's
      own task here would abort the disconnect/shutdown path that has to cancel and
      await the remaining operations, and would surface ``CancelledError`` out of the
      ASGI application. With 100 operations still registered, that is not a
      theoretical difference.

    Deliberately NOT lowered: the limit is upstream's, so the cost of the row (a
    hundred admissions, ~1s) is the cost of testing the real path rather than a
    configured stand-in the router cannot even express.
    """
    _user, cookie, _key = await _make_user_and_session(f"limit_probe_{subprotocol[:9]}")
    gate = _record_outbound_gate(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    over_limit_id = str(_UPSTREAM_SUBSCRIPTION_LIMIT)
    router = _router()

    async with _open_ws(router, cookie=cookie, subprotocol=subprotocol) as communicator:
        for index in range(_UPSTREAM_SUBSCRIPTION_LIMIT):
            channel = f"limit-{index}"
            _controller(channel)
            await _send_operation(
                communicator,
                _controlled_subscription(channel),
                op_id=str(index),
            )
        await _wait_until(
            lambda: probe.reads == _UPSTREAM_SUBSCRIPTION_LIMIT,
            lambda: f"not every operation was admitted: {probe.reads}",
        )

        # From here the NEXT read fails: operation 101's admission is read 101 and
        # still valid, its ``error`` frame's outbound checkpoint is read 102 and is not.
        probe.invalidate_after = _UPSTREAM_SUBSCRIPTION_LIMIT + 1
        _controller("limit-over")
        await _send_operation(
            communicator,
            _controlled_subscription("limit-over"),
            op_id=over_limit_id,
        )
        closed, frames = await _drain_until_close(communicator)
        consumer = gate.consumers[0]

    assert frames == [], frames
    _assert_revoked_close(closed)
    assert gate.frame_types == ["error"], gate.frame_types
    assert gate.entries == [over_limit_id], gate.entries
    assert gate.from_run_task == [True], gate.from_run_task
    assert probe.reads == _UPSTREAM_SUBSCRIPTION_LIMIT + 2
    # The guard's direction: the message loop was left to unwind normally.
    assert consumer.run_task.done()
    assert not consumer.run_task.cancelled()


# ---------------------------------------------------------------------------
# Channels-present: how a revoked operation STOPS, and how its close SETTLES.
#
# The rows above all revoke an operation that was suspended on an ``await`` of
# its own - a released gate, a session read - so they can be satisfied by an
# implementation that only ever unwinds an operation at a suspension point it was
# already sitting on. The rows below remove both of those conveniences: an
# operation whose every later result is already available (nothing suspends, so
# nothing delivers), and a close the transport holds open or refuses outright
# (so "revoked" and "closed" are visibly different facts).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("subprotocol", [_TRANSPORT_WS, _LEGACY_WS])
@pytest.mark.django_db(transaction=True)
async def test_a_revoked_operation_stops_when_its_every_later_result_is_already_available(
    subprotocol,
    monkeypatch,
):
    """A revoked operation ends deterministically, without a suspension point.

    The hard case for stopping an admitted operation, on both protocols. The burst
    subscription has no ``await`` between its yields, so the whole
    produce-gate-suppress-produce cycle can run without handing control back to the
    event loop - and a stop protocol built on requesting cancellation never gets a
    reschedule to deliver the request on. Such an implementation drives every one of
    the ``_BURST_RESULTS`` results into the gate, holds the loop while it does, and
    lets the generator's ``finally`` run only when the sequence is exhausted.

    So the assertions are about WHEN it stopped, not merely that the wire stayed
    quiet:

    - ``emitted`` is exactly one value. The revocation is decided while the FIRST
      result is at the outbound checkpoint, and the result source is asked for
      nothing after that - the suppressed frame's own value is the last one the
      resolver ever produces.
    - the generator's ``finally`` ran, and the operation's own task finished, both
      before the socket's teardown has begun (the assertions are inside the open
      socket, and the sibling below is still running).
    - the sentinel task advanced, so the loop kept scheduling other work throughout.
    - the sibling operation - admitted while the session was valid, and holding a
      payload of its own - is left to upstream's disconnect path, which cancels and
      awaits it; its ``finally`` runs only after the socket is torn down.
    """
    _user, cookie, _key = await _make_user_and_session(f"burst_probe_{subprotocol[:9]}")
    controller = _controller("burst")
    sibling = _controller("burst-sibling")
    gate = _record_outbound_gate(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    router = _router()

    async with _open_ws(router, cookie=cookie, subprotocol=subprotocol) as communicator:
        await _send_operation(communicator, _controlled_subscription("burst-sibling"), op_id="1")
        await _reached(sibling.started, "the sibling operation was never admitted")
        assert probe.reads == 1

        # The burst's admission is read 2 and succeeds; its first outbound frame is
        # read 3 and does not.
        probe.invalidate_after = 2
        async with _loop_sentinel() as sentinel:
            await _send_operation(communicator, _burst_subscription("burst"), op_id="2")
            closed, frames = await _drain_until_close(communicator)
            await _wait_until(
                lambda: gate.tasks and gate.tasks[0].done(),
                lambda: f"the revoked operation never finished: {gate.tasks}",
            )

        assert frames == [], frames
        _assert_revoked_close(closed)
        # Only the burst's own suppressed frame reached the checkpoint, on the
        # burst operation's task rather than the connection's message loop.
        assert gate.entries == ["2"], gate.entries
        assert gate.from_run_task == [False], gate.from_run_task
        assert controller.emitted == ["burst-1"], len(controller.emitted)
        assert controller.finalized, "the burst generator was not closed at the revocation"
        assert sentinel.ticks > 0, "the event loop was monopolized by the revoked operation"
        # The sibling is still parked on its own gate: stopping the revoked
        # operation is not stopping the connection's other work.
        assert not sibling.finalized
        assert sibling.emitted == []

    # Upstream's own teardown finished the siblings, as it always did.
    assert sibling.finalized
    assert probe.reads == 3


@pytest.mark.parametrize("subprotocol", [_TRANSPORT_WS, _LEGACY_WS])
@pytest.mark.django_db(transaction=True)
async def test_a_client_cancelling_the_detecting_operation_cannot_abandon_the_close(
    subprotocol,
    monkeypatch,
):
    """The close belongs to the CONNECTION, not to whichever operation observed it.

    Both protocols let a client cancel one of its own operations - ``complete`` on
    graphql-transport-ws, ``stop`` on legacy graphql-ws - and both reach
    ``cleanup_operation``, which cancels that operation's task. So the operation
    that happens to detect a revocation can be taken away by the client at any
    moment, including while the transport still has the ``4403`` back-pressured with
    its bytes uncommitted. If the close ran on that operation's task, the promised
    non-disclosing close would simply never arrive, while the message loop kept
    serving control frames on a socket the package claims it terminated.

    The row drives exactly that: park the transport's close, cancel the detecting
    operation through the protocol's OWN cancel frame, then release the park.
    Afterwards the close has been committed EXACTLY once - one attempt reached the
    transport, one ``4403`` reached the wire - and the teardown completes. One
    attempt is the whole point in both directions: a later checkpoint must not
    inherit a false "already closed", and the ordinary path must never put two
    ``4403`` frames on the wire.
    """
    _user, cookie, _key = await _make_user_and_session(f"parked_close_{subprotocol[:9]}")
    controller = _controller("parked-close")
    close_probe = _instrument_consumer_close(monkeypatch)
    close_probe.park = asyncio.Event()
    gate = _record_outbound_gate(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    router = _router()

    async with _open_ws(router, cookie=cookie, subprotocol=subprotocol) as communicator:
        await _send_operation(communicator, _controlled_subscription("parked-close"), op_id="1")
        await _reached(controller.started, "the operation was never admitted")
        assert probe.reads == 1

        # Its first result reaches the gate on a read that fails, and the close it
        # starts parks with nothing written.
        probe.invalidate_after = 1
        controller.release(0)
        await _reached(close_probe.entered, "the revocation never reached the transport close")
        assert close_probe.calls == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)]
        detecting_task = gate.tasks[0]
        assert not detecting_task.done()

        # The client cancels the very operation that observed the revocation.
        await communicator.send_json_to(
            {"type": _PROTOCOL_CANCEL_FRAMES[subprotocol], "id": "1"},
        )
        await _wait_until(
            lambda: detecting_task.done(),
            lambda: f"the client's cancel frame never reached the operation: {detecting_task}",
        )
        # Gone, and gone while the transport still has the close open.
        assert len(close_probe.calls) == 1

        close_probe.park.set()
        closed, frames = await _drain_until_close(communicator)

    # No payload escaped, and the gated set is what this row measures: the park
    # holds the close open long enough for the client's cancellation to be
    # acknowledged, and on the legacy protocol that acknowledgement is upstream's
    # own ``complete`` - a delegated frame, whose fate on an already-revoked
    # connection belongs to the suppression rows below rather than to this one.
    assert [frame for frame in frames if frame["type"] in _GATED_FRAME_TYPES] == [], frames
    _assert_revoked_close(closed)
    # One attempt, one 4403: the cancellation neither abandoned the close nor
    # earned the connection a second one.
    assert close_probe.calls == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)]
    assert probe.reads == 2


@pytest.mark.django_db(transaction=True)
async def test_a_close_that_raised_is_retried_by_the_next_permitted_checkpoint(
    monkeypatch,
    caplog,
):
    """A failed close is not a completed close.

    Nothing upstream records that a close was sent, so the package has to - and a
    single flag standing for "revocation decided" AND "close committed" records a
    close that RAISED as one that succeeded. Every later checkpoint then reads
    "already closed" and sends nothing, so the promised ``4403`` never arrives even
    though the transport is still there and would accept it.

    Here the first attempt raises ``OSError`` - a disconnected transport, a server
    state assertion and an ``OSError`` being the realistic set - and the failure is
    reported through the package logger with its traceback rather than swallowed.
    Operation 3, the next permitted checkpoint, then starts exactly ONE new attempt,
    which succeeds and puts the documented close on the wire. Two attempts, one
    ``4403``, one log record.

    The information-bearing gate never depended on any of this: operation 2's own
    payload was suppressed before the close was ever attempted, which is why a
    failing close is a connection-contract defect rather than a disclosure.
    """
    user, cookie, session_key = await _make_user_and_session("close_retry_probe")
    close_probe = _instrument_consumer_close(monkeypatch)
    close_probe.failures = 1
    probe = _instrument_revalidation(monkeypatch)
    router = _router()

    with caplog.at_level(logging.ERROR, logger="django_strawberry_framework"):
        async with _open_ws(router, cookie=cookie) as communicator:
            first = await _ws_operation(communicator, "{ username }", op_id="1")
            assert first["type"] == "next", first

            await _flush_the_session(user, session_key)

            # Refused, and the close that should have followed it raised.
            await _send_operation(communicator, "{ username }", op_id="2")
            await _reached(close_probe.entered, "the revocation never reached the transport close")
            assert await communicator.receive_nothing(timeout=0.2)
            assert close_probe.calls == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)]

            # The next permitted checkpoint cannot inherit a false "already closed".
            await _send_operation(communicator, "{ username }", op_id="3")
            closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    assert close_probe.calls == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)] * 2
    records = _package_logger_records(caplog)
    assert [record.levelname for record in records] == ["ERROR"]
    assert all(record.exc_info is not None for record in records)
    # Both refusals were read-free: only operation 1's two checkpoints and
    # operation 2's failing revalidation paid a session read.
    assert probe.reads == 3


@pytest.mark.django_db(transaction=True)
async def test_the_revocation_close_retry_is_bounded_and_still_refuses_every_payload(
    monkeypatch,
    caplog,
):
    """The retry is bounded, because checkpoints are client-driven.

    The other half of the retry policy. Checkpoints happen when a client sends
    something, so an unbounded retry would hand a client one attempted close per
    frame it chooses to provoke; and the realistic failures are not transient, so a
    third attempt cannot succeed where two did not. This adapter refuses every
    close, and the connection spends exactly two attempts however many checkpoints
    arrive afterwards.

    What must NOT degrade with it is the property the close was never carrying:
    every information-bearing frame stays refused. The last operation's resolver
    never runs and the socket emits nothing, on a connection the package could not
    close - which is why the gate is the security boundary and the close is the
    connection contract.
    """
    user, cookie, session_key = await _make_user_and_session("close_bound_probe")
    close_probe = _instrument_consumer_close(monkeypatch)
    close_probe.failures = 99
    probe = _instrument_revalidation(monkeypatch)
    refused = _controller("close-bound-refused")
    router = _router()

    with caplog.at_level(logging.ERROR, logger="django_strawberry_framework"):
        async with _open_ws(router, cookie=cookie) as communicator:
            first = await _ws_operation(communicator, "{ username }", op_id="1")
            assert first["type"] == "next", first

            await _flush_the_session(user, session_key)

            for op_id in ("2", "3", "4"):
                close_probe.entered.clear()
                await _send_operation(communicator, "{ username }", op_id=op_id)
                assert await communicator.receive_nothing(timeout=0.2)

            # Still fail-closed, with no close of its own left to spend.
            await _send_operation(
                communicator,
                _controlled_subscription("close-bound-refused"),
                op_id="5",
            )
            assert await communicator.receive_nothing(timeout=0.2)
            assert not refused.started.is_set(), "a revoked connection admitted another operation"

    assert close_probe.calls == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)] * 2
    records = _package_logger_records(caplog)
    assert [record.levelname for record in records] == ["ERROR", "ERROR"]
    # One failing revalidation, and every refusal behind it read-free.
    assert probe.reads == 3


# ---------------------------------------------------------------------------
# Channels-present: the connection's FINAL teardown as the close attempt's last
# owner.
#
# The rows above all measure a live connection, where a cancelled waiter is a
# bystander and the shielded attempt rightly survives it. These measure the other
# end: ``disconnect`` runs once, nobody comes after it, and an ASGI server may
# cancel it (shutdown, application-close timeout) or upstream's own teardown may
# raise inside it. An attempt still running past that point would retain the
# adapter, the consumer, the scope and a stale actor on a transport that is gone,
# so teardown has to END the attempt rather than shield it and walk away.
#
# Upstream's teardown is the controlled input here, patched on upstream's own
# consumer class so the subject stays the generated consumer's real
# ``disconnect``. A communicator cannot deliver either input: nothing in
# ``channels.testing`` cancels the application task, and a raising teardown is a
# server-level fault rather than anything a client can send.
# ---------------------------------------------------------------------------


class _ParkedCloseWebSocket:
    """An adapter-shaped websocket whose ``close`` parks until it is released.

    The transport state the teardown rows need and no in-process queue produces:
    a ``4403`` handed to a socket that neither commits it nor refuses it. Released
    only by ``release``, so a row that never releases it is measuring what the
    package does with a close that can only be ended by cancellation.
    """

    def __init__(self):
        self.closes = []
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def close(self, code=None, reason=None):
        self.closes.append((code, reason))
        self.entered.set()
        await self.release.wait()


async def _revocation_with_a_parked_attempt(revocation):
    """Drive ``revocation`` to a real in-flight attempt parked at the transport.

    Through ``decide()`` and ``close()`` rather than by assigning the fields, so
    the attempt under test is the connection-owned task production created, with
    the attempt count and the ``CLOSING`` state it really carries. The starting
    caller is a task of its own because ``close()`` awaits the attempt it started -
    which is the mid-connection waiter every row here needs to keep distinct from
    the terminal owner.
    """
    websocket = _ParkedCloseWebSocket()
    revocation.decide()
    starter = asyncio.create_task(revocation.close(websocket))
    await _reached(websocket.entered, "the close attempt never reached the transport")
    assert revocation.state == consumers_module._REVOCATION_CLOSING
    return websocket, starter


async def _discard(task):
    """Await a task that is expected to end cancelled, leaving nothing behind."""
    with contextlib.suppress(asyncio.CancelledError):
        await task


def _consumer_with_a_controlled_teardown(monkeypatch, teardown):
    """Instantiate the generated consumer with ``teardown`` as upstream's ``disconnect``.

    Patched on upstream's own consumer class, which is where the generated
    ``disconnect``'s ``super()`` call resolves: the row then exercises the real
    package override - its ``try``/``finally`` and its settlement - against a
    teardown whose cancellation and failure it controls.
    """
    upstream_consumer = _graphql_ws_consumer()
    monkeypatch.setattr(upstream_consumer, "disconnect", teardown, raising=False)
    consumer_class = _mounted_ws_callback(_router()).consumer_class
    assert issubclass(consumer_class, upstream_consumer)
    return consumer_class(schema=SCHEMA, revalidation_window=0.0)


async def test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it():
    """A cancelled ``settle()`` cancels and awaits the attempt it owns.

    The helper-level statement of the teardown contract, made where the two
    ownership roles can be held side by side: a mid-connection caller is parked on
    the same attempt, and the terminal owner is cancelled while the transport still
    has the ``4403`` uncommitted. ``asyncio.shield`` protects the attempt from the
    cancellation but does not keep the cancelled caller awaiting it, so shielding
    alone would return the caller and leave the task running against a transport
    nobody is going to read again.

    Both halves are asserted, because either one alone is satisfiable by the wrong
    implementation: the ``CancelledError`` propagates (so the caller's cancellation
    is honoured rather than absorbed by a teardown hook), and the attempt is
    finished. A finished attempt cannot be ``CLOSING`` - that state claims one is in
    flight, and every later checkpoint would await a task that will never complete -
    so the connection ends ``ABANDONED``, still revoked and still permitting no
    further attempt.
    """
    revocation = consumers_module._ConnectionRevocation()
    websocket, starter = await _revocation_with_a_parked_attempt(revocation)
    attempt = revocation.attempt

    settling = asyncio.create_task(revocation.settle())
    await asyncio.sleep(0)
    assert not settling.done()

    settling.cancel()
    with pytest.raises(asyncio.CancelledError):
        await settling

    assert attempt.done() and attempt.cancelled()
    assert revocation.state == consumers_module._REVOCATION_ABANDONED
    assert revocation.revoked
    # One attempt reached the transport, and the terminal state buys no second one.
    assert websocket.closes == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)]
    await revocation.settle()
    assert websocket.closes == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)]
    assert revocation.state == consumers_module._REVOCATION_ABANDONED
    # The mid-connection caller was never the owner: it ends with the attempt.
    await _discard(starter)


async def test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection(monkeypatch):
    """``disconnect`` cancelled by the server ends the connection's own close task.

    The same contract through the consumer the router mounts, with the input an
    ASGI server really delivers: application tasks are cancelled at shutdown and at
    an application-close timeout, and that cancellation arrives at whatever the
    consumer's ``disconnect`` is awaiting - here, the settlement of a ``4403`` the
    transport has parked.

    Afterwards nothing retains this connection. The attempt is done, so the
    adapter, the consumer, the scope and the actor it captured are released, and no
    ``send`` can be issued after the ASGI application has returned. The subsequent
    ``settle()`` is the no-second-close half: a terminal state is not a fresh start,
    and the transport sees exactly the one ``4403`` it already saw.
    """
    teardown_reached = asyncio.Event()

    async def cancellable_teardown(_consumer, _code):
        teardown_reached.set()

    consumer = _consumer_with_a_controlled_teardown(monkeypatch, cancellable_teardown)
    websocket, starter = await _revocation_with_a_parked_attempt(consumer._revocation)
    attempt = consumer._revocation.attempt

    disconnecting = asyncio.create_task(consumer.disconnect(1000))
    await _reached(teardown_reached, "the generated disconnect never delegated to upstream")
    assert not disconnecting.done(), "the teardown returned without settling the parked close"

    disconnecting.cancel()
    with pytest.raises(asyncio.CancelledError):
        await disconnecting

    assert attempt.done() and attempt.cancelled()
    assert consumer._revocation.state == consumers_module._REVOCATION_ABANDONED
    assert websocket.closes == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)]
    await consumer._revocation.settle()
    assert websocket.closes == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)]
    await _discard(starter)


async def test_a_teardown_that_raises_still_settles_the_close_and_propagates(monkeypatch):
    """Upstream's teardown failing does not skip settlement.

    Settlement sequenced after an unguarded ``await super().disconnect(code)`` is
    skipped by exactly the events that produce an orphan, so it runs from a
    ``finally``. This row drives the raising half: upstream's teardown fails, and
    the connection still finishes the close attempt it owns before the failure
    leaves ``disconnect``.

    The ordering is what is being measured, not merely the outcome. While the
    transport holds the close parked the teardown cannot complete - a
    ``finally``-less implementation would have propagated immediately - and
    releasing the transport lets the attempt record its real outcome, ``CLOSED``,
    with the upstream failure then propagating unchanged rather than being
    swallowed by the settlement that ran under it.
    """
    teardown_reached = asyncio.Event()

    async def failing_teardown(_consumer, _code):
        teardown_reached.set()
        raise RuntimeError("upstream teardown failed")

    consumer = _consumer_with_a_controlled_teardown(monkeypatch, failing_teardown)
    websocket, starter = await _revocation_with_a_parked_attempt(consumer._revocation)
    attempt = consumer._revocation.attempt

    disconnecting = asyncio.create_task(consumer.disconnect(1000))
    await _reached(teardown_reached, "the generated disconnect never delegated to upstream")
    await _wait_until(
        lambda: consumer._revocation.attempt is attempt and websocket.entered.is_set(),
        lambda: "the settlement never reached the parked attempt",
        tries=5,
    )
    assert not disconnecting.done(), "the failure escaped before the close was settled"

    websocket.release.set()
    with pytest.raises(RuntimeError, match="upstream teardown failed"):
        await disconnecting

    assert attempt.done() and not attempt.cancelled()
    assert consumer._revocation.state == consumers_module._REVOCATION_CLOSED
    assert websocket.closes == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)]
    await starter


# ---------------------------------------------------------------------------
# Channels-present: what the package writes to a socket it has REFUSED.
#
# Every row above measures the frames the client can read up to the close. These
# measure the ordered TRANSPORT log instead, which is the only vantage point from
# which "the 4403 was the last thing written" is a statement at all - and the one
# the delegated frame path can be judged from, since a delegated frame never
# reaches the outbound checkpoint and so leaves no trace in ``_OutboundGateProbe``.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("subprotocol", [_TRANSPORT_WS, _LEGACY_WS])
@pytest.mark.django_db(transaction=True)
async def test_nothing_is_written_to_the_socket_after_the_revocation_close(
    subprotocol,
    monkeypatch,
):
    """The connection contract: the ``4403`` is the LAST thing the package writes.

    A revoked operation's result loop ends NORMALLY - the stop-aware result source
    returns rather than cancelling - so upstream carries straight on to its own
    end-of-operation frame: ``run_operation``'s ``complete`` on
    graphql-transport-ws, ``handle_async_results``' ``complete`` on legacy
    graphql-ws. That frame is not information-bearing, so it takes the adapter's
    delegated path, and without the revoked check on that path it is committed
    AFTER the close - a control frame arriving on a socket the package says it
    terminated.

    Under this harness that is one extra output message. On a real server it is a
    write past the protocol's open state, which raises inside upstream's own
    operation task - where ``run_operation``'s ``except Exception`` logs it as a
    worker-task failure and re-raises - so every revoked subscription would report
    an error. Neither consequence is visible to a row that stops draining at the
    close, which is why this one reads the ordered transport log.

    The tail is checked twice, and the second check is the load-bearing one: the
    teardown that follows the socket's disconnect cancels every registered
    operation, and on the legacy protocol a cancelled operation answers with a
    ``complete`` of its own. So "nothing after the close" has to survive the
    teardown, not merely the revocation.
    """
    user, cookie, session_key = await _make_user_and_session(f"after_close_{subprotocol[:9]}")
    controller = _controller("after-close")
    log = _record_the_transport(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    router = _router()
    _operation_frame, success_frame = _PROTOCOL_FRAMES[subprotocol]

    async with _open_ws(router, cookie=cookie, subprotocol=subprotocol) as communicator:
        await _send_operation(communicator, _controlled_subscription("after-close"), op_id="1")
        await _reached(controller.started, "the operation was never admitted")

        controller.release(0)
        first = await communicator.receive_json_from(timeout=10)
        assert first["type"] == success_frame, first

        await _flush_the_session(user, session_key)

        controller.release(1)
        closed, frames = await _drain_until_close(communicator)
        _assert_revoked_close(closed)
        assert frames == [], frames
        assert log.after_the_revocation_close() == [], log.messages

    # The teardown wrote nothing either, and the payload really was produced and
    # suppressed rather than never generated.
    assert log.after_the_revocation_close() == [], log.messages
    assert controller.emitted == ["after-close-1", "after-close-2"]
    assert controller.finalized
    assert probe.reads == 3


@pytest.mark.parametrize("subprotocol", [_TRANSPORT_WS, _LEGACY_WS])
@pytest.mark.django_db(transaction=True)
async def test_a_delegated_control_frame_is_suppressed_once_the_revocation_is_decided(
    subprotocol,
    monkeypatch,
):
    """The cut-off is the DECISION, not the committed close - and it is not a mute.

    The window that distinguishes the two rulings, held open on purpose: the
    transport's close is parked, so the connection is decided-revoked with a close
    in flight and NOTHING yet committed. The socket is still physically open and
    upstream's message loop is still serving frames on it, because the parked close
    is awaited by the operation that observed the revocation rather than by the
    loop. A delegated frame written in that window is a frame written to a
    connection the package has already refused, so it is refused too. Keying the
    cut-off on the committed close instead would let every frame in this window
    out, and would let them out forever on a connection whose close attempts all
    failed.

    Both halves are the SAME provoked frame on the SAME socket, which is what makes
    this a gate rather than a mute: before the revocation the client asks for it and
    upstream's reply is committed; after the revocation the client asks again and
    nothing reaches the transport at all. The frame is per protocol only because the
    protocols differ in what a client can provoke (see
    ``_PROTOCOL_PROVOKED_CONTROL``); the path it takes through the adapter is the
    same delegated one on both.

    Reading the transport log rather than the communicator is what pins "suppressed
    rather than merely late": ``receive_nothing`` would be satisfied by a frame
    still queued behind the parked close.
    """
    _user, cookie, _key = await _make_user_and_session(f"delegated_{subprotocol[:9]}")
    warm = _controller("delegated-warm")
    controller = _controller("delegated-refused")
    log = _record_the_transport(monkeypatch)
    close_probe = _instrument_consumer_close(monkeypatch)
    close_probe.park = asyncio.Event()
    probe = _instrument_revalidation(monkeypatch)
    provoke_type, reply_type = _PROTOCOL_PROVOKED_CONTROL[subprotocol]
    router = _router()
    _operation_frame, success_frame = _PROTOCOL_FRAMES[subprotocol]

    async with _open_ws(router, cookie=cookie, subprotocol=subprotocol) as communicator:
        # A live operation, so the legacy protocol has something to cancel, and one
        # delivered result, so its task is parked between two values.
        await _send_operation(
            communicator,
            _controlled_subscription("delegated-warm"),
            op_id="warm",
        )
        await _reached(warm.started, "the warm-up operation was never admitted")
        warm.release(0)
        assert (await communicator.receive_json_from(timeout=10))["type"] == success_frame

        # Before any revocation: the client provokes the delegated frame and it is
        # committed, upstream's own reply, untouched.
        await communicator.send_json_to({"type": provoke_type, "id": "warm"})
        reply = await communicator.receive_json_from(timeout=10)
        assert reply["type"] == reply_type, reply
        permitted = log.frame_types
        assert permitted[-1] == reply_type, permitted

        # The next operation's first frame is refused, and the close it starts parks
        # with nothing written: decided, not closed. Reads so far are the warm-up
        # operation's two checkpoints - the provoked frame paid nothing - so read 3
        # is the new operation's admission and read 4 is its refused result.
        probe.invalidate_after = 3
        await _send_operation(
            communicator,
            _controlled_subscription("delegated-refused"),
            op_id="1",
        )
        await _reached(controller.started, "the second operation was never admitted")
        controller.release(0)
        await _reached(close_probe.entered, "the revocation never reached the transport close")
        assert close_probe.calls == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)]

        # The same provoked frame, on the same still-open socket: nothing at all is
        # committed for it.
        await communicator.send_json_to({"type": provoke_type, "id": "1"})
        assert await communicator.receive_nothing(timeout=0.2)
        assert log.frame_types == permitted, log.frame_types

        close_probe.park.set()
        closed, frames = await _drain_until_close(communicator)

    _assert_revoked_close(closed)
    assert [frame for frame in frames if frame["type"] in _GATED_FRAME_TYPES] == [], frames
    assert log.after_the_revocation_close() == [], log.messages
    # One attempt, one 4403, and the refused operation's own payload never went out.
    assert close_probe.calls == [(_REVOKED_CLOSE_CODE, _REVOKED_CLOSE_REASON)]
    assert controller.emitted == ["delegated-refused-1"]
    assert probe.reads == 4


def _upstream_handler_sources():
    """The source text of upstream's two WebSocket protocol handler modules.

    Read off disk rather than described here, so the transparency row below judges
    the INSTALLED upstream rather than a remembered one.
    """
    from strawberry.subscriptions.protocols.graphql_transport_ws import (
        handlers as transport_ws_handlers,
    )
    from strawberry.subscriptions.protocols.graphql_ws import handlers as legacy_ws_handlers

    return [
        Path(inspect.getfile(module)).read_text()
        for module in (transport_ws_handlers, legacy_ws_handlers)
    ]


def test_the_stop_aware_schema_passes_every_upstream_schema_read_through():
    """The substituted schema is transparent, measured against upstream's own source.

    The stop protocol works by replacing the handler's own ``self.schema`` with a
    per-connection wrapper, and a wrapper is only safe while everything upstream
    asks of that object still resolves to the real one. So the name set is DERIVED
    from the installed handler modules rather than asserted from memory: every
    ``self.schema.<name>`` either is the wrapper's own ``subscribe`` - the one call
    whose result has to become stoppable - or resolves through ``__getattr__`` to
    the identical attribute of the real schema.

    The second half is the ``isinstance`` question, which ``__getattr__`` cannot
    answer for: a handler that type-tested the schema it was handed would reject the
    wrapper outright, so the row proves upstream performs no such test. Both halves
    are what make the wrapper transparent rather than merely convenient, and both
    would go stale silently without a row that re-reads the source.

    Only the HANDLERS' schema is substituted, never the view's, so
    ``AsyncBaseHTTPView.run`` is not part of the question: it reads the consumer's
    own attribute, passes it to the handler as an ordinary keyword, and never sees
    the wrapper.
    """
    sources = _upstream_handler_sources()
    reads = set()
    for source in sources:
        reads.update(re.findall(r"self\.schema\.(\w+)", source))
        assert not re.search(r"(isinstance|type)\(\s*(self\.)?schema\b", source), (
            "upstream now type-tests the schema it was handed, which a delegating "
            "wrapper cannot satisfy"
        )

    assert reads == {"subscribe", "execute"}, reads
    wrapper = consumers_module._StopAwareSchema(SCHEMA, None)
    for name in reads - {"subscribe"}:
        assert getattr(wrapper, name) == getattr(SCHEMA, name), name
    assert wrapper.subscribe != SCHEMA.subscribe


# ---------------------------------------------------------------------------
# Channels-present: the package's OWN logout on the socket it is sent over.
#
# Every row above revokes from somewhere else - a second HTTP request, a direct
# store mutation, an invalidating read - which leaves the socket's scope actor
# authenticated and sends the revalidation down its database-read branch. The
# rows below revoke through ``auth/mutations.py``'s ``logout`` on the connection
# ITSELF, which additionally replaces ``scope["user"]`` with ``AnonymousUser``
# and can complete while a revalidation read is suspended. Those are the two
# states no external-revocation row can reach.
#
# The schema is per-test rather than module-level, and that is load-bearing
# twice: ``logout_mutation()`` is declared through the package registry (a
# process-wide ledger the fixture below clears on both sides, the discipline
# ``tests/auth/test_mutations.py``'s autouse fixture follows), and importing the
# opt-in auth subsystem at collection time would leave it in ``sys.modules``
# where ``::test_revalidation_resolves_its_session_store_outside_the_opt_in_auth_package``
# reads it. Every auth import below is therefore function-local.
# ---------------------------------------------------------------------------

_LOGOUT_MUTATION = "mutation{ logout{ ok } }"


def _build_logout_schema():
    """Build a schema carrying the package's own ``logout`` beside the controlled operations.

    The logout-only auth surface: no ``DjangoType`` is declared, which the
    package's structural logout exemption allows (``logout`` resolves no user
    type), so this adds one mutation field to the module's own ORM-free schema
    and nothing else. ``Subscription`` comes along because the rows that matter
    are about an operation admitted BEFORE the logout and still running after it.
    """
    from django_strawberry_framework import DjangoSchema, finalize_django_types
    from django_strawberry_framework.auth import logout_mutation

    @strawberry.type
    class Mutation:
        logout = logout_mutation()

    finalize_django_types()
    return DjangoSchema(query=Query, mutation=Mutation, subscription=Subscription)


@pytest.fixture
def _logout_schema():
    """Yield the logout-carrying schema, clearing the package registry either side."""
    from django_strawberry_framework.registry import registry

    registry.clear()
    try:
        yield _build_logout_schema()
    finally:
        registry.clear()


async def _logout_on_this_socket(schema, consumer):
    """Run the package's ``logout`` mutation against ONE open socket's own scope.

    The real resolver over the real connection: ``request_from_info`` resolves a
    Channels context whose ``request`` is the WebSocket consumer, and that
    consumer's ``scope`` is the very dict the revalidation checkpoints read, so
    this is the package's own mutation mutating the socket under test.

    Executed through the schema rather than pushed in as a protocol frame because
    the legacy ``graphql-ws`` protocol cannot execute a mutation at all (its
    handler reaches Strawberry through ``Schema.subscribe``; see
    ``Subscription.tick``), and the same-socket contract has to hold on both
    protocols. The frame-driven end-to-end shape is pinned separately, on the
    protocol that can carry it.
    """
    result = await schema.execute(_LOGOUT_MUTATION, context_value={"request": consumer})
    assert result.errors is None, result.errors
    assert result.data == {"logout": {"ok": True}}, result.data


@pytest.mark.parametrize("subprotocol", [_TRANSPORT_WS, _LEGACY_WS])
@pytest.mark.django_db(transaction=True)
async def test_a_same_socket_logout_stops_a_running_subscription_on_both_protocols(
    subprotocol,
    monkeypatch,
    _logout_schema,
):
    """The package's own logout revokes the connection it was sent over.

    The composition every external-revocation row misses: authenticate, admit a
    multi-yield subscription, receive result 1, run the package's ``logout`` on
    THIS socket, then release result 2. The logout flushes the durable session and
    writes ``AnonymousUser`` onto the scope, so the connection's actor identity
    changed rather than its session merely expiring - and the already-admitted
    subscription must not keep emitting into it.

    ``probe.reads`` is the sharpest assertion here. It stays at the two the
    subscription's own checkpoints paid: the refusal is read-free, because it is
    the connection's authenticated PROVENANCE - not a fresh session read - that
    denies an actor which is anonymous now but was not always. An implementation
    that read the live scope actor would find an anonymous socket, take the
    read-free carve-out, and send result 2.
    """
    _user, cookie, _session_key = await _make_user_and_session(f"same_socket_{subprotocol[:9]}")
    controller = _controller("same-socket")
    gate = _record_outbound_gate(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    router = _router(_logout_schema)
    _operation_frame, success_frame = _PROTOCOL_FRAMES[subprotocol]

    async with _open_ws(router, cookie=cookie, subprotocol=subprotocol) as communicator:
        await _send_operation(communicator, _controlled_subscription("same-socket"), op_id="1")
        await _reached(controller.started, "the operation was never admitted")

        controller.release(0)
        first = await communicator.receive_json_from(timeout=10)
        assert first["type"] == success_frame, first
        assert first["payload"]["data"] == {"controlled": "same-socket-1"}
        assert probe.reads == 2

        consumer = gate.consumers[0]
        await _logout_on_this_socket(_logout_schema, consumer)
        # The logout really did change the connection's actor identity.
        assert consumer.scope["user"].is_anonymous

        controller.release(1)
        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    assert controller.emitted == ["same-socket-1", "same-socket-2"]
    assert probe.reads == 2
    assert controller.finalized, "the subscription generator was never unwound"


@pytest.mark.django_db(transaction=True)
async def test_the_logout_mutations_own_reply_is_suppressed_by_the_connection_close(
    monkeypatch,
    _logout_schema,
):
    """The pinned transition contract: the socket ends, so the reply does not arrive.

    The frame-driven end-to-end shape, on the one protocol that can execute a
    mutation. The logout is an ordinary operation: it is admitted against the
    still-valid actor, its resolver tears the session down durably, and its
    ``{ok: true}`` payload then reaches the outbound checkpoint - which is now
    the FIRST protected checkpoint after the transition, and refuses it like any
    other post-revocation frame. The client's answer is the same non-disclosing
    ``4403`` close every other revocation produces.

    That the reply is suppressed rather than exempted is the decision this row
    exists to pin: exempting one frame type from the gate is the disclosure
    distinction the gated set exists to avoid, and the teardown has already
    completed durably - which the deleted session row proves independently of the
    wire.
    """
    _user, cookie, session_key = await _make_user_and_session("logout_frame_probe")
    probe = _instrument_revalidation(monkeypatch)
    router = _router(_logout_schema)

    async with _open_ws(router, cookie=cookie) as communicator:
        first = await _ws_operation(communicator, "{ username }", op_id="1")
        assert first["type"] == "next", first
        assert first["payload"]["data"] == {"username": "logout_frame_probe"}

        await _send_operation(communicator, _LOGOUT_MUTATION, op_id="2")
        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    # Admission for both operations, plus the first operation's own result frame;
    # the refused reply took no read of its own.
    assert probe.reads == 3
    # The durable teardown happened even though its payload never went out.
    assert not await _session_row_still_exists(session_key)


@pytest.mark.django_db(transaction=True)
async def test_an_anonymous_socket_that_logs_out_keeps_the_read_free_carve_out(
    monkeypatch,
    _logout_schema,
):
    """Provenance, not the current actor: a socket that was never authenticated is untouched.

    The control that keeps the carve-out a carve-out. This socket carries no
    cookie, so it has no authenticated provenance to latch; running the package's
    ``logout`` on it flushes any residual session data, answers the honest
    ``{ok: false}``, and changes nothing about the connection. The poisoned store
    resolver makes "zero session reads" a positive proof rather than an
    observation - a read would raise, fail closed, and close the socket - and the
    socket then runs another operation to show it is still fully usable.
    """
    _poison_the_session_store(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    router = _router(_logout_schema)

    async with _open_ws(router) as communicator:
        logged_out = await _ws_operation(communicator, _LOGOUT_MUTATION, op_id="1")
        assert logged_out["type"] == "next", logged_out
        assert logged_out["payload"]["data"] == {"logout": {"ok": False}}

        after = await _ws_operation(communicator, "{ actor }", op_id="2")
        assert after["type"] == "next", after
        assert after["payload"]["data"] == {"actor": "ChannelsRequestAdapter|True"}
        assert await communicator.receive_nothing(timeout=0.2)

    assert probe.reads == 0


@pytest.mark.django_db(transaction=True)
async def test_a_same_socket_logout_cannot_complete_across_a_parked_protected_send(
    monkeypatch,
    _logout_schema,
):
    """The send ordering: an authorized frame and a logout are serialized, not raced.

    The one interleaving no after-the-fact check can repair, and therefore the one
    that has to be excluded rather than detected. An ASGI send is asynchronous, so
    a checkpoint can have validated the actor, entered ``send``, and suspended with
    the bytes not yet committed. If the logout ran under a lock of its own it would
    flush the durable session, replace the scope actor and return THROUGH that
    suspension, and the already-authorized frame would then land on a socket whose
    identity no longer exists. Comparing a generation after ``send`` returns is too
    late; the frame has gone out.

    So the row parks the checkpoint's own send delegate - authorization granted,
    nothing written - and asserts the exclusion from the auth side: the logout
    reaches the scope session lock, and stops. Its durable teardown has NOT run
    (the session row is still there) and the scope actor is untouched, which is
    what distinguishes "the logout is waiting" from "the logout is slow".

    Releasing the park then shows the linearization in the other direction: the
    pre-transition frame - which was legitimately authorized, and is not
    suppressed - goes out first, the logout completes behind it, and only then does
    the connection carry an anonymous actor. Every LATER protected frame is refused
    and the socket takes the documented close, at no session read: the refusal is
    the connection's authenticated provenance, not a fresh lookup.
    """
    from django_strawberry_framework.auth.sessions import _SCOPE_LOCK_KEY

    _user, cookie, session_key = await _make_user_and_session("parked_send_probe")
    controller = _controller("parked-send")
    gate = _record_outbound_gate(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    router = _router(_logout_schema)

    async with _open_ws(router, cookie=cookie) as communicator:
        await _send_operation(communicator, _controlled_subscription("parked-send"), op_id="1")
        await _reached(controller.started, "the operation was never admitted")
        assert probe.reads == 1

        # Result 1 is validated and then parked with its bytes uncommitted.
        gate.hold_before_send = asyncio.Event()
        controller.release(0)
        await _reached(gate.reached_send, "the checkpoint never reached its send delegate")
        assert probe.reads == 2
        consumer = gate.consumers[0]
        assert _actor_lease_held(consumer)

        # The logout takes the scope session lock and can get no further: the lease
        # it needs next is the one the parked send is holding.
        logout_task = asyncio.create_task(_logout_on_this_socket(_logout_schema, consumer))
        await _wait_until(
            lambda: (
                consumer.scope.get(_SCOPE_LOCK_KEY) is not None
                and consumer.scope[_SCOPE_LOCK_KEY].locked()
            ),
            lambda: "the logout never reached the scope session lock",
        )
        assert consumer.scope["user"].is_authenticated
        # A real round trip through the executor thread, so the logout has had
        # every chance to finish if nothing were holding it back.
        assert await _session_row_still_exists(session_key)
        assert not logout_task.done()

        # Released, the authorized frame goes out and the logout linearizes behind it.
        gate.hold_before_send.set()
        first = await communicator.receive_json_from(timeout=10)
        assert first["payload"]["data"] == {"controlled": "parked-send-1"}
        await logout_task
        assert not await _session_row_still_exists(session_key)
        assert consumer.scope["user"].is_anonymous

        controller.release(1)
        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    assert gate.sends_under_lease == [True]
    assert controller.emitted == ["parked-send-1", "parked-send-2"]
    assert controller.finalized
    # The post-transition refusal is provenance, so it cost no read of its own.
    assert probe.reads == 2


@pytest.mark.django_db(transaction=True)
async def test_a_transition_in_flight_denies_both_checkpoints_inside_a_positive_window(
    monkeypatch,
    _logout_schema,
):
    """The other ordering: a positive window's cache hit is not a bypass.

    The reverse of the parked-send row, and the reason a fresh window timestamp
    cannot be a shortcut around the exclusion. Reusing a timestamp IS an
    authorization decision, so it has to happen under the same lease an uncached
    validation holds; a cache hit evaluated outside it would authorize against a
    connection whose actor was already being replaced, and would do so *silently* -
    the read counter, which every other row in this group leans on, does not move
    for a cache hit at all.

    The logout is parked inside its own transition and BEFORE Channels replaces the
    scope actor, which is the worst moment for both checkpoints: the durable
    session is going away, the scope still says "authenticated", and the window
    timestamp is fresh. The row asserts all three of those preconditions, so it
    cannot degrade into a row where the window had simply expired.

    Both checkpoints are then driven at once - a NEW operation reaches admission,
    and the running subscription's next result reaches the outbound gate - and
    neither may proceed. "Neither proceeded" is asserted positively rather than as
    wire silence: the new operation's resolver never started (so admission did not
    delegate to upstream), and the read count is unchanged (so nothing revalidated
    either). When the transition finally releases the lease both refuse on
    provenance, still read-free, and the connection takes the documented close.
    """
    import channels.auth

    _user, cookie, session_key = await _make_user_and_session("transition_window_probe")
    running = _controller("transition-running")
    blocked = _controller("transition-blocked")
    gate = _record_outbound_gate(monkeypatch)
    probe = _instrument_revalidation(monkeypatch)
    router = _router(_logout_schema, websocket_revalidation_window=3600.0)
    native_logout = channels.auth.logout
    inside_transition = asyncio.Event()
    release_transition = asyncio.Event()

    async def parked_logout(scope):
        """Park inside ``actor_transition``, before the scope actor is replaced."""
        inside_transition.set()
        await release_transition.wait()
        await native_logout(scope)

    monkeypatch.setattr(channels.auth, "logout", parked_logout)

    async with _open_ws(router, cookie=cookie) as communicator:
        await _send_operation(
            communicator,
            _controlled_subscription("transition-running"),
            op_id="1",
        )
        await _reached(running.started, "the running operation was never admitted")
        assert probe.reads == 1

        # Result 1 rides the admission's read from the window cache.
        running.release(0)
        first = await communicator.receive_json_from(timeout=10)
        assert first["payload"]["data"] == {"controlled": "transition-running-1"}
        assert probe.reads == 1

        consumer = gate.consumers[0]
        logout_task = asyncio.create_task(_logout_on_this_socket(_logout_schema, consumer))
        await _reached(inside_transition, "the logout never opened its actor transition")

        # The three preconditions that make a cache hit genuinely available here.
        assert _actor_lease_held(consumer)
        assert consumer.scope["user"].is_authenticated
        window_age = time.monotonic() - consumer.scope[consumers_module._REVALIDATED_AT_SCOPE_KEY]
        assert 0.0 <= window_age < 3600.0, window_age

        # Admission and the outbound gate, both driven into the open transition.
        await _send_operation(
            communicator,
            _controlled_subscription("transition-blocked"),
            op_id="2",
        )
        running.release(1)
        assert await communicator.receive_nothing(timeout=0.2)
        assert not blocked.started.is_set(), "admission authorized an operation from the cache"
        assert probe.reads == 1

        release_transition.set()
        await logout_task
        assert not await _session_row_still_exists(session_key)

        closed, frames = await _drain_until_close(communicator)

    assert frames == [], frames
    _assert_revoked_close(closed)
    # Neither checkpoint authorized anything, and neither paid a read to refuse.
    assert not blocked.started.is_set()
    assert probe.reads == 1
    assert running.emitted == ["transition-running-1", "transition-running-2"]
    assert running.finalized
