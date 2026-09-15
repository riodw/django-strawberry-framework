"""State an object owns, that consumer code can neither read out nor forge.

``schema.py::DjangoSchema`` and
``extensions/resource_policy.py::DjangoResourcePolicyExtension`` both need to
settle a piece of configuration once and read it back on every later operation.
Both are handed to every resolver in every request - one as ``info.schema``, the
other through that schema's extension list - and both are process-lived, so an
ordinary attribute holding what enforces a request is a name one resolver can
write to widen or disarm every LATER request the process serves.

Two properties have to hold at once, and each rules out the obvious home for
the other:

- **Lifetime.** The state must die with its owner, and an owner must stay
  collectable. A module-global mapping holding the state strongly is a root:
  extension objects and bound-method factories point back at their schema, so
  rooting one schema's configuration roots the schema, its execution context,
  and the last request's variables with it - and a weak KEY cannot help,
  because the chain that keeps the referent alive runs through the value.
- **Authority.** The state must not be replaceable by whoever can reach the
  owner. An instance attribute is exactly that: ``owner.__dict__[name] = ...``
  writes it whatever the attribute descriptor in front of it does.

So the owner holds the state - which is the correct lifetime, the state being
part of what the owner IS - and this module holds the evidence of which object
was accepted: a weak reference to the state, filed under the owner's identity.
Reading verifies the stored object against that reference, so a forged
replacement is not mistaken for the accepted one; it answers ``None``, and each
caller decides what a missing record means (both current callers fail closed).
Both references are weak, so nothing here keeps an owner alive.

The key is ``id()``, not the owner itself: a ``WeakKeyDictionary`` finds its
keys by hash and equality, and both of those are methods a consumer subclass may
define - two distinct schemas that compare equal would share one entry, and one
that defines ``__eq__`` without a hash could not be filed at all. Which object
owns a record is a question about identity, and ``id()`` answers it without
calling anything the consumer wrote. An ``id()`` is unique among LIVE objects
only, so the weak reference's own callback removes an entry only while that
entry is still the one its reference was filed under: by the time a dead owner's
callback runs, the key may already name the successor that reused the address.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from weakref import ReferenceType, ref

__all__ = ("PrivateState",)

StateT = TypeVar("StateT")


class PrivateState(Generic[StateT]):
    """One kind of accepted state, for every object of one kind that carries it.

    ``attribute`` is the name the state is held under on its owner. It is read
    back only through :meth:`recall`, which is what makes writing it directly a
    detectable forgery rather than a configuration change.
    """

    def __init__(self, attribute: str) -> None:
        self._attribute = attribute
        self._accepted: dict[int, tuple[ReferenceType[Any], ReferenceType[StateT]]] = {}

    def remember(self, owner: Any, state: StateT) -> None:
        """Accept ``state`` as ``owner``'s, replacing whatever it carried before."""
        owner.__dict__[self._attribute] = state
        key = id(owner)

        def forget(dead: ReferenceType[Any]) -> None:
            entry = self._accepted.get(key)
            if entry is not None and entry[0] is dead:
                del self._accepted[key]

        self._accepted[key] = (ref(owner, forget), ref(state))

    def recall(self, owner: Any) -> StateT | None:
        """The state ``owner`` was accepted with, or ``None`` if it carries none.

        ``None`` is also the answer for state that was replaced behind the
        attribute, and for an entry filed under an identity that has since been
        reused: the stored object is what the accepted weak reference points at,
        or it is not the accepted one.
        """
        entry = self._accepted.get(id(owner))
        if entry is None or entry[0]() is not owner:
            return None
        state = owner.__dict__.get(self._attribute)
        return state if entry[1]() is state else None
