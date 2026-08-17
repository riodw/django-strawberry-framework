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
companion Strawberry patch jointly own the malformed-body hardening a
consumer gets on **Strawberry's own** sync view, so disabling either
leaves that incomplete: without this half the sync adapter decodes inside
a property again and an undecodable body is an unhandled ``500``; without
the Strawberry half a scalar or non-object-batch body is an unhandled
``500``.

The gate covers upstream *defects* only, and a **package** view does not
consult it. The strict UTF-8 wire contract (spec-046 Decision 9) is
package policy, and the package view owns both halves of it: the decode,
in ``views.py::_RequestBodyBoundaryMixin.parse_json``, and its own sync
body source, in ``views.py::_RawBodyRequestAdapter`` - a one-property
subclass of the adapter this module patches, so a package mount reaches
that decode with undecoded bytes whatever this setting says. That second
half is not redundant with this patch; it is what made the claim true. With
this half opted out and only the decode view-owned, upstream's property
decoded first and the mounted sync view answered ``500`` instead of the
contract's ``400``. See
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
``self.request.body`` unchanged - so upstream's two transports hand the
same bytes to the same ``parse_json``, where
:mod:`django_strawberry_framework._strawberry_patches` translates the
``UnicodeDecodeError`` that ``json.loads`` raises for the undecodable
ones. The raise then lands in a scope that can answer with a response,
which a property is not.

Who this patch is for
---------------------

Consumers who mount **Strawberry's own** view. It is no longer on the
package's own request path at all: a package view installs its own
raw-body adapter (``views.py::_RawBodyRequestAdapter``, a one-property
subclass of the class patched here) and decodes strictly in its own
``parse_json``, so it behaves identically with this patch installed or
not. What the patch decides is what the *other* mount gets:

- installed - the raw bytes reach ``json.loads``, so gap (1)'s
  undecodable bodies become a controlled ``400`` (through the Strawberry
  patch's ``UnicodeDecodeError`` translation when the detected-encoding
  decode raises, or through upstream's own ``json.JSONDecodeError``
  handling when ``surrogatepass`` lets the decode succeed into non-JSON),
  and every other shape keeps upstream's own RFC 8259
  auto-detection (its documented behavior, which the package deliberately
  does not narrow on someone else's view);
- not installed - an undecodable body raises inside the property and is
  the unhandled ``500`` that is the upstream defect.

Gap (2) survives as the reason the correct fix is "hand over the raw
bytes" rather than "decode defensively inside the property": a property
cannot own an error contract. Sync/async parity is still the property
this patch buys for that mount - without it upstream's two transports
disagree about which bodies are even parseable, and the asymmetry, not
either answer, is the defect.

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

1. End-to-end, and only on a mount of **Strawberry's own** view. A row
   that posts to a *package* mount cannot diagnose this module at all:
   the package view supplies its own body source
   (``views.py::_RawBodyRequestAdapter``) and its own strict decode, so
   every shape below answers the same ``400`` there in every state of
   this setting. Fakeshop keeps the mount that does discriminate
   (``/upstream-graphql/``) and the standing row that reads it,
   ``test_transport_api.py::test_the_cross_web_half_turns_upstreams_own_500_into_a_400``::

       uv run pytest examples/fakeshop/test_query/test_transport_api.py \
           -k cross_web_half

   That row posts an undecodable body to that mount in both states: with
   this module's half un-installed upstream's property decode raises
   before ``parse_json`` is entered and the answer is the unhandled
   ``500`` that IS the upstream defect; with it installed the same bytes
   reach ``json.loads`` inside ``parse_json`` and become a controlled
   ``400``. A ``500`` therefore means the patch is still needed, and a
   ``400`` in the *un-installed* state is what says upstream stopped
   decoding eagerly and this module can be deleted.

   Two readings of that row invert the verdict, so both are pinned by the
   row rather than left to the reader. First, **setting the switch is not
   a simulation**: every patch installs from ``AppConfig.ready()``, long
   before any test runs, so a run that only overrides
   ``DJANGO_STRAWBERRY_FRAMEWORK`` still executes with this module
   installed and reports the installed answer - which is why the row
   restores upstream's property by identity and asserts
   ``_patch_is_installed()`` in both directions inside the block. Second,
   **only a body that upstream's property decode rejects AND the
   raw-bytes JSON path does not accept discriminates** - i.e. only a
   body whose un-installed answer is the ``500``. A BOM'd UTF-16 /
   UTF-32 body fails the first half: auto-detected and *accepted*
   (``200``) on that mount once this patch hands over the raw bytes. A
   BOM-less UTF-16 / UTF-32 body or a UTF-8-BOM body fails the first
   half too, and its un-installed answer is the trap: upstream's
   property decode *succeeds* (NUL-padded ASCII and a UTF-8 BOM are
   valid UTF-8) into a ``str`` that ``json.loads`` refuses, so it
   measures ``400`` un-installed and ``200`` installed - an un-installed
   ``400`` that reads as "retirable" while upstream is still decoding
   eagerly. And the criterion is deliberately not "a body ``json.loads``
   cannot decode": ``json.loads`` decodes ``bytes`` with
   ``errors="surrogatepass"``, so even arbitrary binary usually decodes
   under the detected encoding and is then refused as JSON by upstream's
   own ``except`` - the installed ``400`` has two mechanisms (the
   Strawberry patch's ``UnicodeDecodeError`` translation, and upstream's
   own ``json.JSONDecodeError`` handling), and the row's two parameters
   cover one each.

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


_PATCH_OWNER_ATTRIBUTE = "_django_strawberry_framework_patch_owner"
_PATCH_ORIGINAL_ATTRIBUTE = "_django_strawberry_framework_original"
_PATCH_OWNER = "django_strawberry_framework._cross_web_patches"


def _captured_upstream_body_getter() -> Any:
    """Return cross_web's getter, retaining it across an in-process reload.

    ``importlib.reload()`` leaves the old property installed while this module
    re-executes. Its replacement retains the genuine getter, so recover that
    value for validation rather than accepting the old package getter as
    cross_web's current upstream shape.
    """
    if DjangoHTTPRequestAdapter is None:
        return None
    descriptor = DjangoHTTPRequestAdapter.__dict__.get("body")
    if not isinstance(descriptor, property) or descriptor.fget is None:
        return None
    if getattr(descriptor.fget, _PATCH_OWNER_ATTRIBUTE, None) == _PATCH_OWNER:
        return getattr(descriptor.fget, _PATCH_ORIGINAL_ATTRIBUTE, None)
    return descriptor.fget


# Capture the genuine upstream ``body`` getter once, at import time, before
# ``apply()`` can replace it. The capture also survives an in-process reload,
# so retirement probes and shape validation never inspect the previous package
# getter. Stays ``None`` (the same missing-shape sentinel the sibling patch
# modules use) when the adapter symbol or readable property is absent, so
# ``apply()`` refuses to install over an unexpected shape.
_original_body_fget = _captured_upstream_body_getter()


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

    The return contract is unchanged by spec-046: raw bytes, never a
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

    **What raw bytes mean, and on whose view.** They mean "let
    ``json.loads`` auto-detect the encoding per RFC 8259" - upstream's
    documented behavior, which this patch preserves rather than narrows.
    That is deliberate: the mount this getter serves is Strawberry's own
    view, and a consumer who chose it is entitled to its semantics. A
    **package** view never reaches this getter, because it installs
    ``views.py::_RawBodyRequestAdapter`` instead, and strict-UTF-8-decodes
    in its own ``parse_json`` (spec-046 Decision 9) - so UTF-16 / UTF-32
    (BOM or BOM-less) and a leading UTF-8 BOM are ``400``s there on both
    transports, in every state of this patch's own setting. Keeping the
    wire contract out of this getter is what makes those two answers
    independent, which is exactly the point of the split.

    **Why the patch survives the protocol split, and matters more.**
    It patches ``cross_web.DjangoHTTPRequestAdapter``, the **Django
    view's** sync request adapter - precisely the path the split made
    authoritative - not anything Channels-owned. Before the split a
    Channels-routed deployment never reached that adapter at all, so if
    anything the split raises this patch's importance.
    """
    return self.request.body


setattr(_patched_body, _PATCH_OWNER_ATTRIBUTE, _PATCH_OWNER)
setattr(_patched_body, _PATCH_ORIGINAL_ATTRIBUTE, _original_body_fget)


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
