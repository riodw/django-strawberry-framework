"""Channels router tests: the protocol split, WebSocket wrappers and consumer seam, lazy imports.

Both dependency states are exercised (spec-041 Decision 8, as amended by
spec-065 Decision 2):

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

Transport ownership after spec-065: the router no longer serves GraphQL over
HTTP, so ``HttpCommunicator`` here proves *delegation* - every HTTP path reaches
the supplied Django ASGI application untouched. The request contract, the
schema pass-through with extensions intact, and the authenticated-session round
trip are all proven over the **WebSocket** branch, which is where the package's
own Channels composition (and therefore ``AuthMiddlewareStack``) still lives.
The live HTTP boundary itself is earned over fakeshop's real ``/graphql/`` in
``examples/fakeshop/test_query/test_transport_api.py``.

The WebSocket consumer-injection seam and the per-operation actor revalidation
matrix (spec-065 Decision 11, Test plan rows 25-30) also live here: the
composition rows are structural, and the revalidation rows drive real sockets
through ``WebsocketCommunicator`` on BOTH subprotocols. Decision 13
#"Placement" pins them at this tier - fakeshop has no ``asgi.py``, so the router
half keeps the documented genuinely-unreachable-live exemption.

The execution schema is module-local and ORM-free: the async consumers execute
on the event loop, where sync ORM would raise ``SynchronousOnlyOperation`` -
router behavior is schema-agnostic, so deterministic scalar fields (plus one
one-shot subscription, the only operation type the legacy ``graphql-ws``
protocol can execute) are sufficient (spec-041 Test plan). Every out-of-band
session / user mutation the revalidation rows need therefore rides
``database_sync_to_async``, as Test 18's session mint already did.
"""

import contextlib
import importlib
import inspect
import json
import logging
import sys
import time
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import strawberry
from channels.auth import AuthMiddleware
from channels.db import database_sync_to_async
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from channels.sessions import CookieMiddleware, SessionMiddleware
from channels.testing import HttpCommunicator, WebsocketCommunicator

import django_strawberry_framework
import django_strawberry_framework.consumers as consumers_module
import django_strawberry_framework.routers as routers_module
from django_strawberry_framework.auth import sessions as auth_sessions
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.permissions import request_from_info
from tests._soft_dependency import evicted_modules, simulated_absence

# The hint floors are deliberately RE-TYPED literals, matching
# ``tests/rest_framework/test_soft_dependency.py``'s ``_HINT_SUBSTRING``
# discipline: importing the router constants and asserting them against
# themselves could never catch the hint drifting from the dev-group floor.
_HINT_SUBSTRING = "channels>=4.3.2"
_STRAWBERRY_FLOOR_SUBSTRING = "strawberry-graphql>=0.262.0"

# Same discipline for the revalidation rejection and the two new construction
# hints: a RE-TYPED fragment, never the imported constant, so a message drift
# fails a test instead of asserting itself.
_REVOKED_SUBSTRING = "no longer valid"
_UNUSABLE_CONSUMER_SUBSTRING = "GraphQLWSConsumer"
_WINDOW_WITH_CLASS_SUBSTRING = "injected consumer class owns its own revalidation policy"

# The two subprotocols the package's mount negotiates, and the per-protocol
# frame names one operation round trip uses: (client operation frame, server
# success frame). The rejection frame is ``"error"`` on both - only its payload
# shape differs, which is what the two rejection rows measure.
_TRANSPORT_WS = "graphql-transport-ws"
_LEGACY_WS = "graphql-ws"
_PROTOCOL_FRAMES = {_TRANSPORT_WS: ("subscribe", "next"), _LEGACY_WS: ("start", "data")}


# ---------------------------------------------------------------------------
# Module-local execution schema (ORM-free; see module docstring)
# ---------------------------------------------------------------------------


@strawberry.type
class Query:
    @strawberry.field
    def ping(self) -> str:
        return "pong"

    @strawberry.field
    def username(self, info: strawberry.Info) -> str:
        """The authenticated-session probe (Test 18): the session actor's username."""
        request = request_from_info(info, family_label="FilterSet")
        return request.user.username

    @strawberry.field
    def actor(self, info: strawberry.Info) -> str:
        """Read the scope-backed actor without requiring HTTP-only attributes."""
        request = request_from_info(info, family_label="FilterSet")
        return f"{type(request).__name__}|{request.user.is_anonymous}"

    @strawberry.field
    def actor_identity(self, info: strawberry.Info) -> str:
        """The revalidation-freshness probe (spec-065 row 26): two identity reads.

        A field of its own rather than an extension of ``actor`` (whose exact
        string Test 16 asserts). Both values are attribute reads off whatever
        object ``scope["user"]`` currently holds, so a stale connect-time actor
        and a revalidation-refreshed one are distinguishable without any ORM
        work in the resolver.
        """
        request = request_from_info(info, family_label="FilterSet")
        return f"{request.user.username}|{request.user.is_staff}"


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


SCHEMA = strawberry.Schema(query=Query, subscription=Subscription)
_TICK_SUBSCRIPTION = "subscription { tick }"


def _router_class():
    from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

    return DjangoGraphQLProtocolRouter


# ---------------------------------------------------------------------------
# Construction seam: ``django_application`` is REQUIRED (spec-065 Decision 3),
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


def unwrap_origin_validator(ws_app):
    """Assert the outermost WS layer is the ``OriginValidator`` instance; return its child.

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
    """
    headers = [(b"origin", b"http://testserver")]
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


def _assert_rejected(message, op_id, *, errors_as_list):
    """Assert one revalidation rejection frame, including its per-protocol shape.

    ``graphql-transport-ws`` carries a LIST of formatted errors and legacy
    ``graphql-ws`` a single formatted error - the one irreducible difference
    between the two pre-hook call sites, so the shape itself is asserted rather
    than just the message.
    """
    assert message["type"] == "error", message
    assert message["id"] == op_id, message
    payload = message["payload"]
    if errors_as_list:
        assert isinstance(payload, list), payload
        assert len(payload) == 1, payload
        payload = payload[0]
    else:
        assert isinstance(payload, dict), payload
    assert _REVOKED_SUBSTRING in payload["message"], payload


# ---------------------------------------------------------------------------
# Session / actor fixtures-as-functions for the revalidation rows. Every ORM
# touch rides ``database_sync_to_async`` (the resolver side runs on the event
# loop, where sync ORM raises ``SynchronousOnlyOperation``), and every row that
# needs the executor thread to SEE these writes carries
# ``django_db(transaction=True)`` - Test 18's shape.
# ---------------------------------------------------------------------------


@database_sync_to_async
def _make_user_and_session(username, password="pw-9x-strong"):
    """Create a user plus a real logged-in session row; return (user, cookie, key).

    Lifted verbatim out of Test 18's local ``make_user_and_session_cookie`` when
    the revalidation rows needed a fifth copy of it: same three session keys,
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
    the revalidation DOES run (spec-065 row 30), and it proves the two early
    returns skipped the session read entirely when they do NOT - a swallowed
    exception would surface as a denied operation, so "the operation succeeded"
    is only possible if the read never happened.
    """

    def _raise():
        raise RuntimeError("poisoned session store")

    monkeypatch.setattr(auth_sessions, "session_store_class", _raise)


def _package_logger_records(caplog):
    return [record for record in caplog.records if record.name == "django_strawberry_framework"]


# ---------------------------------------------------------------------------
# Channels-present: construction and composition (Tests 1-6)
# ---------------------------------------------------------------------------


def test_router_is_a_protocol_type_router_mapping_exactly_http_and_websocket():
    """Test 1: a true ``ProtocolTypeRouter`` whose mapping carries exactly the two protocols.

    Framed as a current-shape parity assertion (upstream maps exactly these
    two); the behavior tests below are what the mapping must actually deliver.
    """
    router = _router()
    assert isinstance(router, ProtocolTypeRouter)
    assert set(router.application_mapping) == {"http", "websocket"}


def test_http_branch_is_the_supplied_django_application_by_identity():
    """Test 2 (spec-065 row 8): ``"http"`` IS the supplied object, with no wrapper.

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
    """Test 3 (spec-065 row 10): omission is ``TypeError``; unusable is ``ConfigurationError``.

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
    """Test 3b (spec-065 row 9): ``GraphQLHTTPConsumer`` is nowhere in ``routers.py``.

    Read the module's own SOURCE, not ``dir(routers_module)``: an unimported name
    is absent from ``dir()`` whether or not the module still references it, so
    only the source text proves the import left in the same change as the
    composition (Decision 2).
    """
    source = Path(routers_module.__file__).read_text(encoding="utf-8")
    assert "GraphQLHTTPConsumer" not in source


def test_websocket_branch_wraps_origin_validator_outside_the_auth_stack():
    """Test 4: ``AllowedHostsOriginValidator`` OUTSIDE ``AuthMiddlewareStack`` on WS only."""
    router = _router()
    inner = unwrap_origin_validator(router.application_mapping["websocket"])
    ws_router = unwrap_auth_stack(inner)
    assert _route_patterns(ws_router) == [r"^graphql/?$"]
    # The HTTP branch carries no origin validator - it is the bare Django
    # application, which is not an ``OriginValidator``.
    assert not isinstance(router.application_mapping["http"], OriginValidator)


def test_custom_websocket_url_pattern_reaches_only_the_websocket_re_path():
    """Test 5 (spec-065 row 11, structural half): the pattern is WebSocket-only now.

    ``websocket_url_pattern=`` governs one branch; the HTTP value stays the
    identical supplied object, because HTTP path matching belongs entirely to
    the consumer's Django URLconf (Decision 4).
    """
    django_application = _RecordingDjangoApplication()
    router = _router(
        django_application=django_application,
        websocket_url_pattern="^api/graphql",
    )
    ws_router = unwrap_auth_stack(
        unwrap_origin_validator(router.application_mapping["websocket"]),
    )
    assert _route_patterns(ws_router) == ["^api/graphql"]
    assert router.application_mapping["http"] is django_application


def test_the_websocket_pattern_is_keyword_only_with_no_legacy_url_pattern_alias():
    """Test 5b (spec-065 Decision 4): both NEGATIVE halves of the rename.

    Decision 4 renames rather than aliases - "a single parameter that no longer
    affects HTTP would be a name that lies" - and makes the replacement
    keyword-only. Neither contract has a Test-plan row of its own, and Slice 4
    reopens this exact signature to add two more keywords, so both are pinned
    here: a compatibility alias or a relaxed positional boundary has to fail
    loudly instead of arriving as a convenience edit.
    """
    with pytest.raises(TypeError, match="url_pattern"):
        _router(url_pattern="^graphql")

    with pytest.raises(TypeError, match="positional"):
        _router_class()(SCHEMA, _RecordingDjangoApplication(), "^graphql")


def test_repeated_access_returns_the_cached_class_which_is_subclassable():
    """Test 6: the builder memoizes into ``_ROUTER_CLASS``; the class is a real base."""
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
# construction-time validation (Tests 19-25; spec-065 Decision 11, rows 28-29).
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
    """The single WS route's callback, after asserting both wrappers are in place."""
    ws_router = unwrap_auth_stack(
        unwrap_origin_validator(router.application_mapping["websocket"]),
    )
    assert _route_patterns(ws_router) == [r"^graphql/?$"]
    return ws_router.routes[0].callback


def test_the_default_websocket_consumer_is_the_packages_revalidating_subclass():
    """Test 19 (spec-065 checklist boxes 2-3): the default mount is the package consumer.

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


def test_an_injected_consumer_class_still_sits_inside_both_wrappers():
    """Test 20 (spec-065 row 28): injection opts out of revalidation, not of the wrappers.

    ``AllowedHostsOriginValidator`` and ``AuthMiddlewareStack`` are applied by
    the ROUTER around whatever is injected, so the unwrap walk and the route
    pattern are identical to the default mount's - that structural guarantee is
    Decision 11's whole safety argument. The HTTP branch is unaffected.
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


def test_an_injected_consumer_factory_is_called_with_the_schema_and_mounted():
    """Test 21 (spec-065 Decision 11): the factory shape's calling convention.

    A non-class callable is a factory, invoked as ``factory(schema=schema)``, and
    whatever it returns is what gets mounted - by identity, so the router adds no
    ``as_asgi`` hop of its own.
    """
    received = {}

    async def injected_application(scope, receive, send):
        raise AssertionError("this row never drives the injected application")

    def factory(**kwargs):
        received.update(kwargs)
        return injected_application

    callback = _mounted_ws_callback(_router(websocket_consumer_class=factory))

    assert callback is injected_application
    assert list(received) == ["schema"]
    assert received["schema"] is SCHEMA


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
    """Test 22 (spec-065 Decision 11): neither accepted shape, so ConfigurationError.

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
    ],
)
def test_the_revalidation_window_rejects_unusable_values(unusable):
    """Test 23 (spec-065 Decision 11): the window's construction-time domain.

    ``bool`` is rejected explicitly (``isinstance(True, int)`` is ``True``), and
    both non-finite values are rejected rather than silently meaning "never
    revalidate" (``inf``) or "no window at all" (``nan``, which loses every
    comparison). The failure is ``ConfigurationError`` at construction, never a
    per-operation surprise.
    """
    with pytest.raises(ConfigurationError, match="websocket_revalidation_window"):
        _router(websocket_revalidation_window=unusable)


@pytest.mark.parametrize(
    ("accepted", "expected"),
    [
        pytest.param(0, 0.0, id="int-zero-is-coerced"),
        pytest.param(0.0, 0.0, id="explicit-default"),
        pytest.param(30, 30.0, id="int-seconds-are-coerced"),
        pytest.param(2.5, 2.5, id="fractional-seconds"),
    ],
)
def test_the_revalidation_window_accepts_and_coerces_numbers(accepted, expected):
    """Test 23b: the accepted half, including the int -> float coercion.

    The consumer receives a ``float`` whatever the caller passed, so the window
    comparison never mixes numeric types.
    """
    callback = _mounted_ws_callback(_router(websocket_revalidation_window=accepted))

    window = callback.consumer_initkwargs["revalidation_window"]
    assert window == expected
    assert isinstance(window, float)


def test_injecting_a_consumer_class_with_a_window_is_a_construction_error():
    """Test 24 (spec-065 row 29): a knob that does nothing is worse than an error.

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
    """Test 25: all three WebSocket keywords are KEYWORD_ONLY, with their defaults.

    The sibling of Test 5b, whose subject is the ``url_pattern`` rename: this one
    extends the keyword-only contract to the two parameters Slice 4 adds, so a
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
# Channels-present: execution through communicators (Tests 7-10)
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
    """Test 7 (spec-065 Decision 13): HTTP is delegation, for GraphQL paths too.

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
    """Test 9: the three origin directions (match / mismatch / missing) on the WS branch.

    pytest-django's environment appends ``"testserver"`` to ``ALLOWED_HOSTS``,
    so ``http://testserver`` is the matching origin; a handshake with NO
    ``Origin`` header is denied exactly like a mismatched one
    (``ALLOWED_HOSTS`` never contains ``"*"`` in this suite).
    """
    router = _router()
    communicator = WebsocketCommunicator(
        router,
        "/graphql",
        headers=headers,
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
    """Test 8 (spec-065 row 11, behavioral half): the default pattern is exact.

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
        headers=[(b"origin", b"http://testserver")],
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
    """Test 10 (spec-065 row 12): the consumer holds the exact schema; extensions execute.

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

    ws_router = unwrap_auth_stack(
        unwrap_origin_validator(router.application_mapping["websocket"]),
    )
    assert ws_router.routes[0].callback.consumer_initkwargs["schema"] is recording_schema

    data = await _ws_graphql_data(router, "{ ping }")
    assert data == {"ping": "pong"}
    assert fired == ["operation"]


# ---------------------------------------------------------------------------
# Channels-absent + degraded installs: the eviction-simulated states
# (Tests 11-15, 17). Absence is SIMULATED with the shared ``None`` sentinel +
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
    """Test 11: the root package never touches the guard; the SUBMODULE star opts in."""
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
    """Test 12: ``import django_strawberry_framework.routers`` itself pays no import."""
    mod = importlib.import_module("django_strawberry_framework.routers")
    assert mod.__name__ == "django_strawberry_framework.routers"


def test_symbol_access_raises_the_install_hint_without_channels(_simulate_channels_absent):
    """Test 13: the ``from ... import`` line raises ``ImportError`` naming the floor."""
    with pytest.raises(ImportError, match=_HINT_SUBSTRING) as exc_info:
        exec("from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter", {})
    assert isinstance(exc_info.value.__cause__, ImportError)


def test_restore_is_two_sided_and_the_present_path_works_again():
    """Test 14: after teardown the attribute path and import path hold ONE module object.

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
    """Test 15b (spec-065 Decision 11): ``consumers.py`` is channels-free at import.

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
    """Test 15: a non-router attribute miss raises ``AttributeError``, never the hint."""
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
    """Test 17: present-but-incompatible installs name WHICH half is broken.

    Same eviction + two-sided-restore discipline as the absent path (so the
    re-executed module has no cached ``_ROUTER_CLASS`` and the builder import
    actually fires, order-independence finding P1.2), but here the top-level
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
# Channels-present: the package request contract over WebSocket (Tests 16 and 18)
#
# The HTTP colour of the request-adapter contract is gone with the transport
# (spec-065 Decision 2 - "the Channels request adapter is now a WebSocket-only
# shape"). ``ChannelsRequestAdapter.__getattr__``'s delegated read and
# ``_channels_scope``'s ``consumer.scope`` HTTP duck shape stay covered at the
# package tier by ``tests/utils/test_permissions.py``.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
async def test_request_contract_resolves_over_the_websocket_branch():
    """Test 16: a framework-shaped resolver works under the Channels context.

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
    """Test 18: a real session cookie flows through ``AuthMiddlewareStack`` to the actor.

    Subject preserved from the ``0.0.14`` test, transport moved: the cookie used
    to traverse the HTTP branch's ``AuthMiddlewareStack``, which the protocol
    split removed, so it now rides the WebSocket handshake headers into the one
    stack the package still composes.

    The user + session rows are created async-safely (``database_sync_to_async``,
    since ``AuthMiddlewareStack`` resolves the user on the event loop's executor
    thread); the resolver then sees the AUTHENTICATED user, not ``AnonymousUser``
    - what actually earns the "session user on the scope" claim (finding P1.4).
    The mint itself now lives at module level (``_make_user_and_session``), where
    the Slice-4 revalidation rows share it; the assertions are unchanged.
    """
    _user, cookie, _session_key = await _make_user_and_session("channels_probe")
    router = _router()
    data = await _ws_graphql_data(router, "{ username }", cookie=cookie)
    assert data == {"username": "channels_probe"}


# ---------------------------------------------------------------------------
# Channels-present: per-operation actor revalidation (Tests 26-32; spec-065
# Decision 11, Test plan rows 25-27 and 30). Every row drives a REAL socket
# through the package's own mount, and every out-of-band mutation stands in for
# the spec's "separate request": the property under test is "denied without
# reconnecting", not "an HTTP round trip happened", and this module's execution
# schema is ORM-free on purpose (see the module docstring).
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
async def test_a_revoked_session_is_denied_on_the_next_operation_without_reconnecting(revoke):
    """Test 26 (spec-065 row 25): one socket, three revocation shapes, no reconnect.

    Operation 1 executes as the authenticated actor. The session is then revoked
    out of band - its row deleted, the user disabled, or the password rotated,
    the three shapes ``channels.auth.get_user`` collapses to ``AnonymousUser`` -
    and operation 2 on the SAME communicator is denied. Nothing reconnects: the
    socket is opened exactly once, by ``_open_ws``, and every later frame rides
    it.

    Operation 3 asserts the denial is STABLE (spec-065 Decision 11: "denied
    identically"). That is the fail-closed half of the contract - the scope keeps
    the stale actor rather than being downgraded to anonymous, so a revoked
    session cannot quietly become an anonymous one that keeps executing - and its
    arrival also proves the socket is still open rather than closed by the
    rejection.
    """
    user, cookie, session_key = await _make_user_and_session("revalidation_probe")
    router = _router()

    async with _open_ws(router, cookie=cookie) as communicator:
        first = await _ws_operation(communicator, "{ username }", op_id="1")
        assert first["type"] == "next", first
        assert first["payload"]["data"] == {"username": "revalidation_probe"}

        await revoke(user, session_key)

        _assert_rejected(
            await _ws_operation(communicator, "{ username }", op_id="2"),
            "2",
            errors_as_list=True,
        )
        _assert_rejected(
            await _ws_operation(communicator, "{ username }", op_id="3"),
            "3",
            errors_as_list=True,
        )


@pytest.mark.django_db(transaction=True)
async def test_a_valid_session_keeps_executing_and_the_next_operation_sees_the_refreshed_actor():
    """Test 27 (spec-065 row 26): the refreshed actor is what the next operation observes.

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
    """Test 28 (spec-065 row 27): inside the window a revoked session still executes.

    With ``websocket_revalidation_window=3600.0`` the accepted revocation delay
    is an hour, so operation 2 executes on the cached actor even though the
    session was already flushed. Advancing the clock past the window then denies
    operation 3 - proving the window defers the denial rather than disabling it.

    The clock is advanced by monkeypatching ``consumers._monotonic``, the seam
    that exists for exactly this: an ``asyncio.sleep`` would make the row
    wall-clock dependent, and this suite runs under ``-W error`` with
    ``-n auto``.
    """
    user, cookie, session_key = await _make_user_and_session("window_probe")
    router = _router(websocket_revalidation_window=3600.0)

    async with _open_ws(router, cookie=cookie) as communicator:
        first = await _ws_operation(communicator, "{ username }", op_id="1")
        assert first["type"] == "next", first
        assert first["payload"]["data"] == {"username": "window_probe"}

        await _flush_the_session(user, session_key)

        inside = await _ws_operation(communicator, "{ username }", op_id="2")
        assert inside["type"] == "next", inside
        assert inside["payload"]["data"] == {"username": "window_probe"}

        advanced = time.monotonic() + 7200.0
        monkeypatch.setattr(consumers_module, "_monotonic", lambda: advanced)

        _assert_rejected(
            await _ws_operation(communicator, "{ username }", op_id="3"),
            "3",
            errors_as_list=True,
        )


@pytest.mark.django_db(transaction=True)
async def test_the_legacy_graphql_ws_protocol_is_revalidated_at_handle_start():
    """Test 29: the SECOND protocol is revalidated too, with its own payload shape.

    ``graphql-ws`` is live on the package's mount (upstream's default
    ``subscription_protocols`` carries both), so its per-operation entry -
    ``handle_start`` - needs the same pre-hook. Its rejection payload is a SINGLE
    formatted error rather than a list, which is the one difference between the
    two call sites and is asserted as such by ``_assert_rejected``.

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

        _assert_rejected(
            await _ws_operation(communicator, _TICK_SUBSCRIPTION, op_id="2"),
            "2",
            errors_as_list=False,
        )


@pytest.mark.django_db(transaction=True)
async def test_a_revalidation_store_failure_denies_the_operation_and_is_logged(
    monkeypatch,
    caplog,
):
    """Test 30 (spec-065 row 30): a failed revalidation read fails CLOSED, and is logged.

    The fresh-store resolver raises, so the revalidation cannot answer. The
    operation is denied with the same message a revoked session gets (no
    information disclosure about which happened), the failure is reported through
    the package logger at ``ERROR`` with its traceback rather than swallowed, and
    the next operation is denied identically - there is no fall back to the
    connection's cached actor, which is the property Edge cases requires.
    """
    _user, cookie, _session_key = await _make_user_and_session("failclosed_probe")
    router = _router()

    async with _open_ws(router, cookie=cookie) as communicator:
        first = await _ws_operation(communicator, "{ username }", op_id="1")
        assert first["type"] == "next", first

        _poison_the_session_store(monkeypatch)
        with caplog.at_level(logging.ERROR, logger="django_strawberry_framework"):
            _assert_rejected(
                await _ws_operation(communicator, "{ username }", op_id="2"),
                "2",
                errors_as_list=True,
            )
            _assert_rejected(
                await _ws_operation(communicator, "{ username }", op_id="3"),
                "3",
                errors_as_list=True,
            )

    records = _package_logger_records(caplog)
    assert [record.levelname for record in records] == ["ERROR", "ERROR"]
    assert all(record.exc_info is not None for record in records)
    assert "fail-closed" in records[0].getMessage()


@pytest.mark.django_db
async def test_an_anonymous_socket_is_not_revalidated(monkeypatch, caplog):
    """Test 31: the anonymous carve-out really skips the session read.

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
    """Test 32: an unacknowledged connection is upstream's 4401, not our rejection.

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
