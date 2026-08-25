# DRY review: `django_strawberry_framework/middleware/`

Status: verified

## System trace

`django_strawberry_framework/middleware/` is the Django HTTP middleware integration subpackage for the framework ([spec-042][spec-042], [spec-046][spec-046]). It provides first-party Django HTTP middleware components that instrument GraphQL views for developer diagnostics and enforce security perimeters within Django's HTTP request pipeline ahead of CSRF validation.

The subpackage comprises three modules whose responsibilities, soft-dependency boundaries, and request lifecycle seams are strictly partitioned:

1. [`middleware/__init__.py`][middleware-init]: The subpackage package marker and top-level namespace initializer:
   - **Import-clean package marker and soft-dependency isolation:** Contains an architectural module docstring and zero runtime imports. `import django_strawberry_framework.middleware` succeeds unconditionally on environments without optional dependencies such as `django-debug-toolbar`, allowing whole-package AST walkers ([`scripts/build_tree_md.py`][scripts-build-tree]), test discovery, and coverage analysis to traverse the tree safely.
   - **Django middleware settings string protocol:** Middleware classes are referenced exclusively via dotted module path strings in `settings.MIDDLEWARE` (e.g. `"django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware"`, `"django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware"`), resolved at runtime via `django.utils.module_loading.import_string`.
   - **Zero re-export encapsulation:** Per [spec-042][spec-042] (Decisions 3, 4, 5) and [spec-046][spec-046] (Decision 18), neither middleware class is re-exported from `middleware/__init__.py` or the package root [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] (verified in [`tests/base/test_init.py`][test-base-init]). Importing the leaf module path is the explicit opt-in boundary.

2. [`middleware/debug_toolbar.py`][middleware-debug-toolbar]: The `django-debug-toolbar` integration for Strawberry Django GraphQL views ([spec-042][spec-042]):
   - **Soft-dependency isolation and startup verification:** `django-debug-toolbar` is a soft dependency with a single verified floor pin [`_DEBUG_TOOLBAR_INSTALL_HINT`][middleware-debug-toolbar] (`"django-debug-toolbar>=7.0.0"`). [`require_debug_toolbar`][middleware-debug-toolbar] invokes [`require_optional_module`][utils-imports] at module top-level so that importing this leaf module serves as the explicit opt-in boundary. If `django-debug-toolbar` is installed but omitted from `INSTALLED_APPS`, the module pre-checks `apps.is_installed("debug_toolbar")` and raises `ImproperlyConfigured` carrying [`_DEBUG_TOOLBAR_APP_HINT`][middleware-debug-toolbar], preventing Django's cryptic `HistoryEntry` model registration `RuntimeError`.
   - **Strawberry view request tagging:** [`DebugToolbarMiddleware`][middleware-debug-toolbar] subclasses `debug_toolbar.middleware.DebugToolbarMiddleware`. In [`DebugToolbarMiddleware.process_view`][middleware-debug-toolbar], it inspects `getattr(view_func, "view_class", None)` with `isinstance(view, type) and issubclass(view, BaseView)`, safely tagging the request with `request._is_graphiql` without raising `TypeError` on non-class decorator attributes.
   - **Response postprocessing and GraphQL instrumentation:** [`DebugToolbarMiddleware._postprocess`][middleware-debug-toolbar] delegates first to `super()._postprocess(request, response, toolbar)` to preserve stock toolbar queries, panel rendering, and history tracking. It leaves streaming responses (`response.streaming`) and encoded/compressed bodies (`response.get("Content-Encoding", "")`) untouched. For GraphiQL IDE HTML GET responses (`status_code == 200` and `Content-Type` in [`_HTML_TYPES`][middleware-debug-toolbar] = `{"text/html", "application/xhtml+xml"}`), it appends the client-side bridge template [`django_strawberry_framework/debug_toolbar.html`][template-debug-toolbar] and refreshes `Content-Length`. For tagged GraphQL JSON operation POST responses (`Content-Type == "application/json"`), it inspects `request.body` for `operationName` (skipping `"IntrospectionQuery"` per [spec-042][spec-042] Decision 8), calls [`_get_payload`][middleware-debug-toolbar] to build the panel dictionary, injects it into the response via `DjangoJSONEncoder`, and refreshes `Content-Length`.
   - **Toolbar payload construction:** [`_get_payload`][middleware-debug-toolbar] extracts `toolbar.request_id` and iterates `toolbar.enabled_panels` (excluding `TemplatesPanel`), formatting panel `title` (evaluated when callable, `None` when `not panel.has_content`) and `subtitle` (`nav_subtitle`). Safely bails returning `None` if JSON cannot be parsed or is not a dictionary.
   - **Client-side bridge asset:** [`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`][template-debug-toolbar] intercepts GraphQL responses in the browser, extracts `debugToolbar`, updates `#djDebug` (supporting `#djDebugRoot.shadowRoot` with light-DOM fallback), and scrubs `data.debugToolbar` before GraphiQL parses the payload.

3. [`middleware/request_body.py`][middleware-request-body]: The raw-request-body boundary expressed as a Django `MIDDLEWARE` entry ([spec-046][spec-046] Decision 18):
   - **Request lifecycle ordering seam:** Positions request body measurement and wire-encoding refusals *ahead* of Django's `CsrfViewMiddleware` in the request pipeline. This prevents `CsrfViewMiddleware.process_view` from reading `request.POST` on cookie-bearing multipart POST requests (which triggers `MultiPartParser` and upload handlers before the view is reached), and enables deployments with custom `CsrfViewMiddleware` subclasses to retain their configured class rather than having it replaced by Django's base implementation via view-local `csrf_protect`.
   - **Middleware ordering startup validation:** [`GraphQLRequestBodyBoundaryMiddleware`][middleware-request-body] initializes downstream via [`GraphQLRequestBodyBoundaryMiddleware.__init__`][middleware-request-body] and executes [`_require_boundary_before_csrf`][middleware-request-body], which inspects `settings.MIDDLEWARE` at startup. If [`GraphQLRequestBodyBoundaryMiddleware`][middleware-request-body] (or a subclass) appears *after* `CsrfViewMiddleware` (or a subclass), it raises `ConfigurationError` carrying [`_MISORDERED_MIDDLEWARE_MESSAGE`][middleware-request-body].
   - **Request state tracking & async twin coordination:** [`GraphQLRequestBodyBoundaryMiddleware.__call__`][middleware-request-body] and [`GraphQLRequestBodyBoundaryMiddleware.__acall__`][middleware-request-body] set the active request on context variable `_boundary_middleware_request` in [`_boundary_ordering.py`][boundary-ordering] and reset it in a `finally` block. Coroutine downstreams are marked via `asgiref.sync.markcoroutinefunction` during `__init__`, routing `__call__` to `__acall__` so that context variable cleanup occurs only after downstream coroutines are fully awaited.
   - **View instance preparation and boundary enforcement:** [`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body] short-circuits if `getattr(request, _BOUNDARY_ENFORCED, False)` is `True`. It invokes [`_package_view_instance`][middleware-request-body] to recognize package view callbacks. If recognized, it runs `setup(request, *view_args, **view_kwargs)` (differentiating absent from non-callable via sentinel [`_NO_SETUP`][middleware-request-body]), validates `hasattr(view, 'request')`, and executes `getattr(view, _BOUNDARY_METHOD)(request)`. If `cross_web.HTTPException` is raised, it converts it to `HttpResponse(content=exc.reason, status=exc.status_code, content_type="text/plain")`. If successful, it stamps the request with `_BOUNDARY_PREPARED_VIEW` tuple `(mount, view)` and sets `_BOUNDARY_ENFORCED = True`.
   - **Safe recognition and fallback:** [`_package_view_instance`][middleware-request-body] validates `_BOUNDARY_MARKER` on `view_func`, `isinstance(view_class, type)`, `isinstance(view_initkwargs, dict)`, and `callable(getattr(view_class, _BOUNDARY_METHOD, None))`. All reads are wrapped in `try...except Exception` to decline callbacks with raising metaclasses or descriptors. Construction catches `TypeError` and returns `None`. Declined callbacks remain unstamped, leaving `_CsrfOrderingExemption` active to fall back safely to view-local boundary-then-CSRF re-entry.

Connected root package and sibling subsystem integrations examined:
- [`django_strawberry_framework/_boundary_ordering.py`][boundary-ordering]: Protocol marks (`_BOUNDARY_MARKER`, `_BOUNDARY_ENFORCED`, `_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW`, `_BOUNDARY_METHOD`), context variable `_boundary_middleware_request`, and lazy CSRF exemption `_CsrfOrderingExemption` (`_CSRF_ORDERING_EXEMPTION`).
- [`django_strawberry_framework/_request_body.py`][request-body-internals]: Django private stream measurement (`body_exceeds_limit`, `_measured_remaining`, `_declares_seekable`, `_position_restored`, `_bounded_read_exceeds_limit`, `_measured_by_bounded_read`, `_Probe`), providing zero-policy, fail-closed stream sizing.
- [`django_strawberry_framework/_cross_web_patches.py`][cross-web-patches]: Upstream `cross_web` sync body adapter patch preventing unhandled `500`s on undecodable bodies on Strawberry's own sync view, while package views supply `_RawBodyRequestAdapter`.
- [`django_strawberry_framework/views.py`][views]: `_RequestBodyBoundaryMixin`, `DjangoGraphQLView`, `AsyncDjangoGraphQLView`, `_enforce_request_boundary`, `_enforce_request_boundary_once`, `_resolved_max_request_body_bytes`, `_enforce_request_body_limit`, `_enforce_multipart_form_encoding`, `_enforce_body_charset_declaration`, and `as_view` mount token wrapping / prepared view consumption.
- [`django_strawberry_framework/conf.py`][conf]: Framework configuration singleton managing `MAX_REQUEST_BODY_BYTES_KEY` (`"MAX_REQUEST_BODY_BYTES"`), `get_max_request_body_bytes()`, and `upstream_patches_enabled()`.
- [`django_strawberry_framework/extensions/debug.py`][extensions-debug]: Development-only in-response GraphQL query log extension `DjangoDebugExtension`, kept distinct from Django HTTP middleware `DebugToolbarMiddleware`.
- [`django_strawberry_framework/utils/imports.py`][utils-imports]: Centralized `require_optional_module` helper backing soft-dependency isolation.
- [`django_strawberry_framework/exceptions.py`][exceptions]: `ConfigurationError` exception definition.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/middleware/ --include-constants`):
- Parsed 3 target files (`__init__.py`, `debug_toolbar.py`, `request_body.py`), 673 total lines.
- Inventoried 17 target definitions and module constants across the entire subpackage:
  - `middleware/__init__.py`: 0 definitions/constants (12 lines);
  - `middleware/debug_toolbar.py`: 8 definitions/constants ([`_DEBUG_TOOLBAR_INSTALL_HINT`][middleware-debug-toolbar], [`_DEBUG_TOOLBAR_APP_HINT`][middleware-debug-toolbar], [`require_debug_toolbar`][middleware-debug-toolbar], [`_HTML_TYPES`][middleware-debug-toolbar], [`_get_payload`][middleware-debug-toolbar], [`DebugToolbarMiddleware`][middleware-debug-toolbar], [`DebugToolbarMiddleware.process_view`][middleware-debug-toolbar], [`DebugToolbarMiddleware._postprocess`][middleware-debug-toolbar]);
  - `middleware/request_body.py`: 9 definitions/constants ([`_MISORDERED_MIDDLEWARE_MESSAGE`][middleware-request-body], [`_NO_SETUP`][middleware-request-body], [`GraphQLRequestBodyBoundaryMiddleware`][middleware-request-body], [`GraphQLRequestBodyBoundaryMiddleware.__init__`][middleware-request-body], [`GraphQLRequestBodyBoundaryMiddleware.__call__`][middleware-request-body], [`GraphQLRequestBodyBoundaryMiddleware.__acall__`][middleware-request-body], [`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body], [`_package_view_instance`][middleware-request-body], [`_require_boundary_before_csrf`][middleware-request-body]).
- Confirmed zero missing definitions and verified all reverse references across production, test suites, and examples.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring (types, filters, orders, mutations, forms, rest_framework):**
   - **Perimeter Middleware vs Schema Extensions vs View Layer:**
     - The `middleware/` subpackage operates strictly at the Django HTTP pipeline perimeter.
     - [`DebugToolbarMiddleware`][middleware-debug-toolbar] feeds out-of-band HTML/DOM debug panels and SQL history via `django-debug-toolbar`. In contrast, [`DjangoDebugExtension`][extensions-debug] operates within Strawberry's execution lifecycle to inject in-band query statistics into GraphQL response `extensions["debug"]` for API clients. Both maintain separate responsibilities and zero duplicated logic.
     - [`GraphQLRequestBodyBoundaryMiddleware`][middleware-request-body] controls *where in the request lifecycle* the request body boundary executes (ahead of `CsrfViewMiddleware`), while [`views.py::_RequestBodyBoundaryMixin`][views] owns *what* security policies apply (`_enforce_request_body_limit`, `_enforce_multipart_form_encoding`, `_enforce_body_charset_declaration`) and [`_request_body.py::body_exceeds_limit`][request-body-internals] owns stream measurement.
   - **Soft-Dependency Guards:**
     - [`require_debug_toolbar`][middleware-debug-toolbar] mirrors the package's soft-dependency pattern (`require_channels` in `auth/sessions.py`, DRF guards in `rest_framework/__init__.py`), delegating directly to [`utils/imports.py::require_optional_module`][utils-imports].
   - **Packaging Convention Symmetry:**
     - Both middleware classes are configured independently via dotted string paths in `settings.MIDDLEWARE`. [`middleware/__init__.py`][middleware-init] is an import-clean marker with zero re-exports, perfectly mirroring Django management subpackage conventions ([`management/__init__.py`][management-init]).
2. **Sync and async twins:**
   - **DebugToolbarMiddleware:** Subclasses `debug_toolbar.middleware.DebugToolbarMiddleware`, which handles Django's sync/async middleware protocol adaptation. [`DebugToolbarMiddleware.process_view`][middleware-debug-toolbar] and [`DebugToolbarMiddleware._postprocess`][middleware-debug-toolbar] operate synchronously on `HttpRequest` and `HttpResponse` objects after resolution/execution, requiring zero parallel async code paths.
   - **GraphQLRequestBodyBoundaryMiddleware:** Declares `sync_capable = True` and `async_capable = True`. [`GraphQLRequestBodyBoundaryMiddleware.__call__`][middleware-request-body] routes coroutines to [`GraphQLRequestBodyBoundaryMiddleware.__acall__`][middleware-request-body] via `iscoroutinefunction(self)`. Both `__call__` and `__acall__` manage the `_boundary_middleware_request` context variable in `try...finally`. A dedicated `__acall__` is structurally mandatory because resetting the `ContextVar` in a synchronous `finally` block before an un-awaited coroutine completes would prematurely clear the request context before downstream CSRF middleware can inspect `_BOUNDARY_ENFORCED`.
   - **Unified `process_view`:** [`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body] is synchronous across both sync and async request pipelines in accordance with Django's standard middleware contract.
3. **Derived rather than repeated knowledge:**
   - **Soft-dependency single floor:** [`_DEBUG_TOOLBAR_INSTALL_HINT`][middleware-debug-toolbar] defines the single verified floor (`django-debug-toolbar>=7.0.0`), passed directly to [`require_optional_module`][utils-imports].
   - **Dynamic view tagging:** [`DebugToolbarMiddleware.process_view`][middleware-debug-toolbar] derives `request._is_graphiql` by dynamically inspecting `view_func.view_class` against `BaseView` rather than maintaining hardcoded URL patterns.
   - **Dynamic panel discovery:** [`_get_payload`][middleware-debug-toolbar] dynamically iterates `toolbar.enabled_panels`, reading `panel_id`, `has_content`, `title`, and `nav_subtitle` from active panel instances.
   - **Protocol single sources of truth:** Protocol marker strings (`_BOUNDARY_ENFORCED`, `_BOUNDARY_MARKER`, `_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW`, `_BOUNDARY_METHOD`) and the request context variable (`_boundary_middleware_request`) are defined in [`_boundary_ordering.py`][boundary-ordering] as single sources of truth.
   - **Dynamic middleware sequence:** [`_require_boundary_before_csrf`][middleware-request-body] derives the middleware chain sequence dynamically from `settings.MIDDLEWARE` using `import_string` and `issubclass`, recognizing subclasses without hardcoding class paths.
   - **View kwargs propagation:** [`_package_view_instance`][middleware-request-body] derives kwargs dynamically from `view_initkwargs` (`max_request_body_bytes`), avoiding duplicate setting lookups.
   - **Refusal response derivation:** Rejection responses derive `status` and `content` directly from the caught `HTTPException` (`exc.status_code`, `exc.reason`).
4. **Inverse and round-trip pairs:**
   - **Server payload injection & browser DOM scrubbing:** [`_get_payload`][middleware-debug-toolbar] and [`DebugToolbarMiddleware._postprocess`][middleware-debug-toolbar] inject the `debugToolbar` object into the JSON response; the client-side bridge template [`debug_toolbar.html`][template-debug-toolbar] intercepts the JSON response in the browser, updates `#djDebug`, and deletes `data.debugToolbar` before GraphiQL parses the GraphQL payload.
   - **Context variable set/reset:** `token = _boundary_middleware_request.set(request)` paired with `_boundary_middleware_request.reset(token)` in `finally` blocks across [`GraphQLRequestBodyBoundaryMiddleware.__call__`][middleware-request-body] and [`GraphQLRequestBodyBoundaryMiddleware.__acall__`][middleware-request-body].
   - **Middleware preparation & view handoff:** [`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body] sets `_BOUNDARY_PREPARED_VIEW = (mount, view)` and `_BOUNDARY_ENFORCED = True` on `request`; `views.py::as_view` consumes and clears `_BOUNDARY_PREPARED_VIEW` via `delattr(request, _BOUNDARY_PREPARED_VIEW)` to dispatch the prepared instance, while `_enforce_request_boundary_once` reads `_BOUNDARY_ENFORCED` and skips duplicate measurement.
   - **CSRF exemption round-trip:** `_CsrfOrderingExemption.__bool__()` returns `False` when `_boundary_middleware_request` is active and `_BOUNDARY_ENFORCED` is `True` (withdrawing the exemption so the chain's CSRF middleware runs), and returns `True` for unhandled or unstamped requests (preserving view-local CSRF re-entry fallback).
5. **Contracts restated in another medium:**
   - The middleware contracts are consistently codified across:
     - Specifications: [`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`][spec-042] (Decisions 1–10), [`docs/SPECS/spec-046-transport_security-0_0_14.md`][spec-046] (Decisions 7, 9, 18), [`docs/SPECS/appx/spec-046-transport_security-0_0_14-rationale.md`][spec-046-rationale];
     - Code implementations: [`django_strawberry_framework/middleware/`][middleware-init], [`django_strawberry_framework/_boundary_ordering.py`][boundary-ordering], [`django_strawberry_framework/_request_body.py`][request-body-internals], [`django_strawberry_framework/views.py`][views], [`django_strawberry_framework/conf.py`][conf], [`django_strawberry_framework/extensions/debug.py`][extensions-debug], [`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`][template-debug-toolbar], [`django_strawberry_framework/utils/imports.py`][utils-imports];
     - Test suites: [`tests/middleware/test_debug_toolbar.py`][test-middleware-debug-toolbar], [`tests/test_views.py`][test-views], [`tests/base/test_init.py`][test-base-init], [`examples/fakeshop/test_query/test_debug_toolbar_api.py`][example-test-debug-toolbar-api], [`examples/fakeshop/test_query/test_transport_api.py`][example-test-transport-api];
     - Example configurations: [`examples/fakeshop/config/settings.py`][example-settings], [`examples/fakeshop/config/urls.py`][example-urls];
     - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree], [`GOAL.md`][goal].

### The single-edit-site test

- **Posited change 1 (Adding a new Django middleware integration, e.g. `DjangoTelemetryMiddleware` in `middleware/telemetry.py`):**
  - Add `django_strawberry_framework/middleware/telemetry.py` and reference it via dotted string in `settings.MIDDLEWARE`.
  - *Sites that must move in `middleware/__init__.py`:* Exactly 0 sites (the package marker remains completely decoupled from individual leaf modules).
  - *Site count in `middleware/__init__.py`:* 0.
- **Posited change 2 (Updating the verified `django-debug-toolbar` floor pin, e.g. `>=8.0.0`):**
  - Update [`_DEBUG_TOOLBAR_INSTALL_HINT`][middleware-debug-toolbar] in `django_strawberry_framework/middleware/debug_toolbar.py`.
  - *Sites that must move in `middleware/`:* Exactly 1 site ([`_DEBUG_TOOLBAR_INSTALL_HINT`][middleware-debug-toolbar]).
  - *Site count in subpackage:* 1.
- **Posited change 3 (Updating the misordered middleware configuration error message):**
  - Update [`_MISORDERED_MIDDLEWARE_MESSAGE`][middleware-request-body] in `django_strawberry_framework/middleware/request_body.py`.
  - *Sites that must move in `middleware/`:* Exactly 1 site ([`_MISORDERED_MIDDLEWARE_MESSAGE`][middleware-request-body]).
  - *Site count in subpackage:* 1.
- **Posited change 4 (Renaming the boundary method name protocol contract across views and middleware):**
  - Update `_BOUNDARY_METHOD` in `django_strawberry_framework/_boundary_ordering.py`.
  - *Sites that must move in `middleware/`:* Exactly 0 sites ([`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body] and [`_package_view_instance`][middleware-request-body] import `_BOUNDARY_METHOD` directly).
  - *Site count in subpackage:* 0.
- **Posited change 5 (Modifying HTML content-type sniffing in debug toolbar middleware):**
  - Update [`_HTML_TYPES`][middleware-debug-toolbar] in `django_strawberry_framework/middleware/debug_toolbar.py`.
  - *Sites that must move in `middleware/`:* Exactly 1 site ([`_HTML_TYPES`][middleware-debug-toolbar]).
  - *Site count in subpackage:* 1.
- **Posited change 6 (Modifying the missing `request` attribute error message in `setup()` validation):**
  - Update [`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body] in `django_strawberry_framework/middleware/request_body.py`.
  - *Sites that must move in `middleware/`:* Exactly 1 site ([`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body]).
  - *Site count in subpackage:* 1.
- **Posited change 7 (Modifying panel payload generation or panel exclusions):**
  - Update [`_get_payload`][middleware-debug-toolbar] in `django_strawberry_framework/middleware/debug_toolbar.py`.
  - *Sites that must move in `middleware/`:* Exactly 1 site ([`_get_payload`][middleware-debug-toolbar]).
  - *Site count in subpackage:* 1.
- **Posited change 8 (Altering context variable management for boundary middleware):**
  - Update `_boundary_middleware_request` in `django_strawberry_framework/_boundary_ordering.py`.
  - *Sites that must move in `middleware/`:* Exactly 0 sites ([`GraphQLRequestBodyBoundaryMiddleware.__call__`][middleware-request-body] and [`GraphQLRequestBodyBoundaryMiddleware.__acall__`][middleware-request-body] import `_boundary_middleware_request` directly).
  - *Site count in subpackage:* 0.

### Rejected candidates

1. **Re-exporting `DebugToolbarMiddleware` or `GraphQLRequestBodyBoundaryMiddleware` from `middleware/__init__.py` or package root:**
   - Disproved per [spec-042][spec-042] Decisions 3, 4, 5 and [spec-046][spec-046] Decision 18, verified by [`tests/base/test_init.py`][test-base-init] and [`tests/middleware/test_debug_toolbar.py`][test-middleware-debug-toolbar]. `django-debug-toolbar` is an optional soft dependency whose leaf import triggers `require_debug_toolbar()`. Re-exporting it in `middleware/__init__.py` would break clean imports on environments without the toolbar installed. Furthermore, Django middleware is loaded via dotted-string paths in `settings.MIDDLEWARE`, making subpackage re-exports unnecessary.
2. **Merging `_get_payload` into `DebugToolbarMiddleware._postprocess`:**
   - Disproved. Keeping `_get_payload` as a distinct pure function separates JSON payload decoding, panel traversal, and callable title evaluation from HTTP response mutation, header manipulation, and template writing in `_postprocess`.
3. **Directly importing `views.py` from `middleware/request_body.py` for class checks instead of using `_boundary_ordering.py` protocol:**
   - Disproved per [spec-046][spec-046] Decision 18. Importing `views.py` from `middleware/request_body.py` would create tight bidirectional coupling. Defining protocol attributes in `_boundary_ordering.py` allows the middleware and views to coordinate without importing each other, and enables custom subclasses or alternate view implementations to participate in the boundary ordering protocol.
4. **Unifying `DebugToolbarMiddleware` with `DjangoDebugExtension` (`extensions/debug.py`):**
   - Disproved. `DjangoDebugExtension` is an in-band GraphQL schema extension injecting query stats into `extensions["debug"]` for API clients. `DebugToolbarMiddleware` is an out-of-band Django HTTP middleware integrating with the `django-debug-toolbar` DOM panels and SQL store. Conflating the two would violate single-responsibility boundaries and create invalid couplings between independent extension mechanisms.
5. **Inlining `_require_boundary_before_csrf` inside `GraphQLRequestBodyBoundaryMiddleware.__init__`:**
   - Disproved. Factoring `_require_boundary_before_csrf` as an independent module-level helper keeps `GraphQLRequestBodyBoundaryMiddleware.__init__` clean and allows isolated unit testing of middleware chain ordering logic.
6. **Unifying `GraphQLRequestBodyBoundaryMiddleware.__call__` and `GraphQLRequestBodyBoundaryMiddleware.__acall__` into a single synchronous wrapper:**
   - Disproved. The context variable `_boundary_middleware_request` must remain set until downstream processing completes. In an async request pipeline, a synchronous `finally` block around `get_response(request)` would execute before the returned coroutine was evaluated, clearing the context variable before downstream CSRF middleware could read `_BOUNDARY_ENFORCED`.

## Opportunities

None — The folder integration of `django_strawberry_framework/middleware/` is architecturally clean, robustly tested, and fully consolidated at root owners. Cross-file boundaries between `__init__.py`, `debug_toolbar.py`, and `request_body.py`, as well as integration boundaries with `_boundary_ordering.py`, `_request_body.py`, `_cross_web_patches.py`, `views.py`, `conf.py`, `extensions/debug.py`, and `utils/imports.py`, are strictly defined and honor all repository and security invariants.

## Judgment

Zero-edit folder integration review. All 3 files in `django_strawberry_framework/middleware/` operate in total structural alignment. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 0/1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. Subpackage folder integration verified clean and complete. Checked with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/middleware/ --review docs/dry/dry-folder-middleware.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

I independently verified Worker 1's DRY folder review of `django_strawberry_framework/middleware/`, re-tracing connected behaviors, testing boundaries, verifying single-edit-site counts, and discharging all 5 duplication probing axes.

### Subpackage architecture and boundary verification

1. **Clean package marker and soft-dependency boundary (`__init__.py`):**
   - Verified [`middleware/__init__.py`][middleware-init] is completely empty of runtime imports and defines no re-exports (`__all__ = ()`).
   - Whole-package traversal tools ([`scripts/build_tree_md.py`][scripts-build-tree]), test runners, and coverage analyzers can safely import `django_strawberry_framework.middleware` in environments lacking optional dependencies such as `django-debug-toolbar`.
   - Django middleware classes are referenced solely via dotted string paths in `settings.MIDDLEWARE` and resolved dynamically via `import_string`, making subpackage re-exports unnecessary and preserving soft-dependency opt-in boundaries ([spec-042][spec-042] Decisions 3, 4, 5; [spec-046][spec-046] Decision 18; verified in [`tests/base/test_init.py`][test-base-init]).

2. **Debug toolbar integration and diagnostics separation (`debug_toolbar.py` vs `extensions/debug.py`):**
   - Re-traced [`DebugToolbarMiddleware`][middleware-debug-toolbar] and challenged whether any overlap exists with [`DjangoDebugExtension`][extensions-debug].
   - Confirmed strict separation of concerns:
     - [`DebugToolbarMiddleware`][middleware-debug-toolbar] is a Django HTTP middleware operating out-of-band across the full HTTP request/response pipeline. It integrates with `django-debug-toolbar` to render browser UI panels and track SQL queries in the toolbar's history store.
     - [`DjangoDebugExtension`][extensions-debug] is an in-band Strawberry schema execution extension executing within GraphQL field resolution to inject query execution metrics into the GraphQL response payload under `extensions["debug"]` for API consumers.
   - Verified soft-dependency startup guards: [`_DEBUG_TOOLBAR_INSTALL_HINT`][middleware-debug-toolbar] and [`_DEBUG_TOOLBAR_APP_HINT`][middleware-debug-toolbar] provide actionable configuration errors at import time before Django's internal `HistoryEntry` model registration crashes cryptically.
   - Verified defensive HTML and JSON payload post-processing: streaming and compressed responses pass through untouched, non-dict or invalid JSON degrades safely to `None` without 500ing, and `IntrospectionQuery` is skipped to avoid history pollution.

3. **Request body boundary ordering and protocol decoupling (`request_body.py` vs `_boundary_ordering.py` vs `views.py`):**
   - Re-traced why request body measurement is split across [`middleware/request_body.py`][middleware-request-body], [`_boundary_ordering.py`][boundary-ordering], and [`views.py`][views]:
     - [`views.py::_RequestBodyBoundaryMixin`][views] owns security policy enforcement (`max_request_body_bytes`, form-encoding, charset validation) and [`_request_body.py`][request-body-internals] owns non-destructive stream measurement.
     - [`middleware/request_body.py`][middleware-request-body] owns pipeline lifecycle placement (executing *ahead* of `CsrfViewMiddleware.process_view` before `request.POST` triggers `MultiPartParser` and upload handlers).
     - [`_boundary_ordering.py`][boundary-ordering] defines protocol marks (`_BOUNDARY_MARKER`, `_BOUNDARY_ENFORCED`, `_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW`, `_BOUNDARY_METHOD`), context variable `_boundary_middleware_request`, and lazy CSRF exemption `_CsrfOrderingExemption`.
   - This architecture allows views and middleware to coordinate without importing each other, ensures custom `CsrfViewMiddleware` subclasses retain their configured class rather than being replaced by view-local decorators, and allows unhandled/declined requests to fall back gracefully to view-local boundary-then-CSRF re-entry.
   - Verified sync/async twin coordination: [`GraphQLRequestBodyBoundaryMiddleware.__call__`][middleware-request-body] and [`GraphQLRequestBodyBoundaryMiddleware.__acall__`][middleware-request-body] safely manage `_boundary_middleware_request` in `try...finally` blocks, using `markcoroutinefunction` during `__init__` so that async context variable reset occurs only after downstream coroutines are fully awaited.

### Verification of the 5-axis duplication matrix

1. **Cross-flavor policy mirroring:** Fully discharged. Perimeter middleware, view-level security mixins, and schema extensions have distinct operational boundaries with zero duplicated logic. Packaging and soft-dependency conventions match repository-wide patterns.
2. **Sync and async twins:** Fully discharged. `DebugToolbarMiddleware` delegates sync/async adaptation to upstream, while `GraphQLRequestBodyBoundaryMiddleware` cleanly implements `__call__` and `__acall__` with `markcoroutinefunction` to prevent premature context variable eviction.
3. **Derived rather than repeated knowledge:** Fully discharged. Dynamic view recognition, dynamic panel iteration, protocol constants single sources of truth, dynamic middleware chain inspection in `_require_boundary_before_csrf`, and dynamic view kwargs propagation verified.
4. **Inverse and round-trip pairs:** Fully discharged. Response payload injection & client DOM scrubbing, context variable set/reset, prepared view handoff & consumption, and CSRF exemption dynamic evaluation verified.
5. **Contracts restated in another medium:** Fully discharged. Verified complete consistency across specs (spec-042, spec-046), code implementations, unit/integration test suites, example applications, and architectural documentation.

### Single-edit-site test

Re-evaluated posited changes 1 through 8. Confirmed that every logical change requires modifying exactly 0 or 1 sites within the `middleware/` subpackage.

### Inventory and test verification

- Ran definition coverage check:
  `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/middleware/ --review docs/dry/dry-folder-middleware.md --include-constants`
  -> `OK: 17 target definition(s) and 0 required topic(s) are covered.`
- Executed full test suite:
  `uv run pytest`
  -> `6450 passed, 40 skipped in 92.26s (0:01:32)` with 100% total line coverage.

Status is verified.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../GOAL.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-042]: ../SPECS/spec-042-debug_toolbar-0_0_14.md
[spec-046]: ../SPECS/spec-046-transport_security-0_0_14.md
[spec-046-rationale]: ../SPECS/appx/spec-046-transport_security-0_0_14-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[boundary-ordering]: ../../django_strawberry_framework/_boundary_ordering.py
[conf]: ../../django_strawberry_framework/conf.py
[cross-web-patches]: ../../django_strawberry_framework/_cross_web_patches.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[extensions-debug]: ../../django_strawberry_framework/extensions/debug.py
[management-init]: ../../django_strawberry_framework/management/__init__.py
[middleware-debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[middleware-init]: ../../django_strawberry_framework/middleware/__init__.py
[middleware-request-body]: ../../django_strawberry_framework/middleware/request_body.py
[request-body-internals]: ../../django_strawberry_framework/_request_body.py
[template-debug-toolbar]: ../../django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-middleware-debug-toolbar]: ../../tests/middleware/test_debug_toolbar.py
[test-views]: ../../tests/test_views.py

<!-- examples/ -->
[example-settings]: ../../examples/fakeshop/config/settings.py
[example-test-debug-toolbar-api]: ../../examples/fakeshop/test_query/test_debug_toolbar_api.py
[example-test-transport-api]: ../../examples/fakeshop/test_query/test_transport_api.py
[example-urls]: ../../examples/fakeshop/config/urls.py

<!-- scripts/ -->
[scripts-build-tree]: ../../scripts/build_tree_md.py

<!-- .venv/ -->

<!-- External -->
