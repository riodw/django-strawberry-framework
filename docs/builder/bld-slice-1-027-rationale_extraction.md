# Build: Slice 1 — Rationale extraction

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` (whole file; the move touched the preamble, all twelve Decisions, and eight non-Decision sections)
Status: final-accepted

## Plan (Worker 1)

### Worker-1-only artifact shape

This artifact carries a combined `## Plan (Worker 1)` and `## Final verification (Worker 1)` block with no Worker 2 build report and no Worker 3 review. Two clauses authorize it:

- [`BUILD.md`][build] `## Spec rationale extraction` — "Worker 1 is the only role that performs the move", and its `### Who reads it, and when` sub-section states **Worker 2 never reads** the rationale file. The `## Required reading per worker` matrix marks the active `-rationale.md` **never** for Worker 2 and `yes (owns)` for Worker 1.
- [`BUILD.md`][build] `### Procedural-closure slices` is the precedent for the shape itself: "a single Worker 1 pass that sets `Status: final-accepted` directly — no Worker 2 build, no Worker 3 review. The artifact carries one combined Plan + Final-verification block citing the spec clause that authorizes the closure."

The build plan [`build-027-filters-0_0_8.md`][build-027] declares the same partition in its preamble: "Ownership partition: none; sequential slices. Slices 1 and 3 are Worker 1's alone; Slice 2 is the only slice with a Worker 2 / Worker 3 cycle."

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped: this slice changes no executable statement and adds no helper, constant, validation branch, coercion utility, or test helper. `BUILD.md` `### Package-wide helper inventory before helper planning` gates *helper planning*; there is none to gate. No `.py` file is in this slice's writable list.
- **Existing patterns reused.** The rationale file's shape is taken from the two archived companions the brief names — `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` and `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md`: a `## Provenance of this record` block carrying measured populations and byte counts, a verbatim `## Revision history`, one `## Decision N — <spec heading text>` section per Decision with `### Justification (moved from the spec)` / `### Alternatives considered (and rejected)` / `### Changes this Decision underwent` / `### Claims this Decision may no longer make`, then the spec-wide retractions. The spec-side pointer wording (`Rationale companion — …: [Decision N][rationale-dN].`) is `spec-023`'s, reused verbatim in form.
- **New helpers justified.** None in the package. One throwaway scratch script (`apply.py` under the session scratchpad, outside the repo) applied each exact-string replacement only when its occurrence count matched the expected count, and wrote nothing on any mismatch. It is scratch, not a deliverable.
- **Duplication risk avoided.** The move's characteristic failure is a *copy* rather than a cut, leaving the same paragraph in both files. Prevented mechanically: after the pass, `grep -c '^Justification:'` and `grep -c '^Alternatives considered'` against the spec both return 0, and `rev-?[0-9]` returns 2 occurrences, both inside the single pointer sentence that names the moved history.

### Implementation steps

1. Snapshot `HEAD` read-only to the scratchpad (`git show HEAD:docs/SPECS/spec-027-filters-0_0_8.md`) so every moved block can be recovered verbatim without touching the working tree.
2. Measure the deliberative-layer populations against that snapshot before cutting anything.
3. Strip the review-round narration welded into contract prose, batch by batch, each replacement count-asserted; repair any sentence the strip leaves ungrammatical so it states the contract directly.
4. Cut the twelve `Justification:` / `Alternatives considered (and rejected):` pairs, leaving one `Rationale companion — …` pointer per Decision.
5. Cut the `Revision history (kept inline so the spec is self-contained)` block (`rev1`-`rev8`), leaving one pointer sentence in its place.
6. Write `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` incrementally — provenance, then the verbatim revision history, then the twelve Decision sections, then the non-Decision deliberation, the spec-wide retractions, and the Slice-3 hand-off.
7. Re-point both files' link-definition blocks: add `[rationale-d1]`…`[rationale-d12]` and `[spec-027-rationale]` to the spec, drop the definitions the move orphaned, and resolve every rationale-side path from `docs/SPECS/appx/`.
8. Verify: both gates, the scaffold checker, every in-page anchor, every cross-file anchor in both directions, and the byte counts.

Line numbers are pin-at-write-time navigational hints. This slice renumbered the whole spec, so any line number written before it ran is stale by construction.

### Test additions / updates

None. This slice changes no executable statement, so no test can observe it. The gates that stand in for tests here are `scripts/check_spec_glossary.py`, `scripts/check_citations.py`, and `scripts/check_trailing_commas.py --check`; all three are recorded under `## Final verification (Worker 1)`.

### Implementation discretion items

None. This slice had no Worker 2 to delegate to.

### Spec slice checklist (verbatim)

The spec's own `## Slice checklist` has no entry for this cycle — `027` shipped as `DONE-027-0.0.8` and its six slices are all closed. This slice's contract comes from the build plan's checklist line and from `BUILD.md` `## Spec rationale extraction`. The boxes below are that contract, audited by this same pass under `## Final verification (Worker 1)`.

- [x] Create `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`.
- [x] MOVE the entire `Revision history (kept inline so the spec is self-contained)` block (`rev1` through `rev8`, every H / M / L item under each) — it leaves the spec.
- [x] MOVE every `Justification:` block and every `Alternatives considered (and rejected):` block under all twelve Decisions.
- [x] MOVE every inline review-round narration welded into contract prose, across Decision 3's Layer-5 body, Decision 4's converter table, Decision 8's step list and sync/async subsection, Decision 9's lifecycle clause, the `## Slice checklist`, `## Edge cases and constraints`, `## Test plan`, `## Risks and open questions`, and the `## Definition of done` items.
- [x] Leave behind grammatical, self-consistent contract prose; repair every sentence the removal breaks so it states the contract directly.
- [x] Key every rationale entry to the spec decision it belongs to by heading and anchor.
- [x] Carry, per decision: the alternatives rejected and why each lost; every change the decision has undergone with the round that caused it; any claim the decision once made and may no longer make.
- [x] Keep a one-line pointer on every decision naming what was moved and where.
- [x] Delete — do not move — prose the current decisions have falsified.
- [x] Follow `START.md`'s reference-style link convention with one `<!-- LINK DEFINITIONS -->` block, all 10 canonical group headers in order, defs alphabetical within group, paths resolved from `docs/SPECS/appx/`.
- [x] Do NOT correct claims that are factually wrong at HEAD (build plan D2-D11) — record them for Slice 3 instead.

---

## Final verification (Worker 1)

- Spec slice checklist: every box above is `- [x]`; each is evidenced below.
- DRY check across this slice and prior accepted slices: no prior slice exists in this cycle. No duplication introduced — the move is a cut, verified by the zero-counts below.
- Existing tests still pass: not run. This slice changes no executable statement and the plan calls for no focused test scope; the three static gates below are what this slice can falsify.
- Spec reconciliation: performed as the slice itself, recorded under `### Spec changes made (Worker 1 only)`.
- Final status: `final-accepted`.

### Byte and line counts

Measured with `wc -c` / `wc -l` at the moment each number was written; the `HEAD` baseline comes from `git show HEAD:<path> | wc -c`.

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-027-filters-0_0_8.md` | 324,436 bytes / 1,303 lines | 243,044 bytes / 1,090 lines | −81,392 bytes / −213 lines |
| `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` | 0 (did not exist) | 112,631 bytes / 580 lines | +112,631 bytes |

The rationale file is larger than the bytes the spec shed, and that is expected rather than a sign of a copy: it adds a provenance block, twelve `### Changes this Decision underwent` records and six `### Claims this Decision may no longer make` records that never existed anywhere, a non-Decision deliberation section, a spec-wide retraction list, a Slice-3 hand-off, and its own link-definitions block. The **cut** is proved by the spec-side zero-counts, not by comparing the two file sizes.

### Verification performed by this pass

| Check | Command | Result |
|---|---|---|
| Glossary gate | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-027-filters-0_0_8.md` | `OK: 48 terms - all have glossary entries and at least one spec link.` exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 737 citations resolve (662 in 422 .py files, 75 in KANBAN.md).` exit 0 |
| Markdown scaffold (`source-layout` hook's checker) | `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-027-filters-0_0_8.md docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` | exit 0 |
| Justification blocks left in the spec | `grep -c '^Justification:'` | 0 (was 12) |
| Alternatives blocks left in the spec | `grep -c '^Alternatives considered'` | 0 (was 12) |
| `rev[0-9]` / `rev-[0-9]` tokens left in the spec | per-occurrence scan | 2, both inside the single pointer sentence naming the moved `rev1`-`rev8` history (was 248 + 43) |
| `adversarial review` left in the spec | per-occurrence scan | 0 (was 101 outside the revision-history block) |
| Finding-id attributions left (`per H1`, `of M4`, `the L5 …`) | per-occurrence scan | 0 |
| Per-decision pointers present | `grep -c 'Rationale companion'` | 12 |
| In-page anchors, spec | slug-and-resolve over both files | 0 dangling |
| In-page anchors, rationale | slug-and-resolve over both files | 0 dangling |
| Spec → rationale cross-file anchors (`[rationale-d1]`…`[rationale-d12]`) | resolve each `#anchor` against the rationale's headings | 12 / 12 resolve |
| Rationale → spec cross-file anchors | resolve each `#anchor` against the spec's headings | all resolve |
| Link definitions, both files | used-vs-defined diff plus on-disk existence of every def target | no missing, no unused, no broken path |

**The glossary gate needed a pre-emptive repair, and this is the one place the move could have broken it.** Two CSV terms had their *only* spec link inside text this pass was cutting: `Meta.fields` (anchor `metafields`, linked only from rev5 M9) and `strawberry_config` (anchor `strawberry_config`, linked only from rev3 M2). Both were re-linked at a surviving prose mention before the cut — `Meta.fields` in the Slice-1 checklist bullet beside the existing `Meta.model` link, `strawberry_config` in the Risks section's CSV-deferral bullet that already named it in plain text. Without that, the 48-term gate would have failed on two terms and the failure would have looked like CSV rot rather than a link the move took with it.

### Summary

`spec-027` was the archive's last spec with no `-rationale.md` companion and its largest deliberative-layer carrier. This slice created the companion and moved the deliberative layer into it: the whole `rev1`-`rev8` revision history, all twelve `Justification:` blocks, all twelve `Alternatives considered (and rejected):` lists, and the review-round narration that was welded into the contract prose itself — 248 `rev[0-9]` tokens, 43 `rev-[0-9]` tokens and 101 `adversarial review` occurrences at `HEAD`, now 2 and 0 and 0. Where a strip left a sentence that no longer parsed, the sentence was rewritten to state the contract directly ("Rev4's H4 allowed …" → "A compatible Relay/scalar shape on every related target is **not** sufficient …"). Where a passage existed only to say which revision had been wrong, it was deleted rather than moved, and each deletion is listed in the rationale's provenance block. The spec now reads as a current contract; nothing about its accuracy at `HEAD` changed, which is Slice 3's job.

### Spec changes made (Worker 1 only)

Every edit is to `docs/SPECS/spec-027-filters-0_0_8.md`. Cited by content, not by line number — this slice renumbered the file.

1. **Preamble, `Revision history (kept inline so the spec is self-contained):` plus all 67 lines of `rev1`-`rev8`** → replaced by one sentence pointing at the rationale companion. Reason: `BUILD.md` `## Spec rationale extraction` — "the spec never narrates its own history"; the block stated outright that it was kept inline.
2. **Status line**, the sentence `Original L1-of-rev8 phrasing preserved for historical context: "TODO skeleton present, no public filter behavior shipped yet" was accurate at rev8 sign-off …` → removed. Reason: a spec may not quote its own superseded phrasing. The rest of that line is a build-progress log and is Slice 3's (build-plan D2).
3. **Twelve `Justification:` blocks and twelve `Alternatives considered (and rejected):` lists** → each pair replaced by one `Rationale companion — this Decision's justification and its N rejected alternatives: [Decision N][rationale-dN].` line, with the alternative counts re-derived from the moved text (2 / 3 / 5 / 2 / 3 / 4 / 2 / 5 / 5 / 2 / 4 / 2). Reason: the canonical move.
4. **Decision 5 partial keep.** The reversal narrative and two of its four justification bullets moved; the pinned `from django_filters import filterset` import shape, the `ImportError` warning, and the consumer parent-swap sentence stayed in the spec body as contract. Reason: `worker-1.md` `### Performing the rationale move` — implementation-relevant rationale stays; a builder who never reads it writes `from django_filters import BaseFilterSet`, which does not resolve. The pointer records the partial keep explicitly.
5. **Decision 10 split.** The justification and the two rejected alternatives moved; the `**Contingency:**` clause stayed (a conditional contract, not a review record). The sentence `The Definition of done item that previously said "version bump in pyproject.toml" … is REMOVED from this slice` was moved out: it narrates an edit to the spec's own DoD, which DoD item 24 already states.
6. **Review-round narration across eight non-Decision sections and five Decision bodies** → attributions cut, sentences repaired to state the contract. The structural repairs (not merely parenthetical deletions) were: Decision 3's `FieldSpec` lead-in, Decision 3's `__all__` override lead-in, Decision 4's multi-owner-reuse lead-in, Decision 4's "Where the conditional runs", Decision 4's "Why this matters", Decision 6's four-subpasses lead-in, Decision 6's materialize-before-`Schema` paragraph, Decision 8's sync/async-split lead-in, Decision 8's step 7, Decision 9's `_registry` correction sentence, Decision 11's `filter_input_type` timing paragraph, the Slice-4 test bullet, and four `## Test plan` bullets.
7. **`## Slice checklist`, Slice 4** → the `**Carved during Slice-4 final-verification reconciliation (Worker 1):**` passage removed (moved to the rationale). Reason: named explicitly in this slice's brief as narration to sweep. It also asserted an `xfail` that does not exist at `HEAD`; the surviving Slice-4a bullet still describes the flip and is Slice 3's.
8. **`## Slice checklist`, Slice 4a, final bullet** → removed whole (moved to the rationale). Reason: pure build-process narration ("Worker 1 final-verification picked the sub-slice path"), and it carried three raw spec line numbers (`L446`, `L743`, `L1145`) that `AGENTS.md` rule 27 forbids in a standing doc and that this slice's renumbering would have falsified anyway.
9. **Two glossary links added** to keep the 48-term gate green after the cut: `Meta.fields` in the Slice-1 checklist bullet, `strawberry_config` in the Risks CSV-deferral bullet. Reason: both terms' only spec link lived inside moved text (see the verification note above).
10. **Link-definitions block** → added `[spec-027-rationale]` and `[rationale-d1]`…`[rationale-d12]`; removed `[next-step-8]`, `[spec-019]`, `[spec-021]`, `[spec-022]`, `[spec-023]`, whose only uses left with Decision 1's justification; added a missing `[pyproject]` definition. **`[pyproject]` was already dangling at `HEAD`** — used in `## Borrowing posture` and Decision 5, defined nowhere — so this is a repair of pre-existing rot, not of anything the move caused.

### Notes for Worker 1 (spec reconciliation)

These are for **Slice 3**, which owns build-plan findings D2-D11. This slice deliberately left every one of them standing rather than mixing a claim-correction diff into the move. Each is also recorded in the rationale under `## Claims the spec may no longer make` / `## Handed to Slice 3` and, where it belongs to one Decision, under that Decision's `### Claims this Decision may no longer make`.

1. **D2 — the `Status:` line.** Still a build-progress log, still reads "in progress", still cites the deleted per-cycle artifact `docs/builder/bld-slice-6-composition_smoke_test.md`. This slice removed only its historical-phrasing sentence.
2. **D3 — `base.py` "ships" `Filter`.** Decision 2 and DoD item 3 describe a port; `filters/__init__.py` re-exports `django_filters.Filter` itself.
3. **D4 — relocated mechanics.** `FieldSpec`, `build_input_class`, `_input_type_name_for`, `LazyRelatedClassMixin` and `RelatedFilter`'s owner-bind machinery live in the shared substrate; the `filters/` names are deliberate aliases. The spec should say where the mechanics live.
4. **D5 — the retired misuse mechanism.** Decision 8's sync/async subsection still pins a sentinel-string match on `exc.args[0]` and `types/relay.py::_apply_get_queryset_sync` / `_apply_get_queryset_async`, neither of which exists at `HEAD`. Left verbatim; it is a contract claim, not narration.
5. **D6 — `registry.clear()` integration.** Decision 9's snippet is the retired local-import shape; the subsystem now registers a callback via `register_subsystem_clear`.
6. **D7 — the claimed live async test.** Decision 8 says a live HTTP test exercises the async path; no such test exists.
7. **D8 — three Test-plan test names** that return zero hits (`test_apply_propagates_related_constraints_into_filterset_qs`, `test_check_permissions_only_fires_for_active_filter_branches`, `test_related_target_for_resolves_default_reverse_name`). Their contracts are covered under other names.
8. **D9 — the two unnamed phase-2.5 filter-only audits** (`types/finalizer.py::_audit_filterset_subpass_2_5`).
9. **D10 — `HIDE_FLAT_FILTERS`**, which changes the generated input shape and is unmentioned.
10. **D11 — the scattered stale claims**: `_get_fields` vs the real `get_fields`; the "32 terms" CSV claim (48 rows); the pre-archive `docs/spec-027-…` path; the `DONE-NNN-0.0.8` placeholder; the `WIP-ALPHA-021-0.0.8` / `spec-021` collision; the open joint-cut contingency; the `[fakeshop-test-library-reload]` target (the fixture lives in `conftest.py`); the surviving Slice-4a `xfail` description.

Two further items this slice surfaced, neither in D2-D11:

11. **`[pyproject]` was dangling at `HEAD`.** Repaired here (see spec change 10). Flagged so Slice 3 does not re-derive it as new rot.
12. **`[fakeshop-test-library-reload]` and `[fakeshop-test-library]` now resolve to the same file.** The move preserved both definitions unchanged; the first should point at `examples/fakeshop/test_query/conftest.py` once Slice 3 corrects the fixture claim (D11).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[build]: BUILD.md
[build-027]: build-027-filters-0_0_8.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
