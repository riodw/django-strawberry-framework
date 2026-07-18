"""Live GraphQL HTTP tests for the single-parent windowed-prefetch fast path.

The runtime fast path (``optimizer/single_parent_fetch.py``) replaces the
``ROW_NUMBER() OVER (PARTITION BY fk)`` window with a plain filtered ``LIMIT``
re-query whenever the Django-prefetch-injected parent ``IN`` list has length
exactly ONE and the shape is the count-free plain first page. It is a
``"windowed"``-strategy feature (fakeshop's default) and it degrades - never
breaks - back to the window for any unrecognized shape.

Test substrate (a DEVIATION from the plan, forced by the schema - see the file
report): the plan named ``ShelfType.booksConnection`` for the DIRECT_FK offset
tests, but ``ShelfType`` is NOT Relay-Node-shaped, so no relation connection is
synthesized on it (``types/finalizer.py::_synthesize_relation_connections``
gates on ``implements_relay_node(type_cls)``). The ONLY DIRECT_FK connection on
a Relay-Node parent in the library app is ``PeriodicalType.issuesConnection``
(reverse FK ``Issue.periodical`` -> Relay-Node ``IssueType``), so every DIRECT_FK
case rides it AS STAFF - as staff, ``IssueType.get_queryset`` returns the
queryset unchanged, so the child WHERE tree is just "window range + one parent
IN" and the fast path engages. ``IssueType`` is keyset-cursored
(``cursor_field = ("-number", "id")``), so the first page (``keyset_seek is
None``) still engages while an ``after:`` seek page keeps the window (this
subsumes the plan's separate offset-page test). The anonymous run is the
visibility-degradation case: the non-staff ``get_queryset`` embargo filter lands
as an extra WHERE qual, the recognizer refuses, and the window (``OVER (``) is
kept. The M2M exclusion rides ``genre.booksConnection`` (a THROUGH_TABLE join).

Every assertion scans ``CaptureQueriesContext`` for the presence/absence of the
``OVER (`` window construct in the captured child-table SQL.
"""

import pytest
from apps.library import models
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from graphql_client import post_graphql as _post_graphql

from django_strawberry_framework.testing import TestClient


def _seed_periodical(name: str, count: int, *, embargoed: bool = False):
    """One periodical named ``name`` with issues #1..#count (newest-first window order)."""
    periodical = models.Periodical.objects.create(name=name)
    for number in range(1, count + 1):
        models.Issue.objects.create(
            periodical=periodical,
            number=number,
            title=f"{name} #{number}",
            embargoed=embargoed,
        )
    return periodical


def _seed_one_genre_with_books(*titles: str):
    """One genre with ``titles`` books via the reverse M2M (THROUGH_TABLE substrate)."""
    genre = models.Genre.objects.create(name="Speculative")
    branch = models.Branch.objects.create(name="Central", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    for title in titles:
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)
    return genre


def _capture(query: str):
    """Post an anonymous GraphQL query, returning ``(payload, captured)``."""
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    return payload, captured


def _capture_as_staff(query: str):
    """Post a GraphQL query authenticated as a fresh staff user, returning ``(payload, captured)``.

    Staff bypasses every library ``get_queryset`` visibility hook, so the child
    queryset is the clean "window range + one parent IN" shape the fast path
    recognizes (the anonymous run is the degradation case).
    """
    user_model = get_user_model()
    staff, _created = user_model.objects.get_or_create(
        username="staff",
        defaults={"is_staff": True},
    )
    client = TestClient()
    with CaptureQueriesContext(connection) as captured:
        with client.login(staff):
            response = client.query(query, assert_no_errors=False).response
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    return payload, captured


def _has_window(captured: CaptureQueriesContext) -> bool:
    """Whether any captured statement carries the ``ROW_NUMBER() OVER (...)`` window."""
    return any("OVER (" in entry["sql"] for entry in captured.captured_queries)


def _child_sql(captured: CaptureQueriesContext, table: str) -> list[str]:
    """The captured statements referencing ``table`` (the nested child query)."""
    return [entry["sql"] for entry in captured.captured_queries if table in entry["sql"]]


def _periodicals(payload):
    """The parent edges of the ``allLibraryPeriodicalsConnection`` root."""
    return payload["data"]["allLibraryPeriodicalsConnection"]["edges"]


def _issues_query(inner: str) -> str:
    """Wrap a nested ``issuesConnection(...)`` selection in the periodicals root."""
    return f"""
        query {{
          allLibraryPeriodicalsConnection(first: 10) {{
            edges {{ node {{ name issuesConnection{inner} }} }}
          }}
        }}
        """


@pytest.mark.django_db
def test_single_parent_first_page_skips_window_over_http():
    """One parent + a count-free plain first page: the fast path runs, no ``OVER (``."""
    _seed_periodical("Astro", 3)

    payload, captured = _capture_as_staff(
        _issues_query("(first: 2) { edges { cursor node { title number } } }"),
    )
    parents = _periodicals(payload)
    assert len(parents) == 1
    edges = parents[0]["node"]["issuesConnection"]["edges"]
    assert [edge["node"]["title"] for edge in edges] == ["Astro #3", "Astro #2"]
    assert all(edge["cursor"] for edge in edges)
    assert not _has_window(captured)


@pytest.mark.django_db
def test_single_parent_probe_shape_overfetches_without_window_over_http():
    """``pageInfo { hasNextPage }`` (no ``totalCount``) overfetches ``LIMIT 3`` off-window."""
    _seed_periodical("Astro", 3)

    payload, captured = _capture_as_staff(
        _issues_query("(first: 2) { edges { node { title } } pageInfo { hasNextPage } }"),
    )
    conn = _periodicals(payload)[0]["node"]["issuesConnection"]
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Astro #3", "Astro #2"]
    assert conn["pageInfo"]["hasNextPage"] is True
    assert not _has_window(captured)
    child_sql = _child_sql(captured, models.Issue._meta.db_table)
    assert any("LIMIT 3" in sql for sql in child_sql), child_sql


@pytest.mark.django_db
def test_single_parent_total_count_keeps_window_over_http():
    """Selecting ``totalCount`` keeps the window: a bare ``LIMIT`` cannot count the partition."""
    _seed_periodical("Astro", 3)

    payload, captured = _capture_as_staff(
        _issues_query("(first: 2) { totalCount edges { node { title } } }"),
    )
    conn = _periodicals(payload)[0]["node"]["issuesConnection"]
    assert conn["totalCount"] == 3
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Astro #3", "Astro #2"]
    assert _has_window(captured)


@pytest.mark.django_db
def test_multi_parent_keeps_window_over_http():
    """Two parents (IN length 2) keep the window; each parent's page is correct."""
    _seed_periodical("Astro", 3)
    _seed_periodical("Botany", 2)

    payload, captured = _capture_as_staff(
        _issues_query("(first: 2) { edges { node { title } } }"),
    )
    pages = {
        edge["node"]["name"]: [
            issue["node"]["title"] for issue in edge["node"]["issuesConnection"]["edges"]
        ]
        for edge in _periodicals(payload)
    }
    assert pages == {"Astro": ["Astro #3", "Astro #2"], "Botany": ["Botany #2", "Botany #1"]}
    assert _has_window(captured)


@pytest.mark.django_db
def test_single_parent_offset_page_keeps_window_over_http():
    """A seek (``after:``) page is not the plain first page, so the window is kept.

    ``IssueType`` is keyset-cursored, so the non-first page is reached with a
    minted value cursor (the library substrate has no arrayconnection-offset
    DIRECT_FK connection - see the module docstring).
    """
    _seed_periodical("Astro", 3)

    first_payload, _ = _capture_as_staff(
        _issues_query("(first: 2) { edges { cursor node { title } } }"),
    )
    first_edges = _periodicals(first_payload)[0]["node"]["issuesConnection"]["edges"]
    after = first_edges[-1]["cursor"]

    payload, captured = _capture_as_staff(
        _issues_query(f'(first: 2, after: "{after}") {{ edges {{ node {{ title }} }} }}'),
    )
    conn = _periodicals(payload)[0]["node"]["issuesConnection"]
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Astro #1"]
    assert _has_window(captured)


@pytest.mark.django_db
def test_single_parent_keyset_first_page_skips_window_as_staff_over_http():
    """A keyset first page engages the fast path AND mints valid, round-trippable cursors.

    The consumer derives keyset cursors from the row column values, not from the
    synthesized ``_dst_row_number``, so a cursor minted off the fast-path page
    must replay as a valid ``after:`` seek that continues the partition.
    """
    _seed_periodical("Astro", 4)

    payload, captured = _capture_as_staff(
        _issues_query("(first: 2) { edges { cursor node { title number } } }"),
    )
    conn = _periodicals(payload)[0]["node"]["issuesConnection"]
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Astro #4", "Astro #3"]
    assert not _has_window(captured)

    after = conn["edges"][-1]["cursor"]
    next_payload, _ = _capture_as_staff(
        _issues_query(f'(first: 2, after: "{after}") {{ edges {{ node {{ title }} }} }}'),
    )
    next_conn = _periodicals(next_payload)[0]["node"]["issuesConnection"]
    assert [edge["node"]["title"] for edge in next_conn["edges"]] == ["Astro #2", "Astro #1"]


@pytest.mark.django_db
def test_visibility_filtered_child_keeps_window_over_http():
    """The same first-page query ANONYMOUS: the visibility filter refuses the fast path.

    ``IssueType.get_queryset`` excludes ``embargoed=True`` for non-staff, landing
    an unrecognized WHERE qual on the child - the recognizer fails closed to the
    window and the (all-visible) data stays correct (degradation, never breakage).
    """
    _seed_periodical("Astro", 3, embargoed=False)

    payload, captured = _capture(
        _issues_query("(first: 2) { edges { node { title } } }"),
    )
    conn = _periodicals(payload)[0]["node"]["issuesConnection"]
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Astro #3", "Astro #2"]
    assert _has_window(captured)


@pytest.mark.django_db
def test_single_parent_empty_children_over_http():
    """One parent with zero children: the fast path serves an empty page, no ``OVER (``."""
    _seed_periodical("Astro", 0)

    payload, captured = _capture_as_staff(
        _issues_query("(first: 2) { edges { node { title } } pageInfo { hasNextPage } }"),
    )
    conn = _periodicals(payload)[0]["node"]["issuesConnection"]
    assert conn["edges"] == []
    assert conn["pageInfo"]["hasNextPage"] is False
    assert not _has_window(captured)


@pytest.mark.django_db
def test_fast_path_disabled_by_setting_over_http():
    """``SINGLE_PARENT_FAST_PATH: False`` keeps the window on the otherwise-eligible shape."""
    _seed_periodical("Astro", 3)

    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"SINGLE_PARENT_FAST_PATH": False}):
        payload, captured = _capture_as_staff(
            _issues_query("(first: 2) { edges { node { title } } }"),
        )
    conn = _periodicals(payload)[0]["node"]["issuesConnection"]
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Astro #3", "Astro #2"]
    assert _has_window(captured)


@pytest.mark.django_db
def test_m2m_shape_keeps_window_over_http():
    """A single-parent M2M (THROUGH_TABLE) connection keeps the window (v1 excludes M2M)."""
    _seed_one_genre_with_books("Aurora", "Binti", "Circe")

    payload, captured = _capture_as_staff(
        """
        query {
          allLibraryGenres {
            booksConnection(first: 2) { edges { node { title } } }
          }
        }
        """,
    )
    conn = payload["data"]["allLibraryGenres"][0]["booksConnection"]
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Aurora", "Binti"]
    assert _has_window(captured)
