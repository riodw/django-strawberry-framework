"""Planning URLconf for the spec-042 debug-toolbar middleware tests."""

# TODO(spec-042 Slice 1): Replace this stub with the test-only URLconf used by
# tests/middleware/test_debug_toolbar.py. It must be referenced only by dotted
# path in override_settings(ROOT_URLCONF=...), never imported at test-module
# import time.
#
# High-quality pseudo-code for the production test URLconf:
#
# 1. Import fakeshop's real urlpatterns from config.urls after the fixture has
#    set DEBUG=True and evicted this module from sys.modules.
# 2. Import debug_toolbar.toolbar.debug_toolbar_urls only after debug_toolbar is
#    installed by the Slice-1 dependency gate.
# 3. Define a tiny non-Strawberry JSON probe view returning JsonResponse with a
#    stable body such as {"probe": "ok"}.
# 4. Build urlpatterns as:
#      fakeshop_urlpatterns
#      + [path("__debug_probe__.json", json_probe, name="debug-toolbar-probe")]
#      + debug_toolbar_urls()
# 5. Do not mutate fakeshop's config.urls.urlpatterns in place; copy/compose so
#    teardown can evict this module without leaving global URL state behind.

raise NotImplementedError(
    "TODO(spec-042 Slice 1): debug-toolbar test URLconf is not implemented yet.",
)
