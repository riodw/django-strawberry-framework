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
  holds the members themselves, in one sealed holder, which is what gives the
  graph the owner's lifetime; what the owner holds is never READ, so writing it
  does not change what a later read answers with. This is where an arbitrary
  object graph goes, the schema's extension configuration being the one the
  package has. A member no weak reference can be taken of - a ``__slots__``
  callable, which Strawberry accepts as a factory - is answered by its place
  inside that sealed holder, of which one weak reference is filed; the holder
  belongs to the owner, so neither form roots anything here.

Which object answers is a smaller question than what it holds, and only the
second one is the configuration. A carrier whose contents consumer code can
write is a carrier whose identity that write leaves untouched, so evidence about
the carrier certifies nothing about the membership inside it - which is why the
evidence here is per member and why a read is answered from the evidence rather
than from the owner. Evidence that no longer resolves is the one thing that
cannot be answered: the accepted member is exactly what is gone, so the read
reports that rather than substituting for it.

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
from typing import Any, Generic, TypeVar
from weakref import ReferenceType, ref

__all__ = ("PrivateAuthority", "PrivateMembership")

StateT = TypeVar("StateT")
MemberT = TypeVar("MemberT")

#: What one member's place in an accepted sequence is answered from: a weak
#: reference to the member itself, or - for a member no weak reference can be
#: taken of - its index inside the owner's sealed holder.
_Evidence = ReferenceType[MemberT] | int

#: One owner's filed evidence: which object the entry belongs to, the sealed
#: holder that owner keeps its members in, and one piece of evidence per member
#: of the sequence it was accepted with.
_Accepted = tuple[
    ReferenceType[Any],
    ReferenceType["_SealedMembers"],
    tuple[_Evidence[MemberT], ...],
]


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


def _member_evidence(member: Any, index: int) -> _Evidence[Any]:
    """What one accepted member is answered from: its own weak reference, or its place.

    A weak reference is preferred wherever the member's layout admits one,
    because it is evidence about that member alone and stops resolving exactly
    when the member does. A variable-size or ``__slots__`` object without a
    ``__weakref__`` slot admits none - which says nothing about whether
    Strawberry can run it - so its place in the owner's sealed holder is the
    evidence instead.
    """
    try:
        return ref(member)
    except TypeError:
        return index


class _SealedMembers:
    """One accepted sequence, held by its owner and closed to every later write.

    The holder exists for the entries no weak reference can be taken of. A
    ``__slots__`` callable with no ``__weakref__`` slot is a perfectly valid
    extension factory for Strawberry, and evidence about such an entry has to be
    something ELSE the owner holds - so the owner holds this, and this holds the
    members.

    Sealed, because what a carrier holds is exactly what evidence about a
    carrier cannot certify: an object whose contents consumer code can rewrite
    is one a rewrite leaves looking accepted. Nothing here exposes a membership
    API, and the one attribute is refused a second assignment, so the members
    this answers with are the members it was built with.

    ``__weakref__`` is declared because this object IS the evidence - the record
    filed in the module holds one weak reference to it, which is what lets a
    read verify it is reading the holder that was accepted rather than whatever
    a later attribute write supplied.
    """

    __slots__ = ("__weakref__", "_members")

    def __init__(self, members: tuple[Any, ...]) -> None:
        object.__setattr__(self, "_members", members)

    @property
    def members(self) -> tuple[Any, ...]:
        """The accepted members, as they were accepted."""
        return self._members

    def __setattr__(self, name: str, value: Any) -> None:
        """Refuse every write, including a second write to the sealed tuple."""
        raise AttributeError(
            f"{type(self).__name__} is sealed at construction; {name!r} cannot be assigned.",
        )

    def __delattr__(self, name: str) -> None:
        """Refuse every deletion, for the reason :meth:`__setattr__` refuses writes."""
        raise AttributeError(
            f"{type(self).__name__} is sealed at construction; {name!r} cannot be deleted.",
        )


class PrivateMembership(Generic[MemberT]):
    """One accepted sequence, for every object of one kind that carries one.

    ``attribute`` is the name the members are held under on their owner, as one
    sealed holder. That attribute is the sequence's STRONG hold and nothing
    else: it is what gives an object graph that reaches its owner back the
    owner's own lifetime, and what keeps it out of this module's reach, where
    holding it would root the owner forever. It is not where a read gets its
    answer.

    The answer comes from evidence filed here, per member, and the evidence is
    weak in both of its forms. A member a weak reference can be taken of is
    answered by that reference: weak references retain nothing, so the evidence
    costs the owner no lifetime, and because a read resolves them rather than
    reading the attribute, a member consumer code wrote over the attribute was
    never accepted and is never answered with. A member that takes no weak
    reference - a ``__slots__`` callable, which is a valid extension factory and
    not an invalid surface - is answered by its place inside the holder, of
    which one weak reference is filed; the holder is the owner's, so the record
    here still roots nothing.

    A write that drops the only strong hold on an accepted member does end the
    sequence - the member is collected and its evidence stops resolving - and
    that is the condition :meth:`recall` reports, for the caller to refuse on.
    Nothing here can stand in for what is gone: the accepted member is exactly
    what the evidence was evidence of. A slotted member is the sharper case of
    the same rule, because the holder is its only evidence: losing the holder
    loses the record of what that entry declared, and there is no weaker answer
    to fall back to.
    """

    def __init__(self, attribute: str) -> None:
        self._attribute = attribute
        self._accepted: dict[int, _Accepted[MemberT]] = {}

    def accept(self, owner: Any, members: Iterable[MemberT]) -> None:
        """Accept ``members`` as ``owner``'s sequence, replacing whatever it carried.

        The evidence is taken first, so nothing is half-accepted for a later
        read to answer with; a member that takes no weak reference is recorded
        by its position in the holder the owner is about to be given, rather
        than refused for a memory layout that says nothing about whether
        Strawberry can run it.
        """
        accepted = tuple(members)
        evidence = tuple(_member_evidence(member, index) for index, member in enumerate(accepted))
        holder = _SealedMembers(accepted)
        owner.__dict__[self._attribute] = holder
        key = id(owner)

        def forget(dead: ReferenceType[Any]) -> None:
            entry = self._accepted.get(key)
            if entry is not None and entry[0] is dead:
                del self._accepted[key]

        self._accepted[key] = (ref(owner, forget), ref(holder), evidence)

    def recall(self, owner: Any) -> tuple[MemberT, ...] | None:
        """The sequence ``owner`` was accepted with, or ``None`` for one that is gone.

        ``None`` is the answer when no sequence was ever accepted, when the
        entry was filed under an identity that has since been reused, when any
        accepted member no longer exists - which is what a write to the
        attribute holding them amounts to when that attribute was their last
        strong hold - and, for a member the holder is the only evidence of, when
        the holder itself is what that write replaced.

        The holder is resolved only when a member needs it. A sequence every
        member of which something else still holds is answered without it, which
        is what keeps an accepted class resolvable after an attribute write.
        """
        entry = self._accepted.get(id(owner))
        if entry is None or entry[0]() is not owner:
            return None
        holder: _SealedMembers | None = None
        accepted: list[MemberT] = []
        for evidence in entry[2]:
            if isinstance(evidence, int):
                if holder is None:
                    holder = entry[1]()
                    if holder is None:
                        return None
                accepted.append(holder.members[evidence])
                continue
            member = evidence()
            if member is None:
                return None
            accepted.append(member)
        return tuple(accepted)
