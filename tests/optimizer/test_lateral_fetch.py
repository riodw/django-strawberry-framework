"""Tests for the Postgres lateral fetch strategy (``optimizer/lateral_fetch.py``).

Everything here runs on SQLite (the coverage tier): ``build_lateral_sql`` is
pure, plan-time spec building and downgrades never touch the DB, fetch-time
parent-id extraction runs against real querysets shaped by Django's own
``_filter_prefetch_queryset``, and the raw-SQL execution path runs through a
Postgres facade over the real connection with a scripted cursor. The
``@pytest.mark.pg`` live tier re-proves the same SQL against a real Postgres
server (``tests/test_lateral_pg_parity.py``).
"""

from types import SimpleNamespace

import pytest
from apps.library.models import Book, Genre, Shelf
from django.db import connections
from django.db.models import F, Prefetch, Value
from django.db.models.fields.related_descriptors import _filter_prefetch_queryset

from django_strawberry_framework.optimizer.join_taxonomy import classify_relation_join
from django_strawberry_framework.optimizer.lateral_fetch import (
    LATERAL_STRATEGY,
    LateralPrefetchStrategy,
    LateralQuerySet,
    _build_lateral_spec,
    _extract_parent_ids,
    _fetch_lateral_rows,
    build_lateral_sql,
)
from django_strawberry_framework.optimizer.nested_fetch import NestedConnectionRequest
from django_strawberry_framework.optimizer.plans import (
    WINDOW_ROW_NUMBER,
    WINDOW_TOTAL_COUNT,
    OptimizationPlan,
)


def _quote(name):
    """The identifier quoting the pure-builder tests pin against."""
    return f'"{name}"'


def _request(field_owner, field_name, **overrides):
    """A minimal valid ``NestedConnectionRequest`` for one library relation."""
    field = field_owner._meta.get_field(field_name)
    child_model = field.related_model
    values = {
        "django_field": field,
        "relation_field_name": field_name,
        "prefix": "",
        "child_queryset": child_model.objects.all(),
        "join": classify_relation_join(field),
        "order_by": ("pk",),
        "offset": 0,
        "limit": 2,
        "reverse": False,
        "with_total_count": True,
        "to_attr": f"_dst_{field_name}_connection",
        "lookup": field_name,
    }
    values.update(overrides)
    return NestedConnectionRequest(**values)


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
    assert spec.child_pk_column == "id"
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
    assert spec.prefetch_value_aliases == ("_prefetch_related_val_book_id",)


def test_spec_reverse_m2m_swaps_the_through_sides():
    """Reverse M2M (``Genre.books``): the same through table, sides swapped."""
    spec = _build_lateral_spec(_request(Genre, "books"))
    assert spec.model is Book
    assert spec.parent_link_table == "library_book_genres"
    assert spec.parent_link_column == "genre_id"
    assert spec.through_child_column == "book_id"
    assert spec.prefetch_value_aliases == ("_prefetch_related_val_genre_id",)


def test_spec_maps_pk_alias_and_descending_order():
    """``"pk"`` resolves to the pk column; a ``-`` prefix flips to DESC."""
    spec = _build_lateral_spec(_shelf_books_request(order_by=("-title", "pk")))
    assert spec.order_columns == (("title", True), ("id", False))


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        (
            {"child_queryset": Book.objects.filter(title__startswith="A")},
            "pre-filtered child (custom get_queryset / visibility scope)",
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
    """A composite (columnless) child pk has no single unnest join column."""
    fake_queryset = SimpleNamespace(
        query=SimpleNamespace(
            where=SimpleNamespace(children=[]),
            select_related=False,
            annotations={},
            extra={},
        ),
        model=SimpleNamespace(_meta=SimpleNamespace(pk=SimpleNamespace(column=None))),
    )
    assert _build_lateral_spec(_request(Shelf, "books", child_queryset=fake_queryset)) is None


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
    sql, params = build_lateral_sql(spec, [1, 2, 3], quote_name=_quote, array_cast="bigint")
    assert sql.startswith(
        'SELECT "__dst_parents"."__dst_parent_id", "__dst_window"."id",'
        ' "__dst_window"."title", "__dst_window"."shelf_id",'
        ' "__dst_window"."_dst_row_number", "__dst_window"."_dst_total_count"'
        ' FROM unnest(%s::bigint[]) AS "__dst_parents"("__dst_parent_id")'
        " CROSS JOIN LATERAL (",
    )
    assert (
        'ROW_NUMBER() OVER (ORDER BY "library_book"."title" ASC, "library_book"."id" ASC)'
        ' AS "_dst_row_number"' in sql
    )
    assert 'COUNT(1) OVER () AS "_dst_total_count"' in sql
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
    assert "unnest(%s)" in sql  # no cast when the caller has none.
    assert params == [[1], 2]


def test_sql_offset_shape_keeps_the_marker_row():
    """Overshot ``after:``: the ambiguous-shape ``OR rn = 1`` marker survives."""
    spec = _build_lateral_spec(_shelf_books_request(offset=3, limit=2))
    sql, params = build_lateral_sql(spec, [7], quote_name=_quote)
    assert (
        'WHERE ("__dst_window"."_dst_row_number" > %s'
        ' AND "__dst_window"."_dst_row_number" <= %s)'
        ' OR "__dst_window"."_dst_row_number" = 1' in sql
    )
    assert params == [[7], 3, 5]


def test_sql_first_zero_shape_keeps_the_marker_row():
    """``first: 0``: upper bound zero plus the marker row."""
    spec = _build_lateral_spec(_shelf_books_request(offset=0, limit=0))
    sql, params = build_lateral_sql(spec, [7], quote_name=_quote)
    assert (
        'WHERE ("__dst_window"."_dst_row_number" <= %s)'
        ' OR "__dst_window"."_dst_row_number" = 1' in sql
    )
    assert params == [[7], 0]


def test_sql_unbounded_shape_has_no_range_predicate():
    """``limit=None`` (or the relay maxsize sentinel): every row, no WHERE."""
    spec = _build_lateral_spec(_shelf_books_request(limit=None))
    sql, params = build_lateral_sql(spec, [7], quote_name=_quote)
    assert ') "__dst_window" ORDER BY' in sql
    assert params == [[7]]


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
    assert params == [[7], 2]


def test_sql_reverse_shape_applies_the_offset_filter_when_present():
    """The reverse branch mirrors ``apply_window_pagination``'s offset filter."""
    spec = _build_lateral_spec(_shelf_books_request(reverse=True, offset=1, limit=2))
    sql, params = build_lateral_sql(spec, [7], quote_name=_quote)
    assert (
        'WHERE "__dst_window"."_dst_row_number" > %s'
        ' AND "__dst_window"."_dst_row_number_reversed" <= %s' in sql
    )
    assert params == [[7], 1, 2]


def test_sql_through_table_shape_joins_inside_the_lateral():
    """M2M: the through table drives the lateral branch and the parent match."""
    spec = _build_lateral_spec(_request(Genre, "books"))
    sql, params = build_lateral_sql(spec, [5, 6], quote_name=_quote, array_cast="bigint")
    assert (
        'FROM "library_book_genres" INNER JOIN "library_book"'
        ' ON "library_book"."id" = "library_book_genres"."book_id"' in sql
    )
    assert 'WHERE "library_book_genres"."genre_id" = "__dst_parents"."__dst_parent_id"' in sql
    assert params == [[5, 6], 2]


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
    assert _extract_parent_ids(queryset, queryset._dst_lateral_spec) == [1, 2, 3]


def test_extract_recognizes_the_marker_or_node():
    """The ambiguous-shape marker filter arrives as a nested OR of window quals."""
    queryset = _prefetch_filtered(
        _shelf_books_request(offset=3, limit=2),
        "shelf",
        [Shelf(pk=4)],
    )
    assert _extract_parent_ids(queryset, queryset._dst_lateral_spec) == [4]


def test_extract_recognizes_the_reversed_window_qual():
    """``last``-only windows filter on the reversed row number - still a window qual."""
    queryset = _prefetch_filtered(
        _shelf_books_request(reverse=True, limit=2),
        "shelf",
        [Shelf(pk=4)],
    )
    assert _extract_parent_ids(queryset, queryset._dst_lateral_spec) == [4]


def test_extract_m2m_requires_the_predicted_extra_select():
    """M2M fetch time carries Django's ``_prefetch_related_val`` extra select."""
    queryset = _prefetch_filtered(_request(Genre, "books"), "genres", [Genre(pk=5)])
    spec = queryset._dst_lateral_spec
    # Before the manager's extra(select=...): the alias set mismatches -> None.
    assert _extract_parent_ids(queryset, spec) is None
    with_extra = queryset.extra(
        select={"_prefetch_related_val_genre_id": '"library_book_genres"."genre_id"'},
    )
    assert _extract_parent_ids(with_extra, spec) == [5]


def test_extract_empty_parent_list_short_circuits_to_no_rows():
    """Zero parents extract as ``[]`` and fetch as ``[]`` without touching SQL."""
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [])
    assert _extract_parent_ids(queryset, queryset._dst_lateral_spec) == []


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
        (lambda qs: qs[:5], "a sliced queryset"),
        (lambda qs: qs.distinct(), "a DISTINCT queryset"),
        (lambda qs: qs.select_related("shelf"), "a select_related graft"),
        (
            lambda qs: qs.filter(shelf__in=Shelf.objects.all()),
            "a queryset rhs is not a plain value list",
        ),
    ],
)
def test_extract_returns_none_for_unrecognized_shapes(mutate, reason):
    """Every unrecognized fetch-time mutation falls back to the windowed body."""
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [Shelf(pk=1)])
    mutated = mutate(queryset)
    assert _extract_parent_ids(mutated, queryset._dst_lateral_spec) is None, reason


def test_extract_returns_none_without_a_parent_filter():
    """The bare planned queryset (no prefetch filter yet) has no parent list."""
    queryset = _planned_lateral_queryset(_shelf_books_request())
    assert _extract_parent_ids(queryset, queryset._dst_lateral_spec) is None


def test_extract_returns_none_for_an_ored_parent_filter():
    """A parent filter nested under OR is neither a window qual nor extractable."""
    from django.db.models import Q

    queryset = _planned_lateral_queryset(_shelf_books_request(limit=None))
    queryset = queryset.filter(Q(shelf__in=[1]) | Q(title="x"))
    assert _extract_parent_ids(queryset, queryset._dst_lateral_spec) is None


def test_extract_returns_none_for_a_mutated_root_node():
    """A negated or OR-connected root is not the planner's shape - fall back."""
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [Shelf(pk=1)])
    spec = queryset._dst_lateral_spec
    or_root = queryset._chain()
    or_root.query.where.connector = "OR"
    assert _extract_parent_ids(or_root, spec) is None
    negated_root = queryset._chain()
    negated_root.query.where.negated = True
    assert _extract_parent_ids(negated_root, spec) is None


def test_parent_in_values_guards_target_and_rhs_shapes():
    """The ``__in`` matcher's defensive tail, pinned with synthetic nodes."""
    from django_strawberry_framework.optimizer.lateral_fetch import _parent_in_values

    spec = _build_lateral_spec(_shelf_books_request())
    no_target = SimpleNamespace(lookup_name="in", lhs=None, rhs=[1])
    assert _parent_in_values(no_target, spec) is None
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
    assert _parent_in_values(unresolved_rhs, spec) is None
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
    assert _parent_in_values(wrong_table, spec) is None
    matching_target = SimpleNamespace(
        column="shelf_id",
        model=SimpleNamespace(_meta=SimpleNamespace(db_table="library_book")),
    )
    expression_member = SimpleNamespace(
        lookup_name="in",
        lhs=SimpleNamespace(target=matching_target),
        rhs=[1, F("id")],
    )
    assert _parent_in_values(expression_member, spec) is None
    tuple_rhs = SimpleNamespace(
        lookup_name="in",
        lhs=SimpleNamespace(target=matching_target),
        rhs=(1, 2),
    )
    assert _parent_in_values(tuple_rhs, spec) == [1, 2]


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
    assert "::bigint[]" in sql  # the FK db_type drives the unnest element cast.
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


# ---------------------------------------------------------------------------
# The in-object windowed fallback, end to end on SQLite
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_fallback_executes_the_windowed_body_end_to_end():
    """Off Postgres the SAME queryset serves the identical windowed page.

    This is the correctness floor the lateral path can never fall below: the
    ``LateralQuerySet`` body IS the windowed queryset, so the worst case of
    any fetch-time surprise (here: the SQLite vendor) is windowed SQL, not a
    wrong result.
    """
    from apps.library.models import Branch

    branch = Branch.objects.create(name="central")
    shelf_a = Shelf.objects.create(code="a", branch=branch)
    shelf_b = Shelf.objects.create(code="b", branch=branch)
    for shelf, titles in ((shelf_a, ["t1", "t2", "t3"]), (shelf_b, [])):
        for title in titles:
            Book.objects.create(title=title, shelf=shelf)
    plan = OptimizationPlan()
    LATERAL_STRATEGY.plan(_shelf_books_request(), plan)
    (entry,) = plan.prefetch_related
    shelves = list(Shelf.objects.order_by("code").prefetch_related(entry))
    a_rows = shelves[0]._dst_books_connection
    assert [row.title for row in a_rows] == ["t1", "t2"]
    assert [getattr(row, WINDOW_ROW_NUMBER) for row in a_rows] == [1, 2]
    assert [getattr(row, WINDOW_TOTAL_COUNT) for row in a_rows] == [3, 3]
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
