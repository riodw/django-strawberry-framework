# Build: Slice 0 — Spec rationale extraction (`spec-033`)

Spec reference: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (pre-move: 174,055 bytes / 733 lines; post-move: 137,803 bytes / 643 lines)
Status: final-accepted

**Shape.** Procedural-closure slice ([`docs/builder/BUILD.md`][build-md] `### Procedural-closure slices`): one combined Plan + Final-verification block written by Worker 1, no Worker 2 build pass and no Worker 3 review pass. The authorising clause is the maintainer's cycle framing recorded in the build plan's [`## Cycle shape`][build-033] item 1 — "**Rationale extraction** ... Worker 1 MOVES the spec's deliberative layer into `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md`. Gates every later dispatch." The mechanism is [`docs/builder/BUILD.md`][build-md] `## Spec rationale extraction`; the procedure is [`docs/builder/worker-1.md`][worker-1] `### Performing the rationale move`.

The `## Build report (Worker 2)` and `## Review (Worker 3)` sections of [`ARTIFACT.md`][artifact-md] are deliberately absent, not omitted: no builder or reviewer pass ran. Everything those sections would carry that applies to a Worker-1-only doc pass — the validation run, the failability position, the hot-path and floor-verification declarations — is folded into `## Final verification (Worker 1)` below.

---

## Plan (Worker 1)

### Spec status-line re-verification

Read `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` lines 1-9 (title, shipped-in line, `Status:`, Owner, Predecessors) at the start of this spawn. All still describe the build's current state: the card is `DONE-033-0.0.9`, the `Status:` line reads `SHIPPED (0.0.9)` with all seven slices final-accepted, the unticked-checklist convention it invokes still holds, and no predecessor doc it names has been deleted. **No status-line edit was required by this pass**, and none was made. (The header did gain the rationale-companion pointer sentence — a route-1 edit, recorded under `### Spec changes made (Worker 1 only)`, not a status correction.)

### DRY analysis

- **Helper inventory checked.** Not applicable in the package sense: this pass edits no `.py` file and proposes no helper, so the package-wide AST inventory ([`docs/builder/worker-1.md`][worker-1] `### Package-wide helper inventory before helper planning`) has nothing to prevent. The analogous duplication risk for a rationale move is *prose* duplication between the two files, and it is answered below.
- **Existing patterns reused.** The whole shape is reused rather than invented: `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` (the immediately-preceding spec's companion, produced by the `032` residual cycle) supplies the section order, the per-Decision `Spec:` / `### Justification (moved from the spec)` / `### Alternatives considered (and rejected)` / `### Changes this Decision underwent` block, the `## Provenance of this record` byte-accounting shape, and the `## Non-Decision deliberation` catch-all. `docs/SPECS/spec-032-full_relay-0_0_9.md` supplies the post-move spec shape: the header pointer sentence, the one-line per-Decision `Rationale companion —` pointer, and the surviving-heading-plus-pointer treatment of `## Risks and open questions`.
- **New helpers justified.** None. No new document, section kind, or convention was invented.
- **Duplication risk avoided.** The move is a **cut**, so the single real duplication hazard is text existing in both files. Three mechanical controls answered it, all run as postconditions: (a) every moved block was asserted present in the rationale **and** absent from the spec; (b) the one rule held back in the spec (Risks item 6) was asserted *absent* verbatim from the rationale, which carries only its fallback plus a pointer; (c) the spec was asserted to contain zero occurrences of `Justification:`, `Alternatives considered (and rejected):`, `Revision history (kept inline`, `Preferred answer`, `Fallback:`, and `Rejected:`. The deliberate, bounded exception is the one the `032` companion also carries: the revision-history block duplicates, per Decision, what the `### Changes this Decision underwent` sections say — kept because a reviewer of a Decision's history and a reviewer of the implementation need different cuts of the same facts, and confined to that one block.

### Implementation steps

Line numbers are pin-at-write-time navigational hints against the **pre-move** spec.

1. Measure the pre-move spec (`174,055` bytes / `733` lines) and locate the four routes mechanically rather than by eye: the revision-history block (lines 11-17), the 12 `Justification:` / 12 `Alternatives considered (and rejected):` block pairs under Decisions 1-12, the `## Risks and open questions` body (lines 568-585), and the chronology parentheticals surviving in contract prose.
2. Extract each block byte-for-byte; strip only the label line (or the inline `Justification: ` / `Alternatives considered (and rejected): ` prefix), which becomes a `###` heading in the companion.
3. Re-point every in-page anchor inside moved text that names a spec section the companion does not have; leave `#decision-N--…` and `#risks-and-open-questions` alone, since the companion carries headings with exactly those slugs.
4. Judge each Risks item for a rule that outlives the build; hold such a rule back in the spec and move only its deliberation.
5. Write the companion: header + append-instructions, `## Provenance of this record` with the measured byte accounting, `## Revision history`, one `## Decision N — <exact spec heading text>` per Decision, `## Risks and open questions`, `## Non-Decision deliberation`, link definitions.
6. Apply the spec-side removals; insert the header pointer, the 12 per-Decision pointers, and the Risks pointer; prune link definitions the move left unreferenced; add the `rationale-*` / `spec-033-rationale` definitions.
7. Verify: byte-verbatimness both ways, anchor resolution in both files, link-definition definedness and on-disk existence, `check_spec_glossary.py`, `check_trailing_commas.py --check`, `git diff --check`, and the foreign-citation census as a postcondition.

### Test additions / updates

None, and none possible: this pass edits two markdown files and no `.py` file. `pytest` was **not** run — not needed and not permitted for this pass, and never with a `--cov*` flag anywhere in this cycle ([`docs/builder/BUILD.md`][build-md] `## Coverage is the maintainer's gate, not a worker's tool`).

### Implementation discretion items

None delegated — this is a single-worker pass with no builder to delegate to. Two choices were **assessed and decided here** rather than left open, because each could otherwise have been resolved silently and wrongly:

- **Where the held-back rule lands.** Risks item 6's rule went into Decision 4 as a bullet immediately after the `**Partition key**` bullet it annotates, rather than into Edge cases or a new Decision. Decision 4 owns `window_partition_for_prefetch`; the rule is about that function's parameter type.
- **How much of the Decision 5 retraction survives.** The retraction narrative moved; its trailing test citation (`test_fast_path_wire_parity_last_only`) stayed, restated as a bare contract sentence. A moved test citation is a contract citation, and contract citations stay in the spec.

### Spec slice checklist (verbatim)

`spec-033`'s own `## Slice checklist` carries **no** entry for this pass: Slice 0 is a *cycle* slice created by this cycle's build plan, not one of the seven spec slices (all of which shipped in `0.0.9`). The tick-and-audit surface is therefore the build plan's own Slice-0 line, reproduced verbatim, with the four dispatched routes as sub-boxes.

- [x] Slice 0: rationale extraction — MOVE the spec's deliberative layer to `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` -> `docs/builder/bld-033-slice-0-rationale_extraction.md`
  - [x] Route 1 — the whole `Revision history (kept inline so the spec is self-contained):` block, preamble line deleted rather than moved
  - [x] Route 2 — the 12 `Justification:` blocks and 12 `Alternatives considered (and rejected):` blocks, label lines becoming `###` headings
  - [x] Route 3 — the body of `## Risks and open questions`, spec keeping the heading plus a pointer, each item judged for a rule that outlives the build
  - [x] Route 4 — chronology framing embedded in surviving contract prose, count re-verified rather than inherited

---

## Final verification (Worker 1)

### Byte accounting per route

Measured, in bytes, against the pre-move spec (`174,055` bytes / `733` lines). Every figure below was computed by the extraction pass itself and written into the companion's `## Provenance of this record` from the same variables, so the document and this artifact cannot disagree.

| Route | What moved | Bytes |
|---|---|---|
| 1 | Revision-history block: 62-byte preamble line (**deleted**, not moved) + blank + five `Revision N` entries (**10,320** moved) | **10,383** |
| 2 | 12 `Justification:` blocks (**11,944**) + 12 `Alternatives considered (and rejected):` blocks (**7,549**), carrying 26 justification bullets/paragraphs and 26 rejected alternatives | **19,493** |
| 3 | `## Risks and open questions` body: 127-byte preamble + blank + **15** items (**10,204**) | **10,332** |
| 4 | Chronology framing in surviving contract prose, **9 sites** | **374** |
| — | The blank line separating each Decision's two blocks, belonging to neither (12 × 1) | **12** |
| | **Total removed from the spec** | **40,594** |

Spec after the move: **137,803** bytes / **643** lines — **36,252** bytes and **90** lines below its pre-move size. The 4,342-byte difference against the 40,594 removed is the net framing the move put back, itemised: header pointer 380, twelve per-Decision pointers 1,412, Risks pointer 397, the one held-back Decision 4 bullet 533, fourteen new link definitions 1,900, less four pruned link definitions 280. `40,594 - 4,342 = 36,252`, which is the measured delta exactly. Companion created at **70,960** bytes / **367** lines.

Two counts the dispatch supplied were re-derived rather than inherited, and one was wrong:

- **Route 3 carries 15 items, not 14.** The dispatch and the pre-flight measurement both said 14. Counted mechanically (lines starting `- **` between the preamble and the section's closing blank): 15, at pre-move spec lines 570-584. The companion states 15 and records the correction inline.
- **Route 4 carries 9 sites, not 8.** `grep -on 'Revision [0-9]'` returns 13 occurrences, 5 of them inside the revision history itself and 8 in surviving prose — the dispatch's figure, confirmed. A second grammar found a ninth: pre-move line 304's `(An earlier revision of this Decision described a '_dst_total_count - _dst_row_number' reversed-cursor scheme; …)`, a retraction parenthetical invisible to a capital-`R` numbered-revision pattern. It was treated as a route-4 site and its narrative moved to the companion under Decision 5's `### Changes this Decision underwent`. This is the standing lesson one spelling smaller: **a grep phrase samples a claim's vocabulary, it does not establish its population.**

### What was held back from the Risks body, and why

Exactly **one** item, following the `spec-031` precedent the dispatch names. **Risks item 6** — "`window_partition_for_prefetch` takes the raw Django relation field, not a `FieldMeta`" — was not purely a build-time choice:

- Its rule is **implementation-relevant rationale**: the forward-M2M reverse query name lives only on `field.remote_field`, which `FieldMeta` does not carry, so `optimizer/walker.py::_plan_connection_relation` resolves the live field via `model._meta.get_field(...)` (`_raw_relation_field`) and passes it. That is the "why" that changes how the partition is derived, and [`docs/builder/worker-1.md`][worker-1] `### Performing the rationale move` places such a sentence in the spec.
- The rule appears **nowhere else in the spec.** Decision 4's `**Partition key**` bullet names the helper and the per-relation-kind derivation but not the raw-descriptor requirement, so moving the item whole would have removed the only statement of it.
- Its closing clause — "recorded so a later reader does not re-flag it" — makes it a **verified-and-rejected note**, which is precisely the shape that survives a build.

The rule is now a Decision 4 bullet; only the item's `field_meta.py` fallback moved. The companion's `## Risks and open questions` opens with a paragraph naming the hold-back and states that every other item moved whole, and its item-6 line carries the fallback plus a pointer at the spec's Decision 4 — so the rule exists in exactly one file. The item's in-item `[Decision 4](#decision-4--…)` cross-reference became a self-reference once the rule sat inside Decision 4, so that one clause was restated as "The partition-key bullet above already presupposes that raw descriptor"; this is the only sentence in the whole move that is neither verbatim nor deleted, and it is recorded here for that reason.

No other item was held back. Items 4, 5, 8, 9, 11, 12 and 13 all read like standing constraints at first glance, and each was checked against the spec before moving: Decision 4's DISTINCT-guard and scalar-only bullets, the `## Edge cases and constraints` `.distinct()` and **Backend floor** bullets, Decision 6's fallback matrix, Decision 7, and `## Non-goals` already carry every rule those items rest on. An item whose rule is stated elsewhere in the spec is deliberation, and it moved.

### Foreign-citation census (postcondition)

Run as an **anchor** measurement — every occurrence of the shortest distinctive token `spec-033` across the tracked tree, classified — rather than a grep for a citation-shaped phrase.

- **Deep anchor links:** `grep -rIn --include='*.md' 'spec-033-connection_optimizer-0_0_9.md#' .` → **zero** hits outside the spec's own file. Confirms the dispatch's pre-verification.
- **Occurrences:** **278** in **43** tracked files, excluding the spec itself and this cycle's own plan and artifacts. Classified: **128 contract citations** (`Decision N` / `Goal N` / `Slice N` / `DoD` / `Edge cases` / `Test plan` / `Current state`), which survive by construction because the Decisions stayed in the spec; **133 bare identity mentions** with no citation grammar; **17 that matched a chronology word on the same line, every one a false positive** — closed-cycle records under `docs/builder/DONE/`, two sibling rationale companions' prose *about* this card, and one `KANBAN.html` data line. Each of the 17 was opened and read.
- **The one class the pre-verification could not rule out is empty:** no citation into this spec's revision history or its Risks body exists anywhere in the tree. **This move breaks no citation.**
- One historical pointer was checked because it looked like a live break: `docs/builder/DONE/build-027-filters-0_0_8.md` records that `tests/optimizer/test_walker.py` cited `spec-033 Decision 11 … / Revision 3` and `spec-033 Decision 6 / Revision 3`. Both sites now carry the `Decision N` half only — that hygiene sweep landed — so they are contract citations today.
- `spec-033`'s own outbound `[spec-032-rationale-d12]` anchor is **preserved**: it was referenced only from Decision 8's justification, so it moved into the companion together with the sentence that uses it, re-pathed for `docs/SPECS/appx/` (`spec-032-full_relay-0_0_9-rationale.md#decision-12--…`) and confirmed to resolve to a real heading in that file. Its now-unreferenced definition was pruned from the spec.

### Verification commands and their real results

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-033-connection_optimizer-0_0_9.md` → `OK: 38 terms - all have glossary entries and at least one spec link.`, exit 0. Same 38 as pre-flight. Four glossary refs used inside moved text (`glossary-djangoconnectionfield`, `glossary-djangonodefield`, `glossary-djangonodesfield`, `glossary-optimizerhint`) were checked for surviving uses in kept text *before* the move — 6, 2, 2 and 3 respectively — so no term could lose its only link.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-033-connection_optimizer-0_0_9.md docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` → exit 0. Both files carry the `<!-- LINK DEFINITIONS -->` delimiter and all 10 canonical group headers in order.
- `git diff --check` → exit 0, no whitespace errors or conflict markers.
- **Byte-verbatim proof, both directions.** For each of the 24 Decision blocks, the 5 revision entries, the Risks preamble and the 14 verbatim Risks items: the label-stripped, anchor-re-pointed text was asserted present in the companion **and** absent from the spec. Zero failures. Risks item 6 was asserted *not* present verbatim in the companion and its rule asserted present in the spec.
- **Anchor and link-definition proof, both files.** Every in-page `](#…)` anchor resolves to a heading in its own file (0 dangling); every `[text][ref-id]` use has a definition (0 undefined); every definition is referenced (0 unreferenced, after pruning `[walker]` from the companion, whose only use went back to the spec with the held-back rule); every definition's target file exists on disk. The 7 re-pointed anchor uses across 6 anchors — `#current-state` ×3, `#edge-cases-and-constraints`, `#error-shapes`, `#non-goals`, `#slice-checklist`, and the Test plan's `#slice-5--examplesfakeshoptest_querytest_library_apipy-extend-live` — are recorded in the companion. Note that `#error-shapes` and the Slice-5 anchor were **not** in the dispatch's list of anchors to expect, and `#test-plan` / `#doc-updates` / `#definition-of-done` (which the dispatch listed) do not occur in moved text at all.
- No `ruff` invocation: this pass touched no `.py` file, so neither `uv run ruff format .` nor `uv run ruff check --fix .` applies.
- No `pytest`. Not needed and not permitted for this pass.

### Declarations

- **Hot-path declaration:** `none`. This pass touches no runtime code.
- **Floor-verification scope:** `none`. This pass touches no Django / Strawberry / channels integration seam, so the floor versions were not read and are not cited.
- **Ownership partition:** the four files this cohort owns, per the build plan — `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md`, `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`, `docs/builder/bld-033-slice-0-rationale_extraction.md`, `docs/builder/worker-memory/worker-1.md`. `git status --short` after the pass shows exactly the first three plus the untracked concurrent `0_0_14.md` and Worker 0's untracked `docs/builder/build-033-connection_optimizer-0_0_9.md`; nothing outside the partition was written. `0_0_14.md` and `docs/builder/bld-003-final.md` were neither read as this cycle's nor touched.
- **Failability position:** no boundary, guard, gate, or rejection path was introduced — this pass ships no executable byte. The analogous proof for a text move is the byte-verbatim assertion above, which was run and which fails loudly if a block goes missing in either direction.

### Checklist audit

All four route boxes are `- [x]` and each contract landed on disk: route 1's block is gone from the spec and its five entries are in the companion; route 2's 24 blocks likewise, with the spec carrying 12 pointer lines; route 3's body is gone with the heading and pointer surviving and one rule held back; route 4's 9 sites are removed, and `grep -on 'Revision [0-9]\|An earlier revision'` over the spec now returns nothing. No box is ticked without a landed contract and none is left silently un-ticked.

### Summary

`spec-033`'s deliberative layer moved out of the spec into a new, tracked companion at `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md`, closing the last missing `-rationale.md` sibling in the archived `docs/SPECS/` run. Four routes carried **40,594** bytes out; the spec went from **174,055** to **137,803** bytes and the companion is **70,960**. One rule was held back in the spec. The move breaks no citation anywhere in the tree, both gate scripts pass, and every anchor and link definition in both files resolves. **The spec was not reconciled against `HEAD` in this pass**, and the companion says so under its own `**Not corrected here.**` paragraph, naming the suspected staleness so no later reader mistakes the file for reconciled.

### Spec changes made (Worker 1 only)

Every edit below is a route of the move or its consequence; none changes a contract. Line numbers cite the **pre-move** spec except where noted.

1. **Lines 11-17 removed; one pointer sentence inserted (post-move line 11).** Route 1. The 62-byte preamble line was deleted rather than moved because its claim that the history is kept inline is what the move falsified; the five `Revision N` entries moved verbatim. The replacement is the header's one-sentence pointer at the companion, mirroring `spec-032`'s post-move header.
2. **Twelve `Justification:` + `Alternatives considered (and rejected):` block pairs removed (lines 226-235, 248-250, 256-268, 284-291, 312-323, 336-341, 355-361, 369-380, 386-388, 394-404, 412-414, 420-422); one `Rationale companion —` pointer line inserted under each Decision.** Route 2. Each pointer names the count it points at (`its three rejected alternatives`, `its one rejected alternative`, …), counted mechanically per Decision.
3. **Decision 4 gained one bullet (post-move line 248), immediately after `**Partition key**`.** Route 3 hold-back: Risks item 6's rule, as argued above. This is the only place the move added a sentence to the spec rather than removing one, and the sentence's substance was already in the spec — it changed section, not existence.
4. **Lines 568-585 (the `## Risks and open questions` body) removed; one pointer paragraph inserted.** Route 3. The heading survives, so the six in-spec `#risks-and-open-questions` cross-references — and the `## Edge cases and constraints` **Backend floor** bullet's citation — still resolve, now to a heading that points at the companion.
5. **Nine chronology framings removed from surviving contract prose** (lines 52, 304, 409, 410, 484, 485, 486, 495, 504). Route 4. Line 52 lost `Revision 4 / ` from the `docs/TREE.md` mirror note; lines 409/410 lost `, Revision 4` and ` (Revision 4)` from the module map; lines 484/485/495/504 lost ` (follow-up fix, Revision 3)` and line 486 lost `, Revision 3` from the Test plan; line 304 lost the whole retraction parenthetical, its test citation restated as `Byte-parity is proven by \`test_fast_path_wire_parity_last_only\`.` Each removal is recorded in the companion under the owning Decision's `### Changes this Decision underwent`, or under `## Non-Decision deliberation`. The phrase "post-build DRY refactor" was **left** at lines 409/410 and 52: it names no numbered revision, and the whole no-new-source-module claim it qualifies is under review by Slice 2, so narrowing it here would pre-empt that slice.
6. **Four link definitions pruned** (`next`, `spec-029`, `spec-031`, `spec-032-rationale-d12`) — each referenced only from moved text — and **fourteen added** (`rationale-d1` … `rationale-d12`, `rationale-risks`, `spec-033-rationale`). Verified afterwards: zero unreferenced definitions and zero undefined uses remain in the spec.

**Not done in this pass, deliberately:** no reconciliation of the spec against `HEAD`; no `.py`, `docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, `KANBAN.html`, `CHANGELOG.md`, `TODAY.md`, `README.md`, `docs/README.md`, terms-CSV or kanban-DB edit; no commit, branch, or stash.

### Notes for Worker 1 (spec reconciliation)

Inherited by Slice 2 from disk rather than from a report. Every item below was noticed while reading the spec end to end for the move; **none was verified against source**, because this pass is text-only and the three read-only conformance cohorts own the verification.

- **Decision 9 and Decision 11 are the two most likely stale, and they are stale together.** Decision 9 says the `edges { node }` selection helpers "consolidate into the walker" and explicitly *rejects* `optimizer/selections.py` by name, on the card's bounded-extension pin. Decision 11's module map plus Revision 4's amendment say the card adds exactly one new source module (`utils/connections.py`). On disk `optimizer/selections.py`, `optimizer/nested_fetch.py`, `optimizer/nested_planner.py`, `optimizer/lateral_fetch.py`, `optimizer/single_parent_fetch.py`, and `optimizer/join_taxonomy.py` all exist and all carry this card's `_dst_row_number` / `_dst_total_count` / `_plan_connection_relation` / `window_partition_for_prefetch` vocabulary. If those are post-ship moves, Decision 11's map and Decision 9's rejected alternative both need the shipped shape stated directly, with a `**Post-ship:**` record naming the card that moved them.
- **Cursor-parity is sited on Decision 4 in the spec and on Decision 11 in the tests.** `tests/optimizer/test_walker.py` says `(spec-033 Decision 11, cursor-parity)` at two sites (the `Prefetch.queryset` own-`ORDER BY` pin and the fast-path divergence pin). The spec states the cursor-parity invariant in Decision 4 and gives Decision 11 only the hoist's module location — and Revision 2's finding 7 is precisely the promotion *out of* Decision 11. Whichever side is corrected, the two must agree; the spec's siting is the one Revision 2 chose deliberately.
- **`tests/optimizer/test_walker.py` records an inversion of a Decision 6 fallback.** One test docstring reads "The idea-#2 inversion of the historical spec-033 Decision 6 fallback". Decision 6's matrix is stated as monotonic ("this card strictly adds planned shapes, never changes unplanned ones"), so an inverted fallback is a post-ship contract change the Decision cannot currently describe.
- **A live staged anchor names this build's spec.** `tests/test_connection.py:1588` carries `# TODO(spec-033 Slice 1-2): root-connection no-regression fence. …` — verified present at the time of this pass, and it is the only `TODO(spec-033` anchor anywhere under `tests/`, `examples/`, or `django_strawberry_framework/`. `docs/builder/BUILD.md` `## Cross-slice integration pass` step 6 requires it discharged or explicitly re-classified before this cycle closes. It is not this pass's to touch (no `.py` edit) and it is not in the spec, so it needs an owner in a later slice or the integration pass.
- **The card-number spelling is inconsistent inside one Decision.** Decision 10's justification names `TODO-BETA-062-0.1.5` as the card keeping the rest of the fakeshop activation, then two clauses later calls the same card `051`; Risks item 2 does the same. One spelling is renumber rot. Measured after the move: `TODO-BETA-062-0.1.5` appears **5** times in the spec (post-move lines 79, 127, 230, 480, 490) and **3** times in the companion, while the bare `` `051` `` spelling appears **once** in the spec and **7** times in the companion. The correction therefore has a spec side and a companion side, and neither can be fixed without the other.
- **Three pre-archive path spellings survive in the spec's own prose.** Decision 1's "lives at" sentence, the `## Doc updates` KANBAN sub-bullet, and `## Definition of done` item 1 all still name `docs/spec-033-connection_optimizer-0_0_9.md`, the working location the spec occupied before the `NEXT.md` Step 8 sweep archived it. Nothing resolves prose, so no gate fails; `spec-032`'s post-move shape states the archived path plus the authoring path in one sentence and is the model. This is the `032` cycle's third rot class, not a rationale-move consequence.
- **An absolute developer path sits in the spec at three sites** (post-move lines 59, 91, 148: the Slice-1 checklist's `plans.py` sub-bullet, the `## Problem statement` upstream-proof paragraph, and the `## Borrowing posture` "From `strawberry-graphql-django`" paragraph), each citing `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/...`. `AGENTS.md` names that checkout as the upstream reference, so this may be house convention rather than rot — worth a decision either way, since a machine-specific absolute path in a shipped spec is not reproducible for another reader. Count measured, not inherited.
- **`## Risks and open questions` now has a heading with no body.** That is the `spec-032` post-move shape and is intended. Slice 2 should keep it: six in-spec cross-references plus the Backend-floor bullet point at that heading.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[artifact-md]: ARTIFACT.md
[build-033]: build-033-connection_optimizer-0_0_9.md
[build-md]: BUILD.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
