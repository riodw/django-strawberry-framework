"""Live Postgres byte-parity tests for the lateral fetch strategy (the pg tier).

The lateral backend's correctness bar (``optimizer/lateral_fetch.py``): for
every pagination shape, the SAME GraphQL document executed under
``nested_connection_strategy="lateral"`` and ``"windowed"`` must produce
byte-identical response data at the identical fixed query cost - and the
lateral run must actually have executed ``CROSS JOIN LATERAL`` SQL, not the
in-object windowed fallback. SQLite covers the pure builder, the plan-time
downgrades, the fetch-time extraction, and the scripted-cursor execution
(``tests/optimizer/test_lateral_fetch.py``); only a real Postgres server can
prove the SQL itself, so everything here is ``@pytest.mark.pg``
(auto-skipped off Postgres by the root ``conftest.py``).
"""

import pytest
import strawberry
from apps.library.models import Book, Branch, Genre, Loan, Patron, Shelf
from django.db import connection as db_connection
from django.test.utils import CaptureQueriesContext
from strategy_schemas import build_strategy_schema, make_django_type
from strawberry.relay.utils import to_base64

from django_strawberry_framework import DjangoListField, finalize_django_types

pytestmark = [pytest.mark.pg, pytest.mark.django_db]


@pytest.fixture(autouse=True)
def _isolate_global_registry(isolate_global_registry):
    """Every test here declares fresh ``DjangoType`` classes - opt the module
    into the shared registry/connection-cache isolation (``tests/conftest.py``)."""


def _make_type(
    name,
    model,
    fields,
    *,
    total_count=False,
):
    """Declare a Relay-Node ``DjangoType``; the shared core owns the boilerplate."""
    return make_django_type(
        name,
        model,
        fields,
        meta_extra={"connection": {"total_count": True}} if total_count else None,
    )


def _library_schemas():
    """One finalized type graph, two schemas: windowed vs lateral extension.

    ``shelves`` roots the reverse-FK direction (``Shelf.books``), ``genres``
    the reverse-M2M direction (``Genre.books``); ``BookType`` carries the
    forward M2M (``genresConnection``) and the depth-2 reverse FK
    (``loansConnection``). Every connection target opts into ``totalCount``.
    """
    _make_type("LoanType", Loan, ("id", "note"), total_count=True)
    _make_type(
        "BookType",
        Book,
        (
            "id",
            "title",
            "loans",
            "genres",
        ),
        total_count=True,
    )
    genre_type = _make_type("GenreType", Genre, ("id", "name", "books"), total_count=True)
    shelf_type = _make_type("ShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type], "genres": list[genre_type]},
                "shelves": DjangoListField(shelf_type),
                "genres": DjangoListField(genre_type),
            },
        ),
    )

    # The strategy-mounting seam is the shared ``strategy_schemas`` builder -
    # the SAME construction the nested-fetch benchmark compares.
    return (
        build_strategy_schema(query_cls, "windowed"),
        build_strategy_schema(query_cls, "lateral"),
    )


def _seed_library():
    """Overlap-shaped data: uneven fan-outs, shared genres, a childless parent.

    Shelf A holds five books, shelf B one, shelf C none (the empty-window
    disambiguation case). Every book carries two of three genres (the M2M
    through-table overlap that would expose duplicate-join row inflation),
    and the first two books carry loans for the depth-2 shape.
    """
    branch = Branch.objects.create(name="central")
    shelf_a = Shelf.objects.create(code="A", branch=branch)
    shelf_b = Shelf.objects.create(code="B", branch=branch)
    Shelf.objects.create(code="C", branch=branch)
    genres = [Genre.objects.create(name=f"g{index}") for index in range(3)]
    books = []
    for index in range(5):
        book = Book.objects.create(title=f"a{index}", shelf=shelf_a)
        book.genres.add(genres[index % 3], genres[(index + 1) % 3])
        books.append(book)
    lone = Book.objects.create(title="b0", shelf=shelf_b)
    lone.genres.add(genres[0], genres[2])
    patrons = [Patron.objects.create(name=f"p{index}") for index in range(2)]
    Loan.objects.create(book=books[0], patron=patrons[0], note="n0")
    Loan.objects.create(book=books[0], patron=patrons[1], note="n1")
    Loan.objects.create(book=books[1], patron=patrons[0], note="n2")


def _canonical(data):
    """Sort every root parent list by ``id`` (the roots are unordered)."""
    return {
        root: sorted(parents, key=lambda parent: parent["id"]) for root, parents in data.items()
    }


def _assert_parity(
    query,
    *,
    queries=2,
    expect_lateral=True,
    count_free=False,
):
    """Execute under both strategies; pin identical data and the lateral cost.

    Returns ``(data, captured)`` - the (parity-asserted) response data plus
    the lateral run's ``CaptureQueriesContext`` - so tests that layer extra
    SQL-shape asserts (the through-once tripwire) reuse this preamble instead
    of re-spelling the capture/compare.
    """
    windowed_schema, lateral_schema = _library_schemas()
    windowed = windowed_schema.execute_sync(query)
    assert windowed.errors is None, windowed.errors
    with CaptureQueriesContext(db_connection) as captured:
        lateral = lateral_schema.execute_sync(query)
    assert lateral.errors is None, lateral.errors
    assert _canonical(lateral.data) == _canonical(windowed.data)
    if queries is not None:
        assert len(captured) == queries
    executed_sql = " ".join(entry["sql"] for entry in captured)
    if expect_lateral:
        assert "CROSS JOIN LATERAL" in executed_sql
    else:
        # ``expect_lateral=False`` means the shape must NOT have paid a
        # lateral (or any window) query before falling back - absence is
        # asserted, not merely unchecked (feedback2 P0-3 note).
        assert "CROSS JOIN LATERAL" not in executed_sql
    if count_free:
        assert "_dst_total_count" not in executed_sql
    return windowed.data, captured


_CHEAP_PAGE = "edges { cursor node { title } } pageInfo { hasPreviousPage startCursor }"
_FULL_PAGE = (
    "edges { cursor node { title } } totalCount "
    "pageInfo { hasPreviousPage hasNextPage startCursor endCursor }"
)
# ``hasNextPage`` selected but NOT ``totalCount`` - the count-free n+1 probe shape.
_NEXT_PAGE_PROBE = "edges { cursor node { title } } pageInfo { hasNextPage }"
# ``arrayconnection`` positional cursors: index 0 -> offset 1 (a mid-page
# ``after``), index 49 -> offset 50 (overshoots every partition).
_MID_CURSOR = to_base64("arrayconnection", "0")
_OVERSHOOT_CURSOR = to_base64("arrayconnection", "49")


@pytest.mark.parametrize(
    ("arguments", "page", "count_free"),
    [
        pytest.param("(first: 2)", _CHEAP_PAGE, True, id="first-2-count-free"),
        pytest.param("(first: 2)", _FULL_PAGE, False, id="first-2-full"),
        pytest.param("(first: 0)", _FULL_PAGE, False, id="first-0-marker"),
        pytest.param(
            f'(first: 2, after: "{_MID_CURSOR}")',
            _FULL_PAGE,
            False,
            id="after-mid",
        ),
        pytest.param(
            f'(first: 2, after: "{_OVERSHOOT_CURSOR}")',
            _FULL_PAGE,
            False,
            id="after-overshoot",
        ),
        pytest.param("(last: 2)", _FULL_PAGE, False, id="last-2"),
        pytest.param("", _FULL_PAGE, False, id="unbounded"),
    ],
)
def test_reverse_fk_parity_across_pagination_shapes(arguments, page, count_free):
    """Every reverse-FK pagination shape: identical data, two queries, real lateral."""
    _seed_library()
    data, _ = _assert_parity(
        f"{{ shelves {{ id booksConnection{arguments} {{ {page} }} }} }}",
        count_free=count_free,
    )
    assert len(data["shelves"]) == 3  # including the childless shelf C.


def test_next_page_probe_parity_is_count_free():
    """``first: N`` + ``hasNextPage`` (no ``totalCount``): the count-free n+1 probe.

    Both strategies serve identical data - ``hasNextPage`` included - with NO
    ``_dst_total_count`` / ``COUNT`` window in the executed SQL: the plain first
    page overfetches one sentinel row instead of scanning the partition to
    count. The exact ``LIMIT page + 1`` builder shape is pinned on SQLite
    (``test_sql_next_page_probe_overfetches_one_row_in_branch``); here the bar is
    that a live Postgres server pages byte-identically without a count - for a
    populated parent AND the childless shelf C (the empty-window branch).
    """
    _seed_library()
    query = f"{{ shelves {{ id code booksConnection(first: 2) {{ {_NEXT_PAGE_PROBE} }} }} }}"
    data, captured = _assert_parity(query, count_free=True)
    assert "COUNT(" not in captured[1]["sql"].upper()
    assert len(data["shelves"]) == 3  # including the childless shelf C.
    by_code = {shelf["code"]: shelf["booksConnection"] for shelf in data["shelves"]}
    # Shelf C (no books) resolves as an EMPTY page - empty edges + no next page -
    # not a missing sentinel; shelf A (5 books) reports a next page from the probe.
    assert by_code["C"]["edges"] == []
    assert by_code["C"]["pageInfo"]["hasNextPage"] is False
    assert by_code["A"]["pageInfo"]["hasNextPage"] is True


def test_next_page_probe_parity_childless_no_edges_shape():
    """The count-free probe on the no-``edges`` shape, populated and childless parents.

    The Relay invariant (``hasNextPage`` resolves without ``edges`` selected) on
    the lateral probe path: a separate test (not a second ``_assert_parity`` call
    in the sibling above) because each ``_assert_parity`` re-declares the shared
    ``DjangoType`` graph, and the registry isolation is per-test. Both strategies
    agree byte-for-byte and stay count-free; shelf C (no books) reports no next
    page, shelf A (5 books) reports one - the empty window distinguished from a
    short page with no ``edges`` in play.
    """
    _seed_library()
    query = "{ shelves { code booksConnection(first: 2) { pageInfo { hasNextPage } } } }"
    data, _ = _assert_parity(query, count_free=True)
    flags = {
        shelf["code"]: shelf["booksConnection"]["pageInfo"]["hasNextPage"]
        for shelf in data["shelves"]
    }
    assert flags["C"] is False
    assert flags["A"] is True


def test_reverse_m2m_parity_joins_the_through_table_once():
    """Reverse M2M over overlapping genre membership: parity plus a single
    through-table join in the lateral SQL (the duplicate-join tripwire)."""
    _seed_library()
    query = f"{{ genres {{ id booksConnection(first: 2) {{ {_FULL_PAGE} }} }} }}"
    data, captured = _assert_parity(query)
    lateral_sql = captured[1]["sql"]
    # The duplicate-join tripwire, lateral edition: each lateral branch scans
    # the through table exactly once (as FROM, joining the child) - a second
    # join would re-inflate the row numbers the way the historical M2M
    # prefetch duplication did.
    assert 'FROM "library_book_genres" INNER JOIN "library_book"' in lateral_sql
    assert lateral_sql.count("INNER JOIN") == 1
    assert lateral_sql.count('FROM "library_book_genres"') == 1
    # Overlap sanity: every genre relates to four books (5 two-genre shelf-A
    # books + the two-genre loner distribute evenly); each page shows 2 of 4.
    by_name = {genre["id"]: genre for genre in data["genres"]}
    counts = sorted(genre["booksConnection"]["totalCount"] for genre in by_name.values())
    assert counts == [4, 4, 4]


def test_depth_two_lateral_under_lateral_parity():
    """Nested connections two levels deep: one lateral query per level."""
    _seed_library()
    query = (
        "{ shelves { id booksConnection(first: 2) { edges { node { title "
        "loansConnection(first: 1) { edges { node { note } } totalCount } "
        "} } } } }"
    )
    _assert_parity(query, queries=3)


def test_depth_two_forward_m2m_parity():
    """Forward M2M as the inner level (``genresConnection`` under books)."""
    _seed_library()
    query = (
        "{ shelves { id booksConnection(first: 2) { edges { node { title "
        "genresConnection(first: 2) { edges { node { name } } totalCount } "
        "} } } } }"
    )
    _assert_parity(query, queries=3)


def test_last_zero_quirk_stays_parity_via_the_shared_fallback():
    """``last: 0`` falls back per-parent under BOTH strategies (the upstream
    ``edges[-0:]`` serve-all quirk) - parity holds, cost is per-parent."""
    _seed_library()
    _assert_parity(
        f"{{ shelves {{ id booksConnection(last: 0) {{ {_FULL_PAGE} }} }} }}",
        queries=None,
        expect_lateral=False,
    )


def test_stray_executor_thread_connections_are_tracked_for_session_close():
    """The root-conftest tracker registers handles main-thread teardown misses.

    The xdist ``DROP DATABASE ... is being accessed by other users`` fix
    (feedback2 P0-6): a connection opened on a non-main thread (asgiref's
    thread-sensitive executor in production async tests; a plain worker
    thread here) is invisible to pytest-django's main-thread
    ``close_all()``. The Postgres backend wrapper must register it so the
    session-teardown fixture can close it before the test database drops.
    """
    import threading

    from django.db import connections as django_connections
    from django.db.backends.postgresql import base as postgres_base

    registry_list = postgres_base._dst_stray_connection_registry
    before = len(registry_list)
    failures = []

    def _open_and_close_on_worker_thread():
        try:
            django_connections["default"].ensure_connection()
            django_connections["default"].close()
        except Exception as exc:
            failures.append(exc)

    worker = threading.Thread(target=_open_and_close_on_worker_thread)
    worker.start()
    worker.join()
    assert not failures, failures
    assert len(registry_list) > before
    # The wrapper closed its handle already; the session drain re-closing it
    # must be a harmless no-op (idempotent close is the drain's contract).
    registry_list[-1].close()
