# Review: `django_strawberry_framework/utils/imports.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/imports.py` is the single centralized owner for all dynamic, optional, and guarded import patterns across the framework:

1. **`_plain_text(value: Any) -> Any`**:
   - Defensive normalization helper for string subclasses (e.g. hostile subclasses with overriding `__hash__` or `__str__` implementations).
   - Fast-paths native `str` and non-`str` types; delegates to `str.__str__(value)` to extract the pure string buffer safely before handing names or hints to Python import machinery.

2. **`import_attr_if_importable(module_path: str, attr_name: str) -> Any | None`**:
   - Best-effort import helper. Attempts `importlib.import_module(module_path)`.
   - On `ImportError` (such as uninstalled optional dependencies or a `sys.modules[path] = None` test isolation sentinel), it catches the exception and returns `None` so the caller gracefully degrades.
   - On successful import, calls `getattr(module, attr_name)` with *no default*, failing loud (`AttributeError`) if an importable module lacks the expected symbol (a code defect rather than an absent optional package).
   - Callers: `registry.py::_clear_if_importable` (subsystem co-clears), `types/converters.py` (PostgreSQL fields), `optimizer/nested_planner.py` (PostgreSQL `BTreeIndex`), and `utils/inputs.py::_safe_import`.

3. **`loaded_attr(module_path: str, attr_name: str) -> Any | None`**:
   - Opt-in-preserving loaded-only lookup helper. Probes `sys.modules.get(module_path)`.
   - Never triggers an import if the module is absent or set to `None` in `sys.modules` (returns `None`).
   - If the module is already loaded, accesses `getattr(module, attr_name)` without default, failing loud (`AttributeError`) if the attribute is missing.
   - Callers: `types/finalizer.py` (lazy auth binding without forcing `auth.mutations` import unless previously imported).

4. **`import_attr(module_path: str, attr_name: str) -> Any`**:
   - Strict import helper for internal deferred-import seams (e.g. cycle-breaking resolver lookups).
   - Eagerly imports `module_path` and returns `getattr(module, attr_name)`. Any `ImportError` or `AttributeError` propagates immediately without masking.
   - Callers: `mutations/sets.py` (dynamic dispatch to generated sync/async resolvers).

5. **`require_optional_module(module_name: str, *, install_hint: str) -> Any`**:
   - Raising optional-dependency primitive (spec-041).
   - Eagerly imports `module_name` via `importlib.import_module`.
   - On `ImportError`, wraps and raises a new `ImportError(install_hint)` with the original exception chained via `from exc`.
   - Non-memoized so test suites can evict `sys.modules` entries and test missing dependency paths reliably in-process.
   - Callers: `routers.py` (`require_channels`), `auth/sessions.py`, `rest_framework/__init__.py` (`require_drf`), `middleware/debug_toolbar.py` (`require_debug_toolbar`), and `keyset.py` (`cryptography` AEAD).

## Verification

1. **Call-site and Guard Tracing**:
   - Traced all import points across `registry.py`, `types/converters.py`, `optimizer/nested_planner.py`, `utils/inputs.py`, `types/finalizer.py`, `mutations/sets.py`, `routers.py`, `auth/sessions.py`, `rest_framework/__init__.py`, `middleware/debug_toolbar.py`, and `keyset.py`. Confirmed consistent delegation and no ad-hoc `importlib.import_module` bypassing.
2. **Existing Test Review**:
   - Reviewed `tests/utils/test_imports.py` (9 existing tests) and soft-dependency integration suites in `tests/_soft_dependency.py`, `tests/rest_framework/test_soft_dependency.py`, `tests/test_routers.py`, and `tests/middleware/test_debug_toolbar.py`.
3. **Scratch Experiments**:
   - Created `docs/review/temp-tests/utils_imports/test_scratch.py` probing edge cases: `_plain_text` behavior with non-string types and hostile subclasses, `import_attr` strict propagation, `loaded_attr` lookup and `AttributeError` on missing attributes, `import_attr_if_importable` returning `None` when attribute value is `None` or module absent, and `require_optional_module` exception chaining. Executed via `uv run pytest docs/review/temp-tests/utils_imports/test_scratch.py --no-cov` (5 passed).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/utils/imports.py` provides clean, unified, and resilient primitives for optional, loaded-only, best-effort, and strict import patterns. Hostile string subclasses are properly sanitized, error chaining preserves root causes, and failure semantics (failing loud on missing attributes while degrading on missing optional modules) are maintained across the package.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/utils/test_imports.py`: Added direct unit tests covering `import_attr` success and failure propagation (`ImportError` on missing module, `AttributeError` on missing attribute), `loaded_attr` success on loaded modules and `AttributeError` on missing attributes, `loaded_attr` returning `None` on `sys.modules` `None` sentinels, and `import_attr_if_importable` returning `None` on uninstalled modules.
  - `django_strawberry_framework/utils/imports.py`: Unmodified (implementation is sound and fully satisfies its contract).
- **Permanent tests and pinned behavior:**
  - `tests/utils/test_imports.py::test_loaded_attr_returns_none_when_module_is_none_sentinel`: Pins `loaded_attr` handling of `sys.modules[path] = None`.
  - `tests/utils/test_imports.py::test_loaded_attr_returns_attribute_when_module_is_already_loaded`: Pins `loaded_attr` attribute extraction on loaded modules.
  - `tests/utils/test_imports.py::test_loaded_attr_raises_attribute_error_when_loaded_module_lacks_attr`: Pins `loaded_attr` loud failure on missing attributes.
  - `tests/utils/test_imports.py::test_import_attr_returns_attribute_on_success`: Pins `import_attr` strict import and attribute retrieval.
  - `tests/utils/test_imports.py::test_import_attr_raises_import_error_on_unreachable_module`: Pins `import_attr` propagation of `ImportError`.
  - `tests/utils/test_imports.py::test_import_attr_raises_attribute_error_on_missing_attribute`: Pins `import_attr` propagation of `AttributeError`.
  - `tests/utils/test_imports.py::test_import_attr_if_importable_returns_none_on_absent_module`: Pins `import_attr_if_importable` degrading on absent modules.
- **Scratch or focused verification:**
  - Scratch suite: `docs/review/temp-tests/utils_imports/test_scratch.py` (5 passed).
  - Focused test suite: `uv run pytest tests/utils/test_imports.py --no-cov` (16 passed in 1.71s).
  - Consumer integration tests: `uv run pytest tests/rest_framework/test_soft_dependency.py tests/test_routers.py tests/middleware/test_debug_toolbar.py --no-cov` (204 passed in 8.46s).
- **Formatter and linter results:**
  - `uv run ruff format .`: formatted 1 file (`tests/utils/test_imports.py`), 430 files clean.
  - `uv run ruff check --fix .`: all checks passed.
- **Evidence for rejected findings:** None.
- **Changelog entry:** No — target implementation is unchanged and internal/external behavior contracts are preserved.

## Independent verification (Worker 2)

- **Baseline and Scoped Diff:**
  - Cycle baseline: `HEAD` (`12779c99`).
  - Verified `git diff 12779c99 -- django_strawberry_framework/utils/imports.py` is empty (zero-edit).
- **Behavior & Contract Tracing:**
  - `_plain_text`: Fast-paths native `str` and non-string types; invokes `str.__str__(value)` on custom subclasses to reliably extract pure string buffers without triggering hostile `__hash__` or overridden methods.
  - `import_attr_if_importable`: Catches `ImportError` (e.g. uninstalled modules or `sys.modules` `None` sentinels) returning `None`, while letting missing symbol accesses fail loud with `AttributeError` (matching caller expectations in PostgreSQL converters, query planning, and registry co-clearing).
  - `loaded_attr`: Safely probes `sys.modules.get` without importing absent modules or `None` sentinels, preserving opt-in lazy loading semantics across auth bindings, and fails loud with `AttributeError` if a loaded module lacks the requested symbol.
  - `import_attr`: Performs strict dynamic import and `getattr`, propagating all `ImportError` and `AttributeError` exceptions immediately for internal deferred seams (such as generated mutation sets).
  - `require_optional_module`: Raises explicit `ImportError` carrying feature `install_hint` with the original `ImportError` chained via `from exc`; avoids memoization to support in-process test isolation and eviction.
- **Verification Tests & Experiments:**
  - Focused test suite: `uv run pytest tests/utils/test_imports.py --no-cov` (16 passed in 1.61s).
  - Consumer integration tests: `uv run pytest tests/test_routers.py tests/rest_framework/test_soft_dependency.py tests/middleware/test_debug_toolbar.py --no-cov` (204 passed in 8.36s).
  - Independent scratch test suite: `uv run pytest docs/review/temp-tests/utils_imports/test_independent_scratch.py --no-cov` (5 passed in 1.61s), exercising hostile subclass inputs, strict propagation vs best-effort degradation, loaded-only lookups, and exception chaining.
- **Findings & Disposition:**
  - Zero open findings. All behaviors are complete, tested, and contractually verified.

