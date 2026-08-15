# Build: R3 — finish the documentation and audit the archive

Spec reference: `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` (57 lines, whole file)
Rationale reference: `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`
Plan reference: `docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md`
Status: final-accepted

## Which shape this item took, and why

**Not** the procedural-closure shape the plan predicted. `docs/builder/BUILD.md`
`### Procedural-closure slices` licenses a single self-closing Worker 1 pass only when the item's
contract is to ship nothing, and the plan's own conditional is explicit: "**R3 is expected to be a
procedural-closure item** … If R3's own audit finds writable drift, it runs the full unmodified chain
instead, and Worker 1 says which shape it took in the artifact."

The audit found writable drift, in the rationale. So this item takes the **full chain** —
`planned` → Worker 3 audit → Worker 1 final verification — and `Status:` is set to `planned` rather
than `final-accepted`. One durable-file edit landed and it is not self-closed. The reason the
dispatch gives is the operative one: every one of this cycle's nine apply-changes passes introduced a
defect while closing findings, and a durable-file edit made in a self-closing pass is exactly what
should not go unreviewed.

Per the plan's **Deviation 2** the `built` state does not exist for a Worker-1-exclusive deliverable,
and `planned` is what Worker 0 reads as "dispatch Worker 3".

---

## Plan (Worker 1)

### What R3 had to establish

The dispatch names seven obligations. They are answered in `## Audit findings` below, in the same
order, each with the command that produced its answer.

### DRY analysis

- **Helper inventory checked.** Not applicable in the package-wide AST sense and the absence is
  correct, not a skip: `worker-1.md` `### Package-wide helper inventory before helper planning`
  gates *helper-like logic*, and this item proposes none. No package source is writable in this
  cycle (plan, `## Build-wide context flags`), no `.py` file is read or written, and the item's whole
  output is one Markdown correction plus this artifact. The inventory would answer a question nothing
  here asks.
- **Existing patterns reused.** The correction reuses the disposition this cycle earned twice
  already and recorded on disk both times: **anchor a rotted measurement to the state it measured,
  never swap in the HEAD number** (R2 pass 2's M2 fix; R2's final verification L5 fix). No new shape
  was invented for it.
- **New helpers justified.** None.
- **Duplication risk avoided.** The naive repair — restating the surface count at its HEAD value —
  would have re-created the defect one edit later, because the set it counts is one this cycle is
  still changing. The second naive repair — cross-referencing the reconciliation record's own
  deletion sentence from the extraction entry — would have put the same fact in two places in one
  file, which is the plan's `DRY rule` and `## The single-ownership law` clause 1 in miniature.
  Neither was taken.

### Implementation steps

1. Run the read-only audit in full before writing anything (`## Audit findings`).
2. Correct the one falsified statement in
   `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`, `## Scope` 2
   entry, anchoring the count to the state it measured.
3. Name the correction on disk in the file's own closing corrections section, so the append-only
   record stays auditable.
4. Re-run `check_spec_glossary.py`, `check_trailing_commas.py --check` on both durable files, and
   `import_spec_terms --check`.
5. Write this artifact; record the deferred-work material the final gate needs.

### Test additions / updates

None, and the absence is correct. No `pytest` runs in this pass (dispatch: "no `pytest` in this
pass"; `--cov*` forbidden). The item writes one Markdown file and reads the rest.

### Implementation discretion items

None. The one judgement this pass had — whether the falsified count is repaired by anchoring or by
restatement — is a decided architectural call, recorded under `### DRY analysis`, not delegated.

### Dispatched findings checklist

R3 has no spec `## Slice checklist` and is not a review round; its contract is the plan's `### Residual
scope` R3 clause plus the dispatch's seven obligations. Those are the boxes.

- [x] The durable docs describe the doc set the shipped card actually produced (obligation 1)
- [x] The archive is complete in all three cross-reference directions — outbound, inbound, companion
      (obligation 2)
- [x] The terms-CSV / DONE-card chain is intact (obligation 3)
- [x] The staged-anchor sweep, run with a stated exclusion and a stated true result (obligation 4)
- [x] The known maintainer follow-ups are catalogued, not fixed (obligation 5)
- [x] `[spec-006-rationale]`'s untracked target re-resolved now (obligation 6)
- [x] "Make sure the code is correct" stated plainly as discharged or not (obligation 7)

---

## Audit findings

Every figure, path, heading, and count below was measured by its own command in this pass. Nothing is
carried from the plan, from R1, or from R2 — those are verified floors, not sources.

HEAD re-derived at the open and the close: `947f74948c16b20b0c15ff359bb53fbe462d4b8c`, unchanged. No
`pytest` ran, no `--cov*` flag was passed, no `git stash` / `checkout` / `restore` / `worktree` was
used, nothing was committed, no branch was created, and **no DB write was made or is owed**.

### Spec status-line re-verification

Lines 1-7 read first, checked against the live DB and the file they point at:

- `Target release: 0.0.4 (per KANBAN.md card DONE-007-0.0.4)` — live DB reads `card_id`
  `DONE-007-0.0.4`, `status.key` `done`, `target_version.number` `0.0.4`. Holds; no edit.
- `Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant
  intact` — holds; the stub is still the `SpecDoc` target (`card.spec.path` reads the archived path).
  No edit.
- `Owner: package maintainer` — holds; no edit.
- The line-7 rationale pointer names the change record and the claims the spec may no longer make.
  This pass extended that record rather than falsifying it. No edit.

### 1. Do the durable docs describe the doc set the shipped card produced?

**Yes.** Re-verified rather than inherited from the plan's audit. Direction rule applied as the
dispatch states it: where the spec disagreed with a durable doc, the spec is what moved, and R2 has
already moved it — this pass re-ran the check, it did not re-run R2.

`README.md`'s `## Project documentation` map, and whether its targets resolve:

```text
$ for id in readme glossary goal today tree kanban backlog contributing; do ... done
OK   [readme] -> docs/README.md
OK   [glossary] -> docs/GLOSSARY.md
OK   [goal] -> GOAL.md
OK   [today] -> TODAY.md
OK   [tree] -> docs/TREE.md
OK   [kanban] -> KANBAN.md
OK   [backlog] -> BACKLOG.md
OK   [contributing] -> CONTRIBUTING.md
```

Eight bullets, eight targets, all resolving on disk. `grep -n '^## ' README.md` returns **eight**
`##` headings — Why this package exists, Why it's fast, Is this for you?, Status, the `docs/README.md`
pointer, Project documentation, Inspired by, Contributing & Security — none of them an operational
step, which is what the spec's bullet 1 asserts.

Every role the reconciled `## Scope` assigns, checked against the file it names:

| Spec bullet | Checked by | Result |
|---|---|---|
| root `README.md` — map, positioning, status, pointers into the rest of this set | `grep '^## '`; the eight map targets resolved above; `## Contributing & Security` carries `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md` | **holds** — all five other files in the set are pointed at |
| `docs/README.md` — installation, quick start, running the example project, runtime behavior | `## Installation` (7), `## Quick start` (16), `## Running the example project` (852), `## Nested connection indexing` (175) | **holds** |
| `CONTRIBUTING.md` — setup, tests, formatting, versioning, build, publish | `## Getting started` (15), `## Running the test suite` (25), `## Linting and formatting` (33), `## Updating the package version` (42), `## Building` (51), `## Publishing` (59) | **holds** — all six |
| `docs/GLOSSARY.md` — one stably anchored entry per catalogued capability | the file's own line 3 self-description; the `## \`DjangoOptimizerExtension\`` heading present | **holds** |
| `docs/TREE.md` — detailed layout and test-tree reference | the file's own line 3: "This file is the detailed layout reference" | **holds** |
| `CHANGELOG.md` — the release record | line 3: "All notable changes to this project will be documented in this file" | **holds** |
| `## Card snapshot` — board fields belong to the DB and render into `KANBAN.md` | `KANBAN.md` card 7 block renders Priority `Medium`, Status `Done`, Relative size `S`, Labels `docs`/`internal`/`release`, plus the `#### Scope` / `#### Files likely touched` rows | **holds** |

**Nothing a durable doc is missing.** The dispatch's "finish the documentation" half asks whether a
durable doc lacks something the reconciled spec now says. It does not: every role the spec assigns
is present in the file it assigns it to, and the one claim the spec makes about a *destination*
(`CONTRIBUTING.md` owning the operational half the root README shed) resolves in full.

### 2. The archive, in all three cross-reference directions

**Outbound — the spec's and rationale's links resolve.** Each definition expanded to an absolute path
from its own file's directory and disk-checked:

- **Spec: 10 definitions, 10 resolve.** `[changelog]`, `[contributing]`, `[kanban]`, `[root-readme]`
  (all `../../` → repository root), `[glossary]`, `[glossary-djangooptimizerextension]`, `[readme]`,
  `[tree]` (all `../` → `docs/`), `[spec-007-rationale]` (`appx/…`), `[build]` (`../builder/`).
- **Rationale: 15 definitions, 15 resolve.** Including the two fragment-bearing spec anchors
  `#card-snapshot` and `#scope`, both of which match the spec's only two `##` headings.
- **The depth trap re-resolved per file**, not trusted from either prior artifact. From `docs/SPECS/`:
  `../../README.md` → root `README.md`, `../README.md` → `docs/README.md`. From `docs/SPECS/appx/`:
  `../../../README.md` → root `README.md`, `../../README.md` → `docs/README.md`. Both files'
  `[root-readme]` and `[readme]` land where their names claim.

**The three changes R2 made to this direction, each re-checked:**

1. **The retired `[backlog]` definition.** `grep -n 'backlog\|BACKLOG'` on the spec → **no match**;
   the spec now points at `BACKLOG.md` nowhere. That is intended, not rot — the definition had no use
   site. The **rationale** still defines and uses `[backlog]` (`../../../BACKLOG.md`, resolving), so
   the spec-007 pair as a whole has not stopped referencing it.
2. **The seven new spec definitions** — `[changelog]`, `[contributing]`, `[root-readme]`,
   `[glossary]`, `[readme]`, `[tree]`, `[build]`. All seven resolve, verified in the outbound run
   above.
3. **`#other` removed as an anchor.** Swept for any reference to it anywhere:
   `grep -rn '#other'` over `*.md` / `*.py` / `*.csv` / `*.html` returns hits in **this cycle's own
   `bld-007-r1` and `bld-007-r2` scratchpads only** — passes narrating the anchor's existence and its
   retirement — and `grep -rn 'spec-007-other'` adds only the rationale's own code-span narration of
   the retirement at line 564. **No durable file carries a live `#other` link, and none dangles.**
   `grep -c '^## Other'` on the spec → **0**.

**Inbound — `KANBAN.md` / `KANBAN.html` / `SpecDoc.path`.** All three point at the archived path:

```text
KANBAN.md:140   [spec-007-…-0_0_4.md](docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md)
KANBAN.md:4783  - Spec: [spec-007-…-0_0_4.md](docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md)
KANBAN.html:97  the same path inside the payload
SpecDoc.path    docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
```

`KANBAN.md` / `KANBAN.html` are generated and were **read only**. No DB write was made.

**No sibling spec references spec-007**, re-swept rather than inherited: the only files carrying the
string `spec-007-onboarding_docs_spec_consolidation` are `KANBAN.md`, `KANBAN.html`, the spec, the
rationale, this cycle's own plan and artifacts, and **three out-of-scope concurrent-session files** —
`docs/review/review-0_0_14.md`, `docs/builder/build-006-public_surface-0_0_3.md`, and
`docs/builder/bld-006-r1-rationale_move.md`. The zero-inbound-reference property the plan recorded
for `docs/SPECS/*.md` still holds. See `### Deferred work catalog` for the one thing the spec-006
cycle's mention is worth to the maintainer.

**Companion — the `-terms.csv`.** Present at `docs/SPECS/appx/spec-007-…-terms.csv`, three lines,
header plus **one** data row, therefore trivially one row per anchor and importable:

```text
term,anchor,notes
optimizer behavior,djangooptimizerextension,Backfilled for DONE-card glossary linkage from the shipped spec body.
```

### 3. The terms-CSV / DONE-card chain

`worker-0.md`'s DONE-card invariants are the contract: a card cannot be `done` without a `SpecDoc` and
at least one glossary link, and the CSV must be one row per anchor. Read-only ORM query, run this
pass:

```text
card_id DONE-007-0.0.4 | status done | version 0.0.4
spec.path  docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
spec.name  spec-007-onboarding_docs_spec_consolidation-0_0_4
glossary_links count 1
  raw_text='optimizer behavior'  term.title='`DjangoOptimizerExtension`'  term.anchor='djangooptimizerextension'
items 14  (Scope 6 / Files likely touched 5 / Note 2 / Why it matters 1)  all is_complete: True
```

Three-way match, checked as three separate comparisons rather than asserted as one:

- **DB `raw_text` ↔ spec link text.** `'optimizer behavior'` against
  `[optimizer behavior][glossary-djangooptimizerextension]` at spec line 19 — **byte-identical**.
- **DB `term.anchor` ↔ CSV `anchor` column.** `djangooptimizerextension` both sides.
- **CSV `term` column ↔ DB `raw_text`.** `optimizer behavior` both sides.

The anchor resolves: `docs/GLOSSARY.md #"## \`DjangoOptimizerExtension\`"`, and
`check_spec_glossary.py` confirms it mechanically. **Deliberately cited without a line number**: the
concurrent cycle regenerated `docs/GLOSSARY.md` during this pass and the heading moved from line 712
to 716 while the audit was running, so a line number here would have been a measurement that rotted
inside the same pass that took it. The link's carrier is still `## Scope` bullet 2 after R2's
re-siting, so no prior statement about its position was falsified.

**No DB write was required and none was made**, which is the outcome the plan predicted and the
condition under which the hard stop does not fire.

### 4. The staged-anchor sweep

`BUILD.md` `## Cross-slice integration pass` step 6. Run twice, and both runs are quoted because the
difference between them *is* the finding.

**Raw, no exclusion:**

```text
$ grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' .
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:34
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:244
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:280
exit=0
```

**Excluding this cycle's own plan and artifacts:**

```text
$ grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' . --exclude='build-007-*.md' --exclude='bld-007-*.md'
exit=1
```

**What was excluded and why.** Two glob patterns, `build-007-*.md` and `bld-007-*.md` — this cycle's
own plan and its four artifacts. Every raw hit is one of the three sentences in the plan that
*describe* the sweep (`### Residual scope`'s R3 clause, the read-only audit's own report of the
sweep, and the R3 checklist row). None stages work; none sits in shipped source, tests, or the
example project. A sweep that reports its own description as a finding is a false positive.

**The true result: zero staged anchors.** The shipped source, test, and example trees are clean, and
so is every durable doc. The exclusion is stated rather than silent because the opposite error — a
sweep that quietly swallows a real hit — is the worse one, so the raw run is quoted in full above and
the excluded population is nameable from it by inspection.

**This artifact adds more self-hits.** The paragraphs above contain the pattern, so a later run of
the raw form will return more than three. It changes nothing: `bld-007-*.md` is already inside the
exclusion, and the final gate's own sweep should apply the same two globs.

### 5. `[spec-006-rationale]` — re-resolved now

R1 accepted this definition with a recorded reason and routed it to R3 to re-resolve. Re-resolved
this pass rather than inherited:

```text
$ ls -l docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md
52621 bytes, present on disk
$ git ls-files --error-unmatch docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md
error: pathspec … did not match any file(s) known to git   (still UNTRACKED)
```

**The target is present and the definition stays.** R1's recorded reason still holds in both of its
parts: the file resolves on disk, and the concurrent spec-006 cycle is demonstrably still live —
`docs/builder/bld-006-r3-doc_completion_archive.md` appeared during this pass — so both files enter
the maintainer's commit window together. The alternative R2 named (retire the definition and its use
site if the sibling cycle had not landed it) is not triggered. Re-checked 2026-08-14, at HEAD
`947f7494`, with the sibling cycle at its own R3.

### 6. "Make sure the code is correct" — discharged, and stated plainly

**Yes, discharged.** Spec-007 shipped no code, so the obligation resolves to proving the card left no
residue in source. Confirmed independently this pass, not inherited from the plan's audit:

- **The staged-anchor sweep is clean tree-wide** (`## 4` above) — nothing was staged from this card
  and left unshipped.
- **No source, test, or example file references anything this card owns.**
  `grep -rn 'three-minute' django_strawberry_framework/ tests/ examples/` → **exit 1, no hits**.
  `grep -rn 'spec-007\|DONE-007\|onboarding_docs_spec_consolidation'` over the same three trees,
  `--include='*.py'` → **exit 1, no hits**.
- **No package source, test, or example file was read for content, written, or reverted by this
  pass.** The four files a third concurrent session is editing were not touched.

So the maintainer does not have to infer this from silence: **this cycle found no correctness defect
in shipped source, and there is none to find from spec-007 — the card shipped five Markdown files and
nothing else.**

### 7. The one finding that required a durable-file edit

**F1 — a present-tense surface count in the rationale, falsified by this cycle's own later pass.**

`docs/SPECS/appx/spec-007-…-rationale.md`, the `### \`## Scope\` 2` entry, read at the open of this
pass:

> **"Three-minute path" names no section anywhere in the repository** — the phrase survives on exactly
> three surfaces, this spec, the card row in `KANBAN.md`, and the same row inside the `KANBAN.html`
> payload, all three being renders of the one `CardItem`. There is no fourth occurrence and there
> never was a section by that name.

Measured at HEAD this pass — `grep -rl 'three-minute'` over the tree, `.git` excluded:

```text
KANBAN.md          (card row, line 4794)
KANBAN.html        (the same row in the payload)
docs/SPECS/appx/spec-007-…-rationale.md   (this file's own prose)
docs/builder/build-007-…, bld-007-r1, bld-007-r2   (this cycle's scratchpads)
```

`grep -c 'three-minute'` on the spec → **0**. R2 deleted the phrase from the spec, which its own
reconciliation record two hundred lines below says outright ("'Three-minute path' named nothing and
is deleted rather than moved"). So the extraction entry's present-tense sentence names the spec as
one of three live surfaces that the same cycle then reduced to two, and the file contradicts itself
across sections.

**Why this is drift that must be fixed and not something to record.** It is a literal falsehood in a
durable file, in the present tense, about a set this cycle changed — the same shape as R2's L4
("only") and L5 (a stale qualifier not retired when its correction landed), both of which were ruled
must-fix by the pass that found them. It is the ninth-instance class arriving by its established
route. And the framing that saves the neighbouring sentences does **not** save this one: the entry's
"*Nothing moved.*" preamble and the file's "every claim below is recorded as the spec makes it" rule
scope claims *of the spec*, and this sentence's subject is the repository, not the spec.

**The fix, and the two repairs rejected.** Anchored to the state it measured:

> **"Three-minute path" names no section anywhere in the repository.** When this record was written
> the phrase sat on exactly three surfaces — this spec, the card row in `KANBAN.md`, and the same row
> inside the `KANBAN.html` payload — all three renders of the one `CardItem`. There never was a
> section by that name.

- **Rejected: restate the count at its HEAD value ("two surfaces").** This cycle's own rule, earned
  twice and recorded on disk both times, is that a rotted measurement is repaired by anchoring it to
  its state and never by swapping in the HEAD number — the new number rots on the next edit exactly
  as the old one did, and the set is one this cycle is still changing.
- **Rejected: cross-reference the reconciliation record's deletion sentence from here.** That puts
  one fact in two places in one file, which is the plan's `DRY rule`.
- **`There is no fourth occurrence` was dropped rather than re-anchored.** It is an unbounded
  present-tense absolute over the whole repository — the class the dispatch names — and it was
  already untrue when written, since the record making the claim was itself a further occurrence. The
  load-bearing half ("names no section anywhere") is kept because it is true and re-verified:
  `grep -rn '^#\+ .*[Tt]hree-minute'` finds no heading anywhere.

**Named on disk.** A short paragraph was appended to the file's own
`### What the audit of this record changed in it` section, stating which record the correction touched
(the extraction record above, not the reconciliation record that section otherwise logs), what rotted,
and that nothing in the spec was touched. It is scoped to this pass and does **not** extend the
section's existing "four statements" or "two further statements" counts — extending them is the route
Worker 3 escalated at R2 and it is not taken here.

### 8. Everything else in the rationale reproduced

Read end to end and every measurable claim in it re-derived this pass, because F1 proved the file can
carry a rotted measurement:

| Claim | Command | Result |
|---|---|---|
| spec 2,282 bytes / 65 lines / 0 fenced blocks at `947f7494` | `git show 947f7494:<spec> \| wc -c` | **2282** ✓ |
| the boilerplate paragraph in seven archived specs, with their byte counts at `947f7494` | `git show` + `grep -c 'intentionally lightweight'` per file | 007 2282, 011 1797, 012 1651, 013 1669, 016 4558, 024 1618, 026 3593 — **seven files, each matching once** ✓ |
| spec-007 among the smallest, with 011/012/013/024 smaller | the same figures | ✓ |
| 56 tracked `docs/SPECS/spec-*.md` | `git ls-tree -r --name-only 947f7494` | **56** ✓ |
| root README's eight `##` headings, none operational | `grep -n '^## ' README.md` | **8** ✓ |
| `## Project documentation` has eight entries, all resolving | expansion + disk check | ✓ |
| `docs/README.md` is 1,003 lines / 117,358 bytes at HEAD | `git show HEAD:docs/README.md \| wc -lc` | **1003 117358** ✓ (working tree identical) |
| `CHANGELOG.md` 100,289 bytes / 437 lines at `947f7494` | `git show HEAD:CHANGELOG.md \| wc -lc` | **437 100289** ✓ |
| the `0.0.8` entry cites two spec files | `grep -n 'spec-027-filters\|spec-028-orders' CHANGELOG.md` | line 140 cites both; definitions live at 388-389 ✓ |
| no `## Quick comparison` heading anywhere | `grep -rn '^#\+ Quick comparison' --include='*.md' .` | **exit 1** ✓ |
| `#### Other` renders zero times in `KANBAN.md` | `grep -c '^#### Other$' KANBAN.md` | **0** ✓ |
| card 7 carries three labels | live DB + `KANBAN.md` card block | `docs`, `internal`, `release` ✓ |
| the spec's link block gained seven definitions and lost `[backlog]` | the outbound run above | ✓ |
| zero raw `path:NN` in both durable files | `grep -cE '[a-zA-Z_/]+\.(py\|md):[0-9]+'` | **0** and **0** ✓ |

Two lines in the rationale exceed 110 characters (line 1, the title, at 123; line 359 at 115). Both
**pre-date this pass** — neither is in a paragraph it wrote — and
`scripts/check_trailing_commas.py --check` passes on the file, so the markdown scaffold rule is not
violated. Recorded, not fixed: fixing line 1 would rename the file's title for a cosmetic width and
the checker that owns the rule is green.

---

## Files touched

- `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` — F1's correction
  plus the on-disk naming of it. **634 lines / 42,932 bytes → 641 / 43,502** (`wc -lc`, measured after
  the last edit).
- `docs/builder/bld-007-r3-doc_completion_archive.md` — this artifact (created).
- `docs/builder/worker-memory/spec-007-worker-1.md` — memory entry, gitignored.

**The spec was not edited.** `git diff --numstat` on it reads `20 28`, byte-identical to what R2's
final verification left, and `wc -lc` reads **57 lines / 2,983 bytes** at this pass's open and close.
`## Scope` bullet 2 and its glossary link were never touched, so the 1-anchor constraint was not
exercised.

## Validation run

Every command quoted verbatim with its exit status, run after the edits.

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

$ grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' .
(3 hits, all docs/builder/build-007-…md lines 34, 244, 280)
exit=0

$ grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' . --exclude='build-007-*.md' --exclude='bld-007-*.md'
exit=1
```

Both glossary-chain checks were re-run a second time **after** the concurrent cycle's
`docs/GLOSSARY.md` regenerate landed mid-pass, so the green result is not one taken before the file
moved under it:

```text
$ grep -n '^## `DjangoOptimizerExtension`' docs/GLOSSARY.md
716:## `DjangoOptimizerExtension`

$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/builder/bld-007-r3-doc_completion_archive.md
exit=0
```

**Declarations re-checked against the plan and correct as absences:** ownership partition none;
hot-path none, so no number is owed and its absence is correct; floor-verification scope none, so no
floor run is owed by this item; no failability proof owed — this item introduces no boundary, guard,
gate, or rejection path. The `## Final test-run gate` belongs to `docs/builder/bld-007-final.md` and
was not run here. No `pytest` ran and no `--cov*` flag was passed anywhere in this pass.

## Concurrent-commit check, not `git status` alone

```text
$ git rev-parse HEAD
947f74948c16b20b0c15ff359bb53fbe462d4b8c   (open and close, unchanged)

$ git log --stat --oneline -5 -- <this cycle's six paths>
1592bb90 refactor(kanban): consolidate the card queue onto Status; drop PlanningState
e1f9ed26 docs: backfill shipped spec glossary CSVs
81e4704d docs: archive prior specs to docs/SPECS/ and renumber per Step 8 pass
```

The three commits touching any of this cycle's paths all long predate the cycle, and no commit landed
during it. **Nothing this pass wrote was swept into a concurrent commit.**

## Working-tree churn and baseline growth

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` read **26 entries** at this
pass's open and **29** at its close. This artifact is one of the three new entries; the other two are
**not this pass's**:

- `docs/builder/bld-006-r3-doc_completion_archive.md` (`??`) — the concurrent **spec-006** cycle
  reaching its own R3, mirroring this item. Out of this cycle's writable set, not read for content,
  not touched.
- **`docs/GLOSSARY.md` (`M`)** — clean at this cycle's pre-flight and dirty now,
  `1 file changed, 5 insertions(+), 1 deletion(-)`. This is the concurrent cycle's **authorized
  DB-backed glossary completion**, which the plan's `## Concurrent-writable tracked binary /
  generated files` names in advance as the expected explanation for a diff here. It is **not this
  pass's output** — no worker here wrote the DB or ran a regenerate — and it is not reverted.
  **Consequence checked, not assumed:** the regenerate moved this spec's one anchor from line 712 to
  716, so the anchor was re-resolved afterwards and `check_spec_glossary.py` re-run; both are green
  and quoted in `## Validation run`. A line number for that heading is deliberately absent from this
  artifact for the same reason.

This is the plan's **sixth growth event**; Worker 0 appends it, not a worker.

The five deleted `docs/review/rev-*.md` remain **escalated and unresolved** — still tracked at HEAD,
still absent from disk, not restored, not reverted, not touched. `docs/review/review-0_0_14.md` and
`docs/review/rev-_boundary_ordering.md` were not touched. The concurrent spec-002 and spec-006
cycles' paths and the third session's four package-source and test files were **not read for content,
not touched, not reverted, not staged**. `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, and
`examples/fakeshop/db.sqlite3` were **read only**; no DB write was made and none is owed, so the
plan's hard stop did not fire.

## Deferred work catalog material for `bld-007-final.md`

Worker 1 is the catalog's only author and it lives in the final gate's artifact; this is the material
it needs, each item confirmed still standing this pass rather than copied forward.

1. **`CHANGELOG.md`'s `0.0.8` entry relies on design-doc pointers.** Confirmed live: line 140 cites
   `[spec-027-filters-0_0_8.md][spec-filters]` and `[spec-028-orders-0_0_8.md][spec-orders]` for
   release context, with both definitions live at lines 388-389. The file is 437 lines / 100,289
   bytes, so "condensed" no longer describes it either. Card 7's scope said the changelog would stop
   doing exactly this. `AGENTS.md` rule 21 closes the file, so this was reconciled **in the spec**
   (drift row D9) and the changelog's own state is a **maintainer question**, never a worker edit.
   Source: plan `### Verified spec-versus-HEAD drift` D9; re-confirmed here.
2. **`CONTRIBUTING.md` carries a stale citation of a `BUILD.md` heading that does not exist.**
   Confirmed live at `CONTRIBUTING.md` line 11: `docs/builder/BUILD.md` "Spec filename pattern".
   `grep -n '^## Spec and build-plan filename pattern' docs/builder/BUILD.md` → **line 7**; the cited
   title does not exist. Outside this cycle's writable set. R2's spec fix pointed at the correct
   owners and explicitly does **not** retire the last stale copy. **Two live copies remain**:
   `CONTRIBUTING.md` line 11 and `KANBAN.md` line 4815 (with the same string once in the
   `KANBAN.html` payload) — and the KANBAN ones are generated from a Done card's `CardItem`, so item
   3 governs them.
3. **`KANBAN.md`'s card row carries the "three-minute path" phrase.** Confirmed live at
   `KANBAN.md` line 4794 and once in the `KANBAN.html` payload, both renders of card 7's `CardItem`.
   The phrase names no section anywhere. **This is not drift to fix**: a Done card's `Scope` is a
   correct historical record of what the card said in May 2026, the files are generated, and editing
   the DB row would falsify the record. Catalogued so no later pass "fixes" it.
4. **The five deleted `docs/review/rev-*.md` files.** Escalated by R1, unresolved through R3. Tracked
   at HEAD, absent from disk, no worker in this cycle touched them. `AGENTS.md` rule 22 prescribes
   `git checkout HEAD -- docs/review/`, which is banned in this cycle. **Only the maintainer can tell
   whether this is a closing REVIEW cycle's authorized cleanup or a rule-22 violation, and only the
   maintainer can restore safely.**
5. **The `BUILD.md`-level convention question Worker 3 escalated at R2, unacted on.** Whether every
   durable figure must name both the commit *and* whether it is the committed or the working-tree
   state, or whether working-tree figures are forbidden in durable files entirely. F1 is a further
   data point for the same underlying class in its word-shaped variant.
6. **`AGENTS.md` rule 27 does not name `build-*.md` plans.** Rule 27 exempts per-cycle
   `docs/builder/bld-*.md` scratchpads from the symbol-qualified-path rule but not the committed
   `build-*.md` plans, six of which carry raw `path:NN`. A standing-doc question for the maintainer,
   not a defect of this cycle. Source: plan, R1's final verification.
7. **The rationale is 43,502 bytes against a 2,983-byte spec.** Worth a maintainer's eye at some
   point; not a defect and not this cycle's to fix — the spec is a card-snapshot stub and the
   rationale carries a ten-release change record for it. Source: R2 `### Notes for Worker 1` item 4,
   figure re-measured this pass.
8. **The concurrent spec-006 cycle names spec-007 as the owner of four of its drift rows** (D3, D5,
   D8, D17 in `docs/builder/build-006-public_surface-0_0_3.md`) — every undischargeable
   `docs/README.md` obligation that spec carries. **No conflict was created**: spec-007's reconciled
   `docs/README.md` bullet claims a role (the entry point for *using* the package) and no contents,
   and spec-006's rows describe the same document's actual sections. Recorded so the maintainer sees
   that the two cycles' outputs meet cleanly, and so no later pass reads spec-006's attribution as an
   obligation spec-007 left open.

## Notes for Worker 3

- **The whole of this item's durable output is one paragraph rewritten and one paragraph appended**,
  both in the rationale, both quoted in full in `## 7`. `git diff` on that file is the complete
  change surface. The spec is untouched.
- **The audit's obligation to distrust every number applies to this artifact too.** Every count and
  byte figure above was measured this pass by the command shown beside it; re-derive rather than
  reproduce, per the cycle's standing record.
- **Two specific things to attack.** (a) Whether F1 genuinely *had* to be an edit rather than a
  record — the dispatch prefers recording, and if the "*Nothing moved.*" framing does after all scope
  the sentence to the spec-as-it-then-was, the edit was unnecessary and the shape should have been
  procedural closure. (b) Whether the replacement sentence introduces any new unmeasured quantifier;
  the absolutes it carries are "exactly three" (measured this pass at three surfaces, listed) and
  "names no section anywhere" (measured this pass by heading grep).
- **`scripts/review_inspect.py` was not run**, and the reason is recorded rather than omitted:
  `BUILD.md` `### When to run the helper during build` scopes it to Python source with review-worthy
  logic. This item reads and writes Markdown only, and the plan makes all package source read-only.
- **No temp tests were created**, so `docs/builder/temp-tests/r3/` does not exist.
- **The staged-anchor sweep will return more than three raw hits now** — this artifact describes the
  pattern. Apply the same two `--exclude` globs.

## Notes for Worker 1 (spec reconciliation)

Extends the six instances in `docs/builder/bld-007-r1-rationale_move.md` and the three in
`docs/builder/bld-007-r2-spec_reconciliation.md`. Nothing in any of them is retracted. **L4 and L5 are
closed and must not be re-opened**; nor may the `CONTRIBUTING.md` bullet's legitimacy, R2 pass 1's
`## Other` completeness walk, the line-7 pointer ruling, or L3's two superseded scratchpad miscounts.

New from this pass:

1. **Every item R2 routed to R3 is now closed, and each was re-run rather than inherited**: the
   three-direction sweep, the `SpecDoc.path` / `-terms.csv` / `import_spec_terms` chain, the
   staged-anchor sweep, the `#other` re-sweep, the `[backlog]` retirement, the seven new definitions,
   and `[spec-006-rationale]`'s untracked target. **R3 inherits no open R2 question and leaves none
   for the final gate except the catalog above.**
2. **The tenth instance of the cycle's defect class was found and it is word-shaped again** (F1) —
   this time a *count* rendered false not by a miscount but by the same cycle changing the set it
   counted, one pass after it was measured. That is a variant worth naming separately: the figure was
   right when written, the writer was not still making changes, and a **later pass in the same cycle**
   falsified it. The rule that catches this one is not "measure as you write" but **"a present-tense
   count over a set your own cycle is still editing must be anchored to its state at the moment of
   measurement"**.
3. **No DB write was made or is owed**, so the plan's hard stop did not fire and Worker 0 has nothing
   to adjudicate on that front.
4. **The final gate's sweep needs the two `--exclude` globs**, or it will report this cycle's own
   prose as staged work.

## Status

`planned`. Per the plan's Deviation 2, Worker 0 reads this as "dispatch Worker 3 for the audit".

---

## Review (Worker 3)

Fresh invocation, no context from the audit pass. Every figure below was measured by its own command
in this pass; nothing is reproduced from the artifact, the plan, R1, or R2.

HEAD re-derived at open and close: `947f74948c16b20b0c15ff359bb53fbe462d4b8c`, unchanged. No
`pytest` ran, no `--cov*` flag was passed, no `git stash` / `checkout` / `restore` / `worktree` was
used, nothing was committed, no branch was created, no DB write was made. Files written by this
pass: this artifact (this section only) and `docs/builder/worker-memory/spec-007-worker-3.md`.

### High: one finding

**H1 — the durable rationale asserts, at two sites, that a section named "Three-minute path" never
existed. It did, and the card's own commits are what created and destroyed it.**

Sites, both in `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`:

- `### \`## Scope\` 2 — three of four items, and the sole glossary carrier`, closing sentence of the
  paragraph this pass rewrote: **"There never was a section by that name."** (line 216-217)
- `### Why this spec failed the way it did` — the content-inventory bullet's mechanism enumeration:
  "**Every one of them failed**, by a different mechanism each time: content relocated (`2bd7cb84`),
  **a section that never existed**, a rename sweep substituting the subject (`40c1855f`), …"
  (line 402)

The measurement, run this pass. `docs/README.md` carried a literal `## Three-minute path` heading
with a five-step body, and its whole lifetime sits inside card 7's own three documentation commits,
all dated 2026-05-05:

```text
$ git show 4b8dce07:docs/README.md | grep -c '^## Three-minute path'   -> 0
$ git show 83c25963:docs/README.md | grep -c '^## Three-minute path'   -> 1   (line 42)
$ git show 3a4d40b7 -- docs/README.md | grep -n 'Three-minute'
15:-## Three-minute path
$ git show 231911a8:docs/README.md | grep -c 'Three-minute'            -> 0
$ git merge-base --is-ancestor 83c25963 HEAD                           -> yes (main history)
```

The section body at `83c25963`, for the record: five numbered steps ending "Read
[`FEATURES.md`](FEATURES.md) when you want the full capability catalog."

**Why it matters, and why it is High rather than a note.** This is a false factual statement about
repository history in an archived durable file, at two sites, and it is falsifiable in one command.
It is also the *worst possible* claim to get wrong here, because this file's entire contract is to
record what each spec claim once meant and how it fared: telling a future reader that the spec's
bullet named a section that never existed says the claim was fiction from the start. It was not. It
was **accurate against `83c25963` and falsified by the card's own next commit `3a4d40b7`, the same
day** — the card wrote the section, then deleted it, and never updated the `CardItem` the spec was
later rendered from.

That true history is materially better than the claim replacing it, and it is a **fifth, distinct
mechanism** for the enumeration at line 402, not a repetition of one already there: every other
content-inventory claim was falsified by a *later* card, over months. This one was falsified by its
own card, within one day, before the release commit. It is the sharpest illustration the section's
own thesis has — documentation state moves faster than the sentences describing it — and the file
currently throws it away in favour of a falsehood.

**How this survived, which is the part worth recording.** The clause is not new: it came in with R1's
extraction and passed R2. But this pass *kept it deliberately* as part of F1's fix, and wrote:

> The load-bearing half ("names no section anywhere") is kept because it is true and re-verified:
> `grep -rn '^#\+ .*[Tt]hree-minute'` finds no heading anywhere.

That grep runs against the working tree. It proves the present-tense half and is silent on the
past-tense half, which was kept in the same edit and not verified by anything. This is exactly the
shape recorded in this reviewer's own carry-forward from R2 pass 2 — *check the surviving half of
every sentence a pass says it corrected* — arriving one pass later by its predicted route. A
present-tense absolute was correctly identified and dropped; the past-tense absolute sitting beside
it in the same sentence was re-endorsed without a command behind it.

**Recommended change** (Worker 1's wording, not prescribed here beyond the facts that must survive):
at both sites, replace the "never existed" absolute with the measured history — the section existed
at `83c25963`, was removed at `3a4d40b7`, and both are the card's own commits from 2026-05-05, so the
spec's bullet described a state that had already been deleted before the `0.0.4` release commit
`231911a8`. At line 402 the enumeration should carry that as its own mechanism rather than reusing
another row's. No test expectation: no behavior is affected, this cycle runs no `pytest`, and the
proof is the four `git show` invocations quoted above.

**Two things this finding does not touch.** The `### \`## Scope\` 2` entry's *other* new sentence is
correct and stays (see `### What holds` below), and the reconciliation record's line 498 — "'Three-minute
path' named nothing and is deleted rather than moved" — reads in context as a statement about the
state at reconciliation, which is true; Worker 1 may leave it, though a reader arriving from the
corrected entry above may find it worth one clarifying word.

### Medium: None.

### Low: three, all scratchpad-only, all superseded here rather than routed

Per the disposition this cycle established at R1 pass 3 and used again at R2 pass 1: a `bld-*.md`
arithmetic or prose slip that touches no durable file is discharged by the reviewer who owns a
section, in that section, without a spawn. None of these three requires an edit by Worker 1.

1. **`## 2`, the companion-CSV paragraph: "three lines, header plus one data row".** The file is
   **two** lines. `wc -l` → `2`; `len(open(...,'rb').read().splitlines())` → `2`; bytes `132`,
   newline count `2`. Header + one data row = two lines, so the sentence contradicts itself. The
   substantive conclusion in the same sentence — one row per anchor, therefore importable — is
   **correct and independently verified** (CSV content quoted below).
2. **`## 4` and `## Notes for Worker 3`: "This artifact adds more self-hits … a later run of the raw
   form will return more than three."** Measured this pass, the raw form returns **exactly three**,
   all in the plan, **none in this artifact**. The artifact only ever writes the pattern in its
   backslash-escaped command form (`TODO\(spec-007`), which the regex does not match. The
   recommendation that follows it — the final gate should apply the same two globs — is harmless and
   still correct, so nothing operational turns on it.
3. **`## Notes for Worker 3` (b): "'exactly three' (measured this pass at three surfaces, listed)".**
   The pass measured **two** live `CardItem`-render surfaces (`KANBAN.md`, `KANBAN.html`); the three
   in the corrected sentence is a *historical* count, anchored to the moment the record was written,
   which is the whole point of the fix. The parenthetical describes it as a this-pass measurement,
   which is the one thing it is not.

Separately and not a finding: the raw sweep's three hits now sit at plan lines **34 / 251 / 287**,
not the 34 / 244 / 280 the artifact recorded. Worker 0 appended the plan's sixth growth section after
this pass measured them. Raw `path:NN` in a `bld-*.md` is exempt (`AGENTS.md` rule 27) and the drift
is not this pass's.

### DRY findings: None.

The item proposes no helper, no abstraction, and no new indirection — it writes two Markdown
paragraphs. The existence challenge has no target. The artifact's own `### DRY analysis` correctly
identifies the one real duplication risk it faced (cross-referencing the reconciliation record's
deletion sentence from the extraction entry, putting one fact in two places in one file) and
correctly declines it; H1's fix must not reintroduce that shape either — the corrected history
belongs in the extraction entry and, as a distinct mechanism, in the enumeration at line 402, which
is not a restatement.

### The F1 defect and its fix

**The defect was real.** Verified by measuring both states, not by reading the account of them:

```text
$ git show HEAD:docs/SPECS/spec-007-…-0_0_4.md | grep -c 'three-minute'   -> 1
$ grep -c 'three-minute' docs/SPECS/spec-007-…-0_0_4.md                   -> 0   (working tree)
```

So the sentence R3 found — "the phrase survives on exactly three surfaces, **this spec**, the card
row in `KANBAN.md`, and the same row inside the `KANBAN.html` payload … There is no fourth
occurrence" — named the spec as a live carrier of a phrase R2's uncommitted edit had already removed,
inside a paragraph whose own heading is "*Item by item at HEAD*". The strongest counter-argument
available to the finding is that the paragraph is scoped to HEAD, where the spec *does* still carry
the phrase — and it fails, because the file is uncommitted and lands in the same commit window as the
deletion, so every reader of the finished file reads it against a spec that does not contain the
phrase. The artifact's own note (a) invited this attack and the attack does not land: the entry's
"*Nothing moved.*" preamble labels that no prose was relocated, and cannot be read as scoping a
sentence that sits under an explicit at-HEAD measurement heading. **F1 was correctly identified as an
edit, not a record.**

**The fix is correct in three of its four parts.**

- **Anchoring rather than restating at the HEAD value: right, and the reasoning generalises.** The
  set being counted is one this cycle is still changing, so "two surfaces" would have rotted at the
  next edit exactly as "three" did. This is the disposition the cycle earned twice before and it is
  applied without reinventing it.
- **Dropping `There is no fourth occurrence` rather than re-anchoring it: right.** An anchored
  version of a claim that was never true would have manufactured a new defect. Re-derived: at the
  moment R1 wrote it, the phrase also sat in `build-007-…md` and in `bld-007-r1`, and in the record
  making the claim.
- **The surviving "exactly three surfaces" is not the tenth instance.** Checked specifically, because
  it is the obvious place for one. It is an enumeration (all three members named inline) with its
  class boundary stated in the appositive — "all three renders of the one `CardItem`" — and the
  scratchpads that also carry the phrase are narration, not renders. It also reuses the plan's own
  established sense of "surface" (the plan's fourth correction: "'three-minute' has three surfaces,
  not two: the spec, `KANBAN.md`, and the `KANBAN.html` payload"). Historically accurate at the three
  named members: spec at HEAD **1**, `KANBAN.md` **1**, `KANBAN.html` **1**. The class boundary
  arriving *after* the quantifier is worth a reader's second look, but it is stated, and a stated
  class boundary is what this reviewer's own R1-pass-3 carry-forward asks for.
- **The surviving `There never was a section by that name` IS the tenth instance.** H1 above.

**The on-disk naming of the correction** (rationale `### What the audit of this record changed in it`,
final paragraph) is accurate as written, correctly scoped to this pass, and correctly does **not**
extend the section's existing "four statements" / "two further statements" counts — the route
escalated at R2 and rightly not taken. It states the correction sits in the extraction record rather
than in that section, which is true.

### The spec is genuinely untouched

Re-derived rather than accepted:

```text
$ wc -lc docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
      57    2983
$ git diff --numstat -- docs/SPECS/spec-007-…-0_0_4.md
20      28
$ grep -n 'optimizer behavior' docs/SPECS/spec-007-…-0_0_4.md
19:- [`docs/README.md`][readme] is the entry point for *using* the package — installation, quick
   start, running the example project — and the place a consumer reads runtime behavior,
   [optimizer behavior][glossary-djangooptimizerextension] included.
$ grep -n '^## ' docs/SPECS/spec-007-…-0_0_4.md
9:## Card snapshot
14:## Scope
```

57 lines / 2,983 bytes matches the artifact's open-and-close figure and matches what R2's byte
arithmetic left (2,989 → 2,983). `## Scope` bullet 2 still carries the reference-style glossary link
with byte-identical link text, so the 1-anchor constraint was not exercised and could not have been
broken by this item. The `20 28` numstat is R2's whole reconciliation against HEAD and is unchanged.

### Audit of the audit — what was re-derived, and what failed

Every claim below was re-run at this pass's own scope. **One failed: the "never existed" claim in
`## 8`'s scope, which `## 8` did not enumerate (H1).** Everything else reproduces exactly.

| Claim under audit | Re-derivation this pass | Result |
|---|---|---|
| Outbound: spec 10 definitions, 10 resolve | each def expanded from `docs/SPECS/` and disk-checked | **10/10** ✓ |
| Outbound: rationale 15 definitions, 15 resolve | each def expanded from `docs/SPECS/appx/` and disk-checked | **15/15** ✓ |
| Depth trap, per file | `../../README.md` → root, `../README.md` → `docs/README.md` (from `docs/SPECS/`); `../../../README.md` → root, `../../README.md` → `docs/README.md` (from `appx/`) | ✓ both files |
| The two spec fragments resolve | `#card-snapshot` / `#scope` against the spec's only two `##` headings | ✓ |
| `[backlog]` retired with no dangling use | `grep -n 'backlog\|BACKLOG'` on the spec → **exit 1**; rationale still defines and uses it, resolving | ✓ |
| `#other` referenced nowhere but this cycle's scratchpads | `grep -rn '#other'` over `*.md` `*.py` `*.csv` `*.html` → hits only in `bld-007-r1/r2/r3`; `grep -rn 'spec-007-other'` adds rationale line 564 and `bld-007-r2` only; `grep -c '^## Other'` on spec → **0** | ✓ no durable dangler |
| Inbound: `KANBAN.md` ×2 + `KANBAN.html` ×1 + `SpecDoc.path`, all archived | `grep -n` → lines **140**, **4783**; `KANBAN.html` count **1**; DB `spec.path` | ✓ all four |
| Zero inbound reference from any sibling spec | text-only `grep -rl` → only `KANBAN.*`, the spec-007 pair, and three concurrent-session files (`docs/review/review-0_0_14.md`, `build-006-…md`, `bld-006-r1-…md`) | ✓ exactly as reported |
| Companion CSV: one row per anchor | file content; **2 lines** not 3 (Low 1) — header + one data row | ✓ conclusion holds |
| DONE-card chain, three-way | live ORM: `raw_text='optimizer behavior'`, `term.anchor='djangooptimizerextension'`, `spec.path` archived, `glossary_links` **1**, items **14** (Scope 6 / Files 5 / Note 2 / Why 1) all complete, labels `docs`/`internal`/`release`, `planning_note` `''` | ✓ three-way match |
| The glossary anchor **now**, after the concurrent regenerate | `grep -n '^## \`DjangoOptimizerExtension\`' docs/GLOSSARY.md` → **716**; `git diff --stat` → `5 insertions(+), 1 deletion(-)` | ✓ chain holds now |
| Code-correctness discharge: no source/test/example residue | `grep -rn 'three-minute' django_strawberry_framework/ tests/ examples/` → exit 1; staged-anchor sweep clean outside this cycle's own files | ✓ discharged |
| Rationale reproduction table (`## 8`), spot-checked in full | seven stub specs 2282/1797/1651/1669/4558/1618/3593, boilerplate ×1 each; **56** tracked specs; 007 fifth smallest behind 024/012/013/011; README **8** `##` headings; `docs/README.md` **1003 / 117358**; `CHANGELOG.md` **437 / 100289**; `0.0.8` entry cites both specs at line 140 with defs at 388-389; no `Quick comparison` heading anywhere (exit 1); `#### Other` in `KANBAN.md` → **0**; raw `path:NN` **0** and **0**; over-110 lines exactly **1 (123)** and **359 (115)** | ✓ every row |
| Durable-doc role table (`## 1`) | `README.md` 8 headings, none operational; all 8 map targets resolve; `docs/README.md` `## Installation` 7 / `## Quick start` 16 / `## Today and coming next` 91 / `## Nested connection indexing` 175 / `## Running the example project` 852; `CONTRIBUTING.md` all six at 15/25/33/42/51/59; `docs/GLOSSARY.md` and `docs/TREE.md` line-3 self-descriptions; `CHANGELOG.md` line 3 | ✓ every row |

**The glossary anchor moved mid-audit and has not moved again.** Re-checked at this pass rather than
inherited: still line 716, and both chain checks re-run green *after* the concurrent cycle's
regenerate landed. The artifact's decision to cite the heading symbol-qualified rather than by line
number is correct and is the reason no statement in it rotted when the file moved.

### The staged-anchor sweep and its exclusions

Both forms re-run verbatim, and the excluded population enumerated independently rather than taken on
the artifact's word:

```text
$ grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' .
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:34
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:251
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:287
exit=0

$ grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' . --exclude='build-007-*.md' --exclude='bld-007-*.md'
exit=1
```

All three raw hits are prose in the plan *describing* the sweep (`### Residual scope`'s R3 clause,
the read-only audit's report of it, and the R3 checklist row) — none stages work, none is in shipped
source, tests, or the example project.

**The exclusion swallows nothing.** The excluded population was enumerated by `find` over the whole
tree, not by the two globs' authors:

```text
$ find . -path ./.git -prune -o \( -name 'build-007-*.md' -o -name 'bld-007-*.md' \) -print
./docs/builder/bld-007-r3-doc_completion_archive.md
./docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md
./docs/builder/bld-007-r2-spec_reconciliation.md
./docs/builder/bld-007-r1-rationale_move.md
```

Exactly four files, all this cycle's own plan and artifacts, nothing else anywhere in the tree. The
globs cannot reach a shipped file, a durable doc, or another cycle's artifact. **The true result is
zero staged anchors**, and it is a true zero rather than a hidden one.

### Deferred-work catalog — spot-checks

Four of the eight are mechanically checkable and all four confirm:

- **Item 2 (`CONTRIBUTING.md` stale citation): confirmed live.** `CONTRIBUTING.md` line 11 reads
  `see \`docs/builder/BUILD.md\` "Spec filename pattern"`; the real heading is
  `## Spec and build-plan filename pattern` at `docs/builder/BUILD.md` line 7, and
  `grep -rn 'Spec filename pattern' docs/builder/BUILD.md` → **exit 1**. The second live copy at
  `KANBAN.md` line 4815 (once in the `KANBAN.html` payload) also confirms, and is generated from a
  Done card's `CardItem`, so item 3's rule governs it.
- **Item 3 (`KANBAN.md`'s "three-minute path" row): confirmed live and correctly classified as NOT
  drift.** `KANBAN.md` line 4794 is card 7's `Scope` `CardItem` render, `KANBAN.html` carries it once.
  It is a Done card's historical record of what the card said, in a generated file; editing the DB row
  would falsify the record. Catalogued, not fixed, is right. **H1 sharpens this rather than
  contradicting it**: the row was an accurate description of `docs/README.md` at `83c25963` when it
  was written, which is a better reason to leave it alone than "it names nothing".
- **Item 1 (`CHANGELOG.md` `0.0.8` design-doc pointers): confirmed live.** Line 140 cites both spec
  files for release context, definitions at 388-389, file is 437 lines / 100,289 bytes.
- **Item 8 (spec-006 names spec-007 as owner of D3/D5/D8/D17): confirmed, and no conflict, checked
  independently in both directions since both cycles are uncommitted.** `build-006-…md` rows D3, D5,
  D8, D17 all describe `docs/README.md` sections that **do not exist** (`Goal / vs comparisons`,
  `Current surface`, `Planned surface`, `Package architecture`). Spec-007's reconciled bullet names
  `## Installation` (7), `## Quick start` (16), `## Running the example project` (852) — all of which
  **do** exist, verified above. Disjoint sets, no duplicated concrete claim, so the single-ownership
  law is not strained. The reverse direction is clean too: the working-tree `docs/SPECS/spec-006-…md`
  mentions `docs/README.md` only under its own alpha-signaling rules and **contains no reference to
  spec-007 at all** (`grep -n 'spec-007'` on both spec-006 files → no match). **The two cycles'
  outputs meet cleanly.** The artifact's phrasing that spec-007's bullet "claims a role … and no
  contents" is loose — it does name three sections — but the conclusion it supports is verified
  correct, and the three it names are the three that exist.

### Was declining procedural closure the right call? Yes — and H1 is the proof

Stated explicitly, as the dispatch asks.

`BUILD.md` `### Procedural-closure slices` licenses a self-closing Worker 1 pass only where the item's
contract is to ship nothing. This item shipped a durable edit to an archived file under
`docs/SPECS/appx/`. Taking the full chain was not merely defensible, it was the only reading of the
plan's own conditional that the facts permitted.

The counterfactual is not hypothetical. Under procedural closure, the pass that authored the F1 fix
would have been the only pass to read it, and **both false absolutes would have entered the archive
with no independent read** — the one this pass correctly removed, and the one it re-endorsed. The
argument the artifact gives for declining ("a durable-file edit made in a self-closing pass is exactly
what should not go unreviewed") is not just correct in the abstract; it named the exact failure that
then occurred inside its own fix. Declining was right, and the item should stay on the full chain
through the re-review.

### What holds

- The audit is genuinely re-derived, not inherited. Every figure in it that this pass re-measured
  reproduced exactly, including the ones easiest to copy forward (byte counts at a named commit, the
  56-spec population, the seven-stub table, the two over-110 line numbers).
- The single hardest judgement in the pass — anchor the rotted count rather than restate it at HEAD —
  is correct, is consistent with the disposition the cycle earned twice before, and is argued from
  the property that makes it right (the set is one this cycle is still editing) rather than from
  precedent alone.
- The decision to cite the moving `docs/GLOSSARY.md` heading symbol-qualified instead of by line
  number is the reason nothing in the artifact rotted when the concurrent regenerate landed mid-pass.
  It is `AGENTS.md` rule 27 being load-bearing rather than stylistic, and it was applied before the
  churn, not after.
- The staged-anchor exclusion is stated, its population is enumerable from the raw run, and it is in
  fact exactly this cycle's four files.
- Baseline-dirty handling is clean: nothing reverted, nothing restored, no `git checkout`, no DB
  write, the five deleted `docs/review/rev-*.md` left escalated and untouched, the third session's
  four source/test files untouched.

### Declarations, checked as absences

- **Ownership partition:** none declared, none owed, correct.
- **Hot-path budget:** none declared; no number owed and its absence is correct — this item runs no
  package code.
- **Floor verification:** none in scope; no floor run owed by this item. The `## Final test-run gate`
  is `bld-007-final.md`'s.
- **Failability proofs:** none owed and none recorded, which is correct — the item introduces no
  boundary, guard, gate, or rejection path. The mandatory re-run floor is therefore satisfied by an
  **empty re-run set**, which is legal here precisely because no boundary meets it.
- **Public-surface check:** `git diff -- django_strawberry_framework/__init__.py` → **empty**.
  `__all__` and the re-export list are unchanged. (Two other package-source files are dirty from a
  third concurrent session; neither is `__init__.py`, and neither was read for content or touched.)
- **CHANGELOG sanity:** not applicable — this item does not touch `CHANGELOG.md`, and
  `AGENTS.md` rule 21 closes it to this cycle.
- **`scripts/review_inspect.py`:** not run, and the artifact's stated reason is correct — the helper
  is scoped to Python source with review-worthy logic and this item reads and writes Markdown only.
  Recorded as a skip with its reason, per the role file.
- **Temp tests:** none created by the audit pass and none by this review; nothing to promote.

### Validation run (this review pass, verbatim)

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/builder/bld-007-r3-doc_completion_archive.md
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ grep -n '^## `DjangoOptimizerExtension`' docs/GLOSSARY.md
716:## `DjangoOptimizerExtension`
```

The two staged-anchor sweeps are quoted in full in their own section above. `import_spec_terms` was
run read-only (`--check`); no DB write was made by this pass.

### Working-tree churn and baseline

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` reads **29 entries** at this
review's open and close — **no growth during this pass**, and the same 29 the audit pass recorded at
its close. `HEAD` is `947f7494` at open and close; `git log --stat` over this cycle's paths returns
only `1592bb90` / `e1f9ed26` / `81e4704d`, all long predating the cycle, so nothing this cycle wrote
was swept into a concurrent commit. The five deleted `docs/review/rev-*.md` remain escalated and
unresolved, untouched. `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, and
`examples/fakeshop/db.sqlite3` were read only. The concurrent spec-002 / spec-006 paths and the third
session's four source and test files were not read for content and not touched.

### Notes for Worker 1 (spec reconciliation)

Extends the notes in `bld-007-r1` and `bld-007-r2` and the audit pass's own above; nothing in any of
them is retracted, and the closures listed as un-reopenable stay closed.

1. **H1 is the tenth instance, and it arrived in the surviving half of the sentence the ninth was
   fixed in.** Both halves were absolutes; one was measured and dropped, the other was re-endorsed
   with a command that could not test it. The rule this yields is narrower and more useful than
   "check your counts": **when a pass repairs one clause of a sentence, the other clauses of that
   sentence are now that pass's claims too, and each needs its own command.** A grep at HEAD does not
   verify a claim about history; a claim with the word "never" in it needs `git log -S` or an
   equivalent, not a working-tree scan.
2. **The corrected history is an upgrade, not a patch.** Card 7 wrote `## Three-minute path` at
   `83c25963` and deleted it at `3a4d40b7`, same day, both its own commits, before the release.
   Spec-007 is therefore the only spec in this cycle's table whose claim was falsified **by its own
   card, within one day**. That belongs in the record on its merits, independent of the fact that the
   current sentence is wrong.
3. **`AGENTS.md` rule 34 note for the re-review:** the two false sites are in the rationale, which
   this cycle owns and which is untracked, so the fix is a normal edit — no baseline-dirty question
   arises. The spec must stay untouched; H1 requires no spec change, and the 1-anchor constraint is
   not in play.
4. **Nothing else in the audit is open.** Every item R2 routed to R3 is closed and independently
   re-derived here. The deferred-work catalog's eight items are confirmed as the audit recorded them,
   with the four checkable ones re-measured above. The final gate inherits the catalog and the two
   `--exclude` globs, and nothing else.

### Review outcome

`revision-needed`, routed to **Worker 1** per the plan's Deviation 2 corollary (no Worker 2 exists on
a Worker-1-exclusive deliverable; Worker 1 performs the apply-changes pass and sets `planned` again).

One High finding, at two sites in the durable rationale, both a false statement of repository history
that one command disproves. This is not a convergence call the sixth review pass may wave through: the
dispatch's own bar is "something that would mislead a reader of the durable spec or rationale", and a
sentence telling that reader a section never existed — when the card's own commits created and
destroyed it — is squarely that. The three Lows are scratchpad-only and are discharged in this section
rather than routed; they need no work from Worker 1.

The F1 fix itself is otherwise sound and should be kept: the defect was real, the edit rather than a
record was the right disposition, the anchoring repair is right, and dropping the unbounded absolute
rather than re-anchoring it is right. What is owed is the fourth part — the absolute that was kept.

---

## Apply-changes pass (Worker 1, pass 2) — H1

Fresh invocation, no context from the audit pass. Routed here rather than to Worker 2 per the plan's
Deviation 2 corollary. `HEAD` re-derived at open and close: `947f74948c16b20b0c15ff359bb53fbe462d4b8c`,
unchanged. No `pytest` ran, no `--cov*` flag was passed, no `git stash` / `checkout` / `restore` /
`worktree` was used, nothing was committed, no branch was created, no DB write was made. Files
written by this pass: the rationale, this artifact (this section plus the `Status:` line), and
`docs/builder/worker-memory/spec-007-worker-1.md`.

### The five git facts, re-derived in this pass

Not copied from the review. Each command was run here; output verbatim.

```text
$ git show 83c25963:docs/README.md | grep -n 'Three-minute'
42:## Three-minute path

$ git show 3a4d40b7 -- docs/README.md | grep 'Three-minute'
-## Three-minute path

$ git show 4b8dce07:docs/README.md | grep -c 'Three-minute'
0

$ git show 231911a8:docs/README.md | grep -c 'Three-minute'
0

$ git merge-base --is-ancestor 83c25963 HEAD ; echo $?
0
```

Commit identity, also re-derived rather than inherited:

```text
$ git log -1 --format='%H %ad %s' --date=short <each>
4b8dce07  2026-05-05  Start consolidation of specs and updated docs;
83c25963  2026-05-05  Finish consolidation of specs and doc files;
3a4d40b7  2026-05-05  Finish consolidation of docs;
231911a8  2026-05-08  Release 0.0.4;
```

The section body at `83c25963` is five numbered steps, the last of which points at `FEATURES.md` for
the capability catalog — the file the `## Scope` 3 entry already records as the pre-rename name of
[`docs/GLOSSARY.md`][glossary]. So the deleted section is internally consistent with the rest of the
record; nothing about it was aspirational.

**One sixth fact, measured here and not in the review, because the corrected prose needed it.** The
review and the plan's eighth correction both describe the interval as "three months". It is not:

```text
$ git log --diff-filter=A --format='%H %ad' --date=short -- '*spec-007-onboarding_docs_spec_consolidation-0_0_4.md'
81e4704d 2026-06-01

$ git show 81e4704d:docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md | grep -n 'three-minute'
27:- `docs/README.md` is code-first: quickstart, three-minute path, optimizer behavior, and status.
```

`3a4d40b7` (2026-05-05) to `81e4704d` (2026-06-01) is **twenty-seven days**, and that add-commit is
the earliest appearance of this spec path in history, already carrying the bullet. The rationale
therefore says twenty-seven days. This is the defect vector arriving in the dispatch itself: an
interval written beside the argument it supports rather than measured, propagated from the plan's
correction into the review and into this pass's instructions. It changes nothing about H1's substance
— the section was gone before the release either way — and it is routed to the plan below, not fixed
there.

### How both sites were rewritten, and the third that existed

**Site 1 — `### \`## Scope\` 2`, the closing sentence.** `There never was a section by that name.` is
replaced by the measured history, written as a record and not as a correction narrative: the section
existed, card 7's own commits are the whole of its lifetime, `83c25963` created it and `3a4d40b7`
removed it on 2026-05-05, `231911a8` three days later already carries no occurrence, and the spec
path first enters the tree twenty-seven days after the deletion with the bullet intact. The
preceding, present-tense sentence — "names no section anywhere in the repository" — is true and
untouched, as is the anchored surface count F1 installed.

**Site 2 — `## Standing note`, the mechanism enumeration.** `a section that never existed` becomes
`a section the card's own commits created and deleted on one day (\`83c25963\` then \`3a4d40b7\`)`, and
a short paragraph after the bullet says why that mechanism is the sharpest one in the list: every
other entry is a *later* commit than card 7's falsifying the claim, this one is the authoring card
falsifying itself before its own release. **The enumeration gained substance and lost nothing** — it
still lists the same number of mechanisms, and no count word in the bullet changed.

**A third site existed.** `grep -n 'never was\|no such section\|names no section\|never existed\|named
nothing\|did not exist\|no section'` over the whole rationale, then a second sweep for paraphrases
(`aspirational\|fiction\|phantom\|nonexistent\|non-existent\|was never\|never a section\|invented`),
returned the reconciliation record's `docs/README.md` bullet: **`"Three-minute path" named nothing and
is deleted rather than moved`**. The review judged it defensible in context and left the call to
Worker 1. It is scoped rather than left: **`has named nothing since \`3a4d40b7\``**. Six words, no
history retold, so the DRY constraint the review restated — the corrected history belongs in the
extraction entry and in the enumeration as a distinct mechanism, not a third time — holds. Both
sweeps' surviving hits are unrelated (`## Scope` 3's true claim about the `FEATURES.md` rename, the
preamble's "never deliberated") or are the retired clause quoted inside the correction record below.

**Named on disk.** A paragraph is appended to `### What the audit of this record changed in it`,
stating what the clause said, what the commits show, that the enumeration now carries the mechanism,
that the third site is scoped, that no spec change was involved, and the rule the survival yields —
*a present-tense command cannot verify a past-tense claim.* It is scoped to this pass and does **not**
extend that section's existing "four statements" / "two further statements" / "one statement" counts,
the same discipline the F1 fix observed.

### The three Lows

Left as the review discharged them. No edit is owed, none was made, and none of the three touches a
durable file. Re-stating them here would extend a disposition that is already complete.

### Files touched

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/appx/spec-007-…-0_0_4-rationale.md` | 641 lines / 43,502 bytes | **666 lines / 45,677 bytes** | +25 / +2,175 |
| `docs/builder/bld-007-r3-doc_completion_archive.md` | 1,068 lines / 68,295 bytes | **1,286 lines** | +218 lines (bytes omitted: the row measures the file that contains it, so writing the byte count changes it) |
| `docs/builder/worker-memory/spec-007-worker-1.md` | 70 lines / 5,970 bytes | consolidated + appended, gitignored | — |

Both rationale figures are `wc -lc` on the working tree, the before-figure taken at this pass's open
and the after-figure after the last edit. The file is untracked, so there is no committed state to
measure against and none is implied.

**The spec was not edited.** `wc -lc` reads **57 lines / 2,983 bytes** at this pass's open and close;
`git diff --numstat` on it reads `20 28`, byte-identical to what R2's final verification left and
what the audit pass recorded. `## Scope` bullet 2 and its glossary link were never touched, so the
1-anchor constraint was again not exercised.

### Validation run

Verbatim, with exit status, run after the edits.

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md docs/builder/bld-007-r3-doc_completion_archive.md
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0
```

**The glossary chain re-checked rather than trusted**, because the anchor moved once mid-cycle under a
concurrent regenerate. The spec's `[glossary-djangooptimizerextension]` definition resolves to
`../GLOSSARY.md#djangooptimizerextension`; `grep -n '^## \`DjangoOptimizerExtension\`' docs/GLOSSARY.md`
returns **716** — the post-regenerate line, not the 712 the audit first read. Cited by heading, not by
line, in every durable file.

### Link scaffold of the rationale, re-verified

Run as one script over the file as written, code spans and fences stripped before the inline sweep:

```text
headers in order:      True (10, exactly the canonical list, exact order)
definitions:           15
undefined used:        []
unused defs:           []
unresolved targets:    []
```

Every definition was disk-checked from `docs/SPECS/appx/`. The depth trap is intact and visibly so:
`[readme]: ../../README.md` resolves to `docs/README.md` and `[root-readme]: ../../../README.md`
resolves to the root — two distinct existing files, so neither is masking the other. `[spec-006-rationale]`
still resolves and is still untracked; the sibling cycle is still live at its own R3.

`grep -cE '[a-zA-Z_/]+\.(py|md):[0-9]+'` on the rationale returns **0** — `AGENTS.md` rule 27 holds;
raw `path:NN` appears only in this artifact. Two lines in the rationale exceed 110 characters (line 1,
the title, at 123; line 365 at 115). Both pre-date this pass, both were recorded by the audit pass,
and both are outside any paragraph this pass wrote — three lines this pass's edits pushed over 110
were re-wrapped before the close, so the file adds none.

### Working-tree churn and baseline

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` reads **30 entries** at this
pass's open and close — **no growth caused by this pass**, and **one more than the 29** the audit and
the review each recorded at their closes. The delta is not this cycle's: `docs/review/rev-_cross_web_patches.md`
now reads ` M` rather than `D`, so the escalated `docs/review/` set is currently **four deletions plus
one modification**, not the five deletions the plan's growth sections list, and its mtime (13:00) is
after the audit pass's own close. Escalated and unresolved either way, untouched here. `HEAD` is
`947f7494` at open and close, and `git log --stat` over this cycle's paths still returns only
`1592bb90` / `e1f9ed26` / `81e4704d`, all long predating the cycle — nothing this cycle wrote was
swept into a concurrent commit. `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, and
`examples/fakeshop/db.sqlite3` were read only. The concurrent spec-002 / spec-006 paths and the third
session's four source and test files were not read for content and not touched.

### Notes for Worker 1 (spec reconciliation)

Extends the notes in `bld-007-r1`, `bld-007-r2`, the audit pass's, and the review's; nothing in any of
them is retracted.

1. **Plan-level, for Worker 0: the eighth correction's own interval is unmeasured.** The D6 correction
   says the card "wrote the section, named it in its scope, and removed it again the same day; the
   scope bullet outlived the thing it described by three months." The first clause is exactly right.
   The second is wrong: the spec path first enters history at `81e4704d` (2026-06-01), **twenty-seven
   days** after `3a4d40b7`, already carrying the bullet. D6's conclusion and the correction's whole
   point are unaffected. Routed here rather than edited, because the plan is not this pass's to write.
   Worth noting that this is the cycle's own defect class reaching the correction that documents the
   cycle's own defect class — the number sat beside the argument it supported and no command produced
   it.
2. **The tenth instance is closed, and its rule is the narrowest one this cycle has produced.** Not
   "check your counts" and not "measure as you write", but: **a quantifier's tense selects its
   command.** A present-tense absolute is tested against the working tree; a past-tense or unbounded-
   historical absolute is tested against a named commit and against nothing else. The two halves of
   the H1 sentence differed only in tense, one was verified and one was not, and the verified one's
   command was structurally incapable of reaching the other.
3. **The final gate inherits nothing new.** The deferred-work catalog's eight items and the two
   `--exclude` globs stand exactly as the audit and the review left them; H1 added no deferral, closed
   no catalog item, and required no spec change. Item 1 above is a plan note for Worker 0, not a
   catalog entry — it corrects a correction, and the plan is where corrections to the plan live.
4. **For the re-review, the one thing to test first.** Every past-tense assertion in the two rewritten
   passages, against the commit it names. There are six of them and they are all in the block quoted
   at the top of this section.

### Status

`planned`. The High finding is discharged at all three sites — two named by the review, one it left to
Worker 1's judgement — the spec is untouched and re-measured at 57 / 2,983, all three obligatory
checks pass, and the link scaffold is intact. Back to Worker 0 for a re-review.

---

## Review (Worker 3, pass 2) — re-review of H1's closure

Fresh invocation, no context from pass 1 or from the apply-changes pass. Every fact below was
re-derived by its own command in this pass; nothing is reproduced from the artifact, the plan, the
dispatch, R1, or R2. **No working-tree grep was used to test any past-tense claim** — that
substitution is how H1 arrived, and the whole of this pass's history work runs through `git show`,
`git log`, `git rev-list`, and `git merge-base`.

`HEAD` re-derived at open and close: `947f74948c16b20b0c15ff359bb53fbe462d4b8c`, unchanged. No
`pytest` ran, no `--cov*` flag was passed, no `git stash` / `checkout` / `restore` / `worktree` was
used, nothing was committed, no branch was created, no DB write was made. Files written by this pass:
this artifact (this section plus the `Status:` line) and
`docs/builder/worker-memory/spec-007-worker-3.md`.

### The history, re-derived from commits rather than from the tree

Every one of pass 1's and the apply-changes pass's git facts reproduces, and four more were measured
here that neither pass ran.

```text
$ git show 4b8dce07:docs/README.md | grep -c 'Three-minute'      -> 0
$ git show 83c25963:docs/README.md | grep -n  'Three-minute'     -> 42:## Three-minute path
$ git show 3a4d40b7 -- docs/README.md | grep -n 'Three-minute'   -> 15:-## Three-minute path
$ git show 231911a8:docs/README.md | grep -ic 'three-minute'     -> 0   (case-insensitive)
$ git merge-base --is-ancestor 83c25963 HEAD ; echo $?           -> 0

$ git log -1 --format='%H %ad %s' --date=short <each>
4b8dce07  2026-05-05  Start consolidation of specs and updated docs;
83c25963  2026-05-05  Finish consolidation of specs and doc files;
3a4d40b7  2026-05-05  Finish consolidation of docs;
231911a8  2026-05-08  Release 0.0.4;
81e4704d  2026-06-01  docs: archive prior specs to docs/SPECS/ and renumber per Step 8 pass
```

**New in this pass, because the rewritten prose makes claims the earlier passes did not test:**

1. **"card 7's own commits are the whole of that section's lifetime" — proved over all refs, not
   inferred from four spot commits.** `git log --all --oneline -S'## Three-minute path'` returns
   **exactly two commits, `3a4d40b7` and `83c25963`**. No other commit in any ref ever added or
   removed that heading, anywhere in the tree. The universal in the durable sentence is therefore
   measured, not assumed.
2. **"the same day's next commit has already removed it" — exact, not approximate.**
   `git log -1 --format='%P' 3a4d40b7` → `83c259633e40…`. `83c25963` is `3a4d40b7`'s **parent**, so
   "next commit" is literally true rather than a same-day paraphrase.
3. **"the file this spec renders from first enters the tree at `81e4704d`" — the near-miss checked.**
   `git log --all --diff-filter=A` over the spec path returns `81e4704d` **and `78b69d76`**, same
   subject, same date `2026-06-01`. `git merge-base --is-ancestor 78b69d76 HEAD` → **non-zero;
   `78b69d76` is NOT an ancestor of HEAD** (a rewritten twin, the standing hazard in this repo). On
   main history `81e4704d` is genuinely the first appearance, and it carries the bullet:
   `git show 81e4704d:<spec> | grep -n 'three-minute'` → line 27. The claim survives the one check
   that could have falsified it.
4. **The "five-step body" is five steps.** `git show 83c25963:docs/README.md` — steps 1-5, the fifth
   reading "Read [`FEATURES.md`](FEATURES.md) when you want the full capability catalog", which is
   internally consistent with the `## Scope` 3 entry's record of the `FEATURES.md` → `GLOSSARY.md`
   rename. The rationale's description of the body is accurate.

**The twenty-seven days, re-derived.** `3a4d40b7` 2026-05-05 → `81e4704d` 2026-06-01 is **27 days**
(`datetime.date(2026,6,1) - datetime.date(2026,5,5)`), and `231911a8` 2026-05-08 is **3 days** after
`3a4d40b7` — the second interval the rewritten sentence asserts, which neither the apply-changes pass
nor the dispatch called out. Both hold. Worker 0 has already folded the correction into the plan: the
eighth correction now reads "twenty-seven days" with the `3a4d40b7` → `81e4704d` derivation and an
explicit note that "three months" was unmeasured, so the apply-changes pass's routed note 1 is
**actioned, not outstanding**.

### H1 is closed at all three sites, and there is no fourth

**Site 1 — `### \`## Scope\` 2`, rationale lines 214-223.** The `There never was a section by that
name.` absolute is gone. In its place: "**It did name a section once, and card 7's own commits are the
whole of that section's lifetime.**" followed by the measured chronology — `83c25963` created it with
a five-step body, `3a4d40b7` removed it, both 2026-05-05; `231911a8` three days later carries no
occurrence; the spec path first enters the tree at `81e4704d` (2026-06-01) with the bullet intact, so
the section had been gone twenty-seven days when the bullet was rendered into a present-tense spec.
Every clause of that has its own command above. The present-tense half beside it — "names no section
anywhere in the repository" — is unchanged and still true, and the F1 anchored count ("when this
record was written … exactly three surfaces") is untouched.

**Site 2 — `## Standing note`, rationale lines 402-417.** `a section that never existed` is now
`a section the card's own commits created and deleted on one day (\`83c25963\` then \`3a4d40b7\`)`.

**Site 3 — the reconciliation record's `docs/README.md` bullet, line 511.** Now
`"Three-minute path" has named nothing since \`3a4d40b7\``. Six words, scoped, no history retold, so
the DRY constraint pass 1 restated is respected: the chronology lives once (site 1) and appears once
more as a *distinct mechanism* (site 2), which is not a restatement.

**The fourth-site sweep, run independently and not accepted from the apply-changes pass's account.**
Two forms over the whole rationale and over the spec:

```text
$ grep -nEi 'never|no such|nothing|not exist|non-?existent|phantom|imagin|fiction|absent|
             unreal|made up|made-up|no section|any section|a section' <rationale>
   -> 47 hits, every one inspected
$ grep -nEi 'never|three-minute|not exist|nothing' <spec>
   -> exit 1, no hits
```

**No fourth site exists.** The three near-misses in the 47 are each a different subject and each
already verified elsewhere in this cycle: line 368 "a card section that does not exist in the database
at all" (`## Other`, true — `Card.planning_note` is `''` and no such section exists in the DB), line
373 "That heading does not exist" (`CONTRIBUTING.md`'s stale `BUILD.md` citation — re-confirmed below),
and line 246 "did not exist under that name when the card shipped" (`docs/FEATURES.md`, true). The
remainder are `*Nothing moved.*` disposition labels and unrelated prose. **The spec carries no such
claim at all**, so H1 never reached it.

### Did the rewrite introduce the eleventh instance? One Low, no defect

Every past-tense assertion in the new prose was checked against a named commit; all of them hold, and
the list is above. Three specific traps were checked because they are where this cycle's defect class
has landed before:

- **A historical interval written beside its argument.** Two intervals are asserted — twenty-seven
  days and three days — and **both** were measured here. The apply-changes pass caught the first in
  its own dispatch material; the second it wrote without flagging, and it is correct.
- **A universal over history.** "card 7's own commits are the whole of that section's lifetime" is the
  one universal in the new prose and it is the strongest kind of claim in the file. Proved by the
  all-refs `-S` sweep above, which is the command the class requires.
- **A universal over the enumeration.** "Every other mechanism in the list is some *later* commit than
  card 7's own" — checked member by member: `2bd7cb84` **2026-05-16** and `40c1855f` **2026-05-20** are
  both later than 2026-05-05; the generator-authorship and later-release mechanisms name no commit but
  are later by the file's own dated chain (the board was seeded after `40c1855f`, the spec rendered
  2026-06-01). It holds. That two of the four carry no hash is a looseness in a characterisation, not
  a false claim, and naming them would duplicate rows the file already dates elsewhere.

**Low 1 (durable, non-blocking, escalated below): an unattributed count with an unstated population.**
Rationale line 626: "**The clause survived two passes** because the pass that rewrote its sentence
re-verified it with a working-tree `grep`." The `because` explains one pass — the archive audit. Which
two the number ranges over is not stated, and the file's own correction record names **three** editing
passes between the extraction that wrote the clause and the review that caught it (the reconciliation,
this cycle's final verification of the reconciliation, and the closing archive audit), before counting
any review pass. Under the "passes that edited this file" reading it is two; under the file's own
enumeration it is three. This is the shape this reviewer's R1-pass-3 carry-forward names — *the
unstated class boundary, not the missing member*. **Resolution paths for Worker 1** (either closes it,
and it does not block): name the population ("the two passes that edited this file after the
extraction"), or drop the number ("The clause survived every pass until the review of the audit that
rewrote its sentence"). The sentence's payload — *a present-tense command cannot verify a past-tense
claim* — is correct either way and is the most useful rule this cycle has produced.

### The enumeration survived intact

Checked as arity, not as prose. `## Standing note`'s content-inventory bullet reads
"**Every one of them failed**, by a different mechanism each time:" — **no count word anywhere in the
bullet**, so none could have drifted. The membership is unchanged at **five mechanisms**: content
relocated (`2bd7cb84`), the card's own create-and-delete (`83c25963` then `3a4d40b7`), a rename sweep
substituting the subject (`40c1855f`), a generator taking over authorship, and a later release doing
the thing the card promised it would stop doing. The replacement was **1:1** — pass 1 quoted the prior
form and its second slot held `a section that never existed`, so the substitution neither added nor
removed a member. The claims the mechanisms answer to are also unchanged (the compound changelog claim
supplies two, which is why five mechanisms answer four sentences, and that pairing pre-dates this
pass). The new paragraph's "**The second of those** is the sharpest illustration" indexes the second
slot, which is the create-and-delete mechanism — correct after the substitution, and it would have
been the tell if the list had been reordered.

### No regression

| Check | Command this pass | Result |
|---|---|---|
| Spec untouched | `wc -lc` / `git diff --numstat` | **57 / 2,983**; `20 28` — unchanged from R2's close |
| Spec `## Scope` bullet 2's glossary link | `grep -n 'optimizer behavior'` | line 19, `[optimizer behavior][glossary-djangooptimizerextension]` — byte-identical to the DB `raw_text` and the CSV `term` column |
| Spec structure | `grep -n '^## '` | `9:## Card snapshot`, `14:## Scope` — the two anchors the rationale's fragments target |
| Rationale scaffold | one script over the file | **10 canonical headers, exact order**; **15 definitions**; undefined-used `[]`; unused-defs `[]`; unresolved `[]`; no inline `](path)` survivors |
| Depth trap | per-file resolution | `[readme]: ../../README.md` → `docs/README.md`; `[root-readme]: ../../../README.md` → root `README.md` — two distinct existing files, neither masking the other |
| Raw `path:NN` | `grep -cE '[a-zA-Z_/]+\.(py\|md):[0-9]+'` | **0** on the spec, **0** on the rationale |
| Over-110 lines in the rationale | `awk 'length>110'` | exactly **1 (123)** and **365 (115)**, both pre-dating this pass — the apply-changes pass added none |
| Rationale size | `wc -lc` | **666 / 45,677**, matching its own `### Files touched` row |

**The glossary anchor, re-checked rather than trusted from either reading.**
`grep -n '^## \`DjangoOptimizerExtension\`' docs/GLOSSARY.md` → **716**. It has not moved again since
the concurrent regenerate. **Every durable citation of it is symbol- or anchor-qualified**, verified
by the negative: `grep -n '\b71[26]\b'` over the spec and the rationale returns **no hits at all**, so
neither 712 nor 716 appears in either durable file. The spec cites it as
`[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension`, an anchor the checker
validates, and the rationale cites the heading by name.

### Validation run (this review pass, verbatim)

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

$ grep -n '^## `DjangoOptimizerExtension`' docs/GLOSSARY.md
716:## `DjangoOptimizerExtension`
```

`import_spec_terms` was run read-only (`--check`); no DB write was made by this pass.

### The staged-anchor sweep, and what the final gate needs

Both forms re-run here, and the excluded population re-enumerated by `find` rather than taken on
anyone's word:

```text
$ grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' .
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:34
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:259
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:295
exit=0

$ grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' . --exclude='build-007-*.md' --exclude='bld-007-*.md'
exit=1

$ find . -path ./.git -prune -o \( -name 'build-007-*.md' -o -name 'bld-007-*.md' \) -print
./docs/builder/bld-007-r3-doc_completion_archive.md
./docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md
./docs/builder/bld-007-r2-spec_reconciliation.md
./docs/builder/bld-007-r1-rationale_move.md
```

**The true result is still zero staged anchors.** All three raw hits are the plan's own prose
describing the sweep; the two globs reach exactly this cycle's four files and can touch no shipped
file, no durable doc, and no other cycle's artifact. The three hits now sit at **34 / 259 / 295**
(pass 1 recorded 34 / 251 / 287, the audit 34 / 244 / 280) — Worker 0 has appended the plan's seventh
growth section since. Raw `path:NN` in a `bld-*.md` is exempt (`AGENTS.md` rule 27) and the drift is
nobody's defect; it is recorded only so the final gate does not read a stale line number as a moved
anchor. **`### Notes for Worker 1`'s item 4 is accurate and load-bearing: the final gate must apply
both `--exclude` globs or it will report this cycle's own prose as staged work.**

### The deferred-work catalog is a clean input for the final gate

The four mechanically checkable items re-confirmed here, independently of pass 1:

- **Item 1 (`CHANGELOG.md` `0.0.8` design-doc pointers).** Line 140 cites both spec files for release
  context; file is **437 lines / 100,289 bytes**. Live; `AGENTS.md` rule 21 keeps it a maintainer
  question.
- **Item 2 (`CONTRIBUTING.md` stale `BUILD.md` heading).** Line 11 cites `docs/builder/BUILD.md`
  "Spec filename pattern"; `grep -rn 'Spec filename pattern' docs/builder/BUILD.md` → **exit 1**, and
  the real heading is `## Spec and build-plan filename pattern` at **line 7**. Live, outside the
  writable set.
- **Item 3 (`KANBAN.md`'s "three-minute path" row).** `KANBAN.md` line **4794**, `KANBAN.html` **1**
  occurrence — both renders of card 7's `CardItem`. Correctly classified as **not** drift, and H1's
  closure strengthens the classification rather than disturbing it: the row was an accurate
  description of `docs/README.md` at `83c25963`.
- **Item 5** now has a second data point in Low 1 above — the same class in its population-boundary
  variant.

Items 4, 6, 7 and 8 are unchanged and nothing in this pass touched them. **The catalog's eight items
stand exactly as the audit and pass 1 left them; H1's closure added no deferral and closed none.**

### Public-surface, CHANGELOG, documentation sanity, declarations

- **Public-surface check:** `git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__`
  and the re-export list are unchanged. Two other package-source files are dirty from a third
  concurrent session; neither is `__init__.py`, and neither was read for content or touched.
- **CHANGELOG sanity:** `Not applicable; slice did not modify CHANGELOG.md.`
- **Documentation / release sanity:** applicable and performed. The one changed durable file is the
  archived rationale; its links resolve, its scaffold is canonical, the spec's card ID `DONE-007-0.0.4`
  and target `0.0.4` are unchanged, no KANBAN card moved, no script-rendered doc was regenerated by
  this cycle, and no staging language was introduced.
- **Ownership partition:** none declared, none owed.
- **Hot-path budget:** none declared; **no number owed and its absence is correct** — this item runs
  no package code.
- **Floor verification:** none in scope. The `## Final test-run gate` is `bld-007-final.md`'s and was
  not run here.
- **Failability proofs:** none owed and none recorded, correctly — the item introduces no boundary,
  guard, gate, or rejection path, so the mandatory re-run floor is satisfied by an **empty re-run
  set**, legal here precisely because no boundary meets it.
- **`scripts/review_inspect.py`:** not run; the helper is scoped to Python source with review-worthy
  logic and this item reads and writes Markdown only. Recorded as a skip with its reason.
- **Temp tests:** none created by any pass on this item; nothing to promote.

### What holds

- **The fix is the right kind of fix.** It did not retract a claim, it supplied the record a fact it
  had been missing — and that fact is the file's own sharpest evidence for its thesis. Site 2 gains a
  fifth distinct mechanism where a lesser repair would have deleted a list entry.
- **The third site was found by the apply-changes pass itself**, with a paraphrase sweep pass 1 did
  not require, and it was **scoped rather than rewritten** — six words, no chronology duplicated. That
  is the DRY-correct disposition and it was reached without being told.
- **The pass measured an interval in its own dispatch material and reported it instead of using it.**
  "Three months" came from the plan, through the review, into the instructions; twenty-seven days is
  what the commits say. Routing it to the plan rather than editing the plan is the correct boundary.
- **Every past-tense claim now names a commit**, and the two claims that a working-tree grep could
  never have reached — the lifetime universal and the first-appearance claim — are the two this pass
  attacked hardest. Both survived, including the `78b69d76` rewritten-twin near-miss.

### Convergence judgement — stated explicitly

**`review-accepted`.** This is the seventh review pass of the cycle and what remains is one wording
choice in one sentence of a change record, whose two available readings differ by the number two
versus the number three and whose payload is correct under both. It is not a fact about the
repository, not a fact about the spec, not an anchor, not a link, and not a count of anything a reader
would act on.

The bar the dispatch sets is "something that would mislead a reader of the durable rationale". H1 met
that bar squarely and was rightly held at `revision-needed`: a reader was being told a section never
existed when the card's own commits created and destroyed it. Low 1 does not come close — a reader who
takes "two passes" at face value draws no false conclusion about the repository, about card 7, or
about the record. Holding an eighth round for it would be manufacturing a finding, which the dispatch
forbids as explicitly as it forbids withholding one that matters.

And the finding is **not** withheld: it is stated above with its evidence and two resolution paths,
and escalated to Worker 1's final verification, which is running regardless. That is the correct
disposition for a durable-file cosmetic — it cannot use the scratchpad-supersession lever this cycle
established, because the sentence lives in an archived file rather than in a `bld-*.md`.

### Working-tree churn and baseline

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` reads **30 entries** at this
pass's open and close — **no growth caused by this pass**, and the same 30 the apply-changes pass
recorded. `HEAD` is `947f7494` at open and close.

The escalated `docs/review/` set is confirmed as the dispatch describes it and was not touched:
**four deletions** (`rev-_django_patches.md`, `rev-_strawberry_patches.md`, `rev-apps.md`,
`rev-conf.md`) **plus one modification** (`rev-_cross_web_patches.md`, back on disk with different
content). Escalated, unresolved, untouched by anyone in this cycle; `AGENTS.md` rule 22's remedy
(`git checkout HEAD -- docs/review/`) is banned in this cycle, so it stays the maintainer's call.
`docs/review/review-0_0_14.md` and `docs/review/rev-_boundary_ordering.md` were not touched. All four
generated/binary files (`KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`)
are dirty from the concurrent spec-006 cycle's authorized glossary completion and were **read only**.
The concurrent spec-002 / spec-006 paths and the third session's four source and test files were not
read for content and not touched.

### Notes for Worker 1 (spec reconciliation)

Extends the notes in `bld-007-r1`, `bld-007-r2`, this item's audit pass, pass 1, and the apply-changes
pass; nothing in any of them is retracted, and every closure listed as un-reopenable stays closed —
including, now, H1 itself and its three sites.

1. **`Escalated:` Low 1, the only open item and non-blocking.** Rationale line 626's "survived two
   passes" — unstated population, two defensible readings (two, or three) — with both resolution paths
   given in its finding above. Take either, or record a rejection reason; it does not gate the final
   gate.
2. **Item 1 of the apply-changes pass's notes is already actioned**, so do not route it again: Worker 0
   has folded "twenty-seven days" and the `3a4d40b7` → `81e4704d` derivation into the plan's eighth
   correction, with the "three months" provenance recorded rather than quietly fixed. Re-derived here.
3. **The final gate inherits exactly two things** and they are both accurate as written: the
   deferred-work catalog's eight items (four re-confirmed above) and the two `--exclude` globs for the
   staged-anchor sweep. Without the globs the gate re-reports this cycle's own prose as staged work;
   the plan's three hit lines have already moved twice, so match on the file, never on the line number.
4. **The rule this item produced is worth carrying past the cycle.** *A quantifier's tense selects its
   command.* Present-tense absolutes are tested against the working tree; past-tense and unbounded-
   historical absolutes are tested against named commits, over **all refs** where the claim is a
   lifetime — and a rewritten twin commit on a non-ancestor ref is the trap that makes `--all` plus
   `merge-base --is-ancestor` the pair, not `--all` alone.

### Review outcome

`review-accepted`, with one Low escalated to Worker 1's final verification and no work owed before it.
H1 is closed at all three sites, a fourth was swept for independently and does not exist, the
enumeration's arity is intact, the spec is untouched at 57 / 2,983 with its glossary link byte-
identical, the rationale's scaffold and depth trap hold, both durable files carry zero raw `path:NN`,
and all three obligatory checkers reproduce verbatim. Worker 1's final verification has a clean input.

---

## Final verification (Worker 1)

Fresh invocation, no context from the audit pass, from either review, or from the apply-changes pass.
Every figure, path, count, and history fact below was produced by its own command in this pass;
nothing is reproduced from the plan, from R1, from R2, or from any prior section of this artifact —
those are verified floors, not sources. `HEAD` re-derived at open and close:
`947f74948c16b20b0c15ff359bb53fbe462d4b8c`, unchanged. No `pytest` ran, no `--cov*` flag was passed,
no `git stash` / `checkout` / `restore` / `worktree` was used, nothing was committed, no branch was
created, **no DB write was made and none is owed**. Files written by this pass: the rationale, this
artifact (this section plus the `Status:` line), and `docs/builder/worker-memory/spec-007-worker-1.md`
(gitignored, consolidated before the entry was appended).

### The escalated Low — closed by dropping the count

Path chosen: **drop the count**, the second of the two the re-review offered. The first — naming the
population — would have required asserting a number over a set whose boundary the re-review itself
showed to be genuinely ambiguous, and the sentence's payload does not rest on it.

The sentence as it stood, at rationale line 626:

> Nothing in the spec was touched by this correction either. **The clause survived two passes**
> because the pass that rewrote its sentence re-verified it with a working-tree `grep`, which can test
> only the present-tense half standing beside it: **a present-tense command cannot verify a past-tense
> claim, and an absolute about history needs a command that names a commit.**

As it now stands:

> Nothing in the spec was touched by this correction either. The clause was re-endorsed rather than
> caught by the archive audit that rewrote its sentence: the audit kept it on the strength of a
> working-tree `grep`, which can reach only the present-tense half standing beside it — **a
> present-tense command cannot verify a past-tense claim, and an absolute about history needs a
> command that names a commit.**

The count is gone rather than restated. What replaced it is not a smaller number: it is the causal
claim scoped to the one pass that claim actually explains — the archive audit, whose own `## 7`
records keeping the clause "because it is true and re-verified" on a working-tree `grep`. That is the
half of the original sentence the re-review found sound, and it survives with its subject named
instead of counted.

**Named on disk, in the same discipline every prior correction in this cycle used.** A short paragraph
follows it in `### What the audit of this record changed in it`, saying which count was dropped,
quoting the retired clause, and giving the reason. It is scoped to this pass and does **not** extend
that section's existing "four statements" / "two further statements" / "one statement" counts — the
route escalated at R2 and declined at every pass since.

**Did the fix introduce the eleventh instance? No — checked, not assumed.** The cycle's defect class
is a quantifier written beside the argument it supports rather than measured in its own command. The
replacement prose was scanned for one:

```text
$ sed -n '626,634p' <rationale> | grep -nEi 'never|every|all |always|only|two|three|four|exactly'
3:working-tree `grep`, which can reach only the present-tense half standing beside it — **a
7:This item's final verification then dropped the count that sentence carried — it read "survived two
```

Two hits, neither a quantifier over a set. The first is "can reach **only** the present-tense half",
a statement about what a working-tree command is capable of reaching, which is a property of the
command and not a measurement — and it is the payload rule the whole paragraph exists to teach. The
second is the retired clause quoted inside quotation marks as the thing being retired, which is the
one place a dropped count must still appear. **No new number, interval, universal, or historical
absolute was written.**

The naming paragraph's own claims, each testable: that the sentence "named no population for the
number" — true of the text quoted above, which ranges over an unnamed set of passes; and that "the
rule it teaches does not depend on a count at all" — true, the rule is *a present-tense command
cannot verify a past-tense claim*, which carries no quantity.

### 1. R3's contract, judged against the plan's `### Residual scope` R3 clause

Each of the three limbs re-derived here rather than inherited, because the audit and both reviews each
re-derived them against a tree that has moved under all of them.

**(a) The durable docs describe the doc set the shipped card produced.** Every role the reconciled
`## Scope` assigns, checked against the file it names, this pass:

```text
$ grep -n '^## ' README.md
34 Why this package exists | 40 Why it's fast | 52 Is this for you? | 60 Status
83 Get started -> docs/README.md | 87 Project documentation | 98 Inspired by | 104 Contributing & Security
```

Eight `##` headings, none an operational step — which is what the reconciled bullet 1 asserts. The
`## Project documentation` map's eight reference ids were expanded from their definitions and
disk-checked: `readme`, `glossary`, `goal`, `today`, `tree`, `kanban`, `backlog`, `contributing` —
**eight entries, eight resolving targets**.

```text
$ grep -n '^## \(Installation\|Quick start\|Running the example project\|Nested connection indexing\)' docs/README.md
7:## Installation   16:## Quick start   175:## Nested connection indexing   852:## Running the example project

$ grep -n '^## ' CONTRIBUTING.md
15:## Getting started  25:## Running the test suite  33:## Linting and formatting
42:## Updating the package version  51:## Building  59:## Publishing        (all six, plus five others)

$ sed -n '3p' docs/GLOSSARY.md -> "Glossary of every public symbol … Every entry below has a stable anchor"
$ sed -n '3p' docs/TREE.md     -> "This file is the detailed layout reference."
$ sed -n '3p' CHANGELOG.md     -> "All notable changes to this project will be documented in this file."
```

Every role holds in the file the spec assigns it to, and the one claim the spec makes about a
*destination* — `CONTRIBUTING.md` owning the operational half the root README shed — resolves in all
six of its parts. **Nothing a durable doc is missing.**

**(b) The archive is complete in all three cross-reference directions, in the kanban DB, and in the
terms-CSV importability chain.**

*Outbound.* Both durable files' link blocks re-expanded from their own directories and disk-checked in
one script: spec **10 definitions, 10 resolve, 0 undefined-used, 0 unused**; rationale **15
definitions, 15 resolve, 0 undefined-used, 0 unused**; **10 canonical group headers in the exact
canonical order** in each. The depth trap is intact and visibly so, per file: from `docs/SPECS/`,
`[root-readme]` → root `README.md` and `[readme]` → `docs/README.md`; from `docs/SPECS/appx/`,
`[root-readme]: ../../../README.md` → root and `[readme]: ../../README.md` → `docs/README.md` — two
distinct existing files, neither masking the other.

*The three changes R2 made to this direction, re-checked.* `grep -c 'backlog\|BACKLOG'` on the spec →
**0** (retired, and the rationale still defines and uses `[backlog]`, resolving, so the pair as a whole
has not stopped referencing it). `grep -c '^## Other'` on the spec → **0**, and the `#other` sweep over
`*.md` / `*.py` / `*.csv` / `*.html` returns hits **only in this cycle's own `bld-007-r1` / `r2` / `r3`
scratchpads** — no durable file carries a live `#other` link and none dangles. The seven added spec
definitions are inside the 10/10 resolution above.

*Inbound.* `KANBAN.md` lines **140** and **4783**, `KANBAN.html` **1** occurrence, and DB `spec.path` all
read `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md`. All four generated/DB surfaces
were **read only**. `grep -rn 'spec-007'` over `docs/SPECS/*.md` and `docs/SPECS/appx/*.md`, excluding
spec-007's own pair → **no hit**: the zero-inbound-reference property still holds.

*Companion.* `docs/SPECS/appx/spec-007-…-terms.csv` — **2 lines**, header plus one data row, therefore
one row per anchor and importable. (Pass 1's Low 1 corrected the audit's "three lines" to two; the
file reads two here, so that Low is confirmed closed and the conclusion it did not disturb still
stands.)

*The kanban DB, read-only ORM this pass:*

```text
card_id DONE-007-0.0.4 | status done | version 0.0.4
spec.path  docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
spec.name  spec-007-onboarding_docs_spec_consolidation-0_0_4
glossary_links 1 -> raw_text='optimizer behavior' term.title='`DjangoOptimizerExtension`' term.anchor='djangooptimizerextension'
labels ['docs', 'internal', 'release'] | planning_note '' | items 14 all_complete True
```

**(c) The staged-anchor sweep is clean.** Both forms re-run, and the excluded population
re-enumerated by `find` rather than taken from any prior section:

```text
$ grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' .
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:34
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:259
docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md:295
exit=0

$ grep -rEn 'TODO\(spec-007|TODO-(ALPHA|BETA|STABLE)-007' . --exclude='build-007-*.md' --exclude='bld-007-*.md'
exit=1

$ find . -path ./.git -prune -o \( -name 'build-007-*.md' -o -name 'bld-007-*.md' \) -print
./docs/builder/bld-007-r3-doc_completion_archive.md
./docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md
./docs/builder/bld-007-r2-spec_reconciliation.md
./docs/builder/bld-007-r1-rationale_move.md
```

All three raw hits are the plan's own prose describing the sweep; the two globs reach this cycle's own
plan and artifacts and nothing else in the tree. **The true result is zero staged anchors**, and it is
a true zero rather than a hidden one. The hit lines have now moved a third time (audit 34/244/280,
pass 1 34/251/287, re-review 34/259/295, here 34/259/295) as Worker 0 appends growth sections —
**the final gate must match on the file, never on the line number, and must apply both `--exclude`
globs** or it will re-report this cycle's own prose as staged work.

### 2. The glossary chain, re-checked at this moment

The anchor moved once mid-cycle (712 → 716) under the concurrent cycle's authorized regenerate, and
`docs/GLOSSARY.md` is still dirty and still theirs. The three-way match now:

```text
$ grep -n '^## `DjangoOptimizerExtension`' docs/GLOSSARY.md
716:## `DjangoOptimizerExtension`
```

- **DB `raw_text` ↔ spec link text.** `'optimizer behavior'` against spec line 19's
  `[optimizer behavior][glossary-djangooptimizerextension]` — byte-identical.
- **DB `term.anchor` ↔ CSV `anchor` column.** `djangooptimizerextension` on both sides.
- **CSV `term` column ↔ DB `raw_text`.** `optimizer behavior` on both sides.
- **`SpecDoc.path`** reads the archived path; card 7's DONE invariants hold — a `SpecDoc` is linked and
  `glossary_links` is 1.

**No durable file cites the anchor by line number**, verified by the negative: `grep -n '\b71[26]\b'`
over the spec and the rationale returns **no hit at all**, so neither 712 nor 716 appears in either.
The spec cites the anchor as `../GLOSSARY.md#djangooptimizerextension`, which the checker validates;
the rationale cites the heading by name. `716` appears only in `bld-*.md` scratchpads, where
`AGENTS.md` rule 27 exempts it.

### 3. The deferred-work catalog — complete, accurate, and what the final gate must know

The audit recorded eight items. Each confirmed still live and correctly classified this pass:

1. **`CHANGELOG.md`'s `0.0.8` entry relies on design-doc pointers.** Live: line **140** cites both
   `spec-027-filters-0_0_8.md` and `spec-028-orders-0_0_8.md` for release context, definitions at
   **388-389**; the file is **437 lines / 100,289 bytes**, so "condensed" no longer describes it
   either. `AGENTS.md` rule 21 keeps it a maintainer question; reconciled in the spec at D9.
2. **`CONTRIBUTING.md` carries a stale citation of a `BUILD.md` heading that does not exist.**
   Confirmed live: `CONTRIBUTING.md` line **11** cites `docs/builder/BUILD.md` "Spec filename
   pattern"; `grep -rn 'Spec filename pattern' docs/builder/BUILD.md` → **exit 1**, and the real
   heading is `## Spec and build-plan filename pattern` at **line 7**. Real, outside the writable set.
3. **`KANBAN.md`'s "three-minute path" row is a Done card's historical record, not drift.** Confirmed
   live at `KANBAN.md` line **4794**, once in the `KANBAN.html` payload, both renders of card 7's
   `CardItem`; the card is `done` with all fourteen items complete. **The H1 history makes this
   sharper rather than weaker**: the row is not merely a stale phrase naming nothing — it was an
   accurate description of `docs/README.md` as it stood at `83c25963`. Editing the DB row would
   falsify a correct historical record. Catalogued so no later pass "fixes" it.
4. **The `docs/review/` set.** Escalated by R1, unresolved through this pass, untouched by anyone in
   this cycle. Current state confirmed by `git status --porcelain docs/review/`: **four deletions**
   (`rev-_django_patches.md`, `rev-_strawberry_patches.md`, `rev-apps.md`, `rev-conf.md`) **plus one
   modification** (`rev-_cross_web_patches.md`, back on disk with different content), and two
   untracked (`rev-_boundary_ordering.md`, `review-0_0_14.md`). `AGENTS.md` rule 22's remedy is banned
   in this cycle; only the maintainer can adjudicate and restore.
5. **The `BUILD.md`-level convention question Worker 3 escalated at R2.** Whether a durable figure
   must name both the commit and whether it is committed or working-tree state. Still unacted on; the
   Low closed above is a further data point in its population-boundary variant.
6. **`AGENTS.md` rule 27 does not name `build-*.md` plans.** Standing-doc question for the maintainer.
7. **The rationale is now 46,045 bytes against a 2,983-byte spec** (re-measured this pass; it was
   45,677 before this pass's two paragraphs). Not a defect and not this cycle's to fix.
8. **The concurrent spec-006 cycle names spec-007 as owner of four of its drift rows.** No conflict:
   spec-007's reconciled `docs/README.md` bullet names sections that exist, spec-006's rows name
   sections that do not. Disjoint. **One update for the final gate:** the out-of-scope concurrent
   files carrying the string `spec-007-onboarding_docs_spec_consolidation` are now **four**, not the
   three the audit recorded — `docs/builder/bld-006-r3-doc_completion_archive.md` has since appeared.
   That is the sibling cycle reaching its own R3; it changes nothing about the zero-inbound-reference
   property, which is scoped to `docs/SPECS/*.md`.

**The catalog is complete and accurate as an input.** Nothing was added, nothing closed, nothing
reclassified. What the final gate additionally needs, beyond the eight: the two `--exclude` globs, the
instruction to match the sweep's hits on the file rather than the line, and the plan's baseline
exception governing tree-wide gate commands.

### 4. Mechanical state, re-derived here

| Check | Command this pass | Result |
|---|---|---|
| Spec untouched | `wc -lc`; `git diff --numstat` | **57 / 2,983**; `20 28` — unchanged from R2's close |
| `## Scope` bullet 2's link byte-identical | `sed -n '19p'` vs DB `raw_text` | `[optimizer behavior][glossary-djangooptimizerextension]` ↔ `'optimizer behavior'` — identical |
| Spec structure | `grep -n '^## '` | `9:## Card snapshot`, `14:## Scope` — the two anchors the rationale's fragments target |
| Rationale scaffold | one script over the file, post-edit | **10 canonical headers, exact order**; **15 definitions**; undefined-used `[]`; unused-defs `[]`; unresolved `[]` |
| Depth trap, per file | per-file expansion + disk check | intact in both; `[readme]` and `[root-readme]` land on two distinct existing files |
| Raw `path:NN` | `grep -cE '[a-zA-Z_/]+\.(py\|md):[0-9]+'` | **0** on the spec, **0** on the rationale |
| Over-110 lines in the rationale | `awk 'length>110'` | exactly **1 (123)** and **365 (115)**, both pre-dating this pass — this pass added none |
| Rationale size | `wc -lc` | 666 / 45,677 → **672 / 46,045** |

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
OK: 1 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
exit=0        (re-run AFTER this pass's edit)

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0
```

**H1's history re-derived independently, not accepted from the two passes that argued it.** The
rewritten prose's past-tense claims each have their own command here:

```text
$ git log --all --oneline -S'## Three-minute path'      -> exactly 3a4d40b7 and 83c25963, no other ref
$ git log -1 --format='%P' 3a4d40b7                     -> 83c259633e40…   (83c25963 is its parent)
$ git show 83c25963:docs/README.md | grep -n 'Three-minute'   -> 42:## Three-minute path
$ git show 3a4d40b7 -- docs/README.md | grep -n 'Three-minute' -> 15:-## Three-minute path
$ git show 231911a8:docs/README.md | grep -ic 'three-minute'   -> 0
$ git merge-base --is-ancestor 83c25963 HEAD ; echo $?         -> 0
$ git merge-base --is-ancestor 81e4704d HEAD ; echo $?         -> 0
$ git log --all --diff-filter=A --date=short -- '*spec-007-…-0_0_4.md'
   earliest dated adds are 81e4704d and 78b69d76, both 2026-06-01; every other add is later
$ dates: 4b8dce07 / 83c25963 / 3a4d40b7 = 2026-05-05; 231911a8 = 2026-05-08; 81e4704d = 2026-06-01
$ intervals: 3a4d40b7 -> 81e4704d = 27 days; 3a4d40b7 -> 231911a8 = 3 days
$ enumeration's "every other mechanism is later": 2bd7cb84 = 2026-05-16, 40c1855f = 2026-05-20
```

Every clause of the rewritten passages holds. The twenty-seven days and the three days both reproduce.

**Concurrent-commit check, not `git status` alone.** `git rev-parse HEAD` → `947f7494…` at open and
close. `git log --stat` over this cycle's six paths returns `40e4754a` (2026-07-31), `1592bb90`,
`e1f9ed26`, `81e4704d` — every one long predating the cycle, and no commit landed during it.
**Nothing this cycle wrote was swept into a concurrent commit.**

### 5. "Make sure the code is correct" — discharged, stated plainly

**Spec-007 shipped five Markdown files and no code**, so the obligation resolves to proving the card
left no residue in source, and the sweeps return nothing:

```text
$ grep -rn 'three-minute' django_strawberry_framework/ tests/ examples/                       -> exit 1
$ grep -rn 'spec-007\|DONE-007\|onboarding_docs_spec_consolidation' <same trees> --include='*.py' -> exit 1
$ staged-anchor sweep, shipped source / tests / examples                                       -> clean
```

So the maintainer does not have to infer it from silence: **this cycle found no correctness defect in
shipped source, and there is none to find from spec-007.** No source, test, or example file was
written, reverted, or read for content by any pass in this item, the four a third concurrent session
is editing included.

### 6. Checklist audit, DRY, and the remaining role duties

**`### Dispatched findings checklist`.** All seven boxes are `- [x]` and each contract is confirmed
landed by the corresponding section above — obligation 1 by `### 1(a)`, 2 by `### 1(b)`, 3 by `### 2`,
4 by `### 1(c)`, 5 by `### 3`, 6 by the `[spec-006-rationale]` re-resolution below, 7 by `### 5`. No
box is over-ticked and none is silently un-ticked. No deferral reason is owed.

**`[spec-006-rationale]` (obligation 6), re-resolved a third time, now.** `ls` → present,
**57,777 bytes** (it has grown since the audit read 52,621, which is the sibling cycle still writing
it); `git ls-files --error-unmatch` → *"Did you forget to 'git add'?"*, still **untracked**. The
sibling cycle is demonstrably still live (`bld-006-r3-doc_completion_archive.md` on disk), so both
files still enter the maintainer's commit window together and R1's recorded reason still holds in both
its parts. The definition stays.

**DRY across this item and the prior accepted items.** No new duplication. This pass wrote two
sentences and one short paragraph, introduced no helper, no constant, and no restatement: the H1
chronology still lives once (site 1), appears once more as a distinct enumeration member (site 2), and
is scoped rather than retold at site 3 — the shape both reviews required. The naming paragraph does
not restate the retired sentence's history; it names the count it dropped and why.

**Focused tests.** None run and none owed: this item touches no source, and the dispatch and the plan
both forbid `pytest` in this pass. The `## Final test-run gate` is `bld-007-final.md`'s.

**Declarations, checked as absences and correct:** ownership partition none; hot-path none, so no
number is owed and its absence is correct; floor-verification scope none, so no floor run is owed by
this item; failability proofs none owed — this item introduces no boundary, guard, gate, or rejection
path. `scripts/review_inspect.py` not run, correctly — the helper is scoped to Python source with
review-worthy logic and this item reads and writes Markdown only. Public surface:
`git diff -- django_strawberry_framework/__init__.py` → **empty**. No temp tests exist.

### 7. Working-tree growth

Reported, never reverted (`AGENTS.md` rule 34). `git status --porcelain` reads **30 entries** at this
pass's open — the same 30 the apply-changes pass and the re-review each recorded — and **31** at its
close. **The one new entry is not this pass's.** Both files this pass wrote were already dirty
entries, so neither could add one. `HEAD` is `947f7494` at open and close.

**The eighth growth event**, attributed by mtime rather than by inference:

- `docs/builder/bld-006-final.md` (`??`) — mtime **13:34:47**, later than this pass's last edit to any
  file it owns (`13:32:02` on this artifact, `13:28:46` on the rationale) and later than its open
  reading. It is the concurrent **spec-006** cycle reaching its own final test-run gate, mirroring this
  cycle's next item. Out of this cycle's writable set, not read for content, not touched, not reverted.

One further out-of-scope file is worth naming because a prior growth section fixed its population at
four: the third concurrent session's package-source set is now **five**, not four —
`django_strawberry_framework/_cross_web_patches.py` (`M`, mtime **12:57:00**) joins
`_boundary_ordering.py`, `middleware/request_body.py`, `examples/fakeshop/test_query/test_transport_api.py`,
and `tests/test_views.py`. Its mtime **predates this pass's open**, so it was inside the 30 rather than
part of the growth. All five are declared read-only for this cycle and none was read for content or
touched.

`docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3` were **read only**;
all four are dirty from the concurrent spec-006 cycle's authorized glossary completion. The escalated
`docs/review/` set — four deletions plus one modification — is **untouched, unresolved, and still the
maintainer's call**. The concurrent spec-002 / spec-006 paths and the third session's four package
source and test files were not read for content and not touched.

### Summary

**R3's contract is delivered and the item is `final-accepted`.**

What this cycle changed, in one paragraph a maintainer can read at commit time without opening three
artifacts: **spec-007 is a 57-line card-snapshot stub whose every content claim about the `0.0.4`
documentation set had been falsified by later work, and this cycle moved it from an inventory to a
contract.** The spec now states only the **division of responsibility** the card established — which
document answers which question — and states it in claims that are true at HEAD; every claim it can no
longer make, with the commit or later card that falsified it, moved into a new, tracked companion,
`docs/SPECS/appx/spec-007-…-rationale.md` (672 lines / 46,045 bytes), which is the only record of the
`0.0.4` documentation-set history anywhere in the repository. The spec ends at **57 lines / 2,983
bytes**, its sole glossary anchor re-sited inside the surviving contract prose so the DONE-card chain
never broke, and **no source, test, example, generated doc, or database row was written by any pass** —
`docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3` are dirty only from
a concurrent cycle's authorized work. Four maintainer follow-ups the cycle found but may not fix
(`CHANGELOG.md`'s design-doc pointers, `CONTRIBUTING.md`'s stale `BUILD.md` heading citation, the
`docs/review/` deletions, and two standing-doc convention questions) sit in the deferred-work catalog
above, which is the final gate's input.

**The one recurring defect class, and the rule that would have prevented every instance.** Across
eleven passes this cycle produced ten instances of a single defect: **an unmeasured quantifier in
durable prose** — a number, count, interval, or absolute word written in the same sentence as the
argument it supports, rather than measured in its own command first. It migrated as each catching
discipline closed the previous form: first bare numbers, then universals and "only"-shaped absolutes
once numbers were being re-derived, then historical absolutes ("never", "always", an interval in
months) once present-tense universals were being grepped. The last of them, H1, sat in the *surviving*
half of the very sentence the previous instance was fixed in, and the interval in the plan correction
that documents the class was itself unmeasured — "three months" against a measured twenty-seven days.
The rule that would have caught all ten is one sentence: **a quantifier is a measurement, so only the
command that produced it may write it — and for a historical quantifier that command names a commit,
not the working tree.** Its two corollaries, both earned here: when a pass repairs one clause of a
sentence, that sentence's other clauses become that pass's claims too and each needs its own command;
and a rotted measurement is repaired by anchoring it to the state it measured, never by swapping in
the current number.

### Spec changes made (Worker 1 only)

**None.** The spec was not edited in this pass and was not edited by this item at all. It is verified
untouched at **57 lines / 2,983 bytes** with `git diff --numstat` reading `20 28` — byte-identical to
what R2's final verification left — and `## Scope` bullet 2's glossary link byte-identical to the DB
`CardGlossaryTerm.raw_text` and the CSV `term` column. The 1-anchor constraint was never exercised by
this item. Nothing outstanding reaches the spec.

**Rationale change made in this pass**, the only durable edit:
`docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`,
`### What the audit of this record changed in it` — the escalated Low closed by dropping the
"survived two passes" count and scoping the causal clause to the archive audit, plus one paragraph
naming the change on disk. **666 lines / 45,677 bytes → 672 / 46,045.**

### Final status

`final-accepted`. Worker 0 may tick R3's checkbox and dispatch the final test-run gate
(`docs/builder/bld-007-final.md`), which inherits the deferred-work catalog above, the two `--exclude`
globs for its staged-anchor sweep, and the plan's baseline exception for tree-wide gate commands.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
