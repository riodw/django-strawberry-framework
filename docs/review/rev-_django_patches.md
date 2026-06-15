# Review: `django_strawberry_framework/_django_patches.py`

Status: verified

## DRY analysis

- None — the file's four functions each encapsulate a single distinct concern (the `_DatabaseFailure` isinstance test in `_is_database_failure`, the classmethod-descriptor unwrap in `_patch_is_installed`, the upstream-mirroring loop in `_patched_remove_databases_failures`, and the install/log orchestration in `apply`); the `isinstance(method, _DatabaseFailure)` guard is already factored into `_is_database_failure` and reused as the single call site (`_django_patches.py:173`), and the only literal-ish near-duplication (the wrap-time half of the same pattern) lives in `testing/_wrap.py::safe_wrap_connection_method`, which is a deliberate sibling at a different lifecycle site (wrap vs unwrap) and a different object surface (`connections[alias]` instance attribute vs `SimpleTestCase` classmethod descriptor) — collapsing them would couple two unrelated install protocols, so they are correctly separate.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The single isinstance guard is centralized in `_is_database_failure` (`_django_patches.py:129-131`) and consumed once at the unwrap site (`_django_patches.py:173`); `apply` reuses `_patch_is_installed` (`_django_patches.py:177-189`) rather than re-deriving the `__func__` identity check inline. The module re-exports the canonical package logger via `from . import logger` (`_django_patches.py:107`), matching the package-wide logger convention documented in `__init__.py:7-13`.
- **New helpers considered.** Considered extracting a shared wrap/unwrap helper across `_patched_remove_databases_failures` and `testing/_wrap.py::safe_wrap_connection_method`; rejected because they operate at opposite lifecycle sites (unwrap-time recovery vs wrap-time prevention) on different object surfaces (Django classmethod descriptor vs `connections[alias]` instance method). The module docstring (`_django_patches.py:60-91`) explicitly frames these as two halves of one defense-in-depth pattern, not a single extractable mechanism.
- **Duplication risk in the current file.** The patched loop (`_django_patches.py:167-174`) is a near-verbatim copy of Django's upstream `SimpleTestCase._remove_databases_failures`. This is intentional and necessary: the patch must mirror upstream exactly except for the inserted guard, so any divergence would be a bug, not desirable DRY. Verified verbatim against the installed Django 6.0.5 (`uv run python -c "inspect.getsource(...)"`): the only difference is the `if _is_database_failure(method):` guard wrapping the existing `setattr(connection, name, method.wrapped)`.

### Other positives

- **Faithful, minimal patch.** Confirmed against Django 6.0.5's actual `_remove_databases_failures` source: the body is identical apart from the added isinstance guard. The patch is strictly defensive — when the wrapper is still in place it unwraps exactly as upstream; when replaced it declines to touch the foreign method instead of crashing. The docstring's two-bullet behavior contract (`_django_patches.py:147-156`) matches the code precisely.
- **Idempotent, self-healing install.** `apply` short-circuits via `_patch_is_installed` when already installed and re-installs after a third-party revert. `_patch_is_installed` correctly reads `SimpleTestCase.__dict__` (not attribute access, which would resolve the bound descriptor) and guards the `installed is None` case (`_django_patches.py:186-189`), covering the future-Django-relocation scenario.
- **Graceful private-symbol degradation.** The `_DatabaseFailure` import is wrapped in `try/except ImportError` with `# pragma: no cover` justified by monkeypatch-driven tests; `apply` no-ops with a single INFO log gated by the `_missing_symbol_logged` module sentinel so repeated `ready()` invocations don't spam the logger.
- **Exhaustive test coverage.** `tests/test_django_patches.py` pins every branch: idempotency (`test_apply_is_idempotent`), revert-and-reinstall (`test_apply_reinstalls_when_class_attribute_reverted`), inheritance across `SimpleTestCase`/`TransactionTestCase`/`TestCase` plus a direct `SimpleTestCase` subclass with an explicit MRO assertion, real-wrapper unwrap, non-wrapper skip (the load-bearing fix), the `installed is None` branch, an upstream-crash pin (`test_unpatched_remove_databases_failures_crashes_on_non_wrapper`) that fails loud if Django ever fixes the bug, the missing-symbol no-op, and the once-per-process log sentinel.
- **GLOSSARY in sync.** The `Django Trac #37064 hardening` entry (`docs/GLOSSARY.md:1309-1319`) and the `safe_wrap_connection_method` entry (`docs/GLOSSARY.md:1116-1129`) accurately describe the patch site, the isinstance guard, the auto-application at `ready()`, and the wrap-time/unwrap-time pairing. The `apps.py` cross-reference (`docs/GLOSSARY.md:299`) matches the actual `ready()` body (`apps.py:28-30`). No drift.
- **Correct privacy boundary.** The module is private (leading underscore) and consumers never import it; only `apply` is unprefixed so the regression tests and `apps.ready()` can call it. The docstring's "Surface visibility" section (`_django_patches.py:93-102`) documents this intentionally.

### Summary

A small, single-purpose defensive-patch module that is in excellent shape. The patch body is a verified-verbatim mirror of Django 6.0.5's `_remove_databases_failures` plus one centralized isinstance guard, the install path is idempotent and self-healing, the missing-symbol degradation is graceful and logged-once, and the test suite exhaustively pins every branch including an upstream-crash canary. GLOSSARY documentation is accurate and in sync. No High, Medium, or Low findings; no actionable DRY opportunities (the only near-copy is the intentional, necessary upstream mirror, and the wrap-time sibling is a correct separate concern). The cycle diff against the baseline is empty — the file was not touched this cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 267 files left unchanged.
- `uv run ruff check --fix .` — All checks passed.

### Notes for Worker 3
No-findings file (template shape #1) combined with no-source-edit cycle (shape #5): all severities `None.`, no actionable DRY, zero edits to any tracked file. The patch body was verified verbatim against the installed Django 6.0.5 upstream `SimpleTestCase._remove_databases_failures` (only diff: the centralized `_is_database_failure` guard before `setattr`). GLOSSARY entries (`Django Trac #37064 hardening`, `safe_wrap_connection_method`, the `apps.py` cross-ref) verified in sync — no GLOSSARY-only fix in scope. No Lows to disposition. Cycle diff vs `CYCLE_BASELINE` is empty.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits in scope — the module's comments and docstrings are accurate against the code (verified the behavior contract, privacy-boundary note, and defense-in-depth framing all match implementation).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (empty diff vs baseline), and AGENTS.md instructs not to touch `CHANGELOG.md` unless explicitly instructed; the active plan `docs/review/review-0_0_10.md` is silent on changelog edits for this item.

---

## Verification (Worker 3)

This is a no-source-edit cycle (shape #5) combined with a no-findings file (shape #1). Terminal-verify with shape #5 additional checks.

### Logic verification outcome

No findings to disposition — all severities are `None.` and the claim is that the file genuinely qualifies. Re-read the full source and the shadow overview (`docs/shadow/django_strawberry_framework___django_patches.overview.md`) to confirm no missed High/Medium logic issue:

- **Patch body is a verbatim upstream mirror plus one guard (confirmed live).** Ran `inspect.getsource(SimpleTestCase._remove_databases_failures.__func__)` against the installed Django 6.0.5. The upstream body is byte-for-byte the loop at `_django_patches.py:167-174`; the *only* divergence is the inserted `if _is_database_failure(method):` guard (`_django_patches.py:173`) wrapping the existing `setattr(connection, name, method.wrapped)`. The artifact's central correctness claim holds. The patch is strictly defensive (unwraps exactly as upstream when the wrapper is intact; declines to touch a foreign replacement otherwise) — no behavior regression, no missed logic defect.
- **Install path is sound.** `_patch_is_installed` reads `SimpleTestCase.__dict__.get(...)` (not attribute access, which would resolve the bound descriptor) and guards `installed is None` (`_django_patches.py:186-189`); `apply` short-circuits when installed and re-installs after a revert (`_django_patches.py:225-229`). The `_DatabaseFailure is None` no-op path logs once via the `_missing_symbol_logged` sentinel (`_django_patches.py:216-224`). No missed branch or ordering issue.
- **Tests pin every branch.** All test names cited in `What looks solid` grep-match in `tests/test_django_patches.py` (idempotency:49, revert-reinstall:61, inheritance:109/120/215, real-wrapper unwrap:152, non-wrapper skip:181, `installed is None`:131, upstream-crash canary:248, missing-symbol no-op:295, once-per-process log:330). No High-severity fix exists to require a new test.

### DRY findings disposition

DRY analysis is sound. The single `isinstance` guard is centralized in `_is_database_failure` (`_django_patches.py:129-131`) and consumed once at `_django_patches.py:173`. The only near-duplication — the wrap-time half in `testing/_wrap.py::safe_wrap_connection_method` — is correctly held separate: it operates at the opposite lifecycle site (wrap-time prevention vs unwrap-time recovery) on a different object surface (`connections[alias]` instance method vs the `SimpleTestCase` classmethod descriptor). Collapsing them would couple two unrelated install protocols. The module docstring (`_django_patches.py:60-91`) frames these as two halves of one defense-in-depth pattern. No actionable DRY opportunity. Carried forward: none.

### Temp test verification

- Temp test files used: none. The upstream-mirror claim was confirmed directly via `inspect.getsource` against the installed Django 6.0.5, which is the falsifiable check the artifact rests on.
- Disposition: n/a.

### Shape #5 (no-source-edit) checks

1. `git diff 3cb9c7894e8ba9a84b7596735ba2513e4a6af018 -- django_strawberry_framework/_django_patches.py` is **empty**. `git diff --stat` vs baseline is **empty**. The file was not touched this cycle — claim genuine.
2. Each Worker 2 section begins with `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed (Fix report, Comment/docstring pass, Changelog disposition).
3. No Lows exist (all `None.`); none to forward. No GLOSSARY-only fix in scope — GLOSSARY entries (`Django Trac #37064 hardening`, `safe_wrap_connection_method`, `apps.py` cross-ref) verified present and in sync at `docs/GLOSSARY.md`, not edited this cycle.
4. Changelog disposition is `Not warranted` and cites BOTH `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence. `git diff -- CHANGELOG.md` is **empty**. The cycle is internal-only (zero source change), so `Not warranted` is the correct state.
5. `uv run ruff format --check` — `1 file already formatted`. `uv run ruff check` — `All checks passed!`.

Working-tree dirtiness (`django_strawberry_framework/__init__.py`, `pyproject.toml`, `uv.lock`) is the version bump to `0.0.10`; `git diff` of these vs the baseline SHA is **empty**, so the bump predates this cycle's baseline and is not this item's edit (AGENTS.md #33 — pre-existing/orchestrator work, out of scope). The cycle's "Files touched: None" claim holds.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box at `docs/review/review-0_0_10.md`.
