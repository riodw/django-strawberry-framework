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
out globally with ``DJANGO_STRAWBERRY_FRAMEWORK =
{"APPLY_UPSTREAM_PATCHES": False}`` or for this dependency alone with
``{"APPLY_UPSTREAM_PATCHES": {"strawberry": False}}``. Everything behind
that gate is a workaround for an upstream *defect*, and nothing behind it
is package security policy - which is the whole point of the gate's
scope. What the gate does NOT scope is the **mount**. :func:`apply`
assigns ``BaseView.parse_json``, and
``views.py::_RequestBodyBoundaryMixin.parse_json`` delegates through
``super().parse_json(data)`` to that very attribute, so a **package**
view rides this gate for the body-envelope guard exactly as Strawberry's
own view does: with the gate off, ``b"42"`` and ``b"[1,2]"`` come back
out of a real ``DjangoGraphQLView``'s ``parse_json`` as ``42`` and
``[1, 2]``, and upstream's unguarded ``data.get("query")`` turns each
into an unhandled ``500`` there too - pinned on the wire, against the
package mount, by
``examples/fakeshop/test_query/test_transport_api.py``'s
``test_the_upstream_bug_workaround_still_respects_its_own_opt_out``.
Strawberry's own view additionally depends on the companion ``cross_web``
patch to route its sync bytes into ``parse_json``, so disabling only one
of the pair leaves its malformed-body hardening incomplete, and disabling
both leaves an undecodable body an unhandled ``500`` there, exactly as it
is with the package absent.

What a **package** view keeps in every state of this setting is the
strict UTF-8 **wire contract**, and by construction rather than by luck:
it owns both halves (spec-046 Decision 9) - the decode, in
``views.py::_RequestBodyBoundaryMixin.parse_json``, and the *body source*
that delivers undecoded bytes to it, in
``views.py::_RawBodyRequestAdapter``. Owning only the decode was not
enough: with the ``cross_web`` half off, upstream's sync adapter decodes
inside its own property and the view's ``parse_json`` is never entered
with bytes at all, which cost the sync transport its controlled ``400``
(spec-046 review W3-2). See
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

- On the **sync** view *upstream* decodes in ``cross_web``'s request
  adapter, before ``parse_json`` is even entered - a raise inside a
  property, where no ``except`` can translate it. The companion
  :mod:`django_strawberry_framework._cross_web_patches` therefore makes
  that adapter hand the raw bytes to ``parse_json`` instead of decoding
  eagerly. Moving the raise, not decoding defensively, is that patch's
  entire job.
- On the **async** view the raw bytes reach ``json.loads`` directly,
  which raises ``UnicodeDecodeError`` from *inside* ``parse_json``.

``BaseView.parse_json`` is the single method both the sync and async
views inherit, so widening its ``except`` to also catch
``UnicodeDecodeError`` fixes both transports from one site. Combined
with the ``cross_web`` patch (which routes the sync path's bytes through
``parse_json`` rather than decoding them eagerly), every malformed-body
request becomes a clean ``400`` for every consumer of the installed
Strawberry - including one who mounts Strawberry's own view.

Where the strict UTF-8 wire contract lives (and why not here)
-------------------------------------------------------------

It used to live in this function. It does not any more, and the move is
the point: the wire contract (spec-046 Decision 9 - a GraphQL-over-HTTP
request body is UTF-8 or it is a ``400``) is permanent **package
policy**, while everything else in this module is a temporary workaround
for an upstream *defect*. Sharing one site meant sharing one lifecycle
and one kill switch, so ``APPLY_UPSTREAM_PATCHES = False`` - or just
``{"strawberry": False}`` - silently restored UTF-16 / UTF-32 acceptance,
and retiring the workarounds once upstream fixes them would have retired
a security contract along with them. Two owners now:

- the strict decode is enforced at the package's own HTTP-view parsing
  boundary, ``views.py::_RequestBodyBoundaryMixin.parse_json``, for both
  package views, ungated - together with the body source that feeds it,
  ``views.py::_RawBodyRequestAdapter``, because a decode the bytes never
  reach is not an enforcement;
- this module keeps translating the ``UnicodeDecodeError`` that
  upstream's ``except json.JSONDecodeError`` misses, which is a bug fix
  and stays opt-out-able.

The two compose without overlapping. On a package view the strict decode
runs first, so the delegate here only ever receives ``str`` and the
translation below is unreachable from that path; on upstream's own view
the bytes reach ``json.loads``, RFC 8259 auto-detection applies (upstream's
documented behavior, not a defect), and the translation catches the
undecodable remainder that would otherwise be a ``500``.

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
request body, so the wrapper rejects a parsed result that is not a
JSON object with the same ``HTTPException(400, ...)`` - and, for
arrays, only accepts a well-typed batch (see below).

A JSON *array* is only a valid batch envelope when every element is a
JSON object. Upstream's ``_validate_batch_request`` checks batching
config / ``max_operations`` but never element types, then does
``item.get("query")`` on each entry - so ``[1, 2, 3]``, ``[null]``, or
``[{...}, 42]`` still ``AttributeError`` -> ``500`` once batching is
enabled (with batching off the same bodies 400 as "Batching is not
enabled" *before* the ``.get``, which hides the hole). The wrapper
therefore accepts a ``list`` only when ``all(isinstance(item, dict)
for item in parsed)``; a list containing any non-dict is rejected with
the same ``HTTPException(400, ...)``. A well-formed batch (every element
a ``dict``, including ``[]``) still passes through so upstream's own
batch validation keeps ownership of enablement / size limits.

Unlike the ``UnicodeDecodeError`` widening (which is correct wherever
``parse_json`` runs), the body-envelope guard is a request-*body* contract
grafted onto a generic JSON helper, so it fires at every ``parse_json``
call site in the installed strawberry - nine in total, though one is
unreachable (``AsyncBaseHTTPView.parse_multipart_subscriptions`` is
defined but never called anywhere in the installed 0.316.0 package, so
its body parse is dead code today; eight sites are reachable):

- the sync and async POST-body sites (``sync_base_view.py`` /
  ``async_base_view.py``) the guard was designed for, plus the async
  multipart-subscriptions body (the dead-code site above): guard
  correct;
- the sync and async multipart ``operations`` / ``map`` form fields:
  the guard *widens* behavior beneficially - a scalar ``operations`` or
  ``map`` previously escaped ``replace_placeholders_with_files`` /
  ``data.get("query")`` as an unhandled ``500`` and now gets the
  controlled ``400``;
- the GET ``variables`` / ``extensions`` parses inside
  ``BaseView.parse_query_params`` (``base.py``): the guard is WRONG
  here. Upstream's own downstream handling in ``parse_http_body`` is
  precise (``null`` -> ``None`` -> the request executes; a scalar ->
  a per-param ``400``), so an unshielded guard breaks a valid request
  (``?variables=null`` regressing 200 -> 400) and shadows upstream's
  per-param message with a "request body" message on a bodyless GET.

The two GET sites are therefore shielded: :func:`apply` also installs
:func:`_patched_parse_query_params`, a source-pinned reimplementation
of upstream's ``parse_query_params`` whose two nested parses call the
captured ``_original_parse_json`` directly, restoring exact upstream
GET semantics while the wrapper keeps hardening the seven
body/multipart sites. Because the shield is a *reimplementation* rather
than a delegating wrapper, ``_validate_upstream_shape`` pins the
superseded upstream body source (the reimplementer's contract
established by
``_django_patches._UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE``) so an
upstream body change fails loudly at ``apply()`` time instead of being
silently superseded. The shield shares the envelope guard's lifecycle:
retire both together when upstream #3398 lands.

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
``isinstance(data, dict)`` guard, and the batch branch still does
``item.get(...)`` with no per-element ``isinstance(item, dict)`` guard:
<https://github.com/strawberry-graphql/strawberry/blob/e7d4a8235a11a4c4fd2b9fa605c437c9f86e5fb7/strawberry/http/sync_base_view.py>
(and the ``async_base_view.py`` sibling). It is tracked by the **open**
issue #3398, "AttributeError when query passed is a list and not a dict"
(opened 2024-02-27 against 0.219.2, no merged PR):
<https://github.com/strawberry-graphql/strawberry/issues/3398>. The
issue's title says *list* because at 0.219.2 a top-level list was
unguarded too; current versions intercept lists in the batch branch, so
the still-unhandled triggers are the JSON *scalar* case and the
*non-object batch element* case - the same ``.get()``-on-a-non-dict root
cause. Retire the envelope guard once #3398 lands ``isinstance`` checks
(or equivalent) ahead of both ``data.get("query")`` and each batch
``item.get(...)``.

Two lifecycles, and one that left
---------------------------------

Read the retirement question per concern, because this module carries two
independent upstream *bugs* that do not retire together:

1. **The ``UnicodeDecodeError`` translation** - retirable once upstream
   broadens its ``except`` to cover ``UnicodeDecodeError`` (or
   ``ValueError``).
2. **The body-envelope guard and its ``parse_query_params`` shield** -
   retirable together once upstream #3398 lands the ``isinstance``
   checks; the shield exists only to keep the guard off the GET path, so
   it has no independent lifecycle.

There used to be a third entry: the strict UTF-8 wire contract, which is
**not** retirable with either, because upstream will never "fix" behavior
that is not a bug (RFC 8259 auto-detection over raw ``bytes``) - the
package deliberately narrows it. Keeping a permanent policy in a module
whose other two concerns are scheduled for deletion made "delete this
module when 1 and 2 land" a security regression waiting to happen, so the
policy moved to ``views.py::_RequestBodyBoundaryMixin.parse_json`` (see
"Where the strict UTF-8 wire contract lives" above). **This module can now
be deleted outright once 1 and 2 both retire**, and that is the only
reason the deletion is safe.

Re-checking whether upstream fixed this
---------------------------------------

You do not need to redo the research from scratch. Two ways to tell
whether the two *upstream-bug* halves are still required (the wire
contract is not an upstream question at all, and no longer lives here -
see "Two lifecycles" above):

1. End-to-end, for **gap 2 only**. Set ``DJANGO_STRAWBERRY_FRAMEWORK =
   {"APPLY_UPSTREAM_PATCHES": False}`` and run the fakeshop scalar-body
   and non-object-batch rows::

       uv run pytest examples/fakeshop/test_query/test_products_api.py \
           -k non_object

   If they still return 400 with the patch off, upstream has fixed gap 2;
   if they do not (Django surfaces the raw ``AttributeError`` as a 500 and
   ``django.test.Client`` re-raises it), the guard is still needed. For
   the batch-element half, a 400 of "Batching is not enabled" with the
   patch off (fakeshop's default) is *not* proof of an upstream fix -
   enable ``batching_config`` and re-check that ``[1,2,3]`` still 500s.

   **Gap 1 has no live diagnostic any more**, and reading one into the
   suite inverts the verdict. Every fakeshop body row posts to a *package*
   view, whose own strict UTF-8 decode (spec-046 Decision 9) rejects an
   undecodable body before ``parse_json`` is entered - so
   ``test_post_invalid_utf8_json_body_returns_400_not_500``,
   ``test_post_raw_binary_body_returns_400_not_500``, and the whole
   UTF-16 / UTF-32 / UTF-8-BOM set answer 400 with this patch on OR off.
   That is the wire contract passing, not upstream. Use probe 2 for
   gap 1, or mount ``strawberry.django.views.GraphQLView`` directly.

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

The ``parse_query_params`` shield has no upstream bug of its own to
track - it exists purely to keep the gap-2 envelope guard off the GET
path - so it retires in the same change that retires the envelope guard.

Surface visibility
------------------

The patch module is intentionally private (leading underscore). The
:func:`apply` entry point is exported (no leading underscore) so the
package's regression tests can call it explicitly without going through
the AppConfig.
"""

import inspect
import textwrap
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


# Capture the genuine upstream methods once, at import time, before ``apply()``
# can install our replacements. ``_patched_parse_json`` delegates to the
# captured ``parse_json`` (so a self-healing re-install never wraps a wrapper),
# and ``_patched_parse_query_params`` routes its nested parses through the same
# captured original to keep the scalar guard off the GET path.
_original_parse_json = None if BaseView is None else BaseView.__dict__.get("parse_json")
_original_parse_query_params = (
    None if BaseView is None else BaseView.__dict__.get("parse_query_params")
)


# Upstream's own ``BaseView.parse_json`` rejection reason, reproduced verbatim
# so the widened ``except`` is indistinguishable from the ``except`` it widens.
# ``views.py::_JSON_PARSE_REASON`` reproduces the same literal for the package's
# strict-decode rejection (spec-046 Decision 9): one byte sequence, one
# interpretation at every hop, ``__cause__`` the only discriminator. The two
# copies are deliberate rather than imported - this module must stay importable
# (and deletable) without reaching into the package's view surface, so
# ``tests/test_views.py`` pins both against what upstream actually raises.
_UPSTREAM_JSON_PARSE_REASON = "Unable to parse request body as JSON"


# The exact upstream body :func:`_patched_parse_query_params` supersedes
# (verbatim at strawberry-graphql 0.316.0, dedented). Because the shield
# REIMPLEMENTS upstream's body instead of wrapping and delegating to it, an
# upstream body change does not flow through the patch the way it does for
# the delegating ``parse_json`` wrapper. ``_validate_upstream_shape``
# therefore pins this source so any upstream body change - new query params,
# changed falsy-skip semantics, or different parse routing - fails loudly at
# apply() time instead of being silently superseded.
_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE = textwrap.dedent(
    """\
    def parse_query_params(self, params: QueryParams) -> dict[str, Any]:
        params = dict(params)

        if "variables" in params:
            variables = params["variables"]

            if variables:
                params["variables"] = self.parse_json(variables)

        if "extensions" in params:
            extensions = params["extensions"]

            if extensions:
                params["extensions"] = self.parse_json(extensions)

        return params
    """,
)


def _validate_upstream_shape() -> None:
    """Fail loudly when Strawberry no longer exposes the method shapes we patch.

    Two patched methods, two validation depths (delegators pin the call
    shape, reimplementers pin the body - the ``_django_patches``
    precedent):

    - ``parse_json`` is wrapped and delegated to, so only the captured
      delegation target's presence and ``(self, data)`` arity are
      pinned; upstream body changes flow through the delegated call.
    - ``parse_query_params`` is reimplemented, so on top of presence and
      the ``(self, params)`` arity the captured original's body source
      is pinned against ``_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE``.
      Unreadable source (e.g. a bytecode-only distribution) is treated
      as drift: an unverifiable body must not be silently superseded.
    """
    if (
        BaseView is None
        or HTTPException is None
        or not callable(_original_parse_json)
        or not callable(_original_parse_query_params)
    ):
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Strawberry patch: expected "
            "strawberry.http.base.BaseView.parse_json, BaseView.parse_query_params, "
            "and cross_web.HTTPException. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"strawberry": False} '
            "or use supported dependency versions.",
        )
    parameters = tuple(inspect.signature(_original_parse_json).parameters.values())
    if len(parameters) != 2 or any(
        parameter.kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters
    ):
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Strawberry patch: "
            "BaseView.parse_json no longer has the expected (self, data) signature. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"strawberry": False} '
            "or use a supported Strawberry version.",
        )
    parameters = tuple(inspect.signature(_original_parse_query_params).parameters.values())
    if len(parameters) != 2 or any(
        parameter.kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in parameters
    ):
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Strawberry patch: "
            "BaseView.parse_query_params no longer has the expected (self, params) signature. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"strawberry": False} '
            "or use a supported Strawberry version.",
        )
    try:
        source = textwrap.dedent(inspect.getsource(_original_parse_query_params))
    except (OSError, TypeError):
        source = None
    if source != _UPSTREAM_PARSE_QUERY_PARAMS_SOURCE:
        raise RuntimeError(
            "Cannot apply django-strawberry-framework's Strawberry patch: "
            "BaseView.parse_query_params no longer matches the upstream body "
            "this patch supersedes. "
            'Disable this patch with APPLY_UPSTREAM_PATCHES = {"strawberry": False} '
            "or use a supported Strawberry version.",
        )


def _patched_parse_json(self: Any, data: "str | bytes") -> Any:
    """Wrapper around ``BaseView.parse_json`` closing two upstream gaps.

    1. **The ``UnicodeDecodeError`` translation.** Upstream's ``parse_json``
       catches only ``json.JSONDecodeError``, but ``json.loads`` on
       ``bytes`` that are not decodable under the encoding it detects
       raises ``UnicodeDecodeError`` - a ``ValueError``, and not a
       ``JSONDecodeError``, so it escapes upstream's ``except`` and
       surfaces as an unhandled ``500``. It is translated here to the
       same ``HTTPException(400, ...)`` Strawberry already raises for
       unparseable JSON, which is why closing the gap needs no new status
       code or message.
    2. A successfully-parsed body that is not a GraphQL-over-HTTP envelope
       is rejected with ``HTTPException(400, ...)``. ``parse_http_body``
       handles a JSON object (a single operation) and a JSON array of
       objects (a batch), but a bare scalar falls through to
       ``data.get("query")`` and a batch array containing any non-object
       falls through to ``item.get("query")`` - both raw
       ``AttributeError`` -> ``500``. Upstream's ``_validate_batch_request``
       does not check element types, so a well-typed batch ``list`` (every
       element a ``dict``, including ``[]``) is passed through untouched
       for that validator to own enablement / size limits; scalars and
       lists with any non-``dict`` element are rejected here.

    **This function does not decode, and must not start.** The strict
    UTF-8 wire contract that used to live here now belongs to
    ``views.py::_RequestBodyBoundaryMixin.parse_json`` (spec-046 Decision
    9; see the module docstring for why the lifecycles had to split).
    Consequently this wrapper preserves upstream's ``bytes`` semantics
    exactly - ``json.loads``'s RFC 8259 auto-detection still applies to a
    ``bytes`` argument that reaches it, which is what a consumer mounting
    Strawberry's own view is entitled to - and on a package view it only
    ever receives ``str``, because the view boundary decoded first.

    Adding a decode back here would recreate the defect the split fixed:
    a security policy sharing a temporary patch's kill switch. Adding one
    to the ``cross_web`` request adapter instead would be worse still - a
    ``UnicodeDecodeError`` raised inside that adapter's ``body``
    *property* escapes this ``except`` entirely and surfaces as the
    unhandled ``500`` that is the original upstream bug (see
    :mod:`django_strawberry_framework._cross_web_patches`).

    The body-envelope guard is a request-*body* contract enforced from a
    generic JSON helper, so it fires at every upstream ``parse_json`` call
    site (nine, one of them dead code at 0.316.0; see the module
    docstring's inventory): correct at the seven body/multipart sites (at
    the multipart sites it converts an upstream scalar-``operations``/``map``
    ``500`` into this ``400``), and deliberately kept OFF the two GET
    sites inside
    ``parse_query_params``, which :func:`_patched_parse_query_params`
    routes through the captured original so upstream's own per-param
    handling keeps ownership there. Both views inherit the single
    ``BaseView`` method, so one install covers sync and async. Every
    other outcome - a successful object / well-typed-array parse, or any
    other exception - is passed through untouched.
    """
    try:
        parsed = _original_parse_json(self, data)
    except UnicodeDecodeError as exc:
        raise HTTPException(400, _UPSTREAM_JSON_PARSE_REASON) from exc
    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
        return parsed
    raise HTTPException(
        400,
        "The GraphQL request body must be a JSON object "
        "(or an array of operations for a batch request).",
    )


def _patched_parse_query_params(self: Any, params: Any) -> "dict[str, Any]":
    """Source-pinned reimplementation of ``BaseView.parse_query_params``.

    Byte-for-byte upstream semantics (the superseded body is pinned as
    ``_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE``) except that the two nested
    ``self.parse_json`` calls go through the captured
    ``_original_parse_json`` instead of the patched method. That keeps
    :func:`_patched_parse_json`'s scalar guard - a request-*body*
    contract - out of the GET query-param path, where upstream's
    ``parse_http_body`` has its own precise handling downstream:

    - ``variables=null`` / ``extensions=null`` parse to ``None`` and the
      request executes (valid "object or null" values per upstream);
    - a scalar param (``variables=42``) parses and then gets upstream's
      per-param ``400`` ("must be an object or null, if provided"),
      not the guard's request-body message on a bodyless GET;
    - malformed JSON still becomes upstream's ``HTTPException(400,
      ...)``, raised inside the delegated original. Gap 1 is moot on
      this path: query params arrive as ``str`` (Django has already
      decoded the query string), so ``json.loads`` cannot raise
      ``UnicodeDecodeError`` here.

    An empty-string param is left unparsed (upstream's falsy skip),
    exactly as upstream leaves it. Installed by :func:`apply` alongside
    :func:`_patched_parse_json`; both live on ``BaseView`` so the sync
    and async views share them.
    """
    params = dict(params)

    if "variables" in params:
        variables = params["variables"]

        if variables:
            params["variables"] = _original_parse_json(self, variables)

    if "extensions" in params:
        extensions = params["extensions"]

        if extensions:
            params["extensions"] = _original_parse_json(self, extensions)

    return params


def _patch_is_installed() -> bool:
    """Return ``True`` iff both patched methods currently point at our replacements.

    A partial install (a third party reverted one of the two methods)
    reports ``False`` so the next ``apply()`` re-installs the pair
    together - the scalar guard must never run without its GET shield.
    """
    return (
        BaseView is not None
        and BaseView.__dict__.get("parse_json") is _patched_parse_json
        and BaseView.__dict__.get("parse_query_params") is _patched_parse_query_params
    )


def apply() -> None:
    """Apply the Strawberry defensive patches shipped by the package.

    Installs :func:`_patched_parse_json` (the two-gap body hardening) and
    :func:`_patched_parse_query_params` (the GET shield that keeps the
    scalar guard off upstream's query-param parses) as a pair.

    Idempotent and self-healing: re-entrant calls are no-ops when both
    patches are still installed, and re-install the pair if a third
    party reverted either method since the prior call. Called from
    :meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`
    at Django startup.

    No-ops in two cases:

    - The ``APPLY_UPSTREAM_PATCHES`` setting disables the patches
      globally (``False``) or for the ``"strawberry"`` dependency
      (``{"strawberry": False}``). Returns before touching anything.
    - Both patches are already installed (re-entrant call).

    Before installation, validates the imported symbols, the delegated
    ``parse_json``'s ``(self, data)`` signature, and the superseded
    ``parse_query_params`` body source (see
    :func:`_validate_upstream_shape`). Dependency drift raises a
    targeted ``RuntimeError`` instead of silently dropping the request
    hardening.
    """
    if not upstream_patches_enabled("strawberry"):
        return
    _validate_upstream_shape()
    if _patch_is_installed():
        return
    BaseView.parse_json = _patched_parse_json
    BaseView.parse_query_params = _patched_parse_query_params
