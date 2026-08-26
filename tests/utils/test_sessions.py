"""Behavioral tests for the session-engine resolver and connection actor lease."""

from __future__ import annotations

import asyncio
import contextlib
import sys
import types

import pytest
from django.contrib.sessions.backends.db import SessionStore as DBSessionStore
from django.contrib.sessions.backends.signed_cookies import (
    SessionStore as SignedCookieSessionStore,
)
from django.test import override_settings

from django_strawberry_framework.utils.sessions import (
    _ACTOR_STATE_SCOPE_KEY,
    ConnectionActorState,
    actor_lease,
    actor_transition,
    connection_actor_state,
    connection_was_authenticated,
    note_authenticated_actor,
    session_store_class,
)
from tests.auth._helpers import _drain_until

# ---------------------------------------------------------------------------
# session_store_class
# ---------------------------------------------------------------------------


def test_session_store_class_resolves_default_engine():
    """Default engine resolves to Django's DB SessionStore."""
    resolved = session_store_class()
    assert resolved is DBSessionStore


@override_settings(SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies")
def test_session_store_class_honors_override_settings():
    """Settings overrides at call time dynamically resolve the new store class."""
    resolved = session_store_class()
    assert resolved is SignedCookieSessionStore


def test_session_store_class_resolves_custom_engine(monkeypatch):
    """A custom session engine resolves identically via import_string."""
    module_name = "tests.utils._stub_custom_session_engine"
    module = types.ModuleType(module_name)

    class CustomSessionStore:
        pass

    module.SessionStore = CustomSessionStore
    monkeypatch.setitem(sys.modules, module_name, module)

    with override_settings(SESSION_ENGINE=module_name):
        assert session_store_class() is CustomSessionStore


# ---------------------------------------------------------------------------
# ConnectionActorState & connection_actor_state
# ---------------------------------------------------------------------------


def test_connection_actor_state_initialization():
    """Initial state has unlatched provenance and an asyncio.Lock."""
    state = ConnectionActorState()
    assert state.authenticated_provenance is False
    assert isinstance(state.lock, asyncio.Lock)
    assert not state.lock.locked()


def test_connection_actor_state_slots_prevent_arbitrary_attributes():
    """__slots__ enforces exact field shape and raises AttributeError on typos."""
    state = ConnectionActorState()
    with pytest.raises(AttributeError):
        state.unknown_field = True  # type: ignore[attr-defined]


def test_connection_actor_state_get_or_create_reused_per_scope():
    """First access stores state under the private scope key; subsequent accesses return the same instance."""
    scope: dict[str, object] = {}
    state1 = connection_actor_state(scope)
    assert isinstance(state1, ConnectionActorState)
    assert _ACTOR_STATE_SCOPE_KEY in scope
    assert scope[_ACTOR_STATE_SCOPE_KEY] is state1

    state2 = connection_actor_state(scope)
    assert state2 is state1


def test_connection_actor_state_isolated_across_scopes():
    """Distinct scope dictionaries receive independent ConnectionActorState instances."""
    scope1: dict[str, object] = {}
    scope2: dict[str, object] = {}
    state1 = connection_actor_state(scope1)
    state2 = connection_actor_state(scope2)
    assert state1 is not state2
    assert state1.lock is not state2.lock


# ---------------------------------------------------------------------------
# note_authenticated_actor & connection_was_authenticated
# ---------------------------------------------------------------------------


def test_note_authenticated_actor_latches_provenance():
    """Provenance is initially False, becomes True on note, and remains True."""
    scope: dict[str, object] = {}
    assert connection_was_authenticated(scope) is False

    note_authenticated_actor(scope)
    assert connection_was_authenticated(scope) is True

    # Repeated calls are idempotent
    note_authenticated_actor(scope)
    assert connection_was_authenticated(scope) is True


# ---------------------------------------------------------------------------
# actor_lease & actor_transition
# ---------------------------------------------------------------------------


async def test_actor_lease_returns_scope_lock():
    """actor_lease returns the ConnectionActorState lock and can be held via async with."""
    scope: dict[str, object] = {}
    lock = actor_lease(scope)
    assert isinstance(lock, asyncio.Lock)
    assert lock is connection_actor_state(scope).lock

    async with actor_lease(scope) as held_lock:
        assert held_lock is None  # asyncio.Lock.__aenter__ returns None
        assert lock.locked()
    assert not lock.locked()


async def test_actor_transition_with_authenticated_latches_provenance():
    """actor_transition(was_authenticated=True) latches provenance and holds lease."""
    scope: dict[str, object] = {}
    assert connection_was_authenticated(scope) is False

    async with actor_transition(scope, was_authenticated=True):
        assert connection_was_authenticated(scope) is True
        assert actor_lease(scope).locked()

    assert not actor_lease(scope).locked()
    assert connection_was_authenticated(scope) is True


async def test_actor_transition_without_authenticated_does_not_latch_provenance():
    """actor_transition(was_authenticated=False) holds lease without latching provenance."""
    scope: dict[str, object] = {}
    assert connection_was_authenticated(scope) is False

    async with actor_transition(scope, was_authenticated=False):
        assert connection_was_authenticated(scope) is False
        assert actor_lease(scope).locked()

    assert not actor_lease(scope).locked()
    assert connection_was_authenticated(scope) is False


async def test_actor_transition_failure_still_latches_provenance_and_releases_lease():
    """Fail closed: an exception inside actor_transition still latches provenance and frees lease."""
    scope: dict[str, object] = {}
    assert connection_was_authenticated(scope) is False

    with pytest.raises(RuntimeError, match="teardown boom"):
        async with actor_transition(scope, was_authenticated=True):
            assert connection_was_authenticated(scope) is True
            raise RuntimeError("teardown boom")

    assert not actor_lease(scope).locked()
    assert connection_was_authenticated(scope) is True


async def test_actor_transition_and_lease_are_mutually_exclusive():
    """An in-flight actor_transition serializes against another task acquiring actor_lease."""
    scope: dict[str, object] = {}
    transition_entered = asyncio.Event()
    transition_can_exit = asyncio.Event()
    lease_acquired = {"value": False}

    async def task_transition():
        async with actor_transition(scope, was_authenticated=True):
            transition_entered.set()
            await transition_can_exit.wait()

    async def task_lease():
        await transition_entered.wait()
        async with actor_lease(scope):
            lease_acquired["value"] = True

    tt = asyncio.create_task(task_transition())
    tl = asyncio.create_task(task_lease())

    try:
        await transition_entered.wait()
        lock = actor_lease(scope)
        await _drain_until(lambda: bool(getattr(lock, "_waiters", None)))

        assert lock.locked()
        assert lease_acquired["value"] is False

        transition_can_exit.set()
        await asyncio.gather(tt, tl)

        assert lease_acquired["value"] is True
        assert not lock.locked()
    finally:
        for task in (tt, tl):
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
