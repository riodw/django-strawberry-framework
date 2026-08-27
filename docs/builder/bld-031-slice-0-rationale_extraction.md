# Build: Slice 0 — Spec rationale extraction (pre-flight step 7)

Spec reference: `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` (whole file; pre-move 801 lines / 190,961 bytes)
Rationale companion created: `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`
Status: final-accepted

Procedural-closure slice per `docs/builder/BUILD.md` `### Procedural-closure slices`: one Worker 1 pass,
combined Plan + Final-verification block, no Worker 2 and no Worker 3. The authorizing clause is
`docs/builder/build-031-globalid_encoding-0_0_9.md` `## Dispatch rule for this cycle` together with
`## Cycle shape — this is NOT a feature build` obligation 1, which makes the rationale move this
cycle's first substantive action and gates every later dispatch.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped: `worker-1.md`
  `### Package-wide helper inventory before helper planning` gates *helper planning* before proposing
  new source logic. This pass writes no production code, no tests, and no source of any kind — it moves
  Markdown between two documentation files. No shape in `django_strawberry_framework/` is read, written,
  or duplicated.
- **Existing patterns reused.** The whole move is modelled on the two most recent rationale companions,
  `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md` and
  `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`: the header / provenance / revision
  history / per-Decision (`Justification` + `Alternatives considered (and rejected)` +
  `Changes this Decision underwent`) / Risks / Non-Decision-deliberation layout, the
  `Rationale companion — this Decision's justification and its <N> rejected alternatives: [Decision N][rationale-dN].`
  pointer line left in the spec, the `Spec: [Decision N — <title>][spec-031-dN].` back-pointer, and the
  practice of keeping the *one rule that outlives the build* in the spec's `## Risks and open questions`
  while the deliberation moves.
- **New helpers justified.** None.
- **Duplication risk avoided.** Two. (a) A copy-instead-of-move would leave the deliberation in both
  files; every route below was verified as a deletion from the spec, not a duplication — the spec's
  post-move byte count and a zero-residue grep are the proof. (b) The rationale file's per-Decision
  `Changes this Decision underwent` sections restate findings that also appear in the verbatim
  `## Revision history` block. That duplication is deliberate and bounded to one block, exactly as
  `spec-030`'s companion states: the chronology is what a reviewer of a Decision's *history* needs, the
  per-Decision record is what a reviewer of the *implementation* needs.

### Implementation steps

Executed in this pass, in order.

1. Read the whole spec (801 lines) and both reference companions; enumerate the move set mechanically
   rather than by eye.
2. **Route 1 — the `Revision history` block** (spec lines 11-52, 24,609 bytes). Preamble line deleted
   (its claim "kept inline so the spec is self-contained" is exactly what the move falsifies); the seven
   `Revision N` entries moved byte-for-byte under `## Revision history` in the companion.
3. **Route 2 — 13 `Justification:` blocks and 13 `Alternatives considered (and rejected):` blocks**
   (16,870 bytes; 29 justification bullets or paragraphs, 33 rejected alternatives). Moved byte-for-byte;
   the 26 label lines became `###` headings in the companion. Each Decision in the spec keeps a
   one-line pointer naming what moved and where.
4. **Route 3 — the body of `## Risks and open questions`** (spec lines 665-672, 4,453 bytes). Whole body
   moved; the spec keeps the heading, a pointer, and one surviving rule (below).
5. **Route 4 — chronology framing embedded in surviving contract prose**: 82 sites across 64 lines
   (`(review finding PN)`, `(Rev 7 delta (a)/(b)/(c))`, `(Revision 6)`, one `(P1-b)`, and fourteen whole
   chronology sentences or clauses), 2,235 bytes. Every site is recorded under its owning Decision's
   `### Changes this Decision underwent`, or under `## Non-Decision deliberation`.
6. Add the header pointer paragraph to the spec, and the 15 new link definitions
   (`rationale-d1`…`rationale-d13`, `rationale-risks`, `spec-031-rationale`) sorted into the
   `<!-- docs/SPECS/ -->` group.
7. Verify (below).

**What deliberately STAYED in the spec.** Recorded here because a reader may expect it to have moved:

- **Decision 8's model-label-routing invariant blockquote** and the audit's scoping to
  `registry.models_with_multiple_types()`. Both are normative — the invariant is a contract and the
  scoping is a correctness constraint (a single-type model has no `primary_for`, so an all-models loop
  would mis-handle it). Only the `(review finding P1/P3)` provenance tags moved.
- **Decision 10's step 0 re-entrancy-guard paragraph, including *why* it is load-bearing** (a Phase-2.5
  raise leaves every type `finalized = False`, so a re-run re-enters the loop and, without the guard,
  would re-run the `__func__` test against the type's own installed closure and misclassify it `custom`).
  This is the `worker-1.md` implementation-relevant-"why" carve-out: a builder who never reads it
  reintroduces the misclassification.
- **Decision 10's `_FRAMEWORK_CLOSURE_MARKER` / shadow-install paragraph** and its statement that the
  step-0 guard protects the *same* definition across re-runs while only the marker protects a
  *different* definition inheriting the closure. Same carve-out: the distinction is the mechanism, not
  its history.
- **Decision 13's "silently matching on `node_id` accepted arbitrary payloads"** sentence. It states why
  fail-closed is the contract, not when the contract changed.
- **Decision 4's purity obligation for the callable encoder** (`(type_cls, model, root) -> str`, sync,
  never `node_id`, never `info`). The reason `info` is withheld changes how a consumer writes an
  encoder, so it stays; the "Revision 7 delta (b)" attribution moved.
- **The Risks section's derivation-baseline rule.** `spec-030`'s companion set the precedent that one
  rule outlives the build. Here it is the Strawberry-mechanism baseline: `Node._id` computes the
  type-name slot via `resolve_typename(root, info)` and reads it off the `DjangoType` class in both
  branches, `relay.GlobalID.from_id` raises `GlobalIDValueError ⊂ ValueError`, and `Node._id` asserts
  `isinstance(type_name, str)` — all derived against the uv.lock-resolved Strawberry `0.316.0` against
  an open declared floor. That is a live constraint on future readers, not deliberation.
- **Every `## Current state` bullet.** The section is explicitly framed as the repo as of spec authoring,
  and the spec's own header says so; it is a stated baseline, not a chronology the reader must apply.
- **Line 3's "the on-disk version is still `0.0.8` at spec-authoring time".** Same framing, and identical
  to the shipped `spec-030` header sentence.

**What was DELETED, not moved** (`worker-1.md` rule 2, prose the current decisions have falsified):

- The `Revision history (kept inline so the spec is self-contained):` preamble line (62 bytes). The move
  makes its only claim untrue, so it belongs in neither file.
- Decision 4's `(breaking, pre-`1.0`)` tag on the `info`-drop. It classifies a change, and the spec no
  longer narrates that a change happened; the classification is recorded in the companion instead.

### Test additions / updates

None. This pass writes no `.py` file. No temp tests are appropriate.

### Implementation discretion items

None — no Worker 2 pass exists for this slice.

### Dispatched findings checklist

This is neither a spec slice with a `## Slice checklist` entry nor a review round, so neither
`### Spec slice checklist (verbatim)` nor a findings list applies. The pass's obligations are
`docs/builder/BUILD.md` `## Spec rationale extraction` and `worker-1.md`
`### Performing the rationale move`, audited one by one in `## Final verification (Worker 1)` below.

### Hot-path budget

`none` — carried from the build plan's `## Build-wide context flags`. This pass writes no production
code, so there is no operation to measure. Deliberate, not silence.

### Floor verification

`none` — carried from the build plan's `## Build-wide context flags`. This pass touches no Django /
Strawberry / channels seam. Deliberate, not silence. The floor is recorded for the cycle as Django
**5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**; the shared `.venv` is not the floor.

### Ownership partition

`none; sequential slices` — carried from the build plan.

---

## Final verification (Worker 1)

### Spec status-line re-verification

Read spec lines 1-9 (title, shipped-in header, `Status:`, Owner, Predecessors) at the start of the pass.
All still describe the build's current state: the card is `DONE-031-0.0.9`, `Status: **SHIPPED (0.0.9)**`
is accurate, the five-slice summary matches the shipped surface, and no predecessor doc named there has
been deleted. One line was edited — a new paragraph after Predecessors naming the rationale companion,
which is the move's own header pointer, recorded under `### Spec changes made (Worker 1 only)`.

### Obligation audit

- [x] **The companion exists at the conventional path.** `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`,
      beside the 34 other `-rationale.md` siblings and its own `-terms.csv`. Convention confirmed by
      `ls docs/SPECS/appx/`.
- [x] **Every entry names the spec decision it belongs to by heading and anchor.** Each of the 13
      `## Decision N — <title>` sections opens with `Spec: [Decision N — <title>][spec-031-dN].`,
      resolving to the spec's own heading anchor. Entries belonging to no Decision are under
      `## Non-Decision deliberation`; the chronology block is under `## Revision history`.
- [x] **Each decision carries its rejected alternatives and why each lost** — 33 alternatives across the
      13 `### Alternatives considered (and rejected)` sections, byte-for-byte from the spec.
- [x] **Each decision carries every change it has undergone, with the round that caused it** — 13
      `### Changes this Decision underwent` sections, keyed to Revisions 1-7 and their P1/P2/P3 findings.
- [x] **Each decision carries any claim it may no longer make.** Explicit `**Claim(s) retired.**` bullets
      on Decisions 4, 5, 6, 8, 10, and 13 (callable signature `info`/`node_id`; the one-arg
      `_resolve_globalid_strategy` and the bare `conf.settings` access; `inspect.iscoroutinefunction`;
      `GlobalID.from_base64` and decode-consults-`_resolve_globalid_strategy` and the undefined
      `None`-strategy candidate; the bare `__func__` test and the "production-dead `type` branch";
      the node-id-only fallback for `callable` / `custom`).
- [x] **It is a MOVE, not a copy.** Verified by byte count and by residue grep — see below.
- [x] **Every decision keeps a one-line pointer.** 13 `Rationale companion — this Decision's
      justification and its <N> rejected alternatives: [Decision N][rationale-dN].` lines, one per
      Decision, counts matched against the alternatives actually moved.
- [x] **Falsified prose deleted, not moved.** Two items, listed under `### Implementation steps` above.
- [x] **The spec never narrates its own history.** `grep -nE "review finding P[0-9]|Rev(ision)? ?[0-9]
      delta|Revision [0-9]|rev[0-9]|P1-b|pre-hardening|earlier revisions|0\.0\.1[34]"` over the spec
      returns **zero** matches; a second sweep for `reviewer|feedback pass|revision|previously|earlier
      draft|formerly|prior pass` returns exactly one, the header pointer's own phrase
      "seven-revision review history", which names where the history lives rather than narrating it.
      No amendment block, no retraction paragraph, no "as of Revision 7" hedge survives.
- [x] **`START.md` markdown link convention.** Both files carry a single `<!-- LINK DEFINITIONS -->`
      block with all 10 canonical group headers present in order, defs alphabetical within each group,
      paths resolved from the file's own directory (`docs/SPECS/appx/` for the companion).
- [x] **The rationale file is tracked, not scratch.** Committed alongside the spec by the maintainer; it
      is not under any `.gitignore` scratch path.

### Verification results (`worker-1.md` rule 3)

- **`check_spec_glossary.py`** — `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-031-globalid_encoding-0_0_9.md`
  → `OK: 31 terms - all have glossary entries and at least one spec link.`, exit 0. Same 31 terms as the
  pre-flight run. This was a live risk: the checker requires each CSV term to keep **at least one** link
  in the spec, and the move deleted 48,167 bytes of it. Every glossary ref-id was checked for surviving
  uses *before* the move was applied; none was left orphaned.
- **In-page anchors.** All `](#…)` targets in both files resolve to a heading in the same file
  (GitHub-slug comparison over non-fenced headings). The companion deliberately carries
  `## Decision N — <title>` headings with slugs identical to the spec's, so `#decision-N--…` anchors
  inside moved text resolve locally — which is where a reader of a moved sentence wants to land. The one
  non-Decision anchor in moved text, `#current-state`, names a section the companion does not have and
  was repointed at the spec through the reference-style `[Current state][spec-031-current-state]` link
  rather than left to dangle. This is the only respect in which the move is not byte-verbatim.
- **Link definitions.** In both files every `[text][ref]` use has a def, and every def has a use
  (zero undefined, zero unused). Every def target exists on disk, and every cross-file `#anchor` into a
  `.md` resolves to a real heading — including all `GLOSSARY.md#…` anchors. The single exception at
  verification time was `[bld-031-slice-0]` in the companion, pointing at this artifact, which did not
  yet exist when the check ran; it exists now.
- **`source-layout` hook.** `uv run python scripts/check_trailing_commas.py --check` over both `.md`
  files → exit 0. The scaffold is satisfied rather than left for the auto-fixer.
- **No surviving cross-reference points into moved text without naming the rationale file** — *inside the
  fence*. Repo-wide, two references from `spec-032` now point into text that left `spec-031`; both are
  out of fence and are handed forward below.

### Byte counts

| File | Before | After |
| --- | --- | --- |
| `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` | **190,961** (801 lines) | **148,526** (670 lines) |
| `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md` | — (did not exist) | **82,045** |

Reconciliation: 45,932 bytes left the spec through the three block routes (24,609 + 16,870 + 4,453) and
2,235 more through the chronology route, for **48,167** removed; **5,732** bytes of framing were put back
(the header pointer, 13 per-Decision pointers, the surviving Risks rule, 15 new link definitions), for a
net **-42,435**. `190,961 - 42,435 = 148,526`. The companion is larger than the text it received because
it adds the header, the provenance section, 13 `Spec:` back-pointers, 13
`### Changes this Decision underwent` sections, the Non-Decision-deliberation section, and its own link
block.

### DRY check across prior accepted slices

No prior slice exists in this cycle; this is its first. No duplication introduced — see
`### DRY analysis`, including the one deliberate, bounded duplication between the verbatim
`## Revision history` block and the per-Decision change records.

### Focused test run

None called for: the plan adds no tests and the pass touches no `.py` file. Per `AGENTS.md`, `pytest` is
not run after edits unless asked, and no `--cov*` flag was used anywhere in this pass.

### Staged-anchor sweep

`grep -rn 'TODO(spec-031' .` → no matches. Nothing this pass shipped leaves a staged anchor, and none
exists to remove.

### Summary

The `031` rationale companion now exists, closing the `docs/SPECS/appx/` hole that made `031` the only
archived spec from `001`-`030` / `044`-`048` without one. `spec-031` lost its deliberative layer —
seven revisions of chronology, 13 justification blocks, 13 rejected-alternative blocks, the whole
risk/open-question body, and 82 embedded chronology tags — and reads as a clean current contract with a
pointer at each Decision. `check_spec_glossary` still reports `OK: 31 terms`; every anchor and link
definition in both files resolves; the `source-layout` hook passes on both. No spec-vs-code
reconciliation was performed — that is Slices 1-5's work, and what this pass noticed is handed forward
below.

### Spec changes made (Worker 1 only)

All edits are the move itself. Line ranges are pre-move (the spec's own numbering at HEAD `bc4ed00a`).

| Spec lines (pre-move) | Change | Reason |
| --- | --- | --- |
| 11 | `Revision history (kept inline so the spec is self-contained):` preamble **deleted** | The move falsifies its only claim; a false sentence belongs in neither file (`worker-1.md` rule 2). |
| 11 (replacement) | New paragraph naming the rationale companion | The move's header pointer, matching the `spec-030` header precedent. |
| 12-52 | Seven `Revision N` entries **moved** to the companion's `## Revision history` | Pure chronology — the deliberative layer the move exists to relocate. |
| 291-301, 311-314, 323-333, 347-357, 362-371, 383-394, 399-408, 436-451, 470-476, 492-504, 511-517, 522-525, 539-550 | Decisions 1-13's `Justification:` and `Alternatives considered (and rejected):` blocks **moved**, each replaced by a one-line `Rationale companion —` pointer | `docs/builder/BUILD.md` `## Spec rationale extraction`: every rejected alternative and its reason moves; every decision keeps a pointer. |
| 665-672 | `## Risks and open questions` body **moved**; heading kept, plus a pointer and the surviving derivation-baseline rule | A preferred-answer / fallback pair is a build-time deliberation instrument, not a contract (`spec-030` precedent). |
| 82 sites over 64 surviving lines | Chronology framing **removed**, recorded per Decision in the companion | The spec never narrates its own history. Contract sentences around each tag are unchanged. |
| link-definitions block | 15 defs added (`rationale-d1`…`rationale-d13`, `rationale-risks`, `spec-031-rationale`) | Targets for the header pointer and the 13 per-Decision pointers. |

Deferrals: none. No obligation of this pass is left open.

### Notes for Worker 1 (spec reconciliation)

Divergences noticed while reading. **None was fixed in this pass** — the maintainer's fence confines
Slice 0 to the move, and `docs/builder/BUILD.md` gives spec-vs-code reconciliation to the owning slice.
These are additional to the five the build plan's `## Build-wide context flags` already pre-verified.

1. **Spec-internal contradiction: `install_globalid_typename_resolver` arity.** The Slice-2 checklist
   spells `install_globalid_typename_resolver(type_cls, definition)` (two arguments) while
   `### Decision 10` and the shipped
   `django_strawberry_framework/types/relay.py::install_globalid_typename_resolver` both take
   `(type_cls, definition, globalid_setting)`. This is an unpropagated corner of the Revision-7
   delta-(a) snapshot work. **Owner: Slice 2.**
2. **`## Definition of done` item 1 is stale about the companion CSV.** It states the net-new
   `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` symbols "have **no** glossary heading yet … so
   they are intentionally absent from the CSV". Both headings now exist in `docs/GLOSSARY.md` and both
   terms are listed in `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-terms.csv` — which is precisely
   why `check_spec_glossary` reports 31 terms rather than 29. The companion's
   `## Risks and open questions` section records the same closure for the moved item 1. **Owner: Slice 5**
   (the CSV and `docs/GLOSSARY.md` themselves are out of fence — the *spec sentence* is not).
3. **`### Decision 1` asserts a location the archival convention falsified.** "The spec file lives at
   `docs/spec-031-globalid_encoding-0_0_9.md`" — it lives at `docs/SPECS/`, with its companions under
   `docs/SPECS/appx/`. The same stale `docs/spec-031-…` path appears in DoD item 1, DoD item 8, the
   Slice-5 checklist's `KANBAN.md` line, and the `## Doc updates` card-completion bullet. The reference
   -style `[spec-031]` def is correct; only the prose paths are wrong. Recorded in the companion under
   Decision 1 as a `**Post-ship:**` bullet. **Owner: Slice 5.**
4. **Two out-of-fence cross-references from `spec-032` now point into moved text.**
   `docs/SPECS/spec-032-full_relay-0_0_9.md` line 13 says a delta is "recorded in full in
   [`spec-031`][spec-031] Revision 7" — `spec-031` no longer has a Revision 7; the entry is in
   `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md#revision-history`. Line 452 quotes
   `spec-031` Decision 11's rejected alternative ("no shipped `0.0.9` consumer"), which now lives in the
   companion's `### Alternatives considered (and rejected)` for Decision 11; line 281's "recording the
   card's older name" likewise describes Decision 1's moved alternative. `spec-032` is out of this
   cycle's fence entirely. **Owner: maintainer / a future `032` cycle** — recorded here so the link rot
   is visible rather than silent.
