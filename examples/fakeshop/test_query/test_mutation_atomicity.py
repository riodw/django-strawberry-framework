"""Live ``/graphql/`` regression: a mutation must not commit a partial write.

Pins the atomicity gap tracked by KANBAN card **BETA-054** ("Mutation
transactions and idempotency"): a ``DjangoMutation`` runs its write inside
``transaction.atomic()``, but graphql-core completes (serializes) the returned
payload *after* the resolver returns - i.e. after the transaction has already
committed. So a response-completion failure can leave a write committed while
the client sees ``data: null`` + a top-level error.

The trigger requires a row that can be written but not serialized back. Normal
ORM writes can't produce one, so the test corrupts the DB directly with raw
SQL: a ``Category.created_date`` of ``"not-a-date"`` hydrates to ``None`` on
refetch (no exception, so nothing rolls back), and only fails later at
completion as ``Cannot return null for non-nullable field CategoryType.createdDate``
- by which point the unrelated ``Item.name`` update has committed.

Marked ``xfail(strict=True)`` rather than ``skip`` on purpose: the test runs and
is expected to fail today, and the moment BETA-054 extends the transaction
boundary to span response completion it will XPASS, turning the suite red so
this marker is removed (the ``skip`` alternative would silently rot). When that
happens, delete the ``xfail`` marker - the assertions already encode the
desired post-fix contract (no 500, the completion error is surfaced, and the
write rolled back).
"""

from __future__ import annotations

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
    category_pk = _execute_raw(
        """
        INSERT INTO products_category (name, description, is_private, created_date, updated_date)
        VALUES (%s, %s, 0, %s, %s)
        """,
        (
            "raw-bad-date-category",
            "category created by raw SQL",
            "not-a-date",
            "not-a-date",
        ),
    )
    item_pk = _execute_raw(
        """
        INSERT INTO products_item
            (name, description, category_id, is_private, created_date, updated_date)
        VALUES (%s, %s, %s, 0, %s, %s)
        """,
        (
            "raw-bad-date-item",
            "item created by raw SQL",
            category_pk,
            "2026-01-02 03:04:05",
            "2026-01-02 03:04:05",
        ),
    )

    response = _post_update(client, item_pk)

    # The request is handled (no 500) and the unserializable response surfaces an error...
    assert response.status_code < 500
    assert "errors" in response.json()

    # ...but the write must NOT have committed: the row keeps its original name.
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM products_item WHERE id = %s", (item_pk,))
        stored_name = cursor.fetchone()[0]
    assert stored_name == "raw-bad-date-item"
