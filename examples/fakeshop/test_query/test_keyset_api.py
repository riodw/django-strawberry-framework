"""Live GraphQL HTTP tests for keyset (``Meta.cursor_field``) cursor pagination.

The acceptance surface for the ``stable_cursor_field`` contract over the
library app's ``IssueType`` (``cursor_field = ("-number", "id")`` - the
newest-first mixed-direction shape) and ``PeriodicalType.issuesConnection``
(the nested windowed keyset seek):

- value cursors round-trip (``endCursor`` -> ``after:``) and SURVIVE inserts
  and deletes before the cursor - the motivating fix for offset-cursor drift;
- ``totalCount`` stays the PRE-seek partition count on every ``after:`` page;
- nested seeks apply UNIFORM VALUE-POSITION semantics across every parent
  partition, and the batched window stays one prefetch query;
- tampered, foreign-order, and offset (``arrayconnection``) cursors are
  rejected with the uniform invalid-cursor error;
- cursors are permission-aware by construction: a staff-minted cursor
  replays for an anonymous viewer over only the rows that viewer can see.

Cursors are always MINTED then round-tripped - never pinned as literals -
because the payload is authenticated-encrypted opaque bytes (the codec contract).
"""

import pytest
from apps.library import models
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from graphql_client import assert_graphql_success as _assert_graphql_success
from graphql_client import post_graphql as _post_graphql
from strawberry.relay.utils import to_base64

from django_strawberry_framework.testing import TestClient


def _seed_periodicals():
    """Two populated periodicals plus one empty; issue numbers repeat across them.

    Under the declared ``("-number", "id")`` order the root connection
    interleaves: astro#5, astro#4, astro#3, bot#3, astro#2, bot#2, astro#1,
    bot#1 (equal numbers tie-break on ascending pk - astronomy rows were
    created first).
    """
    astronomy = models.Periodical.objects.create(name="Astronomy Weekly")
    botany = models.Periodical.objects.create(name="Botany Monthly")
    empty = models.Periodical.objects.create(name="Empty Gazette")
    for number in range(1, 6):
        models.Issue.objects.create(periodical=astronomy, number=number, title=f"Astro #{number}")
    for number in range(1, 4):
        models.Issue.objects.create(periodical=botany, number=number, title=f"Bot #{number}")
    return astronomy, botany, empty


ROOT_PAGE_QUERY = """
query ($first: Int, $last: Int, $after: String, $before: String) {
  allLibraryIssuesConnection(first: $first, last: $last, after: $after, before: $before) {
    totalCount
    pageInfo { hasNextPage hasPreviousPage startCursor endCursor }
    edges { cursor node { title number } }
  }
}
"""


def _root_page(**variables):
    data = _assert_graphql_success(ROOT_PAGE_QUERY, variables=variables)
    return data["allLibraryIssuesConnection"]


def _titles(connection_payload):
    return [edge["node"]["title"] for edge in connection_payload["edges"]]


@pytest.mark.django_db
def test_root_keyset_first_page_orders_by_cursor_field():
    """The declared ``cursor_field`` IS the connection's default order (newest-first)."""
    _seed_periodicals()
    page = _root_page(first=3)
    assert _titles(page) == ["Astro #5", "Astro #4", "Astro #3"]
    assert page["totalCount"] == 8
    assert page["pageInfo"]["hasNextPage"] is True
    assert page["pageInfo"]["hasPreviousPage"] is False
    assert page["pageInfo"]["startCursor"] == page["edges"][0]["cursor"]
    assert page["pageInfo"]["endCursor"] == page["edges"][-1]["cursor"]


@pytest.mark.django_db
def test_root_keyset_round_trip_and_pre_seek_total_count():
    """``endCursor`` -> ``after:`` continues exactly; ``totalCount`` stays pre-seek."""
    _seed_periodicals()
    first_page = _root_page(first=3)
    second_page = _root_page(first=3, after=first_page["pageInfo"]["endCursor"])
    assert _titles(second_page) == ["Bot #3", "Astro #2", "Bot #2"]
    assert second_page["totalCount"] == 8  # the pre-pagination set, not the post-seek tail
    assert second_page["pageInfo"]["hasPreviousPage"] is True
    assert second_page["pageInfo"]["hasNextPage"] is True
    third_page = _root_page(first=3, after=second_page["pageInfo"]["endCursor"])
    assert _titles(third_page) == ["Astro #1", "Bot #1"]
    assert third_page["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
def test_root_keyset_page_survives_inserts_and_deletes_before_cursor():
    """The motivating stability pin: mutations before the cursor cannot drift the page."""
    astronomy, _botany, _empty = _seed_periodicals()
    cursor = _root_page(first=3)["pageInfo"]["endCursor"]
    baseline = _titles(_root_page(first=3, after=cursor))

    # Insert a row that sorts BEFORE the cursor position (number 9 > 5 sorts
    # first under -number) and delete one from before it too - an offset
    # cursor would shift by one in each direction; the value cursor cannot.
    models.Issue.objects.create(periodical=astronomy, number=9, title="Astro #9")
    models.Issue.objects.get(title="Astro #5").delete()
    assert _titles(_root_page(first=3, after=cursor)) == baseline


@pytest.mark.django_db
def test_root_keyset_rejects_tampered_and_offset_cursors():
    """Tampered bytes and offset-vocabulary cursors both get the uniform rejection."""
    _seed_periodicals()
    cursor = _root_page(first=1)["pageInfo"]["endCursor"]
    for bad_cursor in (cursor[:-8] + "AAAAAAAA", to_base64("arrayconnection", 2)):
        response = _post_graphql(ROOT_PAGE_QUERY, variables={"first": 1, "after": bad_cursor})
        assert response.status_code == 200
        payload = response.json()
        assert "errors" in payload, payload
        assert "invalid cursor" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_root_keyset_backward_pagination():
    """``last:`` and ``last:``+``before:`` page backward through the value order."""
    _seed_periodicals()
    tail = _root_page(last=2)
    assert _titles(tail) == ["Astro #1", "Bot #1"]
    assert tail["pageInfo"]["hasPreviousPage"] is True
    assert tail["pageInfo"]["hasNextPage"] is False
    previous = _root_page(last=2, before=tail["pageInfo"]["startCursor"])
    assert _titles(previous) == ["Astro #2", "Bot #2"]
    assert previous["pageInfo"]["hasPreviousPage"] is True
    assert previous["pageInfo"]["hasNextPage"] is True
    # Walk all the way back: the head page reports no previous rows.
    head = previous
    while head["pageInfo"]["hasPreviousPage"]:
        head = _root_page(last=2, before=head["pageInfo"]["startCursor"])
    assert _titles(head) == ["Astro #5"] or _titles(head) == ["Astro #5", "Astro #4"]
    assert head["pageInfo"]["hasPreviousPage"] is False


@pytest.mark.django_db
def test_root_keyset_last_zero_preserves_shipped_connection_semantics():
    """The keyset opt-in changes cursor vocabulary, not Strawberry's ``last: 0`` quirk."""
    _seed_periodicals()
    page = _root_page(last=0)
    assert len(page["edges"]) == 8
    assert page["pageInfo"]["hasPreviousPage"] is False
    assert page["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
def test_root_keyset_first_and_last_guard_still_applies():
    """The package's first+last mutual-exclusivity guard precedes any slicing."""
    _seed_periodicals()
    response = _post_graphql(ROOT_PAGE_QUERY, variables={"first": 1, "last": 1})
    payload = response.json()
    assert "errors" in payload
    assert "mutually exclusive" in payload["errors"][0]["message"]


ROOT_ORDERED_QUERY = """
query ($first: Int, $after: String) {
  allLibraryIssuesConnection(first: $first, after: $after, orderBy: [{ title: ASC }]) {
    pageInfo { endCursor }
    edges { node { title } }
  }
}
"""


@pytest.mark.django_db
def test_root_keyset_order_by_mints_order_fingerprinted_cursors():
    """An ``orderBy:`` page mints cursors bound to THAT order; replay elsewhere is rejected."""
    _seed_periodicals()
    data = _assert_graphql_success(ROOT_ORDERED_QUERY, variables={"first": 2})
    ordered = data["allLibraryIssuesConnection"]
    assert [e["node"]["title"] for e in ordered["edges"]] == ["Astro #1", "Astro #2"]
    ordered_cursor = ordered["pageInfo"]["endCursor"]

    # Same order: the cursor seeks the next title page.
    data = _assert_graphql_success(
        ROOT_ORDERED_QUERY,
        variables={"first": 2, "after": ordered_cursor},
    )
    assert [e["node"]["title"] for e in data["allLibraryIssuesConnection"]["edges"]] == [
        "Astro #3",
        "Astro #4",
    ]

    # Default order: the fingerprint mismatch rejects the replay.
    response = _post_graphql(ROOT_PAGE_QUERY, variables={"first": 2, "after": ordered_cursor})
    payload = response.json()
    assert "errors" in payload
    assert "invalid cursor" in payload["errors"][0]["message"]


NESTED_QUERY = """
query ($first: Int, $after: String) {
  allLibraryPeriodicalsConnection(first: 10) {
    edges { node { name issuesConnection(first: $first, after: $after) {
      totalCount
      pageInfo { hasNextPage hasPreviousPage endCursor }
      edges { cursor node { title number } }
    } } }
  }
}
"""


def _nested_by_periodical(**variables):
    data = _assert_graphql_success(NESTED_QUERY, variables=variables)
    return {
        edge["node"]["name"]: edge["node"]["issuesConnection"]
        for edge in data["allLibraryPeriodicalsConnection"]["edges"]
    }


@pytest.mark.django_db
def test_nested_keyset_window_is_one_batched_query():
    """The counted keyset window stays a single batched prefetch (no per-parent N+1)."""
    _seed_periodicals()
    with CaptureQueriesContext(connection) as ctx:
        by_name = _nested_by_periodical(first=2)
    # parents + ONE window prefetch (plus any session/auth noise Django adds -
    # pin the exact absence of per-parent issue queries instead of a raw count).
    issue_queries = [q["sql"] for q in ctx.captured_queries if "library_issue" in q["sql"]]
    assert len(issue_queries) == 1, issue_queries
    assert by_name["Astronomy Weekly"]["totalCount"] == 5
    assert _titles(by_name["Astronomy Weekly"]) == ["Astro #5", "Astro #4"]
    assert by_name["Botany Monthly"]["totalCount"] == 3
    assert by_name["Empty Gazette"]["totalCount"] == 0
    assert by_name["Empty Gazette"]["edges"] == []


@pytest.mark.django_db
def test_nested_keyset_after_uniform_value_position_and_pre_seek_totals():
    """One ``after:`` cursor re-positions EVERY partition by value; totals stay pre-seek."""
    _seed_periodicals()
    astro_cursor = _nested_by_periodical(first=2)["Astronomy Weekly"]["pageInfo"]["endCursor"]
    with CaptureQueriesContext(connection) as ctx:
        by_name = _nested_by_periodical(first=2, after=astro_cursor)
    issue_queries = [q["sql"] for q in ctx.captured_queries if "library_issue" in q["sql"]]
    assert len(issue_queries) == 1, issue_queries

    # Cursor sits at astro#4: astronomy continues #3, #2; botany's rows past
    # the VALUE position (number < 4) are #3, #2 - the uniform semantics.
    astronomy = by_name["Astronomy Weekly"]
    assert _titles(astronomy) == ["Astro #3", "Astro #2"]
    assert astronomy["totalCount"] == 5  # PRE-seek partition count
    assert astronomy["pageInfo"]["hasPreviousPage"] is True
    assert astronomy["pageInfo"]["hasNextPage"] is True
    botany = by_name["Botany Monthly"]
    assert _titles(botany) == ["Bot #3", "Bot #2"]
    assert botany["totalCount"] == 3
    # Childless parent with a cursor: empty page, hasPrev from the cursor.
    empty = by_name["Empty Gazette"]
    assert empty["edges"] == [] and empty["totalCount"] == 0
    assert empty["pageInfo"]["hasPreviousPage"] is True
    assert empty["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
def test_nested_keyset_marker_distinguishes_pre_cursor_only_parents():
    """A parent whose rows ALL precede the cursor serves an empty page with its true count."""
    _seed_periodicals()
    # Cursor past astro#2 (deep page): botany's numbers 3..1 all precede it? No -
    # under (-number, id), "past the cursor" means SMALLER numbers. Take the
    # cursor at astro#1 (the last astronomy row): the only rows past it are
    # bot#1 (number 1, larger pk). Botany keeps a page; give botany a cursor
    # past ALL its rows instead by cursoring at the global tail.
    tail_cursor = _root_page(last=1)["pageInfo"]["startCursor"]  # bot#1, the final row
    by_name = _nested_by_periodical(first=2, after=tail_cursor)
    astronomy = by_name["Astronomy Weekly"]
    assert astronomy["edges"] == []
    assert astronomy["totalCount"] == 5  # the abs-first marker row carried it
    assert astronomy["pageInfo"]["hasNextPage"] is False
    assert astronomy["pageInfo"]["hasPreviousPage"] is True


@pytest.mark.django_db
def test_nested_keyset_count_free_page_uses_probe_not_partition_count():
    """A ``hasNextPage``-only nested page runs count-free (seek in WHERE + n+1 probe)."""
    _seed_periodicals()
    astro_cursor = _nested_by_periodical(first=2)["Astronomy Weekly"]["pageInfo"]["endCursor"]
    query = """
    query ($after: String) {
      allLibraryPeriodicalsConnection(first: 10) {
        edges { node { name issuesConnection(first: 2, after: $after) {
          pageInfo { hasNextPage }
          edges { node { title } }
        } } }
      }
    }
    """
    with CaptureQueriesContext(connection) as ctx:
        data = _assert_graphql_success(query, variables={"after": astro_cursor})
    issue_queries = [q["sql"] for q in ctx.captured_queries if "library_issue" in q["sql"]]
    assert len(issue_queries) == 1, issue_queries
    # Count-free shape: the seek narrows the base WHERE (no FILTER'd running
    # count, no partition COUNT) and the probe sentinel answers hasNextPage.
    assert "FILTER" not in issue_queries[0]
    assert "COUNT" not in issue_queries[0].upper().replace("ROW_NUMBER", "")
    by_name = {
        e["node"]["name"]: e["node"]["issuesConnection"]
        for e in data["allLibraryPeriodicalsConnection"]["edges"]
    }
    assert _titles(by_name["Astronomy Weekly"]) == ["Astro #3", "Astro #2"]
    assert by_name["Astronomy Weekly"]["pageInfo"]["hasNextPage"] is True
    # Botany's post-seek set (numbers < 4) is three rows; the page of two
    # leaves Bot #1 past the sentinel.
    assert by_name["Botany Monthly"]["pageInfo"]["hasNextPage"] is True


@pytest.mark.django_db
def test_nested_keyset_first_zero_serves_flags_from_markers():
    """``first: 0`` with a cursor: empty edges, true pre-seek count, value-domain flags."""
    _seed_periodicals()
    astro_cursor = _nested_by_periodical(first=2)["Astronomy Weekly"]["pageInfo"]["endCursor"]
    by_name = _nested_by_periodical(first=0, after=astro_cursor)
    astronomy = by_name["Astronomy Weekly"]
    assert astronomy["edges"] == []
    assert astronomy["totalCount"] == 5
    assert astronomy["pageInfo"]["hasNextPage"] is True  # rows past the cursor exist
    assert astronomy["pageInfo"]["hasPreviousPage"] is True
    empty = by_name["Empty Gazette"]
    assert empty["totalCount"] == 0
    assert empty["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
def test_nested_keyset_backward_falls_back_per_parent_with_same_cursors():
    """``last:`` nested pages resolve per-parent through the SAME codec (parity)."""
    _seed_periodicals()
    query = """
    {
      allLibraryPeriodicalsConnection(first: 10) {
        edges { node { name issuesConnection(last: 2) {
          pageInfo { hasPreviousPage hasNextPage endCursor }
          edges { cursor node { title } }
        } } }
      }
    }
    """
    data = _assert_graphql_success(query)
    by_name = {
        e["node"]["name"]: e["node"]["issuesConnection"]
        for e in data["allLibraryPeriodicalsConnection"]["edges"]
    }
    astronomy = by_name["Astronomy Weekly"]
    assert _titles(astronomy) == ["Astro #2", "Astro #1"]
    assert astronomy["pageInfo"]["hasPreviousPage"] is True
    assert astronomy["pageInfo"]["hasNextPage"] is False
    # Cross-path parity: a cursor minted by the per-parent fallback replays
    # against the WINDOWED forward path (same codec, same bytes).
    forward = _nested_by_periodical(first=2, after=astronomy["edges"][0]["cursor"])
    assert _titles(forward["Astronomy Weekly"]) == ["Astro #1"]


@pytest.mark.django_db
def test_nested_keyset_divergent_aliases_each_decode_their_own_cursor():
    """Divergent aliased ``after:`` payloads window independently (per-key scheme)."""
    _seed_periodicals()
    first_pages = _nested_by_periodical(first=2)
    astro_cursor = first_pages["Astronomy Weekly"]["pageInfo"]["endCursor"]
    query = """
    query ($c: String!) {
      allLibraryPeriodicalsConnection(first: 10) {
        edges { node { name
          head: issuesConnection(first: 2) { edges { node { title } } }
          tail: issuesConnection(first: 2, after: $c) { edges { node { title } } }
        } }
      }
    }
    """
    data = _assert_graphql_success(query, variables={"c": astro_cursor})
    astronomy = next(
        e["node"]
        for e in data["allLibraryPeriodicalsConnection"]["edges"]
        if e["node"]["name"] == "Astronomy Weekly"
    )
    assert [e["node"]["title"] for e in astronomy["head"]["edges"]] == ["Astro #5", "Astro #4"]
    assert [e["node"]["title"] for e in astronomy["tail"]["edges"]] == ["Astro #3", "Astro #2"]


@pytest.mark.django_db
def test_keyset_cursor_decode_is_permission_aware():
    """A staff-minted cursor replays for anonymous viewers over ONLY their rows."""
    astronomy, _botany, _empty = _seed_periodicals()
    models.Issue.objects.create(
        periodical=astronomy,
        number=6,
        title="Embargoed #6",
        embargoed=True,
    )

    user_model = get_user_model()
    staff = user_model.objects.create_user(username="keyset-staff", password="pw", is_staff=True)
    client = TestClient()
    with client.login(staff):
        staff_result = client.query(ROOT_PAGE_QUERY, variables={"first": 2}).response
    staff_page = staff_result.json()["data"]["allLibraryIssuesConnection"]
    # Staff sees the embargoed issue first (number 6 sorts before 5).
    assert _titles(staff_page) == ["Embargoed #6", "Astro #5"]
    assert staff_page["totalCount"] == 9
    staff_cursor = staff_page["pageInfo"]["startCursor"]  # points AT the embargoed row

    # Anonymous replay: the seek applies to the anonymous-visibility queryset -
    # no embargoed row leaks, the count is the viewer's, pagination proceeds.
    anon_page = _root_page(first=3, after=staff_cursor)
    assert _titles(anon_page) == ["Astro #5", "Astro #4", "Astro #3"]
    assert anon_page["totalCount"] == 8
    assert all("Embargoed" not in title for title in _titles(anon_page))


@pytest.mark.django_db
def test_root_keyset_order_by_related_path_seeks_via_annotation():
    """A related-path ``orderBy:`` mints/seeks through the annotated join column."""
    _seed_periodicals()
    query = """
    query ($after: String) {
      allLibraryIssuesConnection(
        first: 3
        after: $after
        orderBy: [{ periodical: { name: ASC } }, { number: ASC }]
      ) {
        pageInfo { endCursor hasNextPage }
        edges { node { title } }
      }
    }
    """
    data = _assert_graphql_success(query)
    page = data["allLibraryIssuesConnection"]
    assert [e["node"]["title"] for e in page["edges"]] == ["Astro #1", "Astro #2", "Astro #3"]
    data = _assert_graphql_success(query, variables={"after": page["pageInfo"]["endCursor"]})
    page2 = data["allLibraryIssuesConnection"]
    assert [e["node"]["title"] for e in page2["edges"]] == ["Astro #4", "Astro #5", "Bot #1"]


@pytest.mark.django_db
def test_root_keyset_unbounded_after_caps_at_relay_max_results():
    """``after:`` with no ``first`` mirrors ``ListConnection``'s max-results cap."""
    _seed_periodicals()
    cursor = _root_page(first=1)["pageInfo"]["endCursor"]
    page = _root_page(after=cursor)
    # relay_max_results (100) far exceeds the seven remaining rows.
    assert len(page["edges"]) == 7
    assert page["pageInfo"]["hasNextPage"] is False
    assert page["pageInfo"]["hasPreviousPage"] is True


@pytest.mark.django_db
def test_nested_keyset_omitted_first_caps_at_relay_max_results():
    """Optimized nested pages apply the same default cap as the root slicer."""
    periodical = models.Periodical.objects.create(name="Large Periodical")
    for number in range(1, 106):
        models.Issue.objects.create(
            periodical=periodical,
            number=number,
            title=f"Issue #{number}",
        )

    first_page = _nested_by_periodical()["Large Periodical"]
    assert len(first_page["edges"]) == 100
    assert first_page["pageInfo"]["hasNextPage"] is True

    cursor = _nested_by_periodical(first=1)["Large Periodical"]["pageInfo"]["endCursor"]
    after_page = _nested_by_periodical(after=cursor)["Large Periodical"]
    assert len(after_page["edges"]) == 100
    assert after_page["pageInfo"]["hasNextPage"] is True
    assert after_page["pageInfo"]["hasPreviousPage"] is True
