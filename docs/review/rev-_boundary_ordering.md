# Review: `django_strawberry_framework/_boundary_ordering.py`

Status: verified

## Understanding

`django_strawberry_framework/_boundary_ordering.py` is a private utility module that defines the decoupling protocol between view-level request-body enforcement (`django_strawberry_framework/views.py::_RequestBodyBoundaryMixin`) and middleware-level lifecycle ordering (`django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware`).

It owns:
1. Attribute marks:
   - `_BOUNDARY_MARKER`: Stamped on view callbacks by `_RequestBodyBoundaryMixin.as_view` so the middleware can identify package views without importing view classes.
   - `_BOUNDARY_ENFORCED`: Stamped on `HttpRequest` by `GraphQLRequestBodyBoundaryMiddleware.process_view` once the boundary has run, ensuring views skip redundant measurement and `_CsrfOrderingExemption` recognizes that the chain has supplied boundary enforcement.
   - `_BOUNDARY_MOUNT`: Stamped on view callbacks with a mount sentinel object.
   - `_BOUNDARY_PREPARED_VIEW`: Stamped on `HttpRequest` with `(mount, view_instance)` so the view callback reuses the prepared view instance configured during middleware setup.
2. Boundary method name:
   - `_BOUNDARY_METHOD`: The string `"_enforce_request_boundary"`, read by the middleware probe and invocation hook.
3. Request context & CSRF exemption:
   - `_boundary_middleware_request`: `ContextVar[HttpRequest | None]` tracking the active request within middleware `__call__` and `__acall__`.
   - `_CsrfOrderingExemption` and singleton `_CSRF_ORDERING_EXEMPTION`: Dynamic `csrf_exempt` marker evaluated via `__bool__`. Returns `False` (withdrawing CSRF exemption) if and only if the current request is handled by boundary middleware and has `_BOUNDARY_ENFORCED == True`. In all other cases (no middleware, or boundary not yet run), returns `True` so the middleware chain skips CSRF and the view performs boundary and CSRF checks internally.

The module has zero dependencies outside Python standard library (`contextvars`, `typing`, and `HttpRequest` for `TYPE_CHECKING` only).

## Verification

1. Examined all callers and integrations across `django_strawberry_framework/views.py` and `django_strawberry_framework/middleware/request_body.py`.
2. Reviewed existing permanent tests:
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark`
   - `tests/test_views.py::test_the_chain_refuses_an_over_limit_multipart_before_any_csrf_read`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
   - `tests/test_views.py::test_the_probed_boundary_method_is_the_one_the_package_views_define`
   - `tests/test_views.py::test_the_middleware_runs_the_boundary_it_probed_the_class_for`
   - `examples/fakeshop/test_query/test_transport_api.py::test_the_configured_csrf_class_checks_fakeshops_real_mount_behind_the_boundary`
   - `examples/fakeshop/test_query/test_transport_api.py::test_the_shipped_chain_supplies_the_ordering_for_fakeshops_real_mount`
3. Executed focused tests:
   - `uv run pytest --no-cov tests/test_views.py -k "ordering or boundary or csrf"` (24 passed)
   - `uv run pytest --no-cov examples/fakeshop/test_query/test_transport_api.py` (77 passed)
4. Created and executed disposable scratch test `docs/review/temp-tests/_boundary_ordering/test_scratch_boundary_ordering.py` covering:
   - Constant string uniqueness and type contracts.
   - All branches of `_CsrfOrderingExemption.__bool__` (`request is None`, `request` without mark, `_BOUNDARY_ENFORCED=False`, `_BOUNDARY_ENFORCED=True`, and post-reset).
   - `ContextVar` isolation across concurrent async tasks.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/_boundary_ordering.py` is a clean, minimal, single-responsibility module that decouples `views.py` and `middleware/request_body.py`. All invariants, type annotations, docstring symbol references, and ContextVar lifecycles are correct and thoroughly tested. No defects or design issues found.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/test_views.py` and `examples/fakeshop/test_query/test_transport_api.py`) covers all protocol marks, view-middleware handoffs, dynamic CSRF exemption withdrawal, and async ContextVar scoping.
- Scratch verification:
  - `docs/review/temp-tests/_boundary_ordering/test_scratch_boundary_ordering.py` passed (3/3 tests) verifying truthiness branches and async ContextVar task isolation.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/_boundary_ordering.py` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/_boundary_ordering.py` passed (1 file already formatted).
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/_boundary_ordering.py` passed.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Scoped diff against HEAD (`12779c99`): verified empty.
- Paths and behavior independently traced:
  - Protocol decoupling between `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin` and `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware`.
  - Callback stamping and resolution (`_BOUNDARY_MARKER`, `_BOUNDARY_MOUNT`).
  - Instance reuse via request attachment (`_BOUNDARY_PREPARED_VIEW`).
  - View boundary probing and execution on unmarked/marked classes (`_BOUNDARY_METHOD`).
  - Request boundary mark propagation (`_BOUNDARY_ENFORCED`).
  - Asynchronous / multi-threaded request context isolation (`_boundary_middleware_request`).
  - Dynamic boolean evaluation and CSRF exemption semantics (`_CsrfOrderingExemption` / `_CSRF_ORDERING_EXEMPTION`).
- Disposable scratch verification:
  - Executed `docs/review/temp-tests/_boundary_ordering/test_scratch_boundary_ordering.py` (3 passed).
- Focused permanent test verification:
  - `tests/test_views.py -k "ordering or boundary or csrf"` (24 passed).
  - `examples/fakeshop/test_query/test_transport_api.py` (77 passed).
- Linters & formatters:
  - Ruff check, ruff format check, and trailing comma check verified clean.
- All findings disposed of: zero findings in target module. Module is sound and verified.
