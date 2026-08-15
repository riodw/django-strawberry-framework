# Build: R1 — Spec rationale extraction (spec-007)

Spec reference: `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` (whole file, 65 lines before this pass)
Plan reference: `docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md` (item R1, `### What R1 inherits`, `### The 1-anchor constraint`)
Status: final-accepted
Superseded figures: see `### Corrections to this artifact's own prior sections` (pass 2),
`### Corrections to prior sections (pass 3)`, and `### Correction to pass 3 (this pass)` inside
`## Review (Worker 3, pass 3)` — three figures and one symbol in earlier sections are knowingly wrong
and `ARTIFACT.md` forbids editing them in place.

Per the plan's **Deviation 2**, R1 has no Worker 2 pass: Worker 1 plans **and** performs, sets
`Status: planned`, and Worker 0 reads `planned` on this artifact as "dispatch Worker 3 for the audit".
This artifact therefore carries a `## Perform record (Worker 1)` where a slice artifact would carry
`## Build report (Worker 2)`, in the same position and with the same subsections.

---

## Plan (Worker 1)

### Spec status-line re-verification (every Worker 1 spawn)

Read spec lines 1-5 before anything else. Findings:

- Line 1 title, line 3 target release, line 5 owner — all accurate; `Card.objects.get(number=7)` returns
  `card_id DONE-007-0.0.4`, `target_version.number 0.0.4`, title `0.0.4 onboarding docs and spec consolidation`.
- Line 4 `Status:` — **accurate and load-bearing, not stale.** It says the stub exists to keep the Kanban
  one-to-one spec invariant intact, and the invariant is executable:
  `examples/fakeshop/apps/kanban/signals.py::_validate_done_card_has_spec` and
  `::_validate_done_card_has_glossary_link` refuse to save a `done` card without a linked `SpecDoc` and
  at least one glossary link, and `::protect_done_card_spec` / `::protect_done_card_glossary` refuse to
  move or delete either off a done card. **No status-line edit was needed or made this pass.** Recorded
  because the sentence reads like self-narration a later pass would cut (this is the plan's drift row D2,
  re-verified as holding).

### DRY analysis

**Helper inventory checked.** Not applicable in the code sense and stated rather than skipped: this pass
writes no `.py` file, adds no helper, constant, validation branch, or test helper, and touches no file
under `django_strawberry_framework/`. The package-wide AST inventory would answer a question this pass
does not ask. The DRY question that *does* apply here is the documentation one, and it is the reason for
one of the two moved passages:

- **Existing patterns reused.** The rationale file's shape is taken from
  `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` (read for shape only; it is the
  concurrently-running cycle's output and was not edited) and
  `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`: title line naming the three
  contents, a companion-pointer paragraph, `## How to read this file`, `## Provenance of this record`
  with an exhaustive moved/left/deleted accounting, `## Entries keyed to the spec` keyed by heading and
  anchor, a closing standing note, and the 10-header link block. The spec-side pointer sentence copies
  the sibling convention exactly (`spec-005` line 3, `spec-006` line 3).
- **New shared shape justified.** None. One new file, no new convention.
- **Duplication risk avoided, and one duplication retired.** The moved preamble's first two sentences
  ("This file is intentionally lightweight… so the card has a durable `SpecDoc` FK target") restate what
  the spec's own `Status:` line already says. That is a concrete claim in two places in one file, which
  `## The single-ownership law` clause 1 makes a defect; the `Status:` line is the owner and the preamble
  is the borrower, so the identity survives the move one level up. The opposite risk — the rationale
  restating contract the spec still carries — is managed by `## Provenance of this record` listing the
  left-in-spec set exhaustively, and by every entry recording *what the spec claims* rather than
  restating the claim as fact.

### Boundary count

Zero. This pass introduces no guard, cap, rejection path, or validation branch, in production code or
anywhere else — it moves prose between two Markdown files. No split question arises; recorded because
`worker-1.md` `### Boundary count is a split trigger` wants the count written down, not inferred.

### Hot-path declaration

None, inherited from the plan preamble unchanged. No residual item changes package source, so nothing
here runs per request, per resolver, per row, per connection, or per outbound message.

### Floor-verification scope

None, inherited from the plan preamble unchanged. This pass touches no Django / Strawberry / channels
integration seam. The silence is deliberate: no floor venv is owed by this pass or by the final gate on
its behalf.

### Implementation steps

1. Verify the two move candidates the plan names against the file, and verify each of the plan's fourteen
   drift rows against source, the kanban DB, or `git show` — never against the table.
2. Create `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` with the
   sibling shape, the exhaustive moved/left accounting, and one entry per spec section carrying the
   alternatives rejected, the changes with their causes, and the claims no longer made.
3. Cut the two moved passages out of the spec: the preamble paragraph and the whole `## Planning note`
   section (heading and body).
4. Leave the rule-1 pointer in the spec — one line naming what was moved and where — plus its link
   definition under `<!-- docs/SPECS/ -->`.
5. Verify: `check_spec_glossary.py` still exits 0; `check_trailing_commas.py --check` exits 0 on both
   files; every rationale link definition resolves on disk and lands on the file it means; the three
   surviving `##` anchors the rationale links to still exist; no raw `path:NN` in either file.
6. Record byte counts before and after for both files, the correction list for R2/R3, and the
   baseline-dirty growth.

### Test additions / updates

None, and none are possible: this pass writes no code and no test. The mechanical checks in step 5 are
this item's substitute and their verbatim results are in `### Validation run`. No temp test is
appropriate, so nothing is left under `docs/builder/temp-tests/` for Worker 3.

### Implementation discretion items

Assessed and decided as belonging to the next pass rather than to this one:

- **How each falsified claim should read in the spec.** R2's, by the plan's own statement that a
  prescribed correction is deliberately absent from the drift table. This pass records what the spec
  claims and how each claim fared; it restates nothing.
- **Whether `## Card snapshot`, `## Other`, and the present-tense framing survive as sections at all.**
  R2's. The rationale records the case against each (a hand-maintained DB render that nothing
  re-renders; a heading naming a retired card section) without acting on it.

### Residual-item checklist (plan item R1, verbatim)

The spec has no `## Slice checklist`, so the boxes are the plan's R1 line decomposed. Because R1 has no
Worker 2 pass (Deviation 2), Worker 1 ticks a box in this same pass where the contract landed, under the
identical discipline: tick only what actually landed, leave anything deferred `- [ ]` with the deferral
stated. Worker 3 walks the list; Worker 1 re-audits every tick at final verification.

- [x] R1: Spec rationale extraction into `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`
- [x] Worker 1 performs the move — the deliberative layer is cut from the spec, not copied
- [x] Worker 1 authors the record — every entry names the spec section by heading and anchor, and carries the alternatives rejected with why each lost, every change the claim has undergone with its cause, and any claim the spec may no longer make
- [x] Each of the plan's fourteen drift rows re-verified against source / the kanban DB / `git show` rather than trusted, and any row found wrong recorded
- [x] The 1-anchor constraint held: `check_spec_glossary.py` re-run and quoted verbatim
- [x] Before/after byte counts recorded for both files
- [x] The reference-style scaffold in the new file carries all 10 canonical group headers, and every path is disk-exists-checked against *which* file it resolves to
- [x] Worker 3 audit (`review-accepted` | `revision-needed`) — not this pass; Worker 0 dispatches it off `planned`
- [x] Worker 1 final verification (`final-accepted`) — not this pass

---

## Perform record (Worker 1)

### Files touched

- `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` — **created.** The
  deliberative companion: two moved passages, one entry per spec section, and the falsification record
  for every claim, each with the commit or board change that caused it.
- `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` — **two removals and one pointer.**
  Removed the preamble paragraph (old line 7) and the whole `## Planning note` section (old lines 18-20);
  added the one-line rationale pointer in the preamble's position and its `[spec-007-rationale]`
  definition under `<!-- docs/SPECS/ -->`. Nothing else in the file changed — no `## Scope` bullet, no
  `## Other` bullet, no `## Card snapshot` row, no header line.
- `docs/builder/bld-007-r1-rationale_move.md` — this artifact, created.
- `docs/builder/worker-memory/spec-007-worker-1.md` — memory entry appended (gitignored).

### What moved, and what stayed

**Moved (cut from the spec; exists only in the rationale now) — two passages, and that is the whole move:**

1. The preamble paragraph, all three sentences: "This file is intentionally lightweight. It preserves the
   card scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable
   repository file. Before implementation work starts from this file, expand it into the full
   builder-format spec described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`."
2. The whole `## Planning note` section — heading plus its one-word body, `shipped`.

**This is a correct move, not a thin one, and the file is not padded to disguise its size.** Spec-007 is
the smallest spec in the repository (2,282 bytes / 65 lines / zero fenced blocks) and it was never
deliberated: it is a rendered card snapshot. Exactly two passages were deliberation rather than contract
or status, and both are above. No rejected alternative is invented anywhere in the new file; where a
change has no recorded reasoning the entry names the commit and stops, and the one place the file argues
(why the stub shape is right) is explicitly labelled as this pass's argument against constraints
verifiable at HEAD rather than as a recovered discussion.

**Nothing was deleted outright.** `worker-1.md` rule 2 deletes rather than moves prose the current
decisions have falsified, and the preamble's third sentence is falsified. It is quoted in the rationale
**inside an entry that states it is falsified** — the record clause "any claim the spec once made and may
no longer make" — and is not reproduced anywhere as live instruction. Its removal from the spec is
unconditional.

**Stayed, deliberately, and the list is exhaustive:** the title / target-release / owner lines; the
`Status:` line; all six `## Card snapshot` rows; all six `## Scope` bullets; all seven `## Other` bullets;
the link-definition block. Every one is contract-shaped or a **status claim**, and a status claim moved
into a rationale file is neither a legitimate entry there nor the deletion the move prescribes for
falsified prose — its disposition against HEAD is R2's call. Same line the spec-006 extraction pass drew.

**Byte counts:**

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` | 2,282 bytes / 65 lines | 2,365 bytes / 62 lines | **+83 bytes**, -3 lines |
| `docs/SPECS/appx/spec-007-…-rationale.md` | 0 (absent) | 28,592 bytes / 444 lines | +28,592 |

The spec **grew by 83 bytes** while losing three lines, and that is reported rather than shaved. The two
moved passages are ~356 bytes; the rule-1 pointer sentence and its link definition are ~439. The sibling
convention is a pointer that names what was moved and where (`spec-005` line 3 and `spec-006` line 3 are
both a full sentence of comparable length), and rule 1's purpose — a reviewer who cannot see that
deliberation exists will re-litigate a settled alternative — is not served by a shorter one. No
byte-ratchet applies to specs; the corpus ratchet in `BUILD.md` binds only `BUILD.md`, `ARTIFACT.md`, and
the four role files, none of which this pass touches.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md`
  → verbatim: `OK: 1 terms - all have glossary entries and at least one spec link.` — exit `0`.
  **The 1-anchor constraint held trivially, and by construction rather than by care:** the sole carrier
  `[optimizer behavior][glossary-djangooptimizerextension]` sits in `## Scope` bullet 2, which this pass
  did not touch at all. The constraint is live for R2, which rewrites that bullet; it was not live here.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`
  → no output, exit `0`. Link-definition scaffold and the 10 canonical group headers intact in both files.
- Rationale link block: **16 definitions, all 16 resolve on disk**, checked by resolving each path from
  `docs/SPECS/appx/` and printing the repo-relative target. The depth trap the plan names is handled and
  verified rather than assumed: `[root-readme]: ../../../README.md` resolves to `README.md` and
  `[readme]: ../../README.md` resolves to `docs/README.md` — two different files, both existing, each
  used for the claim that is actually about it. Group headers emitted in the canonical order
  `Root, docs/, docs/SPECS/, docs/builder/, django_strawberry_framework/, tests/, examples/, scripts/, .venv/, External`.
- Spec's new definition: `appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` resolves
  from `docs/SPECS/` to the created file. Exists.
- Cross-file anchors the rationale links to: `grep -n '^## '` on the spec returns `## Card snapshot`,
  `## Scope`, `## Other` — all three slugs (`#card-snapshot`, `#scope`, `#other`) resolve. `## Planning
  note` is deliberately gone, so no entry links to it: the two entries whose sections the move removed
  anchor `## Card snapshot` and say so, per the spec-006 precedent.
- `grep -c '^```'` on the spec → `0` before and `0` after. No fenced block was involved.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` → no match in either the spec or the rationale.
  `AGENTS.md` rule 27 compliance preserved in the spec and established in the new file; the only raw
  `path:NN`-shaped references in this cycle are inside this artifact, where they are permitted.
- `uv run ruff format` / `ruff check --fix` — **not run, and correctly not run.** This pass touched no
  `.py` file.
- `git status --short` after the writes — see `### Working-tree churn and baseline growth`. Every file
  this pass modified appears in `### Files touched`; nothing else is attributable to it.

### Failability proofs

`None; this pass introduced no new boundary.` It moves prose between two Markdown files and adds no
guard, gate, or rejection path. The mechanical checks in `### Validation run` are not failability proofs
and are not offered as substitutes for one.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Not applicable; plan declares floor-verification scope none.`

### Implementation notes

- **The pointer sits where the preamble was**, after the header block rather than at line 3. `spec-005`
  and `spec-006` put theirs at line 3 because those files open with a title and then body prose;
  spec-007 opens with a three-line target/status/owner block, and splitting it to insert a pointer would
  read worse than occupying the paragraph slot the move vacated.
- **The pointer names three things, not one.** Rule 1 asks for a one-line pointer naming what was moved
  and where; the third clause ("every claim … that this spec once made and may no longer make") is there
  because the spec is **not yet reconciled** at the end of this pass, and a reader of the spec between R1
  and R2 needs to know its `## Scope` is a 2026-05-08 snapshot. It is one line.
- **The rationale records the fourteen falsifications as entries keyed to spec sections, not as a
  fourteen-row table.** The record clause requires each entry to name the section it belongs to by
  heading and anchor, and a drift table cannot be looked up from a section. Several plan rows also key to
  the same spec bullet or split across two, so the mapping is not one-to-one: rows D7 and D8 are one
  entry (`## Scope` 3), and rows D11, D12, and D13 are one entry (`## Other`).
- **`## Card snapshot` was left whole even though its label row is wrong.** Patching `docs`, `release` to
  `docs`, `internal`, `release` would be a reconciliation edit, and it would also be the wrong fix — the
  rationale records the case that the hand-maintained-DB-render *section* is the defect, and R2 decides.

### Notes for Worker 3

- **What to audit hardest is the over-cut question, and there is one judgement call in it.** The preamble
  is a single paragraph whose first two sentences are duplicate-of-`Status:` and whose third is falsified
  instruction. It moved as one unit. An auditor with no memory of this pass should ask whether cutting
  all three at once discharged plan drift row **D1** inside R1 rather than leaving it to R2 — it did, and
  the plan's `### What R1 inherits` names the paragraph as an R1 move candidate, so this is sanctioned
  rather than scope creep. But it means **D1 needs no R2 action**, only R2 verification.
- **Read `## Provenance of this record` in the new file against the spec's diff.** It claims the
  moved/left/deleted accounting is exhaustive. That claim is auditable: `git diff -- docs/SPECS/spec-007-…md`
  shows exactly three removed non-empty lines (the preamble, `## Planning note`, `shipped`) and two added
  (the pointer, its definition).
- **No temp test, no shadow file, no mutation.** Nothing was left in the tree by this pass beyond the
  files listed. `docs/shadow/` was not written to.
- **The rationale's one argumentative passage is labelled.** The stub-shape entry supplies reasoning this
  pass authored. It is bracketed as "this pass's argument, not a recovered debate" and every constraint
  it rests on is checkable at HEAD (the four `signals.py` guards; the seven-stub population; the
  creation-after-release chronology). If the label reads as insufficient, that is a finding worth making.

### Notes for Worker 1 (spec reconciliation)

Written here on disk rather than only in the return report, per `BUILD.md` `### Cohorting, naming, and
closure`.

**Five corrections to the plan's verified facts, each measured this pass.** The plan's own instruction is
that R2 re-verifies rather than trusting the table; these are the rows where trusting it would have
produced a wrong spec edit or a wrong rationale entry. The rationale file already carries the corrected
version of each; the corrections themselves are recorded here because naming a build plan is process
provenance that does not belong in a durable doc.

1. **The release commit is not the card's work, and it did not touch five Markdown files.** The plan
   states twice — `### Residual scope` and `### The read-only correctness audit — findings` — that
   "`git show --stat 231911a8` and the card's `Files likely touched` rows agree: five Markdown files and
   nothing else." Measured: `231911a8` touches **`CHANGELOG.md` and `KANBAN.md` only** (2 files, 102
   insertions / 76 deletions). It is the version cut. The card's actual work is three commits three days
   earlier: `4b8dce07` (created `docs/FEATURES.md`, cut `docs/README.md` to code-first), `83c25963`
   (condensed `CHANGELOG.md`, **deleted six completed spec files**), `3a4d40b7` (finished). The audit's
   *conclusion* — no package source in the card's scope — survives: none of the three commits touches a
   package module or test except incidental optimizer/registry work in `83c25963` that belongs to other
   cards. But R3's archive audit should not re-derive the file set from `231911a8`.
2. **Drift row D4's mechanism is wrong.** `## Planning note` does not render the retired `PlanningState`
   dimension. `1592bb90` dropped `PlanningState` and `Card.planning_state` while **explicitly retaining
   `Card.planning_note`**, the free-text field this section renders, and the same commit already scrubbed
   the `Severity:` and `Planning state: Shipped` lines out of this spec's `## Card snapshot`. What is
   stale is the retained field's *value*: card 7's note went `"shipped"` → `""` in `1592bb90` itself
   (measured in the `KANBAN.html` payload at `1592bb90~1` versus `1592bb90`). The section is stale, so
   the row's disposition is unaffected — but "the model behind it is gone" is false and would mislead the
   other six stubs' residual cycles.
3. **Drift row D13's mechanism and attribution are wrong, and this is the substantive one.** The plan
   says `## Other` "flattens four distinct card sections into one undifferentiated list" and attributes
   it to "the stub renderer". Measured from the `KANBAN.html` payload: at `81e4704d`, the commit that
   created this spec, card 7's items sat in exactly **two** sections, `Scope` and `Other`. Nothing was
   flattened — the render was faithful. The four-way taxonomy arrived seven weeks later, on 2026-07-20,
   in a board-wide migration: `0c08204f` reclassified 378 `other` items, `ac7cc6a4` emptied the section,
   `4f68d3f2` deleted its lookup row (migration 0016). `grep -c '^#### Other$' KANBAN.md` → `0`. So the
   correct finding is stronger than the plan's: **the spec's `## Other` heading names a card section that
   no longer exists in the database at all**, and its bullets are the pre-reclassification shape frozen
   in place. R2 should reconcile against that, not against a renderer defect that never happened.
4. **Drift row D6's occurrence count is one short.** "three-minute" occurs on **three** surfaces, not
   two: this spec, `KANBAN.md`, and the same card row inside the `KANBAN.html` payload
   (`grep -c 'three-minute' KANBAN.html` → 1). Both KANBAN files are generated from the one `CardItem`,
   so the conclusion (a correct historical record, not drift to fix) is unchanged, and R3's
   three-direction sweep should expect the third hit rather than treat it as new drift.
5. **The stub population is seven, not three.** `### What R1 inherits` cites specs 011 / 012 / 013 as the
   precedent. `grep -rl 'This file is intentionally lightweight' docs/SPECS/*.md` returns **seven**: 007
   (2,282 bytes), 011 (1,797), 012 (1,651), 013 (1,669), **016 (4,558)**, **024 (1,618)**,
   **026 (3,593)**. All seven also carry a `## Planning note` section. This strengthens rather than
   weakens the plan's point — the stub is a deliberate pattern, not an oversight — and it means the two
   passages this pass moved exist in six other archived specs whose own residual cycles will meet them.

**Routed to R2 (spec reconciliation), beyond the fourteen rows it already owns:**

- **D1 is discharged, not deferred.** The falsified "expand it into the full builder-format spec"
  instruction left the spec in this pass. R2 verifies its absence rather than reconciling it.
- **The finding the drift table does not have.** `## Scope` bullet 6's policy — "completed design-doc
  content is folded into durable docs" — meant **deletion** when the card shipped (`83c25963` deleted six
  spec files, 2,495 lines) and the deletion was **reversed by `81e4704d`, the very commit that created
  this spec file**, which re-established all six under `docs/SPECS/` as byte-verified restorations
  (`docs/spec-django_types.md` 50,075 bytes → `docs/SPECS/spec-001-django_types-0_0_1.md` 50,195 bytes,
  the diff being self-referential filename updates only). The plan's D10 reads the bullet as "true in
  substance and under-described"; it is more than that — the bullet's two halves were in tension and the
  repository resolved it against the first one. The rationale carries the full entry; R2 decides what the
  bullet says now.
- **The role/inventory split is the reconciliation's most useful input**, and it is measured rather than
  asserted: of six `## Scope` bullets, the two that claim a document's *role* hold unchanged at HEAD
  (bullet 4 wholly, bullet 1's first half) and **every** bullet claiming a document's *contents* failed.
  The rationale's `## Standing note` records this. It is also the answer to the plan's own
  `**The scope trap specific to this spec**`: reconciling toward roles is durable, reconciling toward a
  current inventory guarantees this cycle runs again.

**Routed to R3 (documentation and archive audit):**

- `CONTRIBUTING.md` line 11 carries the **same dangling `docs/builder/BUILD.md` "Spec filename pattern"
  citation** as the spec's final `## Other` bullet. `BUILD.md`'s heading is
  `## Spec and build-plan filename pattern`. `CONTRIBUTING.md` is outside this cycle's writable set, so
  this is a maintainer follow-up for the deferred-work catalog, not an edit — but it is a *fourth*
  surface the plan's `### Every reference TO spec-007` table does not list, and it means retiring the
  spec's borrowed copy does not retire the dangling citation from the repository.
- The `## Project documentation` map in the root `README.md` is **eight bullets, not a table**, and all
  eight resolve. The plan says "eight rows"; the shape matters only if R3 greps for table syntax.
- The staged-anchor sweep and `import_spec_terms --check` were **not** re-run by this pass; they are R3's
  and this pass's writes cannot have affected either (no DB write, no `TODO(` anchor added — verified:
  the new rationale file contains no `TODO(`).

### Working-tree churn and baseline growth

Reported, never reverted (`AGENTS.md` rule 34). `git status --short` after this pass:

```text
 M KANBAN.html
 M KANBAN.md
 M docs/SPECS/spec-006-public_surface-0_0_3.md
 M docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
 D docs/review/rev-_cross_web_patches.md
 D docs/review/rev-_django_patches.md
 D docs/review/rev-_strawberry_patches.md
 D docs/review/rev-apps.md
 D docs/review/rev-conf.md
 M examples/fakeshop/db.sqlite3
?? docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md
?? docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
?? docs/builder/bld-006-r1-rationale_move.md
?? docs/builder/bld-007-r1-rationale_move.md
?? docs/builder/build-006-public_surface-0_0_3.md
?? docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md
```

**Attributable to this pass:** `docs/SPECS/spec-007-…md` (M) and
`docs/SPECS/appx/spec-007-…-rationale.md` (??). Nothing else.

**The baseline-dirty list has GROWN by three entries**, all belonging to the concurrently running
spec-006 residual cycle, which has evidently completed its own R1 since this cycle's pre-flight:

- `docs/SPECS/spec-006-public_surface-0_0_3.md` (`M`) — that cycle's R1 spec edit.
- `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` (`??`) — its new rationale file. **Read
  read-only by this pass as the closest sibling for shape**, per the plan's instruction to read the
  nearest sibling for shape and not content. Not edited.
- `docs/builder/bld-006-r1-rationale_move.md` (`??`) — that cycle's R1 artifact. Not read, not edited.

`docs/builder/build-007-…md` (`??`) is this cycle's own plan, expected and untracked; Worker 0 owns it.
Worker 0 should append the new entries to the plan's `## Baseline-dirty out-of-scope files` — a worker
does not edit the plan.

**ESCALATION — every tracked `docs/review/rev-*.md` file was deleted from the working tree during this
pass, and `AGENTS.md` rule 22 names those files as committed source of truth.** They were present at the
start of the pass and absent at the end; this pass never touched `docs/review/` and does not own it.
Measured: `git ls-tree -r --name-only HEAD docs/review/ | grep -c 'rev-'` → **5** tracked at HEAD;
`ls docs/review/ | grep -c 'rev-'` → **0** on disk. All five are gone —
`rev-_cross_web_patches.md`, `rev-_django_patches.md`, `rev-_strawberry_patches.md`, `rev-apps.md`,
`rev-conf.md`. `REVIEW.md`, the five `review-0_0_*.md` files, and the three `worker-*.md` files are
untouched, so this is exactly the `rev-*` set and nothing else.

**Not reverted, deliberately, and the reason is a rule collision worth stating.** Rule 22's prescribed
restore is `git checkout HEAD -- docs/review/` — the one command this cycle's dispatch contract and
`BUILD.md` `## Claims are proven mechanically, never accepted on prose` ban outright, because a
concurrent session is writing this tree and a `git checkout` there can destroy uncommitted work. Rule 34
independently forbids auto-reverting a file that changed without this pass's edits. So the deletion is
reported and left in place. **Only the maintainer can decide whether this is a closing REVIEW cycle's
authorized cleanup or a rule-22 violation by a concurrent session**, and only the maintainer can restore
it safely. Worker 0 should escalate rather than route this to a residual item: it is outside this cycle's
writable set in every direction.

**HEAD is unchanged at `947f7494`**, re-derived this pass rather than trusted from the plan. No commit
landed during it, so this pass's two files could not have been swept into a concurrent commit.

---

## Review (Worker 3)

Audit of item R1 against `BUILD.md` `## Spec rationale extraction`, `## Claims are proven mechanically,
never accepted on prose`, `AGENTS.md` rules 22 / 26 / 27 / 34, `START.md` "Markdown link convention", and
the plan's `### What R1 inherits` / `### The 1-anchor constraint`.

**Diff re-derived, not trusted.** `git rev-parse HEAD` → `947f74948c16b20b0c15ff359bb53fbe462d4b8c`,
matching the artifact's re-derivation. Before-state obtained read-only via
`git show HEAD:docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` into a scratch path
**outside** the repo, then `diff`. No `git stash` / `checkout` / `restore` / `worktree` was used for any
purpose in this pass.

### High:

None.

### Medium:

#### `## Other` carries EIGHT bullets, not seven — and the count is wrong inside the exhaustiveness claim

`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`
`## Provenance of this record` #"all seven `## Other` bullets" (line 62), and
`### `## Other` — a heading that names a card section the board has retired` #"its seven bullets are the
pre-reclassification shape" (line 352).

Re-derived mechanically rather than accepted. Bullet count per spec section, parsed from the file on disk:

```text
  6  ## Card snapshot
  6  ## Scope
  8  ## Other
```

And from the live kanban DB, read-only:

```text
sections: Counter({'scope': 6, 'files_touched': 5, 'note': 2, 'why_it_matters': 1})
```

Six `Scope` rows render as `## Scope`; the remaining **eight** render as `## Other` (1 `Why it matters` +
5 `Files likely touched` + **2** `Note`). The rationale's breakdown reads "one `Why it matters` row, five
`Files likely touched` rows …, and one `Note`" — it drops one `Note` row, and therefore states seven.

Why it matters, and why it is Medium rather than Low: the number sits **inside the sentence that claims the
left-in-spec accounting is exhaustive** ("Deliberately left in the spec by this pass, and the list is
exhaustive: … all seven `## Other` bullets"). An exhaustive-accounting clause whose own count is short by
one is the failure mode `## Claims are proven mechanically` exists for, and this is a **durable** file, not
a per-cycle artifact. It is also a *new* error rather than a propagated one: the plan states the correct
figure twice — `## Worker-0-verified facts` #"`Note` ×2" and #"a lossy merge of the other eight" — so this
pass corrected five plan rows while introducing a sixth discrepancy in the opposite direction. The same
seven appears in this artifact's `### What moved, and what stayed`.

Recommended change: eight, and "two `Note` rows" in the breakdown, in both places in the rationale and in
this artifact's `### What moved, and what stayed`. No other prose is affected — the entry's substantive
finding (the `## Other` heading names a card section the DB has retired) is independently verified and
stands.

#### The spec-001 byte figure is asserted in the present tense and is false at HEAD by 5,599 bytes

`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`
`### `## Scope` 6 — the fold-in policy, reversed by the commit that created this file`
#"is 50,195 bytes" (line 318).

The sentence reads: "`docs/spec-django_types.md` was 50,075 bytes when deleted and
`docs/SPECS/spec-001-django_types-0_0_1.md` **is** 50,195 bytes, the difference being self-referential
filename updates and nothing else."

Re-derived:

```text
git show 83c25963^:docs/spec-django_types.md | wc -c   ->  50075   (deleted size: correct)
git show 81e4704d:docs/SPECS/spec-001-django_types-0_0_1.md | wc -c ->  50195   (at the restoring commit)
git show HEAD:docs/SPECS/spec-001-django_types-0_0_1.md   | wc -c ->  44596   (HEAD)
```

So the pair 50,075 → 50,195 is a correct measurement **at `81e4704d`**, which is exactly the measurement
the argument needs (the restoration was a restoration, not new writing — that holds, and the entry's
conclusion is sound). But the copula is present tense, and the file is 44,596 bytes at HEAD. A reader who
re-derives the number the obvious way gets a mismatch and has no way to tell whether the argument or the
arithmetic is wrong.

This is Medium and not Low because of where it sits: the whole thesis of this rationale — its
`## Standing note` — is that **present-tense claims about a document's contents rot while role claims
hold**. A durable file making that argument may not itself carry an unqualified present-tense byte count.

Recommended change: attribute the second figure to its commit — "…and `spec-001-django_types-0_0_1.md`
was 50,195 bytes when `81e4704d` created it". Two words; no restructuring.

### Low:

#### Dangling symbol reference: `signals.py::protect_done_card_glossary` does not exist

`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`
`### The preamble …` #"`signals.py::protect_done_card_glossary`" (line 119).

The four symbol-qualified references in the file were checked against source. Three resolve:

```text
examples/fakeshop/apps/kanban/signals.py:143:def _validate_done_card_has_spec(
examples/fakeshop/apps/kanban/signals.py:148:def _validate_done_card_has_glossary_link(
examples/fakeshop/apps/kanban/signals.py:404:def protect_done_card_spec(
examples/fakeshop/apps/kanban/signals.py:450:def protect_done_card_glossary_link(   <-- actual name
```

`grep -rn 'protect_done_card_glossary' signals.py` returns only the `_link` symbol and its `dispatch_uid`.
`AGENTS.md` rule 27 makes the symbol path the reference form precisely so it can be grepped; a symbol that
does not exist is a dangling citation in a durable doc, and the guard it names IS load-bearing to the
entry's "delete the file" rejection. Same string appears in this artifact's
`### Spec status-line re-verification`. Fix: `protect_done_card_glossary_link` in both.

#### `docs/GLOSSARY.md` has one markdown table, not two

`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`
`### `## Scope` 3 …` #"the file's two tables are `## Index` and `## Browse by category`" (line 253).

Re-derived by scanning `docs/GLOSSARY.md` for table separator rows (`^\|[\s:|-]+\|$`) and attributing each
to its enclosing `##` heading: **exactly one hit, `## Index`.** `## Browse by category` is a bulleted list
of `·`-separated anchor links, not a table. Propagated unchecked from the plan's drift row **D8**, which
says the same thing.

Not upgraded to Medium because the entry's actual claim is independently verified and unaffected:
`grep -rIl '## Quick comparison' .` hits only this rationale and the build plan — no repository document
contains that heading, so "there is no comparison table at HEAD" is true. Fix: "the file's only table is
its `## Index`".

#### `## Provenance of this record` records what moved and what stayed, but never the one thing that was ADDED

`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` `## Provenance of this
record` (lines 50-72). Its four clauses are Moved / nothing-deleted / left-in-spec / no-fenced-block, plus
the anchor note. The pass's **one addition to the spec** — the rule-1 pointer sentence at old-line-7's
position and its `[spec-007-rationale]` definition — is recorded only in this artifact, and this artifact
closes with the cycle while the rationale is durable. A later reader diffing the spec against `81e4704d`
sees an added sentence with no provenance in the file that owns the move's record.

One clause, e.g. appended to the Moved bullet: "and the paragraph's slot now carries the pointer sentence
this pass wrote, plus its link definition." Low because the pointer is self-describing in the spec.

### DRY findings

- **Same fact told twice inside one file.** `## How to read this file` bullets 3-6 (lines 23-38) and
  `## Provenance of this record` (lines 50-72) both carry: the move is exactly two items; that a two-item
  move is correct and not thin; that the file is not padded with invented debate; and that the substance is
  the change record. The Provenance section is the accounting; the How-to-read section is meta-narration of
  the same accounting. Cite: `#"The move itself is two items, and that is the whole move"` (line 23) against
  `#"Moved — cut from the spec by this pass"` (line 52). Not a blocker on its own — the sibling convention
  carries a `## How to read this file` and it does real work (the no-numbered-Decisions note, the
  two-orphaned-anchor note, the "this pass did NOT reconcile" note, the sibling-pointer note all appear
  nowhere else) — but the four overlapping bullets are recoverable bytes and the shorter of the two copies
  is the one to collapse. **Routed to Worker 1 as a judgement call, not required for acceptance.**
- **Existence challenge: not raised, and stated so rather than left silent.** Every `##` section in the new
  file records something found nowhere else. `## Standing note` in particular is not template filler: it is
  the durable home for the analysis the plan carries at `## The scope trap specific to this spec`, and the
  plan is a per-cycle artifact that closes with the cycle — moving it into the rationale is the correct
  direction, not duplication.
- **No cross-file duplication with the siblings.** `grep -ln '40c1855f\|FEATURES.md'` and
  `grep -ln '83c25963'` across `docs/SPECS/appx/*rationale.md` hit **only** this file. Neither the
  `FEATURES.md` → `GLOSSARY.md` rename chain nor the fold-in-by-deletion reversal is retold from a sibling.
- **No restatement of the causing cards' reasoning.** The entries record what spec-007 claimed and how it
  fared; the later cards' own decisions (spec-046 / 047 / 048's doc landings, the board migration, the
  glossary DB conversion) are named as causes and never argued.
- **Spec-versus-rationale DRY holds in the direction that matters.** The spec's new pointer sentence names
  three things and asserts none of them; the rationale quotes each spec claim before recording its fate
  rather than restating it as fact. The one duplication the move *retired* — the moved preamble's first two
  sentences against the `Status:` line — is real: both said the stub exists to give the DONE card a
  `SpecDoc` FK target, and only the `Status:` line still says it.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are
unchanged. Spec-007 shipped no package surface at all and this cycle's plan declares package source,
`tests/`, and `examples/` read-only throughout; no source edit was made by R1 and none by this review pass.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. (`git status --short` shows no `CHANGELOG.md` entry, and
`AGENTS.md` rule 21 plus the plan's build-wide flags close it to this cycle.)

### Documentation / release sanity

R1 touches docs and an archived spec, so this subsection applies.

- **The move is a MOVE, verified against pristine HEAD.** `diff` of the HEAD copy against the working-tree
  spec returns exactly four hunks: line 7 replaced (preamble paragraph → pointer sentence), lines 18-21
  deleted (`## Planning note`, blank, `shipped`, blank), one link definition added. **Three removed
  non-empty lines, two added** — exactly what the perform record claims, and 2,282 → 2,365 bytes /
  65 → 62 lines re-derived by `wc`. Both moved passages are quoted verbatim in the rationale
  (`### The preamble …` lines 80-83; `### `## Planning note` …` lines 138-139) and appear **nowhere** in the
  spec any more. Nothing was silently duplicated into both files; nothing was dropped from both.
- **Over-cut: none.** The move took two passages. Every remaining line of the spec is contract-shaped or a
  status claim: title / target-release / owner, the `Status:` line, six `## Card snapshot` rows, six
  `## Scope` bullets, eight `## Other` bullets, the link block. No `## Scope` bullet, no `## Other` bullet,
  and no `## Card snapshot` row was touched — confirmed line-by-line from the diff, not from the report.
- **Under-cut: the "left it for R2" line was tested independently and it holds.** The candidates for
  additional cutting are the `Status:` line (D2) and `## Card snapshot`'s wrong label row (D3). Both are
  *status claims about the card*, and `BUILD.md` `## Spec rationale extraction` gives the rationale file the
  deliberative layer — alternatives rejected, changes with causes, claims no longer makeable — not a card's
  status. Moving a status claim there would produce an entry naming no decision, which that section calls
  "worthless however well argued". And deletion is not available either: the mover's deletion rule applies
  to *falsified prose*, and D2 is verified **accurate** (see below) while D3 is a wrong value inside a
  correct section shape, which is a reconciliation edit by definition. So R2 is the right owner and this is
  not avoidance. Independently, both are *recorded* in the rationale rather than dropped —
  `### `Status:` …` and `### `## Card snapshot` — the label list` — so R2 inherits them with evidence.
- **D2 re-verified rather than accepted.** All four kanban guards exist in
  `examples/fakeshop/apps/kanban/signals.py` (three named correctly, one mis-named — Low above), so the
  `Status:` line's claim that the stub exists to hold the one-to-one invariant is an accurate description of
  an executable constraint. Not stale; correctly left alone.
- **Fabricated deliberation — the headline risk of this pass — is CLEAN, and I sampled every
  alternatives entry rather than spot-checking.** There are exactly three places the file records a rejected
  alternative, and each rests on repository evidence:
  1. `### The preamble …`'s three-way expand / delete / keep argument is explicitly bracketed as *"this
     pass's argument, not a recovered debate"*, with the sentence "No commit message, spec, or standing doc
     records the stub shape being weighed against anything". Every constraint it leans on is checkable at
     HEAD and I checked all three: the four `signals.py` guards exist; the creation-after-release
     chronology holds (`231911a8` 2026-05-08 release, `81e4704d` 2026-06-01 creation); and the seven-stub
     population is exact — `grep -rl 'This file is intentionally lightweight' docs/SPECS/*.md` returns 007
     plus 011 / 012 / 013 / 016 / 024 / 026, and the byte sizes 1,797 / 1,651 / 1,669 / 4,558 / 1,618 /
     3,593 all match to the byte. The label is sufficient; I disagree with the perform record's worry that
     it might not be.
  2. `### `## Scope` 6 …`'s delete-on-fold-in rejection is labelled *"on the record by outcome rather than
     by argument"* and closes "No commit message argues this; the reversal is the argument." The outcome is
     real: `83c25963` deleted six named spec files (`--name-status` confirms all six names, 2,495 deletions
     against 459 insertions) and `81e4704d` re-added them under `docs/SPECS/`. That is a reversal on the
     record, not a manufactured debate.
  3. `### `## Scope` 3 …` explicitly **declines** to invent one: "`40c1855f`'s message records no reasoning
     for the rename and this file does not invent any." Verified — the commit message is the four words
     "housekeeping: rename files", and its `--name-status` shows `R099 docs/FEATURES.md docs/GLOSSARY.md`
     and `R099 BETTER.md BACKLOG.md` exactly as described.
     **No entry in the file asserts an alternative the repository does not evidence.** Given the plan graded
     a fabricated alternative "at least Medium", the absence is the most important result of this audit.
- **The 1-anchor constraint holds, and I re-ran the checker rather than quoting R1's quotation.**
  `[optimizer behavior][glossary-djangooptimizerextension]` sits in `## Scope` bullet 2, which the diff
  proves untouched. Both checks re-run by this pass, verbatim:

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
(no output)
exit=0
```

- **Link scaffold and depth correctness in the new file: clean, and the depth trap is genuinely handled.**
  16 definitions (re-counted), all 16 resolve on disk, and I recorded *which* file each lands on rather
  than only that something exists — the trap the plan names is live here because this spec's subject is
  same-named files at two depths:

```text
[root-readme]  ../../../README.md    -> README.md          (root)
[readme]       ../../README.md       -> docs/README.md     (docs/)
[backlog]      ../../../BACKLOG.md   -> BACKLOG.md
[changelog]    ../../../CHANGELOG.md -> CHANGELOG.md
[contributing] ../../../CONTRIBUTING.md -> CONTRIBUTING.md
[glossary]     ../../GLOSSARY.md     -> docs/GLOSSARY.md
[tree]         ../../TREE.md         -> docs/TREE.md
[next]         ../NEXT.md            -> docs/SPECS/NEXT.md
[spec-005-rationale] / [spec-006-rationale] -> docs/SPECS/appx/…  (siblings, same dir)
[spec-007] + 3 anchored variants     -> docs/SPECS/spec-007-…md
[build]        ../../builder/BUILD.md    -> docs/builder/BUILD.md
[worker-1]     ../../builder/worker-1.md -> docs/builder/worker-1.md
```

  Usage is correct per claim, which is the half a bare exists-check misses: `## Scope` 1's entry uses
  `[root-readme]` for the root README's two jobs and `[readme]` for `docs/README.md`, and `## Scope` 2's
  entry uses `[readme]` throughout. All 10 canonical group headers present, in canonical order
  (`Root, docs/, docs/SPECS/, docs/builder/, django_strawberry_framework/, tests/, examples/, scripts/,
  .venv/, External`), alphabetical within every group (checked mechanically, zero violations), empty groups
  retained. No def is unused. The spec's own new definition resolves from `docs/SPECS/` to the created file.
- **The three spec anchors the rationale links to all exist.** `grep -n '^## '` on the spec →
  `## Card snapshot`, `## Scope`, `## Other`; slugs `#card-snapshot` / `#scope` / `#other` resolve.
  `## Planning note` is deliberately gone and nothing links to it — the two entries whose sections the move
  removed anchor `## Card snapshot` and say so in the entry text, which is the `### How to read this file`
  bullet 3 promise kept.
- **`AGENTS.md` rule 27 holds in both written files.**
  `grep -nE '[A-Za-z_./-]+\.(py|md|csv|toml|html):[0-9]+'` → no match in the spec, no match in the
  rationale. Every raw `path:NN`-shaped reference in this cycle is inside `bld-*.md` artifacts, where
  `START.md` "Temp artifact conventions" permits it. The one rule-27 defect is a *wrong* symbol name, not a
  line number (Low above).
- **Zero fenced code blocks in either file**, matching the claim: `grep -c '^\`\`\`'` → 0 on the spec before
  and after, 0 on the rationale. No four-backtick fence question arises.
- **The 83-byte growth: confirmed by reading the rule, and judged earned.** `BUILD.md` `## The corpus
  ratchet` names its scope explicitly — "`docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, and the four
  `docs/builder/worker-*.md` role files" — and "summed across all six files". Specs are not in it, and R1
  touched none of the six. So no ratchet binds this. On whether the sentence earns its bytes: yes. Its
  three clauses each do work a shorter pointer would not — the stub-shape argument and the fold-in reversal
  are the two entries a reader is most likely to re-litigate, and the third clause ("every claim … that this
  spec once made and may no longer make") is the only warning in the spec that its `## Scope` is a
  2026-05-08 snapshot, which matters acutely in the window between R1 and R2 where the spec now sits. The
  net across both files is +28,675 bytes for a file that is the sole record of the `0.0.4` documentation
  history; reporting the growth openly rather than shaving the pointer was the right call.
- **No obsolete staging language, and no script-rendered doc was touched.** R1 wrote no `TODO(` anchor
  (verified: zero in the rationale), and `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md`
  are all untouched by this pass — their churn is the concurrent cycle's, per the plan's
  `## Concurrent-writable tracked binary / generated files`.

### Independently re-derived claims

Everything below was measured by this pass. I did not accept a count, a byte figure, or an "unchanged"
claim on the perform record's word, per `BUILD.md` `## Claims are proven mechanically`.

**R1's own stated counts — all held except as noted in Medium/Low above:**

| Claim | Result |
|---|---|
| spec 2,282 bytes / 65 lines before | held (`wc` on the HEAD copy) |
| spec 2,365 bytes / 62 lines after | held |
| rationale 28,592 bytes / 444 lines | held |
| "+83 bytes, -3 lines" | held (arithmetic re-derived from both) |
| 16 link definitions, all resolve | held; and *which* file each resolves to re-checked |
| 10 group headers, canonical order, alphabetical within group | held |
| three removed non-empty lines, two added | held (diff against pristine HEAD) |
| `check_spec_glossary` → `OK: 1 terms …` | held (re-run, quoted verbatim above) |
| `check_trailing_commas --check` → exit 0 | held (re-run, quoted verbatim above) |
| zero fenced blocks before and after | held |
| no raw `path:NN` in either file | held |
| seven stubs, at the byte sizes listed | held (all seven paths and all seven sizes) |
| all seven stubs carry `## Planning note` | held (the other six each `grep -c` → 1; 007's removed by this pass) |
| `CHANGELOG.md` 100,289 bytes / 437 lines | held |
| `docs/README.md` 1,003 lines / 117,358 bytes | held |
| root README's eight `##` headings, as enumerated | held — the enumeration matches HEAD exactly, pointer entry included |
| the 13 operational headings gone from the root README | held — all 13 present at `231911a8`, none at HEAD; `2bd7cb84` is the removing commit (5 → 0) |
| `## Project documentation` = 8 bullets, all resolving | held (and the plan's "eight rows" is the shape error R1 flagged) |
| no `## Quick comparison` heading anywhere | held |
| "three-minute" on exactly 3 surfaces | held (1 occurrence each in spec / `KANBAN.md` / `KANBAN.html`) |
| "no section by that name, and there never was" | held as far as it is checkable — no heading matching `^#+.*three.minute` in ~400 sampled revisions |
| `## Other` = seven bullets | **FAILED — it is eight** (Medium above) |
| `spec-001-django_types-0_0_1.md` "is 50,195 bytes" | **FAILED at HEAD (44,596); correct at `81e4704d`** (Medium above) |
| `docs/GLOSSARY.md` has two tables | **FAILED — one** (Low above) |
| `signals.py::protect_done_card_glossary` | **FAILED — symbol is `…_glossary_link`** (Low above) |

**The five corrections to Worker 0's verified-facts table — I re-derived all five, and all five hold:**

1. **`231911a8` is the version cut, 2 files not 5.** Held. `git show --stat 231911a8` →
   `CHANGELOG.md | 31`, `KANBAN.md | 147`, "2 files changed, 102 insertions(+), 76 deletions(-)". The
   card's work is `4b8dce07` / `83c25963` / `3a4d40b7`, all 2026-05-05, and `83c25963`'s `--name-status`
   confirms the six deleted spec files by name with 2,495 deletions / 459 insertions. The plan's twice-stated
   "five Markdown files and nothing else" from `231911a8` is wrong; the correction is right.
2. **D4's mechanism — `planning_note` retained, value cleared.** Held, and provable from the commit body
   itself: `1592bb90`'s message says "`Card.planning_note` (the free-text field) is retained", the diff
   drops `PlanningState` / `Card.planning_state` / the `planningstate` O2O, and
   `models.py::Card` #"planning_note = models.TextField" is still there at HEAD. The DB reads
   `planning_note == ''`. The same commit also removed `- Severity: Low` and `- Planning state: Shipped`
   from this spec's `## Card snapshot`, exactly as the rationale states. "The model behind it is gone" was
   false; the correction is right.
3. **D13 — two card sections at `81e4704d`, four-way taxonomy 2026-07-20.** Held. All three migration
   commits are dated 2026-07-20 (`0c08204f` "reclassify the 378 'other' section items", `ac7cc6a4` "empty
   the other section", `4f68d3f2` which adds `kanban/migrations/0016_remove_other_section.py`), and
   `grep -c '^#### Other$' KANBAN.md` → **0**. The corrected finding — the spec's `## Other` heading names a
   card section the DB no longer has — is the stronger one and is correct. (Note the irony captured in the
   Medium above: the corrected entry gets the *mechanism* right and the *bullet count* wrong.)
4. **"three-minute" has 3 surfaces.** Held, at HEAD and in the working tree; 1 occurrence per surface, all
   three renders of one `CardItem`.
5. **Stub population is 7.** Held, with every path and every byte size confirmed.

**Other rationale claims sampled against the repository, all holding:** `2baf93b5` (2026-06-09) as the
`internal` label's arrival, eight days after the 2026-06-01 render; card 7's live labels are exactly
`docs`, `internal`, `release`; `e1f9ed26` (2026-06-04) as the glossary-CSV backfill that made the
`[optimizer behavior]` phrase a reference link; `40c1855f` rewriting `KANBAN.md` in the same sweep
(`FEATURES.md` hits 22 → 0 across `40c1855f~1` → `40c1855f`), which is what substituted the filename into
the card row before the DB was seeded; the `0.0.8` changelog entry citing
`[spec-027-filters-0_0_8.md][spec-filters]` and `[spec-028-orders-0_0_8.md][spec-orders]` with both
definitions live in the bottom block; `docs/README.md`'s `## Quick start` / `## Today and coming next` /
`## Nested connection indexing` all present; `docs/GLOSSARY.md`'s tables being `## Index` (and *not*
`## Browse by category`, the one Low).

### What looks solid

- **The judgement the plan pre-decided is the judgement that was made, and it was made honestly.** A
  2.3KB rendered card snapshot with two deliberative passages produced a two-passage move, said so plainly
  in three places, and did not pad. The temptation the plan named — inventing debate to justify a 28KB
  companion — was not taken anywhere in 444 lines. As the agent with no memory of why any sentence was cut,
  this is the thing I looked hardest for and did not find.
- **The record clause is where the value landed, and it is keyed correctly.** Every entry names its spec
  section by heading and links its anchor, so every entry is *lookup-able from the spec* — the property
  `BUILD.md` says an entry is worthless without. The two entries whose sections the move deleted say so and
  re-anchor to `## Card snapshot` rather than dangling.
- **Three entries are genuinely new knowledge, not restated drift rows.** The `## Scope` 3 chain (a true
  claim about `docs/FEATURES.md` with a different filename mechanically substituted into it by a rename
  sweep, so the sentence cannot be checked against the state it describes *at all*) is a sharper diagnosis
  than the plan's D7/D8. The `## Scope` 6 entry (fold-in meant deletion; the deletion was reversed by the
  very commit that created this spec file) is a finding the plan's D10 did not have. And the `## Scope` 2
  note that the glossary link is a **retrofit** onto whichever sentence happened to contain a linkable
  phrase explains *why* the 1-anchor constraint is as fragile as it is.
- **The `## Standing note`'s role-versus-inventory split is measured, not asserted**, and it is the single
  most useful thing R2 inherits: the two role claims hold at HEAD after ten minor versions, and every
  content-inventory claim failed, each by a different mechanism. I re-derived both halves. It is also
  correctly labelled as analysis rather than disposition.
- **The escalations were handled the way the rules require, in both directions.** The five deleted
  `docs/review/rev-*.md` files are reported and left in place, with the rule-22-versus-rule-34 collision
  named explicitly and `git checkout HEAD -- docs/review/` correctly refused as banned in this tree. I
  independently confirm the state is unchanged and worsened by nothing this pass or my pass did:
  `git ls-tree -r --name-only HEAD docs/review/` lists 5 `rev-*` files, disk has 0, and `REVIEW.md` /
  `review-0_0_*.md` / `worker-*.md` are all present. **No further growth beyond what the plan already
  records.** Nothing was restored, reverted, or touched.
- **Baseline-dirty discipline is exact.** `git status --short` at the end of my pass is byte-identical to
  the block the perform record quotes. Only two entries are attributable to R1, and both appear in
  `### Files touched`.

### Temp test verification

- No temp test was written. Nothing under `docs/builder/temp-tests/r1/` was created, and the directory
  remains as pre-flight left it.
- Correctly so: this pass reviews prose. Every claim under audit is a byte count, a line count, an
  occurrence count, a commit fact, a filesystem-resolution fact, or a checker exit code — all of which are
  measured directly with `git show` / `wc` / `grep` / the two repository checkers, and none of which a
  pytest module could pin better. Recorded rather than skipped silently.

### Failability-proof audit

`None owed, and none owed is the correct state.` R1 introduced no boundary, guard, gate, or rejection
path — it moved prose between two Markdown files — so per `BUILD.md` `### What needs a proof, and what
does not` the obligation does not attach, and the perform record's
`None; this pass introduced no new boundary.` is the right entry rather than a gap. The obligation that
*did* apply is the mechanical-verification class of `## Claims are proven mechanically`, and that is what
`### Independently re-derived claims` above discharges.

- **Boundaries re-run independently:** none, and the empty re-run set is legal because the diff introduces
  no boundary that meets the mandatory floor (`worker-3.md` "Reading is necessary, not sufficient" — the
  floor is computed from recorded row counts, and there are no boundaries to have counts).
- **Boundaries accepted on the performer's record:** none.
- **No mutation was made by this pass**, so the source carve-out was never exercised and no revert
  byte-comparison is owed. `docs/shadow/` was not written to. No `.py` file in the repository was opened
  for writing by this pass at any point.

### Hot-path budget verification

`Not applicable; plan declares no hot path.` Confirmed by reading the plan's preamble
(#"Hot-path declaration: none") rather than the artifact's echo of it, and confirmed against the diff:
R1 changes no package source, so nothing it touches runs per request, per resolver, per row, per
connection, or per outbound message. **The absence of a number is correct here and is not a finding.**

### Floor verification

`Not applicable; plan declares floor-verification scope none.` Confirmed from the plan preamble
(#"Floor-verification scope: none") and against the diff: no Django / Strawberry / channels integration
seam is touched by two Markdown files. No floor venv was built by this pass and none is owed by the final
gate on R1's behalf. **The silence is deliberate, not an omission.**

### Static helper use

`scripts/review_inspect.py` **not run, and the skip is recorded with its reason**: `BUILD.md`
`### When to run the helper during build` triggers Worker 3 on a new `.py` file, on a file under
`optimizer/` or `types/`, or on 30+/50+ new lines of logic. R1 adds no `.py` file and touches none — its
diff is two Markdown files. There is no AST for the helper to parse and no repeated-literal or
import-boundary evidence any finding in this review depends on. `docs/shadow/` was neither read nor
written by this pass (and per the plan's Deviation 3 it holds the concurrent cycle's state, which this pass
left alone).

### Notes for Worker 1 (spec reconciliation)

Recorded on disk, not only in the return report, per `BUILD.md` `### Cohorting, naming, and closure`.

**Owned by the R1 revision pass (Worker 1, per the plan's Deviation 2 corollary — the two rules that make
Worker 1 the only role that may perform the move and edit the spec make it the only role that can fix
them). All four are one-line edits to the rationale; none requires restructuring, and none touches the
spec:**

1. `## Other` is **eight** bullets, and the breakdown is **two** `Note` rows — rationale lines 62 and 352,
   plus this artifact's `### What moved, and what stayed`. (Medium.)
2. Attribute the 50,195-byte figure to `81e4704d` instead of asserting it in the present tense —
   rationale line 318. HEAD is 44,596. (Medium.)
3. `signals.py::protect_done_card_glossary_link`, not `…_glossary` — rationale line 119 and this
   artifact's `### Spec status-line re-verification`. (Low.)
4. `docs/GLOSSARY.md` has one table, `## Index` — rationale line 253. (Low.)
5. Optional, and Worker 1's judgement: record the pointer sentence as this pass's one **addition** in
   `## Provenance of this record` (Low), and collapse the four-bullet overlap between
   `## How to read this file` and `## Provenance of this record` (DRY).

**Escalated: the drift table's D8 carries the same "two tables" error** (`## Index` and
`## Browse by category`). The plan is Worker 0's file and no worker edits it, so this is a note for the
plan's next correction block rather than an edit. Resolution paths: (a) Worker 0 appends it to
`## Corrections to this table` at R2's close, or (b) R2 simply reconciles the spec bullet against the
verified fact and the plan row stays as a known-imprecise input. **(b) is sufficient** — the row's
disposition does not turn on the count.

**Routed to R2 (spec reconciliation) — carried forward from R1 and re-verified by this pass:**

- **D1 is discharged inside R1, not deferred.** The falsified "expand it into the full builder-format spec"
  instruction is gone from the spec; the diff proves it. R2 verifies absence rather than reconciling. I
  confirm cutting all three sentences as one unit was sanctioned — the plan's `### What R1 inherits` names
  the paragraph as an R1 move candidate — and not scope creep.
- **D2 must not be "fixed".** Re-verified against `signals.py` this pass: the `Status:` line accurately
  describes an executable constraint. It is the row most likely to be tidied by a reconciliation pass that
  reads it as self-narration.
- **D3 (the label row) and the `## Card snapshot` section question are live and unpatched**, deliberately.
  The DB reads three labels (`docs`, `internal`, `release`); the spec says two. The rationale records the
  case that the *section* is the defect (a hand-copied DB render that nothing re-renders, already
  hand-patched once by `1592bb90`) rather than the bullet. Both dispositions are open and correctly R2's.
- **`## Scope` bullet 6's fold-in tension is the highest-value input R2 has**, and it is stronger than the
  plan's D10: the bullet's two halves were in conflict, and `81e4704d` — the commit that created this very
  file — resolved it against the first half by restoring the six specs the card had deleted. Verified
  independently.
- **The role-versus-inventory split is the reconciliation strategy, and it is measured.** Reconciling
  toward roles is durable; reconciling toward a current inventory guarantees this cycle runs again at
  `0.1.0`. The `## Standing note` is its durable home and R2 should not restate it in the spec.
- **The 1-anchor constraint is not yet exercised.** It held trivially in R1 by construction (the carrier
  bullet was untouched). R2 rewrites `## Scope` bullet 2, which is where the constraint actually bites:
  re-site `[optimizer behavior][glossary-djangooptimizerextension]` **in the same edit**, and re-run
  `check_spec_glossary.py` before setting any status.

**Routed to R3 (documentation and archive audit) — verified by this pass:**

- **`CONTRIBUTING.md` carries the same dangling `docs/builder/BUILD.md` "Spec filename pattern" citation**
  as the spec's final `## Other` bullet (`BUILD.md`'s real heading is `## Spec and build-plan filename
  pattern`). `CONTRIBUTING.md` is outside this cycle's writable set, so it belongs in the deferred-work
  catalog as a maintainer follow-up. It also means retiring the spec's borrowed copy does not retire the
  dangling citation from the repository — a fourth surface the plan's `### Every reference TO spec-007`
  table does not list.
- **The root README's `## Project documentation` map is eight *bullets*, not a table** — re-confirmed this
  pass, all eight resolving. R3 must not grep for table syntax.
- **`## Other` = 8 bullets is R3's number too**, not seven, if any sweep counts them.
- **The staged-anchor sweep and `import_spec_terms --check` remain R3's** and are unaffected by R1 or by
  this review: neither pass wrote the DB, and the new rationale contains no `TODO(` anchor (verified zero).
- **The `docs/review/rev-*.md` deletion is still open and unresolved**, and R3's archive audit will see it.
  It is not this cycle's output in any direction; do not let a `docs/review/` sweep read the absence as
  drift to fix. Maintainer decision only.

### Review outcome

`revision-needed`.

Set on two Medium findings, both of them wrong stated counts in a **durable** file — the `## Other`
bullet count sitting inside the sentence that claims its own accounting is exhaustive, and a present-tense
byte figure that is false at HEAD by 5,599 bytes inside the file whose thesis is that present-tense content
claims rot. Neither is a judgement disagreement and neither costs more than a line to fix; I am not holding
the item on the DRY note or on the existence question, and I am not holding it on anything routed to R2 or
R3.

What the pass got right is the part that could not have been fixed later: the move is a real move
(verified against pristine HEAD), it is neither over- nor under-cut, the "left it for R2" line is drawn on
a rule rather than on convenience, all five of Worker 0's corrections hold under independent re-derivation,
and **no deliberation was fabricated anywhere in 444 lines** — the risk the plan graded at least Medium
before this pass began. Per the plan's Deviation 2 corollary this routes to **Worker 1**, which re-sets
`planned`.

### Working-tree churn observed during this review pass

Reported, never reverted (`AGENTS.md` rule 34). `git status --short` at the close of this audit is
identical to the block the perform record quotes, **plus one new entry that appeared during this pass**:

- `docs/review/review-0_0_14.md` (`??`, untracked) — absent at the start of this pass, present at its end.
  Not written by this pass and outside this cycle's writable set in every direction. `START.md`
  "Temp artifact conventions" makes `docs/review/review-<X>.md` a REVIEW-cycle scratchpad, so this is most
  likely the same third session the `rev-*.md` deletions are escalated against — which, if so, is evidence
  those deletions are a closing REVIEW cycle's cleanup rather than a rule-22 violation. **That remains the
  maintainer's call and this pass makes no inference binding on it.** Worker 0 should append this entry to
  the plan's `## Baseline-dirty out-of-scope files`; a worker does not edit the plan.

The five `docs/review/rev-*.md` deletions are **unchanged** — still 5 tracked at `HEAD`, still 0 on disk,
still not restored, not reverted, and not touched by this pass. `HEAD` re-derived at the close of the audit
is still `947f7494`, so nothing this cycle wrote was swept into a concurrent commit.

---

## Perform record (Worker 1, pass 2 — apply-changes)

Worker 3 set `revision-needed` on two Medium and three Low findings. Per the plan's **Deviation 2
corollary** the apply-changes pass is Worker 1's, not Worker 2's: the same two rules that make
Worker 1 the only role that may perform the rationale move and edit the spec make it the only role
that can fix them. `Status:` is re-set to `planned`, returning the artifact to the
`planned` -> Worker 3 mapping.

**Prior sections are not edited** (`ARTIFACT.md` `## Re-pass sections`: "never edit prior entries").
Where a prior section carries a figure this pass corrected, the correction is stated here and the
prior figure is superseded rather than overwritten — see `### Corrections to this artifact's own
prior sections` below.

### Files touched

- `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` — **five edits**,
  one per finding. No section added, none removed, no link definition changed, no entry
  restructured.
- `docs/builder/bld-007-r1-rationale_move.md` — this pass section appended; `Status:` line re-set.
- `docs/builder/worker-memory/spec-007-worker-1.md` — memory entry appended (gitignored).

**`docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` was NOT touched by this pass**,
and that is the correct outcome rather than an omission. All five findings are in the rationale
file; none requires a spec edit, and restating a falsified spec claim here would be a reconciliation
rewrite — R2's work, which R2 would then be reviewing its own version of. Proven mechanically:
`git diff --stat` on the spec is still R1's `2 insertions(+), 5 deletions(-)` and `wc -c` still
reads **2,365 bytes / 62 lines**, byte-identical to the figure R1 recorded and Worker 3 re-derived.

### Findings closed

**Medium 1 — `## Other` is eight bullets, not seven; the DB breakdown drops one `Note`.**
Re-derived from the live kanban DB read-only rather than trusted from either the finding or the
plan:

```text
$ uv run python examples/fakeshop/manage.py shell -c "... Counter(i.section.key for i in card.items.all())"
total 14
Counter({'scope': 6, 'files_touched': 5, 'note': 2, 'why_it_matters': 1})
```

Six `scope` rows render as `## Scope`; the remaining **eight** render as `## Other` —
1 `why_it_matters` + 5 `files_touched` + **2** `note`. Cross-checked against the spec on disk: the
`## Other` bullets are the `why_it_matters` row, the first `note` row, the five `files_touched`
rows, and the second `note` row (the spec-filename-convention bullet) = **8**.

Two edits, both in the rationale:

1. `## Provenance of this record`, the left-in-spec clause — the number sitting **inside** the
   exhaustiveness claim: "all seven `## Other` bullets" -> "all **eight** `## Other` bullets".
2. `### `## Other` — a heading that names a card section the board has retired` — "its seven bullets
   are the pre-reclassification shape frozen in place - one `Why it matters` row, five
   `Files likely touched` rows ..., and one `Note`" -> "its eight bullets ... and **two** `Note`
   rows".

The entry's substantive finding (the `## Other` heading names a card section the DB has retired) is
untouched; only the count and the breakdown moved. Noted for the record: this was a **new** error
introduced while correcting five plan rows, not a propagated one — the plan states the correct
figure twice (`## Worker-0-verified facts` #"`Note` x2" and #"a lossy merge of the other eight").
A count asserted in the same breath as the lesson it illustrates is routinely wrong, and this one
sat inside the sentence claiming its own accounting exhaustive.

**Medium 2 — the spec-001 byte figure was asserted in the present tense and is false at HEAD.**
Re-derived all three figures rather than accepting Worker 3's:

```text
$ git show 83c25963^:docs/spec-django_types.md | wc -c            -> 50075
$ git show 81e4704d:docs/SPECS/spec-001-django_types-0_0_1.md | wc -c -> 50195
$ git show HEAD:docs/SPECS/spec-001-django_types-0_0_1.md | wc -c     -> 44596
```

Fixed by **anchoring the measurement to the commit it belongs to**, not by swapping in the HEAD
number — 44,596 would break the argument, because the argument is that `81e4704d` performed a
*restoration* and the evidence for that is the pair of sizes at the two commits either side of it.
`is 50,195 bytes` -> `was 50,195 bytes when 81e4704d created it`, plus one sentence stating that
both figures are measured at the commits they belong to and neither is a claim about HEAD. The
addition is deliberate rather than the two-word minimum Worker 3 proposed: this file's whole
`## Standing note` thesis is that present-tense content claims rot, so the entry now says in its own
prose which tense it means — which is the lesson, applied to itself.

**Low 3 — dangling symbol on a load-bearing guard.** Verified the corrected symbol exists before
writing it (`AGENTS.md` rule 27):

```text
$ grep -n 'def protect_done_card\|def _validate_done_card' examples/fakeshop/apps/kanban/signals.py
143:def _validate_done_card_has_spec(
148:def _validate_done_card_has_glossary_link(
404:def protect_done_card_spec(
450:def protect_done_card_glossary_link(
```

`signals.py::protect_done_card_glossary` -> `signals.py::protect_done_card_glossary_link` in the
`### The preamble ...` entry's delete-the-file rejection. All four symbols the entry names now
resolve. The bullet was reflowed onto three lines by the longer name; no wording else changed.

**Low 4 — `docs/GLOSSARY.md` has one table, not two.** Re-derived by scanning for table separator
rows and attributing each to its enclosing `##` heading:

```text
$ uv run python -c "... re.match(r'^\|[\s:|-]+\|$', line) ... print('TABLE SEP under', current_heading)"
TABLE SEP under ## Index
```

Exactly one. `## Browse by category` is a bulleted list of anchor links. "the file's two tables are
`## Index` and `## Browse by category`" -> "the file's only table is its `## Index`". The
conclusion the sentence supports — the four-column `## Quick comparison` table is gone — is
independently verified and unaffected. This one was propagated unchecked from the plan's D8 row,
which Worker 0 has since corrected in the plan's `## Corrections to this table`; the plan's
correction and this edit now agree.

**Low 5 — `## Provenance of this record` logged the pass's removals but never its one addition.**
The **Moved** bullet now closes with the addition: the vacated paragraph slot carries the one-line
rule-1 pointer sentence naming what was moved and where, plus its `[spec-007-rationale]` link
definition under `<!-- docs/SPECS/ -->`. Recorded in the Moved bullet rather than as a new clause so
the removal and the thing that replaced it read together, which is what a reader diffing the spec
against `81e4704d` needs.

### Declined, with the reason recorded

- **Worker 3's DRY note** — collapsing the four-bullet overlap between `## How to read this file`
  and `## Provenance of this record`. Routed as "a judgement call, not required for acceptance", and
  **declined this pass.** This is an apply-changes pass whose mandate is five wrong facts in a
  durable file; restructuring two sections' prose alongside them would hand the re-review a diff
  where the correctness edits are the minority, and the four bullets are not wrong — only
  redundant. Recorded rather than dropped: it is a live, real observation and belongs to whichever
  pass next has authorship reasons to touch those two sections. It is repeated in
  `### Notes for Worker 1 (spec reconciliation)` below so it survives this artifact's closure.
- **No scope widening.** Nothing outside the five findings and the `Status:` line was edited in any
  file.

### Corrections to this artifact's own prior sections

Stated here rather than by editing them, per `ARTIFACT.md` `## Re-pass sections`:

- `## Perform record (Worker 1)` `### What moved, and what stayed` reads "all seven `## Other`
  bullets" in its exhaustive left-in-spec list. **Superseded: eight** (1 `why_it_matters` +
  5 `files_touched` + 2 `note`), per the DB re-derivation above.
- `## Plan (Worker 1)` `### Spec status-line re-verification` names
  `::protect_done_card_glossary`. **Superseded: `::protect_done_card_glossary_link`.** The
  status-line conclusion it supports — the `Status:` line describes an executable constraint and
  needed no edit — is unaffected; all four guards exist, one was mis-spelled.

### Byte and line counts, measured as each number was written

| File | Before this pass | After this pass | Delta |
|---|---|---|---|
| `docs/SPECS/appx/spec-007-…-rationale.md` | 28,592 bytes / 444 lines | 29,075 bytes / 448 lines | **+483 bytes**, +4 lines |
| `docs/SPECS/spec-007-…-0_0_4.md` | 2,365 bytes / 62 lines | 2,365 bytes / 62 lines | **0** — not touched |

Both after-figures read from `wc -lc` at the moment this row was written, not carried from an
earlier reading. The rationale's +483 bytes buy: the addition clause (finding 5), the
measured-at-their-commits sentence (finding 2), and eleven characters of corrected counts and one
corrected symbol. No `--cov*` flag was used anywhere; no `pytest` was run (none is owed).

The corpus ratchet does not bind this pass: `BUILD.md` `## The corpus ratchet` scopes itself to
`BUILD.md`, `ARTIFACT.md`, and the four `worker-*.md` role files, none of which this pass touches.

### Validation run

Re-run by this pass, on every file it wrote, and quoted verbatim:

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md docs/builder/bld-007-r1-rationale_move.md
(no output)
exit=0
```

The 1-anchor constraint still holds trivially and still by construction: the sole carrier
`[optimizer behavior][glossary-djangooptimizerextension]` is in `## Scope` bullet 2, which neither
R1 nor this pass touched. It remains live for R2.

**No link definition broke, and the depth trap was re-checked rather than assumed.** All **16**
definitions in the rationale re-resolved from `docs/SPECS/appx/`, each printed with the
repo-relative file it actually lands on. No definition was added, removed, or repointed by this
pass; the re-check confirms none was collaterally damaged.

```text
[root-readme]  ../../../README.md  -> README.md          (root)
[readme]       ../../README.md     -> docs/README.md     (docs/)
```

Two different files, both existing, each used for the claim that is about it — the trap `../README.md`
from `appx/` would have masked. The other 14 (`backlog`, `changelog`, `contributing`, `glossary`,
`tree`, `next`, `spec-005-rationale`, `spec-006-rationale`, `spec-007` + its three anchored
variants, `build`, `worker-1`) all resolve on disk. All 10 canonical group headers present, in
canonical order, alphabetical within each group.

The three spec anchors the rationale links to still exist: `grep -n '^## '` on the spec returns
`## Card snapshot`, `## Scope`, `## Other`; `#card-snapshot` / `#scope` / `#other` resolve.

- `grep -nE '[A-Za-z_./-]+\.(py|md|csv|toml|html):[0-9]+'` -> **no match** in the rationale, no
  match in the spec. `AGENTS.md` rule 27 holds in both written files; the raw `path:NN`-shaped refs
  in this cycle are inside `bld-*.md`, where `START.md` permits them.
- `uv run ruff format` / `ruff check --fix` — **not run, and correctly not run.** This pass touched
  no `.py` file.

### Failability proofs

`None; this pass introduced no new boundary.` It corrects five factual statements in one Markdown
file and adds no guard, gate, cap, or rejection path. The mechanical checks above are not failability
proofs and are not offered as substitutes for one.

### Hot-path budget

`Not applicable; plan declares no hot path.` Re-confirmed against the plan preamble
(#"Hot-path declaration: none") rather than this artifact's echo of it. No package source changed.

### Floor verification

`Not applicable; plan declares floor-verification scope none.` Re-confirmed against the plan
preamble (#"Floor-verification scope: none"). No Django / Strawberry / channels integration seam is
touched by one Markdown file.

### Implementation notes

- **Anchoring beat substituting on finding 2.** The obvious repair was to write 44,596. It would
  have destroyed the entry: 50,075 -> 44,596 is not a restoration, it is a 5,479-byte loss, and the
  entry's claim is that `81e4704d` restored the six deleted specs. The measurement the argument needs
  is the one at the restoring commit, so the fix is a tense and an attribution, never a new number.
- **The DB was re-derived, not the plan or the finding.** Both the plan and Worker 3 state eight, but
  they disagreed with the file, and the plan is also the source of the one Low that propagated
  unchecked (D8). Reading the DB directly is the only reading that does not depend on a document.
- **The mis-named symbol forced a reflow, and the reflow is the whole diff on that bullet.** Adding
  `_link` pushed the line past the surrounding wrap width; the bullet is re-wrapped onto three lines
  with no word changed.

### Notes for Worker 3

- **What to audit hardest is that the five edits are exactly five, and that the spec is untouched.**
  `git diff` on the spec must still read `2 insertions(+), 5 deletions(-)` and `wc -c` 2,365 — if it
  moved, this pass performed a reconciliation edit it had no mandate for.
- **Two counts to re-derive independently, not accept.** The eight-bullet figure (from the DB, not
  from this artifact and not from the plan) and the three spec-001 byte figures at their three
  commits. Both are re-derivable in one command each.
- **The prior sections were deliberately not edited**, so `### What moved, and what stayed` and
  `### Spec status-line re-verification` still carry the superseded "seven" and the mis-named symbol.
  That is `ARTIFACT.md` `## Re-pass sections` being followed, not a missed fix; the supersessions are
  stated in `### Corrections to this artifact's own prior sections`. If the round would rather have
  the prior sections corrected in place, that is a finding worth making — the two rules genuinely
  pull against each other here and this pass chose the artifact contract.
- **The declined DRY note is declined, not overlooked**, with the reason recorded above.
- **No temp test, no shadow file, no mutation, no DB write.** `docs/shadow/` was not written to; the
  kanban DB was read via a read-only ORM query and never written.

### Notes for Worker 1 (spec reconciliation)

Extends the section R1 and Worker 3 already wrote; nothing there is retracted. Everything routed to
R2 and R3 by either prior pass **still stands** — D1 discharged inside R1, D2 must not be "fixed",
D3 and the `## Card snapshot` section question open, `## Scope` 6's fold-in tension as R2's
highest-value input, the role-versus-inventory split as the reconciliation strategy, the 1-anchor
constraint live for R2, and R3's `CONTRIBUTING.md` / eight-bullets-not-a-table / `## Other` = 8 items.

New from this pass:

1. **`## Other` = eight is now correct in the durable file**, at both sites. Any later sweep that
   counts them should get 8, and the DB breakdown is `why_it_matters` 1 + `files_touched` 5 +
   `note` 2. R2 will meet this number when it decides the `## Other` heading's disposition — the
   heading names a card section the board retired, and the eighth bullet is the second `note` row,
   the spec-filename-convention bullet carrying D11's dangling `BUILD.md` citation.
2. **The two `note` rows are not interchangeable**, which the corrected breakdown now makes visible:
   one is the card's own summary of what it did ("onboarding-doc consolidation across README / docs
   / CHANGELOG…"), the other is the borrowed spec-filename convention (D11, the single-ownership-law
   row). Merging them under one count is what hid the second one. R2 should dispose of them
   separately.
3. **Every present-tense measurement in the rationale is now attributed to a commit.** If R2 or R3
   adds a byte, line, or occurrence count to either file, attribute it the same way — this file's
   own thesis is that unattributed present-tense content claims rot, and it has already been caught
   breaking that rule once (finding 2).
4. **The DRY collapse is still open**, deliberately: `## How to read this file` bullets 3-6 and
   `## Provenance of this record` both carry the move-is-two-items / not-thin / not-padded / the
   substance-is-the-record facts. Worker 3 measured the overlap and routed it as a judgement call;
   this pass declined it as out of an arithmetic-correction mandate. It is not a blocker and it is
   not required for acceptance — it belongs to whichever later pass has an authorship reason to
   rewrite those two sections, and the shorter of the two copies is the one to collapse.
5. **The plan's D8 row and this file now agree** (one table, `## Index`). Worker 0 already appended
   the sixth correction to the plan's `## Corrections to this table`, so the escalation Worker 3
   raised is closed on both sides and R2 needs no separate action on it.

### Working-tree churn and baseline growth

Reported, never reverted (`AGENTS.md` rule 34). `git status --short` at the close of this pass is
**byte-identical to the block Worker 3's review recorded** — same 17 entries, no growth in either
direction:

```text
 M KANBAN.html
 M KANBAN.md
 M docs/SPECS/spec-006-public_surface-0_0_3.md
 M docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
 D docs/review/rev-_cross_web_patches.md
 D docs/review/rev-_django_patches.md
 D docs/review/rev-_strawberry_patches.md
 D docs/review/rev-apps.md
 D docs/review/rev-conf.md
 M examples/fakeshop/db.sqlite3
?? docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md
?? docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
?? docs/builder/bld-006-r1-rationale_move.md
?? docs/builder/bld-007-r1-rationale_move.md
?? docs/builder/build-006-public_surface-0_0_3.md
?? docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md
?? docs/review/review-0_0_14.md
```

**Attributable to this pass:** `docs/SPECS/appx/spec-007-…-rationale.md` (already `??` from R1) and
this artifact. Nothing new appears, so this pass grew the baseline-dirty list by nothing and Worker 0
has no new entry to append.

**The five `docs/review/rev-*.md` deletions are unchanged and still ESCALATED / UNRESOLVED.** Still
5 tracked at `HEAD`, still 0 on disk, not restored, not reverted, not touched by this pass. The
rule-22-versus-rule-34 collision the prior passes named is unchanged and `git checkout HEAD --
docs/review/` remains banned in this tree. `docs/review/review-0_0_14.md` (`??`) is likewise left
alone. Maintainer's call, in both directions.

**HEAD is unchanged at `947f7494`**, re-derived at the open and the close of this pass rather than
trusted from the plan or from a prior section. No commit landed during it, so nothing this cycle
wrote was swept into a concurrent commit.

### Residual-item checklist — re-audit of the ticks (pass 2)

Every box R1 ticked was re-checked against the file on disk this pass. All seven ticks stand; the
two Medium and three Low findings were defects **inside** contracts that did land, not un-landed
contracts, so no tick is withdrawn:

- The move is still a move (spec byte-identical to R1's post-move state; both passages present in
  the rationale and absent from the spec).
- The record still names every entry by heading and anchor, and all three anchors resolve.
- The five plan-row corrections are unchanged and were not re-litigated.
- The 1-anchor check and the before/after counts are re-run and re-recorded above.
- The 10-header scaffold and all 16 disk-resolved definitions re-verified, depth trap included.

The two open boxes stay open and are correctly open: Worker 3's audit (this pass hands back to it)
and Worker 1's final verification.

### Status

`planned`. Returns the artifact to the `planned` -> Worker 3 re-review mapping declared in the
plan's Deviation 2.

---

## Review (Worker 3, pass 2)

Fresh invocation with no memory of pass 1's reasoning; the artifact and the working tree are the
record. Scope is the re-review of the five closures plus a regression sweep, per `BUILD.md`
`## Subagent dispatch` step 4 ("repeat until Worker 3 has no unresolved findings, or every remaining
finding is intentionally rejected with a recorded reason"). Pass 1's four substantive verdicts (no
fabricated deliberation, the move is a move, the 1-anchor carrier untouched, the "left it for R2"
line rests on a rule) were not re-litigated.

`git rev-parse HEAD` -> `947f74948c16b20b0c15ff359bb53fbe462d4b8c`, unchanged. No `git stash` /
`checkout` / `restore` / `worktree` was used for any purpose; before-states came from
`git show <rev>:<path>` piped to `wc`, never written into the tree.

### The five closures, each re-derived rather than read

| Closure | Independent derivation | Verdict |
|---|---|---|
| M1 `## Other` = eight, two `Note` rows | Live kanban DB, read-only ORM: `total 14`, `Counter({'scope': 6, 'files_touched': 5, 'note': 2, 'why_it_matters': 1})`, and each item's section printed; cross-counted the spec's own `## Other` bullets on disk = 8 | **Held.** Both sites corrected: `## Provenance of this record` #"all **eight** `## Other` bullets" and `### `## Other` ...` #"its eight bullets" with #"two `Note` rows" |
| M2 spec-001 byte figure | `83c25963^` -> 50075; `81e4704d` -> 50195; `HEAD` -> 44596 | **Held, and repaired the right way.** #"was 50,195 bytes when `81e4704d` created it" plus the sentence stating both figures are measured at their commits and neither is a HEAD claim. Substituting 44,596 would have destroyed the restoration argument; anchoring preserves it |
| L3 symbol name | `grep -n 'def protect_done_card\|def _validate_done_card'` on `examples/fakeshop/apps/kanban/signals.py` -> lines 143 / 148 / 404 / 450, the last being `protect_done_card_glossary_link` | **Held.** All four symbols the entry names resolve; `grep 'protect_done_card_glossary\b'` on the rationale returns nothing |
| L4 GLOSSARY table count | Re-scanned `docs/GLOSSARY.md` for `^\|[\s:|-]+\|$` attributing each hit to its enclosing `##`: exactly one, under `## Index` | **Held.** #"the file's only table is its `## Index`". The clause the edit *added* — no file in the repository carries a `## Quick comparison` heading — was also re-derived: `grep -rIn '^#\+ *Quick comparison'` has no match; the three files containing the string carry it in code spans |
| L5 the pass's one addition | Read `## Provenance of this record` on disk | **Held.** The **Moved** bullet now closes #"**Added in exchange, and it is the pass's only addition to the spec:**" naming the pointer sentence and the `[spec-007-rationale]` definition |

### Nothing else regressed

- **Spec untouched, re-derived two ways.** `wc -lc` -> `62 2365`; `git diff --stat` -> `1 file
  changed, 2 insertions(+), 5 deletions(-)`; the full `git diff` body is still exactly R1's move
  (preamble replaced by the pointer, `## Planning note` heading + body removed, one link definition
  added under `<!-- docs/SPECS/ -->`). No reconciliation edit leaked into this pass.
- **No link definition added, removed, or repointed.** All **16** definitions in the rationale
  re-resolved from `docs/SPECS/appx/`, each printed with the repo-relative file it lands on; every
  one exists. All 10 canonical group headers present, in canonical order.
- **Depth trap re-checked, not assumed.** `[root-readme] ../../../README.md -> README.md` and
  `[readme] ../../README.md -> docs/README.md` are two different existing files, and every use site
  matches its subject (lines 181 root; 190/193/206/216/228/308 `docs/README.md`). The masking
  spelling `../README.md` appears nowhere.
- **Rationale counts re-derived at the moment of reading:** `29,075 bytes / 448 lines`, matching the
  after-row; `29075 - 28592 = 483` and `448 - 444 = 4`, matching the delta column. The before-row is
  corroborated by R1's own record and pass 1's re-derivation of it.
- **`AGENTS.md` rule 27:** `grep -nE '[A-Za-z_./-]+\.(py|md|csv|toml|html):[0-9]+'` has no match in
  either written doc file.
- **Checkers re-run by this pass, quoted verbatim** (see `### Validation run (this pass)` below);
  both reproduce Worker 1's quoted output exactly.

### High:

None.

### Medium:

#### `## How to read this file` calls spec-007 "the smallest spec in the repository" — false, and the file itself lists four counterexamples 77 lines later

`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`
`## How to read this file` #"This is the smallest spec in the repository" (line 24).

The bullet reads: "**The move itself is two items, and that is the whole move.** This is the smallest
spec in the repository — 2,282 bytes, 65 lines, zero fenced code blocks — and it has almost no
deliberative layer".

Re-derived over all 56 tracked `docs/SPECS/spec-*.md` at HEAD:

```text
   1618 spec-024-django_trac_37064_hardening-0_0_7.md
   1651 spec-012-version_release_alignment-0_0_4.md
   1669 spec-013-real_m2m_coverage-0_0_4.md
   1797 spec-011-stale_placeholder_cleanup-0_0_4.md
   2282 spec-007-onboarding_docs_spec_consolidation-0_0_4.md   <-- fifth smallest, not smallest
```

Four specs are smaller, and **all four are named with their byte counts in this same file** at
`### The preamble ...` #"011\n(1,797), 012 (1,651), 013 (1,669)" (line 101-102) — so the file
contradicts itself across 77 lines, and the contradiction is re-derivable from the file alone with no
repository access.

Two aggravations, both of which this pass's own work created the standard for:

1. The figures are an **unattributed present-tense measurement** of a file this cycle changed. `wc
   -lc` on the spec now reads `2,365 bytes / 62 lines`; 2,282 / 65 is the pre-move size at HEAD, with
   no commit named. That is finding M2's defect at a second site, and the same
   `## Standing note` thesis governs it.
2. `BUILD.md` `## Claims are proven mechanically` #"a count asserted in the same breath as the lesson
   it illustrates is routinely wrong" applies literally: the count is the evidence for the bullet's
   own conclusion that a two-item move is correct rather than thin.

**This is a pre-existing site that pass 1 missed, not a regression introduced by pass 2.** It is
raised now rather than deferred because the durable-file correctness standard this whole cycle turns
on cannot be applied to five sentences and withheld from a sixth in the same file, and because pass 2
newly asserts the universal form of the rule (see Low below), which this line falsifies.

Medium, not Low: it is a stated count *and* a superlative, both false, inside the sentence that
justifies the move's size, in a durable file. The conclusion it supports survives — spec-007 is
among the smallest specs, and the "almost no deliberative layer / rendered snapshot of a Kanban card"
argument is independent of the superlative.

Recommended change: drop the superlative and attribute the figures, e.g. "This is one of the smallest
specs in the repository — 2,282 bytes and 65 lines at `947f7494`, before this pass, and zero fenced
code blocks". No other prose is affected; the entry at line 101 already carries the comparison data
and needs no change.

### Low:

#### `### Notes for Worker 1` item 3 over-claims universal attribution

`docs/builder/bld-007-r1-rationale_move.md` `## Perform record (Worker 1, pass 2 — apply-changes)`
`### Notes for Worker 1 (spec reconciliation)` item 3 (line 1239).

It reads "**Every present-tense measurement in the rationale is now attributed to a commit.**"
Enumerated mechanically — every `<number> (bytes|lines|entries|times|rows|...)` occurrence in the
rationale:

```text
 24: 2,282 bytes, 65 lines            unattributed, and stale on disk  (the Medium above)
101: 007 (2,282 bytes), 011 (1,797)…  unattributed
216: 1,003 lines and 117,358 bytes    "at HEAD"      -> attributed
286: 100,289 bytes across 437 lines   unattributed   (true at HEAD: wc -lc CHANGELOG.md -> 437 100289)
319: 50,075 / 50,195                  at their commits -> attributed (this pass's M2 fix)
```

The instruction the item gives R2/R3 is right; the claim that the file already satisfies it is not.
Low because the forward-looking instruction is what R2 will act on, and every unattributed figure
except line 24 is currently true. Fix: restate as "the two figures finding 2 touched are now
attributed; lines 24, 101 and 286 are not yet" — or close it by attributing them, which is one edit
each.

#### Finding-4's edit left a 157-character line where the file wraps at ~100

`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` line 256, inside
`### `## Scope` 3 ...`. The only lines over 110 characters in the whole file are 1 (the title, 123),
352 (115, pre-existing) and this one (157) — the L4 edit appended the `## Quick comparison` clause
without re-wrapping. The same pass explicitly re-wrapped the L3 bullet onto three lines for the same
reason, so this is an inconsistency within one pass rather than a house-style question. No checker
enforces prose wrap in `.md`, hence Low. Fix: re-wrap the paragraph.

### Rulings requested by pass 2's `### Notes for Worker 3`

#### The `ARTIFACT.md` tension: Worker 1's reading is correct, and the result is legible enough

`ARTIFACT.md` `## Re-pass sections` says the artifact "reads as a linear pass / review / pass /
review sequence; never edit prior entries" — an unqualified prohibition with no correctness
carve-out, and the reason is that a re-pass that rewrites history destroys the evidence a later
auditor needs to see *that* the figure was wrong. Overwriting "seven" with "eight" in
`### What moved, and what stayed` would have erased the single most useful fact in this cycle: that a
pass which corrected five of someone else's numbers got one of its own wrong. **Stating the
supersession in a section this pass owns is the right reading, and I would have filed the in-place
edit as a finding.** No finding here.

On legibility: adequate, not ideal. Both superseded figures are enumerated with their exact section
locations under an unmissable heading, the pass's `### Notes for Worker 3` points at it, and the next
reader is Worker 1 at final verification, which is the reader best placed to hold both. Recommended
but not required, and satisfiable without touching any prior section: one line in the header block
beneath `Status:` reading "Superseded figures: see `### Corrections to this artifact's own prior
sections` (pass 2)". Routed to `### Notes for Worker 1` below rather than filed as a finding.

#### The declined DRY collapse: declination accepted

`BUILD.md` `## Subagent dispatch` step 4 closes a finding that is "intentionally rejected with a
recorded reason", and this one is recorded twice on disk with a real reason: an arithmetic-correction
pass that also restructures two sections hands the re-review a diff where the correctness edits are
the minority. Pass 1 itself routed it as "a judgement call, not required for acceptance". The overlap
is real and I re-read both sections to confirm it (`## How to read this file` bullets 3-6 against
`## Provenance of this record`), and the observation survives in `### Notes for Worker 1` item 4,
which is where it belongs — the two sections' next author has the authorship reason this pass lacked.
**Accepted as declined; it does not block acceptance and I am not re-filing it.**

#### Artifact size: not a rule violation, and still usable — with one caveat

69,668 -> 90,029 bytes (1,312 lines) for five one-line fixes. The corpus ratchet binds `BUILD.md`,
`ARTIFACT.md` and the four role files, none of which this cycle touches, so no rule is broken and
pass 2's reading of that is correct. As the contract Worker 1 reads at final verification it still
works: the pass-2 section is self-contained, its `### Findings closed` is one block, and its ticks
re-audit is at the end. The caveat is the one the supersession mechanism creates — the artifact now
states "seven" at line ~175 and "eight" at line ~1106, 930 lines apart — which is the whole reason
the header-line pointer above is worth the one line it costs.

### DRY findings

- No new duplication. Pass 2 added no section, no helper, no convention, and no link definition; its
  edits are five in-place corrections in one file.
- The one live DRY observation is the declined overlap, ruled on above and carried in
  `### Notes for Worker 1` item 4. Not re-filed.
- **Existence challenge: not raised.** Nothing was introduced this pass that could carry one.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged. No package source was touched by pass 2 or by this review.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. (`git status --short` carries no `CHANGELOG.md`
entry; `wc -lc CHANGELOG.md` matches `git show HEAD:CHANGELOG.md` exactly at `437 100289`.)

### Validation run (this pass)

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md docs/builder/bld-007-r1-rationale_move.md
(no output)
exit=0
```

Both reproduce pass 2's quoted results. The 1-anchor carrier
`[optimizer behavior][glossary-djangooptimizerextension]` is still in `## Scope` bullet 2, untouched
by both passes, and is what the first check's single term resolves through. The three spec anchors
the rationale links to (`#card-snapshot`, `#scope`, `#other`) still exist.

### Failability-proof audit

`None owed, and its absence is correct.` Pass 2 introduced no boundary, guard, gate, or rejection
path — it corrected five factual statements in one Markdown file. Boundary count: zero, so the
mandatory re-run floor is computed over an empty set and the empty re-run set is legal. No mutation
was made and none was licensed; the source carve-out was not used. The mechanical checks above are
claim verification, not failability proofs, and are not offered as substitutes.

### Hot-path budget verification

`Not applicable; plan declares no hot path.` Re-confirmed against the plan preamble
(#"Hot-path declaration: none"), not against this artifact's echo. No number is owed and none is
missing.

### Floor verification

`Not applicable; plan declares floor-verification scope none.` Re-confirmed against the plan
preamble. No Django / Strawberry / channels seam is touched.

### Static helper use

`scripts/review_inspect.py` **not run, and recorded rather than skipped silently**: it inspects
Python AST and repeated string literals, and this pass wrote no `.py` file. `docs/shadow/` was not
written to by this review. No temp test was created (`docs/builder/temp-tests/` is empty for this
slice) — every suspicion this pass had was settled by a one-command derivation.

### What looks solid

- **M2 was fixed by anchoring rather than substituting**, which is the harder and correct call: the
  entry's claim is that `81e4704d` restored deleted content, and 50,075 -> 44,596 would have read as
  a 5,479-byte loss. The added sentence naming both figures' commits is the file's own thesis applied
  to itself.
- **Every closure re-derived from the primary source**, not from pass 1's finding: pass 2 read the
  kanban DB rather than the plan or the review, which is what caught that the plan is *also* the
  origin of the one Low that propagated unchecked (D8).
- **The spec really is untouched.** The strongest single check in this pass, because the failure mode
  it excludes — an apply-changes pass quietly performing R2's reconciliation — would be nearly
  invisible in a 90KB artifact.
- **The five edits are exactly five.** The +483/+4 delta reconciles against the five edit sites read
  individually; nothing else in the file moved.
- **Nothing in the tree was reverted**, and the five `rev-*.md` deletions and `review-0_0_14.md` were
  left exactly as escalated.

### Notes for Worker 1 (spec reconciliation)

Extends the two prior instances of this section; nothing in either is retracted, and everything
routed to R2/R3 by any prior pass still stands.

1. **New, and the reason this pass is `revision-needed`:** `## How to read this file` line 24 calls
   spec-007 "the smallest spec in the repository" (four smaller specs, all four named later in the
   same file) and states 2,282 bytes / 65 lines with no commit attribution, now stale against the
   post-move 2,365 / 62. One bullet, one edit; the Medium above carries the suggested wording.
2. **Pass 2's `### Notes for Worker 1` item 3 should not be carried forward as written** — lines 24,
   101 and 286 of the rationale still hold unattributed present-tense measurements. The instruction
   to R2/R3 is right; only the "every" is wrong.
3. **Recommended, not a finding, and it costs one line that touches no prior section:** add
   "Superseded figures: see `### Corrections to this artifact's own prior sections` (pass 2)" to this
   artifact's header block under `Status:`. Two figures in prior sections are knowingly wrong by
   design (`ARTIFACT.md` forbids editing them) and the corrections sit 930 lines downstream.
4. **The DRY collapse stays open and stays non-blocking**, as pass 2 declined it and this pass
   accepts the declination. Unchanged from item 4 of pass 2's list.
5. **When R2 disposes of `## Other`, the number it will meet is eight**, breakdown
   `why_it_matters` 1 + `files_touched` 5 + `note` 2, and the two `note` rows are not
   interchangeable — re-derived from the DB this pass, independent of pass 2's record.

### Working-tree churn observed during this review pass

Reported, never reverted (`AGENTS.md` rule 34). At the **open** of this pass `git status --short` was
byte-identical to the 17-entry block pass 2 recorded. At the **close** it carries **four new `M`
entries that this pass did not write and did not revert**:

```text
 M django_strawberry_framework/_boundary_ordering.py
 M django_strawberry_framework/middleware/request_body.py
 M examples/fakeshop/test_query/test_transport_api.py
 M tests/test_views.py
```

All four are package source / tests, all four are declared read-only for this whole cycle, and none
is reachable from a Markdown-only pass — they are a concurrent session's work appearing mid-review
(`START.md` "Concurrent sessions"). Not read for content, not reverted, not staged. Worker 0 should
append them to the baseline-dirty list for the remainder of this cycle so a later pass does not
mistake them for R1's. The 21-entry list is otherwise unchanged: the same 17 entries, no untracked
file added or removed. `HEAD` unchanged at `947f7494`, re-derived at the open and close of this pass;
no concurrent commit landed during it. The five `docs/review/rev-*.md` deletions remain escalated and
unresolved and were not touched; `docs/review/review-0_0_14.md` (`??`) was not touched; the
concurrent spec-006 cycle's four paths were not read for content and not touched. This review wrote
exactly two files: this artifact and `docs/builder/worker-memory/spec-007-worker-3.md`.

### Review outcome

**`revision-needed`.** All five dispatched closures held under independent re-derivation and none of
them regressed anything — the spec is byte-identical, the 16 link definitions are intact, both
checkers reproduce, and M2 in particular was repaired the right way rather than the obvious way. The
return is for one Medium and two Lows, all in the same shape as the closed findings and all in the
same file: a false superlative plus an unattributed, now-stale measurement in the rationale's
`## How to read this file`, an over-claiming forward note in this artifact, and one unwrapped line
left by the L4 edit. Per the plan's **Deviation 2 corollary** this routes to **Worker 1**, not
Worker 2.

`Status: revision-needed`

---

## Perform record (Worker 1, pass 3 — apply-changes)

Worker 3's re-review confirmed all five of pass 2's closures held, then returned one Medium and two
Low **new** findings — a pre-existing site both prior passes missed. Per the plan's **Deviation 2
corollary** the apply-changes pass is Worker 1's, not Worker 2's, and `Status:` is re-set to
`planned`, returning the artifact to the `planned` -> Worker 3 mapping.

Fresh invocation with no memory of either prior pass; the artifact on disk and the working-tree diff
were the record. `git rev-parse HEAD` -> `947f74948c16b20b0c15ff359bb53fbe462d4b8c`, re-derived at
the open and the close of this pass, unchanged. No `git stash` / `checkout` / `restore` / `worktree`
was used for any purpose; every before-state came from `git show <rev>:<path>` piped to `wc`.

**Prior sections are not edited** (`ARTIFACT.md` `## Re-pass sections`, and Worker 3 upheld that
reading explicitly: an in-place overwrite "would itself have been a finding"). Where this pass
corrects a claim a prior section makes, the correction is stated in
`### Corrections to prior sections (pass 3)` below and the prior text is superseded, not overwritten.

### Files touched

- `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` — **four edits**:
  the Medium's bullet rewritten and re-wrapped, two measurements attributed, one 157-character line
  re-wrapped. No section added, none removed, no link definition changed, no entry restructured.
- `docs/builder/bld-007-r1-rationale_move.md` — this pass section appended; `Status:` re-set to
  `planned`; the recommended one-line pointer added under `Status:`. **No prior section edited.**
- `docs/builder/worker-memory/spec-007-worker-1.md` — memory entry appended (gitignored).

**`docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` was NOT touched by this pass**,
and the plan's dispatch declared it non-writable for this pass. Proven mechanically rather than
asserted: `wc -lc` -> `62 2365`, and `git diff --shortstat` -> `1 file changed, 2 insertions(+), 5
deletions(-)` — R1's move and nothing else. A reconciliation rewrite remains R2's work.

### Findings closed

**Medium — `## How to read this file` called spec-007 "the smallest spec in the repository"; four
specs are smaller.** Re-derived independently over all **56** tracked `docs/SPECS/spec-*.md` at
`947f7494` (`git show HEAD:<path> | wc -c`, sorted ascending), rather than accepting the finding's
table:

```text
1618  spec-024-django_trac_37064_hardening-0_0_7.md
1651  spec-012-version_release_alignment-0_0_4.md
1669  spec-013-real_m2m_coverage-0_0_4.md
1797  spec-011-stale_placeholder_cleanup-0_0_4.md
2282  spec-007-onboarding_docs_spec_consolidation-0_0_4.md   <- fifth smallest
```

Two defects in one sentence, and both are fixed without weakening the argument the sentence exists to
carry. The **superlative** is replaced by the **class**: spec-007 is a card-snapshot stub and is
*among* the repository's smallest, with 011 / 012 / 013 / 024 named as smaller and the reader pointed
at the `### The preamble ...` entry that already carries their byte counts — so the two sites now
agree instead of contradicting each other 77 lines apart. The **measurement** is attributed and its
tense fixed: "measured 2,282 bytes, 65 lines and zero fenced code blocks at `947f7494`, before this
pass cut anything out of it". `wc -lc` on the spec reads `62 2365` post-move, so the pre-move figure
is now stated as a pre-move figure at a named commit rather than as a present-tense fact.

The conclusion survives intact, which was the constraint: the move is two items because the file is a
rendered Kanban-card snapshot with almost no deliberative layer, and that argument never needed the
superlative. Nothing in `### The preamble ...` was changed for this finding.

**Low — `### Notes for Worker 1` item 3 over-claimed universal attribution.** Pass 2 wrote "Every
present-tense measurement in the rationale is now attributed to a commit" in the same breath as the
fixes it describes — the failure mode `BUILD.md` `## Claims are proven mechanically` names ("a count
asserted in the same breath as the lesson it illustrates is routinely wrong", generalised here to a
completeness claim). **Closed by making it true rather than by narrowing it**, which is one edit per
site and leaves no forward-looking instruction weaker than it should be:

- `### The preamble ...` — "seven archived specs — 007 (2,282 bytes), 011 (1,797), ..." now reads
  "seven archived specs — measured at `947f7494`, 007 (2,282 bytes), ... and 007's figure is the
  pre-move one". All seven figures re-derived this pass from `git show HEAD:<path> | wc -c`:
  007 2282, 011 1797, 012 1651, 013 1669, 016 4558, 024 1618, 026 3593.
- `### `## Scope` 5 ...` — `"Condensed" is also no longer descriptive: 100,289 bytes across 437
  lines` now carries `at `947f7494``. Re-derived: `wc -lc CHANGELOG.md` -> `437 100289`, and
  `git show HEAD:CHANGELOG.md | wc -lc` matches, so the figure was true and is now attributable.

The remaining measurement sites were enumerated rather than assumed, and the enumeration — not a
universal — is what this pass claims. The rationale's five measurement sites now read:

```text
line  26      2,282 bytes / 65 lines            at 947f7494, stated as pre-move   (this pass)
line  104     seven sibling byte counts         at 947f7494                       (this pass)
lines 219-220 1,003 lines / 117,358 bytes       "at HEAD"                         (pass 1)
lines 290-291 100,289 bytes / 437 lines         at 947f7494                       (this pass)
lines 323-324 50,075 / 50,195 bytes             at their two commits              (pass 2)
```

One site is attributed to `HEAD` by name rather than by hash (219-220). That is attribution, not an
unanchored present-tense claim, and it was in scope for no finding; left as pass 1 wrote it, recorded
here so a later sweep does not read this enumeration as claiming five hash-anchored sites.

**Low — a 157-character line where the file wraps near 100.** Pass 2's L4 edit appended the
`## Quick comparison` clause to a line inside `### `## Scope` 3 ...` without re-wrapping, while
re-wrapping a neighbouring bullet for the same reason in the same pass. Re-wrapped the paragraph onto
three lines; **no word changed**. Verified by re-measuring the whole file rather than the one line:

```text
$ awk 'length($0)>110 {print NR": "length($0)}' <rationale>
1: 123      (the title, pre-existing)
357: 115    (pre-existing; was line 356 before this pass added one line above it)
```

The 157 is gone and no new line over 110 was created. The file's natural ceiling is 103 characters
(28 lines sit at 101-103); every line this pass wrote is at or under 102.

### Rulings applied, not re-opened

- **The `ARTIFACT.md` reading was upheld**, so prior sections are again left intact and the
  supersessions are stated in a section this pass owns.
- **The recommended one-line pointer was added** under `Status:` in the header block — the one change
  Worker 3 asked for that touches no prior section. It names both corrections sections, since this
  pass adds a second one, and says why the wrong figures are still there.
- **The declined DRY collapse stays declined**, with pass 2's recorded reason unchanged and Worker 3's
  acceptance of the declination recorded. This pass did not perform it and did not re-argue it; the
  observation survives in `### Notes for Worker 1` below.

### Corrections to prior sections (pass 3)

Stated here rather than by editing them, per `ARTIFACT.md` `## Re-pass sections`. This list is
cumulative with pass 2's — **neither of pass 2's two supersessions is retracted**, and both still
stand exactly as recorded there (`### What moved, and what stayed` reads "seven `## Other` bullets"
where the number is **eight**; `### Spec status-line re-verification` names
`::protect_done_card_glossary` where the symbol is **`::protect_done_card_glossary_link`**).

- `## Perform record (Worker 1, pass 2 — apply-changes)` `### Notes for Worker 1 (spec
  reconciliation)` item 3 states "Every present-tense measurement in the rationale is now attributed
  to a commit." **Superseded: that was false when written** — three sites (the `## How to read this
  file` figures, the seven sibling byte counts, and the `CHANGELOG.md` figures) were unattributed.
  All three are attributed as of this pass, so the sentence is true on disk now; it was not true then,
  and the *forward-looking instruction* the item gives R2 and R3 was always right and is unchanged.

### Byte and line counts, measured as each number was written

| File | Before this pass | After this pass | Delta |
|---|---|---|---|
| `docs/SPECS/appx/spec-007-…-rationale.md` | 29,075 bytes / 448 lines | 29,396 bytes / 453 lines | **+321 bytes**, +5 lines |
| `docs/SPECS/spec-007-…-0_0_4.md` | 2,365 bytes / 62 lines | 2,365 bytes / 62 lines | **0** — not touched |
| `docs/builder/bld-007-r1-rationale_move.md` | 110,307 bytes / 1,625 lines | 134,690 bytes / 1,990 lines *at the last write before this cell* | this section + the header pointer |
| `docs/builder/worker-memory/spec-007-worker-1.md` | 2,824 bytes / 34 lines | 4,073 bytes / 49 lines | one appended entry |

Every figure was read from `wc -lc` at the moment its cell was written, not carried from an earlier
reading — three of the four defects in the rationale have now been miscounted figures, and a count
copied from a prior paragraph is the exact mechanism. **This artifact's own after-figure is the one
count a self-measuring file cannot fully close**: it was measured after this section's body was
written and then grew by the two cells of this row plus this sentence, so the pass's return report
carries the final measurement. The two figures that matter to a reviewer — the rationale's and the
spec's — are exact and re-derivable. The rationale's +321 bytes buy: the rewritten
stub-class sentence with its attributed pre-move measurement, two `at `947f7494`` attributions, and
two re-wraps. No `--cov*` flag was used; no `pytest` was run (none is owed).

The corpus ratchet does not bind this pass: `BUILD.md` `## The corpus ratchet` scopes itself to
`BUILD.md`, `ARTIFACT.md`, and the four `worker-*.md` role files, none of which this pass touches.

### Validation run

Re-run by this pass, on every file it wrote, and quoted verbatim:

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md docs/builder/bld-007-r1-rationale_move.md
(no output)
exit=0
```

The 1-anchor constraint still holds by construction: the sole carrier
`[optimizer behavior][glossary-djangooptimizerextension]` is in `## Scope` bullet 2, which no pass in
this cycle has touched, and it is what the first check's single term resolves through. It remains
live for R2. The three spec anchors the rationale links to still resolve — `grep -n '^## '` on the
spec returns `## Card snapshot`, `## Scope`, `## Other`, matching `#card-snapshot` / `#scope` /
`#other`.

**No link definition broke, and the depth trap was re-checked rather than assumed.** All **16**
definitions in the rationale were re-resolved from `docs/SPECS/appx/` programmatically, each printed
with the repo-relative file it lands on; all 16 exist. No definition was added, removed, or
repointed by this pass — the count is unchanged from pass 2's 16, and `defined-but-unused` is empty.

```text
[root-readme]  ../../../README.md  -> README.md          (root)
[readme]       ../../README.md     -> docs/README.md     (docs/)
```

Two different existing files, and the masking spelling `../README.md` — which from `appx/` resolves
to `docs/README.md` rather than the root — appears nowhere in the file. All 10 canonical group
headers are present, in canonical order.

One `used-but-undefined` reference is reported by a naive scan and is **correct as written**:
`[optimizer behavior][glossary-djangooptimizerextension]` appears twice in the rationale, both times
**inside a code span**, quoting the spec's link rather than making one. `check_trailing_commas.py`
agrees (exit 0), and both occurrences predate this pass.

- `grep -nE '[A-Za-z_./-]+\.(py|md|csv|toml|html):[0-9]+'` -> **no match** in the rationale.
  `AGENTS.md` rule 27 holds in the durable file; the `line NN` references in this artifact are inside
  `bld-*.md`, where `START.md` permits raw positional refs.
- `uv run ruff format` / `ruff check --fix` — **not run, and correctly not run.** This pass touched
  no `.py` file.

### Failability proofs

`None; this pass introduced no new boundary.` It corrects three factual defects in one Markdown file
and adds no guard, gate, cap, or rejection path. Boundary count: zero. The mechanical re-derivations
above are claim verification and are not offered as substitutes for a failability proof.

### Hot-path budget

`Not applicable; plan declares no hot path.` Re-confirmed against the plan preamble
(#"Hot-path declaration: none") rather than this artifact's echo of it. No package source changed.

### Floor verification

`Not applicable; plan declares floor-verification scope none.` Re-confirmed against the plan
preamble (#"Floor-verification scope: none"). No Django / Strawberry / channels seam is reachable
from a Markdown-only pass.

### Implementation notes

- **The class replaced the superlative; the argument did not move.** The tempting minimal fix was
  "one of the smallest", which is true but says nothing. Naming the *card-snapshot stub* class is
  what the bullet was reaching for all along — the reason the move is two items is that the file was
  rendered, not deliberated — and pointing at the entry that already lists the four smaller specs
  makes the two sites corroborate instead of contradict, at no extra prose.
- **The over-claim was closed by attributing, not by narrowing.** Narrowing to "the two figures
  finding 2 touched are now attributed" would have left three rotting measurements in a file whose
  own thesis is that unattributed present-tense measurements rot. Two attributions cost 30 bytes and
  make the strong version true; the pass then claims the enumeration rather than the universal, so
  the next reader can re-derive it in one command.
- **`at HEAD` was left alone at lines 219-220.** It is attributed, no finding named it, and rewriting
  it would have been the fourth measurement edit in a pass whose mandate is three findings. Recorded
  in the enumeration so its shape is visible rather than silently counted as hash-anchored.
- **Re-wrapping was verified file-wide, not line-wise.** The L4 defect was created by editing one
  line and checking only that line, so this pass re-ran the over-110 sweep across the whole file
  before and after, and additionally measured the file's real ceiling (103) rather than assuming 100.

### Notes for Worker 3

- **Audit hardest that the spec is still untouched and that the four edits are exactly four.**
  `wc -lc` on the spec must read `62 2365` and `git diff --shortstat` `2 insertions(+), 5
  deletions(-)`; the rationale delta must reconcile to +321 / +5 across four edit sites and nothing
  else.
- **Two counts to re-derive from the primary source, not from this section.** The 56-spec sort that
  puts spec-007 fifth (`git show HEAD:<path> | wc -c` over `docs/SPECS/spec-*.md`), and the seven
  sibling byte counts now attributed in `### The preamble ...`. Both are one command each.
- **The measurement-site enumeration is the claim this pass would most like challenged.** It is
  offered as an enumeration precisely because pass 2's universal was wrong; if a sixth site exists,
  the enumeration is wrong in the same way and should be filed as such.
- **Prior sections were again deliberately not edited**, per the ruling Worker 3 returned. Pass 2's
  two supersessions and this pass's one are all stated in the two corrections sections, and the new
  header-block pointer under `Status:` now routes a reader to both.
- **New working-tree growth appeared during this pass** — one untracked `docs/review/rev-*.md`. See
  `### Working-tree churn and baseline growth`; it is not this pass's output and was not touched.
- **No temp test, no shadow file, no mutation, no DB write, no `pytest`.** `docs/shadow/` was not
  written to; the kanban DB was not read or written this pass (no finding required it).

### Notes for Worker 1 (spec reconciliation)

Extends the three prior instances of this section. **Nothing in any of them is retracted** except the
single sentence superseded in `### Corrections to prior sections (pass 3)` above, and everything
routed to R2 or R3 by any prior pass still stands — D1 discharged inside R1, D2 must not be "fixed",
D3 and the `## Card snapshot` question open, `## Scope` 6's fold-in tension as R2's highest-value
input, the role-versus-inventory split as the reconciliation strategy, the 1-anchor constraint live
for R2, `## Other` = **eight** with its two non-interchangeable `note` rows, and R3's
`CONTRIBUTING.md` / deferred-work items.

New from this pass:

1. **The plan carries the same false superlative, and this pass cannot fix it.**
   `### What R1 inherits` opens "Spec-007 is the **smallest spec in the repository**" — the origin of
   the rationale claim just corrected, propagated into the durable file unchecked. Four specs are
   smaller (011, 012, 013, 024). The plan is not writable by any worker, so this is **routed to
   Worker 0** for a seventh entry in `## Corrections to this table`. Its argument is unaffected: the
   inherited point is that spec-007 is a stub with possibly no deliberative layer, which the stub
   *class* establishes better than the superlative did.
2. **The measurement discipline is now enumerated, not universal.** Five measurement sites in the
   rationale, four hash-anchored and one `at HEAD` — the table is in `### Findings closed` above. If
   R2 or R3 adds a byte, line, or occurrence count to either file, anchor it to a commit hash and add
   it to that enumeration; do not restate a completeness claim over the file, which is the exact
   shape that failed twice in this cycle.
3. **This cycle has now produced three arithmetic defects in one durable file** (the `## Other`
   count, the spec-001 byte figure, the smallest-spec superlative plus its stale figures), every one
   of them a number asserted beside the lesson it illustrated. R2 rewrites far more of the spec than
   R1 moved out of it; the cheap prophylactic is to write no count into the spec that R2 has not
   measured in the same minute, and to prefer a form the reader can re-derive over a stated total.
4. **The DRY collapse stays open and stays non-blocking**, unchanged from pass 2 item 4 and Worker 3's
   acceptance of the declination. `## How to read this file` bullets 3-6 and `## Provenance of this
   record` still overlap; this pass touched bullet 4's prose for the Medium and deliberately did not
   restructure either section. The shorter of the two copies is still the one to collapse, and the
   owner is still whichever later pass has an authorship reason to rewrite them.
5. **The header-block pointer now exists**, so a reader arriving at an artifact this long learns in
   the header that two prior sections carry knowingly-wrong figures. If a fourth pass adds a third
   corrections section, extend that line rather than adding a second pointer.

### Working-tree churn and baseline growth

Reported, never reverted (`AGENTS.md` rule 34). `git status --short` at the close of this pass carries
**24 entries — three more than the 21 Worker 3 recorded**, and none of the three is this pass's:

```text
?? docs/review/rev-_boundary_ordering.md
 M docs/SPECS/spec-002-optimizer-0_0_2.md
 M docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
```

The **two spec-002 entries appeared between this pass's mid-point status read and its closing one** —
a spec-002 residual cycle running in a further concurrent session, editing an archived sibling spec
and its rationale companion. Neither path is in this cycle's writable set (which is spec-007's spec,
its rationale, the four `bld-007-*` artifacts, this plan, and the four namespaced memory files), both
are `docs/SPECS/` siblings this cycle is explicitly forbidden to touch, and neither is reachable from
any edit this pass made. **Not read for content, not touched, not reverted, not staged.** Their
existence is worth flagging for one reason beyond attribution: a sibling residual cycle is now
running concurrently with this one on the same convention, so R2 should expect the `docs/SPECS/appx/`
neighbourhood to keep moving and must not read a sibling rationale's mid-flight state as settled shape.

The `rev-*.md` entry is **newly untracked, written by a concurrent session, not read for content and
not touched.** It is
`rev-*.md`-shaped and its slug matches `django_strawberry_framework/_boundary_ordering.py`, one of the
four package-source files the third concurrent session is editing (the plan's
`### Third growth`). That is **additional circumstantial evidence** that the five ` D`
`docs/review/rev-*.md` deletions are a REVIEW cycle regenerating its own scratchpads rather than a
rule-22 violation — a session that deletes five `rev-*.md` and then writes a sixth is regenerating.
**No binding inference is drawn and the escalation stays open**: the five deletions are still 5
tracked at `HEAD` and 0 on disk, still not restored, still not reverted, and
`git checkout HEAD -- docs/review/` remains banned in this tree. Maintainer's call, unchanged.
Worker 0 should append all three entries to the baseline-dirty list as a fourth growth event.

The other 21 entries are byte-identical to the block Worker 3 recorded: the same 14 `M`/` D` tracked
entries — `KANBAN.html`, `KANBAN.md`, `examples/fakeshop/db.sqlite3`, the concurrent spec-006 spec,
this cycle's spec-007, the four concurrently-edited package-source / test files, and the five
`rev-*.md` deletions — plus the same 7 `??` entries. `docs/review/review-0_0_14.md` (`??`) was not
touched. The spec-006 cycle's four paths were not read for content and not touched.

**Attributable to this pass:** `docs/SPECS/appx/spec-007-…-rationale.md` (already `??` since R1) and
this artifact (already `??`). This pass added no new path to the tree.

**HEAD is unchanged at `947f7494`**, re-derived at the open and the close of this pass rather than
trusted from the plan or from a prior section. No commit landed during it, so nothing this cycle
wrote was swept into a concurrent commit.

### Residual-item checklist — re-audit of the ticks (pass 3)

Every box R1 ticked was re-checked against the file on disk this pass. **All seven ticks stand and
none is withdrawn.** The one Medium and two Lows were defects *inside* contracts that did land — a
false superlative inside the record, an over-broad forward note, an unwrapped line — never an
un-landed contract:

- The move is still a move: the spec is byte-identical to its post-R1 state (`62 2365`,
  `2 insertions(+), 5 deletions(-)`), and both moved passages are present in the rationale and absent
  from the spec.
- The record still names every entry by heading and anchor; all three spec anchors resolve.
- The five plan-row corrections are unchanged and were not re-litigated.
- The 1-anchor check and the before/after counts are re-run and re-recorded above.
- The 10-header scaffold and all 16 disk-resolved definitions re-verified, depth trap included.

The two open boxes stay open and are correctly open: Worker 3's audit (this pass hands back to it) and
Worker 1's final verification.

### Status

`planned`. Returns the artifact to the `planned` -> Worker 3 re-review mapping declared in the plan's
Deviation 2.

---

## Review (Worker 3, pass 3)

Fresh invocation with no memory of pass 1, pass 2, or either apply-changes pass. The artifact on disk
and the working-tree diff were the record; every number below was re-derived from the primary source
rather than read out of `### Findings closed`. `git rev-parse HEAD` -> `947f74948c16b20b0c15ff359bb53fbe462d4b8c`,
unchanged at the open and the close of this pass. No `git stash` / `checkout` / `restore` / `worktree`
was used; every before-state came from `git show HEAD:<path>` piped to `wc`.

The `Status:` pointer resolved: `### Corrections to this artifact's own prior sections` (line 1104)
and `### Corrections to prior sections (pass 3)` (line 1746) both exist and both were read. Pass 2's
two supersessions are intact and unretracted, as pass 3 states.

Scope of this pass is convergence, not a fresh sweep. The settled items — no fabricated deliberation,
the move is a genuine move, the 1-anchor carrier untouched, the `ARTIFACT.md` never-edit-prior-entries
reading, the declined DRY collapse — were not re-opened.

### The three closures, each re-derived from the primary source

**1. The false superlative -> the stub class. HELD, and the exhaustiveness is exact.** Re-sorted all
tracked `docs/SPECS/spec-*.md` at HEAD independently of pass 3's table:

```text
$ git ls-tree -r --name-only HEAD -- docs/SPECS | grep -E 'docs/SPECS/spec-[^/]*\.md$' | wc -l
56
1618  spec-024-django_trac_37064_hardening-0_0_7.md
1651  spec-012-version_release_alignment-0_0_4.md
1669  spec-013-real_m2m_coverage-0_0_4.md
1797  spec-011-stale_placeholder_cleanup-0_0_4.md
2282  spec-007-onboarding_docs_spec_consolidation-0_0_4.md   <- fifth of 56
```

Four specs are smaller and **exactly** four, so "011, 012, 013 and 024 are all smaller" is both true
and complete — the sentence cannot be read as an under-count. The class claim survives the move
itself: the spec is 2,365 bytes on disk post-move and is still fifth. The forward pointer resolves —
`### The preamble ...` does carry all four byte counts, so the two sites now corroborate at 77 lines'
distance instead of contradicting. The attributed figure checks out at the named commit:
`git show HEAD:<spec> | wc -lc` -> `65 2282`, and `grep -c '^```'` -> `0` fenced blocks both at
`947f7494` and on disk. The tense fix is real: 2,282 / 65 is now stated as a pre-move figure at a
named commit, and `wc -lc` on disk reads `62 2365`.

**2. The three unattributed measurement sites closed by attribution. HELD, all ten figures.** Every
sibling byte count re-derived from `git show HEAD:<path> | wc -c`: 007 **2282**, 011 **1797**,
012 **1651**, 013 **1669**, 016 **4558**, 024 **1618**, 026 **3593** — all seven match.
`wc -lc CHANGELOG.md` -> `437 100289` and `git show HEAD:CHANGELOG.md | wc -lc` matches, so
`100,289 bytes across 437 lines at 947f7494` is exact. The "seven archived specs" population was
verified rather than assumed: `grep -Fxc` on the full three-sentence paragraph at `947f7494` returns
**1** in each of 007, 011, 012, 013, 016, 024, 026 and **zero** in the other 49 specs — seven, and the
match is verbatim on the whole paragraph, not just its first sentence.

**3. The 157-character line. HELD, and verified file-wide rather than at the line.**

```text
$ awk 'length($0)>110 {print NR": "length($0)}' <rationale>
1: 123
357: 115
$ awk '{if(length($0)>m)m=length($0)} END{print m}'   -> 123 (line 1)
$ awk 'length($0)>=101 && length($0)<=103' | wc -l    -> 28
```

The 157 is gone, the ceiling outside the two pre-existing lines is 103, and 28 lines sit at 101-103 —
all three of pass 3's figures reproduce. Line 357 is pre-existing text (the `0c08204f` sentence in the
`## Other` entry), not something this pass wrote.

### Nothing regressed

- **Spec untouched.** `wc -lc` -> `62 2365`; `git diff --shortstat` -> `1 file changed, 2 insertions(+),
  5 deletions(-)`. The diff is R1's move and nothing else: the pointer sentence plus its link
  definition in, the boilerplate paragraph and the whole `## Planning note` section out. `## Scope`
  still has 6 bullets and `## Other` still has 8.
- **All 16 link definitions resolve, and to the right files.** Re-resolved programmatically from
  `docs/SPECS/appx/`, each printed with the repo-relative file it lands on; 16/16 exist, none added,
  removed, or repointed. **Depth trap holds:** `[root-readme] ../../../README.md -> README.md` and
  `[readme] ../../README.md -> docs/README.md` are two different existing files, and the masking
  spelling `../README.md` appears nowhere. All 10 canonical group headers present, in canonical order.
  `defined-but-unused` and `used-but-undefined` are both empty once code spans are stripped.
- **The three spec anchors resolve:** `grep -n '^## '` on the spec returns `## Card snapshot`,
  `## Scope`, `## Other`, matching `#card-snapshot` / `#scope` / `#other`.
- **`AGENTS.md` rule 27 holds in both durable files.**
  `grep -nE '[A-Za-z_./-]+\.(py|md|csv|toml|html):[0-9]+'` -> no match in the spec or the rationale.
- **The `Status:` pointer resolves** to two real headings (now three, with this pass's correction
  section below).
- **The delta reconciles across all three passes.** 28,592/444 (pass 1) -> 29,075/448 (pass 2, +483/+4)
  -> 29,396/453 (pass 3, +321/+5). Pass 3's before-cell is byte-identical to pass 2's after-cell, and
  `wc -lc` on disk now reads `453 29396`. Four edit sites, +5 lines: the bullet-4 rewrite (+1), the
  sibling-count attribution (+1), the CHANGELOG attribution (+1), the `## Scope` 3 re-wrap (+2).
- **Spot-checks on prior passes' present-tense claims, since the sentences around them were
  re-wrapped this pass.** All still true at HEAD: root README has exactly 8 `##` headings and
  `## Project documentation` has 8 entries; `docs/README.md` is `1003 117358`; `docs/GLOSSARY.md` has
  exactly one table separator (`## Index`, line 88); no file in the repository carries a
  `## Quick comparison` heading; `#### Other` renders zero times in `KANBAN.md`; card 7's rendered
  row carries three labels, `docs`, `internal`, `release`. The `2,495 deleted lines against 459 added`
  figure at `83c25963` reproduces exactly (`git show --shortstat` -> `25 files changed, 459
  insertions(+), 2495 deletions(-)`), and `231911a8` does touch only `CHANGELOG.md` and `KANBAN.md`.

### High:

None.

### Medium:

None. Specifically, the class the dispatch told me to hunt — a *new* unattributed present-tense
measurement, an over-broad claim, or a count that does not reconcile in the sentences pass 3 wrote —
produced no Medium. Every figure pass 3 wrote is anchored to `947f7494`, every one reproduces, the
one `at HEAD` site is disclosed as such, and the enumeration replaced a universal rather than
restating one.

### Low:

#### Pass 3's own parenthetical about line 357 is off by four

`docs/builder/bld-007-r1-rationale_move.md` `## Perform record (Worker 1, pass 3 — apply-changes)`
`### Findings closed` (line 1729) reads:

```text
357: 115    (pre-existing; was line 356 before this pass added one line above it)
```

The pass added **five** lines above it, not one, and pass 2's review recorded that same line at
**352** (`### Low:` #"352 (115, pre-existing)"). 352 + 5 = 357, which is what reconciles the delta;
356 reconciles nothing. The substantive claim the parenthetical supports — the line is pre-existing,
115 characters, and not created by this pass — is **true and independently verified**, so nothing in
the durable rationale is affected and no reader is misled about the file under audit.

Recorded, not routed for a fourth apply-changes pass: it is a parenthetical inside a per-cycle
`bld-*.md` scratchpad, it is superseded below by the same mechanism the cycle already uses for
knowingly-wrong prior figures, and one more spawn to change "one" to "five" would cost more than the
defect does. It is worth naming precisely because it is the **fourth** arithmetic slip in this cycle
and the third to land in the same shape: a number written beside the lesson it illustrates, in the
very sentence proving that this pass measured carefully.

#### The five-site measurement enumeration has a defensible boundary, and it should be stated

`### Findings closed` (lines 1709-1715) enumerates five measurement sites in the rationale. Pass 3
asked for this to be challenged, so: a sixth byte/line figure exists at rationale line 317, "2,495
deleted lines against 459 added" for `83c25963`. It is **not** a defect — it is exact and it is
inherently anchored, because a commit diffstat names its own commit in the same clause and cannot
rot. The enumeration is complete for the class that actually carries the risk (a **document's size**
measured at a point in time, which is what goes stale silently) and line 317 is a different class (a
**commit's diffstat**). The enumeration is therefore correct as scoped, and the scope is what was
left implicit. No edit requested; R2 and R3 should read the enumeration as "file-state size
measurements", which is the class its forward instruction governs.

#### The re-wraps left three ragged short lines

Rationale lines 105 (58 chars), 261 (57), 291 (11), each the tail of a paragraph pass 3 re-wrapped or
extended. No word changed and no checker enforces prose wrap in `.md`, so this is house-style only.
One of them has a small readability cost worth naming: at line 104-105 the inserted clause "and 007's
figure is the pre-move one" now sits between the byte list and the sentence "It carries no fact about
this card", so "It" has a nearer antecedent (the figure) than the one it means (the boilerplate
paragraph). The following sentence — "Removing it from this one file makes spec-007 diverge from its
siblings" — disambiguates it immediately. Cosmetic; a future author with a reason to touch that
paragraph can tidy the wrap in passing.

### Correction to pass 3 (this pass)

Stated here rather than by editing pass 3's section, per `ARTIFACT.md` `## Re-pass sections` and the
ruling pass 2's review returned. Cumulative with pass 2's two supersessions and pass 3's one, **none
of which is retracted**:

- `## Perform record (Worker 1, pass 3 — apply-changes)` `### Findings closed` says line 357 "was line
  356 before this pass added one line above it". **Superseded: it was line 352, and the pass added
  five lines above it.** The conclusion it supports — the 115-character line is pre-existing and was
  not created by this pass — is unaffected and independently verified.

### Notes carried for R2, not filed as findings

- **"The phrase survives on exactly three surfaces ... There is no fourth occurrence"** (rationale
  lines 214-217, pass 1's text) is now literally falsified by this cycle's own files: `grep -rln
  'three-minute'` returns `KANBAN.md`, `KANBAN.html`, the spec, **the rationale itself**, the plan,
  and this artifact. The claim's load-bearing half — that no *section* by that name ever existed, and
  that the three real surfaces are renders of one `CardItem` — is true and verified. This is the
  self-reference every "this phrase occurs N times" claim carries, both prior passes saw the sentence,
  and rewriting it to exclude the file making the claim would be worse prose for no gain. If R2 rewrites
  `## Scope` bullet 2 it will change the count again, so R2 should prefer "no section by that name
  exists" over an occurrence total.
- **The plan's seventh correction landed and matches.** `### What R1 inherits` still opens with the
  false superlative, and the plan's `## Corrections to this table` now carries a seventh entry
  recording it with exactly the figures I re-derived (fifth of 56, behind 1,618 / 1,651 / 1,669 /
  1,797). Worker 0's propagation is on the record and the section's argument is unaffected. One
  cosmetic oddity, Worker 0's to fix or leave: the seventh entry is written *above* the sixth.

### DRY findings

- No new duplication. Pass 3 added no section, no link definition, no convention, and no heading; its
  four edits are in-place corrections and re-wraps in one file.
- The declined collapse (`## How to read this file` bullets 3-6 against `## Provenance of this
  record`) stays declined, per pass 2's recorded reason and my predecessor's acceptance of it. Pass 3
  touched bullet 4's prose for the Medium and correctly did not restructure either section — doing so
  in an arithmetic-correction pass is exactly the diff-legibility problem the declination cites. It
  survives in `### Notes for Worker 1` item 4. Not re-filed.
- **Existence challenge: not raised.** Nothing was introduced this pass that could carry one — no
  helper, registry, indirection, or new abstraction, in any file.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged, and no pass in this cycle has touched any file under `django_strawberry_framework/`.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify `CHANGELOG.md`. It is read-only to this cycle
(`AGENTS.md` rule 21) and is `git diff`-clean; the rationale only *measures* it.

### Documentation / release sanity

Applicable — this cycle's whole deliverable is documentation. Confirmed:

- No version string, shipped/planned status, or card ID changed. The spec's `Status:` line, target
  release `0.0.4`, and card `DONE-007-0.0.4` are byte-identical to HEAD, and no `pyproject.toml` /
  `__init__.py` version is in play.
- No KANBAN card moved; `KANBAN.md` and `KANBAN.html` are baseline-dirty from a concurrent session and
  were not read for content beyond the card-7 render used to re-verify the three labels.
- Every Markdown link introduced or moved by the cycle points at a file that exists on disk: the
  spec's one new `[spec-007-rationale]` definition, and all 16 in the rationale.
- The archive is unaffected: the spec stays at `docs/SPECS/`, its companions at `docs/SPECS/appx/`,
  and `SpecDoc.path` needed no repoint.
- No "coming soon" / "planned" / stale-version wording was introduced. The one instruction that could
  not be followed ("expand it into the full builder-format spec") is out of the spec and recorded in
  the rationale inside an entry stating it is false.
- No script-rendered doc was regenerated by this cycle (`docs/TREE.md`, `docs/GLOSSARY.md`,
  `KANBAN.md` all untouched by it), so the staging-docstring check has no subject.
- **DONE-card chain re-run rather than trusted**, since a concurrent session writes the DB:
  `uv run python examples/fakeshop/manage.py import_spec_terms --check` ->
  `OK: 49 done cards have glossary links.` (exit 0).
- **Staged-anchor sweep re-run as the backstop:**
  `grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' .` -> the only hits are the plan's own
  prose *describing* the sweep. Zero real anchors tree-wide.

### Validation run (this pass)

Re-run by me on the written files, quoted verbatim:

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md docs/builder/bld-007-r1-rationale_move.md
(no output)
exit=0
```

The 1-anchor constraint still holds and is still live for R2: the sole carrier
`[optimizer behavior][glossary-djangooptimizerextension]` is in `## Scope` bullet 2, which no pass in
this cycle has touched, and it is what the first check's single term resolves through. `ruff format` /
`ruff check` were not run and correctly not run — no `.py` file was touched. No `pytest`, no `--cov*`.

### Failability-proof audit

`None owed; R1 introduced no boundary.` The diff is Markdown prose in two files plus this artifact: no
guard, gate, cap, limit, permission decision, or rejection path exists to mutate. Boundary count zero,
so the mandatory re-run floor computes to an **empty re-run set, legally** (`worker-3.md`: "an empty
re-run set is legal only when the diff introduces no boundary that meets the floor"). Pass 3's
`### Failability proofs` block correctly says the same and correctly declines to offer its mechanical
re-derivations as a substitute. Boundaries re-run: **none**. Boundaries accepted on the performer's
record: **none — there are none to accept.**

### Hot-path budget verification

`Not applicable; plan declares no hot path.` Re-confirmed against the plan preamble itself
(#"Hot-path declaration: none"), not against this artifact's echo of it. No number is owed, and the
absence of one is correct rather than a missing-number finding.

### Floor verification

`Not applicable; plan declares floor-verification scope none.` Re-confirmed against the plan preamble
(#"Floor-verification scope: none"). No Django / Strawberry / channels / django-filter seam is
reachable from a Markdown-only change, so no floor run is owed.

### Static helper use

`scripts/review_inspect.py` **not run, and the skip is recorded with its reason**: it inspects Python
modules for repeated literals and import boundaries, and this pass's subject is two Markdown files.
`docs/shadow/` was neither read nor written. No shadow-file line number is cited anywhere in this
section.

### Temp test verification

No temp test was created; `docs/builder/temp-tests/` was not written to. Nothing in this pass is a
behavior question a test could settle — every claim is a byte count, a line count, an occurrence
count, or a path resolution, and each was settled by one command whose output is quoted above. No
mutation of any source file, no DB write.

### What looks solid

- **The closure chosen for the Medium was the right one.** Replacing the superlative with the
  *card-snapshot stub class* keeps the argument the sentence exists to carry — the move is two items
  because the file was rendered, not deliberated — and it makes the two sites corroborate. "One of the
  smallest" would have been true and empty.
- **Closing the over-claim by attributing rather than narrowing** is the disciplined choice. Narrowing
  would have left three rotting figures inside the one file whose thesis is that unattributed
  present-tense measurements rot, at a saving of 30 bytes.
- **Replacing a universal with an enumeration** is the correct structural response to a universal that
  was wrong twice, and it is re-derivable in one command, which is why I could challenge its boundary
  in a Low rather than having to guess at it.
- **The re-wrap was verified file-wide and the ceiling measured rather than assumed** (103, not the
  100 the earlier finding guessed at). That is precisely the discipline whose absence created the
  157-character line in the first place.
- **The `ARTIFACT.md` supersession mechanism is working as intended.** Three corrections now sit in
  sections their own passes own, the header pointer routes a reader to all of them, and the cycle's
  most useful evidence — that each pass corrected numbers and then wrote one of its own wrong — is
  still legible in place instead of overwritten.
- **The prohibitions held under audit, not just in prose.** The spec is byte-identical to its post-R1
  state, no baseline-dirty out-of-scope path was edited or reverted, no `git stash` / `checkout` /
  `restore` / `worktree` was used, and nothing was committed.

### Notes for Worker 1 (spec reconciliation)

Extends all four prior instances. **Nothing in any of them is retracted**, and everything routed to R2
or R3 still stands: D1 discharged inside R1, D2 must not be "fixed", D3 and the `## Card snapshot`
question open, `## Scope` 6's fold-in tension as R2's highest-value input, the role-versus-inventory
split as the reconciliation strategy, the 1-anchor constraint live for R2, `## Other` = **eight** with
its two non-interchangeable `note` rows, the enumerate-don't-universalise measurement discipline, the
non-blocking DRY collapse, and R3's `CONTRIBUTING.md` / deferred-work items.

New from this pass:

1. **What final verification inherits is clean.** The rationale is fit to be the durable record: every
   figure in it is either anchored to `947f7494` or disclosed as `at HEAD`, every one reproduces from
   the primary source, all 16 links resolve to the intended files, and the depth trap holds. The spec
   is untouched and awaiting R2 at `62 2365` / `2 insertions(+), 5 deletions(-)`. Audit the ticks
   against that, not against this section.
2. **One supersession is added, in `### Correction to pass 3 (this pass)` above** — the line-357
   parenthetical. Three corrections sections now exist and the header pointer names all three. A
   fourth pass should extend that line rather than add a pointer.
3. **The measurement enumeration's class is now stated** (file-state size measurements; a commit
   diffstat is a separate class and rationale line 317 is one). If R2 or R3 adds any count to either
   file, anchor it to a hash and extend the enumeration; do not restate a completeness claim over the
   file. That shape has now failed twice in this cycle.
4. **The count-beside-the-lesson failure mode is now 4 for 4 in this cycle**, and every instance has
   been a number written in the same sentence as the point it proves. R2 rewrites far more of the spec
   than R1 moved out of it. The cheap prophylactic stands: write no count into the spec that R2 has not
   measured in the same minute, and prefer a form the reader can re-derive to a stated total.
5. **A sibling residual cycle is running concurrently on `docs/SPECS/`** (spec-002's spec and rationale
   went dirty during pass 3; spec-006's are dirty too, and the rationale's `[spec-006-rationale]`
   definition points at a file that currently exists only **untracked**). It resolves on disk today and
   the sibling cycle is expected to land it, but R2 and R3 should re-resolve that one definition rather
   than assume it, and must not read a sibling rationale's mid-flight state as settled shape.

### Working-tree churn observed during this review pass

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` -> **24 entries**, byte-for-byte
the same 24 pass 3 recorded, re-read at the open **and** the close of this pass. **No growth this
pass, and no new path.** HEAD unchanged at `947f7494` at both reads, so nothing this cycle wrote was
swept into a concurrent commit.

The unresolved escalation is unchanged and stays open: the five ` D docs/review/rev-*.md` deletions are
still 5 tracked at `HEAD` and 0 on disk, still not restored, still not reverted;
`git checkout HEAD -- docs/review/` remains banned in this tree; maintainer's call.
`docs/review/rev-_boundary_ordering.md` and `docs/review/review-0_0_14.md` (both `??`), the two
spec-002 paths, the spec-006 cycle's four paths, `KANBAN.md` / `KANBAN.html`,
`examples/fakeshop/db.sqlite3`, and the four concurrently-edited package-source / test files were
**not read for content** — except `KANBAN.md`'s card-7 render, read read-only to re-verify the
three-label claim — **not touched, not reverted, not staged.**

**Attributable to this pass:** this artifact only (already `??`).

### Convergence judgement

**Converged. Accepting.** Three review rounds on a prose file is a lot, and the stopping condition is
met: all three of pass 3's closures held under independent re-derivation from the primary source, no
new defect exists in the durable rationale, and the residue is one off-by-four parenthetical inside a
per-cycle scratchpad plus two matters of scope-statement and wrap taste. None of them would mislead a
reader of the durable record, which is the bar the dispatch set for `revision-needed`.

The arithmetic favours stopping. This file's own evidence is that each apply-changes pass has closed
its findings and introduced one new defect in the same shape; a fourth pass to change "one" to "five"
in a parenthetical would carry that same risk against a defect that misleads nobody. The correction is
instead recorded above by the mechanism this cycle already uses for knowingly-wrong prior figures,
which discharges it without a spawn. I did not manufacture a finding to justify the pass, and I did
not withhold one that matters: the Medium tier is empty because the sentences pass 3 wrote are
correct, not because I stopped looking — I enumerated every byte/line figure in the file and
re-derived all ten, plus six present-tense occurrence claims from prior passes whose surrounding
prose this pass re-wrapped.

### Review outcome

`review-accepted`. All three of pass 3's findings closed and re-derived as held; one Low superseded in
place by this section's correction, two Lows recorded as notes and intentionally not routed with the
reason recorded above; no High or Medium. Routes to Worker 1 for **final verification** — the
rationale is fit to be the durable record, the spec is untouched and awaiting R2, and the notes for R2
and R3 are on disk and accurate.

---

## Final verification (Worker 1)

Fresh invocation with no context from the planning, perform, or apply-changes passes. The artifact on
disk and the working-tree diff were the record; **every count below was re-derived from the primary
source rather than read out of any prior section**, per `BUILD.md` `## Claims are proven mechanically,
never accepted on prose`. `git rev-parse HEAD` -> `947f74948c16b20b0c15ff359bb53fbe462d4b8c`,
re-derived rather than trusted from the plan's preamble. No `git stash` / `checkout` / `restore` /
`worktree` was used for any purpose; the pristine before-state came from
`git show HEAD:docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` into a scratch path
**outside** the repository, then `diff`.

The `Status:` pointer resolved to all three named sections — `### Corrections to this artifact's own
prior sections` (pass 2), `### Corrections to prior sections (pass 3)`, and `### Correction to pass 3
(this pass)` inside `## Review (Worker 3, pass 3)`. All three were read before any prior figure was
evaluated, so no superseded number was mistaken for a live one.

### Spec status-line re-verification (every Worker 1 spawn)

Spec lines 1-5 re-read first. Title, target release `0.0.4`, and owner are accurate against the live
card (`DONE-007-0.0.4`, `status.key done`, read-only ORM). The `Status:` line still describes an
executable constraint rather than self-narration, and all four guards it rests on resolve at their
**correct** names, re-derived this pass:

```text
$ grep -n 'def protect_done_card\|def _validate_done_card' examples/fakeshop/apps/kanban/signals.py
143:def _validate_done_card_has_spec(
148:def _validate_done_card_has_glossary_link(
404:def protect_done_card_spec(
450:def protect_done_card_glossary_link(
```

**No status-line edit was needed and none was made.** The build has falsified nothing in lines 1-5.

### Mechanical re-verification (re-derived, not accepted)

| Claim under audit | Command | Result | Verdict |
|---|---|---|---|
| spec byte-identical at `2,365 B / 62 L` | `wc -lc` | `62 2365` | **held** |
| spec diff against HEAD | `git diff --shortstat` | `1 file changed, 2 insertions(+), 5 deletions(-)` | **held** |
| spec pre-move size | `git show HEAD:<spec> \| wc -lc` | `65 2282` | **held** |
| rationale at `29,396 B / 453 L` | `wc -lc` | `453 29396` | **held** |
| the move is a CUT, not a copy | `diff` of the pristine HEAD copy against the working tree | three hunks: line 7 replaced, lines 18-21 deleted, one link definition added — 3 removed non-empty lines, 2 added | **held** |
| both moved passages absent from the spec | `grep -c` on the spec | `intentionally lightweight` 0; `Planning note` 0 | **held** |
| both moved passages present in the rationale | `grep -c` on the rationale | 2 and 4 | **held** |
| 16 link definitions, all resolving | programmatic resolution from `docs/SPECS/appx/`, printing the repo-relative target | 16/16 exist | **held** |
| depth trap intact | same resolution | `[root-readme] ../../../README.md -> README.md`; `[readme] ../../README.md -> docs/README.md`; **no definition spelled `../README.md`** | **held** |
| 10 canonical group headers, canonical order | header scan | `Root, docs/, docs/SPECS/, docs/builder/, django_strawberry_framework/, tests/, examples/, scripts/, .venv/, External` | **held** |
| no dangling / orphan reference | code-spans stripped, used-vs-defined differenced | `used-but-undefined` empty, `defined-but-unused` empty | **held** |
| three spec anchors resolve | `grep -n '^## '` on the spec | `## Card snapshot`, `## Scope`, `## Other` -> `#card-snapshot` / `#scope` / `#other` | **held** |
| no raw `path:NN` in either durable file | `grep -nE '[A-Za-z_./-]+\.(py\|md\|csv\|toml\|html):[0-9]+'` | no match in the spec, no match in the rationale | **held** |
| zero fenced blocks in either durable file | `grep -c '^```'` | 0 and 0 | **held** |
| `## Scope` = 6 bullets, `## Other` = 8 bullets on disk | section-scoped bullet count | 6 and **8** | **held** |
| `## Other` = 8 from the live DB, breakdown | read-only ORM | `items 14 Counter({'scope': 6, 'files_touched': 5, 'note': 2, 'why_it_matters': 1})` | **held** |
| card 7 carries three labels | read-only ORM | `['docs', 'internal', 'release']` | **held** |
| `card.planning_note` empty | read-only ORM | `''` | **held** |

Both checkers re-run by this pass on every durable file, quoted verbatim:

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md docs/builder/bld-007-r1-rationale_move.md
(no output)
exit=0
```

The 1-anchor constraint held and, as every pass has said, held **by construction**: the sole carrier
`[optimizer behavior][glossary-djangooptimizerextension]` sits in `## Scope` bullet 2, which the diff
proves untouched by every pass in this cycle. It is live for R2, not for R1.

**Every measurement site in the rationale re-derived independently**, since the pass-2 universal was
wrong once and an enumeration is only as good as its figures:

```text
line 26      2,282 B / 65 L at 947f7494    git show HEAD:<spec> | wc -lc  -> 65 2282        exact
line 104     seven sibling byte counts     007 2282 / 011 1797 / 012 1651 / 013 1669 /
                                          016 4558 / 024 1618 / 026 3593                   all seven exact
lines 219-20 1,003 L / 117,358 B at HEAD   wc -lc docs/README.md -> 1003 117358             exact
lines 290-91 100,289 B / 437 L at 947f7494 git show HEAD:CHANGELOG.md | wc -lc -> 437 100289 exact
lines 323-24 50,075 -> 50,195 at their two 83c25963^ -> 50075; 81e4704d -> 50195;
             commits                       HEAD -> 44596 (correctly NOT the figure used)    exact
line 317     2,495 deleted / 459 added     git show --shortstat 83c25963 -> 25 files
             at 83c25963                   changed, 459 insertions(+), 2495 deletions(-)    exact
```

**Chronology and commit facts spot-checked at the sites the argument leans on**, all holding:
`231911a8` 2026-05-08 (release) and `81e4704d` 2026-06-01 (creation) — the creation-after-release
chronology the stub-shape entry rests on; `40c1855f` 2026-05-20, twelve days after the release, message
exactly "housekeeping: rename files" (so the entry's refusal to invent a reason is correct); `2baf93b5`
2026-06-09, eight days after the render; `1592bb90` 2026-07-09; the three board-migration commits
`0c08204f` / `ac7cc6a4` / `4f68d3f2` all 2026-07-20, seven weeks after `81e4704d`; `grep -c '^####
Other$' KANBAN.md` -> **0**; `docs/GLOSSARY.md` carries exactly **one** table separator row; no file in
the repository carries a `## Quick comparison` heading. The `## Scope` 1 entry's thirteen-heading
enumeration is **exact and complete** — `git show 231911a8:README.md` carries precisely those thirteen
operational headings and four others (`## Project documentation`, `## Quick start`, `### Schema setup
boundary`, `## Contributing & Security`), and `2bd7cb84` takes the six top-level ones from 6 to 0.

### R1's contract was delivered

`BUILD.md` `## Spec rationale extraction` is the contract, and each of its clauses is discharged:

- **It is a MOVE.** The `diff` against pristine HEAD is the proof, not the perform record: the two
  passages are gone from the spec and present in the rationale, and nothing was duplicated into both or
  dropped from both. This is the one claim in the item that could not have been repaired later, and it
  is clean.
- **It is keyed to the spec.** All **eleven** entries under `## Entries keyed to the spec` open with an
  explicit `Spec:` or `Bears on` line naming the section by heading and linking its anchor, and all
  three anchors resolve. The two entries whose sections the move removed (`### The preamble …`,
  `### `## Planning note` …`) say so and re-anchor to `## Card snapshot` rather than dangling. No entry
  in the file names no decision, which is the condition `BUILD.md` says makes an entry worthless.
- **The fourteen drift rows map onto the eleven entries with nothing dropped**, re-checked row by row:
  D1 -> the preamble; D2 -> `Status:`; D3 -> `## Card snapshot`; D4 -> `## Planning note`; D5 -> Scope 1;
  D6 -> Scope 2; D7+D8 -> Scope 3; D14 -> Scope 4; D9 -> Scope 5; D10 -> Scope 6; D11+D12+D13 -> `## Other`.
- **The record clause is where the value is**, as the plan predicted, and it is measured rather than
  asserted: five of six `## Scope` bullets carry a "claim the spec no longer makes" paragraph, and the
  role-versus-inventory split in `## Standing note` is derived from them rather than stated over them.

**Where the rationale is thin — said plainly, because this is my own item.**

- **The "alternatives rejected" clause is thin file-wide.** Only two of eleven entries carry a rejected
  alternative (`### The preamble …`'s three-way expand / delete / keep argument, and `### `## Scope` 6
  …`'s delete-on-fold-in reversal), and a third (`### `## Scope` 3 …`) explicitly declines to invent
  one. That is the correct outcome for a rendered card snapshot, and the plan's `### What R1 inherits`
  pre-decided it ("an imagined alternative is worse than a missing one"), so it is **thinness by
  contract rather than by omission**. But a reader arriving at this file expecting the usual density of
  a `-rationale.md` should be told which clause carries the weight here: it is the change record, not
  the alternatives.
- **Two entries carry none of the three clauses in force.** `### `Status:` — the one-to-one invariant is
  real` and `### `## Scope` 4 — the one claim that held` record, respectively, a correct sentence and a
  provenance gain. Neither moves text, rejects an alternative, or retires a claim. They are legitimate —
  the first exists precisely to stop R2 tidying an accurate sentence that reads like self-narration, and
  the second is the only place the script-generation of `docs/TREE.md` is recorded against this spec —
  but they are the two entries that would look weakest to an auditor counting clauses, and I am naming
  them rather than letting the count read as uniform.
- **The declined DRY collapse is real and still open.** `## How to read this file` bullets 3-6 and
  `## Provenance of this record` genuinely overlap on four facts. I re-read both sections and confirm
  the overlap; I also confirm the declination's reason (an arithmetic-correction pass that restructures
  two sections hands its re-review a diff where the correctness edits are the minority). **Not blocking
  and not re-opened here** — a final-verification pass restructuring prose is the same mistake in a
  worse position, since no reviewer follows me. It carries forward as recorded.

### No `### Spec slice checklist (verbatim)`, and that is correct

Confirmed by reading rather than by inventing boxes: `grep -n '^## '` on the spec returns exactly
`## Card snapshot`, `## Scope`, `## Other` — **there is no `## Slice checklist` to copy from**, and R1
is a residual item rather than a spec slice. The artifact carries
`### Residual-item checklist (plan item R1, verbatim)` in that position instead, decomposed from the
plan's R1 checklist line, which is the same substitution `BUILD.md` `### Dispatched findings checklist`
makes for a review round.

Audited against the plan's `### Residual scope` R1 description and `### What R1 inherits` rather than
against a checklist the spec does not have:

- "the honest reading of *move* on a 2.3KB stub … decided in advance rather than left to the mover" —
  **delivered**; the move is two passages, stated plainly in three places, and the file is not padded.
- "a rationale file is owed the RECORD … fourteen claims the spec makes and can no longer make" —
  **delivered** as the eleven-entry mapping above.
- "do not fabricate rejected alternatives" — **delivered**; the one argumentative passage is labelled as
  this pass's argument and every constraint it rests on is checkable at HEAD (I re-checked all three:
  the four guards, the chronology, the seven-stub population).
- "the stub's own existence is the most valuable rationale entry available" — **delivered**, and it is.
- "do not duplicate the siblings, and do not restate the causing cards' reasoning" — **delivered**; the
  causing commits are named as causes and never argued.

**Tick audit.** All seven ticked boxes were re-checked against the files on disk this pass and **all
seven stand** — each one's contract landed, and the four defects the review rounds found were errors
*inside* landed contracts rather than un-landed contracts. The two boxes left open were future-pass
markers, and both contracts have now landed: Worker 3's audit ran three times and closed
`review-accepted`, and this section is the final verification. **Both are ticked in place**, which
`ARTIFACT.md` `### Spec slice checklist (verbatim)` assigns to Worker 1 at final verification
explicitly ("tick any landed box Worker 2 left open") — it is the one edit to the Plan section the
artifact contract authorizes, and it is not the never-edit-prior-entries prohibition this cycle has
otherwise held to. No box is un-ticked, so no deferral reason is owed under
`### Spec changes made (Worker 1 only)`.

### Ruling on the three review rounds' residue

I agree with Worker 3 on all three, and on the convergence judgement. Each was re-derived before being
signed off, not accepted on the review's word.

1. **The line-357 parenthetical (off by four).** Re-derived: pass 2's review recorded the 115-character
   line at **352**, pass 3 added **five** lines above it, and `awk 'length>110'` on disk reports
   `1: 123` and `357: 115`. So `352 + 5 = 357` reconciles and "356 … one line above" does not. **Agreed:
   non-misleading and no revision needed.** It is a parenthetical inside a per-cycle `bld-*.md`
   scratchpad that closes with this cycle (`START.md` "Temp artifact conventions"), the substantive
   claim it supports — the line is pre-existing and 115 characters — is true and independently verified,
   and it is already superseded in place by `### Correction to pass 3 (this pass)`. **Nothing in either
   durable file is affected.** Superseding it was the right disposition; routing a fourth spawn at it
   would not have been.
2. **The five-site enumeration omitting rationale line 317.** Re-derived: line 317's figure is exact
   (`git show --shortstat 83c25963` -> `459 insertions(+), 2495 deletions(-)`), and the commit is named
   in the **same sentence** as the diffstat, so it cannot rot the way a document-size measurement rots —
   there is no later state for it to disagree with. **Agreed: a different class, and the enumeration is
   correct as scoped.** Two things strengthen the ruling beyond Worker 3's statement of it: the
   enumeration lives in a per-cycle artifact rather than in the durable file, so it binds only this
   cycle's forward instruction; and the class boundary is now stated on disk, which is what a later
   sweep needs. Recorded for R2/R3 below rather than edited.
3. **Three ragged short lines plus the antecedent drift at line 105.** Re-derived: lines 105 (58
   characters), 261 (57), 291 (11) are paragraph tails, and no line in the file exceeds 110 except the
   title (123) and the pre-existing 357 (115). No checker enforces prose wrap in `.md`
   (`check_trailing_commas.py --check` exits 0 on the file). On the antecedent: at 104-105 the inserted
   clause "and 007's figure is the pre-move one" does sit between the byte list and "It carries no fact
   about this card", so "It" has a nearer wrong antecedent — but the next sentence ("Removing **it** from
   this one file makes spec-007 diverge from its siblings") disambiguates immediately, and the paragraph's
   own topic sentence names the boilerplate paragraph as its subject. **Agreed: cosmetic, non-misleading,
   recorded not edited.** `worker-1.md` and this pass's dispatch both prefer recording to editing at
   final verification, and re-wrapping a paragraph in the pass that no one reviews is how a fifth
   arithmetic slip would enter this file.

**On the convergence argument: I agree, and the arithmetic is the reason.** Every apply-changes pass in
this cycle closed its dispatched findings and introduced exactly one new defect in the same shape. A
fourth spawn to change "one" to "five" in a scratchpad parenthetical would carry that demonstrated risk
against a defect that misleads nobody, and the supersession mechanism discharges it at zero risk.
Worker 3 also did not stop looking to justify stopping — it enumerated every byte/line figure and
re-derived all of them, and I re-derived them again independently and found no sixth defect. Three
rounds is the right number to have run and the right number to stop at.

**What caused three rounds, recorded so the next residual cycle inherits it rather than repeating it.**
Three of the four defects were **numbers**, and the fourth was a **completeness claim about numbers**:

- The `## Other` bullet count (seven for eight) — a new error, written while correcting five of the
  plan's rows, and sitting *inside* the sentence claiming its own accounting exhaustive.
- The spec-001 byte figure — correct at its commit, asserted in the present tense, inside the file whose
  thesis is that present-tense content claims rot.
- The "smallest spec in the repository" superlative plus its stale unattributed figures — **propagated
  from the build plan's `### What R1 inherits`**, unchecked, and contradicted by the file's own data 77
  lines later.
- Pass 2's "every present-tense measurement is now attributed" — a universal asserted in the same pass
  as the fixes, false at three sites.

Two of the three number defects **originated in the plan** (D8's "two tables", and the smallest-spec
superlative) and reached the durable file by being copied rather than re-derived. The instructive shape
is not carelessness; it is that **the same pass that re-verifies someone else's figures is the pass
least likely to re-verify its own**, and that a count written in the sentence using it as evidence is
the exact site of the failure. The prophylactic, for R2/R3 and for the next residual cycle:

1. **Re-derive every plan-sourced figure before it enters a durable file**, without exception, including
   the ones the plan states twice — the plan is a verified floor, not a source.
2. **Never write a count in the sentence that uses it as evidence.** Measure it in its own command at
   the moment of writing, and prefer a form the reader can re-derive to a stated total.
3. **Never write a completeness claim in the same pass as the fixes it describes.** Close it by making
   it true and then claiming the **enumeration**, never the universal.

### Ruling on the untracked `[spec-006-rationale]` target

Worker 3 routed this forward as a genuine judgement call, and it is one. The facts, re-derived:
`docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` **resolves on disk** and
`git ls-files --error-unmatch` on it returns "Did you forget to 'git add'?" — untracked. Its sibling
`[spec-005-rationale]` is tracked. During this pass a further path appeared,
`docs/builder/bld-006-r2-spec_reconciliation.md` (`??`), so the spec-006 cycle has reached its R2.

**Ruled: accepted, with the reason recorded, AND noted for R3's archive audit — both, not either.**

A durable file may carry a link definition whose target is uncommitted when three conditions hold, and
all three hold here:

1. **The target resolves on disk at the time of writing**, verified by resolution rather than by
   assumption, and the scaffold checker passes over the file.
2. **The target is authored by a cycle demonstrably in flight against the same convention and into the
   same directory** — spec-006's residual cycle, now at R2, writing the `-rationale.md` companion that
   `AGENTS.md` rule 26 and `BUILD.md` `## Spec and build-plan filename pattern` both name as a tracked
   sibling. The target is not speculative; it exists and its author is mid-cycle.
3. **Both files enter the maintainer's commit window together.** This cycle's own rationale is likewise
   `??` right now. Neither cycle commits; the maintainer commits this working tree, so **this cycle
   cannot cause a dangling definition to be committed by acting alone.** The failure mode requires the
   maintainer to commit spec-007's rationale while discarding spec-006's — which is a maintainer choice,
   not a defect this item can introduce.

What would make it unacceptable is a definition pointing at a file nobody has written — a forward
promise dressed as a link. That is not this case. Rewriting the definition out was also weighed and
rejected: the sentence it serves ("the sibling narrates the documentation *discipline* this card's doc
set was arranged under") is the single-ownership law working correctly — pointing rather than retelling —
and dropping the link to avoid a transient tracking asymmetry would trade a real DRY property for a
bookkeeping one.

**Condition for reversal, recorded for R3:** R3's archive audit re-resolves this one definition. If the
target is gone by then, the definition **and its one use site** come out in R3, in the same edit. If it
is tracked by then, nothing is owed. Either way R3 records the re-resolution rather than inheriting this
ruling as settled.

### What R2 is left, confirmed on disk

`### Notes for Worker 1 (spec reconciliation)` exists in **six** instances (the R1 perform record and
all three apply-changes / review pairs), each cumulative and each stating explicitly that nothing prior
is retracted. I read all six and re-verified their substantive items rather than accepting them:

- **D1 is discharged inside R1, not deferred** — the falsified "expand it into the full builder-format
  spec" instruction is absent from the spec (`grep -c` -> 0) and present in the rationale inside an entry
  stating it is false. R2 verifies absence.
- **D2 must not be "fixed"** — all four guards resolve at their correct names (re-derived above).
- **D3 and the `## Card snapshot` section question are open and unpatched** — the DB reads three labels,
  the spec says two, and both dispositions are correctly R2's.
- **`## Scope` 6's fold-in tension is R2's highest-value input** — re-verified: `83c25963` deleted six
  named specs (2,495 deletions / 459 insertions) and `81e4704d`, the commit that created this spec file,
  restored all six.
- **The role-versus-inventory split is the reconciliation strategy**, and it is measured.
- **The 1-anchor constraint is live for R2 and untested so far** — the carrier bullet is the prose R2 is
  most likely to rewrite. Re-site in the same edit; re-run the checker before setting any status.
- **`## Other` = eight**, breakdown `why_it_matters` 1 + `files_touched` 5 + `note` 2, with the two
  `note` rows non-interchangeable — re-derived from the DB this pass, independent of every prior record.
- **The measurement discipline is an enumeration, not a universal**, and its class is file-state size
  measurements; a commit diffstat is a separate class.
- **R3's items** — `CONTRIBUTING.md`'s dangling `BUILD.md` "Spec filename pattern" citation as a
  maintainer follow-up; the root README's `## Project documentation` being eight **bullets** not a table;
  the staged-anchor sweep and `import_spec_terms --check` as R3's own re-runs; the
  `[spec-006-rationale]` re-resolution ruled above.

**Every one of the six instances is accurate as written**, with the single exception already superseded
on disk (pass 2's item 3 universal). Nothing in them needed correcting by this pass, and R2 can act on
them without re-deriving them — though the enumerate-don't-universalise lesson says it should re-derive
anyway.

### Plan rows this pass's reading shows wrong — for Worker 0

**None.** I re-checked every drift row against the rationale's corrected version and against source,
and the seven corrections already appended to the plan cover every discrepancy I can find. Two
observations for Worker 0 that are **not** drift-row corrections:

- **The seventh correction is written above the sixth** in `## Corrections to this table`, as Worker 3
  noted. Cosmetic; Worker 0's to leave or reorder.
- **The plan carries raw `path:NN` references** (`KANBAN.md:4794` at D6 and in
  `### The read-only correctness audit`, `KANBAN.md:140`, `:4783` in `### Every reference TO spec-007`).
  `AGENTS.md` rule 27 permits raw `path:NN` in per-cycle scratchpads and its list names
  `docs/builder/bld-*.md` — **not** `docs/builder/build-*.md`, which is committed alongside the build.
  This is **not** a spec-007 defect and not this cycle's to fix: six committed `build-*.md` plans carry
  the same shape (`build-046` carries 23), so it is either an established practice rule 27's list does
  not enumerate or a standing-doc gap. **Recorded for the maintainer, no edit anywhere.**

### DRY check across this item and the cycle

- **No new duplication.** R1 created one file, added no convention, no helper, and no shared shape; the
  cycle has landed no source. The one duplication the item *retired* is real and verified: the moved
  preamble's first two sentences said what the spec's `Status:` line says, and only the `Status:` line
  says it now.
- **No cross-file duplication with the siblings**, re-confirmed: neither the `FEATURES.md` ->
  `GLOSSARY.md` rename chain nor the fold-in reversal appears in any other `docs/SPECS/appx/*rationale.md`.
- **The declined collapse stays declined**, ruled on above.
- **Existence challenge: not raised.** Every `##` section in the rationale records something found
  nowhere else, and `## Standing note` in particular is the durable home for analysis the plan carries in
  a file that closes with the cycle — that direction of movement is correct, not duplication.

### Existing tests still pass

**No `pytest` was run and none is owed.** This item's diff is two Markdown files; there is no focused
test scope the plan calls for, and `worker-1.md` `## Scope` plus the plan's declarations put the full
`## Final test-run gate` in `bld-007-final.md`, not here. No `--cov*` flag was used anywhere in this
pass. `ruff format` / `ruff check` were not run and correctly not run — no `.py` file was touched.

### Failability, fail-open, hot-path, and floor confirmations

- **Failability proofs: none owed, and the empty block is correct rather than a gap.** R1 introduced no
  boundary, guard, gate, cap, or rejection path — it moved prose between two Markdown files — so
  `BUILD.md` `### What needs a proof, and what does not` does not attach. Confirmed by reading the diff,
  not by reading the artifact's echo. `None; this pass introduced no new boundary.` appears in all three
  perform records, which is the right entry.
- **No fail-open shape landed.** There is no expression in the diff to fail open: the entire diff is
  Markdown prose. The catalogued shapes have no possible site here.
- **Hot-path: `Not applicable; plan declares no hot path.`** Re-confirmed against the plan preamble
  itself (#"Hot-path declaration: none"), not against the artifact's echo. **No before/after number is
  owed and its absence is correct**, not an omission — nothing in the diff runs per request, per
  resolver, per row, per connection, or per outbound message.
- **Floor verification: `No floor-verification scope declared.`** Re-confirmed against the plan preamble
  (#"Floor-verification scope: none"). No floor venv was built by any pass, none is owed by this item,
  and none is owed by the final gate on R1's behalf. The floor versions are not restated here; their
  single canonical home is `BUILD.md` `## Floor verification` and this item never needed to read it.

### Working-tree churn and baseline growth — FIFTH growth event

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` at the close of this pass
carries **25 entries — one more than the 24 Worker 3 recorded**, and the new one is not this pass's:

```text
?? docs/builder/bld-006-r2-spec_reconciliation.md
```

The concurrent **spec-006 residual cycle has reached its R2** and created that cycle's second artifact.
It is `bld-006-`-prefixed, outside this cycle's writable set by name, and unreachable from anything this
pass wrote. **Not read for content, not touched, not reverted, not staged.** Worker 0 should append it to
the plan's `## Baseline-dirty out-of-scope files` as a fifth growth event. It also corroborates the
plan's fourth-growth note: the two dirty `docs/SPECS/spec-002-*` paths are that cycle's coordinated
`## Visibility status` retirement reaching more inbound sites, not a fifth session.

The other 24 entries are unchanged. **The five ` D docs/review/rev-*.md` deletions remain ESCALATED and
UNRESOLVED** — still 5 tracked at `HEAD`, still 0 on disk, still not restored, not reverted, not touched;
`git checkout HEAD -- docs/review/` remains banned in this tree and rule 34 independently forbids the
auto-revert. `docs/review/rev-_boundary_ordering.md` and `docs/review/review-0_0_14.md` (both `??`) are
further circumstantial evidence that a REVIEW cycle is regenerating its own scratchpads, and **no binding
inference is drawn**: maintainer's call, unchanged. The four concurrently-edited package-source / test
files, `KANBAN.md` / `KANBAN.html`, `examples/fakeshop/db.sqlite3`, the spec-002 pair, and the spec-006
cycle's five paths were not read for content — except card 7's row via a read-only ORM query — and were
not touched.

**Attributable to this pass:** this artifact only (already `??`), plus the gitignored memory file. **No
durable file was edited by this pass**: the rationale still reads `453 29396` and the spec `62 2365`,
both byte-identical to the state Worker 3 accepted.

**HEAD unchanged at `947f7494`**, re-derived at the open and the close. Proven not swept rather than
assumed: `git log --stat` over this cycle's paths shows the three most recent commits touching
`docs/SPECS/` or `docs/builder/` are `947f7494`, `4e9b9c31`, and `570cd670`, **none of which touches
spec-007 or its rationale** — the tip commit's three files are spec-047's rationale and two `-terms.csv`
renames. `git status` alone was not relied on.

### Residual-item checklist — final audit of the ticks

All nine boxes are now `- [x]`. Seven were ticked by R1 and **all seven stand** under this pass's
re-derivation, each contract confirmed landed against the files on disk and the DB rather than against
any prior section: the move is a cut; the record is keyed by heading and anchor with all three anchors
resolving; the fourteen drift rows were re-verified and five corrections recorded (a seventh followed);
the 1-anchor check was re-run and quoted; before/after counts were recorded; the 10-header scaffold and
all 16 disk-resolved definitions verified with the depth trap intact. The two remaining boxes are ticked
by this pass because their contracts have now landed — Worker 3's audit closed `review-accepted` after
three passes, and this section is the final verification. **No box is over-ticked and none is silently
un-ticked**, so nothing is owed under `### Spec changes made (Worker 1 only)`.

### Summary

R1 delivered the contract `BUILD.md` `## Spec rationale extraction` sets. The spec's deliberative layer —
a boilerplate preamble paragraph and a `## Planning note` section rendering a discarded database value —
was **cut** into `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`, proven
against pristine HEAD rather than asserted, and the spec grew 83 bytes while losing three lines because
the rule-1 pointer is longer than the boilerplate it replaced — reported openly rather than shaved. The
substance is not the two-passage move but the **record**: eleven entries keyed to the spec by heading and
anchor, covering all fourteen verified drift rows, establishing that five of six `## Scope` claims were
true the day they were written and are false, uncheckable, or superseded now — each with the commit or
board change that did it. The single most valuable finding is that `## Scope` 6's fold-in-by-deletion
policy was **reversed by `81e4704d`, the very commit that created this spec file**. Three review rounds
were needed, and every defect they found was a miscounted or unattributed figure inside a durable file —
two of them propagated from the build plan. The spec is byte-identical to its post-move state and awaits
R2; the rationale is fit to be the durable record of the `0.0.4` documentation history, which is the only
place that history exists.

### Spec changes made (Worker 1 only)

**None.** The spec was not edited by this pass and correctly was not: R1's contract was the move, which
landed; reconciliation is R2's, and editing the spec here would leave R2 reviewing my own edits. Proven
mechanically rather than asserted — `wc -lc` -> `62 2365` and `git diff --shortstat` -> `1 file changed,
2 insertions(+), 5 deletions(-)`, byte-identical to the state R1 produced and Worker 3 accepted three
times. The `docs/SPECS/appx/…-rationale.md` file was likewise **not** edited: the three residue items
were rulings and records, and `worker-1.md` plus this pass's dispatch both prefer recording to editing at
final verification. Every box in the residual-item checklist is `- [x]`, so no deferral reason is owed.

### Final status

`final-accepted`.
