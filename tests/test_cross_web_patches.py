"""Tests for the ``cross_web`` non-UTF-8 request-body patch.

System-under-test: :mod:`django_strawberry_framework._cross_web_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

The patch makes the **sync** ``DjangoHTTPRequestAdapter.body`` fall back
to the raw request bytes when the body is not valid UTF-8, instead of
letting the bare ``self.request.body.decode()`` raise
``UnicodeDecodeError`` before Strawberry's ``parse_json`` is even
entered. The decoded-cleanly path is byte-for-byte unchanged from
upstream.
"""

from unittest import mock

from cross_web import DjangoHTTPRequestAdapter

from django_strawberry_framework import _cross_web_patches as patches


class _FakeRequest:
    """Minimal stand-in for Django's ``HttpRequest`` exposing ``.body``."""

    def __init__(self, body: bytes) -> None:
        self.body = body


def test_apply_is_idempotent():
    """Repeated ``apply()`` calls leave the patch installed (self-healing no-op)."""
    patches.apply()
    patches.apply()
    assert patches._patch_is_installed() is True


def test_apply_reinstalls_when_property_reverted():
    """``apply()`` re-installs if a third party reverted ``adapter.body``."""
    patches.apply()
    assert patches._patch_is_installed() is True

    saved = DjangoHTTPRequestAdapter.__dict__["body"]
    try:
        DjangoHTTPRequestAdapter.body = property(patches._original_body_fget)
        assert patches._patch_is_installed() is False

        patches.apply()
        assert patches._patch_is_installed() is True
    finally:
        DjangoHTTPRequestAdapter.body = saved


def test_patch_is_installed_on_adapter():
    """By the time pytest collects, ``AppConfig.ready()`` has installed the wrapper."""
    descriptor = DjangoHTTPRequestAdapter.__dict__["body"]
    assert isinstance(descriptor, property)
    assert descriptor.fget is patches._patched_body


def test_body_returns_str_for_valid_utf8():
    """The success path is untouched: a decodable body returns the decoded ``str``."""
    adapter = DjangoHTTPRequestAdapter(_FakeRequest(b'{"a": 1}'))
    assert adapter.body == '{"a": 1}'


def test_body_returns_raw_bytes_for_invalid_utf8():
    """A non-UTF-8 body falls back to the raw bytes (so ``parse_json`` can 400 it)."""
    adapter = DjangoHTTPRequestAdapter(_FakeRequest(b"\xff\xfe\xfa"))
    assert adapter.body == b"\xff\xfe\xfa"


def test_patch_is_installed_false_when_symbol_missing():
    """``_patch_is_installed`` returns ``False`` when the adapter symbol moved."""
    with mock.patch.object(patches, "DjangoHTTPRequestAdapter", None):
        assert patches._patch_is_installed() is False


def test_apply_no_ops_when_symbol_missing(caplog):
    """When cross_web moved the adapter, ``apply()`` logs once and returns."""
    with (
        mock.patch.object(patches, "DjangoHTTPRequestAdapter", None),
        mock.patch.object(patches, "_missing_symbol_logged", False),
    ):
        with caplog.at_level("INFO", logger="django_strawberry_framework"):
            patches.apply()

        skip_records = [
            r
            for r in caplog.records
            if r.name == "django_strawberry_framework" and "body patch" in r.message
        ]
        assert len(skip_records) == 1
        assert skip_records[0].levelname == "INFO"


def test_apply_logs_missing_symbol_notice_only_once(caplog):
    """The missing-symbol INFO notice logs only once per process."""
    with (
        mock.patch.object(patches, "DjangoHTTPRequestAdapter", None),
        mock.patch.object(patches, "_missing_symbol_logged", False),
    ):
        with caplog.at_level("INFO", logger="django_strawberry_framework"):
            patches.apply()
            patches.apply()
            patches.apply()

        skip_records = [
            r
            for r in caplog.records
            if r.name == "django_strawberry_framework" and "body patch" in r.message
        ]
        assert len(skip_records) == 1


def test_apply_no_ops_when_toggle_disabled(settings):
    """``APPLY_UPSTREAM_PATCHES = False`` makes ``apply()`` decline to install."""
    saved = DjangoHTTPRequestAdapter.__dict__["body"]
    try:
        DjangoHTTPRequestAdapter.body = property(patches._original_body_fget)
        assert patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}
        patches.apply()
        assert patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": True}
        patches.apply()
        assert patches._patch_is_installed() is True
    finally:
        DjangoHTTPRequestAdapter.body = saved
