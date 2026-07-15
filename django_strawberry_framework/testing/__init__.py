"""Consumer test utilities for GraphQL clients, connection wrapping, and Relay GlobalID helpers.

Currently exports
-----------------

- :class:`TestClient` / :class:`AsyncTestClient` - live ``/graphql/`` HTTP
  test clients for consumer test suites (spec-043): thin wrappers over
  ``django.test.Client`` / ``django.test.AsyncClient`` posting GraphQL
  operations (JSON, or multipart when ``files=`` is provided) and returning
  the typed :class:`Response`. Endpoint from
  ``DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]`` (default
  ``"/graphql/"``), overridable per instance (``path=``) and per call
  (``url=``).
- :class:`Response` - the typed result (``errors`` / ``data`` /
  ``extensions``, subclassing ``strawberry.test.client.Response``) carrying
  the raw ``django.http.HttpResponse`` as ``response``.
- :class:`GraphQLTestMixin` / :class:`GraphQLTestCase` /
  :class:`GraphQLTransactionTestCase` - the graphene-django-shaped unittest
  family: ``self.query(...)`` through the test case's own ``self.client``,
  plus the ``assertResponseNoErrors`` / ``assertResponseHasErrors`` helpers.
- :func:`safe_wrap_connection_method` - cooperative wrap helper that
  declines to clobber Django's ``_DatabaseFailure`` wrapper. The
  wrap-time mirror of the unwrap-time backstop the package installs in
  :mod:`django_strawberry_framework._django_patches`. Mirrors
  ``django-debug-toolbar``'s wrap-time isinstance check at
  :func:`debug_toolbar.panels.sql.tracking.wrap_cursor`. Together the
  two checks form a defense-in-depth against Django Trac #37064's
  ``AttributeError: 'function' object has no attribute 'wrapped'`` at
  ``tearDownClass`` - see the patch module's docstring for the full
  framing.
- :func:`global_id_for` / :func:`decode_global_id` - the public Relay test
  helpers, importable at the dotted
  ``django_strawberry_framework.testing.relay`` submodule path (NOT
  re-exported here; the card's DoD names the submodule path). Minting the
  strategy-aware encoded ``GlobalID`` a finalized Relay-Node-shaped type
  emits, and decoding one back to ``(target_type, node_id)`` - see
  :mod:`django_strawberry_framework.testing.relay` for the full contract,
  including the secondary-emitter decode asymmetry. Keeping them out of this
  ``__init__`` also keeps ``import django_strawberry_framework.testing``
  light - the submodule's ``types``-package imports are paid only by suites
  that import it (the client module's own ``django.test`` /
  ``strawberry.test`` imports are already paid by any process running Django
  tests, which is the only process that imports ``testing`` at all).
"""

from django_strawberry_framework.testing._wrap import safe_wrap_connection_method
from django_strawberry_framework.testing.client import (
    AsyncTestClient,
    GraphQLTestCase,
    GraphQLTestMixin,
    GraphQLTransactionTestCase,
    Response,
    TestClient,
)

__all__ = [
    "AsyncTestClient",
    "GraphQLTestCase",
    "GraphQLTestMixin",
    "GraphQLTransactionTestCase",
    "Response",
    "TestClient",
    "safe_wrap_connection_method",
]
