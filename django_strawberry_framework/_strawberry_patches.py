"""Defensive patches for upstream Strawberry bugs, applied at app load.

Companion to :mod:`django_strawberry_framework._django_patches`. Where
that module hardens a Django test-runner bug, this module hardens a
Strawberry HTTP-view bug that affects live request handling for every
consumer of ``django-strawberry-framework``. The package ships one
patch module per third-party dependency it has to patch; this is the
Strawberry one.

The patch is applied once from
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`,
so consumers get it automatically by having
``"django_strawberry_framework"`` in ``INSTALLED_APPS`` - no opt-in
boilerplate is required. This patch touches **production** request
handling; like every patch the package ships it is gated by the
``APPLY_UPSTREAM_PATCHES`` setting (default on), so a consumer can opt
out with ``DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES":
False}``. See
:func:`django_strawberry_framework.conf.upstream_patches_enabled`.

The bug
-------

A request body that is not valid UTF-8 (raw binary, an invalid-UTF-8
JSON payload, etc.) makes Strawberry's view raise ``UnicodeDecodeError``
instead of returning a controlled ``400``. Strawberry clearly intends a
``400`` here - :meth:`strawberry.http.base.BaseView.parse_json` already
turns malformed JSON into ``HTTPException(400, ...)`` - but it catches
only ``json.JSONDecodeError``. ``UnicodeDecodeError`` is a ``ValueError``
and is **not** a ``JSONDecodeError``, so it escapes the ``except`` and
surfaces as an unhandled ``500``:

- On the **sync** view the decode happens in ``cross_web``'s request
  adapter, before ``parse_json`` is even entered (handled by the
  companion :mod:`django_strawberry_framework._cross_web_patches`,
  which makes the adapter hand the raw bytes to ``parse_json`` instead
  of decoding eagerly).
- On the **async** view the raw bytes reach ``json.loads`` directly,
  which raises ``UnicodeDecodeError`` from *inside* ``parse_json``.

``BaseView.parse_json`` is the single method both the sync and async
views inherit, so widening its ``except`` to also catch
``UnicodeDecodeError`` fixes both transports from one site. Combined
with the ``cross_web`` patch (which routes the sync path's bytes through
``parse_json`` rather than decoding them eagerly), every malformed-body
request becomes a clean ``400``.

The patch wraps the original ``parse_json`` rather than reimplementing
it: the original is called unchanged and only the previously-uncaught
``UnicodeDecodeError`` is translated to the same ``HTTPException(400,
...)`` Strawberry already raises for malformed JSON. This keeps the
patch robust to upstream changes in the body of ``parse_json``.

A second gap: non-object JSON bodies
------------------------------------

The same wrapper also closes a sibling gap. ``parse_http_body`` handles
a request body that decodes to a JSON object (a single operation) and to
a JSON array (a batch, via ``_validate_batch_request``), but a body that
is a valid JSON *scalar* - ``"a string"``, ``42``, ``true``, ``null`` -
falls through both branches to ``data.get("query")`` and raises a raw
``AttributeError`` (``'str' object has no attribute 'get'``) -> an
unhandled ``500``. A JSON scalar is never a valid GraphQL-over-HTTP
request body, so the wrapper rejects a parsed result that is neither a
``dict`` nor a ``list`` with the same ``HTTPException(400, ...)``. The
``list`` case is passed through so upstream's own batch validation keeps
ownership of it. ``parse_json`` is the *only* producer of a
scalar ``data`` that reaches ``parse_http_body`` (the GET
``parse_query_params`` and ``parse_multipart`` paths always return a
``dict``), so the one-site fix covers the sync and async views together,
exactly as the ``UnicodeDecodeError`` widening does.

Upstream status
---------------

Unfixed upstream as of ``strawberry-graphql`` 0.317.2 (the latest
release) and ``main`` (checked 2026-06-18). ``BaseView.parse_json``
still catches only ``json.JSONDecodeError``:
<https://github.com/strawberry-graphql/strawberry/blob/e7d4a8235a11a4c4fd2b9fa605c437c9f86e5fb7/strawberry/http/base.py#L45-L52>.

No upstream issue or PR tracks this exact ``UnicodeDecodeError`` gap.
The closest ticket, #1214 (closed), covers graceful handling of
malformed-but-valid-UTF-8 JSON - i.e. the ``JSONDecodeError`` case that
is *already* caught - not the non-UTF-8 subclass case this patch fixes:
<https://github.com/strawberry-graphql/strawberry/issues/1214>. This
patch can be retired once upstream broadens the catch to also cover
``UnicodeDecodeError`` (or ``ValueError``); a future upstream shape change
fails loudly so that retirement is deliberate.

The second gap (non-object body) is likewise unfixed in 0.317.2 and
``main`` (checked 2026-06-19). ``parse_http_body`` still handles only the
``list`` (batch) branch and then calls ``data.get("query")`` with no
``isinstance(data, dict)`` guard:
<https://github.com/strawberry-graphql/strawberry/blob/e7d4a8235a11a4c4fd2b9fa605c437c9f86e5fb7/strawberry/http/sync_base_view.py>
(and the ``async_base_view.py`` sibling). It is tracked by the **open**
issue #3398, "AttributeError when query passed is a list and not a dict"
(opened 2024-02-27 against 0.219.2, no merged PR):
<https://github.com/strawberry-graphql/strawberry/issues/3398>. The
issue's title says *list* because at 0.219.2 a top-level list was
unguarded too; current versions intercept lists in the batch branch, so
the still-unhandled trigger is the JSON *scalar* case - the same
``data.get()``-on-a-non-dict root cause, narrowed to scalars. Retire the
scalar guard once #3398 lands an ``isinstance(data, dict)`` check (or
equivalent) ahead of ``data.get("query")``.

Re-checking whether upstream fixed this
---------------------------------------

You do not need to redo the research from scratch. Two ways to tell
whether this patch is still required:

1. End-to-end (definitive). Disable the patches and run the live
   regression: set ``DJANGO_STRAWBERRY_FRAMEWORK =
   {"APPLY_UPSTREAM_PATCHES": False}`` and run the fakeshop tests for
   both gaps - ``test_post_invalid_utf8_json_body_returns_400_not_500``
   and ``test_post_raw_binary_body_returns_400_not_500`` (UnicodeDecodeError)
   plus ``test_post_non_object_json_body_returns_400_not_500`` (scalar
   body)::

       uv run pytest examples/fakeshop/test_query/test_products_api.py \
           -k "utf8 or binary or non_object"

   If they still return 400 with the patch off, upstream has fixed that
   gap; if they 500, the patch is still needed. Both gaps must be fixed
   upstream before this module can be deleted.

2. Quick probe of the *installed* version. This module captures the
   unwrapped upstream callable, so you can exercise each gap directly::

       from django_strawberry_framework import _strawberry_patches as p
       from strawberry.http.base import BaseView

       # Gap 1 (UnicodeDecodeError): b'{' + an invalid UTF-8 byte
       try:
           p._original_parse_json(BaseView(), bytes([0x7b, 0x80]))
       except UnicodeDecodeError:
           print("GAP 1 STILL NEEDED")  # upstream catch is still too narrow
       except Exception as exc:  # noqa: BLE001
           print("GAP 1 RETIRABLE:", type(exc).__name__)  # e.g. HTTPException

       # Gap 2 (non-object body) lives in ``parse_http_body``, not
       # ``parse_json`` (which just returns the scalar), so probe end-to-end
       # via the live test above, or read the ``data.get("query")`` site in
       # sync_base_view.py / async_base_view.py and confirm a non-dict guard
       # now precedes it.

   To check a newer release without upgrading, re-read ``parse_json`` /
   ``decode_json`` at the permalink above (gap 1) and ``parse_http_body``
   (gap 2) on the current ``main``. The latest published version is at
   ``https://pypi.org/pypi/strawberry-graphql/json`` (``info.version``).

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
    from cross_web import HTTPException
    from strawberry.http.base import BaseView
except ImportError:  # pragma: no cover - exercised via monkeypatch in tests
    # Preserve module import long enough for ``apply()`` to report the precise
    # unsupported upstream shape and the explicit opt-out.
    BaseView = None  # type: ignore[assignment,misc]
    HTTPException = None  # type: ignore[assignment,misc]


# Capture the genuine upstream ``parse_json`` once, at import time, before
# ``apply()`` can install our wrapper. The wrapper delegates to this so a
# self-healing re-install never wraps a wrapper.
_original_parse_json = None if BaseView is None else BaseView.__dict__.get("parse_json")


def _validate_upstream_shape() -> None:
    """Fail loudly when Strawberry no longer exposes the method shape we wrap."""
    if BaseView is None or HTTPException is None or not callable(_original_parse_json):
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Strawberry patch: expected "
            "strawberry.http.base.BaseView.parse_json and cross_web.HTTPException. "
            "Disable APPLY_UPSTREAM_PATCHES or use supported dependency versions.",
        )
    parameters = tuple(inspect.signature(_original_parse_json).parameters.values())
    if len(parameters) != 2 or any(
        parameter.kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters
    ):
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Strawberry patch: "
            "BaseView.parse_json no longer has the expected (self, data) signature. "
            "Disable APPLY_UPSTREAM_PATCHES or use a supported Strawberry version.",
        )


def _patched_parse_json(self: Any, data: "str | bytes") -> Any:
    """Wrapper around ``BaseView.parse_json`` hardening two upstream gaps.

    1. A ``UnicodeDecodeError`` (a ``ValueError`` that upstream's
       ``except json.JSONDecodeError`` does not catch) is translated to
       the same ``HTTPException(400, ...)`` Strawberry already raises for
       unparseable JSON.
    2. A successfully-parsed body that is a top-level JSON *scalar*
       (string / number / boolean / ``null``) is rejected with
       ``HTTPException(400, ...)``. ``parse_http_body`` handles a JSON
       object (a single operation) and a JSON array (a batch), but a bare
       scalar falls through to ``data.get("query")`` and raises a raw
       ``AttributeError`` -> ``500``. A JSON ``list`` is passed through
       untouched so upstream's own batch validation
       (``_validate_batch_request``) still runs and owns that path.

    ``parse_json`` is the sole producer of a non-object/non-array ``data``
    reaching ``parse_http_body`` (GET ``parse_query_params`` and
    ``parse_multipart`` always return a ``dict``), so guarding it here
    fixes the body path for both the sync and async views from the single
    method they both inherit - the same one-site rationale as the
    ``UnicodeDecodeError`` widening. Every other outcome - a successful
    object/array parse, or any other exception - is passed through
    untouched.
    """
    try:
        parsed = _original_parse_json(self, data)
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "Unable to parse request body as JSON") from exc
    if not isinstance(parsed, (dict, list)):
        raise HTTPException(
            400,
            "The GraphQL request body must be a JSON object "
            "(or an array of operations for a batch request).",
        )
    return parsed


def _patch_is_installed() -> bool:
    """Return ``True`` iff ``BaseView.parse_json`` currently points at our wrapper."""
    return BaseView is not None and BaseView.__dict__.get("parse_json") is _patched_parse_json


def apply() -> None:
    """Apply the Strawberry defensive patch shipped by the package.

    Idempotent and self-healing: re-entrant calls are no-ops when the
    patch is still installed, and re-install the patch if a third party
    reverted ``BaseView.parse_json`` since the prior call. Called from
    :meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`
    at Django startup.

    No-ops in two cases:

    - The ``APPLY_UPSTREAM_PATCHES`` setting is ``False`` (consumer
      opted out). Returns before logging or touching anything.
    - The patch is already installed (re-entrant call).

    Before installation, validates the imported symbols and the original
    ``(self, data)`` signature. Dependency drift raises a targeted
    ``RuntimeError`` instead of silently dropping the request hardening.
    """
    if not upstream_patches_enabled():
        return
    _validate_upstream_shape()
    if _patch_is_installed():
        return
    BaseView.parse_json = _patched_parse_json
