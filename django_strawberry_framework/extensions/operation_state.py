"""One operation's state, for extensions the engine hands the same object to twice.

Strawberry resolves an ``extensions=[...]`` entry per operation, and two of the
three accepted spellings resolve to the SAME object every time: an instance
entry is passed through unchanged, and a factory that returns a module-level
singleton - the shape the optimizer documents, because its plan cache is
deliberately shared - returns that singleton to every operation. The engine then
assigns ``extension.execution_context`` on every resolved member before it
builds the runner, and brackets ``on_operation``, parsing, validation,
execution, the streaming-result hooks and result collection on that same member.
It neither restores the attribute afterwards nor wraps a pass-through instance.

So an ordinary ``self.execution_context`` on a shared extension is one slot two
operations write: a nested ``info.schema.execute_sync(...)`` leaves the inner
document in it after the inner call returned, and two overlapping requests
leave whichever assigned last. Everything the package reads through that
attribute - the document a resource policy charges, the result an error policy
masks, the payload a debug extension publishes - is then read for the wrong
operation, which is a security question rather than a bookkeeping one: the
charge lands on a benign document while the oversized one executes, and the
mask lands on a result that is not the one going to the client.

**The boundary is one state object per (resolved extension, runner), reachable
only through a task-local binding while that runner is active.** Two kinds of
state separate here and never merge:

- **Configuration** is long-lived, belongs to the extension or the schema, and
  is read-only to resolvers. It stays where it is (``utils/private_state.py``).
- **One operation's mutable state** belongs to the runner created for that
  operation: the engine context, and whatever scratch that extension keeps for
  the operation it is answering.

:class:`_OperationBoundExtension` is the base every framework extension whose
state is per-operation derives from. ``execution_context`` becomes a read of the
state currently bound to that extension, and the engine's assignment becomes a
HANDOFF rather than the binding: it is recorded as a pending assignment,
``schema.py::DjangoSchema.create_extensions_runner`` claims the one that names
its own context, and the runner creates the state from the context it was
constructed with. The claim happens before that factory returns, because
upstream builds the middleware manager and the execution machinery between the
factory and ``operation()`` - a failure in that gap has no operation teardown to
run, and a handoff left standing there would be the leak this module exists to
close.

The binding carrier is itself security-relevant, so it is not an ordinary
attribute a resolver can replace or a second ``__init__`` can recreate: one
``ContextVar`` per extension identity, settled at construction behind
``utils/private_state.py::PrivateAuthority``. The authority may hold the
variable strongly because a ``ContextVar`` points back at nothing; the extension
itself it holds only weakly. Every binding resets, so no request is retained
through a task context after the operation that made it.

**A plain ``strawberry.Schema`` is outside the runner's reach and is not
promised what it cannot be given.** That schema never calls the package's runner
factory, so an assignment queued for it would be a handoff nothing claims. The
setter therefore branches on whether the assigned context belongs to a
``DjangoSchema``: for one that does not, the state is created immediately and
held on the instance, which makes it operation-local exactly for the entries
that are fresh per operation - a class entry and a factory that builds one. A
shared instance on a raw schema remains outside the isolation guarantee; the
documented spelling for that schema is a class or a fresh factory.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterable, Iterator
from contextvars import ContextVar, Token
from typing import Any, NamedTuple
from weakref import ReferenceType, ref

from strawberry.extensions.base_extension import SchemaExtension
from strawberry.extensions.runner import SchemaExtensionsRunner

from ..exceptions import ConfigurationError
from ..utils.private_state import PrivateAuthority

__all__ = ("DjangoExtensionsRunner", "OperationState")


class OperationState:
    """One operation's mutable state, for one extension answering it.

    The engine context is the state every operation-bound extension needs; a
    subclass adds the scratch its own extension keeps for the operation, and
    nothing else may: state that outlives the operation is configuration and
    belongs to an authority instead.

    ``__slots__`` rather than a plain namespace, because this object is reached
    from every hook of the operation it belongs to and a typo that silently
    grows an attribute here is a value the next operation would not have.
    """

    __slots__ = ("execution_context",)

    def __init__(self, execution_context: Any) -> None:
        self.execution_context = execution_context


class _Assignment(NamedTuple):
    """One engine assignment waiting for the runner that will claim it.

    The extension is held WEAKLY. An assignment the runner never claims -
    upstream raises inside its own assignment loop, a consumer entry's setter
    refuses - would otherwise keep a per-operation extension alive in the task's
    context for as long as that task lives. A dead entry is dropped by the next
    claim instead.
    """

    extension: ReferenceType[Any]
    execution_context: Any


#: One binding carrier per operation-bound extension, settled at construction.
#:
#: The variable holds the state bound for the operation this extension is
#: answering IN THIS TASK, and nothing else: it is set by the package runner and
#: reset by it, so two operations on one extension never see each other's state
#: and no request is retained once its operation ends.
#:
#: Held here rather than in an attribute because the carrier decides what
#: ``execution_context`` answers with, and an attribute holding it is one a
#: resolver replaces - pointing the read at a variable the runner never binds,
#: which answers every later operation with whatever that resolver put there.
#: A ``ContextVar`` points back at nothing, so holding one strongly retains
#: nothing but the variable; the extension it belongs to is held weakly, and its
#: entry is dropped when the extension dies.
_OPERATION_CARRIERS: PrivateAuthority[ContextVar[Any]] = PrivateAuthority()

#: The engine assignments this task has made and no runner has claimed yet.
#:
#: One task-local stack rather than a field on the extension, because the
#: assignment is a value two operations on a shared extension both produce: an
#: inner execution assigns while the outer operation's state is still bound, and
#: the inner runner must claim exactly its own. Entries are claimed by identity
#: and by the exact context they name, so nesting resolves in the order it
#: happened.
_PENDING_ASSIGNMENTS: ContextVar[tuple[_Assignment, ...]] = ContextVar(
    "django_strawberry_framework_pending_assignments",
    default=(),
)


def _carrier(extension: Any) -> ContextVar[Any]:
    """The binding carrier settled for ``extension`` at construction.

    Absent for one case only: a subclass whose ``__init__`` never reached
    :meth:`_OperationBoundExtension.__init__`. That extension has no place to
    bind an operation's state, so the operation it was installed for would run
    reading whatever the last one left - which is the failure this module
    exists to remove, and so is refused rather than approximated.
    """
    carrier = _OPERATION_CARRIERS.recall(extension)
    if carrier is None:
        raise ConfigurationError(
            f"{type(extension).__name__} has no operation-state binding, so its "
            "__init__ never ran the one this package installs. A subclass "
            "defining __init__ has to call super().__init__().",
        )
    return carrier


def _is_operation_bound(extension: Any) -> bool:
    """Whether ``extension`` is one of this package's operation-bound extensions.

    ``type()`` rather than ``isinstance``, for the reason
    ``schema.py::_is_extension`` uses it: a consumer object answers
    ``__class__`` with whatever it likes, and this predicate decides whose
    state the runner binds.
    """
    return issubclass(type(extension), _OperationBoundExtension)


def _binds_operation_state(execution_context: Any) -> bool:
    """Whether a package runner will claim an assignment naming this context.

    Only a ``DjangoSchema`` overrides the runner factory, so only a context
    belonging to one leads to a claim. The import is deferred because the schema
    module builds on this one; the read is guarded because the context is an
    engine object on the supported path and an arbitrary consumer object on
    every other.
    """
    from ..schema import DjangoSchema

    try:
        schema = getattr(execution_context, "schema", None)
    except Exception:
        return False
    return issubclass(type(schema), DjangoSchema)


class _OperationBoundExtension(SchemaExtension):
    """A ``SchemaExtension`` whose per-operation state is bound, not stored on it.

    Subclasses keep their configuration wherever their own authority holds it
    and put every value that belongs to ONE operation on the state
    :meth:`_new_operation_state` builds. What they must not do is call
    ``__init__`` without reaching this one: the carrier settled here is what
    makes ``execution_context`` answer for the operation being served rather
    than for the last one that assigned.
    """

    #: Refusal raised when a constructor runs twice on one instance. Overridden
    #: by subclasses whose second construction replaces something more specific
    #: than the binding carrier.
    _reconstruction_refusal = (
        "An extension is configured when it is constructed; re-running its "
        "__init__ on an instance a schema is already serving requests with "
        "would replace the state binding its operations are read through."
    )

    def __init__(self) -> None:
        """Settle this extension's binding carrier, once.

        An accepted instance is reachable from every resolver the schema
        serves, and so is its ``__init__``. A second call would mint a second
        carrier, leaving the runner binding one variable while every read
        answers from another - the operation state would then be permanently
        absent, which is the same disclosure a stale one is.
        """
        if _OPERATION_CARRIERS.settled(self):
            raise ConfigurationError(self._reconstruction_refusal)
        _OPERATION_CARRIERS.settle(
            self,
            ContextVar("django_strawberry_framework_operation_state", default=None),
        )

    @property
    def execution_context(self) -> Any:
        """The engine context of the operation this extension is answering here.

        Three answers in one order, and the order is the lifecycle: the state
        the package runner bound for this operation; else the assignment the
        engine just made and no runner has claimed yet; else the state a plain
        ``strawberry.Schema`` left on this instance. ``None`` when an extension
        is asked outside any operation, which is what a direct caller and a
        half-built request both are.
        """
        state = _carrier(self).get()
        if state is not None:
            return state.execution_context
        assignment = _pending_assignment(self)
        if assignment is not None:
            return assignment.execution_context
        compatibility = self.__dict__.get("_compatibility_state")
        return None if compatibility is None else compatibility.execution_context

    @execution_context.setter
    def execution_context(self, value: Any) -> None:
        """Take the engine's assignment as a handoff, never as the operation binding.

        For a ``DjangoSchema`` the assignment is recorded for the runner that
        is about to be built, and nothing is bound: the runner creates the
        operation's state from the context it is handed, so an inner execution
        cannot write into an outer operation's state on the way past.

        For any other schema no package runner exists to claim a handoff, so the
        state is created here and held on the instance. That is operation-local
        for the entries a raw ``strawberry.Schema`` is documented to use - a
        class, or a factory that builds a fresh extension - because the instance
        itself is per operation.
        """
        if _binds_operation_state(value):
            _PENDING_ASSIGNMENTS.set(
                (*_live_assignments(), _Assignment(ref(self), value)),
            )
            return
        self.__dict__["_compatibility_state"] = (
            None if value is None else self._new_operation_state(value)
        )

    def _new_operation_state(self, execution_context: Any) -> OperationState:
        """Build the state one operation on this extension is answered from."""
        return OperationState(execution_context)

    def _operation_state(self) -> OperationState | None:
        """The state this extension may write this operation's scratch on.

        ``None`` outside an operation - including inside the window between the
        engine's assignment and the runner's binding, which is deliberately not
        a place to accumulate anything: an assignment names a context and
        nothing else, so a value written against one would belong to no
        operation's teardown and would still be there for the next request.
        """
        state = _carrier(self).get()
        if state is not None:
            return state
        return self.__dict__.get("_compatibility_state")


def _live_assignments() -> tuple[_Assignment, ...]:
    """This task's pending assignments, minus any whose extension has died."""
    return tuple(entry for entry in _PENDING_ASSIGNMENTS.get() if entry.extension() is not None)


def _pending_assignment(extension: Any) -> _Assignment | None:
    """The most recent unclaimed assignment made to ``extension`` in this task."""
    for entry in reversed(_PENDING_ASSIGNMENTS.get()):
        if entry.extension() is extension:
            return entry
    return None


def _claim_operation_states(
    extensions: Iterable[Any],
    execution_context: Any,
) -> tuple[tuple[Any, OperationState], ...]:
    """Claim this operation's assignments and build the state each one becomes.

    Only the package's own operation-bound extensions are selected: a consumer
    extension is neither wrapped, copied, nor proxied, and keeps whatever
    upstream assigned it.

    The claim is all-or-nothing by construction. Every state is built first and
    the task's stack is rewritten once, at the end, so a state whose
    construction raises leaves every assignment exactly as it was for the caller
    upstream hands the failure to.

    An assignment is claimed only when it names THIS runner's context: an outer
    operation's handoff that some other schema never claimed stays where it is
    rather than being consumed by the next runner to come along.
    """
    pending = _live_assignments()
    claimed: set[int] = set()
    states: list[tuple[Any, OperationState]] = []
    for extension in extensions:
        if not _is_operation_bound(extension):
            continue
        for index in range(len(pending) - 1, -1, -1):
            entry = pending[index]
            if (
                index not in claimed
                and entry.extension() is extension
                and entry.execution_context is execution_context
            ):
                claimed.add(index)
                break
        states.append((extension, extension._new_operation_state(execution_context)))
    if claimed:
        _PENDING_ASSIGNMENTS.set(
            tuple(entry for index, entry in enumerate(pending) if index not in claimed),
        )
    return tuple(states)


def _bind(states: tuple[tuple[Any, OperationState], ...]) -> list[tuple[Any, Token[Any]]]:
    """Bind every state to its extension, unwinding what bound if one fails."""
    tokens: list[tuple[Any, Token[Any]]] = []
    try:
        for extension, state in states:
            tokens.append((extension, _carrier(extension).set(state)))
    except BaseException:
        _unbind(tokens)
        raise
    return tokens


def _unbind(tokens: list[tuple[Any, Token[Any]]]) -> None:
    """Reset every binding, in the reverse of the order it was made."""
    for extension, token in reversed(tokens):
        _carrier(extension).reset(token)


@contextlib.contextmanager
def _bound(states: tuple[tuple[Any, OperationState], ...]) -> Iterator[None]:
    """Hold ``states`` bound for the body."""
    tokens = _bind(states)
    try:
        yield
    finally:
        _unbind(tokens)


class _BoundScope:
    """One upstream extension scope, with this runner's states bound around it.

    Both context-manager protocols, over ONE binding primitive. A synchronous
    generator hook runs during asynchronous execution, so two implementations
    that each decided when to bind would be two chances to decide differently;
    the async methods here differ from the sync ones only in how they enter and
    exit the scope they wrap.

    Teardown order is fixed: the wrapped scope exits FIRST, so the LIFO unwind
    of every extension teardown still reads its own operation state, and the
    bindings are reset only once nothing is left to read them.
    """

    __slots__ = ("_scope", "_states", "_tokens")

    def __init__(self, states: tuple[tuple[Any, OperationState], ...], scope: Any) -> None:
        self._states = states
        self._scope = scope
        self._tokens: list[tuple[Any, Token[Any]]] = []

    def __enter__(self) -> None:
        self._tokens = _bind(self._states)
        try:
            self._scope.__enter__()
        except BaseException:
            _unbind(self._tokens)
            raise

    def __exit__(self, *exc_info: Any) -> Any:
        try:
            return self._scope.__exit__(*exc_info)
        finally:
            _unbind(self._tokens)

    async def __aenter__(self) -> None:
        self._tokens = _bind(self._states)
        try:
            await self._scope.__aenter__()
        except BaseException:
            _unbind(self._tokens)
            raise

    async def __aexit__(self, *exc_info: Any) -> Any:
        try:
            return await self._scope.__aexit__(*exc_info)
        finally:
            _unbind(self._tokens)


class DjangoExtensionsRunner(SchemaExtensionsRunner):
    """The runner ``DjangoSchema`` builds, and the owner of every operation binding.

    The runner is the only central point that sees the exact resolved extension
    list and the exact ``ExecutionContext`` together, after the engine's
    assignment loop and without calling a factory a second time - which is what
    lets one implementation cover a class entry, an accepted instance and a
    singleton-returning factory alike.

    Every scope the engine can read an extension's state through is bound here:
    the operation, which covers parsing, validation, execution, resolver
    middleware and every ordinary exception path; result collection, which
    upstream performs AFTER the synchronous operation teardown and, on the async
    path, both inside an early-return operation scope and after a completed one;
    and the streaming-result hook, whose binding the operation scope already
    covers and which is bound anyway so the contract is the runner's rather than
    one call ordering's.
    """

    def __init__(self, execution_context: Any, extensions: list[Any] | None = None) -> None:
        super().__init__(execution_context=execution_context, extensions=extensions)
        self._operation_states = _claim_operation_states(self.extensions, execution_context)

    def operation(self) -> Any:
        """The operation scope, with this operation's states bound around it."""
        return _BoundScope(self._operation_states, super().operation())

    def on_stream_result(self, result: Any) -> Any:
        """The streaming-result scope, bound so the runner's contract is complete."""
        return _BoundScope(self._operation_states, super().on_stream_result(result))

    def get_extensions_results_sync(self) -> dict[str, Any]:
        """Collect results with the operation's states bound.

        Upstream calls this after the synchronous operation teardown has
        already unwound. Without this scope an extension whose payload is
        operation state would answer for no operation at all - and the way back
        from that is to leave the payload on the shared extension, which is the
        stale-payload disclosure itself.
        """
        with _bound(self._operation_states):
            return super().get_extensions_results_sync()

    async def get_extensions_results(self, ctx: Any) -> dict[str, Any]:
        """Collect results with the operation's states bound, on the async path."""
        with _bound(self._operation_states):
            return await super().get_extensions_results(ctx)
