"""Tests for fakeshop.products.services — Faker-driven seeding and deletion services."""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from faker import Faker
from fakeshop.products import services
from fakeshop.products.models import Category, Entry, Item, Property

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_is_safe_generator_returns_true_for_scalar():
    fake = Faker()
    # ``name`` returns a str — must be accepted.
    assert services._is_safe_generator(fake, "name") is True


def test_is_safe_generator_returns_false_when_method_raises():
    fake = Faker()
    # A method name that doesn't exist will raise on attribute access — also a "False" path.
    assert services._is_safe_generator(fake, "no_such_method_xyz_123") is False


def test_is_safe_generator_returns_false_for_non_scalar():
    fake = Faker()
    # ``profile()`` returns a dict — non-scalar — must be rejected.
    assert services._is_safe_generator(fake, "profile") is False


def test_fake_value_returns_string():
    fake = Faker()
    out = services._fake_value(fake, "name")
    assert isinstance(out, str)
    assert out  # non-empty


def test_discover_providers_returns_dict_of_methods():
    """Smoke: discover_providers exercises all branches of the introspection loop."""
    fake = Faker()
    providers = services.discover_providers(fake)
    # Faker ships with at least a handful of providers; assert structure not exact counts.
    assert isinstance(providers, dict)
    assert len(providers) > 0
    for short_name, methods in providers.items():
        assert isinstance(short_name, str)
        assert "." not in short_name  # locale sub-packages are filtered
        assert isinstance(methods, list)
        assert len(methods) > 0
        for m in methods:
            assert isinstance(m, str)


def test_discover_providers_handles_module_without_provider_class():
    """If a sub-module lacks ``Provider``, discover_providers must skip it gracefully."""
    fake = Faker()
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        # Force the very first non-package submodule walked to look like a no-Provider module.
        mod = real_import(name, *args, **kwargs)
        return mod

    # Use a real provider but stub away its ``Provider`` attribute mid-discovery to hit the branch.
    import faker.providers.bank as bank_module

    original = bank_module.Provider
    try:
        del bank_module.Provider
        result = services.discover_providers(fake)
        assert "bank" not in result  # skipped because Provider is gone
    finally:
        bank_module.Provider = original


def test_discover_providers_handles_import_error():
    """If ``__import__`` raises ImportError on a sub-package, discover_providers continues."""
    fake = Faker()
    real_import = __import__

    def boom_import(name, *args, **kwargs):
        if name == "faker.providers.bank":
            raise ImportError("synthetic")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=boom_import):
        result = services.discover_providers(fake)
    assert "bank" not in result


def test_discover_providers_handles_unsignaturable_method():
    """When ``inspect.signature`` raises, discover_providers continues."""
    fake = Faker()
    real_signature = services.inspect.signature

    def boom_signature(obj, *args, **kwargs):
        # Trigger only on an arbitrary callable so the rest still runs.
        if getattr(obj, "__name__", "") == "name":
            raise ValueError("synthetic")
        return real_signature(obj, *args, **kwargs)

    with patch.object(services.inspect, "signature", side_effect=boom_signature):
        result = services.discover_providers(fake)
    # The "person" provider's ``name`` method should now be excluded.
    assert "name" not in result.get("person", [])


# ---------------------------------------------------------------------------
# seed_data
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_seed_data_creates_expected_counts():
    result = services.seed_data(1)
    assert result["categories"] == Category.objects.count()
    assert result["properties"] == Property.objects.count()
    assert result["items"] == Item.objects.count()
    assert result["entries"] == Entry.objects.count()
    # Total tracks the formula: rows = categories + properties + (categories * X) + (properties * X)
    assert Item.objects.count() == Category.objects.count()  # X=1, so one item per category
    assert Entry.objects.count() == Property.objects.count()  # one entry per property


@pytest.mark.django_db
def test_seed_data_idempotent_on_categories_and_properties(monkeypatch):
    """A second seed at the same X creates 0 new categories/properties (and only fills item shortfall).

    ``discover_providers`` is non-deterministic across calls because some Faker probe methods
    have random branches; pin the providers dict so both seed_data calls see the same shape.
    """
    fixed = services.discover_providers(Faker())
    monkeypatch.setattr(services, "discover_providers", lambda _fake: fixed)

    services.seed_data(1)
    second = services.seed_data(1)
    assert second["categories"] == 0
    assert second["properties"] == 0
    assert second["items"] == 0
    assert second["entries"] == 0


@pytest.mark.django_db
def test_seed_data_creates_only_shortfall_when_x_grows(monkeypatch):
    """Bumping X from 1 to 2 should create exactly one extra item per provider.

    Pin ``discover_providers`` across both seed_data calls so the property/method shape is identical.
    """
    fixed = services.discover_providers(Faker())
    monkeypatch.setattr(services, "discover_providers", lambda _fake: fixed)

    services.seed_data(1)
    cat_count = Category.objects.count()
    total_props = Property.objects.count()
    second = services.seed_data(2)
    assert second["items"] == cat_count  # one new item per category
    # Each new item gets one entry per property in its category
    assert second["entries"] == total_props


# ---------------------------------------------------------------------------
# delete_data
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_data_int_mode_deletes_first_n_items():
    services.seed_data(2)
    items_before = Item.objects.count()
    entries_before = Entry.objects.count()

    result = services.delete_data(3)

    assert result["items"] == 3
    assert Item.objects.count() == items_before - 3
    assert result["entries"] > 0
    assert Entry.objects.count() == entries_before - result["entries"]
    # Categories and properties untouched
    assert result["categories"] == 0
    assert result["properties"] == 0


@pytest.mark.django_db
def test_delete_data_int_mode_no_data_returns_zeros():
    """When no items exist, the int-mode branch short-circuits before any deletes."""
    result = services.delete_data(5)
    assert result == {"categories": 0, "properties": 0, "items": 0, "entries": 0}


@pytest.mark.django_db
def test_delete_data_all_mode_clears_items_and_entries():
    services.seed_data(1)
    cat_count = Category.objects.count()
    prop_count = Property.objects.count()

    result = services.delete_data("all")

    assert result["items"] > 0
    assert result["entries"] > 0
    assert Item.objects.count() == 0
    assert Entry.objects.count() == 0
    # Categories and properties survive
    assert Category.objects.count() == cat_count
    assert Property.objects.count() == prop_count


@pytest.mark.django_db
def test_delete_data_everything_mode_wipes_all_tables():
    services.seed_data(1)
    result = services.delete_data("everything")
    assert result["categories"] > 0
    assert result["properties"] > 0
    assert result["items"] > 0
    assert result["entries"] > 0
    assert Category.objects.count() == 0
    assert Property.objects.count() == 0
    assert Item.objects.count() == 0
    assert Entry.objects.count() == 0


# ---------------------------------------------------------------------------
# create_users / delete_users
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_users_creates_six_users_per_unit():
    """One unit = staff + regular + 4 per-permission users = 6 users."""
    result = services.create_users(1)
    assert result["users"] == 6
    assert User.objects.count() == 6
    # Verify each per-permission user has exactly the matching permission
    for codename in services.VIEW_PERMISSIONS:
        user = User.objects.get(username=f"{codename}_1")
        assert user.user_permissions.filter(codename=codename).count() == 1
        assert user.is_staff is False
    # Staff and regular users exist
    assert User.objects.filter(username="staff_1", is_staff=True).count() == 1
    assert User.objects.filter(username="regular_1", is_staff=False).count() == 1


@pytest.mark.django_db
def test_create_users_is_idempotent():
    services.create_users(1)
    second = services.create_users(1)
    assert second["users"] == 0
    assert User.objects.count() == 6


@pytest.mark.django_db
def test_delete_users_int_mode_deletes_first_n_non_superusers():
    services.create_users(2)
    User.objects.create_superuser(username="boss", password="boss")
    pre = User.objects.count()
    result = services.delete_users(3)
    assert result["users"] == 3
    assert User.objects.count() == pre - 3
    # Superuser preserved
    assert User.objects.filter(username="boss").exists()


@pytest.mark.django_db
def test_delete_users_int_mode_no_data_returns_zero():
    result = services.delete_users(5)
    assert result == {"users": 0}


@pytest.mark.django_db
def test_delete_users_all_mode_wipes_non_superusers():
    services.create_users(1)
    User.objects.create_superuser(username="boss", password="boss")
    result = services.delete_users("all")
    assert result["users"] == 6
    assert User.objects.filter(is_superuser=True).count() == 1
    assert User.objects.filter(is_superuser=False).count() == 0
