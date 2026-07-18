"""Relation-shape helpers shared by converters, resolvers, and the optimizer."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Literal, Protocol, TypeAlias

from django.core.exceptions import FieldDoesNotExist

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from django.db import models

RelationKind: TypeAlias = Literal[
    "many",
    "reverse_many_to_one",
    "reverse_one_to_one",
    "forward_single",
    "generic",
]

MANY_SIDE_RELATION_KINDS: frozenset[RelationKind] = frozenset(
    {"many", "reverse_many_to_one", "generic"},
)


class _RelationFieldLike(Protocol):
    """Shape contract for the five Django relation flags this classifier reads.

    Every caller in the package hands in a real Django relation field or rel
    descriptor whose ``many_to_many`` / ``one_to_many`` / ``one_to_one`` /
    ``auto_created`` / ``concrete`` attributes are always present. The narrower
    annotation documents the read contract; ``getattr(..., False)`` in the body
    still defends against shapes that omit a flag.
    """

    many_to_many: bool
    one_to_many: bool
    one_to_one: bool
    auto_created: bool
    concrete: bool


def relation_kind(field: _RelationFieldLike) -> RelationKind:
    """Classify a Django relation field by GraphQL/runtime cardinality.

    Five shapes are distinguished:

    - ``"many"`` - forward ``ManyToManyField`` (``many_to_many=True``).
    - ``"generic"`` - a ``contenttypes`` ``GenericRelation`` (the reverse
      side of a ``GenericForeignKey``), detected duck-typed by the presence
      of non-``None`` ``content_type_field_name`` and ``object_id_field_name``
      attributes. It is many-valued (``one_to_many=True``,
      ``auto_created=False``) and would otherwise land in the defensive
      ``"many"`` fallback below; the explicit kind lets the optimizer inject
      the constant content-type morph predicate and partition by the child
      ``object_id`` column instead of guessing a reverse join.
    - ``"reverse_many_to_one"`` - the reverse side of a ``ForeignKey``
      (Django's ``ManyToOneRel`` descriptor: ``one_to_many=True`` paired
      with ``auto_created=True``). Cardinality-wise this collapses into
      the many-side for plan building today, but the descriptor itself
      is conceptually distinct from a forward M2M and is named so
      consumers (and the registry's typed ``PendingRelation`` sentinel)
      can disambiguate.
    - ``"reverse_one_to_one"`` - the reverse side of a
      ``OneToOneField`` (Django's ``OneToOneRel`` descriptor:
      ``one_to_one=True`` + ``auto_created=True`` + ``concrete=False``).
      ``concrete`` distinguishes it from Django's auto-created MTI parent
      link, which is a forward ``OneToOneField`` with the same other flags.
    - ``"forward_single"`` - every other forward single-row relation
      (``ForeignKey``, forward ``OneToOneField``, and the concrete
      auto-created MTI parent link).

    Any ``one_to_many=True`` shape without ``auto_created`` that is NOT a
    ``GenericRelation`` falls back to ``"many"`` as a defensive mapping;
    stock Django relation descriptors
    never produce that combination (``ManyToManyField`` sets
    ``many_to_many=True``; reverse FK/M2M descriptors always set
    ``auto_created=True``; forward FK and forward ``OneToOneField`` set
    ``one_to_many=False``). The branch is test-pinned at
    ``tests/utils/test_relations.py::test_relation_kind_classifies_one_to_many_as_many``
    so the fallback semantics cannot drift.

    Examples:
        ``ManyToManyField``-like -> ``"many"``;
        ``GenericRelation``-like -> ``"generic"``;
        ``ManyToOneRel``-like -> ``"reverse_many_to_one"``;
        ``OneToOneRel``-like -> ``"reverse_one_to_one"``;
        ``ForeignKey``-like -> ``"forward_single"``;
        MTI ``<parent>_ptr``-like -> ``"forward_single"``.
    """
    if getattr(field, "many_to_many", False):
        return "many"
    # A ``GenericRelation`` (and a ``FieldMeta`` snapshot of one) is detected
    # duck-typed BEFORE the ``one_to_many`` ``"many"`` fallback below. The
    # ``getattr(..., None) is not None`` form (not ``hasattr``) is load-bearing:
    # ``FieldMeta`` is a slotted dataclass that ALWAYS carries the two slots, so
    # ``hasattr`` would misclassify every ``FieldMeta`` as ``"generic"`` - only a
    # genuine ``GenericRelation`` populates the slots with real field names.
    if (
        getattr(field, "content_type_field_name", None) is not None
        and getattr(field, "object_id_field_name", None) is not None
    ):
        return "generic"
    if getattr(field, "one_to_many", False):
        if getattr(field, "auto_created", False):
            return "reverse_many_to_one"
        return "many"
    if (
        getattr(field, "one_to_one", False)
        and getattr(field, "auto_created", False)
        and not getattr(field, "concrete", False)
    ):
        return "reverse_one_to_one"
    return "forward_single"


def is_many_side_relation_kind(kind: RelationKind | None) -> bool:
    """Return ``True`` for relation kinds represented as GraphQL lists."""
    return kind in MANY_SIDE_RELATION_KINDS


@lru_cache(maxsize=2048)
def path_traverses_to_many(model: type, field_path: str) -> bool:
    """Return whether an ORM ``field_path`` traverses a to-many relation.

    Walks the ``__``-separated path from ``model`` until it reaches a
    terminal scalar, an unresolvable transform/lookup, or a relation without
    a concrete target model. A reverse FK or forward/reverse M2M hop is
    row-multiplying and returns ``True`` immediately.

    Filter generation uses the result to set ``distinct=True`` on plain
    generated leaf filters; order resolution uses it to replace a fan-out
    ``order_by`` with a row-preserving aggregate. The answer depends only on
    model metadata, so the bounded process-lifetime cache safely serves both
    subsystems.
    """
    current = model
    for segment in field_path.split("__"):
        try:
            field = current._meta.get_field(segment)
        except FieldDoesNotExist:
            return False
        if not getattr(field, "is_relation", False):
            return False
        if is_many_side_relation_kind(relation_kind(field)):
            return True
        related = getattr(field, "related_model", None)
        if related is None:
            return False
        current = related
    return False


def is_forward_many_to_many(field: object) -> bool:
    """Return ``True`` for a forward, writable ``ManyToManyField``.

    ``relation_kind`` maps BOTH a forward ``ManyToManyField`` and an
    auto-created reverse M2M accessor (``ManyToManyRel``) to ``"many"`` -
    cardinality-wise they are identical, so the classifier cannot tell them
    apart. The mutation surfaces need the finer distinction: only a forward,
    writable M2M is an editable column a write can set / index. A forward
    ``ManyToManyField`` is ``concrete`` (equivalently, not ``auto_created``);
    the reverse accessor is ``auto_created`` and not ``concrete``.

    Single-sited here so the predicate cannot drift between the two mutation
    surfaces that select editable M2M fields - the input generator
    (``mutations/inputs.py::_select_editable_fields``) and the relation-field
    index (``mutations/resolvers.py::_index_relation_fields``). ``getattr``
    defaults defend against field shapes that omit a flag, matching
    ``relation_kind``'s read contract.
    """
    return bool(getattr(field, "many_to_many", False)) and (
        bool(getattr(field, "concrete", False)) or not getattr(field, "auto_created", False)
    )


def instance_accessor(field: object) -> str:
    """Return the attribute name relation rows are reached through on an instance.

    For a REVERSE relation declared without ``related_name``, Django's
    ``ForeignObjectRel.name`` is the related *query* name (``"book"`` - the
    filter/annotation vocabulary) while the instance attribute is
    ``get_accessor_name()`` (``"book_set"``); ``getattr(root, field.name)``
    raises ``AttributeError`` there (Round-4 review S3), and Django's
    ``prefetch_related`` rejects the query name as a lookup for the same
    reason. They coincide whenever ``related_name`` is set, which is why
    every fakeshop fixture masked the split. Forward fields
    (``ForeignKey``, ``ManyToManyField``, ``OneToOneField``) have no
    ``get_accessor_name`` and their ``name`` IS the instance attribute.

    Three-tier read, matching the two field shapes the package passes
    around: an ``optimizer.field_meta.FieldMeta`` carries the accessor
    precomputed on its ``accessor_name`` slot (the builders derive it from
    the raw descriptor via this same helper); a raw Django reverse-relation
    descriptor answers ``get_accessor_name()``; everything else (forward
    fields, test doubles) falls back to ``name``.

    ``field.name`` stays the GraphQL-surface / optimizer-key vocabulary;
    this helper is ONLY for the seams Django resolves against the instance:
    the Phase-2 relation resolvers' ``getattr``, the spec-032 synthesized
    relation connections, and the optimizer's prefetch lookup paths.
    """
    precomputed = getattr(field, "accessor_name", None)
    if precomputed is not None:
        return precomputed
    get_accessor_name = getattr(field, "get_accessor_name", None)
    if get_accessor_name is not None:
        return get_accessor_name()
    return field.name  # type: ignore[attr-defined]


def has_composite_pk(model: type[models.Model]) -> bool:
    """Return whether ``model`` declares a Django 5.2+ composite primary key.

    The FK-id-elision eligibility test (a forward single relation satisfying an
    id-only child selection from the source row's local FK column) must fail
    closed for a composite primary key: the source-row ``attname`` carries a
    single-column id, but the target's ``pk`` is a tuple, so eliding would
    compare the wrong shapes and surface wrong data. Single-sited here so the
    optimizer's two elision deciders - ``FieldMeta.from_django_field`` (which
    precomputes the ``fk_id_elision_eligible`` slot) and the walker's raw-field
    fallback (``optimizer/walker.py::_can_elide_fk_id``) - cannot disagree on
    what counts as composite.
    """
    pk_fields = getattr(model._meta, "pk_fields", None)
    return pk_fields is not None and len(pk_fields) > 1
