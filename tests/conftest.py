"""Shared pytest fixtures and test-suite instrumentation.

Closing the SQLite connections async tests leak
================================================
Async tests drive Django's ORM two ways: through ``sync_to_async`` (``afirst``
and friends, which run in asgiref's thread-sensitive executor thread) and - in
the tests that set ``DJANGO_ALLOW_ASYNC_UNSAFE`` - through *synchronous* ORM
calls made on the main thread while the event loop is running.

Django keeps its connections in an asgiref ``Local(thread_critical=True)``. On a
thread that has a running event loop that ``Local`` stores data in a contextvar
(so it is local to the current asyncio task); on a thread with no loop it is a
plain ``threading.local`` (shared and reused within that thread). A connection
opened by main-thread sync ORM *during* an async test therefore lands in the
test task's contextvar context. When the task ends, that context - and the only
reference to the connection - becomes unreachable while the underlying
``sqlite3.Connection`` is still open. The GC later finalizes it, CPython emits
``ResourceWarning: unclosed database``, and pytest's unraisable-exception hook
re-raises it; under this suite's ``-W error`` policy that is a hard ERROR,
attributed nondeterministically to whichever test happens to be running when the
GC fires - hence "a different async test errors each run, only in the full
suite". (pytest-django's own teardown runs on the main thread with no loop, so
it only ever sees the plain thread-local connection, never the context-local
one.)

Neither pytest-django nor an ``async`` fixture can reach these connections: an
async fixture's teardown runs in a *different* contextvar context than the test
body, so ``connections.close_all()`` there closes nothing. The only reliable way
to close them is to hold a direct reference to each raw connection and close it
from a sync fixture, whose teardown always runs. That is what the wrapper and
fixture below do - closing the unclosed connection at its source rather than
relaxing ``-W error`` or filtering the warning.
"""

import asyncio
import contextlib

import pytest
from django.db.backends.sqlite3 import base as sqlite_base

# Raw ``sqlite3.Connection`` handles opened while an event loop was running -
# i.e. the context-local, per-asyncio-task connections that nothing else will
# reuse or close. Connections opened with no running loop go to plain
# thread-local storage, are reused within the thread, and are closed by
# pytest-django, so we never track (or touch) those. Appends only ever happen on
# the main thread - the only thread that runs the event loop - so plain list
# access is race-free here.
_context_local_connections = []

_original_get_new_connection = sqlite_base.DatabaseWrapper.get_new_connection


def _tracking_get_new_connection(self, conn_params):
    """Register connections opened under a running loop, then delegate."""
    connection = _original_get_new_connection(self, conn_params)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass  # no running loop -> plain thread-local connection, left untouched
    else:
        _context_local_connections.append(connection)
    return connection


sqlite_base.DatabaseWrapper.get_new_connection = _tracking_get_new_connection


@pytest.fixture(autouse=True)
def _close_context_local_db_connections():
    """Close per-task SQLite connections an async test left open.

    Runs as a *sync* fixture so its teardown always executes (an ``async``
    fixture's teardown runs in a different contextvar context and could not see
    these connections anyway). By teardown the owning asyncio task is gone, so
    the connection will never be reused - closing the raw handle here simply
    pre-empts the GC finalizer that would otherwise trip ``ResourceWarning``.
    """
    yield
    while _context_local_connections:
        connection = _context_local_connections.pop()
        with contextlib.suppress(Exception):
            connection.close()
