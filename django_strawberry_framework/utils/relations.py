"""Relation-shape helpers shared by converters, resolvers, and the optimizer."""

from __future__ import annotations

from typing import Literal, Protocol, TypeAlias, runtime_checkable

RelationKind: TypeAlias = Literal[
    "many",
    "reverse_many_to_one",
    "reverse_one_to_one",
    "forward_single",
]

MANY_SIDE_RELATION_KINDS: frozenset[RelationKind] = frozenset(
    {
        "many",
        "reverse_many_to_one",
    },
)


@runtime_checkable
class _RelationFieldLike(Protocol):
    """Shape contract for the four Django relation flags this classifier reads.

    Every caller in the package hands in a real Django relation field or rel
    descriptor whose ``many_to_many`` / ``one_to_many`` / ``one_to_one`` /
    ``auto_created`` attributes are always present. The narrower annotation
    documents the read contract; ``getattr(..., False)`` in the body still
    defends against shapes that omit a flag.
    """

    many_to_many: bool
    one_to_many: bool
    one_to_one: bool
    auto_created: bool


def relation_kind(field: _RelationFieldLike) -> RelationKind:
    """Classify a Django relation field by GraphQL/runtime cardinality.

    Four shapes are distinguished:

    - ``"many"`` — forward ``ManyToManyField`` (``many_to_many=True``).
    - ``"reverse_many_to_one"`` — the reverse side of a ``ForeignKey``
      (Django's ``ManyToOneRel`` descriptor: ``one_to_many=True`` paired
      with ``auto_created=True``). Cardinality-wise this collapses into
      the many-side for plan building today, but the descriptor itself
      is conceptually distinct from a forward M2M and is named so
      consumers (and the registry's typed ``PendingRelation`` sentinel)
      can disambiguate.
    - ``"reverse_one_to_one"`` — the reverse side of a
      ``OneToOneField`` (``one_to_one=True`` + ``auto_created=True``).
    - ``"forward_single"`` — every other forward single-row relation
      (``ForeignKey``, forward ``OneToOneField``).
    """
    if getattr(field, "many_to_many", False):
        return "many"
    if getattr(field, "one_to_many", False):
        if getattr(field, "auto_created", False):
            return "reverse_many_to_one"
        return "many"
    if getattr(field, "one_to_one", False) and getattr(field, "auto_created", False):
        return "reverse_one_to_one"
    return "forward_single"


def is_many_side_relation_kind(kind: object) -> bool:
    """Return ``True`` for relation kinds represented as GraphQL lists."""
    return kind in MANY_SIDE_RELATION_KINDS
