"""Tests for the single-parent window fast path (``optimizer/single_parent_fetch.py``).

Everything here runs on SQLite (the coverage tier). Plan-time eligibility
(``single_parent_spec``) and fetch-time recognition (``_fetch_single_parent_rows``)
are pure state inspection - they never touch the DB and fall back to ``None`` for
any shape they do not fully recognize, so the windowed body the strategy already
planned runs instead. The ``@pytest.mark.django_db`` block re-proves that the
recognized shape synthesizes the same ``_dst_row_number`` / probe / nested-prefetch
contract the windowed body would, and that a refused shape still returns correct
rows via that body.

``_parent_in_values`` carries the keyword ``column=`` / ``table=`` signature
(feedback2 Step 1); its defensive matrix is owned by
``test_lateral_fetch.py::test_parent_in_values_guards_target_and_rhs_shapes`` (one
owner), as is the unhashable/NULL ``_deduplicate_parent_ids`` TypeError arm
(``test_parent_id_deduplication_handles_hashable_and_unhashable_values``). Both are
imported here, not re-tested.
"""

import pytest
from apps.library.models import Book, Branch, Genre, Shelf
from django.db.models import QuerySet, Value
from django.db.models.fields.related_descriptors import _filter_prefetch_queryset

from django_strawberry_framework.optimizer.nested_fetch import WindowedPrefetchStrategy
from django_strawberry_framework.optimizer.plans import (
    WINDOW_ROW_NUMBER,
    WINDOW_TOTAL_COUNT,
    OptimizationPlan,
)
from django_strawberry_framework.optimizer.single_parent_fetch import (
    SingleParentWindowQuerySet,
    _fetch_single_parent_rows,
    single_parent_spec,
)
from tests.optimizer._builders import nested_connection_request as _request


def _shelf_books_request(**overrides):
    """Reverse FK ``Shelf.books``, count-free (the fast-path-eligible shape).

    The single-parent fast path only engages count-free (``totalCount`` keeps the
    window), so this helper defaults ``with_total_count=False`` - the eligibility
    reject-matrix flips it back on explicitly.
    """
    overrides.setdefault("child_queryset", Book.objects.only("id", "title", "shelf_id"))
    overrides.setdefault("order_by", ("title", "id"))
    overrides.setdefault("with_total_count", False)
    return _request(Shelf, "books", **overrides)


def _planned_single_parent_queryset(request):
    """Run the windowed strategy and return the planned ``SingleParentWindowQuerySet``."""
    plan = OptimizationPlan()
    assert WindowedPrefetchStrategy().plan(request, plan) is True
    (entry,) = plan.prefetch_related
    assert isinstance(entry.queryset, SingleParentWindowQuerySet)
    return entry.queryset


def _prefetch_filtered(request, field_name, parents):
    """The planned queryset exactly as Django's prefetch hands it to ``_fetch_all``."""
    queryset = _planned_single_parent_queryset(request)
    return _filter_prefetch_queryset(queryset, field_name, parents)


# ---------------------------------------------------------------------------
# Plan-time eligibility (single_parent_spec)
# ---------------------------------------------------------------------------


def test_spec_accepts_the_plain_first_page():
    """A count-free plain ``first: N`` DIRECT_FK page resolves to a spec."""
    spec = single_parent_spec(_shelf_books_request())
    assert spec is not None
    assert spec.fetch_limit == 2  # no probe -> LIMIT equals the page size (limit 2).
    assert spec.order_by == ("title", "id")
    assert spec.parent_link_attname == "shelf_id"
    assert spec.parent_link_column == "shelf_id"
    assert spec.parent_link_table == "library_book"
    assert spec.pristine_child_queryset is not None


def test_spec_probe_overfetches_one_row():
    """The count-free ``hasNextPage`` probe sets ``fetch_limit == limit + 1``."""
    spec = single_parent_spec(_shelf_books_request(next_page_probe=True))
    assert spec is not None
    assert spec.fetch_limit == 3  # limit 2 + 1 probe sentinel.


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"with_total_count": True}, "totalCount cannot come from a bare LIMIT"),
        ({"reverse": True}, "last-only needs the reversed row number"),
        ({"offset": 3}, "an offset page is not the plain first page"),
        ({"limit": None}, "an unbounded page has no LIMIT to push down"),
        ({"limit": 0}, "first: 0 is not a positive bounded page"),
    ],
)
def test_spec_rejects_ineligible_windows(overrides, reason):
    """Every window shape but the count-free plain first page keeps the window."""
    assert single_parent_spec(_shelf_books_request(**overrides)) is None, reason


def test_spec_rejects_a_keyset_seek():
    """A keyset ``after:`` seek is out of v1 scope (not a plain filtered LIMIT)."""
    from django_strawberry_framework.keyset import (
        KeysetCursor,
        KeysetSeek,
        cursor_columns_for,
    )

    seek = KeysetSeek(
        columns=cursor_columns_for(Book, ("title", "id")),
        cursor=KeysetCursor(values=("m", 1)),
    )
    assert single_parent_spec(_shelf_books_request(keyset_seek=seek)) is None


def test_spec_rejects_a_custom_queryset_subclass():
    """A manager/visibility subclass keeps the window (the class rebind would erase it)."""

    class _StatefulQuerySet(QuerySet):
        marker = None

    stateful = _StatefulQuerySet(model=Book).only("id", "title", "shelf_id")
    assert single_parent_spec(_shelf_books_request(child_queryset=stateful)) is None


def test_spec_rejects_a_through_table_join():
    """M2M / THROUGH_TABLE is excluded in v1 (correction 2)."""
    assert single_parent_spec(_request(Book, "genres", with_total_count=False)) is None


# ---------------------------------------------------------------------------
# Fetch-time recognizer refusal matrix (_fetch_single_parent_rows -> None)
# ---------------------------------------------------------------------------


def test_fetch_returns_none_without_a_spec():
    """A ``SingleParentWindowQuerySet`` built outside the strategy falls straight back."""
    assert _fetch_single_parent_rows(SingleParentWindowQuerySet(model=Book)) is None


def test_fetch_returns_none_when_the_setting_is_disabled(settings):
    """``SINGLE_PARENT_FAST_PATH=False`` is observed live at fetch time."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"SINGLE_PARENT_FAST_PATH": False}
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [Shelf(pk=1)])
    assert _fetch_single_parent_rows(queryset) is None


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda qs: qs.values_list("id"), "a values() iterable changes row shape"),
        (lambda qs: qs[:5], "a sliced queryset"),
        (lambda qs: qs.distinct(), "a DISTINCT queryset"),
        (lambda qs: qs.extra(select={"marker": "1"}), "an unpredicted extra select"),
        (lambda qs: qs.extra(tables=["shadow_table"]), "an unexpected extra table"),
        (lambda qs: qs.select_for_update(), "fetch-time row locking"),
        (lambda qs: qs.order_by("subtitle", "id"), "fetch-time ordering drift"),
        (lambda qs: qs.reverse(), "fetch-time ordering reversal"),
        (lambda qs: qs.annotate(marker=Value(1)), "a non-window annotation"),
        (lambda qs: qs.only("id"), "fetch-time projection drift from the planned only()"),
        (lambda qs: qs.select_related("shelf"), "fetch-time select_related drift"),
        (lambda qs: qs.filter(title="x"), "a second unrecognized qual"),
        (lambda qs: qs.filter(shelf__in=[2]), "a second parent IN qual"),
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
def test_fetch_returns_none_for_unrecognized_shapes(mutate, reason):
    """Every unrecognized fetch-time mutation falls back to the windowed body.

    Includes the shared window-predicate-signature guard (P2): the plain re-query
    applies ``spec.fetch_limit``, so an altered row-number bound that
    ``_single_parent_where_ids`` would skip as a window qual must be caught by the
    signature comparison, or the fast path would silently ignore it and serve the
    originally-planned page.
    """
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [Shelf(pk=1)])
    assert _fetch_single_parent_rows(mutate(queryset)) is None, reason


def test_fetch_returns_none_without_a_parent_filter():
    """The bare planned queryset (only the window qual) has no parent list."""
    queryset = _planned_single_parent_queryset(_shelf_books_request())
    assert _fetch_single_parent_rows(queryset) is None


def test_fetch_returns_none_for_a_consumer_filter_without_a_parent():
    """A non-window child that is not the parent IN fails the WHERE walk closed."""
    queryset = _planned_single_parent_queryset(_shelf_books_request()).filter(title="x")
    assert _fetch_single_parent_rows(queryset) is None


def test_fetch_returns_none_for_a_mutated_root_node():
    """A negated or OR-connected WHERE root is not the planner's shape."""
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [Shelf(pk=1)])
    or_root = queryset._chain()
    or_root.query.where.connector = "OR"
    assert _fetch_single_parent_rows(or_root) is None
    negated_root = queryset._chain()
    negated_root.query.where.negated = True
    assert _fetch_single_parent_rows(negated_root) is None


def test_fetch_returns_none_for_zero_parents():
    """Zero parents (dedup to ``[]``) fall to the windowed body's empty result."""
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [])
    assert _fetch_single_parent_rows(queryset) is None


def test_fetch_returns_none_for_two_parents():
    """Two distinct parents are not the degenerate single-parent shape."""
    queryset = _prefetch_filtered(
        _shelf_books_request(),
        "shelf",
        [Shelf(pk=1), Shelf(pk=2)],
    )
    assert _fetch_single_parent_rows(queryset) is None


# ---------------------------------------------------------------------------
# Row synthesis and the windowed-body fallback, end to end on SQLite
# ---------------------------------------------------------------------------


def _seed_shelf(titles):
    """One shelf carrying ``titles`` books in a fresh branch."""
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="a", branch=branch)
    for title in titles:
        Book.objects.create(title=title, shelf=shelf)
    return shelf


@pytest.mark.django_db
def test_fast_path_synthesizes_forward_row_numbers():
    """The recognized shape returns rn 1..N, forward-ordered, count-free, LIMIT-bounded."""
    shelf = _seed_shelf(["t1", "t2", "t3"])
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [shelf])
    rows = _fetch_single_parent_rows(queryset)
    assert rows is not None
    assert [row.title for row in rows] == ["t1", "t2"]  # order_by title, LIMIT 2.
    assert [getattr(row, WINDOW_ROW_NUMBER) for row in rows] == [1, 2]
    assert not any(hasattr(row, WINDOW_TOTAL_COUNT) for row in rows)


@pytest.mark.django_db
def test_fast_path_probe_overfetches_the_sentinel_row():
    """The probe shape fetches ``limit + 1`` rows, numbering the sentinel ``limit + 1``."""
    shelf = _seed_shelf(["t1", "t2", "t3"])
    queryset = _prefetch_filtered(
        _shelf_books_request(next_page_probe=True),
        "shelf",
        [shelf],
    )
    rows = _fetch_single_parent_rows(queryset)
    assert rows is not None
    assert [row.title for row in rows] == ["t1", "t2", "t3"]
    assert [getattr(row, WINDOW_ROW_NUMBER) for row in rows] == [1, 2, 3]


@pytest.mark.django_db
def test_fast_path_accepts_a_duplicated_single_parent_id():
    """Repeated parent ids dedup to one and still fetch the page once."""
    shelf = _seed_shelf(["t1", "t2", "t3"])
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [shelf, shelf])
    rows = _fetch_single_parent_rows(queryset)
    assert rows is not None
    assert [getattr(row, WINDOW_ROW_NUMBER) for row in rows] == [1, 2]


@pytest.mark.django_db
def test_fast_path_populates_a_nested_prefetch():
    """The pristine child clone carries nested prefetches, so two-level nesting resolves."""
    shelf = _seed_shelf(["t1"])
    genre = Genre.objects.create(name="fiction")
    Book.objects.get(title="t1").genres.add(genre)
    request = _shelf_books_request(child_queryset=Book.objects.prefetch_related("genres"))
    queryset = _prefetch_filtered(request, "shelf", [shelf])
    rows = list(queryset)  # drive _fetch_all so the nested prefetch pass runs.
    assert "genres" in rows[0]._prefetched_objects_cache
    assert list(rows[0].genres.all()) == [genre]


@pytest.mark.django_db
def test_refused_shape_falls_back_to_the_windowed_body(settings):
    """A refused fast path still serves correct rows via the windowed body (degrade, not break)."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"SINGLE_PARENT_FAST_PATH": False}
    shelf = _seed_shelf(["t1", "t2", "t3"])
    queryset = _prefetch_filtered(_shelf_books_request(), "shelf", [shelf])
    assert _fetch_single_parent_rows(queryset) is None
    rows = list(queryset)  # the superclass windowed body runs instead.
    assert [row.title for row in rows] == ["t1", "t2"]
    assert [getattr(row, WINDOW_ROW_NUMBER) for row in rows] == [1, 2]


def test_clone_carries_the_spec():
    """Every clone Django's prefetch machinery makes keeps the single-parent spec."""
    queryset = _planned_single_parent_queryset(_shelf_books_request())
    spec = queryset._dst_single_parent_spec
    assert spec is not None
    filtered = queryset.using("default").filter(pk__gt=0)
    assert isinstance(filtered, SingleParentWindowQuerySet)
    assert filtered._dst_single_parent_spec is spec
    # The captured window-range signature rides every clone too.
    assert filtered._dst_window_signature == queryset._dst_window_signature
    assert queryset._dst_window_signature is not None
    # The windowed body rode along verbatim (the in-object fallback).
    assert WINDOW_ROW_NUMBER in queryset.query.annotations
