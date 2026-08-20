# Build: Slice 1 — Rationale extraction

Spec reference: `docs/SPECS/spec-028-orders-0_0_8.md` (whole file; the move touched the preamble, the `Status:` line, all thirteen Decisions, and six non-Decision sections)
Status: final-accepted

## Plan (Worker 1)

### Worker-1-only artifact shape

This artifact carries a combined `## Plan (Worker 1)` and `## Final verification (Worker 1)` block with no Worker 2 build report and no Worker 3 review. Three clauses authorize it:

- [`BUILD.md`][build] `## Spec rationale extraction` — "Worker 1 is the only role that performs the move", and its `### Who reads it, and when` sub-section states **Worker 2 never reads** the rationale file. The `## Required reading per worker` matrix marks the active `-rationale.md` **never** for Worker 2 and `yes (owns)` for Worker 1.
- [`BUILD.md`][build] `### Procedural-closure slices` is the precedent for the shape: a single Worker 1 pass that sets `Status: final-accepted` directly, carrying one combined Plan + Final-verification block citing the clause that authorizes the closure.
- The build plan [`build-028-orders-0_0_8.md`][build-028] declares the same partition in its preamble: "Ownership partition: none; sequential slices. Slices 1 and 3 are Worker 1's alone; Slice 2 is the only slice with a Worker 2 / Worker 3 cycle."

`docs/builder/bld-slice-1-027-rationale_extraction.md` is the format reference for this shape.

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped: this slice changes no executable statement and adds no helper, shared constant, validation branch, coercion utility, or test helper. [`BUILD.md`][build] `### Package-wide helper inventory before helper planning` gates *helper planning*; there is none to gate. No `.py` file is in this slice's writable list, and the diff confirms none was touched.
- **Existing patterns reused.** The rationale file's shape is the archive's: `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`'s `## Provenance of this record` / verbatim `## Revision history` / one `## Decision N — <spec heading text>` per Decision with `### Justification (moved from the spec)`, `### Alternatives considered (and rejected)`, `### Changes this Decision underwent`, `### Claims this Decision may no longer make` / spec-wide retractions / hand-off. The spec-side pointer wording (`Rationale companion — this Decision's justification and its <N> rejected alternatives: [Decision N][rationale-dN].`) is `spec-027`'s, reused verbatim in form, including its spelled-out counts. The rationale-side back-link ids (`[spec-028-dN]`, `[spec-028-<section>]`) mirror `spec-027`'s `[spec-027-dN]` / `[spec-027-<section>]` convention.
- **New helpers justified.** None in the package. Three throwaway scratch scripts under the session scratchpad (outside the repo) did the mechanical work: one applied count-asserted exact-string replacements and regex rules and refused to write on any count mismatch; one assembled the rationale file from the read-only `HEAD` snapshot plus authored per-Decision prose; one generated a word-level review diff for grammar inspection. All scratch, none a deliverable.
- **Duplication risk avoided.** The move's characteristic failure is a *copy* rather than a cut, leaving the same paragraph in both files. Prevented mechanically: after the pass, `grep -oE 'Justification:'` and `grep -oE 'Alternatives considered'` against the spec both return 0 (13 each at `HEAD`), and so do `adversarial review`, `rev-[0-9]`, `rev[0-9]`, `Revision [0-9]`, `Worker 1`, and `per [A-Z][0-9]* of`. Every count is in the table below with its `HEAD` baseline beside it.

### Implementation steps

1. Snapshot `HEAD` read-only to the scratchpad (`git show HEAD:docs/SPECS/spec-028-orders-0_0_8.md`), and confirm the working-tree spec was byte-identical to it before starting, so every moved block can be recovered verbatim without touching the working tree.
2. Measure the deliberative-layer populations against that snapshot before cutting anything, and run the substring-citation sweep as a precondition.
3. Strip the review-round narration welded into contract prose in two stages: an explicit table of 52 count-asserted exact-string replacements for every site whose removal needed a sentence repair, then four generic regex rules for the mechanical parentheticals. Each rule asserts its occurrence count and aborts the whole run on a mismatch.
4. Rewrite the `Status:` line (build-plan **D2**) from a build-progress log to a state.
5. Rewrite `## Definition of done` items 26 and 28, whose contract was welded to a narration of when and by whom the one full-suite run happened.
6. Cut the `Revision history (kept inline so the spec is self-contained)` block — its preamble plus all seven `Revision N` entries — leaving one pointer sentence.
7. Cut the thirteen `Justification:` / `Alternatives considered (and rejected):` pairs, leaving one `Rationale companion — …` pointer per Decision with the alternative count re-derived from the moved text.
8. Write `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md`: provenance, the verbatim revision history, thirteen Decision sections, the non-Decision deliberation, the spec-wide retractions, and the Slice-3 hand-off.
9. Re-point both files' link-definition blocks: add `[spec-028-rationale]` and `[rationale-d1]`…`[rationale-d13]` to the spec, drop the definitions the move orphaned, and resolve every rationale-side path from `docs/SPECS/appx/` (one level deeper than the spec's).
10. Verify: three gates, every in-page anchor, every cross-file anchor in both directions, used-vs-defined link refs with on-disk existence, the substring sweep as a postcondition, and the byte/line counts.

Line numbers are pin-at-write-time navigational hints. This slice renumbered the whole spec, so any line number written before it ran is stale by construction — which is why every replacement in step 3 was keyed to an exact string rather than a line.

### Test additions / updates

None. This slice changes no executable statement, so no test can observe it. The gates that stand in for tests here are `scripts/check_spec_glossary.py`, `scripts/check_citations.py`, and `scripts/check_trailing_commas.py --check`; all three are recorded under `## Final verification (Worker 1)`. No `pytest` was run ([`AGENTS.md`][agents] "No pytest after edits") and no `--cov*` flag was used ([`BUILD.md`][build] `## Coverage is the maintainer's gate, not a worker's tool`). No `ruff` run is owed: the slice touches no Python.

### Implementation discretion items

None. This slice had no Worker 2 to delegate to.

### Boundary count

Zero new boundaries. This slice adds no guard, cap, rejection path, or validation branch, so no failability proof is owed and the split question is answered by the diff shape alone: one cut plus its pointer set, in two files, is one coherent unit.

### Hot-path declaration

Not applicable; the plan declares no hot path for this cycle. This slice edits Markdown only — nothing runs per request, per resolver, per row, per connection, or per outbound message.

### Floor verification

Not applicable; the plan declares floor-verification scope `none`. No slice in this cycle changes an executable statement, so no floor venv was built and no floor run is owed.

### Spec slice checklist (verbatim)

The spec's own `## Slice checklist` has no entry for this cycle — `028` shipped as `DONE-028-0.0.8` and its six slices are all closed and ticked. This slice's contract comes from the build plan's checklist line and from [`BUILD.md`][build] `## Spec rationale extraction` plus [`worker-1.md`][worker-1] `### Performing the rationale move`. The boxes below are that contract, audited by this same pass under `## Final verification (Worker 1)`.

- [x] Create `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md`.
- [x] MOVE the entire `Revision history (kept inline so the spec is self-contained)` block — its preamble plus all seven `Revision N` entries and every B / H / M / N / R / O item under each. The preamble's own assertion that the history is kept inline moves with it.
- [x] MOVE every `Justification:` block and every `Alternatives considered (and rejected):` block under all thirteen Decisions.
- [x] MOVE every inline review-round narration welded into the contract prose, across Decisions 2, 3, 5, 6, 8, 9, 11, 12, 13, the Slice checklist, Edge cases, the Test plan, Doc updates, and the Definition of done.
- [x] Leave behind grammatical, self-consistent contract prose; repair every sentence the removal breaks so it states the contract directly, with no amendment block, no retraction paragraph, and no "as of rev N" hedge.
- [x] Key every rationale entry to the spec decision it belongs to by heading and anchor.
- [x] Carry, per decision: the alternatives rejected and why each lost; every change the decision has undergone with the round that caused it; any claim the decision once made and may no longer make.
- [x] Keep a one-line pointer on every decision naming what was moved and where.
- [x] Delete — do not move — prose the current decisions have falsified, and list each deletion.
- [x] Resolve **D2** (the `Status:` line) as part of this slice.
- [x] Follow [`START.md`][start]'s reference-style link convention in both files: one `<!-- LINK DEFINITIONS -->` block, all 10 canonical group headers in order, defs alphabetical within group, every rationale-side path resolved from `docs/SPECS/appx/` and disk-exists-checked.
- [x] Keep every `### Decision N` heading and the `## Test plan` heading in place and addressable, so the 37 `spec-028 Decision N` and 5 `spec-028 test plan` citations in `.py` survive.
- [x] Do NOT correct claims that are factually wrong at `HEAD` (build-plan D3-D16) — record them for Slice 3 instead.
- [x] Do NOT edit any `.py` file, the terms CSV, or any out-of-scope standing doc.

---

## Final verification (Worker 1)

- Spec slice checklist: every box above is `- [x]`; each is evidenced below.
- DRY check across this slice and prior accepted slices: no prior slice exists in this cycle. No duplication introduced — the move is a cut, proved by the spec-side zero counts below, not by comparing the two files' sizes.
- Existing tests still pass: not run. This slice changes no executable statement and the plan calls for no focused test scope; the three static gates below are what this slice can falsify.
- Spec reconciliation: performed as the slice itself, recorded under `### Spec changes made (Worker 1 only)`.
- Final status: `final-accepted`.

### Byte and line counts

Measured at the moment each number was written. The `HEAD` baseline comes from `git show HEAD:<path> | wc -c` / `| wc -l`; the working-tree spec was verified byte-identical to `HEAD` before the pass started (`diff -q` on the snapshot), so the baseline is this slice's true entry state and not a mixed reading.

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-028-orders-0_0_8.md` | 289,080 bytes / 1,354 lines | 224,759 bytes / 1,153 lines | −64,321 bytes / −201 lines |
| `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md` | 0 (did not exist) | 98,821 bytes / 594 lines | +98,821 bytes / +594 lines |

The rationale file is larger than the bytes the spec shed, and that is expected rather than a sign of a copy: it adds a provenance block, thirteen `### Changes this Decision underwent` records and seven `### Claims this Decision may no longer make` records that existed in neither file, a `## Non-Decision deliberation` section, a spec-wide `## Claims the spec may no longer make` list, a `## Handed to Slice 3` hand-off, and its own link-definitions block. **The cut is proved by the spec-side zero counts, not by the file sizes.**

### Residual-marker readings (re-measured by this pass)

Occurrence counts, not matching-line counts — `grep -oE '<pat>' <file> | wc -l`. The `HEAD` column is `git show HEAD:docs/SPECS/spec-028-orders-0_0_8.md | grep -oE '<pat>' | wc -l`.

| Pattern | Spec at `HEAD` | Spec now |
|---|---|---|
| `Justification:` | 13 | **0** |
| `Alternatives considered` | 13 | **0** |
| `adversarial review` | 90 | **0** |
| `rev-[0-9]` | 84 | **0** |
| `rev[0-9]` | 76 | **0** |
| `Revision [0-9]` | 9 | **0** |
| `Worker 1` | 8 | **0** |
| `per [A-Z][0-9]* of` | 89 | **0** |

Worker 0's entry inventory gave `160` for "rev-N references"; re-measured, that population splits into **84** `rev-[0-9]` plus **76** `rev[0-9]` occurrences, which sum to 160. Both spellings now read 0. The `Revision [0-9]` reading is 9 rather than 7 because the pattern also matched the two prose sentences that named "the first Revision-5 wording" and "Revision 7" inside the block; all nine occurrences left with it.

Structural anchors, re-counted: **13** `^### Decision ` headings and **1** `^## Test plan` heading remain in the spec, and **13** `^Rationale companion` pointers were added (one per Decision). The rationale file carries **13** `^## Decision ` sections, one per spec Decision, each opening with a `Spec: [<heading>][spec-028-dN].` back-link.

### Substring-citation sweep (the standing hazard), precondition and postcondition

A slice that MOVES spec text breaks every `path #"substring"` citation aimed into the moved region, and no gate sees it: `scripts/check_citations.py` resolves `path::Symbol` refs only and `docs/` is outside its scope. Both readings were taken by this pass.

| Reading | Command | Result |
|---|---|---|
| Precondition, substring citations | `git grep -ohE 'spec-028[^)]*#"' HEAD -- '*.py' \| wc -l` | **0** |
| Postcondition, substring citations | `grep -rohE --include='*.py' 'spec-028[^)]*#"' django_strawberry_framework tests examples \| wc -l` | **0** |
| Precondition, wrapped-across-lines probe | whitespace-flattened `spec-028[^"\n]{0,120}#\s*"` over all 400 `HEAD` `.py` blobs under the three trees | **0** |
| Postcondition, wrapped-across-lines probe | same regex over the 400 working-tree `.py` files | **0** |

The wrapped probe is not redundant with the single-line grep: a substring citation reflowed across two source lines is invisible to a single-line pattern, which is the exact defect shape this hazard's standing note names. Both readings are 0, so **there was no substring cohort to break and none was broken.**

The durable citation forms that must survive the move were counted the same way, on `.py` files only, in both directions:

| Form | `HEAD` | Working tree |
|---|---|---|
| `spec-028` (all forms) | 68 | **68** |
| `spec-028 Decision [0-9]*` | 37 | **37** |
| `spec-028 test plan` | 5 | **5** |

Identical, as they must be: `git diff HEAD --name-only -- '*.py'` lists 21 files, all of them the `spec-027` cycle's baseline-dirty set plus `tests/test_registry.py` (see the concurrent-work note below), and a per-file occurrence comparison against `git show HEAD:<path>` found **no** `spec-028` count difference in any of them. This pass authored no `.py` edit.

### Verification performed by this pass

| Check | Command | Result |
|---|---|---|
| Glossary gate | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-028-orders-0_0_8.md` | `OK: 44 terms - all have glossary entries and at least one spec link.` exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 743 citations resolve (666 in 422 .py files, 77 in KANBAN.md).` exit 0 |
| Markdown scaffold (the `source-layout` hook's checker) | `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` | exit 0 |
| Link-def scaffold | delimiter and canonical-group-header count per file | spec: 1 delimiter, 10 headers. rationale: 1 delimiter, 10 headers |
| In-page anchors, spec | slug-and-resolve every `](#…)` against the file's own headings | 0 dangling |
| In-page anchors, rationale | same | 0 dangling |
| Spec → rationale cross-file anchors | resolve `[rationale-d1]`…`[rationale-d13]` and `[spec-028-rationale]` against the rationale's headings | 14 / 14 resolve |
| Rationale → spec cross-file anchors | resolve `[spec-028-d1]`…`[spec-028-d13]` plus `[spec-028-goals]`, `[spec-028-edge-cases]`, `[spec-028-slice-checklist]`, `[spec-028-baseline]`, `[spec-028-dod]`, `[spec-028]` against the spec's headings | all 19 resolve |
| Link definitions, both files | used-vs-defined diff | spec: 0 used-undefined, 1 defined-unused (`[relay]`, pre-existing — see note 1 below). rationale: 0 used-undefined, 0 defined-unused |
| Link-def targets on disk | existence-check every non-URL def path in the rationale, resolved from `docs/SPECS/appx/` | all exist |
| Inline cross-file links | grep both files for inline `](path)` outside code fences | none in either file; the convention holds |
| Strip artifacts | scan for `— ,`, `<non-space> ,`, `[a-z]  [a-z]`, `([,;:]`, `—)`, `**  :` | 0 in each class |

**The glossary gate was the one thing the move could have broken, and it did not.** `check_spec_glossary` requires every CSV term to keep at least one spec-body link; a term whose only link lived inside moved text would have gone red. The reading is unchanged at `OK: 44 terms`, so no CSV term's last spec link left with the deliberative layer, and the CSV was not touched (verified clean against `HEAD`).

### Summary

`spec-028` was the archive's last spec with no `-rationale.md` companion and, after `027`, its largest deliberative-layer carrier. This slice created the companion and moved the deliberative layer into it: the whole seven-revision history including the preamble that asserted it was kept inline, all thirteen `Justification:` blocks, all thirteen `Alternatives considered (and rejected):` lists carrying 39 rejected alternatives, and the review-round narration that was welded into the contract prose itself — 90 `adversarial review`, 160 `rev-N` (84 + 76 across two spellings), 89 `per <ID> of`, and 8 `Worker 1` occurrences at `HEAD`, all now 0.

The spec's `Status:` line, a 4,300-character build-progress log that tracked six slices as they landed and closed "Awaiting maintainer commit", is now a statement of the shipped surface. Where a strip left a sentence that only parsed as a correction, the sentence was rewritten to state the contract directly ("Prior revisions claimed `DjangoType.Meta.model` rejects abstract models at `_validate_meta` time, but the current …" → "`_validate_meta` checks only that `Meta.model` is a Django model class; it does NOT inspect `model._meta.abstract`"). Where a passage existed only to record which revision had been wrong, it was deleted rather than moved, and every deletion is listed in the rationale's provenance block. The spec now reads as a current contract; nothing about its accuracy at `HEAD` changed, which is Slice 3's job.

### Spec changes made (Worker 1 only)

Every edit is to `docs/SPECS/spec-028-orders-0_0_8.md`. Cited by content, not by line number — this slice renumbered the file.

1. **Preamble, `Revision history (kept inline so the spec is self-contained):` plus all seven `Revision 1`-`Revision 7` entries (70 lines)** → replaced by one sentence pointing at the rationale companion. Landed at the rationale's `## Revision history`, verbatim. Reason: [`BUILD.md`][build] `## Spec rationale extraction` — "the spec never narrates its own history"; the block stated outright that it was kept inline, so that assertion went with it.
2. **`Status:` line (build-plan D2)** → rewritten from a build-progress log to a state. What left: the per-slice landing chronology and dates; the full-suite gate's owner, date, pass/skip/coverage numbers and clean-tool list; the two superseded maintainer-review corrections; the quoted disproved round-1 diagnosis; the four-piece (a)-(d) closing narrative; and "Awaiting maintainer commit." What stayed, as a state: the `orders/` file list, the phase-2.5 binding seam, the `ALLOWED_META_KEYS` promotion, the fakeshop wiring, the two test homes, and the `docs/TREE.md` / `docs/GLOSSARY.md` / KANBAN / `CHANGELOG.md` outcomes. The (a)-(d) narrative landed at the rationale's `### The final gate`; the disproved diagnosis and "Awaiting maintainer commit" were **deleted**, both recorded as deletions in the rationale's provenance block.
3. **Thirteen `Justification:` blocks and thirteen `Alternatives considered (and rejected):` lists** → each pair replaced by one `Rationale companion — this Decision's justification and its <N> rejected alternatives: [Decision N][rationale-dN].` line, with `<N>` re-derived by counting the moved bullets: 2 / 3 / 3 / 3 / 4 / 4 / 2 / 4 / 3 / 2 / 4 / 3 / 2, summing to 39. Landed verbatim under each rationale Decision's `### Justification (moved from the spec)` and `### Alternatives considered (and rejected)`.
4. **Review-round narration across five Decision-body regions and six non-Decision sections** → 52 count-asserted exact-string replacements plus four generic regex rules (11 sentence-initial `Per <ID> of the rev-N adversarial review,` forms; 12 parenthetical-opening forms with an em-dash continuation; 10 parenthetical-only citations; 27 bare mid-sentence citations). Every rule asserted its occurrence count and would have aborted the run on a mismatch. The structural repairs — the sites where deleting the citation alone would have left prose that only parsed as a correction — were:
   - `## Key glossary references`, the `only() projection` bullet: `— verified per H2 of the rev-1 adversarial review (no logic in … reads …).` → `— no logic in … reads ….`
   - `## Slice checklist` Slice 1, `base.py` bullet, and Decision 2's `base.py` bullet: `Per H1 of the rev-3 adversarial review, the mixin's home is …` → `The mixin's home is …` / `` `sets_mixins.py` is the neutral home … ``
   - `## Slice checklist` Slice 3: `(per N3 of the rev-1 adversarial review + DoD item 9)` → `(per [Definition of done](#definition-of-done) item 9)`, keeping the durable pointer and dropping the review-item id.
   - `## Slice checklist` Slice 4: `— per B3 …, the test must target a nullable text field that actually exists on the model` → `— the test targets a nullable text field that exists on the model`; and `combined so the total Slice-4 test count matches Decision 13's "14 tests total" pin per Worker 1 Slice-4 final-verification reconciliation` → `both halves ship in one test function`.
   - `## Slice checklist` Slice 5 and `## Doc updates`: two `Per M3 of the rev-3 adversarial review, `Ordering` is/MUST …` → `` `Ordering` is/MUST … ``
   - `## Pre-implementation baseline`: `unlike the Filtering subsystem which had skeleton anchors before Slice-1 implementation per L1 of [spec-027] rev8)` → `… implementation)`.
   - `## Non-goals`: `the filter side already deferred (per M3 of [spec-027] rev8 feedback).` → `the filter side already deferred.`
   - `## User-facing API`, the permission-gate code example's docstring: `same discipline the filter subsystem ships per / docs/spec-027-filters-0_0_8.md Decision 8 M2 of rev5)."""` → `same discipline the filter subsystem ships)."""`
   - Decision 2's `sets.py` bullet: `**No `apply(...)` dispatcher is shipped** — per H1 …, the filter side's …` → `… — the filter side's …`; and `**Placement rationale (refined per N-new-2 of the rev-2 adversarial review):**` → `**Placement rationale:**`
   - Decision 3: `**Corrected per B4 of the rev-3 adversarial review AND further refined against empirical Django 6.0.5 behavior:**` → `**Verified against empirical Django 6.0.5 behavior:**`; and the abstract-model bullet's `Prior revisions claimed …, but the current` lead-in deleted so the sentence states what `_validate_meta` checks.
   - Decision 5's code example, two comments: `# Per M4 …: both imports must be local-to-` → `# Both imports must be local-to-`; `# Django sentinel semantics (M4 of the rev-1 adversarial review):` → `# Django sentinel semantics:`
   - Decision 6: the `(NOT spec-027 rev8 as written — per B1 …, the shipped code is the authoritative shape)` parenthetical deleted whole, so the sentence states the shipped subpass order positively; subpass 3's trailing `; this card mirrors the shipped order, not the spec-027 rev8 H1 prescription which inverted subpasses 3 and 4.` deleted; `(mirrors the filter side's strict reuse check from H2 of [spec-027] rev8)` → `(mirrors the filter side's strict reuse check)`.
   - Decision 8: five repairs — the sync/async lead-in `Same shape as the filter side per H2 of [spec-027] rev5:` → `Same shape as the filter side:`; `(mirrors the filter side's H2 split from [spec-027] rev5)` → `(mirrors the filter side's sync/async split)`; `Same shape the filter side ships per M8 of [spec-027] rev5.` → `Same shape the filter side ships.`; the `only_fields` claim's `(verified per H2 …)` deleted; and `**Active-branch double-dispatch (per H3 …, mirroring the filter side's …)**` → `**Active-branch double-dispatch (mirroring the filter side's …)**`.
   - Decision 9: `(mirrors M5 of [spec-027] rev3 + M4 of rev8):` → `:`; and inside the `registry.py` code example, the three-line comment `# names below are verbatim from registry.py::TypeRegistry.__init__ / # (per B3 …; spec-rev1 mis-named these as / # `_types_by_model` / `_primary_types`).` collapsed to `# names below are verbatim from registry.py::TypeRegistry.__init__.`
   - Decision 11: two code comments (`# the filter side's H5 from spec-027-filters-0_0_8.md rev5).` → `# the filter side's orphan validation).`; `# contract the filter side ships per M4 of rev5 + M4 of rev6 of / # spec-027-filters-0_0_8.md.` → `# contract the filter side ships.`), plus `same mechanics as the filter side per M6 of [spec-027] rev5.` → `… as the filter side.` and `(H5 of [spec-027] rev5):` → `:`.
   - `## Edge cases and constraints`: `Mirrors the filter side's L1 of rev4 flat-field shape` → `Mirrors the filter side's flat-field shape`; `discipline the filter side ships per M5 of [spec-027] rev8.` → `discipline the filter side ships.`; and the duplicate-field bullet's `the exact-14 live test plan does NOT include a duplicate-field test (a prior revision wrongly implied one).` → `the live test plan does not include a duplicate-field test.`
   - `## Test plan`: `**assert the denormalized JOIN+ORDER multiplicity explicitly** per M5 …:` → `… explicitly**:`; `**Per H4 of the rev-3 adversarial review:** the GraphQL enum value is …, and prior revisions wrongly used the Python-attr casing.` → `The GraphQL enum value is …` with the prior-revision clause deleted; `(mirrors the filter side's M1 of rev8 — same `Branch.city` field, same data shape)` → `(same `Branch.city` field and data shape as the filter side's visibility test)`; four `(per Worker 1 Slice-4 final-verification reconciliation; …)` parentheticals reduced to their substantive halves; `(Quiet-half field substituted `city` for `name` per Worker 1 … to dodge the cross-test gate collision.)` → `(The quiet half uses `city` rather than `name` to dodge the cross-test gate collision.)`; `Pins the path-shorthand contract whose mirror on the filter side is covered by spec-027 rev4 L1.` → `Pins the path-shorthand contract; the filter side covers its mirror.`; and the `subtitle_desc_nulls_last` bullet's `(per B3 … — was `title` in earlier revisions but …` → `(`Book.title = TextField()` is non-null and cannot satisfy a NULLS-last test; …`.
   - Decision 11's package-test bullet: `pinned against future drift back to the rev1 self-misuse` → `pinned against future drift to a list shape`.
   - `## Implementation plan` Slice-4 row, Decision 13's capability list, `## Doc updates`' quoted KANBAN body and CHANGELOG bullet, `## Risks and open questions`, and `## Definition of done` items 4, 6, 9, 10, 14, 15: every `per <ID> of rev<N>` / `per H3 of rev3` / `per B2 of rev3` breadcrumb removed, DoD 10's `(NOT the inverted subpasses 3-and-4 prescribed by spec-027 rev8 H1 — …)` parenthetical deleted whole, and DoD 15's `(the rev1 count of 10 expanded by M2 / M5 / M6 / M7 … plus the H3 … test added in rev3 review)` parenthetical deleted whole (the `## Test plan` enumerates the tests).
5. **`## Definition of done` items 26 and 28** → both keep their rule and lose their narration. Item 26's `The **final** full-suite gate (Status line: 1354 passed / 100.00% coverage, 2026-06-02) was run once by the maintainer-directed assistant pass at the maintainer's explicit `run tests and coverage` request` became `A full-suite run happens only on an explicit maintainer ask, which the rule permits (see item 28).` Item 28's closing `The one full-suite run recorded on the Status line (2026-06-02) was exactly such an explicit maintainer ask …, not a worker-initiated run — so the gate-green Status line and this no-local-pytest rule are consistent, not contradictory.` was removed. Reason: both sentences existed to reconcile the rewritten `Status:` line's chronology, which is now gone; the reconciliation itself landed at the rationale's `### The final gate`. Item 26's reference to the Status line's numbers would otherwise have dangled.
6. **Link-definitions block** → added `[spec-028-rationale]` and `[rationale-d1]`…`[rationale-d13]`; removed `[next-step-8]`, `[spec-019]`, `[spec-021]`, `[spec-022]`, `[spec-023]`, `[spec-025]`, and `[upstream-cookbook-filterset-factories]`, whose only uses left with the moved text. All seven are defined in the rationale file instead, resolved from `docs/SPECS/appx/`. The `docs/SPECS/` group was re-sorted alphabetically after the insert.

**Nothing in D3-D16 was corrected.** Where moving a `Justification:` block carried a claim that is false at `HEAD` — Decision 5's `ORDER_BY_ARG = "orderBy"` bullet being the clearest case — the bullet moved verbatim and the finding was recorded under that Decision's `### Claims this Decision may no longer make` in the rationale rather than fixed. `worker-1.md`'s "delete, do not move, prose the current decisions have falsified" governs prose a *current Decision* has falsified; a claim falsified by the shipped code is Slice 3's finding, and deleting it here would have destroyed the evidence Slice 3 needs.

### Notes for Worker 1 (spec reconciliation)

These are for **Slice 3**, which owns build-plan findings D3-D16. This slice deliberately left every one of them standing rather than mixing a claim-correction diff into the move. Each is also in the rationale — per-Decision under `### Claims this Decision may no longer make`, spec-wide under `## Claims the spec may no longer make` and `## Handed to Slice 3` — but is repeated here because detail living only in a file the next pass may not open does not reach the next worker.

**Keyed to a Decision (rationale carries these under that Decision):**

1. **D4 — `OrderSet.check_permissions` was deleted post-ship.** Still named in Decision 8 step 6's parenthetical, Decision 2's `sets.py` bullet, the `## Borrowing posture` "port verbatim" bullet, and DoD item 4(e). Shipped in `11d9fbe0`, removed by `9e864f59`, which rewrote the module docstring from "the `check_permissions` instance method + the classmethod pipeline" to "the classmethod permission pipeline" in the same diff. One `def check_permissions` remains package-wide: `filters/sets.py::FilterSet.check_permissions`. The test Decision 8 step 6 cites, `tests/orders/test_sets.py::test_orderset_check_permissions_instance_method_delegates`, has 0 occurrences outside the spec.
2. **D5 — the mechanics moved into the shared set-family substrate.** `RelatedOrder`'s direct base is `sets_mixins.py::RelatedSetTargetMixin`, not `LazyRelatedClassMixin` (Decision 2, Decision 3 Layer 2, DoD 3 all say otherwise); the permission machinery lives on `sets_mixins.py::ActiveInputPermissionMixin` delegating to `utils/permissions.py::invoke_permission_method` (Decision 8 step 6 attributes it to the order side); metaclass collection is `sets_mixins.py::collect_related_declarations` and the Layer-4 cache/guard `::expanded_once` / `::should_cache_expansion` (Decision 3 Layers 3-4 describe a local `cls.__dict__` guard); `orders/inputs.py`'s `FieldSpec` / `build_input_class` / `_input_type_name_for` / `_iter_orderset_subclasses` are one-line aliases over `utils/inputs.py`. **`_ensure_built` and `_build_class_type`, named by Decision 3 Layer 5 and Decision 6 subpass 4, have 0 occurrences under `orders/`** — those two are gone, not relocated; everything else still resolves from `orders.*` deliberately, so the spec should say where the mechanics live rather than treat it as a surface break.
3. **D6 — `apply_async`'s thread boundary is a shared helper now.** Decision 8's sync/async paragraph pins `await sync_to_async(cls._run_permission_checks, thread_sensitive=True)(…)` literally; `OrderSet.apply_async` calls `await run_in_one_sync_boundary(cls._run_permission_checks, input_value, request)` from `utils/querysets.py`. The behavioral claim survives; the named mechanism does not.
4. **D7 — the gate now REJECTS an `async def check_<field>_permission`.** `utils/permissions.py::invoke_permission_method` runs the return through `reject_async_in_sync_context` and raises `SyncMisuseError`, because an un-awaited coroutine is truthy and an intended denial would otherwise become an authorization **bypass**. Decision 8 step 6, `## Error shapes`, and the `## User-facing API` `check_*_permission` example describe only the `GraphQLError` denial path.
5. **D8 — order paths are pre-validated.** `7000d920` added `utils/relations.py::classify_path` calls in `OrderSet._expand_meta_fields` and `::_resolve_order_expressions`, each raising `ConfigurationError` naming the path and model. Two claims are false: the Edge-case "the framework does not pre-validate the backend's supported expressions", and the `## Error shapes` bullet placing the invalid-`Meta.fields` raise at type-creation time — Decision 3 Layer 3 says the metaclass does not expand, so the raise lands at finalize phase-2.5 subpass 2. Pinned by `test_orderset_resolve_order_expressions_rejects_unknown_order_path` and `::test_orderset_meta_fields_rejects_unknown_order_path`.
6. **D9 — the path resolves against the QUERYSET's model, and a model-less `OrderSet` is legal.** `OrderSet._apply_orderings` calls `_resolve_order_expressions(flat_orders, model=queryset.model)`. Decision 8 step 7 and DoD 4(b) describe `Meta.model`-derived paths only, and Decision 3 treats `Meta.model` as mandatory throughout. Pinned by `test_modelless_orderset_uses_queryset_model_for_to_many_order` and `::test_queryset_model_overrides_conflicting_orderset_meta_model` (`ae6ac9ab`).
7. **D3 — Decision 9's `registry.clear()` integration is the retired shape**, and its fenced `registry.py` block is 59 lines of Python that no longer exists. `registry.py::register_subsystem_clear` / `::iter_subsystem_clears` is the seam; `orders/inputs.py` registers `clear_order_input_namespace` (owner `orders.input_namespace`, `before_bind=True`) and `orders/__init__.py` registers `_clear_helper_referenced_ordersets` (owner `orders.helper_references`), both at import time; `TypeRegistry.clear` carries **no** `except ImportError` guard for either subsystem and replays `for clear in iter_subsystem_clears(): clear()`. `orders/__init__.py`'s own comment records that the older shape predates the seam. The two-separate-blocks rationale is right in intent (the helper ledger clears through its own row) and wrong in mechanism.
8. **D10 — the to-many correction landed in one of five parallel sites.** The row-preserving `Min`/`Max` aggregate (`spec-030-connection_field-0_0_9` P1-B) is stated correctly in the Slice-4 checklist bullet, Decision 12, and the Non-goals DISTINCT-ON bullet. Four sites still pin the retired JOIN-multiplicity contract: the Test-plan `test_library_branches_order_by_reverse_fk_relation` bullet (three separate claims inside it, including "assert the response carries Alpha three times" and "The `RelatedOrder` GLOSSARY entry calls out this multiplicity"), Decision 13's capability list, the Implementation-plan Slice-4 row, and the KANBAN past-tense body quoted in `## Doc updates`. **This slice stripped the provenance from all four but left the claims verbatim**, so the four sites are still four sites — the cross-cohort seam is exactly where this defect class survives review.
9. **D11 — the GLOSSARY claims are false in both directions.** Decision 8 step 4 asserts the `OrderSet` and `RelatedOrder` entries call out the position side channel; neither mentions a side channel, a leak, or a position inference. The Test-plan bullet asserts the `RelatedOrder` entry calls out the multiplicity; it does not, and must not. Conversely the shipped `## `OrderSet`` entry documents three contracts `## Doc updates` does not name: the `Min`/`Max` row-preserving aggregate, the root connection's deterministic pk tiebreaker over the grouped queryset, and the deliberate nested-relation-connection `orderBy:` bypass of window/lateral planning. `docs/GLOSSARY.md` is DB-generated and out of this cycle's scope; only the spec's claims *about* it are in scope.
10. **D12 — the live-test count and one live-test name are stale.** `test_library_api.py` carries **15** order tests, not 14: the 14 plus `test_library_branches_order_by_scalar_then_to_many_aggregate_no_multiplication`, which the spec names nowhere. And `test_library_books_order_by_subtitle_desc_nulls_last` has 0 occurrences; the NULLS-positioning contract ships parametrized as `test_library_books_order_by_subtitle_null_positioning` (four directions, `DESC_NULLS_LAST` among them), with a second nullable-subtitle contract test at `test_library_choice_enum_and_nullable_subtitle_are_deliberate_http_contracts`. **The `14` census shrank from 14 sites to 13:** rewriting the `Status:` line removed its "14 new live HTTP order tests" claim, so Slice 3 should re-derive the census rather than work from Worker 0's figure. This is the "a count can be right in every digit and wrong in its subject" hazard — the number 14 is still correct as *the spec's claim*, but its population changed under it.
11. **D13 — four spec-named package permission tests do not exist.** `test_orderset_check_permission_active_relatedorder_branch_fires_parent_gate`, `..._fires_child_gate`, `test_orderset_check_permission_quiet_for_inactive_field`, and `test_orderset_check_permission_denies_for_active_field` all return 0 occurrences repo-wide. The double-dispatch-plus-dedup contract is pinned once, family-neutrally, at `tests/utils/test_permissions.py::test_run_active_input_permission_checks_double_dispatch_and_dedup`; the family wiring by `tests/test_sets_mixins.py` (five tests); the order-side residue by `tests/orders/test_sets.py::test_orderset_check_permission_dedups_repeated_list_entries` and `::test_orderset_inactive_input_does_not_resolve_lazy_related_target`. All three **live** gate tests do exist. Also `test_registry_clear_works_without_orders_imported` lives in `tests/orders/test_inputs.py`, not `tests/orders/test_finalizer.py` where the Test plan places it.
12. **D14 — `ORDER_BY_ARG = "orderBy"` was never shipped.** Two assertions at `HEAD`: Decision 5's justification bullet (**now moved into the rationale**, so only one remains in the spec) and the `## Borrowing posture` strawberry-django bullet. `git log --oneline -S'ORDER_BY_ARG' --all` hits only the two spec-draft commits (`649a813a`, `c8be7ec9`) and checkpoint refs; the constant has never existed in any `.py`. Nothing needs it — Strawberry derives `orderBy` from the resolver's `order_by` parameter. Worker 0 recommends correcting the spec rather than shipping a dead constant, and I concur: it is the same YAGNI judgement Decision 2 already records for the dropped `apply()` dispatcher and Decision 12 for Layer 6. **The spec-side population is now one site, not two.**
13. **D15 — fakeshop's order graph outgrew the spec.** `examples/fakeshop/apps/library/orders.py` ships **seven** ordersets (the five named plus `PeriodicalOrder` and `IssueOrder`, whose docstring identifies them as the keyset-cursor `orderBy:` substrate); `schema.py` carries **eight** `Meta.orderset_class` wirings against DoD 14's six; `orders_genre.py::GenreOrder` declares `books = RelatedOrder("apps.library.orders.BookOrder")`, a second absolute-import-path form; `BookOrder.loans` and `ShelfOrder.books` are unnamed by the spec. Six root resolvers carry `order_input_type(...)`, matching. Slice 4 and DoD 13-14 should state the shipped shape.
14. **D16 — tail-section staleness.** The Slice-6 test count contradicted itself three ways (checklist "One", Implementation-plan row `New tests = 1`, Status line "two"); **this slice removed the Status-line leg by rewriting that line**, so two contradicting sites remain and HEAD has two tests (`test_filter_and_order_compose_through_finalizer_and_apply_pipelines`, `test_filter_and_order_share_lazy_related_class_mixin_via_neutral_module`). Also: three Key-glossary-reference bullets still read `planned for 0.0.8` as present fact (the other `planned for 0.0.8` occurrences, in the Predecessors line, the Pre-implementation baseline, and the Slice-5 / Doc-updates flip-this instructions, are correct phrasing and should be left); the pre-archive path `docs/spec-028-orders-0_0_8.md` still appears across the Decision 1 body, the Slice-5 KANBAN bullet, the quoted KANBAN body, the CHANGELOG bullet, the Risks terms-CSV bullet, and DoD items 1, 17, 22, and DoD 17's quoted `check_spec_glossary` command would fail as written (the spec is at `docs/SPECS/`); the `docs/TREE.md` Doc-updates bullet names a "Test layout going forward" section that no longer exists (`docs/TREE.md` has `## Test layout` and `### Target test shape`); the Pre-implementation-baseline `docs/TREE.md` bullet's five-file claim is four at HEAD (`build_tree_md.py` omits `__init__.py`); Decision 10's closing "had not happened as of this spec's writing" is a dated `CHANGELOG.md` claim a reader will read as current; the Test-plan preamble says "Tests live in two trees" and `tests/orders/` "Five files mirror the source layout" while Decision 2, Decision 13, and DoD 11 all say seven (seven is correct); and `[fakeshop-test-library-reload]` and `[fakeshop-test-library]` resolve to the same path while the fixture lives at `examples/fakeshop/test_query/conftest.py`. **The two raw intra-document line-range references D16 names are gone** — both lived in the rev-3 R-bullets and Decision 3's `"__all__"` paragraph, which this slice moved or stripped; Slice 3 need not re-derive them.

**Three things this slice changed that Slice 3 must not re-derive as new rot:**

15. **`[relay]` was already an unused link definition at `HEAD`.** Verified against the `HEAD` snapshot: `defined-but-unused` read `['relay']` before the move as well as after. It is not an orphan the cut created. Left in place deliberately, since removing it is a Slice-3 judgement about whether Decision 7's `orders.sets → types.relay → types.base` cycle discussion should link it.
16. **Seven link definitions were removed** because the move took their only uses (`[next-step-8]`, `[spec-019]`, `[spec-021]`, `[spec-022]`, `[spec-023]`, `[spec-025]`, `[upstream-cookbook-filterset-factories]`). All seven now live in the rationale file. If Slice 3 restores a citation that needs one, the definition has to come back.
17. **C2's two raw spec-line-number citations in `.py` are now worse, as predicted.** `django_strawberry_framework/orders/inputs.py` #"per spec-028 Decision 3 line 452" and `tests/orders/test_inputs.py` #"spec-028 Decision 5 lines 525-532" were already pointing at the wrong Decisions at `HEAD`; this slice renumbered the whole spec, so the line numbers are now arbitrary. **Slice 2 owns both** — this slice touched no `.py`.

### Concurrent-work note

`git diff HEAD --name-only -- '*.py'` lists 21 files. Twenty are the `spec-027` cycle's baseline-dirty set named in the build plan. The twenty-first, `tests/test_registry.py`, was **not** dirty at this session's start and is not in this slice's writable list: it is another session's work (or the same cycle's later slice), left untouched per [`AGENTS.md`][agents] rule 34. A per-file occurrence comparison against `git show HEAD:tests/test_registry.py` shows its single `spec-028 Decision 9` reference intact, so it does not disturb the citation sweep. It is also finding **C6**'s file, which Slice 2 owns; whoever dispatches Slice 2 should re-read it against `HEAD` rather than assuming the docstring is still the one the build plan quoted.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[build]: BUILD.md
[build-028]: build-028-orders-0_0_8.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
