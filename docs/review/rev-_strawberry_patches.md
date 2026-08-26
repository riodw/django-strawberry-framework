# Review: `django_strawberry_framework/_strawberry_patches.py`

Status: verified

## Understanding

`django_strawberry_framework/_strawberry_patches.py` implements defensive monkey patches for upstream Strawberry HTTP views (`BaseView`, `SyncBaseHTTPView`, and `AsyncBaseHTTPView`), applied at Django app load time via `DjangoStrawberryFrameworkConfig.ready()`.

It owns:
1. `UnicodeDecodeError` translation in `BaseView.parse_json`:
   - Upstream `BaseView.parse_json` catches only `json.JSONDecodeError`. When `json.loads` encounters undecodable non-UTF-8 bytes, it raises `UnicodeDecodeError` (a `ValueError` subclass, not `JSONDecodeError`), escaping upstream's catch and resulting in an unhandled `500` server error.
   - `_patched_parse_json` wraps `BaseView.parse_json`, catches `UnicodeDecodeError`, and translates it to `HTTPException(400, "Unable to parse request body as JSON")` with the original exception chained as `__cause__`.
2. Request body envelope validation and GET query-params shielding:
   - Upstream `parse_http_body` expects either a `dict` (single operation) or a `list` (batch operations), and unconditionally invokes `data.get("query")` or `item.get("query")`. A JSON scalar (`42`, `"string"`, `true`, `null`) or an array containing non-dict elements (`[1, 2]`, `[null]`, `[{...}, 42]`) crashes with `AttributeError` -> unhandled `500`.
   - `_patched_parse_json` rejects any parsed payload that is not a `dict` or a `list` where `all(isinstance(item, dict) for item in parsed)` with `HTTPException(400, "The GraphQL request body must be a JSON object (or an array of operations for a batch request).")`.
   - GET query-param parses (`BaseView.parse_query_params` for `variables` and `extensions`) are shielded via `_patched_parse_query_params`, which directly invokes `_original_parse_json` so GET requests retain exact upstream semantics (`variables=null` -> `None`, scalars preserved for upstream's specific per-param `400` errors).
3. Structurally invalid multipart map and path traversal handling:
   - Upstream `replace_placeholders_with_files` iterates `files_map.items()` and splits string paths. Client payloads providing an array map (`[{}]`), non-string paths, or invalid list indices crash with `AttributeError`, `IndexError`, `TypeError`, or `ValueError`. Upstream catches only `KeyError`, letting these errors become unhandled `500`s.
   - `_patched_sync_parse_multipart` and `_patched_async_parse_multipart` catch `_MULTIPART_TRAVERSAL_ERRORS` (`AttributeError`, `IndexError`, `TypeError`, `ValueError`) and verify via frame provenance (`_raised_inside_the_upload_utility(exc)`) that the exception originated within `replace_placeholders_with_files`. Validated traversal errors are translated to `HTTPException(400, "Unable to parse the multipart body")`. Same-typed exceptions originating elsewhere (e.g. server bugs in `parse_json`) are re-raised as `500`s.
4. Fail-loud upstream signature and body validation:
   - `_validate_upstream_shape()` verifies the presence and callability of all required symbols (`BaseView`, `HTTPException`, `SyncBaseHTTPView`, `AsyncBaseHTTPView`, `replace_placeholders_with_files`, and captured originals).
   - Verifies exact `(self, argument)` signature arity and `POSITIONAL_OR_KEYWORD` parameter kinds.
   - Source-pins the superseded `BaseView.parse_query_params` body against `_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE`, treating unreadable source as drift.
5. In-process reload safety and idempotency:
   - Preserves reload safety across `importlib.reload()` via `_captured_upstream_method()`, stamping `_PATCH_OWNER_ATTRIBUTE` and `_PATCH_ORIGINAL_ATTRIBUTE` on replacement callables so reloaded modules recover the original upstream method rather than wrapping a previous patch.
   - `_patch_is_installed()` verifies all four methods simultaneously, ensuring `apply()` self-heals if any individual method was reverted.
6. Settings configuration gating:
   - Gated via `upstream_patches_enabled("strawberry")`, respecting global (`APPLY_UPSTREAM_PATCHES = False`) and per-dependency (`{"APPLY_UPSTREAM_PATCHES": {"strawberry": False}}`) opt-outs.

## Verification

1. Traced callers and integration points across `django_strawberry_framework/apps.py`, `django_strawberry_framework/conf.py`, `django_strawberry_framework/views.py`, and `examples/fakeshop/test_query/test_transport_api.py`.
2. Reviewed existing permanent tests:
   - `tests/test_strawberry_patches.py` (55 tests) covering:
     - Idempotent `apply()` and self-healing reinstallation upon partial or complete method reversion.
     - `UnicodeDecodeError` translation with proper `HTTPException(400)` and `__cause__` attribution.
     - Pass-through of valid JSON objects and multibyte UTF-8 strings.
     - Retention of upstream `bytes` auto-detection semantics (UTF-16, UTF-32, UTF-8-BOM) for consumers mounting Strawberry's raw view.
     - Identity preservation for already-decoded `str` inputs.
     - Pass-through of upstream `json.JSONDecodeError` for malformed JSON.
     - Rejection of JSON scalars and non-dict batch elements with `HTTPException(400)`.
     - Pass-through of valid batch arrays to upstream batch validation.
     - Sync and async multipart map structural error translation (`[{}]`, non-string path, invalid list index).
     - Exception provenance checks preserving server-side errors raised outside the upload utility.
     - Query params shield routing for `null`, scalars, valid objects, malformed JSON, and empty strings.
     - Loud validation failures on missing symbols, changed signatures, body drift, and unreadable source.
     - Settings opt-outs (`APPLY_UPSTREAM_PATCHES = False`, `{"strawberry": False}`, `{"django": False}`).
     - Graceful handling of missing upstream owners during initial capture.
   - `tests/test_apps.py` covering startup `ready()` dispatch and reload resilience.
   - `tests/test_views.py` and `examples/fakeshop/test_query/test_transport_api.py` covering package view boundary decoding and HTTP wire behavior.
3. Executed focused test suites:
   - `uv run pytest --no-cov tests/test_strawberry_patches.py` (55 passed).
   - `uv run pytest --no-cov tests/test_apps.py examples/fakeshop/test_query/test_transport_api.py tests/test_views.py` (307 passed).
4. Created and executed disposable scratch test `docs/review/temp-tests/_strawberry_patches/test_scratch_strawberry_patches.py` (5 passed) covering:
   - `importlib.reload` descriptor recovery and reinstallation.
   - Signature validation across 0, 1, 3 parameters, keyword-only, and positional-only arguments.
   - Nested traceback frame traversal in `_raised_inside_the_upload_utility`.
   - Comprehensive scalar and invalid batch envelope combinations.
   - GET query-param shield routing and passthrough.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/_strawberry_patches.py` provides clean, comprehensive, and well-isolated defensive monkey-patches for upstream Strawberry HTTP view defects. It correctly translates `UnicodeDecodeError`, validates GraphQL request body envelopes, shields GET query-parameter parsing, and normalizes multipart traversal errors while preserving provenance for genuine server errors. Its fail-loud upstream validation and reload safety mechanisms are rigorous and fully tested. No defects or design issues found.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/test_strawberry_patches.py`, `tests/test_apps.py`, `tests/test_views.py`, and `examples/fakeshop/test_query/test_transport_api.py`) comprehensively pins `UnicodeDecodeError` translation, JSON envelope validation, GET query-param shielding, multipart error normalization and provenance guarding, upstream signature/body drift validation, reload safety, and per-dependency settings opt-outs.
- Scratch verification:
  - `docs/review/temp-tests/_strawberry_patches/test_scratch_strawberry_patches.py` passed (5/5 tests) verifying reload safety, signature validation variations, nested frame exception provenance, envelope edge cases, and query param routing.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/_strawberry_patches.py tests/test_strawberry_patches.py` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/_strawberry_patches.py tests/test_strawberry_patches.py` passed.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/_strawberry_patches.py tests/test_strawberry_patches.py` passed.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Scoped diff against HEAD (`12779c99`): verified empty.
- Paths and behavior independently traced:
  - `BaseView.parse_json` monkey-patching via `_patched_parse_json`:
    - Catches `UnicodeDecodeError` and translates to `HTTPException(400, "Unable to parse request body as JSON")` with `__cause__` chained.
    - Validates request body envelopes: accepts `dict` objects and `list` arrays of `dict`s; rejects scalars (`42`, `"str"`, `true`, `null`) and arrays with non-dict elements (`[1, 2]`, `[null]`, `[{...}, 42]`) with `HTTPException(400)`.
    - Preserves upstream `bytes` RFC 8259 encoding auto-detection for consumers mounting Strawberry's own view directly, and passes `str` through with identity preservation.
  - `BaseView.parse_query_params` GET shield via `_patched_parse_query_params`:
    - Re-routes GET `variables` and `extensions` parsing directly to `_original_parse_json`, shielding GET query-param parsing from the body envelope scalar guard (`variables=null` -> `None`, scalars preserved for upstream's per-param error).
    - Pinned against `_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE` with unreadable source treated as drift.
  - Sync and async multipart map error normalization via `_patched_sync_parse_multipart` and `_patched_async_parse_multipart`:
    - Traversal errors (`AttributeError`, `IndexError`, `TypeError`, `ValueError`) originating within `replace_placeholders_with_files` (checked via `_raised_inside_the_upload_utility`) translated to `HTTPException(400, "Unable to parse the multipart body")`.
    - Preserves server-side errors and other exception types originating outside the upload utility.
  - Configuration gating via `upstream_patches_enabled("strawberry")` honoring global (`APPLY_UPSTREAM_PATCHES = False`) and per-dependency (`APPLY_UPSTREAM_PATCHES = {"strawberry": False}`) opt-outs, with fail-loud validation of invalid configurations.
  - Fail-loud upstream shape validation (`_validate_upstream_shape`) on symbol availability, `(self, argument)` arity / parameter kind, and body source match.
  - In-process module reload safety via `_captured_upstream_method` and patch owner stamping (`_PATCH_OWNER_ATTRIBUTE`, `_PATCH_ORIGINAL_ATTRIBUTE`).
  - Idempotent and self-healing `apply()` and `_patch_is_installed()` covering all four patched methods simultaneously.
  - Decoupling from package views (`views.py::_RawBodyRequestAdapter` and `_RequestBodyBoundaryMixin.parse_json`), confirming package views own strict UTF-8 policy unconditionally.
- Disposable scratch verification:
  - Executed `docs/review/temp-tests/_strawberry_patches/test_scratch_strawberry_patches.py` and `test_independent_scratch_strawberry_patches.py` (11 passed) verifying reload safety, signature validation variations, nested frame exception provenance, invalid JSON envelopes, query param routing, configuration error propagation, UnicodeDecodeError chaining, JSONDecodeError pass-through, non-traversal exception pass-through, async multipart execution, and patch metadata stamps.
- Focused permanent test verification:
  - `tests/test_strawberry_patches.py` (55 passed).
  - `tests/test_apps.py`, `examples/fakeshop/test_query/test_transport_api.py`, `tests/test_views.py` (307 passed).
- Linters & formatters:
  - Ruff check, ruff format check, and trailing comma check verified clean on `django_strawberry_framework/_strawberry_patches.py` and `tests/test_strawberry_patches.py`.
- All findings disposed of: zero findings in target module. Module is sound and verified.
