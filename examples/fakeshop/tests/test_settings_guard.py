"""Fakeshop settings-module pin: the development fixture fails loudly as production.

Fakeshop's unsafe settings (DEBUG on, a checked-in SECRET_KEY, GraphiQL, open
permission demonstrations) are deliberate test fixtures, appropriate only while
the module cannot be mistaken for a production settings module. These rows pin
the guard that keeps that true: flipping ``DEBUG`` off while keeping the rest is
an import-time ``ImproperlyConfigured``, never a quietly "hardened" fakeshop.

pytest-django flips ``django.conf.settings.DEBUG`` to ``False`` for the test
run AFTER the module import, so the module-level constant - the value the guard
saw at import - is asserted here directly on ``config.settings``.
"""

import pytest
from config import settings as fakeshop_settings
from django.core.exceptions import ImproperlyConfigured


def test_the_shipped_fixture_declares_debug_and_passed_its_own_guard_at_import():
    """The module imported (or no test could run) with ``DEBUG = True`` on it."""
    assert fakeshop_settings.DEBUG is True
    assert fakeshop_settings._require_development_settings(fakeshop_settings.DEBUG) is None


def test_a_production_debug_flag_is_refused_loudly_not_absorbed():
    """``DEBUG = False`` on these settings raises instead of loading."""
    with pytest.raises(ImproperlyConfigured, match="must never be deployed"):
        fakeshop_settings._require_development_settings(False)


def test_the_refusal_says_why_flipping_debug_is_not_a_hardening_step():
    """The message names the unsafe fixtures so the failure teaches the fix."""
    with pytest.raises(ImproperlyConfigured) as excinfo:
        fakeshop_settings._require_development_settings(False)
    message = str(excinfo.value)
    assert "SECRET_KEY" in message
    assert "build a separate project" in message
