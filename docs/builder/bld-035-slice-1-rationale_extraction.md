# Build: Slice 1 — Spec rationale extraction

Spec reference: `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (whole file; the move touched lines 11-16, 144-152, 161-163, 178-184, 203-210, 220-222, 243-251, 267-270, 271, 273, 280-285, 291-293, 406-416 and the `<!-- docs/SPECS/ -->` link-definition group, all pre-move numbering)
Status: final-accepted

**Procedural-closure slice** (`BUILD.md` `### Procedural-closure slices`): Worker 1 only, no source diff, so no Worker 2 build and no Worker 3 review. This artifact carries one combined Plan + Final-verification block. The authorizing clause is `BUILD.md` `## Spec rationale extraction` — "the first substantive action of every build" — performed retrospectively per the maintainer's instruction in `docs/builder/build-035-optimizer_hardening-0_0_10.md` `## Cycle framing`, because the original `DONE-035-0.0.10` cycle never ran pre-flight step 7.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped: `worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper planning*, and this slice proposes no helper, constant, validation branch, coercion utility, or test helper. It writes two Markdown files and no `.py` at all (`django_strawberry_framework/` is untouched — `git status --short django_strawberry_framework/` is empty for this slice).
- **Existing patterns reused.** The rationale companion's shape is copied from the two immediately-preceding executions of the same move: `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md:1-47` (header, `## Provenance of this record`, `## Revision history`, per-Decision `### Justification (moved from the spec)` / `### Alternatives considered (and rejected)` / `### Changes this Decision underwent`, `## Risks and open questions`, `## Non-Decision deliberation`) and `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md:1-20` (the byte-accounted provenance paragraph and the census-grammar note). The spec-side pointer wording is `docs/SPECS/spec-034-permissions-0_0_10.md:11` (header pointer), `:219` etc. (per-Decision pointer), `:491` (Risks pointer). Link-definition relativity from `docs/SPECS/appx/` is copied from `spec-034-permissions-0_0_10-rationale.md:365-436`.
- **New helpers justified.** None. One *new section* is justified — `## Post-ship divergences (spec vs. HEAD)` in the rationale file — because this cycle owes a keyed home for the build plan's six enumerated deviations plus this pass's status-line finding, and `spec-034`'s per-Decision `**Post-ship:**` bullet shape would scatter seven entries that Slice 3 must read as one list. Entries are keyed to the owning Decision by reference-style link, so the `BUILD.md` "every entry names the spec decision it belongs to" rule still holds.
- **Duplication risk avoided.** A rationale move's characteristic duplication is text that ends up in *both* files. Two guards were applied: (a) a mechanical check that every moved chunk is absent from the post-move spec, and (b) a mechanical check that every moved chunk is present byte-verbatim in the rationale file. One real duplicate was caught by (a)/(b) together — Decision 5's closing `Pinned by test_fk_id_elision_enabled_under_mutation ... and test_fk_id_elision_falls_back_when_consumer_only_defers_fk ...` sentence, which is a test pin rather than a rejected alternative and therefore stays in the spec; it was removed from the rationale file's Decision-5 block and recorded in that file's held-back list.

### Implementation steps

1. Census the deliberative layer in `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` across three grammars: `grep -n 'Justification\|Alternatives considered'` (18 hits), `grep -oni 'evision'` (18 hits — the case-insensitive short token, which also catches `Revision history` with no digit), and a chronology-vocabulary sweep for `earlier draft|original draft|first draft|superseded|was **wrong**|as of revision` (9 hits).
2. Extract the moved chunks byte-exactly by line range into a scratch dump, so the rationale file is assembled from the spec's own bytes rather than retyped.
3. Build `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md`: header + `## Provenance of this record` + `## Revision history` + nine `## Decision N` sections + `## Risks and open questions` + `## Post-ship divergences (spec vs. HEAD)` + `## Non-Decision deliberation` + the link-definition block with all ten canonical group headers.
4. Re-point the eight in-page anchors naming spec-only sections (`#borrowing-posture`, `#current-state`, `#definition-of-done`, `#out-of-scope-explicitly-tracked-elsewhere`, `#problem-statement`, `#reference-package-parity-checkpoint`, `#slice-checklist`, and the G3 deferred test-plan heading) at the spec through reference-style links; leave `#decision-N--...` and `#risks-and-open-questions` alone, since this file carries headings with exactly those slugs.
5. Apply the removals to the spec bottom-up (so earlier line indices stay valid), insert the one-line pointers, apply the eleven inline chronology strips, and add the eleven new `<!-- docs/SPECS/ -->` link definitions in alphabetical position.
6. Verify mechanically (see `## Final verification`), not by reading.

Line numbers above are pin-at-write-time navigational hints against the **pre-move** spec; the post-move file is 44 lines shorter.

### Test additions / updates

None, and none are possible: this slice writes no `.py`. The verification instruments are `scripts/check_spec_glossary.py`, `scripts/check_trailing_commas.py --check`, and the four ad-hoc mechanical checks recorded under `## Final verification`. No temp tests.

### Implementation discretion items

None. This slice has one worker and no build pass to delegate to.

### Spec slice checklist (verbatim)

Not applicable. This slice implements a `BUILD.md` pre-flight step, not a spec `## Slice checklist` sub-bullet — the spec's checklist covers Slices 1-4 of the shipped `DONE-035-0.0.10` card, all of which are already ticked or marked deferred, and none of which this cycle re-opens. The governing obligations are `BUILD.md` `## Spec rationale extraction` and `worker-1.md` `### Performing the rationale move`, audited below.

---

## Final verification (Worker 1)

- **Spec slice checklist:** not applicable (above). The five `worker-1.md` `### Performing the rationale move` rules are audited item by item under `### Rationale-move rule audit`.
- **DRY check across this slice and prior accepted slices:** this is the cycle's first slice; no prior accepted slice exists to duplicate. The intra-slice duplication guard is recorded under `### DRY analysis` and caught one real duplicate.
- **Existing tests still pass:** no test scope applies — the slice's diff is two `.md` files, and `AGENTS.md` forbids a `pytest` run that nothing in the diff could affect. No `--cov*` flag was passed to anything.
- **Spec reconciliation:** the spec was edited by this slice for the move only. Substantive claim corrections are Slice 3's and are catalogued under `### Notes for Worker 1 (spec reconciliation)`.
- **Final status:** `final-accepted`.

### Byte count, before and after

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` | 143,045 bytes / 542 lines | 117,931 bytes / 498 lines | **−25,114 bytes / −44 lines** |
| `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md` | absent | 57,185 bytes / 311 lines | **+57,185 bytes** |

The rationale file is larger than the bytes removed because roughly 32KB of it is this pass's own framing: the header, `## Provenance of this record`, the `## Revision history` preamble, nine `### Changes this Decision underwent` sections, the whole `## Post-ship divergences (spec vs. HEAD)` section, `## Non-Decision deliberation`, and a fresh link-definition block. The spec absorbed 11 one-line pointers and 11 new link definitions against the removals, which is why its net loss is smaller than the moved text.

### Rationale-move rule audit (`worker-1.md` `### Performing the rationale move`)

1. **Every decision keeps a one-line pointer.** Nine present, one per Decision: `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md:139,148,163,182,194,215,235,242,248` (post-move numbering), each of the form `Rationale companion — this Decision's justification and its <N> rejected alternatives: [Decision N][rationale-dN].` Decision 7's names the retracted claim as well. The header carries the whole-file pointer at `:11`; `## Risks and open questions` carries its own at `:361`.
2. **Delete — do not move — falsified prose.** One deletion: the `Revision history (kept inline so the spec is self-contained):` preamble line, whose claim the move itself makes untrue. Everything else was moved, because nothing else in the deliberative layer is falsified *as chronology* — the seven statements this cycle found false are false about the **repo**, and those live in surviving contract prose, which Slice 3 owns. That distinction is recorded in the rationale file's `## Post-ship divergences (spec vs. HEAD)` preamble.
3. **The rationale file is keyed to the spec.** Every one of the nine Decision sections opens with `Spec: [<full decision title>][spec-035-dN].`, and the nine link definitions resolve to `../spec-035-optimizer_hardening-0_0_10.md#decision-N--...`. Each carries `### Justification (moved from the spec)`, `### Alternatives considered (and rejected)`, and `### Changes this Decision underwent`. Every `## Post-ship divergences` entry names its owning Decision or spec section by reference-style link. No entry names no decision.
4. **Verify the move; do not assume it.** Six mechanical checks, all run, all recorded under `### Mechanical verification` below.
5. **Tracked and durable.** `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md` is a new tracked file under `docs/SPECS/appx/`, beside the spec's existing `-terms.csv` companion. Nothing about it is scratch.

### Mechanical verification

| Check | Command / method | Result |
|---|---|---|
| Glossary gate still green | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` | `OK: 23 terms - all have glossary entries and at least one spec link.` exit 0 (unchanged from pre-flight step 6's `OK: 23 terms`) |
| Markdown scaffold / link-def convention | `uv run python scripts/check_trailing_commas.py --check` on both files | exit 0 |
| In-page anchors resolve | Slugged every heading in each file, differenced against every `](#anchor)` use | Spec: one dangling anchor, `#slice-2--g2-testsoptimizertest_walkerpy--testsoptimizertest_extensionpy-extend`, **pre-existing** — the identical check against the pre-move copy reports the same single hit. Rationale file: zero. No anchor this move removed is still referenced. |
| Reference-style link ids | Differenced `[text][ref-id]` uses against `[ref-id]:` definitions in both files | Spec: zero used-not-defined, zero defined-not-used (11 defs added, none orphaned). Rationale file: zero / zero, after pruning 14 defs the assembled body did not use. |
| Link-definition targets exist on disk | Resolved every non-URL def in the rationale file relative to `docs/SPECS/appx/` | All resolve. `[bld-035-slice-1]` pointed at this artifact and resolved once this file was written. |
| Move is a move, not a copy | (a) every extracted chunk absent from the post-move spec; (b) every extracted chunk present byte-verbatim in the rationale file, modulo the stripped inline labels and the eight re-pointed anchors | (a) zero chunks still in the spec; (b) zero chunks missing. One duplicate found and resolved before this run — see `### DRY analysis`. |

Also verified by hand: the ten canonical link-definition group headers are present and in `START.md` order in both files, and the new `[rationale-d1..d9]` / `[rationale-risks]` / `[spec-035-rationale]` defs sit under `<!-- docs/SPECS/ -->` in alphabetical position (the companion lives at `docs/SPECS/appx/`, which shares its parent's group per `START.md`). No double blank lines in either file.

### Summary

Cut the spec's deliberative layer into a new tracked companion, `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md`. Four routes carried text out: the whole inline `Revision history` block (preamble deleted, four entries moved); nine `Justification:` blocks and nine `Alternatives considered (and rejected):` blocks under Decisions 1-9 (12 justification bullets or paragraphs, 21 rejected alternatives); the whole `## Risks and open questions` body (preamble plus nine preferred-answer / fallback items); and eleven sites of amendment or retraction framing — nine chronology tags stripped from sentences that survive, and Decision 5's two draft-history parentheticals — plus Decision 7's whole `(An earlier draft of this Decision claimed ... that was **wrong** ...)` retraction, which moved entire.

Six passages were **held back** under the implementation-relevant carve-out and stayed in the spec, each named in the rationale file's provenance section: Decision 4's four-projection-writer enumeration and *why* each must consult the gate; Decision 5's consumer-`.only()` hazard mechanism; Decision 6's both-arms-required and tri-state-not-boolean requirements; Decision 3's two-directional placement argument; every cache-safety argument; and Decision 5's two-test pin sentence.

The rationale file also carries `## Post-ship divergences (spec vs. HEAD)`, seeded with all seven divergences this cycle owes — the build plan's six, re-derived against `HEAD`, plus this pass's status-line finding — each keyed to the Decision or spec section that owns the correction. **No substantive spec claim was corrected this pass**; Slice 3 owns that, and reads that section as its inbox.

### Spec changes made (Worker 1 only)

Every edit below is the move itself. Pre-move line numbers.

| Spec lines | Section / heading | Slice | Change and reason |
|---|---|---|---|
| 11-16 | Header, `Revision history` block | 1 | Preamble line **deleted** (its "kept inline" claim is what the move falsifies); Revisions 1-4 **moved** to the companion; replaced by the whole-file deliberative-layer pointer, matching `spec-034`'s header pointer. |
| 144-152 | `### Decision 1` | 1 | `Justification:` + `Alternatives considered (and rejected):` moved; one-line pointer inserted. |
| 161-163 | `### Decision 2` | 1 | Same. |
| 178-184 | `### Decision 3` | 1 | Same. The two-directional placement argument in the Decision body was **held back** — it states where the guard must sit and what breaks on either side. |
| 203-210 | `### Decision 4` | 1 | Same. The four-projection-writer enumeration and the `_project_scalar_only_window`-never-lands-in-`only_fields` sentence in the Decision body were **held back**: a builder who never reads them writes the leaking version, which is the rejected alternative that moved. |
| 220-222 | `### Decision 5` | 1 | `Justification:` and the two rejected alternatives moved. The block's closing two-test `Pinned by ...` sentence was **held back** and promoted to its own paragraph, because it is a test pin, not an alternative. |
| 243-251 | `### Decision 6` | 1 | `Justification:` + five rejected alternatives moved; both-arms-required and tri-state-not-boolean requirements **held back** in the Decision body. |
| 267-270 | `### Decision 7` | 1 | `Justification:` + one rejected alternative moved. |
| 273 (tail) | `### Decision 7` | 1 | Pointer inserted at the Decision's end rather than at the removal site, so it follows the reachability and maintainer-decision paragraphs the reader needs first. |
| 280-285 | `### Decision 8` | 1 | `Justification:` + two rejected alternatives moved; pointer inserted. |
| 291-293 | `### Decision 9` | 1 | Same. |
| 406-416 | `## Risks and open questions` | 1 | Preamble + all nine items moved; heading kept with a pointer, following `spec-033` / `spec-034`. Nothing held back: no item carries a rule the implementation depends on, and the two card-citation corrections' conclusions already live in Decisions 3 and 6. |
| 3 | Header sentence | 1 | Stripped `, as reconciled in Revision 4,` — the spec may not narrate its own history. |
| 57 | `## Slice checklist`, Slice 3 row | 1 | Stripped `; Revision 3 above`. |
| 75 | `## Current state` lead-in | 1 | `A true description of the repo, reconciled to the shipped state in Revision 4:` → `A true description of the repo:`. |
| 77 | `## Current state`, first bullet | 1 | Stripped ` (Revision 3)`. |
| 156 | `### Decision 2` body | 1 | `**As of Revision 3 the card ships` → `**The card ships` — the Decision states the current scope directly. |
| 216 | `### Decision 5` body | 1 | Stripped ` (the safety hole the first draft missed)`. The hazard mechanism itself stayed. |
| 218 | `### Decision 5` body | 1 | Stripped ` (the follow-up the first draft owed)`. |
| 226 | `### Decision 6` status blockquote | 1 | Stripped ` (Revision 3)` from `A production-reachability review ... established`. |
| 253 | `#### Carry-forward requirements for the follow-up card` | 1 | Stripped ` (added in Revision 3)` from the heading. Verified no in-page anchor referenced that heading, so nothing dangles. |
| 271 | `### Decision 7`, reachability paragraph | 1 | Removed the whole `(An earlier draft of this Decision claimed ... requirement R1 in Decision 6.)` retraction parenthetical; it moved to the companion under Decision 7. The surrounding reachability contract stayed. |
| 273 | `### Decision 7`, maintainer-decision line | 1 | `**Decision (maintainer, Revision 3):` → `**Decision (maintainer):`. |
| link defs | `<!-- docs/SPECS/ -->` | 1 | Added `[rationale-d1]`-`[rationale-d9]`, `[rationale-risks]`, and `[spec-035-rationale]`, all pointing into `appx/spec-035-optimizer_hardening-0_0_10-rationale.md`, in alphabetical position within the group. |

**Deferral reasons.** Nothing in this slice's obligation set is deferred. Everything the spec still says that the repo has falsified is routed to Slice 3 with a named owner, below — that is the cycle's declared partition, not a deferral out of this artifact.

### Notes for Worker 1 (spec reconciliation)

Slice 3's inbox. Every item below is a **substantive spec claim** this pass deliberately did not touch; the explanation for each already sits in the rationale file's `## Post-ship divergences (spec vs. HEAD)` section, so Slice 3 writes the correction into the spec directly and without chronology, and appends nothing new to the companion unless it finds something this pass missed.

**Status-line re-verification (`worker-1.md` `## Spec status-line re-verification`).** Read the post-move spec's lines 1-11. Title, `Status:`, `Owner:`, and `Predecessors:` are accurate at `HEAD`. Two header-adjacent claims are not:

- **The spec's own location, at four sites (post-move lines 137, 357, 380, 406).** `### Decision 1` (`:137`) states "The spec file lives at **`docs/spec-035-optimizer_hardening-0_0_10.md`**"; the `## Doc updates` Slice-4 card-wrap bullet (`:357`) pins the card's `SpecDoc` to the "**live** working path"; `## Definition of done` item 1 (`:380`) carries the stale path twice, once as prose and once *inside a `--spec` argument*, so the verification command as written exits 2 with a missing-file error; and DoD item 10 (`:406`) repeats the live-working-path claim. Revision 4 recorded the same intent (that entry now lives in the companion, where as dated chronology it stands). The `docs/SPECS/NEXT.md` Step 8 batched sweep has since run: the spec is at `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`, its `-terms.csv` and the new `-rationale.md` at `docs/SPECS/appx/`. Slice 3 fixes all four, and `spec-034`'s Decision 1 (`docs/SPECS/spec-034-permissions-0_0_10.md:217`) is the wording precedent. Note the KANBAN `SpecDoc` DB row is **out of this cycle's scope** (spec `.md` + `.py` only, no DB writes) — the spec's prose is what Slice 3 corrects.
- **`__version__` is `0.0.15`, not `0.0.9`.** The header's closing parenthetical reads "the on-disk version reads `0.0.9` as of this writing — the `0.0.9` cut has landed". It self-dates, so `BUILD.md` `### `## Current state`: observations stand, predictions do not` arguably licenses it; but it sits in the header rather than in `## Current state`, and `CHANGELOG.md:99` now carries `## [0.0.10] - 2026-06-16`, which the same sentence's `Status:` sibling already states. Slice 3's call: keep it dated or drop it. Low severity, flagged so it is judged rather than inherited.

**The six post-ship divergences** (build plan `### Deviations later work introduced`, re-derived against `HEAD` by this pass; full evidence in the companion):

1. `_project_scalar_only_window` is defined in `django_strawberry_framework/optimizer/nested_planner.py:652`, not `walker.py`; `walker.py:81` keeps a module-level alias. Commit `991d5120`. The spec cites `walker.py::_project_scalar_only_window` in eight places, one of them the held-back Decision 4 enumeration.
2. Decision 5's "falls back **loudly** ... so strictness sees the access" is only reachable through machinery the Decision never names: `types/resolvers.py:230` `force_unplanned`, `types/resolvers.py:88` `_FK_ELISION_UNSAFE`, `types/resolvers.py:91` `_fk_attname_is_deferred`. Understated, not misstated.
3. The Slice 1 G1 live-coverage waiver is reversed: `examples/fakeshop/apps/library/schema.py:447` `all_library_branches_eager_eval` and `examples/fakeshop/test_query/test_library_api.py:388` `test_library_evaluated_queryset_not_re_executed_over_http` both exist. The waiver's "no future card makes this branch consumer-facing" clause is now false about the repo.
4. The G2 live-test handoff was discharged by the `0.0.11` mutations cohort in `examples/fakeshop/test_query/test_products_api.py`; `mutations/resolvers.py`, `forms/resolvers.py` and `rest_framework/resolvers.py` each cite the G2 gate. The spec still records it as outstanding.
5. The staged-anchor paragraph claims "three `TODO(spec-035 Slice 3)` comments"; there are five sites, only `optimizer/selections.py:381` was retargeted (commit `dd8dc0b3`), and commit `471d4c6b` stripped ` Slice 3` from the two `walker.py` anchors. Stale on both count and form. **Slice 2 fixes the four `.py` anchors** (one baseline-dirty and out of scope); Slice 3 fixes the spec sentence.
6. The `## Current state` connection-field bullet attributes `apply_connection_optimization` to `DjangoConnectionField`; it is a module-level function at `django_strawberry_framework/optimizer/extension.py:1490`, re-exported and called from `connection.py:1643`. Authoring-time imprecision, not later drift.

**One pre-existing defect this pass found and did not cause.** The spec carries a dangling in-page anchor, `](#slice-2--g2-testsoptimizertest_walkerpy--testsoptimizertest_extensionpy-extend)`, used twice. The `### Slice 2 — G2 (...)` heading it targets contains a reference-style link, so the rendered heading's slug is longer than the anchor. Verified present in the pre-move copy too. Not in this slice's writable scope to reword a heading; Slice 3 owns it if the maintainer wants it fixed, and note that renaming that heading breaks the two uses unless both are updated in the same pass.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
