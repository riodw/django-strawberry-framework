# Build: Slice 0 — spec rationale extraction (spec-032)

Spec reference: `docs/SPECS/spec-032-full_relay-0_0_9.md` (whole file; pre-move 794 lines, post-move 672)
Status: final-accepted

Procedural-closure slice per `docs/builder/BUILD.md` `### Procedural-closure slices`: pre-flight step 7 is
Worker-1-only work, so there is no Worker 2 build pass and no Worker 3 review pass. This artifact carries one
combined Plan + Final-verification block. **Zero executable bytes changed** — no `.py` file was touched.

## Plan + Final verification (Worker 1)

### Spec status-line re-verification

Read spec lines 1-9 (title, shipped-in header, `Status:`, Owner, Predecessors) before acting. All five still
describe the build's current state: the card is `DONE-032-0.0.9`, the `Status:` line reads
`**SHIPPED (`0.0.9`)**`, the seven-slice summary matches the shipped slices, and every predecessor doc
(`spec-031`, `spec-030`, `spec-015`) exists at its cited path. No status-line edit was owed. The one header
change this pass made is additive: a new deliberative-layer pointer paragraph after `Predecessors:`.

### DRY analysis

**Helper inventory checked.** Not applicable, and deliberately so: this slice writes no Python and proposes no
helper, shared constant, validation branch, coercion utility, or test helper. The package-wide AST inventory
prevents duplicated *code* shapes; there is no code in this slice's diff to duplicate. Recorded rather than
skipped so a later pass can see the question was asked.

- **Existing patterns reused.** The already-extracted sibling pair is the house shape and was followed
  literally: `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` (post-extraction spec — header pointer paragraph,
  one `Rationale companion —` line per Decision, a `## Risks and open questions` heading reduced to a pointer)
  and `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md` (companion — `# Rationale companion:
  spec-NNN (...)`, `## Provenance of this record`, `## Revision history`, one `## Decision N — <title>` per
  spec Decision each carrying `### Justification (moved from the spec)` / `### Alternatives considered (and
  rejected)` / `### Changes this Decision underwent`, then `## Risks and open questions` and `## Non-Decision
  deliberation`). Link-definition group headers and relative-path depth were copied from that companion, which
  lives in the same `docs/SPECS/appx/` directory.
- **New helpers justified.** None.
- **Duplication risk avoided.** The one real duplication hazard in a rationale move is *copying* instead of
  *cutting*, which leaves the same paragraph in two files that then drift. Every block was removed from the
  spec in the same operation that wrote it to the companion, and the byte reconciliation below is the proof:
  the removed bytes and the post-move file size agree to the byte.

### Implementation steps (as executed)

1. Baseline measured: `wc -c` on the spec; `check_spec_glossary.py` run as a precondition.
2. Rewrote the 32 embedded chronology-marker sites in place so each sentence states its contract directly.
3. Cut the four block routes (revision history, 13 Justification blocks, 13 Alternatives blocks, the Risks
   body) and replaced each with framing: one header pointer, 13 per-Decision pointers, one Risks pointer.
4. Added 15 link definitions to the spec (`[rationale-d1]`..`[rationale-d13]`, `[rationale-risks]`,
   `[spec-032-rationale]`) and pruned the 4 definitions the moved text took with it.
5. Authored `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` on the sibling's section shape.
6. Ran the verification suite below and re-ran the foreign-citation census.

### What MOVED, by section

| Route | Bytes | Detail |
| --- | --- | --- |
| `Revision history (kept inline …)` block | 22,034 | 8 `Revision N` entries, 31 lines, byte-verbatim. The 62-byte preamble line was **deleted, not moved** (see below). |
| 13 `Justification:` + 13 `Alternatives considered (and rejected):` blocks | 18,641 | 26 justification bullets or paragraphs and 33 rejected alternatives (D1 2, D2 1, D3 3, D4 3, D5 5, D6 4, D7 3, D8 2, D9 1, D10 3, D11 2, D12 3, D13 1). The 26 label lines became `###` headings in the companion. |
| `## Risks and open questions` body | 5,864 | Preamble + 9 preferred-answer / fallback items. Unlike `spec-031`, **no item carried a rule that outlives the build**, so nothing was held back and the spec keeps only the heading + pointer. |
| Embedded chronology markers | 525 | 32 sites, enumerated below. |

**The 32 chronology-marker sites** (line numbers are pre-move): 97, 101, 106, 111, 220, 263, 340, 341, 342,
367, 391, 433 (two markers on one line), 448, 450, 513, 518, 523, 524, 528, 544, 558, 559, 563, 569, 575, 581,
589, 598, 599, 614, 668, 677. Twenty-eight were `(Revision N PN)` / `(Revision 3 / second-review PN)`
parentheticals removed outright. Four needed a rewrite rather than a deletion:

- **L111** — "(checked - needs no edit, Revision 7 Q4)" became "(checked - needs no edit)".
- **L448** — "(Revision 8: the encoder signature dropped info in the 0.0.14 hardening)" became "(the encoder
  signature is (type_cls, model, root) -> str and never receives info)". The chronology became the contract it
  was narrating, which is the ideal outcome of a marker rewrite.
- **L433** — "spec-030 already corrected this exact claim (its Revision 2)" became "spec-030 carries the same
  corrected contract (its rationale companion)". A **foreign** spec's chronology, re-pointed at that spec's
  rationale companion; the reference-style link definition is unchanged, only the link text and the clause.
- **L513** — "the precedent spec-031's build followed (its Revision 6 swept the stale shipped-slice anchors)"
  became "..., whose own stale shipped-slice anchors were swept the same way (rationale companion)".

### What STAYED, by section

Every normative statement, plus the whole of: Key glossary references, Slice checklist, Problem statement,
Current state, Goals, Non-goals, Borrowing posture (including the parity table), User-facing API (all three
code samples + Error shapes), all 13 Decision **bodies**, Implementation plan (table + staged-anchor rule),
Edge cases and constraints, Test plan (all six slice sections), Doc updates, Out of scope, Definition of done.

Two judgement calls, both resolved by the "when unsure, it stays" rule in `worker-1.md`:

- **Decision 9's `first`+`last` schema-bypass parenthetical stays in the spec.** It reads as build chronology
  ("the Slice-4 build discovered…") but its body is the load-bearing mechanism — Strawberry's generic
  specialization copies `DjangoConnection[T]` into a plain class whose `resolve_connection` is
  `ListConnection`'s, dropping the package override. A builder who never reads it reintroduces the bare alias,
  which is exactly the carve-out `BUILD.md` protects. The chronology half is additionally recorded under
  Decision 9's `### Changes this Decision underwent` in the companion.
- **The three `recorded at final verification` phrases in `## Doc updates` (spec lines 614, 617, 623 pre-move)
  stay.** They are doc-obligation provenance, not `(Revision N)` markers, and removing them was outside this
  slice's named scope. Flagged below for the review round rather than acted on.

### DELETED as falsified, not moved

Exactly one passage:

- **`Revision history (kept inline so the spec is self-contained):`** (spec line 11 pre-move, 62 bytes). The
  sentence asserts the history is kept inline in this document. The move is precisely what makes that false, so
  it belongs in neither file — carrying it into the companion would reproduce a claim that is untrue at its new
  address as well as its old one. Git preserves it. This is the `spec-031` precedent, applied for the same
  reason.

No other spec sentence was found to be falsified **by the spec's own current decisions**. Two are falsified by
**shipped code** (`nodes(ids:)` is uncapped; the `"both"` relation-shape default) — those are Slices 1-3's, not
this pass's, and they are recorded in the companion as post-ship notes rather than deleted here.

### Verification

**1. Glossary gate — precondition and postcondition, both exit 0.**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md
OK: 40 terms - all have glossary entries and at least one spec link.
EXIT=0
```

(Run before the move and again after. The script accepts the archived `docs/SPECS/` path; no substitute
invocation was needed. Same term count both times — no glossary-linked term left the spec, which is the
expected result of moving deliberation only.)

**2. Markdown scaffold gate.**

```
$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-032-full_relay-0_0_9.md docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md
EXIT=0
```

**3. In-page anchors and reference-style links, both files, checked mechanically** (every `](#…)` target
resolved against the surviving headings by GitHub slug rules; every `[ref-id]` use resolved against the bottom
link-definition block; every definition path checked for existence on disk; every cross-file
`#anchor` in a definition checked against the target file's headings):

| Check | `spec-032` | `...-rationale.md` |
| --- | --- | --- |
| `[ref-id]` uses with no definition | none | none |
| Definitions never used | none (4 pruned - see below) | none |
| Dangling in-page `](#...)` anchors | none | none |
| Definition paths missing on disk | none | none |
| Definition cross-file anchors missing | none | none |

**Instrument note (this cost a false pass once already).** The first run of the anchor checker reported 12
"dangling" anchors in each file - all false. The slugger collapsed runs of whitespace with
`re.sub(r'\s+', '-', ...)`, so " - " (space, em-dash, space) became one hyphen instead of two after the dash
was stripped, and every `decision-N--title` anchor missed. Fixed to substitute each whitespace character
individually, and asserted against three known-good headings before believing the second run's zero. **A wrong
instrument's false positives are indistinguishable from real rot** - and a checker that passes for the wrong
reason would have been worse.

**4. Definitions pruned from the spec** (each became unreferenced because the only text using it moved, and
each is now defined in the companion): `[resolvers]`, `[spec-030-rationale-d3]`, `[spec-031-rationale-d1]`,
`[spec-031-rationale-d3]`. `[spec-031-rationale-d11]` and `[spec-031-rationale-revisions]` are still used by
surviving prose and were kept.

**5. Companion link-definition block** carries all 10 canonical group headers in `START.md` order, defs
alphabetical within each group, paths relative to `docs/SPECS/appx/`. Two groups (tests, scripts) are present
and empty. Every path was disk-exists-checked (see table above); the one definition that pointed at a
not-yet-existing file, the reference to this artifact, resolves now that this artifact exists.

**6. No surviving cross-reference in the spec points into moved text without naming the companion.** Every
Decision carries its `Rationale companion -` pointer line, the header carries the deliberative-layer pointer,
and `## Risks and open questions` carries its pointer. Grep for "revision history", "kept inline", and "this
history" in the post-move spec returns zero hits.

**7. Cut-and-paste proved mechanically, not asserted.** Every non-label line of the 15 cut blocks was checked
to appear in the companion AND to be absent from the spec: 0 lines missing from the companion, 0 lines still
in the spec. The 10 inline-label forms (`Justification: <text>` on one line) were checked separately on their
body text, since the label became a heading. The spec carries 0 residual `Justification:` /
`Alternatives considered` labels and exactly 13 `Rationale companion -` pointers.

**8. Byte counts (Worker 0 needs these for the plan preamble).**

| File | Before | After |
| --- | --- | --- |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | **188,525** bytes / 794 lines | **145,056** bytes / 672 lines |
| `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` | did not exist | **75,855** bytes / 429 lines |

Reconciliation, to the byte: 47,127 bytes left the spec (22,034 revision-history entries + 62 deleted preamble
+ 1 blank line + 18,641 Justification/Alternatives + 5,864 Risks body + 525 chronology markers). The move put
4,162 bytes of framing back (header pointer + 13 Decision pointers + Risks pointer = 2,299; 15 new link
definitions = 1,863), then pruning 4 dead definitions took 504 off again - net framing 3,658. 47,127 - 3,658 =
**43,469**, which is exactly 188,525 - 145,056. The spec is **23.1% smaller** and the last spec in the shipped
run without a companion now has one.

These figures measure the move and nothing after it. Slices 1-3 of this cycle will grow the spec again, so
this is not a claim about the file's current size at any later date.

**9. Tool runs after edits.** `uv run ruff format .` - `434 files left unchanged`. `uv run ruff check --fix .`
- `All checks passed!`. No `.py` file was touched, so both are no-ops confirming exactly that. No `pytest` was
run, per `AGENTS.md` and the Worker 1 role file.

### Foreign-citation census (re-run, not inherited)

Method: (a) grep the tree for `spec-032-full_relay-0_0_9.md#` to find deep links; (b) grep for `spec-032` /
`spec_032` to enumerate every citing file (49 files); (c) filter those hits for
`revision|justification|alternativ|rejected|risk|open question`; (d) read every surviving hit against the moved
text; (e) separately sweep every `.py` file for `spec-032` and read each citation's grammar. `.venv/` and
`.git/` excluded; `docs/builder/DONE/` treated as closed-cycle history.

**Confirmed, as pre-recorded:** no `spec-032-full_relay-0_0_9.md#<anchor>` deep link exists anywhere outside
the two files this slice wrote. Plain `spec-032 Decision N` / `Goal N` / `Edge cases` / `Non-goals` / `DoD`
citations - 47 sites across 20 `.py` files and 4 sibling specs - survive the move untouched, because the
Decisions and those sections stayed in the spec. **The general shape: a rationale move breaks history and
deliberation citations only; contract citations survive by construction.** One near-miss worth recording:
`spec-033` line 410 also matches a case-insensitive "revision" grep, but it is `spec-033`'s own Revision 4, a
self-reference, not a citation into `spec-032`.

**One foreign spec site, as pre-recorded** (belongs to Slice 3, NOT repaired here):

- `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` #"Revision 6 P2 established that nothing implements
  strictness for connections" (line 371 at the time of writing). Re-point it at the companion. Two valid
  targets, both in `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md`:
  - **preferred**, the Decision-keyed home:
    `#decision-12--sequencing-against-the-connection-aware-optimizer-and-the-library-first-activation`, whose
    `### Changes this Decision underwent` carries the finding as "**Revision 6 P2** - the strictness-mode claim
    described behavior nothing implements. ... All three sites were corrected to 'strictness does **not** flag
    it until `033`'";
  - the chronology home: `#revision-history`, where the entry reads verbatim "**P2 - the strictness-mode claim
    described behavior nothing implements.**".

  `spec-033` links reference-style, so the repair is one new definition (e.g.
  `[spec-032-rationale-d12]: appx/spec-032-full_relay-0_0_9-rationale.md#decision-12--...`) plus a reword of
  the sentence so it stops narrating `spec-032`'s revision numbering. Prefer the Decision anchor: a Decision
  citation cannot rot in a future rationale move, a Revision citation can.

**Two sites the pre-run census MISSED:**

- `tests/test_relay_node_field.py` #"(spec-032 Revision 7 P1)" - a comment on the malformed-base64 parametrize
  case (line 678 at the time of writing).
- `tests/test_relay_node_field.py` #"Discriminating (spec-032 Revision 7 P2)" - a test docstring (line 1218).

Both cite `spec-032`'s revision history, which is exactly the text that moved. The pre-run's claim that "plain
`spec-032 Decision N` citations in `.py` comments survive" is true, but it was scoped to the `Decision N`
grammar, so the `Revision N PN` grammar in the same tree went unsampled. **A census is only as wide as its
grammar: the population is `spec-032` plus any chronology word, not `spec-032 Decision`.**

### Notes for Worker 1 (spec reconciliation)

1. **Slice 3 owns the `spec-033` citation repair.** Exact site, both replacement anchors, and the
   reference-style mechanics are recorded above so the item cannot be lost. Deliberately NOT repaired here -
   sibling-spec edits are Slice 3's.
2. **The two `.py` comment citations need a NAMED owner, and this slice is not it.** Both now point into the
   companion: the P1 finding is recorded under
   `#decision-4--djangonodefield--djangonodesfield-a-bare-interface-form-and-a-typed-form` (the
   Argument-spelling bullet) and the P2 finding under
   `#decision-5--null-for-invisible-rows-graphqlerror-for-malformed-ids` (the narrow-catch-scope bullet); both
   also sit in `#revision-history`. Lowest-risk repair: re-cite them as `spec-032 Decision 4` and `spec-032
   Decision 5`, since both contracts stayed in the spec. **This is a `.py` edit and this slice changes zero
   executable bytes**, so it is routed, not taken. The cycle's scope authorizes `.py` edits only on a code-gap
   finding, which this is not, so it needs either (a) Slice 3 taking it as a comment-only repair under an
   explicit maintainer widening, or (b) the final gate's `### Deferred work catalog`, the `031`-cycle precedent
   for comment-only clauses. An item routed forward without a named owner does not survive.
3. **Three "recorded at final verification" provenance phrases survive in `## Doc updates`** (post-move spec
   lines ~491, ~494, ~500). They are build chronology under the strict reading of `BUILD.md` "the spec never
   narrates its own history", but they are not `(Revision N)` markers and were outside this slice's named
   scope. Offered to the review round as a judgement call, not asserted as a defect.
4. **The companion already carries two post-ship notes Slices 1-3 must discharge in the spec**, recorded under
   its `## Risks and open questions`: Risks item 1's glossary-entry gap is closed (both entries shipped, so
   Definition-of-done item 1's "intentionally absent from the CSV" is stale), and Risks item 7 is **falsified
   outright** - `nodes(ids:)` is capped at 200 by `resource_policy.py::ResourcePolicy.max_node_ids`, which is
   that item's own recorded *fallback*, not its preferred answer. The matching `## Edge cases and constraints`
   entry in the spec still says uncapped, and is Slice 1's.

### Test additions / updates

None. This slice changes zero executable bytes, adds no source and no test, and runs no `pytest` per
`AGENTS.md`. `git status --short` after the pass shows only the three in-scope paths this slice wrote plus the
maintainer's concurrent untracked work (`0_0_14.md`) and Worker 0's untracked build plan. The eleven staged
`bld-031-*` deletions recorded in the plan's baseline are gone from `git status` - the maintainer committed
them mid-cycle. Nothing was reverted and nothing out of scope was touched.

### Spec slice checklist (verbatim)

Not applicable. Slice 0 is a pre-flight step, not an entry in the spec's `## Slice checklist` (which carries
the seven build slices 1-7, all shipped). There are no boxes to copy, tick, or audit. Recorded explicitly
rather than omitted, so the absence reads as a decision.

### Implementation discretion items

None. Every choice in a rationale move is the custodian's; nothing was delegated.

### Summary

`docs/SPECS/spec-032-full_relay-0_0_9.md` shrank from 188,525 bytes / 794 lines to 145,056 / 672, and its
deliberative layer now lives in the net-new 75,855-byte
`docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md`, keyed to the spec by Decision heading and anchor.
Four routes carried text out - the eight-entry inline revision history, 13 Justification blocks, 13
Alternatives blocks, and the Risks-and-open-questions body - plus 32 embedded chronology markers rewritten in
place so each sentence states its contract directly. One sentence was deleted as falsified rather than moved.
Both gates exit 0, every anchor and link definition in all three files resolves, the cut-and-paste was proved
line by line in both directions, and the foreign-citation census found one sibling-spec site (routed to Slice 3
with both replacement anchors) plus two `.py` test-comment sites the pre-run missed (routed with a named-owner
requirement).

### Spec changes made (Worker 1 only)

All within `docs/SPECS/spec-032-full_relay-0_0_9.md`, all triggered by Slice 0 (the rationale move). Line
numbers are pre-move.

1. **Lines 11-43 removed**, replaced by a one-line deliberative-layer pointer after `Predecessors:`. Reason:
   the revision history is the spec's largest chronology block, and the spec must not narrate its own history.
   Line 11 (the "kept inline so the spec is self-contained" preamble) was deleted rather than moved, because
   the move is what falsifies it.
2. **Lines 274-282, 294-296, 302-313, 324-334, 345-357, 369-381, 395-401, 416-425, 440-442, 454-460, 467-472,
   481-487, 493-495 removed**, each replaced by a `Rationale companion -` pointer naming what moved, where, and
   how many alternatives it carries. Reason: Justification and rejected-alternative blocks are deliberation,
   and the pointer is what stops a later reviewer re-litigating a settled alternative.
3. **Lines 627-637 removed**, replaced by a pointer paragraph under a RETAINED `## Risks and open questions`
   heading (retained so every in-page link to it still resolves). Reason: the preferred-answer / fallback shape
   is a build-time instrument, not a contract. Unlike `spec-031`, no item held normative residue, so nothing
   was held back.
4. **32 chronology-marker sites rewritten in place** (all enumerated above). Reason: a normative sentence
   states its contract directly; "as of Revision N" is a chronology hedge whose home is the companion.
5. **15 link definitions added** (`[rationale-d1]`..`[rationale-d13]`, `[rationale-risks]`,
   `[spec-032-rationale]`) and **4 pruned** (`[resolvers]`, `[spec-030-rationale-d3]`,
   `[spec-031-rationale-d1]`, `[spec-031-rationale-d3]`). Reason: the spec must name the companion wherever it
   points into moved text, and a definition whose only user left is dead weight that reads like a live
   reference.

No source or test file was edited. No sibling spec was edited. No closeout or agentflow doc was edited.

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
