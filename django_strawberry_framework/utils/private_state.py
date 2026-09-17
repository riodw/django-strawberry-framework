"""State an object owns, that consumer code can neither read out nor forge.

``schema.py::DjangoSchema`` and
``extensions/resource_policy.py::DjangoResourcePolicyExtension`` both need to
settle configuration once and read it back on every later operation. Both are
handed to every resolver in every request - one as ``info.schema``, the other
through that schema's extension list - and both are process-lived, so an
ordinary attribute holding what enforces a request is a name one resolver can
write to widen or disarm every LATER request the process serves.

Two demands pull in opposite directions, and which one wins depends on what the
state IS:

- **Authority.** The values a bound is read from must survive whatever a
  resolver does to the object that carries them. An instance attribute cannot:
  ``owner.__dict__[name] = ...`` replaces it past any descriptor, ``del``
  removes it, and the object the attribute answered with is itself writable -
  a frozen dataclass still admits ``policy.__dict__[bound] = wider``. Detecting
  the tamper and then continuing under whatever the fallback selects is not
  preservation: the fallback may be wider than the policy the deployment
  accepted.
- **Lifetime.** An owner must stay collectable. A module-global mapping holding
  an owner's state STRONGLY is a garbage-collection root, and a schema's
  extension configuration points back at the schema - an extension instance
  reaches it through the execution context, and ``extensions=[self.factory]``
  is a bound method - so rooting that configuration roots the schema, its last
  execution context, and that request's variables for the life of the process.
  A weak KEY does not help when the chain back to the referent runs through the
  value.

The two classes here are those two answers, and each kind of state goes to the
one its own shape admits:

- :class:`PrivateAuthority` holds the payload itself, strongly, filed under the
  owner's identity. Nothing on the owner answers with it, so there is no
  attribute to rewrite, delete, or reach the stored object through. This is
  where a policy goes: a policy is primitives, so holding one retains nothing
  but the policy, and the weak reference filed beside it drops the entry when
  the owner dies.
- :class:`PrivateMembership` holds one piece of weak evidence per MEMBER of an
  accepted sequence and answers with what that evidence points at. The owner
  holds the members themselves, which is what gives the graph the owner's
  lifetime; the ATTRIBUTE holding them is never read, so writing it does not
  change what a later read answers with. This is where an arbitrary object graph goes,
  the schema's extension configuration being the one the package has. A member
  no weak reference can be taken of - a ``__slots__`` callable, which Strawberry
  accepts as a factory - is held by the owner inside a box the interpreter
  itself refuses to rewrite, and answered from one weak reference to that box.

Which object answers is a smaller question than what it holds, and only the
second one is the configuration. A carrier whose contents consumer code can
write is a carrier whose identity that write leaves untouched, so evidence about
the carrier certifies nothing about the membership inside it - which is why the
evidence here is per member, why a read is answered from the evidence rather
than from the owner, and why the box a non-weak member is answered through is
one whose contents no assignment, ``__dict__`` write, ``object.__setattr__`` or
re-initialization can change: the object authenticated by weak identity and the
object supplying the member have to be the same immutable thing, or the
authentication is of a carrier and the member inside it is anyone's to swap.
Evidence that no longer resolves is the one thing that cannot be answered: the
accepted member is exactly what is gone, so the read reports that rather than
substituting for it.

Both file entries under ``id(owner)`` rather than under the owner itself. A
``WeakKeyDictionary`` finds its keys by hash and equality, and both of those are
methods a consumer subclass may define - two distinct schemas that compare equal
would share one entry, and one that defines ``__eq__`` without a hash could not
be filed at all. Which object owns a record is a question about identity, and
``id()`` answers it without calling anything the consumer wrote. An ``id()`` is
unique among LIVE objects only, so every read verifies the filed weak reference
still points at the owner asking, and the reference's own callback removes an
entry only while that entry is still the one it was filed under: by the time a
dead owner's callback runs, the key may already name the successor that reused
the address.
"""

from __future__ import annotations

from collections.abc import Iterable
from types import MethodType
from typing import Any, Generic, NamedTuple, TypeVar
from weakref import ReferenceType, ref

__all__ = ("PrivateAuthority", "PrivateMembership")

StateT = TypeVar("StateT")
MemberT = TypeVar("MemberT")


class PrivateAuthority(Generic[StateT]):
    """One kind of settled authority, for every object of one kind that carries it.

    The payload is held here and nowhere else. No attribute on the owner
    answers with it, which is what makes it neither replaceable nor deletable
    nor reachable for an in-place write by consumer code that holds the owner:
    the object every bound is read from is one nothing outside this package has
    a name for.

    Only for payloads that point at nothing - a policy of ints, strings and
    bools. Holding an object graph here roots whatever it can reach, and an
    owner reachable from its own payload never dies; :class:`PrivateMembership`
    is that case's home.
    """

    def __init__(self) -> None:
        self._settled: dict[int, tuple[ReferenceType[Any], StateT]] = {}

    def settled(self, owner: Any) -> bool:
        """Whether ``owner`` already has an authority filed here.

        Asked by a constructor before it settles one, because settling twice is
        re-configuring an object that is already serving requests: an owner
        reachable from a resolver is one whose ``__init__`` a resolver can call
        again, and the second call would hand the process a new ceiling. Each
        caller raises its own typed refusal, so the message names the object the
        consumer is actually holding.

        This is the whole construction record, and it answers for a payload of
        every shape - the deliberate absence of an override included. A caller
        that instead took a non-empty payload for the record would read one
        supported configuration as an object that was never constructed at all,
        and admit the second constructor call that configuration is open to.
        """
        entry = self._settled.get(id(owner))
        return entry is not None and entry[0]() is owner

    def settle(self, owner: Any, state: StateT) -> None:
        """File ``state`` as ``owner``'s authority."""
        key = id(owner)

        def forget(dead: ReferenceType[Any]) -> None:
            entry = self._settled.get(key)
            if entry is not None and entry[0] is dead:
                del self._settled[key]

        self._settled[key] = (ref(owner, forget), state)

    def recall(self, owner: Any) -> StateT | None:
        """The authority ``owner`` was settled with, or ``None`` if it has none.

        ``None`` means never settled. It cannot mean lost: the entry is held
        here strongly and is removed only when the owner it belongs to dies, so
        an owner that is alive to ask still has the authority it was accepted
        with.
        """
        entry = self._settled.get(id(owner))
        return None if entry is None or entry[0]() is not owner else entry[1]


def _boxed_member() -> None:
    """The callable a box binds its member to, and never calls.

    ``types.MethodType`` needs a function to bind an object to, and this is that
    function: a box is a carrier, so nothing invokes it and it takes no
    arguments to be invoked with. What matters is the binding, which the
    interpreter holds in ``__self__`` and refuses every write to.
    """


class _BoxedMember(NamedTuple):
    """Evidence for a member no weak reference can be taken of: its owner's box.

    A ``types.MethodType`` is weak-referenceable, holds the object it was built
    on strongly, and hands it back through ``__self__`` - which is a read-only
    C-level attribute, not a Python one: assignment, ``object.__setattr__``,
    ``del`` and a second ``__init__`` all leave it exactly as it was bound, and
    it carries no state-restoring protocol for a caller to rebuild it through.
    That is what a Python class cannot offer, whatever its ``__setattr__``
    refuses: the primitive its own constructor uses to write its slot is a
    primitive consumer code can use too.

    So the box IS the evidence. One weak reference to it is filed, the owner
    holds it, and the member comes back out of the object that weak reference
    authenticated rather than out of anything a later write could substitute.
    """

    box: ReferenceType[MethodType]


#: What one member of an accepted sequence is answered from: a weak reference to
#: the member itself, or - for a member no weak reference can be taken of - one
#: to the box its owner holds it in.
_Evidence = ReferenceType[MemberT] | _BoxedMember

#: One owner's filed evidence: which object the entry belongs to, and one piece
#: of evidence per member of the sequence it was accepted with.
_Accepted = tuple[ReferenceType[Any], tuple[_Evidence[MemberT], ...]]


def _accepted_member(member: MemberT) -> tuple[_Evidence[MemberT], Any]:
    """What one accepted member is answered from, and what the owner holds for it.

    A weak reference is preferred wherever the member's layout admits one,
    because it is evidence about that member alone and stops resolving exactly
    when the member does; the owner then holds the member itself. A
    variable-size or ``__slots__`` object without a ``__weakref__`` slot admits
    none - which says nothing about whether Strawberry can run it - so the owner
    holds a box built on it and the evidence is a weak reference to that box.
    """
    try:
        return ref(member), member
    except TypeError:
        box = MethodType(_boxed_member, member)
        return _BoxedMember(ref(box)), box


class PrivateMembership(Generic[MemberT]):
    """One accepted sequence, for every object of one kind that carries one.

    ``attribute`` is the name the sequence is held under on its owner. That
    attribute is the STRONG hold and nothing else: it is what gives an object
    graph that reaches its owner back the owner's own lifetime, and what keeps
    it out of this module's reach, where holding it would root the owner
    forever. It is not where a read gets its answer.

    The answer comes from evidence filed here, per member, and the evidence is
    weak in both of its forms. A member a weak reference can be taken of is
    answered by that reference: weak references retain nothing, so the evidence
    costs the owner no lifetime, and because a read resolves them rather than
    reading the attribute, a member consumer code wrote over the attribute was
    never accepted and is never answered with. A member that takes no weak
    reference - a ``__slots__`` callable, which is a valid extension factory and
    not an invalid surface - is answered through the box the owner holds it in
    (:class:`_BoxedMember`), which is the same rule one indirection along: what
    the weak reference authenticates is the object the member is read out of.

    A write that drops the only strong hold on an accepted member does end the
    sequence - the member or its box is collected and the evidence stops
    resolving - and that is the condition :meth:`recall` reports, for the caller
    to refuse on. Nothing here can stand in for what is gone: the accepted
    member is exactly what the evidence was evidence of.
    """

    def __init__(self, attribute: str) -> None:
        self._attribute = attribute
        self._accepted: dict[int, _Accepted[MemberT]] = {}

    def accept(self, owner: Any, members: Iterable[MemberT]) -> None:
        """Accept ``members`` as ``owner``'s sequence, replacing whatever it carried.

        The evidence is taken first, so nothing is half-accepted for a later
        read to answer with; a member that takes no weak reference is boxed
        rather than refused for a memory layout that says nothing about whether
        Strawberry can run it.
        """
        taken = tuple(_accepted_member(member) for member in members)
        owner.__dict__[self._attribute] = tuple(hold for _, hold in taken)
        key = id(owner)

        def forget(dead: ReferenceType[Any]) -> None:
            entry = self._accepted.get(key)
            if entry is not None and entry[0] is dead:
                del self._accepted[key]

        self._accepted[key] = (ref(owner, forget), tuple(evidence for evidence, _ in taken))

    def recall(self, owner: Any) -> tuple[MemberT, ...] | None:
        """The sequence ``owner`` was accepted with, or ``None`` for one that is gone.

        ``None`` is the answer when no sequence was ever accepted, when the
        entry was filed under an identity that has since been reused, and when
        any accepted member no longer exists - which is what a write to the
        attribute holding them amounts to when that attribute was their last
        strong hold, for a boxed member and a directly referenced one alike.

        Each member is resolved from its own evidence, so a sequence whose
        entries something else still holds is answered in full: an accepted
        class the module it was defined in still names survives a write to the
        attribute, and the entry the write dropped the last hold on is the one
        that ends the sequence.
        """
        entry = self._accepted.get(id(owner))
        if entry is None or entry[0]() is not owner:
            return None
        accepted: list[MemberT] = []
        for evidence in entry[1]:
            if isinstance(evidence, _BoxedMember):
                box = evidence.box()
                if box is None:
                    return None
                accepted.append(box.__self__)
                continue
            member = evidence()
            if member is None:
                return None
            accepted.append(member)
        return tuple(accepted)
