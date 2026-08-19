# Build: Slice 2 — Spec reconciliation (spec-023 multi_db)

Spec reference: `docs/SPECS/spec-023-multi_db-0_0_7.md` (whole file)
Status: final-accepted

This slice is Worker-1-exclusive by `docs/builder/BUILD.md`'s own rules — only Worker 1 may mutate the spec, and Worker 2 may never read the rationale file — so the Plan, the work, and the final-verification block were written in one pass. No Worker 2 or Worker 3 dispatch. No code change was found to be required at any point; nothing in this pass touched a source or test file.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped, same as Slice 1 and for the same reason: this slice writes Markdown and one CSV, and adds no logic to `django_strawberry_framework/`. The build plan declares `Hot-path declaration: none` and `Floor-verification scope: none` and states "No production code is planned." The package-wide AST inventory runs ~1,600 lines that no step of this slice can consume. Recorded as an explicit skip with reason, per `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning`.
- **Existing patterns reused.** The rationale file's own shape, established by Slice 1: per-Decision entries keyed by heading and anchor, a measured-populations table with the instrument named beside each figure, and an explicit moved / deleted / deliberately-not-changed ledger. Slice 2's append follows it. Slice 1's `bld-slice-1-023-rationale_extraction.md` was read and never edited.
- **New helpers justified.** None (no code). One throwaway verification script was written to the session scratchpad (`check.py` — resolves every in-page anchor against a file's own computed heading slugs, every reference id against its definitions, every definition path against disk, and every cross-file `#fragment` against the target file's real headings). It is not a repo artifact. It is worth re-writing rather than trusting a prose anchor claim: it found two broken in-page anchors nobody had reported and caught `[rationale-d7]` pointing at a stale anchor mid-pass.
- **Duplication risk avoided.** The characteristic duplication of a reconciliation pass is a corrected claim landing in the spec *and* an explanation of the correction landing beside it. Prevented structurally: every "what changed and why" sentence went into `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`'s `## Slice 2 — spec reconciliation` section, and the spec's own text was rewritten to read as though it had always been right. The post-pass check for the failure mode is that the spec contains no sentence about a previous state of the spec; `grep -c 'rev[0-9]'` on the spec still returns 0, and no `corrected`, `formerly`, `used to`, or `as of review` phrasing was introduced.

### Implementation steps

1. Re-derive every finding D1-D15 against source before acting on it; treat the build plan's list as a claim, not a measurement, and sweep for others.
2. Decide the D1 / D2 judgement call (frozen card record vs durable contract record), state it and the rejected alternative in the rationale, and apply it consistently across both halves of every split claim.
3. Fix the mechanical defects: the broken `#decision-9--joint-0_0_7-cut` anchor at every occurrence, the (f)-vs-(g) letter drift at every occurrence, the `WIP-ALPHA-019-0.0.7` card id.
4. Rewrite the drifted factual claims (`## Current state`, `### Decision 1`, `### Decision 7`, `### Decision 9`, `## Edge cases and constraints`, `## Risks and open questions`, `## Doc updates`, `## Definition of done`) to state `HEAD`.
5. Absorb the in-subject-matter behavior the spec never had (D2's fetch-time alias threading, D6's resolver-level alias re-pin) without breaking the shipped GLOSSARY's four-axis framing.
6. Clean the terms CSV's `notes` column of round attributions, preserving one row per anchor.
7. Append the Slice 2 record to the rationale, keyed to the Decisions it touches.
8. Verify: `check_spec_glossary.py` exits 0, `check_trailing_commas.py --check` exits 0 on all three files, every in-page anchor resolves in both files, every ref id resolves both ways, every definition path exists on disk, every cross-file fragment resolves.

### Test additions / updates

None. This slice adds no test and modifies no test file. The mechanical checks in step 8 stand in for tests and are recorded under `## Final verification` below. No `pytest` was run and no `--cov*` flag appears anywhere in this pass.

### Implementation discretion items

None delegated — this pass performed the work itself. The one genuinely open architectural question (what a shipped spec IS) was the pass's own to decide and is recorded with its rejected alternative in the rationale.

### Spec slice checklist (verbatim)

The spec's `## Slice checklist` has no sub-bullets for this work: its three slices are the original card's build, all of which shipped. This cycle's units come from the build plan's own `## Checklist`, so the box below is that plan's Slice 2 line, quoted.

- [x] Slice 2: Spec reconciliation — rewrite D1-D13 so the spec states the current contract, recording each change in the rationale -> `docs/builder/bld-slice-2-023-spec_reconciliation.md`

---

## Final verification (Worker 1)

### Summary

`docs/SPECS/spec-023-multi_db-0_0_7.md` now states the cooperation contract as it stands at `HEAD`, with no chronology a reader must apply. Thirty-one edits landed across fifteen spec sections plus the terms CSV; every explanation of every one of them is in `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` under a new `## Slice 2 — spec reconciliation` section keyed to the Decisions it touches. No source or test file was read for anything but verification, and none was modified.

The governing decision — recorded in the rationale with its rejected alternative — is that **the spec is the durable record of the cooperation contract, not a frozen record of what card `023` shipped**. Its own `Status:` line says so. Every factual claim about the package therefore describes `HEAD`, and later cooperation behavior inside the four axes' subject matter was absorbed into the spec body rather than left as a rationale-only footnote. The line drawn against the no-chronology rule: a version or card id appears in the spec only where a consumer needs it to use the contract; no sentence says anything about a previous state of the spec.

**Byte counts (`wc -c`, this working tree):**

| File | Before this pass | After |
|---|---|---|
| `docs/SPECS/spec-023-multi_db-0_0_7.md` | 110,831 | 113,649 |
| `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` | 84,471 | 109,189 |
| `docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv` | 2,545 | 2,679 |

The spec grew by 2,818 bytes despite deleting a falsified fallback clause and an enumerated test-module inventory: absorbing D2's fetch-time behavior and D6's resolver-level alias re-pin adds contract that was not there before. The rationale grew by 24,718 — all of it this pass's change record, none of it moved text (Slice 1 performed the only move in this cycle).

### Findings re-derived before acting — the catalog was wrong three times

Every item in the build plan's `## Pre-dispatch verification` and in Slice 1's handoff was re-measured against source. **Four of the inherited figures were wrong**, three of them understated:

| Claim as inherited | Measured this pass | Instrument |
|---|---|---|
| D14: the broken anchor has **2** uses in the spec | **7** | `grep -o '#decision-9--joint-0_0_7-cut' \| wc -l` |
| D12: the letter drift is **1** surviving `(g)`, plus a 4-site (f)/(g) disagreement | **8** letter sites total; **3** needed changing (two `(g)`->`(f)`, one `(g)`->`(e)`); the other 5 already said `(f)` | `grep -no 'test (f)\|test (g)\|(f) consumer\|Slice 1 (g)'` |
| D9: `tests/optimizer/` ships **17** test modules | **15** (plus `__init__.py` and `_builders.py`) | `ls tests/optimizer/test_*.py \| wc -l` |
| D1: `.using(` appears across **ten** package modules | **13** modules mention the token; **9** contain an actual call. Four hits are docstrings and error-message strings | `grep -rn '\.using(' django_strawberry_framework/`, read line by line |

Two more corrections to the catalog's shape rather than its counts:

- **D4 is already discharged and needs no spec edit.** The build plan says the `## Test plan` test-(e) entry quotes `RelationKind` as a four-member literal and `MANY_SIDE_RELATION_KINDS` as `{"many", "reverse_many_to_one"}`, both of which gained `"generic"` at `HEAD`. Those quotes only ever lived in the revision history Slice 1 moved out: `grep -c 'reverse_one_to_one\|MANY_SIDE_RELATION_KINDS' docs/SPECS/spec-023-multi_db-0_0_7.md` returns **0**. The spec's surviving sentence says `"forward_single"` is the right kind and `"many_to_one"` is not a member — both still true. Closed as already-discharged, with a time-scope note added to the rationale's revision-history section so a reader does not mistake rev4 V2's quoted membership for current.
- **D8 is wider than "the justification rests on a false premise".** The build plan frames it as Decision 7's *reasoning* being stale. The Decision's **normative sentence** is false at `HEAD`: it says `test_multi_db.py` copies the reload fixture verbatim, and it does not — `examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests` is the tree's single autouse definition and no module carries a private copy. That forced a Decision heading rename (below), which the catalog did not anticipate.

Three findings were discovered by this pass and assigned new ids: **D16** (the fakeshop `default` alias is no longer unconditional), **D17** (two GLOSSARY-internal in-page anchors quoted into the spec resolve nowhere from the spec), **D19/D20** (the `## Doc updates` KANBAN and CHANGELOG pins diverge from what shipped). **D18** (the `WIP-ALPHA-019-0.0.7` card id) was named in the dispatch prompt as a question and is treated as a finding here.

### The Decision 7 heading rename

`### Decision 7 — Reuse the `test_library_api` reload fixture verbatim` became `### Decision 7 — The reload fixture comes from the shared `test_query` conftest`. This is the largest structural change in the pass and the one most worth a reviewer's attention.

Justification: the Decision's own body named the condition that would justify extracting the fixture ("a `conftest.py` shared across `test_query/` files, justified once 2+ files need it") and set the boundary as "do not pre-emptively factor". The condition has been met, the extraction happened, and the module now depends on the shared fixture. The Decision's escape clause fired; the spec states the shipped source. Keeping the heading while rewriting the body was rejected — a heading contradicting its own body is worse than a stale heading, and the anchor would keep advertising the retracted answer.

Cost, paid in the same pass: 8 anchor uses in the spec and 7 in the rationale rewritten (15 total), the rationale's own heading moved with them, five dependent spec sentences rewritten, and `### Decision 6`'s pinned module header trimmed of its `importlib` / `sys` imports (they existed only to support a locally-copied reload fixture, and the shipped file does not import them). `[rationale-d7]`'s cross-file fragment was left pointing at the old anchor by the first sweep and was caught by the fragment resolver, not by reading.

### Spec changes made (Worker 1 only)

Every edit below is Slice 2. Sections are cited by heading; the finding id is the trigger.

| Spec section | Change | Reason | Finding |
|---|---|---|---|
| `Predecessors:`, `## Slice checklist` (x2), `## Doc updates` (x2), `## Risks and open questions`, `## Definition of done` item 15 | Rewrote all **7** uses of `#decision-9--joint-0_0_7-cut` to `#decision-9--joint-007-cut` | A dotted version slugs to `007`; the anchor resolved nowhere | D14 |
| `### Decision 3` axis 3, `## Risks and open questions` (x2) | `(g)` -> `(f)` twice (consumer-`Prefetch` test) and `(g)` -> `(e)` once (strictness test) | The shipped layout is six items, a-e resolver plus f optimizer; all 8 letter sites now agree | D12 |
| `## Slice checklist`, `## Doc updates` (x2), `## Definition of done` item 13 | Removed all 4 `WIP-ALPHA-019-0.0.7` occurrences; the card is `DONE-023-0.0.7` | A board state that no longer exists, requiring the reader to apply a chronology | D18 |
| `## Current state` bullet 1 | Replaced the "only explicit `router.db_for_read` call, verified by grep" claim with the four real call sites, symbol-qualified, and the axis-scope statement | The grep returns dozens of hits at `HEAD`; the scope statement survives, the expired instrument does not | D1 |
| `## Current state` settings bullet | Named the two `default`-alias overrides (`DJANGO_STRAWBERRY_KANBAN_DB`, `FAKESHOP_PG_DSN`) and kept the additive property the contract rests on | `default → db.sqlite3` is no longer unconditional | D16 |
| `## Current state` read-time bullet | "not exercised by any existing test — Slice 2 closes that gap" -> states the live tests exercise it | The gap closed when the card shipped | D9 |
| `## Current state` reload-fixture bullet | Re-pointed at `test_query/conftest.py` | The fixture moved | D8 |
| `## Current state` GLOSSARY bullet | States the entry's shipped four-axis body and names it as the shipped statement of the contract | The status flip landed | D9 |
| `## Current state` `tests/optimizer/` bullet | Deleted the seven-filename inventory; states the durable structural fact instead | 15 modules now; a filename list re-rots every card | D9 |
| `## Current state` version bullet | Names the three files that move together without quoting `0.0.6`; states the joint-cut ownership | All three pin `0.0.14` | D9 |
| `## Goals` item 1 | Archived path; axis-3 clause qualified to plan-time with the alias-late boundary; closing sentence reworded | D2 + the archive already ran | D2, D11 |
| `## Goals` item 3 | "containing **two** tests" -> "with **two** tests" | The module holds ten | D7 |
| `## Key glossary references`, `## Problem statement` | Axis-3 sentence qualified to plan-construction time with the alias-late clause | D2 | D2 |
| `## Slice checklist` live-test bullet | States what this contract contributes to the module rather than what the module contains | The module holds ten tests | D7 |
| `## Slice checklist` reload bullet | Points at the shared conftest fixture | D8 | D8 |
| `## Slice checklist` GLOSSARY bullet | Dropped "currently" and the quoted stale status cell | A claim about `HEAD` that is false | D9 |
| `## User-facing API` `get_queryset` bullet | Added the alias-late fetch-time paragraph and the `_visible_related_object` re-pin sentence | D2 + D6 | D2, D6 |
| `### Decision 1` | Rewrote: the file is archived at `docs/SPECS/`, companions at `docs/SPECS/appx/`; the lifecycle note is now a general rule, not a prediction | The archive has run | D11 |
| `### Decision 3` axis 3 | Rewrote: no alias in the plan, why that is deliberate, and the two fetch-time pinning sites by symbol-qualified path; out-of-scope narrowed to shard-aware *planning* | The flat boundary was never wrong about the plan and always incomplete about the fetch | D2 |
| `### Decision 3`, closing paragraph (new) | Added the `_visible_related_object` alias re-pin as an instance of the alias-late principle, explicitly not a fifth axis | Cooperation behavior in the contract's subject matter that appeared nowhere; "four axes" is load-bearing in the shipped GLOSSARY and CHANGELOG | D6 |
| `### Decision 6` pinned header | Dropped `importlib` / `sys`; rewrote both annotations | The reload work belongs to the shared conftest fixture; the import list is not a ceiling on the module | D7, D8 |
| `### Decision 7` | Renamed the heading and rewrote the body; 15 anchor uses across both files rewritten | The normative sentence is false at `HEAD`; the Decision's own extraction condition fired | D8 |
| `### Decision 9` | Removed the two-card roster and `DONE-025-0.0.7` "still in flight"; states the policy only | The bundle shipped 2026-05-27 with seven cards, tag `0.0.7` at `72f6cd9` | D10 |
| `## Edge cases and constraints` null-FK bullet | Names all three pre-router exits including `_FK_ELISION_UNSAFE` | The body gained an earlier exit | D5 |
| `## Edge cases and constraints` signature bullet | Added keyword-only `runtime_prefixes` to the pinned signature | `optimizer/walker.py::plan_optimizations` | D3 |
| `## Edge cases and constraints` `Prefetch` bullet | Plan-time qualifier plus the alias-late pointer | D2 | D2 |
| `## Test plan` live section | "**Two** tests" -> "**Two** tests from this contract"; existing-tests note re-pointed at the shared conftest | D7, D8 | D7, D8 |
| `## Doc updates` GLOSSARY pin | Two GLOSSARY-internal in-page anchors re-relativized to the spec's own `[glossary-*]` ref ids; pinned text unchanged | They resolved nowhere from the spec | D17 |
| `## Doc updates` KANBAN pin | Replaced the free-prose Done body with the card's four real obligations against the DB-rendered card structure | `KANBAN.md` is generated; that shape was never renderable | D19 |
| `## Doc updates` CHANGELOG pin | Intro rewritten (joint-cut framing, live card ids); the one prose divergence aligned to the shipped bullet | The pin claimed something false about `CHANGELOG.md` | D20 |
| `## Risks and open questions` bullet 1 | States the standing joint-cut hazard without quoting a date or version; the never-fired `0.0.8` fallback **deleted** | `## [0.0.7] - 2026-05-27`, package at `0.0.14`; the contingency resolved against the fallback | D9 |
| `## Risks and open questions` bullet 2 | Reworded to name the canonical stem rather than an active path | D11 | D11 |
| `## Risks and open questions` generated-`Prefetch` bullet | Plan-time framing; fallback re-scoped to plan-time alias resolution | The old fallback describes behavior the package now has | D2 |
| `## Out of scope` | Deferred item re-scoped from "threading the parent `_db` into generated child querysets" to "resolving a generated child's alias at plan-construction time"; `DONE-025-0.0.7` wording de-staled | The package threads the alias at fetch time | D2, D10 |
| `## Definition of done` items 1, 3, 13 | Archived paths for the spec and CSV; "contains the 2 tests" -> "carries"; item 13 rewritten against the real card structure | D11, D7, D19 | D11, D7, D19 |
| Link definitions | Added `[filters-sets]`, `[permissions]`, `[single-parent-fetch]`, `[write-transaction]`, `[test-query-conftest]`; removed `[test-library-api]`, orphaned by the Decision 7 rewrite | Every new source reference needs a resolvable def; groups kept alphabetical | D1, D2, D8 |
| `docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv` | Two `notes` cells de-attributed (`rev2 H2`, `rev2 H6`); three sibling-card ids corrected from pre-renumber `DONE-016/017/018`; the `Multi-database cooperation` note now describes the term's role rather than the status flip | The `notes` column describes the term, not the round that produced the wording | D15 |

### Mechanical verification

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-023-multi_db-0_0_7.md` -> `OK: 18 terms - all have glossary entries and at least one spec link.` exit 0. Unchanged from Slice 1's close. The three joint-cut terms (`DjangoListField`, `Django AppConfig`, `Schema export management command`) were the ones at risk, because the `## Doc updates` CHANGELOG-pin rewrite touched one of their link sites; all three survive there and in `## Current state`.
- `uv run python scripts/check_trailing_commas.py --check` on the spec, the rationale, and the terms CSV -> exit 0.
- In-page anchors, both files: every `](#…)` resolved against the file's own computed heading slugs. **0 unresolved**, down from 3 distinct broken targets over 9 occurrences.
- Reference ids, both files: `used-not-defined: []`, `defined-not-used: []`, with code spans and fenced blocks stripped before scanning.
- Every link-definition path in both files disk-exists-checked -> 0 missing. Every cross-file `#fragment` resolved against the target file's real headings -> 0 unresolved (this is the check that caught `[rationale-d7]` mid-pass).
- Terms CSV grammar: `awk -F',' 'NR>1{print $2}' … | sort | uniq -d` returns empty over all 18 rows — one row per anchor, which is what `import_spec_terms` requires.
- `grep -c 'rev[0-9]'` -> **0** on the spec and **0** on the terms CSV. No `path:NN` line reference was introduced in the spec, the rationale, or the CSV.
- No `pytest`. No `--cov*` flag. No source or test file modified. No commit, no branch, no `git stash` / `checkout` / `restore`.

### Concurrent-session state

The tree was dirty throughout with another session's `spec-021` / `spec-022` cycle. During this pass that session deleted `docs/builder/bld-integration.md`, `bld-review-1-rationale_and_spec_reconciliation.md`, and `bld-review-2-db_backed_doc_reconciliation.md`, modified `docs/builder/bld-final.md` and `build-021-apps-0_0_7.md`, and `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` went from untracked to absent while `spec-021-apps-0_0_7-terms.csv` went dirty. None of it was touched, reverted, or read for content beyond `git status`. Nothing in this cycle's writable set was affected: the only dirty paths this pass produced are `docs/SPECS/spec-023-multi_db-0_0_7.md`, `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`, `docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv`, and this artifact.

### Notes for the next pass (integration)

- **The rationale is now 109KB against a 114KB spec.** Worker 3 reads it during review and Worker 1 owns it; Worker 2 must never be handed it. Nothing in this pass changes that routing, but the integration pass should confirm the build plan's dispatch note still says so.
- **`## Implementation plan`'s line-delta table was checked and deliberately left.** Its figures are a planning estimate, the shipped delta is not measurable as one number (the card landed across several commits; the largest, `3bc2330b`, mixes it with two siblings' artifacts, and all three files have since been rewritten by later cards). Reasoning is in the rationale's `### Deliberately not changed`.
- **Every `- [ ]` checkbox in the spec was left unticked.** The `Status:` line is the source of truth for a shipped card; this is the house convention and not an oversight.
- **No code change was required and none was made.** Worker 0's finding stands after independent re-derivation: the ship commit matched the spec, and every divergence found in this cycle is post-ship drift in the document.
