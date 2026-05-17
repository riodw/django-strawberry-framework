# Review feedback — Python changes in `df13b64403d07e5587cfce902ac2eef0c31c71f1`

Scope: reviewed every `.py` file changed by `df13b64403d07e5587cfce902ac2eef0c31c71f1` against its parent:

- `django_strawberry_framework/__init__.py`
- `django_strawberry_framework/scalars.py`
- `django_strawberry_framework/types/converters.py`
- `examples/fakeshop/apps/products/schema.py`
- `examples/fakeshop/tests/test_schema.py`
- `tests/base/test_init.py`
- `tests/test_scalars.py`
- `tests/types/test_converters.py`

## Blockers

None.

## High-severity issues

None.

## Medium-severity issues

None.

## Low-severity issues

### L1. `__all__` is no longer pinned as the exact public tuple

File: `tests/base/test_init.py:35`

`test_public_api_surface_is_pinned()` converts `django_strawberry_framework.__all__` to a `set` before comparing. That proves membership, but it does not pin the spec's exact tuple shape, order, or duplicate-free tuple contract. The implementation currently has the right tuple in `django_strawberry_framework/__init__.py`, but the test would still pass if a future edit reordered it, changed it to a list, or duplicated an export.

Recommended change: compare `django_strawberry_framework.__all__` directly to the expected tuple:

```python
assert django_strawberry_framework.__all__ == (
    "BigInt",
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "__version__",
    "auto",
    "finalize_django_types",
)
```

## What looks solid

- `BigInt` parser and serializer are strict on both input and output, including bool rejection before the `int` branch.
- The import-time Strawberry deprecation suppression is tightly scoped to scalar definition and is covered by a subprocess import test.
- `ArrayField` / `HStoreField` soft imports are guarded by module-level sentinels, so non-postgres environments can still import the package.
- The converter tests exercise schema execution, not only direct helper calls, for the new public mapping behavior.
- Full default validation passed: `uv run pytest` ended with `629 passed, 3 skipped, 3 warnings` and package coverage at `100.00%`.

## Notes

- A focused partial run of `uv run pytest tests/test_scalars.py tests/types/test_converters.py` had all selected tests pass, but exited nonzero because `pytest.ini` auto-enables coverage and partial runs cannot meet the package-wide `fail_under = 100`. The full default suite above is the meaningful CI signal.
- The three full-suite warnings are the pre-existing shard-setting warning and two pre-existing synthetic-model re-registration warnings; I did not treat them as findings for this commit.
