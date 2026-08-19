# Build: Slice 1 — Rationale authoring

Spec reference: `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` (whole file; the move touches lines 4, 8-10, 118-122, 209-219, 226-246, 300-311, 316-328, 333-345, 350-360, 367-380, 387-399, 404-415, 603-614 as they stood before this pass)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Refreshed for the **whole package** with the `worker-1.md` `### Package-wide helper inventory before helper planning` AST command over `django_strawberry_framework/` (all `*.py`, not just `utils/`), and grepped it for the shapes this slice could plausibly touch: `scalar`, `config`, `parse`, `serialize`, `label`, `safe`. Relevant candidates found: `scalars.py::strawberry_config`, `scalars.py::_safe_scalar_map_key_label`, `scalars.py::_parse_bigint`, `scalars.py::_serialize_bigint`, `exceptions.py::_safe_arg_repr`, `exceptions.py::_safe_type_name`. **None is planned for change**: this slice writes Markdown only, and the inventory was refreshed because the step is unconditional, not because a helper was under consideration.
- **Existing patterns reused.** The rationale file's structure is copied from the one sibling already on disk, `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` — its `## Provenance of this record` measured-population table, its per-Decision `### Justification (moved from the spec)` / `### Alternatives considered (and rejected)` / `### Changes this Decision underwent` / `### Claims this Decision may no longer make` quartet, its `## Deliberation moved from non-Decision sections` bucket, and its `### Verification performed by this pass` close. The spec-side pointer sentence reuses `docs/SPECS/spec-023-multi_db-0_0_7.md`'s exact shape (`Rationale companion — <what moved>: [Decision N][rationale-dN].`) and its `Status:`-line pointer clause.
- **New helpers justified.** None. No `.py` file is touched, so `ruff` is not run this slice.
- **Duplication risk avoided.** The single real risk in a rationale move is **a copy instead of a cut** — the same paragraph left live in both files, which is worse than either alone because a reader cannot tell which is current. Prevented mechanically: the moved blocks are extracted from the spec and re-emitted into the rationale by one script, so the same string cannot be written to one file without being deleted from the other, and the post-pass sweep counts `Justification:` and `Alternatives considered (and rejected):` occurrences in the spec (must be 0) as well as in the rationale.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing.

1. Create `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md` on the `spec-023` sibling's shape.
2. Move OUT of `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`, verbatim:
   - the `Revision history` block (spec lines 8-10);
   - all **nine** `Justification:` blocks (209-213, 226-235, 300-304, 316-321, 333-338, 350-354, 367-373, 387-392, 404-409), less the one bullet named in step 3;
   - all **nine** `Alternatives considered (and rejected):` blocks (215-218, 237-245, 306-310, 323-327, 340-344, 356-359, 375-379, 394-398, 411-414);
   - the three `### Explicitly do not borrow` rejection bullets (120-122);
   - the `Preferred answer:` / `Fallback:` deliberation inside `## Risks and open questions` (607-614) — all 8 bullets, cut uniformly from `Preferred answer:` to end of bullet, which is exactly where each bullet stops stating a constraint and starts reasoning about a contingency.
3. **Retain in the spec, per the `BUILD.md` implementation-relevant carve-out:** Decision 7's `**Defense-in-depth note (intentional duplication with `tests/types/test_converters.py`).**` bullet, re-homed as body prose rather than as a `Justification:` bullet. It tells a future DRY pass not to delete the duplication; a builder who never reads it deletes two integration tests. Nothing else from the nine blocks stays.
4. Add a one-line `Rationale companion — …: [Decision N][rationale-dN].` pointer under each of the nine Decisions, a pointer sentence under `### Explicitly do not borrow`, a pointer clause on the `Status:` line, and one under `## Risks and open questions`.
5. Write the **D1-D13 divergence record** into the rationale, one entry per divergence, each keyed to the spec heading + anchor it touches, recording the spec's claim, the truth at HEAD, the attribution, and — where the original reasoning was wrong in **mechanism** rather than merely superseded — saying so plainly. D3 and D5 are the load-bearing entries.
6. Add rationale entries for the two Decision-level facts Worker 0 re-verified as still true (Decision 3's no-warning overload, Decision 4's `ValueError`-not-`ConfigurationError`), so a future reader can separate "still true" from "not checked".
7. Add the ten canonical link-definition group headers to the new file, in order, and re-relativize every moved reference from `docs/SPECS/` to `docs/SPECS/appx/` (one extra `../`).
8. Verify: `check_spec_glossary.py` still exits 0 at 17 terms; `check_trailing_commas.py --check` exits 0 on both files; every in-page anchor resolves in both files; no `used-not-defined` / `defined-not-used` reference id in either file; every link-definition path disk-exists and every cross-file `#fragment` resolves. Record the spec's byte count before and after.

### Test additions / updates

None. No `.py` file is touched, so there is nothing to pin with a test and no focused suite is owned by this slice. The two suites Worker 0 recorded green (`tests/test_scalars.py tests/base/test_init.py tests/types/test_converters.py` -> 134 passed; `examples/fakeshop/test_query/test_scalars_api.py` -> 29 passed) are re-run by the final gate, not here — this slice cannot change their outcome. No temp tests are appropriate.

### Implementation discretion items

Assessed and decided as this pass's own judgement calls, recorded so the reviewer sees they were decided rather than defaulted:

- **Whether `## Risks and open questions` survives as a section.** It does. Preferred-answer-plus-fallback is forward-looking contingency, not chronology, and the `spec-023` sibling set the same precedent. Only the deliberative halves move.
- **Whether the falsified `Upload` prediction is deleted or moved.** Moved, wrapped in an explicit retraction, because the D3 entry needs the wrong mechanism on the page to be able to correct it. `BUILD.md` rule 2 (delete, do not move, falsified prose) governs the **spec**; the rationale's own "claims this Decision may no longer make" register is where a retracted claim is supposed to live.
- **Whether the D1-D13 record lands in this file now or at Slice 2.** Now. The maintainer's dispatch puts the reconciliation story here, and Slice 2 appends its own record beneath it — the same two-pass shape `spec-023`'s rationale carries.

### Spec slice checklist (verbatim)

The spec's `## Slice checklist` has no sub-bullet for a rationale move: the move is a `docs/builder/BUILD.md` pre-flight obligation (step 7) that the original `025` cycle never ran, not a spec-authored slice. There is therefore no verbatim text to copy, and no `### Dispatched findings checklist` either (this is not a review round). The obligations this slice is audited against are the `worker-1.md` `### Performing the rationale move` rules, tracked here:

- [x] Every block that landed in the rationale file LEFT the spec (cut, not copy).
- [x] Every Decision keeps a one-line pointer naming what was moved and where.
- [x] Prose the current decisions have falsified is deleted from the spec, not restated in it — **scoped to the moved text**: the two dead contingencies inside the risks fallbacks and the retracted `Upload` mechanism left the spec and are marked as retracted in the rationale. The thirteen drifted claims that are *not* part of the deliberative layer are untouched by design; rewriting them is Slice 2's writable scope, and doing it here would fold two reviewable diffs into one.
- [x] `check_spec_glossary.py` exits 0 after the move.
- [x] Every in-page anchor still resolves in both files.
- [x] No surviving cross-reference points into moved text without naming the rationale file.
- [x] The spec's byte count before and after is recorded for the plan preamble.
- [x] Every entry in the rationale names the spec decision or section it belongs to, by heading and anchor.

---

## Build report (Worker 2)

Not applicable. Worker 1 is the sole writing role in this cycle (`docs/builder/build-025-scalar_map_helper-0_0_7.md` `Ownership partition`), and a rationale file is a surface Worker 2 may never touch (`docs/builder/BUILD.md` `## Required reading per worker`: **never**). The execution record for this slice is below, under `## Execution record (Worker 1)`. A separate Worker 3 spawn reviews it, so writer/reviewer isolation holds.

---

## Execution record (Worker 1)

### Files touched

- `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md` — **created.** The deliberative layer moved out of the spec, plus the D1-D13 post-ship divergence record and the two re-verified-still-true facts.
- `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` — the move's removals and the pointer lines. Every edit is itemized under `### Spec changes made (Worker 1 only)`.
- `docs/builder/bld-slice-1-025-rationale_authoring.md` — this artifact.
- `docs/builder/worker-memory/worker-1-025.md` — memory entry appended.

No `.py` file was touched, so `ruff format` / `ruff check --fix` were not run (`AGENTS.md` scopes them to edits; the spec's own DoD 20 is a ship-time item already discharged).

### Populations measured

Measured on the spec as it stood immediately before the first edit of this pass.

| Population | Measured | Instrument |
|---|---|---|
| spec bytes before | 135,777 | `wc -c` |
| spec bytes after | 107,692 | `wc -c` |
| `Revision history` entries, inline | 1 | `grep -cE '^\- \*\*Revision [0-9]+\*\*'` |
| `Justification:` blocks at line start | 9 | `grep -c '^Justification:'` |
| `Justification`-prefixed clauses **anywhere** | 9 | `grep -oE 'Justification[a-z ]*:' \| wc -l` |
| `Alternatives considered (and rejected):` blocks | 9 | `grep -c '^Alternatives considered (and rejected):'` |
| rejected-alternative bullets under those 9 blocks | 28 | counted per block from the extractor's line spans |
| `### Explicitly do not borrow` rejection bullets | 3 | `sed -n '120,122p'` |
| justification bullets under those 9 blocks | 38 (37 moved, 1 retained) | counted per block from the extractor's line spans |
| `## Risks and open questions` bullets | 8 | the section's own `- **` lines |
| `Preferred answer:` clauses | 8 | `grep -o 'Preferred answer:' \| wc -l` |
| `Fallback:` clauses | 8 | `grep -o 'Fallback:' \| wc -l` |
| `def test_` items in `tests/test_scalars.py` | 53 | `grep -c '^def test_'` |

The two clause-level counts matter more than the block counts: a `Justification`-prefixed clause **anywhere** (9) equalling the line-start count (9) is what proves no inline justification survived outside the nine blocks. `grep -c` counts *lines*, not occurrences, so every population above that can appear more than once on a line was taken with `grep -o | wc -l` instead. Two figures this pass carried in from its own first reading were wrong and were corrected by re-deriving them: the risks section has **8** bullets, not 7, and the nine alternatives blocks carry **28** bullets, not 24.

**Third count corrected at final verification (Worker 1).** The justification-bullet row above read `37 (36 moved, 1 retained)` and is now `38 (37 moved, 1 retained)`. Re-derived per block from `git show HEAD:<spec>`: `[3, 8, 3, 4, 4, 3, 5, 4, 4]` = **38**, of which Decision 7's fifth bullet is the retained one, leaving **37** in the rationale — which is what the rationale actually carries (counted independently under its nine `### Justification (moved from the spec)` headings). Both halves of the original figure were low by one. The same wrong figure is in this cycle's Worker 1 memory entry, corrected there in the final-verification entry rather than by rewriting the earlier one.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` -> `OK: 17 terms - all have glossary entries and at least one spec link.` exit 0. **Unchanged from pre-flight step 6**, which is the number the spec's own DoD 9a pins — the move could have dropped a term's only spec link and did not.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-025-scalar_map_helper-0_0_7.md docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md docs/builder/bld-slice-1-025-rationale_authoring.md` -> exit 0.
- In-page anchors, both files: every `](#…)` resolved against the file's own computed heading slugs. Spec: the same 10 unresolved targets as before the pass, all of them **quoted GLOSSARY entry text** inside `## Doc updates` (`#bigint-scalar`, `#upload-scalar`, `#specialized-scalar-conversions`, `#djangotype`, `#strawberry_config`) plus one genuine pre-existing break, `](#step-3--read-the-kanban)` in Decision 8 — carried into `### Notes for Worker 1 (spec reconciliation)` for Slice 2, untouched here. Rationale: 0 unresolved.
- Reference ids, both files: `used-not-defined: []`, `defined-not-used: []`, with code spans and fenced blocks stripped before the sweep. Four spec definitions were orphaned by the removals (`[spec-018]`, `[spec-019]`, `[conf]`, `[next-step-8]`) and were deleted; all four are defined in the rationale, whose moved text still uses them. `[next]`, `[readme-repo]` and the `spec-020` / `spec-021` / `spec-022` / `spec-023` ids survive in the spec because non-moved text still uses them.
- Link-definition paths, both files: every path disk-exists-checked and every cross-file `#fragment` resolved against the target file's real headings. The rationale reports 0 failures. The spec reports the same 5 pre-existing failures as before the pass (`[config]` and `[scalar]` under `python3.10` = D12; `#decision-9--joint-0_0_7-cut` on `spec-023` = anchor rot; two `TODAY.md` fragments) — all Slice 2's, none introduced here.
- `git status --short`: the four files above, plus the baseline-dirty out-of-scope set the plan lists. No unexpected churn; nothing reverted.
- No `pytest` run this slice, with or without a coverage flag. No `.py` file, no test, no commit, no branch.

### Failability proofs

None; this pass introduced no new boundary. It writes Markdown only — no guard, gate, cap, or rejection path exists in the diff to mutate.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The move ran as one script over the spec's own bytes**, not as retyping. Each block was extracted by line span, re-emitted into the rationale, and deleted from the spec in the same run, so a copy-instead-of-cut is structurally impossible rather than merely checked for afterwards.
- **`## Provenance of this record` says what this pass did and did not reconstruct.** The nine justifications, the nine alternatives lists, the revision history, the three do-not-borrow bullets and the moved risk clauses are cuts. The per-Decision `### Changes this Decision underwent` records and the whole D1-D13 section are **new material** — the original cycle never wrote a change record because it never ran this pass. A reader who cannot tell those apart cannot trust either.
- **One justification bullet stayed in the spec.** Decision 7's defense-in-depth note is why the duplication between `tests/test_scalars.py` and `tests/types/test_converters.py` exists; it changes what a future DRY pass is allowed to delete, which is the `BUILD.md` carve-out exactly. It is re-homed as Decision 7 body prose and is deliberately **absent** from the rationale, so the two files do not both carry it.
- **Every letter, number, and checkbox in the moved text was left as written.** Pre-correcting during a move is how a move becomes an unreviewable diff; the D1-D13 record states what is wrong, and Slice 2 changes the spec.

### Notes for Worker 3

- The diff is best read as three independent things: (a) `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md` as a new file, (b) deletions in the spec, (c) 12 added pointer lines in the spec. The cut-not-copy property is checkable in one command: `grep -c '^Justification:' docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` -> 0, and the same for `^Alternatives considered`.
- The rationale file is **not** in Worker 2's reading set and is in Worker 3's (`docs/builder/BUILD.md` `## Required reading per worker`), so reviewing it against the shipped implementation is in scope.
- The `### Verification performed by this pass` subsection at the end of the rationale file restates the checks above from inside the durable record; both are meant to be there (the artifact closes with the cycle, the rationale does not).

### Notes for Worker 1 (spec reconciliation)

Carried forward to **Slice 2**, whose writable set includes the spec's D1-D13 rewrites. Nothing here is actionable in Slice 1.

- **D1-D13 are unstarted as spec edits.** This slice recorded all thirteen in the rationale and changed no drifted claim in the spec beyond deleting moved deliberation. Every one of the thirteen surfaces in `docs/builder/build-025-scalar_map_helper-0_0_7.md` `### Verified post-ship divergences handed to Worker 1` is still live in the spec.
- **Two anchor-level defects found by this pass's own sweep**, neither in the divergence catalog:
  - `## Risks and open questions` -> Decision 8's body carries `[Step 3](#step-3--read-the-kanban)`, an in-page anchor with no matching heading anywhere in the spec. It points at a step of the authoring flow the spec never included. Slice 2 should drop the link and keep the claim, or re-point it at `docs/SPECS/NEXT.md`.
  - The link definition `[spec-023-decision-9]: spec-023-multi_db-0_0_7.md#decision-9--joint-0_0_7-cut` no longer resolves: the sibling's heading now slugs to `decision-9--joint-007-cut` (dotted-version anchors slug to `007`). Two spec sites use that id.
- **Decision 8's own heading text is falsified by D1** (`### Decision 8 — Version posture: cut already shipped, this card lands under `[Unreleased]``). Renaming the heading moves its slug, so Slice 2 must sweep every in-page use of `#decision-8--version-posture-cut-already-shipped-this-card-lands-under-unreleased` in the spec **and** the `[spec-025-d8]` reference id in the rationale in the same pass. **Population re-derived at final verification: 7 uses in the spec, not 6** (`grep -o … | wc -l`), and the rationale carries **5** `spec-025-d8` occurrences — 1 definition plus 4 uses, not the single definition this note originally implied. Both figures are what Slice 2 must actually sweep.
- **Doc-side residue outside the scope fence** (spec + `.py` only), for the final gate's deferred-work catalog, not for an edit: `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv` rows for `DjangoFileType` / `DjangoImageType` cite `TODO-ALPHA-028-0.0.11`, which shipped as `DONE-037-0.0.11`; and the `TODO-ALPHA-051-0.0.15` KANBAN bullet still describes six `[spec-013]` / `[spec-011]` occurrences in this spec that grep now reports as 0.

---

## Review (Worker 3)

Pending — a separate Worker 3 spawn reviews this slice.

---

## Final verification (Worker 1)

Performed by a **fresh** Worker 1 spawn that did not write this slice. Every number the report states was re-derived here rather than accepted; where a re-derivation disagreed with the report, the report was corrected in place and the correction is named below. The HEAD reference for every read-only comparison is `git show HEAD:docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` written to a scratch path **outside** the repository; no `git stash`, `checkout`, `restore`, or `worktree` was used at any point (a concurrent session is live on this tree — `HEAD` moved to `ddf8bbaf` between this cycle's pre-flight and this pass).

**Process deviation, recorded not waived.** `## Review (Worker 3)` reads `Pending` and the artifact arrived at `Status: built`, so this pass ran before the review step `worker-1.md` `## Final verification job` assumes. The maintainer's dispatch ordered it explicitly. Because the slice is Markdown-only with no diff for a reviewer to read beyond the two files audited here, every check a Worker 3 pass would have owned was performed independently in this section; nothing is accepted on the mover's word.

### 1. The move was a MOVE, not a copy

Verified by content, not by the report's sweep tokens.

- Spec byte counts confirmed exactly: `git show HEAD:` copy is **135,777** and the worktree spec is **107,692** — both figures as reported.
- The report's own tokens are absent from the spec: `Justification` **0**, `Alternatives considered` **0**, `Preferred answer:` **0**, `Fallback:` **0**, `Revision history` **0** occurrences (`grep -o | wc -l`, not `grep -c`).
- That token sweep is not sufficient on its own, so the whole diff was walked: **132** removed lines, **34** added. Every removed line was tested for verbatim presence in the rationale; **112 of 132** matched exactly. The **20** that did not were each resolved individually by a distinctive-token search rather than assumed benign, and all 20 are accounted for: 1 `Status:` line rewritten in place, 1 `Revision history` header, 1 risks-section preamble rewritten, 8 risk bullets split at `Preferred answer:` (retained half in the spec, moved half in the rationale — all 8 moved halves found **exactly once** in the rationale and **zero** times in the spec), 4 link definitions deleted-and-redefined in the rationale, 1 defense-in-depth bullet deliberately retained (item 6 below), and 4 bullets whose only difference is a re-relativized link target or an in-page anchor re-pointed at the spec — each confirmed present in the rationale by its distinctive prose.
- The 34 added lines were read end to end: the `Status:` rewrite, the borrowing pointer, **9** `Rationale companion` pointer lines (one per Decision, count re-derived), the re-homed defense-in-depth bullet, the risks preamble, the 8 trimmed risk bullets, and 12 new link definitions. **No D1-D13 rewrite crept in** — the spec diff is confined to the move, as the slice's fence requires.

### 2. The spec reads as a clean current contract

No chronology survives. Occurrences in the spec: `Revision 1` **0**, `as of revision` **0**, `as of review` **0**, `Amendment` **0**, `Retraction` **0**, `review round` **0**, `Superseded` **0**, `archaeology` **0**. The single `Revision history` occurrence and the single `retracted` occurrence are both inside `Rationale companion` pointer sentences naming what moved, which `worker-1.md` `### Performing the rationale move` rule 1 requires rather than forbids. There is no amendment block and no retraction block. A reader never has to apply a history to the spec.

### 3. The rationale is keyed to the spec

Not spot-checked — verified exhaustively, which turned out to be cheaper than sampling. Every reference definition in the rationale was disk-resolved and every definition carrying a `#fragment` was resolved against the target file's real computed heading slugs: **0 failures** across all 44 definitions, including all nine `[spec-025-d1]`-`[spec-025-d9]` anchors and the `dod` / `edge-cases` / `error-shapes` / `non-goals` / `problem-statement` / `risks` / `slice-checklist` / `test-plan` / `user-facing-api` anchors the D-entries key off. Every Decision entry carries the `### Justification` / `### Alternatives considered (and rejected)` / `### Changes this Decision underwent` quartet, with `### Claims this Decision may no longer make` present on Decisions 1, 2, 3, 7, 8, 9 and absent on 4, 5, 6 — correct, since `BUILD.md` requires *any* such claim, not a placeholder. The keying is bidirectional: the spec's twelve new `[rationale-*]` definitions were resolved the same way and all twelve hit real rationale headings.

### 4. Nothing was lost in transit

- **Decision 2's alternatives list, the longest, checked end to end.** HEAD carries **7** bullets at lines 239-245. All **7** are present in the rationale **byte-identical** (whole-line `grep -F`), each exactly once, and each **absent** from the spec.
- **Both bullet populations re-derived per block from HEAD.** Alternatives: `[2, 7, 3, 3, 3, 2, 3, 3, 2]` = **28**, and the rationale's nine `### Alternatives considered` sections hold the same per-block spans and the same total. The report's corrected 28 is right.
- **The report's other corrected figure is still wrong, and is now fixed.** Justification bullets at HEAD are `[3, 8, 3, 4, 4, 3, 5, 4, 4]` = **38**, not 37; 1 retained leaves **37** moved, not 36. The rationale independently holds 37. Both halves were low by one. Corrected in `### Populations measured` with the derivation recorded. This is the third count in one pass to fail on first statement, after the two the mover caught itself — the standing lesson holds, and a *corrected* figure deserves no more trust than the original.
- The nine `Rationale companion` pointer lines each state their own block's bullet counts in prose ("two rejected filename alternatives", "eight justification bullets and its seven rejected alternatives", …). All nine were checked against the per-block derivation and **all nine are accurate**.

### 5. D1-D13, with D3 and D5 re-verified against source

All thirteen entries present as `### D1` … `### D13`, each keyed to spec headings by reference-style anchor, each stating claim / truth-at-HEAD / attribution.

- **D3 — confirmed exactly as stated.** `Upload = NewType("Upload", bytes)` at `.venv/lib/python3.14/site-packages/strawberry/file_uploads/scalars.py:5`; present in `DEFAULT_SCALAR_REGISTRY` as `Upload: UploadDefinition`; `django_strawberry_framework/scalars.py::_PACKAGE_SCALAR_MAP` holds `{BigInt: _BIGINT_SCALAR_DEFINITION}` and nothing else, so there is **no** `Upload` entry; both pins exist (`tests/test_scalars.py::test_strawberry_config_scalar_map_excludes_upload`, `::test_upload_field_resolves_under_plain_strawberry_config`). The entry's distinction — the prediction was right in outcome and wrong in mechanism — is the correct reading of the source.
- **D5 — confirmed exactly as stated,** including the quoted HEAD code block, which matches `django_strawberry_framework/scalars.py::strawberry_config` character for character: an explicit `if extra_scalar_map is None:` branch, and an `else` whose `dict(extra_scalar_map)` sits under `except BaseException as exc: raise ValueError("strawberry_config(extra_scalar_map=...) must be materializable; …") from exc`. `dc00f4a6` exists and touches `scalars.py` (52 lines), so the attribution holds. The entry's load-bearing claim — that the **spec itself** specified the fail-open shape rather than an implementation slipping it past the spec — is correct and is the right thing to have recorded.
- D4 and D6 were confirmed incidentally while reading `scalars.py` (`_safe_scalar_map_key_label` present with the raising-`__name__` and non-`str` guards).

### 6. The retained justification bullet — graded

**The carve-out licenses it; keep it.** `BUILD.md` `## Spec rationale extraction` keeps in the spec "the 'why' that changes HOW a thing is built", and closes with "when it is unclear whether a sentence is deliberation or instruction, **it stays**." Decision 7's defense-in-depth note is not narration of how the Decision was reached — it is a standing instruction to a future DRY pass that two integration tests are duplicated **on purpose** and may not be collapsed. A maintainer who never reads it deletes coverage. That is the carve-out's central case, not its margin, and the tie-break sentence would keep the bullet even if the call were close.

**Its absence from the rationale is defensible, and is the only correct outcome.** The operation is a MOVE, so a bullet that stayed in the spec cannot also be in the rationale without creating the two-live-copies state that is worse than either alone. What matters is that the rationale does not *hide* the retention, and it does not: line 21 names the bullet, quotes its heading, says it stayed, and gives the carve-out reason. The Decision 7 pointer line in the spec also names the retention ("this Decision's **remaining** justification"). A reader of either file can reach the fact from the other. Confirmed by count: `Defense-in-depth note` appears once in the spec as body prose (with its full text) and once in the rationale (as the retention record only, no text). Nothing to change.

### 7. Gates

| Gate | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` | `OK: 17 terms - all have glossary entries and at least one spec link.` exit **0** — the count DoD 9a pins, unchanged from pre-flight, and re-run after this pass's own edit |
| `uv run python scripts/check_trailing_commas.py --check` on the spec, the rationale, and this artifact | exit **0**, before and after this pass's edits |
| `git diff --check` on the spec | exit **0**, no output |
| whitespace on the untracked rationale (not reachable by `git diff --check`) | **0** lines with trailing whitespace in either file; the rationale ends with exactly one newline. `git diff --check --no-index /dev/null <file>` exits 1 purely because the diff is non-empty and printed no whitespace error, so it is not the instrument for an untracked file — recorded so a later pass does not misread that exit code |
| `pytest` | not run; no `.py` file in the slice, and no `--cov*` flag was used anywhere in this pass |

### 8. Link integrity — one defect found and fixed

`START.md` "Markdown link convention" compliance for the rationale: exactly **1** `<!-- LINK DEFINITIONS -->` delimiter, all **10** canonical group headers present in the exact canonical order, defs alphabetical within every group (including the non-obvious `spec-025-slice-checklist` < `spec-025-terms` < `spec-025-test-plan`), and each def grouped by where its **target** lives — `[spec-025-terms]` correctly under `<!-- docs/SPECS/ -->` despite sitting in `appx/`, per the closed-list rule. Re-relativization from `docs/SPECS/` to `docs/SPECS/appx/` is correct throughout: all **44** definition paths disk-exist and every `#fragment` among them resolves (**0** failures).

**Defect (fixed in this pass).** The mover's sweep covered link *definitions*, so it was structurally blind to inline links — and the rationale carried one, in Decision 2's moved `**Type signature.**` bullet: `](../../../.venv/lib/python3.10/site-packages/strawberry/schema/config.py)`. Two faults in one link. It is an inline cross-file link in a brand-new file, which the convention forbids; and its path is **dead on disk**, because the venv is `python3.14`. The report's "the rationale reports 0 failures" was true of definitions and could not see this. Fixed by pointing it at the file's already-present, already-resolving `[config]` definition, which makes it identical in shape to the same citation two bullets later (`…scalar.py …`][scalar]`) — the stale `python3.10` **label** is left exactly as the moved text wrote it, since relabelling is D12's business and D12 is Slice 2's. Post-fix: the rationale has **zero** live inline cross-file links, and `used-not-defined: []` / `defined-not-used: []` still hold, as do both gates. (The two apparent `](../../CHANGELOG.md)` hits a naive sweep reports are inside code spans in the provenance section that *documents* the re-relativization; they are not links. An instrument that does not strip inline code spans over-reports here — which is also why my first anchor sweep wrongly showed 5 unresolved anchors in the rationale.)

**In-page anchors, with code spans stripped.** Rationale: **53** anchors, **0** unresolved — the report's claim is correct, and the two anchors that would have dangled after the move (`#error-shapes`, `#risks-and-open-questions`, which have no counterpart heading in the rationale) were correctly converted to `[spec-025-error-shapes]` / `[spec-025-risks]` reference links into the spec, while `#decision-4--…` correctly stayed in-page because the rationale has its own Decision 4. That is the subtle half of this move and it was done right.

**Pre-existence claim verified read-only.** The spec's **5** dead definitions and its unresolved in-page anchors are byte-for-byte the same set at `HEAD` and in the worktree, so all of them predate this pass: dead paths `[config]` and `[scalar]` (both `python3.10`), and dead fragments `[spec-023-decision-9]`, `today-what-to-put-in-examplesfakeshopconfigschemapy-today`, `today-whats-in-examplesfakeshopappsproductsschemapy-today`. Unresolved in-page anchors are **10 occurrences** at HEAD and **10** now — `strawberry_config` ×2, `bigint-scalar` ×2, `upload-scalar` ×2, `specialized-scalar-conversions` ×2, `djangotype` ×1, `step-3--read-the-kanban` ×1 — with the total anchor population dropping 95 → 73 as the move predicts. The spec also retains one inline dead `python3.10` link at `## Edge cases`, likewise present at HEAD. **None introduced by this slice.**

### 9. The two deferred anchor defects — both confirmed

- `](#step-3--read-the-kanban)` in Decision 8's body resolves to **no heading anywhere in the spec** — confirmed by slug computation over every heading, and confirmed present at HEAD.
- `[spec-023-decision-9]: spec-023-multi_db-0_0_7.md#decision-9--joint-0_0_7-cut` — the target heading is `### Decision 9 — Joint \`0.0.7\` cut`, which slugs to `decision-9--joint-007-cut`. The dotted version collapses to `007`, so the def's `0_0_7` spelling cannot resolve. Confirmed, and confirmed used at **2** sites in the spec.

Both are correctly **deferred, not dropped**: both are written up in `### Notes for Worker 1 (spec reconciliation)` as Slice 2 work, with a proposed remedy each. Leaving them live in Slice 1 is right — they are spec-side claim repairs, which is Slice 2's writable scope.

### 10. Scope compliance

`git status --short` confirms Slice 1 wrote exactly its four authorized paths — the spec, the rationale, this artifact, and `worker-memory/worker-1-025.md` — with mtimes clustered at 00:05:39-00:07:59. Every baseline-dirty out-of-scope file in the build plan is still dirty and **none was reverted**. No `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `CHANGELOG.md` / `docs/TREE.md` / `GOAL.md` / `README.md` edit, no `db.sqlite3` write, no `-terms.csv` edit is attributable to this slice. No `docs/builder/` artifact of the concurrent `spec-024` cycle was touched (`bld-slice-1a/1b/2/3-024`, `build-024`, `bld-003-final`, `docs/builder/DONE/` all carry earlier mtimes), and no other worker's memory file was read or written. A **third** concurrent cycle (`spec-026`) has since appeared on the tree — `docs/SPECS/spec-026-*.md`, `examples/fakeshop/apps/scalars/models.py`, `examples/fakeshop/test_query/test_scalars_api.py`, and several `-026` artifacts, none in this plan's baseline list because they postdate its pre-flight. All are out of scope and untouched.

### Checklist audit

All eight boxes in `### Spec slice checklist (verbatim)` are `- [x]` and all eight were independently confirmed above: cut-not-copy (1), pointers (4), falsified prose deleted (1, 2), `check_spec_glossary` (7), anchors (8), no cross-reference into moved text without naming the rationale (3, 8), byte counts (1), every entry keyed by heading and anchor (3). No box is over-ticked and none needed un-ticking. The D1-D13 spec rewrites are correctly **not** claimed by any box.

### Summary

The rationale MOVE is sound and is the strongest of these moves I have audited: the deliberative layer left the spec (135,777 → 107,692 bytes), landed complete in a companion keyed to the spec (76,619 bytes as the mover left it; **76,554** after this pass's one-link fix) in both directions with zero unresolved anchors or dead definitions, and the spec now reads as a clean current contract with no chronology. Nothing was lost in transit — Decision 2's seven alternatives are byte-identical, all eight risk fallbacks moved, and the one retained bullet is correctly licensed by the implementation-relevant carve-out and correctly recorded as retained rather than silently kept. Two defects were found and both were fixed in this pass: one dead inline cross-file link in the new rationale (the mover's definitions-only sweep could not see it) and one off-by-one bullet population in the report. Neither is a reason to re-loop a Markdown slice whose custodian is the same role performing this pass, so the status is `final-accepted` with the corrections recorded.

Standing lesson this pass adds: **a link sweep that enumerates definitions cannot see an inline link, and a rationale file inherits inline links from the spec it was cut from** — so re-relativization must sweep `](` targets as well as `[id]:` definitions. The mover's other claims all survived re-derivation.

### Spec changes made (Worker 1 only)

All edits are to `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`, all triggered by **Slice 1** (the rationale move). Line citations are the pre-edit positions.

| Spec line(s) | Change | Reason |
|---|---|---|
| 4 (`Status:`) | dropped "the revision history below is preserved for archaeology"; added the pointer clause naming the rationale file | the sentence described a block this pass removed; the `Status:` line is the reader's entry point to the companion |
| 8-10 | deleted the `Revision history` block | Revision 1's enumeration is deliberation, not contract; moved verbatim to the rationale's `## Revision history` |
| 118-122 | deleted the three `### Explicitly do not borrow` rejection bullets; added a pointer sentence | rejection reasoning; the section's factual no-upstream-precedent statements stay |
| 209-218 (D1) | deleted `Justification:` + `Alternatives considered (and rejected):`; added `Rationale companion` line | deliberation |
| 226-245 (D2) | same | deliberation |
| 300-310 (D3) | same | deliberation; the no-warning-overload mechanism is already stated normatively in the Decision body above, so nothing implementation-relevant left with it |
| 316-327 (D4) | same | deliberation; the message's key-naming and recourse requirement is already normative in the Decision body's quoted `ValueError` text |
| 333-344 (D5) | same | deliberation |
| 350-359 (D6) | same | deliberation |
| 367-379 (D7) | deleted both blocks **except** the defense-in-depth bullet, which was re-homed as Decision 7 body prose; added `Rationale companion` line naming the retention | the retained bullet changes what a future DRY pass may delete — the `BUILD.md` implementation-relevant carve-out |
| 387-398 (D8) | deleted both blocks; added `Rationale companion` line | deliberation |
| 404-414 (D9) | same | deliberation |
| 605 | rewrote the section preamble | it advertised a "preferred answer and fallback" shape the move removes |
| 607-614 | trimmed each of the 8 risk bullets to its live constraint; moved the `Preferred answer:` / `Fallback:` reasoning out | contingency reasoning, and two fallbacks are dead (the `WIP-ALPHA-020-0.0.8` re-tag; the "a future card may add a `BigIntegerField` column", which `DONE-026-0.0.7` did) |
| link definitions | removed `[spec-018]`, `[spec-019]`, `[conf]`, `[next-step-8]`; added `[spec-025-rationale]`, `[rationale-borrowing]`, `[rationale-risks]`, `[rationale-d1]`-`[rationale-d9]` | the four removed were used only by moved text; the twelve new ids serve the pointer lines |

No spec edit in this slice changes a contract, so no `revision-needed` is triggered and no builder re-pass is owed. The D1-D13 claim rewrites are **Slice 2's**, deliberately untouched here.

**Corrections made by the final-verification pass** (a different Worker 1 spawn from the mover; both files are this role's to correct, so neither warranted `revision-needed`):

| File | Change | Reason |
|---|---|---|
| `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`, Decision 2's `**Type signature.**` bullet | the inline link target `](../../../.venv/lib/python3.10/site-packages/strawberry/schema/config.py)` became the reference-style `][config]` | it was the file's only live inline cross-file link (`START.md` requires reference-style) **and** its path was dead on disk, the venv being `python3.14`. `[config]` was already defined and already resolving. The stale `python3.10` **label text** is untouched — relabelling every such citation is D12, which belongs to Slice 2 |
| `docs/builder/bld-slice-1-025-rationale_authoring.md`, `### Populations measured` | justification bullets `37 (36 moved, 1 retained)` -> `38 (37 moved, 1 retained)`, with the per-block derivation added below the table | re-derived from `git show HEAD:` as `[3, 8, 3, 4, 4, 3, 5, 4, 4]` = 38; the rationale independently carries 37. Both halves of the stated figure were low by one |

The spec itself was **not** edited by the final-verification pass: every remaining defect in it (the five dead definitions, the ten unresolved in-page anchors, the `step-3--read-the-kanban` break, the `[spec-023-decision-9]` slug, and all thirteen drifted claims) was verified **pre-existing at `HEAD`** and belongs to Slice 2's writable scope. `worker-1.md` `## Spec status-line re-verification` is discharged the same way: the header's `[Unreleased]` claim on line 3 **is** falsified, and it is catalogued as D1 with Slice 2 as its owner, so it is left live deliberately rather than overlooked.

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
