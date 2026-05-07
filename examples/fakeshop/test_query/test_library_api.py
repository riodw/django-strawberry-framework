"""Live GraphQL HTTP tests for the library acceptance app."""

import importlib
import sys

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches
from library import models

from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests():
    """Recreate imported DjangoType classes if package tests cleared the registry."""
    registry.clear()
    library_schema = sys.modules.get("library.schema")
    if library_schema is None:
        importlib.import_module("library.schema")
    else:
        importlib.reload(library_schema)

    project_schema = sys.modules.get("schema")
    if project_schema is None:
        importlib.import_module("schema")
    else:
        importlib.reload(project_schema)

    urls = sys.modules.get("urls")
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
