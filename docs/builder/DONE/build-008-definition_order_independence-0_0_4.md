# Package build plan: definition_order_independence / 0.0.4 (008)

Spec source: `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` (**already archived** — the spec and its `-terms.csv` already sit at their post-archive locations, and `SpecDoc.path` already reads the archived path; item R3 verifies rather than performs the move)
Target release: `0.0.4` (**shipped long ago** — card `DONE-008-0.0.4`, `target_version.number` `0.0.4`; the package is at `0.0.14` in `pyproject.toml`)
Date created: 2026-08-14
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging. A fact told twice across the spec and its rationale sibling goes stale in one of them — the rationale carries the deliberation, the spec carries the contract, and neither restates the other. This cycle additionally inherits `## The single-ownership law`, which extends the same rule ACROSS specs and standing docs.
Ownership partition: none; sequential residual items. (Declared explicitly rather than omitted, per `worker-0.md` `### Ownership partition`, so an interrupted item's output stays attributable against a tree several concurrent sessions are also writing.) The writable sets happen to be disjoint — R1 and R2 write Markdown only, R2b writes two source comments only — but the items are **not** dispatched concurrently: R2 consumes R1's output, and R2b is the cycle's only source diff and gets an undivided review pass.
Hot-path declaration: none. The only item touching package source is **R2b**, and it changes two comments — no executable line, so nothing runs per request, per resolver, per row, per connection, or per outbound message.
Floor-verification scope: none. R2b touches two files under `types/`, which is a Strawberry type-construction seam and would ordinarily be in scope — but a **comment-and-message-only** diff (decision 8's error string included: a changed string is still no changed control flow) changes no behavior at any version, so a floor run could not distinguish pass from fail. Declared `none` deliberately, with the reason stated, rather than omitted (`BUILD.md` `## Floor verification` `### When it is required`). R2b's Worker 3 pass verifies the comment-and-message-only property; if the diff turns out to touch an executable line, the item re-loops with floor scope declared.
Pre-flight: passed on 2026-08-14 with **four** recorded deviations (below); baseline: eighteen tracked-modified / thirteen untracked entries, every one attributable to the concurrently-running or just-closed spec-006 and spec-007 residual cycles, a transport-surface source session, or a REVIEW cycle — see `## Baseline-dirty out-of-scope files`; cleanup: **nothing deleted** (Deviations 1, 3, 4), every path this plan creates verified absent.

## This is a residual-completion cycle, not a fresh build

Spec-008 is a **design-exploration document**, and the shape difference from its five predecessors in this residual series is the whole story of the cycle. Spec-005 was falsified in its *subject*; spec-006 in its *instruments*; spec-007 in its *referents*. **Spec-008 is falsified in its TENSE.** It is 30,186 bytes / 603 lines of deliberation written *before* a decision was made, and it says so in its own headings: `## Current strongest direction, not a final plan`, `### Proposed shape to evaluate`, `### Finalization trigger choices`, `### Registry questions`, `### User annotation questions`, `### Generic fallback questions`, `### Rich-schema dependency questions`. **Nineteen** of those questions were settled by shipped code between `0.0.4` and `0.0.14`, and the spec still asks all of them. (Worker 0 first wrote "twenty-one", unmeasured; corrected at R1's review after Worker 3 re-derived it. The measurement is `?`-terminated lines across the four `### … questions` sections — `sed -n '425,494p' <HEAD copy> | grep -c '?$'` → `19`. `### Finalization trigger choices` contributes none: it poses its alternatives as statements, not questions, which is also why "four question-sections" and "five" are both defensible readings and why the new files must pick one and hold it.)

Its card is a **design record**, not an implementation card. `Card.objects.get(number=8)` reads title `Definition-order independence design`, and its three `Scope` rows are "Frame the class-definition-time relation-resolution problem", "Compare options for preserving concrete related `DjangoType`s without import-order coupling", and "Set the failure-mode requirements that **the 0.0.4 foundation slice implements**". The foundation slice is card 10 / `docs/SPECS/spec-010-foundation-0_0_4.md`, which says of this spec: it "discusses the relation-resolution problem space and prior art at length. This spec narrows that into one shippable slice and resolves the open design questions raised there."

So spec-008 is the only spec in this residual series whose deliverable was **a decision**, and whose decision was **taken elsewhere**. That is what makes its reconciliation different from a tense-fix: the spec must stop presenting a settled decision as an open one, without absorbing the implementation contract that its sibling owns.

**The decision the spec leans toward is the decision that landed — with one significant exception.** `## Current strongest direction` names Option 4 (Graphene-style deferred relation resolution via a pending-relation registry), and that is exactly what shipped: `types/relations.py::PendingRelation`, `registry.py::TypeRegistry.add_pending_relation` / `iter_pending_relations` / `discard_pending`, and the seven-phase `types/finalizer.py::finalize_django_types`. The exception is the **finalization trigger**, where the spec's stated leading direction was rejected outright — see drift row **D3**, the single most consequential row in this cycle.

### Residual scope (this cycle's actual work)

- **R1 — spec rationale extraction.** `docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md` does not exist. `docs/builder/BUILD.md` `## Spec rationale extraction` makes the move the first substantive action of a build and pre-flight step 7 gates dispatch on it; the shipped card predates the rule by three months. Worker 1 is the only role that may perform it. **This is the largest rationale move of any residual cycle so far** — see `### What R1 inherits`, and the maintainer's scoping decision at `### Maintainer decision 1`, which fixes in advance the one judgement that would otherwise dominate the pass.
- **R2 — reconcile the spec with what landed and what later changes corrected.** The maintainer's framing: *make sure the spec matches what actually exists, make sure the code is correct, and where later updates corrected what landed, the spec reflects that; the explanation of each change goes in the rationale, never in the spec.* Sixteen verified drift rows are tabled below. Worker 1 is the only role that may edit the spec.
- **R3 — finish the documentation and audit the archive.** Verify the durable docs describe the graph the shipped code actually builds; verify the archive is complete in all three cross-reference directions, in the kanban DB, and in the terms-CSV importability chain; and run the `TODO(spec-008` / `TODO-<MILESTONE>-008` staged-anchor sweep.

**"Make sure the code is correct" is a read-only audit obligation, and Worker 0 has already discharged its verification half.** The audit at `### The read-only correctness audit — findings` found **no defect and no omission in package source**: every hard invariant the spec sets holds at HEAD, and every acceptance criterion the spec lists is met except the two the spec itself got wrong (D3, D9). **No source file, test file, or example file is writable in this cycle.** If any pass finds a genuine correctness defect in shipped source, it is recorded as a finding and escalated to the maintainer — it does not become a source edit inside a documentation cycle.

## The single-ownership law

Maintainer instruction, given during the spec-006 residual cycle's pre-dispatch escalation and standing since. It is a contract-level decision about how specs relate to each other, not a spec-006-local one, so it binds every item here:

> each "thing"/feature should only exist concretely in a single spec, other specs can reference them (this should be rare as each spec should be able to stand on it's own) but the claim on ownership should exist in ONLY ONE spec

and, on the mechanics:

> since we did not fix every inbound reference in the same change last time, do that now

**This cycle is the first in the residual series where the law bites hard**, because spec-008 sits in a four-spec cluster (001 / 008 / 009 / 010) that all describe the same relation-resolution machinery from different altitudes, and two of them make **directly conflicting ownership claims** about the finalization pass. That conflict is `### Maintainer decision 2` below, and it is settled before R2 is dispatched rather than discovered during it.

## Maintainer decisions taken before dispatch

`docs/builder/BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch` requires each of these be decided by the maintainer, with the rejected alternatives and the reason each lost recorded, before any worker runs. All three were escalated on 2026-08-14 and answered the same day.

### Maintainer decision 1 — condensed prior art STAYS in the spec

**Decision.** The spec keeps a tight prior-art section: the two upstream approaches, and what this package borrowed from and avoided in each. The rationale takes the line-by-line source tours, the `### Pros` / `### Cons` lists, and the four-option comparison.

**Why this was a live question.** `## Prior art: Graphene-Django` and `## Prior art: Strawberry-Django` together run lines 68-241 — roughly 40% of the file — and every byte of it is deliberation by the ordinary test, which would send all of it to the rationale.

**Rejected alternatives.**

- *Move all prior art to the rationale.* Lost because `docs/SPECS/spec-010-foundation-0_0_4.md #"discusses the relation-resolution problem space and prior art at length"` describes spec-008 by that content. Emptying the spec of prior art would falsify a sibling's inbound description in the same change that was supposed to make the cluster consistent, and would require editing spec-010 for a reason unrelated to the rewrite.
- *Keep prior art in the spec as-is.* Lost because the per-line source tours are the deliberative layer at its purest — a builder needs none of it, and the thirty-one raw `path:NN` citations inside it are drift-by-construction (**D12**).

**Consequence for R1.** The prior-art move is a **condensation**, not a lift: what stays in the spec is rewritten to state the borrowed and avoided conclusions directly, and what moves carries the evidence for them. This is the one place in the cycle where R1 writes new spec prose rather than only removing it, and Worker 3 audits the condensation for the over-cut it invites.

### Maintainer decision 2 — the 001-through-010 ownership boundary

**Decision.** *Taken by a dedicated analysis pass, dispatched and returned 2026-08-14, on the maintainer's instruction to have specs 001-008 read in full against the single-ownership law and the boundary decided from the text rather than have Worker 0 pick between two readings.* The finding is recorded at `### The 001-010 ownership partition` below and is **binding input to R2**.

**The conflict that forced it.** Two siblings claim the same thing:

- `docs/SPECS/spec-001-django_types-0_0_1.md #"owns that pass"` — "Collection is separate from finalization: subclass creation collects, and a later `finalize_django_types()` pass resolves the recorded relation targets and applies `strawberry.type` to every collected class. `spec-008-definition_order_independence-0_0_4.md` **owns that pass**; this spec owns what subclass creation collects."
- `docs/SPECS/spec-010-foundation-0_0_4.md #"narrows that into one shippable slice"` — spec-010 carries the pending-relation records, the finalization phases, and the unresolved-target error, i.e. the actual finalization contract.

Both cannot own it, and the boundary decides how much of `### Proposed shape to evaluate` and `## Acceptance criteria` survives in spec-008 versus being pointed at spec-010.

#### The 001-010 ownership partition

The governing observation the analysis rests on: **spec-008 declines, in its own text, to own any contract.** It says "This section is not a final implementation plan", "Current strongest direction, not a final plan", and frames every mechanism as a question to settle. `docs/SPECS/spec-010-foundation-0_0_4.md` says of itself that it "is the single source of truth for what ships in this release" and "resolves the open design questions raised there". And spec-008 has **no companion rationale file** — it *is* the deliberative record, which is why R1's move is mostly a re-homing of the file's own nature rather than a surgical extraction.

So: **spec-008 owns the problem and the analysis; spec-010 owns every shipped contract; spec-001 owns what collection does.**

| # | Thing | Owner | Why |
|---|---|---|---|
| 1 | Definition-order **problem statement** | **spec-008** | Its `## Problem` / `## Why this matters for the goal` are the only full statement of why eager resolution blocks bidirectional graphs; spec-010 line 5 already concedes it "discusses the relation-resolution problem space… at length" |
| 2 | **Prior art** (graphene-django `Dynamic`; strawberry-django `auto` / explicit annotation) | **spec-008** | Analysis depth exists only here. Spec-010's "What we take from…" sections are borrow/reject *decisions* citing pinned references — they reference, they do not re-derive, which is the law's permitted rare reference. Spec-001's own prior-art section covers the type-primitive foundation, a different subject; no collision |
| 3 | The **design decision** — deferred resolution via a pending-relation registry | **spec-010** | Spec-008 explicitly declines to decide; spec-010 pins the `PendingRelation` shape, the registry extensions, and closes the rejected option via its Spike B. **Spec-008 keeps the Options 1-4 analysis as the why-alternatives-lost record**, rewritten to state that the decision landed in spec-010 |
| 4 | **Hard invariants** | **spec-010** | Its "Invariants this slice must protect" list has enforcement teeth ("Any change that violates one of them is a rejected change") and matches shipped code. **Spec-008's near-duplicate `### Hard invariants` collapses to a pointer** — this reverses drift row **D11**'s provisional reading, which expected the section to be what spec-008 durably owns, and D11's underlying fact (every invariant holds at HEAD) is unaffected |
| 5 | The **`finalize_django_types()` contract** — what the pass does, phase order, when to call it | **spec-010** | It pins the phase skeleton, idempotency, the single-threaded setup window, and the call point. **`spec-001` line 66 is simply wrong** (Edit 1 below). Later insertions into the pass — Phase 2.5's `apply_interfaces` (spec-015), `_synthesize_relation_connections` (spec-032), `_bind_filtersets` (spec-027), GlobalID wiring (spec-031) — stay owned by the specs that shipped them; spec-010 owns only the base lifecycle |
| 6 | What **subclass creation collects** | **spec-001** | Its line 66 claims it and its body delivers it: Meta validation, `ALLOWED` / `DEFERRED_META_KEYS`, field selection, scalar/enum synthesis, registration, the `get_queryset` sentinel. Spec-010's collection-phase pseudocode is migration record for the *split*, plus `DjangoTypeDefinition` and the consumer-authored relation-override contract, which spec-010 keeps (spec-005 already defers to spec-010 for that override surface) |
| 7 | The **unresolved-target `ConfigurationError`** | **spec-010** | It carries the canonical wording, the substring test contract, and the source-model / field / target requirement. Spec-008's fail-loud requirement becomes rationale; spec-001's one descriptive sentence is a reference, not a claim — **leave it** |
| 8 | The **registry** | **split three ways; no edit needed** | `TypeRegistry` itself is **spec-001**'s (it created `register` / `get` / `register_enum` / `get_enum` / `clear`, the three registration collisions, and the primary-aware `get()` lookup). The finalization-state extensions — `PendingRelation`, `add`/`iter`/`discard_pending`, `is_finalized` / `mark_finalized`, the extended `clear()` — are **spec-010**'s. The primary-type mechanism is **spec-018**'s. The partition is already articulated in spec-001 and spec-005 |
| 9 | **Acceptance / failure criteria** | **spec-010** | Its "Test fixtures and acceptance criteria" is the shipped, checkable inventory. Spec-008's `## Acceptance criteria` / `### Failure criteria` were *design-gating* criteria and largely duplicate item 4; in the rewrite they become rationale — "the criteria the design was judged against" — not live claims |
| 10 | **Fakeshop / cookbook fixtures** | **spec-010** (fakeshop) / **spec-009** (cookbook) | The shipped fixture is spec-010's library substrate plus the products multi-cycle graph. The cookbook fixture is aspirational (it lists still-deferred `aggregate_class` / `fields_class` / `search_fields`) and is spec-009's target-outcome material. **Spec-008's `## Cookbook implication` becomes a pointer to spec-009.** Both specs' "resolves to `list[ItemType]`" tables are version-scoped — the many-side default moved to `"connection"` at `0.0.14` (drift row **D14**), so reference that owner rather than restate the shape |

**Glossary-owned — no spec may claim these.** The **supported-relation-cycles roster** (forward/reverse FK, forward/reverse O2O, forward/reverse M2M, multi-cycle graphs) and the **consumer call-site recipe** (import every `DjangoType` module → call once → build the schema). Both live in `docs/GLOSSARY.md` under `## Definition-order independence` and `` ## `finalize_django_types` ``, which is the capability catalog's job under spec-006's discipline. Spec-010's acceptance tests *pin* the roster; the rewritten spec-008 restates neither.

#### Sibling-sentence edits authorized by this decision

The minimum set that leaves exactly one owner per item. **These three, plus `### Maintainer decision 3`'s two citations, are the complete writable surface outside spec-008 and its rationale.**

| Edit | File | Current | Replacement |
|---|---|---|---|
| 1 | `docs/SPECS/spec-001-django_types-0_0_1.md #"owns that pass"` | "`spec-008-definition_order_independence-0_0_4.md` owns that pass; this spec owns what subclass creation collects." | "`spec-010-foundation-0_0_4.md` owns that pass; this spec owns what subclass creation collects." |
| 2 | `docs/SPECS/spec-010-foundation-0_0_4.md #"helpers wrap it in later releases"` | "The foundation only exposes the explicit `finalize_django_types()` entry point; helpers wrap it in later releases." | "The foundation only exposes the explicit `finalize_django_types()` entry point; no shipped helper wraps it — the explicit consumer call remains the only trigger." |
| 3 | `docs/SPECS/spec-010-foundation-0_0_4.md #"Auto-trigger via"` | "Auto-trigger via `DjangoSchema(...)` and `DjangoConnectionField(Type)` is a later-phase wrapper around this same entry point — see `spec-009-…md (670-687)`." | "No shipped helper auto-triggers finalization: `DjangoSchema`, `DjangoConnectionField`, and `DjangoNodeField` do not call `finalize_django_types()`; the explicit consumer call is the only trigger. The auto-trigger direction in `spec-009-…md (670-687)` was not adopted." |

Edit 1 is a bare-filename reference, so no link-definition block changes. Edits 2 and 3 are the **same falsification as drift row D3**, reaching the sibling that inherited the prediction — which is why they belong in this change rather than a later one.

#### What R2 demotes from claim to rationale-plus-pointer

Directly implied by the partition, recorded so R2 does not re-derive it: `### Hard invariants` → spec-010; `### Proposed shape to evaluate` → spec-010; `### Finalization trigger choices` → spec-010; the four "questions to settle" subsections → spec-010, except the registry-primary questions → spec-018; `## Acceptance criteria` / `### Failure criteria` → spec-010; `## Fakeshop implication` → spec-010; `## Cookbook implication` → spec-009.

**What spec-008 keeps as its own:** the problem statement, the condensed prior art (`### Maintainer decision 1`), and the four-option analysis as the record of why three alternatives lost.

**One warning the analysis flagged for R2's prose.** Spec-008 lines 416-423 echo spec-009's hybrid finalization direction as live guidance, and call the explicit `finalize_django_types()` an "escape hatch". Neither may survive as live direction in any rewritten sentence: the direction was not adopted, and the "escape hatch" is the only trigger there is.

### Maintainer decisions 4-6 — three conflicts found OUTSIDE the ownership question

The ownership analysis surfaced three defects it was not asked about, each outside this cycle's writable set as first planned. All three were escalated to the maintainer on 2026-08-14 and answered the same day. **Worker 0 re-verified each against source before escalating** (`worker-0.md` `## Scope`: never dispatch a builder at an unverified finding), and the verification is recorded with each.

Items 4 and 5 below are the **same falsification as drift row D3 propagating across the 008/009/010 cluster** — which is the argument for fixing them together, and equally the reason the third was held back.

#### Maintainer decision 4 — the two `spec-014` source misattributions ARE fixed here

**Decision.** A narrow, comment-and-message-only carve-out (widened by `### Maintainer decision 8` to cover one error string) to `## Build-wide context flags`' source read-only rule. **This is item R2b**, dispatched as its own artifact through the full unmodified worker chain.

**Verified by Worker 0, 2026-08-14.** `grep -rn 'spec-014' django_strawberry_framework/` returns exactly two hits, and both are wrong:

| Site | Current text | Correct owner |
|---|---|---|
| `types/relations.py` #"addressed by spec-014" | "the two scaffolding objects that close the import-order trap addressed by spec-014: `PendingRelation` … and `PendingRelationAnnotation`" | **spec-010** — `docs/SPECS/spec-010-foundation-0_0_4.md #"### \`PendingRelation\`"` defines the dataclass and the three registry methods |
| `types/base.py::_build_annotations` #"the import-order trap closed by spec-014" | "The earlier eager-bind branch froze the relation against whichever type was already registered … (the import-order trap closed by spec-014)." | **spec-018** — `docs/SPECS/spec-018-meta_primary-0_0_6.md` **H1** states the trap and the always-defer fix verbatim: "That misses the import-order trap where a *single* secondary type registers first … Fix: **defer all relation annotations to finalization** regardless of registry state." |

`docs/SPECS/spec-014-testing_shift-0_0_4.md` is the **IRL API test shift** — it created the fakeshop `library` app and moved public GraphQL behavior into the live tier. It owns neither object. Almost certainly rot from the card renumber.

**Why fix rather than defer.** `AGENTS.md` rule 27 makes symbol-and-spec provenance in comments load-bearing precisely so the next reader can find the owning decision; a pointer to the wrong spec sends them to a testing document and costs them the trail. The edit is two comments, no behavior change, no test change.

**Rejected alternative.** *Record as a maintainer follow-up.* Lost because this cycle is already establishing the 001/008/009/010 ownership boundary, and leaving source pointing at a third spec would contradict the boundary in the same commit that fixes it.

**Scope limit.** Exactly those two comments. No behavior change, no signature change, no test change, no other source file. **`## Build-wide context flags`' "no source or test file changes" flag is amended by this decision and by nothing else.**

#### Maintainer decision 5 — spec-010's rerun-recovery contract is amended here

**Decision.** Worker 1 corrects spec-010's rerun-recovery contract to match shipped code, and acknowledges the Phase 2.5 insertion point. Folded into **R2**, alongside `### Maintainer decision 3`'s two citations and the partition's Edits 2 and 3.

**The contradiction.** Spec-010 states that re-calling `finalize_django_types()` after a Phase 2/3 failure on the same classes is unsupported and requires `registry.clear()` plus fresh classes. `types/finalizer.py`'s module docstring states the opposite: a raise in Phase 2 / 2.5 / 3 "supports a fine-grained partial recovery on rerun" via per-entry `definition.finalized` guards, with `clear()` demoted to "recommended escape hatch only when the offending type cannot be fixed in place". Some later change relaxed the contract and **no spec records it** — so spec-010 actively contradicts the code it owns.

Related and in the same edit: spec-010 documents a three-phase order; shipped code runs **four** (Phase 2.5), and Phase 1 additionally runs `_audit_primary_ambiguity`. Spec-010's phase-order prose should acknowledge the insertion points **without claiming them** — Phase 2.5's contents belong to spec-015 / 027 / 031 / 032 and the ambiguity audit to spec-018, per `#### The 001-010 ownership partition` item 5.

**Why here.** The relaxed behavior is a property of the pass spec-010 owns, so under the single-ownership law spec-010 is the only correct home for it; and this cycle is already editing four sentences in that file.

**Rejected alternative.** *Record for a future spec-010 residual cycle.* Lost because it would leave a shipped spec asserting the opposite of its own code for however long that cycle takes — a stronger defect than any this cycle set out to fix.

**Boundary.** R2 does **not** re-derive the recovery semantics from scratch: it states what `types/finalizer.py`'s docstring and the `definition.finalized` guards actually do, verified against source. If source and docstring disagree, that is a **finding to escalate**, not a contract to invent.

#### Maintainer decision 6 — spec-009's auto-trigger prose is DEFERRED

**Decision.** Recorded in R3's deferred-work catalog for a future spec-009 residual cycle. **Not edited here.**

Spec-009 Layer 3 describes `DjangoConnectionField` / `DjangoNodeField` / `DjangoSchema` calling the finalizer as "preferred triggers" — the D3 falsification one spec further out. Verified: `schema.py::DjangoSchema` contains no finalize call.

**Why deferred.** Spec-009 is a large architecture spec that deserves its own cycle; a drive-by edit to one section leaves the rest unreconciled and creates the false impression that the file has been checked.

**Consequence for R2, which is not optional.** Spec-008 lines 416-423 currently echo spec-009's hybrid direction as live guidance ("The newer rich-schema architecture spec leans toward a hybrid finalization story… This spec should continue to treat that as the leading direction"). Deferring the spec-009 fix does **not** license spec-008 to keep pointing at it as current: R2 states that the direction was **not adopted**, and cites spec-009 as the place it is recorded, never as a live recommendation. The partition's Edit 3 does the same for spec-010.

### Maintainer decisions 7-8 — taken at R2's review (2026-08-14), after the audit surfaced them

Both were escalated by Worker 3 at R2's review rather than at pre-flight, because neither was visible until R2's diff existed. `BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch` governs: the apply-changes pass is not dispatched until they are decided and recorded here.

#### Maintainer decision 7 — the unresolved-target error requirement SPLITS; partition item 7 gets a recorded exception

**Decision.** `spec-008` keeps the three-element requirement (the error must name the source model, the source field, and the target model) as the **design constraint any implementation must satisfy**. `spec-010` owns the **canonical wording, the message format, and the substring-test contract**. `spec-010`'s citation of `spec-008` is then a *reference*, which `## The single-ownership law` explicitly permits ("other specs can reference them"), not a second ownership claim.

**Why this was live.** `#### The 001-010 ownership partition` item 7 reads "spec-008's fail-loud requirement becomes rationale", and R2's diff did the opposite in one spot: `spec-008 #"### The shape that shipped"` states the three elements, and `spec-010 #"### Unresolved-target error format"` — as rewritten by decision 3's citation conversion — now sources the requirement *from* spec-008. Decision 3 authorized converting the citation's **form** (`(397-505)` → heading-anchored); what nobody weighed is that the retargeted heading was one the same pass had just demoted, turning a stale line range into a live cross-claim. So the finding is a genuine consequence of two correct decisions interacting, not a worker error.

**Rejected alternative.** *Enforce item 7 as written* — drop the enumeration from `spec-008`, leaving "a fail-loud raise", and repoint `spec-010`'s citation. Lost because it strips the design record of the single fail-loud constraint that motivated the whole decision: the plan's own drift row **D10** lists that error among the acceptance criteria spec-008 set and met, and a design record whose constraints have all been demoted stops being a design record. Fixing a requirement any implementation must satisfy is precisely what this document is for.

**Consequence.** Item 7 of the partition now carries a recorded exception rather than being silently contradicted. Worker 1 states the split explicitly in both specs, so a reader of either lands on the same division.

#### Maintainer decision 8 — `testing/relay.py`'s misleading error string is folded into R2b

**Decision.** R2b's scope extends to one further source edit: `django_strawberry_framework/testing/relay.py #"call finalize_django_types() (or build the schema) first"`. The parenthetical must name a remedy that actually works.

**Why.** Nothing in the package auto-finalizes (**D3**), so "build the schema" is at best ambiguous and at worst a remedy that does not. It is defensible under one reading — *import your project's schema module, which conventionally calls `finalize_django_types()` itself*, as `examples/fakeshop/config/schema.py` does — which is why this is a clarity fix rather than a bug fix, and why it was escalated rather than folded in silently.

**Rejected alternative.** *Leave it and record it in R3's deferred-work catalog.* Lost because it is the same defect class R2b already exists to fix (source prose falsified by a later change), because R2b is already running the full unmodified worker chain, and because a consumer-visible error string that names a non-remedy costs more than a stale comment does.

**Scope limit.** This authorizes **exactly that one string** in `testing/relay.py`. R2b remains comment-and-message-only: no behavior change, no test change beyond any assertion that pins the message text.

### Maintainer decision 3 — spec-010's inbound line-range citations are fixed in the SAME change

**Decision.** Worker 1 converts spec-010's two line-range citations into heading-anchored references, in the same pass that rewrites spec-008.

`docs/SPECS/spec-010-foundation-0_0_4.md` cites this spec by raw line range in two places:

| Site | Current text | What it points at today |
|---|---|---|
| spec-010 #"Option B from" | ``Option B from `spec-008-…md (400-414)` is closed out as rejected`` | lines 400-414 = `### Finalization trigger choices`, the four numbered approaches |
| spec-010 #"exactly as required by" | ``exactly as required by `spec-008-…md (397-505)` and `spec-009-…md (1076-1077)` `` | lines 397-505 = the tail of `### Proposed shape to evaluate` through `## Acceptance criteria` |

Any rewrite of spec-008 invalidates both, silently — a line-range citation cannot dangle loudly the way a broken link can.

**Rejected alternative.** *Defer to a follow-up.* Lost on the maintainer's own standing instruction above ("since we did not fix every inbound reference in the same change last time, do that now"), and because a stale range is worse than a missing one: it resolves to real prose that no longer says what the citing sentence claims.

**Scope limit.** This authorizes editing **exactly those two citations** in `docs/SPECS/spec-010-foundation-0_0_4.md`, plus whatever `### Maintainer decision 2` names. `spec-010` is otherwise read-only in this cycle, and no other sibling spec is writable except as decision 2 directs.

## Pre-flight outcome (7 steps, `docs/builder/worker-0.md` `## Pre-flight procedure`)

1. **Working-tree baseline is explicit.** `git status --short` → thirty-one entries, every one attributable to another session. See `## Baseline-dirty out-of-scope files`. HEAD is `947f7494`.
2. **`scripts/review_inspect.py` runs.** `uv run python scripts/review_inspect.py django_strawberry_framework/types/relations.py --output-dir docs/shadow --stdout` emitted its overview (4 imports, 4 symbols, 0 control-flow hotspots, 0 TODO comments, 0 repeated string literals). Exit 0. Run against `types/relations.py` deliberately: it is the module that *is* this spec's decision, so the smoke test doubles as a read of the shipped shape.
3. **Build artifacts are reset — DEVIATION 1, see below.** Verified instead that every path this plan creates is absent: no `docs/builder/build-008*`, no `docs/builder/bld-008*`, no `docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md`.
4. **`.gitignore` lists the untracked scratch paths.** `docs/shadow/` (line 174), `docs/builder/worker-memory/` (188), `docs/builder/temp-tests/` (192). Present.
5. **Scratch directories are cleared — DEVIATIONS 3 and 4, see below.** `docs/shadow/`, `docs/builder/temp-tests/`, and `docs/builder/worker-memory/` were **not** cleared: all three hold other cycles' state.
6. **Spec-doc consistency check.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-definition_order_independence-0_0_4.md` → `OK: 10 terms - all have glossary entries and at least one spec link.` Exit 0. Baseline for the constraint in `### The 10-anchor surface`.
7. **Spec rationale is extracted.** **Not done — it is item R1 of this cycle.** Ordinarily this gates dispatch. Here it cannot, because R1 *is* the dispatch: the work whose spawns the gate protects was built and released before this plan existed, so there is no builder left to protect. R1 runs first regardless, so every later spawn in this cycle reads the reconciled spec exactly as the rule intends.

Two further baselines recorded at pre-flight, both re-checked by any pass that writes:

- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-008-definition_order_independence-0_0_4.md` → exit 0 (link-definition scaffold and the 10 canonical group headers intact).
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/spec-008-definition_order_independence-0_0_4.md` → **25 matching lines carrying 31 citations** (corrected; see the D12 correction below), all inside the two prior-art sections. Unlike every prior residual cycle, `AGENTS.md` rule 27 compliance here is a property to **establish**, not one to preserve. See drift row **D12**.

Spec size before R1: **30,186 bytes / 603 lines**, **6** fenced code blocks. Worker 1 reports the after-count in the R1 artifact.

### Deviation 1 — other cycles' `build-*.md` and `bld-*.md` artifacts are PRESERVED

Pre-flight step 3 deletes old `build-*.md` / `bld-*.md`. They are **not** deleted here:

- `docs/builder/build-006-*.md` / `bld-006-*.md` and `build-007-*.md` / `bld-007-*.md` are the **uncommitted** records of two residual cycles that closed today (both carry a `bld-*-final.md`). They are the maintainer's pending commit; deleting them destroys work that has never been committed.
- The older committed `build-*.md` plans and `bld-003-*` / `bld-005-*` artifacts are records of closed cycles, and `BUILD.md` `### Cohorting, naming, and closure` ("Pre-flight for a round") already establishes that when a cycle's input is already-built work, the prior artifacts are the record of that work and must survive. Every residual item here operates on already-built, already-released work.
- **Collision is avoided by naming, not by deletion.** Every artifact this plan creates is `bld-008-`-prefixed and the plan is `build-008-`-prefixed; none of those paths exists.

### Deviation 2 — the `built` state is skipped where the deliverable is Worker-1-exclusive

`docs/builder/ARTIFACT.md` `## Status field ownership` gives `built` to Worker 2, and `worker-0.md` `## Per-slice dispatch` maps `planned` → Worker 2. Items **R1 and R2** have no Worker 2 role that could set it:

- **R1** — `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move, and states outright that **Worker 2 never reads the rationale file** — "that is the point of the move." Dispatching a builder at it would hand the file to the one worker the mechanism exists to keep away from it.
- **R2** — `BUILD.md` `## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the **only** role that may mutate the spec. R2's entire deliverable is spec edits.

So for R1 and R2 the chain is **Worker 1 (plan + perform, `planned`) → Worker 3 (audit, `review-accepted` | `revision-needed`) → Worker 1 (final verification, `final-accepted`)**, and Worker 0 reads `planned` on those artifacts as "dispatch Worker 3", not Worker 2. Declared here, before dispatch, so no pass improvises the mapping.

**Corollary, carried forward from the four prior residual cycles:** `worker-0.md` `## Per-slice dispatch` step 4 routes a Worker-3 `revision-needed` to Worker 2 for the apply-changes pass. On R1 and R2 that route does not exist — the same two rules that remove Worker 2 from the perform pass remove it from the fix. **The apply-changes pass for R1 and R2 is Worker 1's, and it sets `planned` again**, returning the artifact to the `planned` → Worker 3 mapping above. The loop is otherwise unchanged and repeats until Worker 3 has no unresolved finding.

The Worker 3 audit is **not** skippable alongside the Worker 2 build. `BUILD.md` names Worker 3 as a reader of the rationale file during review and as the pass that checks the finished work against it. A rewrite performed by the author is reviewed by an agent with no memory of why a sentence was cut — the only vantage point from which an over-cut looks like an over-cut, and this cycle's move is the largest in the series (`### What R1 inherits`), so the over-cut risk is correspondingly the highest.

**R3's shape is not predeclared.** In the two prior cycles R3 was a procedural-closure item because the audit found nothing writable for a builder. Here the audit found the archive already complete and the durable docs already accurate (`### The read-only correctness audit — findings`), so procedural closure is *expected* — but `### Maintainer decision 3` gives R3 a live edit (spec-010's two citations) if Worker 1 does not fold it into R2. Worker 1 says which shape R3 took in the artifact, and runs the full unmodified chain if it carries any edit.

### Deviation 3 — `docs/shadow/` was not emptied

Pre-flight step 5 clears it. It was not: it holds two just-closed cycles' overviews plus this cycle's step-2 `types/relations.py` smoke.

This is safe and changes nothing operationally. `docs/shadow/` is gitignored, regenerable, and — per `AGENTS.md` rule 23 — **each generator clears its own folder before writing**, so a stale overview cannot be read as fresh output by any pass that runs the helper. A pass that wants a file it did not generate itself regenerates it rather than trusting the folder's mtime.

### Deviation 4 — worker memory is NAMESPACED, not re-seeded

Pre-flight step 5 re-seeds the four `docs/builder/worker-memory/worker-<N>.md` files empty. Doing so here would destroy the `spec-005-*`, `spec-006-*`, and `spec-007-*` namespaces belonging to other cycles, and would touch the un-namespaced `worker-<N>.md` files this cycle does not own.

So this cycle uses its own namespace: **`docs/builder/worker-memory/spec-008-worker-<N>.md`**, seeded empty by Worker 0 at plan creation (verified present and zero-length). The rule's intent — a private notebook per worker that persists across a single build and is invisible to every other worker — is preserved exactly; what changes is only that concurrent builds no longer collide in one file, which the rule never contemplated and which would have broken isolation in **every** direction. Every dispatch prompt in this cycle names the namespaced path and the standing "do not read the other workers' memory files" instruction; it additionally forbids reading the un-namespaced `worker-<N>.md` files and the `spec-005-*` / `spec-006-*` / `spec-007-*` namespaces, which belong to other cycles.

## Baseline-dirty out-of-scope files

Workers neither edit nor revert these, and never `git checkout` them (`AGENTS.md` rule 34). Attribution is positive, not inferred: this cycle's writable set is the archived spec-008 file, its new rationale sibling, the two citations in spec-010 that `### Maintainer decision 3` names, whatever `### Maintainer decision 2` names, the four `bld-008-*` artifacts, this plan, and the four namespaced memory files — **no entry below is in any of them.**

Thirty-one entries at pre-flight, in four attributable groups:

- **The just-closed spec-006 and spec-007 residual cycles** (uncommitted, awaiting the maintainer's commit): `docs/SPECS/spec-006-public_surface-0_0_3.md`, `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md`, `docs/SPECS/spec-002-optimizer-0_0_2.md` and its rationale sibling (`M`); `docs/SPECS/appx/spec-006-…-rationale.md`, `docs/SPECS/appx/spec-007-…-rationale.md`, the four `bld-006-*`, the four `bld-007-*`, `build-006-*`, `build-007-*` (`??`). **The spec-002 pair is the spec-006 cycle's coordinated `## Visibility status` retirement, not a separate spec-002 cycle** — verified during the spec-007 cycle and recorded in its plan; a pass must not carry "a spec-002 cycle appeared" forward as fact.
- **A transport-surface source session**: `django_strawberry_framework/_boundary_ordering.py`, `django_strawberry_framework/_cross_web_patches.py`, `django_strawberry_framework/middleware/request_body.py`, `examples/fakeshop/test_query/test_transport_api.py`, `tests/test_views.py` (`M`). Declared read-only here and unreachable from any Markdown pass in this cycle.
- **A REVIEW cycle**: `docs/review/rev-_cross_web_patches.md` (`M`), `rev-_django_patches.md` / `rev-_strawberry_patches.md` / `rev-apps.md` / `rev-conf.md` (` D`), `rev-_boundary_ordering.md` / `review-0_0_14.md` (`??`). **This was escalated to the maintainer during the spec-007 cycle and remains open and unresolved.** `AGENTS.md` rule 22 names `rev-*.md` committed source of truth; its prescribed `git checkout HEAD -- docs/review/` restore is banned in this cycle by the `git checkout` ban in `BUILD.md` `## Claims are proven mechanically` and by rule 34's no-auto-revert. **No worker in this cycle restores, reverts, or touches anything under `docs/review/`**, and no pass treats the absence as its own output.
- **Generated / DB-backed files**: `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` (`M`) — see `## Concurrent-writable tracked binary / generated files`.

### First growth, recorded at the close of R1's re-review (2026-08-14)

Reported by Worker 3, verified and appended by Worker 0. **Nothing was reverted, and no worker may revert any of it.** `HEAD` has not moved (`947f7494`). Thirty-eight entries now, all growth inside the REVIEW cycle's own group:

- `docs/review/rev-_request_body.md` (`??`) — a new `rev-*.md` whose slug matches one of the five concurrently-edited transport-surface source files, and the second such correspondence in the series.
- **`docs/review/rev-_django_patches.md` moved ` D` → ` M`** — back on disk with different content, joining `rev-_cross_web_patches.md`, which made the same transition during the spec-007 cycle. The escalated set now reads **two modifications plus three deletions**, not the five deletions first recorded.

Two files coming *back* is not what a stray `rm` looks like, and it is now the second and third instance of the pattern — strong evidence the deletions are a REVIEW cycle regenerating its own artifacts rather than an `AGENTS.md` rule 22 violation. **It remains evidence, not a conclusion, and the escalation opened during the spec-007 cycle stays open**: only the maintainer can confirm the intent, and no worker in this cycle touches, restores, or reverts anything under `docs/review/`.

### Second growth, recorded at the close of R2's final verification (2026-08-14)

Reported by Worker 1, appended by Worker 0. Not reverted; `HEAD` still `947f7494`. **Forty-three entries now**, up from 41. All growth is again inside the concurrent transport-source and REVIEW-cycle groups:

- `django_strawberry_framework/_request_body.py` (`M`) — the transport-surface session's **sixth** source file. That session's set has now grown twice during this cycle; a pass reading the plan's group list as a fixed population will mis-attribute.
- `docs/review/rev-_request_body.md` (`??`) — a new `rev-*.md` whose slug again matches a concurrently-edited source file, plus state changes on three other `docs/review/` files.

**The `docs/review/` escalation stays open and unresolved.** No worker in this cycle touches, restores, or reverts anything under that directory.

**Expect this list to grow further.** `HEAD` may move during this cycle; **any pass quoting a commit hash from this plan re-derives it rather than trusting it**, and proves its own work was not swept into someone else's commit with `git log --stat` over this cycle's paths — never `git status` alone (`AGENTS.md` #"Staged `git mv` gets swept by a concurrent commit" is the standing hazard). If the list grows, workers **report it and never revert it**, and Worker 0 appends it here rather than a worker editing the plan.

**Baseline exception for the final test-run gate**, recorded here because `BUILD.md` `## Final test-run gate` requires it in the plan's preamble to be honoured: `uv run pytest --no-cov`, `uv run ruff format --check .`, `uv run ruff check .`, and `git diff --check` all read the whole tree, so they will see five concurrently-edited source files and two cycles' uncommitted output. A failure attributable to a file this cycle never wrote does **not** block `final-accepted` and does **not** route back through a residual item's loop; it is reported to the maintainer. The gate still reports each command's real result — the exception governs what a result *blocks*, never whether it is recorded honestly.

## Concurrent-writable tracked binary / generated files

Churn in these is not proof a worker caused it (`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`). All four are **already dirty** at this pre-flight, so **attribution by diff is not available to this cycle** and no pass may treat a diff in them as its own output or as drift to fix.

- `examples/fakeshop/db.sqlite3` — **no residual item is expected to write it.** Card 8 is already Done, its `SpecDoc.path` already points at the archived location, its ten glossary links already match the terms CSV exactly, and the CSV is one-row-per-anchor and therefore importable (verified below). Compare `iterdump()` semantics, never file bytes.
- `KANBAN.md`, `KANBAN.html` — generated; this cycle writes neither the DB nor the rendered files. Never hand-edited.
- `docs/GLOSSARY.md` — DB-rendered; no residual item is expected to change it. A diff here is another cycle's authorized glossary work, never this cycle's output. **Cite glossary entries by heading, symbol-qualified, never by line number** — the spec-007 cycle recorded an anchor moving mid-audit under exactly this churn.

If any pass concludes a DB write is genuinely required, it **stops and escalates to Worker 0** rather than writing: other sessions are mid-flight on the same DB, and the two-consecutive-regenerate verification `worker-0.md` step 8 requires cannot distinguish this cycle's write from theirs while theirs is in flight.

## Build-wide context flags

- **`0.0.4` shipped and the version quintet is at `0.0.14`.** No residual item touches `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, the GLOSSARY package-version line, or `uv.lock`.
- **Source and tests are read-only except for R2b's two comments.** `### Maintainer decision 4` carves out exactly two comment sites — `types/relations.py` #"addressed by spec-014" and `types/base.py::_build_annotations` #"the import-order trap closed by spec-014" — and nothing else. No behavior change, no signature change, no test change, no other file. `tests/` and `examples/` remain fully read-only. Beyond that carve-out the rule stands: spec-008 shipped no source, so there is no source prose it owns.
- **`CHANGELOG.md` is closed.** `AGENTS.md` rule 21 governs.
- **`README.md`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `AGENTS.md`, `START.md`, and `docs/builder/BUILD.md` are read-only.** The audit found the durable docs correct as written; where the spec disagrees with them, the spec is what moves.
- **Sibling specs are read-only except as `### Maintainer decision 2` and `### Maintainer decision 3` name.** A pass that finds a defect in an unnamed sibling records it for the maintainer and does not widen.
- **The spec is already archived.** `BUILD.md` `### Spec stays at its working location` requires a move be plan-declared as a Worker-1-owned final-verification step. There is no move: `docs/SPECS/spec-008-…md` and `docs/SPECS/appx/spec-008-…-terms.csv` are already at their archived paths, `SpecDoc.path` already reads the archived path, and the `KANBAN.md` reference already points there. **R1's new rationale file is therefore written directly to `docs/SPECS/appx/`** — the archived-companion location `AGENTS.md` rule 26 names — never to `docs/` first and moved after.
- **Only the maintainer commits.** No worker commits, and none creates or switches a branch.

## Worker-0-verified facts, passed into dispatch so no worker re-derives them

`worker-0.md` `## Closing out a kanban card` requires the live DB references be verified before a card/glossary edit is planned, because plan and spec text can carry stale ones. Read-only ORM queries, run 2026-08-14:

- `Card.objects.get(number=8)` → `card_id` `DONE-008-0.0.4`, `status.key` `done`, `target_version.number` `0.0.4`, `priority` `High`, `relative_size` `M`, title **`Definition-order independence design`**. The card is **already Done**; no status flip is in scope, and the 2026-07-30 card renumber left 008 untouched (it rotated 045-068 only).
- `card.labels` → four keys: `types`, `registry`, `relations`, `finalizer`. The spec has no `## Card snapshot` section, so unlike spec-007 there is no label list in the spec to drift.
- `card.planning_note` → **`''` (empty)**. No `## Planning note` section exists in this spec either.
- `SpecDoc` for card 8 → name `spec-008-definition_order_independence-0_0_4`, **`path` already `docs/SPECS/spec-008-definition_order_independence-0_0_4.md`**. No repoint needed. (`SpecDoc.path` is the writable column; `SpecDoc.url` is a read-only `@property` deriving from it — assigning `url=` raises.)
- `card.glossary_links` → **ten**, exactly matching the ten rows of `docs/SPECS/appx/spec-008-…-terms.csv`: `configurationerror`, `definition-order-independence`, `djangoconnectionfield`, `djangonodefield`, `djangotype`, `finalize_django_types`, `metafields`, `metaprimary`, `relay-node-integration`, `schema-audit`. One row per anchor, so the CSV is importable (`worker-0.md` `### DONE-card invariants` — a green `check_spec_glossary` alone does not prove this).
- Card 8 carries **six `CardItem`s** across three sections: `Scope` ×3 (all `is_complete = True`), `Verified in upstream` ×2 (**both `is_complete = False`**), `Note` ×1 (`True`). **No card-body edit is in scope** — a Done card's `Scope` is a record of what that card did. The two incomplete `Verified in upstream` rows are recorded as an observation for the maintainer, not fixed here: they cite upstream symbols (`graphene_django/converter.py::convert_field_to_djangomodel`, `strawberry_django/type.py::_process_type`) in a section that is not a `Definition of done`, so the mark-every-DoD convention does not reach them.
- **Staged-anchor sweep:** `grep -rEn 'TODO\(spec-008|TODO-(ALPHA|BETA|STABLE)-008' .` (excluding `KANBAN.md` / `KANBAN.html` / `BACKLOG.md`) → **zero hits anywhere**, spec included. `BUILD.md` `## Cross-slice integration pass` step 6 is therefore already discharged at baseline; R3 re-runs it as its backstop.

### The 10-anchor surface

Unlike spec-007's single-anchor knife-edge, spec-008 carries **ten** glossary anchors, and they are spread across the whole document — which makes the constraint *looser* per anchor and *broader* in total. Their carriers, verified at pre-flight:

| Anchor | Carrier in the spec body |
|---|---|
| `definition-order-independence` | the H1 title itself |
| `djangotype`, `configurationerror` | `## Problem` step 4 |
| `metafields` | `### Option 4` |
| `relay-node-integration` | `## Why this matters for the goal` |
| `djangoconnectionfield`, `djangonodefield` | `### Features that depend on this decision` |
| `finalize_django_types` | `### Finalization trigger choices` option 4 |
| `metaprimary` | `### Registry questions` |
| `schema-audit` | `### Generic fallback questions` |

**Five of those ten sit in sections R2 is most likely to rewrite or retire** (`### Finalization trigger choices`, `### Registry questions`, `### Generic fallback questions`, `### Features that depend on this decision`). Each must be **re-sited into surviving contract prose in the same edit that rewrites its carrier** — never by editing the CSV, never by leaving a hollow section behind purely to host a link, and never by re-adding narration the item just removed. Losing any one takes `check_spec_glossary` from `OK: 10 terms` to a failure and breaks the `import_spec_terms` chain for card 8.

**Every pass that writes the spec re-runs `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-008-definition_order_independence-0_0_4.md` and quotes the result in its artifact.**

### What R1 inherits

**This is the largest rationale move in the residual series, by a wide margin** — 30,186 bytes against spec-007's 2,282 and spec-006's 10,934 — and it is the first where the *majority* of the file moves. The mover's risk is therefore the opposite of spec-007's: not "is there anything to move", but "what is left when the deliberation is gone, and is it still a spec".

Decided in advance, so the mover does not improvise the judgement:

- **`### Maintainer decision 1` fixes the prior-art question.** It is settled; R1 implements it and does not re-open it.
- **The seven question-sections are the core of the move.** `### Finalization trigger choices`, `### Registry questions`, `### User annotation questions`, `### Generic fallback questions`, `### Rich-schema dependency questions`, `### Decision criteria`, and the four `### Option N` sections are deliberation about a decision now taken. Their **answers** belong in the spec as settled contract; their **question form, their "likely direction" hedges, and the alternatives they weigh** belong in the rationale.
- **The rationale is owed the RECORD, not just the move.** `BUILD.md` `## Spec rationale extraction` requires each entry name the spec decision it serves by heading and anchor, and carry: the alternatives rejected and why each lost; every change the decision has undergone; and **any claim the decision once made and may no longer make**. For this spec, the second and third clauses are unusually rich — this is the only document in the repository where the four rejected relation-resolution designs are recorded at all, and **D3** is a case of the spec's own leading direction being rejected by the implementation. That is the highest-value entry available.
- **Do not fabricate rejected alternatives — and here you do not need to.** Unlike spec-007, this spec *records its own deliberation explicitly*: four numbered options each with Pros and Cons, four numbered finalization approaches with tradeoffs, and five question-sections each with a "Likely direction". The rationale's job is to preserve that as decided history with the outcome attached, not to invent it. Where a question was settled by a **later** card (`Meta.primary` by spec-018 at `0.0.6`, `relation_shapes` by `0.0.9`/`0.0.14`), name the card — those are changes the decision underwent.
- **Do not duplicate the siblings.** `docs/SPECS/appx/spec-001-…-rationale.md` through `spec-007-…-rationale.md` exist (006 and 007 uncommitted but present). R1 reads the closest one for shape, not for content. It must also not restate the reasoning of spec-010, which owns the slice that implemented this decision — this rationale records what spec-008 claimed and how it fared.

### Verified spec-versus-HEAD drift — R2's input, verified by Worker 0

Read at HEAD (`947f7494`) on 2026-08-14, against package source, the kanban DB, and `docs/GLOSSARY.md`. Each row is a claim the spec makes that HEAD complicates or falsifies. **A prescribed correction is not included: how the spec should read is Worker 1's call, and the alternatives it rejects belong in the rationale file.** Worker 1 re-verifies each row rather than trusting this table.

| # | Spec claim | HEAD reality | Owner of the move |
|---|---|---|---|
| D1 | The whole document's **tense**: `## Current strongest direction, not a final plan`, "This should not be treated as a finalized implementation plan yet", "the exact type-finalization mechanics still need implementation research and tests", `### Proposed shape to evaluate`, and five `### … questions` sections | **The decision was taken and shipped at `0.0.4`.** Card `DONE-008-0.0.4` is Done; `types/relations.py::PendingRelation`, `registry.py::TypeRegistry.add_pending_relation`, and the seven-phase `types/finalizer.py::finalize_django_types` are the shipped answer. Every "should", "would", "needs research", and "questions to settle" is falsified by construction. This is the row that motivates the whole cycle | card 8 → card 10 |
| D2 | `## Problem` and `## Current package behavior`: "`DjangoType` **currently** resolves relation target types eagerly", "`convert_relation(field)` **immediately** asks the registry", "unresolved relation targets raise during type creation" | **The named symbol does not exist.** `grep -rn 'convert_relation' django_strawberry_framework/` → **0 occurrences**; relation annotations resolve through `types/converters.py::resolved_relation_annotation`. The described eager behavior is the pre-`0.0.4` state. `KANBAN.md #"the present-tense survivals in shipped specs"` already records that spec-008 / 009 / 010 / 019 all still name `convert_relation` and rules them **out of that board item's sweep** as "correct as history" — so this cycle, not that sweep, is where the spec's own tense is reconciled | the `0.0.4` foundation slice |
| D3 | `### Finalization trigger choices` + the four approaches (lines 399-423): the "leading direction" is a **hybrid** — "`DjangoConnectionField(Type)` finalizes before building a rich field", "`DjangoNodeField(Type)` finalizes before building a node field", "`DjangoSchema(...)` finalizes before constructing `strawberry.Schema`", with "`finalize_django_types()` remains public for explicit control" as an **escape hatch** | **The leading direction was REJECTED; Option 3 shipped instead.** Nothing in the package auto-finalizes: `grep -rn 'finalize_django_types' django_strawberry_framework/` returns no call site outside the definition, its re-exports, and docstrings. `connection.py` and `relay.py` contain no finalize call (`connection.py::_finalize_queryset` is queryset pagination, an unrelated name collision). The explicit consumer call is the **sole** trigger, documented as such in `docs/README.md #"Schema setup boundary"` and `docs/GLOSSARY.md #"## \`finalize_django_types\`"`. It is not an escape hatch — it is the contract. **This is the most consequential row in the cycle**, and the one spec-010 cites by line range (`### Maintainer decision 3`) | the `0.0.4` foundation slice |
| D4 | `### Finalization trigger choices`: "`DjangoSchema(...)` finalizes before constructing `strawberry.Schema`" names a symbol as the finalizing constructor | **`DjangoSchema` shipped, at `0.0.14`, for an unrelated contract.** `django_strawberry_framework/schema.py` — it installs `DjangoMutationExecutionContext` so a generated mutation's `transaction.atomic()` spans response completion, and resolves the production `ErrorPolicy` at construction. It does **not** finalize. So the spec's speculative name was later taken by a different feature, which is worse than a name that never landed: a reader checking the claim finds the symbol and infers the contract holds | spec-046 / 048 (`0.0.14`) |
| D5 | `### Registry questions` — five open questions ("Can there be multiple `DjangoType`s per model before `Meta.primary` exists?", "which one should automatic relations choose?", "should ambiguous automatic relation targets be a configuration error?", "how should tests reset registry state?") | **All five settled, and the "Likely direction" was right on every one.** `Meta.primary` shipped at `0.0.6` (spec-018); ambiguity **is** a `ConfigurationError` (`types/finalizer.py::_format_ambiguity_error`, whose fix sentence is "Declare Meta.primary = True on exactly one…"); pending records **are** stored separately (`registry.py::TypeRegistry.add_pending_relation` / `iter_pending_relations` / `discard_pending`); reset is `TypeRegistry.clear()` plus `registry.py::register_subsystem_clear`. The section asks questions whose answers are in the package | spec-018 (`0.0.6`) + the foundation slice |
| D6 | `### User annotation questions` — four open questions, incl. "should the package validate that manual annotations match the Django relation cardinality?" and "how should forward references and `from __future__ import annotations` interact?" | **Settled and documented.** `docs/GLOSSARY.md #"Supported forward-reference / manual relation shapes"` enumerates the shipped set: same-module string annotations, `from __future__ import annotations` stringified forms, cross-module `Annotated[..., strawberry.lazy(...)]`, annotation-only overrides (which keep the generated resolver), and `strawberry.field(resolver=...)` overrides (which keep the consumer resolver). The cardinality-validation question is the one whose answer Worker 1 must read out of source rather than out of the glossary | the foundation slice + spec-019 (`0.0.6`) |
| D7 | `### Generic fallback questions` — "Should generic fallback exist at all in 1.0?", "should it be per-field, per-type, or global?", "how would it appear in schema audit output?" | **Answered by omission, exactly as the section's "Likely direction" predicted.** No generic relation fallback exists anywhere: `grep -rn 'DjangoModelType' django_strawberry_framework/` → **0 occurrences** through `0.0.14`. Unresolved exposed relations raise, and `docs/GLOSSARY.md #"## Schema audit"` reports unregistered targets as warnings while ignoring hidden and `OptimizerHint.SKIP` fields — which is precisely the "distinguishes unresolved targets from intentionally skipped fields" behavior `## Acceptance criteria` asks for | the foundation slice + spec-004 (`0.0.3`) |
| D8 | `### Rich-schema dependency questions`: "Should `DjangoTypeDefinition` store `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, and `search_fields` **from the start**?" | **Answered "no — per subsystem, as each ships", and the split is visible in source.** `types/definition.py` carries `filterset_class` (bound `0.0.8`), `orderset_class` (bound `0.0.8`), and `fields_class` (**declared but reserved**, `None` while `Meta.fields_class` sits in `DEFERRED_META_KEYS`). `aggregate_class` and `search_fields` have **no slot at all** — `types/base.py::DEFERRED_META_KEYS` is `{"aggregate_class", "fields_class", "search_fields"}`, and their cards are still unshipped Beta work (`0.1.1`-`0.1.3`). So one of the five landed reserved, two landed bound, and two do not exist | spec-027 / 028 (`0.0.8`); Beta cards 054-057 |
| D9 | `## Acceptance criteria`, broader-goal bullet: "root `DjangoConnectionField` can **finalize** reachable model types before schema construction" | **Not met, and cannot be — by design.** `DjangoConnectionField` does not finalize anything (D3). The *dependency* the bullet was protecting is satisfied a different way: the field is constructed against already-finalized metadata because the consumer called `finalize_django_types()` first. An acceptance criterion that names a mechanism the implementation deliberately rejected reads as an unmet requirement rather than as a superseded one | the `0.0.4` foundation slice |
| D10 | `## Acceptance criteria`, the other twelve bullets | **Every one met.** Bidirectional `CategoryType.items` / `ItemType.category` in either declaration order; all six relation shapes (forward/reverse FK, forward/reverse O2O, forward/reverse M2M — enumerated in `docs/GLOSSARY.md #"Supported relation cycles"`); `Meta.fields = "__all__"`; the `ConfigurationError` naming source model, source field, and target model (`types/finalizer.py::_format_unresolved_targets_error` emits `"  - {source_model}.{field_name} -> {related_model} (no registered DjangoType)"`); optimizer plans over concrete targets; schema audit distinguishing unresolved from skipped; manual annotation override; no silent generic fallback; `DjangoNodeField` on finalized primary metadata. **This row exists so R2 does not churn a section that is right** | holds |
| D11 | `### Hard invariants` — the eight-bullet list (no Graphene dependency, no silent field skipping, no generic fallback by default, no serving a schema with unresolved exposed relations, no manual annotations required on `"__all__"`, no optimizer regression, no import-order-dependent schema shape, clear test reset story) | **Every invariant holds at HEAD.** This is the most contract-shaped section in the spec and the strongest candidate for what spec-008 durably owns (see `### Maintainer decision 2`). **Recorded so R2 preserves it rather than dissolving it into the rationale along with its neighbours** — it sits between two heavily-falsified sections and is easy to lose in the sweep | holds |
| D12 | Thirty-one raw `path:NN` citations on 25 lines (count corrected below) across `## Prior art: Graphene-Django` (lines 81-89) and `## Prior art: Strawberry-Django` (163-178), e.g. `graphene_django/converter.py:274`, `strawberry_django/type.py:410` | **An `AGENTS.md` rule 27 violation**, and the only residual cycle so far where the rule must be *established* rather than preserved. Rule 27 permits raw `path:NN` only in per-cycle scratchpads (`bld-*.md`, `rev-*.md`, `dry-*.md`) — **a `-rationale.md` is not on that list**, so moving them under `### Maintainer decision 1` does not launder them. Both targets are third-party checkouts outside this repo whose line numbers have certainly drifted (`graphene_django` lives in a sibling project's `.venv`). Every surviving citation, in either file, converts to the symbol-qualified form rule 27 prescribes | `AGENTS.md` rule 27 |
| D13 | `## Prior art: Graphene-Django` `### Cons`: "The dynamic placeholder is Graphene-specific; **Strawberry does not expose the same exact field lifecycle**" | **True as stated and overcome in practice** — the con was priced as a blocker and turned out not to be one. The package built a Strawberry-native equivalent: `types/relations.py::PendingRelationAnnotation`, a sentinel class whose metaclass `__repr__` names itself as unfinalized, rewritten in place by the finalizer. The "Parts to avoid" list correctly rules out porting `graphene.Dynamic`; what it could not know is that the *pattern* ported cleanly without the substrate | the foundation slice |
| D14 | `## Fakeshop implication`: eight rows, each of the form "`Category.items` should resolve to `list[ItemType]`", "`Category.properties` should resolve to `list[PropertyType]`", … "Today this cannot be represented as one rich primary type per model without omitting some relation fields" | **All eight relations are exposed — and half the stated shapes are now wrong.** `examples/fakeshop/apps/products/schema.py` exposes every one on a rich primary type, so the closing sentence is falsified in the best way. But `Meta.relation_shapes` (`0.0.9`) and its default move to `"connection"` (`0.0.14`) changed the shapes: `CategoryType.properties` has **no `list[PropertyType]` form at all** and is reachable only through `propertiesConnection`, while `CategoryType.items` and `ItemType.entries` carry explicit `relation_shapes = {"…": "both"}` opt-ins. The type also uses an explicit field tuple, not `fields = "__all__"` | spec-032 (`0.0.9`) + `0.0.14` |
| D15 | `## Cookbook implication`: the target node uses `fields = "__all__"`, `interfaces = (relay.Node,)`, `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `get_queryset`, and cascade permissions | **Six of nine shipped; three are still unshipped Beta work.** Shipped: `"__all__"` (`0.0.4`), `relay.Node` interfaces (`0.0.5`), `filterset_class` / `orderset_class` (`0.0.8`), `get_queryset` (`0.0.1`+), cascade permissions (`0.0.10`). Unshipped: `fields_class` (`0.1.1`, card 054), `search_fields` (`0.1.2`, card 055), `aggregate_class` (`0.1.3`). The section is aspiration that has aged into two-thirds fact, and reads as though none of it landed | the `0.0.8`/`0.0.10` cards; Beta cards 054-057 |
| D16 | `### Features that depend on this decision` — eight bullets naming `DjangoConnectionField`, `DjangoNodeField`, related filters, related orders, related aggregates, fieldsets, cascade permissions, optimizer relation kinds, each in the future tense ("needs", "need") | **Six of eight shipped on this foundation exactly as predicted** (`DjangoConnectionField` / `DjangoNodeField` `0.0.9`, related filters/orders `0.0.8`, cascade permissions `0.0.10`, optimizer relation-kind dispatch throughout). Aggregates and fieldsets remain Beta. **The section is the spec's strongest vindication and its most-falsified tense** — it is the load-bearing argument for why the decision mattered, written as a prediction that came true and never updated. Sole carrier of two glossary anchors (`### The 10-anchor surface`) | the `0.0.8`-`0.0.10` cards |

**Corrections to this table, appended by Worker 0 at the close of R1 (2026-08-14).** Worker 1 re-verified every row against source at HEAD rather than trusting the table, as its dispatch required, and returned three corrections plus one correction to the plan's own reasoning. **Each was independently re-verified by Worker 0 before being written here.** The table above stands except as follows. Rows D2, D3, D4, D5, D7, D8, and D13 were re-verified and confirmed **exactly as stated**.

- **D12's count is wrong, and it is Worker 0's own error of exactly the class `BUILD.md` `## Claims are proven mechanically` names.** The row said "twenty-eight raw `path:NN` citations" and the pre-flight baseline said "twenty-eight matches" (both now corrected in place, each pointing here). Both are wrong in both directions: the grep matches **25 lines**, and the true citation count is **31**. Three lines carry three citations each (`converter.py:274`, `342`, `381`; `converter.py:336`, `376`, `471`; `typing.py:105`, `113`, `116`), where the continuation numbers are bare backticked integers the regex cannot see — so `grep -c` under-reports and a hand-count of the *printed* lines over-reports. Re-derived by Worker 0 against a read-only HEAD copy: `grep -cE` → `25`; `grep -oE '…|\`[0-9]+\`' | wc -l` → `31`. **The lesson the rule states is the one that caught it**: search the shortest distinctive token and count *occurrences*, not matching lines — and measure as you write the number, because a count asserted alongside the lesson it illustrates is routinely wrong. D12's substance is unaffected; every citation converts either way.
- **D14 under-reports the falsification.** The row says "half the stated shapes are now wrong" and names `CategoryType.properties` as the connection-only case. `PropertyType` also carries **no `relation_shapes` key**, so `Property.entries` is connection-only too. The corrected reading: of the eight fakeshop rows, **two** are falsified (`Category.properties`, `Property.entries`) and **six still hold** — the two explicit `"both"` opt-ins (`Category.items`, `Item.entries`) and the four forward-FK rows, which `relation_shapes` never touched. Verified by Worker 0 against `examples/fakeshop/apps/products/schema.py`. The row's conclusion — that the shapes moved and the closing "this cannot be represented today" sentence is falsified in the best way — is unaffected.
- **D6's closing instruction is unnecessary.** The row hands Worker 1 the cardinality-validation question to "read out of source rather than out of the glossary". It is in the glossary, verbatim: `docs/GLOSSARY.md #"Validation that a manual relation annotation matches the Django relation cardinality is deferred."`, restated at #"manual override validation for relation cardinality is deferred; the package trusts relation-field annotations supplied by the consumer". It is the **only one of the spec's settled questions whose answer is still "deferred"** — and deferred *explicitly*, which is an answer, not a gap.
- **The plan was wrong that the upstream line numbers had drifted.** D12 and the pre-flight baseline both assert the cited line numbers "have certainly drifted" because the targets live in a sibling project's `.venv`. Worker 1 checked all 25 and reports every one still lands correctly. The conversion to symbol-qualified form proceeded regardless, correctly: `AGENTS.md` rule 27 is not conditional on a citation being accurate.

**The count-error class is this cycle's signature defect, and it has now hit three passes in a row.** Worker 0's `28` citations and `21` settled questions; Worker 1's fence, anchor, and question counts (Worker 3 finding **M1**, five numbers). Every instance shares one shape: **a number describing the spec's own structure, asserted inside narrative prose about that structure, measured by a `grep -c` whose unit is lines when the claim's unit is something else** — citations (3 per line), fenced blocks (2 delimiter lines each), questions (`?`-lines, not headings). None was a research failure; each was a unit mismatch nobody re-derived. Every pass from here re-derives such a number with an explicit unit, or writes the derivation command beside it so the reader can. This paragraph is the canonical telling; the D12 bullet above carries the first instance and the artifact carries M1.

Two things this table deliberately does **not** say. First, that every row must change the spec: D10, D11, and D13 are the spec being *right*, and are here so R2 preserves them — Worker 1 decides per row whether the contract is restated, pointed elsewhere, or dropped to the rationale. Second, that the list is exhaustive; it is Worker 0's verified floor, and R2 owns the full sweep.

**The scope trap specific to this spec.** Spec-008's subject is *a decision*, and the decision's implementation is spec-010's. The pull is therefore toward rewriting spec-008 as a description of how `finalize_django_types()` works today — which would duplicate spec-010's contract, duplicate `docs/GLOSSARY.md #"## \`finalize_django_types\`"`'s seven-phase list, and violate `## The single-ownership law` in the same change that was supposed to enforce it. The durable contribution of a design-record card is **the decision and the constraints it fixed** — which approach was chosen over which three alternatives, why, and what invariants any implementation of it must hold — never the phase order of the implementation that followed.

### The read-only correctness audit — findings

The maintainer's instruction "MAKE SURE NOTHING WAS SKIPPED IN THE CODE" reaches, for this card, the implementation that its decision authorized. **No defect and no omission found in package source.** Worker 0's read-only verification, 2026-08-14:

- **The chosen design shipped whole.** Option 4's proposed shape — record pending relations at class creation, resolve them against the registry before schema construction, compute the concrete annotation per relation shape, merge with user annotations, attach Django relation metadata for the optimizer, raise naming source model / source field / related model if anything is unresolved — maps one-to-one onto `types/relations.py::PendingRelation`, `registry.py::TypeRegistry.add_pending_relation`, `types/converters.py::resolved_relation_annotation`, `types/resolvers.py`, and `types/finalizer.py::finalize_django_types`. Nothing in the proposed shape was silently dropped.
- **Every hard invariant holds** (D11), including the two that are absence-shaped and therefore easiest to erode without noticing: zero Graphene imports, and zero generic-fallback types.
- **The fail-loud contract is stronger than the spec asked for.** The spec asks for one `ConfigurationError` on unresolved targets; the finalizer ships that plus a sibling primary-ambiguity error, both with actionable fix sentences, both grep-stable by deliberate convention (`types/finalizer.py::_format_unresolved_targets_error` documents the sibling relationship).
- **Two acceptance criteria are unmet because the SPEC is wrong, not the code** (D3, D9). The implementation deliberately rejected the hybrid finalization trigger in favour of one explicit call. That is a decision reversal to record, not a gap to fill — and recording it is exactly the maintainer's "where later updates corrected what landed, the spec reflects that".
- **The durable docs are accurate and complete.** `docs/GLOSSARY.md`'s `## Definition-order independence`, `` ## `finalize_django_types` ``, and `## Schema audit` entries describe the shipped behavior correctly, including the seven-phase order and the full supported forward-reference shape list. `docs/README.md #"Schema setup boundary"` documents the explicit-call contract with both the correct and the incorrect ordering. **No durable-doc edit is expected in R3.**
- **No staged work was left behind.** The `TODO(spec-008` / `TODO-<MILESTONE>-008` sweep is empty tree-wide.

One observation recorded so R2 does not mistake it for drift to "fix": **the card body is a faithful record and stays untouched.** Card 8's three `Scope` rows accurately describe what the card did — frame the problem, compare the options, set the failure-mode requirements — and all three are `is_complete = True`. The spec's problem is that it presents an *open* deliberation as current. The fix is entirely inside the spec file.

### Every reference TO spec-008 (verified by grep, 2026-08-14)

The archive already landed, so this is R3's **verification** list rather than a rewrite list — except the two spec-010 citations, which `### Maintainer decision 3` makes writable. R3 re-runs the sweep rather than trusting it.

| Location | Current text | Status |
|---|---|---|
| `KANBAN.md:139` (+ the corresponding `KANBAN.html` payload) | `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` | **Generated** — already correct; never hand-edit |
| `KANBAN.md:248` | a board item naming spec-008 among "present-tense survivals in shipped specs … correct as history and are not in the sweep" | **Generated**, and it scopes a *different* board item's sweep out of this spec. Not a conflict with this cycle: that item declines to fix the survivals in passing; this cycle is the authorized place | 
| `examples/fakeshop/db.sqlite3` (`SpecDoc.path`) | `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` | Already the archived path; no repoint |
| `docs/SPECS/appx/spec-008-…-terms.csv` | ten rows, one per anchor | Importable; all ten anchors resolve in `docs/GLOSSARY.md` |
| `docs/SPECS/spec-001-django_types-0_0_1.md #"owns that pass"` | "`spec-008-…md` owns that pass; this spec owns what subclass creation collects" | **The ownership conflict** — writable only as `### Maintainer decision 2` directs |
| `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md #"The narrow definition-order problem is documented in"` | points at spec-008 for the narrow problem, positions itself as broader | Consistent; verify only |
| `docs/SPECS/spec-010-foundation-0_0_4.md` ×4 | line 5 (the "problem space and prior art" description), the two line-range citations, and a closing `## References` pointer | Line 5 and the reference pointer are consistent; **the two line-range citations are writable per `### Maintainer decision 3`** |
| `docs/builder/build-001-*.md`, `build-002-*.md` | historical build plans naming the spec | Closed cycles' records; **never edited** |

**The direction this table cannot show** is the one inside the new file: R1's rationale lands at `docs/SPECS/appx/`, two levels below `docs/`, so its link definitions need `../../GLOSSARY.md` for a `docs/` target, `../../../README.md` for a root target, and `../spec-NNN-….md` for a `docs/SPECS/` sibling. The archived siblings (`docs/SPECS/appx/spec-005-…-rationale.md`) show the shape. One trap is live: a same-named file one level up **masks** depth rot (`../README.md` from `appx/` resolves to `docs/README.md`, not the root `README.md`). Disk-exists-check every rewritten path, and check *which* `README.md` each one lands on.

## Artifact list

- `docs/builder/bld-008-r1-rationale_move.md`
- `docs/builder/bld-008-r2-spec_reconciliation.md`
- `docs/builder/bld-008-r2b-source_attribution.md`
- `docs/builder/bld-008-r3-doc_completion_archive.md`
- `docs/builder/bld-008-final.md`

No `bld-integration.md`-equivalent: a cross-slice integration pass exists to find duplication across slices that landed source, and this cycle lands none. Its live obligations are folded in — the staged-anchor sweep (`BUILD.md` `## Cross-slice integration pass` step 6) runs in R3, and the cross-artifact read runs in the final gate.

## Checklist

- [x] R1: Spec rationale extraction into `docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md`, implementing `### Maintainer decision 1` (Worker 1 performs the move and authors the record; Worker 3 audits it; Worker 1 final-verifies) -> `docs/builder/bld-008-r1-rationale_move.md`
- [x] R2: Reconcile the spec with HEAD — every claim the repository falsifies is restated as the contract that actually holds, or handed to the document that now owns it under `### Maintainer decision 2`; the five authorized sibling-spec edits land in the same change (`### Maintainer decision 3`'s two citations, the partition's Edits 1-3) plus `### Maintainer decision 5`'s spec-010 rerun-recovery amendment; the explanation of each change lands in the rationale, never in the spec -> `docs/builder/bld-008-r2-spec_reconciliation.md`
- [x] R2b: Correct the two `spec-014` source misattributions per `### Maintainer decision 4`, plus `testing/relay.py`'s misleading `(or build the schema)` remedy per `### Maintainer decision 8` — comment-and-message-only (no behavior change), `types/relations.py` -> spec-010 and `types/base.py::_build_annotations` -> spec-018. **Full unmodified worker chain** (Worker 1 plans, Worker 2 builds, Worker 3 reviews, Worker 1 final-verifies): it is the cycle's only source edit, so `BUILD.md` `### Isolation is non-waivable` applies with no deviation -> `docs/builder/bld-008-r2b-source_attribution.md`
- [x] R3: Finish the documentation and audit the archive — durable-doc audit against the shipped relation graph, the cross-reference sweep in all three directions, `SpecDoc.path` / terms-CSV verification, and the `TODO(spec-008` / `TODO-<MILESTONE>-008` staged-anchor sweep -> `docs/builder/bld-008-r3-doc_completion_archive.md`
- [x] Final test-run gate -> `docs/builder/bld-008-final.md`

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
