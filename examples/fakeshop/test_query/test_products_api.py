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

Per AGENTS.md, the catalog is seeded via ``services.seed_data`` and the auth
user via ``services.create_users`` -- never hand-rolled. Faker-generated names
vary per provider set, so assertions are data-driven: the expected rows are
derived from the seeded data (or from the equivalent ORM query) and compared
against the GraphQL result, which both pins the filter behaviour and stays
robust across Faker versions.
"""

import importlib
import json
import sys

import pytest
from apps.products import models
from apps.products.services import create_users, seed_data
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
    """Log in the seeded ``staff_1`` user (``is_staff=True``) created by ``create_users``."""
    create_users(1)
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))
    return client


@pytest.mark.django_db
def test_products_categories_filter_by_name_exact_as_staff():
    """A staff user clears ``CategoryFilter.check_name_permission`` and filters by name."""
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    _assert_graphql_data(
        f"query {{ allCategories(filter: {{ name: {{ exact: {json.dumps(category.name)} }} }}) {{ name }} }}",
        {"allCategories": [{"name": category.name}]},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_categories_filter_by_name_denied_for_anonymous():
    """An anonymous user filtering by ``Category.name`` (exact) is rejected by the gate."""
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    response = _post_graphql(
        f"query {{ allCategories(filter: {{ name: {{ exact: {json.dumps(category.name)} }} }}) {{ name }} }}",
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_categories_name_permission_fires_for_non_exact_lookup():
    """The gate fires for a NON-``exact`` lookup too (regression guard).

    Before the fix, ``check_<field>_permission`` was dispatched on the
    lookup-expanded form key, so only ``exact`` (the suffix-free key)
    triggered it; ``iContains`` slipped past ungated. The gate now keys on
    the source field, so an anonymous ``name: { iContains: ... }`` filter
    is rejected exactly like the ``exact`` form.
    """
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    response = _post_graphql(
        f"query {{ allCategories(filter: {{ name: {{ iContains: {json.dumps(category.name[:2])} }} }}) {{ name }} }}",
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_items_related_category_name_permission_fires_for_anonymous():
    """A child ``RelatedFilter`` permission gate fires through the live API."""
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    response = _post_graphql(
        f"query {{ allItems(filter: {{ category: {{ name: {{ exact: {json.dumps(category.name)} }} }} }}) {{ name }} }}",
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_categories_filter_by_relay_own_pk_global_id_in():
    """Own-PK Relay ``id: { in: [...] }`` accepts a list of GlobalIDs.

    ``CategoryType`` is a Relay node, so ``id`` is a GlobalID; the ``in``
    lookup resolves to ``GlobalIDMultipleChoiceFilter`` and each element is
    decoded + type-validated before the ``id__in`` clause runs. No
    permission gate guards ``id``, so this works anonymously.
    """
    seed_data(1)
    categories = list(models.Category.objects.order_by("id")[:2])
    gids = ", ".join(
        f'"{relay.GlobalID(type_name="CategoryType", node_id=str(category.pk))}"'
        for category in categories
    )
    _assert_graphql_data(
        f"query {{ allCategories(filter: {{ id: {{ in: [{gids}] }} }}) {{ name }} }}",
        {"allCategories": [{"name": category.name} for category in categories]},
    )


@pytest.mark.django_db
def test_products_categories_filter_by_starts_with_via_all_lookups():
    """``Meta.fields = {"name": "__all__"}`` exposes lookups beyond the explicit set.

    ``startsWith`` is in none of the hand-listed lookup sets -- it exists only
    because ``CategoryFilter.name`` uses the per-field ``"__all__"`` shorthand,
    which expands to every concrete (non-transform) lookup for the field. The
    expected rows are computed with the equivalent ORM ``startswith`` so the
    assertion pins API == ORM rather than a Faker-specific name.
    """
    seed_data(1)
    prefix = models.Category.objects.order_by("id").first().name[:2]
    expected = [
        {"name": name}
        for name in models.Category.objects.filter(name__startswith=prefix)
        .order_by("id")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allCategories(filter: {{ name: {{ startsWith: "{prefix}" }} }}) {{ name }} }}',
        {"allCategories": expected},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_items_filter_by_related_category_global_id():
    """``Item.category`` ``RelatedFilter`` traversal via the nested GlobalID input."""
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    gid = str(relay.GlobalID(type_name="CategoryType", node_id=str(category.pk)))
    expected = [
        {"name": name}
        for name in models.Item.objects.filter(category=category)
        .order_by("id")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allItems(filter: {{ category: {{ id: {{ exact: "{gid}" }} }} }}) {{ name }} }}',
        {"allItems": expected},
    )
