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
from django.test import Client
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
