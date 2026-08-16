# Build: R1 — rationale companion and spec reconciliation (spec-012)

Spec reference: `docs/SPECS/spec-012-version_release_alignment-0_0_4.md` (whole file, 60 lines at `HEAD`)
Rationale companion: `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md` (created by this pass)
Plan: `docs/builder/build-012-version_release_alignment-0_0_4.md`, item R1 (findings F1-F8)
Status: final-accepted

This item was dispatched to **Worker 1 alone** (the plan's `## Dispatch record`), so this artifact carries the combined Plan + Final-verification blocks. No Worker 2 build pass and no Worker 3 review pass exist for it, and none is owed: the item writes Markdown only, lands no source and no test, and `### Isolation is non-waivable` binds a pass that writes code.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in the code sense and recorded rather than skipped: this item's writable set is four Markdown paths, so there is no package surface for `### Package-wide helper inventory before helper planning` to inventory. The prose analogue was run instead — the two prior residual-completion rationales (`spec-007`, `spec-011`) were read end to end for reusable argument, and the reuse is recorded below.
- **Existing patterns reused.** The rationale's whole structure is spec-011's: `## How to read this file` / `## Provenance of this record` / `## Entries keyed to the spec` / `## Reconciliation record`, one entry per spec heading, each carrying *Moved* / *Claim the spec no longer makes* / *alternatives rejected*. The reconciled spec's `## Card snapshot` is spec-011's two-bullet identity-only shape, verbatim in structure.
- **New shared shape justified.** None. The one argument this cycle would otherwise have had to make from scratch — expand-it / delete-it / keep-and-reconcile for the boilerplate preamble — is **cross-referenced** to `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md` `### The preamble — the stub's own justification, and an instruction that cannot be followed`, which already weighs it and already names spec-012 by byte count (1,651 at `947f7494`). Re-arguing it would be the documentation form of a near-copy.
- **Duplication risk avoided.** Two. (a) Restating the preamble argument — avoided by the cross-reference above. (b) Restating the board's label/priority/size rows in the spec — avoided by deleting them, which is also the F5 fix; a hand-copied render of DB rows in a file nothing re-renders is duplication that goes *wrong*, not merely redundant, and this spec is the proof (its label list had drifted).

### Implementation steps

1. Re-derive every figure the plan states (V1-V4, F4, F5, F7, F8) against this working tree before writing anything. Record disagreements.
2. Create `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md` on the spec-011 rationale's structure.
3. Reconcile `docs/SPECS/spec-012-version_release_alignment-0_0_4.md`: cut the preamble paragraph and `## Planning note` (move), delete `## Card snapshot`'s board-metadata bullets and the whole `## Other` section (falsified / duplicative), rewrite both `## Scope` bullets.
4. Re-run `scripts/check_spec_glossary.py` and disk-check every link-definition path from each file's own directory.
5. Write this artifact; append the memory entry.

### Test additions / updates

None. The item writes no code and adds no test. `AGENTS.md` rule 15 and the plan's `Floor-verification scope: none` both apply; the final gate owns the suite.

### Implementation discretion items

None. Every disposition below was decided at plan time and is recorded with its rejected alternatives in the rationale.

### Dispatched findings checklist

R1 has no spec `## Slice checklist` to copy from — the spec is a card-snapshot stub with no slices — so the round form applies.

- [x] **F1** — no rationale companion exists; create it (`docs/builder/BUILD.md` `## Spec rationale extraction`; specs 001-011 all have one).
- [x] **F2** — the boilerplate preamble's instruction is counterfactual at `HEAD` (`spec-012:7`); cross-reference the spec-007 argument, do not re-litigate.
- [x] **F3** — `## Planning note` is the single word `shipped`, a raw Kanban column render (`spec-012:18-20`).
- [x] **F4** — `## Other` is an undifferentiated Kanban dump under a heading that names none of its rows (`spec-012:27-35`).
- [x] **F5** — `## Card snapshot` restates board fields **and drifts from them**: Labels `release`, `versioning` vs. the card's `internal`, `release`, `versioning` (`spec-012:9-16`).
- [x] **F6** — `## Scope` bullet 1 states a release-cut fact in the present tense ("now agree on `0.0.4`"), which reads at `HEAD` as a standing invariant that is false (`spec-012:24`). **The item's central reconciliation.**
- [x] **F7** — the five-file list is the board's `#### Files likely touched` prediction; the card's own diff touched two files, neither of them in the list (`spec-012:31-35`).
- [x] **F8** — the unused `[backlog]` link definition (`spec-012:40`). **Recorded, not fixed** — left in place, with the reason written into the rationale; carried to the deferred-work catalog.

---

## Final verification (Worker 1)

### Re-derivation of the plan's measurements

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` binds this pass to the plan's numbers. Every figure below was re-measured at this working tree (`HEAD` = `5851bb59`) rather than accepted.

| Plan claim | Re-measured | Verdict |
|---|---|---|
| V1: five surfaces agree on `0.0.4` at `231911a8` | `pyproject.toml:4`, `__init__.py:14`, `tests/base/test_init.py:7`, `uv.lock` root entry, `CHANGELOG.md:10` — all `0.0.4` | reproduces |
| V2: same invariant at `HEAD` on `0.0.14` | `pyproject.toml:4`, `__init__.py:58`, `tests/base/test_init.py:21`, `uv.lock:544`, `CHANGELOG.md:19` | reproduces (all five line refs exact) |
| V3: the `0.0.4` changelog block survives byte-identical | `## [0.0.4]`-to-`## [0.0.3]` block from `git show 231911a8:CHANGELOG.md` and from the working tree: **2,621 bytes each**, `diff` exit 0 | reproduces |
| V4: the condensation lost no substantive claim | the `GenericForeignKey` / `ConfigurationError` row survives in `### Fixed` with "with guidance to exclude or override the field" | reproduces |
| V5: rule 31's pairing has no executable pin | `tests/base/test_init.py::test_version` asserts the literal `"0.0.14"`; nothing reads `pyproject.toml` | reproduces |
| the card's commit touched two files | `git show --stat 231911a8` -> `CHANGELOG.md` (31), `KANBAN.md` (147) | reproduces |
| the four surfaces were already `0.0.4` at `118f71a1` | `118f71a1~1`: `pyproject.toml`/`__init__.py` = `0.0.3`; `118f71a1`: all four = `0.0.4` | reproduces |
| changelog section counts after condensation (5/6/4/1) | counted from the block at `HEAD`: `### Added` 5, `### Changed` 6, `### Fixed` 4, `### Removed` 1 | reproduces |
| F5: card labels at `HEAD` are `internal`, `release`, `versioning` | `KANBAN.md:4537` | reproduces |
| F7: five-file list is a prediction | `KANBAN.md` card 012 `#### Files likely touched` = the same five paths | reproduces |
| F8: `[backlog]` occurs once | `grep -c 'backlog'` -> 1 | reproduces |
| spec byte count 1,651 | `git show HEAD:…spec-012…md \| wc -c` -> 1,651 / 60 lines; identical at `947f7494` | reproduces |
| **F4: `## Other` is "six heterogeneous Kanban rows"** | **seven** bullets, enumerated | **does not reproduce** |

**The one correction.** The plan's F4 says six bullets, and its own parenthetical enumeration — "two `#### Note` bullets and the five `#### Files likely touched` paths" — sums to **seven**, which is also what the file carries. The discrepancy is arithmetic inside the plan, not drift in the spec; the plan's line range (`27-35`) is consistent with seven. The corrected figure is recorded in the rationale's `## Other` entry, which names the disagreement rather than silently using the right number. **Surfaced here for Worker 0** (the plan is Worker 0's file; this pass does not edit it).

**One plan-adjacent nuance worth Worker 0's record, not a correction.** The plan's F5 frames the label drift as a straight two-to-three addition. The blob history is slightly different and slightly stronger: the two-label set was current on 2026-06-01 (`bdfdc9cc`, the day the spec file was created at `81e4704d`), the board then rendered **no** `- Labels:` line for card 12 at all from `91f9db12` (2026-06-04) through `c8f03087` (2026-06-09), and the dimension returned rebuilt at `2baf93b5` (2026-06-09) with `internal` present. Same conclusion — the spec's copy is wrong at `HEAD` — reached by a dimension rebuild rather than a single label edit, which strengthens the argument against restating DB rows in a file nothing re-renders.

### Findings checklist audit

All eight boxes are `- [x]` and each contract landed in this pass's diff; nothing is deferred un-recorded. F8 is ticked as **recorded, not fixed** — its contract was "record it and leave the definition alone", and that is what landed (the definition is still in the spec's `<!-- Root -->` group, and the rationale carries a dedicated entry saying why). Its onward disposition is the deferred-work catalog, listed below for the final gate.

### Verification of the two files

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-012-version_release_alignment-0_0_4.md` -> `OK: 1 terms - all have glossary entries and at least one spec link.` (exit 0). The `#djangotype` anchor changed carrier inside `## Scope` and still resolves; `docs/GLOSSARY.md:765` carries `## \`DjangoType\``.
- **Every link path disk-checked from its own source directory.** Spec (at `docs/SPECS/`): `../../KANBAN.md`, `../../BACKLOG.md`, `../../CHANGELOG.md`, `../../pyproject.toml`, `../../uv.lock`, `../../django_strawberry_framework/__init__.py`, `../../tests/base/test_init.py`, `../GLOSSARY.md`, `appx/spec-012-…-rationale.md`. Rationale (at `docs/SPECS/appx/`, one level deeper): `../../../KANBAN.md`, `../../../BACKLOG.md`, `../../GLOSSARY.md`, `../spec-012-….md`, `../../builder/BUILD.md`, `../../builder/worker-0.md`, `../../builder/worker-1.md`, and the two sibling rationales by bare filename. All exist.
- **Both in-page anchors resolve**: `#card-snapshot` and `#scope` are live headings in the reconciled spec, and both rationale entries keyed to removed headings anchor to a surviving section as `worker-1.md` requires.
- **Scaffold**: both files carry the single `<!-- LINK DEFINITIONS -->` delimiter and all ten canonical group headers in order, defs alphabetical within group.
- **`AGENTS.md` rule 27**: the spec cites `pyproject.toml #"version = "` and `__init__.py #"__version__ = "` in the module-level `path #"unique substring"` form (neither assignment sits inside a symbol) and `tests/base/test_init.py::test_version` in the symbol form. No `path:NN` appears in either the spec or the rationale; the raw line refs in this artifact are licensed by `AGENTS.md` rule 27's per-cycle `bld-*.md` carve-out.
- No fenced code block exists in either file, so the four-backtick drop-in hazard does not arise.

### Do-not-touch compliance

This pass wrote exactly four paths, and only these four: `docs/SPECS/spec-012-version_release_alignment-0_0_4.md` (` M`), `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md` (`??`), this artifact (`??`), and `docs/builder/worker-memory/spec-012-worker-1.md` (gitignored at `.gitignore:188`, so it never appears in `git status`). The baseline itself moved during the pass — `git status --porcelain | wc -l` read 93 at plan time and **102** at the end, the extra six being concurrent sessions' work, which is why the plan says any pass needing the baseline re-derives it rather than quoting a number. `docs/GLOSSARY.md` was read only; `scripts/build_glossary_md.py` was **not** run. `KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3` were read only. The build plan was not edited — the F4 correction is surfaced above for Worker 0. No baseline-dirty path was edited, reverted, staged, or `git checkout`ed; no `git stash` was used; the read-only history reads all went through `git show <rev>:<path>` into a scratch path outside the repository.

### Summary

`## Scope` was the item. The spec's five sections became two: the boilerplate preamble and `## Planning note` were **moved** into the new rationale companion; `## Card snapshot`'s board-metadata bullets and the whole `## Other` section were **deleted outright** (the label list was already false at `HEAD`, and the rest was a duplicate scope row, a board triage note, and a file-list prediction); both `## Scope` bullets were **rewritten**.

The reconciled `## Scope` now enumerates the five version surfaces one per bullet — each named by the file plus the exact key it carries — states `0.0.4` as what **the `0.0.4` cut** put on them, and then says in its own sentence that alignment is a per-release obligation rather than a standing property of those files. That sentence is F6's remedy: it makes the moving value legible as moving, so no reader has to apply a chronology to decide whether the spec is still true. The section closes with the changelog entry's checkable shape (5/6/4/1 plus its date) and the byte-identity guarantee promoted from V3 — "no later commit rewrites it", the one claim in this spec a future commit could falsify without anyone editing it.

**V5 was deliberately not written into the spec as an enforcement claim.** The spec says instead exactly what holds: `AGENTS.md` rule 31 carries the `pyproject.toml` / `__init__.py` pairing as **prose** policy, and `::test_version` pins the runtime literal alone. Claiming a mechanical check the tree does not have would be this cycle widening a shipped card, and the rejection is recorded in the rationale.

The spec went 1,651 bytes / 60 lines -> 2,814 / 57: more prose, less structure. The rationale is 23,818 bytes / 364 lines and carries seven entries keyed to the spec, the recovered history of what `231911a8` actually did, the alternatives each reconciliation choice rejected, and the provenance split between moved / deleted / added.

### Spec changes made (Worker 1 only)

`docs/SPECS/spec-012-version_release_alignment-0_0_4.md`, all line refs against the pre-edit file at `HEAD` (`5851bb59`).

| Spec line(s) | Change | Reason | Trigger |
|---|---|---|---|
| 7 | Preamble paragraph **moved** to the rationale; replaced by the one-line pointer sentence naming what moved and where. | Process justification, not contract; and its instruction ("expand it before implementation work starts") is counterfactual — the work shipped 2026-05-08, the file was created 2026-06-01. Argument cross-referenced to the spec-007 rationale, not re-litigated. | F2 |
| 9-16 | `## Card snapshot` reduced to two bullets: card id / status / milestone, plus a sentence stating the remaining board fields belong to the Kanban DB. Labels, priority, and relative size **deleted**. | The label list was already wrong at `HEAD` (`release`, `versioning` vs. `internal`, `release`, `versioning`). A hand-copied DB render in a file nothing re-renders drifts silently on every board edit; patching it buys correctness until the next one. | F5 |
| 18-20 | `## Planning note` **moved** in full (heading plus the one-word body "shipped"). | It renders one Kanban column, and the value it rendered is a status the `Status:` line already carries one screen above. | F3 |
| 24 | `## Scope` bullet 1 **rewritten** into a five-bullet enumeration of the version surfaces plus the per-release-obligation sentence and the enforcement statement. | "now agree on `0.0.4`" is a release-cut fact in the present tense, so at `HEAD` it reads as a standing invariant that is false. The fact is true and verified (V1); only the tense outlived it. | F6, F7, V5 |
| 25 | `## Scope` bullet 2 **rewritten** to state the changelog entry's shape (5/6/4/1) and date, plus "no later commit rewrites it". | "condensed" names an act against a draft the reader cannot see, so it is true and uncheckable. The resulting shape is checkable; the act and its before/after table live in the rationale. | F4 (partial), V3 |
| 27-35 | `## Other` heading and all **seven** bullets **deleted**, disposed of one by one in the rationale. | Two `#### Note` rows and five `#### Files likely touched` paths flattened under a heading naming neither kind; one row duplicated `## Scope` bullet 1, one is board triage, and the five paths are a *prediction* the card's own diff (two files, neither of them listed) contradicts. The five survive re-framed in `## Scope` as the surfaces the version string lives on. | F4, F7 |
| 40 | `[backlog]: ../../BACKLOG.md` **left in place, unused**. | A 71-definition / 23-file cross-surface pattern the board's checker card already owns; `worker-0.md` `## Closing out a kanban card` forbids partial-fixing it. Same disposition as the spec-011 cycle. | F8 |
| link block | Gained `[spec-012-rationale]`, `[changelog]`, `[pyproject]`, `[uv-lock]`, `[init]`, `[test-init]`; `[glossary-djangotype]` changed carrier within `## Scope`. | The rewritten `## Scope` cites five files by path; the pointer sentence needs its target. | F1, F6 |

New file created: `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md`. No file was moved or renamed; the spec was already at its archived location with correct-depth link definitions (the plan's F10, R2's to audit).

### Items for the final gate's `### Deferred work catalog`

- **The `pyproject.toml` <-> `__init__.py` pairing has no executable pin.** `AGENTS.md` rule 31 states it in prose; `tests/base/test_init.py::test_version` asserts a literal and never reads `pyproject.toml`. Not a spec-012 defect — the card promised agreement at one release and delivered it — and deliberately not written into the spec as an enforcement claim. Source: this artifact, `### Re-derivation of the plan's measurements` (V5) and `### Summary`.
- **The unused `[backlog]` link definition** in this spec, one of 71 unused definitions across 23 files the board's checker card owns as a single sweep. Left in place. Source: this artifact, F8; the rationale's `### The \`[backlog]\` link definition — recorded, not fixed`.

### Notes for Worker 0

- The plan's **F4 count is wrong: seven bullets, not six** (its own enumeration sums to seven). The plan is Worker 0's file and was not edited by this pass.
- The plan's **F5 framing** is directionally right but historically compressed; the blob-verified sequence is in `### Re-derivation of the plan's measurements` above.
- Nothing this item found requires a `KANBAN.md` card-body or kanban-DB edit. F5's label drift is a defect in the **spec's copy** of the board data, and the fix was deleting the copy; the board itself is correct.

### Final status

`final-accepted`. R1 is complete: the rationale companion exists, the spec states a current contract with no chronology in it, all eight findings are discharged or recorded with their disposition, and every plan figure was re-derived with the one that disagreed corrected on the record.

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
