# Review feedback — Python/code changes

Scope: reviewed only Python/code changes in the current local history, focused on `django_strawberry_framework/registry.py` and the related tests.

## Prior findings — status

The Python issues from the previous pass are resolved:

- **H1 (`unregister()` mutating finalized registry)** — fixed. `TypeRegistry.unregister()` now calls `_check_mutable()` before mutating state, and `tests/test_registry.py::test_unregister_raises_after_finalize` pins the finalized-registry guard.
- **H2 (`set_primary()` public API)** — fixed. `TypeRegistry.set_primary()` has been removed, and the walker tests now declare primaries through `registry.register(..., primary=True)` via the synthetic `_register_type_definition(...)` helper.

## Remaining finding

### L1. Stale test docstring still references removed `set_primary()`

Reference: [tests/test_registry.py:1192](../tests/test_registry.py:1192).

`test_unregister_keeps_siblings_intact_in_multi_type_case` still says the caller is expected to "`set_primary` a sibling if needed." That helper was removed in the latest Python fix, and `registry.py` now correctly describes the recovery path as a fresh registration cycle. This is not a runtime bug, but it leaves misleading guidance in the test suite.

## Verification

- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed.
- `git diff --check` passed.
- `uv run pytest` passed: 688 passed, 3 skipped, 100.00% package coverage.
