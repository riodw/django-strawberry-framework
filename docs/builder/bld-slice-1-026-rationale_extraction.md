# Build: Slice 1 — Rationale extraction

Spec reference: `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` (whole file; 3,593 bytes at `HEAD` `ddf8bbaf`, 4 headings)
Status: final-accepted

**Combined Worker 1 pass.** The maintainer authorized Worker 1 to act alone on the slices of this cycle that need no code change. Slice 1 touches Markdown only, so there is no `## Build report (Worker 2)` and no `## Review (Worker 3)` section: the Plan and the Final verification below are one pass. `docs/builder/build-026-scalar_conversion_fakeshop-0_0_7.md` `Ownership partition:` declares this shape.

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** Not applicable and not run. This slice writes no Python and adds no helper, shared constant, validation branch, coercion utility, or test helper. The package-wide AST inventory (`worker-1.md` `### Package-wide helper inventory before helper planning`) exists to prevent duplicated *code* shapes; there is no code in this slice's diff to duplicate. Recorded rather than silently skipped.

- **Existing patterns reused.** The rationale file's structure is taken from the two nearest siblings rather than invented: `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md:1-60` (the `## Provenance of this record` / measured-population table / **Moved** / **Stayed in the spec** / **Deleted, not moved** shape, and the fixed-width-placeholder byte-count technique) and `docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md` (per-entry `Alternatives rejected` / `Changes this decision has undergone` / `Claims this decision may no longer make` subsections). The spec-side pointer sentence copies the wording shape of `docs/SPECS/spec-023-multi_db-0_0_7.md:197` and `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md:149`.
- **New helpers justified.** None. One new file, no new mechanism.
- **Duplication risk avoided.** The one real risk is stating a measured fact in both the spec and the rationale, which is exactly what the move forbids. Prevented mechanically: the moved phrase is grepped for in both files after the cut (`## Final verification (Worker 1)`, move proof).

### Implementation steps

1. Re-derive every seeded fact from the build plan against source before using it — the plan's numbers are Worker 0's measurements, not this pass's. (`docs/builder/build-026-scalar_conversion_fakeshop-0_0_7.md:78-110`.)
2. Create `docs/SPECS/appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md` with the keyed-entry frame, the ship provenance, the `## Provenance of this record` move record, and entries `D4` and `D5`.
3. Cut the deliberative half of the `## Other` bullet at `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md:28` and add the one-line rationale pointer required by `worker-1.md` `### Performing the rationale move` rule 1.
4. Add `[spec-026-rationale]` to the spec's `<!-- docs/SPECS/ -->` link-definition group.
5. Prove the move, re-run `check_spec_glossary.py`, disk-check every link definition, run the scaffold check in `--check` mode.

Line numbers are pin-at-write-time navigational hints.

### Test additions / updates

None. This slice writes no Python and needs no test. `AGENTS.md` forbids `pytest` after edits unless asked, and nothing in the diff is executable.

### Implementation discretion items

None. Every choice in this slice — what moves, what stays, what is deleted rather than moved — is fixed by `worker-1.md` `### Performing the rationale move` and is Worker 1's own call in any case; there is no second worker to delegate to.

### Spec slice checklist (verbatim)

`spec-026` has **no `## Slice checklist`** — its absence is finding `D1` and is the reason this cycle exists. The boxes below are the build plan's Slice 1 line (`docs/builder/build-026-scalar_conversion_fakeshop-0_0_7.md` `## Checklist`) decomposed into its verifiable obligations, plus the four verification obligations of `worker-1.md` `### Performing the rationale move`. Recorded here so the audit at final verification has something to audit.

- [x] Create `docs/SPECS/appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md`
- [x] MOVE the stub's deliberative layer into it (cut-and-paste, not copy: the moved text leaves the spec)
- [x] Establish the keyed-to-the-spec frame — every entry names the spec decision or section by heading and anchor, and carries rejected alternatives, the change record, and the claims it may no longer make
- [x] Seed entry `D4` — the "upstream code paths no other example app reaches" justification, with the measurement showing it was already false when written and the narrower claim that is true
- [x] Seed entry `D5` — nine tests shipped, not eight; the omitted one named; the miscount traced to the ship commit message
- [x] Rule 1 — the spec keeps a one-line pointer naming what was moved and where
- [x] Rule 2 — prose the current facts have falsified is deleted, not moved
- [x] Rule 3 — `check_spec_glossary.py` still exits 0; every in-page anchor resolves; no surviving cross-reference points into moved text without naming the rationale file
- [x] Rule 3 — spec byte count before and after reported

---

## Final verification (Worker 1)

- **Spec slice checklist:** every box above is `- [x]`; each is evidenced below.
- **DRY check across this slice and prior accepted slices:** this is the cycle's first slice; no prior accepted slice exists. No duplication introduced — the move proof below shows the moved text exists in exactly one file.
- **Existing tests still pass:** not run, and none apply. The diff is two Markdown files plus this artifact; `AGENTS.md` forbids a `pytest` run that was not asked for.
- **Spec reconciliation:** yes, and it is recorded under `### Spec changes made (Worker 1 only)`.
- **Final status:** `final-accepted`.

### Verification evidence (measured this pass, not inherited)

Every number the build plan seeded was re-derived here before use. All matched.

| Claim | Instrument | Result |
| --- | --- | --- |
| ship commits and their pre-renumber attribution | `git log -1 --format='%H%n%ad%n%s%n%b' 2701eb88 cae2d5a3` | both dated 2026-05-27, both closing `Part of DONE-048-0.0.7.` |
| `apps/library` model count at ship | `git show 2701eb88:examples/fakeshop/apps/library/models.py \| grep -cE '^class .*models\.Model'` | 8 |
| `apps/library` sibling `DjangoType` count at ship | `git show 2701eb88:examples/fakeshop/apps/library/schema.py \| grep -E '^class '` | 7 `DjangoType` classes + `class Query` |
| `apps/library` initial-migration `CreateModel` count at ship | `git show 2701eb88:examples/fakeshop/apps/library/migrations/0001_initial.py \| grep -c 'migrations.CreateModel'` | 7 |
| `apps/products` at ship | same two greps against `apps/products` | 4 models, 4 `DjangoType` classes |
| apps present at ship | `git ls-tree --name-only 2701eb88 examples/fakeshop/apps/` | `library`, `products`, `scalars` only |
| `apps/scalars` initial-migration `CreateModel` count at ship | `git show 2701eb88:examples/fakeshop/apps/scalars/migrations/0001_initial.py \| grep -c` | 2 |
| test count at ship | `git show 2701eb88:examples/fakeshop/test_query/test_scalars_api.py \| grep -c '^def test_'` | **9**, not 8 |
| the omitted test's name | same, `grep '^def test_'` | `test_scalar_specimen_introspects_json_scalar_in_both_shapes` |
| the commit message's own miscount | commit body | header reads `(8 tests):` above **9** bullets |
| test count at `HEAD` | `grep -c '^def test_' examples/fakeshop/test_query/test_scalars_api.py` | 29 |
| the narrower true claim (all-nullable twin) | AST scan of every `examples/fakeshop/apps/*/models.py`, comparing non-relational column-name sets and per-column `null=True` — script reproduced verbatim in the rationale file | 48 models with concrete columns; `NullableScalarSpecimen` is the **only** all-nullable one; `ScalarSpecimen` <-> `NullableScalarSpecimen` (11 columns) is the only identical-column-set pair whose halves are all-non-null / all-nullable |
| spec byte count before | `git show HEAD:docs/SPECS/spec-026-…md \| wc -c` and `wc -c` on disk, both clean | 3,593 |
| spec byte count after | `wc -c` | 3,668 |
| rationale byte count after | `wc -c` | 17,340 |

The build plan's D4 and D5 figures were correct as stated. Re-derivation found no discrepancy; it is recorded because a count accepted on prose is not a measurement.

### Move proof (mechanical, re-derivable)

```
$ grep -c "no other example app reaches" docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md
0
$ grep -c "no other example app reaches" docs/SPECS/appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md
4
$ grep -c 'two-`CreateModel`' docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md
0
$ grep -c 'SET_NULL` ondelete behavior' docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md
0
```

Text that landed in the rationale left the spec. The two "deleted, not moved" fragments are absent from the spec and appear in the rationale only inside the quoted dead-claim block, explicitly labelled.

### Gate results

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` -> `OK: 3 terms - all have glossary entries and at least one spec link.` exit 0. **This constrained the cut.** Two of the three CSV terms (`DjangoType`, `finalize_django_types`) are linked from nowhere in the spec except the bullet this slice cut, so removing the bullet whole would have failed the gate. The surviving true fragments that carry those two links therefore stay in the spec — which is also the right answer on the merits, since they are the reason the pairing exists.
- `uv run python scripts/check_trailing_commas.py --check <both files>` -> exit 0. Run in `--check` mode deliberately; the default auto-fixes.
- Link definitions: all 9 in the rationale and all 6 in the spec disk-checked from each file's own directory; every target exists. All 10 canonical group headers present in order in both files.
- In-page anchors: the rationale's `#d4--the-upstream-code-paths-no-other-example-app-reaches-justification` self-link resolves against its own heading (double hyphen, matching the sibling rationale files' em-dash slugs). The spec's `#other` cross-file anchor from the rationale resolves against `## Other`.

### Notes for the spec-reconstruction slice

Everything below is on disk because this artifact, not a dispatch prompt, is the contract the next pass reads.

- **The rationale file is append-only from here** (`worker-1.md` rule 4). Its `## Entry shape for entries appended after this pass` section states the required shape: spec heading and anchor first, then rejected alternatives with the reason each lost, then the change record, then the claims the decision may no longer make. Entries `D4` and `D5` are recorded; the cycle's remaining verified findings are not.
- **The spec keeps one pointer, and it is scoped to the pairing bullet.** A reconstruction that adds numbered Decisions should add per-Decision `Rationale companion — …: [Decision N][rationale-dN]` lines in the sibling specs' style, and the existing `[spec-026-rationale]` definition can carry them or be joined by `[rationale-dN]` anchors.
- **D4's corrected claim is not yet in the spec.** This slice removed the false justification and left the surviving true fragments; the narrower measured claim (`ScalarSpecimen` / `NullableScalarSpecimen` is the example tree's only all-nullable-twin pair, so both branches of one `SCALAR_MAP` row are exercised over one identical column set) lives only in the rationale. Stating it in the spec is reconstruction work, and the measurement to cite is in the rationale's `### What is true instead, and is still true`.
- **D5's ninth test is not yet in the spec's list.** The eight enumerated bullets are unchanged; `test_scalar_specimen_introspects_json_scalar_in_both_shapes` and the corrected count of nine belong in the reconstructed test plan. The spec's second `## Other` bullet still says `eight live HTTP tests`.
- **Two dangling link uses pre-date this cycle and are still there.** `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` uses `[example-schema]` and `[settings]` with no matching definitions (its `<!-- examples/ -->` group is empty), and defines `[backlog]` with no use. Verified present at `HEAD` before this slice's edit, so this slice did not introduce them and did not fix them — they are contract-surface link rot for the reconstruction pass. Targets are `examples/fakeshop/config/schema.py` and `examples/fakeshop/config/settings.py`, both present on disk.
- **The `Status:` line was left alone deliberately.** `worker-1.md` `## Spec status-line re-verification` requires editing a status line the build has falsified. `Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact` is still an accurate description of the file after this slice, because the file is still a stub. It stops being accurate the moment the reconstruction lands, and the reconstruction owns it (finding `D9`), along with the one-word `## Planning note` (`D10`) and the stub preamble sentence instructing a reader to expand the file before implementation starts.
- **The spec grew by 75 bytes** (3,593 -> 3,668). Expected on a stub: the required pointer plus its link definition exceed the one clause available to move. The rationale file states this explicitly so a later reader does not read the growth as a failed move.

### Summary

Created `docs/SPECS/appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md` (17,340 bytes) and performed the rationale MOVE the `026` cycle never ran. The exclusivity justification for the paired-model shape left the spec; two of its five list items were deleted rather than moved because the current facts falsify them; the three surviving true fragments stayed, carrying the two glossary links the terms CSV depends on. The file establishes the keyed-to-the-spec frame and records two entries: `D4`, a central justification that was already false when written, with the measured narrower claim that replaces it; and `D5`, a nine-test surface the spec and its source commit message both call eight.

### Spec changes made (Worker 1 only)

1. `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md:28` — cut the phrase `It exercises **upstream code paths no other example app reaches**`, the list item "Django's two-`CreateModel` initial migration path", and the list item "and `SET_NULL` ondelete behavior" from the `## Other` pairing bullet; appended the one-line rationale pointer. Reason: the exclusivity claim is false (four of five items were already reached by `apps/library` and `apps/products` at the ship commit; the fifth is false at `HEAD`), and rule 1 requires the pointer. Triggered by Slice 1.
2. `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` link-definition block, `<!-- docs/SPECS/ -->` group — added `[spec-026-rationale]: appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md`. Reason: the pointer added in change 1 needs its definition; path disk-checked from the spec's own directory. Triggered by Slice 1.

No other spec text was touched. No `.py` file, no `-terms.csv`, no generated doc, and no baseline-dirty out-of-scope file was opened for writing.

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
