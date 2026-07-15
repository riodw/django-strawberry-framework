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
composite primary key, or selected/ordered columns from a multi-table
inheritance parent) downgrade INSIDE the strategy to the windowed plan - the
selection is still planned, so Decision-6 strictness visibility is unaffected.
The walker-owned fallback shapes (sidecar, SKIP, DISTINCT, malformed slice,
unwindowable join) never reach any strategy; divergent aliases arrive as one
request per response key, each self-contained.

SQL-injection surface: every identifier in ``build_lateral_sql`` passes
through ``connection.ops.quote_name`` and every VALUE (parent ids, offsets,
limits) is a query parameter; nothing user-controlled is interpolated.

Scalar parent keys use one typed Postgres array parameter, keeping SQL text and
parameter count constant as the parent page grows. JSON, array, range, and
other non-scalar/custom key types use individually prepared typed ``VALUES``
rows instead: wrapping those values in a second array changes psycopg's
adaptation semantics and was the source of incorrect parent-key fidelity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import connections
from django.db.models import QuerySet
from django.db.models.expressions import Window
from django.db.models.query import ModelIterable

from ..keyset import keyset_seek_greater
from ..utils.connections import assert_window_fetch_mode_for, window_range_plan
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
)

#: The typed parent-relation alias/column the lateral SQL binds parent ids to.
#: The ``__dst`` prefix keeps them out of any model's column namespace.
LATERAL_PARENT_ALIAS = "__dst_parents"
LATERAL_PARENT_COLUMN = "__dst_parent_id"
LATERAL_WINDOW_ALIAS = "__dst_window"
LATERAL_CHILD_ALIAS = "__dst_child"
LATERAL_THROUGH_ALIAS = "__dst_through"

# Django scalar field identities that psycopg can safely adapt as one Postgres
# array parameter after per-element ``get_db_prep_value``. Unknown/custom and
# structured field types deliberately take the typed ``VALUES`` fallback.
_ARRAY_BINDABLE_PARENT_FIELD_TYPES = frozenset(
    {
        "AutoField",
        "BigAutoField",
        "BigIntegerField",
        "BinaryField",
        "BooleanField",
        "CharField",
        "DateField",
        "DateTimeField",
        "DecimalField",
        "DurationField",
        "EmailField",
        "FilePathField",
        "FloatField",
        "GenericIPAddressField",
        "IntegerField",
        "PositiveBigIntegerField",
        "PositiveIntegerField",
        "PositiveSmallIntegerField",
        "SlugField",
        "SmallAutoField",
        "SmallIntegerField",
        "TextField",
        "TimeField",
        "URLField",
        "UUIDField",
    },
)

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
    per-value parent cast at fetch time; ``prefetch_value_aliases`` are the
    ``_prefetch_related_val_<attname>`` attributes Django's M2M prefetch
    reads to attach rows to parents (their value IS the parent id the row's
    lateral branch was joined on). ``query_order_by`` freezes the planned
    ordering, while ``select_fields`` carries the Django expressions whose
    converter chains raw cursor rows must pass through.
    """

    model: type
    db_table: str
    select_columns: tuple[tuple[str, str], ...]
    select_fields: tuple[Any, ...]
    order_columns: tuple[tuple[str, bool], ...]
    query_order_by: tuple[Any, ...]
    parent_link_field: Any
    parent_link_table: str
    parent_link_column: str
    through_table: str | None
    through_child_column: str | None
    child_join_column: str
    prefetch_value_aliases: tuple[str, ...]
    offset: int
    limit: int | None
    reverse: bool
    with_total_count: bool
    next_page_probe: bool = False
    # The count-free keyset value seek (``keyset.KeysetSeek``) riding this
    # spec, or ``None``. Only the COUNT-FREE shape reaches the lateral SQL -
    # the counted keyset shape downgrades to the windowed strategy inside
    # ``LateralPrefetchStrategy.plan`` (its qualify-wrapped filtered-count
    # window is already the whole-partition scan the count forces, so raw
    # SQL would buy nothing and cost a second dialect of the marker/count
    # arithmetic). The seek's columns are the window's ``order_columns`` in
    # the same sequence (the ``cursor_field`` IS the order), which
    # ``build_lateral_sql`` relies on when rendering the seek.
    keyset_seek: Any | None = None

    def __post_init__(self) -> None:
        """Enforce the probe/count mutual-exclusion on the lateral window spec.

        The lateral twin of ``NestedConnectionRequest.__post_init__``: the same
        shared ``assert_window_fetch_mode_for`` so the raw-SQL backend cannot
        develop a different fetch-mode contract from the ORM window.
        """
        assert_window_fetch_mode_for(
            offset=self.offset,
            limit=self.limit,
            reverse=self.reverse,
            with_total_count=self.with_total_count,
            next_page_probe=self.next_page_probe,
        )


def build_lateral_sql(
    spec: LateralWindowSpec,
    parent_ids: list,
    *,
    quote_name: Any,
    parent_cast: str | None = None,
    prepare_value: Any | None = None,
) -> tuple[str, list]:
    """Render the lateral page query for ``spec`` over ``parent_ids``.

    Pure: identifiers are quoted through the passed ``quote_name``
    (``connection.ops.quote_name`` in production, so the builder is fully
    unit-testable on SQLite), and every value - the parent ids and every
    row-number bound - is a parameter. ``parent_cast`` (the parent link
    column's ``db_type``, e.g. ``"bigint"``) types the parent relation.
    Scalar target fields bind all ids as one typed array parameter through
    ``unnest``; structured or unknown target fields use one typed ``VALUES``
    parameter per id so field-specific adapters retain their value semantics.
    ``None`` leaves parent values to the driver's parameter typing and thus
    uses ``VALUES``.
    ``prepare_value`` applies the parent-link and keyset-column fields'
    database adapters to their values. Production passes
    ``Field.get_db_prep_value``; pure builder tests may omit it for
    already-adaptable scalar values.

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
    child_table = qn(spec.db_table)
    child = qn(LATERAL_CHILD_ALIAS)
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
        through_table = qn(spec.through_table)
        through = qn(LATERAL_THROUGH_ALIAS)
        from_sql = (
            f"{through_table} AS {through} INNER JOIN {child_table} AS {child}"
            f" ON {child}.{qn(spec.child_join_column)} = {through}.{qn(spec.through_child_column)}"
        )
        link_table = through
    else:
        from_sql = f"{child_table} AS {child}"
        link_table = child
    lateral_sql = (
        f"SELECT {', '.join(inner_select)} FROM {from_sql}"
        f" WHERE {link_table}.{qn(spec.parent_link_column)} = {pid}"
    )

    # The range predicate: the shared ``window_range_plan`` decisions (the
    # same plan ``apply_window_pagination`` renders as ``Q`` objects), here
    # rendered as raw SQL - only the rendering is lateral-specific.
    range_parts: list[str] = []
    prepared_parent_ids = [
        prepare_value(spec.parent_link_field, value) if prepare_value is not None else value
        for value in parent_ids
    ]
    target_field = spec.parent_link_field.target_field
    use_parent_array = (
        parent_cast is not None
        and target_field.get_internal_type() in _ARRAY_BINDABLE_PARENT_FIELD_TYPES
    )
    params: list = [prepared_parent_ids] if use_parent_array else list(prepared_parent_ids)
    if spec.keyset_seek is not None:
        # The keyset value seek, INSIDE the lateral branch: paired with the
        # in-branch ``ORDER BY ... LIMIT`` below this is the O(page) shape -
        # Postgres seeks a ``(cursor columns..., pk)`` index to the cursor
        # position and stops each branch after the page. Values are bound as
        # query parameters prepared through each cursor column's Django field
        # adapter (JSONField and custom fields cannot rely on the driver's
        # native Python adaptation); nothing is interpolated.
        seek_sql, seek_params = _keyset_seek_sql(
            spec,
            qn,
            child,
            prepare_value=prepare_value,
        )
        lateral_sql += f" AND ({seek_sql})"
        params.extend(seek_params)
    range_plan = window_range_plan(
        offset=spec.offset,
        limit=spec.limit,
        reverse=spec.reverse,
        next_page_probe=spec.next_page_probe,
    )
    if range_plan.plain_first_page:
        # ``first: N``: in-branch ORDER BY + LIMIT (see the docstring). The
        # row numbers are computed BEFORE the limit applies, so the returned
        # rows carry rn 1..N exactly as the filtered shape would. ``fetch_limit``
        # is the page size plus the one ``next_page_probe`` sentinel row (equal
        # to ``limit`` when the probe is off), so the count-free ``hasNextPage``
        # overfetch is a single-token change here and the resolver drops the
        # sentinel.
        lateral_sql += f" ORDER BY {order_sql(descending_flip=False)} LIMIT %s"
        params.append(range_plan.fetch_limit)
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
    if use_parent_array:
        parent_relation = f"unnest(%s::{parent_cast}[])"
    else:
        parent_param = "%s" if parent_cast is None else f"%s::{parent_cast}"
        parent_values = ", ".join(f"({parent_param})" for _ in prepared_parent_ids)
        parent_relation = f"(VALUES {parent_values})"
    sql = (
        f"SELECT {', '.join(outer_select)}"
        f" FROM {parent_relation} AS {parents}({qn(LATERAL_PARENT_COLUMN)})"
        f" CROSS JOIN LATERAL ({lateral_sql}) {window}"
    )
    if where_sql:
        sql += f" WHERE {where_sql}"
    sql += f" ORDER BY {pid}, {rn}"
    return sql, params


def _keyset_seek_sql(
    spec: LateralWindowSpec,
    qn: Any,
    child: str,
    *,
    prepare_value: Any | None,
) -> tuple[str, list]:
    """Render the in-branch keyset seek for ``spec`` as ``(sql, params)``.

    Uniform directions emit the native row-value comparison
    ``(a, b) > (%s, %s)`` - the exact index-seek form Postgres optimizes
    best; mixed ASC/DESC directions (which row-value SQL cannot express)
    emit the same redundant-leading-bound OR-expansion the ORM Q-builder
    renders, so the two dialects seek the identical row set. The seek
    columns ARE ``spec.order_columns`` (the ``cursor_field`` is the window
    order), aligned index-for-index with the decoded cursor values -
    ``_build_lateral_spec`` guarantees the arity.
    """
    seek = spec.keyset_seek
    values = [
        prepare_value(column.field, value) if prepare_value is not None else value
        for column, value in zip(seek.columns, seek.cursor.values, strict=True)
    ]
    columns = spec.order_columns
    refs = [f"{child}.{qn(column)}" for column, _ in columns]
    greater = [keyset_seek_greater(descending, flip=seek.flip) for _, descending in columns]
    if len(set(greater)) == 1:
        op = ">" if greater[0] else "<"
        if len(refs) == 1:
            return f"{refs[0]} {op} %s", values
        placeholders = ", ".join(["%s"] * len(refs))
        return f"({', '.join(refs)}) {op} ({placeholders})", list(values)
    params: list = [values[0]]
    lead = f"{refs[0]} {'>=' if greater[0] else '<='} %s"
    or_parts: list[str] = []
    for index in range(len(columns)):
        arm_sql: list[str] = []
        for j in range(index):
            arm_sql.append(f"{refs[j]} = %s")
            params.append(values[j])
        arm_sql.append(f"{refs[index]} {'>' if greater[index] else '<'} %s")
        params.append(values[index])
        or_parts.append(f"({' AND '.join(arm_sql)})" if len(arm_sql) > 1 else arm_sql[0])
    return f"{lead} AND ({' OR '.join(or_parts)})", params


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
    # Repeated parent rows would execute duplicate lateral branches and inflate
    # every attached child page, so de-duplicate them before binding.
    parent_ids = _deduplicate_parent_ids(parent_ids)
    if not parent_ids:
        return []
    sql, params = build_lateral_sql(
        spec,
        parent_ids,
        quote_name=connection.ops.quote_name,
        parent_cast=spec.parent_link_field.db_type(connection),
        prepare_value=lambda field, value: field.get_db_prep_value(
            value,
            connection,
            prepared=False,
        ),
    )
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        fetched = _apply_lateral_converters(spec, cursor.fetchall(), connection)
    return [_instantiate_row(spec, row, queryset.db) for row in fetched]


def _deduplicate_parent_ids(parent_ids: list) -> list:
    """De-duplicate hashable parent ids; discard NULL ids that cannot match a branch."""
    try:
        unique = dict.fromkeys(parent_ids)
        unique.pop(None, None)
        return list(unique)
    except TypeError:
        # Unhashable values cannot be represented by the ordered dict, so
        # retain their original order and only remove non-matching NULLs.
        return [value for value in parent_ids if value is not None]


def _apply_lateral_converters(spec: LateralWindowSpec, rows: list, connection: Any) -> list:
    """Apply Django's backend + field converter chain to raw cursor rows."""
    expressions = [
        spec.parent_link_field.target_field.get_col(spec.parent_link_table),
        *(field.get_col(spec.db_table) for field in spec.select_fields),
    ]
    converters = {}
    for position, expression in enumerate(expressions):
        chain = connection.ops.get_db_converters(expression) + expression.get_db_converters(
            connection,
        )
        if chain:
            converters[position] = (chain, expression)
    converted = []
    for raw_row in rows:
        row = list(raw_row)
        for position, (chain, expression) in converters.items():
            value = row[position]
            for converter in chain:
                value = converter(value, expression, connection)
            row[position] = value
        converted.append(tuple(row))
    return converted


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
    if (
        query.is_sliced
        or query.distinct
        or query.select_related
        or query.select_for_update
        or query.combinator
        or query.extra_tables
        or query.group_by is not None
    ):
        return None
    if tuple(query.order_by) != spec.query_order_by or not query.standard_ordering:
        return None
    if _select_columns(queryset, queryset.model._meta) != spec.select_columns:
        return None
    if set(query.annotations) - _WINDOW_ANNOTATIONS:
        return None
    if set(query.extra or ()) != set(spec.prefetch_value_aliases):
        return None
    where = query.where
    if where.negated or where.connector != "AND":
        return None
    parent_ids: list | None = None
    unrecognized: list[Any] = []
    for child in where.children:
        if _is_window_qual(child):
            continue
        if parent_ids is None:
            maybe_ids = _parent_in_values(child, spec)
            if maybe_ids is not None:
                parent_ids = maybe_ids
                continue
        unrecognized.append(child)
    if spec.keyset_seek is not None:
        # The planned count-free keyset body carries the seek in its base
        # WHERE (the windowed-fallback correctness floor); the fetch-time
        # tree must contain EXACTLY that seek - structurally verified
        # against the spec - and nothing else. Any other residue means a
        # consumer/Django mutation: fall back to the windowed body.
        if not _keyset_seek_quals_match(unrecognized, spec):
            return None
    elif unrecognized:
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


def _keyset_seek_quals_match(nodes: list[Any], spec: LateralWindowSpec) -> bool:
    """Whether ``nodes`` are exactly the planned keyset seek's WHERE residue.

    ``keyset.keyset_seek_q`` builds a deterministic tree - the redundant
    leading bound plus the OR-expansion - which Django's same-connector
    squash splices into the root AND as TWO children (one child for a
    single-column cursor, where the "expansion" is a bare comparison).
    This verifies that exact shape against the spec's columns, directions,
    and decoded values, so the lateral SQL never silently drops a filter
    that is NOT the seek (which would return wrong rows) and never
    double-applies one that is.
    """
    seek = spec.keyset_seek
    columns = spec.order_columns
    values = list(seek.cursor.values)
    if len(nodes) != 2 or len(columns) != len(values):
        return False
    greater = [keyset_seek_greater(descending, flip=seek.flip) for _, descending in columns]

    def is_lookup(node: Any, lookup_name: str, index: int) -> bool:
        if getattr(node, "lookup_name", None) != lookup_name:
            return False
        target = getattr(getattr(node, "lhs", None), "target", None)
        if target is None or getattr(target, "column", None) != columns[index][0]:
            return False
        if target.model._meta.db_table != spec.db_table:
            return False
        rhs = node.rhs
        return not hasattr(rhs, "resolve_expression") and rhs == values[index]

    def is_cmp(node: Any, index: int) -> bool:
        return is_lookup(node, "gt" if greater[index] else "lt", index)

    lead, expansion = nodes
    if not is_lookup(lead, "gte" if greater[0] else "lte", 0):
        return False
    if len(columns) == 1:
        return is_cmp(expansion, 0)
    arms = getattr(expansion, "children", None)
    if (
        arms is None
        or expansion.negated
        or expansion.connector != "OR"
        or len(arms) != len(columns)
    ):
        return False
    for index, arm in enumerate(arms):
        if index == 0:
            if not is_cmp(arm, 0):
                return False
            continue
        arm_children = getattr(arm, "children", None)
        if (
            arm_children is None
            or arm.negated
            or arm.connector != "AND"
            or len(arm_children) != index + 1
        ):
            return False
        if not all(is_lookup(arm_children[j], "exact", j) for j in range(index)):
            return False
        if not is_cmp(arm_children[index], index):
            return False
    return True


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
      ``__`` traversals, or multi-table parent columns);
    - a ``defer()``-shaped projection (the ``.only()`` walker contract is
      the supported shape), selected multi-table parent columns, or a
      composite/columnless primary key.
    """
    if request.keyset_seek is not None and request.with_total_count:
        # Counted keyset seek: the ORM's qualify-wrapped filtered-count window
        # (``plans.py::_apply_keyset_counted_window``) is already the
        # whole-partition scan the pre-seek count forces - a raw-SQL dialect
        # of the same scan buys nothing, so downgrade to windowed rather than
        # grow a second marker/count arithmetic.
        return None
    child_queryset = request.child_queryset
    query = child_queryset.query
    if (
        query.where.children
        or query.select_related
        or query.annotations
        or query.extra
        or query.extra_tables
        or query.group_by is not None
    ):
        return None
    child_meta = child_queryset.model._meta
    child_pk_column = getattr(child_meta.pk, "column", None)
    if child_pk_column is None:
        return None  # composite primary key - no single default child join column.
    if type(child_queryset) is not QuerySet:
        return None  # custom subclass - the lateral class rebind would erase it.
    order_columns = _order_columns(request.order_by, child_meta)
    if order_columns is None:
        return None
    if request.keyset_seek is not None:
        seek_signature = tuple(
            (column.field.column, column.descending) for column in request.keyset_seek.columns
        )
        if seek_signature != order_columns or len(order_columns) != len(
            request.keyset_seek.cursor.values,
        ):
            # The seek rides the order columns index-for-index (the cursor_field
            # IS the window order); an arity/order mismatch means the deterministic
            # order drifted from the cursor columns - downgrade rather than
            # misalign values against raw SQL columns.
            return None
    select_columns = _select_columns(child_queryset, child_meta)
    if select_columns is None:
        return None
    fields_by_attname = {field.attname: field for field in child_meta.concrete_fields}
    select_fields = tuple(fields_by_attname[attname] for attname, _column in select_columns)
    # Only the five link-shaped fields differ between the two join shapes;
    # the resolved link FIELD OBJECTS come from the request's join descriptor
    # (``join_taxonomy.classify_relation_join`` owns everything join-shaped a
    # relation field implies - this function only READS it).
    join = request.join
    parent_link_field = join.parent_link_field
    if parent_link_field is None:
        return None
    child_join_column = child_pk_column
    if join.lateral_shape is LateralJoinShape.THROUGH_TABLE:
        through_child_field = join.through_child_field
        if through_child_field is None:
            return None
        child_target_field = through_child_field.target_field
        if child_target_field.model._meta.db_table != child_meta.db_table:
            return None
        child_join_column = child_target_field.column
        through_table = parent_link_field.model._meta.db_table
        parent_link_table = through_table
        through_child_column = through_child_field.column
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
        select_fields=select_fields,
        order_columns=order_columns,
        query_order_by=tuple(request.order_by),
        parent_link_field=parent_link_field,
        parent_link_table=parent_link_table,
        parent_link_column=parent_link_field.column,
        through_table=through_table,
        through_child_column=through_child_column,
        child_join_column=child_join_column,
        prefetch_value_aliases=prefetch_value_aliases,
        offset=request.offset,
        limit=request.limit,
        reverse=request.reverse,
        with_total_count=request.with_total_count,
        next_page_probe=request.next_page_probe,
        keyset_seek=request.keyset_seek,
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
        if field is None or field.model._meta.db_table != child_meta.db_table:
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
    ``plans.py::deferred_loading_of``; unreadable shapes downgrade to the
    windowed strategy instead of escaping a private-contract error.
    """
    loading = deferred_loading_of(queryset)
    if loading is None:
        return None
    names, defer = loading
    if defer:
        if names:
            return None
        fields = tuple(child_meta.concrete_fields)
    else:
        fields = tuple(
            field
            for field in child_meta.concrete_fields
            if field.primary_key or field.name in names or field.attname in names
        )
    if any(field.model._meta.db_table != child_meta.db_table for field in fields):
        return None
    return tuple((field.attname, field.column) for field in fields)
