# DRY review: `django_strawberry_framework/middleware/request_body.py`

Status: verified

## System trace

`django_strawberry_framework/middleware/request_body.py` implements the framework's raw-request-body boundary expressed as a Django `MIDDLEWARE` entry ([spec-046][spec-046] Decision 18). It exposes [`GraphQLRequestBodyBoundaryMiddleware`][middleware-request-body], which allows deployments to position request body measurement and wire-encoding refusals *ahead* of Django's CSRF middleware in the request lifecycle without substituting or weakening the deployment's configured CSRF middleware class.

It owns the following responsibilities:

1. **Request Lifecycle Ordering Seam:**
   - Django's `CsrfViewMiddleware.process_view` reads `request.POST.get("csrfmiddlewaretoken", "")` on cookie-bearing POST requests, which invokes `MultiPartParser` and upload handlers before the view callback is reached.
   - Enforcing the request body cap from inside the view required exempting the view from CSRF and re-entering CSRF via `csrf_protect`. However, `csrf_protect` is hardcoded to Django's stock `CsrfViewMiddleware`. Deployments using a custom `CsrfViewMiddleware` subclass (e.g., for tenant isolation, token binding, or audit logging) would have their subclass silently replaced by the base class on GraphQL endpoints.
   - [`GraphQLRequestBodyBoundaryMiddleware`][middleware-request-body] moves boundary enforcement into the Django middleware chain, running from [`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body] before `CsrfViewMiddleware.process_view`.

2. **Middleware Ordering Startup Validation:**
   - [`_require_boundary_before_csrf`][middleware-request-body] inspects `settings.MIDDLEWARE` during [`GraphQLRequestBodyBoundaryMiddleware.__init__`][middleware-request-body] and raises `ConfigurationError` carrying [`_MISORDERED_MIDDLEWARE_MESSAGE`][middleware-request-body] if [`GraphQLRequestBodyBoundaryMiddleware`][middleware-request-body] (or a subclass) appears *after* any `CsrfViewMiddleware` (or subclass) in the chain.
   - It resolves middleware entries via `django.utils.module_loading.import_string` and compares classes using `issubclass`, correctly handling custom subclasses and skipping non-class function middleware.

3. **Request State Tracking and Exemption Coordination:**
   - [`GraphQLRequestBodyBoundaryMiddleware.__call__`][middleware-request-body] and [`GraphQLRequestBodyBoundaryMiddleware.__acall__`][middleware-request-body] publish the active request to `_boundary_middleware_request` (a `ContextVar` in [`_boundary_ordering.py`][boundary-ordering]) across downstream processing, resetting the token in a `finally` block to prevent leakage across requests.
   - On coroutine downstream callers, [`GraphQLRequestBodyBoundaryMiddleware.__init__`][middleware-request-body] marks the middleware with `asgiref.sync.markcoroutinefunction`, and [`GraphQLRequestBodyBoundaryMiddleware.__call__`][middleware-request-body] routes to [`GraphQLRequestBodyBoundaryMiddleware.__acall__`][middleware-request-body] so that the context variable reset occurs only after downstream coroutines are fully awaited.

4. **Package View Instance Preparation and Boundary Enforcement:**
   - [`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body] calls [`_package_view_instance`][middleware-request-body] to recognize package view callbacks.
   - If already stamped with `_BOUNDARY_ENFORCED`, `process_view` short-circuits immediately.
   - It invokes `setup(request, *view_args, **view_kwargs)` on the constructed instance using sentinel [`_NO_SETUP`][middleware-request-body] to safely detect when `setup` is absent vs. non-callable, and validates that `self.request` is established (raising `AttributeError` if `super().setup()` was omitted).
   - It executes `getattr(view, _BOUNDARY_METHOD)(request)` where `_BOUNDARY_METHOD` (`_enforce_request_boundary`) is defined in [`_boundary_ordering.py`][boundary-ordering].
   - If an `HTTPException` is raised, it converts it to a plain text `HttpResponse(content=exc.reason, status=exc.status_code, content_type="text/plain")`, guaranteeing wire format parity with upstream view dispatch.
   - If successful, it stamps the request with `_BOUNDARY_PREPARED_VIEW` tuple `(mount, view)` for the matching view callback to consume, and marks `_BOUNDARY_ENFORCED = True` on the request.

5. **Safe Recognition and Fallback:**
   - [`_package_view_instance`][middleware-request-body] validates that `view_func` has `_BOUNDARY_MARKER` (`graphql_request_body_boundary`), `view_class` is a class, `view_initkwargs` is a dictionary, and `_BOUNDARY_METHOD` is a callable on `view_class`.
   - All attribute lookups in `_package_view_instance` are defensively wrapped in `try...except Exception` to safely decline callbacks with raising metaclasses or descriptors.
   - If recognition fails or `TypeError` is raised during `view_class(**initkwargs)`, `_package_view_instance` returns `None`. The request remains unstamped, leaving `_CsrfOrderingExemption` true, which safely triggers the view's internal boundary-then-CSRF continuation.

Connected behavior examined:
- [`django_strawberry_framework/_boundary_ordering.py`][boundary-ordering]: Protocol marks (`_BOUNDARY_MARKER`, `_BOUNDARY_ENFORCED`, `_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW`, `_BOUNDARY_METHOD`), context variable `_boundary_middleware_request`, and lazy exemption `_CsrfOrderingExemption`.
- [`django_strawberry_framework/_request_body.py`][request-body-internals]: Django private request stream measurement (`body_exceeds_limit`, `_measured_remaining`, `_bounded_read_exceeds_limit`, `_Probe`).
- [`django_strawberry_framework/views.py`][views]: `_RequestBodyBoundaryMixin`, `DjangoGraphQLView`, `AsyncDjangoGraphQLView`, `_enforce_request_boundary`, `_enforce_request_boundary_once`, `as_view` mount token wrapping and prepared view handoff consumption.
- [`django_strawberry_framework/middleware/__init__.py`][middleware-init]: Package marker keeping `middleware/` import-clean without eager leaf re-exports.
- [`django_strawberry_framework/middleware/debug_toolbar.py`][middleware-debug-toolbar]: Sibling Django HTTP middleware providing debug-toolbar integration.
- [`django_strawberry_framework/exceptions.py`][exceptions]: `ConfigurationError` exception definition.
- [`tests/test_views.py`][test-views]: Comprehensive unit and integration test suite covering middleware ordering, subclass auditing, startup validation, async context variable lifecycle, non-callable setup failures, and view fallback behavior.
- [`examples/fakeshop/config/settings.py`][example-settings]: Reference configuration installing `GraphQLRequestBodyBoundaryMiddleware` ahead of `CsrfViewMiddleware`.
- [`docs/SPECS/spec-046-transport_security-0_0_14.md`][spec-046]: Specification defining Decision 7 (cumulative body cap), Decision 9 (wire refusals), and Decision 18 (middleware chain ordering).

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/middleware/request_body.py --include-constants`):
- Target file contains 371 lines, 1 class definition ([`GraphQLRequestBodyBoundaryMiddleware`][middleware-request-body]), 4 methods ([`GraphQLRequestBodyBoundaryMiddleware.__init__`][middleware-request-body], [`GraphQLRequestBodyBoundaryMiddleware.__call__`][middleware-request-body], [`GraphQLRequestBodyBoundaryMiddleware.__acall__`][middleware-request-body], [`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body]), 2 functions ([`_package_view_instance`][middleware-request-body], [`_require_boundary_before_csrf`][middleware-request-body]), and 2 private constants ([`_MISORDERED_MIDDLEWARE_MESSAGE`][middleware-request-body], [`_NO_SETUP`][middleware-request-body]).
- Verified protocol separation, zero cross-module import coupling between `views.py` and `middleware/request_body.py`, fail-safe error handling in recognition hooks, and strict startup ordering validation.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring (types, filters, orders, mutations, forms, rest_framework):**
   - **Boundary Policy vs. Execution Ordering:** `GraphQLRequestBodyBoundaryMiddleware` states zero body-limit numbers, wire charset names, or custom exceptions. All boundary security policy is owned exclusively by `views.py::_RequestBodyBoundaryMixin` (`_enforce_request_body_limit`, `_enforce_multipart_form_encoding`, `_enforce_body_charset_declaration`) and `_request_body.py::body_exceeds_limit`. The middleware purely decides *when* that boundary runs.
   - **Sibling Middleware Separation:** `GraphQLRequestBodyBoundaryMiddleware` and [`DebugToolbarMiddleware`][middleware-debug-toolbar] operate independently in `settings.MIDDLEWARE` without shared intermediate base classes or cross-imports.
2. **Sync and async twins:**
   - `GraphQLRequestBodyBoundaryMiddleware` declares `sync_capable = True` and `async_capable = True`.
   - `GraphQLRequestBodyBoundaryMiddleware.__call__` routes coroutine instances to `GraphQLRequestBodyBoundaryMiddleware.__acall__`.
   - Both methods manage the `_boundary_middleware_request` context variable with `set()` and `reset()` in a `try...finally` block. A distinct `__acall__` is structurally mandatory because resetting in a synchronous `finally` block before an un-awaited coroutine finishes would prematurely clear the context variable before downstream CSRF middleware could read it.
   - `process_view` is synchronous across both sync and async request pipelines in accordance with Django's standard middleware contract.
3. **Derived rather than repeated knowledge:**
   - Boundary method name is not repeated as a string literal; it is imported as `_BOUNDARY_METHOD` from `_boundary_ordering.py`.
   - Protocol marker strings (`_BOUNDARY_ENFORCED`, `_BOUNDARY_MARKER`, `_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW`) and the request context variable (`_boundary_middleware_request`) are defined in `_boundary_ordering.py` as single sources of truth.
   - `_require_boundary_before_csrf` derives the middleware chain sequence dynamically from `settings.MIDDLEWARE` using `import_string` and `issubclass`, correctly recognizing derived subclasses without hardcoded dotted path strings.
   - View instance instantiation derives kwargs dynamically from `view_initkwargs` (such as `max_request_body_bytes`), avoiding duplicate setting lookups.
   - Refusal wire responses derive `status` and `content` directly from the caught `HTTPException` (`exc.status_code`, `exc.reason`).
4. **Inverse and round-trip pairs:**
   - **Context Variable Management:** `token = _boundary_middleware_request.set(request)` paired with `_boundary_middleware_request.reset(token)` in `finally` blocks across `__call__` and `__acall__`.
   - **Middleware Preparation & View Handoff:** `process_view` sets `_BOUNDARY_PREPARED_VIEW = (mount, view)` and `_BOUNDARY_ENFORCED = True` on `request`; `views.py::as_view` consumes and clears `_BOUNDARY_PREPARED_VIEW` via `delattr(request, _BOUNDARY_PREPARED_VIEW)` to dispatch the prepared instance, while `_enforce_request_boundary_once` reads `_BOUNDARY_ENFORCED` and skips duplicate measurement.
   - **CSRF Exemption State Round-Trip:** `_CsrfOrderingExemption.__bool__()` returns `False` when `_boundary_middleware_request` is active and `_BOUNDARY_ENFORCED` is `True` (withdrawing the exemption so the chain's CSRF middleware runs), and returns `True` for unhandled or unstamped requests (preserving view-local CSRF re-entry fallback).
5. **Contracts restated in another medium:**
   The boundary middleware protocol and ordering contract are codified across:
   - Code: [`django_strawberry_framework/middleware/request_body.py`][middleware-request-body], [`django_strawberry_framework/_boundary_ordering.py`][boundary-ordering], [`django_strawberry_framework/views.py`][views], [`django_strawberry_framework/_request_body.py`][request-body-internals];
   - Specifications: [`docs/SPECS/spec-046-transport_security-0_0_14.md`][spec-046] (Decisions 7, 9, 18), [`docs/SPECS/appx/spec-046-transport_security-0_0_14-rationale.md`][spec-046-rationale];
   - Test suites: [`tests/test_views.py`][test-views] (lines 2650–3865);
   - Reference application: [`examples/fakeshop/config/settings.py`][example-settings];
   - Standing documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary] (GraphQLRequestBodyBoundaryMiddleware), [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Updating the misordered middleware configuration error message):**
  - Update `_MISORDERED_MIDDLEWARE_MESSAGE` in `django_strawberry_framework/middleware/request_body.py`.
  - *Sites that must move in `django_strawberry_framework/middleware/request_body.py`:* Exactly 1 site ([`_MISORDERED_MIDDLEWARE_MESSAGE`][middleware-request-body]).
  - *Site count in target:* 1.
- **Posited change 2 (Renaming the boundary method name protocol contract across views and middleware):**
  - Update `_BOUNDARY_METHOD` in `django_strawberry_framework/_boundary_ordering.py`.
  - *Sites that must move in `django_strawberry_framework/middleware/request_body.py`:* Exactly 0 sites ([`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body] and [`_package_view_instance`][middleware-request-body] import `_BOUNDARY_METHOD` directly).
  - *Site count in target:* 0.
- **Posited change 3 (Modifying the missing `request` attribute error message in `setup()` validation):**
  - Update `GraphQLRequestBodyBoundaryMiddleware.process_view` in `django_strawberry_framework/middleware/request_body.py`.
  - *Sites that must move in `django_strawberry_framework/middleware/request_body.py`:* Exactly 1 site ([`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body]).
  - *Site count in target:* 1.
- **Posited change 4 (Changing HTTP rejection response encoding or content type for boundary failures):**
  - Update `GraphQLRequestBodyBoundaryMiddleware.process_view` in `django_strawberry_framework/middleware/request_body.py`.
  - *Sites that must move in `django_strawberry_framework/middleware/request_body.py`:* Exactly 1 site ([`GraphQLRequestBodyBoundaryMiddleware.process_view`][middleware-request-body]).
  - *Site count in target:* 1.
- **Posited change 5 (Altering the context variable for active middleware request tracking):**
  - Update `_boundary_middleware_request` in `django_strawberry_framework/_boundary_ordering.py`.
  - *Sites that must move in `django_strawberry_framework/middleware/request_body.py`:* Exactly 0 sites ([`GraphQLRequestBodyBoundaryMiddleware.__call__`][middleware-request-body] and [`GraphQLRequestBodyBoundaryMiddleware.__acall__`][middleware-request-body] import `_boundary_middleware_request` directly).
  - *Site count in target:* 0.

### Rejected candidates

1. **Re-exporting `GraphQLRequestBodyBoundaryMiddleware` from `django_strawberry_framework/middleware/__init__.py` or package root:**
   - Disproved per [spec-046][spec-046] Decision 18. Django discovers and imports middleware via dotted module path strings in `settings.MIDDLEWARE`. Eagerly importing or re-exporting `GraphQLRequestBodyBoundaryMiddleware` from `middleware/__init__.py` or package root would pollute the namespace and defeat lazy module loading.
2. **Directly importing `DjangoGraphQLView` in `middleware/request_body.py` for class checks instead of using `_boundary_ordering.py` protocol:**
   - Disproved per [spec-046][spec-046] Decision 18. Importing `views.py` from `middleware/request_body.py` would create tight bidirectional coupling. Defining protocol attributes in `_boundary_ordering.py` allows the middleware and views to coordinate without importing each other, and enables custom subclasses or alternate view implementations to participate in the boundary ordering protocol.
3. **Inlining `_require_boundary_before_csrf` inside `GraphQLRequestBodyBoundaryMiddleware.__init__`:**
   - Disproved. Factoring `_require_boundary_before_csrf` as an independent module-level helper keeps `GraphQLRequestBodyBoundaryMiddleware.__init__` clean and allows isolated unit testing of middleware chain ordering logic.
4. **Unifying `__call__` and `__acall__` into a single synchronous wrapper:**
   - Disproved. The context variable `_boundary_middleware_request` must remain set until downstream processing completes. In an async request pipeline, a synchronous `finally` block around `get_response(request)` would execute before the returned coroutine was evaluated, clearing the context variable before downstream CSRF middleware could read `_BOUNDARY_ENFORCED`.
5. **Eliminating the view-local boundary fallback in `views.py`:**
   - Disproved. Backward compatibility requires that applications omitting `GraphQLRequestBodyBoundaryMiddleware` from `settings.MIDDLEWARE` continue to enforce request body limits and CSRF protection via internal view re-entry.

## Opportunities

None — `django_strawberry_framework/middleware/request_body.py` is a highly focused, 371-line module with zero duplicate policy. It delegates all protocol constants to [`_boundary_ordering.py`][boundary-ordering], all body measurement to [`_request_body.py`][request-body-internals], and all security boundaries to [`views.py`][views], while providing robust startup validation, async-safe context variable management, and comprehensive error handling.

## Judgment

Zero-edit review. `django_strawberry_framework/middleware/request_body.py` contains zero duplicate policy or redundant code. All 5 axes of the mandatory duplication matrix are verified and discharged. Single-edit-site counts are 0/1 across all posited changes.

## Implementation (Worker 1)

No tracked code changes needed. The target file is verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/middleware/request_body.py --review docs/dry/dry-file-middleware__request_body.md --include-constants`. Setting `Status: fix-implemented`.

## Independent verification (Worker 2)

Independently retraced all architectural boundaries, lifecycle contracts, and security mechanisms in [`django_strawberry_framework/middleware/request_body.py`][middleware-request-body]:

1. **Request Lifecycle & Ordering Integrity:**
   - Verified that `GraphQLRequestBodyBoundaryMiddleware.process_view` executes prior to `CsrfViewMiddleware.process_view`, ensuring multipart request bodies and wire encodings are measured and validated before `request.POST` evaluation triggers `MultiPartParser` and file upload handlers.
   - Challenged boundary coupling: confirmed that `middleware/request_body.py` imports neither `views.py` nor `_request_body.py`. All protocol markers (`_BOUNDARY_MARKER`, `_BOUNDARY_ENFORCED`, `_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW`, `_BOUNDARY_METHOD`), context variable `_boundary_middleware_request`, and lazy exemption `_CsrfOrderingExemption` are isolated in [`_boundary_ordering.py`][boundary-ordering].
2. **Fail-Safe Recognition & Fallback:**
   - Probed `_package_view_instance` recognition defenses: verified that `view_func` is checked for `_BOUNDARY_MARKER`, `view_class` is verified to be an instance of `type`, `view_initkwargs` is verified to be a `dict`, and `_BOUNDARY_METHOD` is verified as callable on `view_class` before any instance construction is attempted.
   - Verified that attribute lookups are enclosed in `try...except Exception` to safely ignore malformed descriptors or raising metaclasses, and that `TypeError` during `view_class(**initkwargs)` cleanly returns `None`. In all fallback cases, the request remains unstamped, leaving `_CsrfOrderingExemption` active and safely falling back to view-local boundary-then-CSRF re-entry.
3. **Instance Setup, Execution & Error Parity:**
   - Probed `process_view` instance preparation: verified that `view.setup(request, *view_args, **view_kwargs)` is invoked when callable (using sentinel `_NO_SETUP` to differentiate absent from non-callable `setup`), and that `hasattr(view, 'request')` is validated to catch omitted `super().setup()`.
   - Verified that `HTTPException` caught during `_BOUNDARY_METHOD` execution is transformed into `HttpResponse(content=exc.reason, status=exc.status_code, content_type="text/plain")`, ensuring exact wire parity with upstream `dispatch` error handling.
   - Verified that `_BOUNDARY_PREPARED_VIEW` tuple `(mount, view)` is placed on `request` and consumed by `views.py::as_view` to preserve request-local setup state without duplicate instance construction.
4. **Startup Ordering Validation:**
   - Verified `_require_boundary_before_csrf`: `settings.MIDDLEWARE` is inspected during `__init__`, resolving entries via `import_string` and comparing them using `issubclass`. This correctly detects misordered custom `CsrfViewMiddleware` and `GraphQLRequestBodyBoundaryMiddleware` subclasses while ignoring function-style middleware.
5. **Async Context Variable Lifetime:**
   - Verified that `__call__` and `__acall__` manage `_boundary_middleware_request` within `try...finally` blocks. Marking `self` as a coroutine function when `get_response` is async guarantees that `__acall__` is dispatched and context variable reset occurs only after downstream coroutines are fully awaited.
6. **Matrix & Single-Edit Verification:**
   - Confirmed all 5 axes of the mandatory duplication matrix are fully discharged with valid justifications.
   - Re-evaluated posited single-edit-site scenarios: confirmed all site counts hold at 0 or 1.
   - Re-ran `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/middleware/request_body.py --review docs/dry/dry-file-middleware__request_body.md --include-constants` with 100% coverage across 9 target definitions.

Status updated to `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-046]: ../SPECS/spec-046-transport_security-0_0_14.md
[spec-046-rationale]: ../SPECS/appx/spec-046-transport_security-0_0_14-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[boundary-ordering]: ../../django_strawberry_framework/_boundary_ordering.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[middleware-debug-toolbar]: ../../django_strawberry_framework/middleware/debug_toolbar.py
[middleware-init]: ../../django_strawberry_framework/middleware/__init__.py
[middleware-request-body]: ../../django_strawberry_framework/middleware/request_body.py
[request-body-internals]: ../../django_strawberry_framework/_request_body.py
[views]: ../../django_strawberry_framework/views.py

<!-- tests/ -->
[test-views]: ../../tests/test_views.py

<!-- examples/ -->
[example-settings]: ../../examples/fakeshop/config/settings.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
