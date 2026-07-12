"""Debug-toolbar middleware: the django-debug-toolbar SQL-panel window into ``/graphql/`` requests.

``DebugToolbarMiddleware`` subclasses the stock
``debug_toolbar.middleware.DebugToolbarMiddleware`` and contributes exactly the
two GraphQL-shaped overrides its strawberry-graphql-django counterpart ships
(``strawberry_django/middlewares/debug_toolbar.py``, itself based on the
archived https://github.com/flavors/django-graphiql-debug-toolbar project):
``process_view`` tags requests whose resolved view is a Strawberry Django view
(``strawberry.django.views.BaseView``), and ``_postprocess`` appends the
GraphiQL bridge template to the IDE's HTML page and injects the ``debugToolbar``
panel payload into tagged JSON operation responses (introspection queries
skipped, spec-042 Decision 8). Everything else - panels, request tracking,
history storage, handle rendering, show-toolbar gating - stays the stock
toolbar's own (spec-042 Decision 6).

``django-debug-toolbar`` is a SOFT dependency (the package's third, after
djangorestframework and channels). Importing THIS leaf module is the opt-in
boundary - Django's ``MIDDLEWARE`` dotted path reaches it via ``import_string``
at server startup - so ``require_debug_toolbar()`` runs at module import time
(the ``rest_framework/`` shape, spec-042 Decision 5) and a toolbar-less machine
gets one actionable install-hint ``ImportError`` at the first moment the
integration is reached for, while ``import django_strawberry_framework`` and
``import django_strawberry_framework.middleware`` both stay clean.

Wiring (the toolbar's own three standard pieces, one package-specific swap):
list ``"debug_toolbar"`` in ``INSTALLED_APPS``, list this class's dotted path
near the front of ``MIDDLEWARE`` REPLACING the stock
``debug_toolbar.middleware.DebugToolbarMiddleware`` entry (it subclasses it;
listing both runs the toolbar twice), and add ``debug_toolbar_urls()`` to the
URLconf - omitting the URLconf step fails every toolbar-processed request with
``NoReverseMatch``, not a quiet panel-click 404. Omitting ``"debug_toolbar"``
from ``INSTALLED_APPS`` raises ``ImproperlyConfigured`` at leaf import (a second
wiring gate, spec-042 Error shapes): the ``debug_toolbar.middleware`` import
below defines a Django model, and an unregistered app would otherwise surface
Django's cryptic ``HistoryEntry`` app-label ``RuntimeError`` instead.

The Python middleware keeps two narrow, deliberate robustness divergences from
the verbatim upstream borrow, both documented in spec-042: ``process_view``
guards ``issubclass`` with ``isinstance(view, type)`` (this middleware runs for
ALL global traffic, and a non-class ``view_class`` must not ``TypeError``/500 an
unrelated view), and ``_get_payload`` bails to ``None`` when a declared-JSON
body cannot be decoded or parsed, or when the decoded body is not an object (a
dev-only tool must not turn an unusual response into a 500). The injected
GraphiQL bridge template carries the third documented divergence: defensive
DOM guards that keep ``debugToolbar`` payload scrubbing mandatory while
treating the toolbar DOM updates as best-effort. No other Python behavior
differs.
"""

from __future__ import annotations

import collections
import json
from collections.abc import Callable
from typing import Any

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from django_strawberry_framework.utils.imports import require_optional_module

# The single django-debug-toolbar install-hint string (spec-042 Decision 5).
# Every toolbar-absent raise routes through ``require_debug_toolbar()`` so the
# hint lives in exactly one source location and names the verified floor
# (place 2 of the three-places-that-must-agree: place 1 is the
# ``[dependency-groups].dev`` pin in ``pyproject.toml``, place 3 is the
# re-typed test literal; all three say ``>=7.0.0``).
_DEBUG_TOOLBAR_INSTALL_HINT: str = (
    "DebugToolbarMiddleware requires django-debug-toolbar, which is not installed. Install it "
    "with `pip install 'django-debug-toolbar>=7.0.0'` (the package's verified debug-toolbar "
    "floor)."
)

# The single "debug_toolbar app not in INSTALLED_APPS" hint (spec-042 Error
# shapes). django-debug-toolbar's ``middleware`` import chain defines a Django
# model (``debug_toolbar.models.HistoryEntry`` via ``debug_toolbar.store``), so
# importing this leaf without ``"debug_toolbar"`` in ``INSTALLED_APPS`` would
# otherwise fail with Django's cryptic model-registration ``RuntimeError``
# (naming ``HistoryEntry``, never the missing app). The ``apps.is_installed``
# gate below turns that into one actionable ``ImproperlyConfigured``.
_DEBUG_TOOLBAR_APP_HINT: str = (
    'DebugToolbarMiddleware requires "debug_toolbar" in INSTALLED_APPS. Add "debug_toolbar" to '
    "INSTALLED_APPS before using "
    '"django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware".'
)


def require_debug_toolbar() -> Any:
    """Import + return the top-level ``debug_toolbar`` package, or raise the install hint.

    A thin wrapper over ``utils/imports.py::require_optional_module`` (spec-042
    Helper-reuse D1 - never a fourth hand-rolled import pattern): present, the
    imported ``debug_toolbar`` module is returned; absent, the ``ImportError``
    is re-raised carrying the single ``_DEBUG_TOOLBAR_INSTALL_HINT`` string with
    the original chained (``__cause__``). Only the TOP-LEVEL package is guarded:
    a present-but-broken install whose ``debug_toolbar.middleware`` submodule
    fails propagates its own raw ``ImportError`` from the statement imports
    below, naming the real missing module (spec-042 Error shapes). No
    memoization - each call re-runs the import so eviction-simulated absence
    tests can re-hit the guard in one process.
    """
    return require_optional_module("debug_toolbar", install_hint=_DEBUG_TOOLBAR_INSTALL_HINT)


require_debug_toolbar()

# Second wiring gate (spec-042 Error shapes): the top-level package imports, but
# the ``debug_toolbar.middleware`` import below reaches
# ``debug_toolbar.models.HistoryEntry`` - defining a Django model requires
# ``"debug_toolbar"`` in ``INSTALLED_APPS``, else Django raises a cryptic
# ``HistoryEntry`` app-label ``RuntimeError`` that never names the missing app.
# The app registry is ready by the time Django's ``MIDDLEWARE`` resolution
# imports this leaf, so pre-check it and raise the one actionable
# ``ImproperlyConfigured`` (an ``INSTALLED_APPS`` omission is a settings error;
# ``ImproperlyConfigured`` is Django's idiom for it).
if not apps.is_installed("debug_toolbar"):
    raise ImproperlyConfigured(_DEBUG_TOOLBAR_APP_HINT)

# Everything below needs the optional dependency, so the guard above must run
# first and these imports stay beneath it (spec-042 Decision 5); ``E402`` is
# the deliberate price of the import-time-guard shape.
from debug_toolbar.middleware import (  # noqa: E402
    DebugToolbarMiddleware as _DebugToolbarMiddleware,
)
from debug_toolbar.toolbar import DebugToolbar  # noqa: E402
from django.core.serializers.json import DjangoJSONEncoder  # noqa: E402
from django.http.request import HttpRequest  # noqa: E402
from django.http.response import HttpResponse  # noqa: E402
from django.template.loader import render_to_string  # noqa: E402
from django.utils.encoding import force_str  # noqa: E402
from strawberry.django.views import BaseView  # noqa: E402

# The content-type sniff set for the HTML injection path (upstream verbatim).
_HTML_TYPES = {"text/html", "application/xhtml+xml"}


def _get_payload(
    request: HttpRequest,  # noqa: ARG001 - upstream-verbatim signature (spec-042 Decision 6)
    response: HttpResponse,
    toolbar: DebugToolbar,
) -> dict | None:
    """Build the ``debugToolbar`` payload for a JSON operation response, or ``None``.

    ``None`` when the toolbar assigned no ``request_id`` (nothing to reference),
    when the response bytes cannot be decoded with their declared charset, when
    the decoded text is not valid JSON, or when the decoded body is not a JSON
    object. Those response-shape guards leave an unusual declared-JSON response
    untouched instead of turning a development diagnostic into a 500. Otherwise
    the decoded body gains a top-level ``debugToolbar`` object carrying the
    toolbar ``requestId`` plus, per enabled panel, its ``title`` (only when
    ``panel.has_content`` - ``None`` tells the frontend not to touch that panel's
    content area) and ``nav_subtitle``, each called when callable.
    ``TemplatesPanel`` is skipped (upstream's deliberate exclusion: its nav
    content churns per request and floods the payload).
    """
    if not toolbar.request_id:
        return None

    try:
        content = force_str(response.content, encoding=response.charset)
        payload = json.loads(content, object_pairs_hook=collections.OrderedDict)
    except (json.JSONDecodeError, LookupError, UnicodeError):
        return None
    if not isinstance(payload, dict):
        return None

    payload["debugToolbar"] = collections.OrderedDict(
        [("panels", collections.OrderedDict())],
    )
    payload["debugToolbar"]["requestId"] = toolbar.request_id

    for panel in reversed(toolbar.enabled_panels):
        if panel.panel_id == "TemplatesPanel":
            continue

        title = panel.title if panel.has_content else None

        subtitle = panel.nav_subtitle
        payload["debugToolbar"]["panels"][panel.panel_id] = {
            "title": title() if callable(title) else title,
            "subtitle": subtitle() if callable(subtitle) else subtitle,
        }

    return payload


class DebugToolbarMiddleware(_DebugToolbarMiddleware):
    """The stock debug-toolbar middleware taught to see Strawberry ``/graphql/`` traffic.

    Referenced by dotted settings path
    (``django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware``)
    in ``MIDDLEWARE``, REPLACING the stock toolbar entry. The class name matches
    both upstream and the stock toolbar deliberately - a Django middleware's
    public identity is its dotted path, and the class name is the ecosystem
    convention (spec-042 Decision 3). Injection is view-scoped, not IDE-scoped:
    while the toolbar is enabled, EVERY JSON response from a Strawberry Django
    view gets the ``debugToolbar`` key (minus ``IntrospectionQuery``), whether
    the request came from GraphiQL or a programmatic client; the bridge
    template strips the key only inside the GraphiQL page.
    """

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., HttpResponse],
        *args,
        **kwargs,
    ) -> None:
        """Tag the request when its resolved view is a Strawberry Django view.

        ``view_class`` is the attribute Django's ``View.as_view()`` sets on the
        returned callable (and ``functools.wraps``-copying decorators such as
        ``ensure_csrf_cookie`` preserve). The ``isinstance(view, type)`` guard
        in front of ``issubclass`` is the module's first deliberate divergence
        from upstream (spec-042 Decision 7): this middleware runs for ALL
        global traffic, and a non-class ``view_class`` attached by an unrelated
        decorator would make a bare ``issubclass`` raise ``TypeError`` and 500
        the request. No ``super()`` chain: the stock toolbar middleware defines
        no ``process_view`` hook to preserve.
        """
        view = getattr(view_func, "view_class", None)
        request._is_graphiql = isinstance(view, type) and issubclass(view, BaseView)

    def _postprocess(
        self,
        request: HttpRequest,
        response: HttpResponse,
        toolbar: DebugToolbar,
    ) -> HttpResponse:
        """Run the stock postprocess, then arm the two GraphQL response shapes.

        Overrides (and chains FIRST to) the stock toolbar's private
        ``_postprocess`` - the knowingly borrowed coupling upstream carries too
        (spec-042 Risks). The stock method generates per-panel stats/timing,
        renders and stores the toolbar for every processed response (the
        mechanism the panel-content routes ride), adds headers, and inserts the
        handle into processable HTML. This override then: returns streaming
        responses untouched; appends the GraphiQL bridge template to tagged
        200 HTML responses; and re-encodes tagged ``application/json``
        operation responses with the ``_get_payload`` injection (skipping
        ``IntrospectionQuery``), refreshing ``Content-Length`` on both mutation
        paths only when the header is already present.
        """
        response = super()._postprocess(request, response, toolbar)

        if response.streaming:
            return response

        content_type = response.get("Content-Type", "").split(";")[0]
        is_html = content_type in _HTML_TYPES
        is_graphiql = getattr(request, "_is_graphiql", False)

        if is_html and is_graphiql and response.status_code == 200:
            template = render_to_string("django_strawberry_framework/debug_toolbar.html")
            response.write(template)
            if "Content-Length" in response:
                response["Content-Length"] = len(response.content)

        if is_html or not is_graphiql or content_type != "application/json":
            return response

        try:
            operation_name = json.loads(request.body).get("operationName")
        except Exception:  # upstream verbatim: any unreadable body degrades to "inject"
            operation_name = None

        # Do not return the payload for introspection queries, otherwise IDEs
        # such as apollo sandbox that query the introspection all the time will
        # remove older results from the history (spec-042 Decision 8).
        payload = (
            _get_payload(request, response, toolbar)
            if operation_name != "IntrospectionQuery"
            else None
        )
        if payload is None:
            return response

        response.content = json.dumps(payload, cls=DjangoJSONEncoder)
        if "Content-Length" in response:
            response["Content-Length"] = len(response.content)

        return response
