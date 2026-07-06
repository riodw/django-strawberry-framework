"""Channels ASGI router placeholder for spec-041.

The implemented Slice 1 surface will expose ``DjangoGraphQLProtocolRouter`` as a
soft-``channels`` migration helper. Until that slice lands, this module is kept
importable and channels-free so package walkers, docs tooling, and channels-less
consumers do not pay for a half-built optional integration.
"""

from __future__ import annotations

from typing import Any

# The one public symbol is resolved lazily via the PEP 562 module ``__getattr__``
# below, so it is never a real module global; ruff's F822 (undefined name in
# ``__all__``) is a false positive here. Listing it is deliberate: ``from
# ...routers import *`` should opt into the router and thus the channels guard
# (spec-041 finding P2.6).
__all__ = ("DjangoGraphQLProtocolRouter",)  # noqa: F822 - PEP 562 lazy export

_CHANNELS_INSTALL_HINT = (
    "DjangoGraphQLProtocolRouter requires channels, which is not installed. Install it "
    "with `pip install 'channels>=4.3.2'` (the package's verified Channels floor)."
)

# TODO(spec-041 Slice 1): add a SEPARATE builder-failure hint (spec-041 finding
# P1.3) for present-but-incompatible installs, distinct from
# _CHANNELS_INSTALL_HINT (which is top-level channels absence only). A failing
# channels.* import names `channels>=4.3.2`; a failing strawberry.channels
# consumer import names BOTH `channels>=4.3.2` and `strawberry-graphql>=0.262.0`
# with the consumers importable, so a broken Strawberry install is not
# misreported as a missing-channels problem.

_ROUTER_CLASS: type[Any] | None = None


def require_channels() -> Any:
    """Return the installed ``channels`` module once spec-041 Slice 1 implements the guard."""
    # TODO(spec-041 Slice 1): implement as a thin wrapper over
    # ``utils/imports.py::require_optional_module``; do not hand-roll a local
    # import guard in this module.
    #
    # TODO(spec-041 Slice 1) pseudo-steps:
    # - call ``require_optional_module`` with module name ``channels``;
    # - pass ``_CHANNELS_INSTALL_HINT`` as the single public hint string
    #   (``require_optional_module`` takes NO ``feature_label`` - finding P2.5);
    # - return the imported module object unchanged.
    #
    # The helper must not memoize success or failure. The router class cache
    # belongs to ``_build_router_class()`` only, so the absence tests can evict
    # ``channels*`` and re-hit the guard in the same process.
    raise NotImplementedError(
        "TODO(spec-041 Slice 1): implement require_channels() via "
        "utils.imports.require_optional_module().",
    )


def _build_router_class() -> type[Any]:
    """Materialize and cache ``DjangoGraphQLProtocolRouter`` behind the soft guard."""
    # TODO(spec-041 Slice 1): build the real ``ProtocolTypeRouter`` subclass only
    # after ``require_channels()`` succeeds. Keep every optional import inside
    # this builder, including ``strawberry.channels``; its handlers import
    # ``channels`` at module import time.
    #
    # TODO(spec-041 Slice 1) pseudo-steps:
    # - return the cached class when ``_ROUTER_CLASS`` is already populated;
    # - run ``require_channels()`` before any Channels or Strawberry-Channels
    #   import so ordinary absence always raises the single install hint;
    # - import ``ProtocolTypeRouter``, ``URLRouter``, ``AuthMiddlewareStack``,
    #   ``AllowedHostsOriginValidator``, ``re_path``, ``GraphQLHTTPConsumer``,
    #   and ``GraphQLWSConsumer`` inside one builder try block;
    # - wrap builder import failures from present-but-incompatible installs in
    #   an actionable ``ImportError`` that still chains the original exception,
    #   naming WHICH half is broken (spec-041 finding P1.3): a ``channels.*``
    #   failure names ``channels>=4.3.2``; a ``strawberry.channels`` consumer
    #   failure names both ``channels>=4.3.2`` and
    #   ``strawberry-graphql>=0.262.0`` with the consumers importable;
    # - define the router subclass with signature
    #   ``(schema, django_application=None, url_pattern="^graphql")``;
    # - build the HTTP URLs as GraphQL first, optional Django fallback second;
    # - build the WebSocket URLs as GraphQL only;
    # - pass a two-key mapping to ``ProtocolTypeRouter``:
    #   HTTP is ``AuthMiddlewareStack(URLRouter(http_urls))``;
    #   WebSocket is ``AllowedHostsOriginValidator`` outside
    #   ``AuthMiddlewareStack(URLRouter(websocket_urls))``;
    # - cache and return the subclass object.
    #
    # Do not add a package-root re-export. The public import path is deliberately
    # ``django_strawberry_framework.routers.DjangoGraphQLProtocolRouter``.
    raise NotImplementedError(
        "TODO(spec-041 Slice 1): materialize DjangoGraphQLProtocolRouter here.",
    )


def __getattr__(name: str) -> Any:
    """Resolve the future router symbol lazily; unrelated misses stay normal misses."""
    if name == "DjangoGraphQLProtocolRouter":
        # TODO(spec-041 Slice 1): return ``_build_router_class()`` once the guard
        # and class builder above are implemented.
        raise NotImplementedError(
            "TODO(spec-041 Slice 1): DjangoGraphQLProtocolRouter is not built yet.",
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
