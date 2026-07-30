"""Tests for the ``cross_web`` non-UTF-8 request-body patch.

System-under-test: :mod:`django_strawberry_framework._cross_web_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

The patch replaces the **sync** ``DjangoHTTPRequestAdapter.body`` so it
always returns the raw request bytes (the async ``get_body`` contract)
instead of UTF-8-decoding first. That return contract is unchanged by
spec-046; what changed is where the bytes go next. Handing them over raw
stops an undecodable body from raising ``UnicodeDecodeError`` inside a
*property*, where no ``except`` can translate it, and delivers them to
whichever ``parse_json`` the mounted view resolves - on a package view
``views.py::_RequestBodyBoundaryMixin.parse_json``, which decodes them once
with strict UTF-8 (spec-046 Decision 9).

The adapter's own contract is one half of a joint one, so the rows below
are written as two: the adapter hands the bytes over unexamined, and the
*rejection* of a non-UTF-8 body - BOM-less UTF-16/32 and a UTF-8 BOM
included - belongs to the package view's decode or to the ``json.loads``
it delegates to. The full per-encoding matrix (which mechanism refused
which byte shape) lives in ``tests/test_views.py`` alongside the policy
itself; this module pins the raw-bytes half plus the fact that those exact
bytes then reach a ``400`` at the endpoint that receives them.
"""

from unittest import mock

import pytest
import strawberry
from cross_web import DjangoHTTPRequestAdapter, HTTPException

from django_strawberry_framework import _cross_web_patches as patches
from django_strawberry_framework.views import DjangoGraphQLView


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> str:
        return "pong"


#: Upstream's view constructor requires a schema, and the two rows that follow the
#: adapter's bytes into the view's ``parse_json`` need a real instance. The schema
#: is never executed here - the whole point is that the body is refused first.
_SCHEMA = strawberry.Schema(query=_Query)


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
    """A non-UTF-8 body is returned as raw bytes, so the strict decode can 400 it.

    The adapter must not examine the bytes at all. Upstream's eager decode
    raises here - inside a ``property``, outside any ``except`` that could turn
    it into a response - which is the whole reason this getter exists. Handing
    the bytes over unexamined puts the raise one frame later, inside a
    ``parse_json`` that can translate it into a controlled ``400``: the package
    view's strict decode on a package mount, the patch module's widened
    ``except`` on an upstream one.
    """
    adapter = DjangoHTTPRequestAdapter(_FakeRequest(b"\xff\xfe\xfa"))
    assert adapter.body == b"\xff\xfe\xfa"


def test_body_returns_raw_bytes_for_utf8_bom():
    """UTF-8 BOM stays bytes here; the package view's parse is what rejects it.

    Two halves of one joint contract. The adapter's half is unchanged - raw
    bytes, no inspection. The rejection belongs to the view boundary, and
    spec-046 Decision 10 chose it over stripping the BOM; it costs no branch,
    because the bytes decode cleanly and upstream's own ``json.loads`` refuses the
    leading U+FEFF.

    Handing these exact bytes to the *view* rather than to
    ``_patched_parse_json`` is load-bearing rather than incidental: ``json.loads``
    on ``bytes`` detects ``utf-8-sig`` and strips the BOM itself, so the patch
    module alone would accept this body. What refuses it is the package's own
    strict decode, which is why the adapter's output has to be followed to the
    endpoint that actually receives it.
    """
    raw = b"\xef\xbb\xbf" + b'{"a": 1}'
    adapter = DjangoHTTPRequestAdapter(_FakeRequest(raw))
    assert adapter.body == raw
    assert isinstance(adapter.body, bytes)

    with pytest.raises(HTTPException) as excinfo:
        DjangoGraphQLView(schema=_SCHEMA).parse_json(adapter.body)
    assert excinfo.value.status_code == 400


def test_body_returns_raw_bytes_for_utf16_le_without_bom():
    """BOM-less UTF-16-LE stays bytes here; the package view's parse rejects it.

    ``encode("utf-16-le")`` is NUL-padded ASCII, hence UTF-8-decodable, so
    upstream's ``.decode()`` still *succeeds* - the sanity assertion below is
    the live proof that the sync adapter really does bare-decode, i.e. that
    this patch is still required. What survives of that bug is gap (1): a
    decode inside a property raises where nothing can translate it. It is no
    longer a wrong *success*, because under the wire contract the view's strict
    decode reaches the same NUL-studded ``str`` and upstream's ``json.loads``
    refuses it either way - which the second half asserts on these exact bytes.
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

    with pytest.raises(HTTPException) as excinfo:
        DjangoGraphQLView(schema=_SCHEMA).parse_json(adapter.body)
    assert excinfo.value.status_code == 400


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
