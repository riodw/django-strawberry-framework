"""Tests for ``django_strawberry_framework.routers`` (spec-041).

Both dependency states are exercised (spec-041 Decision 8):

- **channels-present** - construction / composition (the middleware wrapping
  order behind intent-named unwrap helpers), real execution through Channels'
  in-process communicators (``HttpCommunicator`` / ``WebsocketCommunicator``),
  the package-realistic request contract (a resolver reading the actor through
  ``request_from_info()``, Test 16), and the authenticated-session round trip
  (Test 18);
- **channels-absent** - simulated via the ``builtins.__import__`` block +
  strict ``sys.modules`` eviction with the TWO-SIDED restore (the parent
  package's ``routers`` attribute is saved/restored alongside the module
  entries, so the attribute path and the import path never end up holding two
  live module objects with independent class caches);
- **channels-present-but-degraded** - the same eviction discipline with one
  builder import blocked, pinning the split actionable error shapes (Test 17).

The execution schema is module-local and ORM-free: the async
``GraphQLHTTPConsumer`` executes on the event loop, where sync ORM would raise
``SynchronousOnlyOperation`` - router behavior is schema-agnostic, so a
deterministic scalar field is sufficient (spec-041 Test plan).
"""

import builtins
import contextlib
import importlib
import json
import sys

import pytest
import strawberry
from channels.auth import AuthMiddleware
from channels.db import database_sync_to_async
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from channels.sessions import CookieMiddleware, SessionMiddleware
from channels.testing import HttpCommunicator, WebsocketCommunicator

import django_strawberry_framework
import django_strawberry_framework.routers as routers_module
from django_strawberry_framework.utils.permissions import request_from_info

# The hint floors are deliberately RE-TYPED literals, matching
# ``tests/rest_framework/test_soft_dependency.py``'s ``_HINT_SUBSTRING``
# discipline: importing the router constants and asserting them against
# themselves could never catch the hint drifting from the dev-group floor.
_HINT_SUBSTRING = "channels>=4.3.2"
_STRAWBERRY_FLOOR_SUBSTRING = "strawberry-graphql>=0.262.0"


# ---------------------------------------------------------------------------
# Module-local execution schema (ORM-free; see module docstring)
# ---------------------------------------------------------------------------


@strawberry.type
class Query:
    @strawberry.field
    def ping(self) -> str:
        return "pong"

    @strawberry.field
    def whoami(self, info: strawberry.Info) -> str:
        """Read the actor through the package's shared request helper (Test 16).

        Returns the adapter type name, a scope-backed read (``user``), and a
        DELEGATED read (``method``, resolved off the wrapped ``ChannelsRequest``)
        so the round trip proves both halves of the P1.1 adapter contract.
        """
        request = request_from_info(info, family_label="FilterSet")
        return f"{type(request).__name__}|{request.user.is_anonymous}|{request.method}"

    @strawberry.field
    def username(self, info: strawberry.Info) -> str:
        """The authenticated-session probe (Test 18): the session actor's username."""
        request = request_from_info(info, family_label="FilterSet")
        return request.user.username


SCHEMA = strawberry.Schema(query=Query)


def _router_class():
    from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter

    return DjangoGraphQLProtocolRouter


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


def _graphql_post(
    application,
    query,
    path="/graphql",
    cookie=None,
):
    body = json.dumps({"query": query}).encode()
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
        (b"host", b"testserver"),
    ]
    if cookie is not None:
        headers.append((b"cookie", cookie.encode()))
    return HttpCommunicator(application, "POST", path, body=body, headers=headers)


async def _graphql_data(application, query, cookie=None):
    response = await _graphql_post(application, query, cookie=cookie).get_response(timeout=10)
    assert response["status"] == 200
    payload = json.loads(response["body"])
    assert payload.get("errors") is None, payload
    return payload["data"]


# ---------------------------------------------------------------------------
# Channels-present: construction and composition (Tests 1-6)
# ---------------------------------------------------------------------------


def test_router_is_a_protocol_type_router_mapping_exactly_http_and_websocket():
    """Test 1: a true ``ProtocolTypeRouter`` whose mapping carries exactly the two protocols.

    Framed as a current-shape parity assertion (upstream maps exactly these
    two); the behavior tests below are what the mapping must actually deliver.
    """
    router = _router_class()(SCHEMA)
    assert isinstance(router, ProtocolTypeRouter)
    assert set(router.application_mapping) == {"http", "websocket"}


def test_http_branch_is_auth_wrapped_and_routes_only_graphql_without_fallback():
    """Test 2: no ``django_application`` means the GraphQL route is the only HTTP route."""
    router = _router_class()(SCHEMA)
    url_router = unwrap_auth_stack(router.application_mapping["http"])
    assert _route_patterns(url_router) == ["^graphql"]


def test_django_application_fallback_is_appended_after_the_graphql_route():
    """Test 3: the fallback is HTTP-branch-only and ordered AFTER the GraphQL route."""

    async def fallback(scope, receive, send):  # pragma: no cover - never called here
        raise AssertionError("structural test only")

    router = _router_class()(SCHEMA, django_application=fallback)
    url_router = unwrap_auth_stack(router.application_mapping["http"])
    assert _route_patterns(url_router) == ["^graphql", "^"]
    assert url_router.routes[1].callback is fallback
    # The WS branch never grows a fallback route - parity with upstream.
    ws_router = unwrap_auth_stack(
        unwrap_origin_validator(router.application_mapping["websocket"]),
    )
    assert _route_patterns(ws_router) == ["^graphql"]


def test_websocket_branch_wraps_origin_validator_outside_the_auth_stack():
    """Test 4: ``AllowedHostsOriginValidator`` OUTSIDE ``AuthMiddlewareStack`` on WS only."""
    router = _router_class()(SCHEMA)
    inner = unwrap_origin_validator(router.application_mapping["websocket"])
    ws_router = unwrap_auth_stack(inner)
    assert _route_patterns(ws_router) == ["^graphql"]
    # The HTTP branch carries no origin validator - its outermost layer is the
    # auth stack itself.
    assert not isinstance(router.application_mapping["http"], OriginValidator)


def test_custom_url_pattern_reaches_the_re_path_on_both_branches():
    """Test 5: ``url_pattern=`` is the ``re_path`` regex on both protocol branches."""
    router = _router_class()(SCHEMA, url_pattern="^api/graphql")
    http_router = unwrap_auth_stack(router.application_mapping["http"])
    ws_router = unwrap_auth_stack(
        unwrap_origin_validator(router.application_mapping["websocket"]),
    )
    assert _route_patterns(http_router) == ["^api/graphql"]
    assert _route_patterns(ws_router) == ["^api/graphql"]


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
# Channels-present: execution through communicators (Tests 7-10)
# ---------------------------------------------------------------------------


# The communicator tests carry ``django_db``: the router's ``AuthMiddlewareStack``
# is DB-coupled (``get_user`` rides ``database_sync_to_async``), and Channels'
# consumer dispatch runs ``aclose_old_connections()`` outside the windows
# ``channels.testing`` no-op-patches - under pytest-django's blocker an unmarked
# test would trip ``Database access not allowed`` whenever another test's
# executor-thread connection lingers (in-memory sqlite ``close()`` is a no-op).


@pytest.mark.django_db
async def test_http_communicator_graphql_round_trip():
    """Test 7: a real GraphQL POST through the router's ``http`` branch resolves."""
    router = _router_class()(SCHEMA)
    data = await _graphql_data(router, "{ ping }")
    assert data == {"ping": "pong"}


@pytest.mark.django_db
async def test_non_graphql_path_reaches_the_fallback_only_when_provided():
    """Test 8: the Django fallback owns non-GraphQL HTTP paths; without it, no route."""
    seen_paths = []

    async def recording_fallback(scope, receive, send):
        seen_paths.append(scope["path"])
        await send({"type": "http.response.start", "status": 418, "headers": []})
        await send({"type": "http.response.body", "body": b"fallback"})

    router = _router_class()(SCHEMA, django_application=recording_fallback)
    communicator = HttpCommunicator(router, "GET", "/admin/login/")
    response = await communicator.get_response(timeout=10)
    assert response["status"] == 418
    assert seen_paths == ["/admin/login/"]

    bare_router = _router_class()(SCHEMA)
    communicator = HttpCommunicator(bare_router, "GET", "/admin/login/")
    await communicator.send_input({"type": "http.request", "body": b""})
    # ``wait()`` surfaces the application task's exception immediately;
    # ``get_response`` would sit out its full timeout before re-raising it.
    with pytest.raises(ValueError, match="No route found"):
        await communicator.wait(timeout=10)


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
    router = _router_class()(SCHEMA)
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


@pytest.mark.django_db
async def test_schema_object_passes_through_unchanged_with_extensions_intact():
    """Test 10: the consumers hold the exact schema object; its extensions execute.

    Proven the async-safe way (no ORM, no ``DjangoType``): a recording
    Strawberry extension fires through the router, and the structural half
    asserts the consumer ``initkwargs`` carry the identical schema object.
    """
    fired = []

    class RecordingExtension(strawberry.extensions.SchemaExtension):
        def on_operation(self):
            fired.append("operation")
            yield

    recording_schema = strawberry.Schema(query=Query, extensions=[RecordingExtension])
    router = _router_class()(recording_schema)

    # Structural identity: both branches' consumers hold the object passed in.
    http_router = unwrap_auth_stack(router.application_mapping["http"])
    ws_router = unwrap_auth_stack(
        unwrap_origin_validator(router.application_mapping["websocket"]),
    )
    assert http_router.routes[0].callback.consumer_initkwargs["schema"] is recording_schema
    assert ws_router.routes[0].callback.consumer_initkwargs["schema"] is recording_schema

    data = await _graphql_data(router, "{ ping }")
    assert data == {"ping": "pong"}
    assert fired == ["operation"]


# ---------------------------------------------------------------------------
# Channels-absent + degraded installs: the eviction-simulated states
# (Tests 11-15, 17). Absence is SIMULATED (the DRF soft-dependency discipline):
# a ``builtins.__import__`` block + strict ``sys.modules`` eviction/restore,
# two-sided (the parent package's ``routers`` attribute is restored to the SAME
# original module object as ``sys.modules``, because a blocked-then-retried
# import re-executes ``routers.py`` and rebinds the attribute to a fresh module
# with its own empty ``_ROUTER_CLASS`` cache).
# ---------------------------------------------------------------------------

_EVICT_PREFIXES = (
    "channels",
    "strawberry.channels",
    "daphne",
    "django_strawberry_framework.routers",
)

_REAL_IMPORT = builtins.__import__


def _should_evict(name):
    return any(name == prefix or name.startswith(prefix + ".") for prefix in _EVICT_PREFIXES)


@contextlib.contextmanager
def _evicted_router_state(is_blocked_name):
    """Evict the router + channels modules and block matching ABSOLUTE imports.

    ``is_blocked_name`` decides which top-level (``level == 0``) import names
    raise; relative imports (the re-executed ``routers.py`` reaching its own
    ``.utils.imports``) always pass through so the guard itself stays reachable.
    Teardown restores every evicted module AND the parent package's ``routers``
    attribute to the original module object (the two-sided restore, spec-041
    Decision 8 / Helper-reuse D3).
    """
    saved = {name: sys.modules.pop(name) for name in list(sys.modules) if _should_evict(name)}
    saved_parent_attr = getattr(django_strawberry_framework, "routers", None)

    def _blocking_import(
        name,
        globals=None,  # noqa: A002 - mirrors builtins.__import__'s exact signature
        locals=None,  # noqa: A002 - mirrors builtins.__import__'s exact signature
        fromlist=(),
        level=0,
    ):
        if level == 0 and is_blocked_name(name):
            raise ImportError(f"No module named {name!r} (simulated absence)")
        return _REAL_IMPORT(name, globals, locals, fromlist, level)

    builtins.__import__ = _blocking_import
    try:
        yield
    finally:
        builtins.__import__ = _REAL_IMPORT
        # Drop any partially-imported modules created under the block, then
        # restore the originally-evicted real modules.
        for name in list(sys.modules):
            if _should_evict(name):
                del sys.modules[name]
        sys.modules.update(saved)
        if saved_parent_attr is not None:
            django_strawberry_framework.routers = saved_parent_attr
        else:  # pragma: no cover - the module import at file top makes this unreachable
            with contextlib.suppress(AttributeError):
                delattr(django_strawberry_framework, "routers")


def _channels_absent_name(name):
    return name == "channels" or name.startswith("channels.")


@pytest.fixture
def _simulate_channels_absent():
    with _evicted_router_state(_channels_absent_name):
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
    with _evicted_router_state(_channels_absent_name):
        # Re-execute the module under the block (the rebinding the restore must undo).
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


def test_unrelated_attribute_miss_stays_a_plain_attribute_error(_simulate_channels_absent):
    """Test 15: a non-router attribute miss raises ``AttributeError``, never the hint."""
    mod = importlib.import_module("django_strawberry_framework.routers")
    with pytest.raises(AttributeError, match="DefinitelyNotARouter"):
        _ = mod.DefinitelyNotARouter


def _blocked_channels_security(name):
    return name == "channels.security.websocket"


def _blocked_strawberry_channels(name):
    return name == "strawberry.channels" or name.startswith("strawberry.channels.")


@pytest.mark.parametrize(
    ("is_blocked_name", "expected_substrings"),
    [
        pytest.param(
            _blocked_channels_security,
            [_HINT_SUBSTRING],
            id="channels-half",
        ),
        pytest.param(
            _blocked_strawberry_channels,
            [_HINT_SUBSTRING, _STRAWBERRY_FLOOR_SUBSTRING],
            id="strawberry-half",
        ),
    ],
)
def test_degraded_partial_install_raises_the_split_actionable_errors(
    is_blocked_name,
    expected_substrings,
):
    """Test 17: present-but-incompatible installs name WHICH half is broken.

    Uses the same eviction + parent-attribute-restore discipline as the absent
    path so the re-executed module has no cached ``_ROUTER_CLASS`` and the
    blocked builder import actually fires (order-independence, finding P1.2).
    A failing ``channels.*`` import names the channels floor; a failing
    ``strawberry.channels`` consumer import names BOTH halves, so a broken
    Strawberry install is never misreported as a Channels problem. Both chain
    the original ``ImportError``.
    """
    with _evicted_router_state(is_blocked_name):
        with pytest.raises(ImportError) as exc_info:
            exec("from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter", {})
        message = str(exc_info.value)
        for substring in expected_substrings:
            assert substring in message
        assert isinstance(exc_info.value.__cause__, ImportError)


# ---------------------------------------------------------------------------
# Channels-present: the package request contract (Tests 16 and 18)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
async def test_request_contract_resolves_through_the_router_for_anonymous_reads():
    """Test 16: a framework-shaped resolver works under the Channels context.

    ``request_from_info()`` resolves the Strawberry-Channels dict context to the
    wrapping adapter instead of raising ``ConfigurationError``: the
    ``AuthMiddlewareStack``-populated ``scope["user"]`` is the (anonymous) actor
    and a DELEGATED attribute (``request.method``) reads through to the wrapped
    ``ChannelsRequest`` - the P1.1 contract, end to end.
    """
    router = _router_class()(SCHEMA)
    data = await _graphql_data(router, "{ whoami }")
    assert data == {"whoami": "ChannelsRequestAdapter|True|POST"}


@pytest.mark.django_db(transaction=True)
async def test_authenticated_session_round_trip_reaches_the_resolver():
    """Test 18: a real session cookie flows through ``AuthMiddlewareStack`` to the actor.

    The user + session rows are created async-safely (``database_sync_to_async``,
    since ``AuthMiddlewareStack`` resolves the user on the event loop's executor
    thread); the resolver then sees the AUTHENTICATED user, not ``AnonymousUser``
    - what actually earns the "session user on the scope" claim (finding P1.4).
    """
    from django.conf import settings
    from django.contrib.auth import (
        BACKEND_SESSION_KEY,
        HASH_SESSION_KEY,
        SESSION_KEY,
        get_user_model,
    )

    @database_sync_to_async
    def make_user_and_session_cookie():
        user = get_user_model().objects.create_user(
            username="channels_probe",
            password="pw-9x-strong",
        )
        engine = importlib.import_module(settings.SESSION_ENGINE)
        session = engine.SessionStore()
        session[SESSION_KEY] = str(user.pk)
        session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()
        return f"{settings.SESSION_COOKIE_NAME}={session.session_key}"

    cookie = await make_user_and_session_cookie()
    router = _router_class()(SCHEMA)
    data = await _graphql_data(router, "{ username }", cookie=cookie)
    assert data == {"username": "channels_probe"}
