# Build: Pre-flight step 7 — spec rationale extraction (`030`)

Spec reference: `docs/SPECS/spec-030-connection_field-0_0_9.md` (whole file; pre-move 790 lines)
Rationale companion (created): `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`
Build plan: `docs/builder/build-030-connection_field-0_0_9.md`, checklist item 0
Status: final-accepted

This is a Worker-1-only procedural pass (`BUILD.md` `### Procedural-closure slices` shape): one
combined Plan + Final-verification block, no Worker 2 build, no Worker 3 review. It ships no `.py`
change, so there is nothing for a builder to implement and nothing for a reviewer to diff.

- **Hot-path declaration: none.** This pass touches two `.md` files and no `.py` file at all, so no
  code runs differently and no number can move. The build plan's conditional hot-path clause (any
  slice landing a change inside `connection.py::_pipeline_sync` / `::_resolve_from_window` /
  `::_finalize_queryset` or `optimizer/extension.py::apply_connection_optimization`) is not
  triggered. Stated explicitly rather than left to be read out of a silence.
- **Floor-verification scope: none.** Same reason: the plan's conditional clause fires only on a
  `.py` change under `connection.py`, `types/base.py`, `types/definition.py`, or
  `optimizer/extension.py`. No floor venv was built and none is owed.
- **No `pytest` run.** Nothing executable changed; no test could observe this pass. No `--cov*`
  flag was used in any form.
- **No `ruff`.** `AGENTS.md` requires `ruff format .` / `ruff check --fix .` after every edit, but
  both are no-ops against `.md` and running them repo-wide would touch a concurrent session's dirty
  `.py` files. Not run, deliberately.

## Plan (Worker 1)

### Spec status-line re-verification

Read on entry (spec lines 1-9: title, shipped-in line, `Status:`, owner, predecessors). All five
still describe the build's current state: the card is `DONE-030-0.0.9`, the spec is the final
implementation record, the five-slice decomposition and the joint-`0.0.9`-cut version boundary are
accurate, and no predecessor doc it names has been deleted. One clause in the Predecessors
paragraph is false at `HEAD` — it says this card "leaves the fourth planned" for the
`Connection-aware optimizer planning` glossary entry, which is `shipped (0.0.9)` at `HEAD`. That is
a spec-reconciliation item, not a status-line falsification, and it is out of this pass's scope
(recorded below under `### Notes for Worker 1 (spec reconciliation)`). No status-line edit was
needed or made.

### What this pass does

`BUILD.md` `## Spec rationale extraction` plus `worker-1.md` `### Performing the rationale move`: a
cut-and-paste MOVE of the spec's deliberative layer into the archive's appendix directory, where
`AGENTS.md` rule 26 pins every archived spec's companions. `spec-030` was the only archived spec
from `001` through `029`+ with a `-terms.csv` and no `-rationale.md`.

### Environment note (blocks nothing, but changes the commands)

`uv run` is currently broken on this tree by a concurrent session's in-progress edit to
`pyproject.toml` (`dynamic = ["version"]` declared with no `[tool.hatch.version]` table yet, so
`hatchling.build.prepare_metadata_for_build_editable` raises `Missing 'tool.hatch.version'
configuration`). `pyproject.toml` is a concurrent session's dirty file and this cycle's scope fence
excludes it, so it was neither edited nor reverted. Every command below therefore runs
`.venv/bin/python` directly — the same interpreter `uv run` would have used, minus the editable
re-resolve. The build plan's baseline-dirty list should gain `pyproject.toml`.

### DRY analysis

- **Helper inventory checked — not applicable, and why.** The package-wide AST inventory exists to
  prevent duplicated *code* shapes before a builder writes them. This pass writes no code and adds
  no helper, constant, validation branch, coercion utility, or test helper, so there is no candidate
  to inventory against. Recorded rather than skipped so a later pass does not read the absence as an
  omission. The `.py` surface is byte-unchanged (proof below).
- **Existing patterns reused.** The companion's structure, voice, and depth are taken from the three
  nearest predecessors — `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` (the
  immediate predecessor and closest model), `spec-028-orders-0_0_8-rationale.md`, and
  `spec-027-filters-0_0_8-rationale.md`. Section order (`## Provenance of this record` →
  `## Revision history` → one `## Decision N` per Decision, each with
  `### Justification (moved from the spec)` / `### Alternatives considered (and rejected)` /
  `### Changes this Decision underwent` → `## Non-Decision deliberation` →
  `## Risks and open questions`) is `spec-029`'s exactly. The spec-side pointer sentence
  (`Rationale companion — this Decision's justification and its N rejected alternatives: [Decision
  N][rationale-dN].`) is `spec-029`'s wording verbatim, counts spelled as words to match.
- **New helpers justified: none.** No shared shape was created.
- **Duplication risk avoided.** The one real duplication risk in a rationale move is reproducing a
  block in the companion while leaving it in the spec, which yields two copies that drift. It is
  prevented mechanically: the companion was generated by a script that reads the pre-move spec by
  line index and the spec was cut by a second script keyed to the same line ranges, so a block
  reproduced here is a block deleted there. `grep -c Justification` and `grep -c 'Alternatives
  considered'` on the post-move spec both return `0`.
- **Boundary count: 0.** No guard, cap, rejection path, or validation branch is added. The
  split question does not arise.

### Implementation steps (as executed)

1. Read the three predecessor companions, then the whole `## Architectural decisions`,
   `Revision history`, and `## Risks and open questions` surface of `spec-030`.
2. Ran the `check_spec_glossary` precondition and mapped every glossary link ref in the spec against
   the planned moved line ranges, to find any term whose only link sat inside moved text.
3. Swept the tree for citations into the moved passages before the move.
4. Generated `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`, reproducing the moved
   blocks byte-for-byte from the pre-move spec by line index.
5. Cut the same line ranges out of the spec, inserting one `Rationale companion —` pointer per
   Decision, the header pointer paragraph, and the surviving Risks rule.
6. Cut the inline chronology framing embedded in surviving contract prose.
7. Re-relativized every link definition for `docs/SPECS/appx/` (one level deeper than the spec) and
   disk-exists-checked all of them.
8. Ran the postcondition proofs below.

### Test additions / updates

None. No executable surface changed.

### Implementation discretion items

None. Every judgement call in this pass is recorded as a decision below, not delegated.

---

## Byte counts (measured, `wc -c` / `wc -l`)

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-030-connection_field-0_0_9.md` | 138,023 bytes / 790 lines | 119,551 bytes / 698 lines | **-18,472** bytes / -92 lines |
| `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md` | did not exist (0 / 0) | 52,311 bytes / 406 lines | **+52,311** bytes / +406 lines |

Commands and output:

```
$ wc -c docs/SPECS/spec-030-connection_field-0_0_9.md    # before (pre-move copy kept outside the repo)
  138023
$ wc -l docs/SPECS/spec-030-connection_field-0_0_9.md    # before
     790
$ wc -c docs/SPECS/spec-030-connection_field-0_0_9.md docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
  119551 docs/SPECS/spec-030-connection_field-0_0_9.md
   52311 docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
  171862 total
$ wc -l docs/SPECS/spec-030-connection_field-0_0_9.md docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
     698 docs/SPECS/spec-030-connection_field-0_0_9.md
     406 docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
    1104 total
```

The companion is larger than the bytes it received because it also carries its own framing: the
provenance section, fourteen `### Changes this Decision underwent` sections, the
`## Non-Decision deliberation` grouping, and the link block. The spec's drop reconciles exactly:

```
23,742 (three moved routes)  +  475 (removed outright)  -  5,745 (framing put back)  =  18,472
```

- **23,742** — the three moved routes, measured off the pre-move copy as whole-line byte counts
  including newlines: the `Revision history` block (lines 11-26) **7,328**; the fourteen
  `Justification:` + `Alternatives considered (and rejected):` block pairs **12,775**; the
  `## Risks and open questions` body (lines 623-630) **3,639**.
- **475** — removed and not moved: **459** bytes of inline chronology framing in surviving contract
  prose (twelve substitutions), plus the **16**-byte `[next]: NEXT.md` link definition, orphaned in
  the spec once the only text citing it left.
- **5,745** — framing put back into the spec: the header pointer paragraph, fourteen
  `Rationale companion —` pointer lines, the surviving Risks rule and its lead-in, and sixteen new
  link definitions (`rationale-d1` … `rationale-d14`, `rationale-risks`, `spec-030-rationale`).

## What moved, by spec heading

**Moved whole (byte-for-byte in the companion, deleted from the spec):**

- **`Revision history (kept inline so the spec is self-contained):`** (pre-move lines 11-26) — the
  preamble plus Revisions 1-3, including the long rev-2 P1/P2/P3 finding narration. Pure chronology;
  exactly what `BUILD.md` means by "the spec never narrates its own history". The preamble line
  itself was **deleted, not moved** — its claim that the history is kept inline is what the move
  made untrue (`worker-1.md` rule 2). The remaining fourteen lines are reproduced verbatim under
  `## Revision history`, and every finding in them is *also* recorded under the Decision it changed,
  in that Decision's `### Changes this Decision underwent`. The double telling is deliberate and
  bounded to that one block: the chronology is what a reviewer of a Decision's history needs and the
  per-Decision record is what a reviewer of the implementation needs.
- **All fourteen `Justification:` blocks and all fourteen `Alternatives considered (and rejected):`
  blocks** under `## Architectural decisions`, Decisions 1-14 — 25 justification bullets or
  paragraphs and 29 rejected alternatives. The 28 label lines became `###` headings in the
  companion; the bodies are verbatim.
- **The body of `## Risks and open questions`** (preamble plus six items).

**Moved as a record, cut from surviving prose:**

- Twelve inline chronology sites in text that otherwise stays: ten `(the review round's PN)` /
  `per the review round's PN` parentheticals (spec slice checklist, Goals item 3, and Decisions 4,
  5, 6, 7, 8, and the Edge-cases `after:`-cursor bullet), plus two whole chronology sentences —
  Decision 11's `rev1's "Slice 3 needs no source change" was therefore false` and Decision 14's
  `rev1 deferred the export to Slice 5 (docs), which conflicted …`. Both sentences are recorded
  under their Decision's `### Changes this Decision underwent`; the parentheticals are pure
  provenance and the sentences around them state the contract unchanged. After the cuts,
  `grep -c 'review round'` and `grep -c rev1` on the spec both return `0`.

**Stayed in the spec, deliberately:**

- `## Current state`, `## Problem statement`, `## Goals`, `## Non-goals`, `## Borrowing posture`,
  `## User-facing API`, `## Slice checklist`, `## Implementation plan`,
  `## Edge cases and constraints`, `## Test plan`, `## Doc updates`, `## Out of scope`,
  `## Definition of done` — untouched apart from the chronology cuts named above.
- **Every Decision body.** Each Decision still reads as a complete, self-sufficient statement of
  what the package does. No Justification held a load-bearing sentence that needed promoting back
  into a Decision body: this spec keeps its mechanism prose *in* the Decision (Decision 3's
  "Strawberry `0.316.0` does NOT reject `first` + `last` … therefore the package implements that
  guard itself"; Decision 5's `_is_relay_shaped`-ORs-both-spellings paragraph and why an MRO-only
  check is insufficient; Decision 7's effective-ordering resolution and the
  `_ends_in_unique_column` exception; Decision 10's dispatch-frozen-at-build-time paragraph;
  Decision 11's `Scope honesty` and `Forward design input for 033` blocks) and confines the
  `Justification:` blocks to *why this over that*. Checked Decision by Decision before cutting, not
  assumed. Zero promotions were needed and zero were made.
- **Decision 11's `P1-B` chronology reference, repointed rather than removed.** See the citation
  sweep below — five live sites cite that label and none is writable by this pass.

### `## Risks and open questions` — the judgement, stated

The section is deliberative in shape (a preferred-answer / fallback pair per item), which is what
makes it a build-time instrument rather than a contract, so the whole **body** moved and the spec
keeps the heading plus a pointer. Each item was read for a live contract before the cut:

- **Items 1 and 2** (synthesized-signature vs custom `FieldExtension`; the consumer annotation vs
  the resolved concrete type) are mechanism bets Slice 2 settled by compiling against the locked
  Strawberry. Nothing normative survives them — the shipped mechanism is stated in Decisions 6, 4
  and 5.
- **Item 3** (the card body's unnumbered spec filename) is a `KANBAN.md` reconciliation Decision 1
  already states as contract.
- **Item 4** (optimizer cooperation scope) restates Decision 11 and its `033` bound. The bound is a
  spec-reconciliation item at `HEAD` (below), not a rule.
- **Items 5 and 6** (finalize auto-trigger; dict vs flat boolean) restate Decisions 12 and 8 with
  fallbacks the build never needed.
- **One rule does outlive the build, and stayed.** Every Strawberry-mechanism claim in this spec is
  derived against the uv.lock-resolved `0.316.0` while `pyproject.toml` declares an open
  `strawberry-graphql` floor, so the mechanism can drift across the supported range even where the
  conclusion holds. The spec now carries that as the single surviving bullet under the heading,
  naming the three specific upstream behaviors it depends on (`SliceMetadata.from_arguments` not
  rejecting `first` + `last`; `ConnectionExtension.resolve` forwarding non-pagination `**kwargs`
  and not awaiting the inner return; `ListConnection.resolve_connection` receiving the pagination
  arguments) and the requirement to re-derive by execution rather than from a changelog. This is
  the `spec-029` precedent, applied to this spec's own upstream surface.

## Final verification (Worker 1)

### Postcondition proofs

**1. `check_spec_glossary` — precondition and postcondition.** The build plan recorded `OK: 50
terms` at pre-flight. Run before the move and again after; no term lost its last spec link, so the
terms CSV was never touched and never needed to be.

```
$ .venv/bin/python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md   # BEFORE
OK: 50 terms - all have glossary entries and at least one spec link.
EXIT=0
$ .venv/bin/python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md   # AFTER
OK: 50 terms - all have glossary entries and at least one spec link.
EXIT=0
```

The gate was not left to discover a break: before cutting anything, every `][ref]` use in the spec
body was mapped to its line and differenced against the planned moved ranges. Exactly one ref was
used **only** inside moved text — `next` (`docs/SPECS/NEXT.md`), which is not a glossary term, so
no CSV term was at risk. That ref's definition was removed from the spec and added to the
companion. `goal` was already an unused definition in the spec before this pass and is left alone.

**2. Link-scaffold and path proof, both files.** `START.md`'s convention is enforced by the
`source-layout` pre-commit hook; the companion sits one level deeper than the spec, so every
definition path was re-relativized (`../../../AGENTS.md`, `../../GLOSSARY.md`,
`../spec-030-connection_field-0_0_9.md`, `spec-030-connection_field-0_0_9-terms.csv`) and
disk-exists-checked. The group-header block was copied from an existing `appx/*-rationale.md`
rather than hand-derived: single-line `<!-- LINK DEFINITIONS -->` delimiter, all ten canonical
group headers in canonical order, present even when empty (`<!-- scripts/ -->` and
`<!-- .venv/ -->` are empty here).

```
$ .venv/bin/python scripts/check_trailing_commas.py --check docs/SPECS/spec-030-connection_field-0_0_9.md docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
EXIT=0

$ .venv/bin/python  # audit both files: undefined refs / unused defs / defs whose path is not on disk / dangling in-page anchors / inline cross-file links
== docs/SPECS/spec-030-connection_field-0_0_9.md
 undefined: []
 unused: ['goal']          # pre-existing before this pass; verified against the pre-move copy
 missing paths: []
 dangling in-page anchors: []
 inline cross-file links: []
== docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
 undefined: []
 unused: []
 missing paths: []
 dangling in-page anchors: []
 inline cross-file links: []
```

**3. In-page anchors.** Every `](#…)` in both files resolves to a heading in its own file (the
`dangling in-page anchors: []` rows above). The spec's `#decision-N--…` anchors stay inline per
`START.md` and are not reference-style. The companion's `## Decision N — <title>` headings slug
identically to the spec's `### Decision N — <title>`, so a `(#decision-N--…)` anchor inside moved
text resolves locally in the companion — which is where a reader of a moved sentence wants to land
— and `#risks-and-open-questions` does the same. Two anchors inside the moved revision history
named spec sections the companion does not have (`#test-plan`, `#doc-updates`); both were repointed
at the spec through reference-style definitions rather than left to dangle. These two lines are the
only reproduced text that is not byte-verbatim, and the companion says so.

**4. Citation sweep — population and instrument.** `scripts/check_citations.py` resolves
`path::Symbol` only and puts `docs/` out of scope, and no link checker sees a prose citation, so
this sweep is the only instrument. **Population:** every `.py` / `.md` / `.csv` / `.html` / `.toml`
file under `django_strawberry_framework/`, `tests/`, `examples/`, `docs/`, `scripts/` plus the root
standing docs — swept for the string `spec-030` before the move to enumerate every citing site, and
then swept again for the specific labels a citation could resolve *into* moved text. Per hazard 3,
the second sweep counts **occurrences**, not matching lines, so a citation wrapped across two source
lines cannot hide.

Before the move the sweep found four finding labels cited from live code and tests: `P1-B`, `P3a`,
`P3b`, and `Open Question: direct relay.Node inheritance`. **Three of the four were already dangling
at `HEAD`, before this pass touched anything** — `P3a`, `P3b`, and `Open Question` occur **zero**
times in the pre-move spec:

```
$ for t in 'P1-B' 'P3a' 'P3b' 'Open Question'; do grep -c "$t" <pre-move spec>; done
1
0
0
0
```

Post-move occurrence counts across the swept population, with the non-`030` files listed:

```
'P1-B': 17 occurrences in 7 files
     django_strawberry_framework/orders/sets.py
     docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md
     docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
     docs/SPECS/spec-028-orders-0_0_8.md
     docs/SPECS/spec-030-connection_field-0_0_9.md
     docs/builder/DONE/build-028-orders-0_0_8.md
     examples/fakeshop/test_query/test_library_api.py
'P3a': 9 occurrences in 3 files
     docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
     docs/SPECS/spec-035-optimizer_hardening-0_0_10.md   # that spec's own round label, unrelated
     tests/test_connection.py
'P3b': 7 occurrences in 4 files
     docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
     docs/builder/DONE/build-028-orders-0_0_8.md
     tests/test_connection.py
     tests/test_registry.py
'Open Question': 4 occurrences in 2 files
     docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
     tests/test_connection.py
'spec-030 Decision': 32 occurrences in 10 files   # every cited Decision heading still exists
'spec-connection.md': 5 occurrences in 3 files
```

Re-resolution across the spec+companion pair, one line each:

- **`P1-B`** — cited by `django_strawberry_framework/orders/sets.py`,
  `examples/fakeshop/test_query/test_library_api.py`, and
  `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md`, none of them writable by this pass. Its one
  pre-move anchor was Decision 11's `see the review round's P1-B`. Rather than break five live
  sites, the label was **kept in the spec** and repointed: the parenthetical now reads
  `the finding recorded as `P1-B` in the rationale companion, [Decision 11][rationale-d11]`. The
  label therefore resolves in **both** halves of the pair, and the companion's Decision 11 entry
  records what the finding was and which `spec-028` claim it retired.
- **`P3a`** (the cooperation point short-circuiting to the unchanged queryset when
  `_active_optimizer` is `None`, rather than fabricating a throwaway optimizer) — now recorded under
  the companion's Decision 11.
- **`P3b`** (the connection-type cache's co-clear reached through a cycle-safe local import, with
  `clear()` skipping the block rather than raising) — now recorded under the companion's Decision 4.
- **`Open Question: direct relay.Node inheritance`** (accepted by the guard because
  `_is_relay_shaped` ORs the `Meta.interfaces` disjunct with `issubclass(target_type, relay.Node)`)
  — now recorded under the companion's Decision 5.
- **`spec-030 Decision N`** (32 occurrences, Decisions 3/4/5/6/7/8/10/11/14) — every cited Decision
  heading survives at its original anchor. No repointing needed.

Net effect: this pass broke zero citations and **converted three pre-existing dangling citations
into resolvable ones**.

**5. `.py` surface unchanged — the inverse proof.** The claim is that no executable byte moved, so
the proof is a diff that is empty by construction rather than a green suite.

```
$ git status --short -- '*.py' | wc -l
      15                      # none is this pass's; see note 8 below
$ git status --short docs/SPECS/
 M docs/SPECS/spec-030-connection_field-0_0_9.md
?? docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
```

The only two paths this pass wrote under version control are the spec and the companion, plus this
artifact; `docs/builder/worker-memory/worker-1.md` is the fourth write and
`docs/builder/worker-memory/` is `.gitignore`d. Every dirty `.py` in the tree was already dirty at
pass start; four of the fifteen are **not** in the build plan's baseline list and are recorded in
note 8 below.

**6. Structural sanity.** No blank-line run was introduced: the post-move spec contains three
`\n\n\n` runs and the pre-move copy contained the same three, all inside fenced code blocks in
`## User-facing API`. The companion contains none. `grep -c Justification` and
`grep -c 'Alternatives considered'` on the post-move spec both return `0` — the move was a cut, not
a copy.

### Summary

`spec-030`'s deliberative layer now lives in
`docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`: the three-revision history, 14
justification blocks, 14 rejected-alternative blocks, and the `## Risks and open questions` body,
plus a per-Decision `### Changes this Decision underwent` record that carries each revision-2
finding under the Decision it changed and names the three claims those findings retracted. The spec
dropped 18,472 bytes and reads as a clean current contract with one pointer per Decision and no
chronology anywhere in it. Every Decision remains self-sufficient; no sentence needed promoting back
into a Decision body. `check_spec_glossary` holds at `OK: 50 terms`, both link scaffolds validate,
every in-page anchor resolves, and the citation sweep closed net-positive.

Pre-flight step 7 is discharged. Slice 1 may be dispatched.

### Spec changes made (Worker 1 only)

Line numbers are post-move unless stated. Cause for every entry: pre-flight step 7's rationale
move, `docs/builder/build-030-connection_field-0_0_9.md` checklist item 0.

1. **Pre-move lines 11-26 → post-move line 11.** The `Revision history` block was replaced by a
   one-line pointer at the companion (`This spec's deliberative layer … lives in the rationale
   companion`). The block's preamble line was deleted rather than moved.
2. **Fourteen `Justification:` / `Alternatives considered (and rejected):` block pairs across
   `## Architectural decisions`** (pre-move lines 300-308, 319-321, 329-338, 351-360, 383-391,
   399-408, 424-434, 447-457, 463-465, 473-475, 487-497, 503-505, 511-513, 523-528) → one
   `Rationale companion —` pointer line each, at post-move lines 285, 296, 304, 317, 340, 348, 364,
   377, 383, 391, 403, 409, 415, 425.
3. **`## Risks and open questions` body** (pre-move lines 623-630) → a pointer paragraph plus the
   one surviving derivation-baseline rule. The heading stays, so the four in-page
   `#risks-and-open-questions` links elsewhere in the spec still resolve.
4. **Twelve inline chronology sites in surviving prose** — ten `(the review round's PN)` /
   `per the review round's PN` parentheticals and two whole `rev1` sentences (under Decisions 11 and
   14) — removed. Reason: `BUILD.md` "the spec never narrates its own history"; the content is
   recorded per-Decision in the companion. Decision 11's `P1-B` reference was repointed at the
   companion instead of removed, because five live sites cite that label.
5. **Link definitions.** `[next]: NEXT.md` removed (orphaned by the move). Sixteen added:
   `[rationale-d1]` … `[rationale-d14]`, `[rationale-risks]`, `[spec-030-rationale]`, all under the
   existing `<!-- docs/SPECS/ -->` group in alphabetical order.

No spec claim was corrected, reworded for accuracy, or reconciled against `HEAD` in this pass. That
is the owning slices' work; the items below are handed to them.

### Notes for Worker 1 (spec reconciliation)

Found while reading the spec end to end for the move. **None was fixed** — the scope of this pass is
the text move. Each is for the owning slice's audit.

1. **`Connection-aware optimizer planning` is `shipped (0.0.9)` in `docs/GLOSSARY.md` at `HEAD`, and
   the spec says four times that this card leaves it planned.** Verified:
   `docs/GLOSSARY.md` `## Connection-aware optimizer planning` carries `**Status:** shipped
   (`0.0.9`).`. The false sites are the Predecessors paragraph (line 9, "leaves the fourth
   planned"), the `## Current state` glossary bullet (line 111), the Slice-5 checklist sub-bullet
   (line 81, "Leave … `planned for 0.0.9`"), the `## Doc updates` Slice-5 GLOSSARY bullet (line
   508), and Definition-of-done item 8. Owner: Slice 5 is **audit-only** under this cycle's scope
   fence, so the glossary itself is not editable here — but the *spec's* claim about it is Slice 3's
   or Slice 5's to correct.
2. **The "derived plan is empty for every connection field in `0.0.9`" bound was closed by
   `DONE-033-0.0.9`.** Live at spec line 399 (Decision 11 `Scope honesty`), line 73 (Slice-3
   checklist), line 488 (`## Test plan`), and Definition-of-done item 6 (line 561). Worker 0 already
   flagged this as the cycle's largest reconciliation item; confirmed present at all four sites. The
   companion's Decision 11 entry is where the "what changed and why" record belongs when Slice 3
   rewrites the spec to the current contract.
3. **Three stale symbol citations.** `_initial_queryset(target_type)` (lines 69, 104, 354, 447) and
   `_apply_get_queryset_sync` / `_apply_get_queryset_async` (lines 69, 103, 104, 362, 387, 389, 557)
   are cited as `types/relay.py` symbols; at `HEAD` they are `initial_queryset(...)` and
   `apply_type_visibility_sync` / `apply_type_visibility_async` in
   `django_strawberry_framework/utils/querysets.py` (the spec-045 sealed-execution boundary).
   `_ends_in_unique_column` (lines 71, 358) is pinned as a `connection.py` symbol; at `HEAD` the
   canonical implementation is `django_strawberry_framework/optimizer/plans.py::ends_in_unique_column`,
   re-exported into `connection.py` under the old private name. Worker 0 flagged these; line
   inventory added.
4. **Decision 9 defers `Meta.cursor_field`, which later shipped.** Spec lines 131, 171, 379-381,
   446, 536 all state the deferral; the keyset-cursor work landed in the `0.0.14` line and
   `connection.py` carries `_resolve_keyset_connection` / `_KeysetPage` / `Meta.cursor_field` at
   `HEAD`. The spec must state the current contract without narrating the chronology; the chronology
   goes in the companion under Decision 9.
5. **At least one review round of this spec was never recorded.** The `Revision history` block
   listed three revisions and exactly one finding round (Revision 2, with unlettered P1/P2/P3
   findings), yet live source and tests cite four finding labels from this spec — `P1-B`, `P3a`,
   `P3b`, and an `Open Question` heading — of which three occur **zero** times in the pre-move spec.
   All four are now recorded in the companion under the Decision each belongs to, and the underlying
   behavior is shipped and tested in every case, so this is a provenance gap rather than a code gap.
   Worth knowing for any later pass that treats the revision history as the complete record of what
   reshaped this spec: it was not.
6. **`[goal]` is an unused link definition in the spec.** Pre-existing (verified against the
   pre-move copy), harmless, and not this pass's to clean — noted so a later sweep does not
   attribute it here.
7. **`pyproject.toml` is dirty from a concurrent session in a state that breaks `uv run`.**
   `dynamic = ["version"]` is declared with no `[tool.hatch.version]` table, so any `uv run`
   invocation fails with `Missing 'tool.hatch.version' configuration` before executing anything.
   Out of scope (`AGENTS.md` rule 34) — never edited, never reverted. Every later pass in this cycle
   should expect to run `.venv/bin/python` directly until the concurrent session finishes, and the
   build plan's baseline-dirty list should gain the file.

8. **The concurrent session's dirty-`.py` footprint has grown past the build plan's baseline
   list.** Four modified `.py` files are dirty that the plan's baseline does not name:
   `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `scripts/bug_hunt.py`, and
   `tests/test_bug_hunt.py`. The first two plus the `pyproject.toml` state in note 7 read as one
   in-progress change moving the version to a single source of truth (`dynamic = ["version"]`
   sourced from `__version__`, with the parity test rewritten). All four are out of scope
   (`AGENTS.md` rule 34) — never edited, never reverted — and are recorded here so no later pass in
   this cycle mistakes them for its own output or for a regression. `AGENTS.md` and `uv.lock` went
   dirty from the same session during this pass; both are likewise out of scope and untouched.

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
