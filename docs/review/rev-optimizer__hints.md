# Review: `django_strawberry_framework/optimizer/hints.py`

## High:

None.

## Medium:

### `OptimizerHint(force_select=True, force_prefetch=True)` is silently accepted

The dataclass accepts any combination of flags, but the walker consumes them with a strict priority order (`skip` first, then `prefetch_obj`, then `force_select`, then `force_prefetch`). A consumer who writes `OptimizerHint(force_select=True, force_prefetch=True)` — perhaps via a programmatic helper that forgot to make the flags exclusive — gets `select_related` applied silently, with no signal that their `force_prefetch` was ignored.

Recommended: add a `__post_init__` that raises `ConfigurationError` for any of the conflicting combinations:

- `skip=True` with any of `force_select` / `force_prefetch` / `prefetch_obj` truthy
- `force_select=True` with `force_prefetch=True`
- `force_select=True` with `prefetch_obj is not None`
- `force_prefetch=True` with `prefetch_obj is not None`

This is a frozen dataclass, so `__post_init__` should call `object.__setattr__` only if it wants to normalize — but in this case the right behavior is to *raise*, which works fine on a frozen dataclass. Add tests for each conflicting combination.

```django_strawberry_framework/optimizer/hints.py:50:53
force_select: bool = False
force_prefetch: bool = False
prefetch_obj: Any = field(default=None, repr=False)
skip: bool = False
```

## Low:

### `prefetch_obj: Any` could be `Prefetch | None`

Like `FieldMeta.related_model`, `prefetch_obj` is annotated `Any` but the documented value is a `django.db.models.Prefetch`. Tightening the annotation under `TYPE_CHECKING` (the file already uses `from __future__ import annotations`) gives consumers and tooling the right shape. Comment polish — defer.

```django_strawberry_framework/optimizer/hints.py:52:52
prefetch_obj: Any = field(default=None, repr=False)
```

### `SKIP` sentinel post-class assignment uses `# type: ignore[misc]`

The `ClassVar` declaration plus post-class assignment is the right pattern for a singleton sentinel that references the class itself, but the `# type: ignore[misc]` comment hides the fact that the dataclass decorator does not register `SKIP` as a regular field. A short comment explaining *why* the ignore is needed (dataclass would otherwise treat the assignment as a default-factory candidate) would help future maintainers. Comment polish — defer.

```django_strawberry_framework/optimizer/hints.py:88:89
# Sentinel instance — must be created after the class body.
OptimizerHint.SKIP = OptimizerHint(skip=True)  # type: ignore[misc]
```

## What looks solid

- Frozen dataclass with documented attributes and three factory classmethods covering the documented consumer API (`select_related()`, `prefetch_related()`, `prefetch(obj)`) plus the `SKIP` sentinel for the most common case.
- Module docstring shows the consumer-facing usage with a real `Meta.optimizer_hints` block, so the API is discoverable from the source file alone.
- `OptimizerHint.SKIP` is identity-comparable in the walker (`hint is OptimizerHint.SKIP or hint.skip`), so consumers who write `OptimizerHint(skip=True)` get the same behavior as the singleton — no footgun on the walker side.
- Re-exported from `__init__.py` so consumers write `from django_strawberry_framework import OptimizerHint`, keeping the import path short — DRF-shaped.
- File lives in the optimizer subpackage with no Django/Strawberry imports — no circular-import risk.

---

### Summary:

Compact, frozen, well-documented hint type with a sentinel pattern that survives identity comparison and a small factory API. The Medium item is a real footgun: conflicting flag combinations are silently accepted and the walker resolves them via priority order, hiding the consumer's mistake. Add `__post_init__` validation and pin each conflict with a test. Low items are typing/comment polish on `prefetch_obj` and the `# type: ignore[misc]` rationale.

---

### Worker 3 verification

- Medium fix: `__post_init__` rejects all four conflicting flag combinations with `ConfigurationError`. The factory classmethods (`select_related`, `prefetch_related`, `prefetch`) all produce single-flag instances, so they continue to work; the four documented shapes (`SKIP`, `select_related()`, `prefetch_related()`, `prefetch(obj)`) all pass through unchanged.
- Tests added (`tests/optimizer/test_hints.py::TestConflictingFlagsRejected`): six cases, one per rejected combination — `skip + force_select`, `skip + force_prefetch`, `skip + prefetch_obj`, `force_select + force_prefetch`, `prefetch_obj + force_select`, `prefetch_obj + force_prefetch`.
- Low fix 1: `prefetch_obj` annotation tightened from `Any` to `Prefetch | None`. The `Prefetch` import is gated behind `TYPE_CHECKING` with `# pragma: no cover`.
- Low fix 2: comment on the post-class `OptimizerHint.SKIP = ...` assignment now explains why the `# type: ignore[misc]` is necessary (dataclass decorator interaction with `ClassVar`).
- New runtime import: `from ..exceptions import ConfigurationError`. Per `exceptions.py`'s docstring, that module is designed to live at the bottom of the import graph and may be imported anywhere — no circular-import risk.
- Validation: `uv run ruff format` reformatted hints.py (cosmetic line-wrap inside one error message); `uv run ruff check` clean; `uv run pytest -q` -> 351 passed, 4 skipped, 100% coverage (gain of 6 tests in `tests/optimizer/test_hints.py`).
- CHANGELOG: not updated. The new validation rejects combinations that no documented consumer surface produces (the four factory shapes are all single-flag); AGENTS.md forbids changelog edits without explicit instruction.
- Scope: changes confined to `django_strawberry_framework/optimizer/hints.py` and `tests/optimizer/test_hints.py`.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.
