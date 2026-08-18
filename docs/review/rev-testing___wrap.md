# Review: `django_strawberry_framework/testing/_wrap.py`

Status: verified

Cycle baseline: current `HEAD` `fa248bdf064b3dca52c1e591b6c6444b041bb65f`. The owned source and permanent test files were clean at dispatch:
`git --no-pager diff HEAD -- django_strawberry_framework/testing/_wrap.py tests/testing/test_wrap.py` is empty.

## Understanding

`safe_wrap_connection_method` owns the public, opt-in wrap-time protocol for a Django `BaseDatabaseWrapper` instance. It validates the consumer's replacement is callable, reads the named connection attribute, declines with `False` when the current value is Django's private `_DatabaseFailure`, and otherwise installs the exact wrapper object with `setattr` and returns `True`.

`django_strawberry_framework._django_patches::_is_database_failure` is the shared private-symbol-tolerant predicate. Its `None` fallback keeps importing the testing helper safe when Django removes or relocates `_DatabaseFailure`; the helper then follows the ordinary install path. The private `SimpleTestCase._remove_databases_failures` replacement is a separate unwrap-time owner, applied by `DjangoStrawberryFrameworkConfig.ready`; it restores only genuine `_DatabaseFailure` instances and leaves foreign replacements alone. Django's classmethod inheritance covers `SimpleTestCase`, `TransactionTestCase`, and `TestCase`.

The helper intentionally does not own restoration. Consumers save the original instance attribute and restore it in their teardown. This preserves wrapper identity because functions and callable objects assigned to a connection instance are returned without descriptor rebinding. A missing attribute or non-string attribute name raises the native `AttributeError` or `TypeError` before `setattr`, while arbitrary existing method names such as `chunked_cursor` and `create_cursor` use the same path.

## Verification

- Read the complete target, its public re-export in `testing/__init__.py`, `apps.py` startup dispatch, `_django_patches.py` import/validation/unwrap lifecycle, Django 6.1's `_DatabaseFailure` and audited teardown body, and `tests/testing/test_wrap.py` plus `tests/test_django_patches.py`.
- `uv run pytest -q --no-cov tests/testing/test_wrap.py tests/test_django_patches.py` — **28 passed** on Django 6.1.
- `DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop uv run python` lifecycle probe after `django.setup()` — **passed** exact callable identity for an arbitrary `create_cursor` name, explicit restoration, foreign callable preservation despite a misleading `.wrapped` attribute, and normal installation when `_DatabaseFailure` is patched to `None`.
- Direct malformed-input probe confirmed a non-callable wrapper raises the documented `TypeError` without changing the connection, `method_name=None` / `method_name=1` raise native `TypeError`, and a missing method name raises native `AttributeError`; no mutation occurs before those failures.
- Existing permanent tests cover non-callable wrappers including hostile `repr`, missing private-symbol behavior, arbitrary `chunked_cursor`, real `_DatabaseFailure` refusal, wrap/unwrap composition, identity/restoration, and the unwrap patch's foreign-method preservation. The target is not reachable through a real GraphQL HTTP request, so package tests are the strongest applicable tier.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The target has one clear wrap-time owner and correctly composes with the app-load unwrap backstop. Callable validation occurs before mutation, private-symbol absence degrades safely, arbitrary existing connection methods retain the same behavior, wrapper identity/restoration is explicit, and foreign or malformed-looking objects are not duck-unwrapped. No root-cause production change or permanent-test addition is warranted.

## Implementation (Worker 1)

No source or permanent-test edit was needed. The scoped target diff against current `HEAD` remains empty; no cross-file ownership expanded beyond the traced `_django_patches.py` and `apps.py` lifecycle seams. The required artifact is the only Worker 1 file created, and its status is `fix-implemented` for Worker 2's independent verification. No changelog entry is warranted. After creating this artifact, `uv run ruff format .` reported 423 files unchanged and `uv run ruff check --fix .` reported all checks passed.

## Independent verification (Worker 2)

No source or permanent-test edit was made during this verification. The target
and its connected production/test paths remain unchanged.

Focused regression suite:

`uv run pytest -q --no-cov tests/testing/test_wrap.py tests/test_django_patches.py` —
**28 passed** on Django 6.1.

Fresh-process probes after `django.setup()` exercised Django 6.1's actual
`SimpleTestCase._add_databases_failures` → consumer helper → patched
`_remove_databases_failures` lifecycle. The feature list was confirmed as
`connect`, `temporary_connection`, `cursor`, and `chunked_cursor`; all four
real `_DatabaseFailure` instances declined replacement, and teardown restored
each wrapped callable. A mixed lifecycle where `cursor` was replaced by a
foreign callable (including one exposing a misleading `.wrapped`) left that
replacement untouched while unmodified feature-list methods still unwrapped.
An arbitrary `create_cursor` method retained exact wrapper identity and
explicit instance restoration. Missing and non-string method names raised the
native `AttributeError`/`TypeError` boundary without mutation.

The shared `_is_database_failure` predicate was independently exercised in
both a fresh-import probe with Django's private symbol removed and a runtime
`None` patch; the public helper remained importable, returned `True`, and
installed the exact wrapper. This confirms graceful degradation when Django
removes or relocates `_DatabaseFailure`; the unwrap patch itself continues to
fail loudly unless its documented dependency opt-out is used.

The package's app-load lifecycle was also checked: the unwrap backstop is
installed by `DjangoStrawberryFrameworkConfig.ready()` after `django.setup()`,
which is the documented requirement for the automatic teardown protection.
No correctness, feature-list symmetry, arbitrary-name, identity/restoration,
foreign-`.wrapped`, private-symbol, or connection-lifecycle finding remains.

