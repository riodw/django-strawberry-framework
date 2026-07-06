"""Channels ASGI router: GraphQL on HTTP + WebSocket in one import (spec-041).

``DjangoGraphQLProtocolRouter`` is the package's Channels transport helper - a
``channels.routing.ProtocolTypeRouter`` subclass wiring Strawberry's Channels
consumers onto both protocols with Django's ``AuthMiddlewareStack`` (sessions +
``scope["user"]`` on both) and ``AllowedHostsOriginValidator`` (the WebSocket
origin check) composed in, exactly the upstream
``strawberry_django.routers.AuthGraphQLProtocolTypeRouter`` composition under a
distinctly-ours name (spec-041 Decisions 3 and 6).

``channels`` is a SOFT dependency (spec-041 Decision 5): importing this module
is channels-free, and the router class materializes lazily through the PEP 562
module ``__getattr__`` behind the ``require_channels()`` guard - the
install-hint ``ImportError`` fires at the consumer's
``from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter``
line (their ``asgi.py``), never at ``import django_strawberry_framework``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .utils.imports import require_optional_module

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from django.core.handlers.asgi import ASGIHandler
    from strawberry.schema import BaseSchema

# The one public symbol is resolved lazily via the PEP 562 module ``__getattr__``
# below, so it is never a real module global; ruff's F822 (undefined name in
# ``__all__``) is a false positive here. Listing it is deliberate: ``from
# ...routers import *`` should opt into the router and thus the channels guard
# (spec-041 finding P2.6).
__all__ = ("DjangoGraphQLProtocolRouter",)  # noqa: F822 - PEP 562 lazy export

# The single channels-ABSENT install hint (spec-041 Decision 5 / Helper-reuse D2):
# names the verified floor (place 2 of the three-places-that-must-agree; place 1
# is the ``channels[daphne]>=4.3.2`` dev-group row, place 3 is the spec's Risks
# note). One floor covers the package's whole advertised Django range through 6.0.
_CHANNELS_INSTALL_HINT = (
    "DjangoGraphQLProtocolRouter requires channels, which is not installed. Install it "
    "with `pip install 'channels>=4.3.2'` (the package's verified Channels floor)."
)

# Present-but-incompatible builder failures get their OWN actionable messages
# (spec-041 finding P1.3), split by which half of the import boundary broke so a
# broken Strawberry install is never misreported as a missing-channels problem.
_CHANNELS_BROKEN_HINT = (
    "DjangoGraphQLProtocolRouter could not import its Channels composition pieces even "
    "though `channels` is installed - the install is likely broken or older than the "
    "package's verified floor. Reinstall with `pip install 'channels>=4.3.2'`."
)
_STRAWBERRY_CHANNELS_BROKEN_HINT = (
    "DjangoGraphQLProtocolRouter could not import Strawberry's Channels consumers. It "
    "requires both `channels>=4.3.2` and `strawberry-graphql>=0.262.0` with the "
    "`strawberry.channels` consumers (GraphQLHTTPConsumer / GraphQLWSConsumer) importable."
)

# The built router class, cached by ``_build_router_class()``. A module global so
# evicting this module from ``sys.modules`` drops the cache with it - the property
# the eviction-simulated absence and degraded-install tests rely on.
_ROUTER_CLASS: type[Any] | None = None


def require_channels() -> Any:
    """Import + return the ``channels`` package, or raise the install-hint ``ImportError``.

    A thin wrapper over the shared optional-import owner
    (``utils/imports.py::require_optional_module``) passing the single
    ``_CHANNELS_INSTALL_HINT`` string - the ``require_drf()`` contract
    generalized (spec-041 Decision 5). No memoization: each access re-fires the
    guard so eviction-based absence tests can re-hit it in one process.
    """
    return require_optional_module("channels", install_hint=_CHANNELS_INSTALL_HINT)


def _build_router_class() -> type[Any]:
    """Materialize and cache ``DjangoGraphQLProtocolRouter`` behind the soft guard.

    ``require_channels()`` runs FIRST so every true-absence path routes through
    the single install hint (``strawberry.channels`` imports ``channels.db`` at
    module level, so it is equally unimportable without channels). A guard-passing
    build whose imports then fail is a present-but-incompatible install; each
    half raises its own actionable ``ImportError`` chaining the original
    (spec-041 Error shapes).
    """
    global _ROUTER_CLASS
    if _ROUTER_CLASS is not None:
        return _ROUTER_CLASS

    require_channels()

    try:
        from channels.auth import AuthMiddlewareStack
        from channels.routing import ProtocolTypeRouter, URLRouter
        from channels.security.websocket import AllowedHostsOriginValidator
    except ImportError as exc:
        raise ImportError(_CHANNELS_BROKEN_HINT) from exc
    try:
        from strawberry.channels import GraphQLHTTPConsumer, GraphQLWSConsumer
    except ImportError as exc:
        raise ImportError(_STRAWBERRY_CHANNELS_BROKEN_HINT) from exc

    from django.urls import re_path

    class DjangoGraphQLProtocolRouter(ProtocolTypeRouter):
        """GraphQL on both HTTP and WebSocket, with Django auth sessions on the scope.

        The one-import ASGI entrypoint (spec-041 Decision 6 - the composition and
        constructor signature are byte-compatible with upstream
        ``strawberry_django.routers.AuthGraphQLProtocolTypeRouter``)::

            from django.core.asgi import get_asgi_application

            django_asgi = get_asgi_application()

            from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter
            from myproject.schema import schema

            application = DjangoGraphQLProtocolRouter(
                schema,
                django_application=django_asgi,
            )

        Every HTTP and WebSocket request matching ``url_pattern`` (a ``re_path``
        regex, default ``"^graphql"``) routes to Strawberry's Channels consumers
        over ``schema`` (passed through untouched, extensions intact); both
        branches carry ``AuthMiddlewareStack`` so the session machinery and
        ``scope["user"]`` are present; the WebSocket branch is wrapped in
        ``AllowedHostsOriginValidator`` (cross-origin - and missing-``Origin`` -
        handshakes are denied against ``ALLOWED_HOSTS``); non-GraphQL HTTP paths
        fall through to ``django_application`` when provided (HTTP-branch only,
        after the GraphQL route).
        """

        def __init__(
            self,
            schema: BaseSchema,
            django_application: ASGIHandler | None = None,
            url_pattern: str = "^graphql",
        ) -> None:
            http_urls = [re_path(url_pattern, GraphQLHTTPConsumer.as_asgi(schema=schema))]
            if django_application is not None:
                http_urls.append(re_path(r"^", django_application))

            super().__init__(
                {
                    "http": AuthMiddlewareStack(URLRouter(http_urls)),
                    "websocket": AllowedHostsOriginValidator(
                        AuthMiddlewareStack(
                            URLRouter(
                                [re_path(url_pattern, GraphQLWSConsumer.as_asgi(schema=schema))],
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
