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
only through a task-local binding while that runner owns it.** Two kinds of
state separate here and never merge:

- **Configuration** is long-lived, belongs to the extension or the schema, and
  is read-only to resolvers. It stays where it is (``utils/private_state.py``).
- **One operation's mutable state** belongs to the runner created for that
  operation: the engine context, and whatever scratch that extension keeps for
  the operation it is answering.

:class:`_OperationBoundExtension` is the base every framework extension whose
state is per-operation derives from, and ``execution_context`` becomes a read of
the state bound to that extension here. **The engine's assignment is compatibility
glue rather than an authority**: the runner is handed the same
``ExecutionContext`` directly, upstream runs no hook between the assignment loop
and ``schema.py::DjangoSchema.create_extensions_runner``, and so nothing is
recorded when a ``DjangoSchema`` operation assigns. A protocol that instead made
the assignment readable would have to survive a consumer entry's setter raising
midway through that loop - a failure with no package teardown to run, because no
runner exists yet - and would hold the refused request's context, its variables
and its schema for as long as the task lived. It would also be writable from a
resolver, which can assign a forged context naming the real schema as often as
it likes.

The binding carrier is itself security-relevant, so it is not an ordinary
attribute a resolver can replace or a second ``__init__`` can recreate: one
``ContextVar`` per extension identity, settled at construction behind
``utils/private_state.py::PrivateAuthority``. The authority may hold the
variable strongly because a ``ContextVar`` points back at nothing; the extension
itself it holds only weakly.

**What a carrier holds is a LEASE on a weak reference to the state, and the
runner is the state's one strong owner.** Resetting a token repairs the task
that bound it and nothing else: a task created while a binding is in force gets
a COPY of that context, which no later reset rewrites, so a resolver's
background task outliving the request would otherwise go on reading the
completed operation's context, variables and result, and hold them alive for as
long as it ran. Every scope here therefore binds a lease
(``utils/operation_lease.py::OperationLease``) and closes it on the way out, so
a copied binding stops answering at the instant the scope ends - which is not
the instant the runner dies, the runner deliberately outliving its own operation
scope to collect results. The weak reference inside the lease is the other half
of the same statement: the state lives exactly as long as the runner that built
it.

A runner also publishes the scope it is active in, because "nested" is a fact
about runners rather than about hook ordering: an operation started anywhere
inside another one - from a resolver, from a consumer extension's teardown, from
result collection - opens its first binding while a LIVE outer scope is bound,
and :func:`operation_is_nested` is how the optimizer knows not to treat the
outer request's context object as its own to clear and publish to. It is settled
at that first binding rather than at construction, because what a runner is
inside is decided where it starts running: a stream built inside one operation
and driven after it is inside nothing by then, and the closed lease its copied
context holds is what says so.

The runner also binds the operation's EXECUTOR MODE, for the same reason and
with the opposite timing. Which executor is driving is settled by the entry
point the caller chose, before anything runs, and the schema puts it in the
chain it built for this operation (:class:`_OperationModeMarker`); the runner
reads it once and binds it everywhere it binds state. It is bound rather than
sampled because ``execute_sync`` is callable while an event loop is running -
from a resolver inside an asynchronous operation, among other places - so the
ambient loop and the executor disagree exactly where a field factory must not
guess (``utils/execution_mode.py``).

**A stream is bound in the task that drives it.** An async iterator may be
advanced, thrown into and closed by whatever task holds it, and Python runs an
async generator's body in the context of the caller that resumed it - so every
binding made while one frame was produced is gone by the next, and a token
created for the first is not resettable from the second. The runner therefore
re-binds everything it owns around each ``__anext__``, ``asend``, ``athrow`` and
``aclose`` (:meth:`DjangoExtensionsRunner.resumed`), and the long-lived scopes
inside the generator bind nothing while the runner's own scope is already in
force. No token spans a yield, a frame produced in a second task enforces the
budget the first one armed, and a close from a third task tears that budget down
instead of leaving it armed.

**A plain ``strawberry.Schema`` is outside the runner's reach and is not
promised what it cannot be given.** That schema never calls the package's runner
factory, so the setter creates the state immediately and holds it on the
instance, which makes it operation-local exactly for the entries that are fresh
per operation - a class entry and a factory that builds one. A shared instance
on a raw schema remains outside the isolation guarantee; the documented spelling
for that schema is a class or a fresh factory.

**That branch is for an extension no ``DjangoSchema`` has ever managed, and
nothing puts one back into it.** An extension a package runner has resolved - or
that the engine has handed a ``DjangoSchema``'s context - is recorded as
package-managed, and from then on its setter ignores every assignment of every
shape: ``None``, a raw-schema-shaped object, a forged context naming the real
schema, an arbitrary graph. The alternative is a resolver reaching any shared
framework extension, assigning an object of its own, and making every direct
read outside an operation answer with that object - and keeping whatever it
reaches alive - for the life of the process. Marking is one-way because the
question it answers is one-way: a shared instance that has served a
``DjangoSchema`` operation is not an instance a raw schema can be given
per-operation state through.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterable, Iterator
from contextvars import ContextVar, Token
from typing import Any, NamedTuple
from weakref import ref

from strawberry.extensions.base_extension import SchemaExtension
from strawberry.extensions.runner import SchemaExtensionsRunner

from ..exceptions import ConfigurationError
from ..utils.execution_mode import OperationMode, bind_operation_mode
from ..utils.operation_lease import OperationLease
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
    ``__weakref__`` is declared because the binding a hook reads through is a
    weak reference to this object, which is what makes the runner that built it
    the only thing keeping it - and the request it names - alive.
    """

    __slots__ = ("__weakref__", "_resumed_bindings", "execution_context")

    def __init__(self, execution_context: Any) -> None:
        self.execution_context = execution_context
        self._resumed_bindings: list[tuple[ContextVar[Any], Any]] = []

    def rebind_on_resume(
        self,
        variable: ContextVar[Any],
        value: Any,
        token: Token[Any],
    ) -> bool:
        """Have the runner bind ``variable`` to ``value`` again on every resume.

        For the task-local state an extension arms for the WHOLE operation
        rather than for one hook - the resource budget is the one the package
        arms - because a streamed operation's later frames run in whatever task
        drives them and inherit none of it. The value registered is expected to
        be a lease its arming scope still owns: the runner re-binds it, and the
        scope that armed it is what ends it.

        Registered on the state rather than on the runner, because the state is
        what an extension has a handle on, and because a registration is then
        scoped to exactly one operation by construction.

        ``token`` is the one that armed the value, and the registration hands it
        to the resume this arming is happening inside. Whole-operation state is
        armed DURING a frame rather than before one, so a resume that only bound
        what was registered before it started would leave this value set in the
        task that drove the frame, with no token to take it back: the caller
        would go on answering with a paused operation's budget while no operation
        of its own was running. Resume lifetime and operation lifetime are
        different things, and this is the point they are told apart at - the
        value stays armed for the operation, and stays bound only while some
        task is driving it.

        What comes back says whether a resume took the binding over, which is
        the caller's answer to who ends it.
        """
        self._resumed_bindings.append((variable, value))
        return _register_resumed_binding(variable, token)

    def resumed_bindings(self) -> tuple[tuple[ContextVar[Any], Any], ...]:
        """The variables an extension asked the runner to bind again on resume."""
        return tuple(self._resumed_bindings)


class _RunnerScope(NamedTuple):
    """The scope one runner binds around everything it owns.

    ``nested`` is settled when the runner opens its FIRST binding, from whether
    a live outer scope was bound in that task. It is a property of the RUNNER
    rather than of the hook asking, so an operation started from a resolver,
    from a consumer extension's teardown and from result collection all answer
    the same way; and it is read from a live lease rather than from a bound
    value, so a runner started in a task that merely COPIED an outer operation's
    context is top-level, which is what it is.

    ``mode`` is the opposite kind of fact and is settled at construction: which
    executor is driving this operation is decided by the entry point the caller
    chose, before anything runs, and the schema puts it in the chain
    (:class:`_OperationModeMarker`). ``None`` is a runner built for a chain
    carrying no marker, which is a schema that is not a ``DjangoSchema`` or one
    whose subclass builds its own chain; the readers then fall back to ambient
    dispatch, exactly as upstream leaves it.

    One object per runner, identity included: a scope already bound to this
    exact object is this runner's own, which is how a scope inside the runner's
    stream resume - or inside its own operation - knows it has nothing to bind.
    """

    nested: bool
    mode: OperationMode | None


#: One binding carrier per operation-bound extension, settled at construction.
#:
#: The variable holds a lease on a weak reference to the state bound for the
#: operation this extension is answering IN THIS TASK, and nothing else: it is
#: set by the package runner, closed and reset by it, so two operations on one
#: extension never see each other's state and a task that copied the binding
#: sees neither.
#:
#: Held here rather than in an attribute because the carrier decides what
#: ``execution_context`` answers with, and an attribute holding it is one a
#: resolver replaces - pointing the read at a variable the runner never binds,
#: which answers every later operation with whatever that resolver put there.
#: A ``ContextVar`` points back at nothing, so holding one strongly retains
#: nothing but the variable; the extension it belongs to is held weakly, and its
#: entry is dropped when the extension dies.
_OPERATION_CARRIERS: PrivateAuthority[ContextVar[Any]] = PrivateAuthority()

#: Every extension a ``DjangoSchema`` has managed, and nothing else.
#:
#: The record is what closes the compatibility setter. An extension the package
#: runner binds gets its operation state from that runner and needs no other
#: signal, so once one has been marked here every assignment to it is ignored -
#: and the assignments that matter are the ones no engine makes: a resolver
#: holds the shared instance through ``info.schema``'s extension configuration
#: and can hand it any object at all, which without this mark the setter would
#: accept as a raw-schema compatibility state, answer direct reads outside the
#: operation with, and hold for the life of the process.
#:
#: Filed behind the same authority as the carriers, for the same two reasons: a
#: flag on the extension is a flag a resolver clears, and a module-global
#: holding the extension strongly would keep every schema it is configured on
#: alive. A ``bool`` payload points at nothing.
_PACKAGE_MANAGED: PrivateAuthority[bool] = PrivateAuthority()

#: The runner scope bound in this task, or ``None`` outside every runner.
#:
#: One variable for every runner rather than one per runner, because the
#: question it answers is about the innermost one: an operation runs nested when
#: a live scope was already bound as its runner opened its first binding.
_RUNNER_SCOPES: ContextVar[OperationLease[_RunnerScope] | None] = ContextVar(
    "django_strawberry_framework_runner_scope",
    default=None,
)

#: The bindings the resume running in this task is accountable for, or ``None``
#: when no resume is driving anything here.
#:
#: A resume binds what the operation registered BEFORE it started, and an
#: operation registers its whole-operation state during its first frame - so the
#: first resume of every streamed operation ends with one binding it never made.
#: The registrar is how it finds out: an extension arming such a value while
#: this is set hands over the token, and the resume takes the value back on its
#: way out along with everything it bound itself.
_RESUME_REGISTRARS: ContextVar[list[_Binding] | None] = ContextVar(
    "django_strawberry_framework_resume_registrar",
    default=None,
)


def _register_resumed_binding(variable: ContextVar[Any], token: Token[Any]) -> bool:
    """Hand ``token`` to the resume driving this task, if one is; say whether it took it.

    Nothing to hand it to on the ordinary operation path, where the scope that
    armed the value is also the scope that ends it, in the task that made the
    token. A plain ``strawberry.Schema`` has no runner and reaches this the same
    way.
    """
    registrar = _RESUME_REGISTRARS.get()
    if registrar is None:
        return False
    registrar.append(_Binding(variable, token, None, adopted=True))
    return True


class _OperationModeMarker(SchemaExtension):
    """The operation's executor mode, carried into the chain the schema built.

    ``schema.py::DjangoSchema.get_extensions`` is the one place that is handed
    the authoritative ``sync`` flag, and ``create_extensions_runner`` is the one
    place that sees the resolved chain and this operation's engine context
    together. Nothing upstream passes the flag from the first to the second, and
    recording it on the schema would be one slot two concurrent operations
    write - the defect this whole module exists to close. So the fact travels
    the way every other per-operation fact travels: as a member of the chain
    that was built for this operation and nothing else.

    It implements no hook. Upstream assigns ``execution_context`` on it with
    every other resolved member and then finds nothing to call, which is the
    whole contract: the marker is read once, by the runner, out of the list it
    arrived in.
    """

    def __init__(self, mode: OperationMode) -> None:
        super().__init__()
        self.mode = mode


def _declared_operation_mode(extensions: Iterable[Any]) -> OperationMode | None:
    """The mode the chain declares, or ``None`` when no chain member declares one.

    Exact type, and the first one found: a consumer extension that grew a
    ``mode`` attribute declares nothing, and a chain the package built carries
    exactly one marker.
    """
    for extension in extensions:
        if type(extension) is _OperationModeMarker:
            return extension.mode
    return None


def _live_scope() -> _RunnerScope | None:
    """The scope bound and still open here, or ``None``.

    ``None`` covers both "no runner bound one" and "the runner that bound one
    has finished with it", which are the same answer to every caller: a context
    that merely COPIED a binding is not inside the operation that made it.
    """
    lease = _RUNNER_SCOPES.get()
    return None if lease is None else lease.held()


def operation_is_nested() -> bool:
    """Whether the operation running here belongs to a runner inside another one.

    ``False`` outside every package runner, which is what a direct call into a
    resolver and a plain ``strawberry.Schema`` operation both are: neither has a
    runner, so neither is inside one. ``False`` again in a task that copied a
    binding and outlived it, for the same reason the state itself is gone there.
    """
    scope = _live_scope()
    return scope is not None and scope.nested


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


def _bound_state(extension: Any) -> OperationState | None:
    """The state bound to ``extension`` here, or ``None`` outside that binding.

    Two conditions, one answer. The lease is closed when the scope that bound it
    ends, so a context that copied the binding earlier reads nothing even while
    the runner still owns the state for result collection; and the reference
    inside a live lease stops resolving when the runner itself is gone.
    """
    lease = _carrier(extension).get()
    if lease is None:
        return None
    binding = lease.held()
    return None if binding is None else binding()


def _is_package_managed(extension: Any) -> bool:
    """Whether a ``DjangoSchema`` has already managed ``extension``."""
    return _PACKAGE_MANAGED.settled(extension)


def _mark_package_managed(extension: Any) -> None:
    """Record ``extension`` as one the package runner owns the state of.

    Also drops whatever the compatibility branch had left on the instance: an
    extension that served a raw ``strawberry.Schema`` before being installed on
    a ``DjangoSchema`` keeps no state from that arrangement, and a read outside
    an operation answers ``None`` rather than with an earlier schema's context.
    """
    if not _PACKAGE_MANAGED.settled(extension):
        _PACKAGE_MANAGED.settle(extension, True)
    extension.__dict__.pop("_compatibility_state", None)


def _is_operation_bound(extension: Any) -> bool:
    """Whether ``extension`` is one of this package's operation-bound extensions.

    ``type()`` rather than ``isinstance``, for the reason
    ``schema.py::_is_extension`` uses it: a consumer object answers
    ``__class__`` with whatever it likes, and this predicate decides whose
    state the runner binds.
    """
    return issubclass(type(extension), _OperationBoundExtension)


def _binds_operation_state(execution_context: Any) -> bool:
    """Whether a package runner will build this context's operation state.

    Only a ``DjangoSchema`` overrides the runner factory, so only a context
    belonging to one gets its state from the runner. The import is deferred
    because the schema module builds on this one; the read is guarded because
    the context is an engine object on the supported path and an arbitrary
    consumer object on every other.
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

        Two answers in one order: the state the package runner bound for this
        operation, else the state a plain ``strawberry.Schema`` left on this
        instance. ``None`` when an extension is asked outside any operation,
        which is what a direct caller and a half-built request both are - the
        window between the engine's assignment and the runner's binding
        included, because an assignment names a context and confers nothing.
        """
        state = self._operation_state()
        return None if state is None else state.execution_context

    @execution_context.setter
    def execution_context(self, value: Any) -> None:
        """Take the engine's assignment for the schemas it is the only signal for.

        Under a ``DjangoSchema`` the runner is handed this same context and
        builds every operation state from it, so the assignment records
        nothing: what is not written cannot be read for the wrong operation,
        cannot be left behind by a failure upstream, and cannot be forged by a
        resolver assigning a context of its own. The assignment does say which
        extensions that schema has managed, which is the one thing recorded.

        For any other schema this IS the only signal, so the state is created
        here and held on the instance. That is operation-local for the entries a
        raw ``strawberry.Schema`` is documented to use - a class, or a factory
        that builds a fresh extension - because the instance itself is per
        operation.

        An extension the package has managed takes neither branch. Every
        assignment to it is ignored whatever its shape, because the runner is
        its state's only authority and the assignments left over are the ones a
        resolver makes: an arbitrary object it wants direct reads answered with,
        and the graph behind that object kept for the life of the process.
        """
        if _is_package_managed(self):
            return
        if _binds_operation_state(value):
            _mark_package_managed(self)
            return
        self.__dict__["_compatibility_state"] = (
            None if value is None else self._new_operation_state(value)
        )

    def _new_operation_state(self, execution_context: Any) -> OperationState:
        """Build the state one operation on this extension is answered from."""
        return OperationState(execution_context)

    def _operation_state(self) -> OperationState | None:
        """The state this extension may write this operation's scratch on.

        ``None`` outside an operation, and ``None`` again in a task that copied
        a binding and outlived the scope that made it: the state a completed
        operation wrote is not state a later reader may still answer from.

        The compatibility state answers only for an extension the package has
        never managed. For one it has, the runner's binding is the whole answer,
        so an instance shared between a ``DjangoSchema`` and a raw one reads as
        outside an operation rather than as inside the raw schema's.
        """
        state = _bound_state(self)
        if state is not None:
            return state
        if _is_package_managed(self):
            return None
        return self.__dict__.get("_compatibility_state")


def _operation_states(
    extensions: Iterable[Any],
    execution_context: Any,
) -> tuple[tuple[Any, OperationState], ...]:
    """Build the state each operation-bound extension answers this operation from.

    Only the package's own operation-bound extensions are selected: a consumer
    extension is neither wrapped, copied, nor proxied, and keeps whatever
    upstream assigned it.

    Building the state is also what records the extension as package-managed.
    Every supported spelling arrives here - a class entry resolved fresh, an
    accepted instance, a factory's singleton - so this is the one point that
    sees them all, and an entry whose engine assignment was skipped or refused
    is marked exactly the same way.
    """
    selected = tuple(extension for extension in extensions if _is_operation_bound(extension))
    for extension in selected:
        _mark_package_managed(extension)
    return tuple(
        (extension, extension._new_operation_state(execution_context)) for extension in selected
    )


class _Binding(NamedTuple):
    """One variable this scope set, and what it has to undo on the way out.

    ``lease`` is the one the scope minted and is therefore the one it closes;
    ``None`` marks a value the scope only re-bound, whose lease belongs to the
    scope that armed it and outlives this one.

    ``adopted`` marks a binding some other scope made inside this one and handed
    over (:func:`_register_resumed_binding`). Undoing it is the same statement -
    the token is reset in the task that made it, which is this one - but the
    scope that armed it may have reset it already, and that is not this scope's
    bookkeeping gone wrong.
    """

    variable: ContextVar[Any]
    token: Token[Any]
    lease: OperationLease[Any] | None
    adopted: bool = False


def _bind(
    scope: _RunnerScope,
    states: tuple[tuple[Any, OperationState], ...],
    *,
    registrar: bool = False,
) -> list[_Binding]:
    """Bind the runner scope and every state, unwinding what bound if one fails.

    Nothing is bound when ``scope`` is already the live scope here, which is the
    runner meeting its own bindings: the stream resume holds them while the
    generator's operation scope enters, and the operation scope holds them while
    the streaming-result scope does. Rebinding would be harmless; the tokens it
    would leave are not, because the inner scope's exit can run in a task that
    cannot reset them - and every one of those cases is a scope that spans a
    ``yield``.

    ``registrar`` opens this scope to bindings made inside it and handed over,
    which only a resume needs: it is the one scope whose body arms
    whole-operation state the scope did not bind itself. It is set last, so the
    handed-over bindings sit after everything bound here and come off first.
    """
    if _already_bound(scope):
        return []
    bindings: list[_Binding] = []
    try:
        lease: OperationLease[Any] = OperationLease(scope)
        bindings.append(_Binding(_RUNNER_SCOPES, _RUNNER_SCOPES.set(lease), lease))
        if scope.mode is not None:
            bindings.append(_Binding(*bind_operation_mode(scope.mode)))
        for extension, state in states:
            carrier = _carrier(extension)
            binding: OperationLease[Any] = OperationLease(ref(state))
            bindings.append(_Binding(carrier, carrier.set(binding), binding))
            for variable, value in state.resumed_bindings():
                bindings.append(_Binding(variable, variable.set(value), None))
        if registrar:
            bindings.append(
                _Binding(_RESUME_REGISTRARS, _RESUME_REGISTRARS.set(bindings), None),
            )
    except BaseException:
        _unbind(bindings)
        raise
    return bindings


def _already_bound(scope: _RunnerScope) -> bool:
    """Whether ``scope`` is the scope bound and open in this context.

    Identity, not equality: one runner has one scope object, so this is true
    only for a scope the same runner already has in force here.
    """
    lease = _RUNNER_SCOPES.get()
    return lease is not None and lease.held() is scope


def _reset_binding(variable: ContextVar[Any], token: Token[Any]) -> None:
    """Reset one binding, in the context that made it.

    Every binding here is reset where it was created: a scope that spans a
    ``yield`` binds nothing, because the stream resume around it already holds
    this runner's bindings in the driving task (:func:`_bind`), so no token of
    this module's crosses a task. A token that cannot be reset here is a
    bookkeeping defect, and Python's own ``ValueError`` / ``RuntimeError`` is
    the right answer to it.
    """
    variable.reset(token)


def _unbind(bindings: list[_Binding]) -> None:
    """Close every lease this scope minted and reset every binding it made.

    Closing comes first and happens for every binding, because that is the half
    a context copied from this one can observe: the task that copied it never
    sees the reset, and must stop reading the moment the scope ends rather than
    when the owner is eventually collected. The reset is what gives THIS context
    its enclosing operation back, and each one is attempted independently so a
    token this context cannot reset does not strand the ones after it.
    """
    for binding in reversed(bindings):
        if binding.lease is not None:
            binding.lease.close()
        if binding.adopted:
            _reset_adopted_binding(binding.variable, binding.token)
        else:
            _reset_binding(binding.variable, binding.token)


def _reset_adopted_binding(variable: ContextVar[Any], token: Token[Any]) -> None:
    """Take back a binding this scope adopted, restoring its exact predecessor.

    The token was made in this task, so the reset belongs here and restores
    whatever the caller had - the enclosing operation's value for a stream
    driven inside another operation, and nothing bound for an ordinary caller.

    Already used is the one tolerated answer, and it means the scope that armed
    the value also ENDED it inside this same resume: a streamed operation whose
    whole life fits in one frame arms and disarms between the same pair of
    ``yield``s. The variable is already back at the value this reset would put
    there, so there is nothing left to do and nothing wrong.
    """
    # RuntimeError: the arming scope ended inside this one and reset it already.
    with contextlib.suppress(RuntimeError):
        variable.reset(token)


@contextlib.contextmanager
def _bound(
    scope: _RunnerScope,
    states: tuple[tuple[Any, OperationState], ...],
    *,
    registrar: bool = False,
) -> Iterator[None]:
    """Hold ``scope`` and ``states`` bound for the body."""
    bindings = _bind(scope, states, registrar=registrar)
    try:
        yield
    finally:
        _unbind(bindings)


class _BoundScope:
    """One upstream extension scope, with this runner's bindings around it.

    Both context-manager protocols, over ONE binding primitive. A synchronous
    generator hook runs during asynchronous execution, so two implementations
    that each decided when to bind would be two chances to decide differently;
    the async methods here differ from the sync ones only in how they enter and
    exit the scope they wrap.

    Teardown order is fixed: the wrapped scope exits FIRST, so the LIFO unwind
    of every extension teardown still reads its own operation state, and the
    bindings are reset only once nothing is left to read them.
    """

    __slots__ = (
        "_bindings",
        "_runner_scope",
        "_scope",
        "_states",
    )

    def __init__(
        self,
        runner_scope: _RunnerScope,
        states: tuple[tuple[Any, OperationState], ...],
        scope: Any,
    ) -> None:
        self._runner_scope = runner_scope
        self._states = states
        self._scope = scope
        self._bindings: list[_Binding] = []

    def __enter__(self) -> None:
        self._bindings = _bind(self._runner_scope, self._states)
        try:
            self._scope.__enter__()
        except BaseException:
            _unbind(self._bindings)
            raise

    def __exit__(self, *exc_info: Any) -> Any:
        try:
            return self._scope.__exit__(*exc_info)
        finally:
            _unbind(self._bindings)

    async def __aenter__(self) -> None:
        self._bindings = _bind(self._runner_scope, self._states)
        try:
            await self._scope.__aenter__()
        except BaseException:
            _unbind(self._bindings)
            raise

    async def __aexit__(self, *exc_info: Any) -> Any:
        try:
            return await self._scope.__aexit__(*exc_info)
        finally:
            _unbind(self._bindings)


class _ResumedStream:
    """A streamed operation's frames, each produced with the runner bound.

    An async iterator belongs to whoever holds it: a transport may advance it
    from one task, close it from another, and cancel it from a third. Python
    runs an async generator's body in the context of the caller that resumed it,
    so a binding made while frame one was produced is simply absent for frame
    two, and the token that made it is not resettable from there. Without this
    wrapper the second frame runs with no armed budget and no runner scope - the
    operation's own resolvers enforcing the fallback rather than the policy the
    request was admitted under - and the close runs with nothing to tear down.

    So the runner is bound around every method that can drive the generator, in
    the task that drives it. Nothing here enters an extension hook: the scopes
    inside the generator are upstream's, they run exactly as often as upstream
    runs them, and they bind nothing while this wrapper's bindings are in force.

    ``__slots__`` because this object stands where a transport expects an async
    generator, and an attribute it grows by accident is one nobody reads back.
    """

    __slots__ = ("_runner", "_source")

    def __init__(self, runner: DjangoExtensionsRunner, source: Any) -> None:
        self._runner = runner
        self._source = source

    def __aiter__(self) -> _ResumedStream:
        """Answer for itself, so the bindings cover every frame the caller pulls."""
        return self

    async def __anext__(self) -> Any:
        """Produce the next frame with this operation bound in the calling task."""
        with self._runner.resumed():
            return await self._source.__anext__()

    async def asend(self, value: Any) -> Any:
        """Resume the stream with ``value``, bound in the calling task."""
        with self._runner.resumed():
            return await self._source.asend(value)

    async def athrow(self, *args: Any, **kwargs: Any) -> Any:
        """Throw into the stream, bound so its teardown reads its own operation."""
        with self._runner.resumed():
            return await self._source.athrow(*args, **kwargs)

    async def aclose(self) -> Any:
        """Close the stream, bound so every scope it unwinds tears its own state down.

        The one method whose caller is routinely not the task that produced a
        frame - a cancelled subscription is closed by the connection - and the
        one where being unbound is not a stale read but a scope that never ends:
        the budget stays armed and the operation's state stays reachable in
        whatever context does the closing.
        """
        with self._runner.resumed():
            return await self._source.aclose()


class DjangoExtensionsRunner(SchemaExtensionsRunner):
    """The runner ``DjangoSchema`` builds, and the owner of every operation binding.

    The runner is the only central point that sees the exact resolved extension
    list and the exact ``ExecutionContext`` together, after the engine's
    assignment loop and without calling a factory a second time - which is what
    lets one implementation cover a class entry, an accepted instance and a
    singleton-returning factory alike. It is also the one object that knows the
    operation's full lifetime, so the states it builds live exactly as long as
    it does and every binding is a lease on a weak reference to one of them.

    Every scope the engine can read an extension's state through is bound here:
    the operation, which covers parsing, validation, execution, resolver
    middleware and every ordinary exception path; result collection, which
    upstream performs AFTER the synchronous operation teardown and, on the async
    path, both inside an early-return operation scope and after a completed one;
    the streaming-result hook, whose binding the operation scope already covers
    and which is bound anyway so the contract is the runner's rather than one
    call ordering's; and every resumption of a streamed operation, which is the
    only one of them that can happen in a task the operation never started in.
    """

    def __init__(self, execution_context: Any, extensions: list[Any] | None = None) -> None:
        super().__init__(execution_context=execution_context, extensions=extensions)
        self._operation_states = _operation_states(self.extensions, execution_context)
        self._operation_mode = _declared_operation_mode(self.extensions)
        self._runner_scope: _RunnerScope | None = None

    def _scope(self) -> _RunnerScope:
        """This runner's scope, settled the first time it binds anything.

        Not at construction. Upstream builds the runner before the operation
        begins and a streamed one is driven long afterwards, so construction is
        neither where the operation starts nor, for a stream, in the task that
        will run it. The first binding is both, and what it reads is a live
        outer lease: a runner whose task merely inherited a copy of an ended
        operation's context is inside nothing.
        """
        if self._runner_scope is None:
            self._runner_scope = _RunnerScope(
                nested=_live_scope() is not None,
                mode=self._operation_mode,
            )
        return self._runner_scope

    def operation(self) -> Any:
        """The operation scope, with this operation's bindings around it."""
        return _BoundScope(self._scope(), self._operation_states, super().operation())

    def on_stream_result(self, result: Any) -> Any:
        """The streaming-result scope, bound so the runner's contract is complete."""
        return _BoundScope(self._scope(), self._operation_states, super().on_stream_result(result))

    @contextlib.contextmanager
    def resumed(self) -> Iterator[None]:
        """Hold this operation bound for one resumption of its streamed result.

        What :class:`_ResumedStream` wraps every drive of the generator in, and
        the only binding scope whose caller is not the operation's own machinery
        - which is why it exists: the task that pulls a frame, throws into the
        stream, or closes it is the transport's, and every binding the previous
        frame made lives in a context that task does not have.
        """
        with _bound(self._scope(), self._operation_states, registrar=True):
            yield

    def resumed_stream(self, source: Any) -> _ResumedStream:
        """Wrap ``source`` so every frame it yields is produced with this operation bound."""
        return _ResumedStream(self, source)

    def get_extensions_results_sync(self) -> dict[str, Any]:
        """Collect results with the operation's bindings in force.

        Upstream calls this after the synchronous operation teardown has
        already unwound. Without this scope an extension whose payload is
        operation state would answer for no operation at all - and the way back
        from that is to leave the payload on the shared extension, which is the
        stale-payload disclosure itself.
        """
        with _bound(self._scope(), self._operation_states):
            return super().get_extensions_results_sync()

    async def get_extensions_results(self, ctx: Any) -> dict[str, Any]:
        """Collect results with the operation's bindings in force, on the async path."""
        with _bound(self._scope(), self._operation_states):
            return await super().get_extensions_results(ctx)
