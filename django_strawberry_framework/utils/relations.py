"""Relation-shape helpers shared by converters, resolvers, and the optimizer."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Literal, Protocol, TypeAlias, TypeGuard, cast, overload

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.constants import LOOKUP_SEP

from django_strawberry_framework.exceptions import (
    ConfigurationError,
    LookupValidationError,
    PathResolutionError,
    _safe_type_name,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence, Sized

    from django.db.models.lookups import Lookup, Transform
    from django.db.models.query_utils import PathInfo

    from .typing import ConcreteField, ForeignKeyField, ModelField

__all__ = [
    "MANY_SIDE_RELATION_KINDS",
    "ClassifiedPath",
    "RelationKind",
    "RelationLink",
    "RelationPathHop",
    "classify_path",
    "has_composite_pk",
    "instance_accessor",
    "is_forward_concrete_relation",
    "is_forward_many_to_many",
    "is_many_side_relation_kind",
    "is_single_column_foreign_key",
    "m2m_through_link_fields",
    "m2m_through_model",
    "path_traverses_to_many",
    "relation_attr",
    "relation_bool",
    "relation_kind",
    "relation_link",
    "relation_name",
    "safe_truthy",
    "validate_lookup_expr",
]

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

_MISSING = object()


def safe_truthy(value: object) -> bool:
    """Ask a value for its truth, treating a raising truth test as false.

    Containing the READ is only half a never-raises boundary: the read hands
    back whatever it found, so every ``if`` / ``or`` / ``not`` applied to that
    result is a second escape route one frame later. A double whose ``__bool__``
    raises would otherwise break the contract after the read itself was safely
    contained.
    """
    try:
        return bool(value)
    except BaseException:
        return False


def relation_attr(
    field: object,
    name: str,
    default: object = _MISSING,
    *,
    lenient: bool = False,
) -> object:
    """Read relation metadata without allowing consumer objects to escape raw errors.

    ``lenient`` selects the FAILURE POLICY, and it is the only axis on which the
    package's two relation-reading surfaces differ. Strict (the default) turns an
    unreadable attribute into a typed ``ConfigurationError``, because a schema
    built on metadata that cannot be read is a configuration the consumer must
    fix. Lenient returns ``default`` instead, for the optimizer's join taxonomy,
    whose whole contract is that it never raises: it classifies a relation to
    decide a FETCH STRATEGY, and an unclassifiable relation must degrade to the
    unplanned path rather than fail the request.

    The two policies stay genuinely different - they can and do answer
    differently for the same malformed field - but they now share one read body,
    so a change to HOW relation metadata is read is one edit rather than two
    parallel families that drifted.
    """
    try:
        return getattr(field, name, default)
    except BaseException as exc:
        if lenient:
            return default
        raise ConfigurationError(
            f"Could not read relation metadata {name!r} from {_safe_type_name(field)}.",
        ) from exc


def relation_bool(
    field: object,
    name: str,
    default: bool = False,
    *,
    lenient: bool = False,
) -> bool:
    """Read one relation flag under the strict or lenient policy.

    Strict rejects a non-``bool`` outright (malformed metadata is a
    configuration error, and a truthy non-bool must not silently pass for
    ``True``). Lenient answers with :func:`safe_truthy`, guarding both the read
    and the truth test, because the taxonomy has no way to surface an error.
    """
    value = relation_attr(field, name, default, lenient=lenient)
    if lenient:
        return safe_truthy(value)
    if value is None:
        value = default
    if type(value) is not bool:
        raise ConfigurationError(
            f"Relation metadata {name!r} on {_safe_type_name(field)} must be a bool; "
            f"got {_safe_type_name(value)}.",
        )
    return value


def relation_name(field: object, name: str) -> str | None:
    """Read an optional GenericRelation field-name slot without dispatching errors."""
    value = relation_attr(field, name, None)
    if value is not None and type(value) is not str:
        raise ConfigurationError(
            f"Relation metadata {name!r} on {_safe_type_name(field)} must be a string or "
            f"None; got {_safe_type_name(value)}.",
        )
    return value


class _RelationFieldLike(Protocol):
    """Shape contract for the five Django relation flags the relation classifiers read.

    Every caller in the package hands in a real Django relation field or rel
    descriptor whose ``many_to_many`` / ``one_to_many`` / ``one_to_one`` /
    ``auto_created`` / ``concrete`` attributes are always present. The narrower
    annotation documents the read contract; ``getattr(..., False)`` in the body
    still defends against shapes that omit a flag. The flags are read, never
    written, and a ``None`` reads as ``False`` (a plain Django ``Field`` carries
    ``None`` in the three cardinality slots), so a read-only snapshot such as
    ``FieldMeta`` satisfies the contract as well.
    """

    @property
    def many_to_many(self) -> bool | None: ...
    @property
    def one_to_many(self) -> bool | None: ...
    @property
    def one_to_one(self) -> bool | None: ...
    @property
    def auto_created(self) -> bool | None: ...
    @property
    def concrete(self) -> bool | None: ...


class _TraversableRelationLike(_RelationFieldLike, Protocol):
    """A relation whose ``path_infos`` a path walk can follow."""

    @property
    def path_infos(self) -> Sequence[PathInfo]: ...


def relation_kind(field: object) -> RelationKind:
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
    many_to_many = relation_bool(field, "many_to_many")
    one_to_many = relation_bool(field, "one_to_many")
    one_to_one = relation_bool(field, "one_to_one")
    auto_created = relation_bool(field, "auto_created")
    concrete = relation_bool(field, "concrete")
    content_type_field_name = relation_name(field, "content_type_field_name")
    object_id_field_name = relation_name(field, "object_id_field_name")

    if many_to_many:
        return "many"
    # A ``GenericRelation`` (and a ``FieldMeta`` snapshot of one) is detected
    # duck-typed BEFORE the ``one_to_many`` ``"many"`` fallback below. The
    # ``getattr(..., None) is not None`` form (not ``hasattr``) is load-bearing:
    # ``FieldMeta`` is a slotted dataclass that ALWAYS carries the two slots, so
    # ``hasattr`` would misclassify every ``FieldMeta`` as ``"generic"`` - only a
    # genuine ``GenericRelation`` populates the slots with real field names.
    if content_type_field_name is not None and object_id_field_name is not None:
        return "generic"
    if one_to_many:
        if auto_created:
            return "reverse_many_to_one"
        return "many"
    if one_to_one and auto_created and not concrete:
        return "reverse_one_to_one"
    return "forward_single"


def is_many_side_relation_kind(kind: RelationKind | None) -> bool:
    """Return ``True`` for relation kinds represented as GraphQL lists."""
    try:
        return kind in MANY_SIDE_RELATION_KINDS
    except BaseException:
        return False


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
    target_model: type[models.Model]
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

    model: type[models.Model]
    path: str
    hops: tuple[RelationPathHop, ...]
    terminal: ModelField
    first_many_index: int | None
    relation_chain: tuple[str, ...]


def _resolve_segment_field(model: type[models.Model], segment: str) -> ModelField:
    """Return the field a path segment names, resolving ``pk`` to the pk field.

    ``pk`` is Django's ORM alias for the model's primary key; a ``pk`` segment
    anywhere in a path behaves like that pk field. Any other unresolvable
    segment surfaces as ``FieldDoesNotExist`` for the caller to convert into a
    typed ``PathResolutionError`` (this includes a hidden reverse relation
    declared ``related_name="+"``, whose reverse name ``get_field`` rejects).
    """
    try:
        if segment == "pk":
            return model._meta.pk
        return model._meta.get_field(segment)
    except FieldDoesNotExist:
        raise
    except BaseException:
        raise FieldDoesNotExist(segment) from None


def _is_traversable_relation(field: object) -> TypeGuard[_TraversableRelationLike]:
    """Return whether a resolved field is a relation the walk can follow.

    A traversable relation is one exposing usable ``path_infos``. A forward
    ``GenericForeignKey`` reports ``is_relation=True`` but defines NO
    ``path_infos`` - reading it before this guard would raise ``AttributeError``
    instead of the typed error, so ``path_infos`` is touched ONLY after this
    returns ``True``.
    """
    try:
        if not relation_bool(field, "is_relation"):
            return False
        return getattr(field, "path_infos", _MISSING) is not _MISSING
    except BaseException:
        return False


def classify_path(model: type[models.Model], field_path: str) -> ClassifiedPath:
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
    if type(field_path) is not str:
        raise PathResolutionError(model, field_path, field_path) from None
    segments = field_path.split(LOOKUP_SEP)
    current = model
    hops: list[RelationPathHop] = []
    terminal: object = None
    last_index = len(segments) - 1
    for index, segment in enumerate(segments):
        try:
            field = _resolve_segment_field(current, segment)
        except FieldDoesNotExist:
            raise PathResolutionError(current, field_path, segment) from None
        try:
            is_relation = relation_bool(field, "is_relation")
        except ConfigurationError:
            raise PathResolutionError(current, field_path, segment) from None
        if is_relation:
            if not _is_traversable_relation(field):
                raise PathResolutionError(current, field_path, segment)
            try:
                path_infos = field.path_infos
                if type(path_infos) not in (list, tuple) or not path_infos:
                    raise ValueError("relation path_infos is empty or malformed")
                last_path = path_infos[-1]
                target_model = last_path.to_opts.model
                many_side = False
                for path_info in path_infos:
                    if relation_bool(path_info, "m2m"):
                        many_side = True
                        break
            except BaseException:
                raise PathResolutionError(current, field_path, segment) from None
            try:
                kind = relation_kind(field)
            except BaseException:
                raise PathResolutionError(current, field_path, segment) from None
            hops.append(
                RelationPathHop(
                    segment=segment,
                    kind=kind,
                    target_model=target_model,
                    many_side=many_side,
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
        # The final segment assigned its ``_resolve_segment_field`` result here or raised.
        terminal=cast("ModelField", terminal),
        first_many_index=first_many_index,
        relation_chain=tuple(hop.segment for hop in hops),
    )


def validate_lookup_expr(terminal: ModelField, lookup_expr: str) -> type[Lookup[object]]:
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
    if type(lookup_expr) is not str:
        raise LookupValidationError(terminal, lookup_expr, lookup_expr) from None
    if not lookup_expr:
        raise LookupValidationError(terminal, lookup_expr, lookup_expr)
    parts = lookup_expr.split(LOOKUP_SEP)
    for part in parts:
        if not part:
            raise LookupValidationError(terminal, lookup_expr, part)
    cursor: ModelField | Transform = terminal
    # ``str.split`` always yields at least one part, so the final part always exists.
    *transform_parts, final_part = parts
    for part in transform_parts:
        try:
            transform = cursor.get_transform(part)
        except BaseException:
            raise LookupValidationError(terminal, lookup_expr, part) from None
        if transform is None:
            raise LookupValidationError(terminal, lookup_expr, part)
        try:
            cursor = transform(cursor)
        except BaseException:
            raise LookupValidationError(terminal, lookup_expr, part) from None
    try:
        lookup = cursor.get_lookup(final_part)
    except BaseException:
        raise LookupValidationError(terminal, lookup_expr, final_part) from None
    if lookup is not None:
        return lookup
    try:
        transform = cursor.get_transform(final_part)
    except BaseException:
        raise LookupValidationError(terminal, lookup_expr, final_part) from None
    if transform is not None:
        try:
            exact = transform(cursor).get_lookup("exact")
        except BaseException:
            raise LookupValidationError(terminal, lookup_expr, final_part) from None
        if exact is not None:
            return exact
    raise LookupValidationError(terminal, lookup_expr, final_part)


def _lenient_traverses_to_many(model: type[models.Model], field_path: str) -> bool:
    """Legacy lenient to-many walk, retained verbatim as a fail-open fallback.

    Walks the ``__``-separated path swallowing any resolution failure into a
    ``False`` answer, returning ``True`` the instant a many-side relation is
    reached - even if garbage follows it. ``path_traverses_to_many`` runs this
    ONLY when strict ``classify_path`` raises ``PathResolutionError``, which
    preserves the pre-refactor answer on every path the classifier REJECTS: a
    many-then-garbage path (e.g. ``genres__nonexistent``) still answers
    ``True`` here, whereas plain ``False`` on the raise would have regressed it.
    On paths the classifier RESOLVES the answer comes from ``PathInfo.m2m``
    instead; see ``path_traverses_to_many`` for the one deliberate divergence
    from this lenient walk's cardinality rule.
    """
    if type(field_path) is not str:
        return False
    segments = field_path.split(LOOKUP_SEP)
    current = model
    for segment in segments:
        try:
            field = current._meta.get_field(segment)
            if not relation_bool(field, "is_relation"):
                return False
            if is_many_side_relation_kind(relation_kind(field)):
                return True
            # ``Field.related_model`` checks the app registry is ready, so it is a resolved
            # model class or ``None`` (``GenericForeignKey`` declares ``None``).
            related: type[models.Model] | None = getattr(field, "related_model", None)
        except BaseException:
            return False
        if related is None:
            return False
        current = related
    return False


@lru_cache(maxsize=2048)
def _classify_path_cached(model: type[models.Model], field_path: str) -> ClassifiedPath:
    """Bounded ``lru_cache`` over ``classify_path`` for the hot to-many probe.

    ``path_traverses_to_many`` is called repeatedly with the same
    definition-time ``(model, field_path)`` pairs during filter/order
    generation; caching the frozen ``ClassifiedPath`` here avoids re-walking
    model metadata without forcing a cache onto the public, uncached
    ``classify_path`` (which must accept unhashable test doubles).
    """
    return classify_path(model, field_path)


def _traverses_to_many(
    classify: Callable[[type[models.Model], str], ClassifiedPath],
    model: type[models.Model],
    field_path: str,
) -> bool:
    """Answer the to-many question over ``classify``, with the shared fallback ladder.

    ONE body for both arms of :func:`path_traverses_to_many`: the hashable arm
    passes the cached classifier, the unhashable arm passes the uncached one.
    The ladder itself - strict answer, lenient walk on ``PathResolutionError``,
    ``False`` on anything else - is the contract a 32-path matrix pins, and it
    must not be able to differ between the two arms.
    """
    try:
        return classify(model, field_path).first_many_index is not None
    except PathResolutionError:
        return _lenient_traverses_to_many(model, field_path)
    except BaseException:
        return False


@lru_cache(maxsize=2048)
def _path_traverses_to_many_cached(model: type[models.Model], field_path: str) -> bool:
    """Cached implementation for hashable definition-time model/path pairs."""
    return _traverses_to_many(_classify_path_cached, model, field_path)


def path_traverses_to_many(model: type[models.Model], field_path: str) -> bool:
    """Return whether an ORM ``field_path`` traverses a to-many relation.

    Built on ``classify_path``: the strict classifier is the single
    site of the relation taxonomy, and this helper answers
    ``classify_path(...).first_many_index is not None``. When strict
    classification raises ``PathResolutionError`` (an unresolvable head, a
    garbage tail, a forward ``GenericForeignKey``) it falls back to the
    lenient walk (``_lenient_traverses_to_many``) rather than a bare ``False``.

    That fallback keeps the resolvable-vs-unresolvable boundary faithful: the
    lenient walk returns ``True`` the instant it reaches a many-side hop and never
    sees a garbage tail beyond it, while ``classify_path`` raises on that tail. A
    32-path matrix (``tests/utils/test_relations.py``) pins the
    fallback's answers on the raise paths, including
    ``genres__nonexistent`` -> ``True`` and ``genres__name__icontains`` ->
    ``True`` (many-then-garbage), where a plain ``False`` would diverge.

    One DELIBERATE divergence from ``relation_kind`` holds on the RESOLVED path:
    ``relation_kind`` reads every ``ManyToOneRel`` as ``reverse_many_to_one``
    (many-side), whereas the strict classifier reads ``PathInfo.m2m``
    (``not field.unique``). The reverse side of a ``ForeignKey(unique=True)`` is
    therefore reported single-valued here (-> ``False``) where a
    ``relation_kind``-based walk would answer ``True``. That is the correct
    answer: a unique reverse FK is genuinely single-valued, so it neither fans
    out nor needs the ``distinct`` stamp / order aggregate a ``True`` would trigger.

    Filter generation uses the result to set ``distinct=True`` on plain
    generated leaf filters; order resolution uses it to replace a fan-out
    ``order_by`` with a row-preserving aggregate. The answer depends only on
    model metadata, so the bounded process-lifetime cache safely serves both
    subsystems.
    """
    try:
        hash(model)
        hash(field_path)
    except BaseException:
        return _traverses_to_many(classify_path, model, field_path)
    return _path_traverses_to_many_cached(model, field_path)


def _path_traverses_to_many_cache_clear() -> None:
    """Invalidate every cache ``path_traverses_to_many`` reads.

    The probe layers a bounded classifier cache beneath its own answer cache;
    a clear that emptied only the outer layer would leave a metadata change
    under a warm ``(model, field_path)`` key answering from the stale frozen
    classification even after the clear was called.
    """
    _classify_path_cached.cache_clear()
    _path_traverses_to_many_cached.cache_clear()


@overload
def is_forward_many_to_many(field: ModelField) -> TypeGuard[ConcreteField]: ...
@overload
def is_forward_many_to_many(field: object) -> bool: ...
def is_forward_many_to_many(field: object) -> bool:
    """Return ``True`` for a forward, writable ``ManyToManyField``.

    ``relation_kind`` maps BOTH a forward ``ManyToManyField`` and an
    auto-created reverse M2M accessor (``ManyToManyRel``) to ``"many"`` -
    cardinality-wise they are identical, so the classifier cannot tell them
    apart. The mutation surfaces need the finer distinction: only a forward,
    writable M2M is an editable column a write can set / index. A forward
    ``ManyToManyField`` is ``concrete`` (equivalently, not ``auto_created``);
    the reverse accessor is ``auto_created`` and not ``concrete``.

    Single-sited here so the predicate cannot drift across the write surfaces
    that select editable / attestable M2M fields - the model-mutation input
    generator (``mutations/inputs.py::editable_input_fields``), the
    relation-field index (``mutations/inputs.py::_relation_field_index``),
    and the DRF attestation filter
    (``rest_framework/resolvers.py::_attestable_m2m_fields``). ``getattr``
    defaults defend against field shapes that omit a flag, matching
    ``relation_kind``'s read contract. Over a model field, ``True`` narrows it to
    the forward ``ManyToManyField`` (a concrete ``Field``, never a reverse rel).
    """
    many_to_many = relation_bool(field, "many_to_many")
    concrete = relation_bool(field, "concrete")
    auto_created = relation_bool(field, "auto_created")
    return many_to_many and (concrete or not auto_created)


@overload
def is_forward_concrete_relation(field: ModelField) -> TypeGuard[ConcreteField]: ...
@overload
def is_forward_concrete_relation(field: _RelationFieldLike) -> bool: ...
def is_forward_concrete_relation(field: object) -> bool:
    """Return whether ``field`` is a forward FK / OneToOne with a real DB column.

    Cardinality is decided by ``relation_kind`` - this module's single site of
    the relation taxonomy - so the predicate is exactly "the kind is
    ``"forward_single"``, and it is backed by a real local column". Cardinality
    deliberately does NOT come from ``column`` / ``concrete``: Django moves BOTH
    flags for ``ManyToManyField`` inside the supported range. On the 5.2 support
    floor a forward M2M reports ``column="genres"`` and ``concrete=True``
    (``Field.set_attributes_from_name`` fills the attname in even though no such
    column exists on the source table - the pairing lives in the through table);
    6.0+ reports ``column=None`` and ``concrete=False``. A ``column``-only test
    therefore called a forward M2M a forward concrete relation on 5.2 and not on
    6.x - one predicate answering two ways across one supported matrix. The four
    flags ``relation_kind`` reads (``many_to_many`` / ``one_to_many`` /
    ``one_to_one`` / ``auto_created``) are stable across that range, so routing
    the cardinality question through it makes the answer version-independent.

    This helper is single-sited precisely so the predicate cannot drift across
    the write surfaces, and the M2M guard belongs HERE rather than at the
    callers. Both of today's callers - ``forms/inputs.py::_model_column_for``
    and ``mutations/inputs.py::_relation_field_index`` - screen M2M into their
    own forward-M2M arm before reaching this, which is why the promotion of
    this predicate out of ``forms/inputs.py`` carried the narrower ``column``
    test in unnoticed; the gate is here so the NEXT caller inherits the whole
    contract instead of having to re-derive that half of it.

    The ``column`` / ``related_model`` reads stay load-bearing AFTER the kind
    gate, because a forward ``GenericForeignKey`` also classifies
    ``"forward_single"``: it carries ``ct_field`` / ``fk_field``, not the
    ``content_type_field_name`` / ``object_id_field_name`` slots that mark a
    ``GenericRelation``, so the ``"generic"`` arm never claims it. It is virtual
    all the same (``column=None``, ``related_model=None``), and excluding it
    keeps a scalar or extra form field that merely shares a name with a virtual
    or reverse relation from being misclassified by the FK index or by ModelForm
    backing-column resolution.

    Every read is contained, so a descriptor with hostile metadata fails closed
    to ``False`` instead of dispatching its own exception into the caller. Over a
    model field, ``True`` narrows it to the forward FK / OneToOne ``Field``.
    """
    try:
        if not relation_bool(field, "is_relation"):
            return False
        if relation_kind(field) != "forward_single":
            return False
        return (
            getattr(field, "column", None) is not None
            and getattr(field, "related_model", None) is not None
        )
    except BaseException:
        return False


@dataclass(frozen=True)
class RelationLink:
    """A relation link's column pairs, as Django's ``ForeignObject`` declares them.

    ``carriers`` are the columns on the model that STORES the key (the link's
    ``local_related_fields``); ``targets`` are the columns they reference on the
    other model (``foreign_related_fields``), index-for-index. Which model each
    side lives on depends on the hop:

    - a forward ``ForeignKey`` / ``OneToOneField`` / ``ForeignObject``: carriers
      on the source row (``(<name>_id,)``, one per ``from_fields`` entry),
      targets on the related model (its pk, a ``to_field``, the ``to_fields``);
    - a reverse FK / reverse one-to-one / reverse ``ForeignObject``: the forward
      link read from the other side, so carriers on the child and targets on the
      source row;
    - a ``GenericRelation``: the child's ``object_id`` carrying the source pk;
    - an M2M hop in either direction: the through table's foreign key onto the
      SOURCE model (``m2m_through_link_fields``), so carriers on the through row
      and targets on the source row (the source pk, or a through FK's
      ``to_field``).

    Both tuples are empty for every shape that is not such a link (a
    ``GenericForeignKey``, a non-relation, an M2M whose through table does not
    resolve).
    """

    carriers: tuple[ConcreteField, ...] = ()
    targets: tuple[ConcreteField, ...] = ()

    @property
    def carrier_attnames(self) -> tuple[str, ...]:
        """The carrier columns' attnames, in link order."""
        return tuple(field.attname for field in self.carriers)

    @property
    def target_attnames(self) -> tuple[str, ...]:
        """The target columns' attnames, in link order."""
        return tuple(field.attname for field in self.targets)


def _link_field_tuple(value: object, *, lenient: bool) -> tuple[ConcreteField, ...] | None:
    """Return ``value`` as a tuple of column fields, or ``None`` when it is not one."""
    if not isinstance(value, (tuple, list)):
        return None
    fields = cast("tuple[object, ...]", tuple(value))
    for field in fields:
        if type(relation_attr(field, "attname", None, lenient=lenient)) is not str:
            return None
    return cast("tuple[ConcreteField, ...]", fields)


def relation_link(field: object, *, lenient: bool = False) -> RelationLink:
    """Return the column pairs of the link ``field`` is, or is the reverse of.

    The one reader of "which columns join this relation". A forward
    ``ForeignObject`` (``ForeignKey``, ``OneToOneField``, ``GenericRelation``
    included) answers from its own ``local_related_fields`` /
    ``foreign_related_fields``; an M2M hop (forward ``ManyToManyField`` or
    reverse ``ManyToManyRel``) answers from its through table's foreign key onto
    the source model; a reverse descriptor (``ManyToOneRel``, ``OneToOneRel``,
    ``ForeignObjectRel``) answers from its forward ``.field``.
    A relation's ``attname`` names its carrier column only for a ``ForeignKey``
    (``<name>_id``): a plain ``ForeignObject`` has ``attname == name``,
    ``column`` ``None``, and its columns exist only as these pairs, so a
    consumer deriving a column from ``attname`` reads a name no table carries.

    Shapes that carry no pairs, and malformed ones (unequal or empty sides, a
    member without a string ``attname``), answer the empty ``RelationLink``.
    ``lenient`` selects :func:`relation_attr`'s failure policy for a read that
    raises: strict raises ``ConfigurationError``, lenient answers empty.
    """
    link = field
    carriers = relation_attr(field, "local_related_fields", None, lenient=lenient)
    if carriers is None and relation_bool(field, "many_to_many", lenient=lenient):
        link, _target_side = m2m_through_link_fields(field, lenient=lenient)
        if link is None:
            return RelationLink()
        carriers = relation_attr(link, "local_related_fields", None, lenient=lenient)
    elif carriers is None:
        link = relation_attr(field, "field", None, lenient=lenient)
        if link is None:
            return RelationLink()
        carriers = relation_attr(link, "local_related_fields", None, lenient=lenient)
    carrier_fields = _link_field_tuple(carriers, lenient=lenient)
    target_fields = _link_field_tuple(
        relation_attr(link, "foreign_related_fields", None, lenient=lenient),
        lenient=lenient,
    )
    if not carrier_fields or target_fields is None or len(carrier_fields) != len(target_fields):
        return RelationLink()
    return RelationLink(carriers=carrier_fields, targets=target_fields)


def m2m_through_model(field: object, *, lenient: bool = False) -> type[models.Model] | None:
    """The M2M join table: ``field.through`` (rel side) or ``remote_field.through``."""
    through = relation_attr(field, "through", None, lenient=lenient)
    if through is None:
        through = relation_attr(
            relation_attr(field, "remote_field", None, lenient=lenient),
            "through",
            None,
            lenient=lenient,
        )
    # A relation's ``through`` slot holds the join-table model class.
    return cast("type[models.Model] | None", through)


def m2m_through_link_fields(
    field: object,
    *,
    lenient: bool = False,
) -> tuple[ForeignKeyField | None, ForeignKeyField | None]:
    """The M2M through table's (source-side FK, target-side FK) for one M2M hop.

    Resolved from the forward ``ManyToManyField``'s own naming
    (``m2m_field_name`` / ``m2m_reverse_field_name``, which honor
    ``through_fields``), which stays correct for self-referential M2Ms where
    scanning through-model FKs by target would be ambiguous. ``field`` is either
    the forward field (the source owns it) or the ``ManyToManyRel`` (the source
    is the target; the sides swap). ``(None, None)`` when the through model or
    the naming API is missing; a through model whose field lookup raises is a
    ``ConfigurationError`` under the strict policy and ``(None, None)`` under
    the lenient one.
    """
    forward_field = relation_attr(field, "field", None, lenient=lenient)
    if not safe_truthy(forward_field):
        forward_field = field
    through = m2m_through_model(field, lenient=lenient)
    source_name = relation_attr(forward_field, "m2m_field_name", None, lenient=lenient)
    target_name = relation_attr(forward_field, "m2m_reverse_field_name", None, lenient=lenient)
    if through is None or not callable(source_name) or not callable(target_name):
        return None, None
    try:
        through_meta = through._meta
        # ``m2m_field_name`` / ``m2m_reverse_field_name`` name the through table's
        # two ``ForeignKey`` columns.
        source_fk = cast("ForeignKeyField", through_meta.get_field(cast("str", source_name())))
        target_fk = cast("ForeignKeyField", through_meta.get_field(cast("str", target_name())))
    except BaseException as exc:
        if lenient:
            return None, None
        raise ConfigurationError(
            f"Could not resolve the M2M through-table foreign keys of {_safe_type_name(field)}.",
        ) from exc
    if forward_field is field:
        return source_fk, target_fk
    return target_fk, source_fk


def is_single_column_foreign_key(field: object) -> TypeGuard[ForeignKeyField]:
    """Return whether ``field`` is a forward FK / OneToOne whose value is one column.

    ``isinstance(field, models.ForeignKey)`` is the forward-concrete test:
    ``OneToOneField`` subclasses ``ForeignKey`` (MTI ``<parent>_ptr`` parent
    links included), while reverse relations (``ForeignObjectRel``), M2M
    (join-table-backed), ``GenericForeignKey`` (virtual, polymorphic),
    ``GenericRelation`` (a ``ForeignObject`` but not a ``ForeignKey``), and plain
    ``ForeignObject`` relations of any width are all excluded by construction.
    The ``column`` check guards the single-column contract against a
    ``ForeignKey`` shape whose value is not one concrete column. Every consumer
    that joins, casts, or filters on ``.column`` / ``.attname`` /
    ``.target_field`` as ONE column (the visibility cascade's ``__in`` edge, the
    lateral and single-parent fetch link) gates on this predicate.
    """
    return isinstance(field, models.ForeignKey) and getattr(field, "column", None) is not None


def instance_accessor(field: object) -> str:
    """Return the attribute name relation rows are reached through on an instance.

    For a REVERSE relation declared without ``related_name``, Django's
    ``ForeignObjectRel.name`` is the related *query* name (``"book"`` - the
    filter/annotation vocabulary) while the instance attribute is
    ``get_accessor_name()`` (``"book_set"``); ``getattr(root, field.name)``
    raises ``AttributeError`` there, and Django's
    ``prefetch_related`` rejects the query name as a lookup for the same
    reason. They coincide whenever ``related_name`` is set, so only a
    relation declared without one exposes the split (fakeshop's
    ``RepairTicket.venue``, ``VenueBadge.venue``, ``VenueSponsor.venues``). Forward fields
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
    precomputed = relation_attr(field, "accessor_name", None)
    if precomputed is not None:
        if type(precomputed) is not str:
            raise ConfigurationError(
                f"Relation accessor metadata on {_safe_type_name(field)} must be a string; "
                f"got {_safe_type_name(precomputed)}.",
            )
        return precomputed
    get_accessor_name = relation_attr(field, "get_accessor_name", None)
    if get_accessor_name is not None:
        if not callable(get_accessor_name):
            raise ConfigurationError(
                f"Relation accessor metadata on {_safe_type_name(field)} must be callable.",
            )
        try:
            accessor_name = get_accessor_name()
        except BaseException as exc:
            raise ConfigurationError(
                f"Could not resolve relation accessor on {_safe_type_name(field)}.",
            ) from exc
    else:
        accessor_name = relation_attr(field, "name")
    if type(accessor_name) is not str:
        raise ConfigurationError(
            f"Resolved relation accessor on {_safe_type_name(field)} must be a string; "
            f"got {_safe_type_name(accessor_name)}.",
        )
    return accessor_name


def has_composite_pk(model: type[models.Model]) -> bool:
    """Return whether ``model`` declares a Django 5.2+ composite primary key.

    The FK-id-elision eligibility test (a forward single relation satisfying an
    id-only child selection from the source row's local FK column) must fail
    closed for a composite primary key: the source-row ``attname`` carries a
    single-column id, but the target's ``pk`` is a tuple, so eliding would
    compare the wrong shapes and surface wrong data. Single-sited here so
    ``FieldMeta.from_django_field`` stamps ``fk_id_elision_eligible`` the
    same way for registered types and the walker's unregistered fallback
    map.
    """
    try:
        meta = model._meta
        # Django 5.2+ ``Options.pk_fields`` is a list of fields; older Django lacks it.
        pk_fields: Sized | None = getattr(meta, "pk_fields", None)
        return pk_fields is not None and len(pk_fields) > 1
    except BaseException as exc:
        raise ConfigurationError(
            f"Could not read composite-primary-key metadata from {_safe_type_name(model)}.",
        ) from exc
