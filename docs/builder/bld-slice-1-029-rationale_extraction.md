# Build: Slice 1 — Rationale extraction

Spec reference: `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` (whole file; before the move it was 823 lines / 170,042 bytes)
Status: final-accepted

**Dispatch shape.** This slice has no Worker 2 pass. `BUILD.md` `## Spec reconciliation` makes Worker 1 the only worker permitted to mutate a spec or its rationale companion, so a builder would have nothing it is allowed to write; the build plan's `## Dispatch-shape deviation for the two Worker-1-owned slices` records the deviation. Worker 3 is dispatched off `planned` and reviews the **performed** move. Both the plan and a full report of what was performed are below, so Worker 3 can review the result against the stated intent.

---

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** Not applicable, and this is a decided answer rather than a skip: this slice writes no `.py`, plans no helper, shared constant, validation branch, coercion utility, or test helper, and the build plan's ownership partition gives it exactly three writable files, none of them source. The package-wide AST inventory exists to prevent duplicated *code* shapes at plan time; running it here would produce ~1,600 lines nothing in this slice could consume. The condition that would change the answer: any slice of this cycle that touches `django_strawberry_framework/` — Slice 2 does, and owes the inventory.

- **Existing patterns reused.** The rationale companion's shape, depth, and voice are taken from the two most recent siblings, both created by residual cycles of the same kind: `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md` (`## Provenance of this record` -> `## Revision history` -> per-`## Decision N` with `### Justification (moved from the spec)` / `### Alternatives considered (and rejected)` / `### Changes this Decision underwent` -> `## Non-Decision deliberation`) and `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`. The spec-side pointer sentences reuse `docs/SPECS/spec-028-orders-0_0_8.md`'s two forms verbatim in shape: the header paragraph at its line 8, and the per-Decision `Rationale companion — this Decision's justification and its N rejected alternatives: [Decision N][rationale-dN].` line.
- **New helpers justified.** None. No new convention is invented; every structural element already exists in `appx/`.
- **Duplication risk avoided.** The one real risk in a move of this kind is **copying instead of moving**, leaving the same paragraph in two files that then drift. Prevented by construction: the excisions and the extraction were performed by one script over one read of the source, so every byte in the companion is a byte the spec no longer has. Proven afterwards by the byte arithmetic under `### The arithmetic` and by re-grepping the spec for the moved section labels (`Justification:` and `Alternatives considered (and rejected):` both read `0` in the spec now).

### Implementation steps

Line numbers below are pin-at-write-time against the pre-move spec (823 lines). They are the anchors the move was performed on; the file has since shifted and they will not resolve now.

1. Enumerate, before touching anything, the two citation populations the move can break (see `### Citation sweep`), line-scoped, whitespace-flattened, join-aware, and case-insensitively.
2. Excise `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:11-57` (the `Revision history` block) and replace it with the one-paragraph header pointer at the `spec-028` shape.
3. Excise each Decision's `Justification:` + `Alternatives considered (and rejected):` pair and replace each with one `Rationale companion —` pointer line naming the count of rejected alternatives: D1 `302-311`, D2 `317-325`, D3 `346-357`, D4 `377-388`, D5 `394-403`, D6 `409-417`, D7 `431-440`, D8 `458-468`, D9 `474-481`, D10 `487-496`, D11 `506-514`, D12 `522-529`.
4. Excise the body of `## Risks and open questions` (`643-654`), keep the heading (nine in-page references resolve to it), and replace the body with a pointer plus the one item that states a live rule.
5. Delete the two cross-reference clauses the move falsifies (the Predecessors line and the Current-state glossary bullet each claim the Risks section "flags" the missing-glossary-heading caveat).
6. Create `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`: header, `## Provenance of this record`, the revision history verbatim, twelve `## Decision N` sections, `## Non-Decision deliberation`, `## Risks and open questions`, and a complete `<!-- LINK DEFINITIONS -->` block with all ten canonical group headers, paths relativized from `docs/SPECS/appx/`.
7. Repoint every in-page anchor inside moved text that names a spec section the companion does not have.
8. Add the fourteen new link definitions to the spec; prune any definition the move orphaned.
9. Verify: `check_spec_glossary.py`, `check_citations.py`, the `source-layout` markdown scaffold, every in-page and cross-file anchor in both files, the citation populations from step 1, and the byte arithmetic.

### Test additions / updates

None. This slice writes no `.py` and adds no test. No temp tests are appropriate.

The verification this slice does owe is mechanical rather than test-shaped, and Worker 3 can re-run all of it read-only:

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`
- `uv run python scripts/check_citations.py`
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`

### Implementation discretion items

None. Every choice this slice makes is either fixed by `worker-1.md` `### Performing the rationale move` or is a judgement recorded under `### Judgements made` below. There is no Worker 2 pass to delegate to.

### Spec slice checklist (verbatim)

Not applicable in the form the template names. `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`'s `## Slice checklist` describes the three **functional** slices the card shipped in `0.0.9`; it contains no sub-bullet for this residual cycle's Slice 1, which is a documentation move authored years after the card closed. This slice's contract comes from the build plan's checklist line and from `BUILD.md` `## Spec rationale extraction`, so its boxes are written here in the same position and under the identical tick-and-audit discipline.

- [x] The whole `Revision history` block leaves the spec.
- [x] Every `Justification:` passage under every Decision leaves the spec.
- [x] Every `Alternatives considered (and rejected):` list under every Decision leaves the spec.
- [x] The deliberative half of `## Risks and open questions` leaves the spec; only live contract stays.
- [x] The `### Reference-package parity checkpoint` argumentation is judged either deliberation or contract, and the judgement is recorded with its reason.
- [x] Every rationale entry names the spec Decision it belongs to, by heading and by anchor.
- [x] Every Decision keeps a one-line pointer naming what was moved and where.
- [x] The revision-history content is redistributed under the Decision it belongs to, not pasted as one undigested block.
- [x] Prose the current decisions have falsified is deleted rather than moved.
- [x] Every `#"unique substring"` citation in the spec, and every citation elsewhere pointing into spec-029, is enumerated before the move and re-verified after it.
- [x] The citation sweep is measured line-scoped, whitespace-flattened, join-aware, and case-insensitively.
- [x] The rationale file carries a complete link block: ten canonical group headers, fixed order, present even when empty, alphabetical within group, paths relativized from `docs/SPECS/appx/`, every path disk-exists-checked.
- [x] The spec's link block drops every definition the move orphaned and keeps every one still used.
- [x] `check_spec_glossary.py` still exits 0.
- [x] `check_citations.py` still passes.
- [x] Before-and-after byte counts recorded for both files, with the arithmetic stated.

---

## Build report (Worker 1, performing pass)

There is no Worker 2 on this slice; this section is the record of what Worker 1 actually performed, in the position a builder's report would occupy.

### Files touched

- `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` — the deliberative layer excised; header pointer, twelve per-Decision pointers, a contract-only Risks body, and fourteen link definitions added. 823 lines / 170,042 bytes -> 679 lines / 133,839 bytes.
- `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` — **created**. 459 lines / 68,917 bytes.
- `docs/builder/bld-slice-1-029-rationale_extraction.md` — this artifact.
- `docs/builder/worker-memory/worker-1.md` — memory entry appended.

Nothing else. In particular: no `.py`, no `-terms.csv`, no `KANBAN.*`, no `docs/GLOSSARY.md`, no `docs/TREE.md`, no `CHANGELOG.md`, no sibling spec or rationale.

### What moved, measured

Populations were enumerated, not asserted. Each figure below was produced by a script over the pre-move file.

| Moved | Population | Bytes |
|---|---|---|
| `Revision history` block | preamble + 7 `Revision N` entries over 47 lines | 17,883 |
| `Justification:` blocks | 12 blocks, 33 bullets | see below |
| `Alternatives considered (and rejected):` blocks | 12 blocks, 25 rejected alternatives (2 / 1 / 4 / 4 / 2 / 1 / 2 / 3 / 1 / 2 / 2 / 1 for D1-D12) | 16,278 combined with the Justification blocks |
| `## Risks and open questions` body | preamble + 10 preferred-answer / fallback items | 6,620 |
| Falsified cross-reference clauses | 2 | 181 |

### The arithmetic

**Superseded by the apply-changes pass.** Three figures in the original version of this section did not re-derive (Worker 3's M1), and the section duplicated a ledger that belongs in one place. The single corrected ledger now lives in `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` `## Provenance of this record` — the durable record; this artifact closes with the cycle. What was wrong and what replaced it is under `## Apply-changes pass (Worker 1)` -> `### M1 — byte arithmetic` below.

The two figures this per-cycle artifact still owns, both re-measured in the apply-changes pass and both reflecting every edit of this slice, the M2 chronology cuts and the E1 collapse included:

- **Spec:** 170,042 bytes / 823 lines at `HEAD` -> **133,713** bytes / 679 lines on disk. Net **-36,329**.
- **Rationale companion:** created; **58,950** bytes / 428 lines on disk.

**The spec did not grow.** Every byte the move added back to it is either a pointer the `### Performing the rationale move` rules require or a link definition those pointers need.

### Citation sweep

**Population A — `#"unique substring"` citations inside the spec.** Measured `grep -o '#"'` for occurrences (not matching lines) and `grep -o '#"[^"]*"'` for the closed forms; the two counts agreeing at **7** is itself the proof that none is wrapped across a line, and a separate multiline regex confirmed `WRAPPED = 0` in both files. All 7 survive unchanged; **none lived in moved text**, which was verified before the move rather than discovered after:

| Citation | Home | Disposition |
|---|---|---|
| `#"Meta.exclude must be a non-string sequence"` | Edge cases | stays |
| `#"No CHANGELOG.md updates unless told"` (x2) | Key glossary references; Doc updates | stays |
| `#"No pytest after edits"` | Definition of done item 17 | stays |
| `#"annotations[field.name] = convert_scalar(field, cls.__name__)"` | Slice checklist, Slice 3 | stays |
| `#"extensions=[_CaptureExt()]"` | Current state | stays |
| `#"suppress_pk_annotation"` | Decision 4 body | stays |

The new rationale file carries **0** `#"..."` citations, so the move created no new citation surface for a future edit to break.

**Population B — references elsewhere pointing into spec-029.** Swept with a line-scoped grep and, separately, with a whitespace-flattened join-aware case-insensitive regex (`(?i)spec[-_ ]?029`) over every tracked `.md` / `.py` / `.csv`. Both sweeps returned the **same 25 tracked files** plus `KANBAN.html`, so no reference is visible only when wrapped. A script then resolved every markdown link into spec-029 from every other tracked file — link-definition and inline forms, file existence and anchor existence both — and reported **0 broken**. Every Decision heading the siblings cite (`spec-030` / `spec-031` / `spec-032` / `spec-033` cite Decisions 6 and 11; `spec-017`'s companion cites Decision 7; `spec-001`'s companion cites Decision 3) is unchanged, because only the Justification and Alternatives *under* a heading moved.

**One outbound citation the move breaks.** `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` (line 229 at time of writing) cites `` [`spec-029`][spec-029] `P1.1 — stale extension-lifecycle model` ``. That string lived only in the spec's revision history and now lives only in the new companion. It is a prose citation, not a markdown link, so no link check sees it; and `scripts/check_citations.py` resolves `path::Symbol` only with `docs/` out of scope, so no gate sees it either. That file is a read-only sibling for this cycle (the build plan's fence and the allowed-files list both exclude it), so the repair is recorded under `### Notes for Worker 1 (spec reconciliation)` for the deferred-work catalog rather than performed here.

### Judgements made

- **The `### Reference-package parity checkpoint` stays in the spec, whole.** The prompt left this to judgement; the answer turned out to be mechanically forced rather than discretionary. The table holds the **only** links in the spec for three terms the companion CSV requires to be linked — `RelatedFilter`, `RelatedOrder`, `RelatedAggregate` (rows 35-37 of `spec-029-consumer_dx_cleanup-0_0_9-terms.csv`) — so moving it fails `check_spec_glossary.py`, and the CSV is explicitly outside this slice's write list. Measured before deciding: a script computed which reference ids would have their last surviving use inside the planned move set, and returned exactly those three plus `upstream-cookbook`. Independently, the prose around the table is scope-setting ("it does not itself port a parity surface — it hardens schema construction, adds a type-metadata inspection command, and expresses GraphQL nullability overrides through `Meta`"), which is Non-goals-shaped and therefore contract under `### Performing the rationale move`. Only the table's *provenance* left, as the rev5 P2 entry in the moved revision history.
- **`## Risks and open questions` keeps its heading and one item's rule.** Nine in-page references pointed at that anchor; six of them are in surviving text (the Slice checklist's Slice 2 bullet, Decision 4's Test-placement paragraph, Decision 11's CHANGELOG-heading paragraph, Definition-of-done item 1, and the two clauses noted below). Deleting the section outright would have dangled all six. The surviving body is a pointer plus one rule that genuinely outlives the build: every mechanism claim is pinned to the `0.316.0` derivation baseline while `pyproject.toml` declares an open floor, so a Strawberry version that stops calling the `extensions=` factory per request requires Decision 3 to be **re-derived by execution** against that version. That is implementation-relevant rationale under the carve-out — a reader who does not have it re-reads a stale mechanism forward.
- **Two clauses were deleted rather than moved.** The Predecessors line and the Current-state glossary bullet each claimed the Risks section "flags" the missing-glossary-heading caveat. After the move it does not, so both clauses are false wherever they sit; rule 2 deletes rather than moves. 181 bytes.
- **The revision-history preamble was deleted rather than reproduced.** "Revision history (kept inline so the spec is self-contained)" is precisely the assertion this move made untrue. 63 bytes.
- **Four in-page anchors inside moved text were repointed, not left verbatim.** `#definition-of-done`, `#non-goals`, `#out-of-scope-explicitly-tracked-elsewhere` (x2), and `#implementation-scaffolding--staging-notes` name spec sections the companion does not have; each now resolves to the spec through a reference-style link. The `#decision-N--...` anchors and `#risks-and-open-questions` were left exactly as written: the companion carries headings with those same slugs, so they resolve locally, which is where a reader of a moved sentence wants to land. This is the same treatment `spec-028`'s companion gave its own moved revision history.
- **The revision history was redistributed, not pasted.** It appears once verbatim under `## Revision history` (a chronology is what a reviewer of a decision's history actually needs), and its findings are *also* redistributed under the Decision each one changed, in twelve `### Changes this Decision underwent` sections. The mapping was derived by extracting every `#decision-N--` anchor from each revision entry and then reading all 46 entry lines for plain-text Decision mentions the anchor scan misses — which is how the rev7 "Slice 3 two-set split" (plain-text "Decision 8") and the rev7 "Relay-suppressed pk everywhere" (plain-text "Decision 4") entries were placed. Fifteen findings belonging to no Decision are grouped under `## Non-Decision deliberation` in four themed subsections rather than dropped.
- **No unverified HEAD-divergence claim was written into the rationale.** The build plan's section C enumerates nine spec-vs-HEAD divergences and labels each "a claim to re-derive". Slice 1 re-derived none of them, so restating any as fact in a durable document would manufacture exactly the false-provenance this cycle exists to remove. The companion's provenance says plainly that Slice 1 moved text and did not reconcile, and the divergences are carried in this artifact instead.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` -> **pass**, `OK: 44 terms - all have glossary entries and at least one spec link.`
- `uv run python scripts/check_citations.py` -> **pass**, `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md).`
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` -> **pass** (exit 0). This is the `source-layout` pre-commit hook's markdown link-definition scaffold; the block was written correct by construction rather than auto-fixed.
- Anchor validator over both files -> **0 problems**: every in-page `](#...)` resolves to a heading in its own file, every link-definition target exists on disk, and every cross-file `#anchor` target resolves to a heading in the target file.
- Orphan check on the spec's link block -> **0 definitions orphaned by the move** and **0 dangling uses**. Worth stating because it was not guaranteed: `[upstream-cookbook]`, `[next]`, and `[spec-004]` each had uses in moved text, and each survives through a use in text that stayed (the parity table's lead-in, Decision 2's body, Decision 3's mechanism paragraph).
- `uv run ruff format .` / `uv run ruff check --fix .` -> not run. This slice touches no `.py`; running the repo-wide write-mode formatters with a concurrent session active would churn files this slice does not own.
- No `pytest`. `AGENTS.md` forbids it after edits unless asked, and no `.py` changed.
- `git status --short` after the pass shows this slice's three files plus four files belonging to a **concurrent session** — `docs/review/review-0_0_14.md` (modified), `docs/review/rev-mutations__operations.md`, `tests/mutations/test_operations.py`, and the build plan itself. Three of those were already present at this slice's start and none was touched: reported, never reverted (`AGENTS.md` rule 34).

### Failability proofs

None; this pass introduced no new boundary, guard, gate, or rejection path. It moved documentation text.

### Hot-path budget

Not applicable; the build plan declares Slice 1 `none`.

### Floor verification

Not applicable; the build plan declares Slice 1 `none` (no framework surface).

### Notes for Worker 3

- The move was performed by script over a single read of the source, so the companion's verbatim sections are byte-identical to what left the spec except for the four repointed anchors and the two label-lines-to-headings conversions listed under `### Judgements made`. A pristine pre-move copy sits **outside the repo** at `<scratchpad>/spec-029.before.md`; `git show HEAD:docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` is the read-only reference to diff against if you want to re-derive the excisions yourself. Do not use `git stash` / `git checkout` / `git restore` — concurrent sessions are writing this tree.
- The cheapest independent re-derivation of the central claim (a move, not a copy) is `grep -c 'Justification:' <spec>` and `grep -c 'Alternatives considered' <spec>`, both of which must read `0`, against `12` each in the companion.
- Every number in this artifact was measured at the moment it was written. If you re-measure the spec's byte count and it disagrees, suspect a concurrent session before suspecting the arithmetic — and say which.

### Notes for Worker 1 (spec reconciliation)

Slice 3 owns all of the below. None was corrected in this pass, and none was re-derived by it, so each is inherited as a claim rather than a finding.

1. **The nine spec-vs-HEAD divergences in the build plan's `### C. Spec-vs-HEAD divergences` are unchanged by this slice.** The move did not touch any of the sentences they name — every one lives in contract prose that stayed. The two that now have a *new* home for their explanation are worth naming, because Slice 3's correction and its record are in different files: divergence 1 (scope widened past scalar-only) belongs under Decision 10's entry in the companion, and divergence 2 (the apply call site is `convert_field_output`, not `convert_scalar`) belongs under Decision 7's.
2. **`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` cites a string that has left the spec.** Its `` [`spec-029`][spec-029] `P1.1 — stale extension-lifecycle model` `` reference should point at `spec-029-consumer_dx_cleanup-0_0_9-rationale.md` instead. That file is a read-only sibling under this cycle's fence, so this is a deferred-work-catalog item for `bld-final-029.md`, not a Slice 3 edit — unless the maintainer widens the fence.
3. **`docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md` records "spec-029 (6 hits) | P1 / P1.1 / Decision 3 / Risks" as its read-only-sibling assessment.** Two of those four landmarks (P1, P1.1) are now in the companion rather than the spec. That file is an archived per-cycle artifact and is out of scope for every slice of this cycle; noted only so a future reader does not mistake the drift for a miss.
4. **Definition-of-done item 1 still points at `## Risks and open questions` for a deferral that section no longer describes.** Its "the three net-new symbols are intentionally NOT in the CSV" claim is the build plan's divergence 5 and is false at HEAD; its `(per [Risks and open questions](#risks-and-open-questions))` pointer now leads to a section that carries only the derivation-baseline rule. Slice 3 should fix the claim and the pointer in one edit rather than repointing a sentence it is about to delete.
5. **The `[rationale-dN]` / `[rationale-risks]` / `[spec-029-rationale]` definitions added to the spec are load-bearing for the companion's discoverability.** If Slice 3 renames a Decision heading, both files' anchors move together — the companion's `## Decision N` headings deliberately carry the spec's exact titles so the slugs match. Rename in both, or the pointer chain breaks silently in the direction no gate checks.

---

## Review (Worker 3)

**Reference used.** `git show HEAD:docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` into a scratch path **outside** the repo, then `diff -u`. No `git stash` / `checkout` / `restore` / `worktree` at any point. Byte/line counts confirmed independently: HEAD 823 lines / 170,042 bytes; current spec 679 / 133,839; companion 459 / 68,917 — all three match the build report exactly.

**Instruments were controlled before being believed.** Three of the checks below would have read identically whether or not they measured anything, so each was given a positive control first; one control changed the conclusion:

- The "reproduced in the companion" comparator was controlled by feeding it a line known to be in both files (found) and by the reverse direction (0 hits) — it distinguishes.
- The anchor / link-def validator was controlled by mutating one anchor to `#decision-9--BOGUS` in an in-place copy; it reported exactly `('spec-029-d9', 'MISSING ANCHOR decision-9--BOGUS')` and nothing else.
- `scripts/check_trailing_commas.py --check` was controlled by swapping two adjacent link definitions out of alphabetical order in a scratch copy of the companion. **It still exited 0** — the scaffold hook does **not** enforce within-group ordering, so the build report's passing `--check` is evidence for the ten group headers and nothing about the sort. Ordering was therefore re-derived by hand (result under "What looks solid").

### High:

None.

### Medium:

#### M1 — The reproduction arithmetic does not re-derive, and the un-derivable figures are written into the durable companion

`docs/builder/bld-slice-1-029-rationale_extraction.md` `### The arithmetic`, and the same sentence again at `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md:24`:

> Of this file's bytes, **40,022** are that moved text reproduced verbatim. The arithmetic against the 40,781 bytes of moved *sections* closes on two items: the 63-byte revision-history preamble … and 696 bytes of `Justification:` / `Alternatives considered (and rejected):` label lines …

Most of the ledger is exactly right and was re-derived digit-for-digit:

| Claim | Re-derived | Verdict |
|---|---|---|
| net spec drop 36,203 | `170042 - 133839 = 36203` | exact |
| 17,883 + 16,278 + 6,620 = 40,781 moved-section bytes | byte-summed HEAD lines 11-57, the twelve Decision ranges, and 643-654 | exact |
| 181 bytes of falsified clauses | `len(old)-len(new)` on the two edited lines = 112 + 69 | exact |
| 40,962 left / 4,759 added back | 40,781 + 181; 40,962 - 36,203 | exact |
| 25 rejected alternatives, 33 justification bullets, per-Decision split 2/1/4/4/2/1/2/3/1/2/2/1 | counted in the companion; every one of the twelve spec pointer lines names the right number | exact |

The three that do not:

- **696** — there are 24 label lines in the HEAD spec (12 + 12, confirmed by a `Counter` over the raw bytes) totalling **660** bytes with newlines (`12*15 + 12*40`). 696 is not reachable from any grouping I can construct; even charging each label its trailing blank line gives 684.
- **63** — the preamble line `Revision history (kept inline so the spec is self-contained):` is **62** bytes with its newline. (63 works only if the following blank line is charged to it, which the sentence does not say.)
- **40,022** — measured directly, the moved content reproduced in the companion is **39,996** bytes spec-side / **39,933** bytes companion-side. Neither is 40,022, and 40,781 - 62 - 660 = 40,059 is the largest defensible figure.

And **"verbatim" is not accurate for ~2,178 bytes of it**: five lines carrying four repointed in-page anchors are reproduced *modified*, which the very next paragraph of both files concedes. So the sentence asserts a byte figure that is not a measurement, then says it "closes exactly" against a decomposition that does not measure either.

Why it matters, and why Medium rather than Low: `BUILD.md` `## Claims are proven mechanically, never accepted on prose` names a stated count as one of the three shapes that must re-derive, and this one is now in a **durable, tracked** document rather than a per-cycle scratchpad — every later reader will treat it as measured. It is also the exact failure mode that section warns about ("a count asserted in the same breath as the lesson it illustrates is routinely wrong — measure as you write the number").

**Nothing was lost.** This is an accounting defect, not a content defect: see "What looks solid" for the independent proof that every moved chunk is present in the companion.

**To close:** in both files, replace the un-derivable figures with measured ones and qualify "verbatim" — e.g. *"The 40,781 bytes of moved sections carry over in full except for 722 bytes that did not: the 62-byte revision-history preamble line, deleted deliberately, and 660 bytes of the 24 `Justification:` / `Alternatives considered (and rejected):` label lines, which became `###` headings here. The remainder is reproduced byte-for-byte apart from the four repointed in-page anchors noted below."* Any wording is fine provided each number is one a reader can re-derive from the two files.

#### M2 — The spec still carries a retraction paragraph, in Decision 8

`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:333`:

```docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:333
The override validation splits across the existing three-stage type-construction flow. (An earlier draft proposed a single `_validate_nullability_overrides(meta, selected_names, consumer_authored_fields, model)` helper called from `_validate_meta` — that is not implementable: [`_validate_meta`][base] runs *before* `_select_fields`, …)
```

This is a chronology fragment inside the contract: a reader has to know what an earlier draft proposed in order to read the sentence. `BUILD.md` `## Spec rationale extraction` is explicit — "no amendment block, no retraction paragraph … a reader must never reconstruct what is currently true by applying a chronology to it" — and `worker-1.md` `### Performing the rationale move` lists "Retraction paragraphs — a claim a decision is no longer permitted to make, and what replaced it" under **What MOVES**.

It is also now duplicated. `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` Decision 8 `### Changes this Decision underwent` already records the same thing twice over — the rev1 single-helper signature and the rev2 P1 finding that it is not implementable, with the same three reasons. Two copies of one retraction in two files is precisely the drift the move exists to prevent.

A repo-wide sweep of the spec for chronology vocabulary (`earlier|initially|first draft|as of revision|amendment|retract|superseded|was rewritten|the review found|feedback pass|rev[0-9]` and a dozen more spellings) returns **only this one site**, so the finding is narrow and the fix is one sentence.

**Careful — do not over-cut.** The *constraint* half is implementation-relevant rationale and must stay under the carve-out; only the "an earlier draft proposed" framing is deliberation. A closing rewrite is roughly: *"The override validation splits across the existing three-stage type-construction flow; it cannot be a single helper called from `_validate_meta`, which runs before `_select_fields`, before `consumer_authored_fields` is computed, and before Relay-pk suppression is known, so `selected_names` and `consumer_authored_fields` do not exist there."* The rejected single-helper shape is already recorded in the companion and needs nothing added.

Note this passage was **inherited unchanged from HEAD** — Slice 1 did not create it. It is still Slice 1's, because Slice 1's contract is "the deliberative layer leaves the spec" and this is the deliberative layer.

#### M3 — The one citation this move breaks was routed to a deferred catalog on a constraint that is half true (escalated; see Notes for Worker 1)

Independently confirmed the breakage is real. `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:229` cites `` [`spec-029`][spec-029] `P1.1 — stale extension-lifecycle model` ``; that string exists in the HEAD spec, does **not** exist in the current spec, and now exists only at `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md:46`. No gate sees it: `check_citations.py` resolves `path::Symbol` only and puts `docs/` out of scope (re-ran it — 789 citations resolve, and this is not among them).

I also swept for the whole class rather than the one instance handed to me. Every `` ` ``-quoted and `"`-quoted span of 12+ characters in all 26 tracked files that mention spec-029 (flattened + case-insensitive `(?i)spec[-_ ]?029`) was tested for `in HEAD-spec and not in current-spec`. **Nothing landed in "neither file"** — no string was lost. Beyond the spec-004 site the only other real hit is `docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md`, an archived per-cycle artifact that the build report already names and that is correctly out of scope.

The disposition is what I disagree with. The build report says the file is excluded by "the build plan's fence **and** the allowed-files list". The **fence** does not exclude it — the maintainer fence is "spec files and `.py` files only", and a `-rationale.md` under `docs/SPECS/appx/` is a spec companion, which `BUILD.md` `## Spec and build-plan filename pattern` treats as a tracked sibling of the spec. Only the plan's per-slice ownership table excludes it, and `BUILD.md` `### Parallel cohorts under a declared ownership partition` gives the in-flight remedy for exactly that: *"If a collision surfaces mid-flight (a cohort needs to write a file it does not own), Worker 0 stops that cohort, folds the file into the owning cohort's scope or re-partitions, and records the correction in the plan."* Routing to the deferred catalog skips that step.

The standing repo lesson points the same way: budget the post-move `#"substring"` sweep into the **moving** slice. In a sibling cycle the repair cohort grew threefold because each pass swept only the vocabulary of the finding it was handed.

Because the resolution needs a plan-level re-partition rather than a spec edit, this is escalated rather than held — see `### Notes for Worker 1 (spec reconciliation)` for the resolution paths. It is **not** part of the `revision-needed` above.

### Low:

#### L1 — "mechanically forced rather than discretionary" over-states what the parity-checkpoint test shows

The judgement was tested rather than read. Two scratch copies of the current spec, checked with `--terms` / `--glossary` pointed at the real companions:

- **whole `### Reference-package parity checkpoint` section removed** → `exit=1`, and the failures are *exactly* the three terms named: `RelatedFilter`, `RelatedOrder`, `RelatedAggregate`. The mechanical constraint on the **table** is real, and the gate is distinguishing.
- **both prose paragraphs removed, table kept** → `OK: 44 terms`, `exit=0`.

So the forcing applies to the table, not to the section. The prose half is a judgement — a defensible one: the first paragraph's closing sentence is the table's lead-in and cannot leave without orphaning it, and both paragraphs are scope statements ("it does not itself port a parity surface"), which is Non-goals-shaped and therefore contract under `worker-1.md`, with the tie-break rule ("when it is unclear … it stays") pointing the same way. The build report does say "**Independently**, the prose … is Non-goals-shaped and therefore contract", so the reasoning is fully disclosed; only the opening clause, applied to the section as a whole, reads as though both halves were forced. **To close:** scope the word — the table is forced, the prose stays on the contract argument. One clause, in both the artifact and `…-rationale.md:22`.

### DRY findings

- **`## Revision history` is reproduced verbatim (18,170 bytes, 26% of the companion) alongside a complete redistribution of the same findings.** The seven revision entries carry 38 nested finding bullets; the twelve `### Changes this Decision underwent` sections carry 43 bullets covering the same material, and `## Non-Decision deliberation` (4,671 bytes) carries the remainder in four themed groups. Every finding is therefore stated twice inside one file, in two different wordings. `BUILD.md` requires the per-Decision form ("every change the decision has undergone, with the round that caused it"); it does not require the chronological block. This is the existence challenge, raised as a first-class DRY finding and routed to the maintainer — see Notes for Worker 1. It is **not** grounds for `revision-needed` on its own and is not part of the outcome below.
- **The byte ledger is duplicated between the per-cycle artifact and the durable companion.** `### The arithmetic` here and `## Provenance of this record` at `…-rationale.md:11-24` state the same figures in the same order. `START.md` "Temp artifact conventions" makes `docs/builder/bld-*.md` the home for per-cycle measurement — it closes with the cycle. The durable half of the provenance (what moved, the parity judgement, the four repointed anchors, the outbound broken citation, "Slice 1 did not reconcile") is genuinely worth keeping; the byte accounting is not, and keeping it in two places is what let one wrong number land in the durable copy (M1). Recommend the companion keep the qualitative provenance and cite the artifact for the ledger.
- No repeated string keys, error fragments, helpers, or parallel data flows — this slice writes no code.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are unchanged. The slice touches no `.py` at all; the only `.py` churn in the tree is the untracked `tests/mutations/test_operations.py`, which the build plan attributes to a concurrent session and which is neither this slice's nor mine to touch.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

This slice is entirely a docs change, so the checklist applies in full:

- **Version strings / statuses / card IDs.** The spec's `Status:` line still reads `SHIPPED (0.0.9)`, card `DONE-029-0.0.9`, Slice checklist correctly unticked under the shipped-spec convention. The diff touches none of them; re-read against the current tree and each still holds. No version file is in the diff.
- **KANBAN movement.** None; the fence excludes it.
- **Markdown links introduced or moved point at existing files.** Verified mechanically for both files — every link definition's file resolved on disk and, where the target carried an `#anchor`, the anchor resolved to a real heading in that file. Spec: 110 defs, 110 uses, 0 undefined, 0 unused, 0 unresolved in-page anchors. Companion: 53/53, same zeros. The path re-relativization from `docs/SPECS/` to `docs/SPECS/appx/` (one level deeper: `../../GLOSSARY.md`, `../../../KANBAN.md`, `../spec-0NN-….md`) is correct in every definition.
- **Archival.** Not applicable; the spec did not move (the build plan records that it was already archived and does not move for this cycle).
- **Verbatim drop-ins.** Verified far past `diff` — see "What looks solid".
- **No obsolete "coming soon" / "planned" wording** introduced. The surviving Risks rule and the new header pointer both read as present-tense contract.
- **Script-rendered docs.** None regenerated; `docs/TREE.md` and `docs/GLOSSARY.md` are untouched and outside the fence.

### Failability proofs, hot path, floor, static helper

- **Failability proofs — obligation considered and dismissed, with the reason.** `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a **new boundary, guard, gate, or rejection path**, and explicitly exempts relocated bodies and doc edits. This slice moves documentation text: it adds no guard, no rejection path, and no code of any kind. Manufacturing a proof here would be a rubber stamp. The build report's `None; this pass introduced no new boundary.` is correct and I did not re-run anything under the failability rubric. My **re-run set is therefore empty, legally** — the diff introduces no boundary that meets the mandatory floor. What the slice *does* claim is a **relocation**, and that claim is proven mechanically below rather than accepted on prose, which is the correct rule for it (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`).
- **Hot-path budget.** Plan declares Slice 1 `none`; the build report says so. Nothing to verify.
- **Floor verification.** Plan declares Slice 1 `none` (no framework surface); the build report says so. Nothing to verify.
- **`scripts/review_inspect.py` — skipped, reason recorded.** `BUILD.md` `### When to run the helper during build` triggers Worker 3 on a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+/50+ new logic lines. This diff contains zero `.py` bytes, so no trigger fires.
- **No `pytest` run.** No `.py` changed; `AGENTS.md` forbids it after edits unless asked. No `--cov*` flag was used anywhere in this pass.

### What looks solid

- **It is a MOVE, not a copy — proven in both directions, and the proof is independent of the build report's greps.** Forward: every one of the 179 removed lines was mapped against the companion; 142 are non-blank, and all but 33 appear in it byte-identically. Every one of the 33 is accounted for — 24 `Justification:` / `Alternatives considered (and rejected):` label lines that became `###` headings, the deleted revision-history preamble, the two lines carrying the falsified clauses, the repositioned `[spec-029]` definition, and 5 lines whose only delta is the four repointed anchors (each confirmed by a character-level opcode diff, e.g. `'(#non-goals)' -> '[spec-029-non-goals]'`). Reverse: of 178 companion lines of 100+ normalized characters, **0** appear anywhere in the current spec under whitespace-flattened comparison, against a positive control that found a real spec paragraph on the same instrument. The only line present in both files is `[upstream-cookbook]: https://…`, a link definition.
- **Nothing load-bearing was lost, and the excision is exactly the declared 14 ranges.** A `SequenceMatcher` over HEAD-vs-current reports only **three** deleted-or-changed non-blank lines outside those ranges, and they are precisely the two falsified-clause lines and the repositioned link definition. Contiguity was then checked rather than assumed: every chunk of every one of the 14 ranges is present in the companion as a **contiguous byte substring** (the two that did not match on first pass, `rev-history` and D3's alternatives list, matched once the four documented anchor repointings were applied — nothing else differed).
- **Move-completeness greps re-derived independently, not taken from the report.** `Justification:` 0 in the spec / 12 `### Justification (moved from the spec)` headings in the companion; `Alternatives considered` 0 / 12; `**Revision N**` 0 / 7; `Preferred answer` 0 / 10 and `Fallback` 0 / 10, matching the ten Risks items. A separate sweep for un-labelled deliberation left behind (`Rejected:|rejected because|considered and|the alternative (was|is)|why this over`) returns **zero** hits in the spec.
- **The companion is keyed to the spec.** All twelve `## Decision N` sections open with `Spec: [Decision N — <exact spec title>][spec-029-dN].` — heading **and** anchor, and each anchor was disk-resolved against a real heading in the spec. The reverse pointers are all present too: twelve `Rationale companion —` lines in the spec, and **every one names the right count** (2/1/4/4/2/1/2/3/1/2/2/1 re-counted from the companion's own bullets; totals 25 alternatives and 33 justification bullets, both matching). The two sections that name no Decision are the ones that structurally cannot — the chronology and the fifteen findings belonging to no Decision — and each entry there still names the spec section it changed.
- **The revision history really was redistributed**, not only pasted. Twelve `### Changes this Decision underwent` sections plus four themed `## Non-Decision deliberation` groups carry the rev1-rev7 findings under the thing each one changed, including the two the report says an anchor-scan alone would have missed (rev7's "Slice 3 two-set split" under Decision 8, rev7's "Relay-suppressed pk everywhere" under Decision 4 — both checked and correctly placed).
- **Falsified prose was deleted, not moved, and the 181 bytes are exact.** Both clauses claimed the Risks section "flags" the missing-glossary-heading caveat; after the move it does not. The two deletions measure 112 and 69 bytes, and neither string survives in either file.
- **The spec still reads as a contract.** No amendment block, no "as of revision N" hedge, no retraction paragraph — with the single exception at Decision 8 (M2). Every Decision states its contract directly and ends with a pointer. The surviving `## Risks and open questions` body is a genuine live rule (mechanism claims pinned to the `0.316.0` derivation baseline against an open `pyproject.toml` floor, with re-derivation-by-execution as the trigger), which is implementation-relevant rationale and correctly kept — deleting the heading would also have dangled six in-page references from surviving text.
- **Link discipline.** Ten canonical group headers, in the fixed order, present in both files including the empty `docs/builder/`, `.venv/`, and (in the spec) `docs/builder/` groups. Every definition disk-exists; every anchored definition resolves to a real heading; no orphaned definition and no dangling use in either file. Within-group ordering had to be re-derived by hand once the scaffold-hook control came back non-distinguishing: each group is sorted, and the `[spec-029-rationale]` / `[spec-029-terms]` / `[spec-029]` ordering the move introduced is **not** drift — it is byte-for-byte the shape `docs/SPECS/spec-028-orders-0_0_8.md` uses for its own trio. I had this flagged as a finding and withdrew it after re-deriving against the sibling.
- **Gates re-run rather than trusted.** `check_spec_glossary.py --spec …` → `OK: 44 terms`, exit 0. `check_citations.py` → `OK: 789 citations resolve`, exit 0. `check_trailing_commas.py --check` on both files → exit 0 (scoped, per the control note above, to the scaffold).
- **Citations survived.** Population A: `#"` occurrences and closed `#"…"` forms both read **7** in the HEAD spec and **7** in the current spec, and a join-aware `re.S` scan agrees with the line-scoped one in both files, which is what rules out a wrapped citation. It is the same seven strings, unchanged. The companion carries **0**, so the move created no new `#"substring"` surface. Population B is covered under M3.
- **Concurrent-session attribution is right.** `docs/review/review-0_0_14.md`, the four `docs/review/rev-*.md`, and `tests/mutations/test_operations.py` are another session's; none is in this slice's diff and none was touched or reverted. `git status` was not used as a reading of this cycle's diff.

### Temp test verification

None created. `docs/builder/temp-tests/slice-1-029/` was not used: every assertion in this review was demonstrable with read-only scratch copies **outside** the repo plus the two `check_spec_glossary.py` runs against those copies, and no permanent-suite behavior is at issue. Disposition: nothing to promote.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated (M3): the outbound citation repair needs a plan-level decision, not a catalog entry.** `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:229` cites a string this move relocated into `…-029-…-rationale.md:46`; no gate can see it. The recorded reason for deferring ("the build plan's fence *and* the allowed-files list both exclude it") is half wrong — the maintainer fence admits spec files, and a `-rationale.md` companion is one; only the plan's ownership table excludes it, and `BUILD.md` gives the in-flight remedy for that. Resolution paths, for the maintainer through Worker 0:
   - **(a) Re-partition and repair in-cycle.** Worker 0 folds `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` into Slice 1's or Slice 3's writable-file list and records the correction in the plan; the repair is one sentence plus one link definition, and it is stable against Slice 3 (the cited string sits in the companion's `## Revision history`, which Slice 3 does not rewrite).
   - **(b) Keep the deferral, but on the true reason.** If the maintainer wants the sibling untouched, the catalog entry should say so — "out of the plan's ownership partition, and the maintainer declined to re-partition" — rather than citing a fence that does not exclude it.
   - My recommendation is (a): the standing lesson in this repo is that the moving slice owes the post-move sweep, and a citation nothing can detect is precisely the kind that survives an integration pass.
2. **Escalated (existence challenge): should `## Revision history` exist in the companion at all?** 18,170 bytes, 26% of the file, and all 38 of its finding bullets are also carried by the twelve `### Changes this Decision underwent` sections and `## Non-Decision deliberation`. `BUILD.md` requires the per-Decision form and does not require the chronological one. Against deletion: the block is the seven revisions *as written*, and the redistributed form is a paraphrase. Paths: **(a)** keep both and accept the duplication as a deliberate archive, saying so in the provenance so the next editor knows to update both; **(b)** keep the chronology as a bare index (revision → the Decisions it changed) and let the per-Decision sections carry the content; **(c)** drop the block. This is a contract-level call and is not a worker's; per `worker-3.md` it is raised, not acted on, and the slice is **not** held on it.
3. **The two Mediums both land in files only Worker 1 may edit**, which is why this routes back to Worker 1 rather than Worker 2, per the build plan's `## Dispatch-shape deviation`. M1 touches `### The arithmetic` here and `…-rationale.md:24`; M2 touches `spec-029-…-0_0_9.md:333` only. Neither changes any contract the spec states.
4. **Inherited from the build report and unchanged by this review:** its five `### Notes for Worker 1` items all still stand. Two are worth re-flagging because this pass touched their evidence — item 4 (Definition-of-done item 1's pointer into a Risks section that no longer describes its deferral) is real and I confirmed the pointer now leads to a section carrying only the derivation-baseline rule; item 5 (the `[rationale-dN]` anchors move in lockstep with the spec's Decision titles) is load-bearing and no gate checks it, so a Slice 3 heading rename must edit both files.
5. **The build plan's nine section-C divergences are untouched by this slice**, as the build report says — I confirmed the move touched none of the sentences they name; every one lives in contract prose that stayed.

### Review outcome

`revision-needed`.

Two Medium findings are unresolved and neither has a recorded rejection reason: **M1** (a stated count in a durable document that does not re-derive) and **M2** (a retraction paragraph left in the contract, duplicated in the companion). Both are narrow — one sentence each — and both live in files only Worker 1 may edit, so this routes to **Worker 1**, not Worker 2. **L1** should be closed in the same pass (one clause, two files).

**M3 and the two DRY findings are escalated, not held**: M3 needs a plan-level re-partition that is Worker 0's and the maintainer's to make, and the `## Revision history` existence challenge is a contract-level call that `worker-3.md` forbids holding a unit on. They are recorded above with their resolution paths and belong in the cycle's record whichever way they go.

**What is emphatically not in doubt:** the move itself. It is a move and not a copy, in both directions, on controlled instruments; the excision is exactly the fourteen declared ranges and nothing else; every moved chunk is present in the companion contiguously; every citation, link definition, and anchor in both files resolves; and all three gates pass. The rejections above are about the *record* of the move, not its content.

---

## Apply-changes pass (Worker 1)

Closes Worker 3's `revision-needed`. Every finding below was re-derived before being acted on, not applied from the review text; one was **narrower** than handed down (L1's forcing claim, confirmed), one was **wider** (M2's chronology population: three more sites), and one changed my own instrument (M3 — my first sweep failed its positive control).

**Reference used.** `git show HEAD:docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` into a scratch path outside the repo. No `git stash` / `checkout` / `restore` / `worktree` at any point.

**Instruments controlled before being believed.** Three of the checks below would read identically whether or not they measured anything:

- The link / anchor / group-header / sort validator was controlled by pointing one definition at a non-existent file in a scratch copy; it reported exactly that one problem. Its first version was **wrong twice** and both errors were caught by the control, not by the result: its GitHub slug function collapsed the double dash an em-dash heading produces (`decision-9--choice-field-interaction`), and it assumed a single alphabetical convention where the repo has two (this file's companion sorts by `ref-id]`, so `[spec-029]` follows `[spec-029-d1]`; `spec-004`'s companion sorts by bare `ref-id`, so `[spec-029]` precedes `[spec-029-rationale]`). Each file was checked against its own existing convention.
- `check_spec_glossary.py` was controlled by removing the whole `### Reference-package parity checkpoint` section from a scratch copy: `exit=1` naming exactly `RelatedFilter` / `RelatedOrder` / `RelatedAggregate`. The prose-only variant was run separately (L1).
- The moved-text sweep was controlled in both directions, and its **first version failed the positive control** (M3).

### M1 — byte arithmetic

Re-measured every disputed figure. Worker 3 is right on all three.

- **660, not 696.** The HEAD spec carries exactly 24 label lines — twelve `Justification:` at 15 bytes with newline, twelve `Alternatives considered (and rejected):` at 40 — `12*15 + 12*40 = 660`. No grouping reaches 696.
- **62, not 63.** `Revision history (kept inline so the spec is self-contained):` is 61 bytes plus its newline.
- **40,022 is not a measurement.** Replaced with a per-section ledger whose parts sum to their section, all counted as whole `HEAD` lines with newlines:

| Moved section | Bytes | Where it is now |
|---|---|---|
| Twelve `Justification:` / `Alternatives considered (and rejected):` blocks | 16,278 | 15,273 byte-for-byte + 660 label lines (now `###` headings) + 345 one line whose in-page anchor was repointed |
| `## Risks and open questions` body (`HEAD` 643-654) | 6,620 | 6,620 byte-for-byte, all of it |
| `Revision history` block (`HEAD` 11-57) | 17,883 | 2,173 (Revision 1's entry) + 1 blank + 1,478 (six Revision 2-7 headers, extended) + 14,169 (38 finding sub-bullets, not reproduced — see E1) + 62 (preamble, deleted) |

`16,278 + 6,620 + 17,883 = 40,781`, and each row's parts sum to its own total. "Verbatim" is now scoped: exactly one reproduced line differs from its `HEAD` original, and it differs only by one repointed anchor (`(#out-of-scope-explicitly-tracked-elsewhere)` -> `[spec-029-out-of-scope]`). Before E1 the modified-line count was five; the other four lived in the sub-bullets E1 removed.

Two figures Worker 3 verified and I left standing, with one clause added so they are exactly true rather than approximately: **40,962** is the span of the four routes through the pre-move spec (`17,883 + 16,278 + 6,620 + 181`), and **4,759** is the difference between that and the 36,203-byte net drop — that difference is the framing the move added back **plus one blank separator line inside the Risks range which the spec kept**, which is the one byte that otherwise makes "4,759 bytes of framing" false.

**Where the ledger lives.** One place, the companion's `## Provenance of this record`. The artifact's `### The arithmetic` now points at it instead of restating it: keeping the same numbers in a per-cycle scratchpad and a durable record is what let one wrong figure land in the durable half, which is Worker 3's second DRY finding and it is accepted.

**The ledger reflects the whole slice, not the move alone.** This pass changed both files after the move, so a ledger anchored to the move's intermediate output would name a spec no reader can produce. Every figure above re-derives from `git show HEAD:<spec>` against the two files on disk.

### M2 — the retraction paragraph, and three siblings the handed-down sweep missed

`Decision 8`'s retraction is rewritten to state the constraint directly:

> The override validation splits across the existing three-stage type-construction flow, and it cannot be collapsed into one helper called from `_validate_meta`: `_validate_meta` runs *before* `_select_fields`, before `consumer_authored_fields` is computed, and before Relay-pk suppression is known, so `selected_names` and `consumer_authored_fields` do not exist at `_validate_meta` time. The staging is forced by that ordering, not chosen for style.

The constraint survives; the "an earlier draft proposed" framing is gone. The rejected single-helper shape was already recorded twice in the companion's Decision 8, so nothing was added there.

**The "one site only" claim does not re-derive.** Sweeping the spec line-scoped, whitespace-flattened, join-aware and case-insensitively, in **both** polarities — negative (`earlier|previously|no longer|superseded|amendment|rev\d|feedback pass|draft|claimed|proposed|…`) and positive (`now|currently|today|since|still|has since|at present|…`) — plus a separate scan for review-finding tags (`\bP[123](\.\d)?\b`) returned four chronology sites in contract prose, not one:

| Pre-edit line | Text | Fix |
|---|---|---|
| 281 | "…a silent regression, not \"harmless in sync\" **as an earlier draft claimed**" | clause deleted; the retracted claim moved to the companion's Decision 3 as a first-class *claim this Decision may no longer make* |
| 333 | the `_validate_nullability_overrides` retraction paragraph | rewritten as above |
| 428 | "The slice's one new assertion **corrects the rev2 \"no `DeprecationWarning`\" error (P1.2)**" | reworded to "pins the deprecation behavior"; the rev3 P1.2 correction is already in the companion twice |
| 468 | "Schema-wide-assertion check before declaring the suite undisturbed **(P2.4)**" | tag dropped; rev3 P2.4 is already in the companion under Non-Decision deliberation |

The positive-polarity half is what found nothing extra and was worth running anyway: 29 flattened hits, every one either the `TODAY.md` filename, a present-tense statement about the *code's* state ("`config/schema.py` currently uses the bare class form"), or a forward-looking instruction ("in case a schema-snapshot test **has since** been added"). None narrates the spec's own drafting.

Re-swept after the edits: the remaining negative hits are `no longer` x2 (both about **upstream Strawberry's** source at `0.316.0`, not about this spec — implementation-relevant and staying), `previously-emitted` (Python's warning-dedupe semantics), `flipped from` (SDL nullability), and one `previously` in a Slice 1 checklist item naming the from-state of a file being migrated. A migration checklist has to name what it migrates from; that is contract, not chronology.

### M3 — the broken outbound citation, repaired in-cycle; and the sibling sweep

Worker 0's `## Mid-flight ownership re-partition` folded `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` into this slice. Repaired: its prose citation now reads

> [`spec-029`'s rationale companion][spec-029-rationale] carries the `P1.1 — stale extension-lifecycle model` finding that names spec-004's model as stale, and [`spec-029`][spec-029]'s Decision 3 is the successor: …

with one new link definition (`[spec-029-rationale]`, placed under `<!-- docs/SPECS/ -->` in that file's own bare-`ref-id` sort order). The quoted string stays on one line, so the repair does not create the wrapped-citation blind spot.

**The cited string had to be put back.** E1's collapse removed the sub-bullet `- **P1.1 — stale extension-lifecycle model.**`, which was the exact cited text. Repointing alone would have produced a citation that resolves only against a paragraph *about* the citation. Decision 3's redistributed entry is therefore relabelled `- **rev3 P1.1 — stale extension-lifecycle model** — …`, so the citation resolves against the record of the finding. Ordering matters here: had the citation been repaired before the collapse it would have re-broken silently.

**Sibling sweep — and the instrument that failed its own control.** My first sweep extracted backtick- and quote-delimited spans from every tracked file and tested each for `in HEAD-spec and not in current-spec`. It returned 252 candidates and **missed the one citation I already knew was broken**: delimiter pairing drifts across a file containing code fences, so the span was never extracted. A sweep that produces 252 hits and misses the known positive reads exactly like a passing sweep.

Replaced with a shingle index: every 30-character window of the 40,781 bytes of moved text, minus every 30-character window of the current spec, all flattened and lower-cased so a wrapped citation cannot hide. Controls: the known-broken citation **is** detected; a second moved sentence is detected; two invented sentences are not. Run over every tracked `.md` / `.py` / `.csv` / `.txt` / `.toml` / `.html`, then scoped to the **25 tracked files that reference spec-029** (flattened, case-insensitive `spec[-_ ]?029`), and re-run as a short-span pass (8-400 characters, exact containment) to catch citations below the shingle length.

Result — two files carry text that moved, and no others:

- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — repaired above.
- `docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md` — the same string, in an archived per-cycle artifact that closed with its own cycle (`START.md` "Temp artifact conventions"). Out of scope for every slice of this cycle; recorded, not edited.

Everything else the sweep surfaced is the shared spec template (`Alternatives considered (and rejected):`, `Revision history (kept inline so the spec is self-contained):`, `preferred answer per [Decision N]`) appearing in **other specs' own bodies**, or `KANBAN` card-body prose that mirrors spec text. Two near-misses were checked by reading rather than by pattern: `spec-030`'s `Predecessors:` line describes spec-029's Decision 11 as the "joint-`0.0.9`-cut version-bump boundary" — a paraphrase whose Decision is still in the spec, not a quotation of moved text — and `spec-004`'s companion separately observes that spec-029 calls `0.316.0` "the locked" version, a string that is in **neither** the HEAD spec nor the current one and so is not this move's breakage.

**Scope this sweep does not cover, stated rather than implied:** a file that quotes moved text without ever naming spec-029, in a span shorter than 30 characters. Such a reference has nothing to resolve against in the first place, and the un-scoped 30-character pass over the whole tree surfaced no such case that was not template boilerplate.

### E1 — the verbatim `## Revision history` block: collapsed

**Decided: collapse.** The block was 18,169 bytes, 26% of the companion; it is now 5,990 bytes — a chronological index that carries each round's own identity and where its findings landed, and no finding text.

**Coverage was proven before anything was dropped, not assumed.** Each of the 38 finding sub-bullets was scored against the 58 rev-keyed bullets in the per-Decision `### Changes this Decision underwent` sections and `## Non-Decision deliberation` by token overlap. Every one of the 38 matches a redistributed bullet, lowest score 0.33, highest 1.00. Control: two invented finding bullets of the same shape scored 0.08 and 0.00 — the instrument distinguishes. One finding (rev5's "`Meta`-key dict" wording) turned out to live under Decision **5**, not where a per-round reading would put it, which is exactly the kind of placement a coverage claim asserted from the review text would have got wrong.

**What is kept, and why it is not the same content twice.** Redistribution loses two things the per-Decision entries structurally cannot carry:

- **Each round's identity** — what it reviewed and what it was checked against. "Revision 3 … verified against the **uv.lock-resolved Strawberry `0.316.0`** and source", "Revision 5 … review of rev4 against the released `django_graphene_filters` parity baseline", "Revision 7 — TODO-scaffold verification pass". A per-Decision bullet says `rev3 P1.1`; it cannot say what rev3 was.
- **Which findings landed together.** Each header now ends with a count and a landing list — e.g. rev7: eight findings, under Decision 3 (1), Decision 4 (2), Decision 8 (1), Non-Decision deliberation (4). That is the index; the bodies are one click away.

Revision 1's entry is kept byte-for-byte because it is *already* an index — it names all twelve Decisions and the three card-body conflicts, and carries no finding body of its own.

Two link definitions (`[spec-029-dod]`, `[spec-029-scaffolding]`) had their only uses inside the dropped sub-bullets. Rather than delete the definitions, the two redistributed entries that carry those findings now use them, so the pointer survives where the content survives. Orphan count after: 0 definitions, 0 dangling uses.

### L1 — the parity-checkpoint judgement: scoped

Both halves re-run rather than read. Whole `### Reference-package parity checkpoint` section removed from a scratch copy -> `exit=1` on exactly `RelatedFilter` / `RelatedOrder` / `RelatedAggregate`. Prose paragraphs removed, table kept -> `OK: 44 terms`, `exit=0`. So the forcing is real for the **table** and absent for the **prose**.

The companion's paragraph now says so in two labelled halves — "**The table is mechanically forced**" with the test that shows it, and "**The surrounding prose is a judgement, not a constraint**" with the test that shows *that*, followed by the reason it stays anyway: it is Non-goals-shaped scope-setting, and its closing sentence is the table's lead-in and cannot leave without orphaning the table. The same paragraph's pointer to "the rev5 P2 entry in the revision history below" was repointed to `Documentation-coherence passes`, where that entry now lives after E1.

The artifact's `### Judgements made` records the earlier pass's reasoning and is left as that pass's record; this section is the correction.

### Spec changes made (Worker 1 only)

Every edit to `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` in this pass. Line numbers are pre-edit and are anchors, not durable references.

| Spec heading | Pre-edit line | Change | Reason | Triggered by |
|---|---|---|---|---|
| `### Decision 8 — Override validation and collision behavior` | 333 | retraction paragraph rewritten to state the ordering constraint directly | A spec is a contract and never narrates its own history (`BUILD.md` `## Spec rationale extraction`); the constraint is implementation-relevant and stays under the carve-out | Slice 1, Worker 3 M2 |
| `### Decision 3` (Mechanism section, class-form drift paragraph) | 281 | deleted "as an earlier draft claimed"; the retracted "harmless in sync" claim moved to the companion's Decision 3 | Same rule. A retraction is deliberation and moves; the corrected claim stays stated directly | Slice 1, M2 sweep |
| `## Test plan` (Slice 1 migration paragraph) | 428 | deleted the clause crediting the rev2 no-`DeprecationWarning` error (P1.2) | Same rule — a revision-round citation inside the contract. Already recorded twice in the companion | Slice 1, M2 sweep |
| `## Test plan` (schema-wide-assertion check) | 468 | deleted the "(P2.4)" review-finding tag | Same rule. Already recorded in the companion under Non-Decision deliberation | Slice 1, M2 sweep |

**Status-line re-verification (every Worker 1 spawn).** The spec's first eleven lines were read against the build's current state. the `Status:` line's `SHIPPED (0.0.9)`, card `DONE-029-0.0.9`, the unticked-checklist convention, the `Predecessors:` line, and the line-11 pointer to the rationale companion all still describe it correctly. No status line was falsified by this pass, and none was edited.

**Deferred boxes.** None. Every box in `### Spec slice checklist (verbatim)` is `- [x]`, and this pass added no obligation to it.

### Files written this pass

- `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` — four chronology edits. 133,839 -> **133,713** bytes; line count unchanged at 679.
- `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` — corrected ledger, `## Revision history` collapsed to an index, L1 scoped, M3 status updated, one retracted claim added under Decision 3, one finding relabelled, two link definitions re-homed. 68,917 -> **58,950** bytes, 459 -> 428 lines.
- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — **citation repair only**: one prose citation repointed, one link definition added. Nothing else in that file was read for correction or touched.
- `docs/builder/bld-slice-1-029-rationale_extraction.md` — this section, plus the `### The arithmetic` correction, plus `Status:`.
- `docs/builder/worker-memory/worker-1.md`.

No `.py`, no `-terms.csv`, no `KANBAN.*`, no `docs/GLOSSARY.md`, no `docs/TREE.md`, no `CHANGELOG.md`, no `docs/review/**`, no other spec or companion.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` -> **pass**, `OK: 44 terms - all have glossary entries and at least one spec link.` Controlled (see preamble); the control failed on exactly the three expected terms.
- `uv run python scripts/check_citations.py` -> **pass**, `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md).`
- `uv run python scripts/check_trailing_commas.py --check` on the spec, the companion, and `spec-004`'s companion -> **exit 0**. Scoped, per Worker 3's control, to the ten group headers and the scaffold — **not** to within-group sort order, which was re-derived by hand against each file's own convention.
- Link / anchor validator over all three files -> **0 problems**: ten group headers present in the fixed order, every definition's file resolves on disk, every anchored definition resolves to a real heading in its target, every in-page `](#…)` resolves, 0 orphaned definitions, 0 dangling uses. Positive control fired.
- Move-completeness re-derived after every edit: `Justification:` and `Alternatives considered` both read **0** in the spec; the companion carries **12** `### Justification (moved from the spec)` and **12** `### Alternatives considered (and rejected)` headings.
- No `pytest`, no `--cov*` flag, no `ruff` write-mode run. This slice touches no `.py`, and running the repo-wide formatters would churn files a concurrent session owns.
- `git status` continues to show this cycle's files alongside `docs/review/review-0_0_14.md`, four `docs/review/rev-*.md`, and `tests/mutations/test_operations.py`, all a concurrent session's. None was read as this cycle's diff, edited, or reverted.

### Notes for Worker 3 (re-review)

- The cheapest independent check of M1 is to re-run the ledger: sum whole `HEAD` lines over the fourteen ranges (11-57, the twelve Decision ranges, 643-654) and count how many of those lines appear byte-identically in the companion. The three section totals are 16,278 / 6,620 / 17,883 and each row's parts sum to its own total.
- E1's coverage proof is the one to re-run rather than read: if any of the 38 findings has no home under a Decision or under Non-Decision deliberation, the collapse lost content. Score them and control the scorer with an invented bullet.
- M3's sweep is the one that already failed once. The failure mode was a quoted-span extractor, not the search itself; re-derive with substring containment over flattened text rather than by re-extracting quotes.
- `docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md` still carries the moved string, deliberately.

### Notes for Worker 1 (spec reconciliation)

Slice 3 inherits the earlier pass's five items unchanged, with two corrections and one addition:

1. Item 2 is **closed** — the `spec-004` companion citation is repaired in-cycle, not deferred.
2. Item 4 stands and is now sharper: `Definition-of-done` item 1's pointer into `## Risks and open questions` still leads to a section carrying only the derivation-baseline rule, and its "the three net-new symbols are intentionally NOT in the CSV" claim is false at `HEAD`. Fix claim and pointer in one edit.
3. **New.** The companion's per-Decision `### Changes this Decision underwent` bullets are keyed by round tag (`rev3 P1.2`) and mostly do **not** carry the finding's original topic label; only the ones that were already labelled do, plus `rev3 P1.1 — stale extension-lifecycle model`, relabelled here because `spec-004`'s companion cites it by name. The sweep in M3 confirms nothing else in the tree cites a finding label, so this is a known asymmetry rather than an open break — but a future citation of a per-Decision entry should quote a label that exists.

---

## Review (Worker 3, pass 2)

Re-review of Worker 1's apply-changes pass. Every one of M1 / M2 / M3 / E1 / L1 was re-derived from `HEAD` and the two files on disk before being judged; none was accepted from the apply report's prose. Two of the five are corrections of my predecessor's own measurements, so each was checked for **overshoot** as well as for correctness.

**Reference used.** `git show HEAD:docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` and `git show HEAD:docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` into a scratch path **outside** the repo. No `git stash` / `checkout` / `restore` / `worktree` at any point. Independent size confirmation: spec 133,713 bytes / 679 lines; companion 58,950 / 428; both match `### Files written this pass` exactly.

**Instruments controlled before being believed.** Four checks this pass would have read identically whether or not they measured anything, and one of mine failed its control and was replaced:

- The **link / anchor / sort validator** was run against three separate mutations of a scratch copy: a broken anchor (`#decision-9--BOGUS`), a def pointed at a non-existent file, and two adjacent defs swapped out of order. All three fired; the unmutated baseline reported `[]`. My first slug function stripped `_`, which made 24 real anchors read as missing; caught by the baseline, not by the mutants.
- The **moved-text sweep** (M3) — my first instrument was a sentence-segmenter, and it **failed its positive control**: it never produced the known-broken citation as a segment, because splitting on ` — ` and sentence punctuation buries a short label inside a long span. Discarded and replaced (below). This is the second instrument in this slice to fail on exactly this hazard.
- The **E1 coverage instrument** — a 6-gram overlap scorer — also failed to distinguish: three genuine findings scored 0 and so did both invented controls, because redistribution is a rewrite, not a copy. Replaced with a `(revision, tag)` multiset plus title-level identity reading, which was controlled by deleting one bullet from a scratch copy (`rev3 P2.4`) and confirming the count dropped.
- `check_spec_glossary.py` was re-controlled on the L1 pair (below); the whole-section variant fails on exactly the three named terms.

### High:

None.

### Medium:

None. All four Mediums/Lows handed to the apply pass close.

### Low:

#### L2 — Revision 2's landing list in the collapsed index omits Decision 7

`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md:38` (the `## Revision history` index):

> **Revision 2** — feedback pass over rev1. … Nine findings, landing under Decision 3 (1), Decision 4 (4), Decision 8 (1), and Non-Decision deliberation (3).

The nine-finding count is right and every other revision's landing list re-derives digit-for-digit against the actual bullets. Revision 2's does not: the file carries **ten** `rev2 P*` bullets, and the tenth is at `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md:207`, under **Decision 7**, which the list does not name.

Measured landing distribution versus the index, for all six rounds:

| Round | Actual bullets | Index says |
|---|---|---|
| rev2 | D3 1, D4 4, **D7 1**, D8 1, ND 3 (=10) | D3 1, D4 4, D8 1, ND 3 (=9) |
| rev3 | D3 3, D4 2, ND 3 | identical |
| rev4 | D3 2, ND 1 | identical |
| rev5 | D3 2, D5 1, ND 2 | identical |
| rev6 | D3 1, D4 2, ND 2 | identical |
| rev7 | D3 1, D4 2, D8 1, ND 4 | identical |

It is not a lost or invented finding — it is a **split**. `HEAD` line 16's `P1 — inspect read source` ends "Reconciled with [Decision 7] / [Non-goals]", so the redistribution correctly gave that one finding two homes, and the Decision 7 bullet is its reconciliation half. What is wrong is only the index entry: E1's own justification for keeping the block is that it records "which findings landed together … That is the index; the bodies are one click away", and for rev2 the index sends a reader to four sections when the material sits in five.

**To close:** name Decision 7 in Revision 2's landing list — either as a fifth `(1)` entry with the count re-worded (nine findings across ten bullets, one split across Decisions 4 and 7), or with a trailing clause saying the Decision-4 finding is also recorded under Decision 7. One sentence, in the companion only. No other round needs touching; I checked all six.

### M1 — byte arithmetic. **Closed.**

Re-derived every part and every sum from `git show HEAD:` against the two files on disk. Nothing in the ledger is asserted.

| Ledger claim | Re-derived | Verdict |
|---|---|---|
| `Justification:` label lines = 660 | 12 lines at 15 bytes + 12 at 40 = 660 | exact |
| revision-history preamble = 62 | `Revision history (kept inline so the spec is self-contained):\n` = 62 bytes | exact |
| Decisions section = 16,278 | byte-sum of the twelve `HEAD` ranges | exact |
| … = 15,273 + 660 + 345 | 57 non-blank lines present byte-for-byte in the companion (15,237) + 36 blank (36) = **15,273**; 25 absent lines = 24 label lines (660) + **one** 345-byte line | exact, and the "exactly one modified line" claim holds — the absent set is 25 lines and 24 of them are labels |
| Risks body = 6,620, "byte-for-byte, all of it" | every one of `HEAD` 643-654 present in the companion, and the whole block present as a **contiguous** 6,620-byte substring | exact |
| Revision history = 17,883 = 2,173 + 1 + 1,478 + 14,169 + 62 | preamble 62, blank 1, Revision 1 entry 2,173, six `- **Revision 2..7**` headers 1,478, 38 `  - ` sub-bullets 14,169; residual lines: **0** | exact |
| 16,278 + 6,620 + 17,883 = 40,781 | ✓ | exact |
| 181 falsified-clause bytes | `HEAD` 9 → cur 9 = 112; `HEAD` 151 → cur 105 = 69 | exact |
| 40,962 / 36,203 / 4,759 / 133,839 | 40,781 + 181; 170,042 − 133,839; 40,962 − 36,203 | exact |
| "a further **126** bytes … so the spec now measures **133,713**, **36,329** below `HEAD`" | the four M2 line deltas are 36 + 56 + 27 + 7 = **126**; 133,839 − 126 = 133,713; 170,042 − 133,713 = 36,329 | exact |
| the added `4,759` clause: "plus one blank separator line inside the Risks range which the spec kept" | the line-level diff shows `HEAD` 644 (blank, 1 byte) surviving as cur 492 inside the declared 643-654 range — so 40,781 over-counts by exactly that byte, and the clause names it | exact, and it is the kind of one-byte precision that was missing before |

Every other number in the durable companion was enumerated and checked too — I swept **every** numeric literal in the file (`660 / 6,620 / 40,962 / 36,329 / 36,203 / 345 / 2,173 / 17,883 / 16,278 / 15,273 / 14,169 / 133,713 / 133,839 / 126 / 1,478 / 40,781 / 4,759 / 170,042 / 62 / 181 / 823 / 12 / 33 / 25 / 10 / 38 / 7`) rather than only the ones the apply pass discusses. All re-derive. The 33 justification bullets, 25 rejected alternatives, and the 2/1/4/4/2/1/2/3/1/2/2/1 split were re-counted from the companion's own bullets after the apply pass's edits, and all twelve spec pointer lines still name the right number. The ten `Preferred answer` / ten `Fallback` items read 10/10 in `HEAD` and 10/10 in the companion.

**Ledger location.** The durable/per-cycle duplication that produced the original defect is gone: `### The arithmetic` in this artifact now points at the companion and holds only the two figures a per-cycle artifact owns. The apply pass's own `### M1` section restates the corrected table, and `### What moved, measured` still carries the three section totals — both are per-cycle records that close with the cycle, and the second is a prior pass's report that the artifact contract forbids editing. Considered and not filed: the durable copy is now singular, which is what the DRY finding asked for.

### M2 — chronology removal. **Closed, and the correction did not overshoot.**

All four sites verified fixed at `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:281`, `:333`, `:428`, `:468`, each read against its `HEAD` original (`:344`, `:444`, `:580`, `:620`).

**The predecessor's "one site only" was wrong and the apply pass's four is right.** Confirmed by a line-level `SequenceMatcher` over `HEAD`-vs-current that classifies *every* change: the only changes outside the fourteen declared move ranges are `HEAD` 9 and 151 (the two falsified clauses), `HEAD` 344 / 444 / 580 / 620 (the four chronology sites), and one repositioned link definition at `HEAD` 778. There is no fifth chronology edit and no stray edit of any kind.

**No fifth site remains.** Swept independently, at wider vocabulary than the apply pass used:

- **Negative polarity** (adding `originally`, `at first`, `we had`, `had been`, `was dropped`, `changed from`, `corrected`, `the review found/noted`, `round \d`, `revised`, `rewritten`, `formerly`, `used to`, `amend`, `proposed` to the handed-down list) — **7 hits**, all benign and all identical to the apply pass's residual set: `no longer` ×2 about **upstream Strawberry `0.316.0`**, `previously-emitted` about Python's warning dedupe, `flipped from` about SDL nullability, and `previously` ×2 in Definition-of-done item 3 naming the from-state of the files being migrated. A migration item has to name what it migrates from.
- **Positive polarity** (`now|currently|today|since|still|as of|has since|at present|this pass|this revision|going forward|…`) — **34 hits**, every one either the `TODAY.md` filename, a present-tense statement about the *code's* state, or a forward-looking instruction. None narrates the spec's own drafting.
- **Review-finding tags** (`\bP[123](\.\d)?\b`, `\brev[2-9]\b`, `\bRevision \d\b`), swept independently of prose vocabulary and both line-scoped and flattened — **0 hits**, in both spellings.
- **Structural shapes, not vocabulary:** a scan for the retraction *grammar* (`(not|rather than|instead of|contrary to) +"…"`) returns **0** in the current spec against **2** at `HEAD` — the control fires, and the instrument is not a synonym of the word-list sweeps.

**The Decision 8 constraint survives, stated directly.** `:333` keeps all three ordering facts the retraction carried — `_validate_meta` runs before `_select_fields`, before `consumer_authored_fields` is computed, and before Relay-pk suppression is known — and closes with why the staging is forced rather than stylistic. Nothing in the rewrite has to be read as a correction of an earlier claim. `:428` likewise keeps the whole `DeprecationWarning` mechanism and drops only the "(P1.2)" provenance; `:468` drops only the "(P2.4)" tag.

**And the retracted claims landed where they belong.** `harmless in sync` appears **once in the whole tree**, at `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md:109`, as a first-class *"Claim this Decision may no longer make"*. The rejected `_validate_nullability_overrides(...)` single-helper shape is recorded at `…-rationale.md:227` as Decision 8's rev1 origin.

### M3 — citation repair and sweep. **Closed, with a third instrument that fires on the control.**

**The population re-derives to the same two files, on a differently-shaped instrument.** Mine is a **word n-gram set difference**: normalize to lowercase alphanumeric words (which erases backtick, bracket, and em-dash drift entirely, so the pairing failure that broke the first instrument cannot occur), take every 6-word window of the 40,781 bytes of moved sections plus the six edited lines, subtract every 6-word window of the current spec, then intersect that set against every tracked `.md` / `.py` / `.csv` / `.txt` / `.toml` / `.html` / `.json` / `.yaml` / `.lock`. It is not a shingle index written twice: it is word-granular rather than character-granular, set-difference rather than containment-scan, and unbounded in span rather than fixed at 30 characters.

- **Positive control:** the known-broken citation's n-gram `p1 1 stale extension lifecycle model` **is** in the moved-and-gone set (5,566 n-grams) and **is** found in `spec-004`'s companion. It fires.
- **Negative controls:** two invented sentences of the same shape are absent from the moved set and from every file.

Result over 71 files carrying at least one moved-and-gone n-gram, scoped to the 25 that reference `spec-029`: exactly **two** carry the distinctive moved string, and they are the two the apply pass names — `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` (repaired) and `docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md` (archived per-cycle artifact, correctly out of scope). Everything else is the shared spec template (`Alternatives considered (and rejected):`, `Revision history (kept inline so the spec is self-contained):`, `preferred answer … fallback`, the `spec-<NNN>-<topic>-<0_0_X>.md` convention sentence) appearing in **other specs' own bodies**, or KANBAN card prose mirroring spec text. Four near-misses were resolved by reading rather than by pattern: `spec-031:571` and `spec-032:78` say "flagged in Risks and open questions" about **their own** Risks sections; `tests/types/test_base.py:2002` is a test docstring whose phrasing coincides; `django_strawberry_framework/types/base.py:96` paraphrases the moved Decision 6 justification in a comment that cites `spec-029 Decision 6`, an unmoved heading.

**The ordering claim is true.** `HEAD` line 25's sub-bullet `- **P1.1 — stale extension-lifecycle model.**` was in the block E1 deleted; the exact cited string now exists as a record entry at `…-029-…-rationale.md:108` (`- **rev3 P1.1 — stale extension-lifecycle model** — …`), under **Decision 3**, i.e. outside the collapsed `## Revision history` (lines 36-47). Had the repointing happened before the collapse, the citation would have re-broken with nothing to see it. The repaired citation sits entirely on one line, so it does not create the wrapped-citation blind spot.

**The `spec-004` link def follows that file's own sort convention.** The repo does carry two, and this file's is bare-`ref-id` order — established four times over in its own block (`[spec-002]` before `[spec-002-rationale]`, `[spec-003]` before `[spec-003-rationale]`, `[spec-004]` before `[spec-004-checklist]`). `[spec-029]` then `[spec-029-rationale]` conforms. The `029` companion is the other convention (`ref-id]` order: `[spec-004-rationale]` before `[spec-004]`, `[glossary-…]` before `[glossary]`) and is internally consistent throughout.

**And nothing else in `spec-004`'s companion changed.** `git diff` on that file is two hunks: the prose citation and the one added definition. It is another card's durable record and it is intact.

### E1 — the revision-history collapse. **Closed. No finding was lost.**

**Every one of the 38 findings has a home, verified by identity and not only by count.** Extracted all 38 `HEAD` sub-bullets with their `(revision, tag)` key, extracted the 58 rev-keyed bullets in the companion's per-Decision and Non-Decision sections, and compared multisets:

- Per-`(rev, tag)` class the companion covers `HEAD` everywhere, with exactly **one** surplus — `(rev2, P1)` 5 vs 4 — which is the `inspect read source` split described in L2.
- Where a class holds several findings (`rev2 P1` ×4, `rev2 P2` ×4, `rev5 P2` ×3, `rev6 P1/P2` ×2, `rev7 P1` ×2, `rev7 P2` ×5) the members were matched **by title**, one at a time, so that a duplicate cannot mask a loss. All matched. `rev5`'s `"Meta"-key dict` finding does sit under Decision **5**, as the apply report says.
- The per-round totals the index states (9 / 8 / 3 / 5 / 5 / 8) sum to 38 and each matches the `HEAD` round's actual finding count.
- Control: deleting one bullet from a scratch copy drops that class's count. The instrument detects loss.

**Substance survived, not just presence.** Spot-read the three largest `HEAD` findings (1,201 / 896 / 745 bytes) against their redistributed entries. Each keeps its whole technical content — the `import_string` vs `import_module_symbol` failure mode and the dot dispatch, the per-site-vs-per-file cache-counter and `strictness=` reasoning, the instance-bound plan cache and the full list of sections that moved with the Decision — including the rev6 follow-up note about the dot-dispatch wording not having propagated.

**Revision 1's entry is byte-identical** to `HEAD` line 13, 2,173 bytes, confirmed by exact containment.

**The two re-homed link definitions are live and resolve.** `[spec-029-dod]` is used at `…-rationale.md:337` (rev2 CSV-honesty) and `[spec-029-scaffolding]` at `:324`; the companion reports 53 defs / 53 uses / 0 unused / 0 dangling, and both targets resolve to real headings.

**5,990 bytes is earned.** Measured: the section is 5,989 bytes of content plus its trailing newline. Of that, Revision 1's kept entry is 2,173 and is genuinely an index already — it names all twelve Decisions and the three card-body conflicts and carries no finding body. The six remaining headers carry what no per-Decision bullet states anywhere: what each round *was* and what it was verified against (the `uv.lock`-resolved Strawberry `0.316.0` source read, the released `django_graphene_filters` parity baseline, the TODO-scaffold verification pass). A bullet keyed `rev3 P1.2` cannot say that. The 14,169 bytes that went were the redundant half, and they went.

**This also settles the pass-1 existence challenge** the maintainer was asked to rule on: the resolution taken is path (b) — chronology kept as an index, per-Decision sections carry the content — and it is now implemented, not just chosen.

### L1 — the parity checkpoint. **Closed.**

Both halves re-run against the current spec, not read:

- Whole `### Reference-package parity checkpoint` section (lines 129-144) removed from a scratch copy → `exit=1`, failing on exactly `RelatedFilter`, `RelatedOrder`, `RelatedAggregate` and nothing else.
- Both prose paragraphs removed, table kept → `OK: 44 terms`, `exit=0`.
- Baseline on the real file → `OK: 44 terms`, `exit=0`.

The companion's paragraph at `…-rationale.md:30` now states this in two labelled halves — "**The table is mechanically forced**" with the test that shows it, and "**The surrounding prose is a judgement, not a constraint**" with the test that shows *that*, plus the (disclosed, defensible) reason the prose stays. The record no longer overstates the constraint, and the earlier over-broad wording no longer appears in either durable file. Its pointer to the rev5 parity entry now resolves to `Documentation-coherence passes`, where the entry lives after the collapse — checked; the anchor resolves.

### Independent checks, beyond the five findings

- **It is still a MOVE.** Re-proved in both directions *after* the apply pass rewrote text in both files, so no part of the prior pass's proof was carried forward. Reverse: of 156 companion lines of 100+ flattened characters, **0** appear anywhere in the current spec; positive control (a real spec line, same instrument) is found. Forward: the full line-level opcode classification above accounts for every changed `HEAD` line, and every one falls in the fourteen declared ranges, the two falsified clauses, the four chronology sites, or the link block. Move-completeness re-grepped: `Justification:` **0** in the spec / 12 `### Justification (moved from the spec)` in the companion; `Alternatives considered` **0** / 12; `**Revision ` **0**; `Preferred answer` **0**; `Fallback` **0**.
- **The spec still reads as a contract.** No amendment block, no retraction, no chronology to apply — the M2 sweeps above are the evidence, and the one remaining self-referential sentence (line 11) is the required pointer to the companion, not a history. The surviving `## Risks and open questions` body is a pointer plus one present-tense rule (mechanism claims pinned to the `0.316.0` derivation baseline against an open `pyproject.toml` floor, re-derivation-by-execution as the trigger). Six in-page references still resolve to that heading.
- **The companion is still keyed to the spec.** All twelve `## Decision N` headings are **character-for-character** identical to the spec's `### Decision N` headings (checked programmatically, not by eye — this is what keeps the slug pairs in step), and each section opens with `Spec: [Decision N — <exact title>][spec-029-dN].`, heading **and** anchor. Every one of those anchors resolves to a real heading in the spec. Reverse: twelve `Rationale companion —` pointer lines in the spec, each naming the correct alternative count. The three sections that name no Decision are the ones that structurally cannot.
- **Markdown link discipline, on all three touched files, with the hook explicitly not trusted for ordering.** Ten canonical group headers present in the fixed order in all three, including empty groups. Every definition's path disk-exists; every anchored definition resolves to a real heading in its target; every in-page `](#…)` resolves. Spec 110 defs / 110 uses, companion 53/53, `spec-004` companion 25/25 — **0** undefined uses and **0** unused defs in each. Within-group ordering was re-derived by hand against each file's own convention (see M3), because the swapped-adjacent-defs control confirms `check_trailing_commas.py --check` does not see sort order. One thing checked and **not** filed: the spec's `<!-- docs/SPECS/ -->` group flipped from bare-`ref-id` order at `HEAD` to `ref-id]` order, which makes that file internally mixed against its `<!-- docs/ -->` group — but `spec-028` (the immediately preceding extraction of the same kind) is mixed in exactly the same way and orders its `[rationale-d*]` / `[spec-028-rationale]` / `[spec-028-terms]` / `[spec-028]` block identically, as does `spec-027`. It is the established post-extraction shape, not drift.
- **Gates, re-run.** `check_spec_glossary.py --spec …` → `OK: 44 terms - all have glossary entries and at least one spec link.`, exit 0. `check_citations.py` → `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md).`, exit 0. `check_trailing_commas.py --check` (repo-wide) → exit 0.
- **`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` received a citation repair and nothing else** — confirmed by reading the full `git diff` for that path: two hunks, both named in the apply report.
- **Worker 0's mid-flight re-partition is recorded in the plan**, at `docs/builder/build-029-consumer_dx_cleanup-0_0_9.md:66`, and the ownership table row for Slice 1 carries the added file. The in-cycle repair was authorized before it was performed.
- **Concurrent-session attribution.** `docs/review/review-0_0_14.md`, the four `docs/review/rev-*.md`, and `tests/mutations/test_operations.py` are another session's; none is in this slice's diff, none was read as part of it, none was touched. `git status` was not used as a reading of this cycle's diff — the build plan's ownership table was.

### DRY findings

- **The byte-ledger duplication that caused M1 is resolved.** The durable companion is now the single authoritative home; `### The arithmetic` in this artifact points at it and keeps only the two figures a per-cycle scratchpad owns. Accepted as closed.
- **The `## Revision history` existence challenge is resolved.** 18,169 → 5,990 bytes, and what remains is the half the per-Decision sections structurally cannot carry. This was the largest DRY win available in this slice and it is a deletion, which is the right shape.
- No repeated string keys, error fragments, helpers, or parallel data flows — this slice writes no code. No new abstraction was introduced that warrants an existence challenge.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are unchanged. The slice touches no `.py`.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The slice is entirely a docs change, so the checklist applies in full.

- **Version strings / statuses / card IDs.** The spec's `Status:` still reads `SHIPPED (0.0.9)`, card `DONE-029-0.0.9`, Slice checklist correctly unticked under the shipped-spec convention. The apply pass edits none of them; re-read against the current tree and each still holds.
- **KANBAN movement.** None.
- **Markdown links introduced or moved point at existing files.** Verified mechanically for all three files, paths and anchors both, with the validator controlled three ways.
- **Archival.** Not applicable; the spec did not move.
- **Verbatim drop-ins.** Verified well past `diff` — see M1 and E1.
- **No obsolete "coming soon" / "planned" wording** introduced.
- **Script-rendered docs.** None regenerated. `docs/TREE.md` and `docs/GLOSSARY.md` untouched and outside the fence.
- `docs/README.md` and `examples/fakeshop/test_query/README.md` (the two Worker-3 required reads) were checked against this diff: neither references `spec-029`, neither is touched, and the M3 sweep surfaced no moved text in either beyond template boilerplate.

### Failability proofs, hot path, floor, static helper

- **Failability proofs — obligation considered and dismissed, with the reason recorded.** `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new **boundary, guard, gate, or rejection path**. This diff contains none: it moves and rewrites documentation prose and adds link definitions. There is no input this pass now refuses that it previously accepted, which is the test. Manufacturing a proof would be a rubber stamp. The apply pass's position is inherited from `### Failability proofs` above (`None; this pass introduced no new boundary.`) and is correct. My **re-run set is empty, legally** — no boundary in the diff meets the mandatory floor because there is no boundary in the diff. The claim this slice *does* make is a **relocation**, and that is proven mechanically above rather than accepted on prose, which is its correct rubric.
- **Hot-path budget.** Build plan declares Slice 1 `none`. Nothing to verify.
- **Floor verification.** Build plan declares Slice 1 `none` (no framework surface). Nothing to verify.
- **`scripts/review_inspect.py` — skipped; reason: zero `.py` bytes in the diff.** `BUILD.md` `### When to run the helper during build` triggers Worker 3 on a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+/50+ new logic lines. No trigger fires.
- **No `pytest`, no `--cov*` flag** anywhere in this pass. No `.py` changed.

### What looks solid

- The M1 ledger is the strongest thing in this pass. A per-section decomposition whose parts sum to their section is auditable in a way a single total never is, and every one of its eighteen figures re-derived from `HEAD` on the first attempt. The added `4,759` clause naming a **one-byte** blank line inside the Risks range is the tell that the number was measured rather than reconstructed.
- The apply pass corrected its handler in both directions honestly — wider on M2 (four sites where one was handed down), narrower on L1 (the table is forced, the prose is a judgement) — and recorded that its own first M3 instrument failed its control rather than quietly swapping it.
- E1 proved coverage **before** deleting, and the ordering discipline in M3 (relabel the record, then repoint the citation) is the non-obvious half; done the other way round the citation would have re-broken with no gate to see it.
- The retracted claims did not evaporate. `harmless in sync` and the rejected `_validate_nullability_overrides` helper each have exactly one home in the tree, in the companion, keyed to the Decision they belonged to.

### Temp test verification

None created; `docs/builder/temp-tests/slice-1-029/` was not used. Every assertion in this review was demonstrable with read-only scratch copies **outside** the repo plus three `check_spec_glossary.py` runs against those copies. No permanent-suite behavior is at issue. Disposition: nothing to promote.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated (L2): Revision 2's landing list omits Decision 7.** One sentence in the companion's `## Revision history` index. It is in a file only Worker 1 may edit, which is why it is escalated rather than held. Final verification owns the decision: close it as described under L2, or reject it with a recorded reason. Acceptance below is on that condition.
2. **Item 4 from the earlier passes stands, unchanged and still Slice 3's.** `Definition of done` item 1's `(per [Risks and open questions](#risks-and-open-questions))` pointer leads to a section that now carries only the derivation-baseline rule, and its "the three net-new symbols are intentionally NOT in the CSV" claim is false at `HEAD`. Fix claim and pointer in one edit.
3. **New, for Slice 3's divergence list.** `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:98` (`## Current state`) still calls `_validate_nullability_overrides` "Slice 3's new helper", while Decision 8 at `:333` says the validation cannot be collapsed into one helper called from `_validate_meta` — and `grep -rn "_validate_nullability_overrides" django_strawberry_framework/` returns **nothing**, so no helper of that name shipped. This is **pre-existing at `HEAD`** and untouched by this slice: the M2 rewrite neither created nor worsened it (the `HEAD` retraction named the same rejected shape). Recorded so a later pass does not read it as this slice's damage.
4. **The apply pass's own new note (`rev3 P1.1` is the only per-Decision bullet relabelled with its topic) is correct and worth keeping.** My n-gram sweep independently confirms nothing else in the tree cites a finding by label, so the asymmetry is a known state rather than an open break.
5. **The artifact's `Status:` line read `planned` on arrival**, after a completed apply-changes pass. `ARTIFACT.md` `## Status field ownership` makes `planned` the value set at artifact creation, and Worker 0 reads `Status:` to drive dispatch — a repaired-and-awaiting-re-review artifact and an unbuilt one are indistinguishable at that line. Resolved by this pass's write; noted only so the next Worker-1-performing slice sets it explicitly.

### Review outcome

`review-accepted`.

M1, M2, M3, E1 and L1 all close on re-derivation. The move is still a move, in both directions, on controlled instruments; the excision is exactly the fourteen declared ranges plus the two falsified clauses plus the four chronology edits and nothing else; every one of the 38 revision-history findings has a home and the three largest keep their whole technical content; every citation, definition, and anchor in all three touched files resolves; and all three gates pass.

One **Low** (L2) is open and is escalated to Worker 1's final verification under `### Notes for Worker 1` item 1, because it lives in a file only Worker 1 may edit. It closes with one sentence.

---

## Final verification (Worker 1)

Final verification of the whole slice, after Worker 3's pass-2 `review-accepted`. Nothing below is accepted from the chain's prose: every claim this pass depends on was re-derived from `git show HEAD:` against the files on disk, including the four figures the chain itself has already had wrong once (a reviewer's "one chronology site" that was four, and an apply pass's `40,022` that was never a measurement).

**Reference used.** `git show HEAD:docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` into a scratch path **outside** the repo. No `git stash` / `checkout` / `restore` / `worktree` at any point. Attribution is by the build plan's per-slice ownership table, never by `git status`.

**Instrument controlled before being believed.** The anchor / link-definition validator used below was controlled by mutating the one anchor this pass adds to `#decision-7--BOGUS` in a scratch copy: it reported exactly `['decision-7--BOGUS']` and nothing else. It distinguishes.

### Summary

`final-accepted`. **L2 is accepted as a real defect and closed** by one edit in the companion. The slice's contracted deliverable is present and correct: the missing `-rationale.md` companion exists, it was authored as a MOVE out of the spec, and the spec reads as a clean current contract with no chronology. All three gates re-run green. `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` carries a citation repair and nothing else.

### L2 — verdict: **accepted, and closed in the companion**

Re-derived before acting, on my own instrument rather than Worker 3's: parse the companion, track the current `##` / `###` section, and collect every bullet whose **leading** tag is `- **revN …**` — leading-tag only, because a bullet that merely *mentions* another round in its body (`rev3 P1.2` opens by quoting rev2's claim; `rev1 through rev7` names two) inflates a naive `rev\d` count. Scope: the twelve `### Changes this Decision underwent` sections plus `## Non-Decision deliberation`.

The finding holds exactly as reported. rev2 carries **ten** leading-tag bullets — Decision 3 (1), Decision 4 (4), **Decision 7 (1)**, Decision 8 (1), Non-Decision deliberation (3) — against an index entry naming four sections summing to nine. The tenth is `…-rationale.md:207`.

And it is a **split, not a loss or an invention**, confirmed against `HEAD` rather than inferred: `HEAD` line 16's `- **P1 — inspect read source.**` closes `Reconciled with [Decision 7] / [Non-goals]`, so the redistribution correctly gave that one finding two homes. `HEAD`'s rev2 block carries nine sub-bullets; the companion carries ten bullets for them. The count `nine` was right; its **subject** was where it went wrong — the digits describe findings while the list describes bullets, and for rev2 alone those are different numbers.

**Closed** by rewriting Revision 2's landing list to name Decision 7 and to state both numbers, which is the only round where they diverge. The spec is untouched.

### Every other round's landing list, re-derived on the same instrument

Worker 3 reported the other five re-derive; that is a hypothesis, so all six were measured, and each round's stated finding total was additionally checked against `HEAD`'s own sub-bullet count for that round rather than against the companion.

| Round | Leading-tag bullets measured | Index landing list | `HEAD` findings | Verdict |
|---|---|---|---|---|
| rev2 | D3 1, D4 4, **D7 1**, D8 1, ND 3 = **10** | D3 1, D4 4, D8 1, ND 3 = 9 | 9 | **defect — D7 omitted; fixed** |
| rev3 | D3 3, D4 2, ND 3 = 8 | identical | 8 | exact |
| rev4 | D3 2, ND 1 = 3 | identical | 3 | exact |
| rev5 | D3 2, D5 1, ND 2 = 5 | identical | 5 | exact |
| rev6 | D3 1, D4 2, ND 2 = 5 | identical | 5 | exact |
| rev7 | D3 1, D4 2, D8 1, ND 4 = 8 | identical | 8 | exact |

Totals: `HEAD` 9+8+3+5+5+8 = **38** findings, matching the provenance ledger's `38`; the companion carries 39 bullets for them, the surplus being rev2's one split. Because every round except rev2 has bullets == findings, no second split can exist there without an accompanying loss, and a loss would have shown as a deficit in this same table. Revision 1 carries no landing list — its entry is itself an index of all twelve Decisions, kept byte-for-byte — and the companion's twelve `- **rev1** — introduced.` bullets are consistent with that.

### The slice's contracted deliverable

- **The companion exists** at `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`, which is the one thing the build plan's Slice 1 row contracts and the one durable artifact the original `029` cycle never produced.
- **It is a MOVE.** Re-derived independently: `Justification:` reads **0** in the spec against **12** `### Justification (moved from the spec)` headings in the companion; `Alternatives considered` **0** against **12**; `**Revision ` **0** in the spec.
- **The excision is exactly the declared ranges and nothing else.** A line-level `SequenceMatcher` over `HEAD`-vs-current classifying *every* change reports exactly **7** changed non-blank `HEAD` lines outside the fourteen move ranges: `HEAD` 9 and 151 (the two falsified clauses), `HEAD` 344 / 444 / 580 / 620 (the four chronology sites), and `HEAD` 778 (the repositioned `[spec-029-terms]` definition). The insert side is the fourteen new `[rationale-*]` / `[spec-029-rationale]` definitions plus that repositioning. No stray edit of any kind.
- **The spec reads as a clean current contract.** Swept independently at wider vocabulary than either prior pass: negative prose vocabulary returns 7 hits, every one benign and identical to the recorded residual set (`no longer` ×2 about **upstream Strawberry `0.316.0`**, `previously-emitted` about Python's warning dedupe, `flipped from` ×2 about SDL nullability, `previously` ×2 in Definition-of-done item 3 naming what the migration migrates *from*). Review-finding tags (`\bP[123](\.\d)?\b`, `\brev[1-9]\b`, `\bRevision \d\b`) return **0** line-scoped and **0** flattened. The parenthesised-retraction grammar returns **0**. There is no chronology left to apply.
- **Every Decision keeps its pointer, in both directions.** Twelve `Rationale companion —` lines in the spec; twelve `Spec: [Decision N — …][spec-029-dN].` openers in the companion.
- **The surviving `## Risks and open questions` body** is a pointer plus one present-tense rule (mechanism claims pinned to the `0.316.0` derivation baseline against an open `pyproject.toml` floor). Read in full: it states a live rule, not a deliberation.

### Gates, re-run rather than trusted

| Gate | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` | `OK: 44 terms - all have glossary entries and at least one spec link.` exit 0 — re-run **after** the L2 edit |
| `uv run python scripts/check_citations.py` | `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md).` exit 0 |
| `uv run python scripts/check_trailing_commas.py --check` (repo-wide) | exit 0 |
| Anchor / link-def validator, both files | spec 110 defs / 110 uses / 0 undefined / 0 unused / 0 unresolved in-page anchors; companion 53 / 53 / 0 / 0 / 0. Positive control fired. |

Per Worker 3's control the trailing-commas hook does **not** see within-group sort order, so it is credited only for the ten group headers and the scaffold. The single definition this pass touched is not a new one — the L2 edit reuses the existing `#decision-7--…` in-page anchor, so no ordering question arises.

### Claims a later reader will treat as measured

Every figure the durable companion states was re-derived here from `HEAD`, not carried from the chain:

| Companion figure | Re-derived |
|---|---|
| `Revision history` block = 17,883 | byte-sum of `HEAD` 11-57 |
| twelve Decision blocks = 16,278 | byte-sum of the twelve ranges |
| `## Risks and open questions` body = 6,620 | byte-sum of `HEAD` 643-654 |
| sum = 40,781 | 17,883 + 16,278 + 6,620 |
| 24 label lines = 660 | `Counter` over `HEAD`: twelve `Justification:` at 15 bytes, twelve `Alternatives considered (and rejected):` at 40 |
| preamble = 62 | `Revision history (kept inline so the spec is self-contained):\n` |
| spec now 133,713, `36,329` below `HEAD` | `wc -c` = 133,713; 170,042 − 133,713 = 36,329; and 133,839 − 126 = 133,713 |

**The indirection holds.** `### The arithmetic` above no longer restates the ledger; it points at the companion's `## Provenance of this record`, and that section is now the single home for it. Verified rather than assumed: the two figures `### The arithmetic` still owns (spec 133,713 / 679, companion bytes) are the per-cycle figures a `bld-*.md` is entitled to, and they agree with disk.

**Two stale figures, both correctly fenced, recorded so no later reader mistakes them.** `### Files touched` and `### What moved, measured` in the performing pass's build report state the spec at `133,839` and the companion at `68,917` / `459` lines. Those were true of that pass's output and were superseded by the apply pass, which says so explicitly at `### The arithmetic`. `ARTIFACT.md` forbids editing a prior pass's report, so they stand as that pass's record. The current-on-disk figures are here and in the companion.

**This pass's own figures.** The L2 edit grows the companion by 316 bytes: **58,950 -> 59,266** bytes, lines unchanged at **428**. The `## Revision history` section grows 5,990 -> **6,306** bytes; E1's argument for keeping it (it carries each round's identity and where its findings landed, which no per-Decision bullet can state) is unaffected, and the section still carries no finding text of its own. The spec is **unchanged** by this pass: 133,713 bytes / 679 lines.

### `### Spec slice checklist (verbatim)` audit

All sixteen boxes are `- [x]` and every one was checked against the diff rather than against the report. The four that are not already discharged elsewhere in this section: the deliberative half of Risks left the spec and only the derivation-baseline rule stays (read in full); the parity-checkpoint judgement is recorded with its reason and, after L1, with the correct scope on which half is mechanically forced; the falsified prose was deleted rather than moved (`HEAD` 9 and 151, and neither string survives in either file); and both before-and-after byte counts are recorded with arithmetic a reader can re-run. **No box needed un-ticking and none was left `- [ ]`, so there is no deferral to record.**

### `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — citation repair only

Confirmed by reading the complete `git diff` for that path: **two hunks, 4 insertions / 2 deletions**, one repointing the prose citation and one adding `[spec-029-rationale]`. Nothing else in another card's durable record was touched. The cited string `` `P1.1 — stale extension-lifecycle model` `` resolves against `…-029-…-rationale.md:108`, sits entirely on one line (so the repair creates no wrapped-citation blind spot), and the repair was authorized before it was performed by Worker 0's `## Mid-flight ownership re-partition`, which is recorded in the build plan with the file added to Slice 1's ownership row.

### Failability, hot path, floor, tests

- **Failability proofs — not applicable, and the dismissal was recorded rather than a proof manufactured.** Confirmed present in all three prior passes: the build report (`None; this pass introduced no new boundary, guard, gate, or rejection path.`), Worker 3 pass 1, and Worker 3 pass 2, each naming `BUILD.md` `### What needs a proof, and what does not` and the reason. The diff contains zero `.py` bytes and no input is refused that was previously accepted, which is the test.
- **Hot path.** Build plan declares Slice 1 `none`. Honored — no code runs differently.
- **Floor verification.** Build plan declares Slice 1 `none` (no framework surface). Honored.
- **No `pytest`**, and no `--cov*` flag anywhere in this pass. No `.py` changed, so none is expected.
- **Staged-anchor sweep.** `grep -rn "TODO(spec-029" --include="*.py" --include="*.md" .` returns **no live anchor** — the only hits are prose *about* the scaffold inside the spec's `Implementation scaffolding & staging notes` and the companion's record of rev7, which are contract and record, not anchors.

### Files written this pass

- `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` — one sentence, Revision 2's landing list (L2).
- `docs/builder/bld-slice-1-029-rationale_extraction.md` — this section and `Status:`.
- `docs/builder/worker-memory/worker-1.md` — memory entry appended.

No `.py`, no `-terms.csv`, no `KANBAN.*`, no `docs/GLOSSARY.md`, no `docs/TREE.md`, no `CHANGELOG.md`, no `docs/review/**`, no other spec or companion — `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` needed nothing further and was not re-opened.

**Concurrent-session attribution.** `docs/review/review-0_0_14.md`, the four `docs/review/rev-*.md`, and `tests/mutations/test_operations.py` are another session's; none is in this slice's diff, none was touched, none was reverted, and `git status` was not read as this cycle's diff.

### Spec changes made (Worker 1 only)

Every edit to `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` in this slice. Line ranges are against the **pre-move** file (823 lines) and are the anchors the edits were performed on; they will not resolve against the current file.

**The final-verification pass itself made no spec edit.** Its one edit is in the companion — `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` `## Revision history`, Revision 2's landing list, which named four landing sections where the findings sit in five. Reason: the index's whole justification for surviving E1's collapse is that it records where each round's findings landed, so an index that sends a reader to four sections when the material is in five fails at the one job it was kept for. Triggered by Slice 1, Worker 3 pass-2 **L2**. The four chronology edits the apply pass made to the spec are recorded in full under `## Apply-changes pass (Worker 1)` -> `### Spec changes made (Worker 1 only)`; they are not restated here.

| Spec heading | Pre-move lines | Change | Reason |
|---|---|---|---|
| (header block, after `Predecessors:`) | 11-57 | `Revision history` block excised; replaced by a one-paragraph pointer to the companion | A spec is a contract and must never narrate its own history (`BUILD.md` `## Spec rationale extraction`). Triggered by Slice 1. |
| (header block) `Predecessors:` | 9 | deleted the clause "and are flagged in [Risks and open questions] as the missing-glossary-heading caveat" | The move falsifies it — the section no longer flags anything. Rule 2 deletes rather than moves. Triggered by Slice 1. |
| `## Current state` (glossary bullet) | 151 | deleted the clause "and flagged in [Risks and open questions]" | Same falsification, same rule. Triggered by Slice 1. |
| `### Decision 1 — Spec filename and canonical naming` | 302-311 | `Justification:` + `Alternatives considered` excised; one `Rationale companion —` pointer line added | Deliberative layer moves; every Decision keeps a one-line pointer. Triggered by Slice 1. |
| `### Decision 2 — One spec covers all three slices` | 317-325 | same | same |
| `### Decision 3 — Slice 1 adopts the singleton-factory `extensions=` form` | 346-357 | same | same |
| `### Decision 4 — `inspect_django_type` command shape and argument resolution` | 377-388 | same | same |
| `### Decision 5 — Two-key tuple-set override form` | 394-403 | same | same |
| `### Decision 6 — Net-new `ALLOWED_META_KEYS` entries, not a `DEFERRED_META_KEYS` promotion` | 409-417 | same | same |
| `### Decision 7 — Tri-state `force_nullable` threaded through `convert_scalar`` | 431-440 | same | same |
| `### Decision 8 — Override validation and collision behavior` | 458-468 | same | same |
| `### Decision 9 — Choice-field interaction` | 474-481 | same | same |
| `### Decision 10 — Scalar-only scope; relation-field overrides rejected and deferred` | 487-496 | same | same |
| `### Decision 11 — Version bumps are owned by the joint `0.0.9` cut` | 506-514 | same | same |
| `### Decision 12 — Slice independence and the Slice-3 carve-off contingency` | 522-529 | same | same |
| `## Risks and open questions` | 643-654 | body excised; heading kept; replaced by a pointer plus the one item stating a live rule (the derivation-baseline pin and its re-derivation trigger) | The preferred-answer / fallback shape is a build-time instrument, not a contract; the heading stays because six surviving references resolve to its anchor. Triggered by Slice 1. |
| `<!-- LINK DEFINITIONS -->`, `<!-- docs/SPECS/ -->` | 769-778 | added 14 definitions (`[rationale-d1]`-`[rationale-d12]`, `[rationale-risks]`, `[spec-029-rationale]`); removed none | The new pointers need targets; nothing was orphaned, verified by script. Triggered by Slice 1. |

**Status-line re-verification (every Worker 1 spawn).** The spec's first five lines were read against the build's current state. They still describe it correctly: the card is `DONE-029-0.0.9`, all three functional slices landed, the `Status:` line says `SHIPPED (0.0.9)`, the Slice checklist is correctly unticked under the shipped-spec convention, and the `Predecessors:` line names only files that exist. The **only** edit the header needed was the falsified Risks clause recorded above. No status line was falsified by this build.

**Deferred boxes.** None. Every box in `### Spec slice checklist (verbatim)` is `- [x]`.

### Notes for Worker 1 (spec reconciliation)

Everything Slice 3 inherits from Slice 1, consolidated. Items closed in-cycle are marked so and are not carried. Each open item is a **claim for Slice 3 to re-derive**, not an instruction — this slice re-derived none of the build plan's section-C divergences.

1. **The nine spec-vs-HEAD divergences in the build plan's `### C. Spec-vs-HEAD divergences` are untouched by Slice 1.** Confirmed by the line-level classification above: the move changed no sentence any of them names — every one lives in contract prose that stayed. Two now have a *new* home for their explanation, so the correction and its record land in different files: divergence 1 (scope widened past scalar-only) belongs under Decision 10's entry in the companion, divergence 2 (the apply call site is `convert_field_output`, not `convert_scalar`) under Decision 7's.
2. **`Definition of done` item 1 is false at `HEAD` and its pointer now leads somewhere else.** Its "the three net-new symbols are intentionally NOT in the CSV … honestly incomplete" claim is the build plan's divergence 5, and `check_spec_glossary` reports `OK: 44 terms` with all three present. Its `(per [Risks and open questions](#risks-and-open-questions))` pointer now resolves to a section carrying only the derivation-baseline rule. Fix the claim and the pointer in one edit rather than repointing a sentence about to be deleted.
3. **Divergence C4 — the `_validate_nullability_overrides` helper-name conflict. `PRE-EXISTING AT HEAD`; do not read it as Slice 1's damage.** `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:98` (`## Current state`) calls `_validate_nullability_overrides` "Slice 3's new helper", while Decision 8 at `:333` states the validation cannot be collapsed into one helper called from `_validate_meta`, and no helper of that name shipped — `grep -rn '_validate_nullability_overrides\b' django_strawberry_framework/` returns nothing; the shipped name is `django_strawberry_framework/types/base.py::_validate_nullability_override_targets`. Verified pre-existing by byte-comparing `:98` against `HEAD` line 144: **identical**. Slice 1's M2 rewrite of `:333` neither created nor worsened it — the `HEAD` retraction named the same rejected shape. Note when correcting it that `## Current state` is framed by the spec's own header as "the repo as of this spec's authoring, before the build", so the defect is the forward-looking claim about what Slice 3 *would* build, not the section's vintage; the build plan's divergence 4 carries the rest of that helper's drift (keyword-only signature with `relay_shaped: bool`, the `_selected_meta_targets` / `_format_unknown_fields_error` consolidation, and the shipped check order unknown -> excluded -> consumer-authored -> Relay-pk -> relation against Decision 8's listing).
4. **A Decision rename breaks the pointer chain silently, in the direction no gate checks.** The companion's twelve `## Decision N` headings are character-for-character the spec's `### Decision N` titles, deliberately, so the slugs match both ways. `[rationale-dN]` / `[rationale-risks]` / `[spec-029-rationale]` in the spec and `[spec-029-dN]` in the companion all depend on it. Rename in both files in the same edit.
5. **Closed in-cycle, carried only so it is not re-opened.** The `spec-004` companion's broken prose citation was repaired under Worker 0's mid-flight re-partition, not deferred; `### The arithmetic`'s ledger duplication is resolved onto the companion; the `## Revision history` existence challenge was resolved as path (b) and implemented; and L2 is closed above.
6. **Two records outside this cycle's reach still point at moved text, both deliberate.** `docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md:239` carries `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md #"P1.1 — stale extension-lifecycle model"` — a real `path #"substring"` citation that no longer resolves against the spec — and the same file's read-only-sibling assessment records "spec-029 (6 hits) | P1 / P1.1 / Decision 3 / Risks", two of whose four landmarks now live in the companion. It is an **archived per-cycle artifact** that closed with its own cycle (`START.md` "Temp artifact conventions") and is out of scope for every slice of this cycle; `check_citations.py` puts `docs/` out of scope so no gate sees it either. Recorded, not edited — and not a candidate for Slice 3, which owns the spec, not the archive.
7. **Only one per-Decision bullet carries its finding's topic label.** The `### Changes this Decision underwent` bullets are keyed by round tag (`rev3 P1.2`); `rev3 P1.1 — stale extension-lifecycle model` was relabelled because `spec-004`'s companion cites it by name. Two independent sweeps (a shingle index, then a word-n-gram set difference) agree nothing else in the tree cites a finding by label, so this is a known asymmetry rather than an open break — but a future citation of a per-Decision entry should quote a label that exists.

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
