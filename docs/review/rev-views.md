# Review: `django_strawberry_framework/views.py`

Status: verified

## Understanding

`django_strawberry_framework/views.py` provides the package's Django HTTP integration views (`DjangoGraphQLView` and `AsyncDjangoGraphQLView`), subclassing Strawberry's `GraphQLView` and `AsyncGraphQLView`.

It owns:
1. **Request body size enforcement:**
   - Enforces a cumulative byte limit on request bodies (`max_request_body_bytes`) before CSRF verification, multipart parsing, or JSON decoding.
   - Evaluates the limit ladder: mount keyword argument > `settings.DJANGO_STRAWBERRY_FRAMEWORK["MAX_REQUEST_BODY_BYTES"]` > 1 MiB (`1024 * 1024`) fallback. Validates strictly via `_resolved_max_request_body_bytes` (exact `int`, reject `bool`, reject `<= 0`).
   - Rejects over-limit requests with `HTTPException(413, _BODY_LIMIT_REASON)`.
   - Checks declared `Content-Length` header first (`_declared_content_length`), avoiding stream reads on obvious violations.
   - Delegates non-multipart stream probing and bounded reads to `django_strawberry_framework/_request_body.py::body_exceeds_limit` without prematurely materializing payloads.
   - Preserves multipart file upload streaming by checking declared `Content-Length` only and deferring field/file size handling to Django's upload handlers.
2. **CSRF ordering and middleware cooperation:**
   - Coordinates with `django_strawberry_framework/_boundary_ordering.py` and `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware`.
   - Stamped by `_RequestBodyBoundaryMixin.as_view` with `csrf_exempt = _CSRF_ORDERING_EXEMPTION`, `_BOUNDARY_MARKER = True`, and `_BOUNDARY_MOUNT = mount`.
   - Supports prepared view instance reuse via `_BOUNDARY_PREPARED_VIEW` tuple inspection, avoiding redundant instance instantiation.
   - Skips redundant view-level boundary execution via `_enforce_request_boundary_once` when `_BOUNDARY_ENFORCED` was already stamped by upstream middleware.
   - Re-enters CSRF protection safely via `_csrf_protected_run` (`csrf_protect(_run_after_csrf_check)`) for sync and `_csrf_protected_async_run` (`csrf_protect(_async_run_after_csrf_check)`) for async, ensuring views are CSRF-protected even when `CsrfViewMiddleware` is absent from `MIDDLEWARE`.
3. **Strict UTF-8 wire contract & charset validation:**
   - Overrides `request_adapter_class = _RawBodyRequestAdapter` on `DjangoGraphQLView` to return raw `bytes` from `adapter.body`, bypassing upstream's eager `decode()` and eliminating uncaught 500s on non-UTF-8 payloads.
   - Overrides `parse_json` to strictly decode JSON payload bytes with `utf-8`, refusing UTF-16, UTF-32, UTF-8 with BOM, and invalid byte sequences with `HTTPException(400, _JSON_PARSE_REASON)` matching upstream error shape.
   - Validates declared charset on non-multipart POST bodies via `_enforce_body_charset_declaration` and `_declared_charset_is_unhonourable`.
   - Validates multipart form encoding via `_enforce_multipart_form_encoding` and `_form_encoding_is_utf8`, verifying that `request.encoding or settings.DEFAULT_CHARSET` canonicalizes to UTF-8.
   - Rejects lossily-decoded control documents (`operations`, `map`) containing replacement characters `\ufffd` via `_reject_lossy_multipart_control_fields` in `parse_multipart` on both sync and async views.
4. **Channels isolation:**
   - Pure WSGI/ASGI HTTP view module with zero dependency on `channels`, allowing WSGI projects to import and use the views without channels installed.

## Verification

1. Traced connections across callers, settings, middleware, and adapters:
   - `django_strawberry_framework/conf.py` (`max_request_body_bytes_setting`)
   - `django_strawberry_framework/_boundary_ordering.py` (`_CSRF_ORDERING_EXEMPTION`, `_BOUNDARY_MARKER`, `_BOUNDARY_MOUNT`, `_BOUNDARY_PREPARED_VIEW`, `_BOUNDARY_ENFORCED`)
   - `django_strawberry_framework/_request_body.py` (`body_exceeds_limit`)
   - `django_strawberry_framework/middleware/request_body.py` (`GraphQLRequestBodyBoundaryMiddleware`)
   - `django_strawberry_framework/routers.py`
2. Evaluated existing permanent tests in `tests/test_views.py` and `examples/fakeshop/test_query/test_transport_api.py`:
   - Precedence ladder and fail-loud type validation for `max_request_body_bytes`.
   - `as_view` kwarg binding, view callback attribute stamping, coroutine marking preservation, and prepared view instance reuse.
   - Strict UTF-8 decoding matrix for sync and async views (valid UTF-8, invalid UTF-8, UTF-8 with BOM, UTF-16 LE/BE, UTF-32 LE/BE).
   - Non-multipart charset declaration refusal (e.g. `charset=iso-8859-1`, `charset=utf-16`).
   - Multipart form encoding and lossy control document rejection (`\ufffd` in `operations` or `map`).
   - CSRF exemption withdrawal under middleware, CSRF re-entry when middleware absent, and multipart size refusal before CSRF reads `request.POST`.
   - Seekable stream probing vs unseekable bounded reading without memory exhaustion.
   - WSGI import safety without Channels.
3. Executed focused test runs:
   - `uv run pytest tests/test_views.py --no-cov` (222 passed)
   - `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov` (77 passed)
   - `uv run pytest tests/test_cross_web_patches.py --no-cov` (14 passed)
4. Executed scratch verification tests `docs/review/temp-tests/views/test_scratch_views.py`:
   - Verified cap resolution validation on boundary types (`bool`, `0`, negatives, floats, strings).
   - Verified `_declared_content_length`, `_canonicalizes_to_utf8`, `_declared_charset_is_unhonourable`, `_form_encoding_is_utf8`, and `_is_multipart_form_post` helper functions.
   - Verified `_RawBodyRequestAdapter.body` returning raw bytes.
   - Verified `_RequestBodyBoundaryMixin.as_view` prepared view dispatch.
   - Verified `_reject_lossy_multipart_control_fields` on both operations and map control documents.
   - Verified `_enforce_request_boundary_once` skipping when `_BOUNDARY_ENFORCED = True`.
   - Verified declared `Content-Length` over limit raising 413.
   - Verified non-UTF-8 charset declaration raising 400.
   - Verified `AsyncDjangoGraphQLView.parse_multipart` rejecting lossy control fields.
   - Result: 13 passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/views.py` is an exceptionally well-engineered, thoroughly defensive module. It solves complex integration challenges between Django's request lifecycle, CSRF protection, streaming uploads, memory bounds, and Strawberry's execution pipeline with precision and clean separation of concerns. All invariants, type annotations, wire parity error shapes, docstrings, and framework hooks are verified correct. No defects or design issues found.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py`, and `tests/test_cross_web_patches.py`) comprehensively pins all view behaviors, cap resolution, probe hierarchies, UTF-8 wire contracts, multipart control validation, CSRF ordering, and middleware handoffs.
- Scratch verification:
  - `docs/review/temp-tests/views/test_scratch_views.py` passed (13/13 tests) verifying limit validation, helper functions, raw body adapters, prepared instance dispatch, lossy control field rejection, boundary idempotency, and async multipart parsing.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/views.py docs/review/temp-tests/views/test_scratch_views.py` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/views.py docs/review/temp-tests/views/test_scratch_views.py` passed (2 files already formatted).
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/views.py` passed.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Scoped diff verification:
  - Scoped diff against baseline HEAD (`12779c99`) for `django_strawberry_framework/views.py` is confirmed empty (`git diff 12779c99 -- django_strawberry_framework/views.py`).
- Trace and contract analysis:
  - Re-traced `django_strawberry_framework/views.py` across connected boundaries: `django_strawberry_framework/conf.py`, `django_strawberry_framework/_boundary_ordering.py`, `django_strawberry_framework/_request_body.py`, `django_strawberry_framework/middleware/request_body.py`, `cross_web`, and `strawberry.django.views`.
  - Confirmed request body size enforcement precedence ladder, exact-type checking rejecting non-positive ints and `bool` subclasses, seekable stream probing without materialization, and multipart upload handler streaming preservation.
  - Confirmed CSRF ordering semantics: outer `_CSRF_ORDERING_EXEMPTION`, prepared view instance recycling via `_BOUNDARY_PREPARED_VIEW`, and inner continuation re-entry via `csrf_protect`.
  - Confirmed strict UTF-8 decoding in `_RawBodyRequestAdapter` and `_RequestBodyBoundaryMixin.parse_json`, along with multipart replacement character detection (`\ufffd`) in control documents and content-type charset validation.
  - Confirmed WSGI isolation without Channels dependency.
- Test execution:
  - Ran focused test suites:
    - `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov` (299 passed).
  - Authored and ran independent scratch verification suite `docs/review/temp-tests/views/test_independent_worker2_views.py` (10 tests) alongside Worker 1's scratch tests (13 tests) -> 23 passed in `docs/review/temp-tests/views/`:
    - Verified exact int type gating rejecting subclasses, bools, 0, negatives, floats, strings, and iterables.
    - Verified settings ladder (`MAX_REQUEST_BODY_BYTES` kwarg > setting > default 1MB, `None` in setting disabling cap).
    - Verified `_declared_content_length` edge cases (negative, float string, invalid non-digits, absent).
    - Verified `_canonicalizes_to_utf8` on complete set of aliases and non-UTF-8 codecs (including `utf-8-sig`).
    - Verified `_declared_charset_is_unhonourable` matrix.
    - Verified `_form_encoding_is_utf8` matrix across `request.encoding` and `settings.DEFAULT_CHARSET`.
    - Verified `_is_multipart_form_post` method and content-type discrimination.
    - Verified prepared view instance handoff, token matching, cleanup, and fallback.
    - Verified `parse_json` strict UTF-8 decoding and error translation (`HTTPException(400)` with `UnicodeDecodeError` cause).
- Finding disposition:
  - All findings disposed; zero open issues or defects found.
- Verification result:
  - Verified. Status set to `verified`.

