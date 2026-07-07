"""Repo-root pytest hooks shared by every test tree in ``testpaths``.

Owns two Postgres-tier concerns (both repo-root because ``pg`` behavior
spans all three test trees - ``tests/``, ``examples/fakeshop/test_query/``,
per-app ``examples/fakeshop/apps/*/tests/`` - and ``tests/conftest.py``
only covers the first):

1. The ``pg`` marker (registered in ``pytest.ini``): Postgres-only tests -
   vendor-specific SQL such as the LATERAL-join nested-fetch strategy -
   are auto-skipped unless the suite runs against Postgres (the
   ``FAKESHOP_PG_DSN`` settings branch in
   ``examples/fakeshop/config/settings.py``; the ``test-postgres`` CI job).

2. Stray-connection tracking for the Postgres tier. Async tests open ORM
   connections in asgiref's thread-sensitive executor threads and (under
   ``DJANGO_ALLOW_ASYNC_UNSAFE``) in per-asyncio-task contextvar contexts.
   pytest-django's teardown runs ``connections.close_all()`` on the MAIN
   thread only, so those handles stay open for the life of the worker - on
   SQLite that surfaces as the ``ResourceWarning`` handled per-test in
   ``tests/conftest.py``; on Postgres it holds the per-worker test database
   open and xdist teardown intermittently fails with ``DROP DATABASE
   test_fakeshop_gwN ... is being accessed by other users``. The tracking
   here mirrors the SQLite wrapper but closes at SESSION teardown (executor
   threads legitimately REUSE their thread-local connection across tests,
   so per-test closing would break the live wrapper), ordered BEFORE
   pytest-django drops the databases via the ``django_db_setup``
   dependency. Backend modules stay separate: this touches only
   ``django.db.backends.postgresql``.
"""

import asyncio
import contextlib
import threading
from typing import Any

import pytest

#: Raw psycopg connections opened from an executor thread or under a running
#: event loop - the handles main-thread ``close_all()`` can never reach.
#: ``list.append`` is GIL-atomic, so cross-thread appends need no lock; the
#: drain runs single-threaded at session teardown.
_stray_postgres_connections: list = []


def _opened_outside_main_thread_sync_context() -> bool:
    """True when the caller cannot be closed by main-thread teardown."""
    if threading.current_thread() is not threading.main_thread():
        return True
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    return True


def _install_postgres_connection_tracking() -> None:
    """Wrap the Postgres backend's connection factory with stray tracking."""
    try:
        from django.db.backends.postgresql import base as postgres_base
    except ImportError:  # psycopg absent: the sqlite-only coverage tier.
        return
    original = postgres_base.DatabaseWrapper.get_new_connection
    if getattr(original, "_dst_tracks_stray_connections", False):
        return  # already installed (defensive against double import).

    def _tracking_get_new_connection(self: Any, conn_params: Any) -> Any:
        connection = original(self, conn_params)
        if _opened_outside_main_thread_sync_context():
            _stray_postgres_connections.append(connection)
        return connection

    _tracking_get_new_connection._dst_tracks_stray_connections = True
    postgres_base.DatabaseWrapper.get_new_connection = _tracking_get_new_connection
    # Anchor the registry on the backend module so pg-tier tests can assert
    # tracking without importing this conftest by module path.
    postgres_base._dst_stray_connection_registry = _stray_postgres_connections


_install_postgres_connection_tracking()


@pytest.fixture(autouse=True, scope="session")
def _close_stray_postgres_connections(django_db_setup: Any) -> Any:  # noqa: ARG001 - ordering dependency
    """Close tracked stray Postgres connections before the test DBs drop.

    Depending on ``django_db_setup`` orders this fixture's teardown BEFORE
    pytest-django's database teardown (finalizers run in reverse setup
    order), so every executor-thread / task-context connection is closed
    before ``DROP DATABASE`` needs the database free. Already-closed or
    still-wrapped handles close idempotently; errors are irrelevant by this
    point and suppressed.
    """
    yield
    while _stray_postgres_connections:
        stray = _stray_postgres_connections.pop()
        with contextlib.suppress(Exception):
            stray.close()


def pytest_collection_modifyitems(config: Any, items: list) -> None:  # noqa: ARG001 - pytest hookspec
    """Skip ``pg``-marked tests when the default DB vendor is not Postgres.

    ``connection.vendor`` is a static attribute of the configured backend -
    reading it opens no database connection, so this is safe at collection
    time under pytest-django (Django is already set up by then).
    """
    from django.db import connection

    if connection.vendor == "postgresql":
        return
    skip_pg = pytest.mark.skip(reason="requires the Postgres tier (FAKESHOP_PG_DSN)")
    for item in items:
        if "pg" in item.keywords:
            item.add_marker(skip_pg)
