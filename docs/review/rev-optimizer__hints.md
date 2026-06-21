# Review: `django_strawberry_framework/optimizer/hints.py`

Status: verified

## DRY analysis

- None — the module is itself the DRY resolution: `hint_is_skip` (`optimizer/hints.py::hint_is_skip`) single-sources the `hint is OptimizerHint.SKIP or hint.skip` dispatch consumed verbatim by `optimizer/walker.py::_apply_hint` (`walker.py:687`), `optimizer/walker.py` connection-sibling skip (`walker.py:1331`), and `optimizer/extension.py` schema audit (`extension.py:1045`); the four `__post_init__` rejection messages are distinct user-facing strings (static overview reports 0 repeated literals), and the four factory classmethods are one-line constructors with no shareable body.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `hint_is_skip` (`optimizer/hints.py::hint_is_skip`) is the single source of the skip-shape contract: callers at `optimizer/walker.py:687`, `optimizer/walker.py:1331`, and `optimizer/extension.py:1045` all route through it rather than re-spelling `hint is OptimizerHint.SKIP or hint.skip`. The validation contract is single-sited in `__post_init__` (`optimizer/hints.py:71-106`); the walker's `_apply_hint` priority order (`walker.py:684-685`) explicitly defers collision arbitration to `__post_init__` ("documentation, not collision arbitration"), so the conflict rules are not duplicated across the two modules.
- **New helpers considered.** A shared factory body for `select_related()` / `prefetch_related()` / `prefetch(obj)` was considered and rejected — each is a single distinct `cls(...)` call with a different keyword, so a wrapper would add indirection without removing a line.
- **Duplication risk in the current file.** The four `ConfigurationError` messages in `__post_init__` share the `OptimizerHint`/factory vocabulary but each describes a distinct rejected combination; they are intentional sibling diagnostics, not near-copies. `force_select` / `force_prefetch` / `prefetch_obj` / `skip` appear across the dataclass, `__post_init__`, the factories, and `_apply_hint` as the field-name vocabulary of one contract — that is the shared shape, not duplication.

### Other positives

- **Construction-time fail-loud contract.** `__post_init__` rejects every shape outside the four documented ones at `OptimizerHint(...)` time, surfacing mistakes at `Meta.optimizer_hints` build time rather than query time. `frozen=True` keeps instances immutable so the shared `SKIP` sentinel is safe to alias across types.
- **`hint_is_skip` defensive `getattr(hint, "skip", False)`** (`optimizer/hints.py:150`) preserves the schema audit's "never raises" contract for a hypothetical future hint surface lacking `.skip`, while the `hint is None` early return keeps the audit's `hints.get(field_name)` probe path clean.
- **Runtime `Prefetch` import is justified inline** (`optimizer/hints.py:33-37`): the comment documents that the `isinstance(..., Prefetch)` check in `__post_init__` (`hints.py:97`) is the load-bearing reason it cannot sit under `TYPE_CHECKING`. The `# type: ignore[misc]` on the `SKIP` rebind (`hints.py:159`) is similarly documented (`hints.py:153-158`).
- **GLOSSARY in sync.** `docs/GLOSSARY.md` `## OptimizerHint` (931-955) accurately mirrors the four supported modes and all four `__post_init__` rejection rules (`skip` + any other flag; `force_select` + `force_prefetch`; `prefetch_obj` + either force flag; non-`Prefetch` `prefetch_obj`). `Meta.optimizer_hints` (824-847) and the connection / schema-audit / strictness cross-references describe `OptimizerHint.SKIP` behavior consistent with source. No drift on this public-contract symbol.

### Summary

`hints.py` is the `OptimizerHint` typed-wrapper plus the `hint_is_skip` skip-shape primitive. Per-cycle baseline `78366bb9` and HEAD `d63d77f8` both yield an empty diff for this file — no edits this cycle. Logic re-verified end-to-end: construction-time validation rejects every non-documented shape, the factories are the documented consumer API, and `hint_is_skip` single-sources the skip contract consumed by the walker (two sites) and the extension schema audit. GLOSSARY prose for the public-contract `OptimizerHint` symbol matches source with no drift. No High/Medium/Low findings; this qualifies as a no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; "289 files left unchanged".
- `uv run ruff check --fix .` — pass; "All checks passed!".

### Notes for Worker 3
- Shape #5: both `git diff 78366bb9 -- django_strawberry_framework/optimizer/hints.py` and `git diff HEAD -- …/hints.py` are empty; the file is unchanged this cycle.
- No Low findings to disposition (all severities `None.`).
- No GLOSSARY-only fix in scope — `docs/GLOSSARY.md` `## OptimizerHint` (931-955) was verified accurate against source (four modes + four `__post_init__` rejection rules), no drift, no edit needed.
- Cross-module skip-contract consumers re-confirmed: `optimizer/walker.py:687`, `optimizer/walker.py:1331`, `optimizer/extension.py:1045` all route through `hint_is_skip`.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits — the module's inline comments (runtime `Prefetch` import rationale `hints.py:33-37`; `SKIP` sentinel + `type: ignore` rationale `hints.py:153-158`; `hint_is_skip` caller-context note `hints.py:143-145`) are accurate and the docstrings match implementation. No stale TODOs (static overview: 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — zero edits to any tracked file (source, tests, GLOSSARY, CHANGELOG). AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed". Active plan `docs/review/review-0_0_11.md` is silent on any changelog entry for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / Low findings to disposition — every severity is `None.` Each Worker 2 (Worker 1-filled) section opens with `Filled by Worker 1 per no-source-edit cycle pattern.`, satisfying the shape #5 gate. Independently re-confirmed the "What looks solid" claims:

- **`hint_is_skip` single-sourcing.** `grep -rn "hint_is_skip"` shows the definition (`optimizer/hints.py::hint_is_skip`) plus exactly three consumers, all routing through it: `optimizer/walker.py` `_apply_hint` (`#"if hint_is_skip(hint):"`), the walker connection-sibling skip (`#"if hint_is_skip(hints_map.get(relation_field_name)):"`), and the extension schema audit (`#"if hint_is_skip(hints.get(field_name)):"`). `grep -rn "is OptimizerHint.SKIP or"` returns only the docstring inside `hint_is_skip` itself — zero inline skip-shape stragglers at any call site, so the DRY-None "this is the resolution" claim holds.
- **`__post_init__` collision rules (4 genuine).** Verified the four rejection branches in `optimizer/hints.py::OptimizerHint.__post_init__`: (1) `skip` + any other flag; (2) `force_select` + `force_prefetch`; (3) non-`Prefetch` `prefetch_obj`; (4) `prefetch_obj` + either force flag. All four are pinned positively by `tests/optimizer/test_hints.py::TestConflictingFlagsRejected` (`skip`+force_select / +force_prefetch / +prefetch_obj, force_select+force_prefetch, prefetch_obj+force_select / +force_prefetch) and `test_prefetch_obj_rejects_non_prefetch_value`.
- **Four hint modes.** `SKIP` sentinel (`hints.py #"OptimizerHint.SKIP = OptimizerHint(skip=True)"`), `select_related()`, `prefetch_related()`, `prefetch(obj)` — all present and test-pinned (`TestSkipSentinel`, `TestSelectRelatedFactory`, `TestPrefetchRelatedFactory`, `TestPrefetchFactory`).

### DRY findings disposition
DRY analysis is `None — the module is itself the DRY resolution`. Confirmed: the extracted skip-shape primitive has no straggler (grep above), the four `ConfigurationError` strings are distinct sibling diagnostics, and the three one-line factory classmethods have no shareable body. No carry-forward.

### Temp test verification
- No temp tests created. Verification was exhaustively achievable via grep against live source plus the existing permanent suite `tests/optimizer/test_hints.py` (pins all four rejection rules, the SKIP sentinel, the three factories, frozen immutability, and equality).
- Disposition: n/a.

### #4-vs-#5 gate (GLOSSARY accuracy)
Genuine #5, not a missed #4. `docs/GLOSSARY.md` `## OptimizerHint` is CORRECT vs live source — the four "Supported modes" bullets match the sentinel + three factories, and the "Validation" prose enumerates exactly the four `__post_init__` rejection rules in the same combinations the source raises on. No GLOSSARY edit in scope (diff empty); a GLOSSARY-only fix would have been disqualifying, and none was needed.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

Zero-edit proof (shape #5): `git diff 78366bb9 -- …/hints.py` empty, `git diff HEAD -- …/hints.py` empty, and the owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) is empty — no sibling-cycle attribution needed. Changelog `Not warranted` verified: `git diff -- CHANGELOG.md` empty, both citations present (AGENTS.md + active-plan silence), and the internal-only framing matches the empty diff scope.
