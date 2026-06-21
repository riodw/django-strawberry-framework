# Review: `django_strawberry_framework/_strawberry_patches.py`

Status: verified

## DRY analysis

- Defer to project pass — the `apply()` scaffold (toggle gate via `upstream_patches_enabled()` + once-only missing-symbol `INFO` notice gated by a module sentinel + `_patch_is_installed()` re-entrancy short-circuit + import-time `ImportError` capture that nulls the patched symbols) is near-identical across `_cross_web_patches.py::apply`, `_strawberry_patches.py::apply` (lines 236-270), and `_django_patches.py::apply`. Consolidation candidate (e.g. a shared `_patch_scaffold` helper or a small base taking `is_installed`/`install`/`missing-symbol message` callables). Per the spawn brief and the two sibling artifacts, this is forwarded to the project-level pass — see `docs/review/rev-django_strawberry_framework.md`; not treated as a local defect. Trigger to act: the project pass confirming all three modules and a fourth patch module not being imminent (a fourth would only strengthen the case).

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Reuses the canonical `upstream_patches_enabled()` setting gate (`_strawberry_patches.py:164,257`) and the package `logger` (`_strawberry_patches.py:163,261`) rather than re-reading settings or constructing a logger locally. The wrapper delegates to the captured original (`_strawberry_patches.py:219` `_original_parse_json`) instead of reimplementing parse logic, so it tracks upstream changes to `parse_json`'s body.
- **New helpers considered.** A local helper to fold the two `HTTPException(400, ...)` raises (lines 221, 223-227) was considered and rejected — they carry distinct messages for distinct failure modes (decode failure vs non-object body) and a single helper would obscure that. The shared `apply()` scaffold is the only real consolidation candidate and is forwarded to the project pass (see DRY analysis), not extracted locally.
- **Duplication risk in the current file.** The `parse_json` string appears twice (the `BaseView.__dict__.get("parse_json")` capture at line 182 and the same lookup in `_patch_is_installed` at line 233). This is intentional sibling design: both must read the live `__dict__` slot to remain correct under a third-party revert, and hoisting to a constant would not reduce the two lookups (they query mutable runtime state, not a literal-dedup opportunity).

### Other positives

- Correctness re-verified against the installed Strawberry this cycle: `inspect.getsource(BaseView.parse_json)` shows the upstream catch is still only `except json.JSONDecodeError`, so `UnicodeDecodeError` (a `ValueError`, not a `JSONDecodeError`) still escapes — gap 1 is real. `SyncBaseHTTPView.parse_http_body` still has no `isinstance(data, dict)` guard before `data.get("query")` — gap 2 (scalar body) is real. The patch is still required.
- Wrap-not-reimplement design: the wrapper calls the captured upstream `_original_parse_json` and only translates the one previously-uncaught error and rejects non-`dict`/non-`list` results, so it is robust to upstream edits inside `parse_json`. The `list` branch is passed through untouched so upstream's own `_validate_batch_request` retains ownership of batch validation.
- Single-site rationale is sound: `parse_json` is the sole producer of a scalar `data` reaching `parse_http_body` (GET `parse_query_params` / `parse_multipart` always return a `dict`), so guarding the one inherited method fixes both sync and async transports — mirroring the `UnicodeDecodeError` widening.
- Idempotent, self-healing, gated: `apply()` returns early on the disabled setting, on missing symbols (with a once-per-process `INFO` notice gated by `_missing_symbol_logged`), and on re-entrant calls (`_patch_is_installed()`); it re-installs if a third party reverted the slot. Import-time `ImportError` nulls `BaseView`/`HTTPException` so a future incompatible Strawberry leaves the package loadable.
- Test discipline: all cited regression tests exist — `tests/test_strawberry_patches.py::test_apply_no_ops_when_symbols_missing`, plus `examples/fakeshop/test_query/test_products_api.py::test_post_invalid_utf8_json_body_returns_400_not_500`, `::test_post_raw_binary_body_returns_400_not_500`, and `::test_post_non_object_json_body_returns_400_not_500`. The `# pragma: no cover` on the import-fallback (line 169) is justified — the branch is exercised via monkeypatch, and the fallback is genuinely unreachable when the symbols import cleanly.
- Module docstring is exemplary: documents both gaps, upstream status with permalinks and issue refs (#1214 closed, #3398 open), two reproducible retirement-check procedures, and the deliberate private-module / public-`apply` surface split.

### Summary

`_strawberry_patches.py` is a clean, defensive monkeypatch module — the third of three sibling patch modules and the same high quality as the other two. It hardens two real, still-unfixed upstream Strawberry gaps (non-UTF-8 body `UnicodeDecodeError`, and scalar-body `AttributeError`) from the single inherited `BaseView.parse_json` site, wrapping rather than reimplementing the original, fully gated/idempotent/self-healing, and comprehensively tested. The `git diff HEAD` is empty (unchanged since the cycle baseline) and the upstream-still-needed claim re-verified against the installed Strawberry. Zero findings at any severity; the only DRY item is the cross-module `apply()` scaffold, forwarded to the project pass per the spawn brief. No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 289 files left unchanged (no edits).
- `uv run ruff check --fix .` — pass; "All checks passed!" (no edits).

### Notes for Worker 3
- Zero findings; nothing to verify per-severity beyond confirming the no-finding disposition.
- The one DRY-analysis bullet is a defer-to-project-pass forward (shared `apply()` scaffold across the three patch modules), citing `docs/review/rev-django_strawberry_framework.md`. Not a local edit.
- No GLOSSARY-only fix in scope — `docs/GLOSSARY.md` has no entry on this file's symbols (`parse_json` / `_strawberry_patches`); the only patch-module GLOSSARY prose is the `_django_patches` reference under `apps.py` (line 308), out of scope here.
- Correctness claim re-verified this cycle against installed Strawberry: `BaseView.parse_json` still catches only `json.JSONDecodeError`; `SyncBaseHTTPView.parse_http_body` still lacks an `isinstance(data, dict)` guard before `data.get("query")`. Both gaps remain real — patch still required.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring changes warranted. The module docstring, the `_patched_parse_json` docstring, and the inline comments accurately describe current behavior and were verified against the installed Strawberry source this cycle.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source, test, or doc edits were made (no-source-edit cycle), so there is nothing to record. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan's silence on changelog entries for review cycles, no changelog change is appropriate.

---

## Verification (Worker 3)

Shape #5 (no-source-edit) terminal-verify.

### Zero-edit proof
- `git diff HEAD -- django_strawberry_framework/_strawberry_patches.py` is empty.
- `git diff --stat HEAD -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` is empty — no source/test/glossary/changelog path is dirty. The only dirty paths in the working tree are per-cycle / regenerable docs scratchpad (`docs/bug_hunt/*`, `docs/dry/dry-0_0_11.md`, sibling `rev-*.md`, `review-0_0_11.md`) — not a rejection trigger. The cycle's "Files touched: None" claim holds.
- Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.`

### Logic verification outcome
No High / Medium / Low findings to disposition — all three sections are `None.`, and the no-finding disposition is genuine, not lazy:
- **Gap 1 (UnicodeDecodeError) re-verified independently** against installed `strawberry-graphql` 0.316.0: `inspect.getsource(BaseView.parse_json)` shows the catch is still `except json.JSONDecodeError` only. `UnicodeDecodeError` is a `ValueError`, not a `JSONDecodeError`, so it escapes → 500. Patch still required.
- **Gap 2 (scalar body) re-verified independently**: `inspect.getsource(SyncBaseHTTPView.parse_http_body)` shows it intercepts `list` (batch) then calls `data.get("query")` with no `isinstance(data, dict)` guard. A scalar `data` → `AttributeError` → 500. Patch still required.
- Wrapper logic is sound: rejecting anything not `(dict, list)` exactly mirrors upstream's two valid shapes; the `list` branch is passed through so upstream's `_validate_batch_request` retains batch ownership; the wrapper delegates to the captured `_original_parse_json` so it tracks upstream body changes. No missed defect forces a source edit.
- All cited tests grep-confirmed at their paths: `tests/test_strawberry_patches.py::test_apply_no_ops_when_symbols_missing` (line 123); `examples/fakeshop/test_query/test_products_api.py::test_post_invalid_utf8_json_body_returns_400_not_500` (2039), `::test_post_raw_binary_body_returns_400_not_500` (2049), `::test_post_non_object_json_body_returns_400_not_500` (2066).
- Content-not-identifier note: the docstring cites 0.317.2 as the latest release while the installed version is 0.316.0. The behavioral claims (the two gaps) are what matter and both are confirmed true against the actually-installed version; the version string is a recency detail, not a defect. Not a rejection trigger.

### DRY findings disposition
One DRY item: the shared `apply()` scaffold (toggle gate + once-only missing-symbol INFO + `_patch_is_installed()` re-entrancy short-circuit + import-time `ImportError` capture) near-identical across `_cross_web_patches.py`, `_strawberry_patches.py`, and `_django_patches.py`. Correctly forwarded to the project-level pass (`docs/review/rev-django_strawberry_framework.md`), not resolved locally — consistent with how the two sibling patch-module cycles forwarded the same item. Carry forward, do not resolve here.

### Temp test verification
- None used — the no-finding disposition was verifiable by `inspect.getsource` against installed Strawberry plus grep of the cited tests.

### Changelog disposition
`Not warranted`, `git diff -- CHANGELOG.md` empty, citing BOTH `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization. Internal-only framing matches scope (zero edits). Accepted.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.
