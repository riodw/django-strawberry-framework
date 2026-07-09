"""Live GraphQL HTTP tests for the spec-042 ``DebugToolbarMiddleware``.

Since ``0.0.14`` fakeshop's shipped settings wire the debug-toolbar (the
``debug_toolbar`` app, the package middleware near the front of ``MIDDLEWARE``,
``INTERNAL_IPS``, and ``debug_toolbar_urls()`` in ``config.urls``), so the
toolbar's ``/graphql/`` integration is reachable through the example's REAL
request path - exactly what ``test_query/README.md``'s live-first coverage rule
sends here. These tests drive fakeshop's real ``/graphql/`` URL through
``django.test.Client``: the GraphiQL HTML render (through the real
``ensure_csrf_cookie`` decorator) and real SQL-emitting operations (through the
real optimizer), asserting the two injections the middleware contributes.

The ONE setting still overridden is ``DEBUG``: pytest-django forces the suite to
``DEBUG=False``, and under it both ``debug_toolbar``'s ``show_toolbar`` gate AND
``debug_toolbar_urls()`` short-circuit - so the toolbar-present group runs under
``override_settings(DEBUG=True)`` with an always-true ``SHOW_TOOLBAR_CALLBACK``
and reloads ``config.urls`` INSIDE the override so its DEBUG-gated ``djdt`` routes
populate. Everything else is fakeshop's shipped configuration, unmodified.

The dependency-absent tests and the coverage-only ``_postprocess`` /
``_get_payload`` unit branches no live request can reach stay package-internal in
``tests/middleware/test_debug_toolbar.py`` (that file's module docstring maps the
split).
"""

import contextlib
import json

import pytest
import schema_reload
from apps.products.services import seed_data
from django.test import Client, override_settings
from django.urls import reverse

# A distinctive substring of the package's appended bridge asset: present only
# when the middleware's HTML branch fired, never in stock toolbar markup.
_TEMPLATE_MARKER = "Response.prototype.json"

# ``render_panel``'s miss fallback (debug-toolbar 7.0.0): a 200 JSON response
# with NON-empty content, so the round-trip test pins its ABSENCE, not just shape.
_PANEL_FALLBACK = "isn't available anymore"

# A NAMED operation: a non-null ``operationName`` in the JSON envelope requires a
# named operation document (an anonymous ``{ ... }`` document plus a non-null
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
    """The response media type without parameters - the middleware's own sniff.

    Mirrors the production first-segment split
    (``middleware/debug_toolbar.py::_postprocess``) so the tests key on the media
    type the branch actually inspects, not the raw header.
    """
    return response["Content-Type"].split(";")[0]


def _show_toolbar_always(request):
    """The always-true show-toolbar callback: independent of REMOTE_ADDR / INTERNAL_IPS."""
    return True


@contextlib.contextmanager
def _debug_toolbar_cache_state():
    """Save / clear / restore the toolbar's process-level caches (spec-042 Decision 9 hygiene).

    ``show_toolbar_func_or_path`` is ``@cache``-memoized and ``DebugToolbar``
    caches ``_panel_classes`` / ``_urlpatterns`` on the class - none reset with a
    settings override, and under ``--dist loadscope`` a leaked always-true
    callback would let this file pass while a later same-worker test inherits it.
    Restore puts back the SAVED values (not ``None``), so a neighboring test gets
    back exactly the state it had.
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


@pytest.fixture(autouse=True)
def _reload_project_schema_for_acceptance_tests(reload_all_project_app_schemas):
    """Rebuild the FULL project schema if a package test cleared the registry (see conftest.py)."""
    reload_all_project_app_schemas()


@pytest.fixture
def toolbar_client():
    """Real fakeshop ``/graphql/`` client with the toolbar active under ``DEBUG=True``.

    Fakeshop's shipped settings already carry the ``debug_toolbar`` app, the
    package middleware, ``INTERNAL_IPS`` and ``debug_toolbar_urls()`` - so no
    ``INSTALLED_APPS`` / ``MIDDLEWARE`` / ``ROOT_URLCONF`` override is needed, only
    ``DEBUG=True`` (which pytest-django forces off). ``config.urls`` is reloaded
    INSIDE the override so its ``debug_toolbar_urls()`` recomputes the ``djdt``
    routes (empty under ``DEBUG=False``); the always-true callback keeps the
    show-toolbar gate independent of ``REMOTE_ADDR``. No teardown reload is needed:
    every acceptance test reloads ``config.urls`` under the ambient ``DEBUG=False``
    in its autouse fixture, so the ``djdt`` routes never leak past this fixture.
    """
    with override_settings(
        DEBUG=True,
        DEBUG_TOOLBAR_CONFIG={"SHOW_TOOLBAR_CALLBACK": _show_toolbar_always},
    ):
        with _debug_toolbar_cache_state():
            schema_reload.reload_all_project_schemas()
            yield Client()


@pytest.fixture
def stock_client():
    """A client under fakeshop's SHIPPED settings (pytest-django forces ``DEBUG=False``)."""
    return Client()


@pytest.mark.django_db
class TestToolbarPresent:
    """The toolbar-present group: real ``/graphql/`` traffic under ``DEBUG=True``."""

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
        """Test 2: fakeshop's shipped wiring is INERT under ``DEBUG=False`` (production safety).

        The middleware is now in fakeshop's shipped ``MIDDLEWARE``, but
        ``debug_toolbar``'s ``show_toolbar`` returns ``False`` when ``DEBUG`` is
        false (pytest-django's forced default) - so a normal ``/graphql/`` request
        emits neither the stock handle nor the package bridge. This pins that the
        opt-in stays off wherever ``DEBUG`` is off, i.e. in production. Behavior,
        not bytes: under ``--dist loadscope`` an earlier toolbar-present test on
        the same worker legitimately leaves the leaf in ``sys.modules`` while this
        response is perfectly clean.
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
        # Behavior check only - the header-present refresh BRANCHES are owned by
        # the targeted units in tests/middleware/test_debug_toolbar.py.
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
        branch (a GET without it renders the GraphiQL HTML page instead); the empty
        GET body makes ``json.loads(request.body)`` raise, so ``operationName``
        degrades to ``None`` and the payload is injected.
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

        ``render_panel`` returns 200 JSON with non-empty ``content`` even on a miss
        (the "isn't available anymore" fallback), so the success direction is
        pinned on both sides: fallback absent AND a seeded-operation SQL marker
        present. ``reverse("djdt:render_panel")`` resolves through the ``djdt``
        routes that ``config.urls`` computed under this fixture's ``DEBUG=True``.
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
        # The stored SQL-panel content for THIS id: the seeded operation's SELECT
        # against the products table.
        assert "SELECT" in panel_payload["content"]
        assert "products_item" in panel_payload["content"]

    @pytest.mark.parametrize("url", ["/", "/login/"])
    def test_non_strawberry_html_views_pass_through(self, toolbar_client, url):
        """Test 7: HTML detection negatives for function-based AND class-based views.

        Package-scoped, not toolbar-scoped: under the fixture's always-true
        callback the STOCK toolbar handle may legitimately appear in this ordinary
        HTML (the subclass preserves stock behavior), so only the package's own
        injections are asserted absent.
        """
        response = toolbar_client.get(url)
        assert response.status_code == 200
        body = response.content.decode()
        assert _TEMPLATE_MARKER not in body
        assert "debugToolbar" not in body
