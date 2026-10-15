"""Behavioral tests for the session-engine resolver and connection actor lease.

``session_store_class`` hostile ``SESSION_ENGINE`` shapes and the WebSocket actor
lease have no GraphQL document: login/logout sessions live in
``examples/fakeshop/test_query/test_auth_api.py``; actor serialization stays here
until fakeshop mounts ASGI.
"""

from __future__ import annotations

import asyncio
import contextlib
import sys
import types
from typing import NoReturn

import pytest
from django.conf import settings as django_settings
from django.contrib.sessions.backends.db import SessionStore as DBSessionStore
from django.contrib.sessions.backends.signed_cookies import (
    SessionStore as SignedCookieSessionStore,
)
from django.test import override_settings
from django.utils.functional import SimpleLazyObject
from typing_extensions import override

from django_strawberry_framework.exceptions import ConfigurationError
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
from tests._idioms import ClaimsClass, ClassReadRaises, stub_module
from tests.auth._helpers import _drain_until

# ---------------------------------------------------------------------------
# session_store_class
# ---------------------------------------------------------------------------


def test_session_store_class_resolves_default_engine() -> None:
    """Default engine resolves to Django's DB SessionStore."""
    resolved = session_store_class()
    assert resolved is DBSessionStore


@override_settings(SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies")
def test_session_store_class_honors_override_settings() -> None:
    """Settings overrides at call time dynamically resolve the new store class."""
    resolved = session_store_class()
    assert resolved is SignedCookieSessionStore


def test_session_store_class_resolves_custom_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    """A custom session engine resolves identically via import_string."""
    module_name = "tests.utils._stub_custom_session_engine"

    class CustomSessionStore:
        pass

    module = stub_module(module_name, SessionStore=CustomSessionStore)
    monkeypatch.setitem(sys.modules, module_name, module)

    with override_settings(SESSION_ENGINE=module_name):
        assert session_store_class() is CustomSessionStore


def test_session_store_class_reports_an_unreadable_setting_as_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``settings.SESSION_ENGINE`` read that RAISES becomes ``ConfigurationError``.

    A settings object whose ``SESSION_ENGINE`` descriptor raises is the
    hostile-configuration shape the five-shape guard exists for: the resolver
    must name the setting rather than let the descriptor's own exception escape
    through the session boundary.
    """

    class _RaisingSettings:
        def __getattr__(self, name: str) -> object:
            raise KeyError(name)

    monkeypatch.setattr("django_strawberry_framework.utils.sessions.settings", _RaisingSettings())
    with pytest.raises(ConfigurationError, match="SESSION_ENGINE could not be read"):
        session_store_class()

    # The module attribute is restored by monkeypatch; prove the resolver is
    # not left wedged on the stand-in.
    monkeypatch.undo()
    assert django_settings.SESSION_ENGINE
    assert session_store_class() is DBSessionStore


@override_settings(SESSION_ENGINE=object())
def test_session_store_class_rejects_a_non_string_engine() -> None:
    """A non-string ``SESSION_ENGINE`` is rejected before any import is attempted."""
    with pytest.raises(ConfigurationError, match="must be a string"):
        session_store_class()


@override_settings(SESSION_ENGINE="")
def test_session_store_class_rejects_an_empty_engine() -> None:
    """An empty ``SESSION_ENGINE`` is rejected rather than importing ``.SessionStore``."""
    with pytest.raises(ConfigurationError, match="non-empty string"):
        session_store_class()


@override_settings(SESSION_ENGINE="tests.utils._no_such_session_engine")
def test_session_store_class_reports_an_unresolvable_engine_as_configuration_error() -> None:
    """An engine that does not import is a ``ConfigurationError`` naming the engine."""
    with pytest.raises(ConfigurationError, match="_no_such_session_engine"):
        session_store_class()


def test_session_store_class_reports_a_storeless_engine_as_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An engine module WITHOUT ``SessionStore`` is a ``ConfigurationError``, not an ImportError.

    ``import_string`` raises ``ImportError`` for a missing module and for a
    missing attribute alike; both arrive at the same guard, so the module-exists
    arm needs its own proof.
    """
    module_name = "tests.utils._stub_storeless_session_engine"
    monkeypatch.setitem(sys.modules, module_name, types.ModuleType(module_name))

    with (
        override_settings(SESSION_ENGINE=module_name),
        pytest.raises(ConfigurationError, match="SessionStore"),
    ):
        session_store_class()


class _FormatHostileEngine(str):
    """A deployment-supplied engine whose ``__format__`` raises while being interpolated."""

    @override
    def __format__(self, spec: str) -> str:
        raise RuntimeError("hostile __format__")


class _ReprHostileEngine(str):
    """A deployment-supplied engine whose ``__repr__`` raises while being rendered."""

    @override
    def __repr__(self) -> str:
        raise RuntimeError("hostile __repr__")


@override_settings(SESSION_ENGINE=_FormatHostileEngine("tests.utils._no_such_engine"))
def test_session_store_class_format_hostile_engine_raises_configuration_error() -> None:
    """A hostile ``__format__`` on the engine cannot defeat the typed rejection.

    ``SESSION_ENGINE`` is deployment-supplied, so the import-path f-string
    ``f"{engine}.SessionStore"`` must never dispatch a consumer dunder: a
    raising ``__format__`` would replace the promised ``ConfigurationError``
    with an arbitrary exception on exactly the misconfiguration path where the
    typed error matters (the same guarantee ``describe_value`` gives the
    non-string rejection). The engine is flattened through the base ``str``
    slot, so the rejection stays typed.
    """
    with pytest.raises(ConfigurationError, match="Could not resolve SESSION_ENGINE"):
        session_store_class()


@override_settings(SESSION_ENGINE=_ReprHostileEngine("tests.utils._no_such_engine"))
def test_session_store_class_repr_hostile_engine_raises_configuration_error() -> None:
    """A hostile ``__repr__`` on the engine cannot defeat the typed rejection.

    The import-failure message renders the engine through ``{engine!r}`` at the
    RAISE SITE - before any exception object exists, so the error hierarchy's
    own ``__repr__`` guards cannot help. A deployment-supplied engine subclass
    with a raising ``__repr__`` must therefore arrive at that site as a plain
    base ``str``.
    """
    with pytest.raises(ConfigurationError, match="Could not resolve SESSION_ENGINE"):
        session_store_class()


@override_settings(SESSION_ENGINE=_ReprHostileEngine("tests.utils._no_such_engine"))
def test_session_store_class_repr_hostile_engine_names_the_engine_path() -> None:
    """The flattened engine still renders its path in the rejection message.

    Flattening is a safety measure, not a redaction: the actionable part of the
    message (which module could not be imported) survives.
    """
    with pytest.raises(ConfigurationError, match=r"tests\.utils\._no_such_engine"):
        session_store_class()


@pytest.mark.parametrize(
    ("engine", "rendered"),
    [
        pytest.param(
            ClassReadRaises(RuntimeError),
            "ClassReadRaises <ClassReadRaises>",
            id="class-read-raises",
        ),
        pytest.param(
            ClassReadRaises(KeyboardInterrupt),
            "ClassReadRaises <ClassReadRaises>",
            id="class-read-interrupts",
        ),
        pytest.param(ClaimsClass(str), "ClaimsClass <ClaimsClass>", id="claims-str"),
        pytest.param(
            SimpleLazyObject(lambda: "django.contrib.sessions.backends.db"),
            "SimpleLazyObject <SimpleLazyObject: ",
            id="lazy-str",
        ),
    ],
)
def test_session_store_class_rejects_an_engine_that_is_not_really_a_string(
    engine: object,
    rendered: str,
) -> None:
    """The engine is a string only if its real type is: its ``__class__`` is never consulted.

    A ``__class__`` that raises or claims ``str`` would otherwise escape the typed rejection
    (the base ``str`` slot below refuses an object that is not really a ``str``).
    """
    with override_settings(SESSION_ENGINE=engine), pytest.raises(ConfigurationError) as excinfo:
        session_store_class()
    assert str(excinfo.value).startswith(f"SESSION_ENGINE must be a string; got {rendered}")


class _TruthinessHostileEngine(str):
    """An engine whose ``__bool__`` and ``__len__`` raise when its truthiness is tested."""

    def __bool__(self) -> NoReturn:
        raise RuntimeError("hostile __bool__")

    @override
    def __len__(self) -> NoReturn:
        raise RuntimeError("hostile __len__")


def test_session_store_class_resolves_a_truthiness_hostile_engine() -> None:
    """The emptiness test reads the flattened engine, never the subclass's ``__bool__`` / ``__len__``."""
    engine = _TruthinessHostileEngine("django.contrib.sessions.backends.signed_cookies")
    with override_settings(SESSION_ENGINE=engine):
        assert session_store_class() is SignedCookieSessionStore


def test_session_store_class_rejects_an_empty_truthiness_hostile_engine() -> None:
    """An empty hostile engine meets the typed emptiness rejection, not its own exception."""
    with (
        override_settings(SESSION_ENGINE=_TruthinessHostileEngine("")),
        pytest.raises(ConfigurationError, match="SESSION_ENGINE must be a non-empty string"),
    ):
        session_store_class()


# ---------------------------------------------------------------------------
# ConnectionActorState & connection_actor_state
# ---------------------------------------------------------------------------


def test_connection_actor_state_initialization() -> None:
    """Initial state has unlatched provenance and an asyncio.Lock."""
    state = ConnectionActorState()
    assert state.authenticated_provenance is False
    assert isinstance(state.lock, asyncio.Lock)
    assert not state.lock.locked()


def test_connection_actor_state_slots_prevent_arbitrary_attributes() -> None:
    """__slots__ enforces exact field shape and raises AttributeError on typos."""
    state = ConnectionActorState()
    with pytest.raises(AttributeError):
        # basedpyright: the undeclared slot write is the rejected operation under test
        state.unknown_field = True  # pyright: ignore[reportAttributeAccessIssue]


def test_connection_actor_state_get_or_create_reused_per_scope() -> None:
    """First access stores state under the private scope key; subsequent accesses return the same instance."""
    scope: dict[str, object] = {}
    state1 = connection_actor_state(scope)
    assert isinstance(state1, ConnectionActorState)
    assert _ACTOR_STATE_SCOPE_KEY in scope
    assert scope[_ACTOR_STATE_SCOPE_KEY] is state1

    state2 = connection_actor_state(scope)
    assert state2 is state1


def test_connection_actor_state_isolated_across_scopes() -> None:
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


def test_note_authenticated_actor_latches_provenance() -> None:
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


async def test_actor_lease_returns_scope_lock() -> None:
    """actor_lease returns the ConnectionActorState lock and can be held via async with."""
    scope: dict[str, object] = {}
    lock = actor_lease(scope)
    assert isinstance(lock, asyncio.Lock)
    assert lock is connection_actor_state(scope).lock

    async with actor_lease(scope) as held_lock:
        assert held_lock is None  # asyncio.Lock.__aenter__ returns None
        assert lock.locked()
    assert not lock.locked()


async def test_actor_transition_with_authenticated_latches_provenance() -> None:
    """actor_transition(was_authenticated=True) latches provenance and holds lease."""
    scope: dict[str, object] = {}
    assert connection_was_authenticated(scope) is False

    async with actor_transition(scope, was_authenticated=True):
        assert connection_was_authenticated(scope) is True
        assert actor_lease(scope).locked()

    assert not actor_lease(scope).locked()
    assert connection_was_authenticated(scope) is True


async def test_actor_transition_without_authenticated_does_not_latch_provenance() -> None:
    """actor_transition(was_authenticated=False) holds lease without latching provenance."""
    scope: dict[str, object] = {}
    assert connection_was_authenticated(scope) is False

    async with actor_transition(scope, was_authenticated=False):
        assert connection_was_authenticated(scope) is False
        assert actor_lease(scope).locked()

    assert not actor_lease(scope).locked()
    assert connection_was_authenticated(scope) is False


async def test_actor_transition_failure_still_latches_provenance_and_releases_lease() -> None:
    """Fail closed: an exception inside actor_transition still latches provenance and frees lease."""
    scope: dict[str, object] = {}
    assert connection_was_authenticated(scope) is False

    async def body_that_raises() -> NoReturn:
        async with actor_transition(scope, was_authenticated=True):
            assert connection_was_authenticated(scope) is True
            raise RuntimeError("teardown boom")

    with pytest.raises(RuntimeError, match="teardown boom"):
        await body_that_raises()

    assert not actor_lease(scope).locked()
    assert connection_was_authenticated(scope) is True


async def test_actor_transition_and_lease_are_mutually_exclusive() -> None:
    """An in-flight actor_transition serializes against another task acquiring actor_lease."""
    scope: dict[str, object] = {}
    transition_entered = asyncio.Event()
    transition_can_exit = asyncio.Event()
    lease_acquired = {"value": False}

    async def task_transition() -> None:
        async with actor_transition(scope, was_authenticated=True):
            transition_entered.set()
            await transition_can_exit.wait()

    async def task_lease() -> None:
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
