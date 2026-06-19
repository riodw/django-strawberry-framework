"""Live ``/graphql/`` regression: a mutation must not commit a partial write.

Pins the atomicity gap tracked by KANBAN card **BETA-054** ("Mutation
transactions and idempotency"): a ``DjangoMutation`` runs its write inside
``transaction.atomic()``, but graphql-core completes (serializes) the returned
payload *after* the resolver returns - i.e. after the transaction has already
committed. So a response-completion failure can leave a write committed while
the client sees ``data: null`` + a top-level error.

The trigger requires a row that can be written but not serialized back. Normal
ORM writes can't produce one, so the tests corrupt the DB directly with raw
SQL: a ``Category.created_date`` of ``"not-a-date"`` hydrates to ``None`` on
refetch or snapshot (no exception, so nothing rolls back), and only fails later
at completion as ``Cannot return null for non-nullable field CategoryType.createdDate``
- by which point the create/update/delete side effect has committed.

Marked ``xfail(strict=True)`` rather than ``skip`` on purpose: the test runs and
is expected to fail today, and the moment BETA-054 extends the transaction
boundary to span response completion it will XPASS, turning the suite red so
this marker is removed (the ``skip`` alternative would silently rot). When that
happens, delete the ``xfail`` marker - the assertions already encode the
desired post-fix contract (no 500, the completion error is surfaced, and the
write rolled back).

Keep future BETA-054 response-completion partial-commit regressions in this
module so the card's eventual implementation has one live HTTP acceptance file
to un-xfail and satisfy.
"""

from __future__ import annotations

import sqlite3

import pytest
from apps.products.services import create_users
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client
from strawberry import relay

_UPDATE_ITEM = """
mutation($id: ID!, $d: ItemPartialInput!) {
  updateItem(id: $id, data: $d) {
    node {
      id
      name
      category { id name createdDate updatedDate }
    }
    errors { field messages }
  }
}
"""

_UPDATE_ITEM_DESCRIPTION = """
mutation($id: ID!, $d: ItemPartialInput!) {
  updateItem(id: $id, data: $d) {
    node {
      id
      name
      description
    }
    errors { field messages }
  }
}
"""

_CREATE_ITEM = """
mutation($d: ItemInput!) {
  createItem(data: $d) {
    node {
      id
      name
      category { id name createdDate updatedDate }
    }
    errors { field messages }
  }
}
"""

_DELETE_ITEM = """
mutation($id: ID!) {
  deleteItem(id: $id) {
    node {
      id
      name
      category { id name createdDate updatedDate }
    }
    errors { field messages }
  }
}
"""


def _login_with_perm(username: str, *codenames: str) -> Client:
    user = get_user_model().objects.get(username=username)
    for codename in codenames:
        permission = Permission.objects.get(codename=codename, content_type__app_label="products")
        user.user_permissions.add(permission)
    client = Client()
    client.force_login(get_user_model().objects.get(pk=user.pk))
    return client


def _global_id(type_name: str, pk: int) -> str:
    return str(relay.GlobalID(type_name=type_name, node_id=str(pk)))


def _execute_raw(sql: str, params: tuple = ()) -> int:
    """Run a raw INSERT (bypassing the ORM, to plant un-serializable data) and return its pk."""
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.cursor.lastrowid


def _post_update(client: Client, item_pk: int):
    return client.post(
        "/graphql/",
        data={
            "query": _UPDATE_ITEM,
            "variables": {
                "id": _global_id("products.item", item_pk),
                "d": {"name": "post-corruption-update"},
            },
        },
        content_type="application/json",
    )


def _post_update_description(client: Client, item_pk: int):
    return client.post(
        "/graphql/",
        data={
            "query": _UPDATE_ITEM_DESCRIPTION,
            "variables": {
                "id": _global_id("products.item", item_pk),
                "d": {"name": "post-blob-corruption-update"},
            },
        },
        content_type="application/json",
    )


def _post_create(client: Client, category_pk: int):
    return client.post(
        "/graphql/",
        data={
            "query": _CREATE_ITEM,
            "variables": {
                "d": {
                    "name": "create-post-corruption",
                    "categoryId": _global_id("products.category", category_pk),
                },
            },
        },
        content_type="application/json",
    )


def _post_delete(client: Client, item_pk: int):
    return client.post(
        "/graphql/",
        data={"query": _DELETE_ITEM, "variables": {"id": _global_id("products.item", item_pk)}},
        content_type="application/json",
    )


def _insert_bad_category(name: str) -> int:
    """Insert a category whose dates hydrate to ``None`` but don't raise on fetch."""
    return _execute_raw(
        """
        INSERT INTO products_category (name, description, is_private, created_date, updated_date)
        VALUES (%s, %s, 0, %s, %s)
        """,
        (
            name,
            "category created by raw SQL",
            "not-a-date",
            "not-a-date",
        ),
    )


def _insert_item(name: str, category_pk: int) -> int:
    """Insert an item under ``category_pk`` without normal ORM validation."""
    return _execute_raw(
        """
        INSERT INTO products_item
            (name, description, category_id, is_private, created_date, updated_date)
        VALUES (%s, %s, %s, 0, %s, %s)
        """,
        (
            name,
            "item created by raw SQL",
            category_pk,
            "2026-01-02 03:04:05",
            "2026-01-02 03:04:05",
        ),
    )


def _insert_item_with_description(name: str, category_pk: int, description: object) -> int:
    """Insert an item with a deliberately non-ORM-written ``description`` value."""
    return _execute_raw(
        """
        INSERT INTO products_item
            (name, description, category_id, is_private, created_date, updated_date)
        VALUES (%s, %s, %s, 0, %s, %s)
        """,
        (
            name,
            description,
            category_pk,
            "2026-01-02 03:04:05",
            "2026-01-02 03:04:05",
        ),
    )


@pytest.mark.xfail(
    strict=True,
    reason="KANBAN BETA-054 (Mutation transactions and idempotency): the mutation transaction "
    "boundary ends when the resolver returns, before graphql-core completes the payload, so a "
    "response-completion failure commits a partial write. Remove this marker when BETA-054 lands.",
)
@pytest.mark.django_db(transaction=True)
def test_update_does_not_commit_when_response_completion_fails():
    """An update whose response can't be serialized must roll back, not commit a partial write."""
    create_users(1)
    client = _login_with_perm("view_item_1", "view_category", "change_item")

    # A category whose `created_date` cannot round-trip: it hydrates to None on
    # refetch (no exception), then fails the non-nullable `createdDate` at completion.
    category_pk = _insert_bad_category("raw-update-bad-date-category")
    item_pk = _insert_item("raw-bad-date-item", category_pk)

    response = _post_update(client, item_pk)

    # The request is handled (no 500) and the unserializable response surfaces an error...
    assert response.status_code < 500
    assert "errors" in response.json()

    # ...but the write must NOT have committed: the row keeps its original name.
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM products_item WHERE id = %s", (item_pk,))
        stored_name = cursor.fetchone()[0]
    assert stored_name == "raw-bad-date-item"


@pytest.mark.xfail(
    strict=True,
    reason="KANBAN BETA-054 (Mutation transactions and idempotency): response completion can "
    "also fail while serializing a scalar field on the mutated object itself. Remove this "
    "marker when BETA-054 lands.",
)
@pytest.mark.django_db(transaction=True)
def test_update_does_not_commit_when_own_scalar_response_completion_fails():
    """An update selecting a corrupt own scalar must roll back, not commit a partial write."""
    create_users(1)
    client = _login_with_perm("view_item_1", "view_category", "change_item")
    category_pk = _execute_raw(
        """
        INSERT INTO products_category (name, description, is_private, created_date, updated_date)
        VALUES (%s, %s, 0, %s, %s)
        """,
        (
            "raw-blob-description-category",
            "normal category",
            "2026-01-02 03:04:05",
            "2026-01-02 03:04:05",
        ),
    )
    item_pk = _insert_item_with_description(
        "raw-blob-description-item",
        category_pk,
        sqlite3.Binary(b"\x80\x81PY\x00\xffCODE"),
    )

    response = _post_update_description(client, item_pk)

    assert response.status_code < 500
    assert "errors" in response.json()
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM products_item WHERE id = %s", (item_pk,))
        stored_name = cursor.fetchone()[0]
    assert stored_name == "raw-blob-description-item"


@pytest.mark.xfail(
    strict=True,
    reason="KANBAN BETA-054 (Mutation transactions and idempotency): create has the same "
    "response-completion transaction gap as update. Remove this marker when BETA-054 lands.",
)
@pytest.mark.django_db(transaction=True)
def test_create_does_not_commit_when_response_completion_fails():
    """A create whose response can't be serialized must roll back, not leave a row."""
    create_users(1)
    client = _login_with_perm("view_item_1", "add_item")
    category_pk = _insert_bad_category("raw-create-bad-date-category")

    response = _post_create(client, category_pk)

    assert response.status_code < 500
    assert "errors" in response.json()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM products_item WHERE name = %s",
            ("create-post-corruption",),
        )
        created_count = cursor.fetchone()[0]
    assert created_count == 0


@pytest.mark.xfail(
    strict=True,
    reason="KANBAN BETA-054 (Mutation transactions and idempotency): delete has the same "
    "response-completion transaction gap as update. Remove this marker when BETA-054 lands.",
)
@pytest.mark.django_db(transaction=True)
def test_delete_does_not_commit_when_response_completion_fails():
    """A delete whose response can't be serialized must roll back, not remove the row."""
    create_users(1)
    client = _login_with_perm("staff_1", "delete_item")
    category_pk = _insert_bad_category("raw-delete-bad-date-category")
    item_pk = _insert_item("raw-delete-bad-date-item", category_pk)

    response = _post_delete(client, item_pk)

    assert response.status_code < 500
    assert "errors" in response.json()
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM products_item WHERE id = %s", (item_pk,))
        remaining_count = cursor.fetchone()[0]
    assert remaining_count == 1
