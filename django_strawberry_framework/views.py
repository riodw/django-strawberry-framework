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
process, so both live on one mixin, ``_RequestBodyBoundaryMixin``: see it for the
contract, including the honest statement of what an application-level cap can and
cannot bound (Decision 8). The private-Django interaction the cap needs to measure
a body without materializing it is centralized in ``_request_body.py``, which this
module reads one boolean out of.

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

from typing import TYPE_CHECKING, Any

from cross_web import DjangoHTTPRequestAdapter, HTTPException
from strawberry.django.views import AsyncGraphQLView, GraphQLView

from django_strawberry_framework._request_body import body_exceeds_limit
from django_strawberry_framework.conf import max_request_body_bytes_setting
from django_strawberry_framework.exceptions import ConfigurationError, describe_value

if TYPE_CHECKING:
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
       (spec-065 Decision 7), enforced from ``run`` on both views.
    2. **How they become text** - the strict UTF-8 wire contract (Decision 9),
       enforced by overriding ``parse_json``.

    They belong together because they are the same boundary read twice: the cap
    decides which bytes reach the parse, and the parse decides how those exact
    bytes are decoded. Both are permanent package policy that a consumer opts
    into by mounting a package view, and neither depends on an upstream defect
    or on ``APPLY_UPSTREAM_PATCHES`` (see ``parse_json`` for why that ownership
    is load-bearing rather than tidy).

    Sits first in each view's bases so ``max_request_body_bytes`` is already a
    class attribute by the time Django's ``View.as_view`` runs its ``hasattr``
    keyword guard, so ``parse_json`` resolves to this policy ahead of anything
    upstream defines, and so a consumer subclass can override any part.

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

    **Multipart.** Bounded by the declared-size gate plus Django's own
    ``MultiPartParser``, and nothing else. The body is deliberately never
    materialized for a multipart request - reading it would pull the whole
    payload into memory and defeat Django's streaming upload handlers, breaking
    the ``Upload``-scalar path this package ships. Per-file count, per-file
    size, and aggregate size are NOT bounded here (audit S4).

    **GET.** A no-op: the view reads no body on GET. The ``variables`` /
    ``extensions`` query-param size is a separate concern, and
    ``_strawberry_patches.py::_patched_parse_query_params`` already shields
    those parses.

    **The honest boundary** (spec-065 Decisions 7 and 8). What this guarantees
    is that the application never parses, allocates a document from, or executes
    a schema against an over-limit body, that it never allocates or reads more
    than ``limit + 1`` bytes of one - except where an earlier middleware already
    materialized it, the one shape named at the end of this paragraph - and that
    the rejection is a tested ``413``.
    What it cannot guarantee is that the bytes were never received:
    ``django.core.handlers.asgi.ASGIHandler.read_body`` has already drained the
    entire request into a spooled temporary file - rolling to disk past
    ``FILE_UPLOAD_MAX_MEMORY_SIZE`` - before any application cap can run. A
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

    def _enforce_request_body_limit(self, request: HttpRequest) -> None:
        """Raise ``HTTPException(413)`` when the request body exceeds the cap.

        Called at the top of ``run`` on both views, so the raise lands inside
        upstream's ``dispatch`` ``except HTTPException`` and comes out as the
        ``413`` ``text/plain`` response the spec pins - the same translation the
        package's malformed-body ``400`` already rides. Resolving the cap first
        means a misconfigured mount fails loud on every request, GET included.
        """
        limit = _resolved_max_request_body_bytes(self.max_request_body_bytes)
        if limit is None or request.method == "GET":
            return
        declared = _declared_content_length(request)
        if declared is not None and declared > limit:
            raise HTTPException(413, _BODY_LIMIT_REASON)
        if request.content_type == _MULTIPART_CONTENT_TYPE:
            return
        if body_exceeds_limit(request, limit):
            raise HTTPException(413, _BODY_LIMIT_REASON)

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
    """

    #: The package's own body source (see :class:`_RawBodyRequestAdapter`), so
    #: the strict decode below is reached on this transport whatever the
    #: upstream-patch setting says. The async twin needs no override: upstream's
    #: async adapter already hands over raw bytes.
    request_adapter_class = _RawBodyRequestAdapter

    def run(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """Enforce the body cap, then delegate to upstream's ``run`` unchanged."""
        self._enforce_request_body_limit(request)
        return super().run(request, *args, **kwargs)


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
    """

    async def run(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """Enforce the body cap, then delegate to upstream's ``run`` unchanged."""
        self._enforce_request_body_limit(request)
        return await super().run(request, *args, **kwargs)
