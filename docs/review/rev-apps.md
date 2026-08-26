# Review: `django_strawberry_framework/apps.py`

Status: verified

## Understanding

`django_strawberry_framework/apps.py` defines the Django `AppConfig` subclass (`DjangoStrawberryFrameworkConfig`) responsible for registering the package with Django's application registry and dispatching defensive upstream patches at application startup.

It owns:
1. AppConfig registration contracts:
   - `name = "django_strawberry_framework"`: Matches the Python package name.
   - `verbose_name = "Django Strawberry Framework"`: Provides the human-readable display name.
   - Subclasses `django.apps.AppConfig`.
   - Django discovers and resolves `DjangoStrawberryFrameworkConfig` when consumers list `"django_strawberry_framework"` (or the explicit path `"django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig"`) in `INSTALLED_APPS`.
   - Carries no extraneous attributes (e.g. `label`, `default_auto_field`, or `default`).
2. Defensive patch dispatch lifecycle:
   - `ready()` method performs one-time upstream patch installation when Django is fully initialized.
   - Dispatches `apply()` across the three private patch modules in deterministic order:
     - `django_strawberry_framework._django_patches.apply()` (Django Trac #37064 test connection unwrap hardening)
     - `django_strawberry_framework._strawberry_patches.apply()` (Strawberry `BaseView.parse_json` / `parse_query_params` / multipart parser hardening)
     - `django_strawberry_framework._cross_web_patches.apply()` (`cross_web.DjangoHTTPRequestAdapter.body` raw bytes parity)
   - Function-local imports ensure importing `django_strawberry_framework.apps` in isolation does not eagerly import patch modules or upstream third-party dependencies before Django is configured.
   - Patch application is idempotent, self-healing on module reload, and gated via `APPLY_UPSTREAM_PATCHES` within each patch module.
   - `ready()` connects no unnecessary signals, registers no checks, and does not preempt consumer type finalization (`finalize_django_types`).

## Verification

1. Traced integrations across `django.apps.registry`, `django_strawberry_framework/_django_patches.py`, `django_strawberry_framework/_strawberry_patches.py`, `django_strawberry_framework/_cross_web_patches.py`, `django_strawberry_framework/conf.py`, and `examples/fakeshop/config/settings.py`.
2. Reviewed existing permanent tests in `tests/test_apps.py`:
   - `test_djangostrawberryframeworkconfig_importable_from_apps_module`
   - `test_djangostrawberryframeworkconfig_is_appconfig_subclass`
   - `test_djangostrawberryframeworkconfig_pins_name_and_verbose_name`
   - `test_djangostrawberryframeworkconfig_resolves_through_django_app_registry`
   - `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`
   - `test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`
   - `test_ready_dispatches_all_three_patch_appliers_and_refires_safely`
   - `test_ready_reinstalls_patches_after_their_modules_reload`
3. Executed focused tests:
   - `uv run pytest --no-cov tests/test_apps.py` (8 passed)
4. Created and executed disposable scratch test `docs/review/temp-tests/apps/test_scratch_apps.py` covering:
   - Module import purity without eager patch application or extraneous symbol exports.
   - Direct `DjangoStrawberryFrameworkConfig` instantiation lifecycle and registry lookup.
   - `ready()` execution and idempotency across multiple invocations.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/apps.py` is a clean, minimal, single-responsibility module that adheres strictly to Django's AppConfig contract and the package's design requirements. Patch dispatching is lazy, deterministic, idempotent, and thoroughly tested. No defects or design improvements identified.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/test_apps.py`) pins AppConfig subclassing, name/verbose_name values, registry resolution, forbidden attribute absences, deterministic dispatch of all three upstream patch appliers, idempotency on re-fire, and module reload resilience.
- Scratch verification:
  - `docs/review/temp-tests/apps/test_scratch_apps.py` passed (3/3 tests) verifying module purity, AppConfig instantiation lifecycle, registry resolution, and repeated `ready()` execution.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/apps.py tests/test_apps.py` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/apps.py tests/test_apps.py` passed (already formatted).
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/apps.py tests/test_apps.py` passed.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Scoped diff against HEAD (`12779c99`): verified empty.
- Paths and behaviors independently traced:
  - `DjangoStrawberryFrameworkConfig` AppConfig subclass contract (`name`, `verbose_name`).
  - AppConfig resolution via `django.apps.apps.get_app_config("django_strawberry_framework")` and `AppConfig.create("django_strawberry_framework")`.
  - Negative-shape validation: confirming absence of `label`, `default_auto_field`, and `default` in `DjangoStrawberryFrameworkConfig.__dict__`.
  - Function-local lazy imports of upstream patch appliers inside `ready()` preserving module-import purity.
  - Deterministic dispatch sequence across `_django_patches.apply()`, `_strawberry_patches.apply()`, `_cross_web_patches.apply()`.
  - Re-fire safety and idempotency of `ready()`.
  - Settings gating behavior when `APPLY_UPSTREAM_PATCHES` is toggled.
  - Module reload resilience of patch appliers driven through `ready()`.
- Disposable scratch verification:
  - `docs/review/temp-tests/apps/test_scratch_apps.py` passed (3/3 tests).
  - `docs/review/temp-tests/apps/test_independent_scratch_apps.py` passed (5/5 tests) verifying module purity, AppConfig factory resolution, strict patch dispatch order, clean handling of disabled patch settings, and class invariant annotations.
- Focused permanent test verification:
  - `uv run pytest --no-cov tests/test_apps.py` passed (8/8 tests).
- Linters & formatters:
  - Ruff check passed with 0 errors.
  - Trailing comma check passed.
- All findings disposed of: zero findings in target module. Module is sound and verified.
