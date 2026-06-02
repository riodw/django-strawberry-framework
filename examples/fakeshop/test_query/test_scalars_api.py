"""Live GraphQL HTTP tests for the scalar conversion coverage app.

Each test pins the wire format of one entry in
``django_strawberry_framework/types/converters.py::SCALAR_MAP`` against a
real ``/graphql/`` round-trip. ``BigInt`` (signed and unsigned variants) is
exercised with values past the JS safe-integer boundary (``2**53 - 1 ==
9007199254740991``) so the decimal-string serialization is genuinely
verified, not accidentally satisfied by an in-range value that would also
round-trip as a JSON number.
"""

import datetime
import importlib
import sys
from decimal import Decimal
from uuid import UUID

import pytest
from apps.scalars import models
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches

from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests():
    """Recreate imported DjangoType classes if package tests cleared the registry.

    Mirrors the ``test_library_api.py`` fixture: package tests clear the
    global registry, while the example schema finalizes import-time
    ``DjangoType`` classes. Reload only schema modules (not
    ``apps.scalars.models``) so Django model classes stay stable.
    """
    registry.clear()
    scalars_schema = sys.modules.get("apps.scalars.schema")
    if scalars_schema is None:
        importlib.import_module("apps.scalars.schema")
    else:
        importlib.reload(scalars_schema)

    project_schema = sys.modules.get("config.schema")
    if project_schema is None:
        importlib.import_module("config.schema")
    else:
        importlib.reload(project_schema)

    urls = sys.modules.get("config.urls")
    if urls is not None:
        importlib.reload(urls)
        clear_url_caches()


# Sentinel values chosen so each wire format is unambiguous in the response.
# BigInt boundary values intentionally exceed ``2**53 - 1`` so the
# decimal-string serialization is the only way the value can survive a
# JSON round-trip without precision loss.
_SIGNED_BIG = 9223372036854775000  # below 2**63 - 1, comfortably past 2**53
_UNSIGNED_BIG = 9223372036854775001
_UUID_VALUE = UUID("12345678-1234-5678-1234-567812345678")
_DATE_VALUE = datetime.date(2026, 5, 27)
_TIME_VALUE = datetime.time(12, 34, 56)
_DATETIME_VALUE = datetime.datetime(2026, 5, 27, 12, 34, 56, tzinfo=datetime.timezone.utc)
_DECIMAL_VALUE = Decimal("12345.6789")
# Mixed-primitive payload: top-level string, int, list of ints, JSON ``null``
# (key present, value is ``None``), and a nested dict carrying a bool. Pins
# the round-trip shape that the migrated package test
# ``test_json_field_round_trips_dict_via_schema_execution`` formerly covered
# with ``{"k1": "v1", "k2": 2, "k3": [1, 2, 3], "k4": None}`` — the
# JSON-internal-``null`` case is the unique one (distinct from the column
# itself being NULL, which is exercised by
# ``test_nullable_scalar_specimen_all_null_wire_format_over_http``).
_JSON_PAYLOAD = {
    "label": "demo",
    "count": 2,
    "items": [1, 2, 3],
    "absent": None,
    "nested": {"flag": True},
}


def _seed_specimen(**overrides):
    defaults = {
        "label": "demo",
        "flag": True,
        "score": 1.5,
        "price": _DECIMAL_VALUE,
        "occurred_on": _DATE_VALUE,
        "occurred_at": _DATETIME_VALUE,
        "occurred_time": _TIME_VALUE,
        "payload": _JSON_PAYLOAD,
        "external_id": _UUID_VALUE,
        "signed_big": _SIGNED_BIG,
        "unsigned_big": _UNSIGNED_BIG,
    }
    defaults.update(overrides)
    return models.ScalarSpecimen.objects.create(**defaults)


def _seed_nullable_specimen(**overrides):
    """Seed a ``NullableScalarSpecimen`` with every field defaulting to ``None``.

    Pass field values explicitly via ``**overrides`` when a test needs a non-
    null value; the bare ``_seed_nullable_specimen()`` exercise the all-null
    wire format.
    """
    return models.NullableScalarSpecimen.objects.create(**overrides)


def _seed_tag(label: str, *, active: bool = True):
    """Seed a ``ScalarSpecimenTag`` with the given label and active flag."""
    return models.ScalarSpecimenTag.objects.create(label=label, active=active)


def _post_graphql(query: str):
    client = Client()
    return client.post(
        "/graphql/",
        data={"query": query},
        content_type="application/json",
    )


def _query_one_specimen() -> dict:
    response = _post_graphql(
        """
        query {
          allScalarSpecimens {
            label
            flag
            score
            price
            occurredOn
            occurredAt
            occurredTime
            payload
            externalId
            signedBig
            unsignedBig
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    rows = body["data"]["allScalarSpecimens"]
    assert len(rows) == 1, rows
    return rows[0]


@pytest.mark.django_db
def test_scalar_specimen_every_field_wire_format_over_http():
    _seed_specimen()
    row = _query_one_specimen()

    # ``str`` collapses (label) — sanity anchor.
    assert row["label"] == "demo"
    # ``bool`` — JSON boolean.
    assert row["flag"] is True
    # ``float`` — JSON number.
    assert row["score"] == 1.5
    # ``Decimal`` — Strawberry serializes as string.
    assert row["price"] == "12345.6789"
    # ``date`` — ISO 8601 date.
    assert row["occurredOn"] == "2026-05-27"
    # ``datetime`` — ISO 8601 with UTC offset.
    assert row["occurredAt"] == "2026-05-27T12:34:56+00:00"
    # ``time`` — ISO 8601 time.
    assert row["occurredTime"] == "12:34:56"
    # ``JSON`` — passes through verbatim.
    assert row["payload"] == _JSON_PAYLOAD
    # ``UUID`` — string form.
    assert row["externalId"] == "12345678-1234-5678-1234-567812345678"
    # ``BigInt`` — decimal-string serialization, signed variant.
    assert row["signedBig"] == "9223372036854775000"
    # ``BigInt`` — decimal-string serialization, unsigned variant.
    assert row["unsignedBig"] == "9223372036854775001"


@pytest.mark.django_db
def test_scalar_specimen_bigint_negative_signed_round_trip():
    """Signed ``BigInt`` survives a negative value past the JS safe-integer floor."""
    _seed_specimen(label="negative", signed_big=-_SIGNED_BIG)
    row = _query_one_specimen()
    assert row["signedBig"] == "-9223372036854775000"


@pytest.mark.django_db
def test_scalar_specimen_bigint_zero_serializes_as_string():
    """Edge case: zero still serializes as the string ``"0"`` (not a JSON number)."""
    _seed_specimen(label="zero", signed_big=0, unsigned_big=0)
    row = _query_one_specimen()
    assert row["signedBig"] == "0"
    assert row["unsignedBig"] == "0"


@pytest.mark.django_db
def test_filter_specimens_by_bigint_in_accepts_64bit_values():
    """Spec-021 H2: a ``BigIntegerField`` ``in`` lookup uses the ``BigInt`` scalar.

    Regression for the generated CSV (``BaseInFilter``) element collapsing to
    ``Int`` (32-bit), which rejected the 64-bit values a ``BigIntegerField``
    holds. The element type now mirrors ``SCALAR_MAP`` (``BigIntegerField`` ->
    ``BigInt``), so a value past 2**31 coerces instead of erroring.
    """
    _seed_specimen(label="big", signed_big=_SIGNED_BIG)
    _seed_specimen(label="small", signed_big=1)
    response = _post_graphql(
        f"""
        query {{
          allScalarSpecimens(filter: {{ signedBig: {{ in: [{_SIGNED_BIG}] }} }}) {{
            label
          }}
        }}
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    assert body["data"]["allScalarSpecimens"] == [{"label": "big"}]


@pytest.mark.django_db
def test_scalar_specimen_self_referential_parent_children_over_http():
    """Self-FK round-trip: parent + reverse-FK ``children`` traversal both work.

    Seeds a three-level chain (root -> middle -> leaf) and queries the full
    tree in one request. Exercises ``select_related("parent")`` (forward FK
    to the same model) and ``prefetch_related("children")`` (reverse FK on
    the same model) under the optimizer extension.
    """
    root = _seed_specimen(label="root")
    middle = _seed_specimen(label="middle", parent=root)
    _seed_specimen(label="leaf", parent=middle)

    response = _post_graphql(
        """
        query {
          allScalarSpecimens {
            label
            parent { label }
            children { label }
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    rows = {row["label"]: row for row in body["data"]["allScalarSpecimens"]}

    assert rows["root"]["parent"] is None
    assert [child["label"] for child in rows["root"]["children"]] == ["middle"]

    assert rows["middle"]["parent"] == {"label": "root"}
    assert [child["label"] for child in rows["middle"]["children"]] == ["leaf"]

    assert rows["leaf"]["parent"] == {"label": "middle"}
    assert rows["leaf"]["children"] == []


def _introspect_field_types(type_name: str) -> dict:
    """Fetch the field-type map for ``type_name`` via live ``/graphql/`` introspection."""
    response = _post_graphql(
        f"""
        query {{
          __type(name: "{type_name}") {{
            fields {{
              name
              type {{ name kind ofType {{ name kind }} }}
            }}
          }}
        }}
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    return {field["name"]: field["type"] for field in body["data"]["__type"]["fields"]}


@pytest.mark.django_db
def test_scalar_specimen_introspects_bigint_scalar_for_both_fields():
    """Both halves of the ``BigInt`` converter table entry — signed and unsigned —
    introspect correctly in both shapes (``NON_NULL`` and nullable ``SCALAR``).

    Migrated from these tests in ``tests/types/test_converters.py``:
    - ``test_big_integer_field_maps_to_bigint_in_schema`` (non-null signed)
    - ``test_big_integer_field_nullable_in_schema`` (nullable signed)
    - ``test_positive_big_integer_field_maps_to_bigint_in_schema`` (non-null unsigned)

    All three synthetic ``managed=False`` owner models are superseded by the
    real ``ScalarSpecimen`` / ``NullableScalarSpecimen`` pair.
    """
    required_fields = _introspect_field_types("ScalarSpecimenType")
    nullable_fields = _introspect_field_types("NullableScalarSpecimenType")

    # ``ScalarSpecimen`` declares ``signed_big`` / ``unsigned_big`` without
    # ``null=True``, so introspection must report ``NON_NULL`` wrapping the
    # ``BigInt`` ``SCALAR``.
    for field_name in ("signedBig", "unsignedBig"):
        field_type = required_fields[field_name]
        assert field_type["kind"] == "NON_NULL", field_name
        assert field_type["ofType"] == {"name": "BigInt", "kind": "SCALAR"}, field_name

    # ``NullableScalarSpecimen`` declares the same fields with ``null=True``,
    # so introspection must report a bare ``SCALAR`` (no ``NON_NULL`` wrapper).
    for field_name in ("signedBig", "unsignedBig"):
        field_type = nullable_fields[field_name]
        assert field_type == {"name": "BigInt", "kind": "SCALAR", "ofType": None}, field_name


@pytest.mark.django_db
def test_scalar_specimen_introspects_json_scalar_in_both_shapes():
    """``payload`` introspects as ``JSON`` in both non-null and nullable shapes.

    Pins the ``JSONField -> strawberry.scalars.JSON`` converter table entry at
    the GraphQL introspection layer over a live ``/graphql/`` request.
    Migrated from ``tests/types/test_converters.py::test_json_field_maps_to_json_scalar_in_schema``
    (and supersedes the sibling ``test_json_field_nullable_in_schema``).
    """
    required_fields = _introspect_field_types("ScalarSpecimenType")
    nullable_fields = _introspect_field_types("NullableScalarSpecimenType")

    # ``ScalarSpecimen.payload`` has no ``null=True`` (the model uses
    # ``default=dict`` to make it implicitly required), so introspection must
    # report ``NON_NULL`` wrapping the ``JSON`` ``SCALAR``.
    payload_type = required_fields["payload"]
    assert payload_type["kind"] == "NON_NULL"
    assert payload_type["ofType"] == {"name": "JSON", "kind": "SCALAR"}

    # ``NullableScalarSpecimen.payload`` has ``null=True``, so introspection
    # reports a bare ``SCALAR`` (no ``NON_NULL`` wrapper).
    nullable_payload_type = nullable_fields["payload"]
    assert nullable_payload_type == {"name": "JSON", "kind": "SCALAR", "ofType": None}


@pytest.mark.django_db
def test_nullable_scalar_specimen_all_null_wire_format_over_http():
    """Every nullable scalar serializes as JSON ``null`` when the column is NULL.

    Pins the nullable-branch wire format for every entry in
    ``django_strawberry_framework/types/converters.py::SCALAR_MAP`` —
    ``BooleanField``, ``FloatField``, ``DecimalField``, ``DateField``,
    ``DateTimeField``, ``TimeField``, ``JSONField``, ``UUIDField``,
    ``BigIntegerField``, ``PositiveBigIntegerField`` — over a live
    ``/graphql/`` request. Counterpart to
    ``test_scalar_specimen_every_field_wire_format_over_http`` which pins the
    non-null branch.
    """
    _seed_nullable_specimen(label="empty")

    response = _post_graphql(
        """
        query {
          allNullableScalarSpecimens {
            label
            flag
            score
            price
            occurredOn
            occurredAt
            occurredTime
            payload
            externalId
            signedBig
            unsignedBig
            partner { label }
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    rows = body["data"]["allNullableScalarSpecimens"]
    assert len(rows) == 1
    row = rows[0]

    assert row["label"] == "empty"  # the one non-null field we set
    for field_name in (
        "flag",
        "score",
        "price",
        "occurredOn",
        "occurredAt",
        "occurredTime",
        "payload",
        "externalId",
        "signedBig",
        "unsignedBig",
        "partner",
    ):
        assert row[field_name] is None, field_name


@pytest.mark.django_db
def test_nullable_scalar_specimen_partner_fk_linkage_over_http():
    """Cross-model FK round-trip: ``NullableScalarSpecimen.partner -> ScalarSpecimen``.

    Exercises forward-FK selection across a model boundary inside the same
    app — distinct from the intra-model ``parent`` self-FK on ``ScalarSpecimen``.
    Asserts the nullable forward FK populates correctly when a target exists.
    """
    target = _seed_specimen(label="target", signed_big=42, unsigned_big=42)
    _seed_nullable_specimen(label="linked", partner=target, signed_big=_SIGNED_BIG)

    response = _post_graphql(
        """
        query {
          allNullableScalarSpecimens {
            label
            signedBig
            partner { label signedBig }
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    rows = body["data"]["allNullableScalarSpecimens"]
    assert len(rows) == 1
    assert rows[0] == {
        "label": "linked",
        "signedBig": "9223372036854775000",
        "partner": {"label": "target", "signedBig": "42"},
    }


@pytest.mark.django_db
def test_scalar_specimen_nullable_partners_reverse_relation_over_http():
    """Reverse-FK exposure: ``ScalarSpecimen.nullable_partners``.

    Two ``NullableScalarSpecimen`` rows point at the same ``ScalarSpecimen``;
    the reverse relation should list both via the ``nullablePartners`` field.
    Distinct from ``children`` (self-FK reverse) on the same type and from
    every reverse-FK in the library app (which crosses model boundaries
    between domain entities, not between paired all-required/all-nullable
    mirrors).
    """
    hub = _seed_specimen(label="hub")
    _seed_nullable_specimen(label="spoke_a", partner=hub)
    _seed_nullable_specimen(label="spoke_b", partner=hub)
    _seed_nullable_specimen(label="detached")  # no partner

    response = _post_graphql(
        """
        query {
          allScalarSpecimens {
            label
            nullablePartners { label }
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    rows = {row["label"]: row for row in body["data"]["allScalarSpecimens"]}
    spoke_labels = sorted(p["label"] for p in rows["hub"]["nullablePartners"])
    assert spoke_labels == ["spoke_a", "spoke_b"]


@pytest.mark.django_db
def test_scalars_set_null_ondelete_detaches_partner_in_http_query():
    """Deleting the partner target detaches the source row via ``on_delete=SET_NULL``.

    Pins the only ``SET_NULL`` ondelete in the example tree (the
    ``NullableScalarSpecimen.partner`` FK) end-to-end. The
    setup-trigger-observe shape uses live ``/graphql/`` requests for the
    consumer-visible halves (BEFORE the delete and AFTER) and a plain
    ORM ``target.delete()`` call for the trigger — same pattern every
    seed call uses, just on the other end of the row lifecycle.

    Asserts three things the post-delete query must prove:
    1. ``partner`` resolves to ``None`` after the cascade (the optimizer's
       prefetched row reflects post-delete state — no stale cache, no
       orphaned FK-id stub).
    2. The source ``NullableScalarSpecimen`` row itself survives (cascade
       is ``SET_NULL``, not ``CASCADE``).
    3. ``partner_id`` is cleared at the column level (``SET_NULL``
       actually nulled the FK column, not just hid the relation from
       GraphQL).
    """
    target = _seed_specimen(label="target")
    nullable = _seed_nullable_specimen(label="linked", partner=target)

    # BEFORE — the link is live.
    response = _post_graphql(
        """
        query {
          allNullableScalarSpecimens {
            label
            partner { label }
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    assert body["data"]["allNullableScalarSpecimens"] == [
        {"label": "linked", "partner": {"label": "target"}},
    ]

    # TRIGGER — delete the partner target via ORM (mutations aren't in the
    # example schema yet; deletion goes through the same path every seed
    # uses, just in reverse).
    target.delete()

    # AFTER — SET_NULL fired, the link is gone, but the source row survives.
    response = _post_graphql(
        """
        query {
          allNullableScalarSpecimens {
            label
            partner { label }
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    assert body["data"]["allNullableScalarSpecimens"] == [
        {"label": "linked", "partner": None},
    ]

    # Sanity — the source row survived and the FK column was cleared
    # (not the relation hidden from GraphQL — actually nulled at the DB
    # level).
    nullable.refresh_from_db()
    assert nullable.pk is not None
    assert nullable.partner_id is None


@pytest.mark.django_db
def test_scalar_specimen_bigint_input_decimal_string_argument_over_http():
    """A ``BigInt!`` argument provided as a decimal-string literal parses correctly.

    Pins ``BigInt.parse_value``'s decimal-string acceptance end-to-end:
    the consumer passes ``signedBig: "9223372036854775000"`` (string form,
    safe for values past the JS safe-integer boundary) and the resolver
    must receive ``9223372036854775000`` as an int so the ORM lookup finds
    the seeded row. Migrated from
    ``tests/types/test_converters.py::test_bigint_parses_string_argument_via_schema_execution``.
    """
    target = _seed_specimen(label="target", signed_big=_SIGNED_BIG)
    _seed_specimen(label="other", signed_big=42)

    response = _post_graphql(
        """
        query {
          scalarSpecimenBySignedBig(signedBig: "9223372036854775000") {
            label
            signedBig
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    assert body["data"]["scalarSpecimenBySignedBig"] == {
        "label": "target",
        "signedBig": "9223372036854775000",
    }
    # Sanity: the value we asserted on resolved through the ORM lookup,
    # not an accidental fixture coincidence.
    assert target.signed_big == _SIGNED_BIG


@pytest.mark.django_db
def test_scalar_specimen_bigint_input_int_literal_argument_over_http():
    """A ``BigInt!`` argument provided as a JSON-int literal parses correctly.

    Pins ``BigInt.parse_value``'s int acceptance end-to-end: when the
    requested value fits in JSON's safe-integer range the consumer can
    pass it as a bare int literal (``signedBig: 42``) and the resolver
    must receive ``42`` as an int. Migrated from
    ``tests/types/test_converters.py::test_bigint_parses_int_argument_via_schema_execution``.
    """
    _seed_specimen(label="target", signed_big=42)
    _seed_specimen(label="other", signed_big=_SIGNED_BIG)

    response = _post_graphql(
        """
        query {
          scalarSpecimenBySignedBig(signedBig: 42) {
            label
            signedBig
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    # The outbound wire format is still the decimal string — even for
    # small values that JSON could represent as a bare number. That's
    # the BigInt scalar's contract: consumers must always parse the
    # response as a string. Anything else would be a wire-format leak.
    assert body["data"]["scalarSpecimenBySignedBig"] == {"label": "target", "signedBig": "42"}


@pytest.mark.django_db
def test_scalars_optimizer_select_related_on_self_fk_in_http_query():
    """Forward self-FK selection collapses to one SQL query under the optimizer.

    Pins ``DjangoOptimizerExtension``'s ``select_related`` plan against a
    self-referential FK (``ScalarSpecimen.parent`` -> ``ScalarSpecimen``) —
    a distinct shape from the cross-model FK select_related already covered
    by ``test_library_api.py::test_library_optimizer_selects_book_shelf_in_http_query``
    (book -> shelf). Proves the walker's planner does not loop or
    double-resolve when the relation target is the source model itself.
    Migrated from
    ``tests/optimizer/test_extension.py::test_optimizer_applies_select_related_for_forward_fk``
    (whose synthetic ``schema.execute_sync`` against ``Item -> Category`` is
    redundant with the library HTTP test plus this self-FK shape).
    """
    parent = _seed_specimen(label="root")
    _seed_specimen(label="child_a", parent=parent)
    _seed_specimen(label="child_b", parent=parent)

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allScalarSpecimens {
                label
                parent { label }
              }
            }
            """,
        )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    # 1 query: SELECT scalars_scalarspecimen ... LEFT OUTER JOIN
    # scalars_scalarspecimen T2 ON parent_id. Without the optimizer the
    # ``parent { label }`` branch would issue 1 + 3 = 4 queries.
    assert len(captured) == 1, [q["sql"] for q in captured]
    sql = captured[0]["sql"]
    assert "scalars_scalarspecimen" in sql
    assert "JOIN" in sql.upper()


@pytest.mark.django_db
def test_scalars_optimizer_prefetch_related_on_reverse_self_fk_in_http_query():
    """Reverse self-FK selection collapses to two SQL queries via ``prefetch_related``.

    Pins the ``DjangoOptimizerExtension`` ``prefetch_related`` plan against
    ``ScalarSpecimen.children`` — the reverse side of a self-referential FK.
    Distinct from the cross-model reverse-FK ``prefetch_related`` already
    covered by
    ``test_library_api.py::test_library_reverse_fk_and_m2m_prefetch_sql_shape_over_http``
    (shelf -> books). Proves the prefetch planner does not loop or
    double-prefetch when the source and target model coincide.
    Migrated from
    ``tests/optimizer/test_extension.py::test_optimizer_applies_prefetch_related_for_reverse_fk``.
    """
    root = _seed_specimen(label="root")
    _seed_specimen(label="leaf_a", parent=root)
    _seed_specimen(label="leaf_b", parent=root)

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allScalarSpecimens {
                label
                children { label }
              }
            }
            """,
        )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    # 2 queries: SELECT scalars_scalarspecimen ... + a single prefetched
    # SELECT for the ``children`` reverse relation. Without the optimizer
    # the ``children`` branch would issue 1 + 3 = 4 queries.
    assert len(captured) == 2, [q["sql"] for q in captured]


@pytest.mark.django_db
def test_scalars_optimizer_fk_id_elision_for_self_fk_in_http_query():
    """``parent { id }`` is served from ``ScalarSpecimen.parent_id`` with no JOIN.

    Pins the ``B2`` FK-id elision behavior end-to-end against a self-
    referential FK. An id-only forward-FK selection should NOT issue a
    JOIN — Django already has the FK column (``parent_id``) on the source
    row, so the optimizer plans the query with ``only(..., "parent_id")``
    and synthesizes the stub at resolver time. Distinct from the
    cross-model FK case; previously unreachable from any HTTP test.
    Behavioral half of the migration from
    ``tests/optimizer/test_extension.py::test_optimizer_elides_forward_fk_id_only_selection``;
    the plan-state assertions (``plan.fk_id_elisions``, ``plan.only_fields``,
    ``ctx.dst_optimizer_fk_id_elisions``) stay package-internal in the same
    test, slimmed of the now-redundant query-count and data-correctness
    assertions.
    """
    root = _seed_specimen(label="root")
    child = _seed_specimen(label="child", parent=root)

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allScalarSpecimens {
                label
                parent { id }
              }
            }
            """,
        )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    rows = {row["label"]: row for row in body["data"]["allScalarSpecimens"]}
    assert rows["root"]["parent"] is None
    # Child's ``parent { id }`` should equal the root row's id without a JOIN.
    # ``id`` resolves to ``Int`` (via ``BigAutoField -> int``), so JSON
    # serializes it as a number.
    assert rows["child"]["parent"] == {"id": root.id}
    # 1 query: SELECT scalars_scalarspecimen ... (no JOIN). Without the
    # elision the ``parent { id }`` selection would either JOIN or issue
    # a follow-up SELECT per non-null child row.
    assert len(captured) == 1, [q["sql"] for q in captured]
    sql = captured[0]["sql"]
    assert "JOIN" not in sql.upper(), sql
    # And ``parent_id`` must be in the projection (Django needs it to
    # synthesize the stub the resolver returns).
    assert "parent_id" in sql, sql
    # Sanity: the row we asserted on is the one we created.
    assert child.parent_id == root.id


@pytest.mark.django_db
def test_scalars_optimizer_no_fk_id_elision_when_extra_scalar_selected_in_http_query():
    """Selecting any target scalar beyond ``id`` forces the normal JOIN path.

    Pins B2's "elision opt-out" rule end-to-end: as soon as the consumer
    selects ANY target scalar besides ``id``, the optimizer must NOT elide
    the relation — it must plan ``select_related("parent")`` and issue a
    JOIN. Otherwise the resolver-time FK-id stub would carry only the id
    and the extra scalar would resolve to ``None``. Exercised against the
    self-FK ``ScalarSpecimen.parent``. Behavioral half of the migration from
    ``tests/optimizer/test_extension.py::test_optimizer_does_not_elide_forward_fk_when_extra_scalar_selected``;
    the plan-state half (``select_related == ("parent",)``,
    ``fk_id_elisions == ()``, full ``only_fields``) stays package-internal
    in the slimmed sibling test.
    """
    root = _seed_specimen(label="root")
    child = _seed_specimen(label="child", parent=root)

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allScalarSpecimens {
                label
                parent { id label }
              }
            }
            """,
        )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    rows = {row["label"]: row for row in body["data"]["allScalarSpecimens"]}
    assert rows["root"]["parent"] is None
    # Both ``id`` AND ``label`` must populate from the JOINed row — proving
    # the optimizer did NOT elide and that the ``parent`` stub is the real
    # joined row, not the fk-id-only stub.
    assert rows["child"]["parent"] == {"id": root.id, "label": "root"}
    # Still 1 query — but via JOIN, not via the elision shortcut.
    assert len(captured) == 1, [q["sql"] for q in captured]
    sql = captured[0]["sql"]
    assert "JOIN" in sql.upper(), sql


@pytest.mark.django_db
def test_scalars_optimizer_fk_id_elision_for_each_alias_in_http_query():
    """Duplicate aliases on an id-only forward FK both resolve from the source FK column.

    Pins B2/O4 behavior end-to-end: selecting the same FK twice under two
    GraphQL field aliases must still elide to a single FK-column SELECT
    with no JOIN, and both aliases must surface the same id value at
    resolve time. Exercised against the self-FK
    (``ScalarSpecimen.parent``) — distinct from the cross-model case. The
    plan-state assertions (``plan.fk_id_elisions`` covering BOTH alias
    keys, ``plan.only_fields == ("parent_id",)``) remain pinned by
    ``tests/optimizer/test_extension.py::test_optimizer_elides_forward_fk_id_only_selection_for_each_alias_plan_shape``.
    """
    root = _seed_specimen(label="root")
    child = _seed_specimen(label="child", parent=root)

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allScalarSpecimens {
                label
                first: parent { id }
                second: parent { id }
              }
            }
            """,
        )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    rows = {row["label"]: row for row in body["data"]["allScalarSpecimens"]}
    # Root has no parent; both aliases must collapse to ``None``.
    assert rows["root"]["first"] is None
    assert rows["root"]["second"] is None
    # Child's two aliases must report the same id (==> the source FK column).
    assert rows["child"]["first"] == {"id": root.id}
    assert rows["child"]["second"] == {"id": root.id}
    # 1 query, no JOIN.
    assert len(captured) == 1, [q["sql"] for q in captured]
    sql = captured[0]["sql"]
    assert "JOIN" not in sql.upper(), sql
    assert "parent_id" in sql, sql
    # Sanity: the row we asserted on is the one we created.
    assert child.parent_id == root.id


@pytest.mark.django_db
def test_scalars_optimizer_fk_id_elision_does_not_leak_to_sibling_root_in_http_query():
    """FK-id elision on one root branch does not poison a sibling branch.

    The first root selects ``ScalarSpecimen.parent { id }`` and should use
    the FK-id elision path: one root SELECT, no JOIN, ``parent_id`` projected.
    The sibling root selects ``NullableScalarSpecimen.partner { label }`` and
    therefore needs the real related row. This pins the same B2/O4 branch
    isolation contract through the real fakeshop `/graphql/` request path.
    """
    root = _seed_specimen(label="root")
    _seed_specimen(label="child", parent=root)
    _seed_nullable_specimen(label="linked", partner=root)

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allScalarSpecimens {
                label
                parent { id }
              }
              allNullableScalarSpecimens {
                label
                partner { label }
              }
            }
            """,
        )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    specimens = {row["label"]: row for row in body["data"]["allScalarSpecimens"]}
    nullable = {row["label"]: row for row in body["data"]["allNullableScalarSpecimens"]}
    assert specimens["root"]["parent"] is None
    assert specimens["child"]["parent"] == {"id": root.id}
    assert nullable["linked"]["partner"] == {"label": "root"}

    assert len(captured) == 2, [q["sql"] for q in captured]
    specimen_sql = captured[0]["sql"]
    nullable_sql = captured[1]["sql"]
    assert "JOIN" not in specimen_sql.upper(), specimen_sql
    assert "parent_id" in specimen_sql, specimen_sql
    assert "JOIN" in nullable_sql.upper(), nullable_sql
    assert "scalars_nullablescalarspecimen" in nullable_sql.lower(), nullable_sql
    assert "scalars_scalarspecimen" in nullable_sql.lower(), nullable_sql


@pytest.mark.django_db
def test_scalars_optimizer_o6_downgrade_to_prefetch_for_custom_get_queryset_in_http_query():
    """O6 / B2: forward FK to a target with custom ``get_queryset`` downgrades to ``Prefetch``.

    When the target type declares ``get_queryset(cls, queryset, info)``, the
    optimizer must NOT use ``select_related`` (which would JOIN raw without
    consulting the classmethod) and must NOT elide the relation even for an
    id-only selection. It must plan a ``Prefetch(queryset=cls.get_queryset(...))``
    so the consumer's filter survives end-to-end. Observable as 2 SQL
    queries (root SELECT + prefetched tag SELECT) rather than 1 SQL query
    via JOIN or elision. Behavioral half of the migration from
    ``tests/optimizer/test_extension.py::test_optimizer_does_not_elide_forward_fk_when_target_has_custom_get_queryset``;
    the plan-state half (``plan.select_related``, ``plan.fk_id_elisions``,
    ``plan.only_fields``, ``plan.prefetch_related``) stays package-internal
    in the slimmed sibling test.
    """
    active = _seed_tag(label="active-tag", active=True)
    _seed_specimen(label="tagged", tag=active)

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allScalarSpecimens {
                label
                tag { id }
              }
            }
            """,
        )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    # 2 queries: SELECT scalars_scalarspecimen + a prefetched SELECT for
    # scalars_scalarspecimentag (filtered to ``active=True`` by the custom
    # get_queryset). Without the O6 downgrade this would either JOIN
    # (1 query) or elide entirely — both incorrect because the consumer's
    # filter would be silently bypassed.
    assert len(captured) == 2, [q["sql"] for q in captured]
    main_sql = captured[0]["sql"]
    # Main query must NOT JOIN — that would be the un-downgraded path.
    assert "scalarspecimentag" not in main_sql.lower(), main_sql
    # Prefetch SELECT must hit the tag table and carry the ``active`` filter.
    tag_sql = captured[1]["sql"]
    assert "scalarspecimentag" in tag_sql.lower(), tag_sql
    assert "active" in tag_sql.lower(), tag_sql


@pytest.mark.django_db
def test_scalars_custom_get_queryset_filters_inactive_tag_to_null_in_http_query():
    """A specimen pointing at an inactive tag resolves ``tag`` to ``null``.

    Pins the consumer-visible effect of ``ScalarSpecimenTagType.get_queryset``
    end-to-end: tags with ``active=False`` are excluded from the prefetched
    queryset, so the source specimen's ``tag`` field collapses to ``None``
    even though the row's FK column is non-null in the database. Proves
    the optimizer planned ``Prefetch(queryset=cls.get_queryset(...))`` and
    that the filter survived plan execution.
    """
    inactive = _seed_tag(label="inactive-tag", active=False)
    active = _seed_tag(label="active-tag", active=True)
    _seed_specimen(label="with-active", tag=active)
    _seed_specimen(label="with-inactive", tag=inactive)
    _seed_specimen(label="untagged")

    response = _post_graphql(
        """
        query {
          allScalarSpecimens {
            label
            tag { label active }
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    rows = {row["label"]: row for row in body["data"]["allScalarSpecimens"]}

    assert rows["with-active"]["tag"] == {"label": "active-tag", "active": True}
    # The inactive tag isn't in the Prefetch result, so the source-side
    # ``tag`` resolves to None even though the FK column is set.
    assert rows["with-inactive"]["tag"] is None
    # And the untagged specimen also resolves None (FK column is NULL).
    assert rows["untagged"]["tag"] is None


@pytest.mark.django_db
def test_scalars_tagged_specimens_reverse_fk_in_http_query():
    """The reverse-FK ``ScalarSpecimenTag.tagged_specimens`` lists every linked specimen.

    Distinct from the existing reverse-FK shapes on ``ScalarSpecimenType``
    (self-FK ``children`` and cross-model ``nullable_partners``):
    ``tagged_specimens`` is reverse-FK from a model OUTSIDE the
    ``ScalarSpecimen`` family back into it. Confirms reverse-FK exposure
    works even when the source side has a custom ``get_queryset``.
    """
    tag_a = _seed_tag(label="tag-a")
    tag_b = _seed_tag(label="tag-b")
    _seed_specimen(label="a1", tag=tag_a)
    _seed_specimen(label="a2", tag=tag_a)
    _seed_specimen(label="b1", tag=tag_b)
    _seed_specimen(label="orphan")

    response = _post_graphql(
        """
        query {
          allScalarSpecimenTags {
            label
            taggedSpecimens { label }
          }
        }
        """,
    )
    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    rows = {row["label"]: row for row in body["data"]["allScalarSpecimenTags"]}
    assert sorted(s["label"] for s in rows["tag-a"]["taggedSpecimens"]) == ["a1", "a2"]
    assert sorted(s["label"] for s in rows["tag-b"]["taggedSpecimens"]) == ["b1"]


@pytest.mark.django_db
def test_scalars_optimizer_coerces_manager_to_queryset_in_http_query():
    """A plain ``@strawberry.field`` resolver returning a bare ``Manager`` is still optimized.

    Pins the optimizer's defensive ``Manager``-coercion code path:
    consumers commonly write ``return Model.objects`` rather than
    ``return Model.objects.all()``; both shapes resolve identical data
    via Strawberry's default resolver, but without the optimizer's
    coercion the ``isinstance(QuerySet)`` gate would let the Manager
    pass through unoptimized and the consumer would pay N+1 on any
    forward-FK selection. ``apps.scalars.schema.Query.all_scalar_specimens_via_manager``
    deliberately returns the bare Manager so the live HTTP query
    exercises this path end-to-end. Behavioral half of the migration
    from ``tests/optimizer/test_extension.py::test_optimize_coerces_manager_through_all``;
    the cache-state half (``ext.cache_info().misses == 1`` — proof the
    plan was actually built) stays package-internal in the slimmed
    sibling test.

    Distinct from ``DjangoListField``'s own Manager coercion path
    exercised by ``apps.library.schema._branches_manager_resolver``:
    that goes through the listfield wrapper, this goes through a plain
    ``@strawberry.field`` resolver and hits the optimizer-extension
    coercion code instead.
    """
    root = _seed_specimen(label="root")
    _seed_specimen(label="child_a", parent=root)
    _seed_specimen(label="child_b", parent=root)

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allScalarSpecimensViaManager {
                label
                parent { label }
              }
            }
            """,
        )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body, body
    # 1 query: SELECT scalarspecimen ... LEFT OUTER JOIN scalarspecimen
    # via select_related("parent"). Without the optimizer's Manager
    # coercion this would be 1 + 3 = 4 queries — one per child's parent
    # lookup — proving the gate would have let the Manager pass through
    # unoptimized.
    assert len(captured) == 1, [q["sql"] for q in captured]
    sql = captured[0]["sql"]
    assert "JOIN" in sql.upper(), sql
