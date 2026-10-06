"""Live GraphQL HTTP tests for a combined ``get_queryset`` result served as its primary-key set.

A visibility hook may return ``union`` / ``intersection`` / ``difference`` over the
queryset it is handed. Every read surface serves that result as the set of primary
keys the combinator selects: the root list and connections, the keyset connection,
plain-list and many-to-many children, a to-one downgraded to a prefetch, a nested
connection (windowed under the optimizer, per parent without it), ``node`` /
``nodes``, a related-filter derive, both ends of ``apply_cascade_permissions``, a
mutation's locate and payload, a consumer ``Prefetch`` a hook returns, and the
optimizer under ``strictness="raise"``. Each served row asserts the exact rows and
that they equal what the uncombined equivalent hook answers, with the optimizer
installed (the shipped ``/graphql/``) and without it (the library schema mounted at
``/graphql-test/`` with no extension).

The outer ordering is carried when it names a column: a column name, an exact
``F()`` over one, or that ``F()`` under ``.asc()`` / ``.desc()``, served in the order
the combinator itself returns (a forward relation by its key column). A shape that
the primary-key set cannot carry (duplicate rows, a branch's selected
annotations, ``extra(select=)`` aliases or ``.values()`` projection, a branch row
lock, an outer ordering by a lookup, transform or other expression, an outer ``.values()``
projection where the surface accepts projections) is refused with the ``combined``
defect naming the type, the combinator and what would be lost, one row each,
reached through a real field and rendered as that field's GraphQL error. A model-row
surface refuses an outer ``.values()`` as a projection first; a sliced combined
result is refused as ``sliced`` where the seal refuses slices and as ``combined``
under a nested connection, whose seal licenses a slice the rewrite cannot carry.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass

import pytest
import strawberry
from apps.library import models
from django.conf import settings
from django.db import connection
from django.db.models import F, Model, OrderBy, Prefetch, Q, QuerySet, Value
from django.db.models.functions import Lower
from django.http import HttpRequest
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path
from graphql_client import JSONObject, post_graphql
from strategy_schemas import make_django_type
from strawberry.extensions import SchemaExtension
from typing_extensions import TypedDict, Unpack

from django_strawberry_framework import (
    DjangoListField,
    DjangoSchema,
    DjangoType,
    OptimizerHint,
    apply_cascade_permissions,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.views import DjangoGraphQLView

#: Opens the error policy's pass-through gate so a refusal's message reaches the
#: wire; the toolbar middleware is dropped because ``config.urls`` computed its
#: ``djdt`` routes under the ambient ``DEBUG=False``.
_ERROR_POLICY_PASS_THROUGH = {
    "DEBUG": True,
    "MIDDLEWARE": [entry for entry in settings.MIDDLEWARE if "debug_toolbar" not in entry],
}

_CURRENT: dict[str, DjangoSchema | None] = {"schema": None}


def _graphql_view(request: HttpRequest):
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


urlpatterns = [path("graphql-test/", _graphql_view)]


def _library_schema(
    extensions: list[type[SchemaExtension] | Callable[[], SchemaExtension]],
) -> DjangoSchema:
    """The library app's own ``Query`` and ``Mutation``, carrying ``extensions`` only."""
    from apps.library.schema import Mutation, Query

    return DjangoSchema(
        query=Query,
        mutation=Mutation,
        config=strawberry_config(),
        extensions=extensions,
    )


def _post(
    query: str,
    *,
    optimizer: bool = True,
    variables: JSONObject | None = None,
    schema: DjangoSchema | None = None,
) -> JSONObject:
    """Post ``query`` and return the parsed envelope.

    ``optimizer=True`` posts to the shipped ``/graphql/``, whose schema carries the
    project's ``DjangoOptimizerExtension``; ``optimizer=False`` posts the same
    document to the library schema mounted with no extension. ``schema`` mounts a
    caller-built schema instead.
    """
    if optimizer and schema is None:
        with override_settings(**_ERROR_POLICY_PASS_THROUGH):
            response = post_graphql(query, variables=variables)
    else:
        _CURRENT["schema"] = schema if schema is not None else _library_schema([])
        try:
            with override_settings(ROOT_URLCONF=__name__, **_ERROR_POLICY_PASS_THROUGH):
                response = post_graphql(query, variables=variables, url="/graphql-test/")
        finally:
            _CURRENT["schema"] = None
    assert response.status_code == 200
    return response.json()


class _PostOptions(TypedDict, total=False):
    """The keyword options :func:`_data` forwards to :func:`_post`."""

    optimizer: bool
    variables: JSONObject | None
    schema: DjangoSchema | None


def _data(query: str, **kwargs: Unpack[_PostOptions]) -> JSONObject:
    payload = _post(query, **kwargs)
    assert "errors" not in payload, payload
    return payload["data"]


def _order_free(value: object) -> object:
    """``value`` with every list sorted, for comparing payloads whose rows are unordered.

    ``Genre`` and ``Book`` declare no ``Meta.ordering``, so a surface with no
    ``orderBy`` serves its rows in whatever order the backend returns them: SQLite
    happens to return primary-key order, Postgres a hash join's. The served SET is
    the contract; a test whose surface is ordered asserts that order itself.
    """
    if isinstance(value, dict):
        return {key: _order_free(item) for key, item in value.items()}
    if isinstance(value, list):
        return sorted(
            (_order_free(item) for item in value),
            key=lambda item: json.dumps(item, sort_keys=True),
        )
    return value


def _starts(column: str, letter: str) -> Q:
    return Q(**{f"{column}__startswith": letter})


def _holds(column: str, fragment: str) -> Q:
    return Q(**{f"{column}__contains": fragment})


@dataclass(frozen=True)
class _Shape:
    """A combined hook body and the uncombined hook that selects the same rows."""

    combined: Callable[[QuerySet[Model], str], QuerySet[Model]]
    uncombined: Callable[[QuerySet[Model], str], QuerySet[Model]]


_SHAPES = {
    "union": _Shape(
        lambda qs, col: qs.filter(_starts(col, "A")).union(qs.filter(_starts(col, "B"))),
        lambda qs, col: qs.filter(_starts(col, "A") | _starts(col, "B")),
    ),
    "intersection": _Shape(
        lambda qs, col: qs.filter(_holds(col, "i")).intersection(qs.exclude(_starts(col, "Q"))),
        lambda qs, col: qs.filter(_holds(col, "i")).exclude(_starts(col, "Q")),
    ),
    "difference": _Shape(
        lambda qs, col: qs.difference(qs.filter(_starts(col, "A"))),
        lambda qs, col: qs.exclude(_starts(col, "A")),
    ),
    "nested": _Shape(
        lambda qs, col: (
            qs.filter(_starts(col, "A"))
            .union(qs.filter(_starts(col, "B")))
            .difference(qs.filter(_holds(col, "i")))
        ),
        lambda qs, col: qs.filter(_starts(col, "A") | _starts(col, "B")).exclude(_holds(col, "i")),
    ),
}
_SHAPE_IDS = list(_SHAPES)
_OPTIMIZER = pytest.mark.parametrize("optimizer", [True, False], ids=["optimized", "unoptimized"])
_EVERY_SHAPE = pytest.mark.parametrize("shape", _SHAPE_IDS)

#: The seven words every seed below draws its text column from, and the words
#: each shape keeps. Starting letter and the letter ``i`` are what the shapes
#: test, so each shape keeps a different subset and hides at least two words.
_WORDS = (
    "Aurora",
    "Binti",
    "Zed",
    "Ancillary",
    "Circe",
    "Babel",
    "Quill",
)
_VISIBLE = {
    "union": {
        "Aurora",
        "Binti",
        "Ancillary",
        "Babel",
    },
    "intersection": {"Binti", "Ancillary", "Circe"},
    "difference": {
        "Binti",
        "Zed",
        "Circe",
        "Babel",
        "Quill",
    },
    "nested": {"Aurora", "Babel"},
}
#: Genre names with the same letter profile, in the order of ``_WORDS``.
_GENRE_NAMES = (
    "Arcana",
    "Biopunk",
    "Cozy",
    "Anime",
    "Mythic",
    "Baroque",
    "Quixotic",
)
_GENRE_FOR_WORD: dict[str, str] = dict(zip(_WORDS, _GENRE_NAMES, strict=True))


def _visible_genres(shape: str) -> set[str]:
    return {_GENRE_FOR_WORD[word] for word in _VISIBLE[shape]}


def _install(
    monkeypatch: pytest.MonkeyPatch,
    type_name: str,
    body: Callable[[QuerySet[Model], strawberry.Info[object, object]], QuerySet[Model, object]],
) -> None:
    """Make ``type_name``'s ``get_queryset`` return ``body(queryset, info)``."""
    from apps.library import schema as library_schema

    def _hook(
        cls: type[DjangoType],
        queryset: QuerySet[Model],
        info: strawberry.Info[object, object],
        **kwargs: object,
    ):
        del cls, kwargs
        return body(queryset, info)

    monkeypatch.setattr(getattr(library_schema, type_name), "get_queryset", classmethod(_hook))


def _install_shape(
    monkeypatch: pytest.MonkeyPatch,
    type_name: str,
    shape: str,
    column: str,
    *,
    combined: bool,
):
    chosen = _SHAPES[shape].combined if combined else _SHAPES[shape].uncombined
    _install(monkeypatch, type_name, lambda queryset, info: chosen(queryset, column))


def _both_hooks(
    monkeypatch: pytest.MonkeyPatch,
    type_name: str,
    shape: str,
    column: str,
    query: str,
    **kwargs: Unpack[_PostOptions],
) -> JSONObject:
    """The data the combined hook serves, after asserting the uncombined hook serves the same rows.

    The two payloads are compared order-free (``_order_free``); a caller whose query
    orders its rows asserts that order against the expected rows itself.
    """
    _install_shape(monkeypatch, type_name, shape, column, combined=True)
    combined = _data(query, **kwargs)
    _install_shape(monkeypatch, type_name, shape, column, combined=False)
    uncombined = _data(query, **kwargs)
    assert _order_free(combined) == _order_free(uncombined)
    return combined


def _seed_books() -> dict[str, models.Book]:
    """Books titled from ``_WORDS`` across three shelves and two genres.

    Shelf ``A-1`` holds Aurora, Binti, Zed; ``B-2`` holds Ancillary, Circe; ``C-3``
    holds Babel, Quill. ``Spec`` carries Aurora, Binti, Zed, Ancillary, Babel and
    ``Myth`` carries Aurora, Circe, Quill. Books are created in ``_WORDS`` order,
    so primary-key order is ``_WORDS`` order.
    """
    branch = models.Branch.objects.create(name="Central", city="Boston")
    shelves = {
        code: models.Shelf.objects.create(code=code, topic="Fiction", branch=branch)
        for code in ("A-1", "B-2", "C-3")
    }
    shelf_for = {
        "Aurora": "A-1",
        "Binti": "A-1",
        "Zed": "A-1",
        "Ancillary": "B-2",
        "Circe": "B-2",
        "Babel": "C-3",
        "Quill": "C-3",
    }
    spec = models.Genre.objects.create(name="Spec")
    myth = models.Genre.objects.create(name="Myth")
    books = {}
    for word in _WORDS:
        books[word] = models.Book.objects.create(title=word, shelf=shelves[shelf_for[word]])
    spec.books.add(
        *(
            books[w]
            for w in (
                "Aurora",
                "Binti",
                "Zed",
                "Ancillary",
                "Babel",
            )
        ),
    )
    myth.books.add(*(books[w] for w in ("Aurora", "Circe", "Quill")))
    return books


_BOOKS_BY_SHELF = {
    "A-1": ("Aurora", "Binti", "Zed"),
    "B-2": ("Ancillary", "Circe"),
    "C-3": ("Babel", "Quill"),
}
_BOOKS_BY_GENRE = {
    "Spec": (
        "Aurora",
        "Binti",
        "Zed",
        "Ancillary",
        "Babel",
    ),
    "Myth": ("Aurora", "Circe", "Quill"),
}


def _seed_genres() -> None:
    for name in _GENRE_NAMES:
        models.Genre.objects.create(name=name)


# ---------------------------------------------------------------------------
# Root list, root connection, keyset connection
# ---------------------------------------------------------------------------


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_root_list_without_arguments_serves_the_combined_rows(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``allLibraryGenresViaListField`` with no arguments serves exactly the hook's genres."""
    _seed_genres()

    data = _both_hooks(
        monkeypatch,
        "GenreType",
        shape,
        "name",
        "{ allLibraryGenresViaListField { name } }",
        optimizer=optimizer,
    )

    names = sorted(row["name"] for row in data["allLibraryGenresViaListField"])
    assert names == sorted(_visible_genres(shape))


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_root_list_orders_the_combined_rows_by_order_by(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``orderBy:`` on the root list orders the combined set, descending here."""
    _seed_genres()

    data = _both_hooks(
        monkeypatch,
        "GenreType",
        shape,
        "name",
        "{ allLibraryGenresViaListField(orderBy: [{ name: DESC }]) { name } }",
        optimizer=optimizer,
    )

    names = [row["name"] for row in data["allLibraryGenresViaListField"]]
    assert names == sorted(_visible_genres(shape), reverse=True)


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_root_list_limits_the_ordered_combined_rows(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``limit:`` takes the first rows of the ordered combined set, not of the table."""
    _seed_genres()

    data = _both_hooks(
        monkeypatch,
        "GenreType",
        shape,
        "name",
        "{ allLibraryGenresViaListField(limit: 2, orderBy: [{ name: ASC }]) { name } }",
        optimizer=optimizer,
    )

    names = [row["name"] for row in data["allLibraryGenresViaListField"]]
    assert names == sorted(_visible_genres(shape))[:2]


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_root_connection_pages_the_combined_rows(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``allLibraryGenresConnection(first: 2)`` pages the ordered combined set."""
    _seed_genres()

    data = _both_hooks(
        monkeypatch,
        "GenreType",
        shape,
        "name",
        """
        {
          allLibraryGenresConnection(first: 2, orderBy: [{ name: ASC }]) {
            edges { node { name } }
            pageInfo { hasNextPage }
          }
        }
        """,
        optimizer=optimizer,
    )

    conn = data["allLibraryGenresConnection"]
    visible = sorted(_visible_genres(shape))
    assert [edge["node"]["name"] for edge in conn["edges"]] == visible[:2]
    assert conn["pageInfo"]["hasNextPage"] is (len(visible) > 2)


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_root_connection_filters_the_combined_rows(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``filter:`` narrows the combined set: a hidden genre never matches."""
    _seed_genres()

    data = _both_hooks(
        monkeypatch,
        "GenreType",
        shape,
        "name",
        """
        {
          allLibraryGenresConnection(
            filter: { name: { iContains: "o" } }
            orderBy: [{ name: ASC }]
          ) {
            edges { node { name } }
          }
        }
        """,
        optimizer=optimizer,
    )

    names = [edge["node"]["name"] for edge in data["allLibraryGenresConnection"]["edges"]]
    assert names == sorted(name for name in _visible_genres(shape) if "o" in name)


def _seed_issues() -> None:
    """Issues titled from ``_WORDS``, numbered 1-7 in that order."""
    periodical = models.Periodical.objects.create(name="Monthly")
    for number, word in enumerate(_WORDS, start=1):
        models.Issue.objects.create(periodical=periodical, number=number, title=word)


_ISSUES_PAGE = """
query ($after: String) {
  allLibraryIssuesConnection(first: 2, after: $after) {
    edges { node { title } }
    pageInfo { hasNextPage endCursor }
  }
}
"""


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_keyset_connection_seeks_through_the_combined_rows(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """The ``cursor_field = ("-number", "id")`` connection pages the combined set by value cursor.

    The second page is fetched from the first page's ``endCursor``, so the seek
    predicate composes onto the served set, and the two pages together are the
    visible issues newest first.
    """
    _seed_issues()
    newest_first = [word for word in reversed(_WORDS) if word in _VISIBLE[shape]]
    pages = {}
    for combined in (True, False):
        _install_shape(monkeypatch, "IssueType", shape, "title", combined=combined)
        first = _data(_ISSUES_PAGE, optimizer=optimizer)["allLibraryIssuesConnection"]
        second = _data(
            _ISSUES_PAGE,
            optimizer=optimizer,
            variables={"after": first["pageInfo"]["endCursor"]},
        )["allLibraryIssuesConnection"]
        pages[combined] = [
            [edge["node"]["title"] for edge in first["edges"]],
            [edge["node"]["title"] for edge in second["edges"]],
        ]

    assert pages[True] == pages[False] == [newest_first[:2], newest_first[2:4]]


# ---------------------------------------------------------------------------
# Nested children
# ---------------------------------------------------------------------------


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_reverse_foreign_key_list_child_serves_the_combined_rows(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``shelves { books }`` serves each shelf's books that the combined hook keeps."""
    _seed_books()

    data = _both_hooks(
        monkeypatch,
        "BookType",
        shape,
        "title",
        "{ allLibraryShelves { code books { title } } }",
        optimizer=optimizer,
    )

    served = {
        row["code"]: sorted(book["title"] for book in row["books"])
        for row in data["allLibraryShelves"]
    }
    assert served == {
        code: sorted(t for t in titles if t in _VISIBLE[shape])
        for code, titles in _BOOKS_BY_SHELF.items()
    }


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_many_to_many_list_child_serves_the_combined_rows(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``genres { books }`` serves each genre's books that the combined hook keeps."""
    _seed_books()

    data = _both_hooks(
        monkeypatch,
        "BookType",
        shape,
        "title",
        "{ allLibraryGenres { name books { title } } }",
        optimizer=optimizer,
    )

    served = {
        row["name"]: sorted(book["title"] for book in row["books"])
        for row in data["allLibraryGenres"]
    }
    assert served == {
        name: sorted(t for t in titles if t in _VISIBLE[shape])
        for name, titles in _BOOKS_BY_GENRE.items()
    }


def _seed_venues() -> None:
    """One venue per ``_WORDS`` word, named after it, whose lead ticket is coded after it."""
    for word in _WORDS:
        venue = models.Venue.objects.create(name=word)
        venue.lead_ticket = models.RepairTicket.objects.create(code=word, venue=venue)
        venue.save(update_fields=["lead_ticket"])


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_downgraded_to_one_resolves_only_combined_targets(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``leadTicket`` resolves a ticket the combined hook keeps and ``null`` for one it hides.

    ``RepairTicketType`` declares a hook, so the nullable ``lead_ticket`` forward key
    is fetched through a ``Prefetch`` over that hook instead of a join, and the
    combined result is what that prefetch runs on. ``VenueType``'s own hook is
    replaced by one that keeps every venue, so no cascade hides a venue first and
    both verdicts land in one payload.
    """
    _seed_venues()
    _install(monkeypatch, "VenueType", lambda queryset, info: queryset)

    data = _both_hooks(
        monkeypatch,
        "RepairTicketType",
        shape,
        "code",
        "{ allLibraryVenues(orderBy: [{ name: ASC }]) { name leadTicket { code } } }",
        optimizer=optimizer,
    )

    assert data["allLibraryVenues"] == [
        {"name": word, "leadTicket": {"code": word} if word in _VISIBLE[shape] else None}
        for word in sorted(_WORDS)
    ]


_NESTED_CONNECTION = """
{
  allLibraryGenres {
    name
    booksConnection(first: 2) {
      edges { node { title } }
      pageInfo { hasNextPage }
    }
  }
}
"""


class _NestedPage(TypedDict):
    """One genre's nested ``booksConnection`` window: its titles and whether more remain."""

    titles: list[str]
    has_next: bool


def _expected_nested_pages(shape: str) -> dict[str, _NestedPage]:
    """Each genre's first two visible books in primary-key order, and whether more remain."""
    pages = {}
    for name, titles in _BOOKS_BY_GENRE.items():
        visible = [word for word in _WORDS if word in titles and word in _VISIBLE[shape]]
        pages[name] = {"titles": visible[:2], "has_next": len(visible) > 2}
    return pages


def _nested_pages(data: JSONObject) -> dict[str, _NestedPage]:
    return {
        row["name"]: {
            "titles": [edge["node"]["title"] for edge in row["booksConnection"]["edges"]],
            "has_next": row["booksConnection"]["pageInfo"]["hasNextPage"],
        }
        for row in data["allLibraryGenres"]
    }


@_EVERY_SHAPE
@pytest.mark.django_db
def test_nested_connection_windows_the_combined_rows_in_one_prefetch(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
):
    """Under the optimizer ``booksConnection(first: 2)`` stays one ``ROW_NUMBER`` window query.

    The window is taken over the combined set: two library statements (the genre
    root and the windowed book prefetch, never ``1 + N``), the window's
    ``_dst_row_number`` present and no count window.
    """
    _seed_books()
    _install_shape(monkeypatch, "BookType", shape, "title", combined=True)

    with CaptureQueriesContext(connection) as captured:
        data = _data(_NESTED_CONNECTION)

    assert _nested_pages(data) == _expected_nested_pages(shape)
    library_sql = [q["sql"] for q in captured.captured_queries if "library_" in q["sql"]]
    assert len(library_sql) == 2, library_sql
    assert "_dst_row_number" in library_sql[1]
    assert "COUNT(" not in library_sql[1].upper()


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_nested_connection_serves_the_combined_rows(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``booksConnection(first: 2)`` serves the same page windowed and per parent."""
    _seed_books()

    data = _both_hooks(
        monkeypatch,
        "BookType",
        shape,
        "title",
        _NESTED_CONNECTION,
        optimizer=optimizer,
    )

    assert _nested_pages(data) == _expected_nested_pages(shape)


# ---------------------------------------------------------------------------
# Relay refetch
# ---------------------------------------------------------------------------


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_nodes_refetch_only_combined_rows(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``nodes(ids:)`` over every book returns the combined hook's books and ``null`` elsewhere."""
    from apps.library.schema import BookType

    books = _seed_books()
    ids = ", ".join(f'"{global_id_for(BookType, books[word].pk)}"' for word in _WORDS)

    data = _both_hooks(
        monkeypatch,
        "BookType",
        shape,
        "title",
        "{ nodes(ids: [%s]) { ... on BookType { title } } }" % ids,
        optimizer=optimizer,
    )

    assert data["nodes"] == [
        {"title": word} if word in _VISIBLE[shape] else None for word in _WORDS
    ]


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_node_refetches_a_combined_row_and_hides_an_excluded_one(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``node(id:)`` resolves a book the combined hook keeps and ``null`` for one it excludes."""
    from apps.library.schema import BookType

    books = _seed_books()
    kept = next(word for word in _WORDS if word in _VISIBLE[shape])
    excluded = next(word for word in _WORDS if word not in _VISIBLE[shape])
    query = """
    {
      kept: node(id: "%s") { ... on BookType { title } }
      excluded: node(id: "%s") { ... on BookType { title } }
    }
    """ % (global_id_for(BookType, books[kept].pk), global_id_for(BookType, books[excluded].pk))

    data = _both_hooks(monkeypatch, "BookType", shape, "title", query, optimizer=optimizer)

    assert data == {"kept": {"title": kept}, "excluded": None}


# ---------------------------------------------------------------------------
# Related-filter derive and the visibility cascade
# ---------------------------------------------------------------------------


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_related_filter_matches_only_through_combined_rows(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``shelves(filter: { books: ... })`` matches a shelf only through a book the hook keeps."""
    _seed_books()

    data = _both_hooks(
        monkeypatch,
        "BookType",
        shape,
        "title",
        '{ allLibraryShelves(filter: { books: { title: { iContains: "r" } } }) { code } }',
        optimizer=optimizer,
    )

    expected = sorted(
        code
        for code, titles in _BOOKS_BY_SHELF.items()
        if any(t in _VISIBLE[shape] and "r" in t for t in titles)
    )
    assert sorted(row["code"] for row in data["allLibraryShelves"]) == expected


def _seed_desks(*, secret_word: str | None = None) -> None:
    """One circulation desk per ``_WORDS`` word, named after it, on a shelf coded after it.

    ``secret_word``'s shelf carries ``topic="secret"``, which the shipped
    ``ShelfType`` hook hides, so the cascade hides that desk too.
    """
    branch = models.Branch.objects.create(name="Central", city="Boston")
    for word in _WORDS:
        shelf = models.Shelf.objects.create(
            code=word,
            topic="secret" if word == secret_word else "Fiction",
            branch=branch,
        )
        models.CirculationDesk.objects.create(name=word, branch=branch, shelf=shelf)


_DESKS = "{ allLibraryCirculationDesks(orderBy: [{ name: ASC }]) { name shelf { code } } }"


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_cascade_through_a_combined_target_hides_desks_on_excluded_shelves(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``CirculationDeskType``'s cascade over ``shelf`` binds to the combined ``ShelfType`` set.

    A desk is served exactly when its shelf is one the combined hook keeps, and its
    ``shelf`` to-one resolves through the same hook.
    """
    _seed_desks()

    data = _both_hooks(monkeypatch, "ShelfType", shape, "code", _DESKS, optimizer=optimizer)

    assert data["allLibraryCirculationDesks"] == [
        {"name": word, "shelf": {"code": word}} for word in sorted(_VISIBLE[shape])
    ]


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_cascade_narrows_a_combined_root(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """``apply_cascade_permissions`` handed a combined root narrows that set by the cascade.

    The desk hook combines over desk names, then cascades over ``branch`` and
    ``shelf``: the desk on the secret shelf is hidden although the combinator keeps
    it, and every other served desk is one the combinator keeps.
    """
    secret = next(word for word in _WORDS if word in _VISIBLE[shape])
    _seed_desks(secret_word=secret)

    results = {}
    for combined in (True, False):
        chosen = _SHAPES[shape].combined if combined else _SHAPES[shape].uncombined

        def _body(
            queryset: QuerySet[Model],
            info: strawberry.Info[object, object],
            chosen: Callable[[QuerySet[Model], str], QuerySet[Model]] = chosen,
        ):
            from apps.library.schema import CirculationDeskType

            return apply_cascade_permissions(
                CirculationDeskType,
                chosen(queryset, "name"),
                info,
                fields=["branch", "shelf"],
            )

        _install(monkeypatch, "CirculationDeskType", _body)
        results[combined] = _data(_DESKS, optimizer=optimizer)

    assert results[True] == results[False]
    assert results[True]["allLibraryCirculationDesks"] == [
        {"name": word, "shelf": {"code": word}} for word in sorted(_VISIBLE[shape] - {secret})
    ]


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

_UPDATE_BOOK = """
mutation ($id: ID!, $data: BookPartialInput!) {
  updateBookViaCustomInput(id: $id, data: $data) {
    node { title shelf { code } }
    errors { field messages }
  }
}
"""


#: What the locate answers for a row its type's hook does not keep.
_EXCLUDED_UPDATE_ENVELOPE = {
    "data": {
        "updateBookViaCustomInput": {
            "node": None,
            "errors": [{"field": "id", "messages": ["No matching row found."]}],
        },
    },
}


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.parametrize("combined", [True, False], ids=["combined", "uncombined"])
@pytest.mark.django_db
def test_mutation_locates_and_updates_only_a_combined_row(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
    combined: bool,
):
    """``updateBookViaCustomInput`` locates its row through the combined ``BookType`` hook.

    A kept book is updated and returned; an excluded one is answered exactly as the
    uncombined hook answers it and keeps its title.
    """
    from apps.library.schema import BookType

    books = _seed_books()
    kept = next(word for word in _WORDS if word in _VISIBLE[shape])
    excluded = next(word for word in _WORDS if word not in _VISIBLE[shape])
    _install_shape(monkeypatch, "BookType", shape, "title", combined=combined)

    updated = _data(
        _UPDATE_BOOK,
        optimizer=optimizer,
        variables={"id": global_id_for(BookType, books[kept].pk), "data": {"title": "Renamed"}},
    )
    refused = _post(
        _UPDATE_BOOK,
        optimizer=optimizer,
        variables={
            "id": global_id_for(BookType, books[excluded].pk),
            "data": {"title": "Renamed"},
        },
    )

    assert updated["updateBookViaCustomInput"]["errors"] == []
    assert updated["updateBookViaCustomInput"]["node"]["title"] == "Renamed"
    books[excluded].refresh_from_db()
    assert books[excluded].title == excluded
    books[kept].refresh_from_db()
    assert books[kept].title == "Renamed"
    assert refused == _EXCLUDED_UPDATE_ENVELOPE, refused


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_mutation_payload_resolves_its_relation_through_the_combined_hook(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """The payload's ``node { shelf }`` resolves through the combined ``ShelfType`` hook."""
    from apps.library.schema import BookType

    branch = models.Branch.objects.create(name="Central", city="Boston")
    code = next(word for word in _WORDS if word in _VISIBLE[shape])
    shelf = models.Shelf.objects.create(code=code, topic="Fiction", branch=branch)
    for word in _WORDS:
        if word != code:
            models.Shelf.objects.create(code=word, topic="Fiction", branch=branch)
    book = models.Book.objects.create(title="Kindred", shelf=shelf)
    payloads = {}
    for combined in (True, False):
        _install_shape(monkeypatch, "ShelfType", shape, "code", combined=combined)
        payloads[combined] = _data(
            _UPDATE_BOOK,
            optimizer=optimizer,
            variables={
                "id": global_id_for(BookType, book.pk),
                "data": {"title": f"Kindred {combined}"},
            },
        )["updateBookViaCustomInput"]

    assert payloads[True] == {
        "node": {"title": "Kindred True", "shelf": {"code": code}},
        "errors": [],
    }
    assert payloads[False] == {
        "node": {"title": "Kindred False", "shelf": {"code": code}},
        "errors": [],
    }


# ---------------------------------------------------------------------------
# Consumer prefetch and strictness
# ---------------------------------------------------------------------------


@_OPTIMIZER
@_EVERY_SHAPE
@pytest.mark.django_db
def test_consumer_prefetch_of_a_combined_queryset_serves_its_rows(
    monkeypatch: pytest.MonkeyPatch,
    shape: str,
    optimizer: bool,
):
    """A hook's ``Prefetch("books", queryset=<combined>)`` serves each genre's kept books."""
    _seed_books()
    results = {}
    for combined in (True, False):
        chosen = _SHAPES[shape].combined if combined else _SHAPES[shape].uncombined

        def _body(
            queryset: QuerySet[Model],
            info: strawberry.Info[object, object],
            chosen: Callable[[QuerySet[Model], str], QuerySet[Model]] = chosen,
        ):
            del info
            books = chosen(models.Book.objects.all(), "title")
            return queryset.prefetch_related(Prefetch("books", queryset=books))

        _install(monkeypatch, "GenreType", _body)
        results[combined] = _data(
            "{ allLibraryGenresViaListField { name books { title } } }",
            optimizer=optimizer,
        )

    assert _order_free(results[True]) == _order_free(results[False])
    served = {
        row["name"]: sorted(book["title"] for book in row["books"])
        for row in results[True]["allLibraryGenresViaListField"]
    }
    assert served == {
        name: sorted(t for t in titles if t in _VISIBLE[shape])
        for name, titles in _BOOKS_BY_GENRE.items()
    }


@_EVERY_SHAPE
@pytest.mark.django_db
def test_strictness_raise_plans_a_combined_child(monkeypatch: pytest.MonkeyPatch, shape: str):
    """Under ``strictness="raise"`` a combined ``books`` child is planned: nothing lazy-loads."""
    _seed_books()
    _install_shape(monkeypatch, "BookType", shape, "title", combined=True)
    optimizer = DjangoOptimizerExtension(strictness="raise")

    data = _data(
        "{ allLibraryShelves { code books { title } } allLibraryGenres { name books { title } } }",
        schema=_library_schema([lambda: optimizer]),
    )

    assert {
        row["code"]: sorted(book["title"] for book in row["books"])
        for row in data["allLibraryShelves"]
    } == {
        code: sorted(t for t in titles if t in _VISIBLE[shape])
        for code, titles in _BOOKS_BY_SHELF.items()
    }
    assert {
        row["name"]: sorted(book["title"] for book in row["books"])
        for row in data["allLibraryGenres"]
    } == {
        name: sorted(t for t in titles if t in _VISIBLE[shape])
        for name, titles in _BOOKS_BY_GENRE.items()
    }


# ---------------------------------------------------------------------------
# Ordering carried by the rewrite
# ---------------------------------------------------------------------------


@_OPTIMIZER
@pytest.mark.django_db
def test_reversed_outer_ordering_of_a_combined_hook_is_served_reversed(
    monkeypatch: pytest.MonkeyPatch,
    optimizer: bool,
):
    """``union(...).order_by("name").reverse()`` serves the combined genres in descending order."""
    _seed_genres()
    results = {}
    for combined in (True, False):
        chosen = _SHAPES["union"].combined if combined else _SHAPES["union"].uncombined
        _install(
            monkeypatch,
            "GenreType",
            lambda queryset, info, chosen=chosen: (
                chosen(queryset, "name").order_by("name").reverse()
            ),
        )
        results[combined] = _data("{ allLibraryGenresViaListField { name } }", optimizer=optimizer)

    assert results[True] == results[False]
    assert [row["name"] for row in results[True]["allLibraryGenresViaListField"]] == sorted(
        _visible_genres("union"),
        reverse=True,
    )


#: Outer orderings by an ``F()`` over a ``Genre`` column, each with the order the
#: visible union genres arrive in: by name ascending or descending, or by pk descending.
_F_ORDERINGS = {
    "F": (F("name"), "asc"),
    "F-desc": (F("name").desc(), "desc"),
    "F-asc-nulls-last": (F("name").asc(nulls_last=True), "asc"),
    "OrderBy-descending-nulls-first": (
        OrderBy(F("name"), descending=True, nulls_first=True),
        "desc",
    ),
    "F-pk-desc": (F("pk").desc(), "pk-desc"),
}


@_OPTIMIZER
@pytest.mark.parametrize("ordering", list(_F_ORDERINGS))
@pytest.mark.django_db
def test_outer_f_ordering_of_a_combined_hook_is_served_in_that_order(
    monkeypatch: pytest.MonkeyPatch,
    ordering: str,
    optimizer: bool,
):
    """``union(...).order_by(F(c).desc())`` and its ``F`` / ``OrderBy`` kin serve that order.

    The rewrite re-applies an exact ``F`` over a column, bare or wrapped in an
    ``OrderBy`` with any direction and nulls placement, so the combined genres
    arrive in the same order the uncombined hook with that ordering serves.
    """
    _seed_genres()
    term, expected_order = _F_ORDERINGS[ordering]
    results = {}
    for combined in (True, False):
        chosen = _SHAPES["union"].combined if combined else _SHAPES["union"].uncombined
        _install(
            monkeypatch,
            "GenreType",
            lambda queryset, info, chosen=chosen: chosen(queryset, "name").order_by(term),
        )
        results[combined] = _data("{ allLibraryGenresViaListField { name } }", optimizer=optimizer)

    assert results[True] == results[False]
    visible = _visible_genres("union")
    if expected_order == "pk-desc":
        expected = [name for name in reversed(_GENRE_NAMES) if name in visible]
    else:
        expected = sorted(visible, reverse=expected_order == "desc")
    assert [row["name"] for row in results[True]["allLibraryGenresViaListField"]] == expected


#: Outer orderings by the entry's forward relation to ``ReadingList``, which
#: carries a title ``Meta.ordering``, and the entry titles each serves.
_FOREIGN_KEY_ORDERINGS = {
    "name": ("reading_list", ["Ax", "Bx", "Ay"]),
    "-name": ("-reading_list", ["Ay", "Bx", "Ax"]),
    "attname": ("reading_list_id", ["Ax", "Bx", "Ay"]),
    "F-desc": (F("reading_list").desc(), ["Ay", "Bx", "Ax"]),
}


@_OPTIMIZER
@pytest.mark.parametrize("ordering", list(_FOREIGN_KEY_ORDERINGS))
@pytest.mark.django_db
def test_outer_foreign_key_ordering_of_a_combined_hook_orders_by_the_key_column(
    monkeypatch: pytest.MonkeyPatch,
    ordering: str,
    optimizer: bool,
):
    """A combined hook ordered by a forward relation serves the combinator's own key-column order.

    A combinator orders ``"reading_list"`` by the ``reading_list_id`` column, where a
    plain queryset would expand it into ``ReadingList``'s title ``Meta.ordering``.
    The lists are created Zeta, Alpha, Mu, so key order, list-title order and entry
    title order all differ; the served order is the key column's, the order the
    combinator itself returns.
    """
    lists = [models.ReadingList.objects.create(title=title) for title in ("Zeta", "Alpha", "Mu")]
    for title, reading_list in zip(
        (
            "Ax",
            "Bx",
            "Ay",
            "Cz",
        ),
        [*lists, lists[0]],
        strict=True,
    ):
        models.ReadingListEntry.objects.create(title=title, reading_list=reading_list)
    term, expected = _FOREIGN_KEY_ORDERINGS[ordering]

    def _union(queryset: QuerySet[Model]) -> QuerySet[Model]:
        return queryset.filter(_starts("title", "A")).union(queryset.filter(_starts("title", "B")))

    pk_for = dict(models.ReadingListEntry.objects.values_list("title", "pk"))
    combinator_rows = _union(models.ReadingListEntry.objects.all()).order_by(term)
    assert [row.pk for row in combinator_rows] == [pk_for[title] for title in expected]
    _install(
        monkeypatch,
        "ReadingListEntryType",
        lambda queryset, info: _union(queryset).order_by(term),
    )

    data = _data(
        "{ allLibraryReadingListEntriesConnection { edges { node { title } } } }",
        optimizer=optimizer,
    )

    edges = data["allLibraryReadingListEntriesConnection"]["edges"]
    assert [edge["node"]["title"] for edge in edges] == expected


# ---------------------------------------------------------------------------
# Refused shapes
# ---------------------------------------------------------------------------


def _a(queryset: QuerySet[Model]):
    return queryset.filter(_starts("name", "A"))


def _b(queryset: QuerySet[Model]):
    return queryset.filter(_starts("name", "B"))


@dataclass(frozen=True)
class _Refused:
    body: Callable[[QuerySet[Model]], QuerySet[Model]]
    fragments: tuple[str, ...]


_REFUSED = {
    "union-all": _Refused(
        lambda qs: _a(qs).union(qs.filter(_holds("name", "i")), all=True),
        ("union: union(all=True) keeps duplicate rows, which a primary-key set cannot",),
    ),
    "branch-annotation": _Refused(
        lambda qs: _a(qs).annotate(rank=Value(1)).union(_b(qs).annotate(rank=Value(2))),
        ("union: a branch selects annotations ('rank') that would be dropped from the rows",),
    ),
    "branch-extra-select": _Refused(
        lambda qs: _a(qs).extra(select={"rank": "1"}).union(_b(qs).extra(select={"rank": "2"})),
        ("union: a branch selects extra(select=...) aliases ('rank') that would be dropped",),
    ),
    "branch-values": _Refused(
        lambda qs: _a(qs).union(_b(qs).values("id", "name")),
        (
            "union: a branch projects .values('id', 'name'), which the primary-key subquery "
            "cannot re-project",
        ),
    ),
    "branch-select-for-update": _Refused(
        lambda qs: _a(qs).select_for_update().union(_b(qs)),
        (
            "union: a branch carries select_for_update(), which the database refuses inside "
            "a compound query",
        ),
    ),
    "outer-order-by-transform": _Refused(
        lambda qs: _a(qs).union(_b(qs)).order_by(Lower("name").desc()),
        (
            "union: its ordering by OrderBy(Lower(F(name)), descending=True) is not a Genre "
            "column, so the rewritten query cannot carry it (it carries a column name or an "
            "F() over a column, with .asc() / .desc(); never a lookup, transform or other "
            "expression)",
        ),
    ),
    "outer-order-by-related-span": _Refused(
        lambda qs: _a(qs).union(_b(qs)).order_by(F("books__title")),
        ("union: its ordering by F(books__title) is not a Genre column",),
    ),
    "outer-order-by-descending-related-span": _Refused(
        lambda qs: _a(qs).union(_b(qs)).order_by(F("books__title").desc()),
        (
            "union: its ordering by OrderBy(F(books__title), descending=True) is not a Genre column",
        ),
    ),
    "nested-branch-annotation": _Refused(
        lambda qs: qs.difference(
            _a(qs).annotate(rank=Value(1)).union(_b(qs).annotate(rank=Value(1))),
        ),
        ("difference: a branch selects annotations ('rank') that would be dropped from the rows",),
    ),
}


@pytest.mark.parametrize("refused", list(_REFUSED))
@pytest.mark.django_db
def test_combined_shape_the_key_set_cannot_carry_is_refused_at_the_field(
    monkeypatch: pytest.MonkeyPatch,
    refused: str,
):
    """A combined hook result whose rows the primary-key set would change fails closed, named.

    The refusal is the field's own GraphQL error: ``data`` is ``null`` for the
    non-null root list, the error's ``path`` is that field, and the message names
    the type, the defect, the combinator and what would be lost. No genre row is
    read.
    """
    _seed_genres()
    shape = _REFUSED[refused]
    _install(monkeypatch, "GenreType", lambda queryset, info: shape.body(queryset))

    with CaptureQueriesContext(connection) as captured:
        payload = _post("{ allLibraryGenresViaListField { name } }")

    assert payload["data"] is None, payload
    [error] = payload["errors"]
    assert error["path"] == ["allLibraryGenresViaListField"]
    message = error["message"]
    assert "GenreType" in message, message
    assert "combined" in message, message
    for fragment in shape.fragments:
        assert fragment in message, message
    assert [q["sql"] for q in captured.captured_queries if "library_genre" in q["sql"]] == []


@pytest.mark.django_db
def test_sliced_combined_hook_is_refused_as_sliced(monkeypatch: pytest.MonkeyPatch):
    """A sliced union on the root list is refused by the ``sliced`` defect."""
    _seed_genres()
    _install(
        monkeypatch,
        "GenreType",
        lambda queryset, info: _a(queryset).union(_b(queryset)).order_by("name")[:2],
    )

    payload = _post("{ allLibraryGenresViaListField { name } }")

    assert payload["data"] is None, payload
    [error] = payload["errors"]
    assert error["path"] == ["allLibraryGenresViaListField"]
    assert "GenreType.get_queryset returned a sliced queryset (rows 0:2)" in error["message"]


@pytest.mark.django_db
def test_refused_combined_shape_is_masked_by_the_production_error_policy(
    monkeypatch: pytest.MonkeyPatch,
):
    """Without ``DEBUG`` the refusal reaches the client as the masked error at the same field."""
    _seed_genres()
    _install(
        monkeypatch,
        "GenreType",
        lambda queryset, info: _a(queryset).union(_b(queryset), all=True),
    )

    response = post_graphql("{ allLibraryGenresViaListField { name } }")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] is None, payload
    [error] = payload["errors"]
    assert error["path"] == ["allLibraryGenresViaListField"]
    assert error["message"] == "An unexpected error occurred."
    assert "union" not in str(error)


def _outer_values(queryset: QuerySet[Model]):
    return (
        queryset.filter(_holds("name", "i")).intersection(queryset.exclude(_starts("name", "Q")))
    ).values("pk")


@pytest.mark.django_db
def test_outer_values_projection_after_a_combinator_is_refused_as_a_projection(
    monkeypatch: pytest.MonkeyPatch,
):
    """On a model-row surface ``intersection(...).values("pk")`` is refused as a projection.

    The projection check runs before the combined rewrite, so the rewrite never turns a
    projected combinator into model rows.
    """
    _seed_genres()
    _install(monkeypatch, "GenreType", lambda queryset, info: _outer_values(queryset))

    payload = _post("{ allLibraryGenresViaListField { name } }")

    assert payload["data"] is None, payload
    [error] = payload["errors"]
    assert error["path"] == ["allLibraryGenresViaListField"]
    assert "GenreType.get_queryset returned a ValuesIterable projection" in error["message"]


@pytest.mark.django_db
def test_outer_values_projection_through_the_cascade_is_refused_as_combined(
    monkeypatch: pytest.MonkeyPatch,
):
    """A cascade target's ``intersection(...).values("pk")`` is refused as ``combined``.

    The cascade accepts a ``.values()`` projection of an uncombined target, so this
    refusal comes from the combinator, not from the projection check.
    """
    _seed_desks()
    _install(
        monkeypatch,
        "ShelfType",
        lambda queryset, info: (
            queryset.filter(_holds("code", "i")).intersection(
                queryset.exclude(_starts("code", "Q")),
            )
        ).values("pk"),
    )

    payload = _post("{ allLibraryCirculationDesks { name } }")

    assert payload["data"] is None, payload
    [error] = payload["errors"]
    assert error["path"] == ["allLibraryCirculationDesks"]
    message = error["message"]
    for fragment in (
        "ShelfType",
        "combined",
        "intersection",
        ".values(",
    ):
        assert fragment in message, message


@pytest.mark.django_db
def test_sliced_combined_hook_on_a_nested_connection_is_refused_naming_the_slice(
    monkeypatch: pytest.MonkeyPatch,
):
    """A sliced union under ``booksConnection`` is refused at plan time as ``combined``.

    The nested-connection child's seal licenses a slice of an uncombined queryset,
    but a slice cannot ride inside the primary-key subquery a combinator is served
    through, so the rewrite refuses it while the root field plans.
    """
    _seed_books()
    _install(
        monkeypatch,
        "BookType",
        lambda queryset, info: (
            queryset.filter(_starts("title", "A"))
            .union(queryset.filter(_starts("title", "B")))
            .order_by("title")[:2]
        ),
    )

    payload = _post(_NESTED_CONNECTION)

    assert payload["data"] is None, payload
    [error] = payload["errors"]
    assert error["path"] == ["allLibraryGenres"]
    assert "BookType.get_queryset returned a combined queryset" in error["message"]
    assert "union: it is sliced" in error["message"]


def _hinted_shelf_schema(books: QuerySet[Model]) -> DjangoSchema:
    """A holder shelf type whose ``books`` hint is ``OptimizerHint.prefetch(Prefetch(books))``.

    No shipped type can carry a consumer ``Prefetch`` hint without changing the
    example schema, so the pair is declared here; the registry is cleared first and
    the acceptance conftest rebuilds the project registrations after the test.
    """
    registry.clear()
    make_django_type("HintBookType", models.Book, ("id", "title"), node=False)

    class HintShelfType(DjangoType):
        class Meta:
            model = models.Shelf
            fields = ("id", "code", "books")
            optimizer_hints = {
                "books": OptimizerHint.prefetch(Prefetch("books", queryset=books)),
            }

    finalize_django_types()

    @strawberry.type
    class Query:
        shelves: list[HintShelfType] = DjangoListField(HintShelfType)

    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(query=Query, config=strawberry_config(), extensions=[lambda: optimizer])


@_EVERY_SHAPE
@pytest.mark.django_db
def test_hinted_prefetch_of_a_combined_queryset_serves_its_rows(shape: str):
    """``OptimizerHint.prefetch(Prefetch("books", queryset=<combined>))`` serves the kept books."""
    _seed_books()
    results = {}
    for combined in (True, False):
        chosen = _SHAPES[shape].combined if combined else _SHAPES[shape].uncombined
        schema = _hinted_shelf_schema(chosen(models.Book.objects.all(), "title"))
        results[combined] = _data("{ shelves { code books { title } } }", schema=schema)

    assert _order_free(results[True]) == _order_free(results[False])
    assert {
        row["code"]: sorted(book["title"] for book in row["books"])
        for row in results[True]["shelves"]
    } == {
        code: sorted(t for t in titles if t in _VISIBLE[shape])
        for code, titles in _BOOKS_BY_SHELF.items()
    }
