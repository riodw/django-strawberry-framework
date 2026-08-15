# Build: R2 — spec reconciliation (spec-008)

Spec reference: `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` (whole file, 327 lines at
R2 entry)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** Not applicable in the source sense — this item writes Markdown only and
adds no Python. The equivalent inventory for a documentation item is the **cross-spec ownership
inventory**, and it was performed for me: `### Maintainer decision 2`'s `#### The 001-010 ownership
partition` is a ten-row mapping of every "thing" in the 001/008/009/010 cluster to exactly one owner,
produced by a dedicated analysis pass that read specs 001-008 in full. I re-verified the two rows the
rewrite turns on (item 4, hard invariants → spec-010; item 5, the `finalize_django_types()` contract
→ spec-010) against the sibling text before planning against them.

- **Existing patterns reused.** The rationale file's entry shape — `*Moved …*` / `*Claims the section
  no longer makes.*` keyed to a spec heading and anchor — is R1's and every R2 append reuses it
  rather than inventing a second shape. The demotion prose reuses one sentence form throughout ("X is
  `spec-NNN`'s", plus a reference-style link), so a reader can recognise a pointer on sight.
- **New helpers justified.** None. No new spec section is created except where a demotion needs a
  host heading; every demotion lands under the heading it replaces or is folded into a neighbour.
- **Duplication risk avoided.** The scope trap the plan names (`## The single-ownership law` and
  `**The scope trap specific to this spec**`) is *this* item's principal risk: the pull is to rewrite
  spec-008 as a description of how `finalize_django_types()` works today, which would be a third
  telling after spec-010 and `docs/GLOSSARY.md`. The plan prevents it by rule: spec-008 states **which
  option won and what constrained the choice**, and never a phase, a signature, an error string, or a
  call point. Every such fact is a reference-style link to `spec-010`.
- **A DRY call R1 handed me, resolved here.** `## Decision context to preserve` is, after R1's two
  condensations, the third telling of the same borrow/avoid conclusions already carried by the two
  `### Relevance to this package` subsections and by `## Why this matters for the goal`. It is retired
  rather than kept in sync; the reasoning is recorded in the rationale.

### Implementation steps

Line numbers are pin-at-write-time navigational hints against the 327-line post-R1 spec.

1. Re-verify every drift row D1-D16 against HEAD source, the kanban DB, and `docs/GLOSSARY.md` before
   any edit. Record per row: verified-as-stated, corrected, or falsified.
2. Rewrite `## Problem` / `## Current package behavior` (spec 5-68) out of the falsified present
   tense (D2) without turning the spec into a chronology: the problem is stated as the constraint the
   design faced, not as "what the package currently does".
3. Rewrite `## Why this matters for the goal` (22-49) so the feature list reads as the foundation
   requirement it was, with the two still-unshipped members marked as such (D16's sibling fact).
4. Retense the two `### Relevance to this package` subsections from "the parts to borrow / avoid"
   into what the package borrowed and avoided.
5. Rewrite `### Features that depend on this decision` (132-144) per D16 — six shipped, two Beta —
   preserving the `djangoconnectionfield` and `djangonodefield` anchors in place.
6. Rewrite `## Current strongest direction, not a final plan` (160-172) into the decision that was
   taken, including D3's reversal stated as the contract that holds. No "was later corrected" prose.
7. Demote the seven sections `#### What R2 demotes from claim to rationale-plus-pointer` names, each
   to a one- or two-sentence pointer at its new owner, with the demoted content appended to the
   rationale as a keyed entry.
8. Re-site the anchors the demotions displace, each in the same edit that removes its carrier.
9. Retire `## Decision context to preserve` (286-294) per the DRY call above.
10. Land the five authorized sibling edits: spec-001 Edit 1; spec-010 Edits 2 and 3; spec-010's two
    line-range citations (`### Maintainer decision 3`); spec-010's rerun-recovery amendment
    (`### Maintainer decision 5`).
11. Append every R2 entry to the rationale, keyed by spec heading and anchor.
12. Re-run the four verification commands and record every count with its unit and derivation.

### Test additions / updates

No tests. This item writes Markdown only and touches no package source, no test file, and no example
file. The verification instruments are `scripts/check_spec_glossary.py`,
`scripts/check_trailing_commas.py --check`, the rule-27 occurrence sweep, and the anchor / link
resolution sweep — all recorded under `### Checks re-run, with results quoted`.

### Implementation discretion items

- The exact wording of each demotion pointer, provided it names the owning document by
  reference-style link and asserts no concrete contract of its own.
- Whether a demoted section's heading survives as the host of its pointer or the pointer folds into
  the preceding section. Assessed: both are equally valid; a surviving heading is preferred where an
  in-page anchor or a sibling's inbound reference targets it.

### Dispatched findings checklist

- [x] D1 — the document's tense: `## Current strongest direction, not a final plan`, "should not be
      treated as a finalized implementation plan yet", `### Proposed shape to evaluate`, and the
      question-section residue all presented a settled decision as open.
- [x] D2 — `## Problem` / `## Current package behavior` present tense, and the dead symbol
      `convert_relation` (0 occurrences in `django_strawberry_framework/`).
- [x] D3 — the hybrid auto-finalization leading direction was rejected; the explicit
      `finalize_django_types()` call is the sole trigger and is not an escape hatch.
- [x] D4 — `DjangoSchema` shipped at `0.0.14` for an unrelated contract and does not finalize.
- [x] D5 — the five registry questions are settled (`Meta.primary` at `0.0.6`; ambiguity is a
      `ConfigurationError`; pending records stored separately; reset is `TypeRegistry.clear()`).
- [x] D6 — the user-annotation questions are settled; cardinality validation is an explicit published
      deferral.
- [x] D7 — generic fallback answered by omission; `DjangoModelType` has 0 occurrences.
- [x] D8 — rich-schema `Meta` keys landed per subsystem, not all five up front.
- [x] D9 — the acceptance bullet "root `DjangoConnectionField` can finalize reachable model types" is
      unmeetable by design.
- [x] D10 — the other twelve acceptance bullets are met (preserve, do not churn).
- [x] D11 — every hard invariant holds at HEAD (preserve the fact; `### Maintainer decision 2` item 4
      moves the *section*).
- [x] D12 — raw `path:NN` citations: rule-27 compliance must hold at 0 occurrences in both files.
- [x] D13 — the Graphene `Dynamic` con was priced as a blocker and was not one (preserve).
- [x] D14 — two of the eight `## Fakeshop implication` rows are falsified by `relation_shapes`; six
      hold; the closing "cannot be represented today" sentence is falsified.
- [x] D15 — six of the nine cookbook members shipped; three are unshipped Beta work.
- [x] D16 — six of the eight dependent features shipped; aggregates and fieldsets remain Beta.
- [x] Partition demotions ×7 — `### Hard invariants`, `### Proposed shape to evaluate`, the
      finalization-trigger and question-section residue, `## Acceptance criteria` / `### Failure
      criteria`, `## Fakeshop implication`, `## Cookbook implication`.
- [x] Sibling Edit 1 — `spec-001` #"owns that pass" → spec-010.
- [x] Sibling Edit 2 — `spec-010` #"helpers wrap it in later releases".
- [x] Sibling Edit 3 — `spec-010` #"Auto-trigger via".
- [x] `### Maintainer decision 3` — spec-010's two line-range citations → heading-anchored.
- [x] `### Maintainer decision 5` — spec-010's rerun-recovery contract amended to match source, with
      the Phase 2.5 / ambiguity-audit insertion points acknowledged and not claimed.
- [x] All ten glossary anchors survive; `check_spec_glossary` stays `OK: 10 terms`.

---

## Build report (Worker 1 — perform pass)

`### Deviation 2` of the build plan removes Worker 2 from R2 entirely: `BUILD.md` `## Spec
reconciliation` and `worker-1.md` `## Scope` make Worker 1 the only role that may mutate a spec, and
R2's whole deliverable is spec edits. So the plan and the perform record are one pass and the
artifact returns at `Status: planned`, which Worker 0 reads as "dispatch Worker 3".

### Files touched

- `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` — the reconciliation. 40 hunk groups.
- `docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md` — thirteen appended
  entries plus four link-definition maintenance edits and one re-pointed "Bears on" line.
- `docs/SPECS/spec-001-django_types-0_0_1.md` — partition Edit 1. **1 hunk.**
- `docs/SPECS/spec-010-foundation-0_0_4.md` — partition Edits 2 and 3, decision 3's two citations,
  decision 5's rerun-recovery amendment and phase-insertion acknowledgement. **10 hunks.**

Nothing else. `git status --short django_strawberry_framework/types/` is empty: `types/relations.py`
and `types/base.py` are absent from this diff, as R2b's dispatch requires.

### Drift-row disposition — every row re-verified against HEAD before it was acted on

Worker 0's table was re-derived rather than trusted, as the dispatch required and as its own four
appended corrections justify. Verification commands are quoted per row; every count states its unit.

| Row | Re-verification | Disposition in the spec |
|---|---|---|
| D1 | Confirmed. `Card.objects.get(number=8)` is `DONE-008-0.0.4`; the shipped answer is `types/relations.py::PendingRelation`, `registry.py::TypeRegistry.add_pending_relation`, `types/finalizer.py::finalize_django_types` | `## Current strongest direction, not a final plan` → `## The decision`; the "not a finalized implementation plan" disclaimer and every "should" in the target-behavior list retensed to indicative |
| D2 | Confirmed. `grep -rn 'convert_relation' django_strawberry_framework/ \| wc -l` → **0** (unit: matching lines; the symbol is one token so lines = occurrences). `types/converters.py:714:def resolved_relation_annotation` is the live path | `## Problem` restated as the constraint the design faced; `## Current package behavior` → `## Package behavior before this decision`; the dead symbol removed and the step described functionally |
| D3 | Confirmed, and **strengthened**: a text grep can be fooled by docstrings, so the call sites were re-derived by AST — `ast.walk` over every `django_strawberry_framework/**/*.py` collecting `ast.Call` whose `func` resolves to `finalize_django_types` → **`[]`** (unit: call nodes). `schema.py::DjangoSchema` read end to end; no finalize | `### The finalization trigger` states the explicit call as the sole trigger and the implicit alternative as not adopted. The "escape hatch" framing is gone in the finalization sense. Enumerating the three non-finalizing symbols is spec-010's (Edit 3), not restated here |
| D4 | Confirmed. `schema.py:204:class DjangoSchema(strawberry.Schema)` — installs `DjangoMutationExecutionContext`, resolves the production `ErrorPolicy` and `ResourcePolicy` at construction. No finalize | The speculative naming is removed from the spec with the trigger claim. The hazard — a speculative name later taken by a real feature — is recorded in the rationale, where it is a lesson rather than a contract |
| D5 | Confirmed, all five. `registry.py:508 add_pending_relation`, `:513 iter_pending_relations`, `:526 discard_pending`, `:580 clear`, `:68 register_subsystem_clear`; `finalizer.py:109 _format_ambiguity_error`, `:131 _audit_primary_ambiguity` | Already moved to the rationale by R1; R2 adds the `Meta.primary` pointer at `spec-018` inside `### The finalization trigger`, which also re-sites that anchor |
| D6 | Confirmed **as corrected by R1**, not as originally written. The cardinality answer is in the glossary verbatim: `docs/GLOSSARY.md:514` "Validation that a manual relation annotation matches the Django relation cardinality is deferred", restated at `:795`. No source read was needed | No spec change; the rationale entry R1 wrote already records it as the one settled question still answered "deferred" |
| D7 | Confirmed. `grep -rc 'DjangoModelType' -r django_strawberry_framework/` returns no non-zero file (unit: files with ≥1 matching line) | No spec change; already in the rationale |
| D8 | Confirmed. `types/definition.py:161-163` declares `filterset_class`, `orderset_class`, `fields_class`; `types/base.py:65-67` `DEFERRED_META_KEYS` is exactly `{"aggregate_class", "fields_class", "search_fields"}`. Two bound, one reserved, two with no slot | No spec change; already in the rationale |
| D9 | Confirmed, and it is the same reversal as D3. The bullet names a mechanism the implementation rejected | The bullet is retired with the rest of `## Acceptance criteria`; the rationale records **why** it is superseded rather than unmet, which is the distinction a reader auditing the package against the list would otherwise get wrong |
| D10 | Confirmed — the row is the spec being right. `finalizer.py:86 _format_unresolved_targets_error`; zero `import graphene` / `from graphene` occurrences | **Not churned.** The twelve met criteria are not re-worded; the section is demoted to a pointer at spec-010's checkable inventory, per the ownership partition, and the twelve are restated in the rationale so nothing is lost |
| D11 | Confirmed — every invariant holds. **The partition (`### Maintainer decision 2` item 4) explicitly reverses D11's disposition** while leaving its fact untouched, and says so in those words | The eight-bullet list moves to the rationale and the heading survives as a pointer at spec-010's "Invariants this slice must protect", which carries the same constraints with tests behind them. `### Failure criteria` is retired: seven of its seven entries are the negation of an invariant, so it was a duplicate *inside* the spec first |
| D12 | Confirmed compliant, and re-measured rather than assumed. Rule-27 occurrence sweep on both files → **0 and 0** (unit: regex occurrences via `grep -oE '[A-Za-z0-9_./-]+\.(py\|md):[0-9]+' <file> \| wc -l`, not matching lines — the unit that produced Worker 0's original 28-versus-31 error) | Nothing to convert; R1 discharged it. R2 introduced no new raw citation, verified by the same sweep after every edit |
| D13 | Confirmed — the row is the spec being right | **Not churned.** The Graphene `### Cons` already sit in the rationale; the "parts to avoid" list still rules out porting `Dynamic`, now stated as what the package avoided rather than what it should |
| D14 | Confirmed **as corrected by R1**, and independently re-read: `examples/fakeshop/apps/products/schema.py` — `CategoryType.Meta.relation_shapes = {"items": "both"}` with `properties` deliberately left on the `0.0.14` `"connection"` default; `ItemType.Meta.relation_shapes = {"entries": "both"}`; `PropertyType.Meta` carries **no** `relation_shapes` key. So **2 of 8 rows falsified** (`Category.properties`, `Property.entries`), **6 hold** (two explicit `"both"` opt-ins plus the four forward-FK rows) | The eight-row table is demoted; the spec keeps the fixture's role and points at `spec-032` for the wire shape, which is the artifact that moved twice in two releases |
| D15 | Confirmed. Shipped: `"__all__"`, `relay.Node` interfaces, `filterset_class` / `orderset_class`, `get_queryset`, `apply_cascade_permissions` (`permissions.py:549`). Unshipped: no `aggregates`, `fieldsets`, or `fields.py` module exists under `django_strawberry_framework/` | `## Cookbook implication` becomes a pointer at `spec-009`, which owns the target outcome and is the document that must re-score it as the three Beta cards ship |
| D16 | Confirmed. `DjangoConnectionField` (`connection.py:2113`), `DjangoNodeField` (`relay.py`), `filters/`, `orders/`, cascade permissions, optimizer relation-kind dispatch all present; no aggregates or fieldsets module | The eight-bullet list is **kept intact** — it is spec-008's own material and the sole carrier of two anchors — with the shipped / Beta split stated in one closing sentence rather than per bullet |

Two rows the table warned against churning, D10 and D13, were not churned. D11 was moved, and that is
not a churn of a correct section but the partition's explicit instruction, taken with its stated
reversal of the row.

### The seven demotions

Each is a claim retired from the spec, its content appended to the rationale, and a pointer left in
the spec naming the owner by reference-style link.

| Demoted | New owner | Spec residue |
|---|---|---|
| `### Hard invariants` | spec-010 `#invariants-this-slice-must-protect` | heading kept, one pointer paragraph |
| `### Failure criteria` | — (retired; negation of the above) | none; folded into the invariants pointer |
| `### Proposed shape to evaluate` | spec-010 `#finalization-phase-finalize_django_types` + spec-001 | renamed `### The shape that shipped`, one paragraph |
| the finalization-trigger and question-section residue | spec-010, and spec-018 for the primary question | `### The finalization trigger`, three paragraphs |
| `## Acceptance criteria` | spec-010 `#test-fixtures-and-acceptance-criteria` | heading kept, two paragraphs |
| `## Fakeshop implication` | spec-010 (fixture) + spec-032 (wire shape) | heading kept, two paragraphs |
| `## Cookbook implication` | spec-009 | heading kept, two paragraphs |

Plus one **retirement** that is not a demotion: `## Decision context to preserve` was, after R1's two
prior-art condensations, the third telling inside one file of conclusions already carried by both
`### Relevance to this package` subsections and by `## Why this matters for the goal`. Every bullet is
a conclusion, so the ordinary deliberation test does not reach it — R1 flagged it as R2's DRY call and
left it. It is recorded verbatim in the rationale and removed from the spec.

### The five sibling-spec edits

All five landed; no sixth site in any sibling was touched.

1. **`spec-001` #"owns that pass"** — `spec-008-…md owns that pass` → `spec-010-foundation-0_0_4.md
   owns that pass`. Bare-filename reference, so no link-definition block changed.
   `check_spec_glossary --spec spec-001` still `OK: 21 terms`.
2. **`spec-010` #"helpers wrap it in later releases"** — replaced with the contract that holds: no
   shipped helper wraps the entry point.
3. **`spec-010` #"Auto-trigger via"** — replaced with the negative fact naming all three symbols, and
   the never-adopted direction cited as recorded rather than recommended. **The sentence's second
   half was deliberately kept**: the single-threaded-window obligation binds any *future* helper and
   is a live constraint, not a claim about shipped code.
4. **`spec-010`'s two line-range citations into spec-008** — `(400-414)` and `(397-505)` converted to
   the `#"<heading>"` substring form `AGENTS.md` rule 27 prescribes, pointing at
   `### The finalization trigger` and `### The shape that shipped`. Both ranges resolved into text
   this pass rewrote, and a stale range is worse than a broken link because it resolves silently.
5. **`spec-010`'s rerun-recovery contract** (`### Maintainer decision 5`) — spec-010 asserted the
   opposite of the code it owns. `types/finalizer.py`'s module docstring (lines 37-46) states a raise
   in Phase 2 / 2.5 / 3 leaves the finalized flag False and "supports a fine-grained partial recovery
   on rerun" through per-entry `if definition.finalized: continue` guards, with `registry.clear()`
   demoted to "the recommended escape hatch only when the offending type cannot be fixed in place".
   **Shipped tests pin the relaxed behavior**, so this is not a docstring-versus-code disagreement
   requiring escalation: `tests/mutations/test_sets.py:705` re-finalizes **without**
   `registry.clear()` after fixing the cause and asserts the rerun is clean, and
   `tests/test_relay_connection.py:550`/`:585` and `tests/types/test_relay_interfaces.py:1903` pin the
   same rerun path. The amendment states what the guards do and nothing more, per the decision's
   stated boundary. It also retires spec-010's reference to
   `test_phase3_strawberry_failure_requires_full_restart`, which has **0** occurrences tree-wide
   (unit: matching lines under `tests/` and `examples/`).

   *In the same edit, the phase-count acknowledgement.* Spec-010 documented three phases; the shipped
   pass runs four (`types/finalizer.py`'s docstring: "It runs four phases"), with Phase 2.5 inserted
   and a primary-ambiguity audit at the top of Phase 1. Spec-010 now **acknowledges** both insertion
   points without **claiming** them — their contents belong to spec-015 / 018 / 027 / 031 / 032 per
   the partition's item 5. The seven-step public phase order stays `docs/GLOSSARY.md`'s, restated in
   neither spec.

**`spec-009` was not touched.** `### Maintainer decision 6` defers its Layer 3 auto-trigger prose to
its own cycle. Deferring it does not license spec-008 to keep pointing at it as live guidance, so
`## The decision` states the direction was not adopted; the rationale names spec-009 as where the
inversion is still recorded. Handed to R3's deferred-work catalog.

### Anchor re-sites — four, each in the edit that removed its carrier

`### The 10-anchor surface` is binding and `check_spec_glossary` is the gate. No terms CSV was
touched; no section was left hollow to host a link.

| Anchor | Carrier at R2 entry | New carrier | How |
|---|---|---|---|
| `metafields` | `## Acceptance criteria` bullet (demoted) | `## Prior art: Strawberry-Django` `### Relevance to this package` closing sentence | **link-form change on surviving prose** — the sentence already said `Meta.fields = "__all__"` in HEAD's own words |
| `finalize_django_types` | the R1 rationale-pointer line (rewritten) | `### The finalization trigger`, opening sentence | R1's host had to stay trigger-neutral while the question read as open. It no longer is: the answer is stated, so the anchor sits on the answer — which is what R1's handoff asked for ("must still describe the trigger as *weighed*, never as *chosen*" applied while the outcome was unstated) |
| `metaprimary` | `## Acceptance criteria` bullet (demoted) | `### The finalization trigger`, the spec-018 pointer sentence | naming the key is the point of the pointer, so no narration was added to host it |
| `schema audit` | `## Acceptance criteria` bullet (demoted) | the `## Acceptance criteria` pointer sentence | the pointer names what the inventory covers; the anchor rides an existing enumeration rather than a new one |

The six anchors that did not move: `definition-order-independence` (H1), `djangotype` and
`configurationerror` (`## Problem`), `relay-node-integration` (`## Why this matters for the goal`),
`djangoconnectionfield` and `djangonodefield` (`### Features that depend on this decision`, kept
intact partly for that reason).

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-definition_order_independence-0_0_4.md`
  → `OK: 10 terms - all have glossary entries and at least one spec link.` exit 0.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md`
  → `OK: 21 terms - all have glossary entries and at least one spec link.` exit 0.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-010-foundation-0_0_4.md`
  → `OK: 12 terms - all have glossary entries and at least one spec link.` exit 0.
- `uv run python scripts/check_trailing_commas.py --check` over all five `.md` files this pass wrote
  (spec-008, its rationale, this artifact, spec-001, spec-010) → exit 0.
- `git status --short` over the writable set → exactly the five expected entries (`M` spec-001,
  `M` spec-008, `M` spec-010, `??` rationale, `??` this artifact) and nothing else.
- No `pytest` run; none needed (`BUILD.md` `## Coverage is the maintainer's gate`). No `--cov*` flag
  anywhere. No `git stash` / `checkout` / `restore` / `worktree`. No branch. No commit.

### Failability proofs

None; this pass introduced no new boundary. It writes Markdown only and adds no executable line.

### Hot-path budget

Not applicable; plan declares no hot path (`## Hot-path declaration`: the only source-touching item
in this cycle is R2b, and it is comment-only).

### Floor verification

Not applicable; plan declares floor-verification scope `none`.

### Implementation notes

- **Why `## The decision` states the trigger outcome but not the three non-finalizing symbols.** The
  negative claim ("`DjangoSchema` / `DjangoConnectionField` / `DjangoNodeField` do not call the
  finalizer") is a property of the pass, so under the partition it is spec-010's, and this pass wrote
  it there. Stating it in both would have been the exact duplication the cycle exists to remove.
  Spec-008 states the *decision* — which trigger won over which alternative — because that is this
  record's own deliverable and nobody else's.
- **Why the demotion pointers name what the target covers rather than pointing bare.** A bare "see
  spec-010" is unusable: a reader cannot tell whether the thing they are looking for is there. Each
  pointer names the topics the target owns without restating any contract, which is also what let the
  `schema audit` anchor ride an existing enumeration instead of a manufactured sentence.
- **Why `### Failure criteria` was retired rather than demoted.** All seven entries are the negation
  of an invariant in the section above it. It duplicated inside the spec before it duplicated across
  the cluster, so a pointer would have preserved a redundancy rather than relocating a claim.
- **Why `## Problem` keeps the four-step pipeline.** The steps are the problem statement, which
  partition item 1 gives spec-008 outright; only the present-tense framing and the dead symbol were
  falsified. Deleting the steps would have left the problem asserted without its mechanism.
- **`Option 1: Keep eager resolution` said "Keep the current behavior".** Retensed to "Keep the eager
  pipeline unchanged" — the same D2 falsification, in the one place a sweep for "currently" misses.

### Notes for Worker 3

- **The R1 baseline was reconstructed mechanically, not eyeballed, and it is proved.** R2's hunk
  ranges below are diffed against `<scratchpad>/R1-baseline.md`, produced by reverse-applying every
  R2 edit's exact replacement string to the current file. The reconstruction is proved by its counts
  matching R1's three independently derived measurements exactly: **19,612 bytes / 327 lines**. A
  `git diff` against `HEAD` would have shown R1+R2 combined, which is why it is not the instrument
  here. `git diff --no-index -U0` was used; no `git checkout` / `stash` / `restore` / `worktree`.
- Every count in this artifact carries its unit and its derivation command. The unit trap has fired
  seven times in this cycle; the two that most invite it here are the rule-27 sweep (occurrences, not
  lines) and the fence count (delimiter lines, not blocks).
- The rationale's `### Entries added by the spec-reconciliation pass` block is appended below R1's
  entries and never edits them. Four link-definition maintenance edits and one re-pointed "Bears on"
  line inside R1's block were unavoidable: two spec headings R1's defs targeted no longer exist
  (`#current-strongest-direction-not-a-final-plan`, `#proposed-shape-to-evaluate`), so leaving them
  would have been the dangling-anchor defect the same rule forbids.

### Notes for Worker 1 (spec reconciliation)

Nothing outstanding for a later custodian pass. Items handed onward are in `### Handed to R3` under
the final-verification section.

---

## Spec changes made (Worker 1 only)

Ranges are the **left (baseline) side** of `git diff -U0`, never eyeballed section bounds — the
failure R1's own final audit found in its first list. **The hunk count is the audit**, and it is
quoted verbatim from the tool below rather than paraphrased: **40** hunk groups in spec-008 (unit:
`@@` lines from `git diff --no-index -U0 | grep -c '^@@'`), **1** in spec-001, **10** in spec-010 —
**51** in total. The prose that follows the machine list *groups* those hunks by reason, so its
bullet count is deliberately smaller and is not a second count of the same thing. Baseline for spec-008 is
the reconstructed R1 output (`### Notes for Worker 3` proves it); baseline for the two siblings is
`HEAD`, which is correct for them because neither was dirty at R2 entry.

### `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` — 40 hunks, R1-baseline lines

```
-6 -> +6
-8 -> +8
-11,2 -> +11,2
-15 -> +15
-27 -> +27
-41 -> +41
-43 -> +43
-51,2 -> +51,2
-58 -> +58
-64 -> +64
-66 -> +66
-68 -> +68
-82 -> +82
-87 -> +87
-89 -> +89
-96 -> +96
-108 -> +108
-110 -> +110
-119 -> +119
-125 -> +125
-130 -> +130
-133 -> +133
-144 -> +144
-147 -> +147
-160,2 -> +160,2
-163 -> +163
-165 -> +165,6
-167,6 -> +172,2
-174,43 -> +175
-218,34 -> +177
-253,2 -> +179,2
-256,8 -> +182,2
-265 -> +185,2
-267,14 -> +188
-282 -> +190,2
-284 -> +193
-286,2 -> +195,2
-289,6 -> +198
-312,0 -> +217
-313,0 -> +219,7
```

Reason and trigger per hunk group, in file order (baseline lines cited above):

- **6, 8, 11-12, 15** — `## Problem`: present-tense claim about package behavior removed; dead symbol
  `convert_relation` removed; closing sentence retensed. Reason: D2. Trigger: the drift table.
- **27, 41, 43, 51-52** — `## Why this matters for the goal`: "intended end state" → the end state
  this foundation has to support; the eager-resolution consequence stated as a property rather than a
  future risk; "The real question is" → "It is five questions at once". Reason: D1 tense.
- **58, 64, 66, 68** — `## Current package behavior` → `## Package behavior before this decision`,
  and its three following paragraphs retensed. Reason: D2.
- **82, 87, 89, 96** — `## Prior art: Graphene-Django` `### Relevance to this package`: borrow / avoid
  lists stated as what the package did. Reason: D1 tense; the lists themselves are unchanged.
- **108, 110, 119, 125** — the Strawberry equivalent, plus the closing sentence which now carries the
  **`metafields` anchor re-site**. Reason: D1 tense + `### The 10-anchor surface`.
- **130** — `## Design options for this package`: the rationale pointer's trailing "with the
  deliberative framing this section originally carried" removed. Reason: the spec does not narrate
  its own history, and the clause is exactly that.
- **133** — `### Option 1`: "Keep the current behavior" → "Keep the eager pipeline unchanged".
  Reason: D2, in the one place a `currently` sweep misses.
- **144, 147** — `### Features that depend on this decision`: opening retensed, closing sentence
  states the six-shipped / two-Beta split. Reason: D16. The eight bullets are untouched.
- **160-165** — `## Current strongest direction, not a final plan` → `## The decision`; the "not a
  finalized implementation plan" disclaimer removed; the six target-behavior bullets retensed.
  Reason: D1 + D3. Trigger: the drift table and `### Maintainer decision 2`.
- **167-172, 174-216** — `### The finalization trigger` replaces the trigger residue and the
  `### Hard invariants` / `### Proposed shape to evaluate` bodies with pointers. **This hunk group
  carries three of the four anchor re-sites** (`finalize_django_types`, `metaprimary`, and the host
  for the invariants pointer). Reason: D3 + `#### What R2 demotes from claim to
  rationale-plus-pointer`.
- **218-251** — `## Acceptance criteria` and `### Failure criteria` demoted; the **`schema audit`
  anchor** re-sited onto the pointer sentence. Reason: D9, D10, and the partition's item 9.
- **253-265** — `## Fakeshop implication` demoted. Reason: D14 as corrected by R1 (two of eight rows
  falsified, six hold) plus partition item 10.
- **267-284** — `## Cookbook implication` demoted to a spec-009 pointer. Reason: D15 + partition
  item 10.
- **286-294** — `## Decision context to preserve` retired. Reason: the DRY call R1 handed R2; the
  section is the third telling inside one file.
- **312 (insertion), 313-319 (insertion)** — five reference-style link definitions added to the
  `<!-- docs/SPECS/ -->` group, alphabetical within it: `spec-001`, `spec-009`, `spec-010`,
  `spec-010-acceptance`, `spec-010-finalization`, `spec-010-invariants`, `spec-018`, `spec-032`.
  Reason: `START.md` link convention; every demotion pointer needs one. All eight disk-verified, and
  the three anchored ones verified against the target's actual headings.

### `docs/SPECS/spec-001-django_types-0_0_1.md` — 1 hunk, HEAD lines

- **HEAD line 66** — partition Edit 1: `spec-008-…md owns that pass` →
  `spec-010-foundation-0_0_4.md owns that pass`. Reason: spec-008 declines in its own text to own any
  contract; spec-010 pins the pass. Trigger: `#### Sibling-sentence edits authorized by this
  decision`, Edit 1.

### `docs/SPECS/spec-010-foundation-0_0_4.md` — 10 hunks, HEAD lines

- **HEAD 21** — Edit 2, `#"helpers wrap it in later releases"`.
- **HEAD 48** — decision 3, the `(400-414)` citation → `#"### The finalization trigger"`.
- **HEAD 65** — Edit 3, `#"Auto-trigger via"`. Second half kept (future-helper obligation).
- **HEAD 310 (insertion of 2 lines)** — decision 5's phase-insertion acknowledgement under
  `### Finalization phase: finalize_django_types()`.
- **HEAD 322, 325, 332-339** — decision 5, the pseudocode docstring's rerun-recovery contract.
- **HEAD 393-396** — decision 5, the `# Phase 3` comment's "requires registry.clear() + fresh class
  recreation" claim.
- **HEAD 405** — decision 3, the `(397-505)` citation → `#"### The shape that shipped"`. The
  `spec-009-…md (1076-1077)` citation in the same sentence is **untouched**: decision 3 authorizes
  exactly the two spec-008 citations, and spec-009 is deferred.
- **HEAD 470** — decision 5, the `## Idempotency and lifecycle contract` bullet, split into a
  bounded-atomicity bullet and a supported-rerun bullet.

No other line in either sibling was touched, and `spec-009` was not opened.

## Checks re-run, with results quoted

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-definition_order_independence-0_0_4.md
OK: 10 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
OK: 21 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-010-foundation-0_0_4.md
OK: 12 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-008-definition_order_independence-0_0_4.md \
    docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md \
    docs/builder/bld-008-r2-spec_reconciliation.md \
    docs/SPECS/spec-001-django_types-0_0_1.md \
    docs/SPECS/spec-010-foundation-0_0_4.md
exit=0
```

### Rule-27 occurrence sweep — 0 and 0

**Unit: regex occurrences, not matching lines.** This is the exact unit that produced the cycle's
28-versus-31 error, so the command counts with `grep -o`:

```
$ grep -oE '[A-Za-z0-9_./-]+\.(py|md):[0-9]+' docs/SPECS/spec-008-definition_order_independence-0_0_4.md | wc -l
0
$ grep -oE '[A-Za-z0-9_./-]+\.(py|md):[0-9]+' docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md | wc -l
0
```

R1 established compliance; R2 introduced no new raw citation. The `#"<substring>"` form used for the
two spec-010 citations is rule 27's prescribed replacement, not a raw `path:NN`, and is invisible to
the sweep because it carries no `:NN`.

### Counts, with units and derivation commands

| File | Bytes (`wc -c`) | Lines (`wc -l`) | Fenced blocks |
|---|---|---|---|
| spec-008, R1 baseline | 19,612 | 327 | 0 |
| spec-008, after R2 | **17,098** | **239** | **0** |
| rationale, R1 baseline | 42,265 | 630 | 2 |
| rationale, after R2 | **67,883** | **997** | **2** |

**Fenced blocks are derived, not counted directly**: `grep -c '^```'` reports fence **delimiter
lines** and a block is two of them. Spec-008 → `0` delimiter lines → **0 blocks**. Rationale → `4`
delimiter lines → **2 blocks**, unchanged from R1 (R2 appended no fence). Every other number above is
a direct `wc` reading, whose unit is stated in the header.

The spec lost 2,514 bytes / 88 lines while the rationale gained 25,618 / 367. The asymmetry is the
same one R1 recorded and for the same reason: the **record** of a demoted claim — the claim verbatim,
its verified fate, and what it may no longer say — is larger than the claim.

### Anchors and link definitions, verified rather than assumed

- **In-page anchors:** `grep -on '](#[a-z0-9-]*)'` → **0 occurrences** in both files (unit: matches).
  Neither file uses in-page anchors, so no heading rename could dangle one. Both were checked after
  the rewrite, not before.
- **Cross-file anchored link definitions:** every `[id]: path#anchor` def in both files was resolved
  by slugifying the target file's real headings and testing membership. **19 anchored defs, 19 OK, 0
  BAD** (GLOSSARY targets excluded — `check_spec_glossary` is their gate). This caught the two R1 defs
  that the rewrite would otherwise have left dangling
  (`#current-strongest-direction-not-a-final-plan`, `#proposed-shape-to-evaluate`).
- **Every link-definition path disk-verified:** 47 defs across both files, **0 missing** (unit: def
  lines). The `appx/` depth trap was checked specifically — no def in either file targets a
  `README.md`, so the "same-named file one level up masks depth rot" hazard has no surface here.
- **Ref-id integrity:** used-but-undefined = **0**, defined-but-unused = **0**, in both files (unit:
  distinct ref-ids, via `comm` over sorted `grep -oE` extractions).
- **The 10 canonical group headers:** `grep -cE` for the exact closed list → **10** in spec-008 and
  **10** in the rationale, in order, empty groups retained.

## Handed to R3

- **`spec-009`'s `### Layer 3: Finalization trigger`** — "Preferred triggers:" over four
  never-shipped items, the D3 falsification one document further out. Deferred by
  `### Maintainer decision 6`; belongs in R3's `### Deferred work catalog` with the reason (spec-009
  is a large architecture spec owed its own cycle) and the note that spec-008 and spec-010 no longer
  point at it as live guidance.
- **`django_strawberry_framework/testing/relay.py:73`** — the consumer-visible message "call
  `finalize_django_types()` (or build the schema) first". R1 escalated this and R2 confirms it reads
  as though building the schema is an alternative trigger, which D3 says it is not. **Source, so
  outside every writable set in this cycle including R2b's two-comment carve-out.** Escalate to the
  maintainer through R3's catalog; do not fold it into R2b.
- **`docs/SPECS/spec-010-foundation-0_0_4.md:513`** — "phase 2/3 partial-mutation limits … covered as
  explicit contracts" was read and **left**: partial mutation is still real, only the *recovery* claim
  was stale. Recorded so R3 does not re-flag it.
- **Card 8's two incomplete `Verified in upstream` `CardItem`s** — Worker 0's pre-flight recorded them
  as a maintainer observation, not a fix. R2 touched no DB row; R3 owns the verification.
- **The kanban board item at `KANBAN.md:248`** now has one fewer target: it lists `spec-008` among the
  specs still naming `convert_relation`, and spec-008 no longer does (`spec-009`, `spec-010`, and
  `spec-019` still do). Generated from the DB, so **not hand-editable** — R3 records it for the
  maintainer rather than regenerating.

## Status

> Not the artifact's status. The canonical `Status:` line is the header block above (line 5), and it
> is the only line Worker 0 reads to drive dispatch (`ARTIFACT.md:3`). This block records one pass's
> transition at the moment that pass wrote it.

`Status: planned` — set deliberately, per the build plan's `### Deviation 2`. R1 and R2 skip `built`
because no Worker 2 role exists for them, and Worker 0 reads `planned` on this artifact as "dispatch
Worker 3 for the audit".

---

## Review (Worker 3)

### Verdict on the reconstruction methodology — ACCEPTED, and independently corroborated

R2's R1 baseline could not be re-derived by re-running its procedure (the replacement strings live only
in R2's own edit history), so the claim was tested a different way: **the hunk list is arithmetically
self-proving against the file on disk.**

- Summing `new_count - old_count` across all 40 recorded hunk groups gives **-88 lines**. `327 - 88 =
  239`, and `wc -l` on the current spec is **239**. An exact match.
- Every right-side start offset in the list reconciles with the running delta of the hunks above it
  (checked all 40; the two `-N,0 -> +M` insertions follow git's convention correctly), and the
  unchanged tail reconciles: baseline 314-327 = 14 lines maps to right 226-239 = 14 lines.
- R1 recorded **19,612 bytes / 327 lines** independently in `bld-008-r1-rationale_move.md` (its
  corrected figure, superseding a pass-1 `19,578`). The 327 matches what the arithmetic forces.

A reconstruction that yields a hunk list which is internally consistent AND terminates at the observed
239 lines is a valid baseline for auditing the hunk ranges. **The byte figure (19,612) is the one
number here I cannot independently re-derive** — it rests on R1's own record — but no range in the
artifact depends on it. The hunk list is auditable; I relied on it.

### High:

None.

### Medium:

#### M1 — `## Fakeshop implication` points the reader at the wrong owner for the `0.0.14` default

`docs/SPECS/spec-008-definition_order_independence-0_0_4.md:193`:

> `Meta.relation_shapes` made it declarable per field at `0.0.9` and the default moved to
> `"connection"` at `0.0.14`, so [`spec-032-full_relay-0_0_9.md`][spec-032] owns it.

Both facts are true (`types/base.py #"DEFAULT_RELATION_SHAPE = "connection""` confirms the default),
but **the ownership attribution is wrong for the second one**, and it is wrong in the way that hurts
most: a reader who follows the pointer lands on prose asserting the *opposite*.
`docs/SPECS/spec-032-full_relay-0_0_9.md #"the \`\"both\"\` default keeps the \`list[T]\` field"`
documents `"both"` as the implicit default — that is spec-032's shipped contract at `0.0.9`.
`docs/GLOSSARY.md #"Many-side default (\`0.0.14\`, spec-047)"` names the owner explicitly:
**`spec-047-resource_policy-0_0_14.md`**, where the many-side default was narrowed as part of the
bounded-output work.

This is the same defect class as `### Maintainer decision 4`'s two `spec-014` misattributions — a
provenance pointer sending the reader to a document that does not own the claim — introduced here
rather than inherited. It also weakens the demotion itself: the sentence's job is to hand the wire
shape to its owner, and it hands half of it to the wrong one.

**Recommended change.** Attribute per fact: `Meta.relation_shapes` (per-field declarability, `0.0.9`)
to `spec-032`; the `0.0.14` many-side default to `spec-047`. Or state only the key and its owner and
drop the default-move clause from the spec entirely (the rationale already carries it — see L3).
Whichever is chosen, add the `spec-047` link definition to the `<!-- docs/SPECS/ -->` group in
alphabetical position and disk-verify it.

#### M2 — the unresolved-target error requirement is now stated in three places, and spec-010 cites spec-008 as its source

`#### The 001-010 ownership partition` item 7 is explicit: *"The **unresolved-target
`ConfigurationError`** → **spec-010** … Spec-008's fail-loud requirement becomes rationale."* The diff
does the opposite in one spot:

- `spec-008 …:183` (`### The shape that shipped`) states "**a fail-loud raise naming the source model,
  source field, and related model** — shipped whole."
- `spec-010 …` `### Unresolved-target error format`, as **rewritten by this pass**, now reads "It must
  name the source model, source field, and target model, **exactly as required by**
  `spec-008-…md` #"### The shape that shipped"" — i.e. spec-010 sources the requirement *from*
  spec-008.
- The rationale carries it a third time, verbatim, in the moved pre-schema-construction step 7.

So after a pass whose purpose was one owner per claim, the source-model/field/target requirement has
two spec homes and the owner-of-record defers to the non-owner. Decision 3 authorized converting that
citation's *form* (`(397-505)` → `#"<heading>"`), and the conversion is correct; what was not weighed
is that the retargeted heading is a section this pass had just demoted, which turned a stale range
into a live cross-claim.

**Recommended change** — one of:

- (a) Keep spec-008's sentence as the *design requirement* and record the split explicitly (spec-008
  requires the error name three things; spec-010 owns the canonical wording, the substring test
  contract, and the format), noting it as a deliberate exception to partition item 7. This is the
  cheaper path and arguably what a design record legitimately does.
- (b) Drop the three-element enumeration from `spec-008:183` (leave "a fail-loud raise") and repoint
  spec-010's citation at `#"### The finalization trigger"` or at the rationale, so the requirement
  lives once.

This is contract-level (it re-opens a maintainer-decided partition row), so it is escalated below
rather than decided here.

### Low:

#### L1 — Edit 3 silently dropped the maintainer-prescribed `spec-009 (670-687)` citation

`#### Sibling-sentence edits authorized by this decision` gives Edit 3's replacement **verbatim**,
ending: "The auto-trigger direction in `spec-009-…md (670-687)` was not adopted." The landed text
drops the `(670-687)`. Dropping a raw range is defensible on rule 27 grounds, but (i) it deviates from
a maintainer-written replacement string with no record in `### The five sibling-spec edits`, and (ii)
it contradicts this pass's own stated rule two bullets later, where the *other* spec-009 range
(`(1076-1077)`) is left untouched because "decision 3 authorizes exactly the two spec-008 citations,
and spec-009 is deferred". Pick one rule and record it.

#### L2 — the spec states the universal form of the negative claim the build report says it withheld

`### Implementation notes` says spec-008 deliberately does **not** state that
`DjangoSchema` / `DjangoConnectionField` / `DjangoNodeField` do not finalize, because that negative
claim is spec-010's. But `spec-008:173` states its universal quantification: "**nothing in the package
finalizes on a consumer's behalf**", followed by "the ordinary path and the only path". That is the
same claim as spec-010's Edit 3, generalized. Either the claim is spec-008's (then the note is wrong)
or it is spec-010's (then the sentence should say what was *decided* — an explicit trigger was chosen
over an implicit one — without asserting the package-wide negative). Low because the claim is true and
the harm is a mis-describing build report plus a soft duplication, not a reader hazard.

#### L3 — one verbatim 15-word claim now sits in both files

A 9-word-shingle sweep of spec-008 against the rationale (link-def block excluded) returns exactly
three substantive overlaps, and two are legitimate (a quoted spec-010 sentence; the rationale quoting
a retired claim). The third is a genuine duplicate:

- `spec-008 …:193` and rationale `#"One step's wire shape is version-scoped"` both carry
  "`Meta.relation_shapes` made it declarable per field at `0.0.9` and the default moved to
  `"connection"` at `0.0.14`" word for word.

Resolving M1 is the natural moment to remove one copy.

#### L4 — "five reference-style link definitions added" is eight

`### \`docs/SPECS/spec-008-…\` — 40 hunks`, last bullet: "**five** reference-style link definitions
added to the `<!-- docs/SPECS/ -->` group … `spec-001`, `spec-009`, `spec-010`, `spec-010-acceptance`,
`spec-010-finalization`, `spec-010-invariants`, `spec-018`, `spec-032`" — then "All **eight**
disk-verified". Eight is right: the two insertion hunks add `1 + 7 = 8` lines, and the file carries 19
defs where 11 (10 glossary + `spec-008-rationale`) pre-date this pass. **This is the count-error class
the plan calls the cycle's signature defect, firing an eighth time**, inside the artifact section that
warns about it. Unit: def lines. Artifact prose only — no durable doc is wrong.

#### L5 — the rationale's `<!-- docs/SPECS/ -->` defs are not alphabetical

Two misplacements, both in the rationale (spec-008's own block is correctly ordered):

- `spec-008-invariants` sits after `spec-008-options`; it belongs before `spec-008-option1`.
- `spec-008-trigger` precedes `spec-008-strawberry`.

`check_trailing_commas.py` enforces the scaffold and the group headers, not the ordering, so both
passed the gate. Authorship is ambiguous — the ids around them are R1's — but `spec-008-trigger`
points at a heading **this pass created** (`#the-finalization-trigger`), so its position was at least
re-touched here, and the pass's link-definition sweep did not check ordering.

#### L6 — implementation step 3's "two still-unshipped members marked as such" was not performed there

`### Implementation steps` step 3 says `## Why this matters for the goal`'s feature list is rewritten
"with the two still-unshipped members marked as such". The list (`spec-008:29-39`) is byte-identical
to HEAD, and `related aggregates` / `fieldsets` carry no marking. The retensed lead-in ("The end state
this foundation has to support") arguably makes the marking unnecessary, and the shipped/Beta split
*is* stated at `:144` under `### Features that depend on this decision` (D16's box, correctly ticked),
so nothing is factually wrong — but the step was neither performed nor recorded as a deviation.
Confirm the intent and record it either way.

#### L7 — four rationale entries name no spec heading anchor

`BUILD.md` `## Spec rationale extraction` requires each entry name its spec decision by heading **and
anchor**. Eight of the thirteen appended entries carry a `Spec: [Heading][anchor]` line. Five do not:
`### \`## Decision context to preserve\` — retired` (excusable — the heading no longer exists),
`### The two \`### Relevance to this package\` subsections` (`spec-008-graphene` / `spec-008-strawberry`
both exist and are unused by it), and the three pass-level entries (`### Anchor custody across this
pass`, `### The five sibling-spec edits…`, `### \`spec-010\`'s rerun-recovery contract`), which are
keyed to the pass rather than to a spec decision. The last three are reasonable as pass records; the
`Relevance` one should carry its anchors.

### DRY findings

- **The `0.0.9` / `0.0.14` `relation_shapes` sentence is duplicated across spec and rationale** (L3),
  and misattributed in the spec copy (M1). Fix once, in the spec.
- **The unresolved-target error's three-element requirement now has two spec homes** (M2). This is the
  one duplication the pass introduced that the single-ownership law reaches directly.
- **No other duplication found.** The 9-word shingle sweep over spec-vs-rationale returned three runs,
  two benign. The seven demotions genuinely point rather than restate: each pointer names the topics
  the target owns and asserts no phase, signature, error string, or call point of its own. The
  `## Decision context to preserve` retirement is a correct DRY call — all six bullets are preserved
  verbatim in the rationale and every one was already said twice elsewhere in the file.
- **No existence challenge raised.** The pass creates no abstraction; the one candidate — whether a
  demoted heading should survive as a pointer host at all — is settled by the plan's discretion item
  and by inbound anchors from the rationale (`#hard-invariants`, `#acceptance-criteria`,
  `#fakeshop-implication`, `#cookbook-implication` are all live def targets).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **0 lines**. `__all__` and the re-export list
are unchanged. No source file is in this pass's diff at all.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md` (`git status --short CHANGELOG.md` is empty).

### Documentation / release sanity

- **Version strings and card IDs.** No version string was written. Every version reference in the new
  prose (`0.0.4`, `0.0.6`, `0.0.8`, `0.0.9`, `0.0.10`, `0.0.14`) was checked against source or
  `docs/GLOSSARY.md`; all are correct. The only defect is *ownership*, not version — M1.
- **Links introduced or moved.** All 47 link-definition paths across both files disk-verified from
  each file's own directory → **0 missing** (unit: def lines; 19 in the spec, 28 in the rationale).
  **29 anchored defs**, of which **19 are non-GLOSSARY** (3 in the spec, 16 in the rationale) and were
  resolved by slugifying the target's real headings → **19 OK / 0 BAD**, matching R2's figure exactly.
  In-page anchors: **0 occurrences** in both files, so no heading rename could dangle one.
  Used-but-undefined = **0**; defined-but-unused = **0**, both files (unit: distinct ref-ids).
- **Group headers.** All **10** canonical headers present and in order in both files (unit: matching
  header lines). Ordering *within* the rationale's `docs/SPECS/` group is wrong — L5.
- **KANBAN / DB / durable docs.** Untouched by this pass. `KANBAN.md`, `KANBAN.html`,
  `examples/fakeshop/db.sqlite3` and everything under `docs/review/` are dirty from other sessions and
  covered by `## Baseline-dirty out-of-scope files`; none was edited or reverted here.
- **No obsolete staging wording.** No script-rendered doc was regenerated; none needed to be.

### Scope discipline — verified mechanically

- `git status --short` → **41 entries**. The plan records **38** at R1's close; this pass adds exactly
  **3** (`M spec-001`, `M spec-010`, `?? bld-008-r2-…md`) on top of the two it inherited already-dirty
  (`M spec-008`, `?? rationale`). **38 + 3 = 41.** No unaccounted entry, and no baseline-dirty file
  moved state.
- **`spec-009` untouched** — `git status --short docs/SPECS/spec-009-…md` is empty.
- **No source, test, or example file in this pass's diff.** `types/relations.py` and `types/base.py`
  are clean, as R2b's dispatch requires. The seven dirty source/test/example entries are the transport
  session's, all named in the plan.
- **Hunk counts re-derived** (unit: `@@` lines from `git diff -U0 | grep -c '^@@'`): spec-001 → **1**,
  spec-010 → **10**. Both match. spec-008's **40** matches the artifact's own list (40 entries,
  hand-counted) and is corroborated by the -88-line arithmetic above. Total **51**.
- **Exactly five sibling edit sites**, no sixth: spec-001's single sentence; spec-010's Edit 2, Edit 3,
  two citations, and the decision-5 amendment (spanning the docstring, the Phase-3 comment, the
  lifecycle bullet, and the phase-insertion insertion). Reading both diffs end to end, no other line in
  either sibling changed.

### Claims re-verified independently against source

Every one below was re-derived here, not accepted on the artifact's prose.

| Claim | Method | Result |
|---|---|---|
| D3 — no `finalize_django_types` call site in the package | `ast.walk` over all 45 package `.py` files collecting `ast.Call` whose func resolves to the name (unit: call nodes) | **`[]`** — and the collision is real: the only `*finalize*` call nodes are `_finalize_queryset` ×2, `_apply_common_finalize`, `is_finalized` ×4, `finalize` ×3, `_finalize`, `mark_finalized`. **None** is `finalize_django_types`. Textual grep gives 45 *lines*, all docstrings/comments/re-exports — the exact unit trap the AST upgrade was for, and the upgrade was warranted |
| D2 — `convert_relation` | `grep -rn … django_strawberry_framework/ \| wc -l` | **0** |
| D7 — `DjangoModelType` | same | **0** |
| D14 — fakeshop shapes | read `examples/fakeshop/apps/products/schema.py` | `CategoryType.Meta.relation_shapes = {"items": "both"}` (no `properties` key); `ItemType.Meta.relation_shapes = {"entries": "both"}`; `PropertyType.Meta` has **no** key. **2 of 8 falsified, 6 hold** — confirmed |
| D14's premise — the default really is connection-only | `types/base.py #"DEFAULT_RELATION_SHAPE"` | `= "connection"`. Load-bearing for the 2-of-8 split, and it holds |
| D6 — cardinality deferral verbatim in the glossary | `grep -n cardinality docs/GLOSSARY.md` | present verbatim, and restated at the second site. No source read needed — the correction to the plan was right |
| Decision 5 — a shipped test re-finalizes without `registry.clear()` | read `tests/mutations/test_sets.py` around the cited line | Confirmed, and stronger than the artifact claims: the test injects a post-bind Phase-2.5 failure, asserts `registry.is_finalized() is False`, then `monkeypatch.undo()` + `finalize_django_types()` and asserts a clean rerun with the same materialized input class |
| Decision 5 — `test_phase3_strawberry_failure_requires_full_restart` does not exist | `grep -rn` tree-wide | **0** under `tests/` and `examples/`. Tree-wide the count is now **1** — `bld-008-r2-…md:215`, this artifact naming it. Self-reference, not a falsification |
| Decision 5 — the amendment states only what source does | read `types/finalizer.py` docstring + the guards | "It runs four phases"; Phase 1 carries `_audit_primary_ambiguity`; the flag "flips only after every type's Phase 3 call returns … supports a fine-grained partial recovery on rerun"; `if definition.finalized: continue` guards at lines 791, 814, 961/966; `mark_finalized()` is the last statement. The amendment is a faithful restatement, invents nothing, and correctly acknowledges Phase 2.5 without enumerating owners as claims |
| D10 / D13 not churned | diffed every `- ` bullet in the current spec against `git show HEAD:…` | Both prior-art borrow/avoid lists, the `## Why this matters` 11-item list, and D16's eight dependent-feature bullets are **byte-identical to HEAD**. Only the six `## The decision` bullets and one Graphene borrow bullet changed, and that one is a pure retense ("should be preferred" → "are preferred"), exactly as recorded |
| D15 — three cookbook members unshipped | `ls django_strawberry_framework/` | no `aggregates`, no `fieldsets`, no `fields.py`; `permissions.py::apply_cascade_permissions` present |

### Checks re-run

- `check_spec_glossary.py --spec spec-008` → `OK: 10 terms - all have glossary entries and at least one
  spec link.` exit 0. spec-001 → `OK: 21 terms`, exit 0. spec-010 → `OK: 12 terms`, exit 0.
- `check_trailing_commas.py --check` over all five `.md` files → exit 0.
- **Rule-27 occurrence sweep (unit: regex occurrences via `grep -oE … | wc -l`, not lines):** spec →
  **0**, rationale → **0**. Re-run with a widened pattern (`[A-Za-z0-9_/-]+\.[a-z]+:[0-9]+`, any
  extension) → **0** and **0**. A `-rationale.md` is not an exempt scratchpad and it is clean.
- **Fenced blocks (unit: delimiter lines / 2):** spec `grep -c '^\`\`\`'` → **0** lines → **0 blocks**.
  Rationale → **4** lines → **2 blocks**. Matches.
- **Link-def lines (unit: def lines):** spec **19**, rationale **28**, total **47**. Matches.

### The whole-spec read, as a first-time reader

This is the item's point, so it is recorded as a judgement rather than a checklist. **The spec reads as
a current contract.** A reader arriving cold gets: the problem, why it matters, what the two upstream
libraries did and what this package took and refused from each, four options, which won, what the
decision fixed, what triggers finalization, and four pointers at the documents that own the
implementation. **At no point must a chronology be applied to work out what is currently true.**

Specifically, none of the forbidden shapes survives: no amendment block, no retraction paragraph, no
"this was later corrected", no "as of round N", no "should be treated as", no "likely direction", no
"questions to settle". The `## Current strongest direction, not a final plan` heading is gone. Every
grep hit for a hedge marker resolves to one of two legitimate registers — a **rationale pointer**
describing what the companion file contains ("the four sets of questions this record asked … each with
the answer it eventually received"), which is R1's already-accepted shape from line 3 and is not the
spec narrating itself; or a **retained escape-hatch sentence about user annotations**, which is a live
contract and correctly not swept with the finalization sense.

On the over-correction risk the dispatch names: I looked for prose stating a contract the code does not
hold, and found none. Every new assertion was checked against source (table above). The closest calls
are `:66-68`, where `## Package behavior before this decision` keeps a forward-looking voice ("Fail-loud
is not the part to give up", "Any acceptable design must preserve that invariant after finalization") —
but both are true of the shipped package and read as the constraint the decision fixed, which is
precisely what a design record is for. Not a finding.

The one place the reading found a real problem is M1: `## Fakeshop implication`'s closing pointer sends
the reader to a spec that says the opposite. That is a first-time-reader defect, and it is why this
pass is not accepted.

### What looks solid

- **The demotions are genuine.** Seven sections, each with its content preserved in the rationale
  (checked entry by entry — the eight invariants, the seven failure criteria, the two 7/8-step shape
  lists, the eight fakeshop rows, the twelve met acceptance criteria, the nine cookbook members, and
  all six retired `## Decision context to preserve` bullets are quoted verbatim there) and each leaving
  a pointer in the spec that names topics without asserting a contract. Nothing was lost.
- **`### Failure criteria`'s retirement rather than demotion is the right call** and the reasoning is
  right: seven of seven entries are the negation of an invariant in the section above, so a pointer
  would have relocated a redundancy.
- **The four anchor re-sites all landed on prose that carries the meaning.** `metafields` on a sentence
  that already named `Meta.fields = "__all__"` in HEAD's own words (verified against HEAD);
  `finalize_django_types` on the sentence that states the answer, which is exactly what R1's handoff
  conditioned on; `metaprimary` on the spec-018 pointer, where naming the key is the pointer's point;
  `schema audit` riding an existing enumeration. **No hollow host.** The six that did not move are
  where the plan's pre-flight table says they are.
- **The D3 method upgrade was warranted, not ceremony.** A text grep returns 45 lines here; the AST
  walk returns `[]`. The `_finalize_queryset` collision the dispatch warned about is real and was
  correctly excluded.
- **Decision 5 is the strongest work in the pass.** It found a shipped spec asserting the opposite of
  its own code, held the plan's boundary (restate source, do not re-derive), grounded the amendment in
  a shipped test rather than a docstring, and retired a citation to a test that does not exist.
- **Scope is exact.** Three new git-status entries, five sibling edit sites, `spec-009` unopened, no
  source file, no DB, no durable doc, no other cycle's artifact.

### Temp test verification

None. No `.py` was touched and no behavior is at stake; `docs/builder/temp-tests/spec-008-r2/` was not
created. Per the dispatch: failability proofs, hot-path budget, floor verification, and
`scripts/review_inspect.py` are all correctly not applicable to a Markdown-only item, and their
`### …` sections in the build report say so accurately.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: M2 (unresolved-target error requirement).** Resolution needs a maintainer-level call
  because it re-opens `#### The 001-010 ownership partition` item 7, which was decided before dispatch.
  The two paths are written out under M2; path (a) — record the requirement/wording split as a
  deliberate exception — is the cheaper one and does not disturb the citation this pass just fixed.
  Route it to the maintainer through the final gate rather than deciding it inside R2.
- **M1 is not escalated.** It is a plain factual correction with a named owner in `docs/GLOSSARY.md`
  (`spec-047`), and it needs a new link definition in the spec's `<!-- docs/SPECS/ -->` group.
- **L6 needs an intent statement, not necessarily an edit.** If the retensed lead-in was judged
  sufficient, record that as a deviation from implementation step 3.
- **The `### Handed to R3` list stands** — all five items were re-checked and remain accurate, and
  `KANBAN.md`'s board item does now have one fewer target (spec-008 no longer names
  `convert_relation`; `spec-009`, `spec-010`, `spec-019` still do). Generated file; do not hand-edit.
- **Baseline-dirty count is unchanged since R1's close** (38 entries + this pass's 3 = 41). No new
  concurrent growth to append to the plan.

### Review outcome

`revision-needed` — two Medium findings (M1 wrong owner in a durable spec pointer; M2 an
ownership duplication the pass introduced) plus seven Low. Per `### Deviation 2` this routes back to
**Worker 1**, not Worker 2.

The pass is close: the reconstruction methodology holds, the demotions are real and lossless, the
anchors are honest, the scope is exact, and every substantive claim re-derived here checked out.
M1 is a small edit. M2 needs a decision before an edit.

---

## Build report (Worker 1 — apply-changes pass, 2026-08-14)

Second Worker 1 pass on this artifact, dispatched at Worker 3's `revision-needed`. `### Deviation 2`
routes a Worker-3 finding on R1/R2 back to Worker 1 rather than Worker 2, and the pass sets
`planned` again so the artifact returns to the `planned` -> Worker 3 mapping. The prior build-report
block and the review block are left **byte-intact**; every correction to a claim made in them is
recorded in `### Superseding corrections to the prior build report` below.

**Baseline for every range in this block.** The prior pass's ranges are R1-baseline lines. This
pass's are **R2-output lines** — the exact bytes Worker 3 reviewed — because that is the state on
disk when this pass began and the only baseline against which a reader can reproduce the hunks.
Derivation: the three writable durable files were copied to a scratchpad before the first edit and
the ranges come from `git diff --no-index -U0 <scratchpad copy> <file> | grep '^@@'`. The R2-output
copies measure **spec 17,098 bytes / 239 lines** and **rationale 67,883 bytes / 997 lines** (unit:
bytes from `wc -c`, newline-terminated lines from `wc -l`), matching the figures Worker 3 recorded,
which is what proves the copies are the reviewed state and not a later one.

### Files touched

- `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` — M1, M2/decision 7, L2, and one new
  link definition. **5 hunks** (unit: `@@` lines).
- `docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md` — M2/decision 7's third
  telling, L5's ordering, L7's anchors, one new link definition. **16 hunks.**
- `docs/SPECS/spec-010-foundation-0_0_4.md` — decision 7's half of the split, and L1's restored
  citation. **2 hunks** against the R2 output; the cumulative HEAD-side hunk count is unchanged at
  **10**, because both edits fell inside lines the prior pass had already rewritten.
- `docs/builder/bld-008-r2-spec_reconciliation.md` — this block, and the `Status:` line.

`docs/SPECS/spec-001-django_types-0_0_1.md` was **not** touched this pass: no finding reached it.
No source, test, or example file is in this pass's diff — `types/relations.py`, `types/base.py`, and
`testing/relay.py` are all absent from it, as `### Maintainer decision 8`'s dispatch of R2b requires.

### Maintainer decision 7 — how the split was written into both specs

The decision is path (a): spec-008 keeps the three-element requirement as the design constraint, and
spec-010 owns the wording, the format, and the substring-test contract. Written **explicitly in both
documents plus the rationale**, so a reader arriving at any of the three lands on the same division.

- **spec-008 `### The shape that shipped`** gains a paragraph after the shipped-whole sentence: the
  three elements are "the one part of the shape this record still states as a requirement … a design
  constraint, not a message", with the wording, format, and substring assertions handed to
  `[spec-010][spec-010-error]`, and the sentence saying outright why spec-010 cites this section —
  as the requirement's source, not as a second owner. Closes with "The split is deliberate and is
  stated in both documents."
- **spec-010 `### Unresolved-target error format`** keeps the citation decision 3 converted, and
  gains the mirrored half in the same sentence group: "Those citations are the **source of the
  requirement** and nothing more: the design constraint that all three be named is spec-008's, and
  this spec owns the canonical wording, the message format, and the substring-test contract that pin
  it." Same closing sentence.
- **The rationale's third telling is demoted in place, not deleted.** `### The shape that shipped …`
  quotes the pre-schema-construction steps verbatim, step 7 included. A new paragraph *above* the
  "Every step landed" paragraph states that step 7 is quoted "as this record's proposal, not restated
  here as a contract", names where each half now lives, and ends "This entry is the deliberative
  record of what was asked for; it is not a third home for the contract, and nothing below should be
  read as one." The verbatim quotation is untouched — a moved section's quotation is the record, and
  editing it would falsify the word "verbatim" two lines above it.

**One correction to the wording decision 7 invited.** The draft of spec-010's sentence attributed the
requirement to *both* cited specs. Disk check first: `spec-009 (1076-1077)` resolves to
`### Should multiple DjangoTypes per model be allowed?`, not to the error requirement — spec-009
states it at its `### Decision 6: fail loudly`. So the range is **already stale**, independently of
this cycle. The sentence was rewritten to say "Those citations" without asserting what the spec-009
range contains, and the stale range is handed to R3 (below) rather than fixed: spec-009 is deferred
by `### Maintainer decision 6`, and `### Maintainer decision 3` authorizes exactly the two spec-008
citations.

### M1 — the attribution split, disk-verified against both owners

`## Fakeshop implication`'s closing sentence credited `spec-032` for both facts. Rewritten to name
one owner per fact:

> The wire shape each many-side relation exposes is not this record's to state, and it has two owners
> rather than one. Per-field declarability through `Meta.relation_shapes` is
> [`spec-032-full_relay-0_0_9.md`][spec-032]'s. The default a many-side relation falls back to when no
> such declaration is made is [`spec-047-resource_policy-0_0_14.md`][spec-047]'s, which narrowed it as
> part of the bounded-output work.

Verified before writing, not after: `docs/SPECS/spec-047-resource_policy-0_0_14.md` exists on disk,
and `docs/GLOSSARY.md #"Many-side default (\`0.0.14\`, spec-047)"` names spec-047 and gives the
reason ("row-bounded by the execution resource policy") that makes it resource policy rather than
Relay surface. `[spec-047]: spec-047-resource_policy-0_0_14.md` added to the spec's
`<!-- docs/SPECS/ -->` group in alphabetical position (after `spec-032`), path disk-verified.

**L3 falls out of the same edit, as Worker 3 predicted.** The 15-word run
("`Meta.relation_shapes` made it declarable per field at `0.0.9` and the default moved to
`"connection"` at `0.0.14`") no longer appears in the spec at all — the replacement states ownership
rather than the version chronology, and the chronology survives once, in the rationale, which is
where a version history belongs.

**Re-derived, and the first derivation was wrong in the cycle's signature way.** `grep -c 'made it
declarable per field'` returns **0** for *both* files — not because the rationale lost the phrase, but
because the rationale **wraps it across two lines** ("made it declarable\nper field"), and `grep`
matches within a line. A line-oriented grep cannot count a wrapped phrase, exactly as it cannot count
fence blocks or multi-citation lines. Re-derived by normalizing whitespace over the whole file and
counting substring occurrences (unit: occurrences, not lines): spec **0**, rationale **1**. The claim
holds; the first command that appeared to prove it did not. **This is the ninth firing of the unit
trap in this cycle, and the second inside a paragraph about the unit trap** — the failure mode is not
"picking the wrong unit" but "picking a line-oriented tool for a quantity that is not a line".

### The seven Low findings

| # | Resolution | Evidence |
|---|---|---|
| L1 | **Fixed by restoring the citation**, and the rule is now recorded. `spec-010:65` reads "`spec-009-rich_schema_architecture-0_0_4.md (670-687)`" again, as `#### Sibling-sentence edits authorized by this decision` Edit 3 prescribes verbatim. The rule, stated once and applied to both: **this cycle converts spec-008 citations and leaves spec-009 citations exactly as authorized**, because decision 3 authorizes only the two spec-008 ones and decision 6 defers spec-009. Under that rule `(1076-1077)` stays untouched *and* `(670-687)` comes back; the prior pass applied it to one and not the other | Range disk-verified: spec-009 lines 670-687 are `### Layer 3: Finalization trigger` through "Avoid relying only on a schema extension", which is exactly the direction the sentence says was not adopted |
| L2 | **Fixed in the spec, not in the build report.** `### The finalization trigger` no longer asserts the package-wide negative. It now states what was decided ("the trigger this decision chose"; the implicit alternative "was weighed and not adopted") and hands the negative to its owner: "Which constructors do not finalize, and the package-wide guarantee that none of them does, are [`spec-010`][spec-010-finalization]'s." The prior block's `### Implementation notes` becomes accurate rather than being contradicted | `grep -c 'nothing in the package finalizes'` -> **0** (unit: matching lines). The `finalize_django_types` glossary anchor stays on this sentence; `check_spec_glossary` still `OK: 10 terms` |
| L3 | **Fixed with M1** — see above | |
| L4 | **Artifact-prose only; corrected in the superseding table below**, not by editing the reviewed block | Re-derived here: **8** def lines added by the prior pass, **21** def lines in the spec now (unit: lines matching `^\[ref\]: `) |
| L5 | **Fixed.** `spec-008-invariants` moved to before `spec-008-option1`; `spec-008-trigger` moved to after `spec-008-strawberry`. Both groups in both files now verify as sorted by an ordering check, not by eye | Script below reports no `NOT ALPHABETICAL` group in either file |
| L6 | **Recorded as a deviation from implementation step 3; no edit made.** The two unshipped members (`related aggregates`, `fieldsets`) stay unmarked in `## Why this matters for the goal`'s list because (i) the list's lead-in is explicitly forward-looking — "The end state this foundation has to support" — so an unmarked member asserts nothing false, (ii) the shipped/Beta split is already stated once, at `### Features that depend on this decision` ("related aggregates and fieldsets are Beta cards"), and marking it twice is the duplication this cycle exists to remove, and (iii) Worker 3 verified that list byte-identical to HEAD as part of D10/D13 being un-churned; editing it now would churn a list the audit certified | `grep -n 'related aggregates and fieldsets are Beta cards'` -> 1 occurrence, spec line 144 |
| L7 | **Fixed for TEN entries, not the four the finding counted** — see the widened-scope note below. Each now names something a reader can look up. `### The two \`### Relevance to this package\` subsections` gets both parent anchors, with a parenthetical saying why the parent rather than the subsection (the two `### Relevance to this package` headings are duplicates). `### \`## Decision context to preserve\` — retired` gets `Spec: none — the heading was retired`, plus the four anchors its content was distributed to. The three pass-level entries each get `Spec: no single decision — this entry is keyed to the reconciliation pass rather than to a spec heading`, with one line saying where the change landed. The five R1-era removed-section entries each get `Spec: none — the heading was removed`, naming the one surviving sentence that is the pointer for all five | Derived by parsing the file into entries rather than by grepping (unit: `###` entry blocks after `## Entries keyed to the spec`): **22 entries, 0 without a `Spec:` line**. Before this pass: 5 without. One new ref-id, `spec-008-goal`, added to the rationale's `<!-- docs/SPECS/ -->` group in alphabetical position; its anchor resolves |

#### L7's scope is wider than the finding, and the widening was found by re-deriving its number

The finding says "four rationale entries name no spec heading anchor" in its heading and lists
**five** in its body — the count discrepancy that made re-derivation worth doing. Parsing the file
into entries rather than grepping for a string found **five more**, all R1-era and all outside the
thirteen entries Worker 3 audited: `### \`### Finalization trigger choices\``, `### \`### Registry
questions\``, `### \`### User annotation questions\``, `### \`### Generic fallback questions\``, and
`### \`### Rich-schema dependency questions\``. Worker 3 scoped the audit to the entries this pass
appended, which is the correct scope for auditing a pass; but `BUILD.md` `## Spec rationale
extraction`'s requirement is a property of the **file**, so ten entries were failing it, not five.

All five key to headings the R1 move removed whole, so no anchor to them can exist. They now say so
and name the surviving pointer: spec-008's `### The finalization trigger` closes with one sentence
covering the four candidate triggers **and** all four question sections, so it is the correct host
for all five. This also discharges a promise the rationale's own `## How to read this file` already
made — "Five entries key to headings that no longer exist in the spec at all … Each anchors the
surviving section nearest to where it stood and says so" — which was true of the prose and not yet
true of the entries.

### Superseding corrections to the prior build report

The reviewed blocks are byte-intact, so corrections live here. Each was re-derived this pass rather
than copied from the review.

| Where | Claim as written | Correct value, with unit and command |
|---|---|---|
| `### \`docs/SPECS/spec-008-…\` — 40 hunks`, last bullet | "**five** reference-style link definitions added" | **eight** def lines, unit: lines matching `^\[[^]]+\]: `. `git diff -U0` on that pass's two insertion hunks adds `1 + 7 = 8` lines; the same bullet's own list names eight ref-ids and its next sentence says "All eight disk-verified". L4 — the unit trap's eighth firing, inside the section that warns about it |
| Same section | Def count at that pass's close | **19** def lines. **21** now (`spec-010-error`, `spec-047`) |
| `### Implementation notes`, the withheld-negative note | Accurate as written **after** this pass's L2 edit; it was contradicted by the spec at the time it was written | No correction to the note; the spec changed to match it |
| `### Implementation steps` step 3 | "with the two still-unshipped members marked as such" | **Not performed, and deliberately not performed** — see L6 above |

### Checks re-run, with results quoted

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-definition_order_independence-0_0_4.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` exit 0. Unchanged, as the
  dispatch requires.
- Same script on `spec-010` -> `OK: 12 terms - all have glossary entries and at least one spec link.`
  exit 0.
- `uv run python scripts/check_trailing_commas.py --check` over all three durable `.md` files written
  this pass -> exit 0 (scaffold and the 10 canonical group headers intact in each).
- **Rule-27 occurrence sweep** (unit: regex **occurrences** via `grep -oE … | wc -l`, never lines):
  narrow pattern `[a-zA-Z_/-]+\.(py|md):[0-9]+` -> spec **0**, rationale **0**. Widened to any
  extension, `[A-Za-z0-9_/-]+\.[a-z]+:[0-9]+` -> spec **0**, rationale **0**.

### Counts, with units and derivation commands

Every number below was derived by running the command, this pass, on the file as it now stands. The
before/after pairs use the scratchpad R2-output copies as "before".

| Quantity | Unit | Command | spec-008 | rationale |
|---|---|---|---|---|
| Size | bytes | `wc -c` | 17,098 -> **18,023** | 67,883 -> **70,620** |
| Length | newline-terminated lines | `wc -l` | 239 -> **243** | 997 -> **1,042** |
| Fenced blocks | delimiter lines / 2 | `grep -c '^\`\`\`'` | 0 lines -> **0 blocks** | 4 lines -> **2 blocks** |
| Link definitions | def lines | `grep -cE '^\[[^]]+\]: '` | 19 -> **21** | 28 -> **29** |
| Canonical group headers | matching header lines | `grep -cE '^<!-- (…) -->$'` | **10** | **10** |
| Rationale entries | `###` blocks after `## Entries keyed to the spec` | parsed, not grepped | n/a | **22**, of which **0** lack a `Spec:` line (was 5) |
| Hunks this pass | `@@` lines | `git diff --no-index -U0 <R2 copy> <file>` | **5** | **16** |

**Arithmetic self-check, the same proof Worker 3 accepted for the R1 baseline.** Summing
`new_count - old_count` across this pass's hunks: spec `0 + 2 + 0 + 1 + 1 = +4`, and `239 + 4 = 243`
= `wc -l`. Rationale `(4 x 5) + 7 + 4 + 4 + 3 + 3 + 3 + 1 + 1 - 1 - 1 + 1 = +45`, and
`997 + 45 = 1,042` = `wc -l`. Both terminate at the observed file, so the hunk lists below are
complete. **Sixteen hunks, and the prose groups them into four changes** — five identical L7 lines,
one decision-7 paragraph, five more L7 blocks, five link-definition lines — which is a different
count from sixteen and is said so here rather than left to read as a contradiction.

### Link-definition audit — ordering, paths, and reconciliation, all machine-checked

Run as one script over both files rather than by eye, because L5 is exactly the defect eye-checking
misses:

- **All 10 canonical group headers** present and in order in both files (unit: matching header lines).
- **Alphabetical within every group** — the check compares each group's ref-id list against its own
  sort and prints any mismatch. **No mismatch in either file**, after L5's two moves.
- **Every def path disk-verified** from the citing file's own directory: **21 + 29 = 50** paths,
  **0 missing** (unit: def lines).
- **Every anchored def's anchor resolved** by slugifying the target file's real headings, duplicate
  headings included: **0 bad anchors** in either file.
- **Used-but-undefined: 0. Defined-but-unused: 0**, both files (unit: distinct ref-ids; 21 used / 21
  defined in the spec, 29 / 29 in the rationale).
- **In-page anchors in either body: 0**, so no heading this pass touched can dangle one.

### Spec changes made (Worker 1 only)

Ranges are **R2-output lines**, per the baseline note at the top of this block, and come from
`git diff --no-index -U0`'s left side.

#### `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` — 5 hunks

- **173** (`### The finalization trigger`, opening sentence) — L2. Replaced the universal negative
  "nothing in the package finalizes on a consumer's behalf" with the decision it was standing in for,
  and handed the package-wide guarantee to spec-010. *Claim the section no longer makes: that no
  constructor anywhere in the package finalizes — true, but spec-010's to state.*
- **184,0 -> +185,2** (`### The shape that shipped`, after the shipped-whole sentence) — decision 7,
  spec-008's half of the split. Two lines: the blank separator and the new paragraph.
- **193** (`## Fakeshop implication`, closing sentence) — M1 and L3. One owner per fact; the version
  chronology dropped from the spec.
- **221,0 -> +224** and **225,0 -> +229** (`<!-- docs/SPECS/ -->` group) — one def line each:
  `spec-010-error` (between `spec-010-acceptance` and `spec-010-finalization`) and `spec-047` (after
  `spec-032`). Both alphabetical, both disk-verified.

#### `docs/SPECS/appx/spec-008-…-rationale.md` — 16 hunks

- **352,0 -> +353,4**, **435,0 -> +440,4**, **475,0 -> +484,4**, **512,0 -> +525,4**,
  **548,0 -> +565,4** — L7 widened: the five R1-era removed-section entries
  (`### Finalization trigger choices` and the four `### … questions`), each gaining the same
  three-line `Spec: none — the heading was removed` block plus its blank separator.
- **743,0 -> +764,7** (`### The shape that shipped …`) — decision 7's third-telling demotion, above
  the "Every step landed" paragraph.
- **829,0 -> +857,4**, **854,0 -> +886,4**, **870,0 -> +906,3**, **887,0 -> +926,3**,
  **918,0 -> +960,3** — L7 as filed: five `Spec:` lines, one per reconciliation-pass entry that
  lacked one (`## Decision context to preserve`, the two `### Relevance to this package` subsections,
  `### Anchor custody across this pass`, `### The five sibling-spec edits …`,
  `### \`spec-010\`'s rerun-recovery contract`).
- **964,0 -> +1009**, **965,0 -> +1011**, **971 -> (removed)**, **974 -> (removed)**,
  **975,0 -> +1020** — the link-definition block: `spec-008-goal` added, `spec-008-invariants` moved
  before `spec-008-option1`, `spec-008-trigger` moved after `spec-008-strawberry` (L5).

#### `docs/SPECS/spec-010-foundation-0_0_4.md` — 2 hunks

- **65** (`## Strawberry finalization strategy`, the auto-trigger bullet) — L1. `(670-687)` restored
  to the spec-009 citation, matching Edit 3's prescribed replacement verbatim.
- **408** (`### Unresolved-target error format`, opening) — decision 7, spec-010's half of the split.

### Failability proofs / hot-path budget / floor verification / `review_inspect.py`

Not applicable, and for the same reason as the prior pass: no `.py` file was touched, no boundary was
added, no code path runs. Recorded rather than omitted.

### Handed to R3

The prior block's `### Handed to R3` list stands and Worker 3 re-checked it. Two items change and one
is added:

- **`django_strawberry_framework/testing/relay.py`'s "(or build the schema)" message** — no longer
  R3's to escalate. `### Maintainer decision 8` folds it into **R2b**, which runs the full unmodified
  worker chain. R3 records it as dispatched, not as deferred.
- **`spec-010 #"exactly as required by"`'s `spec-009 (1076-1077)` range is stale** — NEW, found this
  pass while writing decision 7's spec-010 half. It resolves to
  `### Should multiple \`DjangoType\`s per model be allowed?`; the requirement it is cited for is at
  spec-009's `### Decision 6: fail loudly`. Left untouched on purpose — decision 3 authorizes exactly
  the two **spec-008** citations and decision 6 defers spec-009 — and it is the same defect class as
  the two spec-008 ranges decision 3 exists to fix. Belongs in R3's `### Deferred work catalog`
  alongside spec-009's `### Layer 3`, ideally in the same future spec-009 residual cycle, since both
  are spec-009-facing citations.
- **`spec-009`'s `### Layer 3: Finalization trigger`** — unchanged as an item, with one addition:
  spec-010 now cites the `(670-687)` range again (L1), so the deferred spec-009 cycle has two inbound
  citations to reconcile, not one.

### Scope discipline

- `git status --short` -> **41 entries** (unit: status lines), the same 41 Worker 3 counted. This pass
  creates no new file and moves no baseline-dirty file's state: every file it wrote was already dirty.
- `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` — read only, never written.
  `git status --short` on it is empty.
- `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, `CHANGELOG.md`,
  `README.md`, `docs/TREE.md`, everything under `docs/review/`, and every other cycle's artifact:
  untouched.
- No `git stash`, `git checkout`, `git restore`, or `git worktree` was run. HEAD-side reads used
  `git show HEAD:<path>` and `git diff`.

## Status

> Not the artifact's status. The canonical `Status:` line is the header block above (line 5), and it
> is the only line Worker 0 reads to drive dispatch (`ARTIFACT.md:3`). This block records one pass's
> transition at the moment that pass wrote it.

`Status: planned` — set per `### Deviation 2`. R1 and R2 skip `built`, and `planned` routes this
artifact back to Worker 3 for re-review of the two Medium findings and the seven Low.

---

## Review (Worker 3, pass 2)

Re-review of the apply-changes pass. Fresh subagent: no in-context memory of pass 1's review. The
prior pass's settled results (the whole-spec clean-contract read, the reconstruction methodology, the
D10/D13 un-churned verdict, the drift-row re-verification) are taken as standing per the dispatch and
were not redone. **Every number in this section was re-derived on disk this pass**; none was copied
from the build report or from the dispatch prompt.

### Verdict 1 — Maintainer decision 7's split: SYMMETRIC, and correctly written into all three documents

Read as three separate first-time readers, one per document. All three land on the same division.

| Document | What it claims as its own | What it hands over |
|---|---|---|
| `spec-008 #"### The shape that shipped"` (`:185`) | "any implementation must name the source model, the source field, and the target model … a design constraint, not a message" | "the canonical wording, the message format, and the substring assertions that pin them are [`spec-010`][spec-010-error]'s" |
| `spec-010 #"### Unresolved-target error format"` (`:408`) | "this spec owns the canonical wording, the message format, and the substring-test contract that pin it" | "the design constraint that all three be named is spec-008's" |
| rationale `#"### \`### The shape that shipped\`"` (`:764`) | nothing — "it is not a third home for the contract" | both halves, each named with its owner |

- **The mirror is exact.** Both specs close with the identical sentence "The split is deliberate and
  is stated in both documents." — the only two 9-word shingles spec-008 and spec-010 now share
  beyond the pre-existing quoted-invariant run (measured: 3 shared shingles total, listed below).
  Neither document's half is a superset of the other's.
- **Both directions are linked, not just asserted.** `spec-008:185` carries
  `[spec-010][spec-010-error]` → `#unresolved-target-error-format`, verified to resolve; `spec-010:408`
  carries `#"### The shape that shipped"`, verified to resolve. This closes the prior M2 exactly: the
  citing spec no longer defers to a non-owner, because the section it cites now says on its face what
  it does and does not own.
- **The "why spec-010 cites this section" statement is present and accurate** — "which is why
  spec-010 cites this section as the requirement's source rather than restating the constraint as its
  own", and spec-010 does exactly that.
- **The three-element enumeration is NOT literally duplicated between the two specs.** spec-008 writes
  "the source model, the source field, and the target model"; spec-010 writes "source model, source
  field, and target model". They do not shingle-match. What survives in both is the *requirement*,
  which is what a permitted cross-spec reference looks like under `## The single-ownership law`
  ("other specs can reference them"), with the ownership claim now asserted in exactly one place per
  half.

**The rationale's third telling is unambiguously deliberative.** The new paragraph is not "above the
step list" (the dispatch prompt's paraphrase) — on disk it sits **below** the verbatim quotation and
above "Every step landed", i.e. immediately after the step 7 it disclaims. That is the better
position, not a worse one: the reader meets the disclaimer at the point of exposure. Its language
leaves no room ("quoted above as this record's proposal, not restated here as a contract"; "it is not
a third home for the contract, and nothing below should be read as one"), and it names where each
half lives with live links.

**The in-place-demotion argument is sound, not a rationalisation.** Verified on disk: the quotation's
own italic lead-in two lines above reads *"Moved — the pre-schema-construction steps, verbatim."*
Editing step 7 inside that block would falsify the label. More decisively, `BUILD.md`
`## Spec rationale extraction` makes the rationale the home for "any claim the decision once made and
may no longer make" — the quotation **is** the record, and a record edited to match the current
contract stops being one. Deleting step 7 from the quote was the only alternative and it destroys the
archive. Demote-in-place was the only correct option available.

### Verdict 2 — the `spec-009 (1076-1077)` staleness claim: VERIFIED against disk

Worker 1's rejection of part of decision 7's invited wording is correct on the facts.

- `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:1075` is
  `### Should multiple \`DjangoType\`s per model be allowed?`; **1076-1077** are its body and a blank
  line, and say nothing about an error, a raise, or a fail-loud requirement.
- The requirement is at **1068-1069**: `### Decision 6: fail loudly` — "Raise at finalization with the
  source model, field, and target model named." An 8-line miss, not a near-miss.

So the range **is** stale independently of this cycle (it is stale at HEAD too — `### Maintainer
decision 3`'s own table quotes it unchanged), the rewrite to "Those citations" was **necessary** and
not over-caution, and handing the range to R3 rather than fixing it is the right disposition:
`### Maintainer decision 3` authorizes exactly the two **spec-008** citations and
`### Maintainer decision 6` defers spec-009. Correct reasoning, correctly scoped.

Corroborating: L1's restored `(670-687)` was re-derived line by line — spec-009 **670** is
`### Layer 3: Finalization trigger` and **687** is "Avoid relying only on a schema extension.
Extensions run too late; the schema is already built." The artifact's evidence cell is exact.
`git status --short` on spec-009 is empty: **untouched**, as required.

### Verdict 3 — L7's widening from 4/5 to 10: VERIFIED, and `Spec: none — …` SATISFIES the requirement

Re-derived by parsing, not grepping. The rationale was split into `###` blocks from
`## Entries keyed to the spec` (`:88`) to the link-definition delimiter, fence-aware:

- **22 entries. 0 without a `Spec:` line.** (Unit: `###` blocks, not lines.) Confirmed exactly.
- The five newly-fixed R1-era entries are at `:351`, `:438`, `:482`, `:523`, `:563` and all key to
  `### Finalization trigger choices` / the four `### … questions` headings — headings that do not
  exist in the spec, so the "no anchor can exist" premise is true.
- Their shared pointer host is verified live: `spec-008 #"### The finalization trigger"` closes with
  one sentence covering "The four candidate triggers weighed here … **and** the four sets of
  questions this record asked about the registry, user annotations, generic fallback, and the
  rich-schema subsystems". It genuinely hosts all five.

**Judgement on the requirement.** `BUILD.md` states the rule and, in the same sentence, its purpose:
"an entry naming no decision cannot be looked up, and is worthless however well argued." The test is
**lookup-ability**, and every one of the ten reworked entries passes it — each `Spec: none — …` names
a live, anchored, resolving destination (`[The finalization trigger][spec-008-trigger]`,
`[Prior art: Graphene-Django][spec-008-graphene]`, `[Why this matters for the goal][spec-008-goal]`,
`[The decision][spec-008-decision]`, `[\`spec-010\`][spec-010]`). This **satisfies** the requirement
rather than evading it. It would be an evasion if `Spec: none` stood alone; a bare "none" is what
"cannot be looked up" means, and none of the ten is bare.

The widening itself is the right call and was found the right way: the requirement is a property of
the **file**, not of a pass's additions, so scoping it to the appended entries was the defect. The
finding's own 4-vs-5 discrepancy is what triggered the re-derivation — the intended effect of
re-deriving rather than trusting.

### High:

None.

### Medium:

None. Both prior Mediums are closed:

- **M1 — closed.** `## Fakeshop implication:194` now reads one owner per fact. Disk-verified
  independently of the build report: `docs/SPECS/spec-047-resource_policy-0_0_14.md` exists;
  `docs/GLOSSARY.md #"Many-side default (\`0.0.14\`, spec-047)"` names spec-047 and gives the
  resource-policy reason; and spec-032's own text confirms it is **not** the `0.0.14` owner — it
  states the opposite default twice (`#"the \`\"both\"\` default keeps the \`list[T]\` field"` and its
  Slice-3 checklist "`\"both\"` (default) keeps the `list[T]` field"). Attribution is now correct in
  both directions. `[spec-047]: spec-047-resource_policy-0_0_14.md` is in the `<!-- docs/SPECS/ -->`
  group in alphabetical position (after `spec-032`) and its path resolves.
- **M2 — closed** by decision 7's split; see Verdict 1.

### Low:

#### L8 — NEW: L2's replacement pointer resolves to a spec-010 section that does not carry the claim

`docs/SPECS/spec-008-definition_order_independence-0_0_4.md:173`, the sentence this pass wrote to
close L2:

> Which constructors do not finalize, and the package-wide guarantee that none of them does, are
> [`spec-010`][spec-010-finalization]'s.

`[spec-010-finalization]: spec-010-foundation-0_0_4.md#finalization-phase-finalize_django_types`
resolves to `spec-010:309`, `### Finalization phase: \`finalize_django_types()\``. That section is the
phase lifecycle and the failure-atomicity contract. **It does not state the negative.** Grepped
spec-010 for `do not call` / `does not call` / `auto-trigger` / `only trigger`: hits at **21, 65, 475,
552** — none inside 309-406. The claim's real homes are:

- `spec-010:21` (`## What does not ship in this slice`) — "no shipped helper wraps it — the explicit
  consumer call remains the only trigger"
- `spec-010:65` (`## Strawberry finalization strategy`) — "No shipped helper auto-triggers
  finalization: `DjangoSchema`, `DjangoConnectionField`, and `DjangoNodeField` do not call
  `finalize_django_types()`; the explicit consumer call is the only trigger."

So a reader who follows the pointer lands 244 lines from the guarantee, in a section about something
else. This is the **same defect class** as the M1 the pass just fixed and as the prior M2, and it is
new prose from this pass: the ref-id was reused because it names the right *document*, without
checking that the anchor's section makes the claim being handed to it.

**Low, not Medium**, on a deliberate severity call: the named owner (`spec-010`) is correct, the claim
genuinely is spec-010's, the anchor resolves to a real section in the right file, and — unlike M1 —
the reader is not sent to prose asserting the opposite, only to prose that is silent. No durable
statement is false.

**Recommended change.** Add one anchored def to the spec's `<!-- docs/SPECS/ -->` group, in
alphabetical position, e.g.
`[spec-010-trigger]: spec-010-foundation-0_0_4.md#strawberry-finalization-strategy`, and use it for
the negative half of `:173` only. `[spec-010-finalization]`'s other two uses (`:175` the pass itself,
`:183` the finalization contract) are **correct for `:309`** and were checked; leave them alone.
Re-run the link-def audit afterwards — the def block stays alphabetical and the anchor slug
`strawberry-finalization-strategy` was verified to resolve.

### The prior seven Low findings — each confirmed against disk

| # | Verdict | Independent evidence re-derived this pass |
|---|---|---|
| L1 | **Confirmed fixed** | `spec-010:65` carries "`spec-009-rich_schema_architecture-0_0_4.md (670-687)`" again, matching Edit 3's prescribed replacement. The stated rule — *this cycle converts spec-008 citations and leaves spec-009 citations exactly as authorized* — is applied **consistently to both** spec-009 ranges: `(670-687)` restored at `:65`, `(1076-1077)` left byte-untouched at `:408`. Both are spec-009 citations; both are now left as authorized. One rule, applied twice, as the finding demanded |
| L2 | **Confirmed fixed** | `grep -c 'nothing in the package finalizes'` -> **0** in both files, and — because a line-oriented grep cannot see a wrapped phrase — re-derived by whitespace-normalizing each whole file and counting substring **occurrences**: spec **0**, rationale **0**. The universal negative is gone. The replacement states the decision and its rejected alternative without the package-wide quantifier. `check_spec_glossary` still `OK: 10 terms`, so the `finalize_django_types` anchor rode the rewrite. (The pointer's *anchor* is L8; the removal itself is clean) |
| L3 | **Confirmed fixed, and it did fall out of M1** | Whitespace-normalized occurrence count of "made it declarable per field at `0.0.9` and the default moved to": spec **0**, rationale **1**. Stating ownership instead of chronology genuinely deleted the run — the replacement shares no 9-word shingle with the rationale sentence. The version chronology survives once, in the rationale, which is where it belongs |
| L4 | **Confirmed corrected in the superseding table**, and the corrected value re-derived: **8** def lines added by the prior pass; the spec now carries **21** def lines (unit: lines matching `^\[ref\]: `), consistent with 19 at that pass's close plus this pass's `spec-010-error` and `spec-047`. Prior blocks are byte-intact, per `ARTIFACT.md` `## Re-pass sections` | |
| L5 | **Confirmed fixed, and machine-checked independently.** My own ordering script (parse each `<!-- group -->`, compare its ref-id list against `sorted()`) reports **no mismatched group in any of the three files**. `spec-008-invariants` now precedes `spec-008-option1`; `spec-008-trigger` now follows `spec-008-strawberry` | |
| L6 | **The no-edit is RIGHT, not an evasion** — see the judgement below | |
| L7 | **Confirmed fixed, at the widened scope** — see Verdict 3 | |

#### L6 — judgement: the no-edit is correct, and all three of its arguments verify

The dispatch asks whether declining to edit is an evasion. It is not, and the reasons are checkable
rather than rhetorical:

- **(i) verified.** The lead-in is "The end state this foundation has to support:" — forward-looking,
  so an unmarked `related aggregates` / `fieldsets` asserts nothing false. Note this lead-in **was**
  rewritten by the prior pass (HEAD reads "The intended end state includes:"), so implementation step
  3 was substantially performed; only its marking clause was not.
- **(ii) verified.** `grep -n 'related aggregates and fieldsets are Beta cards'` -> exactly **1**
  occurrence, `spec-008:144`. The shipped/Beta split is stated once, and marking the list would state
  it twice — the precise duplication this cycle exists to remove.
- **(iii) verified.** The eleven bullets are byte-identical to `git show HEAD:` (extracted and
  `diff`ed; the surrounding lead-in and trailing paragraph differ, the bullet block does not).
  Editing them now would churn a list the audit certified.

The prior finding's own remedy was "Confirm the intent and record it either way." A recorded
deviation with a substantive argument is one of the two offered resolutions, and it is the one whose
argument survives checking. Accepted.

### DRY findings

- **No new duplication that the single-ownership law reaches.** Re-ran the 9-word-shingle sweep of
  spec-008 against the rationale (link-def blocks excluded, whitespace normalized): **4 runs**, up
  from 3. Two are the pre-existing benign pair (a quoted spec-010 invariant sentence; the
  rich-primary-type fakeshop phrase). The two new ones — `name the source model, the source field, and
  the target model` and `the canonical wording, the message format, and the substring assertions that
  pin` — are **both inside decision 7's demotion paragraph**, i.e. inside the prose whose entire job
  is to say "the requirement lives in the spec and the wording lives in spec-010, and not here." A
  pointer that names what it is pointing at is the shape this cycle's other seven demotions already
  use and that pass 1 accepted. Not a finding; recorded so the count change is not silent.
- **spec-008 vs spec-010: 3 shared shingles**, and two of them are the deliberate mirrored closing
  sentence. The three-element enumeration itself does **not** match across the two specs.
- **No existence challenge raised.** This pass creates no abstraction; the two new ref-ids
  (`spec-010-error`, `spec-047`, plus the rationale's `spec-008-goal`) are link definitions with live
  readers, not indirection.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **0 lines**. `__all__` and the re-export list
unchanged. No `.py` file is in this pass's diff at all.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md` (`git status --short CHANGELOG.md` is empty).

### Documentation / release sanity

- **Link definitions, machine-audited across all three written files** (one script: parse the def
  block, check the ten canonical headers and their order, check alphabetical ordering per group,
  resolve every path from the citing file's own directory, slugify every target's real headings
  including duplicate-heading `-1` suffixes, and diff used-vs-defined ref-ids):

  | | spec-008 | rationale | spec-010 |
  |---|---|---|---|
  | 10 canonical headers, in order | yes | yes | yes |
  | alphabetical within every group | yes | yes | yes |
  | def lines | **21** | **29** | **12** |
  | paths missing on disk | **0** | **0** | **0** |
  | anchored defs that fail to resolve | **0** | **0** | **0** |
  | used-but-undefined / defined-but-unused | **0 / 0** | **0 / 0** | **0 / 0** |
  | in-page `](#…)` anchors in body | **0** | **0** | **0** |

  Total def paths disk-verified: **21 + 29 = 50**, matching the build report. **L8 is the one defect
  this table structurally cannot catch** — an anchor that resolves to the wrong section is a
  *semantic* miss, not a broken link, which is exactly why it needed reading and not a script.
- **Version strings and card IDs.** No version string was written this pass. `0.0.9` / `0.0.14` in the
  M1 rewrite were re-checked against `docs/GLOSSARY.md` and spec-032's own text; correct.
- **KANBAN / DB / generated docs.** `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`,
  `examples/fakeshop/db.sqlite3` untouched by this pass — all dirty from other sessions and covered by
  `## Baseline-dirty out-of-scope files`. No script-rendered doc was regenerated; none needed to be.
- **Nothing under `docs/review/` was touched.** Its 8 entries (3 `M`, 2 ` D`, 3 `??`) are the open
  maintainer escalation; not edited, not reverted, not restored.

### Scope discipline — re-derived mechanically

- `git status --short` -> **41 entries** (unit: status lines). Unchanged from pass 1's count; this
  pass created no new file and moved no baseline-dirty file's state.
- **No source, test, or example file in this pass's diff.** The three R2b-owned files are **clean**:
  `git status --short django_strawberry_framework/types/relations.py types/base.py testing/relay.py`
  returns nothing. The dirty `.py` entries are the transport session's five, all named in the plan's
  baseline-dirty group 2.
- **`spec-009` untouched** — `git status --short` on it is empty, and `### Maintainer decision 6`
  requires exactly that.
- **`spec-001` untouched this pass** — cumulative HEAD-side hunks still **1** (unit: `@@` lines).
- **`spec-010` cumulative HEAD-side hunks still 10**, confirming the build report's claim that this
  pass's 2 hunks fell inside lines the prior pass had already rewritten.

### Counts re-derived, with units

Every cell below was produced by running the command on disk this pass. **None was carried from the
build report or the dispatch prompt.**

| Quantity | Unit | Command | spec-008 | rationale |
|---|---|---|---|---|
| Size | bytes | `wc -c` | **18,023** | **70,620** |
| Length | newline-terminated lines | `wc -l` | **243** | **1,042** |
| Fence delimiter lines | lines | `grep -c '^\`\`\`'` | **0** | **4** |
| Fenced blocks | delimiter lines / 2 | derived | **0** | **2** |
| Link definitions | def lines | `grep -cE '^\[[^]]+\]: '` | **21** | **29** |
| Canonical group headers | matching header lines | `grep -cE '^<!-- … -->$'` | **10** | **10** |
| Rationale entries | `###` blocks, parsed fence-aware | script | n/a | **22**, of which **0** lack `Spec:` |
| Rule-27, narrow `\.(py\|md):[0-9]+` | regex **occurrences** (`grep -oE … \| wc -l`) | | **0** | **0** |
| Rule-27, widened `\.[a-z]+:[0-9]+` | regex **occurrences** | | **0** | **0** |

All match the build report. `spec-010`: 596 lines, 12 def lines, 10 headers.

**Arithmetic self-proof — verified, and it terminates.** Summing `new_count - old_count` across the
recorded hunk groups:

- spec: `0 + 2 + 0 + 1 + 1 = +4`; `239 + 4 = 243` = `wc -l` on disk. **5 hunk groups**, matching the
  claimed 5.
- rationale: `(4 x 5) + 7 + 4 + 4 + 3 + 3 + 3 + 1 + 1 - 1 - 1 + 1 = +45`; `997 + 45 = 1,042` =
  `wc -l` on disk. Re-added the expression independently: `20+7=27, +4+4+3+3+3=44, +1+1-1-1+1=45`.
  **5 + 1 + 5 + 5 = 16 hunk groups**, matching the claimed 16.

Both lists are internally consistent AND terminate at the observed file, which is the standard pass 1
accepted for the R1 baseline. The `239` / `997` "before" figures are the values pass 1 recorded and
are not independently re-derivable here (the scratchpad copies are the pass's own artifact) — but
they are the *only* inputs not re-derived, and the arithmetic forces them from the observed 243 /
1,042 given the hunk lists.

### Checks re-run, with results quoted

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-…md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0.** Exactly the
  `OK: 10 terms` the dispatch requires.
- Same script on `docs/SPECS/spec-010-foundation-0_0_4.md` -> `OK: 12 terms - all have glossary
  entries and at least one spec link.` **exit 0.**
- `uv run python scripts/check_trailing_commas.py --check` over all four `.md` files written this
  pass (spec-008, rationale, spec-010, this artifact) -> **exit 0.**
- Rule-27 occurrence sweep: **0 / 0** narrow, **0 / 0** widened. Unit is regex occurrences, never
  lines — a `path:NN` wrapped across a line break would be invisible to a line count, and both
  patterns were run with `grep -oE … | wc -l` for that reason.

### The new prose, read against the clean-contract standard

Only prose written **this pass** was re-read for this (the whole-spec read is settled). Two borderline
calls, both examined and cleared:

- **`:185` "the one part of the shape this record still states as a requirement".** "still" reads as a
  contrast against the *surrounding demotions in the same document*, not against a past version of it;
  a reader needs no chronology to know what is currently true, because the sentence states the
  requirement outright in its next clause. Cleared — recorded rather than passed over silently,
  because it is the closest this pass comes to self-narration.
- **`:173` "was weighed and not adopted".** States a rejected alternative, which is what a design
  record's decision section is for, and it carries no hedge about what currently holds. Cleared.

No amendment block, no retraction, no "as of round N", no "should be treated as" entered the spec this
pass.

### What looks solid

- **Decision 7's split is the strongest work in the pass.** It is symmetric, bidirectionally linked,
  stated in three documents without becoming a third contract, and it closes M2 at the root rather
  than by moving text around. The rejected-alternative reasoning in the decision itself (that a design
  record whose constraints have all been demoted stops being a design record) is right.
- **Worker 1 checked disk before writing, and it caught a real defect.** Rejecting part of the
  maintainer's own invited wording because `spec-009 (1076-1077)` does not say what it is cited for is
  exactly the behaviour that should be rewarded, and the claim survives independent verification.
- **The L7 widening was self-inflicted and correct.** A worker that re-derives a number it was handed,
  finds the scope is wrong, and doubles its own workload is the behaviour the re-derivation rule
  exists to produce.
- **The unit discipline held under adversarial conditions.** The build report catches its own
  `grep -c` failure on a line-wrapped phrase, names it the ninth firing, and re-derives by normalized
  substring occurrence. I re-ran that derivation independently and it is right.
- **L6's refusal is argued, not asserted**, and all three of its arguments verify on disk.
- **Scope is exact.** 41 status entries unchanged, no new file, no source/test/example file, spec-009
  unopened, `docs/review/` untouched, no `git stash` / `checkout` / `restore` / `worktree`.

### Temp test verification

- `docs/builder/temp-tests/spec-008-r2/notes.md` — a running scratch of re-derived figures, written
  incrementally during this pass. Gitignored, no behavioural content.
- Disposition: **noted, not promoted.** No `.py` was touched and no behaviour is at stake.
- Failability proofs, hot-path budget, floor verification, and `scripts/review_inspect.py` are all
  correctly recorded as not applicable to a Markdown-only pass.

### Notes for Worker 1 (spec reconciliation)

- **L8 is a one-line fix inside this cycle's existing authority** — a new anchored def in a file the
  cycle already writes. It is not escalated and needs no maintainer decision. It is the third instance
  of one recurring failure mode in this cycle (M1, prior-M2, now L8): *the pointer names the right
  target and the anchor lands on prose that does not carry the claim*. Worth a standing habit for the
  remaining rounds — when a demotion hands a claim to another document, read the destination section
  and confirm it makes that claim, not merely that the link resolves.
- **The `spec-009 (1076-1077)` staleness is confirmed and belongs in R3's deferred-work catalog**, as
  the build report proposes, alongside spec-009's `### Layer 3`. Both are spec-009-facing citations
  and the correct target for `(1076-1077)` is now known: spec-009 `### Decision 6: fail loudly`
  (`:1068-1069`). Recording the answer here saves the future spec-009 cycle the derivation.
- **`### Maintainer decision 8` is dispatched, not deferred.** `testing/relay.py`'s
  "(or build the schema)" string is R2b's; this pass correctly left the file clean.
- **Baseline-dirty count unchanged at 41.** Nothing to append to the plan's growth section. The
  `docs/review/` escalation remains open and untouched.

### Review outcome

`revision-needed` — **one new Low finding (L8)** and nothing else. Per `### Deviation 2` this routes
to **Worker 1**, not Worker 2.

Both Mediums are closed at the root, all seven prior Lows are confirmed resolved or correctly
recorded as deviations, every count in the build report re-derived correctly with its unit, the
staleness rejection is right, and the split is genuinely symmetric. L8 is a single link definition
plus a one-ref-id swap on `spec-008:173`; the other two uses of that ref-id are correct and must not
be changed with it.

## Status

> Not the artifact's status. The canonical `Status:` line is the header block above (line 5), and it
> is the only line Worker 0 reads to drive dispatch (`ARTIFACT.md:3`). This block records one pass's
> transition at the moment that pass wrote it.

`Status: revision-needed` — set by Worker 3 at this re-review. Routes to Worker 1 per
`### Deviation 2`.

## Build report (Worker 1 — apply-changes pass 2, L8 only, 2026-08-14)

Third Worker 1 pass on this artifact, dispatched at Worker 3's second `revision-needed`. Scope is
**one Low finding (L8)** and nothing else. The prior two build-report blocks and both review blocks
are left **byte-intact** (`ARTIFACT.md` `## Re-pass sections`); this pass corrects no claim made in
them, so there is no superseding-corrections section.

**Baseline for every range in this block.** Ranges are **HEAD-side lines** from
`git diff -U0 | grep '^@@'`, per the dispatch. Where a pre-pass figure is needed, it comes from a
reverse-application of this pass's two exact edits into a scratchpad copy — the same instrument the
R2 pass used — and the reconstruction **proves itself**: it measures **18,023 bytes / 243 lines**,
matching to the byte the two figures Worker 3 independently re-derived on disk in
`### Counts re-derived, with units`. A reconstruction that lands on someone else's independent
measurement is a reconstruction, not an assumption.

### Files touched

- `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` — L8 only: one ref-id swap on the
  `### The finalization trigger` sentence, and one new anchored link definition. **2 edits.**
- `docs/builder/bld-008-r2-spec_reconciliation.md` — this block, and the `Status:` line.

Not touched, and each verified clean or unchanged rather than assumed:
`docs/SPECS/spec-010-foundation-0_0_4.md` (the fix needed no heading or anchor there — the heading it
targets is pre-existing at HEAD), the rationale, `spec-001`, `spec-009`, every source/test/example
file, and everything under `docs/review/`.

### L8 — Worker 3's grep re-verified before acting, then the fix

A prescribed fix is a hypothesis (`BUILD.md` `## Review rounds`), so the finding was re-derived from
scratch on disk before any edit.

| Claim in L8 | Re-derived this pass | Verdict |
|---|---|---|
| `spec-008:173` hands the package-wide no-auto-finalize guarantee to `[spec-010][spec-010-finalization]` | `grep -n ''` line 173 is the `### The finalization trigger` body; the sentence and ref-id are exactly as quoted | **Confirmed** |
| That ref-id resolves to `#finalization-phase-finalize_django_types` = `spec-010:309` | Anchor resolver (parse headings fence-aware, slugify, match) reports `spec-010-finalization -> line 309` | **Confirmed** |
| `### Finalization phase` spans 309-406 | Next heading is `### Unresolved-target error format` at **407**; the section is **309-406** (unit: lines, endpoints inclusive) | **Confirmed** |
| Grep `do not call` / `does not call` / `auto-trigger` / `only trigger` hits **21, 65, 475, 552**, none inside 309-406 | Ran the union pattern plus `auto-finaliz` as a fifth alternative to guard against a spelling the finding missed: hits at **21, 65, 475, 552** and no others. `309 <= n <= 406` is false for all four | **Confirmed, and widened without changing the answer** |
| The guarantee's real homes are `:21` and `:65` | `:65` under `## Strawberry finalization strategy` (heading at `:58`, section **58-66**) carries **both halves in one sentence**: the three constructors named, and "the explicit consumer call is the only trigger" | **Confirmed** |

**The fix, and why this shape.** `[spec-010-finalization]` is correct for its other two uses
(`:175` the pass itself, `:183` the finalization contract), so editing the existing def would have
broken two correct citations to fix one wrong one — the def is not the defect, the *reuse* is. So:

1. New def `[spec-010-trigger]: spec-010-foundation-0_0_4.md#strawberry-finalization-strategy`, placed
   in the `<!-- docs/SPECS/ -->` group after `[spec-010-invariants]` and before `[spec-018]`
   (alphabetical position, machine-checked below).
2. `:173`'s use only, swapped to `[spec-010-trigger]`.

Post-edit occurrence check (unit: ref-id occurrences, `grep -no`): `spec-010-trigger` at **173** and
**227** (its def line); `spec-010-finalization` at **175**, **183**, and **225** (its def line). The
two protected uses are byte-untouched, and no third use of either exists.

**The destination carries the claim, checked by reading it, not by resolving it.** `:173` hands over
two things — *which* constructors do not finalize, and the *package-wide* guarantee that none does.
`spec-010:65` states both in one sentence, in that order. This is the check the whole finding is
about, so it is recorded as a reading, not as a link-resolution result.

### Anchor spot-check — every anchored def in the three cycle files, read at its destination

Not a full re-audit; the question asked of each was narrower and is the one an audit script cannot
ask: **does the section it lands on carry the claim its citing sentence makes?**

Mechanical layer first (a script that parses headings fence-aware, slugifies, and matches):
**43 anchored defs** across the three files (unit: def lines carrying a `#` fragment — spec-008 **14**,
spec-010 **12**, rationale **17**), **43 resolve to a real heading, 0 fail.**

Semantic layer, restricted to the cross-spec defs — the only ones where the failure mode can occur, a
GLOSSARY anchor being a term whose section is the term's definition by construction. **7 destinations
read** (unit: distinct anchored cross-spec defs in spec-008), covering **8 citing sentences**:

| Citing sentence | Destination | Carries the claim? |
|---|---|---|
| `:173` which constructors do not finalize + package-wide guarantee | `spec-010:58` `## Strawberry finalization strategy` | **Yes** — after this pass's fix; this was L8 |
| `:175` the pass's phases, idempotency, single-threaded window, earliest safe call point | `spec-010:309` `### Finalization phase` | **Yes, with a noted seam** — see below |
| `:180` invariants carried with enforcement teeth, and the quoted sentence | `spec-010:26` `## Invariants this slice must protect` | **Yes** — `spec-010:27` is verbatim "Any change that violates one of them is a rejected change." |
| `:183` the finalization contract | `spec-010:309` | **Yes** |
| `:185` canonical wording, message format, substring assertions | `spec-010:407` `### Unresolved-target error format` | **Yes** — and the section states its own ownership on its face |
| `:188` the acceptance inventory | `spec-010:479` `## Test fixtures and acceptance criteria` | **Yes** — its five subsections are the inventory |
| `:193` the fixture inventory | `spec-010:479` | **Yes** |
| rationale's 17 spec-008 anchors | spec-008 headings `:5` - `:197` | **Yes** — each is a `Spec:` pointer naming its own section, so citing sentence and destination are the same claim by construction |

**One seam examined and cleared, recorded rather than passed over.** `:175` names four properties;
`spec-010:309-406` carries the phases and idempotency, but the single-threaded setup window and the
earliest safe call point live at `## Idempotency and lifecycle contract` (`:471-478`). This is not an
L8: the citing sentence's subject is *the pass itself*, `:309` is the pass's own section, and the
section explicitly forwards — `spec-010:341` reads "This contract is documented in the idempotency /
lifecycle section below." A reader lands on the right subject and is handed the rest by name. L8's
reader landed on a different subject with no forwarding. Cleared, with the distinction stated so a
later pass does not re-open it.

### The failure mode this is the third instance of — and why no script can catch it

M1 (an owner pointer naming the wrong spec), the prior M2 (an anchor landing on a section claiming the
opposite), and L8 (an anchor landing on a section that is silent) are **one defect class in three
costumes**: *the reference is well-formed and the destination does not carry the claim.*

A link-definition audit is structurally blind to all three, and the reason is worth stating precisely
rather than as a caution. Such a script decides three things — does the path exist, does the anchor
slugify to a real heading, is every def used and every use defined. All three were **green on L8
before this pass and green after**; the only thing that changed is which section a human reads. The
script's entire input is the *source* file plus the destination's *heading list*; the claim lives in
the destination's *body*, which the script never opens. So the check is not merely missing, it is
outside the instrument's domain — adding a rule would not help, because there is no rule over headings
that decides whether a paragraph asserts a proposition.

The transferable form: **a resolving link is evidence about the document graph, never about the
claim.** Whenever a demotion hands a claim to another document — which is this entire cycle's
mechanism, so the exposure is systematic rather than incidental — the acceptance test is to read the
destination section and confirm it makes *that* claim. Cheap here, and it is the only place it is
cheap: after the cycle closes, the reader who finds it has neither document's context.

This is also a **unit trap in link form**, the same shape as the nine prose firings: the quantity of
interest is *claims carried*, and the tool measures *anchors resolved*. Two different units, and the
one that is easy to measure is not the one the finding is about.

### Spec changes made (Worker 1 only)

Ranges are HEAD-side lines from `git diff -U0`. Both edits fall **inside hunks the prior passes had
already opened**, so the cumulative HEAD-side hunk count for spec-008 is **unchanged at 51** (unit:
`@@` lines) — verified by counting hunks against the reverse-applied pre-pass copy (51) and against
disk (51). A pass that changed the hunk count would have restructured something outside its finding.

| Spec / HEAD lines | Enclosing hunk | Change | Trigger | Reason |
|---|---|---|---|---|
| `spec-008` HEAD **343-344** | `@@ -343,2 +172,2 @@` | `:173`'s ref-id `[spec-010-finalization]` -> `[spec-010-trigger]` | L8 | The cited section is silent on the package-wide no-auto-finalize guarantee; `## Strawberry finalization strategy` states it in one sentence |
| `spec-008` HEAD **589** (insertion) | `@@ -589,0 +219,12 @@` | New def line `[spec-010-trigger]: spec-010-foundation-0_0_4.md#strawberry-finalization-strategy` at new-file `:227` | L8 | A new ref-id was required because `[spec-010-finalization]`'s two other uses are correct for `:309` and must not move |

Negative rows, so a reader can tell a non-edit from an oversight:

- `spec-010` — **NOT changed.** The fix needed no heading and no anchor there: `## Strawberry
  finalization strategy` exists at HEAD and its slug already resolves. Cumulative HEAD-side hunks
  remain **10**, unchanged from the prior pass's count.
- rationale — **NOT changed.** No finding reached it; its 17 anchors were spot-checked read-only.
- `spec-008` `:175` and `:183` — **NOT changed**, byte-identical, deliberately: L8 names them correct.

Status-line re-verification (every Worker 1 spawn): spec-008 lines 1-4 re-read. The header states the
record's role and its `0.0.4` target and names spec-010 as the shipping contract; nothing in this pass
falsifies any of it. **No status-line edit needed.**

### Checks re-run, with results quoted

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-…md` ->
  `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0.**
- Same script on `docs/SPECS/spec-010-foundation-0_0_4.md` ->
  `OK: 12 terms - all have glossary entries and at least one spec link.` **exit 0.**
- `uv run python scripts/check_trailing_commas.py --check` over spec-008, the rationale, spec-010, and
  this artifact -> **exit 0.**
- Rule-27 occurrence sweep, spec and rationale. Unit is **regex occurrences**
  (`grep -oE … | wc -l`), never matching lines — a `path:NN` wrapped across a newline is invisible to
  a line count. Narrow `\.(py|md):[0-9]+` -> **0 / 0**. Widened `\.[a-z]+:[0-9]+` -> **0 / 0.**
- Never run: `pytest` (with or without `--cov*`), `git stash`, `git checkout`, `git restore`,
  `git worktree`, `git commit`, any branch operation.

### Counts, with units and derivation commands

Every figure re-derived on disk this pass; none carried from the dispatch prompt or the review block.

| Quantity | Unit | Command | spec-008 before | spec-008 after | delta |
|---|---|---|---|---|---|
| Size | bytes | `wc -c` | **18,023** | **18,100** | **+77** |
| Length | newline-terminated lines | `wc -l` | **243** | **244** | **+1** |
| Link definitions | def lines matching `^\[…\]: ` | `grep -cE` | **21** | **22** | **+1** |
| Anchored defs | def lines carrying `#` | script | **13** | **14** | **+1** |
| Canonical group headers | `<!-- … -->` lines minus the `<!-- LINK DEFINITIONS -->` delimiter | script | **10** | **10** | 0 |
| Cumulative HEAD-side hunks | `@@` lines | `git diff -U0 \| grep -c '^@@'` | **51** | **51** | 0 |

**Unit note on the header count, because a naive command gets it wrong.**
`grep -cE '^<!-- .* -->$'` returns **11**, not 10, on every file in this cycle: it also matches the
`<!-- LINK DEFINITIONS -->` delimiter, which is not a group header. The canonical count is 10 and the
correct derivation parses the block and compares the group list against `LINK_DEF_CATEGORIES`. Both
were run; the parse is the one quoted.

Unchanged and re-measured to prove it: rationale **70,620 bytes / 1,042 lines / 29 defs**; spec-010
**61,005 bytes / 596 lines / 12 defs**. All three match Worker 3's re-derived figures.

The `+77` bytes decompose exactly, which is the arithmetic self-proof: the def line is
`len("[spec-010-trigger]: spec-010-foundation-0_0_4.md#strawberry-finalization-strategy\n")` = **82**;
the ref-id swap is `len("trigger") - len("finalization")` = **-5**. `82 - 5 = +77`. Terminates at the
observed file.

### Link-definition audit — all three files, machine-checked

One script, run over spec-008, spec-010, and the rationale, reporting five things:

- **10 canonical group headers, in `LINK_DEF_CATEGORIES` order** — `OK (10 groups)` for all three.
- **Alphabetical within every group** — compared each group's ref-id list against `sorted()`; **no
  mismatched group in any of the three files.** `[spec-010-trigger]` sorts after `spec-010-invariants`
  and before `spec-018`, which is where it was placed.
- **Paths disk-verified** — every def's path resolved from its own file's directory; **0 missing.**
- **No used-undefined, no defined-unused** — `none` / `none` for all three files. The new def is used
  (at `:173`), so it did not land as a defined-unused.
- **Every anchored def resolves to a real heading** — **43 / 43**, `0` failures, fence-aware so a
  `#`-prefixed line inside a code fence cannot be mistaken for a heading.

### Failability proofs / hot-path budget / floor verification / `review_inspect.py`

Not applicable: Markdown-only pass, no boundary, no runtime code, no behavior. Recorded rather than
omitted.

### Scope discipline

- `git status --short` -> **41 entries** (unit: status lines). Unchanged; this pass created no file
  and moved no baseline-dirty file's state.
- `git status --short` on `spec-009` and on the three R2b-owned files
  (`types/relations.py`, `types/base.py`, `testing/relay.py`) -> **empty**. Untouched, as
  `### Maintainer decision 6` and `### Maintainer decision 8` require.
- `spec-001` cumulative HEAD-side hunks still **1**; `spec-010` still **10**. Neither opened.
- `docs/review/` untouched — the maintainer escalation stays open.

### Handed to R3

- **`spec-009 (1076-1077)`** remains stale and remains out of scope, with its answer now recorded by
  Worker 3: the correct target is spec-009 `### Decision 6: fail loudly` (`:1068-1069`). Deferred-work
  catalog, alongside spec-009's `### Layer 3`.
- **Nothing else.** L8 was the only open finding and it is closed at the root.

## Status

> Not the artifact's status. The canonical `Status:` line is the header block above (line 5), and it
> is the only line Worker 0 reads to drive dispatch (`ARTIFACT.md:3`). This block records one pass's
> transition at the moment that pass wrote it.

`Status: planned` — set by Worker 1 at the L8 apply-changes pass. Routes to Worker 3 for re-review per
`### Deviation 2`.

## Review (Worker 3, pass 3)

Narrow re-review of the L8-only apply-changes pass. Fresh subagent, no in-context memory of pass 2.
Settled results from the prior passes (the clean-contract whole-spec read, the reconstruction
methodology, D10/D13 un-churned, decision 7's symmetry, the `spec-009` staleness claim, L6's no-edit,
and fixes M1/M2/L1-L7) were taken as standing per the dispatch and were **not** redone. Everything
below was re-derived on disk this pass; no number was copied from the build report or the dispatch.

### Verdict 1 — the new destination CARRIES the claim, and is a better host than "adequate"

The citing sentence, read at `spec-008:173`:

> Which constructors do not finalize, and the package-wide guarantee that none of them does, are
> [`spec-010`][spec-010-trigger]'s.

Two claims are handed over: (a) *which* constructors, (b) the *package-wide* negative. The new def
resolves to `## Strawberry finalization strategy`, heading at `spec-010:58`, section **58-66** (unit:
lines, endpoints inclusive; next heading `### Manual annotation contract for relation fields (0.0.4)`
at **67**). Read, not resolved — `spec-010:65`:

> No shipped helper auto-triggers finalization: `DjangoSchema`, `DjangoConnectionField`, and
> `DjangoNodeField` do not call `finalize_django_types()`; the explicit consumer call is the only
> trigger.

Both halves, in one sentence, **in the same order the citing sentence asks for them**: the three
constructors named, then the universal ("no shipped helper", "the only trigger"). (a) and (b) both
land. This is a genuine fix at the root, not a relabelled pointer.

**Corroboration the finding did not claim.** The same bullet continues "The auto-trigger direction in
`spec-009-rich_schema_architecture-0_0_4.md (670-687)` was not adopted." `spec-008:173`'s immediately
preceding clause is "The alternative — finalizing implicitly, inside the rich-schema field and schema
constructors — was weighed and not adopted." The destination therefore carries the *rejection* the
citing sentence records as well as the two claims it hands over. The section is not merely sufficient;
it is the correct home for the whole sentence.

**Independent negative check, widened.** Ran the union pattern `do not call|does not call|
auto-trigger|only trigger|auto-finaliz` over spec-010: hits at **21, 65, 475, 552** and no others.
`309 <= n <= 406` is false for all four, so the *old* destination (`### Finalization phase`, 309-406,
next heading at 407) is confirmed silent — L8 was a real defect and the retarget was necessary, not
cosmetic.

### Verdict 2 — the shared ref-id was left intact

- The def is byte-identical to the string pass 2 quoted:
  `spec-008:225` `[spec-010-finalization]: spec-010-foundation-0_0_4.md#finalization-phase-finalize_django_types`.
  Not edited.
- Occurrence sweep (unit: ref-id occurrences, `grep -n`): `spec-010-finalization` at **175**, **183**,
  **225** (its def). `spec-010-trigger` at **173**, **227** (its def). `:173` no longer uses the shared
  id; no third use of either exists; the two protected uses are where they were.
- Both protected uses re-checked at their destination rather than assumed correct:
  - `:175` ("the pass itself — its phases, its idempotency, its single-threaded setup window, and its
    earliest safe call point") — see Verdict 3's seam judgement.
  - `:183` ("the finalization contract is [`spec-010`][spec-010-finalization]'s") — `309-406` is the
    finalization contract: the three-phase lifecycle, the failure-atomicity boundary, the pseudocode.
    Correct.

### Verdict 3 — auditing Worker 1's anchor spot-check

**The semantic layer is real, and is in fact complete — but two of its counts are wrong.**

*Completeness, derived independently.* I enumerated every anchored cross-spec def in spec-008 and
every body use of each, rather than reading the report's table:

| Def | Body uses | Distinct destination |
|---|---|---|
| `spec-010-trigger` | `:173` | `spec-010:58` |
| `spec-010-finalization` | `:175`, `:183` | `spec-010:309` |
| `spec-010-invariants` | `:180` | `spec-010:26` |
| `spec-010-error` | `:185` | `spec-010:407` |
| `spec-010-acceptance` | `:188`, `:193` | `spec-010:479` |

**5 anchored cross-spec defs, 7 citing sentences, 5 distinct destination sections.** The report's table
carries exactly those 7 spec-008 rows plus a rationale aggregate row. **No citing sentence went
unread**, which is the question that matters. Four of the seven were re-read at their destinations
independently this pass, and all four carry their claim:

- `:180` — `spec-010:27` is verbatim "Any change that violates one of them is a rejected change.", and
  `26-34` is the invariant list with its acceptance framing. Carries it.
- `:185` — `spec-010:408` states its own half explicitly ("this spec owns the canonical wording, the
  message format, and the substring-test contract that pin it") and names spec-008's. Carries it, and
  reciprocally.
- `:188` / `:193` — `spec-010:479` `## Test fixtures and acceptance criteria`; its six `###`
  subsections (`:480`, `:485`, `:496`, `:506`, `:511`, `:517`) are the inventory. Carries it.

*The count defect.* The mechanical layer's denominator is wrong, and so is the counts table's row:

| Claim | Re-derived (unit: def lines matching `^\[…\]: [^ ]*#`) | Verdict |
|---|---|---|
| spec-008 anchored defs = **14** | **15** — 10 `GLOSSARY.md#…` + 5 `spec-010-…#…` | **Wrong, +1** |
| spec-010 = **12** | **12** | Correct |
| rationale = **17** | **17** | Correct |
| total = **43**, all resolving | **44**, **44 resolve, 0 fail** | **Wrong, +1**; the *resolution* verdict stands |
| `### Counts…` row "Anchored defs 13 -> 14" | should read **14 -> 15** | **Wrong, +1 both sides** |

The delta (+1) is correct in both places; only the absolute is off. Filed as **L9** below.

*"7 destinations read (unit: distinct anchored cross-spec defs in spec-008), covering 8 citing
sentences"* also misdescribes its own unit: **7 is the number of citing sentences** and **5 is the
number of distinct anchored cross-spec defs / distinct destinations**; the "8th citing sentence" is the
rationale aggregate row, not a spec-008 sentence. Filed as part of L9. The work behind the label is
right; the label is not.

**The `:175` seam — clearing it was RIGHT. It is not a fourth instance of the class.** Verified
property by property against the section it cites (`309-406`):

| Property claimed at `:175` | Where it actually lives | In `309-406`? |
|---|---|---|
| the pass's phases | `spec-010:312` "the three phases below" + the pseudocode | **Yes** |
| its idempotency | `spec-010:344` `return  # idempotent`, and `:341` names the contract | **Yes, with an explicit forward** |
| its single-threaded setup window | `## Idempotency and lifecycle contract` `:475` | No — forwarded |
| its earliest safe call point | **`spec-010:60`**, a bullet of `## Strawberry finalization strategy` | No — see below |

The distinction from L8 is structural, not a matter of degree, and it holds:

- **Subject match.** `:175`'s subject is *the pass itself*; `:309` is the pass's own section. L8's
  reader landed on the pass's section while being handed a claim about *constructors that are not the
  pass*.
- **Explicit forwarding.** `spec-010:341`, inside the cited section, reads "This contract is documented
  in the idempotency / lifecycle section below." The reader is handed the remainder **by name**. L8's
  destination forwarded nothing; it was simply silent.
- **Nothing false.** No durable sentence asserts the missing properties are at `:309`.

One correction to the build report's evidence, which does not disturb the verdict: it says the two
absent properties "live at `spec-010:471-478`". Only one does. `471-478` carries the single-threaded
setup window (`:475`) but **not** the earliest safe call point — that is `spec-010:60`, a bullet of
`## Strawberry finalization strategy`, i.e. the section `:173` now points at one sentence earlier. That
is a mildly *better* fact than the one recorded: a reader of the paragraph reaches both halves through
the paragraph's own two links. Filed as part of L9.

### High:

None.

### Medium:

None. L8 is closed at the root: the destination carries both claims, the shared ref-id's two correct
uses are byte-untouched, and no new ref-id collision was created.

### Low:

#### L9 — three artifact-only count/location inaccuracies in the anchor spot-check

`docs/builder/bld-008-r2-spec_reconciliation.md`, `### Anchor spot-check` (`:1614-1645`) and
`### Counts, with units and derivation commands` (`:1719`):

1. `:1620-1621` — "**43 anchored defs** … spec-008 **14**" is **44 / 15**. Same unit, miscounted by one
   (the ten `GLOSSARY.md#…` defs plus five `spec-010-…#…` defs = 15).
2. `:1719` — "Anchored defs … **13** -> **14**" should be **14 -> 15**. The delta `+1` is right.
3. `:1625` — "**7 destinations read** (unit: distinct anchored cross-spec defs in spec-008), covering
   **8 citing sentences**": the file has **5** distinct anchored cross-spec defs resolving to **5**
   distinct destinations, and **7** spec-008 citing sentences; the eighth row is the rationale
   aggregate.
4. `:1640` — "the single-threaded setup window and the earliest safe call point live at
   `spec-010:471-478`": only the former does. The earliest safe call point is `spec-010:60`.

**Why Low, and why it does not gate acceptance.** No durable file carries any of these numbers — they
exist only in this per-cycle scratchpad, which `START.md` "Temp artifact conventions" closes with the
cycle. The three verdicts they support are all independently correct: **44/44 anchors resolve** (0
failures, re-derived), the semantic layer read **every** anchored cross-spec citing sentence in
spec-008, and the `:175` clearing is right. Contrast pass 1's M1, which was rejected because five wrong
counts sat in **durable prose** — that distinction is the whole severity call here.

**Resolution: corrected in this section, no further pass required.** The corrected values are stated
above with their derivation commands and units, which is the same superseding-correction mechanism this
artifact already uses (`### Superseding corrections to the prior build report`). Reopening a build pass
to restate four scratchpad numbers would churn an artifact that closes with the cycle.

This is the **tenth firing** of the counting trap in this cycle, and its shape is worth naming because
it is *not* the usual one: nothing here is a line-oriented tool applied to a non-line quantity. The
unit was named correctly ("def lines carrying a `#` fragment") and then the count was simply taken
wrong — and it happened inside the pass whose own closing paragraph diagnoses the trap "in link form".
Naming a unit is not measuring it. Re-run the command.

### Standing checks — every one re-derived, none trusted

| Check | Command / unit | Result |
|---|---|---|
| Glossary, spec-008 | `uv run python scripts/check_spec_glossary.py --spec …spec-008…` | `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0** |
| Glossary, spec-010 | same script | `OK: 12 terms …` **exit 0** |
| Trailing commas / scaffold | `check_trailing_commas.py --check` over spec-008, spec-010, the rationale, this artifact | **exit 0** |
| Rule 27, spec-008 | regex **occurrences**, `grep -oE … \| wc -l` | narrow `\.(py\|md):[0-9]+` **0**; widened `\.[a-z]+:[0-9]+` **0** |
| Rule 27, rationale | same | narrow **0**; widened **0** |

**The `+77` decomposition — verified, and it terminates.**
`len("[spec-010-trigger]: spec-010-foundation-0_0_4.md#strawberry-finalization-strategy\n")` = **82**
(computed, not counted by eye); `len("trigger") - len("finalization")` = **-5**; `82 - 5 = 77`. On
disk: `wc -c` = **18,100**, and `18,100 - 77 = 18,023` — the figure pass 2 independently measured
before this pass existed. `wc -l` = **244** = `243 + 1`. Def lines = **22** = `21 + 1`. Every "before"
figure is forced by an on-disk "after" plus a decomposition that closes exactly.

**Link definitions — machine-audited, all three files** (own script: parse the block, check the ten
`LINK_DEF_CATEGORIES` headers and their order, compare each group's ref-id list against `sorted()`,
resolve every path from the citing file's own directory, slugify every target's headings fence-aware
with duplicate `-1` suffixes, diff used-vs-defined):

| | spec-008 | spec-010 | rationale |
|---|---|---|---|
| 10 canonical headers, in order | yes | yes | yes |
| alphabetical within every group | yes | yes | yes |
| def lines | **22** | **12** | **29** |
| anchored defs | **15** | **12** | **17** |
| paths missing on disk | **0** | **0** | **0** |
| anchored defs failing to resolve | **0** | **0** | **0** |
| used-undefined / defined-unused | **0 / 0** | **0 / 0** | **0 / 0** |
| inline `](#…)` anchors in body | **0** | **0** | **0** |

`[spec-010-trigger]` sorts after `spec-010-invariants` and before `spec-018`, which is `spec-008:227` —
placed correctly, and used at `:173`, so it did not land as a defined-unused.

**The header-grep caution is real and I hit it in the reverse direction.** `grep -cE '^<!-- .* -->$'`
on spec-008 returns **11**; the parse returns **10** groups plus the `<!-- LINK DEFINITIONS -->`
delimiter. Confirmed, and the parse is what the table above quotes. My own slugifier independently
produced two false anchor failures until I stopped stripping `_` as emphasis
(`finalization-phase-finalize_django_types`, `GLOSSARY.md#finalize_django_types`) — a reminder that a
"0 failures" result is only as good as the slug function, and a *non-zero* result is the cheap one to
misread.

**Scope — re-derived mechanically.**

- `git status --short` -> **41 entries** (unit: status lines). Unchanged.
- `git status --short` on `spec-009`, `django_strawberry_framework/types/relations.py`,
  `types/base.py`, `testing/relay.py` -> **empty**. All four clean.
- Cumulative HEAD-side hunks (unit: `@@` lines, `git diff -U0 | grep -c '^@@'`): spec-008 **51**,
  spec-010 **10**, spec-001 **1**. All three match the claim; both edits fell inside already-opened
  hunks.
- `spec-010` and the rationale re-measured to prove they were not touched: **61,005 bytes / 596 lines /
  12 defs** and **70,620 bytes / 1,042 lines / 29 defs** — byte-identical to pass 2's figures.
- `docs/review/` -> **8 entries**, untouched. The maintainer escalation stays open.
- No `git stash` / `checkout` / `restore` / `worktree`; no `pytest`; no commit; no branch operation.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **0 lines**. `__all__` and the re-export list
unchanged. No `.py` file is in this pass's diff.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md` (`git status --short CHANGELOG.md` is empty).

### Documentation / release sanity

- No version string written; no card ID written; no script-rendered doc (`TREE.md`, `GLOSSARY.md`,
  `KANBAN.md`) regenerated or needing regeneration.
- `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` remain baseline-dirty
  from other sessions and untouched by this pass.

### DRY findings

- **None.** A two-edit pass that adds one link definition and swaps one ref-id creates no abstraction,
  no duplicated literal, and no parallel data flow. The new ref-id has one reader (`:173`) — a live
  reader, not an indirection layer.
- **No existence challenge.** The obvious one — "could `:173` reuse `[spec-010]`, the unanchored
  whole-file def, instead of a second anchored id?" — was considered and answers itself: an unanchored
  link drops the reader at the top of a 596-line spec, which is a weaker version of the exact defect
  L8 named. Two ref-ids to one document with different anchors is the convention working, not
  duplication.

### Observation for R3's deferred-work catalog — rule 27 in spec-010

**Out of this cycle's writable scope** (spec-010 is writable only at the sites the maintainer decisions
name), recorded here, not fixed, and the diff was not widened by it.

The dispatch named one instance: `spec-010:63`, inside `#"the foundation slice's registry is
intentionally lockless"`, carries a raw `registry.py:28-33`. Confirmed on disk — and it sits **inside
`## Strawberry finalization strategy` (58-66)**, the section this pass's fix now targets. It does not
touch the claim `:173` hands over; the bullet carrying the guarantee is `:65` and is clean.

**Sweep of the whole file.** Unit is **regex occurrences** (`grep -oE … | wc -l`), never matching
lines — several lines carry more than one:

| Pattern | Occurrences | Distinct lines |
|---|---|---|
| narrow `\.(py\|md):[0-9]+` | **42** | 30 |
| widened `\.[a-z]+:[0-9]+` | **42** | 30 |

Both patterns give the same answer because every reference is a `.py` path. Split by target, since the
remediation differs:

- **20 occurrences on 15 lines** name **in-repo** paths (`django_strawberry_framework/types/base.py:80`,
  `registry.py:93`, `registry.py:154`, `types/converters.py:211`, `types/resolvers.py:168`,
  `walker.py:64`, `registry.py:28-33` twice, …), at `:63`, `:79`, `:299`, `:383`, `:448-452`,
  `:455-456`, `:458`, `:468`, `:475`, `:476`. These are rule-27 violations in the plain sense.
- **22 occurrences on 15 lines** name **pinned third-party prior-art snapshots**
  (`strawberry_django/…`, `graphene_django/…`, `graphene/…`).

**The catalog entry is larger than a line sweep, and R3 should be told so.** `spec-010:554`
`## Note on source line references` is a standing section that **institutionalizes** the practice —
"reviewers should treat in-repo line references as soft hints and verify against the symbol names",
plus an instruction to refresh the in-repo lines before implementation. Closing this means converting
~20 in-repo references to `path::QualifiedName` form **and** retiring or rewriting that section; it is
not a find-and-replace, and it needs the maintainer decision that authorizes touching spec-010 outside
the named sites. Two of the in-repo refs (`:299`, `:383`) also sit inside pseudocode comment lines.

### What looks solid

- **The fix is the smallest correct one.** The defect was the *reuse*, not the def, and the pass
  diagnosed that in one sentence and acted on it: a new ref-id rather than an edit to a def with two
  correct readers. Editing the def would have broken two citations to fix one.
- **The finding was re-derived before being acted on.** A prescribed fix is a hypothesis, and this pass
  treated it as one — re-running the negative grep with `auto-finaliz` added as a fifth alternative
  guards against exactly the spelling a finding might have missed. The answer did not change, which is
  what a widened check is supposed to produce most of the time.
- **The destination check was recorded as a reading, not as a link-resolution result.** That is the
  distinction the whole finding was about, and the report keeps it explicit.
- **The `:175` seam was surfaced rather than buried.** A pass that finds a near-instance of the class it
  is fixing, examines it, clears it, and writes down the distinguishing test so a later pass does not
  re-open it is doing the expensive half of the job. The distinction it drew (subject match plus
  explicit forwarding) survives independent checking.
- **The failure-mode analysis at `:1647-1670` is correct and transferable.** "A resolving link is
  evidence about the document graph, never about the claim" is the right generalisation, and the
  observation that the check is *outside* a link auditor's domain — the script never opens the
  destination's body — is precisely why no rule addition would have caught it.
- **Scope is exact.** Two edits, one file, both inside already-open hunks, 41 status entries unchanged,
  spec-010 and the rationale byte-identical, `spec-009` and the three R2b files clean, `docs/review/`
  untouched.

### Temp test verification

- `/…/scratchpad/audit.py` — a link-definition and anchor-resolution auditor written this pass
  (fence-aware heading parse, GitHub slugification with duplicate-suffix handling, group-order and
  alphabetical checks, path resolution, used-vs-defined diff). Scratchpad only, outside the repo, not
  under `docs/builder/temp-tests/`; nothing to promote.
- Disposition: **noted, not promoted.** No `.py` in the repo was touched and no behaviour is at stake.
- Failability proofs, hot-path budget, floor verification, and `scripts/review_inspect.py`: **not
  applicable** to a Markdown-only, boundary-free pass. Recorded rather than omitted.

### Notes for Worker 1 (spec reconciliation)

- **L9 is closed by this section** and needs no further build pass. The corrected figures — spec-008
  **15** anchored defs, **44** across the three files, **5** distinct cross-spec defs / **7** citing
  sentences, and the earliest safe call point at `spec-010:60` — are the ones a later reader should
  use.
- **Deferred-work catalog, two entries** for R3:
  1. `spec-009 (1076-1077)` remains stale; the correct target is spec-009 `### Decision 6: fail loudly`
     (`:1068-1069`), already derived by pass 2. Cited from `spec-010:408`. Alongside spec-009's
     `### Layer 3`.
  2. **New:** spec-010's raw `path:NN` references — **42 occurrences on 30 lines**, of which **20
     occurrences on 15 lines** are in-repo — plus the `## Note on source line references` section
     (`:554`) that institutionalizes them. Needs a maintainer decision authorizing spec-010 edits
     outside the sites decisions 1-8 name.
- **The recurring failure mode now has a fourth data point and a stated non-instance.** M1, prior-M2,
  L8 are instances; `:175` is the near-miss that is *not* one, and the two tests that separate them
  (subject match; explicit forwarding by name) are the ones to apply in the remaining rounds.
- **Baseline-dirty count unchanged at 41.** Nothing to append to the plan's growth section.

### Review outcome

`review-accepted`. L8 is closed at the root: the retargeted anchor's destination carries **both** halves
of the claim in a single sentence in the citing order, the shared ref-id's two correct uses are
byte-untouched, the new def is alphabetically placed and used, and the whole link graph re-audits clean
at **44/44** anchors across the three files. Every standing check was re-derived and passes; the `+77`
decomposition closes exactly against the on-disk file; scope is unchanged at 41 status entries with
spec-009, spec-001, spec-010, the rationale, the three R2b source files, and `docs/review/` all
verified untouched.

The one new finding (**L9**) is four count/location inaccuracies confined to this per-cycle artifact,
with no durable file affected and none of them changing a verdict; they are corrected above under the
artifact's own superseding-correction convention. The spec-010 rule-27 observation is recorded for
R3's deferred-work catalog and was deliberately not fixed.

## Status

> Not the artifact's status. The canonical `Status:` line is the header block above (line 5), and it
> is the only line Worker 0 reads to drive dispatch (`ARTIFACT.md:3`). This block records one pass's
> transition at the moment that pass wrote it.

`Status: review-accepted` — set by Worker 3 at this third-pass re-review.

---

## Final verification (Worker 1, 2026-08-14)

Fresh spawn, no in-context memory of R1 or of the three R2 passes. Every number below was re-derived
on disk this pass; nothing was carried from the dispatch prompt, the build report, or the review
blocks. Prior blocks are byte-intact; corrections live here.

### The `### Spec changes made` audit — the hunk count is the audit, and it closes

**Cumulative HEAD-side hunk counts, re-derived** (unit: `@@` lines,
`git diff -U0 -- <path> | grep -c '^@@'`): spec-008 **51**, spec-010 **10**, spec-001 **1**. All three
match every claim in the artifact.

**The R1-baseline reconstruction is proven, by a method independent of the one the prior passes used.**
They reverse-applied replacement strings and matched R1's recorded byte/line counts. This pass instead
**simulated the quoted 40-hunk list as a diff script** and checked it against disk arithmetic — no
reconstruction file, no reverse-apply:

- Walking the 40 quoted hunks with a running offset (git's convention that a `-a,0` pure-insert hunk's
  new start is `a + offset + 1`, the trap that makes a naive gap check report a false ±1) produced
  **zero position mismatches** and a net delta of **-88** lines.
- `327 - 88 = 239` = the R2 pass-1 output length. Pass 2 added **+4** lines (a 2-line paragraph
  insertion at `184,0 -> +185,2` and two def lines); pass 3 added **+1** (one def line).
  `239 + 4 + 1 = 244`.
- On disk: `wc -l` = **244**. And independently of the whole chain, the cumulative HEAD diff's net
  delta is **-359** against a HEAD of **603** lines (`git show HEAD:… | wc -l`): `603 - 359 = 244`.

Two derivations that never touch each other land on the same on-disk number. The 327-line R1 baseline
is therefore forced, not asserted.

**The prose grouping was audited for a phantom, the failure R1's own list had.** Mapping each of the
15 reason bullets onto the quoted hunks in file order: 4+4+4+4+4+1+1+2+3+2+1+3+3+2+2 = **40**. Every
hunk is claimed by exactly one bullet; no bullet claims a hunk that is not in the list. **No phantom,
no omission.**

**Per-file verification of the two sibling lists, read against the actual diff:**

| File | Claimed | Verified on disk |
|---|---|---|
| `spec-001` | 1 hunk, HEAD 66, Edit 1 | `@@ -66 +66 @@`, and the changed line is exactly `spec-008-…md owns that pass` -> `spec-010-foundation-0_0_4.md owns that pass`. **Exact.** |
| `spec-010` | 10 hunks, 8 reason bullets | `@@` starts at HEAD **21, 48, 65, 310, 322, 325, 332, 393, 405, 470** = 10. The bullet "HEAD 322, 325, 332-339" covers 3; the other 7 bullets cover 1 each. 7 + 3 = **10.** |

**Every entry in all three `### Spec changes made` blocks was treated as a claim and checked.** No
entry is unsupported by a hunk, and no hunk is unclaimed by an entry. **Audit result: clean.**

### The contract, confirmed

- **Clean current contract.** Spot-checked by reading spec-008 end to end plus a mechanical sweep:
  `grep -nEi 'was later|amendment|previously stated|has since been|correction|superseded|no longer
  accurate'` -> **0 matches**. No chronology, no amendment block. Line 3 is the required one-line
  rationale pointer; the record voice ("this record", "shipped whole", "was weighed and not adopted")
  states what the design decided, which is contract, not a history of the document's revisions.
- **Maintainer decision 7 — the error-requirement split, stated in both specs.** spec-008 `:185`:
  "any implementation must name the source model, the source field, and the target model when it
  raises. That is a design constraint, not a message — the canonical wording, the message format, and
  the substring assertions that pin them are `spec-010`'s … The split is deliberate and is stated in
  both documents." spec-010 `:408`: "Those citations are the **source of the requirement** and nothing
  more … this spec owns the canonical wording, the message format, and the substring-test contract …
  The split is deliberate and is stated in both documents." **Symmetric, one owner per half,
  reciprocal.** The rationale's `### The shape that shipped …` entry carries the third-telling
  demotion above its byte-intact verbatim quotation.
- **Scope limits on decisions 3, 5, 6.** D3 authorized exactly two spec-010 citations: both landed
  (`:48` `(400-414)` -> `#"### The finalization trigger"`; `:405` `(397-505)` ->
  `#"### The shape that shipped"`), and the `spec-009 (1076-1077)` range in the same sentence is
  **byte-untouched**, as D3 and D6 require. D5's amendment landed at exactly the rerun-recovery and
  phase-insertion sites (`:310`, `:322`-`:339`, `:393`-`:396`, `:470`) and nowhere else. D6:
  `git status --short docs/SPECS/spec-009-…md` -> **empty**.
- **Exactly five authorized sibling-spec edit sites, no sixth.** Partition Edit 1 = spec-001 `:66`;
  Edit 2 = spec-010 `:21`; Edit 3 = spec-010 `:65`; D3's two citations = spec-010 `:48` and `:405`.
  Five sites, five hunks. The remaining six spec-010 hunks are D5's (five) and D7's (one, inside the
  `:405` hunk). Every hunk in both siblings maps to a named decision; **none is unauthorized.**
- **No source, test, or example file in this cycle's diff.** `git status --short` on
  `types/relations.py`, `types/base.py`, `testing/relay.py` -> **empty**, all three. R2b's carve-out is
  undispatched and the files are clean. `git diff --name-only` carries no `.py` this cycle owns.
- **All ten glossary anchors survive.** spec-008 carries **10** `../GLOSSARY.md#…` def lines and
  `check_spec_glossary.py` reports `OK: 10 terms`. Both counts agree.
- **Rationale entries — re-derived by parsing, not grepping.** Parsing the file into fence-aware `###`
  blocks yields **22** entries and **0** entries lacking a `Spec:` line. Twenty carry a reference-style
  anchored link to a spec heading; two carry the accepted explicit `Spec: no single decision — this
  entry is keyed to the reconciliation pass rather than to a spec` form, and five of the twenty carry
  `Spec: none — the heading was removed`. `grep -c '^Spec: '` is the wrong instrument here (it returns
  17 against 22 entries, because several `Spec:` lines are indented or wrapped) — the parse is what is
  quoted.
- **Durable numeric claims re-derived.** spec-008 `:43` "five questions at once" -> 5 bullets
  (`:45`-`:49`). `:144` "Six of the eight … two are Beta cards" -> 8 bullets (`:135`-`:142`), 6 shipped
  + 2 Beta. `:130` "thirteen criteria" -> the rationale's verbatim list has **13** slash-separated
  items, and its "Six of the thirteen are prohibitions" decomposes as 3 negative + 3 positive = **6**.
  `:185` "Those three elements" -> source model, source field, target model. **All correct.**

### Disposition of L9 — the severity distinction is right, and nothing leaked

**Confirmed, with the counts re-derived independently.** My own link auditor reports spec-008 **15**
anchored defs (not 14) and **15 + 12 + 17 = 44** across spec-008 / spec-010 / the rationale (not 43) —
matching Worker 3's corrections exactly, and derived from a script written this pass without reference
to theirs.

**The severity call holds, and it is a mechanical result rather than a judgement.** Sweeping all four
durable files for every L9 figure — `43`, `44`, `13 -> 14`, `7 destinations`, `471-478`, and any
statement of an anchor or def count at all — returns **0 matches in every durable file**. The only
`anchored`/`link definition`/`def lines` strings anywhere in the durable set are the
`<!-- LINK DEFINITIONS -->` delimiters themselves. **No wrong count leaked out of the scratchpad.**
That is precisely the distinction from pass 1's M1, whose five wrong counts sat in spec prose a
downstream reader would inherit; `START.md` "Temp artifact conventions" closes this file with the
cycle. **L9 is correctly Low, correctly closed by its own superseding correction, and correctly does
not gate acceptance.**

**L10 — NEW, same class as L9, artifact-only, also non-gating.** Pass 3's status-line note
(`### Spec changes made`, third block) says "spec-008 lines 1-4 re-read. The header states the record's
role and its `0.0.4` target and names spec-010 as the shipping contract." On disk, lines 1-4 are the
title, a blank, the rationale pointer, and a blank: the `0.0.4` target lives in the filename and
spec-010 is named at `:161`, not in the header. **The conclusion is right** — this archived spec
carries no status line for the build to falsify, so "No status-line edit needed" stands — only the
description of what was read is loose. No durable file is affected. Recorded, not fixed, for the same
reason L9 was not: reopening a build pass to restate a scratchpad sentence churns a file that closes
with the cycle. Status-line re-verification for **this** spawn: spec-008 has no status/header line;
nothing to edit.

### Disposition of the spec-010 rule-27 debt — carried to R3 intact, deliberately not fixed

**Re-derived, unit stated.** Occurrences, not lines (`grep -oE … | wc -l`):

| Pattern | Occurrences | Distinct lines |
|---|---|---|
| narrow `\.(py\|md):[0-9]+` | **42** | **30** |
| widened `\.[a-z]+:[0-9]+` | **42** | **30** |

Both patterns agree because every reference is a `.py` path. The split Worker 3 recorded — **20
occurrences on 15 lines** in-repo, **22 on 15** pinned third-party prior art — is carried forward with
its framing. The instance at `spec-010:63` sits inside `## Strawberry finalization strategy` (58-66),
the section this cycle retargeted `[spec-010-trigger]` to; the bullet carrying the handed-over claim is
`:65` and is clean, so the retarget is unaffected. One further in-repo instance (`registry.py:28-33` at
`:475`) sits in the bullet adjacent to D5's `:470` edit and was correctly left untouched.

**Not fixed, and the reason is the framing, not the effort.** `spec-010:554`
`## Note on source line references` **institutionalizes** the practice as a standing instruction to
readers. Closing the debt means converting ~20 in-repo references to `path::QualifiedName` **and**
retiring or rewriting that section — a contract change to spec-010 outside every site decisions 1-8
name. It needs a maintainer decision authorizing that widening. **Carried to R3's deferred-work catalog
with that framing intact; the diff was not widened.**

### Checks re-run, quoted

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-definition_order_independence-0_0_4.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0.**
- Same script on `docs/SPECS/spec-010-foundation-0_0_4.md` ->
  `OK: 12 terms - all have glossary entries and at least one spec link.` **exit 0.**
- Same script on `docs/SPECS/spec-001-django_types-0_0_1.md` (the third file in the diff) ->
  `OK: 21 terms - all have glossary entries and at least one spec link.` **exit 0.**
- `uv run python scripts/check_trailing_commas.py --check` over **every `.md` in the diff this cycle
  owns** — spec-008, spec-010, spec-001, the rationale, and this artifact -> **exit 0.**
- Rule-27 occurrence sweep, spec-008 and the rationale. Unit is **regex occurrences**
  (`grep -oE … | wc -l`), never matching lines: narrow `\.(py|md):[0-9]+` -> **0 / 0**; widened
  `\.[a-z]+:[0-9]+` -> **0 / 0.**
- Never run: `pytest` (with or without `--cov*`), `git stash`, `git checkout`, `git restore`,
  `git worktree`, `git commit`, any branch operation. HEAD reads used `git show HEAD:<path>`.

### Counts, with units and derivation commands

| File | bytes (`wc -c`) | lines (`wc -l`, newline-terminated) | fenced blocks (`grep -c '^```'` / 2) | def lines (`grep -cE '^\[[^]]+\]: '`) | anchored defs (parse) |
|---|---|---|---|---|---|
| `spec-008` | **18,100** | **244** | **0** (0 delimiter lines) | **22** | **15** |
| rationale | **70,620** | **1,042** | **2** (4 delimiter lines) | **29** | **17** |
| `spec-010` | **61,005** | **596** | **6** (12 delimiter lines) | **12** | **12** |
| `spec-001` | **44,577** | **508** | **7** (14 delimiter lines) | **22** | **21** |

The two durable files this cycle authored are spec-008 and the rationale; the other two are re-measured
to prove the siblings were not restructured. spec-008's and the rationale's figures are byte-identical
to pass 3's and to Worker 3's independent re-derivations. **Unit note:** the fenced-block column is
delimiter lines halved — `grep -c '^```'` alone counts *delimiters*, not blocks, which is the first
shape this cycle's counting trap took.

### Link-definition audit — all four files, machine-parsed

Own script written this pass (parse the block after the `<!-- LINK DEFINITIONS -->` delimiter, compare
the group list and its order against `LINK_DEF_CATEGORIES`, compare each group's ref-ids against
`sorted()`, resolve every path from the citing file's own directory, slugify every target's headings
fence-aware with duplicate `-N` suffixes and **without** stripping `_`):

| | spec-008 | spec-010 | spec-001 | rationale |
|---|---|---|---|---|
| 10 canonical group headers, in order | yes | yes | yes | yes |
| alphabetical within every group | yes | yes | yes | yes |
| paths missing on disk | **0** | **0** | **0** | **0** |
| anchored defs failing to resolve | **0** | **0** | **0** | **0** |
| used-undefined / defined-unused | **0 / 0** | **0 / 0** | **0 / 0** | **0 / 0** |
| inline `](#…)` anchors in body | **0** | **0** | **0** | **0** |

Every anchored def resolves: **15 + 12 + 21 + 17 = 65 / 65**, and **44 / 44** across the three files
Worker 3 scoped.

**The header-grep caution is real and was hit.** `grep -cE '^<!-- .* -->$'` returns **11** on every one
of these files — it matches the `<!-- LINK DEFINITIONS -->` delimiter too. The parse returns **10**
groups, and the parse is what the table quotes.

**A second unit trap fired inside this very audit and is worth recording**, because it is the same
class in a new costume. My first run reported one defined-unused def in spec-010 and 24 in the
rationale. Both were artifacts of my own *used*-detection: stripping inline code spans before matching
`][ref-id]` re-pairs backticks across a long file and swallows link uses whose text contains code
(`` [`Meta.fields`][glossary-metafields] ``). Re-running without the strip gives **0 / 0** for both.
Quantity of interest = link uses; tool measured = link uses *surviving a lossy pre-transform*. The
lesson is the one this cycle keeps re-learning: a green **or** a red result is only as good as the
normalization in front of it, and a **non-zero** result is the cheap one to misread.

### Scope discipline

- `git status --short` -> **43 entries** (unit: status lines), up from the **41** the prior passes
  recorded. The two new entries are `django_strawberry_framework/_request_body.py` and
  `docs/review/rev-_request_body.md`, plus state changes on `docs/review/rev-_strawberry_patches.md`,
  `rev-apps.md`, and `rev-conf.md` — **all concurrent-session work on files outside this cycle's
  writable set**, per `AGENTS.md` rule 34. Not edited, not reverted, not counted against this cycle.
- `spec-009`, `types/relations.py`, `types/base.py`, `testing/relay.py` -> `git status --short` **empty**
  on all four.
- `docs/review/` -> **8 entries**, untouched; the maintainer escalation stays open.
- Cumulative HEAD-side hunks unchanged by this pass: spec-008 **51**, spec-010 **10**, spec-001 **1**.
  This pass wrote **one file** — this artifact — and edited no spec, no rationale, and no sibling.
- `CHANGELOG.md`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`,
  `examples/fakeshop/db.sqlite3`, `AGENTS.md`, `START.md`, `BUILD.md`, the build plan, and every other
  cycle's artifact: untouched.

### Failability proofs / hot-path budget / floor verification / `review_inspect.py`

**Not applicable.** Markdown-only cycle: no boundary added, no runtime code, no behavior, no `.py` in
the diff. Recorded rather than omitted, as `worker-1.md` `### Failability and fail-open checks`
requires — a boundary with no proof would be `revision-needed`, and the correct discharge for a cycle
with **zero** boundaries is to say so explicitly.

### Notes for Worker 1 (spec reconciliation)

Everything R2b and R3 must not re-derive. Each item is disk-verified as of this pass.

**For R2b (`bld-008-r2b-source_attribution.md`), dispatched separately:**

1. All three of its files are **clean at HEAD** — `types/relations.py`, `types/base.py`,
   `testing/relay.py`. R2 opened none of them; R2b starts from an unmodified baseline.
2. Its scope is three sites and no more: `types/relations.py` `#"addressed by spec-014"` -> spec-010,
   `types/base.py::_build_annotations` `#"the import-order trap closed by spec-014"` -> spec-018
   (decision 4), and `testing/relay.py`'s `(or build the schema)` message (decision 8). **Comment and
   message only; no behavior, no signature, no test change.**
3. The contract R2b's `testing/relay.py` fix must match is now settled and quotable rather than
   inferred: **the explicit consumer call to `finalize_django_types()` is the sole trigger**, and
   spec-010 `:65` states the package-wide negative in one sentence — `DjangoSchema`,
   `DjangoConnectionField`, and `DjangoNodeField` do not call it. That is why "(or build the schema)"
   reads as a second trigger and is wrong. R2b cites spec-010, not spec-008: spec-008 `:173`
   deliberately hands the package-wide guarantee away.
4. `AGENTS.md` rule 27 applies to its comments in full — `path::QualifiedName`, never `path:NN`.

**For R3's `### Deferred work catalog`:**

1. **`spec-010 #"exactly as required by"`'s `spec-009 (1076-1077)` citation is stale.** It resolves to
   `### Should multiple \`DjangoType\`s per model be allowed?`; the error requirement it is cited for is
   at spec-009 `### Decision 6: fail loudly` (`:1068-1069`), **8 lines earlier**. **Stale at HEAD and
   independent of this cycle** — it was already wrong before R2 opened the file, and D3 authorizes only
   the two spec-008 citations while D6 defers spec-009. Do not present it as damage this cycle caused.
2. **spec-009's `### Layer 3: Finalization trigger`** now carries **two** inbound citations to
   reconcile, not one: L1 restored `(670-687)` at spec-010 `:65` as Edit 3 prescribes, and
   `(1076-1077)` at `:408` stays. Both belong in the same future spec-009 residual cycle.
3. **spec-010's rule-27 debt — 42 occurrences on 30 lines**, of which **20 occurrences on 15 lines**
   are in-repo violations and **22 on 15** are pinned third-party prior art. Carry the framing, not
   just the number: `spec-010:554` `## Note on source line references` **institutionalizes** the
   practice, so closing this is a conversion **plus** a section retirement, and it **needs a maintainer
   decision authorizing spec-010 edits outside the sites decisions 1-8 name**. Two of the in-repo refs
   (`:299`, `:383`) sit inside pseudocode comment lines. Not a find-and-replace.
4. **`testing/relay.py`'s `(or build the schema)` string is DISPATCHED, not deferred.** Decision 8
   folded it into R2b. R3 records it as dispatched; listing it as deferred would double-count it.
5. **`spec-010:513`** — "phase 2/3 partial-mutation limits … covered as explicit contracts" was read
   and deliberately **left**: partial mutation is still real, only the *recovery* claim was stale.
   Recorded so R3 does not re-flag it.
6. **Card 8's two incomplete `Verified in upstream` `CardItem`s** — Worker 0's pre-flight recorded them
   as a maintainer observation, not a fix. No pass in R2 touched a DB row; **R3 owns the
   verification.** The kanban DB is concurrently written, so read it, do not reset it.
7. **`KANBAN.md:248`'s board item has one fewer target** — it lists spec-008 among the specs still
   naming `convert_relation`, and spec-008 no longer does (`spec-009`, `spec-010`, `spec-019` still
   do). **Generated from the DB, so not hand-editable**; R3 records it for the maintainer rather than
   regenerating.
8. **`docs/review/` holds an open maintainer escalation, 8 entries, untouched by every pass in this
   cycle.** Out of scope for R3 as well.

**Standing, for whoever runs the remaining rounds:**

9. The recurring failure mode (M1, prior-M2, L8) is *the pointer names the right target and the anchor
   lands on prose that does not carry the claim*. A resolving link is evidence about the document
   graph, never about the claim. The two tests that separate a real instance from the `spec-008:175`
   near-miss, which was examined and cleared: **subject match** and **explicit forwarding by name**.
10. **Baseline-dirty count is now 43, not 41** — two concurrent-session entries appeared during this
    pass. Append the new figure to the plan's growth section rather than re-deriving the delta.

### Verdict

R2's contract is delivered. The `### Spec changes made` lists survive a claim-by-claim audit against
the real diff — 51 / 10 / 1 hunks, every hunk claimed exactly once, no phantom, and the R1 baseline
proven by an arithmetic route independent of the reverse-apply the prior passes used. The spec reads as
a clean current contract with no chronology and no amendment block; all eight maintainer decisions are
honored, decision 7's split is symmetric and reciprocal across both specs, and the five authorized
sibling edit sites are exactly five with spec-009 and all three R2b files clean. No source, test, or
example file is in the diff. All ten glossary anchors survive, 65 / 65 anchored defs resolve, and all
22 rationale entries carry a `Spec:` line.

The two open items are disposed of rather than carried: **L9 is correctly Low** — a durable-file sweep
for every one of its figures returns zero matches, which is the mechanical form of the severity
distinction Worker 3 argued — and the **spec-010 rule-27 debt is carried to R3 with its
institutionalizing framing intact and deliberately not fixed.** One new artifact-only inaccuracy (L10)
is recorded on the same basis. Nothing found requires a spec edit, so the diff was not widened.

### Header-field correction (Worker 1, 2026-08-14)

The header `Status:` line still read `planned` through all five passes; it is now `final-accepted`, the
value this final-verification block records. The six per-pass `## Status` sections **stay**, each with
a pointer line marking the header as canonical. The argument is `ARTIFACT.md`, not convenience.
`ARTIFACT.md:187` governs a multi-pass artifact — the file "reads as a linear pass / review / pass /
review sequence; never edit prior entries" — and `ARTIFACT.md:3` makes the artifact the thing that
"accumulates the full back-and-forth" between workers. Six recorded transitions, each attributable to
the one worker `## Status field ownership` puts on the hook for it, are exactly the entries that rule
protects; deleting them to fix a header defect would trade a stale field for a destroyed record, and
would also void Worker 3's line-cited references across three review passes. What the header defect
actually proves is that these blocks were never *labelled* — a reader landing on line 541 saw
`planned` with nothing telling them it was one pass's snapshot rather than the file's state. The
pointer lines close that, and they close it in the direction `ARTIFACT.md` already points: the header
is what Worker 0 reads, `ARTIFACT.md:181` makes writing it part of setting a review outcome, and no
per-pass block is ever a dispatch input. No historical value was rewritten. Each pointer costs 4 lines,
so a line below the first `## Status` shifts by 4 per preceding block (the six headings move
541 / 1167 / 1552 / 1773 / 2138 / 2446 -> 541 / 1171 / 1560 / 1785 / 2154 / 2487, the last also
carrying this paragraph). The only in-artifact line citation is `:215` (line 788's self-reference),
which sits above the first insertion and is unaffected.

## Status

> Not the artifact's status. The canonical `Status:` line is the header block above (line 5), and it
> is the only line Worker 0 reads to drive dispatch (`ARTIFACT.md:3`). This block records one pass's
> transition at the moment that pass wrote it — it happens to agree with the header, which is a
> coincidence of being last, not a guarantee.

`Status: final-accepted` — set by Worker 1 at final verification. R2 is closed. Worker 0 dispatches
**R2b** (`bld-008-r2b-source_attribution.md`, full unmodified worker chain) and then **R3**, which owns
the eight-item deferred-work catalog above.
