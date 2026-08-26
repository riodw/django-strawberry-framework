# Review: `django_strawberry_framework/middleware/`

Status: verified

## Understanding

`django_strawberry_framework/middleware/` provides the package's Django HTTP middleware integrations, maintaining clean isolation of soft dependencies and robust lifecycle coordination with Django request/response handling.

The subpackage comprises:
1. **`__init__.py` (Import-clean package boundary):**
   - Implements an empty, import-clean boundary (no re-exports) so `import django_strawberry_framework.middleware` succeeds on environments without `django-debug-toolbar` installed, allowing whole-package introspection, walker tools (`docs/TREE.md`), and test runners to traverse the package safely without raising soft-dependency errors.
   - Requires consumers to reference full leaf dotted paths in `settings.MIDDLEWARE` (e.g. `django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware` or `django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware`).
2. **`debug_toolbar.py` (`DebugToolbarMiddleware`):**
   - Subclasses `debug_toolbar.middleware.DebugToolbarMiddleware` to provide Django Debug Toolbar integration for Strawberry GraphQL views.
   - Manages soft-dependency isolation via `require_debug_toolbar()` and prevents cryptic model registration errors via pre-emptive `apps.is_installed("debug_toolbar")` checks at module import time.
   - In `process_view`, identifies Strawberry views (`strawberry.django.views.BaseView`) with defensive type checks (`isinstance(view, type)`) to avoid crashing on non-class view attributes.
   - In `_postprocess`, delegates to upstream toolbar processing, preserves streaming and pre-encoded responses untouched, injects the GraphiQL bridge template (`templates/django_strawberry_framework/debug_toolbar.html`) on 200 HTML responses, and attaches panel metadata (`_get_payload`) to JSON responses while safely bypassing `IntrospectionQuery` to avoid history flooding.
3. **`request_body.py` (`GraphQLRequestBodyBoundaryMiddleware`):**
   - Relocates the raw-request-body boundary enforcement ahead of `CsrfViewMiddleware` in the Django middleware pipeline, preventing unbounded multipart payload parsing during CSRF token inspection.
   - Validates middleware ordering at startup (`_require_boundary_before_csrf`) to ensure the first boundary middleware entry precedes the first CSRF middleware entry.
   - Supports both synchronous and asynchronous execution (`sync_capable = True`, `async_capable = True`) with deterministic request publication via `_boundary_middleware_request` (`ContextVar`).
   - In `process_view`, recognizes package views defensively (`_package_view_instance`), invokes the view's `setup()` lifecycle, runs `_BOUNDARY_METHOD`, translates `HTTPException` into plain text `HttpResponse`, and stores `(mount, view)` on the request under `_BOUNDARY_PREPARED_VIEW` while stamping `_BOUNDARY_ENFORCED = True`.

## Verification

1. **Cross-module lifecycle & boundary tracing:**
   - Traced interaction between `GraphQLRequestBodyBoundaryMiddleware` and `DebugToolbarMiddleware` when both are active in `settings.MIDDLEWARE`.
   - Verified that `DebugToolbarMiddleware.process_view` and `GraphQLRequestBodyBoundaryMiddleware.process_view` execute independently without conflicting state or lifecycle collisions.
   - Verified that `DebugToolbarMiddleware._postprocess` reliably inspects `request.body` for `operationName` without stream exhaustion or unparsed body issues because `HttpRequest.body` caches read bytes and `GraphQLRequestBodyBoundaryMiddleware` already safely measured the payload.
2. **Permanent test evaluation:**
   - Examined `tests/middleware/test_debug_toolbar.py` (soft dependency absence, invalid configurations, streaming bypass, response encoding, panel payload construction, GraphiQL bridge templates).
   - Examined `tests/test_views.py` (middleware ordering validation, custom CSRF subclasses, multiple boundary entries, async handling, view recognition error isolation).
   - Examined `examples/fakeshop/test_query/test_debug_toolbar_api.py` and `examples/fakeshop/test_query/test_transport_api.py` (live end-to-end HTTP integration under sync/async transports, GraphiQL bridge injection, toolbar SQL tracking, CSRF enforcement).
3. **Focused test execution:**
   - Ran `uv run pytest tests/middleware/test_debug_toolbar.py tests/test_views.py examples/fakeshop/test_query/test_debug_toolbar_api.py examples/fakeshop/test_query/test_transport_api.py --no-cov` (333 passed in 26.94s).
4. **Folder-level scratch verification:**
   - Executed `docs/review/temp-tests/middleware/test_scratch_middleware_folder.py` verifying clean package `__init__` imports, combined sync middleware chain execution with `DjangoGraphQLView`, and async middleware chain execution with `AsyncDjangoGraphQLView` (3 passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The `django_strawberry_framework/middleware/` subpackage forms a cohesive, robust, and well-isolated component. Its clean module boundary protects environments without optional dependencies, while the two middleware classes seamlessly manage pre-CSRF request body validation and GraphQL debug toolbar instrumentation without lifecycle leaks or ordering conflicts.

## Implementation (Worker 1)

- **Changed files:** None — zero-edit cycle.
- **Scoped diff against HEAD (`12779c99`):** empty.
- **Permanent tests and pinned behavior:**
  - Existing test suites (`tests/middleware/test_debug_toolbar.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_debug_toolbar_api.py`, `examples/fakeshop/test_query/test_transport_api.py`) comprehensively cover all 333 test cases spanning soft dependency gates, lifecycle stages, sync/async execution, response mutation, and CSRF ordering.
- **Scratch verification:**
  - `docs/review/temp-tests/middleware/test_scratch_middleware_folder.py` passed (3 passed) confirming package import cleanliness and simultaneous middleware execution under sync and async transports.
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/middleware/` (0 errors, all checks passed).
  - `uv run ruff format --check django_strawberry_framework/middleware/` (clean, 3 files already formatted).
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, subpackage behavior verified unchanged.
 
+## Independent verification (Worker 2)
+
+- **Verification scope:** Complete folder pass across `django_strawberry_framework/middleware/` (`__init__.py`, `debug_toolbar.py`, `request_body.py`).
+- **Re-tracing and behavioral checks:**
+  1. *Package boundary & import isolation:* Verified `django_strawberry_framework/middleware/__init__.py` contains no re-exports, permitting clean imports and tree walkers when `django-debug-toolbar` is not installed in the environment.
+  2. *Soft-dependency gates:* Verified `DebugToolbarMiddleware` uses `require_debug_toolbar()` and guards against uninstalled django-debug-toolbar or uninstalled apps configurations before initializing toolbar panels.
+  3. *Middleware pipeline coordination:* Verified concurrent chain execution with `GraphQLRequestBodyBoundaryMiddleware` placed ahead of `CsrfViewMiddleware` and `DebugToolbarMiddleware`. Confirmed `process_view` hooks coordinate cleanly: `DebugToolbarMiddleware` identifies Strawberry views and sets `_is_graphiql`, while `GraphQLRequestBodyBoundaryMiddleware` enforces raw request size limits and sets `_BOUNDARY_ENFORCED`.
+  4. *CSRF ordering validation:* Confirmed startup check `_require_boundary_before_csrf` correctly inspects the first occurrence of boundary and CSRF middleware in `settings.MIDDLEWARE`.
+  5. *Async capability:* Verified `GraphQLRequestBodyBoundaryMiddleware` supports async middleware execution with `AsyncDjangoGraphQLView` using `_boundary_middleware_request` context variable for isolation across tasks.
+- **Test execution:**
+  - `uv run pytest docs/review/temp-tests/middleware/test_scratch_middleware_folder.py tests/middleware/test_debug_toolbar.py tests/test_views.py --no-cov` (251 passed).
+  - `uv run pytest examples/fakeshop/test_query/test_debug_toolbar_api.py examples/fakeshop/test_query/test_transport_api.py --no-cov` (85 passed).
+- **Findings disposition:** Zero unresolved findings. No code edits or permanent test promotions required for this folder pass.
+- **Conclusion:** Subpackage behavior verified; all contracts and boundaries operate cleanly and safely.

