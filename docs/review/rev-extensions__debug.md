# Review: `django_strawberry_framework/extensions/debug.py`

Status: verified

## Understanding

`django_strawberry_framework/extensions/debug.py` implements `DjangoDebugExtension`, the development-only Strawberry `SchemaExtension` that captures Django database query logs and execution exceptions during GraphQL operations, exposing them on the response's `extensions["debug"]` envelope.

It owns:
1. **Cursor Capture Coordination & Overlap Safety:**
   - Coordinates database connection instrumentation via `_CursorCaptureCoordinator` (`_coordinator`), acquiring `force_debug_cursor = True` per concrete `BaseDatabaseWrapper` instance across `connections.all()`.
   - Tracks nesting depth and saved original flag values in `_ActiveCapture`, guaranteeing clean restoration of previous flag values upon release regardless of async/sync overlap or prior context state.
   - Guarantees fail-loud, exception-safe setup cleanup via `contextlib.ExitStack` in `on_operation`: if acquisition fails on a later alias, all previously acquired connections are safely unwound before the exception propagates.
2. **Fail-Closed Security Posture (`settings.DEBUG = False`):**
   - Strictly fails closed when `settings.DEBUG` is not `True` unless explicitly initialized with `allow_unsafe_production=True`.
   - Enforces that `allow_unsafe_production` is a strict `bool` at `__init__`, raising `ConfigurationError` on any non-bool input (rejecting truthy strings like `"false"` or `"0"` that would otherwise accidentally arm disclosure).
   - In inert posture, skips cursor acquisition and snapshotting completely, emitting a single descriptive `logger.warning` without disrupting normal request execution.
3. **Deterministic Payload Serialization:**
   - SQL rows (`_serialize_sql_row`): serializes Django query-log entries to graphene wire keys (`vendor`, `alias`, `sql`, `duration`, `isSlow`, `isSelect`), keeping SQL strings verbatim with interpolated parameters and deriving `isSlow` against `_SLOW_QUERY_SECONDS = 10`.
   - Exception rows (`_serialize_exception`): extracts exception type, string representation, and formatted traceback (`__traceback__`).
   - Exception chain unrolling (`_terminal_original_error`): resolves nested `GraphQLError.original_error` references to the underlying terminal Python exception with cycle detection (`seen_identities`) and a deterministic recursion depth ceiling (`_MAX_ORIGINAL_ERROR_HOPS = 64`).
   - Error classification (`_collect_exceptions`): filters out parse/validation errors lacking `original_error`, preserving execution error order without speculative deduplication.
4. **Deterministic Payload Caps & Budgeting:**
   - Enforces invariant limits: `_MAX_SQL_ROWS = 100`, `_MAX_EXCEPTION_ROWS = 25`, `_MAX_SQL_TEXT_CHARS = 4096`, `_MAX_EXCEPTION_MESSAGE_CHARS = 4096`, `_MAX_EXCEPTION_STACK_CHARS = 16384`, and `_MAX_PAYLOAD_TEXT_CHARS = 262144`.
   - Applies three-pass truncation in `_apply_payload_caps`:
     1. Per-row string truncation with `_TRUNCATION_MARKER = "... [truncated]"`.
     2. Earliest row preservation up to row count caps.
     3. Shared variable string cost budget (`_row_cost`), prioritizing exception rows before allocating remaining budget to SQL rows, stopping immediately on over-budget rows.
5. **Non-Interference & Lifecycle Resilience:**
   - In `_build_payload`, catches exceptions independently during SQL log draining (preserving prefix rows serialized prior to failure) and exception collection (degrading to an empty list), logging server-side errors without compromising the primary operation result.
   - Stashes payload only when `execution_context.result` is an instance of `GraphQLExecutionResult`, ensuring parse/validation failures never publish an empty `debug` dictionary.
   - Provides an idempotent, side-effect-free `get_results()` read returning `{"debug": self._payload}` or `{}`.

## Verification

1. Traced connections across callers, dependencies, and lifecycle points:
   - `django_strawberry_framework/extensions/__init__.py` (re-export of `DjangoDebugExtension`)
   - `tests/extensions/test_debug.py` (comprehensive suite covering wire serialization, coordinator overlap, partial-acquisition unwind, query-log slicing clamp, double `get_results` recovery, error masking ordering, async task overlap, nested sync log sharing, concurrent instance isolation, diagnostic degradation, transaction boundaries, sibling hook ordering, fail-closed gate, and payload cap arithmetic)
   - `examples/fakeshop/test_query/test_debug_extension_api.py` (live HTTP acceptance tests for forced debug cursor capture, optimizer visibility prefetch shape, mutation INSERT capture, unmasked exception rows, validation vs execution boundaries, no-SQL queries, default off posture, fail-closed warning, and over-cap payload truncation)
2. Ran existing test suites:
   - `uv run pytest tests/extensions/test_debug.py examples/fakeshop/test_query/test_debug_extension_api.py --no-cov` (76 passed).
3. Executed scratch test suite `docs/review/temp-tests/extensions__debug/test_scratch_debug.py`:
   - Verified `_CursorCaptureCoordinator` acquire/release depth and saved state tracking.
   - Verified `_serialize_sql_row` wire keys and `isSlow` threshold boundaries.
   - Verified `_serialize_exception` formatting.
   - Verified `_terminal_original_error` cycle handling and 64-hop recursion ceiling.
   - Verified `_collect_exceptions` None/empty handling and validation error filtering.
   - Verified `_query_log_entries_since` start offset slicing and length overflow clamp.
   - Verified `_truncate` marker suffix and `_row_cost` string character summation.
   - Verified `_apply_payload_caps` row limits, individual field limits, and total text budget priority.
   - Verified `_build_payload` error degradation and logging.
   - Verified `DjangoDebugExtension` init type checks and fail-closed withheld lifecycle.
   - Result: 12 passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/extensions/debug.py` is a robust, well-architected, and secure extension. It enforces strict fail-closed disclosure controls under production settings, thread- and overlap-safe cursor reference counting, bounded memory and wire payload caps, deterministic exception chain unrolling with cycle defense, and comprehensive error resilience that shields operation execution from diagnostic failures.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/extensions/test_debug.py` and `examples/fakeshop/test_query/test_debug_extension_api.py`) covers all contracts: wire serialization, coordinator overlap safety, partial-acquisition cleanup, double `get_results` recovery, async task overlap, nested sync attribution, concurrent instance isolation, failure degradation, transaction capture boundaries, fail-closed production gates, and payload budget caps.
- Scratch verification:
  - `docs/review/temp-tests/extensions__debug/test_scratch_debug.py` passed (12/12 tests) verifying coordinator mechanics, serializer field contracts, deep error unrolling, slicing clamps, truncation markers, payload caps, and fail-closed lifecycles.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/extensions/debug.py docs/review/temp-tests/extensions__debug/test_scratch_debug.py` passed with 0 errors.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/extensions/debug.py` passed with 0 errors.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Verified zero-edit cycle: scoped diff `git diff 12779c99 -- django_strawberry_framework/extensions/debug.py` is empty.
- Re-traced behavior and security contracts:
  - `_CursorCaptureCoordinator`: Verified thread-safe lock-protected reference counting, saved flag restoration, and multi-bracket nesting support across concrete `BaseDatabaseWrapper` instances.
  - Fail-closed security gate: Verified strict `settings.DEBUG is True` check, strict `isinstance(allow_unsafe_production, bool)` construction validation, safe withholding under production settings without disrupting query execution, and warning emission.
  - Serialization contracts: Verified exact graphene wire dictionary keys (`vendor`, `alias`, `sql`, `duration`, `isSlow`, `isSelect`), verbatim query string preservation, and `_SLOW_QUERY_SECONDS = 10` boundary condition.
  - Exception unrolling and error filtering: Verified `_terminal_original_error` cycle termination via identity tracking and 64-hop depth bounds, alongside parse/validation error exclusion in `_collect_exceptions`.
  - Bounded payload caps and budgeting: Verified deterministic three-pass truncation, row count caps (`_MAX_SQL_ROWS = 100`, `_MAX_EXCEPTION_ROWS = 25`), string field truncation limits, and prioritized variable text budget (`_MAX_PAYLOAD_TEXT_CHARS = 262144`).
  - Error degradation: Verified independent SQL collection degrade (retaining produced prefix rows) and exception collection degrade (to empty list) with logging on `logger.exception`.
  - Extension lifecycle and idempotency: Verified `ExitStack` acquisition/unwind safety on `on_operation`, stashing on `GraphQLExecutionResult` only, and side-effect-free idempotent `get_results()`.
- Test execution:
  - Ran focused test suites: `uv run pytest tests/extensions/test_debug.py examples/fakeshop/test_query/test_debug_extension_api.py docs/review/temp-tests/extensions__debug/test_scratch_debug.py --no-cov` (88 passed).
  - Linters and formatters: `uv run ruff check django_strawberry_framework/extensions/debug.py docs/review/temp-tests/extensions__debug/test_scratch_debug.py` and `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/extensions/debug.py` passed with 0 errors.
- Disposition:
  - All findings disposed. Implementation is correct, complete, and fully verified.

