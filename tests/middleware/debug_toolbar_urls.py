"""Test-only URLconf for the spec-042 debug-toolbar middleware tests.

Composes fakeshop's real ``urlpatterns`` with ``debug_toolbar_urls()`` (the
``djdt`` panel-content routes the stock toolbar render reverses on EVERY
processed response - omitting them is a hard ``NoReverseMatch``) plus a tiny
non-Strawberry JSON probe view (the Test 8 payload leak guard).

Import-ordering contract (spec-042 Decision 9): this module is referenced ONLY
by dotted path in the toolbar fixture's ``ROOT_URLCONF`` override - never
imported at test-module import time - and is evicted from ``sys.modules`` on
fixture setup and teardown, so this module body always executes under
``DEBUG=True``. ``debug_toolbar_urls()`` returns ``[]`` when ``DEBUG`` is
false, and ``urlpatterns`` are computed once at first import: an import under
pytest-django's forced ``DEBUG=False`` would permanently strand the ``djdt``
namespace for this module object.
"""

from config import urls as fakeshop_urls
from debug_toolbar.toolbar import debug_toolbar_urls
from django.http import JsonResponse
from django.urls import path


def _json_probe(request):
    """A non-Strawberry JSON view: its body must NEVER gain a ``debugToolbar`` key."""
    return JsonResponse({"probe": "ok"})


# Compose (never mutate) fakeshop's patterns, so evicting this module on
# fixture teardown leaves no global URL state behind.
urlpatterns = [
    *fakeshop_urls.urlpatterns,
    path("__debug_probe__.json", _json_probe, name="debug-toolbar-probe"),
    *debug_toolbar_urls(),
]
