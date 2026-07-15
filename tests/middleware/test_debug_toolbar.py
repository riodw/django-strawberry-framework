"""DebugToolbarMiddleware tests for import guards, payload injection, response rewriting, and templates.

Placement (spec-042 Decision 9, honoring the ``test_query/README.md`` coverage
rule): since ``0.0.14`` fakeshop's shipped settings wire the toolbar (the
``debug_toolbar`` app, the package middleware, ``INTERNAL_IPS`` and
``debug_toolbar_urls()``), so the toolbar-PRESENT tests that drive a real
``/graphql/`` request now live in the live tier at
``examples/fakeshop/test_query/test_debug_toolbar_api.py`` - the live-first
mandate's home once a package line is reachable through the example's shipped
configuration. THIS file keeps only what no live ``/graphql/`` request can reach:
the soft-dependency absence matrix (a missing dependency is never a live path) and
the coverage-only ``_postprocess`` / ``_get_payload`` branch units (streaming
early-out, the non-object-JSON bail, the non-class ``view_class`` guard, the
header-present ``Content-Length`` refreshes, and the untagged-JSON passthrough leak
guard, plus malformed/undecodable declared-JSON response bails) that the real toolbar
lifecycle does not naturally expose - driven directly against fake toolbar /
middleware objects.

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
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, StreamingHttpResponse
from django.test import RequestFactory, modify_settings

import django_strawberry_framework
from tests._soft_dependency import evicted_modules, simulated_absence

_LEAF = "django_strawberry_framework.middleware.debug_toolbar"
_PARENT = "django_strawberry_framework.middleware"

# The verified debug-toolbar floor; the install hint must name it. RE-TYPED
# literal (the ``_HINT_SUBSTRING`` drift-catch discipline - place 3 of the
# three-places-that-must-agree; place 1 is the ``[dependency-groups].dev``
# specifier, place 2 is ``_DEBUG_TOOLBAR_INSTALL_HINT``).
_HINT_SUBSTRING = "django-debug-toolbar>=7.0.0"

# A distinctive substring of the package's appended bridge asset: present only
# when the middleware's HTML branch fired, never in stock toolbar markup.
_TEMPLATE_MARKER = "Response.prototype.json"


# ---------------------------------------------------------------------------
# Fixtures shared by the absence tests and the targeted units. The leaf's first
# import in a process defines the ``HistoryEntry`` model, so it must happen with
# ``"debug_toolbar"`` in ``INSTALLED_APPS`` (fakeshop ships the app, but this
# file's tests do not assume that suite state) - the ``toolbar_leaf`` fixture
# owns it, keeping these order-independent under pytest-xdist.
# ---------------------------------------------------------------------------


@pytest.fixture
def toolbar_leaf():
    """Import (or reuse) the leaf module with the ``debug_toolbar`` app installed.

    The first ``debug_toolbar.middleware`` import in a process defines the
    ``HistoryEntry`` model, which requires the app in ``INSTALLED_APPS`` - this
    fixture makes the targeted units and absence tests order-independent under
    pytest-xdist instead of relying on another test having imported the leaf
    earlier on the same worker.
    """
    with modify_settings(INSTALLED_APPS={"append": "debug_toolbar"}):
        yield importlib.import_module(_LEAF)


@pytest.fixture
def middleware(toolbar_leaf):
    """The package middleware instance the targeted units drive directly.

    Depends on ``toolbar_leaf`` so ``debug_toolbar`` stays in ``INSTALLED_APPS``
    for the unit's lifetime; ``lambda request: None`` is the sync ``get_response``
    the stock ``__init__`` inspects (sync -> not async mode).
    """
    return toolbar_leaf.DebugToolbarMiddleware(lambda request: None)


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
    ``RuntimeError``) unless the app is registered. The leaf's second wiring gate
    raises one actionable ``ImproperlyConfigured`` instead. This test removes the
    app so its body re-runs the gate; ``modify_settings(remove=...)`` is a no-op if
    fakeshop's shipped settings did not carry it, so the gate fires either way, and
    only the leaf is evicted so its body re-runs BEFORE the middleware import.
    """
    with modify_settings(INSTALLED_APPS={"remove": "debug_toolbar"}):
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
# Coverage-only targeted units (Tests 8, 13-15, 14a): branches the real toolbar
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
    returns a streaming response, so this branch is unreachable through the live
    suite.
    """
    request = RequestFactory().post("/graphql/")
    request._is_graphiql = True
    response = StreamingHttpResponse(iter([b'{"data": 1}']), content_type="application/json")
    result = middleware._postprocess(request, response, _FakeToolbar(request_id="stream-id"))
    assert result is response
    # The streaming content is unchanged: no appended script, no injected payload.
    assert b"".join(result.streaming_content) == b'{"data": 1}'


def test_unrelated_json_view_body_is_never_mutated(middleware):
    """Test 8 (unit): an untagged JSON response passes through unmutated - the leak guard.

    The live counterpart in
    ``examples/fakeshop/test_query/test_debug_toolbar_api.py`` drives fakeshop's
    real Strawberry ``/graphql/`` traffic, but fakeshop ships no NON-Strawberry
    JSON endpoint to prove the guard against - and an implementation injecting into
    EVERY JSON response would still pass the live HTML negatives (Test 7). Driving
    ``_postprocess`` with an untagged response (``_is_graphiql`` False, the state
    ``process_view`` sets for any non-``BaseView``) pins the ``not is_graphiql``
    early return on the JSON branch: the body round-trips exactly, no
    ``debugToolbar`` key added.
    """
    request = RequestFactory().get("/unrelated.json")
    request._is_graphiql = False
    response = HttpResponse(b'{"probe": "ok"}', content_type="application/json")
    result = middleware._postprocess(request, response, _FakeToolbar(request_id="riid"))
    assert json.loads(result.content) == {"probe": "ok"}
    assert b"debugToolbar" not in result.content


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


@pytest.mark.parametrize("content", [b"not json", b"\xff"])
def test_malformed_json_body_gets_no_package_rewrite(middleware, content):
    """A tagged declared-JSON body that cannot be parsed or decoded is not rewritten.

    A valid Strawberry operation always returns a JSON object, so the custom
    response/error-handler path is unreachable through fakeshop's real GraphQL
    endpoint. Driving the full package postprocess proves the development
    middleware neither masks the original response nor turns it into a 500. The
    stock postprocess may still add its normal toolbar headers.
    """
    request = RequestFactory().post("/graphql/", data="{}", content_type="application/json")
    request._is_graphiql = True
    response = HttpResponse(content, content_type="application/json; charset=utf-8")
    response["Content-Length"] = len(response.content)

    result = middleware._postprocess(request, response, _FakeToolbar(request_id="riid"))

    assert result is response
    assert result.content == content
    assert int(result["Content-Length"]) == len(content)


def test_process_view_tolerates_non_class_view_class(middleware):
    """Test 14a: a non-class ``view_class`` -> ``False``, no ``TypeError`` (the P2.1 guard).

    The live Test 7 only drives real class/function views; this guard matters
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
    # 5a. debug-toolbar>=7 defaults USE_SHADOW_DOM=True: resolve #djDebug via
    #     #djDebugRoot's shadowRoot (stock getDebugElement pattern) with a
    #     light-DOM fallback; nav nodes are queried under djDebug, not document.
    assert 'getElementById("djDebugRoot")' in template
    assert "shadowRoot" in template
    assert 'querySelector("#djDebug")' in template
    assert "djDebug.querySelector(`#djdt-${id}`)" in template
    assert "document.getElementById(`djdt-${id}`)" not in template
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
