"""Live GraphQL HTTP tests for scalar filtering, ordering, and related-queryset behavior.

Where ``test_scalars_api.py`` pins the converter table on the OUTPUT side,
these tests exercise it on the INPUT side via the filtersets wired in
``apps.scalars.schema``. The scalar types are NOT Relay nodes, so
``id: { in: [...] }`` resolves to the django-filter-generated
``BaseInFilter`` -> ``list[int]`` converter path -- the non-Relay
counterpart to the library/products own-PK ``GlobalIDMultipleChoiceFilter``
path. ``ScalarSpecimenFilter.tag`` (a ``RelatedFilter`` onto a type whose
``get_queryset`` filters ``active=True``) exercises related-branch
visibility through a relation traversal. The self-referential ``parent`` /
``children`` relation keys filter by raw ``Int`` specimen pks (the target type is
not a Relay node): one pk or a list for the forward key, a list for the reverse
one, with the README membership rules on every list. ``price_span`` is a declared
``RangeFilter`` on both specimen filtersets: its nested input type is scoped
per owning filterset and the ``range`` lookup applies over the wire.
"""

import datetime
import uuid
from decimal import Decimal

import pytest
from apps.scalars import models
from graphql_client import assert_graphql_data as _assert_graphql_data
from graphql_client import assert_graphql_success as _assert_graphql_success

_DATE = datetime.date(2021, 6, 15)
_DATETIME = datetime.datetime(2021, 6, 15, 9, 30, tzinfo=datetime.timezone.utc)
_TIME = datetime.time(9, 30)
_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")


def _seed_specimen(label: str, **overrides: object) -> models.ScalarSpecimen:
    defaults: dict[str, object] = {
        "label": label,
        "flag": False,
        "score": 1.0,
        "occurred_on": _DATE,
        "occurred_at": _DATETIME,
        "occurred_time": _TIME,
        "external_id": uuid.uuid4(),
        "signed_big": 1,
        "unsigned_big": 1,
    }
    defaults.update(overrides)
    return models.ScalarSpecimen.objects.create(**defaults)


@pytest.mark.django_db
def test_scalars_filter_by_label_icontains():
    """Text-scalar filter input (``label: { iContains }``)."""
    _seed_specimen("alpha")
    _seed_specimen("beta")
    _assert_graphql_data(
        """
        query {
          allScalarSpecimens(filter: { label: { iContains: "alph" } }) {
            label
          }
        }
        """,
        {"allScalarSpecimens": [{"label": "alpha"}]},
    )


@pytest.mark.django_db
def test_scalars_filter_by_flag_exact():
    """Boolean-scalar filter input (``flag: { exact: true }``)."""
    _seed_specimen("alpha", flag=True)
    _seed_specimen("beta", flag=False)
    _seed_specimen("gamma", flag=True)
    _assert_graphql_data(
        """
        query {
          allScalarSpecimens(filter: { flag: { exact: true } }) {
            label
          }
        }
        """,
        {"allScalarSpecimens": [{"label": "alpha"}, {"label": "gamma"}]},
    )


@pytest.mark.django_db
def test_scalars_filter_by_non_relay_pk_in_list():
    """Non-Relay ``id: { in: [...] }`` resolves to the integer CSV path (H5c).

    The scalar types are not Relay nodes, so ``id`` is a plain integer column.
    Its ``in`` lookup routes through the framework's ``IntegerInFilter`` (a
    ``BaseInFilter`` subclass that also drops out-of-range members and matches
    nothing on a fully-dropped non-empty list) and converts to a ``list[Int]``
    CSV input rather than the own-PK ``GlobalIDMultipleChoiceFilter`` the Relay
    apps use. This pins the non-Relay counterpart of that fix end to end.
    """
    alpha = _seed_specimen("alpha")
    _seed_specimen("beta")
    gamma = _seed_specimen("gamma")
    _assert_graphql_data(
        f"""
        query {{
          allScalarSpecimens(filter: {{ id: {{ in: [{alpha.pk}, {gamma.pk}] }} }}) {{
            label
          }}
        }}
        """,
        {"allScalarSpecimens": [{"label": "alpha"}, {"label": "gamma"}]},
    )


@pytest.mark.django_db
def test_scalars_filter_by_related_tag_label():
    """``RelatedFilter`` onto ``ScalarSpecimenTag`` (whose ``get_queryset`` is active=True)."""
    hot = models.ScalarSpecimenTag.objects.create(label="hot", active=True)
    _seed_specimen("alpha", tag=hot)
    _seed_specimen("beta")
    _assert_graphql_data(
        """
        query {
          allScalarSpecimens(filter: { tag: { label: { exact: "hot" } } }) {
            label
          }
        }
        """,
        {"allScalarSpecimens": [{"label": "alpha"}]},
    )


@pytest.mark.django_db
def test_scalars_order_by_label_desc():
    """``orderBy: [{ label: DESC }]`` sorts specimens by label descending (DONE-028 wiring)."""
    _seed_specimen("alpha")
    _seed_specimen("gamma")
    _seed_specimen("beta")
    expected = [
        {"label": label}
        for label in models.ScalarSpecimen.objects.order_by("-label").values_list(
            "label",
            flat=True,
        )
    ]
    _assert_graphql_data(
        "query { allScalarSpecimens(orderBy: [{ label: DESC }]) { label } }",
        {"allScalarSpecimens": expected},
    )


_RANGE_TYPE_QUERY = """
query {
  scalar: __type(name: "ScalarSpecimenFilterPriceRangeInputType") {
    name
    inputFields { name }
  }
  nullable: __type(name: "NullableScalarSpecimenFilterPriceRangeInputType") {
    name
    inputFields { name }
  }
}
"""


@pytest.mark.django_db
def test_range_input_types_are_scoped_per_filterset():
    """Two shipped filtersets sharing a RangeFilter field_name mint distinct nested types.

    ``price_span`` is a declared ``RangeFilter(field_name="price")`` on both
    ``ScalarSpecimenFilter`` and ``NullableScalarSpecimenFilter``. Unscoped,
    both nested classes would claim ``PriceRangeInputType`` and Strawberry
    would silently keep one. The owning-filterset qualifier keeps both
    ``__type`` results non-null, each with ``start`` / ``end``.
    """
    data = _assert_graphql_success(_RANGE_TYPE_QUERY)

    scalar = data["scalar"]
    nullable = data["nullable"]
    assert scalar is not None
    assert nullable is not None
    assert scalar["name"] == "ScalarSpecimenFilterPriceRangeInputType"
    assert nullable["name"] == "NullableScalarSpecimenFilterPriceRangeInputType"
    assert scalar["name"] != nullable["name"]
    assert {field["name"] for field in scalar["inputFields"]} == {"start", "end"}
    assert {field["name"] for field in nullable["inputFields"]} == {"start", "end"}


@pytest.mark.django_db
def test_scalars_filter_by_price_span_range():
    """Declared ``priceSpan: { range: { start, end } }`` keeps in-range rows and drops the rest."""
    _seed_specimen("cheap", price=Decimal("1.0000"))
    _seed_specimen("mid", price=Decimal("50.0000"))
    _seed_specimen("dear", price=Decimal("50000.0000"))
    _assert_graphql_data(
        """
        query {
          allScalarSpecimens(
            filter: { priceSpan: { range: { start: "10.0000", end: "100.0000" } } }
          ) {
            label
          }
        }
        """,
        {"allScalarSpecimens": [{"label": "mid"}]},
    )


_BY_PARENT = """
query ($filter: ScalarSpecimenFilterInputType) {
  allScalarSpecimens(filter: $filter) {
    label
  }
}
"""


@pytest.mark.django_db
def test_scalars_filter_by_forward_fk_primary_key_exact_and_in():
    """``parent`` takes one raw pk for ``exact`` and a list for ``in``; ``isNull`` stays Boolean."""
    root_a = _seed_specimen("root-a")
    root_b = _seed_specimen("root-b")
    _seed_specimen("child-a", parent=root_a)
    _seed_specimen("child-b", parent=root_b)

    for filter_input, labels in (
        ({"parent": {"exact": root_a.pk}}, ["child-a"]),
        ({"parent": {"in": [root_a.pk, root_b.pk]}}, ["child-a", "child-b"]),
        ({"parent": {"isNull": True}}, ["root-a", "root-b"]),
    ):
        _assert_graphql_data(
            _BY_PARENT,
            {"allScalarSpecimens": [{"label": label} for label in labels]},
            variables={"filter": filter_input},
        )


@pytest.mark.django_db
def test_scalars_forward_fk_primary_key_follows_the_membership_rules():
    """A missing pk matches nothing, beside a real one it is dropped, and ``in: []`` is empty.

    None of these is a validation error: the relation key never checks that the target
    row exists, so a missing pk and one the caller cannot see answer alike.
    """
    root = _seed_specimen("root")
    _seed_specimen("child", parent=root)
    missing = root.pk + 1000

    for filter_input, labels in (
        ({"parent": {"exact": missing}}, []),
        ({"parent": {"in": [missing]}}, []),
        ({"parent": {"in": [missing, root.pk]}}, ["child"]),
        ({"parent": {"in": []}}, []),
    ):
        _assert_graphql_data(
            _BY_PARENT,
            {"allScalarSpecimens": [{"label": label} for label in labels]},
            variables={"filter": filter_input},
        )


@pytest.mark.django_db
def test_scalars_filter_by_reverse_fk_primary_keys():
    """``children`` (the reverse FK) takes a list of raw child pks."""
    root_a = _seed_specimen("root-a")
    root_b = _seed_specimen("root-b")
    child_a = _seed_specimen("child-a", parent=root_a)
    child_b = _seed_specimen("child-b", parent=root_b)
    _seed_specimen("child-a2", parent=root_a)

    _assert_graphql_data(
        _BY_PARENT,
        {"allScalarSpecimens": [{"label": "root-a"}, {"label": "root-b"}]},
        variables={"filter": {"children": {"exact": [child_a.pk, child_b.pk]}}},
    )
