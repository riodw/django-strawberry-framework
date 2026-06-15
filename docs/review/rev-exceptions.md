# Review: `django_strawberry_framework/exceptions.py`

Status: verified

## DRY analysis

- None — the module is three pure exception-class definitions with empty bodies (docstrings only). There is no logic, no literal, and no shared shape to consolidate; the hierarchy `DjangoStrawberryFrameworkError` → `ConfigurationError` / `OptimizerError` is the canonical single source for the package's exception types, and every other module imports from here rather than redefining.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

This is a **skip artifact** (REVIEW.md shape #2): the shadow overview confirms 0 imports, 3 symbols all class definitions, 0 executable marker lines, 0 calls of interest, and 0 module-level functions — so the static helper was correctly skipped per worker-1.md ("may skip for pure-class-definition modules") and the cycle collapses to the no-source-edit path (shape #5: cycle diff against `CYCLE_BASELINE` is empty, no High/Medium, no edit to any tracked file).

### DRY recap

- **Existing patterns reused.** The module is the canonical bottom-of-import-graph exception home (`exceptions.py:11-48`); `ConfigurationError` (`exceptions.py:20`) and `OptimizerError` (`exceptions.py:33`) are imported across the package (e.g. `conf.py` reads `ConfigurationError`) rather than redefined, and `SyncMisuseError` multiple-inherits `ConfigurationError` per the GLOSSARY contract — the single base hierarchy is reused, not duplicated.
- **Duplication risk in the current file.** None — three empty class bodies; no repeated literals (shadow: 0 repeated string literals) and no near-copy structure beyond the intentional shared base class.

### Other positives

- Module docstring (`exceptions.py:1-6`) correctly states the dependency discipline: no Django, no Strawberry, no internal imports, so the hierarchy can be raised anywhere without circulars. Verified against the shadow "Imports: None" section.
- `__all__` (`exceptions.py:8`) is sorted and complete — all three public classes exported, nothing extra.
- Docstrings are accurate to current behavior: `ConfigurationError`'s examples (missing `Meta.model`, `fields`/`exclude` collision, deferred-surface keys, duplicate model registration) and `OptimizerError`'s two raise-site families (the `FieldMeta.from_django_field` typed input-guard and the strictness-`"raise"` N+1 guard covering both the list-relation resolver and the nested-connection window-partition path) match the documented contracts in `docs/GLOSSARY.md` (inline `OptimizerError` references at GLOSSARY.md:884, 1279, 1283).
- GLOSSARY drift check: `ConfigurationError` has a dedicated, consistent entry (GLOSSARY.md:230); `OptimizerError` and `DjangoStrawberryFrameworkError` have no dedicated entries, and all inline `OptimizerError` mentions agree with the docstring — no stale prose on a documented contract symbol.

### Summary

`exceptions.py` is a pure-class-definition module: three empty-bodied exception classes under a single base, a complete sorted `__all__`, and an accurate docstring documenting its deliberate bottom-of-graph position. It qualifies as a skip artifact (shape #2) and produces zero source edits, collapsing to the no-source-edit cycle (shape #5). No DRY opportunities, no High/Medium/Low findings, no GLOSSARY drift, both ruff runs clean.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 267 files left unchanged.
- `uv run ruff check --fix .` — pass, all checks passed (COM812-vs-formatter warning is the standing repo config notice, not a finding).

### Notes for Worker 3
Skip artifact (shape #2) collapsing to no-source-edit cycle (shape #5). Cycle diff `git diff 756727858c3e82cfcb772f3ab4f306589a33d9ad -- django_strawberry_framework/exceptions.py` is empty (file unchanged since baseline). All severities `None.`; the single DRY bullet is the justified `None`. No GLOSSARY-only fix in scope — `ConfigurationError`'s dedicated entry (GLOSSARY.md:230) and the inline `OptimizerError` references are accurate to the docstrings; `OptimizerError` and `DjangoStrawberryFrameworkError` have no dedicated entries to drift. Static helper skipped per worker-1.md pure-class-definition allowance (no shadow regeneration).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

**Not warranted** — no source, test, GLOSSARY, or behavior change in this cycle (no-source-edit). AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed." The active plan (`docs/review/review-0_0_10.md`) names only the review artifact, with no changelog action.

---

## Verification (Worker 3)

### Logic verification outcome
No High/Medium/Low findings to adjudicate — all severities `None.`. Skip-artifact qualification (shape #2) independently confirmed: source re-read shows only a module docstring, a sorted `__all__`, and three empty-bodied exception classes (`DjangoStrawberryFrameworkError`, `ConfigurationError`, `OptimizerError`) with docstrings only — zero imports, zero module-level functions, zero executable code outside class bodies. Cross-checked against shadow `docs/shadow/django_strawberry_framework__exceptions.overview.md` (imports: 0, symbols: 3 all class defs, executable marker lines: 0, calls of interest: 0, repeated string literals: 0). Static-helper skip is correct per worker-1.md pure-class-definition allowance.

Docstring contracts spot-checked live, not trusted: `OptimizerError`'s two raise-site families resolve to real sites — `optimizer/field_meta.py:156` (the `FieldMeta.from_django_field` typed input-guard) and the strictness-`"raise"` N+1 guard at `types/resolvers.py:188` (list-relation resolver) plus `optimizer/plans.py:567`/`:575` (single-valued forward relation / nested-connection window-partition path). `ConfigurationError`'s examples align with its dedicated GLOSSARY entry (`#configurationerror`).

### DRY findings disposition
DRY=`None` is sound: three empty class bodies, no repeated literals (shadow: 0), the single base hierarchy is the canonical exception home reused across the package (`field_meta.py`, `resolvers.py`, `walker.py`, `plans.py` all `from ..exceptions import`), not duplicated. No carry-forward.

### Temp test verification
- None used — no-source-edit cycle; no behavior to pin.
- Disposition: n/a.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` and marks the checklist box.

Shape #5 checks: (1) `git diff CYCLE_BASELINE -- django_strawberry_framework/exceptions.py` empty; `--stat` over `django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty — no dirty paths to attribute to sibling cycles. (2) Each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.` (3) No Low findings, no GLOSSARY-only fix. (4) Changelog `Not warranted` cites both AGENTS.md and the active plan's silence; `git diff -- CHANGELOG.md` empty. (5) `uv run ruff format --check` + `ruff check` both clean. Internal-only framing correct — no public-API surface changed.

---

## Iteration log

(none)
