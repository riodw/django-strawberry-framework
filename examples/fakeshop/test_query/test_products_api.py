"""Live GraphQL HTTP tests for the products app filter surface.

Mirrors ``test_library_api.py``'s harness. Exercises the products
filtersets wired in ``apps.products.schema`` end to end:

* the per-field ``check_name_permission`` gate on ``CategoryFilter`` (a
  ``DONE-021-0.0.8`` filter permission hook) -- including the regression
  guard that the gate now fires for NON-``exact`` lookups (``iContains``),
  not just ``exact``;
* own-PK Relay ``GlobalID`` filtering (``id: { in: [...] }``) now that the
  products types declare ``interfaces = (relay.Node,)``;
* ``RelatedFilter`` traversal (``Item.category``) via the nested
  GlobalID input.
"""

import importlib
import sys

import pytest
from apps.products import models
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import clear_url_caches
from strawberry import relay

from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests():
    """Recreate imported DjangoType classes if package tests cleared the registry.

    Mirrors the ``test_library_api.py`` fixture: package tests clear the
    global registry, while the example schema finalizes import-time
    ``DjangoType`` classes. Reload only schema modules (not
    ``apps.products.models``) so Django model classes stay stable.
    """
    registry.clear()
    products_schema = sys.modules.get("apps.products.schema")
    if products_schema is None:
        importlib.import_module("apps.products.schema")
    else:
        importlib.reload(products_schema)

    project_schema = sys.modules.get("config.schema")
    if project_schema is None:
        importlib.import_module("config.schema")
    else:
        importlib.reload(project_schema)

    urls = sys.modules.get("config.urls")
    if urls is not None:
        importlib.reload(urls)
        clear_url_caches()


def _seed_catalog():
    bank = models.Category.objects.create(name="Bank", description="Banking provider")
    person = models.Category.objects.create(name="Person", description="People provider")
    models.Category.objects.create(name="Address", description="Address provider")
    models.Item.objects.create(name="checking", category=bank)
    models.Item.objects.create(name="iban", category=bank)
    models.Item.objects.create(name="first_name", category=person)
    return bank, person


def _post_graphql(query: str, *, client: Client | None = None):
    graphql_client = client or Client()
    return graphql_client.post(
        "/graphql/",
        data={"query": query},
        content_type="application/json",
    )


def _assert_graphql_data(query: str, expected: dict, *, client: Client | None = None):
    response = _post_graphql(query, client=client)
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"] == expected
    return response


def _staff_client() -> Client:
    staff = get_user_model().objects.create_user(username="staff", password="pw", is_staff=True)
    client = Client()
    client.force_login(staff)
    return client


@pytest.mark.django_db
def test_products_categories_filter_by_name_exact_as_staff():
    """A staff user clears ``CategoryFilter.check_name_permission`` and filters by name."""
    _seed_catalog()
    _assert_graphql_data(
        """
        query {
          allCategories(filter: { name: { exact: "Bank" } }) {
            name
          }
        }
        """,
        {"allCategories": [{"name": "Bank"}]},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_categories_filter_by_name_denied_for_anonymous():
    """An anonymous user filtering by ``Category.name`` (exact) is rejected by the gate."""
    _seed_catalog()
    response = _post_graphql(
        """
        query {
          allCategories(filter: { name: { exact: "Bank" } }) {
            name
          }
        }
        """,
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_categories_name_permission_fires_for_non_exact_lookup():
    """The gate fires for a NON-``exact`` lookup too (H2 regression guard).

    Before the fix, ``check_<field>_permission`` was dispatched on the
    lookup-expanded form key, so only ``exact`` (the suffix-free key)
    triggered it; ``iContains`` slipped past ungated. The gate now keys on
    the source field, so an anonymous ``name: { iContains: ... }`` filter
    is rejected exactly like the ``exact`` form.
    """
    _seed_catalog()
    response = _post_graphql(
        """
        query {
          allCategories(filter: { name: { iContains: "ban" } }) {
            name
          }
        }
        """,
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_categories_filter_by_relay_own_pk_global_id_in():
    """Own-PK Relay ``id: { in: [...] }`` accepts a list of GlobalIDs (H5/M1 E2E).

    ``CategoryType`` is a Relay node, so ``id`` is a GlobalID; the ``in``
    lookup resolves to ``GlobalIDMultipleChoiceFilter`` and each element is
    decoded + type-validated before the ``id__in`` clause runs. No
    permission gate guards ``id``, so this works anonymously.
    """
    bank, person = _seed_catalog()
    gid_bank = str(relay.GlobalID(type_name="CategoryType", node_id=str(bank.pk)))
    gid_person = str(relay.GlobalID(type_name="CategoryType", node_id=str(person.pk)))
    _assert_graphql_data(
        f"""
        query {{
          allCategories(filter: {{ id: {{ in: ["{gid_bank}", "{gid_person}"] }} }}) {{
            name
          }}
        }}
        """,
        {"allCategories": [{"name": "Bank"}, {"name": "Person"}]},
    )


@pytest.mark.django_db
def test_products_categories_filter_by_starts_with_via_all_lookups():
    """``Meta.fields = {"name": "__all__"}`` exposes lookups beyond the explicit set.

    ``startsWith`` is in none of the hand-listed lookup sets -- it exists only
    because ``CategoryFilter.name`` uses the per-field ``"__all__"`` shorthand,
    which expands to every concrete (non-transform) lookup for the field.
    """
    _seed_catalog()
    _assert_graphql_data(
        """
        query {
          allCategories(filter: { name: { startsWith: "Ba" } }) {
            name
          }
        }
        """,
        {"allCategories": [{"name": "Bank"}]},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_items_filter_by_related_category_global_id():
    """``Item.category`` ``RelatedFilter`` traversal via the nested GlobalID input."""
    bank, _person = _seed_catalog()
    gid_bank = str(relay.GlobalID(type_name="CategoryType", node_id=str(bank.pk)))
    _assert_graphql_data(
        f"""
        query {{
          allItems(filter: {{ category: {{ id: {{ exact: "{gid_bank}" }} }} }}) {{
            name
          }}
        }}
        """,
        {"allItems": [{"name": "checking"}, {"name": "iban"}]},
    )
