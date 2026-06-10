"""Defensive patches to Django that ship with this package.

The package ships fixes for a small set of Django bugs that affect
consumers of ``django-strawberry-framework`` in multi-database setups.
The patches are applied once from the package's
:meth:`apps.DjangoStrawberryFrameworkConfig.ready`, so consumers get
them automatically by having ``"django_strawberry_framework"`` in
``INSTALLED_APPS`` - no opt-in boilerplate (no ``conftest.py``
workaround, no test-case base class to inherit) is required on the
consumer side.

Currently implemented
---------------------

- :func:`_patched_remove_databases_failures` - defensive replacement
  for :meth:`django.test.testcases.SimpleTestCase._remove_databases_failures`.
  Django defines the method on ``SimpleTestCase`` so a single patch
  covers every test-case class in Django's hierarchy
  (``SimpleTestCase`` -> ``TransactionTestCase`` -> ``TestCase``).
  Adds an ``isinstance(method, _DatabaseFailure)`` guard before the
  unwrap step, so any code path that replaced a connection method
  between ``setUpClass`` and ``tearDownClass`` no longer crashes the
  cleanup loop with ``AttributeError: 'function' object has no
  attribute 'wrapped'``.

  Tracks Django Trac #37064 (closed upstream as ``wontfix``):
  <https://code.djangoproject.com/ticket/37064>.

Ecosystem precedent
-------------------

Two ``django-debug-toolbar`` fixes point at the same underlying
monkey-patch fragility from opposite directions.

First, the ``isinstance(_, _DatabaseFailure)`` guard pattern is not
unique to this package. ``django-debug-toolbar`` ships the same pattern
at the SQL panel's *wrap-time* site:
:func:`debug_toolbar.panels.sql.tracking.wrap_cursor` checks
``isinstance(connection.cursor, _DatabaseFailure)`` before installing
its own cursor wrapper and refuses to wrap on top of Django's
``_DatabaseFailure``:

  <https://github.com/django-commons/django-debug-toolbar/blob/main/debug_toolbar/panels/sql/tracking.py>

This package installs the matching check at the *unwrap-time* site so
the same Django fragility cannot crash teardown regardless of which
third-party library (debug-toolbar, Sentry's Django integration, a
consumer's own ``setUp``, or anything else) replaced the wrapper.

Second, ``django-debug-toolbar``'s cache-panel fix for Sentry
interoperability reached the broader teardown conclusion: once multiple
parties can monkey-patch the same method, undoing the patch stack
perfectly can be impossible without a shared ordering protocol. That
fix kept the debug-toolbar wrapper installed and toggled an owner
sentinel instead of trying to uninstall/reinstall around every request.
That exact strategy is available to libraries that own their wrapper,
and it is the right pattern for any future package-owned connection
instrumentation here.

This package does not own Django's ``_DatabaseFailure`` wrapper, so it
cannot adopt the cache-panel sentinel approach for
``_remove_databases_failures`` itself. The best root-cause mitigation
available at this layer is the combined guard strategy:

* **Wrap-time prevention** (debug-toolbar SQL panel's flavor, and this
  package's ``safe_wrap_connection_method`` helper) - each well-behaved
  wrap-party declines to clobber Django's wrapper when it sees one
  already installed. This is the cheapest path because it avoids
  installing another wrapper at all.

* **Unwrap-time recovery** (this package's automatic patch) - Django's
  teardown becomes robust to wrappers having been replaced anyway. This
  is necessary because this package cannot force every third-party
  wrapper to participate in the wrap-time protocol.

The two guards don't fix the underlying multi-party mutation design,
but together they protect against the worst observable symptom -
crashes during ``tearDownClass`` - at the two lifecycle sites this
package can influence.

This package does NOT wrap any connection method itself, so it has
no wrap-time site of its OWN at which to add the debug-toolbar-style
preventive check. Instead the package ships
:func:`django_strawberry_framework.testing.safe_wrap_connection_method`
as a consumer-facing helper: any consumer code path that wraps a
connection method (typically in a test ``setUp`` or in middleware)
calls the helper instead of raw ``setattr``, and the helper applies
the same wrap-time isinstance check debug-toolbar uses. Consumers who
use the helper are auto-protected at the wrap site; consumers who
don't (or who use a third-party library that doesn't) are still
auto-protected at the unwrap site by the patch in this module.

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
from django.test.testcases import SimpleTestCase

from . import logger

try:
    from django.test.testcases import _DatabaseFailure
except ImportError:  # pragma: no cover - exercised via monkeypatch in tests
    # Django renamed, relocated, or removed the private ``_DatabaseFailure``
    # symbol. The package's defensive patch only makes sense when that
    # symbol exists, so ``apply()`` will no-op instead of crashing the
    # whole app loader. See ``apply()`` for the runtime branch and the
    # accompanying test ``test_apply_no_ops_when_database_failure_symbol_missing``.
    _DatabaseFailure = None  # type: ignore[assignment,misc]


# Module-level sentinel: ``apply()`` may run more than once because
# ``AppConfig.ready()`` can fire repeatedly under some Django test
# runners. The missing-``_DatabaseFailure`` notice should log only on
# the first such call per process so the framework logger isn't spammed
# during repeated app initialization. Patched to ``False`` in the
# regression tests for hermetic per-test state.
_missing_symbol_logged = False


def _is_database_failure(method: object) -> bool:
    """Return whether ``method`` is Django's disallowed-database wrapper."""
    return _DatabaseFailure is not None and isinstance(method, _DatabaseFailure)


def _patched_remove_databases_failures(cls: type) -> None:
    """Defensive replacement for ``SimpleTestCase._remove_databases_failures``.

    Identical to Django's upstream classmethod except for the
    ``isinstance(method, _DatabaseFailure)`` guard before the
    ``setattr(..., method.wrapped)`` line. Without the guard, any code
    path that replaced ``connection.<method>`` with something other
    than a ``_DatabaseFailure`` instance between ``setUpClass`` and
    ``tearDownClass`` crashes the cleanup loop with
    ``AttributeError: 'function' object has no attribute 'wrapped'``.

    The patch is strictly defensive - it never makes Django's behaviour
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
            if _is_database_failure(method):
                setattr(connection, name, method.wrapped)


def _patch_is_installed() -> bool:
    """Return ``True`` iff ``SimpleTestCase._remove_databases_failures`` currently points at our patch.

    Encapsulates the ``__func__`` unwrap so ``apply()`` does not need to
    know that Django stores the method as a ``classmethod`` descriptor
    on the class. Used by ``apply()`` to enforce the "ensure current
    state" contract - if a third party reverted the class attribute
    after a prior ``apply()`` call, the next ``apply()`` re-installs.
    """
    installed = SimpleTestCase.__dict__.get("_remove_databases_failures")
    if installed is None:
        return False
    return getattr(installed, "__func__", None) is _patched_remove_databases_failures


def apply() -> None:
    """Apply every Django defensive patch shipped by the package.

    Idempotent and self-healing: re-entrant calls are no-ops when the
    patch is still installed, and re-install the patch if a third
    party reverted the class attribute since the prior call. Called
    from
    :meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`
    at Django startup (which may itself fire more than once under some
    Django test runners - the ``_patch_is_installed()`` check below
    handles both the re-entrant case and a third-party revert);
    exposed at the module level so the regression tests can drive the
    apply-and-revert cycle without spinning up a second AppConfig.

    When Django renamed, relocated, or removed the private
    ``_DatabaseFailure`` symbol the patch depends on (``ImportError``
    at module load time), this function logs a single ``INFO``-level
    notice (once per process, gated by the ``_missing_symbol_logged``
    module sentinel so repeat ``ready()`` invocations don't spam the
    logger) and returns without touching ``SimpleTestCase``. That keeps
    the rest of the package loadable on future Django versions that
    break the private symbol.
    """
    global _missing_symbol_logged
    if _DatabaseFailure is None:
        if not _missing_symbol_logged:
            logger.info(
                "django-strawberry-framework: skipping _remove_databases_failures patch - "
                "Django's private _DatabaseFailure symbol is unavailable at this Django "
                "version. The Trac #37064 backstop will not be installed.",
            )
            _missing_symbol_logged = True
        return
    if _patch_is_installed():
        return
    SimpleTestCase._remove_databases_failures = classmethod(
        _patched_remove_databases_failures,
    )
