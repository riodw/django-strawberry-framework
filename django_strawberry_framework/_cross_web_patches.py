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
``APPLY_UPSTREAM_PATCHES`` setting (default on); see
:func:`django_strawberry_framework.conf.upstream_patches_enabled`.

The bug
-------

:attr:`cross_web.DjangoHTTPRequestAdapter.body` (the **sync** adapter)
returns ``self.request.body.decode()`` - a bare UTF-8 decode with no
error handling. A request body that is not valid UTF-8 therefore raises
``UnicodeDecodeError`` from inside the property, *before* Strawberry's
``parse_json`` is entered, so Strawberry's ``400`` handling never gets a
chance and the request surfaces as an unhandled ``500``.

The decode is also gratuitous: ``json.loads`` accepts ``bytes``
directly, and the **async** adapter (``AsyncDjangoHTTPRequestAdapter``)
already hands Strawberry the raw bytes without decoding. This patch
brings the sync adapter in line with that contract: when the body
decodes cleanly it is returned unchanged (byte-for-byte identical to
upstream), and only the previously-``500``-ing case changes - the raw
bytes are handed back instead, so ``parse_json`` raises
``UnicodeDecodeError`` from ``json.loads``, which the companion
:mod:`django_strawberry_framework._strawberry_patches` patch turns into
a clean ``HTTPException(400, ...)``.

The patch wraps the original property getter rather than
reimplementing it, so the success path stays exactly upstream's and
only the failure path gains the bytes fallback.

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
raw bytes. The graceful no-op in :func:`apply` means a future fixed
``cross-web`` needs no action here.

Re-checking whether upstream fixed this
---------------------------------------

The same two checks as
:mod:`django_strawberry_framework._strawberry_patches`:

1. End-to-end (definitive). Set ``DJANGO_STRAWBERRY_FRAMEWORK =
   {"APPLY_UPSTREAM_PATCHES": False}`` and run the fakeshop tests
   ``test_post_invalid_utf8_json_body_returns_400_not_500`` and
   ``test_post_raw_binary_body_returns_400_not_500``::

       uv run pytest examples/fakeshop/test_query/test_products_api.py -k "utf8 or binary"

   Passing with the patch off means upstream is fixed and this module
   can be deleted; a 500 means the patch is still needed.

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

from typing import Any

from . import logger
from .conf import upstream_patches_enabled

try:
    from cross_web import DjangoHTTPRequestAdapter
except ImportError:  # pragma: no cover - exercised via monkeypatch in tests
    # cross_web renamed, relocated, or removed the sync Django adapter.
    # The patch only makes sense when it exists, so ``apply()`` no-ops
    # instead of crashing the app loader. See ``apply()`` for the
    # runtime branch and ``test_apply_no_ops_when_symbol_missing``.
    DjangoHTTPRequestAdapter = None  # type: ignore[assignment,misc]


def _original_body_fget(
    adapter: Any,
) -> Any:  # pragma: no cover - replaced below when symbol present
    """Placeholder; rebound to the upstream ``body`` getter at import time."""
    raise NotImplementedError


# Capture the genuine upstream ``body`` getter once, at import time,
# before ``apply()`` can install our wrapper. The wrapper delegates to
# this so a self-healing re-install never wraps a wrapper.
if DjangoHTTPRequestAdapter is not None:
    _descriptor = DjangoHTTPRequestAdapter.__dict__.get("body")
    if isinstance(_descriptor, property) and _descriptor.fget is not None:
        _original_body_fget = _descriptor.fget


# Module-level sentinel: see the matching note in
# :mod:`django_strawberry_framework._strawberry_patches`.
_missing_symbol_logged = False


def _patched_body(self: Any) -> "str | bytes":
    """Wrapper around ``DjangoHTTPRequestAdapter.body`` with a bytes fallback.

    Delegates to the upstream getter; when it raises
    ``UnicodeDecodeError`` (the body is not valid UTF-8) the raw
    ``self.request.body`` bytes are returned instead. ``json.loads``
    accepts bytes, so Strawberry's ``parse_json`` handles them and
    raises a controlled ``400`` (via the Strawberry patch) rather than
    letting the decode crash escape as a ``500``.
    """
    try:
        return _original_body_fget(self)
    except UnicodeDecodeError:
        return self.request.body


def _patch_is_installed() -> bool:
    """Return ``True`` iff ``DjangoHTTPRequestAdapter.body`` points at our wrapper."""
    if DjangoHTTPRequestAdapter is None:
        return False
    descriptor = DjangoHTTPRequestAdapter.__dict__.get("body")
    return isinstance(descriptor, property) and descriptor.fget is _patched_body


def apply() -> None:
    """Apply the ``cross_web`` defensive patch shipped by the package.

    Idempotent and self-healing, gated by ``APPLY_UPSTREAM_PATCHES``,
    and a graceful no-op when the upstream symbol moved - the same
    contract as :func:`django_strawberry_framework._strawberry_patches.apply`.
    """
    global _missing_symbol_logged
    if not upstream_patches_enabled():
        return
    if DjangoHTTPRequestAdapter is None:
        if not _missing_symbol_logged:
            logger.info(
                "django-strawberry-framework: skipping cross_web body patch - "
                "cross_web.DjangoHTTPRequestAdapter is unavailable at this cross_web "
                "version. Non-UTF-8 request bodies may surface as 500s on the sync view.",
            )
            _missing_symbol_logged = True
        return
    if _patch_is_installed():
        return
    DjangoHTTPRequestAdapter.body = property(_patched_body)
