"""Package settings-reader tests for DJANGO_STRAWBERRY_FRAMEWORK."""

from types import MappingProxyType

import pytest

from django_strawberry_framework import conf
from django_strawberry_framework.conf import (
    Settings,
    reload_settings,
    testing_endpoint_setting,
    upstream_patches_enabled,
)
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
    setattr(
        django_settings,
        conf.DJANGO_SETTINGS_KEY,
        ["not", "a", "mapping"],
    )
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
    rather than rebinding the module global - otherwise the docstring's
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


def test_settings_uninitialized_user_settings_does_not_recurse():
    """Accessing _user_settings on an uninitialized Settings object raises AttributeError directly instead of recursing."""
    s = Settings.__new__(Settings)
    with pytest.raises(AttributeError, match="_user_settings"):
        _ = s._user_settings


def test_settings_normalization_attribute_error_does_not_recurse(monkeypatch):
    """An AttributeError in _normalize_user_settings must not trigger infinite recursion in __getattr__."""

    def racy_normalize(value):
        raise AttributeError("Simulated normalization AttributeError")

    monkeypatch.setattr(conf, "_normalize_user_settings", racy_normalize)
    s = Settings()
    with pytest.raises(AttributeError, match="user_settings"):
        _ = s.SOME_KEY


# ---------------------------------------------------------------------------
# upstream_patches_enabled (APPLY_UPSTREAM_PATCHES toggle)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dependency", sorted(conf.UPSTREAM_PATCH_DEPENDENCIES))
def test_upstream_patches_enabled_defaults_true_when_key_absent(settings, dependency):
    """Missing key (or whole dict) -> ``True``: consumers opt out, not in."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {}
    assert upstream_patches_enabled(dependency) is True


@pytest.mark.parametrize("dependency", sorted(conf.UPSTREAM_PATCH_DEPENDENCIES))
def test_upstream_patches_enabled_true_when_set_true(settings, dependency):
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": True}
    assert upstream_patches_enabled(dependency) is True


@pytest.mark.parametrize("dependency", sorted(conf.UPSTREAM_PATCH_DEPENDENCIES))
def test_upstream_patches_enabled_false_when_set_false(settings, dependency):
    """The plain global ``False`` keeps its pre-mapping semantics (back-compat)."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}
    assert upstream_patches_enabled(dependency) is False


def test_upstream_patches_enabled_mapping_opts_out_per_dependency(settings):
    """A mapping disables exactly the named dependency; missing names stay on.

    The rev-apps.md Medium-2 escape hatch: ``{"django": False}`` silences the
    test-only Django patch without dropping the production request-hardening
    patches (``strawberry`` / ``cross_web``).
    """
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"django": False}}
    assert upstream_patches_enabled("django") is False
    assert upstream_patches_enabled("strawberry") is True
    assert upstream_patches_enabled("cross_web") is True


@pytest.mark.parametrize("dependency", sorted(conf.UPSTREAM_PATCH_DEPENDENCIES))
def test_upstream_patches_enabled_empty_mapping_keeps_every_patch_on(settings, dependency):
    """An empty mapping is "no opt-outs", identical to the missing key."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {}}
    assert upstream_patches_enabled(dependency) is True


def test_upstream_patches_enabled_mapping_accepts_non_dict_mappings(settings):
    """Any ``Mapping`` works, mirroring ``_normalize_user_settings``'s contract."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {
        "APPLY_UPSTREAM_PATCHES": MappingProxyType({"strawberry": False}),
    }
    assert upstream_patches_enabled("strawberry") is False
    assert upstream_patches_enabled("django") is True


def test_upstream_patches_enabled_rejects_unknown_mapping_name(settings):
    """A typo'd dependency name must not silently keep patching.

    The whole mapping is validated on every read: the raise fires even when
    the requested dependency itself is spelled correctly.
    """
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"stawberry": False}}
    with pytest.raises(ConfigurationError, match="stawberry"):
        upstream_patches_enabled("django")


def test_upstream_patches_enabled_rejects_non_bool_mapping_value(settings):
    """``{"django": "false"}`` must fail loud, not silently invert intent."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"django": "false"}}
    with pytest.raises(ConfigurationError, match="must be a bool"):
        upstream_patches_enabled("django")


def test_upstream_patches_enabled_rejects_non_string_mapping_key(settings):
    """A non-string mapping key gets the ``ConfigurationError`` framing, not a ``TypeError``.

    Mixed unorderable key types (``{1: False, "x": False}``) once leaked
    ``TypeError: '<' not supported`` from the unknown-name framing's
    ``sorted()`` while building the error message; the key-type guard runs
    first (the ``types/base.py::_validate_relation_shapes`` precedent) so the
    docstring-promised ``ConfigurationError`` fires instead.
    """
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {1: False, "x": False}}
    with pytest.raises(ConfigurationError, match="dependency name strings"):
        upstream_patches_enabled("django")


@pytest.mark.parametrize(
    "value",
    [
        "false",
        0,
        1,
        None,
    ],
)
def test_upstream_patches_enabled_rejects_non_bool_non_mapping_value(settings, value):
    """A non-bool/non-mapping top-level value fails loud.

    Closes the old ``bool()`` coercion's silent wrong-shape acceptance: a
    ``"false"`` string was truthy and ENABLED the patches; ``0``/``1``
    silently coerced. An explicit ``None`` is a per-key value, not the
    missing-key case, so it is rejected like any other wrong shape.
    """
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": value}
    with pytest.raises(ConfigurationError, match="bool or a mapping"):
        upstream_patches_enabled("django")


def test_upstream_patches_enabled_rejects_unknown_dependency_argument():
    """The gate call sites and ``UPSTREAM_PATCH_DEPENDENCIES`` cannot drift.

    A future patch module whose ``apply()`` passes a name missing from the
    constant would otherwise be silently un-opt-out-able; the internal-API
    guard fails loud at the first gate read instead.
    """
    with pytest.raises(ValueError, match="graphql_core"):
        upstream_patches_enabled("graphql_core")


# ---------------------------------------------------------------------------
# testing_endpoint_setting pytest-collection guard
# ---------------------------------------------------------------------------


def test_testing_endpoint_setting_carries_pytest_collection_guard():
    """The reader's ``test*``-matching name must never be collected as a test.

    Self-proving: this module imports ``testing_endpoint_setting`` UNALIASED,
    so if the ``__test__ = False`` guard is ever dropped, pytest collects the
    function, its ``str`` return trips ``PytestReturnNotNoneWarning``, and
    the suite fails under ``filterwarnings = error`` at this very import.
    """
    assert testing_endpoint_setting.__test__ is False


# ---------------------------------------------------------------------------
# Live sync when django.conf mutates without setting_changed
# ---------------------------------------------------------------------------


def test_delattr_clears_stale_cache_and_restores_defaults(settings):
    """``del settings.DJANGO_STRAWBERRY_FRAMEWORK`` must not leave stale overrides.

    pytest-django's ``SettingsWrapper.__delattr__`` deletes the key on a
    ``UserSettingsHolder`` without emitting ``setting_changed`` for that key.
    A signal-only cache would keep serving the prior mapping (wrong
    ``APPLY_UPSTREAM_PATCHES`` / endpoint / strategy / hide-flat values).
    Django-backed live sync rebuilds from the absent key as empty settings.
    """
    from django_strawberry_framework.conf import (
        hide_flat_filters_setting,
        nested_connection_strategy_setting,
        testing_endpoint_setting,
    )

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {
        "FILTER_KEY": "x",
        "APPLY_UPSTREAM_PATCHES": False,
        "NESTED_CONNECTION_STRATEGY": "eager",
        "TESTING_ENDPOINT": "/custom/",
        "HIDE_FLAT_FILTERS": True,
    }
    assert conf.settings.FILTER_KEY == "x"
    assert upstream_patches_enabled("django") is False
    assert nested_connection_strategy_setting() == "eager"
    assert testing_endpoint_setting() == "/custom/"
    assert hide_flat_filters_setting() is True

    del settings.DJANGO_STRAWBERRY_FRAMEWORK

    assert conf.settings.user_settings == {}
    with pytest.raises(AttributeError, match="Invalid setting: `FILTER_KEY`"):
        _ = conf.settings.FILTER_KEY
    assert upstream_patches_enabled("django") is True
    assert nested_connection_strategy_setting() == "windowed"
    assert testing_endpoint_setting() == "/graphql/"
    assert hide_flat_filters_setting() is False


def test_django_backed_resync_fails_loud_after_silent_bad_replacement(settings):
    """A live non-mapping that never reached ``reload`` must fail on next read.

    Covers the gap where ``django.conf.settings`` already holds a rejected
    shape (signal delivered it, ``reload`` raised before updating the cache,
    and the harness did not roll the live value back): the next
    django-backed read must raise ``ConfigurationError`` rather than keep
    serving the prior good mapping.
    """
    from django.conf import settings as django_settings
    from django.test.signals import setting_changed

    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"FILTER_KEY": "good"}
    assert conf.settings.FILTER_KEY == "good"

    # Commit a bad live value without going through override_settings' rollback,
    # then deliver the signal the same way a post-commit notifier would.
    # Prefer the public setattr path so LazySettings' cache bookkeeping stays
    # consistent (``object.__setattr__`` would shadow on the proxy).
    django_settings.DJANGO_STRAWBERRY_FRAMEWORK = ["bad"]
    with pytest.raises(ConfigurationError, match="must be a mapping"):
        setting_changed.send(
            sender=type(django_settings),
            setting=conf.DJANGO_SETTINGS_KEY,
            value=["bad"],
            enter=True,
        )
    with pytest.raises(ConfigurationError, match="must be a mapping"):
        _ = conf.settings.user_settings
    # A rejected normalize must not bind the bad live object as a successful
    # cache key; every subsequent read retries and fails loud again.
    with pytest.raises(ConfigurationError, match="must be a mapping"):
        _ = conf.settings.FILTER_KEY

    # Restore a valid mapping so later tests / fixture teardown are clean.
    django_settings.DJANGO_STRAWBERRY_FRAMEWORK = {}
    conf.settings.reload({})


def test_explicit_settings_instance_ignores_django_delattr(settings):
    """``Settings(mapping)`` is not django-backed; live django changes must not clobber it."""
    s = Settings({"OWN": 1})
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"OTHER": 2}
    del settings.DJANGO_STRAWBERRY_FRAMEWORK
    assert s.user_settings == {"OWN": 1}
    assert s.OWN == 1
