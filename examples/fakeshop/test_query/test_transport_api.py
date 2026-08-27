"""Live ``/graphql/`` transport-boundary acceptance tests (spec-046).

The HTTP-boundary tier: every proof that Django's real request lifecycle
executes on the package's GraphQL HTTP route now that ``routers.py`` no longer
serves HTTP at all (Decision 2). Fakeshop mounts
``django_strawberry_framework.views.DjangoGraphQLView`` at ``/graphql/``
(Decision 6), so these are proofs about the shipped package view rather than
about a package reimplementation of Django's boundary.

Test plan rows 1-7 land here: a project middleware sentinel on the GraphQL route
(row 1), ``SecurityMiddleware``'s configured headers including HSTS (row 2), a
hostile ``Host`` rejected before schema execution (row 3), the three CSRF
directions on a cookie-authenticated mutation (row 4), ``Vary: Cookie`` on an
authenticated GET (row 5), Django's own exact routing policy including the
``APPEND_SLASH`` redirect (row 6), and ``graphql_ide=None`` /
``allow_queries_via_get=False`` on a second mount of the package view (row 7).
An async probe adds the ``AsyncDjangoGraphQLView`` colour of row 1 + row 2.
One further mount proves ``docs/README.md``'s combined production-profile
recipe (row 7's two knobs plus introspection disabled through
``AddValidationRules``) as a single unit over the real fakeshop schema.

Test plan rows 13-17 - the whole body-cap matrix (Decision 7) - land here
too, against three more mounts of the package view that differ only in their
``max_request_body_bytes``: the below / at / above boundary trio, what an absent
or understated ``Content-Length`` can and cannot do on each transport, a
cumulative multi-fragment body, malformed JSON on both sides of the cap,
multipart, the parse-and-execution witnesses, which of the two ceilings fired,
and the three precedence rungs. Row 18 (the py3.10 / Django 5.2.16 floor) is a
separately-invoked run of this same file, not a separate row.

Test plan rows 19 / 22 / 23 add one more async row. The strict UTF-8
wire contract (Decision 9) is enforced in
``views.py::_RequestBodyBoundaryMixin.parse_json``, which both views inherit, so
the async transport must reject UTF-16 and a leading UTF-8 BOM exactly as the sync
``/graphql/`` rows in ``test_products_api.py`` do. It lives here rather than beside
those rows because this module already owns the ``/async-graphql/`` mount and the
``AsyncClient`` scaffolding it needs.

The final section pins the strict UTF-8 wire contract as package policy on the
*view*, not as one of the upstream-bug patches, so it is asserted on both
transports with ``APPLY_UPSTREAM_PATCHES = {"strawberry": False}`` in effect -
and the workaround the switch really does own is asserted to be genuinely off in
the same state, so the ownership split cannot be satisfied by moving everything
somewhere ungated. Its last rows take the switch off entirely
(``APPLY_UPSTREAM_PATCHES = False``, both patch modules un-installed) - the state
in which the sync transport used to answer ``500``. It is now the same controlled
``400``, and one row reads all four answers across two mounts
and two patch states so that constancy is attributable to the package view rather
than to a patch that was quietly still installed. One further row moves the
``cross_web`` member of that switch alone, against Strawberry's own mount, which is
the only place the patch this package ships for that mount still has an observable
value - and is therefore its standing retirement diagnostic.

Three of those rows need a body shape neither ``Client`` nor ``AsyncClient`` can
present, so they drive Django's own ``ASGIHandler`` in-process through
``_asgi_post`` - see that helper for why, and for the ``receive`` contract it
depends on. The package-tier half of the cap (the precedence ladder as a pure
function, the validation matrix, and the ``request._body``-was-never-touched
witnesses) is in ``tests/test_views.py``.

Most rows drive a bare ``django.test.Client`` rather than the shared
``graphql_client.py`` helpers, because their subject IS the raw request envelope
- a hostile ``Host`` header, ``secure=True``, ``enforce_csrf_checks=True``, an
``AsyncClient`` - which is the documented raw-envelope exemption in
``README.md``. The two rows whose subject is an ordinary GraphQL response still
go through the shared helpers.
"""

import asyncio
import contextlib
import json

import pytest
import strawberry
from apps.products import models
from apps.products.services import create_users, seed_data
from cross_web import DjangoHTTPRequestAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadhandler import MemoryFileUploadHandler
from django.core.handlers.asgi import ASGIHandler
from django.http import HttpResponseForbidden
from django.middleware.csrf import CsrfViewMiddleware, get_token
from django.test import AsyncClient, Client, RequestFactory, override_settings
from django.urls import include, path, resolve
from graphql import NoSchemaIntrospectionCustomRule
from graphql_client import assert_graphql_data, post_graphql
from strawberry.django.views import GraphQLView as UpstreamGraphQLView
from strawberry.extensions import AddValidationRules
from strawberry.http.base import BaseView

from django_strawberry_framework import DjangoSchema, strawberry_config
from django_strawberry_framework import _cross_web_patches as cross_web_patches
from django_strawberry_framework import _strawberry_patches as strawberry_patches
from django_strawberry_framework._boundary_ordering import _BOUNDARY_MARKER
from django_strawberry_framework.middleware.request_body import _package_view_instance
from django_strawberry_framework.views import (
    _BODY_LIMIT_REASON,
    AsyncDjangoGraphQLView,
    DjangoGraphQLView,
)

# ---------------------------------------------------------------------------
# Operations. ``__typename`` is deliberately DB-free so a row whose subject is a
# header or a status code never depends on seeded data (and so the async probe
# never touches the ORM from the event loop). The catalog read and the category
# write are shipped fakeshop surfaces already driven by sibling live suites.
# ---------------------------------------------------------------------------

_TYPENAME = "{ __typename }"
_ITEMS = "{ allItems(first: 1) { edges { node { name } } } }"
_ME = "{ me { username } }"
_CREATE_CATEGORY = (
    "mutation($d: CategoryInput!) { createCategory(data: $d) { "
    "node { name } errors { field messages } } }"
)


# ---------------------------------------------------------------------------
# Row-1 scaffolding: a project middleware referenced from ``MIDDLEWARE`` by its
# dotted path. Importable because pytest has already put this module in
# ``sys.modules`` under ``__name__`` - the same mechanism the Probe URLconf below
# relies on for ``ROOT_URLCONF=__name__``.
# ---------------------------------------------------------------------------

_SENTINEL_HEADER = "X-Fakeshop-Transport-Probe"
_MIDDLEWARE_PATHS: list[str] = []


class _SentinelMiddleware:
    """Record the request path and stamp a sentinel header on the response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _MIDDLEWARE_PATHS.append(request.path)
        response = self.get_response(request)
        response[_SENTINEL_HEADER] = "1"
        return response


class _LatinOneEncodingMiddleware:
    """Assign ``request.encoding``, which is Django's documented per-request override.

    The deployment the encoding gate exists for, as one line of consumer
    middleware - the exact shape its docstring cites as the reason it consults
    ``request.encoding`` at all. ``HttpRequest.encoding``'s setter is public API and
    ``HttpRequest.parse_file_upload`` hands ``MultiPartParser`` nothing but this
    value, so a project can legitimately install this and every multipart form on
    every route is then decoded as Latin-1 - **including** one whose
    ``Content-Type`` declared ``charset=utf-8``, because Django never re-reads
    ``content_params`` at parse time.

    Mounted last (innermost) by :func:`_with_a_middleware_that_sets_the_encoding`,
    so it runs immediately before the view, which is the hostile ordering: the
    assignment lands after the declaration was promoted and cannot be seen from the
    request line.
    """

    encoding = "iso-8859-1"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.encoding = self.encoding
        return self.get_response(request)


def _with_a_middleware_that_sets_the_encoding():
    """``override_settings`` adding :class:`_LatinOneEncodingMiddleware` innermost.

    Derived from the project's real ``MIDDLEWARE`` rather than a hand-written list,
    the same way ``_without_the_global_csrf_middleware`` is, so the row adds exactly
    one entry and keeps fakeshop's session, auth, CSRF and security middleware in
    place - the deployment is "a project that also does this", not "a project with
    nothing else".
    """
    entry = f"{__name__}._LatinOneEncodingMiddleware"
    assert entry not in settings.MIDDLEWARE, settings.MIDDLEWARE
    return override_settings(MIDDLEWARE=[*settings.MIDDLEWARE, entry])


# ---------------------------------------------------------------------------
# Probe URLconf (inert unless a test overrides ``ROOT_URLCONF`` to ``__name__``):
# extra mounts of the package views - and, for one attribution row, of
# Strawberry's own - alongside the real fakeshop URLconf.
# Every probe view builds its view at REQUEST time, mirroring
# ``test_client_api.py::_alt_graphql_view`` - resolving late keeps the probe
# pointed at the schema the per-test reload fixture just rebuilt.
# ---------------------------------------------------------------------------


def _ide_off_view(request, *args, **kwargs):
    """The package view with the IDE and GET queries both turned off (row 7)."""
    from config.schema import schema

    view = DjangoGraphQLView.as_view(
        schema=schema,
        graphql_ide=None,
        allow_queries_via_get=False,
    )
    return view(request, *args, **kwargs)


def _production_profile_view(request, *args, **kwargs):
    """The documented production mount, assembled exactly as the guide's recipe.

    ``docs/README.md``'s "Production security profile" section tells a deployment
    to mount the package view with the IDE off, GET queries off, and schema
    introspection disabled through ``AddValidationRules``. This probe IS that
    recipe over the real fakeshop ``Query`` / ``Mutation`` surface, rebuilt per
    request like every other probe so it tracks the per-test schema reload.
    """
    from config.schema import Mutation, Query

    schema = DjangoSchema(
        query=Query,
        mutation=Mutation,
        config=strawberry_config(),
        # A FACTORY, not an instance: Strawberry deprecates extension instances in
        # ``extensions=`` (one instance would be shared across every request), and
        # this suite runs under ``-W error``. The guide's recipe says the same.
        extensions=[lambda: AddValidationRules([NoSchemaIntrospectionCustomRule])],
    )
    view = DjangoGraphQLView.as_view(
        schema=schema,
        graphql_ide=None,
        allow_queries_via_get=False,
    )
    return view(request, *args, **kwargs)


async def _async_graphql_view(request, *args, **kwargs):
    """The async twin, mounted so Django dispatches it on the event loop."""
    from config.schema import schema

    view = AsyncDjangoGraphQLView.as_view(schema=schema)
    return await view(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Body-cap scaffolding: three more mounts of the package view, differing only in
# their ``max_request_body_bytes``. ``_TINY_CAP`` is small enough that a
# hand-sized operation crosses it, so no row needs a megabyte-scale payload
# except the one whose subject IS the 1 MiB default.
# ---------------------------------------------------------------------------

_TINY_CAP = 256
_ROOMY_CAP = 8 * 1024 * 1024

#: Every ``parse_json`` call the spy mount saw, newest last. The row-15 witness:
#: a ``413`` that leaves this empty is a ``413`` raised before any parse.
_PARSE_CALLS: list[str | bytes] = []


class _ParseSpyView(DjangoGraphQLView):
    """The package view with a ``parse_json`` recorder bolted on, and nothing else changed.

    Subclassing rather than monkeypatching keeps the recorder scoped to one
    mount, so the surrounding suite's own posts never pollute the witness. The
    override delegates through ``super()``, so the whole shipped chain still runs
    behind it - the package's strict UTF-8 wire contract
    (``views.py::_RequestBodyBoundaryMixin.parse_json``) and then the
    malformed-body hardening (``_strawberry_patches.py::_patched_parse_json``) -
    and the under-cap control behaves exactly like the real mount. Recording
    before the delegation is deliberate: the witness has to be the bytes as they
    arrived, so a ``413`` that leaves the list empty proves the cap ran ahead of
    the entire parse chain rather than merely ahead of the JSON decode.
    """

    def parse_json(self, data):
        _PARSE_CALLS.append(data)
        return super().parse_json(data)


@strawberry.type
class _SetupProbeQuery:
    """The smallest executable schema for the setup-lifecycle boundary probe."""

    @strawberry.field
    def ping(self) -> str:
        return "pong"


_SETUP_PROBE_SCHEMA = strawberry.Schema(query=_SetupProbeQuery)
_SETUP_CALLS: list[str] = []


class _SetupLimitedView(DjangoGraphQLView):
    """Derive the mount's request cap from Django's per-request setup lifecycle."""

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        _SETUP_CALLS.append(request.path)
        self.max_request_body_bytes = kwargs["limit"]


_SETUP_LIMITED_CALLBACK = _SetupLimitedView.as_view(schema=_SETUP_PROBE_SCHEMA)


def _carrying_the_packages_csrf_mark(view_class):
    """Copy the package view's ``csrf_exempt`` mark - and only that one - onto a probe wrapper.

    Every probe mount in this file resolves its view per request, so the callback
    the URL resolver hands ``CsrfViewMiddleware.process_view`` is the wrapper
    function here rather than the one ``as_view`` returned - and ``process_view``
    reads ``csrf_exempt`` off *that* callback. A real mount needs nothing: ``as_view``
    stamps **two** ordering marks on its callback, the withdrawable exemption and the
    boundary marker the chain middleware recognizes, and every Django view decorator
    carries both onward through ``functools.wraps`` (which is how fakeshop's own
    ``ensure_csrf_cookie`` mount at ``/graphql/`` keeps them). A bare wrapper defined
    here carries neither, so it copies the exemption - otherwise the probe mount, not
    the package, is what loses the ordering, and a row would be measuring its own
    scaffolding.

    Copying ONLY the exemption is deliberate, and it is what these rows are for.
    Without the boundary marker the chain middleware declines this callback, so every
    probe mount here exercises the **view-local fallback** even though fakeshop's
    ``MIDDLEWARE`` installs the boundary middleware. The declined-callback contract is
    exactly that: the CSRF class degrades to Django's stock one, while the ordering and
    the cap do not. Fakeshop's real ``/graphql/`` mount keeps both marks and therefore
    exercises the chain-supplied arrangement, so the two halves of Decision 18 are both
    covered live, by construction rather than by an ``override_settings`` toggle.

    The value is READ FROM the package rather than hardcoded, so this raises at
    import the day the package stops setting it. The load-bearing ordering evidence
    is still the row that runs against fakeshop's real ``/graphql/`` mount, where no
    scaffolding is involved at all.
    """
    mark = view_class.as_view().csrf_exempt

    def decorate(view):
        view.csrf_exempt = mark
        return view

    return decorate


def _capped_view(view_class, limit, *, uploads=False):
    """A request-time-resolving mount of ``view_class`` with the cap pinned.

    Resolving the schema per request mirrors ``_ide_off_view`` above: it keeps
    every probe mount pointed at the schema the per-test reload fixture just
    rebuilt instead of one captured at import.

    ``uploads=True`` turns on upstream's ``multipart_uploads_enabled``, which the
    multipart wire-contract rows need: with it off, upstream refuses every
    ``multipart/form-data`` request as an unsupported content type before
    ``operations`` is ever read, so a mount without it cannot show what the
    package does to a control document it DOES parse.
    """

    @_carrying_the_packages_csrf_mark(view_class)
    def view(request, *args, **kwargs):
        from config.schema import schema

        built = view_class.as_view(
            schema=schema,
            max_request_body_bytes=limit,
            multipart_uploads_enabled=uploads,
        )
        return built(request, *args, **kwargs)

    return view


@_carrying_the_packages_csrf_mark(AsyncDjangoGraphQLView)
async def _async_capped_multipart_view(request, *args, **kwargs):
    """The async view with uploads on and a roomy cap, for the async wire rows.

    Spelled out rather than produced by ``_capped_view`` for the same reason
    ``_async_graphql_view`` is: the ``await`` is the difference. Fakeshop's own
    ``/graphql/`` is the sync half of every multipart row below (it already mounts
    the package view with ``multipart_uploads_enabled=True``), so this is the one
    mount the async half needs.
    """
    from config.schema import schema

    view = AsyncDjangoGraphQLView.as_view(
        schema=schema,
        max_request_body_bytes=_ROOMY_CAP,
        multipart_uploads_enabled=True,
    )
    return await view(request, *args, **kwargs)


async def _async_cap_tiny_view(request, *args, **kwargs):
    """The async twin under the tiny cap, so the ``async def run`` override is proven live.

    Spelled out rather than produced by ``_capped_view`` for the same reason
    ``_async_graphql_view`` is: the ``await`` is the difference, and one mount
    needs it.
    """
    from config.schema import schema

    view = AsyncDjangoGraphQLView.as_view(schema=schema, max_request_body_bytes=_TINY_CAP)
    return await view(request, *args, **kwargs)


@_carrying_the_packages_csrf_mark(AsyncDjangoGraphQLView)
async def _async_cap_tiny_multipart_view(request, *args, **kwargs):
    """The async twin under the tiny cap with uploads on, for the ordering rows.

    The async colour of ``multipart-tiny/``: an over-cap multipart request has to
    be refused before Django's parser on the event loop too, and the under-cap
    control has to reach the schema, which needs uploads enabled.
    """
    from config.schema import schema

    view = AsyncDjangoGraphQLView.as_view(
        schema=schema,
        max_request_body_bytes=_TINY_CAP,
        multipart_uploads_enabled=True,
    )
    return await view(request, *args, **kwargs)


def _upstream_graphql_view(request, *args, **kwargs):
    """Strawberry's OWN sync view, mounted as the negative witness for the patch gate.

    Not a package surface and never recommended - it exists so one row can show
    what the ``APPLY_UPSTREAM_PATCHES`` switch actually costs the consumer it is
    scoped to. With both patch halves off, an undecodable body on this mount is
    the unhandled ``500`` that IS the upstream defect, while the same bytes on the
    package mount are a controlled ``400``: the difference is attributable to the
    package view (its own request adapter and its own ``parse_json``) rather than
    to a patch that was still quietly installed.
    """
    from config.schema import schema

    view = UpstreamGraphQLView.as_view(schema=schema)
    return view(request, *args, **kwargs)


urlpatterns = [
    path("", include("config.urls")),
    path("ide-off/", _ide_off_view),
    path("production-profile/", _production_profile_view),
    path("async-graphql/", _async_graphql_view),
    path("cap-tiny/", _capped_view(DjangoGraphQLView, _TINY_CAP)),
    path("cap-spy/", _capped_view(_ParseSpyView, _TINY_CAP)),
    path("cap-off/", _capped_view(DjangoGraphQLView, _ROOMY_CAP)),
    path("multipart-tiny/", _capped_view(DjangoGraphQLView, _TINY_CAP, uploads=True)),
    path("async-multipart-tiny/", _async_cap_tiny_multipart_view),
    path("async-multipart/", _async_capped_multipart_view),
    path("async-cap-tiny/", _async_cap_tiny_view),
    path("setup-limited/<int:limit>/", _SETUP_LIMITED_CALLBACK),
    path("upstream-graphql/", _upstream_graphql_view),
]


def _post_bytes(client, raw, path="/graphql/", **extra):
    """POST an exact byte string, so a row can own the length or a hostile header."""
    return client.post(path, data=raw, content_type="application/json", **extra)


def _post(client, query, path="/graphql/", variables=None, **extra):
    """Raw JSON GraphQL POST, so a row can own the client, the host, or the scheme."""
    body = {"query": query}
    if variables is not None:
        body["variables"] = variables
    return _post_bytes(client, json.dumps(body), path=path, **extra)


def _sized_body(size, query=_TYPENAME, variables=None):
    """A valid GraphQL request body of EXACTLY ``size`` bytes.

    The padding key is inert - Strawberry ignores unknown top-level members - so
    the operation still executes when the body is under the cap. ``"y"`` needs no
    JSON escaping, so one pad character is one byte and the arithmetic is exact,
    which is what lets the below / at / above trio pin ``>`` rather than ``>=``.
    """
    body = {"query": query, "pad": ""}
    if variables is not None:
        body["variables"] = variables
    pad = size - len(json.dumps(body))
    assert pad >= 0, f"size {size} is below the {len(json.dumps(body))}-byte envelope"
    body["pad"] = "y" * pad
    raw = json.dumps(body)
    assert len(raw) == size
    return raw


def _user_who_can_add_categories():
    """A ``view_category_1`` actor holding ``add_category``, ready to authorize a write.

    No ``create_users`` user holds a write permission by default and ``staff_1``
    is ``is_staff`` but not a superuser, so a row driving ``createCategory`` has
    to grant the permission explicitly - the same way ``test_products_api.py``
    does - or it fails on authorization rather than on its own subject.
    """
    from django.contrib.auth.models import Permission

    create_users(1)
    user_model = get_user_model()
    user = user_model.objects.get(username="view_category_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_category", content_type__app_label="products"),
    )
    return user_model.objects.get(pk=user.pk)  # drop the stale per-request perm cache


def _assert_body_limit_response(response):
    """The package's own ``413``: the exact reason, ``text/plain``, no envelope.

    Pinning the literal reason is what distinguishes the package's ceiling from
    Django's ``DATA_UPLOAD_MAX_MEMORY_SIZE`` rejection (row 16) - both are
    correct outcomes, and a bare status assertion could not tell them apart.
    """
    assert response.status_code == 413
    assert response.headers["Content-Type"].startswith("text/plain")
    assert response.content == _BODY_LIMIT_REASON.encode()
    _assert_no_graphql_envelope(response)


def _asgi_post(path_, fragments, extra_headers=()):
    """Drive Django's own ``ASGIHandler`` in-process; return ``(status, headers, body)``.

    Neither ``django.test.Client`` nor ``AsyncClient`` can present the body
    shapes test-plan row 13 requires: both derive ``CONTENT_LENGTH`` from the
    payload, both build the request object directly, and ``AsyncClientHandler``
    wraps the whole body in one ``LimitedStream`` without ever calling
    ``ASGIHandler.read_body``. So an absent ``Content-Length``, an understated
    one, and a multi-fragment body are only reachable through Django's real ASGI
    handler - which is what this drives, against fakeshop's actual settings,
    ``MIDDLEWARE``, URLconf, and mounted view.

    The ``receive`` shape is load-bearing: after the queued fragments it awaits
    something that never resolves, and ``ASGIHandler.handle`` cancels its
    ``listen_for_disconnect`` task once the response is sent. Returning
    ``http.disconnect`` instead would abort the request before the view answered.

    Unlike ``django.test.Client``, this is the real handler with the real
    middleware chain, so ``CsrfViewMiddleware`` enforces for real - hence the
    minted ``csrftoken`` cookie echoed in the ``X-CSRFToken`` header, which is
    exactly the round trip a browser (and Strawberry's own GraphiQL) makes. That
    is stronger than exempting the mount: these rows pass Django's CSRF check
    legitimately, so a ``413`` they report is unambiguously the view's.
    """
    handler = ASGIHandler()
    csrf_token = get_token(RequestFactory().get(path_))
    scope = {
        "type": "http",
        "http_version": "1.1",
        "asgi": {"version": "3.0"},
        "method": "POST",
        "scheme": "http",
        "path": path_,
        "raw_path": path_.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"cookie", f"csrftoken={csrf_token}".encode()),
            (b"x-csrftoken", csrf_token.encode()),
            *extra_headers,
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    pending = [
        {"type": "http.request", "body": fragment, "more_body": index < len(fragments) - 1}
        for index, fragment in enumerate(fragments)
    ]
    sent = []

    async def receive():
        if pending:
            return pending.pop(0)
        await asyncio.Event().wait()
        raise AssertionError("unreachable: the handler cancels this await")  # pragma: no cover

    async def send(message):
        sent.append(message)

    async def drive():
        await handler(scope, receive, send)

    asyncio.run(drive())

    start = next(message for message in sent if message["type"] == "http.response.start")
    body = b"".join(
        message.get("body", b"") for message in sent if message["type"] == "http.response.body"
    )
    headers = {name.decode(): value.decode() for name, value in start.get("headers", [])}
    return start["status"], headers, body


# ---------------------------------------------------------------------------
# Wire-contract and cap-ordering scaffolding: hand-built multipart requests, a
# CSRF token round trip, and an upload-handler sentinel.
#
# Neither ``Client.post`` nor ``AsyncClient.post`` can present these bodies:
# both run the payload through ``_encode_data``, which re-encodes it with the
# charset parsed off the declared content type - so a malformed UTF-8 byte or an
# explicit ``charset=iso-8859-1`` raises inside the test client instead of
# reaching the endpoint. ``generic`` puts the bytes and the header on the wire
# untouched, which is the whole point of a wire-contract row.
# ---------------------------------------------------------------------------

_MULTIPART_BOUNDARY = "BoUnDaRyFoRtHeWiReRoWs"

#: Every upload-handler and parser call the sentinel handler saw, newest last.
#: The ordering witness: a ``413`` that leaves this EMPTY is a ``413`` raised
#: before Django's multipart parser ran at all. A status alone cannot say that.
_UPLOAD_EVENTS: list[str] = []


class _RecordingUploadHandler(MemoryFileUploadHandler):
    """Django's own in-memory upload handler, with a call recorder in front of it.

    Installed through ``FILE_UPLOAD_HANDLERS``, so it is reached the way a
    project's handlers are reached - lazily, from
    ``HttpRequest.parse_file_upload`` - and it records the two events that prove
    Django's multipart machinery ran: ``handle_raw_input``, which
    ``MultiPartParser.parse`` calls on every handler for **any** multipart body
    (fields included, files or not), and ``new_file`` /
    ``receive_data_chunk``, which are called only for a file payload.

    Subclassing Django's handler rather than faking one keeps the accepted
    direction honest: files really are streamed through the normal handler chain,
    and the row that proves it is asserting about the shipped path.

    Every override takes ``*args, **kwargs`` deliberately - the hook signatures
    carry Django's own ``META`` spelling, which is not a name this repo's lint
    allows a parameter to have, and forwarding blind also keeps the recorder
    correct if a supported Django adds a hook argument.
    """

    def handle_raw_input(self, *args, **kwargs):
        _UPLOAD_EVENTS.append("handle_raw_input")
        return super().handle_raw_input(*args, **kwargs)

    def new_file(self, *args, **kwargs):
        _UPLOAD_EVENTS.append("new_file")
        return super().new_file(*args, **kwargs)

    def receive_data_chunk(self, *args, **kwargs):
        _UPLOAD_EVENTS.append("receive_data_chunk")
        return super().receive_data_chunk(*args, **kwargs)


def _recording_upload_handlers():
    """``override_settings`` for the sentinel handler, by dotted path.

    The path resolves because pytest has already put this module in
    ``sys.modules`` under ``__name__`` - the same mechanism the probe URLconf
    relies on.
    """
    return override_settings(FILE_UPLOAD_HANDLERS=[f"{__name__}._RecordingUploadHandler"])


def _csrf_failure_probe(request, reason=""):
    """A custom ``CSRF_FAILURE_VIEW``, so one row can prove the setting still fires."""
    return HttpResponseForbidden(b"probe-csrf-failure")


def _csrf_token(path="/graphql/"):
    """A usable CSRF token, minted the way Django mints one for a real client.

    The same round trip ``_asgi_post`` performs: the value goes into the
    ``csrftoken`` cookie AND the ``X-CSRFToken`` header, which is what a browser
    (and Strawberry's own GraphiQL) sends.
    """
    return get_token(RequestFactory().get(path))


def _multipart_content_type(charset=None):
    """The declared ``Content-Type`` for a hand-built multipart body."""
    content_type = f"multipart/form-data; boundary={_MULTIPART_BOUNDARY}"
    if charset is not None:
        content_type = f"{content_type}; charset={charset}"
    return content_type


def _multipart_bytes(fields, files=()):
    """A multipart body over exactly the given raw bytes.

    ``fields`` and ``files`` are ``(name, raw)`` / ``(name, filename, raw)``
    pairs whose payloads are **bytes**, never text: a row's whole subject can be
    one undecodable byte, so nothing here may encode on the caller's behalf. No
    per-part ``charset`` is ever declared, because Django honours one only in its
    FILE branch - a per-part charset on ``operations`` is ignored, which is
    precisely why the top-level declaration is the one the package checks.
    """
    parts = []
    for name, raw in fields:
        disposition = f'Content-Disposition: form-data; name="{name}"'
        parts.append(
            f"--{_MULTIPART_BOUNDARY}\r\n{disposition}\r\n\r\n".encode() + raw + b"\r\n",
        )
    for name, filename, raw in files:
        disposition = f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'
        parts.append(
            f"--{_MULTIPART_BOUNDARY}\r\n{disposition}\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n".encode()
            + raw
            + b"\r\n",
        )
    parts.append(f"--{_MULTIPART_BOUNDARY}--\r\n".encode())
    return b"".join(parts)


def _post_multipart(
    client,
    path,
    fields,
    *,
    files=(),
    charset=None,
    token=None,
    send_header=True,
    **extra,
):
    """POST a hand-built multipart body; return whatever the client returns.

    Sync callers get a response, async callers get an awaitable - both clients
    inherit ``generic`` from their request factory, so one helper serves both
    transports and the rows stay symmetric.

    ``token`` installs the CSRF cookie and, unless ``send_header=False``, the
    ``X-CSRFToken`` header - the shape ``Client(enforce_csrf_checks=True)``
    accepts. Omitting the token is how the missing-token direction is expressed,
    and dropping only the header is how the form-token direction is: the cookie
    still has to be there, because a token in the form is checked against it.

    Extra request headers ride the ``headers=`` mapping rather than WSGI-style
    ``HTTP_*`` keyword arguments, because that is the only spelling both clients
    accept: ``AsyncRequestFactory`` treats ``**extra`` as ASGI *scope* entries and
    would put ``HTTP_X_CSRFTOKEN`` on the wire as a header literally named
    ``http-x-csrftoken``.
    """
    headers = dict(extra.pop("headers", {}))
    if token is not None:
        client.cookies["csrftoken"] = token
        if send_header:
            headers["x-csrftoken"] = token
    return client.generic(
        "POST",
        path,
        data=_multipart_bytes(fields, files),
        content_type=_multipart_content_type(charset),
        headers=headers,
        **extra,
    )


def _operations_bytes(*, note=b"plain", operation_name=None):
    """A serialized ``operations`` control document with two byte-exact slots.

    ``note`` is an inert top-level member - Strawberry ignores unknown members,
    exactly as ``_sized_body``'s ``pad`` relies on - so a row can carry arbitrary
    bytes through the control document while the operation still executes
    normally. ``operation_name`` becomes ``operationName``, which upstream echoes
    back verbatim when it does not match (``Unknown operation named "..."``), and
    that echo is how a row proves the bytes arrived byte-for-byte rather than
    merely arrived.
    """
    document = b'{"query": "{ __typename }", "note": "' + note + b'"'
    if operation_name is not None:
        document += b', "operationName": "' + operation_name + b'"'
    return document + b"}"


def _assert_multipart_control_document_refused(response):
    """The package's refusal for a control document it will not read as JSON.

    Pinning the reason is what makes the row a statement about the wire contract:
    the same bytes without the contract reach the schema and answer ``200``, and a
    lossily-decoded ``map`` that got past this check would answer ``400`` with
    upstream's "File(s) missing in form data" instead. Only the exact reason tells
    those apart.
    """
    assert response.status_code == 400
    assert response.headers["Content-Type"].startswith("text/plain")
    assert response.content == b"Unable to parse request body as JSON"
    _assert_no_graphql_envelope(response)


def _assert_no_graphql_envelope(response):
    """The response is Django's own, produced BEFORE the schema ever ran.

    The load-bearing half of every row whose subject is a boundary Django owns -
    the ``ALLOWED_HOSTS`` host check, CSRF, URL resolution, and the GET-query
    refusal. A ``200`` with a payload and a ``400`` with a payload are different
    failures; only the absence of a ``data`` key distinguishes "Django answered
    first" from "the view executed and reported an error". Named once so the four
    rows say what they mean, and so the assertion message carries the path.
    """
    assert b'"data"' not in response.content, response.request["PATH_INFO"]


# ---------------------------------------------------------------------------
# Row 1: the project's own middleware runs on the GraphQL route
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_project_middleware_executes_on_the_graphql_http_route():
    """Row 1: a consumer middleware sees the GraphQL request and shapes its response.

    Asserting the recorded PATH is what makes this a proof about the GraphQL
    route rather than about any route. The ``Client`` is constructed INSIDE the
    override block on purpose: a handler caches its middleware chain at its first
    request, so a client built before the override would never load the sentinel.
    """
    seed_data(1)
    _MIDDLEWARE_PATHS.clear()

    with override_settings(MIDDLEWARE=[*settings.MIDDLEWARE, f"{__name__}._SentinelMiddleware"]):
        response = _post(Client(), _ITEMS)

    assert response.status_code == 200
    assert response.json()["data"]["allItems"]["edges"]
    assert _MIDDLEWARE_PATHS == ["/graphql/"]
    assert response[_SENTINEL_HEADER] == "1"


# ---------------------------------------------------------------------------
# Row 2: SecurityMiddleware's headers
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_security_middleware_headers_ride_the_graphql_response():
    """Row 2: ``SecurityMiddleware`` decorates the GraphQL response like any other.

    Nosniff and the referrer policy are Django's defaults under fakeshop's
    settings and need no override. HSTS does: ``SECURE_HSTS_SECONDS`` is ``0`` by
    default, and ``SecurityMiddleware`` emits the header only when
    ``request.is_secure()`` - hence ``secure=True``, which is load-bearing, and a
    fresh ``Client`` inside the override so the middleware re-reads the setting.
    """
    seed_data(1)

    response = _post(Client(), _TYPENAME)
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "same-origin"

    with override_settings(SECURE_HSTS_SECONDS=3600):
        secure_response = _post(Client(), _TYPENAME, secure=True)

    assert secure_response.status_code == 200
    assert "max-age=3600" in secure_response.headers["Strict-Transport-Security"]


# ---------------------------------------------------------------------------
# Row 3: the ALLOWED_HOSTS boundary
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_a_hostile_host_header_is_rejected_before_the_schema_runs():
    """Row 3: a hostile ``Host`` gets Django's ``400``, not a GraphQL envelope.

    ``ALLOWED_HOSTS`` is set explicitly so the row never depends on fakeshop's
    ``DEBUG`` value (its shipped ``ALLOWED_HOSTS = []`` would accept only
    ``localhost`` / ``127.0.0.1`` under ``DEBUG=True``). The load-bearing half is
    the SECOND assertion: no ``data`` key means Django's host boundary answered
    before the view, so the schema never executed.
    """
    seed_data(1)

    with override_settings(ALLOWED_HOSTS=["testserver"]):
        response = _post(Client(), _TYPENAME, HTTP_HOST="evil.example")

    assert response.status_code == 400
    _assert_no_graphql_envelope(response)


# ---------------------------------------------------------------------------
# Row 4: CSRF on a cookie-authenticated mutation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("token_mode", "expected_status"),
    [
        pytest.param("missing", 403, id="missing-token"),
        pytest.param("wrong", 403, id="wrong-token"),
        pytest.param("correct", 200, id="correct-token"),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_csrf_is_enforced_on_a_cookie_authenticated_graphql_mutation(token_mode, expected_status):
    """Row 4: all three CSRF directions on a real write, under a cookie session.

    ``Client(enforce_csrf_checks=True)`` turns off the test client's usual CSRF
    bypass, so ``CsrfViewMiddleware`` runs for real. The correct token is read
    off the ``csrftoken`` cookie that fakeshop's ``ensure_csrf_cookie`` mount sets
    on the IDE GET - the same round trip a browser makes. ``createCategory`` is a
    shipped write already driven by ``test_products_api.py``, and the caller is
    granted ``add_category`` the same way that suite does (no ``create_users``
    user holds a write perm by default, and ``staff_1`` is ``is_staff`` but not a
    superuser) so the row fails on CSRF alone, never on authorization.
    """
    user = _user_who_can_add_categories()
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    client.get("/graphql/", HTTP_ACCEPT="text/html")

    extra = {}
    if token_mode == "wrong":
        extra["HTTP_X_CSRFTOKEN"] = "n0tth3r1ghtt0k3n" * 4
    elif token_mode == "correct":
        extra["HTTP_X_CSRFTOKEN"] = client.cookies["csrftoken"].value

    name = f"zzz_csrf_cat_{token_mode}"
    response = _post(client, _CREATE_CATEGORY, variables={"d": {"name": name}}, **extra)

    assert response.status_code == expected_status
    if expected_status == 200:
        payload = response.json()["data"]["createCategory"]
        assert payload["errors"] == []
        assert payload["node"] == {"name": name}
        assert models.Category.objects.filter(name=name).exists()
    else:
        _assert_no_graphql_envelope(response)
        assert not models.Category.objects.filter(name=name).exists()


# ---------------------------------------------------------------------------
# Row 5: cache policy on an authenticated read
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_an_authenticated_get_varies_on_cookie():
    """Row 5: an authenticated GraphQL GET is not blindly cacheable.

    ``Vary: Cookie`` is deterministic on this mount from two directions:
    ``ensure_csrf_cookie`` forces ``CsrfViewMiddleware`` to set the CSRF cookie
    (which calls ``patch_vary_headers(response, ("Cookie",))``), and
    ``SessionMiddleware`` patches it as well once the session is accessed. The
    payload assertion pins that the response really is the logged-in actor's,
    which is what makes the cache-variation requirement meaningful.
    """
    create_users(1)
    client = Client()
    client.force_login(get_user_model().objects.get(username="staff_1"))

    response = client.get("/graphql/", {"query": _ME})

    assert response.status_code == 200
    assert response.json()["data"]["me"] == {"username": "staff_1"}
    assert "Cookie" in response.headers.get("Vary", "")


# ---------------------------------------------------------------------------
# Row 6: routing policy belongs to Django's URLconf
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_routing_policy_is_djangos_urlconf_not_the_routers():
    """Row 6: exact match at ``/graphql/``, ``APPEND_SLASH`` at ``/graphql``, ``404`` beyond.

    The ``301`` on a POST to ``/graphql`` is the documented policy the migration
    note must warn about: most clients will not re-``POST`` a redirect. It is the
    ambient expectation here because pytest-django runs the suite at
    ``DEBUG=False``; under ``DEBUG=True`` ``CommonMiddleware`` raises
    ``RuntimeError`` for exactly this case, so this row must NOT override
    ``DEBUG``. The prefix-extension paths reach the rest of the URLconf, proving
    no package-owned prefix route claims them.
    """
    seed_data(1)
    client = Client()

    exact = _post(client, _ITEMS)
    assert exact.status_code == 200
    assert exact.json()["data"]["allItems"]["edges"]

    appended = _post(client, _ITEMS, path="/graphql")
    assert appended.status_code == 301
    assert appended.headers["Location"] == "/graphql/"

    for unmatched in ("/graphql-admin", "/graphqlanything"):
        response = _post(client, _ITEMS, path=unmatched)
        assert response.status_code == 404, unmatched
        _assert_no_graphql_envelope(response)


# ---------------------------------------------------------------------------
# Row 7: the per-mount IDE and GET controls
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_graphql_ide_and_get_queries_can_be_turned_off_on_the_package_view():
    """Row 7: ``graphql_ide=None`` and ``allow_queries_via_get=False`` are supported.

    Proven against a second mount of the package view through the Probe URLconf,
    contrasted with fakeshop's default mount in the same test so the difference is
    attributable to the keywords rather than to the environment. Status codes,
    content types, and the absence of an HTML body are pinned; upstream's reason
    strings are not, since those are upstream's to change.
    """
    seed_data(1)

    with override_settings(ROOT_URLCONF=__name__):
        client = Client()
        ide_off = client.get("/ide-off/", HTTP_ACCEPT="text/html")
        get_query = client.get("/ide-off/", {"query": _TYPENAME})
        default_ide = client.get("/graphql/", HTTP_ACCEPT="text/html")
        ide_off_post = _post(client, _TYPENAME, path="/ide-off/")

    # The IDE is off: an HTML-accepting GET is refused instead of served a page.
    assert ide_off.status_code == 404
    assert ide_off.headers["Content-Type"].startswith("text/plain")
    assert b"<html" not in ide_off.content.lower()

    # GET queries are off: the operation is rejected, never executed.
    assert get_query.status_code == 400
    _assert_no_graphql_envelope(get_query)

    # POST still works on that mount, so the two keywords narrow the surface
    # rather than breaking it.
    assert ide_off_post.status_code == 200
    assert ide_off_post.json()["data"] == {"__typename": "Query"}

    # The default fakeshop mount keeps both, so the contrast is the keywords'.
    assert default_ide.status_code == 200
    assert default_ide.headers["Content-Type"].startswith("text/html")


# ---------------------------------------------------------------------------
# The full production-profile mount: the guide's recipe, proven as one unit
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_the_production_profile_mount_refuses_introspection_and_still_serves_operations():
    """The documented production mount works as one unit, not only knob by knob.

    ``graphql_ide=None`` and ``allow_queries_via_get=False`` are proven
    individually in row 7 above; this row proves the guide's COMBINED recipe -
    those two plus ``AddValidationRules([NoSchemaIntrospectionCustomRule])`` on a
    ``DjangoSchema`` - over the real fakeshop surface. Introspection documents
    (``__schema`` / ``__type``) are refused at validation with ``data`` never
    produced, ``__typename`` stays available (the rule's actual scope - it is a
    recon-narrowing control, not an authorization boundary), and an ordinary
    operation is served so the profile narrows the mount without breaking it.
    Upstream's refusal message is not pinned; the refusal and its phase are.
    """
    seed_data(1)

    with override_settings(ROOT_URLCONF=__name__):
        client = Client()
        schema_probe = _post(
            client,
            "{ __schema { queryType { name } } }",
            path="/production-profile/",
        )
        type_probe = _post(
            client,
            '{ __type(name: "Query") { name } }',
            path="/production-profile/",
        )
        typename = _post(client, _TYPENAME, path="/production-profile/")
        operation = _post(client, _ITEMS, path="/production-profile/")
        ide = client.get("/production-profile/", HTTP_ACCEPT="text/html")
        get_query = client.get("/production-profile/", {"query": _TYPENAME})

    # Both introspection entry points are validation-refused: errors without data.
    for refused in (schema_probe, type_probe):
        payload = refused.json()
        assert payload["errors"]
        assert payload.get("data") is None

    # ``__typename`` is outside the rule's scope and keeps working.
    assert typename.status_code == 200
    assert typename.json()["data"] == {"__typename": "Query"}

    # An ordinary operation still executes on the same mount.
    assert operation.status_code == 200
    assert operation.json()["data"]["allItems"]["edges"]

    # The row-7 knobs hold on this mount too: no IDE page, no GET execution.
    assert ide.status_code == 404
    assert b"<html" not in ide.content.lower()
    assert get_query.status_code == 400


# ---------------------------------------------------------------------------
# The async twin: the same middleware chain, dispatched on the event loop
# ---------------------------------------------------------------------------


async def test_the_async_package_view_runs_inside_djangos_middleware_chain():
    """``AsyncDjangoGraphQLView`` answers a real request with the security headers on.

    The async colour of rows 1-2: Django dispatches the coroutine view directly
    (upstream's ``as_view`` marks it), and ``SecurityMiddleware`` still decorates
    the response, so the middleware chain demonstrably ran on the async path. The
    operation is deliberately DB-free - a query touching the ORM from the event
    loop would raise ``SynchronousOnlyOperation`` and prove nothing about the
    transport.
    """
    with override_settings(ROOT_URLCONF=__name__):
        response = await _post_bytes(
            AsyncClient(),
            json.dumps({"query": _TYPENAME}),
            path="/async-graphql/",
        )

    assert response.status_code == 200
    assert response.json()["data"] == {"__typename": "Query"}
    assert response.headers["X-Content-Type-Options"] == "nosniff"


async def test_the_async_package_view_enforces_the_same_utf8_wire_contract():
    """The async colour of rows 19 / 22 / 23: non-UTF-8 request JSON is a 400 here too.

    The sync half of this contract runs over ``/graphql/`` in
    ``test_products_api.py``. The async half is the stronger attribution, and is
    why it is worth a row of its own: ``_cross_web_patches`` patches only the
    **sync** request adapter, so the async transport's bytes were never touched
    by the package before this slice - and, being raw bytes, ``json.loads``
    auto-detected them and a UTF-16 body silently *succeeded* with nothing
    pinning it. Both 400s here are therefore attributable to
    ``views.py::_RequestBodyBoundaryMixin.parse_json``'s strict decode having
    replaced the raw-bytes path, which is the but-for cause of each even though
    only the UTF-16 body fails *at* the decode (the BOM'd UTF-8 body decodes and
    is then refused by upstream's ``json.loads``, whose ``__cause__`` is a
    ``json.JSONDecodeError`` - the per-mechanism split is pinned in
    ``tests/test_views.py``).

    The valid-UTF-8 control shares the request sequence so the two rejections
    cannot be a broken-mount artifact. DB-free for the same reason as the
    sibling async rows: an ORM read from the event loop would raise
    ``SynchronousOnlyOperation``.
    """
    document = json.dumps({"query": _TYPENAME})
    with override_settings(ROOT_URLCONF=__name__):
        client = AsyncClient()
        utf16 = await _post_bytes(client, document.encode("utf-16"), path="/async-graphql/")
        utf8_bom = await _post_bytes(
            client,
            b"\xef\xbb\xbf" + document.encode("utf-8"),
            path="/async-graphql/",
        )
        control = await _post_bytes(client, document, path="/async-graphql/")

    assert utf16.status_code == 400
    assert utf8_bom.status_code == 400

    assert control.status_code == 200
    assert control.json()["data"] == {"__typename": "Query"}


# ---------------------------------------------------------------------------
# The shared-helper colour: the ordinary path still reads as an ordinary
# GraphQL response through ``graphql_client.py`` on the package's own view.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_the_package_view_serves_an_ordinary_graphql_response():
    """The mounted package view is a drop-in: the shared live helpers work unchanged.

    Guards the swap in ``config/urls.py`` itself - every sibling live suite posts
    through ``graphql_client.py`` against this mount, so a regression in the
    package view would surface here first with a transport-shaped name.
    """
    seed_data(1)
    assert_graphql_data(_TYPENAME, {"__typename": "Query"})
    assert post_graphql(_ITEMS).status_code == 200


# ===========================================================================
# The cumulative request-body cap. Test-plan rows 13-18.
# ===========================================================================


# ---------------------------------------------------------------------------
# Row 13 + 14 (JSON): below, at, and above the limit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("size", "expected_status"),
    [
        pytest.param(_TINY_CAP - 32, 200, id="below"),
        pytest.param(_TINY_CAP, 200, id="at"),
        pytest.param(_TINY_CAP + 1, 413, id="one-byte-above"),
        pytest.param(_TINY_CAP * 4, 413, id="far-above"),
    ],
)
@pytest.mark.django_db
def test_a_declared_body_is_capped_at_the_configured_limit(size, expected_status):
    """Row 13/14: a valid JSON operation below and AT the cap runs; above it gets ``413``.

    The ``at`` and ``one-byte-above`` rows are the pair that pins the comparison
    as ``>`` rather than ``>=``: a body exactly at the configured limit is a legal
    body. Bodies are byte-exact rather than approximate, so the boundary is
    actually tested instead of straddled.
    """
    seed_data(1)

    with override_settings(ROOT_URLCONF=__name__):
        response = _post_bytes(Client(), _sized_body(size), path="/cap-tiny/")

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["data"] == {"__typename": "Query"}
    else:
        _assert_body_limit_response(response)


# ---------------------------------------------------------------------------
# Row 13: what the declared length can and cannot do, per transport
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "content_length",
    [pytest.param("", id="absent"), pytest.param("10", id="understated")],
)
@pytest.mark.django_db
def test_on_wsgi_a_missing_or_understated_content_length_shrinks_the_body_it_cannot_grow_it(
    content_length,
):
    """Row 13, WSGI colour: the declared length cannot UNDERSTATE what the app receives.

    Django's ``LimitedStream`` truncates reads at the declared length, so an
    absent declaration yields **0** bytes to the application and an understated
    one yields exactly the declared count. The honest outcome is therefore
    upstream's malformed-JSON ``400`` on a truncated document, not a ``413`` -
    there is nothing for the counted check to catch on this transport, which is
    exactly the claim Decision 7 step 2 makes about WSGI. The ASGI colour of the
    same two shapes is where the counted check earns its keep (below).
    """
    seed_data(1)

    with override_settings(ROOT_URLCONF=__name__):
        response = _post_bytes(
            Client(),
            _sized_body(_TINY_CAP * 4),
            path="/cap-tiny/",
            CONTENT_LENGTH=content_length,
        )

    assert response.status_code == 400
    assert response.content != _BODY_LIMIT_REASON.encode()
    _assert_no_graphql_envelope(response)


@pytest.mark.parametrize(
    ("extra_headers", "case_id"),
    [
        pytest.param((), "no-content-length"),
        pytest.param(((b"content-length", b"10"),), "understated-content-length"),
    ],
)
def test_on_asgi_an_absent_or_lying_content_length_cannot_buy_a_larger_body(
    extra_headers,
    case_id,
):
    """Row 13, ASGI colour: the COUNTED check is what bounds an undeclared body.

    This is the shape the declared gate structurally cannot see. Django's ASGI
    handler hands the application every byte it received regardless of the
    header, so with no declaration - or a declaration of ``10`` against a
    four-times-oversized payload - the only application-level bound left is the
    real byte count. On the oldest supported Django (the ``5.2.16`` floor) it is
    the ONLY bound at all, since the 5.2 series'
    ``HttpRequest.body`` has no seekable actual-size check of its
    own - which is exactly why the package performs its own size probe on the
    spooled body file rather than counting ``len(request.body)``. That the probe
    costs no read is a package-tier proof (``tests/test_views.py``); what this row
    owns is that the real handler, with the real middleware chain, produces the
    package's ``413`` for both undeclarable shapes.

    Deliberately DB-free and un-marked: an ORM read from the event loop would
    raise ``SynchronousOnlyOperation`` and prove nothing about the transport.
    ``DATA_UPLOAD_MAX_MEMORY_SIZE`` is left alone here on purpose - it is the one
    cell where the two supported Django versions diverge, so no ASGI row lowers
    it.
    """
    with override_settings(ROOT_URLCONF=__name__):
        status, headers, body = _asgi_post(
            "/cap-tiny/",
            [_sized_body(_TINY_CAP * 4).encode()],
            extra_headers=extra_headers,
        )

    assert status == 413, case_id
    assert headers["Content-Type"].startswith("text/plain")
    assert body == _BODY_LIMIT_REASON.encode()


def test_a_body_arriving_in_several_asgi_fragments_is_capped_on_the_cumulative_total():
    """Row 13: *cumulative* - three individually-legal fragments that together are not.

    Each fragment is comfortably under the cap; only their sum crosses it. The
    under-cap control in the same test is what makes the ``413`` attributable to
    the total rather than to the harness: the identical three-fragment shape
    answers ``200`` with real data when the sum fits, so the driver is proven
    capable of success first.
    """
    head = b'{"query": "{ __typename }", "pad": "'
    tail = b'"}'
    over = [head + b"y" * 150, b"y" * 150, tail]
    under = [head + b"y" * 100, b"y" * 100, tail]

    # The point of the row, asserted before the requests so a later arithmetic
    # drift cannot leave it silently proving something weaker.
    assert all(len(fragment) < _TINY_CAP for fragment in over)
    assert sum(len(fragment) for fragment in over) > _TINY_CAP
    assert sum(len(fragment) for fragment in under) <= _TINY_CAP

    with override_settings(ROOT_URLCONF=__name__):
        over_status, over_headers, over_body = _asgi_post("/cap-tiny/", over)
        under_status, _, under_body = _asgi_post("/cap-tiny/", under)

    assert over_status == 413
    assert over_headers["Content-Type"].startswith("text/plain")
    assert over_body == _BODY_LIMIT_REASON.encode()

    assert under_status == 200
    assert json.loads(under_body)["data"] == {"__typename": "Query"}


# ---------------------------------------------------------------------------
# Row 14: malformed JSON, both sides of the cap
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_malformed_json_over_the_cap_gets_413_and_under_it_still_gets_400():
    """Row 14/15: the cap outranks the parse, and the discrimination proves it ran.

    The same malformed bytes produce two different failures depending only on
    length, which is an independent witness that no parse happens above the cap:
    a ``400`` with upstream's parse message can only come from a parse that
    executed, so its absence in the over-cap direction is meaningful. The
    under-cap direction also pins that the cap did not disturb the shipped
    malformed-body contract.
    """
    seed_data(1)
    malformed = b"this is not JSON at all"

    with override_settings(ROOT_URLCONF=__name__):
        client = Client()
        under = _post_bytes(client, malformed, path="/cap-tiny/")
        over = _post_bytes(client, malformed + b" " * (_TINY_CAP * 2), path="/cap-tiny/")

    assert under.status_code == 400
    assert under.content == b"Unable to parse request body as JSON"

    _assert_body_limit_response(over)


# ---------------------------------------------------------------------------
# Row 14: multipart
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_a_multipart_request_over_the_declared_cap_is_refused():
    """Row 14: multipart gets the declared-size gate (Decision 7 step 3).

    The declared gate is the whole of this card's multipart contract: per-file
    count, per-file size, and aggregate size are a later card's. What the view must
    NOT do is read ``request.body`` to measure a multipart payload - that would
    defeat Django's streaming upload handlers and break the ``Upload``-scalar
    path - so the un-broken direction of this row is earned by
    ``test_uploads_api.py``'s multipart mutations continuing to pass against
    fakeshop's default mount, which now carries the 1 MiB default cap.
    """
    seed_data(1)

    with override_settings(ROOT_URLCONF=__name__):
        response = Client().post("/cap-tiny/", data={"operations": "x" * (_TINY_CAP * 2)})

    _assert_body_limit_response(response)


# ---------------------------------------------------------------------------
# Row 15: proof that neither parsing nor schema execution ran
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_an_over_cap_mutation_is_rejected_before_any_parse_or_schema_execution():
    """Row 15: two negative witnesses, made meaningful by an under-cap control.

    The rejected request is a **valid** ``createCategory`` mutation - it would
    have parsed and written a row had it run - padded past the cap. Over the cap:
    ``413``, the spy's ``parse_json`` list stays empty, and no ``Category`` row
    exists. Under the cap, the SAME mutation: ``200``, exactly one recorded
    parse, and the row is there.

    The control is not optional. Two empty witnesses on their own are equally
    consistent with a spy that never records and a database that never writes;
    only the positive direction shows both instruments work, which is what turns
    the empty lists into evidence.
    """
    user = _user_who_can_add_categories()

    over_name = "zzz_cap_rejected_cat"
    under_name = "zzz_cap_allowed_cat"
    over_body = _sized_body(
        _TINY_CAP * 4,
        query=_CREATE_CATEGORY,
        variables={"d": {"name": over_name}},
    )
    under_body = json.dumps(
        {"query": _CREATE_CATEGORY, "variables": {"d": {"name": under_name}}},
    )
    assert len(under_body) <= _TINY_CAP

    _PARSE_CALLS.clear()
    with override_settings(ROOT_URLCONF=__name__):
        client = Client()
        client.force_login(user)
        over = _post_bytes(client, over_body, path="/cap-spy/")

        assert _PARSE_CALLS == []
        assert not models.Category.objects.filter(name=over_name).exists()

        under = _post_bytes(client, under_body, path="/cap-spy/")

    _assert_body_limit_response(over)

    assert under.status_code == 200
    payload = under.json()["data"]["createCategory"]
    assert payload["errors"] == []
    assert payload["node"] == {"name": under_name}
    assert models.Category.objects.filter(name=under_name).exists()
    assert len(_PARSE_CALLS) == 1
    assert under_name.encode() in bytes(_PARSE_CALLS[0])
    _PARSE_CALLS.clear()


# ---------------------------------------------------------------------------
# Row 16: which ceiling fired
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce():
    """Row 16: the package cap vs Django's ``DATA_UPLOAD_MAX_MEMORY_SIZE``, both directions.

    Package direction: the tiny mount rejects with the package's own ``413`` and
    the package's exact reason, with Django's knob left at its default.

    Django direction: a mount whose cap is 8 MiB, under a 64-byte
    ``DATA_UPLOAD_MAX_MEMORY_SIZE``, is refused by Django first. The MEASURED
    status is **400**, not ``413`` - on both Django 5.2 and 6.0, and on both
    transports. ``ASGIHandler.create_request``'s ``except RequestDataTooBig ->
    413`` wraps only ``ASGIRequest`` construction, which never touches the body;
    ``RequestDataTooBig`` is raised lazily from ``HttpRequest.body`` inside the
    view, where ``response_for_exception`` maps ``SuspiciousOperation`` to
    ``400``. Deliberately WSGI-only: lowering Django's knob under the
    ASGI harness is the single cell where the two Django versions diverge.
    """
    seed_data(1)
    body = _sized_body(_TINY_CAP * 4)

    with override_settings(ROOT_URLCONF=__name__):
        ours = _post_bytes(Client(), body, path="/cap-tiny/")

        with override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=64):
            djangos = _post_bytes(Client(), body, path="/cap-off/")

    _assert_body_limit_response(ours)

    assert djangos.status_code == 400
    assert djangos.content != _BODY_LIMIT_REASON.encode()
    _assert_no_graphql_envelope(djangos)


# ---------------------------------------------------------------------------
# Row 17: the precedence ladder, behaviorally
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_the_view_kwarg_beats_the_setting_on_a_real_request():
    """Row 17: two mounts, one setting, one body - only the kwarg differs.

    A generous project-wide setting does not loosen a mount that pinned its own
    smaller cap, and a mount that pinned nothing takes the setting. Both halves
    run inside one override against identical bytes, so the difference is
    attributable to the keyword rather than to the environment.
    """
    seed_data(1)
    body = _sized_body(_TINY_CAP * 4)

    with override_settings(
        ROOT_URLCONF=__name__,
        DJANGO_STRAWBERRY_FRAMEWORK={"MAX_REQUEST_BODY_BYTES": 1_048_576},
    ):
        client = Client()
        pinned = _post_bytes(client, body, path="/cap-tiny/")
        inherited = _post_bytes(client, body, path="/graphql/")

    _assert_body_limit_response(pinned)

    assert inherited.status_code == 200
    assert inherited.json()["data"] == {"__typename": "Query"}


@pytest.mark.django_db
def test_the_setting_beats_the_default_on_a_real_request():
    """Row 17: a small setting caps fakeshop's own mount, which declares no kwarg.

    The default is 1 MiB, so this body would sail through without the setting -
    which the sibling row above demonstrates on the same path. The mount here is
    fakeshop's real ``/graphql/``, so this is the rung a project actually turns.
    """
    seed_data(1)
    body = _sized_body(_TINY_CAP * 4)

    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"MAX_REQUEST_BODY_BYTES": 64}):
        capped = _post_bytes(Client(), body, path="/graphql/")

    _assert_body_limit_response(capped)


@pytest.mark.django_db
def test_a_none_setting_disables_the_package_cap_that_the_default_would_apply():
    """Row 17: ``MAX_REQUEST_BODY_BYTES = None`` disables the package cap.

    The only row that needs a megabyte-scale payload, because "disabled" is only
    demonstrable against a body the DEFAULT rejects. The same bytes are posted
    twice - once with the key absent (the 1 MiB default applies, ``413``) and
    once with it explicitly ``None`` (accepted) - so the difference is
    attributable to the setting alone. It stays under Django's own 2.5 MiB
    ``DATA_UPLOAD_MAX_MEMORY_SIZE`` default so the package cap is the only
    ceiling in play.
    """
    seed_data(1)
    body = _sized_body(1_048_576 + 64)

    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={}):
        defaulted = _post_bytes(Client(), body, path="/graphql/")

    with override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"MAX_REQUEST_BODY_BYTES": None}):
        disabled = _post_bytes(Client(), body, path="/graphql/")

    _assert_body_limit_response(defaulted)

    assert disabled.status_code == 200
    assert disabled.json()["data"] == {"__typename": "Query"}


# ---------------------------------------------------------------------------
# The async twin carries the same cap
# ---------------------------------------------------------------------------


async def test_the_async_package_view_enforces_the_same_body_cap():
    """The async colour of rows 13-14: the same ``413``, from the ``async def run``.

    The two ``run`` overrides differ only in ``async`` / ``await``, which is the
    same irreducible split upstream carries in its own ``dispatch`` pair - so the
    contract needs proving on both. DB-free for the same reason as the sibling
    async row: an ORM read from the event loop would raise
    ``SynchronousOnlyOperation``.
    """
    with override_settings(ROOT_URLCONF=__name__):
        client = AsyncClient()
        over = await _post_bytes(client, _sized_body(_TINY_CAP * 4), path="/async-cap-tiny/")
        under = await _post_bytes(client, _sized_body(_TINY_CAP), path="/async-cap-tiny/")

    _assert_body_limit_response(over)

    assert under.status_code == 200
    assert under.json()["data"] == {"__typename": "Query"}


# ===========================================================================
# The strict UTF-8 wire contract is the package VIEW's policy,
# so it does not share the ``APPLY_UPSTREAM_PATCHES`` lifecycle. These rows
# mount the package view with the Strawberry patch opted out and assert the
# policy still holds - and, separately, that the upstream-bug workaround the
# switch really does own is genuinely off in the same state.
# ===========================================================================

#: The three non-UTF-8 shapes, as real request bodies. Two fail at the
#: view's strict decode (a BOM'd multi-byte form's leading byte is not valid
#: UTF-8) and the third decodes cleanly and is refused by ``json.loads`` for its
#: leading U+FEFF - so the trio covers both mechanisms, which matters because
#: only one of them is the package's own code.
_NON_UTF8_BODIES = (
    pytest.param(json.dumps({"query": _TYPENAME}).encode("utf-16"), id="utf-16-with-bom"),
    pytest.param(json.dumps({"query": _TYPENAME}).encode("utf-32"), id="utf-32-with-bom"),
    pytest.param(b"\xef\xbb\xbf" + json.dumps({"query": _TYPENAME}).encode(), id="utf-8-bom"),
)


@contextlib.contextmanager
def _strawberry_patch_opted_out():
    """Run the block in the state ``APPLY_UPSTREAM_PATCHES = {"strawberry": False}`` produces.

    The patch installs from ``AppConfig.ready()``, long before any test runs, so
    setting the switch alone cannot un-install it - a row that only overrode the
    setting would prove nothing. The honest simulation restores upstream's own two
    methods *and* sets the switch, so a stray ``apply()`` during the block stays a
    no-op and what remains running is exactly what an opted-out consumer runs.

    The ``cross_web`` patch is deliberately left installed: it has its own
    ``{"cross_web": False}`` member, and it is what routes the sync transport's
    raw bytes to ``parse_json`` in the first place. Disabling it too would test a
    different finding (upstream's decode-inside-a-property ``500``) and would say
    nothing about who owns the wire contract.
    """
    saved_parse_json = BaseView.__dict__["parse_json"]
    saved_parse_query_params = BaseView.__dict__["parse_query_params"]
    override = override_settings(
        ROOT_URLCONF=__name__,
        DJANGO_STRAWBERRY_FRAMEWORK={"APPLY_UPSTREAM_PATCHES": {"strawberry": False}},
    )
    try:
        BaseView.parse_json = strawberry_patches._original_parse_json
        BaseView.parse_query_params = strawberry_patches._original_parse_query_params
        assert strawberry_patches._patch_is_installed() is False
        with override:
            yield
    finally:
        BaseView.parse_json = saved_parse_json
        BaseView.parse_query_params = saved_parse_query_params


@pytest.mark.parametrize("body", _NON_UTF8_BODIES)
@pytest.mark.django_db
def test_the_utf8_wire_contract_survives_the_upstream_patch_kill_switch(body):
    """The finding, over the wire: a non-UTF-8 body still 400s with the patch opted out.

    Before this change the strict decode lived inside
    ``_strawberry_patches.py::_patched_parse_json``, so a consumer who disabled
    the package's workarounds for *upstream bugs* also disabled a permanent
    package security policy and silently got UTF-16 / UTF-32 acceptance back. A
    permanent security contract must not share a temporary patch's lifecycle, so
    the decode now lives on the mounted view.

    The valid-UTF-8 control in the same opted-out state is what makes the
    rejection attributable: it shows the mount still serves real GraphQL while the
    patch is off, so the 400 is the wire contract firing rather than a broken
    endpoint.
    """
    seed_data(1)

    with _strawberry_patch_opted_out():
        client = Client()
        rejected = _post_bytes(client, body)
        control = _post_bytes(client, json.dumps({"query": _TYPENAME}))

    assert rejected.status_code == 400
    _assert_no_graphql_envelope(rejected)

    assert control.status_code == 200
    assert control.json()["data"] == {"__typename": "Query"}


@pytest.mark.parametrize("body", _NON_UTF8_BODIES)
async def test_the_async_view_keeps_the_utf8_wire_contract_with_the_patch_opted_out(body):
    """The async colour: one shared mixin method, so neither transport can drift.

    Worth its own row for the same reason the patch-on async row is: the
    ``cross_web`` patch touches only the **sync** adapter, so on this transport
    the bytes reach ``parse_json`` raw with or without any patch. If the wire
    contract were still gated, this is the transport where a UTF-16 body would
    silently *succeed* - ``json.loads`` auto-detects raw bytes - rather than
    merely 500. DB-free like its sibling async rows: an ORM read from the event
    loop would raise ``SynchronousOnlyOperation``.
    """
    with _strawberry_patch_opted_out():
        client = AsyncClient()
        rejected = await _post_bytes(client, body, path="/async-graphql/")
        control = await _post_bytes(
            client,
            json.dumps({"query": _TYPENAME}),
            path="/async-graphql/",
        )

    assert rejected.status_code == 400

    assert control.status_code == 200
    assert control.json()["data"] == {"__typename": "Query"}


@contextlib.contextmanager
def _every_upstream_patch_opted_out():
    """Run the block in the state the BROAD ``APPLY_UPSTREAM_PATCHES = False`` produces.

    The sibling helper simulates ``{"strawberry": False}`` and deliberately leaves
    the ``cross_web`` half installed. This one takes both halves out, which is a
    materially different state: with ``cross_web`` un-installed, upstream's sync
    ``DjangoHTTPRequestAdapter.body`` decodes inside its own *property* again, so a
    property - not ``parse_json`` - is where an undecodable body raises. That is
    why the package view mounts its own request adapter
    (``views.py::_RawBodyRequestAdapter``): the wire contract has to hold on a
    package mount in every patch state, not only in the states where a patch
    happens to be routing the bytes.

    All three replacements are restored by identity in a ``finally``, and both
    ``_patch_is_installed`` probes are asserted ``False`` inside the block, so the
    row cannot pass because a patch was quietly still installed.

    Only the sync transport needs a broad-switch row of its own: the ``cross_web``
    patch touches the sync adapter only, and upstream's
    ``AsyncDjangoHTTPRequestAdapter.get_body`` already hands over raw bytes, so
    the async transport's state is identical under either spelling of the switch
    and is covered by the ``{"strawberry": False}`` async row above.
    """
    saved_parse_json = BaseView.__dict__["parse_json"]
    saved_parse_query_params = BaseView.__dict__["parse_query_params"]
    saved_body = DjangoHTTPRequestAdapter.__dict__["body"]
    override = override_settings(
        ROOT_URLCONF=__name__,
        DJANGO_STRAWBERRY_FRAMEWORK={"APPLY_UPSTREAM_PATCHES": False},
    )
    try:
        BaseView.parse_json = strawberry_patches._original_parse_json
        BaseView.parse_query_params = strawberry_patches._original_parse_query_params
        DjangoHTTPRequestAdapter.body = property(cross_web_patches._original_body_fget)
        assert strawberry_patches._patch_is_installed() is False
        assert cross_web_patches._patch_is_installed() is False
        with override:
            yield
    finally:
        BaseView.parse_json = saved_parse_json
        BaseView.parse_query_params = saved_parse_query_params
        DjangoHTTPRequestAdapter.body = saved_body


@pytest.mark.parametrize("body", _NON_UTF8_BODIES)
@pytest.mark.django_db
def test_the_sync_wire_contract_holds_with_every_upstream_patch_opted_out(body):
    """The wire contract on the sync transport with the WHOLE kill switch thrown.

    ``{"strawberry": False}`` leaves the ``cross_web`` half routing the sync
    transport's bytes into ``parse_json``; ``False`` does not, and in that state
    the two BOM'd multi-byte bodies used to come back as an unhandled ``500``
    because upstream's adapter decoded them inside a
    property before the view's ``parse_json`` was reached. The success set was
    never wider - a ``500`` is not an acceptance - but the *controlled 400* and
    the "``__cause__`` is the only discriminator" half of Decisions 9 and 10 were
    both lost, and no row covered the state.

    The package view now owns its body source as well as its parse
    (``views.py::_RawBodyRequestAdapter``), so all three shapes are the same
    ``400``, from the same mount, with every shipped patch off. The valid-UTF-8
    control in the same state is what makes the ``400`` the wire contract firing
    rather than a broken endpoint, and ``raise_request_exception=False`` is what
    would let a regression here be observed as the ``500`` a deployment would
    return instead of being re-raised as an error.
    """
    seed_data(1)

    with _every_upstream_patch_opted_out():
        client = Client(raise_request_exception=False)
        rejected = _post_bytes(client, body)
        control = _post_bytes(client, json.dumps({"query": _TYPENAME}))

    assert rejected.status_code == 400
    _assert_no_graphql_envelope(rejected)

    assert control.status_code == 200
    assert control.json()["data"] == {"__typename": "Query"}


@pytest.mark.django_db
def test_only_the_package_mount_answers_the_same_way_in_both_patch_states():
    """Attribution: the package mount's ``400`` is the VIEW's, not a leftover patch.

    The row above would also pass if the ``cross_web`` patch had merely failed to
    un-install, so this one posts one undecodable byte string - UTF-16 with a BOM -
    to two mounts in both patch states and reads all four answers. Strawberry's own
    view moves; the package view does not:

    * upstream mount, patches OFF -> ``500``. The property-scope
      ``UnicodeDecodeError`` no ``except HTTPException`` can reach. This IS the
      upstream defect, and observing it here is what proves the simulation really
      un-installed the ``cross_web`` half.
    * upstream mount, patches ON -> ``200``. Not a typo and not a regression: with
      the strict decode moved to the package view, ``_patched_parse_json`` no
      longer narrows encodings, so ``json.loads`` applies RFC 8259 auto-detection
      to the raw bytes and *accepts* the UTF-16 document. A consumer who
      deliberately mounts Strawberry's own view keeps Strawberry's own semantics -
      the deliberate scope of the ownership split (spec-046), pinned
      at the patch tier by
      ``test_patched_parse_json_leaves_upstreams_bytes_semantics_alone`` and
      recorded here as live behavior.
    * package mount, patches OFF and ON -> ``400``, both times.

    So the switch moves upstream's mount between an unhandled ``500`` and a
    ``200``, and moves the package mount not at all. That constancy is the package
    view's own request adapter plus its own ``parse_json``, and nothing else left
    running could produce it.
    """
    seed_data(1)
    undecodable = json.dumps({"query": _TYPENAME}).encode("utf-16")

    with _every_upstream_patch_opted_out():
        client = Client(raise_request_exception=False)
        upstream_unpatched = _post_bytes(client, undecodable, path="/upstream-graphql/")
        package_unpatched = _post_bytes(client, undecodable)

    with override_settings(ROOT_URLCONF=__name__):
        patched_client = Client(raise_request_exception=False)
        upstream_patched = _post_bytes(patched_client, undecodable, path="/upstream-graphql/")
        package_patched = _post_bytes(patched_client, undecodable)

    assert upstream_unpatched.status_code == 500
    assert upstream_patched.status_code == 200

    assert package_unpatched.status_code == 400
    assert package_patched.status_code == 400


@contextlib.contextmanager
def _cross_web_patch_opted_out():
    """Run the block in the state ``{"cross_web": False}`` produces - that half alone.

    The mirror image of :func:`_strawberry_patch_opted_out`: this one takes the
    ``cross_web`` half out and deliberately leaves the Strawberry half installed,
    which is the only state that isolates what ``_cross_web_patches.py`` itself
    buys - upstream's sync ``DjangoHTTPRequestAdapter.body`` decoding inside its own
    *property* again, with the widened ``except`` still waiting in ``parse_json``
    for bytes that no longer arrive.

    Setting the switch alone would prove nothing (the patch installs from
    ``AppConfig.ready()``, long before any test runs), so upstream's property is
    restored by identity and BOTH ``_patch_is_installed`` probes are asserted
    inside the block - the half under test genuinely off, its companion genuinely
    on - so the row cannot pass for either wrong reason.
    """
    saved_body = DjangoHTTPRequestAdapter.__dict__["body"]
    override = override_settings(
        ROOT_URLCONF=__name__,
        DJANGO_STRAWBERRY_FRAMEWORK={"APPLY_UPSTREAM_PATCHES": {"cross_web": False}},
    )
    try:
        DjangoHTTPRequestAdapter.body = property(cross_web_patches._original_body_fget)
        assert cross_web_patches._patch_is_installed() is False
        assert strawberry_patches._patch_is_installed() is True
        with override:
            yield
    finally:
        DjangoHTTPRequestAdapter.body = saved_body


#: The two bodies that DISCRIMINATE: upstream's property decode rejects each (the
#: un-installed ``500``) and the raw-bytes JSON path accepts neither (the
#: installed ``400``). Their installed ``400``s travel DIFFERENT routes, measured
#: rather than assumed: ``json.loads`` decodes ``bytes`` with
#: ``errors="surrogatepass"``, so the invalid-UTF-8 body (detected ``utf-8``,
#: where ``surrogatepass`` cannot represent ``0xFF``) raises ``UnicodeDecodeError``
#: and is translated by the Strawberry half, while the raw-binary body *decodes*
#: under its detected ``utf-16-be`` and is refused as JSON by upstream's OWN
#: ``except json.JSONDecodeError``. Covering both routes is the point of the pair.
#: The excluded shapes each invert the retirement verdict if read as one: a BOM'd
#: UTF-16 body is *accepted* (``200``) once the patch hands over the raw bytes,
#: and a BOM-less multi-byte or UTF-8-BOM body answers ``400`` UN-installed - a
#: false "retirable", because upstream's decode succeeded rather than stopped.
_UNDECODABLE_BODIES = (
    pytest.param(b'{"query":"{ __typename }","pad":"\xff\xfe\xfa"}', id="invalid-utf8-in-json"),
    pytest.param(bytes(range(256)) * 4, id="raw-binary"),
)


@pytest.mark.parametrize("body", _UNDECODABLE_BODIES)
@pytest.mark.django_db
def test_the_cross_web_half_turns_upstreams_own_500_into_a_400(body):
    """What the ``cross_web`` patch buys, on the only mount that can show it.

    The rows above prove the package mount is indifferent to this switch, which is
    exactly why they cannot also prove the patch is worth shipping: a package view
    owns its own body source, so the patch's whole remaining audience is a consumer
    who mounts **Strawberry's own** view. This row is that audience. One
    undecodable body, one mount, one switch member moved:

    * half un-installed -> ``500``. Upstream's property UTF-8-decodes the body and
      the ``UnicodeDecodeError`` raises inside a *property*, where no ``except
      HTTPException`` can reach it. The Strawberry half is still installed, so the
      ``500`` is attributable to this half alone.
    * half installed -> ``400``. The raw bytes reach ``json.loads`` inside
      ``parse_json`` - a scope that can answer with a response - and the two
      parameters take the two routes out of it: the invalid-UTF-8 body raises
      ``UnicodeDecodeError`` one frame later, which
      ``_strawberry_patches.py::_patched_parse_json`` translates, while the
      raw-binary body *decodes* under ``surrogatepass`` and is refused as JSON
      by upstream's own ``except json.JSONDecodeError``. Both routes exist only
      because the bytes arrived undecoded, so the 500 -> 400 delta is this
      half's either way (verified with the Strawberry half alone restored:
      raw-binary still 400, invalid-UTF-8 500).

    So the patch does not decode anything and does not widen any success set; it
    moves the raise into a scope that can answer with a response, and this row is
    the live measurement of that move. It is also the module's standing retirement
    diagnostic: a ``400`` from the un-installed state would mean upstream stopped
    decoding eagerly and the module can be deleted.

    The valid-UTF-8 control in the un-installed state is what keeps the ``500``
    from being a broken mount, and ``raise_request_exception=False`` is what lets
    the unhandled case be observed as the ``500`` a deployment would return instead
    of being re-raised into the test.
    """
    seed_data(1)
    document = json.dumps({"query": _TYPENAME})

    with _cross_web_patch_opted_out():
        client = Client(raise_request_exception=False)
        unpatched = _post_bytes(client, body, path="/upstream-graphql/")
        control = _post_bytes(client, document, path="/upstream-graphql/")

    with override_settings(ROOT_URLCONF=__name__):
        assert cross_web_patches._patch_is_installed() is True
        patched = _post_bytes(
            Client(raise_request_exception=False),
            body,
            path="/upstream-graphql/",
        )

    assert unpatched.status_code == 500
    assert patched.status_code == 400
    _assert_no_graphql_envelope(patched)

    assert control.status_code == 200
    assert control.json()["data"] == {"__typename": "Query"}


@pytest.mark.django_db
def test_the_upstream_bug_workaround_still_respects_its_own_opt_out():
    """The other half of the ownership split: what the switch DOES still turn off.

    The two rows above would be satisfiable by a bad fix - moving everything
    somewhere ungated - so this row is what stops that. A JSON scalar body is
    upstream defect #3398: ``parse_http_body`` falls through to
    ``data.get("query")`` and raises a raw ``AttributeError``. The package's
    envelope guard converts it to a ``400``, and that guard is a workaround for a
    specific upstream version's bug, so a consumer pinning a fixed or reshaped
    Strawberry must be able to switch it off - and here it demonstrably is off,
    with the same body 400ing on the same mount once the patch is back.

    ``raise_request_exception=False`` is what lets the unhandled case be observed
    as the 500 a real deployment would return, instead of being re-raised into the
    test.
    """
    seed_data(1)
    scalar = b"42"

    with _strawberry_patch_opted_out():
        unguarded = _post_bytes(Client(raise_request_exception=False), scalar)

    guarded = _post_bytes(Client(), scalar)

    assert unguarded.status_code == 500

    assert guarded.status_code == 400
    assert b"request body" in guarded.content


# ===========================================================================
# The multipart control documents. ``parse_json``'s strict decode
# only ever sees the ``application/json`` body; ``operations`` and ``map`` reach
# the package as ``str``, already decoded by Django's own multipart parser with
# ``errors="replace"``. These rows are the wire proof of the two checks that
# close that gap - an effective UTF-8 form encoding, and no replacement marker
# in either control document - on both transports, because a direct
# ``parse_json(str)`` call cannot express a wire boundary at all.
# ===========================================================================

#: The four lossy control documents, as raw bytes, each paired with
#: the field it rides in. ``0x80`` is a lone continuation byte - never valid
#: UTF-8 - and ``0xEF 0xBF 0xBD`` is a genuine, well-formed encoding of U+FFFD,
#: which is the harder case: it decodes cleanly, so only the marker check
#: refuses it, and refusing it is what makes the malformed-byte check
#: unforgeable.
_LOSSY_CONTROL_DOCUMENTS = (
    pytest.param("operations", _operations_bytes(note=b"\x80"), id="operations-malformed"),
    pytest.param(
        "operations",
        _operations_bytes(note=b"\xef\xbf\xbd"),
        id="operations-literal-fffd",
    ),
    pytest.param("map", b'{"\x80": []}', id="map-malformed"),
    pytest.param("map", b'{"\xef\xbf\xbd": []}', id="map-literal-fffd"),
)


def _multipart_fields(field, raw):
    """The two control fields, with ``field`` replaced by ``raw`` bytes."""
    documents = {"operations": _operations_bytes(), "map": b"{}"}
    documents[field] = raw
    return list(documents.items())


@pytest.mark.django_db
def test_a_multipart_map_must_be_an_object_not_a_batched_body():
    """A JSON list in ``map`` is a controlled 400 rather than an unhandled 500.

    The general JSON guard permits a list of objects because an HTTP request body
    may be a valid GraphQL batch. Multipart's ``map`` is not a request body: the
    upload utility consumes it as a mapping and calls ``.items()``. A list of
    objects therefore used to pass the generic guard, then escape from the
    utility as ``AttributeError``. This live mount pins that the multipart
    wrapper owns the narrower field contract while ordinary batched
    ``operations`` remain Strawberry's concern.
    """
    seed_data(1)

    response = _post_multipart(
        Client(raise_request_exception=False),
        "/graphql/",
        _multipart_fields("map", b"[{}]"),
    )

    assert response.status_code == 400
    assert response.content == b"Unable to parse the multipart body"
    _assert_no_graphql_envelope(response)


async def test_the_async_view_rejects_the_same_multipart_map_shape():
    """The async multipart parser gets the same malformed-map boundary."""
    with override_settings(ROOT_URLCONF=__name__):
        response = await _post_multipart(
            AsyncClient(),
            "/async-multipart/",
            _multipart_fields("map", b"[{}]"),
        )

    assert response.status_code == 400
    assert response.content == b"Unable to parse the multipart body"
    _assert_no_graphql_envelope(response)


@pytest.mark.django_db(transaction=True)
async def test_post_pathologically_nested_body_returns_400_on_the_async_view_too(
    pathological_json_body,
):
    """Async transport: a body nested past the parser's C stack -> controlled 400.

    Both views inherit the one patched ``BaseView.parse_json``, but the wire
    answer deserves its own row per transport: pre-fix this escaped as an
    unhandled ``RecursionError`` -> ``500`` from ``run`` on the event loop.
    """
    with override_settings(ROOT_URLCONF=__name__):
        response = await _post_bytes(
            AsyncClient(),
            pathological_json_body,
            path="/async-graphql/",
        )

    assert response.status_code == 400
    assert response.content == b"Unable to parse request body as JSON"


@pytest.mark.django_db(transaction=True)
def test_a_multipart_operations_document_nested_past_the_c_stack_is_refused(
    deepcopy_overflow_operations_text,
):
    """Valid-JSON ``operations`` whose depth overflows the upload utility.

    ``json.loads`` survives this document, so the generic guard passes
    it as a well-typed object - and ``replace_placeholders_with_files``'s
    unconditional ``copy.deepcopy`` then raised ``RecursionError``, which the
    delegates' traversal tuple missed: an unhandled ``500`` for a tiny body.
    The translated answer is the delegates' own multipart-parse ``400``,
    provenance-scoped to the utility's frame.
    """
    seed_data(1)

    response = _post_multipart(
        Client(),
        "/graphql/",
        [("operations", deepcopy_overflow_operations_text.encode()), ("map", b"{}")],
    )

    assert response.status_code == 400
    assert response.content == b"Unable to parse the multipart body"
    _assert_no_graphql_envelope(response)


async def test_the_async_view_refuses_the_same_deep_operations_document(
    deepcopy_overflow_operations_text,
):
    """The async delegate scopes the deepcopy recursion identically."""
    with override_settings(ROOT_URLCONF=__name__):
        response = await _post_multipart(
            AsyncClient(),
            "/async-multipart/",
            [("operations", deepcopy_overflow_operations_text.encode()), ("map", b"{}")],
        )

    assert response.status_code == 400
    assert response.content == b"Unable to parse the multipart body"
    _assert_no_graphql_envelope(response)


@pytest.mark.parametrize(("field", "raw"), _LOSSY_CONTROL_DOCUMENTS)
@pytest.mark.django_db
def test_a_multipart_control_document_that_lost_bytes_to_djangos_decode_is_refused(field, raw):
    """The bodies that used to answer ``200`` now answer ``400``.

    An ``operations`` field carrying a malformed UTF-8 byte used to be
    replacement-decoded by Django into something that parsed and executed -
    a byte sequence the package calls invalid UTF-8, accepted on one GraphQL body
    shape. Both control documents are covered, and both directions of the same
    detector: the malformed byte Django *converts* into U+FFFD, and a literal
    U+FFFD the client sent as valid UTF-8. They are indistinguishable after
    Django's decode, which is the honest limit of this contract and the reason it
    is documented as "must survive Django's decode without a replacement marker"
    rather than "must be valid UTF-8".

    The exact reason is asserted, not just the status: a lossy ``map`` that slipped
    past the check would still answer ``400``, from upstream's own "File(s) missing
    in form data" once the replaced key failed to match a variable path. Only the
    reason distinguishes the contract from that accident.
    """
    seed_data(1)

    response = _post_multipart(Client(), "/graphql/", _multipart_fields(field, raw))

    _assert_multipart_control_document_refused(response)


@pytest.mark.parametrize(("field", "raw"), _LOSSY_CONTROL_DOCUMENTS)
async def test_the_async_view_refuses_the_same_lossy_control_documents(field, raw):
    """The async colour: one shared mixin method, two ``parse_multipart`` overrides.

    Upstream's ``parse_multipart`` is a coroutine on the async base view and a plain
    method on the sync one, so the package needs one override per transport - which
    is exactly the seam where a policy silently applies to one transport only. DB
    free for the same reason as the other async rows: an ORM read from the event
    loop would raise ``SynchronousOnlyOperation``.
    """
    with override_settings(ROOT_URLCONF=__name__):
        response = await _post_multipart(
            AsyncClient(),
            "/async-multipart/",
            _multipart_fields(field, raw),
        )

    _assert_multipart_control_document_refused(response)


_NON_UTF8_FORM_CHARSETS = (
    pytest.param("iso-8859-1", id="explicit-latin-1"),
    pytest.param("utf-16", id="explicit-utf-16"),
    pytest.param("utf-8-sig", id="bom-eating-codec"),
    pytest.param("no-such-codec", id="unusable-codec-name"),
)


@pytest.mark.parametrize("charset", _NON_UTF8_FORM_CHARSETS)
@pytest.mark.django_db
def test_a_multipart_request_declaring_a_non_utf8_form_encoding_is_refused(charset):
    """An explicit ``charset`` the package will not honour.

    A Latin-1 form declaration used to execute with ``200``, and Django's behaviour is why:
    ``_set_content_type_params`` copies a usable declared charset onto
    ``request.encoding``, which is the encoding ``MultiPartParser`` then decodes
    every field with. So the declaration is honoured - just not with the UTF-8 the
    endpoint promises - and a Latin-1 byte becomes a different character than the
    same byte would in a JSON body. The endpoint refuses instead, before the form
    is parsed at all.

    ``utf-8-sig`` is in the matrix because it is the near-miss: a codec whose name
    contains "utf-8" and which would silently swallow the BOM that Decision 10
    deliberately refuses. ``no-such-codec`` is the other end - Django drops an
    unusable charset and decodes with ``DEFAULT_CHARSET``, so accepting it would
    mean honouring a declaration nobody honoured.

    The control in the same row is what keeps this from passing for the wrong
    reason: the identical body with no charset at all executes normally.
    """
    seed_data(1)
    fields = _multipart_fields("operations", _operations_bytes())

    declared = _post_multipart(Client(), "/graphql/", fields, charset=charset)
    control = _post_multipart(Client(), "/graphql/", fields)

    _assert_multipart_control_document_refused(declared)

    assert control.status_code == 200
    assert control.json()["data"] == {"__typename": "Query"}


@pytest.mark.parametrize("charset", _NON_UTF8_FORM_CHARSETS)
async def test_the_async_view_refuses_the_same_non_utf8_form_encodings(charset):
    """The async colour of the declared-charset refusal, from the shared boundary."""
    with override_settings(ROOT_URLCONF=__name__):
        response = await _post_multipart(
            AsyncClient(),
            "/async-multipart/",
            _multipart_fields("operations", _operations_bytes()),
            charset=charset,
        )

    _assert_multipart_control_document_refused(response)


@pytest.mark.django_db
def test_genuine_utf8_and_escaped_unicode_survive_the_multipart_boundary_intact():
    """The contract is UTF-8, not ASCII - and the accepted bytes arrive unchanged.

    Four directions, because "rejects the bad shapes" is only half a contract:

    1. genuine multibyte UTF-8 in the control document executes normally. This is
       also a losslessness proof by construction, not merely an acceptance: had
       Django replacement-decoded any of those bytes, the marker check would have
       refused the request, so a ``200`` here means the document survived the
       decode byte-for-byte. It is what ``JSON.stringify`` emits by default for
       non-ASCII text, so the endpoint has not become ASCII-only.
    2. the same text as a JSON escape executes normally too - the ASCII
       serialization is unaffected.
    3. an ESCAPED U+FFFD is accepted, and reaches the schema as the real
       character: upstream echoes ``operationName`` back verbatim, so the response
       body carries the exact bytes. That is the documented escape hatch for a
       client that genuinely needs U+FFFD as data, and it is the pair to the
       literal-U+FFFD refusal above - identical status, different reason,
       different cause.
    4. genuine multibyte UTF-8 in ``operationName`` comes back byte-for-byte in
       upstream's error text, which is the strongest available statement that the
       transport did not touch the bytes.
    """
    seed_data(1)
    cafe = "caf\u00e9"

    raw_utf8 = _post_multipart(
        Client(),
        "/graphql/",
        _multipart_fields("operations", _operations_bytes(note=cafe.encode())),
    )
    escaped = _post_multipart(
        Client(),
        "/graphql/",
        _multipart_fields("operations", _operations_bytes(note=b"caf\\u00e9")),
    )
    escaped_marker = _post_multipart(
        Client(),
        "/graphql/",
        _multipart_fields("operations", _operations_bytes(operation_name=b"\\ufffd")),
    )
    echoed = _post_multipart(
        Client(),
        "/graphql/",
        _multipart_fields("operations", _operations_bytes(operation_name=cafe.encode())),
    )

    for accepted in (raw_utf8, escaped):
        assert accepted.status_code == 200
        assert accepted.json()["data"] == {"__typename": "Query"}

    assert escaped_marker.status_code == 400
    assert escaped_marker.content.decode() == 'Unknown operation named "\ufffd".'

    assert echoed.status_code == 400
    assert echoed.content.decode() == f'Unknown operation named "{cafe}".'


@pytest.mark.django_db
def test_the_marker_check_is_scoped_to_the_two_control_documents():
    """A replacement marker outside ``operations`` / ``map`` is none of the package's business.

    The check exists because those two fields are JSON documents the package
    parses. Any other form field is application data Django decoded under its own
    rules, and refusing a request over one would be the package inventing a
    contract about somebody else's field - so the same undecodable byte that gets
    a request refused in ``operations`` passes through untouched in a neighbouring
    field, and the operation still executes.
    """
    seed_data(1)
    fields = [*_multipart_fields("operations", _operations_bytes()), ("junk", b"\x80\x80")]

    response = _post_multipart(Client(), "/graphql/", fields)

    assert response.status_code == 200
    assert response.json()["data"] == {"__typename": "Query"}


#: The exploit body for a middleware-forced form encoding: a raw Latin-1
#: ``0xe9``, which is not
#: valid UTF-8 on its own. Under the Latin-1 decode the middleware forces it
#: becomes an ordinary character with **no** replacement marker, so the loss
#: detector is structurally blind to it and the control document reaches
#: ``json.loads`` non-UTF-8-decoded. Under UTF-8 it would have become ``U+FFFD``
#: and the marker check would have caught it - which is exactly why the encoding
#: gate has to read the value Django will really use.
_LATIN1_CONTROL_DOCUMENT = _operations_bytes(note=b"\xe9")


@pytest.mark.django_db
def test_a_middleware_set_request_encoding_is_not_masked_by_a_declared_utf8_charset():
    """The deployment the gate exists for, on the shipped mount.

    The wire contract is re-breakable behind one line of consumer
    middleware. ``HttpRequest.parse_file_upload`` hands ``MultiPartParser`` nothing
    but ``request.encoding``, and ``content_params`` is never re-read at parse
    time - so a client declaring ``charset=utf-8`` while a middleware has assigned
    ``request.encoding = "iso-8859-1"`` got the declaration validated and the
    override applied. The client picked which value the gate consulted.

    Three answers make this a statement about the encoding rung rather than about
    the body:

    * an ordinary ASCII control document, refused under the middleware. Nothing is
      wrong with these bytes - the same request without the middleware is the
      control below - so only the effective-encoding condition can be refusing it;
    * the same request with the middleware removed, ``200``. That is what stops the
      first answer from passing for the wrong reason;
    * the exploit body itself: a raw Latin-1 byte in ``operations``, refused. It
      is the shape the marker check cannot see, because a Latin-1 decode never
      fails (proved at the package tier in
      ``tests/test_views.py::test_a_declared_utf8_charset_does_not_mask_a_middleware_set_request_encoding``).

    Run against fakeshop's real ``/graphql/`` - the shipped mount - because the
    whole subject is a deployment shape.
    """
    seed_data(1)
    ascii_fields = _multipart_fields("operations", _operations_bytes())
    latin1_fields = _multipart_fields("operations", _LATIN1_CONTROL_DOCUMENT)

    with _with_a_middleware_that_sets_the_encoding():
        refused_ascii = _post_multipart(Client(), "/graphql/", ascii_fields, charset="utf-8")
        refused_latin1 = _post_multipart(Client(), "/graphql/", latin1_fields, charset="utf-8")

    control = _post_multipart(Client(), "/graphql/", ascii_fields, charset="utf-8")

    _assert_multipart_control_document_refused(refused_ascii)
    _assert_multipart_control_document_refused(refused_latin1)

    assert control.status_code == 200
    assert control.json()["data"] == {"__typename": "Query"}


async def test_the_async_view_is_not_masked_by_a_declared_utf8_charset_either():
    """The async colour of the encoding gate, from the one shared mixin method.

    The gate lives on ``_RequestBodyBoundaryMixin`` and is called from each
    transport's own ``run``, so it is a seam where a fix can silently apply to one
    transport only - the same reason every other multipart row in this file has an
    async twin. The control in the same row is the identical request with the
    middleware removed.
    """
    fields = _multipart_fields("operations", _LATIN1_CONTROL_DOCUMENT)

    with override_settings(ROOT_URLCONF=__name__):
        with _with_a_middleware_that_sets_the_encoding():
            refused = await _post_multipart(
                AsyncClient(),
                "/async-multipart/",
                fields,
                charset="utf-8",
            )
        control = await _post_multipart(
            AsyncClient(),
            "/async-multipart/",
            _multipart_fields("operations", _operations_bytes()),
            charset="utf-8",
        )

    _assert_multipart_control_document_refused(refused)

    assert control.status_code == 200
    assert control.json()["data"] == {"__typename": "Query"}


@pytest.mark.django_db
def test_a_project_that_reconfigured_default_charset_is_refused_unless_the_client_declares_utf8():
    """The third rung of the effective encoding, live, and its exact boundary.

    ``MultiPartParser.__init__`` resolves ``encoding or
    settings.DEFAULT_CHARSET``, so a project that reconfigures ``DEFAULT_CHARSET``
    away from UTF-8 changes how every undeclared multipart form is decoded and the
    endpoint's promise quietly stops being true. It is refused instead.

    The second answer is the part a "every value in sight must be UTF-8" reading
    gets wrong, and it is measured Django behaviour rather than a preference: with
    ``DEFAULT_CHARSET`` at Latin-1 and the client declaring ``charset=utf-8``,
    ``_set_content_type_params`` promotes ``utf-8`` onto ``request.encoding``,
    ``MultiPartParser`` receives ``utf-8``, and the form genuinely IS decoded as
    UTF-8 - so refusing it would refuse a request Django handles exactly as the
    contract promises.

    The control document is deliberately ASCII: ``RequestFactory.generic``
    transcodes its payload through ``force_bytes(data, settings.DEFAULT_CHARSET)``,
    so a non-ASCII byte in the body would be rewritten by the test client under
    this override and the row would be measuring its own harness.
    """
    seed_data(1)
    fields = _multipart_fields("operations", _operations_bytes())

    with override_settings(DEFAULT_CHARSET="iso-8859-1"):
        refused = _post_multipart(Client(), "/graphql/", fields)
        accepted = _post_multipart(Client(), "/graphql/", fields, charset="utf-8")

    _assert_multipart_control_document_refused(refused)

    assert accepted.status_code == 200
    assert accepted.json()["data"] == {"__typename": "Query"}


@pytest.mark.django_db
def test_a_get_carrying_a_stray_multipart_content_type_still_serves_the_query():
    """The encoding gate is scoped to the forms Django decodes.

    ``HttpRequest._load_post_and_files`` installs an empty ``QueryDict`` without
    parsing anything unless the method is ``POST``, so a stale
    ``multipart/form-data`` ``Content-Type`` on a GET - a client reusing a previous
    request's headers - describes a form nothing will decode, and this endpoint
    reads no body on GET at all. It used to be answered ``400``, which made the
    mixin's own "**GET.** A no-op" sentence false and refused a query Django would
    have served from the query string.

    The header is passed as a raw WSGI ``CONTENT_TYPE`` rather than through a body,
    because that is the only way to put a content type on a bodyless GET:
    ``RequestFactory.generic`` populates ``CONTENT_TYPE`` only ``if data``.
    """
    seed_data(1)
    query = {"query": _TYPENAME}
    stray = _multipart_content_type("iso-8859-1")

    response = Client().get("/graphql/", query, CONTENT_TYPE=stray)
    control = Client().get("/graphql/", query)

    for answer in (response, control):
        assert answer.status_code == 200, answer.content
        assert answer.json()["data"] == {"__typename": "Query"}


# ===========================================================================
# The declared multipart cap runs BEFORE Django's CSRF middleware reads
# ``request.POST``. Every row here uses
# ``Client(enforce_csrf_checks=True)`` - so
# ``CsrfViewMiddleware`` is live rather than short-circuited, and the ordering
# witness is the upload-handler sentinel rather than the status code.
# ===========================================================================


@pytest.mark.django_db
def test_an_over_cap_multipart_request_is_refused_before_djangos_parser_runs():
    """The ``413`` precedes ``MultiPartParser`` and every upload handler.

    The defect this closes is an ordering one, not a status one.
    ``CsrfViewMiddleware.process_view`` reads
    ``request.POST.get("csrfmiddlewaretoken", "")`` for **every** cookie-bearing
    POST - even one that will authenticate with the ``X-CSRFToken`` header - and it
    runs before the view, so on a multipart request Django had already parsed the
    form and invoked the project's upload handlers by the time the package's
    declared-size gate could refuse it. The old row could not see that: it used a
    plain ``Client``, whose CSRF checks are disabled, so the middleware exited
    before touching ``request.POST``.

    Here CSRF is enforced for real, with a valid cookie/header token, so
    ``process_view`` genuinely wants the form - and the upload sentinel stays
    EMPTY. The under-cap control in the same row is what makes that emptiness
    evidence rather than an absent instrument: the identical request under the cap
    fires the sentinel and executes.

    Deliberately run against fakeshop's OWN ``/graphql/`` - the shipped mount,
    wrapped in ``ensure_csrf_cookie`` - with the cap turned down through the
    project-wide setting rung. A probe mount would prove the ordering for a
    wrapper written in this file; the shipped mount proves it for the deployment
    shape the README documents, including that ``functools.wraps`` carries the
    ``csrf_exempt`` mark through a consumer's own view decorator.
    """
    seed_data(1)
    token = _csrf_token()
    over = _multipart_fields("operations", _operations_bytes(note=b"y" * (_TINY_CAP * 4)))
    under = _multipart_fields("operations", _operations_bytes())

    _UPLOAD_EVENTS.clear()
    with (
        override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"MAX_REQUEST_BODY_BYTES": _TINY_CAP}),
        _recording_upload_handlers(),
    ):
        refused = _post_multipart(
            Client(enforce_csrf_checks=True),
            "/graphql/",
            over,
            token=token,
        )
        refused_events = list(_UPLOAD_EVENTS)

        accepted = _post_multipart(
            Client(enforce_csrf_checks=True),
            "/graphql/",
            under,
            token=token,
        )

    _assert_body_limit_response(refused)
    assert refused_events == []

    assert accepted.status_code == 200
    assert accepted.json()["data"] == {"__typename": "Query"}
    assert "handle_raw_input" in _UPLOAD_EVENTS
    _UPLOAD_EVENTS.clear()


async def test_the_async_view_also_refuses_before_djangos_parser_runs():
    """The async colour of the ordering guarantee, including the ``csrf_protect`` await.

    ``csrf_protect`` is ``decorator_from_middleware(CsrfViewMiddleware)``, and it
    only awaits the view it wraps when the wrapped callable is itself a coroutine
    function - so this row is the live proof that the async continuation was wired
    to the async branch. If it had not been, the CSRF decorator would have handed a
    coroutine to ``process_response`` in place of a response and the request would
    have failed rather than answered ``200``.

    **A known asymmetry with its sync twin, recorded rather than left to be
    discovered.** The sync row drives fakeshop's real
    ``/graphql/`` mount; this one drives ``_async_cap_tiny_multipart_view``, a probe
    mount decorated with ``_carrying_the_packages_csrf_mark`` - i.e. exactly the
    hand-written, non-``functools.wraps`` wrapper shape that DROPS the mark and
    therefore loses the ordering, repaired by copying the mark off the package.
    There is no shipped async fakeshop mount to use instead, so this is the
    strongest available async evidence, but it is evidence about the *mechanism*
    and not about a deployment shape: only the sync row is deployment-shape
    evidence. Do not read a green run here as proof that an arbitrary async mount
    keeps the ordering.
    """
    token = _csrf_token("/async-multipart-tiny/")
    over = _multipart_fields("operations", _operations_bytes(note=b"y" * (_TINY_CAP * 4)))
    under = _multipart_fields("operations", _operations_bytes())

    _UPLOAD_EVENTS.clear()
    with override_settings(ROOT_URLCONF=__name__), _recording_upload_handlers():
        refused = await _post_multipart(
            AsyncClient(enforce_csrf_checks=True),
            "/async-multipart-tiny/",
            over,
            token=token,
        )
        refused_events = list(_UPLOAD_EVENTS)

        accepted = await _post_multipart(
            AsyncClient(enforce_csrf_checks=True),
            "/async-multipart-tiny/",
            under,
            token=token,
        )

    _assert_body_limit_response(refused)
    assert refused_events == []

    assert accepted.status_code == 200
    assert accepted.json()["data"] == {"__typename": "Query"}
    assert "handle_raw_input" in _UPLOAD_EVENTS
    _UPLOAD_EVENTS.clear()


def _csrf_matrix_paths(token):
    """The six CSRF directions of the row below, as keyword sets for ``_post_multipart``.

    Named once so the sync and async rows run the *same* matrix rather than two
    hand-copied ones that could drift apart - which is the failure mode the two
    ``run`` overrides make possible in the first place.
    """
    fields = _multipart_fields("operations", _operations_bytes())
    return (
        ("untokened", {"fields": fields}),
        ("headered", {"fields": fields, "token": token}),
        (
            "wrong_token",
            {
                "fields": fields,
                "token": token,
                "send_header": False,
                "headers": {"x-csrftoken": "n0tth3r1ghtt0k3n" * 4},
            },
        ),
        (
            "formed",
            {
                "fields": [*fields, ("csrfmiddlewaretoken", token.encode())],
                "token": token,
                "send_header": False,
            },
        ),
        (
            "hostile_origin",
            {"fields": fields, "token": token, "headers": {"origin": "https://evil.example"}},
        ),
        ("insecure_referer", {"fields": fields, "token": token, "secure": True}),
    )


def _assert_csrf_matrix(answers, custom_failure):
    """The one set of assertions both transports' rows make."""
    for name in (
        "untokened",
        "wrong_token",
        "hostile_origin",
        "insecure_referer",
    ):
        assert answers[name].status_code == 403, name
        _assert_no_graphql_envelope(answers[name])

    for name in ("headered", "formed"):
        assert answers[name].status_code == 200, name
        assert answers[name].json()["data"] == {"__typename": "Query"}, name

    assert custom_failure.status_code == 403
    assert custom_failure.content == b"probe-csrf-failure"


@pytest.mark.django_db
def test_a_within_cap_request_still_faces_djangos_complete_csrf_check():
    """The exemption is an ordering mechanism: everything past the gate still gets CSRF.

    Six directions plus the failure-view override, all of them Django's own
    implementation running from inside the view instead of ahead of it:

    * no token at all -> ``403``, and no GraphQL envelope;
    * a wrong header token -> ``403``;
    * the header token -> ``200``;
    * the ``csrfmiddlewaretoken`` FORM field, with no header -> ``200``. This is the
      path ``_check_token`` reads ``request.POST`` for in the first place, so it
      would be the first casualty of an ordering fix that skipped the form;
    * a hostile ``Origin`` with a valid token -> ``403``;
    * HTTPS with a valid token and no ``Referer`` -> ``403``, the strict-Referer
      branch that only runs on a secure request;
    * a custom ``CSRF_FAILURE_VIEW`` -> that view's own response body, which proves
      the setting is still consulted from the re-entry point.

    Together these are what makes "``csrf_exempt`` on the outer callback" a claim
    about ORDER rather than about protection: nothing in the CSRF implementation
    stopped running, it just stopped running before the body boundary.
    """
    seed_data(1)
    token = _csrf_token()

    answers = {
        name: _post_multipart(
            Client(enforce_csrf_checks=True),
            "/graphql/",
            keywords.pop("fields"),
            **keywords,
        )
        for name, keywords in _csrf_matrix_paths(token)
    }
    with override_settings(CSRF_FAILURE_VIEW=f"{__name__}._csrf_failure_probe"):
        custom_failure = _post_multipart(
            Client(enforce_csrf_checks=True),
            "/graphql/",
            _multipart_fields("operations", _operations_bytes()),
        )

    _assert_csrf_matrix(answers, custom_failure)


async def test_the_async_view_faces_the_same_complete_csrf_check():
    """The async colour of the whole CSRF matrix, through the awaited continuation.

    The two ``run`` overrides differ only in ``async`` / ``await``, and the CSRF
    re-entry is the part of them that is NOT shared code: ``csrf_protect`` picks an
    awaiting or a non-awaiting wrapper by inspecting the callable it was handed, so
    the async view rides a second continuation function. A wrong pairing there
    would hand a coroutine to ``process_response`` in place of a response, so every
    ``200`` below is also a statement about that wiring.
    """
    token = _csrf_token("/async-multipart/")

    with override_settings(ROOT_URLCONF=__name__):
        answers = {}
        for name, keywords in _csrf_matrix_paths(token):
            answers[name] = await _post_multipart(
                AsyncClient(enforce_csrf_checks=True),
                "/async-multipart/",
                keywords.pop("fields"),
                **keywords,
            )
        with override_settings(CSRF_FAILURE_VIEW=f"{__name__}._csrf_failure_probe"):
            custom_failure = await _post_multipart(
                AsyncClient(enforce_csrf_checks=True),
                "/async-multipart/",
                _multipart_fields("operations", _operations_bytes()),
            )

    _assert_csrf_matrix(answers, custom_failure)


def _without_the_global_csrf_middleware():
    """``override_settings`` with ``CsrfViewMiddleware`` taken out of ``MIDDLEWARE``.

    Derived from the project's real ``MIDDLEWARE`` rather than a hand-written list,
    so the row removes exactly one entry and leaves fakeshop's session, auth and
    security middleware in place.
    """
    remaining = [entry for entry in settings.MIDDLEWARE if "CsrfViewMiddleware" not in entry]
    assert len(remaining) == len(settings.MIDDLEWARE) - 1, settings.MIDDLEWARE
    return override_settings(MIDDLEWARE=remaining)


@pytest.mark.django_db
def test_the_endpoint_stays_csrf_protected_with_the_global_middleware_removed():
    """The invariant the re-entry buys: protection that does not depend on ``MIDDLEWARE``.

    This is the row that distinguishes the fix from a bypass in the one direction
    nothing else can. With ``CsrfViewMiddleware`` deleted from the project entirely,
    a consumer who mounts the package view still cannot post to it without a valid
    token, because the continuation inside ``run`` is package-owned, unconditional,
    and carries Django's real implementation with it. A reordering that had merely
    disabled the check would answer ``200`` to all three.

    Both transports, because the sync and async ``csrf_protect`` wrappers are
    different code paths in Django - and the async half is driven from the same
    ``asyncio`` entry point the ``_asgi_post`` rows already use rather than an
    ``async def`` test, so one row can state the invariant for both.
    """
    seed_data(1)
    token = _csrf_token()
    fields = _multipart_fields("operations", _operations_bytes())
    wrong = "n0tth3r1ghtt0k3n" * 4

    async def async_answers():
        answers = {}
        for name, keywords in (
            ("untokened", {}),
            (
                "wrong_token",
                {"token": token, "send_header": False, "headers": {"x-csrftoken": wrong}},
            ),
            ("headered", {"token": token}),
        ):
            answers[name] = await _post_multipart(
                AsyncClient(enforce_csrf_checks=True),
                "/async-multipart/",
                fields,
                **keywords,
            )
        return answers

    with _without_the_global_csrf_middleware():
        sync_answers = {
            "untokened": _post_multipart(Client(enforce_csrf_checks=True), "/graphql/", fields),
            "wrong_token": _post_multipart(
                Client(enforce_csrf_checks=True),
                "/graphql/",
                fields,
                token=token,
                send_header=False,
                headers={"x-csrftoken": wrong},
            ),
            "headered": _post_multipart(
                Client(enforce_csrf_checks=True),
                "/graphql/",
                fields,
                token=token,
            ),
        }
        with override_settings(ROOT_URLCONF=__name__):
            async_answers_ = asyncio.run(async_answers())

    for answers in (sync_answers, async_answers_):
        for name in ("untokened", "wrong_token"):
            assert answers[name].status_code == 403, name
            _assert_no_graphql_envelope(answers[name])
        assert answers["headered"].status_code == 200
        assert answers["headered"].json()["data"] == {"__typename": "Query"}


def test_the_shipped_chain_supplies_the_ordering_for_fakeshops_real_mount():
    """The deployed arrangement is the chain one, and this row is what says so.

    Every other ordering row in this file runs against a probe mount, and a probe
    mount deliberately carries only the exemption (see
    ``_carrying_the_packages_csrf_mark``), so the middleware declines it and those
    rows measure the view-local fallback. Nothing there can fail if the shipped
    chain silently stopped being the chain arrangement - the fallback would simply
    absorb it, cap intact, and the only observable loss would be that the project's
    configured CSRF class no longer runs on this endpoint. That is precisely the
    failure the middleware exists to prevent, so it gets a row of its own.

    Three facts, and the third is the one a settings edit would break: the boundary
    entry is installed, it precedes the CSRF entry, and the callback the URL resolver
    hands ``process_view`` for the real ``/graphql/`` mount is one the middleware
    actually recognizes. ``ensure_csrf_cookie`` wraps that mount, so the third fact
    is also the assertion that ``functools.wraps`` carries BOTH ordering marks
    through a real decorator rather than only the exemption.
    """
    chain = list(settings.MIDDLEWARE)
    boundary = (
        "django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware"
    )
    csrf = "django.middleware.csrf.CsrfViewMiddleware"
    assert boundary in chain, "fakeshop no longer installs the boundary middleware"
    assert csrf in chain
    assert chain.index(boundary) < chain.index(csrf), (
        "the boundary entry must precede the CSRF entry - the package refuses the "
        "reverse order at startup, so this ordering is load-bearing"
    )

    callback = resolve("/graphql/").func
    assert getattr(callback, _BOUNDARY_MARKER, False), (
        "the real mount's callback lost the boundary marker, so the chain would "
        "decline it and fall back to the view-local arrangement"
    )
    assert _package_view_instance(callback) is not None, (
        "the middleware no longer recognizes the real mount"
    )


@pytest.mark.django_db
def test_the_chain_applies_boundary_state_derived_during_view_setup():
    """The middleware instance follows the same setup lifecycle as the real view.

    ``View.as_view`` calls ``setup(request, *args, **kwargs)`` before dispatch, and
    consumer subclasses may derive request-local state there. This mount takes its
    body cap from the resolved route keyword, so a pre-setup boundary sees no cap at
    all: it accepts and stamps the request, then the real instance sets the eight-byte
    cap but skips it because of that stamp. Before the fix this valid GraphQL document
    therefore executed and answered ``200``; the ``413`` proves the chain applied the
    setup-derived limit before it claimed the boundary had run.
    """
    seed_data(1)
    _SETUP_CALLS.clear()

    with override_settings(ROOT_URLCONF=__name__):
        client = Client()
        refused = _post(client, "{ ping }", path="/setup-limited/8/")
        accepted = _post(client, "{ ping }", path="/setup-limited/1024/")

    _assert_body_limit_response(refused)
    assert accepted.status_code == 200
    assert accepted.json()["data"] == {"ping": "pong"}
    assert _SETUP_CALLS == ["/setup-limited/8/", "/setup-limited/1024/"], (
        "the middleware and callback must share one prepared view lifecycle"
    )


#: The methods RFC 9110 calls safe, verbatim the tuple
#: ``CsrfViewMiddleware.process_view`` returns early for. Named so the recorder below
#: defers on exactly the requests the base class does not check.
_SAFE_METHODS = (
    "GET",
    "HEAD",
    "OPTIONS",
    "TRACE",
)


class _RecordingCsrfMiddleware(CsrfViewMiddleware):
    """The project's own CSRF class, standing in fakeshop's chain and recording its work.

    A subclass rather than a mock because the question is which class the chain hands
    the request to, and only a class of the project's own can answer it: Django's base
    implementation accepts a test-client request and is indistinguishable from one it
    never saw. It records and then delegates, so the endpoint keeps behaving exactly
    as it does in the shipped chain - the row's second half depends on that.

    Both deferrals are honoured for the same reason
    ``tests/test_views.py::_RejectingCsrfMiddleware`` honours them: a safe method is
    not something ``CsrfViewMiddleware`` checks and an exempt callback is one it
    declines, so recording only what is left is what turns ``calls`` into evidence
    about the exemption having withdrawn itself.
    """

    calls: list[str] = []

    def process_view(
        self,
        request,
        callback,
        callback_args,
        callback_kwargs,
    ):
        """Record a checkable callback, then let the base class decide the request."""
        if request.method not in _SAFE_METHODS and not getattr(callback, "csrf_exempt", False):
            type(self).calls.append(request.path)
        return super().process_view(request, callback, callback_args, callback_kwargs)


def _with_the_projects_own_csrf_class():
    """``override_settings`` swapping fakeshop's CSRF entry for the recording subclass.

    Derived from the project's real ``MIDDLEWARE`` the same way
    :func:`_without_the_global_csrf_middleware` is, so the row changes exactly one
    entry and keeps the boundary middleware where the shipped chain puts it - which is
    the whole subject of the row below.
    """
    entry = f"{__name__}._RecordingCsrfMiddleware"
    swapped = [
        entry if "CsrfViewMiddleware" in candidate else candidate
        for candidate in settings.MIDDLEWARE
    ]
    assert swapped.count(entry) == 1, settings.MIDDLEWARE
    return override_settings(MIDDLEWARE=swapped)


@pytest.mark.django_db
def test_the_configured_csrf_class_checks_fakeshops_real_mount_behind_the_boundary():
    """The behavioral half of the row above: the exemption really does withdraw itself.

    ``test_the_shipped_chain_supplies_the_ordering_for_fakeshops_real_mount`` proves
    the preconditions - the entry is installed, it precedes CSRF, the callback is
    recognized - and a request is what turns them into the property they exist for:
    the project's *configured* CSRF class is handed this endpoint's callback in a
    checkable state, which happens only because ``process_view`` stamped the request
    and ``_boundary_ordering.py::_CsrfOrderingExemption`` therefore answered false for
    it. Nothing else here can fail if that stops happening: the callback would simply
    be skipped again, the view's own continuation would supply the check, and every
    status code in this file would stay exactly as it is.

    So the empty-or-not call log is the whole witness, and the ``200`` is what keeps
    it honest - a chain that recorded the callback while refusing the request would
    prove the class ran and nothing about the endpoint still working behind it.
    """
    seed_data(1)
    _RecordingCsrfMiddleware.calls = []

    with _with_the_projects_own_csrf_class():
        response = _post(Client(), _TYPENAME)

    assert response.status_code == 200
    assert response.json()["data"] == {"__typename": "Query"}
    assert _RecordingCsrfMiddleware.calls == ["/graphql/"], (
        "the configured CSRF class never saw the real mount's callback, so the "
        "exemption did not withdraw itself and the chain is not supplying the ordering"
    )


@pytest.mark.django_db
def test_the_csrf_cookie_and_vary_header_survive_the_outer_exemption():
    """``csrf_exempt`` skips ``process_view`` only - the cookie machinery is untouched.

    Worth its own row because the exemption sounds like it should break exactly
    this: fakeshop's mount wraps the view in ``ensure_csrf_cookie`` so the IDE GET
    hands a browser the ``csrftoken`` cookie Strawberry's GraphiQL then echoes back.
    That cookie is set by ``CsrfViewMiddleware.process_request`` /
    ``process_response``, neither of which the exemption touches - and
    ``_set_csrf_cookie`` is what patches ``Vary: Cookie``, so both are asserted
    together on the one request a browser actually makes first.
    """
    seed_data(1)

    response = Client().get("/graphql/", HTTP_ACCEPT="text/html")

    assert response.status_code == 200
    assert "csrftoken" in response.cookies
    assert "Cookie" in response.headers.get("Vary", "")


@pytest.mark.django_db
def test_an_accepted_file_upload_still_streams_through_djangos_upload_handlers():
    """The un-broken direction: Django keeps owning multipart framing and files.

    The whole design constraint on both fixes was that Django's parser, limits and
    upload handlers stay in charge - no private multipart parser, no double read,
    no ``handle_raw_input`` takeover - so the accepted path has to be asserted too,
    not just the refused one. A real file part on a request that passes the
    boundary reaches the project's handler chain through ``new_file`` and
    ``receive_data_chunk``, and the file lands in ``request.FILES`` where
    upstream's ``replace_placeholders_with_files`` looks for it.

    The end-to-end ``Upload``-scalar mutations in ``test_uploads_api.py`` run
    against this same package mount, so they are the second half of this proof.
    """
    seed_data(1)
    token = _csrf_token()
    fields = _multipart_fields("operations", _operations_bytes())

    _UPLOAD_EVENTS.clear()
    with _recording_upload_handlers():
        response = _post_multipart(
            Client(enforce_csrf_checks=True),
            "/graphql/",
            fields,
            files=[("0", "note.txt", b"streamed through django")],
            token=token,
        )

    assert response.status_code == 200
    assert response.json()["data"] == {"__typename": "Query"}
    assert "handle_raw_input" in _UPLOAD_EVENTS
    assert "new_file" in _UPLOAD_EVENTS
    assert "receive_data_chunk" in _UPLOAD_EVENTS
    _UPLOAD_EVENTS.clear()
