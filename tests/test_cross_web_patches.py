"""Tests for the ``cross_web`` non-UTF-8 request-body patch.

System-under-test: :mod:`django_strawberry_framework._cross_web_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

The patch replaces the **sync** ``DjangoHTTPRequestAdapter.body`` so it
always returns the raw request bytes (the async ``get_body`` contract)
instead of UTF-8-decoding first.

What stays here, and why a live request cannot express it:

- ``apply()`` lifecycle: idempotence, self-heal after a third-party revert,
  ``AppConfig.ready()`` having installed the wrapper by collection,
  missing-symbol / missing-capture / signature-drift refusals, and the
  ``APPLY_UPSTREAM_PATCHES`` global and per-dependency toggles. Those are
  install-time contracts; a GraphQL document cannot show that ``apply()``
  was the caller or that a missing capture refused to install.
- The adapter-property contract: ``body`` returns ``bytes`` without
  decoding. A wire ``400`` is identical whether the adapter handed over
  bytes or a ``str``; only an in-process read of the property can pin the
  return type. The captured upstream getter still decoding BOM-less
  UTF-16-LE into a ``str`` is the same class of fact (why the patch must
  return bytes rather than wrap ``.decode()``).

Wire shape lives live. UTF-16 / UTF-32 (BOM and BOM-less) and a leading
UTF-8 BOM are a controlled ``400`` on fakeshop's ``/graphql/`` in
``examples/fakeshop/test_query/test_products_api.py``; the async colour,
the ``APPLY_UPSTREAM_PATCHES`` opt-out matrix, and the ``cross_web``
half's 500-to-400 delta on Strawberry's own mount live in
``examples/fakeshop/test_query/test_transport_api.py``. Which mechanism
refused which byte shape (``__cause__``) is invisible over the wire and
stays in ``tests/test_views.py``.
"""

from unittest import mock

import pytest
from cross_web import DjangoHTTPRequestAdapter

from django_strawberry_framework import _cross_web_patches as patches


class _FakeRequest:
    """Minimal stand-in for Django's ``HttpRequest`` exposing ``.body``."""

    def __init__(self, body: bytes) -> None:
        self.body = body


class _MalformedAdapter:
    body = object()


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
    """A non-UTF-8 body is returned as raw bytes, so the strict decode can 400 it.

    The adapter must not examine the bytes at all. Upstream's eager decode
    raises here - inside a ``property``, outside any ``except`` that could turn
    it into a response - which is the whole reason this getter exists. Handing
    the bytes over unexamined puts the raise one frame later, inside a
    ``parse_json`` that can translate it into a controlled ``400``. The live
    ``400`` is
    ``test_products_api.py::test_post_invalid_utf8_json_body_returns_400_not_500``;
    the 500-to-400 delta on Strawberry's own mount is
    ``test_transport_api.py::test_the_cross_web_half_turns_upstreams_own_500_into_a_400``.
    """
    adapter = DjangoHTTPRequestAdapter(_FakeRequest(b"\xff\xfe\xfa"))
    assert adapter.body == b"\xff\xfe\xfa"


def test_body_returns_raw_bytes_for_utf8_bom():
    """UTF-8 BOM stays bytes here; the package view's parse is what rejects it.

    The adapter does not inspect the bytes. ``json.loads`` on ``bytes`` detects
    ``utf-8-sig`` and would strip the BOM, so a patch-module parse would accept
    this body; the live ``400`` is
    ``test_products_api.py::test_post_utf8_bom_json_body_is_rejected_as_400``.
    """
    raw = b"\xef\xbb\xbf" + b'{"a": 1}'
    adapter = DjangoHTTPRequestAdapter(_FakeRequest(raw))
    assert adapter.body == raw
    assert isinstance(adapter.body, bytes)


def test_body_returns_raw_bytes_for_utf16_le_without_bom():
    """BOM-less UTF-16-LE stays bytes here; upstream's getter still decodes to ``str``.

    ``encode("utf-16-le")`` is NUL-padded ASCII, hence UTF-8-decodable, so
    upstream's ``.decode()`` still succeeds into a ``str``. That is why this
    patch returns raw bytes rather than wrapping the decode: a try/except
    around ``.decode()`` would still hand ``parse_json`` a ``str``. The live
    ``400`` is
    ``test_products_api.py::test_post_utf16_le_json_body_is_rejected_as_400``.
    """
    raw = '{"query":"{ __typename }"}'.encode("utf-16-le")
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


@pytest.mark.parametrize(
    "adapter",
    [
        pytest.param(None, id="missing-adapter"),
        pytest.param(_MalformedAdapter, id="non-property-body"),
    ],
)
def test_capture_returns_none_for_missing_adapter_or_body_property(adapter):
    """Neither a missing adapter nor a non-property ``body`` may capture as a usable getter.

    The capture runs at module scope, before ``apply()`` can complain, so both
    absent-shape cases have to resolve to the ``None`` sentinel rather than
    raising: an unimportable patch module takes the package's app config down
    with it on precisely the installs whose shape ``apply()`` is meant to refuse
    by name. The second case is the one that cannot be inferred from the first -
    a ``body`` that is present but is not a readable ``property`` is not
    something this patch can supersede, and capturing it would let ``apply()``
    install over an unrecognized descriptor.
    """
    with mock.patch.object(patches, "DjangoHTTPRequestAdapter", adapter):
        assert patches._captured_upstream_body_getter() is None


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

    The production half of the per-dependency opt-out contract: opting out of
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
