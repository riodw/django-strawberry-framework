"""Tests for django_strawberry_framework.conf."""

import pytest

from django_strawberry_framework import conf
from django_strawberry_framework.conf import Settings, reload_settings

# ---------------------------------------------------------------------------
# Settings.__getattr__
# ---------------------------------------------------------------------------


def test_settings_invalid_attribute_raises():
    s = Settings({})
    with pytest.raises(AttributeError, match="Invalid setting: `BOGUS`"):
        s.BOGUS


def test_settings_returns_user_setting_when_provided():
    s = Settings({"FILTER_KEY": "where"})
    assert s.FILTER_KEY == "where"


# ---------------------------------------------------------------------------
# Settings.user_settings (lazy-load + falsy fallback)
# ---------------------------------------------------------------------------


def test_settings_user_settings_lazy_loads_from_django_settings():
    """First access triggers a read from ``django.conf.settings``."""
    s = Settings()
    assert s._user_settings is None
    _ = s.user_settings
    assert s._user_settings is not None


def test_settings_user_settings_returns_preset_value():
    s = Settings({"X": "y"})
    assert s.user_settings == {"X": "y"}


def test_settings_user_settings_falsy_falls_back_to_empty_dict(settings):
    """Setting our key to ``None`` should yield ``{}`` via ``or {}``."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = None
    s = Settings()
    assert s.user_settings == {}


# ---------------------------------------------------------------------------
# reload_settings (via signal + direct invocation)
# ---------------------------------------------------------------------------


def test_reload_settings_replaces_global_when_our_key_changes(settings):
    """Changing our key replaces the module-level ``settings`` instance."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"FILTER_KEY": "f1"}
    assert conf.settings.FILTER_KEY == "f1"
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"FILTER_KEY": "f2"}
    assert conf.settings.FILTER_KEY == "f2"


def test_reload_settings_for_unrelated_key_keeps_global():
    """Direct call with an unrelated key should not replace the instance."""
    sentinel = conf.settings
    reload_settings("UNRELATED_SETTING", "value")
    assert conf.settings is sentinel


def test_reload_settings_updates_already_imported_reference(settings):
    """A reference bound via ``from .conf import settings`` must see updates.

    Pins the contract that ``reload_settings`` mutates the existing instance
    rather than rebinding the module global — otherwise the docstring's
    recommended import pattern breaks under ``override_settings`` /
    ``pytest-django``'s ``settings`` fixture.
    """
    from django_strawberry_framework.conf import settings as bound_settings

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"FILTER_KEY": "first"}
    assert bound_settings.FILTER_KEY == "first"
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"FILTER_KEY": "second"}
    assert bound_settings.FILTER_KEY == "second"
    assert bound_settings is conf.settings
