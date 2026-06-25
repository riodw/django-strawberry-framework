"""Live GraphQL HTTP tests for the products catalog API surface.

Mirrors ``test_library_api.py``'s harness. Exercises the products schema
wired in ``apps.products.schema`` end to end:

* optimizer SQL-shape contracts that are reachable through the real
  products GraphQL API;
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
from apps.products.forms import REJECTED_ITEM_NAME
from apps.products.services import create_users, delete_data, seed_cascade_split, seed_data
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import clear_url_caches
from strawberry import relay

from django_strawberry_framework.registry import registry


def _reload_products_project_schema() -> None:
    """Recreate imported DjangoType classes if package tests cleared the registry.

    Mirrors ``test_library_api.py::_reload_library_project_schema``: package
    tests clear the global registry, while the example schema finalizes
    import-time ``DjangoType`` classes. Reload only schema modules (not
    ``apps.products.models``) so Django model classes stay stable.

    Lifted out of the autouse fixture so a test can drive the reload itself
    after applying ``override_settings`` (e.g. the ``type``-strategy opt-out),
    ensuring the override is active *before* the schema finalizes.
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


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests():
    """Recreate the project schema around package-test registry clears."""
    _reload_products_project_schema()


def _post_graphql(query: str, *, client: Client | None = None, variables: dict | None = None):
    graphql_client = client or Client()
    payload: dict = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    return graphql_client.post(
        "/graphql/",
        data=payload,
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


def _global_id(type_name: str, pk: int) -> str:
    return str(relay.GlobalID(type_name=type_name, node_id=str(pk)))


def _login_with_perm(username: str, *codenames: str) -> Client:
    """Log in a seeded ``create_users(1)`` user after granting explicit products perms.

    The faithful exercise of the default ``DjangoModelPermission`` (spec-036
    Decision 15 / AR-H3): no ``create_users`` user holds ``add`` / ``change`` /
    ``delete`` by default and ``staff_1`` is ``is_staff=True`` but NOT a superuser,
    so a permitted caller must obtain the model perm in-test. Granting the explicit
    ``Permission`` (the ``services.create_users`` ``Permission.objects.get(
    codename=..., content_type__app_label="products")`` idiom) exercises the
    codename check exactly - a superuser would pass via the superuser
    short-circuit and never test the codename path. The user is re-fetched from the
    DB after the grant so the per-request permission cache is not stale.
    """
    from django.contrib.auth.models import Permission

    User = get_user_model()
    user = User.objects.get(username=username)
    for codename in codenames:
        perm = Permission.objects.get(codename=codename, content_type__app_label="products")
        user.user_permissions.add(perm)
    user = User.objects.get(pk=user.pk)  # drop the stale perm cache
    client = Client()
    client.force_login(user)
    return client


# The live mutation query strings (the wire contract the SDL renders):
# createItem(data: ItemInput!), updateItem(id: ID!, data: ItemPartialInput!),
# deleteItem(id: ID!), createCategory(data: CategoryInput!). ``id`` is the raw
# ``ID!`` GlobalID string (server-side-decoded - the DjangoNodeField precedent).
_CREATE_ITEM = (
    "mutation($d: ItemInput!) { createItem(data: $d) { "
    "node { name category { name } } errors { field messages } } }"
)
_UPDATE_ITEM = (
    "mutation($id: ID!, $d: ItemPartialInput!) { updateItem(id: $id, data: $d) { "
    "node { name } errors { field messages } } }"
)
_DELETE_ITEM = (
    "mutation($id: ID!) { deleteItem(id: $id) { "
    "node { id name category { name } } errors { field messages } } }"
)
_CREATE_CATEGORY = (
    "mutation($d: CategoryInput!) { createCategory(data: $d) { "
    "node { name } errors { field messages } } }"
)


@pytest.mark.django_db(transaction=True)
def test_create_item_happy_path():
    """``createItem`` with a permitted caller returns the optimizer-refetched node, no errors.

    AR-H3 permitted-caller success on the codename path: ``view_item_1`` is granted
    the explicit ``products.add_item`` (NOT a superuser). The payload ``node`` is
    the optimizer re-fetch with the nested ``category { name }`` resolvable, and the
    row persists in the DB after the request.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    client = _login_with_perm("view_item_1", "add_item")

    response = _post_graphql(
        _CREATE_ITEM,
        client=client,
        variables={
            "d": {
                "name": "LiveWidget",
                "categoryId": _global_id("products.category", category.pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItem"]
    assert result["errors"] == []
    assert result["node"] == {"name": "LiveWidget", "category": {"name": category.name}}
    created = models.Item.objects.get(name="LiveWidget", category=category)
    assert created.description == ""
    assert created.is_private is False


@pytest.mark.django_db(transaction=True)
def test_update_item_non_colliding_partial_update():
    """A partial update changing only ``name`` to a fresh value persists, leaving other fields.

    The spec's non-colliding partial-update case: ``ItemPartialInput`` provides
    only ``name``; the unprovided ``description`` / ``isPrivate`` / ``categoryId``
    are left unchanged in the DB (DRF ``partial=True`` parity). Driven as
    ``staff_1`` (full visibility, so the located row is the private-flagged one)
    granted the explicit ``change_item`` codename - ``staff_1`` is ``is_staff`` but
    NOT a superuser, so the ``DjangoModelPermission`` codename check still runs
    (AR-H3); visibility and write-authorization stay distinct contracts.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    item = models.Item.objects.create(
        name="Before",
        description="keep me",
        category=category,
        is_private=True,
    )
    client = _login_with_perm("staff_1", "change_item")

    response = _post_graphql(
        _UPDATE_ITEM,
        client=client,
        variables={"id": _global_id("products.item", item.pk), "d": {"name": "After"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItem"]
    assert result["errors"] == []
    assert result["node"] == {"name": "After"}
    item.refresh_from_db()
    assert item.name == "After"
    # Unprovided fields untouched.
    assert item.description == "keep me"
    assert item.is_private is True
    assert item.category_id == category.pk


@pytest.mark.django_db(transaction=True)
def test_delete_item_happy_path():
    """``deleteItem`` returns the pre-deletion snapshot (id + relation) and removes the row.

    The delete payload selects ``node { id name category { name } }`` - the AR-M5
    snapshot-before-delete shape, fully materialized (the relation populated on the
    detached instance) before ``delete()``. The id is preserved for client cache
    eviction; the row is gone from the DB after the request.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    item = models.Item.objects.create(name="Doomed", category=category)
    gid = _global_id("products.item", item.pk)
    client = _login_with_perm("staff_1", "delete_item")

    response = _post_graphql(_DELETE_ITEM, client=client, variables={"id": gid})
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["deleteItem"]
    assert result["errors"] == []
    assert result["node"]["name"] == "Doomed"
    assert result["node"]["category"] == {"name": category.name}
    # The id is preserved for cache eviction (feedback P1): it decodes to the
    # ORIGINAL pk even though the row is gone - the deletion runs against the
    # located instance, so Django's delete()-nulls-pk never touches this snapshot.
    assert relay.GlobalID.from_id(result["node"]["id"]).node_id == str(item.pk)
    assert not models.Item.objects.filter(pk=item.pk).exists()


@pytest.mark.django_db(transaction=True)
def test_create_category_happy_path():
    """``createCategory`` (the >=1 Category write) creates a fresh-named row end to end.

    Exercises a second model through the pipeline. ``Category.name`` is
    ``unique=True``, so the name must not be one ``seed_data`` produced (Faker
    provider names) - ``"zzz_live_cat"`` is reserved for the cascade seed helper's
    namespace and never a provider name, so no spurious uniqueness ``FieldError``.
    """
    create_users(1)
    seed_data(1)
    client = _login_with_perm("view_category_1", "add_category")

    response = _post_graphql(
        _CREATE_CATEGORY,
        client=client,
        variables={"d": {"name": "zzz_live_cat"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createCategory"]
    assert result["errors"] == []
    assert result["node"] == {"name": "zzz_live_cat"}
    assert models.Category.objects.filter(name="zzz_live_cat").exists()


# A lone UTF-16 surrogate code point (U+D800), carried over the wire as a JSON
# ``\ud800`` escape, is not a valid Unicode scalar value and cannot be encoded to
# UTF-8 for storage. It is rejected at input decode as a field-keyed FieldError,
# never reaching the DB-bound validate_unique/save where the backend would raise a
# raw UnicodeEncodeError (an unmapped ValueError) and leak as a top-level error.
_LONE_SURROGATE = "\ud800"


@pytest.mark.django_db(transaction=True)
def test_create_category_surrogate_in_unique_name_is_field_error_no_crash():
    """An unpaired surrogate in the unique ``name`` -> in-band ``FieldError`` on ``name``, no 500.

    The unique-field path: ``name`` is ``unique=True``, so an unstorable value would
    otherwise blow up inside ``full_clean()``'s ``validate_unique()`` DB lookup with
    a raw ``UnicodeEncodeError``. Decode rejects it first as a ``FieldError`` on
    ``name`` (the offending input field is decoded before ``description``), so the
    response is the in-band envelope, not a top-level error with ``data: null``.
    """
    create_users(1)
    client = _login_with_perm("view_category_1", "add_category")
    before = models.Category.objects.count()

    response = _post_graphql(
        _CREATE_CATEGORY,
        client=client,
        variables={"d": {"name": f"surrogate-{_LONE_SURROGATE}", "description": _LONE_SURROGATE}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createCategory"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["name"]
    assert models.Category.objects.count() == before


@pytest.mark.django_db(transaction=True)
def test_create_category_surrogate_in_nonunique_description_is_field_error_no_crash():
    """An unpaired surrogate in the non-unique ``description`` -> ``FieldError`` on ``description``, no 500.

    The non-unique-field path: a clean ``name`` passes ``validate_unique()``, so the
    unstorable ``description`` would otherwise blow up at ``save()``'s INSERT with a
    raw ``UnicodeEncodeError``. Decode rejects it first as a ``FieldError`` on
    ``description``; no row is written.
    """
    create_users(1)
    client = _login_with_perm("view_category_1", "add_category")
    before = models.Category.objects.count()

    response = _post_graphql(
        _CREATE_CATEGORY,
        client=client,
        variables={"d": {"name": "surrogate-description-only", "description": _LONE_SURROGATE}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createCategory"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["description"]
    assert not models.Category.objects.filter(name="surrogate-description-only").exists()


@pytest.mark.django_db(transaction=True)
def test_create_category_explicit_null_on_nonnullable_description_is_field_error():
    """An explicit ``null`` on the non-nullable ``description`` -> ``FieldError``, not a vague ``__all__`` (feedback #12).

    ``Category.description`` is ``blank=True, null=False``. An explicit ``null`` slips
    past ``full_clean`` (Django skips a blank-allowed field whose value is an empty
    value) and would otherwise hit a NOT NULL ``IntegrityError`` at ``save()``,
    surfacing as the generic ``"__all__"`` "A database constraint was violated." with
    no field attribution. It is now rejected at decode as a field-keyed ``FieldError``
    on ``description`` before any write; no row is created.
    """
    create_users(1)
    client = _login_with_perm("view_category_1", "add_category")
    before = models.Category.objects.count()

    response = _post_graphql(
        _CREATE_CATEGORY,
        client=client,
        variables={"d": {"name": "zzz_live_null_desc", "description": None}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createCategory"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["description"]
    assert models.Category.objects.count() == before


@pytest.mark.django_db(transaction=True)
def test_create_item_unique_constraint_envelope_uses_all_sentinel():
    """A duplicate ``(category, name)`` create returns a ``"__all__"``-keyed ``FieldError``.

    The multi-field ``unique_item_per_category`` constraint is caught by
    ``full_clean()``'s ``validate_constraints()`` BEFORE ``save()`` as a
    ``ValidationError`` mapping ``NON_FIELD_ERRORS`` -> the ``"__all__"`` sentinel
    (AR-M3). ``node`` is null, ``errors`` carries the one entry - NOT a top-level
    GraphQL error and never an ``IntegrityError`` / 500.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    existing = models.Item.objects.create(name="Dup", category=category)
    client = _login_with_perm("view_item_1", "add_item")

    response = _post_graphql(
        _CREATE_ITEM,
        client=client,
        variables={
            "d": {
                "name": existing.name,
                "categoryId": _global_id("products.category", category.pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItem"]
    assert result["node"] is None
    assert len(result["errors"]) == 1
    assert result["errors"][0]["field"] == "__all__"
    # No second row was written.
    assert models.Item.objects.filter(name="Dup", category=category).count() == 1


@pytest.mark.django_db(transaction=True)
def test_update_item_partial_collision_on_unique_constraint_changing_only_name():
    """AR-H2: a ``name``-only update colliding on ``unique_item_per_category`` -> ``"__all__"``.

    Two ``Item``s ``A`` / ``B`` under the SAME category; ``updateItem`` on ``A``
    changing only ``name`` -> ``B``. The unchanged (unprovided) ``category``
    co-participates in the composite constraint with the provided ``name``, so it is
    NOT dropped from the ``full_clean(exclude=...)`` set - the collision is caught
    before ``save()`` as a ``"__all__"``-keyed ``FieldError``, never an
    ``IntegrityError``. ``A``'s name is unchanged in the DB.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    item_a = models.Item.objects.create(name="A", category=category)
    models.Item.objects.create(name="B", category=category)
    client = _login_with_perm("staff_1", "change_item")

    response = _post_graphql(
        _UPDATE_ITEM,
        client=client,
        variables={"id": _global_id("products.item", item_a.pk), "d": {"name": "B"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItem"]
    assert result["node"] is None
    assert len(result["errors"]) == 1
    assert result["errors"][0]["field"] == "__all__"
    item_a.refresh_from_db()
    assert item_a.name == "A"


@pytest.mark.django_db(transaction=True)
def test_create_item_anonymous_is_denied_top_level_error_no_write():
    """AR-H3: an anonymous ``createItem`` is denied with a top-level error and no write.

    The default ``DjangoModelPermission`` denies a caller with no authenticated
    ``request.user`` (``is_authenticated == False``). The denial RAISES a top-level
    ``GraphQLError`` (in ``payload["errors"]``), NOT a field-keyed ``FieldError``
    envelope entry (spec-036 Decision 15) - and no row is written.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    before = models.Item.objects.count()

    response = _post_graphql(
        _CREATE_ITEM,
        variables={
            "d": {
                "name": "AnonWidget",
                "categoryId": _global_id("products.category", category.pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("errors"), payload
    # The denial RAISES on a non-null ``createItem(...): CreateItemPayload!`` field,
    # so GraphQL nulls the whole ``data`` - the authorization-failure surface, NOT a
    # ``FieldError`` envelope entry on a present payload.
    assert payload["data"] is None
    assert "Not authorized" in payload["errors"][0]["message"]
    assert models.Item.objects.count() == before
    assert not models.Item.objects.filter(name="AnonWidget").exists()


@pytest.mark.django_db(transaction=True)
def test_create_item_missing_model_perm_is_denied_no_write():
    """AR-H3: a caller lacking ``add_item`` is denied with a top-level error, no write.

    ``view_item_1`` holds only ``products.view_item`` (``create_users`` grants each
    ``view_*`` user only the matching ``view_*`` perm) and LACKS ``add_item``, so
    the default ``DjangoModelPermission`` denies the create - a top-level
    ``GraphQLError``, no row written. Isolates the model-perm codename denial from
    the anonymous case.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    client = _login("view_item_1")  # only products.view_item, no add_item
    before = models.Item.objects.count()

    response = _post_graphql(
        _CREATE_ITEM,
        client=client,
        variables={
            "d": {
                "name": "NoPermWidget",
                "categoryId": _global_id("products.category", category.pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("errors"), payload
    assert payload["data"] is None
    assert "Not authorized" in payload["errors"][0]["message"]
    assert models.Item.objects.count() == before
    assert not models.Item.objects.filter(name="NoPermWidget").exists()


@pytest.mark.django_db(transaction=True)
def test_visibility_scoped_update_delete_hidden_private_row_is_not_found():
    """Decision 10: a caller who holds the write perm but cannot SEE a private row gets not-found.

    ``seed_cascade_split`` gives ``item_under_private`` (a public Item under a
    PRIVATE category) and ``item_under_public``. A non-staff ``view_item_1`` user
    (granted ``change_item`` + ``delete_item``) cannot see ``item_under_private``
    (the ``ItemType.get_queryset`` cascade hides it through its private category),
    so the update / delete LOCATE misses -> a not-found ``FieldError`` on ``id``
    (indistinguishable from a genuinely-missing row, no existence leak). The write
    perm is HELD, isolating the visibility miss from an authorization denial; the
    same write succeeds for ``item_under_public``.
    """
    create_users(1)
    chain = seed_cascade_split()
    private_gid = _global_id("products.item", chain["item_under_private"].pk)
    public_gid = _global_id("products.item", chain["item_under_public"].pk)
    client = _login_with_perm("view_item_1", "change_item", "delete_item")

    # Hidden private row: update -> not-found FieldError on `id`, row unchanged.
    response = _post_graphql(
        _UPDATE_ITEM,
        client=client,
        variables={"id": private_gid, "d": {"name": "Renamed"}},
    )
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItem"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["id"]
    chain["item_under_private"].refresh_from_db()
    assert chain["item_under_private"].name == "zzz_item_under_private"

    # Hidden private row: delete -> not-found FieldError on `id`, row still present.
    response = _post_graphql(_DELETE_ITEM, client=client, variables={"id": private_gid})
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["deleteItem"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["id"]
    assert models.Item.objects.filter(pk=chain["item_under_private"].pk).exists()

    # Contrast: the SAME write succeeds for the visible public row.
    response = _post_graphql(
        _UPDATE_ITEM,
        client=client,
        variables={"id": public_gid, "d": {"name": "PublicRenamed"}},
    )
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItem"]
    assert result["errors"] == []
    assert result["node"] == {"name": "PublicRenamed"}


@pytest.mark.django_db(transaction=True)
def test_create_item_wrong_type_global_id_on_category_id_is_field_error():
    """AR-H4: a wrong-type ``GlobalID`` on ``categoryId`` -> ``FieldError`` on ``categoryId``.

    ``categoryId`` is fed a well-formed ``Item`` GlobalID (the wrong target model).
    The decode type-checks it against the relation's Django target (``Category``)
    and returns a ``FieldError`` keyed to the input field ``categoryId`` - never a
    cross-model pk lookup, never a raw ``DoesNotExist``, never a top-level
    ``GraphQLError``. ``node`` is null and no row is written.
    """
    create_users(1)
    seed_data(1)
    some_item = models.Item.objects.first()
    wrong_gid = _global_id("products.item", some_item.pk)
    client = _login_with_perm("view_item_1", "add_item")
    before = models.Item.objects.count()

    response = _post_graphql(
        _CREATE_ITEM,
        client=client,
        variables={"d": {"name": "WrongTypeWidget", "categoryId": wrong_gid}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItem"]
    assert result["node"] is None
    assert len(result["errors"]) == 1
    assert result["errors"][0]["field"] == "categoryId"
    assert models.Item.objects.count() == before
    assert not models.Item.objects.filter(name="WrongTypeWidget").exists()


@pytest.mark.django_db(transaction=True)
def test_update_item_wrong_type_global_id_on_id_is_field_error():
    """A wrong-type / unresolvable ``GlobalID`` on the ``updateItem`` ``id:`` -> ``FieldError`` on ``id``.

    The top-level ``id:`` is type-checked against the mutation's target model
    (``Item``), the same identity guard the typed ``DjangoNodeField`` applies: a
    well-formed ``Category`` GlobalID (the wrong model) - or a GlobalID naming an
    unregistered type - is rejected as a ``FieldError`` on ``id`` BEFORE any
    lookup, never silently coerced to a bare pk that would target the same-pk
    ``Item``. ``node`` is null and the row is untouched (spec-036 Decision 10 /
    finding-#1 hardening).
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    item = models.Item.objects.create(name="Untouched", category=category)
    client = _login_with_perm("staff_1", "change_item")

    # A well-formed Category GlobalID whose numeric pk collides with the Item's pk
    # is the dangerous case: a bare-pk coercion would silently hit this Item.
    wrong_gid = _global_id("products.category", item.pk)
    response = _post_graphql(
        _UPDATE_ITEM,
        client=client,
        variables={"id": wrong_gid, "d": {"name": "Renamed"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItem"]
    assert result["node"] is None
    assert len(result["errors"]) == 1
    assert result["errors"][0]["field"] == "id"
    item.refresh_from_db()
    assert item.name == "Untouched"

    # A GlobalID naming a type that resolves to nothing is rejected the same way.
    unresolvable_gid = _global_id("nope.nonexistent", item.pk)
    response = _post_graphql(
        _UPDATE_ITEM,
        client=client,
        variables={"id": unresolvable_gid, "d": {"name": "Renamed"}},
    )
    result = response.json()["data"]["updateItem"]
    assert result["node"] is None
    assert result["errors"][0]["field"] == "id"
    item.refresh_from_db()
    assert item.name == "Untouched"


@pytest.mark.django_db(transaction=True)
def test_delete_item_wrong_type_global_id_on_id_is_field_error():
    """A wrong-type ``GlobalID`` on the ``deleteItem`` ``id:`` -> ``FieldError`` on ``id``, no deletion.

    The same top-level ``id:`` type-check guards ``delete``: a ``Category``
    GlobalID with a pk that collides with a real ``Item`` does not delete that
    ``Item`` - it returns a ``FieldError`` on ``id`` and the row survives (spec-036
    Decision 10 / finding-#1 hardening).
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    item = models.Item.objects.create(name="Survivor", category=category)
    client = _login_with_perm("staff_1", "delete_item")

    wrong_gid = _global_id("products.category", item.pk)
    response = _post_graphql(_DELETE_ITEM, client=client, variables={"id": wrong_gid})
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["deleteItem"]
    assert result["node"] is None
    assert len(result["errors"]) == 1
    assert result["errors"][0]["field"] == "id"
    assert models.Item.objects.filter(pk=item.pk).exists()


@pytest.mark.django_db(transaction=True)
def test_create_item_relation_id_for_hidden_category_is_field_error():
    """feedback P1: a permitted writer cannot attach a `Category` they cannot SEE.

    `seed_cascade_split` gives a PRIVATE category. A non-staff `view_item_1` user
    (granted `add_item`) cannot see it (`CategoryType.get_queryset` hides private
    categories from non-staff), so `createItem(categoryId=<private cat gid>)` is a
    `FieldError` on `categoryId` - the relation id is resolved through the target's
    visibility `get_queryset`, never silently attached via the later `full_clean`
    FK check (which uses Django's default manager). The SAME create succeeds against
    the visible public category, isolating the visibility miss from the write perm
    (which is held throughout).
    """
    create_users(1)
    chain = seed_cascade_split()
    client = _login_with_perm("view_item_1", "add_item")
    before = models.Item.objects.count()

    # Hidden private category: FieldError on categoryId, no write.
    response = _post_graphql(
        _CREATE_ITEM,
        client=client,
        variables={
            "d": {
                "name": "AttachHidden",
                "categoryId": _global_id("products.category", chain["private_cat"].pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItem"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["categoryId"]
    assert models.Item.objects.count() == before
    assert not models.Item.objects.filter(name="AttachHidden").exists()

    # Visible public category: the same caller's same create succeeds.
    response = _post_graphql(
        _CREATE_ITEM,
        client=client,
        variables={
            "d": {
                "name": "AttachVisible",
                "categoryId": _global_id("products.category", chain["public_cat"].pk),
            },
        },
    )
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItem"]
    assert result["errors"] == []
    assert result["node"] == {
        "name": "AttachVisible",
        "category": {"name": chain["public_cat"].name},
    }


@pytest.mark.django_db(transaction=True)
def test_update_item_malformed_id_is_field_error_no_coercion_crash():
    """feedback #1: a malformed / raw-pk ``id:`` on `updateItem` -> `FieldError` on `id`, no crash.

    The ``id:`` is `ID!` and decoded server-side; a string that is not a well-formed
    GlobalID - a raw pk, or garbage - is a `FieldError` on ``id`` decided BEFORE any
    lookup, never coerced to a bare pk that an integer-pk model would raise a Django
    ``ValueError`` (top-level 500) on at ``.get(pk=...)``.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    item = models.Item.objects.create(name="Untouched", category=category)
    client = _login_with_perm("staff_1", "change_item")

    for bad_id in ("not-a-global-id", str(item.pk)):
        response = _post_graphql(
            _UPDATE_ITEM,
            client=client,
            variables={"id": bad_id, "d": {"name": "Renamed"}},
        )
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        result = payload["data"]["updateItem"]
        assert result["node"] is None
        assert [e["field"] for e in result["errors"]] == ["id"]
    item.refresh_from_db()
    assert item.name == "Untouched"


@pytest.mark.django_db(transaction=True)
def test_create_item_malformed_category_id_is_top_level_coercion_error():
    """feedback #7: a MALFORMED `categoryId` is a top-level coercion error, not a `FieldError`.

    Relation ids are typed `GlobalID` (not `ID!`), so Strawberry rejects a malformed
    value during argument coercion BEFORE the resolver runs - a top-level GraphQL
    error, `data` null. The in-band `FieldError` envelope is reserved for a
    well-formed-but-invalid / wrong-type / hidden relation id (the decode-time
    AR-H4 + visibility checks). This pins the boundary the spec documents.
    """
    create_users(1)
    seed_data(1)
    client = _login_with_perm("view_item_1", "add_item")

    response = _post_graphql(
        _CREATE_ITEM,
        client=client,
        variables={"d": {"name": "Malformed", "categoryId": "not-a-valid-global-id"}},
    )
    assert response.status_code == 200
    payload = response.json()
    # Top-level GraphQL error (variable coercion), NOT an in-band FieldError envelope.
    assert payload.get("errors"), payload
    assert payload["data"] is None
    assert not models.Item.objects.filter(name="Malformed").exists()


@pytest.mark.django_db(transaction=True)
def test_update_item_wellformed_id_uncoercible_node_id_is_not_found_no_crash():
    """CR-1: a well-formed ``Item`` ``id:`` carrying an uncoercible ``node_id`` -> not-found, no 500.

    Distinct from the malformed case above: this ``id`` IS a well-formed
    ``products.item`` GlobalID, so it passes decode and the AR-H4 type-check - but
    its ``node_id`` (``"abc"``) is not a valid integer-pk literal. The ``id`` is
    coerced through the model's pk field and, failing, treated as not-found - a
    ``FieldError`` on ``id`` (indistinguishable from a missing row), NEVER reaching
    ``.get(pk="abc")`` where Django would raise a top-level ``ValueError`` (500) and
    leak the pk column type. Pins the ``coerce_lookup_id`` UNCOERCIBLE_PK branch
    over the live HTTP stack (the malformed test above exercises only DECODE_FAILED,
    the wrong-type test only WRONG_MODEL).
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    item = models.Item.objects.create(name="Untouched", category=category)
    client = _login_with_perm("staff_1", "change_item")

    bad_id = str(relay.GlobalID(type_name="products.item", node_id="abc"))
    response = _post_graphql(
        _UPDATE_ITEM,
        client=client,
        variables={"id": bad_id, "d": {"name": "Renamed"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItem"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["id"]
    item.refresh_from_db()
    assert item.name == "Untouched"


@pytest.mark.django_db(transaction=True)
def test_create_item_wellformed_relation_id_uncoercible_node_id_is_field_error_no_crash():
    """CR-1: a well-formed ``Category`` ``categoryId`` with an uncoercible ``node_id`` -> ``FieldError``.

    The relation analogue of the case above. ``categoryId`` is typed ``GlobalID``,
    and a well-formed ``products.category`` GlobalID carrying ``node_id="abc"``
    passes both Strawberry argument coercion (it IS a valid GlobalID, unlike the
    top-level-error malformed case) and the AR-H4 type-check (it IS a Category id) -
    but ``"abc"`` is not a valid integer pk. It is coerced and mapped to the uniform
    relation ``FieldError`` on ``categoryId``, never reaching ``filter(pk__in=["abc"])``
    where Django would raise a top-level ``ValueError`` (500). No row is written.
    """
    create_users(1)
    seed_data(1)
    client = _login_with_perm("view_item_1", "add_item")
    before = models.Item.objects.count()

    bad_cat = str(relay.GlobalID(type_name="products.category", node_id="abc"))
    response = _post_graphql(
        _CREATE_ITEM,
        client=client,
        variables={"d": {"name": "UncoercibleRel", "categoryId": bad_cat}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItem"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["categoryId"]
    assert models.Item.objects.count() == before
    assert not models.Item.objects.filter(name="UncoercibleRel").exists()


# A syntactically-valid but absurdly large integer ``node_id``: ``to_python`` casts
# it to a Python int cleanly (no range check), so it would reach the ORM where
# SQLite's parameter binding raises a raw ``OverflowError``. The pk field's
# backend range validators reject it at coercion instead -> uncoercible (not found).
_ABSURD_INTEGER_NODE_ID = "9" * 400


@pytest.mark.django_db(transaction=True)
def test_create_item_relation_id_absurd_huge_pk_is_field_error_no_overflow():
    """An out-of-range ``Category`` relation pk -> ``FieldError`` on ``categoryId``, never an OverflowError 500.

    A well-formed ``products.category`` GlobalID whose ``node_id`` is an absurd
    integer (``"9" * 400``) passes decode and the AR-H4 type-check. ``to_python``
    casts it to a Python int without range-checking, so before the fix it reached
    the relation visibility ``filter(pk__in=[...])``, where SQLite raises a top-level
    ``OverflowError`` (500). The shared pk coercer now runs the pk field's backend
    range validators, so the out-of-range value is uncoercible -> the uniform
    relation ``FieldError`` on ``categoryId``, no query issued, no row written.
    """
    create_users(1)
    seed_data(1)
    client = _login_with_perm("view_item_1", "add_item")
    before = models.Item.objects.count()

    huge_cat = str(relay.GlobalID(type_name="products.category", node_id=_ABSURD_INTEGER_NODE_ID))
    response = _post_graphql(
        _CREATE_ITEM,
        client=client,
        variables={"d": {"name": "HugePk", "categoryId": huge_cat}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItem"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["categoryId"]
    assert models.Item.objects.count() == before
    assert not models.Item.objects.filter(name="HugePk").exists()


@pytest.mark.django_db(transaction=True)
def test_update_item_id_absurd_huge_pk_is_not_found_no_overflow():
    """An out-of-range top-level ``id:`` -> not-found ``FieldError`` on ``id``, consistent with the relation path.

    The top-level ``updateItem`` ``id:`` analogue. ``.get(pk=<huge>)`` happens to
    return ``DoesNotExist`` on SQLite (not an overflow), so this path already
    behaved; the coercer change makes it decide uncoercible -> not-found at the same
    coercion step the relation path uses, BEFORE any query, so both paths handle an
    out-of-range pk identically. The item is untouched.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    item = models.Item.objects.create(name="Untouched", category=category)
    client = _login_with_perm("staff_1", "change_item")

    huge_id = str(relay.GlobalID(type_name="products.item", node_id=_ABSURD_INTEGER_NODE_ID))
    response = _post_graphql(
        _UPDATE_ITEM,
        client=client,
        variables={"id": huge_id, "d": {"name": "Renamed"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItem"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["id"]
    item.refresh_from_db()
    assert item.name == "Untouched"


@pytest.mark.django_db(transaction=True)
def test_g2_mutation_response_keeps_relation_with_bounded_query_count():
    """G2 behavioral tier (AR-M7): a mutation response selecting a relation has no N+1, no lazy query.

    Discharges the ``spec-035`` G2 live-test handoff at the BEHAVIORAL tier: a
    ``createItem`` response selecting ``node { name category { name } }`` is wrapped
    in ``CaptureQueriesContext``. The post-write re-fetch is one optimizer-planned
    ``products_item`` queryset that keeps ``select_related`` / ``prefetch_related``
    for the ``category`` relation, so exactly ONE ``products_category`` query
    services it (no N+1) and no deferred-field lazy refetch fires (a regression
    would show as an extra ``products_item`` SELECT after the re-fetch).

    The absolute bounded count is DERIVED from a real run (BUILD.md forbids
    guessing it). A write needs an authorized caller, so the count includes the
    auth machinery; each query is annotated below (the per-query breakdown is
    pinned in the inline comment beside the count assertion). The exact
    ``only_fields`` / ``deferred_loading`` plan state is
    the package mirror's job (``tests/optimizer/test_walker.py``, AR-M7) - this
    live tier pins only the load-bearing behavior, NOT a column-exact SQL snapshot.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    client = _login_with_perm("view_item_1", "add_item")

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            _CREATE_ITEM,
            client=client,
            variables={
                "d": {
                    "name": "G2Widget",
                    "categoryId": _global_id("products.category", category.pk),
                },
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItem"]
    assert result["errors"] == []
    # The relation renders WITHOUT an error (planned, not a broken / lazy FK).
    assert result["node"] == {"name": "G2Widget", "category": {"name": category.name}}

    # Bounded count = 12, derived from a real run (stable across runs):
    #   BEGIN + COMMIT                                    = 2 (the resolver's one
    #                                                         transaction.atomic())
    #   session + auth_user + user_perms + group_perms    = 4 (authorized-caller
    #                                                         machinery)
    #   relation-id visibility decode: products_category  = 1 (feedback P1: the
    #                                                         categoryId is resolved
    #                                                         through CategoryType.
    #                                                         get_queryset before write)
    #   validate_constraints: category-FK + item-unique   = 2 (full_clean before save)
    #   INSERT products_item                              = 1
    #   post-write re-fetch: products_item                = 1 (optimizer-planned)
    #   the `category` relation:  products_category       = 1 (select_related/prefetch;
    #                                                         no N+1, no lazy refetch)
    sql = [query["sql"] for query in captured]
    assert len(captured) == 12, sql
    # G2 load-bearing property: the re-fetch reads the item once and the relation
    # once - a deferred-field lazy refetch or an N+1 would add EXTRA products SELECTs.
    item_selects = [
        s for s in sql if "products_item" in s.lower() and s.strip().upper().startswith("SELECT")
    ]
    category_selects = [
        s
        for s in sql
        if "products_category" in s.lower() and s.strip().upper().startswith("SELECT")
    ]
    # One re-fetch SELECT for the item, plus the validate_constraints SELECT-1.
    assert len([s for s in item_selects if "select 1" not in s.lower()]) == 1, sql
    # TWO real category SELECTs (plus the validate_constraints SELECT-1): the
    # relation-id visibility decode (feedback P1) and the post-write re-fetch
    # relation - neither is an N+1 / lazy refetch.
    assert len([s for s in category_selects if "select 1" not in s.lower()]) == 2, sql


@pytest.mark.django_db
def test_emitted_globalid_is_model_anchored():
    """An emitted ``node { id }`` decodes to the Django model label, not the type name.

    Under the ``0.0.9`` model-label default, ``ItemType``'s ``GlobalID``
    carries ``products.item:<pk>`` (``models.Item._meta.label_lower``), not the
    GraphQL type name ``ItemType``. Decode the API-emitted ``id`` via
    ``relay.GlobalID.from_id`` and assert the model-label payload.

    Runs as ``staff_1`` so the first item is visible regardless of its
    (``seed_data``-randomized) ``is_private`` / category privacy under the
    activated cascade hooks (spec-034 Slice 4); the GlobalID emit/decode subject
    is orthogonal to visibility.
    """
    seed_data(1)
    client = _staff_client()
    item = models.Item.objects.order_by("id").first()
    response = _post_graphql(
        "query { allItems { edges { node { id name } } } }",
        client=client,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    nodes = [edge["node"] for edge in payload["data"]["allItems"]["edges"]]
    emitted = next(node for node in nodes if node["name"] == item.name)
    parsed = relay.GlobalID.from_id(emitted["id"])
    assert parsed.type_name == models.Item._meta.label_lower
    assert parsed.node_id == str(item.pk)


@pytest.mark.django_db
def test_globalid_filter_round_trip():
    """THE headline ``0.0.9`` workflow: feed an emitted GlobalID straight back as a filter.

    Take the model-label ``id`` the products API just emitted for one item and
    feed it back verbatim as ``filter: { id: { exact: "<that id>" } }``; the
    strategy-aware filter ([Decision 13]) accepts the model-label payload it now
    emits and returns exactly that one row. Uses the API-emitted id (not a
    reconstructed one) so the test proves true emit -> filter symmetry.

    Runs as ``staff_1`` so the target item is visible for both the emit and the
    filter-round-trip under the activated cascade hooks (spec-034 Slice 4); the
    emit -> filter symmetry subject is orthogonal to visibility.
    """
    seed_data(1)
    client = _staff_client()
    target = models.Item.objects.order_by("id").first()
    emit_response = _post_graphql(
        "query { allItems { edges { node { id name } } } }",
        client=client,
    )
    assert emit_response.status_code == 200
    emit_payload = emit_response.json()
    assert "errors" not in emit_payload, emit_payload
    emitted_nodes = [edge["node"] for edge in emit_payload["data"]["allItems"]["edges"]]
    emitted = next(node for node in emitted_nodes if node["name"] == target.name)
    emitted_id = emitted["id"]

    _assert_graphql_data(
        f'query {{ allItems(filter: {{ id: {{ exact: "{emitted_id}" }} }}) '
        "{ edges { node { id name } } } }",
        {"allItems": {"edges": [{"node": {"id": emitted_id, "name": target.name}}]}},
        client=client,
    )


@pytest.mark.django_db
def test_type_strategy_opt_out_reproduces_type_name():
    """``RELAY_GLOBALID_STRATEGY = "type"`` opts back into the GraphQL-type-name payload.

    Ordering matters here: the override is applied *before*
    ``_reload_products_project_schema()`` finalizes the schema (the fakeshop
    fixtures reload at finalization, so a strategy override must precede the
    reload or the test silently exercises the default schema). Under the ``type``
    strategy ``ItemType``'s ``id`` reproduces the GraphQL type name ``ItemType``
    (== ``ItemType.__name__``, no ``Meta.name``), NOT the model label. The
    per-test autouse fixture re-reloads the default-strategy schema for siblings.

    Runs as ``staff_1`` so the first item is visible regardless of its
    (``seed_data``-randomized) privacy under the activated cascade hooks
    (spec-034 Slice 4); the strategy opt-out subject is orthogonal to visibility.
    """
    seed_data(1)
    client = _staff_client()
    item = models.Item.objects.order_by("id").first()
    with override_settings(
        DJANGO_STRAWBERRY_FRAMEWORK={"RELAY_GLOBALID_STRATEGY": "type"},
    ):
        _reload_products_project_schema()
        response = _post_graphql(
            "query { allItems { edges { node { id name } } } }",
            client=client,
        )
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        nodes = [edge["node"] for edge in payload["data"]["allItems"]["edges"]]
        emitted = next(node for node in nodes if node["name"] == item.name)
        parsed = relay.GlobalID.from_id(emitted["id"])
        assert parsed.type_name == "ItemType"
        assert parsed.node_id == str(item.pk)


@pytest.mark.django_db
def test_products_optimizer_merges_duplicate_root_field_nodes_over_http():
    """Re-pinned through the connection wrapper: duplicate-root-field merge holds.

    The two `allItems` connection selections still merge into one node set (each
    `node` carries both `name` and `category { name }`) issuing exactly ONE
    `allItems` slice query, and NO COUNT runs (products declare no
    `Meta.connection`). Under the activated cascade hooks (spec-034 Slice 4) the
    forward FK `item.category` no longer plans `select_related` - `CategoryType`
    now defines a custom `get_queryset`, so the optimizer downgrades it to a
    windowed `Prefetch` (the shipped `get_queryset` -> `Prefetch` rule). The
    merged shape is therefore a deterministic 2 products queries - one `allItems`
    slice + one `category` prefetch, no inter-products JOIN - and an unmerged
    shape would issue two item slices instead of one. Run anonymously (no auth
    queries pollute the count); the cascade narrows rows to the anonymously
    visible set (public items under public categories), so the expected rows are
    derived from the equivalent post-cascade ORM query (API == ORM), keeping the
    pin robust across `seed_data`'s random Item privacy. The appended
    deterministic `ORDER BY pk` matches `.order_by("id")` (`id` IS the pk).
    """
    seed_data(1)
    expected = [
        {"node": {"name": item.name, "category": {"name": item.category.name}}}
        for item in models.Item.objects.select_related("category")
        .filter(is_private=False, category__is_private=False)
        .order_by("id")
    ]

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allItems { edges { node { name } } }
              allItems { edges { node { category { name } } } }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"] == {"allItems": {"edges": expected}}
    # One allItems slice (the merge) + one category Prefetch (the hook downgrade),
    # no COUNT, no inter-products JOIN.
    assert len(captured) == 2, [query["sql"] for query in captured]
    item_slices = [q for q in captured if "products_item" in q["sql"].lower()]
    assert len(item_slices) == 1, [q["sql"] for q in captured]
    assert any("products_category" in q["sql"].lower() for q in captured)
    assert not any(
        "products_item" in q["sql"].lower()
        and "products_category" in q["sql"].lower()
        and "join" in q["sql"].lower()
        for q in captured
    )


@pytest.mark.django_db
def test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http():
    """Re-pinned through the connection wrapper: depth-2 reverse-FK prefetch holds.

    `allCategories` is a connection (one planned categories slice query), and
    `items` / `entries` stay LIST relations (`{ name }`, not `itemsConnection`)
    - the depth-2 reverse-FK prefetch chain the test pins is structurally
    unchanged: 1 categories slice + 1 `items` prefetch + 1 `entries` prefetch =
    3 queries, no COUNT. The activated cascade hooks (spec-034 Slice 4) do NOT
    add per-row queries - their `__in` subqueries compile inline (Decision 7) -
    so the count stays a fixed 3.

    What the cascade DOES change is row VISIBILITY: run anonymously, the three
    levels narrow to the cascade-visible set (public categories; non-private
    items under them; entries passing the full Entry -> Item -> Category /
    Entry -> Property -> Category chain). Counts are therefore derived from the
    equivalent post-cascade ORM queries (API == ORM), keeping the pin robust
    across `seed_data`'s random Item/Entry privacy. The deterministic Category
    `% 2` split keeps the public-category count well under the
    `relay_max_results` cap.
    """
    seed_data(1)
    visible_categories = models.Category.objects.filter(is_private=False)
    visible_items = models.Item.objects.filter(is_private=False, category__is_private=False)
    visible_entries = models.Entry.objects.filter(
        is_private=False,
        item__is_private=False,
        item__category__is_private=False,
        property__is_private=False,
        property__category__is_private=False,
    )
    assert visible_categories.count() < _RELAY_MAX_RESULTS, (
        "fixture must stay under the cap so the full-set assertion is not silently truncated"
    )

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allCategories {
                edges {
                  node {
                    name
                    items {
                      name
                      entries { value }
                    }
                  }
                }
              }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    categories = [edge["node"] for edge in payload["data"]["allCategories"]["edges"]]
    items = [item for category in categories for item in category["items"]]
    entries = [entry for item in items for entry in item["entries"]]
    assert len(categories) == visible_categories.count()
    assert len(items) == visible_items.count()
    assert len(entries) == visible_entries.count()
    assert len(captured) == 3, [query["sql"] for query in captured]
    assert "products_category" in captured[0]["sql"]
    assert "products_item" in captured[1]["sql"]
    assert "products_entry" in captured[2]["sql"]


# The connection caps an un-paginated default page (and any explicit ``first:``)
# at ``relay_max_results``; Strawberry rejects a ``first:`` above it outright.
# 100 is Strawberry's default ``StrawberryConfig.relay_max_results``; the fakeshop
# schema sets no override. Used by the staff full-set cascade pin (staff sees all
# rows, capped at 100) and the reverse-FK depth-2 pin's under-cap precondition.
# The forward-FK depth-2 pin below runs anonymously under the activated cascade
# (spec-034 Slice 4): the cascade narrows the visible entry set well under the
# cap, so that pin no longer exercises the cap boundary.
_RELAY_MAX_RESULTS = 100


@pytest.mark.django_db
def test_products_optimizer_selects_nested_forward_fk_depth_2_over_http():
    """Re-pinned for the activated cascade: depth-2 forward-FK plans a Prefetch chain.

    Before spec-034 Slice 4 this query planned a single `select_related(
    "item__category")` JOIN. With the cascade hooks active, `ItemType` and
    `CategoryType` both define a custom `get_queryset`, so the optimizer
    downgrades each forward FK in the `item -> category` chain to a windowed
    `Prefetch` (the shipped `get_queryset` -> `Prefetch` rule). The traversal is
    therefore a deterministic 3 products queries - one `allEntries` slice + one
    `item` prefetch + one `category` prefetch - with NO inter-products JOIN, and
    the cascade adds zero round-trips (its `__in` subqueries compile inline,
    Decision 7). Run anonymously (no auth queries pollute the count); the cascade
    narrows the visible entries to those passing the full
    Entry -> Item -> Category / Entry -> Property -> Category chain, well under the
    `relay_max_results` cap, so the expected page is the entire visible set in pk
    order, derived from the equivalent post-cascade ORM query (API == ORM, robust
    across `seed_data`'s random Item/Entry/Property privacy). The appended
    `ORDER BY pk` matches `.order_by("id")` (`id` IS the pk).
    """
    seed_data(1)
    visible_entries = (
        models.Entry.objects.select_related("item__category")
        .filter(
            is_private=False,
            item__is_private=False,
            item__category__is_private=False,
            property__is_private=False,
            property__category__is_private=False,
        )
        .order_by("id")
    )
    assert visible_entries.count() <= _RELAY_MAX_RESULTS, (
        "cascade-narrowed visible set must stay under the cap for the full-set assertion"
    )
    expected = [
        {
            "node": {
                "id": _global_id(models.Entry._meta.label_lower, entry.pk),
                "value": entry.value,
                "item": {
                    "id": _global_id(models.Item._meta.label_lower, entry.item_id),
                    "name": entry.item.name,
                    "category": {
                        "id": _global_id(
                            models.Category._meta.label_lower,
                            entry.item.category_id,
                        ),
                        "name": entry.item.category.name,
                    },
                },
            },
        }
        for entry in visible_entries
    ]

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            """
            query {
              allEntries {
                edges {
                  node {
                    id
                    value
                    item {
                      id
                      name
                      category { id name }
                    }
                  }
                }
              }
            }
            """,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    assert payload["data"] == {"allEntries": {"edges": expected}}
    # Prefetch chain: entry slice + item prefetch + category prefetch, no COUNT.
    assert len(captured) == 3, [query["sql"] for query in captured]
    assert "products_entry" in captured[0]["sql"]
    assert "products_item" in captured[1]["sql"]
    assert "products_category" in captured[2]["sql"]
    # The cascade composed inline (zero added round-trips) and the forward FK
    # downgraded to a Prefetch chain rather than a select_related JOIN.
    all_sql = " ".join(query["sql"] for query in captured)
    assert "IN (SELECT" in all_sql
    assert not any(
        "products_entry" in q["sql"].lower()
        and "products_item" in q["sql"].lower()
        and "join" in q["sql"].lower()
        for q in captured
    )


@pytest.mark.django_db
def test_products_categories_filter_by_name_exact_as_staff():
    """A staff user clears ``CategoryFilter.check_name_permission`` and filters by name."""
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    _assert_graphql_data(
        f"query {{ allCategories(filter: {{ name: {{ exact: {json.dumps(category.name)} }} }}) "
        "{ edges { node { name } } } }",
        {"allCategories": {"edges": [{"node": {"name": category.name}}]}},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_categories_filter_by_name_denied_for_anonymous():
    """An anonymous user filtering by ``Category.name`` (exact) is rejected by the gate."""
    seed_data(1)
    category = models.Category.objects.order_by("id").first()
    response = _post_graphql(
        f"query {{ allCategories(filter: {{ name: {{ exact: {json.dumps(category.name)} }} }}) "
        "{ edges { node { name } } } }",
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
        f"query {{ allCategories(filter: {{ name: {{ iContains: {json.dumps(category.name[:2])} }} }}) "
        "{ edges { node { name } } } }",
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
        f"query {{ allItems(filter: {{ category: {{ name: {{ exact: {json.dumps(category.name)} }} }} }}) "
        "{ edges { node { name } } } }",
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

    Picks two PUBLIC categories so they are visible under the activated cascade
    (spec-034 Slice 4) - anonymous sees only `is_private=False` categories (the
    deterministic `% 2` split makes ~half private), and the GlobalID `in`-decode
    subject is orthogonal to which specific rows are chosen.
    """
    seed_data(1)
    categories = list(models.Category.objects.filter(is_private=False).order_by("id")[:2])
    gids = ", ".join(
        f'"{relay.GlobalID(type_name=models.Category._meta.label_lower, node_id=str(category.pk))}"'
        for category in categories
    )
    _assert_graphql_data(
        f"query {{ allCategories(filter: {{ id: {{ in: [{gids}] }} }}) "
        "{ edges { node { name } } } }",
        {
            "allCategories": {
                "edges": [{"node": {"name": category.name}} for category in categories],
            },
        },
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
        {"node": {"name": name}}
        for name in models.Category.objects.filter(name__startswith=prefix)
        .order_by("id")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allCategories(filter: {{ name: {{ startsWith: "{prefix}" }} }}) '
        "{ edges { node { name } } } }",
        {"allCategories": {"edges": expected}},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_items_filter_by_related_category_global_id():
    """``Item.category`` ``RelatedFilter`` traversal via the nested GlobalID input.

    Filters to a PUBLIC category (visible anonymously under the activated cascade,
    spec-034 Slice 4). The cascade narrows the anonymous result to that category's
    ``is_private=False`` items, so the expected rows are derived from the
    equivalent post-cascade ORM query (API == ORM) - the ``RelatedFilter`` content
    subject composed with the cascade's row narrowing.
    """
    seed_data(1)
    category = models.Category.objects.filter(is_private=False).order_by("id").first()
    gid = str(
        relay.GlobalID(type_name=models.Category._meta.label_lower, node_id=str(category.pk)),
    )
    expected = [
        {"node": {"name": name}}
        for name in models.Item.objects.filter(category=category, is_private=False)
        .order_by("id")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allItems(filter: {{ category: {{ id: {{ exact: "{gid}" }} }} }}) '
        "{ edges { node { name } } } }",
        {"allItems": {"edges": expected}},
    )


# ---------------------------------------------------------------------------
# Ordering (DONE-028-0.0.8) - wired in ``apps.products.schema`` via the
# ``orderset_class`` Meta key and the ``order_input_type(...)`` resolver
# arguments. Expectations compare against the equivalent ORM ``order_by`` so
# the GraphQL ``ORDER BY`` and the expected sequence share one DB collation
# (robust across Faker-generated values and name ties).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_products_items_order_by_name_asc():
    """``orderBy: [{ name: ASC }]`` sorts items by name ascending (Item has no order gate).

    Runs anonymously, so the activated cascade (spec-034 Slice 4) narrows to
    non-private items under non-private categories before ordering; the expected
    rows are derived from the equivalent post-cascade ORM query (API == ORM), the
    ordering subject composed with the cascade's row narrowing.
    """
    seed_data(1)
    expected = [
        {"node": {"name": name}}
        for name in models.Item.objects.filter(is_private=False, category__is_private=False)
        .order_by("name")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        "query { allItems(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
        {"allItems": {"edges": expected}},
    )


@pytest.mark.django_db
def test_products_items_order_by_name_desc():
    """``orderBy: [{ name: DESC }]`` sorts items by name descending.

    Anonymous, so the cascade-narrowed visible set (non-private items under
    non-private categories) is ordered; expected rows come from the equivalent
    post-cascade ORM query (spec-034 Slice 4).
    """
    seed_data(1)
    expected = [
        {"node": {"name": name}}
        for name in models.Item.objects.filter(is_private=False, category__is_private=False)
        .order_by("-name")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        "query { allItems(orderBy: [{ name: DESC }]) { edges { node { name } } } }",
        {"allItems": {"edges": expected}},
    )


@pytest.mark.django_db
def test_products_categories_order_by_name_denied_for_anonymous():
    """``CategoryOrder.check_name_permission`` rejects an anonymous order-by-name.

    Active-input-only: the gate fires because the ``orderBy`` input names the
    gated ``name`` field - mirroring ``CategoryFilter.check_name_permission``
    on the filter side.
    """
    seed_data(1)
    response = _post_graphql(
        "query { allCategories(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_categories_order_by_name_as_staff():
    """A staff user clears the order-by-name gate and gets categories sorted by name."""
    seed_data(1)
    expected = [
        {"node": {"name": name}}
        for name in models.Category.objects.order_by("name").values_list("name", flat=True)
    ]
    _assert_graphql_data(
        "query { allCategories(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
        {"allCategories": {"edges": expected}},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_items_order_by_related_category_name_denied_for_anonymous():
    """A child ``RelatedOrder`` permission gate fires through the live API."""
    seed_data(1)
    response = _post_graphql(
        """
        query {
          allItems(orderBy: [{ category: { name: ASC } }]) {
            edges { node { name } }
          }
        }
        """,
    )
    payload = response.json()
    assert "errors" in payload, payload
    assert "staff user" in payload["errors"][0]["message"]


@pytest.mark.django_db
def test_products_items_order_by_related_category_name_as_staff():
    """Nested ``RelatedOrder`` input sorts by the child order field.

    Each item's category is distinct (one item per category at
    ``seed_data(1)``) and category names are unique provider names, so
    ``category__name`` is a total order and the connection's appended
    deterministic ``ORDER BY pk`` tiebreaker is a no-op against the ORM
    ``order_by("category__name")`` expectation.
    """
    seed_data(1)
    expected = [
        {"node": {"name": item.name, "category": {"name": item.category.name}}}
        for item in models.Item.objects.select_related("category").order_by("category__name")
    ]
    _assert_graphql_data(
        """
        query {
          allItems(orderBy: [{ category: { name: ASC } }]) {
            edges { node { name category { name } } }
          }
        }
        """,
        {"allItems": {"edges": expected}},
        client=_staff_client(),
    )


@pytest.mark.django_db
def test_products_items_filter_and_order_compose():
    """``filter:`` narrows rows then ``orderBy:`` arranges them (filter -> order chain).

    Filters items to one category via the own-PK GlobalID ``RelatedFilter``
    (no gate on ``id``) and orders the survivors by ``name`` (no gate on
    ``Item.name``), so the whole query runs anonymously.

    Uses a PUBLIC category (visible anonymously) and derives the expected rows
    from the equivalent post-cascade ORM query - the activated cascade (spec-034
    Slice 4) narrows the anonymous result to that category's ``is_private=False``
    items, on top of which the filter -> order chain runs.
    """
    seed_data(1)
    category = models.Category.objects.filter(is_private=False).order_by("id").first()
    gid = str(
        relay.GlobalID(type_name=models.Category._meta.label_lower, node_id=str(category.pk)),
    )
    expected = [
        {"node": {"name": name}}
        for name in models.Item.objects.filter(category=category, is_private=False)
        .order_by("name")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allItems(filter: {{ category: {{ id: {{ exact: "{gid}" }} }} }}, '
        "orderBy: [{ name: ASC }]) { edges { node { name } } } }",
        {"allItems": {"edges": expected}},
    )


# ---------------------------------------------------------------------------
# Nested relation-connection windowed-prefetch coverage (spec-033 Slice 6,
# DoD item 10). The reverse-FK windowed nested-connection shape the M2M-only
# library graph cannot express live: ``Category.items`` synthesizes an
# ``itemsConnection`` sibling (both ``CategoryType`` and ``ItemType`` are
# Relay-Node-shaped, so the ``DONE-032-0.0.9`` implicit ``"both"`` default made
# it), and Slices 1-2 plan it as a single windowed ``Prefetch``.
# ---------------------------------------------------------------------------

# itemsConnection carries ONLY ``first:`` -- a ``filter:`` / ``orderBy:`` sidecar
# on a NESTED connection diverts it to the per-parent fallback (Decision 6),
# which would issue one query per parent category (count scaling with parent
# cardinality) instead of the single windowed prefetch. Selecting only ``first:``
# pins the windowed path.
_CATEGORIES_ITEMS_CONNECTION_QUERY = """
query {
  allCategories {
    edges {
      node {
        name
        itemsConnection(first: 2) {
          edges { node { name } }
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
def test_products_categories_items_connection_fixed_query_count():
    """The nested reverse-FK ``itemsConnection`` resolves in a FIXED query count.

    Runs the same ``allCategories { edges { node { itemsConnection(first: 2)
    { edges { node } } } } }`` query under two seed cardinalities and asserts
    the captured query count is EQUAL (and absolutely small) across both -- the
    N+1 disproof. The windowed path is a FIXED 2 queries (one ``allCategories``
    slice + one windowed ``itemsConnection`` prefetch covering every category's
    page). A per-parent fallback issues at least one query per parent and scales
    with the number of ITEMS under ``first: 2``, so it neither stays equal across
    the two seedings nor lands at 2. Both seedings hold the parent-category count
    fixed and grow items-per-category, so the equality rules out a per-child N+1
    and the absolute ``== 2`` rules out the item-scaling fallback.

    Under the activated cascade (spec-034 Slice 4) this query runs anonymously,
    so the cascade narrows the result to the public categories (the deterministic
    ``% 2`` split, ~half of the seeded providers) and the windowed
    ``itemsConnection`` prefetch child carries ``ItemType``'s cascade too (only
    non-private items). That is exactly the interaction this pin must prove
    query-stable: the cascade's ``__in`` subqueries compile inline (Decision 7),
    so the count stays a FIXED 2 even with the hooks active. The membership check
    confirms each returned ``itemsConnection`` page is its own parent's window
    (every returned item belongs to that category, ``first: 2`` honoured).

    ``itemsConnection`` carries only ``first:`` (no sidecars) so it window-plans
    rather than falling back (Decision 6). Both seedings stay well under the
    ``relay_max_results`` cap.
    """

    def _run(seed_count: int) -> int:
        delete_data("everything")
        seed_data(seed_count)
        with CaptureQueriesContext(connection) as captured:
            response = _post_graphql(_CATEGORIES_ITEMS_CONNECTION_QUERY)
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        edges = payload["data"]["allCategories"]["edges"]
        # Each category node's itemsConnection is its OWN windowed page: every
        # returned item belongs to that category and the page honours first: 2.
        for edge in edges:
            node = edge["node"]
            category = models.Category.objects.get(name=node["name"])
            item_names = {ie["node"]["name"] for ie in node["itemsConnection"]["edges"]}
            assert len(item_names) <= 2
            assert item_names <= set(
                category.items.values_list("name", flat=True),
            )
        return len(captured)

    one_item_each = _run(1)
    three_items_each = _run(3)

    # Load-bearing: count is equal across the two parent cardinalities (no N+1).
    assert one_item_each == three_items_each
    # Strengthening: the empirically-derived windowed fixed count (1 allCategories
    # slice query + 1 windowed itemsConnection prefetch); a fallback issues at
    # least one query per parent and scales with items (measured ~52 / ~102 here).
    assert three_items_each == 2


# Slice 6 (spec-033) deliberately adds NO Meta.connection opt-in on the four
# products types (no totalCount; minimal cookbook-mirror conversion) and NO root
# node(id:) / nodes(ids:) entry points (those stay TODO-BETA-052-0.1.5).


# =============================================================================
# Live cascade-permission HTTP coverage (spec-034 Slice 4). The four products
# get_queryset hooks are now active in apps/products/schema.py. Real permission
# users only - every test's FIRST line is `create_users(1)` (per AGENTS.md / card
# DoD: never mock info.context.user). Exercises the 2-deep
# Entry -> Item -> Category / Entry -> Property -> Category chain.
#
# Each test seeds the private/public split it needs as a dedicated ORM chain
# AFTER `create_users(1)` / `seed_data(N)`, so the assertions are deterministic
# regardless of `seed_data`'s random Item/Entry `is_private` assignment (the
# Category/Property split is the deterministic `% 2` alternation; Item/Entry are
# `random.choice`). The hooks resolve the user from `info.context.request.user`
# (the Strawberry-Django context shape; see schema.py), so these run real logins.
# =============================================================================


def _login(username: str) -> Client:
    """Log in a seeded ``create_users(1)`` user by username."""
    client = Client()
    client.force_login(get_user_model().objects.get(username=username))
    return client


@pytest.mark.django_db
def test_cascade_anonymous_sees_no_entries_under_private_categories():
    """The 2-deep live pin: a private Category hides its Items' Entries from anonymous.

    Seeds a private Category with a public Item carrying a public Entry (via a
    public Property under that same private Category); an anonymous
    ``allEntries`` request returns no entry whose item's category is private -
    the cascade reaches Entry -> Item -> Category. The fully-public control entry
    IS returned, proving narrowing (not a blanket empty result).
    """
    create_users(1)
    chain = seed_cascade_split()

    response = _post_graphql(
        """
        query {
          allEntries {
            edges { node { value item { name category { name } } } }
          }
        }
        """,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    nodes = [edge["node"] for edge in payload["data"]["allEntries"]["edges"]]
    category_names = {node["item"]["category"]["name"] for node in nodes}
    values = {node["value"] for node in nodes}
    # The cascade hides the entry whose item's category is private...
    assert chain["private_cat"].name not in category_names
    assert chain["entry_under_private"].value not in values
    # ...but the fully-public control entry is still visible (narrowing, not empty).
    assert chain["entry_under_public"].value in values


@pytest.mark.django_db
def test_cascade_view_item_user_respects_category_visibility():
    """A ``view_item`` user only sees Items under a visible Category; nested ``category`` never errors.

    The ``view_item`` branch cascades after its ``is_private=False`` filter
    (feedback H1), so it is coherent with the relation it exposes: a non-staff
    viewer cannot see an Item whose non-null ``category`` target their own hooks
    hide. ``item_under_private`` (public Item under the PRIVATE category) is
    therefore DROPPED for this user, while ``item_under_public`` survives. Because
    every surviving Item's ``category`` is itself visible, selecting the non-null
    ``category { name }`` resolves cleanly instead of raising
    ``RelatedObjectDoesNotExist`` ("Item has no category") the no-cascade branch
    produced. The drop is the cascade, not a resolver error.
    """
    create_users(1)
    chain = seed_cascade_split()
    client = _login("view_item_1")

    response = _post_graphql(
        "query { allItems { edges { node { name category { name } } } } }",
        client=client,
    )
    assert response.status_code == 200
    payload = response.json()
    # No RelatedObjectDoesNotExist on the non-null `category` selection (feedback H1).
    assert "errors" not in payload, payload
    nodes = [edge["node"] for edge in payload["data"]["allItems"]["edges"]]
    item_names = {node["name"] for node in nodes}
    category_names = {node["category"]["name"] for node in nodes}
    # The Item under the private category is dropped (not surfaced with a broken FK)...
    assert chain["item_under_private"].name not in item_names
    assert chain["private_cat"].name not in category_names
    # ...and the Item under the public category survives with its category intact.
    assert chain["item_under_public"].name in item_names
    assert chain["public_cat"].name in category_names


@pytest.mark.django_db
def test_cascade_view_entry_user_nested_selection_drops_hidden_targets():
    """A ``view_entry`` user selecting ``item { name category { name } }`` drops hidden-target Entries, no resolver error.

    ``EntryType``'s ``view_entry`` branch cascades through both non-null FK edges
    (``item`` and ``property``) after its own ``is_private=False`` filter, so an
    Entry whose ``item`` (or ``property``) target is hidden from this user is
    dropped from the root rather than surfaced with an unresolvable non-null FK.
    ``entry_under_private`` (item + property both under the PRIVATE category) is
    dropped; the fully-public ``entry_under_public`` survives and its nested
    ``item { category { name } }`` resolves cleanly. Pins the feedback-H1 contract:
    hidden-target rows are dropped, not returned as ``RelatedObjectDoesNotExist``.
    """
    create_users(1)
    chain = seed_cascade_split()
    client = _login("view_entry_1")

    response = _post_graphql(
        "query { allEntries { edges { node { value item { name category { name } } } } } }",
        client=client,
    )
    assert response.status_code == 200
    payload = response.json()
    # The whole point of H1: the nested non-null FK selection does not error.
    assert "errors" not in payload, payload
    nodes = [edge["node"] for edge in payload["data"]["allEntries"]["edges"]]
    values = {node["value"] for node in nodes}
    category_names = {node["item"]["category"]["name"] for node in nodes}
    # Entry under the private category is dropped...
    assert chain["entry_under_private"].value not in values
    assert chain["private_cat"].name not in category_names
    # ...the fully-public entry survives with its nested item/category intact.
    assert chain["entry_under_public"].value in values
    assert chain["public_cat"].name in category_names


@pytest.mark.django_db
def test_cascade_staff_sees_everything():
    """A staff user (``create_users`` makes ``staff_<n>`` is_staff, NOT is_superuser) bypasses the cascade.

    Staff hits the ``user.is_staff`` short-circuit in every hook, so the visible
    counts equal the full ORM counts (capped at ``_RELAY_MAX_RESULTS`` for the
    connection page). Asserts against the seeded full set, including the private
    rows the cascade would hide for anyone else.
    """
    create_users(1)
    seed_data(1)
    seed_cascade_split()
    client = _login("staff_1")

    for field, model in (("allCategories", models.Category), ("allItems", models.Item)):
        response = _post_graphql(
            f"query {{ {field} {{ edges {{ node {{ id }} }} }} }}",
            client=client,
        )
        assert response.status_code == 200
        payload = response.json()
        assert "errors" not in payload, payload
        returned = len(payload["data"][field]["edges"])
        expected = min(model.objects.count(), _RELAY_MAX_RESULTS)
        assert returned == expected, (field, returned, expected)

    # Sanity: staff sees the private-chain rows that the cascade hides for others.
    assert models.Category.objects.filter(is_private=True).exists()
    assert models.Category.objects.count() <= _RELAY_MAX_RESULTS


@pytest.mark.django_db
def test_cascade_query_count_fixed():
    """``allEntries { value item { name category { name } } }`` runs in a FIXED query count.

    The cascade adds zero round-trips - the ``__in`` subqueries compile inline as
    nested ``SELECT``s (Decision 7). Because ``EntryType`` cascades through
    ``item`` to the custom-hooked ``ItemType`` / ``CategoryType``, the optimizer
    downgrades the forward-FK ``select_related`` to a windowed ``Prefetch`` chain
    (the shipped ``get_queryset`` -> ``Prefetch`` rule; spec-034 Slice 2). The
    anonymous request issues no auth queries, so the products query count is a
    deterministic 3 (one entry slice + one ``item`` prefetch + one ``category``
    prefetch), independent of how ``seed_data`` randomized row privacy. The
    cascade's nested ``IN (SELECT`` subqueries appear in the SQL, so the test
    cannot pass on a fall-through that skipped the cascade.
    """
    create_users(1)
    seed_data(1)
    seed_cascade_split()

    with CaptureQueriesContext(connection) as captured:
        response = _post_graphql(
            "query { allEntries { edges { node { value item { name category { name } } } } } }",
        )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    # Fixed, structurally deterministic: entry slice + item prefetch + category
    # prefetch (forward-FK select_related downgraded to Prefetch by the hooks).
    assert len(captured) == 3, [query["sql"] for query in captured]
    all_sql = " ".join(query["sql"] for query in captured)
    # Cascade composed its subqueries inline (zero added round-trips), not a
    # fall-through that skipped the cascade.
    assert "IN (SELECT" in all_sql
    # The forward chain plans as a Prefetch chain, NOT a select_related JOIN
    # across products tables (the hook-presence downgrade).
    assert not any(
        "products_entry" in query["sql"]
        and "products_item" in query["sql"]
        and "JOIN" in query["sql"].upper()
        for query in captured
    )


@pytest.mark.django_db
def test_cascade_composes_with_filter_and_order_live():
    """``filter:`` + ``orderBy:`` + cascade in one request; ``check_name_permission`` keeps firing.

    Two shapes per Decision 11 (cascade narrows rows, gates judge input):

    (a) a gated-field input (anonymous ``allCategories(orderBy: [{ name: ASC }])``)
        still raises the ``check_name_permission`` "staff user" error - the gate
        fires on input shape, independent of the cascade;
    (b) a non-gated anonymous composing request
        (``allItems(filter: { category: { id: { exact: <public-cat> } } }, orderBy: [{ name: ASC }])``)
        narrows first to the cascade-visible set (anonymous sees only non-private
        items under non-private categories) then filters + orders the survivors,
        matching the equivalent post-cascade ORM query.
    """
    create_users(1)
    seed_data(1)

    # (a) the gate fires on the gated order input, regardless of cascade.
    gated = _post_graphql(
        "query { allCategories(orderBy: [{ name: ASC }]) { edges { node { name } } } }",
    )
    gated_payload = gated.json()
    assert "errors" in gated_payload, gated_payload
    assert "staff user" in gated_payload["errors"][0]["message"]

    # (b) anonymous filter (no gate on `id`) + order (no gate on Item.name) on top
    # of the cascade-narrowed set: the public category's non-private items, ordered
    # by name. Derived from the equivalent post-cascade ORM query (API == ORM).
    category = models.Category.objects.filter(is_private=False).order_by("id").first()
    gid = str(
        relay.GlobalID(type_name=models.Category._meta.label_lower, node_id=str(category.pk)),
    )
    expected = [
        {"node": {"name": name}}
        for name in models.Item.objects.filter(category=category, is_private=False)
        .order_by("name")
        .values_list("name", flat=True)
    ]
    _assert_graphql_data(
        f'query {{ allItems(filter: {{ category: {{ id: {{ exact: "{gid}" }} }} }}, '
        "orderBy: [{ name: ASC }]) { edges { node { name } } } }",
        {"allItems": {"edges": expected}},
    )


# ---------------------------------------------------------------------------
# Malformed request bodies: a non-UTF-8 body must surface as a controlled 400,
# not an unhandled 500. Fixed by the framework's upstream patches for
# Strawberry (`BaseView.parse_json`) and cross_web (`DjangoHTTPRequestAdapter.body`),
# applied at app load. Without them the sync `GraphQLView` raises a raw
# `UnicodeDecodeError` while decoding the body, before GraphQL parsing runs.
# ---------------------------------------------------------------------------


def _post_raw_body(body: bytes, *, client: Client | None = None):
    """POST raw bytes to ``/graphql/`` as ``application/json`` (bypasses JSON encoding)."""
    graphql_client = client or Client()
    return graphql_client.post("/graphql/", data=body, content_type="application/json")


@pytest.mark.django_db(transaction=True)
def test_post_invalid_utf8_json_body_returns_400_not_500():
    """An invalid-UTF-8 byte inside an otherwise-JSON body -> controlled 400."""
    body = b'{"query":"{ __typename }","variables":{"d":"\xff\xfe\xfa"}}'

    response = _post_raw_body(body)

    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
def test_post_raw_binary_body_returns_400_not_500():
    """A wholly non-UTF-8 binary body -> controlled 400, never a 500."""
    response = _post_raw_body(bytes(range(256)) * 4)

    assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "body",
    [
        pytest.param(b'"just a string"', id="json-string"),
        pytest.param(b"42", id="json-number"),
        pytest.param(b"true", id="json-boolean"),
        pytest.param(b"null", id="json-null"),
    ],
)
def test_post_non_object_json_body_returns_400_not_500(body):
    """A valid-JSON-but-non-object body (scalar / null) -> controlled 400, never a 500.

    Strawberry's `parse_http_body` handles a JSON object (a single operation) and
    a JSON array (a batch), but lets a bare scalar fall through to
    `data.get("query")`, raising a raw `AttributeError` -> 500. The framework's
    Strawberry patch rejects a parsed body that is neither object nor array as a
    400. A JSON *array* body is deliberately excluded here - that is upstream's
    batch path, which the patch passes through untouched.
    """
    response = _post_raw_body(body)

    assert response.status_code == 400


# =============================================================================
# Form-mutation live surface (spec-038 Slice 4 / Decision 12). The products
# schema exposes `DjangoModelFormMutation` (`createItemViaForm` /
# `updateItemViaForm` over `ItemModelForm`, `createItemWithFileViaForm` over
# `ItemFileModelForm`, `createStampedItemViaForm` over `StampedItemModelForm`)
# and a plain `DjangoFormMutation` (`submitContact` over `ContactForm`). Every
# test seeds via `seed_data` / `create_users` / `seed_cascade_split` first line
# and reuses the existing reload fixture + `_post_graphql` / `_login_with_perm` /
# `_global_id` helpers. The `ModelForm` wire envelope is
# `{ node, errors { field messages } }`; the plain form is
# `{ ok, errors { field messages } }`.
# =============================================================================

# The form-mutation query strings (named distinctly from the `036` `_CREATE_ITEM`
# constants so each wire contract is spelled once). `createItemViaForm(data:
# ItemModelFormInput!)`, `updateItemViaForm(id: ID!, data: ItemModelFormPartialInput!)`,
# `submitContact(data: ContactFormInput!)`, `createStampedItemViaForm(data:
# StampedItemModelFormInput!)`. `categoryId` is the Relay `ID!` GlobalID string,
# server-decoded (the same shape the `036` `createItem` uses).
_CREATE_ITEM_VIA_FORM = (
    "mutation($d: ItemModelFormInput!) { createItemViaForm(data: $d) { "
    "node { name category { name } } errors { field messages } } }"
)
_UPDATE_ITEM_VIA_FORM = (
    "mutation($id: ID!, $d: ItemModelFormPartialInput!) { updateItemViaForm(id: $id, data: $d) { "
    "node { name } errors { field messages } } }"
)
_CREATE_STAMPED_ITEM_VIA_FORM = (
    "mutation($d: StampedItemModelFormInput!) { createStampedItemViaForm(data: $d) { "
    "node { name description } errors { field messages } } }"
)
_SUBMIT_CONTACT = (
    "mutation($d: ContactFormInput!) { submitContact(data: $d) { ok errors { field messages } } }"
)


@pytest.mark.django_db(transaction=True)
def test_create_item_via_form_happy_path():
    """`createItemViaForm` with a permitted caller creates the `Item`, no errors.

    The `ModelForm` create flavor mirrors the `036` `createItem` happy path:
    `view_item_1` granted the explicit `add_item` (the `ModelForm` flavor inherits
    `DjangoModelPermission`, codename `add_item`). The payload `node` carries the
    created `name` + the nested `category { name }` (the optimizer re-fetch), and the
    row persists.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    client = _login_with_perm("view_item_1", "add_item")

    response = _post_graphql(
        _CREATE_ITEM_VIA_FORM,
        client=client,
        variables={
            "d": {
                "name": "FormWidget",
                "categoryId": _global_id("products.category", category.pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItemViaForm"]
    assert result["errors"] == []
    assert result["node"] == {"name": "FormWidget", "category": {"name": category.name}}
    created = models.Item.objects.get(name="FormWidget", category=category)
    assert created.description == ""


@pytest.mark.django_db(transaction=True)
def test_create_item_via_form_category_id_writes_through_form_category_field():
    """`categoryId` validates + writes through the form's `category` field (P1 reverse map).

    The created `Item.category_id` equals the submitted category pk, and the only
    channel the test query offers for setting it is the generated `categoryId` input
    arg (the form's `category` `ModelChoiceField` reverse-mapped). This is NOT a raw
    model `setattr` - the value reaches the bound form by its form-field key.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    client = _login_with_perm("view_item_1", "add_item")

    response = _post_graphql(
        _CREATE_ITEM_VIA_FORM,
        client=client,
        variables={
            "d": {
                "name": "ReverseMapWidget",
                "categoryId": _global_id("products.category", category.pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItemViaForm"]
    assert result["errors"] == []
    created = models.Item.objects.get(name="ReverseMapWidget")
    # The FK was written through the form's `category` field from the `categoryId` arg.
    assert created.category_id == category.pk


@pytest.mark.django_db(transaction=True)
def test_update_item_via_form_non_colliding_partial_update():
    """A `name`-only `updateItemViaForm` persists `name`, leaving the row otherwise intact.

    The non-colliding partial-update success: `ItemModelFormPartialInput` provides only
    `name`; the unprovided `description` / `category` are reconstructed from the located
    row via `model_to_dict` and left unchanged. `staff_1` (full visibility) granted the
    explicit `change_item` codename.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    item = models.Item.objects.create(
        name="BeforeForm",
        description="keep me",
        category=category,
    )
    client = _login_with_perm("staff_1", "change_item")

    response = _post_graphql(
        _UPDATE_ITEM_VIA_FORM,
        client=client,
        variables={"id": _global_id("products.item", item.pk), "d": {"name": "AfterForm"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItemViaForm"]
    assert result["errors"] == []
    assert result["node"] == {"name": "AfterForm"}
    item.refresh_from_db()
    assert item.name == "AfterForm"
    assert item.description == "keep me"
    assert item.category_id == category.pk


@pytest.mark.django_db(transaction=True)
def test_update_item_via_form_partial_update_preserves_category_and_description():
    """RIGHT-PATH / LOAD-BEARING: a `name`-only update preserves `category` (FK) + `description`.

    The mutation's `data:` is `{name: ...}` ONLY, so the test can only exercise the
    partial-update reconstruction path - it cannot accidentally pass `category` /
    `description` through. After the update, the located row's `category_id` and
    `description` are UNCHANGED from their seeded values while `name` IS the new value.
    If reconstruction dropped the FK / scalar, this assertion would fail.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    item = models.Item.objects.create(
        name="PreserveBefore",
        description="preserve this description",
        category=category,
    )
    original_category_id = item.category_id
    client = _login_with_perm("staff_1", "change_item")

    response = _post_graphql(
        _UPDATE_ITEM_VIA_FORM,
        client=client,
        variables={"id": _global_id("products.item", item.pk), "d": {"name": "PreserveAfter"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItemViaForm"]
    assert result["errors"] == []
    item.refresh_from_db()
    assert item.name == "PreserveAfter"
    # The unprovided FK + scalar are reconstructed (not dropped) - the P1 preservation.
    assert item.category_id == original_category_id
    assert item.description == "preserve this description"


@pytest.mark.django_db(transaction=True)
def test_update_item_via_form_partial_collision_fires_unique_constraint_on_name_change():
    """RIGHT-PATH / LOAD-BEARING: a `name`-only collision fires `unique_item_per_category`.

    Two `Item`s `A` / `B` under one category; `updateItemViaForm(A, {name: "B"})`. The
    mutation's `data:` carries ONLY `name`, so the unchanged `category` co-participates
    in the composite constraint via the `model_to_dict` reconstruction (the right-path
    proof - if reconstruction dropped `category`, the constraint could not fire). The
    form's `_post_clean` -> `validate_constraints()` catches it as a `NON_FIELD_ERRORS`
    entry mapped to the `"__all__"` sentinel; `node` is null, exactly one `errors` entry,
    and `A`'s name is unchanged.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    item_a = models.Item.objects.create(name="FormA", category=category)
    models.Item.objects.create(name="FormB", category=category)
    client = _login_with_perm("staff_1", "change_item")

    response = _post_graphql(
        _UPDATE_ITEM_VIA_FORM,
        client=client,
        variables={"id": _global_id("products.item", item_a.pk), "d": {"name": "FormB"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItemViaForm"]
    assert result["node"] is None
    assert len(result["errors"]) == 1
    assert result["errors"][0]["field"] == "__all__"
    item_a.refresh_from_db()
    assert item_a.name == "FormA"


@pytest.mark.django_db(transaction=True)
def test_create_item_via_form_clean_field_error_is_field_keyed():
    """A `clean_<field>` error -> `FieldError` keyed to the FORM field (`name`), no top-level error.

    `ItemModelForm.clean_name` rejects `REJECTED_ITEM_NAME`. The failure surfaces in
    `form.errors["name"]`, mapped to a `FieldError` whose `field` is the form field name
    `name`. `node` is null, `messages` non-empty, no top-level GraphQL error, no write.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    client = _login_with_perm("view_item_1", "add_item")
    before = models.Item.objects.count()

    response = _post_graphql(
        _CREATE_ITEM_VIA_FORM,
        client=client,
        variables={
            "d": {
                "name": REJECTED_ITEM_NAME,
                "categoryId": _global_id("products.category", category.pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItemViaForm"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["name"]
    assert result["errors"][0]["messages"]
    assert models.Item.objects.count() == before


@pytest.mark.django_db(transaction=True)
def test_create_item_via_form_unique_constraint_envelope_uses_all_sentinel():
    """A duplicate `(category, name)` `createItemViaForm` -> a `"__all__"`-keyed `FieldError`.

    The model's `unique_item_per_category` constraint surfaces through the `ModelForm`'s
    `_post_clean` -> `validate_constraints()` as a `NON_FIELD_ERRORS` entry mapped to the
    `"__all__"` sentinel - identical to the `036` model-driven path (line 388). `node` is
    null, exactly one `errors` entry, no second row written.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    existing = models.Item.objects.create(name="FormDup", category=category)
    client = _login_with_perm("view_item_1", "add_item")

    response = _post_graphql(
        _CREATE_ITEM_VIA_FORM,
        client=client,
        variables={
            "d": {
                "name": existing.name,
                "categoryId": _global_id("products.category", category.pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItemViaForm"]
    assert result["node"] is None
    assert len(result["errors"]) == 1
    assert result["errors"][0]["field"] == "__all__"
    assert models.Item.objects.filter(name="FormDup", category=category).count() == 1


@pytest.mark.django_db(transaction=True)
def test_create_item_via_form_anonymous_is_denied_top_level_error_no_write():
    """An anonymous `createItemViaForm` -> top-level error, `data` null, no write.

    The `ModelForm` flavor inherits the `DjangoModelPermission` default, which denies a
    caller with no authenticated user. The denial RAISES a top-level `GraphQLError` on
    the non-null payload field (so GraphQL nulls `data`), NOT a `FieldError` envelope
    entry - identical to the `036` anonymous denial (line 458).
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    before = models.Item.objects.count()

    response = _post_graphql(
        _CREATE_ITEM_VIA_FORM,
        variables={
            "d": {
                "name": "AnonFormWidget",
                "categoryId": _global_id("products.category", category.pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("errors"), payload
    assert payload["data"] is None
    assert "Not authorized" in payload["errors"][0]["message"]
    assert models.Item.objects.count() == before
    assert not models.Item.objects.filter(name="AnonFormWidget").exists()


@pytest.mark.django_db(transaction=True)
def test_create_item_via_form_missing_model_perm_is_denied_no_write():
    """A caller holding only `view_item` (lacks `add_item`) -> top-level denial, no write.

    `view_item_1` holds only `products.view_item` and LACKS `add_item`, so the inherited
    `DjangoModelPermission` denies the create - a top-level `GraphQLError`, no row written
    (mirror line 493). Isolates the model-perm codename denial from the anonymous case.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    client = _login("view_item_1")  # only products.view_item, no add_item
    before = models.Item.objects.count()

    response = _post_graphql(
        _CREATE_ITEM_VIA_FORM,
        client=client,
        variables={
            "d": {
                "name": "NoPermFormWidget",
                "categoryId": _global_id("products.category", category.pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("errors"), payload
    assert payload["data"] is None
    assert "Not authorized" in payload["errors"][0]["message"]
    assert models.Item.objects.count() == before
    assert not models.Item.objects.filter(name="NoPermFormWidget").exists()


@pytest.mark.django_db(transaction=True)
def test_update_item_via_form_visibility_scoped_hidden_private_row_is_not_found():
    """A caller who holds `change_item` but cannot SEE a private `Item` gets not-found.

    `seed_cascade_split` gives `item_under_private` (a public Item under a PRIVATE
    category) and `item_under_public`. A non-staff `view_item_1` user granted
    `change_item` cannot see `item_under_private` (the `ItemType.get_queryset` cascade
    hides it), so the `updateItemViaForm` LOCATE misses -> a not-found `FieldError` on
    `id`, row unchanged; the same update succeeds for `item_under_public`. The write perm
    is HELD, isolating the visibility miss from an authorization denial (mirror line 528).
    """
    create_users(1)
    chain = seed_cascade_split()
    private_gid = _global_id("products.item", chain["item_under_private"].pk)
    public_gid = _global_id("products.item", chain["item_under_public"].pk)
    client = _login_with_perm("view_item_1", "change_item")

    response = _post_graphql(
        _UPDATE_ITEM_VIA_FORM,
        client=client,
        variables={"id": private_gid, "d": {"name": "RenamedHidden"}},
    )
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItemViaForm"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["id"]
    chain["item_under_private"].refresh_from_db()
    assert chain["item_under_private"].name == "zzz_item_under_private"

    # Contrast: the SAME update succeeds for the visible public row.
    response = _post_graphql(
        _UPDATE_ITEM_VIA_FORM,
        client=client,
        variables={"id": public_gid, "d": {"name": "RenamedPublicForm"}},
    )
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["updateItemViaForm"]
    assert result["errors"] == []
    assert result["node"] == {"name": "RenamedPublicForm"}


@pytest.mark.django_db(transaction=True)
def test_create_item_via_form_relation_id_for_hidden_category_is_field_error():
    """RIGHT-PATH / LOAD-BEARING (P1): a permitted writer cannot attach a `Category` they cannot SEE.

    `seed_cascade_split` gives a PRIVATE category. A non-staff `view_item_1` user granted
    `add_item` cannot see it, so `createItemViaForm(categoryId=<private cat gid>)` is a
    field-keyed `FieldError` on `categoryId` - the relation id is resolved through the
    target's visibility `get_queryset` (the form decode), NOT delegated to the form's
    default `Category.objects.all()` queryset (which would have accepted it). The SAME
    caller's create against the VISIBLE public category SUCCEEDS - the contrast proving
    the decode visibility query, not the form queryset, is the guard. The submitted
    GlobalID is well-formed-but-hidden, so the test can only exercise the
    visibility-decode path, not a parse-failure path. The headline slice invariant
    (mirror line 694).
    """
    create_users(1)
    chain = seed_cascade_split()
    client = _login_with_perm("view_item_1", "add_item")
    before = models.Item.objects.count()

    # Hidden private category: FieldError on categoryId, no write.
    response = _post_graphql(
        _CREATE_ITEM_VIA_FORM,
        client=client,
        variables={
            "d": {
                "name": "AttachHiddenForm",
                "categoryId": _global_id("products.category", chain["private_cat"].pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItemViaForm"]
    assert result["node"] is None
    assert [e["field"] for e in result["errors"]] == ["categoryId"]
    assert models.Item.objects.count() == before
    assert not models.Item.objects.filter(name="AttachHiddenForm").exists()

    # Visible public category: the same caller's same create succeeds.
    response = _post_graphql(
        _CREATE_ITEM_VIA_FORM,
        client=client,
        variables={
            "d": {
                "name": "AttachVisibleForm",
                "categoryId": _global_id("products.category", chain["public_cat"].pk),
            },
        },
    )
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createItemViaForm"]
    assert result["errors"] == []
    assert result["node"] == {
        "name": "AttachVisibleForm",
        "category": {"name": chain["public_cat"].name},
    }


@pytest.mark.django_db(transaction=True)
def test_create_item_with_file_via_form_multipart_upload_over_http(tmp_path):
    """A raw `django.test.Client` multipart upload to a form-backed `Upload` field (P1 file-routing).

    Mirrors `test_uploads_api.py::test_multipart_create_uploads_real_files_over_http`'s
    transport: under `override_settings(MEDIA_ROOT=tmp_path)`, a permitted caller
    (force-login + `add_item`) POSTs the GraphQL-multipart `{operations, map, "0":
    SimpleUploadedFile(...)}` body, with `map` pointing `"0"` at
    `variables.d.attachment` and `variables.d.attachment` set to `None`.
    **Load-bearing:** `errors == []`, the row exists with the file attached
    (`attachment.name` endswith `doc.txt`), proving the resolver split routed the
    `Upload` into the form's `files=` (NOT `data=`) and the form validated + wrote it. A
    plain-text `FileField` (no Pillow / no image-dimension assertions).
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    from django.contrib.auth.models import Permission

    user = get_user_model().objects.get(username="view_item_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_item", content_type__app_label="products"),
    )
    user = get_user_model().objects.get(pk=user.pk)  # drop the stale perm cache

    mutation = (
        "mutation($d: ItemFileModelFormInput!) { createItemWithFileViaForm(data: $d) { "
        "node { name } errors { field messages } } }"
    )
    operations = {
        "query": mutation,
        "variables": {
            "d": {
                "name": "UploadedFormWidget",
                "categoryId": _global_id("products.category", category.pk),
                "attachment": None,
            },
        },
    }
    file_map = {"0": ["variables.d.attachment"]}

    with override_settings(MEDIA_ROOT=str(tmp_path)):
        client = Client()
        client.force_login(user)
        response = client.post(
            "/graphql/",
            data={
                "operations": json.dumps(operations),
                "map": json.dumps(file_map),
                "0": SimpleUploadedFile(
                    "doc.txt",
                    b"form upload bytes",
                    content_type="text/plain",
                ),
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert "errors" not in body, body
        result = body["data"]["createItemWithFileViaForm"]
        assert result["errors"] == []
        assert result["node"] == {"name": "UploadedFormWidget"}

        # The row landed with the file routed into `files=` (the data=/files= split).
        created = models.Item.objects.get(name="UploadedFormWidget")
        assert created.attachment.name.endswith("doc.txt")
        # Read + close the handle so the suite's `-W error` does not catch a leaked
        # file finalizer (the FieldFile leaves the underlying file open after read()).
        with created.attachment.open("rb") as handle:
            assert handle.read() == b"form upload bytes"


@pytest.mark.django_db(transaction=True)
def test_create_stamped_item_via_form_get_form_kwargs_injects_user():
    """A `get_form_kwargs` override injecting `user` drives a kwarg-requiring form (P2).

    `StampedItemModelForm.__init__` REQUIRES a `user` kwarg and its `clean()` requires
    `user.is_authenticated`; `CreateStampedItemViaForm.get_form_kwargs` injects
    `user=info.context.request.user`. The create succeeds for a logged-in caller, and the
    injected user stamps the created row's `description` (`stamped by <username>`) - the
    user-stamped side effect pins that the user actually reached the form. The bind
    succeeded despite the required-kwarg `__init__`, proving schema-time `base_fields`
    discovery never instantiated the form.
    """
    create_users(1)
    seed_data(1)
    category = models.Category.objects.first()
    client = _login_with_perm("view_item_1", "add_item")

    response = _post_graphql(
        _CREATE_STAMPED_ITEM_VIA_FORM,
        client=client,
        variables={
            "d": {
                "name": "StampedWidget",
                "categoryId": _global_id("products.category", category.pk),
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["createStampedItemViaForm"]
    assert result["errors"] == []
    assert result["node"] == {"name": "StampedWidget", "description": "stamped by view_item_1"}
    created = models.Item.objects.get(name="StampedWidget")
    assert created.description == "stamped by view_item_1"


@pytest.mark.django_db(transaction=True)
def test_submit_contact_plain_form_success_shape():
    """`submitContact` with valid data -> `ok: true`, empty `errors` (the plain-form success).

    The model-less `DjangoFormMutation` flavor: `AllowAny` opens the success path to any
    caller. Valid `ContactForm` data validates (no write - the form is model-less), so
    the payload is `{ ok: true, errors: [] }`.
    """
    create_users(1)

    response = _post_graphql(
        _SUBMIT_CONTACT,
        variables={"d": {"subject": "Hello there", "email": "user@example.com"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["submitContact"]
    assert result["ok"] is True
    assert result["errors"] == []


@pytest.mark.django_db(transaction=True)
def test_submit_contact_plain_form_validation_failure_shape():
    """`submitContact` with data failing `clean_subject` -> `ok: false`, field-keyed `errors`.

    A blank-after-strip `subject` trips `ContactForm.clean_subject`, so `form.is_valid()`
    fails. The payload is `{ ok: false }` with a field-keyed `errors` entry on the form
    field `subject` (`messages` non-empty). No top-level GraphQL error.
    """
    create_users(1)

    response = _post_graphql(
        _SUBMIT_CONTACT,
        variables={"d": {"subject": "   ", "email": "user@example.com"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "errors" not in payload, payload
    result = payload["data"]["submitContact"]
    assert result["ok"] is False
    assert [e["field"] for e in result["errors"]] == ["subject"]
    assert result["errors"][0]["messages"]


@pytest.mark.django_db
def test_submit_ping_plain_form_denied_by_default_top_level_error():
    """A plain ``DjangoFormMutation`` with NO ``permission_classes`` denies every caller live.

    The model-less ``SubmitPing`` does not opt into ``AllowAny`` (unlike
    ``submitContact``), so a model-less form falls to the ``DenyAll`` deny-by-default
    posture: the live call is rejected with a top-level authorization ``GraphQLError``
    (data nulled), never reaching the form - the deny default earned over real HTTP.
    """
    response = _post_graphql(
        "mutation($d: PingFormInput!){ submitPing(data: $d) { ok errors { field } } }",
        variables={"d": {"message": "hi"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("errors"), payload  # top-level authorization error
    assert payload["data"] is None
    assert "Not authorized" in payload["errors"][0]["message"]
