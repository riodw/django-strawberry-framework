"""Live ``/graphql/`` acceptance for the BETA-055 response-completion transaction contract.

Pins the atomicity fix tracked by KANBAN card **BETA-055** ("Mutation
transactions and idempotency"): a ``DjangoMutation`` runs its write inside a
transaction that graphql-core historically committed when the resolver
returned - BEFORE the returned payload was *completed* (serialized) - so a
completion failure left the write committed while the client saw
``data: null`` + a top-level error. ``DjangoSchema``'s execution context now
holds each generated top-level mutation field's transaction open THROUGH value
completion and rolls it back when completion adds an error.

The trigger requires a row that can be written but not serialized back. Normal
ORM writes can't produce one, so the tests corrupt the DB directly with raw
SQL: a ``created_date`` of ``"not-a-date"`` hydrates to ``None`` on refetch or
snapshot (no exception, so nothing fails at write time), and only fails at
completion as ``Cannot return null for non-nullable field ...createdDate`` -
by which point the create/update/delete side effect must ROLL BACK, not stay
committed.

These began life as ``xfail(strict=True)`` regressions; BETA-055 landed, they
XPASSed, and the markers were removed - the assertions encode the shipped
contract (no 500, the completion error is surfaced, the write rolled back).
The success-side contract (a serializable payload still commits, and serial
top-level mutation fields keep independent transactions) is pinned alongside.
"""

from __future__ import annotations

import pytest
from apps.products.services import create_users
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client
from strawberry import relay

from django_strawberry_framework.testing import TestClient

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

_DELETE_ITEM_OWN_SCALAR = """
mutation($id: ID!) {
  deleteItem(id: $id) {
    node {
      id
      name
      createdDate
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

# Two serial top-level fields in ONE operation: the GraphQL spec executes them
# serially, and each generated field gets its OWN completion-spanning
# transaction - the first field's outcome must not couple to the second's.
_TWO_UPDATES = """
mutation($idA: ID!, $dA: ItemPartialInput!, $idB: ID!, $dB: ItemPartialInput!) {
  first: updateItem(id: $idA, data: $dA) {
    node { id name }
    errors { field messages }
  }
  second: updateItem(id: $idB, data: $dB) {
    node { id name category { createdDate } }
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


def _post_update(
    client: Client,
    item_pk: int,
    *,
    query: str = _UPDATE_ITEM,
    name: str,
):
    res = TestClient(client=client).query(
        query,
        variables={"id": _global_id("products.item", item_pk), "d": {"name": name}},
        assert_no_errors=False,
    )
    return res.response


def _post_create(client: Client, category_pk: int):
    res = TestClient(client=client).query(
        _CREATE_ITEM,
        variables={
            "d": {
                "name": "create-post-corruption",
                "categoryId": _global_id("products.category", category_pk),
            },
        },
        assert_no_errors=False,
    )
    return res.response


def _post_delete(client: Client, item_pk: int):
    res = TestClient(client=client).query(
        _DELETE_ITEM,
        variables={"id": _global_id("products.item", item_pk)},
        assert_no_errors=False,
    )
    return res.response


def _insert_category(name: str, *, created_date: str = "2026-01-02 03:04:05") -> int:
    """Insert a category by raw SQL; a ``created_date`` of ``"not-a-date"`` corrupts it.

    A corrupt date hydrates to ``None`` on refetch (no exception, nothing rolls
    back at write time) and only fails later, completing the non-nullable
    ``createdDate``.
    """
    return _execute_raw(
        """
        INSERT INTO products_category (name, description, is_private, created_date, updated_date)
        VALUES (%s, %s, 0, %s, %s)
        """,
        (
            name,
            "category created by raw SQL",
            created_date,
            created_date,
        ),
    )


def _insert_item(name: str, category_pk: int, *, created_date: str = "2026-01-02 03:04:05") -> int:
    """Insert an item by raw SQL; a ``created_date`` of ``"not-a-date"`` corrupts it."""
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
            created_date,
            created_date,
        ),
    )


def _stored_item_name(item_pk: int) -> str:
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM products_item WHERE id = %s", (item_pk,))
        return cursor.fetchone()[0]


@pytest.mark.django_db(transaction=True)
def test_update_does_not_commit_when_response_completion_fails():
    """An update whose response can't be serialized must roll back, not commit a partial write."""
    create_users(1)
    client = _login_with_perm("view_item_1", "view_category", "change_item")

    # A category whose `created_date` cannot round-trip: it hydrates to None on
    # refetch (no exception), then fails the non-nullable `createdDate` at completion.
    category_pk = _insert_category("raw-update-bad-date-category", created_date="not-a-date")
    item_pk = _insert_item("raw-bad-date-item", category_pk)

    response = _post_update(client, item_pk, name="post-corruption-update")

    # The request is handled (no 500) and the unserializable response surfaces an error...
    assert response.status_code < 500
    assert "errors" in response.json()

    # ...but the write must NOT have committed: the row keeps its original name.
    assert _stored_item_name(item_pk) == "raw-bad-date-item"


@pytest.mark.django_db(transaction=True)
def test_delete_does_not_commit_when_own_scalar_response_completion_fails():
    """A delete selecting a corrupt scalar on the deleted object ITSELF must roll back.

    Distinct from the relation-path tests: here the completion failure is on the
    target row's OWN non-nullable ``createdDate`` (the corrupt date lives on the
    ITEM, hydrating to ``None`` in the pre-delete snapshot), so the failing field
    sits directly under the payload's ``node`` slot. Delete is the only operation
    that can surface an own-column corruption at completion: create/update
    ``save()`` writes every column back, so a corrupt own column is refused at
    write time as a NOT NULL constraint envelope instead (itself rolled back).
    """
    create_users(1)
    client = _login_with_perm("staff_1", "delete_item")
    category_pk = _insert_category("raw-own-scalar-category")
    item_pk = _insert_item("raw-own-scalar-item", category_pk, created_date="not-a-date")

    res = TestClient(client=client).query(
        _DELETE_ITEM_OWN_SCALAR,
        variables={"id": _global_id("products.item", item_pk)},
        assert_no_errors=False,
    )
    response = res.response

    assert response.status_code < 500
    assert "errors" in response.json()
    # The delete rolled back: the row survives.
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM products_item WHERE id = %s", (item_pk,))
        assert cursor.fetchone()[0] == 1


@pytest.mark.django_db(transaction=True)
def test_create_does_not_commit_when_response_completion_fails():
    """A create whose response can't be serialized must roll back, not leave a row."""
    create_users(1)
    client = _login_with_perm("view_item_1", "add_item")
    category_pk = _insert_category("raw-create-bad-date-category", created_date="not-a-date")

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


@pytest.mark.django_db(transaction=True)
def test_delete_does_not_commit_when_response_completion_fails():
    """A delete whose response can't be serialized must roll back, not remove the row."""
    create_users(1)
    client = _login_with_perm("staff_1", "delete_item")
    category_pk = _insert_category("raw-delete-bad-date-category", created_date="not-a-date")
    item_pk = _insert_item("raw-delete-bad-date-item", category_pk)

    response = _post_delete(client, item_pk)

    assert response.status_code < 500
    assert "errors" in response.json()
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM products_item WHERE id = %s", (item_pk,))
        remaining_count = cursor.fetchone()[0]
    assert remaining_count == 1


@pytest.mark.django_db(transaction=True)
def test_successful_update_still_commits_through_the_completion_spanning_transaction():
    """The completion-spanning transaction COMMITS a cleanly-serializable write.

    The rollback contract's other half: extending the transaction through
    completion must not turn every mutation read-only. A normal update over
    healthy rows completes, returns the success payload, and persists.
    """
    create_users(1)
    client = _login_with_perm("view_item_1", "view_category", "change_item")
    category_pk = _insert_category("healthy-commit-category")
    item_pk = _insert_item("healthy-commit-item", category_pk)

    response = _post_update(client, item_pk, name="committed-update")

    payload = response.json()
    assert response.status_code == 200
    assert "errors" not in payload, payload
    assert payload["data"]["updateItem"]["errors"] == []
    assert _stored_item_name(item_pk) == "committed-update"


@pytest.mark.django_db(transaction=True)
def test_serial_top_level_mutations_keep_independent_transactions():
    """Two serial top-level mutation fields: the second's completion failure rolls back
    ONLY the second's write - the first field's already-committed transaction survives.
    """
    create_users(1)
    client = _login_with_perm("view_item_1", "view_category", "change_item")
    healthy_category_pk = _insert_category("serial-healthy-category")
    corrupt_category_pk = _insert_category("serial-corrupt-category", created_date="not-a-date")
    first_pk = _insert_item("serial-first-item", healthy_category_pk)
    second_pk = _insert_item("serial-second-item", corrupt_category_pk)

    res = TestClient(client=client).query(
        _TWO_UPDATES,
        variables={
            "idA": _global_id("products.item", first_pk),
            "dA": {"name": "serial-first-updated"},
            "idB": _global_id("products.item", second_pk),
            "dB": {"name": "serial-second-updated"},
        },
        assert_no_errors=False,
    )

    payload = res.response.json()
    assert res.response.status_code < 500
    # The second field's completion failed (its category createdDate is corrupt);
    # the non-nullable error null-bubbles to the nearest nullable ancestor - the
    # payload's `node` slot - and surfaces as a top-level error...
    assert "errors" in payload
    assert payload["data"]["second"]["node"] is None
    # ...and only ITS write rolled back; the first field committed independently.
    assert payload["data"]["first"]["node"]["name"] == "serial-first-updated"
    assert _stored_item_name(first_pk) == "serial-first-updated"
    assert _stored_item_name(second_pk) == "serial-second-item"
