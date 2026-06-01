"""Tests for ``django_strawberry_framework.testing._wrap``.

System-under-test:
:func:`django_strawberry_framework.testing.safe_wrap_connection_method` —
the wrap-time half of the package's Django Trac #37064 defense-in-depth
(the unwrap-time half lives in :mod:`django_strawberry_framework._django_patches`
and is tested in ``tests/test_django_patches.py``).

These tests don't require ``FAKESHOP_SHARDED=1``; the helper operates
on any Django connection, and the `default` alias is always present.
"""

from unittest import mock

import pytest
from django.db import connections

from django_strawberry_framework import _django_patches
from django_strawberry_framework.testing import safe_wrap_connection_method


def _database_failure(wrapped):
    if _django_patches._DatabaseFailure is None:
        pytest.skip("Django private _DatabaseFailure symbol is unavailable.")
    return _django_patches._DatabaseFailure(wrapped, "test message")


def test_safe_wrap_connection_method_installs_wrapper_when_no_database_failure():
    """Happy path: when ``connection.<method>`` is NOT a ``_DatabaseFailure``,
    the helper installs the consumer's wrapper.
    """
    connection = connections["default"]
    original_cursor = connection.cursor

    consumer_wrapper = mock.Mock(name="consumer_wrapper")

    try:
        installed = safe_wrap_connection_method(connection, "cursor", consumer_wrapper)

        assert installed is True
        assert connection.cursor is consumer_wrapper
    finally:
        connection.cursor = original_cursor


def test_safe_wrap_connection_method_declines_when_database_failure_in_place():
    """The Trac #37064 cooperative-wrap mirror: when Django has already
    installed ``_DatabaseFailure`` at the method, the helper refuses
    to clobber it and returns ``False``.
    """
    connection = connections["default"]
    original_cursor = connection.cursor

    django_wrapper = _database_failure(original_cursor)
    connection.cursor = django_wrapper

    consumer_wrapper = mock.Mock(name="consumer_wrapper")

    try:
        installed = safe_wrap_connection_method(connection, "cursor", consumer_wrapper)

        assert installed is False
        # Django's wrapper was NOT replaced.
        assert connection.cursor is django_wrapper
    finally:
        connection.cursor = original_cursor


def test_safe_wrap_connection_method_installs_when_database_failure_symbol_missing():
    """Future-Django private-symbol drift must not break the public test helper.

    ``_DatabaseFailure`` is a private Django symbol. If Django renames
    or removes it, ``safe_wrap_connection_method`` should still be
    importable and should behave like the normal "no Django wrapper is
    visible" path.
    """
    connection = connections["default"]
    original_cursor = connection.cursor

    consumer_wrapper = mock.Mock(name="consumer_wrapper")

    try:
        with mock.patch.object(_django_patches, "_DatabaseFailure", None):
            installed = safe_wrap_connection_method(connection, "cursor", consumer_wrapper)

        assert installed is True
        assert connection.cursor is consumer_wrapper
    finally:
        connection.cursor = original_cursor


def test_safe_wrap_connection_method_works_on_arbitrary_method_names():
    """Helper works for any disallowed-connection method, not just
    ``cursor``. Pinned so the helper doesn't accidentally become
    cursor-specific over time.
    """
    connection = connections["default"]
    original = connection.chunked_cursor

    chunked_wrapper = mock.Mock(name="chunked_wrapper")

    try:
        installed = safe_wrap_connection_method(
            connection,
            "chunked_cursor",
            chunked_wrapper,
        )

        assert installed is True
        assert connection.chunked_cursor is chunked_wrapper
    finally:
        connection.chunked_cursor = original


def test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth():
    """End-to-end composition: when a consumer uses
    :func:`safe_wrap_connection_method` AND Django's setup/teardown
    pair runs, the package's unwrap-time patch
    (:func:`_django_patches._patched_remove_databases_failures`)
    restores the wrapper without any work from the consumer.

    The test wires up the full sequence: install a ``_DatabaseFailure``
    on the connection (simulating ``_add_databases_failures``), have
    the consumer call ``safe_wrap_connection_method`` (which declines
    because the ``_DatabaseFailure`` is in place), then exercise the
    package's patched teardown method. The wrapper is unwrapped
    exactly as upstream would do — proving the two halves compose.
    """
    from django.test.testcases import TransactionTestCase

    connection = connections["default"]
    original_cursor = connection.cursor

    sentinel_original = mock.sentinel.untouched_original

    # Simulate Django's setUpClass installing the ``_DatabaseFailure``.
    django_wrapper = _database_failure(sentinel_original)
    connection.cursor = django_wrapper

    # The consumer attempts to wrap and is correctly declined — Django
    # already wrapped first. Wrap-time half of defense-in-depth fires.
    installed = safe_wrap_connection_method(
        connection,
        "cursor",
        mock.Mock(name="consumer_wrapper"),
    )
    assert installed is False
    assert connection.cursor is django_wrapper  # Django's wrapper intact

    # Now exercise the package's patched ``_remove_databases_failures``
    # (the unwrap-time half) against a synthetic narrow-allow-list
    # test class. Should restore the original cursor cleanly.
    class _NarrowTest(TransactionTestCase):
        databases = frozenset()  # exclude every alias including default

    try:
        _NarrowTest._remove_databases_failures()
        # Wrapper unwrapped to the sentinel original.
        assert connection.cursor is sentinel_original
    finally:
        connection.cursor = original_cursor


def test_safe_wrap_connection_method_raises_on_non_callable_wrapper():
    """Wrap-time guard: a non-callable ``wrapper`` raises ``TypeError``
    at the wrap site instead of installing silently and failing at the
    next ``connection.<method>()`` invocation.

    Pins the wrap-time-vs-call-time silent-failure mode closed: the
    type annotation ``Callable[..., Any]`` is now enforced at runtime,
    so a typo (e.g. ``connection.cursor()`` — a cursor object, not
    callable — accidentally passed instead of
    ``lambda: connection.cursor()``) surfaces at the wrap site with a
    traceback pointing at the consumer's call.
    """
    connection = connections["default"]
    original_cursor = connection.cursor

    try:
        with pytest.raises(TypeError, match="non-callable wrapper"):
            safe_wrap_connection_method(connection, "cursor", 42)

        # Connection method untouched — the early-validate raise must
        # not mutate connection state before raising.
        assert connection.cursor is original_cursor
    finally:
        connection.cursor = original_cursor
