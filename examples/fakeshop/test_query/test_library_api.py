"""Live GraphQL HTTP tests for the library app's read/write, Relay, keyset, and optimizer surface."""

import base64

import pytest
from apps.library import models
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from graphql_client import assert_graphql_data as _assert_graphql_data
from graphql_client import post_graphql as _post_graphql
from strawberry import relay

from django_strawberry_framework.testing import TestClient
from django_strawberry_framework.testing.relay import global_id_for


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


def _input_field_type(type_name: str, field_name: str) -> dict:
    """Return an input object field's TYPE tree (``kind`` / ``name`` / ``ofType``) via introspection.

    Used to assert an input field's GraphQL nullability: a ``NON_NULL`` wrapper (``kind ==
    "NON_NULL"``, ``ofType`` the scalar) means a non-null ``String!``; a bare scalar (``kind
    == "SCALAR"``, ``name == "String"``) means a nullable, omittable ``String``. Pins, e.g.,
    that an ``allow_blank=True`` required ``CharField`` is still ``String!`` (allow_blank is
    absent from the SDL) and that two hooks differing only in ``allow_null`` emit
    ``String!`` vs ``String`` (spec-039 M2 / High).
    """
    response = _post_graphql(
        f"""
        query {{
          __type(name: "{type_name}") {{
            inputFields {{ name type {{ kind name ofType {{ kind name }} }} }}
          }}
        }}
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    type_info = payload["data"]["__type"]
    assert type_info is not None
    return next(f["type"] for f in type_info["inputFields"] if f["name"] == field_name)


def _mutation_data_input_type_name(field_name: str) -> str:
    """Return the input type name of a mutation field's ``data`` argument via introspection.

    A serializer mutation's ``data:`` argument is ``<Input>!`` (a ``NON_NULL`` wrapping the
    generated input object), so the named type is the wrapper's ``ofType``. Used to compare
    the descriptor-derived input names of two same-serializer hook mutations without
    hard-coding the (deliberately opaque) digest-bearing names.
    """
    response = _post_graphql(
        """
        query {
          __type(name: "Mutation") {
            fields { name args { name type { kind name ofType { kind name } } } }
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    fields = payload["data"]["__type"]["fields"]
    field = next(f for f in fields if f["name"] == field_name)
    data_arg = next(arg for arg in field["args"] if arg["name"] == "data")
    arg_type = data_arg["type"]
    return arg_type["name"] or arg_type["ofType"]["name"]


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
def test_library_evaluated_queryset_not_re_executed_over_http():
    """G1 (spec-035): a resolver that EVALUATES its queryset before returning it
    runs exactly ONE SQL query over the live stack.

    ``all_library_branches_eager_eval`` does ``if not queryset: return []``,
    whose ``bool(queryset)`` populates ``_result_cache``. The optimizer's
    evaluated-queryset guard passes the already-executed queryset through
    instead of cloning it and applying ``.only(...)`` - which, pre-G1, would
    re-execute the SQL (two queries for one logical read). The guard makes it
    one.
    """
    _seed_library_graph()

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryBranchesEagerEval { name }
            }
            """,
        )

    assert response.status_code == 200
    assert response.json() == {
        "data": {"allLibraryBranchesEagerEval": [{"name": "Central"}]},
    }
    # G1: exactly one query - the consumer's own ``bool(queryset)`` evaluation.
    # Without the evaluated-queryset guard, the optimizer's ``.only()`` clone
    # would re-execute and this would be two.
    assert len(captured) == 1


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
    # The consumer override OWNS the relation (workstream D - the
    # strawberry-django #697 bug class): the walker leaves ``shelves``
    # fully unplanned, so the historical speculative prefetch (a query the
    # override's ``order_by("-code")`` re-query never consumed) is GONE.
    # The observable baseline is root query + one override manager query
    # per Branch row - and nothing else.
    assert len(captured) == 3


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
        default resolver returns ``Branch._default_manager.all()``).
      * 0 SELECTs for a ``shelves`` prefetch: the consumer override on
        ``BranchType.shelves`` OWNS the relation, so the walker leaves it
        fully unplanned (workstream D) - the historical speculative
        ``prefetch_related("shelves")`` query (which the override's
        ``order_by("-code")`` re-query never consumed) no longer runs.
      * 2 SELECTs (one per seeded ``Branch``) for the consumer-override
        ``BranchType.shelves`` resolver at ``apps/library/schema.py`` (which
        evaluates ``self.shelves.order_by("-code")``). This mirrors the
        baseline established by
        ``test_library_relation_override_shapes_http_response_data`` above
        for the same nested-selection shape.

    Total: 1 + 0 + 2 = 3 queries. If a future maintainer adds ``order_by`` to
    the new field, removes the consumer override on ``BranchType.shelves`` (or
    opts it back into planning with an ``OptimizerHint``), or changes the
    seeded branch count, recompute N accordingly.
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
    assert len(captured) == 3
    assert "library_branch" in captured[0]["sql"]
    # The two per-branch consumer-override queries; no prefetch query precedes
    # them (workstream D - the relation is consumer-owned, so unplanned).
    assert "library_shelf" in captured[1]["sql"]
    assert "library_shelf" in captured[2]["sql"]


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
    """Issue a GraphQL POST authenticated as a freshly-created staff user, via ``TestClient``.

    The authenticated flow through ``TestClient.login()`` (spec-043 Slice 2): the
    force-login/logout bracket wraps the one post, and the raw ``HttpResponse``
    the client kept on ``Response.response`` is returned so callers keep their
    ``.status_code`` / ``.json()`` assertions.
    """
    user_model = get_user_model()
    staff = user_model.objects.create_user(
        username="staff",
        password="pw",
        is_staff=True,
    )
    client = TestClient()
    with client.login(staff):
        return client.query(query, assert_no_errors=False).response


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


def test_hide_flat_filters_changes_library_filter_input_shape_over_http(
    project_schema_override,
):
    """``HIDE_FLAT_FILTERS`` changes the real GraphQL input shape exposed at ``/graphql/``."""
    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"HIDE_FLAT_FILTERS": False}):
        project_schema_override()
        shown = _input_field_names("BranchFilterInputType")
        assert "shelves" in shown
        assert "shelvesCode" in shown

    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"HIDE_FLAT_FILTERS": True}):
        project_schema_override()
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
def test_library_genres_filter_malformed_own_pk_global_id_raises_globalid_invalid():
    """A MALFORMED (undecodable) own-PK GlobalID filter value surfaces the uniform
    ``GLOBALID_INVALID`` coded error, not a raw ``GlobalIDValueError`` leak.

    ``GenreType`` is a Relay node, so ``GenreFilter.id { exact }`` resolves to a
    ``GlobalIDFilter``. An unparseable wire string (bad base64 / not a
    ``type_name:node_id`` payload) must not escape as Strawberry's raw
    ``GlobalIDValueError`` ("Incorrect padding", ...): the filter mirrors the
    node-refetch contract (``relay.py::_decode_or_graphql_error``) and every
    other package decode site, raising ``GraphQLError`` with
    ``extensions={"code": "GLOBALID_INVALID"}``. The wrong-TYPE case above keeps
    its own (code-less) ``"GlobalID type mismatch"`` message; this pins the
    malformed-payload sibling.
    """
    models.Genre.objects.create(name="SciFi")
    response = _post_graphql(
        """
        query {
          allLibraryGenres(filter: { id: { exact: "not-a-valid-base64!!!" } }) {
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" in payload, payload
    error = payload["errors"][0]
    assert error["extensions"]["code"] == "GLOBALID_INVALID", payload
    assert "Invalid GlobalID" in error["message"], payload


@pytest.mark.django_db
def test_library_genres_filter_malformed_own_pk_global_id_in_names_index():
    """A malformed element inside an own-PK ``id { in: [...] }`` list names its index.

    ``in`` resolves to ``GlobalIDMultipleChoiceFilter``; each element is decoded
    independently, so a malformed element raises the same ``GLOBALID_INVALID``
    coded error with its list position named (parity with the per-element
    ``"GlobalID type mismatch ... at index N"`` message).
    """
    models.Genre.objects.create(name="SciFi")
    response = _post_graphql(
        """
        query {
          allLibraryGenres(filter: { id: { in: ["Zm9v"] } }) {
            name
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" in payload, payload
    error = payload["errors"][0]
    assert error["extensions"]["code"] == "GLOBALID_INVALID", payload
    assert "at index 0" in error["message"], payload


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
def test_library_genres_connection_pages_by_to_many_aggregate():
    """A root connection paginates a grouped to-many order without duplicate or missing nodes.

    This is the cross-backend acceptance pin for the orders pre-BETA review:
    the same live HTTP test runs in the default SQLite suite and the PostgreSQL
    CI tier. ``GenreOrder.books.title`` traverses the reverse M2M, so ASC orders
    each genre by ``Min("books__title")``. The connection then appends its
    deterministic pk tiebreaker and cursor-slices that grouped queryset.

    A root connection does not use the nested optimizer's row-number window,
    while nested connections carrying ``orderBy:`` deliberately use the
    per-parent fallback. The SQL assertion pins that real boundary: the root
    page contains ``MIN`` + ``GROUP BY`` and no ``_dst_row_number`` layer.
    """
    branch = models.Branch.objects.create(name="Branch", city="Boston")
    shelf = models.Shelf.objects.create(code="A-1", topic="general", branch=branch)
    genres = {
        name: models.Genre.objects.create(name=name)
        for name in (
            "Aggregate A",
            "Aggregate B",
            "Aggregate C",
            "Aggregate D",
        )
    }
    for title, genre_name in (
        ("Alpha", "Aggregate A"),
        ("Zulu", "Aggregate A"),
        ("Beta", "Aggregate B"),
        ("Charlie", "Aggregate C"),
        ("Delta", "Aggregate D"),
    ):
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genres[genre_name])

    def _page(after: str | None = None):
        after_argument = f', after: "{after}"' if after is not None else ""
        with CaptureQueriesContext(connection) as captured:
            response = _post_graphql(
                f"""
                query {{
                  allLibraryGenresConnection(
                    orderBy: [{{ books: {{ title: ASC }} }}]
                    first: 2
                    {after_argument}
                  ) {{
                    totalCount
                    edges {{ cursor node {{ name }} }}
                    pageInfo {{ hasNextPage endCursor }}
                  }}
                }}
                """,
            )
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        return payload["data"]["allLibraryGenresConnection"], captured

    page_one, captured = _page()
    aggregate_sql = next(query["sql"] for query in captured if "MIN(" in query["sql"].upper())
    assert "GROUP BY" in aggregate_sql.upper()
    assert "_dst_row_number" not in aggregate_sql
    assert page_one["totalCount"] == 4
    assert [edge["node"]["name"] for edge in page_one["edges"]] == ["Aggregate A", "Aggregate B"]
    assert page_one["pageInfo"]["hasNextPage"] is True

    page_two, _captured = _page(page_one["pageInfo"]["endCursor"])
    assert page_two["totalCount"] == 4
    assert [edge["node"]["name"] for edge in page_two["edges"]] == ["Aggregate C", "Aggregate D"]
    assert page_two["pageInfo"]["hasNextPage"] is False

    all_names = [edge["node"]["name"] for page in (page_one, page_two) for edge in page["edges"]]
    assert all_names == [
        "Aggregate A",
        "Aggregate B",
        "Aggregate C",
        "Aggregate D",
    ]
    assert len(all_names) == len(set(all_names))


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
    """``PublicPatron`` (``Meta.exclude`` + ``Meta.name`` + ``Meta.description``) vs ``PatronType``.

    ``PublicPatronType`` selects via a deny-list ``Meta.exclude = ("email",
    "lifetime_fines_cents")`` over the same ``Patron`` model that the primary
    ``PatronType`` selects via an allow-list ``Meta.fields``. It also renames the
    GraphQL type to ``PublicPatron`` (``Meta.name``, decoupled from the
    ``PublicPatronType`` class name) and carries a ``Meta.description``. This pins:
    the renamed GraphQL type exists with the description and resolves; the original
    class name is NOT a GraphQL type; the excluded columns are absent (selecting one
    is a query error); the kept columns resolve; and the primary ``PatronType`` is
    unaffected.
    """
    models.Patron.objects.create(
        name="Ada",
        email="ada@example.com",
        lifetime_fines_cents=1234,
    )

    # 1. Schema shape: the type is exposed under its Meta.name ``PublicPatron`` (the
    #    ``PublicPatronType`` class name is NOT a GraphQL type), carries the
    #    Meta.description, drops the two excluded columns, and the allow-list primary
    #    PatronType still carries lifetimeFinesCents.
    response = _post_graphql(
        """
        query {
          public: __type(name: "PublicPatron") { description fields { name } }
          renamedAway: __type(name: "PublicPatronType") { name }
          primary: __type(name: "PatronType") { fields { name } }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    # Meta.name renamed the GraphQL type; the class-name type no longer resolves.
    assert payload["data"]["public"] is not None
    assert payload["data"]["renamedAway"] is None
    # Meta.description surfaces verbatim through introspection.
    assert payload["data"]["public"]["description"] == (
        "A patron projection with PII (email) and financial (lifetime fines) columns removed."
    )
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
def test_genre_connection_total_count_skip_include_no_count():
    """A directive-excluded ``totalCount`` fires no COUNT (selection-gating + directives).

    Selection-gating (Decision 4) must honor live ``@skip`` / ``@include`` on the
    direct ``totalCount`` child, not just its absence. ``info.selected_fields``
    (Strawberry ``convert_selections``) carries the field with its already-resolved
    directive args (``{"skip": {"if": True}}`` / variable-resolved ``include``) -
    it does NOT pre-drop the node - so ``direct_child_selected`` must apply the same
    ``should_include`` gate its sibling converted-selection walks do. Three excluded
    shapes (direct ``@skip(if: true)``, variable-driven ``@include(if: $show=false)``,
    named-fragment-wrapped ``@skip(if: true)``) must each issue zero ``COUNT(`` SQL
    and omit the field; the ``@skip(if: false)`` control proves the count still
    fires when the directive resolves to "keep". Mirrors
    ``test_genre_connection_total_count_omitted_no_count`` for the directive case.
    """
    _seed_genres("Alpha", "Beta", "Gamma")

    def _count_queries(captured: CaptureQueriesContext) -> int:
        return sum("COUNT(" in query["sql"].upper() for query in captured.captured_queries)

    # (1) direct ``@skip(if: true)`` -> field excluded, no COUNT.
    with CaptureQueriesContext(connection) as captured_skip:
        response = _post_graphql(
            """
            query {
              allLibraryGenresConnection(first: 2) {
                edges { node { name } }
                totalCount @skip(if: true)
              }
            }
            """,
        )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert "totalCount" not in payload["data"]["allLibraryGenresConnection"]
    assert _count_queries(captured_skip) == 0

    # (2) variable-driven ``@include(if: $show)`` with ``$show = false`` -> excluded, no COUNT.
    with CaptureQueriesContext(connection) as captured_include:
        response = _post_graphql(
            """
            query Q($show: Boolean!) {
              allLibraryGenresConnection(first: 2) {
                edges { node { name } }
                totalCount @include(if: $show)
              }
            }
            """,
            variables={"show": False},
        )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert "totalCount" not in payload["data"]["allLibraryGenresConnection"]
    assert _count_queries(captured_include) == 0

    # (3) named-fragment-wrapped ``totalCount`` under ``@skip(if: true)`` -> excluded, no COUNT.
    with CaptureQueriesContext(connection) as captured_fragment:
        response = _post_graphql(
            """
            query {
              allLibraryGenresConnection(first: 2) {
                edges { node { name } }
                ...CountFields @skip(if: true)
              }
            }
            fragment CountFields on GenreTypeConnection { totalCount }
            """,
        )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert "totalCount" not in payload["data"]["allLibraryGenresConnection"]
    assert _count_queries(captured_fragment) == 0

    # Control: ``@skip(if: false)`` resolves to "keep" -> field present, COUNT fires.
    with CaptureQueriesContext(connection) as captured_kept:
        response = _post_graphql(
            """
            query {
              allLibraryGenresConnection(first: 2) {
                edges { node { name } }
                totalCount @skip(if: false)
              }
            }
            """,
        )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"]["allLibraryGenresConnection"]["totalCount"] == 3
    assert _count_queries(captured_kept) == 1


@pytest.mark.django_db
def test_anonymous_inline_fragment_under_connection_field_resolves():
    """An anonymous inline fragment under a connection field resolves cleanly.

    Regression for the optimizer-folder High. Pre-fix, a query placing an
    anonymous inline fragment (``... { f }``, ``type_condition=None``) anywhere
    under a ``DjangoConnectionField`` crashed with ``AttributeError: 'NoneType'
    object has no attribute 'name'`` - Strawberry's ``convert_selections``
    (reached via the optimizer's ``apply_to`` AND via ``info.selected_fields``
    inside Strawberry's own ``ListConnection.resolve_connection`` ->
    ``should_resolve_list_connection_edges``) reads ``type_condition.name.value``
    on the missing condition. The package now routes its own conversion through
    the anonymous-safe ``ast_to_converted_selections`` adapter and primes
    ``info.selected_fields`` with it before the connection resolver runs, so both
    shapes - the anonymous fragment directly under the connection field and one
    nested down at the ``node`` level - resolve and return the seeded genre names.
    """
    _seed_genres("Alpha", "Beta", "Gamma")
    expected = ["Alpha", "Beta", "Gamma"]

    # (a) anonymous inline fragment at the node level.
    payload = _post_graphql(
        """
        query {
          allLibraryGenresConnection {
            edges { node { ... { name } } }
          }
        }
        """,
    ).json()
    assert "errors" not in payload, payload
    node_names = [
        edge["node"]["name"] for edge in payload["data"]["allLibraryGenresConnection"]["edges"]
    ]
    assert sorted(node_names) == expected

    # (b) anonymous inline fragment directly under the connection field.
    payload = _post_graphql(
        """
        query {
          allLibraryGenresConnection {
            ... { edges { node { name } } }
          }
        }
        """,
    ).json()
    assert "errors" not in payload, payload
    under_conn_names = [
        edge["node"]["name"] for edge in payload["data"]["allLibraryGenresConnection"]["edges"]
    ]
    assert sorted(under_conn_names) == expected


@pytest.mark.django_db
def test_anonymous_inline_fragment_with_total_count_resolves():
    """``totalCount`` alongside an anonymous inline fragment resolves and counts.

    Pins the second crash site flagged in the optimizer-folder review Low: the
    ``totalCount`` fast path reads ``info.selected_fields`` (Strawberry's crashing
    ``convert_selections``) via ``_total_count_requested``, and Strawberry's own
    ``should_resolve_list_connection_edges`` reads it too. The single prime of
    ``info.selected_fields`` in ``_resolve_connection_fast_path`` routes BOTH
    reads through the anonymous-safe conversion, so a connection query carrying an
    anonymous inline fragment AND ``totalCount`` resolves: the count still fires
    (== 3) and the edges still resolve.
    """
    _seed_genres("Alpha", "Beta", "Gamma")

    payload = _post_graphql(
        """
        query {
          allLibraryGenresConnection {
            totalCount
            edges { node { ... { name } } }
          }
        }
        """,
    ).json()
    assert "errors" not in payload, payload
    conn = payload["data"]["allLibraryGenresConnection"]
    assert conn["totalCount"] == 3
    assert sorted(edge["node"]["name"] for edge in conn["edges"]) == ["Alpha", "Beta", "Gamma"]


@pytest.mark.django_db
def test_anonymous_inline_fragment_sibling_of_edges_resolves():
    """An anonymous inline fragment SIBLING of ``edges`` (wrapping ``totalCount``) resolves.

    Distinct from ``test_anonymous_inline_fragment_with_total_count_resolves`` (which
    keeps ``totalCount`` a bare connection child and puts the anonymous fragment at the
    NODE level): here the anonymous fragment (``... { totalCount }``, ``type_condition=
    None``) is a direct connection child sitting BESIDE a plain ``edges { node { name } }``
    selection, with ``first: 2`` paginating. This is the exact shape the optimizer-folder
    report flagged: pre-fix the converted-selection plan walk read ``sel.name`` /
    ``snake_case(sel.name)`` on the anonymous ``InlineFragment`` shell (``name=None``) and
    crashed with ``AttributeError: 'NoneType' object has no attribute 'name'``.

    The package routes its conversion through the anonymous-safe
    ``ast_to_converted_selections`` adapter (``type_condition=None`` instead of
    dereferencing the missing condition) and the walker descends fragment shells via
    ``is_fragment`` before reading any name, so the COUNT still fires through the
    fragment (``totalCount == 3``) while the page stays bounded to ``first: 2``.
    """
    _seed_genres("Alpha", "Beta", "Gamma")

    payload = _post_graphql(
        """
        query {
          allLibraryGenresConnection(first: 2) {
            edges { node { name } }
            ... { totalCount }
          }
        }
        """,
    ).json()
    assert "errors" not in payload, payload
    conn = payload["data"]["allLibraryGenresConnection"]
    assert conn["totalCount"] == 3
    names = [edge["node"]["name"] for edge in conn["edges"]]
    assert names == ["Alpha", "Beta"]


@pytest.mark.django_db
def test_anonymous_inline_fragment_with_directive_around_node_field_resolves():
    """A directive-bearing anonymous inline fragment around a node-level field resolves.

    Second report shape: ``edges { node { name ... @skip(if: true) { id } } }`` - the
    anonymous inline fragment (``name=None``) wraps a node-level ``id`` under
    ``@skip(if: true)``. Pre-fix the plan walk crashed reading ``sel.name`` on the
    anonymous shell; the directive only made the same unguarded name read fire on a
    skipped subtree. The walker now evaluates ``should_include`` and descends fragments
    via ``is_fragment`` before any name read, so the skipped ``id`` is pruned and the
    page resolves to the genre names alone (bounded to ``first: 2``).
    """
    _seed_genres("Alpha", "Beta", "Gamma")

    payload = _post_graphql(
        """
        query {
          allLibraryGenresConnection(first: 2) {
            edges { node { name ... @skip(if: true) { id } } }
          }
        }
        """,
    ).json()
    assert "errors" not in payload, payload
    edges = payload["data"]["allLibraryGenresConnection"]["edges"]
    assert [edge["node"]["name"] for edge in edges] == ["Alpha", "Beta"]
    assert all("id" not in edge["node"] for edge in edges)


# TODO(spec-035 Slice 3): extend this live connection-fragment block with the
# matching-type relation-planning acceptance test required by the test_query
# README. Pseudocode: seed multiple genres and books, capture SQL around
# ``allLibraryGenresConnection { edges { node { ... on GenreType { books {
# title } } } } }``, assert the response succeeds, and assert the books M2M is
# prefetched rather than loaded once per genre.
@pytest.mark.django_db
def test_typed_inline_fragment_under_connection_field_still_resolves():
    """A typed inline fragment (``... on T {}``) under a connection field stays working.

    Regression guard paired with the anonymous-fragment fix: the typed form
    carries a ``type_condition`` AST node, so Strawberry's converter never
    crashed on it. The package-owned ``ast_to_converted_selections`` adapter must
    keep the typed path resolving identically (``type_condition`` set to the
    condition's name), not just the anonymous path.
    """
    _seed_genres("Alpha", "Beta", "Gamma")

    payload = _post_graphql(
        """
        query {
          allLibraryGenresConnection {
            edges { node { ... on GenreType { name } } }
          }
        }
        """,
    ).json()
    assert "errors" not in payload, payload
    names = [
        edge["node"]["name"] for edge in payload["data"]["allLibraryGenresConnection"]["edges"]
    ]
    assert sorted(names) == ["Alpha", "Beta", "Gamma"]


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
def test_genre_books_connection_has_next_page_served_count_free_via_probe():
    """``first: N`` + ``hasNextPage`` (no ``totalCount``) is served by the n+1 probe.

    The count-free ``hasNextPage`` win over the live HTTP stack: the plain first
    page overfetches ONE sentinel row instead of a per-partition
    ``COUNT(1) OVER`` scan. Three facts are pinned - the SQL-negative that proves
    the probe fired (``_dst_row_number`` present, NO count window), the fixed
    2-query cost (root genres + one window prefetch, never 2 + N), and byte
    parity with the per-parent (optimizer-off) pipeline: the SAME page served
    through the per-parent fallback - reached by supplying an ``orderBy``
    sidecar whose order matches the window's deterministic pk order - reports
    identical edges, cursors, and ``hasNextPage``. No ``orderBy`` is supplied on
    the probe query itself (a sidecar would route it, too, to the fallback);
    the window's deterministic pk order matches the seed order.
    """
    genre = models.Genre.objects.create(name="Speculative")
    shelf = _seed_shelf()
    for title in ("Aurora", "Binti", "Circe"):
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)

    probe_query = """
        query {
          allLibraryGenres {
            booksConnection(first: 2) {
              edges { cursor node { title } }
              pageInfo { hasNextPage }
            }
          }
        }
        """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(probe_query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    conn = payload["data"]["allLibraryGenres"][0]["booksConnection"]

    # A full page over a 3-book set -> a next page exists, derived from the
    # overfetched sentinel row (not a count).
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Aurora", "Binti"]
    assert conn["pageInfo"]["hasNextPage"] is True

    # 2 queries, not 2 + N: the nested connection is windowed in one prefetch.
    assert len(captured) == 2
    window_sql = captured[1]["sql"]
    assert "_dst_row_number" in window_sql
    assert "_dst_total_count" not in window_sql
    assert "COUNT(" not in window_sql.upper()  # no per-partition count window.

    # Byte parity with the per-parent (optimizer-off) pipeline: the ``orderBy``
    # sidecar routes this to the shipped per-parent fallback, whose title order
    # equals the window's pk order for the seed. Same edges, cursors, and flag.
    fallback_query = """
        query {
          allLibraryGenres {
            booksConnection(orderBy: [{ title: ASC }], first: 2) {
              edges { cursor node { title } }
              pageInfo { hasNextPage }
            }
          }
        }
        """
    fallback_response = _post_graphql(fallback_query)
    assert fallback_response.status_code == 200
    fallback_payload = fallback_response.json()
    assert "errors" not in fallback_payload, fallback_payload
    fallback_conn = fallback_payload["data"]["allLibraryGenres"][0]["booksConnection"]
    assert fallback_conn["edges"] == conn["edges"]
    assert fallback_conn["pageInfo"]["hasNextPage"] == conn["pageInfo"]["hasNextPage"]


@pytest.mark.django_db
def test_genre_books_connection_probe_short_page_reports_no_next_page():
    """A page as large as the set: the probe finds no sentinel -> ``hasNextPage`` False.

    The other half of the byte-parity bar - a short/last page. ``first: 5`` over
    a 3-book set fetches all three and no overfetch sentinel, so ``hasNextPage``
    is False (matching the count path), still with no count window and 2 queries.
    """
    genre = models.Genre.objects.create(name="Speculative")
    shelf = _seed_shelf()
    for title in ("Aurora", "Binti", "Circe"):
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)

    query = """
        query {
          allLibraryGenres {
            booksConnection(first: 5) {
              edges { node { title } }
              pageInfo { hasNextPage }
            }
          }
        }
        """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    conn = response.json()["data"]["allLibraryGenres"][0]["booksConnection"]
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Aurora", "Binti", "Circe"]
    assert conn["pageInfo"]["hasNextPage"] is False
    assert len(captured) == 2
    window_sql = captured[1]["sql"]
    assert "_dst_total_count" not in window_sql
    assert "COUNT(" not in window_sql.upper()


@pytest.mark.django_db
def test_genre_books_connection_probe_childless_and_populated_parents():
    """The probe serves a childless parent as an empty page, next to a populated one.

    The empty-``to_attr`` branch of ``_resolve_from_window`` is load-bearing: an
    empty window must render empty ``edges`` + ``hasNextPage`` False - never
    confused with a missing sentinel or routed to a per-parent fallback. Pinned
    LIVE over /graphql for a populated parent (full page -> next page) AND a
    childless parent (empty page -> no next page) in ONE request, in both the
    ``edges`` + ``pageInfo`` shape and the no-``edges`` (``pageInfo``-only) shape,
    still count-free (the n+1 probe: no ``_dst_total_count`` / ``COUNT`` window)
    and in the fixed two-query cost regardless of parent count.
    """
    shelf = _seed_shelf()
    populated = models.Genre.objects.create(name="Populated")
    for title in ("Aurora", "Binti", "Circe"):
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(populated)
    models.Genre.objects.create(name="Empty")  # childless parent, no books.

    edges_query = """
        query {
          allLibraryGenres {
            name
            booksConnection(first: 2) {
              edges { node { title } }
              pageInfo { hasNextPage }
            }
          }
        }
        """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(edges_query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    by_name = {row["name"]: row["booksConnection"] for row in payload["data"]["allLibraryGenres"]}
    # Populated: a full first page over 3 books -> the sentinel signals a next page.
    assert [edge["node"]["title"] for edge in by_name["Populated"]["edges"]] == ["Aurora", "Binti"]
    assert by_name["Populated"]["pageInfo"]["hasNextPage"] is True
    # Childless: empty edges + no next page (the empty-window branch, not a fallback).
    assert by_name["Empty"]["edges"] == []
    assert by_name["Empty"]["pageInfo"]["hasNextPage"] is False
    # Still one root query + one windowed prefetch, count-free, for BOTH parents.
    assert len(captured) == 2
    window_sql = captured[1]["sql"]
    assert "_dst_total_count" not in window_sql
    assert "COUNT(" not in window_sql.upper()

    # The no-``edges`` shape: ``hasNextPage`` still resolves for both parents.
    no_edges_query = """
        query {
          allLibraryGenres {
            name
            booksConnection(first: 2) { pageInfo { hasNextPage } }
          }
        }
        """
    no_edges_response = _post_graphql(no_edges_query)
    assert no_edges_response.status_code == 200
    no_edges_payload = no_edges_response.json()
    assert "errors" not in no_edges_payload, no_edges_payload
    flags = {
        row["name"]: row["booksConnection"]["pageInfo"]["hasNextPage"]
        for row in no_edges_payload["data"]["allLibraryGenres"]
    }
    assert flags == {"Populated": True, "Empty": False}


@pytest.mark.django_db
def test_genre_books_connection_alias_merge_probe_plus_edges_drops_the_sentinel():
    """Same-arg aliases share ONE overfetched window; the sentinel never leaks.

    The alias-merge regression for the probe: ``a`` selects
    ``pageInfo { hasNextPage }`` (which alone takes the count-free n+1 probe) and
    ``b`` selects only ``edges`` under the SAME ``first: 2`` arguments, so
    spec-033 Decision 6 merges them into one shared window. The window is
    overfetched to ``LIMIT 3`` from the MERGED selection, so the resolver must
    drop the sentinel row for EVERY alias - not just the one that selected
    ``hasNextPage`` - or ``b`` would render 3 edges instead of 2. The probe is
    read off the window's physical shape (no ``_dst_total_count`` annotation),
    not each alias's ``info``, so both aliases resolve identically: ``a`` reports
    the next page, ``b`` returns exactly its page of 2. Byte-parity with the
    per-parent pipeline (the ``orderBy`` sidecar reference) is pinned for both.
    """
    genre = models.Genre.objects.create(name="Speculative")
    shelf = _seed_shelf()
    for title in ("Aurora", "Binti", "Circe"):
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)

    merged_query = """
        query {
          allLibraryGenres {
            a: booksConnection(first: 2) { pageInfo { hasNextPage } }
            b: booksConnection(first: 2) { edges { cursor node { title } } }
          }
        }
        """
    response = _post_graphql(merged_query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    node = payload["data"]["allLibraryGenres"][0]
    # ``b`` (edges-only) must NOT leak the overfetched sentinel: exactly its page.
    assert [edge["node"]["title"] for edge in node["b"]["edges"]] == ["Aurora", "Binti"]
    # ``a`` (hasNextPage-only) still reports the next page from the same window.
    assert node["a"]["pageInfo"]["hasNextPage"] is True

    # Byte parity: the per-parent fallback (via the ``orderBy`` sidecar) serves
    # the identical edges for the edges-only alias.
    fallback_query = """
        query {
          allLibraryGenres {
            b: booksConnection(orderBy: [{ title: ASC }], first: 2) {
              edges { cursor node { title } }
            }
          }
        }
        """
    fallback = _post_graphql(fallback_query).json()["data"]["allLibraryGenres"][0]["b"]
    assert fallback["edges"] == node["b"]["edges"]


@pytest.mark.django_db
def test_genres_connection_alias_merge_total_count_sibling_keeps_has_next():
    """A ``totalCount`` sibling keeps the count; the probe alias reads the true flag.

    The other alias-merge direction. ``a`` selects only
    ``pageInfo { hasNextPage }`` and ``b`` selects ``totalCount`` under the SAME
    ``first: 2`` args, so the merged window keeps ``_dst_total_count`` (a
    ``totalCount`` observer forces it) and is NOT overfetched. If the resolver
    re-derived the probe from ``a``'s own selection it would expect an overfetch
    that never happened and report ``hasNextPage: false`` off the un-probed
    window - a silently wrong flag even though the count (3) sits on the rows.
    Reading the physical shape, ``a`` falls back to ``row_number < total``
    (2 < 3) and correctly reports the next page. Uses ``genresConnection``
    because ``GenreType`` exposes ``totalCount`` (``BookType`` does not).
    """
    shelf = _seed_shelf()
    book = models.Book.objects.create(title="Anthology", shelf=shelf)
    for name in ("Sci-Fi", "Fantasy", "Horror"):
        book.genres.add(models.Genre.objects.create(name=name))

    query = """
        query {
          allLibraryBooks {
            a: genresConnection(first: 2) { pageInfo { hasNextPage } }
            b: genresConnection(first: 2) { totalCount edges { node { name } } }
          }
        }
        """
    response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    target = next(
        bk
        for bk in payload["data"]["allLibraryBooks"]
        if bk["a"] is not None and bk["b"]["totalCount"] == 3
    )
    # 3 genres, page of 2 -> a next page exists, read from the retained count.
    assert target["a"]["pageInfo"]["hasNextPage"] is True
    assert len(target["b"]["edges"]) == 2


@pytest.mark.django_db
def test_genre_books_connection_divergent_aliases_batched_per_key():
    """Divergent aliases are batched: one window query PER ALIAS, never per-parent.

    The idea-#2 win over the live HTTP stack (the graph-node model: one batched
    children query per response key). ``a: booksConnection(first: 2)`` +
    ``b: booksConnection(first: 9)`` was the historical whole-relation
    per-parent fallback; now each response key gets its own windowed prefetch
    (``_dst_books$a_connection`` / ``_dst_books$b_connection``) and the
    resolver routes by ``info.path.key``. Pinned: the fixed 3-query cost (root
    genres + one window per alias - independent of parent count), each alias's
    OWN page bound and ``hasNextPage`` (both served count-free by the n+1
    probe - no alias observes ``totalCount``), and byte parity for both
    aliases with the per-parent pipeline (the ``orderBy`` sidecar reference,
    whose title order equals the window's pk order for this seed).
    """
    shelf = _seed_shelf()
    for name in ("Speculative", "Poetry"):
        genre = models.Genre.objects.create(name=name)
        for title in (
            "Aurora",
            "Binti",
            "Circe",
            "Dune",
        ):
            book = models.Book.objects.get_or_create(title=title, shelf=shelf)[0]
            book.genres.add(genre)

    divergent_query = """
        query {
          allLibraryGenres {
            a: booksConnection(first: 2) {
              edges { cursor node { title } }
              pageInfo { hasNextPage }
            }
            b: booksConnection(first: 9) {
              edges { cursor node { title } }
              pageInfo { hasNextPage }
            }
          }
        }
        """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(divergent_query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    rows = payload["data"]["allLibraryGenres"]
    assert len(rows) == 2  # the fixed cost below holds ACROSS parents.
    for row in rows:
        # ``a``: its own 2-bound window; the sentinel signals a next page.
        assert [edge["node"]["title"] for edge in row["a"]["edges"]] == ["Aurora", "Binti"]
        assert row["a"]["pageInfo"]["hasNextPage"] is True
        # ``b``: its own 9-bound window; all four books, no next page.
        assert [edge["node"]["title"] for edge in row["b"]["edges"]] == [
            "Aurora",
            "Binti",
            "Circe",
            "Dune",
        ]
        assert row["b"]["pageInfo"]["hasNextPage"] is False

    # 3 queries: root genres + ONE batched window per alias (never 1 + parents x aliases).
    assert len(captured) == 3
    window_sqls = [entry["sql"] for entry in captured[1:]]
    for window_sql in window_sqls:
        assert "_dst_row_number" in window_sql
        # Both windows serve ``hasNextPage`` count-free via the probe.
        assert "_dst_total_count" not in window_sql
        assert "COUNT(" not in window_sql.upper()

    # Byte parity: the per-parent fallback (via the ``orderBy`` sidecar) serves
    # identical edges, cursors, and flags for BOTH aliases.
    fallback_query = """
        query {
          allLibraryGenres {
            a: booksConnection(orderBy: [{ title: ASC }], first: 2) {
              edges { cursor node { title } }
              pageInfo { hasNextPage }
            }
            b: booksConnection(orderBy: [{ title: ASC }], first: 9) {
              edges { cursor node { title } }
              pageInfo { hasNextPage }
            }
          }
        }
        """
    fallback_payload = _post_graphql(fallback_query).json()
    assert "errors" not in fallback_payload, fallback_payload
    assert fallback_payload["data"] == payload["data"]


def _seed_genre_books(*titles: str) -> models.Genre:
    """Seed one genre with ``titles`` books (pk / window order == argument order)."""
    genre = models.Genre.objects.create(name="Speculative")
    shelf = _seed_shelf()
    for title in titles:
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)
    return genre


def _genre_books_connection(arguments: str, selection: str):
    """Post one anonymous ``allLibraryGenres[0].booksConnection`` page + captured SQL.

    Returns ``(connection_payload, captured)`` so the WS-A count-policy pins can
    assert the served page AND the SQL shape (count-free vs counted) plus the
    fixed two-query cost (no per-parent fallback) in one place.
    """
    # An unbounded page passes no arguments; GraphQL rejects an empty ``()``
    # argument list, so emit the parens only when there are arguments.
    arg_clause = f"({arguments})" if arguments else ""
    query = f"""
        query {{
          allLibraryGenres {{
            booksConnection{arg_clause} {{ {selection} }}
          }}
        }}
        """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    return payload["data"]["allLibraryGenres"][0]["booksConnection"], captured


def _array_cursor(index: int) -> str:
    """The ``arrayconnection`` cursor for a 0-based offset index (matches endCursor)."""
    return relay.to_base64("arrayconnection", str(index))


@pytest.mark.django_db
def test_genre_books_connection_offset_page_probe_composes_marker_count_free():
    """WS-A A1: the bounded offset page serves ``hasNextPage`` from the composed probe.

    ``after:`` offset with ``first: N`` + ``hasNextPage`` (no ``totalCount``) now
    overfetches ONE sentinel row composed with the marker, so ``hasNextPage`` is
    the sentinel's presence - NO ``Count(1) OVER`` scan. Pinned both boundary
    directions (a sentinel exists -> True; the partition ends exactly at
    offset+limit -> False), the count-free SQL, and the fixed two-query cost.
    """
    _seed_genre_books("Aurora", "Binti", "Circe", "Delta", "Echo")

    # offset 1 (after index 0), first 2 -> [Binti, Circe]; Delta is the sentinel.
    conn, captured = _genre_books_connection(
        f'first: 2, after: "{_array_cursor(0)}"',
        "edges { node { title } } pageInfo { hasNextPage hasPreviousPage }",
    )
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Binti", "Circe"]
    assert conn["pageInfo"]["hasNextPage"] is True
    assert conn["pageInfo"]["hasPreviousPage"] is True
    assert len(captured) == 2
    window_sql = captured[1]["sql"]
    assert "_dst_total_count" not in window_sql
    assert "COUNT(" not in window_sql.upper()

    # offset 3 (after index 2), first 2 -> [Delta, Echo]; the partition ends
    # exactly at offset+limit, so NO sentinel -> hasNextPage False (boundary).
    boundary, boundary_captured = _genre_books_connection(
        f'first: 2, after: "{_array_cursor(2)}"',
        "edges { node { title } } pageInfo { hasNextPage }",
    )
    assert [edge["node"]["title"] for edge in boundary["edges"]] == ["Delta", "Echo"]
    assert boundary["pageInfo"]["hasNextPage"] is False
    assert len(boundary_captured) == 2
    assert "_dst_total_count" not in boundary_captured[1]["sql"]


@pytest.mark.django_db
def test_genre_books_connection_offset_page_edges_only_served_count_free():
    """WS-A: an edges-only bounded offset page serves the page count-free, no fallback.

    Neither ``hasNextPage`` nor ``totalCount`` is selected, so the window is
    planned without the probe - but the offset marker still lands and the
    resolver serves the page from ``offset < rn <= upper_bound`` with no count
    window and no per-parent fallback.
    """
    _seed_genre_books("Aurora", "Binti", "Circe", "Delta")
    conn, captured = _genre_books_connection(
        f'first: 2, after: "{_array_cursor(0)}"',
        "edges { cursor node { title } }",
    )
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Binti", "Circe"]
    assert len(captured) == 2  # no per-parent fallback.
    window_sql = captured[1]["sql"]
    assert "_dst_total_count" not in window_sql
    assert "COUNT(" not in window_sql.upper()


@pytest.mark.django_db
def test_genre_books_connection_offset_overshoot_served_count_free_no_fallback():
    """WS-A: an overshot ``after:`` on the offset page serves an empty page, no fallback.

    Both the ``hasNextPage``-only shape and the edges-only shape (the Gap-6b hole):
    the marker proves ``total <= offset``, so ``hasNextPage`` is False and the
    edges are empty - served directly, count-free, in the fixed two-query cost
    (a per-parent fallback would be an N+1 regression vs today).
    """
    _seed_genre_books("Aurora", "Binti", "Circe")
    overshoot = _array_cursor(9)  # far past the 3-book partition.

    has_next, has_next_captured = _genre_books_connection(
        f'first: 2, after: "{overshoot}"',
        "edges { node { title } } pageInfo { hasNextPage }",
    )
    assert has_next["edges"] == []
    assert has_next["pageInfo"]["hasNextPage"] is False
    assert len(has_next_captured) == 2
    assert "_dst_total_count" not in has_next_captured[1]["sql"]

    edges_only, edges_captured = _genre_books_connection(
        f'first: 2, after: "{overshoot}"',
        "edges { node { title } }",
    )
    assert edges_only["edges"] == []
    assert len(edges_captured) == 2  # Gap-6b: served, not per-parent fallback.
    assert "_dst_total_count" not in edges_captured[1]["sql"]


@pytest.mark.django_db
def test_genre_books_connection_unbounded_overshoot_served_count_free_no_fallback():
    """WS-A finding-2 hole: ``after:`` past the end with NO ``first`` is served count-free.

    An unbounded overshot page must serve the empty page from the marker-only
    window (``total <= offset``), never silently degrade to a per-parent
    fallback. Pinned: empty edges, ``hasNextPage`` False, count-free, two queries.
    """
    _seed_genre_books("Aurora", "Binti", "Circe")
    conn, captured = _genre_books_connection(
        f'after: "{_array_cursor(9)}"',
        "edges { node { title } } pageInfo { hasNextPage }",
    )
    assert conn["edges"] == []
    assert conn["pageInfo"]["hasNextPage"] is False
    assert len(captured) == 2  # NO per-parent fallback.
    window_sql = captured[1]["sql"]
    assert "_dst_total_count" not in window_sql
    assert "COUNT(" not in window_sql.upper()


@pytest.mark.django_db
def test_genre_books_connection_empty_partition_on_page_two_served_count_free():
    """WS-A: a childless parent queried with ``after:`` serves an empty page, no fallback.

    The empty-window branch on an offset page: no rows (not even a marker) means
    the parent has no children, so the empty page is served count-free with
    ``hasNextPage`` False and the fixed two-query cost.
    """
    models.Genre.objects.create(name="Empty")
    conn, captured = _genre_books_connection(
        f'first: 2, after: "{_array_cursor(0)}"',
        "edges { node { title } } pageInfo { hasNextPage }",
    )
    assert conn["edges"] == []
    assert conn["pageInfo"]["hasNextPage"] is False
    assert len(captured) == 2
    assert "_dst_total_count" not in captured[1]["sql"]


@pytest.mark.django_db
def test_genre_books_connection_last_page_has_next_page_constant_false_count_free():
    """WS-A A2: reversed ``last: N`` serves ``hasNextPage`` as a constant False, count-free.

    A ``last``-only page is the partition's tail, so ``hasNextPage`` is False by
    construction - no ``Count(1) OVER`` needed. ``hasPreviousPage`` still derives
    from the forward row number. Pinned: correct tail edges, both flags,
    count-free SQL, two queries.
    """
    _seed_genre_books("Aurora", "Binti", "Circe", "Delta", "Echo")
    conn, captured = _genre_books_connection(
        "last: 2",
        "edges { node { title } } pageInfo { hasNextPage hasPreviousPage }",
    )
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Delta", "Echo"]
    assert conn["pageInfo"]["hasNextPage"] is False
    assert conn["pageInfo"]["hasPreviousPage"] is True
    assert len(captured) == 2
    window_sql = captured[1]["sql"]
    assert "_dst_total_count" not in window_sql
    assert "COUNT(" not in window_sql.upper()


@pytest.mark.django_db
def test_genre_books_connection_unbounded_edges_and_has_next_page_count_free():
    """WS-A A2: an unbounded forward page serves ``hasNextPage`` False, count-free.

    A served unbounded page ends at the partition's last row, so ``hasNextPage``
    is a constant False - the count is dropped. Pinned: every edge, the constant
    flag, count-free SQL, two queries.
    """
    _seed_genre_books("Aurora", "Binti", "Circe")
    conn, captured = _genre_books_connection(
        "",
        "edges { node { title } } pageInfo { hasNextPage }",
    )
    assert [edge["node"]["title"] for edge in conn["edges"]] == ["Aurora", "Binti", "Circe"]
    assert conn["pageInfo"]["hasNextPage"] is False
    assert len(captured) == 2
    window_sql = captured[1]["sql"]
    assert "_dst_total_count" not in window_sql
    assert "COUNT(" not in window_sql.upper()


@pytest.mark.django_db
def test_genre_books_connection_offset_alias_merge_composes_probe_and_marker():
    """WS-A: composed-offset aliases share ONE window; sentinel AND marker never leak.

    ``a`` selects ``pageInfo { hasNextPage }`` (the offset probe) and ``b`` selects
    only ``edges`` under the SAME ``first: 2, after:`` args, so Decision 6 merges
    them into one overfetched, marker-bearing window. The resolver must drop both
    the sentinel AND the marker for EVERY alias: ``b`` renders exactly its page of
    2, ``a`` reports the next page. Count-free throughout.
    """
    _seed_genre_books("Aurora", "Binti", "Circe", "Delta", "Echo")
    after = _array_cursor(0)  # offset 1.
    query = f"""
        query {{
          allLibraryGenres {{
            a: booksConnection(first: 2, after: "{after}") {{ pageInfo {{ hasNextPage }} }}
            b: booksConnection(first: 2, after: "{after}") {{ edges {{ node {{ title }} }} }}
          }}
        }}
        """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    node = payload["data"]["allLibraryGenres"][0]
    assert [edge["node"]["title"] for edge in node["b"]["edges"]] == ["Binti", "Circe"]
    assert node["a"]["pageInfo"]["hasNextPage"] is True
    for window_sql in (entry["sql"] for entry in captured[1:]):
        assert "_dst_total_count" not in window_sql
        assert "COUNT(" not in window_sql.upper()


@pytest.mark.django_db
def test_book_genres_connection_last_page_with_total_count_stays_counted():
    """WS-A regression pin: ``last: N`` + ``totalCount`` keeps the count (unchanged).

    The A2 constant-False path applies ONLY when ``totalCount`` is not observed;
    a reversed page that DOES select ``totalCount`` still annotates the partition
    count and serves its true value. Uses ``genresConnection`` (which exposes
    ``totalCount``) on a book with three genres.
    """
    shelf = _seed_shelf()
    book = models.Book.objects.create(title="Anthology", shelf=shelf)
    for name in ("Sci-Fi", "Fantasy", "Horror"):
        book.genres.add(models.Genre.objects.create(name=name))

    query = """
        query {
          allLibraryBooks {
            genresConnection(last: 2) {
              totalCount
              edges { node { name } }
              pageInfo { hasPreviousPage hasNextPage }
            }
          }
        }
        """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    target = next(
        row["genresConnection"]
        for row in payload["data"]["allLibraryBooks"]
        if row["genresConnection"]["totalCount"] == 3
    )
    assert target["totalCount"] == 3
    assert [edge["node"]["name"] for edge in target["edges"]] == ["Fantasy", "Horror"]
    assert target["pageInfo"]["hasPreviousPage"] is True
    assert target["pageInfo"]["hasNextPage"] is False
    # The count IS annotated for the counted reverse page (regression pin).
    executed = " ".join(entry["sql"] for entry in captured)
    assert "_dst_total_count" in executed


@pytest.mark.django_db
def test_genre_books_connection_divergent_sidecar_alias_isolated():
    """A sidecar alias resolves per-parent WITHOUT dragging its divergent sibling.

    Mixed shape (idea #2 per-key gates): ``a`` carries an ``orderBy`` sidecar
    (per-parent by design - Decision 6), ``b`` is a plain page served from its
    own per-key window. Each alias's rows must be correct for ITS arguments,
    and exactly ONE batched window query runs (``b``'s; ``a`` never plans one).
    """
    genre = models.Genre.objects.create(name="Speculative")
    shelf = _seed_shelf()
    for title in ("Aurora", "Binti", "Circe"):
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)

    query = """
        query {
          allLibraryGenres {
            a: booksConnection(orderBy: [{ title: DESC }], first: 2) {
              edges { node { title } }
            }
            b: booksConnection(first: 2) {
              edges { node { title } }
            }
          }
        }
        """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    node = payload["data"]["allLibraryGenres"][0]
    # ``a`` honors its sidecar order (per-parent pipeline).
    assert [edge["node"]["title"] for edge in node["a"]["edges"]] == ["Circe", "Binti"]
    # ``b`` serves its plain pk-order page (per-key window).
    assert [edge["node"]["title"] for edge in node["b"]["edges"]] == ["Aurora", "Binti"]
    # Exactly one batched window ran - ``b``'s; the sidecar alias planned none.
    window_sqls = [entry["sql"] for entry in captured if "_dst_row_number" in entry["sql"]]
    assert len(window_sqls) == 1


@pytest.mark.django_db
def test_genres_connection_divergent_total_count_sibling_keeps_count_on_both():
    """A ``totalCount`` alias keeps the count on EVERY divergent window (union rule).

    The divergent twin of the alias-merge count-sibling pin: the count/probe
    observers are read off the merged UNION selection, so ``b`` observing
    ``totalCount`` retains ``_dst_total_count`` on ``a``'s window too -
    conservative and correct. ``a`` (page of 1 over 3 genres) reads its true
    ``hasNextPage`` from the retained count; ``b`` reports its own page of 2
    and the full count of 3 - two different windows, one shared decision.
    """
    shelf = _seed_shelf()
    book = models.Book.objects.create(title="Anthology", shelf=shelf)
    for name in ("Sci-Fi", "Fantasy", "Horror"):
        book.genres.add(models.Genre.objects.create(name=name))

    query = """
        query {
          allLibraryBooks {
            a: genresConnection(first: 1) { pageInfo { hasNextPage } }
            b: genresConnection(first: 2) { totalCount edges { node { name } } }
          }
        }
        """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    target = next(
        bk
        for bk in payload["data"]["allLibraryBooks"]
        if bk["a"] is not None and bk["b"]["totalCount"] == 3
    )
    assert target["a"]["pageInfo"]["hasNextPage"] is True
    assert len(target["b"]["edges"]) == 2
    # BOTH per-key windows carry the count; NEITHER overfetches a probe sentinel.
    window_sqls = [entry["sql"] for entry in captured if "_dst_row_number" in entry["sql"]]
    assert len(window_sqls) == 2
    for window_sql in window_sqls:
        assert "_dst_total_count" in window_sql


def _seed_two_genres_three_shared_books():
    """Two genres; three books, each carrying BOTH genres (nested-page fodder)."""
    shelf = _seed_shelf()
    alpha = models.Genre.objects.create(name="G-Alpha")
    beta = models.Genre.objects.create(name="G-Beta")
    for title in ("Aurora", "Binti", "Circe"):
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(alpha, beta)


@pytest.mark.django_db
def test_divergent_aliases_nested_same_key_conflict_serves_each_subtree_args():
    """A same-key nested conflict under divergent aliases serves each subtree's args.

    The idea-#2 review P0: both alias subtrees select ``genresConnection``
    (ONE response key) with DIFFERENT ``first`` values. The union merge must
    flag the conflict and leave the NESTED level per-parent - a silent
    first-payload-wins window served ``b``'s books one genre instead of two.
    The OUTER relation still gets its per-key windows, and the whole payload
    is byte-identical to the per-parent reference (the ``orderBy`` sidecar on
    the outer aliases, whose title order equals pk order for this seed).
    """
    _seed_two_genres_three_shared_books()

    def _nested_query(outer_extra: str) -> str:
        return f"""
        query {{
          allLibraryGenres {{
            name
            a: booksConnection({outer_extra}first: 1) {{
              edges {{ node {{ title
                genresConnection(first: 1) {{ edges {{ node {{ name }} }} }}
              }} }}
            }}
            b: booksConnection({outer_extra}first: 9) {{
              edges {{ node {{ title
                genresConnection(first: 2) {{ edges {{ node {{ name }} }} }}
              }} }}
            }}
          }}
        }}
        """

    response = _post_graphql(_nested_query(""))
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    for genre_row in payload["data"]["allLibraryGenres"]:
        # ``a``'s subtree asked for 1 nested genre per book...
        for edge in genre_row["a"]["edges"]:
            assert len(edge["node"]["genresConnection"]["edges"]) == 1
        # ...and ``b``'s asked for 2 - the P0 served it 1 (first-payload-wins).
        assert len(genre_row["b"]["edges"]) == 3
        for edge in genre_row["b"]["edges"]:
            nested = [e["node"]["name"] for e in edge["node"]["genresConnection"]["edges"]]
            assert nested == ["G-Alpha", "G-Beta"]

    # Byte parity with the fully per-parent reference (outer sidecar fallback).
    reference = _post_graphql(_nested_query("orderBy: [{ title: ASC }], ")).json()
    assert "errors" not in reference, reference
    assert reference["data"] == payload["data"]


@pytest.mark.django_db
def test_identical_aliases_nested_same_key_conflict_serves_each_subtree_args():
    """The nested same-key conflict under IDENTICAL-args aliases (pre-existing bug).

    Same-argument outer aliases share ONE merged window (spec-033 Decision 6),
    so their union-merged children hit the same conflict: ``a``'s subtree
    selects ``genresConnection(first: 1)`` and ``b``'s ``(first: 2)`` under
    one response key. This shape returned wrong data even BEFORE idea #2
    (first-payload-wins at HEAD); the conflict gate now routes the nested
    level per-parent while the outer keeps its shared window.
    """
    _seed_two_genres_three_shared_books()
    response = _post_graphql(
        """
        query {
          allLibraryGenres {
            a: booksConnection(first: 2) {
              edges { node { title
                genresConnection(first: 1) { edges { node { name } } }
              } }
            }
            b: booksConnection(first: 2) {
              edges { node { title
                genresConnection(first: 2) { edges { node { name } } }
              } }
            }
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    for genre_row in payload["data"]["allLibraryGenres"]:
        for edge in genre_row["a"]["edges"]:
            assert len(edge["node"]["genresConnection"]["edges"]) == 1
        for edge in genre_row["b"]["edges"]:
            assert len(edge["node"]["genresConnection"]["edges"]) == 2


@pytest.mark.django_db
def test_plain_list_aliases_nested_same_key_conflict_serves_each_subtree_args():
    """The nested same-key conflict under merged plain LIST aliases (pre-existing bug).

    ``a: books`` + ``b: books`` (no arguments) merge into one prefetched list;
    their subtrees carry ``genresConnection`` with different ``first`` values
    under one response key. Third shape of the same collapse - the conflict
    gate leaves the nested connection per-parent so each alias subtree's own
    page size is honored.
    """
    _seed_two_genres_three_shared_books()
    response = _post_graphql(
        """
        query {
          allLibraryGenres {
            a: books { title genresConnection(first: 1) { edges { node { name } } } }
            b: books { title genresConnection(first: 2) { edges { node { name } } } }
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    for genre_row in payload["data"]["allLibraryGenres"]:
        assert len(genre_row["a"]) == 3
        for book in genre_row["a"]:
            assert len(book["genresConnection"]["edges"]) == 1
        for book in genre_row["b"]:
            nested = [e["node"]["name"] for e in book["genresConnection"]["edges"]]
            assert nested == ["G-Alpha", "G-Beta"]


@pytest.mark.django_db
def test_genre_books_connection_after_last_page_info_matches_per_parent():
    """``booksConnection(after: c, last: N)`` reports the per-parent ``hasPreviousPage``.

    The offset-bearing backward window regression (spec-033 Decision 5): an
    ``after`` + ``last`` nested connection used to slip into the reversed
    row-number window with a NON-ZERO offset, returning the right rows but a
    ``hasPreviousPage`` that diverged from the per-parent pipeline whenever the
    after-remainder was ``<= last`` rows. The reversed window numbers rows from
    the partition END but ``_dst_row_number`` (and thus the page flags) stays
    FORWARD over the whole partition, so for an ``after``-trimmed tail of two
    rows numbered 4, 5 the fast path read ``hasPreviousPage = (4 > 1) = True``,
    while the per-parent pipeline slices the last ``N`` of the two-row after-set
    and reports ``hasPreviousPage = False`` (nothing was trimmed off the front).

    The fix makes ``after`` + ``last`` an unwindowable fallback: the walker leaves
    the selection unplanned and the shipped per-parent pipeline serves it, so the
    optimizer-on ``/graphql/`` answer matches the optimizer-off truth. NO sidecar
    is supplied so the shape itself - not the sidecar gate - is what routes to the
    fallback (the connection orders by pk via the deterministic-order rule).
    """
    genre = models.Genre.objects.create(name="Speculative")
    shelf = _seed_shelf()
    # Five books in pk order; cursors are positional (arrayconnection:0..4).
    for title in (
        "Aurora",
        "Binti",
        "Circe",
        "Dune",
        "Elantris",
    ):
        book = models.Book.objects.create(title=title, shelf=shelf)
        book.genres.add(genre)

    def _books_page(args: str) -> dict:
        response = _post_graphql(
            f"""
            query {{
              allLibraryGenres {{
                booksConnection({args}) {{
                  edges {{ cursor node {{ title }} }}
                  pageInfo {{ hasNextPage hasPreviousPage startCursor endCursor }}
                }}
              }}
            }}
            """,
        )
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        return payload["data"]["allLibraryGenres"][0]["booksConnection"]

    # Page forward to the third book ("Circe") to obtain a real ``after`` cursor;
    # the after-set is then {Dune, Elantris} - exactly two rows, ``<= last: 3``.
    forward = _books_page("first: 3")
    after_cursor = forward["pageInfo"]["endCursor"]

    page = _books_page(f'after: "{after_cursor}", last: 3')
    titles = [edge["node"]["title"] for edge in page["edges"]]
    # Right rows: the whole two-row after-tail (last: 3 of 2 rows = both).
    assert titles == ["Dune", "Elantris"]
    # The regression assertion: the after-remainder (2) is ``<= last`` (3), so the
    # pipeline trims nothing off the front and ``hasPreviousPage`` is False - the
    # buggy reversed-window fast path reported True here.
    assert page["pageInfo"]["hasPreviousPage"] is False
    assert page["pageInfo"]["hasNextPage"] is False
    # Cursors stay positional and byte-match the forward window's (Dune/Elantris
    # are positions 3/4), proving the per-parent pipeline served the page.
    forward_two = _books_page("first: 5")
    forward_cursors = {edge["node"]["title"]: edge["cursor"] for edge in forward_two["edges"]}
    page_cursors = {edge["node"]["title"]: edge["cursor"] for edge in page["edges"]}
    assert page_cursors == {
        "Dune": forward_cursors["Dune"],
        "Elantris": forward_cursors["Elantris"],
    }


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
    ``edges`` selected still reports ``hasNextPage`` True - this is the plain
    first-page probe shape (``hasNextPage`` selected, ``totalCount`` not), so it
    is served count-free by the n+1 overfetch sentinel, NOT a ``_dst_total_count``
    annotation, in the same fixed two-query window (root genres-connection + one
    ``booksConnection`` prefetch), independent of parent count.
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
    # The probe shape it now describes: the window is count-free (the sentinel
    # answers ``hasNextPage``), so it carries no ``_dst_total_count`` / COUNT.
    window_sql = captured[1]["sql"]
    assert "_dst_total_count" not in window_sql
    assert "COUNT(" not in window_sql.upper()


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


# ---------------------------------------------------------------------------
# B8 consumer-prefetch collision over live /graphql/ (feedback2.md high-confidence
# moves from tests/optimizer/test_extension.py). A consumer resolver returning a
# queryset whose prefetch_related overlaps the optimizer's own Genre -> books ->
# loans plan must reconcile, not raise, and must stay flat (no per-row prefetch)
# through the configured project schema, the view/request stack, and real
# query-count assertions -- stronger than the synthetic in-process schema tests.
# ---------------------------------------------------------------------------


def _seed_genre_book_loan_graph() -> None:
    """Seed two genres -> books -> loans for the B8 consumer-prefetch tests.

    G1 owns two books (one with a loan, one without); G2 owns one book with two
    loans. The variety makes an N+1 regression explode the query count while the
    correct flat plan stays constant.
    """
    branch = models.Branch.objects.create(name="Main", city="Boston")
    shelf = models.Shelf.objects.create(code="S-1", topic="permanent collection", branch=branch)
    reader = models.Patron.objects.create(name="Reader")
    reader_two = models.Patron.objects.create(name="Reader Two")

    g1 = models.Genre.objects.create(name="G1")
    b1a = models.Book.objects.create(title="B1a", shelf=shelf)
    b1a.genres.add(g1)
    b1b = models.Book.objects.create(title="B1b", shelf=shelf)
    b1b.genres.add(g1)
    models.Loan.objects.create(book=b1a, patron=reader, note="L1")

    g2 = models.Genre.objects.create(name="G2")
    b2a = models.Book.objects.create(title="B2a", shelf=shelf)
    b2a.genres.add(g2)
    models.Loan.objects.create(book=b2a, patron=reader, note="L2")
    models.Loan.objects.create(book=b2a, patron=reader_two, note="L3")


def _assert_genre_book_loan_shape(rows: list) -> None:
    """Assert the seeded Genre -> books -> loans graph renders intact."""
    by_name = {genre["name"]: genre for genre in rows}
    assert set(by_name) == {"G1", "G2"}
    g1_books = {
        book["title"]: sorted(loan["note"] for loan in book["loans"])
        for book in by_name["G1"]["books"]
    }
    assert g1_books == {"B1a": ["L1"], "B1b": []}
    g2_books = {
        book["title"]: sorted(loan["note"] for loan in book["loans"])
        for book in by_name["G2"]["books"]
    }
    assert g2_books == {"B2a": ["L2", "L3"]}


@pytest.mark.django_db
def test_b8_consumer_descendant_prefetch_stays_flat_over_http():
    """A consumer ``prefetch_related("books__loans")`` cooperates with the optimizer.

    The live twin of ``test_b8_consumer_descendant_prefetch_does_not_raise``: the
    consumer descendant prefetch overlaps the optimizer's Genre -> books -> loans
    plan, which historically raised "'books' lookup was already seen with a
    different queryset". Over HTTP the operation must return the full nested graph
    AND stay flat -- one query each for genres, the books M2M, and the loans FK
    reverse -- never a per-book loans query.
    """
    _seed_genre_book_loan_graph()

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryGenresConsumerDescendantPrefetch {
                name
                books { title loans { note } }
              }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    _assert_genre_book_loan_shape(payload["data"]["allLibraryGenresConsumerDescendantPrefetch"])
    # Flat: genres + books prefetch + loans prefetch. An N+1 collision would
    # have raised or issued one loans query per book.
    assert len(captured) == 3


@pytest.mark.django_db
def test_b8_consumer_exact_plus_descendant_prefetch_stays_flat_over_http():
    """A consumer ``prefetch_related("books", "books__loans")`` cooperates too.

    The live twin of ``test_b8_consumer_exact_plus_descendant_prefetch_does_not_raise``:
    declaring both the exact relation and a descendant of it must reconcile with
    the optimizer plan without colliding, returning the same intact graph at the
    same flat query count.
    """
    _seed_genre_book_loan_graph()

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryGenresConsumerExactPlusDescendantPrefetch {
                name
                books { title loans { note } }
              }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    _assert_genre_book_loan_shape(
        payload["data"]["allLibraryGenresConsumerExactPlusDescendantPrefetch"],
    )
    assert len(captured) == 3


# ---------------------------------------------------------------------------
# Raw-pk relation visibility + ``to_field_name`` over a LIVE request (spec-038 /
# the test_query live-coverage rule). ``Shelf.branch`` / ``Shelf.alt_branches``
# target the NON-Relay ``BranchType`` primary, so their inputs are raw pk (not
# GlobalID); ``BranchType.get_queryset`` hides ``city="restricted"`` from non-staff,
# so an anonymous writer (the mutations use the explicit ``[]`` allow-any opt-out) can
# write but cannot attach a hidden branch.
# ``branch`` sets ``to_field_name="name"`` so the decode binds the resolved Branch
# by its unique name.
# ---------------------------------------------------------------------------


_CREATE_SHELF_VIA_FORM = (
    "mutation($d: ShelfRelationsFormInput!){ createShelfViaForm(data:$d){ "
    "result{ code } errors{ field messages } } }"
)
_CREATE_SHELF_MODEL = (
    "mutation($d: ShelfAlt_ubranchesBranchCodeInput!){ createShelf(data:$d){ "
    "result{ code } errors{ field messages } } }"
)


@pytest.mark.django_db
def test_create_shelf_via_form_hidden_branch_fk_is_relation_field_error():
    """A raw-pk FK whose Branch is hidden by ``BranchType.get_queryset`` -> field error, no write.

    The form relation decoder resolves the raw pk through the non-Relay primary's
    visibility hook; a hidden (restricted) Branch is the same field-keyed error a
    GlobalID relation gives - earned live (single FK, form path).
    """
    restricted = models.Branch.objects.create(name="FormRestrictedFK", city="restricted")
    response = _post_graphql(
        _CREATE_SHELF_VIA_FORM,
        variables={"d": {"code": "RF-1", "branchId": restricted.pk}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaForm"]
    assert result["result"] is None
    assert [e["field"] for e in result["errors"]] == ["branchId"]
    assert not models.Shelf.objects.filter(code="RF-1").exists()


@pytest.mark.django_db
def test_create_shelf_via_form_hidden_branch_in_alt_branches_is_field_error():
    """A raw-pk M2M element whose Branch is hidden -> field error, no write (multi, form path)."""
    visible = models.Branch.objects.create(name="FormVisibleM2M", city="open")
    restricted = models.Branch.objects.create(name="FormRestrictedM2M", city="restricted")
    response = _post_graphql(
        _CREATE_SHELF_VIA_FORM,
        variables={"d": {"code": "RM-1", "branchId": visible.pk, "altBranches": [restricted.pk]}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaForm"]
    assert result["result"] is None
    assert [e["field"] for e in result["errors"]] == ["altBranches"]
    assert not models.Shelf.objects.filter(code="RM-1").exists()


@pytest.mark.django_db
def test_create_shelf_via_form_visible_branch_resolves_by_to_field_name_and_writes():
    """A request-scoped visible FK resolves by ``to_field_name="name"`` and writes.

    Earns the success raw-pk decode AND the ``to_field_name`` conversion live: the
    class-level ``ModelChoiceField`` declares ``queryset=None`` and receives its real
    queryset in ``ShelfRelationsForm.__init__``. The decoder must use the target model
    recorded from the backing FK column rather than dereference the absent class-level
    queryset; it resolves the visible Branch by pk, converts it to its ``name``, and
    the bound ``ModelChoiceField(to_field_name="name")`` validates by that key.
    """
    visible = models.Branch.objects.create(name="FormVisibleOK", city="open")
    response = _post_graphql(
        _CREATE_SHELF_VIA_FORM,
        variables={"d": {"code": "OK-1", "branchId": visible.pk}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaForm"]
    assert result["errors"] == []
    assert result["result"]["code"] == "OK-1"
    shelf = models.Shelf.objects.get(code="OK-1")
    assert shelf.branch_id == visible.pk  # resolved by name (to_field_name) + written


@pytest.mark.django_db
def test_create_shelf_model_mutation_hidden_branch_is_field_error():
    """The MODEL pipeline's raw-pk relation decode hides a Branch live (``_raw_pk_relation_error``).

    The model-path twin of the form decoder's raw-pk visibility fix: a raw-pk FK to
    the non-Relay ``BranchType`` is visibility-checked through its ``get_queryset``,
    so a hidden Branch is a field-keyed error with no write.
    """
    restricted = models.Branch.objects.create(name="ModelRestrictedFK", city="restricted")
    response = _post_graphql(
        _CREATE_SHELF_MODEL,
        variables={"d": {"code": "MM-1", "branchId": restricted.pk}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelf"]
    assert result["result"] is None
    assert [e["field"] for e in result["errors"]] == ["branchId"]
    assert not models.Shelf.objects.filter(code="MM-1").exists()


@pytest.mark.django_db
def test_create_shelf_model_mutation_hidden_alt_branch_m2m_is_field_error():
    """The MODEL pipeline's raw-pk M2M decode hides a Branch live (``_raw_pk_relation_error``, multi).

    Rounds out the model-path raw-pk arm: ``createShelf`` accepts ``altBranches`` (a
    raw-pk M2M to the non-Relay ``BranchType``), so a hidden (restricted) member is a
    field-keyed error with no write - the M2M twin of the single-FK model-path case.
    The provided ``branch`` is visible, so the only failure is the hidden M2M member.
    """
    visible = models.Branch.objects.create(name="ModelVisibleM2M", city="open")
    restricted = models.Branch.objects.create(name="ModelRestrictedM2M", city="restricted")
    response = _post_graphql(
        _CREATE_SHELF_MODEL,
        variables={"d": {"code": "MM-2", "branchId": visible.pk, "altBranches": [restricted.pk]}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelf"]
    assert result["result"] is None
    assert [e["field"] for e in result["errors"]] == ["altBranches"]
    assert not models.Shelf.objects.filter(code="MM-2").exists()


_UPDATE_BOOK_VIA_FORM = (
    "mutation($id: ID!, $d: BookGenresModelFormPartialInput!){ updateBookViaForm(id:$id, data:$d){ "
    "node{ title } errors{ field messages } } }"
)


@pytest.mark.django_db
def test_update_book_via_form_partial_update_preserves_m2m_over_http():
    """A ``title``-only ``updateBookViaForm`` preserves the OMITTED required ``genres`` M2M.

    The live FORM partial-update M2M-preservation case (previously package-only): the
    bound ``ModelForm`` would fail required-validation on ``genres`` unless the omitted
    M2M is reconstructed from the located row (``_reconstruct_partial_data`` ->
    ``_to_form_key_value``). ``BookType`` is Relay-Node so the update ``id`` is a
    ``GlobalID``; ``title`` changes while the two genres survive untouched.
    """
    from apps.library.schema import BookType

    shelf = _seed_shelf()
    genre_one = models.Genre.objects.create(name="UpdGenreOne")
    genre_two = models.Genre.objects.create(name="UpdGenreTwo")
    book = models.Book.objects.create(title="BeforeFormTitle", shelf=shelf)
    book.genres.set([genre_one, genre_two])

    response = _post_graphql(
        _UPDATE_BOOK_VIA_FORM,
        variables={"id": global_id_for(BookType, book.pk), "d": {"title": "AfterFormTitle"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateBookViaForm"]
    assert result["errors"] == []
    assert result["node"]["title"] == "AfterFormTitle"
    book.refresh_from_db()
    assert book.title == "AfterFormTitle"
    # The OMITTED required M2M was reconstructed from the row (not cleared).
    assert set(book.genres.values_list("pk", flat=True)) == {genre_one.pk, genre_two.pk}


@pytest.mark.django_db
def test_update_book_via_form_partial_update_preserves_optional_nullable_scalar_over_http():
    """A ``title``-only ``updateBookViaForm`` preserves the OMITTED optional ``subtitle``.

    The distinct live optional-scalar case: ``Book.subtitle`` is genuinely optional AND
    nullable (``blank=True, null=True``), unlike the products ``description``
    (``default=""``). Omitted on a partial update, it is reconstructed from the located
    row (``_reconstruct_partial_data`` via ``model_to_dict``) rather than reset to null,
    so the seeded subtitle survives a ``title``-only change.
    """
    from apps.library.schema import BookType

    shelf = _seed_shelf()
    genre = models.Genre.objects.create(name="SubtitleGenre")
    book = models.Book.objects.create(
        title="SubBeforeTitle",
        subtitle="Original Subtitle",
        shelf=shelf,
    )
    book.genres.set([genre])

    response = _post_graphql(
        _UPDATE_BOOK_VIA_FORM,
        variables={"id": global_id_for(BookType, book.pk), "d": {"title": "SubAfterTitle"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateBookViaForm"]
    assert result["errors"] == []
    book.refresh_from_db()
    assert book.title == "SubAfterTitle"
    # The OMITTED optional nullable scalar was reconstructed (not reset to null).
    assert book.subtitle == "Original Subtitle"


# ---------------------------------------------------------------------------
# spec-036 Meta.input_class / partial_input_class merge override (over Book).
# ---------------------------------------------------------------------------


def _input_fields_by_name(type_name: str) -> dict:
    """Introspect a generated input type and index its inputFields by GraphQL name."""
    response = _post_graphql(
        'query { __type(name: "'
        + type_name
        + '") { inputFields { name type { kind name ofType { kind name } } } } }',
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    introspected = payload["data"]["__type"]
    assert introspected is not None, f"{type_name} not in schema"
    return {field["name"]: field["type"] for field in introspected["inputFields"]}


@pytest.mark.django_db
def test_book_input_class_override_merges_into_generated_create_input():
    """``Meta.input_class`` merges a required ``subtitle`` into the generated ``BookInput``.

    ``BookCreateFieldOverrides`` declares only ``subtitle`` (required); the merged
    ``BookInput`` keeps the canonical name and carries that override ALONGSIDE the
    generated remainder (``title`` / ``circulationStatus`` / ``shelfId`` / ``genres``) - so
    the merge is proven by both the override's new requiredness AND the presence of every
    generated column. ``Book.subtitle`` is ``blank/null``, so WITHOUT the override it would
    be nullable; here it renders ``NON_NULL``.
    """
    by_name = _input_fields_by_name("BookInput")
    assert set(by_name) == {
        "title",
        "subtitle",
        "circulationStatus",
        "shelfId",
        "genres",
    }
    # The override took effect: subtitle is now required (NON_NULL String).
    assert by_name["subtitle"]["kind"] == "NON_NULL"
    assert by_name["subtitle"]["ofType"] == {"kind": "SCALAR", "name": "String"}
    # Generated remainder unchanged: title + shelfId required, the rest optional.
    assert by_name["title"]["kind"] == "NON_NULL"
    assert by_name["shelfId"]["kind"] == "NON_NULL"
    assert by_name["circulationStatus"]["kind"] != "NON_NULL"
    assert by_name["genres"]["kind"] != "NON_NULL"


@pytest.mark.django_db
def test_book_partial_input_class_override_merges_into_generated_partial_input():
    """``Meta.partial_input_class`` pins ``title`` required in the otherwise-all-optional partial.

    The generated ``BookPartialInput`` makes every field optional; ``BookUpdateFieldOverrides``
    overrides ``title`` to required. The merged ``BookPartialInput`` carries ``title:
    String!`` while ``subtitle`` / ``circulationStatus`` / ``shelfId`` / ``genres`` stay
    optional - the override plus the all-optional remainder.
    """
    by_name = _input_fields_by_name("BookPartialInput")
    assert set(by_name) == {
        "title",
        "subtitle",
        "circulationStatus",
        "shelfId",
        "genres",
    }
    # The override took effect: title is required even in the partial input.
    assert by_name["title"]["kind"] == "NON_NULL"
    # Generated remainder stays optional (the partial default).
    assert by_name["subtitle"]["kind"] != "NON_NULL"
    assert by_name["shelfId"]["kind"] != "NON_NULL"
    assert by_name["circulationStatus"]["kind"] != "NON_NULL"
    assert by_name["genres"]["kind"] != "NON_NULL"


_CREATE_BOOK_VIA_CUSTOM_INPUT = (
    "mutation($d: BookInput!){ createBookViaCustomInput(data:$d){ "
    "node{ title subtitle } errors{ field messages } } }"
)


@pytest.mark.django_db
def test_create_book_via_custom_input_happy_path():
    """``createBookViaCustomInput`` creates a row through the merged ``BookInput``.

    ``permission_classes = []`` opens the path (no login). The required-``subtitle``
    override is supplied; ``shelfId`` is the raw pk (``ShelfType`` is non-Relay); the row
    persists and the Relay payload ``node`` carries it back.
    """
    shelf = _seed_shelf()

    response = _post_graphql(
        _CREATE_BOOK_VIA_CUSTOM_INPUT,
        variables={
            "d": {
                "title": "CustomBook",
                "subtitle": "required by the input_class override",
                "shelfId": shelf.pk,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createBookViaCustomInput"]
    assert result["errors"] == []
    assert result["node"] == {
        "title": "CustomBook",
        "subtitle": "required by the input_class override",
    }
    created = models.Book.objects.get(title="CustomBook", shelf=shelf)
    assert created.subtitle == "required by the input_class override"


@pytest.mark.django_db
def test_create_book_via_custom_input_omitting_overridden_required_field_errors():
    """Omitting the override-required ``subtitle`` is a top-level GraphQL coercion error.

    The override has teeth at the wire: ``subtitle`` is ``String!`` in ``BookInput``, so
    omitting it fails input coercion BEFORE execution (a top-level error, not a
    ``FieldError`` envelope), and no row is written.
    """
    shelf = _seed_shelf()

    response = _post_graphql(
        _CREATE_BOOK_VIA_CUSTOM_INPUT,
        variables={"d": {"title": "NoSubtitleBook", "shelfId": shelf.pk}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("errors"), payload  # top-level coercion error
    assert "subtitle" in str(payload["errors"])
    assert not models.Book.objects.filter(title="NoSubtitleBook").exists()


@pytest.mark.django_db
def test_update_book_via_custom_partial_input_happy_path():
    """``updateBookViaCustomInput`` updates through the merged ``BookPartialInput``.

    The ``partial_input_class`` makes ``title`` required on update; supplying it renames
    the located row, which is located through ``BookType.get_queryset`` visibility (the
    available book is visible to the anonymous caller) then re-fetched into the payload.
    The omitted optional ``subtitle`` is reconstructed from the row, not reset.
    """
    from apps.library.schema import BookType

    shelf = _seed_shelf()
    book = models.Book.objects.create(title="OldBookTitle", subtitle="keep", shelf=shelf)

    response = _post_graphql(
        "mutation($id: ID!, $d: BookPartialInput!){ updateBookViaCustomInput(id:$id, data:$d){ "
        "node{ title } errors{ field messages } } }",
        variables={"id": global_id_for(BookType, book.pk), "d": {"title": "NewBookTitle"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateBookViaCustomInput"]
    assert result["errors"] == []
    assert result["node"]["title"] == "NewBookTitle"
    book.refresh_from_db()
    assert book.title == "NewBookTitle"
    assert book.subtitle == "keep"


@pytest.mark.django_db
def test_update_book_replaces_m2m_and_returns_row_after_visibility_exit_over_http():
    """A live update fully replaces M2M membership and returns the newly hidden row.

    ``BookType.get_queryset`` hides repair-state books from anonymous callers.
    The visible seed is located through that scope, then the update both replaces
    the complete ``genres`` set and moves the book to ``repair``. The success
    payload still returns the row because post-write re-fetch intentionally uses
    the default manager; a visibility-scoped re-fetch would incorrectly lose it.
    """
    from apps.library.schema import BookType, GenreType

    shelf = _seed_shelf()
    old_one = models.Genre.objects.create(name="ReplaceOldOne")
    old_two = models.Genre.objects.create(name="ReplaceOldTwo")
    replacement = models.Genre.objects.create(name="ReplaceNew")
    book = models.Book.objects.create(title="VisibleBeforeUpdate", shelf=shelf)
    book.genres.set([old_one, old_two])

    response = _post_graphql(
        "mutation($id: ID!, $d: BookPartialInput!){ updateBookViaCustomInput(id:$id, data:$d){ "
        "node{ title } errors{ field messages } } }",
        variables={
            "id": global_id_for(BookType, book.pk),
            "d": {
                "title": "HiddenAfterUpdate",
                "circulationStatus": "repair",
                "genres": [global_id_for(GenreType, replacement.pk)],
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateBookViaCustomInput"]
    assert result["errors"] == []
    assert result["node"]["title"] == "HiddenAfterUpdate"
    book.refresh_from_db()
    assert book.circulation_status == models.Book.CirculationStatus.REPAIR
    assert set(book.genres.values_list("pk", flat=True)) == {replacement.pk}


# ---------------------------------------------------------------------------
# spec-015 custom (non-Relay) @strawberry.interface in Meta.interfaces.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_named_interface_is_implemented_by_library_types_over_http():
    """``BranchType`` / ``GenreType`` / ``PatronType`` declare the consumer ``Named`` interface.

    ``Meta.interfaces`` accepts any Strawberry interface, not only ``relay.Node``: the SDL
    exposes ``Named`` as an INTERFACE carrying ``name``, all three types are among its
    ``possibleTypes``, and each lists ``Named`` (``GenreType`` lists BOTH ``Node`` and
    ``Named``) as an implemented interface.
    """
    response = _post_graphql(
        """
        query {
          iface: __type(name: "Named") { kind fields { name } possibleTypes { name } }
          genre: __type(name: "GenreType") { interfaces { name } }
          branch: __type(name: "BranchType") { interfaces { name } }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    iface = payload["data"]["iface"]
    assert iface is not None, "Named interface missing from the SDL"
    assert iface["kind"] == "INTERFACE"
    assert {"name"} <= {f["name"] for f in iface["fields"]}
    possible = {pt["name"] for pt in iface["possibleTypes"]}
    assert {"BranchType", "GenreType", "PatronType"} <= possible
    assert {"Node", "Named"} <= {i["name"] for i in payload["data"]["genre"]["interfaces"]}
    assert "Named" in {i["name"] for i in payload["data"]["branch"]["interfaces"]}


@pytest.mark.django_db
def test_named_library_records_returns_polymorphic_interface_list_over_http():
    """``namedLibraryRecords`` returns a polymorphic ``list[Named]`` discriminated by ``__typename``.

    The custom interface is genuinely a return type: the resolver mixes Branch / Genre /
    Patron rows, ``is_type_of`` resolves each to its concrete ``DjangoType``, and the
    shared ``name`` selects directly across all three.
    """
    models.Branch.objects.create(name="IfaceBranch", city="X")
    models.Genre.objects.create(name="IfaceGenre")
    models.Patron.objects.create(name="IfacePatron", email="iface@example.com")

    response = _post_graphql("query { namedLibraryRecords { __typename name } }")
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    pairs = {(r["__typename"], r["name"]) for r in payload["data"]["namedLibraryRecords"]}
    assert ("BranchType", "IfaceBranch") in pairs
    assert ("GenreType", "IfaceGenre") in pairs
    assert ("PatronType", "IfacePatron") in pairs


@pytest.mark.django_db
def test_named_library_records_hides_restricted_branch_from_anonymous_over_http():
    """``namedLibraryRecords`` routes Branch rows through ``BranchType.get_queryset`` (feedback #3).

    The resolver materializes a plain list (no downstream queryset re-execution), so a
    direct ``Branch.objects`` read would serialize ``city="restricted"`` rows that
    ``BranchType.get_queryset`` hides from non-staff. Routing through the hook keeps the
    visible branch and drops the restricted one for an anonymous caller, while a staff
    caller (the ``get_queryset`` bypass) still sees it. Fails on the pre-fix direct read.
    """
    models.Branch.objects.create(name="NamedVisible", city="Boston")
    models.Branch.objects.create(name="NamedRestricted", city="restricted")

    response = _post_graphql("query { namedLibraryRecords { __typename name } }")
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    branch_names = {
        r["name"]
        for r in payload["data"]["namedLibraryRecords"]
        if r["__typename"] == "BranchType"
    }
    assert "NamedVisible" in branch_names
    assert "NamedRestricted" not in branch_names  # hidden by get_queryset for anonymous

    # Staff bypasses the gate, so the restricted branch is visible to them.
    staff_response = _post_graphql_as_staff("query { namedLibraryRecords { __typename name } }")
    assert staff_response.status_code == 200
    staff_payload = staff_response.json()
    assert "errors" not in staff_payload, staff_payload
    staff_branch_names = {
        r["name"]
        for r in staff_payload["data"]["namedLibraryRecords"]
        if r["__typename"] == "BranchType"
    }
    assert {"NamedVisible", "NamedRestricted"} <= staff_branch_names


# ---------------------------------------------------------------------------
# spec-038 plain-form perform_mutate write hook (custom multi-row write).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_branch_with_shelf_perform_mutate_runs_custom_write():
    """``createBranchWithShelf`` overrides ``perform_mutate`` to write two related rows.

    A model-less plain ``DjangoFormMutation`` has no ``form.save()``, so its default
    ``perform_mutate`` is a no-op. ``CreateBranchWithShelf`` overrides it to create a
    ``Branch`` plus a starter ``Shelf`` under it from the validated form data. The payload
    is the pinned ``{ ok, errors }``; both rows land in the DB.
    """
    response = _post_graphql(
        "mutation($d: BranchWithShelfFormInput!){ createBranchWithShelf(data:$d){ "
        "ok errors{ field messages } } }",
        variables={"d": {"branchName": "HookBranch", "shelfCode": "H-1"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createBranchWithShelf"]
    assert result["ok"] is True
    assert result["errors"] == []
    # perform_mutate ran the custom multi-row write inside the mutation transaction.
    branch = models.Branch.objects.get(name="HookBranch")
    assert models.Shelf.objects.filter(code="H-1", branch=branch).exists()


@pytest.mark.django_db
def test_create_branch_pair_rolls_back_first_write_when_second_conflicts():
    """An error envelope from a partial plain-form write rolls back every insert.

    ``CreateBranchPair.perform_mutate`` inserts the first unique branch before
    attempting the second. Seeding the second name forces a real database
    ``IntegrityError`` after that first write. The framework maps the failure to
    ``ok: false`` and must mark the active atomic block for rollback; otherwise
    the client would see failure while ``RollbackFirst`` remained committed.
    """
    models.Branch.objects.create(name="RollbackConflict")

    response = _post_graphql(
        "mutation($d: BranchPairFormInput!){ createBranchPair(data:$d){ "
        "ok errors{ field messages } } }",
        variables={
            "d": {"firstName": "RollbackFirst", "secondName": "RollbackConflict"},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createBranchPair"]
    assert result["ok"] is False
    assert result["errors"][0]["field"] == "__all__"
    assert not models.Branch.objects.filter(name="RollbackFirst").exists()


# ---------------------------------------------------------------------------
# Serializer-mutation surface (spec-039): get_serializer_for_schema() schema hook +
# subclass validation, earned live over /graphql/ (the README live-first mandate).
# Shelf is non-Relay, so the payload object slot is `result` and the `branch` relation
# input is a raw pk. The schema-hook / subclass inputs take descriptor-derived (non-
# canonical) names, so their input object is supplied INLINE (no typed `$d` variable).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_shelf_via_serializer_happy_path():
    """``createShelfViaSerializer`` writes a ``Shelf`` through ``ShelfSerializer`` (the subclass parent).

    The plain serializer-create path over a library model: a raw-pk ``branch`` relation
    resolves and the row writes. This is the parent the subclass mutation extends.
    """
    branch = models.Branch.objects.create(name="SerBranch", city="Boston")
    response = _post_graphql(
        "mutation($d: ShelfSerializerInput!) { createShelfViaSerializer(data: $d) { "
        "result { code } errors { field messages } } }",
        variables={"d": {"code": "SerShelf", "branchId": branch.pk}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaSerializer"]
    assert result["errors"] == []
    assert result["result"] == {"code": "SerShelf"}
    assert models.Shelf.objects.filter(code="SerShelf", branch=branch).exists()


@pytest.mark.django_db
def test_create_shelf_via_schema_hook_serializer_executes_over_http():
    """A schema-hook serializer mutation (construction-kwarg-requiring serializer) writes over HTTP.

    ``TenantShelfSerializer`` requires a ``tenant`` constructor kwarg, so default no-arg
    schema discovery fails; ``get_serializer_for_schema()`` supplies the schema-time field
    map and ``get_serializer_kwargs`` injects the runtime tenant. A successful create proves
    the schema-time hook and the runtime serializer construction AGREE; the stamped ``topic``
    (``tenant:<username>``) proves the injected tenant reached the constructed serializer.
    """
    branch = models.Branch.objects.create(name="HookBranchSer", city="Boston")
    query = (
        "mutation { createShelfViaSchemaHookSerializer(data: { "
        f'code: "HookShelf", branchId: {branch.pk} '
        "}) { result { code topic } errors { field messages } } }"
    )
    response = _post_graphql_as_staff(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaSchemaHookSerializer"]
    assert result["errors"] == []
    assert result["result"] == {"code": "HookShelf", "topic": "tenant:staff"}
    shelf = models.Shelf.objects.get(code="HookShelf", branch=branch)
    assert shelf.topic == "tenant:staff"


@pytest.mark.django_db
def test_create_shelf_via_subclassed_serializer_validates_against_child_serializer():
    """A subclass redefining ``Meta.serializer_class`` writes via the CHILD serializer over HTTP.

    ``CreateShelfViaSubclassedSerializer`` subclasses ``CreateShelfViaSerializer`` but
    redefines ``serializer_class`` to ``RenamedShelfSerializer`` + ``fields = (shelf_code,
    branch)``. The schema even building (the reload fixture) proves the child validated
    against its OWN serializer - the inherited parent (``ShelfSerializer``) snapshot would
    reject ``shelf_code`` as unknown at class creation. A real ``/graphql/`` create writes
    through the renamed wire name ``shelfCode``.
    """
    branch = models.Branch.objects.create(name="SubclassBranch", city="Boston")
    query = (
        "mutation { createShelfViaSubclassedSerializer(data: { "
        f'shelfCode: "SubclassShelf", branchId: {branch.pk} '
        "}) { result { code } errors { field messages } } }"
    )
    response = _post_graphql_as_staff(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaSubclassedSerializer"]
    assert result["errors"] == []
    assert result["result"] == {"code": "SubclassShelf"}
    assert models.Shelf.objects.filter(code="SubclassShelf", branch=branch).exists()


@pytest.mark.django_db
def test_create_shelf_rejecting_serializer_save_time_all_sentinel():
    """A serializer ``save()`` raising a BARE DRF ``ValidationError`` surfaces as the ``"__all__"`` envelope.

    Field validation passes (valid ``code`` + ``branch``); the serializer then rejects the
    whole object at save with a bare (non-dict) ``ValidationError`` detail. The recursive
    flattener normalizes its empty path to the ``"__all__"`` sentinel - ``result`` is null
    and no row is written (the write rolled back).
    """
    branch = models.Branch.objects.create(name="RejectBranch", city="Boston")
    response = _post_graphql(
        "mutation($d: RejectingShelfSerializerInput!) { createShelfRejectingViaSerializer(data: $d) { "
        "result { code } errors { field messages } } }",
        variables={"d": {"code": "RejShelf", "branchId": branch.pk}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfRejectingViaSerializer"]
    assert result["result"] is None
    assert result["errors"] == [
        {"field": "__all__", "messages": ["Shelf rejected by a whole-object business rule."]},
    ]
    assert not models.Shelf.objects.filter(code="RejShelf").exists()


@pytest.mark.django_db
def test_serializer_hook_same_serializer_different_targets_distinct_inputs_and_decode_over_http():
    """Two mutations over ONE serializer whose hooks point a shared ``target`` at different models bind to DISTINCT inputs AND decode ``targetId`` against their OWN model over HTTP (spec-039 High).

    The same-serializer hook-shape collision, reproduced in the REAL project schema:
    ``createShelfViaHookTargetingPatron`` and ``createShelfViaHookTargetingLoan`` share
    ``TargetedShelfSerializer`` and return the SAME hook field names (``code`` / ``branch`` /
    ``target``) with ``target`` pointed at different models. That the autouse reload imports
    the composed schema AT ALL proves the materialize ledger no longer collides on one
    canonical name (pre-fix this raised "... is materialized by two distinct SerializerMutation
    input classes"). Introspection proves the two generated input types are DISTINCT (folding
    ``target``'s ``related_model``) yet both expose the divergent ``targetId`` beside ``code`` +
    ``branchId``.

    ``target`` is a REAL runtime field, so this also pins the DIFFERENTIATING relation decode
    (not just the name): a ``Patron``-only pk POSTed as ``targetId`` SUCCEEDS for the Patron
    mutation (decoded against ``Patron``, re-validated by the runtime serializer, then popped
    before the write) but is a ``targetId`` relation error for the Loan mutation (decoded
    against ``Loan``, where that pk does not exist) - proving each half decodes against its OWN
    bind-stashed ``related_model``, with ``result: null`` and no row for the wrong-model post.
    """
    branch = models.Branch.objects.create(name="CollisionBranch", city="Boston")
    patron = models.Patron.objects.create(name="CollisionPatron")
    # A pk that exists in Patron but NOT in Loan (no Loan rows are created), so the same
    # ``targetId`` resolves for the Patron half and fails for the Loan half.
    target_pk = patron.pk

    patron_target_input = _mutation_data_input_type_name("createShelfViaHookTargetingPatron")
    loan_target_input = _mutation_data_input_type_name("createShelfViaHookTargetingLoan")
    # Distinct descriptor-derived names (no canonical-name collision at materialize) ...
    assert patron_target_input != loan_target_input
    # ... yet both carry the same divergent ``targetId`` field beside code + branchId.
    assert _input_field_names(patron_target_input) == {"code", "branchId", "targetId"}
    assert _input_field_names(loan_target_input) == {"code", "branchId", "targetId"}

    # The Patron half decodes targetId against Patron: the Patron pk resolves, the runtime
    # serializer re-validates + pops it, and the Shelf writes through code + branch.
    patron_response = _post_graphql(
        "mutation { createShelfViaHookTargetingPatron(data: { "
        f'code: "CollisionViaPatron", branchId: {branch.pk}, targetId: {target_pk} '
        "}) { result { code } errors { field messages } } }",
    )
    assert patron_response.status_code == 200
    patron_payload = patron_response.json()
    assert "errors" not in patron_payload, patron_payload
    patron_result = patron_payload["data"]["createShelfViaHookTargetingPatron"]
    assert patron_result["errors"] == []
    assert patron_result["result"] == {"code": "CollisionViaPatron"}
    assert models.Shelf.objects.filter(code="CollisionViaPatron", branch=branch).exists()

    # The Loan half decodes the SAME targetId against Loan, where that pk does not exist:
    # a targetId-keyed relation error, result null, no row (the wrong-model assertion).
    loan_response = _post_graphql(
        "mutation { createShelfViaHookTargetingLoan(data: { "
        f'code: "CollisionViaLoanWrongTarget", branchId: {branch.pk}, targetId: {target_pk} '
        "}) { result { code } errors { field messages } } }",
    )
    assert loan_response.status_code == 200
    loan_payload = loan_response.json()
    assert "errors" not in loan_payload, loan_payload
    loan_result = loan_payload["data"]["createShelfViaHookTargetingLoan"]
    assert loan_result["result"] is None
    assert [e["field"] for e in loan_result["errors"]] == ["targetId"]
    assert not models.Shelf.objects.filter(code="CollisionViaLoanWrongTarget").exists()


@pytest.mark.django_db
def test_create_shelf_via_hook_narrowed_serializer_recovers_unsupported_default_field():
    """A serializer whose DEFAULT field set has an unsupported field still builds + writes via a narrowing hook (spec-039 High).

    ``HookNarrowedShelfSerializer`` declares an unsupported ``SlugRelatedField(many=True)``
    ``alt_branches``: default no-arg discovery succeeds but its field WALK raises converting
    it, so the canonical name is not reserved and the supported hook map is NOT rejected
    (``inputs.py::_default_full_shape_identity`` swallows the walk error). The hook narrows
    the schema-time map to the supported subset, so the live write proves the hook map drives
    BOTH the schema and the runtime decode: the input exposes the supported ``code`` +
    ``branchId`` (NOT the unsupported ``altBranches`` slug list), and a ``branchId`` create
    writes the row.
    """
    branch = models.Branch.objects.create(name="NarrowBranch", city="Boston")
    response = _post_graphql(
        "mutation { createShelfViaHookNarrowedSerializer(data: { "
        f'code: "NarrowShelf", branchId: {branch.pk} '
        "}) { result { code } errors { field messages } } }",
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaHookNarrowedSerializer"]
    assert result["errors"] == []
    assert result["result"] == {"code": "NarrowShelf"}
    assert models.Shelf.objects.filter(code="NarrowShelf", branch=branch).exists()

    # The hook narrowed the schema to the supported subset: the input is exactly
    # code + branchId (the unsupported alt_branches slug list is dropped, not exposed).
    input_type_name = _mutation_data_input_type_name("createShelfViaHookNarrowedSerializer")
    assert _input_field_names(input_type_name) == {"code", "branchId"}


@pytest.mark.django_db
def test_create_shelf_via_serializer_hidden_branch_is_relation_field_error():
    """A raw-pk ``branchId`` whose Branch is hidden by ``BranchType.get_queryset`` -> field error, no write (serializer path).

    The serializer relation decode (``resolvers.py::_decode_relation_single``) resolves the
    raw pk through the non-Relay ``BranchType`` primary's visibility hook, just like the form
    / model paths: an anonymous caller (the mutation uses ``permission_classes = []``) cannot
    attach a ``city="restricted"`` Branch, so the hidden pk is a ``branchId``-keyed
    ``FieldError`` with ``result: null`` and no ``Shelf`` row. ``ShelfSerializerInput`` is the
    canonical (default full shape) input name, so it is referenced by a typed variable.
    """
    restricted = models.Branch.objects.create(name="SerRestrictedFK", city="restricted")
    response = _post_graphql(
        "mutation($d: ShelfSerializerInput!) { createShelfViaSerializer(data: $d) { "
        "result { code } errors { field messages } } }",
        variables={"d": {"code": "HiddenSerShelf", "branchId": restricted.pk}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaSerializer"]
    assert result["result"] is None
    assert [e["field"] for e in result["errors"]] == ["branchId"]
    assert not models.Shelf.objects.filter(code="HiddenSerShelf").exists()


@pytest.mark.django_db
def test_create_shelf_via_schema_hook_serializer_hidden_branch_is_relation_field_error():
    """The schema-hook serializer mutation also rejects a hidden raw-pk ``branchId`` (hook-generated input + serializer relation visibility in one request, spec-039).

    Covers the README's preference to pin serializer relation visibility through the
    hook-generated input too: ``createShelfViaSchemaHookSerializer`` builds its input from
    ``get_serializer_for_schema()`` and decodes ``branchId`` through the same visibility-scoped
    ``BranchType.get_queryset``. Posted ANONYMOUSLY (so the ``city="restricted"`` Branch is
    hidden), the relation decode fails BEFORE the serializer is even constructed (decode runs
    before construct in the pipeline), so the tenant injection never matters: ``result: null``,
    a ``branchId``-keyed ``FieldError``, and no ``Shelf`` row.
    """
    restricted = models.Branch.objects.create(name="HookRestrictedFK", city="restricted")
    response = _post_graphql(
        "mutation { createShelfViaSchemaHookSerializer(data: { "
        f'code: "HiddenHookShelf", branchId: {restricted.pk} '
        "}) { result { code } errors { field messages } } }",
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaSchemaHookSerializer"]
    assert result["result"] is None
    assert [e["field"] for e in result["errors"]] == ["branchId"]
    assert not models.Shelf.objects.filter(code="HiddenHookShelf").exists()


@pytest.mark.django_db
def test_create_shelf_via_blank_code_serializer_accepts_empty_string_over_http():
    """An ``allow_blank=True`` required ``code`` is a non-null ``String!`` in the SDL but accepts ``""`` at runtime (spec-039 M2 - allow_blank pinned).

    ``allow_blank`` is NOT a GraphQL concern (M2): the generated input's ``code`` is still a
    non-null ``String`` (a required ``CharField`` - allow_blank is absent from the SDL), and
    the empty-string acceptance is enforced by the serializer at runtime. Introspection pins
    the non-null shape; posting ``code: ""`` then proves the serializer accepts + writes the
    blank (a plain required ``CharField`` would reject it with a field error).
    """
    branch = models.Branch.objects.create(name="BlankBranch", city="Boston")

    # allow_blank is invisible in the SDL: the required code input is a non-null String!.
    code_type = _input_field_type("BlankCodeShelfSerializerInput", "code")
    assert code_type["kind"] == "NON_NULL"
    assert code_type["ofType"]["name"] == "String"

    response = _post_graphql(
        "mutation($d: BlankCodeShelfSerializerInput!) { createShelfViaBlankCodeSerializer(data: $d) { "
        "result { code } errors { field messages } } }",
        variables={"d": {"code": "", "branchId": branch.pk}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaBlankCodeSerializer"]
    # The serializer accepted the blank (a plain required CharField would have rejected it).
    assert result["errors"] == []
    assert result["result"] == {"code": ""}
    assert models.Shelf.objects.filter(code="", branch=branch).exists()


@pytest.mark.django_db
def test_serializer_optional_fields_over_http_uses_distinct_input_and_in_band_required_error():
    """Mutation ``Meta.optional_fields`` weakens GraphQL requiredness without hiding DRF validation.

    Two mutations share one serializer and the same field set. The strict mutation uses the
    serializer's natural required ``code``; the optional mutation sets mutation-level
    ``Meta.optional_fields = ("code",)``. They must not share a stale generated input, and the
    optional shape must accept omission at GraphQL coercion while DRF still returns its
    field-keyed required error in the payload.
    """
    branch = models.Branch.objects.create(name="OptionalCodeBranch", city="Boston")

    strict_input = _mutation_data_input_type_name("createShelfViaOptionalCodeStrictSerializer")
    optional_input = _mutation_data_input_type_name("createShelfViaOptionalCodeSerializer")
    assert strict_input != optional_input

    strict_code = _input_field_type(strict_input, "code")
    assert strict_code["kind"] == "NON_NULL"
    assert strict_code["ofType"]["name"] == "String"
    optional_code = _input_field_type(optional_input, "code")
    assert optional_code["kind"] == "SCALAR"
    assert optional_code["name"] == "String"
    optional_branch = _input_field_type(optional_input, "branchId")
    assert optional_branch["kind"] == "NON_NULL"
    assert optional_branch["ofType"]["name"] == "Int"

    omitted_response = _post_graphql(
        f"mutation($d: {optional_input}!) {{ createShelfViaOptionalCodeSerializer(data: $d) {{ "
        "result { code } errors { field messages } } }",
        variables={"d": {"branchId": branch.pk}},
    )
    assert omitted_response.status_code == 200
    omitted_payload = omitted_response.json()
    assert "errors" not in omitted_payload, omitted_payload
    omitted_result = omitted_payload["data"]["createShelfViaOptionalCodeSerializer"]
    assert omitted_result["result"] is None
    assert [error["field"] for error in omitted_result["errors"]] == ["code"]
    assert not models.Shelf.objects.filter(branch=branch, code="").exists()

    success_response = _post_graphql(
        f"mutation($d: {optional_input}!) {{ createShelfViaOptionalCodeSerializer(data: $d) {{ "
        "result { code } errors { field messages } } }",
        variables={"d": {"code": "OptionalCodeShelf", "branchId": branch.pk}},
    )
    assert success_response.status_code == 200
    success_payload = success_response.json()
    assert "errors" not in success_payload, success_payload
    success_result = success_payload["data"]["createShelfViaOptionalCodeSerializer"]
    assert success_result["errors"] == []
    assert success_result["result"] == {"code": "OptionalCodeShelf"}
    assert models.Shelf.objects.filter(code="OptionalCodeShelf", branch=branch).exists()


@pytest.mark.django_db
def test_serializer_hooks_differing_only_in_allow_null_bind_distinct_nullability_over_http():
    """Two mutations over ONE serializer whose hooks differ ONLY in a field's ``allow_null`` bind to DISTINCT inputs with the CORRECT per-field nullability (spec-039 High / M2).

    ``createShelfViaHookNonNullNote`` and ``createShelfViaHookNullableNote`` share
    ``NoteShelfSerializer`` and return the SAME ``code`` + ``branch`` + ``note`` hook fields,
    with ``note`` a ``required=True`` ``CharField`` differing ONLY in ``allow_null``; each also
    constructs the SAME serializer at runtime with the matching ``note_allow_null`` (rev6 #1 -
    the agreement guard forbids a schema-only field the runtime does not declare). The EMITTED
    nullability is part of the descriptor identity, so the two generated inputs are DISTINCT
    types: the ``allow_null=False`` half exposes ``note`` as a non-null ``String!``, the
    ``allow_null=True`` half as a nullable, OMITTABLE ``String``. Before the fix the descriptor
    recorded the base annotation (NOT the post-widening one), so the two shapes compared EQUAL
    and the second declaration silently reused the first's cached input class - giving one
    mutation the other's nullability (the SAME input type name, same SDL nullability for both).

    Both also execute over HTTP: the non-null half must supply ``note`` (a non-null
    ``String!``); the nullable half sends an explicit ``null`` (its ``allow_null=True`` note
    accepts it). ``note`` is decoded + validated then dropped by ``NoteShelfSerializer.create``.
    """
    branch = models.Branch.objects.create(name="NullabilityBranch", city="Boston")

    non_null_input = _mutation_data_input_type_name("createShelfViaHookNonNullNote")
    nullable_input = _mutation_data_input_type_name("createShelfViaHookNullableNote")
    # Distinct descriptor-derived names: the emitted-annotation nullability is part of the
    # identity, so the second declaration does NOT silently reuse the first's input class.
    assert non_null_input != nullable_input

    # The allow_null=False half emits a non-null String! note; the allow_null=True half a
    # nullable String (M2 - required-AND-nullable is omittable, DRF enforces presence in-band).
    non_null_note = _input_field_type(non_null_input, "note")
    assert non_null_note["kind"] == "NON_NULL"
    assert non_null_note["ofType"]["name"] == "String"
    nullable_note = _input_field_type(nullable_input, "note")
    assert nullable_note["kind"] == "SCALAR"
    assert nullable_note["name"] == "String"

    # The non-null half requires note (String!); it is decoded + validated then dropped by the
    # runtime NoteShelfSerializer.create, and the Shelf writes.
    non_null_response = _post_graphql(
        "mutation { createShelfViaHookNonNullNote(data: { "
        f'code: "NonNullNoteShelf", branchId: {branch.pk}, note: "provided" '
        "}) { result { code } errors { field messages } } }",
    )
    assert non_null_response.status_code == 200
    non_null_payload = non_null_response.json()
    assert "errors" not in non_null_payload, non_null_payload
    non_null_result = non_null_payload["data"]["createShelfViaHookNonNullNote"]
    assert non_null_result["errors"] == []
    assert non_null_result["result"] == {"code": "NonNullNoteShelf"}
    assert models.Shelf.objects.filter(code="NonNullNoteShelf", branch=branch).exists()

    # The nullable half sends an EXPLICIT null (its allow_null=True note accepts it); the note
    # is decoded then dropped and the Shelf still writes.
    nullable_response = _post_graphql(
        "mutation { createShelfViaHookNullableNote(data: { "
        f'code: "NullableNoteShelf", branchId: {branch.pk}, note: null '
        "}) { result { code } errors { field messages } } }",
    )
    assert nullable_response.status_code == 200
    nullable_payload = nullable_response.json()
    assert "errors" not in nullable_payload, nullable_payload
    nullable_result = nullable_payload["data"]["createShelfViaHookNullableNote"]
    assert nullable_result["errors"] == []
    assert nullable_result["result"] == {"code": "NullableNoteShelf"}
    assert models.Shelf.objects.filter(code="NullableNoteShelf", branch=branch).exists()

    # The nullable half is also GraphQL-omittable; omission reaches DRF as a missing key, so
    # the required-field error stays in-band rather than becoming a top-level GraphQL error.
    omitted_response = _post_graphql(
        "mutation { createShelfViaHookNullableNote(data: { "
        f'code: "OmittedNullableNoteShelf", branchId: {branch.pk} '
        "}) { result { code } errors { field messages } } }",
    )
    assert omitted_response.status_code == 200
    omitted_payload = omitted_response.json()
    assert "errors" not in omitted_payload, omitted_payload
    omitted_result = omitted_payload["data"]["createShelfViaHookNullableNote"]
    assert omitted_result["result"] is None
    assert [error["field"] for error in omitted_result["errors"]] == ["note"]
    assert not models.Shelf.objects.filter(code="OmittedNullableNoteShelf", branch=branch).exists()


@pytest.mark.django_db
def test_create_shelf_via_metadata_serializer_expanded_input_type_system_over_http():
    """The rev6 type-system matrix over ``/graphql/``: a serializer-only enum, a DictField JSON, and a registry-mapped custom field (spec-039 rev6 #6 / #7 / #11).

    ``ShelfMetadataSerializer`` carries three serializer-only write-only fields:
    ``priority`` (a ``ChoiceField`` -> a GENERATED GraphQL enum, #6), ``attributes`` (a
    ``DictField`` -> ``JSON``, #7), and ``accent_color`` (a custom ``HexColorField`` mapped
    ONLY via ``register_serializer_field_converter`` -> ``String``, #11). Introspection pins
    each input field's GraphQL type; the create then posts through all three, proving the
    expanded input type system works end to end (the enum value round-trips into ``topic``,
    the JSON + custom field are decoded + validated then dropped).
    """
    branch = models.Branch.objects.create(name="MetadataBranch", city="Boston")

    # #6: the serializer-only ChoiceField became a GENERATED enum (not a String).
    priority_type = _input_field_type("ShelfMetadataSerializerInput", "priority")
    assert priority_type["kind"] == "ENUM"
    assert priority_type["name"] == "ShelfMetadataSerializerInputPriorityEnum"
    # #7: the DictField became strawberry JSON.
    attributes_type = _input_field_type("ShelfMetadataSerializerInput", "attributes")
    assert attributes_type["kind"] == "SCALAR"
    assert attributes_type["name"] == "JSON"
    # #11: the custom HexColorField mapped to String via the registered converter.
    accent_type = _input_field_type("ShelfMetadataSerializerInput", "accentColor")
    assert accent_type["kind"] == "SCALAR"
    assert accent_type["name"] == "String"

    # The generated enum exposes the choice VALUES as its member names (sanitized).
    enum_values = _post_graphql(
        """
        query {
          __type(name: "ShelfMetadataSerializerInputPriorityEnum") { enumValues { name } }
        }
        """,
    ).json()["data"]["__type"]["enumValues"]
    assert {v["name"] for v in enum_values} == {"low", "normal", "high"}

    # Post through all three (the enum via a variable string, the JSON via an object).
    response = _post_graphql(
        "mutation($d: ShelfMetadataSerializerInput!) { createShelfViaMetadataSerializer(data: $d) { "
        "result { code topic } errors { field messages } } }",
        variables={
            "d": {
                "code": "MetaShelf",
                "branchId": branch.pk,
                "priority": "high",
                "attributes": {"note": "x"},
                "accentColor": "#3366ff",
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaMetadataSerializer"]
    assert result["errors"] == []
    # The enum value round-tripped into ``topic``; the JSON + custom field were dropped.
    assert result["result"] == {"code": "MetaShelf", "topic": "priority:high"}
    assert models.Shelf.objects.filter(
        code="MetaShelf",
        topic="priority:high",
        branch=branch,
    ).exists()


def _input_field_description(type_name: str, field_name: str) -> str | None:
    """Return an input object field's GraphQL description via introspection (spec-039 rev6 #9)."""
    response = _post_graphql(
        f"""
        query {{
          __type(name: "{type_name}") {{ inputFields {{ name description }} }}
        }}
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    fields = payload["data"]["__type"]["inputFields"]
    return next(f["description"] for f in fields if f["name"] == field_name)


@pytest.mark.django_db
def test_serializer_input_field_description_threads_drf_metadata_over_http():
    """A DRF field's ``help_text`` + validation constraints surface as the input field's SDL description (spec-039 rev6 #9).

    ``ShelfMetadataSerializer.label`` is a ``CharField(help_text=..., max_length=40)``; the
    generated ``ShelfMetadataSerializerInput.label`` carries a description combining the help
    text and a constraint summary (``max_length=40``). This is documentation / introspection
    only - DRF still owns runtime validation - so the field's TYPE stays a plain ``String``.
    """
    description = _input_field_description("ShelfMetadataSerializerInput", "label")
    assert description is not None
    assert "A short human label for the shelf." in description
    assert "max_length=40" in description
    # The metadata is documentation only: the field type is unchanged (a nullable String).
    label_type = _input_field_type("ShelfMetadataSerializerInput", "label")
    assert label_type["kind"] == "SCALAR"
    assert label_type["name"] == "String"


@pytest.mark.django_db
def test_serializer_error_envelope_carries_codes_and_path_over_http():
    """The mutation error envelope carries structured ``codes`` + ``path`` alongside ``field`` / ``messages`` (spec-039 rev6 #4 / #13).

    A DRF field validation error preserves the DRF ``ErrorDetail.code`` (``label`` exceeds its
    ``max_length=40`` -> code ``max_length``) and a structured ``path`` (``["label"]``); a
    framework relation-decode error (a nonexistent ``branchId``) carries the framework code
    ``invalid`` + the wire-name path. Both keep the legacy ``field`` / ``messages`` intact.
    """
    branch = models.Branch.objects.create(name="CodesBranch", city="Boston")

    # A DRF field error: label is a CharField(max_length=40); posting 50 chars fails is_valid.
    response = _post_graphql(
        "mutation($d: ShelfMetadataSerializerInput!) { createShelfViaMetadataSerializer(data: $d) { "
        "result { code } errors { field messages codes path } } }",
        variables={"d": {"code": "CodesShelf", "branchId": branch.pk, "label": "x" * 50}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfViaMetadataSerializer"]
    assert result["result"] is None
    (err,) = result["errors"]
    assert err["field"] == "label"
    assert err["path"] == ["label"]
    assert "max_length" in err["codes"]  # the DRF ErrorDetail.code is preserved (#4).
    assert not models.Shelf.objects.filter(code="CodesShelf").exists()

    # A framework relation-decode error: a nonexistent branch pk -> code "invalid", path=["branchId"].
    bad = _post_graphql(
        "mutation($d: ShelfMetadataSerializerInput!) { createShelfViaMetadataSerializer(data: $d) { "
        "result { code } errors { field messages codes path } } }",
        variables={"d": {"code": "CodesShelf2", "branchId": 999999}},
    )
    bad_result = bad.json()["data"]["createShelfViaMetadataSerializer"]
    assert bad_result["result"] is None
    (rel_err,) = bad_result["errors"]
    assert rel_err["field"] == "branchId"
    assert rel_err["codes"] == ["invalid"]
    assert rel_err["path"] == ["branchId"]


@pytest.mark.django_db
def test_serializer_injected_field_contract_over_http():
    """A required field narrowed away + declared in ``Meta.injected_fields`` is supplied by the override (spec-039 rev6 #2).

    ``CreateShelfWithInjectedTopic`` narrows the input to ``code`` + ``branchId`` (dropping the
    ``OwnerStampShelfSerializer``-required ``topic``) and declares ``Meta.injected_fields =
    ("topic",)`` with a ``get_serializer_kwargs`` override that supplies ``topic`` into the
    serializer data. The create-required guard SUBTRACTS the declared injected field (so the
    narrowing binds), and the write succeeds with the injected ``topic`` - the auditable,
    per-field replacement for the old blanket waiver.
    """
    branch = models.Branch.objects.create(name="InjectBranch", city="Boston")

    # ``topic`` is narrowed away from the input (only code + branchId remain).
    input_name = _mutation_data_input_type_name("createShelfWithInjectedTopic")
    assert _input_field_names(input_name) == {"code", "branchId"}

    response = _post_graphql(
        "mutation($d: " + input_name + "!) { createShelfWithInjectedTopic(data: $d) { "
        "result { code topic } errors { field messages } } }",
        variables={"d": {"code": "InjectShelf", "branchId": branch.pk}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfWithInjectedTopic"]
    assert result["errors"] == []
    # The override supplied the narrowed-away required ``topic``; the write succeeded with it.
    assert result["result"] == {"code": "InjectShelf", "topic": "stamped-by-injection"}
    assert models.Shelf.objects.filter(
        code="InjectShelf",
        topic="stamped-by-injection",
        branch=branch,
    ).exists()


@pytest.mark.django_db
def test_serializer_m2m_relation_visibility_over_http():
    """A raw-pk M2M serializer input writes visible branches and rejects a hidden one (spec-039 rev6 #3).

    ``createShelfViaAltBranchesSerializer`` exposes ``alt_branches`` (a raw-pk M2M over the
    non-Relay ``BranchType``). The decode confirms the whole list's visibility in one batched
    query through ``BranchType.get_queryset`` (which hides ``city="restricted"`` from the
    anonymous caller); DRF re-validates against the same visibility-scoped queryset. Two visible
    branches write; a hidden branch is a ``altBranches`` relation error with no row written.
    """
    branch = models.Branch.objects.create(name="M2MHome", city="Boston")
    alt1 = models.Branch.objects.create(name="M2MAlt1", city="Boston")
    alt2 = models.Branch.objects.create(name="M2MAlt2", city="Boston")
    hidden = models.Branch.objects.create(name="M2MHidden", city="restricted")

    # Visible alt branches: the M2M writes.
    ok = _post_graphql(
        "mutation($d: AltBranchesShelfSerializerInput!) { createShelfViaAltBranchesSerializer(data: $d) { "
        "result { code } errors { field messages } } }",
        variables={
            "d": {"code": "M2MShelf", "branchId": branch.pk, "altBranches": [alt1.pk, alt2.pk]},
        },
    )
    assert ok.status_code == 200
    ok_payload = ok.json()
    assert "errors" not in ok_payload, ok_payload
    ok_result = ok_payload["data"]["createShelfViaAltBranchesSerializer"]
    assert ok_result["errors"] == []
    shelf = models.Shelf.objects.get(code="M2MShelf", branch=branch)
    assert set(shelf.alt_branches.values_list("pk", flat=True)) == {alt1.pk, alt2.pk}

    # A hidden branch in the list is a field-keyed relation error; no row written.
    bad = _post_graphql(
        "mutation($d: AltBranchesShelfSerializerInput!) { createShelfViaAltBranchesSerializer(data: $d) { "
        "result { code } errors { field messages codes } } }",
        variables={
            "d": {
                "code": "M2MBadShelf",
                "branchId": branch.pk,
                "altBranches": [alt1.pk, hidden.pk],
            },
        },
    )
    bad_result = bad.json()["data"]["createShelfViaAltBranchesSerializer"]
    assert bad_result["result"] is None
    (err,) = bad_result["errors"]
    assert err["field"] == "altBranches"
    assert err["codes"] == ["invalid"]
    assert not models.Shelf.objects.filter(code="M2MBadShelf").exists()


@pytest.mark.django_db
def test_serializer_save_kwargs_hook_injects_server_side_data_over_http():
    """``get_serializer_save_kwargs`` injects NON-model server-side data at ``serializer.save()``.

    ``CreateShelfWithSaveKwargs`` accepts ``code`` + ``branchId`` and stamps a server-side
    ``stamp`` at SAVE time (not a client input, not a model field); the serializer's own
    ``create()`` consumes it into ``topic``. The write succeeds and the ``Shelf`` carries the
    save-time-stamped ``topic``, proving the DRF-native ``serializer.save(stamp=...)`` seam
    runs inside the framework's value-preserving save closure.
    """
    branch = models.Branch.objects.create(name="SaveKwargsBranch", city="Boston")
    response = _post_graphql(
        "mutation($d: SaveKwargsShelfSerializerInput!) { createShelfWithSaveKwargs(data: $d) { "
        "result { code topic } errors { field messages } } }",
        variables={"d": {"code": "SaveKwargsShelf", "branchId": branch.pk}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createShelfWithSaveKwargs"]
    assert result["errors"] == []
    assert result["result"] == {"code": "SaveKwargsShelf", "topic": "stamped-at-save"}
    assert models.Shelf.objects.filter(
        code="SaveKwargsShelf",
        topic="stamped-at-save",
        branch=branch,
    ).exists()


@pytest.mark.django_db
def test_serializer_save_kwargs_naming_a_model_field_is_rejected_over_http():
    """A save kwarg naming a MODEL field is a top-level ``ConfigurationError``, no row written.

    ``CreateShelfWithModelFieldSaveKwargs`` returns ``{"topic": ...}`` - a ``Shelf`` column -
    from ``get_serializer_save_kwargs``; the unaudited model-field injection channel is
    rejected before ``serializer.save()`` and nothing persists.
    """
    branch = models.Branch.objects.create(name="ModelFieldSaveKwargsBranch", city="Boston")
    response = _post_graphql(
        "mutation($d: ShelfSerializerInput!) { createShelfWithModelFieldSaveKwargs(data: $d) { "
        "result { code } errors { field messages } } }",
        variables={"d": {"code": "ModelFieldSaveKwargsShelf", "branchId": branch.pk}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] is None
    assert "model field" in payload["errors"][0]["message"]
    assert not models.Shelf.objects.filter(code="ModelFieldSaveKwargsShelf").exists()


@pytest.mark.django_db
def test_serializer_save_kwargs_rejects_renamed_source_shadow_over_http():
    """A save kwarg cannot silently replace a renamed input's value (spec-039 rev6 #12).

    ``shelfCode`` is declared as ``shelf_code`` but validates into DRF's ``code`` key through
    ``source="code"``. The colliding server-side ``code`` kwarg is rejected before save, and
    neither the client nor server value reaches the database.
    """
    branch = models.Branch.objects.create(name="SaveKwargsAliasBranch", city="Boston")
    response = _post_graphql(
        "mutation($d: RenamedShelfSerializerInput!) { "
        "createShelfWithRenamedSaveKwargsCollision(data: $d) { "
        "result { code } errors { field messages } } }",
        variables={"d": {"shelfCode": "client-value", "branchId": branch.pk}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] is None
    assert payload["errors"][0]["path"] == ["createShelfWithRenamedSaveKwargsCollision"]
    # The hardened check compares against the ACTUAL validated_data keys (the resolved
    # `source="code"` key), not a reconstruction from the input specs.
    assert "['code']" in payload["errors"][0]["message"]
    assert "validated_data" in payload["errors"][0]["message"]
    assert not models.Shelf.objects.filter(
        code__in=("client-value", "server-shadow"),
        branch=branch,
    ).exists()


@pytest.mark.django_db
def test_serializer_update_with_select_for_update_over_http():
    """An update serializer mutation with ``Meta.select_for_update = True`` updates cleanly over HTTP (spec-039 rev6 #14).

    ``UpdateBookViaSerializerWithLock`` locks the located ``Book`` row inside the pipeline
    transaction (after visibility filtering). On sqlite Django silently skips the ``FOR UPDATE``
    clause, so this proves the update + row-lock path integrates; on a supporting backend the
    row is genuinely locked. ``BookType`` is Relay-Node, so the update ``id`` is a ``GlobalID``
    and the payload slot is ``node``.
    """
    from apps.library.schema import BookType

    shelf = _seed_shelf()
    book = models.Book.objects.create(title="BeforeLock", shelf=shelf)

    response = _post_graphql(
        "mutation($id: ID!, $d: BookSerializerPartialInput!) { "
        "updateBookViaSerializerWithLock(id: $id, data: $d) { "
        "node { title } errors { field messages } } }",
        variables={"id": global_id_for(BookType, book.pk), "d": {"title": "AfterLock"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateBookViaSerializerWithLock"]
    assert result["errors"] == []
    assert result["node"]["title"] == "AfterLock"
    book.refresh_from_db()
    assert book.title == "AfterLock"


@pytest.mark.django_db
def test_serializer_update_provided_genres_list_replaces_complete_set_over_http():
    """A PROVIDED list relation on a serializer update replaces the complete stored set.

    ``UpdateBookGenresViaSerializer`` exposes the ``genres`` M2M; DRF's own ``update``
    ``set()``s the provided list inside the pipeline transaction, so the stored set after the
    write is EXACTLY the provided membership - prior members not in the list are detached.
    """
    from apps.library.schema import BookType, GenreType

    shelf = _seed_shelf()
    old_genre = models.Genre.objects.create(name="ReplaceOld")
    new_genre = models.Genre.objects.create(name="ReplaceNew")
    book = models.Book.objects.create(title="GenreSwap", shelf=shelf)
    book.genres.set([old_genre])

    response = _post_graphql(
        "mutation($id: ID!, $d: BookGenresSerializerPartialInput!) { "
        "updateBookGenresViaSerializer(id: $id, data: $d) { "
        "node { title } errors { field messages } } }",
        variables={
            "id": global_id_for(BookType, book.pk),
            "d": {"genres": [global_id_for(GenreType, new_genre.pk)]},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"]["updateBookGenresViaSerializer"]["errors"] == []
    assert list(book.genres.values_list("name", flat=True)) == ["ReplaceNew"]


@pytest.mark.django_db
def test_serializer_update_omitted_genres_leaves_relation_unchanged_over_http():
    """An OMITTED list relation on a serializer update leaves the stored set untouched (hardening).

    The partial-update contract: updating only ``title`` (no ``genres`` key in the input)
    must not clear or rewrite the M2M - ``partial=True`` means unsent fields keep their
    stored values.
    """
    from apps.library.schema import BookType

    shelf = _seed_shelf()
    kept = models.Genre.objects.create(name="KeptGenre")
    book = models.Book.objects.create(title="KeepGenres", shelf=shelf)
    book.genres.set([kept])

    response = _post_graphql(
        "mutation($id: ID!, $d: BookGenresSerializerPartialInput!) { "
        "updateBookGenresViaSerializer(id: $id, data: $d) { "
        "node { title } errors { field messages } } }",
        variables={"id": global_id_for(BookType, book.pk), "d": {"title": "TitleOnly"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"]["updateBookGenresViaSerializer"]["node"]["title"] == "TitleOnly"
    # The omitted M2M is unchanged.
    assert list(book.genres.values_list("name", flat=True)) == ["KeptGenre"]


@pytest.mark.django_db
def test_serializer_update_genres_empty_and_duplicates_have_set_semantics_over_http():
    """Duplicate members normalize to one relation and an explicit empty list clears it."""
    from apps.library.schema import BookType, GenreType

    shelf = _seed_shelf()
    genre = models.Genre.objects.create(name="SetSemanticsGenre")
    book = models.Book.objects.create(title="SetSemanticsBook", shelf=shelf)
    mutation = (
        "mutation($id: ID!, $d: BookGenresSerializerPartialInput!) { "
        "updateBookGenresViaSerializer(id: $id, data: $d) { "
        "node { title } errors { field messages } } }"
    )
    book_id = global_id_for(BookType, book.pk)
    genre_id = global_id_for(GenreType, genre.pk)

    duplicate_response = _post_graphql(
        mutation,
        variables={"id": book_id, "d": {"genres": [genre_id, genre_id]}},
    )
    duplicate_payload = duplicate_response.json()
    assert "errors" not in duplicate_payload, duplicate_payload
    assert duplicate_payload["data"]["updateBookGenresViaSerializer"]["errors"] == []
    assert list(book.genres.values_list("pk", flat=True)) == [genre.pk]

    clear_response = _post_graphql(
        mutation,
        variables={"id": book_id, "d": {"genres": []}},
    )
    clear_payload = clear_response.json()
    assert "errors" not in clear_payload, clear_payload
    assert clear_payload["data"]["updateBookGenresViaSerializer"]["errors"] == []
    assert not book.genres.exists()


@pytest.mark.django_db
def test_serializer_update_invalid_or_hidden_genre_preserves_prior_set_over_http(monkeypatch):
    """Invalid and visibility-hidden members fail before M2M mutation, preserving the prior set."""
    from apps.library.schema import BookType, GenreType

    shelf = _seed_shelf()
    kept = models.Genre.objects.create(name="FailureKeptGenre")
    hidden = models.Genre.objects.create(name="FailureHiddenGenre")
    book = models.Book.objects.create(title="FailurePreservesGenres", shelf=shelf)
    book.genres.set([kept])
    mutation = (
        "mutation($id: ID!, $d: BookGenresSerializerPartialInput!) { "
        "updateBookGenresViaSerializer(id: $id, data: $d) { "
        "node { title } errors { field messages codes } } }"
    )
    book_id = global_id_for(BookType, book.pk)

    invalid_response = _post_graphql(
        mutation,
        variables={
            "id": book_id,
            "d": {"genres": [global_id_for(GenreType, hidden.pk + 100_000)]},
        },
    )
    invalid_result = invalid_response.json()["data"]["updateBookGenresViaSerializer"]
    assert invalid_result["node"] is None
    assert invalid_result["errors"][0]["field"] == "genres"
    assert list(book.genres.values_list("pk", flat=True)) == [kept.pk]

    def _hide_genre(cls, queryset, info):
        del cls, info
        return queryset.exclude(pk=hidden.pk)

    monkeypatch.setattr(GenreType, "get_queryset", classmethod(_hide_genre))
    hidden_response = _post_graphql(
        mutation,
        variables={"id": book_id, "d": {"genres": [global_id_for(GenreType, hidden.pk)]}},
    )
    hidden_result = hidden_response.json()["data"]["updateBookGenresViaSerializer"]
    assert hidden_result["node"] is None
    assert hidden_result["errors"][0]["field"] == "genres"
    assert list(book.genres.values_list("pk", flat=True)) == [kept.pk]


@pytest.mark.django_db
def test_serializer_update_substituted_instance_is_rejected_without_writes_over_http():
    """A hook substituting the located instance is a top-level error and NEITHER row is written (hardening).

    ``UpdateBookSubstitutingInstance.get_serializer_kwargs`` returns a DIFFERENT ``Book``
    than the located, authorized row - the "row A's authorization writes row B" bypass.
    ``instance`` is framework-owned, so the substitution is a ``ConfigurationError`` over
    ``/graphql/`` and no write reaches either row.
    """
    from apps.library.schema import BookType

    shelf = _seed_shelf()
    addressed = models.Book.objects.create(title="AddressedRow", shelf=shelf)
    victim = models.Book.objects.create(title="VictimRow", shelf=shelf)

    response = _post_graphql(
        "mutation($id: ID!, $d: BookSerializerPartialInput!) { "
        "updateBookSubstitutingInstance(id: $id, data: $d) { "
        "node { title } errors { field messages } } }",
        variables={"id": global_id_for(BookType, addressed.pk), "d": {"title": "Hijacked"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] is None
    assert "`instance` kwarg" in payload["errors"][0]["message"]
    addressed.refresh_from_db()
    victim.refresh_from_db()
    assert addressed.title == "AddressedRow"
    assert victim.title == "VictimRow"


@pytest.mark.django_db
def test_create_branch_with_nested_shelves_over_http():
    """An EXPLICIT opt-in nested serializer write creates a branch + nested shelves over HTTP (spec-039 rev6 #17).

    ``CreateBranchWithNestedShelves`` opts a nested ``shelves`` list in via
    ``Meta.nested_fields = {"shelves": NestedSerializerConfig()}``; the serializer's OWN
    ``create()`` performs the nested write (the framework never auto-saves the relation). The
    generated input carries a nested ``NestedShelfSerializerInput`` (``code`` / ``topic`` / a
    raw-pk ``altBranches`` list). A create writes the branch + every nested shelf, and a nested
    ``altBranches`` id is visibility-decoded through ``BranchType.get_queryset``.
    """
    home = models.Branch.objects.create(name="NestVisibleAlt", city="Boston")

    # Introspection: the top input has a nested ``shelves`` list of ``NestedShelfSerializerInput``.
    top_input = _mutation_data_input_type_name("createBranchWithNestedShelves")
    assert "shelves" in _input_field_names(top_input)
    assert _input_field_names("NestedShelfSerializerInput") == {"code", "topic", "altBranches"}

    response = _post_graphql(
        "mutation($d: " + top_input + "!) { createBranchWithNestedShelves(data: $d) { "
        "result { name shelves { code topic } } errors { field messages } } }",
        variables={
            "d": {
                "name": "NestedHome",
                "city": "Boston",
                "shelves": [
                    {"code": "N1", "topic": "fiction", "altBranches": [home.pk]},
                    {"code": "N2"},
                ],
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createBranchWithNestedShelves"]
    assert result["errors"] == []
    # ``BranchType.shelves`` orders by ``-code``, so N2 then N1.
    assert result["result"] == {
        "name": "NestedHome",
        "shelves": [{"code": "N2", "topic": ""}, {"code": "N1", "topic": "fiction"}],
    }
    branch = models.Branch.objects.get(name="NestedHome")
    n1 = models.Shelf.objects.get(branch=branch, code="N1")
    # The nested ``alt_branches`` pk was decoded, visibility-checked, and written by create().
    assert set(n1.alt_branches.values_list("pk", flat=True)) == {home.pk}


@pytest.mark.django_db
def test_nested_shelf_hidden_alt_branch_is_structured_path_error_over_http():
    """A hidden id in a NESTED relation is a structured ``shelves.<i>.altBranches`` error with no partial write (spec-039 rev6 #17 / #3 / #13).

    A nested ``shelves[0].altBranches`` pointing at a ``city="restricted"`` branch (hidden from
    the anonymous caller by ``BranchType.get_queryset``) is a relation error keyed to the FULL
    nested path - proving the recursive decode visibility-checks nested relations and keys the
    error to its structured path. The whole write rolls back (no branch, no shelves).
    """
    hidden = models.Branch.objects.create(name="NestHiddenAlt", city="restricted")
    top_input = _mutation_data_input_type_name("createBranchWithNestedShelves")

    response = _post_graphql(
        "mutation($d: " + top_input + "!) { createBranchWithNestedShelves(data: $d) { "
        "result { name } errors { field messages codes path } } }",
        variables={
            "d": {
                "name": "NestedRollback",
                "shelves": [{"code": "N1", "altBranches": [hidden.pk]}],
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createBranchWithNestedShelves"]
    assert result["result"] is None
    (err,) = result["errors"]
    assert err["field"] == "shelves.0.altBranches"
    assert err["path"] == ["shelves", "0", "altBranches"]
    assert err["codes"] == ["invalid"]
    # H6: the error envelope committed nothing.
    assert not models.Branch.objects.filter(name="NestedRollback").exists()
    assert not models.Shelf.objects.filter(code="N1", branch__name="NestedRollback").exists()


@pytest.mark.django_db
def test_nested_shelf_validation_error_flattens_to_structured_path_over_http():
    """A NESTED DRF validation error flattens to the structured ``shelves.<i>.code`` path (spec-039 rev6 #17).

    ``NestedShelfSerializer.validate_code`` rejects the sentinel ``"BANNED"`` (a valid String at
    the GraphQL boundary, so it survives coercion and reaches DRF's ``is_valid()``). The nested
    field error surfaces through the recursive flattener keyed to ``shelves.1.code`` (the second
    nested item), with the DRF ``ErrorDetail.code`` preserved; the whole write rolls back.
    """
    top_input = _mutation_data_input_type_name("createBranchWithNestedShelves")

    response = _post_graphql(
        "mutation($d: " + top_input + "!) { createBranchWithNestedShelves(data: $d) { "
        "result { name } errors { field messages path } } }",
        variables={
            "d": {"name": "NestedBadCode", "shelves": [{"code": "OK1"}, {"code": "BANNED"}]},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createBranchWithNestedShelves"]
    assert result["result"] is None
    (err,) = result["errors"]
    assert err["field"] == "shelves.1.code"
    assert err["path"] == ["shelves", "1", "code"]
    assert err["messages"] == ["This shelf code is not allowed."]
    assert not models.Branch.objects.filter(name="NestedBadCode").exists()


# ---------------------------------------------------------------------------
# Golden SDL coverage for the serializer-mutation input lane (spec-039 rev6 #16)
# ---------------------------------------------------------------------------


def _render_gql_type(type_dict: dict) -> str:
    """Render an introspected GraphQL type tree to its SDL string (``String!`` / ``[FieldError!]!``)."""
    kind = type_dict["kind"]
    if kind == "NON_NULL":
        return _render_gql_type(type_dict["ofType"]) + "!"
    if kind == "LIST":
        return "[" + _render_gql_type(type_dict["ofType"]) + "]"
    return type_dict["name"]


def _input_fields_sdl(type_name: str) -> list[tuple]:
    """Return an input object's ``[(field, rendered_type, description)]`` via introspection (rev6 #16)."""
    response = _post_graphql(
        'query { __type(name: "' + type_name + '") { inputFields { name description '
        "type { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } }",
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    fields = payload["data"]["__type"]["inputFields"]
    return [(f["name"], _render_gql_type(f["type"]), f["description"]) for f in fields]


def _type_fields_sdl(type_name: str) -> list[tuple]:
    """Return an object type's ``[(field, rendered_type, description)]`` via introspection (rev6 #16)."""
    response = _post_graphql(
        'query { __type(name: "' + type_name + '") { fields { name description '
        "type { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } }",
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    fields = payload["data"]["__type"]["fields"]
    return [(f["name"], _render_gql_type(f["type"]), f["description"]) for f in fields]


def test_golden_sdl_library_schema_hook_serializer_input():
    """Golden SDL for a library schema-hook serializer input + payload + the FieldError envelope (rev6 #16).

    Pins the generated input names, field names, nullability, descriptions (rev6 #9), the
    serializer-only enum (rev6 #6), the JSON / registry-mapped scalars (rev6 #7 / #11), the
    raw-pk relation id, the ``result`` payload slot (non-Relay ``Shelf``), and the additive
    ``codes`` / ``path`` on the shared ``FieldError`` envelope (rev6 #4 / #13) - so cross-field
    SDL drift is caught in one focused snapshot (NOT a whole-schema dump).
    """
    assert _input_fields_sdl("ShelfMetadataSerializerInput") == [
        ("code", "String!", None),
        ("branchId", "Int!", None),
        ("priority", "ShelfMetadataSerializerInputPriorityEnum", None),
        ("attributes", "JSON", None),
        ("accentColor", "String", None),
        ("label", "String", "A short human label for the shelf. Constraints: max_length=40."),
    ]
    assert _type_fields_sdl("CreateShelfViaMetadataSerializerPayload") == [
        ("result", "ShelfType", None),
        ("errors", "[FieldError!]!", None),
    ]
    # The shared FieldError envelope carries the additive codes + path (rev6 #4 / #13).
    assert _type_fields_sdl("FieldError") == [
        ("field", "String!", None),
        ("messages", "[String!]!", None),
        ("codes", "[String!]!", None),
        ("path", "[String!]!", None),
    ]


def test_golden_sdl_products_serializer_input():
    """Golden SDL for a products serializer input + payload (rev6 #16).

    Pins the file (``Upload``) + Relay-``GlobalID`` relation id (``categoryId: ID!``) + the
    ``allow_blank`` / ``max_length`` descriptions (rev6 #9) + the ``node`` payload slot
    (Relay-Node ``Item``). Both this and the library snapshot read the ONE aggregate
    ``/graphql/`` schema.
    """
    assert _input_fields_sdl("ItemSerializerInput") == [
        ("name", "String!", None),
        ("description", "String", "Constraints: allow_blank=true."),
        ("categoryId", "ID!", None),
        ("attachment", "Upload", "Constraints: max_length=100."),
    ]
    assert _type_fields_sdl("CreateItemViaSerializerPayload") == [
        ("node", "ItemType", None),
        ("errors", "[FieldError!]!", None),
    ]


# ---------------------------------------------------------------------------
# M2M duplicate-through-join tripwires (connection window rigor, workstream A).
#
# The windowed nested-connection prefetch partitions by an M2M relation name
# (plans.py::window_partition_for_prefetch), which joins the through table at
# plan time. Django's prefetch filtering then applies the parent predicate with
# django/db/models/fields/related_descriptors.py::_filter_prefetch_queryset
# #"reuse_all=True", which REUSES that join. On older Django generations (and
# in a hypothetical refactor that moves the window annotation after prefetch
# filtering) the predicate would add a SECOND through-table join instead -
# cartesian row duplication that inflates ``_dst_row_number`` partitions and
# ``_dst_total_count``. The prior live tests could not catch that: their data
# shapes attach each child to exactly one parent, so a duplicate join has
# fan-out x1 and produces correct-looking pages. These two tests seed
# OVERLAP-shaped graphs (children shared across parents, both M2M directions)
# and pin the per-parent pages, the counts, the fixed query count, and the
# exact number of through-table joins in the captured window SQL.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_nested_books_connection_overlap_single_through_join():
    """Reverse-M2M windows stay per-parent-exact when books span genres.

    Five books spread across three genres, every book in 2+ genres: a
    duplicate through-table join would multiply each book row once per extra
    membership, corrupting the ``ROW_NUMBER`` partitions (duplicated edges,
    inflated ``hasNextPage``). The window must page each genre's OWN books in
    pk order, in one prefetch query whose SQL joins ``library_book_genres``
    exactly once.
    """
    shelf = _seed_shelf()
    books = [
        models.Book.objects.create(title=f"Overlap-{index}", shelf=shelf) for index in range(5)
    ]
    genres = [models.Genre.objects.create(name=f"Overlap genre {index}") for index in range(3)]
    memberships = {
        0: (
            0,
            1,
            2,
            3,
        ),  # Overlap genre 0 <- books 0-3
        1: (
            1,
            2,
            3,
            4,
        ),  # Overlap genre 1 <- books 1-4
        2: (0, 2, 4),  # Overlap genre 2 <- books 0, 2, 4
    }
    for genre_index, book_indexes in memberships.items():
        for book_index in book_indexes:
            books[book_index].genres.add(genres[genre_index])

    query = """
    query {
      allLibraryGenresConnection {
        edges {
          node {
            name
            booksConnection(first: 2) {
              edges { node { title } }
              pageInfo { hasNextPage }
            }
          }
        }
      }
    }
    """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload

    edges = payload["data"]["allLibraryGenresConnection"]["edges"]
    expected_pages = {
        "Overlap genre 0": ["Overlap-0", "Overlap-1"],
        "Overlap genre 1": ["Overlap-1", "Overlap-2"],
        "Overlap genre 2": ["Overlap-0", "Overlap-2"],
    }
    assert len(edges) == 3
    for edge in edges:
        node = edge["node"]
        books_conn = node["booksConnection"]
        titles = [book_edge["node"]["title"] for book_edge in books_conn["edges"]]
        # Per-parent pk-ordered page - a duplicated join would repeat titles
        # or leak another parent's books into the page.
        assert titles == expected_pages[node["name"]]
        # Every genre carries >2 books, so the flag (derived from the window's
        # per-partition count) is True; an inflated count stays True, but a
        # partition corrupted by duplicates surfaces above in the titles.
        assert books_conn["pageInfo"]["hasNextPage"] is True

    # Root genres-connection query + ONE windowed prefetch (never per-parent).
    assert len(captured) == 2
    prefetch_sql = captured[1]["sql"]
    # The tripwire: the through table is joined exactly once - the window's
    # partition join, REUSED by the prefetch's parent predicate.
    assert prefetch_sql.count('JOIN "library_book_genres"') == 1


@pytest.mark.django_db
def test_nested_genres_connection_overlap_single_through_join():
    """Forward-M2M windows keep exact ``totalCount`` when genres span books.

    The forward direction of the tripwire above, riding ``genresConnection``
    (target ``GenreType``, ``total_count`` opted in): three books sharing
    genres from a pool of five. ``_dst_total_count`` is ``Count(1) OVER
    (PARTITION BY ...)`` - a duplicate through-table join inflates it
    directly, so the exact per-parent ``totalCount`` is the sharpest live
    signal this shape has.
    """
    shelf = _seed_shelf()
    genres = [models.Genre.objects.create(name=f"Shared genre {index}") for index in range(5)]
    memberships = {
        "Parable": (0, 1, 2),  # genres 0-2
        "Fledgling": (1, 2, 3),  # genres 1-3
        "Survivor": (0, 2, 4),  # genres 0, 2, 4
    }
    for title, genre_indexes in memberships.items():
        book = models.Book.objects.create(title=title, shelf=shelf)
        for genre_index in genre_indexes:
            book.genres.add(genres[genre_index])

    query = """
    query {
      allLibraryBooks {
        title
        genresConnection(first: 2) {
          edges { node { name } }
          totalCount
          pageInfo { hasNextPage }
        }
      }
    }
    """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload

    expected_pages = {
        "Parable": ["Shared genre 0", "Shared genre 1"],
        "Fledgling": ["Shared genre 1", "Shared genre 2"],
        "Survivor": ["Shared genre 0", "Shared genre 2"],
    }
    books = payload["data"]["allLibraryBooks"]
    assert len(books) == 3
    for book in books:
        genres_conn = book["genresConnection"]
        names = [genre_edge["node"]["name"] for genre_edge in genres_conn["edges"]]
        assert names == expected_pages[book["title"]]
        # Every book carries exactly 3 genres; a duplicated join would report
        # an inflated multiple here.
        assert genres_conn["totalCount"] == 3
        assert genres_conn["pageInfo"]["hasNextPage"] is True

    # Root books-list query + ONE windowed prefetch.
    assert len(captured) == 2
    prefetch_sql = captured[1]["sql"]
    assert prefetch_sql.count('JOIN "library_book_genres"') == 1


@pytest.mark.django_db
def test_nested_cheap_page_window_omits_total_count_annotation():
    """The common cheap-page shape compiles NO ``_dst_total_count`` window.

    Conditional total count (connection window rigor, workstream B - the
    MrThearMan-optimizer lesson): ``edges`` + cursors + ``hasPreviousPage``
    derive from ``_dst_row_number`` alone, so the per-partition ``Count(1)
    OVER`` is dropped from the window SQL for this shape. The page itself
    stays exact and the two-query cost holds - the annotation is the only
    thing that changed. ``hasNextPage`` / ``totalCount`` shapes keep the
    count; their existing pins above re-run unchanged.
    """
    shelf = _seed_shelf()
    for index in range(3):
        _seed_genre_with_books(
            f"Cheap-{index}",
            shelf,
            (f"Cheap-{index}-a", f"Cheap-{index}-b", f"Cheap-{index}-c"),
        )
    query = """
    query {
      allLibraryGenresConnection {
        edges {
          node {
            booksConnection(first: 2) {
              edges { cursor node { title } }
              pageInfo { hasPreviousPage startCursor }
            }
          }
        }
      }
    }
    """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload

    edges = payload["data"]["allLibraryGenresConnection"]["edges"]
    assert len(edges) == 3
    for index, edge in enumerate(edges):
        books_conn = edge["node"]["booksConnection"]
        titles = [book_edge["node"]["title"] for book_edge in books_conn["edges"]]
        assert titles == [f"Cheap-{index}-a", f"Cheap-{index}-b"]
        assert books_conn["pageInfo"]["hasPreviousPage"] is False
        assert books_conn["pageInfo"]["startCursor"] == books_conn["edges"][0]["cursor"]

    # Two queries (root + one window), and the window SQL carries the row
    # number but NOT the count aggregate.
    assert len(captured) == 2
    window_sql = captured[1]["sql"]
    assert "_dst_row_number" in window_sql
    assert "_dst_total_count" not in window_sql


@pytest.mark.django_db
@pytest.mark.parametrize(
    "args",
    ["first: 0", 'first: 2, after: "YXJyYXljb25uZWN0aW9uOjk5"'],
)
def test_nested_ambiguous_empty_served_from_marker_in_fixed_queries(args):
    """``first: 0`` / overshot ``after:`` serve true counts in TWO queries live.

    The marker-row disambiguation (connection window rigor, workstream C)
    live over /graphql/: these shapes historically fell back per-parent
    (2 + N queries for N parents); the window now keeps each partition's
    row 1, so every parent's empty page serves the TRUE ``totalCount`` and
    pipeline-parity ``pageInfo`` from the same single window query. Three
    parents, still two queries - the N+1 disproof for the previously
    ambiguous shapes.
    """
    shelf = _seed_shelf()
    for index in range(3):
        _seed_genre_with_books(
            f"Marker-{index}",
            shelf,
            (f"Marker-{index}-a", f"Marker-{index}-b", f"Marker-{index}-c"),
        )
    query = f"""
    query {{
      allLibraryGenresConnection {{
        edges {{
          node {{
            booksConnection({args}) {{
              edges {{ node {{ title }} }}
              pageInfo {{ hasNextPage hasPreviousPage }}
            }}
          }}
        }}
      }}
    }}
    """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload

    overshot = "after" in args
    edges = payload["data"]["allLibraryGenresConnection"]["edges"]
    assert len(edges) == 3
    for edge in edges:
        books_conn = edge["node"]["booksConnection"]
        assert books_conn["edges"] == []
        # Pipeline-parity flags (pinned against ListConnection in
        # tests/test_relay_connection.py): first: 0 -> a next page exists
        # (3 books past position 0); overshot after -> a previous page exists
        # (start > 0) and nothing follows.
        assert books_conn["pageInfo"]["hasNextPage"] is (not overshot)
        assert books_conn["pageInfo"]["hasPreviousPage"] is overshot

    # Root genres-connection + ONE window query - never 2 + parent_count.
    assert len(captured) == 2


@pytest.mark.django_db
def test_library_card_projection_survives_select_related_relation():
    """B8 root fix (feedback2 P0-1), live: consumer ``.only()`` + ``select_related``.

    ``allLibraryCardsProjected`` returns ``.only("barcode")`` while the query
    selects the forward ``patron`` relation - ``PatronType`` has no
    visibility hook, so the walker plans a REAL ``select_related("patron")``.
    Pre-fix the optimizer applied it on top of the projection and every
    request failed with ``FieldError: Field MembershipCard.patron cannot be
    both deferred and traversed using select_related at the same time``. The
    relation-aware prune drops the path (and its strictness keys - the
    package pin lives in ``tests/optimizer/test_extension.py``), so the
    response is correct and the relation resolves per row.
    """
    _seed_library_graph()

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryCardsProjected { barcode patron { name } }
            }
            """,
        )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "allLibraryCardsProjected": [
                {"barcode": "CARD-1", "patron": {"name": "Ada"}},
            ],
        },
    }
    # The dropped join resolves per row: root card page (patron_id stayed
    # deferred), the deferred ``patron_id`` load, then the patron row.
    assert len(captured) == 3
    assert "library_patron" not in captured[0]["sql"]


@pytest.mark.django_db
def test_library_card_deferred_projection_survives_select_related():
    """B8 root fix, defer flavor, live: ``.defer("patron")`` + ``select_related``.

    Django raises the same deferred-and-traversed ``FieldError`` for a
    ``defer()`` projection, so the prune's defer-mode rules (exact entries
    defer; everything else stays loaded) must drop the planned
    ``select_related("patron")`` live. Cheaper than the ``.only()`` sibling:
    the plan's own ``only()`` projection chains AFTER the consumer
    ``defer()`` and re-loads the ``patron_id`` connector (Django's
    defer-then-only replacement semantics), so no per-row deferred loads
    fire - just the root page and the patron fetch.
    """
    _seed_library_graph()

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allLibraryCardsDeferred { barcode patron { name } }
            }
            """,
        )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "allLibraryCardsDeferred": [
                {"barcode": "CARD-1", "patron": {"name": "Ada"}},
            ],
        },
    }
    assert len(captured) == 2
    assert "library_patron" not in captured[0]["sql"]


@pytest.mark.django_db
def test_nested_connection_last_zero_serves_quirk_via_per_parent_fallback():
    """``last: 0`` live: the serve-all quirk through the fallback, no dead window.

    Upstream ``ListConnection`` slices ``edges[-0:]`` - the WHOLE list - so
    ``last: 0`` returns every edge. The walker plans NOTHING for the shape
    (feedback2 P0-3): live queries pay the root query plus the per-parent
    pipeline (count + edges per genre for ``totalCount``), and NO discarded
    reversed-window query rides along.
    """
    shelf = _seed_shelf()
    for index in range(2):
        _seed_genre_with_books(
            f"LastZero-{index}",
            shelf,
            (f"LastZero-{index}-a", f"LastZero-{index}-b", f"LastZero-{index}-c"),
        )
    query = """
    query {
      allLibraryGenresConnection {
        edges {
          node {
            booksConnection(last: 0) {
              edges { node { title } }
              pageInfo { hasNextPage hasPreviousPage }
            }
          }
        }
      }
    }
    """
    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    edges = payload["data"]["allLibraryGenresConnection"]["edges"]
    assert len(edges) == 2
    for index, edge in enumerate(edges):
        books_conn = edge["node"]["booksConnection"]
        # The upstream ``edges[-0:]`` quirk: ALL three edges served.
        assert [e["node"]["title"] for e in books_conn["edges"]] == [
            f"LastZero-{index}-a",
            f"LastZero-{index}-b",
            f"LastZero-{index}-c",
        ]
        assert books_conn["pageInfo"] == {"hasNextPage": False, "hasPreviousPage": False}
    # Root genres connection + one per-parent pipeline query per genre = 3 -
    # and no window SQL anywhere (pre-fix: a discarded reversed window added
    # one more query per request and hid the fallback from strictness).
    assert len(captured) == 3
    assert not any("_dst_row_number" in entry["sql"] for entry in captured)
