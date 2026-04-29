"""Tests for fakeshop.products.admin — covers the changelist_view query-param branches."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from fakeshop.products.models import Category, Item
from fakeshop.products.services import create_users, seed_data

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_client(db):
    """Logged-in superuser client for hitting admin URLs."""
    User.objects.create_superuser(username="admin", password="admin", email="admin@example.com")
    client = Client()
    client.login(username="admin", password="admin")
    return client


# ---------------------------------------------------------------------------
# UserAdmin: create_users / delete_users query params
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_user_admin_changelist_no_query_params(admin_client):
    response = admin_client.get("/admin/auth/user/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_admin_create_users_success(admin_client):
    response = admin_client.get("/admin/auth/user/?create_users=1")
    assert response.status_code == 302
    # 1 superuser + 6 from create_users(1) = 7
    assert User.objects.count() == 7


@pytest.mark.django_db
def test_user_admin_create_users_zero_does_not_create(admin_client):
    response = admin_client.get("/admin/auth/user/?create_users=0")
    assert response.status_code == 302
    assert User.objects.count() == 1  # only the admin


@pytest.mark.django_db
def test_user_admin_create_users_invalid(admin_client):
    response = admin_client.get("/admin/auth/user/?create_users=abc", follow=True)
    assert response.status_code == 200
    assert b"Invalid value for create_users" in response.content


@pytest.mark.django_db
def test_user_admin_delete_users_int_mode_success(admin_client):
    create_users(1)  # 6 non-superusers
    response = admin_client.get("/admin/auth/user/?delete_users=3")
    assert response.status_code == 302
    # Started with 7 (admin + 6), deleted 3, left with 4
    assert User.objects.count() == 4


@pytest.mark.django_db
def test_user_admin_delete_users_no_data_warns(admin_client):
    response = admin_client.get("/admin/auth/user/?delete_users=5")
    assert response.status_code == 302
    # No non-superusers to delete; admin survives
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_user_admin_delete_users_invalid(admin_client):
    response = admin_client.get("/admin/auth/user/?delete_users=garbage", follow=True)
    assert response.status_code == 200
    assert b"Invalid value for delete_users" in response.content


# ---------------------------------------------------------------------------
# ItemAdmin: seed_data / delete_data query params
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_item_admin_changelist_no_query_params(admin_client):
    response = admin_client.get("/admin/products/item/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_item_admin_seed_data_success(admin_client):
    response = admin_client.get("/admin/products/item/?seed_data=1")
    assert response.status_code == 302
    assert Category.objects.count() > 0


@pytest.mark.django_db
def test_item_admin_seed_data_zero_does_not_create(admin_client):
    response = admin_client.get("/admin/products/item/?seed_data=0")
    assert response.status_code == 302
    assert Category.objects.count() == 0


@pytest.mark.django_db
def test_item_admin_seed_data_invalid(admin_client):
    response = admin_client.get("/admin/products/item/?seed_data=abc", follow=True)
    assert response.status_code == 200
    assert b"Invalid value for seed_data" in response.content


@pytest.mark.django_db
def test_item_admin_delete_data_int_mode(admin_client):
    seed_data(2)
    response = admin_client.get("/admin/products/item/?delete_data=3")
    assert response.status_code == 302
    # 50 items minus 3 = 47 (Faker has 25 providers, X=2 => 50 items)
    assert Item.objects.count() < 50


@pytest.mark.django_db
def test_item_admin_delete_data_all_mode(admin_client):
    seed_data(1)
    response = admin_client.get("/admin/products/item/?delete_data=all")
    assert response.status_code == 302
    assert Item.objects.count() == 0


@pytest.mark.django_db
def test_item_admin_delete_data_everything_mode(admin_client):
    seed_data(1)
    response = admin_client.get("/admin/products/item/?delete_data=everything")
    assert response.status_code == 302
    assert Category.objects.count() == 0


@pytest.mark.django_db
def test_item_admin_delete_data_nothing_to_delete(admin_client):
    response = admin_client.get("/admin/products/item/?delete_data=5")
    assert response.status_code == 302
    # Nothing to delete; "summary" branch is "nothing"


@pytest.mark.django_db
def test_item_admin_delete_data_invalid(admin_client):
    response = admin_client.get("/admin/products/item/?delete_data=garbage", follow=True)
    assert response.status_code == 200
    assert b"Invalid value for delete_data" in response.content
