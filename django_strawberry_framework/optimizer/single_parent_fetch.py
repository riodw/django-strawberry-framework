"""Runtime single-parent degenerate fast path for the windowed nested prefetch.

The windowed nested-connection scheme (``plans.py::apply_window_pagination``,
``ROW_NUMBER() OVER (PARTITION BY fk)``) has no LIMIT pushdown - with N parents
that is the right trade (one query, not N), but when the Django-prefetch-injected
parent ``IN`` list has length exactly ONE the database numbers EVERY child row of
that partition before filtering ``rn <= limit``. A parent with 50k children and
``first: 10`` scans all 50k rows where the equivalent ``WHERE fk = x ORDER BY ...
LIMIT 10`` is a bounded index walk.

This module adds a RUNTIME-ONLY fast path mirroring ``lateral_fetch``'s
strict-degradation contract: ``WindowedPrefetchStrategy.plan`` wraps the planned
windowed queryset as a ``SingleParentWindowQuerySet`` carrying a
``SingleParentWindowSpec``. At fetch time, when the injected ``IN`` list has
length 1 and the query is exactly the count-free plain-first-page shape we
planned - same order, annotations, projection, and ``select_related`` join graph
(verified at fetch time against the plan-frozen spec, mirroring
``_recognize_lateral_fetch``) - ``_fetch_single_parent_rows`` executes the plain
filtered ``LIMIT`` query from the pristine child clone and synthesizes
``_dst_row_number`` in Python. Any unrecognized shape returns ``None`` and the
superclass ``_fetch_all``
runs the already-planned windowed body - a performance downgrade, never a
correctness cliff. The wrapped queryset IS cached inside the ``Prefetch`` (same
as lateral); only the len==1 decision is fetch-time, so cache hits and misses
behave identically.

Two verified corrections to the original idea:

1. ``node(id:)`` roots do NOT reach the windowed prefetch today -
   ``types/relay.py::_resolve_node_default`` returns ``qs.first()`` (an instance)
   and the extension middleware only optimizes ``QuerySet`` results. The fast
   path targets the general case: any windowed prefetch whose injected parent-IN
   list has length 1 (e.g. a root connection/filtered list returning one parent
   row). It claims no node-root benefit.
2. M2M / ``THROUGH_TABLE`` joins are excluded in v1: Django's M2M prefetch
   attaches rows via ``extra(select={"_prefetch_related_val_*": ...})``, which a
   degenerate re-query from the pristine clone cannot reproduce. v1 requires the
   ``DIRECT_FK`` join shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db.models import QuerySet
from django.db.models.query import ModelIterable

from ..utils.connections import window_range_plan
from . import logger
from .join_taxonomy import LateralJoinShape
from .lateral_fetch import (
    _deduplicate_parent_ids,
    _is_window_qual,
    _parent_in_values,
    _select_columns,
    window_predicate_signature,
)
from .nested_fetch import NestedConnectionRequest
from .plans import WINDOW_ROW_NUMBER


@dataclass(frozen=True)
class SingleParentWindowSpec:
    """Everything ``_fetch_single_parent_rows`` needs, resolved once at plan time.

    ``pristine_child_queryset`` is ``request.child_queryset`` BEFORE
    ``apply_window_pagination`` wrapped it - it carries the child plan
    (``select_related`` / ``only`` / nested prefetches / visibility hook), so the
    degenerate re-query reproduces the exact projection and deeper nesting the
    windowed body would. ``order_by`` freezes the planned deterministic order (the
    filter kwarg re-applies it). ``parent_link_attname`` is the child FK's
    ``.filter(**{attname: pid})`` kwarg; ``parent_link_column`` /
    ``parent_link_table`` match the fetch-time ``__in`` WHERE leaf (``DIRECT_FK``
    means the link lives on the child table itself). ``fetch_limit`` is the
    in-branch ``LIMIT`` (the page size plus the one ``next_page_probe`` sentinel
    row, equal to the page size when the probe is off).

    ``select_related`` (the planned child join graph) and ``select_columns`` (the
    planned ``(attname, column)`` projection, or ``None`` for a ``defer()`` shape
    ``_select_columns`` declines to model) freeze the child projection at plan
    time so ``_fetch_single_parent_rows`` can prove the fetch-time query still
    loads exactly what the windowed body would before trusting the pristine
    re-query.

    Eligibility pins ``with_total_count`` / ``reverse`` / ``offset`` and the
    keyset seek out (``single_parent_spec``), so no counted / reversed / offset /
    keyset fields ride here.
    """

    pristine_child_queryset: Any
    order_by: tuple[Any, ...]
    parent_link_attname: str
    parent_link_column: str
    parent_link_table: str
    fetch_limit: int
    select_related: Any
    select_columns: tuple[tuple[str, str], ...] | None


def single_parent_spec(request: NestedConnectionRequest) -> SingleParentWindowSpec | None:
    """Resolve the request into a single-parent fast-path spec, or ``None``.

    ``None`` (the windowed body stays) unless EVERY eligibility condition holds:

    - ``request.keyset_seek is None`` - keyset seeks are out of v1 scope; their
      cursor arithmetic is not a plain filtered ``LIMIT``.
    - ``not request.with_total_count`` - a bare ``LIMIT`` cannot produce the
      partition count, so ``totalCount``/counted shapes keep the window (whose
      ``COUNT(1) OVER ()`` scans the whole partition anyway).
    - ``not request.reverse`` - a ``last``-only page needs the reversed row
      number the window computes.
    - ``type(request.child_queryset) is QuerySet`` - a custom subclass (a manager
      or visibility hook's own class) would have its ``_clone`` state and iterator
      behavior erased by the class rebind, so anything but a plain ``QuerySet``
      keeps the windowed strategy (same rule as ``_build_lateral_spec``).
    - the join shape is ``DIRECT_FK`` with a resolved ``parent_link_field`` - M2M
      ``THROUGH_TABLE`` is correction 2's exclusion, and a generic relation is
      ``DIRECT_FK`` but leaves ``parent_link_field`` ``None`` (join_taxonomy owns
      the link resolution). The two checks fold into ONE branch: for a genuine
      ``DIRECT_FK`` FK relation ``parent_link_field`` is always resolved, so a
      separate ``is None`` arm would be unreachable and break ``fail_under=100``.
    - the window is the plain first page (``plain_first_page`` implies
      ``offset == 0`` and a bounded positive ``limit``) - the only shape a plain
      filtered ``LIMIT`` reproduces row-for-row.
    """
    if request.keyset_seek is not None:
        return None
    if request.with_total_count or request.reverse:
        return None
    if type(request.child_queryset) is not QuerySet:
        return None
    join = request.join
    if join.lateral_shape is not LateralJoinShape.DIRECT_FK or join.parent_link_field is None:
        return None
    range_plan = window_range_plan(
        offset=request.offset,
        limit=request.limit,
        reverse=request.reverse,
        next_page_probe=request.next_page_probe,
    )
    if not range_plan.plain_first_page:
        return None
    parent_link_field = join.parent_link_field
    return SingleParentWindowSpec(
        pristine_child_queryset=request.child_queryset,
        order_by=tuple(request.order_by),
        parent_link_attname=parent_link_field.attname,
        parent_link_column=parent_link_field.column,
        parent_link_table=request.child_queryset.model._meta.db_table,
        fetch_limit=range_plan.fetch_limit,
        select_related=request.child_queryset.query.select_related,
        select_columns=_select_columns(
            request.child_queryset,
            request.child_queryset.model._meta,
        ),
    )


class SingleParentWindowQuerySet(QuerySet):
    """A windowed-prefetch queryset that runs the plain page query when it can.

    Constructed only by ``WindowedPrefetchStrategy`` (via
    ``as_single_parent_queryset``): its ORM body IS the windowed queryset the
    strategy would plan, and ``_dst_single_parent_spec`` rides alongside through
    every clone (``.using()`` / ``_add_hints`` / the prefetch machinery's
    ``.filter()`` all go through ``_clone``). ``_fetch_all`` swaps in the plain
    filtered ``LIMIT`` execution only when ``_fetch_single_parent_rows``
    recognizes the fetch-time query completely; any other shape executes the
    windowed body via the superclass - Django-internals drift or a multi-parent
    fetch degrades performance, never correctness.
    """

    _dst_single_parent_spec: SingleParentWindowSpec | None = None
    # The signature of the window-range quals the PLANNED windowed body carried
    # when it was wrapped (``window_predicate_signature``), captured once so the
    # fetch-time recognizer can prove the row-number range was not mutated before
    # trusting the plain re-query. ``None`` means the planned window could not be
    # normalized, so the fast path never engages (fail closed).
    _dst_window_signature: tuple | None = None

    def _clone(self) -> SingleParentWindowQuerySet:
        clone = super()._clone()
        clone._dst_single_parent_spec = self._dst_single_parent_spec
        clone._dst_window_signature = self._dst_window_signature
        return clone

    def _fetch_all(self) -> None:
        if self._result_cache is None:
            rows = _fetch_single_parent_rows(self)
            if rows is not None:
                self._result_cache = rows
        # The superclass call is a no-op on a populated cache except for the
        # nested ``prefetch_related`` pass. Synthesized rows are usually already
        # populated (the pristine child queryset carries the nested prefetches,
        # so listing it ran them), in which case the pass skips them; the call
        # stays load-bearing for the windowed-body fallback and mirrors
        # ``lateral_fetch.py::LateralQuerySet._fetch_all``.
        super()._fetch_all()


def as_single_parent_queryset(
    queryset: Any,
    spec: SingleParentWindowSpec,
) -> SingleParentWindowQuerySet:
    """Rebind ``queryset`` (a plain windowed ``QuerySet``) as the fast-path class.

    A chain-then-reclass mirroring ``_as_lateral_queryset``:
    ``SingleParentWindowQuerySet`` adds no construction-time state beyond the spec
    attribute, so the class swap on a fresh clone is safe and keeps the windowed
    body verbatim. The planned window-range signature is captured here (from the
    windowed body BEFORE Django's prefetch machinery appends the parent ``__in``)
    so ``_fetch_single_parent_rows`` can later prove the fetch-time range is the
    one planned.
    """
    clone = queryset._chain()
    clone.__class__ = SingleParentWindowQuerySet
    clone._dst_single_parent_spec = spec
    clone._dst_window_signature = window_predicate_signature(queryset.query)
    return clone


def _single_parent_where_ids(where: Any, spec: SingleParentWindowSpec) -> list | None:
    """The parent-id list if ``where`` is "window range + ONE parent IN", else ``None``.

    The structural twin of ``lateral_fetch._recognize_lateral_fetch``'s WHERE
    walk minus the keyset/visibility arms: the root must be a non-negated ``AND``,
    each child is either a window-range qual (``_is_window_qual`` - skipped) or the
    single prefetch ``__in`` lookup on the spec's parent link column
    (``_parent_in_values``). At most one IN qual is accepted; a second
    unrecognized child - an extra consumer/visibility filter, a second IN, an
    expression rhs - fails closed to ``None`` (the windowed body runs).
    """
    if where.negated or where.connector != "AND":
        return None
    parent_ids: list | None = None
    for child in where.children:
        if _is_window_qual(child):
            continue
        if parent_ids is None:
            maybe_ids = _parent_in_values(
                child,
                column=spec.parent_link_column,
                table=spec.parent_link_table,
            )
            if maybe_ids is not None:
                parent_ids = maybe_ids
                continue
        return None
    return parent_ids


def _fetch_single_parent_rows(queryset: SingleParentWindowQuerySet) -> list | None:
    """Execute the plain page query for ``queryset`` if its state is recognized.

    Returns ``None`` for every unrecognized shape (the superclass then runs the
    windowed body): a missing spec (a queryset built outside the strategy), the
    setting disabled, a ``values()``-style iterable, a query someone mutated away
    from the planned window, an order/annotation drift, a projection or
    ``select_related`` drift away from the planned child body, a WHERE tree that
    is not "window range + one parent IN", or a parent count other than exactly
    one.
    """
    spec = queryset._dst_single_parent_spec
    if spec is None:
        return None
    # Lazy import: ``conf`` is heavy and unrelated to the plan-time path, and the
    # flag is read at FETCH time so ``override_settings`` is observed live.
    from ..conf import single_parent_fast_path_setting

    if not single_parent_fast_path_setting():
        return None
    if queryset._iterable_class is not ModelIterable:
        return None
    query = queryset.query
    if (
        query.is_sliced
        or query.distinct
        or query.select_for_update
        or query.combinator
        or query.extra
        or query.extra_tables
        or query.group_by is not None
    ):
        return None
    if tuple(query.order_by) != tuple(spec.order_by) or not query.standard_ordering:
        return None
    if set(query.annotations) != {WINDOW_ROW_NUMBER}:
        return None
    # The window quals must be EXACTLY the planned range (``window_predicate_
    # signature``), not merely "some ``Window`` lookup": the plain re-query below
    # applies ``spec.fetch_limit``, so a mutated / added / dropped row-number
    # bound that ``_single_parent_where_ids`` would skip as a window qual must be
    # caught here or it would be silently ignored. A captured ``None`` (the
    # planned window did not normalize) or any divergence downgrades to the
    # windowed body.
    planned_signature = queryset._dst_window_signature
    if planned_signature is None or window_predicate_signature(query) != planned_signature:
        return None
    # The synthesized rows come from ``spec.pristine_child_queryset``, so the
    # fetch-time projection and ``select_related`` join graph must still be the
    # planned ones - otherwise the pristine re-query would load a different set
    # of columns / related objects than the windowed body would. Mirrors
    # ``_recognize_lateral_fetch``'s projection guard (``_select_columns`` +
    # ``select_related``); any drift falls back to the windowed body.
    if query.select_related != spec.select_related:
        return None
    if _select_columns(queryset, queryset.model._meta) != spec.select_columns:
        return None
    parent_ids = _single_parent_where_ids(query.where, spec)
    if parent_ids is None:
        return None
    # ``_deduplicate_parent_ids`` (imported, single owner of the unhashable/NULL
    # semantics): zero parents falls through to the windowed body's trivially
    # empty result, and more than one parent is not the degenerate shape.
    unique = _deduplicate_parent_ids(parent_ids)
    if len(unique) != 1:
        return None
    (pid,) = unique
    # ``.using`` honors the prefetch/router alias the fetch runs under; the
    # pristine clone carries the same projection/nested prefetches the windowed
    # body would, so the synthesized rows satisfy the same ``to_attr`` contract.
    child_qs = spec.pristine_child_queryset.using(queryset.db)
    rows = list(
        child_qs.filter(**{spec.parent_link_attname: pid}).order_by(*spec.order_by)[
            : spec.fetch_limit
        ],
    )
    # Row numbers are computed BEFORE the limit applies in the windowed body, so
    # the plain page's rows carry rn 1..N exactly as the filtered shape would;
    # 1-based, page-relative == absolute (offset 0), forward order, the probe row
    # is the ``limit + 1``th. ``_dst_total_count`` is NEVER set - its ABSENCE is
    # what makes ``connection.py::_resolve_from_window`` re-infer the probe.
    for index, row in enumerate(rows):
        setattr(row, WINDOW_ROW_NUMBER, index + 1)
    logger.debug(
        "Optimizer: single-parent fast path fetched %d row(s) for parent %r via %s",
        len(rows),
        pid,
        spec.parent_link_attname,
    )
    return rows
