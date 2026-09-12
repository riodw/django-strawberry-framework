"""Live ``/graphql/`` proof that fakeshop's composed project schema publishes every app's surface.

``config/schema.py`` merges each app's ``Query`` / ``Mutation`` into one
``DjangoSchema``, and a composition failure is silent in the worst way: the
endpoint keeps answering, just without one app's types, or with a relation whose
target was registered by an app that did not finalize. The rows here read that
composition from outside - an introspection request naming one type per app, and
an ordinary anonymous read that walks a reverse relation - so the claim is about
the schema a client reaches over HTTP rather than about an in-process rebuild.
The app manifest below is checked against the installed apps that ship a
``schema`` module, so a seventh contributor cannot join the composition without
also joining this suite.
"""

import importlib.util
from collections import defaultdict

import pytest
from apps.products import models as product_models
from apps.products.services import seed_data
from django.apps import apps as django_apps
from graphql_client import assert_graphql_success

_TYPE_FIELDS_QUERY = """
query($name: String!) {
  __type(name: $name) {
    name
    fields { name }
  }
}
"""


#: One representative type and field contract per app that contributes to
#: ``config/schema.py``: (app label, published type name, fields a client needs).
_APP_TYPE_CONTRACTS = (
    ("accounts", "UserType", {"username", "email"}),
    ("glossary", "GlossaryTermType", {"title", "anchor", "categories"}),
    ("kanban", "CardType", {"title", "number", "status"}),
    ("library", "BookType", {"title", "shelf", "genres"}),
    ("products", "ItemType", {"name", "category", "entries"}),
    ("products", "CategoryType", {"name", "description", "items"}),
    ("scalars", "ScalarSpecimenType", {"label", "parent", "children"}),
)


def _schema_contributing_app_labels():
    """Return the labels of the installed ``apps.*`` packages that ship a ``schema`` module."""
    return {
        config.label
        for config in django_apps.get_app_configs()
        if config.name.startswith("apps.")
        and importlib.util.find_spec(f"{config.name}.schema") is not None
    }


def test_the_manifest_covers_every_app_that_contributes_a_schema_module():
    """Every installed app with a ``schema`` module has a row above, and no row names a phantom app.

    ``config/schema.py`` imports each contributor by hand, so the introspection
    rows are only proof of composition if their manifest is the full contributor
    set; this row makes the manifest and the installed apps fail together.
    """
    assert {label for label, _, _ in _APP_TYPE_CONTRACTS} == _schema_contributing_app_labels()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("type_name", "expected_fields"),
    [(type_name, fields) for _, type_name, fields in _APP_TYPE_CONTRACTS],
    ids=[f"{label}-{type_name}" for label, type_name, _ in _APP_TYPE_CONTRACTS],
)
def test_the_composed_schema_publishes_each_apps_types(type_name, expected_fields):
    """One type per contributing app is on the shipped endpoint, with the fields a client traverses.

    Where the model has relations the set includes one (a forward FK, a reverse
    FK, or an M2M) next to a scalar; the schema-only accounts type has scalars
    alone. A type that never registered introspects as ``null`` here rather than
    failing the request, which is exactly why the absence has to be asserted
    rather than inferred from a green suite.
    """
    data = assert_graphql_success(_TYPE_FIELDS_QUERY, variables={"name": type_name})

    published = data["__type"]
    assert published is not None, type_name
    assert published["name"] == type_name
    assert expected_fields <= {field["name"] for field in published["fields"]}


@pytest.mark.django_db
def test_the_anonymous_category_page_lists_each_visible_category_with_its_own_visible_items():
    """The composed endpoint resolves a reverse relation under the anonymous cascade.

    Both levels narrow, and the mapping is what pins them together: the page
    carries exactly the non-private categories, and each one carries exactly its
    OWN non-private items. A total-count comparison would be satisfied by a page
    that attached the right number of items to the wrong parents, which is the
    failure a reverse-relation prefetch actually produces when its join key
    drifts. Expected values come from the equivalent post-cascade ORM queries
    (API == ORM), so the row survives ``seed_data``'s fixed-seed privacy split.
    Item lists are compared sorted, so no ``orderBy:`` is implied on the
    relation.
    """
    seed_data(1)
    expected: dict[str, list[str]] = defaultdict(list)
    for name in product_models.Category.objects.filter(is_private=False).values_list(
        "name",
        flat=True,
    ):
        expected[name] = []
    for category_name, item_name in product_models.Item.objects.filter(
        is_private=False,
        category__is_private=False,
    ).values_list("category__name", "name"):
        expected[category_name].append(item_name)
    assert expected, "the fixture must publish at least one visible category"

    data = assert_graphql_success(
        "{ allCategories { edges { node { name items { name } } } } }",
    )

    returned = {
        edge["node"]["name"]: sorted(item["name"] for item in edge["node"]["items"])
        for edge in data["allCategories"]["edges"]
    }
    assert returned == {name: sorted(items) for name, items in expected.items()}
