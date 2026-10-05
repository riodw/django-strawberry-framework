"""Row-preserving ORM predicate primitives.

A pure ORM utility that compiles to-many relational predicates as a correlated
``EXISTS`` subquery instead of the row-multiplying ``JOIN`` + ``DISTINCT`` idiom.
It knows NOTHING about django-filter or Strawberry selections, builds NO
predicate bodies, does NO ``OR`` grouping, and never calls ``.filter()``,
``.exclude()``, or ``.distinct()`` on the outer queryset - ``.alias()`` is its
only outer mutation. Predicate meaning stays with the caller: the FilterSet
flat-leaf applicator (``filters/sets.py::FilterSet._apply_flat_leaves``) applies
one original filter invocation inside the correlated root, and the search-fields
feature (docs/SPECS/spec-060-search_fields-0_1_2.md) builds its own same-value search
disjunctions. Keeping those semantics outside this module also keeps request
values out of the selection optimizer's cross-request ``OptimizationPlan`` cache.

Multiset contract: attaching an existence test does not multiply outer rows, so
a caller composing framework-generated relational predicates preserves the outer
queryset's row multiplicity (no framework fan-out, no injected ``DISTINCT``, and
no framework dedup of consumer duplicates). That is the production row-semantics
contract the applicator and live tiers assert. Generated to-many leaves are
never globally deduplicated.

``related_rows_exist`` is the target-side sibling: "the outer row reaches a row
of THIS queryset through a relation path", built from the given rows and
correlated to the outer row by the relation's own link columns. A declared
``RelatedFilter`` branch restricts its parent with it
(``filters/sets.py::_restrict_to_related``), so a nested branch and a flat leaf
walking the branch read the related rows the same way.

Implementation invariant: the INNER queryset built here is correlated with
``OuterRef`` and compiles inside the outer statement - it must never execute
independently. An evaluated OUTER queryset is still valid input (``.alias()`` /
``.filter()`` clone the query and run a fresh statement; a cached outer result
is never embedded in SQL), so there is no evaluated-outer input guard.

No ``negated`` parameter: negation placement is a boolean-composition decision
that belongs to the caller whose semantics are proven, not to this primitive.

Identity / no-op short-circuits (a filter invocation that returns its
correlated inner root unchanged) live in callers, above this module - there is
no empty or no-op input to ``attach_exists``; calling it always performs an
attachment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar, cast

from django.db.models import Exists, OuterRef, Q
from django.db.models.constants import LOOKUP_SEP

from ..exceptions import ConfigurationError, OptimizerError
from ..utils.relations import m2m_through_link_fields, relation_kind, relation_link

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.contrib.contenttypes.fields import GenericRelation
    from django.db import models
    from django.db.models import QuerySet

    from ..utils.typing import ConcreteField, ModelField

_M = TypeVar("_M", bound="models.Model")

_RESERVED_ALIAS_PREFIX = "_dst_predicate_"


def correlated_inner_root(queryset: QuerySet[_M]) -> QuerySet[_M]:
    """Return an unevaluated inner root correlated to the outer row's pk.

    Built as ``model._base_manager.using(queryset.db).filter(pk=OuterRef("pk"))``.

    - ``_base_manager``: the outer queryset already applied visibility and the
      consumer manager; the inner row exists only to test relation existence for
      an already-qualified outer pk, so replaying a filtered default manager here
      could only introduce false negatives.
    - ``queryset.db``: pins the outer queryset's resolved database alias onto the
      inner root (on a hint-less outer queryset ``.db`` invokes the router at
      build time). The inner never executes independently - the pin keeps the
      alias pair consistent, it does not re-run routing.
    - ``pk=OuterRef("pk")`` is the default and ONLY correlation implementation;
      composite primary keys compile to a tuple comparison on supported Django.
    """
    model = queryset.model
    return model._base_manager.using(queryset.db).filter(pk=OuterRef("pk"))


def _effective_alias_names(queryset: QuerySet[models.Model]) -> set[str]:
    """Return the effective alias namespace the reserved alias must avoid.

    Django is lax in the dangerous direction - a duplicate ``.alias()`` silently
    overwrites, and an ``extra(select=)`` name collision compiles ambiguous SQL -
    so this covers every namespace a reserved alias could clash with:

    - model field names AND attnames (e.g. ``shelf`` and ``shelf_id``);
    - the literal ``"pk"``;
    - ``query.annotations`` (covers both ``annotate`` and ``alias``);
    - ``query.extra`` names (``extra(select=...)``);
    - ``query.values_select`` (``values()`` / ``only()`` projected names).
    """
    query = queryset.query
    names: set[str] = set()
    for field in queryset.model._meta.get_fields():
        names.add(field.name)
        attname: str | None = getattr(field, "attname", None)
        if attname is not None:
            names.add(attname)
    names.add("pk")
    names.update(query.annotations)
    names.update(query.extra)
    names.update(query.values_select)
    return names


def _next_reserved_alias(
    queryset: QuerySet[models.Model],
    prefix: str = _RESERVED_ALIAS_PREFIX,
) -> str:
    """Advance a deterministic counter past every occupied effective alias name.

    Yields ``_dst_predicate_0``, ``_dst_predicate_1``, ... skipping any name
    already present in ``_effective_alias_names(queryset)``. Recomputed from the
    current queryset on every attachment so repeated invocations and existing
    ``_dst_order_*`` / window aliases safely coexist.
    """
    occupied = _effective_alias_names(queryset)
    index = 0
    while f"{prefix}{index}" in occupied:
        index += 1
    return f"{prefix}{index}"


def attach_exists(
    queryset: QuerySet[_M],
    inner_queryset: QuerySet[models.Model, object],
) -> tuple[QuerySet[_M], Q]:
    """Attach ``Exists(inner_queryset)`` under a reserved alias, row-preservingly.

    Returns ``(new_queryset, Q(<alias>=True))``: the caller owns boolean
    placement and applies the returned positive branch. This function never calls
    ``filter()``, ``exclude()``, ``distinct()``, or builds a predicate body -
    ``.alias()`` is its only outer mutation.

    Runtime guards (all ``OptimizerError`` for family coherence - each is a
    caller-contract violation in runtime query state, not consumer
    configuration):

    - ``inner_queryset.model`` must be ``queryset.model``.
    - ``inner_queryset.db`` must equal ``queryset.db`` (same database alias).
    - ``queryset.query.combinator`` (union / intersection / difference) must be
      unset - attaching aliases to a combined queryset is runtime misuse. This
      guard runs only when attachment is actually required, because there is no
      empty / no-op input to this function; identity short-circuits live in
      callers.

    An evaluated OUTER queryset is valid input (see module docstring). The INNER
    queryset must never execute independently (module invariant).
    """
    model = queryset.model
    inner_model = inner_queryset.model
    if inner_model is not model:
        raise OptimizerError(
            f"attach_exists inner queryset model {inner_model.__name__!r} does not "
            f"match outer model {model.__name__!r}; the inner root must be a "
            f"correlated queryset over the same model.",
        )
    # Snapshot both resolutions BEFORE comparing and format the message from the
    # snapshots: ``.db`` re-resolves through the router on every read of a
    # hint-less queryset, so re-reading inside the f-string would report aliases
    # that were never compared (a stateful router can make the message claim a
    # mismatch between two identical aliases). Mirrors the combinator arm below,
    # which already snapshots before it formats.
    inner_db = inner_queryset.db
    outer_db = queryset.db
    if inner_db != outer_db:
        raise OptimizerError(
            f"attach_exists database-alias mismatch: inner {inner_db!r} "
            f"vs outer {outer_db!r}; both querysets must resolve to the same "
            f"database alias.",
        )
    combinator = queryset.query.combinator
    if combinator:
        raise OptimizerError(
            f"attach_exists cannot attach a reserved alias to a combined queryset "
            f"(combinator {combinator!r}); attach existence predicates before "
            f"union / intersection / difference.",
        )
    alias = _next_reserved_alias(queryset)
    new_queryset = queryset.alias(**{alias: Exists(inner_queryset)})
    return new_queryset, Q(**{alias: True})


@dataclass(frozen=True)
class _CorrelationStep:
    """One link of a relation path: rows of ``model`` whose ``pairs`` columns equal the outer row's.

    ``pairs`` are ``(inner column, outer column)`` pairs, index for index;
    ``restriction`` is the constant filter the link carries (a
    ``GenericRelation``'s content type), empty for every other link.
    ``segment`` is the index of the path segment whose target rows the link
    reads, ``None`` for a many-to-many's join-table link.
    """

    model: type[models.Model]
    pairs: tuple[tuple[ConcreteField, ConcreteField], ...]
    restriction: tuple[tuple[str, object], ...] = ()
    segment: int | None = None


def _column_ref(field: ConcreteField) -> str:
    """Name ``field`` for a lookup: ``pk`` for a primary key, its attname otherwise.

    ``pk`` resolves on every model of the key's inheritance chain (a
    multi-table-inheritance child, a proxy) without the join to the parent
    table the parent's own attname would add.
    """
    return "pk" if field.primary_key else field.attname


def _correlation_steps(
    model: type[models.Model],
    relation_path: str,
) -> tuple[_CorrelationStep, ...]:
    """Read ``relation_path`` from ``model`` as the links an existence test crosses.

    Each segment is read off its own link columns (``utils/relations.py::relation_link``),
    never a reverse query name, so a relation whose reverse side is hidden
    (``related_name="+"``) correlates like any other. A forward single relation
    is one link whose carriers sit on the outer row; a reverse relation and a
    ``GenericRelation`` are one link whose carriers sit on the related row (the
    latter also restricted to the declaring model's content type); a
    many-to-many in either direction is two links, through its join table.
    A segment that names no such link (a ``GenericForeignKey``) raises
    ``ConfigurationError``: an uncorrelated existence test would match every
    outer row that has any related row at all.
    """
    steps: list[_CorrelationStep] = []
    current = model
    for index, segment in enumerate(relation_path.split(LOOKUP_SEP)):
        field = cast("ModelField", current._meta.get_field(segment))
        kind = relation_kind(field)
        if kind == "many":
            source_fk, target_fk = m2m_through_link_fields(field)
            source, target = relation_link(source_fk), relation_link(target_fk)
            links = [
                (
                    getattr(source_fk, "model", None),
                    tuple(zip(source.carriers, source.targets, strict=True)),
                    None,
                ),
                (
                    field.related_model,
                    tuple(zip(target.targets, target.carriers, strict=True)),
                    index,
                ),
            ]
        else:
            link = relation_link(field)
            pairs = (
                zip(link.targets, link.carriers, strict=True)
                if kind == "forward_single"
                else zip(link.carriers, link.targets, strict=True)
            )
            links = [(field.related_model, tuple(pairs), index)]
        for link_model, pairs, link_segment in links:
            if not pairs or not isinstance(link_model, type):
                raise ConfigurationError(
                    f"{model.__qualname__}.{relation_path}: segment {segment!r} is not a "
                    "relation with link columns, so a related row cannot be correlated to "
                    "the outer row.",
                )
            restriction: tuple[tuple[str, object], ...] = ()
            if kind == "generic":
                # ``relation_kind`` reads ``"generic"`` off ``GenericRelation``'s own slots.
                generic = cast("GenericRelation", field)
                content_type_field = generic.content_type_field_name
                declaring = generic.model
                if generic.for_concrete_model:
                    declaring = cast("type[models.Model]", declaring._meta.concrete_model)
                restriction = (
                    (f"{content_type_field}__app_label", declaring._meta.app_label),
                    (f"{content_type_field}__model", declaring._meta.model_name),
                )
            steps.append(
                _CorrelationStep(
                    cast("type[models.Model]", link_model),
                    pairs,
                    restriction,
                    link_segment,
                ),
            )
        current = steps[-1].model
    return tuple(steps)


def _correlated(rows: QuerySet[models.Model], step: _CorrelationStep) -> QuerySet[models.Model]:
    """Keep the ``rows`` whose ``step`` link columns equal the outer row's."""
    lookups: dict[str, object] = {
        _column_ref(inner): OuterRef(_column_ref(outer)) for inner, outer in step.pairs
    }
    lookups.update(step.restriction)
    return rows.filter(**lookups)


def related_rows_exist(
    model: type[models.Model],
    relation_path: str,
    rows: QuerySet[models.Model],
    *,
    using: str,
    via: Sequence[QuerySet[models.Model] | None] = (),
) -> Exists:
    """Return ``EXISTS`` "the outer ``model`` row reaches a row of ``rows`` through ``relation_path``".

    Built from ``rows`` (the target side) and correlated to the outer row by
    each link's own columns (``_correlation_steps``): the outer table is never
    re-scanned and nothing the outer queryset already applied is embedded, so
    every restriction an outer queryset carries costs one semi-join on its own.
    A multi-link path nests one ``EXISTS`` per link. ``via`` is empty or holds,
    index for index, the rows each segment before the last may pass through
    (the intermediate rows a visibility hook lets the request see); a segment
    whose entry is ``None``, every segment when ``via`` is empty, and a
    many-to-many's join table are read through ``_base_manager`` on ``using``
    (a join applies no manager either).
    The test is row-preserving and keeps any ``DISTINCT`` ``rows`` carry inside
    the subquery, where it changes no answer. Negated (``~``), it is the
    relation's ``NOT EXISTS``, which a ``NULL`` link column cannot empty the way
    it empties a ``NOT IN``.
    """
    *outer_steps, last = _correlation_steps(model, relation_path)
    query = _correlated(rows, last)
    for step in reversed(outer_steps):
        through = via[step.segment] if via and step.segment is not None else None
        if through is None:
            through = step.model._base_manager.using(using)
        query = _correlated(through, step).filter(Exists(query))
    return Exists(query)
