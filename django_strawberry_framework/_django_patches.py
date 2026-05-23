"""Defensive patches to Django that ship with this package.

The package ships fixes for a small set of Django bugs that affect
consumers of ``django-strawberry-framework`` in multi-database setups.
The patches are applied once from the package's
:meth:`apps.DjangoStrawberryFrameworkConfig.ready`, so consumers get
them automatically by having ``"django_strawberry_framework"`` in
``INSTALLED_APPS`` — no opt-in boilerplate (no ``conftest.py``
workaround, no test-case base class to inherit) is required on the
consumer side.

Currently implemented
---------------------

- :func:`_patched_remove_databases_failures` — defensive replacement
  for :meth:`django.test.testcases.TransactionTestCase._remove_databases_failures`.
  Adds an ``isinstance(method, _DatabaseFailure)`` guard before the
  unwrap step, so any code path that replaced a connection method
  between ``setUpClass`` and ``tearDownClass`` no longer crashes the
  cleanup loop with ``AttributeError: 'function' object has no
  attribute 'wrapped'``.

  Tracks Django Trac #37064 (closed upstream as ``wontfix``):
  <https://code.djangoproject.com/ticket/37064>.

The patch surface is intentionally private (leading underscore on the
module). Consumers do not import from this module; the patch is
applied as a side effect of Django's app-loading. The
:func:`apply` entry point is exported (no leading underscore) so the
package's regression tests can call it explicitly without going through
the AppConfig.
"""

from django.db import connections
from django.test.testcases import TransactionTestCase, _DatabaseFailure

_PATCH_APPLIED = False


def _patched_remove_databases_failures(cls: type) -> None:
    """Defensive replacement for ``TransactionTestCase._remove_databases_failures``.

    Identical to Django's upstream classmethod except for the
    ``isinstance(method, _DatabaseFailure)`` guard before the
    ``setattr(..., method.wrapped)`` line. Without the guard, any code
    path that replaced ``connection.<method>`` with something other
    than a ``_DatabaseFailure`` instance between ``setUpClass`` and
    ``tearDownClass`` crashes the cleanup loop with
    ``AttributeError: 'function' object has no attribute 'wrapped'``.

    The patch is strictly defensive — it never makes Django's behaviour
    worse:

    * When the original wrapper is still in place, the ``isinstance``
      check passes and the method is unwrapped exactly as upstream
      does.
    * When the wrapper has been replaced, the ``isinstance`` check
      fails and the (foreign) replacement is left untouched. This
      mirrors Django's documented contract that
      ``_add_databases_failures`` / ``_remove_databases_failures``
      operate symmetrically on the methods they themselves wrapped, and
      simply declines to crash on a method the pair never owned.

    See module docstring for the upstream ticket reference.
    """
    for alias in connections:
        if alias in cls.databases:
            continue
        connection = connections[alias]
        for name, _ in cls._disallowed_connection_methods:
            method = getattr(connection, name)
            if isinstance(method, _DatabaseFailure):
                setattr(connection, name, method.wrapped)


def apply() -> None:
    """Apply every Django defensive patch shipped by the package.

    Idempotent: re-entrant calls are no-ops. Called once from
    :meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`
    at Django startup; exposed at the module level so the regression
    tests can drive the apply-and-revert cycle without spinning up a
    second AppConfig.
    """
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        return
    TransactionTestCase._remove_databases_failures = classmethod(
        _patched_remove_databases_failures,
    )
    _PATCH_APPLIED = True
