"""Tests for django_strawberry_framework.conf."""

from types import MappingProxyType

import pytest

from django_strawberry_framework import conf
from django_strawberry_framework.conf import Settings, reload_settings
from django_strawberry_framework.exceptions import ConfigurationError

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
# Settings.user_settings (lazy-load + normalization)
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


def test_settings_user_settings_accepts_mapping_values():
    s = Settings(MappingProxyType({"X": "y"}))
    assert s.user_settings == {"X": "y"}


def test_settings_user_settings_falsy_falls_back_to_empty_dict(settings):
    """Setting our key to ``None`` should behave like no configured settings."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = None
    s = Settings()
    assert s.user_settings == {}


def test_settings_user_settings_rejects_non_mapping_django_setting(monkeypatch):
    django_settings = type("DjangoSettings", (), {})()
    setattr(django_settings, conf.DJANGO_SETTINGS_KEY, ["not", "a", "mapping"])
    monkeypatch.setattr(conf, "django_settings", django_settings)

    s = Settings()
    with pytest.raises(ConfigurationError, match="DJANGO_STRAWBERRY_FRAMEWORK.*list"):
        _ = s.user_settings


# ---------------------------------------------------------------------------
# reload_settings (via signal + direct invocation)
# ---------------------------------------------------------------------------


def test_reload_settings_refreshes_singleton_when_our_key_changes(settings):
    """Changing our key mutates the singleton ``settings`` instance in place."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"FILTER_KEY": "f1"}
    assert conf.settings.FILTER_KEY == "f1"
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"FILTER_KEY": "f2"}
    assert conf.settings.FILTER_KEY == "f2"


def test_reload_settings_for_unrelated_key_keeps_singleton():
    """Direct call with an unrelated key should not mutate the instance."""
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


# ---------------------------------------------------------------------------
# Dunder lookups + reload() helper + idempotent signal connect
# ---------------------------------------------------------------------------


def test_settings_dunder_lookup_raises_plain_attributeerror():
    """Dunder probes from introspection tools must not surface as 'Invalid setting'."""
    s = Settings({})
    with pytest.raises(AttributeError) as exc:
        s.__wrapped__
    assert "Invalid setting" not in str(exc.value)


def test_settings_reload_replaces_cached_mapping():
    s = Settings({"A": 1})
    s.reload({"B": 2})
    assert s.user_settings == {"B": 2}


def test_settings_reload_with_none_restores_lazy_load():
    s = Settings({"A": 1})
    s.reload(None)
    assert s._user_settings is None


def test_settings_reload_rejects_non_mapping_value():
    s = Settings({"A": 1})
    with pytest.raises(ConfigurationError, match="DJANGO_STRAWBERRY_FRAMEWORK.*str"):
        s.reload("bad")
    assert s.user_settings == {"A": 1}


def test_setting_changed_receiver_uses_dispatch_uid():
    """Re-connecting with the same dispatch_uid must be a no-op."""
    from django.test.signals import setting_changed

    from django_strawberry_framework.conf import _DISPATCH_UID, reload_settings

    before = len(setting_changed.receivers)
    setting_changed.connect(reload_settings, dispatch_uid=_DISPATCH_UID)
    after = len(setting_changed.receivers)
    assert before == after
