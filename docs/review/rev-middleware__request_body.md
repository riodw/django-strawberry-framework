# Review: `django_strawberry_framework/middleware/request_body.py`

Status: verified

Cycle baseline: `HEAD` `9ebb4bb0594ccb88c3cf6fbac55bf5883bac7d88`; the target and its connected boundary files were clean at dispatch. `git diff HEAD -- django_strawberry_framework/middleware/request_body.py django_strawberry_framework/_boundary_ordering.py django_strawberry_framework/views.py` is empty.

## Understanding

`GraphQLRequestBodyBoundaryMiddleware` owns lifecycle placement, not body policy. It recognizes the package view callback through `_boundary_ordering.py::_BOUNDARY_MARKER`, rebuilds the mounted class from Django's `view_class`/`view_initkwargs`, runs `setup`, invokes the protocol's `_BOUNDARY_METHOD`, and hands the prepared instance to the callback through `_BOUNDARY_MOUNT`/`_BOUNDARY_PREPARED_VIEW`. A completed request receives `_BOUNDARY_ENFORCED`; duplicate entries therefore become idempotent and do not repeat setup or stream measurement.

The sync and async `__call__` paths publish `_boundary_middleware_request` around the entire downstream lifecycle and reset it in `finally`, including after exceptions. `_CsrfOrderingExemption` uses that request-scoped state to withdraw the callback exemption only when this middleware has actually completed the boundary. The configured CSRF class then runs after the boundary; when this middleware is absent or declines a callback, the package view's own `csrf_protect` continuation remains the protected fallback.

`_require_boundary_before_csrf` resolves configured middleware classes and rejects a boundary after the first CSRF middleware, while accepting a chain with no CSRF entry. Non-package traffic is passed through. The boundary itself remains in `views.py::_RequestBodyBoundaryMixin`: exact cap validation and precedence, declared-length refusal, seekable/bounded stream measurement, multipart streaming carve-out, strict UTF-8/charset checks, malformed multipart control-field rejection, and sync/async parsing.

## Verification

- Read the complete middleware, `_boundary_ordering.py`, connected view mixin and raw-body helper, Django CSRF/request internals, transport specification, fakeshop middleware/URL wiring, package tests, and live HTTP tests.
- `uv run pytest tests/test_views.py --no-cov -q -n0 -k 'body or multipart or charset or csrf or ordering or boundary or setup or probe or stream or request_encoding or utf8 or malformed'` — 151 passed.
- `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov -q -n0` — 77 passed.
- `uv run pytest tests/base/test_init.py tests/base/test_conf.py tests/middleware/test_debug_toolbar.py tests/test_views.py --no-cov -q -n0 -k 'middleware or toolbar or body or csrf or boundary or ordering or setup or import or public or version or setting'` — 125 passed.
- Existing adversarial tests prove duplicate-entry idempotence, malformed callback recognition, setup-derived cap handoff, first-CSRF ordering detection, sync/async ContextVar reset, CSRF failure/cookie behavior, encoded and malformed bodies, bounded reads, stream-position restoration, multipart upload-handler preservation, body limits, charset aliases, BOM handling, and ordinary non-package traffic.
- Django source inspection and live fakeshop requests confirmed that CSRF's multipart `request.POST` read occurs behind the boundary only when the middleware is correctly ordered, while Django remains the owner of multipart parsing and upload limits.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The middleware recognizes only callbacks it can safely prepare, preserves the mounted view instance and setup state, makes duplicate entries idempotent, and scopes the CSRF exemption to the exact request lifecycle. Policy remains in the view/raw-body owners, Django retains multipart/upload ownership, and all tested sync/async, malformed, ordering, and ordinary-traffic paths are coherent. No new root-cause edit is required.

## Implementation (Worker 1)

None — zero-edit cycle.

No production or permanent-test files changed for this item. The current target and required connected boundary files match `HEAD`; no cross-file ownership expansion was necessary. No changelog entry is warranted. No formatter/linter run was required for a source-zero-edit cycle; `CHANGELOG.md` was untouched.

## Independent verification (Worker 2)

Re-read the complete middleware, `_boundary_ordering.py`, connected view/raw-body owners, Django CSRF internals, fakeshop settings/URLconf, package tests, live transport tests, and the transport/body specifications. `git --no-pager status --short` and `git --no-pager diff --name-only` show no Worker 1 source or permanent-test changes; only the three review artifacts are untracked.

Focused validation passed:

- `uv run pytest tests/test_views.py --no-cov -q -n0 -k 'body or multipart or charset or csrf or ordering or boundary or setup or probe or stream or request_encoding or utf8 or malformed'` — 151 passed, 71 deselected.
- `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov -q -n0` — 77 passed.
- An independent `DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop uv run python` probe passed duplicate boundary-entry idempotence (one boundary run and one prepared instance), boundary/CSRF subclass ordering rejection and acceptance, prepared-view identity handoff, and async `ContextVar` publication/reset across a raising downstream call.

The combined evidence covers optional middleware absence/presence, duplicate entries, subclass detection, malformed callback bookkeeping and setup, cap precedence/validation, declared and counted length behavior, streaming/multipart parser ordering, charset aliases and overrides, strict UTF-8/BOM handling, CSRF continuation, sync/async parity, and ordinary non-package traffic. No root-cause defect was reproduced.

**Verdict:** verified. The middleware remains a lifecycle/order adapter; cap, charset, multipart, CSRF, and stream policy stay with their existing owners, and no production or permanent-test edit is required.

