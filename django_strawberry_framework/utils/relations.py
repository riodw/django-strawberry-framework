"""Relation-shape helpers shared by converters, resolvers, and the optimizer."""

from __future__ import annotations

from typing import Literal, Protocol, TypeAlias

RelationKind: TypeAlias = Literal[
    "many",
    "reverse_many_to_one",
    "reverse_one_to_one",
    "forward_single",
]

MANY_SIDE_RELATION_KINDS: frozenset[RelationKind] = frozenset(
    {"many", "reverse_many_to_one"},
)


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

    - ``"many"`` - forward ``ManyToManyField`` (``many_to_many=True``).
    - ``"reverse_many_to_one"`` - the reverse side of a ``ForeignKey``
      (Django's ``ManyToOneRel`` descriptor: ``one_to_many=True`` paired
      with ``auto_created=True``). Cardinality-wise this collapses into
      the many-side for plan building today, but the descriptor itself
      is conceptually distinct from a forward M2M and is named so
      consumers (and the registry's typed ``PendingRelation`` sentinel)
      can disambiguate.
    - ``"reverse_one_to_one"`` - the reverse side of a
      ``OneToOneField`` (``one_to_one=True`` + ``auto_created=True``).
    - ``"forward_single"`` - every other forward single-row relation
      (``ForeignKey``, forward ``OneToOneField`` - i.e.,
      ``auto_created=False``).

    Any ``one_to_many=True`` shape without ``auto_created`` falls back to
    ``"many"`` as a defensive mapping; stock Django relation descriptors
    never produce that combination (``ManyToManyField`` sets
    ``many_to_many=True``; reverse FK/M2M descriptors always set
    ``auto_created=True``; forward FK and forward ``OneToOneField`` set
    ``one_to_many=False``). The branch is test-pinned at
    ``tests/utils/test_relations.py::test_relation_kind_classifies_one_to_many_as_many``
    so the fallback semantics cannot drift.

    Examples:
        ``ManyToManyField``-like -> ``"many"``;
        ``ManyToOneRel``-like -> ``"reverse_many_to_one"``;
        ``OneToOneRel``-like -> ``"reverse_one_to_one"``;
        ``ForeignKey``-like -> ``"forward_single"``.
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


def is_many_side_relation_kind(kind: RelationKind | None) -> bool:
    """Return ``True`` for relation kinds represented as GraphQL lists."""
    return kind in MANY_SIDE_RELATION_KINDS


def instance_accessor(field: object) -> str:
    """Return the attribute name relation rows are reached through on an instance.

    For a REVERSE relation declared without ``related_name``, Django's
    ``ForeignObjectRel.name`` is the related *query* name (``"book"`` - the
    filter/annotation vocabulary) while the instance attribute is
    ``get_accessor_name()`` (``"book_set"``); ``getattr(root, field.name)``
    raises ``AttributeError`` there (Round-4 review S3). They coincide
    whenever ``related_name`` is set, which is why every fakeshop fixture
    masked the split. Forward fields (``ForeignKey``, ``ManyToManyField``,
    ``OneToOneField``) have no ``get_accessor_name`` and their ``name`` IS
    the instance attribute.

    ``field.name`` stays the GraphQL-surface / optimizer-key vocabulary;
    this helper is ONLY for the ``getattr(root, ...)`` seam shared by the
    Phase-2 relation resolvers and the spec-032 synthesized relation
    connections.
    """
    get_accessor_name = getattr(field, "get_accessor_name", None)
    if get_accessor_name is not None:
        return get_accessor_name()
    return field.name  # type: ignore[attr-defined]
