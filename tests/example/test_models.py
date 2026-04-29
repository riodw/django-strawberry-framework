"""Tests for example app models — covers the __str__ implementations.

Per AGENTS.md: every test seeds via ``services.seed_data`` first, never
hand-rolls Category/Item/Property/Entry instances.
"""

import pytest
from fakeshop.products.models import Category, Entry, Item, Property
from fakeshop.products.services import seed_data


@pytest.mark.django_db
def test_category_str_returns_name():
    seed_data(1)
    cat = Category.objects.first()
    assert str(cat) == cat.name


@pytest.mark.django_db
def test_item_str_returns_name():
    seed_data(1)
    item = Item.objects.first()
    assert str(item) == item.name


@pytest.mark.django_db
def test_property_str_returns_name():
    seed_data(1)
    prop = Property.objects.first()
    assert str(prop) == prop.name


@pytest.mark.django_db
def test_entry_str_returns_value():
    seed_data(1)
    entry = Entry.objects.first()
    assert str(entry) == entry.value
