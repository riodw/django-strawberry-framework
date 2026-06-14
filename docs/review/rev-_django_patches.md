# Review: `django_strawberry_framework/_django_patches.py`

Status: verified

## DRY analysis

- None — the one shared predicate (`_is_database_failure`) is already extracted and imported by the sibling wrap-time half (`django_strawberry_framework/testing/_wrap.py:27`, used at `_wrap.py:144`), so both lifecycle sites resolve `_DatabaseFailure` through a single function and degrade together if the private symbol moves. The patched loop body in `_patched_remove_databases_failures` (`_django_patches.py:167-174`) is an intentional minus-one-guard near-copy of Django's upstream `SimpleTestCase._remove_databases_failures` — it must track upstream verbatim except for the `isinstance` guard, so collapsing it into a shared helper would defeat the "mirror of upstream" auditability the patch depends on.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The wrap-time/unwrap-time defense-in-depth shares exactly one predicate: `_is_database_failure` (`_django_patches.py:129-131`) is imported and reused by `testing/_wrap.py:27` rather than re-deriving the `_DatabaseFailure` isinstance check at the wrap site. The package logger is reused via `from . import logger` (`_django_patches.py:107`), matching the package-wide single-logger convention declared in `django_strawberry_framework/__init__.py:13`.
- **New helpers considered.** Considered factoring the patched loop body (`_django_patches.py:167-174`) against Django's upstream method — rejected: the patch's value is being a line-for-line mirror of upstream with a single inserted guard (confirmed byte-identical to Django 6.0.5's `SimpleTestCase._remove_databases_failures` modulo the guard), so abstracting it would obscure the diff a future maintainer must re-check on each Django bump. Considered extracting the `classmethod(...)` install + `__func__` identity check into one helper — rejected: `_patch_is_installed` (`_django_patches.py:177-189`) already encapsulates the descriptor-unwrap, and the single install site in `apply` (`_django_patches.py:227-229`) does not justify another indirection.
- **Duplication risk in the current file.** The teardown-loop shape (`for alias in connections` / `if alias in cls.databases: continue` / inner `for name, _ in cls._disallowed_connection_methods`) duplicates upstream Django; this is required parallelism, not divergence-prone duplication, and the companion test `test_unpatched_remove_databases_failures_crashes_on_non_wrapper` pins that upstream still has the bug shape so the patch can be retired when it no longer does.

### Other positives

- **Defensive import is correct and tested.** The `try/except ImportError` fallback to `_DatabaseFailure = None` (`_django_patches.py:109-117`) keeps the whole package loadable on a future Django that moves/removes the private symbol; `apply()` no-ops with a single INFO notice rather than crashing the app loader. Both the no-op branch and the once-per-process log gating are pinned (`tests/test_django_patches.py::test_apply_no_ops_when_database_failure_symbol_missing`, `::test_apply_logs_missing_symbol_notice_only_once`). The `# pragma: no cover` on the except line (`_django_patches.py:111`) is legitimate per AGENTS.md — the import succeeds under the test runner; the branch is exercised via `mock.patch.object(_django_patches, "_DatabaseFailure", None)` instead.
- **Idempotent and self-healing `apply()`.** `_patch_is_installed` (`_django_patches.py:177-189`) reads the raw `classmethod` descriptor off `SimpleTestCase.__dict__` and compares `__func__` identity, correctly handling both the re-entrant `ready()` case and a third-party revert; the `installed is None` branch guards a future Django that relocates the method off `SimpleTestCase`. All three states (idempotent re-call, re-install-after-revert, attribute-absent) are pinned (`::test_apply_is_idempotent`, `::test_apply_reinstalls_when_class_attribute_reverted`, `::test_patch_is_installed_returns_false_when_attribute_absent_from_class_dict`).
- **Patch placement is minimal and inheritance-aware.** Patching `SimpleTestCase` (the class where Django *defines* the method) covers `TransactionTestCase` and `TestCase` and direct `SimpleTestCase` subclasses through normal inheritance — one patch, whole hierarchy. The MRO premise is itself asserted (`::test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass` checks `TransactionTestCase not in __mro__`).
- **Module/docstring quality.** The module docstring accurately documents the upstream Trac #37064 reference, the debug-toolbar precedent at both lifecycle sites, why this package owns no wrap-time site of its own, and the private-module rationale (only `apply` is unprefixed, for the regression tests). The `apply` and `_patch_is_installed` docstrings match their implementations exactly. No stale TODOs; no spec anchors.
- **GLOSSARY consistency.** The "Django Trac #37064 hardening" and `safe_wrap_connection_method` entries in `docs/GLOSSARY.md` (lines 1289-1299, 1096-1115) describe the guard (`isinstance(method, _DatabaseFailure)` before `setattr(..., method.wrapped)`), the `SimpleTestCase` install site, the inheritance coverage, and the `AppConfig.ready` application path accurately. No drift.

### Summary

A small, sharply-scoped defensive-patch module that is correct, idempotent, self-healing, and exhaustively tested across every branch (happy unwrap, the Trac-#37064 skip-non-wrapper assertion, the upstream-still-broken companion, the missing-symbol no-op, and the once-per-process log gate). The one cross-module DRY opportunity — a shared `_DatabaseFailure` predicate — is already realized via the `_is_database_failure` import in `testing/_wrap.py`. The patched-loop near-copy of Django upstream is intentional and audit-friendly, not a DRY defect. No High/Medium/Low findings; GLOSSARY prose is accurate. Nothing to fix.

---

## Fix report (Worker 2)

Consolidated single-spawn (no-findings file pass, REVIEW shape #1). Worker 1
recorded High 0 / Medium 0 / Low 0 and a single `- None` DRY bullet. Source
verified against the artifact's premises before recording the pass:

- `_is_database_failure` at `_django_patches.py:129-131` and its cross-module
  reuse premise (the shared predicate imported by `testing/_wrap.py`) confirmed.
- The patched loop body at `_django_patches.py:167-174` confirmed as the
  intentional minus-one-guard near-copy of upstream Django.
- `_patch_is_installed` at `_django_patches.py:177-189` and the single install
  site in `apply` at `_django_patches.py:227-229` confirmed.

No finding requires an edit; the DRY opportunity is already realized. No-op
logic pass.

### Files touched

None — no source or test file changed.

### Tests added or updated

None — no behaviour change to pin.

### Validation run

- `uv run ruff format .` — pass / no-changes (265 files left unchanged)
- `uv run ruff check --fix .` — pass / no-changes (All checks passed!)
- pytest not run (AGENTS.md). No focused validation applicable to a no-op pass.

### Notes for Worker 3

- Shadow overview consulted: `docs/shadow/django_strawberry_framework___django_patches.overview.md` (read-only; line numbers there are non-canonical, source line numbers cited above).
- No intentionally-rejected findings (artifact had none to reject); the source matches every artifact premise verbatim.
- No deferred findings.
- `uv.lock` untouched after both ruff runs.
- Out-of-scope tree noise present at dispatch (deleted `feedback2.md`/`feedback3.md`, untracked `docs/review/review-0_0_9.md`) left untouched per AGENTS.md #33.

---

## Verification (Worker 3)

### Logic verification outcome

Shape #1 no-findings consolidated cycle (High 0 / Med 0 / Low 0). No High/Medium/Low
finding to disposition; independently re-inspected the file for correctness,
edge-case, and DRY issues a clean pass might have missed:

- **Cross-module DRY premise confirmed.** `_is_database_failure`
  (`_django_patches.py:129-131`) is imported by the wrap-time half at
  `testing/_wrap.py:27` and used at `_wrap.py:144`, so both lifecycle sites
  resolve `_DatabaseFailure` through one predicate. Premise holds; the lone DRY
  opportunity is already realized.
- **Upstream-mirror claim verified against the live dependency.**
  `uv run python -c "inspect.getsource(SimpleTestCase._remove_databases_failures)"`
  on Django 6.0.5 returns a loop byte-identical to `_django_patches.py:167-174`
  (same `for alias in connections` / `if alias in cls.databases: continue` /
  inner `for name, _ in cls._disallowed_connection_methods` / `getattr` /
  `setattr(..., method.wrapped)`), differing only by the inserted
  `if _is_database_failure(method):` guard. The "minus-one-guard near-copy" /
  "intentional upstream mirror, not a DRY defect" framing is exactly correct;
  collapsing it would defeat audit-on-bump.
- **Helper correctness re-checked.** `_patch_is_installed` reads the raw
  `classmethod` descriptor off `SimpleTestCase.__dict__` (not via attribute
  access, so an inherited entry cannot false-match), guards `installed is None`,
  and compares `__func__` identity. `apply` declares `global`, gates the
  missing-symbol INFO notice behind the `_missing_symbol_logged` sentinel
  (written only in that branch), is idempotent, and re-installs after revert.
  `_is_database_failure` short-circuits safely when `_DatabaseFailure is None`.
  No mutable-default, resource-leak, or concurrency concern (module-load +
  single-threaded `AppConfig.ready`).
- **`# pragma: no cover` on the ImportError branch** (`_django_patches.py:111`)
  is legitimate per AGENTS.md — the import succeeds under the test runner; the
  branch is exercised via `mock.patch.object(..., "_DatabaseFailure", None)`.
- **Test-coverage premises grep-confirmed.** All seven test names the artifact
  cites exist in `tests/test_django_patches.py` (`test_apply_is_idempotent`,
  `test_apply_reinstalls_when_class_attribute_reverted`,
  `test_patch_is_installed_returns_false_when_attribute_absent_from_class_dict`,
  `test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass`,
  `test_unpatched_remove_databases_failures_crashes_on_non_wrapper`,
  `test_apply_no_ops_when_database_failure_symbol_missing`,
  `test_apply_logs_missing_symbol_notice_only_once`).

No defect found. Worker 1's "no findings" conclusion is sound.

### DRY findings disposition

The single `- None` DRY bullet is accepted. The one cross-module predicate
(`_is_database_failure`) is already extracted and shared with `testing/_wrap.py`;
the patched-loop near-copy of upstream is required parallelism, not
divergence-prone duplication. Nothing to carry forward.

### Temp test verification

No temp tests created — the no-op pass introduced no behaviour to pin, and the
existing permanent suite (`tests/test_django_patches.py`) already covers every
branch. Cross-module reuse, the upstream-mirror claim, ruff cleanliness, and the
empty cycle diff were verified by direct grep / source inspection / `git diff`,
which require no temp scaffold.

### No-source-edit (shape #1) checks

- Cycle diff empty: `git diff 0872a20fcbecf870b3669742f108364202709e26 -- django_strawberry_framework/_django_patches.py` → empty.
- `git diff -- CHANGELOG.md` → empty (consistent with "Not warranted").
- `uv run ruff format --check django_strawberry_framework/_django_patches.py` → "1 file already formatted".
- `uv run ruff check django_strawberry_framework/_django_patches.py` → "All checks passed!".
- Tree noise at dispatch (deleted `feedback2.md`/`feedback3.md`, untracked
  `docs/review/review-0_0_9.md`) left untouched per AGENTS.md #33 — not owned by
  any source path this cycle reviews.

### Changelog disposition verification

`Not warranted` accepted. `git diff -- CHANGELOG.md` is empty (consistent). The
disposition cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly
instructed") AND the active plan's silence on changelog authorization for this
per-file cycle. The internal-only framing is honest: the cycle landed zero
source/test/comment changes, so there is no consumer-visible surface to record —
"Not warranted" is the correct state (not the deferred-to-maintainer state).

### Comment/docstring verification

No comment or docstring change landed. Re-read the module docstring and the
`_is_database_failure`, `_patched_remove_databases_failures`, `_patch_is_installed`,
and `apply` docstrings: each accurately describes the final (unchanged) behaviour,
the Trac #37064 reference, the debug-toolbar precedent, and the private-module
rationale. No stale TODOs, no spec anchors, no forward-looking slice labels.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
checklist box in `docs/review/review-0_0_9.md`.

---

## Comment/docstring pass

No comment or docstring change. The module docstring, the `_is_database_failure`,
`_patched_remove_databases_failures`, `_patch_is_installed`, and `apply`
docstrings all describe the final (unchanged) behaviour accurately — Worker 1's
"Module/docstring quality" positive confirms the `apply` and `_patch_is_installed`
docstrings match their implementations exactly, and source re-read confirms the
same for the module docstring and the two helpers. No stale TODOs, no spec
anchors, no forward-looking phase/slice labels to drop.

### Files touched

None.

### Per-finding dispositions

No High/Medium/Low findings to disposition.

### Validation run

- `uv run ruff format .` — pass / no-changes
- `uv run ruff check --fix .` — pass / no-changes

### Notes for Worker 3

No comment edits; nothing to verify beyond the no-op.

---

## Changelog disposition

### State

`Not warranted`.

### Reason

No source, test, or comment change landed this cycle — there is no
consumer-visible change to record. Per `AGENTS.md` ("Do not update CHANGELOG.md
unless explicitly instructed"), and the active review plan is silent on any
changelog authorization for this per-file cycle (per-file cycles are never the
authorising scope and forward any drift to the project pass). Both citations
apply.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass / no-changes
- `uv run ruff check --fix .` — pass / no-changes

---

## Iteration log
