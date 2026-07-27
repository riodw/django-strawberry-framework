"""Live ``/graphql/`` transport-boundary acceptance tests (spec-065 Slices 1-2).

The S1 HTTP-boundary tier: every proof that Django's real request lifecycle
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

Test plan rows 13-17 - the whole S2 body-cap matrix (Decision 7) - land here
too, against three more mounts of the package view that differ only in their
``max_request_body_bytes``: the below / at / above boundary trio, what an absent
or understated ``Content-Length`` can and cannot do on each transport, a
cumulative multi-fragment body, malformed JSON on both sides of the cap,
multipart, the parse-and-execution witnesses, which of the two ceilings fired,
and the three precedence rungs. Row 18 (the py3.10 / Django 5.2 floor) is a
maintainer-invoked run of this same file, not a separate row.

Test plan rows 19 / 22 / 23 add one more async row (Slice 3). The strict UTF-8
wire contract (Decision 9) is enforced in
``views.py::_RequestBodyBoundaryMixin.parse_json``, which both views inherit, so
the async transport must reject UTF-16 and a leading UTF-8 BOM exactly as the sync
``/graphql/`` rows in ``test_products_api.py`` do. It lives here rather than beside
those rows because this module already owns the ``/async-graphql/`` mount and the
``AsyncClient`` scaffolding it needs.

The final section is the review's High-2 remediation: the wire contract is package
policy on the *view*, not one of the upstream-bug patches, so it is asserted on
both transports with ``APPLY_UPSTREAM_PATCHES = {"strawberry": False}`` in effect -
and the workaround the switch really does own is asserted to be genuinely off in
the same state, so the ownership split cannot be satisfied by moving everything
somewhere ungated. Its last rows take the switch off entirely
(``APPLY_UPSTREAM_PATCHES = False``, both patch modules un-installed), which is the
state the round-1 review found the sync transport answering ``500`` in: it is now
the same controlled ``400``, and one row reads all four answers across two mounts
and two patch states so that constancy is attributable to the package view rather
than to a patch that was quietly still installed.

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
from apps.products import models
from apps.products.services import create_users, seed_data
from cross_web import DjangoHTTPRequestAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.handlers.asgi import ASGIHandler
from django.middleware.csrf import get_token
from django.test import AsyncClient, Client, RequestFactory, override_settings
from django.urls import include, path
from graphql_client import assert_graphql_data, post_graphql
from strawberry.django.views import GraphQLView as UpstreamGraphQLView
from strawberry.http.base import BaseView

from django_strawberry_framework import _cross_web_patches as cross_web_patches
from django_strawberry_framework import _strawberry_patches as strawberry_patches
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


async def _async_graphql_view(request, *args, **kwargs):
    """The async twin, mounted so Django dispatches it on the event loop."""
    from config.schema import schema

    view = AsyncDjangoGraphQLView.as_view(schema=schema)
    return await view(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Slice-2 scaffolding: three more mounts of the package view, differing only in
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


def _capped_view(view_class, limit):
    """A request-time-resolving mount of ``view_class`` with the cap pinned.

    Resolving the schema per request mirrors ``_ide_off_view`` above: it keeps
    every probe mount pointed at the schema the per-test reload fixture just
    rebuilt instead of one captured at import.
    """

    def view(request, *args, **kwargs):
        from config.schema import schema

        built = view_class.as_view(schema=schema, max_request_body_bytes=limit)
        return built(request, *args, **kwargs)

    return view


async def _async_cap_tiny_view(request, *args, **kwargs):
    """The async twin under the tiny cap, so the ``async def run`` override is proven live.

    Spelled out rather than produced by ``_capped_view`` for the same reason
    ``_async_graphql_view`` is: the ``await`` is the difference, and one mount
    needs it.
    """
    from config.schema import schema

    view = AsyncDjangoGraphQLView.as_view(schema=schema, max_request_body_bytes=_TINY_CAP)
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
    path("async-graphql/", _async_graphql_view),
    path("cap-tiny/", _capped_view(DjangoGraphQLView, _TINY_CAP)),
    path("cap-spy/", _capped_view(_ParseSpyView, _TINY_CAP)),
    path("cap-off/", _capped_view(DjangoGraphQLView, _ROOMY_CAP)),
    path("async-cap-tiny/", _async_cap_tiny_view),
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
    from django.contrib.auth.models import Permission

    create_users(1)
    user_model = get_user_model()
    user = user_model.objects.get(username="view_category_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_category", content_type__app_label="products"),
    )
    user = user_model.objects.get(pk=user.pk)  # drop the stale per-request perm cache
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
        response = await AsyncClient().post(
            "/async-graphql/",
            data=json.dumps({"query": _TYPENAME}),
            content_type="application/json",
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
        utf16 = await client.post(
            "/async-graphql/",
            data=document.encode("utf-16"),
            content_type="application/json",
        )
        utf8_bom = await client.post(
            "/async-graphql/",
            data=b"\xef\xbb\xbf" + document.encode("utf-8"),
            content_type="application/json",
        )
        control = await client.post(
            "/async-graphql/",
            data=document,
            content_type="application/json",
        )

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
# Slice 2 (S2): the cumulative request-body cap. Test-plan rows 13-18.
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
    real byte count. On the Django 5.2 floor it is the ONLY bound at all, since
    that release's ``HttpRequest.body`` has no seekable actual-size check of its
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
    under-cap direction also pins that Slice 2 did not disturb the shipped
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
    count, per-file size, and aggregate size are audit S4's. What the view must
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
    from django.contrib.auth.models import Permission

    create_users(1)
    user_model = get_user_model()
    user = user_model.objects.get(username="view_category_1")
    user.user_permissions.add(
        Permission.objects.get(codename="add_category", content_type__app_label="products"),
    )
    user = user_model.objects.get(pk=user.pk)  # drop the stale per-request perm cache

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
    ``400``. The spec's Edge-case sentence predicting a ``413`` on the ASGI
    direction is inaccurate against both supported releases; this row pins the
    measured behavior. Deliberately WSGI-only: lowering Django's knob under the
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
        over = await client.post(
            "/async-cap-tiny/",
            data=_sized_body(_TINY_CAP * 4),
            content_type="application/json",
        )
        under = await client.post(
            "/async-cap-tiny/",
            data=_sized_body(_TINY_CAP),
            content_type="application/json",
        )

    _assert_body_limit_response(over)

    assert under.status_code == 200
    assert under.json()["data"] == {"__typename": "Query"}


# ===========================================================================
# Review High 2: the strict UTF-8 wire contract is the package VIEW's policy,
# so it does not share the ``APPLY_UPSTREAM_PATCHES`` lifecycle. These rows
# mount the package view with the Strawberry patch opted out and assert the
# policy still holds - and, separately, that the upstream-bug workaround the
# switch really does own is genuinely off in the same state.
# ===========================================================================

#: The three shapes the review names, as real request bodies. Two fail at the
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
        rejected = await client.post(
            "/async-graphql/",
            data=body,
            content_type="application/json",
        )
        control = await client.post(
            "/async-graphql/",
            data=json.dumps({"query": _TYPENAME}),
            content_type="application/json",
        )

    assert rejected.status_code == 400

    assert control.status_code == 200
    assert control.json()["data"] == {"__typename": "Query"}


@contextlib.contextmanager
def _every_upstream_patch_opted_out():
    """Run the block in the state the BROAD ``APPLY_UPSTREAM_PATCHES = False`` produces.

    The sibling helper simulates ``{"strawberry": False}`` and deliberately leaves
    the ``cross_web`` half installed. This one takes both halves out, which is a
    materially different state and the one the review's residual finding was
    measured in: with ``cross_web`` un-installed, upstream's sync
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
    (review W3-2, measured) because upstream's adapter decoded them inside a
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
      the deliberate scope of the ownership split (spec-065 review High 2), pinned
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
        unguarded = Client(raise_request_exception=False).post(
            "/graphql/",
            data=scalar,
            content_type="application/json",
        )

    guarded = _post_bytes(Client(), scalar)

    assert unguarded.status_code == 500

    assert guarded.status_code == 400
    assert b"request body" in guarded.content
