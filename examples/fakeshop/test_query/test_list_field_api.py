"""Live sync-HTTP contract for ``DjangoListField`` arguments.

This is the SYNC counterpart of ``test_list_field_async_api.py``. It covers the sync
acceptance surface over live HTTP (``/graphql/`` for shipped schema fields and
``/graphql-test/`` for test-local holder schemas).
"""

from __future__ import annotations

from typing import Any

import pytest
import strawberry
from apps.glossary import models as glossary_models
from apps.glossary import schema as glossary_schema
from apps.library import models as library_models
from apps.library import schema as library_schema
from apps.library.orders import BranchOrder
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, models
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches, path
from graphql_client import graphql_payload, post_graphql
from strawberry.schema.name_converter import NameConverter

import django_strawberry_framework.list_field as list_field_module
from django_strawberry_framework import (
    DjangoConnection,
    DjangoConnectionField,
    DjangoListField,
    strawberry_config,
)
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.orders import Ordering
from django_strawberry_framework.resource_policy import bounded_rows
from django_strawberry_framework.schema import DjangoSchema
from django_strawberry_framework.utils.querysets import apply_type_visibility_sync
from django_strawberry_framework.views import DjangoGraphQLView

_ERROR_POLICY_PASS_THROUGH = {
    "DEBUG": True,
    "MIDDLEWARE": [entry for entry in settings.MIDDLEWARE if "debug_toolbar" not in entry],
}

_CURRENT: dict[str, Any] = {"schema": None, "view_class": None}


def _graphql_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    view_class = _CURRENT["view_class"] or DjangoGraphQLView
    return view_class.as_view(schema=schema)(request)


urlpatterns = [
    path("graphql-test/", _graphql_view),
]


def _staff_client() -> Client:
    user_model = get_user_model()
    staff = user_model.objects.create_user(
        username="staff_list_sync",
        password="pw",
        is_staff=True,
    )
    client = Client()
    client.force_login(staff)
    return client


def _post_sync_response(
    schema: DjangoSchema | strawberry.Schema,
    query: str,
    *,
    variables: dict[str, Any] | None = None,
    client: Client | None = None,
    extra_settings: dict[str, Any] | None = None,
    view_class: type[DjangoGraphQLView] | None = None,
):
    """Post to the test mount and return the RAW ``HttpResponse``.

    The parsed-payload sibling below is what most cases want; the raw response is
    for the one claim a parsed dictionary cannot carry - that two renderings are
    the same bytes.
    """
    _CURRENT["schema"] = schema
    _CURRENT["view_class"] = view_class
    override_dict: dict[str, Any] = {"ROOT_URLCONF": __name__}
    if extra_settings:
        override_dict.update(extra_settings)
    try:
        with override_settings(**override_dict):
            clear_url_caches()
            return post_graphql(
                query,
                client=client,
                variables=variables,
                url="/graphql-test/",
            )
    finally:
        _CURRENT["schema"] = None
        _CURRENT["view_class"] = None
        clear_url_caches()


def _post_sync(
    schema: DjangoSchema | strawberry.Schema,
    query: str,
    *,
    variables: dict[str, Any] | None = None,
    client: Client | None = None,
    extra_settings: dict[str, Any] | None = None,
    view_class: type[DjangoGraphQLView] | None = None,
) -> dict[str, Any]:
    response = _post_sync_response(
        schema,
        query,
        variables=variables,
        client=client,
        extra_settings=extra_settings,
        view_class=view_class,
    )
    assert response.status_code == 200
    return response.json()


# ---------------------------------------------------------------------------
# 1. Shipped fields introspection
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_shipped_branches_introspection_arguments():
    query = """
    query {
      __type(name: "Query") {
        fields {
          name
          type {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                }
              }
            }
          }
          args {
            name
            type {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    payload = graphql_payload(query)
    fields = {f["name"]: f for f in payload["data"]["__type"]["fields"]}

    for field_name in (
        "allLibraryBranchesViaListField",
        "allLibraryBranchesViaListFieldNullable",
        "allLibraryBranchesViaListFieldManagerResolver",
    ):
        assert field_name in fields
        field_data = fields[field_name]
        args_map = {a["name"]: a for a in field_data["args"]}

        assert "offset" in args_map
        assert args_map["offset"]["type"]["kind"] == "SCALAR"
        assert args_map["offset"]["type"]["name"] == "Int"

        assert "limit" in args_map
        assert args_map["limit"]["type"]["kind"] == "SCALAR"
        assert args_map["limit"]["type"]["name"] == "Int"

        assert "orderBy" in args_map
        order_type = args_map["orderBy"]["type"]
        assert order_type["kind"] == "LIST"
        assert order_type["ofType"]["kind"] == "NON_NULL"
        assert order_type["ofType"]["ofType"]["name"] == "BranchOrderInputType"

    # Non-null list return type: the consumer's bare ``list[BranchType]``
    # annotation renders all four levels NON_NULL -> LIST -> NON_NULL -> OBJECT,
    # so neither the list nor an item may ever be null.
    ret_default = fields["allLibraryBranchesViaListField"]["type"]
    assert ret_default["kind"] == "NON_NULL"
    assert ret_default["ofType"]["kind"] == "LIST"
    assert ret_default["ofType"]["ofType"]["kind"] == "NON_NULL"
    assert ret_default["ofType"]["ofType"]["ofType"]["kind"] == "OBJECT"
    assert ret_default["ofType"]["ofType"]["ofType"]["name"] == "BranchType"

    # Nullable list return type: LIST -> NON_NULL -> OBJECT. Only the OUTER
    # nullability differs from the default sibling above, which is what makes
    # that sibling's four levels a statement about the annotation rather than
    # about ``DjangoListField`` rendering one fixed shape.
    ret_nullable = fields["allLibraryBranchesViaListFieldNullable"]["type"]
    assert ret_nullable["kind"] == "LIST"
    assert ret_nullable["ofType"]["kind"] == "NON_NULL"
    assert ret_nullable["ofType"]["ofType"]["kind"] == "OBJECT"
    assert ret_nullable["ofType"]["ofType"]["name"] == "BranchType"


# ---------------------------------------------------------------------------
# 2-4. Live filtering, visibility, ordering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_shipped_branches_staff_ordered_offset_limit():
    library_models.Branch.objects.create(name="Bravo", city="Boston")
    library_models.Branch.objects.create(name="Alpha", city="Boston")
    library_models.Branch.objects.create(name="Delta", city="Boston")
    library_models.Branch.objects.create(name="Charlie", city="Boston")

    client = _staff_client()
    with CaptureQueriesContext(connection) as limit_ctx:
        limit_payload = graphql_payload(
            "{ allLibraryBranchesViaListField(limit: 2) { name } }",
            client=client,
        )
    assert "errors" not in limit_payload, limit_payload
    limit_queries = [
        query["sql"].upper()
        for query in limit_ctx.captured_queries
        if "LIBRARY_BRANCH" in query["sql"].upper()
    ]
    assert len(limit_queries) == 1
    assert "LIMIT 2" in limit_queries[0]
    assert "OFFSET" not in limit_queries[0]

    query = """
    query {
      allLibraryBranchesViaListField(
        orderBy: [{ name: ASC }, { id: ASC }]
        offset: 1
        limit: 2
      ) {
        name
      }
    }
    """
    with CaptureQueriesContext(connection) as ctx:
        payload = graphql_payload(query, client=client)
    assert "errors" not in payload, payload
    names = [row["name"] for row in payload["data"]["allLibraryBranchesViaListField"]]
    assert names == ["Bravo", "Charlie"]
    branch_queries = [
        q["sql"].upper() for q in ctx.captured_queries if "LIBRARY_BRANCH" in q["sql"].upper()
    ]
    assert len(branch_queries) == 1
    assert "LIMIT 2 OFFSET 1" in branch_queries[0]


@pytest.mark.django_db
def test_shipped_branches_anonymous_visibility_before_offset():
    # Restricted city branch must be excluded by BranchType.get_queryset BEFORE offset
    library_models.Branch.objects.create(name="Alpha", city="Boston")
    library_models.Branch.objects.create(name="Hidden", city="restricted")
    library_models.Branch.objects.create(name="Bravo", city="Boston")
    library_models.Branch.objects.create(name="Charlie", city="Boston")

    query = """
    query {
      allLibraryBranchesViaListField(
        orderBy: [{ city: ASC }, { id: ASC }]
        offset: 1
        limit: 2
      ) {
        name
      }
    }
    """
    payload = graphql_payload(query)
    assert "errors" not in payload, payload
    names = [row["name"] for row in payload["data"]["allLibraryBranchesViaListField"]]
    assert names == ["Bravo", "Charlie"]


@pytest.mark.django_db
def test_shipped_branches_order_by_alone():
    library_models.Branch.objects.create(name="Charlie", city="Boston")
    library_models.Branch.objects.create(name="Alpha", city="Boston")
    library_models.Branch.objects.create(name="Bravo", city="Boston")

    client = _staff_client()
    query = """
    query {
      allLibraryBranchesViaListField(orderBy: [{ name: ASC }]) {
        name
      }
    }
    """
    payload = graphql_payload(query, client=client)
    assert "errors" not in payload, payload
    names = [row["name"] for row in payload["data"]["allLibraryBranchesViaListField"]]
    assert names == ["Alpha", "Bravo", "Charlie"]


# ---------------------------------------------------------------------------
# 5-7. Bounds and order precondition rejections
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_shipped_branches_nonzero_offset_without_order_rejected():
    library_models.Branch.objects.create(name="Alpha", city="Boston")
    query = """
    query {
      allLibraryBranchesViaListField(offset: 1) {
        name
      }
    }
    """
    payload = graphql_payload(query)
    assert "errors" in payload
    err = payload["errors"][0]
    assert err["extensions"]["code"] == "LIST_ARGUMENT_INVALID"
    assert err["extensions"]["reason"] == "order_required"
    assert err["extensions"]["argument"] == "offset"
    assert err["extensions"]["value"] == 1
    assert "Invalid argument 'offset' on allLibraryBranchesViaListField:" in err["message"]
    assert "requires an active ordering via 'orderBy' or model 'Meta.ordering'." in err["message"]


@pytest.mark.django_db
def test_shipped_branches_offset_bounds_rejected():
    # Negative offset
    payload_neg = graphql_payload(
        "{ allLibraryBranchesViaListField(offset: -1) { name } }",
    )
    assert "errors" in payload_neg
    err_neg = payload_neg["errors"][0]
    assert err_neg["extensions"]["code"] == "LIST_ARGUMENT_INVALID"
    assert err_neg["extensions"]["reason"] == "negative"
    assert err_neg["extensions"]["argument"] == "offset"
    assert err_neg["extensions"]["value"] == -1

    # Over ceiling (default policy max_list_rows is 100)
    payload_ceil = graphql_payload(
        "{ allLibraryBranchesViaListField(offset: 101) { name } }",
    )
    assert "errors" in payload_ceil
    err_ceil = payload_ceil["errors"][0]
    assert err_ceil["extensions"]["code"] == "LIST_ARGUMENT_INVALID"
    assert err_ceil["extensions"]["reason"] == "over_ceiling"
    assert err_ceil["extensions"]["argument"] == "offset"
    assert err_ceil["extensions"]["value"] == 101
    assert err_ceil["extensions"]["ceiling"] == 100


@pytest.mark.django_db
def test_shipped_branches_limit_bounds_rejected():
    # Negative limit
    payload_neg = graphql_payload(
        "{ allLibraryBranchesViaListField(limit: -1) { name } }",
    )
    assert "errors" in payload_neg
    err_neg = payload_neg["errors"][0]
    assert err_neg["extensions"]["code"] == "LIST_ARGUMENT_INVALID"
    assert err_neg["extensions"]["reason"] == "negative"
    assert err_neg["extensions"]["argument"] == "limit"
    assert err_neg["extensions"]["value"] == -1

    # Over ceiling (101 > 100)
    payload_ceil = graphql_payload(
        "{ allLibraryBranchesViaListField(limit: 101) { name } }",
    )
    assert "errors" in payload_ceil
    err_ceil = payload_ceil["errors"][0]
    assert err_ceil["extensions"]["code"] == "LIST_ARGUMENT_INVALID"
    assert err_ceil["extensions"]["reason"] == "over_ceiling"
    assert err_ceil["extensions"]["argument"] == "limit"
    assert err_ceil["extensions"]["value"] == 101
    assert err_ceil["extensions"]["ceiling"] == 100


# ---------------------------------------------------------------------------
# 8-10. Coercion and limit: 0 short-circuiting
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_shipped_branches_coercion_failures_and_integral_floats():
    library_models.Branch.objects.create(name="Alpha", city="Boston")

    query_var = """
    query($lim: Int) {
      allLibraryBranchesViaListField(limit: $lim) {
        name
      }
    }
    """
    for bad_val in ("one", True, 1.5):
        with CaptureQueriesContext(connection) as ctx:
            payload = graphql_payload(query_var, variables={"lim": bad_val})
        assert "errors" in payload
        # No resolver SQL executed
        assert len(ctx.captured_queries) == 0

    # Float literal in document
    with CaptureQueriesContext(connection) as ctx:
        payload_lit = graphql_payload(
            "{ allLibraryBranchesViaListField(limit: 1.5) { name } }",
        )
    assert "errors" in payload_lit
    assert len(ctx.captured_queries) == 0

    # Integral float variable coerces to int 1 and succeeds
    payload_int_float = graphql_payload(query_var, variables={"lim": 1.0})
    assert "errors" not in payload_int_float, payload_int_float
    assert len(payload_int_float["data"]["allLibraryBranchesViaListField"]) == 1


@pytest.mark.django_db
def test_shipped_branches_limit_zero_short_circuits_sql():
    library_models.Branch.objects.create(name="Alpha", city="Boston")
    library_models.Branch.objects.create(name="Bravo", city="Boston")

    with CaptureQueriesContext(connection) as ctx:
        payload = graphql_payload(
            "{ allLibraryBranchesViaListField(limit: 0) { name } }",
        )
    assert "errors" not in payload, payload
    assert payload["data"]["allLibraryBranchesViaListField"] == []
    assert len(ctx.captured_queries) == 0


@pytest.mark.django_db
def test_shipped_branches_offset_with_limit_zero_precondition():
    # offset: 1, limit: 0 without ordering violates precondition
    payload_no_ord = graphql_payload(
        "{ allLibraryBranchesViaListField(offset: 1, limit: 0) { name } }",
    )
    assert "errors" in payload_no_ord
    assert payload_no_ord["errors"][0]["extensions"]["reason"] == "order_required"

    # offset: 1, limit: 0 with active ordering short-circuits with 0 row queries
    with CaptureQueriesContext(connection) as ctx:
        payload_ord = graphql_payload(
            """
            query {
              allLibraryBranchesViaListField(
                orderBy: [{ city: ASC }]
                offset: 1
                limit: 0
              ) {
                name
              }
            }
            """,
        )
    assert "errors" not in payload_ord, payload_ord
    assert payload_ord["data"]["allLibraryBranchesViaListField"] == []
    assert len(ctx.captured_queries) == 0


# ---------------------------------------------------------------------------
# 11-13. Holder schemas: trusted, non-queryset, presliced
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_holder_trusted_widened_field():
    @strawberry.type
    class _TrustedQuery:
        branches_trusted: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            max_rows=105,
            trusted_max_rows=True,
        )

    schema = DjangoSchema(query=_TrustedQuery, config=strawberry_config())
    library_models.Branch.objects.bulk_create(
        [library_models.Branch(name=f"Branch {i}", city="Boston") for i in range(105)],
    )

    # Omitted client limit returns widened max_rows (105)
    payload_wide = _post_sync(schema, "{ branchesTrusted { name } }")
    assert "errors" not in payload_wide, payload_wide
    assert len(payload_wide["data"]["branchesTrusted"]) == 105

    # Client offset over policy ceiling (101 > 100) still rejects
    payload_offset = _post_sync(schema, "{ branchesTrusted(offset: 101) { name } }")
    assert "errors" in payload_offset
    err = payload_offset["errors"][0]
    assert err["extensions"]["reason"] == "over_ceiling"
    assert err["extensions"]["ceiling"] == 100


@pytest.mark.django_db
def test_holder_materialized_and_nullable_none_fields():
    @strawberry.type
    class _NonQsQuery:
        branches_materialized: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: list(library_models.Branch.objects.all()),
        )
        branches_nullable_none: list[library_schema.BranchType] | None = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: None,
        )

    schema = DjangoSchema(query=_NonQsQuery, config=strawberry_config())
    library_models.Branch.objects.create(name="Alpha", city="Boston")
    library_models.Branch.objects.create(name="Bravo", city="Boston")
    library_models.Branch.objects.create(name="Charlie", city="Boston")

    # Materialized list: limit and offset 0 work
    p_mat = _post_sync(schema, "{ branchesMaterialized(limit: 2) { name } }")
    assert "errors" not in p_mat, p_mat
    assert len(p_mat["data"]["branchesMaterialized"]) == 2

    p_mat_off0 = _post_sync(schema, "{ branchesMaterialized(offset: 0) { name } }")
    assert "errors" not in p_mat_off0, p_mat_off0
    assert len(p_mat_off0["data"]["branchesMaterialized"]) == 3

    # Nonzero offset rejects order_required
    p_mat_off = _post_sync(schema, "{ branchesMaterialized(offset: 1) { name } }")
    assert p_mat_off["errors"][0]["extensions"]["reason"] == "order_required"

    # Non-null orderBy rejects queryset_required
    p_mat_ord = _post_sync(schema, "{ branchesMaterialized(orderBy: []) { name } }")
    assert p_mat_ord["errors"][0]["extensions"]["reason"] == "queryset_required"
    assert "on branchesMaterialized" in p_mat_ord["errors"][0]["message"]

    # Nullable None list: limit and offset 0 return null
    p_none = _post_sync(schema, "{ branchesNullableNone(limit: 2) { name } }")
    assert "errors" not in p_none, p_none
    assert p_none["data"]["branchesNullableNone"] is None

    p_none_off0 = _post_sync(schema, "{ branchesNullableNone(offset: 0) { name } }")
    assert "errors" not in p_none_off0, p_none_off0
    assert p_none_off0["data"]["branchesNullableNone"] is None

    p_none_off = _post_sync(schema, "{ branchesNullableNone(offset: 1) { name } }")
    assert p_none_off["errors"][0]["extensions"]["reason"] == "order_required"

    p_none_ord = _post_sync(schema, "{ branchesNullableNone(orderBy: []) { name } }")
    assert p_none_ord["errors"][0]["extensions"]["reason"] == "queryset_required"


@pytest.mark.django_db
def test_holder_presliced_configuration_error_under_pass_through():
    @strawberry.type
    class _PreslicedQuery:
        branches_presliced: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: library_models.Branch.objects.all()[:5],
        )

    schema = DjangoSchema(query=_PreslicedQuery, config=strawberry_config())
    library_models.Branch.objects.create(name="Alpha", city="Boston")

    # Omitted arguments
    p_omit = _post_sync(
        schema,
        "{ branchesPresliced { name } }",
        extra_settings=_ERROR_POLICY_PASS_THROUGH,
    )
    assert p_omit["data"] is None
    assert "sliced" in p_omit["errors"][0]["message"].lower()

    # Active limit argument
    p_act = _post_sync(
        schema,
        "{ branchesPresliced(limit: 2) { name } }",
        extra_settings=_ERROR_POLICY_PASS_THROUGH,
    )
    assert p_act["data"] is None
    assert "sliced" in p_act["errors"][0]["message"].lower()


# ---------------------------------------------------------------------------
# 14-16. Order precedence, aggregation distinct, error pairs
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_shipped_branches_empty_order_and_permission_precedence():
    # Empty order input does not satisfy nonzero offset order requirement
    p_empty = graphql_payload(
        "{ allLibraryBranchesViaListField(orderBy: [], offset: 1) { name } }",
    )
    assert p_empty["errors"][0]["extensions"]["reason"] == "order_required"

    # All-null terms do not satisfy it
    p_null_term = graphql_payload(
        "{ allLibraryBranchesViaListField(orderBy: [{ id: null }], offset: 1) { name } }",
    )
    assert p_null_term["errors"][0]["extensions"]["reason"] == "order_required"

    # Anonymous user sending staff-gated 'name' order + offset: 1 hits permission first
    p_perm = graphql_payload(
        "{ allLibraryBranchesViaListField(orderBy: [{ name: ASC }], offset: 1) { name } }",
    )
    assert p_perm["errors"][0]["extensions"]["code"] == "ORDER_PERMISSION_DENIED"


@pytest.mark.django_db
def test_shipped_branches_aggregate_order_no_distinct_in_sql():
    client = _staff_client()
    for i in range(3):
        b = library_models.Branch.objects.create(name=f"Branch {i}", city="Boston")
        library_models.Shelf.objects.create(code=f"S-{i}-1", branch=b)
        library_models.Shelf.objects.create(code=f"S-{i}-2", branch=b)

    query = """
    query {
      allLibraryBranchesViaListField(
        orderBy: [{ shelves: { code: DESC } }]
        offset: 1
        limit: 2
      ) {
        name
      }
    }
    """
    with CaptureQueriesContext(connection) as ctx:
        payload = graphql_payload(query, client=client)
    assert "errors" not in payload, payload
    rows = payload["data"]["allLibraryBranchesViaListField"]
    assert len(rows) == 2
    assert len({r["name"] for r in rows}) == 2

    # Verify no SELECT DISTINCT was injected into SQL
    for q in ctx.captured_queries:
        assert "DISTINCT" not in q["sql"].upper()


@pytest.mark.django_db
def test_shipped_branches_error_precedence_pairs():
    # 1. offset: -1, limit: -1 -> negative precedes limit
    p_both = graphql_payload(
        "{ allLibraryBranchesViaListField(offset: -1, limit: -1) { name } }",
    )
    assert p_both["errors"][0]["extensions"]["reason"] == "negative"
    assert p_both["errors"][0]["extensions"]["argument"] == "offset"

    # 2. Materialized field with orderBy + offset: 1 -> queryset_required precedes order_required
    @strawberry.type
    class _MatQuery:
        branches_materialized: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: list(library_models.Branch.objects.all()),
        )

    schema = DjangoSchema(query=_MatQuery, config=strawberry_config())
    p_mat = _post_sync(
        schema,
        "{ branchesMaterialized(orderBy: [{ city: ASC }], offset: 1) { name } }",
    )
    assert p_mat["errors"][0]["extensions"]["reason"] == "queryset_required"

    # 3. Presliced with orderBy under pass-through -> presliced source seal precedes order
    @strawberry.type
    class _PreQuery:
        branches_presliced: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: library_models.Branch.objects.all()[:2],
        )

    schema_pre = DjangoSchema(query=_PreQuery, config=strawberry_config())
    p_pre = _post_sync(
        schema_pre,
        "{ branchesPresliced(orderBy: [{ city: ASC }]) { name } }",
        extra_settings=_ERROR_POLICY_PASS_THROUGH,
    )
    assert p_pre["data"] is None
    assert "sliced" in p_pre["errors"][0]["message"].lower()


# ---------------------------------------------------------------------------
# 17-20. Combined querysets, naming converters, model ordering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_holder_branches_combined_seals(monkeypatch):
    library_models.Branch.objects.create(name="A", city="Boston")
    library_models.Branch.objects.create(name="B", city="Boston")

    visibility_calls = 0
    original_get_queryset = library_schema.BranchType.get_queryset

    def _tracking_get_queryset(cls, queryset, info, **kwargs):
        nonlocal visibility_calls
        visibility_calls += 1
        return original_get_queryset(queryset, info, **kwargs)

    monkeypatch.setattr(
        library_schema.BranchType,
        "get_queryset",
        classmethod(_tracking_get_queryset),
    )

    # Combined source queryset: union combinator
    @strawberry.type
    class _CombinedQuery:
        branches_combined: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: library_models.Branch.objects.filter(name="A").union(
                library_models.Branch.objects.filter(name="B"),
            ),
        )

    schema = DjangoSchema(query=_CombinedQuery, config=strawberry_config())

    # Active argument (limit: 0 or offset: 0) rejects at source seal with ConfigurationError
    p_act = _post_sync(
        schema,
        "{ branchesCombined(limit: 0) { name } }",
        extra_settings=_ERROR_POLICY_PASS_THROUGH,
    )
    assert p_act["data"] is None
    assert "combined" in p_act["errors"][0]["message"].lower()
    assert visibility_calls == 0

    # Result seal: test-local custom OrderSet override returning a union combined queryset
    def _malicious_apply_sync(
        cls,
        order_input,
        queryset,
        info,
    ):
        return queryset.filter(name="A").union(queryset.filter(name="B"))

    monkeypatch.setattr(BranchOrder, "apply_sync", classmethod(_malicious_apply_sync))

    with override_settings(**_ERROR_POLICY_PASS_THROUGH):
        p_hook = graphql_payload(
            """
            query {
              allLibraryBranchesViaListField(
                orderBy: [{ city: ASC }]
                offset: 1
              ) {
                name
              }
            }
            """,
        )
    # Post-orderset validation rejects with the exact ``combined`` defect.
    assert "errors" in p_hook
    assert p_hook["data"] is None
    assert p_hook["errors"][0]["message"].startswith(_BRANCH_ORDER_SHAPE_PREFIX)
    assert "got combined defect" in p_hook["errors"][0]["message"]


_BRANCH_ORDER_SHAPE_PREFIX = (
    "BranchOrder.apply_sync must return an unevaluated, unsliced, uncombined "
    "QuerySet of Branch rows; got "
)


@pytest.mark.django_db
def test_holder_branches_post_orderset_malformed_result_matrix(monkeypatch):
    """Every malformed ``apply_sync`` result the seal can reach live names its exact defect.

    Each row runs a real ``/graphql/`` request against the shipped field with the
    override in place, asserts the exact rejection it must produce rather than the
    sentence the rows share, and captures SQL so a row that must not execute proves
    it did not.
    """
    library_models.Branch.objects.create(name="A", city="Boston")
    query = "{ allLibraryBranchesViaListField(orderBy: [{ city: ASC }]) { name } }"

    def _run(override):
        monkeypatch.setattr(BranchOrder, "apply_sync", classmethod(override))
        with (
            override_settings(**_ERROR_POLICY_PASS_THROUGH),
            CaptureQueriesContext(connection) as ctx,
        ):
            payload = graphql_payload(query)
        assert payload["data"] is None
        branch_sql = [
            q["sql"] for q in ctx.captured_queries if "library_branch" in q["sql"].lower()
        ]
        return payload["errors"][0]["message"], branch_sql

    # 1. Evaluated: the override executed the query and returned the SAME, now-cached
    #    queryset. The seal names ``evaluated`` and the framework issued no second query.
    def _evaluated(
        cls,
        order_input,
        queryset,
        info,
    ):
        list(queryset)
        return queryset

    message, branch_sql = _run(_evaluated)
    assert message.startswith(_BRANCH_ORDER_SHAPE_PREFIX + "evaluated defect")
    assert len(branch_sql) == 1

    # 2. A materialized list is not a QuerySet at all: a ``type`` defect, distinct from row 1.
    message, branch_sql = _run(lambda cls, order_input, queryset, info: list(queryset))
    assert message.startswith(_BRANCH_ORDER_SHAPE_PREFIX + "type defect")
    assert len(branch_sql) == 1

    # 3. ``None`` is the other non-queryset shape.
    message, branch_sql = _run(lambda cls, order_input, queryset, info: None)
    assert message.startswith(_BRANCH_ORDER_SHAPE_PREFIX + "type defect")
    assert branch_sql == []

    # 4. Projection.
    message, branch_sql = _run(lambda cls, order_input, queryset, info: queryset.values("name"))
    assert message.startswith(_BRANCH_ORDER_SHAPE_PREFIX + "projection defect")
    assert branch_sql == []

    # 5. Wrong model.
    message, branch_sql = _run(
        lambda cls, order_input, queryset, info: library_models.Book.objects.all(),
    )
    assert message.startswith(_BRANCH_ORDER_SHAPE_PREFIX + "table defect")
    assert branch_sql == []

    # 6. Sliced after ordering: the window is the framework's to take, once.
    message, branch_sql = _run(
        lambda cls, order_input, queryset, info: queryset.order_by("name")[:1],
    )
    assert message.startswith(_BRANCH_ORDER_SHAPE_PREFIX + "sliced defect")
    assert branch_sql == []

    # 7. Combined.
    message, branch_sql = _run(
        lambda cls, order_input, queryset, info: queryset.filter(name="A").union(
            queryset.filter(name="B"),
        ),
    )
    assert message.startswith(_BRANCH_ORDER_SHAPE_PREFIX + "combined defect")
    assert branch_sql == []

    # 8. A sync override returning an awaitable violates the sync protocol; the
    #    awaitable is disposed rather than left un-awaited.
    async def _later(queryset):
        return queryset

    message, branch_sql = _run(lambda cls, order_input, queryset, info: _later(queryset))
    assert message.startswith(
        "BranchOrder.apply_sync returned an awaitable in a sync resolver context.",
    )
    assert branch_sql == []

    # 9. Routing rewritten IN PLACE on the queryset the override was handed, then
    #    returned as-is: compared against the pre-call snapshot, not the mutated object.
    def _in_place_routing(
        cls,
        order_input,
        queryset,
        info,
    ):
        queryset._hints = {"tenant": 2}
        return queryset

    message, branch_sql = _run(_in_place_routing)
    assert message.startswith("BranchOrder.apply_sync changed database routing intent")
    assert "expected db=None, hints={}" in message
    assert "got db=None, hints={'tenant': 2}" in message
    assert branch_sql == []

    # 10. A queryset SUBCLASS carrying an unresolved deferred filter: a predicate
    #     not yet baked into the query, which the seal cannot faithfully rebuild.
    #     Django leaves one only on an EXACT plain queryset, so a subclass holding
    #     one is not that artifact and fails closed as ``untrusted``.
    class _DeferredFilterQuerySet(models.QuerySet):
        pass

    def _untrusted(
        cls,
        order_input,
        queryset,
        info,
    ):
        candidate = _DeferredFilterQuerySet(model=library_models.Branch)
        candidate._deferred_filter = (False, (), {"name": "A"})
        return candidate

    message, branch_sql = _run(_untrusted)
    assert message.startswith(_BRANCH_ORDER_SHAPE_PREFIX + "untrusted defect")
    assert "carries an unresolved deferred filter" in message
    assert branch_sql == []


@pytest.mark.django_db
def test_holder_branches_hostile_normalized_term_is_rejected_before_it_can_run(monkeypatch):
    """A ``_normalize_input`` override returning a ``str`` SUBCLASS term is a configuration error.

    The term never reaches the purity compare or the flat-order walk, so its
    ``__eq__`` / ``__format__`` hooks never fire; the request reports the
    boundary's actionable error instead of the hook's own failure.
    """
    library_models.Branch.objects.create(name="A", city="Boston")

    class _HostileStr(str):
        def __eq__(self, other):
            raise RuntimeError("hostile equality ran")

        __hash__ = str.__hash__

        def __format__(self, spec):
            raise RuntimeError("hostile format ran")

    monkeypatch.setattr(
        BranchOrder,
        "_normalize_input",
        classmethod(lambda cls, input_value: [(_HostileStr("city"), Ordering.ASC)]),
    )
    with override_settings(**_ERROR_POLICY_PASS_THROUGH), CaptureQueriesContext(connection) as ctx:
        payload = graphql_payload(
            "{ allLibraryBranchesViaListField(orderBy: [{ city: ASC }], offset: 1) { name } }",
        )
    assert payload["data"] is None
    message = payload["errors"][0]["message"]
    assert "BranchOrder._normalize_input returned invalid term" in message
    assert "hostile" not in message
    assert [q for q in ctx.captured_queries if "library_branch" in q["sql"].lower()] == []


@pytest.mark.django_db
def test_holder_naming_converters():
    # 1. auto_camel_case=False
    @strawberry.type
    class _SnakeQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)

    snake_schema = DjangoSchema(
        query=_SnakeQuery,
        config=strawberry_config(auto_camel_case=False),
    )
    # Introspect args
    introspect_q = """
    query {
      __schema {
        queryType {
          fields {
            name
            args {
              name
            }
          }
        }
      }
    }
    """
    p_intro = _post_sync(snake_schema, introspect_q)
    field_args = {a["name"] for a in p_intro["data"]["__schema"]["queryType"]["fields"][0]["args"]}
    assert "order_by" in field_args
    assert "offset" in field_args
    assert "limit" in field_args

    # Error message reports 'offset' wire name
    p_err = _post_sync(
        snake_schema,
        "{ branches(order_by: [{ id: null }], offset: 1) { name } }",
    )
    assert p_err["errors"][0]["extensions"]["argument"] == "offset"

    # 2. Custom NameConverter
    class _UpperConverter(NameConverter):
        def get_graphql_name(self, obj):
            name = super().get_graphql_name(obj)
            return name.upper()

    @strawberry.type
    class _UpperQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)

    upper_schema = DjangoSchema(
        query=_UpperQuery,
        config=strawberry_config(name_converter=_UpperConverter()),
    )
    p_up_intro = _post_sync(
        upper_schema,
        "query { __schema { queryType { fields { name args { name } } } } }",
    )
    up_args = {a["name"] for a in p_up_intro["data"]["__schema"]["queryType"]["fields"][0]["args"]}
    assert "OFFSET" in up_args
    assert "LIMIT" in up_args
    assert "ORDERBY" in up_args

    p_up_err = _post_sync(upper_schema, "{ BRANCHES(OFFSET: -1) { NAME } }")
    assert p_up_err["errors"][0]["extensions"]["argument"] == "OFFSET"

    # 3. The rejection reports the PUBLISHED name and runs the converter no more than
    #    a successful request does: Strawberry maps arguments through the converter
    #    on every execution, and the framework's error path adds nothing to that.
    class _CountingConverter(NameConverter):
        calls = 0

        def from_argument(self, argument):
            type(self).calls += 1
            return super().from_argument(argument).upper()

    @strawberry.type
    class _CountingQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)

    counting_schema = DjangoSchema(
        query=_CountingQuery,
        config=strawberry_config(name_converter=_CountingConverter()),
    )
    p_intro = _post_sync(
        counting_schema,
        "query { __schema { queryType { fields { name args { name } } } } }",
    )
    published = {a["name"] for a in p_intro["data"]["__schema"]["queryType"]["fields"][0]["args"]}
    assert published == {"OFFSET", "LIMIT", "ORDERBY"}

    before = _CountingConverter.calls
    p_ok = _post_sync(counting_schema, "{ branches(LIMIT: 1) { name } }")
    assert "errors" not in p_ok, p_ok
    per_success = _CountingConverter.calls - before

    before = _CountingConverter.calls
    p_rejected = _post_sync(counting_schema, "{ branches(OFFSET: -1) { name } }")
    assert p_rejected["errors"][0]["extensions"]["argument"] == "OFFSET"
    assert _CountingConverter.calls - before == per_success


@pytest.mark.django_db
def test_holder_model_default_ordering_verdicts():
    @strawberry.type
    class _GlossaryOrderingQuery:
        terms_default_ordered: list[glossary_schema.GlossaryTermType] = DjangoListField(
            glossary_schema.GlossaryTermType,
        )
        terms_cleared_ordering: list[glossary_schema.GlossaryTermType] = DjangoListField(
            glossary_schema.GlossaryTermType,
            resolver=lambda root, info: glossary_models.GlossaryTerm.objects.all().order_by(),
        )

    schema = DjangoSchema(query=_GlossaryOrderingQuery, config=strawberry_config())
    status = glossary_models.GlossaryStatus.objects.create(key="shipped", label="Shipped")
    glossary_models.GlossaryTerm.objects.create(
        title="Beta",
        title_sort="b",
        anchor="beta",
        status=status,
        status_text="Shipped",
        entry_order=2,
    )
    glossary_models.GlossaryTerm.objects.create(
        title="Alpha",
        title_sort="a",
        anchor="alpha",
        status=status,
        status_text="Shipped",
        entry_order=1,
    )
    glossary_models.GlossaryTerm.objects.create(
        title="Gamma",
        title_sort="g",
        anchor="gamma",
        status=status,
        status_text="Shipped",
        entry_order=3,
    )

    # Model default ordering (entry_order, title_sort) allows offset: 1 with no orderBy
    with CaptureQueriesContext(connection) as ctx:
        payload_ok = _post_sync(
            schema,
            "{ termsDefaultOrdered(offset: 1) { title } }",
        )
    assert "errors" not in payload_ok, payload_ok
    titles = [row["title"] for row in payload_ok["data"]["termsDefaultOrdered"]]
    assert titles == ["Beta", "Gamma"]

    # Verify no injected pk tiebreaker in SQL (only entry_order, title_sort)
    order_sqls = [q["sql"] for q in ctx.captured_queries if "ORDER BY" in q["sql"].upper()]
    assert len(order_sqls) > 0
    assert "id" not in order_sqls[0].lower().split("order by")[-1]

    # Sibling clearing default ordering (.order_by()) flips to order_required
    payload_cleared = _post_sync(
        schema,
        "{ termsClearedOrdering(offset: 1) { title } }",
    )
    assert payload_cleared["errors"][0]["extensions"]["reason"] == "order_required"


@pytest.mark.django_db
def test_holder_target_without_orderset_or_model_ordering():
    @strawberry.type
    class _CardQuery:
        cards: list[library_schema.MembershipCardType] = DjangoListField(
            library_schema.MembershipCardType,
        )

    schema = DjangoSchema(query=_CardQuery, config=strawberry_config())

    # Introspection: offset and limit present, orderBy omitted
    p_intro = _post_sync(
        schema,
        "query { __schema { queryType { fields { args { name } } } } }",
    )
    args = {a["name"] for a in p_intro["data"]["__schema"]["queryType"]["fields"][0]["args"]}
    assert "offset" in args
    assert "limit" in args
    assert "orderBy" not in args

    # Nonzero offset returns order_required
    p_err = _post_sync(schema, "{ cards(offset: 1) { barcode } }")
    assert p_err["errors"][0]["extensions"]["reason"] == "order_required"
    assert "on cards" in p_err["errors"][0]["message"]
    assert "'orderBy'" not in p_err["errors"][0]["message"]


_PARITY_CAPTURE: dict[str, Any] = {}


def _query_marks(queryset: models.QuerySet) -> tuple[str, int, int | None]:
    return str(queryset.query), queryset.query.low_mark, queryset.query.high_mark


def _legacy_reference_resolver(source_factory):
    """The pre-card list pipeline, composed from shipped public primitives only.

    Visibility through ``apply_type_visibility_sync`` and ONE ``bounded_rows`` call
    with no client window - exactly what a no-argument list resolution did before
    the argument surface existed. A test oracle, never a second pagination
    implementation: it records the final queryset's SQL and marks before returning.
    """

    def resolver(root, info: strawberry.Info) -> list[library_schema.BranchType]:
        queryset = apply_type_visibility_sync(library_schema.BranchType, source_factory(), info)
        bounded = bounded_rows(queryset, info, None)
        _PARITY_CAPTURE["legacy_marks"] = _query_marks(bounded)
        return bounded

    return resolver


def _build_current_parity_schema(source_factory) -> DjangoSchema:
    """The card's field, published under the GraphQL name ``branches``."""

    @strawberry.type
    class _CurrentParityQuery:
        branches: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: source_factory(),
        )

    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=_CurrentParityQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _build_legacy_parity_schema(source_factory) -> DjangoSchema:
    """The pre-card reference resolver, published under the SAME GraphQL name.

    Two schemas rather than two fields in one: the response-byte claim is about
    a request envelope that cannot tell the two apart, and a differently named
    field would make the bytes differ for a reason that has nothing to do with
    the pipeline. Both parity schemas carry the optimizer extension the project
    schema carries, because column planning is what the SQL comparison would
    otherwise trip over - and the pre-card pipeline shipped with it too.
    """

    @strawberry.type
    class _LegacyParityQuery:
        branches: list[library_schema.BranchType] = strawberry.field(
            resolver=_legacy_reference_resolver(source_factory),
        )

    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=_LegacyParityQuery,
        config=strawberry_config(),
        extensions=[lambda: optimizer],
    )


def _install_parity_probes(monkeypatch) -> dict[str, int]:
    """Count ``BranchType.get_queryset`` calls and record the current field's final marks."""
    counters = {"visibility": 0}
    original_get_queryset = library_schema.BranchType.get_queryset

    def _tracking_get_queryset(cls, queryset, info, **kwargs):
        counters["visibility"] += 1
        return original_get_queryset(queryset, info, **kwargs)

    monkeypatch.setattr(
        library_schema.BranchType,
        "get_queryset",
        classmethod(_tracking_get_queryset),
    )
    original_bounded_rows = list_field_module.bounded_rows

    def _recording_bounded_rows(result, info, declared=None, **kwargs):
        bounded = original_bounded_rows(result, info, declared, **kwargs)
        _PARITY_CAPTURE["current_marks"] = _query_marks(bounded)
        return bounded

    monkeypatch.setattr(list_field_module, "bounded_rows", _recording_bounded_rows)
    return counters


def _parity_run(
    query: str,
    counters: dict[str, int],
    *,
    schema=None,
    client=None,
    extra_settings: dict[str, Any] | None = None,
):
    """Execute one live request, returning ``(response, branch_sql, visibility_calls)``.

    The raw ``HttpResponse`` is returned, not just its parsed body: the oracle's
    strongest claim is that the response BYTES are unchanged, and parsed
    dictionaries compare equal across renderings that are not.
    """
    counters["visibility"] = 0
    with CaptureQueriesContext(connection) as ctx:
        if schema is None:
            response = post_graphql(query, client=client)
        else:
            response = _post_sync_response(
                schema,
                query,
                client=client,
                extra_settings=extra_settings,
            )
    assert response.status_code == 200
    branch_sql = [q["sql"] for q in ctx.captured_queries if "library_branch" in q["sql"].lower()]
    return response, branch_sql, counters["visibility"]


@pytest.mark.django_db
def test_branches_omitted_and_null_arguments_match_the_legacy_reference(monkeypatch):
    """Omitted and all-null arguments reproduce the PRE-CARD pipeline, not merely each other.

    The oracle is a test-local legacy schema publishing the same ``branches``
    field name, composed from the shipped primitives the old pipeline used, so
    the same request envelope reaches both and the raw response BYTES can be
    compared. The all-null form is compared against the legacy OMITTED response
    because that is precisely the claim: the two spellings are the same request.
    Behind the bytes, ``library_branch`` SQL, the final queryset's
    ``str(query)`` / ``low_mark`` / ``high_mark``, and the visibility-hook count
    must match too. The shipped field publishes its own name, so its rows are
    compared semantically against the same oracle.
    """
    for name in ("Alpha", "Bravo", "Charlie"):
        library_models.Branch.objects.create(name=name, city="Boston")
    library_models.Branch.objects.create(name="Hidden", city="restricted")
    counters = _install_parity_probes(monkeypatch)
    source_factory = library_models.Branch.objects.all
    legacy_schema = _build_legacy_parity_schema(source_factory)
    current_schema = _build_current_parity_schema(source_factory)

    omitted = "{ branches { id name } }"
    all_null = "{ branches(offset: null, limit: null, orderBy: null) { id name } }"

    legacy_response, legacy_sql, legacy_visibility = _parity_run(
        omitted,
        counters,
        schema=legacy_schema,
    )
    legacy = legacy_response.json()
    assert "errors" not in legacy, legacy
    legacy_rows = legacy["data"]["branches"]
    assert [row["name"] for row in legacy_rows] == ["Alpha", "Bravo", "Charlie"]
    assert len(legacy_sql) == 1
    assert legacy_visibility == 1
    legacy_marks = _PARITY_CAPTURE["legacy_marks"]
    assert legacy_marks[1] == 0
    assert legacy_marks[2] is not None

    # The two envelopes the card promises are unchanged, byte for byte.
    for label, query in (("omitted", omitted), ("all-null", all_null)):
        _PARITY_CAPTURE.pop("current_marks", None)
        response, sql, visibility = _parity_run(query, counters, schema=current_schema)
        assert response.content == legacy_response.content, label
        assert sql == legacy_sql, label
        assert visibility == legacy_visibility, label
        assert _PARITY_CAPTURE["current_marks"] == legacy_marks, label

    # The shipped field publishes its own name, so its rows are compared to the
    # same oracle semantically; the pipeline claims are identical.
    shipped_queries = {
        "shipped omitted": "{ allLibraryBranchesViaListField { id name } }",
        "shipped all-null": (
            "{ allLibraryBranchesViaListField(offset: null, limit: null, orderBy: null) "
            "{ id name } }"
        ),
    }
    for label, query in shipped_queries.items():
        _PARITY_CAPTURE.pop("current_marks", None)
        response, sql, visibility = _parity_run(query, counters)
        payload = response.json()
        assert "errors" not in payload, (label, payload)
        assert payload["data"]["allLibraryBranchesViaListField"] == legacy_rows, label
        assert sql == legacy_sql, label
        assert visibility == legacy_visibility, label
        assert _PARITY_CAPTURE["current_marks"] == legacy_marks, label


@pytest.mark.django_db
def test_holder_branches_combined_legacy_branch_matches_the_legacy_reference(monkeypatch):
    """The combined-source legacy branch is held to the pre-card oracle, not to "no new error".

    A union source under omitted / all-null arguments takes the legacy policy path,
    which is exactly where argument mode diverges (any non-null argument rejects at
    the source seal). Both schemas publish the same ``branches`` field name over the
    same source factory, so the oracle is the legacy response's RAW BYTES - whatever
    the pre-card composition produces, rows or a pre-existing error, with its
    envelope ordering, locations, path and extensions intact - plus its
    ``library_branch`` SQL, final marks, and visibility-hook count. A semantic
    projection would pass while the envelope drifted. The staff client bypasses ``BranchType.get_queryset``'s
    ``exclude`` so the combined queryset is not refused by Django before the seal.
    """
    client = _staff_client()
    library_models.Branch.objects.create(name="A", city="Boston")
    library_models.Branch.objects.create(name="B", city="Boston")
    counters = _install_parity_probes(monkeypatch)

    def _combined_source():
        return library_models.Branch.objects.filter(name="A").union(
            library_models.Branch.objects.filter(name="B"),
        )

    legacy_schema = _build_legacy_parity_schema(_combined_source)
    current_schema = _build_current_parity_schema(_combined_source)

    legacy_response, legacy_sql, legacy_visibility = _parity_run(
        "{ branches { name } }",
        counters,
        schema=legacy_schema,
        client=client,
        extra_settings=_ERROR_POLICY_PASS_THROUGH,
    )
    legacy_payload = legacy_response.json()
    assert legacy_visibility == 1
    legacy_marks = _PARITY_CAPTURE["legacy_marks"]
    assert "UNION" in legacy_marks[0].upper()
    if "errors" not in legacy_payload:
        assert sorted(row["name"] for row in legacy_payload["data"]["branches"]) == ["A", "B"]
        assert len(legacy_sql) == 1

    for query in ("{ branches { name } }", "{ branches(offset: null, limit: null) { name } }"):
        _PARITY_CAPTURE.pop("current_marks", None)
        response, sql, visibility = _parity_run(
            query,
            counters,
            schema=current_schema,
            client=client,
            extra_settings=_ERROR_POLICY_PASS_THROUGH,
        )
        assert response.content == legacy_response.content, query
        assert sql == legacy_sql
        assert visibility == legacy_visibility
        assert _PARITY_CAPTURE["current_marks"] == legacy_marks

    # Argument mode is where the two branches part: any non-null argument rejects the
    # combined source at the seal before visibility runs.
    counters["visibility"] = 0
    p_active = _post_sync(
        current_schema,
        "{ branches(limit: 1) { name } }",
        client=client,
        extra_settings=_ERROR_POLICY_PASS_THROUGH,
    )
    assert p_active["data"] is None
    assert "combined" in p_active["errors"][0]["message"].lower()
    assert counters["visibility"] == 0


# ---------------------------------------------------------------------------
# 21-25. Offset alone, aliases, nullability, subclass, context isolation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_shipped_branches_offset_alone_bounds():
    client = _staff_client()
    for i in range(5):
        library_models.Branch.objects.create(name=f"Branch {i}", city="Boston")

    query = """
    query {
      allLibraryBranchesViaListField(
        orderBy: [{ name: ASC }]
        offset: 2
      ) {
        name
      }
    }
    """
    with CaptureQueriesContext(connection) as ctx:
        payload = graphql_payload(query, client=client)
    assert "errors" not in payload, payload
    assert len(payload["data"]["allLibraryBranchesViaListField"]) == 3

    # Low mark 2, high mark 102 in SQL (slice [2:102] -> LIMIT 100 OFFSET 2)
    sql_candidates = [
        q["sql"]
        for q in ctx.captured_queries
        if "library_branch" in q["sql"].lower() and "limit" in q["sql"].lower()
    ]
    assert len(sql_candidates) > 0
    sql = sql_candidates[0].upper()
    assert "OFFSET 2" in sql
    assert "LIMIT 100" in sql


@pytest.mark.django_db
def test_shipped_branches_independent_aliases():
    client = _staff_client()
    library_models.Branch.objects.create(name="Alpha", city="Boston")
    library_models.Branch.objects.create(name="Bravo", city="Boston")
    library_models.Branch.objects.create(name="Charlie", city="Boston")

    query = """
    query {
      p1: allLibraryBranchesViaListField(
        orderBy: [{ name: ASC }]
        offset: 0
        limit: 1
      ) {
        name
      }
      p2: allLibraryBranchesViaListField(
        orderBy: [{ name: ASC }]
        offset: 1
        limit: 1
      ) {
        name
      }
    }
    """
    payload = graphql_payload(query, client=client)
    assert "errors" not in payload, payload
    assert payload["data"]["p1"] == [{"name": "Alpha"}]
    assert payload["data"]["p2"] == [{"name": "Bravo"}]


@pytest.mark.django_db
def test_holder_nullability_propagation_over_none_source():
    @strawberry.type
    class _NullabilityQuery:
        nullable_none: list[library_schema.BranchType] | None = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: None,
        )
        non_null_none: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: None,
        )

    schema = DjangoSchema(query=_NullabilityQuery, config=strawberry_config())

    # limit-only request preserves nullability
    p_null = _post_sync(schema, "{ nullableNone(limit: 1) { name } }")
    assert "errors" not in p_null, p_null
    assert p_null["data"]["nullableNone"] is None

    # rejected argument rejects before resolving
    p_null_err = _post_sync(schema, "{ nullableNone(offset: -1) { name } }")
    assert p_null_err["errors"][0]["extensions"]["reason"] == "negative"

    p_non_err = _post_sync(schema, "{ nonNullNone(offset: -1) { name } }")
    assert p_non_err["errors"][0]["extensions"]["reason"] == "negative"


@pytest.mark.django_db
def test_holder_orderset_override_returning_queryset_subclass(monkeypatch):
    client = _staff_client()
    library_models.Branch.objects.create(name="Alpha", city="Boston")
    library_models.Branch.objects.create(name="Bravo", city="Boston")

    class _CustomBranchQuerySet(models.QuerySet):
        pass

    orig_apply_sync = BranchOrder.apply_sync

    def _subclass_apply_sync(
        cls,
        order_input,
        queryset,
        info,
    ):
        ordered = orig_apply_sync(order_input, queryset, info)
        return _CustomBranchQuerySet(
            model=ordered.model,
            query=ordered.query.clone(),
            using=ordered._db,
        )

    monkeypatch.setattr(BranchOrder, "apply_sync", classmethod(_subclass_apply_sync))

    query = """
    query {
      allLibraryBranchesViaListField(
        orderBy: [{ name: ASC }]
        offset: 1
        limit: 1
      ) {
        name
      }
    }
    """
    payload = graphql_payload(query, client=client)
    assert "errors" not in payload, payload
    assert payload["data"]["allLibraryBranchesViaListField"] == [{"name": "Bravo"}]


# ---------------------------------------------------------------------------
# 26. Ordering never writes the consumer context
# ---------------------------------------------------------------------------

_CONTEXT_CAPTURE: dict[str, Any] = {}


class _CapturingContextView(DjangoGraphQLView):
    """Pre-populates a consumer attribute on the context and hands the object to the test."""

    def get_context(self, request, response):
        context = super().get_context(request, response)
        context.consumer_marker = _CONTEXT_CAPTURE["marker"]
        _CONTEXT_CAPTURE["context"] = context
        return context


class _FrozenContext:
    """A context that refuses every attribute write or delete after construction."""

    def __init__(self, request, response):
        object.__setattr__(self, "request", request)
        object.__setattr__(self, "response", response)

    def __setattr__(self, name, value):
        raise AttributeError(f"frozen context refuses write to {name!r}")

    def __delattr__(self, name):
        raise AttributeError(f"frozen context refuses delete of {name!r}")


class _FrozenContextView(DjangoGraphQLView):
    def get_context(self, request, response):
        return _FrozenContext(request, response)


def _build_context_schema() -> DjangoSchema:
    @strawberry.type
    class _ContextQuery:
        branches: list[library_schema.BranchType] = DjangoListField(library_schema.BranchType)
        genres: DjangoConnection[library_schema.GenreType] = DjangoConnectionField(
            library_schema.GenreType,
        )

    return DjangoSchema(query=_ContextQuery, config=strawberry_config())


_ORDERED_CONTEXT_REQUESTS: tuple[tuple[str, str], ...] = (
    # (control without ordering, the same field with public ordering applied)
    (
        "{ branches(limit: 1) { name } }",
        "{ branches(orderBy: [{ city: ASC }], offset: 1, limit: 1) { name } }",
    ),
    (
        "{ genres { edges { node { name } } } }",
        "{ genres(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
    ),
)


@pytest.mark.django_db
def test_holder_ordering_leaves_the_consumer_context_exactly_as_found():
    """An ordered list or connection adds nothing to ``info.context`` a control request does not.

    The order-normalization handoff is task-local, so the context object holds the
    same attribute set after an ordered request as after the same field without
    ordering, and a consumer attribute set before execution survives by identity.
    """
    client = _staff_client()
    for name in ("Alpha", "Bravo"):
        library_models.Branch.objects.create(name=name, city="Boston")
    library_models.Genre.objects.create(name="Fiction")
    schema = _build_context_schema()

    for control_query, ordered_query in _ORDERED_CONTEXT_REQUESTS:
        observed: dict[str, Any] = {}
        for label, query in (("control", control_query), ("ordered", ordered_query)):
            marker = object()
            _CONTEXT_CAPTURE.clear()
            _CONTEXT_CAPTURE["marker"] = marker
            payload = _post_sync(schema, query, client=client, view_class=_CapturingContextView)
            assert "errors" not in payload, (label, payload)
            context = _CONTEXT_CAPTURE["context"]
            assert context.consumer_marker is marker
            observed[label] = set(vars(context))
        assert observed["ordered"] == observed["control"], observed


@pytest.mark.django_db
def test_holder_ordering_succeeds_on_a_context_that_forbids_writes():
    """A context refusing every write still serves ordered lists and connections.

    Nothing in public ordering, the offset guard, or the post-order seal asks the
    consumer context to accept a value or to give one up.
    """
    client = _staff_client()
    for name in ("Alpha", "Bravo"):
        library_models.Branch.objects.create(name=name, city="Boston")
    library_models.Genre.objects.create(name="Fiction")
    schema = _build_context_schema()

    for _control_query, ordered_query in _ORDERED_CONTEXT_REQUESTS:
        payload = _post_sync(schema, ordered_query, client=client, view_class=_FrozenContextView)
        assert "errors" not in payload, payload
    p_list = _post_sync(
        schema,
        "{ branches(orderBy: [{ name: ASC }], offset: 1, limit: 1) { name } }",
        client=client,
        view_class=_FrozenContextView,
    )
    assert p_list["data"]["branches"] == [{"name": "Bravo"}]
