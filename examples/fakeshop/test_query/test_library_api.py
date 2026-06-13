"""Live GraphQL HTTP tests for library relations, optimizer behavior, and Relay fields."""

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
from django_strawberry_framework.testing.relay import global_id_for


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


def _post_graphql(query: str, *, client: Client | None = None, variables: dict | None = None):
    graphql_client = client or Client()
    payload: dict = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    return graphql_client.post(
        "/graphql/",
        data=payload,
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

    Pins ``django_strawberry_framework/utils/querysets.py::normalize_query_source #"source = source.all()"`` - the field-wrapper's
    shared ``Manager.all()`` coercion (reached via ``_post_process_consumer_sync``) before
    ``apply_type_visibility_sync`` runs (rev4 M1). The fakeshop resolver
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


@pytest.mark.django_db
def test_public_patron_exclude_deny_list_shapes_type_and_resolves():
    """``PublicPatronType`` (``Meta.exclude``) drops PII/financial columns; ``PatronType`` keeps them.

    ``PublicPatronType`` selects via a deny-list ``Meta.exclude = ("email",
    "lifetime_fines_cents")`` over the same ``Patron`` model that the primary
    ``PatronType`` selects via an allow-list ``Meta.fields``. This pins both halves
    of the contrast: the excluded columns are absent from the GraphQL type
    (selecting one is a query error), the kept columns resolve, and the primary
    ``PatronType`` is unaffected.
    """
    models.Patron.objects.create(
        name="Ada",
        email="ada@example.com",
        lifetime_fines_cents=1234,
    )

    # 1. Schema shape: the two excluded columns are gone from PublicPatronType,
    #    while the allow-list primary PatronType still carries lifetimeFinesCents.
    response = _post_graphql(
        """
        query {
          public: __type(name: "PublicPatronType") { fields { name } }
          primary: __type(name: "PatronType") { fields { name } }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    public_fields = {field["name"] for field in payload["data"]["public"]["fields"]}
    primary_fields = {field["name"] for field in payload["data"]["primary"]["fields"]}
    assert "email" not in public_fields
    assert "lifetimeFinesCents" not in public_fields
    assert {
        "id",
        "name",
        "card",
        "loans",
    } <= public_fields
    # Contrast: the allow-list primary still exposes the financial column.
    assert "lifetimeFinesCents" in primary_fields

    # 2. Acceptance: the kept columns resolve over the dedicated root field.
    data_response = _post_graphql(
        """
        query {
          allLibraryPublicPatrons {
            name
          }
        }
        """,
    )
    assert data_response.status_code == 200
    data_payload = data_response.json()
    assert "errors" not in data_payload, data_payload
    assert data_payload["data"]["allLibraryPublicPatrons"] == [{"name": "Ada"}]

    # 3. An excluded column is not selectable - the deny-list removed it from the type.
    excluded_response = _post_graphql(
        "query { allLibraryPublicPatrons { lifetimeFinesCents } }",
    )
    excluded_payload = excluded_response.json()
    assert "errors" in excluded_payload, excluded_payload
    assert "lifetimeFinesCents" in str(excluded_payload["errors"])


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
#
# spec-032 Slice 4 - this block is also the live PRIMARY home of the
# cursor-contract conformance matrix (Decision 9; the test_query README
# coverage rule; no Slice-6 dependency - ``allLibraryGenresConnection`` is
# already shipped). ``test_genre_connection_first_zero_empty_edges`` and
# ``test_genre_connection_first_and_last_rejected`` above are the matrix's
# ``first: 0`` and ``first`` + ``last`` pins (re-affirmed, not duplicated);
# the five conformance tests at the end of the block (``test_first_overrun``
# through ``test_backward_pagination_last_before``) complete the matrix. The stale-``after`` test pins ONLY the no-error
# property (Revision 2 P1 - offset cursors encode a position, not row
# identity). All assertions are behavior-only - never SQL shape
# (pre-``033`` posture, Decision 12).
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


def _genres_connection(args: str, selection: str) -> dict:
    """Post one ``allLibraryGenresConnection`` query; return the connection dict.

    Asserts the no-error envelope (HTTP 200, no ``errors`` entry) so every
    caller pins at least the query-succeeds property.
    """
    response = _post_graphql(
        f"query {{ allLibraryGenresConnection({args}) {{ {selection} }} }}",
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    return payload["data"]["allLibraryGenresConnection"]


@pytest.mark.django_db
def test_first_overrun():
    """``first: N`` past the remainder returns the actual remainder (Decision 9).

    Three rows, ``first: 10``: exactly the three rows come back and
    ``hasNextPage`` is false - the overrun is clamped, never an error.
    """
    _seed_genres("Alpha", "Beta", "Gamma")

    conn = _genres_connection(
        "first: 10",
        "edges { node { name } } pageInfo { hasNextPage }",
    )
    assert [edge["node"]["name"] for edge in conn["edges"]] == ["Alpha", "Beta", "Gamma"]
    assert conn["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
def test_stale_after_cursor_no_error():
    """An ``after`` cursor whose row was deleted does NOT error (Revision 2 P1).

    Pins ONLY the no-error property: Strawberry's offset cursors encode a
    position, not row identity, so no skip / duplicate / next-row assertion
    is made - positional stability under deletes is deliberately NOT part of
    the contract (keyset cursors are BACKLOG item 39 sub-feature 3).
    """
    _seed_genres("Alpha", "Beta", "Gamma", "Delta")

    page_one = _genres_connection("first: 2", "pageInfo { endCursor }")
    end_cursor = page_one["pageInfo"]["endCursor"]
    # Delete the row the cursor position points at (the second row in
    # deterministic pk order).
    models.Genre.objects.order_by("pk")[1].delete()

    # The helper's envelope assertions (200 + no ``errors``) ARE the test.
    _genres_connection(
        f'first: 2, after: "{end_cursor}"',
        "edges { node { name } }",
    )


@pytest.mark.django_db
def test_page_info_four_fields():
    """All four ``pageInfo`` fields are correct across a forward page walk.

    Page 1 (``first: 2`` over 3 rows): ``hasNextPage`` true, ``hasPreviousPage``
    false, ``startCursor`` / ``endCursor`` equal to the first / last edge
    cursors. Page 2 (``after`` page 1's ``endCursor``): ``hasNextPage`` false,
    ``hasPreviousPage`` true (Strawberry computes it from slice start > 0).
    """
    _seed_genres("Alpha", "Beta", "Gamma")
    selection = "edges { cursor } pageInfo { hasNextPage hasPreviousPage startCursor endCursor }"

    page_one = _genres_connection("first: 2", selection)
    cursors = [edge["cursor"] for edge in page_one["edges"]]
    info_one = page_one["pageInfo"]
    assert info_one["hasNextPage"] is True
    assert info_one["hasPreviousPage"] is False
    assert info_one["startCursor"] == cursors[0]
    assert info_one["endCursor"] == cursors[1]

    page_two = _genres_connection(f'first: 2, after: "{info_one["endCursor"]}"', selection)
    info_two = page_two["pageInfo"]
    assert info_two["hasNextPage"] is False
    assert info_two["hasPreviousPage"] is True


@pytest.mark.django_db
def test_has_next_page_correct_when_edges_unrequested():
    """A ``pageInfo``-only query (no ``edges`` selection) computes ``hasNextPage``.

    Strawberry's ``should_resolve_list_connection_edges`` takes a distinct
    path when neither ``edges`` nor ``pageInfo`` is selected; a ``pageInfo``-only
    selection must still walk the window and report the flag correctly for
    both a windowed (true) and an exact (false) page (Revision 6 P3 - the
    observable inverse of an unrequested field).
    """
    _seed_genres("Alpha", "Beta", "Gamma")

    windowed = _genres_connection("first: 2", "pageInfo { hasNextPage }")
    assert windowed["pageInfo"]["hasNextPage"] is True

    exact = _genres_connection("first: 3", "pageInfo { hasNextPage }")
    assert exact["pageInfo"]["hasNextPage"] is False


@pytest.mark.django_db
def test_backward_pagination_last_before():
    """``last`` / ``before`` honor the Relay spec (row identity is the contract).

    ``last: 2`` returns the final two rows in order; ``last: 2`` before the
    last row's cursor returns the two rows immediately preceding it. Cursors
    are fed back opaquely from a prior response - never hand-minted
    (Decision 9's opacity contract).
    """
    _seed_genres("Alpha", "Beta", "Gamma", "Delta", "Echo")

    tail = _genres_connection(
        "last: 2",
        "edges { node { name } } pageInfo { hasNextPage hasPreviousPage }",
    )
    assert [edge["node"]["name"] for edge in tail["edges"]] == ["Delta", "Echo"]
    assert tail["pageInfo"]["hasPreviousPage"] is True
    assert tail["pageInfo"]["hasNextPage"] is False

    full = _genres_connection("first: 5", "edges { cursor node { name } }")
    last_row_cursor = full["edges"][-1]["cursor"]
    window = _genres_connection(
        f'last: 2, before: "{last_row_cursor}"',
        "edges { node { name } } pageInfo { hasNextPage hasPreviousPage }",
    )
    assert [edge["node"]["name"] for edge in window["edges"]] == ["Gamma", "Delta"]
    # Locked-Strawberry flag values: rows exist on both sides of the window
    # (the overfetch sees Echo; slice start > 0 sees Alpha / Beta).
    assert window["pageInfo"]["hasNextPage"] is True
    assert window["pageInfo"]["hasPreviousPage"] is True


# ---------------------------------------------------------------------------
# Slice 6 - fakeshop library activation (spec-032 Decision 12): live root
# node(id:) / nodes(ids:) / typed genre(id:) refetch plus the synthesized
# relation-as-Connection surfaces, the mandated live coverage home per the
# test_query README rule. Every test rides the autouse
# _reload_project_schema_for_acceptance_tests fixture; seeding is inline
# Model.objects.create (library rule - no services.py); nested-connection
# assertions are BEHAVIOR only, never SQL shape (pre-033 posture). Book ids
# are minted via testing.relay.global_id_for over IN-TEST-BODY class imports
# (the file-header reload invariant). The spec-named
# test_genres_connection_cursor_round_trip / test_genres_connection_total_count
# contracts are mapped, not duplicated: they are already live-proven by
# test_genre_connection_full_round_trip (endCursor -> after continuation with
# no-overlap + post-filter totalCount) and
# test_genre_connection_first_zero_empty_edges (pre-slice totalCount) above.
# ---------------------------------------------------------------------------


def _seed_shelf() -> models.Shelf:
    """Create one branch + shelf so book fixtures stay inline one-liners."""
    branch = models.Branch.objects.create(name="Relay", city="Boston")
    return models.Shelf.objects.create(code="R-1", topic="Relay fixtures", branch=branch)


def _post_node(global_id: str, selection: str = "__typename") -> dict:
    """Post one bare ``node(id:)`` query; return the full response payload.

    Returns the whole payload (not ``data.node``) so callers can assert the
    presence or absence of ``errors`` per the Decision-5 failure families.
    Pins only the never-a-500 transport contract itself.
    """
    response = _post_graphql(f'query {{ node(id: "{global_id}") {{ {selection} }} }}')
    assert response.status_code == 200
    return response.json()


@pytest.mark.django_db
def test_node_refetch_genre():
    """The bare ``node(id:)`` refetches an emitted Genre GlobalID round-trip.

    The id fed back is the EMITTED wire string from a prior query, never
    hand-minted - the opaque-id realism half of the refetch contract.
    """
    models.Genre.objects.create(name="Speculative")

    listed = _post_graphql("query { allLibraryGenres { id name } }")
    assert listed.status_code == 200
    listed_payload = listed.json()
    assert "errors" not in listed_payload, listed_payload
    emitted = listed_payload["data"]["allLibraryGenres"][0]

    refetched = _post_node(emitted["id"], "... on GenreType { id name }")
    assert "errors" not in refetched, refetched
    assert refetched["data"]["node"] == {"id": emitted["id"], "name": "Speculative"}


@pytest.mark.django_db
def test_typed_node_field_live():
    """The typed ``genre(id:)`` field resolves a genre GlobalID to the row."""
    from apps.library.schema import GenreType

    genre = models.Genre.objects.create(name="Speculative")
    gid = global_id_for(GenreType, genre.pk)

    response = _post_graphql(f'query {{ genre(id: "{gid}") {{ id name }} }}')
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"]["genre"] == {"id": gid, "name": "Speculative"}


@pytest.mark.django_db
def test_typed_node_field_mismatch_live():
    """A book id at the typed ``genre(id:)`` field raises the mismatch error.

    The expected/received-types ``GraphQLError`` (Decision 4): a wrong-type
    id at a typed field is a client bug surfaced loudly, not a ``null``.
    """
    from apps.library.schema import BookType

    book = models.Book.objects.create(title="Kindred", shelf=_seed_shelf())
    book_gid = global_id_for(BookType, book.pk)

    response = _post_graphql(f'query {{ genre(id: "{book_gid}") {{ name }} }}')
    assert response.status_code == 200
    payload = response.json()
    assert "errors" in payload, payload
    messages = " ".join(error["message"] for error in payload["errors"])
    assert "Wrong node type: expected a GenreType id, received a BookType id." in messages


@pytest.mark.django_db
def test_node_malformed_id_live():
    """A malformed id surfaces ``GLOBALID_INVALID`` in-band, never a 500.

    The package-owned conversion (Decision 5) - reachable because the field
    argument is ``strawberry.ID``, so the raw string gets past Strawberry's
    argument conversion to ``decode_global_id`` (Revision 7 P1).
    """
    payload = _post_node("not-base64!!!")
    assert "errors" in payload, payload
    error = payload["errors"][0]
    assert error["extensions"]["code"] == "GLOBALID_INVALID"
    assert error["message"].startswith("Invalid GlobalID:")


@pytest.mark.django_db
def test_node_uncoercible_pk_live():
    """A well-formed payload with an uncoercible pk resolves to ``null``.

    ``library.genre:abc`` decodes cleanly but ``abc`` is not an integer pk -
    the existence-family ``null``, with no errors entry and no 500 leaking
    Django's ``ValueError`` (Revision 7 P2).
    """
    gid = base64.b64encode(b"library.genre:abc").decode()
    payload = _post_node(gid)
    assert "errors" not in payload, payload
    assert payload["data"]["node"] is None


@pytest.mark.django_db
def test_nodes_batch_mixed_types_order_and_null():
    """``nodes(ids:)`` preserves input order across types with a ``null`` hole.

    Genre + book ids interleaved with one WELL-FORMED missing-pk id; the
    hole resolves to a positional ``null``, both real rows resolve to their
    concrete types. (A malformed id mid-batch fails the whole field - pinned
    package-side in tests/test_relay_node_field.py.)
    """
    from apps.library.schema import BookType, GenreType

    genre = models.Genre.objects.create(name="Speculative")
    book = models.Book.objects.create(title="Kindred", shelf=_seed_shelf())
    ids = (
        global_id_for(GenreType, genre.pk),
        global_id_for(GenreType, 999999),
        global_id_for(BookType, book.pk),
    )
    id_literals = ", ".join(f'"{gid}"' for gid in ids)

    response = _post_graphql(
        f"""
        query {{
          nodes(ids: [{id_literals}]) {{
            __typename
            ... on GenreType {{ name }}
            ... on BookType {{ title }}
          }}
        }}
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"]["nodes"] == [
        {"__typename": "GenreType", "name": "Speculative"},
        None,
        {"__typename": "BookType", "title": "Kindred"},
    ]


@pytest.mark.django_db
def test_nodes_duplicates_and_empty_live():
    """Duplicate ids resolve per position; ``ids: []`` returns ``[]``."""
    from apps.library.schema import GenreType

    genre = models.Genre.objects.create(name="Speculative")
    gid = global_id_for(GenreType, genre.pk)

    duplicated = _post_graphql(
        f'query {{ nodes(ids: ["{gid}", "{gid}"]) {{ ... on GenreType {{ name }} }} }}',
    )
    assert duplicated.status_code == 200
    duplicated_payload = duplicated.json()
    assert "errors" not in duplicated_payload, duplicated_payload
    assert duplicated_payload["data"]["nodes"] == [{"name": "Speculative"}] * 2

    empty = _post_graphql("query { nodes(ids: []) { __typename } }")
    assert empty.status_code == 200
    empty_payload = empty.json()
    assert "errors" not in empty_payload, empty_payload
    assert empty_payload["data"]["nodes"] == []


@pytest.mark.django_db
def test_genre_books_connection_behavior():
    """The synthesized reverse-M2M ``booksConnection`` paginates correctly.

    Behavior only (right rows, right order, no overlap) - SQL-shape
    assertions are 033's deliverable. The ``repair`` book also proves the
    target ``BookType.get_queryset`` runs INSIDE the nested connection for
    an anonymous client (the Decision-12 nested visibility bonus).
    """
    genre = models.Genre.objects.create(name="Speculative")
    shelf = _seed_shelf()
    for title in ("Aurora", "Binti", "Circe"):
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)
    hidden = models.Book.objects.create(
        title="Withdrawn",
        circulation_status=models.Book.CirculationStatus.REPAIR,
        shelf=shelf,
    )
    hidden.genres.add(genre)

    def _books_page(args: str) -> dict:
        response = _post_graphql(
            f"""
            query {{
              allLibraryGenres {{
                booksConnection({args}) {{
                  edges {{ node {{ title }} }}
                  pageInfo {{ hasNextPage endCursor }}
                }}
              }}
            }}
            """,
        )
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        return payload["data"]["allLibraryGenres"][0]["booksConnection"]

    page_one = _books_page("orderBy: [{ title: ASC }], first: 2")
    titles_one = [edge["node"]["title"] for edge in page_one["edges"]]
    assert titles_one == ["Aurora", "Binti"]
    assert page_one["pageInfo"]["hasNextPage"] is True

    end_cursor = page_one["pageInfo"]["endCursor"]
    page_two = _books_page(f'orderBy: [{{ title: ASC }}], first: 2, after: "{end_cursor}"')
    titles_two = [edge["node"]["title"] for edge in page_two["edges"]]
    # The continuation advances with no overlap, and the repair row stays
    # hidden from the anonymous client even through the nested connection.
    assert titles_two == ["Circe"]
    assert page_two["pageInfo"]["hasNextPage"] is False
    assert "Withdrawn" not in titles_one + titles_two


@pytest.mark.django_db
def test_book_genres_connection_sidecars_and_total_count():
    """The forward-M2M ``genresConnection`` proves sidecars + totalCount live.

    ``filter:`` / ``orderBy:`` derive from the genre sidecars; ``totalCount``
    resolves because the TARGET ``GenreType`` declares
    ``Meta.connection = {"total_count": True}`` (the type-level contract) and
    counts the unpaginated post-filter set - distinct from both the page
    size (2) and the grand total (4).
    """
    book = models.Book.objects.create(title="Kindred", shelf=_seed_shelf())
    for name in (
        "Gamma",
        "Alpha",
        "Banana",
        "Echo",
    ):
        book.genres.add(models.Genre.objects.create(name=name))

    response = _post_graphql(
        """
        query {
          allLibraryBooks {
            genresConnection(
              filter: { name: { iContains: "a" } }
              orderBy: [{ name: ASC }]
              first: 2
            ) {
              totalCount
              edges { node { name } }
            }
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    conn = payload["data"]["allLibraryBooks"][0]["genresConnection"]
    # ``iContains "a"`` matches Gamma / Alpha / Banana (Echo excluded); the
    # orderBy arranges, the first: 2 window slices.
    assert [edge["node"]["name"] for edge in conn["edges"]] == ["Alpha", "Banana"]
    assert conn["totalCount"] == 3


@pytest.mark.django_db
def test_book_loans_relation_stays_list_only():
    """``BookType.loans`` (reverse FK to non-Relay ``LoanType``) stays list-only.

    The live graceful-degradation proof: no ``loansConnection`` is
    synthesized under the implicit ``"both"`` default because the target is
    not Relay-shaped; ``genresConnection`` in the same field set is the
    positive control.
    """
    introspected = _post_graphql('query { __type(name: "BookType") { fields { name } } }')
    assert introspected.status_code == 200
    introspected_payload = introspected.json()
    assert "errors" not in introspected_payload, introspected_payload
    field_names = {field["name"] for field in introspected_payload["data"]["__type"]["fields"]}
    assert "loans" in field_names
    assert "loansConnection" not in field_names
    assert "genresConnection" in field_names

    book = models.Book.objects.create(title="Kindred", shelf=_seed_shelf())
    patron = models.Patron.objects.create(name="Ada")
    models.Loan.objects.create(book=book, patron=patron, note="first checkout")
    _assert_graphql_data(
        "query { allLibraryBooks { loans { note } } }",
        {"allLibraryBooks": [{"loans": [{"note": "first checkout"}]}]},
    )


@pytest.mark.django_db
def test_node_hidden_row_null_live():
    """A ``get_queryset``-hidden row refetches to ``null``; staff sees the row.

    The Decision-5 headline contract live: the anonymous ``null`` is a
    VISIBILITY outcome indistinguishable from a missing row (no errors
    entry), and the same id resolves for a staff request.
    """
    from apps.library.schema import BookType

    book = models.Book.objects.create(
        title="Withdrawn",
        circulation_status=models.Book.CirculationStatus.REPAIR,
        shelf=_seed_shelf(),
    )
    gid = global_id_for(BookType, book.pk)

    anonymous = _post_node(gid, "... on BookType { title }")
    assert "errors" not in anonymous, anonymous
    assert anonymous["data"]["node"] is None

    staff = _post_graphql_as_staff(
        f'query {{ node(id: "{gid}") {{ ... on BookType {{ title }} }} }}',
    )
    assert staff.status_code == 200
    staff_payload = staff.json()
    assert "errors" not in staff_payload, staff_payload
    assert staff_payload["data"]["node"] == {"title": "Withdrawn"}


# ---------------------------------------------------------------------------
# Slice 5 (spec-033) - live nested-connection SQL-shape coverage.
#
# The spec-032 Slice-6 behavior pins above (test_genre_books_connection_behavior,
# test_book_genres_connection_sidecars_and_total_count) asserted BEHAVIOR ONLY and
# named THIS card as the owner of the deferred SQL-shape pins. The three tests
# below add them, live over /graphql/, riding the
# _reload_project_schema_for_acceptance_tests autouse fixture. No source change.
#
# ``totalCount`` siting (the line-79 reconciliation): ``booksConnection``'s target
# ``BookType`` does NOT declare ``Meta.connection = {"total_count": True}`` (only
# ``GenreType`` does), so the nested-``totalCount``-no-per-parent-COUNT pin rides
# ``allLibraryBooks { genresConnection(first: N) { totalCount ... } }`` (target
# ``GenreType``, ``total_count`` on). The ``booksConnection`` shape (target
# ``BookType``, ``get_queryset`` ``circulation_status="repair"`` filter) carries the
# fixed-query-count and visibility pins.
# ---------------------------------------------------------------------------


def _seed_genre_with_books(name: str, shelf: models.Shelf, titles: tuple[str, ...]) -> None:
    """Create one genre and attach a fresh book per title via the M2M.

    Each genre gets its OWN books (unique titles per genre keep the
    ``(shelf, title)`` unique constraint satisfied) so the windowed
    ``booksConnection`` page is per-parent, not a shared slice.
    """
    genre = models.Genre.objects.create(name=name)
    for title in titles:
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)


# One query string shared across the 3-genre and 10-genre runs of the
# fixed-query-count test (the DRY pin: the two parent-count runs differ only in
# seeding, never in the query). ``totalCount`` is NOT selected on
# ``booksConnection`` - ``BookType`` has no ``Meta.connection`` opt-in, so that
# field does not exist on the type (selecting it is a validation error).
_NESTED_BOOKS_CONNECTION_QUERY = """
query {
  allLibraryGenresConnection {
    edges {
      node {
        booksConnection(first: 2) {
          edges { node { title } }
          pageInfo { hasNextPage }
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
def test_nested_books_connection_fixed_query_count():
    """The two-level genres->books window costs the same for 3 vs 10 parents.

    The literal N+1 disproof: the captured query count for the nested
    ``booksConnection`` window is INDEPENDENT of the number of parent genres
    (spec-033 Slice 5 / Goal 5 / DoD item 8). The window is one prefetch over
    all parents, not one query per parent. ``totalCount`` is not selected -
    ``BookType`` has no ``Meta.connection`` opt-in, so the field does not exist.
    """

    def _run(genre_count: int) -> tuple[int, dict]:
        shelf = _seed_shelf()
        for index in range(genre_count):
            # Per-genre unique titles keep the (shelf, title) unique
            # constraint satisfied while every genre carries >2 books so
            # ``first: 2`` leaves a meaningful ``hasNextPage``.
            _seed_genre_with_books(
                f"Genre-{index}",
                shelf,
                (f"Book-{index}-a", f"Book-{index}-b", f"Book-{index}-c"),
            )
        with CaptureQueriesContext(connection) as captured:
            response = _post_graphql(_NESTED_BOOKS_CONNECTION_QUERY)
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        return len(captured), payload

    three_count, three_payload = _run(3)

    # Wire assertion: every parent genre returns its OWN windowed page of 2
    # books with hasNextPage True (3 books seeded per genre), proving the
    # window is per-parent-correct, not a single shared slice.
    three_edges = three_payload["data"]["allLibraryGenresConnection"]["edges"]
    assert len(three_edges) == 3
    for index, edge in enumerate(three_edges):
        books_conn = edge["node"]["booksConnection"]
        titles = [book_edge["node"]["title"] for book_edge in books_conn["edges"]]
        assert titles == [f"Book-{index}-a", f"Book-{index}-b"]
        assert books_conn["pageInfo"]["hasNextPage"] is True

    # Reset the graph so the 10-genre run starts from an empty library, then
    # re-run the identical query under a fresh capture.
    models.Book.objects.all().delete()
    models.Genre.objects.all().delete()
    models.Shelf.objects.all().delete()
    models.Branch.objects.all().delete()

    ten_count, ten_payload = _run(10)
    assert len(ten_payload["data"]["allLibraryGenresConnection"]["edges"]) == 10

    # The load-bearing pin: equal query count across the two parent counts -
    # the per-parent independence that disproves N+1. The absolute count is a
    # small fixed N pinned empirically (one root genres-connection query + one
    # windowed ``booksConnection`` prefetch query), NOT 1 + parent_count.
    assert three_count == ten_count
    assert three_count == 2


@pytest.mark.django_db
def test_nested_books_connection_has_next_page_without_edges():
    """Nested ``pageInfo { hasNextPage }`` is correct on the window with NO ``edges``.

    The Relay invariant ("``hasNextPage`` MUST resolve correctly even when the
    consumer didn't request ``edges``") asserted LIVE over /graphql/ on the
    windowed nested path spec-033 introduces - the root-field live twin
    (``test_has_next_page_correct_when_edges_unrequested``) and the package window
    pins cover the other paths. Each genre carries 3 books; ``first: 2`` with no
    ``edges`` selected still reports ``hasNextPage`` True, served from the window's
    ``_dst_total_count`` annotation in the same fixed two-query window (root
    genres-connection + one ``booksConnection`` prefetch), independent of parent
    count.
    """
    query = """
    query {
      allLibraryGenresConnection {
        edges {
          node {
            booksConnection(first: 2) {
              pageInfo { hasNextPage }
            }
          }
        }
      }
    }
    """
    shelf = _seed_shelf()
    for index in range(3):
        _seed_genre_with_books(
            f"Genre-{index}",
            shelf,
            (f"Book-{index}-a", f"Book-{index}-b", f"Book-{index}-c"),
        )
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    edges = payload["data"]["allLibraryGenresConnection"]["edges"]
    assert len(edges) == 3
    for edge in edges:
        # No ``edges`` requested; the page-flag still resolves True (3 > first: 2).
        assert edge["node"]["booksConnection"]["pageInfo"]["hasNextPage"] is True
    # One root genres-connection query + one windowed prefetch; no per-parent COUNT
    # and no per-parent fallback despite ``edges`` being absent.
    assert len(captured) == 2


@pytest.mark.django_db
def test_nested_total_count_without_edges():
    """Nested ``genresConnection { totalCount }`` with NO ``edges`` reads the annotation.

    The totalCount-only live sibling of ``test_nested_total_count_no_per_parent_count``
    (which selects ``totalCount`` AND ``edges``): selecting ``totalCount`` alone on
    the windowed connection serves the true count from ``_dst_total_count`` without
    a per-parent ``COUNT``.
    """
    query = """
    query {
      allLibraryBooks {
        genresConnection(first: 2) {
          totalCount
        }
      }
    }
    """
    shelf = _seed_shelf()
    genres = [
        models.Genre.objects.create(name=name)
        for name in (
            "Alpha",
            "Beta",
            "Gamma",
            "Echo",
        )
    ]
    for title in ("Kindred", "Dawn", "Wild Seed"):
        book = models.Book.objects.create(title=title, shelf=shelf)
        for genre in genres:
            book.genres.add(genre)

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    books = payload["data"]["allLibraryBooks"]
    assert books, payload
    for book in books:
        assert book["genresConnection"]["totalCount"] == 4  # all four genres, no edges
    # Root books list + one windowed genres prefetch; no per-book COUNT.
    assert len(captured) == 2


@pytest.mark.django_db
def test_nested_total_count_no_per_parent_count():
    """Selecting nested ``totalCount`` adds zero queries over the same shape.

    Rides ``genresConnection`` (target ``GenreType``, ``total_count`` on) under
    the optimizer-rooted ``allLibraryBooks`` list resolver - the forward-M2M
    shape ``test_book_genres_connection_sidecars_and_total_count`` established.
    The count comes from the window's ``_dst_total_count`` annotation, NOT a
    per-book ``COUNT``, so adding ``totalCount`` to the selection costs nothing
    extra even with multiple parent books (spec-033 Slice 5 / Edge case;
    DoD item 8).
    """
    shelf = _seed_shelf()
    # Multiple parent books, each with the SAME set of >2 genres, strengthens
    # the "no per-parent COUNT" claim: a per-book COUNT would scale with the
    # number of books; the window annotation does not.
    genres = [
        models.Genre.objects.create(name=name)
        for name in (
            "Alpha",
            "Beta",
            "Gamma",
            "Echo",
        )
    ]
    for title in ("Kindred", "Dawn", "Wild Seed"):
        book = models.Book.objects.create(title=title, shelf=shelf)
        for genre in genres:
            book.genres.add(genre)

    without_query = """
        query {
          allLibraryBooks {
            genresConnection(first: 2) {
              edges { node { name } }
            }
          }
        }
        """
    with_query = """
        query {
          allLibraryBooks {
            genresConnection(first: 2) {
              totalCount
              edges { node { name } }
            }
          }
        }
        """

    with CaptureQueriesContext(connection) as without_captured:
        without_response = _post_graphql(without_query)
    assert without_response.status_code == 200
    without_payload = without_response.json()
    assert "errors" not in without_payload, without_payload

    with CaptureQueriesContext(connection) as with_captured:
        with_response = _post_graphql(with_query)
    assert with_response.status_code == 200
    with_payload = with_response.json()
    assert "errors" not in with_payload, with_payload

    # Selecting nested ``totalCount`` adds ZERO queries - the window already
    # carries ``_dst_total_count``.
    assert len(with_captured) == len(without_captured)

    # The ``totalCount`` value is the full genre count per book (4), distinct
    # from the page size (first: 2) - and identical across every parent book.
    books = with_payload["data"]["allLibraryBooks"]
    assert len(books) == 3
    for book in books:
        assert book["genresConnection"]["totalCount"] == 4
        assert len(book["genresConnection"]["edges"]) == 2


@pytest.mark.django_db
def test_nested_window_respects_book_visibility():
    """``circulation_status="repair"`` books are windowed post-visibility.

    The target ``BookType.get_queryset`` runs INSIDE the nested windowed
    ``booksConnection`` (post-visibility row numbering, spec-033 Edge case
    "visibility-filtered targets"): an anonymous client never sees the repair
    book in any parent genre's nested page, while a staff client does.

    No ``orderBy:`` sidecar is selected - that matters: a nested connection
    carrying ``filter:`` / ``orderBy:`` input is left UNPLANNED and falls back
    per-parent (Decision 6), which would exercise the fallback pipeline, NOT
    the window. The plain selection IS window-planned, so this test pins the
    windowed-visibility branch. Two assertions enforce that:

    1. the captured query count is FLAT (parent-count-independent) - it would
       scale ~1-per-parent if the selection silently fell back per-parent; and
    2. the visible / hidden split is correct (post-``get_queryset`` row set).

    The window appends a deterministic pk-terminal order (Decision 4), so the
    books come back in seeded insertion order with no ``orderBy`` needed.

    ``booksConnection``'s target ``BookType`` has no ``totalCount`` field (no
    ``Meta.connection`` opt-in), so the "nested ``totalCount``" half of the spec
    line is proven through the VISIBLE-edge set - the post-visibility window row
    count IS the visible count. The ``GenreType`` connection that DOES carry
    ``totalCount`` has no visibility filter, so a visibility-filtered
    ``totalCount`` field is unavailable live; the ``booksConnection`` edge set
    is the correct live surface for ``BookType`` visibility (spec-033 Slice 5 /
    Edge case "visibility-filtered targets" / DoD item 8).
    """
    # No ``orderBy:`` - the plain selection is window-planned (the deterministic
    # pk-terminal order the window appends yields seeded insertion order for
    # free). An ``orderBy:`` sidecar would divert to the per-parent fallback.
    query = """
        query {
          allLibraryGenresConnection {
            edges {
              node {
                booksConnection {
                  edges { node { title } }
                }
              }
            }
          }
        }
        """

    def _seed_genres(genre_count: int, shelf: models.Shelf) -> None:
        """Each genre carries 3 visible books + 1 repair book via the M2M.

        Per-genre unique titles satisfy the ``(shelf, title)`` constraint.
        Every genre carrying its own repair book is what lets the flat
        query-count assertion below distinguish the window (one prefetch over
        all parents) from a per-parent fallback (one query per parent).
        """
        for index in range(genre_count):
            genre = models.Genre.objects.create(name=f"Genre-{index}")
            for title in (f"Aurora-{index}", f"Binti-{index}", f"Circe-{index}"):
                book = models.Book.objects.create(title=title, shelf=shelf)
                book.genres.add(genre)
            repair = models.Book.objects.create(
                title=f"Withdrawn-{index}",
                circulation_status=models.Book.CirculationStatus.REPAIR,
                shelf=shelf,
            )
            repair.genres.add(genre)

    def _nested_titles_by_genre(payload: dict) -> list[list[str]]:
        edges = payload["data"]["allLibraryGenresConnection"]["edges"]
        return [
            [book_edge["node"]["title"] for book_edge in edge["node"]["booksConnection"]["edges"]]
            for edge in edges
        ]

    shelf = _seed_shelf()
    _seed_genres(2, shelf)

    # Anonymous: the window is planned and runs ``BookType.get_queryset`` inside
    # it, so every parent genre's nested page excludes its repair book. The
    # captured query count is FLAT - one root genres-connection query plus one
    # windowed ``booksConnection`` prefetch - and would scale per-parent under a
    # silent fallback (the active window-vs-fallback pin).
    with CaptureQueriesContext(connection) as captured:
        anonymous = _post_graphql(query)
    assert anonymous.status_code == 200
    anonymous_payload = anonymous.json()
    assert "errors" not in anonymous_payload, anonymous_payload
    anonymous_titles = _nested_titles_by_genre(anonymous_payload)
    assert anonymous_titles == [
        ["Aurora-0", "Binti-0", "Circe-0"],
        ["Aurora-1", "Binti-1", "Circe-1"],
    ]
    # The flat count proves the visibility filter rides the WINDOW (Decision 5
    # fast path), not the per-parent fallback: 1 root query + 1 window prefetch,
    # independent of the 2 parent genres. A per-parent fallback would emit
    # ~1 query per genre, failing this pin.
    assert len(captured) == 2

    # Staff: the same windowed selection includes every repair book (visibility
    # bypass), in the same deterministic pk-terminal order after the visible set.
    staff = _post_graphql_as_staff(query)
    assert staff.status_code == 200
    staff_payload = staff.json()
    assert "errors" not in staff_payload, staff_payload
    assert _nested_titles_by_genre(staff_payload) == [
        [
            "Aurora-0",
            "Binti-0",
            "Circe-0",
            "Withdrawn-0",
        ],
        [
            "Aurora-1",
            "Binti-1",
            "Circe-1",
            "Withdrawn-1",
        ],
    ]


# One query string for the "both"-shape coexistence test (a list relation and
# its synthesized connection sibling selected on the same parent).
_BOTH_SHAPE_QUERY = """
query {
  allLibraryGenres {
    name
    books { title }
    booksConnection(first: 2) {
      edges { node { title } }
      pageInfo { hasNextPage }
    }
  }
}
"""


@pytest.mark.django_db
def test_list_relation_and_connection_sibling_coexist_live():
    """The "both" shape over ``/graphql/``: a genre's ``books`` list AND its windowed ``booksConnection`` resolve together.

    spec-033 Decision 4 ``to_attr`` isolation, earned LIVE (the ``test_query/``
    README live-HTTP-first rule). Selecting the list relation and its synthesized
    connection sibling on the same parent lands TWO prefetches on the ``books``
    accessor - the list field's accessor-keyed ``Prefetch`` (the FULL related
    set) and the window's ``_dst_books_connection`` ``to_attr`` ``Prefetch`` (the
    windowed page). The ``to_attr`` slot is precisely what keeps them from
    colliding into Django's "lookup already seen with a different queryset" error.

    Two pins: (1) the wire results are distinct and correct - the list returns
    the full set, the connection only the ``first: 2`` page; (2) the captured
    query count is FLAT (root + the ``books`` list prefetch + the windowed
    ``_dst_books_connection`` prefetch), independent of parent count, proving the
    two prefetches coexist as ONE-per-relation batched queries rather than a
    per-parent fallback.
    """

    def _run(genre_count: int) -> tuple[int, dict]:
        shelf = _seed_shelf()
        for index in range(genre_count):
            # >2 books per genre so ``first: 2`` leaves a meaningful hasNextPage
            # and the list/connection results visibly differ; per-genre unique
            # titles satisfy the (shelf, title) constraint.
            _seed_genre_with_books(
                f"Genre-{index}",
                shelf,
                (f"Book-{index}-a", f"Book-{index}-b", f"Book-{index}-c"),
            )
        with CaptureQueriesContext(connection) as captured:
            response = _post_graphql(_BOTH_SHAPE_QUERY)
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        return len(captured), payload

    two_count, two_payload = _run(2)
    genres = two_payload["data"]["allLibraryGenres"]
    assert len(genres) == 2
    for index, genre in enumerate(genres):
        # The list relation returns the FULL related set...
        assert [b["title"] for b in genre["books"]] == [
            f"Book-{index}-a",
            f"Book-{index}-b",
            f"Book-{index}-c",
        ]
        # ...while the connection sibling returns only the windowed page.
        conn = genre["booksConnection"]
        assert [e["node"]["title"] for e in conn["edges"]] == [
            f"Book-{index}-a",
            f"Book-{index}-b",
        ]
        assert conn["pageInfo"]["hasNextPage"] is True

    # Reset and re-run with more parents: the count must be identical - the list
    # prefetch and the window each run ONCE over all parents, never per-parent.
    models.Book.objects.all().delete()
    models.Genre.objects.all().delete()
    models.Shelf.objects.all().delete()
    models.Branch.objects.all().delete()

    four_count, four_payload = _run(4)
    assert len(four_payload["data"]["allLibraryGenres"]) == 4
    # The coexistence + N+1-disproof pin: equal count across parent counts, and a
    # small fixed N - root genres query + the "books" list prefetch + the windowed
    # "_dst_books_connection" prefetch.
    assert two_count == four_count
    assert two_count == 3


@pytest.mark.django_db
def test_nested_connection_pagination_from_graphql_variable_live():
    """A GraphQL VARIABLE drives the nested window over ``/graphql/`` (not just a literal).

    The in-process Slice-3 cache-key tests pin variable resolution at the plan
    layer; this earns the end-to-end half live - ``$n`` flows through the request
    body, ``ConnectionExtension``, and the window so the page size IS the
    variable's value (spec-033 Slice 5; the round-3 live-coverage G2 follow-up,
    which also added the ``variables=`` parameter to ``_post_graphql``).
    """
    shelf = _seed_shelf()
    _seed_genre_with_books(
        "Variable",
        shelf,
        (
            "a",
            "b",
            "c",
            "d",
        ),
    )
    query = """
    query Books($n: Int!) {
      allLibraryGenres {
        booksConnection(first: $n) {
          edges { node { title } }
          pageInfo { hasNextPage }
        }
      }
    }
    """
    response = _post_graphql(query, variables={"n": 2})
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    conn = payload["data"]["allLibraryGenres"][0]["booksConnection"]
    assert [e["node"]["title"] for e in conn["edges"]] == ["a", "b"]
    assert conn["pageInfo"]["hasNextPage"] is True


@pytest.mark.django_db
def test_nested_connection_first_zero_empty_page_live():
    """Nested ``first: 0`` returns an empty page live (the ambiguous-empty fallback).

    The ROOT ``first: 0`` is pinned at ``test_genre_connection_first_zero_empty_edges``;
    this rounds out the live matrix with the NESTED ambiguous-empty window
    (fast-path -> per-parent fallback, spec-033 Decision 5): empty edges, but
    ``hasNextPage`` True because the genre genuinely has books beyond the zero
    window (the round-3 live-coverage G3 follow-up).
    """
    shelf = _seed_shelf()
    _seed_genre_with_books("Empty", shelf, ("a", "b", "c"))
    response = _post_graphql(
        """
        query {
          allLibraryGenres {
            booksConnection(first: 0) {
              edges { node { title } }
              pageInfo { hasNextPage }
            }
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    conn = payload["data"]["allLibraryGenres"][0]["booksConnection"]
    assert conn["edges"] == []
    assert conn["pageInfo"]["hasNextPage"] is True


_EMPTY_PARENT_GENRES_CONNECTION_QUERY = """
    query {
      allLibraryBooks {
        genresConnection(first: 2) {
          totalCount
          edges { node { name } }
          pageInfo { hasNextPage hasPreviousPage }
        }
      }
    }
    """


@pytest.mark.django_db
def test_nested_empty_parent_serves_zero_total_count_no_fallback_live():
    """A genuinely-empty parent is fast-path-served zero live - NOT per-parent fallback.

    The contrast with ``test_nested_connection_first_zero_empty_page_live``: that
    is the AMBIGUOUS empty window (``first: 0``, ``limit == 0``) which falls back
    per parent; this is the UNAMBIGUOUS empty window (``offset == 0``,
    ``limit > 0``, no related rows) the fast path serves directly -
    ``totalCount = 0``, no cursors, both ``pageInfo`` flags ``False`` - WITHOUT a
    per-parent fallback query (spec-033 Decision 5 / the ``Parents with no
    related rows`` edge case). Rides ``genresConnection`` (target ``GenreType``,
    ``total_count`` on) so ``totalCount`` exists.

    This earns LIVE the behavior the package-level
    ``test_fast_path_genuinely_empty_parent_serves_zero`` pins in-process
    (``tests/test_relay_connection.py``): the README's live-HTTP-first rule
    requires a fakeshop-expressible coverage line to be earned here, and a book
    with zero genres expresses it. The no-fallback claim is held the same way
    the sibling fixed-query-count pins hold theirs - the captured count is
    INDEPENDENT of the number of empty parents (a per-parent fallback would
    scale with it).
    """

    def _run(book_count: int) -> tuple[int, dict]:
        shelf = _seed_shelf()
        # Each book carries ZERO genres: the genuinely-empty window shape.
        for index in range(book_count):
            models.Book.objects.create(title=f"Genre-less-{index}", shelf=shelf)
        with CaptureQueriesContext(connection) as captured:
            response = _post_graphql(_EMPTY_PARENT_GENRES_CONNECTION_QUERY)
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        return len(captured), payload

    three_count, three_payload = _run(3)
    three_books = three_payload["data"]["allLibraryBooks"]
    assert len(three_books) == 3
    for book in three_books:
        conn = book["genresConnection"]
        assert conn["edges"] == []
        assert conn["totalCount"] == 0
        assert conn["pageInfo"] == {"hasNextPage": False, "hasPreviousPage": False}

    # Reset to an empty library, then re-run with more empty parents.
    models.Book.objects.all().delete()
    models.Shelf.objects.all().delete()
    models.Branch.objects.all().delete()

    eight_count, eight_payload = _run(8)
    assert len(eight_payload["data"]["allLibraryBooks"]) == 8

    # The load-bearing pin: equal query count across 3 vs 8 empty parents -
    # the genuinely-empty parents are served from the single window prefetch,
    # never a per-parent fallback (which would make the count scale).
    assert three_count == eight_count


# ---------------------------------------------------------------------------
# RelatedFilter behavior over live /graphql/ (feedback2.md high-confidence
# moves from ``tests/filters/test_sets.py``). The live ``BranchFilter.shelves``
# carries an explicit ``queryset=Shelf.objects.filter(topic="permanent collection")``
# (apps/library/filters.py), so these exercise GraphQL input coercion, root
# visibility, the real configured RelatedFilter + explicit-queryset
# intersection, and the HTTP envelope - strictly stronger than the
# ``BranchFilter.apply_sync`` package twins they replace.
# ---------------------------------------------------------------------------


def _seed_branch_with_shelf_codes(name: str, codes: tuple[str, ...]) -> None:
    """Create a branch (visible city) owning one shelf per code.

    Shelves carry ``topic="permanent collection"`` so they survive the live
    ``BranchFilter.shelves`` explicit queryset; the branch city is never
    ``"restricted"`` so ``BranchType.get_queryset`` keeps it visible to the
    anonymous client.
    """
    branch = models.Branch.objects.create(name=name, city="Boston")
    for code in codes:
        models.Shelf.objects.create(code=code, topic="permanent collection", branch=branch)


@pytest.mark.django_db
def test_nested_or_related_branch_constrains_parent_live():
    """A ``RelatedFilter`` nested in ``or`` constrains the parent over /graphql/.

    The live twin of ``test_apply_sync_nested_or_branch_applies_related_constraint``:
    ``_normalize_input`` strips related-branch keys from a child branch's form
    data, so without ``_q_for_branch`` re-deriving the related constraint,
    ``or: [{ shelves: {...} }]`` would silently widen to the whole parent set.
    Here only ``alpha`` owns a shelf matching ``code: "match"``; ``beta`` must
    NOT leak through, driving the real ``allLibraryBranches`` filter pipeline
    (``apply_sync`` -> ``_evaluate_logic_tree`` -> ``_q_for_branch`` ->
    ``_apply_related_constraints``) end to end over HTTP.
    """
    _seed_branch_with_shelf_codes("alpha", ("match",))
    _seed_branch_with_shelf_codes("beta", ("other",))

    response = _post_graphql(
        """
        query {
          allLibraryBranches(
            filter: { or: [{ shelves: { code: { exact: "match" } } }] }
          ) {
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"]["allLibraryBranches"] == [{"name": "alpha"}]


@pytest.mark.django_db
def test_many_side_related_filter_returns_each_parent_once_live():
    """A many-side related branch matching N shelves yields the parent ONCE.

    The live twin of ``test_related_filter_on_many_side_relation_returns_each_parent_once``:
    ``_apply_related_constraints`` restricts the parent via a
    ``pk__in=<parent-pk subquery>`` rather than a fan-out join, so a branch
    whose TWO shelves both match comes back exactly once - no duplicate node in
    the HTTP list (a join would surface ``alpha`` twice and corrupt any
    downstream pagination count).
    """
    _seed_branch_with_shelf_codes("alpha", ("match-1", "match-2", "other"))
    _seed_branch_with_shelf_codes("beta", ("unrelated",))

    response = _post_graphql(
        """
        query {
          allLibraryBranches(
            filter: { shelves: { code: { iContains: "match" } } }
          ) {
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    # ``alpha`` appears exactly once despite two matching shelves; ``beta`` is
    # absent. A fan-out join would have returned ``[alpha, alpha]``.
    assert payload["data"]["allLibraryBranches"] == [{"name": "alpha"}]


@pytest.mark.django_db
def test_related_filter_identical_direct_and_inside_logic_tree_live():
    """The same related branch answers identically direct and wrapped in ``and``.

    The live twin of ``test_related_filter_answers_identically_direct_and_inside_logic_tree``:
    the direct path constrains via ``_apply_related_constraints`` while the
    logic-tree path routes through ``_q_for_branch``'s ``Q(pk__in=...)``; both
    share the parent-pk-subquery shape, so two aliases in ONE request - one
    direct, one wrapped in ``and`` - must return identical rows.
    """
    _seed_branch_with_shelf_codes("alpha", ("match-1", "match-2"))
    _seed_branch_with_shelf_codes("beta", ("other",))

    response = _post_graphql(
        """
        query {
          direct: allLibraryBranches(
            filter: { shelves: { code: { iContains: "match" } } }
          ) { name }
          wrapped: allLibraryBranches(
            filter: { and: [{ shelves: { code: { iContains: "match" } } }] }
          ) { name }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    data = payload["data"]
    assert data["direct"] == data["wrapped"] == [{"name": "alpha"}]


# ---------------------------------------------------------------------------
# Schema-shape introspection over live /graphql/ (feedback2.md high-confidence
# moves from ``tests/types/test_definition_order_schema.py``). The library
# schema already exposes the M2M (``BookType.genres``), a Relay-declared
# ``GenreType``, and a non-Relay ``ShelfType``, so the rendered shapes are
# assertable through the real ``__type`` introspection over HTTP.
# ---------------------------------------------------------------------------


def _introspect_type(type_name: str) -> dict:
    """Return the ``__type`` payload (interfaces + fields with nested type tree)."""
    response = _post_graphql(
        f"""
        query {{
          __type(name: "{type_name}") {{
            interfaces {{ name }}
            fields {{
              name
              type {{ kind name ofType {{ kind name ofType {{ kind name ofType {{ kind name }} }} }} }}
            }}
          }}
        }}
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    type_info = payload["data"]["__type"]
    assert type_info is not None, f"{type_name} is not in the schema"
    return type_info


@pytest.mark.django_db
def test_book_genres_m2m_renders_as_list_shape_live():
    """``BookType.genres`` (forward M2M) renders as ``[GenreType!]!`` over HTTP.

    The live twin of ``test_m2m_schema_shape_builds_with_real_library_models``:
    the M2M relation surfaces as a non-null list of non-null ``GenreType`` -
    asserted through real introspection rather than ``schema._schema.type_map``.
    """
    genres_type = _field_type(_introspect_type("BookType"), "genres")
    # ``[GenreType!]!`` unwraps NON_NULL -> LIST -> NON_NULL -> OBJECT GenreType.
    assert genres_type["kind"] == "NON_NULL"
    assert genres_type["ofType"]["kind"] == "LIST"
    assert genres_type["ofType"]["ofType"]["kind"] == "NON_NULL"
    assert genres_type["ofType"]["ofType"]["ofType"]["kind"] == "OBJECT"
    assert genres_type["ofType"]["ofType"]["ofType"]["name"] == "GenreType"


@pytest.mark.django_db
def test_relay_genre_type_emits_node_interface_and_global_id_live():
    """A Relay-declared ``GenreType`` exposes the ``Node`` interface and ``id: ID!``.

    The live twin of ``test_relay_declared_type_emits_node_interface_and_global_id``:
    ``GenreType`` declares ``interfaces = (relay.Node,)``, so introspection shows
    the ``Node`` interface and its ``id`` renders as the GlobalID scalar ``ID!``.
    """
    genre_type = _introspect_type("GenreType")
    interface_names = {iface["name"] for iface in genre_type["interfaces"]}
    assert "Node" in interface_names
    id_type = _field_type(genre_type, "id")
    assert id_type["kind"] == "NON_NULL"
    assert id_type["ofType"]["name"] == "ID"


@pytest.mark.django_db
def test_mixed_relay_and_non_relay_no_interface_bleed_live():
    """A non-Relay ``ShelfType`` does NOT implement ``Node`` (no interface bleed).

    The live twin of ``test_mixed_relay_and_non_relay_types_introspect_cleanly``:
    the library schema ships Relay ``GenreType`` and non-Relay ``ShelfType``;
    introspection proves ``Node`` lands on the Relay type only and ``ShelfType.id``
    is NOT the GlobalID scalar (no GlobalID bleed onto the plain type).
    """
    genre_type = _introspect_type("GenreType")
    shelf_type = _introspect_type("ShelfType")
    genre_interfaces = {iface["name"] for iface in genre_type["interfaces"]}
    shelf_interfaces = {iface["name"] for iface in shelf_type["interfaces"]}
    assert "Node" in genre_interfaces
    assert "Node" not in shelf_interfaces
    # The Relay type's id is the GlobalID scalar; the plain type's id is a plain
    # scalar (NOT ``ID``), so the Relay interface does not bleed across.
    assert _field_type(genre_type, "id")["ofType"]["name"] == "ID"
    assert _field_type(shelf_type, "id")["ofType"]["name"] != "ID"


# ---------------------------------------------------------------------------
# DjangoListField default resolver visibility over live /graphql/ (feedback2.md
# high-confidence move from ``tests/test_list_field.py``). ``BranchType.get_queryset``
# excludes ``city="restricted"`` for anonymous requests; the default list-field
# resolver must apply it, so the restricted branch is absent from the HTTP result.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_branches_via_list_field_default_resolver_applies_get_queryset_live():
    """``allLibraryBranchesViaListField`` applies ``BranchType.get_queryset`` over HTTP.

    The live twin of ``test_djangolistfield_default_resolver_returns_queryset_filtered_by_get_queryset``:
    the ``DjangoListField`` default resolver routes the queryset through
    ``BranchType.get_queryset`` (``apply_type_visibility_sync``), which hides
    ``city="restricted"`` branches from the anonymous client - so the seeded
    restricted branch is absent from the field output while the visible one
    remains.
    """
    models.Branch.objects.create(name="Visible", city="Boston")
    models.Branch.objects.create(name="Hidden", city="restricted")

    response = _post_graphql("{ allLibraryBranchesViaListField { name } }")
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    names = [branch["name"] for branch in payload["data"]["allLibraryBranchesViaListField"]]
    assert "Visible" in names
    assert "Hidden" not in names


# ---------------------------------------------------------------------------
# Scalar logic-tree filter unions/intersections and nested-branch validation
# over live /graphql/ (feedback3.md high-confidence + qualifying conditional
# moves from ``tests/filters/test_sets.py``). The live ``BranchFilter`` exposes
# ``name``/``city`` scalar lookups and the ``PatronFilter`` carries the
# ``emailMustHaveAtSign`` custom-validator filter, so the union/intersection
# and per-branch form-validation contracts are reachable through the real API.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_scalar_or_branch_unions_matching_rows_live():
    """A scalar ``or`` over two leaf clauses returns the deduplicated union.

    The live twin of ``test_filter_queryset_unions_or_branch``:
    ``or: [{ name }, { city }]`` ORs the two scalar leaves, so a branch matching
    EITHER arm appears and a branch matching neither is absent. The existing
    live suite covers ``and`` and ``not`` on branches but not a plain scalar
    ``or`` union, and this drives the real ``BranchFilter`` ->
    ``_evaluate_logic_tree`` union path over HTTP.
    """
    models.Branch.objects.create(name="x-row", city="Boston")
    models.Branch.objects.create(name="other-name", city="y-row")
    models.Branch.objects.create(name="no-match", city="elsewhere")

    response = _post_graphql(
        """
        query {
          allLibraryBranches(
            filter: { or: [{ name: { exact: "x-row" } }, { city: { exact: "y-row" } }] }
          ) {
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    # OR does not guarantee ordering; assert the matching set. ``no-match`` is
    # excluded; neither row is duplicated.
    names = {row["name"] for row in payload["data"]["allLibraryBranches"]}
    assert names == {"x-row", "other-name"}


@pytest.mark.django_db
def test_scalar_and_branch_intersects_matching_rows_live():
    """A pure two-scalar ``and`` intersects the leaf clauses.

    The live twin of ``test_filter_queryset_intersects_and_branch``:
    ``and: [{ name }, { city }]`` ANDs the two scalar leaves, so only the branch
    matching BOTH survives while branches matching a single arm are excluded.
    ``test_library_books_filter_combines_and_or_not`` mixes a ``not`` clause and
    is not a pure two-scalar intersection, so this keeps that simpler ``and``
    contract live.
    """
    # Only the first branch matches both scalar arms. The second shares the
    # ``city`` arm only (``Branch.name`` is unique, so a name-only twin cannot
    # exist; the city-only row alone distinguishes AND from a union, which would
    # also return it). The third matches neither.
    models.Branch.objects.create(name="both", city="downtown")
    models.Branch.objects.create(name="city-only", city="downtown")
    models.Branch.objects.create(name="neither", city="elsewhere")

    response = _post_graphql(
        """
        query {
          allLibraryBranches(
            filter: { and: [{ name: { exact: "both" } }, { city: { exact: "downtown" } }] }
          ) {
            name
            city
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    # AND returns only the both-arm row; ``city-only`` (city arm only) is
    # excluded - a union would have returned it too.
    assert payload["data"]["allLibraryBranches"] == [{"name": "both", "city": "downtown"}]


@pytest.mark.django_db
def test_malformed_nested_branch_form_raises_filter_invalid_live():
    """A malformed filter nested inside ``and`` is validated per-branch, not dropped.

    The live twin of ``test_q_for_branch_validates_child_form_and_raises_on_malformed_subbranch``:
    ``_q_for_branch`` runs ``_validate_form_or_raise`` on every nested instance,
    so a value failing the ``email_must_have_at_sign`` validator inside an
    ``and`` branch surfaces ``FILTER_INVALID`` with the nested field error -
    rather than ``BaseFilterSet.qs`` silently falling through to an empty
    ``pk__in`` set. This differs from the top-level
    ``test_apply_raises_graphqlerror_on_invalid_filter_input`` by exercising the
    *nested* branch-validation path. A GraphQL-rejected literal (e.g. a bad
    integer) cannot reach the form, so the custom validator is used instead.
    """
    models.Patron.objects.create(name="Ada", email="ada@example.com")

    response = _post_graphql(
        """
        query {
          allLibraryPatrons(
            filter: { and: [{ emailMustHaveAtSign: { exact: "bogus" } }] }
          ) {
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
