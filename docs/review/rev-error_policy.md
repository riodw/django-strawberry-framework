# Review: `django_strawberry_framework/error_policy.py`

Status: verified

## Understanding

`error_policy.py` owns the frozen schema-level `ErrorPolicy`, package defaults, precedence resolution, option validation, and correlation-id generation. `DjangoSchema` resolves one policy at construction and exposes it to `DjangoErrorPolicyExtension`; `conf.py::error_policy_setting` is the thin settings reader. The extension classifies GraphQL errors structurally, preserves deliberate `GraphQLError` and parse/validation failures, masks unexpected exceptions with a fresh correlation id and server log record, and applies the same helper to HTTP teardown and the Channels streamed-result seam. Views reach the policy through Strawberry's normal sync/async execution, while `consumers.py::_stop_aware_results` handles one result per streamed event.

The scoped baseline `c1d948fc269e4b09823c3c52849631be34025500` has no target diff for `error_policy.py`; review therefore evaluated the complete current policy and its connected extension/schema/consumer callers. Existing package and live tests cover construction, settings precedence, structural classification, logging, debug/opt-out behavior, sync/async HTTP parity, streamed result masking, and extension ordering.

## Verification

- `uv run pytest tests/test_error_policy.py --no-cov` passed 43 tests before the implementation change and 44 after it.
- `uv run pytest examples/fakeshop/test_query/test_error_policy_api.py --no-cov` passed 17 live HTTP tests after the change, covering masked and deliberate errors, parse/validation errors, correlation logging, completion failures, custom policy values, `DEBUG`, opt-out, and sync/async parity.
- `uv run pytest tests/test_routers.py --no-cov -k 'error_policy or streamed_value_the_policy_cannot_mask or stop_aware_schema_passes_every_upstream_schema_read'` passed 2 streamed-result seam tests.
- `docs/review/temp-tests/error_policy/test_runtime.py` reproduced the defect through an admitted Strawberry execution-result subclass whose `errors` property raises: the helper returned the documented safe `data=None` floor, but the extension seam retained the original data before the fix. The same scratch test passed after the fix.
- Source inspection confirmed graphql-core and Strawberry execution-result shapes are mutable stock objects, and Strawberry's extension teardown runs after execution for sync and async operations. The policy's streamed path remains the transport-owned per-result seam.

## Improvements

### High

None.

### Medium

- **Observation:** `mask_execution_result` correctly failed closed to a fresh result with the policy message, `data=None`, and no extensions when an execution result's error list could not be read. `DjangoErrorPolicyExtension::_process_result` then copied only `errors` onto the original execution result, leaving its prior `data` and `extensions` available to the renderer.
- **Evidence:** `docs/review/temp-tests/error_policy/test_runtime.py` used a `StrawberryExecutionResult` subclass accepted by `is_maskable_result` whose `errors` getter raises while its data contains a sensitive marker. Before the fix, `_process_result` left that marker in `result.data`; the helper-only fail-closed test did not exercise the integration assignment seam.
- **Impact:** A masking failure could turn the documented fail-closed floor into a response that still publishes execution data (and potentially extension payloads) from a result the policy explicitly could not inspect. This is a bounded custom-result edge, but it violates the security invariant precisely on the masking-failure path.
- **Recommendation:** Adopt `data`, `errors`, and `extensions` together whenever the helper returns a replacement. If a consumer-supplied result holder rejects one of those assignments, replace `execution_context.result` with a safe stock `StrawberryExecutionResult` carrying only the policy message and no data.
- **Proof:** `tests/test_error_policy.py::test_the_extension_adopts_all_fields_of_the_outer_fail_closed_degrade` pins the unreadable-result path through `_process_result`, asserting data and extensions are cleared and the policy error remains.

### Low

None.

## Summary

The policy object's validation and settings resolution are coherent, and the connected extension preserves deliberate GraphQL errors while masking unexpected sync, async, and streamed failures with correlated server logging. One medium fail-closed integration gap was confirmed and fixed at the extension result-adoption seam; no other root-cause finding was justified.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/extensions/error_policy.py`: `_process_result` now adopts all result fields from the masking helper, including the `data=None`/empty-extension floor; assignment failures log and replace the execution-context result with a safe stock result instead of leaving potentially unsafe data attached.
- Changed `tests/test_error_policy.py`: added an admitted hostile Strawberry result and a regression test for complete outer-degrade adoption.
- Scratch verification: `uv run pytest docs/review/temp-tests/error_policy/test_runtime.py --no-cov -q` failed before the fix with the sensitive data retained and passed after the fix.
- Focused post-edit validation: `uv run pytest tests/test_error_policy.py --no-cov` — 44 passed; `uv run pytest examples/fakeshop/test_query/test_error_policy_api.py --no-cov` — 17 passed; `uv run pytest tests/test_routers.py --no-cov -k 'error_policy or streamed_value_the_policy_cannot_mask or stop_aware_schema_passes_every_upstream_schema_read'` — 2 passed.
- Formatter/linter: `uv run ruff format .` and `uv run ruff check --fix .` passed.
- Rejected findings: no changes were made to the policy defaults, structural GraphQLError classification, settings precedence, debug gate, correlation-id generation, logging contract, extension ordering, or streamed transport seam; connected live/package/router tests and runtime source inspection support those contracts. No full suite was run.
- Changelog: no entry added; this is a bounded fail-closed hardening correction.

## Independent verification (Worker 2)

- Scoped review: `git --no-pager diff c1d948fc269e4b09823c3c52849631be34025500 -- django_strawberry_framework/extensions/error_policy.py` contains only the item-10 `_process_result` change: adopt `data`, `errors`, and `extensions`, with a stock-result replacement when assignment fails. The permanent test delta adds only `tests/test_error_policy.py::test_the_extension_adopts_all_fields_of_the_outer_fail_closed_degrade` and its admitted hostile Strawberry result.
- Production trace: `error_policy.py` resolves the frozen policy at schema construction with explicit > setting > defaults precedence; the extension structurally preserves parse/validation errors and raised `GraphQLError`s, masks other exceptions with fresh `uuid4().hex` IDs and package `ERROR` logs carrying `exc_info`, and applies the same synchronous hook to sync/async execution. `consumers.py::_stop_aware_results` applies the shared classifier and replacement per streamed result for both `subscribe` and `stream`, while `_StopAwareSchema` delegates all other schema reads; the schema installs one extension class per operation and reads the immutable policy from the executing schema.
- Focused validation passed: `uv run pytest tests/test_error_policy.py --no-cov` (44 passed); `uv run pytest examples/fakeshop/test_query/test_error_policy_api.py --no-cov` (17 passed); `uv run pytest tests/test_routers.py --no-cov -k 'error_policy or streamed_value_the_policy_cannot_mask or stop_aware_schema_passes_every_upstream_schema_read'` (2 passed); and explicit streamed/error cases in `tests/test_routers.py` (6 passed across both WebSocket protocols).
- Hostile-result reproduction independently demonstrated the root cause and fix without changing source or permanent tests. With an unreadable admitted Strawberry result, the old `result.errors = masked.errors` seam retained sensitive `data` and `extensions`; the current seam cleared both while retaining the policy error. A hostile `data` setter also selected the new stock `StrawberryExecutionResult(data=None, errors=[policy error])` fallback with `extensions=None`. The permanent regression invariant therefore fails under the old assignment and passes under the fix.
- Rejected findings remain disposed: no evidence against policy defaults/validation or precedence, structural deliberate-error preservation, DEBUG/explicit opt-out behavior, correlation-id/logging contract, extension ordering, sync/async parity, streaming transport ownership, or operation isolation. No unrelated paths were adopted, no source/permanent tests/CHANGELOG were edited, and no full suite was run.
