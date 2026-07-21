"""Transport classification, session pre-check, scope lock, and capability tests.

Commit 1 of the auth session-lifecycle hardening plan introduces the private
``auth/sessions.py`` transport boundary. These are pure-unit tests over
fabricated request / scope shapes (no ``create_users`` / ``seed_data`` seeding is
needed -- no user rows are touched): they pin the ``isinstance``-first
classification, the actionable missing-session error, the per-scope
``asyncio.Lock`` acquisition helper (including the immutable-scope rejection a
real ASGI ``dict`` scope can never reach), the signed-cookie session-engine
detection, and the login/logout capability answers the later stages gate on. The
channels-absent classification path is proved with the shared ``sys.modules``
None-sentinel discipline (``tests/_soft_dependency.py``), mirroring the router
soft-dependency suite, and a subprocess proves importing the auth submodule stays
channels-free.
"""

from __future__ import annotations

import asyncio
import contextlib
import subprocess
import sys
import types
from pathlib import Path
from types import MappingProxyType

import pytest
from django.contrib.sessions.backends.signed_cookies import (
    SessionStore as SignedCookieSessionStore,
)
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, override_settings

import django_strawberry_framework.auth as auth_pkg
from django_strawberry_framework.auth.sessions import (
    _SCOPE_LOCK_KEY,
    Transport,
    classify_transport,
    login_supported,
    logout_supported,
    require_session,
    scope_session_lock,
    uses_signed_cookie_sessions,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.permissions import ChannelsRequestAdapter
from tests._soft_dependency import simulated_absence
from tests.auth._helpers import _drain_until

_SIGNED_COOKIES_ENGINE = "django.contrib.sessions.backends.signed_cookies"


def _adapter(scope):
    """Wrap a fabricated scope in a ChannelsRequestAdapter with a stub wrapped request."""
    return ChannelsRequestAdapter(object(), scope)


# ---------------------------------------------------------------------------
# classify_transport -- isinstance-first, scope["type"]-second
# ---------------------------------------------------------------------------


def test_classify_django_httprequest_takes_the_native_path():
    request = RequestFactory().post("/graphql/")
    assert classify_transport(request) is Transport.DJANGO_HTTP


def test_classify_channels_http_scope():
    assert classify_transport(_adapter({"type": "http"})) is Transport.CHANNELS_HTTP


def test_classify_channels_websocket_scope():
    assert classify_transport(_adapter({"type": "websocket"})) is Transport.CHANNELS_WEBSOCKET


@pytest.mark.parametrize("scope_type", [None, "lifespan", "sse"])
def test_classify_rejects_missing_or_unknown_scope_type(scope_type):
    scope = {} if scope_type is None else {"type": scope_type}
    with pytest.raises(ConfigurationError, match="unsupported `type`"):
        classify_transport(_adapter(scope))


def test_classify_rejects_an_unknown_transport_object():
    with pytest.raises(ConfigurationError, match="could not classify the request transport"):
        classify_transport(object())


# ---------------------------------------------------------------------------
# classify_transport -- channels-absent raises the install hint (soft-dep)
# ---------------------------------------------------------------------------


def test_classify_channels_scope_without_channels_raises_the_install_hint():
    """A Channels-shaped context without the soft dependency is a loud install hint."""
    with simulated_absence(
        "channels",
        "django_strawberry_framework.auth.sessions",
        parent=auth_pkg,
        attr="sessions",
    ):
        # Re-import under absence so the classification re-runs its lazy guard.
        from django_strawberry_framework.auth import sessions as reloaded

        with pytest.raises(ImportError, match="channels>=4.3.2") as exc_info:
            reloaded.classify_transport(_adapter({"type": "http"}))
        assert isinstance(exc_info.value.__cause__, ImportError)


def test_auth_submodule_import_stays_channels_free():
    """Importing ``django_strawberry_framework.auth`` + ``.auth.sessions`` never imports channels.

    Subprocess-based so the assertion is deterministic regardless of what modules
    the running worker already imported (the router suite imports channels at
    module import time in this same process).
    """
    fakeshop = Path(__file__).resolve().parents[2] / "examples" / "fakeshop"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import django, os, sys; "
                f"sys.path.insert(0, {str(fakeshop)!r}); "
                "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); "
                "django.setup(); "
                "import django_strawberry_framework.auth; "
                "import django_strawberry_framework.auth.sessions; "
                "assert 'channels' not in sys.modules, sorted(sys.modules)"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"subprocess failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# require_session -- actionable missing-middleware error keeps "session"
# ---------------------------------------------------------------------------


def test_require_session_returns_the_present_django_session():
    request = RequestFactory().post("/graphql/")
    SessionMiddleware(lambda _r: None).process_request(request)
    assert require_session(request, Transport.DJANGO_HTTP) is request.session


def test_require_session_missing_django_middleware_raises_with_the_session_substring():
    request = RequestFactory().post("/graphql/")  # no SessionMiddleware ran
    with pytest.raises(ConfigurationError, match="session") as exc_info:
        require_session(request, Transport.DJANGO_HTTP)
    assert "session" in str(exc_info.value).lower()


def test_require_session_none_channels_session_raises():
    adapter = _adapter({"type": "websocket"})  # no ``session`` key -> adapter.session is None
    with pytest.raises(ConfigurationError, match="session"):
        require_session(adapter, Transport.CHANNELS_WEBSOCKET)


def test_require_session_returns_the_present_channels_session():
    session = object()
    adapter = _adapter({"type": "http", "session": session})
    assert require_session(adapter, Transport.CHANNELS_HTTP) is session


# ---------------------------------------------------------------------------
# scope_session_lock -- lazy per-scope asyncio.Lock, one acquisition helper
# ---------------------------------------------------------------------------


async def test_scope_lock_is_lazily_created_and_reused_per_scope():
    scope = {"type": "websocket"}
    adapter = _adapter(scope)
    async with scope_session_lock(adapter) as first:
        assert first.locked()
    # Deliberately spelled as the raw literal (not ``_SCOPE_LOCK_KEY``): this one
    # site pins the public scope-key bytes so a rename of the constant cannot
    # silently change the string stored on the consumer's scope.
    stored = scope["__django_strawberry_framework_auth_session_lock__"]
    assert stored is first
    async with scope_session_lock(adapter) as second:
        assert second is stored  # same scope -> same lock object


async def test_scope_lock_serializes_two_operations_on_one_scope():
    """Two coroutines on one scope are mutually excluded: B cannot enter while A holds.

    Deterministic and single-loop -- no wall-clock sleeps and no reliance on a
    particular ready-queue ordering. Task A acquires the per-scope lock and parks
    at an event barrier. Task B, released only after A holds, blocks on the SAME
    scope-owned lock (``await a_holds.wait()`` guarantees the store already holds
    A's lock, so B contends for it rather than minting its own). The main coroutine
    then advances the loop with ``_drain_until`` until B is provably parked inside
    ``scope_session_lock``'s acquire -- i.e. a waiter is enqueued on the lock --
    before asserting B has not entered. This makes the "B is blocked" barrier a
    fact about the lock's own waiter queue instead of an assumption about when B
    was scheduled, so the proof cannot race under a different loop implementation.
    Releasing A must then let B acquire the same lock and run its body.

    Every task is torn down in ``finally`` so a failure anywhere in the body can
    never leave an orphaned pending task to be destroyed at loop teardown (which,
    under the suite's ``-W error`` policy, would surface as a ``RuntimeWarning``
    misattributed to a later test).
    """
    scope = {"type": "websocket"}
    adapter = _adapter(scope)

    a_holds = asyncio.Event()
    a_may_release = asyncio.Event()
    b_entered = {"value": False}

    async def task_a():
        async with scope_session_lock(adapter):
            a_holds.set()
            await a_may_release.wait()

    async def task_b():
        await a_holds.wait()
        async with scope_session_lock(adapter):
            b_entered["value"] = True

    ta = asyncio.create_task(task_a())
    tb = asyncio.create_task(task_b())
    try:
        await a_holds.wait()
        lock = scope[_SCOPE_LOCK_KEY]
        # Advance the loop until B is genuinely parked on the shared lock: a
        # contended ``acquire`` enqueues a waiter on ``lock._waiters``. Only then is
        # "B is blocked behind A" an established fact rather than a timing guess.
        await _drain_until(lambda: bool(getattr(lock, "_waiters", None)))

        # A holds the one scope-owned lock; B is provably blocked behind it.
        assert lock.locked()
        assert b_entered["value"] is False

        a_may_release.set()
        await asyncio.gather(ta, tb)
        # With A released, B was able to acquire the same lock and run its body.
        assert b_entered["value"] is True
        assert not lock.locked()
    finally:
        for task in (ta, tb):
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task


async def test_scope_lock_rejects_an_immutable_scope_loudly():
    """A read-only mapping scope is a loud error, never a silent unserialized path."""
    adapter = _adapter(MappingProxyType({"type": "websocket"}))
    with pytest.raises(ConfigurationError, match="mutable Channels scope"):
        async with scope_session_lock(adapter):
            pass  # pragma: no cover - the __aenter__ raise never reaches the body


# ---------------------------------------------------------------------------
# Session-engine capability answers
# ---------------------------------------------------------------------------


def test_uses_signed_cookie_sessions_is_false_for_the_default_engine():
    assert uses_signed_cookie_sessions() is False


@override_settings(SESSION_ENGINE=_SIGNED_COOKIES_ENGINE)
def test_uses_signed_cookie_sessions_true_under_the_signed_cookie_engine():
    assert uses_signed_cookie_sessions() is True


def test_signed_cookie_detection_follows_a_subclassed_engine():
    """A deployment subclassing the signed-cookie engine shares its no-record limit.

    ``uses_signed_cookie_sessions`` resolves the engine's ``SessionStore`` and tests
    it with ``issubclass``, so a custom engine whose store subclasses the signed-
    cookie store is recognized (and its WebSocket logout is therefore unsupported).
    The stub engine module is registered in ``sys.modules`` for ``import_string`` to
    resolve, then removed so no global state leaks.
    """
    module_name = "tests.auth._stub_signed_cookie_engine"
    module = types.ModuleType(module_name)

    class SessionStore(SignedCookieSessionStore):
        pass

    module.SessionStore = SessionStore
    sys.modules[module_name] = module
    try:
        with override_settings(SESSION_ENGINE=module_name):
            assert uses_signed_cookie_sessions() is True
            assert logout_supported(Transport.CHANNELS_WEBSOCKET) is False
    finally:
        del sys.modules[module_name]


def test_login_supported_everywhere_except_websocket():
    assert login_supported(Transport.DJANGO_HTTP) is True
    assert login_supported(Transport.CHANNELS_HTTP) is True
    assert login_supported(Transport.CHANNELS_WEBSOCKET) is False


def test_logout_supported_except_signed_cookie_websocket():
    assert logout_supported(Transport.DJANGO_HTTP) is True
    assert logout_supported(Transport.CHANNELS_HTTP) is True
    # Server-side engine (the default): a WebSocket logout is supportable.
    assert logout_supported(Transport.CHANNELS_WEBSOCKET) is True


@override_settings(SESSION_ENGINE=_SIGNED_COOKIES_ENGINE)
def test_logout_unsupported_on_a_signed_cookie_websocket():
    assert logout_supported(Transport.CHANNELS_WEBSOCKET) is False
    # A signed-cookie engine does not change the non-WebSocket answers.
    assert logout_supported(Transport.CHANNELS_HTTP) is True


# ---------------------------------------------------------------------------
# Lock lifecycle: cancellation release, scope-ownership, no global registry
# (auth session-lifecycle hardening, Commit 5)
# ---------------------------------------------------------------------------


async def test_cancelling_a_task_holding_the_scope_lock_releases_it():
    """Cancelling a task parked mid-critical-section releases the lock; the next op proceeds.

    The ``async with scope_session_lock`` block unwinds on ``CancelledError``, so a
    cancelled holder can never orphan a held lock. A subsequent acquisition on the
    same scope acquires the same lock object immediately.
    """
    scope = {"type": "websocket"}
    adapter = _adapter(scope)
    holding = asyncio.Event()
    never = asyncio.Event()  # deliberately never set: the holder parks until cancelled

    async def holder():
        async with scope_session_lock(adapter):
            holding.set()
            await never.wait()

    task = asyncio.create_task(holder())
    try:
        await holding.wait()
        lock = scope[_SCOPE_LOCK_KEY]
        assert lock.locked()

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not lock.locked()  # cancellation unwound the async-with release

        # No orphaned held lock: a subsequent operation proceeds on the same lock.
        async with scope_session_lock(adapter) as again:
            assert again is lock
            assert again.locked()
        assert not lock.locked()
    finally:
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


async def test_cancelling_a_task_waiting_on_the_scope_lock_leaves_it_acquirable():
    """Cancelling a task parked on the lock's waiter queue leaves the lock healthy.

    Task A holds the scope lock; task B blocks acquiring the same lock. B is
    cancelled while parked on the waiter queue, then A releases. A fresh operation
    must still acquire the lock -- a cancelled waiter leaves no wedged state.
    """
    scope = {"type": "websocket"}
    adapter = _adapter(scope)
    a_holds = asyncio.Event()
    a_may_release = asyncio.Event()

    async def task_a():
        async with scope_session_lock(adapter):
            a_holds.set()
            await a_may_release.wait()

    async def task_b():
        async with scope_session_lock(adapter):
            pass  # pragma: no cover - B is cancelled before it ever acquires

    ta = asyncio.create_task(task_a())
    tb = asyncio.create_task(task_b())
    try:
        await a_holds.wait()
        lock = scope[_SCOPE_LOCK_KEY]
        await _drain_until(lambda: bool(getattr(lock, "_waiters", None)))

        tb.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tb

        a_may_release.set()
        await ta
        assert not lock.locked()

        # The lock survived the cancelled waiter: a fresh operation acquires it.
        async with scope_session_lock(adapter) as again:
            assert again is lock
            assert again.locked()
    finally:
        for task in (ta, tb):
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task


async def test_locks_are_scope_owned_and_independent_across_scopes():
    """Two different scopes have independent locks: no cross-scope serialization.

    Holding scope 1's lock does not block acquiring scope 2's lock -- they are
    distinct objects, each owned by its own scope dict, so unrelated Channels
    connections never serialize against each other.
    """
    scope1 = {"type": "websocket"}
    scope2 = {"type": "websocket"}
    adapter1 = _adapter(scope1)
    adapter2 = _adapter(scope2)

    async with scope_session_lock(adapter1) as lock1:
        # Acquiring scope 2's lock while scope 1's is held proves independence.
        async with scope_session_lock(adapter2) as lock2:
            assert lock1 is not lock2
            assert lock1.locked()
            assert lock2.locked()
    assert scope1[_SCOPE_LOCK_KEY] is lock1
    assert scope2[_SCOPE_LOCK_KEY] is lock2


def test_no_process_global_lock_registry_in_the_sessions_module():
    """Security invariant 12: the lock lives only in the scope dict, no global registry.

    A code-shape assertion over the module namespace: there is no module-level
    ``ContextVar``, no ``dict`` / ``WeakKeyDictionary`` / ``WeakValueDictionary``
    that could serve as a process-global scope->lock registry, and no module-level
    ``asyncio.Lock`` itself. The only storage for a scope's lock is the scope
    mapping under ``_SCOPE_LOCK_KEY`` (proved by
    ``test_scope_lock_is_lazily_created_and_reused_per_scope``).
    """
    import contextvars
    import weakref

    from django_strawberry_framework.auth import sessions as sessions_mod

    forbidden = (
        dict,
        contextvars.ContextVar,
        weakref.WeakKeyDictionary,
        weakref.WeakValueDictionary,
        asyncio.Lock,
    )
    offenders = [
        name
        for name, value in vars(sessions_mod).items()
        if not name.startswith("__") and isinstance(value, forbidden)
    ]
    assert offenders == [], f"unexpected process-global lock storage: {offenders}"
