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

Ecosystem precedent
-------------------

The ``isinstance(_, _DatabaseFailure)`` guard pattern is not unique to
this package. ``django-debug-toolbar`` ships the same pattern at the
*wrap-time* site:
:func:`debug_toolbar.panels.sql.tracking.wrap_cursor` checks
``isinstance(connection.cursor, _DatabaseFailure)`` BEFORE installing
its own cursor wrapper and refuses to wrap on top of Django's
``_DatabaseFailure``:

  <https://github.com/django-commons/django-debug-toolbar/blob/main/debug_toolbar/panels/sql/tracking.py>

This package installs the matching check at the *unwrap-time* site so
the same Django fragility cannot crash teardown regardless of which
third-party library (debug-toolbar, Sentry's Django integration, a
consumer's own ``setUp``, or anything else) replaced the wrapper.
Together the two pattern-mates form a defense-in-depth against the
"multi-party wrap on one connection-method attribute" architectural
limitation Django's setup/teardown pair has:

* **Wrap-time prevention** (debug-toolbar's flavor) — each well-behaved
  wrap-party declines to clobber Django's wrapper when it sees one
  already installed. Sufficient if everyone participates.

* **Unwrap-time recovery** (this package's flavor) — Django's teardown
  becomes robust to wrappers having been replaced anyway. Sufficient
  regardless of whether anyone participates.

As the upstream ticket discussion notes, correct teardown when N parties
wrap one attribute is *theoretically* impossible to do without an
ordering protocol Python doesn't provide and Django doesn't enforce.
The two pragmatic mitigations above don't fix the underlying design
fragility, but they protect against the worst observable symptom —
crashes during ``tearDownClass`` — at the only two sites each library
controls.

This package does NOT wrap any connection method itself, so it has
no wrap-time site at which to add the debug-toolbar-style preventive
check. A future card may ship a consumer-facing helper
(``safe_wrap_connection_method``) that lets consumers writing
monkey-patches in their own ``setUp`` use the same isinstance pattern;
that is out of scope here.

Surface visibility
------------------

The patch module is intentionally private (leading underscore on the
module). Consumers do not import from this module; the patch is
applied as a side effect of Django's app-loading. The :func:`apply`
entry point is exported (no leading underscore) so the package's
regression tests can call it explicitly without going through the
AppConfig.
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

    The unwrap-time isinstance check here is the mirror of the
    wrap-time isinstance check ``django-debug-toolbar`` uses in
    :func:`debug_toolbar.panels.sql.tracking.wrap_cursor` (which
    declines to install a debug-cursor wrapper on top of a
    ``_DatabaseFailure``). Two pragmatic mitigations of the same
    underlying multi-party-wrap fragility, applied at the two
    lifecycle sites each library controls. See module docstring for
    the upstream ticket reference and the defense-in-depth framing.
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
