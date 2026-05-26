"""Tests for the package's Django defensive patches.

System-under-test: :mod:`django_strawberry_framework._django_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

The currently-shipped patch hardens
``SimpleTestCase._remove_databases_failures`` against Django Trac
#37064 (closed upstream as ``wontfix``):
<https://code.djangoproject.com/ticket/37064>. Without the patch, any
code path that replaces a connection method between ``setUpClass`` and
``tearDownClass`` crashes the cleanup loop with
``AttributeError: 'function' object has no attribute 'wrapped'``.
Django defines the classmethod on ``SimpleTestCase`` itself, so a
single patch on the base class covers ``TransactionTestCase`` and
``TestCase`` via normal inheritance — including direct
``SimpleTestCase`` subclasses, which ``TransactionTestCase`` is NOT in
the MRO of.

These tests do not require ``FAKESHOP_SHARDED=1``; they drive the
patched method directly against synthetic ``SimpleTestCase`` /
``TransactionTestCase`` subclasses with hand-built ``databases``
allow-lists. The test ``default`` alias is always present, so a
one-alias multi-DB scenario is enough to exercise both branches of
the patched loop. (The end-to-end demo shape from
<https://github.com/riodw/django-remove_databases_failures-demo> runs
under vanilla ``manage.py test`` rather than pytest-django and cannot
be reproduced 1:1 under our test runner — pytest-django's per-test
flush calls ``connection.cursor()`` mid-lifecycle and crashes on the
swapped cursor before reaching ``tearDownClass``. The unit tests
below isolate the bug class from that machinery.)
"""

from unittest import mock

import pytest
from django.db import connections
from django.test.testcases import SimpleTestCase, TestCase, TransactionTestCase

from django_strawberry_framework import _django_patches


def _database_failure(wrapped):
    if _django_patches._DatabaseFailure is None:
        pytest.skip("Django private _DatabaseFailure symbol is unavailable.")
    return _django_patches._DatabaseFailure(wrapped, "test message")


def test_apply_is_idempotent():
    """Repeated calls to :func:`apply` leave the patch installed.

    Pins the "ensure current state" contract called out in the module
    docstring. AppConfig.ready() may run more than once under some
    Django test runners; the patch must tolerate that.
    """
    _django_patches.apply()
    _django_patches.apply()  # second call should be a self-healing no-op
    assert _django_patches._patch_is_installed() is True


def test_apply_reinstalls_when_class_attribute_reverted():
    """``apply()`` re-installs the patch if a third party reverted the
    class attribute between calls.

    Pins the strengthened "re-entrant calls are no-ops; the patch
    re-installs if not currently present" contract on ``apply()``.
    Without this, a misbehaving test that swapped
    ``SimpleTestCase._remove_databases_failures`` without restoring
    would leave the class permanently in the unpatched state for the
    rest of the process — and the next ``apply()`` call would silently
    decline to re-install.
    """
    _django_patches.apply()
    assert _django_patches._patch_is_installed() is True

    # Capture the classmethod descriptor via ``__dict__`` (assigning a
    # bound method back via the attribute would replace the descriptor
    # with a regular function and break later tests).
    saved = SimpleTestCase.__dict__["_remove_databases_failures"]
    try:

        def _foreign(cls):
            pass

        SimpleTestCase._remove_databases_failures = classmethod(_foreign)
        assert _django_patches._patch_is_installed() is False

        _django_patches.apply()
        assert _django_patches._patch_is_installed() is True
    finally:
        SimpleTestCase._remove_databases_failures = saved


def test_patch_is_installed_on_simple_test_case():
    """``SimpleTestCase._remove_databases_failures`` is the patched
    version after :func:`apply` runs.

    Django defines the method on ``SimpleTestCase`` (not on
    ``TransactionTestCase``), so the patch is installed there. By the
    time pytest starts collecting, the patched version should already
    be in place via ``AppConfig.ready()``.
    """
    assert (
        SimpleTestCase._remove_databases_failures.__func__
        is _django_patches._patched_remove_databases_failures
    )


def test_patch_is_inherited_by_transaction_test_case():
    """``TransactionTestCase`` inherits ``_remove_databases_failures``
    from ``SimpleTestCase`` — patching the base class covers the
    subclass for free.
    """
    assert (
        TransactionTestCase._remove_databases_failures.__func__
        is _django_patches._patched_remove_databases_failures
    )


def test_patch_is_inherited_by_test_case():
    """``TestCase`` inherits ``_remove_databases_failures`` from
    ``SimpleTestCase`` (via ``TransactionTestCase``) — one patch
    covers the whole Django test-case hierarchy.
    """
    assert TestCase._remove_databases_failures.__func__ is _django_patches._patched_remove_databases_failures


def test_patched_remove_databases_failures_unwraps_a_real_wrapper():
    """Happy path: when ``connection.<method>`` is a genuine
    ``_DatabaseFailure`` instance, the patched method unwraps it
    exactly as Django's upstream version does.

    Builds a ``TransactionTestCase`` subclass whose ``databases``
    allow-list excludes ``default``, wraps
    ``connections["default"].cursor`` with a ``_DatabaseFailure``
    pointing at an original (sentinel) callable, and invokes the
    patched method. The cursor must be restored to the sentinel.
    """

    class _NarrowTest(TransactionTestCase):
        databases = frozenset()  # exclude every alias including default

    connection = connections["default"]
    original_cursor = connection.cursor
    sentinel = mock.sentinel.original_cursor

    wrapper = _database_failure(sentinel)
    connection.cursor = wrapper
    try:
        _NarrowTest._remove_databases_failures()
        # Wrapper unwrapped → method now equals the sentinel.
        assert connection.cursor is sentinel
    finally:
        connection.cursor = original_cursor


def test_patched_remove_databases_failures_skips_non_wrapper_methods():
    """The Trac #37064 fix proper: when ``connection.<method>`` is NOT
    a ``_DatabaseFailure`` instance (something replaced it without
    restoring the wrapper), the patched method leaves it alone instead
    of crashing on ``method.wrapped``.

    This is the load-bearing assertion of the whole patch — without
    the ``isinstance`` guard, the same setup raises
    ``AttributeError: 'function' object has no attribute 'wrapped'``.
    The companion test
    :func:`test_unpatched_remove_databases_failures_crashes_on_non_wrapper`
    pins that the crash IS real at our Django pin.
    """

    class _NarrowTest(TransactionTestCase):
        databases = frozenset()  # exclude every alias including default

    connection = connections["default"]
    original_cursor = connection.cursor

    def _plain_cursor(*args, **kwargs):
        return None  # explicitly not a ``_DatabaseFailure`` wrapper

    connection.cursor = _plain_cursor
    try:
        # Should NOT raise.
        _NarrowTest._remove_databases_failures()
        # And the replacement is left untouched (the patch declines to
        # restore a wrapper it never installed).
        assert connection.cursor is _plain_cursor
    finally:
        connection.cursor = original_cursor


def test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass():
    """Direct ``SimpleTestCase`` subclasses — ``TransactionTestCase``
    is NOT in their MRO — must also get the unwrap-time protection.

    Pins that the patch is installed on ``SimpleTestCase`` itself, not
    only on ``TransactionTestCase``. Without this coverage, the patch
    silently bypasses the simplest kind of Django test class.
    """

    class _NarrowSimpleTest(SimpleTestCase):
        databases = frozenset()  # exclude every alias including default

    # MRO sanity-check the test's premise: ``TransactionTestCase`` is
    # NOT in the inheritance chain.
    assert TransactionTestCase not in _NarrowSimpleTest.__mro__

    connection = connections["default"]
    original_cursor = connection.cursor

    def _plain_cursor(*args, **kwargs):
        return None

    connection.cursor = _plain_cursor
    try:
        # Should NOT raise even though this class only inherits from
        # ``SimpleTestCase``. If the patch were still installed on
        # ``TransactionTestCase``, this call would raise.
        _NarrowSimpleTest._remove_databases_failures()
        assert connection.cursor is _plain_cursor
    finally:
        connection.cursor = original_cursor


def test_unpatched_remove_databases_failures_crashes_on_non_wrapper():
    """Pins that Trac #37064's bug shape IS still in Django at our pin.

    Temporarily reverts ``SimpleTestCase._remove_databases_failures``
    to its upstream (un-patched) form, exercises the same setup as the
    happy-path test above, and asserts that the crash happens. A
    Django upgrade that quietly fixed the bug upstream would make this
    test fail with a different error, signalling that the package's
    patch can be retired.
    """
    # Capture the classmethod descriptor via ``__dict__`` so the
    # ``finally`` restore puts the patch back in its native shape (a
    # ``classmethod`` descriptor on ``SimpleTestCase``).
    patched = SimpleTestCase.__dict__["_remove_databases_failures"]

    def _unpatched(cls):
        """Verbatim copy of Django 5.2.13's upstream method body."""
        for alias in connections:
            if alias in cls.databases:
                continue
            connection = connections[alias]
            for name, _ in cls._disallowed_connection_methods:
                method = getattr(connection, name)
                setattr(connection, name, method.wrapped)

    SimpleTestCase._remove_databases_failures = classmethod(_unpatched)
    try:

        class _NarrowTest(TransactionTestCase):
            databases = frozenset()  # exclude every alias including default

        connection = connections["default"]
        original_cursor = connection.cursor

        def _plain_cursor(*args, **kwargs):
            return None

        connection.cursor = _plain_cursor
        try:
            with pytest.raises(AttributeError, match="wrapped"):
                _NarrowTest._remove_databases_failures()
        finally:
            connection.cursor = original_cursor
    finally:
        SimpleTestCase._remove_databases_failures = patched


def test_apply_no_ops_when_database_failure_symbol_missing(caplog):
    """When Django renamed/removed ``_DatabaseFailure``, ``apply()``
    must log a single ``INFO`` notice and return without touching
    ``SimpleTestCase``.

    Pins the defensive-import branch: the package must remain loadable
    even if a future Django release drops the private symbol the patch
    depends on. The patch itself silently retires; the rest of the
    package is unaffected.
    """
    # The classmethod descriptor that ``apply()`` would normally
    # install on. Capture via ``__dict__`` so identity comparison after
    # ``apply()`` returns is stable (``Class.method`` rebuilds the
    # bound-method object on each access).
    saved = SimpleTestCase.__dict__["_remove_databases_failures"]

    with mock.patch.object(_django_patches, "_DatabaseFailure", None):
        with caplog.at_level("INFO", logger="django_strawberry_framework"):
            _django_patches.apply()

        # ``apply()`` returned without touching ``SimpleTestCase``.
        assert SimpleTestCase.__dict__["_remove_databases_failures"] is saved
        # ...and logged a single notice about the skip.
        skip_records = [
            r
            for r in caplog.records
            if r.name == "django_strawberry_framework" and "_DatabaseFailure" in r.message
        ]
        assert len(skip_records) == 1
        assert skip_records[0].levelname == "INFO"
