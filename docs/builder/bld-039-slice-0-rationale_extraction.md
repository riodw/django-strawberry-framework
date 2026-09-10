# Build: Slice 0 — Rationale extraction (`spec-039`)

Spec reference: `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` (whole file; the
move touched lines 308-617, 1667-1684, 1708-1725, 1735-1758, 1774-1806, 1860-1878,
1913-1950, 2277-2296, 2545-2565, 2608-2619, 2661-2674, 2688-2700, 2739-2741, 2780-2781,
2803-2818, 2854-2879, 2909-2911, 2913-2922, 3585-3702, 3921-3927 at `HEAD`, plus the
in-place re-points listed under `### Spec changes made (Worker 1 only)`)
Status: final-accepted

This is a **procedural-closure slice** (`docs/builder/BUILD.md`
`### Procedural-closure slices`): spec-and-companion-only, no executable change, no
Worker 2 build and no Worker 3 review. It closes as one combined Plan + Final-verification
pass by Worker 1. The authorizing clause is the build plan's own
`docs/builder/build-039-serializer_mutations-0_0_13.md` pre-flight step 7 — "**owed by
Slice 0 of this cycle**; it is the cycle's own first deliverable rather than a
precondition, because writing it *is* the work."

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped: this slice adds
  no code, no helper, no constant and no test. `docs/builder/worker-1.md`
  `### Package-wide helper inventory before helper planning` gates *helper planning*, and
  the slice proposes none. The package `.py` tree was not read or written.
- **Existing patterns reused.** The whole slice is a re-execution of an existing pattern:
  `docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md` is the immediately-preceding
  execution of the same move and is the structural twin (`spec-039` is `spec-038`'s twin by
  the spec's own `Predecessors:` line). Its section shape, its
  `### Changes this Decision underwent` sections, its `## Provenance of this record`
  framing, its `### Justification (moved from the spec)` /
  `### Alternatives considered (and rejected)` split, its per-Decision `Spec:` back-pointer,
  its `Rationale companion — …` forward pointer in the spec, and its ten-group link-definition
  block were all copied rather than re-invented.
- **New helpers justified.** None.
- **Duplication risk avoided.** The one duplication this slice can create is **the move
  becoming a copy** — text landing in the rationale while surviving in the spec. Prevented
  by extracting every region to a scratch file *before* editing and then proving, line by
  line, that no substantive moved line remains in the spec (see
  `### Move-not-copy proof`).

### Implementation steps

1. Read the required standing docs, the active spec, the build plan, and the `spec-038`
   rationale precedent end to end.
2. Verify `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` byte-identical to `HEAD`
   via `git show HEAD:<path>` into a scratch path outside the repo, then `diff -q`.
3. Census the deliberative layer with the shortest distinctive token
   (`grep -oin 'ustification'`, `grep -oin 'lternatives'`), establish the 1:1 pairing by
   interleaving rather than by equal counts, and enumerate every region's exact line span.
4. Grade every candidate heading clause by clause (`### Heading-by-heading grading`).
5. Extract each region verbatim to the session scratchpad.
6. Apply the spec cuts bottom-up under a pre-asserted anchor check, replacing each with a
   pointer.
7. Author `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md` by splicing
   the verbatim regions into the `spec-038` section shape.
8. Add the `[rationale-d1]`…`[rationale-d14]` / `[rationale-rev6]` / `[rationale-risks]` /
   `[spec-039-rationale]` definitions to the spec and build the rationale's own ten-group
   block.
9. Run the two gates and the link / anchor / on-disk-path audits.

### Test additions / updates

None. The slice ships no executable change, so no test can pin it; its verification is the
two gates plus the mechanical audits recorded under `## Final verification (Worker 1)`.
No temp tests were created.

### Implementation discretion items

None. Every judgement in this slice is a grading judgement and is recorded explicitly.

### Spec slice checklist (verbatim)

`spec-039`'s own `## Slice checklist` has no Slice-0-of-this-cycle entry: this cycle's
Slice 0 is a **residual-reconciliation** slice, not a `spec-039` implementation slice (the
spec's own "Slice 0" is the shipped DRF dependency gate). The governing checklist is the
build plan's, so its one box is copied here verbatim:

- [x] Slice 0: write the rationale companion; move the spec's deliberative layer out -> `docs/builder/bld-039-slice-0-rationale_extraction.md`

### Heading-by-heading grading

Every candidate the dispatch named, graded clause by clause. **MOVED** = cut into the
rationale. **STAYS** = graded and deliberately left. **SLICE 2** = a defect this slice
found and is not licensed to fix.

| Spec heading | Verdict | Why |
|---|---|---|
| `Revision history (kept inline …)` block | **MOVED** (label deleted) | Ten `Revision N` entries are pure authoring chronology — `docs/builder/worker-1.md` `### Performing the rationale move` names "any chronology of how a decision reached its current form" as moving text. The label line itself was **deleted, not moved**: its claim that the history is kept inline is what the move made untrue. |
| 14 × `Justification:` | **MOVED** | Derivation narrative. Each states why a Decision won, never what the code must do. |
| 14 × `Alternatives considered (and rejected):` | **MOVED** | 31 rejected alternatives with the reason each lost — the canonical moving shape. |
| `## Architectural decisions` Decision **bodies** 1-14 | **STAYS** | Every one is the normative ruling. Each keeps a one-line `Rationale companion — …` pointer per rule 1. |
| Decision 4 `**Shared-helper homes …**` paragraph | **STAYS** | An import obligation naming where each promoted helper lands — normative, not deliberation. |
| Decision 6 / 7 / 8 `**Cross-flavor reuse …**` paragraphs | **STAYS** | Same: they forbid a third byte-parallel copy and name the shared site. |
| Decision 12's `This reverses the earlier draft's "stays in `__all__`" choice …` | **MOVED** | One sentence of chronology; the paragraph it trailed states the contract. |
| Decision 14's `(An earlier draft lumped `uv.lock` with the version files …)` | **MOVED** | Same shape. |
| Decision 12's soft-dep-coverage item | **STAYS**, and **grew** | It received the held-back recorded-floor statement (below). |
| `## Risks and open questions` **body** | **MOVED** | Nine items: eight preferred-answer / fallback pairs and one card-citation tension recorded rather than reconciled. Both shapes are a build-time deliberation instrument. Heading + pointer kept. |
| … its `Recorded floor (Slice 0, verified): djangorestframework>=3.17.0` statement | **HELD BACK** | A measured normative record and the spec's only statement of the pinned floor, which the Slice 0 checklist calls one of "three places that must agree". Appended to Decision 12's surviving normative sentence; **not** reproduced in the rationale. |
| Decision 3's `(and with `DjangoType` / `FilterSet` / `OrderSet`)` parenthetical | **HELD BACK** | Ordinary deliberation, but it carries the spec's **only** links to two `-terms.csv` terms. Moved to the Decision body's own "declared exactly like every other consumer surface" sentence, which it explains. |
| `## Round-6 improvements` **preamble** | **MOVED** | Narrates where the improvement set came from and calls the section a design record. Replaced with a non-chronological lead-in + pointer. |
| `## Round-6 improvements` 17 × `### rev6 #N` **subsections** | **STAYS** | Each states a shipped contract — the registry, the scalar matrix, the enum rule, the agreement guard, the injection contract, the nested opt-in. Removing them would strip contract. The `### rev6 #N` **heading vocabulary** is a **SLICE 2** obligation. |
| `## Problem statement` | **STAYS** | Normative framing of what the card is for, plus the crit-7 soft-dep posture, which is implementation-relevant under the carve-out. |
| `## Current state` | **STAYS** | Five dated observations of the pre-build repo, which stand under `docs/builder/BUILD.md` ``### `## Current state`: observations stand, predictions do not``. Graded clause by clause; no clause is a prediction about the build's outcome. |
| `## Goals` / `## Non-goals` | **STAYS** | `docs/builder/worker-1.md` lists both under "What STAYS in the spec". |
| `## Borrowing posture` (incl. `### Reference-package parity checkpoint`, the three borrow / do-not-borrow subsections) | **STAYS** | The parity contract: what is adopted, what is not, and the shape each maps to. `spec-038`'s execution of this move kept the identical section, `### Explicitly do not borrow` included. |
| The `> **Post-ship hardening revision (2026-07-15 …)**` blockquote | **SLICE 2** | See `### Notes for Worker 1 (spec reconciliation)`. |
| The `**[superseded by the 2026-07-15 hardening revision — …]**` bracket in the Slice 3 checklist | **SLICE 2** | Named in the dispatch; not fixed here. |
| The 199 process labels | **UNTOUCHED** | Removing them now blinds this cycle's four audit passes. |

---

## Final verification (Worker 1)

### Summary

`docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md` now exists and carries
`spec-039`'s deliberative layer: the ten-revision authoring history, all 14 justifications,
all 14 alternatives blocks (31 rejected alternatives), the two inline chronology fragments,
the whole `## Risks and open questions` body, and the `## Round-6 improvements` preamble.
The spec keeps every contract and reads as a self-contained contract without it.

### Before / after

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` | 343,592 bytes / 4,354 lines | 296,665 bytes / 3,725 lines | **−46,927 bytes / −629 lines** |
| `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md` | did not exist | 95,992 bytes / 1,390 lines | new |

The spec was verified byte-identical to `HEAD` before the first edit:

```shell
git show HEAD:docs/SPECS/spec-039-serializer_mutations-0_0_13.md > <scratchpad>/spec-039.HEAD.md
diff -q <scratchpad>/spec-039.HEAD.md docs/SPECS/spec-039-serializer_mutations-0_0_13.md
# -> IDENTICAL-TO-HEAD
```

**53,853 bytes were cut** by six routes and **6,926 bytes** of pointers, link definitions
and two hold-backs were added back. Per route: revision-history block 26,041 B / 310 lines;
14 `Justification:` blocks 7,649 B; 14 `Alternatives considered (and rejected):` blocks
9,766 B; two inline chronology fragments 171 B + 130 B; `## Risks and open questions` body
9,525 B / 118 lines; `## Round-6 improvements` preamble 571 B / 7 lines.

`git diff` against `HEAD` for the spec is **645 lines removed, 99 added**, and every one of
the 99 is a pointer, a re-point, one of the two hold-backs, or a link definition.

### Move-not-copy proof

Every region was extracted to the scratchpad **before** the first edit. Afterwards, each
substantive line of the extracted corpus (≥ 40 characters, excluding lines that are nothing
but a wrapped `([Decision N](#anchor))` cross-reference) was searched in both files:

```
prose lines checked: 557 | leaks into spec: 1
    ('moved-risks.txt', '`docs/spec-039-serializer_mutations-0_0_13.md`')
```

The single hit is a bare filename string that Decision 1's surviving body also contains; it
is not prose content. Spot-checked quotes, `spec count / rationale count`:

| Quote | spec | rationale |
|---|---|---|
| `the card is sized **L** and auth is separately carded with its own` | 0 | 1 |
| `Rejected: it forces every consumer to` | 0 | 1 |
| `initial draft authored from the [`TODO-ALPHA-039-0.0.13`][kanban]` | 0 | 1 |
| `Each item names a preferred answer for the `0.0.13` cut and a fallback if` | 0 | 1 |
| `A review pass (rev6) proposed 16 improvements that make the serializer` | 0 | 1 |
| `resolves to 3.17.1` (the held-back record) | 1 | 0 |
| `declared exactly like every other consumer surface in the package` (the held-back enumeration's host sentence) | 1 | 0 |

The 20 extracted lines that do **not** appear verbatim in the rationale are exactly the
deliberate transformations, all accounted for: the 13 inline `Justification: ` prefixes
stripped (Decisions 2-14), the 2 lines of the Decision 3 glossary hold-back, and the 5
revision-history anchors re-pointed at the spec.

### Link / anchor verification

```
docs/SPECS/spec-039-serializer_mutations-0_0_13.md
  undefined refs = []   unused defs = []   dangling in-page anchors = []   defs whose file is missing = []
docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md
  undefined refs = []   unused defs = []   dangling in-page anchors = []   defs whose file is missing = ['bld-039-slice-0']
```

`bld-039-slice-0` is this artifact; it exists as of this write. Both files carry all ten
canonical `<!-- LINK DEFINITIONS -->` group headers in the canonical order (verified against
the list in `START.md` "Markdown link convention"), defs alphabetical within group, paths
relative to each file's own directory. Cross-file:

- every `[rationale-*]` definition in the spec resolves to a heading that exists in the
  rationale — **0 missing**;
- every `[spec-039-*]` definition in the rationale resolves to a heading that exists in the
  spec — **0 missing**;
- the 14 Decision headings are reproduced **character-for-character**, so their GitHub slugs
  are identical in both files and the 68 `#decision-N--…` occurrences inside moved text
  needed no re-pointing.

### Gates

```shell
uv run python scripts/check_trailing_commas.py \
  docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md \
  docs/SPECS/spec-039-serializer_mutations-0_0_13.md
# -> Fixed 0 file(s).   (exit 0)

uv run python scripts/check_spec_glossary.py \
  --spec docs/SPECS/spec-039-serializer_mutations-0_0_13.md
# -> OK: 38 terms - all have glossary entries and at least one spec link.   (exit 0)
```

`38 terms` matches the build plan's recorded pre-flight reading exactly. The gate would
have failed without the Decision 3 hold-back: `FilterSet` and `OrderSet` each had exactly
**one** link in the whole spec and it sat inside moved prose. Measured before the cut, per
term, not discovered by a red gate.

No `pytest` was run: the slice ships no executable change, and no `--cov*` flag was used
anywhere in this pass.

### Process-label population (for the audit passes)

The four audit passes navigate `spec-039` by its process labels, so the population is
recorded here rather than left to be re-derived. Instrument: the build plan's own label
vocabulary (`P1.1`-`P1.7`, `P2.1`-`P2.7`, `P1`/`P2`/`P3`, `F1`-`F11`, `M1`-`M5`,
`H1`-`H3`) matched with non-word / non-dot boundaries, counting **occurrences**:

| | spec @ `HEAD` | spec now | rationale |
|---|---|---|---|
| label occurrences | 199 | 165 | 52 |

**No label was stripped.** All 34 that left the spec travelled inside a sentence this move
cut (the revision history alone accounts for most of them), which the move-not-copy proof
independently establishes. The 52 in the rationale are those 34 plus this pass's own
`### Changes this Decision underwent` citations, where a label is a dated record of what a
review round found rather than standing prose. The build plan states 202; that figure came
from a different instrument, and this one is stated with its pattern so a later pass can
re-derive it.

### DRY check across this slice and prior accepted slices

No prior slice of this cycle exists — this is Slice 0. No duplication introduced: the
rationale's only repeated shapes are the 14 uniform `Spec:` back-pointers and the 14
uniform `Rationale companion — …` forward pointers, which are the `spec-038` house form and
are deliberately uniform.

### Spec changes made (Worker 1 only)

Cuts (line spans at `HEAD`), each replaced by a pointer:

- `308-617` — the whole `Revision history (kept inline so the spec is self-contained):`
  block. Replaced by a five-line deliverative-layer pointer paragraph.
- `1667-1684`, `1708-1725`, `1735-1758`, `1774-1806`, `1860-1878`, `1913-1950`,
  `2277-2296`, `2545-2565`, `2608-2619`, `2661-2674`, `2688-2700`, `2803-2818`,
  `2854-2879`, `2913-2922` — the 14 `Justification:` + `Alternatives considered (and
  rejected):` regions. Each replaced by a two-line `Rationale companion — this Decision's
  justification and its <N> rejected alternative(s): [Decision N][rationale-dN].`
- `2739-2741` — Decision 12's `This reverses the earlier draft's …` sentence (partial-line
  edit; the paragraph's closing `re-break the soft-dep contract.)` survives).
- `2909-2911` — Decision 14's `(An earlier draft lumped `uv.lock` …)` sentence (partial-line
  edit; `entry inside `uv.lock` — stays `0.0.12` until the joint cut.` survives).
- `3585-3702` — the `## Risks and open questions` body. Heading kept, replaced by an
  eight-line pointer paragraph that also names Decision 12 as the floor's home.
- `3921-3927` — the `## Round-6 improvements` preamble. Replaced by an eight-line
  non-chronological lead-in + `[Round-6 improvements][rationale-rev6]` pointer.

Hold-backs (text that stayed because it is contract, not deliberation):

- `2780-2781` (Decision 12) — the sentence `This is the pre-Slice-1 floor check in
  [Risks](…), not an implementation-time discovery.` was rewritten to drop the now-pointer
  reference and to carry the **recorded floor** (`djangorestframework>=3.17.0`, its release
  date, the 9-cell warning-free proof, and the three-places-that-must-agree rule) that the
  Risks body was the spec's only home for.
- `1730` (Decision 3) — `declared exactly like every other consumer surface in the package.`
  now names those surfaces (`DjangoType` / `FilterSet` / `OrderSet` + the two write bases),
  carrying the two `-terms.csv`-pinned links out of the moved justification.

Re-points forced by the move (a surviving reference that promised deliberation now resolves
in one hop instead of landing on a pointer-only heading):

- to `[Risks and open questions][rationale-risks]` — `## Current state` (1), `## Non-goals`
  (3), the `### Reference-package parity checkpoint` table (3), Decision 6 (1), Decision 7
  (1), Decision 10 (2), `## Out of scope` (1) = **12**.
- to `[Decision 12](#decision-12--soft-…)` — the two Slice 0 checklist sub-checks, the
  `## User-facing API` partial-update paragraph, Decision 13's live-coverage list, and the
  `## Test plan` partial-update row = **5**. All five reached for the recorded floor.

Link definitions added to the spec (`<!-- docs/SPECS/ -->` group, alphabetical):
`[rationale-d1]`…`[rationale-d14]`, `[rationale-rev6]`, `[rationale-risks]`,
`[spec-039-rationale]` — 17 definitions, all used.

Deferrals: none. The one box in `### Spec slice checklist (verbatim)` is `- [x]`.

### Notes for Worker 1 (spec reconciliation)

Slice 2 obligations found by this pass. **None was fixed here** — each is a spec rewrite,
and Slice 2 is the reconciliation slice that owns every spec rewrite.

1. **The `> **Post-ship hardening revision (2026-07-15, on `main` after `0.0.13`).**`
   blockquote — 178 lines at the top of the spec (`HEAD` lines 55-232).** This is the
   largest obligation in the file and the reason the move could not simply take it. Its
   framing is pure chronology and belongs in the rationale: it says a security audit
   "superseded parts of this spec's hook contract" and that "where this spec and the code
   disagree, the code and `docs/README.md` govern" — a reader must apply a chronology to
   recover the contract, which `docs/builder/BUILD.md` `## Spec rationale extraction`
   forbids outright. But its **bullets are the current contract** of the hook surface
   (`SerializerHookContext`, the frozen data views, the omission-sentinel + identity check),
   the pipeline-wide alias guard and its authorization-phase exception, the phase
   separation, the authorized-pk / target-state drift snapshot, the relation-intent ledger,
   the post-save database attestation, the write witness, the `save()` result validation,
   and the unique-`source` rule. **Nothing else in the spec states any of them**, and
   Decisions 7, 8 and 12 still assert the superseded pre-hardening shape. Moving the framing
   alone would leave the spec asserting a superseded hook contract with no correction — the
   exact trap the `038` cycle recorded for its own ordering correction, and strictly worse
   than the chronology. **The fix is to fold each bullet into the Decision it supersedes,
   restate that Decision's contract directly, then delete the blockquote and sweep its
   citations** — including `docs/README.md` #"Serializer mutation contracts", which the
   blockquote elevates above the spec. Budget for it: it is the single biggest piece of
   Slice 2.
2. **The `**[superseded by the 2026-07-15 hardening revision — …]**` bracket inside the
   Slice 3 checklist** (`HEAD` lines 1128-1134, now at spec lines 824-830). The construct
   step spells `serializer_class(**get_serializer_kwargs(...))` and then appends a bracketed
   note saying that shape "no longer describes the construct step". A checklist box is the
   one place a stale figure is a **false completion claim**
   (`docs/builder/BUILD.md` ``### `## Current state`: observations stand, predictions do
   not``), so the fix is to state the shipped construct step directly and retire the
   bracket. Named in the dispatch; confirmed present and left alone.
3. **The process-label vocabulary — 165 occurrences left in the spec** (see
   `### Process-label population` for the instrument). Every prior residual cycle stripped
   it and `AGENTS.md` bans process provenance from standing prose, but stripping a label
   vocabulary is a **rename that strands every citer** and no gate in this repo can see it
   (`scripts/check_citations.py` is `path::Symbol`-only). The strip and its `.py` citer
   sweep must land in **one** pass, which is why the fence includes `.py` files. Re-derive
   the `.py` citer population at the time of the strip rather than trusting the plan's
   plan-time figure.
4. **The `### rev6 #N` heading vocabulary — 17 headings.** `rev6` names the review pass that
   proposed the item, which is process provenance in exactly the sense `START.md` "Style Rio
   cares about" forbids. Renaming a heading strands every in-page anchor and every
   `#"substring"` citation into it. Measured: **no in-page anchor targets a `rev6` heading**
   today (`#round-6-improvements-better-than-graphene-django` is the only anchor into the
   section and survives a per-subsection rename), but the `docs/` and package `.py` sweep is
   still owed before any rename, and this companion's `[rationale-rev6]` definition points
   at the **section** heading, not a subsection, so it survives too.
5. **The Round-6 count is seventeen, not eighteen.** The dispatch for this slice said 18
   `### rev6 #N` subsections; the heading list carries `#1` through `#17`, each exactly once,
   in a deliberately non-numeric order. The spec's own preamble said "16 improvements … plus
   one follow-on (#17)", which is seventeen and is where the miscount likely came from. The
   replacement preamble now states the measured count.
6. **The build plan's `202` process labels and this pass's `199` disagree.** Both are
   plausible; they are different instruments and neither published its pattern. This
   artifact publishes its pattern (`### Process-label population`). Slice 2 should re-derive
   rather than pick one.
7. **`## Current state` was graded and owes no edit** — all five bullets are dated
   observations, and the pass found no prediction clause among them. Recorded so a later
   pass can tell a measured no-change from an unexamined one.
8. **The rationale's `### Changes this Decision underwent` sections carry no
   `**Post-ship:**` bullets yet.** This pass checked **nothing** against `HEAD`; it graded
   prose against the spec's own text only. Until the audit slices and Slice 2 run, the
   absence of a `**Post-ship:**` bullet under a Decision means *unexamined*, not
   *unchanged* — the rationale says so explicitly in `## Provenance of this record`, so the
   distinction cannot be lost.

### Final status

`final-accepted`.

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
