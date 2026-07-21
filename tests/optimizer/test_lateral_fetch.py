"""Tests for the Postgres lateral fetch strategy (``optimizer/lateral_fetch.py``).

Everything here runs on SQLite (the coverage tier): ``build_lateral_sql`` is
pure, plan-time spec building and downgrades never touch the DB, fetch-time
parent-id extraction runs against real querysets shaped by Django's own
``_filter_prefetch_queryset``, and the raw-SQL execution path runs through a
Postgres facade over the real connection with a scripted cursor. The
``@pytest.mark.pg`` live tier re-proves the same SQL against a real Postgres
server (``tests/test_lateral_pg_parity.py``).
"""

import dataclasses
from types import SimpleNamespace

import pytest
from apps.library.models import Book, Genre, Shelf
from django.db import connections, models
from django.db.models import F, Prefetch, Value
from django.db.models.fields.related_descriptors import _filter_prefetch_queryset

from django_strawberry_framework.exceptions import OptimizerError
from django_strawberry_framework.optimizer.lateral_fetch import (
    LateralPrefetchStrategy,
    LateralQuerySet,
    _build_lateral_spec,
    _fetch_lateral_rows,
    _is_window_qual,
    _normalize_window_node,
    _recognize_lateral_fetch,
    build_lateral_sql,
    window_predicate_signature,
)
from django_strawberry_framework.optimizer.nested_fetch import AUTO_STRATEGY
from django_strawberry_framework.optimizer.plans import (
    WINDOW_ROW_NUMBER,
    WINDOW_TOTAL_COUNT,
    OptimizationPlan,
)
from tests.optimizer._builders import nested_connection_request as _request


def _quote(name):
    """The identifier quoting the pure-builder tests pin against."""
    return f'"{name}"'


def _shelf_books_request(**overrides):
    """Reverse FK ``Shelf.books`` with the walker's ``.only()`` projection."""
    overrides.setdefault(
        "child_queryset",
        Book.objects.only("id", "title", "shelf_id"),
    )
    overrides.setdefault("order_by", ("title", "id"))
    return _request(Shelf, "books", **overrides)


def _planned_lateral_queryset(request):
    """Run the strategy and return the planned ``LateralQuerySet``."""
    plan = OptimizationPlan()
    assert LateralPrefetchStrategy().plan(request, plan) is True
    (entry,) = plan.prefetch_related
    assert isinstance(entry.queryset, LateralQuerySet)
    return entry.queryset


# ---------------------------------------------------------------------------
# Spec building (plan time)
# ---------------------------------------------------------------------------


def test_spec_direct_fk_reverse_foreign_key():
    """Reverse FK: the child table itself carries the parent-id column."""
    spec = _build_lateral_spec(_shelf_books_request())
    assert spec.model is Book
    assert spec.db_table == "library_book"
    assert spec.select_columns == (("id", "id"), ("title", "title"), ("shelf_id", "shelf_id"))
    assert spec.order_columns == (("title", False), ("id", False))
    assert spec.parent_link_table == "library_book"
    assert spec.parent_link_column == "shelf_id"
    assert spec.through_table is None
    assert spec.through_child_column is None
    assert spec.child_join_column == "id"
    assert spec.prefetch_value_aliases == ()
    assert (
        spec.offset,
        spec.limit,
        spec.reverse,
        spec.with_total_count,
    ) == (
        0,
        2,
        False,
        True,
    )


def test_lateral_spec_rejects_engaged_probe_with_count():
    """The lateral window spec enforces the same probe/count contract as the ORM.

    The lateral twin of the ``NestedConnectionRequest`` guard: constructing a
    ``LateralWindowSpec`` that engages the count-free probe while also annotating
    the count raises ``OptimizerError``, so the raw-SQL backend cannot develop a
    different fetch-mode contract. Built by flipping ``with_total_count`` on a
    real count-free probe spec (a bad request can no longer reach the spec - the
    request guards first).
    """
    probe_spec = _build_lateral_spec(
        _shelf_books_request(with_total_count=False, next_page_probe=True),
    )
    assert probe_spec.next_page_probe is True
    with pytest.raises(OptimizerError, match="mutually exclusive"):
        dataclasses.replace(probe_spec, with_total_count=True)


def test_spec_forward_m2m_through_table():
    """Forward M2M (``Book.genres``): the through table owns the parent link."""
    spec = _build_lateral_spec(_request(Book, "genres"))
    assert spec.model is Genre
    assert spec.db_table == "library_genre"
    # No ``.only()`` on the child -> the full concrete projection.
    assert spec.select_columns == tuple((f.attname, f.column) for f in Genre._meta.concrete_fields)
    assert spec.parent_link_table == "library_book_genres"
    assert spec.parent_link_column == "book_id"
    assert spec.through_table == "library_book_genres"
    assert spec.through_child_column == "genre_id"
    assert spec.child_join_column == "id"
    assert spec.prefetch_value_aliases == ("_prefetch_related_val_book_id",)


def test_spec_reverse_m2m_swaps_the_through_sides():
    """Reverse M2M (``Genre.books``): the same through table, sides swapped."""
    spec = _build_lateral_spec(_request(Genre, "books"))
    assert spec.model is Book
    assert spec.parent_link_table == "library_book_genres"
    assert spec.parent_link_column == "genre_id"
    assert spec.through_child_column == "book_id"
    assert spec.prefetch_value_aliases == ("_prefetch_related_val_genre_id",)


def test_spec_downgrades_for_unresolvable_through_link_fields():
    """Incomplete or cross-table through metadata cannot be rendered safely."""
    request = _request(Book, "genres")
    assert (
        _build_lateral_spec(
            dataclasses.replace(
                request,
                join=dataclasses.replace(request.join, parent_link_field=None),
            ),
        )
        is None
    )
    assert (
        _build_lateral_spec(
            dataclasses.replace(
                request,
                join=dataclasses.replace(request.join, through_child_field=None),
            ),
        )
        is None
    )
    cross_table_field = SimpleNamespace(
        target_field=SimpleNamespace(model=Shelf, column="id"),
    )
    assert (
        _build_lateral_spec(
            dataclasses.replace(
                request,
                join=dataclasses.replace(
                    request.join,
                    through_child_field=cross_table_field,
                ),
            ),
        )
        is None
    )


def test_spec_maps_pk_alias_and_descending_order():
    """``"pk"`` resolves to the pk column; a ``-`` prefix flips to DESC."""
    spec = _build_lateral_spec(_shelf_books_request(order_by=("-title", "pk")))
    assert spec.order_columns == (("title", True), ("id", False))


# ---------------------------------------------------------------------------
# Single-table visibility WHERE carried on the spec
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "child_queryset",
    [
        pytest.param(
            Book.objects.only("id", "title", "shelf_id").exclude(circulation_status="repair"),
            id="exclude",
        ),
        pytest.param(
            Book.objects.only("id", "title", "shelf_id").filter(title__startswith="A"),
            id="filter",
        ),
    ],
)
def test_spec_carries_single_table_visibility_where(child_queryset):
    """A DIRECT_FK single-table plain-column scope rides the spec.

    The common anonymous-traffic shape: a target-type ``get_queryset``
    ``exclude``/``filter`` on a base column no longer downgrades - it is cloned
    onto ``visibility_where`` for fetch-time compilation and splicing. The clone
    is independent of the request queryset (a later mutation cannot reach it).
    """
    request = _shelf_books_request(child_queryset=child_queryset)
    spec = _build_lateral_spec(request)
    assert spec is not None
    assert spec.visibility_where is not None
    assert spec.visibility_where is not child_queryset.query.where  # a clone.
    assert spec.visibility_where.children  # the qual survived the clone.


def test_spec_refuses_visibility_where_on_m2m_through():
    """v1 visibility WHERE is DIRECT_FK-only: an M2M through filter downgrades."""
    request = _request(Genre, "books", child_queryset=Book.objects.filter(title="x"))
    assert _build_lateral_spec(request) is None


def test_spec_refuses_visibility_where_with_a_keyset_seek():
    """A keyset shape carrying a filter downgrades (the matchers do not combine)."""
    from django_strawberry_framework.keyset import (
        KeysetCursor,
        KeysetSeek,
        cursor_columns_for,
    )

    seek = KeysetSeek(
        columns=cursor_columns_for(Book, ("title", "id")),
        cursor=KeysetCursor(values=("m", 1)),
    )
    request = _shelf_books_request(
        child_queryset=Book.objects.only("id", "title", "shelf_id").filter(title__startswith="A"),
        with_total_count=False,
        next_page_probe=True,
        keyset_seek=seek,
    )
    assert _build_lateral_spec(request) is None


def test_plain_single_table_where_rejects_relation_and_expression_quals():
    """The admission helper's defensive tail, pinned directly.

    A base-column ``exclude`` (nested negated node) is admitted; a
    relation-traversal Col (a joined alias, not the base table) and an
    expression right-hand side (a ``Subquery``/queryset rhs, single-alias but
    inexpressible against the unaliased branch) both fail closed.
    """
    from django_strawberry_framework.optimizer.lateral_fetch import _plain_single_table_where

    assert _plain_single_table_where(
        Book.objects.exclude(circulation_status="repair").query.where,
        "library_book",
    )
    assert not _plain_single_table_where(
        Book.objects.filter(shelf__code="A").query.where,
        "library_book",
    )
    assert not _plain_single_table_where(
        Book.objects.filter(shelf__in=Shelf.objects.all()).query.where,
        "library_book",
    )
    # A NESTED subtree (exclude wraps a negated WhereNode) whose leaf is a
    # relation-traversal Col: the recursion into the subtree fails closed.
    assert not _plain_single_table_where(
        Book.objects.exclude(shelf__code="A").query.where,
        "library_book",
    )


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        (
            {"child_queryset": Book.objects.filter(shelf__code="A")},
            "multi-table WHERE (join traversal reaches another alias)",
        ),
        (
            {"child_queryset": Book.objects.filter(shelf__in=Shelf.objects.all())},
            "a Subquery-rhs qual is refused even though it is single-alias",
        ),
        (
            {"child_queryset": Book.objects.none()},
            "an is_empty() (qs.none()) hook degrades rather than raising at compile",
        ),
        (
            {"child_queryset": Book.objects.select_related("shelf")},
            "select_related joins are not reproduced in the lateral subquery",
        ),
        (
            {"child_queryset": Book.objects.annotate(marker=Value(1))},
            "child annotations are not reproduced",
        ),
        (
            {"child_queryset": Book.objects.extra(select={"marker": "1"})},
            "extra(select=...) is not reproduced",
        ),
        (
            {"child_queryset": Book.objects.defer("subtitle")},
            "defer() projection shape (the walker only plans .only())",
        ),
        ({"order_by": (F("title").asc(), "id")}, "expression ordering"),
        ({"order_by": ("shelf__code", "id")}, "relation-traversal ordering"),
    ],
)
def test_spec_downgrades_to_windowed(overrides, reason):
    """Inexpressible shapes plan the plain windowed prefetch (still planned)."""
    plan = OptimizationPlan()
    assert LateralPrefetchStrategy().plan(_request(Shelf, "books", **overrides), plan) is True
    (entry,) = plan.prefetch_related
    assert isinstance(entry, Prefetch)
    assert not isinstance(entry.queryset, LateralQuerySet), reason
    assert WINDOW_ROW_NUMBER in entry.queryset.query.annotations


def test_order_columns_reject_unresolvable_names():
    """The order mapper's defensive tail, pinned directly.

    ``"?"``, empty entries, and names that resolve to nothing are not walker
    products (``deterministic_order`` starts from a validated queryset
    ordering), so they are pinned on the helper rather than through the
    strategy - the windowed fallback could not ``order_by`` them either.
    """
    from django_strawberry_framework.optimizer.lateral_fetch import _order_columns

    assert _order_columns(("no_such_field",), Book._meta) is None
    assert _order_columns(("?",), Book._meta) is None
    assert _order_columns(("",), Book._meta) is None


def test_spec_downgrades_on_columnless_primary_key():
    """A composite (columnless) child pk has no single default join column."""
    fake_queryset = SimpleNamespace(
        query=SimpleNamespace(
            where=SimpleNamespace(children=[]),
            select_related=False,
            annotations={},
            extra={},
            extra_tables=(),
            group_by=None,
        ),
        model=SimpleNamespace(_meta=SimpleNamespace(pk=SimpleNamespace(column=None))),
    )
    assert _build_lateral_spec(_request(Shelf, "books", child_queryset=fake_queryset)) is None


def test_spec_downgrades_for_multi_table_inherited_order_column():
    """Parent-table order columns cannot be rendered against the child table."""

    class ParentOrderRecord(models.Model):
        inherited_order = models.IntegerField()

        class Meta:
            app_label = "tests"
            managed = False

    class ChildOrderRecord(ParentOrderRecord):
        local_value = models.IntegerField()

        class Meta:
            app_label = "tests"
            managed = False

    request = _shelf_books_request(
        child_queryset=ChildOrderRecord.objects.all(),
        order_by=("inherited_order", "pk"),
    )
    assert _build_lateral_spec(request) is None


def test_spec_downgrades_for_selected_multi_table_parent_column():
    """A parent-table projection needs Django's join, so raw lateral SQL downgrades."""

    class ParentProjectionRecord(models.Model):
        inherited_value = models.IntegerField()

        class Meta:
            app_label = "tests"
            managed = False

    class ChildProjectionRecord(ParentProjectionRecord):
        local_order = models.IntegerField()

        class Meta:
            app_label = "tests"
            managed = False

    request = _shelf_books_request(
        child_queryset=ChildProjectionRecord.objects.all(),
        order_by=("local_order", "pk"),
    )
    assert _build_lateral_spec(request) is None


def test_spec_downgrades_on_unreadable_deferred_loading():
    """Unreadable projection state downgrades instead of raising in the lateral path."""
    queryset = Book.objects.all()
    queryset.query.deferred_loading = (None, False)
    assert _build_lateral_spec(_request(Shelf, "books", child_queryset=queryset)) is None


# ---------------------------------------------------------------------------
# build_lateral_sql (pure)
# ---------------------------------------------------------------------------


def test_sql_forward_page_shape():
    """``first: 2``: an in-branch ORDER BY + LIMIT page (the plannable shape).

    The unambiguous forward page paginates INSIDE the lateral branch - a
    ``LIMIT`` the Postgres planner can cost (it picks an order-satisfying
    index and stops each branch after the page, where an outer ``rn <= N``
    filter relies on the uncosted window run condition and degrades to a
    full per-partition sort).
    """
    spec = _build_lateral_spec(_shelf_books_request())
    sql, params = build_lateral_sql(spec, [1, 2, 3], quote_name=_quote, parent_cast="bigint")
    assert sql.startswith(
        'SELECT "__dst_parents"."__dst_parent_id", "__dst_window"."id",'
        ' "__dst_window"."title", "__dst_window"."shelf_id",'
        ' "__dst_window"."_dst_row_number", "__dst_window"."_dst_total_count"'
        " FROM unnest(%s::bigint[])"
        ' AS "__dst_parents"("__dst_parent_id")'
        " CROSS JOIN LATERAL (",
    )
    # DIRECT_FK drops the child alias: every child column ref is the real
    # ``library_book`` table name (so a spliced visibility WHERE, which Django
    # compiles against the real name, agrees for free).
    assert (
        'ROW_NUMBER() OVER (ORDER BY "library_book"."title" ASC, "library_book"."id" ASC)'
        ' AS "_dst_row_number"' in sql
    )
    assert 'COUNT(1) OVER () AS "_dst_total_count"' in sql
    assert 'FROM "library_book" WHERE' in sql  # unaliased child table.
    assert 'WHERE "library_book"."shelf_id" = "__dst_parents"."__dst_parent_id"' in sql
    assert sql.endswith(
        ' ORDER BY "library_book"."title" ASC, "library_book"."id" ASC LIMIT %s)'
        ' "__dst_window"'
        ' ORDER BY "__dst_parents"."__dst_parent_id", "__dst_window"."_dst_row_number"',
    )
    assert '"__dst_window" WHERE' not in sql  # the page is bounded in-branch.
    assert params == [[1, 2, 3], 2]


def test_sql_count_free_page_omits_the_count_window():
    """``with_total_count=False`` drops the count from both select lists."""
    spec = _build_lateral_spec(_shelf_books_request(with_total_count=False))
    sql, params = build_lateral_sql(spec, [1], quote_name=_quote)
    assert "_dst_total_count" not in sql
    assert "COUNT(1)" not in sql
    assert "FROM (VALUES (%s))" in sql  # no cast when the caller has none.
    assert params == [1, 2]


def test_sql_next_page_probe_overfetches_one_row_in_branch():
    """The count-free ``hasNextPage`` probe: in-branch ``LIMIT limit + 1``, no count.

    The lateral half of the win. ``fetch_limit`` (``2 + 1``) is a single-token
    change to the plain-first-page ``LIMIT`` and the count window is gone, so a
    ``first: 2`` page reads ~3 rows per partition instead of scanning it to
    ``COUNT``. The resolver drops the sentinel and derives ``hasNextPage`` from
    its presence.
    """
    spec = _build_lateral_spec(
        _shelf_books_request(with_total_count=False, next_page_probe=True),
    )
    sql, params = build_lateral_sql(spec, [7], quote_name=_quote)
    assert "_dst_total_count" not in sql
    assert "COUNT(1)" not in sql
    assert sql.endswith(
        ' ORDER BY "library_book"."title" ASC, "library_book"."id" ASC LIMIT %s)'
        ' "__dst_window"'
        ' ORDER BY "__dst_parents"."__dst_parent_id", "__dst_window"."_dst_row_number"',
    )
    assert '"__dst_window" WHERE' not in sql  # bounded in-branch, no outer filter.
    assert params == [7, 3]  # limit 2 + 1 sentinel row.


def test_sql_offset_shape_keeps_the_marker_row():
    """Overshot ``after:``: the ambiguous-shape ``OR rn = 1`` marker survives."""
    spec = _build_lateral_spec(_shelf_books_request(offset=3, limit=2))
    sql, params = build_lateral_sql(spec, [7], quote_name=_quote)
    assert (
        'WHERE ("__dst_window"."_dst_row_number" > %s'
        ' AND "__dst_window"."_dst_row_number" <= %s)'
        ' OR "__dst_window"."_dst_row_number" = 1' in sql
    )
    assert params == [7, 3, 5]


def test_sql_offset_probe_composes_marker_and_fetch_upper_bound():
    """The bounded offset page binds ``fetch_upper_bound`` and keeps the marker.

    The load-bearing lateral half of A1: the rn-filter upper bound is
    ``fetch_upper_bound`` (page bound ``offset + limit`` plus the probe sentinel),
    NOT the raw ``upper_bound`` - otherwise the lateral offset page would never
    fetch the sentinel and ``hasNextPage`` would read constantly False on PG only.
    ``after: 3``, ``first: 2`` with the probe: ``(rn > 3 AND rn <= 6) OR rn = 1``
    (6 == upper_bound 5 + 1), no count window, byte-parity with the ORM Q.
    """
    spec = _build_lateral_spec(
        _shelf_books_request(offset=3, limit=2, with_total_count=False, next_page_probe=True),
    )
    sql, params = build_lateral_sql(spec, [7], quote_name=_quote)
    assert "_dst_total_count" not in sql
    assert "COUNT(1)" not in sql
    assert (
        'WHERE ("__dst_window"."_dst_row_number" > %s'
        ' AND "__dst_window"."_dst_row_number" <= %s)'
        ' OR "__dst_window"."_dst_row_number" = 1' in sql
    )
    assert params == [7, 3, 6]  # lower 3, fetch ceiling 5 + 1 sentinel.


def test_sql_first_zero_shape_keeps_the_marker_row():
    """``first: 0``: upper bound zero plus the marker row."""
    spec = _build_lateral_spec(_shelf_books_request(offset=0, limit=0))
    sql, params = build_lateral_sql(spec, [7], quote_name=_quote)
    assert (
        'WHERE ("__dst_window"."_dst_row_number" <= %s)'
        ' OR "__dst_window"."_dst_row_number" = 1' in sql
    )
    assert params == [7, 0]


def test_sql_unbounded_shape_has_no_range_predicate():
    """``limit=None`` (or the relay maxsize sentinel): every row, no WHERE."""
    spec = _build_lateral_spec(_shelf_books_request(limit=None))
    sql, params = build_lateral_sql(spec, [7], quote_name=_quote)
    assert ') "__dst_window" ORDER BY' in sql
    assert params == [7]


def test_sql_reverse_shape_filters_the_reversed_row_number():
    """``last: 2``: a reversed row number bounds the page; forward rn returns."""
    spec = _build_lateral_spec(_shelf_books_request(reverse=True, limit=2))
    sql, params = build_lateral_sql(spec, [7], quote_name=_quote)
    assert (
        'ROW_NUMBER() OVER (ORDER BY "library_book"."title" DESC, "library_book"."id" DESC)'
        ' AS "_dst_row_number_reversed"' in sql
    )
    assert 'WHERE "__dst_window"."_dst_row_number_reversed" <= %s' in sql
    # The returned order stays FORWARD (cursor parity with the windowed body).
    assert sql.endswith(
        'ORDER BY "__dst_parents"."__dst_parent_id", "__dst_window"."_dst_row_number"',
    )
    assert params == [7, 2]


def test_sql_reverse_shape_applies_the_offset_filter_when_present():
    """The reverse branch mirrors ``apply_window_pagination``'s offset filter."""
    spec = _build_lateral_spec(_shelf_books_request(reverse=True, offset=1, limit=2))
    sql, params = build_lateral_sql(spec, [7], quote_name=_quote)
    assert (
        'WHERE "__dst_window"."_dst_row_number" > %s'
        ' AND "__dst_window"."_dst_row_number_reversed" <= %s' in sql
    )
    assert params == [7, 1, 2]


def test_sql_through_table_shape_joins_inside_the_lateral():
    """M2M: the through table drives the lateral branch and the parent match."""
    spec = _build_lateral_spec(_request(Genre, "books"))
    sql, params = build_lateral_sql(spec, [5, 6], quote_name=_quote, parent_cast="bigint")
    assert (
        'FROM "library_book_genres" AS "__dst_through"'
        ' INNER JOIN "library_book" AS "__dst_child"'
        ' ON "__dst_child"."id" = "__dst_through"."book_id"' in sql
    )
    assert 'WHERE "__dst_through"."genre_id" = "__dst_parents"."__dst_parent_id"' in sql
    assert params == [[5, 6], 2]


def test_sql_non_scalar_parent_keys_keep_typed_values_rows():
    """Structured parent keys avoid the value-changing array-of-values adapter."""
    spec = _build_lateral_spec(_shelf_books_request())
    spec = dataclasses.replace(
        spec,
        parent_link_field=SimpleNamespace(
            target_field=models.JSONField(),
        ),
    )
    sql, params = build_lateral_sql(
        spec,
        [{"tenant": 1}, {"tenant": 2}],
        quote_name=_quote,
        parent_cast="jsonb",
    )
    assert "FROM (VALUES (%s::jsonb), (%s::jsonb))" in sql
    assert params == [{"tenant": 1}, {"tenant": 2}, 2]


def test_sql_splices_the_compiled_visibility_where_into_the_branch():
    """The compiled scope is ``AND (...)``-spliced into the branch.

    The predicate lands next to the parent-link predicate (inside the lateral
    branch, before the in-branch ``LIMIT``) and its params come after the parent
    ids and before the ``LIMIT`` bind - the exact SQL/param order a real
    ``compile(where_node)`` feeds it. The child column ref is the real
    (unaliased) table name, so the compiled predicate agrees for free.
    """
    spec = _build_lateral_spec(_shelf_books_request(with_total_count=False))
    compiled = ('NOT ("library_book"."circulation_status" = %s)', ["repair"])
    sql, params = build_lateral_sql(
        spec,
        [1, 2],
        quote_name=_quote,
        parent_cast="bigint",
        visibility_where_sql=compiled,
    )
    assert (
        'WHERE "library_book"."shelf_id" = "__dst_parents"."__dst_parent_id"'
        ' AND (NOT ("library_book"."circulation_status" = %s))' in sql
    )
    # parent ids array, then the visibility bind, then the in-branch LIMIT.
    assert params == [[1, 2], "repair", 2]


# ---------------------------------------------------------------------------
# LateralQuerySet plumbing
# ---------------------------------------------------------------------------


def test_lateral_queryset_clones_carry_the_spec():
    """Every clone Django's prefetch machinery makes keeps the lateral spec."""
    queryset = _planned_lateral_queryset(_shelf_books_request())
    spec = queryset._dst_lateral_spec
    assert spec is not None
    filtered = queryset.using("default").filter(pk__gt=0)
    assert isinstance(filtered, LateralQuerySet)
    assert filtered._dst_lateral_spec is spec
    # The captured window-range signature rides every clone too.
    assert filtered._dst_window_signature == queryset._dst_window_signature
    assert queryset._dst_window_signature is not None
    # The windowed body rode along verbatim (the in-object fallback).
    assert WINDOW_ROW_NUMBER in queryset.query.annotations
    assert WINDOW_TOTAL_COUNT in queryset.query.annotations


def test_fetch_returns_none_without_a_spec():
    """A ``LateralQuerySet`` built outside the strategy falls straight back."""
    assert _fetch_lateral_rows(LateralQuerySet(model=Book)) is None


def test_fetch_returns_none_off_postgres(monkeypatch):
    """The vendor guard: a non-Postgres connection executes the windowed body.

    Scripted (rather than read off the real connection) so the pin holds on
    BOTH tiers - on the pg tier the real vendor IS postgresql.
    """
    from django_strawberry_framework.optimizer import lateral_fetch

    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [Shelf(pk=1)])
    facade = _PostgresFacade(rows=[])
    facade.vendor = "sqlite"
    monkeypatch.setattr(lateral_fetch, "connections", {"default": facade})
    assert _fetch_lateral_rows(queryset) is None
    assert facade.scripted_cursor.executed is None


# ---------------------------------------------------------------------------
# Fetch-time parent-id extraction
# ---------------------------------------------------------------------------


def _prefetch_filtered(request, field_name, parents):
    """The planned queryset exactly as Django's prefetch hands it to ``_fetch_all``."""
    queryset = _planned_lateral_queryset(request)
    return _filter_prefetch_queryset(queryset, field_name, parents)


def test_extract_reverse_fk_parent_ids():
    """The happy path: window quals plus the prefetch ``__in`` on the FK column."""
    queryset = _prefetch_filtered(
        _shelf_books_request(),
        "shelf",
        [Shelf(pk=1), Shelf(pk=2), Shelf(pk=3)],
    )
    assert _recognize_lateral_fetch(queryset, queryset._dst_lateral_spec).parent_ids == [1, 2, 3]


def test_extract_recognizes_the_marker_or_node():
    """The ambiguous-shape marker filter arrives as a nested OR of window quals."""
    queryset = _prefetch_filtered(
        _shelf_books_request(offset=3, limit=2),
        "shelf",
        [Shelf(pk=4)],
    )
    assert _recognize_lateral_fetch(queryset, queryset._dst_lateral_spec).parent_ids == [4]


def test_extract_recognizes_the_reversed_window_qual():
    """``last``-only windows filter on the reversed row number - still a window qual."""
    queryset = _prefetch_filtered(
        _shelf_books_request(reverse=True, limit=2),
        "shelf",
        [Shelf(pk=4)],
    )
    assert _recognize_lateral_fetch(queryset, queryset._dst_lateral_spec).parent_ids == [4]


def _shelf_books_visibility_request(**overrides):
    """A ``Shelf.books`` request whose child carries a single-table scope."""
    overrides.setdefault(
        "child_queryset",
        Book.objects.only("id", "title", "shelf_id").exclude(circulation_status="repair"),
    )
    return _shelf_books_request(**overrides)


def test_extract_recognizes_the_planned_visibility_scope():
    """The planned single-table scope in the fetch-time residue is
    proven byte-equal to the spec and consumed, leaving the parent ids AND the
    APPROVED compiled predicate the executor reuses (P3-1: no third compile)."""
    queryset = _prefetch_filtered(
        _shelf_books_visibility_request(),
        "shelf",
        [Shelf(pk=1), Shelf(pk=2)],
    )
    spec = queryset._dst_lateral_spec
    assert spec.visibility_where is not None
    recognized = _recognize_lateral_fetch(queryset, spec)
    assert recognized.parent_ids == [1, 2]
    # The recognizer carries the exact byte-equal ``(sql, params)`` it proved, so
    # ``_fetch_lateral_rows`` splices those bytes rather than recompiling.
    compiled_sql, compiled_params = recognized.visibility_where_sql
    assert "circulation_status" in compiled_sql
    assert compiled_params == ["repair"]


def test_extract_returns_none_for_an_unmatched_visibility_residue():
    """An extra consumer filter beyond the planned scope fails the byte-equal
    match - the recognizer degrades to the windowed body (never double-applies)."""
    queryset = _prefetch_filtered(_shelf_books_visibility_request(), "shelf", [Shelf(pk=1)])
    spec = queryset._dst_lateral_spec
    mutated = queryset.filter(title="x")  # a qual the plan never carried.
    assert _recognize_lateral_fetch(mutated, spec) is None


def test_extract_returns_none_when_the_planned_visibility_scope_is_missing():
    """A visibility spec whose fetch-time tree lost the scope (only the parent
    filter remains) is not the planned shape - fall back."""
    plain = _prefetch_filtered(_shelf_books_request(), "shelf", [Shelf(pk=1)])
    visibility_spec = _build_lateral_spec(_shelf_books_visibility_request())
    assert visibility_spec.visibility_where is not None
    # The plain queryset's residue is empty; the spec expects the scope.
    assert _recognize_lateral_fetch(plain, visibility_spec) is None


def test_extract_returns_none_when_the_scope_compiles_to_an_empty_result_set():
    """A single-table scope that compiles to ``EmptyResultSet`` (an ``__in=[]``)

    passes the spec-time ``is_empty()`` gate (the queryset is not ``.none()``)
    but cannot be proven byte-equal at fetch time: the byte-equal compile in
    ``_visibility_quals_match`` raises and the recognizer degrades to the
    windowed body rather than trusting the raw SQL.
    """
    child = Book.objects.only("id", "title", "shelf_id").filter(pk__in=[])
    assert not child.query.is_empty()  # slips past the spec-time is_empty() gate.
    queryset = _prefetch_filtered(
        _shelf_books_request(child_queryset=child, with_total_count=False),
        "shelf",
        [Shelf(pk=1)],
    )
    spec = queryset._dst_lateral_spec
    assert spec.visibility_where is not None
    assert _recognize_lateral_fetch(queryset, spec) is None


def test_extract_m2m_requires_the_predicted_extra_select():
    """M2M fetch time carries Django's ``_prefetch_related_val`` extra select."""
    queryset = _prefetch_filtered(_request(Genre, "books"), "genres", [Genre(pk=5)])
    spec = queryset._dst_lateral_spec
    # Before the manager's extra(select=...): the alias set mismatches -> None.
    assert _recognize_lateral_fetch(queryset, spec) is None
    with_extra = queryset.extra(
        select={"_prefetch_related_val_genre_id": '"library_book_genres"."genre_id"'},
    )
    assert _recognize_lateral_fetch(with_extra, spec).parent_ids == [5]


def test_extract_empty_parent_list_short_circuits_to_no_rows():
    """Zero parents extract as ``[]`` and fetch as ``[]`` without touching SQL."""
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [])
    assert _recognize_lateral_fetch(queryset, queryset._dst_lateral_spec).parent_ids == []


# ---------------------------------------------------------------------------
# The shared window-predicate signature (the P2 recognizer-safety boundary)
# ---------------------------------------------------------------------------


def _window_body(**overrides):
    """A bare windowed ``Book`` queryset for window-signature shape unit tests."""
    from django_strawberry_framework.optimizer.plans import apply_window_pagination

    overrides.setdefault("with_total_count", False)
    return apply_window_pagination(
        Book.objects.only("id", "title", "shelf_id"),
        partition_by="shelf_id",
        order_by=("title", "id"),
        **overrides,
    )


def test_window_signature_is_deterministic_for_one_shape():
    """Two independent builds of the same window shape sign identically (the match path)."""
    assert window_predicate_signature(_window_body(limit=2).query) == window_predicate_signature(
        _window_body(limit=2).query,
    )


def test_window_signature_distinguishes_a_changed_bound():
    """``first: 2`` and ``first: 3`` differ only in the bound value - and so do their signatures."""
    assert window_predicate_signature(_window_body(limit=2).query) != window_predicate_signature(
        _window_body(limit=3).query,
    )


def test_window_signature_of_an_unbounded_window_is_empty():
    """An unbounded forward window plans no row-number filter -> the empty signature.

    ``()`` is a real signature (no window quals), distinct from a bounded window
    that DOES plan a bound - so a dropped bound is caught as a mismatch.
    """
    assert window_predicate_signature(_window_body(limit=None).query) == ()
    assert window_predicate_signature(_window_body(limit=2).query) != ()


def test_window_signature_distinguishes_the_reversed_annotation():
    """A ``last``-only window filters the REVERSED row number - a different ``_dst_*`` name."""
    assert window_predicate_signature(
        _window_body(limit=2).query,
    ) != window_predicate_signature(_window_body(limit=2, reverse=True).query)


def test_window_signature_distinguishes_the_marker_or_shape():
    """The offset page's nested marker ``OR`` node is a distinct shape from the plain page."""
    assert window_predicate_signature(
        _window_body(offset=3, limit=2, next_page_probe=True).query,
    ) != window_predicate_signature(_window_body(limit=2).query)


def test_window_signature_is_none_when_a_bound_is_an_expression():
    """A window qual whose rhs is an expression cannot be normalized -> ``None`` (fail closed)."""
    mutated = _window_body(limit=2).filter(**{f"{WINDOW_ROW_NUMBER}__lte": F("id")})
    assert window_predicate_signature(mutated.query) is None


def test_normalize_window_node_fails_closed_on_a_nested_unmapped_leaf():
    """A nested marker OR whose leaves are not in the annotation map returns ``None``.

    Drives the internal fail-closed propagation of ``_normalize_window_node``: an
    empty ``names_by_id`` makes every leaf under the marker OR unresolvable, so the
    recursive walk short-circuits to ``None`` rather than signing an unreadable
    nested shape.
    """
    body = _window_body(offset=3, limit=2, next_page_probe=True)
    (marker_or,) = [child for child in body.query.where.children if _is_window_qual(child)]
    assert getattr(marker_or, "children", None)  # the marker arrives as a nested node.
    assert _normalize_window_node(marker_or, {}) is None


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda qs: qs.filter(title="x"), "an unexpected consumer filter"),
        (lambda qs: qs.filter(pk__in=[1]), "an IN lookup on the wrong column"),
        (
            lambda qs: qs.exclude(subtitle="x"),
            "a negated node is never a window qual or a parent filter",
        ),
        (lambda qs: qs.annotate(marker=Value(1)), "a non-window annotation"),
        (lambda qs: qs.extra(select={"marker": "1"}), "an unpredicted extra select"),
        (lambda qs: qs.order_by("-title", "id"), "fetch-time ordering drift"),
        (lambda qs: qs.reverse(), "fetch-time ordering reversal"),
        (lambda qs: qs.only("id", "shelf_id"), "fetch-time projection drift"),
        (lambda qs: qs.extra(tables=["shadow_table"]), "an unexpected extra table"),
        (lambda qs: qs.select_for_update(), "fetch-time row locking"),
        (lambda qs: qs[:5], "a sliced queryset"),
        (lambda qs: qs.distinct(), "a DISTINCT queryset"),
        (lambda qs: qs.select_related("shelf"), "a select_related graft"),
        (
            lambda qs: qs.filter(shelf__in=Shelf.objects.all()),
            "a queryset rhs is not a plain value list",
        ),
        (
            lambda qs: qs.filter(**{f"{WINDOW_ROW_NUMBER}__lte": 1}),
            "a tightened window upper bound (an extra/changed row-number lookup)",
        ),
        (
            lambda qs: qs.filter(**{f"{WINDOW_ROW_NUMBER}__gt": 1}),
            "an added window lower bound the plan never carried",
        ),
    ],
)
def test_extract_returns_none_for_unrecognized_shapes(mutate, reason):
    """Every unrecognized fetch-time mutation falls back to the windowed body.

    Includes the shared window-predicate-signature guard (P2): a leaf whose ``lhs``
    is the planned ``Window`` annotation but whose bound / multiplicity differs
    from the captured plan is caught here even though ``_is_window_qual`` would
    structurally accept it - the recognizer must execute the range it PLANNED, not
    an arbitrary row-number predicate the ORM query was mutated into.
    """
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [Shelf(pk=1)])
    mutated = mutate(queryset)
    assert _recognize_lateral_fetch(mutated, queryset._dst_lateral_spec) is None, reason


def test_extract_returns_none_without_a_parent_filter():
    """The bare planned queryset (no prefetch filter yet) has no parent list."""
    queryset = _planned_lateral_queryset(_shelf_books_request())
    assert _recognize_lateral_fetch(queryset, queryset._dst_lateral_spec) is None


def test_extract_returns_none_for_an_ored_parent_filter():
    """A parent filter nested under OR is neither a window qual nor extractable."""
    from django.db.models import Q

    queryset = _planned_lateral_queryset(_shelf_books_request(limit=None))
    queryset = queryset.filter(Q(shelf__in=[1]) | Q(title="x"))
    assert _recognize_lateral_fetch(queryset, queryset._dst_lateral_spec) is None


def test_extract_returns_none_for_a_mutated_root_node():
    """A negated or OR-connected root is not the planner's shape - fall back."""
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [Shelf(pk=1)])
    spec = queryset._dst_lateral_spec
    or_root = queryset._chain()
    or_root.query.where.connector = "OR"
    assert _recognize_lateral_fetch(or_root, spec) is None
    negated_root = queryset._chain()
    negated_root.query.where.negated = True
    assert _recognize_lateral_fetch(negated_root, spec) is None


def test_parent_in_values_guards_target_and_rhs_shapes():
    """The ``__in`` matcher's defensive tail, pinned with synthetic nodes.

    C1: ``_parent_in_values`` takes the target ``column``/``table`` as keyword
    arguments (feedback2 Step 1's signature), not a whole spec.
    """
    from django_strawberry_framework.optimizer.lateral_fetch import _parent_in_values

    no_target = SimpleNamespace(lookup_name="in", lhs=None, rhs=[1])
    assert _parent_in_values(no_target, column="shelf_id", table="library_book") is None
    unresolved_rhs = SimpleNamespace(
        lookup_name="in",
        lhs=SimpleNamespace(
            target=SimpleNamespace(
                column="shelf_id",
                model=SimpleNamespace(_meta=SimpleNamespace(db_table="library_book")),
            ),
        ),
        rhs=Shelf.objects.all(),  # a subquery rhs is not a plain value list.
    )
    assert _parent_in_values(unresolved_rhs, column="shelf_id", table="library_book") is None
    wrong_table = SimpleNamespace(
        lookup_name="in",
        lhs=SimpleNamespace(
            target=SimpleNamespace(
                column="shelf_id",
                model=SimpleNamespace(_meta=SimpleNamespace(db_table="other_table")),
            ),
        ),
        rhs=[1],
    )
    assert _parent_in_values(wrong_table, column="shelf_id", table="library_book") is None
    matching_target = SimpleNamespace(
        column="shelf_id",
        model=SimpleNamespace(_meta=SimpleNamespace(db_table="library_book")),
    )
    expression_member = SimpleNamespace(
        lookup_name="in",
        lhs=SimpleNamespace(target=matching_target),
        rhs=[1, F("id")],
    )
    assert _parent_in_values(expression_member, column="shelf_id", table="library_book") is None
    tuple_rhs = SimpleNamespace(
        lookup_name="in",
        lhs=SimpleNamespace(target=matching_target),
        rhs=(1, 2),
    )
    assert _parent_in_values(tuple_rhs, column="shelf_id", table="library_book") == [1, 2]


# ---------------------------------------------------------------------------
# Execution (scripted cursor over a Postgres facade)
# ---------------------------------------------------------------------------


class _ScriptedCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = None

    def execute(self, sql, params):
        self.executed = (sql, params)

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _PostgresFacade:
    """The real connection with the vendor flipped and the cursor scripted.

    Delegation keeps ``ops.quote_name`` and ``Field.db_type`` real, so the
    executed SQL in these tests is byte-for-byte what a Postgres connection
    would receive (modulo the backend's identical double-quote quoting).
    """

    vendor = "postgresql"

    def __init__(self, rows):
        self._real = connections["default"]
        self.scripted_cursor = _ScriptedCursor(rows)

    def cursor(self):
        return self.scripted_cursor

    def __getattr__(self, name):
        return getattr(self._real, name)


def test_lateral_execution_instantiates_window_rows(monkeypatch):
    """The full lateral fetch: extraction, SQL, params, and row instantiation."""
    from django_strawberry_framework.optimizer import lateral_fetch

    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [Shelf(pk=1), Shelf(pk=2)])
    facade = _PostgresFacade(
        rows=[
            (
                1,
                101,
                "Alpha",
                1,
                1,
                3,
            ),
            (
                1,
                102,
                "Beta",
                1,
                2,
                3,
            ),
            (
                2,
                201,
                "Gamma",
                2,
                1,
                1,
            ),
        ],
    )
    monkeypatch.setattr(lateral_fetch, "connections", {"default": facade})
    # Iterate the queryset itself (not the extraction helper): the pin covers
    # ``_fetch_all`` landing the lateral rows in the result cache.
    rows = list(queryset)
    sql, params = facade.scripted_cursor.executed
    assert "CROSS JOIN LATERAL" in sql
    assert "unnest(%s::bigint[])" in sql  # the FK db_type drives the parent array cast.
    assert params == [[1, 2], 2]
    assert [type(row) for row in rows] == [Book, Book, Book]
    assert [(row.pk, row.title, row.shelf_id) for row in rows] == [
        (101, "Alpha", 1),
        (102, "Beta", 1),
        (201, "Gamma", 2),
    ]
    assert [getattr(row, WINDOW_ROW_NUMBER) for row in rows] == [1, 2, 1]
    assert [getattr(row, WINDOW_TOTAL_COUNT) for row in rows] == [3, 3, 1]
    # The projection matches the windowed ``.only()`` shape: unfetched columns defer.
    assert rows[0].get_deferred_fields() == {"subtitle", "circulation_status"}
    assert rows[0]._state.db == "default"


def test_lateral_execution_splices_the_visibility_predicate(monkeypatch):
    """The recognized visibility scope is compiled and spliced at execution.

    The full path over the facade: a DIRECT_FK spec carrying a single-table
    ``exclude`` scope compiles that scope through the fetch-time compiler and
    splices ``AND (...)`` into the lateral branch, with its bind value in the
    params between the parent ids and the in-branch ``LIMIT``.
    """
    from django_strawberry_framework.optimizer import lateral_fetch

    queryset = _prefetch_filtered(
        _shelf_books_visibility_request(with_total_count=False),
        "shelf",
        [Shelf(pk=1)],
    )
    facade = _PostgresFacade(rows=[])
    monkeypatch.setattr(lateral_fetch, "connections", {"default": facade})
    assert _fetch_lateral_rows(queryset) == []
    sql, params = facade.scripted_cursor.executed
    assert "CROSS JOIN LATERAL" in sql
    assert 'AND (NOT ("library_book"."circulation_status" = %s))' in sql
    assert params == [[1], "repair", 2]  # parent array, scope bind, in-branch LIMIT.


def test_lateral_execution_sets_m2m_prefetch_values(monkeypatch):
    """M2M rows carry the ``_prefetch_related_val_*`` parent id Django attaches by."""
    from django_strawberry_framework.optimizer import lateral_fetch

    queryset = _prefetch_filtered(
        _request(Genre, "books", with_total_count=False),
        "genres",
        [Genre(pk=5)],
    )
    queryset = queryset.extra(
        select={"_prefetch_related_val_genre_id": '"library_book_genres"."genre_id"'},
    )
    book_fields = len(Book._meta.concrete_fields)
    row = (5, *range(100, 100 + book_fields), 1)  # pid, full projection, rn.
    facade = _PostgresFacade(rows=[row])
    monkeypatch.setattr(lateral_fetch, "connections", {"default": facade})
    (instance,) = _fetch_lateral_rows(queryset)
    assert instance._prefetch_related_val_genre_id == 5
    assert getattr(instance, WINDOW_ROW_NUMBER) == 1
    assert not hasattr(instance, WINDOW_TOTAL_COUNT)
    sql, params = facade.scripted_cursor.executed
    assert "_dst_total_count" not in sql
    assert params == [[5], 2]


def test_lateral_execution_deduplicates_parent_ids(monkeypatch):
    """Repeated parent ids execute one lateral branch instead of duplicating child rows."""
    from django_strawberry_framework.optimizer import lateral_fetch

    queryset = _prefetch_filtered(
        _shelf_books_request(),
        "shelf",
        [Shelf(pk=1), Shelf(pk=1), Shelf(pk=2)],
    )
    facade = _PostgresFacade(rows=[])
    monkeypatch.setattr(lateral_fetch, "connections", {"default": facade})
    assert _fetch_lateral_rows(queryset) == []
    _sql, params = facade.scripted_cursor.executed
    assert params == [[1, 2], 2]


def test_parent_id_deduplication_handles_hashable_and_unhashable_values():
    """Hashable values de-duplicate; unhashable values retain their input order."""
    from django_strawberry_framework.optimizer.lateral_fetch import _deduplicate_parent_ids

    assert _deduplicate_parent_ids(
        [
            1,
            None,
            1,
            2,
        ],
    ) == [1, 2]
    assert _deduplicate_parent_ids(
        [
            [1],
            None,
            [1],
            [2],
        ],
    ) == [[1], [1], [2]]


def test_lateral_raw_rows_run_through_django_field_converters():
    """Raw JSON text is converted exactly as ORM-compiled model rows are."""
    from apps.scalars.models import ScalarSpecimen

    from django_strawberry_framework.optimizer.lateral_fetch import _apply_lateral_converters

    spec = _build_lateral_spec(_shelf_books_request())
    payload_field = ScalarSpecimen._meta.get_field("payload")
    spec = dataclasses.replace(
        spec,
        model=ScalarSpecimen,
        db_table=ScalarSpecimen._meta.db_table,
        select_columns=(("payload", "payload"),),
        select_fields=(payload_field,),
    )
    converted = _apply_lateral_converters(
        spec,
        [
            (
                1,
                '{"rank": 2}',
                1,
                1,
            ),
        ],
        connections["default"],
    )
    assert converted == [
        (
            1,
            {"rank": 2},
            1,
            1,
        ),
    ]


def test_lateral_execution_serves_zero_parents_without_sql(monkeypatch):
    """An empty parent list returns an empty page without executing anything."""
    from django_strawberry_framework.optimizer import lateral_fetch

    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [])
    facade = _PostgresFacade(rows=[])
    monkeypatch.setattr(lateral_fetch, "connections", {"default": facade})
    assert _fetch_lateral_rows(queryset) == []
    assert facade.scripted_cursor.executed is None


def test_fetch_returns_none_when_extraction_fails_on_postgres(monkeypatch):
    """Unextractable state on a real-vendor connection still falls back."""
    from django_strawberry_framework.optimizer import lateral_fetch

    # The bare planned queryset carries no parent filter -> extraction None.
    queryset = _planned_lateral_queryset(_shelf_books_request())
    facade = _PostgresFacade(rows=[])
    monkeypatch.setattr(lateral_fetch, "connections", {"default": facade})
    assert _fetch_lateral_rows(queryset) is None
    assert facade.scripted_cursor.executed is None


def test_fetch_returns_none_for_values_iteration(monkeypatch):
    """``values_list()`` changes row shape - never intercepted."""
    from django_strawberry_framework.optimizer import lateral_fetch

    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [Shelf(pk=1)])
    facade = _PostgresFacade(rows=[])
    monkeypatch.setattr(lateral_fetch, "connections", {"default": facade})
    assert _fetch_lateral_rows(queryset.values_list("id")) is None


def test_fetch_vendor_follows_the_queryset_alias_not_default(monkeypatch):
    """A routed non-Postgres alias windows even when ``default`` is Postgres."""
    from django_strawberry_framework.optimizer import lateral_fetch

    queryset = _prefetch_filtered(
        _shelf_books_request(),
        "shelf",
        [Shelf(pk=1)],
    ).using("archive")
    default = _PostgresFacade(rows=[])
    archive = SimpleNamespace(vendor="sqlite")
    monkeypatch.setattr(
        lateral_fetch,
        "connections",
        {"default": default, "archive": archive},
    )

    assert queryset.db == "archive"
    assert _fetch_lateral_rows(queryset) is None
    assert default.scripted_cursor.executed is None


# ---------------------------------------------------------------------------
# The in-object windowed fallback, end to end on SQLite
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_auto_fallback_executes_the_windowed_body_end_to_end():
    """Off Postgres ``"auto"`` serves the bounded window and count annotations.

    This is the correctness floor the lateral path can never fall below: the
    auto strategy's ``LateralQuerySet`` body IS the windowed queryset, so the
    worst case of any fetch-time surprise (here: the SQLite vendor) is
    windowed SQL, not an unbounded child fetch or wrong ``hasNextPage`` input.
    """
    from apps.library.models import Branch

    branch = Branch.objects.create(name="central")
    shelf_a = Shelf.objects.create(code="a", branch=branch)
    shelf_b = Shelf.objects.create(code="b", branch=branch)
    for shelf, titles in ((shelf_a, ["t1", "t2", "t3"]), (shelf_b, [])):
        for title in titles:
            Book.objects.create(title=title, shelf=shelf)
    plan = OptimizationPlan()
    AUTO_STRATEGY.plan(_shelf_books_request(), plan)
    (entry,) = plan.prefetch_related
    assert isinstance(entry.queryset, LateralQuerySet)
    shelves = list(Shelf.objects.order_by("code").prefetch_related(entry))
    a_rows = shelves[0]._dst_books_connection
    assert [row.title for row in a_rows] == ["t1", "t2"]
    assert [getattr(row, WINDOW_ROW_NUMBER) for row in a_rows] == [1, 2]
    assert [getattr(row, WINDOW_TOTAL_COUNT) for row in a_rows] == [3, 3]
    assert len(a_rows) < getattr(a_rows[-1], WINDOW_TOTAL_COUNT)
    assert shelves[1]._dst_books_connection == []


def test_spec_downgrades_for_custom_queryset_subclasses():
    """A custom ``QuerySet`` subclass keeps the windowed strategy (feedback2 P0-5).

    ``_as_lateral_queryset`` rebinds the queryset class, which would erase a
    manager/visibility subclass's ``_clone`` state and iterator behavior.
    The lateral spec refuses anything but a plain ``QuerySet``; the windowed
    downgrade preserves the subclass AND its clone-carried state through the
    window annotations.
    """
    from django.db.models import QuerySet

    class _StatefulQuerySet(QuerySet):
        marker = None

        def _clone(self):
            clone = super()._clone()
            clone.marker = self.marker
            return clone

    stateful = _StatefulQuerySet(model=Book).only("id", "title", "shelf_id")
    stateful.marker = "visibility-scope"
    plan = OptimizationPlan()
    assert (
        LateralPrefetchStrategy().plan(
            _shelf_books_request(child_queryset=stateful),
            plan,
        )
        is True
    )
    (entry,) = plan.prefetch_related
    assert not isinstance(entry.queryset, LateralQuerySet)
    assert isinstance(entry.queryset, _StatefulQuerySet)
    assert entry.queryset.marker == "visibility-scope"
    assert WINDOW_ROW_NUMBER in entry.queryset.query.annotations
