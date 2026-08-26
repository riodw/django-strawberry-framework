# Review: `django_strawberry_framework/conf.py`

Status: verified

## Understanding

`django_strawberry_framework/conf.py` implements the centralized settings management system for the package, reading configuration from the host project's `DJANGO_STRAWBERRY_FRAMEWORK` Django settings dictionary.

It owns:
1. `Settings` accessor class and `settings` singleton:
   - Provides attribute-style access (`settings.SOME_KEY`) to configured library settings.
   - Raises `AttributeError("Invalid setting: `...`")` when accessing undefined setting keys.
   - Preserves internal and dunder attribute lookups: `_user_settings`, `_live_source`, `_django_backed`, and `__*__` names raise plain `AttributeError` without recursion or misleading error messages.
   - Normalizes top-level settings inputs via `_normalize_user_settings`:
     - `None` or absent key coerces to `{}` (package-wide defensive `None` stance).
     - Standard `dict` instances are returned directly, preserving object identity for live in-place mutations.
     - General `Mapping` instances are copied to a `dict`.
     - Non-mapping types raise `ConfigurationError` eagerly.
   - Live synchronization against `django.conf.settings`:
     - Django-backed instances track `_live_source` and re-evaluate when `django.conf.settings.DJANGO_STRAWBERRY_FRAMEWORK` is replaced or deleted without a signal (e.g. `del settings.DJANGO_STRAWBERRY_FRAMEWORK` in pytest-django).
     - Explicit `Settings(mapping)` instances remain unbacked and fixed to their provided mapping.
   - In-place mutation on `django.test.signals.setting_changed`:
     - Connected at module import time with dispatch UID `django_strawberry_framework.conf.reload_settings`.
     - Signal receiver `reload_settings` calls `_reload_from_django` to mutate the existing singleton in place rather than rebinding the module global, ensuring imported references (`from .conf import settings`) observe live updates across test overrides.
2. Setting key constants and subsystem reader helper functions:
   - `APPLY_UPSTREAM_PATCHES_KEY = "APPLY_UPSTREAM_PATCHES"` / `upstream_patches_enabled(dependency: str) -> bool`:
     - Default `True`. Accepts a boolean or a `Mapping[str, bool]` keyed by `UPSTREAM_PATCH_DEPENDENCIES = frozenset({"django", "strawberry", "cross_web"})`.
     - Eagerly validates mapping shape, non-string keys, unknown dependency names, and non-boolean values, raising `ConfigurationError`.
     - Protects against unknown caller arguments with `ValueError`.
   - `NESTED_CONNECTION_STRATEGY_KEY = "NESTED_CONNECTION_STRATEGY"` / `nested_connection_strategy_setting() -> str`:
     - Default `"windowed"`. Read by `optimizer/nested_fetch.py::resolve_strategy`.
   - `SINGLE_PARENT_FAST_PATH_KEY = "SINGLE_PARENT_FAST_PATH"` / `single_parent_fast_path_setting() -> bool`:
     - Default `True`. Read at fetch time by `optimizer/single_parent_fetch.py`.
   - `TESTING_ENDPOINT_KEY = "TESTING_ENDPOINT"` / `testing_endpoint_setting() -> str`:
     - Default `"/graphql/"`. Read by `testing/client.py`.
     - Protected with `testing_endpoint_setting.__test__ = False` against pytest collection warnings.
   - `HIDE_FLAT_FILTERS_KEY = "HIDE_FLAT_FILTERS"` / `hide_flat_filters_setting() -> bool`:
     - Default `False`. Read by `filters/inputs.py::_build_input_fields`.
   - `RELAY_GLOBALID_STRATEGY_KEY = "RELAY_GLOBALID_STRATEGY"` / `relay_globalid_strategy_setting() -> str | Callable[..., str] | None`:
     - Default `None`. Read by `types/relay.py::_validated_globalid_setting`.
   - `MAX_REQUEST_BODY_BYTES_KEY = "MAX_REQUEST_BODY_BYTES"` / `max_request_body_bytes_setting() -> int | None`:
     - Default `1_048_576` (1 MiB). Read by `views.py::_resolved_max_request_body_bytes`.
   - `RESOURCE_POLICY_KEY = "RESOURCE_POLICY"` / `resource_policy_setting() -> Any`:
     - Default `None`. Read by `resource_policy.py::resolve_resource_policy`.
   - `ERROR_POLICY_KEY = "ERROR_POLICY"` / `error_policy_setting() -> Any`:
     - Default `None`. Read by `error_policy.py::resolve_error_policy`.

## Verification

1. Traced connections across consumer modules:
   - `_django_patches.py`, `_strawberry_patches.py`, `_cross_web_patches.py` (`upstream_patches_enabled`)
   - `optimizer/nested_fetch.py` (`nested_connection_strategy_setting`)
   - `optimizer/single_parent_fetch.py` (`single_parent_fast_path_setting`)
   - `testing/client.py` (`testing_endpoint_setting`)
   - `filters/inputs.py` (`hide_flat_filters_setting`)
   - `types/relay.py` (`relay_globalid_strategy_setting`)
   - `views.py` (`max_request_body_bytes_setting`)
   - `resource_policy.py` (`resource_policy_setting`)
   - `error_policy.py` (`error_policy_setting`)
2. Evaluated existing permanent tests in `tests/base/test_conf.py`:
   - `Settings` attribute lookup, missing key `AttributeError`, user setting return, lazy loading, preset mappings, defensive `None` fallback, and invalid type `ConfigurationError`.
   - Signal-driven and direct `reload_settings` behavior, in-place singleton mutation, imported reference consistency, dunder attribute lookup guards, recursion prevention on uninitialized instances, and idempotent signal connection.
   - `upstream_patches_enabled` default on, global boolean overrides, per-dependency mapping opt-outs, non-dict mapping handling, fail-loud validation on unknown dependencies, non-boolean values, non-string keys, non-mapping values, and invalid internal caller arguments.
   - `testing_endpoint_setting` pytest collection guard.
   - `single_parent_fast_path_setting` default on, live re-evaluation, and unvalidated truthiness handling.
   - Live sync on `del settings.DJANGO_STRAWBERRY_FRAMEWORK` restoring defaults across all reader helpers.
   - Reader helper defaults and explicit override values.
   - Retried live sync failures after bad live configuration values.
   - Explicit `Settings(mapping)` instance isolation from live Django settings changes.
3. Executed focused test run:
   - `uv run pytest tests/base/test_conf.py --no-cov` (48 passed).
4. Executed scratch test `docs/review/temp-tests/conf/test_conf_scratch.py`:
   - Verified default reader behavior, multi-key custom overrides, `override_settings` context manager integration and clean exit restoration, and attribute lookup guards on uninitialized instances (4 passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/conf.py` is robust, well-architected, and adheres cleanly to all repository and framework conventions. The singleton in-place mutation and live-sync mechanisms prevent test pollution and stale caches across Django test runners, while dedicated thin readers provide unambiguous settings access with strict downstream domain validation. No defects or design improvements identified.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - `tests/base/test_conf.py` (48 tests) comprehensively pins `Settings` lifecycle, lazy loading, live-sync with `django.conf.settings`, signal-driven in-place mutation, `upstream_patches_enabled` opt-out and fail-loud validation, `testing_endpoint_setting` collection guard, and all reader helper functions.
- Scratch verification:
  - `docs/review/temp-tests/conf/test_conf_scratch.py` passed (4/4 tests) verifying all 9 reader helpers under default and overridden configurations, `override_settings` context manager lifecycle, and `Settings` internal attribute guards.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/conf.py tests/base/test_conf.py` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/conf.py tests/base/test_conf.py` passed (2 files already formatted).
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/conf.py tests/base/test_conf.py` passed.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Scoped diff against HEAD (`12779c99`): verified empty.
- Paths and behaviors independently traced:
  - `Settings` accessor and `settings` singleton lifecycle, lazy loading on first attribute access, unbacked explicit instances vs django-backed singleton.
  - Live synchronization with `django.conf.settings` on attribute access, including resilience against non-signal key deletions (`del settings.DJANGO_STRAWBERRY_FRAMEWORK`).
  - Signal receiver `reload_settings` connected with `_DISPATCH_UID` idempotency and in-place singleton mutation preserving bound references (`from django_strawberry_framework.conf import settings`).
  - Defensive `None` stance: `DJANGO_STRAWBERRY_FRAMEWORK = None` coerced to `{}` uniformly across all reader helpers.
  - Eager validation: non-mapping settings raise `ConfigurationError`, uninitialized attribute lookups raise plain `AttributeError` without recursion or misleading messages.
  - Upstream patch configuration: `upstream_patches_enabled` global boolean toggle, per-dependency `Mapping[str, bool]` opt-out, unknown dependency detection, key/value type validation, and unknown caller argument validation (`ValueError`).
  - All 9 dedicated setting reader functions:
    - `upstream_patches_enabled`
    - `nested_connection_strategy_setting` (default `"windowed"`)
    - `single_parent_fast_path_setting` (default `True`)
    - `testing_endpoint_setting` (default `"/graphql/"`, `__test__ = False` collection guard)
    - `hide_flat_filters_setting` (default `False`)
    - `relay_globalid_strategy_setting` (default `None`)
    - `max_request_body_bytes_setting` (default `1_048_576`)
    - `resource_policy_setting` (default `None`)
    - `error_policy_setting` (default `None`)
  - Clean interactions with `override_settings` context manager.
- Disposable scratch verification:
  - `docs/review/temp-tests/conf/test_conf_scratch.py` passed (4/4 tests).
  - `docs/review/temp-tests/conf/test_worker2_conf_verification.py` passed (6/6 tests).
- Focused permanent test verification:
  - `uv run pytest tests/base/test_conf.py --no-cov` passed (48/48 tests).
- Linters & formatters:
  - Ruff check passed with 0 errors.
  - Trailing comma check passed.
- All findings disposed of: zero findings in target module. Module is sound, robust, and verified.
