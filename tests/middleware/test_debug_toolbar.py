"""Planning anchors for spec-042 DebugToolbarMiddleware tests."""

# TODO(spec-042 Slice 1): Build this suite only after adding
# django-debug-toolbar>=7.0.0 to the dev dependency group and regenerating
# uv.lock. Do not run pytest unless the maintainer explicitly asks.
#
# Fixture pseudo-code:
# - reload_all_project_schemas() first, before URLconf setup.
# - Save and evict tests.middleware.debug_toolbar_urls from sys.modules.
# - Enable DEBUG=True so debug_toolbar_urls() returns routes and the toolbar's
#   default DEBUG gate is open.
# - Append "debug_toolbar" to INSTALLED_APPS with modify_settings.
# - Build MIDDLEWARE from settings.MIDDLEWARE, inserting
#   "django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware"
#   near the front while ensuring the stock debug_toolbar middleware is absent.
# - Set ROOT_URLCONF by dotted path:
#   "tests.middleware.debug_toolbar_urls".
# - Set DEBUG_TOOLBAR_CONFIG with an always-true SHOW_TOOLBAR_CALLBACK.
# - Clear debug_toolbar.middleware.show_toolbar_func_or_path on setup and
#   teardown.
# - Save DebugToolbar._panel_classes and DebugToolbar._urlpatterns, set both to
#   None for the test, then restore the saved values on teardown.
# - Evict tests.middleware.debug_toolbar_urls again on teardown so the next
#   import recomputes urlpatterns under that test's DEBUG value.
#
# Toolbar-present real-request pseudo-code:
# - Mark the present-path group with pytest.mark.django_db.
# - GraphiQL GET /graphql/: assert 200 HTML, stock toolbar handle present,
#   package template script present, and Content-Length correct when present.
# - No-toolbar baseline GET /graphql/ without the fixture: assert normal
#   GraphiQL HTML, no stock handle, and no package script. Do not assert the
#   package leaf module is absent from sys.modules because xdist order can make
#   that import-state assertion flaky.
# - Every product-query test starts with seed_data(1) as the first executable
#   line.
# - POST a named products operation with operationName="ToolbarItems": assert
#   data is intact, debugToolbar exists, requestId exists, SQLPanel has a
#   subtitle, and TemplatesPanel is absent.
# - POST a real introspection query with operationName="IntrospectionQuery":
#   assert no debugToolbar key.
# - GET /graphql/?query=... with HTTP_ACCEPT="application/json": assert the
#   content type before body inspection, then assert debugToolbar injection.
# - Fetch the SQL panel through the real debug_toolbar_urls() route using the
#   injected requestId. Assert JSON response shape with content/scripts, assert
#   the "isn't available anymore" fallback is absent, and assert a seeded-query
#   SQL marker is present.
# - For HTML negative detection, drive fakeshop's index view and LoginView:
#   assert no package-appended script and no debugToolbar body key, but allow
#   the stock toolbar handle because the always-true callback may render it.
# - For JSON negative detection, drive the test URLconf's JSON probe view and
#   assert the body is exactly the probe payload with no debugToolbar key.
#
# Toolbar-absent pseudo-code:
# - Reuse the channels two-sided restore discipline, targeting
#   debug_toolbar*, django_strawberry_framework.middleware.debug_toolbar, and
#   the parent django_strawberry_framework.middleware.debug_toolbar attribute.
# - The import blocker must intercept only absolute top-level debug_toolbar
#   imports so the package leaf reaches require_debug_toolbar().
# - Assert import django_strawberry_framework and import
#   django_strawberry_framework.middleware both succeed.
# - Assert importing the leaf raises ImportError with the re-typed literal
#   "django-debug-toolbar>=7.0.0" and chains the original ImportError.
# - After restore, assert the leaf imports again in the same process and the
#   parent attribute is the same object as sys.modules[leaf_name].
# - Assert require_debug_toolbar() returns the imported top-level debug_toolbar
#   module when present and raises the install hint under the import block.
#
# Targeted-unit pseudo-code:
# - StreamingHttpResponse: after stock _postprocess completes, assert the
#   package branch appended no script and injected no debugToolbar payload.
# - _get_payload with toolbar.request_id = None returns None.
# - _get_payload with a panel whose has_content is false emits title None while
#   preserving subtitle behavior.
# - HTML and JSON mutation paths refresh Content-Length only when that header
#   was already present.
#
# Template-port pseudo-code:
# - Read or render the final template asset and assert the five spec-042
#   invariants from the template-port checklist using exact production
#   substrings/patterns.
