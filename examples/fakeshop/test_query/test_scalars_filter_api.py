"""Live GraphQL HTTP tests for scalar filter input and queryset behavior.

Where ``test_scalars_api.py`` pins the converter table on the OUTPUT side,
these tests exercise it on the INPUT side via the filtersets wired in
``apps.scalars.schema``. The scalar types are NOT Relay nodes, so
``id: { in: [...] }`` resolves to the django-filter-generated
``BaseInFilter`` -> ``list[int]`` converter path -- the non-Relay
counterpart to the library/products own-PK ``GlobalIDMultipleChoiceFilter``
path. ``ScalarSpecimenFilter.tag`` (a ``RelatedFilter`` onto a type whose
``get_queryset`` filters ``active=True``) exercises related-branch
visibility through a relation traversal.
"""

import datetime
import uuid

import pytest
from apps.scalars import models
from django.test import Client

_DATE = datetime.date(2021, 6, 15)
_DATETIME = datetime.datetime(2021, 6, 15, 9, 30, tzinfo=datetime.timezone.utc)
_TIME = datetime.time(9, 30)
_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests(reload_all_project_app_schemas):
    """Recreate imported DjangoType classes if package tests cleared the registry.

    Rebuilds the FULL project schema (every contributing app + config), not just
    ``apps.scalars.schema``: ``config.schema`` aggregates all five apps, so a
    scalars-only reload left the other apps unregistered after a package
    ``registry.clear()`` and the combined build raised a ``LazyType`` ``KeyError``
    under collection orders that did not pre-materialize them. See ``conftest.py``.
    """
    reload_all_project_app_schemas()


def _seed_specimen(label: str, **overrides):
    defaults = {
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


def _post_graphql(query: str):
    return Client().post("/graphql/", data={"query": query}, content_type="application/json")


def _assert_graphql_data(query: str, expected: dict):
    response = _post_graphql(query)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"] == expected
    return response


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
