"""Live GraphQL HTTP tests for keyset (``Meta.cursor_field``) cursor pagination.

The acceptance surface for the ``stable_cursor_field`` contract over the
library app's ``IssueType`` (``cursor_field = ("-number", "id")`` - the
newest-first mixed-direction shape) and ``PeriodicalType.issuesConnection``
(the nested windowed keyset seek):

- value cursors round-trip (``endCursor`` -> ``after:``) and SURVIVE inserts
  and deletes before the cursor - the motivating fix for offset-cursor drift;
- ``totalCount`` stays the PRE-seek partition count on every ``after:`` page;
- a ``totalCount``-only document counts that set without fetching page rows;
- omitting every pagination argument serves the full set when it is under the
  Relay cap;
- nested seeks apply UNIFORM VALUE-POSITION semantics across every parent
  partition, and the batched window stays one prefetch query;
- tampered, foreign-order, and offset (``arrayconnection``) cursors are
  rejected with the uniform invalid-cursor error;
- minted cursors are deterministic across requests and do not disclose
  ordering values in the clear (AES-SIV authenticated-encrypted payload);
- a cursor outlives a ``SECRET_KEY`` rotation that declares the old key in
  ``SECRET_KEY_FALLBACKS``, and dies with one that does not;
- cursors are permission-aware by construction: a staff-minted cursor
  replays for an anonymous viewer over only the rows that viewer can see;
- the nested window itself is scoped by the target hook the plan applied, so a
  keyset page is partitioned over the viewer's rows and counted on them.

Resolver-contract refusals (a list source, an already-sliced QuerySet) and the
async slicer colour (``acount``, async iteration, deferred cursor columns) ride
a test-local holder: ``/graphql-test/`` (sync ``DjangoGraphQLView``) and
``/graphql-async/`` (``AsyncDjangoGraphQLView``) over shipped ``IssueType``.
Async rows are exempt from ``graphql_client.py`` (sync-only) and use
``AsyncTestClient`` with ``django_db(transaction=True)``.

Cursors are always MINTED then round-tripped - never pinned as literals -
because the payload is authenticated-encrypted opaque bytes (the codec contract).
"""

import base64
from typing import Any

import pytest
import strawberry
from apps.library import models
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches, path
from graphql_client import assert_graphql_success as _assert_graphql_success
from graphql_client import graphql_payload as _graphql_payload
from graphql_client import post_graphql as _post_graphql
from strawberry.relay.utils import from_base64, to_base64

from django_strawberry_framework import DjangoConnectionField, strawberry_config
from django_strawberry_framework.keyset import KEYSET_CURSOR_PREFIX
from django_strawberry_framework.testing import AsyncTestClient, TestClient
from django_strawberry_framework.views import AsyncDjangoGraphQLView, DjangoGraphQLView

_CURRENT: dict[str, Any] = {"schema": None}


def _holder_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


async def _async_holder_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    return await AsyncDjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-test/", _holder_view), path("graphql-async/", _async_holder_view)]


def _issue_holder_schema(resolver):
    from apps.library.schema import IssueType

    @strawberry.type
    class Query:
        issues = DjangoConnectionField(IssueType, resolver=resolver)

    return strawberry.Schema(query=Query, config=strawberry_config())


def _post_holder(schema, query, *, variables=None):
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            return _graphql_payload(query, variables=variables, url="/graphql-test/")
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


async def _post_async_holder(schema, query, *, variables=None):
    _CURRENT["schema"] = schema
    try:
        with override_settings(ROOT_URLCONF=__name__):
            clear_url_caches()
            result = await AsyncTestClient().query(
                query,
                variables=variables,
                assert_no_errors=False,
                url="/graphql-async/",
            )
        assert result.response.status_code == 200, result.response.content
        return result.response.json()
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


def _seed_three_issues():
    periodical = models.Periodical.objects.create(name="Holder Journal")
    for number in (1, 2, 3):
        models.Issue.objects.create(
            periodical=periodical,
            number=number,
            title=f"i{number}",
        )


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
def test_root_keyset_total_count_only_does_not_fetch_edges():
    """A ``totalCount``-only document counts the pre-pagination set and fetches no page rows."""
    _seed_periodicals()
    with CaptureQueriesContext(connection) as ctx:
        data = _assert_graphql_success("{ allLibraryIssuesConnection { totalCount } }")
    assert data["allLibraryIssuesConnection"] == {"totalCount": 8}
    issue_sql = [
        entry["sql"] for entry in ctx.captured_queries if 'FROM "library_issue"' in entry["sql"]
    ]
    assert issue_sql, ctx.captured_queries
    assert all("COUNT(" in sql.upper() for sql in issue_sql), issue_sql
    assert not any("LIMIT" in sql.upper() for sql in issue_sql), issue_sql


@pytest.mark.django_db
def test_root_keyset_cursors_are_deterministic():
    """Identical values under the same order mint identical cursor bytes across requests."""
    _seed_periodicals()
    first = _root_page(first=1)
    second = _root_page(first=1)
    assert first["edges"][0]["cursor"] == second["edges"][0]["cursor"]
    assert first["pageInfo"]["endCursor"] == second["pageInfo"]["endCursor"]


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
@pytest.mark.parametrize("kind", ["tampered", "offset"], ids=["tampered", "offset"])
def test_root_keyset_rejects_tampered_and_offset_cursors(kind):
    """Tampered bytes and offset-vocabulary cursors both get the uniform rejection."""
    _seed_periodicals()
    minted = _root_page(first=1)["pageInfo"]["endCursor"]
    bad_cursor = {
        "tampered": minted[:-8] + "AAAAAAAA",
        "offset": to_base64("arrayconnection", 2),
    }[kind]
    response = _post_graphql(ROOT_PAGE_QUERY, variables={"first": 1, "after": bad_cursor})
    assert response.status_code == 200
    payload = response.json()
    assert "errors" in payload, payload
    assert "invalid cursor" in payload["errors"][0]["message"]
    assert payload["data"] is None, payload


@pytest.mark.django_db
def test_root_keyset_cursor_survives_a_secret_key_rotation_that_keeps_the_fallback():
    """A live cursor keeps working across a ``SECRET_KEY`` rotation that declares the old key.

    Cursors are authenticated-encrypted with the deployment's ``SECRET_KEY``, so a
    rotation would otherwise invalidate every page link a client is holding mid-
    session. The decode consults ``SECRET_KEY_FALLBACKS``, which is what makes a
    rotation a configuration change rather than an outage. The must-not is the
    second half: with the old key dropped from the fallbacks the SAME cursor is
    tamper-equivalent, so the fallback list is a declared trust set, not a
    weakening of the authentication.
    """
    _seed_periodicals()
    original_key = settings.SECRET_KEY
    cursor = _root_page(first=3)["pageInfo"]["endCursor"]

    with override_settings(SECRET_KEY="rotated-live-key", SECRET_KEY_FALLBACKS=[original_key]):
        rotated = _root_page(first=3, after=cursor)
    assert _titles(rotated) == ["Bot #3", "Astro #2", "Bot #2"]

    with override_settings(SECRET_KEY="rotated-live-key", SECRET_KEY_FALLBACKS=[]):
        response = _post_graphql(ROOT_PAGE_QUERY, variables={"first": 3, "after": cursor})

    assert response.status_code == 200
    payload = response.json()
    assert "errors" in payload, payload
    assert payload["data"] is None, payload
    assert "invalid cursor" in payload["errors"][0]["message"], payload


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
def test_root_keyset_last_zero_preserves_bounded_shipped_connection_semantics():
    """``last: 0`` keeps Strawberry's quirk without bypassing the Relay result cap."""
    astronomy, _botany, _empty = _seed_periodicals()
    models.Issue.objects.bulk_create(
        [
            models.Issue(
                periodical=astronomy,
                number=number,
                title=f"Cap probe #{number}",
            )
            for number in range(100, 193)
        ],
    )
    page = _root_page(last=0)
    assert page["totalCount"] == 101
    assert len(page["edges"]) == 100
    assert page["pageInfo"]["hasPreviousPage"] is False
    assert page["pageInfo"]["hasNextPage"] is True


@pytest.mark.django_db
def test_root_keyset_last_zero_with_after_matches_offset_pageinfo():
    """``last: 0`` + ``after:`` serves the after-tail but keeps Strawberry pageInfo.

    Offset ``ListConnection`` materializes ``nodes[after:]`` then takes
    ``edges[-0:]`` (the whole tail) and overwrites ``hasPreviousPage`` from
    "did the ``-last`` trim drop rows?" - always False for ``last == 0``, even
    though ``after`` advanced the window. Keyset must match that pageInfo while
    still seeking in the value domain (the after-tail titles), or offset and
    keyset connections disagree on the same arguments.
    """
    _seed_periodicals()
    first = _root_page(first=2)
    assert _titles(first) == ["Astro #5", "Astro #4"]
    page = _root_page(last=0, after=first["pageInfo"]["endCursor"])
    assert _titles(page) == [
        "Astro #3",
        "Bot #3",
        "Astro #2",
        "Bot #2",
        "Astro #1",
        "Bot #1",
    ]
    assert page["totalCount"] == 8
    assert page["pageInfo"]["hasPreviousPage"] is False
    assert page["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
def test_root_keyset_last_zero_with_after_stays_bounded_by_cap():
    """``last: 0`` + ``after:`` still caps the served tail at ``relay_max_results``.

    The serve-all quirk must never let ``after`` widen the page past the Relay
    cap. With an after-tail well over the default cap of 100, the page is
    trimmed to exactly the cap and ``hasNextPage`` flips True while the quirk
    keeps ``hasPreviousPage`` False.
    """
    astronomy, _botany, _empty = _seed_periodicals()
    models.Issue.objects.bulk_create(
        [
            models.Issue(periodical=astronomy, number=number, title=f"Cap probe #{number}")
            for number in range(100, 250)
        ],
    )
    # Cursor at the very first row: the after-tail is everything else (157
    # rows), far past the cap.
    first = _root_page(first=1)
    page = _root_page(last=0, after=first["pageInfo"]["endCursor"])
    assert len(page["edges"]) == 100  # trimmed to the Relay cap, not the 157-row tail
    assert page["pageInfo"]["hasPreviousPage"] is False  # last:0 serve-all quirk
    assert page["pageInfo"]["hasNextPage"] is True  # the cap trim leaves rows unserved


NESTED_LAST_ZERO_AFTER = """
query ($after: String) {
  allLibraryPeriodicalsConnection(first: 10) {
    edges {
      node {
        name
        issuesConnection(last: 0, after: $after) {
          totalCount
          edges { node { title } }
          pageInfo { hasNextPage hasPreviousPage }
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
def test_nested_keyset_last_zero_with_after_matches_root_pageinfo():
    """Nested ``last: 0`` + ``after:`` (per-parent keyset slicer) keeps the same pageInfo."""
    astronomy, _botany, _empty = _seed_periodicals()
    # Mint a cursor from the nested window's first page, then replay last:0 after it.
    head = _assert_graphql_success(
        """
        query {
          allLibraryPeriodicalsConnection(first: 10) {
            edges {
              node {
                name
                issuesConnection(first: 2) {
                  pageInfo { endCursor }
                  edges { node { title } }
                }
              }
            }
          }
        }
        """,
    )
    astro = next(
        e["node"]
        for e in head["allLibraryPeriodicalsConnection"]["edges"]
        if e["node"]["name"] == astronomy.name
    )
    assert [e["node"]["title"] for e in astro["issuesConnection"]["edges"]] == [
        "Astro #5",
        "Astro #4",
    ]
    after = astro["issuesConnection"]["pageInfo"]["endCursor"]
    data = _assert_graphql_success(NESTED_LAST_ZERO_AFTER, variables={"after": after})
    page = next(
        e["node"]["issuesConnection"]
        for e in data["allLibraryPeriodicalsConnection"]["edges"]
        if e["node"]["name"] == astronomy.name
    )
    assert [e["node"]["title"] for e in page["edges"]] == ["Astro #3", "Astro #2", "Astro #1"]
    assert page["totalCount"] == 5
    assert page["pageInfo"] == {"hasNextPage": False, "hasPreviousPage": False}


@pytest.mark.django_db
def test_root_keyset_first_and_last_guard_still_applies():
    """The package's first+last mutual-exclusivity guard precedes any slicing."""
    _seed_periodicals()
    response = _post_graphql(ROOT_PAGE_QUERY, variables={"first": 1, "last": 1})
    payload = response.json()
    assert "errors" in payload
    assert payload["data"] is None, payload
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
    assert "errors" in payload, payload
    assert "invalid cursor" in payload["errors"][0]["message"]
    assert payload["data"] is None, payload


@pytest.mark.django_db
def test_root_keyset_order_by_literal_string_none_title_round_trips():
    """A real ``title == \"None\"`` row mints and seeks correctly (null is not encoded)."""
    astronomy, _botany, _empty = _seed_periodicals()
    models.Issue.objects.create(periodical=astronomy, number=80, title="None")
    models.Issue.objects.create(periodical=astronomy, number=81, title="None2")
    query = """
    query ($first: Int, $after: String) {
      allLibraryIssuesConnection(
        first: $first, after: $after, orderBy: [{ title: ASC }]
      ) {
        edges { cursor node { title } }
      }
    }
    """
    data = _assert_graphql_success(query, variables={"first": 20})
    edges = data["allLibraryIssuesConnection"]["edges"]
    none_edge = next(e for e in edges if e["node"]["title"] == "None")
    data2 = _assert_graphql_success(
        query,
        variables={"first": 5, "after": none_edge["cursor"]},
    )
    titles = [e["node"]["title"] for e in data2["allLibraryIssuesConnection"]["edges"]]
    assert "None" not in titles
    assert "None2" in titles


@pytest.mark.django_db
def test_root_keyset_cursors_do_not_disclose_ordering_values():
    """An ``orderBy:`` cursor's encrypted payload does not contain the ordering value."""
    astronomy, _botany, _empty = _seed_periodicals()
    sentinel = "cursor-secret-value"
    models.Issue.objects.create(periodical=astronomy, number=80, title=sentinel)
    data = _assert_graphql_success(
        """
        query {
          allLibraryIssuesConnection(first: 20, orderBy: [{ title: ASC }]) {
            edges { cursor node { title } }
          }
        }
        """,
    )
    edge = next(
        e for e in data["allLibraryIssuesConnection"]["edges"] if e["node"]["title"] == sentinel
    )
    prefix, encrypted = from_base64(edge["cursor"])
    assert prefix == KEYSET_CURSOR_PREFIX
    assert sentinel not in encrypted
    assert sentinel.encode() not in base64.urlsafe_b64decode(encrypted)


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
def test_nested_keyset_unselected_cursor_column_is_not_lazy_loaded_per_edge():
    """A node selection omitting the cursor columns still mints cursors in ONE query.

    ``IssueType.cursor_field = ("-number", "id")``. When the node selection does
    NOT select ``number`` (only ``title``), the scalar-only window projection
    would ``.only("title", "id")`` and DEFER ``number`` - so minting each edge's
    value cursor would lazy-load ``number`` once PER edge (an N+1). The already
    -implemented ``_extend_only_projection`` (which killed the strawberry-django
    ``annotate_ordering_fields`` port) folds the cursor columns back into the
    projection, so the whole nested window stays a single batched prefetch with
    zero per-edge lazy loads. Pinned here as live behavior.
    """
    _seed_periodicals()
    query = """
    {
      allLibraryPeriodicalsConnection(first: 10) {
        edges { node { name issuesConnection(first: 3) {
          edges { cursor node { title } }
        } } }
      }
    }
    """
    with CaptureQueriesContext(connection) as ctx:
        data = _assert_graphql_success(query)
    issue_queries = [q["sql"] for q in ctx.captured_queries if "library_issue" in q["sql"]]
    # One batched window prefetch: no per-edge lazy-load of the deferred
    # ``number`` cursor column.
    assert len(issue_queries) == 1, issue_queries
    # Cursors still mint correctly for every edge (the projection carried the
    # cursor columns despite ``number`` not being selected).
    by_name = {
        e["node"]["name"]: e["node"]["issuesConnection"]
        for e in data["allLibraryPeriodicalsConnection"]["edges"]
    }
    astronomy_edges = by_name["Astronomy Weekly"]["edges"]
    assert [e["node"]["title"] for e in astronomy_edges] == ["Astro #5", "Astro #4", "Astro #3"]
    assert all(edge["cursor"] for edge in astronomy_edges)


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


NESTED_BACKWARD_QUERY = """
query ($last: Int, $before: String) {
  allLibraryPeriodicalsConnection(first: 10) {
    edges { node { name issuesConnection(last: $last, before: $before) {
      pageInfo { hasPreviousPage hasNextPage }
      edges { cursor node { title } }
    } } }
  }
}
"""


@pytest.mark.django_db
def test_nested_keyset_before_pages_backward_per_parent():
    """Nested ``before:`` (head + interior) rides the per-parent fallback with root parity.

    Nested ``before:`` is unwindowable, so it falls back to the same
    ``_resolve_keyset_connection`` codec the root uses. Both flags and edges
    must therefore match the root backward contract per parent.
    """
    _seed_periodicals()
    # Mint cursors from a full forward page: order is newest-first, #5..#1.
    forward = _nested_by_periodical(first=5)["Astronomy Weekly"]
    assert _titles(forward) == [
        "Astro #5",
        "Astro #4",
        "Astro #3",
        "Astro #2",
        "Astro #1",
    ]
    cursors = {edge["node"]["title"]: edge["cursor"] for edge in forward["edges"]}

    def _astro(**variables):
        data = _assert_graphql_success(NESTED_BACKWARD_QUERY, variables=variables)
        return next(
            edge["node"]["issuesConnection"]
            for edge in data["allLibraryPeriodicalsConnection"]["edges"]
            if edge["node"]["name"] == "Astronomy Weekly"
        )

    # Interior cursor: the two rows before #2 are #4, #3 (both flags True).
    interior = _astro(last=2, before=cursors["Astro #2"])
    assert _titles(interior) == ["Astro #4", "Astro #3"]
    assert interior["pageInfo"]["hasPreviousPage"] is True
    assert interior["pageInfo"]["hasNextPage"] is True

    # Head cursor: only #5 precedes #4, so the head page reports no previous rows.
    head = _astro(last=2, before=cursors["Astro #4"])
    assert _titles(head) == ["Astro #5"]
    assert head["pageInfo"]["hasPreviousPage"] is False
    assert head["pageInfo"]["hasNextPage"] is True


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
def test_root_keyset_omitted_pagination_returns_the_full_set_under_the_cap():
    """Omitting ``first`` / ``last`` / ``after`` / ``before`` serves every row under the Relay cap."""
    _seed_periodicals()
    data = _assert_graphql_success(
        """
        {
          allLibraryIssuesConnection {
            pageInfo { hasNextPage hasPreviousPage }
            edges { node { title } }
          }
        }
        """,
    )
    page = data["allLibraryIssuesConnection"]
    assert _titles(page) == [
        "Astro #5",
        "Astro #4",
        "Astro #3",
        "Bot #3",
        "Astro #2",
        "Bot #2",
        "Astro #1",
        "Bot #1",
    ]
    assert page["pageInfo"] == {"hasNextPage": False, "hasPreviousPage": False}


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


@pytest.mark.django_db
def test_nested_keyset_window_hides_embargoed_rows_and_counts_them_out():
    """The keyset window is built from the SAME definition that answered the hook.

    ``PeriodicalType.issuesConnection`` is a synthesized relation connection in
    keyset mode: the walker decides whether ``IssueType.get_queryset`` runs over
    the child queryset, then derives the window's cursor vocabulary - columns,
    ordering, fingerprint - from the target's declared ``cursor_field``. Both
    answers come from the child definition the relation was resolved through, so
    a keyset page cannot be partitioned over a population its visibility hook
    never saw.

    The embargoed issue is the newest one in its partition, so under the
    declared newest-first order it would be the FIRST edge of that page and the
    page's ``endCursor`` would point at a row the viewer may not see. It is
    absent, the partition count is the viewer's, and the whole page is still one
    batched query - the planned window, not a per-parent fallback.
    """
    astronomy, _botany, _empty = _seed_periodicals()
    models.Issue.objects.create(
        periodical=astronomy,
        number=6,
        title="Embargoed #6",
        embargoed=True,
    )

    with CaptureQueriesContext(connection) as ctx:
        by_name = _nested_by_periodical(first=2)
    issue_queries = [q["sql"] for q in ctx.captured_queries if 'FROM "library_issue"' in q["sql"]]
    assert len(issue_queries) == 1, issue_queries

    astro = by_name["Astronomy Weekly"]
    assert _titles(astro) == ["Astro #5", "Astro #4"]
    assert astro["totalCount"] == 5
    assert by_name["Botany Monthly"]["totalCount"] == 3


@pytest.mark.django_db
def test_nested_keyset_window_keeps_embargoed_rows_for_staff():
    """The same window returns the embargoed issue first once the viewer is staff.

    The absence above is ``IssueType.get_queryset``'s non-staff branch running
    inside the plan, not the window declining to reach the row: under the declared
    newest-first order the embargoed issue leads its partition here, and the
    partition count is the staff viewer's.
    """
    astronomy, _botany, _empty = _seed_periodicals()
    models.Issue.objects.create(
        periodical=astronomy,
        number=6,
        title="Embargoed #6",
        embargoed=True,
    )
    user_model = get_user_model()
    staff = user_model.objects.create_user(username="nested-staff", password="pw", is_staff=True)
    client = TestClient()
    with client.login(staff):
        with CaptureQueriesContext(connection) as ctx:
            payload = client.query(NESTED_QUERY, variables={"first": 2}).response.json()
    assert payload.get("errors") is None, payload
    by_name = {
        edge["node"]["name"]: edge["node"]["issuesConnection"]
        for edge in payload["data"]["allLibraryPeriodicalsConnection"]["edges"]
    }
    issue_queries = [q["sql"] for q in ctx.captured_queries if 'FROM "library_issue"' in q["sql"]]
    assert len(issue_queries) == 1, issue_queries

    astro = by_name["Astronomy Weekly"]
    assert _titles(astro) == ["Embargoed #6", "Astro #5"]
    assert astro["totalCount"] == 6


_HOLDER_PAGE_QUERY = """
query ($first: Int, $after: String) {
  issues(first: $first, after: $after) {
    totalCount
    pageInfo { hasNextPage endCursor }
    edges { cursor node { title } }
  }
}
"""


@pytest.mark.django_db
def test_keyset_list_source_is_rejected_over_http():
    """A keyset connection resolver that returns a list is refused on the wire."""

    def _list_resolver(root, info):
        return list(models.Issue.objects.all())

    _seed_three_issues()
    payload = _post_holder(
        _issue_holder_schema(_list_resolver),
        "{ issues(first: 1) { edges { cursor } } }",
    )
    assert payload["data"] is None, payload
    assert "errors" in payload, payload
    assert "must return a QuerySet" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_keyset_pre_sliced_source_is_rejected_over_http():
    """A keyset connection resolver that returns an already-sliced QuerySet is refused."""

    def _sliced_resolver(root, info):
        return models.Issue.objects.all()[:5]

    payload = _post_holder(
        _issue_holder_schema(_sliced_resolver),
        "{ issues(first: 1) { edges { cursor } } }",
    )
    assert payload["data"] is None, payload
    assert "errors" in payload, payload
    assert "already-sliced" in payload["errors"][0]["message"]


@pytest.mark.django_db(transaction=True)
async def test_async_keyset_first_page_slices_and_counts():
    """An async keyset field slices the first page through the async engine and ``acount``."""

    async def _async_resolver(root, info):
        return models.Issue.objects.all()

    await sync_to_async(_seed_three_issues)()
    payload = await _post_async_holder(
        _issue_holder_schema(_async_resolver),
        _HOLDER_PAGE_QUERY,
        variables={"first": 2},
    )
    assert payload.get("errors") is None, payload
    page = payload["data"]["issues"]
    assert page["totalCount"] == 3
    assert page["pageInfo"]["hasNextPage"] is True
    assert [edge["node"]["title"] for edge in page["edges"]] == ["i3", "i2"]


@pytest.mark.django_db(transaction=True)
async def test_async_keyset_after_cursor_continues_the_page():
    """A minted async keyset cursor round-trips on the same async field."""

    async def _async_resolver(root, info):
        return models.Issue.objects.all()

    await sync_to_async(_seed_three_issues)()
    schema = _issue_holder_schema(_async_resolver)
    first = await _post_async_holder(schema, _HOLDER_PAGE_QUERY, variables={"first": 2})
    assert first.get("errors") is None, first
    cursor = first["data"]["issues"]["pageInfo"]["endCursor"]
    second = await _post_async_holder(
        schema,
        _HOLDER_PAGE_QUERY,
        variables={"first": 2, "after": cursor},
    )
    assert second.get("errors") is None, second
    assert [edge["node"]["title"] for edge in second["data"]["issues"]["edges"]] == ["i1"]


@pytest.mark.django_db(transaction=True)
async def test_async_keyset_total_count_only():
    """A totalCount-only async keyset query counts via ``acount`` and fetches no edges."""

    async def _async_resolver(root, info):
        return models.Issue.objects.all()

    await sync_to_async(_seed_three_issues)()
    payload = await _post_async_holder(
        _issue_holder_schema(_async_resolver),
        "{ issues { totalCount } }",
    )
    assert payload.get("errors") is None, payload
    assert payload["data"]["issues"] == {"totalCount": 3}


@pytest.mark.django_db(transaction=True)
async def test_async_keyset_deferred_cursor_column_is_loaded():
    """Cursor minting on an async keyset field must not lazy-load a deferred order column."""

    async def _async_resolver(root, info):
        return models.Issue.objects.defer("number", "title")

    await sync_to_async(_seed_three_issues)()
    payload = await _post_async_holder(
        _issue_holder_schema(_async_resolver),
        "{ issues(first: 1) { edges { cursor } } }",
    )
    assert payload.get("errors") is None, payload
    assert len(payload["data"]["issues"]["edges"]) == 1
    assert payload["data"]["issues"]["edges"][0]["cursor"]
