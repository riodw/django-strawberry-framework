# Build: R1 — Spec rationale extraction for spec-001

Spec reference: `docs/SPECS/spec-001-django_types-0_0_1.md` (whole file; 52,341 bytes at pass start)
Build plan: `docs/builder/build-001-django_types-0_0_1.md` (residual item R1)
Status: final-accepted

**Deviation 3 of the build plan governs this artifact.** R1 has no Worker 2 pass — `BUILD.md`
`## Spec rationale extraction` makes Worker 1 the only role that performs the move and states that
Worker 2 never reads the rationale file. So this single Worker 1 pass **wrote the plan below AND
performed the move**, and `Status: planned` here means "dispatch Worker 3 for the audit", not
"dispatch a builder". The `## Move performed` section stands in for the Worker 2 build report and
keeps its subsection names so Worker 3 reads a familiar shape.

## Plan (Worker 1)

### Spec status-line re-verification

`spec-001-django_types-0_0_1.md` has **no status/header block** — no title-adjacent target-release,
status, owner, or predecessor lines. Line 1 is the `# Spec: DjangoType Foundation` title and line 3
opens `## Problem statement`. Nothing to re-verify or falsify; recorded so the next spawn does not
re-derive the absence. The stale *body* claims (`## Current state`, the tense of the scalar table)
are item R2's scope, not this pass's.

### DRY analysis

**Helper inventory checked.** Not applicable in the form `worker-1.md` defines it: that step exists
to prevent duplicated *code* helpers, and this item writes no `.py` file and plans none. The
package-wide AST inventory would answer a question R1 does not ask. The DRY question R1 *does* ask
is the plan's own preamble rule — "a fact told twice across the spec and its rationale sibling goes
stale in one of them" — and it is answered per moved passage below.

- **Existing patterns reused.** The rationale file's shape is taken from the one archived sibling
  that already exists, `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`: title line,
  companion preamble, `## How to read this file`, `## Provenance of this record`, keyed entries with
  a `Spec: [heading][ref]` line and italic `*Moved — …*` / `*Alternative rejected — …*` leads, and a
  link-definitions block whose `docs/` targets resolve `../../` and whose `docs/SPECS/` siblings
  resolve `../`. Reusing it means a reader who has read one rationale file can read this one.
- **New helpers justified.** None. No source, no test, no script.
- **Duplication risk avoided.** Three, all real in this spec:
  1. **The same fact left in both files.** Every passage moved was *cut*, not copied. Where a
     passage mixed contract with deliberation, the contract half was restated in the spec in
     present tense and the deliberative half moved — the rationale then says explicitly which half
     stayed, so neither file silently owns both.
  2. **The spec already duplicated itself.** The `lazy_ref` candidate approaches appear twice
     (`## Registry` and `## Post-slice-7 future work`), and the `Meta.interfaces` parking claim
     appears twice (`## DjangoType` and `## Post-slice-7 future work`). Both duplications are the
     mechanism by which a spec goes stale in one place and not the other. The rationale records
     both copies in one entry each; the `Meta.interfaces` copy that survives in `## DjangoType` is
     flagged for R2 rather than silently cut.
  3. **Pointer inflation.** `BUILD.md` rule 1 requires every decision keep a one-line pointer to
     what moved. Written naively that is one pointer per removed paragraph. This pass uses **one
     global pointer** (after `## Non-goals`, naming all four whole-section moves) plus **five
     section-local pointers** where a section kept text and lost text — six lines total, not
     fourteen.

### Implementation steps

Pin-at-write-time line numbers are from the pre-move spec.

1. Cut `## Scope creep into the N+1 problem` entire (45-53); replace with the global rationale
   pointer paragraph.
2. Under `## Scalar field conversion`: cut the `Deviation from earlier draft` (251),
   `Slice 2 implementation subset` (253) and `Deferred scalar conversions` (255) paragraphs;
   restate the unsupported-field-type raise as a present-tense rule that keeps its fail-open
   reasoning; add a section pointer.
3. Under `## Choice field enum generation`: de-slice the section opener (259); cut the
   label-vs-value comparison from the sanitization paragraph (282), keeping the rule and its cost;
   add a pointer. Leave the import-order/`Meta.choice_enum_names` paragraph (313-315) untouched.
4. Under `## Relation field conversion`: cut `Slice 2 -> Slice 3 hand-off` (369) and
   `Slice 3 status (post-implementation)` (371), promoting the dispatch rule and the relation set
   into contract prose; **re-site the `definition-order-independence` glossary link** from the cut
   paragraph onto the surviving forward-reference sentence (346); add a pointer.
5. Under `## Registry`: cut the three `lazy_ref` candidate bullets (377-381); keep the `lazy_ref`
   sentence; add a pointer.
6. Under `## Suggested implementation slices`: strip every `Status:` annotation and the
   supersession / move narratives (622-634); fold Slices 4-6 into one ownership line naming
   `spec-002-optimizer-0_0_2.md`; add a pointer.
7. Cut `## Post-slice-7 future work` (666-680) and `## Open questions` (682-688) entire.
8. Repair the one dangling forward reference the cuts create: the scalar table's
   "relay `GlobalID` remapping is the open question below" (164).
9. Add `[spec-001-rationale]: appx/spec-001-django_types-0_0_1-rationale.md` under the spec's
   `<!-- docs/SPECS/ -->` group.
10. Write `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` directly at `appx/` (the spec
    is already archived; there is no later move step), keyed entry per spec heading, with all ten
    canonical link-definition group headers.
11. Run both verification commands and quote them.

### Test additions / updates

None, and none possible: this item writes no `.py` file. The executable checks that stand in for
tests are the two commands in `### Validation run` below, both of which have a recorded pre-move
baseline in the build plan (exit 0 / `OK: 21 terms …` and exit 0 / `OK: 48 done cards …`).

### Implementation discretion items

None delegated — there is no Worker 2 pass to delegate to. Every judgement call this item raised is
decided in `### Implementation notes`.

### Dispatched findings checklist

R1 is neither a spec slice (spec-001's slices shipped at `0.0.1`) nor a review round, so there is no
`## Slice checklist` to copy verbatim. Per `BUILD.md` `## Review rounds`, `### Dispatched findings
checklist` is the named substitute in this position; the boxes are R1's obligations as the build
plan's checklist line and the maintainer's dispatch state them. **Ticked by Worker 1 in this pass**
because Deviation 3 gives it the performer's role; Worker 3 audits the ticks, Worker 1 re-audits at
final verification.

- [x] The deliberative layer is **moved**, not copied and not summarized: text landing in
      `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` leaves the spec.
- [x] `## Scope creep into the N+1 problem` is gone from the spec (100% deliberative layer).
- [x] The spec no longer narrates its own history: `Deviation from earlier draft:`,
      `Slice 2 implementation subset:`, `Slice 2 -> Slice 3 hand-off:`,
      `Slice 3 status (post-implementation):`, the `Status: shipped` / `superseded by` / `Moved to`
      annotations, `## Post-slice-7 future work`, `## Open questions`.
- [x] Every entry in the rationale file names the spec section it belongs to **by heading and
      anchor**, and carries the alternatives rejected and why each lost, the changes the decision
      has undergone, and the claims it may no longer make.
- [x] Every decision that lost text keeps a one-line pointer naming what moved and where.
- [x] The rationale file is written **directly** to `docs/SPECS/appx/`, never to `docs/` first.
- [x] Both files use reference-style links with one `<!-- LINK DEFINITIONS -->` block and all ten
      canonical group headers, and every path is disk-exists-checked.
- [x] `check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md` exits 0 with
      `OK: 21 terms …`; no anchor lost its last spec-body link.
- [x] `import_spec_terms --check` exits 0 with `OK: 48 done cards have glossary links.`
- [x] Spec byte count reported before and after.
- [x] R2's work was **not** done here: no claim was reconciled against HEAD, and every removed
      status claim is recorded in the rationale as a claim the spec *made*, not as one HEAD
      falsifies.

---

## Move performed (Worker 1, in place of the Worker 2 build pass)

### Files touched

- `docs/SPECS/spec-001-django_types-0_0_1.md` — the removals (steps 1-8), the
  `definition-order-independence` link re-site, and the new `[spec-001-rationale]` link definition.
- `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` — **created**, 23,370 bytes.
- `docs/builder/bld-001-r1-rationale_move.md` — this artifact.
- `docs/builder/worker-memory/worker-1.md` — one appended entry under a new
  `## spec-001 residual cycle` heading (gitignored; not part of the diff).

### Byte counts

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-001-django_types-0_0_1.md` | 52,341 | **42,480** | **-9,861 (-18.8%)** |
| `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` | 0 (absent) | 23,370 | +23,370 |

The rationale file is larger than the bytes removed, and that is expected rather than a copy leak:
it carries its own preamble, `## How to read this file`, `## Provenance of this record`, a
`Spec: [heading]` line and a framing sentence per entry, and the *why each alternative lost*
reasoning the spec mostly stated as bare assertions. The 047 sibling has the same shape (18,548
bytes for a spec whose moved text was likewise smaller). What matters for the mechanism is the
spec's number: every future spawn reads 9,861 fewer bytes.

### What moved, by spec heading

| Spec heading | What left it |
|---|---|
| `## Scope creep into the N+1 problem` | **Whole section.** The scope argument, the enumeration of where the spec reached into N+1, the rejected two-specs-in-lockstep alternative, and the self-predicted cut line. |
| `## Scalar field conversion` | `Deviation from earlier draft:` (the rejected `typing.Any` fallback, as chronology); `Slice 2 implementation subset:`; `Deferred scalar conversions:`. |
| `## Choice field enum generation` | The section opener's slice scheduling; the graphene-django / strawberry-graphql-django label-sanitization comparison. |
| `## Relation field conversion` | `Slice 2 -> Slice 3 hand-off:`; `Slice 3 status (post-implementation):`. |
| `## Registry` | The three candidate `lazy_ref` resolution approaches. |
| `## Suggested implementation slices` | Every `Status:` annotation; Slice 4's supersession narrative (the two architectural issues, the surviving symbols, the O1-O6 rebuild split); Slice 5's and Slice 6's move reasons. |
| `## Post-slice-7 future work` | **Whole section**, all six deferral items. |
| `## Open questions` | **Whole section**, all three questions and their recommendations. |

### What deliberately STAYED, and why

- **`## N+1 strategy` entire**, including the PR #583 paragraph and the three per-slice
  implementation paragraphs (`Resolver-to-type tracing (Slice 4)`, `only() and FK columns (O5)`,
  `plan_relation integration (O6)`). The PR #583 paragraph is the exact carve-out `worker-1.md`
  names: *"otherwise FK joins bypass per-type visibility filtering and leak rows"* is why the
  downgrade rule is built the way it is, and a builder who never reads it writes the leak. The
  three per-slice paragraphs describe mechanism, not deliberation; whether the section belongs to
  `spec-002` at all is a disposition call the build plan explicitly reserves for R2.
- **`## get_queryset`'s O6 sentinel-flip paragraph.** It names a slice, but what it states is the
  mechanism (`_is_default_get_queryset`, `has_custom_get_queryset` returning its negation). It is
  also drift row D15, i.e. already on R2's list. `worker-1.md`: when it is unclear whether a
  sentence is deliberation or instruction, it stays.
- **The `Meta.interfaces` parking paragraph** under `## DjangoType`. A status claim, not
  deliberation; drift row D5. Moving a status claim is neither a legitimate rationale entry nor the
  deletion `BUILD.md` rule 2 prescribes for falsified prose — that deletion is R2's call, made
  against HEAD, which this pass is forbidden to do.
- **The enum import-order paragraph** (`the first type defined wins the enum's name …`). Consumer
  instruction with a stated consequence, and it carries the spec's **only** link to the
  `metachoice_enum_names` glossary anchor.
- **`Field-selection defaults`**, **the `## What both libraries overlap on` closing scope
  sentence**, **`## Current state`**, **`## What this enables immediately after implementation`**,
  **the `schema.py` coordination note**, and **`## References`**. The first two are normative with
  one clause of justification; the next two are stale-by-tense, which is R2's axis, not R1's; the
  coordination note is instruction to whoever uncomments the example; references are contract
  scaffolding.

### Minimal repairs made to keep surviving prose coherent

Six. Each is the smallest edit that leaves a parsing sentence; none introduces a claim the spec did
not already make.

1. **Global pointer added** after `## Non-goals`, occupying the removed `## Scope creep` section's
   position and naming all four whole-section moves. Required by `BUILD.md` rule 1, which the
   whole-section removals would otherwise leave with no pointer site at all.
2. **Unsupported-field-type raise restated** (`## Scalar field conversion`). The rule lived only
   inside the `Deviation from earlier draft:` chronology and in an illustrative code block. Cutting
   the paragraph would have left the fail-open reasoning nowhere in the spec, so it is now one
   present-tense sentence: *"A field type missing from `SCALAR_MAP` must raise `ConfigurationError`
   naming the offending field, never fall back to `typing.Any`: …"* keeping the masking/opaque-error
   reasoning verbatim. This is the one place the pass rewrote rather than cut, and it is deliberate:
   `worker-1.md` names exactly this shape as the carve-out the move can otherwise turn into a defect.
3. **Choice-enum section opener de-sliced.** `"Slice 7 routes Django choice columns through …"` →
   `"Django choice columns route through …"`, keeping the second sentence's mechanism.
4. **Sanitization rule kept, comparison cut.** `"Sanitization runs on the value, not the label."`
   plus the `MEMBER_<digit>` cost sentence survive; the library comparison moved.
5. **Relation dispatch promoted to contract.** The hand-off paragraph was the only statement of the
   dispatch rule and of which relations `fields = "__all__"` surfaces, so those two facts are now
   one present-tense sentence pair in `## Relation field conversion`. Everything else in both cut
   paragraphs moved.
6. **Dangling forward reference repaired.** The scalar table read `"relay GlobalID remapping is the
   open question below"` and `## Open questions` no longer exists; it now reads *"whether these
   remap to a relay `GlobalID` is a question this spec left open — see the rationale file"*, which
   is the same claim with a resolvable target.

Also, not a repair but a required re-siting: **`definition-order-independence`'s last spec-body
link** lived inside `Slice 3 status (post-implementation)`. It was re-sited onto the surviving
contract sentence in `## Relation field conversion` (*"use Strawberry forward references, so that
[definition order does not matter]"*), which is where the concept is normative. No narration was
re-added to save an anchor and the terms CSV was not touched.

### Validation run

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
OK: 21 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 48 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-001-django_types-0_0_1.md \
    docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md
exit=0
```

Both baselines from the build plan are held exactly. No `ruff` run: no `.py` file was touched. No
`pytest` run: no test exists for a markdown move, and none was in the plan.

Link paths, disk-exists-checked from `docs/SPECS/appx/`: `../spec-001-django_types-0_0_1.md`,
`../spec-002-optimizer-0_0_2.md`, `../../builder/BUILD.md` — all present (`ls` confirmed). The
spec's new definition `appx/spec-001-django_types-0_0_1-rationale.md` resolves from `docs/SPECS/`
to the created file. Every in-page anchor the rationale cites was checked against the spec's
surviving `## ` headings: `#goal`, `#djangotype`, `#scalar-field-conversion`,
`#choice-field-enum-generation`, `#relation-field-conversion`, `#registry`, `#n1-strategy`,
`#suggested-implementation-slices`.

### Concurrent-session churn observed (not this pass's, not reverted)

`git status --short` after the pass shows, beyond this pass's two spec paths: `M KANBAN.html`,
`M KANBAN.md`, `M docs/SPECS/appx/spec-027-filters-0_0_8-terms.csv`,
`M docs/SPECS/appx/spec-048-secure_output_defaults-0_0_14-terms.csv`, `M examples/fakeshop/db.sqlite3`,
plus the two baseline-dirty spec-048 paths. These appeared during the pass and are the concurrent
spec-048 session's card-wrap (KANBAN.md +5 lines, the 048 terms CSV +6 rows). This pass ran exactly
two DB-touching commands, both read-only: `check_spec_glossary.py` (no `--auto-link`) and
`import_spec_terms --check`, whose `--check` flag is documented and implemented as
"validate DB rows against the CSVs **without writing**". `AGENTS.md` rule 34: recorded, not
reverted, not edited.

### Failability proofs

None; this pass introduced no new boundary, guard, gate, or rejection path. It writes no executable
code.

### Hot-path budget

Not applicable; plan declares no hot path (`build-001-django_types-0_0_1.md` preamble: *"Hot-path
declaration: none"*).

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **One global pointer plus five section-local ones.** Rule 1 wants a pointer per decision; a
  literal reading yields fourteen. Whole-section removals have no site left to carry a pointer, so
  those four are named in the one global line after `## Non-goals`; sections that lost only part of
  their text carry their own.
- **The rationale keys on headings, not Decisions.** spec-001 predates the numbered-Decision
  convention. Two entries key to headings that no longer exist anywhere; each names the surviving
  sections its argument bears on, so the entry is still lookup-able from the spec.
- **Claims are recorded in the spec's tense, with a `claims the spec no longer makes` line.** The
  reader's rule in `BUILD.md` requires "any claim the decision once made and may no longer make".
  This pass records those claims *as the spec made them* and states in `## How to read this file`
  that whether the package still honours them is R2's determination. That is the only shape that
  discharges the reader's rule without doing R2's verification.
- **One HEAD read was made, and only to avoid asserting a falsehood.** The Registry entry says the
  third candidate (registry-tracked pending relations post-processed after every subclass is seen)
  is the approach that was taken. Verified read-only rather than taken from the plan's table:
  `grep -rn 'lazy_ref' django_strawberry_framework/` returns no `registry.py` hit (only the
  unrelated `mutations/fields.py::_lazy_ref`), while `registry.py` carries `PendingRelation`,
  `_pending`, `iter_pending_relations` / `discard_pending`, and `types/finalizer.py` carries
  `finalize_django_types`. This is a statement about which alternative won — a rationale-file
  obligation — not a reconciliation of spec text, which stays R2's.
- **The spec's two self-duplications were left in place.** `lazy_ref`'s candidate list and the
  `Meta.interfaces` parking claim each appeared twice; the copy inside a moved section moved, and
  the copy inside a surviving section stayed. Collapsing them would have been an R2 edit.

### Notes for Worker 3

- **The audit's sharpest question is over-cut, not under-cut.** Read `### What deliberately STAYED`
  first, then the six repairs, then look for a *seventh* place where a cut sentence was the only
  statement of a rule. Repairs 2 and 5 exist because that check found two; a third would be a High.
- The diff to read is `git diff -- docs/SPECS/spec-001-django_types-0_0_1.md` plus the new
  untracked `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`. Do not `git stash`,
  `git checkout` or `git restore` anything — the tree carries a concurrent session's work
  (`### Concurrent-session churn observed`).
- Re-run both verification commands yourself rather than accepting the quoted output; the
  21-anchor constraint is the one failure mode of this pass that is silent until `import_spec_terms`
  runs. The anchor with a single link is `definition-order-independence` (re-sited by this pass);
  `metachoice_enum_names` also has exactly one, in a paragraph this pass deliberately did not touch.
- A passage this pass left in the spec is **not** an R1 finding if the reason it looks wrong is that
  HEAD falsifies it. That is R2, by the build plan's own scoping. It *is* an R1 finding if the
  passage is deliberation or self-narration that should have moved.

### Notes for Worker 1 (spec reconciliation)

Carried into R2, from performing this move:

1. **`## N+1 strategy` and the `## get_queryset` O6 paragraph are unresolved dispositions.** The
   spec's own (now moved) cut-line argument says the section, the `DjangoOptimizerExtension` public
   name, and the optimizer-shaped sentences in `## Goal` / `## get_queryset` belong in `spec-002`.
   The slice list now points Slices 4-6 there; the prose was never lifted. R2 decides: restate,
   point elsewhere, or drop.
2. **The `Meta.interfaces` parking paragraph (D5) survives in `## DjangoType`** and its twin left
   with `## Post-slice-7 future work`. R2 owns the surviving copy.
3. **`## Registry`'s illustrative code still declares `lazy_ref`** (D2) and the prose sentence above
   it still says the registry exposes it. The rationale records which alternative actually won;
   R2 restates the surface.
4. **`## Current state`, `## What this enables immediately after implementation`, and the
   `examples/fakeshop/fakeshop/…` paths** are the spec's largest remaining stale-by-tense surface
   (D11, D14).
5. **Anchor budget for R2.** After this pass, `definition-order-independence` and
   `metachoice_enum_names` each have exactly one spec-body link; both sentences are ones R2 may want
   to rewrite. Re-check the anchor count as part of any rewrite of either, not after.

---

## Review (Worker 3)

Audit of the R1 rationale move. Everything below was re-derived from the working tree, not read out
of `## Move performed` — `BUILD.md` `## Claims are proven mechanically, never accepted on prose`
applies to every count and to every "I only moved it" claim in that section.

**What was re-derived, and how.** Byte counts by `wc -c` against the working tree and
`git show HEAD:<path> | wc -c` (read-only; no `stash` / `checkout` / `restore`, per the ban). The
move-vs-copy question by an 8-word-shingle overlap scan between the two files, code fences and
link-def blocks stripped, extending each hit to its maximal length
(`docs/builder/temp-tests/r1-spec001/overlap.py`). Link definitions, undefined refs, orphan defs,
group headers and on-disk path existence by
`docs/builder/temp-tests/r1-spec001/links.py`. Anchor budget by counting `][glossary-<id>]`
occurrences per anchor in **both** the working tree and the HEAD copy. Both verification commands
re-run in full.

### High:

None.

The specific defect this audit exists to catch — implementation-relevant contract leaving the spec
— did not occur. Walked every removal in `git diff -- docs/SPECS/spec-001-django_types-0_0_1.md`
and classified each as deliberation or contract; every normative statement inside a cut passage is
still stated in the spec. Detail under `### What looks solid`.

### Medium:

#### The anchor-budget handoff is wrong: **all 21** anchors have exactly one spec-body link, not two

`### Notes for Worker 3` and `### Notes for Worker 1` item 5 both state that
`definition-order-independence` and `metachoice_enum_names` are the anchors carrying exactly one
spec-body link, which reads as "the other nineteen have spare links". Measured, every one of the 21
has exactly one, both before and after this pass:

```
$ grep -o '\]\[glossary-[a-z0-9-]*\]' docs/SPECS/spec-001-django_types-0_0_1.md | sort | uniq -c
   1 ][glossary-aggregateset]
   1 ][glossary-apply-cascade-permissions]
   ... (21 ids, every count 1)
$ git show HEAD:docs/SPECS/spec-001-django_types-0_0_1.md > <scratch outside repo>   # same 21 x 1
```

There are no inline `](../GLOSSARY.md#…)` forms in either version, so the reference-style count is
the whole population.

Why it matters: the build plan calls the anchor budget *"the trap in this cycle"*, and R2 rewrites
spec prose against fifteen drift rows. The true constraint is that **every** glossary-linked
sentence in the spec is load-bearing — rewriting any one of them without re-siting its link drops
an anchor. A two-name watchlist invites R2 to rewrite the other nineteen sentences freely. The
harm is bounded (the build plan's own `### The 21-anchor constraint` lists all 21 and mandates a
`check_spec_glossary.py` re-run after every spec write, and that checker fails loudly on a drop),
which is why this is Medium and not High — but the artifact is what the next worker reads, and it
currently understates the constraint.

Recommended change: Worker 1 restates the budget as "all 21 anchors have exactly one spec-body link
each" in its `## Final verification (Worker 1)` section and carries that wording into R2's plan.
`ARTIFACT.md` forbids editing prior entries, so the correction lands as a restatement, not an
in-place edit. Escalated below.

### Low:

#### `## How to read this file` says "Two entries" and then lists three

`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` #"Two entries key to headings that no
longer exist in the spec at all" — the parenthetical in the same sentence names three
(`## Scope creep into the N+1 problem`, `## Post-slice-7 future work`, `## Open questions`), and
three entries exist: the headings at rationale lines 56, 250 and 289. `### Implementation notes`
repeats the same "Two entries" wording. One-word fix; recorded because it is the third asserted
count in this pass that did not survive re-derivation.

#### The repair inventory reports six; a seventh surviving-prose rewrite is not in it

`### Minimal repairs made to keep surviving prose coherent` lists six and says "Each is the smallest
edit that leaves a parsing sentence". The `## Suggested implementation slices` fold — three slice
entries collapsed into one `Slices 4-6:` line carrying new prose ("These are owned by
`spec-002-optimizer-0_0_2.md` (slices O1-O6)", "the optimizer is only their consumer") — is exactly
that shape and is the **largest** prose rewrite in the diff. It is covered by implementation step 6
and by the `### What moved` table, so nothing is hidden; the defect is that a reviewer told to
"verify each of the six repairs is faithful" would not have it in scope.

Verified independently, and it is faithful:

- The dropped clause *"The `__init_subclass__` flip that toggles the sentinel and the
  `plan_relation`-style downgrade itself move to the optimizer spec"* is not lost — the surviving
  `## get_queryset` paragraph states it directly, attributing the flip to
  `spec-002-optimizer-0_0_2.md` O6, so the symbol-ownership split still reads off the spec.
- `(slices O1-O6)` is supported by the cut text (Slice 4 named O1-O6, Slice 5 named O5, Slice 6
  named O6).
- One argument-direction shift, benign: in the cut text "the optimizer is the only consumer" is the
  reason the flip **moves**; in the new sentence it is appended as a reason the sentinel and helper
  **stay**. The proposition is true either way and the surviving text asserts nothing the spec did
  not already assert.

The same incompleteness appears once more in the rationale's `## Provenance of this record` "Moved"
bullet, which omits the choice-enum section opener's slice framing that its own entry records as
*Moved*.

#### Two spec-002 prose references now point into text that lives only in the rationale

`worker-1.md` `### Performing the rationale move` rule 3 requires that "no surviving cross-reference
points into moved text without naming the rationale file". Two survive, both in a file R1 may not
write:

- `docs/SPECS/spec-002-optimizer-0_0_2.md:9` — *"`spec-001-django_types-0_0_1.md` predicted that the
  optimizer half of its scope would eventually warrant its own document"*. That prediction was the
  cut-line paragraph of `## Scope creep into the N+1 problem` and is now only in the rationale.
- `docs/SPECS/spec-002-optimizer-0_0_2.md:80` — *"The visibility-leak / `Prefetch` downgrade
  discussion that motivated bundling the optimizer with `spec-001-django_types-0_0_1.md`
  originally"*. The bundling argument moved; the downgrade rule itself stayed.

Neither is a markdown link, so nothing is broken and no checker fires. Not held against R1 —
`spec-002` is outside its writable list and the build plan assigns the inbound-reference sweep to
R3. Routed below.

### DRY findings

#### Two "why" clauses are told twice, once in each file

The overlap scan found no wholesale copy leak — the longest shared run is 26 words — but two
clauses are present verbatim in both files as **present-tense argument**, which is the shape that
goes stale in one of them:

- 26 words, `## Scalar field conversion` vs the rationale's *Alternative rejected — `typing.Any`*:
  "a silent `Any` fallback masks unsupported columns at schema-build time and surfaces them as
  opaque type errors much later (Strawberry has no native `Any` scalar mapping)", plus a 12-word
  continuation ("fails fast with the field path in the message and a one-line …").
- 16 words, `## Choice field enum generation` vs the rationale's *Alternative rejected — label-based
  member names*: "are display strings consumers may translate or restyle, and coupling the GraphQL
  schema to them is [fragile]".

The rationale's own framing under-describes this: it says *"The **rule** stays in the spec; only the
'originally / instead' chronology came here"*, when in fact the reason-it-lost sentence came here
too. Recommended shape: the rationale keeps the chronology and the alternative's identity, and
defers the reason to the spec by pointer ("it lost for the reason the spec states at
[Scalar field conversion][spec-001-scalars]").

**Recorded as intentionally-rejected, not held.** `### DRY analysis` duplication-risk item 1 decided
this shape before the move — "the contract half was restated in the spec in present tense and the
deliberative half moved — the rationale then says explicitly which half stayed, so neither file
silently owns both" — and BUILD.md's reader rule independently requires the rationale carry "why
each [alternative] lost". The two obligations genuinely collide on one sentence. The recorded
reason stands; the only inaccuracy is the "only the chronology came here" wording, folded into the
Low above rather than tiered separately.

The three remaining overlaps are quotation-with-attribution, not duplication: the enum import-order
sentence (14 words) and the `search_fields` coordination note (8 words) are quoted inside
*"Deliberately not moved"* / *"it stays in the spec"* statements, and the relation-set list (14
words) sits inside the verbatim quote of the moved hand-off paragraph whose contract half was
promoted. Each is self-labelling about where ownership sits. No change recommended.

### Move-not-delete verification

Every removed passage is findable in the rationale. Walked the diff removal-by-removal:

| Removed from the spec | Found in the rationale |
|---|---|
| `## Scope creep` para 1 (scope statement) | entry 1, *Moved — the scope argument in full* (self-reference `This document is spec-001…` dropped; the build plan's reference table licenses "travels with it or is dropped") |
| `## Scope creep` para 2 (the seven-item enumeration) | entry 1, all seven items present |
| `## Scope creep` para 3 (reason + lockstep rejection) | entry 1, *Alternative rejected — two specs in lockstep* |
| `## Scope creep` para 4 (the cut line) | entry 1, quoted verbatim |
| `Deviation from earlier draft:` | entry 2, *Alternative rejected* (chronology) + rule restated in the spec |
| `Slice 2 implementation subset:` | entry 2, verbatim |
| `Deferred scalar conversions:` | entry 2, verbatim |
| choice-enum opener slice framing | entry 3, *Moved — the slice framing of the section opener*, quoted |
| label-vs-value library comparison | entry 3, verbatim |
| `Slice 2 -> Slice 3 hand-off:` | entry 4, verbatim |
| `Slice 3 status (post-implementation):` | entry 4, verbatim |
| three `lazy_ref` candidate bullets | entry 5, verbatim |
| slice `Status:` annotations (1, 2, 3, 7) | entry 6, all four |
| Slice 4 supersession narrative | entry 6, incl. both architectural issues, the surviving symbols and the O1-O6 split |
| Slice 5 / Slice 6 move reasons | entry 6 |
| `## Post-slice-7 future work` (6 items) | entry 7, all six |
| `## Open questions` (3 + recommendations) | entry 8, all three verbatim |

Nothing vanished. Two rewrites-in-place rather than moves — the scalar table's forward reference and
the relation forward-reference sentence — are covered under repairs 6 and the re-site.

### Over-cut sweep: the seventh place

`### Notes for Worker 3` asks for a seventh passage where a cut sentence was the only statement of a
rule. Enumerated every normative-sounding claim inside removed text and located each in the
surviving spec:

- unsupported-field-type raise -> repair 2 **and** the `convert_scalar` code block (`raise
  ConfigurationError(...)`), so it is stated twice in the spec independently of the repair.
- relation dispatch + the `fields = "__all__"` relation set -> repair 5.
- `Meta.fields = "__all__"` cardinality / M2M -> the surviving cardinality table.
- `AutoField` family -> `int` -> the surviving scalar table.
- `Meta.interfaces`: subclass `relay.Node` directly -> the surviving parking paragraph at
  `## DjangoType`.
- the `__init_subclass__` sentinel flip belongs to the optimizer spec -> the surviving
  `## get_queryset` O6 paragraph.
- `registry.lazy_ref(model)` exists on the registry surface -> the surviving `## Registry` sentence
  and its illustrative code block.

**One cut rule is deliberately not restated, and that is correct.** *"`convert_relation` looks up the
target via `registry.get(field.related_model)` and raises `ConfigurationError` … if the target is
not yet declared"* left with `Slice 3 status (post-implementation)` and is nowhere in the spec.
Restating it would have re-entrenched the spec's own self-contradiction (the surviving contract
sentence says forward references make definition order irrelevant), and drift row D3 records HEAD as
order-independent. The rationale carries it verbatim and lists it under *Claims the spec no longer
makes*. No seventh over-cut found.

One process observation, not a finding: `worker-1.md` rule 2 ("Delete — do not move — prose the
current decisions have falsified") and `BUILD.md`'s reader rule ("any claim the decision once made
and may no longer make") pull in opposite directions on exactly this paragraph. Moving it is the
defensible reading here — Worker 2 never reads the rationale, so no builder can implement it, and
every such claim is explicitly tense-marked in `## How to read this file`.

### The 21-anchor constraint — re-run, not accepted

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
OK: 21 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 48 done cards have glossary links.
exit=0
```

Both match the artifact's quoted output character-for-character, and both match the build plan's
pre-move baseline. Stronger than "no anchor lost its last link": the per-anchor counts are
**identical** to HEAD's — 21 anchors, one link each, before and after — so the move is
anchor-neutral rather than merely non-fatal.

**The `definition-order-independence` re-site reads naturally**, not as a link parked to satisfy a
checker. Its new home is
`docs/SPECS/spec-001-django_types-0_0_1.md` #"use Strawberry forward references, so that": the
linked phrase *is* the concept, in the one sentence that states it normatively, in the section the
concept belongs to. The old home (`Slice 3 status`) was a paragraph asserting the **opposite**
(dependency order mandatory), so the link moved from a passage contradicting the glossary term to
the passage that states it. Nit only: the comma added before "so that" is unnecessary.

### Markdown link convention

Checked mechanically for both files (`docs/builder/temp-tests/r1-spec001/links.py`):

- Reference-style throughout; no inline `](path)` cross-file links in either body outside code
  fences.
- One `<!-- LINK DEFINITIONS -->` block each, with all 10 canonical group headers in the exact
  START.md order, empty groups retained.
- Spec: 22 defs / 22 used refs, 0 undefined, 0 orphaned. The new `[spec-001-rationale]` def is
  correctly filed under `<!-- docs/SPECS/ -->` (subdirectory shares the parent group, per START.md's
  closed-list rule) and the `docs/` glossary group stayed alphabetical.
- Rationale: 11 defs / 11 used refs, 0 undefined, 0 orphaned; `docs/SPECS/` group alphabetical.
- **Depth is right**: `../spec-001-…md` / `../spec-002-…md` for `docs/SPECS/` siblings,
  `../../builder/BUILD.md` for a `docs/` target from `docs/SPECS/appx/`.
- **Every path disk-exists-checked** by `os.path.exists` on the normalized join, both files, all 33
  defs: all present.
- Every in-page anchor the rationale cites resolves against a surviving spec `##` heading —
  `#goal`, `#djangotype` (heading is backticked; backticks do not enter the slug),
  `#scalar-field-conversion` (heading is itself a link; the rendered text slugs),
  `#choice-field-enum-generation`, `#relation-field-conversion`, `#registry`, `#n1-strategy`
  (`N+1` -> `n1`), `#suggested-implementation-slices`. No rationale anchor points at a removed
  heading.
- No inbound link anywhere in the repo targets a removed spec-001 section
  (`grep -rn 'scope-creep\|open-questions\|post-slice-7'` over `docs/`, `KANBAN.md`, `README.md`
  returns only other specs' own `#risks-and-open-questions` anchors).
- `uv run python scripts/check_trailing_commas.py --check` on both files plus this artifact: exit 0.
  `git diff --check` on the spec: exit 0.

### Rationale file keyed to the spec

`BUILD.md` `## Spec rationale extraction`'s reader rule, checked entry by entry. All eight entries
name their spec section by heading **and** carry a resolving anchor link (`Spec: [heading][ref]`, or
`Bears on [heading][ref]…` for the three whose heading no longer exists). Alternatives-rejected are
present and reasoned wherever one existed (`typing.Any`; label-based members; two-specs-in-lockstep;
auto-attached optimizer; the two unchosen `lazy_ref` approaches, with the third marked as taken).
Changes-undergone are present (the relation entry's self-contradiction record; the scope entry's
"the second half of the cut was never performed"). Claims-no-longer-made lines are present on the
four entries that carry retracted claims. No entry is unlookup-able.

### Byte accounting

| File | Claimed | Measured |
|---|---|---|
| spec, before | 52,341 | 52,341 (`git show HEAD:… \| wc -c`) |
| spec, after | 42,480 | 42,480 (`wc -c`) |
| delta | -9,861 | -9,861 |
| rationale | 23,370 | 23,370 |

The rationale exceeding the bytes removed is accounted for and is not a copy leak — the overlap scan
above is the mechanical evidence for that, and it puts the total shared-text budget at well under
100 words.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty: `__all__` and the re-export list are
unchanged. This item writes no `.py` file at all.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Applicable — the item edits an archived spec and creates its archived companion.

- Version strings: untouched. The spec carries no status/header block (confirmed: line 1 is the
  title, line 3 opens `## Problem statement`), so no target-release or status line could drift.
- No KANBAN card movement in this item's diff. `KANBAN.md` / `KANBAN.html` churn in the tree is the
  concurrent spec-048 card wrap — verified by reading it: the added rows are
  `Meta.filesystem_path_fields`, `DjangoFilePathType`, `DjangoImagePathType`, `ErrorPolicy`,
  `DjangoErrorPolicyExtension`, all `shipped (0.0.14)`, i.e. spec-048's surface, not spec-001's.
  The artifact's attribution is correct and the files were correctly left alone (`AGENTS.md` 34).
- Archival: no move performed and none owed — the spec and its `-terms.csv` were already at
  `docs/SPECS/` / `docs/SPECS/appx/`, and the new companion was written **directly** to
  `docs/SPECS/appx/`, never to `docs/` first. Confirmed by `git status` (single `??` entry at the
  archived path).
- The terms CSV was not touched (`git status` clean for
  `docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv`) — correct; the plan forbids buying an
  anchor by editing the CSV.
- No "coming soon" / "planned" / old-version wording introduced. One residual staging phrase the
  pass did not reach is noted for R2 below (`Slice 7 supports both forms transparently`).
- No script-rendered doc regenerated; none was in scope.

### `scripts/review_inspect.py`

Skipped. Reason: this pass touches no `.py` file — the diff is two Markdown files — so none of the
three Worker 3 trigger conditions in `BUILD.md` `### When to run the helper during build` (new
`.py`, a file under `optimizer/` or `types/`, 30+/50+ new logic lines) is met, and the helper's
repeated-literal output has no subject.

### Failability proofs

Audited: `### Failability proofs` records `None; this pass introduced no new boundary, guard, gate,
or rejection path.` Confirmed correct — the diff contains no executable code, so there is no
boundary that could meet the re-run floor. `worker-3.md`: "An empty re-run set is legal only when
the diff introduces no boundary that meets the floor." That condition holds. Re-run set: empty.

### Hot-path budget

No number owed. The build plan preamble declares `Hot-path declaration: none`, and the diff adds no
runtime cost of any kind. Its absence is not a finding.

### Floor verification

No floor run owed. The build plan preamble declares `Floor-verification scope: none`, and the diff
touches no Django / Strawberry / channels seam.

### What looks solid

- **The move is a move.** Seventeen removed passages, every one located in the rationale, most
  verbatim. The overlap scan is the mechanical proof that it is not also a copy.
- **The carve-out held.** The PR #583 paragraph — *"This rule must be part of the first spec because
  otherwise FK joins bypass per-type visibility filtering and leak rows"* — is still in the spec, in
  `## N+1 strategy`, with its issue #572 / PR #583 provenance intact. This is the exact
  implementation-relevant "why" `worker-1.md` names as the one place the move can itself cause a
  defect, and the pass identified it unprompted in `### What deliberately STAYED`.
- **Anchor-neutral.** Not merely "the checker still passes": every one of the 21 anchors has the
  same link count after the move as at HEAD.
- **The `definition-order-independence` re-site is an improvement, not a rescue.** It moved from a
  paragraph asserting the opposite of the glossary term to the sentence that states it normatively.
- **Repairs 2 and 5 are the right call and are faithfully executed.** Both restate a rule that lived
  only inside a chronology paragraph; both were checked against the spec's own illustrative code and
  cardinality table and neither invents, weakens, or strengthens the claim. Repair 2 does convert a
  descriptive past-tense sentence ("Slice 2 instead raises") into a normative "must raise" — that is
  the correct direction for a contract and it matches the `convert_scalar` code block.
- **Restraint on R2's axis.** Several passages that look wrong (the `lazy_ref` code block, the
  `Meta.interfaces` parking paragraph, `## Current state`) were left alone with the reason recorded,
  and no removed claim was reconciled against HEAD. Exactly one HEAD read was made and it is
  disclosed, bounded, and used only to avoid asserting a falsehood about which alternative won.
- **Pointer discipline.** Seven `[rationale file][spec-001-rationale]` uses (one global after
  `## Non-goals` + six section-local), each naming what left that section, so no reader can miss
  that deliberation exists. The pointer count is one above the "one global plus five" the notes
  describe because the scalar-table forward-reference repair also carries one — an undercount in the
  artifact's favour, not worth a finding.

### Temp test verification

Two throwaway scripts, both under `docs/builder/temp-tests/r1-spec001/` (gitignored), both read-only
over the two Markdown files:

- `overlap.py` — maximal shared-shingle scan between spec and rationale. This is what turned "it was
  a move, not a copy" from a prose claim into a measurement, and what produced the DRY finding.
- `links.py` — link-definition audit: undefined refs, orphan defs, group headers, `os.path.exists`
  per path, for both files.

Disposition: neither promotes to a permanent test — there is no package behavior to pin and no
production code in the diff. `overlap.py` is a candidate `scripts/` helper for future rationale
moves; raised as a suggestion under `### Notes for Worker 1`, not as a finding.

### Notes for Worker 1 (spec reconciliation)

1. **`Escalated:` — correct the anchor budget before writing R2's plan.** The Medium above. The
   artifact's two anchor-budget sentences name two anchors; the measured answer is all 21, each with
   exactly one spec-body link. `ARTIFACT.md` forbids editing a prior entry, so the resolution paths
   are: (a) restate the corrected budget in `## Final verification (Worker 1)` on this artifact
   **and** carry it into R2's plan as the operative constraint — recommended, and it costs one
   sentence; or (b) re-loop R1 for an artifact correction, which under Deviation 3 has no declared
   dispatch target since there is no Worker 2. Path (a) is why this pass is `review-accepted` rather
   than `revision-needed`: the deliverable is clean and mechanically verified, and the defect is in a
   handoff note that only Worker 1's already-scheduled next pass can restate. Operative wording for
   R2: *every glossary-linked sentence in the spec is the sole link for its anchor; any rewrite of
   one re-sites its link in the same edit, and `check_spec_glossary.py` is re-run per write.*
2. **Two counts in this artifact and its rationale did not survive re-derivation** (the "Two
   entries" / three, and "Six" repairs / seven). Both Lows above. Worth folding into R2's practice
   as much as fixing here — three asserted counts, three misses.
3. **Residual slice narration the pass did not reach.** `### Django TextChoices / IntegerChoices
   support` still reads *"Slice 7 supports both forms transparently"*, three subsections below the
   opener this pass deliberately de-sliced; `### Test surface` still reads *"the fixture is the only
   path that exercises this slice"*; `### Tests` still reads *"slice 7 reuses the same fixture"*.
   These are self-narration on R1's axis rather than HEAD-drift on R2's, but they are one-word edits
   inside sentences R2 will be rewriting anyway (they name `tests/test_choice_enums.py`, which drift
   row D10 says does not exist). Recommend R2 absorbs them rather than re-looping R1.
4. **Two `spec-002` prose references now point into moved text** (Low above): `spec-002:9` and
   `spec-002:80`. Neither is a link, so nothing is broken, but `worker-1.md` rule 3 wants the
   rationale named. The build plan already routes the inbound-reference sweep to R3; recommend R3
   picks these two up, since `spec-002` is outside R1's writable list.
5. **The rule-2-versus-reader-rule tension** on `Slice 3 status (post-implementation)` (recorded
   under `### Over-cut sweep`) will recur in R2, which is explicitly about prose HEAD falsifies.
   R1's shape — move it, quote it in the spec's own tense, mark it under *Claims the spec no longer
   makes* — is a reasonable precedent worth stating once in R2's plan so it is not re-decided per
   row.
6. **`overlap.py` as a `scripts/` helper.** The maximal-shingle scan is the only thing that can turn
   "it was a move, not a copy" into a measurement, and every future spec's rationale extraction owes
   that proof. Maintainer's call, not a build item; raised here so it reaches them.
7. **R1 did not do R2's work.** Confirmed against the diff: no drift row D1-D15 is touched, no claim
   is reconciled against HEAD, and the one HEAD read made is disclosed and scoped to which
   alternative won. The last checklist box is correctly ticked. Beyond D1-D15, the only further
   drift noticed while reading is item 3 above (the `tests/test_choice_enums.py` narration in
   `### Test surface` / `### Tests`, an extension of D10's surface, not a new row).

### Review outcome

`review-accepted`.

Every High-tier concern this audit exists to catch was checked mechanically and came back clean: the
move is a move, nothing load-bearing left the spec, the carve-out held, no text is duplicated as
live prose beyond two disclosed clauses, the rationale is keyed and lookup-able, all six declared
repairs (and the seventh undeclared one) are faithful, and the 21-anchor constraint is not merely
intact but unchanged from HEAD.

One Medium and three Lows remain, all of them in the artifact's own prose rather than in the
deliverable. The Medium is escalated to Worker 1 under `### Notes for Worker 1` item 1 with its
resolution paths, per `worker-3.md`'s escalation clause: under Deviation 3 this item has no Worker 2,
so `revision-needed` would leave Worker 0 without a declared dispatch target, while Worker 1's
final-verification pass both owns the artifact's remaining sections and writes the plan the
correction has to reach.

---

## Final verification (Worker 1)

Fresh Worker 1 spawn; no memory of the pass that performed the move. Everything below was
re-derived from the working tree. Worker 3 set `review-accepted` with one Medium and three Lows
escalated here because Deviation 3 gives R1 no Worker 2 to route a `revision-needed` to; all four
are resolved in this section, plus the residual slice narration Worker 3's pass did not reach.
`ARTIFACT.md` forbids editing a prior entry, so every correction below is a **restatement**, never
an in-place edit of `## Move performed` or `## Review (Worker 3)`.

### Spec status-line re-verification

Re-read `docs/SPECS/spec-001-django_types-0_0_1.md` lines 1-5. Confirmed again: **no status/header
block**. Line 1 is `# Spec: DjangoType Foundation`, line 2 blank, line 3 `## Problem statement`.
There is no target-release, status, owner, or predecessor line for this build to have falsified,
and this build deleted no predecessor doc a header could point at. Nothing to edit. The stale
*body* claims (`## Current state`, the tense of the scalar table, the example paths) remain R2's
axis, unchanged by this pass.

### Finding 1 (Medium) — the anchor budget, re-measured and restated

Re-measured rather than accepted from either prior section, per `BUILD.md`
`## Claims are proven mechanically, never accepted on prose` — shortest distinctive token,
occurrences counted, not matching lines:

```
$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-001-django_types-0_0_1.md \
    | sort | uniq -c | awk '{print $1}' | sort | uniq -c
  21 1
$ grep -c 'GLOSSARY\.md#' docs/SPECS/spec-001-django_types-0_0_1.md
21          # all 21 are link *definitions*; the body carries no inline ](../GLOSSARY.md#…) form
```

Same measurement against the read-only HEAD copy (`git show HEAD:… > <scratch outside the repo>`):
also 21 ids at exactly 1 occurrence each. So the corrected statement is Worker 3's, confirmed
independently and now including my own edits below:

> **All 21 anchors have exactly one spec-body link each — before the move, after the move, and
> after this pass.** There are no spare links anywhere in the spec. `definition-order-independence`
> and `metachoice_enum_names` are not a two-name watchlist; they are two of twenty-one.

The operative constraint for R2, in the form its planning pass can act on directly:

> **Every glossary-linked sentence in spec-001 is the sole link for its anchor.** Any rewrite,
> merge, or deletion that touches one of the 21 linked sentences must re-site that anchor's link
> into surviving *contract* prose in the same edit — never rescue it by keeping narration, never
> by editing `docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv`. Re-run
> `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md`
> after **every** spec write, not once at the end.

**The measured concentration is what makes this operative rather than decorative**, and no prior
section reports it. Anchor line map at the close of this pass:

| Spec section | Line(s) | Anchors carried |
|---|---|---|
| `## Problem statement` | 5 | `filterset`, `orderset`, `aggregateset` |
| **`## Current state`** | 9, 13, 15 | `djangotype`, `djangoconnectionfield`, `apply_cascade_permissions`, `relay-node-integration`, `djangooptimizerextension`, `only-projection` |
| `## Non-goals` | 43 | `per-field-permission-hooks` |
| `## DjangoType` | 72, 74, 76, 78, 80, 82 | `metamodel`, `metafields`, `metaexclude`, `metainterfaces`, `metaname`, `metadescription` |
| `## DjangoType` | 101 | `configurationerror` |
| `## Scalar field conversion` | 146 (the heading itself) | `scalar-field-conversion` |
| `## Scalar field conversion` | 158 | `bigint-scalar` |
| `## Choice field enum generation` | 305 | `metachoice_enum_names` |
| `## Relation field conversion` | 336 | `definition-order-independence` |

Two consequences R2 must plan around, both falling out of that map:

1. **`## Current state` is the single densest anchor site in the spec — six of twenty-one — and it
   is simultaneously drift rows D11 and D14, the largest stale-by-tense surface R2 owns.** A
   rewrite or removal of that section drops six anchors at once. It is the highest-risk edit in
   R2's whole scope and should be planned as a re-siting exercise first and a prose rewrite second.
   The six concepts all still exist in the package, so surviving contract prose to re-site into is
   available; naming the destination sentence per anchor **before** editing is the cheap order.
2. **`## [Scalar field conversion][glossary-scalar-field-conversion]` is a heading that is itself a
   link.** Rewording that heading changes both the anchor's link site and the slug
   `#scalar-field-conversion`, which the rationale file cites twice
   (`[spec-001-scalars]`) and the `## Post-slice-7 future work` / `## Open questions` entries cite
   again. Leave the heading text alone, or fix the rationale's link definitions in the same edit.

### Finding 2 (Low) — "Two entries" where three exist: fixed in the rationale

Verified the count myself before changing it: entries keyed to headings that no longer exist in the
spec are three — `### Whole-document scope … (former ## Scope creep into the N+1 problem)`,
`### ## Post-slice-7 future work …`, and `### ## Open questions …`. `## How to read this file` now
reads **"Three entries"**. The identical wording in this artifact's `### Implementation notes` is a
prior entry and stays as written; this restatement is its correction.

### Finding 3 (Low) — the repair inventory, corrected

Re-derived from `git diff -- docs/SPECS/spec-001-django_types-0_0_1.md` by classifying every added
prose line, rather than by re-reading the inventory. The correct accounting of R1's move is
**eight edits to surviving spec prose**, not six:

| # | Edit | Declared? |
|---|---|---|
| 1 | Global rationale pointer after `## Non-goals` | yes — repair 1 |
| 2 | Unsupported-field-type raise restated as present-tense contract | yes — repair 2 |
| 3 | Choice-enum section opener de-sliced | yes — repair 3 |
| 4 | Sanitization rule kept, library comparison cut | yes — repair 4 |
| 5 | Relation dispatch + `fields = "__all__"` relation set promoted to contract | yes — repair 5 |
| 6 | Scalar table's dangling forward reference repaired | yes — repair 6 |
| 7 | `definition-order-independence` re-sited onto the surviving contract sentence | declared, but outside the numbered inventory |
| 8 | **The `Slices 4-6` fold** — three slice entries collapsed into one line carrying new prose (`These are owned by spec-002-optimizer-0_0_2.md (slices O1-O6)` … `the optimizer is only their consumer`) | **not declared** |

Edit 8 is the largest prose rewrite in the diff and is Worker 3's seventh. I re-verified it faithful
independently: the dropped clause *"The `__init_subclass__` flip that toggles the sentinel and the
`plan_relation`-style downgrade itself move to the optimizer spec"* survives in `## get_queryset`,
which states the flip and attributes it to `spec-002-optimizer-0_0_2.md` O6, so the
symbol-ownership split still reads off the spec; `(slices O1-O6)` is supported by the cut text; and
the argument-direction shift on *"the optimizer is only their consumer"* asserts nothing the spec
did not already assert.

Completing the accounting so the number is re-derivable rather than asserted:

- **Seven** `[rationale file][spec-001-rationale]` pointer uses (`grep -c` = 7): one global after
  `## Non-goals`, plus Scalar field conversion x2 (the section pointer and edit 6's repair),
  Choice field enum generation, Relation field conversion, Registry, Suggested implementation
  slices. The `## Move performed` prose describes "one global plus five"; measured, it is seven.
- **Four pure status cuts** that left a parsing sentence with no rewrite: the Slice 1 / 2 / 3
  `Status:` strips and the Slice 7 `Status: shipped. With Slices 4 through 6 moved …` strip. Not
  repairs.
- **One borderline** counted under the pointer budget rather than as a repair: `## Registry`'s
  `"Slice 3 picks one of:"` clause was replaced by a pointer clause on the same line. The kept
  clause is byte-identical; only the de-sliced lead was substituted.

**This is now the fourth asserted count in this cycle that did not survive re-derivation** — see
also the shared-text budget under `### Independent re-derivation` below. Carried into memory as a
practice note, not just fixed here.

### Finding 4 (Low) — the two `spec-002` references: handed over explicitly, not resolved here

Confirmed both against the tree:

- `docs/SPECS/spec-002-optimizer-0_0_2.md:9` — *"`spec-001-django_types-0_0_1.md` predicted that the
  optimizer half of its scope would eventually warrant its own document"*. That prediction is the
  cut-line paragraph of `## Scope creep into the N+1 problem`, now only in the rationale.
- `docs/SPECS/spec-002-optimizer-0_0_2.md:80` — *"The visibility-leak / `Prefetch` downgrade
  discussion that motivated bundling the optimizer with `spec-001-django_types-0_0_1.md`
  originally"*. The bundling argument moved; the downgrade rule itself stayed in `## N+1 strategy`.
- Also checked, and **not** affected: `:56` (a heading) and `:57` (*"Slices 4-6 are superseded by
  this optimizer spec family"*), which points at the spec-001 slice list — text that survives and
  still says exactly that. No third reference.

**Judgement: this does not belong to R1 or to R2, and I am handing it to R3.** Reasoning, stated so
R3 does not re-derive it:

- The dangling references are **in `spec-002`**, not in spec-001. Nothing in spec-001 points into
  its own moved text — `worker-1.md` rule 3 is satisfied on the file R1 owns. `spec-002` is outside
  R1's writable list and outside R2's, whose entire deliverable is spec-001-versus-HEAD.
- The build plan already routes the inbound-reference sweep to R3 (`### Every reference TO
  spec-001`, which lists `spec-002:9`, `:56`, `:57`, `:80` verbatim as R3's verification rows), and
  the plan's own instruction for that table is "only edits if one is wrong". Two of the four rows
  are now wrong in a way the table could not have predicted, because R1 created the file they
  should name.
- The fix is a **pointer, not new narration** — the minimum discharge is naming the companion, e.g.
  appending *"(that prediction is recorded in `appx/spec-001-django_types-0_0_1-rationale.md`)"* at
  `:9` and *"…, recorded in `appx/spec-001-django_types-0_0_1-rationale.md`"* at `:80`. Neither
  reference is a markdown link, so nothing is broken today and no checker fires; the obligation is
  legibility, not repair.
- One mechanic R3 must not miss: `spec-002` is a spec file, so under `BUILD.md`
  `## Spec reconciliation` the edit is **Worker 1's to make**, not R3's Worker 2's, even though R3
  has a real Worker 2 pass for its durable-doc work. R3's plan should assign these two lines to its
  own Worker 1 pass explicitly.

### Residual slice narration — cleared here, on R1's axis

Worker 3 named three residuals its pass did not reach and recommended R2 absorb them. I cleared all
three instead: each is pure de-narration that changes no claim about HEAD, so none needs the
reconciliation that would make it R2's, and leaving self-narration in the spec is precisely the
defect R1 exists to remove (`BUILD.md`: *"the spec … never narrates its own history"*).

1. `### Django TextChoices / IntegerChoices support` — *"Slice 7 supports both forms transparently"*
   -> *"Both forms are supported transparently"*. The mechanism clause (*"the iteration over
   `field.choices` treats them identically"*) is untouched.
2. `### Test surface` — *"the fixture is the only path that exercises this slice"* -> *"… that
   exercises choice-field enum generation"*.
3. `### Tests` (`## Files to add`) — *"and slice 7 reuses the same fixture for the cross-type
   enum-reuse test"* -> *"and the cross-type enum-reuse test reuses the same fixture"*.

Edits 2 and 3 sit inside sentences that also name `tests/test_choice_enums.py`, which drift row D10
says does not exist at HEAD. **That file name and every other HEAD claim in both sentences were
deliberately left alone** — D10 stays whole for R2, and the de-narration does not pre-empt it.

Slice references I considered and deliberately left, so R2 does not read their survival as an
oversight:

- `## get_queryset`'s O6 paragraph (line 443, *"since Slice 1's scaffolding"*) and `## N+1
  strategy`'s *"Resolver-to-type tracing (Slice 4)"* / *"the simple Slice 4 cardinality rule"*
  (469, 473) — mechanism, and already drift rows / R2 disposition calls. `worker-1.md`: when it is
  unclear whether a sentence is deliberation or instruction, it stays.
- `## Suggested implementation slices` itself, including *"(Slice 2 deferred it)"* on the Slice 7
  entry — a slice list is a plan, and cross-slice sequencing is its own vocabulary. Its *status*
  annotations were the narration, and those left with R1.
- The `Meta.interfaces` parking paragraph's *"Until a future slice injects declared interfaces"*
  (144) — a status claim, drift row D5, explicitly reserved for R2 by `## Move performed`.
- The three rationale pointers (45, 245, 361, 618) that name what moved by slice. Naming the moved
  content is rule 1's requirement, not narration.

### Dispatched findings checklist — audit

Walked all eleven `- [x]` boxes in `## Plan (Worker 1)` against the diff and my own re-derivations
below. **All eleven landed; none is un-ticked, none is over-ticked, nothing is deferred.** The two
that could only be discharged by re-running are the two verification commands, both re-run in
`### Validation run` with identical output. Box 11 ("R2's work was not done here") holds for this
pass as well: my five edits touch no drift row D1-D15 and reconcile nothing against HEAD.

### Independent re-derivation (claims proven mechanically)

`worker-1.md` `### Verifying relocation / promotion claims`: R1's central claim is a relocation
claim — *"it was a move, not a copy"* — so I ran the proof myself rather than reading Worker 3's
acceptance as discharge.

Maximal-shared-shingle scan (n=8), code fences and link-definition blocks stripped from both files,
each hit extended to its maximal run:

```
spec body words: 4335   overlapping runs >= 8 words: 11
total overlapping words: 150
   27w  a silent any fallback masks unsupported columns at schema build time and surfaces them ...
   23w  labels are display strings consumers may translate or restyle and coupling the graphql ...
   16w  consumers who want a stable predictable name should declare the djangotype they want to win first
   14w  relations on category items properties item category entries property category and entry property item
   14w  fails fast with the field path in the message and a one line fix
   10w  the alternatives each decision rejected and why each lost the
   10w  fk joins bypass per type visibility filtering and leak rows
    9w  the first type defined wins the enum s name
    9w  spec ships the last subsystem the example depends on
    9w  move every search_fields line into the doubly commented set
    9w  injects declared interfaces into cls __bases__ before strawberry type
```

**Conclusion confirmed, one number corrected.** 150 shared words against a 4,335-word spec body is
3.5% — there is no wholesale copy, and R1's move is a move. But `## Review (Worker 3)`
`### Byte accounting` puts "the total shared-text budget at well under 100 words"; measured at n=8
it is 150 across 11 runs, and its longest run is 27 words, not 26. The conclusion is unaffected;
the count is the fourth in this cycle that did not survive re-derivation, which is why it is
recorded rather than waved through.

Classification of the 11 runs, so the number is interpretable:

- **Two are live prose in both files** — the `typing.Any` reason clause (27w + its 14w
  continuation) and the label-fragility clause (23w). These are the DRY finding Worker 3 recorded
  as **intentionally rejected**, and that disposition stands: `BUILD.md`'s reader rule requires the
  rationale carry *why each alternative lost*, while the carve-out in `worker-1.md` requires the
  spec keep implementation-relevant "why". The two obligations genuinely collide on one sentence,
  and the spec is the copy a builder reads. **What was inaccurate was the rationale's own framing**
  — *"only the 'originally / instead' chronology came here"* — and I fixed that sentence in the file
  I own (see `### Spec changes made`). No text moved.
- **Eight are quotation-with-attribution**, each sitting inside a rationale sentence that says
  where ownership lives (*"Deliberately not moved"*, *"it stays in the spec"*, or inside the
  verbatim quote of a moved paragraph whose contract half was promoted): the enum import-order
  sentence, the relation set, the PR #583 leak clause, the enum-name-wins sentence, and the two
  `search_fields` / `Meta.interfaces` quotes.
- **One is the pointer echoing its target** — the spec's new global pointer paragraph describing
  what the rationale contains, against the rationale's own preamble describing the same. That is
  the intended shape of a pointer, not duplication.

Re-derived independently and confirmed: spec `42,483` bytes (`wc -c`) against HEAD's `52,341`
(`git show HEAD:… | wc -c`) = **-9,858 (-18.8%)**; the three-byte drift from the `42,480` reported
in `## Move performed` is this pass's own de-narration edits. Rationale `24,011` bytes.

### Link and anchor resolution after my edits

Re-run over **both** files after every edit in this pass:

- Reference-style throughout; one `<!-- LINK DEFINITIONS -->` block each; all 10 canonical group
  headers present in START.md's exact order, empty groups retained (verified positionally, both
  files).
- Spec: 22 defs / 22 used refs, 0 undefined, 0 orphaned. Rationale: 11 / 11, 0 / 0.
- **Every path `os.path.exists`-checked on the normalized join from its own file's directory — all
  33 defs across both files resolve on disk.**
- All 8 in-page anchors the rationale cites resolve against surviving spec `##` headings
  (`#goal`, `#djangotype`, `#scalar-field-conversion`, `#choice-field-enum-generation`,
  `#relation-field-conversion`, `#registry`, `#n1-strategy`, `#suggested-implementation-slices`);
  unresolved set empty.
- No inbound reference anywhere in the tree targets a removed spec-001 heading — re-derived after
  the concurrent commit regenerated `KANBAN.md` / `KANBAN.html`; the only `Scope creep` /
  `Post-slice-7` / `Open questions` hits outside `docs/builder/` are the rationale naming its own
  entry keys, plus unrelated `START.md`-scope-creep-rule prose in specs 034-040 and 052.
- The set of files referencing `spec-001-django_types-0_0_1` is unchanged from the build plan's
  table (KANBAN.md/html, spec-002, spec-005, spec-006, spec-037) — no new inbound direction.

### Validation run

Re-run after **every** edit this pass made, per the 21-anchor rule:

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
OK: 21 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 48 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-001-django_types-0_0_1.md \
    docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md \
    docs/builder/bld-001-r1-rationale_move.md
exit=0

$ git diff --check -- docs/SPECS/spec-001-django_types-0_0_1.md
exit=0
```

Both hold the build plan's pre-move baselines exactly. **Note the DB moved under this cycle** (see
below) and `import_spec_terms --check` still passes against the new committed
`examples/fakeshop/db.sqlite3` — the 48-card baseline is re-established, not inherited.

No `pytest` and no `ruff`: this pass, like R1 itself, writes no `.py` file. No focused test scope
exists for a Markdown move and the plan calls for none.

### Concurrent-session state changed: the churn was COMMITTED

`## Move performed` `### Concurrent-session churn observed` and the build plan's *"Grew during item
R1"* list are both now stale, in the cycle's favour. The concurrent spec-048 session **committed**
at `b29b851e` (*"docs(spec-048): extract the rationale companion and make the ledger agree with
it"*), a child of the `fe2249fd` this cycle started from:

```
$ git diff --name-status fe2249fd..HEAD
M  KANBAN.html
M  KANBAN.md
M  docs/SPECS/appx/spec-027-filters-0_0_8-terms.csv
A  docs/SPECS/appx/spec-048-secure_output_defaults-0_0_14-rationale.md
M  docs/SPECS/appx/spec-048-secure_output_defaults-0_0_14-terms.csv
M  docs/SPECS/spec-048-secure_output_defaults-0_0_14.md
M  examples/fakeshop/db.sqlite3

$ git status --short
 M docs/SPECS/spec-001-django_types-0_0_1.md
?? docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md
?? docs/builder/bld-001-r1-rationale_move.md
?? docs/builder/build-001-django_types-0_0_1.md
```

Every file the plan listed as baseline-dirty or as R1-era growth is clean again; the only modified
tracked file in the tree is this cycle's spec, and the three untracked paths are this cycle's own.
Nothing was reverted and nothing of the concurrent session's was touched (`AGENTS.md` rule 34) —
this is a report of a state change, not an action. Consequences are routed to R3 below.

### Summary

R1 is accepted. The move is a move; the spec reads as a clean current contract with no
self-narration left on R1's axis; the deliverable was clean when Worker 3 audited it and is clean
now. This pass changed no contract and moved no text — it corrected four prose defects Worker 3
raised (one restatement, three fixes in files Worker 1 owns), cleared the three residual slice
narrations Worker 3's pass did not reach, re-derived every mechanical claim rather than accepting
it, and wrote the anchor constraint R2's planning pass depends on. Spec `52,341 -> 42,483` bytes
(**-9,858, -18.8%**) against HEAD, paid back on every future spawn; rationale `24,011` bytes at
`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`, tracked and untracked-pending-commit.

### Spec changes made (Worker 1 only)

**Seven edit sites** — three in the spec, four in the rationale — all on R1's axis (self-narration
removal, and factual correction of prose in files Worker 1 owns). None reconciles a claim against
HEAD; none touches drift rows D1-D15; none changes a contract; none altered any anchor's link
count. (Counted against the numbered list below as it was written, not asserted beside it.)

**`docs/SPECS/spec-001-django_types-0_0_1.md`**

1. Line 280, `### Django TextChoices / IntegerChoices support` — *"Slice 7 supports both forms
   transparently"* -> *"Both forms are supported transparently"*. Reason: residual slice narration
   on R1's axis, three subsections below the opener R1 de-sliced; the mechanism clause is unchanged.
2. Line 313, `### Test surface` — *"the only path that exercises this slice"* -> *"… that exercises
   choice-field enum generation"*. Reason: same; the `tests/test_choice_enums.py` claim (D10) is
   deliberately untouched and stays R2's.
3. Line 640, `### Tests` under `## Files to add` — *"and slice 7 reuses the same fixture for the
   cross-type enum-reuse test"* -> *"and the cross-type enum-reuse test reuses the same fixture"*.
   Reason: same.

**`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`** (Worker 1's file; append-only during
a build, and these are corrections to this pass's own prose, not to moved text)

4. `## How to read this file` — *"Two entries key to headings that no longer exist"* ->
   *"Three entries"*. Reason: Worker 3's Low; the parenthetical in the same sentence already named
   three and three entries exist. Count re-derived before editing.
5. `## Provenance of this record`, `**Moved**` bullet — added the slice framing of the
   `## Choice field enum generation` section opener, and made the slice-list item name the Slice 4
   supersession narrative and the Slice 5 / Slice 6 move reasons the annotations carried. Reason:
   Worker 3's Low; the bullet omitted content its own entries record as *Moved*, so the file's
   index disagreed with the file.
6. `### ## Scalar field conversion` entry — *"The **rule** stays in the spec; only the 'originally /
   instead' chronology came here"* replaced with a statement that the reason-it-holds sentence stays
   in the spec **and** is deliberately restated here because the reader rule requires it. Reason:
   Worker 3's DRY finding measured the reason clause present verbatim in both files; the recorded
   *disposition* stands, but the framing sentence was false. No text moved.
7. `## Provenance of this record`, `**Restated in the spec, not moved**` bullet — the same false
   *"only the chronology came here"* clause appeared a second time in the file's index. Corrected
   in the same terms as 6. Reason: found while verifying 6 landed; a correction applied to an entry
   but not to the index that summarizes it leaves the file disagreeing with itself, which is the
   defect 5 also fixed.

### Notes for Worker 1 (spec reconciliation) — R2's input

R2's planning pass reads this block as its input. Items 1-3 are the corrected handoff; 4-6 are what
this pass deliberately left on R2's axis; 7-11 are drift, hand-overs, and state changes beyond the
plan's D1-D15.

1. **The anchor constraint, corrected — supersedes `### Notes for Worker 1` item 5 above.** All 21
   anchors have exactly one spec-body link each. Plan against the map in `### Finding 1`, and treat
   **`## Current state` (six anchors, and simultaneously D11/D14) as the highest-risk edit in R2's
   scope**: name the destination sentence for each of its six anchors before writing. Do not reword
   the `## Scalar field conversion` heading without also fixing the rationale's `[spec-001-scalars]`
   definition, because that heading is itself the anchor's link site and the slug the rationale
   cites.
2. **Re-run `check_spec_glossary.py` after every spec write, not once at the end**, and quote it in
   the R2 artifact. `import_spec_terms --check` is the downstream chain (card `DONE-001-0.0.1`);
   it now reads a **newly committed** DB, so re-establish its baseline at R2's start rather than
   inheriting the plan's `OK: 48 done cards`.
3. **Measure every count as you write it.** Four asserted counts in this cycle failed
   re-derivation: the two-anchor budget, "Two entries", "six repairs", and "well under 100 words"
   of shared text. Three were written beside the lesson they illustrated, which is exactly the
   failure `BUILD.md` names. Prefer a form the reader can re-derive.
4. **`## N+1 strategy` and `## get_queryset`'s O6 paragraph remain unresolved dispositions.** The
   spec's own (now moved) cut-line argument says the section, the `DjangoOptimizerExtension` public
   name, and the optimizer-shaped sentences in `## Goal` / `## get_queryset` belong in `spec-002`.
   The slice list now points Slices 4-6 there; the prose was never lifted. R2 decides: restate,
   point elsewhere, or drop. **`## N+1 strategy` carries the PR #583 carve-out** — *FK joins bypass
   per-type visibility filtering and leak rows* — which must survive any disposition, in this spec
   or in the one that takes the section.
5. **Left for R2, deliberately, with the reason on record**: the `Meta.interfaces` parking
   paragraph in `## DjangoType` (D5, whose twin left with `## Post-slice-7 future work`);
   `## Registry`'s illustrative code still declaring `lazy_ref` plus the prose sentence above it
   (D2 — the rationale records that the pending-relation approach actually won); and `## Current
   state`, `## What this enables immediately after implementation`, and the
   `examples/fakeshop/fakeshop/…` paths (D11, D14).
6. **Precedent worth stating once in R2's plan rather than re-deciding per row.** `worker-1.md`
   rule 2 ("delete, do not move, prose the current decisions have falsified") and `BUILD.md`'s
   reader rule ("any claim the decision once made and may no longer make") pull opposite ways on a
   falsified status claim. R1's shape: move it, quote it in the spec's own tense, and list it under
   *Claims the spec no longer makes*. Defensible because Worker 2 never reads the rationale, so no
   builder can implement it. R2 is entirely about prose HEAD falsifies, so it will meet this on
   nearly every row.
7. **Drift noticed beyond D1-D15.** Only one, and it is an extension of an existing row rather than
   a new one: the `tests/test_choice_enums.py` narration in `### Test surface` and in `### Tests`
   under `## Files to add` describes a fixture and a file that D10 says do not exist. I de-narrated
   both sentences without touching the file name, so the surface is intact for R2. `## Testing
   strategy`'s *"All new package tests go in a new root-level file"* is the same D10 surface a
   third time. Nothing else surfaced: the diff was read end to end and every other stale claim I
   saw is already a D-row.
8. **`## Files to add` is the largest un-rowed stale surface in the spec** and R2 should scope it
   deliberately rather than by drift row. It describes a flat module layout (`types.py`,
   `converters.py`, `optimizer.py`) that D1 falsifies wholesale, and it restates
   `registry.lazy_ref` (D2), the deferred-key list (D4), and the three test files (D10) — four rows
   converging in one section that no row names by heading.
9. **The concurrent session committed; re-baseline instead of inheriting.** Everything the plan
   lists under *"Grew during item R1"* and under `## Baseline-dirty out-of-scope files` is clean at
   `b29b851e`. For **R3** this materially changes its instructions: the plan's *"R3 may not verify
   its own DB/KANBAN work by `git diff` is clean"* was written against a dirty baseline that no
   longer exists, so R3 should re-measure `git status` at its own start and derive its verification
   strategy from what it finds — not assume clean, and not assume dirty. The concurrent session may
   open another cycle at any time.
10. **Handed to R3, not R2 (see `### Finding 4`):** `spec-002:9` and `spec-002:80` point into text
    that now lives only in the rationale. The fix is a pointer naming
    `appx/spec-001-django_types-0_0_1-rationale.md`, not new narration. `spec-002` is a spec file,
    so R3 must assign the edit to its **Worker 1** pass, not to its Worker 2.
11. **`overlap.py` as a `scripts/` helper** (Worker 3's item 6). Endorsed, and my own independent
    re-run is the second data point: the maximal-shingle scan is the only thing that converts "it
    was a move, not a copy" into a measurement, both prior runs of it produced a finding, and every
    future rationale extraction owes that proof. Maintainer's call; raised here so it reaches them,
    not carded.

### Final status

`final-accepted`.

Every High-tier concern was checked mechanically by Worker 3 and the load-bearing ones re-derived
independently here. The one Medium and three Lows were prose defects in the artifact and its
rationale rather than in the deliverable; all four are resolved — one by restatement with a
re-measured constraint, two by edits to files Worker 1 owns, one by an explicit hand-over to R3
with the reasoning and the operative wording. The residual slice narration is cleared. Both
constraint commands were re-run after every edit and hold their baselines, all 33 link definitions
resolve on disk, and all 21 anchors still carry exactly one spec-body link.
