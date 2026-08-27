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
import copy
import json
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
        from django.core.exceptions import ImproperlyConfigured
        from django.db.backends.postgresql import base as postgres_base
    except ImportError:
        return
    except ImproperlyConfigured as error:
        if str(error) != "Error loading psycopg2 or psycopg module":
            raise
        # psycopg absent: the sqlite-only coverage tier.
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


# ---------------------------------------------------------------------------
# Interpreter-derived nesting depths for the transport depth guards.
#
# Three test trees drive the same two guards with a pathologically nested
# document, and each one used to carry its own hard-coded depth. Both bounds
# are properties of the RUNNING interpreter, not constants:
#
# * ``json.loads``' scanner is bounded by the C stack. ``sys.setrecursionlimit``
#   does not move it (lowering the limit changes nothing), and the budget varies
#   by platform and interpreter - CPython 3.14 overflows near 74k depth on macOS
#   and tolerates well past 120k on the Linux CI runner.
# * ``copy.deepcopy`` recurses in pure Python, so IT is bounded by
#   ``sys.getrecursionlimit()`` and overflows around depth 500 everywhere.
#
# A hard-coded depth is therefore a document that overflows on whoever tuned it
# and parses cleanly everywhere else - and a depth guard whose input no longer
# overflows is a test that passes without exercising anything. Probe instead,
# once per session, and fail loudly when the interpreter offers no usable depth
# rather than skipping into a silent pass.
# ---------------------------------------------------------------------------

#: Ceiling for both probes. The array text is two bytes per level, so this
#: caps a document at 512 KiB - still under the package's own 1 MiB
#: request-body cap, which the live POST tiers actually hit.
_MAX_NESTING_PROBE_DEPTH = 262_144


def _nested_array_text(depth: int) -> str:
    """A syntactically valid JSON array nested ``depth`` levels deep."""
    return "[" * depth + "]" * depth


def _json_loads_overflow_depth() -> int:
    """The shallowest probed depth whose parse overflows ``json.loads``."""
    depth = 1024
    while depth <= _MAX_NESTING_PROBE_DEPTH:
        try:
            json.loads(_nested_array_text(depth))
        except RecursionError:
            return depth
        depth *= 2
    msg = (
        f"json.loads parsed a {_MAX_NESTING_PROBE_DEPTH}-deep document without "
        "overflowing, so the transport's RecursionError guard cannot be exercised "
        "under a body this interpreter would accept. Raise "
        "_MAX_NESTING_PROBE_DEPTH only if the resulting body still fits the 1 MiB "
        "request-body cap."
    )
    raise RuntimeError(msg)


def _deepcopy_overflow_depth() -> int:
    """The shallowest probed depth whose copy overflows ``copy.deepcopy``."""
    depth = 64
    while depth <= _MAX_NESTING_PROBE_DEPTH:
        nested: list = []
        for _ in range(depth):
            nested = [nested]
        try:
            copy.deepcopy(nested)
        except RecursionError:
            return depth
        depth *= 2
    msg = (
        f"copy.deepcopy walked a {_MAX_NESTING_PROBE_DEPTH}-deep value without "
        "overflowing, so the upload utility's RecursionError guard cannot be "
        "exercised."
    )
    raise RuntimeError(msg)


@pytest.fixture(scope="session")
def pathological_json_text() -> str:
    """A JSON array this interpreter's ``json.loads`` answers with ``RecursionError``.

    The input for the ``parse_json`` / ``parse_query_params`` depth guards: the
    document is syntactically valid, so nothing short of the parser's own stack
    budget rejects it.
    """
    return _nested_array_text(_json_loads_overflow_depth())


@pytest.fixture(scope="session")
def pathological_json_body(pathological_json_text: str) -> bytes:
    """``pathological_json_text`` as request-body bytes for the live tiers."""
    return pathological_json_text.encode()


@pytest.fixture(scope="session")
def deepcopy_overflow_operations_text() -> str:
    """An ``operations`` document ``json.loads`` accepts but ``copy.deepcopy`` cannot walk.

    The multipart guard needs the WINDOW between the two bounds: the envelope
    check must pass the document as a well-typed object, and the upload
    utility's unconditional ``copy.deepcopy`` must then overflow inside its own
    frame. The text is emitted directly rather than through ``json.dumps``
    because the ENCODER recurses too, and on the 3.10 floor - where both it and
    ``copy.deepcopy`` answer to the same ``sys.getrecursionlimit()`` - building
    the fixture overflowed before the test could run.
    """
    depth = _deepcopy_overflow_depth()
    loads_limit = _json_loads_overflow_depth()
    if depth >= loads_limit:
        msg = (
            f"copy.deepcopy overflows at depth {depth} but json.loads already "
            f"overflows at {loads_limit}, so no document can reach the upload "
            "utility intact. The multipart depth guard has no exercisable input "
            "on this interpreter."
        )
        raise RuntimeError(msg)
    text = '{"0": ' + _nested_array_text(depth) + "}"
    # Prove the precondition rather than assume it: the guard under test only
    # matters for a document the envelope check has already accepted.
    json.loads(text)
    return text
