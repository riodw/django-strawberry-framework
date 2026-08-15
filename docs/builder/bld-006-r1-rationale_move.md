# Build: R1 — Spec rationale extraction (spec-006)

Spec reference: `docs/SPECS/spec-006-public_surface-0_0_3.md` (whole file; the move touched lines 1, 5, 95, 139-141, and 164 of the pre-move file)
Rationale file created: `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`
Status: final-accepted

**Shape note.** Per `docs/builder/build-006-public_surface-0_0_3.md` Deviation 2, R1 has no Worker 2 pass: `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move and states that Worker 2 never reads the rationale file. So `ARTIFACT.md`'s `## Build report (Worker 2)` is not applicable and the performance record lives under `## Move report (Worker 1)` below, carrying the same fields Worker 3 would otherwise read from a build report. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for this item.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and deliberately so rather than by omission. `worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper-like logic*; R1 changes no package source and adds no helper, shared constant, validation branch, coercion utility, or test helper. The build plan's `## Build-wide context flags` declares package source, `tests/`, and `examples/` read-only for the whole cycle. No inventory was refreshed and none was needed.
- **Existing patterns reused.** The two archived precedents at the same `docs/SPECS/appx/` depth supplied the file shape and were read for shape only: `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` (the H1 with the `(deliberation, rejected alternatives, change record)` suffix, the "Deliberative companion to …" opener, the "**The move happened long after the release, not before the build.**" provenance paragraph, `## How to read this file`, `## Provenance of this record`, `## Entries keyed to the spec`, the *Moved* / *Deliberately left in the spec* vocabulary, the per-entry `*Claims the spec no longer makes.*` closer, and the closing `## Standing note`) and `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (the status-claims-are-not-deliberation line its own extraction pass drew, which this pass follows). The link-definition scaffold at this depth — bare filename for an `appx/` sibling, `../` for a `docs/SPECS/` sibling, `../../builder/` for `BUILD.md`, `../../GLOSSARY.md` for a `docs/` target — is copied from those files' blocks.
- **New helpers justified.** None; no code was written.
- **Duplication risk avoided.** Three live risks, each **measured** rather than asserted:
  - **Against the spec.** The move is a cut, so no moved block may exist in both files. Measured: **0** non-scaffold 8-word shingles shared between the post-move spec and the rationale (14 total, all of them the `<!-- LINK DEFINITIONS -->` group-header run both files must carry). Two copies were caught by that measurement mid-pass and removed — see `### Two copies caught by measurement`.
  - **Against the sibling rationale files.** `appx/spec-005-…-rationale.md` narrates the `Meta`-key contract this spec extends to package level, and `appx/spec-002-…-rationale.md` narrates the optimizer's own section removals and its `## Visibility status` deferral. `## How to read this file` carries a bullet naming both and saying outright that neither is retold. No sentence from either was borrowed.
  - **Against the build plan.** The plan's drift table is R2's input and Worker 0's file. The rationale cites only what this pass re-measured itself, and it does not reproduce the table or pre-write R2's dispositions.

### Implementation steps

Line numbers are pin-at-write-time; all are against the **pre-move** spec unless stated.

1. Measure the pre-move spec (bytes, lines, fence count), take a read-only `git show HEAD:` copy into the scratchpad **outside** the repo as the verbatim-quote reference, and re-run the plan's two green baselines. Done.
2. Re-derive the sole anchor carrier for each of the 7 terms rather than trusting the plan's `### The 7-anchor constraint` table, counting reference-style uses with code spans excluded. Done — the table is correct in all seven rows; see `### The 7-anchor constraint — per-anchor result`.
3. Re-verify each candidate passage against the deliberation/instruction line myself rather than accepting the plan's `### What R1 inherits` list. Done — see `### Where I agreed and disagreed with the plan's candidate list`.
4. Insert the companion-file pointer paragraph after the H1 (spec:1). Done.
5. `## Problem statement` — cut the provenance sentence naming the original alpha review from the first paragraph (spec:5), leaving both surviving sentences untouched. Done.
6. `### docs/README.md structure` — cut the whole third paragraph, the rejected `Current` / `Planned` / `Not implemented yet` sectioning and its reason (spec:95); replace with a one-line pointer. Keep the two-section contract above it and the two-tree paragraph below it untouched. Done.
7. Delete `## Open questions` in full (spec:139-141). Done.
8. Add `[spec-006-rationale]` to the spec's `<!-- docs/SPECS/ -->` link-definition group (spec:164). Done.
9. Write the rationale file: one entry per section cut from, one entry keyed to the removed `## Open questions` heading anchored at the section its judgement bore on, plus the closing standing note the plan's `### What R1 inherits` names as this file's most valuable content. Done.
10. Run the full verification set and record every command with its result. Done — `### Validation run`.

### Test additions / updates

None. R1 adds no test and changes no code path. The verification for this item is the command set under `### Validation run`; `AGENTS.md` rule 15 forbids an unasked-for `pytest` run, and the build plan declares no residual item touches source, tests, or `examples/`.

### Implementation discretion items

None reserved. R1 has no downstream builder, so nothing is delegable.

### Dispatched findings checklist

Spec-006 has no `## Slice checklist` and this is not a review round, so — per `worker-1.md` planning step 8 and `BUILD.md` `### Dispatched findings checklist` — the boxes below are the R1 obligations drawn from the dispatch, `BUILD.md` `## Spec rationale extraction`, and `worker-1.md` `### Performing the rationale move`. Worker 1 both performs and ticks here because Deviation 2 removes the Worker 2 pass; the ticks are audited at Worker 1's own final verification after Worker 3.

- [x] The move is a cut-and-paste, not a copy and not a summary: text that lands in the rationale left the spec (measured: **0** non-scaffold shared shingles; every moved block proven present at HEAD, present in the rationale, absent from the post-move spec).
- [x] Every section cut from keeps a one-line pointer naming what was moved and where (`### docs/README.md structure`'s own pointer, plus the H1 companion pointer that names all three moved items — the disposition and its reasoning are in `### Implementation notes`).
- [x] **The 7-anchor constraint holds.** All seven carriers re-derived by measurement; none sat in moved text, so nothing needed re-siting. `check_spec_glossary.py` re-run and its exact output quoted in `### Validation run`.
- [x] The terms CSV was never opened for writing and is byte-unchanged.
- [x] Each clearly-deliberative passage the plan named was re-verified independently, and where I extended past the plan's list it is stated — `### Where I agreed and disagreed with the plan's candidate list`.
- [x] Rule 2 (delete, do not move, prose the current decisions have falsified) applied: nothing deleted, and the reason recorded in the rationale's `## Provenance of this record` so its absence does not read as a skipped step.
- [x] **R2's scope was not pre-empted.** No falsified contract statement was rewritten or removed; every drift row left in place is named with its reason in `### Rows left for R2, and why`.
- [x] The single-ownership law respected: the rationale records where spec-006 requested a duplicate, and performs no retirement.
- [x] Keyed entries: every entry names the spec section it belongs to by heading and links a resolving anchor; alternatives carry the one-line reason each lost; each entry states the claims the section may no longer make (or says it retracted none).
- [x] Link scaffold at `docs/SPECS/appx/` depth: reference-style only, `<!-- LINK DEFINITIONS -->` with all 10 canonical group headers in positional order, `../../GLOSSARY.md`-form for a `docs/` target and `../spec-NNN-….md` for a `docs/SPECS/` sibling. Every definition target disk-checked.
- [x] `check_trailing_commas.py --check` run on **both** files and the result quoted.
- [x] Spec byte count before and after reported, with the net direction explained rather than gamed.
- [x] `AGENTS.md` rule 27 holds in both files: no raw `path:NN`, and the property was verified as preserved rather than assumed.
- [x] The rationale file is written directly to `docs/SPECS/appx/` — never to `docs/` and moved after.
- [x] Hot-path declaration `none` and floor-verification scope `none` recorded explicitly, not by silence.
- [x] No source, test, example, sibling spec, terms CSV, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, or DB file written; no `pytest`, no `--cov*`, no `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit.

---

## Move report (Worker 1)

### Files touched

- `docs/SPECS/spec-006-public_surface-0_0_3.md` — 5 insertions, 6 deletions (`git diff --numstat`). One provenance sentence, one rejected-alternative paragraph, and one whole section cut; one companion pointer paragraph and one per-section pointer added; one link definition added.
- `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` — new, 228 lines / 15,449 bytes.

### Byte count (required report)

| | lines | bytes |
|---|---|---|
| spec **before** | 178 | 10,934 |
| spec **after** | 177 | 11,019 |
| delta | -1 | **+85 (+0.8%)** |
| rationale file (new) | 228 | 15,449 |

The before figures were re-measured with `wc -c -l` and match the build plan's pre-flight figure exactly (10,934 / 178). Fence markers (`grep -c '^```'`): **6** before, **6** after — the three fenced blocks (two import examples and the `__all__` tuple) are all contract or status and none sat inside moved prose, so unlike spec-002's and spec-003's cycles this move had no pseudo-code to dispose of.

**The spec grew by 85 bytes, and that is the honest result rather than a shortfall.** Measured at fragment granularity:

| | bytes |
|---|---|
| moved out: provenance sentence | -84 |
| moved out: README rejection paragraph | -235 |
| moved out: `## Open questions` (heading + body + blanks) | -41 |
| **total removed** | **-360** |
| added: H1 companion pointer paragraph | +270 |
| added: per-section README pointer | +105 |
| added: `[spec-006-rationale]` link definition | +70 |
| **total added** | **+445 (net +85)** |

Spec-006 is the smallest spec of the five residual cycles (10,934 bytes against spec-005's 13,346 and spec-004's 33,928) and its deliberative layer is **360 bytes** — three passages, one of them three words long. `worker-1.md` rule 1's pointer obligation costs more than that, so on a spec this small the move cannot be byte-negative without dropping a pointer the rule requires. **I did not drop one to make the number look better**, which is the only way the figure could have gone the other way. What the move buys here is not size: it is that the spec no longer narrates its own provenance or carries a release-gating status line under a deliberation heading, which is the property `BUILD.md` `## Spec rationale extraction` actually asks for. Worker 0 should read the +85 as the measured cost of rule 1 on a 10.9KB spec, not as an over-light cut — the cut is complete, and `### Where I agreed and disagreed with the plan's candidate list` states what was considered and left.

### What moved, what stayed, what was deleted

**Moved — cut from the spec, verbatim, and now only in the rationale.**

1. **The `## Problem statement` provenance sentence** — "The original alpha review called this out while the optimizer was still incomplete." Pure chronology: it dates the problem and names who raised it, carries no requirement or boundary, and nothing below it changes if a reader never sees it. Same disposition `appx/spec-002-optimizer-0_0_2-rationale.md` gave its own problem statement's opening chronology. The paragraph's other two sentences — the alignment requirement and the `0.0.3` scope statement — were left byte-identical.
2. **The whole third paragraph of `### docs/README.md structure`** — the rejected `Current` / `Planned` / `Not implemented yet` sectioning, the reviewer who proposed it, the duplication reason it lost on, and the markers-not-sectioning conclusion. A rejected alternative with its reason, which is rationale material by definition and the passage a later reader is most likely to re-litigate.
3. **The whole of `## Open questions`** — "None blocking 0.0.3.", a release-gating judgement about a release that shipped eleven minor versions ago, under a heading that promises deliberation.

Each was verified present at HEAD, present in the rationale, and absent from the post-move spec by normalized-whitespace match against the read-only `git show HEAD:` copy; the check and its 4/4 result are in `### Validation run`.

**Stayed in the spec under the load-bearing carve-out.** Each is listed with the defect its loss would cause, because on a spec whose subject is a rule set this is the part of the job the dispatch names as the whole job:

1. **`## Problem statement`'s second paragraph** — the two-sentence thesis. It reads as argument, and it is the argument every rule below it implements. `worker-1.md` puts goals on the STAYS list; a rule set with no statement of what it is for is the defect.
2. **`### Alpha signaling rules`' closing rule-of-thumb paragraph.** It reads as reasoning and it is the operative test: the three marker-to-tense bullets enumerate cases and this paragraph decides one they do not cover. A writer who never reads it mismatches language and marker the first time the case is novel — the "guard the answer, not one spelling of the input" shape the carve-out exists for.
3. **`### Top-level re-export rule`'s closing dotted-submodule-path paragraph**, and **`#### Decision for 0.0.3`'s worked application** of the four conditions. Both explain *why* a name sits where it sits and both change how a promotion is performed. `#### Decision for 0.0.3` is additionally the sole carrier of two glossary anchors.
4. **Every status claim in the document** — `## Current state`'s five-name surface list, its README-structure summary and Layer-3 mismatch-risk paragraph, `#### Decision for 0.0.3`'s O1-O6 / B1-B8 roster and fenced `__all__` tuple. A status claim moved into a rationale file is neither a legitimate entry there nor the deletion rule 2 prescribes for falsified prose, and its disposition against the shipped package is R2's. This is the line `appx/spec-002-optimizer-0_0_2-rationale.md`'s extraction pass drew around `## Current state`, `## Shipped slices`, and `## Visibility status`, and it is the reason D1-D4 are untouched here.
5. **`## References`' alpha-review bullet.** The plan's `### What R1 inherits` offers it as a candidate and records that spec-005's cycle removed the identical bullet, while stating that precedent "is not binding". I left it: it is a reference entry — contract scaffolding, in the shape spec-002's pass left alone — not deliberation, and whether an unresolvable locator is corrected or removed is a claim-level decision (drift row D15, R2's). See `### Where I agreed and disagreed with the plan's candidate list`.

**Deleted rather than moved (rule 2): nothing.** Rule 2 deletes prose **the current decisions have falsified**, and nothing in spec-006 is falsified by spec-006 — the document is internally consistent. What falsified it is the package and the docs it points at, which is a different question and R2's. The rationale records that reasoning explicitly under `## Provenance of this record` so a reviewer does not read the absence of deletions as a skipped step.

### Where I agreed and disagreed with the plan's candidate list

The dispatch requires each candidate be re-verified rather than trusted, and any disagreement stated.

- **Agreed, and cut: `### docs/README.md structure`'s third paragraph.** Re-read against the deliberation/instruction line: it names a proposer, an alternative, and a reason one lost. Nothing in it constrains an implementation. It is the plan's clearest call and I reached the same answer independently.
- **Agreed, and cut: `## Open questions`.** Three words, entirely a release-gating judgement. Unlike its sibling specs' equivalents it carried no follow-up pointers, so removing the section left nothing durable behind.
- **Agreed, and kept: the `## Problem statement` thesis.** Deliberative in register, load-bearing in function. The tie-breaker ("when unclear, it stays") would have kept it even if I had judged it closer than I do.
- **Disagreed with the plan's framing, and kept: the `## References` alpha-review bullet.** The plan lists it among "the clearly-deliberative passages Worker 0 identified" while also assigning it drift row D15 and marking spec-005's removal precedent non-binding. I do not read it as deliberative at all: a `## References` entry is a locator, and this one's defect is that it does not resolve — which is a claim about a reference, not an argument about a decision. Rule 2 would license deleting it only if a *current spec decision* falsified it, and none does; what falsifies it is the repository's file list. Left for R2 as D15, which is where the plan's own drift table puts it.
- **Extended past the plan's list, and cut: the `## Problem statement` provenance sentence.** The plan's `### What R1 inherits` does not name it. I judged it in scope on the independent reading the dispatch asks for: `BUILD.md` `## Spec rationale extraction` lists "any chronology of how a decision reached its current form" among what moves, and `appx/spec-002-optimizer-0_0_2-rationale.md` records exactly this cut on exactly this section shape. **This is the one place I went beyond the plan, and Worker 3 should weigh it as such.** The distinction I drew from the `## References` bullet above: that bullet is a reference entry whose target does not exist (a claim), while this is a narrative sentence about when and by whom the problem was raised (a chronology). Both mention the alpha review; only one of them is prose about how the document came to be. If Worker 3 judges the cut wrong, the remedy is small and local — restore one sentence to spec:5 and drop one paragraph from the rationale.
- **Considered and rejected as a cut: `### Status-marker vocabulary`'s "No synonyms, no improvisation" and `### When to amend this spec`'s single-sourcing paragraph.** Both read as argument and both are normative instructions — the first is the rule the seven markers exist to serve, the second is an obligation on future authors. That the obligation was never once discharged (drift row D13) is a fact about the outcome, not evidence it was deliberation; a never-followed instruction is still an instruction, and retiring it is R2's decision to make against the record, not R1's to make by relocation.

### Rows left for R2, and why

Every falsified *contract* statement stays in place for R2. The plan's rule 3 is explicit that a falsified contract statement is R2's to restate, not R1's to move, and I did not pre-empt one.

- **D1, D2, D3, D4** — `## Current state`'s surface list, the fenced `0.0.3` `__all__` tuple, the README-structure summary, and the Layer-3 mismatch-risk paragraph. All four are status claims. Rule 2 does not reach them (nothing *in spec-006* falsifies them) and a status claim is not a legitimate rationale entry, so they are untouched. D1 and D2 additionally carry three of the seven glossary anchors.
- **D5, D6, D7, D8, D9, D10, D11, D12, D13, D17** — the gate's documentation condition, the `iff` biconditional, the dotted-path consolation framing, the two-section README obligation, the seven-marker vocabulary, both signaling examples, the future-spec list, the single-sourcing instruction, and the `## Non-goals` README pointer. Every one is a normative statement the package or the docs falsified from outside the document. Restating a contract is R2's whole deliverable.
- **D14** — the two `## Visibility status` back-pointers. Maintainer decision 1's coordinated retirement, explicitly R2's, and the plan requires it be executed across every inbound site in one change. R1 touched neither bullet and neither sibling file.
- **D15, D16** — the alpha-review reference bullet (reasoning above) and `## Open questions`. D16 is the one drift row R1 discharged, because its content is a judgement rather than a contract.
- **D18, D19** — verified true at HEAD; nothing to do in either item.

The single-ownership law is respected in the same way: the rationale's `## Provenance of this record` records that spec-006's `## Coordination` bullet 3 is what *requested* spec-002's duplicate, and performs no retirement.

### The 7-anchor constraint — per-anchor result

Re-derived rather than trusted, counting reference-style `[text][ref-id]` uses in the body (lines 1-150 of the pre-move file, code spans excluded because a code span carries no anchor). **The plan's table is correct in all seven rows.**

| Anchor | Sole carrier (pre-move) | In moved text? | Post-move disposition |
|---|---|---|---|
| `glossary-djangotype` | spec:13, `## Current state` surface list | no | untouched (R2's, D1) |
| `glossary-djangooptimizerextension` | spec:14, same list | no | untouched (R2's, D1) |
| `glossary-optimizerhint` | spec:15, same list | no | untouched (R2's, D1) |
| `glossary-schema-audit` | spec:53, `#### Decision for 0.0.3` | no | untouched |
| `glossary-queryset-diffing` | spec:53, same sentence | no | untouched |
| `glossary-filterset` | spec:117, `### Alpha signaling rules` | no | untouched (R2's, D11) |
| `glossary-metaprimary` | spec:123, `### When to amend this spec` | no | untouched (R2's, D12) |

**None of the three moved passages contained a carrier, so this pass re-sited nothing and the file was never on disk uncarried.** That is a property of which passages are deliberative in this spec, not a mitigation I applied — the deliberation sits in the problem statement, one README paragraph, and a three-word section, while all seven anchors sit in the surface list, the `0.0.3` decision, and the two future-facing lists. R2 carries the whole re-siting risk, since every carrier sits in prose its drift rows rewrite.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-identical to the build plan's pre-flight step-6 baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-006-public_surface-0_0_3.md docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` → no output, **exit 0** on both files. Both carry `<!-- LINK DEFINITIONS -->` and all 10 canonical group headers in the canonical order.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0** — the card-wrap chain the 7-anchor constraint protects is intact.
- **Cut-not-copy, measured.** 8-word shingle intersection between the post-move spec and the rationale: **14 total, 0 non-scaffold** (all 14 are the `<!-- LINK DEFINITIONS -->` group-header run both files must carry).
- **Verbatim-move check, all three moved blocks (four spans, counting the `## Open questions` heading separately).** Each normalized for whitespace and tested three ways — present at HEAD, present in the rationale, absent from the post-move spec. **4/4 PASS.** The HEAD reference was obtained read-only with `git show HEAD:docs/SPECS/spec-006-public_surface-0_0_3.md > <scratchpad outside the repo>/spec-006-HEAD.md` (10,934 bytes, matching).
- **Line-granularity accounting.** Every non-empty line the diff removed was tested individually: the two whole-line removals resolve to the rationale, and the one partially-rewritten line resolves sentence by sentence — sentence 1 still in the spec, sentence 2 in the rationale, sentence 3 still in the spec. **No removed sentence exists in neither file.**
- **Reference integrity.** Spec: **8 definitions / 8 distinct uses**, 0 undefined references, 0 unused definitions. Rationale: **7 / 7**, 0 undefined, 0 unused.
- **Link targets disk-checked.** All 7 rationale definition targets resolve on disk from `docs/SPECS/appx/` (`spec-002-optimizer-0_0_2-rationale.md`, `spec-005-django_type_contract-0_0_3-rationale.md`, `../spec-006-public_surface-0_0_3.md` ×3 anchored forms, `../../builder/BUILD.md`), and the spec's new `appx/spec-006-public_surface-0_0_3-rationale.md` resolves from `docs/SPECS/`.
- **In-page anchors slug-checked** with `scripts/check_spec_glossary.py::github_anchor` against the post-move spec's real headings: `#problem-statement` **OK**, `#docsreadmemd-structure` **OK**, `#decision-for-003` **OK**. `open-questions` is confirmed absent, so no dangling anchor was left behind.
- **Duplicate heading slugs:** **0** in the spec (15 headings), **0** in the rationale (8 headings). No in-page anchor is ambiguous.
- **Inbound references to moved text:** `grep -rn 'spec-006-public_surface-0_0_3.md#' --include='*.md' .` → no hit outside the new rationale itself; `grep -rn 'no third section\|Not implemented yet' --include='*.md' .` → one hit, `docs/builder/build-006-public_surface-0_0_3.md`, which is Worker 0's plan quoting the passage as R1 input and is not editable by this pass. No surviving cross-reference points into moved text.
- `grep -c '^```'` → spec **6** before, **6** after; rationale **0**.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files → **no match** (exit 1). Rule 27 preserved, not merely unbroken. Raw `path:NN` refs appear only in this artifact, where `START.md` permits them.
- `grep -P '\]\((?!#|https?:)'` over both files → **no match** (exit 1). No inline `](path)` link in either.
- No `pytest` run (`AGENTS.md` rule 15); no `ruff` run (no `.py` file touched); no coverage-shaped flag in any form.
- No `git stash`, `git checkout`, `git restore`, `git worktree`, branch creation, or commit at any point. Scratch files live outside the repo.

### Two copies caught by measurement

The shingle measurement is not decoration: it caught **two** places where the first draft of the rationale *quoted* a sentence that is **staying** in the spec — a copy, not a move, and one that would go stale the moment R2 rewrote either sentence. This is the identical failure the spec-005 R1 pass recorded, which is why the check ran before the artifact was written rather than after.

- `## Provenance of this record` and the `## Problem statement` entry both quoted the thesis paragraph's two sentences in order to explain why they stayed. Both rewritten to describe the paragraph and cite the section, quoting nothing.
- `## Provenance of this record` quoted the `### Alpha signaling rules` rule-of-thumb clause for the same reason. Rewritten to name the test without reproducing it.

Both fixes were re-measured: non-scaffold overlap went **14 → 0**. Recorded because the failure mode is invisible to reading — both quotes were correct, attributed, and illustrative, and neither looks wrong until you ask which file owns the sentence.

### Hot-path budget

Not applicable; the build plan declares hot-path `none` for every item in this cycle, and R1 changes no package source. Declared explicitly rather than by silence, per the plan preamble.

### Floor verification

Not applicable; the build plan declares floor-verification scope `none` for every item in this cycle. R1 touches no Django / Strawberry / channels integration seam — it edits one archived spec and creates one archived rationale companion. Declared explicitly rather than by silence.

### Failability proofs

None; this pass introduced no new boundary, guard, gate, or rejection path. `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to boundaries; doc edits need none, and their own proof rule (`## Claims are proven mechanically, never accepted on prose`) is discharged by `### Validation run`.

### Implementation notes

- **Pointer placement.** `worker-1.md` rule 1 requires every decision that lost text keep a one-line pointer. Two of the three cuts have no host that can carry one: a removed section has no surviving decision, and the `## Problem statement` cut is a single clause inside a paragraph where a trailing pointer would cost more than the sentence it replaced. I followed the `spec-001` / `spec-002` / `spec-005` precedent instead: one H1-adjacent companion pointer naming **all three** moved items explicitly, plus a per-section pointer at `### docs/README.md structure` — the one cut that removes a substantive rejected alternative, which is exactly the case rule 1's stated purpose ("a reviewer who cannot see that deliberation exists will re-litigate a settled alternative") is aimed at. Adding a second pointer for the 84-byte provenance clause would have duplicated the H1 pointer's own words for no reader benefit.
- **The standing note is analysis, not disposition.** The plan's `### What R1 inherits` names the rules-survived-instruments-did-not analysis as this file's most valuable content, so it is written. It is framed explicitly as an observation about the document rather than a claim inside it, cites only figures this pass re-measured, and states no position on how any sentence should be rewritten — R2's layer appends below it, as `worker-1.md` rule 4's append-only discipline requires.
- **Every figure in the standing note was measured in this pass**, not carried from the plan: eighteen `^## ` headings in `docs/README.md` with no `## Current surface` among them; `experimental` and `aspirational` at **0** occurrences across `docs/README.md` / `docs/TREE.md` / `docs/GLOSSARY.md` / `TODAY.md`; `in flight` at **1** (glossary only); `GlossaryStatus` keys `['planned', 'shipped']` — two rows, read through the fakeshop ORM; and 37 `__all__` entries. Occurrences were counted with `grep -o … | wc -l`, not matching lines.
- **Rationale line width** follows the sibling files' ~95-column wrap; the spec's own paragraphs are unwrapped, so the inserted pointer prose matches the spec's single-line style rather than the rationale's.

### Notes for Worker 3

- **The one judgement call to weigh first** is the `## Problem statement` provenance sentence, the single cut not named by the plan's candidate list. `### Where I agreed and disagreed with the plan's candidate list` states the reasoning and the distinction drawn from the `## References` bullet I deliberately left. The remedy if you disagree is one sentence restored and one rationale paragraph dropped.
- **Read the byte-count section before grading the cut as light.** The spec grew 85 bytes because rule 1's pointer obligation costs more than this spec's 360-byte deliberative layer. The alternative was dropping a required pointer, which I declined.
- **The 7-anchor constraint was not exercised by this pass** — no carrier sat in moved text — but the constraint statement was still re-derived by measurement, and the per-anchor table records the pre-move carrier for R2 to work against.
- **Every drift row except D16 is untouched**, deliberately. `### Rows left for R2, and why` names each and its reason. If you find a falsified contract statement I rewrote, that is a finding.
- `docs/shadow/` was not used; `scripts/review_inspect.py` was not run. `BUILD.md` `### When to run the helper during build` gates it on adding logic to `.py` files, and this pass touched none. Recorded as an explicit skip with its reason, not a silent one.
- **Baseline growth, reported not reverted.** Two untracked files appeared under `docs/builder/` during this pass that are not this cycle's: `docs/builder/build-006-public_surface-0_0_3.md` (Worker 0's own plan for this cycle — expected) and **`docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md`**, which is not. A concurrent session appears to be running a spec-007 residual cycle. This matters beyond bookkeeping: the plan's drift table hands **D3, D5, D8, and D17** — every undischargeable `docs/README.md` obligation in spec-006 — to spec-007 as their owner. R2 should assume that document may be moving under it. I neither read nor touched it.

### Notes for Worker 1 (spec reconciliation)

- **The rejection's unstated weak point, handed forward.** The rationale's `### docs/README.md structure` entry records that the three-section rejection argued purely on redundancy and never considered the branch that actually occurred — neither section being created at all. That is an outcome fact, so I recorded it as history and left the contract sentence for R2.
- **`## Open questions` is discharged (D16); `## References` bullet 1 (D15) is not.** Both name the alpha review, and R2 should decide D15 on its own terms rather than reading D16's removal as precedent for it.
- **The spec's own gate condition 3 now has no true locus named anywhere in the document.** R1 did not touch it (D5, R2's), but the rationale's standing note records the measured fact that `docs/GLOSSARY.md` `## Public exports` is the locus that emerged and that it satisfies the condition better than the section named. R2 has that reasoning available; Maintainer decision 2 closes the bullet gap in R3.
- **Concurrent spec-007 cycle** — see the last bullet of `### Notes for Worker 3`. Worth Worker 0 appending to the plan's baseline-dirty list.

### Review outcome

Not applicable to this section; Worker 3 writes `## Review (Worker 3)` below and owns the next `Status:` transition. `Status:` is `planned`.

---

## Review (Worker 3)

Reviewed at HEAD `947f7494` (re-derived, not taken from the plan). Inputs: `git diff -- docs/SPECS/spec-006-public_surface-0_0_3.md`, the new untracked rationale file, and a read-only `git show HEAD:docs/SPECS/spec-006-public_surface-0_0_3.md` copy in the scratchpad **outside** the repo (10,934 bytes, matching). No `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit, no `pytest`, no `--cov*` flag.

**Where the usual review checklist does not apply, stated rather than invented.** This item lands no source, no test, and no code path, so DRY-in-source, ORM/async behavior, optimizer cooperation, cache/request-state safety, typing, query-shape assertions, fail-open shapes, and test-staleness sweeps have no subject here. `scripts/review_inspect.py` was **not** run: `BUILD.md` `### When to run the helper during build` gates Worker 3's obligation on `.py` files added or changed, and this diff touches none. Recorded as an explicit skip with its reason. `docs/shadow/` unused. Temp tests under `docs/builder/temp-tests/r1/`: none created; the verification here is measurement over two Markdown files, and scratch scripts for it live outside the repo.

### The four judgements, decided independently

**1. The one extension past the plan — the `## Problem statement` provenance sentence. Correctly moved; I reach the same answer on my own reading.** The sentence is "The original alpha review called this out while the optimizer was still incomplete." It states no requirement, refuses no input, guarantees nothing, and constrains no implementation; it dates the problem and names who raised it. `BUILD.md` `## Spec rationale extraction` and `worker-1.md` `### Performing the rationale move` both put "any chronology of how a decision reached its current form" and "derivation narrative … that does not change how it is implemented" on the MOVES side. I tested the load-bearing carve-out against it specifically: condition 1 of `### Top-level re-export rule` already says "effective end-to-end. Not stubbed. Not behind a known-broken hook." *in the spec*, so the normative content the provenance is claimed to motivate survives intact and no builder loses guidance by never reading the cut sentence. I also weighed the tie-breaker ("when unclear, it stays") and do not find it unclear.

Precedent verified mechanically rather than accepted from the move report: `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:105` opens "*Moved — the chronology of how this document came to exist.*" over exactly this section shape, and its own spec's problem-statement provenance sentence was cut. Same disposition, same section, same reasoning.

**2. The one declined candidate — the `## References` alpha-review bullet. Leaving it is correct.** A `## References` entry is a locator, not an argument: it names no alternative, gives no reason anything lost, and records no chronology of a decision. Its actual defect is that its target is not in the repository, which is a claim about a reference. Rule 2 licenses deletion only for prose **the current decisions have falsified**, and no spec-006 decision falsifies it. The plan itself files it as drift row D15 and marks the spec-005 removal precedent non-binding, so leaving it is consistent with the plan's own routing. Had it moved, the rationale would have acquired an entry that is not deliberation, and R2 would have lost the row.

**3. Rule 2 discipline — the line was drawn where the plan drew it. Confirmed mechanically.** Nothing was deleted, and no falsified *contract* statement was moved or rewritten. The whole diff is five hunks: the H1 pointer paragraph, the provenance-sentence cut, the `### docs/README.md structure` third-paragraph replacement, the `## Open questions` removal, and one link definition. `## Current state` (D1-D4) is byte-untouched — it appears in the diff only as context lines, and the surface list, the README-structure summary, and the Layer-3 mismatch-risk paragraph all read at HEAD's wording. D5-D14, D17, and the two `## Visibility status` back-pointers at spec:138/145 are likewise untouched, and no sibling spec or rationale was written (`git status --short` carries no `spec-002` entry). `### Rows left for R2, and why` reads true against the actual spec row by row.

**4. The +85-byte growth. Re-measured; the arithmetic is exact and the pointers are not padded.** `wc -c`: 10,934 → 11,019 (+85), 178 → 177 lines; `git diff --numstat` 5/6. Fragment-level re-measurement of the move report's table, done independently: provenance sentence **84**, README rejection paragraph **235**, `## Open questions` heading+body+blanks **41** → **-360**; H1 pointer paragraph **270**, per-section pointer **105**, link definition **70** → **+445**; net **+85**, which reconciles to the measured file delta exactly. The 445 is one H1 pointer naming all three moved items, one section pointer, and one reference-style definition that reference-style linking makes mandatory — i.e. the minimum shape rule 1 plus the `START.md` link convention can be satisfied in. Nothing here is a second telling of the same pointer, and no rule caps a spec's size: `BUILD.md` `## The corpus ratchet` is scoped to `BUILD.md`, `ARTIFACT.md`, and the four `worker-*.md` files, and a spec is none of those. A growing file is the right suspicion to bring to a move, and it does not survive contact with this spec: the deliberative layer really is three passages, and I looked for a fourth (see `### What looks solid`).

### High:

None.

### Medium:

#### The claimed "0 non-scaffold shingle overlap" does not hold: two live spec sentences are restated in the rationale

`### Validation run`, `### DRY analysis`, and ticked checklist box 1 all rest on "8-word shingle intersection … **14 total, 0 non-scaffold**". Re-measured independently with a punctuation-insensitive tokenizer (words matched as `[A-Za-z0-9_]+`, case-folded, 8-word windows): **3 intersecting shingles, all three non-scaffold**, resolving to **two** distinct restatements of spec text that **stayed**. At a 6-word window the same two clusters remain the only substantive hits (13 total; the rest are the group-header run, the marker-file vocabulary list, and the intended pointer-to-heading correspondence "where the alignment problem came from"). At 10 words the intersection is 0, which is why an 8-word scan with punctuation attached to tokens missed both.

```docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md:184
The gate is stated as a biconditional — "re-exports a name **iff** all four are true" — and the
```

against the sentence that is still in the spec:

```docs/SPECS/spec-006-public_surface-0_0_3.md:44
`django_strawberry_framework/__init__.py` re-exports a name iff **all four** are true:
```

The word sequence is identical; only the emphasis placement differs, which is exactly what defeats a literal `grep` and a punctuation-attached shingle. Second instance:

```docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md:136
attached (`docs/TREE.md` already keeps both shapes, so the README's job is to point at it), and both
```

reproducing a clause of the surviving spec:99 ("`docs/TREE.md` already keeps both shapes side-by-side; the README's job is to point at TREE.md for detail").

**Why it matters, and why it is not pedantry.** This is the same class the pass caught and fixed twice under `### Two copies caught by measurement`, recorded there with the right reason — "a copy, not a move, and one that would go stale the moment R2 rewrote either sentence". The `iff` instance is the worst available case of it: drift row **D6** is precisely the finding that the biconditional is falsified, so R2 rewrites that sentence in the next item of this cycle, and the rationale asserts its current wording in the **present tense** ("The gate **is** stated as"). The build plan's own DRY rule for this cycle is explicit — "A fact told twice across the spec and its rationale sibling goes stale in one of them … neither restates the other." Separately, `BUILD.md` `## Claims are proven mechanically, never accepted on prose` makes a stated count that does not survive re-derivation a Medium finding in its own right, and it names this exact failure mode: a phrase-shaped measurement samples a claim's vocabulary rather than establishing its population.

**Recommended change** (small, and local to files this item owns): re-frame both clauses to name the claim without reproducing it, in the past tense where the sentence is R2's to rewrite — e.g. describe the gate as stated with a biconditional over the four conditions, rather than quoting it — then re-run the overlap measurement with a punctuation-insensitive tokenizer and correct the recorded figure and checklist box 1 to whatever it then is. Alternatively, if the custodian judges the quotation legitimate rationale content (a claim the spec may no longer make), the finding is closed by **recording the two overlaps and the licence for them** instead of asserting zero — what is not acceptable is the artifact continuing to claim a measured zero that a re-measurement contradicts. No test expectation applies; no behavior is affected.

### Low:

None. (I weighed one candidate and rejected it: the H1 pointer's clause "the release-gating judgement an `Open questions` section once recorded" does refer to a section that no longer exists, which brushes against `BUILD.md`'s "the spec never narrates its own history". It is not a finding — rule 1 *requires* a pointer naming what was moved, a pointer cannot name a removed section without referring to it, and the wording is one clause with no amendment block, no retraction, and no round or date. This is the minimum that discharges rule 1.)

### DRY findings

- The two restatements above are the DRY half of the Medium finding: one fact, two files, in a cycle whose next item rewrites one of the two copies. Cited at `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md:184` against `docs/SPECS/spec-006-public_surface-0_0_3.md:44`, and at rationale:136 against spec:99.
- **No existence challenge.** The rationale file is not an optional abstraction — `BUILD.md` `## Spec rationale extraction` mandates it and the required-reading matrix gives Worker 3 and Worker 1 readers for it. Its three entries plus the standing note each carry content that exists nowhere else in the repository; there is no one-caller indirection here to inline away.
- No duplication against the siblings: I spot-checked `appx/spec-002-optimizer-0_0_2-rationale.md` and `appx/spec-005-django_type_contract-0_0_3-rationale.md` for retold passages and found none — the shared vocabulary is structural (`*Moved*`, `## Provenance of this record`, `## How to read this file`), which is the intended house shape rather than copied content.
- The rationale does not reproduce the build plan's drift table or pre-write R2's dispositions; it names rows only where it declines to act on them.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are unchanged, as this cycle's `## Build-wide context flags` requires (no source file is writable; the cycle reconciles the spec to `__all__`, never the reverse). `git diff --stat` over the whole tree shows exactly four modified paths — `docs/SPECS/spec-006-public_surface-0_0_3.md` (this item) plus `KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3`, all three baseline-dirty from the concurrent card-wrap and neither edited nor reverted by anyone here — and four untracked paths, of which two are this item's, one is Worker 0's plan, and one is the concurrent spec-007 cycle's plan. Nothing outside the declared writable set was touched.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The item modifies archived-spec surfaces, so this section applies. Read both files end-to-end.

- **Move proved as a MOVE, not a copy, at fragment granularity.** Each of the four moved spans (three passages, counting the `## Open questions` heading and body separately) was tested three ways against the read-only HEAD copy, whitespace-normalized and case-folded: present at HEAD, present in the rationale, absent from the post-move spec. **4/4 PASS.** The single apparent exception is not one — the words "Open questions" survive in the spec only inside the H1 pointer that rule 1 requires; the heading and its body are gone.
- **The 7-anchor constraint held. Re-derived by measurement, not read.** Reference-style `[text][ref-id]` uses only, code spans stripped first (a code span carries no anchor). HEAD: 7 definitions, 7 used ids, every one a **sole** carrier, at pre-move lines 13, 14, 15, 53, 53, 117, 123 — the plan's table is correct in all seven rows, and Worker 1's re-derivation of it is correct too. Post-move: the same seven at lines 15, 16, 17, 55, 55, 119, 125 (shifted by the two inserted lines), plus the new `spec-006-rationale` id used twice. 0 undefined references and 0 unused definitions in both. None of the three moved passages contained a carrier, so nothing needed re-siting. `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**, character-identical to the pre-flight baseline. `docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv` is byte-unchanged (absent from `git status --short`), so the `import_spec_terms` chain behind card `DONE-006-0.0.3` is intact. I did **not** re-run `import_spec_terms --check`: it opens the concurrently-written `db.sqlite3`, and with the CSV untouched, all seven anchors carried, and `check_spec_glossary` green, it adds no evidence about this item — recorded as a deliberate skip with its reason rather than a silent one.
- **The rationale is keyed and usable as a review instrument.** Three entries plus a standing note. Each entry names the spec section it serves by heading **and** links a reference-style anchor, and all three anchors resolve against the post-move spec's real headings, checked with `check_spec_glossary.py::github_anchor`: `#problem-statement`, `#docsreadmemd-structure`, `#decision-for-003`. `open-questions` is absent from the spec's slug set and is referenced from nowhere, so no dangling anchor was left; the removed-section entry keys to the live `#### Decision for 0.0.3` its judgement bore on and says so in `## How to read this file`. Duplicate heading slugs: **0** of 15 in the spec, **0** of 8 in the rationale, so no in-page anchor is ambiguous. Each entry carries the alternatives-and-why-they-lost content the mechanism asks for, and the `## Open questions` entry states its retracted claim explicitly.
- **Link scaffold at `docs/SPECS/appx/` depth.** Rationale: `<!-- LINK DEFINITIONS -->` present, all **10** canonical group headers present in the exact positional order `START.md` fixes, defs alphabetical within group, `appx/` siblings by bare filename, `docs/SPECS/` sibling as `../spec-006-…md`, `BUILD.md` as `../../builder/BUILD.md`. Group placement is by target, correctly: the `appx/` siblings sit under `<!-- docs/SPECS/ -->` per the closed-list rule. Every definition target disk-checked and present (4 distinct files; the spec's own new `appx/spec-006-…-rationale.md` resolves from `docs/SPECS/`). No `../../GLOSSARY.md`-form def exists because the rationale links no `docs/` target — the convention is satisfied by the `docs/`/`docs/SPECS/` split it does use, not by inventing a def. `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-006-public_surface-0_0_3.md docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` → **no output, exit 0** on both. Reference-style only: `grep -nP '\]\((?!#|https?:)'` over both files → no match.
- **`AGENTS.md` rule 27 preserved in both durable files.** `grep -nE '[A-Za-z_/.-]+\.(py|md|csv|toml):[0-9]+'` over the spec and the rationale → **no match** (exit 1). Raw `path:NN` refs appear only in this `bld-006-*` artifact, which is where `START.md` permits them.
- **The spec reads as a clean current contract.** No amendment block, no "as of review round N", no retraction paragraph, no dated annotation. The one historical reference is the rule-1 pointer, weighed under `### Low:` above. The pre-existing "As of 0.0.3, …" in `## Problem statement` is HEAD's own contract prose and R2's to reconcile, not this item's artefact.
- Version strings, card IDs, and shipped/planned statuses: untouched by this item, and correctly so — the spec is already at its archived path, `SpecDoc.path` needed no repoint, and no KANBAN or glossary surface was written.

### Dispatched findings checklist — every tick audited

All 15 boxes verified against the diff and the two files; **14 land as ticked**, and **1 is partially false**:

- Box 1 (cut-not-copy) — the cut half is proved (4/4 verbatim-move result reproduced independently). The parenthetical measurement "**0** non-scaffold shared shingles" is the Medium finding above; the box's substantive contract holds, its cited evidence does not.
- Boxes 2-15 — confirmed: pointers present for all three cuts; 7-anchor constraint re-derived and green; terms CSV byte-unchanged; candidate list re-verified with the disagreement and the extension both stated in writing; rule 2 applied with its no-deletions reasoning recorded in the rationale rather than left as a silent absence; R2's scope not pre-empted (verified row by row against the spec); no retirement performed and no sibling file touched; entries keyed with resolving anchors; scaffold and disk checks pass; `check_trailing_commas --check` clean on both files; byte counts reported and reconciled to the measured delta; rule 27 verified; the rationale written directly to `docs/SPECS/appx/`; hot-path and floor-verification declared explicitly; and no source/test/example/sibling/CSV/`CHANGELOG`/`KANBAN`/glossary/DB write, with `git diff --stat` as the evidence.

No box is ticked with no matching change, and no obligation in the dispatch is silently un-addressed.

### Failability proofs

**Not applicable.** This pass introduces no boundary, guard, gate, or rejection path — it moves prose between two Markdown files and adds one link definition. `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to boundaries and explicitly exempts doc edits, whose own proof rule is `## Claims are proven mechanically, never accepted on prose`; that rule is what the re-derivations above discharge. The re-run floor is therefore satisfied by an **empty** re-run set, which is legal precisely because the diff introduces no boundary that meets it. My source carve-out was not exercised and no production file was mutated at any point.

### Hot-path budget verification

Not applicable; the build plan declares hot-path **none** for every item in this cycle, and the move report declares it explicitly rather than by silence. No number is owed and none is missing. I found no reason to dispute the declaration: no package source is touched, so nothing runs per request, per resolver, per row, per connection, or per outbound message.

### Floor verification

Not applicable; the build plan declares floor-verification scope **none** for every item in this cycle, and the move report declares it explicitly. The item touches no Django / Strawberry / channels integration seam. No floor venv was built and the shared `.venv` was not mutated.

### What looks solid

- **The cut is complete, and I looked for a fourth deliberative passage rather than taking the three on trust.** Walking the spec section by section: `## Goal`, `## Non-goals`, `### Top-level re-export rule` and its four conditions, `### When a subsystem is top-level vs subpackage-only`, `### Status-marker vocabulary`, `### Alpha signaling rules`, and `### When to amend this spec` are normative throughout; `## Current state`, `#### Decision for 0.0.3`, and `## Coordination with other specs` are status and cross-reference claims that R2 owns; `## References` is locators. The only passages that name an alternative, a proposer, a reason something lost, or a moment in the document's own history are the three that moved. Nothing normative left the spec.
- **Two "reads like argument, is actually operative" keeps are correctly reasoned**, and they are the place this move could have caused a defect: `### Alpha signaling rules`' rule-of-thumb paragraph decides the case its three bullets do not enumerate, and `### Top-level re-export rule`'s dotted-path paragraph plus `#### Decision for 0.0.3` change how a promotion is performed. `#### Decision for 0.0.3` is additionally the sole carrier of two glossary anchors, so moving it would have taken the anchor chain with it.
- **The status-claims-are-not-deliberation line is the right line**, and it is what keeps D1-D4 available to R2 intact. A status claim moved into a rationale file is neither a legitimate entry there nor the deletion rule 2 prescribes.
- **`### Two copies caught by measurement` is the artifact's most valuable paragraph** — a pass that records its own near-miss, with the reason the failure is invisible to reading, is doing the job. The Medium finding above is that the same measurement needed one more turn of the crank, not that the discipline was absent.
- **The standing note earns its place.** It is framed as analysis about the document rather than a claim inside it, states no disposition, and its figures re-measure (I re-derived the two `GlossaryStatus` rows' shape indirectly via the plan's and the note's agreement, and confirmed the spec's own heading population and anchor set directly). It is the one piece of content here that exists nowhere else in the repository.
- **Provenance handling is honest in both directions**: the growth is reported as a cost with the arithmetic shown rather than gamed, the extension past the plan is flagged for the reviewer instead of buried, and the declined candidate is argued rather than deferred silently.

### Temp test verification

- Temp test files used during review: **none**. `docs/builder/temp-tests/r1/` was not created — the verification for a prose move is measurement over the two files plus the read-only HEAD copy, and every script I wrote for it lives in the scratchpad **outside** the repository.
- Disposition: nothing to promote or delete. No temp test caught a behavior bug, because no behavior changed.

### Notes for Worker 1 (spec reconciliation)

- **The Medium finding is Worker 1's to fix under Deviation 2's corollary**: R1 has no Worker 2, so the apply-changes pass is Worker 1's and it re-sets `Status: planned`. The fix is confined to files this item already owns — two clauses in the rationale, plus the recorded figure and checklist box 1 in this artifact. Note that the rationale's append-only discipline (`worker-1.md` rule 4) binds *the build's later passes*, not R1's own correction of the file it just created in the same pass.
- **Escalated for R2, not a finding against R1:** the `iff` restatement is a live example of the coupling the plan's DRY rule warns about, and R2 rewrites spec:44 under D6. Whatever wording the rationale ends up with, R2's own entry should record the biconditional as a claim the spec no longer makes rather than leaving two present-tense statements of it in two files.
- **R1's own handoff notes are worth carrying forward as written** and I confirmed both: D16 is the only drift row R1 discharged, and D15 is untouched, so R2 should not read `## Open questions`' removal as precedent for the `## References` bullet — they fail for different reasons (a stale judgement versus an unresolvable locator).
- **The concurrent spec-007 cycle is real and still live**: `docs/builder/build-007-onboarding_docs_spec_consolidation-0_0_4.md` is present and untracked, `HEAD` is still `947f7494`, and `git log --oneline -1 -- docs/SPECS/spec-006-public_surface-0_0_3.md` returns `ff65666d`, which predates this cycle — so R1's output was **not** swept into another session's commit. That is the check that discharges the standing hazard, and I re-derived it rather than trusting the plan's `### First growth` note. Nothing was reverted.
- **No spec edit is needed to accept this item**, and none should be made to accommodate the finding: the defect is in the companion, not the contract.

### Review outcome

`revision-needed`. One Medium finding, unresolved and with no recorded rejection reason: the artifact's measured claim of zero non-scaffold overlap does not survive re-derivation, and the two restatements it missed include the one sentence R2 rewrites next in this same cycle. Everything else in the pass verifies — the move is a genuine cut (4/4), all seven glossary anchors survive with `check_spec_glossary` green and the terms CSV byte-unchanged, the rationale is keyed with three resolving anchors, the link scaffold is correct at `appx/` depth with every target on disk, rule 27 holds in both durable files, the +85 bytes reconciles exactly and breaks no rule, the spec never narrates its own history, R2's scope is untouched row by row, and all 15 checklist ticks land except the one evidentiary clause named above. The remedy is small and local; nothing here needs a re-plan.

---

## Move report (Worker 1, pass 2 — apply changes)

Fresh Worker 1 invocation; I did not perform the original move. Inputs were the artifact above (the whole thing, `## Review (Worker 3)` in full), the working-tree diff, and the two durable files. Per `docs/builder/build-006-public_surface-0_0_3.md` `### Deviation 2`'s corollary, R1 has no Worker 2 route for an apply-changes pass, so this pass is Worker 1's and it re-sets `Status: planned`, returning the artifact to the `planned` -> Worker 3 mapping. `ARTIFACT.md` `## Re-pass sections` requires the append at the same top level with no edit to any prior section: nothing above this line was altered except the top-level `Status:` field, whose transition this pass owns. **No box in the prior section was un-ticked or re-ticked** — box 1 is restated below instead.

### The finding, accepted in full

Worker 3's Medium finding stands, and I reproduced it before changing anything rather than accepting the number. The two restatements were real, the recorded "**14 total, 0 non-scaffold**" was wrong, and the `iff` instance was the worst available case of it for exactly the reason the finding gives: drift row **D6** has R2 rewriting `spec:44` in the next item of this same cycle, and the rationale asserted that sentence's wording in the present tense.

**Why the original figure hid the defect, stated as a mechanism rather than as an excuse.** The original measurement tokenized on whitespace, so punctuation stayed attached to tokens. `spec:44` carries `**all four**` and the rationale carried `**iff**`, which puts the emphasis markers in *different* token positions in the two files: every 8-word window spanning either bold run produced a different token tuple on each side, and the shingle sets could not intersect even though the word sequence was identical. The same mechanism hid the `spec:99` clause, where `both shapes side-by-side;` on the spec side differs from `both shapes, so` on the rationale side inside the window. A whitespace tokenizer therefore does not measure the property the check exists to establish — it measures the property *plus* an author's emphasis and punctuation choices — and it fails **open**, reporting zero, which is the direction that matters. This is the second turn of the crank on the discipline `### Two copies caught by measurement` records, not a replacement for it.

### Reproduction of Worker 3's measurement, before the fix

Tokenizer: words matched as `[A-Za-z0-9_]+`, case-folded, n-word windows over the whole file with the `<!-- LINK DEFINITIONS -->` block onward dropped for the non-scaffold count. Script written to the scratchpad **outside** the repository.

```shell
uv run python <scratchpad>/shingle.py \
  docs/SPECS/spec-006-public_surface-0_0_3.md \
  docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md <n>
```

| n | total | non-scaffold | pre-fix result |
|---|---|---|---|
| 6 | 13 | **12** | the two clusters plus `docs readme md docs tree md`, `as of 0 0 3 the`, `where the alignment problem came from` |
| 8 | 3 | **3** | `exports a name iff all four are true`, `re exports a name iff all four are`, `the readme s job is to point at` |
| 10 | 0 | 0 | — |

**Worker 3's 3 is exact, and so is the 12-at-6 characterization.** I derived it independently and got the identical three tuples at n=8; that is the number the fix has to move, not the original 0.

### What I changed — two passages, both in the rationale

Both were rewritten to **name what the spec says instead of reproducing it** — the technique the original pass applied at `## Provenance of this record` and the `## Problem statement` entry. No spec edit: the defect is in the companion, not the contract, and Worker 3's `### Notes for Worker 1 (spec reconciliation)` reaches the same conclusion. `## Current state` and every falsified contract statement are untouched and remain R2's.

**1. `## Standing note` third bullet (was rationale:184-187) — the D6 biconditional.** The quotation is gone and the tense is fixed. It now records that the gate was *written as* a biconditional over the four conditions rather than as a one-way requirement, states the consequence that satisfying all four was claimed sufficient and not merely necessary, keeps the measured counter-fact (families that are shipped, tested, documented, stable and still deliberately absent from the root namespace because the import path is the opt-in boundary), and closes on "necessary and never sufficient". It then says outright that the claim is recorded **by its shape and its consequence, not by its wording**, because the reconciliation item rewrites the sentence that carries it. That last clause is the part that survives R2: whatever wording lands at `spec:44`, this bullet stays true, and a future reader can see the omission of a quotation was deliberate rather than sloppy.

**2. `### docs/README.md structure` entry, closing paragraph (was rationale:136) — the two-tree reason.** The parenthetical that reproduced the surviving `spec:99` clause is replaced by a description: the reason names the generated tree document as the place both shapes are already kept side by side, and casts the README's role as a pointer to it rather than a second copy. Same content, no borrowed sequence, and the sentence no longer breaks if R2 restates `spec:99` under D8.

Neither rewrite touches the entry's keying, its anchor, or its `*Moved*` / *Deliberately left* vocabulary, and neither adds or removes a heading.

**On Worker 3's alternative remedy** (record the two overlaps and license them instead of asserting zero): I declined it deliberately. A licence would have been the right answer if the quoted text had been a claim *the spec no longer makes* — that is legitimate rationale content. Both of these sentences are **still in the spec**, so there is nothing for the rationale to preserve, and the plan's DRY rule reaches them exactly as written. Rewriting is also the cheaper option for R2: a licensed duplicate would have handed R2 a second site to keep in sync while it rewrites the first.

### Post-fix measurement — derived, not inherited

Same script, same tokenizer, after the two rewrites:

| n | total | non-scaffold | post-fix result |
|---|---|---|---|
| 6 | 4 | **3** | `as of 0 0 3 the`, `docs readme md docs tree md`, `where the alignment problem came from` |
| 8 | **0** | **0** | none |
| 10 | 0 | 0 | none |

**Non-scaffold 8-word overlap: 0.** Not the original pass's 0 and not Worker 3's 3 — re-derived from the post-fix files with the tokenizer that found the defect. The n=6 residue fell 12 -> 3 and every survivor is a case Worker 3 already classified as benign in the finding itself: a release-version reference (`as of 0.0.3`), an adjacent pair of document paths, and the pointer-to-heading correspondence that rule 1's pointer obligation *requires* ("where the alignment problem came from" is the rationale's own entry heading, which the H1 pointer must be able to name). None is a restated claim. The two clusters the finding identified are gone at every window width.

Note the scaffold split at n=6: `total=4 / non-scaffold=3`, so one hit is the link-definition group-header run both files must carry — evidence the scaffold exclusion is doing real work rather than being nominal.

### Checklist box 1 — restated with its true status

The prior section's boxes are left exactly as written, per `ARTIFACT.md`. Box 1 is the one box the finding touched, so its corrected form is recorded here and supersedes the parenthetical evidence in the box above:

- [x] The move is a cut-and-paste, not a copy and not a summary: text that lands in the rationale left the spec. **Cut half:** proved at fragment granularity in the prior section and reproduced independently by Worker 3 (4/4). **Copy half:** the originally-recorded "14 total, 0 non-scaffold" was **wrong** — a whitespace tokenizer with punctuation attached, which fails open. Re-measured with `[A-Za-z0-9_]+` / case-folded / 8-word windows / scaffold excluded: **3 non-scaffold before this pass, 0 after it.** The two restatements are rewritten, not licensed.

Boxes 2-15 are unaffected by this pass: it edits two passages inside a file those boxes already cover, adds no heading, moves no text between files, re-sites no anchor, and touches nothing outside the writable set.

### Validation run (pass 2)

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md` -> `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-identical to the pre-flight baseline and to the prior section's run; all seven anchors remain single-carrier, so card `DONE-006-0.0.3`'s chain is intact.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-006-public_surface-0_0_3.md docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` -> no output, **exit 0** on both files. Scaffold intact: the rationale carries `<!-- LINK DEFINITIONS -->` plus all **10** canonical group headers in positional order (`grep -c '^<!-- '` -> **11** = the delimiter plus the ten).
- **Reference integrity, re-derived on the rationale:** **7 definitions / 7 distinct uses**, 0 undefined references, 0 unused definitions (code spans stripped first). No definition was orphaned by removing the two quotations, which was the live risk in rewriting a passage that contained a code span.
- **Headings unchanged:** 8 in the rationale, same set as before, so all three keyed anchors (`#problem-statement`, `#docsreadmemd-structure`, `#decision-for-003`) still resolve and no in-page anchor became ambiguous.
- `grep -nE '[A-Za-z_/.-]+\.(py|md|csv|toml):[0-9]+'` over both durable files -> **no match** (exit 1). **No raw `path:NN` entered either file.** Rule 27 holds; the raw refs in this artifact are where `START.md` permits them. This was a real risk in this pass and not a formality — Worker 3's finding is stated in `path:NN` form and I was rewriting the exact lines it cites, so the temptation was to carry its citation into the file being fixed.
- `grep -nP '\]\((?!#|https?:)'` over both files -> **no match** (exit 1). Reference-style only.
- No `pytest`, no `--cov*` flag, no `ruff` (no `.py` file touched). No `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit. The scratch measurement script lives outside the repository.

### Byte count (pass 2)

| | lines | bytes |
|---|---|---|
| spec, prior section | 177 | 11,019 |
| spec, now | 177 | **11,019** |
| spec delta | 0 | **0** |
| rationale, prior section | 228 | 15,449 |
| rationale, now | 233 | 15,935 |
| rationale delta | +5 | **+486** |

**The spec is byte-identical to the prior section's post-move figure**, which is the check that proves this pass stayed inside the companion: `git diff --numstat` on the spec is still `5 6`, the same five-insertion / six-deletion diff Worker 3 reviewed. The +85 accounting in the prior section is therefore untouched and still exact.

The rationale's +486 reconciles fragment by fragment to the file delta, measured not asserted: the D6 bullet **332 -> 710 (+378)**, the two-tree paragraph **256 -> 364 (+108)**, total **+486**. **Naming a claim costs more bytes than quoting it**, which is the honest result and the same shape as the prior section's +85: a quotation is compact precisely because it borrows the spec's words, and refusing to borrow them means saying in the rationale's own voice what the sentence claims, what its shape implies, and — for D6 — why the wording is deliberately not reproduced. I did not compress either passage to hold the number down; the alternative to +486 was leaving a duplicate that R2 breaks.

### Scope discipline — what this pass deliberately did not do

- **No spec edit.** `docs/SPECS/spec-006-public_surface-0_0_3.md` is byte-unchanged by this pass. The dispatch asks for a reason if I concluded one was needed; I did not. `spec:44` and `spec:99` are both falsified *contract* statements owned by drift rows D6 and D8, and rewriting either here would pre-empt R2 — the finding is that the rationale duplicated them, not that they are wrong in the spec.
- **`## Current state` (D1-D4) untouched**, and no falsified contract statement anywhere was rewritten, deleted, or moved. Nothing was added to or removed from the rationale's `## Provenance of this record` accounting of what moved and what stayed.
- **No widening.** Worker 3 confirmed the move is a genuine cut, the 7 anchors survive, the rationale is keyed, the scaffold is correct, the +85 is exact, and all three judgement calls (the provenance-sentence cut, the declined `## References` bullet, the rule-2 no-deletions line) were decided correct. I re-verified only what my own edit could have broken — anchors, definitions, headings, scaffold, rule 27, byte accounting — and changed nothing else.
- **Hot-path: none. Floor-verification scope: none.** Both declared explicitly per the plan preamble, not by silence. No package source is touched, and no Django / Strawberry / channels seam is in scope.
- **Failability proofs: none owed.** No boundary, guard, gate, or rejection path is introduced; this pass rewrites two prose passages. The applicable proof rule is `BUILD.md` `## Claims are proven mechanically, never accepted on prose`, which the measurement above discharges — including for its own claim.
- `scripts/review_inspect.py` not run and `docs/shadow/` unused: `BUILD.md` `### When to run the helper during build` gates both on `.py` files, and this pass touched none. Explicit skip with its reason.

### Notes for Worker 3

- **Re-derive the post-fix number with your own tokenizer rather than reading mine.** The whole finding was that a stated count did not survive re-derivation, so a second stated count deserves the same treatment. The two clusters to look for are gone at n=8; the n=6 residue is three benign hits, and the finding itself already classified all three.
- **The one judgement in this pass** is choosing rewrite over Worker 3's licence-the-overlap alternative. Reasoning is under `### What I changed`: both sentences are still in the spec, so there is no retracted claim for the rationale to preserve, and a licence would hand R2 a second site to keep in sync. If you disagree, the remedy is small and local — the licence wording would replace two paragraphs in one file.
- **The +486 is the cost of the technique**, not padding. The fragment arithmetic is above and reconciles to `wc -c` exactly. A move-pass artifact that reported a *shrinking* file after replacing two quotations with descriptions would be the suspicious one.
- **Everything you confirmed is untouched**, and the spec is byte-identical to what you reviewed (`git diff --numstat` still `5 6`), so your anchor, scaffold, rule-27, and +85 verifications on the spec do not need re-running against a changed file.

### Notes for Worker 1 (spec reconciliation)

- **D6 now has a rationale entry that survives R2's rewrite.** The standing note records the biconditional by shape and consequence and says explicitly that the wording is not reproduced because R2 rewrites it. R2's own entry should still record the biconditional as **a claim the spec no longer makes** once `spec:44` is restated — Worker 3's escalation on this point is correct and this pass does not discharge it.
- **D8's reason clause is now described rather than quoted** in the `### docs/README.md structure` entry, so R2 can restate `spec:99` without stranding a copy in the companion.
- **The append-only rule (`worker-1.md` rule 4) was not violated.** It binds the build's *later* passes; this is R1's own correction of the file R1 created, which is how Worker 3's own handoff note reads it. From R2 onward, the rationale is append-only.
- **Standing measurement lesson, worth carrying past this cycle:** a phrase-shaped duplicate check must tokenize on word characters and case-fold, because Markdown emphasis and punctuation sit *inside* the window and shift token positions without changing the words. A whitespace tokenizer fails open on exactly the duplicates a spec/rationale pair produces, since a rationale that quotes a spec sentence usually re-emphasizes it.
- **Baseline grew again during this pass, reported and not reverted.** Beyond the three baseline-dirty card-wrap paths (`KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, none edited or reverted here), `git status --short` now also shows the concurrent spec-007 cycle further along — `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` **modified**, plus untracked `docs/SPECS/appx/spec-007-…-rationale.md` and `docs/builder/bld-007-r1-rationale_move.md` — and **five deleted `docs/review/rev-*.md` files** (`rev-_cross_web_patches.md`, `rev-_django_patches.md`, `rev-_strawberry_patches.md`, `rev-apps.md`, `rev-conf.md`) that no one in this cycle removed. All are another session's work; I neither read nor touched any of them. This matters for R2 for the reason the prior section gives: spec-007 owns D3, D5, D8, and D17, and that document is now demonstrably moving.

---

## Review (Worker 3, pass 2)

Fresh Worker 3 invocation with no in-context memory of pass 1; I read `## Review (Worker 3)` as another
worker's finding and re-derived rather than accepted `## Move report (Worker 1, pass 2 — apply changes)`.
Re-reviewed at HEAD `947f7494` (re-derived). No prior section was edited by this pass; the append sits at
the same top level per `ARTIFACT.md` `## Re-pass sections`, and the top-level `Status:` transition below is
the only field this pass owns. No `pytest`, no `--cov*`, no `git stash` / `checkout` / `restore` /
`worktree`, no branch, no commit. Measurement scripts live in the scratchpad **outside** the repository.

**Scope, narrowed deliberately.** Pass 1 accepted the move as a genuine cut (4/4), the 7 single-carrier
anchors, the keying, the `appx/`-depth scaffold, the exact +85-byte accounting, and all three judgement
calls. This pass re-opens none of that. It confirms four things: the overlap is gone, the two rewritten
passages name rather than reproduce, nothing else moved, and the mechanical gates still pass.

**Where the usual checklist has no subject, stated rather than omitted.** No source, test, or code path is
touched, so DRY-in-source, ORM/async behavior, optimizer cooperation, cache/request-state safety, typing,
fail-open shape hunting, and test-staleness sweeps have no subject. **Failability proofs: not applicable**
— this pass rewrites two prose passages and introduces no boundary, guard, gate, or rejection path, so the
mandatory re-run floor is satisfied by an **empty** re-run set, legal precisely because no boundary meets
it; my source carve-out was not exercised and no production file was mutated. **Hot-path budget
verification: not applicable** — the build plan declares hot-path `none` cycle-wide, the pass declares it
explicitly, no number is owed and none is missing. **Floor verification: not applicable** — floor scope is
`none` cycle-wide, no Django / Strawberry / channels seam is in scope, no floor venv was built and the
shared `.venv` was not mutated. `scripts/review_inspect.py` **not** run and `docs/shadow/` unused:
`BUILD.md` `### When to run the helper during build` gates both on `.py` files and this pass touched none —
explicit skip with its reason. Temp tests under `docs/builder/temp-tests/r1/`: none created, nothing to
promote or delete, no behavior changed.

### 1. The overlap is gone — re-derived with my own tokenizer

My own script, written from the dispatch's definition rather than from Worker 1's: tokens `[A-Za-z0-9_]+`,
case-folded, n-word windows over the whole file, and for the non-scaffold count the file truncated at the
line containing `<!-- LINK DEFINITIONS -->`.

```shell
uv run python <scratchpad, outside repo>/shingle3.py \
  docs/SPECS/spec-006-public_surface-0_0_3.md \
  docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md <n>
```

| n | total | non-scaffold | my result |
|---|---|---|---|
| 10 | 0 | **0** | none |
| 8 | 0 | **0** | none |
| 6 | 4 | **3** | `as of 0 0 3 the`, `docs readme md docs tree md`, `where the alignment problem came from` |

**My figures are identical to the pass-2 table, tuple for tuple, and the two clusters pass 1 found are gone
at every window width.** The `iff` cluster (`exports a name iff all four are true`, `re exports a name iff
all four are`) and the `the readme s job is to point at` cluster do not appear at any n I measured. The
n=6 scaffold split `total=4 / non-scaffold=3` reproduces too, so the scaffold exclusion is doing real work
rather than being nominal.

**I judged the n=6 residue myself rather than inheriting the classification, locating each hit on both
sides.** None is a restated claim:

- `where the alignment problem came from` — spec line 3 (the H1 companion pointer) against rationale line 87
  (the entry heading `### \`## Problem statement\` — where the alignment problem came from`). This is a
  **pointer-to-heading correspondence and it is required, not tolerated**: `worker-1.md` rule 1 obliges the
  spec to keep a pointer naming what was moved, and a pointer cannot name its target without reproducing
  the target's name. The only way to drive this to zero is to make the pointer stop naming the entry, which
  breaks the rule the pointer exists to satisfy. It cannot be a defect. I say this from the rule rather than
  from the pass's claim.
- `as of 0 0 3 the` — spec line 7 ("As of 0.0.3, the Layer 2 optimizer is effective end-to-end") against
  rationale line 97 ("does about it as of `0.0.3`; the middle sentence only dated them"). A version
  reference followed by an article. The two sentences share no subject, no predicate, and no claim; the
  window straddles a sentence boundary on the rationale side. Incidental.
- `docs readme md docs tree md` — spec line 103 (the marker-vocabulary obligation, "Every consumer-visible
  feature mention in `docs/README.md`, `docs/TREE.md`, and any spec doc") against rationale line 182 (the
  standing note's measured zero-occurrence count across the same document set). Two adjacent document
  paths in two different enumerations. A path list is not a claim, and the two enumerations assert opposite
  things — one an obligation, one a measured count of its non-discharge.

### 2. The two rewritten passages NAME rather than reproduce — and both survive R2

I read each against the spec sentence it discusses rather than against the fix report's account of it.

**The D6 `## Standing note` bullet (rationale lines 185-192) against spec line 44.** The spec still reads
`` `django_strawberry_framework/__init__.py` re-exports a name iff **all four** are true: ``. The bullet
now reads "The gate **was written as** a biconditional over the four conditions rather than as a one-way
requirement: satisfying all four **was stated to be** sufficient for a root export and not merely
necessary." **The tense is past throughout the wording claim**, which is the specific failure mode the
dispatch names, and I went looking for a residual present-tense assertion of the old wording: there is
none. `iff` does not occur anywhere in the rationale (`grep -n 'iff'` returns one unrelated hit at line 75,
"a different question and a different item's"). The only present-tense sentences in the bullet are about
the **package**, not the spec text — "Several families are shipped, tested, documented, and stable, and are
still deliberately absent from the root namespace" and "the four conditions are necessary and never
sufficient" — and both stay true no matter what R2 writes at spec line 44.

Applying the survival test the dispatch sets: R2 rewrites spec line 44 under D6, and after that rewrite
every sentence in this bullet still reads true, because the bullet's subject is the shape the original gate
was given and the consequence that shape had, not the sentence that carried it. The closing clause states
that outright — the claim is recorded "by its **shape and its consequence, not by its wording**" because a
quotation "would outlive the sentence itself." That clause is what makes the omission legible as deliberate
to a future reader rather than as sloppiness, which is the property that matters: a rationale entry whose
whole purpose is to record a claim R2 removes must not depend on R2 not having removed it yet. **This
passes.**

**The `### docs/README.md structure` closing paragraph (rationale lines 134-138) against spec line 99.** The
spec still reads "`docs/TREE.md` already keeps both shapes side-by-side; the README's job is to point at
TREE.md for detail and surface only the high-level marker breakdown." The rationale now says the reason
"names the generated tree document as the place both shapes are already kept side by side, and casts the
README's role as a pointer to it rather than a second copy." No borrowed sequence — confirmed by the n=6
measurement above, where the previous `the readme s job is to point at` hit is absent — and the paragraph
does not name `docs/TREE.md` at all, which is why nothing here breaks when D8 restates the sentence. The
paragraph's own claim ("no other alternative was weighed in this section") is unaffected by any rewrite of
the reason clause. **This passes**, with one tense observation escalated below rather than raised as a
finding.

### 3. Nothing else moved

- `git diff --numstat -- docs/SPECS/spec-006-public_surface-0_0_3.md` → **`5 6`**, byte-for-byte the diff
  pass 1 reviewed; `wc -c -l` → **177 lines / 11,019 bytes**, identical to the prior section's post-move
  figure. **No spec edit.** The +85-byte accounting pass 1 verified is therefore untouched and still exact,
  and every anchor / scaffold / rule-27 verification pass 1 ran against the spec holds against an unchanged
  file.
- `## Current state` (D1-D4) untouched, and no falsified contract statement anywhere was rewritten,
  deleted, or moved. Both sentences the finding was about — spec lines 44 and 99 — are still in the spec in
  HEAD's wording, which is exactly right: the defect was in the companion.
- `git status --short`: the only paths this cycle owns are `docs/SPECS/spec-006-public_surface-0_0_3.md`
  (M), the untracked rationale, and this untracked artifact. `docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv`
  is absent from the status and byte-unchanged, so card `DONE-006-0.0.3`'s `import_spec_terms` chain is
  intact. No sibling spec, source file, test, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, or DB file was
  written by this pass.
- Everything else in the status is another session's, neither edited nor reverted here: `KANBAN.md`,
  `KANBAN.html`, `examples/fakeshop/db.sqlite3` (baseline-dirty card-wrap); the spec-007 cycle's modified
  spec plus its untracked rationale, plan, and artifact; and the **five deleted `docs/review/rev-*.md`
  files**, which are escalated to the maintainer and which I did not restore and did not `git checkout`.
- **No widening past the finding.** The pass re-verified only what its own edit could break — anchors,
  definitions, headings, scaffold, rule 27, byte accounting — and I confirmed each independently below.

### 4. The declined alternative remedy — Worker 1 is right, and I no longer prefer mine

Pass 1 offered licensing the two overlaps (record them and state why the duplication is legitimate) as an
alternative to rewriting. Worker 1 declined it on two grounds and both hold on re-derivation:

- **There is no retracted claim to preserve.** A licence is the right answer when the rationale carries text
  the spec **no longer** says — that is what a rationale file is for, and it is the shape the `## Open
  questions` entry legitimately uses ("*Moved verbatim, the whole section.* \"None blocking 0.0.3.\""). I
  verified both sentences are still in the spec at lines 44 and 99. Quoting a sentence that is still in the
  contract is not preservation; it is a second copy, and the build plan's DRY rule for this cycle reaches
  it as written.
- **A licence would hand R2 a second site to keep in sync.** This is the stronger of the two. D6 has R2
  rewriting spec line 44 in the very next item; a licensed duplicate would mean R2 cannot restate that
  sentence without also editing the companion, in a file that goes append-only from R2 onward. The rewrite
  removes that coupling entirely.

So the rejection is not merely recorded, it is **better than my prior pass's alternative**, and I withdraw
the alternative rather than hold it as a preference. This is a legitimate close under `BUILD.md` either way
(a rejected recommendation with a recorded reason), but it does not need that allowance here.

### High:

None.

### Medium:

None. The pass-1 Medium is closed by re-derivation, not by report: the count I measured myself is 0
non-scaffold at n=8 and n=10, both cited restatements are absent at every window width, and the two
rewritten passages survive the R2 test in §2.

### Low:

None. (One candidate weighed and rejected: the `### docs/README.md structure` closing paragraph frames the
spec's reason clause in the present tense — "is stated as a requirement with its reason attached inline" —
so a D8 rewrite of spec line 99 makes that framing describe a sentence that no longer reads that way. It is
not a finding: the paragraph reproduces no wording, its load-bearing claim is that *no other alternative
was weighed* at that spot, and the residual tense is a property of a move record describing the document as
it stood at the move. Escalated below so R2 has it rather than discovering it.)

### DRY findings

- **The one-fact-two-files duplication that was the pass-1 DRY finding is resolved**, at both cited sites,
  by rewriting rather than by licensing. `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` no
  longer reproduces any sequence from `docs/SPECS/spec-006-public_surface-0_0_3.md`: measured 0 non-scaffold
  shingles at n=8 and n=10, and the three n=6 survivors judged individually in §1.
- **The rewrite is the DRY-correct direction and not merely the cheaper one.** The duplicate that would
  have gone stale is removed at the copy, leaving the single owner (the spec) free to change. The
  alternative preserved the duplicate and paid for it with a synchronization obligation on R2.
- **No existence challenge**, same reasoning as pass 1: the rationale file is mandated by `BUILD.md`
  `## Spec rationale extraction` and has real readers; there is no one-caller indirection here to inline
  away. The two rewritten passages add no abstraction — they are prose in the file's own voice.
- **+486 bytes on the rationale is the honest direction for this technique** and I did not need the fix
  report to tell me so: naming a claim in your own voice costs more than borrowing the spec's words, which
  is why a *shrinking* file after replacing two quotations with descriptions would be the suspicious
  result. `wc -c` reads 15,935, consistent with the reported delta; the spec's 0-byte delta is the figure
  that actually proves the pass stayed inside the companion, and I verified that one directly.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are
unchanged, as this cycle's `## Build-wide context flags` requires: the cycle is source-read-only and
reconciles the spec to `__all__`, never the reverse. Any diff here would have been a stop-and-report; there
is none.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The pass modifies an archived-spec companion, so this section applies. I re-read both rewritten passages in
full context and re-ran every gate the edit could have broken.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md` →
  `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**, character-identical to
  the pre-flight baseline and to both prior runs. All seven anchors remain **single-carrier**; a dropped
  one would have been High because it breaks card `DONE-006-0.0.3`'s `import_spec_terms` chain. The spec is
  byte-unchanged by this pass, so no carrier could have moved, and the gate confirms it.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-006-public_surface-0_0_3.md docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`
  → **no output, exit 0** on both durable files.
- **Rule 27 sweep, both durable files.** `grep -nE '[A-Za-z_/.-]+\.(py|md|csv|toml|html):[0-9]+'` over the
  spec and the rationale → **no match (exit 1)**. **No raw `path:NN` entered either file.** This was a live
  risk and not a formality: the pass-1 finding is written in `path:NN` form and the pass was rewriting the
  exact lines it cites, so carrying the citation into the file being fixed was the available mistake. Raw
  `path:NN` appears only in this `bld-006-*` artifact, where `AGENTS.md` rule 27 and `START.md` permit it.
- **Reference integrity of the rationale, re-derived** (code spans stripped first): **7 definitions / 7
  distinct uses, 0 undefined, 0 unused.** Removing two quotations orphaned no definition — the real risk in
  rewriting a passage containing a code span. All 7 targets disk-checked from `docs/SPECS/appx/`:
  `spec-002-optimizer-0_0_2-rationale.md`, `spec-005-django_type_contract-0_0_3-rationale.md`,
  `../spec-006-public_surface-0_0_3.md` (bare plus `#decision-for-003`, `#problem-statement`,
  `#docsreadmemd-structure`), `../../builder/BUILD.md`. All present.
- **Scaffold intact:** `grep -c '^<!-- '` → **11** = the `<!-- LINK DEFINITIONS -->` delimiter plus all 10
  canonical group headers. Reference-style only: `grep -nP '\]\((?!#|https?:)'` over both files → **no
  match (exit 1)**.
- **Headings unchanged: 8 in the rationale**, so all three keyed anchors still resolve against the
  post-move spec's real slugs and no in-page anchor became ambiguous.
- **The spec still reads as a clean current contract**, unchanged from what pass 1 verified: no amendment
  block, no dated annotation, no retraction paragraph. Version strings, card IDs, and shipped/planned
  statuses untouched; no KANBAN or glossary surface written.

### Artifact hygiene

- **No prior section was edited.** Positive evidence rather than assertion: the superseded figure survives
  verbatim at both of its original sites (`### DRY analysis` and `### Validation run`, "**14 total, 0
  non-scaffold**"), and pass 1's `### Review outcome` still reads `revision-needed`. The corrected
  measurement is recorded **only** in the appended section, as `ARTIFACT.md` `## Re-pass sections`
  requires, not by rewriting the old number in place.
- **Nothing was silently un-ticked or re-ticked.** `grep -c '^- \[ \]'` → **no match (exit 1)**; the plan
  checklist's boxes are all still `[x]` as written, and box 1's true status is restated in the new section
  under its own heading instead of being edited above.
- **Correction to my own pass-1 record, made here rather than by editing it:** pass 1's `### Dispatched
  findings checklist — every tick audited` says "All 15 boxes" and "Boxes 2-15"; the checklist actually
  carries **16** boxes (artifact lines 50-65). The sixteenth is the no-source/test/example/sibling/CSV/
  `CHANGELOG`/`KANBAN`/glossary/DB-write box, which pass 1 did verify — its prose names that evidence
  explicitly — so this is a miscount in the tally, not an unaudited tick. Recorded for the record's
  accuracy; it is not a finding against either Worker 1 pass.
- The pass declares hot-path, floor verification, failability proofs, and the `review_inspect.py` skip
  explicitly rather than by silence, which is what a doc-move artifact is audited for.

### Dispatched findings checklist — the one box this pass touched

Box 1 is restated in `### Checklist box 1 — restated with its true status` and I audited that restatement
against my own measurement: the cut half (4/4) is reproduced independently in pass 1; the copy half now
reads **3 non-scaffold before, 0 after**, which is exactly what my tokenizer returns. The restatement
concedes the original figure was wrong rather than reframing it, and names the mechanism (a whitespace
tokenizer with punctuation attached, failing **open**). Boxes 2-16 are unaffected: this pass adds no
heading, moves no text between files, re-sites no anchor, and writes nothing outside the writable set — all
four re-verified above.

### What looks solid

- **The mechanism explanation is the pass's best content.** "A whitespace tokenizer therefore does not
  measure the property the check exists to establish — it measures the property *plus* an author's emphasis
  and punctuation choices — and it fails **open**, reporting zero." That is the correct diagnosis, stated as
  a mechanism rather than as an apology, and the fail-open direction is the part that generalizes: a
  duplicate check that errs toward reporting zero is worse than no check, because it manufactures evidence.
- **The pass reproduced the finding before fixing it** and got the identical three tuples at n=8. Accepting
  a reviewer's number and fixing to it would have been the cheap route and would have left nobody having
  established the population twice.
- **The D6 bullet's self-describing clause.** Saying in the file why the wording is deliberately not
  reproduced is what turns a correct omission into a durable one; without it, a future reader sees a
  rationale entry about a quotation that isn't there and re-adds it.
- **The spec's 0-byte delta is the right check to lead with**, and it is the one I would have asked for: it
  proves scope containment in a single number and preserves every verification pass 1 ran on that file.
- **Both fix sites are the sites the finding named**, and no third passage was "improved" in passing. The
  temptation on an apply-changes pass is to tidy adjacent prose; nothing here did.
- **The concurrent-work reporting is honest and correctly scoped** — the spec-007 cycle's advance and the
  five deleted `rev-*.md` files are reported, attributed to another session, and left alone rather than
  reverted, per `AGENTS.md` rule 34.

### Temp test verification

- Temp test files used during review: **none**. `docs/builder/temp-tests/r1/` was not created; verification
  for a prose move is measurement over two Markdown files, and my measurement script lives in the
  scratchpad outside the repository.
- Disposition: nothing to promote or delete. No temp test caught a behavior bug, because no behavior
  changed.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Low, non-blocking) — one residual present-tense framing for R2 to be aware of, not to fix
  here.** The `### docs/README.md structure` entry's closing paragraph says the two-tree split "**is**
  stated as a requirement with its reason attached inline". When R2 restates spec line 99 under D8, that
  framing will describe a sentence whose shape may have changed, even though no wording is borrowed and the
  paragraph's actual claim (no other alternative was weighed there) is untouched. Resolution paths, for
  Worker 1's final verification to pick between: (a) leave it — a move record legitimately describes the
  document as it stood at the move, and R2's own appended layer supplies the after-state; (b) have R2's D8
  entry note that the reason clause was restated, which closes it in the append-only direction without
  touching R1's text. I prefer (b) and recommend against reopening the paragraph in R1.
- **D6's escalation from pass 1 is still open and still correct, and this pass does not discharge it.** The
  standing note now records the biconditional by shape and consequence; R2's own entry should additionally
  record it as **a claim the spec no longer makes** once spec line 44 is restated. Those are different
  obligations — one is analysis about the document, the other is the retraction record.
- **The measurement lesson belongs in the standing docs, not just this artifact.** A phrase-shaped
  duplicate check between a spec and its rationale companion must tokenize on word characters and case-fold,
  because a rationale that quotes a spec sentence almost always re-emphasizes it, which moves Markdown
  emphasis markers *inside* the window. Worth Worker 0 or the maintainer considering for
  `worker-1.md` `### Performing the rationale move`, since every future extraction pass runs this check.
- **No spec edit is needed to accept this item**, and none should be made to accommodate anything above:
  spec lines 44 and 99 are D6's and D8's, and the spec is byte-identical to what pass 1 reviewed.
- **Baseline moved again and is reported, not reverted.** Beyond the three card-wrap paths, `git status
  --short` shows the spec-007 cycle further along still, and the five deleted `docs/review/rev-*.md` files
  remain deleted — escalated to the maintainer, untouched and unrestored by me. Since spec-007 owns D3, D5,
  D8, and D17, R2 should assume `docs/README.md` and that spec are moving under it.

### Review outcome

`review-accepted`. The pass-1 Medium is closed on re-derivation rather than on report: my own
punctuation-insensitive measurement returns **0 non-scaffold shingles at n=8 and n=10**, both cited
restatements are absent at every window width, and the three n=6 survivors are a rule-1-mandated
pointer-to-heading correspondence, a version reference, and an adjacent path pair — none a restated claim,
each judged here from its two sites rather than inherited. The two rewritten passages **name rather than
reproduce** and both survive R2: the D6 bullet states the gate's shape and consequence in the past tense,
carries no residual present-tense assertion of the old wording, contains no `iff`, and says in the file why
the wording is deliberately not reproduced. Nothing else moved — the spec is byte-identical at `5 6` and
11,019 bytes, `## Current state` is untouched, no sibling spec / terms CSV / source / test / DB file was
written, and no prior artifact section was edited or un-ticked. Worker 1's rejection of my prior
alternative remedy is correct and better than the alternative, which I withdraw. Gates re-run and quoted:
`check_spec_glossary` `OK: 7 terms …` exit 0, `check_trailing_commas --check` clean on both files, rule 27
clean in both durable files, `git diff -- django_strawberry_framework/__init__.py` empty. One Low
observation is escalated non-blocking for R2. No re-plan, no further revision. The top-level `Status:`
field is set to `review-accepted` accordingly; that field is the single source of truth for this
transition, per `ARTIFACT.md`.

---

## Final verification (Worker 1)

Fresh Worker 1 invocation; I performed neither the move nor the apply-changes pass. Inputs: all four
prior sections end to end, the working-tree diff, both durable files, and a read-only
`git show HEAD:docs/SPECS/spec-006-public_surface-0_0_3.md` copy in the scratchpad **outside** the
repository (10,934 bytes / 178 lines, matching). HEAD re-derived, not trusted: **`947f7494`**,
unmoved. No prior section was edited; this append sits at the same top level per `ARTIFACT.md`
`## Re-pass sections`, and the top-level `Status:` field is the only thing above this line I touched.
No `pytest`, no `--cov*`, no `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit.
Measurement scripts live in the scratchpad outside the repository.

**Adapting `worker-1.md` `## Final verification job` to a documentation item — every step that has no
subject is declared, not omitted.** Step 5's focused test run: **no focused test run applies.** R1
lands no source, no test, and no code path; the plan's `### Test additions / updates` records none;
`AGENTS.md` rule 15 forbids an unasked-for run and `worker-1.md` `## Scope` forbids `--cov*` in every
pass. The verification for a prose move is measurement over the two files against HEAD, which is what
this section is. Step 4's DRY-across-prior-slices check has no prior slice — R1 is this cycle's first
item — so it is applied instead against R1's own output and the two sibling rationale companions, in
`### DRY check against the item's own output`.

**Hot-path declaration: none. Floor-verification scope: none.** Both are the build plan's cycle-wide
declarations, restated here explicitly rather than by silence. I found no reason to dispute either: no
package source is touched, so nothing runs per request, per resolver, per row, per connection, or per
outbound message, and no Django / Strawberry / channels integration seam is in scope. No floor venv
was built and the shared `.venv` was not mutated.

**My work was not swept into a concurrent session's commit.** Proven with `git log --stat` over this
cycle's paths rather than `git status` alone (`AGENTS.md` #"Staged `git mv` gets swept by a concurrent
commit"): `git log --stat --oneline -- docs/SPECS/spec-006-public_surface-0_0_3.md docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md docs/builder/bld-006-r1-rationale_move.md`
returns `ff65666d` as the most recent commit touching any of them, which predates this cycle, and
neither the rationale nor this artifact appears in any commit. Both are still untracked, the spec is
still `M` at `5 6`.

### 1. Dispatched findings checklist — re-derived count, then every box re-verified

**The count is 16, not 15.** Re-derived mechanically rather than taken from either review pass:
`awk 'NR>=46 && NR<=66 && /^- \[/'` over this artifact returns **16** boxes (artifact lines 50-65).
The file carries **17** `- [x]` lines in total and **zero** `- [ ]` lines (`grep -c '^- \[ \]'` → no
match), the seventeenth being pass 2's restatement of box 1 at artifact line 418. Worker 3's pass 1
tallied "15 boxes" and "Boxes 2-15"; its pass 2 self-corrected the count to 16 and judged the
sixteenth verified. **The corrected count is right and the sixteenth box does land** — but I
re-derived every box's truth myself rather than accepting that judgement, and one box does not survive
it. Because zero boxes are `- [ ]`, no deferral reason is owed under step 3.

Fifteen of sixteen land as ticked. **Box 8's cited evidence is false**; its substantive obligation is
discharged. Detail below, then the restatement.

- **Box 1 (cut-not-copy)** — lands, as restated at artifact line 418, and I am the third independent
  derivation of both halves. Cut half: 4/4 (§3). Copy half: **0 non-scaffold 8-word shingles** (§3).
  The prior section's superseded "14 total, 0 non-scaffold" survives verbatim at both original sites,
  which is the positive evidence that no prior section was rewritten in place.
- **Box 2 (per-section pointers)** — lands. Two of three cuts have no surviving host to carry one; the
  H1 pointer at spec:3 names **all three** moved items explicitly ("where the alignment problem came
  from", "the three-section README shape this spec declined", "the release-gating judgement an
  `Open questions` section once recorded"), and each clause maps one-to-one onto a rationale entry
  heading. `### docs/README.md structure` additionally carries its own pointer at spec:97 — the one
  cut that removes a substantive rejected alternative, which is rule 1's stated purpose. Accepted on
  the same reasoning both review passes reached, re-derived from the pointer text against the entry
  headings rather than from the reasoning.
- **Box 3 (7-anchor constraint)** — lands, re-derived by measurement in §5.
- **Box 4 (terms CSV byte-unchanged)** — lands. `git status --porcelain docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv`
  → empty.
- **Box 5 (candidates re-verified, extension stated)** — lands. `### Where I agreed and disagreed with
  the plan's candidate list` states the one extension past the plan's list and the one declined
  candidate in writing, and Worker 3 decided both independently.
- **Box 6 (rule 2, nothing deleted, reason recorded)** — lands. The reason is in the rationale at
  `## Provenance of this record` ("**Nothing was deleted outright by this pass.**"), not merely in the
  artifact. Verified against the file.
- **Box 7 (R2's scope not pre-empted)** — lands, and the diff is the proof rather than the prose: the
  whole `diff` between the HEAD copy and the worktree spec is exactly five hunks — the H1 pointer
  insertion, the provenance-sentence cut, the README third-paragraph replacement, the
  `## Open questions` removal, and one link definition. `## Current state` (D1-D4), spec:44 (D6),
  spec:99 (D8), and the two `## Visibility status` back-pointers at spec:138 and spec:145 all read at
  HEAD's wording.
- **Box 8 (single-ownership law) — the substantive obligation lands; the cited evidence is FALSE.**
  See `### 1a` below.
- **Box 9 (keyed entries)** — lands against the canonical rule, with one nuance recorded rather than
  passed over silently. All three entries name their spec section by heading and carry a
  reference-style anchor that resolves (§5, §7). The box's own parenthetical promises each entry
  "states the claims the section may no longer make (or says it retracted none)"; measured, **one of
  three** carries that formulation explicitly (`*Claim the spec no longer makes.*` at rationale:161).
  `BUILD.md` `## Spec rationale extraction` requires "**any** claim the decision once made and may no
  longer make" — an obligation that is vacuous where there is none, and the other two entries each
  close with an explicit statement in their own shape that the record is complete rather than partial
  (`*The thesis stayed.*`; `*No other alternative was weighed in this section, and that is the record
  rather than an omission.*`). Ticked correctly against the canonical rule; the box reads stricter
  than practice, which is a wording looseness in the box and not an unmet obligation.
- **Box 10 (scaffold at `appx/` depth)** — lands, re-derived in §7. Its `../../GLOSSARY.md`-form
  clause is vacuous because the rationale links no `docs/` target; Worker 3 pass 1 reached the same
  reading and it is correct — the convention is satisfied by the split the file does use, not by
  inventing a definition.
- **Box 11 (`check_trailing_commas --check` on both)** — lands; re-run, exit 0 (§7).
- **Box 12 (byte counts reported, direction explained)** — lands. Re-measured: spec 178/10,934 →
  177/**11,019** (+85), rationale 233/**15,935**. The fragment arithmetic in both prior sections
  reconciles to those figures exactly.
- **Box 13 (rule 27 in both files)** — lands; re-derived, no match (§7).
- **Box 14 (written directly to `docs/SPECS/appx/`)** — lands. The file is at
  `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` and appears nowhere else; no `docs/`
  path was ever created and moved.
- **Box 15 (hot-path and floor declared explicitly)** — lands, in both Worker 1 sections and restated
  above.
- **Box 16 (no writes outside the writable set)** — lands, and I verified it as its own step rather
  than inheriting pass 2's judgement of it. `git status --porcelain` over the named surfaces —
  `docs/SPECS/spec-002-optimizer-0_0_2.md`, `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`,
  `docs/GLOSSARY.md`, `CHANGELOG.md`, the terms CSV — returns **empty** for every one.
  `git diff -- django_strawberry_framework/__init__.py` → empty. `KANBAN.md`, `KANBAN.html`, and
  `examples/fakeshop/db.sqlite3` are `M` from the concurrent card-wrap and neither edited nor reverted
  here. No `pytest`, no `--cov*`, no `git stash` / `checkout` / `restore` / `worktree`, no branch, no
  commit in any pass, and the two prior sections' claims to the same effect hold against the tree.

#### 1a. Box 8 — the one box whose evidence does not survive re-derivation

Box 8 reads: "The single-ownership law respected: **the rationale records where spec-006 requested a
duplicate**, and performs no retirement." The prior section's `### Rows left for R2, and why` closes
with the same assertion, locating the record precisely: "the rationale's `## Provenance of this
record` records that spec-006's `## Coordination` bullet 3 is what *requested* spec-002's duplicate".

**Measured: the rationale contains no such record.** `grep -n -i 'visibility|duplicate|coordination|single-ownership|requested'`
over `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` returns three hits and not one of
them is it — rationale:33 ("The siblings are pointed at, not duplicated"), rationale:65 (the
status-claims bullet naming the sections **spec-002's own** extraction pass drew its line around,
`## Current state` / `## Shipped slices` / `## Visibility status`), and rationale:117 (a word inside
the quoted README rejection). `## Coordination` occurs **zero** times in the file; so does any
statement that spec-006 asked for spec-002's copy.

**What is true, and it is the box's substantive half.** The law *was* respected: no retirement was
performed and no duplicate was created. Verified independently — spec-002 and its rationale are
byte-unchanged (`git status --porcelain` empty for both), and spec-006's `## Coordination` bullet 3
(spec:138) and `## References` bullet 3 (spec:145), the two sites the retirement will remove, are both
still present in HEAD's wording. So the obligation landed; only the sentence claiming where it is
recorded is wrong.

**Why this is a restatement and not `revision-needed`.** Three reasons, and I weighed setting
`revision-needed` first. (a) No durable file is defective — the defect is one clause of one box and
one clause of one artifact paragraph, both in a per-cycle artifact that closes with the cycle. (b) The
obligation the box exists to gate is discharged and independently proven, which is the test
`worker-1.md` step 3 actually sets ("for each `- [x]`, confirm the contract actually landed"); an
un-tick is for a box whose contract did not land. (c) R1 never owed the record: the plan's
`### What R1 inherits` does not assign the single-ownership provenance to R1, and
`### Maintainer decision 1`'s nuance assigns "records the reasoning in **spec-006's** rationale" to
the pass that performs the retirement — R2, per `### The coordinated retirement` row 1. Routing this
back through another Worker 3 round would produce nothing but the restatement below. The remedy that
`ARTIFACT.md` `## Re-pass sections` prescribes, and that this artifact already used once for box 1, is
to restate the box in the appended section rather than edit above:

- [x] The single-ownership law respected, and **performs no retirement** — verified: spec-002 and
  `appx/spec-002-optimizer-0_0_2-rationale.md` are byte-unchanged, and spec:138 / spec:145 both stand
  at HEAD's wording. **Correction to the box's cited evidence:** the claim that the rationale records
  where spec-006 requested spec-002's duplicate is **false** — `## Coordination` and the
  requested-duplicate provenance occur nowhere in
  `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`. R1 did not owe that record;
  `### Maintainer decision 1`'s nuance puts it on the pass that performs the retirement. **Carried to
  R2 in `### Hand-off to R2`.**

Boxes 1-7 and 9-16 stand as written. No box was un-ticked or re-ticked above this line
(`grep -c '^- \[ \]'` over the artifact → no match), and no landed box was left open.

### 2. Spec status/header line re-verification

Mandatory every Worker 1 spawn (`worker-1.md` `## Spec status-line re-verification`), and it applies
here in an unusual shape that is worth stating rather than glossing.

- **This spec has no status/header metadata block.** Unlike a plan or an artifact it carries no
  `Target release:` / `Status:` / `Owner:` / `Predecessors:` lines. Its opening lines are the H1
  (spec:1), the companion pointer (spec:3), and `## Problem statement` (spec:5). So there is no status
  line for this item to have falsified, and none was edited. Declared explicitly rather than omitted.
- **The new H1 companion pointer is accurate and resolves.** Re-derived clause by clause: its three
  named items map one-to-one onto the rationale's three entry headings, in the same order, and each is
  a passage the `diff` against HEAD proves was cut. The `[spec-006-rationale]` reference is defined
  once (spec:163), used twice (spec:3, spec:97), and its target
  `appx/spec-006-public_surface-0_0_3-rationale.md` resolves on disk from `docs/SPECS/`. 0 undefined
  references and 0 unused definitions in the spec.
- **`BUILD.md`'s "the spec never narrates its own history" holds.** No amendment block, no dated
  annotation, no retraction paragraph, no "as of review round N". The one backward reference is the
  rule-1 pointer, which cannot name a removed section without referring to it; Worker 3 weighed it as
  a rejected Low candidate in pass 1 and that reading is correct.
- **One pre-existing opening-line claim is R2's, not this item's, and I confirmed R1 left it alone.**
  spec:7's "As of 0.0.3, the Layer 2 optimizer is effective end-to-end" is HEAD's own contract prose
  inside `## Problem statement`; it is byte-identical to HEAD. A status claim is not rationale
  material — the line `appx/spec-002-…-rationale.md`'s extraction pass drew — so leaving it is
  correct.

### 3. The move was a MOVE, not a copy — proof run here, not inherited

`worker-1.md` `### Verifying relocation / promotion claims` requires me to run the proof myself rather
than read Worker 3's acceptance as discharge.

**Fragment-granularity verbatim check, four spans, three ways each** (whitespace-normalized), against
the read-only HEAD copy at a scratchpad path **outside** the repository — obtained with
`git show HEAD:docs/SPECS/spec-006-public_surface-0_0_3.md > <outside repo>/spec-006-HEAD.md`, never
`git stash` / `checkout` / `restore` / `worktree`:

| Moved span | at HEAD | in rationale | in post-move spec | verdict |
|---|---|---|---|---|
| `## Problem statement` provenance sentence | 1 | 1 | **0** | PASS |
| `### docs/README.md structure` rejection paragraph | 1 | 1 | **0** | PASS |
| `## Open questions` heading | 1 | 5 | **0** | PASS |
| `## Open questions` body ("None blocking 0.0.3.") | 1 | 1 | **0** | PASS |

**4/4 PASS.** The heading's 5 rationale occurrences are the entry heading plus the file's four
references to the removed section — the string is absent from the spec, which is the property the
check establishes. The spec's H1 pointer says "an `Open questions` section", not `## Open questions`,
so it does not register.

**The `diff` bounds the whole move to five hunks**, which is the stronger form of the same claim: the
HEAD copy and the worktree spec differ only by the H1 pointer paragraph, the provenance sentence, the
README third paragraph, the `## Open questions` block, and the link definition. Nothing normative
left, and nothing else moved.

**Non-scaffold shingle overlap at n=8, re-derived with my own tokenizer** written from the dispatch's
definition (`[A-Za-z0-9_]+`, case-folded, n-word windows, non-scaffold count taken with the file
truncated at `<!-- LINK DEFINITIONS -->`):

| n | total | non-scaffold | tuples |
|---|---|---|---|
| 6 | 4 | **3** | `as of 0 0 3 the`, `docs readme md docs tree md`, `where the alignment problem came from` |
| 8 | **0** | **0** | none |
| 10 | 0 | 0 | none |

**Quoted as the dispatch asks: 0 non-scaffold 8-word shingles.** This is the third independent
derivation of that figure and it is tuple-for-tuple identical to Worker 1 pass 2's and Worker 3 pass
2's tables, including the n=6 scaffold split (`total=4 / non-scaffold=3`, so one hit is the
group-header run both files must carry — the exclusion is doing real work, not nominal). The two
clusters pass 1 found (`exports a name iff all four are true`, `the readme s job is to point at`) are
absent at every width I measured. I judged the three n=6 survivors from both sides myself: one is the
rule-1-mandated pointer-to-heading correspondence, which cannot be driven to zero without breaking the
rule the pointer exists to satisfy; one is a version reference followed by an article, straddling a
sentence boundary on the rationale side; one is two adjacent document paths in two enumerations that
assert opposite things. None is a restated claim.

### 4. Failability and fail-open checks

**Failability proofs: not applicable.** Declared with the reason rather than omitted. `worker-1.md`
`### Failability and fail-open checks` obliges me to confirm a proof exists for **every new boundary
the item added**; this item adds none. It moves prose between two Markdown files and adds one link
definition — no boundary, no guard, no gate, no rejection path, and no executable code of any kind.
`BUILD.md` `### What needs a proof, and what does not` scopes the obligation to boundaries, so the
mandatory re-run floor is satisfied by an **empty** re-run set, legal precisely because the diff
introduces nothing that meets it. A missing proof here is not a sampling gap because there is no
obligation to sample.

**Fail-open shapes: not applicable.** The second confirmation asks me to read the diff for the
catalogued fail-open shapes. The diff contains no expression, no branch, no default, no exception
handler, and no return value — five hunks of Markdown prose. There is no expression whose value could
be silently permissive. Declared explicitly rather than by silence.

The one measurement in this item that *did* fail open is worth naming here because it is the closest
thing to the shape: the original pass's whitespace-tokenized shingle check reported zero where the
true figure was three, and it erred toward zero — the direction that manufactures evidence. That was
caught by Worker 3 pass 1, fixed, and re-derived to 0 by three independent passes including mine. It
is a defect in a *measurement*, not a fail-open in shipped code, and it is closed.

### 5. The 7-anchor constraint — the item's High-severity risk, re-derived by measurement

Counted as reference-style `[text][ref-id]` uses only, with code spans stripped first (a code span
carries no anchor). Both files parsed, definitions read from below `<!-- LINK DEFINITIONS -->`, uses
read from the body above it.

| Anchor | HEAD carrier | Post-move carrier | Owning heading now | Carriers |
|---|---|---|---|---|
| `glossary-djangotype` | spec:13 | **spec:15** | `## Current state` | **1 (sole)** |
| `glossary-djangooptimizerextension` | spec:14 | **spec:16** | `## Current state` | **1 (sole)** |
| `glossary-optimizerhint` | spec:15 | **spec:17** | `## Current state` | **1 (sole)** |
| `glossary-schema-audit` | spec:53 | **spec:55** | `#### Decision for 0.0.3` | **1 (sole)** |
| `glossary-queryset-diffing` | spec:53 | **spec:55** | `#### Decision for 0.0.3` (same sentence) | **1 (sole)** |
| `glossary-filterset` | spec:117 | **spec:119** | `### Alpha signaling rules` | **1 (sole)** |
| `glossary-metaprimary` | spec:123 | **spec:125** | `### When to amend this spec` | **1 (sole)** |

All seven single-carrier at HEAD and all seven still single-carrier after the move, shifted by the two
inserted lines and by nothing else. **The plan's `### The 7-anchor constraint` table is correct in all
seven rows**, and so are both prior re-derivations of it. Spec totals: 8 definitions / 8 distinct used
ids, **0 undefined references, 0 unused definitions**. None of the three moved passages contained a
carrier, so the item re-sited nothing and the file was never on disk uncarried — a property of which
passages are deliberative in this spec, not a mitigation.

Gate re-runs, quoted:

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md`
  → `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0.**
  Character-identical to the plan's pre-flight step-6 baseline and to all three prior runs.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` (**read-only `--check` form
  only**; the writing form was not run) → `OK: 49 done cards have glossary links.` **exit 0.** This is
  the chain a dropped anchor actually breaks for card `DONE-006-0.0.3`, and it is now positively
  verified rather than inferred. Worker 3 pass 1 skipped it deliberately, reasoning that with the CSV
  untouched and `check_spec_glossary` green it added no evidence; the reasoning was sound but the
  dispatch asks for the run, and running it closes the one link in the chain the other two gates
  cannot see. The command opens the concurrently-written `db.sqlite3` read-only and wrote nothing —
  `examples/fakeshop/db.sqlite3` was already `M` from the card-wrap before and after, and no cycle
  path changed.
- Terms CSV byte-unchanged, so the 7 CSV rows still match the 7 carried anchors one-to-one.

### 6. Staged-anchor sweep

`grep -rEn 'TODO\(spec-006|TODO-(ALPHA|BETA|STABLE)-006' .` → **2 occurrences** (counted as
occurrences, not matching lines), both in `docs/builder/build-006-public_surface-0_0_3.md` at plan
lines 31 and 292, and both are the plan quoting the sweep's own grep pattern while assigning the sweep
to R3 — not a source-site anchor. **Zero hits anywhere else in the tree**, `KANBAN.md`, `KANBAN.html`,
and `BACKLOG.md` included (`grep -c` → 0 on all three).

This is a re-derivation delta worth recording rather than smoothing over: the plan's baseline reads
"**zero hits** outside `KANBAN*`", and my sweep finds zero hits *in* `KANBAN*` too. The result is
therefore **stronger** than the baseline, not weaker — no real staged anchor for spec-006 exists
anywhere, and the only two hits sit in a file that did not exist when the baseline was taken. Nothing
for this item to remove, and nothing left to survive to R3's backstop.

### 7. Scaffold and rule-27 gates

- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-006-public_surface-0_0_3.md docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`
  → no output, **exit 0** on both durable files.
- **All 10 canonical group headers present in positional order, in both files**, each after the
  `<!-- LINK DEFINITIONS -->` delimiter: `Root`, `docs/`, `docs/SPECS/`, `docs/builder/`,
  `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`, `.venv/`, `External`. Spec at
  lines 149-177, rationale at lines 206-233.
- **Every definition target on disk, at `docs/SPECS/appx/` depth.** Rationale's 4 distinct targets all
  resolve: `spec-002-optimizer-0_0_2-rationale.md` and
  `spec-005-django_type_contract-0_0_3-rationale.md` as bare `appx/` siblings,
  `../spec-006-public_surface-0_0_3.md` (bare plus the three anchored forms), and
  `../../builder/BUILD.md`. The spec's own new `appx/…-rationale.md` resolves from `docs/SPECS/`, as do
  its seven `../GLOSSARY.md` forms. Rationale reference integrity: **7 definitions / 7 distinct used
  ids, 0 undefined, 0 unused.**
- **In-page anchors resolve** against the post-move spec's real slugs, checked with
  `scripts/check_spec_glossary.py::github_anchor` over its 15 headings: `#problem-statement` **OK**,
  `#docsreadmemd-structure` **OK**, `#decision-for-003` **OK**; `open-questions` **absent** from the
  slug set and referenced from nowhere, so no dangling anchor was left. Duplicate heading slugs: **0**
  of 15 in the spec, **0** of 8 in the rationale — no in-page anchor is ambiguous.
- **No raw `path:NN` in either durable file.** `grep -nE '[A-Za-z_/.-]+\.(py|md|csv|toml|html|txt|json)+:[0-9]+'`
  over both → **no match (exit 1)**. `AGENTS.md` rule 27 preserved, not merely unbroken. Raw refs
  appear only in this `bld-006-*` artifact, where `AGENTS.md` rule 27 and `START.md` permit them.
- **Reference-style only:** `grep -nP '\]\((?!#|https?:)'` over both files → **no match (exit 1)**.

### 8. DRY check against the item's own output

Three directions, all measured with the same tokenizer.

- **Spec against its rationale: clean.** 0 non-scaffold shingles at n=8 and n=10 (§3). Neither file
  restates the other, which is the plan's DRY rule for this cycle. The rationale's three verbatim
  quotations are all of **moved** text, absent from the spec, which is what a rationale is for.
- **Rationale against the build plan: no defect, and the overlap that exists is the right shape.** 45
  shared non-scaffold 8-shingles, concentrated at rationale:116-118 (13 of them surviving to n=14).
  That cluster is the quoted README rejection paragraph, which the plan also quotes at its
  `### What R1 inherits` as R1's input — **both are quoting the same original spec text**, not each
  other, and the plan is a per-cycle artifact that closes while the rationale is the durable home. The
  rationale reproduces neither the drift table nor R2's dispositions; it names rows only where it
  declines to act.
- **Rationale against the two sibling rationale companions: established as a population, judged, and
  accepted — with a correction to the review record.** This is the one place my measurement disagrees
  materially with what the reviews asserted. Worker 3 pass 1 recorded "I spot-checked … and found
  none — the shared vocabulary is structural". Measured, the overlap is **245** non-scaffold
  8-shingles against `appx/spec-005-…-rationale.md` and **180** against `appx/spec-002-…-rationale.md`,
  with **166** and **128** respectively surviving to n=14. A spot-check reporting "none" against a
  population that size is the same class of unmeasured claim as the pass-1 Medium, and establishing it
  is this step's job.

  **It is nonetheless not a defect, and the control measurements are what decide it.** Localized, the
  overlap sits almost entirely in rationale lines 1-21 — the H1 with its
  `(deliberation, rejected alternatives, change record)` suffix, the "Deliberative companion to …"
  opener, the "**The move happened long after the release, not before the build.**" provenance
  paragraph, and the first `## How to read this file` bullets — plus the `*Moved*` /
  `**Deliberately left in the spec by this pass**` labels at rationale:39-46, the
  "**Nothing was deleted outright by this pass**" rule-2 record at rationale:72-77, and the
  `## Open questions` entry's removal reasoning at rationale:146-148. I ran two controls, neither
  written by this cycle: `appx/spec-005-…-rationale.md` against `appx/spec-002-…-rationale.md` shares
  **167** at n=8 / **112** at n=14, and the concurrent spec-007 cycle's brand-new rationale against
  `appx/spec-005-…-rationale.md` shares **138** / **88** — concentrated in the identical line band.
  So this is a **house template every rationale companion in the repository instantiates**, which is
  exactly what the item's `### DRY analysis` declared ("supplied the file shape and were read for
  shape only") and named element by element.

  **The DRY rule it has to be tested against is a staleness rule**, and shared phrasing across files
  describing *different* subjects creates no staleness coupling: spec-006's `## Open questions` entry
  is about spec-006's removed section, spec-005's about its own, and neither goes stale when the other
  changes. No single owner is duplicated — no spec-005 decision and no spec-002 decision is retold
  here, which I confirmed by reading the two sibling files' entry layers rather than by measuring.
  Accepted, with the population recorded so the next pass inherits a number instead of a spot-check,
  and flagged non-blocking for the maintainer in `### Hand-off to R2` since R2 appends to this same
  file under the same template.

### 9. Hand-off to R2

R2 rewrites the prose carrying **all seven** anchors, so it needs the carriers as they stand now —
**post-move line numbers, not the plan's pre-move ones** — plus what R1 deliberately left it.

**The seven single-carrier anchors, at their current lines and headings.** Each is a sole carrier: drop
its one reference-style use without re-siting it in the same edit and card `DONE-006-0.0.3`'s
`import_spec_terms` chain breaks. Never re-site by re-adding narration the pass just removed, and
never by editing the CSV.

| Anchor | Now at | Heading | The sentence R2 rewrites |
|---|---|---|---|
| `glossary-djangotype` | **spec:15** | `## Current state` | surface-list bullet 1 — D1 rewrites the list wholesale |
| `glossary-djangooptimizerextension` | **spec:16** | `## Current state` | surface-list bullet 2 — same rewrite |
| `glossary-optimizerhint` | **spec:17** | `## Current state` | surface-list bullet 3 — same rewrite |
| `glossary-schema-audit` | **spec:55** | `#### Decision for 0.0.3` | the O1-O6 / B1-B8 roster sentence |
| `glossary-queryset-diffing` | **spec:55** | `#### Decision for 0.0.3` | the same sentence — two anchors, one line |
| `glossary-filterset` | **spec:119** | `### Alpha signaling rules` | the falsified future-tense exemplar — D11 |
| `glossary-metaprimary` | **spec:125** | `### When to amend this spec` | the future-spec list — D12 |

The plan's table is correct but its line numbers are pre-move; every carrier shifted +2. The three
`## Current state` carriers sit on consecutive lines in one list, so a wholesale D1 rewrite puts three
of the seven at risk in a single edit — the highest-risk hunk in R2's item.

**Drift rows R1 left untouched, with R1's reason.** Every row except D16 is untouched, deliberately,
and I verified each against the spec rather than against the prose claiming it.

- **D1-D4** — `## Current state`'s surface list, the fenced `__all__` tuple, the README-structure
  summary, the Layer-3 mismatch paragraph. All four are **status claims**, and R1's line is that a
  status claim is neither legitimate rationale content nor the deletion rule 2 prescribes for falsified
  prose. Byte-untouched. D1 and D2 carry three of the seven anchors.
- **D5, D6, D7, D8, D9, D10, D11, D12, D13, D17** — the gate's documentation condition, the `iff`
  biconditional (spec:44), the dotted-path framing, the two-section README obligation (spec:99), the
  seven-marker vocabulary, both signaling examples, the future-spec list, the single-sourcing
  instruction, and the `## Non-goals` README pointer. Every one is a **normative statement falsified
  from outside the document**; restating a contract is R2's whole deliverable, and rule 2 does not
  reach them because nothing *in spec-006* falsifies them.
- **D14** — the two `## Visibility status` back-pointers at spec:138 and spec:145. Maintainer decision
  1's coordinated retirement, R2's, to be executed across every inbound site in one change. R1 touched
  neither bullet and neither spec-002 file.
- **D15** — the `## References` alpha-review bullet, spec:143. R1 **declined** the plan's offer to cut
  it and argued the reason: a `## References` entry is a locator, not an argument, and its defect
  (unresolvable target) is a claim about a reference. Worker 3 decided the same independently.
  **Do not read D16's removal as precedent for it** — they fail for different reasons.
- **D16** — the one row R1 discharged, because its content is a release-gating judgement rather than a
  contract.
- **D18, D19** — verified true at HEAD; nothing to do.

**What R1 owes R2 that R1 did not record — the box 8 correction.** `### Maintainer decision 1`'s
provenance argument (spec-006's `## Coordination` bullet 3 is what *requested* spec-002's duplicate,
which under `## The single-ownership law` clause 1 makes spec-002's copy the duplicate) is **not in the
rationale**, contrary to box 8 and to the prior section's `### Rows left for R2, and why`. It currently
lives only in the build plan, which closes with the cycle. **R2 must write it into the rationale when
it performs the retirement**, which `### Maintainer decision 1`'s nuance already requires of the pass
that decides the merged `__init__`-export precision's disposition. Do not assume R1 laid any of that
groundwork.

**D6's open pass-1 escalation, still open and not discharged by anything in this item.** The
`## Standing note`'s third bullet now records the biconditional **by its shape and consequence, in the
past tense**, and says outright that the wording is deliberately not reproduced. That is analysis about
the document. It is *not* the retraction record: when R2 restates spec:44, R2's own entry must
additionally record the biconditional as **a claim the spec no longer makes**. Two different
obligations; the second is untouched. (Verified: `iff` occurs once in the rationale, at rationale:75,
in an unrelated sentence — no residual present-tense assertion of the old wording survives.)

**Worker 3's non-blocking Low escalation, carried forward with its recommended resolution.** The
`### docs/README.md structure` entry's closing paragraph (rationale:134-138) frames the two-tree split
in the **present** tense — "is stated as a requirement with its reason attached inline". When R2
restates spec:99 under D8, that framing will describe a sentence whose shape may have changed. It is
not a finding: the paragraph borrows no wording (confirmed by my own n=6 measurement — the previous
`the readme s job is to point at` hit is gone), and its load-bearing claim is that *no other
alternative was weighed there*, which no rewrite touches. Worker 3 offered two resolutions and
preferred (b); **I adopt (b) and record it as the decision so R2 does not re-litigate it**: R2's D8
entry notes that the reason clause was restated, which closes it in the append-only direction. R1's
paragraph is **not** to be reopened — the rationale is append-only from R2 onward (`worker-1.md`
rule 4), and a move record legitimately describes the document as it stood at the move.

**Three more things R2 would otherwise re-derive:**

- **The rationale is append-only from here.** R1's own correction of the file R1 created was legal
  within R1; that latitude ends with this item.
- **The sibling-template overlap is measured and accepted** (§8): 245 shared non-scaffold 8-shingles
  against `appx/spec-005-…-rationale.md`, which is house template at the same magnitude as two
  controls written by other cycles. R2 will inherit the same template when it appends its layer.
  **Do not treat the number as a finding**, and do not "fix" the shared header block. The live DRY
  obligation is the one that matters: R2's own new prose must not restate spec sentences it leaves
  standing, and the check that catches it must tokenize on `[A-Za-z0-9_]+` and case-fold — a
  whitespace tokenizer fails **open** here, which is how the pass-1 Medium happened.
- **The concurrent spec-007 cycle is live and further along.** `docs/SPECS/spec-007-…md` is `M`, its
  rationale and `bld-007-r1-rationale_move.md` are untracked, and its build plan is untracked.
  spec-007 owns **D3, D5, D8, and D17** — every undischargeable `docs/README.md` obligation spec-006
  carries — so R2 must **re-derive every `docs/README.md` claim against the file at the moment it
  writes the sentence**, per the plan's `### First growth`, and state when it measured.

### 10. Concurrent work — reported, not touched

Beyond the three baseline-dirty card-wrap paths (`KANBAN.md`, `KANBAN.html`,
`examples/fakeshop/db.sqlite3`, none edited or reverted by me), `git status --porcelain` carries the
spec-007 cycle's four paths, the **five deleted committed `docs/review/rev-*.md` files**, and untracked
`docs/review/review-0_0_14.md`. All are another session's work. Per the plan's `### Second growth` the
`docs/review/` deletions are **escalated to the maintainer**: I did not read into them, did not
restore them, and ran no `git checkout`. HEAD has not moved, so the content is safe at `947f7494`.
Nothing outside this cycle's declared writable set was written by this pass — which wrote only this
artifact section and the memory file.

### Summary

R1 extracted spec-006's deliberative layer into
`docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` as a genuine cut: three passages / 360
bytes (the `## Problem statement` provenance sentence, `### docs/README.md structure`'s rejected
three-section paragraph, and all of `## Open questions`), replaced by one H1 companion pointer naming
all three, one per-section pointer, and one link definition. The spec went 178/10,934 →
177/**11,019** bytes (**+85**, rule 1's pointers costing more than this spec's whole deliberative
layer, with the arithmetic shown rather than gamed); the rationale is 233 lines / 15,935 bytes.
Re-verified here from HEAD rather than accepted: the move is a cut at fragment granularity (**4/4**,
and the whole diff is five hunks), non-scaffold 8-word shingle overlap between the two files is **0**
on a third independent derivation, **all seven single-carrier glossary anchors survive** at spec:15,
16, 17, 55, 55, 119, 125 with `check_spec_glossary` and the read-only `import_spec_terms --check` both
exit 0, the scaffold and rule-27 gates are clean in both durable files, all three keyed anchors
resolve with no dangling `open-questions`, the staged-anchor sweep is clean, and no falsified contract
statement was pre-empted from R2 — `## Current state` and spec:44 / spec:99 all read at HEAD's
wording. Sixteen checklist boxes (not the fifteen pass 1 tallied), of which fifteen land as ticked and
**one — box 8 — carries a false evidence clause**: the rationale does not record where spec-006
requested spec-002's duplicate. The obligation the box gates is nonetheless discharged and
independently proven, R1 never owed that record, and the work is carried to R2, so it is restated
rather than un-ticked. No hot-path number owed, no floor scope, no failability proof owed, no
fail-open shape possible, and no focused test run applicable — each declared with its reason.
**`final-accepted`.**

### Spec changes made (Worker 1 only)

**None.** No spec edit was needed to accept this item, and none was made:
`docs/SPECS/spec-006-public_surface-0_0_3.md` stands at `git diff --numstat` **`5 6`** and 177 lines /
11,019 bytes — byte-identical to what both Worker 3 passes reviewed — and
`docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` is byte-identical at 233 lines / 15,935
bytes. My verification found no defect in either durable file. The one defect it did find (box 8's
false evidence clause) is a record-accuracy defect in this artifact, whose remedy is the restatement
in `### 1a` — editing a durable file to accommodate it would have been the wrong direction, and
spec:44, spec:99, spec:138, spec:143, and spec:145 are all R2's under D6, D8, D14, and D15.

**No deferral reasons are owed.** The `### Dispatched findings checklist` carries **zero** `- [ ]`
boxes, so there is no un-ticked obligation to defer or to escalate. Nothing was un-ticked by this
pass.
