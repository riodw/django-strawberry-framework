"""The spec-042 ``DebugToolbarMiddleware`` suite - both dependency states, real requests.

Placement (spec-042 Decision 9, honoring the ``test_query/README.md`` coverage
rule): the live-first mandate sends a test to ``examples/fakeshop/test_query/``
when a package line is reachable by a real GraphQL query **through the
example's shipped configuration** - and no ``middleware/debug_toolbar.py`` line
is: fakeshop's shipped settings deliberately carry no ``debug_toolbar`` app, no
toolbar middleware, and no show-toolbar override, so the middleware exists in
the request path only under this file's per-test settings overrides (package
machinery, not the example's consumer surface). The tests are NOT structural
for it - the toolbar-present group drives fakeshop's REAL ``/graphql/`` URL
(the real GraphiQL HTML render through the real ``ensure_csrf_cookie``
decorator, and a real SQL-emitting products operation through the real
optimizer) via ``django.test.Client``, with the acceptance suites' schema
reload discipline (``schema_reload.reload_all_project_schemas()`` on fixture
setup, before any URLconf step).

The toolbar-absent path simulates absence with the importlib-compatible
``sys.modules["debug_toolbar"] = None`` sentinel, NOT the router/DRF
``builtins.__import__`` block (spec-042 Revision 5): ``require_debug_toolbar()``
is a ``require_optional_module`` wrapper, i.e. an ``importlib.import_module``
call that never consults ``builtins.__import__``, so a ``__import__`` block
would re-import the still-installed toolbar and the raise would come from a
later hintless statement-import. The eviction + two-sided restore discipline
(modules AND the parent-package attribute) is unchanged from
``tests/rest_framework/test_soft_dependency.py``.

debug-toolbar 7.0.0's ``middleware`` import chain defines a Django model
(``HistoryEntry``), so the FIRST leaf import in a process must happen while
``"debug_toolbar"`` is in ``INSTALLED_APPS`` - the ``toolbar_leaf`` fixture
owns that, keeping the targeted units and absence tests order-independent
under pytest-xdist.
"""

from __future__ import annotations

import contextlib
import importlib
import json
import sys
from pathlib import Path

import pytest
import schema_reload
from apps.products.services import seed_data
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, StreamingHttpResponse
from django.test import Client, RequestFactory, modify_settings, override_settings
from django.urls import reverse

import django_strawberry_framework
from tests._soft_dependency import evicted_modules, simulated_absence

_LEAF = "django_strawberry_framework.middleware.debug_toolbar"
_PARENT = "django_strawberry_framework.middleware"
_PACKAGE_MIDDLEWARE = f"{_LEAF}.DebugToolbarMiddleware"
_STOCK_MIDDLEWARE = "debug_toolbar.middleware.DebugToolbarMiddleware"
_TEST_URLCONF = "tests.middleware.debug_toolbar_urls"

# The verified debug-toolbar floor; the install hint must name it. RE-TYPED
# literal (the ``_HINT_SUBSTRING`` drift-catch discipline - place 3 of the
# three-places-that-must-agree; place 1 is the ``[dependency-groups].dev``
# specifier, place 2 is ``_DEBUG_TOOLBAR_INSTALL_HINT``).
_HINT_SUBSTRING = "django-debug-toolbar>=7.0.0"

# A distinctive substring of the package's appended bridge asset: present only
# when the middleware's HTML branch fired, never in stock toolbar markup.
_TEMPLATE_MARKER = "Response.prototype.json"

# ``render_panel``'s miss fallback (debug-toolbar 7.0.0): a 200 JSON response
# with NON-empty content, so Test 6 must pin its absence, not just shape.
_PANEL_FALLBACK = "isn't available anymore"

# A NAMED operation: a non-null ``operationName`` in the JSON envelope requires
# a named operation document (an anonymous ``{ ... }`` document plus a non-null
# ``operationName`` fails GraphQL validation before proving anything).
_TOOLBAR_ITEMS_QUERY = """
query ToolbarItems {
  allItems(first: 1) {
    edges { node { name category { name } } }
  }
}
"""

_INTROSPECTION_QUERY = "query IntrospectionQuery { __schema { queryType { name } } }"


def _post_graphql(client, query, operation_name=None):
    """POST a GraphQL JSON envelope to fakeshop's real ``/graphql/`` URL."""
    payload = {"query": query}
    if operation_name is not None:
        payload["operationName"] = operation_name
    return client.post("/graphql/", data=json.dumps(payload), content_type="application/json")


def _content_type(response):
    """The response's media type without parameters - the middleware's own sniff.

    Mirrors the production first-segment split
    (``middleware/debug_toolbar.py::_postprocess``) so the tests key on the
    media type the branch actually inspects, not the raw header.
    """
    return response["Content-Type"].split(";")[0]


# ---------------------------------------------------------------------------
# The Decision 9 toolbar-present fixture (file-local by design - P3.1: do not
# promote to a shared helper until a second card needs the same machinery).
# ---------------------------------------------------------------------------


def _show_toolbar_always(request):
    """The always-true show-toolbar callback: independent of REMOTE_ADDR / INTERNAL_IPS."""
    return True


def _middleware_with_debug_toolbar():
    """Build MIDDLEWARE from the REAL fakeshop stack with the package path in front.

    Preserves the rest of fakeshop's stack (sessions, CSRF, auth, messages) so
    the test path stays the real request path - never an abbreviated
    replacement list. The list must never contain BOTH the stock toolbar entry
    and the package middleware (the subclass replaces the stock entry).
    """
    middleware = [m for m in settings.MIDDLEWARE if m != _STOCK_MIDDLEWARE]
    assert _PACKAGE_MIDDLEWARE not in middleware
    return [_PACKAGE_MIDDLEWARE, *middleware]


def _evict_test_urlconf():
    """Drop the test URLconf so its ``urlpatterns`` recompute under the active DEBUG."""
    sys.modules.pop(_TEST_URLCONF, None)


@contextlib.contextmanager
def _debug_toolbar_cache_state():
    """Save / clear / restore the toolbar's process-level caches (Decision 9 hygiene).

    ``show_toolbar_func_or_path`` is ``@cache``-memoized and ``DebugToolbar``
    caches ``_panel_classes`` / ``_urlpatterns`` on the class - none reset with
    a settings override, and under ``--dist loadscope`` a leaked always-true
    callback would let this module pass while a later same-worker test inherits
    it. Restore puts back the SAVED values (not ``None``), so a neighboring
    test gets back exactly the state it had.
    """
    from debug_toolbar import middleware as dt_middleware
    from debug_toolbar.toolbar import DebugToolbar

    dt_middleware.show_toolbar_func_or_path.cache_clear()
    saved_panel_classes = DebugToolbar._panel_classes
    saved_urlpatterns = DebugToolbar._urlpatterns
    DebugToolbar._panel_classes = None
    DebugToolbar._urlpatterns = None
    try:
        yield
    finally:
        dt_middleware.show_toolbar_func_or_path.cache_clear()
        DebugToolbar._panel_classes = saved_panel_classes
        DebugToolbar._urlpatterns = saved_urlpatterns


@pytest.fixture
def toolbar_client():
    """Real fakeshop requests with the toolbar's three pieces layered per-test.

    Setup order is load-bearing (Decision 9): the full-project schema reload
    runs FIRST (order-independence-by-reconstruction after any package-test
    ``registry.clear()``), the test URLconf is evicted so its ``urlpatterns``
    compute under the ``DEBUG=True`` override (pytest-django forces the suite
    to ``DEBUG=False``; ``debug_toolbar_urls()`` returns ``[]`` under it), and
    the URLconf is referenced by dotted path only.
    """
    schema_reload.reload_all_project_schemas()
    _evict_test_urlconf()
    try:
        with override_settings(DEBUG=True):
            with modify_settings(INSTALLED_APPS={"append": "debug_toolbar"}):
                with _debug_toolbar_cache_state():
                    with override_settings(
                        MIDDLEWARE=_middleware_with_debug_toolbar(),
                        ROOT_URLCONF=_TEST_URLCONF,
                        DEBUG_TOOLBAR_CONFIG={"SHOW_TOOLBAR_CALLBACK": _show_toolbar_always},
                    ):
                        yield Client()
    finally:
        _evict_test_urlconf()


@pytest.fixture
def stock_client():
    """A schema-reloaded client under fakeshop's SHIPPED settings (no toolbar)."""
    schema_reload.reload_all_project_schemas()
    return Client()


@pytest.fixture
def toolbar_leaf():
    """Import (or reuse) the leaf module with the ``debug_toolbar`` app installed.

    The first ``debug_toolbar.middleware`` import in a process defines the
    ``HistoryEntry`` model, which requires the app in ``INSTALLED_APPS`` - this
    fixture makes the targeted units and absence tests order-independent under
    pytest-xdist instead of relying on a toolbar-present test having imported
    the leaf earlier on the same worker.
    """
    with modify_settings(INSTALLED_APPS={"append": "debug_toolbar"}):
        yield importlib.import_module(_LEAF)


@pytest.fixture
def middleware(toolbar_leaf):
    """The package middleware instance the targeted units drive directly.

    Depends on ``toolbar_leaf`` so ``debug_toolbar`` stays in
    ``INSTALLED_APPS`` for the unit's lifetime; ``lambda request: None`` is the
    sync ``get_response`` the stock ``__init__`` inspects (sync -> not async
    mode). Replaces the identical hand-built instance the units repeated.
    """
    return toolbar_leaf.DebugToolbarMiddleware(lambda request: None)


# ---------------------------------------------------------------------------
# Toolbar-present: real in-process fakeshop requests (Tests 1-8).
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestToolbarPresent:
    """The toolbar-present group: real ``/graphql/`` traffic under the Decision 9 fixture."""

    def test_graphiql_page_carries_stock_handle_and_bridge_script(self, toolbar_client):
        """Test 1: the GraphiQL HTML page gets BOTH injections."""
        response = toolbar_client.get("/graphql/", HTTP_ACCEPT="text/html")
        assert response.status_code == 200
        assert _content_type(response) == "text/html"
        body = response.content.decode()
        # The stock toolbar handle: proves super()._postprocess ran and the
        # stock pipeline is intact.
        assert 'id="djDebug"' in body
        # The package's appended template script: proves the HTML branch fired.
        assert _TEMPLATE_MARKER in body
        if "Content-Length" in response:
            assert int(response["Content-Length"]) == len(response.content)

    def test_no_toolbar_baseline_under_shipped_settings(self, stock_client):
        """Test 2: stock fakeshop settings stay toolbar-free (stable behavior, not bytes).

        No "package middleware module not imported" assertion: under
        ``--dist loadscope`` an earlier toolbar-present test on the same worker
        legitimately leaves the leaf in ``sys.modules`` while this response is
        perfectly clean; import-surface guarantees belong to the absence tests.
        """
        response = stock_client.get("/graphql/", HTTP_ACCEPT="text/html")
        assert response.status_code == 200
        assert _content_type(response) == "text/html"
        body = response.content.decode()
        assert "graphiql" in body.lower()
        assert _TEMPLATE_MARKER not in body
        assert 'id="djDebug"' not in body

    def test_named_json_operation_gets_panel_payload(self, toolbar_client):
        """Test 3: a real SQL-emitting named operation carries the injected payload."""
        seed_data(1)
        response = _post_graphql(toolbar_client, _TOOLBAR_ITEMS_QUERY, "ToolbarItems")
        assert response.status_code == 200
        assert _content_type(response) == "application/json"
        payload = json.loads(response.content)
        # The operation's own result is intact beside the injected key.
        assert payload["data"]["allItems"]["edges"]
        toolbar_payload = payload["debugToolbar"]
        assert toolbar_payload["requestId"]
        panels = toolbar_payload["panels"]
        assert panels
        # The SQL the operation actually emitted (the query count subtitle).
        assert panels["SQLPanel"]["subtitle"] is not None
        # The TemplatesPanel skip.
        assert "TemplatesPanel" not in panels
        # Behavior check only - the header-present refresh BRANCHES are owned
        # by the targeted units below.
        if "Content-Length" in response:
            assert int(response["Content-Length"]) == len(response.content)

    def test_introspection_query_is_skipped(self, toolbar_client):
        """Test 4: no payload for ``operationName == "IntrospectionQuery"``."""
        response = _post_graphql(toolbar_client, _INTROSPECTION_QUERY, "IntrospectionQuery")
        assert response.status_code == 200
        payload = json.loads(response.content)
        assert payload["data"]["__schema"]["queryType"]["name"] == "Query"
        assert "debugToolbar" not in payload

    def test_get_with_json_accept_hits_the_operation_name_except_branch(self, toolbar_client):
        """Test 5: a JSON-``Accept`` GET (empty body) degrades to inject.

        ``HTTP_ACCEPT="application/json"`` keeps this deterministic on the JSON
        branch (a GET without it renders the GraphiQL HTML page instead); the
        empty GET body makes ``json.loads(request.body)`` raise, so
        ``operationName`` degrades to ``None`` and the payload is injected.
        """
        response = toolbar_client.get(
            "/graphql/",
            {"query": "{ __typename }"},
            HTTP_ACCEPT="application/json",
        )
        # Assert the content type BEFORE inspecting the body.
        assert _content_type(response) == "application/json"
        assert response.status_code == 200
        payload = json.loads(response.content)
        assert payload["data"]["__typename"] == "Query"
        assert payload["debugToolbar"]["requestId"]

    def test_injected_request_id_round_trips_to_stored_sql_panel_content(self, toolbar_client):
        """Test 6: the injected ``requestId`` is USABLE through the real panel route.

        ``render_panel`` returns 200 JSON with non-empty ``content`` even on a
        miss (the "isn't available anymore" fallback), so the success direction
        is pinned on both sides: fallback absent AND a seeded-operation SQL
        marker present.
        """
        seed_data(1)
        response = _post_graphql(toolbar_client, _TOOLBAR_ITEMS_QUERY, "ToolbarItems")
        request_id = json.loads(response.content)["debugToolbar"]["requestId"]

        # Resolve through the route, staying correct under a custom prefix.
        panel_url = reverse("djdt:render_panel")
        panel_response = toolbar_client.get(
            panel_url,
            {"request_id": request_id, "panel_id": "SQLPanel"},
        )
        assert panel_response.status_code == 200
        panel_payload = json.loads(panel_response.content)
        assert set(panel_payload) >= {"content", "scripts"}
        assert _PANEL_FALLBACK not in panel_payload["content"]
        # The stored SQL-panel content for THIS id: the seeded operation's
        # SELECT against the products table.
        assert "SELECT" in panel_payload["content"]
        assert "products_item" in panel_payload["content"]

    @pytest.mark.parametrize("url", ["/", "/login/"])
    def test_non_strawberry_html_views_pass_through(self, toolbar_client, url):
        """Test 7: HTML detection negatives for function-based AND class-based views.

        Package-scoped, not toolbar-scoped: under the fixture's always-true
        callback the STOCK toolbar handle may legitimately appear in this
        ordinary HTML (the subclass preserves stock behavior), so only the
        package's own injections are asserted absent.
        """
        response = toolbar_client.get(url)
        assert response.status_code == 200
        body = response.content.decode()
        assert _TEMPLATE_MARKER not in body
        assert "debugToolbar" not in body

    def test_unrelated_json_body_is_never_mutated(self, toolbar_client):
        """Test 8: the JSON payload leak guard - the probe body round-trips exactly.

        The HTML negatives cannot prove this: an implementation injecting into
        EVERY JSON response would still pass Tests 1-7. Stock toolbar headers
        are acceptable; the contract is "unrelated JSON bodies are never
        mutated".
        """
        response = toolbar_client.get("/__debug_probe__.json")
        assert response.status_code == 200
        assert _content_type(response) == "application/json"
        assert json.loads(response.content) == {"probe": "ok"}


# ---------------------------------------------------------------------------
# Toolbar-absent (Tests 9-12, 11a): eviction + two-sided restore + the
# importlib-compatible None sentinel. Unmarked - pure import machinery.
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _simulated_toolbar_absence():
    """Simulate toolbar absence with the shared ``sys.modules["debug_toolbar"] = None`` sentinel.

    Importlib-compatible by construction (spec-042 Revision 5):
    ``require_debug_toolbar()`` imports via ``importlib.import_module``, which never
    consults ``builtins.__import__`` - so the ``None`` sentinel, not an
    ``__import__`` block, is the technique that makes ``import_module`` raise
    ``ModuleNotFoundError`` for the guard to wrap. Eviction + two-sided restore are
    the shared helper's (``tests/_soft_dependency.py::evicted_modules``); the
    parent's own ``debug_toolbar`` attribute rides along because the parent module
    OBJECT is saved and restored.
    """
    with simulated_absence(
        "debug_toolbar",
        "debug_toolbar",
        _PARENT,
        parent=django_strawberry_framework,
        attr="middleware",
    ):
        yield


def test_package_and_middleware_imports_stay_clean_without_toolbar():
    """Test 9: root + parent-package imports succeed; star import binds no toolbar name."""
    with _simulated_toolbar_absence():
        root = importlib.import_module("django_strawberry_framework")
        assert root is django_strawberry_framework
        # A FRESH parent import under absence (it was evicted): stays clean
        # because the package marker imports nothing optional.
        parent = importlib.import_module(_PARENT)
        assert parent is sys.modules[_PARENT]
        namespace = {}
        exec("from django_strawberry_framework import *", namespace)
        assert "DebugToolbarMiddleware" not in namespace


def test_leaf_import_raises_install_hint_when_toolbar_absent():
    """Test 10: the leaf import raises the HINT-carrying ImportError, cause chained.

    The hint (not a bare ``ModuleNotFoundError``) proves ``require_debug_toolbar()``
    wrapped the absence - which the ``None`` sentinel makes possible and a
    ``builtins.__import__`` block would not.
    """
    with _simulated_toolbar_absence():
        with pytest.raises(ImportError, match=_HINT_SUBSTRING) as excinfo:
            importlib.import_module(_LEAF)
        assert isinstance(excinfo.value.__cause__, ImportError)


def test_leaf_reimports_after_restore(toolbar_leaf):
    """Test 11: after restore the leaf imports again and both sides hold ONE object."""
    with _simulated_toolbar_absence():
        with pytest.raises(ImportError, match=_HINT_SUBSTRING):
            importlib.import_module(_LEAF)
    leaf = importlib.import_module(_LEAF)
    assert leaf is sys.modules[_LEAF]
    assert leaf is toolbar_leaf
    # The two-sided-restore invariant: the parent attribute path and the
    # import path resolve to the same module object.
    parent = importlib.import_module(_PARENT)
    assert parent.debug_toolbar is leaf


def test_broken_toolbar_install_propagates_raw_import_error(toolbar_leaf):
    """Test 11a: a present-but-broken install propagates the RAW ImportError, unwrapped.

    The guard imports only the TOP-LEVEL package, so with ``debug_toolbar``
    importable but its ``middleware`` submodule broken,
    ``require_debug_toolbar()`` passes and the leaf's own statement import
    fails - naming the real missing module, WITHOUT the install hint (a broken
    install is never misreported as "not installed"). The raw statement-import
    error propagates unwrapped, so - unlike Test 10's guarded raise - it chains
    no ``__cause__`` of its own.
    """
    assert toolbar_leaf is not None  # leaf (and debug_toolbar) preimported for the save/restore
    with evicted_modules(
        "debug_toolbar",
        _PARENT,
        parent=django_strawberry_framework,
        attr="middleware",
    ) as saved:
        sys.modules["debug_toolbar"] = saved["debug_toolbar"]  # top-level: present + real
        sys.modules["debug_toolbar.middleware"] = None  # its submodule: broken
        with pytest.raises(ImportError, match="debug_toolbar.middleware") as excinfo:
            importlib.import_module(_LEAF)
        assert _HINT_SUBSTRING not in str(excinfo.value)
        assert excinfo.value.__cause__ is None


def test_leaf_import_requires_debug_toolbar_in_installed_apps():
    """Test 11b: toolbar importable but app absent from INSTALLED_APPS -> package ImproperlyConfigured.

    The distinct-from-11a misconfiguration (spec-042 Error shapes): the package
    imports, but the leaf's ``debug_toolbar.middleware`` import defines the
    ``HistoryEntry`` model, which Django refuses (a cryptic app-label
    ``RuntimeError``) unless the app is registered. The leaf's second wiring
    gate raises one actionable ``ImproperlyConfigured`` instead. fakeshop's
    shipped settings omit the app, so no override is needed - only the leaf is
    evicted so its body re-runs the gate, which fires BEFORE the middleware
    import (debug_toolbar's own submodules need no eviction).
    """
    assert not apps.is_installed("debug_toolbar")
    middleware_pkg = importlib.import_module(_PARENT)
    with evicted_modules(_LEAF, parent=middleware_pkg, attr="debug_toolbar"):
        with pytest.raises(ImproperlyConfigured, match="INSTALLED_APPS"):
            importlib.import_module(_LEAF)


def test_require_debug_toolbar_guard_unit(toolbar_leaf):
    """Test 12: the thin-wrapper contract - module identity when present, hint when absent."""
    assert toolbar_leaf.require_debug_toolbar() is sys.modules["debug_toolbar"]
    with _simulated_toolbar_absence():
        with pytest.raises(ImportError, match=_HINT_SUBSTRING) as excinfo:
            toolbar_leaf.require_debug_toolbar()
        assert isinstance(excinfo.value.__cause__, ImportError)


# ---------------------------------------------------------------------------
# Coverage-only targeted units (Tests 13-15, 14a): branches the real toolbar
# lifecycle does not naturally expose. Unmarked, no database.
# ---------------------------------------------------------------------------


class _FakePanel:
    """A minimal stand-in for a stock panel in the ``_get_payload`` units."""

    def __init__(
        self,
        panel_id,
        has_content,
        title,
        nav_subtitle,
    ):
        self.panel_id = panel_id
        self.has_content = has_content
        self.title = title
        self.nav_subtitle = nav_subtitle


class _FakeToolbar:
    """A protocol-complete fake toolbar for the stock ``_postprocess``.

    The package override chains to ``super()._postprocess`` FIRST, so any unit
    entering ``_postprocess`` runs the stock toolbar postprocess - the fake
    must satisfy the small protocol it consumes: ``enabled_panels`` (iterated
    for stats / server timing / headers) and ``render_toolbar()``.
    """

    def __init__(self, request_id=None, enabled_panels=()):
        self.request_id = request_id
        self.enabled_panels = list(enabled_panels)

    def render_toolbar(self):
        return ""


def test_streaming_response_gets_no_package_mutation(middleware):
    """Test 13: streaming early-out - no package-specific mutation after the stock pass.

    Not "returns untouched" in the absolute sense: the stock postprocess runs
    first and may legitimately generate stats and headers before
    ``response.streaming`` sends the package branch home. No real-request test
    returns a streaming response, so this branch is unreachable through
    Tests 1-8.
    """
    request = RequestFactory().post("/graphql/")
    request._is_graphiql = True
    response = StreamingHttpResponse(iter([b'{"data": 1}']), content_type="application/json")
    result = middleware._postprocess(request, response, _FakeToolbar(request_id="stream-id"))
    assert result is response
    # The streaming content is unchanged: no appended script, no injected payload.
    assert b"".join(result.streaming_content) == b'{"data": 1}'


def test_get_payload_bails_without_request_id(toolbar_leaf):
    """Test 14: no ``request_id`` -> ``None`` (the real toolbar always assigns one)."""
    request = RequestFactory().post("/graphql/")
    response = HttpResponse(b"{}", content_type="application/json")
    assert toolbar_leaf._get_payload(request, response, _FakeToolbar(request_id=None)) is None


def test_get_payload_panel_title_only_when_has_content(toolbar_leaf):
    """Test 14 sibling: ``has_content``-false -> ``title`` None; callables are called."""
    request = RequestFactory().post("/graphql/")
    response = HttpResponse(b"{}", content_type="application/json")
    toolbar = _FakeToolbar(
        request_id="riid",
        enabled_panels=[
            _FakePanel("QuietPanel", has_content=False, title="Quiet", nav_subtitle="quiet sub"),
            _FakePanel(
                "LoudPanel",
                has_content=True,
                title=lambda: "Loud",
                nav_subtitle=lambda: "loud sub",
            ),
            _FakePanel("TemplatesPanel", has_content=True, title="Templates", nav_subtitle="t"),
        ],
    )
    payload = toolbar_leaf._get_payload(request, response, toolbar)
    assert payload["debugToolbar"]["requestId"] == "riid"
    panels = payload["debugToolbar"]["panels"]
    assert panels["QuietPanel"] == {"title": None, "subtitle": "quiet sub"}
    assert panels["LoudPanel"] == {"title": "Loud", "subtitle": "loud sub"}
    assert "TemplatesPanel" not in panels


def test_get_payload_bails_on_non_object_json_body(toolbar_leaf):
    """Test 14 sibling: a non-object JSON body -> ``None`` (the P2.3 guard).

    A valid single GraphQL response is always a JSON object, so this branch is
    unreachable through the real-request tests; without the guard the
    subscript-assign would raise and 500 the request.
    """
    request = RequestFactory().post("/graphql/")
    response = HttpResponse(b"[1, 2]", content_type="application/json")
    assert toolbar_leaf._get_payload(request, response, _FakeToolbar(request_id="riid")) is None


def test_process_view_tolerates_non_class_view_class(middleware):
    """Test 14a: a non-class ``view_class`` -> ``False``, no ``TypeError`` (the P2.1 guard).

    Tests 7-8 only drive real class/function views; this guard matters
    precisely because the middleware runs for ALL global traffic.
    """
    request = RequestFactory().get("/")

    def view_func(request):
        return None

    view_func.view_class = "not-a-class"
    middleware.process_view(request, view_func)
    assert request._is_graphiql is False


def test_html_content_length_refresh_branch(middleware):
    """Test 15 (HTML): a pre-set ``Content-Length`` is refreshed after the append.

    The pre-set header is the point: a real Strawberry ``HttpResponse`` may
    reach the middleware without it (Django computes it at serialization
    time), so the header-present branch needs it planted.
    """
    request = RequestFactory().get("/graphql/", HTTP_ACCEPT="text/html")
    request._is_graphiql = True
    response = HttpResponse(b"<html><body>ide</body></html>", content_type="text/html")
    response["Content-Length"] = len(response.content)
    result = middleware._postprocess(request, response, _FakeToolbar(request_id="riid"))
    assert _TEMPLATE_MARKER.encode() in result.content
    assert int(result["Content-Length"]) == len(result.content)


def test_json_content_length_refresh_branch(middleware):
    """Test 15 (JSON): a pre-set ``Content-Length`` is refreshed after the re-encode."""
    request = RequestFactory().post(
        "/graphql/",
        data='{"query": "query Q { x }"}',
        content_type="application/json",
    )
    request._is_graphiql = True
    response = HttpResponse(b'{"data": {"x": 1}}', content_type="application/json")
    response["Content-Length"] = len(response.content)
    result = middleware._postprocess(request, response, _FakeToolbar(request_id="riid"))
    payload = json.loads(result.content)
    assert payload["data"] == {"x": 1}
    assert payload["debugToolbar"]["requestId"] == "riid"
    assert int(result["Content-Length"]) == len(result.content)


# ---------------------------------------------------------------------------
# Template-port guard (Test 16): mechanical, no JS runtime.
# ---------------------------------------------------------------------------


def test_template_port_invariants_and_robustness_divergence():
    """Test 16: the copied-asset invariants + the JSON.parse robustness divergence.

    The suite has no JS runtime, so this does not prove the script WORKS - it
    turns the template-port checklist's by-eye diff into a mechanical guard that
    fails if a future edit drops a load-bearing behavior OR silently reverts the
    hook back to upstream's unsafe verbatim form (spec-042 Revision 7): the third
    documented divergence from the verbatim borrow, template-side this time.
    """
    template = (
        Path(django_strawberry_framework.__file__).parent
        / "templates"
        / "django_strawberry_framework"
        / "debug_toolbar.html"
    ).read_text()
    # 1. The JSON.parse wrapper - our robustness divergence from upstream's
    #    verbatim ``function (text) { return update(origParse(text)); }``: forward
    #    every argument via ``.apply`` so a page-wide ``JSON.parse(text, reviver)``
    #    keeps its ``reviver`` while GraphiQL is open.
    assert "JSON.parse = function ()" in template
    assert "return update(origParse.apply(this, arguments))" in template
    # 2. The Response.prototype.json wrapper.
    assert "Response.prototype.json = function" in template
    # 3. The key is stripped before the IDE renders.
    assert "delete data.debugToolbar" in template
    # 4. The data-request-id update on #djDebug (via setAttribute). Reads the
    #    captured ``toolbar`` ref rather than ``data.debugToolbar`` - the key is
    #    scrubbed before any DOM write (see the ordering invariant, #7 below).
    assert 'djDebug.setAttribute("data-request-id", toolbar.requestId)' in template
    # 5. The per-panel title / subtitle DOM updates.
    assert '.querySelector("h3").textContent = panel.title' in template
    assert '.querySelector("small").textContent = panel.subtitle' in template
    # 6. The ``update`` guard's robustness divergence (spec-042 Revision 7): a
    #    membership test that never throws for null-prototype /
    #    ``hasOwnProperty``-shadowing objects, guarded by a non-object bail and a
    #    null-handle bail before any DOM mutation.
    assert 'Object.prototype.hasOwnProperty.call(data, "debugToolbar")' in template
    assert 'typeof data !== "object"' in template
    assert "if (djDebug === null) return data;" in template
    # 7. Scrubbing is mandatory, DOM updates are best-effort: the server-only
    #    ``debugToolbar`` key is deleted BEFORE the null-handle bail, so the
    #    toolbar-DOM-absent path still returns a clean GraphQL payload instead of
    #    leaking the key back to GraphiQL (the P2.1 ordering fix must not drift).
    assert template.index("delete data.debugToolbar") < template.index(
        "if (djDebug === null) return data;",
    )
    # 8. Best-effort per-panel DOM (spec-042 Revision 8): the loop is a
    #    side-effect-only ``forEach`` that skips a panel whose content node is
    #    absent, so a payload panel missing from the current toolbar DOM cannot
    #    throw inside the patched ``JSON.parse`` and break the IDE response path.
    assert "Object.entries(toolbar.panels).forEach(" in template
    assert "if (content === null) return;" in template
