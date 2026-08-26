# Review: `django_strawberry_framework/middleware/debug_toolbar.py`

Status: verified

## Understanding

`django_strawberry_framework/middleware/debug_toolbar.py` provides the package's Django Debug Toolbar integration (`DebugToolbarMiddleware`), subclassing `debug_toolbar.middleware.DebugToolbarMiddleware`.

It owns:
1. **Soft-dependency isolation and configuration validation:**
   - Provides `require_debug_toolbar()` wrapping `utils.imports.require_optional_module("debug_toolbar", ...)`. Importing root packages (`django_strawberry_framework` or `django_strawberry_framework.middleware`) remains clean and raises no error when `django-debug-toolbar` is uninstalled.
   - Raises an actionable `ImportError` with install instructions when `django_strawberry_framework.middleware.debug_toolbar` is imported without `django-debug-toolbar` installed.
   - Validates `apps.is_installed("debug_toolbar")` at module load time, raising an actionable `ImproperlyConfigured` before Django's model registry raises a cryptic `RuntimeError` regarding `HistoryEntry`.
2. **Strawberry view recognition in `process_view`:**
   - Inspects `view_func.view_class` and stamps `request._is_graphiql = issubclass(view, BaseView)` where `BaseView` is `strawberry.django.views.BaseView`.
   - Defensively guards `issubclass` with `isinstance(view, type)` to prevent `TypeError` when unrelated middlewares or decorators attach non-class objects to `view_class`.
3. **Response postprocessing and GraphQL payload injection in `_postprocess`:**
   - Chains to `super()._postprocess(request, response, toolbar)` first, preserving stock toolbar timing, panel generation, and history storage.
   - Bails out early without mutating streaming responses (`response.streaming`) or pre-encoded responses (`Content-Encoding` present) to prevent corruption.
   - For tagged 200 HTML responses (`is_html and is_graphiql and response.status_code == 200`), renders and appends the GraphiQL bridge template (`templates/django_strawberry_framework/debug_toolbar.html`) and updates `Content-Length` if present.
   - For tagged `application/json` responses:
     - Extracts `operationName` safely from `request.body` (degrading to `None` if `request.body` is absent or unparseable).
     - Skips payload injection for `operationName == "IntrospectionQuery"` to prevent IDE background polling from flooding toolbar history.
     - Calls `_get_payload(request, response, toolbar)` to assemble panel metadata (`requestId`, panel titles/subtitles, skipping `TemplatesPanel` and inactive panels).
     - Re-serializes the payload with `DjangoJSONEncoder` and updates `Content-Length` if present.

## Verification

1. Traced connections across callers, dependencies, templates, and tests:
   - `django_strawberry_framework/middleware/__init__.py` (import-clean package marker)
   - `django_strawberry_framework/utils/imports.py` (`require_optional_module`)
   - `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` (GraphiQL bridge script with DOM and shadow root defensive guards)
   - `debug_toolbar.middleware.DebugToolbarMiddleware` and `debug_toolbar.toolbar.DebugToolbar`
   - `strawberry.django.views.BaseView`
2. Evaluated existing permanent tests in `tests/middleware/test_debug_toolbar.py` and `examples/fakeshop/test_query/test_debug_toolbar_api.py`:
   - Soft-dependency absence matrix (clean root/parent imports, install-hint error propagation, two-sided eviction/restore).
   - Broken install error propagation and missing `INSTALLED_APPS` `ImproperlyConfigured` gate.
   - Streaming response passthrough, pre-encoded response passthrough, and untagged JSON passthrough.
   - `_get_payload` handling (absent `request_id`, non-object JSON bodies, malformed JSON, and panel title/subtitle evaluation).
   - `process_view` defensive handling of non-class `view_class` values.
   - `Content-Length` recalculation on HTML appends and JSON re-encodes.
   - GraphiQL bridge template structural invariants.
   - Live HTTP integration under `DEBUG=True` (GraphiQL HTML handle/bridge injection, production inertness under `DEBUG=False`, named query SQL panel tracking, introspection query exclusion, JSON-Accept GET handling, round-trip SQL panel inspection via `requestId`, and non-Strawberry view passthrough).
3. Executed focused test runs:
   - `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py --no-cov` (27 passed).
4. Executed scratch verification tests `docs/review/temp-tests/middleware/test_scratch_debug_toolbar.py`:
   - Verified soft dependency contract functions and hint constants.
   - Verified `process_view` recognition matrix across `BaseView`, `GraphQLView`, `AsyncGraphQLView`, custom subclasses, non-Strawberry classes, and non-class values (`str`, `int`, `dict`, `list`, `object`, `None`).
   - Verified `_get_payload` handling (no request ID, non-object JSON responses, malformed JSON, unknown charsets, static and callable titles/subtitles, content-free panels, and TemplatesPanel omission).
   - Verified `_postprocess` edge cases (streaming passthrough, encoded response passthrough, non-200 HTML status, 200 HTML injection + Content-Length update, untagged request passthrough, non-JSON/non-HTML content types, non-200 JSON responses e.g. 400 GraphQL errors, and introspection query skip).
   - Result: 4 passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/middleware/debug_toolbar.py` is a concise, robust, and clean middleware subclass. It seamlessly adapts Django Debug Toolbar to Strawberry GraphQL views, cleanly isolates the optional dependency, prevents cryptic startup errors via pre-emptive `INSTALLED_APPS` checking, and defensively guards against non-standard view attributes and non-object responses. All public contracts, wire behaviors, and edge cases are thoroughly verified.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/middleware/test_debug_toolbar.py` and `examples/fakeshop/test_query/test_debug_toolbar_api.py`) comprehensively pins soft-dependency handling, `INSTALLED_APPS` validation, view tagging, streaming/encoding bypasses, payload construction, introspection skipping, `Content-Length` management, and live HTTP panel resolution.
- Scratch verification:
  - `docs/review/temp-tests/middleware/test_scratch_debug_toolbar.py` passed (4/4 test functions covering 25+ assertions) verifying view recognition matrices, error resilience, payload construction, and postprocessing edge cases.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/middleware/debug_toolbar.py` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/middleware/debug_toolbar.py` passed (1 file already formatted).
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

1. **Production diff confirmation:**
   - Confirmed `git diff 12779c99 -- django_strawberry_framework/middleware/debug_toolbar.py` is empty (0 lines changed).
2. **Behavioral trace and contract verification:**
   - Re-traced `require_debug_toolbar()` and `apps.is_installed("debug_toolbar")` early import gates protecting root and middleware package imports while cleanly preventing cryptic Django `HistoryEntry` model registration errors.
   - Re-traced `process_view` defensive type check (`isinstance(view, type) and issubclass(view, BaseView)`) ensuring robust compatibility across all views without 500ing on non-class `view_class` attributes.
   - Re-traced `_postprocess` flow: stock `super()._postprocess` delegation, streaming and encoded response bypasses, GraphiQL HTML bridge template injection (`templates/django_strawberry_framework/debug_toolbar.html`) with `Content-Length` sync, JSON response inspection, `IntrospectionQuery` exclusion to avoid history churn, safe `_get_payload` panel formatting (skipping `TemplatesPanel` and non-content panels), and robust fallback on non-object / unparseable JSON bodies.
3. **Automated verification:**
   - Executed permanent test suite:
     - `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py --no-cov` (27 passed in 21.11s).
   - Executed disposable scratch test suite:
     - `uv run pytest docs/review/temp-tests/middleware/test_scratch_debug_toolbar.py --no-cov` (4 passed in 1.66s).
   - Checked linting and formatting:
     - `uv run ruff check django_strawberry_framework/middleware/debug_toolbar.py` (0 errors).
     - `uv run ruff format --check django_strawberry_framework/middleware/debug_toolbar.py` (already formatted).
4. **Conclusion:**
   - Zero findings; implementation is robust, well-tested, and fully conforms to spec. Status verified.

