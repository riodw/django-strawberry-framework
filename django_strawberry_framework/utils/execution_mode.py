"""Which GraphQL executor is driving this resolver, as a fact rather than a guess.

A field factory that can serve both execution surfaces has to know which one is
running, because the two want different return values: the asynchronous executor
awaits a coroutine and consumes an ``AsyncIterable``, and the synchronous one
completes neither - it cancels the top-level awaitable, answers with its own
generic completion failure, and leaves every inner coroutine unawaited.

**Execution mode and ambient-loop presence are two facts, and they disagree.**
``strawberry.utils.inspect.in_async_context`` answers whether a loop is running
in this thread, which is the right question for "may I touch the ORM here" and
the wrong one for "which executor is driving me". ``Schema.execute_sync`` is
callable while a loop is running - most directly from a resolver inside an
asynchronous operation, which is a nesting shape this package supports - and on
that path the loop is running while the synchronous executor holds the
operation. A field that read the loop there would build exactly the value that
executor cannot complete.

**So the mode is carried, not sampled.** ``schema.py::DjangoSchema.get_extensions``
is handed the authoritative ``sync`` flag for every operation and puts it in the
chain; the runner binds it for the operation's whole lifetime
(``extensions/operation_state.py::DjangoExtensionsRunner``), around result
collection, around every streamed frame and around every stream resume. The
binding is a lease, so a task that merely COPIED the context stops reading the
mode when the operation ends rather than when its owner is collected; and it is
a token, so a nested operation restores its caller's mode on the way out.

Two questions are asked of that one fact, and they are different questions:

- :func:`operation_is_async` is the fact itself - which executor is driving -
  for code that has its own answer to every outcome.
- :func:`async_execution` is the dispatch decision: may this resolver hand back
  a value only the asynchronous executor can complete? It refuses the one
  combination where the honest answer is neither branch - the synchronous
  executor driving while a loop runs - rather than returning a coroutine the
  caller cannot await or driving the ORM on the event-loop thread.

**A plain ``strawberry.Schema`` never creates the package runner and is not
promised what it cannot be given.** Nothing binds a mode there, both readers
fall back to ambient dispatch, and the disagreement above remains reachable on
that schema exactly as upstream leaves it. ``DjangoSchema`` is the spelling that
makes the mode authoritative.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from enum import Enum
from typing import Any

from strawberry.utils.inspect import in_async_context

from .operation_lease import OperationLease
from .querysets import SyncMisuseError

__all__ = (
    "OperationMode",
    "async_execution",
    "bind_operation_mode",
    "current_operation_mode",
    "operation_is_async",
)


class OperationMode(Enum):
    """The GraphQL executor an operation is being driven by.

    Settled by the entry point the caller chose - ``execute_sync`` is
    :attr:`SYNC`, ``execute``, ``stream`` and ``subscribe`` are :attr:`ASYNC` -
    and never by anything about the thread the operation happens to run in.
    """

    SYNC = "sync"
    ASYNC = "async"


#: The mode bound for the operation running in this task, or ``None`` outside
#: every package runner.
#:
#: A lease rather than the mode itself, so the answer a copied context gives is
#: "nothing" the instant the operation ends. Reading a stale mode out of a
#: background task would be the same defect the ambient loop already has, only
#: harder to see.
_OPERATION_MODES: ContextVar[OperationLease[OperationMode] | None] = ContextVar(
    "django_strawberry_framework_operation_mode",
    default=None,
)


def bind_operation_mode(
    mode: OperationMode,
) -> tuple[ContextVar[Any], Token[Any], OperationLease[OperationMode]]:
    """Bind ``mode`` here and hand the owner back everything that undoes it.

    The variable, the token and the lease, because the runner that owns the
    operation owns all three: it resets the token in the task that made it and
    closes the lease on every exit path. Nothing here decides when that is.
    """
    lease: OperationLease[OperationMode] = OperationLease(mode)
    return _OPERATION_MODES, _OPERATION_MODES.set(lease), lease


def current_operation_mode() -> OperationMode | None:
    """The executor driving the operation here, or ``None`` when nothing bound one.

    ``None`` covers both "no package runner is involved" and "the runner that
    bound this context's mode has finished with it" - the same answer to every
    caller, because a context that merely copied a binding is not inside the
    operation that made it.
    """
    lease = _OPERATION_MODES.get()
    return None if lease is None else lease.held()


def operation_is_async() -> bool:
    """Whether the asynchronous executor is driving the operation here.

    Falls back to the ambient loop when no mode is bound, which is a plain
    ``strawberry.Schema`` and nothing else.
    """
    mode = current_operation_mode()
    if mode is None:
        return in_async_context()
    return mode is OperationMode.ASYNC


def async_execution() -> bool:
    """Whether this resolver may hand back a value only the async executor completes.

    True under the asynchronous executor. False under the synchronous one, which
    is the branch that finishes the work itself.

    The third state is a misuse rather than a branch: the synchronous executor
    driving while an event loop runs in this thread. Neither answer is available
    there - a coroutine or an async-only iterable is cancelled unawaited by that
    executor, and the synchronous branch would drive the ORM on the event-loop
    thread, which Django refuses further down with an error naming none of this.
    So it is refused here, where the call that caused it is still nameable.
    """
    mode = current_operation_mode()
    if mode is None:
        return in_async_context()
    if mode is OperationMode.ASYNC:
        return True
    if in_async_context():
        raise SyncMisuseError(
            "This operation is running under the synchronous GraphQL executor "
            "while an event loop is running in this thread, so a field cannot "
            "return a value only the asynchronous executor can complete. Use "
            "`await schema.execute(...)` for this operation, or run the "
            "synchronous call in a worker thread.",
        )
    return False
