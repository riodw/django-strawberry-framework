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
import inspect

import pytest
from django.db.backends.sqlite3 import base as sqlite_base
from django.test import SimpleTestCase

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


def _django_db_signature(
    transaction=False,
    reset_sequences=False,
    databases=None,
    serialized_rollback=False,
    available_apps=None,
):
    """Bind a ``django_db`` marker's arguments exactly as pytest-django's signature does.

    ``transaction`` and ``reset_sequences`` are the first two positional parameters, so
    ``django_db(True)`` and ``django_db(transaction=True)`` mean the same thing; an argument
    pytest-django would reject raises the same ``TypeError`` here.
    """
    return transaction, reset_sequences


def _uses_db_and_is_transactional(item):
    """Resolve a test's database setup the way pytest-django orders and runs it.

    Returns ``(uses_db, transactional)``. A ``django_db`` marker means database access, and
    it is transactional when ``transaction`` or ``reset_sequences`` is set (pytest-django
    runs a ``reset_sequences`` test as a ``TransactionTestCase``). Independently of any
    marker, requesting ``db`` means database access, and requesting ``transactional_db`` or
    ``live_server`` (directly or through another fixture, so ``django_db_reset_sequences``
    counts) makes the test transactional whatever the marker says.
    """
    marker = item.get_closest_marker("django_db")
    if marker is None:
        uses_db = transactional = False
    else:
        transaction, reset_sequences = _django_db_signature(*marker.args, **marker.kwargs)
        uses_db = True
        transactional = bool(transaction or reset_sequences)
    fixtures = getattr(item, "fixturenames", ())
    transactional = transactional or "transactional_db" in fixtures or "live_server" in fixtures
    uses_db = uses_db or "db" in fixtures
    return uses_db, transactional


def pytest_collection_modifyitems(items):
    """Fail collection for an ``async`` test that uses the database non-transactionally.

    An async test reaches the ORM through ``sync_to_async`` (or Django's ``a*`` methods),
    which run on asgiref's thread-sensitive executor thread. That thread's connection sits
    outside the transaction pytest-django opens on the main thread for a plain ``django_db``
    test or a ``db`` fixture, so rows written there are committed to the shared in-memory
    SQLite database and leak into every later test in the process. A transactional test
    flushes after the test, so the rule is "async + database => transactional". Enforcing it
    at collection makes the failure deterministic and names the offending test, instead of
    surfacing later as a nondeterministic row-count failure in an unrelated module.

    Every offender is collected before raising so one run reports them all. ``asyncio_mode =
    auto`` means async tests carry no explicit asyncio marker, so the coroutine check is the
    only signal; ``get_closest_marker`` covers module-level ``pytestmark`` and lets a
    per-test marker override it. Methods of Django's own test classes are skipped:
    pytest-django ignores ``django_db`` on them, and Django runs an async test method
    through ``async_to_sync``, which keeps its ORM calls on the thread holding the test's
    transaction.
    """
    offenders = []
    for item in items:
        function = getattr(item, "obj", None)
        if function is None or not inspect.iscoroutinefunction(function):
            continue
        test_class = getattr(item, "cls", None)
        if test_class is not None and issubclass(test_class, SimpleTestCase):
            continue
        uses_db, transactional = _uses_db_and_is_transactional(item)
        if uses_db and not transactional:
            offenders.append(item.nodeid)
    if offenders:
        listing = "\n".join(f"  {nodeid}" for nodeid in offenders)
        raise pytest.UsageError(
            "async tests that use the database must be transactional - a plain django_db "
            "marker or db fixture opens its transaction on the main thread and cannot contain "
            "ORM writes made on asgiref's executor thread, so those rows leak into later "
            "tests. Mark @pytest.mark.django_db(transaction=True) (or request "
            "transactional_db) on:\n" + listing,
        )


@pytest.fixture
def isolate_global_registry():
    """Clear the global registry and the connection-type cache around a test.

    The shared test-isolation invariant for modules that declare fresh
    function-scope ``DjangoType`` classes: connection classes are cached on
    ``target_type`` identity, so a discarded class must not leak into a later
    test's identity check (the ``tests/test_connection.py`` fixture shape).
    Opt-in - modules wrap it in their own thin ``autouse=True`` fixture so the
    invariant has ONE implementation without imposing the clears on suites
    that use the shipped fakeshop types.
    """
    from django_strawberry_framework.connection import _connection_type_cache
    from django_strawberry_framework.registry import registry

    registry.clear()
    _connection_type_cache.clear()
    yield
    registry.clear()
    _connection_type_cache.clear()


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
