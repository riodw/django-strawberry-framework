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
``{"APPLY_UPSTREAM_PATCHES": {"cross_web": False}}`` (note this patch
and the companion Strawberry patch jointly own the sync transport's
malformed-body hardening, so disabling only one of the pair leaves it
incomplete). See
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
   (``AsyncDjangoHTTPRequestAdapter.get_body``) already hands Strawberry
   the raw ``bytes`` that ``json.loads`` accepts per RFC 8259.

The decode is therefore both unsafe and gratuitous: ``json.loads``
accepts ``bytes`` directly. This patch replaces the sync ``body``
property with the async contract - always return
``self.request.body`` unchanged. JSON-decodable UTF-16/UTF-32 (with or
without BOM) and UTF-8-with-BOM then parse and the request *succeeds*
on sync exactly as on async; anything undecodable makes ``parse_json``
raise ``UnicodeDecodeError`` from ``json.loads``, which the companion
:mod:`django_strawberry_framework._strawberry_patches` patch turns into
a clean ``HTTPException(400, ...)``.

Upstream's getter is still captured at import time so retirement probes
and shape validation can see the bare ``.decode()``, but the installed
property does not call it - calling it would re-introduce the
UTF-8-decodable-but-wrong-encoding gap (2) on the success path.

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
   {"APPLY_UPSTREAM_PATCHES": False}`` and run the fakeshop tests
   covering both gaps - undecodable bodies (``utf8`` / ``binary``) and
   UTF-8-decodable non-UTF-8 JSON (``utf16_le`` / ``bom``)::

       uv run pytest examples/fakeshop/test_query/test_products_api.py \
           -k "utf8 or binary or utf16_le or bom"

   Passing with the patch off means upstream returns raw bytes (or
   otherwise matches async) and this module can be deleted; a 500 on
   binary or a 400 on ``utf16_le`` / BOM means the patch is still needed.

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

    Upstream's sync getter UTF-8-decodes first. That both ``500``s on
    undecodable bodies and mis-handles UTF-8-decodable non-UTF-8 JSON
    (BOM-less UTF-16/32, UTF-8 BOM) by feeding ``json.loads`` a ``str``.
    Always returning the raw bytes matches
    ``AsyncDjangoHTTPRequestAdapter.get_body`` so RFC 8259 encoding
    detection runs inside ``json.loads``; undecodable bodies become a
    controlled ``400`` via the Strawberry ``parse_json`` patch.
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
