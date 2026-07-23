"""Relation-shape helpers shared by converters, resolvers, and the optimizer."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypeAlias

from django.core.exceptions import FieldDoesNotExist
from django.db.models.constants import LOOKUP_SEP

from django_strawberry_framework.exceptions import (
    LookupValidationError,
    PathResolutionError,
)

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


@dataclass(frozen=True)
class RelationPathHop:
    """One resolved relation segment of a classified model-field path.

    ``kind`` is ``relation_kind(field)`` - the semantic topology of the hop.
    ``many_side`` is the SQL-cardinality answer read from Django's
    ``PathInfo`` records (``any(pi.m2m for pi in field.path_infos)``): despite
    the name, ``PathInfo.m2m`` is ``True`` for an ordinary non-unique reverse
    FK too, so it, not ``kind``, decides whether the hop multiplies rows.
    ``target_model`` is ``field.path_infos[-1].to_opts.model`` - the model the
    walk continues from after one declared segment (which may expand to several
    ``PathInfo`` records, e.g. an M2M through table, collapsed at the segment
    boundary). No Django ``PathInfo`` object is retained on the frozen record.
    """

    segment: str
    kind: RelationKind
    target_model: type
    many_side: bool


@dataclass(frozen=True)
class ClassifiedPath:
    """The strict, immutable classification of one model-field path.

    ``hops`` are the ordered relation segments (empty for a local scalar).
    ``terminal`` is NEVER ``None``: for a path ending on a column it is that
    concrete Django field; for a relation-terminal path (e.g. ``genres`` used
    by an ``isnull`` relation filter) it is the terminal relation descriptor
    itself, which ALSO appears as the last hop. ``first_many_index`` is the
    index into ``hops`` of the first ``many_side`` hop, or ``None`` when the
    whole path is row-preserving. ``relation_chain`` is the tuple of relation
    (hop) segments - the path minus a scalar terminal - the safe subquery
    grouping key predicate generation consumes.
    """

    model: type
    path: str
    hops: tuple[RelationPathHop, ...]
    terminal: Any
    first_many_index: int | None
    relation_chain: tuple[str, ...]


def _resolve_segment_field(model: type, segment: str) -> object:
    """Return the field a path segment names, resolving ``pk`` to the pk field.

    ``pk`` is Django's ORM alias for the model's primary key; a ``pk`` segment
    anywhere in a path behaves like that pk field. Any other unresolvable
    segment surfaces as ``FieldDoesNotExist`` for the caller to convert into a
    typed ``PathResolutionError`` (this includes a hidden reverse relation
    declared ``related_name="+"``, whose reverse name ``get_field`` rejects).
    """
    if segment == "pk":
        return model._meta.pk
    return model._meta.get_field(segment)


def _is_traversable_relation(field: object) -> bool:
    """Return whether a resolved field is a relation the walk can follow.

    A traversable relation is one exposing usable ``path_infos``. A forward
    ``GenericForeignKey`` reports ``is_relation=True`` but defines NO
    ``path_infos`` - reading it before this guard would raise ``AttributeError``
    instead of the typed error, so ``path_infos`` is touched ONLY after this
    returns ``True``.
    """
    return bool(getattr(field, "is_relation", False)) and hasattr(field, "path_infos")


def classify_path(model: type, field_path: str) -> ClassifiedPath:
    """Strictly classify an ORM ``field_path`` into an immutable relation plan.

    Splits on ``LOOKUP_SEP`` and walks each segment through
    ``Model._meta.get_field`` (with ``pk`` resolved to the pk field). A
    non-relation field is a valid terminal only as the LAST segment; anywhere
    earlier the path continues past an untraversable column and raises. A
    relation segment must expose non-empty ``path_infos``; its hop records
    ``relation_kind(field)`` as ``kind`` and ``any(pi.m2m ...)`` as
    ``many_side``, and the walk continues from ``path_infos[-1].to_opts.model``.
    A relation reached at the final segment is preserved as ``terminal`` AND as
    the last hop. Raises ``PathResolutionError`` (naming model, path, and
    segment) for a missing, non-traversable (forward ``GenericForeignKey``),
    empty-``path_infos``, or non-relation-mid-path segment.

    Kept uncached so callers may pass unhashable test doubles (a
    ``SimpleNamespace`` fake model pins the empty-``path_infos`` branch);
    ``_classify_path_cached`` layers a bounded ``lru_cache`` over it for the
    hot ``path_traverses_to_many`` path, keyed on the hashable,
    definition-time-stable ``(model, field_path)`` pair.
    """
    segments = field_path.split(LOOKUP_SEP)
    current = model
    hops: list[RelationPathHop] = []
    terminal: Any = None
    last_index = len(segments) - 1
    for index, segment in enumerate(segments):
        try:
            field = _resolve_segment_field(current, segment)
        except FieldDoesNotExist:
            raise PathResolutionError(current, field_path, segment) from None
        if getattr(field, "is_relation", False):
            if not _is_traversable_relation(field):
                raise PathResolutionError(current, field_path, segment)
            path_infos = field.path_infos  # type: ignore[attr-defined]
            if not path_infos:
                raise PathResolutionError(current, field_path, segment)
            target_model = path_infos[-1].to_opts.model
            hops.append(
                RelationPathHop(
                    segment=segment,
                    kind=relation_kind(field),  # type: ignore[arg-type]
                    target_model=target_model,
                    many_side=any(pi.m2m for pi in path_infos),
                ),
            )
            current = target_model
            if index == last_index:
                terminal = field
        elif index == last_index:
            terminal = field
        else:
            raise PathResolutionError(current, field_path, segment)
    first_many_index = next(
        (i for i, hop in enumerate(hops) if hop.many_side),
        None,
    )
    return ClassifiedPath(
        model=model,
        path=field_path,
        hops=tuple(hops),
        terminal=terminal,
        first_many_index=first_many_index,
        relation_chain=tuple(hop.segment for hop in hops),
    )


def validate_lookup_expr(terminal: Any, lookup_expr: str) -> type:
    """Validate a django-filter lookup expression against a classified terminal.

    A contract SEPARATE from path classification. ``terminal`` is a
    ``ClassifiedPath.terminal`` - a concrete Django field or a relation
    descriptor (forward relation field / ``ForeignObjectRel``). ``lookup_expr``
    is a ``LOOKUP_SEP``-joined chain of zero or more transforms followed by a
    final lookup (e.g. ``"icontains"``, ``"date__year__gte"``, ``"exact"``,
    ``"isnull"``).

    The walk advances an EXPRESSION cursor (the terminal, then successive
    transform instances). For each non-final part the cursor's
    ``get_transform`` must resolve a transform; the cursor advances to that
    transform bound to the previous cursor, so validation of the next part runs
    against the transform's own output field - NEVER re-validated against the
    original terminal. For the final part the cursor's ``get_lookup`` is tried
    first; if it returns ``None`` the part is treated as a TRAILING TRANSFORM
    with an implicit ``exact`` (Django's own ORM semantics: a lookup path
    ending on a transform compiles as ``transform + exact``), accepted only
    when the transform's output field supports ``exact``.

    Both concrete Django fields and Django relation descriptors (verified
    empirically against ``ManyToManyField`` / ``ManyToOneRel`` / ``OneToOneRel``
    / ``ForeignKey``: all expose ``get_lookup`` returning ``RelatedIsNull`` /
    ``RelatedExact`` / ``RelatedIn``) answer ``get_lookup`` / ``get_transform``
    directly, so the walk uses the cursor's own methods uniformly.

    Returns the resolved final lookup CLASS (the trailing-transform case
    returns the ``exact`` lookup class) - cheap and useful to callers.

    Raises ``LookupValidationError`` (naming the terminal, the full
    ``lookup_expr``, and the offending part) for an empty expression, an empty
    part, an unresolvable mid-chain transform, or a final part that is neither
    a lookup nor a trailing transform with a supported ``exact``.
    """
    if not lookup_expr:
        raise LookupValidationError(terminal, lookup_expr, lookup_expr)
    parts = lookup_expr.split(LOOKUP_SEP)
    for part in parts:
        if not part:
            raise LookupValidationError(terminal, lookup_expr, part)
    cursor: Any = terminal
    last_index = len(parts) - 1
    for index, part in enumerate(parts):
        if index < last_index:
            transform = cursor.get_transform(part)
            if transform is None:
                raise LookupValidationError(terminal, lookup_expr, part)
            cursor = transform(cursor)
            continue
        lookup = cursor.get_lookup(part)
        if lookup is not None:
            return lookup
        transform = cursor.get_transform(part)
        if transform is not None:
            exact = transform(cursor).get_lookup("exact")
            if exact is not None:
                return exact
        raise LookupValidationError(terminal, lookup_expr, part)


def _lenient_traverses_to_many(model: type, field_path: str) -> bool:
    """Legacy lenient to-many walk, retained verbatim as a fail-open fallback.

    Walks the ``__``-separated path swallowing any resolution failure into a
    ``False`` answer, returning ``True`` the instant a many-side relation is
    reached - even if garbage follows it. ``path_traverses_to_many`` runs this
    ONLY when strict ``classify_path`` raises ``PathResolutionError``, which
    guarantees byte-identical answers to the pre-refactor implementation: a
    many-then-garbage path (e.g. ``genres__nonexistent``) still answers
    ``True`` here, whereas plain ``False`` on the raise would have regressed it.
    """
    current = model
    for segment in field_path.split(LOOKUP_SEP):
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


@lru_cache(maxsize=2048)
def _classify_path_cached(model: type, field_path: str) -> ClassifiedPath:
    """Bounded ``lru_cache`` over ``classify_path`` for the hot to-many probe.

    ``path_traverses_to_many`` is called repeatedly with the same
    definition-time ``(model, field_path)`` pairs during filter/order
    generation; caching the frozen ``ClassifiedPath`` here avoids re-walking
    model metadata without forcing a cache onto the public, uncached
    ``classify_path`` (which must accept unhashable test doubles).
    """
    return classify_path(model, field_path)


@lru_cache(maxsize=2048)
def path_traverses_to_many(model: type, field_path: str) -> bool:
    """Return whether an ORM ``field_path`` traverses a to-many relation.

    Reimplemented on ``classify_path``: the strict classifier is the single
    site of the relation taxonomy, and this helper answers
    ``classify_path(...).first_many_index is not None``. When strict
    classification raises ``PathResolutionError`` (an unresolvable head, a
    garbage tail, a forward ``GenericForeignKey``) it falls back to the legacy
    lenient walk (``_lenient_traverses_to_many``) rather than a bare ``False``.

    That fallback is load-bearing for byte-identical compatibility: the old
    walk returned ``True`` the instant it reached a many-side hop and never saw
    a garbage tail beyond it, while ``classify_path`` raises on that tail. A
    32-path adversarial matrix (``tests/utils/test_relations.py``) confirms the
    fallback reproduces the pre-refactor answers exactly, including
    ``genres__nonexistent`` -> ``True`` and ``genres__name__icontains`` ->
    ``True`` (many-then-garbage), where a plain ``False`` would have diverged.

    Filter generation uses the result to set ``distinct=True`` on plain
    generated leaf filters; order resolution uses it to replace a fan-out
    ``order_by`` with a row-preserving aggregate. The answer depends only on
    model metadata, so the bounded process-lifetime cache safely serves both
    subsystems.
    """
    try:
        return _classify_path_cached(model, field_path).first_many_index is not None
    except PathResolutionError:
        return _lenient_traverses_to_many(model, field_path)


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
