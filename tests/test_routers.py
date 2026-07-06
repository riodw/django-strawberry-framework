"""Pending tests for ``django_strawberry_framework.routers`` (spec-041 Slice 1)."""

# The hint floor is deliberately re-typed in the eventual executable tests,
# matching ``tests/rest_framework/test_soft_dependency.py``. Importing the
# router constant and asserting it against itself would not catch dependency
# floor drift.
_HINT_SUBSTRING = "channels>=4.3.2"


# TODO(spec-041 Slice 1): build the channels-present fixtures and structural
# helper functions here. Keep attribute spelunking isolated behind intent names.
#
# TODO(spec-041 Slice 1) pseudo-steps:
# - ``unwrap_origin_validator`` should assert the WebSocket branch is an
#   ``OriginValidator`` instance and return its ``.application`` child;
# - ``unwrap_auth_stack`` should assert the Cookie, Session, and Auth middleware
#   layers in order and return the inner router application;
# - ``minimal_schema`` should build a small async Strawberry query returning
#   ``"pong"`` so communicator tests do real protocol work without touching ORM.


# TODO(spec-041 Slice 1): implement channels-absent simulation by adapting the
# DRF soft-dependency fixture, with the parent-package restore fixed for modules.
#
# TODO(spec-041 Slice 1) pseudo-steps:
# - save and evict every ``channels*``, ``strawberry.channels*``, and framework
#   router module from ``sys.modules``;
# - save the parent package's current ``routers`` attribute, including the
#   "missing" state;
# - monkeypatch absolute ``channels`` imports to raise ``ImportError`` while
#   leaving framework-relative imports alone;
# - after the test, undo the monkeypatch, delete partial modules, restore saved
#   modules, and restore the parent attribute to the same object or absence;
# - assert after teardown that the parent attribute and ``sys.modules`` agree on
#   the router module object whenever a module object should exist.


# TODO(spec-041 Slice 1): executable tests 1-6, construction and composition.
#
# TODO(spec-041 Slice 1) pseudo-code:
# - importing ``DjangoGraphQLProtocolRouter`` yields a cached subclass of
#   ``channels.routing.ProtocolTypeRouter``;
# - its ``application_mapping`` currently has exactly ``{"http", "websocket"}``;
# - the HTTP branch unwraps through ``AuthMiddlewareStack`` to a ``URLRouter``;
# - the HTTP fallback route is absent by default and appended after GraphQL when
#   ``django_application=`` is provided;
# - the WS branch unwraps ``OriginValidator`` outside ``AuthMiddlewareStack``;
# - ``url_pattern=`` reaches the ``re_path`` entries on both protocol branches;
# - repeated symbol access returns the same class object and that class is
#   subclassable.


# TODO(spec-041 Slice 1): executable tests 7-10, communicator behavior.
#
# TODO(spec-041 Slice 1) pseudo-code:
# - ``HttpCommunicator`` POST to ``/graphql`` returns ``{"data": {"ping": "pong"}}``;
# - non-GraphQL HTTP path reaches a recording fallback ASGI callable only when
#   ``django_application=`` is supplied;
# - ``WebsocketCommunicator`` connects to ``/graphql`` with matching
#   ``Origin: http://testserver`` and the ``graphql-transport-ws`` subprotocol;
# - the same websocket path with a mismatched origin is denied;
# - a schema built with ``strawberry_config()`` and ``DjangoOptimizerExtension``
#   executes unchanged, proving the router passes the schema object through.


# TODO(spec-041 Slice 1): executable tests 11-15, channels-absent behavior.
#
# TODO(spec-041 Slice 1) pseudo-code:
# - ``import django_strawberry_framework`` succeeds and star import binds no
#   router symbol;
# - ``import django_strawberry_framework.routers`` succeeds without channels;
# - ``from django_strawberry_framework.routers import DjangoGraphQLProtocolRouter``
#   raises ImportError matching ``_HINT_SUBSTRING``;
# - after fixture teardown, present-path access works again and the parent
#   package attribute and ``sys.modules`` point at the same router module;
# - unrelated module attribute misses raise ordinary ``AttributeError``.


# TODO(spec-041 Slice 1): executable Test 16, the package request contract.
#
# TODO(spec-041 Slice 1) pseudo-code:
# - build a schema resolver that calls
#   ``utils/permissions.py::request_from_info(info, family_label="Auth")``;
# - run it through ``HttpCommunicator`` and the router;
# - assert anonymous scope user resolution returns a value instead of raising
#   ``ConfigurationError``. This proves framework-shaped code works under the
#   Channels context, not just plain Strawberry transport.


# TODO(spec-041 Slice 1): executable Test 17, degraded partial install.
#
# TODO(spec-041 Slice 1) pseudo-code:
# - with ``channels`` importable, block one builder-required import such as
#   ``channels.security.websocket`` after evicting the relevant modules;
# - symbol access raises an actionable ImportError matching ``_HINT_SUBSTRING``;
# - ``exc_info.value.__cause__`` is the original ImportError, preserving the
#   missing transitive symbol for deployment debugging.
