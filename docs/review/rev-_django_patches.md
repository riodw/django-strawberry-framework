# Review: `django_strawberry_framework/_django_patches.py`

Status: verified

## DRY analysis

- None — the file's four functions each encapsulate a single distinct concern (the `_DatabaseFailure` isinstance test in `_is_database_failure`, the classmethod-descriptor unwrap in `_patch_is_installed`, the upstream-mirroring loop in `_patched_remove_databases_failures`, and the install/log orchestration in `apply`); the `isinstance(method, _DatabaseFailure)` guard is already factored into `_is_database_failure` and reused as the single call site (`_django_patches.py:178`), and the only literal-ish near-duplication (the wrap-time half of the same pattern) lives in `testing/_wrap.py::safe_wrap_connection_method`, which is a deliberate sibling at a different lifecycle site (wrap vs unwrap) and a different object surface (`connections[alias]` instance attribute vs `SimpleTestCase` classmethod descriptor) — collapsing them would couple two unrelated install protocols, so they are correctly separate.
- Forward to project pass (`rev-django_strawberry_framework.md`), not a local defect — the `apply()` scaffold (toggle gate via `upstream_patches_enabled()`, the `_missing_symbol_logged` once-only notice, the `_patch_is_installed()` re-entrancy short-circuit, and the import-time `ImportError` capture of the upstream private symbol) is near-identical across `_cross_web_patches.py`, `_strawberry_patches.py`, and `_django_patches.py`. Per the 0.0.11 plan and this file's spawn brief, the sibling-DRY consolidation candidate is being collected at the project-level pass; restated here so the project pass sees all three patch modules flag it. No stronger local reason to act now — each module's guarded body and patched target differ, so only the orchestration skeleton is shared.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The single isinstance guard is centralized in `_is_database_failure` (`_django_patches.py:134-136`) and consumed once at the unwrap site (`_django_patches.py:178`); `apply` reuses `_patch_is_installed` (`_django_patches.py:182-194`) rather than re-deriving the `__func__` identity check inline. The module re-exports the canonical package logger via `from . import logger` (`_django_patches.py:111`) and gates on the shared `upstream_patches_enabled()` (`_django_patches.py:112`), matching the package-wide patch-module convention shared with `_cross_web_patches.py` / `_strawberry_patches.py`.
- **New helpers considered.** Considered extracting a shared wrap/unwrap helper across `_patched_remove_databases_failures` and `testing/_wrap.py::safe_wrap_connection_method`; rejected because they operate at opposite lifecycle sites (unwrap-time recovery vs wrap-time prevention) on different object surfaces (Django classmethod descriptor vs `connections[alias]` instance method). The module docstring (`_django_patches.py:64-95`) explicitly frames these as two halves of one defense-in-depth pattern, not a single extractable mechanism. The cross-module `apply()` scaffold was also considered and forwarded to the project pass (see DRY analysis) rather than extracted locally.
- **Duplication risk in the current file.** The patched loop (`_django_patches.py:172-179`) is a near-verbatim copy of Django's upstream `SimpleTestCase._remove_databases_failures`. This is intentional and necessary: the patch must mirror upstream exactly except for the inserted guard, so any divergence would be a bug, not desirable DRY. Verified verbatim against the installed Django 6.0.5 via `inspect.getsource(SimpleTestCase._remove_databases_failures.__func__)`: the only difference is the `if _is_database_failure(method):` guard wrapping the existing `setattr(connection, name, method.wrapped)`.

### Other positives

- **Faithful, minimal patch.** Confirmed against Django 6.0.5's actual `_remove_databases_failures` source: the body is identical apart from the added isinstance guard. The patch is strictly defensive — when the wrapper is still in place it unwraps exactly as upstream; when replaced it declines to touch the foreign method instead of crashing. The docstring's two-bullet behavior contract (`_django_patches.py:152-161`) matches the code precisely.
- **Idempotent, self-healing install.** `apply` short-circuits via `_patch_is_installed` when already installed and re-installs after a third-party revert. `_patch_is_installed` correctly reads `SimpleTestCase.__dict__` (not attribute access, which would resolve the bound descriptor) and guards the `installed is None` case (`_django_patches.py:191-194`), covering the future-Django-relocation scenario.
- **Graceful private-symbol degradation.** The `_DatabaseFailure` import is wrapped in `try/except ImportError` with `# pragma: no cover` justified by monkeypatch-driven tests; `apply` no-ops with a single INFO log gated by the `_missing_symbol_logged` module sentinel (`_django_patches.py:227-235`) so repeated `ready()` invocations don't spam the logger.
- **Correct privacy boundary.** The module is private (leading underscore) and consumers never import it; only `apply` is unprefixed so the regression tests and `apps.ready()` can call it. The docstring's "Surface visibility" section (`_django_patches.py:97-105`) documents this intentionally.
- **GLOSSARY in sync.** The `Django Trac #37064 hardening` and `safe_wrap_connection_method` entries (`docs/GLOSSARY.md:1149-1166` and the cross-refs at `:52`, `:133`, `:145`, `:168`) accurately describe the patch site, the isinstance guard, the auto-application at `ready()`, and the wrap-time/unwrap-time pairing. The `apps.py` cross-reference (`docs/GLOSSARY.md:308`) matches the actual `ready()` body. No drift.

### Summary

A small, single-purpose defensive-patch module in excellent shape, unchanged since the 0.0.10 review (empty diff vs HEAD). The patch body is a verified-verbatim mirror of Django 6.0.5's `_remove_databases_failures` plus one centralized `_is_database_failure` guard, the install path is idempotent and self-healing, and the missing-symbol degradation is graceful and logged-once. No High, Medium, or Low findings. The only local DRY near-copy is the intentional, necessary upstream mirror; the wrap-time sibling in `testing/_wrap.py` is a correct separate concern; and the shared `apply()` scaffold across the three patch modules is forwarded to the project pass per the 0.0.11 plan rather than treated as a local defect.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 289 files left unchanged.
- `uv run ruff check --fix .` — All checks passed.

### Notes for Worker 3
No-findings file (template shape #1) combined with no-source-edit cycle (shape #5): all severities `None.`, no act-now DRY, zero edits to any tracked file. `git diff HEAD -- django_strawberry_framework/_django_patches.py` is empty — the file is byte-identical to the prior (0.0.10) review. The patch body was verified verbatim against the installed Django 6.0.5 upstream `SimpleTestCase._remove_databases_failures` (only diff: the centralized `_is_database_failure` guard before `setattr`). GLOSSARY entries (`Django Trac #37064 hardening`, `safe_wrap_connection_method`, the `apps.py` cross-ref) verified in sync — no GLOSSARY-only fix in scope. The one DRY-analysis bullet flagging the shared `apply()` scaffold is an explicit forward to `rev-django_strawberry_framework.md` (project pass), not an actionable local Low. No Lows to disposition.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits in scope — the module's comments and docstrings are accurate against the code (verified the behavior contract, privacy-boundary note, missing-symbol sentinel rationale, and defense-in-depth framing all match the implementation).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (empty diff vs HEAD), and AGENTS.md instructs not to touch `CHANGELOG.md` unless explicitly instructed; the active plan `docs/review/review-0_0_11.md` is silent on changelog edits for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No-findings (template shape #1) combined with no-source-edit cycle (shape #5). All High / Medium / Low are `None.`; independently confirmed genuine, not a lazy pass:
- **Verbatim-upstream mirror confirmed.** `inspect.getsource(SimpleTestCase._remove_databases_failures.__func__)` against the installed Django 6.0.5 is identical to `_patched_remove_databases_failures` (`_django_patches.py:172-179`) except for the inserted `if _is_database_failure(method):` guard before `setattr(connection, name, method.wrapped)`. The artifact's central claim holds byte-for-byte.
- **Guard centralized and single-call-site.** `_is_database_failure` (`:134-136`) folds the `_DatabaseFailure is not None` null-guard with the isinstance test; consumed once at `:178`. No re-derivation.
- **`_patch_is_installed` reads `__dict__`, not attribute access** (`:191`), correctly avoiding descriptor resolution, and guards `installed is None` (`:192-193`) for the future-Django-relocation case.
- **Every branch is test-pinned** in `tests/test_django_patches.py`: toggle gate → `test_apply_no_ops_when_toggle_disabled`; missing-symbol no-op → `test_apply_no_ops_when_database_failure_symbol_missing`; once-only log sentinel → `test_apply_logs_missing_symbol_notice_only_once`; re-entrancy short-circuit → `test_apply_is_idempotent`; revert/reinstall self-healing → `test_apply_reinstalls_when_class_attribute_reverted`; `installed is None` branch → `test_patch_is_installed_returns_false_when_attribute_absent_from_class_dict`; guard true/false paths → `test_patched_remove_databases_failures_unwraps_a_real_wrapper` / `_skips_non_wrapper_methods`; hierarchy inheritance → `_inherited_by_transaction_test_case` / `_test_case`; upstream-crash baseline → `test_unpatched_remove_databases_failures_crashes_on_non_wrapper`.

No real defect was missed that would force a source edit.

### DRY findings disposition
Two DRY-analysis bullets, both correct: (1) the `_is_database_failure` guard is already the single factored call site, and the wrap-time sibling `testing/_wrap.py::safe_wrap_connection_method` is a deliberate separate concern (wrap vs unwrap, instance attribute vs classmethod descriptor) — collapsing them would couple two unrelated install protocols. (2) The shared `apply()` scaffold across `_cross_web_patches.py` / `_strawberry_patches.py` / `_django_patches.py` is correctly **forwarded** to the project pass (`rev-django_strawberry_framework.md`) per the 0.0.11 plan, not resolved locally. Carry-forward confirmed appropriate.

### Temp test verification
None. No temp tests created — verification done via upstream-source comparison and read of the existing pinned regression tests.

### Shape #5 structural checks
- `git diff HEAD -- django_strawberry_framework/_django_patches.py` empty; target absent from `git diff --stat HEAD` over `django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` (empty stat).
- Each Worker 2 section opens with "Filled by Worker 1 per no-source-edit cycle pattern."
- No Lows to forward; no GLOSSARY-only fix in scope.
- Changelog "Not warranted" cites BOTH AGENTS.md and the active plan's silence — both present.
- `uv run ruff format --check` and `uv run ruff check` pass on the target.
- Remaining dirty working-tree paths (`docs/bug_hunt/`, `docs/dry/dry-0_0_11.md`, `docs/review/rev-_cross_web_patches.md`, `docs/review/review-0_0_11.md`) are per-cycle/regenerable scratchpad, not owned source — not a rejection trigger.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box for `_django_patches.py` in `docs/review/review-0_0_11.md`.
