# Review: `django_strawberry_framework/extensions/error_policy.py`

Status: verified

## Understanding

`django_strawberry_framework/extensions/error_policy.py` implements the execution-result masking and enforcement layer for `ErrorPolicy` (`spec-048`). It ensures that in production (`settings.DEBUG is not True`), unexpected exceptions are replaced with a uniform client-safe error message and a unique correlation identifier on the wire, while preserving full diagnostic tracebacks in server-side logs.

It owns:
1. **Error Classification (`_is_unexpected`):**
   - Implements the structural classification defined in `spec-048` (Decision 8):
     - Non-`GraphQLError` objects (raw Python exceptions or strings) are classified as unexpected (`True`) and masked.
     - `GraphQLError` with `original_error is None` represents syntax, parse, or GraphQL document validation errors constructed directly by graphql-core from client input; these are preserved untouched (`False`).
     - `GraphQLError` with `original_error` being an instance of `GraphQLError` represents deliberate client-facing rejections (such as `GLOBALID_INVALID`, `RESOURCE_LIMIT_EXCEEDED`, permission denials, and consumer-authored `GraphQLError` instances); these are preserved untouched (`False`).
     - `GraphQLError` with any other `original_error` (e.g. `ValueError`, `RuntimeError`, `DatabaseError`) represents unhandled execution exceptions escaping resolvers or value-completion routines (non-null propagation, list completion, scalar serialization); these are classified as unexpected (`True`) and masked.
2. **Safe Error Replacement (`_masked` & `_degraded`):**
   - `_masked`: Mints a fresh 32-character hexadecimal correlation identifier via `new_correlation_id()`, logs an `ERROR`-level record to `django_strawberry_framework` with `exc_info` carrying the original exception/traceback and the correlation ID, and constructs a replacement `GraphQLError`. Retains client-side document location metadata (`nodes`, `source`, `positions`, `path`) while clearing `original_error = None` and injecting `extensions={policy.correlation_extension_key: correlation_id}`.
   - `_degraded`: The fail-closed floor. Returns a minimal `GraphQLError(message=policy.message)` with no location or extensions if error masking itself encounters an exception (e.g. hostile properties).
3. **Execution Masking Pipeline (`mask_execution_result`):**
   - Applies per-error replacement across `result.errors` without mutating the engine's original result in place.
   - Returns the identical `result` instance if `result.errors` is empty or if all errors are expected/deliberate, avoiding unnecessary allocations.
   - Creates a shallow copy of `result` (`copy.copy(result)`) with `masked.errors = replacements` when masking is applied, keeping the original result object unmodified for preceding LIFO extensions (e.g. `DjangoDebugExtension`).
   - Fails closed: if reading `result.errors` or processing the result fails, logs the failure and returns a degraded `StrawberryExecutionResult(data=None, errors=[_degraded(policy)])`.
4. **Extension Lifecycle (`DjangoErrorPolicyExtension`):**
   - Inherits from Strawberry's `SchemaExtension`.
   - Placed at index 0 of `schema.extensions` during schema construction (`schema.py::_with_error_policy_extension`). Because Strawberry unwinds `on_operation` teardown hooks in LIFO order, index 0 tears down last—guaranteeing that diagnostic extensions like `DjangoDebugExtension` observe original unmasked errors before this extension masks the wire result.
   - In `on_operation`, yields to execution, resolves `policy` via `schema_error_policy`, checks `masking_is_active(policy)`, and applies `_process_result` on `is_maskable_result(result)`.
   - Outer fail-closed guard: catches any unexpected exception during teardown and replaces `execution_context.result` with `StrawberryExecutionResult(data=None, errors=[_degraded(policy)])`.
5. **Shared Gates & Helpers:**
   - `masking_is_active`: Returns `policy.enabled and settings.DEBUG is not True`, ensuring truthy strings (e.g. `"False"`) cannot accidentally disable masking.
   - `is_maskable_result`: Admits only `GraphQLExecutionResult` and `StrawberryExecutionResult`, preventing accidental manipulation of raw SSE frames or other non-result objects.
   - `schema_error_policy`: Safely retrieves `schema.error_policy` or falls back to `DEFAULT_ERROR_POLICY` if missing, invalid, or throwing.

## Verification

1. Traced connections across callers, dependencies, and integration seams:
   - `django_strawberry_framework/extensions/__init__.py` (re-export of `DjangoErrorPolicyExtension`).
   - `django_strawberry_framework/schema.py` (`_with_error_policy_extension` prepending index 0, duplicate suppression for custom entries).
   - `django_strawberry_framework/consumers.py` (subscription streaming seam calling `schema_error_policy`, `masking_is_active`, `is_maskable_result`, and `mask_execution_result` in `_stop_aware_results`).
   - `django_strawberry_framework/extensions/debug.py` (teardown ordering interaction ensuring `DjangoDebugExtension` reads unmasked `original_error` before error policy runs).
2. Examined test suites:
   - `tests/test_error_policy.py` (38 tests): covers `ErrorPolicy` dataclass validation, precedence ladder, correlation ID uniqueness and format, extension install position at index 0, consumer entry suppression, standalone schema fallback, teardown no-ops, fail-closed degradation, and copy contract.
   - `examples/fakeshop/test_query/test_error_policy_api.py` (36 tests): covers live HTTP `/graphql/` acceptance tests across the error classification matrix, value-completion phase masking, field path retention, log emission with correlation IDs, multiple error ID distinctness, deliberate `GraphQLError` preservation, permission denials, and `DEBUG=True` pass-through.
3. Test executions:
   - `uv run pytest tests/test_error_policy.py examples/fakeshop/test_query/test_error_policy_api.py --no-cov` (74 passed).
4. Scratch tests:
   - `docs/review/temp-tests/extensions__error_policy/test_scratch_error_policy.py` (16 passed): tested `_is_unexpected` matrix, `_masked` location retention and logging, raw exception masking, `_degraded` minimal error structure, `masking_is_active` strict boolean gate, `is_maskable_result` type filters, `schema_error_policy` safe fallbacks, `mask_execution_result` identity and mixed error lists, hostile error/result fail-closed degradation, and `DjangoErrorPolicyExtension.on_operation` lifecycle under normal, debug, non-maskable, and outer failure states.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/extensions/error_policy.py` is robust, cleanly structured, and adheres strictly to the security and architectural requirements of `spec-048`. It implements comprehensive fail-closed error classification, safe degradation, LIFO teardown ordering, copy semantics for streamed subscriptions and diagnostic extensions, and strict boolean handling for `DEBUG` bypass. No defects or design flaws were found.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:** None (zero-edit cycle). Scoped diff against cycle baseline (`HEAD` = `12779c99`) for `django_strawberry_framework/extensions/error_policy.py` is empty.
- **Permanent tests and pinned behavior:**
  - `tests/test_error_policy.py` (38 tests) pins index 0 extension placement, LIFO teardown ordering, standalone fallback, copy-semantics preservation for original errors, and fail-closed degradation under unreadable error/result objects.
  - `examples/fakeshop/test_query/test_error_policy_api.py` (36 tests) pins live HTTP acceptance tests for the classification matrix, completion-phase masking, path retention, logger correlation ID emission, and `DEBUG=True` bypass.
- **Scratch verification:**
  - `docs/review/temp-tests/extensions__error_policy/test_scratch_error_policy.py` passed (16/16 tests), verifying `_is_unexpected` classification, `_masked` location preservation and logger output, `_degraded` minimal error structure, `masking_is_active` strict `DEBUG` gating, `is_maskable_result` type enforcement, `schema_error_policy` error handling, `mask_execution_result` shallow copy behavior, and `DjangoErrorPolicyExtension.on_operation` lifecycle.
- **Formatter and linter results:**
  - `uv run ruff check django_strawberry_framework/extensions/error_policy.py docs/review/temp-tests/extensions__error_policy/test_scratch_error_policy.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/extensions/error_policy.py` passed with 0 errors.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- **Scoped diff confirmation:** Verified that `git diff 12779c99 -- django_strawberry_framework/extensions/error_policy.py` is empty (zero-edit cycle).
- **Behavioral re-trace & verification:**
  - `_is_unexpected`: Confirmed structural classification rule. Plain exceptions and non-`GraphQLError` instances return `True` (masked). Document validation and syntax errors (`original_error is None`) return `False` (unmasked). Deliberate rejections (`isinstance(original_error, GraphQLError)`) return `False` (unmasked). Unhandled execution exceptions escaping resolvers or value-completion routines return `True` (masked).
  - `_masked` and `_degraded`: Verified `_masked` logs original exceptions under `new_correlation_id()`, preserves document AST coordinates (`nodes`, `positions`, `path`, `source`), sets `original_error=None`, and embeds the correlation ID into extensions. Verified `_degraded` produces minimal safe `GraphQLError` without location or extension leaks.
  - `mask_execution_result`: Verified instance identity preservation when `errors` is empty or all errors are expected; verified shallow copy creation when masking is needed to preserve the engine's original result for preceding LIFO extensions (`DjangoDebugExtension`); verified fail-closed degradation if errors list or replacement building raises.
  - `DjangoErrorPolicyExtension`: Verified index 0 schema placement ensures LIFO teardown ordering; verified `masking_is_active` strict boolean gate (`policy.enabled and settings.DEBUG is not True`); verified `is_maskable_result` type filter; verified outer fail-closed exception handling during operation teardown.
- **Permanent tests executed:**
  - `tests/test_error_policy.py` and `examples/fakeshop/test_query/test_error_policy_api.py` (74 passed).
- **Scratch challenge tests executed:**
  - `docs/review/temp-tests/extensions__error_policy/` (21 passed across `test_scratch_error_policy.py` and `test_scratch_w2_error_policy.py`), covering error classification edges, custom `GraphQLError` subclasses, minimal error shapes, iterator/generator error lists, `None` execution context, and sealed result assignment failure fallback.
- **Outcome:** Verified. No defects, contract gaps, or regressions found.

