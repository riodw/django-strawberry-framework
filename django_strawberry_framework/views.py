"""The package's Django GraphQL HTTP endpoint, declared in the consumer's URLconf.

``DjangoGraphQLView`` and ``AsyncDjangoGraphQLView`` are the package's thin
subclasses of Strawberry's Django views. Mounting one of them in the project's
``urlpatterns`` is what puts GraphQL HTTP inside Django's real request
lifecycle - the whole ``MIDDLEWARE`` stack, the ``ALLOWED_HOSTS`` host check,
CSRF, security headers, cache policy, and every consumer-authored middleware
(spec-065 Decision 6)::

    # myproject/urls.py
    from django.urls import path

    from django_strawberry_framework.views import DjangoGraphQLView

    from myproject.schema import schema

    urlpatterns = [
        path("graphql/", DjangoGraphQLView.as_view(schema=schema)),
    ]

HTTP path matching is therefore Django's: ``path("graphql/", ...)`` matches
``/graphql/`` and nothing else, ``/graphql`` is handled by ``CommonMiddleware``'s
``APPEND_SLASH``, and ``/graphql-admin`` reaches the rest of the URLconf. This
declaration is independent of ``routers.py``'s ``websocket_url_pattern``, which
governs the WebSocket branch alone.

The module also owns the package's whole raw-request-body boundary on this path -
the cumulative body cap (spec-065 Decision 7) and the strict UTF-8 wire contract
(Decision 9). Both are properties of the bytes this endpoint is willing to
process, so both decisions land on one mixin, ``_RequestBodyBoundaryMixin``: see
it for the contract, including the honest statement of what an application-level
cap can and cannot bound (Decision 8). The private-Django interaction the cap
needs to measure a body without materializing it is centralized in
``_request_body.py``, which this module reads one boolean out of.

A cap that runs after something else has already parsed the body is not a gate,
and Django's own ``CsrfViewMiddleware.process_view`` reads
``request.POST.get("csrfmiddlewaretoken", "")`` on **every** cookie-bearing POST -
before the view, and on a multipart request that read is what invokes
``MultiPartParser`` and the upload handlers. Both package views therefore mark
the callback ``as_view`` returns ``csrf_exempt`` - once, on the shared mixin - and
re-enter Django's *own* CSRF implementation from inside the view, after the
boundary has run, through the public ``csrf_protect`` decorator (see
:func:`_run_after_csrf_check`). The
exemption is an ORDERING MECHANISM, never a bypass: every request that gets past
the size boundary still goes through the complete CSRF check.

The wire contract needs one thing the mixin cannot provide, which is why it has a
second owner here: upstream's sync adapter decodes inside its own ``body``
property, so the mixin's strict decode would never see the bytes at all whenever
the ``APPLY_UPSTREAM_PATCHES`` workarounds are off. ``_RawBodyRequestAdapter``
supplies the raw-bytes body source through upstream's own
``request_adapter_class`` seam, so the decode is reached in every patch state - a
decode the bytes never reach is not an enforcement. The async view needs no
counterpart, because upstream's async adapter already hands over bytes; that
asymmetry is deliberate and pinned by test.

This module is ``channels``-free, and so is everything it imports:
``strawberry.django.views`` reaches only for the standard library, ``asgiref``,
``cross_web``, ``django``, ``strawberry.http``, and its own
``strawberry.django.context`` sibling; ``cross_web`` is part of that same
existing hard dependency chain; and the two first-party imports (``conf``,
``exceptions``) reach only ``django.conf`` / ``django.test.signals`` and the
standard library. A WSGI-only project can therefore adopt the package's GraphQL
HTTP endpoint without ever touching the soft ``channels`` dependency that
``routers.py::require_channels`` guards - both this body and upstream's
re-execute under a simulated ``channels`` absence to keep that true. Like every
other integration surface
(``routers.py``, ``middleware/debug_toolbar.py``, ``extensions/``), these are
leaf-module imports and never package-root exports.
"""

from __future__ import annotations

import codecs
from typing import TYPE_CHECKING, Any

from cross_web import DjangoHTTPRequestAdapter, HTTPException
from django.conf import settings
from django.utils.decorators import classonlymethod
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from strawberry.django.views import AsyncGraphQLView, GraphQLView

from django_strawberry_framework._request_body import body_exceeds_limit
from django_strawberry_framework.conf import max_request_body_bytes_setting
from django_strawberry_framework.exceptions import ConfigurationError, describe_value

if TYPE_CHECKING:  # pragma: no cover - type-checking-only imports.
    from collections.abc import Mapping

    from cross_web import AsyncHTTPRequestAdapter, SyncHTTPRequestAdapter
    from django.http import HttpRequest

__all__ = ("AsyncDjangoGraphQLView", "DjangoGraphQLView")


#: The wire reason for an over-limit body, verbatim from spec-065's Error
#: shapes. Named once so the package tier can import the exact bytes the live
#: tier reads off the response.
_BODY_LIMIT_REASON = "Request body exceeded the configured GraphQL request-body limit."

#: The wire reason for a request body the endpoint refuses to read as JSON -
#: ``strawberry.http.base.BaseView.parse_json``'s own literal, reproduced
#: verbatim rather than invented. Identity with upstream is the contract, not a
#: coincidence: a body rejected by the package's strict decode and a body
#: rejected by upstream's ``json.loads`` must be indistinguishable on the wire,
#: so one byte sequence has one interpretation at every hop and no caller can
#: attribute a rejection by message (spec-065 Decision 9). ``__cause__`` is the
#: only discriminator. ``_strawberry_patches.py`` reproduces the same literal for
#: its own upstream-bug translation, and
#: ``tests/test_views.py::test_the_wire_reason_is_upstreams_own_parse_json_literal``
#: pins this constant against what upstream actually raises, so a message change
#: on either side fails loudly instead of splitting the contract.
_JSON_PARSE_REASON = "Unable to parse request body as JSON"

#: Django's own spelling for a multipart request, as ``HttpRequest.content_type``
#: reports it (the bare media type, with ``boundary=...`` split off into
#: ``content_params``).
_MULTIPART_CONTENT_TYPE = "multipart/form-data"

#: The two GraphQL-multipart form fields that carry a JSON control document, as
#: named by the multipart request specification and read by upstream's
#: ``parse_multipart`` on both transports. Everything else in the form is a file
#: payload Django's upload handlers own.
_MULTIPART_CONTROL_FIELDS = ("operations", "map")

#: U+FFFD REPLACEMENT CHARACTER, written as an escape to keep this file ASCII.
#: Django decodes non-file multipart fields with ``errors="replace"``, so every
#: byte sequence it could not decode arrives as exactly this character - which is
#: what makes its presence a loss detector rather than a taste judgement.
_REPLACEMENT_CHARACTER = "\ufffd"

#: The canonical name every UTF-8 alias resolves to (``"utf8"``, ``"UTF-8"``,
#: ``"u8"``, ...). Compared against rather than string-matched so an alias the
#: package never heard of is still accepted when Python says it IS UTF-8, and so
#: ``utf-8-sig`` - a *different* codec that would silently eat a BOM Decision 10
#: deliberately refuses - is not mistaken for one.
_UTF8_CODEC_NAME = codecs.lookup("utf-8").name


def _resolved_max_request_body_bytes(value: object) -> int | None:
    """Resolve the per-mount cap: constructor > setting > default.

    ``value`` is the view instance's ``max_request_body_bytes``. ``None`` there
    means "this mount did not override anything", so the
    ``MAX_REQUEST_BODY_BYTES`` setting decides (and its own default supplies the
    1 MiB package default - this module never restates that number). ``None``
    from the *setting* is the documented way to disable the package cap
    entirely, which is why the two rungs read the same sentinel differently
    (spec-065 Decision 7 step 4).

    Validation lives here rather than in ``conf.py``, which stays a thin reader
    - the same split ``optimizer/nested_fetch.py::resolve_strategy`` uses for
    ``NESTED_CONNECTION_STRATEGY``. ``0`` is rejected rather than treated as
    "unlimited": it is the near-universal unlimited spelling elsewhere, yet
    under this module's ``>`` comparison it would mean "reject every non-empty
    body", so failing loud is the only reading that cannot be misread. ``bool``
    is rejected explicitly because ``isinstance(True, int)`` is ``True``.

    The ``got`` tail is rendered by ``exceptions.py::describe_value`` rather than
    interpolated directly, because the f-string runs at the RAISE SITE: a
    negative integer too large to convert to a string (CPython 3.11+ refuses
    beyond ``sys.get_int_max_str_digits()``) reaches the ``value <= 0`` arm and
    would raise ``ValueError`` from inside the message instead of the promised
    ``ConfigurationError`` - on exactly the hostile-configuration path where the
    typed error IS the contract.
    """
    if value is None:
        value = max_request_body_bytes_setting()
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigurationError(
            f"max_request_body_bytes must be a positive int of bytes or None to disable "
            f"the package request-body cap; got {describe_value(value)}.",
        )
    return value


def _declared_content_length(request: HttpRequest) -> int | None:
    """The request's declared ``CONTENT_LENGTH`` as an ``int``, or ``None``.

    ``None`` covers both unmeasurable shapes: the header is absent
    (``int(None)`` -> ``TypeError``) or is not a number (``ValueError``). Both
    fall through to the counted check rather than being trusted, which is the
    fail-safe direction - an unparseable declaration must not buy a larger body.
    """
    try:
        return int(request.META.get("CONTENT_LENGTH"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _canonicalizes_to_utf8(encoding: object) -> bool:
    """Whether ``encoding`` names a codec Python canonicalizes to UTF-8.

    ``codecs.lookup`` supplies the answer instead of a name comparison, so every
    UTF-8 alias is accepted (``"utf8"``, ``"U8"``, an alias the package never
    heard of) and only codecs that genuinely canonicalize to UTF-8 are -
    ``utf-8-sig`` is a *different* codec and is refused. An unknown name raises
    ``LookupError`` and a non-string raises ``TypeError``; both mean "the package
    cannot prove this is UTF-8", which is a rejection.
    """
    try:
        return codecs.lookup(encoding).name == _UTF8_CODEC_NAME  # type: ignore[arg-type]
    except (LookupError, TypeError):
        return False


def _form_encoding_is_utf8(request: HttpRequest) -> bool:
    """Whether Django will decode this form's non-file fields as UTF-8.

    Two INDEPENDENT conditions, joined with ``and``. They are deliberately not a
    fallback chain: Django applies no such order, and reading them as one was a
    bypass (spec-065 review round 2, M1). What Django actually does, read out of
    ``django/http/request.py`` and ``django/http/multipartparser.py`` and
    confirmed by execution at both supported versions:

    * the declaration is consulted exactly **once**, at
      ``HttpRequest._set_content_type_params``, which promotes a *usable*
      ``charset`` onto ``request.encoding`` and silently ignores an unusable one;
    * at parse time ``content_params`` is never read again.
      ``HttpRequest.parse_file_upload`` hands ``MultiPartParser`` only
      ``self.encoding``, and ``MultiPartParser.__init__`` resolves
      ``encoding or settings.DEFAULT_CHARSET``. **That pair is the only value
      Django decodes with.**

    So the conditions are, numbered in the order the body below evaluates them:

    1. **A declared ``charset``, when present, must canonicalize to UTF-8.** Not
       implied by condition 2: for a codec name Django cannot load, the promotion
       does not happen, so ``request.encoding`` stays ``None`` and condition 2 is
       satisfied by ``DEFAULT_CHARSET`` - accepting a request whose declaration
       nobody honoured. The package refuses instead. A client that asks for an
       encoding this endpoint will not honour gets a controlled ``400`` rather
       than a decode in some other encoding, and that stays true for a *usable*
       non-UTF-8 name as well, so the two conditions never have to be reasoned
       about jointly.
    2. **The encoding Django will actually use** - ``request.encoding or
       settings.DEFAULT_CHARSET``, verbatim the expression
       ``parse_file_upload`` and ``MultiPartParser.__init__`` produce between
       them - must canonicalize to UTF-8. It is checked whatever the client
       declared, which is the whole point: ``request.encoding`` is Django's
       documented per-request override, so one line of consumer middleware
       assigning it overwrites the promotion, and a declared ``charset=utf-8``
       must not be allowed to mask that. Reading the declaration *instead* let a
       client pick which value was validated while Django decoded with the other
       one - and a Latin-1 decode never fails, so it produces no
       :data:`_REPLACEMENT_CHARACTER` and
       :meth:`_RequestBodyBoundaryMixin._reject_lossy_multipart_control_fields`
       could not see it either.

    A project that reconfigures ``DEFAULT_CHARSET`` away from UTF-8 is therefore
    refused when nothing else supplies the encoding, and accepted when the client
    declares UTF-8 - because that declaration is promoted onto
    ``request.encoding`` and is genuinely what Django decodes with. The package
    tracks Django's real behavior rather than restating a rung order of its own.

    A per-*part* charset is deliberately not consulted, because Django does not
    consult it either: ``MultiPartParser._parse`` honours it only in the FILE
    branch, so on ``operations`` / ``map`` it has no effect and treating it as
    meaningful would be inventing a contract Django does not implement.
    """
    declared = (request.content_params or {}).get("charset")
    if declared is not None and not _canonicalizes_to_utf8(declared):
        return False
    return _canonicalizes_to_utf8(request.encoding or settings.DEFAULT_CHARSET)


def _is_multipart_form_post(request: HttpRequest) -> bool:
    """Whether Django will hand this request's fields to ``MultiPartParser``.

    Both halves are load-bearing and both are read off
    ``django/http/request.py::HttpRequest._load_post_and_files``: it installs an
    empty ``QueryDict`` without parsing anything unless ``request.method`` is
    ``"POST"``, and only then does a ``multipart/form-data`` content type reach
    ``parse_file_upload``. So a stray multipart ``Content-Type`` on a GET - a
    client reusing a previous request's headers - is not a multipart form at all:
    Django decodes no field, the view reads no body, and refusing it would be the
    package inventing a rejection for bytes nobody parses (spec-065 review round
    2, L1).

    Naming the discrimination once is also what keeps the two guards below from
    disagreeing about what "multipart" means. Upstream answers ``405`` to every
    method other than GET and POST, so the one shape this excludes from the cap's
    multipart carve-out - a multipart content type on some other method - is a
    request Django parses no form for and Strawberry refuses outright; it is
    counted like any other body, which is the stricter direction.
    """
    return request.method == "POST" and request.content_type == _MULTIPART_CONTENT_TYPE


class _RawBodyRequestAdapter(DjangoHTTPRequestAdapter):
    """Upstream's sync Django request adapter, minus the eager body decode.

    ``strawberry.http.sync_base_view`` reads the request body at exactly one site,
    as ``request_adapter.body``, and upstream's sync adapter answers it with
    ``self.request.body.decode()`` - a bare UTF-8 decode performed inside a
    *property*. A property cannot own an error contract: the
    ``UnicodeDecodeError`` it raises escapes ``dispatch``'s
    ``except HTTPException`` and surfaces as an unhandled ``500``, and
    ``parse_json`` is never entered with bytes at all, so the decode below it
    cannot run.

    The strict UTF-8 wire contract (spec-065 Decision 9) therefore needs two
    things from the sync transport, not one: a strict decode
    (``_RequestBodyBoundaryMixin.parse_json``) *and* the bytes arriving there
    undecoded. ``request_adapter_class`` is upstream's own per-view seam for the
    second half - every integration sets it (Django, Flask, Starlette, Sanic,
    Chalice, ...) - so the package view sets its own, and this subclass overrides
    exactly one property to match ``AsyncDjangoHTTPRequestAdapter.get_body``'s
    contract: raw bytes, handed to the one method that can answer a bad body with
    a response.

    **Why this is not the ``cross_web`` patch again.** The two fix the same
    upstream defect at deliberately different scopes.
    ``_cross_web_patches.py::_patched_body`` replaces the property on upstream's
    class for the whole process, so that a consumer who mounts *Strawberry's own*
    view also gets a controlled ``400``; it is a workaround for someone else's
    bug, so it is gated by ``APPLY_UPSTREAM_PATCHES`` and it retires when upstream
    stops decoding eagerly. This class is the package view's own body source, and
    it is what makes the wire contract hold on a package mount in **every** patch
    state - including the broad ``APPLY_UPSTREAM_PATCHES = False``, where the sync
    transport used to answer ``500`` for a BOM'd UTF-16 / UTF-32 body (spec-065
    review W3-2). Ownership follows lifecycle here exactly as it does for the
    decode itself: permanent package policy must not be reachable only through a
    switchable workaround.

    Subclassing rather than copying keeps every other adapter member upstream's,
    and means the patch state cannot matter to a package view even by install
    order: this property shadows the class attribute by identity, patched or not.

    The async view needs no counterpart - upstream's
    ``AsyncDjangoHTTPRequestAdapter.get_body`` already returns
    ``self.request.body`` untouched, which is the contract this class reproduces
    for sync - and ``tests/test_views.py`` pins that so the asymmetry cannot
    silently become a gap.
    """

    @property
    def body(self) -> bytes:
        """The raw request body, undecoded, for ``parse_json`` to decode strictly."""
        return self.request.body


class _RequestBodyBoundaryMixin:
    """The package's raw-request-body boundary, shared by both package views.

    One mixin, one subject: the bytes of an incoming GraphQL request, and the
    two questions the package answers about them before Strawberry sees
    anything.

    1. **How many of them will be processed** - the cumulative request-body cap
       (spec-065 Decision 7), enforced from ``run`` on both views through
       :meth:`_enforce_request_boundary`.
    2. **How they become text** - the strict UTF-8 wire contract (Decision 9),
       enforced by overriding ``parse_json`` for a ``bytes`` body and, for the
       multipart control documents Django decodes before the package sees them,
       by :meth:`_enforce_multipart_form_encoding` and
       :meth:`_reject_lossy_multipart_control_fields`.

    They belong together because they are the same boundary read twice: the cap
    decides which bytes reach the parse, and the parse decides how those exact
    bytes are decoded. Both are permanent package policy that a consumer opts
    into by mounting a package view, and neither depends on an upstream defect
    or on ``APPLY_UPSTREAM_PATCHES`` (see ``parse_json`` for why that ownership
    is load-bearing rather than tidy).

    Sits first in each view's bases so this mixin's attribute and its methods take
    precedence over any same-named attribute or method upstream may later add:
    ``max_request_body_bytes`` and ``parse_json`` resolve to this policy ahead of
    anything upstream defines, and a consumer subclass can still override any part.
    Mixin-FIRST is not what satisfies ``View.as_view``'s keyword guard - that guard
    is a ``hasattr`` over the whole MRO, so a mixin-last subclass would bind
    ``max_request_body_bytes=`` identically; precedence over upstream is the
    operative reason.

    **Precedence.** ``as_view(max_request_body_bytes=...)`` > the
    ``MAX_REQUEST_BODY_BYTES`` setting > the setting's own 1 MiB default. A
    ``None`` kwarg defers to the setting; ``None`` *in the setting* disables the
    cap project-wide. A single mount therefore cannot disable the cap for itself
    - only the project-wide setting can - which is the documented cost of
    keeping one sentinel instead of adding a second one to a URLconf-facing
    keyword.

    **What is counted.** Bytes the application actually received, not the
    client's ``Content-Length``: a declaration that is absent or lying cannot
    buy a larger body. A declared over-limit length is refused first, without
    reading the body at all; otherwise the real length decides. A body exactly
    at the limit is allowed.

    **How it is counted, and why that matters.** Never by
    ``len(request.body)``. That property performs an unbounded read of the whole
    request into one ``bytes`` value, so counting it would detect an over-limit
    body only *after* the attacker-sized allocation the cap exists to prevent -
    and Django 5.2.0, this card's floor, has no seekable-stream size check of its
    own to shrink that window. ``_request_body.py::body_exceeds_limit`` measures
    instead: a seekable ASGI spool is size-probed with ``seek`` / ``tell`` and
    refused with nothing read, a non-seekable stream is read in bounded chunks up
    to ``limit + 1`` bytes and no further, and a body an earlier middleware
    already cached is measured from that cache and still refused. An allowed body
    is handed back as a rewound stream rather than as a pre-filled cache, so
    ``HttpRequest.body`` still runs in full: Strawberry receives the original bytes
    byte-for-byte, and Django's own ``DATA_UPLOAD_MAX_MEMORY_SIZE`` ceiling still
    fires where it always did. Whichever ceiling is lower still wins.

    **Multipart, on a POST.** Bounded by the declared-size gate plus Django's own
    ``MultiPartParser``, and nothing else. The carve-out is POST-scoped - a
    multipart content type on any other method is counted like any other body,
    which is the stricter direction (see :func:`_is_multipart_form_post`). The
    body is deliberately never
    materialized for a multipart request - reading it would pull the whole
    payload into memory and defeat Django's streaming upload handlers, breaking
    the ``Upload``-scalar path this package ships. Per-file count, per-file
    size, and aggregate size are NOT bounded here (audit S4); Django's
    ``DATA_UPLOAD_MAX_MEMORY_SIZE``, ``DATA_UPLOAD_MAX_NUMBER_FIELDS``,
    ``DATA_UPLOAD_MAX_NUMBER_FILES`` and ``FILE_UPLOAD_MAX_MEMORY_SIZE`` own them,
    and they are a CO-REQUIREMENT of this cap on any mount that enables uploads.

    **GET.** A no-op, on both halves: the view reads no body on GET, so the cap
    returns early, and a stray ``multipart/form-data`` ``Content-Type`` on a GET
    is not a form Django decodes either, so the encoding guard returns too (see
    :func:`_is_multipart_form_post`). The ``variables`` / ``extensions``
    query-param size is a separate concern, and
    ``_strawberry_patches.py::_patched_parse_query_params`` already shields
    those parses.

    **The honest boundary** (spec-065 Decisions 7 and 8). What this guarantees
    is that the application never parses, allocates a document from, or executes
    a schema against an over-limit body, that it never allocates or reads more
    than ``limit + 1`` bytes of one - except where an earlier middleware already
    materialized it, the one shape named at the end of this paragraph - and that
    the rejection is a tested ``413``.

    For a **multipart** request the declared gate is what runs, and what it now
    genuinely precedes is stated exactly: the ``413`` is raised before
    ``request.POST``, ``request.FILES``, ``MultiPartParser``, or any upload
    handler is entered, because the package view is ``csrf_exempt`` at its outer
    dispatch callback and re-enters CSRF *after* this boundary (see
    :func:`_run_after_csrf_check`; before that ordering fix, Django's
    ``CsrfViewMiddleware.process_view`` had already parsed the form to look for
    ``csrfmiddlewaretoken``). What the gate does NOT bound is a multipart body
    whose declared length is absent or understated: the counted check is skipped
    for multipart, so such a request is parsed by Django under Django's own
    upload settings and only its *control documents* are the package's business.

    What no application-level check can guarantee is that the bytes were never
    received: ``django.core.handlers.asgi.ASGIHandler.read_body`` has already
    drained the entire request into a spooled temporary file - rolling to disk
    past ``FILE_UPLOAD_MAX_MEMORY_SIZE`` - before any application cap can run. A
    reverse-proxy / ASGI-server cap is therefore a CO-REQUIREMENT of this one,
    not an alternative to it; this cap bounds what the application *processes*,
    never what the server *accepts*. The one shape it cannot bound at all is a
    body some earlier middleware already materialized: the allocation is done by
    the time ``run`` is entered, so the cap refuses the request rather than
    processing it, which is all that is left to do.
    """

    #: ``None`` means "this mount did not override the setting". Declared here
    #: rather than on each view so Django's ``as_view`` keyword guard admits it
    #: on both (``hasattr``, so an inherited attribute satisfies the guard).
    max_request_body_bytes: int | None = None

    @classonlymethod
    def as_view(cls, **initkwargs: Any) -> Any:  # noqa: N805 - Django's own signature
        """Return upstream's view callback, marked ``csrf_exempt``.

        The ordering half of the body boundary (spec-065 Decision 18), stamped
        once, here, so both views get it and a URLconf author cannot forget it.
        ``CsrfViewMiddleware.process_view`` reads ``csrf_exempt`` off the callback
        the URL resolver holds - so the callback is where it is put, rather than on
        ``dispatch`` for ``View.as_view`` to copy: a consumer subclass that
        overrides ``dispatch`` then keeps the ordering too, and the transport's
        coroutine marking (upstream's ``as_view`` sets it, ``csrf_exempt``
        preserves it, and ``functools.wraps`` carries ``view_class`` /
        ``view_initkwargs`` through) is untouched.

        See :func:`_run_after_csrf_check` for why an exemption is what buys this
        endpoint *more* CSRF ordering rather than less, and for the two shapes that
        can still lose the ordering (a wrapper that drops the attribute, and a
        consumer middleware that reads the body inbound).
        """
        return csrf_exempt(super().as_view(**initkwargs))

    def _enforce_request_boundary(self, request: HttpRequest) -> None:
        """Run the whole pre-CSRF, pre-parse boundary, in the one order that is safe.

        The size gate goes first because it is the only check that must run
        before anything else has touched the body, and the multipart encoding
        check goes second because it reads headers only - so neither of them
        parses the form, and ``run`` can hand a request that passes both to the
        CSRF continuation with the ordering guarantee intact.

        Both halves agree on what "multipart" means, through the one
        :func:`_is_multipart_form_post` discriminator, so the cap's carve-out and
        the encoding guard cannot drift apart on a request shape.
        """
        self._enforce_request_body_limit(request)
        self._enforce_multipart_form_encoding(request)

    def _enforce_request_body_limit(self, request: HttpRequest) -> None:
        """Raise ``HTTPException(413)`` when the request body exceeds the cap.

        Called first by :meth:`_enforce_request_boundary`, which ``run`` calls
        before anything else on both views, so the raise lands inside upstream's
        ``dispatch`` ``except HTTPException`` and comes out as the ``413``
        ``text/plain`` response the spec pins - the same translation the package's
        malformed-body ``400`` already rides. Being raised from there also puts it
        *outside* the CSRF continuation, so a ``413`` is produced before Django's
        token check reads ``request.POST``. Resolving the cap first means a
        misconfigured mount fails loud on every request, GET included.
        """
        limit = _resolved_max_request_body_bytes(self.max_request_body_bytes)
        if limit is None or request.method == "GET":
            return
        declared = _declared_content_length(request)
        if declared is not None and declared > limit:
            raise HTTPException(413, _BODY_LIMIT_REASON)
        if _is_multipart_form_post(request):
            return
        if body_exceeds_limit(request, limit):
            raise HTTPException(413, _BODY_LIMIT_REASON)

    def _enforce_multipart_form_encoding(self, request: HttpRequest) -> None:
        """Refuse a multipart request whose form fields will not be decoded as UTF-8.

        Half of the multipart wire contract (spec-065 Decision 9, review High 2),
        and the half that can be answered from headers alone - so it runs in
        ``run``, before the form is parsed at all, and an unhonourable
        declaration costs nothing to refuse.

        Scoped by :func:`_is_multipart_form_post` rather than by the content type
        alone, so it applies to exactly the requests whose fields Django decodes:
        a stray multipart ``Content-Type`` on a GET is not a form Django will
        parse, and this endpoint reads no body on GET either.

        The ``400`` carries :data:`_JSON_PARSE_REASON`, the same reason every
        other body the endpoint refuses to read as JSON carries, because a caller
        must not be able to attribute a rejection by message.
        """
        if not _is_multipart_form_post(request):
            return
        if not _form_encoding_is_utf8(request):
            raise HTTPException(400, _JSON_PARSE_REASON)

    def _reject_lossy_multipart_control_fields(self, form: Mapping[str, str | bytes]) -> None:
        """Refuse ``operations`` / ``map`` that Django could not decode losslessly.

        The other half of the multipart wire contract, and the reason it cannot be
        ``parse_json``'s: by the time the package sees these fields they are
        ``str``, because ``django/http/multipartparser.py::MultiPartParser._parse``
        has already run them through ``force_str(data, encoding,
        errors="replace")``. The original bytes are gone and so is the decode
        failure - every byte sequence Django could not decode is now
        :data:`_REPLACEMENT_CHARACTER`. Detecting that marker is therefore how a
        malformed-UTF-8 control document is detected at all, and it is checked
        before ``json.loads`` runs, because a replaced byte often *repairs* the
        document into something that parses.

        **What this contract is, precisely.** An accepted multipart control
        document must use an effective UTF-8 encoding (see
        :meth:`_enforce_multipart_form_encoding`) and must survive Django's decode
        without a replacement marker. That is slightly narrower than "every valid
        UTF-8 document": a client that genuinely needs U+FFFD *as data* sends its
        six-character ASCII JSON escape instead, which is preserved exactly - only
        a **literal** U+FFFD in the serialized document is refused. Genuine
        multibyte UTF-8, including everything a browser's ``JSON.stringify``
        emits, is untouched, so this is not an ASCII-only contract.

        **Why the check lives here rather than in a private parser.** Django owns
        multipart framing, limits, and file streaming, and it must keep owning
        them: ``FileUploadHandler.receive_data_chunk`` is only called for file
        payloads, never for ``operations`` / ``map``; ``handle_raw_input``'s
        contract is to take over the *entire* multipart parse; and copying or
        subclassing ``MultiPartParser._parse`` would fork Django's parser into
        this package for every release it supports. Distinguishing a genuine
        literal U+FFFD from a replacement-generated one is not possible above
        Django's decode, and the root fix for that is an upstream Django public
        hook for strict, non-file multipart-field decoding. Until such a hook
        exists at the supported floor, the package must not own or copy Django's
        multipart parser, and this loss detector is the honest boundary instead.

        A ``bytes`` value (which Django never produces, but the adapter protocol
        permits) is left alone deliberately: it still carries its own encoding, so
        ``parse_json``'s strict decode is the correct owner of it, not this
        marker check.
        """
        for field in _MULTIPART_CONTROL_FIELDS:
            value = form.get(field)
            if isinstance(value, str) and _REPLACEMENT_CHARACTER in value:
                raise HTTPException(400, _JSON_PARSE_REASON)

    def parse_json(self, data: str | bytes) -> Any:
        """Decode a ``bytes`` request body as strict UTF-8, then delegate upstream.

        The strict UTF-8 wire contract (spec-065 Decision 9): the success set for
        a GraphQL-over-HTTP body is UTF-8, and UTF-8 only. Because the delegate
        never sees ``bytes``, ``json.loads``'s RFC 8259 encoding auto-detection
        cannot run, so UTF-16 / UTF-32 (BOM or BOM-less) and a leading UTF-8 BOM
        stop being accepted request bodies - with **no rejection branch written
        for any of them**. The BOM'd multi-byte forms carry a leading byte that is
        not valid UTF-8 and fail at the decode below; the BOM-less forms and the
        UTF-8 BOM decode cleanly into text that upstream's own ``json.loads``
        refuses (a UTF-8 BOM is deliberately not stripped and not decoded with
        ``utf-8-sig`` - Decision 10). Both routes end in the identical ``400``;
        only ``__cause__`` differs (``UnicodeDecodeError`` vs
        ``json.JSONDecodeError``).

        A ``str`` input is passed through **untouched** and never re-encoded:
        upstream's GET ``variables`` / ``extensions`` parses and the multipart
        ``operations`` / ``map`` form fields arrive already decoded by Django.
        For the multipart pair that pass-through is not the whole contract, and
        cannot be - the bytes were consumed by Django's own parser before this
        method could see them - so their encoding is enforced separately, and
        earlier, by :meth:`_enforce_multipart_form_encoding` and
        :meth:`_reject_lossy_multipart_control_fields`. GET query parameters get no
        such treatment: they are ``str`` that Django decoded from the URL under
        ``request.encoding``, not a body, and upstream's ``json.loads`` is their
        only parser here.

        **Why the policy lives here and not in the patch module.** It used to
        live in ``_strawberry_patches.py::_patched_parse_json``, which made a
        permanent package security contract share the lifecycle - and the
        ``APPLY_UPSTREAM_PATCHES`` kill switch - of temporary workarounds for
        upstream bugs. A consumer disabling those workarounds (or a future
        maintainer deleting them once upstream fixes them) silently restored
        multi-encoding request bodies. Ownership now follows lifecycle: the patch
        module keeps translating the ``UnicodeDecodeError`` upstream's own
        ``except json.JSONDecodeError`` misses, which is a bug fix and stays
        opt-out-able, while the narrowing of the success set is enforced here, for
        every consumer who mounts a package view, whatever that switch says. A
        consumer who deliberately mounts Strawberry's own view keeps Strawberry's
        own semantics - that is their choice to make, and it is no longer made for
        them by an unrelated setting.

        That claim needs a second owner to be true on the sync transport, and it
        has one: a decode the bytes never reach is not an enforcement, and
        upstream's sync request adapter decodes inside a *property* before this
        method is entered. The view supplies its own body source instead
        (:class:`_RawBodyRequestAdapter`), so ``bytes`` arrive here on both
        transports in every patch state - see that class for the ``500`` the
        missing half used to produce.

        Both package views inherit this one method, so sync and async cannot
        diverge; ``super()`` keeps delegating to upstream's ``parse_json`` rather
        than reimplementing any part of it, so upstream stays the only JSON
        parser in the path.
        """
        if isinstance(data, bytes):
            try:
                data = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise HTTPException(400, _JSON_PARSE_REASON) from exc
        return super().parse_json(data)  # type: ignore[misc]


def _run_after_csrf_check(
    request: HttpRequest,
    delegate: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Call ``delegate`` - and be the function ``csrf_protect`` wraps.

    The whole ordering fix for the multipart declared cap (spec-065 Decision 7,
    review High 3) is which side of this function the CSRF check falls on.

    Django's ``CsrfViewMiddleware.process_view`` reads
    ``request.POST.get("csrfmiddlewaretoken", "")`` for every cookie-bearing POST,
    even one that will end up authenticating with the ``X-CSRFToken`` header, and
    on a multipart request that single read is what invokes ``MultiPartParser``
    and the project's upload handlers. Because ``process_view`` runs *before* the
    view, the package's declared-size gate used to be reached only after Django
    had already parsed - and possibly spooled to disk - the very body the gate
    exists to refuse.

    The fix is composition Django documents rather than machinery the package
    invents: the shared mixin's ``as_view`` returns
    ``csrf_exempt(super().as_view(...))``, which puts the mark on exactly the
    object ``process_view`` reads it off - the callback the URL resolver holds - so
    the project's global ``CsrfViewMiddleware.process_view`` skips the callback
    without touching ``request.POST`` (its ``process_request`` may still run, which
    parses nothing), and the view re-enters CSRF from *inside* ``run``, after the
    boundary, by calling this function through ``csrf_protect``.

    **This is an ordering mechanism, not a CSRF bypass.** ``csrf_protect`` is
    ``decorator_from_middleware(CsrfViewMiddleware)``: the same class, running its
    real ``process_request`` / ``process_view`` / ``process_response``, so cookie
    and header tokens, form tokens, ``Origin`` and ``Referer`` checks,
    ``CSRF_FAILURE_VIEW``, cookie rotation and ``Vary: Cookie`` all behave exactly
    as they did. Django anticipates this composition explicitly -
    ``process_response`` clears ``CSRF_COOKIE_NEEDS_UPDATE`` so "both a decorator
    and middleware" cannot double-set the cookie, and ``_accept`` sets
    ``request.csrf_processing_done`` so the check cannot run twice. The
    continuation is package-owned and unconditional: there is no setting that
    turns it off, which also means the package's GraphQL endpoint stays
    CSRF-protected on a project that forgot ``CsrfViewMiddleware`` entirely.

    It is a module-level function decorated once at import, not a per-request
    decoration, so exactly one ``CsrfViewMiddleware`` instance exists per
    transport - the same lifetime a ``MIDDLEWARE`` entry has. ``delegate`` is
    passed *in* rather than closed over so the function stays stateless and both
    views can share one shape; the first positional parameter has to be the
    request because that is the view signature ``csrf_protect`` calls.

    **What this does NOT guarantee, stated rather than assumed.** Three limits,
    each of them a property of the surrounding stack rather than of this function:

    - It orders the package's own CSRF check behind the body boundary, and
      nothing else. **Any consumer middleware that touches ``request.POST`` (or
      ``request.body``) on the way in still runs before the view and therefore
      still beats the gate.** The cap then measures a body that is already
      materialized and refuses it (see ``_request_body.py``'s first rung), which
      is all that is left to do; a project that cares about the ordering for
      multipart must not parse the request in middleware.
    - A ``csrf_exempt`` mark reaches ``process_view`` only if it is on the
      callback the URL resolver holds. The mixin's ``as_view`` puts it there, and
      every Django view decorator carries it onward through ``functools.wraps`` -
      so ``ensure_csrf_cookie(View.as_view(...))`` keeps it, and so does a consumer
      subclass that overrides ``dispatch``. A hand-written wrapper function that
      calls the view without copying its ``__dict__`` does NOT, and loses the
      ORDERING - but keeps the protection: CSRF then runs twice, once as middleware
      and once here, and the second run short-circuits on
      ``csrf_processing_done``.
    - A rejection raised *inside* the protected continuation (the ``413`` and the
      ``400`` this module raises are translated by upstream's ``dispatch``, but an
      ``HTTPException`` from Strawberry itself unwinds through here) never reaches
      ``csrf_protect``'s ``_post_process_request``, so the inner
      ``process_response`` does not run on that path and the response carries no
      rotated CSRF cookie from *this* decorator. The project's global
      ``CsrfViewMiddleware.process_response`` still runs and still honours
      ``CSRF_COOKIE_NEEDS_UPDATE``, so a project with the middleware installed
      loses nothing; a project without it gets an error response with no cookie
      refresh. That is left as-is deliberately - papering over it would mean
      re-implementing part of the middleware chain to catch and re-raise, which is
      exactly the ownership this fix refuses to take.
    """
    return delegate(request, *args, **kwargs)


async def _async_run_after_csrf_check(
    request: HttpRequest,
    delegate: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """The async twin of :func:`_run_after_csrf_check` - see it for the whole contract.

    Needed as a separate function because ``csrf_protect`` branches on
    ``iscoroutinefunction(view_func)`` to decide whether to ``await`` the view, so
    the decorated callable must itself be a coroutine function for the async view
    to be handled correctly. Wrapping the sync one instead would hand a coroutine
    to ``process_response`` in place of a response. That branch exists in
    ``django/utils/decorators.py::make_middleware_decorator`` at the supported
    Django 5.2.0 floor as well as on current, and it was confirmed by EXECUTION at
    the floor - Python 3.10 / Django 5.2.0, both views, the full CSRF matrix and
    the untouched-parser witness - rather than by reading current and assuming
    backwards. ``examples/fakeshop/test_query/test_transport_api.py``'s async CSRF
    rows are the standing regression, and test-plan row 18 is the same file
    re-invoked at the floor.

    One consequence of ``decorator_from_middleware``'s shape is worth naming here
    rather than leaving for a reader to find: ``_pre_process_request`` is
    synchronous inside the async wrapper, so ``process_view``'s token check - and
    with it the ``request.POST`` read that parses a multipart body - happens on the
    event loop. That is acceptable *because* the body boundary already ran: the
    request has passed the declared-size gate, so the parse is bounded by the
    consumer's own cap and by Django's upload settings rather than by whatever the
    client sent. It is the same synchronous read Django's global middleware
    performed before this fix, moved behind the gate, which is precisely the
    mitigation.
    """
    return await delegate(request, *args, **kwargs)


#: The two continuations, wrapped once at import so each transport carries one
#: long-lived ``CsrfViewMiddleware`` instance rather than building one per
#: request.
_csrf_protected_run = csrf_protect(_run_after_csrf_check)
_csrf_protected_async_run = csrf_protect(_async_run_after_csrf_check)


class DjangoGraphQLView(_RequestBodyBoundaryMixin, GraphQLView):
    """The package's synchronous Django GraphQL view.

        A subclass of ``strawberry.django.views.GraphQLView`` that overrides exactly
        one thing - the raw request body: the cumulative cap, enforced at the top of
        ``run`` (spec-065 Decision 7), and the strict UTF-8 decode of the bytes that
        survive it (Decision 9). Everything else is inherited: every upstream
        ``as_view()`` keyword still applies and behaves identically - ``schema``,
        ``graphql_ide``, ``allow_queries_via_get``, and
        ``multipart_uploads_enabled`` - as do the ``get_context`` /
        ``get_root_value`` / ``process_result`` hooks a consumer may override. The
        one package keyword it adds is ``max_request_body_bytes=``, whose contract
        lives on ``_RequestBodyBoundaryMixin``.

        It exists as a package-owned symbol so the URLconf entry, the migration
        note, and the transport bounds the package owns on the HTTP path all name
        one class instead of forking between "upstream's view" and "the package's"
        (spec-065 Decision 6).

        The one other thing it overrides is upstream's ``request_adapter_class``,
        with a subclass that hands the raw body bytes to ``parse_json`` instead of
        decoding them inside a property. That is the sync half of the wire contract's
        independence from ``APPLY_UPSTREAM_PATCHES``; see
        :class:`_RawBodyRequestAdapter`.

    The ordering half of the body boundary - the ``csrf_exempt`` mark on the
        callback ``as_view`` returns - comes from the shared mixin, so it cannot
        diverge between the two transports; see
        ``_RequestBodyBoundaryMixin.as_view`` and :func:`_run_after_csrf_check`.
    """

    #: The package's own body source (see :class:`_RawBodyRequestAdapter`), so
    #: the strict decode below is reached on this transport whatever the
    #: upstream-patch setting says. The async twin needs no override: upstream's
    #: async adapter already hands over raw bytes.
    request_adapter_class = _RawBodyRequestAdapter

    def run(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """Enforce the request boundary, then run CSRF, then upstream's ``run``.

        The order is the contract (spec-065 Decision 7): nothing here may touch
        ``request.POST``, so an over-limit multipart request is refused before
        Django's multipart parser or any upload handler is entered, and every
        request that survives the boundary still passes Django's complete CSRF
        check before Strawberry parses anything.
        """
        self._enforce_request_boundary(request)
        return _csrf_protected_run(request, super().run, args, kwargs)

    def parse_multipart(self, request: SyncHTTPRequestAdapter) -> dict[str, str]:
        """Refuse lossily-decoded control documents, then delegate upstream.

        The narrowest possible seam for the check: it runs only when Strawberry is
        actually about to parse ``operations`` / ``map``, reads the form Django has
        already cached, and hands the same adapter to upstream so upstream stays
        the only reader of the multipart request. The split into a sync and an
        async override is upstream's own - ``parse_multipart`` is a coroutine on
        the async base view - so the policy itself lives once, on
        ``_RequestBodyBoundaryMixin``.
        """
        self._reject_lossy_multipart_control_fields(request.post_data)
        return super().parse_multipart(request)


class AsyncDjangoGraphQLView(_RequestBodyBoundaryMixin, AsyncGraphQLView):
    """The asynchronous twin, with an identical surface.

    The shape an ASGI deployment generally wants: ``AsyncGraphQLView.as_view``
    marks the returned view as a coroutine function, so Django dispatches it on
    the event loop rather than an executor thread. Resolvers then run in async
    context, which is why the migration note keeps ``DjangoGraphQLView`` as its
    default recommendation - adopting the async view is a decision about the
    consumer's own resolvers, not about the transport.

    It carries the same ``max_request_body_bytes=`` keyword, the same cap
    contract, and the same strict UTF-8 wire contract - all three from the one
    shared mixin, so the two transports cannot diverge. The cap check itself is
    synchronous on both because ``request.META`` is a dict and, once the cap has
    run, the bytes are either already in memory or bounded to at most
    ``limit + 1``: the unbounded synchronous disk read this view used to perform
    on the event loop (``len(request.body)``) is gone, which is the async half of
    what the bounded measurement bought.

    It carries the same ``csrf_exempt``-then-``csrf_protect`` ordering as its sync
    twin, through the async continuation ``csrf_protect`` awaits; see
    :func:`_run_after_csrf_check`.
    """

    async def run(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """Enforce the request boundary, then run CSRF, then upstream's ``run``.

        The sync twin's docstring is the contract; the only difference is the
        ``await``, and the only reason a second continuation function exists is
        that ``csrf_protect`` decides whether to await by inspecting the callable
        it wraps.
        """
        self._enforce_request_boundary(request)
        return await _csrf_protected_async_run(request, super().run, args, kwargs)

    async def parse_multipart(self, request: AsyncHTTPRequestAdapter) -> dict[str, str]:
        """Refuse lossily-decoded control documents, then delegate upstream.

        The async twin of the sync override; ``get_form_data`` is awaited twice
        across the two calls, which costs nothing because Django caches ``POST`` /
        ``FILES`` after the first parse.
        """
        form_data = await request.get_form_data()
        self._reject_lossy_multipart_control_fields(form_data.form)
        return await super().parse_multipart(request)
