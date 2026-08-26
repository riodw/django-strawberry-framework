# Review: `django_strawberry_framework/middleware/request_body.py`

Status: verified

## Understanding

`django_strawberry_framework/middleware/request_body.py` provides `GraphQLRequestBodyBoundaryMiddleware`, the package's raw-request-body boundary expressed as a Django `MIDDLEWARE` entry.

It owns:
1. **Lifecycle ordering in Django middleware chain:**
   - Moves request-body boundary enforcement ahead of `CsrfViewMiddleware` so multipart parses (`MultiPartParser` invoked during `request.POST.get("csrfmiddlewaretoken", "")`) do not parse an unbounded body before the cap is evaluated.
   - Enforces startup-time configuration validation (`_require_boundary_before_csrf`) verifying that `GraphQLRequestBodyBoundaryMiddleware` (or a subclass) precedes `CsrfViewMiddleware` (or a subclass) in `settings.MIDDLEWARE`.
2. **Per-request boundary execution & dynamic CSRF exemption handoff:**
   - In `__call__` and `__acall__`, manages request context publication via `_boundary_middleware_request` (`ContextVar`), safely resetting after downstream returns or raises.
   - In `process_view`, recognizes package views via `_package_view_instance`, sets up the view instance, invokes `_BOUNDARY_METHOD`, converts `HTTPException` to `HttpResponse(exc.reason, status=exc.status_code, content_type="text/plain")`, stores `(mount, view)` on `request` under `_BOUNDARY_PREPARED_VIEW` for the view callback's reuse, and marks `request` with `_BOUNDARY_ENFORCED = True`.
   - On unrecognized or declined callbacks, leaves the request unstamped so `_CsrfOrderingExemption` falls back to view-local CSRF re-entry.
3. **Safe view recognition & error isolation:**
   - `_package_view_instance` defensively checks callback attributes (`_BOUNDARY_MARKER`, `view_class`, `view_initkwargs`, and callable `_BOUNDARY_METHOD`), catching any attribute access exceptions from hostile or non-standard objects and catching `TypeError` on construction.

## Verification

1. Examined all callers and connections across `django_strawberry_framework/views.py`, `django_strawberry_framework/_boundary_ordering.py`, `tests/test_views.py`, and `examples/fakeshop/test_query/test_transport_api.py`.
2. Reviewed existing test bodies in `tests/test_views.py` and `examples/fakeshop/test_query/test_transport_api.py`.
3. Created scratch test `docs/review/temp-tests/middleware__request_body/test_scratch_request_body.py` to test middleware ordering combinations.
4. Identified a defect in `_require_boundary_before_csrf`: when multiple boundary middleware entries are present in `MIDDLEWARE` (e.g. `[Boundary1, Csrf, Boundary2]`), `boundary_index` was updated to the last occurrence rather than recording the first occurrence, causing a false-positive `ConfigurationError`.
5. Fixed `_require_boundary_before_csrf` to record the index of the first boundary entry (`and boundary_index is None`), matching the existing logic for `csrf_index`.
6. Added permanent test `tests/test_views.py::test_the_first_boundary_entry_is_the_one_the_ordering_is_measured_against`.
7. Ran focused test suites:
   - `tests/test_views.py -k "ordering or boundary or csrf"` (25 passed).
   - `examples/fakeshop/test_query/test_transport_api.py` (77 passed).

## Improvements

### High

None.

### Medium

- **Observation:** `_require_boundary_before_csrf` overwrote `boundary_index` on every matching entry rather than recording the first occurrence (`and boundary_index is None`).
- **Evidence:** In a chain such as `[BoundaryMiddleware, CsrfViewMiddleware, BoundarySubclass]`, the first boundary middleware runs at index 0 before CSRF at index 1. However, `boundary_index` was updated to index 2, causing `csrf_index > boundary_index` (1 > 2) to evaluate `False` and incorrectly raise `ConfigurationError(_MISORDERED_MIDDLEWARE_MESSAGE)`.
- **Impact:** Legitimate configurations with multiple boundary entries (e.g., base configuration plus a subclass for logging/metrics later in the chain) were falsely rejected at startup.
- **Recommendation:** Record the index of the first boundary middleware entry (`and boundary_index is None`), mirroring the first-occurrence rule already used for `csrf_index`.
- **Proof:** Scratch test `test_require_boundary_before_csrf_first_boundary_precedes_first_csrf` and permanent test `tests/test_views.py::test_the_first_boundary_entry_is_the_one_the_ordering_is_measured_against`.

### Low

None.

## Summary

`django_strawberry_framework/middleware/request_body.py` correctly implements middleware-level boundary ordering and safe view recognition. The first-entry index tracking bug in `_require_boundary_before_csrf` was identified, corrected, and pinned with a permanent test.

## Implementation (Worker 1)

- **Changed files:**
  - `django_strawberry_framework/middleware/request_body.py`: In `_require_boundary_before_csrf`, record `boundary_index` only on the first matching entry (`and boundary_index is None`) and update docstring.
  - `tests/test_views.py`: Added `test_the_first_boundary_entry_is_the_one_the_ordering_is_measured_against` asserting that chains with multiple boundary entries are judged by the earliest boundary entry.
- **Permanent tests and pinned behavior:**
  - `tests/test_views.py::test_the_first_boundary_entry_is_the_one_the_ordering_is_measured_against`: pins that chains containing multiple boundary middleware entries (e.g. base and derived subclass) succeed at startup as long as the earliest boundary entry precedes CSRF middleware.
- **Scratch verification:**
  - `docs/review/temp-tests/middleware__request_body/test_scratch_request_body.py` (3 passed).
- **Formatter and linter results:**
  - `uv run ruff format --check .` (clean, 429 files already formatted).
  - `uv run ruff check .` (clean, all checks passed).
  - `scripts/check_trailing_commas.py` (clean).
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — internal startup validation refinement for multiple boundary middleware entries.

## Independent verification (Worker 2)

- **Verification paths & behaviors checked:**
  1. *Middleware ordering validation (`_require_boundary_before_csrf`):* Checked order comparison across varied `settings.MIDDLEWARE` permutations (empty, only boundary, only CSRF, boundary before CSRF, CSRF before boundary, multiple boundary occurrences before/after CSRF, multiple CSRF occurrences, derived middleware subclasses, and function middleware interspersing).
  2. *Request lifecycle & ContextVar safety (`__call__`, `__acall__`):* Verified that `_boundary_middleware_request` is accurately published during sync and async execution and deterministically reset via `finally` blocks on normal response return as well as on raised exceptions.
  3. *Safe view instance recognition (`_package_view_instance`):* Challenged attribute access error isolation with hostile objects raising on attribute access, non-class `view_class`, non-dict `view_initkwargs`, non-callable `_BOUNDARY_METHOD`, and classes whose `__init__` raises `TypeError`.
  4. *Hook execution & CSRF handoff (`process_view`):* Verified that already-enforced requests short-circuit; view `setup()` lifecycle is executed and missing `super().setup()` raises `AttributeError`; view body boundary execution converts `HTTPException` into plain text responses matching view error shapes; and mount token handoff properly stores `(mount, view)` on `request` under `_BOUNDARY_PREPARED_VIEW` while stamping `_BOUNDARY_ENFORCED = True`.
- **Finding confirmation:**
  - Independently confirmed the Medium finding in `_require_boundary_before_csrf`: when multiple boundary entries exist in `MIDDLEWARE`, the earliest boundary entry is the one that executes first and measures the body ahead of CSRF, so `boundary_index` must record the first occurrence (`and boundary_index is None`).
- **Tests run & evidence:**
  - Scratch tests: `docs/review/temp-tests/middleware__request_body/test_scratch_request_body.py` (3 passed) and `docs/review/temp-tests/middleware__request_body/test_independent_scratch_request_body.py` (9 passed, 12 passed total).
  - Focused suite: `tests/test_views.py -k "ordering or boundary or csrf"` (27 passed).
- **Quality & hygiene:**
  - `uv run ruff check .` passed with no issues.
  - `uv run ruff format --check .` passed (429 files formatted).
  - Zero unintended modifications; unrelated dirty files untouched.

