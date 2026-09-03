"""The session-engine resolver and the connection actor lease, shared across the opt-in boundary.

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

The second subject is the **connection actor lease**: the ONE synchronization
primitive a Channels connection's actor transitions and the WebSocket
revalidation share (spec-046 Decision 11). It is scope-keyed rather than owned by
either side, because the two sides are structurally forbidden from importing each
other and a lock private to one of them is not a contract at all:
``consumers.py``'s revalidation checkpoints only ever serialized against each
other, ``auth/sessions.py::scope_session_lock`` only ever serializes session
mutations against each other, and two independent locks give no ordering AT ALL
between the two state machines - so a same-connection ``logout`` and an in-flight
revalidation could interleave freely, including in the one ordering no
after-the-fact check can repair: a checkpoint that has already authorized a frame
and whose asynchronous ASGI send has not yet committed the bytes. A generation
compared after ``send`` is too late, because by then the frame is on the wire.
``ConnectionActorState`` therefore carries two facts, and the first of them IS
the missing lock:

* ``lock`` - the connection's actor lease, reached through ``actor_lease``. A
  revalidation checkpoint holds it across its ENTIRE validate / commit / send
  sequence, and ``actor_transition`` holds it across the whole native teardown
  that changes the actor, so the two are mutually exclusive **by construction**:
  a transition cannot begin while a protected frame is still being written, and
  no checkpoint can authorize anything - from a session read OR from a
  positive-window cache hit - while a transition owns the connection. Both
  directions are load-bearing, and the cache hit is the half a lease-free design
  silently omits: reusing a timestamp is an authorization decision like any
  other, so it happens under the same lease an uncached validation holds.
* ``authenticated_provenance`` - whether this connection has EVER carried an
  authenticated actor. Immutable once latched, because the question the
  revalidation asks is "was this socket ever authenticated", and the current
  ``scope["user"]`` cannot answer it: a package-owned ``logout`` replaces that
  value with ``AnonymousUser``, so reading the live actor would classify a
  logged-out authenticated socket as a socket that was always anonymous - and let
  the anonymous carve-out skip the revalidation of every frame an
  already-admitted operation still wants to send. The latch keeps the carve-out
  (a genuinely anonymous socket still performs zero session reads) while denying
  it to an identity change, and it is what makes the post-transition refusal
  READ-FREE.

**Lock order: the scope session lock is OUTER, the actor lease is INNER.** Exactly
one site holds both - ``auth/mutations.py::_channels_logout``, which enters
``actor_transition`` while already holding
``auth/sessions.py::scope_session_lock`` - and nothing that holds the lease ever
asks for the session lock, because the revalidation checkpoints are pure
transport and never enter the auth layer. The order is therefore total and
acyclic with one rule to remember, which is precisely why the lease had to be
this state's own lock rather than a third independent primitive beside the two
that already exist.

**What the lease costs, stated rather than left emergent.** It is a
per-connection serialization point that spans a session read on one side and a
native ``channels.auth.logout`` teardown on the other, so a same-connection
``logout`` waits for an in-flight protected send and a protected send waits for a
running ``logout``. That waiting is not overhead around the guarantee, it IS the
guarantee; ``consumers.py``'s module docstring carries the head-of-line
consequence for the outbound hot path, and it is bounded by the same session
backend the read already depends on.

The lazy get-or-create below has NO ``await`` between the read and the store, so
it is atomic on the single event loop the scope's operations share - the same
argument ``auth/sessions.py::scope_session_lock``'s own lazy get-or-create rests
on, and the reason one scope can never end up with two leases.
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
from collections.abc import AsyncIterator, MutableMapping
from typing import Any

__all__ = (
    "ConnectionActorState",
    "ScopeSingletonMessages",
    "actor_lease",
    "actor_transition",
    "connection_actor_state",
    "connection_was_authenticated",
    "note_authenticated_actor",
    "scope_key",
    "scope_singleton",
    "session_store_class",
)


def scope_key(name: str) -> str:
    """Build the collision-resistant ASGI scope key for ``name``.

    An ASGI scope is a shared namespace: Channels, Django, and any consumer
    middleware write into the same mapping, so every key this package stores is
    namespaced with the distribution name. That namespacing was hand-spelled at
    each key, which is a convention nothing enforced - one key written without
    the prefix collides silently, and the collision surfaces as corrupted state
    on a security path rather than as an error.
    """
    return f"__django_strawberry_framework_{name}__"


@dataclasses.dataclass(frozen=True, slots=True)
class ScopeSingletonMessages:
    """The four consumer-facing failures :func:`scope_singleton` can report.

    Declared as DATA per call site rather than interleaved with the control
    flow, because the wordings are genuinely per-surface (the auth boundary
    names the lock; the revalidation boundary names the actor state) while the
    algorithm must not be. Making them a required field set also means a new
    failure mode added to the algorithm cannot be added at one call site and
    forgotten at the other: it is a field, so every site must answer it.

    ``corrupted`` is a format template receiving ``actual`` (the safely-rendered
    type name of whatever was found in the slot).
    """

    unreadable: str
    unstorable: str
    uninspectable: str
    corrupted: str


def scope_singleton(
    scope: MutableMapping[str, Any],
    key: str,
    *,
    factory: Any,
    expect: type,
    messages: ScopeSingletonMessages,
) -> Any:
    """Return the scope's singleton under ``key``, creating it on first use.

    The per-scope lazy singleton, once. Nothing the package owns runs early
    enough to seed a scope (it arrives from Channels' middleware stack), and a
    connection that never reaches the feature must not pay for one, so every
    per-scope object is created on first use.

    Two properties are load-bearing and are why this is one body rather than
    two:

    * **No ``await`` between the read and the store.** The get-or-create is
      therefore atomic on the event loop, and two operations multiplexed on one
      connection cannot each create their own object - which for a lock would
      mean no serialization at all.
    * **A corrupted slot is a typed error, never a silent replacement.** Every
      read, store and type test is contained, because the scope is a mapping
      other software also writes to: finding the wrong object there means
      something else owns the key, and quietly overwriting it would trade a
      loud configuration error for two systems sharing one slot.
    """
    from ..exceptions import ConfigurationError, _safe_type_name

    try:
        value = scope.get(key)
    except BaseException as exc:
        raise ConfigurationError(messages.unreadable) from exc
    if value is None:
        value = factory()
        try:
            scope[key] = value
        except BaseException as exc:
            raise ConfigurationError(messages.unstorable) from exc
        return value
    try:
        matches = isinstance(value, expect)
    except BaseException as exc:
        raise ConfigurationError(messages.uninspectable) from exc
    if not matches:
        raise ConfigurationError(messages.corrupted.format(actual=_safe_type_name(value)))
    return value


def session_store_class() -> type:
    """Resolve the configured ``SESSION_ENGINE``'s ``SessionStore`` class.

    The ONE expression that reads the deployment's session engine
    (``import_string(f"{settings.SESSION_ENGINE}.SessionStore")``) for both
    callers named in the module docstring. The resolution goes through Django's
    own ``import_string``, so a consumer-authored engine subclass resolves
    identically to a shipped one. ``settings`` is read at CALL time, never
    captured, so ``override_settings(SESSION_ENGINE=...)`` is honored. A
    deployment-supplied engine that is a hostile ``str`` subclass is flattened
    through the base ``str`` slot before it reaches either interpolation below,
    so a raising ``__format__`` / ``__repr__`` cannot replace the typed
    ``ConfigurationError`` with an arbitrary consumer exception while the import
    path or the rejection message is being assembled.
    """
    from django.conf import settings
    from django.utils.module_loading import import_string

    from ..exceptions import ConfigurationError, describe_value

    try:
        engine = settings.SESSION_ENGINE
    except (
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
        IndexError,
    ) as exc:
        raise ConfigurationError(
            "SESSION_ENGINE could not be read from settings "
            f"({type(exc).__name__}); check settings.SESSION_ENGINE.",
        ) from exc
    if not isinstance(engine, str):
        raise ConfigurationError(
            f"SESSION_ENGINE must be a string; got {describe_value(engine)}.",
        )
    if not engine:
        raise ConfigurationError(
            "SESSION_ENGINE must be a non-empty string; got empty value.",
        )
    # ``engine`` came from the deployment and may be a ``str`` subclass whose
    # dunders raise. ``str.__str__`` on a non-exact ``str`` returns a plain base
    # copy without dispatching the subclass's ``__str__``, so both f-string
    # interpolations below (the import path here and the ``{engine!r}`` tail at
    # the raise site) render through C slots that cannot run consumer code - the
    # same guarantee ``describe_value`` gives the non-string rejection above.
    engine = str.__str__(engine)
    try:
        return import_string(f"{engine}.SessionStore")
    except (
        ImportError,
        TypeError,
        ValueError,
        AttributeError,
        KeyError,
        IndexError,
    ) as exc:
        raise ConfigurationError(
            f"Could not resolve SESSION_ENGINE {engine!r}'s SessionStore "
            f"({type(exc).__name__}); check settings.SESSION_ENGINE.",
        ) from exc


#: The private scope key one connection's ``ConnectionActorState`` is stored
#: under, namespaced through the shared :func:`scope_key` builder alongside
#: ``auth/sessions.py::_SCOPE_LOCK_KEY`` and
#: ``consumers.py::_REVALIDATED_AT_SCOPE_KEY``.
_ACTOR_STATE_SCOPE_KEY = scope_key("connection_actor_state")

_ACTOR_STATE_MESSAGES = ScopeSingletonMessages(
    unreadable="The WebSocket revalidation state could not be read from the scope.",
    unstorable="The WebSocket revalidation state could not be stored on the scope.",
    uninspectable="The WebSocket revalidation state could not be inspected.",
    corrupted=(
        "The WebSocket revalidation state is corrupted; expected a "
        "ConnectionActorState, got {actual}."
    ),
)


class ConnectionActorState:
    """One connection's actor lease and its authentication provenance.

    A tiny mutable record rather than two separate scope keys, so the lease and
    the fact it protects arrive together in ONE lookup and cannot be created
    independently - a caller holding a lease from one scope key while reading
    provenance from another is not a synchronization contract. ``__slots__``
    keeps it a fixed shape: an actor-state field is a security contract between
    two modules, so a typo must be an ``AttributeError`` rather than a silently
    ignored attribute nobody reads.

    ``asyncio.Lock()`` is constructed here rather than lazily beside the first
    ``await``, which is safe because it binds its loop on first use rather than at
    construction (Python 3.10+, the package's floor) - the same property
    ``consumers.py``'s per-connection lock already relied on. Constructing it
    eagerly is what keeps ``connection_actor_state``'s get-or-create a single
    ``await``-free step, and therefore atomic. It inherits
    ``auth/sessions.py::scope_session_lock``'s loop caveat verbatim, for the same
    reason and with the same resolution: an ``asyncio.Lock`` binds to the loop that
    first contends it, so only a scope that lives on ONE loop may reuse it - which
    is exactly what a WebSocket connection is, while the ``async_to_sync`` bridge
    only ever sees a per-request scope whose lease is created and awaited on that
    request's own loop.
    """

    __slots__ = ("authenticated_provenance", "lock")

    def __init__(self) -> None:
        self.authenticated_provenance = False
        self.lock = asyncio.Lock()


def connection_actor_state(scope: MutableMapping[str, Any]) -> ConnectionActorState:
    """Return the scope's ``ConnectionActorState``, creating it on first use.

    Lazily created for the same reason the per-scope lock is: a scope arrives
    from Channels' middleware stack, so nothing the package owns runs early
    enough to seed it, and an HTTP scope that never reaches a checkpoint must not
    pay for one. The get-or-create has no ``await`` between the read and the
    store, so it is atomic on the event loop.
    """
    return scope_singleton(
        scope,
        _ACTOR_STATE_SCOPE_KEY,
        factory=ConnectionActorState,
        expect=ConnectionActorState,
        messages=_ACTOR_STATE_MESSAGES,
    )


def note_authenticated_actor(scope: MutableMapping[str, Any]) -> None:
    """Latch that this connection has carried an authenticated actor.

    Write-once in meaning: the flag is only ever set, never cleared, which is
    what makes it *provenance* instead of a second copy of ``scope["user"]``.
    """
    connection_actor_state(scope).authenticated_provenance = True


def connection_was_authenticated(scope: MutableMapping[str, Any]) -> bool:
    """Whether an authenticated actor has ever been observed on this connection."""
    return connection_actor_state(scope).authenticated_provenance


def actor_lease(scope: MutableMapping[str, Any]) -> asyncio.Lock:
    """Return the connection's actor lease, to be held with ``async with``.

    The transport side of the shared primitive: ``consumers.py``'s two
    revalidation checkpoints wrap their whole critical section in this - the
    revoked-state read, the window decision, the session read, the actor
    write-back, the revoked-state transition AND the information-bearing send -
    so an actor transition can neither start inside that sequence nor complete
    across it. Holding it through the send is the load-bearing part: an ASGI send
    is asynchronous, so releasing the lease after validation would leave a window
    in which a same-connection ``logout`` runs to completion and the
    already-authorized frame is then committed to the socket behind it.

    The lease is handed back rather than wrapped in an ``asynccontextmanager``,
    which reads the same at every call site and costs strictly less at the one
    place per-acquisition cost multiplies: an ``asyncio.Lock`` IS an async context
    manager, so wrapping it would build an async generator and an
    ``_AsyncGeneratorContextManager`` per acquisition, and drive that generator
    once on the way in and once on the way out - on the outbound hot path, per
    protected frame, inside the serialization point this whole design accepts. It
    also keeps the lease usable as a plain object where that is what a caller
    needs, which is how ``auth/sessions.py::scope_session_lock`` already yields
    its own lock rather than only its scope.

    Deliberately NOT re-entrant (an ``asyncio.Lock`` never is): a checkpoint that
    reached a second checkpoint on the same connection in the same task would be
    a control-flow bug, and deadlocking on it is a better outcome than silently
    authorizing a nested send. See the module docstring for the one site that
    holds this together with ``auth/sessions.py::scope_session_lock`` and for the
    order the two observe.
    """
    return connection_actor_state(scope).lock


@contextlib.asynccontextmanager
async def actor_transition(
    scope: MutableMapping[str, Any],
    *,
    was_authenticated: bool,
) -> AsyncIterator[None]:
    """Own the connection's actor lease across a package-owned actor transition.

    The auth side of the same primitive, named for what it means there. Wrapped
    around the native teardown / establishment itself rather than recorded at one
    of its edges: the transition is an interval during which the durable session
    and the scope actor disagree with each other, and no revalidation checkpoint
    may authorize anything - by a read or from the positive-window cache -
    anywhere inside it. Because the lease is exclusive, the wait runs in both
    directions: entering here also blocks until any protected frame already being
    written has left, so this teardown cannot complete underneath one.

    ``was_authenticated`` latches the provenance of the actor being transitioned
    AWAY from, and must be read before the body replaces it. It is latched INSIDE
    the lease and before the body runs, so the first checkpoint to acquire the
    lease after this block sees a connection that was authenticated even when the
    teardown failed part way - which is the fail-closed direction, and is why the
    latch is not conditional on the body returning.
    """
    async with actor_lease(scope):
        if was_authenticated:
            note_authenticated_actor(scope)
        yield
