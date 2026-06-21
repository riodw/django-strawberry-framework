# Review: `django_strawberry_framework/_cross_web_patches.py`

Status: verified

## DRY analysis

- Defer the three-module patch-scaffold extraction until the project-level pass (`docs/review/rev-django_strawberry_framework.md`) triages it as a package-wide concern. `_cross_web_patches.py`, `_strawberry_patches.py`, and `_django_patches.py` all replicate the same `apply()` skeleton: the `if not upstream_patches_enabled(): return` toggle gate, the `_missing_symbol_logged` once-per-process `logger.info(...)` notice, the `if _patch_is_installed(): return` re-entrancy short-circuit, and the import-time symbol-capture-with-`ImportError`-fallback pattern (`_cross_web_patches.py:108-115,136,163-184`; `_strawberry_patches.py:166-176,190,236-270`; `_django_patches.py:112,131,182,197-234`). A shared helper — e.g. `_apply_patch(*, is_installed, install, missing_symbol_present, missing_msg, _state)` or a small `PatchModule` dataclass holding the captured original + install/check callables — would collapse three near-identical `apply()` bodies into one. This is genuinely cross-module, so it is a forward-to-project-pass item, not a local defect; flagging it here per REVIEW.md's "forward package-wide concerns by citing `rev-django_strawberry_framework.md`". Trigger to act: the project pass confirms the three modules stay structurally parallel after their own per-file reviews land.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Reuses the canonical package `logger` via `from . import logger` (`_cross_web_patches.py:105`) and the shared settings gate `upstream_patches_enabled()` from `conf` (`_cross_web_patches.py:106`, called at `apply()` `_cross_web_patches.py:171`) rather than re-reading `DJANGO_STRAWBERRY_FRAMEWORK` directly. Deliberately mirrors the companion `_strawberry_patches.py` shape (same `_missing_symbol_logged` sentinel, same `_patch_is_installed`/`apply` contract), keeping the patch family consistent.
- **New helpers considered.** A local intra-file helper was considered and rejected: each of the four module functions is single-purpose and called once, so there is no within-file duplication to extract. The only real consolidation is the cross-module `apply()` scaffold, which is correctly a project-pass concern (see `## DRY analysis`), not a local helper.
- **Duplication risk in the current file.** The `_missing_symbol_logged` sentinel, the `isinstance(descriptor, property)` descriptor check (`_cross_web_patches.py:130,160`), and the wrapper/`_original_*`/`_patch_is_installed`/`apply` quartet are intentional sibling-of-`_strawberry_patches.py` design; the near-copy across the two modules is the documented "one patch module per third-party dependency" convention (module docstring `_cross_web_patches.py:5-6`), not accidental duplication. Correct to keep parallel until the project pass decides on a shared scaffold.

### Other positives

- **Root-cause-correct, minimal-surface patch.** `_patched_body` (`_cross_web_patches.py:139-152`) wraps the captured upstream getter and only diverges on the `UnicodeDecodeError` path, returning raw `self.request.body` bytes. The success path is byte-for-byte upstream (verified by `tests/test_cross_web_patches.py::test_body_returns_str_for_valid_utf8`), and the failure path hands bytes to `json.loads` so the companion Strawberry patch can produce a clean `400` instead of a `500`. This is the mirror-the-async-adapter fix, not a surface workaround.
- **Robust import-time capture.** The genuine upstream getter is captured once at import (`_cross_web_patches.py:128-131`) behind an `isinstance(_descriptor, property) and _descriptor.fget is not None` guard, before `apply()` can install the wrapper, so a self-healing re-install never wraps a wrapper. The `_original_body_fget` placeholder raises `NotImplementedError` and is `pragma: no cover` only for the genuinely-unreachable symbol-present case.
- **Graceful degradation.** Missing-symbol `ImportError` is absorbed (`_cross_web_patches.py:108-115`) and `apply()` no-ops with a single once-per-process `INFO` notice gated by `_missing_symbol_logged` (`_cross_web_patches.py:173-181`), keeping the package loadable on a future `cross_web` that relocates the adapter. The toggle (`APPLY_UPSTREAM_PATCHES`), idempotency, and self-heal are all exercised.
- **Strong test coverage.** `tests/test_cross_web_patches.py` pins idempotency, self-heal-after-revert, the str/bytes success/failure split, symbol-missing no-op + once-only logging, and the toggle-off path — every branch in `apply()` and `_patched_body` is covered.
- **Exemplary documentation.** The module docstring states the exact upstream bug, the upstream version/permalink (`cross-web` 0.7.0, checked 2026-06-18), retirement criteria, and two reproducible re-check procedures. The `apply()` entry point is correctly the only non-underscore export (private module, callable-by-tests entry), documented under "Surface visibility".

### Summary

A small (185-line), single-responsibility defensive monkeypatch module that fixes a real upstream `cross_web` bug (bare `.decode()` on the sync request adapter turning non-UTF-8 bodies into `500`s) at the root-cause level by handing raw bytes to `json.loads`, mirroring the async adapter. The implementation is idempotent, self-healing, settings-gated, and degrades gracefully when the upstream symbol moves; every branch is covered by `tests/test_cross_web_patches.py`. No correctness, API, ORM, async, or typing issues found. The only DRY opportunity is the `apply()` scaffold shared with the two sibling patch modules, correctly forwarded to the project-level pass. No source edits warranted — this is a no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; "289 files left unchanged" (no source changes).
- `uv run ruff check --fix .` — pass; "All checks passed!" (no source changes).

### Notes for Worker 3
- No High/Medium/Low findings; all severities `None.`.
- The single DRY item is a forward-to-project-pass concern (shared `apply()` scaffold across `_cross_web_patches.py`/`_strawberry_patches.py`/`_django_patches.py`), not a local defect and not an edit-now item; it is cited for `docs/review/rev-django_strawberry_framework.md` to triage.
- No GLOSSARY-only fix in scope: `docs/GLOSSARY.md` contains no backticked symbols from this module (grep for `cross_web` / `_cross_web_patches` / `_original_body_fget` / `_patched_body` returned nothing).
- `git diff HEAD -- django_strawberry_framework/_cross_web_patches.py` is empty; the file is unchanged since commit `d807a3b7`.

---

## Verification (Worker 3)

Terminal-verify, shape #5 (no-source-edit) cycle. Incoming `Status: fix-implemented` (bare).

### Shape #5 zero-edit proof
- `git diff HEAD -- django_strawberry_framework/_cross_web_patches.py` is empty.
- `git diff --stat HEAD -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` is empty — zero tracked source/test/GLOSSARY/CHANGELOG edits this cycle.
- The only dirty paths in `git status` are per-cycle scratchpad/regenerable artifacts (`docs/review/rev-_cross_web_patches.md`, `docs/review/review-0_0_11.md`, `docs/dry/dry-0_0_11.md`, `docs/bug_hunt/bug_hunt.8b648557.md`, `docs/bug_hunt/dicta.md`) — none are tracked source owned by any cycle's edit scope; not a rejection trigger.
- Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` (Fix report, Comment/docstring pass, Changelog disposition). Confirmed.

### Logic verification outcome
All severities are `None.` and that is genuinely correct — no missed defect forces a source edit:
- `_patched_body` (source 149-152) delegates to the import-time-captured `_original_body_fget` and diverges only on `UnicodeDecodeError`, returning raw bytes; success path is byte-for-byte upstream. Root-cause fix mirroring the async adapter, not a surface patch. Pinned by `tests/test_cross_web_patches.py::test_body_returns_str_for_valid_utf8` (line 59) and `::test_body_returns_raw_bytes_for_invalid_utf8` (line 65).
- Import-time capture guarded by `isinstance(_descriptor, property) and _descriptor.fget is not None` (source 130) runs before `apply()`, so a self-heal never wraps a wrapper; `_patch_is_installed` checks `descriptor.fget is _patched_body` (source 160). Re-entrancy + self-heal pinned by `::test_apply_is_idempotent` (line 29) and `::test_apply_reinstalls_when_property_reverted` (line 36).
- `apply()` branch order (toggle gate → symbol-missing once-only INFO → already-installed → install) is correct; `_missing_symbol_logged` sentinel with `global` declaration ensures once-per-process logging. Pinned by `::test_apply_no_ops_when_symbol_missing` (line 77), `::test_apply_logs_missing_symbol_notice_only_once` (line 95), `::test_apply_no_ops_when_toggle_disabled` (line 114), `::test_patch_is_installed_false_when_symbol_missing` (line 71).
- `_original_body_fget` placeholder raises `NotImplementedError` and is `pragma: no cover` only for the genuinely-unreachable symbol-present case (source 118-122) — legitimate per AGENTS.md "unreachable under the test runner".
- Dependencies confirmed live: `conf.upstream_patches_enabled` (conf.py:168) and package `logger` (`__init__.py:13`). No false-premise rejections to audit (no `## Notes for Worker 3` false-premise entries).

### DRY findings disposition
Single DRY item (shared `apply()` scaffold across `_cross_web_patches.py` / `_strawberry_patches.py` / `_django_patches.py`) is correctly a cross-module concern forwarded to `docs/review/rev-django_strawberry_framework.md` for the project-level pass — not a local defect, not an edit-now item. Carried forward, not resolved here. Accepted.

### Temp test verification
- No temp tests needed; claims verified by reading live source/tests and grepping cited substrings. No pytest run (no test introduced; all cited tests already exist and the cycle is no-source-edit).
- Disposition: n/a.

### Changelog disposition verification
`Not warranted`. `git diff HEAD -- CHANGELOG.md` is empty (matches). Disposition cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan `docs/review/review-0_0_11.md` silence on changelog authorization. Internal-only framing is honest — zero edits, no public-API surface change. Accepted.

### GLOSSARY check
`grep -nE 'cross_web|_cross_web_patches|_original_body_fget|_patched_body' docs/GLOSSARY.md` returns nothing — no GLOSSARY-only fix in scope (disqualifying pattern absent). Confirmed.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box in `docs/review/review-0_0_11.md`.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No source edits; the module's comments and docstrings are accurate and current (upstream version/permalink dated 2026-06-18, retirement criteria and re-check procedures present). No comment/docstring changes warranted.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source or behavior change in this cycle (zero tracked-file edits). AGENTS.md instructs "Do not update CHANGELOG.md unless explicitly instructed", and the active plan `docs/review/review-0_0_11.md` is silent on changelog edits for this item.

---

## Iteration log

(none)
