"""Live sync-HTTP contract for ``DjangoListField`` arguments (spec-050 Slice 4).

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
from graphql_client import graphql_payload
from strawberry.schema.name_converter import NameConverter

from django_strawberry_framework import (
    DjangoListField,
    strawberry_config,
)
from django_strawberry_framework.schema import DjangoSchema
from django_strawberry_framework.views import DjangoGraphQLView

_ERROR_POLICY_PASS_THROUGH = {
    "DEBUG": True,
    "MIDDLEWARE": [entry for entry in settings.MIDDLEWARE if "debug_toolbar" not in entry],
}

_CURRENT: dict[str, object | None] = {"schema": None}


def _graphql_view(request):
    schema = _CURRENT["schema"]
    assert schema is not None
    return DjangoGraphQLView.as_view(schema=schema)(request)


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


def _post_sync(
    schema: DjangoSchema | strawberry.Schema,
    query: str,
    *,
    variables: dict[str, Any] | None = None,
    client: Client | None = None,
    extra_settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _CURRENT["schema"] = schema
    override_dict: dict[str, Any] = {"ROOT_URLCONF": __name__}
    if extra_settings:
        override_dict.update(extra_settings)
    try:
        with override_settings(**override_dict):
            clear_url_caches()
            return graphql_payload(
                query,
                client=client,
                variables=variables,
                url="/graphql-test/",
            )
    finally:
        _CURRENT["schema"] = None
        clear_url_caches()


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

    # Non-null list return type: NON_NULL -> LIST -> NON_NULL -> BranchType
    ret_default = fields["allLibraryBranchesViaListField"]["type"]
    assert ret_default["kind"] == "NON_NULL"
    assert ret_default["ofType"]["kind"] == "LIST"

    # Nullable list return type: LIST -> NON_NULL -> BranchType
    ret_nullable = fields["allLibraryBranchesViaListFieldNullable"]["type"]
    assert ret_nullable["kind"] == "LIST"
    assert ret_nullable["ofType"]["kind"] == "NON_NULL"


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
    assert "on branches_materialized" in p_mat_ord["errors"][0]["message"]

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
    # Post-orderset validation rejects with ConfigurationError
    assert "errors" in p_hook
    assert p_hook["data"] is None
    assert "combined" in p_hook["errors"][0]["message"].lower()


@pytest.mark.django_db
def test_holder_branches_post_orderset_evaluated_projection_and_wrong_model(monkeypatch):
    library_models.Branch.objects.create(name="A", city="Boston")

    # 1. Evaluated return (list instead of QuerySet)
    monkeypatch.setattr(
        BranchOrder,
        "apply_sync",
        classmethod(lambda cls, order_input, queryset, info: list(queryset)),
    )
    with override_settings(**_ERROR_POLICY_PASS_THROUGH):
        p_eval = graphql_payload(
            "{ allLibraryBranchesViaListField(orderBy: [{ city: ASC }]) { name } }",
        )
    assert "errors" in p_eval
    assert p_eval["data"] is None
    assert "must return an unevaluated" in p_eval["errors"][0]["message"]

    # 2. Projection return (values instead of model instances)
    monkeypatch.setattr(
        BranchOrder,
        "apply_sync",
        classmethod(lambda cls, order_input, queryset, info: queryset.values("name")),
    )
    with override_settings(**_ERROR_POLICY_PASS_THROUGH):
        p_proj = graphql_payload(
            "{ allLibraryBranchesViaListField(orderBy: [{ city: ASC }]) { name } }",
        )
    assert "errors" in p_proj
    assert p_proj["data"] is None
    assert "projection defect" in p_proj["errors"][0]["message"]

    # 3. Wrong-model return (Book queryset instead of Branch)
    monkeypatch.setattr(
        BranchOrder,
        "apply_sync",
        classmethod(
            lambda cls, order_input, queryset, info: library_models.Book.objects.all(),
        ),
    )
    with override_settings(**_ERROR_POLICY_PASS_THROUGH):
        p_model = graphql_payload(
            "{ allLibraryBranchesViaListField(orderBy: [{ city: ASC }]) { name } }",
        )
    assert "errors" in p_model
    assert p_model["data"] is None
    assert "table defect" in p_model["errors"][0]["message"]


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


@pytest.mark.django_db
def test_shipped_branches_omitted_and_null_argument_sql_parity():
    library_models.Branch.objects.create(name="Alpha", city="Boston")
    library_models.Branch.objects.create(name="Bravo", city="Boston")
    library_models.Branch.objects.create(name="Charlie", city="Boston")

    with CaptureQueriesContext(connection) as omitted_ctx:
        omitted = graphql_payload("{ allLibraryBranchesViaListField { id name } }")
    with CaptureQueriesContext(connection) as null_ctx:
        explicit_null = graphql_payload(
            """
            query {
              allLibraryBranchesViaListField(
                offset: null
                limit: null
                orderBy: null
              ) {
                id
                name
              }
            }
            """,
        )

    assert "errors" not in omitted, omitted
    assert "errors" not in explicit_null, explicit_null
    omitted_sql = [
        query["sql"]
        for query in omitted_ctx.captured_queries
        if "library_branch" in query["sql"].lower()
    ]
    null_sql = [
        query["sql"]
        for query in null_ctx.captured_queries
        if "library_branch" in query["sql"].lower()
    ]
    assert len(omitted_sql) == 1
    assert omitted_sql == null_sql
    assert omitted["data"] == explicit_null["data"]


# ---------------------------------------------------------------------------
# 21-25. Offset alone, legacy baseline, aliases, nullability, subclass
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


def _baseline_branches_combined_legacy(
    schema: DjangoSchema,
    client: Client | None = None,
) -> tuple[dict, int]:
    """Execute raw omitted-argument query against combined schema and return payload + query count."""
    with CaptureQueriesContext(connection) as ctx:
        res = _post_sync(schema, "{ branchesCombined { name } }", client=client)
    return res, len(ctx.captured_queries)


@pytest.mark.django_db
def test_holder_branches_combined_legacy_baseline():
    client = _staff_client()
    library_models.Branch.objects.create(name="A", city="Boston")
    library_models.Branch.objects.create(name="B", city="Boston")

    @strawberry.type
    class _CombinedQuery:
        branches_combined: list[library_schema.BranchType] = DjangoListField(
            library_schema.BranchType,
            resolver=lambda root, info: library_models.Branch.objects.filter(name="A").union(
                library_models.Branch.objects.filter(name="B"),
            ),
        )

    schema = DjangoSchema(query=_CombinedQuery, config=strawberry_config())

    baseline_payload, baseline_queries = _baseline_branches_combined_legacy(schema, client=client)

    # All-null explicit argument request
    with CaptureQueriesContext(connection) as ctx:
        null_payload = _post_sync(
            schema,
            "{ branchesCombined(offset: null, limit: null) { name } }",
            client=client,
        )
    assert null_payload == baseline_payload
    assert len(ctx.captured_queries) == baseline_queries


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
