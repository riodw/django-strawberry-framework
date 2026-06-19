"""Tests for the Strawberry non-UTF-8 request-body patch.

System-under-test: :mod:`django_strawberry_framework._strawberry_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

The patch widens :meth:`strawberry.http.base.BaseView.parse_json` to
translate ``UnicodeDecodeError`` (raised by ``json.loads`` on a
non-UTF-8 body) into the same ``HTTPException(400, ...)`` Strawberry
already raises for malformed JSON. Without it, a non-UTF-8 request body
surfaces as an unhandled ``500`` because ``UnicodeDecodeError`` is a
``ValueError``, not a ``json.JSONDecodeError``, and escapes upstream's
``except``.
"""

from unittest import mock

import pytest
from cross_web import HTTPException
from strawberry.http.base import BaseView

from django_strawberry_framework import _strawberry_patches as patches


def test_apply_is_idempotent():
    """Repeated ``apply()`` calls leave the patch installed (self-healing no-op)."""
    patches.apply()
    patches.apply()
    assert patches._patch_is_installed() is True


def test_apply_reinstalls_when_method_reverted():
    """``apply()`` re-installs if a third party reverted ``BaseView.parse_json``."""
    patches.apply()
    assert patches._patch_is_installed() is True

    saved = BaseView.__dict__["parse_json"]
    try:
        BaseView.parse_json = patches._original_parse_json
        assert patches._patch_is_installed() is False

        patches.apply()
        assert patches._patch_is_installed() is True
    finally:
        BaseView.parse_json = saved


def test_patch_is_installed_on_base_view():
    """By the time pytest collects, ``AppConfig.ready()`` has installed the wrapper."""
    assert BaseView.__dict__["parse_json"] is patches._patched_parse_json


def test_patched_parse_json_translates_unicode_decode_error():
    """A non-UTF-8 body -> controlled ``HTTPException(400)``, not ``UnicodeDecodeError``."""
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_json(BaseView(), b'{"a":"\xff\xfe"}')
    assert excinfo.value.status_code == 400


def test_patched_parse_json_passes_through_valid_json():
    """The success path is untouched: valid JSON parses exactly as upstream."""
    assert patches._patched_parse_json(BaseView(), b'{"a": 1}') == {"a": 1}


def test_patched_parse_json_passes_through_malformed_json_as_400():
    """Malformed (but UTF-8) JSON still becomes upstream's ``HTTPException(400)``.

    Pins that the wrapper does not regress Strawberry's existing
    ``json.JSONDecodeError -> 400`` handling - that error is raised by
    the delegated original and passes through the wrapper untouched.
    """
    with pytest.raises(HTTPException) as excinfo:
        patches._patched_parse_json(BaseView(), "{not valid json")
    assert excinfo.value.status_code == 400


def test_patch_is_installed_false_when_base_view_symbol_missing():
    """``_patch_is_installed`` short-circuits to ``False`` when the symbol moved."""
    with mock.patch.object(patches, "BaseView", None):
        assert patches._patch_is_installed() is False


def test_apply_no_ops_when_symbols_missing(caplog):
    """When Strawberry/cross_web moved the symbols, ``apply()`` logs once and returns."""
    with (
        mock.patch.object(patches, "BaseView", None),
        mock.patch.object(patches, "HTTPException", None),
        mock.patch.object(patches, "_missing_symbol_logged", False),
    ):
        with caplog.at_level("INFO", logger="django_strawberry_framework"):
            patches.apply()

        skip_records = [
            r
            for r in caplog.records
            if r.name == "django_strawberry_framework" and "parse_json patch" in r.message
        ]
        assert len(skip_records) == 1
        assert skip_records[0].levelname == "INFO"


def test_apply_logs_missing_symbol_notice_only_once(caplog):
    """The missing-symbol INFO notice logs only once per process."""
    with (
        mock.patch.object(patches, "BaseView", None),
        mock.patch.object(patches, "HTTPException", None),
        mock.patch.object(patches, "_missing_symbol_logged", False),
    ):
        with caplog.at_level("INFO", logger="django_strawberry_framework"):
            patches.apply()
            patches.apply()
            patches.apply()

        skip_records = [
            r
            for r in caplog.records
            if r.name == "django_strawberry_framework" and "parse_json patch" in r.message
        ]
        assert len(skip_records) == 1


def test_apply_no_ops_when_toggle_disabled(settings):
    """``APPLY_UPSTREAM_PATCHES = False`` makes ``apply()`` decline to install."""
    saved = BaseView.__dict__["parse_json"]
    try:
        BaseView.parse_json = patches._original_parse_json
        assert patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}
        patches.apply()
        assert patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": True}
        patches.apply()
        assert patches._patch_is_installed() is True
    finally:
        BaseView.parse_json = saved
