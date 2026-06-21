# Review: `django_strawberry_framework/conf.py`

Status: verified

## DRY analysis

- None — `_normalize_user_settings` is already the single shared shape-contract helper for all three cache-write sites (`Settings.__init__` conf.py:106-108, `Settings.user_settings` conf.py:124-127, `Settings.reload` conf.py:137), so the `None`→`{}` / non-mapping→`ConfigurationError` / dict-passthrough / Mapping-copy normalization exists in exactly one place; no duplicated literal, branch, or parallel data-flow remains to consolidate.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The four cache-write paths funnel through one normalizer: `Settings.__init__` (conf.py:106-108), the lazy `Settings.user_settings` read (conf.py:124-127), and `Settings.reload` (conf.py:137) all call `_normalize_user_settings` (conf.py:56-89), so the validation/normalization contract is defined once and applied uniformly. The two module-level setting-name constants (`DJANGO_SETTINGS_KEY` conf.py:46, `APPLY_UPSTREAM_PATCHES_KEY` conf.py:53) are named once and reused at every read/error site (conf.py:85, 126, 182, 196), so no raw string-key literal is repeated (helper reports 0 repeated literals).
- **New helpers considered.** None needed at this granularity — the module is 8 symbols, 0 control-flow hotspots, and the only branching logic already lives in the shared normalizer. A wrapper around the two `getattr(..., default)` reflective reads (conf.py:126, 182) was considered and rejected: they read different defaults (`None` vs `True`) for different semantics (lazy-load probe vs opt-out toggle) and unifying them would obscure that distinction.
- **Duplication risk in the current file.** The `None if X is None else _normalize_user_settings(X)` shape appears at conf.py:106-108 and conf.py:137 — this is intentional sibling design (construction-time vs reload-time entry), each is a single delegating line to the shared helper, and folding them would require a private method whose only body is that one-liner; the current factoring is correct.

### Other positives

- Clean separation of the two defensive-`None` consumer-input seams from the optimizer's reflective `getattr(...) or {}` reads, documented at length in the module docstring (conf.py:17-35) with an explicit "Do not unify the two" instruction — prevents a future DRY pass from incorrectly collapsing semantically distinct coercions.
- `__getattr__` correctly short-circuits dunder names and the two internal attribute names with bare `AttributeError` (conf.py:153-154) so `copy`/`deepcopy`/`inspect` get readable traces, and only catches `KeyError` (conf.py:161-162) — a malformed-config `ConfigurationError` from the lazy `user_settings` read deliberately propagates through `hasattr`/`getattr(default=...)` probes rather than masquerading as a missing attribute. This is the documented fail-loud contract.
- `reload_settings` mutates the singleton in place rather than rebinding the module global (conf.py:185-197), so `from .conf import settings` bindings observe `setting_changed`-driven test overrides immediately; the `**kwargs` absorption of the `setting_changed` payload is documented as required, not optional.
- Import-time `setting_changed.connect(..., dispatch_uid=_DISPATCH_UID)` (conf.py:205) is idempotent under re-import and is justified in-comment (conf.py:200-204) as not relocatable to `AppConfig.ready()` because `conf` may be imported during test bootstrap before app loading.
- Conforms to the AGENTS.md conf.py contract: reads `DJANGO_STRAWBERRY_FRAMEWORK` from the consumer settings dict, missing keys raise `AttributeError`, and no future-feature keys are preemptively populated (only `APPLY_UPSTREAM_PATCHES`, whose feature has shipped, is named).
- GLOSSARY drift quick-check passed: the `ConfigurationError` entry (GLOSSARY.md:239-250) and the `RELAY_GLOBALID_STRATEGY` "thin `conf.py` reader" prose (GLOSSARY.md:1131) accurately describe current `conf.py` behavior; no conf.py-owned public symbol has stale documentation.

### Summary

`conf.py` is a small, well-factored settings-reader module (8 symbols, no control-flow hotspots, no ORM markers, no repeated literals). It is byte-identical to HEAD and to the cycle baseline `f5e2d02da87fcd2469848627ac9faf7f2480df16` — no edits this cycle. The single shared normalizer already gives it the maximally-DRY shape, the defensive-`None` contract is precisely documented and deliberately not over-unified with the optimizer's reflective reads, and the public-symbol GLOSSARY prose has not drifted. No High, Medium, or Low findings. This is a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 289 files left unchanged (no changes).
- `uv run ruff check --fix .` — pass, all checks passed (no changes).

### Notes for Worker 3
- No GLOSSARY-only fix in scope: the `ConfigurationError` (GLOSSARY.md:239-250) and `RELAY_GLOBALID_STRATEGY` (GLOSSARY.md:1131) entries that touch conf.py territory accurately describe current behavior; no conf.py-owned public symbol has drifted prose.
- Cycle diff is empty against both the cycle baseline `f5e2d02da87fcd2469848627ac9faf7f2480df16` and HEAD (`git diff HEAD -- django_strawberry_framework/conf.py` empty); conf.py is unchanged this cycle.
- All severities `None.`; single DRY-analysis bullet is the `- None — ...` form. No deferred findings.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits — the module docstring (conf.py:1-36), the per-symbol docstrings, and the inline comments (conf.py:49-52, 156-159, 200-204) accurately describe current behavior; nothing stale, restating, or promising un-implemented behavior.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source edits this cycle (AGENTS.md #21 "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_11.md` records no changelog action for this item).

---

## Verification (Worker 3)

### Logic verification outcome
Every High / Medium / Low is `None.` and genuine. Independently confirmed no missed defect forces a source edit:
- `_normalize_user_settings` (conf.py:56-89) is the single shared normalizer; all four cache-write sites (`__init__` conf.py:106-108, `user_settings` conf.py:124-127, `reload` conf.py:137) funnel through it — DRY-maximal, no duplicated branch to consolidate.
- Every conf.py branch is pinned by a named test in `tests/base/test_conf.py`: None→{} (`test_settings_user_settings_falsy_falls_back_to_empty_dict`), non-Mapping→`ConfigurationError` (`test_settings_user_settings_rejects_non_mapping_django_setting`, `test_settings_reload_rejects_non_mapping_value`), dict-passthrough / Mapping-copy (`test_settings_user_settings_accepts_mapping_values`, `test_settings_returns_user_setting_when_provided`), `__getattr__` dunder short-circuit (`test_settings_dunder_lookup_raises_plain_attributeerror`), KeyError→AttributeError (`test_settings_invalid_attribute_raises`), non-recursion on both seams (`test_settings_uninitialized_user_settings_does_not_recurse`, `test_settings_normalization_attribute_error_does_not_recurse`), lazy load, in-place reload (None-restore, unrelated-key), dispatch_uid idempotency, and `upstream_patches_enabled` default/true/false. No unpinned defensive seam; `None.` severities are correct, not lazy.

### Shape #5 (no-source-edit) gate
1. `git diff f5e2d02da87fcd2469848627ac9faf7f2480df16 -- django_strawberry_framework/conf.py` empty; `git diff HEAD -- django_strawberry_framework/conf.py` empty; conf.py byte-identical to baseline and HEAD. Working tree clean for conf.py.
2. Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` (Fix report, Comment/docstring pass, Changelog disposition). ✓
3. All severities `None.`; single DRY item is the `- None — ...` form. No GLOSSARY-only fix (not disqualifying). ✓
4. Changelog `Not warranted` cites BOTH AGENTS.md #21 AND active-plan silence; `git diff -- CHANGELOG.md` empty. ✓ Internal-only framing honest — cycle made zero edits.
5. Ruff format-check + check recorded as pass; no edits, nothing to re-run.

### Shape #4-vs-#5 (no GLOSSARY edit owed)
Confirmed genuine shape #5, not a missed shape #4. The only `docs/GLOSSARY.md` working-tree hunk is at line ~305 (relation-cardinality annotation validation) — unrelated concurrent maintainer/sibling work per AGENTS.md #33, not a conf.py-owned edit. The two conf.py-territory entries are untouched by the diff and accurate against live source: `ConfigurationError` (GLOSSARY.md:239-256, generic type-creation/finalization error; conf.py:84 raises it for the non-mapping case) and `RELAY_GLOBALID_STRATEGY` "read through the thin `conf.py` reader" (GLOSSARY.md:1131 — accurately describes `Settings.__getattr__`). No conf.py-owned public symbol has drifted prose; no GLOSSARY fix owed.

### DRY findings disposition
Single `- None` DRY bullet — the shared normalizer already gives conf.py its maximally-DRY shape; nothing carried forward.

### Temp test verification
- None used — zero-edit cycle; branch coverage independently confirmed against the existing permanent suite (`tests/base/test_conf.py`).
- Disposition: n/a.

### Verification outcome
cycle accepted; verified — sets top-level `Status: verified` AND marks the `conf.py` checklist box in `docs/review/review-0_0_11.md`.
