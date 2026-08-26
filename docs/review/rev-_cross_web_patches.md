# Review: `django_strawberry_framework/_cross_web_patches.py`

Status: verified

## Understanding

`django_strawberry_framework/_cross_web_patches.py` implements a defensive patch for `cross_web.DjangoHTTPRequestAdapter.body` (the synchronous HTTP request adapter used by Strawberry's Django view).

It owns:
1. Sync/async transport parity:
   - Upstream `cross_web.DjangoHTTPRequestAdapter.body` executes an unhandled `self.request.body.decode()`. When given non-UTF-8 bytes, this raises `UnicodeDecodeError` inside property evaluation, escaping view exception handlers and producing an unhandled `500`.
   - The async adapter (`AsyncDjangoHTTPRequestAdapter.get_body`) returns raw bytes `self.request.body`.
   - `_cross_web_patches.py` replaces `DjangoHTTPRequestAdapter.body` with `_patched_body(self)`, returning raw bytes `self.request.body` without eager decoding. This routes raw bytes into Strawberry's `BaseView.parse_json`, where `_strawberry_patches.py` can translate any decode errors into controlled `400` HTTP responses.
2. Safe lifecycle and configuration gate:
   - Evaluates `upstream_patches_enabled("cross_web")` to support global (`APPLY_UPSTREAM_PATCHES = False`) and per-dependency (`APPLY_UPSTREAM_PATCHES = {"cross_web": False}`) opt-outs.
   - Validates upstream shapes loudly at `apply()` via `_validate_upstream_shape()`: verifies `DjangoHTTPRequestAdapter` symbol availability, readable property presence, and `(self)` signature arity.
   - Preserves reload safety via `_captured_upstream_body_getter()`: stamps `_PATCH_OWNER_ATTRIBUTE` and `_PATCH_ORIGINAL_ATTRIBUTE` on `_patched_body` so in-process module reload recovers the genuine upstream descriptor instead of the patched replacement.
   - Provides idempotent and self-healing installation via `_patch_is_installed()` and `apply()`.
3. Independence from package view security policy:
   - Package views (`django_strawberry_framework/views.py`) use `_RawBodyRequestAdapter` (subclassing `DjangoHTTPRequestAdapter` to return raw bytes) and enforce strict UTF-8 decoding in `views.py::_RequestBodyBoundaryMixin.parse_json`. As a result, package views are completely independent of `APPLY_UPSTREAM_PATCHES` setting states.

## Verification

1. Traced integrations across `django_strawberry_framework/apps.py`, `django_strawberry_framework/conf.py`, `django_strawberry_framework/views.py`, `django_strawberry_framework/_strawberry_patches.py`, and `examples/fakeshop/test_query/test_transport_api.py`.
2. Reviewed existing permanent tests:
   - `tests/test_cross_web_patches.py`:
     - `test_apply_is_idempotent`
     - `test_apply_reinstalls_when_property_reverted`
     - `test_patch_is_installed_on_adapter`
     - `test_body_returns_raw_bytes_for_valid_utf8`
     - `test_body_returns_raw_bytes_for_invalid_utf8`
     - `test_body_returns_raw_bytes_for_utf8_bom`
     - `test_body_returns_raw_bytes_for_utf16_le_without_bom`
     - `test_patch_is_installed_false_when_symbol_missing`
     - `test_capture_returns_none_for_missing_adapter_or_body_property`
     - `test_apply_fails_loudly_when_symbol_missing`
     - `test_apply_fails_loudly_when_body_getter_signature_changes`
     - `test_apply_fails_loudly_when_original_getter_was_never_captured`
     - `test_apply_no_ops_when_toggle_disabled`
     - `test_apply_no_ops_when_cross_web_dependency_opted_out`
   - `tests/test_apps.py`:
     - `test_ready_applies_defensive_upstream_patches`
     - `test_each_individual_dependency_can_be_opted_out_alone`
   - `examples/fakeshop/test_query/test_transport_api.py`:
     - `test_the_cross_web_half_turns_upstreams_own_500_into_a_400` (parameterized over `invalid-utf8-in-json` and `raw-binary`)
3. Executed focused tests:
   - `uv run pytest --no-cov tests/test_cross_web_patches.py` (14 passed)
   - `uv run pytest --no-cov tests/test_apps.py examples/fakeshop/test_query/test_transport_api.py -k "cross_web"` (4 passed)
4. Created and executed disposable scratch test `docs/review/temp-tests/_cross_web_patches/test_scratch_cross_web_patches.py` covering:
   - `importlib.reload` safety and descriptor preservation across multiple reloads.
   - `_validate_upstream_shape` failure modes across various invalid parameter signatures (0 args, 2 args, `*args`, `**kwargs`, `keyword-only`).
   - Patch owner attribute stamping on `_patched_body`.
   - `_patched_body` raw byte pass-through across multiple byte payloads (empty bytes, arbitrary binary, large payloads, UTF-8 BOM, JSON payloads).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/_cross_web_patches.py` is a well-scoped, robust, and reload-safe upstream patch module. It reliably eliminates the sync/async body-handling asymmetry in upstream `cross_web`, validates upstream shape contracts, adheres to all repository conventions, and has comprehensive test coverage. No defects or design improvements identified.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/test_cross_web_patches.py`, `tests/test_apps.py`, and `examples/fakeshop/test_query/test_transport_api.py`) pins raw bytes pass-through, sync/async parity, upstream error translation to 400, loud shape validation, reload descriptor preservation, idempotency, and per-dependency settings opt-outs.
- Scratch verification:
  - `docs/review/temp-tests/_cross_web_patches/test_scratch_cross_web_patches.py` passed (4/4 tests) verifying in-process reload safety, signature validation variations, owner attribute stamps, and arbitrary byte payloads.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/_cross_web_patches.py tests/test_cross_web_patches.py` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/_cross_web_patches.py tests/test_cross_web_patches.py` passed.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/_cross_web_patches.py tests/test_cross_web_patches.py` passed.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Scoped diff against HEAD (`12779c99`): verified empty.
- Paths and behavior independently traced:
  - Third-party `cross_web.DjangoHTTPRequestAdapter.body` property replacement with `_patched_body` returning raw bytes (`self.request.body`), establishing parity with `AsyncDjangoHTTPRequestAdapter.get_body`.
  - Prevention of unhandled `500` `UnicodeDecodeError` in property context, routing raw bytes to `parse_json` for controlled `400` translation (in conjunction with `_strawberry_patches.py`).
  - Configuration gating via `upstream_patches_enabled("cross_web")` honoring both global (`APPLY_UPSTREAM_PATCHES = False`) and per-dependency (`APPLY_UPSTREAM_PATCHES = {"cross_web": False}`) settings opt-outs.
  - Upstream shape validation (`_validate_upstream_shape`) checking adapter symbol presence, readable property descriptor, and arity `(self)`.
  - In-process module reload descriptor preservation via `_PATCH_OWNER_ATTRIBUTE` and `_PATCH_ORIGINAL_ATTRIBUTE` on `_patched_body`.
  - Idempotent and self-healing application semantics via `_patch_is_installed()` and `apply()`.
  - Decoupling from package views (`views.py::_RawBodyRequestAdapter` and `_RequestBodyBoundaryMixin.parse_json`), confirming package views enforce strict UTF-8 policy irrespective of patch enablement.
- Disposable scratch verification:
  - Executed `docs/review/temp-tests/_cross_web_patches/test_scratch_cross_web_patches.py` (4 passed) verifying reload safety, descriptor unwrapping, invalid getter signature rejections, owner attribute stamping, and arbitrary byte pass-through.
- Focused permanent test verification:
  - `tests/test_cross_web_patches.py` (14 passed).
  - `tests/test_apps.py` and `examples/fakeshop/test_query/test_transport_api.py -k "cross_web"` (2 passed).
- Linters & formatters:
  - Ruff check, ruff format check, and trailing comma check verified clean on `django_strawberry_framework/_cross_web_patches.py` and `tests/test_cross_web_patches.py`.
- All findings disposed of: zero findings in target module. Module is sound and verified.
