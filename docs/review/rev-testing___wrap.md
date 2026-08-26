# Review: `django_strawberry_framework/testing/_wrap.py`

Status: verified

## Understanding

`django_strawberry_framework/testing/_wrap.py` provides `safe_wrap_connection_method`, the consumer-facing wrap-time half of the package's defense-in-depth against Django Trac #37064 (`AttributeError: 'function' object has no attribute 'wrapped'` during `tearDownClass` unwrap loops).

### Architectural Responsibilities and Invariants:

1. **Wrap-Time Defense-in-Depth (Trac #37064)**:
   - Consumers or third-party libraries that need to monkey-patch a Django database connection method (e.g. `cursor`, `chunked_cursor`, `create_cursor`) between `setUpClass` and `tearDownClass` call `safe_wrap_connection_method(connection, method_name, wrapper)`.
   - Checks if Django's `_DatabaseFailure` wrapper is already installed via `django_strawberry_framework._django_patches._is_database_failure`. If present, declines to wrap, leaves the connection method untouched, and returns `False`.
   - If `_DatabaseFailure` is not in place (or if the private symbol is unavailable due to upstream Django drift), installs `wrapper` via `setattr(connection, method_name, wrapper)` and returns `True`.

2. **Wrap-Time Type Validation**:
   - Enforces `callable(wrapper)` up front, raising `TypeError("safe_wrap_connection_method() received a non-callable wrapper")` before inspecting or modifying `connection`.
   - Protects against common typos (e.g., passing `connection.cursor()` result instead of a callable) so errors surface immediately at the call site rather than deep inside Django's ORM machinery.

3. **Ecosystem & Lifecycle Coordination**:
   - Mirrors the wrap-time check pattern established in `django-debug-toolbar` (`debug_toolbar.panels.sql.tracking.wrap_cursor`).
   - Composes symmetrically with the package's unwrap-time patch (`django_strawberry_framework._django_patches._patched_remove_databases_failures`) installed automatically at `AppConfig.ready()`.

## Verification

1. **Static and Structural Audit**:
   - Audited all 148 lines of `django_strawberry_framework/testing/_wrap.py`.
   - Traced callers and re-exports in `django_strawberry_framework/testing/__init__.py` and integration with `django_strawberry_framework/_django_patches.py`.

2. **Existing Test Suite Audit**:
   - `tests/testing/test_wrap.py`: 7 existing tests covering happy-path installation, declining on `_DatabaseFailure`, symbol drift resilience, arbitrary method names, end-to-end defense-in-depth composition with unwrap-time patch, non-callable `TypeError` guards, and hostile `__repr__` boundary safety.

3. **Scratch Experiments**:
   - Authored and ran `docs/review/temp-tests/_wrap/test_scratch.py` probing missing method attribute handling and callable class instances (`__call__`). Both passed cleanly.

4. **Permanent Tests & Test Suite Run**:
   - Added `test_safe_wrap_connection_method_accepts_callable_class_instance` and `test_safe_wrap_connection_method_raises_attribute_error_on_missing_method` to `tests/testing/test_wrap.py`.
   - `uv run pytest tests/testing/test_wrap.py --no-cov`: 9 passed.
   - Verified 100% statement coverage on `_wrap.py`: `uv run pytest tests/testing/test_wrap.py -o "addopts=" --cov=django_strawberry_framework.testing._wrap --cov-report=term-missing` (12/12 statements, 100%).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/testing/_wrap.py` provides a clean, robust, and safe connection-method wrapping utility that prevents clobbering Django's `_DatabaseFailure` wrappers. The target has zero defects, achieves 100% statement coverage, and is fully verified.

## Implementation (Worker 1)

- **changed files and why each was necessary:**
  - `tests/testing/test_wrap.py`: Added permanent tests pinning callable class instance support (`__call__`) and `AttributeError` on non-existent connection methods.
  - `django_strawberry_framework/testing/_wrap.py`: Zero production code diff; existing implementation is correct and robust.
- **permanent tests and the behavior they pin:**
  - `test_safe_wrap_connection_method_accepts_callable_class_instance`: Pins that any object implementing `__call__` is accepted by the callable check and correctly installed.
  - `test_safe_wrap_connection_method_raises_attribute_error_on_missing_method`: Pins that attempting to wrap a non-existent method raises `AttributeError`.
- **scratch or focused verification and its result:**
  - Authored and ran `docs/review/temp-tests/_wrap/test_scratch.py` (2 passed).
  - Executed `uv run pytest tests/testing/test_wrap.py --no-cov` (9 passed).
  - Verified 100% statement coverage (12/12 statements) on `_wrap.py`.
- **formatter and linter results:**
  - Executed `uv run ruff format .` and `uv run ruff check --fix .` (clean, 0 errors).
- **evidence for any rejected finding:**
  - No findings were rejected; implementation is robust and fully verified.
- **whether the completed behavior merits a changelog entry:**
  - No (test additions only; zero production code diff).

## Independent verification (Worker 2)

### 1. Scoped Diff & Zero-Edit Confirmation
- Confirmed `django_strawberry_framework/testing/_wrap.py` has 0 diff against cycle baseline HEAD (`12779c99`).
- Production code remains completely untouched and verified clean.

### 2. Behavioral Re-tracing & Architectural Invariants
- `safe_wrap_connection_method(connection, method_name, wrapper)`:
  - **Early Validation**: Verified `not callable(wrapper)` check raises `TypeError("safe_wrap_connection_method() received a non-callable wrapper")` before querying `connection` attributes.
  - **Connection Attribute Resolution**: Verified `current = getattr(connection, method_name)` properly accesses existing methods and raises standard `AttributeError` for non-existent methods without modifying `connection`.
  - **Wrap-Time Defense against Trac #37064**: Verified `_is_database_failure(current)` check correctly detects Django's `_DatabaseFailure` wrapper (or degrades gracefully if Django private symbols drift) and returns `False` while leaving `connection` untouched.
  - **Wrapper Installation**: Verified `setattr(connection, method_name, wrapper)` correctly installs wrapper and returns `True` when safe.

### 3. Verification Execution
- Executed focused test suite:
  - `uv run pytest tests/testing/test_wrap.py --no-cov`: 9 passed.
  - `uv run pytest tests/test_django_patches.py --no-cov`: 21 passed.
- Linters and formatting:
  - `uv run ruff check django_strawberry_framework/testing/_wrap.py tests/testing/test_wrap.py`: Clean (0 errors).
  - `uv run ruff format --check django_strawberry_framework/testing/_wrap.py tests/testing/test_wrap.py`: Clean (2 files formatted).

### 4. Findings & Disposition
- All behaviors verified sound; no open findings or defects.
- Verification complete.

