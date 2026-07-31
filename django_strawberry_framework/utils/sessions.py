"""The session-engine resolver and the connection actor state, shared across the opt-in boundary.

Two subjects, and one reason for this module to hold both: each is state or an
expression that the **transport** layer (``consumers.py``) and the **auth** layer
(``auth/sessions.py`` / ``auth/mutations.py``) must agree on exactly, while
neither may drag the other in.

The first subject is the ``SESSION_ENGINE``
expression that resolves a deployment's ``SessionStore`` class, which has two
callers on opposite sides of the package's opt-in boundary.

* ``auth/sessions.py::uses_signed_cookie_sessions`` asks a *capability* question
  about the resolved class (can a WebSocket ``logout`` truthfully invalidate a
  session, or is there no server-side record to delete?).
* ``consumers.py::_refreshed_actor`` *instantiates* it to reload a WebSocket
  connection's session during the per-operation actor revalidation (spec-046
  Decision 11).

**Why it lives here and not in ``auth/sessions.py``.** The ``auth`` package is
structurally opt-in (spec-040 Decision 3): ``auth/__init__.py`` eagerly imports
``.mutations`` and ``.queries``, which pull the generated-mutation, declaration
registry, permission and Strawberry type machinery. Importing a submodule
executes its package's ``__init__`` first, so
``from .auth.sessions import session_store_class`` made the FIRST authenticated
WebSocket operation in a process that never opted into the GraphQL auth fields
import and register the entire auth subsystem on the event loop just to read one
settings string. Hosting the resolver in ``utils`` - which the transport layer and
the auth layer both already depend on - keeps one expression for the engine while
leaving ``auth`` opt-in, and keeps this module cycle-neutral: nothing here imports
``auth``, ``consumers``, ``routers``, or ``channels``, and both Django imports are
function-local, so importing this module costs nothing that is not already loaded.

The second subject is the **connection actor state**: the ONE synchronization
contract a Channels connection's actor transitions and the WebSocket revalidation
share (spec-046 Decision 11). It is scope-keyed rather than owned by either side,
because the two sides are structurally forbidden from importing each other and a
lock private to one of them is not a contract at all: the revalidation's
``consumers.py::_revocation_lock`` serializes checkpoints against each other, and
``auth/sessions.py::scope_session_lock`` serializes session mutations against each
other, so before this state existed a same-connection ``logout`` and an in-flight
revalidation could interleave freely. ``ConnectionActorState`` carries the two
facts neither lock can express:

* ``authenticated_provenance`` - whether this connection has EVER carried an
  authenticated actor. Immutable once latched, because the question the
  revalidation asks is "was this socket ever authenticated", and the current
  ``scope["user"]`` cannot answer it: a package-owned ``logout`` replaces that
  value with ``AnonymousUser``, so reading the live actor would classify a
  logged-out authenticated socket as a socket that was always anonymous - and let
  the anonymous carve-out skip the revalidation of every frame an
  already-admitted operation still wants to send. The latch keeps the carve-out
  (a genuinely anonymous socket still performs zero session reads) while denying
  it to an identity change.
* ``generation`` / ``transitions_in_flight`` - the read token an asynchronous
  actor read commits against. An actor transition is a WINDOW, not an instant
  (``channels.auth.logout`` fires a signal, flushes the store, and replaces the
  scope actor), so both edges are recorded: a read that starts before the window
  observes a bumped ``generation`` afterwards, and a read that starts inside it
  captures a non-zero ``transitions_in_flight``. Either way
  ``actor_read_is_committable`` refuses, and the refusing checkpoint - never this
  module - decides what that means for the connection.

**Lock order.** There is none to observe, and that is deliberate: no site
acquires the revocation lock and the scope session lock together, so no ordering
between them can deadlock. This state is what makes that safe. Every read and
write of it below is a plain attribute access with NO ``await`` between the read
and the store, so each is atomic on the single event loop the scope's operations
share - the same argument ``auth/sessions.py::scope_session_lock``'s lazy
get-or-create rests on. A checkpoint therefore captures its token before its
``await``, and commits only if the state still matches.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator, MutableMapping
from typing import Any


def session_store_class() -> type:
    """Resolve the configured ``SESSION_ENGINE``'s ``SessionStore`` class.

    The ONE expression that reads the deployment's session engine
    (``import_string(f"{settings.SESSION_ENGINE}.SessionStore")``) for both
    callers named in the module docstring. The resolution goes through Django's
    own ``import_string``, so a consumer-authored engine subclass resolves
    identically to a shipped one. ``settings`` is read at CALL time, never
    captured, so ``override_settings(SESSION_ENGINE=...)`` is honored.
    """
    from django.conf import settings
    from django.utils.module_loading import import_string

    return import_string(f"{settings.SESSION_ENGINE}.SessionStore")


#: The private scope key one connection's ``ConnectionActorState`` is stored
#: under. Namespaced with the distribution name exactly like
#: ``auth/sessions.py::_SCOPE_LOCK_KEY`` and
#: ``consumers.py::_REVALIDATED_AT_SCOPE_KEY``, so it can never collide with an
#: ASGI key set by Channels, Django, or consumer middleware.
_ACTOR_STATE_SCOPE_KEY = "__django_strawberry_framework_connection_actor_state__"


class ConnectionActorState:
    """One connection's actor provenance and transition bookkeeping.

    A tiny mutable record rather than three separate scope keys, so a caller
    cannot read half of it: ``actor_read_is_committable`` has to answer from the
    generation and the in-flight count TOGETHER, and a single object makes that
    one lookup. ``__slots__`` keeps it a fixed shape - an actor-state field is a
    security contract between two modules, so a typo must be an
    ``AttributeError`` rather than a silently ignored attribute nobody reads.
    """

    __slots__ = ("authenticated_provenance", "generation", "transitions_in_flight")

    def __init__(self) -> None:
        self.authenticated_provenance = False
        self.generation = 0
        self.transitions_in_flight = 0


def connection_actor_state(scope: MutableMapping[str, Any]) -> ConnectionActorState:
    """Return the scope's ``ConnectionActorState``, creating it on first use.

    Lazily created for the same reason the per-scope lock is: a scope arrives
    from Channels' middleware stack, so nothing the package owns runs early
    enough to seed it, and an HTTP scope that never reaches a checkpoint must not
    pay for one. The get-or-create has no ``await`` between the read and the
    store, so it is atomic on the event loop.
    """
    state = scope.get(_ACTOR_STATE_SCOPE_KEY)
    if state is None:
        state = ConnectionActorState()
        scope[_ACTOR_STATE_SCOPE_KEY] = state
    return state


def note_authenticated_actor(scope: MutableMapping[str, Any]) -> None:
    """Latch that this connection has carried an authenticated actor.

    Write-once in meaning: the flag is only ever set, never cleared, which is
    what makes it *provenance* instead of a second copy of ``scope["user"]``.
    """
    connection_actor_state(scope).authenticated_provenance = True


def connection_was_authenticated(scope: MutableMapping[str, Any]) -> bool:
    """Whether an authenticated actor has ever been observed on this connection."""
    return connection_actor_state(scope).authenticated_provenance


def actor_read_token(scope: MutableMapping[str, Any]) -> tuple[int, int]:
    """Capture the state an asynchronous actor read will have to commit against.

    Taken BEFORE the read suspends, and handed back to
    ``actor_read_is_committable`` afterwards.
    """
    state = connection_actor_state(scope)
    return (state.generation, state.transitions_in_flight)


def actor_read_is_committable(scope: MutableMapping[str, Any], token: tuple[int, int]) -> bool:
    """Whether a read taken at ``token`` may still be committed to the scope.

    Committable means: no actor transition is running now, and none started or
    finished while the read was in flight. A ``token`` whose in-flight count was
    already non-zero can never match, so a read that begins inside a transition
    window is refused even if it resumes before the window closes.
    """
    state = connection_actor_state(scope)
    return state.transitions_in_flight == 0 and token == (state.generation, 0)


@contextlib.contextmanager
def actor_transition(
    scope: MutableMapping[str, Any],
    *,
    was_authenticated: bool,
) -> Iterator[None]:
    """Mark a package-owned actor transition on ``scope`` for its whole duration.

    Wrapped around the native teardown / establishment itself rather than
    recorded at one of its edges: the transition is a window during which the
    session and the scope actor disagree with each other, and a concurrent
    revalidation must be refused throughout it. ``was_authenticated`` latches the
    provenance of the actor being transitioned AWAY from, and must be read before
    the body replaces it.

    The generation is advanced on the way out unconditionally - including when
    the body raises. A failed teardown leaves a state the transitioning code
    itself compensates but no concurrent read observed consistently, so refusing
    that read is the fail-closed answer.
    """
    state = connection_actor_state(scope)
    if was_authenticated:
        state.authenticated_provenance = True
    state.transitions_in_flight += 1
    try:
        yield
    finally:
        state.generation += 1
        state.transitions_in_flight -= 1
