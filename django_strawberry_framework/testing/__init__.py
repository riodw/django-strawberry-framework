"""Testing utilities for consumers of ``django-strawberry-framework``.

Currently exports
-----------------

- :func:`safe_wrap_connection_method` — cooperative wrap helper that
  declines to clobber Django's ``_DatabaseFailure`` wrapper. The
  wrap-time mirror of the unwrap-time backstop the package installs in
  :mod:`django_strawberry_framework._django_patches`. Mirrors
  ``django-debug-toolbar``'s wrap-time isinstance check at
  :func:`debug_toolbar.panels.sql.tracking.wrap_cursor`. Together the
  two checks form a defense-in-depth against Django Trac #37064's
  ``AttributeError: 'function' object has no attribute 'wrapped'`` at
  ``tearDownClass`` — see the patch module's docstring for the full
  framing.

Future exports (tracked in ``docs/GLOSSARY.md``; planned for
``0.0.12``):

- ``TestClient``, ``AsyncTestClient`` — live ``/graphql/`` HTTP clients
  for consumer test suites.
- ``GraphQLTestCase`` — a ``django.test.TestCase`` subclass that
  bundles the common patterns.

The subpackage exists now so consumers have a stable import path
(``from django_strawberry_framework.testing import …``) regardless of
which utility lands first.
"""

from django_strawberry_framework.testing._wrap import safe_wrap_connection_method

__all__ = ["safe_wrap_connection_method"]
