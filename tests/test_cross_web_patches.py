"""Tests for the ``cross_web`` non-UTF-8 request-body patch.

System-under-test: :mod:`django_strawberry_framework._cross_web_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

The patch replaces the **sync** ``DjangoHTTPRequestAdapter.body`` so it
always returns the raw request bytes (the async ``get_body`` contract)
instead of UTF-8-decoding first. That both stops undecodable bodies from
raising ``UnicodeDecodeError`` before ``parse_json`` and keeps
UTF-8-decodable non-UTF-8 JSON (BOM-less UTF-16/32, UTF-8 BOM) on the
bytes path ``json.loads`` accepts.
"""

from unittest import mock

import pytest
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


def test_body_returns_raw_bytes_for_valid_utf8():
    """Valid UTF-8 is returned as raw bytes (async parity), not decoded ``str``."""
    raw = b'{"a": 1}'
    adapter = DjangoHTTPRequestAdapter(_FakeRequest(raw))
    assert adapter.body == raw
    assert isinstance(adapter.body, bytes)


def test_body_returns_raw_bytes_for_invalid_utf8():
    """A non-UTF-8 body is returned as raw bytes (so ``parse_json`` can 400 it)."""
    adapter = DjangoHTTPRequestAdapter(_FakeRequest(b"\xff\xfe\xfa"))
    assert adapter.body == b"\xff\xfe\xfa"


def test_body_returns_raw_bytes_for_utf8_bom():
    """UTF-8 BOM must stay bytes - decoded ``str`` makes ``json.loads`` reject the body."""
    raw = b"\xef\xbb\xbf" + b'{"a": 1}'
    adapter = DjangoHTTPRequestAdapter(_FakeRequest(raw))
    assert adapter.body == raw
    assert isinstance(adapter.body, bytes)


def test_body_returns_raw_bytes_for_utf16_le_without_bom():
    """BOM-less UTF-16-LE is UTF-8-decodable (NUL-padded ASCII); must still be bytes.

    Upstream's ``.decode()`` succeeds and returns a NUL-studded ``str`` that
    ``json.loads`` rejects. The permanent ``encode("utf-16")`` e2e case includes
    a BOM that forces ``UnicodeDecodeError`` and masked this gap.
    """
    raw = '{"query":"{ __typename }"}'.encode("utf-16-le")
    # Sanity: upstream still "succeeds" into a str - that is the bug shape.
    assert isinstance(
        patches._original_body_fget(DjangoHTTPRequestAdapter(_FakeRequest(raw))),
        str,
    )
    adapter = DjangoHTTPRequestAdapter(_FakeRequest(raw))
    assert adapter.body == raw
    assert isinstance(adapter.body, bytes)


def test_patch_is_installed_false_when_symbol_missing():
    """``_patch_is_installed`` returns ``False`` when the adapter symbol moved."""
    with mock.patch.object(patches, "DjangoHTTPRequestAdapter", None):
        assert patches._patch_is_installed() is False


def test_apply_fails_loudly_when_symbol_missing():
    """A dependency-shape change cannot silently disable request hardening."""
    with mock.patch.object(patches, "DjangoHTTPRequestAdapter", None):
        with pytest.raises(RuntimeError, match="DjangoHTTPRequestAdapter"):
            patches.apply()


def test_apply_fails_loudly_when_body_getter_signature_changes():
    """The patch pins the getter arity it replaces."""
    with mock.patch.object(patches, "_original_body_fget", lambda self, extra: None):
        with pytest.raises(RuntimeError, match=r"expected \(self\) getter signature"):
            patches.apply()


def test_apply_fails_loudly_when_original_getter_was_never_captured():
    """A valid-looking live ``body`` property cannot mask a missing capture.

    When the import-time capture never happened (``_original_body_fget`` is the
    ``None`` sentinel), ``apply()`` must refuse to install even though the live
    descriptor is a perfectly-shaped property: shape validation would otherwise
    have nothing authoritative to pin against. Pins that the shape validation
    inspects the captured getter, not the live descriptor.
    """
    saved = DjangoHTTPRequestAdapter.__dict__["body"]
    try:
        DjangoHTTPRequestAdapter.body = property(patches._original_body_fget)
        assert patches._patch_is_installed() is False

        with mock.patch.object(patches, "_original_body_fget", None):
            with pytest.raises(RuntimeError, match="no longer a readable property"):
                patches.apply()
            assert patches._patch_is_installed() is False
    finally:
        DjangoHTTPRequestAdapter.body = saved


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


def test_apply_no_ops_when_cross_web_dependency_opted_out(settings):
    """``{"cross_web": False}`` disables only this module; ``{"django": False}`` does not.

    The production half of the rev-apps.md Medium-2 scenario: opting out of
    the test-only Django patch alone leaves this request hardening
    installing normally (each gate reads its own dependency name).
    """
    saved = DjangoHTTPRequestAdapter.__dict__["body"]
    try:
        DjangoHTTPRequestAdapter.body = property(patches._original_body_fget)
        assert patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"cross_web": False}}
        patches.apply()
        assert patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"django": False}}
        patches.apply()
        assert patches._patch_is_installed() is True
    finally:
        DjangoHTTPRequestAdapter.body = saved
