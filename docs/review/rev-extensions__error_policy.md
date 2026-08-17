# Review: `django_strawberry_framework/extensions/error_policy.py`

Status: verified

## Understanding

`DjangoErrorPolicyExtension` applies the schema's immutable `ErrorPolicy` at the
completed-result boundary and shares `mask_execution_result()` with the
transport's per-event masking seam for streamed operations. It classifies
parse/validation errors and deliberate `GraphQLError` instances as client-authored
and leaves them unchanged; plain Python exceptions are replaced with a stable
policy message and one correlation id while the original is logged.

Masking returns a shallow result copy, preserving the engine-owned result and its
`original_error` values for later diagnostic extensions. It fails closed when an
error entry or error list is hostile, and `_process_result()` adopts all safe
`data`, `errors`, and `extensions` fields or replaces the outer result with a
safe stock result. The policy is active only when enabled and `settings.DEBUG is
not True`, so malformed truthy debug settings cannot disable production masking.

## Verification

- Traced policy resolution and extension installation through `error_policy.py`,
  `schema.py`, `consumers.py`, debug ordering, and the live fakeshop views.
- Reviewed the structural classifier, standalone-schema fallback, schema
  extension position, sync/async teardown behavior, per-event copy contract,
  correlation logging, and fail-closed hostile-result paths.
- `uv run pytest tests/test_error_policy.py --no-cov` passed as part of the
  combined 197-test package extension run.
- `uv run pytest examples/fakeshop/test_query/test_error_policy_api.py
  examples/fakeshop/test_query/test_resource_policy_api.py --no-cov -q` passed
  53 live tests combined.
- Compile and Ruff checks passed for the extension modules and related tests.
- The module and test changes already present at dispatch were concurrent
  hardening work; this cycle did not overwrite or reclassify them.

## Improvements

### High

None.

### Medium
- **Callable consumer entries bypassed automatic error-policy suppression.**
  - **Observation:** Strawberry accepts classes, instances, and zero-argument
    factories, but `_with_error_policy_extension()` only recognized classes and
    instances. A callable factory returning `DjangoErrorPolicyExtension` left
    the automatic class installed as a duplicate.
  - **Evidence:** Independent Worker 1 and Worker 2 reproductions with
    `lambda: DjangoErrorPolicyExtension()` produced two runtime policy
    instances. With a callable acknowledged debug entry placed before the
    callable policy, the policy teardown stripped `original_error` before debug
    teardown, yielding no exception diagnostic.
  - **Impact:** The documented consumer-supplied policy suppression contract was
    false for the supported Strawberry factory form, and diagnostic exception
    capture could silently disappear depending on consumer ordering.
  - **Recommendation:** Keep opaque factories uncalled at schema construction;
    after Strawberry resolves per-operation extensions, remove only the first
    automatic policy instance when a factory produced an explicit policy, while
    preserving consumer order and fresh-per-operation construction.
  - **Proof:** `tests/test_error_policy.py::test_a_callable_policy_entry_suppresses_the_auto_policy_at_runtime`
    and `test_callable_policy_and_debug_entries_preserve_debug_exception_capture`.

### Low

None.

## Summary

Result classification, production masking, deliberate-error preservation,
correlation diagnostics, streamed-result reuse, extension ordering, malformed
debug-setting behavior, and fail-closed degradation are coherent. Callable
factory suppression was fixed at the runtime resolution boundary.

## Implementation (Worker 1)

- Changed `schema.py` so callable factory entries are resolved once per
  operation and the automatic error-policy instance is removed only when a
  factory supplied an explicit policy.
- Added package regressions for callable suppression and debug exception capture.
- Preserved the pre-existing strict debug gate and safe-result adoption changes
  already present in the working tree.
- No changelog entry was requested.

## Independent verification (Worker 2)

- Independently checked that masking cannot retain unsafe data/extensions when
  result adoption fails and that a malformed `DEBUG` value does not open the
  development pass-through.
- Independently confirmed Strawberry's factory contract and reproduced duplicate
  runtime policy instances before the fix.
- Re-ran the package extension suite after the fix: 203 tests passed, and the
  post-fix live extension suites passed serially: 65 tests.
- No additional error-policy finding remains.
