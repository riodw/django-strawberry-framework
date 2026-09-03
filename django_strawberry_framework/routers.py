"""Channels ASGI router: Django owns HTTP, the package composes WebSocket (spec-046).

``DjangoGraphQLProtocolRouter`` is the package's Channels transport helper - a
``channels.routing.ProtocolTypeRouter`` subclass whose ``"http"`` value IS the
consumer's own Django ASGI application, dispatched directly with no wrapper.
Every HTTP request therefore traverses the project's real ``MIDDLEWARE`` - the
``ALLOWED_HOSTS`` host check, CSRF, security headers, cache policy, and every
consumer-authored middleware - exactly as it does under WSGI. The router does
not serve GraphQL over HTTP at all: the GraphQL HTTP endpoint is
``views.py::DjangoGraphQLView``, declared in the consumer's own URLconf
(spec-046 Decisions 2, 3 and 6).

The ``"websocket"`` value is the package's Channels composition:
``consumers.py::DjangoWebSocketHostValidator`` (the Host check, which calls
Django's own ``HttpRequest.get_host()``; spec-046 Decision 19) wrapping
``AllowedHostsOriginValidator`` (the Origin check) wrapping
``AuthMiddlewareStack`` (sessions + ``scope["user"]``) wrapping a ``URLRouter``
holding one ``re_path`` onto a GraphQL WebSocket consumer, matched by
``websocket_url_pattern`` - exact at both ends by default (spec-046 Decision 4;
spec-041 Decisions 3 and 5). This module composes those wrappers and names them;
it implements no transport policy of its own - the Host validator lives in
``consumers.py`` beside the consumer factory, which is the package's WebSocket
module.

Which consumer sits at the end of that chain is the ``websocket_consumer_class``
seam (spec-046 Decision 11): by default ``consumers.py``'s revalidating
``GraphQLWSConsumer`` subclass, otherwise a consumer class or factory the
project injects. All three wrappers are the ROUTER's either way, so an injected
consumer cannot escape the Host check, the Origin check, or authentication - and
those are two separate checks, in that order, neither standing in for the other.

``channels`` is a SOFT dependency (spec-041 Decision 5): importing this module
is channels-free, and the router class materializes lazily through the PEP 562
module ``__getattr__`` behind the ``require_channels()`` guard - the
install-hint ``ImportError`` fires at the consumer's
``from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter``
line (their ``asgi.py``), never at ``import django_strawberry_framework``. The
HTTP half of the card needs none of it: ``views.py`` is channels-free, so a
WSGI-only project adopts the GraphQL view without the soft dependency.
"""

from __future__ import annotations

import inspect
import re
import threading
from typing import TYPE_CHECKING, Any

from .consumers import (
    _DEFAULT_REVALIDATION_WINDOW,
    DjangoWebSocketHostValidator,
    build_revalidating_consumer_class,
    resolved_revalidation_window,
)
from .exceptions import ConfigurationError, describe_value
from .utils.imports import CHANNELS_FLOOR, STRAWBERRY_FLOOR, require_optional_module

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from django.core.handlers.asgi import ASGIHandler
    from strawberry.schema import BaseSchema

# The one public symbol is resolved lazily via the PEP 562 module ``__getattr__``
# below, so it is never a real module global; ruff's F822 (undefined name in
# ``__all__``) is a false positive here. Listing it is deliberate: ``from
# ...routers import *`` should opt into the router and thus the channels guard
# (spec-041).
__all__ = ("DjangoGraphQLProtocolRouter",)  # noqa: F822 - PEP 562 lazy export

# The single channels-ABSENT install hint (spec-041 Decision 5). The floor
# itself is ``utils/imports.py::CHANNELS_FLOOR`` - the only other place it is
# written is the ``channels[daphne]`` dev-group row in ``pyproject.toml``, which
# must be bumped with it. One floor covers the package's whole advertised Django
# range through 6.0.
_CHANNELS_INSTALL_HINT = (
    "DjangoGraphQLProtocolRouter requires channels, which is not installed. Install it "
    f"with `pip install 'channels>={CHANNELS_FLOOR}'` (the package's verified Channels floor)."
)

# Present-but-incompatible builder failures get their OWN actionable messages
# (spec-041), split by which half of the import boundary broke so a
# broken Strawberry install is never misreported as a missing-channels problem.
_CHANNELS_BROKEN_HINT = (
    "DjangoGraphQLProtocolRouter could not import its Channels composition pieces even "
    "though `channels` is installed - the install is likely broken or older than the "
    f"package's verified floor. Reinstall with `pip install 'channels>={CHANNELS_FLOOR}'`."
)
# Both floors are interpolated, never re-typed: this hint names two dependencies
# and each one's version lives in ``utils/imports.py`` (``CHANNELS_FLOOR``,
# ``STRAWBERRY_FLOOR``) with exactly one other written copy, its own
# ``pyproject.toml`` dependency row.
_STRAWBERRY_CHANNELS_BROKEN_HINT = (
    "DjangoGraphQLProtocolRouter could not import Strawberry's Channels consumers. It "
    f"requires both `channels>={CHANNELS_FLOOR}` and `strawberry-graphql>={STRAWBERRY_FLOOR}` "
    "with the `strawberry.channels` consumer (GraphQLWSConsumer) importable."
)

# The construction-time failure for an unusable ``django_application``
# (spec-046 Decision 3 / Error shapes). Names all three facts a migrant needs:
# what the removed mode was actually doing, that it is REMOVED rather than
# flagged, and the two-place repair (the asgi.py argument AND the URLconf
# entry - migration is no longer one line). Omitting the argument entirely is
# Python's own ``TypeError``, deliberately, so a required parameter fails as one.
_MISSING_DJANGO_APPLICATION_HINT = (
    "DjangoGraphQLProtocolRouter requires a usable Django ASGI application for its `http` "
    "branch. A 0.0.14 deployment that passed `django_application=None` (or omitted it) "
    "served GraphQL over HTTP through a Channels consumer, OUTSIDE Django's middleware "
    "stack: no ALLOWED_HOSTS host check, no CSRF protection, and no security headers on "
    "the one route that accepts session credentials. That mode is REMOVED, not flagged. "
    "Repair it in two places: pass "
    "`django_application=django.core.asgi.get_asgi_application()` from your asgi.py, and "
    "serve GraphQL HTTP from your URLconf with `path('graphql/', "
    "django_strawberry_framework.views.DjangoGraphQLView.as_view(schema=schema))`."
)

# The construction-time failure for an unusable ``websocket_consumer_class``
# (spec-046 Decision 11). Names both accepted shapes and their calling
# conventions, because the seam's whole safety argument is that the router - not
# the consumer - applies the Host/Origin and auth wrappers around whatever is
# injected. The received value is appended at the raise site.
_UNUSABLE_WEBSOCKET_CONSUMER_HINT = (
    "websocket_consumer_class must be either a strawberry.channels.GraphQLWSConsumer "
    "subclass (mounted through its own `as_asgi(schema=schema)`) or a factory callable "
    "invoked as `factory(schema=schema)` that returns the ASGI application to mount; "
    "None selects the package's own revalidating consumer. Either way the router still "
    "wraps the result in DjangoWebSocketHostValidator, AllowedHostsOriginValidator and "
    "AuthMiddlewareStack, so an injected consumer opts out of revalidation, never out of "
    "the wrappers."
)

# The factory half of that seam, spelled once and shared by BOTH of its
# construction-time rejections (the calling convention and the returned object) -
# a consumer who got one of them wrong needs the same whole contract restated
# either way (spec-046 Decision 11).
_FACTORY_CONTRACT_HINT = (
    "A websocket_consumer_class factory is invoked ONCE, at router construction, as "
    "`factory(schema=schema)`, and must return the ASGI application the WebSocket route "
    "mounts - typically `YourConsumer.as_asgi(schema=schema)`, or an `async def "
    "app(scope, receive, send)` function itself (never the coroutine that CALLING one "
    "returns). The router wraps whatever it returns in DjangoWebSocketHostValidator, "
    "AllowedHostsOriginValidator and AuthMiddlewareStack."
)
# Appended only for the coroutine shape, which is the one mistake whose repair is
# not obvious from the contract alone: the factory is one `async` keyword away
# from correct, and the router cannot await anything at construction time.
_ASYNC_FACTORY_HINT = (
    " A coroutine object is what an `async def` factory returns, so this factory is one "
    "keyword away from correct: make it a plain `def` that RETURNS the ASGI application. "
    "Router construction is synchronous and cannot await anything."
)

# Rejecting the combination rather than ignoring the window: a knob that does
# nothing is worse than an error
# (spec-046 Edge cases #"is meaningless when a custom class"). An explicit
# ``0.0`` alongside an injected class stays legal - it configures nothing
# either way.
_WINDOW_WITH_INJECTED_CONSUMER_HINT = (
    "websocket_revalidation_window configures the package's own WebSocket consumer, so "
    "it cannot be combined with a positive value and websocket_consumer_class: an "
    "injected consumer class owns its own revalidation policy. Drop the window (or pass "
    "0.0) and implement the policy in the injected class, or drop the class to use the "
    "package consumer."
)

_INVALID_WEBSOCKET_URL_PATTERN_HINT = (
    "websocket_url_pattern must be a valid regular-expression string used only for the "
    "WebSocket URLRouter branch; got "
)

# The built router class, cached by ``_build_router_class()``. A module global so
# evicting this module from ``sys.modules`` drops the cache with it - the property
# the eviction-simulated absence and degraded-install tests rely on.
_ROUTER_CLASS: type[Any] | None = None
_ROUTER_CLASS_LOCK = threading.Lock()


def _validated_websocket_url_pattern(value: object) -> str:
    """Validate the WebSocket URL regex before Django installs a route.

    Django's ``re_path`` stringifies non-string values when it lazily compiles a
    ``RegexPattern``.  That makes ``None``, a number, or an arbitrary object silently
    install a route that never matches (and lets a hostile ``__str__`` fail later during
    the first handshake).  The router's public annotation is a string, so reject every
    other type at construction and compile the string now to turn malformed regexes into
    the same typed configuration boundary.
    """
    if type(value) is not str:
        raise ConfigurationError(
            f"{_INVALID_WEBSOCKET_URL_PATTERN_HINT}{describe_value(value)}.",
        )
    try:
        re.compile(value)
    except BaseException as exc:
        raise ConfigurationError(
            f"{_INVALID_WEBSOCKET_URL_PATTERN_HINT}{describe_value(value)}.",
        ) from exc
    return value


def require_channels() -> Any:
    """Import + return the ``channels`` package, or raise the install-hint ``ImportError``.

    A thin wrapper over the shared optional-import owner
    (``utils/imports.py::require_optional_module``) passing the single
    ``_CHANNELS_INSTALL_HINT`` string - the ``require_drf()`` contract
    generalized (spec-041 Decision 5). No memoization: each access re-fires the
    guard so eviction-based absence tests can re-hit it in one process.
    """
    return require_optional_module("channels", install_hint=_CHANNELS_INSTALL_HINT)


def _require_factory_calling_convention(factory: Any, *, schema: BaseSchema) -> None:
    """Raise ``ConfigurationError`` unless ``factory(schema=schema)`` can bind.

    See ``_factory_application`` rejection 1 for why the binding is pre-checked
    rather than caught. An un-introspectable callable is deliberately allowed
    through: ``inspect.signature`` raises ``TypeError`` / ``ValueError`` for the
    standard un-introspectable shapes, and a consumer-defined ``__signature__``
    descriptor may raise another ordinary exception; none is evidence that the
    CALL would fail.
    """
    try:
        signature = inspect.signature(factory)
    except Exception:
        return
    try:
        signature.bind(schema=schema)
    except TypeError as exc:
        raise ConfigurationError(
            f"{_FACTORY_CONTRACT_HINT} The factory {describe_value(factory)} cannot accept "
            f"that call: {exc}.",
        ) from exc


def _factory_application(factory: Any, *, schema: BaseSchema) -> Any:
    """Invoke the injection seam's factory and validate what it handed back.

    The factory shape's whole contract is enforced here, at CONSTRUCTION, because
    the alternative is a value that is not an ASGI application being installed as
    a URL route callback and failing on the first matching handshake, deep inside
    Channels' routing, with no mention of the seam that produced it. Two rejections, both
    ``ConfigurationError``:

    1. **The calling convention.** Bound with ``inspect.signature(...).bind``
       BEFORE the call rather than by catching ``TypeError`` around it: a
       ``TypeError`` raised by the call cannot be told apart from one raised
       INSIDE a correct factory's body, and converting the latter into a
       configuration error would mask a consumer bug behind the wrong diagnosis.
       Pre-binding uses the same algorithm the call itself would, so it accepts
       exactly what the call accepts; a callable whose signature cannot be read
       (a C callable, a ``__signature__`` liar) skips the pre-check and is judged
       by the call, which is why this is not a new source of false rejections.
       The originating ``TypeError`` is preserved as ``__cause__``.
    2. **The returned object.** What "a valid ASGI application" means at
       construction time is deliberately narrow, and stated rather than implied:
       the only honest, false-positive-free check is that the object is
       CALLABLE. ASGI conformance - accepting ``(scope, receive, send)``,
       awaiting, emitting the right event dicts - is observable only by running a
       real connection through it, which construction must not do. So this is a
       floor, not a conformance proof: it converts every shape that CANNOT be an
       ASGI application (``None``, a scalar, a mapping, a coroutine object) into
       an actionable construction error, and leaves a callable that merely
       misbehaves to fail at the handshake, where its own traceback is the useful
       signal. Rejected alternative: arity-checking the RESULT with
       ``bind(scope, receive, send)``, which would falsely reject legitimate
       ``*args`` middleware, ``functools.partial`` mounts and callable instances
       whose ``__call__`` is a C slot - a real cost for no security gain.

    The factory's OWN exceptions are never normalized. A factory that raises from
    its body is a consumer bug whose traceback is the most useful thing the
    package can hand back, and wrapping it would only bury it.
    """
    _require_factory_calling_convention(factory, schema=schema)
    application = factory(schema=schema)
    if callable(application):
        return application

    received = describe_value(application)
    addendum = ""
    if inspect.iscoroutine(application):
        # Close the coroutine this rejection refuses. Dropping it un-awaited makes
        # CPython emit an unraisable "coroutine ... was never awaited"
        # RuntimeWarning from the garbage collector at an unrelated moment - noise
        # that points at the package instead of at the factory, and a hard error
        # in any consumer running under ``-W error``.
        application.close()
        addendum = _ASYNC_FACTORY_HINT
    raise ConfigurationError(
        f"{_FACTORY_CONTRACT_HINT}{addendum} The factory {describe_value(factory)} returned "
        f"{received}.",
    )


def _websocket_application(
    candidate: Any,
    *,
    schema: BaseSchema,
    package_consumer_class: type[Any],
    base_consumer_class: type[Any],
    revalidation_window: float,
) -> Any:
    """Resolve the WebSocket branch's ASGI application from the injection seam.

    Exactly three accepted shapes (spec-046 Decision 11): ``None`` selects the
    package's own revalidating consumer and hands it the validated window; a
    ``GraphQLWSConsumer`` subclass is mounted through its own
    ``as_asgi(schema=schema)``; any other callable is a factory, invoked as
    ``factory(schema=schema)`` by ``_factory_application``, which validates both
    the calling convention and the returned application before it is mounted.
    Everything else raises ``ConfigurationError``.

    The class test comes first on purpose: a class IS callable, so testing
    ``callable`` first would route a non-consumer class into the factory branch
    and call it with an unexpected keyword instead of naming the real mistake.
    Lives here rather than inline in ``__init__`` so the class builder does not
    grow a four-branch selector, and takes ``base_consumer_class`` as an argument
    because ``GraphQLWSConsumer`` is only in scope inside that builder.
    """
    if candidate is None:
        return package_consumer_class.as_asgi(
            schema=schema,
            revalidation_window=revalidation_window,
        )
    if isinstance(candidate, type):
        if issubclass(candidate, base_consumer_class):
            return candidate.as_asgi(schema=schema)
    elif callable(candidate):
        return _factory_application(candidate, schema=schema)
    raise ConfigurationError(
        f"{_UNUSABLE_WEBSOCKET_CONSUMER_HINT} Got {describe_value(candidate)}.",
    )


def _build_router_class() -> type[Any]:
    """Return the one lazily-built router class, serializing its first construction."""
    global _ROUTER_CLASS
    if _ROUTER_CLASS is not None:
        return _ROUTER_CLASS
    with _ROUTER_CLASS_LOCK:
        if _ROUTER_CLASS is not None:
            return _ROUTER_CLASS
        return _build_router_class_uncached()


def _build_router_class_uncached() -> type[Any]:
    """Materialize and cache ``DjangoGraphQLProtocolRouter`` behind the soft guard.

    ``require_channels()`` runs FIRST so every true-absence path routes through
    the single install hint (``strawberry.channels`` imports ``channels.db`` at
    module level, so it is equally unimportable without channels). A guard-passing
    build whose imports then fail is a present-but-incompatible install; each
    half raises its own actionable ``ImportError`` chaining the original
    (spec-041 Error shapes).
    """
    global _ROUTER_CLASS

    require_channels()

    try:
        from channels.auth import AuthMiddlewareStack
        from channels.routing import ProtocolTypeRouter, URLRouter
        from channels.security.websocket import AllowedHostsOriginValidator
    except ImportError as exc:
        raise ImportError(_CHANNELS_BROKEN_HINT) from exc
    try:
        from strawberry.channels import GraphQLWSConsumer
    except ImportError as exc:
        raise ImportError(_STRAWBERRY_CHANNELS_BROKEN_HINT) from exc

    from django.urls import re_path

    # Built once, inside the same guarded builder, so the package consumer class
    # is cached with ``_ROUTER_CLASS`` and dies with it: a module-level cache in
    # ``consumers.py`` would survive the eviction-simulated absence tests and hand
    # a fresh router a subclass derived from a dead ``GraphQLWSConsumer``.
    package_consumer_class = build_revalidating_consumer_class(GraphQLWSConsumer)

    class DjangoGraphQLProtocolRouter(ProtocolTypeRouter):
        """GraphQL over WebSocket, with the consumer's Django application owning HTTP.

        The ASGI entrypoint, which now pairs with one URLconf entry (spec-046
        Decisions 2, 3, 4 and 6)::

            # myproject/asgi.py
            import os

            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

            from django.core.asgi import get_asgi_application

            django_asgi = get_asgi_application()   # Django is fully initialized here

            from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter
            from myproject.schema import schema

            application = DjangoGraphQLProtocolRouter(
                schema,
                django_application=django_asgi,    # REQUIRED
            )

            # myproject/urls.py
            from django.urls import path

            from django_strawberry_framework.views import DjangoGraphQLView

            urlpatterns = [
                path("graphql/", DjangoGraphQLView.as_view(schema=schema)),
            ]

        ``django_application`` is required and becomes the ``"http"`` value
        verbatim - no ``URLRouter``, no ``re_path``, no ``AuthMiddlewareStack``,
        and no GraphQL consumer - so HTTP runs Django's own request lifecycle.
        Omitting it raises ``TypeError``; ``None`` or any non-callable raises
        ``ConfigurationError`` naming the migration. The router never calls
        ``get_asgi_application()`` itself: *when* that runs is load-bearing
        (it calls ``django.setup()``), so it stays the consumer's explicit,
        visible decision.

        ``websocket_url_pattern`` governs the WebSocket branch ONLY and is
        exact at both ends by default (``r"^graphql/?$"``), so - with Channels'
        leading-slash strip - ``/graphql`` and ``/graphql/`` match while
        ``/graphql-admin``, ``/graphqlanything``, and ``/graphql/extra`` do not.
        HTTP path matching belongs entirely to the Django URLconf, so the two
        declarations are independent by design: a project that moves its GraphQL
        URL changes both.

        The WebSocket branch carries ``AuthMiddlewareStack`` (the session
        machinery and ``scope["user"]``) inside ``AllowedHostsOriginValidator``,
        which denies cross-origin - and missing-``Origin`` - handshakes against
        ``ALLOWED_HOSTS``, inside ``consumers.py::DjangoWebSocketHostValidator``,
        which denies a handshake whose ``Host`` Django's own
        ``HttpRequest.get_host()`` refuses (spec-046 Decision 19). Those are two
        separate questions - which server authority the client addressed, and
        which browser origin initiated the socket - so both run and neither
        substitutes for the other. ``schema`` passes through untouched, extensions
        intact.

        ``websocket_consumer_class`` is the WebSocket consumer injection seam
        (spec-046 Decision 11), accepting either a
        ``strawberry.channels.GraphQLWSConsumer`` subclass - mounted through its
        own ``as_asgi(schema=schema)`` - or a factory callable invoked as
        ``factory(schema=schema)`` that returns the ASGI application to mount.
        Anything else raises ``ConfigurationError``, and so does a factory that
        cannot accept that call or does not return a mountable (callable)
        application: the seam fails at construction rather than on the first
        matching handshake. Whatever is injected, the
        three wrappers above are applied by the ROUTER around it, so an injected
        consumer opts out of the package's revalidation but never out of the Host
        check, the Origin check, or authentication.

        ``None`` (the default) selects the package's own
        ``consumers.py::GraphQLWebSocketConsumer``, which revalidates the session
        actor at TWO security checkpoints - operation admission, and every
        outbound information-bearing frame - because the actor is
        connection-scoped, not operation-scoped. The first failed validation at
        either checkpoint therefore closes the whole SOCKET with upstream's own
        ``4403`` / ``"Forbidden"``, suppressing the pending frame and sending no
        preceding operation error: the close IS the rejection.
        ``websocket_revalidation_window`` is the accepted revocation delay in
        seconds for that consumer: ``0.0`` (the default) revalidates at every
        checkpoint - every admission and every information-bearing frame - and a
        positive value trades one session read per authenticated checkpoint for a
        named number of seconds during which a revoked session still executes. It
        configures the package's consumer only, so pairing a positive window with
        ``websocket_consumer_class`` is a construction error rather than a
        silently ignored knob. See
        ``consumers.py::GraphQLWebSocketConsumer`` for which frame types are
        gated, the maximum-connection-lifetime statement, and the knobs an
        injected class can set.
        """

        def __init__(
            self,
            schema: BaseSchema,
            django_application: ASGIHandler,
            *,
            websocket_url_pattern: str = r"^graphql/?$",
            websocket_consumer_class: Any = None,
            websocket_revalidation_window: float = _DEFAULT_REVALIDATION_WINDOW,
        ) -> None:
            # One guard for both failure shapes Error shapes gives one message:
            # ``callable(None)`` is already False, so the migrant who carried
            # ``django_application=None`` over from 0.0.14 lands on the prose
            # here rather than on a bare ``TypeError``.
            if not callable(django_application):
                raise ConfigurationError(_MISSING_DJANGO_APPLICATION_HINT)

            websocket_url_pattern = _validated_websocket_url_pattern(websocket_url_pattern)

            # Validated on its own terms first, so a bad value is a bad value
            # whatever else was passed; only then is the combination judged.
            window = resolved_revalidation_window(websocket_revalidation_window)
            if websocket_consumer_class is not None and window > 0.0:
                raise ConfigurationError(_WINDOW_WITH_INJECTED_CONSUMER_HINT)

            websocket_application = _websocket_application(
                websocket_consumer_class,
                schema=schema,
                package_consumer_class=package_consumer_class,
                base_consumer_class=GraphQLWSConsumer,
                revalidation_window=window,
            )

            super().__init__(
                {
                    "http": django_application,
                    # Host OUTSIDE Origin (spec-046 Decision 19): the Host check
                    # answers which server authority was addressed, so it runs
                    # before Channels' Origin check, before the session
                    # middleware, and before any consumer is constructed. The
                    # HTTP branch needs neither - Django's own ALLOWED_HOSTS
                    # middleware already owns the question there.
                    "websocket": DjangoWebSocketHostValidator(
                        AllowedHostsOriginValidator(
                            AuthMiddlewareStack(
                                URLRouter(
                                    [
                                        re_path(
                                            websocket_url_pattern,
                                            websocket_application,
                                        ),
                                    ],
                                ),
                            ),
                        ),
                    ),
                },
            )

    _ROUTER_CLASS = DjangoGraphQLProtocolRouter
    return _ROUTER_CLASS


def __getattr__(name: str) -> Any:
    """Resolve ``DjangoGraphQLProtocolRouter`` lazily; unrelated misses stay normal misses."""
    if name == "DjangoGraphQLProtocolRouter":
        return _build_router_class()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
