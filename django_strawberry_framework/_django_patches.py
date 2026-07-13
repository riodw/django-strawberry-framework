"""Defensive patches for upstream Django bugs, applied at app load.

The package ships fixes for a small set of Django bugs that affect
consumers of ``django-strawberry-framework`` in multi-database setups.
The patches are applied once from the package's
:meth:`apps.DjangoStrawberryFrameworkConfig.ready`, so consumers get
them automatically by having ``"django_strawberry_framework"`` in
``INSTALLED_APPS`` - no opt-in boilerplate (no ``conftest.py``
workaround, no test-case base class to inherit) is required on the
consumer side. Like every patch the package ships, it is gated by the
``APPLY_UPSTREAM_PATCHES`` setting (default on): a consumer who wants
the package to apply no patches at all sets
``DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}``,
and a consumer who wants to disable only this module's test-only patch
(for example while upgrading Django ahead of the package) sets the
per-dependency mapping ``{"APPLY_UPSTREAM_PATCHES": {"django":
False}}``, which leaves the production request-hardening patches
(``strawberry`` / ``cross_web``) installed. See
:func:`django_strawberry_framework.conf.upstream_patches_enabled`.

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

import inspect
import textwrap

from django.db import connections
from django.test.testcases import SimpleTestCase

from .conf import upstream_patches_enabled

try:
    from django.test.testcases import _DatabaseFailure
except ImportError:  # pragma: no cover - exercised via monkeypatch in tests
    # Preserve module import long enough for ``apply()`` to report the precise
    # unsupported upstream shape and the explicit opt-out.
    _DatabaseFailure = None  # type: ignore[assignment,misc]


_original_remove_databases_failures = SimpleTestCase.__dict__.get(
    "_remove_databases_failures",
)


# The exact upstream body this module supersedes (verbatim at Django 5.2-6.0,
# dedented). Because :func:`_patched_remove_databases_failures` REIMPLEMENTS
# upstream's whole loop instead of wrapping and delegating to it, an upstream
# body change does not flow through the patch the way it does for the
# delegating siblings (``_cross_web_patches``/``_strawberry_patches``).
# ``_validate_upstream_shape`` therefore pins this source so any upstream body
# change - a renamed ``_disallowed_connection_methods``, a changed
# ``_DatabaseFailure`` protocol, or an upstream fix of Trac #37064 itself -
# fails loudly at apply() time instead of clobbering a working teardown.
_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE = textwrap.dedent(
    """\
    @classmethod
    def _remove_databases_failures(cls):
        for alias in connections:
            if alias in cls.databases:
                continue
            connection = connections[alias]
            for name, _ in cls._disallowed_connection_methods:
                method = getattr(connection, name)
                setattr(connection, name, method.wrapped)
    """,
)


def _validate_upstream_shape() -> None:
    """Fail loudly when Django no longer matches the private shape this patch supersedes.

    Three tiers: the private symbols exist (``_DatabaseFailure`` plus the
    ``_remove_databases_failures`` classmethod descriptor), the ``(cls)``
    call shape holds, and the captured original's body source still
    matches ``_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE``. The body pin
    is the reimplementer's equivalent of the sibling patches' delegation:
    they only need their call shape validated because upstream body
    changes flow through the delegated call, while this module supersedes
    the whole body and must re-audit whenever that body changes.
    Unreadable source (e.g. a bytecode-only distribution) is treated as
    drift: an unverifiable body must not be silently superseded.
    """
    descriptor = _original_remove_databases_failures
    function = getattr(descriptor, "__func__", None)
    if _DatabaseFailure is None or not isinstance(descriptor, classmethod) or function is None:
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Django patch: expected "
            "django.test.testcases._DatabaseFailure and "
            "SimpleTestCase._remove_databases_failures as a classmethod. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"django": False} '
            "or use a supported Django version.",
        )
    parameters = tuple(inspect.signature(function).parameters.values())
    if len(parameters) != 1 or parameters[0].kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD:
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Django patch: "
            "SimpleTestCase._remove_databases_failures no longer has the expected (cls) signature. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"django": False} '
            "or use a supported Django version.",
        )
    try:
        source = textwrap.dedent(inspect.getsource(function))
    except (OSError, TypeError):
        source = None
    if source != _UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE:
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Django patch: "
            "SimpleTestCase._remove_databases_failures no longer matches the upstream body "
            "this patch supersedes. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"django": False} '
            "or use a supported Django version.",
        )


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

    Gated by the ``APPLY_UPSTREAM_PATCHES`` setting (default on):
    returns immediately, before touching ``SimpleTestCase``, when a
    consumer disabled the patches globally (``False``) or this
    dependency alone (``{"django": False}``).

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

    Before installation, validates the private symbol, classmethod
    descriptor, and ``(cls)`` signature the replacement assumes, plus the
    upstream body source the replacement supersedes (see
    :func:`_validate_upstream_shape`). Dependency drift raises a targeted
    ``RuntimeError`` instead of silently dropping the protection;
    consumers can explicitly disable this test-only patch alone
    (``{"django": False}``) - or every upstream patch (``False``) -
    through ``APPLY_UPSTREAM_PATCHES`` while upgrading dependencies.
    """
    if not upstream_patches_enabled("django"):
        return
    _validate_upstream_shape()
    if _patch_is_installed():
        return
    SimpleTestCase._remove_databases_failures = classmethod(
        _patched_remove_databases_failures,
    )
