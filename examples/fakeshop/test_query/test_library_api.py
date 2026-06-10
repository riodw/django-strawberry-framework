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


def _reload_library_project_schema() -> None:
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


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests():
    """Recreate the project schema around package-test registry clears."""
    _reload_library_project_schema()


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


def _input_field_names(type_name: str) -> set[str]:
    response = _post_graphql(
        f"""
        query {{
          __type(name: "{type_name}") {{
            inputFields {{ name }}
          }}
        }}
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    type_info = payload["data"]["__type"]
    assert type_info is not None
    return {field["name"] for field in type_info["inputFields"]}


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
                                    "shelf": {"code": "A-1", "branch": {"name": "Central"}},
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
                    "card": {"barcode": "CARD-1", "patron": {"name": "Ada"}},
                    "loans": [
                        {
                            "note": "first checkout",
                            "book": {"title": "Kindred", "genres": [{"name": "Speculative"}]},
                        },
                    ],
                },
                {"name": "Grace", "card": None, "loans": []},
            ],
            "allLibraryGenres": [
                {
                    "name": "Speculative",
                    "books": [
                        {
                            "title": "Kindred",
                            "shelf": {"code": "A-1", "branch": {"name": "Central"}},
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
    # 2**53 + 12345 - past JS safe-integer (``2**53 - 1``) so a numeric
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
                {"title": "Kindred", "shelf": {"code": "A-1"}},
            ],
        },
    }
    # Slice 4 added ShelfType.get_queryset for the H1-rev4 nested-visibility
    # contract; the optimizer correctly downgrades select_related("shelf") to
    # Prefetch so the visibility hook applies before the join surfaces hidden
    # rows. Two queries - one for the books, one prefetch for shelves through
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
                        {"title": "Kindred", "genres": [{"name": "Speculative"}]},
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
                {"title": "Kindred", "subtitle": None, "circulationStatus": "checked_out"},
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
    assert subtitle_type == {"kind": "SCALAR", "name": "String", "ofType": None}


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
                {"name": "Override", "shelves": [{"code": "B-2"}, {"code": "A-1"}]},
                {"name": "Override East", "shelves": [{"code": "B-2"}, {"code": "A-1"}]},
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

    Query count derivation (rev6 M6, spec-016 #"pin the assertion to exact query count" - exact ``assertNumQueries(N)``):
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
    # Order-agnostic comparison: the new field has no ``order_by`` (rev2 M1 -
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
    """End-to-end ``Manager -> QuerySet`` coercion via a sync consumer ``resolver=``.

    Pins ``django_strawberry_framework/list_field.py::_post_process_consumer_sync #"result = result.all()"`` - the field-wrapper's
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
    names = {
        branch["name"]
        for branch in payload["data"]["allLibraryBranchesViaListFieldManagerResolver"]
    }
    assert names == {"ManagerResolver West", "ManagerResolver East"}


@pytest.mark.django_db
def test_library_branches_via_djangolistfield_nullable_outer_renders_and_resolves():
    """A ``list[BranchType] | None`` DjangoListField renders nullable-outer and still resolves.

    Live counterpart of the (removed) package test
    ``tests/test_list_field.py::test_djangolistfield_nullable_outer_via_consumer_annotation``,
    promoted to this tier per ``test_query/README.md`` (the shape is reachable from a live
    ``/graphql/`` introspection query). The consumer's ``list[BranchType] | None`` class
    annotation - NOT a constructor argument - must drive the rendered GraphQL type to
    ``[BranchType!]`` (a ``LIST`` whose outer ``NON_NULL`` wrapper is ABSENT, vs the sibling
    non-nullable field's ``NON_NULL`` outer). ``DjangoListField`` itself has no
    outer-nullability branch, so the same ``list_field.py`` lines stay pinned by the
    package companion ``test_djangolistfield_non_nullable_outer_default_via_consumer_annotation``;
    this live test adds the real-stack pressure the throwaway-schema package test lacked -
    introspection over the *composed* schema plus an end-to-end resolve over the wire.
    """
    # Introspection over the real composed schema: outer LIST is nullable (no NON_NULL
    # wrapper); the inner item stays NON_NULL.
    introspection = _post_graphql(
        '{ __type(name: "Query") { fields { name type '
        "{ kind ofType { kind ofType { kind name } } } } } }",
    )
    assert introspection.status_code == 200
    ibody = introspection.json()
    assert "errors" not in ibody, ibody
    fields = {f["name"]: f["type"] for f in ibody["data"]["__type"]["fields"]}
    nullable = fields["allLibraryBranchesViaListFieldNullable"]
    assert nullable["kind"] == "LIST"  # outer NON_NULL absent -> nullable list
    assert nullable["ofType"]["kind"] == "NON_NULL"
    assert nullable["ofType"]["ofType"]["kind"] == "OBJECT"
    assert nullable["ofType"]["ofType"]["name"] == "BranchType"
    # Load-bearing contrast: the sibling non-nullable field DOES wrap the list in NON_NULL.
    assert fields["allLibraryBranchesViaListField"]["kind"] == "NON_NULL"

    # End-to-end resolve: the nullable-outer field still returns a real list over the wire.
    _seed_branch_with_two_shelves("Nullable West")
    response = _post_graphql("query { allLibraryBranchesViaListFieldNullable { id name } }")
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    names = {b["name"] for b in body["data"]["allLibraryBranchesViaListFieldNullable"]}
    assert "Nullable West" in names


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
    # Under the 0.0.9 model-label default the GlobalID carries the Django model
    # label (``library.genre``), not the GraphQL type name ``GenreType``.
    assert type_name == models.Genre._meta.label_lower
    assert node_id == str(genre.pk)
    assert genres[0]["name"] == "Speculative"


# ---------------------------------------------------------------------------
# Slice 4 - live HTTP filter coverage (spec-021 L1044-1057).
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


def test_hide_flat_filters_changes_library_filter_input_shape_over_http(settings):
    """``HIDE_FLAT_FILTERS`` changes the real GraphQL input shape exposed at ``/graphql/``."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"HIDE_FLAT_FILTERS": False}
    _reload_library_project_schema()
    shown = _input_field_names("BranchFilterInputType")
    assert "shelves" in shown
    assert "shelvesCode" in shown

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"HIDE_FLAT_FILTERS": True}
    _reload_library_project_schema()
    hidden = _input_field_names("BranchFilterInputType")
    assert "shelves" in hidden
    assert "shelvesCode" not in hidden


@pytest.mark.django_db
def test_library_branches_empty_filter_input_is_noop_over_http():
    """An empty GraphQL filter input behaves like no filter while preserving root visibility."""
    models.Branch.objects.create(name="Visible", city="Boston")
    models.Branch.objects.create(name="Restricted", city="restricted")

    _assert_graphql_data(
        """
        query {
          unfiltered: allLibraryBranches {
            name
          }
          filtered: allLibraryBranches(filter: {}) {
            name
          }
        }
        """,
        {"unfiltered": [{"name": "Visible"}], "filtered": [{"name": "Visible"}]},
    )


@pytest.mark.django_db
def test_library_branches_not_filter_respects_root_visibility_over_http():
    """``not`` filtering runs inside the root ``get_queryset`` visibility scope."""
    models.Branch.objects.create(name="x-row", city="Boston")
    models.Branch.objects.create(name="keep-1", city="Boston")
    models.Branch.objects.create(name="keep-2", city="Boston")
    models.Branch.objects.create(name="Hidden", city="restricted")

    _assert_graphql_data(
        """
        query {
          allLibraryBranches(filter: { not: { name: { exact: "x-row" } } }) {
            name
          }
        }
        """,
        {"allLibraryBranches": [{"name": "keep-1"}, {"name": "keep-2"}]},
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
def test_library_books_filter_by_choice_enum_in():
    """Spec-021 H2: a choice column's ``in`` lookup keeps its enum element type.

    Regression for the CSV (``BaseInFilter``) branch collapsing a choice
    column's ``in`` element to ``String`` -- so ``{ in: [available] }`` failed
    coercion ("String cannot represent ... available") while ``exact``
    correctly used the enum. The element type now comes from the model field,
    so the shared ``BookTypeCirculationStatusEnum`` is reused.
    """
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
          allLibraryBooks(filter: { circulationStatus: { in: [available] } }) {
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

    global_id = str(
        relay.GlobalID(type_name=models.Genre._meta.label_lower, node_id=str(sci_fi.pk)),
    )
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
def test_library_genres_filter_by_relay_own_pk_global_id_in_list():
    """Own-PK Relay ``id: {in: [...]}`` accepts a LIST of GlobalIDs (H5 + M1 E2E).

    ``GenreType`` is a Relay node, so ``GenreFilter.id`` is a GlobalID. The
    ``in`` lookup must take a *list*: the resolved filter is
    ``GlobalIDMultipleChoiceFilter`` (cardinality, H5a), its form field
    accepts the submitted list instead of rejecting it against an empty
    ``choices`` set (H5b), and each element is decoded + type-validated
    before the ``id__in`` clause runs (M1). Previously the own-PK branch
    collapsed every lookup to a single ``GlobalIDFilter`` and ``in`` could
    not take a list at all.
    """
    sci_fi = models.Genre.objects.create(name="SciFi")
    fantasy = models.Genre.objects.create(name="Fantasy")
    models.Genre.objects.create(name="Mystery")

    gid_sci_fi = str(
        relay.GlobalID(type_name=models.Genre._meta.label_lower, node_id=str(sci_fi.pk)),
    )
    gid_fantasy = str(
        relay.GlobalID(type_name=models.Genre._meta.label_lower, node_id=str(fantasy.pk)),
    )
    _assert_graphql_data(
        f"""
        query {{
          allLibraryGenres(filter: {{ id: {{ in: ["{gid_sci_fi}", "{gid_fantasy}"] }} }}) {{
            name
          }}
        }}
        """,
        {"allLibraryGenres": [{"name": "SciFi"}, {"name": "Fantasy"}]},
    )


@pytest.mark.django_db
def test_library_genres_filter_by_relay_own_pk_global_id_in_rejects_wrong_type():
    """A wrong-type GlobalID in the ``in`` list is rejected before the query (M1 + H5b).

    Each list element is type-validated against the ``library.genre`` model
    label; a ``library.book`` (``BookType``) GlobalID must raise rather than
    silently decode to a bare node id. Under the 0.0.9 model-label default the
    wrong-model payload is the model label ``library.book``, not ``BookType``.
    """
    genre = models.Genre.objects.create(name="SciFi")
    wrong = str(relay.GlobalID(type_name=models.Book._meta.label_lower, node_id=str(genre.pk)))
    response = _post_graphql(
        f"""
        query {{
          allLibraryGenres(filter: {{ id: {{ in: ["{wrong}"] }} }}) {{
            name
          }}
        }}
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" in payload, payload
    assert "GlobalID type mismatch" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_library_branches_filter_by_reverse_fk_lookup():
    """Spec-021 L1048: reverse-FK filter (``shelves.code``) routes through ``ShelfFilter``."""
    branch_with = models.Branch.objects.create(name="With Match", city="Boston")
    branch_without = models.Branch.objects.create(name="Without Match", city="Boston")
    # ``BranchFilter.shelves`` carries the explicit ``queryset=Shelf.objects.filter(
    # topic="permanent collection")`` constraint per spec-021 L1051 - seed both
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
    # adds no additional queries - the count survives ``.filter(...)``
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
    # (a) ``branch_B`` is EXCLUDED - no shelf with ``topic="permanent collection"``.
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
    constraint that test #8 pins separately - running both contracts
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

    right_id = str(
        relay.GlobalID(type_name=models.Genre._meta.label_lower, node_id=str(sci_fi.pk)),
    )
    wrong_id = str(relay.GlobalID(type_name=models.Loan._meta.label_lower, node_id=str(sci_fi.pk)))

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
    # Under the 0.0.9 model-label default the mismatch message reports the model
    # labels (``library.genre`` expected, ``library.loan`` received), not the
    # GraphQL type names.
    assert "GlobalID type mismatch" in message
    assert models.Genre._meta.label_lower in message
    assert models.Loan._meta.label_lower in message

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


# ---------------------------------------------------------------------------
# Slice 4 - live HTTP order coverage (spec-028 Slice 4 - 14 acceptance tests).
# ---------------------------------------------------------------------------


def _seed_branches_with_varying_shelves():
    """Seed Alpha (shelves A, C, E) + Beta (shelf B), both ``city="Boston"``.

    Load-bearing for the row-preserving reverse-FK ordering contract
    (``docs/feedback.md`` P1-B): ordering by ``shelves: { code: ASC }`` orders
    each Branch by an AGGREGATE of its shelf codes (``Min`` for ASC), so a
    Branch with N shelves appears ONCE -- Alpha (min code A) then Beta (min code
    B) -- not N times.
    """
    alpha = models.Branch.objects.create(name="Alpha", city="Boston")
    beta = models.Branch.objects.create(name="Beta", city="Boston")
    models.Shelf.objects.create(code="A", topic="general", branch=alpha)
    models.Shelf.objects.create(code="C", topic="general", branch=alpha)
    models.Shelf.objects.create(code="E", topic="general", branch=alpha)
    models.Shelf.objects.create(code="B", topic="general", branch=beta)


def _seed_books_with_nullable_subtitles():
    """Seed one nullable-subtitle book + two non-null-subtitle books.

    Load-bearing for the ``NULLS_FIRST`` / ``NULLS_LAST`` contracts per
    spec-028 Slice 4 Test 2 (B3-rev3): the null row must move to the
    requested edge, while the two non-null rows still prove ASC versus
    DESC ordering inside the non-null partition.
    """
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    models.Book.objects.create(title="Null Title", subtitle=None, shelf=shelf)
    models.Book.objects.create(
        title="Alpha Subtitle Title",
        subtitle="A Short Subtitle",
        shelf=shelf,
    )
    models.Book.objects.create(
        title="Zulu Subtitle Title",
        subtitle="Z Long Subtitle",
        shelf=shelf,
    )


@pytest.mark.django_db
def test_library_branches_order_by_name_asc():
    """Spec-028 Slice 4 Test 1: scalar ASC on ``Branch.name``.

    Uses staff context because ``BranchOrder.check_name_permission``
    (declared in ``apps.library.orders``) denies anonymous requests
    that order by ``name``; the gate is load-bearing for Test 9, and
    the spec's intent for Test 1 is to assert the ASC ordering
    contract -- the bypass-on-staff path is the canonical way to
    exercise the contract while leaving the gate intact.
    """
    models.Branch.objects.create(name="Bravo", city="Boston")
    models.Branch.objects.create(name="Alpha", city="Boston")
    models.Branch.objects.create(name="Charlie", city="Boston")

    response = _post_graphql_as_staff(
        """
        query {
          allLibraryBranches(orderBy: [{ name: ASC }]) {
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    names = [row["name"] for row in payload["data"]["allLibraryBranches"]]
    assert names == ["Alpha", "Bravo", "Charlie"]


@pytest.mark.parametrize(
    ("direction", "expected_subtitles"),
    [
        ("ASC_NULLS_FIRST", [None, "A Short Subtitle", "Z Long Subtitle"]),
        ("ASC_NULLS_LAST", ["A Short Subtitle", "Z Long Subtitle", None]),
        ("DESC_NULLS_FIRST", [None, "Z Long Subtitle", "A Short Subtitle"]),
        ("DESC_NULLS_LAST", ["Z Long Subtitle", "A Short Subtitle", None]),
    ],
)
@pytest.mark.django_db
def test_library_books_order_by_subtitle_null_positioning(direction, expected_subtitles):
    """Spec-028 Slice 4 Test 2: NULLS positioning through real ``/graphql/``."""
    _seed_books_with_nullable_subtitles()

    response = _post_graphql(
        f"""
        query {{
          allLibraryBooks(orderBy: [{{ subtitle: {direction} }}]) {{
            title
            subtitle
          }}
        }}
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    rows = payload["data"]["allLibraryBooks"]
    assert [row["subtitle"] for row in rows] == expected_subtitles


@pytest.mark.django_db
def test_library_books_order_by_forward_fk_relation():
    """Spec-028 Slice 4 Test 3: forward-FK nested ``shelf: { code: ASC }``.

    Exercises the same-module ``RelatedOrder("ShelfOrder")``
    declaration on ``BookOrder.shelf``.
    """
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf_c = models.Shelf.objects.create(code="C", topic="general", branch=branch)
    shelf_a = models.Shelf.objects.create(code="A", topic="general", branch=branch)
    shelf_b = models.Shelf.objects.create(code="B", topic="general", branch=branch)
    models.Book.objects.create(title="Book on C", shelf=shelf_c)
    models.Book.objects.create(title="Book on A", shelf=shelf_a)
    models.Book.objects.create(title="Book on B", shelf=shelf_b)

    _assert_graphql_data(
        """
        query {
          allLibraryBooks(orderBy: [{ shelf: { code: ASC } }]) {
            shelf { code }
          }
        }
        """,
        {
            "allLibraryBooks": [
                {"shelf": {"code": "A"}},
                {"shelf": {"code": "B"}},
                {"shelf": {"code": "C"}},
            ],
        },
    )


@pytest.mark.django_db
def test_library_branches_order_by_reverse_fk_relation():
    """Spec-028 Slice 4 Test 4: reverse-FK ordering is row-preserving (aggregate).

    Alpha branch has shelves A, C, E; Beta branch has shelf B. Ordering by
    ``shelves: { code: ASC }`` orders each Branch by an AGGREGATE of its shelf
    codes (``Min`` for ASC) rather than a raw fan-out JOIN, so a Branch with N
    shelves appears ONCE, not N times: Alpha (min code A) then Beta (min code
    B).

    Corrected contract per ``docs/feedback.md`` P1-B. The old raw
    ``order_by("shelves__code")`` multiplied parent rows (one per child), which
    silently corrupted cursors / ``totalCount`` on a connection. ``OrderSet``
    now orders to-many paths by ``Min`` / ``Max`` of the child column so the
    parent row is not multiplied; ``DjangoListField`` (this field) and
    ``DjangoConnectionField`` both get the row-preserving result.

    Uses staff context because ``BranchOrder.check_shelves_permission``
    (declared in ``apps.library.orders``) denies anonymous requests that order
    by the ``shelves`` RelatedOrder branch.
    """
    _seed_branches_with_varying_shelves()

    response = _post_graphql_as_staff(
        """
        query {
          allLibraryBranches(orderBy: [{ shelves: { code: ASC } }]) {
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    names = [row["name"] for row in payload["data"]["allLibraryBranches"]]
    assert names == ["Alpha", "Beta"]


@pytest.mark.django_db
def test_library_branches_order_by_scalar_then_to_many_aggregate_no_multiplication():
    """Mixed scalar + to-many-aggregate ``orderBy`` executes and preserves rows (P1-B).

    A mixed order input -- a scalar term (``city``) followed by a to-many
    ``RelatedOrder`` term (``shelves: { code: ASC }``) -- compiles to
    ``.annotate(<alias>=Min("shelves__code")).order_by("city", <alias>)``: a
    ``GROUP BY`` on the parent that ALSO orders by a non-aggregate scalar
    column. This live query exercises that GROUP-BY functional-dependency shape
    end-to-end (``docs/feedback.md`` round-2 follow-up): the unit test in
    ``tests/orders/test_sets.py`` asserts the expression SHAPE, while this
    asserts the EXECUTED result on a real backend, and proves both terms are
    load-bearing AND no parent row is multiplied despite multi-shelf branches.

    Seed -- each branch's MIN shelf code in parentheses:
      West  (Austin; shelves A + Z -> min A)
      South (Austin; shelf  C      -> min C)
      North (Boston; shelves B + D -> min B)

    ``[{ city: ASC }, { shelves: { code: ASC } }]`` groups by city first
    (Austin before Boston), then breaks the Austin tie by the min shelf code
    (West min A before South min C)::

        ["West", "South", "North"]

    Aggregate-ONLY ordering would be ``["West"(A), "North"(B), "South"(C)]``, so
    the result distinguishes the mixed order from a single-term order -- the
    scalar term is genuinely primary. West and North each own two shelves, so a
    raw fan-out JOIN would list each twice; the aggregate keeps every parent
    single.

    Uses staff context because ``BranchOrder.check_shelves_permission``
    (declared in ``apps.library.orders``) denies anonymous requests that order
    by the ``shelves`` RelatedOrder branch.
    """
    west = models.Branch.objects.create(name="West", city="Austin")
    south = models.Branch.objects.create(name="South", city="Austin")
    north = models.Branch.objects.create(name="North", city="Boston")
    models.Shelf.objects.create(code="A", topic="general", branch=west)
    models.Shelf.objects.create(code="Z", topic="general", branch=west)
    models.Shelf.objects.create(code="C", topic="general", branch=south)
    models.Shelf.objects.create(code="B", topic="general", branch=north)
    models.Shelf.objects.create(code="D", topic="general", branch=north)

    response = _post_graphql_as_staff(
        """
        query {
          allLibraryBranches(orderBy: [{ city: ASC }, { shelves: { code: ASC } }]) {
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    names = [row["name"] for row in payload["data"]["allLibraryBranches"]]
    # city ASC primary (Austin < Boston), shelf-min ASC tiebreaker within Austin
    # (West min A < South min C) -- distinct from aggregate-only ["West","North","South"].
    assert names == ["West", "South", "North"]
    # No parent multiplied despite West/North each owning two shelves.
    assert len(names) == len(set(names))


@pytest.mark.django_db
def test_library_books_order_by_m2m_absolute_import_path():
    """Spec-028 Slice 4 Test 5: M2M order via Layer-2 absolute-import-path.

    ``BookOrder.genres = RelatedOrder("apps.library.orders_genre.GenreOrder")``
    exercises the ``import_string`` first-attempt branch -- the
    absolute-import-path Layer-2 lazy-resolution path.
    """
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    mystery = models.Genre.objects.create(name="Mystery")
    fantasy = models.Genre.objects.create(name="Fantasy")
    sci_fi = models.Genre.objects.create(name="SciFi")
    book_m = models.Book.objects.create(title="Mystery Book", shelf=shelf)
    book_m.genres.add(mystery)
    book_f = models.Book.objects.create(title="Fantasy Book", shelf=shelf)
    book_f.genres.add(fantasy)
    book_s = models.Book.objects.create(title="SciFi Book", shelf=shelf)
    book_s.genres.add(sci_fi)

    _assert_graphql_data(
        """
        query {
          allLibraryBooks(orderBy: [{ genres: { name: ASC } }]) {
            title
          }
        }
        """,
        {
            "allLibraryBooks": [
                {"title": "Fantasy Book"},
                {"title": "Mystery Book"},
                {"title": "SciFi Book"},
            ],
        },
    )


@pytest.mark.django_db
def test_library_books_filter_and_order_compose():
    """Spec-028 Slice 4 Test 6: filter + order compose cleanly.

    ``{ circulationStatus: { exact: available } }`` narrows the rows;
    ``orderBy: [{ title: ASC }]`` arranges the survivors.
    """
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    models.Book.objects.create(
        title="Beta Title",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.AVAILABLE,
    )
    models.Book.objects.create(
        title="Alpha Title",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.AVAILABLE,
    )
    models.Book.objects.create(
        title="Gamma Title",
        shelf=shelf,
        circulation_status=models.Book.CirculationStatus.CHECKED_OUT,
    )

    _assert_graphql_data(
        """
        query {
          allLibraryBooks(
            filter: { circulationStatus: { exact: available } }
            orderBy: [{ title: ASC }]
          ) {
            title
            circulationStatus
          }
        }
        """,
        {
            "allLibraryBooks": [
                {"title": "Alpha Title", "circulationStatus": "available"},
                {"title": "Beta Title", "circulationStatus": "available"},
            ],
        },
    )


@pytest.mark.django_db
def test_library_books_order_preserves_optimizer_cooperation():
    """Spec-028 Slice 4 Test 7 (H2-rev1): ``order_by(...)`` survives the optimizer plan.

    ``select_related("shelf")`` + ``prefetch_related("genres")`` survive
    ``.order_by(...)``; the query count is identical to the shipped
    filter-only test (3 queries: root SELECT + ``select_related("shelf")``
    JOIN + ``prefetch_related("genres")`` SELECT).
    """
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
              allLibraryBooks(
                filter: { circulationStatus: { exact: available } }
                orderBy: [{ title: ASC }]
              ) {
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
    # Optimizer cooperation: ``.order_by(...)`` does NOT add to the
    # query count; the plan stays at root SELECT + shelf JOIN +
    # genres prefetch.
    assert len(captured) == 3


@pytest.mark.django_db
def test_root_get_queryset_runs_before_order_apply():
    """Spec-028 Slice 4 Test 8: root ``get_queryset`` runs before ``apply_sync``.

    ``BranchType.get_queryset`` strips ``city="restricted"`` for
    anonymous users so the DESC order clause sees only the visible
    rows. Staff bypass the gate and see all rows ordered.

    Spec line 1038 names ``name: DESC`` as the order field, but
    ``BranchOrder.check_name_permission`` (declared per spec line
    1039) denies anonymous queries on ``name`` -- the gate fires
    before ``get_queryset`` returns rows would matter. To pin the
    Test 8 contract (visibility scope BEFORE order arrangement)
    without colliding with the Test 9 gate, this test orders by
    ``city: DESC`` (an unguarded scalar). The same Branch+city
    fixture pinned by the spec proves the contract: the
    ``city="restricted"`` row is hidden by ``get_queryset`` and so
    does NOT appear at the head of the descending order list. Same
    spec-reconciliation flag Worker 1 raised for Test 11's quiet
    half (substitute ``city`` for ``name`` when the ``name`` gate
    would denial-trigger).
    """
    models.Branch.objects.create(name="Alpha", city="Boston")
    models.Branch.objects.create(name="Zeta", city="restricted")

    response = _post_graphql(
        """
        query {
          allLibraryBranches(orderBy: [{ city: DESC }]) {
            name
            city
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    rows = payload["data"]["allLibraryBranches"]
    # The hidden ``Zeta`` (``city="restricted"``) does NOT appear at
    # the head of the DESC list; the visibility scope ran BEFORE the
    # order clause.
    assert [row["name"] for row in rows] == ["Alpha"]
    assert rows[0]["city"] == "Boston"

    staff_response = _post_graphql_as_staff(
        """
        query {
          allLibraryBranches(orderBy: [{ city: DESC }]) {
            name
            city
          }
        }
        """,
    )
    assert staff_response.status_code == 200
    staff_payload = staff_response.json()
    assert "errors" not in staff_payload, staff_payload
    staff_rows = staff_payload["data"]["allLibraryBranches"]
    # Staff bypasses the visibility hook so both rows order
    # descending: "restricted" > "Boston" lexically.
    assert [row["name"] for row in staff_rows] == ["Zeta", "Alpha"]


@pytest.mark.django_db
def test_order_check_permission_denies_for_active_field():
    """Spec-028 Slice 4 Test 9 (M6-rev1): scalar gate fires for active field.

    ``BranchOrder.check_name_permission`` fires for anonymous request
    because ``name`` is active in the input; the gate raises
    ``GraphQLError`` with ``code="ORDER_PERMISSION_DENIED"``.
    """
    models.Branch.objects.create(name="Alpha", city="Boston")

    response = _post_graphql(
        """
        query {
          allLibraryBranches(orderBy: [{ name: ASC }]) {
            id
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" in payload, payload
    assert payload["errors"][0]["extensions"]["code"] == "ORDER_PERMISSION_DENIED"


@pytest.mark.django_db
def test_order_check_permission_quiet_for_inactive_field():
    """Spec-028 Slice 4 Test 10 (M6-rev1): scalar gate quiet for inactive field.

    ``BranchOrder.check_name_permission`` does NOT fire because
    ``name`` is absent from the input; the only active field is
    ``city`` (unguarded), so the query succeeds and rows order by
    city ascending.
    """
    models.Branch.objects.create(name="Alpha", city="Boston")
    models.Branch.objects.create(name="Beta", city="Cambridge")

    response = _post_graphql(
        """
        query {
          allLibraryBranches(orderBy: [{ city: ASC }]) {
            city
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    cities = [row["city"] for row in payload["data"]["allLibraryBranches"]]
    assert cities == ["Boston", "Cambridge"]


@pytest.mark.django_db
def test_order_check_permission_denies_active_related_branch():
    """Spec-028 Slice 4 Test 11 (H3-rev3): active-branch relation-level gate.

    ``BranchOrder.check_shelves_permission`` fires when the ``shelves``
    RelatedOrder branch is active in the input; quiet when the branch
    is absent. The quiet half uses ``city`` (unguarded scalar) per
    Worker 1's spec-reconciliation note -- ``name`` collides with the
    Test 9 / 10 gate, so the quiet half routes around it.
    """
    branch = models.Branch.objects.create(name="Alpha", city="Boston")
    models.Shelf.objects.create(code="A-1", topic="general", branch=branch)

    denial_response = _post_graphql(
        """
        query {
          allLibraryBranches(orderBy: [{ shelves: { code: ASC } }]) {
            id
          }
        }
        """,
    )
    assert denial_response.status_code == 200
    denial_payload = denial_response.json()
    assert "errors" in denial_payload, denial_payload
    assert denial_payload["errors"][0]["extensions"]["code"] == "ORDER_PERMISSION_DENIED"

    quiet_response = _post_graphql(
        """
        query {
          allLibraryBranches(orderBy: [{ city: ASC }]) {
            city
          }
        }
        """,
    )
    assert quiet_response.status_code == 200
    quiet_payload = quiet_response.json()
    assert "errors" not in quiet_payload, quiet_payload
    assert [row["city"] for row in quiet_payload["data"]["allLibraryBranches"]] == [
        "Boston",
    ]


@pytest.mark.django_db
def test_library_books_order_by_multi_field_priority():
    """Spec-028 Slice 4 Test 12: multi-field priority via list-element ordering.

    ``orderBy: [{ shelf: { code: ASC } }, { title: DESC }]`` -- shelf
    code dominates (ASC); title is the secondary tie-breaker (DESC,
    so ``Foo`` before ``Bar``).
    """
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf_a = models.Shelf.objects.create(code="A", topic="general", branch=branch)
    shelf_b = models.Shelf.objects.create(code="B", topic="general", branch=branch)
    models.Book.objects.create(title="Foo", shelf=shelf_a)
    models.Book.objects.create(title="Bar", shelf=shelf_a)
    models.Book.objects.create(title="Foo", shelf=shelf_b)
    models.Book.objects.create(title="Bar", shelf=shelf_b)

    response = _post_graphql(
        """
        query {
          allLibraryBooks(
            orderBy: [{ shelf: { code: ASC } }, { title: DESC }]
          ) {
            title
            shelf { code }
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    rows = payload["data"]["allLibraryBooks"]
    assert [(row["shelf"]["code"], row["title"]) for row in rows] == [
        ("A", "Foo"),
        ("A", "Bar"),
        ("B", "Foo"),
        ("B", "Bar"),
    ]


@pytest.mark.django_db
def test_library_books_order_by_flat_shorthand_path():
    """Spec-028 Slice 4 Test 13 (M2-rev1): flat-shorthand ``shelfCode: ASC``.

    ``BookOrder.Meta.fields = [..., "shelf__code"]`` renders as
    ``shelfCode: Ordering`` on the GraphQL input type; the runtime
    normalizer reconstructs the Django ORM path as ``shelf__code``.
    Row-order assertion pins the contract.
    """
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf_c = models.Shelf.objects.create(code="C", topic="general", branch=branch)
    shelf_a = models.Shelf.objects.create(code="A", topic="general", branch=branch)
    shelf_b = models.Shelf.objects.create(code="B", topic="general", branch=branch)
    models.Book.objects.create(title="Book on C", shelf=shelf_c)
    models.Book.objects.create(title="Book on A", shelf=shelf_a)
    models.Book.objects.create(title="Book on B", shelf=shelf_b)

    _assert_graphql_data(
        """
        query {
          allLibraryBooks(orderBy: [{ shelfCode: ASC }]) {
            title
          }
        }
        """,
        {
            "allLibraryBooks": [
                {"title": "Book on A"},
                {"title": "Book on B"},
                {"title": "Book on C"},
            ],
        },
    )


@pytest.mark.django_db
def test_library_branches_order_empty_list_and_null_direction_no_op():
    """Spec-028 Slice 4 Test 14 (M7-rev1): combined empty-list + null-direction no-op.

    Both halves return the queryset in its default resolver-level
    order (``models.Branch.objects.order_by("id")``) without raising.

    - Empty-list half: ``orderBy: []`` -- ``_normalize_input`` returns
      an empty list and ``apply_sync`` returns the queryset unchanged.
    - Null-direction half: ``orderBy: [{ name: null }]`` -- the null
      direction decodes to ``None`` in the Strawberry input and the
      apply pipeline filters ``None`` directions before
      ``queryset.order_by(...)``.
    """
    models.Branch.objects.create(name="Bravo", city="Boston")
    models.Branch.objects.create(name="Alpha", city="Boston")
    models.Branch.objects.create(name="Charlie", city="Boston")

    empty_response = _post_graphql(
        """
        query {
          allLibraryBranches(orderBy: []) {
            name
          }
        }
        """,
    )
    assert empty_response.status_code == 200
    empty_payload = empty_response.json()
    assert "errors" not in empty_payload, empty_payload
    empty_names = [row["name"] for row in empty_payload["data"]["allLibraryBranches"]]
    assert empty_names == ["Bravo", "Alpha", "Charlie"]

    null_response = _post_graphql(
        """
        query {
          allLibraryBranches(orderBy: [{ name: null }]) {
            name
          }
        }
        """,
    )
    assert null_response.status_code == 200
    null_payload = null_response.json()
    assert "errors" not in null_payload, null_payload
    null_names = [row["name"] for row in null_payload["data"]["allLibraryBranches"]]
    assert null_names == ["Bravo", "Alpha", "Charlie"]


# ---------------------------------------------------------------------------
# spec-029 Slice 3 - Meta.nullable_overrides / Meta.required_overrides
#
# Live HTTP coverage against the acceptance-only ``NullabilityOverrideBookType``
# secondary type on ``library.Book``: the SDL flip (title String! -> String,
# subtitle String -> String!) proves the override decouples GraphQL nullability
# from the Django column without an AlterField; the data query proves the
# forced ``subtitle = String!`` invariant holds at the boundary (the resolver
# excludes null-subtitle rows). The existing ``BookType`` baseline above stays
# untouched.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_nullability_override_flips_sdl_nullability():
    """The override flips the acceptance type's SDL nullability, columns unchanged."""
    _seed_library_graph()

    response = _post_graphql(
        """
        query {
          __type(name: "NullabilityOverrideBookType") {
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
    payload = response.json()
    assert "errors" not in payload, payload
    type_info = payload["data"]["__type"]
    assert type_info is not None

    # title: NOT NULL column natively String! -> flipped to String by nullable_overrides.
    title_type = _field_type(type_info, "title")
    assert title_type == {"kind": "SCALAR", "name": "String", "ofType": None}
    # subtitle: null=True column natively String -> flipped to String! by required_overrides.
    subtitle_type = _field_type(type_info, "subtitle")
    assert subtitle_type["kind"] == "NON_NULL"
    assert subtitle_type["ofType"] == {"kind": "SCALAR", "name": "String"}

    # The override changes only the GraphQL contract; the Django columns are unchanged.
    assert models.Book._meta.get_field("title").null is False
    assert models.Book._meta.get_field("subtitle").null is True


@pytest.mark.django_db
def test_nullability_override_acceptance_api_is_queryable():
    """The dedicated root field is queryable with no errors over non-null-subtitle rows.

    The autouse seed creates a ``subtitle=None`` book; this test adds a book
    WITH a non-null subtitle so the resolver's
    ``exclude(subtitle__isnull=True)`` returns a row and the forced
    ``subtitle = String!`` contract holds at the boundary (a null subtitle
    would surface a non-null violation otherwise).
    """
    _seed_library_graph()
    shelf = models.Shelf.objects.first()
    models.Book.objects.create(
        title="Parable of the Sower",
        subtitle="Earthseed",
        circulation_status=models.Book.CirculationStatus.CHECKED_OUT,
        shelf=shelf,
    )

    response = _post_graphql(
        """
        query {
          allLibraryNullabilityOverrideBooks {
            title
            subtitle
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    rows = payload["data"]["allLibraryNullabilityOverrideBooks"]
    # Only the non-null-subtitle row survives the resolver's exclude().
    assert rows == [{"title": "Parable of the Sower", "subtitle": "Earthseed"}]


# ---------------------------------------------------------------------------
# spec-030 Slice 4 - live DjangoConnectionField HTTP coverage.
#
# ``allLibraryGenresConnection`` is the root ``DjangoConnectionField(GenreType)``
# field (``Meta.connection = {"total_count": True}``, ``GenreFilter`` /
# ``GenreOrder`` sidecars). These tests exercise the Relay surface end-to-end
# through the sync ``/graphql/`` view: cursor pagination + ordering + filter +
# the pre-slice post-filter ``totalCount``, the ``first`` + ``last`` guard, the
# ``first: 0`` empty-window shape, ``totalCount`` selection-gating, and the
# per-instance count across two aliases.
# ---------------------------------------------------------------------------


def _seed_genres(*names: str) -> None:
    """Seed library ``Genre`` rows inline (library inline-create rule, no services)."""
    for name in names:
        models.Genre.objects.create(name=name)


@pytest.mark.django_db
def test_genre_connection_full_round_trip():
    """(a) filter + orderBy + first + after round-trip with pre-slice totalCount.

    Seeds five genres; the ``icontains: "a"`` filter matches four of them
    (``Alpha`` / ``Gamma`` / ``Delta`` / ``Banana``) and excludes ``Echo``, so
    ``totalCount`` (the unpaginated post-filter count) is 4 - distinct from both
    the grand total (5) and the page size (2). Page 1 (``first: 2``) returns the
    first two in ``name ASC`` order; ``after: <page-1 endCursor>`` advances to the
    next two with no overlap.
    """
    _seed_genres("Alpha", "Gamma", "Echo", "Delta", "Banana")
    # Post-filter (``icontains "a"``) set in name-ASC order:
    # Alpha, Banana, Delta, Gamma (Echo excluded).

    page_one = _post_graphql(
        """
        query {
          allLibraryGenresConnection(
            filter: { name: { iContains: "a" } }
            orderBy: [{ name: ASC }]
            first: 2
          ) {
            edges { node { id name } }
            pageInfo { hasNextPage endCursor }
            totalCount
          }
        }
        """,
    )
    assert page_one.status_code == 200
    payload_one = page_one.json()
    assert "errors" not in payload_one, payload_one
    conn_one = payload_one["data"]["allLibraryGenresConnection"]

    names_one = [edge["node"]["name"] for edge in conn_one["edges"]]
    assert names_one == ["Alpha", "Banana"]
    # ``node.id`` is a decodable model-label GlobalID (``library.genre``), not
    # the raw pk, under the 0.0.9 model-label default.
    for edge in conn_one["edges"]:
        type_name, node_id = _decode_global_id(edge["node"]["id"])
        assert type_name == models.Genre._meta.label_lower
        assert node_id.isdigit()
    assert conn_one["pageInfo"]["hasNextPage"] is True
    end_cursor = conn_one["pageInfo"]["endCursor"]
    assert isinstance(end_cursor, str) and end_cursor
    # ``totalCount`` counts the unpaginated post-filter set (4), NOT the page
    # size (2) and NOT the grand total (5).
    assert conn_one["totalCount"] == 4

    page_two = _post_graphql(
        f"""
        query {{
          allLibraryGenresConnection(
            filter: {{ name: {{ iContains: "a" }} }}
            orderBy: [{{ name: ASC }}]
            first: 2
            after: "{end_cursor}"
          ) {{
            edges {{ node {{ name }} }}
            pageInfo {{ hasNextPage }}
            totalCount
          }}
        }}
        """,
    )
    assert page_two.status_code == 200
    payload_two = page_two.json()
    assert "errors" not in payload_two, payload_two
    conn_two = payload_two["data"]["allLibraryGenresConnection"]

    names_two = [edge["node"]["name"] for edge in conn_two["edges"]]
    # Next page advances with no overlap with page 1.
    assert names_two == ["Delta", "Gamma"]
    assert set(names_two).isdisjoint(set(names_one))
    assert conn_two["pageInfo"]["hasNextPage"] is False
    assert conn_two["totalCount"] == 4


@pytest.mark.django_db
def test_genre_connection_first_and_last_rejected():
    """(b) supplying both ``first`` and ``last`` surfaces the package guard error.

    The package's own ``first`` + ``last`` mutual-exclusivity guard
    (``connection.py::_guard_first_and_last``) lands as a GraphQL ``errors``
    entry on a 200 response, NOT a non-200 HTTP status (Decision 3).
    """
    _seed_genres("Alpha", "Beta", "Gamma")

    response = _post_graphql(
        """
        query {
          allLibraryGenresConnection(first: 1, last: 1) {
            edges { node { id } }
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" in payload, payload
    messages = " ".join(error["message"] for error in payload["errors"])
    assert "mutually exclusive" in messages


@pytest.mark.django_db
def test_genre_connection_first_zero_empty_edges():
    """(c) ``first: 0`` yields empty edges + valid pageInfo, count still pre-slice.

    ``pageInfo`` is delegated to Strawberry's ``ListConnection``; against the
    locked ``0.316.0`` a zero window over a non-empty set overfetches one row,
    drops it, and reports ``hasNextPage: True`` with a null ``endCursor`` (empty
    edges). ``totalCount`` is the pre-slice count, so ``first: 0`` does not zero
    it (the count is selected here, so it runs).
    """
    _seed_genres("Alpha", "Beta", "Gamma")

    response = _post_graphql(
        """
        query {
          allLibraryGenresConnection(first: 0) {
            edges { node { id } }
            pageInfo { hasNextPage endCursor }
            totalCount
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    conn = payload["data"]["allLibraryGenresConnection"]
    assert conn["edges"] == []
    # ListConnection's real first:0-over-rows shape: more rows exist beyond the
    # zero window, so hasNextPage is True; endCursor is null (no edges).
    assert conn["pageInfo"]["hasNextPage"] is True
    assert conn["pageInfo"]["endCursor"] is None
    # Pre-slice count is unaffected by the zero window.
    assert conn["totalCount"] == 3


@pytest.mark.django_db
def test_genre_connection_total_count_omitted_no_count():
    """(d) omitting ``totalCount`` returns a correct count-less response (gating).

    Selection-gating (Decision 4): when ``totalCount`` is not selected, no count
    query runs and the response carries no count field. The ``CaptureQueriesContext``
    assertion is the strongest proof - no ``COUNT(`` SQL is issued - and is robust
    here because the genre connection's only queries are the row fetch and (when
    selected) the count.
    """
    _seed_genres("Alpha", "Beta", "Gamma")

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryGenresConnection(first: 2) {
                edges { node { id name } }
                pageInfo { hasNextPage }
              }
            }
            """,
        )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    conn = payload["data"]["allLibraryGenresConnection"]
    names = [edge["node"]["name"] for edge in conn["edges"]]
    assert names == ["Alpha", "Beta"]
    assert "totalCount" not in conn
    # Selection-gating: no COUNT query is issued when totalCount is unselected.
    assert not any("COUNT(" in query["sql"].upper() for query in captured.captured_queries)


@pytest.mark.django_db
def test_genre_connection_two_aliases_independent_total_counts():
    """(e) two aliases with different filters yield independent totalCounts.

    The count rides the per-connection-instance attribute, NOT a shared
    ``info.context`` stash (Decision 4): ``matchA`` (``icontains "a"``) and
    ``matchZ`` (``icontains "z"``) in one request must report their own filtered
    counts.
    """
    _seed_genres("Alpha", "Banana", "Cobra", "Zephyr")
    # "a": Alpha, Banana, Cobra -> 3; "z": Zephyr -> 1.

    response = _post_graphql(
        """
        query {
          matchA: allLibraryGenresConnection(filter: { name: { iContains: "a" } }) {
            totalCount
            edges { node { name } }
          }
          matchZ: allLibraryGenresConnection(filter: { name: { iContains: "z" } }) {
            totalCount
            edges { node { name } }
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    data = payload["data"]
    assert data["matchA"]["totalCount"] == 3
    assert data["matchZ"]["totalCount"] == 1


@pytest.mark.django_db
def test_genre_connection_order_by_to_many_no_node_multiplication():
    """Ordering the connection by a to-many relation does not multiply nodes (P1-B).

    ``GenreOrder.books`` is a reverse-M2M ``RelatedOrder``; ordering the genre
    connection by ``books: { title: ASC }`` orders each Genre by an AGGREGATE of
    its book titles (``Min`` for ASC) rather than a fan-out JOIN. A Genre with
    several books therefore appears in ``edges`` exactly ONCE (no duplicate node,
    no skipped distinct node under the positional cursors), and ``totalCount``
    counts DISTINCT genres -- the ``docs/feedback.md`` P1-B contract. The old raw
    ``order_by("books__title")`` form would have listed ``Fiction`` twice (one
    row per book) and inflated ``totalCount``.
    """
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf = models.Shelf.objects.create(code="S-1", topic="general", branch=branch)
    fiction = models.Genre.objects.create(name="Fiction")
    history = models.Genre.objects.create(name="History")
    book_a = models.Book.objects.create(title="Aaa", shelf=shelf)
    book_b = models.Book.objects.create(title="Bbb", shelf=shelf)
    book_c = models.Book.objects.create(title="Ccc", shelf=shelf)
    # Fiction has two books ("Aaa", "Ccc") -> raw JOIN would list it twice.
    book_a.genres.add(fiction)
    book_c.genres.add(fiction)
    book_b.genres.add(history)

    response = _post_graphql(
        """
        query {
          allLibraryGenresConnection(orderBy: [{ books: { title: ASC } }]) {
            edges { node { name } }
            totalCount
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    conn = payload["data"]["allLibraryGenresConnection"]
    names = [edge["node"]["name"] for edge in conn["edges"]]
    # Each genre appears exactly once, ordered by its MIN book title
    # (Fiction "Aaa" < History "Bbb") -- no duplicate Fiction despite two books.
    assert names == ["Fiction", "History"]
    assert len(names) == len(set(names))
    # ``totalCount`` counts DISTINCT genres, not the multiplied (genre x book) rows.
    assert conn["totalCount"] == 2
