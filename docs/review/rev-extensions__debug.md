# Review: `django_strawberry_framework/extensions/debug.py`

Status: verified

## Understanding

`DjangoDebugExtension` is an explicit development diagnostic extension. It brackets
configured Django database wrappers with the reference-counted
`force_debug_cursor` coordinator, snapshots query-log positions, serializes SQL and
execution exceptions, applies deterministic row/text caps, and publishes a fresh
`extensions["debug"]` payload only after a real GraphQL execution result exists.
Parse/validation early returns remain free of the debug key. The extension is
intentionally not root-exported and requires either exact `settings.DEBUG is True`
or an explicit boolean `allow_unsafe_production=True` acknowledgement.

The coordinator is keyed by concrete connection wrapper, not alias, and restores
the exact prior flag after overlapping/nested captures. Diagnostic collection
degrades independently so malformed query-log entries or exception objects cannot
replace the operation result or disclose unbounded data. Masking-extension order is
load-bearing: debug must be listed after a masking extension so its teardown sees
the original exceptions.

## Verification

- Traced the extension through Strawberry's sync/async lifecycle, Django cursor
  wrappers and `queries_log`, `schema.py` extension ordering, `error_policy.py`,
  `consumers.py`, and the live fakeshop debug mounts.
- The initial focused package suite passed 194 tests before this cycle's change.
- A direct reproduction with `settings.DEBUG = "False"` showed the old
  `bool(settings.DEBUG)` gate published a `debug` payload containing a sensitive
  exception marker.
- `uv run pytest tests/extensions/test_debug.py --no-cov -q` passed 64 tests after
  the fix.
- `uv run pytest tests/extensions/test_debug.py tests/test_error_policy.py
  tests/test_resource_policy.py --no-cov -q` passed 197 tests.
- `uv run pytest examples/fakeshop/test_query/test_debug_extension_api.py --no-cov
  -q` passed 12 live tests.
- Compile and Ruff checks passed for the extension modules and their tests.

## Improvements

### High

- **The malformed `DEBUG` gate enabled disclosure.**
  - **Observation:** `_disclosure_permitted()` used `bool(settings.DEBUG)`, so any
    truthy malformed value—including the common environment-string value
    `"False"`—enabled SQL and unmasked traceback publication for a bare debug
    extension entry.
  - **Evidence:** A direct schema execution with `settings.DEBUG = "False"` and a
    resolver raising a sensitive marker returned `debug_key=True` and the marker
    inside the debug extension payload.
  - **Impact:** A deployment that intended production mode but supplied a string or
    non-boolean setting could expose credentials, PII, SQL parameters, exception
    messages, and server paths.
  - **Recommendation:** Treat only the exact boolean `True` as the development
    disclosure opt-in; retain `allow_unsafe_production=True` as the explicit
    production acknowledgement.
  - **Proof:** `tests/extensions/test_debug.py::test_malformed_debug_setting_stays_fail_closed`
    covers `"False"`, `1`, and an arbitrary object and confirms normal execution
    with no debug payload.

### Medium

None.

### Low

None.

## Summary

The diagnostic capture, truncation, exception-chain handling, overlap-safe cursor
restoration, execution-result gating, masking ordering, and live response contract
are coherent. One High disclosure defect was fixed at the debug extension's
security gate; no further finding remains.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/extensions/debug.py` so `_disclosure_permitted`
  requires `settings.DEBUG is True` unless the explicit boolean acknowledgement is
  present.
- Added `tests/extensions/test_debug.py::test_malformed_debug_setting_stays_fail_closed`
  for malformed truthy and non-boolean debug settings.
- Ran `uv run ruff format .` and `uv run ruff check --fix .`; both passed.
- Pre-existing concurrent changes in `extensions/error_policy.py`,
  `extensions/resource_policy.py`, and their package tests were preserved and not
  re-attributed to this item.
- No changelog entry was requested.

## Independent verification (Worker 2)

- Re-traced the old and new gate, confirming that exact `True`, explicit unsafe
  acknowledgement, and all malformed values have distinct intended behavior.
- Re-ran the complete debug package suite, the combined extension package suite,
  and the live debug suite; 64, 197, and 12 tests passed respectively.
- Confirmed compile, Ruff, and scoped whitespace checks are clean. No additional
  debug-extension finding remains.
