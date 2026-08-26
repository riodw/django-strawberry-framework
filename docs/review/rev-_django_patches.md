# Review: `django_strawberry_framework/_django_patches.py`

Status: verified

## Understanding

`django_strawberry_framework/_django_patches.py` implements a defensive patch for Django's multi-database test teardown (`django.test.testcases.SimpleTestCase._remove_databases_failures`), hardening consumers against Django Trac #37064 (closed upstream as `wontfix`).

It owns:
1. Unwrap-time database failure recovery:
   - Upstream `SimpleTestCase._remove_databases_failures` unwraps disallowed connection methods by accessing `method.wrapped` unconditionally. If any test hook, middleware, or third-party library (e.g. `django-debug-toolbar`, Sentry) wrapped or replaced a connection method on an unpermitted database alias during test execution, teardown crashes with `AttributeError: 'function' object has no attribute 'wrapped'`.
   - `_django_patches.py` replaces `SimpleTestCase._remove_databases_failures` with `_patched_remove_databases_failures`, which adds an `_is_database_failure(method)` guard (`isinstance(method, _DatabaseFailure)`) before unwrapping. Genuine `_DatabaseFailure` instances are unwrapped to their original targets, while foreign replacements are left untouched.
2. Complete test hierarchy coverage:
   - Installed directly on `SimpleTestCase._remove_databases_failures`, covering `SimpleTestCase`, `TransactionTestCase`, and `TestCase` across Django's class hierarchy via MRO inheritance without requiring custom base classes.
3. Multi-version Django support:
   - Supports both audited upstream shapes via `_disallowed_connection_methods`:
     - Django 5.2.16–6.0.x: reads `cls._disallowed_connection_methods` class attribute.
     - Django 6.1+: reads `connection.features.disallowed_simple_test_case_connection_methods`.
4. Upstream shape and body validation:
   - `_validate_upstream_shape()` verifies that `_DatabaseFailure` exists, the captured descriptor is a `classmethod`, the signature matches `(cls)`, and the dedented body source matches one of `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`. Any drift or unreadable source raises a targeted `RuntimeError` at `apply()` time before modifying class state.
5. In-process reload safety and idempotency:
   - Preserves reload safety via `_captured_upstream_descriptor()`: stamps `_PATCH_OWNER_ATTRIBUTE` and `_PATCH_ORIGINAL_ATTRIBUTE` on `_patched_remove_databases_failures`, allowing `importlib.reload()` to retrieve the genuine Django descriptor instead of treating the package's prior patch as upstream code.
   - Idempotent and self-healing: re-entrant `apply()` calls are no-ops when installed, and re-install if a third party reverted the class attribute.
6. Configuration gating:
   - Evaluates `upstream_patches_enabled("django")` to honor global (`APPLY_UPSTREAM_PATCHES = False`) and per-dependency (`{"APPLY_UPSTREAM_PATCHES": {"django": False}}`) opt-outs.

## Verification

1. Traced callers and integration points across `django_strawberry_framework/apps.py`, `django_strawberry_framework/conf.py`, and `django_strawberry_framework/testing/_wrap.py`.
2. Reviewed existing permanent tests:
   - `tests/test_django_patches.py`:
     - `test_apply_is_idempotent`
     - `test_apply_reinstalls_when_class_attribute_reverted`
     - `test_patch_is_installed_on_simple_test_case`
     - `test_patch_is_inherited_by_transaction_test_case`
     - `test_patch_is_inherited_by_test_case`
     - `test_patch_is_installed_returns_false_when_attribute_absent_from_class_dict`
     - `test_patched_remove_databases_failures_unwraps_a_real_wrapper`
     - `test_patched_remove_databases_failures_skips_non_wrapper_methods`
     - `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass`
     - `test_unpatched_remove_databases_failures_crashes_on_non_wrapper`
     - `test_apply_fails_loudly_when_database_failure_symbol_missing`
     - `test_apply_fails_loudly_when_upstream_method_signature_changes`
     - `test_apply_fails_loudly_when_upstream_body_drifts`
     - `test_validation_accepts_every_audited_upstream_body_and_refuses_a_third`
     - `test_disallowed_methods_read_prefers_the_class_attribute_shape`
     - `test_disallowed_methods_read_falls_back_to_the_connection_feature_flag`
     - `test_disallowed_methods_rejects_an_unvalidated_upstream_shape`
     - `test_apply_fails_loudly_when_upstream_source_is_unavailable`
     - `test_apply_no_ops_when_toggle_disabled`
     - `test_apply_no_ops_when_django_dependency_opted_out`
     - `test_django_dependency_opt_out_silences_drifted_pin_abort`
   - `tests/test_apps.py`:
     - `test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`
     - `test_ready_dispatches_all_three_patch_appliers_and_refires_safely`
     - `test_ready_reinstalls_patches_after_their_modules_reload`
   - `tests/testing/test_wrap.py`:
     - `test_safe_wrap_connection_method_pairs_with_unwrap_time_patch_for_defense_in_depth`
3. Executed focused test suites:
   - `uv run pytest --no-cov tests/test_django_patches.py` (21 passed)
   - `uv run pytest --no-cov tests/test_apps.py` (8 passed)
   - `uv run pytest --no-cov tests/testing/test_wrap.py` (7 passed)
4. Created and executed disposable scratch test `docs/review/temp-tests/_django_patches/test_scratch_django_patches.py` covering:
   - In-process module reload descriptor recovery and reinstallation.
   - `_validate_upstream_shape` failure modes across signature mutations (0 args, varargs, keyword-only args, non-classmethod descriptors).
   - `_is_database_failure` handling when `_DatabaseFailure` is `None`.
   - `_patch_is_installed` edge cases with non-standard class attributes.
   - `_disallowed_connection_methods` rejection of unvalidated sources.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/_django_patches.py` is a robust, well-architected, and fully tested upstream patch module. It addresses Django Trac #37064 at the root definition site (`SimpleTestCase`), correctly validates upstream AST bodies across supported Django versions, handles module reload cycles cleanly, and provides clear settings-based opt-outs. No defects or design issues found.

## Implementation (Worker 1)

- Changed files: None — zero-edit cycle.
- Scoped diff against HEAD (`12779c99`): empty.
- Permanent tests and pinned behavior:
  - Existing suite (`tests/test_django_patches.py`, `tests/test_apps.py`, and `tests/testing/test_wrap.py`) comprehensively pins `_DatabaseFailure` unwrapping, non-wrapper skipping, MRO inheritance across all `SimpleTestCase` subclasses, upstream crash reproduction, loud multi-tier shape validation, reload descriptor preservation, and per-dependency settings opt-outs.
- Scratch verification:
  - `docs/review/temp-tests/_django_patches/test_scratch_django_patches.py` passed (5/5 tests) verifying reload safety, signature validation variations, owner attribute stamps, None-symbol handling, and unvalidated source rejection.
- Formatter and linter results:
  - `uv run ruff check django_strawberry_framework/_django_patches.py tests/test_django_patches.py` passed with 0 errors.
  - `uv run ruff format --check django_strawberry_framework/_django_patches.py tests/test_django_patches.py` passed.
  - `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/_django_patches.py tests/test_django_patches.py` passed.
- Evidence for rejected findings: None.
- Changelog entry: No — zero-edit cycle, existing behavior unchanged.

## Independent verification (Worker 2)

- Trace & behavioral verification:
  - Traced complete lifecycle from `apps.py` (`ready()` dispatching `apply()`), settings configuration gating via `conf.py` (`upstream_patches_enabled("django")`), and interaction with `testing._wrap.py` (`safe_wrap_connection_method`).
  - Re-verified multi-version Django support in `_disallowed_connection_methods` handling class attributes on Django 5.2–6.0.x and per-connection feature flags on Django 6.1+.
  - Re-verified reload safety through `_captured_upstream_descriptor()` recovering original Django descriptors via `_PATCH_ORIGINAL_ATTRIBUTE` without treating prior monkey-patches as upstream code.
  - Re-verified strict upstream validation via `_validate_upstream_shape()` verifying presence of `_DatabaseFailure`, `classmethod` descriptor type, exact `(cls)` signature, and exact match against audited dedented body constants.
- Scoped diff verification:
  - Executed `git diff 12779c99 -- django_strawberry_framework/_django_patches.py` — verified 0 lines changed (clean zero-edit cycle).
- Focused test runs:
  - `uv run pytest --no-cov tests/test_django_patches.py tests/test_apps.py tests/testing/test_wrap.py` (36 passed).
- Independent scratch testing:
  - Created and executed `docs/review/temp-tests/_django_patches/test_independent_scratch_django_patches.py` (4/4 passed), verifying:
    - Selective multi-database teardown unwrapping honoring `cls.databases` inclusion/exclusion.
    - Reload recovery and descriptor preservation under `importlib.reload()`.
    - `_validate_upstream_shape()` loud failure on staticmethods, non-descriptors, 0-parameter functions, and keyword-only signatures.
    - Graceful `_is_database_failure()` behavior when `_DatabaseFailure` is `None`.
  - Combined scratch suite `docs/review/temp-tests/_django_patches/` (9/9 passed).
- Disposition of findings:
  - Verified no defects, performance bottlenecks, or design gaps.
  - Zero-edit review cycle confirmed complete. Status updated to `verified`.
