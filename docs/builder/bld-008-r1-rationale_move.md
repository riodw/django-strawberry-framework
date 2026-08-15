# Build: R1 — spec rationale extraction (spec-008)

Spec reference: `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` (whole file; the move touched lines 1, 68-241, 243-264, 279-341, and 399-494 of the HEAD version)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** Not applicable in the code sense — this item writes no Python and the
plan declares source read-only for the whole cycle with no docstring carve-out. The documentation
analogue was run instead: every `docs/SPECS/appx/spec-00N-…-rationale.md` sibling was enumerated and
`spec-005-django_type_contract-0_0_3-rationale.md` was read end to end for shape (opening paragraph,
`## How to read this file`, `## Provenance of this record`, `## Entries keyed to the spec`, the
`*Moved …*` / `*Claims the section no longer makes.*` idiom, and the ten-group link block). No
sibling's **content** was reused, per the plan's `### What R1 inherits` warning.

- **Existing patterns reused.** The spec-005 rationale's section shape and idioms
  (`docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`); the spec-005 / 006 / 007
  in-spec pointer convention — one companion-file paragraph directly under the H1, plus one-line
  per-section pointers (`docs/SPECS/spec-005-django_type_contract-0_0_3.md` line 3 and line 38 are
  the model). Both were followed rather than re-invented.
- **New helpers justified.** None. No script, constant, or fixture was added.
- **Duplication risk avoided.** The named risk is the plan's `**The scope trap specific to this
  spec**`: writing the rationale as a description of how `finalize_django_types()` works today, which
  would duplicate `spec-010`'s contract and the glossary's seven-phase list. The file states the
  prohibition in its own `## How to read this file` and cites `spec-010` / `spec-018` / `spec-019` /
  `spec-027` / `spec-028` / `spec-004` by reference at every point where restating them was
  tempting. The rationale contains no phase list, no `PendingRelation` field roster, no supported-
  relation-cycle roster, and no consumer call-site recipe — the last two being glossary-owned under
  `### Maintainer decision 2`.

### Implementation steps

Performed in this pass (this item's chain is plan-and-perform; see the plan's `### Deviation 2`).

1. Insert the companion-file pointer paragraph under the spec H1; add
   `[spec-008-rationale]` to the spec's `<!-- docs/SPECS/ -->` link group.
2. `## Prior art: Graphene-Django` — condense per `### Maintainer decision 1`. Move the source
   snapshot list, the ten key source references, `### Graphene-Django behavior` (lead-in + fenced
   example + skip note), `### Pros`, `### Cons`. Keep `### Relevance to this package` untouched.
3. `## Prior art: Strawberry-Django` — same treatment. Move the source snapshot list, the sixteen key
   source references, both mode subsections' bodies and the fenced example, `### Pros`, `### Cons`.
   Keep `### Relevance to this package` untouched.
4. `## Design options for this package` — move the "not a final implementation plan" paragraph and
   the whole of `### Decision criteria`.
5. `### Option 1` – `### Option 4` — move each section's Pros and Cons lists; keep each heading and
   its descriptive sentence.
6. Move `### Finalization trigger choices` whole (heading included).
7. Move `### Registry questions`, `### User annotation questions`, `### Generic fallback questions`,
   and `### Rich-schema dependency questions` whole (headings included).
8. Re-site the three glossary anchors whose carriers step 5, 6, or 7 removed.
9. Create `docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md` carrying the
   record, with every upstream citation converted to the `AGENTS.md` rule 27 symbol-qualified form.
10. Verify: `check_spec_glossary`, `check_trailing_commas --check`, disk-exists + anchor-resolves on
    every link definition, and a line-level presence sweep of every non-empty line the move removed.

### Test additions / updates

None. This item writes no Python and the plan declares no floor scope and no hot path. `pytest` was
not run in this pass and is not owed by it.

### Implementation discretion items

None delegated — this item has no Worker 2.

### Dispatched findings checklist

This is a residual item, not a spec slice, and spec-008 has no `## Slice checklist`. The boxes are
the item's own obligations, from the plan's `### Residual scope` R1 entry, `### What R1 inherits`,
`### Maintainer decision 1`, `### The 10-anchor surface`, and `worker-1.md`
`### Performing the rationale move`.

- [x] `docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md` created at the
  archived-companion location, never written to `docs/` first and moved.
- [x] The move is a cut-and-paste: every block that landed in the rationale left the spec.
- [x] `### Maintainer decision 1` implemented — condensed prior art stays in the spec (the two
  approaches and both `### Relevance to this package` borrow/avoid lists); the per-line source tours,
  the Pros/Cons lists, and the four-option comparison moved.
- [x] The condensation is the only new spec prose written by this item, beyond the companion pointer
  paragraph, the five one-line rationale pointers, and the three anchor re-sites.
- [x] Every decision that lost text keeps a one-line pointer naming what moved and where
  (`worker-1.md` rule 1).
- [x] Nothing was deleted outright (`worker-1.md` rule 2 — nothing in spec-008 is falsified by
  spec-008; see the rationale's `## Provenance of this record`).
- [x] Each rationale entry names the spec decision it serves **by heading and anchor**.
- [x] Each entry carries the alternatives rejected and why each lost.
- [x] Each entry carries every change the decision has undergone, naming the later card where one
  settled the question (`spec-018` at `0.0.6`, `spec-019` at `0.0.6`, `spec-027` / `spec-028` at
  `0.0.8`, `spec-004` at `0.0.3`, `spec-046` / `048` at `0.0.14`).
- [x] Each entry carries a `*Claims the section no longer makes.*` paragraph.
- [x] Drift row **D3** is recorded as its own entry — the spec's stated leading direction rejected by
  the implementation.
- [x] The four rejected relation-resolution designs are recorded; this is their only record anywhere.
- [x] No rejected alternative was fabricated: every one is quoted from the spec's own text.
- [x] All ten glossary anchors survive; `check_spec_glossary` re-run and quoted below.
- [x] `AGENTS.md` rule 27 established, not merely preserved: **zero** raw `path:NN` citations remain
  in either file.
- [x] `START.md` link convention: `<!-- LINK DEFINITIONS -->` block present with all ten canonical
  group headers in order, defs alphabetical within group, every path disk-exists-checked from
  `docs/SPECS/appx/`.
- [x] `check_trailing_commas.py --check` clean on both `.md` files written.
- [x] R2's demotions and the three sibling-sentence edits were **not** performed here.
- [x] No file outside this item's writable set was touched; nothing under `docs/review/` was read,
  restored, or reverted; no `git checkout`, no branch, no commit.

---

## Build report (Worker 2)

Not applicable. `docs/builder/BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role
that performs the move and states that Worker 2 never reads the rationale file; the plan's
`### Deviation 2` records the resulting `planned` → Worker 3 routing.

### Files touched

- `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` — the move's removals, the
  `### Maintainer decision 1` condensation of both prior-art openings, five one-line rationale
  pointers, three glossary-anchor re-sites, the companion-pointer paragraph under the H1, and one new
  link definition.
- `docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md` — created.
- `docs/builder/bld-008-r1-rationale_move.md` — this artifact.
- `docs/builder/worker-memory/spec-008-worker-1.md` — one appended entry.

### Byte and line counts

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-008-…-0_0_4.md` | 30,186 bytes / 603 lines / 6 fenced blocks | **19,578 bytes / 327 lines / 0 fenced blocks** | −10,608 bytes / −276 lines / −6 fences |
| `docs/SPECS/appx/spec-008-…-rationale.md` | absent | **41,604 bytes / 623 lines / 4 fenced blocks** | new |

The rationale is larger than the text it received, which is expected and is the point: `BUILD.md`
`## Spec rationale extraction` requires the file carry the **record** — outcome, the reason each
alternative lost, the later card that settled each question — not only the moved bytes.

**On "the majority of the file moves" (the plan's `### What R1 inherits`).** This pass moved 35% of
the spec, not a majority. That is not an under-cut: the remaining deliberation-shaped sections —
`### Hard invariants`, `### Proposed shape to evaluate`, `## Acceptance criteria`,
`### Failure criteria`, `## Fakeshop implication`, `## Cookbook implication` — are precisely the ones
`#### What R2 demotes from claim to rationale-plus-pointer` assigns to R2, and the prompt for this
item forbids performing those demotions. The majority does leave the spec across R1 + R2 combined;
R1 owns the extraction, R2 owns the demotion. The disposition of every section this pass left behind
is enumerated exhaustively in the rationale's `## Provenance of this record`, so R2 and Worker 3 can
both audit the line rather than infer it.

### Fence disposal

All six of the spec's fenced code blocks are accounted for, none deleted. Four moved with their
sections (the graphene-django class-order example, the strawberry-django explicit-annotation example,
and — counting the two one-line fences — the `registry.get_type_for_model(model)` call). The two
one-line fences were folded into the condensed prose as inline code spans rather than carried as
fences. The spec now has zero; the rationale has four.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-definition_order_independence-0_0_4.md`
  → **`OK: 10 terms - all have glossary entries and at least one spec link.`** (exit 0). Baseline was
  the same string, so the ten-anchor surface is unchanged.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md docs/SPECS/spec-008-definition_order_independence-0_0_4.md`
  → exit 0.
- Raw-citation sweep, both files:
  `grep -cE '[a-zA-Z_/]+\.(py|md):[0-9]+'` → **0** in the spec, **0** in the rationale.
- Link-definition sweep of the rationale: all 21 definitions resolved on disk from
  `docs/SPECS/appx/`, and all 12 in-page anchors resolved against the **post-edit** spec's headings.
  The masking trap named in the plan (`../README.md` from `appx/` landing on `docs/README.md`) does
  not apply — this file defines no `README.md` or root-level target at all, which is the safest
  disposition of it.
- Line-presence sweep: every non-empty, non-link-definition line of
  `git show HEAD:docs/SPECS/spec-008-…md` was tested individually for presence in the union of the
  post-edit spec and the rationale. The residue is 35 lines, each inspected by hand and each in one
  of four classes: (a) a converted citation, present in symbol-qualified form; (b) a list lead-in
  (`Source snapshot inspected:`, `Key source references:`, `Questions to settle:`,
  `Likely direction:`) whose items are all present; (c) a sentence the
  `### Maintainer decision 1` condensation rewrote, with every load-bearing fact preserved; (d) one
  of the three anchor re-sites or the two moved lines whose inline glossary link was stripped for the
  rationale. **No line's content was lost.** Four section-framing sentences were caught by this sweep
  as genuine misses on the first pass and were added to the rationale before it closed.
- `git status --short` after the edits: this item's four paths plus the thirty-one pre-existing
  baseline-dirty entries from other sessions, unchanged and untouched. Nothing under `docs/review/`
  was read or written.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The three anchor re-sites were done by link-form change on existing surviving sentences, never by
  new narration.** `### The 10-anchor surface` warns against a hollow section kept alive purely to
  host a link and against re-adding narration the pass just removed, so each anchor was moved onto a
  sentence that already named its concept in plain words:
  - `metafields` (was in Option 4's Pros) → `## Acceptance criteria`,
    `` - `Meta.fields = "__all__"` for bidirectional model graphs. `` became
    ``- [`Meta.fields`][glossary-metafields] `= "__all__"` for bidirectional model graphs.``
  - `schema-audit` (was in `### Generic fallback questions`) → `## Acceptance criteria`,
    `- schema audit behavior that distinguishes…` became
    `- [schema audit][glossary-schema-audit] behavior that distinguishes…`. Pure link-form change:
    zero words added or removed.
  - `metaprimary` (was in `### Registry questions`) → `## Acceptance criteria`,
    `` - `DjangoNodeField` can rely on finalized primary type metadata. `` became
    ``…can rely on finalized [`Meta.primary`][glossary-metaprimary] type metadata.``
  - `finalize_django_types` (was in `### Finalization trigger choices` approach 4) →
    `### Proposed shape to evaluate`, whose `Before schema construction:` lead-in became
    ``Before schema construction, in the [`finalize_django_types()`][glossary-finalize-django-types] pass:``.
    This is the one re-site that added words (four). It names the pass the surrounding seven-step list
    already describes, so it states no contract the section did not already carry — but it is the one
    of the four worth a reviewer's eye, and R2 may prefer a different host once it rewrites the
    section.
- **The two prior-art condensations state the failure mode, not only the mechanism.** The over-cut
  the condensation invites is dropping *why* each upstream approach was insufficient, leaving the
  surviving `### Relevance to this package` "parts to avoid" lists unmotivated. So the graphene-django
  condensation keeps the silent-field-skip consequence and its import-order corollary explicitly, and
  the strawberry-django condensation keeps all three generic-fallback mappings in prose — the shape of
  the fallback is what this package rejected as a default, and the rejection is unreadable without it.
- **`## Current strongest direction, not a final plan` was left entirely alone**, apart from removing
  its `### Finalization trigger choices` subsection. Its opening sentence is the only place the spec
  says which option won; moving it would have left the document with an option comparison and no
  outcome, which is the over-cut this item's review exists to catch. Its `### Hard invariants` and
  `### Proposed shape to evaluate` subsections are R2's to demote (drift row **D11** notes the former
  is easy to lose in a sweep, and `#### What R2 demotes…` reverses D11's provisional reading).
- **Citation conversion revealed structure the raw line numbers concealed.** All seven
  `strawberry_django/type.py` citations sit inside one function, `_process_type`; all three
  graphene-django `Dynamic(dynamic_type)` returns are the tails of the three relation converters. The
  symbol form makes both facts visible at a glance, which is the rule's actual payoff here rather than
  drift-resistance alone.
- **The upstream line numbers had NOT drifted** in either checkout, despite the plan's expectation
  that they "have certainly drifted". Every one of the twenty-five cited lines still lands on the
  construct the spec describes. That does not make the raw form permissible — rule 27 is not
  conditional on current accuracy — and it is recorded only so a later reader does not assume the
  conversion silently repaired a broken citation. It did not; it converted a correct one.

### Notes for Worker 3

- The rationale's `## Provenance of this record` is the audit surface for over-cut: it lists what
  moved, what was condensed, what was deliberately left in the spec (an exhaustive list), that
  nothing was deleted, how all six fences were disposed of, and how all ten anchors survived. Check
  the condensation against that section's second bullet first.
- Read the spec's two `### Relevance to this package` subsections against their new condensed
  openings. They were not edited, so any conclusion they draw that the condensation no longer
  supplies the premise for is an over-cut finding.
- The `### Finalization trigger choices` entry is the file's centre of gravity and the place a
  fabrication would be easiest to hide. Every quoted line in it is verbatim from
  `git show HEAD:docs/SPECS/spec-008-…md` lines 399-423; the paragraph beginning "Why approach 3 won
  over the hybrid" is explicitly labelled as reconstructed from what shipped rather than as recorded
  reasoning, because the spec records no such reasoning and inventing it was the trap.
- Verification commands are all in `### Validation run` and are cheap to re-run.

### Notes for Worker 1 (spec reconciliation)

R2 inherits these. Each was re-verified against source at HEAD in this pass rather than taken from
the plan's table.

**Drift-table corrections found.** Three rows are wrong or incomplete as written.

1. **D12's count is wrong, in both directions.** The plan states "**twenty-eight matches**" for
   `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` against the HEAD spec. Re-run: that grep returns
   **25 lines / 25 occurrences** (9 in `## Prior art: Graphene-Django`, 16 in
   `## Prior art: Strawberry-Django`). The *true* citation count is higher than either figure —
   **31** — because three lines carry bare continuation line numbers the regex cannot see
   (`` `342` ``, `` `381` `` on the converter line; `` `376` ``, `` `471` `` on the `Dynamic` line;
   `` `113` ``, `` `116` `` on the `utils/typing.py` line). All 31 were converted. R2 needs no action;
   the row is closed either way, but a later pass re-deriving the number should not expect 28.
2. **D14 under-reports the falsified fakeshop rows.** The row names `CategoryType.properties` as the
   relation with no `list[…]` form. `examples/fakeshop/apps/products/schema.py::PropertyType` carries
   **no `relation_shapes` key at all**, so `Property.entries` sits on the `0.0.14` `"connection"`
   default too and is likewise reachable only through `entriesConnection`. The corrected picture:
   of the spec's eight `## Fakeshop implication` rows, the four forward-FK rows (`Item.category`,
   `Property.category`, `Entry.item`, `Entry.property`) are unaffected; of the four many-side rows,
   **two** are falsified (`Category.properties`, `Property.entries`) and **two** hold because their
   owners carry explicit `relation_shapes = {"…": "both"}` opt-ins (`Category.items` on `CategoryType`,
   `entries` on `ItemType`). So "half the stated shapes are now wrong" is true of the many-side rows
   and false of the eight; six of eight still hold. The row's other two claims are confirmed: every
   one of the eight relations *is* exposed on a rich primary type, and `CategoryType` uses an explicit
   field tuple rather than `fields = "__all__"`.
3. **D6's closing instruction is unnecessary.** The row says "The cardinality-validation question is
   the one whose answer Worker 1 must read out of source rather than out of the glossary." It is in
   the glossary, stated in one sentence:
   `docs/GLOSSARY.md #"Validation that a manual relation annotation matches the Django relation cardinality is deferred"`.
   Source agrees — no cardinality validation exists on the relation path
   (`grep -rn 'cardinality' django_strawberry_framework/` hits only `filters/sets.py`, where the word
   means lookup arity in `django-filter` filter selection, an unrelated sense). This is the only one
   of spec-008's twenty-one settled questions whose answer is **still "deferred"**, and it is deferred
   explicitly rather than by omission. Recorded in the rationale's
   `### User annotation questions` entry.

**Rows re-verified and confirmed exactly as the plan states them**, each by direct grep or read at
HEAD, not by trusting the table: **D2** (`convert_relation` → 0 occurrences package-wide);
**D3** (no `finalize_django_types` call site outside its definition, re-exports, and docstrings;
`connection.py`, `relay.py`, and `schema.py::DjangoSchema` each contain none; `GOAL.md`'s own worked
example calls it by hand); **D4** (`schema.py::DjangoSchema` exists at `0.0.14` and installs
`DjangoMutationExecutionContext`; it does not finalize); **D5** (`_audit_primary_ambiguity`,
`_format_ambiguity_error`, `add_pending_relation` / `iter_pending_relations` / `discard_pending`,
`register_subsystem_clear` all present); **D7** (`DjangoModelType` → 0 occurrences; the glossary's
`## Schema audit` entry ignores hidden and `OptimizerHint.SKIP` fields); **D8** (`definition.py`
carries `filterset_class` / `orderset_class` / `fields_class` slots and **no** `aggregate_class` or
`search_fields` slot; `types/base.py::DEFERRED_META_KEYS` is exactly
`{"aggregate_class", "fields_class", "search_fields"}`); **D13** (`PendingRelationAnnotation` and its
`_PendingRelationAnnotationMeta.__repr__` sentinel exist as described).

**Two observations for R2 that are not drift rows.**

- **The `escape hatch` framing reaches further than `### Finalization trigger choices`.** The plan's
  `### Maintainer decision 2` warning names spec-008 lines 416-423. The phrase also sits in the
  *moved* approach-4 text and in `### User annotation questions`' likely-direction bullet ("preserve
  manual annotations as an escape hatch") and in `## Prior art: Strawberry-Django`'s surviving
  `### Relevance to this package` ("Explicit annotations should remain available as an escape hatch",
  spec line ~118 post-move). The last of those three is **correct as written** — a manual relation
  annotation genuinely is an override path, not the required call — so R2 should not sweep the phrase
  globally. Only the finalization-trigger sense is the inversion.
- **`## Decision context to preserve` was left untouched and is R2's call.** Its six bullets restate
  the two prior-art borrow/avoid conclusions at a higher altitude, so after the condensation it is the
  third telling of the same conclusion in one document. It is not deliberation by the ordinary test —
  every bullet is a conclusion — which is why this pass did not move it; but it is a live DRY question
  for the reconciliation, and the plan's `DRY rule` preamble ("a fact told twice across the spec and
  its rationale sibling goes stale in one of them") reaches the within-spec case just as well.

**Escalations inherited, not acted on.** The plan's `### Three conflicts found OUTSIDE the ownership
question` items 1-3 remain open and unactioned. Item 1 is confirmed still present at HEAD:
`django_strawberry_framework/types/relations.py` line 4 attributes the always-defer design to
**spec-014**, which is the testing-shift spec and owns neither half of it. Source is read-only in this
cycle; recorded, not fixed.

---

## Review (Worker 3)

Reviewed against `git show HEAD:docs/SPECS/spec-008-definition_order_independence-0_0_4.md`
(captured read-only to `/tmp/dsf-r1-spec-head.md`; no `git stash` / `checkout` / `restore` /
`worktree` was used). No `pytest`, no `--cov*`, no `scripts/review_inspect.py` (no `.py` touched).
Failability proofs, hot-path budget, and floor verification are all not applicable and are not
looked for, per the item's declared scope.

**The central question — is this an over-cut? — is answered no.** An independent line-level sweep of
all 603 HEAD lines against the union of the two post-edit files found no line whose content is
absent, and no contract that now exists nowhere. The findings below are all accounting and
prose-scope defects, not lost text.

### High:

None.

### Medium:

**M1 — Five wrong counts in durable prose, three of them in the very section the build report
nominates as "the audit surface for over-cut".** Severity is Medium rather than Low because
`## Provenance of this record` is the disposal proof: a later reader re-derives exactly these numbers
and will conclude the disposal was not measured. Each was re-derived mechanically here.

1. `docs/SPECS/appx/spec-008-…-rationale.md` line 36 — "The spec carried **twenty-eight** raw
   `path:NN` citations". The true count is **31**. This item's own
   `### Notes for Worker 1` correction 1 derives 31 and says "All 31 were converted"; the plan's
   `### Maintainer decision 1` also says "the thirty-one raw `path:NN` citations". The durable file
   is the one place still carrying the number this pass corrected. Re-derived: 13 in
   `## Prior art: Graphene-Django` (HEAD lines 81-89) + 18 in `## Prior art: Strawberry-Django`
   (HEAD lines 163-178) = 31, across 25 grep-visible lines. Fix: "thirty-one".
2. Rationale lines 74-77 and this artifact's `### Fence disposal` — "All **six** of the spec's fenced
   code blocks were disposed of… **Four** moved here… the **two** one-line fences". Ground truth,
   `grep -c '^\`\`\`'`: HEAD carries **6 fence delimiter lines = 3 fenced blocks** (93-95, 102-113,
   185-196); the rationale carries **4 delimiter lines = 2 blocks** (121-132, 203-214); the spec
   carries 0. Exactly **one** block — the one-line `registry.get_type_for_model(model)` call — was
   folded inline (spec line 73). The "two one-line fences" names a second one-line fence that never
   existed; the "Graphene relation-mode snippet" it points at is the 12-line class-order example,
   which *moved* rather than folding. **The substance is correct and independently verified — all
   three HEAD blocks are accounted for and none was deleted; only the arithmetic is wrong** (fence
   delimiter lines counted as blocks). Fix: "All three of the spec's fenced code blocks… Two moved
   here with their sections; the one one-line fence… The spec now carries none; the rationale carries
   two."
3. Rationale lines 78-82 — "All ten glossary anchors survive. **Three** sat inside text this pass
   moved", followed by a list of **four** (`Meta.fields`, `finalize_django_types`, `Meta.primary`,
   `schema audit`). Four is right — it matches the plan's `### The 10-anchor surface` table and the
   four re-sites this artifact's `### Implementation notes` enumerates. This artifact repeats "three"
   at four places (implementation step 8, checklist line 81, `### Files touched`, and
   `### Implementation notes`' lead-in, which then lists four bullets). Fix: "Four".
4. Rationale line 497 — "the only one of this spec's **twenty-one** settled questions". The four
   `### … questions` sections carry **19** questions: 6 (`### Registry questions`) + 4
   (`### User annotation questions`) + 4 (`### Generic fallback questions`) + 5
   (`### Rich-schema dependency questions`). Mechanical check: 19 lines ending in `?` in HEAD lines
   425-494. (20 if the finalization-point "main unresolved technical question" is counted; never 21.)
   The same figure is repeated in this artifact's `### Notes for Worker 1` correction 3.
5. `docs/SPECS/spec-008-…-0_0_4.md` lines 3 and 216 — "the **five** sets of open questions". HEAD has
   **four** `### … questions` sections, and line 216 then enumerates only four topics ("the registry,
   user annotations, generic fallback, and the rich-schema subsystems"). The rationale's own
   `## How to read this file` gets it right: "`### Finalization trigger choices` and the **four**
   `### … questions` sections". Both spec sentences are new prose written by this pass and are the
   pointers a reader follows first. Fix: "four".

### Low:

**L1 — The `finalize_django_types()` anchor re-site adds a claim in a section outside this item's
new-prose licence.** `docs/SPECS/spec-008-…-0_0_4.md` line 202: HEAD's neutral lead-in
`Before schema construction:` (HEAD line 385) became
``Before schema construction, in the [`finalize_django_types()`][glossary-finalize-django-types] pass:``.
HEAD deliberately left this open — the section removed in the same edit opens "The main unresolved
technical question is the Strawberry finalization point" — and the seven-step list below it is
trigger-agnostic. Naming the pass resolves, in the spec, the question whose weighing this pass moved
out. The statement is *true at HEAD* (approach 3 shipped; verified: `finalize_django_types(` has no
call site in `django_strawberry_framework/` outside `types/finalizer.py::finalize_django_types` and
error/doc strings), so this is a scope objection, not a correctness one. The build report already
flags it as "the one of the four worth a reviewer's eye", which is the right instinct.
Resolution paths for Worker 1: (a) revert the lead-in to `Before schema construction:` and host the
anchor on a surviving sentence that already names the pass, or (b) keep it and record it explicitly
in `### Notes for Worker 1` as a demotion R2 inherits rather than as a pure link-form change.

The same objection applies more weakly to line 236: HEAD's "`DjangoNodeField` can rely on finalized
**primary type** metadata" became "…finalized [`Meta.primary`][glossary-metaprimary] type metadata".
`Meta.primary` is the key HEAD described as *not yet existing* ("Can there be multiple `DjangoType`s
per model before `Meta.primary` exists?"), so the re-site narrows a generic bullet onto a specific
`Meta` key. It is accurate at HEAD and I would not hold the item on it; noted so R2 sees it.

**L2 — `docs/SPECS/spec-008-…-0_0_4.md` line 3: "the four candidate finalization triggers and the one
the implementation rejected".** The implementation rejected **three** of the four (approaches 1, 2
and 4) and adopted approach 3. What is meant is "the leading one the implementation rejected", which
line 216 states correctly ("the hybrid auto-finalization direction this spec named as leading"). As
written, the headline pointer paragraph reads as though three approaches survived. Suggested:
"…the four candidate finalization triggers, and the leading one the implementation rejected".

**L3 — `docs/SPECS/spec-008-…-0_0_4.md` line 73 strengthens a HEAD claim during condensation.**
HEAD line 97: "after **more modules** have had a chance to import and register their
`DjangoObjectType` classes." Condensed to "after **every module** has had a chance…". Graphene
resolves `Dynamic` when the consumer builds the schema, which is not a guarantee that every module
has imported — HEAD's weaker wording was the accurate one, and its weakness is load-bearing, since
the very next paragraph's failure mode is a target that *never* got imported by then. Restore
"more modules". This is the only claim-strengthening the condensation introduced; every other
surviving prior-art sentence checked out against both HEAD and the upstream checkouts (see
`### What looks solid`).

**L4 — `docs/SPECS/appx/spec-008-…-rationale.md` lines 192-195 misdescribe which three
`utils/typing.py` lines the spec cited.** The entry says "the three cited lines are its
`namespace = sys.modules[c.__module__].__dict__` read, its `is_classvar` filter, and its
`StrawberryAnnotation(v, namespace=namespace)` construction". HEAD line 174 cited **105, 113, 116** =
the `def get_strawberry_annotations` line, the namespace read, and the `StrawberryAnnotation`
construction. The `is_classvar` filter is line 115 and was never cited. The symbol-qualified citation
itself (`strawberry_django/utils/typing.py::get_strawberry_annotations`) is correct and covers all
three; only the parenthetical inventory is wrong.

**L5 — artifact-internal: checklist line 90 credits cards the rationale does not name.** It lists
"`spec-046` / `048` at `0.0.14`" among the later cards each entry names. Neither appears anywhere in
the rationale (`spec-004`, `-009`, `-010`, `-018`, `-019`, `-027`, `-028` do). Either the tick's
evidence list is stale, or a `relation_shapes`-at-`0.0.9`/`0.0.14` note the plan's
`### What R1 inherits` asked for was dropped. The latter is defensible — `## Fakeshop implication` is
the section `relation_shapes` falsifies and it stayed in the spec as R2's D14 item — but the
checklist should say so rather than cite cards that are not there.

### DRY findings

None blocking, and no existence challenge to raise: this item creates no abstraction, helper,
registry, or indirection layer.

Duplication was checked mechanically, not by eye. Every non-trivial line of the post-edit spec was
tested for verbatim presence in the rationale: **2 matches, both structural** (the shared heading
`## Current strongest direction, not a final plan` and the `<!-- django_strawberry_framework/ -->`
link-group comment). No sentence is told twice. The move is a move.

Two sub-line restatements exist and both are licensed and disclosed:

- The `auto`-mode fallback mappings appear as condensed prose in the spec (line 103) and as the
  verbatim moved table in the rationale (lines 216-220). Licensed by `### Maintainer decision 1`, and
  the rationale states the reason in place ("the rejection is unreadable without it"). Accepted.
- The graphene-django condensation (spec lines 73-75) paraphrases two entries of the `### Pros` list
  and one of the `### Cons` list now quoted verbatim in the rationale. Same licence, same disclosure.
  Accepted.

I concur with the build report's own DRY observation that `## Decision context to preserve` is now
the third telling of the two borrow/avoid conclusions, and with its judgement that resolving it is
R2's call rather than R1's — every bullet in it is a conclusion, so the ordinary deliberation test
does not reach it.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list
are unchanged. Consistent with the item's Definition of Done: no new public exports, no source file
touched at all.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; this slice does not touch `CHANGELOG.md`.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Applicable — the item writes one archived spec and creates one archived companion.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-definition_order_independence-0_0_4.md`
  → **`OK: 10 terms - all have glossary entries and at least one spec link.`** (exit 0). Independently
  re-run; matches the build report's quotation. The ten-anchor surface holds.
- `uv run python scripts/check_trailing_commas.py --check` on both `.md` files → **exit 0**, no output.
- `AGENTS.md` rule 27: independent regex `[A-Za-z0-9_/.-]+\.(py|md|txt|toml|cfg|json):[0-9]+` →
  **0 matches in the spec, 0 in the rationale.** Rule 27 is established, not merely preserved.
- `START.md` link convention: both files carry `<!-- LINK DEFINITIONS -->` and all **10** canonical
  group headers in the exact prescribed order; defs are alphabetical within group (checked
  `spec-008` < `spec-008-acceptance` < … < `spec-008-strawberry` < `spec-009`). All 10 rationale def
  paths disk-exist resolved from `docs/SPECS/appx/`, including the two depth-sensitive ones
  (`../../GLOSSARY.md` → `docs/GLOSSARY.md`, `../../builder/BUILD.md` → `docs/builder/BUILD.md`). The
  masking trap does not apply: the rationale defines no `README.md` or root-level target, so no
  `../README.md`-resolving-to-`docs/README.md` shadow exists. Archived companions correctly sit under
  `<!-- docs/SPECS/ -->` per START.md's closed-list rule.
- In-page anchors: all **11 distinct** (12 uses) `spec-008-…md#…` anchors in the rationale were
  slugged against the **post-edit** spec's headings — all resolve. No anchor points at a heading this
  pass removed.
- Generated docs (`docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md`) correctly untouched by this pass;
  `docs/GLOSSARY.md`'s dirty state is baseline, from another session.

### What looks solid

Verified independently, not accepted from the build report:

- **Counts re-derived.** HEAD spec 30,186 bytes / 603 lines; post-edit spec **19,578 / 327**;
  rationale **41,604 / 623**. Byte and line figures are exactly as claimed. Fence *blocks* are
  3 → 0 (spec) and 2 (rationale); see M1.2 for the delimiter-line/block confusion.
- **The move is a cut-and-paste, proven line by line.** All 603 HEAD lines (excluding link
  definitions and HTML comments) were tested for content presence in the union of the two post-edit
  files. Residue falls entirely into the four classes the build report names — converted citations,
  list lead-ins whose items all survive, sentences the Decision-1 condensation rewrote, and the
  anchor re-sites / link-stripped quotations. **Nothing that reads as contract now exists nowhere.**
  The two blocks I probed hardest for over-cut both survive adequately: the removed
  "This section is not a final implementation plan" disclaimer is still carried by the surviving
  heading `## Current strongest direction, not a final plan` and its "should not be treated as a
  finalized implementation plan yet" sentence; and the 13 `### Decision criteria` are covered as
  contract by the surviving `### Hard invariants` and `### Failure criteria`, with only the two
  purely-preferential ones ("works with Strawberry's type lifecycle instead of fighting it",
  "avoids fragile post-schema mutation…") now living solely in the rationale — which is where a
  judgement yardstick belongs.
- **"The upstream line numbers had NOT drifted" — confirmed, all 31.** I re-read every citation in
  both checkouts. All 15 graphene-django/graphene citations and all 19 strawberry-django citations
  (31 citations, 25 lines, some lines carrying several) land on the construct the spec describes.
  This was the cheapest claim in the report to assert and it holds.
- **The symbol-qualified conversions are accurate, including the two structural claims they enable.**
  `graphene_django/types.py:222` and `:264` are both inside
  `DjangoObjectType.__init_subclass_with_meta__` (the only enclosing def before line 266);
  `graphene/types/schema.py:308-310` is inside `TypeMap.create_fields_for_type` (class `TypeMap` at
  line 87, method at 303); the three `return Dynamic(dynamic_type)` lines (336/376/471) are the tails
  of `convert_onetoone_field_to_djangomodel` (274), `convert_field_to_list_or_connection` (342) and
  `convert_field_to_djangomodel` (381) respectively, and the rationale's per-converter Django field
  lists are right — including `ManyToManyField` on the middle one, which is a decorator the spec's
  raw citation never showed. All **seven** `strawberry_django/type.py` citations do sit inside one
  function: `_process_type` is the only `def` before line 420.
- **No rejected alternative was fabricated.** Every quoted `### Pros` / `### Cons` / question /
  "Likely direction" block matches HEAD verbatim (only double→single quote nesting differs), and the
  whole `### Finalization trigger choices` quotation matches HEAD lines 400-423 exactly. The one
  passage that is *not* recorded reasoning — "Why approach 3 won over the hybrid" — is explicitly
  labelled as reconstructed from what shipped. That labelling is the right call and is what stopped
  this from being a fabrication.
- **`BUILD.md` `## Spec rationale extraction` clauses are populated.** 9 entries, each naming its
  spec section **by heading and anchor** (the 5 whose headings no longer exist anchor the nearest
  surviving section and say so). 9 of 9 carry a `*Claims the section no longer makes.*` paragraph.
  "Alternatives rejected and why each lost" is genuinely populated — the `### Option 1` through
  `### Option 4` entry is the only record of the three rejected designs anywhere in the repo, and the
  `### Finalization trigger choices` entry records the spec's own leading direction losing.
- **Every source-backed claim in the rationale checks out at HEAD.**
  `types/finalizer.py::_audit_primary_ambiguity` (line 131), `::_format_ambiguity_error`,
  `::_format_unresolved_targets_error` (line 86); `types/relations.py::PendingRelation` (28),
  `::PendingRelationAnnotation` (75) with `_PendingRelationAnnotationMeta` (59);
  `registry.py::TypeRegistry.add_pending_relation` (508) / `iter_pending_relations` /
  `discard_pending` / `register_subsystem_clear`; `connection.py::_finalize_queryset` (the unrelated
  name collision, real); `DjangoModelType` → **0** occurrences package-wide;
  `types/base.py::DEFERRED_META_KEYS` is exactly `{"aggregate_class", "fields_class",
  "search_fields"}`; `types/definition.py` carries `filterset_class` / `orderset_class` /
  `fields_class` slots (161-163) and **no** `aggregate_class` or `search_fields` slot; the
  "each one's feature ships in the same card that adds it, so they were never
  reserved-but-nonfunctional" convention really is a comment beside `ALLOWED_META_KEYS`
  (`types/base.py` #"never reserved-but-nonfunctional"); `docs/README.md` "## Schema setup boundary"
  exists; `GOAL.md` calls `finalize_django_types()` by hand; the glossary carries
  `` ## `finalize_django_types` ``; spec-010's inbound sentence
  #"discusses the relation-resolution problem space and prior art at length" is exact.
- **The three drift-table corrections were re-verified independently, and all three stand.**
  (a) 31 citations / 25 grep lines, as above. (b)
  `examples/fakeshop/apps/products/schema.py::PropertyType` carries **no** `relation_shapes` key —
  read directly — while `CategoryType` opts in `{"items": "both"}` and `ItemType` opts in
  `{"entries": "both"}`. So two of the four many-side rows are falsified (`Category.properties`,
  `Property.entries`) and six of the eight `## Fakeshop implication` rows still hold. (c)
  `docs/GLOSSARY.md` #"Validation that a manual relation annotation matches the Django relation
  cardinality is deferred" exists verbatim, and a second statement of the same deferral sits in the
  `## Definition-order independence` limitations list.
- **The spec-009 escalation is real.** `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  `### Layer 3: Finalization trigger` does carry the heading "Preferred triggers:" over the same four
  never-shipped auto-finalization items. Correctly escalated rather than fixed (`### Maintainer
  decision 6` defers it).
- **Lane discipline holds.** `git status --short` carries 36 entries; exactly four belong to this
  cycle (`M` the spec, `??` the rationale, `??` this artifact, `??` Worker 0's plan), leaving 32
  baseline-dirty — nothing in that set differs from HEAD in any way this pass caused, nothing under
  `docs/review/` was written, no sibling spec, no source file, no test, no other cycle's artifact was
  touched. `docs/builder/worker-memory/` is gitignored, which is why the appended Worker 1 memory
  entry does not appear in status.

### Temp test verification

None created. `docs/builder/temp-tests/spec-008-r1/` was not used — every claim in this item is
verifiable by read, grep, and the two repo check scripts, and a temp test would have proved nothing a
`git show HEAD:` diff does not.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: `docs/builder/build-008-…md` `## Baseline-dirty out-of-scope files` says "Thirty-one
  entries at pre-flight" but enumerates 32 and the tree carries 32.** Nothing was reverted or edited
  either way; recorded only so a later pass re-deriving the number does not read the discrepancy as
  drift it caused. Worker 0 owns that list; no worker edits it.
- **Escalated (source observation, no action taken — source is read-only this cycle):** the rationale
  asserts "Nothing in the package auto-finalizes", which I verified is true of call sites. But
  `django_strawberry_framework/testing/relay.py` #"call finalize_django_types() (or build the schema)
  first" tells a consumer that *building the schema* is an alternative trigger, which is the same
  inversion `### Maintainer decision 6` defers for spec-009. It is a shipped, consumer-visible
  message rather than a spec sentence. Resolution paths: fold it into the decision-6 deferral, or
  card it separately.
- The **M1** count fixes are all in files only Worker 1 may write, which is the reason this item
  routes back to Worker 1 rather than Worker 2 (plan `### Deviation 2`). Four of the five are
  one-word edits; M1.2 needs the `### Fence disposal` paragraph in this artifact corrected too.
- **L1** is a genuine judgement call about where R1's licence ends and R2's demotion begins, not a
  defect I can decide. Either resolution path is acceptable to me; I would not re-open the review on
  the choice, only on it being left undocumented.

### Review outcome

**`revision-needed`**, on **M1** alone (five re-derived count errors in durable prose, three of them
in the disposal-proof section) plus **L1-L5**. No High findings. The move itself is sound: no
over-cut, no fabrication, no copy-instead-of-move, no lane violation, all ten anchors intact, rule 27
established, both check scripts clean, and every upstream citation and source claim verified
independently. What is wrong is the arithmetic wrapped around a correct move — which is exactly the
class of claim `BUILD.md` `## Claims are proven mechanically, never accepted on prose` exists to
catch, and it is cheap to fix.

Re-review scope on the next pass: the five corrected numbers, the L1 disposition, and L2-L4's three
sentence fixes. Nothing else needs re-walking.

---

## Build report (Worker 1, pass 2 — apply changes)

Applies Worker 3's **M1** (five counts) and **L1**-**L5**. No other change. R2's demotions were not
performed. Files written: the spec, the rationale, this artifact, the Worker 1 memory file — nothing
else. No `git stash` / `checkout` / `restore` / `worktree`; no branch; no commit; no `pytest`.

**Why the prior Plan and Build report blocks are byte-unchanged.** `ARTIFACT.md` `## Re-pass sections`
forbids editing prior entries, and Worker 3's review quotes those blocks by line number — silently
rewriting the numbers it cites would make the review unreadable and destroy the audit trail that is
the point of the correction. So every artifact-internal number Worker 3 flagged is corrected **here**,
in a superseding table, and the durable files (spec + rationale) are corrected in place.

### Corrections to this artifact's earlier prose (superseding; the earlier blocks stand as written)

| Site in the pass-1 blocks | As written | Corrected | Unit / derivation |
|---|---|---|---|
| `### Fence disposal` (whole paragraph) | "All six of the spec's fenced code blocks… Four moved… the two one-line fences" | **All three** fenced blocks; **two** moved with their sections; **one** one-line fence folded inline; spec now 0, rationale 2 | `grep -c '^\`\`\`'` counts **delimiter lines**: HEAD 6, rationale 4, spec 0. Blocks = delimiters / 2 → 3 / 2 / 0. HEAD blocks at lines 93-95, 102-113, 185-196; the folded one is 93-95 |
| Byte-and-line table, "fenced blocks" column | "6 fenced blocks" / "−6 fences" / rationale "4 fenced blocks" | HEAD **3 blocks** / spec **0** (−3) / rationale **2** | same derivation |
| Implementation step 8, checklist box "All ten glossary anchors survive", `### Files touched`, `### Implementation notes` lead-in | "the **three** glossary anchors" / "three anchor re-sites" | **four** | `metafields`, `schema-audit`, `metaprimary`, `finalize-django-types` — the four the `### Implementation notes` bullets themselves enumerate, matching the plan's `### The 10-anchor surface` table |
| Checklist box crediting later cards (`spec-046` / `048` at `0.0.14`) | "…`spec-046` / `048` at `0.0.14`" | the cards the rationale actually names are `spec-004` (`0.0.3`), `spec-018` / `spec-019` (`0.0.6`), `spec-027` / `spec-028` (`0.0.8`), `spec-009`, `spec-010` | `grep -c 'spec-046\|spec-048' <rationale>` → **0**. The `relation_shapes` note the plan asked for was deliberately not written into the rationale: `## Fakeshop implication` is the section `relation_shapes` falsifies and it stayed in the spec as R2's D14 item, so the record belongs to R2's pass, not this one |
| `### Notes for Worker 1` correction 3 | "twenty-one settled questions" | **nineteen** | see the re-derivation table below |
| `### Notes for Worker 1` correction 1 | "25 lines / 25 occurrences… true count 31" | stands as written | re-derived independently below; this one was right |

### Every number re-derived this pass, with its unit and command

Run against `git show HEAD:docs/SPECS/spec-008-definition_order_independence-0_0_4.md > /tmp/dsf-r1-head.md`
(read-only capture; no `git stash` / `checkout` / `restore` / `worktree`).

| Claim | Unit | Command | Result |
|---|---|---|---|
| raw `path:NN` citations in HEAD | **occurrences** | `grep -oE '[a-zA-Z_/]+\.(py\|md):[0-9]+' /tmp/dsf-r1-head.md \| wc -l` → 25, plus the bare backticked continuation integers on HEAD lines 85 (`342`, `381`), 86 (`376`, `471`) and 174 (`113`, `116`), read by hand = +6 | **31** (25 grep-visible + 6 continuations, across **25** lines) |
| the same, per section | occurrences | HEAD 81-89 = 9 + 4; HEAD 163-178 = 16 + 2 | **13** graphene + **18** strawberry = 31 |
| fenced blocks, HEAD / spec / rationale | **blocks** (= delimiter lines / 2) | `grep -c '^\`\`\`'` → 6 / 0 / 4 | **3 / 0 / 2** |
| settled questions | **questions** (lines ending `?`) | `sed -n '425,494p' /tmp/dsf-r1-head.md \| grep -c '?$'` | **19** = 6 registry + 4 user-annotation + 4 generic-fallback + 5 rich-schema |
| sets of open questions | **`### … questions` headings** | `grep -c '^### .*questions' /tmp/dsf-r1-head.md` | **4** (425, 444, 461, 477). `### Finalization trigger choices` poses its alternatives as numbered statements, not questions, and contributes none |
| glossary anchors sitting inside moved text | **anchors** | the four re-sites enumerated in pass 1's `### Implementation notes` | **4** |
| `### Decision criteria` bullets | bullets | `sed -n '/^### Decision criteria/,/^### Features/p' /tmp/dsf-r1-head.md \| grep -c '^- '` | **13** (unchanged; the pass-1 figure was right) |
| of those, prohibitions | bullets | `… \| grep -c '^- avoids'` → 3, plus three positively-worded prohibitions read by hand | **6** — now spelled out in the rationale so the reader re-derives instead of trusting |
| post-edit spec | bytes / lines | `wc -c -l` | **19,612 / 327** (was 19,578 / 327) |
| post-edit rationale | bytes / lines | `wc -c -l` | **42,265 / 630** (was 41,604 / 623) |

Both figures the pass-1 table gave for HEAD are confirmed: **30,186 bytes / 603 lines**.

### Findings and their resolution

**M1.1 — "twenty-eight raw `path:NN` citations"** → **thirty-one**, in the rationale's
`## How to read this file`. The sentence now carries its own unit ("25 of them the only citation on
their line, and six more riding as bare backticked continuation integers on three of those lines,
which is why a line-counting grep sees only 25"), so the next reader re-derives rather than trusts.

**M1.2 — the fence arithmetic** → the rationale's `## Provenance of this record` bullet now reads
"All three of the spec's fenced code blocks…, two moved here…, the one one-line fence…, the spec now
carries none and this file carries two", and states the unit trap in place: `grep -c '^\`\`\`'`
counts delimiter lines and a block is two of them. **The substance was already correct** — Worker 3's
independent sweep and my own re-check agree all three HEAD blocks are accounted for and none was
deleted. Only the arithmetic changed.

**M1.3 — "Three anchors sat inside text this pass moved"** → **Four**, in the same section; the
parenthetical already listed four.

**M1.4 — "twenty-one settled questions"** → **nineteen**, in the
`### User annotation questions` entry.

**M1.5 — "the five sets of open questions"** (spec lines 3 and 216) → **four**, at both sites.
**Reading chosen and held across both files: four**, on the ground that a "set of open questions" is
a `### … questions` section and there are four of them; line 216 already enumerated exactly those
four topics, and the rationale's `## How to read this file` already said four. `### Finalization
trigger choices` is not counted — it asks nothing, it lists four numbered candidate triggers, and the
same two sentences already account for it separately as "the four candidate finalization triggers".

**L1 — the `finalize_django_types()` re-site.** Resolved by a **third path**, because Worker 3's
path (a) is not available: `grep -n 'finalize_django_types' /tmp/dsf-r1-head.md` returns HEAD lines
407 and 421 **only**, both inside `### Finalization trigger choices`, which this pass moved. No
surviving spec sentence names the pass, so *every* host adds the name and there is no "sentence that
already names the pass" to move it onto. Path (b) — keep the claim and label it — leaves a resolved
trigger question sitting in a normative section, which is the actual objection.

So: spec line 202 is **restored to HEAD's trigger-neutral `Before schema construction:`**, and the
anchor moved to line 216 — this pass's own rationale-pointer sentence, whose entire job is to
describe the moved deliberation: "The four candidate finalization triggers weighed here — the
explicit `finalize_django_types()` call among them — …". That names the pass as *one of the four
weighed candidates*, which is exactly what the moved text says, and asserts nothing about which one
won or about where the seven proposed steps run. The normative `### Proposed shape to evaluate` list
is byte-identical to HEAD again; the anchor survives, as `### The 10-anchor surface` binds it to
(`check_spec_glossary` re-run: `OK: 10 terms`).

The weaker `Meta.primary` instance (spec line 236) is **kept as-is and recorded**, not reworked. Same
grep result applies — `Meta.primary` appears in HEAD only at line 430, inside a moved question — so
no neutral host exists there either, and unlike L1 the host bullet is an acceptance-criterion whose
subject genuinely *is* the primary-type metadata the key now names. Worker 3 explicitly would not
hold the item on it. Recorded under `### Notes for Worker 1` below as an R2-inherited item rather
than left as a silent link-form change.

**L2 — "the one the implementation rejected"** → "the **leading** one the implementation rejected"
(spec line 3), matching line 216's already-correct "the hybrid auto-finalization direction this spec
named as leading". Three of the four were rejected; one was rejected *as the spec's own leading
direction*, which is the fact worth pointing at.

**L3 — the strengthened Graphene claim** → spec line 73 restored to HEAD's "after **more modules**
have had a chance to import and register **their** `DjangoObjectType` classes". Worker 3 is right
that the weakness is load-bearing: the next paragraph's failure mode is a target that never got
imported by then, which "every module" would contradict.

**L4 — the `utils/typing.py` parenthetical** → "its `def` line, its
`namespace = sys.modules[c.__module__].__dict__` read, and its `StrawberryAnnotation(...)`
construction". Verified against the checkout: line 105 is
`def get_strawberry_annotations(cls) -> dict[str, StrawberryAnnotation]:`, 113 the namespace read,
116 the `StrawberryAnnotation` construction; `is_classvar` is line **115** and was never cited.

**L5 — the checklist's card credit** → corrected in the superseding table above rather than by
editing the pass-1 checklist box, per `ARTIFACT.md` `## Re-pass sections`. `spec-046` / `spec-048`
appear **0** times in the rationale; the cards it does name are recorded in the table.

### One further defect found while re-deriving (not in Worker 3's list)

`### Decision criteria`'s entry asserted "**Six** of the thirteen are stated as prohibitions" and
then exemplified **four**. Same signature shape as M1: a structural count asserted in narrative prose
with no derivable unit. Six is defensible but only under a reading the sentence never gave, so the
sentence now names all six explicitly — the three worded `avoids …` (`grep -c '^- avoids'` → 3) and
the three that state the same prohibition positively. The count is unchanged; it is now re-derivable.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-definition_order_independence-0_0_4.md`
  → **`OK: 10 terms - all have glossary entries and at least one spec link.`** (exit 0). Unchanged
  from the pass-1 baseline, so the L1 re-site did not cost an anchor.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-008-definition_order_independence-0_0_4.md docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md`
  → **exit 0**, no output.
- Rule-27 sweep, **occurrences** not lines,
  `grep -oE '[A-Za-z0-9_/.-]+\.(py|md|txt|toml|cfg|json):[0-9]+' <file> | wc -l`
  → **0** in the spec, **0** in the rationale.
- `git status --short`: this cycle's four paths plus the baseline-dirty entries from other sessions,
  untouched. Nothing under `docs/review/`, no sibling spec, no source, no test, no other cycle's
  artifact.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Notes for Worker 1 (spec reconciliation)

R2 inherits these, in addition to everything pass 1 recorded (all of which still stands).

- **The `Meta.primary` re-site on spec line 236 is a demotion, not a pure link-form change.** HEAD
  read "finalized primary type metadata"; it now reads "finalized [`Meta.primary`] type metadata",
  which narrows a generic acceptance-criterion onto a specific `Meta` key HEAD described as not yet
  existing. Accurate at HEAD-of-package, and no neutral host exists. R2 may prefer a different host
  when it rewrites `## Acceptance criteria`; if it does, the `metaprimary` anchor must land somewhere
  else in the same edit — all ten anchors are binding.
- **Spec line 216 now carries the `finalize_django_types` anchor.** If R2 rewrites or removes that
  pointer sentence, it owns re-siting the anchor. Same constraint.
- The escalations pass 1 recorded are unchanged and unactioned: the `types/relations.py` spec-014
  misattribution, the `testing/relay.py` "or build the schema" inversion, the build plan's
  thirty-one-vs-32 baseline-dirty discrepancy, and the `## Decision context to preserve` DRY question.

---

## Final verification (Worker 1)

Slice-local final checks for R1 only. No in-context memory of the earlier passes; the artifact and the
working-tree diff were the contract, and every count below was **re-derived**, never read off a prior
table. No `git stash` / `checkout` / `restore` / `worktree`; no branch; no commit; no `pytest`
(none owed — the item writes no Python and the plan declares no floor scope and no hot path).

**Scope taken as settled from the prior passes**, per this pass's brief: the over-cut question. Worker
3 swept all 603 HEAD lines against the union of the two post-edit files and found no lost content, no
fabricated alternative, no High finding. Not redone.

### Checks re-run, with results quoted

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-definition_order_independence-0_0_4.md`
  → **`OK: 10 terms - all have glossary entries and at least one spec link.`**, exit 0. The
  `### The 10-anchor surface` obligation holds after the L1 re-site.
- `uv run python scripts/check_trailing_commas.py --check` on
  `docs/SPECS/spec-008-…-0_0_4.md`, `docs/SPECS/appx/spec-008-…-rationale.md`, and
  `docs/builder/bld-008-r1-rationale_move.md` → **exit 0**, no output. Run over all three in one
  invocation, the artifact included.
- Rule-27 sweep, **occurrences** not lines:
  `grep -oE '[A-Za-z0-9_/.-]+\.(py|md|txt|toml|cfg|json):[0-9]+' <file> | wc -l`
  → **0 occurrences** in the spec, **0 occurrences** in the rationale. (The artifact is exempt —
  `START.md` "Temp artifact conventions" lists `docs/builder/bld-*.md` as a per-cycle scratchpad where
  raw `path:NN` is licensed. Both durable files are held to the rule and both are clean.)

### Counts re-derived, with the unit stated

`wc -c -l` gives bytes and lines; `grep -c '^\`\`\`'` gives fence **delimiter lines**, and a fenced
block is two of them, so blocks = delimiters / 2. HEAD captured read-only with
`git show HEAD:docs/SPECS/spec-008-definition_order_independence-0_0_4.md > /tmp/dsf-r1-head.md`.

| File | bytes | lines | fence delimiter lines | fenced **blocks** |
|---|---|---|---|---|
| post-edit spec | **19,612** | **327** | 0 | **0** |
| post-edit rationale | **42,265** | **630** | 4 | **2** |
| HEAD spec (`/tmp/dsf-r1-head.md`) | **30,186** | **603** | 6 | **3** |

Every figure matches pass 2's table and Worker 3's independent re-derivation. The spec is 35% smaller
by bytes; the rationale is larger than the text it received, which is the point — it carries the
record, not only the moved bytes.

### Contract audit: R1 delivered, and only R1

- **`### Maintainer decision 1` honored.** Condensed prior art stays in the spec: both
  `## Prior art: …` openings and both `### Relevance to this package` borrow/avoid lists are present
  (spec lines 70-97 and 98-126). The per-line source tours, the Pros/Cons lists, and the four-option
  comparison are all gone from the spec and all present in the rationale.
- **R2's work did NOT land.** The spec still carries every section
  `#### What R2 demotes from claim to rationale-plus-pointer` assigns to R2, none demoted:
  `### Hard invariants` (174), `### Proposed shape to evaluate` (186), `## Acceptance criteria` (218),
  `### Failure criteria` (242), `## Fakeshop implication` (253), `## Cookbook implication` (267),
  `## Decision context to preserve` (286). None of the five authorized sibling-spec edits landed:
  `git status --short` shows `spec-001`, `spec-009`, and `spec-010` absent — untouched — and
  `django_strawberry_framework/types/relations.py` is not dirty, so the `spec-014` misattribution is
  still open exactly as pass 1 recorded it.
- **All ten glossary anchors survive**, per `check_spec_glossary` above. The four re-sites resolve at
  spec lines 216 (`finalize_django_types`), 224 (`Meta.fields`), 227 (`schema audit`), 236
  (`Meta.primary`), and all ten `[glossary-…]` definitions are present and contiguous in the link
  block at spec lines 301-310.
- **Every rationale entry names its spec decision by heading and anchor.** Nine entries under
  `## Entries keyed to the spec`, each opening with a `Spec:` or `Bears on` line carrying a
  reference-style link; the twelve `spec-008-…` in-page anchors all slug against **surviving**
  post-edit headings (`#acceptance-criteria`, `#current-strongest-direction-not-a-final-plan`,
  `#design-options-for-this-package`, `#features-that-depend-on-this-decision`,
  `#option-1-keep-eager-resolution` … `#option-4-…`, `#prior-art-graphene-django`,
  `#prior-art-strawberry-django`, `#proposed-shape-to-evaluate`). No entry is unlookupable.
- **`*Claims the section no longer makes.*` — 9 of 9 entries carry it.** Recorded because I nearly
  logged a false defect here: a `grep -c 'Claims the section no longer makes'` returns **8**, because
  the `### Option 1` through `### Option 4` entry covers four sections and correctly pluralises to
  `*Claims the sections no longer make.*` (rationale line 347). The count unit is *entries carrying the
  paragraph*, not *occurrences of one exact string* — the same unit-mismatch signature this cycle has
  now produced seven times. Worker 3's "9 of 9" stands.
- **All 21 rationale link definitions and all 11 spec link definitions disk-exist** as resolved from
  their own directories, including the depth-sensitive `../../GLOSSARY.md` and `../../builder/BUILD.md`.
- **Dispatched findings checklist audited.** Every `- [x]` is true as of this diff. Two boxes carried
  wrong detail in pass-1 prose — the "three anchor re-sites" (four) and the `spec-046` / `048` card
  credit (the rationale names `spec-004`/`-009`/`-010`/`-018`/`-019`/`-027`/`-028`) — and both are
  already corrected in pass 2's superseding table, which is the correct handling under `ARTIFACT.md`
  `## Re-pass sections`. No box is silently un-ticked and none is ticked without a landed contract.
- **Lane discipline.** `git status --short` carries **38** entries; exactly four are this cycle's
  (`M` the spec, `??` the rationale, `??` this artifact, `??` Worker 0's plan). The other 34 are
  baseline-dirty from concurrent sessions — including `django_strawberry_framework/_request_body.py`,
  which appeared after the plan's growth record was written. None was edited, reverted, or read for
  content. Nothing under `docs/review/` was touched. No source, no test, no example, no sibling spec,
  no durable doc, no other cycle's artifact.

### Summary

R1 shipped the spec-008 rationale extraction: `docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md`
now carries the deliberative layer — both upstream source tours, both Pros/Cons weighings, the thirteen
decision criteria, the four candidate designs and why three lost, the four candidate finalization
triggers and the leading direction the implementation rejected, and the four sets of open questions
with the answer each eventually received — and the spec is 30,186 → 19,612 bytes (603 → 327 lines,
3 → 0 fenced blocks) of clean current contract with five one-line rationale pointers, a companion-file
pointer under the H1, and all ten glossary anchors intact. The move is a cut-and-paste, verified line
by line across all 603 HEAD lines. R2's demotions and the five sibling-spec edits were deliberately
not performed.

Final status: **`final-accepted`**.

### Spec changes made (Worker 1 only)

`docs/SPECS/spec-008-definition_order_independence-0_0_4.md`. **Every range below was re-derived from
`git diff -U0` against HEAD in this pass, not carried forward** — the pass-1 list cited approximate
ranges that swept in unchanged heading and blank lines either side of each hunk, and one row (HEAD
line 388) described an edit that the L1 fix reverted. Cited lines are HEAD lines; the trailing arrow
gives the post-edit spec line.

- **insertion after HEAD line 2 → spec line 3** — companion-file pointer paragraph. Reason: a decision
  that lost text keeps a pointer naming what moved and where (`worker-1.md` rule 1). Triggered by R1's
  `### Residual scope` entry. Carries Worker 3's **L2** fix: "the **leading** one the implementation
  rejected", and the **M1.5** reading, "the **four** sets of open questions".
- **HEAD lines 71-106 and 109-129 → spec lines 73-77** — `## Prior art: Graphene-Django` condensed:
  source snapshot list, ten key source references, `### Graphene-Django behavior` with its class-order
  example, `### Pros`, `### Cons` all moved; the mechanism and its failure mode stay in condensed
  prose. Reason and trigger: `### Maintainer decision 1` — prior-art evidence moves, conclusions stay.
  Spec line 73 carries Worker 3's **L3** fix, restored to HEAD's weaker "after **more modules** have
  had a chance to import and register **their** `DjangoObjectType` classes".
- **HEAD lines 151-180, 182-183, 185-186, 188-221 → spec lines 99-105** — `## Prior art:
  Strawberry-Django` condensed: source snapshot list, sixteen key source references, both mode
  subsections with their example, `### Pros`, `### Cons` moved; both modes stay in condensed prose
  including all three `auto` fallback mappings. Same reason, same trigger.
- **HEAD lines 246-263 → spec line 130, one pointer line** — the "not a final implementation plan"
  disclaimer and the whole of `### Decision criteria` moved. Reason: a judgement yardstick is
  deliberation, not contract. Trigger: `### Maintainer decision 1`.
- **HEAD lines 282-294, 298-309, 313-325, 329-341 → spec line 158, one pointer line** — the four
  options' Pros and Cons moved; each `### Option N` heading and its descriptive sentence stay. Reason
  and trigger: the four-option comparison is the deliberation `### Maintainer decision 1` names.
- **HEAD lines 399-493 → spec line 216, one pointer line** — `### Finalization trigger choices` and
  all four `### … questions` sections moved whole. Reason: the settled deliberation this spec exists
  to record. Trigger: R1's `### Residual scope` entry. **This pointer sentence is where the
  `finalize_django_types` glossary anchor now lives**, hosted on a line whose job is to describe moved
  deliberation — it names the explicit call as one of the four weighed candidates and asserts no
  outcome. Trigger for the re-site: Worker 3's **L1**, resolved by the third path.
- **HEAD line 385 — NOT changed.** Recorded as an explicit negative because pass 1's list claimed it
  was. HEAD's trigger-neutral `Before schema construction:` is byte-identical at spec line 202; the
  L1 fix reverted the earlier `finalize_django_types()` re-site, so the normative
  `### Proposed shape to evaluate` lead-in makes no claim HEAD did not. Worker 3 pass 2 proved the
  byte identity by `od -c` and `cmp`. **This closes L6.**
- **HEAD lines 501, 504, 513 → spec lines 224, 227, 236** — `Meta.fields`, `schema audit`, and
  `Meta.primary` anchors re-sited by link-form change on the existing `## Acceptance criteria`
  bullets, whose carriers HEAD lines 430, 469 and Option 4's Pros removed. Reason: all ten anchors are
  binding and three lost their HEAD carriers to the move. Trigger: `### The 10-anchor surface`.
- **insertion after HEAD line 589 → spec line 313** — `[spec-008-rationale]` definition added to the
  `<!-- docs/SPECS/ -->` group, alphabetical within it. Reason: `START.md` link convention. Trigger:
  the companion-file pointer above.

No spec or rationale content was edited by this final-verification pass. The audit found no defect
requiring one; the one row that was wrong (HEAD 388) sits in this block, which is this pass's to write.

### Notes for Worker 1 (spec reconciliation) — what R1 hands to R2

Everything passes 1 and 2 recorded still stands and is unchanged. R2 must not re-derive any of it.

- **Two anchors are hosted on prose R2 is licensed to rewrite, and R2 owns re-siting them in the same
  edit if it does.** All ten anchors are binding (`### The 10-anchor surface`), and `check_spec_glossary`
  is the gate.
  - `glossary-finalize-django-types` sits on spec line 216, the rationale-pointer sentence that
    replaced HEAD 399-493. Its neutrality is load-bearing: HEAD deliberately left the finalization
    trigger open, so any host inside `### Proposed shape to evaluate` or `### Hard invariants`
    re-resolves in the spec the question R1 moved out. If R2 rewrites the pointer, the replacement host
    must still describe the trigger as *weighed*, never as *chosen*.
  - `glossary-metaprimary` sits on spec line 236, a `## Acceptance criteria` bullet, and is a
    **demotion R2 inherits** rather than a pure link-form change: HEAD read "finalized primary type
    metadata" and now names a specific `Meta` key HEAD described as not yet existing. Accurate at
    HEAD-of-package; no neutral host existed (`Meta.primary` appears in HEAD only at line 430, inside
    a moved question).
- **Four sections are the natural hosts if R2 needs to move either anchor** and none currently names
  its concept in HEAD words: `### Hard invariants`, `### Proposed shape to evaluate`,
  `## Acceptance criteria`, `### Failure criteria`. R1 verified there is no surviving HEAD sentence
  anywhere in the spec naming `finalize_django_types` or `Meta.primary` — so every candidate host adds
  the name, and R2 faces the same constraint R1 did, with the same third-path answer available.
- **The count-unit trap is this cycle's signature defect and has now fired seven times** (five in M1,
  one self-found in `### Decision criteria`, one nearly logged in this pass over
  `*Claims the section(s) no longer make(s).*`). Every structural count R2 writes into a durable file
  must carry its **unit** and the **command** beside it. Delimiter lines are not blocks; grep lines are
  not occurrences; string occurrences are not entries.
- **The three drift-table corrections pass 1 made are re-verified and binding on R2's D-row work**:
  D12 is 31 citations across 25 grep-visible lines (not 28); D14 falsifies **two** of the four
  many-side fakeshop rows (`Category.properties` and `Property.entries` — `PropertyType` carries no
  `relation_shapes` key at all), so six of the eight `## Fakeshop implication` rows still hold; D6's
  cardinality answer **is** in the glossary and is the one spec-008 question still answered "deferred".
- **`## Decision context to preserve` is R2's DRY call**, unresolved. After the two condensations its
  six bullets are the third telling of the same borrow/avoid conclusions. Every bullet is a conclusion,
  so the ordinary deliberation test does not reach it — which is why R1 left it — but the plan's DRY
  preamble does.
- **The `escape hatch` phrase must not be swept globally.** Only the finalization-trigger sense is the
  inversion `### Maintainer decision 2` names; the surviving
  `## Prior art: Strawberry-Django` `### Relevance to this package` use ("Explicit annotations should
  remain an escape hatch", spec line 125) is correct as written, as is
  `## Current strongest direction, not a final plan`'s "Explicit user annotations should remain
  available as an escape hatch" (spec line 170).
- **Ambiguity R2 need not re-derive:** spec lines 3 and 216 gloss "the four candidate finalization
  triggers". HEAD's moved section contains two quartets — approaches 1-4 (HEAD 405-408) and the
  rich-schema trigger bullets (HEAD 418-421). The phrase reads correctly under either and the
  continuation pins the referent to the approaches.
- **Escalations still open and unactioned by R1**, all four: the `types/relations.py` `spec-014`
  misattribution (item R2b, dispatched separately); the `testing/relay.py` "or build the schema"
  consumer-visible inversion; the build plan's "Thirty-one entries" versus the 32 it enumerates
  (Worker 0 owns that list — and the tree now carries **38** total, the growth being concurrent
  sessions' scratchpads, not this cycle); and `spec-009`'s `### Layer 3: Finalization trigger`
  "Preferred triggers:" heading over four never-shipped items, deferred by `### Maintainer decision 6`.

---

## Review (Worker 3, pass 2)

Re-review of the same pass, not a new one. I have no in-context memory of pass 1; the artifact and
the tree are the contract. HEAD captured read-only with
`git show HEAD:docs/SPECS/spec-008-definition_order_independence-0_0_4.md > <scratchpad>/HEAD-spec-008.md`.
No `git stash` / `checkout` / `restore` / `worktree`; no branch; no commit; no `pytest`; no `--cov*`;
no `scripts/review_inspect.py` (no `.py` touched). Failability proofs, hot-path budget, and floor
verification remain not applicable per the plan.

**Scope taken as settled from pass 1:** the over-cut question. Pass 1 ran an independent line-level
sweep of all 603 pre-move lines and found no lost content, no fabricated alternative, and no High
finding. Not redone. This pass re-derives the five **M1** counts from scratch, interrogates the
**L1** disposition, confirms **L2**-**L5**, and re-runs the standing checks.

### High:

None.

### Medium:

None. **M1 is closed at all five sites**, and every count was re-derived here independently rather
than read off Worker 1's table. Units stated, because the unit mismatch was this cycle's signature
defect:

| Claim | Unit | My derivation | Verdict |
|---|---|---|---|
| raw `path:NN` citations in HEAD | **citations (occurrences)** | `grep -oE '[a-zA-Z_/]+\.(py\|md):[0-9]+' <HEAD> \| wc -l` → 25 occurrences on 25 lines; HEAD lines 85 (`` `342` ``, `` `381` ``), 86 (`` `376` ``, `` `471` ``), 174 (`` `113` ``, `` `116` ``) each carry two bare backticked continuation integers no regex sees = +6. Per section: HEAD 81-89 = 9 grep + 4 = **13** graphene; HEAD 163-178 = 16 grep + 2 = **18** strawberry | **31** — confirmed, and the 13/18 split confirmed. Rationale line 36 now reads "thirty-one" and carries the unit clause in place |
| fenced blocks | **blocks** (= delimiter lines / 2) | `grep -c '^\`\`\`'` → HEAD 6, spec 0, rationale 4. HEAD delimiters at 93/95, 102/113, 185/196 → blocks **93-95** (one line of content), **102-113**, **185-196**; rationale delimiters at 125/136, 207/218 | **3 / 0 / 2** — confirmed, and the three claimed HEAD block ranges are exact. The one-line block at 93-95 is the folded one; the other two moved. Rationale bullet now states the delimiter-vs-block trap in place |
| anchors inside moved text | **anchors** | `Meta.fields` (Option 4 Pros), `finalize_django_types` (HEAD 407, in the finalization-trigger list), `Meta.primary` (HEAD 430, `### Registry questions`), `schema audit` (HEAD 469, `### Generic fallback questions`) | **4** — confirmed. All four HEAD carriers were removed by this pass; all four anchors resolve now |
| settled questions | **`?`-terminated lines inside the four `### … questions` sections** | HEAD 425-443 = 6, 444-460 = 4, 461-476 = 4, 477-494 = 5 | **19** — confirmed. (File-wide `?`-lines are 24; the extra five are the `## Problem` intro bullets at HEAD 43-47, correctly excluded. There is no reading that yields 21) |
| sets of open questions | **`### … questions` headings** | `grep -c '^### .*questions' <HEAD>` → 4, at HEAD 425 / 444 / 461 / 477 | **4** — confirmed, and held at **both** sites: spec line 3 and spec line 216 now read "the four sets of open questions", and line 216 still enumerates exactly those four topics |

**The sixth instance Worker 1 found while re-deriving is real and its correction is sound.**
`### Decision criteria`'s entry claimed "six of the thirteen are stated as prohibitions" while
exemplifying four. Re-derived: `sed -n '/^### Decision criteria/,/^### /p' <HEAD> | grep -c '^- '` →
**13**, and the six named in the corrected sentence all exist verbatim in that list — three worded
`avoids …` (`avoids Graphene runtime dependencies`, `avoids generic relation placeholders as the
default schema shape`, `avoids fragile post-schema mutation when a cleaner pre-schema lifecycle is
possible`) and three positively-worded twins of the same prohibitions (`preserves concrete related
DjangoTypes by default`, `keeps the optimizer able to inspect concrete relation metadata`, `fails
loudly before serving an incomplete schema`). Thirteen is the right total and the count is unchanged;
it is now re-derivable, which was the defect.

### Low:

**L1 — closed, and the third path is the right one.** All three checks pass:

1. **The impossibility claim is true.** `grep -n 'finalize_django_types' <HEAD>` returns **407**,
   **421**, and **583**. 407 and 421 are both inside `### Finalization trigger choices` (HEAD
   399-423), which this pass moved whole; 583 is the `[glossary-finalize-django-types]` link
   definition, not a sentence. So no surviving spec sentence names the pass, every candidate host
   adds the name, and Worker 3 pass 1's resolution path (a) was indeed unavailable as written.
2. **Spec line 202 is byte-identical to HEAD line 385.** Proven by character comparison, not
   asserted: `sed -n '385p' <HEAD>` and `sed -n '202p' <spec>` both `od -c` to
   `B e f o r e   s c h e m a   c o n s t r u c t i o n :  \n` (12 bytes) and `cmp` reports no
   difference. The normative `### Proposed shape to evaluate` list is neutral again.
3. **The new host is genuinely neutral.** Spec line 216 is this pass's own rationale-pointer
   sentence — a section whose entire job is to describe moved deliberation, which is where the
   new-prose licence lives. It asserts nothing about which trigger won: it names the explicit call as
   one of the candidates *weighed*, and the only outcome word in it ("the hybrid auto-finalization
   direction this spec named as leading") describes the **spec's** leading direction, which is the
   fact the moved text itself states at HEAD 423 and which the implementation then rejected. It
   asserts nothing about where the seven proposed steps run — those now sit under a lead-in restored
   to HEAD bytes. This is the original defect removed, not relocated.

`check_spec_glossary` re-run confirms the re-site cost no anchor.

**The `Meta.primary` anchor is kept and its demotion note is on disk.** Spec line 236 reads
"can rely on finalized [`Meta.primary`][glossary-metaprimary] type metadata", and the R2-inherited
note is present under this artifact's pass-2 `### Notes for Worker 1 (spec reconciliation)`, stating
that it is a demotion rather than a pure link-form change and that R2 owns re-siting the anchor if it
rewrites `## Acceptance criteria`. That is the disposition pass 1 asked for. I confirm the same grep
ground: `Meta.primary` appears in HEAD only at line 430, inside a moved question, so no neutral host
existed.

**L2 — closed.** Spec line 3 reads "the four candidate finalization triggers and the **leading** one
the implementation rejected". Three of the four were rejected; naming the leading one is the fact
worth pointing at, and it now agrees with line 216.

**L3 — closed.** Spec line 73 reads "during Graphene schema construction — after **more modules**
have had a chance to import and register **their** `DjangoObjectType` classes", restoring HEAD line
97's weaker wording. The load-bearing weakness is back: the next paragraph's failure mode is a target
that never got imported at all, which "every module" contradicted.

**L4 — closed and verified against the checkout.** The rationale's parenthetical now reads "its
`def` line, its `namespace = sys.modules[c.__module__].__dict__` read, and its
`StrawberryAnnotation(v, namespace=namespace)` construction". Read directly from
`~/projects/strawberry-django-main/strawberry_django/utils/typing.py`: **105** is
`def get_strawberry_annotations(cls) -> dict[str, StrawberryAnnotation]:`, **113** is the namespace
read, **116** is the `StrawberryAnnotation` construction, and **115** is the `is_classvar` filter,
which HEAD line 174 never cited. All three claims exact.

**L5 — closed.** `grep -c 'spec-04[68]'` on the rationale → **0**. The cards it does name are
recorded in pass 2's superseding table, and the reason the `relation_shapes` note was not written
here (it belongs to `## Fakeshop implication`, which stayed in the spec as R2's D14 item) is stated
rather than implied. Correcting a pass-1 checklist box through a superseding table rather than by
rewriting the box is the right handling under `ARTIFACT.md` `## Re-pass sections`.

**L6 (new, escalated to Worker 1's final verification, not held) — one pass-1 row escaped the
superseding table.** `### Spec changes made (Worker 1 only)`, under `## Final verification (Worker
1)`, still reads "**line 388 (`Before schema construction:`)** — `finalize_django_types` anchor
re-sited here from the removed `### Finalization trigger choices`". The L1 fix reverted that lead-in
to HEAD bytes and moved the anchor onto the pointer sentence that replaced HEAD 399-494, so the row
is now false. It is not protected prior-pass prose: the section it sits in is explicitly marked
"Pending Worker 3's re-review" and is Worker 1's to write, so the correction lands in the same block
Worker 1 writes next. Recorded rather than held because holding would cost a whole extra Worker 1
pass for a line that section's author must rewrite regardless.

### DRY findings

None, and no existence challenge: this item still creates no abstraction, helper, registry, or
indirection layer.

**No new duplication was introduced by the fixes**, checked mechanically rather than by eye. Every
line of the post-edit spec of 30+ characters, excluding blanks, HTML comments, and link definitions,
was tested for verbatim presence in the post-edit rationale: **0 matches**. (Pass 1 found 2, both
structural; both are now below the threshold or reworded. Either way the direction is right — the
fixes added no restatement.) The two disclosed sub-line restatements pass 1 accepted — the `auto`-mode
fallback mappings and the graphene-django Pros/Cons paraphrase — are unchanged by this pass and
remain licensed by `### Maintainer decision 1`.

Spec line 3 and spec line 216 both name "the four candidate finalization triggers" and "the four sets
of open questions". That is the headline-pointer plus per-section-pointer convention the plan's
`### DRY analysis` takes from spec-005 (line 3 and line 38 are its model), not a duplication finding.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty** (0 lines). `__all__` and the
re-export list are unchanged. No source file was touched at all, consistent with the item's Definition
of Done.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; this slice does not touch `CHANGELOG.md`.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Applicable. All run independently this pass:

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-definition_order_independence-0_0_4.md`
  → **`OK: 10 terms - all have glossary entries and at least one spec link.`**, exit 0. All ten
  anchors are binding per the plan's `### The 10-anchor surface`, and all ten hold across the L1
  re-site.
- `uv run python scripts/check_trailing_commas.py --check` on both `.md` files → **exit 0**, no
  output.
- **Rule 27, counting occurrences not lines:**
  `grep -oE '[A-Za-z0-9_/.-]+\.(py|md|txt|toml|cfg|json):[0-9]+' <file> | wc -l` → **0** in the spec,
  **0** in the rationale. A `-rationale.md` is not on rule 27's scratchpad list, so this is the
  correct standard to hold it to; the rule is **established** here, not merely preserved.
- **Counts re-derived**, `wc -c -l`: spec **19,612 bytes / 327 lines / 0 fence blocks**; rationale
  **42,265 / 630 / 2**; HEAD **30,186 / 603 / 3 blocks**. Every figure matches pass 2's table exactly.
  The deltas from pass 1 (spec +34 bytes / +0 lines; rationale +661 / +7) are consistent with
  word-level edits in the spec and added unit clauses in the rationale, and with nothing else.
- Generated docs (`docs/TREE.md`, `KANBAN.md`, `docs/GLOSSARY.md`) untouched by this pass;
  `docs/GLOSSARY.md`'s dirty state is baseline, from another session.

### What looks solid

- **Lane discipline holds.** `git status --short` carries **36** entries; exactly four belong to this
  cycle (`M` the spec, `??` the rationale, `??` this artifact, `??` Worker 0's plan), leaving the 32
  baseline-dirty entries from other sessions — unchanged, unedited, unreverted. Nothing under
  `docs/review/` was written. No sibling spec (`spec-009`, `spec-010` are absent from status), no
  source file, no test, no durable doc, no other cycle's artifact. **The tree grew to 38 entries
  during this pass** — two further `docs/review/rev-*.md` scratchpads from a concurrent session
  appeared between my first and last `git status`. Neither is mine and neither was touched; recorded
  so a later pass re-deriving the baseline count does not read the growth as drift this cycle caused.
- **Worker 1 did not do R2's work.** The spec still carries `### Hard invariants`,
  `### Proposed shape to evaluate`, `## Acceptance criteria`, `### Failure criteria`,
  `## Fakeshop implication`, `## Cookbook implication`, and `## Decision context to preserve` — the
  exact set `#### What R2 demotes from claim to rationale-plus-pointer` assigns to R2, none demoted.
  None of the five authorized sibling-spec edits landed: `docs/SPECS/spec-010-foundation-0_0_4.md` is
  not dirty, and `django_strawberry_framework/types/relations.py` is not dirty either, so
  `### Maintainer decision 4`'s `spec-014` misattribution is still open as pass 1 recorded.
- **The corrections are corrections only.** `git diff --stat` on the spec is 16 insertions / 292
  deletions across the whole cycle — the move plus this pass's word-level fixes, with no new section
  and no new claim.
- **The superseding-table handling is correct.** `ARTIFACT.md` `## Re-pass sections` says never edit
  prior entries; correcting every artifact-internal number in a new table, and the durable files in
  place, is the only handling that keeps pass 1's line-cited review readable. One row escaped it
  (L6), in a section that is not a prior entry.

### Temp test verification

None created. `docs/builder/temp-tests/spec-008-r1/` was not used — every claim in this item is
verifiable by read, grep, `cmp`, and the two repo check scripts.

### Notes for Worker 1 (spec reconciliation)

- **L6 above** is the one open item and it lands in the block Worker 1 writes next: correct the
  `### Spec changes made (Worker 1 only)` row for HEAD line 388, which no longer receives the
  `finalize_django_types` anchor. The accurate picture after L1: HEAD 385 / spec 202 is byte-identical
  to HEAD, and the anchor sits on the pointer line that replaced HEAD 399-494.
- **Header hygiene:** this artifact's `Status:` line still read `planned` after pass 1 set
  `revision-needed` and pass 2 applied changes. Set here to `review-accepted`. A pass reading only the
  header would have mis-read the round's state; worth a glance at the header on every future pass.
- **Observation, not a finding:** spec lines 3 and 216 gloss the four numbered approaches as "the four
  candidate finalization triggers". HEAD's section contains two quartets — approaches 1-4 at HEAD
  405-408, and the rich-schema trigger bullets at HEAD 418-421, of which the explicit
  `finalize_django_types()` call is literally one. The phrase reads correctly under either, and the
  continuation ("the leading one the implementation rejected") pins the intended referent to the
  approaches. Recorded only so R2 does not re-derive the ambiguity from scratch.
- Everything pass 1 and pass 2 escalated stands unactioned and is unchanged by this pass: the
  `types/relations.py` `spec-014` misattribution, the `testing/relay.py` "or build the schema"
  inversion, the plan's thirty-one-vs-32 baseline-dirty discrepancy (I re-counted: the tree carries
  **32**), and the `## Decision context to preserve` DRY question.

### Review outcome

**`review-accepted`.** All five **M1** counts are corrected in the durable files and every one
re-derives to Worker 1's figure with the unit stated: 31 citations (13 graphene + 18 strawberry, 25
grep-visible lines + 6 bare continuations), 3 HEAD fenced blocks (2 moved, 1 folded, spec 0 /
rationale 2), 4 re-sited anchors, 19 settled questions across 4 question sections. The sixth instance
Worker 1 self-reported is real and correctly closed at thirteen with all six prohibitions named.
**L1 is resolved correctly and by the better path** — the impossibility claim holds under my own
grep, spec line 202 is byte-identical to HEAD by `cmp`, and the new host is a rationale pointer that
asserts neither an outcome nor a location. L2-L5 are closed and each was re-verified against HEAD or
the upstream checkout rather than accepted. `check_spec_glossary` gives `OK: 10 terms`,
`check_trailing_commas --check` exits 0 on both files, rule 27 sweeps to 0 occurrences in both, no new
duplication was introduced, and Worker 1 stayed strictly in its lane and did none of R2's work. The
single open item, **L6**, is a stale row in the unwritten `## Final verification (Worker 1)` block and
is escalated into the block its author writes next rather than held.

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
