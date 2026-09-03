# Build: Slice 0 — extract the deliberative layer into the rationale companion

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (whole file; the moved
regions were HEAD lines 98-138, 861-1877 in fourteen `Justification:` /
`Alternatives considered (and rejected):` pairs, 1136-1150, and 2148-2270)
Status: final-accepted

## Artifact shape: procedural-closure slice

This is a **procedural-closure slice** per [`docs/builder/BUILD.md`][build-md]
`### Procedural-closure slices`: one Worker 1 pass, no Worker 2 build, no Worker 3
review. `## Build report (Worker 2)` and `## Review (Worker 3)` are therefore **not
applicable** and are absent — there is no source diff for a builder to land and no
implementation for a reviewer to check. The slice's whole output is a documentation
move plus the mechanical link/gate repairs that move causes, and this artifact
carries one combined Plan + Final-verification block, with Worker 1 setting
`Status: final-accepted` directly.

The clause that authorizes the closure is the build plan's
`## Pre-flight record` step 7 (`Spec rationale extracted` — **Open — this is Slice
0**) read with `docs/builder/BUILD.md` `## Spec rationale extraction`, which makes
the move the first substantive action of every build and assigns it to Worker 1
alone. The plan's `## Checklist` names the slice as a "Worker 1 procedural pass, no
source diff".

Hot-path declaration: **none** (plan-wide `none`; this slice adds no runtime code).
Floor-verification scope: **none** (plan-wide `none`; this slice touches no Django /
Strawberry integration seam). The floor facts were not load-bearing for any
reasoning in this pass. For the record, the shared `.venv` read with `uv pip list`
carries Django `6.1` and strawberry-graphql `0.324.0` on Python `3.14.2` — above the
supported floor of Django `5.2.16` / Python `3.10` / strawberry-graphql `0.316.0`,
and not exercised by this pass.

## Plan + Final verification (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in the source sense — this slice
  writes no `.py` and proposes no helper, so the package-wide AST inventory
  (`worker-1.md` `### Package-wide helper inventory before helper planning`) has no
  candidate to search for. The analogous check for a documentation move is the
  **shape** inventory: the two most recent executions of this same move,
  `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` and
  `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md`, were both read in full
  before a line of the new companion was written.
- **Existing patterns reused.** The new file reuses the `037` / `036` companion
  shape exactly: the four-paragraph header (`Companion to …` / `Read this when …` /
  `**How later passes append to this file.**`), `## Provenance of this record`,
  `## Revision history`, one `## Decision N — <verbatim spec heading>` section per
  Decision carrying `Spec: [<heading>][spec-038-dN].` plus
  `### Justification (moved from the spec)` /
  `### Alternatives considered (and rejected)` /
  `### Changes this Decision underwent`, then `## Risks and open questions` and
  `## Non-Decision deliberation`. The spec side reuses `037`'s two pointer forms
  verbatim in structure: the header `This spec's deliberative layer — … lives in the
  rationale companion […]` paragraph and the per-Decision
  `Rationale companion — this Decision's justification and its N rejected
  alternatives: [Decision N][rationale-dN].` line.
- **New helpers justified.** None. No new section kind was invented.
- **Duplication risk avoided.** The one real risk in this slice is *copying* rather
  than *moving* — text surviving in both files. It is closed mechanically rather
  than by inspection: every moved block was captured verbatim from the pristine
  HEAD copy before the cut, and a post-move assertion confirms each block is present
  in the companion and **absent** from the spec (see `### Verbatim-move proof`). The
  second risk is the two held-back fragments becoming duplicates; both were elided
  from the moved text, and their elision is recorded in the companion's own
  provenance rather than left for a reader to notice.

### Implementation steps

Line numbers below are pin-at-write-time navigational hints against `HEAD`; every
one was re-derived from the pristine HEAD copy at edit time, not trusted from the
plan.

1. Verify the spec byte-identical to `HEAD` read-only, per
   [`docs/builder/BUILD.md`][build-md] `## Claims are proven mechanically, never
   accepted on prose` (no `git stash` / `checkout` / `restore` / `worktree`):

   ```shell
   git show HEAD:docs/SPECS/spec-038-form_mutations-0_0_12.md > "$SCRATCH/spec-038-HEAD.md"
   diff "$SCRATCH/spec-038-HEAD.md" docs/SPECS/spec-038-form_mutations-0_0_12.md && echo IDENTICAL-TO-HEAD
   ```

   → `IDENTICAL-TO-HEAD`. Every measurement in this artifact is against that copy.
2. Census the five moved block classes and re-derive every count (below).
3. Extract each block verbatim from the HEAD copy into a JSON side-file.
4. Cut the spec: replace each block with its pointer, delete the falsified
   revision-history preamble, re-point the four surviving in-page `Risks`
   references, hold back the two glossary-gated fragments, and add the sixteen new
   link definitions.
5. Assemble the companion from the extracted blocks plus this pass's framing prose.
6. Audit link definitions in both directions, on-disk paths, and in-page anchors.
7. Re-run `check_spec_glossary.py`, `ruff format --check`, `ruff check`, and
   `uvx pre-commit run --files` on the three touched files.

### Test additions / updates

None; this slice adds no code and therefore no test. The pass's own verification is
the four gates recorded under `### Gate results` plus the mechanical audits under
`### Link-definition audit` and `### Verbatim-move proof`. `pytest` was not run and
is not owed — no `.py` file was touched (`git status --short` over
`django_strawberry_framework/` shows only the concurrent session's pre-existing
baseline-dirty files, none of them this pass's).

### Implementation discretion items

- **Where the D6 cleaned-data-echo paragraph lands in the companion.** Assessed and
  decided: under that Decision's `### Alternatives considered (and rejected)` as an
  explicitly-labelled third entry, not under `### Changes this Decision underwent`.
  It is a rejected alternative, not a change the Decision underwent; `037` put a
  *supersession* block under `Changes` for the same structural reason in reverse.
- **The wording of the per-Decision `**Revision 1** pinned …` summaries.** Each is a
  compression of the clause the spec's own revision-history entry devotes to that
  Decision, so the summary and the verbatim entry above it cannot disagree.

### Spec slice checklist (verbatim)

The active spec's `## Slice checklist` describes the five **shipped** `0.0.12`
slices; it contains no sub-bullets for this cycle's Slice 0, which exists because
`docs/builder/BUILD.md` `## Spec rationale extraction` obliges it and not because
the spec asked for it. The checklist below is therefore the build plan's own Slice-0
line plus the four "What must be true of the spec afterwards" conditions the plan
and `worker-1.md` `### Performing the rationale move` impose, in the same position
and under the identical tick-and-audit discipline.

- [x] extract the deliberative layer into `docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` (pre-flight step 7; Worker 1 procedural pass, no source diff)
- [x] the move is a cut-and-paste, not a copy and not a summary: text that lands in the rationale file leaves the spec
- [x] every entry names the spec decision it belongs to by heading and anchor
- [x] every decision keeps a one-line pointer naming what was moved and where
- [x] prose the current decisions have falsified is deleted, not moved
- [x] the spec reads as a clean current contract — no amendment block, no retraction paragraph, no "as of review round N" hedge (**one exception, recorded and routed**: see `### Notes for Worker 1 (spec reconciliation)` item 1, which a move cannot discharge)
- [x] every surviving `][label]` in the spec has a definition and every definition has a use; the 10 canonical group headers stay present even when empty
- [x] the companion follows the same reference-style convention with its own bottom block and the same 10 group headers, and every path resolves on disk from `docs/SPECS/appx/`
- [x] `check_spec_glossary.py` still exits 0
- [x] `ruff format --check .` and `ruff check .` stay clean
- [x] `uvx pre-commit run --files <the three touched files>` is clean

### Byte counts

Command, quoted:

```shell
wc -c docs/SPECS/spec-038-form_mutations-0_0_12.md \
      docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md \
      "$SCRATCH/spec-038-HEAD.md"
```

| File | Bytes | Lines |
| --- | --- | --- |
| Spec **before** (`$SCRATCH/spec-038-HEAD.md`, byte-identical to `HEAD`) | 185,851 | 2,555 |
| Spec **after** | 164,240 | 2,227 |
| New companion `docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` | 55,325 | 901 |

The spec's net cut is **21,611 bytes** (185,851 − 164,240). That is **26,640 bytes
removed** by four routes minus **5,029 bytes added back**, and the reader can
re-derive both halves:

- removed, summing the four replaced ranges in the HEAD copy: 2,948 (revision
  history) + 12,581 (the fourteen justification+alternatives regions) + 1,094 (the
  D6 cleaned-data-echo paragraph and its trailing blank) + 10,017 (the Risks body) =
  **26,640**.
- added back: 373 (the header pointer paragraph) + 1,692 (the fourteen per-Decision
  pointer paragraphs) + 410 (the Risks pointer paragraph) + 2,314 (the sixteen new
  link definitions) + 204 (the two held-back fragments) + 36 (four re-pointed
  `Risks` references, `[Risks](#risks-and-open-questions)` → `[Risks and open
  questions][rationale-risks]`, +9 bytes each) = **5,029**. One paragraph was
  re-wrapped to keep a line under 85 characters after a re-point; that reflow is
  byte-neutral.

26,640 − 5,029 = 21,611. ✓

The companion is **larger** than the 26,640 bytes it received (55,325) because this
pass's own framing — the header, `## Provenance of this record`, the fourteen
`Spec:` pointers and `### Changes this Decision underwent` sections, the section
preambles, `## Non-Decision deliberation`, and its own link-definition block — is
new prose that says so in the file.

### Re-measured counts of each moved block class

Every number below was measured **as it was written**, against
`$SCRATCH/spec-038-HEAD.md`, and every one is stated in a form the reader
re-derives with a command rather than trusting.

| Block class | Count | Bytes | How to re-derive |
| --- | --- | --- | --- |
| `Justification:` blocks | **14** | 5,574 | `grep -oin 'ustification' <HEAD copy> \| wc -l` → 14, and all 14 are block labels (the word occurs nowhere else in the spec), so this is the population, not a vocabulary sample |
| `Alternatives considered (and rejected):` blocks | **14** | 6,993 | `grep -oin 'lternatives' <HEAD copy> \| wc -l` → 14, same reasoning |
| rejected alternatives inside those blocks | **25** | — | top-level `- **` bullets per block: 2 / 2 / 2 / 2 / 3 / 2 / 2 / 2 / 1 / 1 / 1 / 1 / 2 / 2 for Decisions 1-14 |
| `### Decision N` headings | **14** | — | `grep -c '^### Decision ' <HEAD copy>` → 14 |
| `## Risks and open questions` items | **14** | 10,017 (body incl. preamble) | top-level `- **` bullets between the section preamble and `## Out of scope` |
| …of those, carrying a `RESOLVED` marker | **9** | — | `sed -n '2148,2270p' <HEAD copy> \| grep -o RESOLVED \| wc -l` → 9, on 9 distinct items |
| D6 `Rejected (recorded, not silently dropped)` paragraph | **1** | 1,093 (1,094 with its trailing blank) | HEAD lines 1136-1149 |
| inline `Revision history` block | **1** (42 lines incl. its trailing blank) | 2,949 | HEAD lines 98-139: a 62-byte preamble, a 1-byte blank, a 2,885-byte `Revision 1` entry, a 1-byte trailing blank |

**The census used the shortest distinctive token deliberately.** Worker 0's plan
estimated "roughly 14" of each; grepping the full label phrase would have sampled
the vocabulary rather than established the population — a phrase wrapped across two
lines does not match. `ustification` / `lternatives`, counted case-insensitively as
*occurrences* rather than matching lines, are the shortest tokens that cannot miss a
wrapped label, and both returned exactly 14 with every hit a label.

**The 1:1 pairing is measured, not inferred from the equal counts.** The two label
line-lists interleave strictly — each `Justification:` at HEAD lines 861 / 904 / 929
/ 961 / 1030 / 1161 / 1434 / 1644 / 1670 / 1699 / 1729 / 1757 / 1829 / 1867 is
immediately followed by its `Alternatives considered (and rejected):` at 869 / 910 /
937 / 968 / 1038 / 1167 / 1442 / 1650 / 1676 / 1703 / 1734 / 1762 / 1839 / 1871, and
each pair sits under exactly one of the fourteen `### Decision N` headings at 857 /
879 / 920 / 945 / 979 / 1053 / 1185 / 1452 / 1658 / 1682 / 1709 / 1740 / 1769 /
1849. So no Decision needs the explicit `None.` the `037` companion had to carry
under a missing half.

The three block-class byte totals reconcile: 5,574 + 6,993 + 14 blank separator
lines = **12,581**, the combined removed region.

### Verbatim-move proof

The move is proven mechanically, not asserted. Each of the 30 moved blocks (14
justifications, 14 alternatives blocks, the D6 cleaned-data-echo paragraph, the
revision-history entry, and the Risks preamble + body) was captured from the
pristine HEAD copy **before** the cut and then asserted, as an exact substring,
present in the companion and **absent** from the post-move spec. All 30 passed
`in rationale=True still in spec=False` — 28 of them byte-verbatim, and the two
exceptions are the deliberate hold-backs below, which were elided from the moved
text so nothing appears twice:

- **Decision 3's justification**, minus the `(and with [`DjangoType`]… /
  [`FilterSet`]… / [`OrderSet`]…)` parenthetical.
- **Decision 13's justification**, minus the `and it still hangs off the single
  [`finalize_django_types()`]… call (no second public finalize entry point).`
  clause.

The revision-history **preamble** line (`Revision history (kept inline so the spec
is self-contained):`, 62 bytes) was **deleted, not moved**, under `worker-1.md`
`### Performing the rationale move` rule 2 — its claim is exactly what this move
falsified. It survives only as a backticked quotation inside the companion's own
provenance narrative, describing what was cut.

### Link-definition audit

Run in both directions on both files, with fenced blocks and inline code spans
stripped before sweeping (per `START.md` "Markdown link convention").

| | defs | distinct labels used | total `][label]` uses | undefined uses | unused defs | dangling in-page anchors |
| --- | --- | --- | --- | --- | --- | --- |
| Spec at `HEAD` (baseline) | 78 | 78 | 504 | none | none | none |
| Spec after the move | 94 | 94 | 483 | none | none | none |
| New companion | 42 | 42 | 72 | none | none | none |

**Which definitions the move orphaned, and why none was pruned.** Removing the
deliberative prose orphaned exactly **three** spec definitions —
`[glossary-filterset]`, `[glossary-orderset]` and
`[glossary-finalize_django_types]`. All three are **glossary-gate terms**: `FilterSet`,
`OrderSet` and `finalize_django_types` are rows in
`docs/SPECS/appx/spec-038-form_mutations-0_0_12-terms.csv`, and
`check_spec_glossary.py` requires every CSV term to keep at least one link in the
spec. Pruning them would have failed the gate, and editing the CSV is not the
permitted fix. So the two clauses carrying those three links were **held back** into
the surviving normative sentence each explains (see `### Spec changes made (Worker 1
only)` items 5 and 6) and the moved text reads without them. Net result: **three
definitions orphaned by the move, three re-linked in the body, zero pruned.**

**Sixteen definitions were added** to the spec's `<!-- docs/SPECS/ -->` group —
`[rationale-d1]` … `[rationale-d14]`, `[rationale-risks]`, `[spec-038-rationale]` —
sorted by full definition line within the group, matching the `037` spec's ordering
convention byte for byte in shape (`[rationale-d10]` before `[rationale-d1]`, since
`0` sorts before `]`).

**Both files carry all 10 canonical group headers, in the canonical order, present
even when empty** — verified programmatically against the closed list in
`START.md`. The companion's `<!-- examples/ -->`, `<!-- scripts/ -->`,
`<!-- .venv/ -->` and `<!-- External -->` groups are empty and stay.

**Every companion path resolves on disk, checked by normalising each target from
`docs/SPECS/appx/` rather than by eye** — which is what defeats the depth-rot
masking `START.md` warns about (a same-named file one level up making a wrong
`../` count look valid). The resolved table:

| definition target | resolves to | exists |
| --- | --- | --- |
| `../../../AGENTS.md` | `AGENTS.md` | ✓ |
| `../../../KANBAN.md` | `KANBAN.md` | ✓ |
| `../../../START.md` | `START.md` | ✓ |
| `../../GLOSSARY.md` (+ 10 anchors) | `docs/GLOSSARY.md` | ✓ |
| `../NEXT.md` | `docs/SPECS/NEXT.md` | ✓ |
| `../spec-027-filters-0_0_8.md` | `docs/SPECS/spec-027-filters-0_0_8.md` | ✓ |
| `../spec-028-orders-0_0_8.md` | `docs/SPECS/spec-028-orders-0_0_8.md` | ✓ |
| `../spec-035-optimizer_hardening-0_0_10.md` | `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` | ✓ |
| `../spec-036-mutations-0_0_11.md` | `docs/SPECS/spec-036-mutations-0_0_11.md` | ✓ |
| `../spec-038-form_mutations-0_0_12.md` (+ 14 Decision anchors) | `docs/SPECS/spec-038-form_mutations-0_0_12.md` | ✓ |
| `spec-038-form_mutations-0_0_12-terms.csv` | `docs/SPECS/appx/spec-038-form_mutations-0_0_12-terms.csv` | ✓ |
| `../../builder/BUILD.md` | `docs/builder/BUILD.md` | ✓ |
| `../../builder/build-038-form_mutations-0_0_12.md` | `docs/builder/build-038-form_mutations-0_0_12.md` | ✓ |
| `../../builder/bld-038-slice-0-rationale_extraction.md` | `docs/builder/bld-038-slice-0-rationale_extraction.md` | ✓ (this file) |
| `../../../django_strawberry_framework/forms/resolvers.py` | same | ✓ |
| `../../../django_strawberry_framework/mutations/fields.py` | same | ✓ |
| `../../../django_strawberry_framework/mutations/sets.py` | same | ✓ |
| `../../../tests/forms/` | `tests/forms/` | ✓ |

**Cross-file anchors were checked too, not just the files.** Every
`<file>#<anchor>` definition in both files was resolved by slugging the target
file's own headings (GitHub rule: lowercase, drop backticks, strip non-word except
hyphens, each surviving space → its own hyphen) and confirming the anchor is
present. Zero bad anchors in either direction — the fourteen
`../spec-038-…md#decision-N--…` definitions in the companion and the fifteen
`appx/spec-038-…-rationale.md#…` definitions in the spec all hit real headings,
because the fourteen Decision headings were reproduced character-for-character.

**In-page anchors.** The moved text carried **36 anchor occurrences across 15
distinct anchors** — all fourteen `#decision-N--…` slugs plus
`#risks-and-open-questions`. The companion carries headings with exactly those
fifteen slugs, so **zero** anchors inside moved text needed re-pointing. Both files
report **0 dangling in-page anchors** after the move.

### Gate results

**`check_spec_glossary.py`, before:**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-038-form_mutations-0_0_12.md
OK: 31 terms - all have glossary entries and at least one spec link.
exit=0
```

**`check_spec_glossary.py`, after:**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-038-form_mutations-0_0_12.md
OK: 31 terms - all have glossary entries and at least one spec link.
exit=0
```

Same 31 terms, exit 0. The two held-back fragments are what kept it there; without
them three terms would have lost their only spec link (see
`### Link-definition audit`).

**`ruff`** — recorded verbatim under `### Validation run` below. No `.py` file was
touched, so both are no-regression checks.

**`uvx pre-commit run --files …`** — recorded verbatim under `### Validation run`.

### Validation run

```
$ uv run ruff format --check .
438 files already formatted
exit=0

$ uv run ruff check .
All checks passed!
exit=0
```

Both are no-regression checks: this slice touched no `.py` file.

```
$ uvx pre-commit run --files docs/SPECS/spec-038-form_mutations-0_0_12.md \
    docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md \
    docs/builder/bld-038-slice-0-rationale_extraction.md
kanban tracked path constants...............................................Passed
source layout (py trailing commas + ascii-only; md link-def scaffold; json/graphql brace explosion)...Passed
ruff format.................................................(no files to check)Skipped
ruff check..................................................(no files to check)Skipped
kanban anchors collision-free (card vs card, card vs glossary, render ids)...Passed
citations resolve (AGENTS.md rule 27 path::Symbol refs)......................Passed
exit=0
```

**Passed on the first run; no hook rewrote a file, so no re-stage-and-re-run was
needed.** Proved rather than assumed: `wc -c` over the two files this slice's output
actually consists of is byte-identical before and after the hook run — 164,240 for
the spec and 55,325 for the companion — and the run was repeated to confirm a second
clean pass. This artifact's own byte count is deliberately **not** cited: it is a
live count of a file the citing sentence is editing, which cannot be stated truly
from inside. The `source-layout` hook's `.md`
link-definition-scaffold check is the one that governs this slice's output, and it
accepted both markdown files as written — the 10 canonical group headers were
authored in place rather than left for the auto-fix. The two `ruff` hooks report
`(no files to check) Skipped` because the file list is Markdown only, which is the
mechanical confirmation that this slice has no source diff.
- `git status --short` after the runs — the three files this slice owns, plus the concurrent session's pre-existing baseline-dirty paths listed in the plan's `## Baseline-dirty out-of-scope files`. **Nothing was reverted and nothing outside the three files was edited.** No `.py` file in `django_strawberry_framework/` changed by this pass.
- `pytest` — **not run and not owed.** No source or test file was touched. (Recorded because `worker-1.md` `## Final verification job` step 5 asks for the focused existing tests the plan calls for; the plan calls for none on a slice with no source diff.)

### Failability proofs

`None; this pass introduced no new boundary.` No guard, gate, cap, or rejection path
was added — this slice's whole diff is Markdown.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Not applicable; plan declares floor-verification scope none.`

### DRY check across this slice and prior accepted slices

No prior slice of this cycle has been accepted — this is the first. Against the
**preceding cycles'** executions of the same move, the check is whether this
companion re-derives shape the `034` / `035` / `036` / `037` companions already
settled. It does not: the section grammar, the per-Decision keying, the
`**Post-ship:**` bullet convention, and the reference-style link scaffold are all
reused unchanged. The one place this file adds rather than reuses is the
`### Changes this Decision underwent` "no Post-ship bullet yet" line, needed because
`037`'s companion was committed *after* its reconciliation slice had already
appended, while this file is committed before Slice 2 runs; without the line a
reader could not tell an unexamined Decision from a checked-and-unchanged one, which
is the exact ambiguity the convention exists to prevent.

### Summary

The whole deliberative layer of `spec-038` moved out of the spec and into a new
`docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` companion, closing the
build plan's pre-flight step 7. Five block classes left the spec by cut-and-paste —
14 `Justification:` blocks, 14 `Alternatives considered (and rejected):` blocks
carrying 25 rejected alternatives, the 14-item `## Risks and open questions` body,
Decision 6's inline cleaned-data-echo rejection, and the inline `Revision history`
block — 26,640 bytes removed, 5,029 bytes of pointers, link definitions and two
held-back fragments added back, for a net 21,611-byte cut: 185,851 → 164,240 bytes.
Every Decision keeps a one-line pointer into the companion, every companion entry
names its spec Decision by heading and anchor, and both files pass a two-way
link-definition audit, an on-disk path check, a cross-file anchor check, and the
glossary gate at the same 31 terms. No `.py` file, no closeout surface, and none of
the ~116 baseline-dirty files were touched.

### Spec changes made (Worker 1 only)

All line citations are against the **post-move** spec unless marked `HEAD`. Every
one is the move itself or a repair the move mechanically caused; **no stale contract
statement was fixed** — Slice 2 owns that, and what I noticed is routed below.

1. **Removed the inline `Revision history` block** (`HEAD` lines 98-138) and
   replaced it with the four-line "This spec's deliberative layer … lives in the
   rationale companion" pointer, now lines 98-102. Reason: the move; the
   `Revision 1` entry is the companion's `## Revision history`. Its 62-byte preamble
   (`Revision history (kept inline so the spec is self-contained):`) was **deleted,
   not moved** — the move falsified its own claim.
2. **Removed all 14 `Justification:` and 14 `Alternatives considered (and
   rejected):` blocks** (`HEAD` lines 861-1877, fourteen contiguous regions) and
   replaced each with a two- or three-line `Rationale companion — …` pointer naming
   what moved and its count (post-move lines 825, 853, 867, 886, 940, 1037, 1290,
   1485, 1500, 1520, 1543, 1563, 1627, 1648). Reason: the move.
3. **Removed Decision 6's `Rejected (recorded, not silently dropped): **cleaned-data
   echo**` paragraph** (`HEAD` lines 1136-1149). Reason: the move; it is a rejected
   alternative recorded in the Decision body, and Decision 6's pointer now names it.
4. **Removed the `## Risks and open questions` body** (`HEAD` lines 2148-2270) and
   replaced it with a six-line pointer, now lines 1921-1926; the `##` heading stays.
   Reason: the move.
5. **Held back Decision 3's sibling-surface parenthetical** into the Decision body,
   post-move lines 860-862:

   ```markdown
   declared exactly like every other consumer surface in the package
   ([`DjangoType`][glossary-djangotype] / [`FilterSet`][glossary-filterset] /
   [`OrderSet`][glossary-orderset]).
   ```

   Reason:
   the move orphaned `[glossary-filterset]` and `[glossary-orderset]`, both
   glossary-gate terms, and the fix the task and `check_spec_glossary.py` both
   prescribe is to keep the term mentioned in the spec body rather than edit the
   CSV. The Decision body already asserted the mutation is declared like every other
   consumer surface; the parenthetical now names which. The moved justification
   reads without it.
6. **Held back Decision 13's single-finalize-call clause** into the Decision body,
   post-move lines 1601-1602:

   ```markdown
   It still hangs off the single
   [`finalize_django_types()`][glossary-finalize_django_types] call.
   ```

   Reason: same
   gate coupling for `[glossary-finalize_django_types]`, **and** the clause is
   implementation-relevant under `docs/builder/BUILD.md` `## Spec rationale
   extraction`'s carve-out — a builder who never reads it adds the second public
   finalize entry point the Decision's own rejected alternative names. The moved
   justification reads without it.
7. **Re-pointed the four surviving `[Risks](#risks-and-open-questions)` uses** at
   `[Risks and open questions][rationale-risks]` — in `## Non-goals`, the
   `### Reference-package parity checkpoint` table, Decision 6's
   `Meta.return_field_name` paragraph, and Decision 11's plain-form paragraph.
   Reason: each promises the reader deliberation that is now in the companion;
   leaving them would resolve in two hops, landing a reader on a heading containing
   only a pointer back. `037`'s execution of this move made the same call
   deliberately. One paragraph was re-wrapped byte-neutrally to keep its lines under
   85 characters after the substitution.
8. **Added sixteen link definitions** to the `<!-- docs/SPECS/ -->` group. Reason:
   the pointers in 1, 2, 4 and 7 need them.

No deferral is owed on any `### Spec slice checklist (verbatim)` box: all eleven are
`- [x]`, with the one exception inside box 6 recorded and routed rather than
silently dropped (item 1 below).

### Notes for Worker 1 (spec reconciliation)

Everything below was noticed while reading the spec end to end and **deliberately
not acted on** — Slice 2 owns spec reconciliation. Items 1-8 are shapes the move
itself surfaced and could not discharge; they are additive to, not a replacement
for, Worker 0's verified findings D-1 … D-19 in the build plan, which Slice 1 grades
and Slice 2 writes.

1. **Decision 8 narrates its own history and its seven steps are in the superseded
   order — and a move cannot fix it.** This is Worker 0's finding D-9, re-confirmed
   by reading. The Decision opens with `**Ordering correction — authorize runs
   BEFORE the relation decode (post-ship security fix).**`, states that "the step
   numbers below reflect the original draft sequence", and then leaves steps 1-7 in
   the draft order (decode → locate → authorize → …). Moving the narration alone
   would leave the spec asserting the wrong pipeline order with **no** correction —
   strictly worse than the chronology, and a false contract rather than a stale one.
   The fix is to renumber into the shipped order (locate → authorize → decode →
   construct/validate → write → re-fetch → return) and sweep every cross-reference
   to a step number, which is a contract rewrite. It is the single reason the
   post-move spec does not fully satisfy "no chronology a reader must apply", and it
   is the highest-value edit available to Slice 2.
2. **Three chronology hedges now have no referent in the spec at all**, because the
   deliberation they point at left with the Risks body. Each is meta-framing with no
   contract content, so trimming it changes nothing a builder implements:
   - Decision 6: `This is the **fully-pinned** resolution of the prior
     preferred/fallback uncertainty: an implementer cannot ship a divergent
     plain-form shape.` — plus the same paragraph's lead-in `**Pinned plain-form
     payload contract (P2 — a fixed schema rule, not a preferred / fallback
     branch).**`, whose "preferred / fallback" vocabulary was the Risks section's.
   - Decision 10: `This split … is the single resolution of the prior contradiction
     (one shared checklist rule that read as if the plain base also took `create` /
     `update`).` — narrates a superseded draft.
   - Decision 7: `This replaces the earlier "instantiate `form_class()` no-arg to
     read `form.fields`" plan, which broke for kwarg-requiring forms.` — same shape.
3. **Two sentences cite "the review" as an authority the spec no longer carries.**
   Decision 7's shape-identity paragraph calls the collision raise "the **fail-loud
   fix** for the two collision cases the review names", and Decision 8's
   required-extra bullet says "This avoids both failure modes the review names".
   Neither the review document nor its findings are in the spec, so a reader cannot
   look up what was named.
4. **The `P1` / `P2` / `P3` priority labels and the bare `#4`-`#8` / `AR-H1` /
   `AR-H4` / `AR-H5` / `AR-M6` / `Medium-1` citations are undecodable from the
   spec.** They are review-round identifiers (the `AR-*` and `Medium-1` ones belong
   to `spec-036`'s review, the `#N` ones to `038`'s own) scattered through Decisions
   6, 7, 8, 9, 13, `## Edge cases and constraints`, `## Test plan` and the
   `## Definition of done`. A shipped contract that keys its own emphasis to an
   unnamed document is a chronology a reader must reconstruct. Slice 2's call
   whether to resolve them to plain emphasis or to cite the source.
5. **`## Key glossary references` describes a shipped card's closeout in the future
   imperative.** Its first bullet says "**The current glossary text is provisional
   and Slice 5 must correct it on one point**" and "Slice 5 promotes both entries
   from `planned for 0.0.12` to `shipped (0.0.12)`" — of a card that shipped three
   patch releases ago. Whether the glossary correction actually landed is a
   `docs/GLOSSARY.md` question the cycle's scope fence puts out of reach, so the
   honest reconciliation is to state the shipped ownership without promising future
   work; flagging the glossary state itself is a maintainer note.
6. **`## Doc updates` and the `## Definition of done` Slice-5/Slice-7/Slice-8 items
   are entirely future-tense** about work that shipped (version files, README status
   line, `docs/TREE.md` summary lines, the KANBAN card move). Same class as item 5,
   and the same scope-fence constraint applies to verifying each landed.
7. **The `## Implementation plan` table's Slice-2 cell still stages a TODO anchor
   that has been discharged**: "`mutations/fields.py` (TODO-anchor only — the
   `_input_type_name` body is now byte-identical to the `input_type_name` seam;
   Slice 3 deletes it)". Worker 0 verified `grep -rn 'TODO(spec-038'` returns
   nothing in source or tests and that `_input_type_name` is gone from the package,
   so the cell describes a staging step that completed.
8. **Decision 8's "Helper reuse" paragraph leaves an unresolved instruction in a
   shipped spec**: "the lighter edit is dropping the leading underscore … the
   cleaner edit is lifting them to a neutral `mutations/_pipeline.py` … Slice 3
   picks one and names it". Slice 3 picked, shipped, and a later card moved three of
   the nine helpers elsewhere (Worker 0's D-1). The paragraph should state where the
   helpers live rather than instruct a builder to choose.
9. **`## Current state` needs the clause-by-clause grading
   `docs/builder/BUILD.md` `### `## Current state`: observations stand, predictions
   do not` requires.** On a first read its five bullets look like dated observations
   throughout ("No `forms/` module exists", "The version line reads `0.0.11`", "`0.0.12`
   has exactly one card") — the section header dates them and they stand. I did not
   grade every clause; that is Slice 2's step, and the borderline case to watch is
   the third bullet's "there is no joint cut to defer the version bump to", which is
   an inference rather than a reading.

Nothing in items 1-9 was edited. Every one is a contract or chronology statement,
not a link or gate repair, and this slice's mandate is the move plus the repairs the
move causes.

### Final status

`final-accepted`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[build-md]: BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
