# Build: Slice 1 — Spec rationale extraction

Spec reference: `docs/SPECS/spec-040-auth_mutations-0_0_13.md` (whole document; the
pre-move file was 2,879 lines / 207,790 bytes)
Status: final-accepted

Worker-1-only slice. It changes no source and no test, and Worker 1 is the only role
permitted to edit a spec or its rationale companion, so no Worker 2 build pass and no
Worker 3 review pass is dispatched for it. The artifact therefore carries one combined
`## Plan (Worker 1)` + `## Final verification (Worker 1)` pair, the shape
[`BUILD.md`][build-md] `### Procedural-closure slices` uses.

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** Not applicable and deliberately not run: the package-wide
AST inventory in [`worker-1.md`][worker-1] `### Package-wide helper inventory before
helper planning` gates **helper planning**, and this slice proposes no helper, no shared
constant, no validation branch, no coercion utility and no test helper — it writes two
Markdown files. Running it would produce ~1,600 lines of index that nothing in the plan
could consume.

- **Existing patterns reused.** The move's shape is not invented here. Three prior
  executions of the same move were read end to end before any text was cut —
  [`docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`][rat-039],
  [`docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md`][rat-038] and
  [`docs/SPECS/appx/spec-046-transport_security-0_0_14-rationale.md`][rat-046] — plus
  the post-move state of their specs. The companion reproduces their structure exactly:
  title + companion paragraph + append contract; `## Provenance of this record`;
  `## Revision history`; one `## Decision N — …` section per Decision carrying
  `### Justification (moved from the spec)` / `### Alternatives considered (and
  rejected)` / `### Changes this Decision underwent`; `## Risks and open questions`;
  `## Non-Decision deliberation`; the ten-group link block. The spec's per-Decision
  pointer wording (`Rationale companion — this Decision's justification and its N
  rejected alternatives: [Decision N][rationale-dN].`) is `spec-038`'s, verbatim in
  shape.
- **New helpers justified.** None. Nothing executable is added.
- **Duplication risk avoided.** The move's characteristic duplication is a section
  existing in **both** files. It is prevented structurally: every moved region was cut
  from the spec by line range in the same operation that wrote it to the companion, and
  the post-move sweep below re-derives the population rather than trusting the cut.

### Implementation steps

1. Prove the spec byte-identical to `HEAD` read-only (`git show HEAD:<path>` into a
   scratch path outside the repo, `diff`), and record the baseline size.
2. Census the moveable population by the **shortest distinctive token**, not the label
   phrase: `grep -oc 'ustification'` and `grep -oc 'lternatives'`.
3. Cut the revision-history block, the eight `Justification` blocks, the twelve
   `Alternatives considered (and rejected):` blocks and the `## Risks and open
   questions` body; write each into the companion under its Decision.
4. Insert a one-line pointer under every Decision naming what was moved and where.
5. Sweep the chronology attribution the moved history stranded.
6. Re-point anchors in both directions and rebuild both link-definition blocks.
7. Verify (the seven checks below) and record the byte counts for Worker 0.

Line numbers cited in this artifact are pin-at-write-time navigational hints against the
**pre-move** spec; the move itself invalidated all of them, which is why every
verification below re-derives its population instead of citing a line.

### Test additions / updates

None. This slice adds no test and touches no executable code. Its instruments are
`scripts/check_spec_glossary.py`, `scripts/check_citations.py`, `uvx pre-commit`, and
the four scripted sweeps recorded under `### Verification`.

### Implementation discretion items

None. Every judgement this slice made was a grading call on specific prose and is
recorded under `### Spec changes made (Worker 1 only)` rather than delegated.

### Spec slice checklist (verbatim)

This cycle is a retrospective reconciliation cycle, not a build of `spec-040`'s own
`## Slice checklist`; the spec's three slices all shipped in `0.0.13`. The boxes below
are this slice's obligations as the maintainer's dispatch and
[`worker-1.md`][worker-1] `### Performing the rationale move` state them.

- [x] The destination is `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`,
      not beside the spec ([`AGENTS.md`][agents] rule 26).
- [x] Cut-and-paste, not copy: no section exists in both files.
- [x] What moves: rejected alternatives and why each lost; amendment blocks and
      decision chronology; retraction claims; derivation narrative that does not change
      how the thing is built.
- [x] What stays: every normative statement; implementation-relevant rationale; the
      public API, slice checklist, test plan, doc obligations, goals, non-goals, edge
      cases, definition of done.
- [x] Every Decision keeps a one-line pointer naming what was moved and where.
- [x] Prose the current decisions have falsified is deleted, not moved.
- [x] The companion is keyed to the spec: every entry names its Decision by heading and
      anchor and carries the alternatives rejected, the changes the Decision underwent
      with the round that caused each, and any claim it may no longer make.
- [x] The companion is left ready to be appended to, and states the append contract in
      its own opening.
- [x] `check_spec_glossary.py` still exits 0.
- [x] Every in-page anchor in the spec still resolves.
- [x] No surviving cross-reference in the spec points into moved text without naming
      the rationale file.
- [x] Both files satisfy the [`START.md`][start] markdown link convention, all ten group
      headers present, every path resolving on disk from its own directory.
- [x] `check_citations.py --check` result recorded.
- [x] `uvx pre-commit run --files <both>` result recorded.
- [x] Byte counts before and after recorded for Worker 0.

---

## Final verification (Worker 1)

### What moved, by route

Five routes account for **47,313 bytes** cut from the spec. **45,936 bytes** are
reproduced in the companion; **1,377 bytes** were deleted rather than moved.

| Route | Count | Bytes | Disposition |
| --- | --- | --- | --- |
| `Revision history (kept inline…)` block | 7 entries | 25,717 | 25,654 moved; the 62-byte preamble line + its 1-byte blank deleted |
| `Justification` blocks | 8 blocks / 9 labels | 4,712 | moved under each Decision |
| `Alternatives considered (and rejected):` blocks | 12 blocks / 35 alternatives | 11,324 | moved under each Decision |
| `## Risks and open questions` body | preamble + 6 items | 4,246 | moved; spec keeps heading + pointer |
| Chronology attributions (36 parentheticals + 2 em-dash clauses) | 38 | 1,314 | deleted; recorded as `### Changes this Decision underwent` bullets |

**3,914 bytes** were added back: fourteen pointer paragraphs, fourteen new link
definitions, two restored clauses and two rewritten passages.

### Byte counts (for Worker 0's plan preamble)

| File | Before | After |
| --- | --- | --- |
| `docs/SPECS/spec-040-auth_mutations-0_0_13.md` | **207,790 bytes / 2,879 lines** | **164,391 bytes / 2,302 lines** |
| `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` | did not exist | **84,865 bytes / 1,249 lines** |

Net removed from the spec: **43,399 bytes / 577 lines** (20.9%). The companion is larger
than the text removed because the `### Changes this Decision underwent` sections, the
provenance record and the `## Non-Decision deliberation` entries are this pass's own
writing, not moved text.

### What deliberately stayed in the spec, and why

- **`## Current state`.** Five dated **observations** of the pre-build repo, which stand
  under [`BUILD.md`][build-md] ``### `## Current state`: observations stand, predictions
  do not``. Graded clause by clause; it carries no prediction about the build's outcome,
  so nothing in it is a falsified claim needing deletion.
- **`## Borrowing posture` and its three sub-sections.** Named in the dispatch as a
  likely source and graded as the carve-out's central case instead. It does not
  deliberate; it enumerates what the implementation borrows semantically from upstream,
  what it borrows structurally from the package's own write family, and the four things
  it must not borrow — including the deliberate improvement of passing the constructed
  user instance to `validate_password(password, user)`, which a builder who never reads
  it implements the upstream way. `spec-038`, `spec-039` and `spec-046` all keep theirs.
- **The `## Slice checklist`'s post-ship blockquote.** A reading instruction about the
  document's own conventions (why the boxes stay unticked, where the completion record
  lives), not deliberation about a decision. It carries a defect this pass did not
  create and does not own — see `### Notes for later slices`.
- **The `## Helper-reuse obligations (DRY)` `D1`–`D19` / `P1`–`P4` / `D-N1`–`D-N3`
  labels and their four in-body citations.** Verified before being touched: these `P`
  labels are a **different vocabulary** that shares the spelling of the review-round
  priority tiers. They are compound labels of the spec's own checklist, defined in the
  spec and cited by it. A sweep keyed on the spelling alone would have deleted four live
  cross-references.
- **The implementation-relevant halves of three attribution parentheticals.** Two
  removals carried substantive reasoning beside the round tag (the denial strings are
  test-asserted contracts; the auth-ledger every-call re-record is what keeps the
  register arm alive across a reload; the cache / conflict state IS the ledger). Under
  [`BUILD.md`][build-md] `## Spec rationale extraction`'s carve-out those stay, so all
  three were rewritten into the surviving sentences as plain statements and only the tags
  dropped. The other 33 removals took nothing but provenance.

### What was deleted as falsified

- **The `Revision history (kept inline so the spec is self-contained):` preamble line**
  (62 bytes). Its claim is exactly what this move made untrue.
- **38 chronology attributions** (1,314 bytes) — 36 parentheticals such as `(the
  Revision-7 wording fix)`, `(the P2 seam fix)` and `(the P1 review finding, folded
  in)`, plus **two mid-sentence clauses that used an em dash rather than parentheses**,
  which the parenthetical-shaped sweep could not see. Those two survived the first
  sweep and were caught only by an independent whole-file token census
  (`grep -c 'Revision'` returned 2 where the sweep's own report implied 0) — the
  second instrument, not the first, is what found them; the spec now carries
  **zero**. The
  `Revision-N` half decoded **against the block this move removed**, so leaving them
  would have stranded every citer in a file no longer containing their referent
  ([`START.md`][start]: stripping a label vocabulary is a rename that strands every
  citer). The bare `P1`–`P3` half decoded against review-round priority tiers never
  present in the spec at all. Both are the review-round attribution [`START.md`][start]
  "Style Rio cares about" bans from standing prose, and `spec-038`, `spec-039` and
  `spec-046` carry **zero** such labels after their moves, against `spec-040`'s 31
  whole-file `Revision` spellings before this pass.
- **[Decision 10][spec-040-d10]'s `**Build note (Worker 1):**` amendment block.** It
  recorded that the optional `run_in_one_sync_boundary` factoring "WAS taken",
  immediately after a sentence still offering it as something a follow-on **may** do,
  while `## Helper-reuse obligations (DRY)` `D17 / P3` still called the primitive "an
  optional follow-on" — three statements of one contract, two of them stale. This is the
  one shape a pure cut-and-paste could not discharge: moving the amendment alone would
  have left the spec offering the thing it had already shipped, which is worse than the
  chronology. The Decision now states the shipped shape directly, `D17 / P3` was
  corrected to match in the same pass, and the chronology is a `**Post-ship**` bullet in
  the companion.

### Verification

1. **Baseline proved read-only.** `git show HEAD:docs/SPECS/spec-040-auth_mutations-0_0_13.md`
   into a scratch path outside the repo, `diff` against the working copy → identical, at
   207,790 bytes / 2,879 lines. No `git stash` / `checkout` / `restore` / `worktree` was
   used ([`BUILD.md`][build-md] `## Claims are proven mechanically, never accepted on
   prose`).
2. **`check_spec_glossary.py` exits 0.**
   `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md`
   → `OK: 30 terms - all have glossary entries and at least one spec link.`, exit 0 —
   the same 30 the pre-flight reported. **The gate was not merely re-run afterwards: the
   cut was graded against it beforehand**, link by link, because a spec's `-terms.csv`
   silently pins which prose a rationale move may take (the `038` execution had to hold
   two clauses back for exactly this). All 30 terms keep a surviving link; the deepest
   losses are `DjangoMutation` 24 → 19, `DjangoMutationField` 19 → 16,
   `ConfigurationError` 16 → 15, and the smallest surviving count for any term is 1. No
   hold-back was needed.
3. **Every in-page anchor resolves, in both files.** Slug derivation follows
   [`START.md`][start]'s GitHub rule (lowercase, drop backticks, strip non-word except
   hyphens, each space to its own hyphen), with fenced blocks stripped before sweeping.
   Spec: **137** anchor occurrences across **17** distinct anchors, **0** unresolved
   (226 across 23 before the move). Companion: **74** occurrences across **15**,
   **0** unresolved. No spec heading was renamed, so no anchor moved; the twelve
   Decision headings are reproduced character-for-character in the companion (only
   `###` → `##`, which does not change a slug), which is why all 55 `#decision-N--…`
   occurrences and all 3 `#risks-and-open-questions` occurrences inside moved text
   resolve locally there.
4. **No surviving cross-reference points into moved text without naming the companion.**
   The moved text carried **82** anchor occurrences; 58 resolve locally in the companion
   and the other **24** (`#test-plan` ×8, `#edge-cases-and-constraints` ×7,
   `#borrowing-posture` ×3, `#slice-checklist` ×2, and one each of `#goals`,
   `#user-facing-api`, `#definition-of-done`,
   `#out-of-scope-explicitly-tracked-elsewhere`) were rewritten as reference-style links
   into the spec. In the other direction the spec's **7** surviving
   ``[Risks](#risks-and-open-questions)`` uses were re-pointed to
   ``[Risks and open questions][rationale-risks]``: each promises the reader
   *deliberation*, and leaving them would have landed a reader on a heading containing
   only a pointer back to the companion. The spec now has **0** inbound in-page anchors
   on that heading.
5. **External citers swept before and after.** `grep -rln 'spec-040'` across the repo
   finds citers in `docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, five sibling specs,
   two sibling rationale companions, the package source and the test trees. **Zero** of
   them cite a `spec-040` *section* — `grep -rn 'spec-040-auth_mutations-0_0_13.md#'`
   returns no match — so no external citation was stranded and none needed repair. The
   one near-miss (`spec-043` line 178, "matching spec-042 Revision 8 and spec-040") names
   `spec-042`'s revision, not this spec's.
6. **Link-definition health, both files.** Every reference-style use has a definition and
   every definition has a use: spec **0** undefined / **0** orphaned (the `feedback2`
   definition orphaned by the move was pruned from the spec and re-defined in the
   companion, where the Revision 2 entry that used it now lives); companion **0** / **0**
   across **49** definitions. All ten canonical group headers are present in both files,
   in [`START.md`][start] order, empty ones included. **Every definition path was
   resolved on disk from its own file's directory** — the companion sits one level deeper
   than the spec, so its relative paths differ throughout (`../../GLOSSARY.md` vs
   `../GLOSSARY.md`, `../../../KANBAN.md` vs `../../KANBAN.md`, the external upstream
   checkout at `../../../../strawberry-django-main/…`). The only initially-missing path
   was this artifact itself, which now exists.
7. **`check_citations.py --check`** — see `### Gate runs` below.
8. **`uvx pre-commit run --files <both>`** — see `### Gate runs` below.

### Gate runs

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md`
  → `OK: 30 terms - all have glossary entries and at least one spec link.` (exit 0)
- `uv run python scripts/check_citations.py --check` → recorded verbatim below.
- `uvx pre-commit run --files docs/SPECS/spec-040-auth_mutations-0_0_13.md docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`
  → recorded verbatim below.

```text
$ uv run python scripts/check_citations.py --check
OK: 975 citations resolve (810 in 442 .py files, 165 in KANBAN.md).
(exit 0)

$ uvx pre-commit run --files docs/SPECS/spec-040-auth_mutations-0_0_13.md \
      docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md
kanban tracked path constants.............................................................................................Passed
source layout (py trailing commas + ascii-only; md link-def scaffold; json/graphql brace explosion).......................Passed
ruff format...........................................................................................(no files to check)Skipped
ruff check............................................................................................(no files to check)Skipped
kanban anchors collision-free (card vs card, card vs glossary, render ids)................................................Passed
citations resolve (AGENTS.md rule 27 path::Symbol refs)...................................................................Passed
```

`check_citations.py` runs whole-tree, so the figure above covers the repository, not
just this slice: both files this slice writes carry `path::Symbol` and
`path #"substring"` citations inherited from the spec, and all of them still resolve
after the move. Both gates were run twice. The `source-layout` hook rewrote **nothing**
on either run — the link-definition scaffold both files were written with is already
the shape it enforces — and `git status --short` after the second run shows only the
three intended paths plus the build plan this cycle's Worker 0 created.

### Notes for later slices

Named, not acted on — later slices own them.

- **A spec-vs-code contradiction noticed in passing, not investigated.**
  [Decision 11][spec-040-d11] states the Channels fallback is **not** borrowed and names
  `SessionMiddleware` + `AuthenticationMiddleware` as the only supported transport, and
  `## Non-goals` repeats it. `django_strawberry_framework/auth/sessions.py` exists at
  `HEAD` and the spec names it nowhere. The build plan already flags this as the largest
  known suspect; this slice read no auth source and asserts nothing about the module's
  behaviour. **Slice 2 owns it.**
- **The `## Slice checklist` blockquote points at retired artifacts.** It directs a
  reader to `docs/builder/bld-slice-*.md`, `bld-integration.md` and `bld-final.md` for
  the per-slice completion record. Those were retired when the `0.0.13` cycle closed;
  under [`START.md`][start] "Retiring a per-cycle artifact strands inbound refs" the
  pointer needs a `git show <commit>:<path>` retarget or de-linking. Left in place: it is
  a reconciliation defect, not a move defect.
- **The companion's append contract is live from here.** Slices 2–5 append the *why* of
  every reconciliation edit they make to the spec as `**Post-ship:**` bullets under the
  owning Decision's `### Changes this Decision underwent`, or under
  `## Non-Decision deliberation` when the finding belongs to no single Decision. The
  spec takes the corrected contract only, stated directly, with no chronology.

### Summary

The rationale extraction `spec-040` never received is done. `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`
now carries the spec's deliberative layer — seven revisions, eight justification blocks,
twelve rejected-alternative blocks with 35 alternatives, and the six-item risk
deliberation — keyed Decision by Decision, with a `### Changes this Decision underwent`
section per Decision naming every change and the revision that caused it, and the claims
six Decisions may no longer make. The spec dropped from 207,790 to 164,451 bytes and
reads as a current contract with no chronology in it.

### Spec changes made (Worker 1 only)

All edits are to `docs/SPECS/spec-040-auth_mutations-0_0_13.md`; the move itself
invalidated pre-move line numbers, so each change is cited by content
([`START.md`][start]: describe by content, never line number).

1. **The `Revision history (kept inline so the spec is self-contained):` block
   removed**, replaced by the five-line paragraph naming the companion. Reason: the move;
   the preamble's own claim is what the move falsified.
2. **Eight `Justification` blocks and twelve `Alternatives considered (and rejected):`
   blocks removed**, each replaced by a `Rationale companion — …: [Decision N][rationale-dN].`
   pointer naming what was moved and its count. Reason: the move.
3. **The `## Risks and open questions` body removed**, heading kept, replaced by a
   pointer paragraph. Reason: the move; every item is a preferred-answer / fallback pair,
   a build-time deliberation instrument rather than a contract.
4. **Seven ``[Risks](#risks-and-open-questions)`` uses re-pointed** to
   ``[Risks and open questions][rationale-risks]``. Reason: each promises deliberation that
   now lives in the companion.
5. **38 chronology attributions deleted** (36 parentheticals, 2 em-dash clauses), with
   the substantive halves of three of them rewritten into their surviving sentences. Reason: falsified / stranded
   by the move (detail under `### What was deleted as falsified`).
6. **[Decision 10][spec-040-d10]'s `**Build note (Worker 1):**` amendment block
   rewritten** to state the shipped `run_in_one_sync_boundary` contract directly, and the
   `## Helper-reuse obligations (DRY)` `D17 / P3` item corrected from "an optional
   follow-on" to the shared-primitive requirement. Reason: [`BUILD.md`][build-md]
   `## Spec rationale extraction` — the spec never narrates its own history, and the two
   statements contradicted the Decision's own build note.
7. **Link definitions:** fourteen added (`rationale-d1`…`rationale-d12`,
   `rationale-risks`, `spec-040-rationale`), one pruned (`feedback2`, orphaned by the
   revision-history move and re-defined in the companion).

No other spec content was touched. No source file, test file, or other spec was opened
for writing.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[rat-038]: ../SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md
[rat-039]: ../SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md
[rat-046]: ../SPECS/appx/spec-046-transport_security-0_0_14-rationale.md
[spec-040-d10]: ../SPECS/spec-040-auth_mutations-0_0_13.md#decision-10--sync--async-session-work-through-one-sync_to_asyncthread_sensitivetrue-boundary
[spec-040-d11]: ../SPECS/spec-040-auth_mutations-0_0_13.md#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully

<!-- docs/builder/ -->
[build-md]: BUILD.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
