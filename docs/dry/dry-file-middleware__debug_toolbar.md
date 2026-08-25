# DRY review: `django_strawberry_framework/middleware/debug_toolbar.py`

Status: verified

## System trace

`django_strawberry_framework/middleware/debug_toolbar.py` provides the framework's integration with `django-debug-toolbar` ([spec-042][spec-042]). It exposes [`DebugToolbarMiddleware`][middleware-debug-toolbar], a subclass of `debug_toolbar.middleware.DebugToolbarMiddleware` that teaches the toolbar's SQL panel and request tracker to recognize and instrument Strawberry Django GraphQL requests. It owns the following responsibilities:

1. **Soft-Dependency Isolation and Startup Verification:**
   - `django-debug-toolbar` is the framework's third [soft dependency][glossary] (alongside `djangorestframework` and `channels`).
   - [`require_debug_toolbar`][middleware-debug-toolbar] invokes [`require_optional_module`][utils-imports] with [`_DEBUG_TOOLBAR_INSTALL_HINT`][middleware-debug-toolbar], executing at module top-level so that importing this leaf module serves as the explicit opt-in boundary ([spec-042][spec-042] Decision 5).
   - If `django-debug-toolbar` is installed but `"debug_toolbar"` is omitted from `INSTALLED_APPS`, the module pre-checks `apps.is_installed("debug_toolbar")` and raises `ImproperlyConfigured` carrying [`_DEBUG_TOOLBAR_APP_HINT`][middleware-debug-toolbar], avoiding Django's cryptic `HistoryEntry` model registration `RuntimeError`.

2. **Strawberry View Request Tagging:**
   - [`DebugToolbarMiddleware.process_view`][middleware-debug-toolbar] inspects the resolved view function (`getattr(view_func, "view_class", None)`) and tags the request with `request._is_graphiql = isinstance(view, type) and issubclass(view, BaseView)` ([spec-042][spec-042] Decision 7).
   - The `isinstance(view, type)` guard protects against non-class `view_class` attributes added by custom view decorators on unrelated traffic.

3. **Response Postprocessing and GraphQL Instrumentation:**
   - [`DebugToolbarMiddleware._postprocess`][middleware-debug-toolbar] first delegates to `super()._postprocess(request, response, toolbar)` to let the stock toolbar capture queries, render panels, and record history ([spec-042][spec-042] Decision 6).
   - Early returns leave streaming responses (`response.streaming`) and encoded/compressed bodies (`response.get("Content-Encoding", "")`) untouched.
   - For GraphiQL IDE HTML GET responses (`status_code == 200` and `Content-Type` in [`_HTML_TYPES`][middleware-debug-toolbar]), it appends the client-side bridge template (`django_strawberry_framework/debug_toolbar.html`) and refreshes `Content-Length`.
   - For tagged GraphQL JSON operation POST responses (`Content-Type == "application/json"`), it inspects `request.body` for `operationName`. If `operationName != "IntrospectionQuery"` ([spec-042][spec-042] Decision 8), it calls [`_get_payload`][middleware-debug-toolbar] and injects the `debugToolbar` dictionary into the response body via `DjangoJSONEncoder`, refreshing `Content-Length` if present.

4. **Toolbar Payload Construction:**
   - [`_get_payload`][middleware-debug-toolbar] extracts `toolbar.request_id` and iterates `toolbar.enabled_panels`, populating per-panel `title` (evaluated when callable, `None` when `not panel.has_content`) and `subtitle` (`nav_subtitle`), while excluding `TemplatesPanel`. If the JSON response cannot be parsed or is not a dictionary, it safely bails returning `None`.

5. **Client-Side GraphiQL Bridge Asset:**
   - `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` patches `JSON.parse` and `Response.prototype.json` in the browser, extracting `data.debugToolbar`, updating `#djDebug` DOM (supporting Shadow DOM via `#djDebugRoot` with light-DOM fallback), and deleting `data.debugToolbar` before GraphiQL processes the response payload.

Connected behavior examined:
- [`django_strawberry_framework/middleware/__init__.py`][middleware-init]: Package marker keeping `middleware/` import-clean without eager leaf re-exports ([spec-042][spec-042] Decision 3).
- [`django_strawberry_framework/middleware/request_body.py`][middleware-request-body]: Sibling Django HTTP middleware enforcing body byte caps before CSRF processing ([spec-046][spec-046]).
- [`django_strawberry_framework/extensions/debug.py`][extensions-debug]: `DjangoDebugExtension` schema extension providing in-band query logging in `extensions["debug"]` ([spec-044][spec-044]).
- [`django_strawberry_framework/utils/imports.py`][utils-imports]: `require_optional_module` raising primitive.
- [`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`][template-debug-toolbar]: Client-side GraphiQL DOM bridge template.
- [`tests/middleware/test_debug_toolbar.py`][test-middleware-debug-toolbar]: Soft-dependency absence matrix and targeted unit tests for `_postprocess`, `_get_payload`, `process_view`, and template port invariants.
- [`examples/fakeshop/test_query/test_debug_toolbar_api.py`][example-test-debug-toolbar-api]: Live HTTP integration tests driving GraphiQL HTML rendering, SQL panel payload injection, and panel content round-trips.
- [`examples/fakeshop/config/settings.py`][example-settings]: Reference application configuration wiring `debug_toolbar` app, `DebugToolbarMiddleware`, and `INTERNAL_IPS`.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/middleware/debug_toolbar.py --include-constants`):
- Target file contains 290 lines, 1 class definition (`DebugToolbarMiddleware`), 2 methods (`DebugToolbarMiddleware.process_view`, `DebugToolbarMiddleware._postprocess`), 2 functions (`require_debug_toolbar`, `_get_payload`), and 3 constants (`_DEBUG_TOOLBAR_INSTALL_HINT`, `_DEBUG_TOOLBAR_APP_HINT`, `_HTML_TYPES`).
- Verified soft-dependency isolation, startup configuration gates, request tagging, payload extraction, and response rewriting across unit and live integration suites.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   - **Middleware vs. Schema Extension:** `DebugToolbarMiddleware` operates at the Django HTTP middleware layer to feed `django-debug-toolbar`'s out-of-band UI panels and SQL store. Its in-band counterpart, [`DjangoDebugExtension`][extensions-debug], operates inside Strawberry's execution lifecycle to inject query logs into `extensions["debug"]`. Both maintain clear architectural boundaries without duplicating logic: `DjangoDebugExtension` instruments the schema execution phase via `SchemaExtension`, while `DebugToolbarMiddleware` instruments HTTP requests/responses via Django's middleware pipeline.
   - **Soft-Dependency Guards:** `require_debug_toolbar` mirrors the soft-dependency guard pattern established in `rest_framework/__init__.py` and `routers.py`, delegating directly to the centralized [`require_optional_module`][utils-imports] utility in `utils/imports.py`.
   - **Sibling Middleware:** `DebugToolbarMiddleware` and [`GraphQLRequestBodyBoundaryMiddleware`][middleware-request-body] are configured independently in `settings.MIDDLEWARE` via dotted strings. Neither is re-exported from `middleware/__init__.py`.
2. **Sync and async twins:**
   Zero duplication. `DebugToolbarMiddleware` subclasses stock `debug_toolbar.middleware.DebugToolbarMiddleware`, which handles Django's sync/async middleware protocol adaptation. `process_view` and `_postprocess` operate synchronously on `HttpRequest` and `HttpResponse` objects after resolution/execution, requiring no parallel async code paths.
3. **Derived rather than repeated knowledge:**
   - Soft-dependency installation hint [`_DEBUG_TOOLBAR_INSTALL_HINT`][middleware-debug-toolbar] defines the single verified floor (`django-debug-toolbar>=7.0.0`), passed directly to [`require_optional_module`][utils-imports].
   - View tagging derives `_is_graphiql` by dynamically inspecting `view_func.view_class` against `BaseView` rather than hardcoding URL patterns or view names.
   - Panel payload generation in [`_get_payload`][middleware-debug-toolbar] dynamically iterates `toolbar.enabled_panels`, reading `panel_id`, `has_content`, `title`, and `nav_subtitle` from the active panel instances.
   - Content-type sniffing in [`_postprocess`][middleware-debug-toolbar] matches against [`_HTML_TYPES`][middleware-debug-toolbar] (`{"text/html", "application/xhtml+xml"}`).
   - Client-side DOM resolution in `debug_toolbar.html` queries `#djDebug` dynamically across Shadow DOM (`#djDebugRoot.shadowRoot`) and light DOM fallback.
4. **Inverse and round-trip pairs:**
   - **Server Payload Injection & Browser DOM Scrubbing:** [`_get_payload`][middleware-debug-toolbar] and [`_postprocess`][middleware-debug-toolbar] construct and inject the `debugToolbar` object into the JSON response; the client-side bridge template `debug_toolbar.html` intercepts the JSON response in the browser, extracts `toolbar.requestId` and panel headings, updates `#djDebug`, and executes `delete data.debugToolbar` before GraphiQL parses the GraphQL payload. Verified in [`tests/middleware/test_debug_toolbar.py`][test-middleware-debug-toolbar] and [`examples/fakeshop/test_query/test_debug_toolbar_api.py`][example-test-debug-toolbar-api].
   - **Module Import & Absence Simulation:** Simulated absence via `sys.modules["debug_toolbar"] = None` raises `ImportError` with [`_DEBUG_TOOLBAR_INSTALL_HINT`][middleware-debug-toolbar]; restoration cleanly re-establishes module identity across `sys.modules` and parent module namespaces.
5. **Contracts restated in another medium:**
   The `DebugToolbarMiddleware` contract (subclassing, soft dependency, import-time guard, app registry check, `BaseView` tagging, template append, JSON payload injection, `IntrospectionQuery` skip, `Content-Length` refresh) is codified across:
   - Code: [`django_strawberry_framework/middleware/debug_toolbar.py`][middleware-debug-toolbar], [`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`][template-debug-toolbar], [`django_strawberry_framework/utils/imports.py`][utils-imports];
   - Specifications: [`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`][spec-042] (Decisions 1–10);
   - Test suites: [`tests/middleware/test_debug_toolbar.py`][test-middleware-debug-toolbar], [`examples/fakeshop/test_query/test_debug_toolbar_api.py`][example-test-debug-toolbar-api];
   - Example configuration: [`examples/fakeshop/config/settings.py`][example-settings], [`examples/fakeshop/config/urls.py`][example-urls];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary] (Debug-toolbar middleware, Soft dependency), [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Updating the verified `django-debug-toolbar` floor pin, e.g. `>=8.0.0`):**
  - Update `_DEBUG_TOOLBAR_INSTALL_HINT` in `django_strawberry_framework/middleware/debug_toolbar.py`.
  - *Sites that must move in `django_strawberry_framework/middleware/debug_toolbar.py`:* Exactly 1 site ([`_DEBUG_TOOLBAR_INSTALL_HINT`][middleware-debug-toolbar]).
  - *Site count in target:* 1.
- **Posited change 2 (Extending HTML content-type sniffing or adding a new HTML MIME type):**
  - Update `_HTML_TYPES` in `django_strawberry_framework/middleware/debug_toolbar.py`.
  - *Sites that must move in `django_strawberry_framework/middleware/debug_toolbar.py`:* Exactly 1 site ([`_HTML_TYPES`][middleware-debug-toolbar]).
  - *Site count in target:* 1.
- **Posited change 3 (Modifying panel payload generation or panel exclusions):**
  - Update `_get_payload` in `django_strawberry_framework/middleware/debug_toolbar.py`.
  - *Sites that must move in `django_strawberry_framework/middleware/debug_toolbar.py`:* Exactly 1 site ([`_get_payload`][middleware-debug-toolbar]).
  - *Site count in target:* 1.
- **Posited change 4 (Refactoring soft-dependency import failure handling):**
  - Update `require_optional_module` in `django_strawberry_framework/utils/imports.py`.
  - *Sites that must move in `django_strawberry_framework/middleware/debug_toolbar.py`:* Exactly 0 sites ([`require_debug_toolbar`][middleware-debug-toolbar] inherits the change automatically).
  - *Site count in target:* 0.

### Rejected candidates

1. **Re-exporting `DebugToolbarMiddleware` from `django_strawberry_framework/middleware/__init__.py` or package root:**
   - Disproved per [spec-042][spec-042] Decisions 3 and 5. `django-debug-toolbar` is a soft dependency. Importing `debug_toolbar.py` triggers `require_debug_toolbar()` and `apps.is_installed("debug_toolbar")`. Re-exporting it from package root or `middleware/__init__.py` would break clean imports on environments without `django-debug-toolbar`. Furthermore, Django loads middleware via dotted-string paths in `settings.MIDDLEWARE`, making re-exports unnecessary.
2. **Merging `_get_payload` directly into `DebugToolbarMiddleware._postprocess`:**
   - Disproved. Keeping `_get_payload` as a separate pure function decouples JSON parsing, dictionary synthesis, and panel iteration from the HTTP response mutation, header manipulation, and template writing in `_postprocess`. It also allows isolated unit testing of payload edge cases (missing request ID, unparseable JSON, callable panel titles).
3. **Unifying `DebugToolbarMiddleware` with `DjangoDebugExtension` (`extensions/debug.py`):**
   - Disproved. `DjangoDebugExtension` is an in-band GraphQL schema extension injecting query stats into `extensions["debug"]` for API clients. `DebugToolbarMiddleware` is an out-of-band Django HTTP middleware integrating with the `django-debug-toolbar` DOM panels and SQL store. Conflating the two would violate single-responsibility boundaries and create invalid couplings between independent extension mechanisms.
4. **Deferring the soft-dependency guard to runtime `process_view`:**
   - Disproved per [spec-042][spec-042] Decision 5. In Django, middleware classes listed in `settings.MIDDLEWARE` are imported at server startup. Raising an actionable `ImportError` or `ImproperlyConfigured` at leaf module import time fails fast during startup with clear remediation instructions, rather than failing on the first incoming user request.

## Opportunities

None — `django_strawberry_framework/middleware/debug_toolbar.py` is a clean, 290-line module. It implements robust error handling, delegates optional dependency imports to [`require_optional_module`][utils-imports], derives panel metadata dynamically, and coordinates with `debug_toolbar.html` without introducing duplicate policy or unowned state.

## Judgment

Zero-edit review. `django_strawberry_framework/middleware/debug_toolbar.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 0/1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/middleware/debug_toolbar.py --review docs/dry/dry-file-middleware__debug_toolbar.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independent re-trace and boundary challenge completed for `django_strawberry_framework/middleware/debug_toolbar.py`.

### Boundaries and Connected Behavior

1. **Opt-in Leaf Boundary & Dependency Isolation:**
   - Soft-dependency handling strictly satisfies [spec-042][spec-042] Decision 5. [`require_debug_toolbar`][middleware-debug-toolbar] wraps [`require_optional_module`][utils-imports] with the package's single source-of-truth install hint string [`_DEBUG_TOOLBAR_INSTALL_HINT`][middleware-debug-toolbar] naming the verified floor (`django-debug-toolbar>=7.0.0`).
   - Module top-level invocation of [`require_debug_toolbar`][middleware-debug-toolbar] and the `apps.is_installed("debug_toolbar")` check guarantees fast, informative failure during Django's `MIDDLEWARE` load cycle, while keeping parent imports (`import django_strawberry_framework` and `import django_strawberry_framework.middleware`) completely clean without optional dependency leaks.

2. **Middleware Hierarchy and Request Lifecycle:**
   - [`DebugToolbarMiddleware`][middleware-debug-toolbar] subclasses `debug_toolbar.middleware.DebugToolbarMiddleware` and provides exactly two targeted overrides:
     - [`process_view`][middleware-debug-toolbar]: Identifies Strawberry Django views (`isinstance(view, type) and issubclass(view, BaseView)`) and tags the request (`request._is_graphiql`). The `isinstance(view, type)` guard defensively avoids `TypeError` when custom decorators expose non-class `view_class` attributes.
     - [`_postprocess`][middleware-debug-toolbar]: Calls `super()._postprocess()` first to preserve stock toolbar instrumentation and panel rendering, then selectively handles streaming/compressed responses, injects the GraphiQL bridge script [`debug_toolbar.html`][template-debug-toolbar] into 200 HTML responses, and attaches the payload from [`_get_payload`][middleware-debug-toolbar] into `application/json` responses for non-`IntrospectionQuery` requests while recalculating `Content-Length`.

3. **Duplication and Matrix Discharge Verification:**
   - Re-verified all 5 axes of the duplication probing matrix:
     - *Cross-flavor policy:* Separation between HTTP middleware layer ([`DebugToolbarMiddleware`][middleware-debug-toolbar]) and GraphQL schema extension layer ([`DjangoDebugExtension`][extensions-debug]).
     - *Sync/async twins:* Zero duplication; delegates sync/async adaptation to stock toolbar base class.
     - *Derived knowledge:* Dynamic derivation of `_is_graphiql`, panel discovery from `toolbar.enabled_panels`, and runtime DOM querying for shadow/light DOM trees.
     - *Inverse pairs:* Round-trip between server-side payload injection ([`_get_payload`][middleware-debug-toolbar]) and browser-side DOM updates + payload deletion in [`debug_toolbar.html`][template-debug-toolbar].
     - *Medium restatements:* Codified across specifications ([spec-042][spec-042]), tests ([`test_debug_toolbar.py`][test-middleware-debug-toolbar], [`test_debug_toolbar_api.py`][example-test-debug-toolbar-api]), configuration, and documentation.
   - Single-edit-site counts independently confirmed (1 site for install hint change, 1 site for HTML sniff types, 1 site for payload generation changes, 0 sites for core import utility changes).

4. **Automated Verification:**
   - Ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/middleware/debug_toolbar.py --review docs/dry/dry-file-middleware__debug_toolbar.md --include-constants` (All 8 definitions and required topics covered).
   - Ran unit and live test suites (`tests/middleware/test_debug_toolbar.py`, `examples/fakeshop/test_query/test_debug_toolbar_api.py`), confirming 27/27 tests passing with 100% statement coverage on the target file.

Conclusion: Worker 1's findings are confirmed in full. Status is updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-042]: ../SPECS/spec-042-debug_toolbar-0_0_14.md
[spec-044]: ../SPECS/spec-044-debug_extension-0_0_14.md
[spec-046]: ../SPECS/spec-046-transport_security-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[middleware-debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[middleware-init]: ../../django_strawberry_framework/middleware/__init__.py
[middleware-request-body]: ../../django_strawberry_framework/middleware/request_body.py
[template-debug-toolbar]: ../../django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html
[utils-imports]: ../../django_strawberry_framework/utils/imports.py

<!-- tests/ -->
[test-middleware-debug-toolbar]: ../../tests/middleware/test_debug_toolbar.py

<!-- examples/ -->
[example-settings]: ../../examples/fakeshop/config/settings.py
[example-test-debug-toolbar-api]: ../../examples/fakeshop/test_query/test_debug_toolbar_api.py
[example-urls]: ../../examples/fakeshop/config/urls.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
