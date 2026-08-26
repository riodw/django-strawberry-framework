# Review: `django_strawberry_framework/_request_body.py`

Status: verified

## Understanding

`django_strawberry_framework/_request_body.py` is the private utility module responsible for determining whether an incoming HTTP request body exceeds a configured byte limit without prematurely materializing over-limit payloads in memory.

It owns:
1. Public evaluation entrypoint:
   - `body_exceeds_limit(request: HttpRequest, limit: int) -> bool`: Evaluates body size across a 4-tier resolution hierarchy and returns a boolean result without raising HTTP exceptions or inspecting application settings (policy is strictly owned by `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin`).
2. Resolution hierarchy:
   - **Tier 1 (Materialized cache):** If `hasattr(request, "_body")`, measures `len(request._body) > limit` directly.
   - **Tier 2 (Seekable stream probe):** For seekable streams (e.g. ASGI `SpooledTemporaryFile`), `_measured_remaining(stream)` inspects `stream.tell()`, seeks to EOF via `stream.seek(0, os.SEEK_END)`, verifies restoration via `_position_restored(stream, position)`, and computes unread bytes without reading or allocating data.
   - **Tier 3 (Bounded-read fallback):** For unseekable streams (e.g. WSGI `LimitedStream`, `AsyncRequestFactory`), `_bounded_read_exceeds_limit` reads at most `limit + 1` bytes in chunks capped at `_READ_CHUNK_BYTES` (64 KB) via `request.read()`. If the body fits within the limit, it closes the consumed stream, substitutes a rewound `BytesIO` stream on `request._stream`, and resets `request._read_started = False` so Django's `HttpRequest.body` property can run normally and enforce `DATA_UPLOAD_MAX_MEMORY_SIZE`.
   - **Tier 4 (Fail-closed error handling):** If a size probe moves a stream but fails to restore the initial offset (`_Probe.CORRUPTED`), or if a bounded read fails (`_bounded_read_exceeds_limit` encountering `UnreadablePostError`, non-bytes chunks, or closing errors), the function returns `True` (fail closed) and logs server-side warnings (`_CORRUPTED_PROBE_LOG_MESSAGE` or `_UNREADABLE_STREAM_LOG_MESSAGE` with `exc_info=True`).
3. Stream capability and integrity guards:
   - `_declares_seekable(stream)`: Safely checks for `seekable` callable/attribute, supporting Python 3.10's `SpooledTemporaryFile` (where `seekable` is absent) by falling back to `tell()`.
   - `_position_restored(stream, position)`: Requires exact `type(position) is int` and verifies `stream.tell()` equals the original offset.
   - `_Probe` (`UNMEASURABLE`, `CORRUPTED`): Distinguishes streams that can be safely measured via reading from streams whose position is corrupted.
   - Strict exact-type enforcement: Enforces `type(...) is int` for positions/offsets and `type(chunk) is bytes` for read chunks to prevent foreign objects or subclasses from overriding comparison/arithmetic operators inside the security boundary.
4. Deferral on foreign/unbounded states:
   - Returns `False` if `request._stream` is `None` (synthetic request) or `request._read_started` is `True` (stream already read without caching `_body`), allowing downstream Django handlers (`RawPostDataException`) to handle the condition naturally.

## Verification

1. Examined all callers and integration points in `django_strawberry_framework/views.py` (`_enforce_request_body_limit`).
2. Reviewed existing permanent tests:
   - `tests/test_views.py`:
     - `test_an_over_limit_asgi_body_is_refused_without_materializing_anything`
     - `test_a_seekable_under_limit_body_reaches_strawberry_byte_for_byte`
     - `test_an_undeclared_seekable_stream_is_still_size_probed_rather_than_read`
     - `test_a_non_seekable_over_limit_body_reads_at_most_one_byte_past_the_limit`
     - `test_a_non_seekable_under_limit_body_is_handed_back_as_a_rewound_stream`
     - `test_an_unmeasurable_stream_falls_back_to_the_bounded_read`
     - `test_a_stream_that_probes_as_empty_is_read_rather_than_believed`
     - `test_a_stream_reporting_a_position_past_its_end_is_refused_rather_than_read`
     - `test_a_foreign_initial_position_uses_the_bounded_read_without_seeking`
     - `test_position_restored_rejects_a_foreign_position_before_calling_the_stream`
     - `test_a_foreign_restored_position_is_not_allowed_to_lie_about_the_stream`
     - `test_a_non_callable_seekable_marker_uses_the_bounded_read`
     - `test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read`
     - `test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate`
     - `test_a_probe_that_cannot_restore_the_position_refuses_instead_of_reading`
     - `test_a_genuinely_empty_body_is_allowed_by_one_bounded_read`
     - `test_a_request_stream_that_cannot_be_read_is_refused_rather_than_escaping`
     - `test_a_non_bytes_chunk_cannot_stall_or_run_protocols_inside_the_bounded_read`
     - `test_a_body_already_cached_by_middleware_is_measured_from_the_cache_and_refused`
     - `test_the_cap_defers_on_a_stream_some_other_component_already_consumed`
     - `test_the_cap_defers_on_a_request_that_carries_no_stream_at_all`
   - `examples/fakeshop/test_query/test_transport_api.py`:
     - Verified end-to-end multi-fragment ASGI body limits, understated/absent Content-Length headers, CSRF re-entry preservation, and upload streaming.
3. Executed focused test runs:
   - `uv run pytest --no-cov tests/test_views.py -k "request_body or probe or seekable or stream or position"` (77 passed)
   - `uv run pytest --no-cov examples/fakeshop/test_query/test_transport_api.py` (77 passed)
4. Created and executed disposable scratch test `docs/review/temp-tests/_request_body/test_scratch_request_body.py` covering:
   - `_declares_seekable` branches (raising attribute access, absent attribute, non-callable attribute, raising callable, callable returning False/True).
   - `_position_restored` branches (non-int target, raising seek, raising tell, non-int tell, wrong int tell, honest stream).
   - `_measured_remaining` branches (unseekable, raising tell, non-int tell, end seek raising with successful restore, end seek raising with failed restore, end seek succeeding with failed restore, non-int end offset, zero/negative remaining, honest positive remaining).
   - `body_exceeds_limit` lifecycle (pre-cached `_body`, synthetic request without `_stream`, `_read_started=True`, corrupted stream probe with warning logging, seekable stream).
   - `_bounded_read_exceeds_limit` non-bytes chunk rejection, exception logging with traceback, KeyboardInterrupt propagation.
   - `_measured_by_bounded_read` under-limit stream replacement and over-limit termination.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/_request_body.py` is a robust, well-specified, and rigorously defensive module. It successfully centralizes all interactions with Django's private request-body stream internals, provides comprehensive capability probing and fail-closed bounded reading, prevents memory exhaustion attacks, preserves Django's own `DATA_UPLOAD_MAX_MEMORY_SIZE` checks, and avoids executing foreign protocol methods. No defects or design issues found.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/test_views.py` and `examples/fakeshop/test_query/test_transport_api.py`) comprehensively pins all probe paths, bounded read ceilings, stream substitution lifecycles, warning log emissions, and type validation invariants.
- Scratch verification:
  - `docs/review/temp-tests/_request_body/test_scratch_request_body.py` passed (6/6 tests) verifying all capability, restoration, measurement, error handling, and lifecycle branches.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/_request_body.py` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/_request_body.py` passed (1 file already formatted).
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/_request_body.py` passed.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Trace & behavioral verification:
  - Re-traced entrypoint `body_exceeds_limit(request, limit)` and its 4-tier resolution hierarchy:
    1. Pre-cached `request._body` fast-path evaluation (`len(request._body) > limit`).
    2. Seekable probe via `_measured_remaining(stream)` inspecting offsets (`tell()`, `seek(0, SEEK_END)`), verifying exact `int` types, restoring offsets via `_position_restored(stream, position)`, and computing unread bytes without body allocation.
    3. Non-seekable fallback via `_bounded_read_exceeds_limit(request, stream, limit)` reading at most `limit + 1` bytes in 64 KB chunks, validating exact `bytes` chunk types, closing the consumed stream on under-limit bodies, installing a rewound `BytesIO` on `request._stream`, and resetting `_read_started = False` so Django's `HttpRequest.body` runs normally with `DATA_UPLOAD_MAX_MEMORY_SIZE` enforcement intact.
    4. Fail-closed security boundary: returns `True` and emits targeted server-side `WARNING` records (`_CORRUPTED_PROBE_LOG_MESSAGE` without traceback, `_UNREADABLE_STREAM_LOG_MESSAGE` with `exc_info=True`) when positions cannot be verified as restored (`_Probe.CORRUPTED`) or when stream reads fail (`UnreadablePostError`, non-bytes chunks, close failures).
  - Confirmed deferral (`return False`) on synthetic requests (`request._stream is None`) and already-consumed un-cached requests (`request._read_started is True`), deferring downstream handling to Django's native `RawPostDataException`.
- Scoped diff verification:
  - Executed `git diff 12779c99 -- django_strawberry_framework/_request_body.py` — verified 0 lines changed (clean zero-edit cycle).
- Focused test runs:
  - `uv run pytest --no-cov tests/test_views.py -k "request_body or probe or seekable or stream or position"` (77 passed).
  - `uv run pytest --no-cov examples/fakeshop/test_query/test_transport_api.py` (77 passed).
- Independent scratch testing:
  - Created and executed `docs/review/temp-tests/_request_body/test_independent_scratch_request_body.py` (6/6 passed), verifying:
    - `_declares_seekable` on raising descriptor properties, non-callable attributes, and truthy callables.
    - `_position_restored` rejecting float/subclassed ints, raising/subclassed `tell()` outputs, and verifying honest streams.
    - `_measured_remaining` rejecting non-int end positions, non-positive remaining counts, and corrupted position restores.
    - Multi-chunk `_measured_by_bounded_read` across chunk boundaries (>64 KB payloads), under-limit stream rewinding, and over-limit termination.
    - Error boundaries capturing `UnreadablePostError` and non-`bytes` chunk objects into fail-closed warnings with attached tracebacks.
    - Full `body_exceeds_limit` lifecycle covering pre-cached bodies, synthetic requests, read-started requests, and corrupted probe logging.
  - Combined scratch suite `docs/review/temp-tests/_request_body/` (12/12 passed).
- Disposition of findings:
  - Verified no defects, performance issues, or design gaps.
  - Zero-edit review cycle confirmed complete. Status updated to `verified`.

