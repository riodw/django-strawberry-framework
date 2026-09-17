"""Revocable access to state that belongs to one operation.

Every task-local answer this package gives is reached through a ``ContextVar``,
and a ``ContextVar`` cannot be revoked. ``asyncio.create_task`` copies the whole
context at creation, and ``Token`` reset rewrites only the context the token was
created in, so a resolver's background task that outlives the request goes on
reading the values that were in force when it started: the operation it is
inside, the budget bounding it, the optimizer's plan for it. A copy is also a
strong reference, so those values stay alive as long as the task does.

**A lease is what a copied context holds instead.** The owner of the state puts
it in a lease, binds the LEASE, and closes the lease when its scope ends. Every
reader asks the lease rather than the variable, so:

- the scope's end is observable from a context that was copied before it, which
  a token reset is not;
- the state stops being reachable at that instant rather than when the last
  copied context is collected, so a request's plans, querysets and variables are
  not retained by a background task;
- a value read out of a copied binding can never be mistaken for an active one,
  because the only thing a closed lease answers is "nothing".

Token reset is still how an enclosing operation gets its own answer back when a
nested one ends. It is cleanup, not authority: the lease decides whether what a
context holds is still live, and the reset decides what the OWNING context sees
next.

``orders/sets.py::_NormalizationLedger`` is the same rule written for one
subsystem, and stays where it is: it tombstones a mutable ledger under its own
lock because a descendant may still be publishing into it. A lease holds one
payload and answers reads, so closing it is one store; a payload with mutable
containers of its own is cleared by its owner, which is the only code that knows
what the containers are.
"""

from __future__ import annotations

from typing import Generic, TypeVar

__all__ = ("OperationLease",)

PayloadT = TypeVar("PayloadT")


class OperationLease(Generic[PayloadT]):
    """One scope's revocable handle on the state that scope owns.

    Bound in place of the payload, and read through :meth:`held`. Before the
    scope resets its binding it calls :meth:`close`, after which every context
    still holding this lease - the owner's own, and every copy a task took of it
    - reads ``None``.

    ``__slots__`` with one payload slot, so closing is a single store: a reader
    in another thread or task sees either the payload or nothing, never a
    half-closed lease, and there is no second flag for a close to leave
    inconsistent with the first. The slot is private because a lease is
    authority for the scope that made it: what it holds is settled at
    construction and the only supported change is closing it.
    """

    __slots__ = ("__weakref__", "_payload")

    def __init__(self, payload: PayloadT) -> None:
        self._payload = payload

    def held(self) -> PayloadT | None:
        """The payload, or ``None`` once the scope that owned it has ended."""
        return self._payload

    def close(self) -> None:
        """End the lease, here and in every context that copied it.

        Idempotent, because the owner closes on every exit path and a scope
        unwound twice is not a reason to raise: the answer after the first close
        is already the final one.
        """
        self._payload = None  # type: ignore[assignment]
