"""Live GraphQL HTTP tests for the library acceptance app."""

import base64
import importlib
import sys

import pytest
from apps.library import models
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches

from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests():
    """Recreate imported DjangoType classes if package tests cleared the registry."""
    # This reload is mandatory for order-independent suite isolation:
    # package tests clear the global registry, while the example project
    # schema finalizes import-time DjangoType classes. Reload only schema
    # modules (not apps.library.models) so Django model classes stay stable and
    # DjangoType subclasses are recreated against a fresh registry.
    # Hidden invariant: tests must not module-level import classes from
    # apps.library.schema, or they will hold stale class objects after reload.
    registry.clear()
    library_schema = sys.modules.get("apps.library.schema")
    if library_schema is None:
        importlib.import_module("apps.library.schema")
    else:
        importlib.reload(library_schema)

    project_schema = sys.modules.get("config.schema")
    if project_schema is None:
        importlib.import_module("config.schema")
    else:
        importlib.reload(project_schema)

    urls = sys.modules.get("config.urls")
    if urls is not None:
        importlib.reload(urls)
        clear_url_caches()


def _seed_library_graph():
    branch = models.Branch.objects.create(name="Central", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="Speculative fiction", branch=branch)
    genre = models.Genre.objects.create(name="Speculative")
    book = models.Book.objects.create(
        title="Kindred",
        subtitle=None,
        circulation_status=models.Book.CirculationStatus.CHECKED_OUT,
        shelf=shelf,
    )
    book.genres.add(genre)
    patron = models.Patron.objects.create(name="Ada")
    models.MembershipCard.objects.create(patron=patron, barcode="CARD-1")
    models.Patron.objects.create(name="Grace")
    models.Loan.objects.create(book=book, patron=patron, note="first checkout")


def _seed_branch_with_two_shelves(name: str = "Override"):
    branch = models.Branch.objects.create(name=name, city="Boston")
    models.Shelf.objects.create(code="A-1", topic="First floor", branch=branch)
    models.Shelf.objects.create(code="B-2", topic="Second floor", branch=branch)


def _post_graphql(query: str):
    client = Client()
    return client.post(
        "/graphql/",
        data={"query": query},
        content_type="application/json",
    )


def _assert_graphql_data(query: str, expected: dict):
    response = _post_graphql(query)
    assert response.status_code == 200
    assert response.json() == {"data": expected}
    return response


def _field_type(type_info: dict, field_name: str) -> dict:
    return next(field["type"] for field in type_info["fields"] if field["name"] == field_name)


@pytest.mark.django_db
def test_library_branch_shelf_book_loan_graph_over_http():
    _seed_library_graph()

    _assert_graphql_data(
        """
        query {
          allLibraryBranches {
            name
            city
            shelves {
              code
              topic
              branch { name }
              books {
                title
                subtitle
                circulationStatus
                shelf { code branch { name } }
                genres { name }
                loans { note patron { name card { barcode } } }
              }
            }
          }
        }
        """,
        {
            "allLibraryBranches": [
                {
                    "name": "Central",
                    "city": "Boston",
                    "shelves": [
                        {
                            "code": "A-1",
                            "topic": "Speculative fiction",
                            "branch": {"name": "Central"},
                            "books": [
                                {
                                    "title": "Kindred",
                                    "subtitle": None,
                                    "circulationStatus": "checked_out",
                                    "shelf": {
                                        "code": "A-1",
                                        "branch": {"name": "Central"},
                                    },
                                    "genres": [{"name": "Speculative"}],
                                    "loans": [
                                        {
                                            "note": "first checkout",
                                            "patron": {
                                                "name": "Ada",
                                                "card": {"barcode": "CARD-1"},
                                            },
                                        },
                                    ],
                                },
                            ],
                        },
                    ],
                },
            ],
        },
    )


@pytest.mark.django_db
def test_library_patron_card_and_genre_reverse_paths_over_http():
    _seed_library_graph()

    _assert_graphql_data(
        """
        query {
          allLibraryPatrons {
            name
            card { barcode patron { name } }
            loans { note book { title genres { name } } }
          }
          allLibraryGenres {
            name
            books { title shelf { code branch { name } } }
          }
        }
        """,
        {
            "allLibraryPatrons": [
                {
                    "name": "Ada",
                    "card": {
                        "barcode": "CARD-1",
                        "patron": {"name": "Ada"},
                    },
                    "loans": [
                        {
                            "note": "first checkout",
                            "book": {
                                "title": "Kindred",
                                "genres": [{"name": "Speculative"}],
                            },
                        },
                    ],
                },
                {
                    "name": "Grace",
                    "card": None,
                    "loans": [],
                },
            ],
            "allLibraryGenres": [
                {
                    "name": "Speculative",
                    "books": [
                        {
                            "title": "Kindred",
                            "shelf": {
                                "code": "A-1",
                                "branch": {"name": "Central"},
                            },
                        },
                    ],
                },
            ],
        },
    )


@pytest.mark.django_db
def test_library_optimizer_selects_book_shelf_in_http_query():
    _seed_library_graph()

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryBooks {
                title
                shelf { code }
              }
            }
            """,
        )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "allLibraryBooks": [
                {
                    "title": "Kindred",
                    "shelf": {"code": "A-1"},
                },
            ],
        },
    }
    assert len(captured) == 1
    sql = captured[0]["sql"]
    assert "JOIN" in sql
    assert "library_book" in sql
    assert "library_shelf" in sql


@pytest.mark.django_db
def test_library_reverse_fk_and_m2m_prefetch_sql_shape_over_http():
    _seed_library_graph()

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryShelves {
                code
                books {
                  title
                  genres { name }
                }
              }
            }
            """,
        )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "allLibraryShelves": [
                {
                    "code": "A-1",
                    "books": [
                        {
                            "title": "Kindred",
                            "genres": [{"name": "Speculative"}],
                        },
                    ],
                },
            ],
        },
    }
    assert len(captured) == 3
    sql = "\n".join(query["sql"] for query in captured)
    assert "library_shelf" in sql
    assert "library_book" in sql
    assert "library_book_genres" in sql
    assert "library_genre" in sql


@pytest.mark.django_db
def test_library_choice_enum_and_nullable_subtitle_are_deliberate_http_contracts():
    _seed_library_graph()

    _assert_graphql_data(
        """
        query {
          allLibraryBooks {
            title
            subtitle
            circulationStatus
          }
        }
        """,
        {
            "allLibraryBooks": [
                {
                    "title": "Kindred",
                    "subtitle": None,
                    "circulationStatus": "checked_out",
                },
            ],
        },
    )

    response = _post_graphql(
        """
        query {
          __type(name: "BookType") {
            fields {
              name
              type {
                kind
                name
                ofType { kind name }
              }
            }
          }
        }
        """,
    )
    assert response.status_code == 200
    type_info = response.json()["data"]["__type"]
    circulation_status_type = _field_type(type_info, "circulationStatus")
    assert circulation_status_type["kind"] == "NON_NULL"
    assert circulation_status_type["ofType"] == {
        "kind": "ENUM",
        "name": "BookTypeCirculationStatusEnum",
    }
    subtitle_type = _field_type(type_info, "subtitle")
    assert subtitle_type == {
        "kind": "SCALAR",
        "name": "String",
        "ofType": None,
    }


@pytest.mark.django_db
def test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http():
    _seed_library_graph()

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryPrefetchedBooks {
                title
                shelf { code }
                genres { name }
              }
            }
            """,
        )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "allLibraryPrefetchedBooks": [
                {
                    "title": "Kindred",
                    "shelf": {"code": "A-1"},
                    "genres": [{"name": "Speculative"}],
                },
            ],
        },
    }
    assert len(captured) == 2
    root_sql = captured[0]["sql"]
    prefetch_sql = captured[1]["sql"]
    assert "JOIN" in root_sql
    assert "library_shelf" in root_sql
    assert "library_book_genres" in prefetch_sql
    assert "library_genre" in prefetch_sql


@pytest.mark.django_db
def test_library_optimizer_hints_are_observable_over_http():
    _seed_library_graph()
    book = models.Book.objects.get(title="Kindred")
    second_patron = models.Patron.objects.create(name="Katherine")
    models.Loan.objects.create(book=book, patron=second_patron, note="second checkout")

    with CaptureQueriesContext(connection) as captured_prefetch:
        prefetch_response = _post_graphql(
            """
            query {
              allLibraryLoans {
                book { title }
              }
            }
            """,
        )

    assert prefetch_response.status_code == 200
    assert prefetch_response.json() == {
        "data": {
            "allLibraryLoans": [
                {
                    "book": {"title": "Kindred"},
                },
                {
                    "book": {"title": "Kindred"},
                },
            ],
        },
    }
    assert len(captured_prefetch) == 2
    assert "JOIN" not in captured_prefetch[0]["sql"]
    assert "library_loan" in captured_prefetch[0]["sql"]
    assert "library_book" in captured_prefetch[1]["sql"]

    with CaptureQueriesContext(connection) as captured_skip:
        skip_response = _post_graphql(
            """
            query {
              allLibraryLoans {
                patron { name }
              }
            }
            """,
        )

    assert skip_response.status_code == 200
    assert skip_response.json() == {
        "data": {
            "allLibraryLoans": [
                {
                    "patron": {"name": "Ada"},
                },
                {
                    "patron": {"name": "Katherine"},
                },
            ],
        },
    }
    # SKIP opts out of relation planning, so patron loads are lazy: one
    # root query plus one lookup per Loan row seeded above.
    assert len(captured_skip) == 3
    assert "JOIN" not in captured_skip[0]["sql"]
    assert "library_loan" in captured_skip[0]["sql"]
    assert "library_patron" in captured_skip[1]["sql"]


@pytest.mark.django_db
def test_library_relation_override_shapes_http_response_data():
    _seed_branch_with_two_shelves("Override")
    _seed_branch_with_two_shelves("Override East")

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryBranches {
                name
                shelves { code }
              }
            }
            """,
        )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "allLibraryBranches": [
                {
                    "name": "Override",
                    "shelves": [
                        {"code": "B-2"},
                        {"code": "A-1"},
                    ],
                },
                {
                    "name": "Override East",
                    "shelves": [
                        {"code": "B-2"},
                        {"code": "A-1"},
                    ],
                },
            ],
        },
    }
    # The optimizer still plans the relation, but the consumer override
    # re-shapes it with order_by("-code"), bypassing the prefetched cache.
    # The observable baseline is root query + planned prefetch + one
    # override manager query per Branch row.
    assert len(captured) == 4


def _decode_global_id(global_id: str) -> tuple[str, str]:
    """Decode a Strawberry Relay ``GlobalID`` string into ``(type_name, node_id)``.

    Strawberry encodes ``GlobalID`` as ``base64("TypeName:nodeId")``; this
    test decodes it manually so the HTTP path stays Strawberry-agnostic
    on the assert side.
    """
    decoded = base64.b64decode(global_id.encode()).decode()
    type_name, _, node_id = decoded.partition(":")
    return type_name, node_id


@pytest.mark.django_db
def test_library_relay_node_global_id_round_trips():
    """A library ``GenreType`` declared as a Relay node returns a decodable GlobalID.

    ``apps/library/schema.py::GenreType`` declares ``interfaces = (relay.Node,)``
    in its ``Meta`` block, so the autouse reload fixture is enough to
    exercise the end-to-end Relay path through ``Meta.interfaces``.
    """
    genre = models.Genre.objects.create(name="Speculative")

    response = _post_graphql(
        """
        query {
          allLibraryGenres {
            id
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    genres = payload["data"]["allLibraryGenres"]
    assert len(genres) == 1
    type_name, node_id = _decode_global_id(genres[0]["id"])
    assert type_name == "GenreType"
    assert node_id == str(genre.pk)
    assert genres[0]["name"] == "Speculative"
