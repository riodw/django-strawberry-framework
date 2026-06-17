# Review: `django_strawberry_framework/optimizer/hints.py`

Status: verified

## DRY analysis

- None — the file is already the single owner of the hint-shape contract. `hint_is_skip` (`hints.py::hint_is_skip`) exists precisely so the two `is SKIP or .skip` call sites (`optimizer/walker.py::_apply_hint` #"if hint_is_skip(hint)", `walker.py` #"hint_is_skip(hints_map.get(relation_field_name))", `optimizer/extension.py` #"if hint_is_skip(hints.get(field_name))") never re-derive the skip dispatch, and the four conflict-rejection blocks in `__post_init__` are heterogeneous (different flag tuples, different messages) — folding them through a shared loop would obscure the distinct error strings without removing real duplication. The `force_select` / `force_prefetch` flag pair plus `prefetch_obj` are the dataclass's single source of truth, consumed by name in the walker. No consolidation candidate.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `hint_is_skip` (`hints.py::hint_is_skip`) centralises the `hint is OptimizerHint.SKIP or hint.skip` dispatch so the walker (two sites) and the schema audit in `extension.py` share one shape rather than open-coding it; the factory classmethods (`select_related` / `prefetch_related` / `prefetch`) funnel all construction through the single `__post_init__`-validated `cls(...)` path, so the conflict gate runs on every shape including direct construction.
- **Duplication risk in the current file.** The four `if ...: raise ConfigurationError(...)` blocks in `__post_init__` (`hints.py::OptimizerHint.__post_init__`) are intentional sibling design, not near-copies: each guards a distinct flag combination and emits a distinct, actionable message naming the offending factory pair. Collapsing them would trade clarity for a false DRY win.

### Other positives

- **Construction-time rejection is the load-bearing contract.** `__post_init__` rejects every combination beyond the four documented shapes at `OptimizerHint(...)` time, so a malformed hint surfaces at `Meta.optimizer_hints` build time, not query time. The walker's priority order in `_apply_hint` is therefore documentation of dispatch sequence, not collision arbitration — the docstring at `hints.py::OptimizerHint.__post_init__` and the mirroring docstring at `walker.py::_apply_hint` both state this explicitly and agree.
- **Frozen dataclass + sentinel discipline.** `@dataclass(frozen=True)` gives value equality and immutability for free; `SKIP` is declared as `ClassVar[OptimizerHint]` so the dataclass decorator ignores it, then assigned `OptimizerHint(skip=True)` after the class body with a justified `# type: ignore[misc]`. Both `is`-identity (sentinel stability) and `==`-equality (`OptimizerHint(skip=True) == OptimizerHint.SKIP`) paths are pinned in `tests/optimizer/test_hints.py`; immutability is pinned (`test_skip_sentinel_cannot_be_mutated`).
- **Runtime `Prefetch` import is correct and documented.** `from django.db.models import Prefetch` is imported at runtime (not under `TYPE_CHECKING`) because `__post_init__` runs `isinstance(self.prefetch_obj, Prefetch)`; the comment block at `hints.py` #"is imported at runtime" explains why the `from __future__ import annotations` string-deferral of the annotation does not cover the load-bearing runtime check. No circular-import risk: the only first-party import is `..exceptions.ConfigurationError`, a leaf module.
- **`hint_is_skip` "never raises" contract is honoured and tested.** The `None` short-circuit, the `is OptimizerHint.SKIP` fast path, and the defensive `getattr(hint, "skip", False)` fallback for unexpected shapes are each pinned: `tests/optimizer/test_extension.py::test_hint_is_skip_handles_sentinel_record_and_unknown_shapes` asserts `None → False`, `SKIP → True`, `OptimizerHint(skip=True) → True`, `select_related() → False`, and `object() → False`. The `object()` case exercises the bare `getattr` fallback, so the schema audit's never-raise guarantee is covered.
- **Public-API back-compat intact.** `OptimizerHint` is re-exported from the package root (`django_strawberry_framework/__init__.py` #"from .optimizer.hints import OptimizerHint", listed in `__all__`); the four shapes documented in `docs/GLOSSARY.md` (`## OptimizerHint`, lines 906-930) match the implementation exactly, including the verbatim conflict-combination list. `select_related`/`prefetch_related`/`prefetch` semantics align with `walker.py::_apply_hint` dispatch (force_select rejects many-side relations with a redirecting message; force_select downgrades to `_plan_prefetch_relation` when the target has a custom `get_queryset`; `prefetch(obj)` is a leaf that stops walking and flips `plan.cacheable = False`).
- **No changes since baseline.** `git log --oneline 14910230..HEAD -- …/hints.py` empty; `git diff HEAD -- …/hints.py` empty — confirms the change-context prediction that spec-035 did not touch this file.

### Summary

`hints.py` is a small, mature, fully-tested public-API module that owns the `OptimizerHint` value type and the `hint_is_skip` dispatch helper. It is unchanged since the cycle baseline (empty log and diff), every branch of `__post_init__` and `hint_is_skip` is pinned across `tests/optimizer/test_hints.py` and `tests/optimizer/test_extension.py`, the factory/sentinel/runtime-import patterns are correct and documented, and `docs/GLOSSARY.md` / `docs/TREE.md` describe it accurately. No High, Medium, or Low findings and no DRY opportunity. Lands as a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 270 files left unchanged (only the pre-existing COM812-vs-formatter config warning).
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- No High/Medium/Low findings; DRY analysis is a single justified `None` bullet.
- No GLOSSARY-only fix in scope — `docs/GLOSSARY.md` `## OptimizerHint` (906-930) and `## Meta.optimizer_hints` (799-822) already match the implementation verbatim, including the conflict-combination list and the four supported modes; `docs/TREE.md` lines 219/292 accurate.
- Baseline HEAD; `git log 14910230..HEAD` and `git diff HEAD` for the target both empty. Unrelated concurrent-dirty files ignored per AGENTS.md #33.
- Branch coverage confirmed: all four `__post_init__` conflict raises pinned in `tests/optimizer/test_hints.py` (`test_skip_with_force_select_raises`, `test_skip_with_force_prefetch_raises`, `test_skip_with_prefetch_obj_raises`, `test_force_select_with_force_prefetch_raises`, `test_prefetch_obj_with_force_select_raises`, `test_prefetch_obj_with_force_prefetch_raises`, `test_prefetch_obj_rejects_non_prefetch_value`); `hint_is_skip`'s three branches incl. the `object()` `getattr` fallback in `tests/optimizer/test_extension.py::test_hint_is_skip_handles_sentinel_record_and_unknown_shapes`.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring defects. The module docstring (consumer-surface example), the `__post_init__` "construction-time rejection is the load-bearing contract" docstring, the runtime-`Prefetch`-import comment block, and the `SKIP` sentinel/`# type: ignore[misc]` comment all accurately describe current behavior and agree with the mirroring `walker.py::_apply_hint` docstring. No stale TODOs (shadow overview: 0 TODO comments). No source edit.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source change occurred (empty diff). AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_10.md` (silent on changelog edits for review cycles) both apply.

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit cycle (shape #5), terminal-verify. `git diff HEAD -- django_strawberry_framework/optimizer/hints.py` empty; `git log 14910230..HEAD -- …/hints.py` empty — confirms the file is unchanged since the cycle baseline, matching the artifact's prediction that spec-035 did not touch it. High/Medium/Low all `None`; nothing to address or reject.

Independently re-derived the public-API and dispatch claims against source (`hints.py`) and the shadow overview (control flow only; line numbers non-canonical):

- **Public-API back-compat.** `OptimizerHint` is a `@dataclass(frozen=True)` with the four-field shape (`force_select`/`force_prefetch`/`prefetch_obj`/`skip`, all defaulted) plus `SKIP` ClassVar sentinel and the three factory classmethods. Re-exported from `__init__.py` and in `__all__` (per Worker 1; consistent with the GLOSSARY `**Status:** shipped (0.0.3)` marker). No signature narrowing beyond the deliberate `prefetch(obj: Prefetch)` type (already pinned by a Medium-fix test from a prior cycle). Shape is back-compat-sound.
- **`__post_init__` conflict rejection covers the documented invalid combinations.** Four `if ... raise ConfigurationError` branches map 1:1 onto the GLOSSARY `## OptimizerHint` (906-930) verbatim list: (1) `skip` + any of the three other flags; (2) `force_select and force_prefetch`; (3) `prefetch_obj` not a `Prefetch` instance; (4) `prefetch_obj` set with `force_select`/`force_prefetch`. Each is test-pinned in `tests/optimizer/test_hints.py`: branch (1) by `test_skip_with_force_select_raises` / `_with_force_prefetch_raises` / `_with_prefetch_obj_raises` (each `match="skip=True"`), branch (2) by `test_force_select_with_force_prefetch_raises` (`match="force_select and force_prefetch"`), branch (3) by `test_prefetch_obj_rejects_non_prefetch_value` (`match="Prefetch"`), branch (4) by `test_prefetch_obj_with_force_select_raises` / `_with_force_prefetch_raises` (`match="prefetch_obj"`). Sentinel immutability pinned by `test_skip_sentinel_cannot_be_mutated`. Every conflict the walker's priority order would have arbitrated is rejected here at construction time, as the docstring states.
- **`hint_is_skip` dispatch incl. defensive fallback is correct.** Three branches: `None → False` short-circuit, `is OptimizerHint.SKIP → True` identity fast path, `bool(getattr(hint, "skip", False))` defensive fallback. All pinned by `tests/optimizer/test_extension.py::test_hint_is_skip_handles_sentinel_record_and_unknown_shapes` (asserts `None→False`, `SKIP→True`, `OptimizerHint(skip=True)→True`, `select_related()→False`, `object()→False`). The `object()` case exercises the bare `getattr` fallback, pinning the schema audit's "never raises" contract.

### DRY findings disposition
Single justified `None` bullet accepted. `hint_is_skip` is the existing consolidation point for the `is SKIP or .skip` dispatch shared by the two walker sites and `extension.py`; the four `__post_init__` raises are heterogeneous sibling guards (distinct flag tuples, distinct actionable messages) whose fusion would obscure the error strings for no real saving. No consolidation candidate. Concur.

### Temp test verification
- None used — the artifact's branch-coverage claims were verifiable by grepping the named tests at their cited paths and re-reading source/test bodies; no behavioral suspicion required a temp test.
- Disposition: n/a.

### Sibling-cycle attribution
The shape #5 diff stat over owned paths is non-empty: `management/commands/_imports.py`, `export_schema.py`, `inspect_django_type.py`, and `tests/management/test_imports.py`. These hunks attribute to the CLOSED sibling cycle `rev-management__commands.md` (Status: verified, `[x]` at review-0_0_10.md:88-90 for the file + folder passes) — the DRY `import_or_command_error` hoist. Not a rejection trigger. This file's own diff is empty, so the "Files touched: None" claim holds.

### Validation
- `git diff -- CHANGELOG.md` empty → "Not warranted" disposition honoured. Disposition cites BOTH `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence — both required citations present. Internal-only framing is honest: zero source edit, so no public-API surface changed this cycle.
- `uv run ruff format --check …/hints.py` → "1 file already formatted" (only the pre-existing COM812-vs-formatter config warning). `uv run ruff check …/hints.py` → "All checks passed!".
- Shape #5 preamble: every Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` Confirmed. No GLOSSARY-only fix in scope (disqualifying if present) — none; GLOSSARY/TREE already match the implementation.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box at `docs/review/review-0_0_10.md`.

---

## Iteration log

(none)
