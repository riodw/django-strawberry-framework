"""Row-preserving ORM predicate primitives.

A pure ORM utility that compiles to-many relational predicates as a correlated
``EXISTS`` subquery instead of the row-multiplying ``JOIN`` + ``DISTINCT`` idiom.
It knows NOTHING about django-filter or Strawberry selections, builds NO
predicate bodies, does NO ``OR`` grouping, and never calls ``.filter()``,
``.exclude()``, or ``.distinct()`` on the outer queryset - ``.alias()`` is its
only outer mutation. Predicate meaning stays with the caller: the FilterSet
flat-leaf applicator (``filters/sets.py::FilterSet._apply_flat_leaves``) applies
one original filter invocation inside the correlated root, and the search-fields
feature (docs/spec-049-search_fields-0_1_2.md) builds its own same-value search
disjunctions. Keeping those semantics outside this module also keeps request
values out of the selection optimizer's cross-request ``OptimizationPlan`` cache.

Multiset contract: attaching an existence test does not multiply outer rows, so
a caller composing framework-generated relational predicates preserves the outer
queryset's row multiplicity (no framework fan-out, no injected ``DISTINCT``, and
no framework dedup of consumer duplicates). That is the production row-semantics
contract the applicator and live tiers assert. The old accidental global
deduplication of generated to-many leaves was legacy behavior and has been
removed.

``Exists`` / ``pk__in`` equivalence: ``filters/sets.py::FilterSet.
_apply_related_constraints`` already expresses the same "outer row has a
qualifying related row" test as a ``pk__in`` parent-pk subquery. That existing
idiom and this ``EXISTS`` primitive are semantically equivalent siblings;
neither should rewrite the other, and they must not silently diverge.

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

from typing import TYPE_CHECKING

from django.db.models import Exists, OuterRef, Q

from ..exceptions import OptimizerError

if TYPE_CHECKING:  # pragma: no cover
    from django.db.models import QuerySet

_RESERVED_ALIAS_PREFIX = "_dst_predicate_"


def correlated_inner_root(queryset: QuerySet) -> QuerySet:
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


def _effective_alias_names(queryset: QuerySet) -> set[str]:
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
        attname = getattr(field, "attname", None)
        if attname is not None:
            names.add(attname)
    names.add("pk")
    names.update(query.annotations)
    names.update(query.extra)
    names.update(query.values_select)
    return names


def _next_reserved_alias(queryset: QuerySet, prefix: str = _RESERVED_ALIAS_PREFIX) -> str:
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


def attach_exists(queryset: QuerySet, inner_queryset: QuerySet) -> tuple[QuerySet, Q]:
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
    if inner_queryset.db != queryset.db:
        raise OptimizerError(
            f"attach_exists database-alias mismatch: inner {inner_queryset.db!r} "
            f"vs outer {queryset.db!r}; both querysets must resolve to the same "
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
