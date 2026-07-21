"""Transport-owned auth session boundary (auth session-lifecycle hardening, Commit 1).

The private classification + capability layer the login / logout state machines
build on. It is deliberately NOT re-exported: neither ``auth.__all__`` nor the
package root names it, and importing it stays ``channels``-free (the ``channels``
soft-dependency is reached lazily, through the same ``require_optional_module``
install-hint family the router uses, only after a real Channels scope has been
classified).

``request_from_info`` (``utils/permissions.py::request_from_info``) resolves a
Django ``HttpRequest`` or a ``ChannelsRequestAdapter``; this module classifies
that object into ONE explicit transport mode before any credential or session
work. Classification begins with an ``isinstance`` check against
``ChannelsRequestAdapter`` rather than sniffing for scope-like attributes,
because the adapter's ``__getattr__`` delegation
(``utils/permissions.py::ChannelsRequestAdapter.__getattr__``) makes
attribute-presence checks unreliable. Only once the request is known to be an
adapter does ``scope["type"]`` distinguish a Channels HTTP scope from a Channels
WebSocket scope; a Django ``HttpRequest`` takes the native Django path; a missing
or unknown scope type is rejected with an actionable error. The transport is
never detected by catching ``AttributeError`` from Django's auth functions.

The module also owns:

* the missing-session pre-check (``adapter.session is None`` -- and the Django
  request whose ``SessionMiddleware`` never ran -- becomes an actionable,
  transport-specific configuration error instead of a downstream
  ``None.cycle_key()`` ``AttributeError``);
* the per-scope ``asyncio.Lock`` primitive and its single acquisition helper that
  the login / logout state machines serialize their same-scope mutations under;
* the session-engine capability answers (login is unsupported on any WebSocket;
  logout is unsupported on a signed-cookie-engine WebSocket) the later stages
  gate on.
"""

from __future__ import annotations

import asyncio
import contextlib
import enum
from collections.abc import AsyncIterator, MutableMapping
from typing import Any

from django.http import HttpRequest

from ..exceptions import ConfigurationError
from ..utils.imports import require_optional_module
from ..utils.permissions import ChannelsRequestAdapter

# The single channels-ABSENT install hint for the auth transport (mirrors
# ``routers.py::_CHANNELS_INSTALL_HINT`` but keyed to this feature so hint strings
# stay single-sited at their owner, per ``utils/imports.py``). A Channels-shaped
# context can only reach this module through ``request_from_info``'s duck-typed
# adapter, so if it arrives without the optional dependency the classification
# raises this rather than swallowing the failure into a later ``AttributeError``.
_CHANNELS_INSTALL_HINT = (
    "A Channels request scope reached the auth session boundary, but channels is not "
    "installed. Install it with `pip install 'channels>=4.3.2'` (the package's verified "
    "Channels floor)."
)

# The private, collision-resistant scope key the per-scope ``asyncio.Lock`` is
# stored under. Namespaced with the distribution name so it can never collide
# with an ASGI key set by Channels, Django, or consumer middleware.
_SCOPE_LOCK_KEY = "__django_strawberry_framework_auth_session_lock__"


class Transport(enum.Enum):
    """The explicit auth transport modes ``classify_transport`` resolves.

    Each mode carries a distinct native session-mutation path and persistence
    contract (auth session-lifecycle hardening plan, Transport contract table):
    ``DJANGO_HTTP`` uses Django's native ``authenticate`` / ``login`` / ``logout``;
    both Channels modes use ``channels.auth`` and require the soft dependency.
    """

    DJANGO_HTTP = "django_http"
    CHANNELS_HTTP = "channels_http"
    CHANNELS_WEBSOCKET = "channels_websocket"


def require_channels() -> Any:
    """Import + return ``channels``, or raise the auth install-hint ``ImportError``.

    A thin wrapper over the shared optional-import owner
    (``utils/imports.py::require_optional_module``) passing this module's own
    ``_CHANNELS_INSTALL_HINT``. Called only from the Channels branch of
    ``classify_transport`` -- i.e. only after a Channels-shaped context has been
    recognized -- so ordinary package / ``auth`` import stays channels-free.
    """
    return require_optional_module("channels", install_hint=_CHANNELS_INSTALL_HINT)


def classify_transport(request: Any) -> Transport:
    """Resolve the ``request_from_info`` result to one explicit ``Transport`` mode.

    Begins with ``isinstance(request, ChannelsRequestAdapter)`` (attribute-presence
    sniffing is unreliable under the adapter's ``__getattr__`` delegation). A
    recognized adapter first forces the ``channels`` soft dependency through
    ``require_channels()`` -- a Channels-shaped context that reached this boundary
    without the dependency is a loud, actionable ``ImportError``, never a swallowed
    failure -- then reads ``scope["type"]`` to split Channels HTTP from Channels
    WebSocket. A Django ``HttpRequest`` takes the native Django path. Every other
    object, and every missing / unrecognized scope type, is rejected with an
    actionable ``ConfigurationError``.
    """
    if isinstance(request, ChannelsRequestAdapter):
        require_channels()
        scope_type = request.scope.get("type")
        if scope_type == "http":
            return Transport.CHANNELS_HTTP
        if scope_type == "websocket":
            return Transport.CHANNELS_WEBSOCKET
        raise ConfigurationError(
            "The auth session boundary received a Channels request scope with an "
            f'unsupported `type` ({scope_type!r}); expected `"http"` or `"websocket"`. '
            "Route GraphQL through DjangoGraphQLProtocolRouter so the scope carries a "
            "recognized protocol type.",
        )
    if isinstance(request, HttpRequest):
        return Transport.DJANGO_HTTP
    raise ConfigurationError(
        "The auth session boundary could not classify the request transport (got "
        f"{type(request).__name__}); expected a Django HttpRequest or a Strawberry "
        "Channels request adapter.",
    )


def require_session(request: Any, transport: Transport) -> Any:
    """Return the request's session, or raise the actionable missing-middleware error.

    A Django request whose ``SessionMiddleware`` never ran has no ``session``
    attribute, and a Channels adapter over a scope with no ``SessionMiddleware``
    exposes ``session`` as ``None`` (``ChannelsRequestAdapter.session``); both
    collapse to ``getattr(request, "session", None) is None`` here. Without this
    pre-check the absence surfaces downstream as a raw ``None.cycle_key()``
    ``AttributeError`` during the native login/logout; the pre-check converts it
    into a transport-specific configuration error. The message keeps the substring
    ``"session"`` (the failed-login byte-compatible envelope promise does not cover
    this configuration error, so its wording is otherwise free).
    """
    session = getattr(request, "session", None)
    if session is None:
        raise ConfigurationError(
            f"The auth session boundary has no session for the {transport.value} transport; "
            "install Django's SessionMiddleware (and, for Channels, wrap the scope in "
            "AuthMiddlewareStack) so login/logout can mutate a real session.",
        )
    return session


def _require_mutable_scope(adapter: ChannelsRequestAdapter) -> MutableMapping[str, Any]:
    """Return the adapter's scope as a ``MutableMapping``, or raise loudly.

    ``ChannelsRequestAdapter.scope`` is typed as a read-only ``Mapping``, but
    storing the per-scope lock needs mutation. Real ASGI scopes are ordinary
    ``dict`` objects, so this rejection is unreachable through a normal
    communicator; it must fail loudly rather than silently fall back to an
    unserialized path (which would drop the same-scope mutation guarantee).
    """
    scope = adapter.scope
    if not isinstance(scope, MutableMapping):
        raise ConfigurationError(
            "The auth session boundary requires a mutable Channels scope to serialize "
            f"same-scope session mutations, but got a {type(scope).__name__}; real ASGI "
            "scopes are dictionaries. Do not route auth through an immutable scope.",
        )
    return scope


@contextlib.asynccontextmanager
async def scope_session_lock(adapter: ChannelsRequestAdapter) -> AsyncIterator[asyncio.Lock]:
    """Hold the per-scope ``asyncio.Lock`` for the duration of the ``async with`` block.

    The single acquisition helper the login / logout state machines serialize
    their same-scope session mutation, persistence, and compensation under
    (security invariant 12: one scope-owned lock, never a process-global registry
    or ``ContextVar``). The lock is created lazily on first use and stored under
    ``_SCOPE_LOCK_KEY`` in the (mutable) scope, so every operation multiplexed on
    the same Channels connection shares one lock. The lazy get-or-create runs with
    no ``await`` between the read and the store, so it is atomic on the single
    event loop.

    An ``asyncio.Lock`` binds to the running loop the first time it is contended.
    The router's async consumer always runs a scope on one persistent loop, but the
    ``async_to_sync`` sync bridge runs each hop on a fresh private loop, so a scope
    reused across bridged calls could see a cross-loop ``RuntimeError`` instead of
    serializing. The sync-bridge arm must therefore only ever see single-operation
    (per-request) scopes - a directly-invoked ``SyncGraphQLHTTPConsumer`` builds a
    new scope per request, so its lock is created and awaited on that request's own
    bridge loop and never crosses loops. Long-lived multiplexed scopes (WebSocket)
    only ever reach the native async body, never the bridge.
    """
    scope = _require_mutable_scope(adapter)
    lock = scope.get(_SCOPE_LOCK_KEY)
    if lock is None:
        lock = asyncio.Lock()
        scope[_SCOPE_LOCK_KEY] = lock
    async with lock:
        yield lock


def uses_signed_cookie_sessions() -> bool:
    """True when the configured session engine is Django's signed-cookie engine.

    A settings / session-store read (``settings.SESSION_ENGINE``), NOT adapter
    metadata: the transport module answers the capability question itself rather
    than bolting a session-engine flag onto ``ChannelsRequestAdapter``. Resolves
    the engine's ``SessionStore`` and tests it against the signed-cookie store so a
    deployment subclassing that engine (which shares its no-server-side-record
    limitation) is recognized too.
    """
    from django.conf import settings
    from django.contrib.sessions.backends.signed_cookies import (
        SessionStore as SignedCookieSessionStore,
    )
    from django.utils.module_loading import import_string

    store_cls = import_string(f"{settings.SESSION_ENGINE}.SessionStore")
    return issubclass(store_cls, SignedCookieSessionStore)


def login_supported(transport: Transport) -> bool:
    """Whether ``login`` can truthfully establish a durable session on ``transport``.

    Login is unsupported on ANY WebSocket regardless of engine: an established
    WebSocket cannot send the replacement session cookie login's key rotation
    produces, so it could only authenticate the in-memory scope while silently
    failing to establish a reusable browser session (auth plan root cause 3).
    """
    return transport is not Transport.CHANNELS_WEBSOCKET


def logout_supported(transport: Transport) -> bool:
    """Whether ``logout`` can truthfully invalidate the session on ``transport``.

    Logout is supportable everywhere except a signed-cookie-engine WebSocket:
    server-side engines invalidate by deleting the record (no new cookie needed),
    but a signed-cookie WebSocket has no server-side record to revoke and cannot
    delete or replace the browser cookie over an established socket (auth plan root
    cause 3).
    """
    if transport is Transport.CHANNELS_WEBSOCKET:
        return not uses_signed_cookie_sessions()
    return True
