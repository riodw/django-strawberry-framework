"""Postgres lateral-fetch tests for parity, SQL shape, cleanup, custom joins, adaptation, and index seeks.

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

from django_strawberry_framework import (
    DjangoListField,
    OptimizerHint,
    finalize_django_types,
)

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


@pytest.mark.parametrize(
    "arguments",
    [
        # Bounded offset page: the composed probe + marker (A1 lateral half - the
        # ``fetch_upper_bound`` rn-filter bind, invisible on the SQLite tier).
        pytest.param(f'(first: 2, after: "{_MID_CURSOR}")', id="offset-probe"),
        # Offset overshoot: marker-only, hasNextPage False, no per-parent fallback.
        pytest.param(f'(first: 2, after: "{_OVERSHOOT_CURSOR}")', id="offset-overshoot"),
        # Unbounded forward: constant-False hasNextPage (A2).
        pytest.param("", id="unbounded-constant-false"),
        # Reversed last:N: constant-False hasNextPage (A2).
        pytest.param("(last: 2)", id="reverse-constant-false"),
    ],
)
def test_count_free_has_next_page_parity_across_shapes(arguments):
    """WS-A count-free ``hasNextPage`` shapes page byte-identically with NO count.

    The A1 composed offset probe (bounded offset page) and the A2 constant-False
    shapes (unbounded forward, reversed ``last: N``, offset overshoot) all resolve
    ``hasNextPage`` without a ``COUNT(1) OVER`` window under BOTH strategies. The
    lateral half of the offset probe depends on the ``fetch_upper_bound``
    rn-filter bind (a raw ``upper_bound`` would read ``hasNextPage`` constantly
    False on PG only). Byte parity + count-free + fixed two-query cost (no
    per-parent fallback, asserted via the real lateral join) is the bar.
    """
    _seed_library()
    query = f"{{ shelves {{ id code booksConnection{arguments} {{ {_NEXT_PAGE_PROBE} }} }} }}"
    _assert_parity(query, count_free=True)


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
    # ``id`` rides along for ``_assert_parity``'s ``_canonical`` root sort,
    # not the shape under test (the no-``edges`` invariant is on the nested
    # connection's selection, which stays ``pageInfo``-only).
    query = "{ shelves { id code booksConnection(first: 2) { pageInfo { hasNextPage } } } }"
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
    assert (
        'FROM "library_book_genres" AS "__dst_through"'
        ' INNER JOIN "library_book" AS "__dst_child"' in lateral_sql
    )
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


def test_divergent_alias_parity_one_lateral_per_response_key():
    """Divergent aliases ride the lateral backend too: one lateral query per key.

    The idea-#2 per-response-key scheme is strategy-independent - the walker
    hands one ``NestedConnectionRequest`` per key, so the lateral strategy
    plans one ``CROSS JOIN LATERAL`` query per alias (3 queries total: roots +
    2 laterals) with byte parity against the windowed strategy. Neither alias
    observes ``totalCount``, so BOTH per-key windows engage the count-free n+1
    probe (idea-#1 interplay) - the executed SQL carries no count aggregate.
    """
    _seed_library()
    query = (
        "{ shelves { id code "
        f"a: booksConnection(first: 2) {{ {_NEXT_PAGE_PROBE} }} "
        f"b: booksConnection(first: 9) {{ {_NEXT_PAGE_PROBE} }} "
        "} }"
    )
    data, captured = _assert_parity(query, queries=3, count_free=True)
    executed_sql = " ".join(entry["sql"] for entry in captured)
    assert "COUNT(" not in executed_sql.upper()
    by_code = {shelf["code"]: shelf for shelf in data["shelves"]}
    # Shelf A (5 books): each alias serves ITS OWN page bound and probe flag.
    assert len(by_code["A"]["a"]["edges"]) == 2
    assert by_code["A"]["a"]["pageInfo"]["hasNextPage"] is True
    assert len(by_code["A"]["b"]["edges"]) == 5
    assert by_code["A"]["b"]["pageInfo"]["hasNextPage"] is False
    # Childless shelf C: an empty page for BOTH per-key windows.
    assert by_code["C"]["a"]["edges"] == []
    assert by_code["C"]["b"]["pageInfo"]["hasNextPage"] is False


def test_divergent_alias_total_count_sibling_keeps_count_on_both_laterals():
    """A ``totalCount`` alias keeps the count on EVERY divergent lateral window.

    The union-conservative observer rule under the lateral backend: ``b``
    observing ``totalCount`` retains the count on ``a``'s window too (no probe
    on either), and each alias still pages by its own bound with full parity.
    """
    _seed_library()
    query = (
        "{ shelves { id code "
        f"a: booksConnection(first: 2) {{ {_NEXT_PAGE_PROBE} }} "
        f"b: booksConnection(first: 9) {{ {_FULL_PAGE} }} "
        "} }"
    )
    data, captured = _assert_parity(query, queries=3)
    # EACH lateral window query carries the count annotation (union rule, per
    # window) - asserted per captured query, not on the concatenated SQL,
    # because one counted lateral alone emits the token twice (inner alias +
    # outer select) and would satisfy a global count even if the sibling
    # window regressed to the probe.
    window_sqls = [entry["sql"] for entry in captured if "CROSS JOIN LATERAL" in entry["sql"]]
    assert len(window_sqls) == 2
    for window_sql in window_sqls:
        assert "_dst_total_count" in window_sql
    by_code = {shelf["code"]: shelf for shelf in data["shelves"]}
    assert by_code["A"]["a"]["pageInfo"]["hasNextPage"] is True
    assert by_code["A"]["b"]["totalCount"] == 5


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


# =============================================================================
# WS-C: single-table visibility WHERE (a get_queryset scope) on the lateral path
# =============================================================================


def _visibility_schemas():
    """A ``ShelfType.booksConnection`` whose child type hides repair books.

    The anonymous-traffic substrate: ``get_queryset`` applies a single-table
    plain-column ``exclude`` (the ``BookType`` visibility shape), which used to
    force the windowed body and now rides the lateral branch as a spliced
    WHERE. The scope is unconditional so both strategies filter identically.
    """

    @classmethod
    def _hide_repair(cls, queryset, info):
        return queryset.exclude(circulation_status="repair")

    make_django_type(
        "VisibilityBookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
        namespace_extra={"get_queryset": _hide_repair},
    )
    shelf_type = make_django_type("VisibilityShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    return (
        build_strategy_schema(query_cls, "windowed"),
        build_strategy_schema(query_cls, "lateral"),
    )


def _seed_visibility():
    """Shelf A: four visible books + two hidden ``repair`` books; shelf B empty."""
    branch = Branch.objects.create(name="central")
    shelf_a = Shelf.objects.create(code="A", branch=branch)
    Shelf.objects.create(code="B", branch=branch)
    for index in range(4):
        Book.objects.create(
            title=f"a{index}",
            shelf=shelf_a,
            circulation_status=Book.CirculationStatus.AVAILABLE,
        )
    for index in range(2):
        Book.objects.create(
            title=f"r{index}",
            shelf=shelf_a,
            circulation_status=Book.CirculationStatus.REPAIR,
        )


def test_visibility_scope_takes_the_lateral_path_with_parity():
    """A single-table ``get_queryset`` scope now takes the lateral path.

    The headline WS-C win: anonymous traffic over a visibility-scoped connection
    executes ``CROSS JOIN LATERAL`` (not the windowed downgrade), the scope's
    column rides into the lateral SQL, and the response is byte-identical to the
    windowed strategy - the hidden ``repair`` books excluded under both.
    """
    _seed_visibility()
    windowed_schema, lateral_schema = _visibility_schemas()
    query = (
        "{ shelves { id code booksConnection(first: 2) "
        "{ edges { node { title } } totalCount pageInfo { hasNextPage } } } }"
    )
    windowed = windowed_schema.execute_sync(query)
    assert windowed.errors is None, windowed.errors
    with CaptureQueriesContext(db_connection) as captured:
        lateral = lateral_schema.execute_sync(query)
    assert lateral.errors is None, lateral.errors
    assert _canonical(lateral.data) == _canonical(windowed.data)
    executed_sql = " ".join(entry["sql"] for entry in captured)
    assert "CROSS JOIN LATERAL" in executed_sql
    assert "circulation_status" in executed_sql  # the scope rode into the branch.
    by_code = {shelf["code"]: shelf["booksConnection"] for shelf in lateral.data["shelves"]}
    # Anonymous sees only the four available books on shelf A (two repair hidden).
    assert by_code["A"]["totalCount"] == 4
    assert by_code["A"]["pageInfo"]["hasNextPage"] is True


def test_visibility_scope_lateral_applies_the_filter_exactly_once():
    """The scope predicate is spliced ONCE - no double-apply, correct rows.

    A double-apply would be invisible on this idempotent ``exclude``, so the pin
    is structural: the ``circulation_status`` predicate appears exactly once in
    the executed lateral SQL, and only the four visible books surface.
    """
    _seed_visibility()
    _windowed_schema, lateral_schema = _visibility_schemas()
    query = "{ shelves { id code booksConnection(first: 10) { edges { node { title } } totalCount } } }"
    with CaptureQueriesContext(db_connection) as captured:
        result = lateral_schema.execute_sync(query)
    assert result.errors is None, result.errors
    lateral_sql = next(entry["sql"] for entry in captured if "CROSS JOIN LATERAL" in entry["sql"])
    assert lateral_sql.count("circulation_status") == 1
    by_code = {shelf["code"]: shelf["booksConnection"] for shelf in result.data["shelves"]}
    titles = [edge["node"]["title"] for edge in by_code["A"]["edges"]]
    assert titles == [
        "a0",
        "a1",
        "a2",
        "a3",
    ]  # repair books excluded, in order.
    assert by_code["A"]["totalCount"] == 4


def test_multi_table_visibility_scope_downgrades_off_the_lateral_path():
    """A join-traversal ``get_queryset`` scope is refused - the windowed body runs.

    The refusal boundary at the live tier: a scope filtering through a relation
    (``branch__city``) uses more than the child table, so the spec refuses it
    and the connection serves through the windowed strategy (no lateral SQL) -
    still byte-identical to the standalone windowed run.
    """
    _seed_visibility()

    @classmethod
    def _hide_by_branch(cls, queryset, info):
        return queryset.exclude(shelf__branch__city="restricted")

    make_django_type(
        "MultiTableBookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
        namespace_extra={"get_queryset": _hide_by_branch},
    )
    shelf_type = make_django_type("MultiTableShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    lateral_schema = build_strategy_schema(query_cls, "lateral")
    query = (
        "{ shelves { id code booksConnection(first: 2) { edges { node { title } } totalCount } } }"
    )
    with CaptureQueriesContext(db_connection) as captured:
        result = lateral_schema.execute_sync(query)
    assert result.errors is None, result.errors
    executed_sql = " ".join(entry["sql"] for entry in captured)
    assert "CROSS JOIN LATERAL" not in executed_sql  # multi-table scope refused.
    by_code = {shelf["code"]: shelf["booksConnection"] for shelf in result.data["shelves"]}
    assert by_code["A"]["totalCount"] == 6  # no city is restricted, so all six show.


def _request_varying_visibility_schema():
    """A ``ShelfType.booksConnection`` whose child scope VARIES by request.

    Mirrors the real fakeshop permission idiom (``BookType.get_queryset`` hides
    ``circulation_status="repair"`` from non-staff): an anonymous request gets the
    restrictive predicate, a staff request gets the queryset unchanged. Returns
    ONE lateral schema bound to a SINGLE persistent extension instance
    (``extensions=[lambda: extension]``) so its plan-cache counters report BOTH
    requests rather than resetting per execution.
    """
    from types import SimpleNamespace

    from django_strawberry_framework import DjangoOptimizerExtension, strawberry_config

    @classmethod
    def _scope_by_staff(cls, queryset, info):
        # The real idiom: unwrap info.context -> request -> user -> is_staff.
        context = getattr(info, "context", None)
        request = getattr(context, "request", None) or context
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_staff", False):
            return queryset
        return queryset.exclude(circulation_status="repair")

    make_django_type(
        "ReqVaryBookType",
        Book,
        ("id", "title"),
        meta_extra={"connection": {"total_count": True}},
        namespace_extra={"get_queryset": _scope_by_staff},
    )
    shelf_type = make_django_type("ReqVaryShelfType", Shelf, ("id", "code", "books"))
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    extension = DjangoOptimizerExtension(nested_connection_strategy="lateral")
    schema = strawberry.Schema(
        query=query_cls,
        config=strawberry_config(),
        extensions=[lambda: extension],
    )
    return schema, extension, SimpleNamespace


def test_request_varying_visibility_is_not_cached_across_callers():
    """P2-4: two callers of ONE extension get their OWN visibility WHERE, never a replay.

    The security-critical composition the earlier unconditional tests could not
    pin: a custom ``get_queryset`` marks the plan non-cacheable, so the anonymous
    caller's restrictive predicate must never survive in the plan cache and be
    replayed for a staff caller (or the reverse). Both callers execute real
    lateral SQL through the SAME extension instance; the anonymous branch carries
    the ``circulation_status`` scope and the staff branch does not; their visible
    rows differ; and the extension's plan-cache counters prove the request-varying
    plan was never cached or reused.
    """
    _seed_visibility()  # shelf A: 4 available + 2 repair; shelf B empty.
    schema, extension, namespace = _request_varying_visibility_schema()
    query = (
        "{ shelves { id code booksConnection(first: 10) "
        "{ edges { node { title } } totalCount } } }"
    )

    def _context(*, is_staff):
        return namespace(request=namespace(user=namespace(is_staff=is_staff)))

    with CaptureQueriesContext(db_connection) as anon_captured:
        anon = schema.execute_sync(query, context_value=_context(is_staff=False))
    assert anon.errors is None, anon.errors
    with CaptureQueriesContext(db_connection) as staff_captured:
        staff = schema.execute_sync(query, context_value=_context(is_staff=True))
    assert staff.errors is None, staff.errors

    anon_books = {s["code"]: s["booksConnection"] for s in anon.data["shelves"]}
    staff_books = {s["code"]: s["booksConnection"] for s in staff.data["shelves"]}
    # The two callers see DIFFERENT rows - each request's scope was applied, not
    # replayed from a cached first-caller plan.
    assert anon_books["A"]["totalCount"] == 4  # repair hidden from anonymous.
    assert staff_books["A"]["totalCount"] == 6  # staff sees all six.
    staff_titles = {edge["node"]["title"] for edge in staff_books["A"]["edges"]}
    anon_titles = {edge["node"]["title"] for edge in anon_books["A"]["edges"]}
    assert staff_titles - anon_titles == {"r0", "r1"}  # the two repair books.

    anon_sql = " ".join(entry["sql"] for entry in anon_captured)
    staff_sql = " ".join(entry["sql"] for entry in staff_captured)
    # Both take the lateral path; only the anonymous branch splices the scope.
    assert "CROSS JOIN LATERAL" in anon_sql
    assert "CROSS JOIN LATERAL" in staff_sql
    assert "circulation_status" in anon_sql
    assert "circulation_status" not in staff_sql

    # The plan is request-scoped (custom get_queryset -> non-cacheable): it never
    # enters the cross-request cache, so no caller can be served another's plan.
    info = extension.cache_info()
    assert info.hits == 0
    assert info.size == 0
    assert info.misses >= 2


# =============================================================================
# Keyset (Meta.cursor_field) parity + the lateral index-seek pin
# =============================================================================


def _keyset_schemas(cursor_field=("-number", "id")):
    """Periodical -> issuesConnection graph with a KEYSET child type.

    ``cursor_field`` parameterizes the seek arm: the mixed-direction default
    exercises the redundant-bound OR-expansion; a uniform ``("number", "id")``
    exercises the native row-value comparison.
    """
    from apps.library.models import Issue, Periodical

    make_django_type(
        "KeysetIssueType",
        Issue,
        ("id", "number", "title"),
        meta_extra={"cursor_field": cursor_field, "connection": {"total_count": True}},
    )
    periodical_type = make_django_type(
        "KeysetPeriodicalType",
        Periodical,
        ("id", "name", "issues"),
        meta_extra={"relation_shapes": {"issues": "connection"}},
    )

    import strawberry

    @strawberry.type
    class Query:
        periodicals: list[periodical_type] = DjangoListField(periodical_type)

    finalize_django_types()
    return (build_strategy_schema(Query, "windowed"), build_strategy_schema(Query, "lateral"))


def _seed_periodicals():
    from apps.library.models import Issue, Periodical

    populated = Periodical.objects.create(name="populated")
    sparse = Periodical.objects.create(name="sparse")
    Periodical.objects.create(name="empty")
    issues = [
        Issue.objects.create(periodical=populated, number=number, title=f"p{number}")
        for number in range(1, 6)
    ]
    for number in range(1, 4):
        Issue.objects.create(periodical=sparse, number=number, title=f"s{number}")
    return issues


def _mint_issue_cursor(issue, cursor_field=("-number", "id")):
    from apps.library.models import Issue

    from django_strawberry_framework.keyset import (
        cursor_columns_for,
        encode_keyset_cursor,
        order_fingerprint,
    )

    return encode_keyset_cursor(
        cursor_columns_for(Issue, cursor_field),
        issue,
        fingerprint=order_fingerprint(cursor_field),
    )


def _assert_keyset_parity(query, *, cursor_field=("-number", "id"), expect_lateral=True):
    """The keyset twin of ``_assert_parity`` (its own type graph per call)."""
    windowed_schema, lateral_schema = _keyset_schemas(cursor_field)
    windowed = windowed_schema.execute_sync(query)
    assert windowed.errors is None, windowed.errors
    with CaptureQueriesContext(db_connection) as captured:
        lateral = lateral_schema.execute_sync(query)
    assert lateral.errors is None, lateral.errors
    assert _canonical(lateral.data) == _canonical(windowed.data)
    assert len(captured) == 2
    executed_sql = " ".join(entry["sql"] for entry in captured)
    if expect_lateral:
        assert "CROSS JOIN LATERAL" in executed_sql
    else:
        assert "CROSS JOIN LATERAL" not in executed_sql
    return lateral.data, captured


_KEYSET_PROBE_PAGE = "edges { cursor node { title } } pageInfo { hasNextPage hasPreviousPage }"
_KEYSET_FULL_PAGE = (
    "edges { cursor node { title } } totalCount pageInfo { hasNextPage hasPreviousPage endCursor }"
)


def test_keyset_count_free_seek_runs_in_branch_on_postgres():
    """The O(page) headline: the seek + ORDER BY + LIMIT inside the lateral branch."""
    issues = _seed_periodicals()
    cursor = _mint_issue_cursor(issues[3])  # p4 under (-number, id)
    data, captured = _assert_keyset_parity(
        f'{{ periodicals {{ id issuesConnection(first: 2, after: "{cursor}") '
        f"{{ {_KEYSET_PROBE_PAGE} }} }} }}",
    )
    lateral_sql = next(sql for sql in (e["sql"] for e in captured) if "LATERAL" in sql)
    # The seek predicate landed INSIDE the branch (count-free shape), with the
    # in-branch LIMIT - not an outer row-number filter.
    assert "_dst_total_count" not in lateral_sql
    assert "LIMIT" in lateral_sql
    by_name = {parent["id"]: parent["issuesConnection"] for parent in data["periodicals"]}
    pages = {
        tuple(edge["node"]["title"] for edge in connection_data["edges"])
        for connection_data in by_name.values()
    }
    # populated continues past p4; sparse re-positions by VALUE (numbers < 4).
    assert ("p3", "p2") in pages
    assert ("s3", "s2") in pages
    assert () in pages  # the childless periodical


def test_keyset_uniform_direction_uses_row_value_seek():
    """Uniform directions emit the native row-value comparison on Postgres."""
    issues = _seed_periodicals()
    cursor = _mint_issue_cursor(issues[1], ("number", "id"))
    _data, captured = _assert_keyset_parity(
        f'{{ periodicals {{ id issuesConnection(first: 2, after: "{cursor}") '
        f"{{ {_KEYSET_PROBE_PAGE} }} }} }}",
        cursor_field=("number", "id"),
    )
    lateral_sql = next(sql for sql in (e["sql"] for e in captured) if "LATERAL" in sql)
    assert ") > (" in lateral_sql  # the row-value tuple comparison


def test_keyset_counted_seek_downgrades_to_windowed_with_pre_seek_totals():
    """totalCount + after: the lateral strategy runs the qualify-wrapped window."""
    issues = _seed_periodicals()
    cursor = _mint_issue_cursor(issues[3])
    data, captured = _assert_keyset_parity(
        f'{{ periodicals {{ id issuesConnection(first: 2, after: "{cursor}") '
        f"{{ {_KEYSET_FULL_PAGE} }} }} }}",
        expect_lateral=False,
    )
    executed_sql = " ".join(entry["sql"] for entry in captured)
    assert "FILTER (WHERE" in executed_sql  # the page-relative filtered count
    totals = {parent["issuesConnection"]["totalCount"] for parent in data["periodicals"]}
    assert totals == {5, 3, 0}  # PRE-seek partition counts


def test_keyset_first_page_full_shape_parity():
    """The cursor-less keyset first page stays on the shipped lateral shapes."""
    _seed_periodicals()
    data, _ = _assert_keyset_parity(
        f"{{ periodicals {{ id issuesConnection(first: 2) {{ {_KEYSET_FULL_PAGE} }} }} }}",
    )
    for parent in data["periodicals"]:
        connection_data = parent["issuesConnection"]
        for edge in connection_data["edges"]:
            # Keyset first pages mint VALUE cursors (the dstcursor prefix),
            # never positional offsets.
            import base64

            decoded = base64.b64decode(edge["cursor"]).decode()
            assert decoded.startswith("dstcursor:")


@pytest.mark.parametrize(
    (
        "cursor_field",
        "cursor_rank",
        "expected_labels",
        "sql_fragment",
    ),
    [
        (
            ("payload", "id"),
            1,
            ["child-2", "child-3"],
            ") > (",
        ),
        (
            ("-payload", "id"),
            3,
            ["child-2", "child-1"],
            '"payload" <= ',
        ),
    ],
)
def test_keyset_json_seek_uses_field_adapter_on_postgres(
    cursor_field,
    cursor_rank,
    expected_labels,
    sql_fragment,
):
    """Internal JSONB seek values are field-prepared before raw lateral execution.

    JSONField is deliberately rejected at the public cursor-field and runtime
    orderBy validation gates because its ordering is not backend-portable.
    This direct internal carrier still pins the raw SQL adapter boundary so a
    future custom field with structured prepared values cannot bypass Django.
    """
    import datetime
    import uuid

    from apps.scalars.models import ScalarSpecimen
    from django.db.models import Prefetch
    from django.utils import timezone

    from django_strawberry_framework.keyset import KeysetCursor, KeysetSeek, cursor_columns_for
    from django_strawberry_framework.optimizer.join_taxonomy import classify_relation_join
    from django_strawberry_framework.optimizer.lateral_fetch import LATERAL_STRATEGY
    from django_strawberry_framework.optimizer.nested_fetch import NestedConnectionRequest
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    def create_specimen(label, payload, *, parent=None):
        return ScalarSpecimen.objects.create(
            label=label,
            occurred_on=datetime.date(2026, 1, 1),
            occurred_at=timezone.now(),
            occurred_time=datetime.time(12, 0),
            payload=payload,
            external_id=uuid.uuid4(),
            parent=parent,
        )

    parent = create_specimen("parent", {"rank": 0})
    children = {
        rank: create_specimen(f"child-{rank}", {"rank": rank}, parent=parent)
        for rank in range(1, 4)
    }
    columns = cursor_columns_for(ScalarSpecimen, cursor_field)
    seek = KeysetSeek(
        columns=columns,
        cursor=KeysetCursor(
            values=(children[cursor_rank].payload, children[cursor_rank].pk),
        ),
    )
    field = ScalarSpecimen._meta.get_field("children")
    request = NestedConnectionRequest(
        django_field=field,
        relation_field_name="children",
        prefix="",
        child_queryset=ScalarSpecimen.objects.all(),
        join=classify_relation_join(field),
        order_by=cursor_field,
        offset=0,
        limit=2,
        reverse=False,
        with_total_count=False,
        next_page_probe=True,
        keyset_seek=seek,
        to_attr="_dst_children_connection",
        lookup="children",
    )
    plan = OptimizationPlan()
    assert LATERAL_STRATEGY.plan(request, plan)
    (planned_prefetch,) = plan.prefetch_related
    assert isinstance(planned_prefetch, Prefetch)
    with CaptureQueriesContext(db_connection) as captured:
        loaded = ScalarSpecimen.objects.prefetch_related(planned_prefetch).get(pk=parent.pk)
    lateral_sql = next(entry["sql"] for entry in captured if "CROSS JOIN LATERAL" in entry["sql"])
    assert sql_fragment in lateral_sql
    assert [row.label for row in loaded._dst_children_connection] == expected_labels
    assert all(isinstance(row.payload, dict) for row in loaded._dst_children_connection)


@pytest.mark.django_db(transaction=True)
def test_lateral_custom_through_joins_the_foreign_key_target_column():
    """A through FK targeting a unique non-PK child column must not join the child PK."""
    from django.db import models

    from django_strawberry_framework.optimizer.join_taxonomy import classify_relation_join
    from django_strawberry_framework.optimizer.lateral_fetch import LATERAL_STRATEGY
    from django_strawberry_framework.optimizer.nested_fetch import NestedConnectionRequest
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    class NaturalChild(models.Model):
        code = models.TextField(unique=True)
        rank = models.IntegerField()

        class Meta:
            app_label = "library"
            managed = False
            db_table = "lateral_natural_child"

    class NaturalParent(models.Model):
        name = models.TextField()
        children = models.ManyToManyField(
            NaturalChild,
            through="NaturalMembership",
            related_name="natural_parents",
        )

        class Meta:
            app_label = "library"
            managed = False
            db_table = "lateral_natural_parent"

    class NaturalMembership(models.Model):
        parent = models.ForeignKey(NaturalParent, on_delete=models.CASCADE)
        child = models.ForeignKey(
            NaturalChild,
            db_column="child_code",
            on_delete=models.CASCADE,
            to_field="code",
        )

        class Meta:
            app_label = "library"
            managed = False
            db_table = "lateral_natural_membership"

    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(NaturalChild)
        schema_editor.create_model(NaturalParent)
        schema_editor.create_model(NaturalMembership)
    try:
        parent = NaturalParent.objects.create(name="parent")
        children = [
            NaturalChild.objects.create(code=f"code-{rank}", rank=rank) for rank in range(3)
        ]
        NaturalMembership.objects.bulk_create(
            [NaturalMembership(parent=parent, child=child) for child in children],
        )
        field = NaturalParent._meta.get_field("children")
        request = NestedConnectionRequest(
            django_field=field,
            relation_field_name="children",
            prefix="",
            child_queryset=NaturalChild.objects.all(),
            join=classify_relation_join(field),
            order_by=("rank", "id"),
            offset=0,
            limit=2,
            reverse=False,
            with_total_count=False,
            next_page_probe=False,
            keyset_seek=None,
            to_attr="_dst_children_connection",
            lookup="children",
        )
        plan = OptimizationPlan()
        assert LATERAL_STRATEGY.plan(request, plan)
        (planned_prefetch,) = plan.prefetch_related
        with CaptureQueriesContext(db_connection) as captured:
            loaded = NaturalParent.objects.prefetch_related(planned_prefetch).get(pk=parent.pk)
        lateral_sql = next(
            entry["sql"] for entry in captured if "CROSS JOIN LATERAL" in entry["sql"]
        )
        assert '"__dst_child"."code" = "__dst_through"."child_code"' in lateral_sql
        assert [row.code for row in loaded._dst_children_connection] == ["code-0", "code-1"]
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(NaturalMembership)
            schema_editor.delete_model(NaturalParent)
            schema_editor.delete_model(NaturalChild)


@pytest.mark.django_db(transaction=True)
def test_keyset_lateral_seek_is_an_index_seek():
    """EXPLAIN pin: with the composite ``(cursor columns..., pk)`` index present,
    the count-free lateral branch seeks the index instead of scanning.

    ``enable_seqscan`` is forced off for the EXPLAIN so the planner's
    small-table seq-scan preference cannot mask index-usability; the pin is
    "the seek CAN use the index", not a cost-model assertion.
    """
    from apps.library.models import Issue

    from django_strawberry_framework.keyset import KeysetCursor, KeysetSeek, cursor_columns_for
    from django_strawberry_framework.optimizer.join_taxonomy import classify_relation_join
    from django_strawberry_framework.optimizer.lateral_fetch import build_lateral_sql
    from django_strawberry_framework.optimizer.nested_fetch import NestedConnectionRequest
    from django_strawberry_framework.optimizer.plans import OptimizationPlan

    issues = _seed_periodicals()
    seek = KeysetSeek(
        columns=cursor_columns_for(Issue, ("number", "id")),
        cursor=KeysetCursor(values=(2, issues[1].pk)),
    )
    from apps.library.models import Periodical

    field = Periodical._meta.get_field("issues")
    request = NestedConnectionRequest(
        django_field=field,
        relation_field_name="issues",
        prefix="",
        child_queryset=Issue.objects.all(),
        join=classify_relation_join(field),
        order_by=("number", "id"),
        offset=0,
        limit=2,
        reverse=False,
        with_total_count=False,
        next_page_probe=True,
        keyset_seek=seek,
        to_attr="_dst_issues_connection",
        lookup="issues",
    )
    plan = OptimizationPlan()
    from django_strawberry_framework.optimizer.lateral_fetch import LATERAL_STRATEGY

    assert LATERAL_STRATEGY.plan(request, plan)
    spec = plan.prefetch_related[0].queryset._dst_lateral_spec
    parent_ids = list(Periodical.objects.values_list("pk", flat=True))
    sql, params = build_lateral_sql(
        spec,
        parent_ids,
        quote_name=db_connection.ops.quote_name,
        parent_cast=spec.parent_link_field.db_type(db_connection),
    )
    with db_connection.cursor() as cursor:
        cursor.execute(
            "CREATE INDEX keyset_seek_pin_idx ON library_issue (periodical_id, number, id)",
        )
        cursor.execute("SET enable_seqscan = off")
        try:
            cursor.execute(f"EXPLAIN {sql}", params)
            explain_plan = " ".join(row[0] for row in cursor.fetchall())
        finally:
            cursor.execute("SET enable_seqscan = on")
            cursor.execute("DROP INDEX keyset_seek_pin_idx")
    assert "keyset_seek_pin_idx" in explain_plan
    assert "Index" in explain_plan


def _hinted_shelf_schema(default_strategy, books_hint):
    """One schema whose ``ShelfType.books`` connection carries a strategy hint.

    The extension default is ``default_strategy``; ``books_hint`` overrides the
    fetch strategy for the ``booksConnection`` field alone
    (``OptimizerHint.strategy(...)`` keyed on the ``"books"`` relation name).
    """
    _make_type("BookType", Book, ("id", "title"))
    shelf_type = make_django_type(
        "ShelfType",
        Shelf,
        ("id", "code", "books"),
        meta_extra={"optimizer_hints": {"books": books_hint}},
    )
    finalize_django_types()
    query_cls = strawberry.type(
        type(
            "Query",
            (),
            {
                "__annotations__": {"shelves": list[shelf_type]},
                "shelves": DjangoListField(shelf_type),
            },
        ),
    )
    return build_strategy_schema(query_cls, default_strategy)


_HINT_QUERY = "{ shelves { id code booksConnection(first: 2) { edges { node { title } } } } }"


def _shelf_a_titles(data):
    """The ``booksConnection`` node titles for shelf ``A`` (the five-book parent)."""
    by_code = {shelf["code"]: shelf["booksConnection"] for shelf in data["shelves"]}
    return [edge["node"]["title"] for edge in by_code["A"]["edges"]]


def test_per_field_hint_windowed_under_lateral_default_takes_windowed_path():
    """``OptimizerHint.strategy("windowed")`` overrides a lateral-default extension.

    The hinted ``booksConnection`` must fetch through the windowed body, so the
    executed SQL carries NO ``CROSS JOIN LATERAL`` even though the extension
    default is ``"lateral"`` - and the page is still correct.
    """
    _seed_library()
    schema = _hinted_shelf_schema("lateral", OptimizerHint.strategy("windowed"))
    with CaptureQueriesContext(db_connection) as captured:
        result = schema.execute_sync(_HINT_QUERY)
    assert result.errors is None, result.errors
    executed_sql = " ".join(entry["sql"] for entry in captured)
    assert "CROSS JOIN LATERAL" not in executed_sql
    assert _shelf_a_titles(result.data) == ["a0", "a1"]


def test_per_field_hint_lateral_under_windowed_default_takes_lateral_path():
    """``OptimizerHint.strategy("lateral")`` overrides a windowed-default extension.

    The hinted ``booksConnection`` must fetch through the lateral join, so the
    executed SQL carries ``CROSS JOIN LATERAL`` even though the extension default
    is ``"windowed"`` - and the page is still correct.
    """
    _seed_library()
    schema = _hinted_shelf_schema("windowed", OptimizerHint.strategy("lateral"))
    with CaptureQueriesContext(db_connection) as captured:
        result = schema.execute_sync(_HINT_QUERY)
    assert result.errors is None, result.errors
    executed_sql = " ".join(entry["sql"] for entry in captured)
    assert "CROSS JOIN LATERAL" in executed_sql
    assert _shelf_a_titles(result.data) == ["a0", "a1"]


# =============================================================================
# Single-parent degenerate fast path parity (optimizer/single_parent_fetch.py)
# =============================================================================


def test_single_parent_fast_path_pages_identically_to_lateral():
    """The windowed single-parent fast path pages byte-identically to lateral.

    With exactly one seeded shelf the Django-prefetch-injected parent ``IN`` list
    has length one, so under the windowed strategy
    ``WindowedPrefetchStrategy.plan``'s runtime wrap swaps in the plain filtered
    ``LIMIT`` fast path (``optimizer/single_parent_fetch.py``) instead of the
    ``ROW_NUMBER() OVER (PARTITION BY fk)`` body. That fast-path run must return
    rows / cursors / ``pageInfo`` byte-identical to the lateral strategy's output
    for the same count-free page - the same parity bar every shape here holds.

    Under ``strategy=lateral`` the fast path never engages (the wrap is
    windowed-branch-only), so the lateral half executes real ``CROSS JOIN
    LATERAL`` SQL and stands as the parity oracle.
    """
    branch = Branch.objects.create(name="central")
    shelf = Shelf.objects.create(code="A", branch=branch)
    for index in range(5):
        Book.objects.create(title=f"a{index}", shelf=shelf)
    data, _ = _assert_parity(
        f"{{ shelves {{ id booksConnection(first: 2) {{ {_CHEAP_PAGE} }} }} }}",
        count_free=True,
    )
    # The single seeded parent is what drives the len==1 IN list the fast path
    # keys on; shelf A carries five books so ``first: 2`` is a real bounded page.
    assert len(data["shelves"]) == 1
