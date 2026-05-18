# Review feedback - Python diff 8cec18a3890d2b2c0a0e60acecd3e83501aaed27

Scope: reviewed only Python files changed by commit `8cec18a3890d2b2c0a0e60acecd3e83501aaed27`.

## High-Severity Findings

### H1. Full pytest fails the 100% coverage gate on the new origin-missing branch

References: `django_strawberry_framework/optimizer/extension.py:415`, `django_strawberry_framework/optimizer/extension.py:416`

The commit adds the explicit `if origin is None: return None` branch in `_resolve_model_from_return_type`, but no test covers it. Running `uv run pytest` now executes successfully at the behavior level (`682 passed, 3 skipped`) but fails the configured coverage gate with:

`django_strawberry_framework/optimizer/extension.py 239 statements, 1 missed, 99%, missing line 416`

Because `pyproject.toml` requires `fail_under = 100`, this is a CI blocker. Add a focused test for a schema type definition whose `get_type_by_name(...)` result has no `origin`, or mark the branch unreachable with a justified `pragma: no cover` if Strawberry can never produce that shape through supported execution.

## Medium-Severity Findings

### M1. The touched glossary checker still fails the active ruff rules

References: `scripts/check_spec_glossary.py:1`, `scripts/check_spec_glossary.py:267`

`uv run ruff check .` fails on the changed Python file:

- `D301` at the module docstring because it contains backslashes but is not a raw docstring.
- `D103` on public `main(...)` because it has no docstring.

Even though the diff only formats this script mechanically, the commit leaves a touched Python file that cannot pass the project lint command. Make the module docstring raw (`r"""..."""`) and add a concise `main` docstring, or explicitly exclude this script from those rules if that is the intended policy.

## Notes

The package/test behavior in the changed Python files otherwise looked coherent in the paths I checked. The focused changed-file test subset passed functionally (`361 passed, 3 skipped`) and `uv run ruff format --check .` plus `git diff --check ... -- '*.py'` passed.
