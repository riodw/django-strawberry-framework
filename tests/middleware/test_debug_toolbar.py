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
import re
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

# The verified debug-toolbar floor, RE-TYPED here rather than imported (the
# ``_HINT_SUBSTRING`` drift-catch discipline: a test comparing the imported
# constant against itself could never notice the hint drifting). The floor is
# GATED in three places that must agree - this literal,
# ``_DEBUG_TOOLBAR_INSTALL_HINT``, and the ``[dependency-groups].dev``
# specifier in ``pyproject.toml`` - and this file compares all of them (the
# hint-matching rows below against the literal,
# ``test_install_hint_floor_matches_the_pyproject_dev_group_row`` against the
# dependency row), which is what makes the three-places-that-must-agree rule a
# gate rather than a note. Those are the GATED sites, not a census of where the
# floor is written: anything else restating it, documentation included, is
# gated by nothing, so a floor bump
# sweeps the tree for the package NAME and reads each hit, rather than trusting
# this enumeration or sweeping for the ``django-debug-toolbar>=`` specifier - a
# restatement that separates the name from the constraint with a backtick or a
# space does not match it.
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
# Toolbar-absent: eviction + two-sided restore + the
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
    """Root + parent-package imports succeed; star import binds no toolbar name."""
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
    """The leaf import raises the HINT-carrying ImportError, cause chained.

    The hint (not a bare ``ModuleNotFoundError``) proves ``require_debug_toolbar()``
    wrapped the absence - which the ``None`` sentinel makes possible and a
    ``builtins.__import__`` block would not.
    """
    with _simulated_toolbar_absence():
        with pytest.raises(ImportError, match=_HINT_SUBSTRING) as excinfo:
            importlib.import_module(_LEAF)
        assert isinstance(excinfo.value.__cause__, ImportError)


def test_leaf_reimports_after_restore(toolbar_leaf):
    """After restore the leaf imports again and both sides hold ONE object."""
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
    """A present-but-broken install propagates the RAW ImportError, unwrapped.

    The guard imports only the TOP-LEVEL package, so with ``debug_toolbar``
    importable but its ``middleware`` submodule broken,
    ``require_debug_toolbar()`` passes and the leaf's own statement import
    fails - naming the real missing module, WITHOUT the install hint (a broken
    install is never misreported as "not installed"). The raw statement-import
    error propagates unwrapped, so - unlike the absent-install guarded raise - it
    chains no ``__cause__`` of its own.
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
    """Toolbar importable but app absent from INSTALLED_APPS -> package ImproperlyConfigured.

    The misconfiguration distinct from a broken install (spec-042 Error shapes):
    the package
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
    """The thin-wrapper contract - module identity when present, hint when absent."""
    assert toolbar_leaf.require_debug_toolbar() is sys.modules["debug_toolbar"]
    with _simulated_toolbar_absence():
        with pytest.raises(ImportError, match=_HINT_SUBSTRING) as excinfo:
            toolbar_leaf.require_debug_toolbar()
        assert isinstance(excinfo.value.__cause__, ImportError)


def test_install_hint_floor_matches_the_pyproject_dev_group_row(toolbar_leaf):
    """The floor's three gated sites agree, including the one nothing imports.

    The hint-matching rows above compare the install hint against the re-typed
    ``_HINT_SUBSTRING`` literal, so those two cannot drift apart. What none of
    them can see is the third gated site: the ``django-debug-toolbar`` row in
    ``pyproject.toml``'s dev group. Nothing imports a TOML dependency row, so
    until this row existed the specifier could move alone and the install hint
    would go on advising a floor the project no longer pins. Parsed with the
    same regex-over-``pyproject.toml`` idiom the suite's Channels and Strawberry
    governance rows use, so the three floor pins cannot diverge in method.

    It gates exactly those three. Documentation that restates the floor is
    behind no gate at all, and this row says nothing about it: a floor bump
    sweeps the tree for the package name and reads each hit, rather than
    trusting any enumeration of where the floor is written or sweeping for the
    ``django-debug-toolbar>=`` specifier, which a restatement separating the
    name from the constraint with a backtick or a space does not match.
    """
    text = (Path(__file__).resolve().parents[2] / "pyproject.toml").read_text(encoding="utf-8")
    rows = re.findall(r'"(django-debug-toolbar>=[0-9][^"]*)"', text)
    assert rows == [_HINT_SUBSTRING], (rows, _HINT_SUBSTRING)
    assert _HINT_SUBSTRING in toolbar_leaf._DEBUG_TOOLBAR_INSTALL_HINT


# ---------------------------------------------------------------------------
# Coverage-only targeted units: branches the real toolbar
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
    """Streaming early-out - no package-specific mutation after the stock pass.

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


def _html_was_appended(body):
    """The GraphiQL HTML branch fired: the bridge asset is in the body."""
    return _TEMPLATE_MARKER.encode() in body


def _payload_was_injected(body):
    """The tagged-JSON branch fired: the payload key is in the body."""
    return b"debugToolbar" in body


@pytest.mark.parametrize("encoding", ["gzip", "br"])
@pytest.mark.parametrize(
    (
        "request_factory",
        "content",
        "content_type",
        "was_mutated",
    ),
    [
        (
            lambda: RequestFactory().get("/graphql/"),
            b"<html><body>ide</body></html>",
            "text/html",
            _html_was_appended,
        ),
        (
            lambda: RequestFactory().post(
                "/graphql/",
                data='{"query": "query Q { x }"}',
                content_type="application/json",
            ),
            b'{"data": {"x": 1}}',
            "application/json",
            _payload_was_injected,
        ),
    ],
    ids=["graphiql_html_append", "operation_json_injection"],
)
def test_encoded_response_gets_no_package_mutation(
    middleware,
    request_factory,
    content,
    content_type,
    was_mutated,
    encoding,
):
    """The `Content-Encoding` header is the only thing holding back each mutation site.

    The encoding guard sits ahead of the GraphiQL HTML append AND the tagged
    ``application/json`` payload re-encode, so each row carries a body its own
    mutation path would otherwise accept - plain HTML for the append, a
    decodable JSON object for the re-encode - and drives that body through
    ``_postprocess`` TWICE. The first drive is the row's positive control,
    header-free, asserting the mutation actually happens; only then does the
    header-bearing twin assert byte-identity. Without the control a row proves
    nothing: an undecodable body would be left alone by ``_get_payload``'s own
    response-shape bail whether or not the encoding guard existed, so it would
    re-prove a different guard and pass with this one deleted.

    Parametrized over two encodings as well as both paths, so the guard rests on
    the header's presence rather than on one value: writing unencoded assets or
    an unencoded JSON dump into a compressed body corrupts the response rather
    than merely failing to instrument it.
    """
    control_request = request_factory()
    control_request._is_graphiql = True
    control = HttpResponse(content, content_type=content_type)
    control_result = middleware._postprocess(
        control_request,
        control,
        _FakeToolbar(request_id="encoded"),
    )
    assert was_mutated(control_result.content), (
        "positive control did not fire: this row cannot distinguish the encoding guard"
    )

    request = request_factory()
    request._is_graphiql = True
    response = HttpResponse(content, content_type=content_type)
    response["Content-Encoding"] = encoding

    result = middleware._postprocess(request, response, _FakeToolbar(request_id="encoded"))

    assert result is response
    assert result.content == content
    assert not was_mutated(result.content)
    assert b"debugToolbar" not in result.content


def test_unrelated_json_view_body_is_never_mutated(middleware):
    """An untagged JSON response passes through unmutated - the leak guard (unit).

    The live counterpart in
    ``examples/fakeshop/test_query/test_debug_toolbar_api.py`` drives fakeshop's
    real Strawberry ``/graphql/`` traffic, but fakeshop ships no NON-Strawberry
    JSON endpoint to prove the guard against - and an implementation injecting into
    EVERY JSON response would still pass the live HTML negatives. Driving
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
    """No ``request_id`` -> ``None`` (the real toolbar always assigns one)."""
    request = RequestFactory().post("/graphql/")
    response = HttpResponse(b"{}", content_type="application/json")
    assert toolbar_leaf._get_payload(request, response, _FakeToolbar(request_id=None)) is None


def test_get_payload_panel_title_only_when_has_content(toolbar_leaf):
    """Sibling of the missing-``request_id`` row: ``has_content``-false -> ``title``
    None; callables are called.
    """
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
    """A non-object JSON body yields ``None``.

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
    """A non-class ``view_class`` -> ``False``, no ``TypeError``.

    The live tests only drive real class/function views; this guard matters
    precisely because the middleware runs for ALL global traffic.
    """
    request = RequestFactory().get("/")

    def view_func(request):
        return None

    view_func.view_class = "not-a-class"
    middleware.process_view(request, view_func)
    assert request._is_graphiql is False


def test_html_content_length_refresh_branch(middleware):
    """HTML: a pre-set ``Content-Length`` is refreshed after the append.

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
    """JSON: a pre-set ``Content-Length`` is refreshed after the re-encode."""
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
# Template-port guard: mechanical, no JS runtime.
# ---------------------------------------------------------------------------


def _template_text():
    """The shipped bridge asset's source text (the asset is never executed here)."""
    return (
        Path(django_strawberry_framework.__file__).parent
        / "templates"
        / "django_strawberry_framework"
        / "debug_toolbar.html"
    ).read_text()


def _present(needle):
    """Predicate: ``needle`` appears in the asset."""
    return lambda text: needle in text


def _absent(needle):
    """Predicate: ``needle`` does NOT appear in the asset."""
    return lambda text: needle not in text


def _defined_once(needle):
    """Predicate: ``needle`` appears exactly once (a spelling that must be single-sited)."""
    return lambda text: text.count(needle) == 1


def _ordered(*needles):
    """Predicate: every ``needle`` is present, in this order, by first occurrence.

    Returns False rather than raising when one is missing, so a row that a
    dropped guard makes unanswerable fails under its own name instead of
    erroring out of the parametrized body.
    """

    def predicate(text):
        if any(needle not in text for needle in needles):
            return False
        positions = [text.index(needle) for needle in needles]
        return positions == sorted(positions)

    return predicate


def _adjacent(first, second):
    """Predicate: ``second`` follows ``first`` with only whitespace between them.

    Ordering predicates compare indices, so a statement wrapped in a condition
    still precedes everything it preceded before - an ``if`` put between the two
    is exactly what an index comparison cannot see, and adjacency can.
    """

    def predicate(text):
        if first not in text:
            return False
        rest = text[text.index(first) + len(first) :]
        if second not in rest:
            return False
        return rest[: rest.index(second)].strip() == ""

    return predicate


def _own_statement_line(statement):
    """Predicate: some line's content is exactly ``statement``, nothing guarding it inline."""
    return lambda text: any(line.strip() == statement for line in text.splitlines())


def _unnested_within(opener, needle):
    """Predicate: ``needle`` sits at the block level ``opener`` opens, not inside a nested one.

    Braces between the two balance out when nothing has been wrapped around the
    needle; a block-form condition around it leaves one unclosed.
    """

    def predicate(text):
        if opener not in text:
            return False
        rest = text[text.index(opener) + len(opener) :]
        if needle not in rest:
            return False
        span = rest[: rest.index(needle)]
        return span.count("{") == span.count("}")

    return predicate


def _return_count_between(first, second, expected):
    """Predicate: exactly ``expected`` ``return`` keywords sit between the two needles.

    Whether a statement is unconditional is a property of the answer - does
    every path reaching the span's start also reach its end - not of any one
    spelling of a weakening. A bail placed above the captured statement leaves
    index, adjacency and nesting predicates intact while making that statement
    skippable, and an enumeration of bail spellings can never be closed;
    counting the returns in the span answers the question directly.
    """

    def predicate(text):
        if first not in text:
            return False
        rest = text[text.index(first) + len(first) :]
        if second not in rest:
            return False
        return rest[: rest.index(second)].count("return") == expected

    return predicate


# The mandatory scrub, named once: the rows below pin its presence, its
# position and that it runs on every path, so the spelling is one fact the
# table states in one place rather than re-typing it per row.
_SCRUB = "delete data.debugToolbar"
_SCRUB_STATEMENT = f"{_SCRUB};"


# The template-port contract as data: one row per predicate, one predicate per
# load-bearing form, so dropping a single guard fails that guard's own rows and
# only those. A ``for`` loop or a list of asserts inside one test would collapse
# the whole contract into one node id - removing every guard would then score
# exactly the same one failing row as removing none but the last.
#
# The failure this table exists to catch is a silent revert to upstream's
# verbatim form, so every diverged form carries BOTH halves of its divergence:
# a row pinning the port's spelling, and a row pinning that the upstream
# spelling it replaced is ABSENT. A presence row alone cannot see a revert that
# restores upstream's shape alongside the port's. Where the contract is a
# position rather than a spelling - the mandatory scrub - the rows compare
# indices, adjacency and nesting instead, which a substring copy satisfies and
# a reordering or a condition wrapped around the statement does not; and where
# the contract is that a statement runs on every path, they count the returns
# in the span, the only one of those instruments that sees a bail hoisted above
# the statement rather than wrapped around it. A preserved invariant carries
# the row pinning the upstream write the port keeps.
# An absence needle must occur in the borrow, contain no sibling absence
# needle, and be typed as a literal: a needle the borrow never spells can never
# fail, one containing another row's needle can never fail without that row,
# and one derived from ``_SCRUB`` / ``_SCRUB_STATEMENT`` rather than typed goes
# silently inert the moment the constant drifts, where a presence row reading
# the same constant goes red instead - all three read exactly like a working
# row. What falsifies this: a diverged form whose rows are all presence checks,
# a post-scrub site no ordering row names, or a guard pinned by an enumeration
# of the spellings that weaken it where the answer it holds can be measured
# directly. The same containment rule is deliberately NOT imposed on presence
# rows. Several plainly state an invariant a stricter sibling already pins - an
# ordering or adjacency row over the same needle - so they cannot fail on their
# own, and the only way to make them fail alone is to delete the plain
# statement of the invariant. Nothing is advertised that the table does not
# hold and its detection power is identical with or without them, so a
# containment check run table-wide meets them and should leave them.
#
# The names are the pytest ids, so a node-id set stays readable and comparable
# across runs (an integer index names nothing once the table is reordered).
_TEMPLATE_CONTRACT = (
    # Preserved upstream invariants: both patched globals, the scrub statement,
    # the handle's data-request-id write, and the per-panel title/subtitle writes.
    ("response-json-wrapper", _present("Response.prototype.json = function")),
    ("scrub-key-deleted", _present(_SCRUB)),
    (
        "data-request-id-write",
        _present('djDebug.setAttribute("data-request-id", toolbar.requestId)'),
    ),
    ("panel-title-write", _present("textContent = panel.title")),
    ("panel-subtitle-write", _present("textContent = panel.subtitle")),
    # Reviver preservation: every argument forwarded, so a page-wide
    # JSON.parse(text, reviver) keeps its reviver while GraphiQL is open.
    ("json-parse-wrapper-signature", _present("JSON.parse = function ()")),
    ("reviver-forwarded-via-apply", _present("return update(origParse.apply(this, arguments))")),
    ("no-upstream-single-argument-parse", _absent("update(origParse(text))")),
    # Membership-guard safety: a membership test that never throws for a
    # null-prototype object or one shadowing hasOwnProperty, behind the record
    # predicate rather than a raw typeof spelling.
    ("entry-guard-uses-record-predicate", _present("!isRecord(data)")),
    (
        "membership-guard-uses-hasownproperty-call",
        _present('Object.prototype.hasOwnProperty.call(data, "debugToolbar")'),
    ),
    ("no-upstream-own-hasownproperty-call", _absent('data.hasOwnProperty("debugToolbar")')),
    # Mandatory scrub: unconditional, and ahead of EVERY early return and DOM
    # write that follows it, so no bail can leak the server-only key back to
    # GraphiQL. One row per post-scrub site - reverting the scrub to upstream's
    # position after the DOM work must not cost a single row - plus the rows that
    # answer "does it run on every path that reaches it", which an index
    # comparison cannot: nothing between the capture and the scrub, the scrub
    # alone on its line, and the scrub not nested inside a block of its own.
    ("null-handle-bail-present", _present("if (djDebug === null) return data;")),
    (
        "scrub-immediately-follows-capture",
        _adjacent("const toolbar = data.debugToolbar;", _SCRUB_STATEMENT),
    ),
    ("scrub-is-its-own-statement", _own_statement_line(_SCRUB_STATEMENT)),
    (
        "scrub-not-nested-inside-update",
        _unnested_within("function update(data) {", _SCRUB_STATEMENT),
    ),
    # The two rows below answer the same question as the three above it from the
    # other end: not "has anything been wrapped around the scrub" but "can any
    # path reach the capture and not the scrub". A bail hoisted ABOVE the capture
    # is that path, and it leaves index, adjacency, own-line and nesting rows
    # all intact. The first row's span opens at the asset's first ``return
    # data;``, which is the entry guard's own - the one return that legitimately
    # precedes the scrub, because it fires only when the key is absent. The
    # second opens at the function instead, so it also sees a bail inserted
    # above that guard returning something other than ``data``, where the first
    # row's span would slide down with it.
    (
        "no-return-between-entry-guard-and-scrub",
        _return_count_between("return data;", _SCRUB_STATEMENT, 0),
    ),
    (
        "entry-guard-return-is-the-only-one-before-the-scrub",
        _return_count_between("function update(data) {", _SCRUB_STATEMENT, 1),
    ),
    ("scrub-before-null-handle-bail", _ordered(_SCRUB, "if (djDebug === null) return data;")),
    (
        "scrub-before-payload-shape-guard",
        _ordered(
            _SCRUB,
            "if (!isRecord(toolbar) || !isRecord(toolbar.panels)) return data;",
        ),
    ),
    ("scrub-before-panel-loop", _ordered(_SCRUB, "Object.entries(toolbar.panels)")),
    ("scrub-before-request-id-write", _ordered(_SCRUB, 'djDebug.setAttribute("data-request-id"')),
    # Best-effort per-panel DOM: a side-effect-only forEach that skips a panel
    # whose content node is absent.
    ("panel-loop-is-foreach", _present("Object.entries(toolbar.panels).forEach(")),
    ("panel-loop-skips-absent-content-node", _present("if (content === null) return;")),
    # The needle is the call, not the call plus upstream's binding: the binding
    # spelling is already the next absence row's needle, and an absence needle
    # containing a sibling's cannot fail without it.
    ("no-upstream-value-returning-panel-map", _absent(".panels).map(")),
    # The same promise applied to the panel KEY, which is payload text the loop
    # interpolates into the two ``#...`` selectors. The rows pin the answer - the
    # key reaches querySelector only through a form the selector parser accepts -
    # rather than any list of keys it would reject: the escape, that it is asked
    # once at the key's entry, that a key escaping to the empty identifier (which
    # can name no node) skips the panel before either lookup, and that it
    # precedes both lookups. The absence row names upstream's own raw binding of
    # the key to ``id``, the spelling a verbatim paste restores.
    ("panel-key-escaped-for-selector", _present("const id = CSS.escape(panelId);")),
    ("panel-key-escape-is-single-sited", _defined_once("CSS.escape(")),
    ("unusable-panel-key-skips-panel", _present('if (id === "") return;')),
    (
        "unusable-panel-key-skipped-before-any-lookup",
        _ordered(
            "const id = CSS.escape(panelId);",
            'if (id === "") return;',
            "if (panel.title)",
        ),
    ),
    (
        "panel-key-escaped-before-content-lookup",
        _ordered(
            "const id = CSS.escape(panelId);",
            "const content = djDebug.querySelector(`#${id}`);",
        ),
    ),
    (
        "panel-key-escaped-before-nav-lookup",
        _ordered(
            "const id = CSS.escape(panelId);",
            "djDebug.querySelector(`#djdt-${id}`)",
        ),
    ),
    ("no-upstream-raw-panel-key-binding", _absent("([id, panel])")),
    # Shadow-DOM handle resolution: debug-toolbar>=7 defaults USE_SHADOW_DOM=True,
    # so #djDebug lives in #djDebugRoot's shadow tree and nav nodes are queried
    # under the resolved handle, never off document. The absence row names the
    # spelling upstream wraps across three lines, so a verbatim paste fails it.
    ("shadow-dom-root-lookup", _present('getElementById("djDebugRoot")')),
    ("shadow-dom-shadow-root-branch", _present("shadowRoot")),
    ("shadow-dom-inner-query", _present('querySelector("#djDebug")')),
    ("nav-lookup-scoped-to-handle", _present("djDebug.querySelector(`#djdt-${id}`)")),
    ("no-document-level-nav-lookup", _absent(".getElementById(`djdt-${id}`)")),
    # Per-node null guards: a toolbar release or a consumer customization may
    # retain a panel container while omitting one of its descendants, and the
    # patched globals must still return the scrubbed response. The absence row
    # names upstream's chained write, which throws the moment a node is missing.
    (
        "panel-title-node-lookup",
        _present('const panelTitle = content.querySelector(".djDebugPanelTitle");'),
    ),
    ("panel-title-node-guarded", _present("if (panelTitle !== null)")),
    ("heading-node-lookup", _present('const heading = panelTitle.querySelector("h3");')),
    ("heading-node-guarded", _present("if (heading !== null)")),
    ("scroll-node-lookup", _present('const scroll = content.querySelector(".djdt-scroll");')),
    ("scroll-node-guarded", _present("if (scroll !== null)")),
    ("loader-node-lookup", _present('const loader = content.querySelector(".djdt-loader");')),
    ("loader-node-guarded", _present("if (loader === null)")),
    (
        "panel-content-node-lookup",
        _present('const panelContent = content.querySelector(".djDebugPanelContent");'),
    ),
    ("panel-content-node-guarded", _present("if (panelContent !== null)")),
    ("nav-subtitle-node-lookup", _present('const subtitle = nav.querySelector("small");')),
    ("nav-subtitle-node-guarded", _present("if (subtitle !== null)")),
    ("no-upstream-chained-panel-title-write", _absent('.querySelector("h3").textContent')),
    # Payload-shape guard: the DOM update runs only for a debugToolbar value
    # whose keys can be read, and skips a single panel entry whose cannot -
    # asked once, of the answer, by a record predicate defined in one place.
    (
        "payload-shape-guard-present",
        _present("if (!isRecord(toolbar) || !isRecord(toolbar.panels)) return data;"),
    ),
    (
        "payload-shape-guard-before-panel-loop",
        _ordered(
            "if (!isRecord(toolbar) || !isRecord(toolbar.panels)) return data;",
            "Object.entries(toolbar.panels)",
        ),
    ),
    ("panel-record-guard-present", _present("if (!isRecord(panel)) return;")),
    (
        "panel-record-guard-first-in-loop",
        _ordered(
            "Object.entries(toolbar.panels)",
            "if (!isRecord(panel)) return;",
            "if (panel.title)",
        ),
    ),
    ("is-record-helper-defined-once", _defined_once("function isRecord(")),
    (
        "is-record-predicate-is-a-record-test",
        _present('return value !== null && typeof value === "object";'),
    ),
    ("no-post-scrub-read-of-panels", _absent("data.debugToolbar.panels")),
    ("no-post-scrub-read-of-request-id", _absent("data.debugToolbar.requestId")),
)


@pytest.mark.parametrize(
    ("name", "predicate"),
    _TEMPLATE_CONTRACT,
    ids=[name for name, _ in _TEMPLATE_CONTRACT],
)
def test_template_port_invariants_and_robustness_divergence(name, predicate):
    """One row per form the copied asset must keep, invariants and divergences alike.

    The suite has no JS runtime, so this does not prove the script WORKS - it
    turns the template-port checklist's by-eye diff into a mechanical guard.
    What the parametrization buys is failability: a test row is one failing node
    id, so a monolithic body would score exactly one row whether a future edit
    dropped one guard or every guard. Here each form fails its own rows - a
    silent revert to upstream's unsafe verbatim shape fails the reverted form's
    presence rows AND the row asserting upstream's spelling is gone, which is the
    half a presence check cannot supply.
    """
    assert predicate(_template_text()), name
