"""Postgres ``CROSS JOIN LATERAL`` fetch strategy for nested connections.

The second ``NestedConnectionStrategy`` backend (the Prisma
``LateralJoinSelectBuilder`` lesson; see ``optimizer/nested_fetch.py`` for the
seam contract). The windowed default computes ``ROW_NUMBER()`` over EVERY
child of every selected parent before filtering to the page - O(sum of all
partition sizes) per request. A lateral join instead runs the page query once
per parent id::

    SELECT "__dst_parents"."__dst_parent_id", w.<cols>, w."_dst_row_number", ...
    FROM unnest(%s::bigint[]) AS "__dst_parents"("__dst_parent_id")
    CROSS JOIN LATERAL (
        SELECT <only-cols>,
               ROW_NUMBER() OVER (ORDER BY <order>) AS "_dst_row_number"
               [, COUNT(1) OVER () AS "_dst_total_count"]
        FROM <child> [INNER JOIN <through> ...]
        WHERE <link>.<parent-column> = "__dst_parents"."__dst_parent_id"
    ) "__dst_window"
    WHERE <the exact row-number range ``apply_window_pagination`` plans>
    ORDER BY "__dst_parents"."__dst_parent_id", "__dst_window"."_dst_row_number"

which Postgres (>= 15, via the monotonic-window-function run condition)
stops after ``offset + limit`` rows per parent - O(parents x page). The row
numbers, the range predicate (including workstream C's ambiguous-shape
markers), and the forward return order are byte-mirrors of
``plans.py::apply_window_pagination``, so the rows satisfy the ``to_attr``
contract and inherit the entire connection fast path
(``connection.py::_resolve_from_window``) untouched.

Correctness never rides on the raw SQL: ``LateralPrefetchStrategy.plan``
builds the SAME windowed queryset the default strategy would and carries the
lateral spec alongside it on a ``LateralQuerySet``. At fetch time the
queryset swaps in the lateral SQL only when everything it expects holds -
Postgres vendor, plain model iteration, and a WHERE tree that is exactly
"the window range we planned + the parent-id IN filter Django's prefetch
machinery adds" (``_filter_prefetch_queryset``: ``Q(<field>__in=parents)``
with the rhs already normalized to pk values). Anything unrecognized - a
Django-internals drift, a consumer mutation, a non-Postgres ``.using()``
route - falls through to the superclass ``_fetch_all``, which executes the
windowed body: a performance downgrade, never a correctness cliff.

Plan-time shapes the lateral SQL cannot express (a pre-filtered child
queryset, ``select_related``, child annotations, expression ordering, a
composite primary key) downgrade INSIDE the strategy to the windowed plan -
the selection is still planned, so Decision-6 strictness visibility is
unaffected. The walker-owned fallback shapes (sidecar, divergent aliases,
SKIP, DISTINCT, malformed slice, unwindowable join) never reach any strategy.

SQL-injection surface: every identifier in ``build_lateral_sql`` passes
through ``connection.ops.quote_name`` and every VALUE (parent ids, offsets,
limits) is a query parameter; nothing user-controlled is interpolated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import connections
from django.db.models import QuerySet
from django.db.models.expressions import Window
from django.db.models.query import ModelIterable

from .join_taxonomy import LateralJoinShape
from .nested_fetch import (
    WINDOWED_STRATEGY,
    NestedConnectionRequest,
    attach_windowed_prefetch,
)
from .plans import (
    WINDOW_ROW_NUMBER,
    WINDOW_ROW_NUMBER_REVERSED,
    WINDOW_TOTAL_COUNT,
    OptimizationPlan,
    deferred_loading_of,
    order_entry_name_and_direction,
    window_range_plan,
)

#: The ``unnest`` alias/column the lateral SQL binds parent ids to. The
#: ``__dst`` prefix keeps them out of any model's column namespace.
LATERAL_PARENT_ALIAS = "__dst_parents"
LATERAL_PARENT_COLUMN = "__dst_parent_id"
LATERAL_WINDOW_ALIAS = "__dst_window"

#: Annotations the planned windowed body owns; any OTHER annotation on the
#: queryset at fetch time means someone mutated it - fall back.
_WINDOW_ANNOTATIONS = frozenset(
    {WINDOW_ROW_NUMBER, WINDOW_TOTAL_COUNT, WINDOW_ROW_NUMBER_REVERSED},
)


@dataclass(frozen=True)
class LateralWindowSpec:
    """Everything ``build_lateral_sql`` needs, resolved once at plan time.

    ``select_columns`` is the ``(attname, db column)`` projection in
    ``concrete_fields`` order (the ``Model.from_db`` deferred-instance
    contract); ``order_columns`` is the deterministic connection order as
    ``(db column, descending)`` pairs; ``parent_link_field`` is the FK whose
    column matches each parent id (on the child table for ``DIRECT_FK``, on
    the through table for ``THROUGH_TABLE``) - its ``db_type`` provides the
    ``unnest`` array cast at fetch time; ``prefetch_value_aliases`` are the
    ``_prefetch_related_val_<attname>`` attributes Django's M2M prefetch
    reads to attach rows to parents (their value IS the parent id the row's
    lateral branch was joined on).
    """

    model: type
    db_table: str
    select_columns: tuple[tuple[str, str], ...]
    order_columns: tuple[tuple[str, bool], ...]
    parent_link_field: Any
    parent_link_table: str
    parent_link_column: str
    through_table: str | None
    through_child_column: str | None
    child_pk_column: str
    prefetch_value_aliases: tuple[str, ...]
    offset: int
    limit: int | None
    reverse: bool
    with_total_count: bool


def build_lateral_sql(
    spec: LateralWindowSpec,
    parent_ids: list,
    *,
    quote_name: Any,
    array_cast: str | None = None,
) -> tuple[str, list]:
    """Render the lateral page query for ``spec`` over ``parent_ids``.

    Pure: identifiers are quoted through the passed ``quote_name``
    (``connection.ops.quote_name`` in production, so the builder is fully
    unit-testable on SQLite), and every value - the parent-id array, the
    row-number bounds - is a parameter. ``array_cast`` (the parent link
    column's ``db_type``, e.g. ``"bigint"``) makes the ``unnest`` element
    type explicit; ``None`` leaves it to the driver's array typing.

    The row-number range predicate reproduces ``apply_window_pagination``
    branch for branch (forward bounds, workstream C's ``OR rn = 1`` marker
    for the ambiguous shapes, the reversed row number for ``last``-only
    windows, ``None``/``sys.maxsize`` as "no upper bound") so a lateral page
    is row-for-row the windowed page.

    The common unambiguous forward page (``first: N``: ``offset == 0``,
    bounded positive limit) is emitted as ``ORDER BY <order> LIMIT %s``
    INSIDE the lateral branch instead of an outer row-number filter - the
    same row set with the same row numbers, but a shape the Postgres planner
    can COST: a ``LIMIT`` makes it pick an order-satisfying index and stop
    each branch after N rows, where the equivalent ``rn <= N`` filter relies
    on the (uncosted) window run condition and loses the ordered-index plan
    to a full per-partition sort (the Prisma ``LateralJoinSelectBuilder``
    lesson). With ``with_total_count`` the branch still scans its whole
    partition - the count is inherently O(partition) under either shape.
    """
    qn = quote_name
    child = qn(spec.db_table)
    parents = qn(LATERAL_PARENT_ALIAS)
    pid = f"{parents}.{qn(LATERAL_PARENT_COLUMN)}"
    window = qn(LATERAL_WINDOW_ALIAS)
    rn = f"{window}.{qn(WINDOW_ROW_NUMBER)}"

    def order_sql(*, descending_flip: bool) -> str:
        return ", ".join(
            f"{child}.{qn(column)} {'DESC' if descending != descending_flip else 'ASC'}"
            for column, descending in spec.order_columns
        )

    inner_select = [f"{child}.{qn(column)}" for _, column in spec.select_columns]
    inner_select.append(
        f"ROW_NUMBER() OVER (ORDER BY {order_sql(descending_flip=False)}) AS {qn(WINDOW_ROW_NUMBER)}",
    )
    if spec.reverse:
        inner_select.append(
            f"ROW_NUMBER() OVER (ORDER BY {order_sql(descending_flip=True)})"
            f" AS {qn(WINDOW_ROW_NUMBER_REVERSED)}",
        )
    if spec.with_total_count:
        inner_select.append(f"COUNT(1) OVER () AS {qn(WINDOW_TOTAL_COUNT)}")
    if spec.through_table is not None:
        through = qn(spec.through_table)
        from_sql = (
            f"{through} INNER JOIN {child}"
            f" ON {child}.{qn(spec.child_pk_column)} = {through}.{qn(spec.through_child_column)}"
        )
        link_table = through
    else:
        from_sql = child
        link_table = child
    lateral_sql = (
        f"SELECT {', '.join(inner_select)} FROM {from_sql}"
        f" WHERE {link_table}.{qn(spec.parent_link_column)} = {pid}"
    )

    # The range predicate: the shared ``window_range_plan`` decisions (the
    # same plan ``apply_window_pagination`` renders as ``Q`` objects), here
    # rendered as raw SQL - only the rendering is lateral-specific.
    range_parts: list[str] = []
    params: list = [list(parent_ids)]
    range_plan = window_range_plan(offset=spec.offset, limit=spec.limit, reverse=spec.reverse)
    if range_plan.plain_first_page:
        # ``first: N``: in-branch ORDER BY + LIMIT (see the docstring). The
        # row numbers are computed BEFORE the limit applies, so the returned
        # rows carry rn 1..N exactly as the filtered shape would.
        lateral_sql += f" ORDER BY {order_sql(descending_flip=False)} LIMIT %s"
        params.append(range_plan.limit)
        where_sql = ""
    else:
        if range_plan.lower_bound is not None:
            range_parts.append(f"{rn} > %s")
            params.append(range_plan.lower_bound)
        if range_plan.upper_bound is not None:
            bound_column = (
                f"{window}.{qn(WINDOW_ROW_NUMBER_REVERSED)}" if range_plan.reverse else rn
            )
            range_parts.append(f"{bound_column} <= %s")
            params.append(range_plan.upper_bound)
        where_sql = " AND ".join(range_parts)
        if range_plan.add_marker_rows:
            # Workstream C's ambiguous-shape marker: keep each parent's row 1
            # so an empty page and a childless parent stay distinguishable.
            where_sql = f"({where_sql}) OR {rn} = 1"

    outer_select = [pid]
    outer_select.extend(f"{window}.{qn(column)}" for _, column in spec.select_columns)
    outer_select.append(rn)
    if spec.with_total_count:
        outer_select.append(f"{window}.{qn(WINDOW_TOTAL_COUNT)}")
    array_param = "%s" if array_cast is None else f"%s::{array_cast}[]"
    sql = (
        f"SELECT {', '.join(outer_select)}"
        f" FROM unnest({array_param}) AS {parents}({qn(LATERAL_PARENT_COLUMN)})"
        f" CROSS JOIN LATERAL ({lateral_sql}) {window}"
    )
    if where_sql:
        sql += f" WHERE {where_sql}"
    sql += f" ORDER BY {pid}, {rn}"
    return sql, params


class LateralQuerySet(QuerySet):
    """A windowed-prefetch queryset that executes lateral SQL when it can.

    Constructed only by ``LateralPrefetchStrategy`` (via
    ``_as_lateral_queryset``): its ORM body IS the windowed queryset the
    default strategy would plan, and ``_dst_lateral_spec`` rides alongside
    through every clone (``.using()`` / ``_add_hints`` / the prefetch
    machinery's ``.filter()`` all go through ``_clone``). ``_fetch_all``
    swaps in the lateral execution only when ``_fetch_lateral_rows``
    recognizes the fetch-time query completely; any other shape executes the
    windowed body via the superclass - Django-internals drift degrades
    performance, never correctness.
    """

    _dst_lateral_spec: LateralWindowSpec | None = None

    def _clone(self) -> LateralQuerySet:
        clone = super()._clone()
        clone._dst_lateral_spec = self._dst_lateral_spec
        return clone

    def _fetch_all(self) -> None:
        if self._result_cache is None:
            rows = _fetch_lateral_rows(self)
            if rows is not None:
                self._result_cache = rows
        # The superclass call is a no-op on a populated cache except for the
        # nested ``prefetch_related`` pass - which the lateral rows need too.
        super()._fetch_all()


def _fetch_lateral_rows(queryset: LateralQuerySet) -> list | None:
    """Execute the lateral SQL for ``queryset`` if its state is recognized.

    Returns ``None`` for every unrecognized shape (the superclass then runs
    the windowed body): missing spec (a queryset constructed outside the
    strategy), a non-Postgres connection (``.using()`` re-routing), a
    ``values()``-style iterable, or a query whose WHERE tree
    ``_extract_parent_ids`` cannot prove is "window range + parent IN".
    """
    spec = queryset._dst_lateral_spec
    if spec is None:
        return None
    connection = connections[queryset.db]
    if connection.vendor != "postgresql":
        return None
    if queryset._iterable_class is not ModelIterable:
        return None
    parent_ids = _extract_parent_ids(queryset, spec)
    if parent_ids is None:
        return None
    if not parent_ids:
        return []
    sql, params = build_lateral_sql(
        spec,
        parent_ids,
        quote_name=connection.ops.quote_name,
        array_cast=spec.parent_link_field.db_type(connection),
    )
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        fetched = cursor.fetchall()
    return [_instantiate_row(spec, row, queryset.db) for row in fetched]


def _extract_parent_ids(queryset: LateralQuerySet, spec: LateralWindowSpec) -> list | None:
    """Pull the parent-id list Django's prefetch filter added, or ``None``.

    The fetch-time query must be EXACTLY the planned windowed body plus
    ``_filter_prefetch_queryset``'s additions: annotations limited to the
    window names, ``extra(select=...)`` limited to the M2M
    ``_prefetch_related_val_*`` aliases the spec predicted, and a WHERE tree
    whose children are window-range quals (their ``lhs`` is the cloned
    ``Window`` expression - including workstream C's nested marker OR node)
    plus ONE ``__in`` lookup on the spec's parent link column with an
    already-normalized value list (``RelatedIn`` resolves model instances to
    pk values at construction). Anything else - an unexpected filter, a
    second IN, an expression rhs, a slice - returns ``None``.
    """
    query = queryset.query
    if query.is_sliced or query.distinct or query.select_related:
        return None
    if set(query.annotations) - _WINDOW_ANNOTATIONS:
        return None
    if set(query.extra or ()) != set(spec.prefetch_value_aliases):
        return None
    where = query.where
    if where.negated or where.connector != "AND":
        return None
    parent_ids: list | None = None
    for child in where.children:
        if _is_window_qual(child):
            continue
        if parent_ids is None:
            parent_ids = _parent_in_values(child, spec)
            if parent_ids is not None:
                continue
        return None
    return parent_ids


def _is_window_qual(node: Any) -> bool:
    """True if ``node`` constrains only the planned window annotations.

    A window-range lookup carries the cloned ``Window`` expression as its
    ``lhs``; the ambiguous-shape marker filter arrives as a nested
    ``WhereNode`` (``(range) OR rn = 1``) whose leaves all do.
    """
    children = getattr(node, "children", None)
    if children is not None:
        return not node.negated and all(_is_window_qual(sub) for sub in children)
    return isinstance(getattr(node, "lhs", None), Window)


def _parent_in_values(node: Any, spec: LateralWindowSpec) -> list | None:
    """The parent-id list if ``node`` is the prefetch ``__in`` filter, else ``None``.

    Matches by the lookup's target column AND table (the child table for
    ``DIRECT_FK``, the through table for ``THROUGH_TABLE`` - Django's
    ``reuse_all=True`` join reuse resolves the M2M path to the through FK
    column directly) and requires a plain expression-free value list.
    """
    if getattr(node, "lookup_name", None) != "in":
        return None
    target = getattr(getattr(node, "lhs", None), "target", None)
    if target is None or getattr(target, "column", None) != spec.parent_link_column:
        return None
    if target.model._meta.db_table != spec.parent_link_table:
        return None
    rhs = node.rhs
    if not isinstance(rhs, (list, tuple)):
        return None
    if any(hasattr(value, "resolve_expression") for value in rhs):
        return None
    return list(rhs)


def _instantiate_row(spec: LateralWindowSpec, row: tuple, db: str) -> Any:
    """Build one model instance from a lateral result row.

    Column order is fixed by ``build_lateral_sql``: parent id, the
    ``select_columns`` projection, ``_dst_row_number``, then
    ``_dst_total_count`` when planned. ``Model.from_db`` yields the same
    deferred-instance shape the windowed ``.only()`` path produces; the
    window attributes and (for M2M) the ``_prefetch_related_val_*``
    parent-id attributes are set exactly as Django's iterators would.
    """
    width = len(spec.select_columns)
    parent_id = row[0]
    instance = spec.model.from_db(
        db,
        [attname for attname, _ in spec.select_columns],
        row[1 : 1 + width],
    )
    setattr(instance, WINDOW_ROW_NUMBER, row[1 + width])
    if spec.with_total_count:
        setattr(instance, WINDOW_TOTAL_COUNT, row[2 + width])
    for alias in spec.prefetch_value_aliases:
        setattr(instance, alias, parent_id)
    return instance


class LateralPrefetchStrategy:
    """Plan nested connections as lateral-capable windowed prefetches.

    Shapes the lateral SQL cannot express downgrade to the windowed plan
    INSIDE ``plan`` (still planned - strictness visibility is a walker
    concern and unaffected); everything else carries a ``LateralQuerySet``
    whose body is the identical windowed queryset, so the worst case of any
    fetch-time surprise is windowed performance.
    """

    name = "lateral"

    def plan(self, request: NestedConnectionRequest, plan: OptimizationPlan) -> bool:
        """Attach the lateral-capable windowed prefetch (or downgrade)."""
        spec = _build_lateral_spec(request)
        if spec is None:
            return WINDOWED_STRATEGY.plan(request, plan)
        # The shared windowed floor (``attach_windowed_prefetch``) with the
        # lateral spec riding alongside: the lateral body IS the windowed body.
        return attach_windowed_prefetch(
            request,
            plan,
            wrap=lambda queryset: _as_lateral_queryset(queryset, spec),
        )


#: The shared lateral-strategy singleton (stateless, like the windowed one).
LATERAL_STRATEGY = LateralPrefetchStrategy()


def _as_lateral_queryset(queryset: Any, spec: LateralWindowSpec) -> LateralQuerySet:
    """Rebind ``queryset`` (a plain windowed ``QuerySet``) as a ``LateralQuerySet``.

    A chain-then-reclass: ``LateralQuerySet`` adds no construction-time state
    beyond the spec attribute, so the class swap on a fresh clone is safe and
    keeps the windowed body verbatim.
    """
    clone = queryset._chain()
    clone.__class__ = LateralQuerySet
    clone._dst_lateral_spec = spec
    return clone


def _build_lateral_spec(request: NestedConnectionRequest) -> LateralWindowSpec | None:
    """Resolve the request into a lateral spec, or ``None`` to downgrade.

    ``None`` for every plan-time shape the lateral SQL cannot express:

    - a custom ``QuerySet`` subclass (a manager or visibility hook's own
      class) - ``_as_lateral_queryset``'s class rebind would erase subclass
      ``_clone`` state and iterator behavior, so anything but a plain
      ``QuerySet`` keeps the windowed strategy, which preserves the class;
    - a child queryset carrying filters (a custom ``get_queryset`` or a
      pre-filtered/visibility-scoped manager), ``select_related``,
      annotations, or ``extra`` - the lateral subquery reproduces none of
      those;
    - an ordering that is not plain local concrete columns (expressions,
      ``__`` traversals);
    - a ``defer()``-shaped projection (the ``.only()`` walker contract is
      the supported shape) or a composite/columnless primary key.
    """
    child_queryset = request.child_queryset
    query = child_queryset.query
    if query.where.children or query.select_related or query.annotations or query.extra:
        return None
    child_meta = child_queryset.model._meta
    child_pk_column = getattr(child_meta.pk, "column", None)
    if child_pk_column is None:
        return None  # composite primary key - no single unnest join column.
    if type(child_queryset) is not QuerySet:
        return None  # custom subclass - the lateral class rebind would erase it.
    order_columns = _order_columns(request.order_by, child_meta)
    if order_columns is None:
        return None
    select_columns = _select_columns(child_queryset, child_meta)
    if select_columns is None:
        return None
    # Only the five link-shaped fields differ between the two join shapes;
    # the resolved link FIELD OBJECTS come from the request's join descriptor
    # (``join_taxonomy.classify_relation_join`` owns everything join-shaped a
    # relation field implies - this function only READS it).
    join = request.join
    parent_link_field = join.parent_link_field
    if join.lateral_shape is LateralJoinShape.THROUGH_TABLE:
        through_table = parent_link_field.model._meta.db_table
        parent_link_table = through_table
        through_child_column = join.through_child_field.column
        prefetch_value_aliases: tuple[str, ...] = (
            f"_prefetch_related_val_{parent_link_field.attname}",
        )
    else:
        # DIRECT_FK: the child table itself carries the parent id (reverse FK /
        # reverse one-to-one; the walker never plans forward-single relations).
        through_table = None
        parent_link_table = child_meta.db_table
        through_child_column = None
        prefetch_value_aliases = ()
    return LateralWindowSpec(
        model=child_queryset.model,
        db_table=child_meta.db_table,
        select_columns=select_columns,
        order_columns=order_columns,
        parent_link_field=parent_link_field,
        parent_link_table=parent_link_table,
        parent_link_column=parent_link_field.column,
        through_table=through_table,
        through_child_column=through_child_column,
        child_pk_column=child_pk_column,
        prefetch_value_aliases=prefetch_value_aliases,
        offset=request.offset,
        limit=request.limit,
        reverse=request.reverse,
        with_total_count=request.with_total_count,
    )


def _order_columns(order_by: tuple, child_meta: Any) -> tuple[tuple[str, bool], ...] | None:
    """Map the deterministic order onto local concrete columns, or ``None``.

    The lateral builder renders plain ``"column" ASC/DESC`` entries (matching
    what Django emits on Postgres for string orderings, so window row numbers
    cannot drift from the windowed body's). Expression entries, relation
    traversals, ``"?"``, and names that are not local concrete fields
    downgrade to windowed.
    """
    columns: list[tuple[str, bool]] = []
    for entry in order_by:
        if not isinstance(entry, str):
            return None
        parsed = order_entry_name_and_direction(entry)
        if parsed is None:
            return None
        name, descending = parsed
        if name == "?" or "__" in name:
            return None
        if name == "pk":
            name = child_meta.pk.attname
        field = next(
            (f for f in child_meta.concrete_fields if name in (f.name, f.attname)),
            None,
        )
        if field is None:
            return None
        columns.append((field.column, descending))
    return tuple(columns)


def _select_columns(queryset: Any, child_meta: Any) -> tuple[tuple[str, str], ...] | None:
    """The loaded ``(attname, column)`` projection in concrete-field order.

    Mirrors the ``.only()`` deferred-loading shape the walker plans (names
    plus the pk); the full projection when nothing is deferred. A ``defer()``
    shape (exclusion list) is not a walker product - downgrade rather than
    re-implement Django's defer semantics. The Django-private
    ``deferred_loading`` read goes through the shared
    ``plans.py::deferred_loading_of`` (never ``None`` here - the strategy
    only reaches this with a real ``QuerySet``).
    """
    names, defer = deferred_loading_of(queryset)
    if defer:
        if names:
            return None
        return tuple((f.attname, f.column) for f in child_meta.concrete_fields)
    return tuple(
        (f.attname, f.column)
        for f in child_meta.concrete_fields
        if f.primary_key or f.name in names or f.attname in names
    )
