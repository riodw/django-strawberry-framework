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

The module also owns the cumulative request-body cap the package enforces on
this path (spec-065 Decision 7) - see ``_RequestBodyLimitMixin`` for the
contract, including the honest statement of what an application-level cap can
and cannot bound (Decision 8).

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

from cross_web import HTTPException
from strawberry.django.views import AsyncGraphQLView, GraphQLView

from django_strawberry_framework.conf import max_request_body_bytes_setting
from django_strawberry_framework.exceptions import ConfigurationError

if TYPE_CHECKING:
    from django.http import HttpRequest

__all__ = ("AsyncDjangoGraphQLView", "DjangoGraphQLView")


#: The wire reason for an over-limit body, verbatim from spec-065's Error
#: shapes. Named once so the package tier can import the exact bytes the live
#: tier reads off the response.
_BODY_LIMIT_REASON = "Request body exceeded the configured GraphQL request-body limit."

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
    """
    if value is None:
        value = max_request_body_bytes_setting()
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigurationError(
            f"max_request_body_bytes must be a positive int of bytes or None to disable "
            f"the package request-body cap; got {type(value).__name__} {value!r}.",
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


class _RequestBodyLimitMixin:
    """The cumulative request-body cap shared by both package views.

    Sits first in each view's bases so ``max_request_body_bytes`` is already a
    class attribute by the time Django's ``View.as_view`` runs its ``hasattr``
    keyword guard, and so a consumer subclass can override either half.

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
    a schema against an over-limit body, and that the rejection is a tested
    ``413``. What it cannot guarantee is that the bytes were never received:
    ``django.core.handlers.asgi.ASGIHandler.read_body`` has already drained the
    entire request into a spooled temporary file - rolling to disk past
    ``FILE_UPLOAD_MAX_MEMORY_SIZE`` - before any application cap can run. A
    reverse-proxy / ASGI-server cap is therefore a CO-REQUIREMENT of this one,
    not an alternative to it; this cap bounds what the application *processes*,
    never what the server *accepts*.
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
        if len(request.body) > limit:
            raise HTTPException(413, _BODY_LIMIT_REASON)


class DjangoGraphQLView(_RequestBodyLimitMixin, GraphQLView):
    """The package's synchronous Django GraphQL view.

    A subclass of ``strawberry.django.views.GraphQLView`` that overrides exactly
    one behavior - the cumulative request-body cap, which it enforces at the top
    of ``run`` (spec-065 Decision 7). Everything else is inherited: every
    upstream ``as_view()`` keyword still applies and behaves identically -
    ``schema``, ``graphql_ide``, ``allow_queries_via_get``, and
    ``multipart_uploads_enabled`` - as do the ``get_context`` /
    ``get_root_value`` / ``process_result`` hooks a consumer may override. The
    one package keyword it adds is ``max_request_body_bytes=``, whose contract
    lives on ``_RequestBodyLimitMixin``.

    It exists as a package-owned symbol so the URLconf entry, the migration
    note, and the transport bounds the package owns on the HTTP path all name
    one class instead of forking between "upstream's view" and "the package's"
    (spec-065 Decision 6).
    """

    def run(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """Enforce the body cap, then delegate to upstream's ``run`` unchanged."""
        self._enforce_request_body_limit(request)
        return super().run(request, *args, **kwargs)


class AsyncDjangoGraphQLView(_RequestBodyLimitMixin, AsyncGraphQLView):
    """The asynchronous twin, with an identical surface.

    The shape an ASGI deployment generally wants: ``AsyncGraphQLView.as_view``
    marks the returned view as a coroutine function, so Django dispatches it on
    the event loop rather than an executor thread. Resolvers then run in async
    context, which is why the migration note keeps ``DjangoGraphQLView`` as its
    default recommendation - adopting the async view is a decision about the
    consumer's own resolvers, not about the transport.

    It carries the same ``max_request_body_bytes=`` keyword and the same cap
    contract; the check itself is synchronous on both transports because
    ``request.META`` is a dict and upstream's own async adapter reads
    ``HttpRequest.body`` synchronously too.
    """

    async def run(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        """Enforce the body cap, then delegate to upstream's ``run`` unchanged."""
        self._enforce_request_body_limit(request)
        return await super().run(request, *args, **kwargs)
