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

This is a **skip artifact** (REVIEW.md shape #2): the shadow overview confirms 0 imports, 3 symbols all class definitions, 0 executable marker lines, 0 calls of interest, and 0 module-level functions — so the static helper was correctly skipped per worker-1.md ("may skip for pure-class-definition modules") and the cycle collapses to the no-source-edit path (shape #5: cycle diff against the `0.0.11` baseline `f41f7ae803ba572e008202b19fe63065e7b1c453` is empty, `git diff HEAD` is empty, no High/Medium, no edit to any tracked file).

### DRY recap

- **Existing patterns reused.** The module is the canonical bottom-of-import-graph exception home (`exceptions.py::DjangoStrawberryFrameworkError` / `::ConfigurationError` / `::OptimizerError`); subclasses are imported across the package rather than redefined (e.g. `conf.py` reads `ConfigurationError`), and `SyncMisuseError` multiple-inherits `ConfigurationError` per the GLOSSARY contract — the single base hierarchy is reused, not duplicated.
- **Duplication risk in the current file.** None — three empty class bodies; no repeated literals (shadow: 0 repeated string literals) and no near-copy structure beyond the intentional shared base class.

### Other positives

- Module docstring (`exceptions.py #"Lives at the bottom of the import graph"`) correctly states the dependency discipline: no Django, no Strawberry, no internal imports, so the hierarchy can be raised anywhere without circulars. Verified against the shadow "Imports: None" section.
- `__all__` (`exceptions.py #"__all__ = "`) is sorted and complete — all three public classes exported, nothing extra.
- Docstrings are accurate to current behavior: `ConfigurationError`'s examples (missing `Meta.model`, `fields`/`exclude` collision, deferred-surface keys, duplicate model registration) and `OptimizerError`'s two raise-site families (the `FieldMeta.from_django_field` typed input-guard and the strictness-`"raise"` N+1 guard covering both the list-relation resolver and the nested-connection window-partition path) match the documented contracts in `docs/GLOSSARY.md`.
- GLOSSARY drift check clean: `ConfigurationError` has a dedicated, consistent entry (GLOSSARY.md:239-252); `OptimizerError`'s prose under Strictness mode (GLOSSARY.md:1305-1317) and all inline mentions agree with the docstring; `DjangoStrawberryFrameworkError` is an internal non-contract base with no dedicated entry — no stale prose on a documented contract symbol.

### Summary

`exceptions.py` is a pure-class-definition module: three empty-bodied exception classes under a single base, a complete sorted `__all__`, and an accurate docstring documenting its deliberate bottom-of-graph position. It qualifies as a skip artifact (shape #2) and produces zero source edits against both the `0.0.11` cycle baseline and HEAD, collapsing to the no-source-edit cycle (shape #5). No DRY opportunities, no High/Medium/Low findings, no GLOSSARY drift, both ruff runs clean.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 289 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed (the COM812-vs-formatter line is the standing repo config notice, not a finding).

### Notes for Worker 3
Skip artifact (shape #2) collapsing to no-source-edit cycle (shape #5). Cycle diff `git diff f41f7ae803ba572e008202b19fe63065e7b1c453 -- django_strawberry_framework/exceptions.py` and `git diff HEAD -- …` are both empty (file unchanged since baseline). All severities `None.`; the single DRY bullet is the justified `None`. No GLOSSARY-only fix in scope — `ConfigurationError`'s dedicated entry (GLOSSARY.md:239-252) and the `OptimizerError` prose (GLOSSARY.md:1305-1317) are accurate to the docstrings; `DjangoStrawberryFrameworkError` has no dedicated entry to drift. Static helper skipped per worker-1.md pure-class-definition allowance (no shadow regeneration; existing overview at `docs/shadow/django_strawberry_framework__exceptions.overview.md` confirms shape).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits warranted. Module and class docstrings accurately describe the raise contract and the deliberate bottom-of-import-graph placement; no stale comments, restated-code comments, or TODO anchors exist (shadow scan: 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

**Not warranted** — no source, test, GLOSSARY, or behavior change in this cycle (no-source-edit). AGENTS.md #21: "Do not update CHANGELOG.md unless explicitly instructed." The active plan (`docs/review/review-0_0_11.md`) names only the review artifact for this item, with no changelog action.

---

## Verification (Worker 3)

### Shape-#2 skip + shape-#5 zero-edit confirmation
Confirmed pure-class-definition module: `grep` shows zero `import`/`from` statements, zero module-level `def`/`lambda`, zero TODO/FIXME, and only the module docstring + `__all__` + three class definitions (`DjangoStrawberryFrameworkError`, `ConfigurationError`, `OptimizerError`) at module top level — no executable code outside class bodies, no first-party imports. Skip claim genuine; static helper correctly skipped per worker-1.md pure-class-definition allowance.

Zero-edit proof two ways: `git diff f41f7ae803ba572e008202b19fe63065e7b1c453 -- django_strawberry_framework/exceptions.py` empty AND `git diff HEAD -- django_strawberry_framework/exceptions.py` empty; `exceptions.py` absent from both the baseline and HEAD `--stat`. Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern." `git diff -- CHANGELOG.md` empty.

Owned-path stat vs baseline shows only `filters/inputs.py` and `filters/sets.py` dirty — neither is `exceptions.py`; these are sibling/concurrent work (AGENTS.md #33), not a rejection trigger for this item.

### Logic verification outcome
All High / Medium / Low `None.` confirmed genuine, not lazy:
- Canonical-home / no-redefinition claim verified: `grep -rn` shows every consumer imports `ConfigurationError` / `OptimizerError` from this module (conf.py, registry.py, relay.py, types/*, optimizer/*, mutations/*, filters/*, etc.); no subclass redefined elsewhere. `SyncMisuseError(ConfigurationError, RuntimeError)` at `utils/querysets.py::SyncMisuseError` confirms the multiple-inherit-base reuse, not duplication.
- `OptimizerError` docstring raise-site claims checked against live source: the typed input-guard at `optimizer/field_meta.py::FieldMeta.from_django_field` (`if not hasattr(field, "name") or not hasattr(field, "is_relation"): raise OptimizerError(...)`) matches the "converts an otherwise late `AttributeError` into a typed, call-site failure naming the bad input" prose verbatim; the strictness-`"raise"` N+1 guard covers both the list-relation resolver (`types/resolvers.py #"Unplanned N+1"`) and the nested-connection window-partition path (`optimizer/plans.py::window_partition_for_prefetch`, which raises for "a single-valued forward relation or any kind without a windowable parent partition") — verbatim with the docstring.

### DRY findings disposition
Single DRY bullet is the justified `None` (three empty class bodies, no repeated literals, only the intentional shared base hierarchy). Genuine — nothing to carry forward.

### GLOSSARY drift check
`ConfigurationError` has a dedicated, accurate entry (GLOSSARY.md "## `ConfigurationError`", status shipped 0.0.1, examples consistent with the docstring); `OptimizerError` prose under Strictness mode and the connection-aware section agree with the docstring; `DjangoStrawberryFrameworkError` returns zero GLOSSARY hits — an internal non-contract base with no dedicated entry to drift. No GLOSSARY-only fix owed; this is a genuine shape #5, not a missed shape #4. Changelog `Not warranted` cites BOTH AGENTS.md #21 and the active plan's silence.

### Temp test verification
None needed — no source change, no new behavior to pin.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `exceptions.py` checklist box.
