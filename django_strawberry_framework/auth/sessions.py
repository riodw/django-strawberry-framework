"""Transport-owned auth session boundary: transport classification + capability.

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
  gate on. They are built on ``utils/sessions.py::session_store_class``, imported
  below: the engine expression stays single-sited, but it is single-sited
  OUTSIDE this package, because its other caller
  (``consumers.py::_refreshed_actor``, which reloads a WebSocket connection's
  session during the per-operation actor revalidation - spec-046 Decision 11)
  must not import ``auth`` at all. ``auth/__init__.py`` eagerly imports
  ``.mutations`` / ``.queries``, so an ``auth``-hosted resolver would have made
  the first authenticated WebSocket operation register the whole opt-in auth
  subsystem (spec-040 Decision 3) just to read ``SESSION_ENGINE``.
"""

from __future__ import annotations

import asyncio
import contextlib
import enum
from collections.abc import AsyncIterator, MutableMapping
from typing import Any

from django.http import HttpRequest

from ..exceptions import (
    ConfigurationError,
    _safe_arg_repr,
    _safe_type_name,
)
from ..utils.imports import CHANNELS_FLOOR, require_optional_module
from ..utils.permissions import ChannelsRequestAdapter
from ..utils.sessions import (
    ScopeSingletonMessages,
    scope_key,
    scope_singleton,
    session_store_class,
)

# The single channels-ABSENT install hint for the auth transport (mirrors
# ``routers.py::_CHANNELS_INSTALL_HINT`` but keyed to this feature so hint strings
# stay single-sited at their owner, per ``utils/imports.py``). A Channels-shaped
# context can only reach this module through ``request_from_info``'s duck-typed
# adapter, so if it arrives without the optional dependency the classification
# raises this rather than swallowing the failure into a later ``AttributeError``.
_CHANNELS_INSTALL_HINT = (
    "A Channels request scope reached the auth session boundary, but channels is not "
    f"installed. Install it with `pip install 'channels>={CHANNELS_FLOOR}'` (the package's "
    "verified Channels floor)."
)

# The private, collision-resistant scope key the per-scope ``asyncio.Lock`` is
# stored under. Namespaced with the distribution name so it can never collide
# with an ASGI key set by Channels, Django, or consumer middleware.
_SCOPE_LOCK_KEY = scope_key("auth_session_lock")

# The per-scope lazy singleton itself is ``utils/sessions.py::scope_singleton``
# (shared with the WebSocket revalidation state, which had the same
# read / create-with-no-await / validate-or-fail-closed body); only these four
# wordings are the auth boundary's own.
_SCOPE_LOCK_MESSAGES = ScopeSingletonMessages(
    unreadable="The auth session boundary could not read the Channels request scope.",
    unstorable="The auth session boundary could not store the per-scope session lock.",
    uninspectable=(
        "The auth session boundary requires an asyncio.Lock per scope, but the "
        "stored value could not be inspected."
    ),
    corrupted=(
        "The auth session boundary requires an asyncio.Lock per scope, but got a "
        "{actual}; the per-scope lock is corrupted."
    ),
)


class Transport(enum.Enum):
    """The explicit auth transport modes ``classify_transport`` resolves.

    Each mode carries a distinct native session-mutation path and persistence
    contract:
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
    try:
        is_channels = isinstance(request, ChannelsRequestAdapter)
    except BaseException as exc:
        raise ConfigurationError(
            "The auth session boundary could not classify the request transport (got "
            f"{_safe_type_name(request)}); expected a Django HttpRequest or a Strawberry "
            "Channels request adapter.",
        ) from exc
    if is_channels:
        require_channels()
        try:
            scope = request.scope
        except BaseException as exc:
            raise ConfigurationError(
                "The auth session boundary could not read the Channels request scope.",
            ) from exc
        try:
            scope_type = scope.get("type")
        except BaseException as exc:
            raise ConfigurationError(
                "The auth session boundary could not read the Channels request scope's `type`.",
            ) from exc
        try:
            is_http = scope_type == "http"
        except BaseException as exc:
            raise ConfigurationError(
                "The auth session boundary received a Channels request scope with an "
                f'unsupported `type` ({_safe_arg_repr(scope_type)}); expected `"http"` or '
                '`"websocket"`. Serve GraphQL over HTTP through DjangoGraphQLView in your '
                "URLconf, and over WebSocket through DjangoGraphQLProtocolRouter, so the scope "
                "carries a recognized protocol type.",
            ) from exc
        if is_http:
            return Transport.CHANNELS_HTTP
        try:
            is_websocket = scope_type == "websocket"
        except BaseException as exc:
            raise ConfigurationError(
                "The auth session boundary received a Channels request scope with an "
                f'unsupported `type` ({_safe_arg_repr(scope_type)}); expected `"http"` or '
                '`"websocket"`. Serve GraphQL over HTTP through DjangoGraphQLView in your '
                "URLconf, and over WebSocket through DjangoGraphQLProtocolRouter, so the scope "
                "carries a recognized protocol type.",
            ) from exc
        if is_websocket:
            return Transport.CHANNELS_WEBSOCKET
        raise ConfigurationError(
            "The auth session boundary received a Channels request scope with an "
            f'unsupported `type` ({_safe_arg_repr(scope_type)}); expected `"http"` or '
            '`"websocket"`. Serve GraphQL over HTTP through DjangoGraphQLView in your '
            "URLconf, and over WebSocket through DjangoGraphQLProtocolRouter, so the scope "
            "carries a recognized protocol type.",
        )
    try:
        is_django = isinstance(request, HttpRequest)
    except BaseException as exc:
        raise ConfigurationError(
            "The auth session boundary could not classify the request transport (got "
            f"{_safe_type_name(request)}); expected a Django HttpRequest or a Strawberry "
            "Channels request adapter.",
        ) from exc
    if is_django:
        return Transport.DJANGO_HTTP
    raise ConfigurationError(
        "The auth session boundary could not classify the request transport (got "
        f"{_safe_type_name(request)}); expected a Django HttpRequest or a Strawberry "
        "Channels request adapter.",
    )


def _safe_transport_label(transport: Any) -> str:
    """Render ``transport`` for an error message without trusting its dunders.

    ``transport`` is expected to be a ``Transport`` enum, but the error path
    must not propagate ``BaseException`` from a hostile ``transport.value``,
    ``transport.__repr__``, or a ``str``-subclass ``value``. Falls back to
    ``_safe_type_name`` so the message stays actionable.
    """
    try:
        raw = transport.value  # type: ignore[union-attr]
    except BaseException:
        return _safe_type_name(transport)
    try:
        if isinstance(raw, str):
            return str.__str__(raw)
        return _safe_arg_repr(raw)
    except BaseException:
        return _safe_type_name(transport)


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
    try:
        session = getattr(request, "session", None)
    except BaseException as exc:
        label = _safe_transport_label(transport)
        raise ConfigurationError(
            f"The auth session boundary has no session for the {label} transport; "
            "install Django's SessionMiddleware (and, for Channels, wrap the scope in "
            "AuthMiddlewareStack) so login/logout can mutate a real session.",
        ) from exc
    if session is None:
        label = _safe_transport_label(transport)
        raise ConfigurationError(
            f"The auth session boundary has no session for the {label} transport; "
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
    try:
        scope = adapter.scope
    except BaseException as exc:
        raise ConfigurationError(
            "The auth session boundary could not read the Channels request scope.",
        ) from exc
    try:
        is_mutable = isinstance(scope, MutableMapping)
    except BaseException as exc:
        raise ConfigurationError(
            "The auth session boundary requires a mutable Channels scope to serialize "
            "same-scope session mutations, but the scope kind could not be inspected.",
        ) from exc
    if not is_mutable:
        raise ConfigurationError(
            "The auth session boundary requires a mutable Channels scope to serialize "
            f"same-scope session mutations, but got a {_safe_type_name(scope)}; real ASGI "
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
    lock = scope_singleton(
        scope,
        _SCOPE_LOCK_KEY,
        factory=asyncio.Lock,
        expect=asyncio.Lock,
        messages=_SCOPE_LOCK_MESSAGES,
    )
    try:
        await lock.acquire()
    except ConfigurationError:
        raise
    except (asyncio.CancelledError, KeyboardInterrupt, SystemExit):
        raise
    except BaseException as exc:
        raise ConfigurationError(
            "The auth session boundary's per-scope session lock could not be acquired.",
        ) from exc
    try:
        yield lock
    finally:
        if lock.locked():
            lock.release()


def uses_signed_cookie_sessions() -> bool:
    """True when the configured session engine is Django's signed-cookie engine.

    A settings / session-store read (``settings.SESSION_ENGINE``), NOT adapter
    metadata: the transport module answers the capability question itself rather
    than bolting a session-engine flag onto ``ChannelsRequestAdapter``. Resolves
    the engine's ``SessionStore`` through the shared
    ``utils/sessions.py::session_store_class`` and tests it against the
    signed-cookie store so a deployment subclassing that engine (which shares its
    no-server-side-record limitation) is recognized too.
    """
    from django.contrib.sessions.backends.signed_cookies import (
        SessionStore as SignedCookieSessionStore,
    )

    try:
        store_cls = session_store_class()
    except ConfigurationError:
        raise
    except BaseException as exc:
        raise ConfigurationError(
            "The auth session boundary could not resolve the session store class.",
        ) from exc
    try:
        return issubclass(store_cls, SignedCookieSessionStore)
    except BaseException as exc:
        raise ConfigurationError(
            "The auth session boundary could not inspect the session store class "
            f"({type(exc).__name__}); check settings.SESSION_ENGINE.",
        ) from exc


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
