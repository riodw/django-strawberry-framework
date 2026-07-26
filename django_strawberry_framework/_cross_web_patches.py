"""Defensive patches for upstream ``cross_web`` bugs, applied at app load.

Companion to :mod:`django_strawberry_framework._strawberry_patches`.
The package ships one patch module per third-party dependency it has to
patch; this is the ``cross_web`` one (``cross_web`` is the HTTP
request/response abstraction Strawberry's Django view is built on).

The patch is applied once from
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`,
so consumers get it automatically by having
``"django_strawberry_framework"`` in ``INSTALLED_APPS``. It touches
**production** request handling, so it is gated by the
``APPLY_UPSTREAM_PATCHES`` setting (default on): opt out globally with
``False`` or for this dependency alone with the mapping shape
``{"APPLY_UPSTREAM_PATCHES": {"cross_web": False}}``. This patch and the
companion Strawberry patch jointly own the sync transport's
malformed-body hardening **and** the strict UTF-8 wire contract
(spec-065 Decision 9, enforced in
:func:`django_strawberry_framework._strawberry_patches._patched_parse_json`),
so disabling only one of the pair leaves both incomplete: without this
half the sync adapter decodes inside a property again and an undecodable
body is an unhandled ``500``; without the Strawberry half the wire
contract is gone and UTF-16 / UTF-32 bodies silently succeed. The gate
is deliberately shared rather than split per concern. See
:func:`django_strawberry_framework.conf.upstream_patches_enabled`.

The bug
-------

:attr:`cross_web.DjangoHTTPRequestAdapter.body` (the **sync** adapter)
returns ``self.request.body.decode()`` - a bare UTF-8 decode with no
error handling. That has two production consequences before Strawberry's
``parse_json`` can own the body:

1. A body that is not valid UTF-8 raises ``UnicodeDecodeError`` from
   inside the property, so Strawberry's ``400`` handling never runs and
   the request surfaces as an unhandled ``500``.
2. A body that *is* UTF-8-decodable but is not UTF-8 JSON - notably
   BOM-less UTF-16-LE/BE and UTF-32-LE/BE (ASCII code units padded with
   NUL bytes, which are valid UTF-8) and a UTF-8 BOM payload - returns a
   ``str`` that ``json.loads`` rejects, while the **async** adapter
   (``AsyncDjangoHTTPRequestAdapter.get_body``) hands Strawberry the raw
   ``bytes`` untouched. Upstream's two transports therefore disagree
   about which bodies are even parseable - the asymmetry, not either
   answer, is the defect.

The decode is therefore both unsafe and misplaced. This patch replaces
the sync ``body`` property with the async contract - always return
``self.request.body`` unchanged - so both transports hand the same bytes
to the same ``parse_json``, which is where
:mod:`django_strawberry_framework._strawberry_patches` decodes them
once with strict UTF-8 and translates any failure into a clean
``HTTPException(400, ...)``.

Under that wire contract (spec-065 Decision 9) only gap (1) still
changes the *response*: an eagerly-decoding adapter and a strict decode
in ``parse_json`` agree on every decodable-but-not-JSON shape - BOM-less
UTF-16/32 and a UTF-8 BOM are a ``400`` either way. Gap (2) survives as
the reason the correct fix is "hand over the raw bytes" rather than
"decode defensively inside the property": a property cannot own an error
contract. Sync/async parity is still the property this patch buys, but
it is now parity of *rejection* rather than of success.

Upstream's getter is still captured at import time so retirement probes
and shape validation can see the bare ``.decode()``, but the installed
property does not call it - calling it would put the decode back inside
the property and re-introduce gap (1)'s unhandled ``500``.

Upstream status
---------------

Unfixed upstream as of ``cross-web`` 0.7.0, which is both the latest
release and ``main`` (checked 2026-06-18). The sync
``DjangoHTTPRequestAdapter.body`` still does a bare ``.decode()``:
<https://github.com/usecross/cross-web/blob/813299cecdc9c2155f99a6fcda074a00eed9b1ed/src/cross_web/request/_django.py>.

No upstream issue or PR tracks it (the repo is ``usecross/cross-web``;
``strawberry-graphql`` only depends on it). This patch can be retired
once upstream stops eagerly decoding the sync body - the minimal fix
mirrors the async adapter in the same file, which already returns the
raw bytes. A future upstream shape change fails loudly at application so the
patch can be re-audited or retired deliberately.

Re-checking whether upstream fixed this
---------------------------------------

The same two checks as
:mod:`django_strawberry_framework._strawberry_patches`:

1. End-to-end (definitive). Set ``DJANGO_STRAWBERRY_FRAMEWORK =
   {"APPLY_UPSTREAM_PATCHES": {"cross_web": False}}`` - this module off,
   the Strawberry patch left **on** - and run the *undecodable*-body
   rows, which are the only ones that discriminate::

       uv run pytest examples/fakeshop/test_query/test_products_api.py \
           -k "invalid_utf8 or raw_binary or utf16_json"

   Those three bodies cannot be UTF-8-decoded at all, so with this module
   off upstream's property decode raises before ``parse_json`` is
   entered: the rows fail (an unhandled ``500`` that
   ``django.test.Client`` re-raises) and the patch is still needed. If
   they answer their ``400``, upstream stopped decoding eagerly and this
   module can be deleted.

   The ``utf16_le`` and ``bom`` rows deliberately do **not** appear in
   that selector any more. Under the wire contract they answer ``400``
   whether or not this patch is installed - upstream's decode succeeds
   into a ``str`` that ``json.loads`` refuses, our decode succeeds into
   the same ``str`` that ``json.loads`` refuses - so they diagnose
   nothing about upstream. Selecting them and reading a ``400`` as
   "still needed" inverts the verdict.

2. Quick probe of the *installed* version, via the captured upstream
   getter::

       from django_strawberry_framework import _cross_web_patches as c
       from cross_web import DjangoHTTPRequestAdapter

       class _Req:
           body = bytes([0xff, 0xfe, 0xfa])  # not valid UTF-8

       try:
           c._original_body_fget(DjangoHTTPRequestAdapter(_Req()))
       except UnicodeDecodeError:
           print("STILL NEEDED")  # sync adapter still bare-decodes
       else:
           print("RETIRABLE")  # adapter no longer raises on non-UTF-8

   To check a newer release without upgrading, re-read the sync
   ``DjangoHTTPRequestAdapter.body`` at the permalink above. The latest
   published version is at ``https://pypi.org/pypi/cross-web/json``
   (``info.version``); cross-web 0.7.0 is currently both the latest
   release and ``main``, so watch for any release later than 0.7.0.

Surface visibility
------------------

The patch module is intentionally private (leading underscore). The
:func:`apply` entry point is exported (no leading underscore) so the
package's regression tests can call it explicitly without going through
the AppConfig.
"""

import inspect
from typing import Any

from .conf import upstream_patches_enabled

try:
    from cross_web import DjangoHTTPRequestAdapter
except ImportError:  # pragma: no cover - exercised via monkeypatch in tests
    # Preserve module import long enough for ``apply()`` to report the precise
    # unsupported upstream shape and the explicit opt-out.
    DjangoHTTPRequestAdapter = None  # type: ignore[assignment,misc]


# Capture the genuine upstream ``body`` getter once, at import time,
# before ``apply()`` can replace it. Retirement probes and shape
# validation still need the bare ``.decode()`` getter; the installed
# property does not call it (see :func:`_patched_body`). Stays ``None``
# (the same missing-shape sentinel the sibling patch modules use) when the
# adapter symbol or the readable ``body`` property is absent at import, so
# ``apply()`` refuses to install over an unexpected shape.
_original_body_fget = None
if DjangoHTTPRequestAdapter is not None:
    _descriptor = DjangoHTTPRequestAdapter.__dict__.get("body")
    if isinstance(_descriptor, property) and _descriptor.fget is not None:
        _original_body_fget = _descriptor.fget


def _validate_upstream_shape() -> None:
    """Fail loudly when cross_web no longer exposes the property shape we replace.

    Pins the import-time-captured upstream getter (presence and ``(self)``
    signature) so a missing or reshaped ``body`` property fails at
    ``apply()`` instead of silently leaving the sync transport on the
    bare ``.decode()``. The live descriptor is only read by
    :func:`_patch_is_installed`; :func:`_patched_body` reads
    ``self.request.body`` directly (the async contract) and does not
    call the captured getter.
    """
    if DjangoHTTPRequestAdapter is None:
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's cross_web patch: expected "
            "cross_web.DjangoHTTPRequestAdapter. Disable this patch with "
            'APPLY_UPSTREAM_PATCHES = {"cross_web": False} or use a '
            "supported cross_web version.",
        )
    if _original_body_fget is None:
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's cross_web patch: "
            "DjangoHTTPRequestAdapter.body is no longer a readable property. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"cross_web": False} '
            "or use a supported cross_web version.",
        )
    parameters = tuple(inspect.signature(_original_body_fget).parameters.values())
    if len(parameters) != 1 or parameters[0].kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD:
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's cross_web patch: "
            "DjangoHTTPRequestAdapter.body no longer has the expected (self) getter signature. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"cross_web": False} '
            "or use a supported cross_web version.",
        )


def _patched_body(self: Any) -> bytes:
    """Return raw ``self.request.body`` bytes - the async adapter's contract.

    The return contract is unchanged by spec-065: raw bytes, never a
    decoded ``str``. What changed is what happens to them next, so the
    reason for the raw bytes is worth stating exactly.

    **Why raw bytes.** Upstream's sync getter UTF-8-decodes inside a
    *property*. A ``UnicodeDecodeError`` raised there escapes
    ``BaseView.parse_json``'s ``except`` entirely and surfaces as an
    unhandled ``500`` - the original upstream bug. Handing the bytes over
    untouched moves that raise into the one scope that can translate it
    into a controlled ``400``, and matches
    ``AsyncDjangoHTTPRequestAdapter.get_body`` so both transports feed
    ``parse_json`` the same thing. This getter therefore deliberately
    performs no decode and no validation of its own; adding either here
    would re-create the property-scope raise.

    **What raw bytes no longer mean.** They no longer mean "let
    ``json.loads`` auto-detect the encoding per RFC 8259".
    :func:`django_strawberry_framework._strawberry_patches._patched_parse_json`
    now strict-UTF-8-decodes them before delegating (spec-065 Decision
    9), so UTF-16 / UTF-32 (BOM or BOM-less) and a leading UTF-8 BOM are
    ``400``s on both transports rather than successes. Sync/async parity
    is preserved and is still this patch's point - it is now parity of
    *rejection* rather than of success.

    **Why the patch survives the S1 protocol split, and matters more.**
    It patches ``cross_web.DjangoHTTPRequestAdapter``, the **Django
    view's** sync request adapter - precisely the path S1 made
    authoritative - not anything Channels-owned. Before S1 a
    Channels-routed deployment never reached that adapter at all, so if
    anything the split raises this patch's importance.
    """
    return self.request.body


def _patch_is_installed() -> bool:
    """Return ``True`` iff ``DjangoHTTPRequestAdapter.body`` points at our patched getter."""
    if DjangoHTTPRequestAdapter is None:
        return False
    descriptor = DjangoHTTPRequestAdapter.__dict__.get("body")
    return isinstance(descriptor, property) and descriptor.fget is _patched_body


def apply() -> None:
    """Apply the ``cross_web`` defensive patch shipped by the package.

    Idempotent and self-healing, gated by ``APPLY_UPSTREAM_PATCHES``
    (globally via ``False``, or for this dependency alone via
    ``{"cross_web": False}``). Before installation it validates the adapter
    symbol and the captured upstream getter's presence and ``(self)``
    signature (so a reshaped ``body`` property fails loud); dependency
    drift raises instead of silently disabling the request hardening.
    """
    if not upstream_patches_enabled("cross_web"):
        return
    _validate_upstream_shape()
    if _patch_is_installed():
        return
    DjangoHTTPRequestAdapter.body = property(_patched_body)
