"""Live GraphQL HTTP tests for the library acceptance app."""

import base64
import importlib
import sys

import pytest
from apps.library import models
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches
from strawberry import relay

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


def _post_graphql(query: str, *, client: Client | None = None):
    graphql_client = client or Client()
    return graphql_client.post(
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
def test_library_patron_bigint_lifetime_fines_over_http():
    """``Patron.lifetime_fines_cents`` survives a value past JS safe-integer range.

    Pins the ``BigIntegerField -> BigInt`` converter row end-to-end at a value
    that JSON would lose precision on if serialized as a number. Companion to
    ``apps.scalars`` which exercises the full converter table; this test
    proves the converter row keeps working on a real-domain model and not
    just the dedicated coverage app.
    """
    # 2**53 + 12345 — past JS safe-integer (``2**53 - 1``) so a numeric
    # round-trip would lose precision; the only correct wire format is the
    # decimal string.
    large_value = 9007199254752336
    models.Patron.objects.create(name="Mae", lifetime_fines_cents=large_value)

    response = _post_graphql(
        """
        query {
          allLibraryPatrons {
            name
            lifetimeFinesCents
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    rows = body["data"]["allLibraryPatrons"]
    mae = next(row for row in rows if row["name"] == "Mae")
    assert mae["lifetimeFinesCents"] == str(large_value)


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
    # Slice 4 added ShelfType.get_queryset for the H1-rev4 nested-visibility
    # contract; the optimizer correctly downgrades select_related("shelf") to
    # Prefetch so the visibility hook applies before the join surfaces hidden
    # rows. Two queries — one for the books, one prefetch for shelves through
    # the visibility-scoped queryset.
    assert len(captured) == 2
    book_sql = captured[0]["sql"]
    shelf_sql = captured[1]["sql"]
    assert "library_book" in book_sql
    assert "library_shelf" in shelf_sql


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


@pytest.mark.django_db
def test_library_branches_via_djangolistfield_optimized_nested_selection():
    """End-to-end pipeline coverage for ``DjangoListField`` via ``/graphql/``.

    Pins the Slice 4 end-to-end contract (spec-016 Decision 4 + rev3 M6,
    spec-016 #"live HTTP test in `examples/fakeshop/test_query/test_library_api.py` covers"):
    URL routing + view + schema execution + JSON serialization + optimizer
    cooperation through the real Django + Strawberry HTTP stack. The package-
    internal return-shape contract is pinned separately by
    ``tests/test_list_field.py::test_djangolistfield_at_root_position_is_optimized``
    (rev2 M3, spec-016 #"Pinned by `test_djangolistfield_at_root_position_is_optimized`").

    Query count derivation (rev6 M6, spec-016 #"pin the assertion to exact query count" — exact ``assertNumQueries(N)``):
      * 1 SELECT for the ``Branch`` root queryset (the ``DjangoListField``
        default resolver returns ``Branch._default_manager.all()``; the
        root-gated ``DjangoOptimizerExtension`` plans
        ``prefetch_related("shelves")`` for the nested ``shelves`` selection).
      * 1 SELECT for the planned ``prefetch_related("shelves")`` prefetch
        (loads all ``Shelf`` rows for the two seeded branches).
      * 2 SELECTs (one per seeded ``Branch``) for the consumer-override
        ``BranchType.shelves`` resolver at ``apps/library/schema.py`` (which
        evaluates ``self.shelves.order_by("-code")`` and bypasses the
        prefetch cache). This mirrors the baseline established by
        ``test_library_relation_override_shapes_http_response_data`` above
        for the same nested-selection shape.

    Total: 1 + 1 + 2 = 4 queries. If a future maintainer adds ``order_by`` to
    the new field, removes the consumer override on ``BranchType.shelves``, or
    changes the seeded branch count, recompute N accordingly.
    """
    _seed_branch_with_two_shelves("ListField West")
    _seed_branch_with_two_shelves("ListField East")

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryBranchesViaListField {
                id
                name
                shelves { id code }
              }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    branches = payload["data"]["allLibraryBranchesViaListField"]
    # Order-agnostic comparison: the new field has no ``order_by`` (rev2 M1 —
    # the add-only posture deliberately does NOT inherit ``order_by("id")``
    # from the sibling ``all_library_branches`` resolver because the new field
    # exercises the default-resolver code path, not a consumer resolver).
    branches_by_name = {b["name"]: b for b in branches}
    assert set(branches_by_name) == {"ListField West", "ListField East"}
    for branch in branches_by_name.values():
        assert {shelf["code"] for shelf in branch["shelves"]} == {"A-1", "B-2"}
    assert len(captured) == 4
    assert "library_branch" in captured[0]["sql"]
    assert "library_shelf" in captured[1]["sql"]
    assert "library_shelf" in captured[2]["sql"]
    assert "library_shelf" in captured[3]["sql"]


@pytest.mark.django_db
def test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http():
    """End-to-end ``Manager → QuerySet`` coercion via a sync consumer ``resolver=``.

    Pins ``django_strawberry_framework/list_field.py::_post_process_consumer_sync #"result = result.all()"`` — the field-wrapper's
    ``_post_process_consumer_sync`` ``Manager.all()`` coercion before
    ``_apply_get_queryset_sync`` runs (rev4 M1). The fakeshop resolver
    ``apps.library.schema._branches_manager_resolver`` returns
    ``Branch.objects`` (a ``Manager``, NOT a ``QuerySet``); rows coming
    back through ``/graphql/`` prove the wrapper coerced and applied the
    default-identity ``get_queryset``. The README rule at
    ``examples/fakeshop/test_query/README.md #"Coverage rule"`` requires this coverage
    to land here, not in the package-internal ``tests/test_list_field.py``.
    """
    _seed_branch_with_two_shelves("ManagerResolver West")
    _seed_branch_with_two_shelves("ManagerResolver East")

    response = _post_graphql(
        "{ allLibraryBranchesViaListFieldManagerResolver { id name } }",
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    names = {branch["name"] for branch in payload["data"]["allLibraryBranchesViaListFieldManagerResolver"]}
    assert names == {"ManagerResolver West", "ManagerResolver East"}


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


# ---------------------------------------------------------------------------
# Slice 4 — live HTTP filter coverage (spec-021 L1044-1057).
# ---------------------------------------------------------------------------


def _post_graphql_as_staff(query: str):
    """Issue a GraphQL POST authenticated as a freshly-created staff user."""
    user_model = get_user_model()
    staff = user_model.objects.create_user(
        username="staff",
        password="pw",
        is_staff=True,
    )
    client = Client()
    client.force_login(staff)
    return _post_graphql(query, client=client)


@pytest.mark.django_db
def test_library_branches_filter_by_name_icontains():
    """Spec-021 L1044: scalar-field filter clause + ``iContains`` lookup name."""
    models.Branch.objects.create(name="Andromeda Main", city="Boston")
    models.Branch.objects.create(name="Side Branch", city="Cambridge")

    _assert_graphql_data(
        """
        query {
          allLibraryBranches(filter: { name: { iContains: "main" } }) {
            name
          }
        }
        """,
        {"allLibraryBranches": [{"name": "Andromeda Main"}]},
    )


@pytest.mark.django_db
def test_library_books_filter_by_choice_enum():
    """Spec-021 L1045: choice-enum filter clause coerces via Strawberry enum."""
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    models.Book.objects.create(
        title="Foundation",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.AVAILABLE,
    )
    models.Book.objects.create(
        title="Kindred",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.CHECKED_OUT,
    )

    _assert_graphql_data(
        """
        query {
          allLibraryBooks(filter: { circulationStatus: { exact: available } }) {
            title
          }
        }
        """,
        {"allLibraryBooks": [{"title": "Foundation"}]},
    )


@pytest.mark.django_db
def test_library_books_filter_by_non_relay_fk_scalar_id():
    """Spec-021 L1046: ``ShelfType`` is non-Relay so ``shelf.id`` is a scalar PK."""
    branch_a = models.Branch.objects.create(name="Branch A", city="Boston")
    branch_b = models.Branch.objects.create(name="Branch B", city="Cambridge")
    shelf_a = models.Shelf.objects.create(code="A-1", topic="general", branch=branch_a)
    shelf_b = models.Shelf.objects.create(code="B-1", topic="general", branch=branch_b)
    models.Book.objects.create(title="On Shelf A", shelf=shelf_a)
    models.Book.objects.create(title="On Shelf B", shelf=shelf_b)

    _assert_graphql_data(
        f"""
        query {{
          allLibraryBooks(filter: {{ shelf: {{ id: {{ exact: {shelf_a.pk} }} }} }}) {{
            title
          }}
        }}
        """,
        {"allLibraryBooks": [{"title": "On Shelf A"}]},
    )


@pytest.mark.django_db
def test_library_books_filter_by_relay_m2m_global_id():
    """Spec-021 L1047: ``GenreType`` is Relay-Node so ``genres.id`` is a GlobalID."""
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    sci_fi = models.Genre.objects.create(name="SciFi")
    other = models.Genre.objects.create(name="Other")
    sci_fi_book = models.Book.objects.create(title="Hyperion", shelf=shelf)
    sci_fi_book.genres.add(sci_fi)
    other_book = models.Book.objects.create(title="Boring", shelf=shelf)
    other_book.genres.add(other)

    global_id = str(relay.GlobalID(type_name="GenreType", node_id=str(sci_fi.pk)))
    _assert_graphql_data(
        f"""
        query {{
          allLibraryBooks(filter: {{ genres: {{ id: {{ exact: "{global_id}" }} }} }}) {{
            title
          }}
        }}
        """,
        {"allLibraryBooks": [{"title": "Hyperion"}]},
    )


@pytest.mark.django_db
def test_library_branches_filter_by_reverse_fk_lookup():
    """Spec-021 L1048: reverse-FK filter (``shelves.code``) routes through ``ShelfFilter``."""
    branch_with = models.Branch.objects.create(name="With Match", city="Boston")
    branch_without = models.Branch.objects.create(name="Without Match", city="Boston")
    # ``BranchFilter.shelves`` carries the explicit ``queryset=Shelf.objects.filter(
    # topic="permanent collection")`` constraint per spec-021 L1051 — seed both
    # shelves under that topic so only the per-shelf code clause narrows the
    # result; the topic-scope test (#8) inverts this pattern.
    models.Shelf.objects.create(code="A-Main", topic="permanent collection", branch=branch_with)
    models.Shelf.objects.create(
        code="B-2",
        topic="permanent collection",
        branch=branch_without,
    )

    response = _post_graphql(
        """
        query {
          allLibraryBranches(filter: { shelves: { code: { iContains: "A" } } }) {
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    names = [b["name"] for b in payload["data"]["allLibraryBranches"]]
    assert names == ["With Match"]


@pytest.mark.django_db
def test_library_books_filter_combines_and_or_not():
    """Spec-021 L1049: ``and_`` / ``not_`` Python attrs surface as ``and`` / ``not``."""
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    models.Book.objects.create(
        title="Foundation",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.AVAILABLE,
    )
    models.Book.objects.create(
        title="Kindred",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.CHECKED_OUT,
    )
    models.Book.objects.create(
        title="Foundation Annotated",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.CHECKED_OUT,
    )

    _assert_graphql_data(
        """
        query {
          allLibraryBooks(filter: {
            and: [
              { title: { iContains: "Foundation" } },
              { not: { circulationStatus: { exact: checked_out } } }
            ]
          }) {
            title
          }
        }
        """,
        {"allLibraryBooks": [{"title": "Foundation"}]},
    )


@pytest.mark.django_db
def test_library_books_filter_preserves_optimizer_cooperation():
    """Spec-021 L1050: ``select_related`` / ``prefetch_related`` survive ``.filter(...)``."""
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    sci_fi = models.Genre.objects.create(name="SciFi")
    available = models.Book.objects.create(
        title="Foundation",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.AVAILABLE,
    )
    available.genres.add(sci_fi)
    checked_out = models.Book.objects.create(
        title="Kindred",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.CHECKED_OUT,
    )
    checked_out.genres.add(sci_fi)

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryBooks(filter: { circulationStatus: { exact: available } }) {
                title
                shelf { code }
                genres { name }
              }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    rows = payload["data"]["allLibraryBooks"]
    assert [row["title"] for row in rows] == ["Foundation"]
    assert rows[0]["shelf"] == {"code": "A-1"}
    assert rows[0]["genres"] == [{"name": "SciFi"}]
    # Optimizer plans the relations under filter cooperation: a root book
    # SELECT, a ``select_related("shelf")`` JOINed pull, and the
    # ``prefetch_related("genres")`` SELECT. The filter clause itself
    # adds no additional queries — the count survives ``.filter(...)``
    # per spec-021 L1050.
    assert len(captured) == 3
    joined_sql = "\n".join(query["sql"] for query in captured)
    assert "library_book" in joined_sql
    assert "library_shelf" in joined_sql
    assert "library_book_genres" in joined_sql


@pytest.mark.django_db
def test_library_branches_filter_respects_related_queryset_boundary_on_parent():
    """Spec-021 L1051: ``RelatedFilter(queryset=...)`` scopes the parent only."""
    branch_a = models.Branch.objects.create(name="Branch A", city="Cambridge")
    branch_b = models.Branch.objects.create(name="Branch B", city="Cambridge")
    models.Shelf.objects.create(code="A-1", topic="permanent collection", branch=branch_a)
    models.Shelf.objects.create(code="A-2", topic="seasonal", branch=branch_a)
    models.Shelf.objects.create(code="A-3", topic="seasonal", branch=branch_b)

    response = _post_graphql(
        """
        query {
          allLibraryBranches(filter: { shelves: { code: { iContains: "A" } } }) {
            name
            shelves { code topic }
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    rows = payload["data"]["allLibraryBranches"]
    # (a) ``branch_B`` is EXCLUDED — no shelf with ``topic="permanent collection"``.
    assert [row["name"] for row in rows] == ["Branch A"]
    # (b) and (c) ``branch_A`` is INCLUDED and its consumer-authored ``shelves``
    # resolver returns BOTH shelves (the constraint scopes the parent
    # filter, NOT the nested resolver's output).
    assert sorted(shelf["code"] for shelf in rows[0]["shelves"]) == ["A-1", "A-2"]


@pytest.mark.django_db
def test_book_genres_uses_absolute_import_path_related_filter():
    """Spec-021 L1052: ``BookFilter.genres`` resolves via the Layer-2 absolute path."""
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    sci_fi = models.Genre.objects.create(name="SciFi")
    other = models.Genre.objects.create(name="Other")
    sci_fi_book = models.Book.objects.create(title="Hyperion", shelf=shelf)
    sci_fi_book.genres.add(sci_fi)
    other_book = models.Book.objects.create(title="Boring", shelf=shelf)
    other_book.genres.add(other)

    _assert_graphql_data(
        """
        query {
          allLibraryBooks(filter: { genres: { name: { exact: "SciFi" } } }) {
            title
          }
        }
        """,
        {"allLibraryBooks": [{"title": "Hyperion"}]},
    )


@pytest.mark.django_db
def test_nested_related_filter_honors_target_get_queryset():
    """Spec-021 L1053 (H1-rev4): nested ``RelatedFilter`` honors target visibility.

    Uses ``BookFilter.shelf`` (no explicit ``queryset=`` constraint) so the
    nested visibility hook on ``ShelfType.get_queryset`` is the only gate
    being exercised. ``BranchFilter.shelves`` carries an explicit
    ``queryset=Shelf.objects.filter(topic="permanent collection")``
    constraint that test #8 pins separately — running both contracts
    through the same query path would double up the gates.
    """
    branch = models.Branch.objects.create(name="Branch", city="Cambridge")
    visible_shelf = models.Shelf.objects.create(code="A", topic="general", branch=branch)
    hidden_shelf = models.Shelf.objects.create(code="B", topic="secret", branch=branch)
    models.Book.objects.create(title="Visible Book", shelf=visible_shelf)
    models.Book.objects.create(title="Hidden Book", shelf=hidden_shelf)

    # Anonymous: ``ShelfType.get_queryset`` strips ``topic="secret"``, so
    # asking for the hidden shelf yields no books (the ``<rel>__in``
    # constraint built from the visibility-scoped child queryset is
    # empty); asking for the visible shelf returns its book.
    hidden_query_response = _post_graphql(
        f"""
        query {{
          allLibraryBooks(filter: {{ shelf: {{ id: {{ exact: {hidden_shelf.pk} }} }} }}) {{
            title
          }}
        }}
        """,
    )
    assert hidden_query_response.status_code == 200
    hidden_payload = hidden_query_response.json()
    assert "errors" not in hidden_payload, hidden_payload
    assert hidden_payload["data"]["allLibraryBooks"] == []

    visible_query_response = _post_graphql(
        f"""
        query {{
          allLibraryBooks(filter: {{ shelf: {{ id: {{ exact: {visible_shelf.pk} }} }} }}) {{
            title
          }}
        }}
        """,
    )
    assert visible_query_response.status_code == 200
    visible_payload = visible_query_response.json()
    assert "errors" not in visible_payload, visible_payload
    assert [row["title"] for row in visible_payload["data"]["allLibraryBooks"]] == [
        "Visible Book",
    ]

    # Staff: the hidden shelf reappears so the hidden book matches.
    staff_response = _post_graphql_as_staff(
        f"""
        query {{
          allLibraryBooks(filter: {{ shelf: {{ id: {{ exact: {hidden_shelf.pk} }} }} }}) {{
            title
          }}
        }}
        """,
    )
    assert staff_response.status_code == 200
    staff_payload = staff_response.json()
    assert "errors" not in staff_payload, staff_payload
    assert [row["title"] for row in staff_payload["data"]["allLibraryBooks"]] == [
        "Hidden Book",
    ]


@pytest.mark.django_db
def test_apply_raises_graphqlerror_on_invalid_filter_input():
    """Spec-021 L1054 (H4-rev8): form-validation rejection surfaces ``FILTER_INVALID``."""
    models.Patron.objects.create(name="Ada", email="ada@example.com")

    response = _post_graphql(
        """
        query {
          allLibraryPatrons(filter: { emailMustHaveAtSign: { exact: "bogus" } }) {
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" in payload, payload
    error = payload["errors"][0]
    assert error["message"] == "Invalid filter input"
    extensions = error["extensions"]
    assert extensions["code"] == "FILTER_INVALID"
    field_errors = extensions["errors"]["email_must_have_at_sign"]
    assert any("missing @" in entry["message"] for entry in field_errors)
    assert any(entry["code"] == "missing_at_sign" for entry in field_errors)


@pytest.mark.django_db
def test_apply_passes_graphql_enum_coercion_before_form_validation():
    """Spec-021 L1055 (H4-rev8 companion): enum coercion fires before form validation."""
    response = _post_graphql(
        """
        query {
          allLibraryBooks(filter: { circulationStatus: { exact: NOT_A_REAL_ENUM_VALUE } }) {
            title
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" in payload, payload
    error = payload["errors"][0]
    # GraphQL parser-level enum-coercion error names the offending value and
    # the enum type; the message wording is set by graphql-core and may
    # change across versions, so assert on substrings only.
    assert "NOT_A_REAL_ENUM_VALUE" in error["message"]
    assert "BookTypeCirculationStatusEnum" in error["message"]
    # The distinct error layer pinned by this test: coercion-level errors
    # do NOT carry the ``FILTER_INVALID`` extension code.
    assert error.get("extensions", {}).get("code") != "FILTER_INVALID"


@pytest.mark.django_db
def test_root_get_queryset_runs_before_filter_apply():
    """Spec-021 L1056 (M5-rev4 + M1-rev8): ``get_queryset`` runs before ``apply``."""
    models.Branch.objects.create(name="Andromeda Main", city="Boston")
    models.Branch.objects.create(name="Andromeda Restricted", city="restricted")

    # Anonymous: ``BranchType.get_queryset`` strips the restricted row so the
    # ``iContains: "andromeda"`` clause runs against the visibility-scoped
    # queryset and matches only the surviving row.
    response = _post_graphql(
        """
        query {
          allLibraryBranches(filter: { name: { iContains: "andromeda" } }) {
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert [row["name"] for row in payload["data"]["allLibraryBranches"]] == ["Andromeda Main"]

    # Staff: both branches reappear under the same filter clause.
    staff_response = _post_graphql_as_staff(
        """
        query {
          allLibraryBranches(filter: { name: { iContains: "andromeda" } }) {
            name
          }
        }
        """,
    )
    assert staff_response.status_code == 200
    staff_payload = staff_response.json()
    assert "errors" not in staff_payload, staff_payload
    staff_names = sorted(row["name"] for row in staff_payload["data"]["allLibraryBranches"])
    assert staff_names == ["Andromeda Main", "Andromeda Restricted"]


@pytest.mark.django_db
def test_relay_global_id_filter_rejects_wrong_type_name():
    """Spec-021 L1057 (M6-rev4): mismatched GlobalID ``type_name`` is rejected."""
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    sci_fi = models.Genre.objects.create(name="SciFi")
    book = models.Book.objects.create(title="Hyperion", shelf=shelf)
    book.genres.add(sci_fi)

    right_id = str(relay.GlobalID(type_name="GenreType", node_id=str(sci_fi.pk)))
    wrong_id = str(relay.GlobalID(type_name="LoanType", node_id=str(sci_fi.pk)))

    wrong_response = _post_graphql(
        f"""
        query {{
          allLibraryBooks(filter: {{ genres: {{ id: {{ exact: "{wrong_id}" }} }} }}) {{
            title
          }}
        }}
        """,
    )
    assert wrong_response.status_code == 200
    wrong_payload = wrong_response.json()
    assert "errors" in wrong_payload, wrong_payload
    message = wrong_payload["errors"][0]["message"]
    assert "GlobalID type mismatch" in message
    assert "GenreType" in message
    assert "LoanType" in message

    right_response = _post_graphql(
        f"""
        query {{
          allLibraryBooks(filter: {{ genres: {{ id: {{ exact: "{right_id}" }} }} }}) {{
            title
          }}
        }}
        """,
    )
    assert right_response.status_code == 200
    right_payload = right_response.json()
    assert "errors" not in right_payload, right_payload
    assert [row["title"] for row in right_payload["data"]["allLibraryBooks"]] == ["Hyperion"]
