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
machinery adds (``_filter_prefetch_queryset``: ``Q(<field>__in=parents)``
with the rhs already normalized to pk values) + (for a visibility spec) the
planned single-table scope, proven byte-equal to what we compiled". Anything
unrecognized - a
Django-internals drift, a consumer mutation, a non-Postgres ``.using()``
route - falls through to the superclass ``_fetch_all``, which executes the
windowed body: a performance downgrade, never a correctness cliff.

Plan-time shapes the lateral SQL cannot express (``select_related``, child
annotations, expression ordering, a composite primary key, or selected/ordered
columns from a multi-table inheritance parent) downgrade INSIDE the strategy to
the windowed plan - the selection is still planned, so Decision-6 strictness
visibility is unaffected. A child ``get_queryset`` visibility scope is the one
filter it CAN express when it is a single-table plain-column WHERE on the
DIRECT_FK non-keyset shape: that WHERE rides the spec, is compiled at fetch
time against the real child table, and is spliced into the lateral branch (the
common anonymous-traffic case, which otherwise silently rode the windowed
body). A multi-table / ``Exists`` / ``Subquery`` / expression qual, an
``is_empty()`` (``qs.none()``) hook, an M2M through filter, or a keyset shape's
filter still downgrades.
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

from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db import connections
from django.db.models import QuerySet
from django.db.models.expressions import Col, Window
from django.db.models.query import ModelIterable
from django.db.models.sql.where import AND, WhereNode

from ..keyset import keyset_seek_sql
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
    # A single-table plain-column visibility WHERE (a target type's
    # ``get_queryset`` scope), cloned off the child query at plan time, or
    # ``None``. Only the DIRECT_FK non-keyset shape carries it (see
    # ``_build_lateral_spec``); at fetch time it is compiled through the child
    # query's own compiler against the real (unaliased) child table and
    # spliced into the lateral branch next to the parent-link predicate, and
    # the fetch-time WHERE residue is proven byte-equal to it before the raw
    # SQL is trusted (``_visibility_quals_match``). Per-user filter values
    # never enter the plan cache: a custom ``get_queryset`` marks the plan
    # non-cacheable (``nested_planner.py``).
    visibility_where: Any | None = None

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
    visibility_where_sql: tuple[str, list] | None = None,
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

    ``visibility_where_sql`` is the ``(sql, params)`` a DIRECT_FK spec's
    ``visibility_where`` compiled to (through the child query's own compiler,
    against the real child table name - which is why DIRECT_FK drops the child
    alias below); it is spliced ``AND (<sql>)`` into the lateral branch next to
    the keyset seek. ``None`` (every non-visibility shape) leaves the branch
    unfiltered beyond the parent-link predicate.

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
    # DIRECT_FK drops the child alias: the child is the only table in the
    # branch, so referring to every child column by the real table name lets a
    # spliced visibility WHERE - which Django compiles against the real table
    # name, not the alias - agree with the select/order/parent-link/seek refs
    # for free. THROUGH_TABLE keeps its alias (it needs disambiguation from the
    # through table, and v1 visibility WHERE is DIRECT_FK-only).
    child = child_table if spec.through_table is None else qn(LATERAL_CHILD_ALIAS)
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
        # DIRECT_FK: the child table drives the branch unaliased (``child`` is
        # already the real quoted table name), so the compiled visibility WHERE
        # spliced below references the same name.
        from_sql = child_table
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
        # native Python adaptation); nothing is interpolated. The SQL text
        # itself is ``keyset.keyset_seek_sql`` - the raw-SQL twin of
        # ``keyset_seek_q`` - so the dialects cannot drift.
        seek_sql, seek_params = _keyset_seek_sql(
            spec,
            qn,
            child,
            prepare_value=prepare_value,
        )
        lateral_sql += f" AND ({seek_sql})"
        params.extend(seek_params)
    if visibility_where_sql is not None:
        # The spec-carried visibility scope, compiled against the real child
        # table by the caller (``_fetch_lateral_rows``): spliced into the
        # branch exactly once. The fetch-time recognizer proves this predicate
        # IS the planned WHERE before the raw SQL is trusted, so it is never
        # double-applied against the windowed body's own copy.
        where_text, where_params = visibility_where_sql
        lateral_sql += f" AND ({where_text})"
        params.extend(where_params)
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
        if range_plan.fetch_upper_bound is not None:
            # Bind the FETCH ceiling (page bound plus the probe sentinel) so the
            # composed offset page fetches the ``rn == upper_bound + 1`` sentinel
            # the resolver reads ``hasNextPage`` from; equals ``upper_bound`` when
            # the probe is off (reverse pages never probe), so every non-probe
            # shape is unchanged. Matches the ORM renderer's ``fetch_upper_bound``
            # bind - the two dialects must not diverge (a raw ``upper_bound`` here
            # would leave ``hasNextPage`` constantly False on PG only).
            bound_column = (
                f"{window}.{qn(WINDOW_ROW_NUMBER_REVERSED)}" if range_plan.reverse else rn
            )
            range_parts.append(f"{bound_column} <= %s")
            params.append(range_plan.fetch_upper_bound)
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
    """Bind ``spec``'s keyset seek into quoted child-column refs for ``keyset_seek_sql``.

    Lateral-specific adapter only: prepares values through each cursor
    column's Django field, quotes the child-table column refs, and hands
    the shared ``KeysetSeekPlan`` to ``keyset.keyset_seek_sql``. The seek
    columns ARE ``spec.order_columns`` (the ``cursor_field`` is the window
    order), aligned index-for-index with the decoded cursor values -
    ``_build_lateral_spec`` guarantees the arity.
    """
    seek = spec.keyset_seek
    values = [
        prepare_value(column.field, value) if prepare_value is not None else value
        for column, value in zip(seek.columns, seek.cursor.values, strict=True)
    ]
    plan = seek.plan(values)
    refs = [f"{child}.{qn(column.field.column)}" for column in seek.columns]
    return keyset_seek_sql(refs, plan)


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
    # The signature of the window-range quals the PLANNED windowed body carried
    # when it was wrapped (``window_predicate_signature``), captured once so the
    # fetch-time recognizer can prove the row-number range was not mutated before
    # trusting the raw SQL. ``None`` means the planned window could not be
    # normalized, so the fast path never engages (fail closed).
    _dst_window_signature: tuple | None = None

    def _clone(self) -> LateralQuerySet:
        clone = super()._clone()
        clone._dst_lateral_spec = self._dst_lateral_spec
        clone._dst_window_signature = self._dst_window_signature
        return clone

    def _fetch_all(self) -> None:
        if self._result_cache is None:
            rows = _fetch_lateral_rows(self)
            if rows is not None:
                self._result_cache = rows
        # The superclass call is a no-op on a populated cache except for the
        # nested ``prefetch_related`` pass - which the lateral rows need too.
        super()._fetch_all()


@dataclass(frozen=True)
class _RecognizedLateralFetch:
    """The proven fetch-time inputs a recognized lateral query yields.

    Carries the parent-id list ``_recognize_lateral_fetch`` pulled from the
    prefetch ``__in`` filter and, for a DIRECT_FK visibility spec, the EXACT
    ``(sql, params)`` its ``visibility_where`` compiled to during the byte-equal
    recognizer check. Handing that approved pair straight to ``build_lateral_sql``
    (instead of recompiling ``spec.visibility_where`` a second time at execution)
    keeps the fail-closed proof honest: the bytes spliced into the lateral branch
    ARE the bytes the recognizer proved byte-equal to the fetch-time residue, so
    a stateful or consumption-based custom lookup compiler cannot make the
    executed predicate diverge from the approved one. ``visibility_where_sql`` is
    ``None`` for every non-visibility shape (plain windows and keyset seeks).
    """

    parent_ids: list
    visibility_where_sql: tuple[str, list] | None = None


def _fetch_lateral_rows(queryset: LateralQuerySet) -> list | None:
    """Execute the lateral SQL for ``queryset`` if its state is recognized.

    Returns ``None`` for every unrecognized shape (the superclass then runs
    the windowed body): missing spec (a queryset constructed outside the
    strategy), a non-Postgres connection (``.using()`` re-routing), a
    ``values()``-style iterable, or a query whose WHERE tree
    ``_recognize_lateral_fetch`` cannot prove is "window range + parent IN".
    """
    spec = queryset._dst_lateral_spec
    if spec is None:
        return None
    connection = connections[queryset.db]
    if connection.vendor != "postgresql":
        return None
    if queryset._iterable_class is not ModelIterable:
        return None
    recognized = _recognize_lateral_fetch(queryset, spec)
    if recognized is None:
        return None
    # Repeated parent rows would execute duplicate lateral branches and inflate
    # every attached child page, so de-duplicate them before binding.
    parent_ids = _deduplicate_parent_ids(recognized.parent_ids)
    if not parent_ids:
        return []
    # The visibility scope was already compiled ONCE by the recognizer's
    # byte-equal check (``_visibility_quals_match``); reuse that exact approved
    # ``(sql, params)`` rather than recompiling ``spec.visibility_where`` a third
    # time - the recognizer only returns a non-``None`` predicate here, so the
    # bytes spliced below are precisely the ones it proved.
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
        visibility_where_sql=recognized.visibility_where_sql,
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


def _recognize_lateral_fetch(
    queryset: LateralQuerySet,
    spec: LateralWindowSpec,
) -> _RecognizedLateralFetch | None:
    """Prove the fetch-time query IS the planned window and return its inputs, or ``None``.

    The fetch-time query must be EXACTLY the planned windowed body plus
    ``_filter_prefetch_queryset``'s additions: annotations limited to the
    window names, ``extra(select=...)`` limited to the M2M
    ``_prefetch_related_val_*`` aliases the spec predicted, and a WHERE tree
    whose children are window-range quals (their ``lhs`` is the cloned
    ``Window`` expression - including workstream C's nested marker OR node)
    plus ONE ``__in`` lookup on the spec's parent link column with an
    already-normalized value list (``RelatedIn`` resolves model instances to
    pk values at construction). The window quals are proven to be EXACTLY the
    planned range - not merely "some ``Window`` lookup" - by matching their
    normalized ``window_predicate_signature`` against the signature captured when
    the queryset was wrapped, so a mutated / added / dropped row-number bound
    downgrades to the windowed body. A DIRECT_FK spec may also carry a single-table
    visibility WHERE; its quals ride the same base tree and are proven
    byte-equal to the plan (``_visibility_quals_match``) before the raw SQL is
    trusted - the APPROVED compiled ``(sql, params)`` rides back on the returned
    ``_RecognizedLateralFetch`` so the executor splices the exact bytes proven
    here, never a fresh compile. Anything else - an unexpected filter, a second
    IN, an expression rhs, a slice - returns ``None`` (the windowed body runs).
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
    # The window quals must be EXACTLY the planned range. The captured signature
    # is ``None`` only if the planned window could not be normalized at wrap time;
    # a fetch-time ``None`` (an unreadable qual) or any structural divergence
    # (changed / added / dropped / duplicated bound, wrong ``_dst_*`` annotation)
    # fails the equality and downgrades to the windowed body.
    planned_signature = queryset._dst_window_signature
    if planned_signature is None or window_predicate_signature(query) != planned_signature:
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
            maybe_ids = _parent_in_values(
                child,
                column=spec.parent_link_column,
                table=spec.parent_link_table,
            )
            if maybe_ids is not None:
                parent_ids = maybe_ids
                continue
        unrecognized.append(child)
    if parent_ids is None:
        return None
    visibility_where_sql: tuple[str, list] | None = None
    if spec.keyset_seek is not None:
        # The planned count-free keyset body carries the seek in its base
        # WHERE (the windowed-fallback correctness floor); the fetch-time
        # tree must contain EXACTLY that seek - structurally verified
        # against the spec - and nothing else. Any other residue means a
        # consumer/Django mutation: fall back to the windowed body.
        if not _keyset_seek_quals_match(unrecognized, spec):
            return None
    elif spec.visibility_where is not None:
        # The planned windowed body carries the same single-table scope in its
        # base WHERE; the fetch-time residue must be EXACTLY that scope - proven
        # by a byte-equal compile - and nothing else. Any divergence falls back
        # to the windowed body. The recognizer returns the APPROVED compiled
        # predicate (not just a boolean) so the executor reuses those exact
        # bytes.
        visibility_where_sql = _visibility_quals_match(queryset, unrecognized, spec)
        if visibility_where_sql is None:
            return None
    elif unrecognized:
        return None
    return _RecognizedLateralFetch(
        parent_ids=parent_ids,
        visibility_where_sql=visibility_where_sql,
    )


def _is_window_qual(node: Any) -> bool:
    """True if ``node`` constrains ONLY the planned ``_dst_*`` window annotations.

    A window-range lookup carries the cloned ``Window`` expression as its
    ``lhs``; the ambiguous-shape marker filter arrives as a nested ``WhereNode``
    (``(range) OR rn = 1``) whose leaves all do. This is a STRUCTURAL classifier
    only - it says a node lives entirely in window-annotation space, NOT that it
    is the specific range the plan intended (that is
    ``window_predicate_signature``'s job). Both nested-connection fetch
    recognizers use it to separate the window quals from the prefetch ``__in`` /
    visibility / keyset residue while scanning the fetch-time WHERE tree.
    """
    children = getattr(node, "children", None)
    if children is not None:
        return not node.negated and all(_is_window_qual(sub) for sub in children)
    return isinstance(getattr(node, "lhs", None), Window)


def _normalize_window_node(node: Any, names_by_id: dict[int, str]) -> tuple | None:
    """Normalize one window-qual node to a canonical comparable signature, or ``None``.

    A leaf becomes ``("leaf", annotation-name, lookup, rhs)`` - the annotation
    resolved by IDENTITY against the query's ``Window`` annotations (a filter on
    an annotation carries the annotation object itself as the lookup ``lhs``), the
    lookup operator, and the plain bound value. A nested ``WhereNode`` becomes
    ``("node", connector, negated, sorted child signatures)`` - order-independent
    but MULTIPLICITY-preserving (a duplicated bound is not silently collapsed).
    Returns ``None`` when a leaf's ``lhs`` is not a mapped window annotation or
    its ``rhs`` is an expression rather than a plain value, so an unreadable
    window qual fails closed. A leaf's ``lookup_name`` (always present on a
    Django lookup) rides the signature verbatim, so a ``gt`` bound never compares
    equal to an ``lte`` one.
    """
    children = getattr(node, "children", None)
    if children is not None:
        subs: list = []
        for child in children:
            normalized = _normalize_window_node(child, names_by_id)
            if normalized is None:
                return None
            subs.append(normalized)
        return (
            "node",
            node.connector,
            bool(node.negated),
            tuple(sorted(subs, key=repr)),
        )
    name = names_by_id.get(id(getattr(node, "lhs", None)))
    if name is None:
        return None
    rhs = getattr(node, "rhs", None)
    if hasattr(rhs, "resolve_expression"):
        return None
    return (
        "leaf",
        name,
        getattr(node, "lookup_name", None),
        rhs,
    )


def window_predicate_signature(query: Any) -> tuple | None:
    """Return a canonical signature of the window-range quals in ``query.where``.

    The safety boundary SHARED by both nested-connection fetch recognizers
    (``_recognize_lateral_fetch`` and
    ``single_parent_fetch.py::_fetch_single_parent_rows``): each captures this
    signature from the PLANNED windowed queryset when the queryset is wrapped, and
    re-derives it from the FETCH-time query, running its optimized path only on an
    exact match. Because a strategy discards the ORM query and executes from its
    stored plan, an altered row-number bound (a changed, removed, added, or
    duplicated window lookup, or the wrong ``_dst_*`` annotation) must be caught
    HERE or it would be silently ignored - a structural "some ``Window`` lookup"
    test (``_is_window_qual``) is necessary but not sufficient.

    Every window qual (a leaf whose ``lhs`` is a ``Window`` annotation, plus the
    nested marker ``OR`` node) is normalized and gathered into an
    order-independent, multiplicity-preserving tuple; NON-window children (the
    prefetch ``__in``, a visibility scope, a keyset seek) are ignored here - the
    recognizers prove those separately. An EMPTY tuple is the valid signature of
    an unbounded window that plans no row-number filter, and is deliberately
    distinct from ``None``, which means a window qual could not be normalized and
    the shape must fail closed at the comparison.
    """
    names_by_id = {
        id(expression): name
        for name, expression in query.annotations.items()
        if isinstance(expression, Window)
    }
    signatures: list = []
    for child in query.where.children:
        if not _is_window_qual(child):
            continue
        normalized = _normalize_window_node(child, names_by_id)
        if normalized is None:
            return None
        signatures.append(normalized)
    return tuple(sorted(signatures, key=repr))


def _keyset_seek_quals_match(nodes: list[Any], spec: LateralWindowSpec) -> bool:
    """Whether ``nodes`` are exactly the planned keyset seek's WHERE residue.

    ``keyset.keyset_seek_q`` builds a deterministic tree - the redundant
    leading bound plus the OR-expansion - which Django's same-connector
    squash splices into the root AND as TWO children (one child for a
    single-column cursor, where the "expansion" is a bare comparison).
    This verifies that exact shape against the shared ``KeysetSeekPlan``
    (columns, directions, decoded values), so the lateral SQL never
    silently drops a filter that is NOT the seek (which would return wrong
    rows) and never double-applies one that is.
    """
    seek = spec.keyset_seek
    plan = seek.plan()
    column_names = [column.field.column for column in seek.columns]
    if len(nodes) != 2 or len(column_names) != len(plan.values):
        return False

    def is_lookup(node: Any, lookup_name: str, index: int) -> bool:
        if getattr(node, "lookup_name", None) != lookup_name:
            return False
        target = getattr(getattr(node, "lhs", None), "target", None)
        if target is None or getattr(target, "column", None) != column_names[index]:
            return False
        if target.model._meta.db_table != spec.db_table:
            return False
        rhs = node.rhs
        return not hasattr(rhs, "resolve_expression") and rhs == plan.values[index]

    def is_cmp(node: Any, index: int) -> bool:
        return is_lookup(node, "gt" if plan.greater[index] else "lt", index)

    lead, expansion = nodes
    if not is_lookup(lead, "gte" if plan.lead_greater else "lte", 0):
        return False
    if len(column_names) == 1:
        return is_cmp(expansion, 0)
    arms = getattr(expansion, "children", None)
    if (
        arms is None
        or expansion.negated
        or expansion.connector != "OR"
        or len(arms) != len(column_names)
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


def _visibility_quals_match(
    queryset: LateralQuerySet,
    nodes: list[Any],
    spec: LateralWindowSpec,
) -> tuple[str, list] | None:
    """Return the APPROVED compiled visibility predicate, or ``None`` on mismatch.

    The fail-closed recognizer for a DIRECT_FK spec's single-table
    ``visibility_where``: the planned windowed body carries the SAME quals in
    its base WHERE, so the fetch-time residue must compile - through the
    fetch-time query's own compiler, against the real (unaliased) child table -
    to the byte-identical ``(sql, params)`` as ``spec.visibility_where``. On a
    match it RETURNS that approved ``(sql, params)`` pair (the residue's own
    compilation, which by the equality check IS the stored scope's), so
    ``_fetch_lateral_rows`` splices exactly the bytes proven here rather than
    recompiling ``spec.visibility_where`` a third time - closing the seam a
    stateful or consumption-based custom lookup compiler could open by returning
    different bytes on the executor's compile. Consuming the residue here exactly
    once is also what keeps the predicate from being double-applied; ANY
    divergence (an extra consumer filter, a dropped qual, a reordered tree, or a
    second compile that differs from the first) returns ``None`` and the windowed
    body runs. ``keyset_seek`` and ``visibility_where`` never coexist on a spec
    (the plan gate refuses the combination), so this and
    ``_keyset_seek_quals_match`` are mutually exclusive.
    """
    if not nodes:
        return None
    compiler = queryset.query.get_compiler(using=queryset.db)
    residual = WhereNode(nodes, AND)
    try:
        residual_compiled = compiler.compile(residual)
        stored_compiled = compiler.compile(spec.visibility_where)
    except (EmptyResultSet, FullResultSet):
        return None
    if residual_compiled != stored_compiled:
        return None
    return residual_compiled


def _parent_in_values(node: Any, *, column: str, table: str) -> list | None:
    """The parent-id list if ``node`` is the prefetch ``__in`` filter, else ``None``.

    Matches by the lookup's target ``column`` AND ``table`` (the child table for
    ``DIRECT_FK``, the through table for ``THROUGH_TABLE`` - Django's
    ``reuse_all=True`` join reuse resolves the M2M path to the through FK
    column directly) and requires a plain expression-free value list.
    """
    if getattr(node, "lookup_name", None) != "in":
        return None
    target = getattr(getattr(node, "lhs", None), "target", None)
    if target is None or getattr(target, "column", None) != column:
        return None
    if target.model._meta.db_table != table:
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
    keeps the windowed body verbatim. The planned window-range signature is
    captured here (from the windowed body BEFORE Django's prefetch machinery
    appends the parent ``__in``) so ``_recognize_lateral_fetch`` can later prove
    the fetch-time range is byte-for-byte the one planned.
    """
    clone = queryset._chain()
    clone.__class__ = LateralQuerySet
    clone._dst_lateral_spec = spec
    clone._dst_window_signature = window_predicate_signature(queryset.query)
    return clone


def _plain_single_table_where(node: Any, base_table: str) -> bool:
    """True iff every leaf qual under ``node`` is a plain ``base_table`` column qual.

    The v1 visibility-WHERE admission test: each leaf lookup's ``lhs`` must be a
    bare ``Col`` on the base child table (``base_table`` is the ``Col.alias``
    Django assigns the base relation) and its ``rhs`` must be a plain value, not
    an expression. Nested ``WhereNode`` subtrees - including the negated node
    Django wraps an ``exclude()`` in - recurse. A relation-traversal Col (whose
    alias is a joined table), a transform ``lhs``, or an ``Exists``/``Subquery``/
    expression ``rhs`` all fail closed, so the combined gate keeps refusing the
    shapes the lateral SQL cannot splice against the real, unaliased table.
    """
    for child in node.children:
        grandchildren = getattr(child, "children", None)
        if grandchildren is not None:
            if not _plain_single_table_where(child, base_table):
                return False
            continue
        lhs = getattr(child, "lhs", None)
        if not isinstance(lhs, Col) or lhs.alias != base_table:
            return False
        if hasattr(getattr(child, "rhs", None), "resolve_expression"):
            return False
    return True


def _build_lateral_spec(request: NestedConnectionRequest) -> LateralWindowSpec | None:
    """Resolve the request into a lateral spec, or ``None`` to downgrade.

    ``None`` for every plan-time shape the lateral SQL cannot express:

    - a custom ``QuerySet`` subclass (a manager or visibility hook's own
      class) - ``_as_lateral_queryset``'s class rebind would erase subclass
      ``_clone`` state and iterator behavior, so anything but a plain
      ``QuerySet`` keeps the windowed strategy, which preserves the class;
    - a child queryset carrying ``select_related``, annotations, or ``extra``
      - the lateral subquery reproduces none of those. A single-table
      plain-column visibility WHERE (a DIRECT_FK non-keyset ``get_queryset``
      scope) is the ONE filter it CAN reproduce: it is carried on the spec and
      spliced at fetch time. A multi-table / ``Exists`` / ``Subquery`` /
      expression qual, an ``is_empty()`` hook, an M2M through filter, or a
      keyset shape's filter still downgrades;
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
        query.select_related
        or query.annotations
        or query.extra
        or query.extra_tables
        or query.group_by is not None
    ):
        return None
    visibility_where = None
    if query.where.children:
        # A single-table plain-column visibility WHERE (a target type's
        # ``get_queryset`` scope) is the one child filter the lateral SQL can
        # reproduce - carry it here, compile and splice it at fetch time. The
        # combined gate keeps refusing every shape the raw SQL cannot express:
        # a keyset seek (its base WHERE already carries the seek residue, and
        # combining the two matchers is out of v1 scope), a THROUGH_TABLE M2M
        # (v1 visibility WHERE is DIRECT_FK-only; the aliased child table would
        # not agree with Django's real-name compile), an ``is_empty()`` hook
        # (``qs.none()`` -> ``EmptyResultSet`` at compile), and any
        # multi-table / ``Exists`` / ``Subquery`` / expression qual.
        if (
            request.keyset_seek is not None
            or request.join.lateral_shape is not LateralJoinShape.DIRECT_FK
            or query.is_empty()
            or not _plain_single_table_where(
                query.where,
                child_queryset.model._meta.db_table,
            )
        ):
            return None
        visibility_where = query.where.clone()
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
        visibility_where=visibility_where,
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
