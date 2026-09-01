# Rationale companion: spec-035 (Optimizer robustness hardening — G1, G2, deferred G3)

Companion to [`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`][spec-035]. It carries that spec's **deliberative layer** and nothing else: the four-revision review history that produced the contract, every Decision's justification, every alternative a Decision rejected and why it lost, the risk / open-question deliberation that settled the card's design questions, and the amendment and retraction prose the spec is no longer allowed to narrate. The spec carries the contract; this file carries how the contract was arrived at. Neither duplicates the other — the text here **left** the spec.

Read this when checking a finished implementation against the reasoning that produced it, or before re-opening a settled question. Worker 2 never reads it ([`docs/builder/BUILD.md`][build-md] `### Who reads it, and when`).

**How later passes append to this file.** Each Decision below carries a `### Changes this Decision underwent` section recording the rounds that changed it. A reconciliation pass that finds the spec stale against `HEAD` — a helper that moved, a guard that needed machinery the Decision never named, a waiver a later card reversed — appends an entry under [Post-ship divergences](#post-ship-divergences-spec-vs-head), keyed to the Decision that owns the correction. Findings belonging to no single Decision go under [Non-Decision deliberation](#non-decision-deliberation). Nothing needs restructuring to take an addition, and the corrections themselves always land in the spec, stated directly and without chronology.

## Provenance of this record

Created by pre-flight step 7 of the `035` retrospective reconciliation cycle, whose plan is [`docs/builder/DONE/build-035-optimizer_hardening-0_0_10.md`][build-035]. That cycle's per-slice artifacts were deleted once it closed; the Slice 1 record that governed this move is recoverable at `git show 8c05f7fc:docs/builder/bld-035-slice-1-rationale_extraction.md`. The move runs late: `DONE-035-0.0.10` shipped in `0.0.10` with a [`-terms.csv`][spec-035-terms] companion and no `-rationale.md` sibling, and the cycle exists to close that gap and to reconcile the spec against the repo the intervening cards left behind. Nothing here is new reasoning: every passage below was cut from the spec in the same pass that created this file, except the framing paragraphs, the `### Changes this Decision underwent` summaries, and the [Post-ship divergences](#post-ship-divergences-spec-vs-head) section, which are this pass's own and say so. The `034` companion is the immediately-preceding execution of the same move and this file matches its shape.

Measured against the spec on disk before the move (143,045 bytes, 542 lines), four routes carried text out:

- **The whole `Revision history (kept inline so the spec is self-contained):` block** — its preamble plus four `Revision N` entries. The four entries are reproduced under [Revision history](#revision-history) below, byte-for-byte; the preamble line was **deleted, not moved** — its claim that the history is kept inline is exactly what this move made untrue.
- **9 `Justification:` blocks and 9 `Alternatives considered (and rejected):` blocks**, one pair under each of Decisions 1-9, carrying 12 justification bullets or paragraphs and 21 rejected alternatives. Reproduced byte-for-byte under each Decision's heading; the 18 labels became `###` headings here — 6 stood on their own line and 12 were inline prefixes stripped from the paragraph they introduced.
- **The body of `## Risks and open questions`** — its preamble plus 9 items, each written as a preferred-answer / fallback pair. That shape is a build-time deliberation instrument, not a contract, so the body moved and the spec keeps the heading and a pointer here. Nothing was held back: no item in this body carries a rule the implementation depends on, and the two card-citation corrections' *conclusions* already live in Decisions 3 and 6.
- **Amendment and retraction framing embedded in surviving contract prose** — 11 sites. Nine are chronology tags stripped from sentences that survive (`, as reconciled in Revision 4`; `; Revision 3 above`; `, reconciled to the shipped state in Revision 4`; ` (Revision 3)` twice; `As of Revision 3 `; ` (Revision 3)` in the Decision 6 status block; ` (added in Revision 3)` in a heading; `, Revision 3` in Decision 7's maintainer-decision line). Two are draft-history parentheticals removed from Decision 5's hazard and implementation-rule paragraphs. One further site — Decision 7's whole `(An earlier draft of this Decision claimed ... that was **wrong** ...)` retraction — moved here entire, recorded under that Decision.

**Held back in the spec under the implementation-relevant carve-out**, six passages. Each is the "why" that changes how the thing is built, a guarantee the contract makes, or a test pin, not an argument against a rejected alternative:

- [Decision 4][spec-035-d4]'s enumeration of the four projection writers and *why* each must consult the gate — `_record_relation_access` populating `only_fields` independently of scalar appends, and `_project_scalar_only_window` applying `.only(...)` without ever touching `only_fields`. A builder who never reads that writes the leaking version, which is precisely the rejected alternative recorded under Decision 4 below.
- [Decision 5][spec-035-d5]'s consumer-`.only()` hazard mechanism — B8 consumer-wins preserves the consumer projection, and strictness stays silent because the relation is recorded planned. That is the reason the loaded-check exists at all; only the draft-history framing around it moved.
- [Decision 6][spec-035-d6]'s "both interface-collection arms are required, neither subsumes the other" mechanism and its tri-state-not-boolean requirement. The rejected alternatives arguing *against* the single-source and boolean shapes moved; the requirements themselves stayed.
- [Decision 3][spec-035-d3]'s two-directional placement argument (after the manager coercion, before the clone). It states where the guard must sit and what breaks on either side of it.
- Every cache-safety argument (Decisions 4 and 6, and the cross-guard edge case). These are normative constraints on where a gate may land, not derivations.
- The closing `Pinned by test_fk_id_elision_enabled_under_mutation ... and test_fk_id_elision_falls_back_when_consumer_only_defers_fk ...` sentence of [Decision 5][spec-035-d5]'s `Alternatives considered (and rejected):` paragraph. It is a test pin rather than a rejected alternative, so it stayed in the spec — promoted to its own paragraph, since the paragraph it was attached to left — and does not appear under Decision 5 below.

**Not byte-verbatim in one respect.** Text carrying the in-page anchors `#borrowing-posture`, `#current-state`, `#definition-of-done`, `#out-of-scope-explicitly-tracked-elsewhere`, `#problem-statement`, `#reference-package-parity-checkpoint`, `#slice-checklist`, and the G3 deferred test-plan heading names spec sections this file does not have; those uses are re-pointed at the spec through reference-style links rather than left to dangle. The `#decision-N--...` anchors were left as they were: this file carries headings with exactly those slugs, so they resolve locally, which is where a reader of a moved sentence wants to land. `#risks-and-open-questions` likewise resolves locally.

**Not reconciled by this pass.** The move did not correct a single substantive spec claim. The divergences it found while reading are recorded under [Post-ship divergences](#post-ship-divergences-spec-vs-head) with the evidence, and Slice 3 of this cycle owns writing the corrections into the spec body — stated directly and without chronology.

## Revision history

Four revisions produced the contract: Revision 1 the initial draft, Revision 2 the G1-already-shipped reconciliation, Revision 3 the G3 deferral after a production-reachability review, and Revision 4 the post-implementation reconciliation that moved the document to completed voice. The block below is the spec's own, verbatim; every finding in it is also recorded under the Decision it changed, in that Decision's `### Changes this Decision underwent` section, or — when it belongs to no Decision — under [Non-Decision deliberation](#non-decision-deliberation). The chronology is what a reviewer of a Decision's history needs; the per-Decision record is what a reviewer of the implementation needs, so both are kept and the duplication is deliberate and bounded to this one block.

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-035-0.0.10`][kanban] card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-06-15). Pinned: the canonical structured spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the three guards ported at the **outcome** level from `strawberry_django` with the package's own minimal mechanisms ([Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize) / [Decision 4](#decision-4--g2--operation-type-gating-of-only-suppress-only_fields-for-non-query-operations-at-plan-build-time) / [Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing)); the **G2 FK-id-elision-under-non-`QUERY` open decision** resolved in favor of keeping elision enabled ([Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations)); the **narrow-not-multi-plan** posture rejecting upstream's per-concrete-type re-walk ([Decision 7](#decision-7--g3--narrow-do-not-multi-plan)); the cache-safety arguments for G2 and G3 (zero key change in both cases); the deferred-audit findings carried into [Out of scope][spec-035-out-of-scope] as spec non-goals; the joint-cut version boundary shared with [`DONE-034-0.0.10`][kanban] ([Decision 9](#decision-9--version-bumps-are-owned-by-the-joint-0010-cut)); and three card-citation corrections recorded rather than silently reconciled — the manager-coercion site (the card's line-number cite predates the DRY consolidation; the live home is the symbol [`utils/querysets.py::normalize_query_source`][querysets], called from [`extension.py::_optimize`][extension], [Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize)), the fragment-inlining anchor (the card's line cites predate the [`DONE-033-0.0.9`][kanban] connection work that moved inlining into the shared substrate; the live primitive is [`selections.py::included_field_selections`][selections] inlined from [`walker.py::_walk_selections`][walker], with the unknown-name `continue` guard in the same function, [Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing)), and the grep results for the three gaps. *(The Revision-1 grep claim that `_result_cache` was also absent was **wrong** — G1 had already shipped in commit `d1dea2fd`; corrected in Revision 2. `OperationType` and a *matched* `type_condition` are genuinely absent — [Current state][spec-035-current-state].)*
- **Revision 2** — G1-already-shipped reconciliation (2026-06-16, same authoring cycle), verified against the live checkout: commit `d1dea2fd` ("implement evaluated-queryset guard in DjangoOptimizerExtension") landed **G1 in full** before this spec was finalized — the `getattr(result, "_result_cache", None) is not None` early-return in [`extension.py::_optimize`][extension] (citing "G1, `spec-035` Decision 3" in its own docstring) plus a `# G1 (spec-035 Slice 1)` test block in [`tests/optimizer/test_extension.py`][test-opt-extension] of **four** tests (`test_optimizer_passes_through_consumer_evaluated_queryset`, `test_optimize_returns_same_instance_for_evaluated_queryset`, `test_optimizer_still_optimizes_manager_after_evaluated_queryset_guard`, `test_resolve_async_passes_through_evaluated_queryset`). The Revision-1 "`_result_cache` absent" grep claim was therefore false. Reconciled (no design change, G1 unchanged from the Decision-3 contract): Slice 1 / [Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize) are reframed as **shipped and recorded** (checklist ticked, DoD item 2 satisfied, the parity-table G1 row marked shipped), the [Current state][spec-035-current-state] / [Problem statement][spec-035-problem-statement] "gap" framing for G1 is corrected to "closed in `d1dea2fd`", and G1's only remaining work is its GLOSSARY note (Slice 4 — the commit touched code + tests, not docs). G2 and G3 remain to build exactly as authored.
- **Revision 3** — G3 deferral after a production-reachability review (2026-06-16, same authoring cycle), verified against the live checkout. The review established that G3's narrowing has **no reachable production trigger**: an interface / union root field never enters the optimizer walker, because [`extension.py::_resolve_model_from_return_type`][extension] resolves the abstract return type's `origin` (the interface / union class, not a registered `DjangoType`) and [`registry.model_for_type`][registry] returns `None` for it, so [`_optimize`][extension] passes the queryset through before the walker (and any fragment classifier) runs. Two further findings refined the design: G3 has a **second** walker inliner consumer ([`walker.py::_selected_scalar_names`][walker], the FK-id-elision-safety analyzer) the original single-call-site framing missed; and the "known sibling concrete type" lookup needs a **non-Relay** registry primitive (the existing [`registry.definition_for_graphql_name`][registry] is Relay-Node-only and raises on miss / ambiguity). **Decision (maintainer, this review): G3 ships no runtime code in spec-035.** Slice 3 moves to a follow-up *abstract-return optimizer entry* card (the [`BACKLOG.md`][backlog] `polymorphic_interface_connections` work, or a dedicated card) that will own the whole abstract-entry contract (target-model resolution, origin / cache identity, possible-concrete-type enumeration, strictness, and the registry-only narrowing) and implement G3 with real production reachability and red/green tests. The G3 analysis here ([Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing) / [Decision 7](#decision-7--g3--narrow-do-not-multi-plan), the [G3 test plan][spec-035-g3-test-plan]) is retained verbatim as **carry-forward requirements**. spec-035 ships **G1 (shipped) + G2 + the doc wrap**. Also corrected in this revision: Decision 5's FK-id-elision safety argument now handles the consumer-`.only()` case (a consumer projection can defer the FK column even when the optimizer suppresses its own `.only()`; see [Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations)).
- **Revision 4** — post-implementation reconciliation (2026-06-16), after the `DONE-035-0.0.10` build cycle landed G2 + the doc wrap and a rigorous implementation review followed. **G2 shipped** in this card: the operation-type `enable_only` projection gate derived in [`walker.py::_enable_only_for_operation`][walker] / [`plan_optimizations`][walker] and threaded through every projection writer, plus the [Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations) FK-id-elision loaded-check in [`types/resolvers.py::_build_fk_id_stub`][types-resolvers]. **Slice 4 completed** (GLOSSARY G1+G2 appends, README / `docs/README.md` "what the optimizer will not touch" notes, the `CHANGELOG.md` `[Unreleased]` bullets, and the kanban card moved to `DONE-035-0.0.10`). **G3 stays deferred** (no runtime code). This revision reconciles the document from in-progress to **completed** voice — the Status line, [Slice checklist][spec-035-slice-checklist] (Slices 2 and 4 now ticked), [Problem statement][spec-035-problem-statement] / [Current state][spec-035-current-state], and [Definition of done][spec-035-dod] describe the shipped state, and the stale pre-build grep evidence (`OperationType` "returns nothing") is corrected: `OperationType` now lives in [`walker.py::_enable_only_for_operation`][walker]. The card's `SpecDoc` reference is kept on the **live** working path `docs/spec-035-optimizer_hardening-0_0_10.md` — the spec is not archived per-card; the `docs/SPECS/` relocation is the next spec author's [`docs/SPECS/NEXT.md`][next] Step 8 batched sweep ([`AGENTS.md`][agents]). `scripts/check_spec_glossary.py` re-run after these edits → `OK`.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-035-d1].

### Justification (moved from the spec)

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `DONE-035-0.0.10`, so `<NNN>` is `035` and `<0_0_X>` is `0_0_10`.
- The topic slug is `optimizer_hardening` — the exact suffix the card's Definition of done names ("numbered to the card at implementation time, suffix `optimizer_hardening-0_0_10`") and the path the card's "Files likely touched" pre-pins (`docs/SPECS/spec-<NNN>-optimizer_hardening-0_0_10.md`).

### Alternatives considered (and rejected)

- **The card's `docs/SPECS/`-rooted path.** The card DoD writes the spec into `docs/SPECS/` directly; the [`docs/SPECS/NEXT.md`][next] flow instead authors new specs at `docs/` root and archives prior specs into `docs/SPECS/` (Step 8). The active spec lands at `docs/spec-035-…`; the card's `docs/SPECS/` path is the eventual archive home, not the authoring location. Recorded, not silently reconciled, per the NEXT.md boundary rule.
- **Topic slug `optimizer_robustness` / `optimizer_guards`.** Rejected: the card DoD pins `optimizer_hardening` verbatim; matching it keeps the spec-reference link in the kanban `SpecDoc` stable.

### Changes this Decision underwent

- **Revision 1** pinned the canonical structured filename and the `optimizer_hardening` topic slug against the card DoD's `docs/SPECS/`-rooted path. Nothing later reopened it.
- **Revision 4** re-affirmed the authoring location, recording that the card's `SpecDoc` reference stays on the live working path and that the `docs/SPECS/` relocation is the next spec author's batched sweep. That statement has since been overtaken by the sweep itself — see [Post-ship divergences](#post-ship-divergences-spec-vs-head) item 7.

## Decision 2 — Card-scope boundary: G1 + G2 ship (G3 deferred); the performance findings and the deferred-audit catalogue are out

Spec: [Decision 2 — Card-scope boundary: G1 + G2 ship (G3 deferred); the performance findings and the deferred-audit catalogue are out][spec-035-d2].

### Justification (moved from the spec)

the audit produced a 36-capability inventory; the card deliberately scoped three guards and parked the rest with explicit dispositions. The spec preserves those dispositions verbatim so a future reader sees which omissions are decisions (prefetch merging) versus deferrals (annotation hints, and now G3) versus other-card ownership (windowed prefetch).

### Alternatives considered (and rejected)

**fold the cheap deferred findings (e.g. the `disabled()` contextvar) into this card.** Rejected: grafting "while I'm here" extras is the scope-creep [`START.md`][start] warns against, and each deferred finding has its own design surface — the same reasoning that, in reverse, justifies *removing* G3 once it proved to need a whole abstract-entry design surface of its own.

### Changes this Decision underwent

- **Revision 1** scoped the card to the three audited guards and parked the rest of the 36-capability inventory with explicit dispositions.
- **Revision 3** moved G3 into that parked set as a recorded deferral. The Decision's `As of Revision 3` framing was deleted by this extraction: the Decision now states the current scope directly, which is what the chronology was standing in for.

## Decision 3 — G1 — evaluated-queryset guard: `_result_cache` early-return in `_optimize`

Spec: [Decision 3 — G1 — evaluated-queryset guard: `_result_cache` early-return in `_optimize`][spec-035-d3].

### Justification (moved from the spec)

this is upstream's execution-state check, minus the flag bookkeeping the package's O3 root gate makes redundant. Upstream guards twice (`_result_cache is None` at the resolve hook AND `is_optimized(qs) or qs._result_cache is not None` inside `optimize()`) because its optimizer can run at nested resolvers and must stay idempotent across `_clone` calls; the package's optimizer runs only at the operation root (`info.path.prev is None`), so a single execution-state check at the one entry is complete. It extends the [`spec-004`][spec-004] B8 "respect what the consumer already did" posture from optimization state (consumer `.only()` / `select_related` wins) to execution state (consumer-evaluated queryset is left alone).

### Alternatives considered (and rejected)

- **Port the full upstream two-part guard (flag + `_clone` monkeypatch).** Rejected: monkeypatching `QuerySet._clone` couples the package to a Django private and exists upstream only to make a nested-capable optimizer idempotent — a problem the O3 root gate already solves. Carrying machinery for a scenario the architecture forbids is dead weight.
- **Guard inside `apply_to` (shared with the connection field) instead of `_optimize`.** Rejected: the connection field's queryset is framework-built and never evaluated, so guarding the shared tail would add a per-connection `getattr` check that can never fire — and would muddy the contract that `apply_to` optimizes whatever pre-built queryset it is handed. The risk is specific to consumer-returned querysets, which only reach `_optimize`.
- **Detect evaluation by `bool(qs._result_cache)` / `len`.** Rejected: `_result_cache` is `None` until evaluated and a (possibly empty) list after — `is not None` is the exact, allocation-free signal upstream uses; truthiness would mis-handle an evaluated-but-empty queryset.

### Changes this Decision underwent

- **Revision 1** pinned the guard, its two-directional placement, and the execution-state-only port (no `is_optimized` flag, no `_clone` monkeypatch).
- **Revision 2** reframed the Decision from pending work to shipped-and-recorded after verifying against the live checkout that commit `d1dea2fd` had already landed the guard plus four tests. The same pass established that Revision 1's grep claim — that `_result_cache` was absent from the package — was false.
- **The `035` reconciliation cycle (Slice 3)** narrowed the Decision's scope statement to the `_optimize` middleware path and named the `spec-045` visibility-boundary carve-out that the original unconditional wording did not anticipate — see [Post-ship divergences](#divergence-8--decision-3-g1s-contract-was-narrowed-at-the-visibility-boundary-by-spec-045) item 8. The same cycle replaced the Decision's live-coverage waiver in the Slice 1 test plan (item 3).

## Decision 4 — G2 — operation-type gating of `.only()`: suppress `only_fields` for non-`QUERY` operations at plan-build time

Spec: [Decision 4 — G2 — operation-type gating of `.only()`: suppress `only_fields` for non-`QUERY` operations at plan-build time][spec-035-d4].

### Justification (moved from the spec)

G2 is sequencing-critical (the `0.0.11` mutations cohort makes mutation root querysets mainstream); landing it at plan-build time is the cache-correct placement (the printed-AST key already separates operations, so no key change is needed and the suppression is cached, not recomputed per request). `select_related` / `prefetch_related` stay on because they never carry the deferred-field hazard — they shape *which related rows load*, not *which columns of a row* are deferred.

### Alternatives considered (and rejected)

- **Apply-time gate in [`plans.py::OptimizationPlan.apply`][plans].** Rejected: a plan built with `only_fields` then conditionally not applying them at apply time means the cache stores a `only_fields`-carrying plan that two operations (query and mutation) would want to apply differently — but the cache already separates them by printed-AST key, so building the right plan per key (build-time) is both simpler and avoids an apply-time branch on `info.operation`. The card pins build-time as preferred for exactly this cacheability reason.
- **Block scalar appends only, relying on `_ensure_connector_only_fields`'s empty-`only_fields` no-op to suppress the rest.** Rejected: this was the original draft's mechanism and it leaks. [`_record_relation_access`][walker] appends FK connector columns on relation traversal, making `only_fields` non-empty *independently of* scalar leaves — so a mutation selecting a relation would still get a non-empty projection and the connector helper would not no-op. And [`_project_scalar_only_window`][nested-planner] applies `.only(...)` directly without populating `only_fields`, so no empty-set check reaches it. The gate must be threaded through all four projection writers, not just the scalar path.
- **Root-only suppression.** Rejected: leaves nested prefetched children carrying deferred-field sets under a mutation, reintroducing the deferred-refetch hazard one level down; upstream gates `.only()` operation-wide.
- **Suppress `select_related` / `prefetch_related` too under non-`QUERY`.** Rejected: those carry no deferred-field hazard and dropping them would reintroduce N+1s on a mutation's response selection — the hazard is specific to column deferral.

### Changes this Decision underwent

- **Revision 1** pinned the plan-build-time placement, the plan-wide (root + nested) suppression scope, and the zero-key-change cache-safety argument.
- **An earlier draft of this Decision** (the revision block records no round for it) gated only the scalar-leaf appends and relied on `_ensure_connector_only_fields`'s empty-`only_fields` no-op to suppress the rest. That mechanism leaks, and the leak is why the Decision's body enumerates all four projection writers rather than naming a single gate site: `_record_relation_access` makes `only_fields` non-empty independently of scalar appends, and `_project_scalar_only_window` applies `.only(...)` without ever touching `only_fields`. The leaking mechanism survives above as a rejected alternative; the enumeration that replaced it stayed in the spec under the implementation-relevant carve-out, because a builder who never reads it writes the leaking version.

## Decision 5 — G2 — FK-id elision stays enabled under non-`QUERY` operations

Spec: [Decision 5 — G2 — FK-id elision stays enabled under non-`QUERY` operations][spec-035-d5].

### Justification (moved from the spec)

elision's correctness precondition is "the FK column is loaded on the parent row." G2 guarantees that *for optimizer-owned projections* but consumer-wins diffing can still defer it, so the precondition must be **checked**, not assumed. Keeping elision on (with the guard) preserves the B2 advantage and avoids a needless join on the common fully-loaded path; the guard only changes the rare consumer-`.only()`-defers-the-FK path, turning a silent lazy-load into a visible, strictness-honest fallback.

### Alternatives considered (and rejected)

**disable elision entirely under non-`QUERY` ops.** Rejected: it does not address the real hazard (which is consumer projection, not operation type — it bites under `QUERY` too) and trades a correct single-query elision for an unnecessary join on every fully-loaded mutation row. **Drop all elisions after diffing whenever the consumer applied `.only()`.** Rejected as insufficient on its own: the elision branch recorded no `select_related` fallback, so merely dropping the elision still leaves the relation needing a resolve path — the resolver-time loaded-check is what makes the fallback honest.

### Changes this Decision underwent

- **Revision 1** resolved the card's open decision in favour of keeping FK-id elision enabled under non-`QUERY` operations.
- **Revision 3** found the safety hole the first draft missed — a consumer-returned `.only(...)` survives B8 consumer-wins diffing and can defer the FK column even when the optimizer suppresses its own projection, and strictness stays silent because the relation is recorded planned — and added the resolver-time loaded-check with a loud fallback. The hazard mechanism itself stayed in the spec: it is the reason the loaded-check exists at all. Only the `(the safety hole the first draft missed)` and `(the follow-up the first draft owed)` framings were removed from those two paragraphs.
- **The `035` reconciliation cycle (Slice 3)** rewrote the implementation rule to state the three-part shipped mechanism — the `_fk_attname_is_deferred` probe, the `_FK_ELISION_UNSAFE` sentinel that signals rather than reads, and `_check_n1`'s keyword-only `force_unplanned` bypass without which the "loud" fallback is silent. The Decision understated its own mechanism rather than misstating it; see [Post-ship divergences](#post-ship-divergences-spec-vs-head) item 2.

## Decision 6 — G3 — registry-only fragment type-condition narrowing

Spec: [Decision 6 — G3 — registry-only fragment type-condition narrowing][spec-035-d6].

### Justification (moved from the spec)

`type_condition` is already carried through the substrate (the inline-fragment shell, the `is_fragment` duck-type); G3 is the first code to *match* it against the planning type. Resolving the match through the registry (the type's `graphql_type_name` and the union of its declared `definition.interfaces` + MRO-inherited interface bases) reuses the exact metadata [`Schema audit`][glossary-schema-audit] already descends and keeps the walk free of per-request schema introspection. Confining the accept set to the planning type's own name and the interfaces it implements — and excluding the shared model's primary type name — keeps the narrowing faithful to GraphQL type-condition semantics (a condition matches the runtime type or an abstract type it belongs to, not the Django model behind it). Threading the classifier only through the walker (not the shared primitive's other callers) contains the change to the one path that plans relations.

### Alternatives considered (and rejected)

- **graphql-core schema lookup of possible types per fragment.** Rejected: violates the B7 invariant (zero per-request Django / schema introspection); the registry already answers "does this planning type satisfy this type condition" from finalized metadata.
- **Accept the model's registered primary type name (the original draft's third accept rule).** Rejected: a `type_condition` matches the runtime GraphQL type, not the Django model. Accepting the primary name would inline a `... on PrimaryType` fragment while planning a *secondary* type over the same model, planning fields / relations the secondary may not expose and crossing distinct `get_queryset` / `relation_shapes` / field-override contracts — the exact over-planning G3 removes. The plan cache already keys on the origin Strawberry type, so there is no cache reason to blur primary and secondary. When the primary type itself roots the walk, its own `graphql_type_name` accepts the fragment anyway, so dropping the rule loses no valid match.
- **Collect interface names from a single source (either `definition.interfaces` alone or `origin.__mro__` alone).** Rejected: the two sources are **complementary, not redundant**, so either alone is incomplete. `definition.interfaces` is the normalized **declared** `Meta.interfaces` tuple ([`types/base.py::_validate_interfaces`][types-base] stores it verbatim and injects nothing); interfaces implemented by **direct class inheritance** (`class Foo(DjangoType, relay.Node)`) appear **only** in `origin.__mro__`, never in `definition.interfaces` (per [`_is_relay_shaped`][types-base]'s `... or issubclass(cls, relay.Node)` arm). A `definition.interfaces`-only collection silently misses every inherited interface (re-introducing the silent-N+1 for a fragment conditioned on an inherited interface); an MRO-only collection misses declared ones. The accept set must be the **union** of both arms.
- **Skip every non-matching condition whole, including unknown composite / union conditions.** Rejected: a union or unrecognized-abstract condition can wrap a nested `... on <ConcreteType>` fragment that *does* match the planning type; skipping the whole subtree under-plans that valid nested fragment. The unknown-composite fallback recurses into nested fragments (re-classifying each) while declining the unknown fragment's own direct fields — conservative in both directions (no under-plan of a valid nested match, no over-plan of unconfirmable direct fields).
- **Skip only the unknown-name fields, not the whole fragment subtree (for sibling concrete types).** Rejected: a sibling-type fragment can name a relation that happens to exist on the planning type too (failure mode (b)); skipping field-by-field on the unknown-name guard misses the same-named-relation over-fetch. For a *known sibling concrete type* the non-matching fragment subtree is skipped whole — that is the correct granularity (distinct from the unknown-composite case above, which recurses).

### Changes this Decision underwent

- **Revision 1** pinned the registry-only narrowing, the accept set (own `graphql_type_name` plus implemented interfaces, never the model's primary type name), and the no-per-request-introspection constraint.
- **The tri-state classifier and the two-source interface collection** replaced an earlier boolean-predicate, single-source shape during authoring; the revision block records no round for the change. Both requirements stayed in the spec under the implementation-relevant carve-out — a boolean predicate cannot express `RECURSE_FRAGMENTS_ONLY`, and either collection source alone silently drops one kind of interface.
- **Revision 3** deferred G3 entirely and added the R1-R3 carry-forward requirements: the abstract-return production-entry contract that must exist first, the second walker inliner consumer `_selected_scalar_names` the original single-call-site framing missed, and the non-Relay registry name-resolution plus ambiguity contract. The `(added in Revision 3)` tag on that subsection's heading was removed by this extraction.

## Decision 7 — G3 — narrow, do not multi-plan

Spec: [Decision 7 — G3 — narrow, do not multi-plan][spec-035-d7].

### Justification (moved from the spec)

the package's plan cache stores one plan per `(document, target_model, origin)` key; a per-concrete-type re-walk would either multiply cache entries or build a union plan that re-introduces the over-projection G3 removes. The registry narrowing achieves the correctness outcome (sibling branches don't plan; same-named relations plan only for the matching branch) at one extra set-membership check per fragment, preserving B7 precompute and the single-plan-per-key contract. Upstream multi-plans because its optimizer lacks the package's class-creation-time metadata and global plan cache — the package doesn't need to.

### Alternatives considered (and rejected)

**adopt upstream's per-concrete-type re-walk for completeness.** Rejected: it fights the package's cache contract and B7 advantage for a correctness outcome the narrowing already achieves; the card is explicit ("we narrow, we do not multi-plan").

### Changes this Decision underwent

- **Revision 1** pinned the narrow-do-not-multi-plan posture against upstream's per-concrete-type re-walk.
- **Revision 3** established the reachability finding and recorded the maintainer's decision to defer G3 from the card. It also retracted the earlier draft's claim that a consumer-authored multi-implementor interface field "would be mis-walked today": it would be passed through unoptimized, not mis-walked, because `registry.model_for_type` returns `None` for the abstract origin and `_optimize` returns before the walker runs. The bug only appears once an abstract-return entry contract exists to make the optimizer walk such a field — requirement R1 in [Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing). That retraction parenthetical moved here; the surrounding reachability contract stayed in the spec.

## Decision 8 — Module and test locations: no new module; G1 + G2 in `tests/optimizer/`, G3 tests deferred

Spec: [Decision 8 — Module and test locations: no new module; G1 + G2 in `tests/optimizer/`, G3 tests deferred][spec-035-d8].

### Justification (moved from the spec)

the source guards are package-internal optimizer mechanics, and tests mirror source one-to-one per [`docs/TREE.md`][tree]; the live-HTTP-priority rule does not force a live test here because no shipping-this-card behavior is live-reachable yet (G1 is execution-state-only; G2's consumer surface arrives with the `0.0.11` mutation cohort). G3's only "live-reachable" shape (a matching-type fragment under `allLibraryGenresConnection`) tests behavior that **already works today** without G3, so it is no-regression coverage, not proof — and it travels with the deferred G3 work.

### Alternatives considered (and rejected)

- **Keep a live G3 test in this card as evidence G3 works.** Rejected: the only live-reachable G3 shape is a *matching-type* fragment, which plans today with no narrowing — it proves nothing about the sibling / union narrowing G3 adds. Carrying it here would imply G3 ships behavior it does not.
- **A new `tests/optimizer/test_hardening.py`.** Rejected: the G1 + G2 pins extend the contracts the predicted files already cover (extension behavior, walker plan content); co-locating them beside the existing extension / walker coverage keeps the one-to-one mirror and the regression context together.

### Changes this Decision underwent

- **Revision 1** pinned the no-new-module, tests-mirror-source placement and the package-internal coverage reason.
- **Revision 3** moved G3's source edits and its whole test plan to the follow-up card, leaving the live `GenreType` matching-type test recorded as no-regression coverage rather than a behavioural proof.

## Decision 9 — Version bumps are owned by the joint `0.0.10` cut

Spec: [Decision 9 — Version bumps are owned by the joint `0.0.10` cut][spec-035-d9].

### Justification (moved from the spec)

the exact precedent of [`spec-034`][spec-034] Decision 13 and [`spec-033`][spec-033] Decision 12, and the [`docs/SPECS/NEXT.md`][next] Step 6 mandate for multi-card patch versions — when multiple cards target one patch, the version bump is the joint cut's, not any single card's.

### Alternatives considered (and rejected)

**bump in Slice 4 since this card may land last of the two.** Rejected: landing order between `034` and `035` is a maintainer scheduling fact, not a spec fact; the cut is a maintainer release act with its own checklist regardless of which card's PR merges last.

### Changes this Decision underwent

- **Revision 1** pinned the joint-cut version boundary shared with [`DONE-034-0.0.10`][kanban]. Nothing later reopened it.

## Risks and open questions

The spec's whole `## Risks and open questions` body. It is a build-time deliberation instrument — each item pairs a preferred answer for the cut with a fallback if implementation proved the preferred answer wrong — so the body moved and the spec keeps the heading and a pointer here. Nothing was held back. Two items are card-citation corrections whose *conclusions* already live in Decisions 3 and 6; only the deliberation that reached them is here. It moved verbatim and has not been corrected since.

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **G2 FK-id elision under non-`QUERY` operations (the card's open decision).** Preferred answer ([Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations)): keep elision enabled — with `only` suppressed the full row loads, the FK column is present, elision is correct and avoids a join. Fallback: if a real consumer surfaces a deferred-elision interaction under mutations (none is known, and the elision-correctness precondition is strictly better satisfied with `only` suppressed), gate elision alongside `.only()` — a one-line addition to the same operation-type branch, test-pinned either way.
- **G2 nested-plan `only_fields` suppression scope.** Preferred answer: suppress plan-wide (root + nested child plans), matching upstream's operation-wide `enable_only`. Fallback: if a consumer relies on nested child-row projection under a mutation (and accepts the deferred-refetch hazard on those children), root-only suppression is a contained narrowing — but it reintroduces the exact hazard one level down, so plan-wide is the safe default.
- **G3 connection-wrapped fragment narrowing.** Preferred answer: narrowing happens at each `_walk_selections` entry (the node model's planning type), so connection-wrapped fragments narrow without touching the extraction helpers. Fallback: if a test shows the extraction helpers ([`named_children`][selections] / [`node_children_with_runtime_prefix`][selections]) flatten a fragment before the node walk re-resolves type, thread the same classifier into those helpers — a contained extension of the Decision 6 mechanism.
- **G3 `... on PrimaryType` fragment when planning a secondary type.** Resolved ([Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing)): the primary type name is **not** in the accept set — a `... on PrimaryType` fragment is skipped when a *secondary* type roots the walk (a type condition matches the runtime GraphQL type, not the shared Django model) and inlines only when the primary type itself roots the walk via its own `graphql_type_name`. Pinned by the secondary-return regression. Fallback: none needed — the strict reading is the GraphQL-correct one and removes the over-planning the permissive model-identity match would have reintroduced (planning fields / relations the secondary may not expose, crossing distinct `get_queryset` / field-override contracts).
- **G3 interface-name collection source and unknown abstract conditions.** Resolved ([Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing)): implemented-interface names are the **union** of two complementary sources — `definition.interfaces` (the normalized **declared** `Meta.interfaces`, stored verbatim by [`types/base.py::_validate_interfaces`][types-base]; it injects nothing) and the interfaces reached by **direct class inheritance**, found by walking `origin.__mro__`. These are *not* primary-plus-fallback: per [`_is_relay_shaped`][types-base], a type Relay-Node-shaped via `class Foo(DjangoType, relay.Node)` has `relay.Node` only in its MRO and never in `definition.interfaces`, so reading either source alone silently drops one kind of interface (the declared, or the inherited). Both arms are required. An unknown composite / union condition recurses into nested fragments (re-classifying each) while declining its own direct fields rather than skipping the subtree whole. Fallback: if neither source records an interface a fragment names, the condition is treated as an unknown composite (recurse-without-direct-fields), never a silent whole-subtree skip.
- **Card-citation correction: the manager-coercion seam.** The card's line cite for the manager coercion the G1 guard must follow is stale; the live home is the symbol [`utils/querysets.py::normalize_query_source`][querysets], called from [`extension.py::_optimize`][extension] (the cite predates the DRY consolidation). Preferred answer: ground the guard on `normalize_query_source` (the live seam); the placement contract ("after coercion, before `diff_plan_for_queryset`") is unchanged. Fallback: none needed — the seam moved, not the contract.
- **Card-citation correction: the fragment-inlining seam.** The card's line cites for the fragment inlining and the `type_condition` marker are stale; the live primitive is [`selections.py::included_field_selections`][selections] (inlined from [`walker.py::_walk_selections`][walker]) with the unknown-name `continue` guard in the same function and the marker uses in [`selections.py`][selections]. Preferred answer: ground G3 on the live `selections.py` primitive. Fallback: none needed — the [`DONE-033-0.0.9`][kanban] connection work moved the inlining into the shared `selections.py` substrate; the gap (unconditional inlining) is unchanged.
- **Upstream parity is a behavior contract, not a line contract.** The 2026-06-11 audit recorded specific [`strawberry_django/optimizer.py`][upstream-optimizer] locations as evidence; this spec treats the *behavior* each names — the resolve-hook `_result_cache is None` guard, the `enable_only and operation == QUERY` gate, the `get_possible_concrete_types` per-type re-walk — as the parity contract, referenced by the stable upstream permalink rather than a checkout line number (which drifts with every upstream release). The behavior descriptions in the [parity checkpoint][spec-035-parity-checkpoint] and the [Borrowing posture][spec-035-borrowing-posture] are the contract; the audit's line evidence is archival. Fallback: none needed.
- **No new module / no settings key.** The guards are edits to three existing optimizer modules; no `permissions.py`-style new module and no `DJANGO_STRAWBERRY_FRAMEWORK` entry. Preferred answer: keep it that way. Fallback: none anticipated.

## Post-ship divergences (spec vs. HEAD)

Not moved text — this cycle's own record. **Nine** places where the shipped repo has moved away from what the spec said. Each names the owning Decision or section, what the spec said, what the repo does, the commit that changed it where one did, and why. **Slice 3 of this cycle wrote every correction into the spec body**, stated directly and without chronology; this section is where the explanation lives afterwards. Items 1-6 are the build plan's [`### Deviations later work introduced`][build-035] enumeration, re-derived against `HEAD` by the Slice 1 extraction pass; item 7 is that pass's spec status-line re-verification. Items 8 and 9 were found by the Slice 3 reconciliation pass itself and carry their own subheadings, the first two entries here long enough to need them.

1. **[Decision 4][spec-035-d4] — `_project_scalar_only_window` no longer lives in `walker.py`.** Commit `991d5120` (2026-07-13, "fix(optimizer): isolate nested planning") relocated the function to [`optimizer/nested_planner.py::_project_scalar_only_window`][nested-planner]; `walker.py` keeps a module-level alias (`_project_scalar_only_window = _nested_planner._project_scalar_only_window`), so the symbol still resolves at the old path but is defined at the new one. The G2 gate travelled with it intact — `walker.py::_plan_connection_relation` forwards `enable_only` to [`nested_planner.py::plan_connection_relation`][nested-planner] (which `walker.py` imports under the local alias `_plan_nested_connection_relation`), and that forwards it to the relocated writer, whose body opens on the closed-gate return — so the contract held throughout and only the citations were stale. Why it mattered: the enumeration of the four projection writers is the held-back implementation-relevant passage above, and a reader who opened `walker.py` to check the fourth writer found an alias rather than the gate. The pre-cycle spec carried **seven** reference-style citations of the symbol and all seven targeted `walker.py`. Six of them are still in the spec and all six now target [`nested_planner.py`][nested-planner]; the spec's four remaining mentions are path-free code spans, so no site in it names `walker.py` as the definition. The seventh left the spec with Decision 4's rejected alternative and lives in this file, above — out of reach of a spec-only sweep, and now pointed at `nested_planner.py` like the rest.
2. **[Decision 5][spec-035-d5] — the loud fallback needed machinery the Decision did not name.** The spec said the elision stub "falls back **loudly** ... so strictness sees the access" and stopped there. That outcome is unreachable on those words alone: the elision branch recorded the relation in `planned`, so `types/resolvers.py::_check_n1` short-circuits on the planned key and stays silent. The shipped implementation adds a keyword-only `force_unplanned` on [`_check_n1`][types-resolvers] that bypasses that short-circuit, plus the [`_FK_ELISION_UNSAFE`][types-resolvers] sentinel returned by `_build_fk_id_stub` and the [`_fk_attname_is_deferred`][types-resolvers] probe that detects the deferred column. The Decision understated its own mechanism rather than misstating it; its implementation rule now states all three parts — detect, signal rather than read, and make the fallback strictness-visible.
3. **[Decision 8][spec-035-d8] and the Slice 1 test plan — the G1 live-coverage waiver was reversed.** The spec declined a live G1 test on the ground that "adding a permanent fakeshop resolver that models it would put an anti-pattern on the example surface purely to host a test", and stated that no future card makes the branch consumer-facing so no live-test obligation is carried forward. Later work added exactly that resolver — [`examples/fakeshop/apps/library/schema.py::Query.all_library_branches_eager_eval`][library-schema] — and the live pin [`test_library_api.py::test_library_evaluated_queryset_not_re_executed_over_http`][test-library-api]. The waiver had become a false statement about the repo. The Slice 1 test plan now records the live pin and the resolver that hosts it; the reasoning that produced the waiver (evaluate-then-return is a consumer anti-pattern) is what belongs here rather than in the spec.
4. **Slice 2 test plan and [Out of scope][spec-035-out-of-scope] — the G2 live-test handoff was discharged.** The spec recorded the live `/graphql/` proof as a standing obligation on "the first card that adds such a mutation". The `0.0.11` mutations cohort discharged it in `examples/fakeshop/test_query/test_products_api.py` for both the model and the serializer flavour, and [`mutations/resolvers.py`][mutations-resolvers], `forms/resolvers.py` and `rest_framework/resolvers.py` each cite the G2 gate in their pipeline docstrings. The handoff is satisfied rather than outstanding, and the Slice 2 test plan names both discharging tests.
5. **Implementation plan (staged-anchor paragraph), owned by the [Decision 6][spec-035-d6] / [Decision 7][spec-035-d7] deferral — the carry-forward anchor retarget landed at one site of five.** The spec claimed "the `TODO(spec-035 Slice 3)` comments at the [`included_field_selections`][selections] inliner, the [`_walk_selections`][walker] planning seam, and the `_selected_scalar_names` second-consumer site" — three anchors. There were five on disk, and only [`selections.py::included_field_selections`][selections] had been retargeted to `TODO(BACKLOG polymorphic_interface_connections — the abstract-return optimizer entry card)` by commit `dd8dc0b3`. Commit `471d4c6b` ("drop build-process vocabulary from code comments") then stripped ` Slice 3` from the two `walker.py` anchors, which the standing no-process-provenance rule exempts: [`AGENTS.md`][agents] requires a staged anchor to name its doc **and** slice. The spec's claim was stale on both the count and the form. Slice 2 of this cycle retargeted the in-scope remainder, and the staged-anchor paragraph now names all five sites carrying the `TODO(BACKLOG ...)` form. One `TODO(spec-035)` still stands in [`test_library_api.py`][test-library-api], baseline-dirty and outside this cycle's scope.
6. **[Current state][spec-035-current-state] — a loose citation, unchanged since `0.0.10`.** The Current-state bullet attributed `apply_connection_optimization` to [`DjangoConnectionField`][glossary-djangoconnectionfield]. It is and always was a module-level function in [`optimizer/extension.py`][extension], re-exported and called from `connection.py`. Not later drift — an authoring-time imprecision, corrected in place: the bullet now names the module-level function and says it is not a method on the field.
7. **[Decision 1][spec-035-d1], the [Doc updates][spec-035-doc-updates] Slice-4 card-wrap bullet, and [Definition of done][spec-035-dod] items 1 and 10 — the spec is archived, and four sites said it was not.** Decision 1 stated "The spec file lives at **`docs/spec-035-optimizer_hardening-0_0_10.md`**"; DoD item 1 repeated that path twice, once as prose and once inside a `--spec` argument, so the verification command as written exited 2 with a missing-file error; the Doc-updates card-wrap bullet and DoD item 10 both pinned the card's `SpecDoc` reference to the "**live** working path", and Revision 4 records the same intent. The [`docs/SPECS/NEXT.md`][next] Step 8 batched sweep has since run: the spec is at `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` with its [`-terms.csv`][spec-035-terms] companion — and now this file — at `docs/SPECS/appx/`. The statements were true when written and describe a per-card policy that still holds; what was false is the present-tense claim about where the file is. All four sites now name the archived path, and DoD item 1's verification command exits 0.

### Divergence 8 — [Decision 3][spec-035-d3]: G1's contract was NARROWED at the visibility boundary by `spec-045`

Found by the Slice 3 reconciliation pass, after items 1-7 were written; it is not in the build plan's enumeration and not a restatement of any item above.

**What the spec said.** G1 was an unconditional pass-through: an already-evaluated root queryset is never re-executed by the optimizer. **What the repo does.** That holds of the `_optimize` middleware path and stops there. Across a [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook] the sealed-execution boundary deliberately discards the evaluated state — [`utils/querysets.py`][querysets] #"an already-evaluated source seals to a fresh," records that the seal rebuilds the source as a fresh framework-owned queryset and never copies `_result_cache`, so cached rows never reach the hook, and [`utils/querysets.py`][querysets] #"is not immutability, so a hook can mutate the sealed source's" records that the hook's result is ALWAYS re-sealed rather than identity-fast-pathed, because object identity is not immutability and a hook that held the sealed source can inject a cache into it and return the same object.

**Why the narrowing wins over G1's guarantee, and why it is not a regression.** The two contracts point opposite ways at exactly one place, and the tie-break is authority over rows. G1 optimizes: it declines to re-run SQL the consumer already ran. The seal authorizes: a queryset the framework did not build is untrusted, and a row cache attached to it has never passed the visibility predicate. Honoring the cache across the hook would serve rows the hook never authorized — a correctness-for-cheapness trade G1 was never entitled to make, since G1's own justification (see [Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize) above) is "respect what the consumer already did", and the visibility hook exists precisely because what the consumer did is not the last word. So the boundary is not a G1 defect and not a bug to fix; it is a scope that G1's original text did not name because `spec-045`'s sealed-execution queryset did not exist at `0.0.10`.

**Rejected: leaving the unconditional wording and treating the carve-out as an implementation detail.** It reads as a guarantee a reader can rely on, and the one case where it does not hold is the security-relevant one — the failure mode is a consumer who believes their evaluated queryset survives a visibility hook. A contract that is wrong exactly where the stakes are highest is worse than one that names its boundary.

**Rejected: restating the boundary only in the `## Edge cases and constraints` list.** Edge cases qualify a contract for a reader who already found it; the G1 statements in [Goals][spec-035-goals] and Decision 3 are where a reader forms the belief. The correction is stated at the Decision and echoed in the edge case, not filed away in one place.

[`docs/README.md`][docs-readme] already carried the unified consumer-facing form ("an already-evaluated root queryset passes through unchanged rather than being re-executed — except across a `get_queryset` visibility hook, where it is refreshed to a lazy clone before it can serve rows (an intentional security carve-out)"), so the spec was the last document still stating the unqualified version.

### Divergence 9 — [Definition of done][spec-035-dod] item 1: the "Spec + companion CSV" grouping predates this file

The DoD grouped the spec with one sibling because one sibling existed. This file is the second, created by Slice 1 of the `035` reconciliation cycle, and a completion contract that names only the CSV leaves a future reader no way to learn from the spec that the deliberative layer was extracted rather than deleted. The grouping and item 1 now name both siblings. Nothing about the CSV's own contract changed.

## Non-Decision deliberation

Findings and provenance that belong to no single Decision.

- **Revision 2 — a grep claim that was false when it was written.** Revision 1 recorded a grep establishing that `_result_cache` was absent from the package. It was not: commit `d1dea2fd` had already landed the G1 guard before the spec was finalized. Revision 2 verified this against the live checkout and reframed Slice 1 and [Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize) as shipped-and-recorded. The other two clauses of the same grep claim — that `OperationType` and a *matched* `type_condition` were genuinely absent — held. The lesson belongs to no Decision: a spec authored across a moving checkout can record a gap the checkout has already closed, and the correction is a re-verification, not a re-design.
- **The two card-citation corrections were recorded rather than silently reconciled.** The card's line cites for the manager-coercion seam and for the fragment-inlining seam both predate DRY consolidations that moved the code, so the spec grounded G1 on [`utils/querysets.py::normalize_query_source`][querysets] and G3 on [`selections.py::included_field_selections`][selections] and said so. In both cases the seam moved and the contract did not. Recorded here because the practice — correct the cite in the spec, name the correction in the deliberation — is the reason a reader can tell a stale citation from a changed decision.
- **Upstream parity is a behaviour contract, not a line contract.** The 2026-06-11 audit recorded specific `strawberry_django/optimizer.py` line locations as evidence; the spec treats the *behaviour* each names as the parity contract and cites the stable upstream permalink instead, because a checkout line number drifts with every upstream release. The full item is in [Risks and open questions](#risks-and-open-questions) above.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[backlog]: ../../../BACKLOG.md
[kanban]: ../../../KANBAN.md
[start]: ../../../START.md

<!-- docs/ -->
[docs-readme]: ../../README.md
[glossary-djangoconnectionfield]: ../../GLOSSARY.md#djangoconnectionfield
[glossary-get-queryset-visibility-hook]: ../../GLOSSARY.md#get_queryset-visibility-hook
[glossary-schema-audit]: ../../GLOSSARY.md#schema-audit
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-004]: ../spec-004-optimizer_beyond-0_0_3.md
[spec-033]: ../spec-033-connection_optimizer-0_0_9.md
[spec-034]: ../spec-034-permissions-0_0_10.md
[spec-035]: ../spec-035-optimizer_hardening-0_0_10.md
[spec-035-borrowing-posture]: ../spec-035-optimizer_hardening-0_0_10.md#borrowing-posture
[spec-035-current-state]: ../spec-035-optimizer_hardening-0_0_10.md#current-state
[spec-035-d1]: ../spec-035-optimizer_hardening-0_0_10.md#decision-1--spec-filename-and-canonical-naming
[spec-035-d2]: ../spec-035-optimizer_hardening-0_0_10.md#decision-2--card-scope-boundary-g1--g2-ship-g3-deferred-the-performance-findings-and-the-deferred-audit-catalogue-are-out
[spec-035-d3]: ../spec-035-optimizer_hardening-0_0_10.md#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize
[spec-035-d4]: ../spec-035-optimizer_hardening-0_0_10.md#decision-4--g2--operation-type-gating-of-only-suppress-only_fields-for-non-query-operations-at-plan-build-time
[spec-035-d5]: ../spec-035-optimizer_hardening-0_0_10.md#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations
[spec-035-d6]: ../spec-035-optimizer_hardening-0_0_10.md#decision-6--g3--registry-only-fragment-type-condition-narrowing
[spec-035-d7]: ../spec-035-optimizer_hardening-0_0_10.md#decision-7--g3--narrow-do-not-multi-plan
[spec-035-d8]: ../spec-035-optimizer_hardening-0_0_10.md#decision-8--module-and-test-locations-no-new-module-g1--g2-in-testsoptimizer-g3-tests-deferred
[spec-035-d9]: ../spec-035-optimizer_hardening-0_0_10.md#decision-9--version-bumps-are-owned-by-the-joint-0010-cut
[spec-035-doc-updates]: ../spec-035-optimizer_hardening-0_0_10.md#doc-updates
[spec-035-dod]: ../spec-035-optimizer_hardening-0_0_10.md#definition-of-done
[spec-035-g3-test-plan]: ../spec-035-optimizer_hardening-0_0_10.md#slice-3--g3--deferred-carry-forward-requirements-for-the-abstract-return-optimizer-entry-card
[spec-035-goals]: ../spec-035-optimizer_hardening-0_0_10.md#goals
[spec-035-out-of-scope]: ../spec-035-optimizer_hardening-0_0_10.md#out-of-scope-explicitly-tracked-elsewhere
[spec-035-parity-checkpoint]: ../spec-035-optimizer_hardening-0_0_10.md#reference-package-parity-checkpoint
[spec-035-problem-statement]: ../spec-035-optimizer_hardening-0_0_10.md#problem-statement
[spec-035-slice-checklist]: ../spec-035-optimizer_hardening-0_0_10.md#slice-checklist
[spec-035-terms]: spec-035-optimizer_hardening-0_0_10-terms.csv

<!-- docs/builder/ -->
[build-035]: ../../builder/DONE/build-035-optimizer_hardening-0_0_10.md
[build-md]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[extension]: ../../../django_strawberry_framework/optimizer/extension.py
[mutations-resolvers]: ../../../django_strawberry_framework/mutations/resolvers.py
[nested-planner]: ../../../django_strawberry_framework/optimizer/nested_planner.py
[plans]: ../../../django_strawberry_framework/optimizer/plans.py
[querysets]: ../../../django_strawberry_framework/utils/querysets.py
[registry]: ../../../django_strawberry_framework/registry.py
[selections]: ../../../django_strawberry_framework/optimizer/selections.py
[types-base]: ../../../django_strawberry_framework/types/base.py
[types-resolvers]: ../../../django_strawberry_framework/types/resolvers.py
[walker]: ../../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-opt-extension]: ../../../tests/optimizer/test_extension.py

<!-- examples/ -->
[library-schema]: ../../../examples/fakeshop/apps/library/schema.py
[test-library-api]: ../../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-optimizer]: https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/optimizer.py
