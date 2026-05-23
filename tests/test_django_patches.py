"""Tests for the package's Django defensive patches.

System-under-test: :mod:`django_strawberry_framework._django_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

The currently-shipped patch hardens
``TransactionTestCase._remove_databases_failures`` against
Django Trac #37064 (closed upstream as ``wontfix``):
<https://code.djangoproject.com/ticket/37064>. Without the patch, any
code path that replaces a connection method between ``setUpClass`` and
``tearDownClass`` crashes the cleanup loop with
``AttributeError: 'function' object has no attribute 'wrapped'``.

These tests do not require ``FAKESHOP_SHARDED=1``; they drive the
patched method directly against synthetic ``TransactionTestCase``
subclasses with hand-built ``databases`` allow-lists. The test
``default`` alias is always present, so a one-alias multi-DB scenario
is enough to exercise both branches of the patched loop. (The
end-to-end demo shape from <https://github.com/riodw/django-remove_databases_failures-demo>
runs under vanilla ``manage.py test`` rather than pytest-django and
cannot be reproduced 1:1 under our test runner — pytest-django's
per-test flush calls ``connection.cursor()`` mid-lifecycle and crashes
on the swapped cursor before reaching ``tearDownClass``. The unit
tests below isolate the bug class from that machinery.)
"""

from unittest import mock

import pytest
from django.db import connections
from django.test.testcases import TransactionTestCase, _DatabaseFailure

from django_strawberry_framework import _django_patches


def test_apply_is_idempotent():
    """Repeated calls to :func:`apply` are no-ops after the first.

    Pins the idempotency contract called out in the module docstring.
    AppConfig.ready() may run more than once under some Django test
    runners; the patch must tolerate that.
    """
    _django_patches.apply()
    _django_patches.apply()  # should be a no-op
    assert _django_patches._PATCH_APPLIED is True


def test_patch_is_installed_on_transaction_test_case():
    """``TransactionTestCase._remove_databases_failures`` is the
    patched version after :func:`apply` runs.

    AppConfig.ready() applies the patch at Django startup; by the time
    pytest starts collecting, the patched version should already be in
    place. This test pins that contract — a future refactor that
    reverts the patch (or fails to install it) breaks this assertion
    loudly.
    """
    assert (
        TransactionTestCase._remove_databases_failures.__func__
        is _django_patches._patched_remove_databases_failures
    )


def test_patch_is_inherited_by_test_case():
    """``TestCase`` inherits ``_remove_databases_failures`` from
    ``TransactionTestCase`` — patching the base class covers the
    subclass for free. Pinned so a future change to Django's class
    hierarchy (or to our patch target) fails loudly.
    """
    from django.test.testcases import TestCase

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

    wrapper = _DatabaseFailure(sentinel, "test message")
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


def test_unpatched_remove_databases_failures_crashes_on_non_wrapper():
    """Pins that Trac #37064's bug shape IS still in Django at our pin.

    Temporarily reverts ``TransactionTestCase._remove_databases_failures``
    to its upstream (un-patched) form, exercises the same setup as the
    happy-path test above, and asserts that the crash happens. A
    Django upgrade that quietly fixed the bug upstream would make this
    test fail with a different error, signalling that the package's
    patch can be retired.
    """
    patched = TransactionTestCase._remove_databases_failures

    def _unpatched(cls):
        """Verbatim copy of Django 5.2.13's upstream method body."""
        for alias in connections:
            if alias in cls.databases:
                continue
            connection = connections[alias]
            for name, _ in cls._disallowed_connection_methods:
                method = getattr(connection, name)
                setattr(connection, name, method.wrapped)

    TransactionTestCase._remove_databases_failures = classmethod(_unpatched)
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
        TransactionTestCase._remove_databases_failures = patched
