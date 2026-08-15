# Build: R2 — Spec reconciliation (spec-007)

Spec reference: `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` (whole file, 62 lines before this pass)
Plan reference: `docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md` (item R2, `### Verified spec-versus-HEAD drift`, its seven corrections, `### The 1-anchor constraint`, `## The single-ownership law`)
Status: final-accepted

Per the plan's **Deviation 2**, R2 has no Worker 2 pass: Worker 1 plans **and** performs, sets
`Status: planned`, and Worker 0 reads `planned` on this artifact as "dispatch Worker 3 for the audit".
This artifact therefore carries a `## Perform record (Worker 1)` where a slice artifact would carry
`## Build report (Worker 2)`, in the same position and with the same subsections.

---

## Plan (Worker 1)

### Spec status-line re-verification (every Worker 1 spawn)

Read lines 1-5 of the spec before anything else and re-verified each against source rather than against
the plan:

- `Target release: 0.0.4 (per KANBAN.md card DONE-007-0.0.4)` — the live DB reads `card_id`
  `DONE-007-0.0.4`, `target_version.number` `0.0.4`, milestone `alpha`. Holds; no edit.
- `Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact`
  — drift row D2, verified accurate and deliberately untouched (see the D2 disposition below).
- `Owner: package maintainer` — holds; no edit.
- The rationale-pointer paragraph R1 added still describes this file correctly after the reconciliation:
  it promises the rationale carries the change record and every claim the spec may no longer make, which
  this pass extends rather than falsifies. No edit.

### DRY analysis

**Helper inventory checked.** Not applicable in the code sense and declared rather than omitted: this
pass writes only Markdown and the plan's `## Build-wide context flags` make every package source file,
test, and example read-only for the whole cycle. No helper, constant, validation branch, or fixture is
proposed, so the package-wide AST inventory would answer a question this pass does not ask. The shapes
this pass did search for are documentary duplicates, and they are the DRY substance here:

- **Existing patterns reused.** The role-claim shape already in the spec's surviving bullet
  (`docs/TREE.md` is the layout reference) is the shape every reconciled `## Scope` bullet now uses, so
  the section is internally uniform rather than a mix of role and inventory sentences. The rationale's
  entry-per-heading shape is reused for the appended reconciliation record.
- **New shared shape justified.** None. The spec gains no new convention, and every mechanism it needs
  is cited to the file that owns it.
- **Duplication risk avoided.** Three near-copies a naive reconciliation would have introduced, all
  refused: (a) restating the documentation map that `README.md` `## Project documentation` owns;
  (b) restating the generated-doc rule that `START.md` "Rendered docs — fix the source, not the file"
  owns, for `docs/GLOSSARY.md` and `docs/TREE.md`; (c) keeping a corrected copy of the spec-filename and
  archival lifecycle that `AGENTS.md` rule 26 and `BUILD.md` `## Spec and build-plan filename pattern`
  own. Each is a pointer or an omission instead.

### Boundary count

Zero. This pass introduces no guard, cap, rejection path, or validation branch — it edits two Markdown
files. The split question is answered rather than skipped: R2 is one coherent unit because every edit is
a consequence of one decision (reconcile toward roles, not inventory), and splitting it would produce a
spec that is half role claims and half rendered card rows, which is worse than either.

### Hot-path declaration

None, per the plan. No residual item changes package source, so nothing runs per request, per resolver,
per row, per connection, or per outbound message. The absence of a number is correct here, not an
omission.

### Floor-verification scope

None, per the plan. No Django / Strawberry / channels integration seam is touched.

### Failability proofs

None owed. A Markdown reconciliation introduces no boundary, and the plan's declaration says so in
advance.

### Implementation steps

1. Re-derive every drift row against source, the live kanban DB, and `git show`, rather than trusting the
   plan's table or its seven corrections.
2. Choose the reconciliation strategy and write down what it rejects **before** editing, so the rewrite
   is not steered by the sentences it meets.
3. Rewrite the spec in one pass — `## Card snapshot` reduced to card identity plus a single-ownership
   statement; `## Scope` restated as role claims; `## Other` retired with each of its eight bullets
   dispositioned; the link block rebuilt.
4. **Re-site `[optimizer behavior][glossary-djangooptimizerextension]` inside the same edit that rewrites
   its carrier sentence** (`### The 1-anchor constraint`), never afterwards.
5. Append the reconciliation record to the rationale, keyed to the spec sections by heading and anchor,
   and re-aim the one link definition the retired heading strands.
6. Re-run both checkers and the link scaffold audit on every file written; measure byte and line counts
   at the moment each is written.

### Test additions / updates

None. This pass runs no `pytest` (dispatch contract), and `--cov*` is forbidden in every pass.

### Implementation discretion items

None delegated — R2 has no Worker 2 to delegate to.

### Residual-item checklist (plan item R2, verbatim)

- [x] Every claim the repository falsifies is restated as the contract that actually holds, or handed to the document that now owns it
- [x] The explanation of each change lands in the rationale, never in the spec
- [x] All fourteen drift rows walked, each with a stated disposition
- [x] The seven corrections to the plan's own verified facts walked, each with a stated disposition
- [x] The 1-anchor constraint held: the glossary link re-sited in the same edit that rewrote its carrier
- [x] `check_spec_glossary.py` and `check_trailing_commas.py --check` re-run and quoted on every file written
- [x] Link scaffold intact: 10 canonical headers in order, every definition resolving, no unused definition
- [x] Worker 3 audit
- [x] Worker 1 final verification

---

## Perform record (Worker 1)

### Files touched

- `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` — the deliverable. `## Card snapshot`
  reduced to card identity plus a single-ownership statement; `## Scope` rewritten as role claims and
  extended by one new bullet naming `CONTRIBUTING.md` and one recovered from the retired section;
  `## Other` retired; link block rebuilt.
- `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` — the appended
  `## Reconciliation record — what the spec now says, and why`, plus two link-integrity repairs named
  under `### Changes to prior rationale text` below.
- `docs/builder/bld-007-r2-spec_reconciliation.md` — this artifact.
- `docs/builder/worker-memory/spec-007-worker-1.md` — consolidated, then appended.

### The reconciliation strategy, and what it rejected

**Chosen: the division of responsibility, not the table of contents.** Every `## Scope` bullet now states
which question a document answers; none states what a document contains. This is the strategy the plan's
`**The scope trap specific to this spec**` and R1's `## Standing note` both argue for, and R1 measured
the evidence for it: every *role* claim in the spec holds at HEAD after ten patch releases, and every
*contents* claim failed. I re-derived that split myself before adopting it (see `### Independently
re-derived claims`) rather than accepting it from either file.

**Rejected — rewrite `## Scope` as a current inventory of the five documents.** It would owe the same
reconciliation again at `0.1.0`, and it would make the spec a second copy of a map `README.md`
`## Project documentation` already owns.

**Rejected — keep the falsified halves behind a tense marker** ("as of `0.0.4`", "later superseded by").
`BUILD.md` `## Spec rationale extraction` forbids it outright: the spec never narrates its own history,
and a reader must never apply a chronology to work out what is true.

**Rejected — expand the stub.** Not seriously in play, but worth recording as decided: R1 removed the
instruction to expand, the stub shape is a seven-spec pattern, and a reconciled stub is still a stub. The
spec grew by 624 bytes and shrank by 5 lines and one section.

### Disposition of all fourteen drift rows

Every row re-verified against the primary source this pass. "No change" is a decided answer.

| Row | Disposition | Basis |
|---|---|---|
| D1 preamble | **No change — discharged in R1, verified absent.** `grep -c 'intentionally lightweight'` on the spec → `0` | reconciled once already; re-reconciling would be invention |
| D2 `Status:` line | **No change, deliberately.** Re-verified the guard names in `examples/fakeshop/apps/kanban/signals.py`; the line describes an executable constraint, not self-narration | the plan and R1 both flag it as the row most likely to be wrongly "fixed" |
| D3 labels | **Restated at the section, not the bullet.** The label list and the other volatile board fields are gone; the section names the card and says the board fields are the database's, rendered into `KANBAN.md` | DB reads three labels (`docs`, `internal`, `release`); patching the bullet re-rots on the next board edit |
| D4 `## Planning note` | **No change — discharged in R1, verified absent.** `grep -c '^## Planning note'` → `0` | R1 moved the section verbatim into the rationale |
| D5 root README | **Restated, and its successor named.** The map half becomes the whole claim; a new bullet gives the operational half to `CONTRIBUTING.md` | README's eight `##` headings at HEAD carry no operational step; `CONTRIBUTING.md` carries setup / test / lint / version / build / publish |
| D6 `docs/README.md` | **Restated as a role, and the anchor re-sited in the same edit.** "Three-minute path" deleted (names nothing); "code-first" dropped | the three surviving items verified at HEAD: `## Quick start`, `## Running the example project`, `## Nested connection indexing` |
| D7 GLOSSARY name | **Restated as a role claim about the file that exists.** The `docs/FEATURES.md` substitution history is the rationale's | the sentence could not be checked against the state it described; a role claim can |
| D8 comparison table | **Dropped to the rationale.** No comparison table at HEAD; the bullet now states the property that makes the catalog role load-bearing — one stable anchor per entry | `docs/GLOSSARY.md` line 3 states the anchor contract; the generated provenance is deliberately NOT restated (`START.md` owns it) |
| D9 CHANGELOG | **Restated as the release-record role;** both falsified claims dropped to the rationale. `CHANGELOG.md` itself untouched | `AGENTS.md` rule 21 closes the file, so the reconciliation happens in the spec — exactly as the dispatch requires |
| D10 fold-in | **Restated as the policy the repository settled on:** content folds into the durable docs **and** the spec files are retained as the design-history record | `81e4704d` resolved the bullet's internal tension by restoring the six specs `83c25963` deleted |
| D11 filename bullet | **Dropped and pointed.** The borrowed convention is retired; the reconciled fold-in bullet cites `AGENTS.md` rule 26 and `BUILD.md` `## Spec and build-plan filename pattern` | single-ownership law clause 1; the cited heading never existed. **A fourth copy remains in `CONTRIBUTING.md`**, outside the writable set — this is not the last one retired |
| D12 present tense | **Resolved by construction.** Every surviving sentence is true at HEAD as a statement about now, so no tense has to be inferred | the card body keeps its present-tense rows and is correct to; the divergence is intended |
| D13 `## Other` heading | **Section retired,** with all eight bullets dispositioned individually (below) | the heading named a card section the board deleted in `0016_remove_other_section.py`; nothing survived that `## Scope` does not now say |
| D14 `docs/TREE.md` | **No substantive change;** wording normalized to the shared role shape. The generated provenance stays out | the only claim wholly true at HEAD; restating who renders it would borrow `START.md`'s |

**The eight `## Other` bullets, individually** (the count is the DB's: `why_it_matters` 1 +
`files_touched` 5 + `note` 2, re-derived from `Card.objects.get(number=7).items` this pass):

1. `internal docs cleanup / spec consolidation — no upstream-parity surface` (`Why it matters`) —
   **retained**, restated as `## Scope`'s closing non-goal bullet.
2-6. The five `Files likely touched` paths — **dropped as duplicates**; `## Scope` names all five
   documents in the sentences that say what each is for.
7. `onboarding-doc consolidation across README / docs / CHANGELOG…` (`Note`) — **dropped as a
   duplicate** of `## Scope` in summary form.
8. The spec-filename convention (`Note`) — **dropped and pointed**; see D11.

### Disposition of the plan's seven corrections

| Correction | Disposition |
|---|---|
| 1. `231911a8` is the version cut (2 files), not the card's work (`4b8dce07` / `83c25963` / `3a4d40b7`) | **Honoured by omission.** No commit-to-file-set claim entered the spec, and the rationale's existing entries already carry the corrected attribution. This pass added no new claim about `231911a8` |
| 2. D4's mechanism: `Card.planning_note` was retained, its value cleared | **No action owed** — D4 is discharged and the rationale already states the corrected mechanism. Re-verified `card.planning_note == ''` this pass |
| 3. D13's mechanism: the `## Other` render was faithful when written; the taxonomy arrived 2026-07-20 | **Adopted, and it is what makes the retirement right.** The section is retired because the board deleted the heading it names, not because the render was defective. Verified `0016_remove_other_section.py` exists |
| 4. "three-minute" has three surfaces (spec, `KANBAN.md`, `KANBAN.html`) | **Adopted.** Removing the spec's copy leaves the two generated ones, which are a correct historical record of a Done card and are not drift to fix. No count entered either durable file |
| 5. The stub population is seven specs, not three | **Adopted as framing, not restated.** The rationale already carries the seven with byte counts; the spec says nothing about its siblings |
| 6. `docs/GLOSSARY.md` has one table (`## Index`), not two | **Adopted.** No table claim of any kind survives in the spec, so the corrected count is not restated anywhere in a durable file |
| 7. Spec-007 is fifth smallest, not smallest | **Adopted as framing.** No superlative and no sibling comparison entered either durable file this pass |

### Spec changes made (Worker 1 only)

Each entry cites the spec section by heading, the drift row that triggered it, and a one-line reason. The
matching rationale entry is named by its own heading; all of them sit under
`## Reconciliation record — what the spec now says, and why`.

1. **`## Card snapshot`** (D3) — replaced the six rendered board-field bullets with two: the card's
   identity, and a statement that labels, priority, relative size, and the item rows belong to the Kanban
   database. Reason: the label list was stale and a hand-copy nothing re-renders drifts on every board
   edit. Rationale: `### `## Card snapshot` — the board fields are the database's`.
2. **`## Scope`, new lead sentence** (D12, and the strategy) — states that the card divided the
   documentation by the question each file answers. Reason: it is the card's durable output and it makes
   every following bullet's shape explicit. Rationale: `### The strategy, and what it rejected`.
3. **`## Scope` bullet 1** (D5) — root `README.md` restated as the documentation map only. Reason: the
   operational half moved out and a claim cannot be half true. Rationale:
   `### `## Scope` — six rendered rows became eight contract claims`.
4. **`## Scope`, new bullet** (D5) — `CONTRIBUTING.md` named as the entry point for working on the
   package. Reason: naming the successor is what makes the corrected division checkable. Same rationale
   entry.
5. **`## Scope` bullet 2** (D6) — `docs/README.md` restated as the entry point for using the package;
   "three-minute path" and "code-first" removed; **the glossary link re-sited into the surviving
   runtime-behavior clause in the same edit**. Reason: the phrase named nothing, and the adjective is an
   inventory claim about a document ten cards have since written into. Same rationale entry.
6. **`## Scope` bullet 3** (D7, D8) — `docs/GLOSSARY.md` restated as the capability catalog with one
   stable anchor per entry; the comparison table dropped. Reason: the table does not exist and the anchor
   contract is the role's load-bearing half. Same rationale entry.
7. **`## Scope` bullet 4** (D14) — `docs/TREE.md` wording normalized only. Reason: uniformity with the
   other role claims; the claim itself holds. Same rationale entry.
8. **`## Scope` bullet 5** (D9) — `CHANGELOG.md` restated as the release record; "condensed" and "no
   longer relies on design-doc pointers" removed. Reason: both are false and `AGENTS.md` rule 21 forbids
   fixing them in the changelog. Same rationale entry.
9. **`## Scope` bullet 6** (D10, D11) — the fold-in bullet restated as the settled policy and pointed at
   its owners. Reason: the bullet's two halves were in tension and the repository resolved it; the
   lifecycle belongs to `AGENTS.md` rule 26 and `BUILD.md`. Same rationale entry.
10. **`## Scope`, new closing bullet** (D13 bullet 1) — the card shipped documentation only, no package
    surface and no upstream-parity change. Reason: recovered from the retired section, where it was the
    one non-duplicate claim. Same rationale entry.
11. **`## Other` retired** (D13, D11) — section and heading removed. Reason: it names a card section the
    board deleted, and its bullets are duplicates, a recovered non-goal, and a borrowed convention.
    Rationale: `### `## Other` — retired, not renamed`.
12. **Link-definition block rebuilt** — added `[changelog]`, `[contributing]`, `[root-readme]`,
    `[glossary]`, `[readme]`, `[tree]`, `[build]`; removed the unused `[backlog]`. Reason: the new
    bullets link to the documents they describe, and an unused definition is drift. Rationale:
    `### The link scaffold, and this file's own pointers`.

### Changes to prior rationale text (two, both link integrity)

`worker-1.md` `### Performing the rationale move` rule 4 makes the rationale append-only during the
build, and rule 3 requires that no surviving cross-reference point into text that no longer exists. Those
collide exactly twice here, and both repairs are the smallest that keep a pointer resolving:

- The `### `## Other` …` entry's `Spec: [Other][spec-007-other].` pointer line now reads as a "bears on"
  pointer to `[Scope][spec-007-scope]`, matching the pattern the `## Planning note` entry already uses
  for a section that no longer exists.
- The `[spec-007-other]` link definition was removed, since `#other` is no longer an anchor in the spec.

No entry's substance, argument, or measurement was edited, and the appended record names both repairs on
disk so a reader of the finished file does not have to diff it to find them.

### Independently re-derived claims

Everything below was measured this pass from the primary source, not read out of the plan, R1's artifact,
or the rationale. HEAD is `947f74948c16b20b0c15ff359bb53fbe462d4b8c`, re-derived at the open and the
close of the pass.

- **Card 7, live DB**: `card_id` `DONE-007-0.0.4`, `status.key` `done`, `target_version` `0.0.4`
  (milestone `alpha`), `priority` `Medium`, `relative_size` `S`, labels `['docs', 'internal', 'release']`
  (three), `planning_note` `''`, `SpecDoc.path`
  `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md`, one glossary link with `raw_text`
  `optimizer behavior` on term `` `DjangoOptimizerExtension` ``, and fourteen items across
  `Scope` ×6 / `Files likely touched` ×5 / `Why it matters` ×1 / `Note` ×2, every one `is_complete`.
- **Root `README.md` at HEAD**: eight `##` headings — "Why this package exists", "Why it's fast",
  "Is this for you?", "Status", "Get started → `docs/README.md`", "Project documentation", "Inspired by",
  "Contributing & Security". No operational step among them. `## Project documentation` is eight bullets,
  not a table.
- **`CONTRIBUTING.md` at HEAD** carries "Getting started", "Running the test suite", "Linting and
  formatting", "Updating the package version", "Building", "Publishing", "Updating dependencies" — the
  operational set the root README lost.
- **`docs/README.md` at HEAD** carries `## Installation`, `## Quick start`, `## Running the example
  project`, `## Using the package in your own project`, and `## Nested connection indexing` (the
  optimizer behavior). No section named or resembling a "three-minute path".
- **`docs/GLOSSARY.md`** self-describes as a glossary of every public symbol, `Meta` key, configuration
  argument, and named behavior, with a stable anchor per entry.
- **`docs/TREE.md`** self-describes as the detailed layout reference.
- **`0016_remove_other_section.py`** exists under `examples/fakeshop/apps/kanban/migrations/`, which is
  what makes the `## Other` heading a dangling card-section name.
- **`2baf93b5`** is dated 2026-06-09 and `81e4704d` 2026-06-01 — the eight-day gap the rationale's label
  entry states.
- **`docs/builder/BUILD.md`'s heading is `## Spec and build-plan filename pattern`** (line 7), so the
  retired bullet's citation of "Spec filename pattern" was dangling, and `CONTRIBUTING.md` still carries
  the same dangling citation.

**One defect this pass caught in its own text before it landed anywhere durable**, recorded because the
cycle's standing hazard is exactly this shape: a first draft of the `## Card snapshot` rationale entry
said "three entries above key to its anchor". The real count is **four** — the preamble, status-line,
planning-note, and label entries all resolve `[spec-007-card-snapshot]`. Re-derived by grep, corrected
before any check was run, and named here rather than left silent.

### Validation run

Both checkers, on every file this pass wrote, quoted verbatim as run:

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
exit=0
```

`check_spec_glossary.py` takes no rationale-file argument, so the rationale is covered by the scaffold
checker only; that is the tool's shape, not a gap this pass introduced.

**The 1-anchor constraint held.** The link was re-sited inside the same edit that rewrote its carrier
sentence — `## Scope` bullet 2 was rewritten and re-emitted with
`[optimizer behavior][glossary-djangooptimizerextension]` inside its runtime-behavior clause. The link
text is unchanged, so the `-terms.csv` row's `raw_text` still matches; the CSV was not touched, and no
hollow bullet was left behind to host the link. The baseline `OK: 1 terms` is unchanged.

No `pytest` was run (dispatch contract), no `--cov*` flag was passed anywhere, no `git stash` /
`checkout` / `restore` / `worktree` was used, nothing was committed, and no branch was created.

### Byte and line counts, measured as each number was written

All measured with `wc -lc` at HEAD `947f7494`.

| File | Before | After |
|---|---|---|
| `docs/SPECS/spec-007-…-0_0_4.md` | 62 lines / 2,365 bytes | 57 lines / 2,989 bytes |
| `docs/SPECS/appx/spec-007-…-rationale.md` | 453 lines / 29,396 bytes | 586 lines / 39,038 bytes |

`git diff --stat` on the spec against HEAD reads `20 insertions(+), 28 deletions(-)` cumulative for R1
and R2 together; R1's own contribution to that total was `2 insertions(+), 5 deletions(-)`.

The spec is longer in bytes and shorter in lines and sections. That is the honest shape of the trade: a
role claim is a sentence where a rendered card row was a fragment, and two sections became one.

### Link scaffold audit

Both files, re-checked after the final edit, with code spans stripped before the sweep:

- All **10** canonical group headers present and in the required order, in both files.
- **Spec**: 10 definitions, 10 uses, **zero unused** and **zero undefined**; every target resolves on
  disk. `[backlog]` — unused since the file was created — is retired.
- **Rationale**: 14 definitions after removing `[spec-007-other]`, zero unused, zero undefined, every
  target resolving.
- **Both spec anchors the rationale points at exist**: `#card-snapshot` and `#scope` match the spec's
  only two `##` headings.
- **Depth trap re-checked in both directions.** From `docs/SPECS/`, `../../README.md` resolves to the
  repository-root `README.md` and `../README.md` to `docs/README.md` — two different files with the same
  name, now linked from the same section, verified by absolute-path expansion rather than by eye. From
  `docs/SPECS/appx/`, `../../../README.md` is the root README and `../../README.md` is `docs/README.md`;
  the rationale's `[root-readme]` and `[readme]` definitions match. The re-check is recorded in the
  rationale's `### The link scaffold, and this file's own pointers` as the dispatch required.
- `AGENTS.md` rule 27: **zero** raw `path:NN` references in either durable file, verified by regex. Raw
  line refs appear only in this artifact, which rule 27 exempts.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **`## Card snapshot` kept its heading on purpose.** Four rationale entries resolve to `#card-snapshot`;
  retiring the heading would have stranded all four to save two lines. The section was hollowed instead,
  which fixes D3 permanently rather than patching a bullet that re-rots.
- **`## Other` was retired rather than renamed.** A renamed section would have been an empty container
  kept for its heading's sake, since every surviving claim moved into `## Scope`.
- **The `CONTRIBUTING.md` bullet is an addition, not a restatement.** Dropping "operational entry point"
  without naming where the content went would leave a reader unable to check the division — which is the
  exact failure this spec is a case study in.
- **Provenance claims were deliberately excluded** for `docs/GLOSSARY.md` and `docs/TREE.md`. Both are
  generated, both facts are true, and both belong to `START.md`. A borrowed copy is what went stale in
  the bullet this pass retired.

### Notes for Worker 3

- The spec's before-state is `git show HEAD:docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md`
  **plus R1's already-applied diff** — HEAD is the pre-R1 state, so a diff against HEAD shows both passes.
  R1's share is `2 insertions(+), 5 deletions(-)`; everything else is this pass.
- The rationale file is untracked (`??`), so `git diff` shows nothing for it; the appended section is
  `## Reconciliation record — what the spec now says, and why` and the two prior-text repairs are named
  under `### Changes to prior rationale text` above.
- Every figure in this artifact and in the appended rationale section was measured this pass. If any
  disagrees with the plan or with R1's artifact, re-derive rather than reconciling the two documents.

### Notes for Worker 1 (spec reconciliation)

Extends the five instances in `docs/builder/bld-007-r1-rationale_move.md`; nothing in any of them is
retracted. Everything they routed to R3 still stands — `CONTRIBUTING.md`'s dangling citation, the
eight-bullets-not-a-table shape of the root README's map, the staged-anchor sweep and
`import_spec_terms --check` as R3's, and the unresolved `docs/review/rev-*.md` escalation.

New from this pass:

1. **Every R2-routed item is now closed.** D1 verified absent, D2 left alone, D3's section question
   decided at the section, `## Scope` 6's fold-in tension carried into the restated bullet with the
   reversal recorded in the rationale, the role-versus-inventory split adopted as the strategy, and the
   1-anchor constraint exercised and held. R3 inherits no open R2 question.
2. **`## Other` = eight is now a historical number.** Any R3 sweep that counts the spec's bullets will
   find eight bullets under `## Scope` plus its lead sentence, and two under `## Card snapshot`
   (counted mechanically this pass, not by eye). The card still has
   fourteen items and R3's DB checks are unaffected — **no card-body edit was made or is owed.**
3. **The `-terms.csv` was not touched and the DB was not written.** The single anchor's chain is intact
   with the same link text, so `import_spec_terms --check` should be unaffected by this pass; R3 re-runs
   it rather than trusting that.
4. **D11's fix does not retire the last stale copy.** `CONTRIBUTING.md` still cites a `BUILD.md` heading
   that does not exist. It is outside the writable set, so it belongs in R3's deferred-work catalog as a
   maintainer follow-up, and this pass's edit must not be described as having fixed it.
5. **The count-beside-the-lesson hazard bit once more and was caught pre-landing** (`### Independently
   re-derived claims`, the four-not-three entry count). R3 should treat every count in this artifact and
   in the appended rationale section as re-derivable and re-derive it; each was measured this pass, but
   the cycle's record is that a fifth instance is likelier than a first clean one.

### Working-tree churn and baseline growth

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` at the open of this pass carried
**25 entries**, matching the plan's fifth growth event exactly; at the close it carries the same 25 plus
this artifact:

```text
 M KANBAN.html
 M KANBAN.md
 M django_strawberry_framework/_boundary_ordering.py
 M django_strawberry_framework/middleware/request_body.py
 M docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
 M docs/SPECS/spec-002-optimizer-0_0_2.md
 M docs/SPECS/spec-006-public_surface-0_0_3.md
 M docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
 D docs/review/rev-_cross_web_patches.md
 D docs/review/rev-_django_patches.md
 D docs/review/rev-_strawberry_patches.md
 D docs/review/rev-apps.md
 D docs/review/rev-conf.md
 M examples/fakeshop/db.sqlite3
 M examples/fakeshop/test_query/test_transport_api.py
 M tests/test_views.py
?? docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md
?? docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
?? docs/builder/bld-006-r1-rationale_move.md
?? docs/builder/bld-006-r2-spec_reconciliation.md
?? docs/builder/bld-007-r1-rationale_move.md
?? docs/builder/build-006-public_surface-0_0_3.md
?? docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md
?? docs/review/rev-_boundary_ordering.md
?? docs/review/review-0_0_14.md
```

**Attributable to this pass:** `docs/SPECS/spec-007-…md` (already `M` from R1),
`docs/SPECS/appx/spec-007-…-rationale.md` (already `??` from R1), this artifact, and the namespaced
memory file. Nothing else. **The baseline-dirty list grew by nothing this pass**, so Worker 0 has no new
entry to append.

**The five `docs/review/rev-*.md` deletions remain ESCALATED and UNRESOLVED** — still tracked at HEAD and
absent from disk, still not restored, not reverted, not touched. `git checkout HEAD -- docs/review/`
remains banned in this tree. `docs/review/review-0_0_14.md` and `docs/review/rev-_boundary_ordering.md`
were not touched. The concurrent spec-002 and spec-006 cycles' six paths and the third session's four
package-source / test files were **not read for content, not touched, not reverted, not staged**.

**HEAD is unchanged at `947f74948c16b20b0c15ff359bb53fbe462d4b8c`**, re-derived at the open and the close
of this pass rather than trusted from the plan. No commit landed during it, so nothing this pass wrote
was swept into a concurrent commit.

### Status

`planned`. Per the plan's Deviation 2, Worker 0 reads this as "dispatch Worker 3 for the audit".

---

## Review (Worker 3)

Fresh invocation, no memory of the pass that wrote this. HEAD re-derived at the open and the close of
this pass: `947f74948c16b20b0c15ff359bb53fbe462d4b8c`, unchanged. The pre-R1 spec was extracted with
`git show HEAD:<path>` into a scratch path outside the repository and diffed there; no `git stash` /
`checkout` / `restore` / `worktree` was used, nothing was committed, no branch was created, no `pytest`
ran, and no `--cov*` flag was passed. No temp tests were needed, so `docs/builder/temp-tests/r2/` was
not created.

**Declarations checked against the plan and found correct as absences:** no failability proof is owed
(the pass introduces no boundary), no hot-path number is owed, no floor run is owed. The `### Failability
proofs` / `### Hot-path budget` / `### Floor verification` headings are present and correctly say so.

### High: None.

### Medium:

**M1 — The `## Scope` lead sentence credits the card with the `CONTRIBUTING.md` division, which the card
did not perform.**
`docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md`, `## Scope` lead sentence + bullet 3.

The dispatch asked for an explicit ruling on this bullet, and it splits in two.

*The bullet itself is legitimate and I rule it so.* `CONTRIBUTING.md` **did** exist at the card's ship
window — `git log --diff-filter=A -- CONTRIBUTING.md` returns `2428cd8f` (2026-04-29, the `v0.0.1`
skeleton), three months before `0.0.4` — so naming it is not anachronistic, and every one of the six
responsibilities the bullet lists resolves at HEAD (`## Getting started`, `## Running the test suite`,
`## Linting and formatting`, `## Updating the package version`, `## Building`, `## Publishing`). As a
statement of the settled division it is true and checkable, which is what the reconciliation strategy
asks for.

*The lead sentence is what makes it a defect.* "The card divided the onboarding documentation by the
question each file answers" turns every following bullet into an assertion about the card's own act, and
for `CONTRIBUTING.md` that assertion is false in two independent ways, both re-derived this pass:

- **The card never touched the file.** `git show --stat` on the card's three documentation commits
  (`4b8dce07`, `83c25963`, `3a4d40b7`, all 2026-05-05) lists `README.md`, `docs/README.md`,
  `docs/FEATURES.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md`, `AGENTS.md`, `START.md`,
  `docs/alpha-review-feedback.md`, `docs/feedback.md`, the deleted `docs/spec-*.md`, and package source.
  `CONTRIBUTING.md` appears in none of them, nor in the release commit `231911a8`.
- **Half the enumerated content did not reach the file until after the release.** At `231911a8`
  (2026-05-08) `CONTRIBUTING.md` carried only `## Getting started`, `## Running the test suite`, and
  `## Linting and formatting`. `## Updating the package version`, `## Building`, `## Publishing`, and
  `## Updating dependencies` arrived at `b57eba38` (2026-05-16), and the root README's operational
  sections were stripped at `2bd7cb84` (2026-05-16) — both **eight days after** the card shipped.

So the spec now credits card 7 with a division two later commits performed. The rationale is careful
here and the spec is not: `### `## Scope` 1` dates the removal to `2bd7cb84` (2026-05-16) correctly, and
the reconciliation record's bullet 1 says only "the division that replaced it", which is accurate — the
false attribution exists **only** in the spec, introduced by coupling a new bullet to a
card-attributing lead sentence.

This is the cycle's own defect class: a durable claim that reads true, verifies true in isolation, and
is false about who did it. The reconciliation moved the defect rather than removing it for this one
bullet.

*Recommended change (Worker 1's call between them):*

1. **Decouple.** Keep the lead sentence's first clause as the card's output and introduce the bullets as
   the division as it now stands — e.g. end the lead sentence at "so that no two files answer the same
   one." and let the bullets be present-tense role claims about the current set, which is what they
   already are. One clause, no bullet changes, and it preserves the strategy exactly.
2. **Attribute explicitly**, marking the `CONTRIBUTING.md` bullet as the destination the operational half
   reached rather than as something the card placed there, with `b57eba38` / `2bd7cb84` recorded in the
   rationale entry that already discusses the split.

Option 1 is the smaller edit and does not put a date into the contract. Either way the rationale's
`### `## Scope` — six rendered rows became eight contract claims` bullet 1 should name the two commits,
since it currently asserts a division without saying when it landed and the spec is where a reader
would otherwise go looking.

**M2 — Two different sizes for one file are attributed to one commit hash inside one durable file.**
`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`,
`## Reconciliation record — what the spec now says, and why`, the paragraph beginning "The spec went
from".

The line reads: "The spec went from 2,365 bytes / 62 lines to 2,989 / 57, **measured at `947f7494`**
before and after the edits."

Re-derived this pass: `git show 947f7494:docs/SPECS/spec-007-…-0_0_4.md | wc -lc` is **65 lines /
2,282 bytes**, not 62 / 2,365. The 2,365 / 62 figure is the *uncommitted working-tree state after R1's
move*, which is correct as a before-figure but is not what `947f7494` yields. The same durable file
already states the committed figure correctly 400 lines earlier — `## How to read this file`: "Spec-007
measured 2,282 bytes, 65 lines and zero fenced code blocks at `947f7494`". A reader who follows the hash
gets a contradiction inside one document, from the two sentences that both claim to be anchored.

The after-figures are correct: `wc -lc` on the working tree gives **57 / 2,989**, reproduced this pass.

This is also the specific instruction R1's sixth `### Notes for Worker 1` item 3 left for R2 — "anchor it
to a hash and extend the enumeration" — discharged in form but not in substance, because the hash named
does not produce the number.

*Recommended change:* state the before-figure as the working-tree state it is, e.g. "from 2,365 bytes /
62 lines — the working-tree state after the extraction pass, on top of `947f7494` — to 2,989 / 57
measured at the same commit after these edits", and extend `## How to read this file`'s measurement
enumeration with this line so the two anchored figures are legible as different scopes rather than as a
contradiction.

### Low:

**L1 — "every other document" is an unqualified universal that is false outside the onboarding set.**
Spec, `## Scope` bullet 1: "Root `README.md` is the canonical documentation map: positioning, status, and
the pointer set into **every other document**."

Verified at HEAD: `README.md` `## Project documentation` carries eight bullets (`docs/README.md`,
`docs/GLOSSARY.md`, `GOAL.md`, `TODAY.md`, `docs/TREE.md`, `KANBAN.md`, `BACKLOG.md`, `CONTRIBUTING.md`)
and `## Contributing & Security` adds `SECURITY.md` and `CHANGELOG.md`. Within the set this spec is about
the claim holds — all five other named files are pointed at. Outside it, `README.md` points at none of
`AGENTS.md`, `START.md`, or `docs/builder/BUILD.md`, all of which are documents in this repository.

Non-blocking on its own, but it is the shape this cycle's record says to distrust: a universal is where
the falsification lives, and this one was written in the same pass that retired five falsified claims.
*Recommended change:* scope it — "the pointer set into the rest of this set" or "into every other
document it names".

**L2 — The spec borrows `docs/GLOSSARY.md`'s own contract and drops one of its four categories.**
Spec, `## Scope` bullet 4: "one stably anchored entry per public symbol, `Meta` key, and named behavior".

`docs/GLOSSARY.md` line 3 self-describes as "every public symbol, `Meta` key, **configuration argument**,
and named behavior … Every entry below has a stable anchor". This pass's own `### Independently
re-derived claims` records all four categories correctly, so the measurement was right and the durable
text is narrower than the owner's.

Two things follow. The enumeration is an inventory fragment inside a role claim, which is the shape the
pass set out to remove; and under `## The single-ownership law` clause 1 the anchor contract's owner is
`docs/GLOSSARY.md` itself, making spec-007 the borrower — the same relation D11 resolved by pointing.
*Recommended change:* drop the enumeration ("one stably anchored entry per catalogued capability") or
match the owner's four. I do not recommend converting the whole bullet to a pointer: the role claim is
the spec's to make, and only the enumeration is borrowed.

**L3 — Two miscounts in this artifact, both scratchpad-only, superseded here rather than routed.**
Recorded because the dispatch asked for a seventh instance of this cycle's standing hazard and there are
two, both in the pass's own reporting of its inputs and outputs:

- `### Notes for Worker 1 (spec reconciliation)`, opening line: "the **five** instances in
  `docs/builder/bld-007-r1-rationale_move.md`". There are **six** — `grep -n` returns lines 273, 870,
  1223, 1572, 1886, 2301 — and R1's own `### What R2 is left, confirmed on disk` says "exists in **six**
  instances (the R1 perform record and all three apply-changes / review pairs)". I read all six; nothing
  in the sixth is unaddressed by this pass, so the miscount misstates the reading list without dropping
  an obligation.
- `### Link scaffold audit`: "**Rationale**: **14** definitions after removing `[spec-007-other]`". There
  are **15** — Root 4, `docs/` 3, `docs/SPECS/` 6, `docs/builder/` 2 — and R1's close recorded 16 before
  the removal, so 15 is also the arithmetic. The audit's substantive claims are correct and re-derived
  below; only the total is wrong.

Both live in a `bld-*.md` scratchpad that closes with this cycle, neither propagated into a durable file,
and both are **superseded by this section** under the same `ARTIFACT.md` no-edit-prior mechanism this
cycle has used three times. They do not require a spawn and are not the reason this pass returns
`revision-needed`.

### DRY findings

Beyond L2, none. The spec and rationale do not tell the same fact twice: the spec states contracts, the
rationale states what changed and why, and every worked example I checked (the fold-in policy, the
label list, the comparison table, the changelog claim) appears as a contract in one and as a change
record in the other, never as the same sentence. The three near-copies the pass records refusing —
the `README.md` map, the `START.md` generated-doc rule, the `AGENTS.md` rule 26 lifecycle — are all
genuinely absent from the spec, verified by grep. No existence challenge is raised: this pass creates no
abstraction, helper, registry, or indirection layer.

### Verification performed

**1. Is every sentence in the reconciled spec true at HEAD?** Each of the six role claims checked against
the actual file, not against the pass's reasoning:

| Spec claim | Verified against | Result |
|---|---|---|
| Root `README.md` — map, positioning, status, pointers | `grep '^#' README.md`: eight `##` headings, no operational step | **True**, except the universal in L1 |
| `docs/README.md` — installation, quick start, running the example project, runtime behavior | `## Installation`, `## Quick start`, `## Running the example project`, `## Nested connection indexing` all present | **True** |
| `CONTRIBUTING.md` — dev setup, tests, formatting, versioning, build, publish | all six headings present at HEAD | **True at HEAD**; attribution defect is M1 |
| `docs/GLOSSARY.md` — one stably anchored entry per symbol / `Meta` key / named behavior | file's own line 3, plus the anchor `## \`DjangoOptimizerExtension\`` resolving at line 712 | **True**, one category short — L2 |
| `docs/TREE.md` — detailed layout and test-tree reference | file's own line 3; `## Test layout` / `### Current test trees` / `### Target test shape` present | **True** |
| `CHANGELOG.md` — the release record | "All notable changes to this project will be documented in this file"; `## Versioning` | **True** |
| `## Card snapshot` — board fields belong to the DB and are rendered into `KANBAN.md` | `KANBAN.md` card 7 block renders Priority `Medium`, Relative size `S`, Labels `docs`/`internal`/`release`, plus `#### Scope` / `#### Files likely touched` | **True** — nothing was lost by removing them |

**2. Was anything lost rather than reconciled?** No. All eight `## Other` bullets walked from the pre-R1
HEAD copy, and every "duplicate" disposition verified against surviving text rather than accepted:

| HEAD `## Other` bullet | Claimed disposition | Verified |
|---|---|---|
| "internal docs cleanup / spec consolidation — no upstream-parity surface" | recovered as `## Scope`'s closing bullet | **Present**: "The card shipped documentation only: no package surface and no upstream-parity change." |
| "onboarding-doc consolidation across README / docs / CHANGELOG; completed spec content folded into durable docs" | duplicate | **Duplicated**: the lead sentence plus the six file bullets carry the first half; the fold-in bullet carries the second verbatim in substance |
| `README.md` | duplicate | **Named** in `## Scope` bullet 1 |
| `docs/README.md` | duplicate | **Named** in bullet 2 |
| `docs/GLOSSARY.md` | duplicate | **Named** in bullet 4 |
| `docs/TREE.md` | duplicate | **Named** in bullet 5 |
| `CHANGELOG.md` | duplicate | **Named** in bullet 6 |
| the spec-filename convention bullet | dropped and pointed (D11) | **Both halves accounted for**: the filename convention is pointed at `AGENTS.md` rule 26 + `BUILD.md`; the "then get folded into durable docs when shipped" half survives in the fold-in bullet |

`## Planning note`'s content ("shipped") lives in the rationale's `### \`## Planning note\`` entry — R1's
move, verified present. The `## Card snapshot` board fields removed (labels, priority, relative size)
are all rendered into `KANBAN.md` as the replacement sentence claims, so their removal is a
de-duplication and not a loss. **Nothing the card asserted has disappeared from the repository.**

**3. Does the spec narrate its own history?** No, and I rule line 7 a legitimate pointer rather than the
beginning of a changelog. It names what lives in the rationale and asserts nothing a reader must apply a
chronology to; every sentence in the spec is a statement about now. It is also squarely on the
repository's established convention — `spec-002` ("every claim it once made and no longer makes"),
`spec-004` ("every claim the spec once made and may no longer make"), `spec-005` ("the retracted claims
of every section that has been reconciled"), and `spec-006` ("the three-section README shape this spec
declined") all carry the same shape, several with the same specificity. No amendment block, no
retraction paragraph, no "as of" hedge and no dual tense exists anywhere in the file — checked by reading
all 57 lines, not by grep.

**4. The 1-anchor constraint — verified, not accepted.**

- Anchor resolves: `grep -n '^## \`DjangoOptimizerExtension\`' docs/GLOSSARY.md` → line 712.
- Link text byte-identical to the CSV: the CSV row is
  `optimizer behavior,djangooptimizerextension,Backfilled…` and the spec carries
  `[optimizer behavior][glossary-djangooptimizerextension]` inside `## Scope` bullet 2's runtime-behavior
  clause. Matches. The CSV was not modified (`git status` shows it clean and untracked-free).
- The DB agrees: card 7's one glossary link is `('optimizer behavior', 'djangooptimizerextension')`.
- No hollow bullet was left to host the link; the carrier is live contract prose.

Commands re-run this pass, quoted verbatim as run:

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0
```

All four reproduce the pass's quoted output exactly. `import_spec_terms --check` was run **read-only**
and wrote nothing; the DONE-card chain for card 7 is intact.

**5. Figures re-derived by me.** Every number in both durable files and in this artifact:

| Figure | Source | Result |
|---|---|---|
| Spec at `947f7494` | `git show … \| wc -lc` | **65 / 2,282** — matches the rationale's `## How to read this file`; **contradicts** the reconciliation record's "measured at `947f7494`" (M2) |
| Spec after | `wc -lc` on the tree | **57 / 2,989** ✓ |
| Rationale after | `wc -lc` | **586 / 39,038** ✓ |
| Cumulative diffstat | `git diff --numstat` | **20 insertions / 28 deletions** ✓; 65 − 8 = 57 reconciles, and R1's 2/5 reconciles 65 → 62 |
| Card 7 items | live DB `Counter(i.section …)` | **14**: `Scope` 6 / `Files likely touched` 5 / `Note` 2 / `Why it matters` 1 → `## Other` = **8** ✓ |
| Labels / priority / size / planning_note | live DB | `['docs','internal','release']` / `Medium` / `S` / `''` ✓ |
| "four entries above resolve to `#card-snapshot`" | `grep -n` → body sites 82, 133, 142, 166 above line 453 | **four** ✓ — the pass's self-caught correction is right |
| "six rendered rows became eight contract claims" | `## Scope` bullets: pre-R1 **6**, now **8** ✓ | ✓ |
| `## Card snapshot` bullets | **2** ✓ | ✓ |
| Spec link defs / uses | script | **10 defs, 10 unique uses** (11 total; `[kanban]` used twice) ✓ |
| Rationale link defs | script | **15**, not 14 (L3) |
| `### Notes for Worker 1` instances in R1 | `grep -n` | **6**, not 5 (L3) |
| Migration `0016_remove_other_section.py` | `ls` | exists ✓ |
| `BUILD.md` `## Spec and build-plan filename pattern` | `grep -n` → line 7 | **exists** ✓ — D11's new citation resolves, unlike the one it replaced |
| `AGENTS.md` rule 26 | read | is the design-doc / spec-filename / archival rule ✓ |
| Working tree | `git status --porcelain \| wc -l` | **26** = the 25 recorded + this artifact ✓ |
| Zero fenced blocks in the spec | `grep -c '```'` → 0 | ✓ |
| Zero raw `path:NN` in both durable files | regex | ✓ |

Two figures failed and both are recorded above (M2, L3). Everything else reproduced.

**6. Link scaffold — resolved by me, per file.** Both files: **10 canonical group headers present and in
the required order**; **zero unused** and **zero undefined** definitions; **every** definition resolves on
disk by absolute-path expansion. The depth trap, established per file rather than trusted from either
document: from `docs/SPECS/`, `../../README.md` → repository-root `README.md` and `../README.md` →
`docs/README.md`; from `docs/SPECS/appx/`, `../../../README.md` → root `README.md` and `../../README.md`
→ `docs/README.md`. **The artifact states both correctly**; I found nothing inverted. `[root-readme]` and
`[readme]` in each file land where their names claim.

The two prior-rationale-text repairs verified: `[spec-007-other]` is absent from the definition block and
has zero remaining uses, and the entry that used it now reads "Bore on [Scope][spec-007-scope]". The
entry still names the spec section it belongs to, so `BUILD.md`'s keying requirement holds — the entry is
keyed to a section that exists rather than to one the spec retired, which is stronger than before. Both
spec anchors the rationale targets (`#card-snapshot`, `#scope`) match the spec's only two `##` headings.

**7. Disposition completeness.** All fourteen drift rows D1-D14 appear in the table with a stated
disposition and a stated basis; no row is silently skipped and every "no change" row (D1, D2, D4, D14)
carries a reason. Spot-verified independently: D1 `grep -c 'intentionally lightweight'` → 0; D4
`grep -c '^## Planning note'` → 0; D13 `grep -c '^## Other'` → 0 and migration 0016 present; D11's new
citation resolves. All seven plan corrections appear with a disposition; the five "honoured by omission"
claims are verifiable as absences and I confirmed each — no `231911a8` file-set claim, no
`planning_note` mechanism claim, no "three-minute" surface count, no sibling-size comparison, no table
count, and no superlative entered either durable file this pass.

**8. Public-surface check.** `git diff -- django_strawberry_framework/__init__.py` → empty. `__all__` and
the re-export list are unchanged; no new public exports.

**CHANGELOG sanity.** Not applicable — this unit does not touch `CHANGELOG.md`, confirmed by
`git diff --stat -- CHANGELOG.md` returning empty. The spec's claim *about* the changelog was reconciled
in the spec, which is what `AGENTS.md` rule 21 requires.

**Static helper.** `scripts/review_inspect.py` was **not** run, and the reason is recorded rather than
omitted: `BUILD.md` `### When to run the helper during build` scopes Worker 3's invocations to
repeated-literal and import-boundary evidence in Python source. This unit writes two Markdown files and
the plan makes all package source read-only, so there is no source for the helper to inspect.

### What looks solid

- **The strategy is the right one and it was independently justified.** The role-versus-inventory split
  is not merely adopted from R1 — the pass re-derived it, and my own check agrees: every role claim in
  the pre-R1 spec still holds ten patch releases later and every contents claim failed. A spec whose
  subject is documentation state has exactly one durable form, and this is it.
- **The `## Card snapshot` judgement is correct and non-obvious.** Hollowing the section rather than
  deleting it preserves four rationale entries' anchor, and pushing the fix to the section rather than
  patching the label bullet is what stops it re-rotting on the next board edit. Patching the bullet to
  "three labels" was the obvious repair and losing it was right.
- **The 1-anchor constraint was the cycle's single point of failure and it held cleanly** — re-sited into
  live contract prose, in the same edit, with byte-identical link text and no hollow carrier.
- **`## Other` was retired without losing anything**, which I verified bullet by bullet from the pre-R1
  copy rather than from the pass's account. The recovered non-goal bullet is a genuine recovery, not a
  restatement.
- **The three refused near-copies are genuinely absent**, so the single-ownership law was applied and not
  merely cited.

### Temp-test verification

None created; a Markdown reconciliation has no behavior to pin. `docs/builder/temp-tests/r2/` was not
created and nothing needs promotion.

### Working-tree churn observed during this review pass

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` → **26 entries** at the open and
at the close of this pass, byte-for-byte identical: the 25 the perform record quotes, plus
`docs/builder/bld-007-r2-spec_reconciliation.md` itself. **No growth this pass and no new path**, so
Worker 0 has nothing to append. HEAD unchanged at `947f7494` at both reads, so nothing this cycle wrote
was swept into a concurrent commit.

The five `docs/review/rev-*.md` deletions remain **escalated and unresolved**; not restored, not
reverted, not touched. `docs/review/review-0_0_14.md` and `docs/review/rev-_boundary_ordering.md` were
not touched. The concurrent spec-002 / spec-006 paths and the third session's four package-source and
test files were not read for content and not touched.

### Notes for Worker 1 (spec reconciliation)

Extends the **six** instances in `docs/builder/bld-007-r1-rationale_move.md` and the one in this
artifact's perform record. Nothing in any of them is retracted, and everything routed to R3 still stands:
`CONTRIBUTING.md`'s dangling `BUILD.md` citation, the eight-bullets-not-a-table shape of the root
README's map, the staged-anchor sweep, `import_spec_terms --check` (re-run green this pass, so R3
inherits a verified-not-assumed baseline), and the unresolved `docs/review/rev-*.md` escalation.

New from this pass:

1. **The apply-changes pass is Worker 1's, not Worker 2's** (plan Deviation 2 corollary), and it sets
   `planned` again. Two Mediums are open; M1 requires a spec edit only Worker 1 may make.
2. **M1 is the finding this audit exists for, and it is a coupling defect rather than a bullet defect.**
   The `CONTRIBUTING.md` bullet is true and belongs; the lead sentence that turns it into a claim about
   the card's act is what fails. Resist widening the fix — deleting or hedging the bullet would recreate
   exactly the failure the spec is a case study in, which is a reader unable to tell where content went.
3. **`[spec-006-rationale]` re-resolved as R1's sixth note required**, rather than assumed: it points at
   `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`, which exists on disk and is still
   **untracked**. Unchanged from R1's ruling; R3 re-resolves it again and, if the sibling cycle has not
   landed it, retires the definition and its use site in one edit.
4. **Escalated — the enumeration convention needs a scope word, not another member.** `## How to read
   this file`'s measurement enumeration is now the third place this cycle has had to extend a
   completeness claim, and M2 is what happens when a figure is anchored to a hash whose *tree state* is
   not the one measured. The resolution paths for the maintainer: (a) require every durable figure to
   name both the commit and whether it is the committed or the working-tree state, or (b) forbid
   working-tree figures in durable files entirely and record them only in `bld-*.md`. Option (b) removes
   the class; option (a) keeps the before/after pair legible. This is a `BUILD.md`-level convention
   question, not a spec-007 one, and I have not acted on it.
5. **Two scratchpad miscounts are superseded in this section, not routed** (L3). No spawn is owed for
   them and the apply-changes pass should not re-open them; the durable files carry neither.

### Review outcome

`Status: revision-needed`. Two Medium findings, both in durable files, both requiring the spec custodian:
M1 is a false attribution introduced by this pass in
`docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md`, and M2 is a self-contradicting
measurement anchor in the rationale. L1 and L2 are spec-text findings that ride with the same edit. L3 is
discharged here. Per the plan's Deviation 2 corollary this routes to **Worker 1**, which re-sets
`planned`.


---

## Perform record (Worker 1, pass 2 — apply changes)

Fresh invocation with none of the prior pass's context; the artifact on disk and the working-tree diff
were the authority. Per the plan's **Deviation 2 corollary** the fix for Worker 3's findings is Worker
1's, so this pass both decides and applies, and re-sets `Status: planned` for the R3 audit.

HEAD re-derived at the open and the close: `947f74948c16b20b0c15ff359bb53fbe462d4b8c`, unchanged. No
`pytest` ran, no `--cov*` flag was passed, no `git stash` / `checkout` / `restore` / `worktree` was
used, nothing was committed, and no branch was created.

**Findings closed:** M1, M2, L1, L2. **L3 left alone** — Worker 3 superseded both scratchpad miscounts
in its own review section rather than routing them, and re-fixing a superseded finding would edit a
prior entry.

### Every claim re-derived before it was written

Nothing below was taken from the plan, from R1, or from Worker 3's review; each was measured this pass
from the primary source, and each figure that landed in a durable file is attributed to the state it
was measured at.

| Claim | Command | Result |
|---|---|---|
| The card's three documentation commits never touch `CONTRIBUTING.md` | `git show --stat` on `4b8dce07`, `83c25963`, `3a4d40b7` | Confirmed. File sets are `README.md`, `docs/README.md`, `docs/FEATURES.md`, `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md`, `AGENTS.md`, `START.md`, `docs/alpha-review-feedback.md`, `docs/feedback.md`, the deleted `docs/spec-*.md`, and package source. No `CONTRIBUTING.md` in any |
| The release commit does not either | `git show --stat 231911a8` | Confirmed — exactly two files, `CHANGELOG.md` and `KANBAN.md` |
| Dates | `git show -s --date=short` | `4b8dce07` / `83c25963` / `3a4d40b7` all 2026-05-05; `231911a8` 2026-05-08; `b57eba38` and `2bd7cb84` both 2026-05-16 — an eight-day gap after the release; `2428cd8f` 2026-04-29 |
| `CONTRIBUTING.md` at the release commit | `git show 231911a8:CONTRIBUTING.md \| grep '^#'` | `## Getting started`, `## Running the test suite`, `## Linting and formatting`, then `## Commit messages`, `## Pull requests`, `## Reporting issues`, `## Code of conduct`. **None of versioning / building / publishing / dependencies** |
| `CONTRIBUTING.md` at HEAD | `grep '^#' CONTRIBUTING.md` | All six responsibilities the spec bullet names resolve, plus `## Where things live` and `## Updating dependencies` |
| Spec at `947f7494` | `git show HEAD:<path> \| wc -lc` | **65 lines / 2,282 bytes** — not the 62 / 2,365 the rationale attributed to that hash |
| Spec on disk at this pass's open | `wc -lc` | **57 lines / 2,989 bytes** |
| Root `README.md`'s pointer set | read `## Project documentation` + `## Contributing & Security` | Eight bullets plus three: `docs/README.md`, `docs/GLOSSARY.md`, `GOAL.md`, `TODAY.md`, `docs/TREE.md`, `KANBAN.md`, `BACKLOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`. **All five other files in this spec's set are pointed at; `AGENTS.md`, `START.md` and `docs/builder/BUILD.md` are not** |
| `docs/GLOSSARY.md`'s categories | the file's own line 3 | **Four**: public symbol, `Meta` key, **configuration argument**, named behavior |
| Glossary link text vs the CSV | read `docs/SPECS/appx/spec-007-…-terms.csv` | `raw_text` is `optimizer behavior`; the spec's `[optimizer behavior][glossary-djangooptimizerextension]` is byte-identical. **Bullet 2 was not touched by this pass**, so the carrier is unchanged |

### The decoupling, and what it rejected

**Chosen: state the division, do not claim authorship of it.** The lead sentence changes from "The card
divided the onboarding documentation by the question each file answers…" to "The onboarding
documentation is divided by the question each file answers…". One clause; no bullet changes; the
`CONTRIBUTING.md` bullet survives untouched. Every bullet is now a present-tense role claim about the
current set, which is what they already were — only the sentence framing them as the card's act was
false. The section states what is true and no longer asserts who did it.

Rejected:

- **Delete the `CONTRIBUTING.md` bullet.** Explicitly refused by the dispatch and correctly so: it
  would trade a true, checkable statement for a gap, and leaving a reader unable to tell where the
  operational content went is the exact failure this spec is a case study in.
- **A dated hedge or an "as of `0.0.4`" clause.** `BUILD.md` `## Spec rationale extraction` forbids the
  spec narrating its own history; the same alternative was already rejected in R2's first pass, and
  admitting it now to fix a different finding would reverse a settled call.
- **Attribute explicitly in the spec** (Worker 3's option 2), naming `b57eba38` / `2bd7cb84` in the
  bullet. Rejected: it puts a chronology into the contract, which is option 1's whole advantage.
- **Keep "the card" and qualify it per bullet** ("the card divided all but one of these…"). Rejected as
  a counting claim inside a contract sentence — the cycle's own defect class — and it would re-rot the
  moment another document joined the set.

The chronology went to the rationale instead, and only the part not already there: `### `## Scope` 1`
already dates the root-README removal to `2bd7cb84` (2026-05-16), so the reconciliation record adds
`b57eba38`, the card's four non-touching commits, and the eight-day gap, and points at the existing
entry for the removal date rather than restating it.

### Spec changes made (Worker 1 only)

Three in the spec, four in the rationale. Each names the section, the finding it closes, and a one-line
reason.

1. **Spec `## Scope`, lead sentence** (closes **M1**) — "The card divided the onboarding documentation
   by the question each file answers" becomes "The onboarding documentation is divided by the question
   each file answers". Reason: the bullets are true about the settled division and false as assertions
   about the card's act, and only the framing sentence made them the latter.
2. **Spec `## Scope`, bullet 1** (closes **L1**) — "the pointer set into every other document" becomes
   "the pointer set into the rest of this set". Reason: the universal is false outside the onboarding
   set; scoped to the set it is verified true for all five other files.
3. **Spec `## Scope`, the `docs/GLOSSARY.md` bullet** (closes **L2**) — "one stably anchored entry per
   public symbol, `Meta` key, and named behavior" becomes "every catalogued capability gets one entry,
   and every entry a stable anchor". Reason: the enumeration was a borrowed taxonomy missing one of its
   owner's four categories; dropping it states the role without a partial list that reads as complete.
4. **Rationale `## Reconciliation record`, opening measurement sentence** (closes **M2**) — the
   before/after pair is now labelled as two working-tree measurements taken on top of `947f7494`, with
   the committed file's own figure pointed at in `## How to read this file` rather than restated.
   Reason: 62 / 2,365 is the post-extraction working tree, not what the hash yields, and the file
   contradicted itself between two anchored sentences. The after-figure was re-measured after the spec
   edits landed, so it is **2,983** bytes, not the 2,989 the sentence previously carried.
5. **Rationale `### The strategy, and what it rejected`** (M1, consistency) — no longer calls the
   division "the card's actual durable output"; states instead that the lead sentence deliberately does
   not credit the division to the card. Reason: the record must not assert what the spec was just
   corrected for asserting.
6. **Rationale `### `## Scope` — six rendered rows became eight contract claims`, root-README bullet**
   (M1 + L1, consistency) — records the narrowing of "every other document", and adds the chronology
   the decoupling rests on: the card's three commits and `231911a8` touch `CONTRIBUTING.md` in none of
   their file sets, and the operational sections arrived at `b57eba38`, eight days after the release.
   Reason: the chronology belongs in the rationale, and this half of it was nowhere on disk.
7. **Rationale, same section, `docs/GLOSSARY.md` bullet** (L2, consistency) — records that the
   enumeration was dropped rather than completed, and why. Reason: the record described a bullet that
   no longer reads that way.

**One addition, not a change:** the rationale gains a closing `### What the audit of this record changed
in it`, naming all four in-place edits to the appended record plus the three spec edits, so the
append-only file stays auditable without a diff. `worker-1.md` rule 4's append-only constraint covers
the rationale during the build; these four edits are corrections *to this cycle's own appended record*
in response to its audit, which is the same mechanism the first pass used for its two link repairs, and
they are named on disk for the same reason.

### Validation run

Every command re-run after the final edit, on every file written, quoted verbatim as run:

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0
```

`import_spec_terms --check` ran read-only and wrote nothing; card 7's DONE chain is intact.

**The 1-anchor constraint was not exercised, and that is the correct outcome.** The single anchor lives
in `## Scope` bullet 2, and no edit this pass touched bullet 2 — M1's fix is the lead sentence, L1's is
bullet 1, L2's is the glossary bullet. The link text remains byte-identical to the `-terms.csv`
`raw_text` (`optimizer behavior`), the CSV was not touched, and the baseline `OK: 1 terms` is unchanged.

### Byte and line counts, measured as written

| File | Before this pass | After this pass |
|---|---|---|
| `docs/SPECS/spec-007-…-0_0_4.md` | 57 lines / 2,989 bytes | **57 lines / 2,983 bytes** |
| `docs/SPECS/appx/spec-007-…-rationale.md` | 586 lines / 39,038 bytes | **625 lines / 42,260 bytes** |
| `docs/builder/bld-007-r2-spec_reconciliation.md` | 862 lines / 59,863 bytes | **1,090 lines / 75,761 bytes** |

All four before-figures were measured on disk at this pass's open with `wc -lc`, not carried from the
prior section; all after-figures were re-measured after the last edit to each file. For the record: the
spec's committed state at `947f7494` is **65 lines / 2,282 bytes**, a third figure again, and the one
M2 exists to keep distinct.

### Link scaffold audit

Both durable files, re-resolved after the final edit, by absolute-path expansion rather than by eye,
with code spans stripped before the use sweep:

- **10** canonical group headers present and in the required order, in both files.
- **Spec**: 10 definitions, 10 unique uses, **zero unused**, **zero undefined**; every target resolves
  on disk.
- **Rationale**: **15** definitions, 15 unique uses, zero unused, zero undefined; every target resolves
  on disk. (15 is Worker 3's L3 correction and it reproduces here; `[glossary]` picked up a second use
  from this pass's edit and was already defined and used.)
- **Depth trap re-checked per file, both directions.** From `docs/SPECS/`: `../../README.md` normalizes
  to `README.md` (repository root) and `../README.md` to `docs/README.md`. From `docs/SPECS/appx/`:
  `../../../README.md` normalizes to `README.md` and `../../README.md` to `docs/README.md`. Both files'
  `[root-readme]` and `[readme]` land where their names claim.
- **Both anchors the rationale targets exist**: `#card-snapshot` and `#scope` match the spec's only two
  `##` headings.
- `AGENTS.md` rule 27: **zero** raw `path:NN` references in either durable file, verified by regex over
  the body of each. Raw line refs appear only in this artifact, which rule 27 exempts.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Notes for Worker 1 (spec reconciliation)

Extends the six instances in `docs/builder/bld-007-r1-rationale_move.md` and the two in this artifact.
Nothing in any of them is retracted, and everything still routed to R3 stands: `CONTRIBUTING.md`'s
dangling `BUILD.md` heading citation, the eight-bullets-not-a-table shape of the root README's map, the
staged-anchor sweep, and the unresolved `docs/review/rev-*.md` escalation.

New from this pass:

1. **All four routed findings are closed and none was closed by deletion.** M1 cost one clause, L1 four
   words, L2 one enumeration; M2 cost a label on a number that was already correct as a measurement.
   Nothing true was removed from either file.
2. **The `CONTRIBUTING.md` bullet stays, ruled a second time.** Worker 3 ruled it legitimate and this
   pass re-verified the ruling from source rather than inheriting it: the file existed three months
   before the ship window and all six responsibilities resolve at HEAD. R3 should not re-open it.
3. **M2's class is now recorded in the file that carries it**, not only in Worker 3's escalation: a
   figure anchored to a hash whose *tree state* is not the one measured. Worker 3's `BUILD.md`-level
   convention question — require both the commit and the committed/working-tree state, or forbid
   working-tree figures in durable files entirely — is still the maintainer's and is **not** acted on
   here. This pass applied option (a) locally because it is the smaller change and keeps the
   before/after pair legible.
4. **The rationale is now 42,260 bytes against a 2,983-byte spec**, a ratio worth a maintainer's eye at
   some point. Not a defect and not this cycle's to fix: the spec is a card-snapshot stub and the
   rationale is carrying a ten-release change record for it.
5. **The eighth instance of the cycle's defect class did not land, and one near-miss is recorded.** The
   after-figure for the spec was written into the rationale as an estimate before the file was measured
   and was corrected in the next command — before any checker ran, and before the sentence was final.
   It is named here rather than left silent because "I measured it afterwards" is exactly how the
   previous seven happened. R3 should re-derive every figure in this section rather than reproduce it.

### Working-tree churn and baseline growth

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` reads **26 entries** at the
open and at the close of this pass, byte-for-byte identical to the 26 Worker 3's review recorded: the
25 baseline-dirty paths plus this artifact. **No growth this pass and no new path**, so Worker 0 has
nothing to append. The namespaced memory file is under `.gitignore` (`docs/builder/worker-memory/`) and
so never appears in the count.

The five `docs/review/rev-*.md` deletions remain **escalated and unresolved** — still tracked at HEAD,
still absent from disk, not restored, not reverted, not touched. `docs/review/review-0_0_14.md` and
`docs/review/rev-_boundary_ordering.md` were not touched. The concurrent spec-002 and spec-006 cycles'
paths and the third session's four package-source and test files were **not read for content, not
touched, not reverted, not staged**. HEAD is unchanged at
`947f74948c16b20b0c15ff359bb53fbe462d4b8c` at both reads, so nothing this pass wrote was swept into a
concurrent commit.

### Status

`planned`. Per the plan's Deviation 2, Worker 0 reads this as "dispatch Worker 3 for the audit".

---

## Review (Worker 3, pass 2)

Fresh invocation with none of pass 1's context; the artifact on disk and the working-tree diff were the
authority. HEAD re-derived at the open and the close: `947f74948c16b20b0c15ff359bb53fbe462d4b8c`,
unchanged. The pre-R1 spec was read with `git show <commit>:<path>` only; no `git stash` / `checkout` /
`restore` / `worktree` was used, nothing was committed, no branch was created, no `pytest` ran and no
`--cov*` flag was passed. No temp tests were needed, so `docs/builder/temp-tests/r2/` was not created.
`scripts/review_inspect.py` was **not** run, for the reason pass 1 recorded and which still holds: this
unit writes two Markdown files and the plan makes all package source read-only, so there is no Python
source for the helper to inspect.

**Declarations checked against the plan and correct as absences:** no failability proof is owed (this
pass introduces no boundary), no hot-path number is owed, no floor run is owed. The three headings are
present and correctly say so.

**Scope of this pass.** Convergence, not a fresh sweep. Pass 1's substantive verdicts — no `## Other`
content lost, the reconciliation states roles rather than a table of contents, the 1-anchor chain
intact, the `CONTRIBUTING.md` bullet legitimate — stand and were not re-opened.

### High: None.

### Medium: None.

Both routed Mediums are closed, and each was re-derived here rather than read off the perform record.

**M1 — closed, and the fix genuinely solves it.** The `## Scope` lead sentence on disk is "The
onboarding documentation is divided by the question each file answers, so that no two files answer the
same one." — impersonal, with the bullets left as present-tense role claims. I then searched for a
surviving attribution rather than accepting the decoupling on its face:

- `grep -n -i 'card'` over the whole spec returns exactly six lines: the target-release line, the
  rationale pointer (line 7), the `## Card snapshot` heading and its two bullets, and `## Scope`'s
  closing non-goal bullet. **None of them asserts that the card performed the division.** The closing
  bullet ("The card shipped documentation only: no package surface and no upstream-parity change") is a
  scope boundary, not a claim of authorship over the six role bullets.
- In the rationale's reconciliation record the decoupling is stated and justified: `### The strategy`
  says the lead sentence "does **not** credit it to the card, because the division as it now stands is
  not entirely the card's act", and the root-README bullet carries the chronology that rests on. The
  record no longer calls the division the card's durable output.
- The M1 chronology is verified from git, not from the record: `git show --stat` on `4b8dce07`,
  `83c25963`, `3a4d40b7` and on `231911a8` yields **zero** `CONTRIBUTING.md` hits in all four
  (`231911a8` is exactly `CHANGELOG.md` + `KANBAN.md`); `b57eba38` (2026-05-16) is the commit that
  touches it; `2bd7cb84` (2026-05-16) is the root-README removal; `231911a8` is 2026-05-08, so the
  eight-day gap is right. `git log --diff-filter=A -- CONTRIBUTING.md` → `2428cd8f`, 2026-04-29.

**M2 — closed.** The measurement sentence now reads "The spec went from 2,365 bytes / 62 lines to 2,983
bytes / 57 lines. Both are **working-tree** measurements taken on top of `947f7494` — the before-figure
is the state the extraction pass left on disk, not the committed file, whose own figure `## How to read
this file` records." Re-derived: `wc -lc` on the tree gives **57 / 2,983**, matching; `git show
947f7494:<spec> | wc -lc` gives **65 / 2,282**, and `## How to read this file` states exactly that at
line 26. The hash is no longer asked to produce a number it does not yield, and the committed figure is
pointed at rather than restated, so the two sentences can no longer contradict each other.

**L1 — closed.** Spec bullet 1 reads "the pointer set into the rest of this set". Verified: root
`README.md`'s definition block resolves `[readme]`, `[contributing]`, `[glossary]`, `[tree]`,
`[changelog]` — all five other members of the set — and defines **no** ref for `AGENTS.md`, `START.md`
or `docs/builder/BUILD.md`, so the narrowing is both necessary and sufficient.

**L2 — closed.** The glossary bullet now reads "every catalogued capability gets one entry, and every
entry a stable anchor" — a role statement with no enumeration. `docs/GLOSSARY.md` line 3 carries four
categories (public symbol, `Meta` key, **configuration argument**, named behavior); the spec no longer
enumerates any, so the partial-list defect is removed rather than patched.

**L3 — correctly left alone.** Both miscounts were superseded in pass 1's own section; re-fixing them
would have edited a prior entry.

### Low:

**L4 — A universal in newly written durable prose that the pass's own measurement contradicts.**
`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`,
`### `## Scope` — six rendered rows became eight contract claims`, the root-README bullet: "At
`231911a8` the file carried getting-started, test-suite, and linting sections only".

`git show 231911a8:CONTRIBUTING.md | grep '^#'` returns **seven** `##` headings, not three: `## Getting
started`, `## Running the test suite`, `## Linting and formatting`, `## Commit messages`, `## Pull
requests`, `## Reporting issues`, `## Code of conduct`. This artifact's own
`### Every claim re-derived before it was written` table records all seven correctly — so the
measurement was right and the sentence written from it narrowed to "only".

The load-bearing content is true and unaffected: none of the four operational responsibilities was
present, and they arrived at `b57eba38`. The semicolon clause that follows scopes the "only" to that
contrast for a careful reader. But the literal sentence asserts a three-section file, which is this
cycle's own recurring class — an unmeasured universal in a durable file — and it is the ninth instance
the dispatch predicted. *Recommended change:* scope the word, e.g. "carried three of the six — getting
started, test suite, and linting — and none of the other three". Four words, no fact changes.

**L5 — A self-contradicting sentence in the new closing section of the rationale.** Same file,
`### What the audit of this record changed in it`, first bullet: "**Only** the after-figure is a
working-tree measurement taken on top of that commit **and the before-figure is too**".

As written this is incoherent: "only X … and Y too". The intended meaning is recoverable from the next
sentence ("Both are now labelled as the working-tree states they are") and from the corrected
measurement sentence itself, so no fact is wrong — but a durable file should not make a reader
reconstruct a clause. It reads as an edit that inserted the correction without retiring the "Only".
*Recommended change:* "Neither figure is the committed file: both are working-tree measurements taken
on top of that commit, whose own figure `## How to read this file` carries and which is a third number
again."

### DRY findings

None. This pass changed one clause, four words, and one enumeration in the spec, and added one section
plus three consistency edits to the rationale. It creates no abstraction, helper, registry or
indirection layer, so no existence challenge arises. The spec-versus-rationale split still holds: I
re-checked the three facts most at risk of being told twice — the `CONTRIBUTING.md` division, the
"every other document" narrowing, and the glossary category taxonomy — and each appears as a contract
in the spec **or** as a change record in the rationale, never as the same sentence in both.

### Verification performed

**1. The four closures, each re-derived.** Recorded above: M1 held, M2 held, L1 held, L2 held. **M1 is
genuinely solved** — no surviving clause in the spec or in the rationale's reconciliation record
asserts that the card performed the division.

**2. The three edits are the only edits, proved arithmetically rather than asserted.** The spec went
57 / 2,989 → 57 / 2,983, a **−6 byte** delta at an unchanged line count. Computing the three claimed
substitutions in isolation:

| Substitution | Delta |
|---|---|
| "The card divided the onboarding documentation" → "The onboarding documentation is divided" | **−6** |
| "every other document" → "the rest of this set" | **0** |
| "one stably anchored entry per public symbol, `Meta` key, and named behavior" → "every catalogued capability gets one entry, and every entry a stable anchor" | **0** |
| **Total** | **−6** |

The three edits account for the whole delta exactly, so nothing else in the spec was touched. That is
also the independent proof that **`## Scope` bullet 2 — the sole glossary carrier — was genuinely not
touched this pass**, which the perform record claims and which the 1-anchor chain depends on.

**3. Every figure re-derived, in both durable files and in this artifact's new section.**

| Figure | Command | Result |
|---|---|---|
| Spec on disk | `wc -lc` | **57 / 2,983** ✓ |
| Spec at `947f7494` | `git show … \| wc -lc` | **65 / 2,282** ✓ — matches `## How to read this file` |
| Rationale on disk | `wc -lc` | **625 / 42,260** ✓ |
| This artifact | `wc -lc` | **1,090 / 75,761** ✓ (before the append below) |
| Spec `##` headings | `grep -n '^## '` | **2** — `Card snapshot`, `Scope`; both rationale anchors resolve ✓ |
| Fenced blocks in the spec | `grep -c` on the fence marker | **0** ✓ |
| Card's three commits + release touch `CONTRIBUTING.md` | `git show --stat` ×4 | **0 hits in all four** ✓; `231911a8` is exactly 2 files |
| Dates | `git show -s --date=short` | `4b8dce07`/`83c25963`/`3a4d40b7` 2026-05-05, `231911a8` 2026-05-08, `b57eba38` and `2bd7cb84` both 2026-05-16, `2428cd8f` 2026-04-29 ✓ — eight-day gap correct |
| `CONTRIBUTING.md` at `231911a8` | `git show … \| grep '^#'` | **seven** `##` headings, not three — **L4** |
| `CONTRIBUTING.md` at HEAD | `grep '^#'` | all six responsibilities the spec bullet names resolve ✓ |
| Root README pointer set | README def block | five set members defined; `AGENTS.md` / `START.md` / `BUILD.md` **absent** ✓ |
| `docs/GLOSSARY.md` categories | file line 3 | **four**, incl. configuration argument ✓ — and the spec now enumerates none |
| Glossary anchor | `grep -n` | `## \`DjangoOptimizerExtension\`` at line **712** ✓ |
| Spec link defs / uses | script, code spans neutralised | **10 defs / 10 unique uses / 11 total** (`[kanban]` twice) ✓ |
| Rationale link defs / uses | same | **15 defs / 15 unique uses / 60 total** ✓ — pass 1's L3 correction reproduces |
| `### Notes for Worker 1` in R1 | `grep -c` | **6** ✓ — the perform record's "six" is right |
| Same heading in this artifact | `grep -c` | **3** including this section; the record's "the two in this artifact" means the two preceding it, matching pass 1's convention ✓ |
| "four of its statements were corrected in place" | count the bullets + cross-check against the perform record's items 4-7 | **four** ✓ |
| "The spec changed in three places" | the −6 arithmetic above | **three** ✓, and each is recorded with the claim it belongs to ✓ |
| Working tree | `git status --porcelain \| wc -l` | **26** ✓ |

Two figures produced a finding (**L4**); everything else reproduced. **The ninth defect exists and it is
L4** — the class held exactly as the dispatch predicted, and the pass's own near-miss note (2,989
estimated, 2,983 measured) shows the discipline caught the numeric instance and missed the verbal one.

**4. Regression checks — commands re-run, quoted verbatim as run.**

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0
```

All four reproduce the perform record's quoted output exactly. `import_spec_terms --check` ran
**read-only** and wrote nothing; card 7's DONE chain is intact.

**5. The 1-anchor chain.** `docs/SPECS/appx/spec-007-…-terms.csv` is a two-line file whose one row is
`optimizer behavior,djangooptimizerextension,…`; the spec carries
`[optimizer behavior][glossary-djangooptimizerextension]`, so the link text is **byte-identical** to
the CSV term. The CSV is clean in `git status`. The carrier is bullet 2's runtime-behavior clause,
proved untouched by the −6 arithmetic above, and the anchor resolves at `docs/GLOSSARY.md` line 712.

**6. Link scaffold, resolved by me per file.** Both files: **10** canonical group headers, present and
in the required order; **zero unused**, **zero undefined**; **every** definition resolves on disk by
absolute-path expansion. Depth trap re-derived per file: from `docs/SPECS/`, `../../README.md`
normalizes to root `README.md` and `../README.md` to `docs/README.md`; from `docs/SPECS/appx/`,
`../../../README.md` → root `README.md` and `../../README.md` → `docs/README.md`. Both files'
`[root-readme]` / `[readme]` land where their names claim. `AGENTS.md` rule 27: **zero** raw `path:NN`
in either durable file, by regex over the body with code spans neutralised.

**7. Does the spec read as a clean current contract?** Yes — read end to end as a first-time reader,
not grepped. Two sections, both present-tense. There is no chronology to apply, no "as of" hedge, no
amendment block, no retraction paragraph and no dual tense. Line 7 is a pointer to where the history
lives, which is the repository's established shape and which pass 1 already ruled legitimate. The one
past-tense sentence in the file — the closing non-goal — states a scope boundary, and a scope boundary
is exactly what a reader of a shipped card's spec needs. The maintainer's bar is met.

**8. Public-surface check.** `git diff -- django_strawberry_framework/__init__.py` → empty. `__all__`
and the re-export list are unchanged; no new public exports.

**CHANGELOG sanity.** Not applicable — this unit does not touch `CHANGELOG.md`, confirmed by
`git diff --stat -- CHANGELOG.md` returning empty.

### Convergence judgement — stated explicitly, as the dispatch requires

**This item converges here, and a third R2 round would cost more than it buys.** Five review rounds
have now run against a 57-line spec. All four routed findings are closed, none by deletion, and each
closure re-derived independently above. What remains is two Low copy defects in newly written rationale
prose: one narrowed word (L4) and one clause left un-retired by an in-place correction (L5). Neither
changes a fact, neither touches the spec, neither reaches the 1-anchor chain, and neither would lead a
reader to a wrong conclusion about what this card did or what these documents are for.

Against that, this cycle's measured evidence is that **every one of the eight prior apply-changes passes
introduced a new defect while closing its findings**, and the pass that produced L4 and L5 is the first
to self-catch one and record it. A ninth round would spend a full spawn to fix eleven words and would
carry the same historical risk of introducing a tenth defect. The findings are recorded with exact
recommended wording so `R3`'s durable-docs audit — a pass Worker 1 is already scheduled to run over
these two files — can apply them without a dedicated spawn.

I have neither manufactured a finding to justify this pass (L4 and L5 are both re-derived from primary
sources and both sit in text written this pass) nor withheld one that matters (nothing found rises to
misleading a reader of the durable files). `revision-needed` is not warranted.

### What looks solid

- **The M1 fix is the minimal correct one and it was verified as such.** One clause, no bullet changes,
  and the −6 arithmetic proves nothing else moved. Option 2 — dating the contract — was rejected for the
  right reason, and the chronology went to the file whose job it is.
- **The chronology added to the rationale is complete and checkable.** Four commits proved not to touch
  `CONTRIBUTING.md`, the successor commit named, the eight-day gap arithmetic correct, and the removal
  date pointed at rather than restated.
- **M2 was fixed at the level of the class, not the instance.** Labelling both figures as working-tree
  states and pointing at the committed figure removes the contradiction permanently rather than
  swapping one number for another.
- **L2 was closed by dropping the enumeration rather than completing it**, which is the correct call
  under the single-ownership law and the one this cycle's own record argues for.
- **The near-miss was recorded rather than left silent.** The 2,989-vs-2,983 self-catch is the first
  time in this cycle a pass has surfaced its own averted defect, and it is what made the L4 hunt
  targeted rather than speculative.

### Temp-test verification

None created; a Markdown reconciliation has no behavior to pin. `docs/builder/temp-tests/r2/` was not
created and nothing needs promotion.

### Working-tree churn observed during this review pass

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` reads **26 entries** at the
open and at the close of this pass, byte-for-byte identical to the 26 both prior sections recorded: the
25 baseline-dirty paths plus this artifact. **No growth this pass and no new path**, so Worker 0 has
nothing to append. HEAD is `947f74948c16b20b0c15ff359bb53fbe462d4b8c` at both reads, so nothing this
cycle wrote was swept into a concurrent commit.

The five `docs/review/rev-*.md` deletions remain **escalated and unresolved** — still tracked at HEAD,
still absent from disk, not restored, not reverted, not touched. `docs/review/review-0_0_14.md` and
`docs/review/rev-_boundary_ordering.md` were not touched. The concurrent spec-002 and spec-006 cycles'
paths and the third session's four package-source and test files were not read for content and not
touched.

### Notes for Worker 1 (spec reconciliation)

Extends the **six** instances in `docs/builder/bld-007-r1-rationale_move.md` and the **two** preceding
instances in this artifact. Nothing in any of them is retracted, and everything routed to R3 still
stands: `CONTRIBUTING.md`'s dangling `BUILD.md` heading citation, the eight-bullets-not-a-table shape of
the root README's map, the staged-anchor sweep, the `SpecDoc.path` / `-terms.csv` chain (re-run green
this pass, so R3 inherits a verified-not-assumed baseline), the `[spec-006-rationale]` definition whose
target still exists on disk and is still **untracked**, and the unresolved `docs/review/rev-*.md`
escalation.

New from this pass:

1. **Escalated — two Low copy defects in the rationale, to fold into R3's durable-docs audit rather
   than a new R2 round.** L4 (the "only" in the root-README bullet's `231911a8` clause) and L5 (the
   "Only … and … too" sentence in `### What the audit of this record changed in it`). Both carry exact
   recommended wording above; both are eleven words in total; neither touches the spec, the 1-anchor
   chain, or any fact. Resolution paths: (a) apply both during R3's sweep of the two durable files, or
   (b) leave L5 and apply only L4, since L4 is a literal falsehood and L5 is only a garbled clause.
   I recommend (a) — they are in the same file and the same audit already reads it end to end.
2. **`### Notes for Worker 1` is on disk in all three places and accurate for R3**, verified rather
   than assumed: six in R1, three here, and the cumulative list above carries every item R3 is
   scheduled to audit. The instance-count convention ("the N preceding it") is consistent across all
   three sections.
3. **The escalated `BUILD.md`-level convention question is unchanged and still the maintainer's** —
   require every durable figure to name both the commit and whether it is the committed or the
   working-tree state, or forbid working-tree figures in durable files entirely. Pass 2 applied option
   (a) locally, which is correct as a local fix and does not settle the convention. L4 is a second data
   point for the same underlying class: the durable-figure rule catches numbers, and this cycle's
   defects are now migrating into words that quantify.
4. **Do not re-open** the `CONTRIBUTING.md` bullet's legitimacy (ruled twice, verified from source both
   times), pass 1's `## Other` completeness walk, the line-7 pointer ruling, or L3's two superseded
   scratchpad miscounts.

### Review outcome

`Status: review-accepted`. No High and no Medium findings. All four findings routed by pass 1 (M1, M2,
L1, L2) are closed and independently re-derived; M1 is genuinely solved, with no surviving attribution
clause anywhere in the spec or the rationale's reconciliation record. Two Low findings (L4, L5) are
recorded with exact recommended wording and escalated to Worker 1's R3 durable-docs audit under
`### Notes for Worker 1` item 1, per `worker-3.md`'s transparent-escalation rule. R2 is converged.

---

## Final verification (Worker 1)

Fresh invocation with none of the prior passes' context; the artifact on disk and the working-tree diff
were the authority. Every figure, path, symbol, heading, category, and commit hash below was re-derived
this pass rather than read out of the plan, R1, the perform records, or either review section.

HEAD re-derived at the open and the close: `947f74948c16b20b0c15ff359bb53fbe462d4b8c`, unchanged. No
`pytest` ran, no `--cov*` flag was passed, no `git stash` / `checkout` / `restore` / `worktree` was
used, nothing was committed, and no branch was created.

**Declarations re-checked against the plan and correct as absences:** ownership partition none;
hot-path none, so no number is owed and its absence is correct; floor-verification scope none, so no
floor run is owed by this item; no failability proof owed. The `## Final test-run gate` belongs to
`bld-007-final.md` and was not run here.

### Spec status-line re-verification

Lines 1-5 read before anything else and checked against source, not against the plan:

- `Target release: 0.0.4 (per KANBAN.md card DONE-007-0.0.4)` — the live DB reads `card_id`
  `DONE-007-0.0.4`, `target_version.number` `0.0.4`, milestone `alpha`. Holds; no edit.
- `Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant
  intact` — holds (see the D2 walk below); no edit.
- `Owner: package maintainer` — holds; no edit.
- The line-7 rationale pointer still describes the finished file: it promises the change record and
  the claims the spec may no longer make, both of which this cycle extended rather than falsified. It
  now also covers this pass's two corrections, which landed in the file it points at. No edit.

### 1. Was R2's contract delivered?

**Yes.** Judged against the plan's `### Residual scope` R2 clause and the maintainer's framing, not
against the artifact's own account of itself.

- **The spec matches what exists.** Every one of the six role claims was re-checked against the file it
  names: root `README.md`'s eight `##` headings carry positioning, map and status with no operational
  step; `docs/README.md` carries `## Installation`, `## Quick start`, `## Running the example project`
  and `## Nested connection indexing`; `CONTRIBUTING.md` carries all six responsibilities the bullet
  names; `docs/GLOSSARY.md` self-describes at line 3 as a stably-anchored catalog; `docs/TREE.md`
  self-describes at line 3 as the detailed layout reference and covers the test-tree rationale;
  `CHANGELOG.md` self-describes at line 3 as the record of notable changes. Each holds.
- **Where later changes corrected what landed, the spec reflects that.** The operational half of the
  root README's old claim is not merely deleted — `CONTRIBUTING.md` is named as its destination, which
  is what makes the corrected division checkable rather than a gap.
- **Every explanation lives in the rationale.** The spec carries no commit hash, no date, no
  supersession note, and no chronology. `grep -ci 'as of'` on the spec → 0; there is no amendment
  block and no retraction paragraph.
- **It reads as a clean current contract.** I read all 57 lines as a first-time reader rather than
  grepping. Two sections, both present-tense; the single past-tense sentence is the closing non-goal,
  which states a scope boundary rather than a history. Nothing requires a chronology to interpret.

### 2. The disposition walk, performed independently

All fourteen drift rows carry a stated disposition and none is silently skipped; every "no change"
row states its reason. Re-derived rather than accepted:

| Row | Independent check | Result |
|---|---|---|
| D1 | `grep -c 'intentionally lightweight'` on the spec | **0** — discharged |
| D2 | the four guards named in `examples/fakeshop/apps/kanban/signals.py` | `_validate_done_card_has_spec` (143), `_validate_done_card_has_glossary_link` (148), `protect_done_card_spec` (404), `protect_done_card_glossary_link` (450) all exist — **leaving it was right**, see below |
| D3 | board fields render in `KANBAN.md` card 7 | Priority, Status, Relative size, Labels (`docs`, `internal`, `release`) all render at `KANBAN.md` lines 4779-4782 |
| D4 | `grep -c '^## Planning note'`; live `card.planning_note` | **0**; `''` |
| D5 | root README `##` headings; `CONTRIBUTING.md` `##` headings at HEAD | eight, none operational; all six named responsibilities resolve |
| D6 | `grep -c 'three-minute'` on the spec; the anchor's carrier | **0**; carrier live at spec line 19 |
| D7 | the bullet names the file that exists and claims a role, not contents | holds |
| D8 | `grep -rn '^#\+ Quick comparison' --include='*.md' .` | **0 heading matches** tree-wide; `grep -ci 'comparison table'` on the spec → **0** |
| D9 | `CHANGELOG.md` line 3 | "All notable changes to this project will be documented in this file" — the release-record role holds; the file itself untouched |
| D10 / D11 | `grep -n '^## Spec and build-plan filename pattern' docs/builder/BUILD.md` | **line 7** — the replacement citation resolves where the retired one did not |
| D12 | read the spec end to end | every surviving sentence true as a statement about now |
| D13 | `grep -c '^#### Other$' KANBAN.md`; migration | **0**; `0016_remove_other_section.py` present |
| D14 | `docs/TREE.md` line 3 | role claim holds — **normalizing only was right**, see below |

**D2 and D14 were deliberately left near-unchanged, and both calls are correct rather than oversights.**
D2's `Status:` line is not self-narration a reconciliation should cut: it describes an executable
constraint, and I confirmed all four guards exist in `signals.py` rather than taking the row's word for
it — the stub is the `SpecDoc` target those guards demand, and card 7's `spec.path` reads
`docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md`. Editing it would have removed a true
statement about a live mechanism. D14 is the one claim wholly true at HEAD; the generated provenance
that *would* have been new information belongs to `START.md` "Rendered docs — fix the source, not the
file", so restating it in the spec would have created exactly the borrowed-copy defect D11 was retired
for. Normalizing the wording and stopping is the correct disposition, and the alternative — adding
provenance — is the one this cycle's own record argues against.

All seven plan corrections carry a disposition. The five "honoured by omission" claims are verifiable
as absences and I confirmed each independently: no `231911a8` file-set claim, no `planning_note`
mechanism claim, no "three-minute" surface count, no sibling-size comparison or superlative, and no
table count entered either durable file. Corrections 3 and 4 are adopted and their effects are visible
on disk (the retirement rests on migration 0016; the two generated "three-minute" surfaces are
untouched).

### 3. Nothing was lost — spot-checked independently

I walked all eight `## Other` bullets from `git show HEAD:<spec>` rather than from either review, and
tested each "duplicate" disposition against the surviving text rather than accepting the label:

- The `Why it matters` row survives as spec line 25 — **a genuine recovery**, not a restatement.
- The five `Files likely touched` paths are each named in the surviving bullet that says what the
  document is for (lines 18, 19, 21, 22, 23). The disposition "duplicate" is therefore literally true:
  the file names survive, only the bare list is gone.
- The first `Note` row is duplicated in substance by the `## Scope` lead sentence plus the fold-in
  bullet — I checked both halves rather than the first.
- The spec-filename `Note` row is pointed rather than dropped, and the new citation resolves (BUILD.md
  line 7) where the retired one never did.

**The removed `## Card snapshot` board fields genuinely render in `KANBAN.md` card 7.** Read directly at
`KANBAN.md` lines 4779-4782: Priority `Medium`, Status `Done`, Relative size `S`, Labels `docs`,
`internal`, `release` — plus `#### Scope`, `#### Files likely touched`, `#### Why it matters` and
`#### Note`. Their removal from the spec is de-duplication against a live renderer, not a loss. Nothing
card 7 asserted has left the repository.

### 4. Mechanical re-verification, re-run rather than accepted

`docs/builder/BUILD.md` `## Claims are proven mechanically` applied to every claim, including the ones
Worker 3 had already proved.

**Counts.** Spec **57 lines / 2,983 bytes** — reproduces. Rationale was **625 / 42,260** at this pass's
open, also reproducing; after this pass's three edits it is **634 lines / 42,932 bytes** (`wc -lc`,
measured after the last edit). The spec's committed state at `947f7494` is **65 / 2,282**, a third
figure and the one M2 exists to keep distinct; the working-tree before-figure 62 lines reconciles
arithmetically against R1's `2 insertions / 5 deletions` (65 − 5 + 2 = 62), and the cumulative
`git diff --numstat` on the spec reads `20 28`, so 65 − 28 + 20 = 57. Both reconcile.

**Link definitions, resolved per file by absolute-path expansion with code spans stripped:** spec
**10 definitions / 10 unique uses**, rationale **15 / 15**; **zero unused and zero undefined in both**;
every target exists on disk, `[spec-006-rationale]` included (still untracked — R3 re-resolves it).
**10 canonical group headers present and in the required order in both files.**

**Depth trap re-resolved per file.** From `docs/SPECS/`: `../../README.md` normalizes to the
repository-root `README.md`, `../README.md` to `docs/README.md`. From `docs/SPECS/appx/`:
`../../../README.md` to the root `README.md`, `../../README.md` to `docs/README.md`. Both files'
`[root-readme]` and `[readme]` land where their names claim.

**`AGENTS.md` rule 27:** `grep -c` with the raw-line-ref regex returns **0** on both durable files.

**Glossary link text against the DB, not only the CSV.** Card 7's single `CardGlossaryTerm` has
`raw_text` `'optimizer behavior'` on term `` `DjangoOptimizerExtension` ``; the spec carries
`[optimizer behavior][glossary-djangooptimizerextension]` at line 19. **Byte-identical.** The anchor
resolves at `docs/GLOSSARY.md` line 712. The CSV was not touched by this pass.

**Live DB, read-only:** `card_id` `DONE-007-0.0.4`, status `done`, version `0.0.4`, priority `Medium`,
size `S`, labels `['docs', 'internal', 'release']`, `planning_note` `''`, `spec.path` the archived
path, **14 items** (`Scope` 6 / `Files likely touched` 5 / `Note` 2 / `Why it matters` 1), every one
`is_complete`. Nothing was written.

**Checkers, quoted verbatim as run after this pass's edits:**

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0
```

**Concurrent-commit check, not `git status` alone.** `git log` over this cycle's four paths returns
`1592bb90`, `e1f9ed26`, `81e4704d` — all long predating this cycle — and `git log -3` shows HEAD still
`947f7494` (2026-08-10). No commit landed during this cycle, so nothing it wrote was swept into one.

### 5. L4 and L5, closed here

Both were re-derived from primary sources before being touched, and both sit in the rationale, which
this role owns.

**L4 — closed.** `git show 231911a8:CONTRIBUTING.md | grep '^##'` returns **seven** headings: Getting
started, Running the test suite, Linting and formatting, Commit messages, Pull requests, Reporting
issues, Code of conduct. The sentence said the file "carried getting-started, test-suite, and linting
sections **only**". The load-bearing content was true — none of the operational responsibilities was
present — and the "only" was not. Rewritten to **"carried three of the six responsibilities this
bullet names — getting started, test suite, and linting — and none of the other three"**, both figures
measured: the bullet 21 lines above names setup, tests, formatting, versioning, build and publish
(**six**), of which the file carried three and lacked three. The following clause is corrected in the
same edit — versioning, build, publish and *a dependencies section* arrived at `b57eba38` (2026-05-16),
which I confirmed by reading `git show b57eba38:CONTRIBUTING.md`; dependencies is a fourth arrival and
is no longer implied to be one of the six. `2bd7cb84` is also 2026-05-16 and `231911a8` is 2026-05-08,
so "the same day as the root-README removal" and "eight days after the release" both hold.

**L5 — closed.** The sentence read "**Only** the after-figure is a working-tree measurement taken on
top of that commit **and the before-figure is too**", which contradicts itself. Rewritten to **"Neither
is the committed file at that commit: both are working-tree measurements taken on top of it, and the
committed figure `## How to read this file` carries is a third number again."** The stale qualifier is
retired rather than out-argued; the three numbers are the ones verified above (2,282 committed / 2,365
post-extraction / 2,983 now), and `## How to read this file` does carry 2,282 bytes, 65 lines at
rationale line 26.

**The third-instance check — and it found one, which I closed in the same pass.** The section holding
L5 opens "The reconciliation above was audited before it closed, and four of its statements were
corrected in place". My two edits would have made that count stale the moment they landed: this is the
cycle's defect class arriving by the exact route Worker 3 escalated — an enumeration extended a member
at a time until a later edit falsifies it. **I did not extend it to six.** The opening is scoped
instead — "that audit corrected four of its statements in place" — so the number now belongs to the
audit it names and cannot rot; and a closing paragraph records this pass's two corrections separately,
naming what each was and stating that neither touched the spec. That paragraph itself carries only
measured claims: seven `##` headings at `231911a8`, three of them the ones the clause names, two
corrections, zero spec edits.

Re-swept the new prose for the class after writing it. The absolute qualifiers I introduced are
"neither", "both", "none of the other three" and "three of the six" — each over a set I enumerated
this pass, none inherited. **No spec edit was made**, so `## Scope` bullet 2 and its glossary link were
not touched and the 1-anchor constraint was not exercised; `check_spec_glossary` is unchanged at
`OK: 1 terms`.

### 6. Spec changes made (Worker 1 only)

**None.** The spec is byte-identical at this pass's open and close (57 lines / 2,983 bytes both times),
and both findings this pass closed lived in the rationale. Recording over editing was the right call
here, as the dispatch prefers: nothing final verification found requires a contract change.

Three rationale edits, all in the reconciliation record this cycle appended, all corrections to *this
cycle's own record* in response to its audit — the same mechanism the two prior passes used and named
on disk, so the append-only rule stays auditable:

1. `### `## Scope` — six rendered rows became eight contract claims`, root-README bullet (closes
   **L4**) — the `231911a8` `CONTRIBUTING.md` clause scoped to the six responsibilities and the
   dependencies section separated from them.
2. `### What the audit of this record changed in it`, first bullet (closes **L5**) — the stale "Only"
   retired.
3. Same section, opening sentence and a new closing paragraph (prevents a third instance) — the
   four-statement count scoped to the audit that made it, and this pass's two corrections recorded
   separately rather than folded into the count.

### 7. Residual-item checklist audit

Every `- [x]` in the Plan's `### Residual-item checklist` was confirmed against the diff and the files,
not against the perform records. All seven substantive boxes hold. The two process boxes are now
discharged and ticked here:

- `- [x] Worker 3 audit` — two review passes on disk, the second `review-accepted` with an explicit
  convergence judgement.
- `- [x] Worker 1 final verification` — this section.

No box is over-ticked, none is silently un-ticked, and nothing is deferred out of this item.

### 8. What R3 inherits

`### Notes for Worker 1 (spec reconciliation)` is on disk in all three of this artifact's passes and in
six instances in `docs/builder/bld-007-r1-rationale_move.md`; I re-read the cumulative list and it is
accurate **minus L4 and L5, which are now closed and must not be re-opened**. Still standing for R3:

- `CONTRIBUTING.md`'s dangling `docs/builder/BUILD.md` "Spec filename pattern" citation — re-confirmed
  live at `CONTRIBUTING.md` line 11. Outside the writable set; a deferred-work-catalog item.
- The root README's map is eight bullets, not a table.
- `[spec-006-rationale]`'s target exists on disk and is **still untracked** — R3 re-resolves it and, if
  the sibling cycle has not landed it, retires the definition and its use site in one edit.
- The five deleted `docs/review/rev-*.md` remain **escalated and unresolved**.
- `SpecDoc.path` / terms-CSV / `import_spec_terms` chain — re-run green this pass, so R3 inherits a
  verified-not-assumed baseline rather than an assumption.

**What R2 changed that R3 must now re-check:**

1. **The retired `[backlog]` definition affects one cross-reference direction.** It was the spec's only
   link to `BACKLOG.md` and it is gone, so R3's outbound sweep will find spec-007 pointing at
   `BACKLOG.md` nowhere. That is intended — the definition had no use site since the file was created —
   but R3 must not read the absence as rot. Note that the **rationale** still defines and uses
   `[backlog]`, so the spec-007 pair as a whole has not stopped referencing `BACKLOG.md`.
2. **Seven definitions are new in the spec** (`[changelog]`, `[contributing]`, `[root-readme]`,
   `[glossary]`, `[readme]`, `[tree]`, `[build]`). R3's outbound direction is therefore materially
   larger than at pre-flight; all seven resolve today, verified above.
3. **`## Other` is gone as a heading.** Any inbound reference to `#other` would now dangle; the only one
   that existed was the rationale's own `[spec-007-other]`, already retired. R3 re-sweeps for others.
4. **The staged-anchor sweep now has three self-hits.** `grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|
   STABLE)-007' .` returns **3** matches at HEAD, all inside
   `docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md` (lines 34, 244, 280) — the plan
   describing the sweep, not staged work. The plan's pre-flight "zero hits anywhere" was measured before
   those sentences existed. **R3 must exclude the cycle's own plan and artifacts from the sweep and say
   so**, or it will report a false positive; the shipped source/test/example trees are clean.

### 9. The cycle-level lesson, for Worker 0's closeout

**Name of the class: an unmeasured quantifier in durable prose — a number, a count, or an absolute word
("only", "every", "all", "smallest") written in the same sentence as the argument it supports, rather
than measured in its own command first.** Five review rounds across R1 and R2 for a 57-line spec, and
every one of the nine instances is this: a false superlative (spec-007 "the smallest spec"), a table
count, a surface count, an entry count, a definition count, a hash whose *tree state* was not the state
measured, "every other document", a three-of-four taxonomy, and finally L4's "only". The class migrated
from numbers to universals precisely **because** the discipline that caught numbers was numeric: the
passes learned to re-measure figures and never extended the habit to words that quantify.

**What would have prevented it, and it is one rule rather than more process:** *a quantifier is a
measurement, so it is written only by the command that produced it.* The failure is never ignorance of
the fact — in seven of the nine instances the correct value was already recorded, correctly, elsewhere
in the same pass's own artifact. It is that prose gets written from a mental model and verified
afterwards, and "I checked it after" is indistinguishable at read time from "I measured it as I wrote
it". The corollary this cycle earned twice: **a completeness claim written by a pass that is still
making changes is stale before it lands** — scope it to the pass that owns it ("that audit corrected
four") rather than extending its enumeration, which is how a count survives the next edit instead of
inviting one more member.

Also worth carrying: **five rounds on a 57-line file is not over-review, it is the cost of a spec whose
every sentence is a claim about another file's current state.** Each round found a real defect and the
last two were the smallest. The lesson is not to review less; it is that the drift table should carry
the *quantifiers* each row's fix will need, so the pass that writes them has the measurements in hand.

### Working-tree churn and growth

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` reads **26 entries** at the
open and at the close of this pass — the 25 baseline-dirty paths plus this artifact — matching both
prior sections byte-for-byte. **No growth this pass and no new path**, so Worker 0 has nothing to
append to `## Baseline-dirty out-of-scope files`. The rationale file was already `??` from R1 and the
spec already `M`; the namespaced memory file is gitignored and never appears in the count.

The five `docs/review/rev-*.md` deletions remain **escalated and unresolved** — still tracked at HEAD,
still absent from disk, not restored, not reverted, not touched. `docs/review/review-0_0_14.md` and
`docs/review/rev-_boundary_ordering.md` were not touched. The concurrent spec-002 and spec-006 cycles'
paths and the third session's four package-source and test files were **not read for content, not
touched, not reverted, not staged**.

### Final status

`final-accepted`. R2's contract is delivered: the spec matches what exists, later corrections are
reflected in it, every explanation lives in the rationale, and it reads as a clean current contract
with no chronology to apply. All fourteen drift rows and all seven plan corrections are dispositioned
with none silently skipped; D2 and D14 were left near-unchanged and both calls verify as correct.
Nothing was lost — the eight retired `## Other` bullets and the removed board fields were traced
independently. The mechanical state re-verified in full. L4 and L5 are closed in the rationale, a third
instance of their class was caught and prevented in the same pass, and the spec required no edit.

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
