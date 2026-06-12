"""Fakeshop project URL tests for the index view and URL configuration."""

import pytest
from django.test import Client


@pytest.mark.django_db
def test_index_view_renders_dev_links():
    client = Client()
    response = client.get("/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "Fakeshop Dev Links" in body
    assert "/graphql/" in body
    assert "/admin/" in body
    assert "seed_data" in body
    assert "delete_data" in body
    assert "create_users" in body
    assert "delete_users" in body
