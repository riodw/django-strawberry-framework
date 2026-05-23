"""Tests for ``django_strawberry_framework.test._wrap``.

System-under-test:
:func:`django_strawberry_framework.test.safe_wrap_connection_method` —
the wrap-time half of the package's Django Trac #37064 defense-in-depth
(the unwrap-time half lives in :mod:`django_strawberry_framework._django_patches`
and is tested in ``tests/test_django_patches.py``).

These tests don't require ``FAKESHOP_SHARDED=1``; the helper operates
on any Django connection, and the `default` alias is always present.
"""

from unittest import mock

from django.db import connections
from django.test.testcases import _DatabaseFailure

from django_strawberry_framework.test import safe_wrap_connection_method


def test_safe_wrap_connection_method_installs_wrapper_when_no_database_failure():
    """Happy path: when ``connection.<method>`` is NOT a ``_DatabaseFailure``,
    the helper installs the consumer's wrapper.
    """
    connection = connections["default"]
    original_cursor = connection.cursor

    sentinel_wrapper = mock.sentinel.consumer_wrapper

    try:
        installed = safe_wrap_connection_method(connection, "cursor", sentinel_wrapper)

        assert installed is True
        assert connection.cursor is sentinel_wrapper
    finally:
        connection.cursor = original_cursor


def test_safe_wrap_connection_method_declines_when_database_failure_in_place():
    """The Trac #37064 cooperative-wrap mirror: when Django has already
    installed ``_DatabaseFailure`` at the method, the helper refuses
    to clobber it and returns ``False``.
    """
    connection = connections["default"]
    original_cursor = connection.cursor

    django_wrapper = _DatabaseFailure(original_cursor, "test message")
    connection.cursor = django_wrapper

    sentinel_wrapper = mock.sentinel.consumer_wrapper

    try:
        installed = safe_wrap_connection_method(connection, "cursor", sentinel_wrapper)

        assert installed is False
        # Django's wrapper was NOT replaced.
        assert connection.cursor is django_wrapper
    finally:
        connection.cursor = original_cursor


def test_safe_wrap_connection_method_works_on_arbitrary_method_names():
    """Helper works for any disallowed-connection method, not just
    ``cursor``. Pinned so the helper doesn't accidentally become
    cursor-specific over time.
    """
    connection = connections["default"]
    original = connection.chunked_cursor

    sentinel_wrapper = mock.sentinel.chunked_wrapper

    try:
        installed = safe_wrap_connection_method(
            connection,
            "chunked_cursor",
            sentinel_wrapper,
        )

        assert installed is True
        assert connection.chunked_cursor is sentinel_wrapper
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
    django_wrapper = _DatabaseFailure(sentinel_original, "test message")
    connection.cursor = django_wrapper

    # The consumer attempts to wrap and is correctly declined — Django
    # already wrapped first. Wrap-time half of defense-in-depth fires.
    installed = safe_wrap_connection_method(
        connection,
        "cursor",
        mock.sentinel.consumer_wrapper,
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
