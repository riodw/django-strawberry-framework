# Rationale companion: spec-035 (Optimizer robustness hardening)

Companion to [`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`][spec-035]. It carries that spec's **deliberative layer**: every Decision's justification, every alternative a Decision rejected and why it lost, and the standing risks with their fallbacks. The spec carries the contract; this file carries why the contract has its shape. Neither duplicates the other.

Read this when checking the implementation against the reasoning behind it, or before re-opening a settled question. Worker 2 never reads it ([`docs/builder/BUILD.md`][build-md] `### Who reads it, and when`).

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-035-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `DONE-035-0.0.10`, so `<NNN>` is `035` and `<0_0_X>` is `0_0_10`.
- The topic slug is `optimizer_hardening` — the exact suffix the card's Definition of done names ("numbered to the card at implementation time, suffix `optimizer_hardening-0_0_10`").

### Alternatives considered (and rejected)

- **Topic slug `optimizer_robustness` / `optimizer_guards`.** Rejected: the card DoD pins `optimizer_hardening` verbatim; matching it keeps the spec-reference link in the kanban `SpecDoc` stable.

## Decision 2 — Card-scope boundary: G1 + G2 ship (G3 deferred); the performance findings and the deferred-audit catalogue are out

Spec: [Decision 2 — Card-scope boundary: G1 + G2 ship (G3 deferred); the performance findings and the deferred-audit catalogue are out][spec-035-d2].

### Justification

The audit produced a 36-capability inventory; the card scopes three guards and parks the rest with explicit dispositions. The spec preserves those dispositions so a reader sees which omissions are decisions (prefetch merging) versus deferrals (annotation hints, G3) versus other-card ownership (windowed prefetch).

### Alternatives considered (and rejected)

**fold the cheap deferred findings (e.g. the `disabled()` contextvar) into this card.** Rejected: grafting "while I'm here" extras is the scope-creep [`START.md`][start] warns against, and each deferred finding has its own design surface — the same reasoning that, in reverse, takes G3 out of the card: it needs a whole abstract-entry design surface of its own.

## Decision 3 — G1 — evaluated-queryset guard: `_result_cache` early-return in `_optimize`

Spec: [Decision 3 — G1 — evaluated-queryset guard: `_result_cache` early-return in `_optimize`][spec-035-d3].

### Justification

This is upstream's execution-state check, minus the flag bookkeeping the package's O3 root gate makes redundant. Upstream guards twice (`_result_cache is None` at the resolve hook AND `is_optimized(qs) or qs._result_cache is not None` inside `optimize()`) because its optimizer can run at nested resolvers and must stay idempotent across `_clone` calls; the package's optimizer runs only at the operation root (`info.path.prev is None`), so a single execution-state check at the one entry is complete. It extends the [`spec-004`][spec-004] B8 "respect what the consumer already did" posture from optimization state (consumer `.only()` / `select_related` wins) to execution state (consumer-evaluated queryset is left alone). The contract stops at a `get_queryset` visibility boundary because a queryset the framework did not build is untrusted there ([`spec-045`][spec-045]): trusting its row cache across the hook would serve rows the hook never authorized.

### Alternatives considered (and rejected)

- **Port the full upstream two-part guard (flag + `_clone` monkeypatch).** Rejected: monkeypatching `QuerySet._clone` couples the package to a Django private and exists upstream only to make a nested-capable optimizer idempotent — a problem the O3 root gate already solves. Carrying machinery for a scenario the architecture forbids is dead weight.
- **Guard inside `apply_to` (shared with the connection field) instead of `_optimize`.** Rejected: the connection field's queryset is framework-built and never evaluated, so guarding the shared tail would add a per-connection `getattr` check that can never fire — and would muddy the contract that `apply_to` optimizes whatever pre-built queryset it is handed. The risk is specific to consumer-returned querysets, which only reach `_optimize`.
- **Detect evaluation by `bool(qs._result_cache)` / `len`.** Rejected: `_result_cache` is `None` until evaluated and a (possibly empty) list after — `is not None` is the exact, allocation-free signal upstream uses; truthiness would mis-handle an evaluated-but-empty queryset.

## Decision 4 — G2 — operation-type gating of `.only()`: suppress `only_fields` for non-`QUERY` operations at plan-build time

Spec: [Decision 4 — G2 — operation-type gating of `.only()`: suppress `only_fields` for non-`QUERY` operations at plan-build time][spec-035-d4].

### Justification

The `0.0.11` write side re-fetches its post-write row as a queryset under the `MUTATION` operation, so a mutation-root queryset is a mainstream path; landing the gate at plan-build time is the cache-correct placement (the printed-AST key already separates operations, so no key change is needed and the suppression is cached, not recomputed per request). `select_related` / `prefetch_related` stay on because they never carry the deferred-field hazard — they shape *which related rows load*, not *which columns of a row* are deferred.

### Alternatives considered (and rejected)

- **Apply-time gate in [`plans.py::OptimizationPlan.apply`][plans].** Rejected: a plan built with `only_fields` then conditionally not applying them at apply time means the cache stores a `only_fields`-carrying plan that two operations (query and mutation) would want to apply differently — but the cache already separates them by printed-AST key, so building the right plan per key (build-time) is both simpler and avoids an apply-time branch on `info.operation`. The card pins build-time as preferred for exactly this cacheability reason.
- **Block scalar appends only, relying on `_ensure_connector_only_fields`'s empty-`only_fields` no-op to suppress the rest.** Rejected: it leaks. [`_record_relation_access`][walker] appends link connector columns on relation traversal, making `only_fields` non-empty *independently of* scalar leaves — so a mutation selecting a relation would still get a non-empty projection and the connector helper would not no-op. And [`_project_scalar_only_window`][nested-planner] applies `.only(...)` directly without populating `only_fields`, so no empty-set check reaches it. The gate must be threaded through all five projection writers, not just the scalar path.
- **Root-only suppression.** Rejected: leaves nested prefetched children carrying deferred-field sets under a mutation, reintroducing the deferred-refetch hazard one level down; upstream gates `.only()` operation-wide.
- **Suppress `select_related` / `prefetch_related` too under non-`QUERY`.** Rejected: those carry no deferred-field hazard and dropping them would reintroduce N+1s on a mutation's response selection — the hazard is specific to column deferral.

## Decision 5 — G2 — FK-id elision stays enabled under non-`QUERY` operations

Spec: [Decision 5 — G2 — FK-id elision stays enabled under non-`QUERY` operations][spec-035-d5].

### Justification

Elision's correctness precondition is "the FK column is loaded on the parent row." G2 guarantees that *for optimizer-owned projections* (and under `QUERY` the union with a consumer projection loads the column the plan records), but under a non-`QUERY` operation a consumer-returned projection stays as returned and can still defer it, so the precondition must be **checked**, not assumed. Keeping elision on (with the guard) preserves the B2 advantage and avoids a needless join on the common fully-loaded path; the guard only changes the rare consumer-`.only()`-defers-the-FK path, turning a silent lazy-load into a visible, strictness-honest fallback.

### Alternatives considered (and rejected)

**disable elision entirely under non-`QUERY` ops.** Rejected: it does not address the real hazard (which is the consumer's projection, not the operation type) and trades a correct single-query elision for an unnecessary join on every fully-loaded mutation row. **Drop all elisions after diffing whenever the consumer applied `.only()`.** Rejected as insufficient on its own: the elision branch recorded no `select_related` fallback, so merely dropping the elision still leaves the relation needing a resolve path — the resolver-time loaded-check is what makes the fallback honest.

## Decision 6 — G3 — registry-only fragment type-condition narrowing

Spec: [Decision 6 — G3 — registry-only fragment type-condition narrowing][spec-035-d6].

### Justification

`type_condition` is already carried through the substrate (the inline-fragment shell, the `is_fragment` duck-type); G3 would be the first code to *match* it against the planning type. Resolving the match through the registry (the type's `graphql_type_name` and the union of its declared `definition.interfaces` + MRO-inherited interface bases) reuses the exact metadata [`Schema audit`][glossary-schema-audit] already descends and keeps the walk free of per-request schema introspection. Confining the accept set to the planning type's own name and the interfaces it implements — and excluding the shared model's primary type name — keeps the narrowing faithful to GraphQL type-condition semantics (a condition matches the runtime type or an abstract type it belongs to, not the Django model behind it). Threading the classifier only through the walker (not the shared primitive's other callers) contains the change to the one path that plans relations. The narrowing has nothing to narrow until an abstract root reaches the walker: an interface-typed field is passed through unoptimized (never mis-walked), because `registry.model_for_type` returns `None` for the abstract origin and `_optimize` returns before the walker runs — which is why requirement R1 comes first.

### Alternatives considered (and rejected)

- **graphql-core schema lookup of possible types per fragment.** Rejected: violates the B7 invariant (zero per-request Django / schema introspection); the registry already answers "does this planning type satisfy this type condition" from finalized metadata.
- **Accept the model's registered primary type name.** Rejected: a `type_condition` matches the runtime GraphQL type, not the Django model. Accepting the primary name would inline a `... on PrimaryType` fragment while planning a *secondary* type over the same model, planning fields / relations the secondary may not expose and crossing distinct `get_queryset` / `relation_shapes` / field-override contracts — the exact over-planning G3 removes. The plan cache already keys on the origin Strawberry type, so there is no cache reason to blur primary and secondary. When the primary type itself roots the walk, its own `graphql_type_name` accepts the fragment anyway, so dropping the rule loses no valid match.
- **Collect interface names from a single source (either `definition.interfaces` alone or `origin.__mro__` alone).** Rejected: the two sources are **complementary, not redundant**, so either alone is incomplete. `definition.interfaces` is the normalized **declared** `Meta.interfaces` tuple ([`types/base.py::_validate_interfaces`][types-base] stores it verbatim and injects nothing); interfaces implemented by **direct class inheritance** (`class Foo(DjangoType, relay.Node)`) appear **only** in `origin.__mro__`, never in `definition.interfaces` (per [`_is_relay_shaped`][types-base]'s `... or issubclass(cls, relay.Node)` arm). A `definition.interfaces`-only collection silently misses every inherited interface; an MRO-only collection misses declared ones. The accept set must be the **union** of both arms.
- **A boolean include / skip predicate.** Rejected: it cannot express the third outcome (`RECURSE_FRAGMENTS_ONLY`) an unknown composite condition needs.
- **Skip every non-matching condition whole, including unknown composite / union conditions.** Rejected: a union or unrecognized-abstract condition can wrap a nested `... on <ConcreteType>` fragment that *does* match the planning type; skipping the whole subtree under-plans that valid nested fragment. The unknown-composite fallback recurses into nested fragments (re-classifying each) while declining the unknown fragment's own direct fields — conservative in both directions.
- **Skip only the unknown-name fields, not the whole fragment subtree (for sibling concrete types).** Rejected: a sibling-type fragment can name a relation that happens to exist on the planning type too (failure mode (b)); skipping field-by-field on the unknown-name guard misses the same-named-relation over-fetch. For a *known sibling concrete type* the non-matching fragment subtree is skipped whole.

## Decision 7 — G3 — narrow, do not multi-plan

Spec: [Decision 7 — G3 — narrow, do not multi-plan][spec-035-d7].

### Justification

The package's plan cache stores one plan per `(document, target_model, origin)` key; a per-concrete-type re-walk would either multiply cache entries or build a union plan that re-introduces the over-projection G3 removes. The registry narrowing achieves the correctness outcome (sibling branches don't plan; same-named relations plan only for the matching branch) at one extra set-membership check per fragment, preserving B7 precompute and the single-plan-per-key contract. Upstream multi-plans because its optimizer lacks the package's class-creation-time metadata and global plan cache — the package doesn't need to.

### Alternatives considered (and rejected)

**adopt upstream's per-concrete-type re-walk for completeness.** Rejected: it fights the package's cache contract and B7 advantage for a correctness outcome the narrowing already achieves; the card is explicit ("we narrow, we do not multi-plan").

## Decision 8 — Module and test locations: no new module; G1 + G2 in `tests/optimizer/`, G3 tests deferred

Spec: [Decision 8 — Module and test locations: no new module; G1 + G2 in `tests/optimizer/`, G3 tests deferred][spec-035-d8].

### Justification

The source guards are package-internal optimizer mechanics, and tests mirror source one-to-one per [`docs/TREE.md`][tree]. The plan-state half (`only_fields`, `deferred_loading`, cache keys) is assertable only package-internally; the behavioral half is live wherever a fakeshop surface reaches it (G1's evaluate-then-return resolver and the manager-coercion row; G2's mutation responses). G3's only "live-reachable" shape (a matching-type fragment under `allLibraryGenresConnection`) tests behavior that already works without G3, so it is no-regression coverage, not proof — and it travels with the deferred G3 work.

### Alternatives considered (and rejected)

- **Keep a live G3 test in this card as evidence G3 works.** Rejected: the only live-reachable G3 shape is a *matching-type* fragment, which plans with no narrowing — it proves nothing about the sibling / union narrowing G3 adds. Carrying it here would imply G3 ships behavior it does not.
- **A new `tests/optimizer/test_hardening.py`.** Rejected: the G1 + G2 pins extend the contracts the predicted files already cover (extension behavior, walker plan content); co-locating them beside the existing extension / walker coverage keeps the one-to-one mirror and the regression context together.

## Decision 9 — Version bumps are owned by the joint `0.0.10` cut

Spec: [Decision 9 — Version bumps are owned by the joint `0.0.10` cut][spec-035-d9].

### Justification

The same shape as [`spec-034`][spec-034] Decision 13 and [`spec-033`][spec-033] Decision 12, and the [`docs/SPECS/NEXT.md`][next] Step 6 mandate for multi-card patch versions — when multiple cards target one patch, the version bump is the joint cut's, not any single card's.

### Alternatives considered (and rejected)

**bump in Slice 4 since this card may land last of the two.** Rejected: landing order between `034` and `035` is a maintainer scheduling fact, not a spec fact; the cut is a maintainer release act with its own checklist regardless of which card's PR merges last.

## Risks and open questions

Each item names the shipped (or, for G3, designed) answer and the fallback if it proves wrong.

- **G2 FK-id elision under non-`QUERY` operations.** Shipped answer ([Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations)): keep elision enabled, guarded by the resolver-time loaded-check. Fallback: if a real consumer surfaces a deferred-elision interaction under mutations, gate elision alongside `.only()` — a one-line addition to the same operation-type branch, test-pinned either way.
- **G2 nested-plan `only_fields` suppression scope.** Shipped answer: suppress plan-wide (root + nested child plans), matching upstream's operation-wide `enable_only`. Fallback: if a consumer relies on nested child-row projection under a mutation (and accepts the deferred-refetch hazard on those children), root-only suppression is a contained narrowing — but it reintroduces the exact hazard one level down, so plan-wide is the safe default.
- **G3 connection-wrapped fragment narrowing.** Designed answer: narrowing happens at each `_walk_selections` entry (the node model's planning type), so connection-wrapped fragments narrow without touching the extraction helpers. Fallback: if a test shows the extraction helpers ([`named_children`][selections] / [`node_children_with_runtime_prefix`][selections]) flatten a fragment before the node walk re-resolves type, thread the same classifier into those helpers — a contained extension of the Decision 6 mechanism.
- **G3 interface-name collection gaps.** If neither collection source records an interface a fragment names, the condition is treated as an unknown composite (recurse-without-direct-fields), never a silent whole-subtree skip.
- **Upstream parity is a behavior contract, not a line contract.** The audit recorded specific [`strawberry_django/optimizer.py`][upstream-optimizer] locations as evidence; this spec treats the *behavior* each names — the resolve-hook `_result_cache is None` guard, the `enable_only and operation == QUERY` gate, the `get_possible_concrete_types` per-type re-walk — as the parity contract, referenced by the stable upstream permalink rather than a checkout line number (which drifts with every upstream release). The behavior descriptions in the [parity checkpoint][spec-035-parity-checkpoint] and the [Borrowing posture][spec-035-borrowing-posture] are the contract.
- **No new module / no settings key.** The guards are edits to existing optimizer and resolver modules; no new module and no `DJANGO_STRAWBERRY_FRAMEWORK` entry.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[start]: ../../../START.md

<!-- docs/ -->
[glossary-schema-audit]: ../../GLOSSARY.md#schema-audit
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-004]: ../spec-004-optimizer_beyond-0_0_3.md
[spec-033]: ../spec-033-connection_optimizer-0_0_9.md
[spec-034]: ../spec-034-permissions-0_0_10.md
[spec-035]: ../spec-035-optimizer_hardening-0_0_10.md
[spec-035-borrowing-posture]: ../spec-035-optimizer_hardening-0_0_10.md#borrowing-posture
[spec-035-d1]: ../spec-035-optimizer_hardening-0_0_10.md#decision-1--spec-filename-and-canonical-naming
[spec-035-d2]: ../spec-035-optimizer_hardening-0_0_10.md#decision-2--card-scope-boundary-g1--g2-ship-g3-deferred-the-performance-findings-and-the-deferred-audit-catalogue-are-out
[spec-035-d3]: ../spec-035-optimizer_hardening-0_0_10.md#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize
[spec-035-d4]: ../spec-035-optimizer_hardening-0_0_10.md#decision-4--g2--operation-type-gating-of-only-suppress-only_fields-for-non-query-operations-at-plan-build-time
[spec-035-d5]: ../spec-035-optimizer_hardening-0_0_10.md#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations
[spec-035-d6]: ../spec-035-optimizer_hardening-0_0_10.md#decision-6--g3--registry-only-fragment-type-condition-narrowing
[spec-035-d7]: ../spec-035-optimizer_hardening-0_0_10.md#decision-7--g3--narrow-do-not-multi-plan
[spec-035-d8]: ../spec-035-optimizer_hardening-0_0_10.md#decision-8--module-and-test-locations-no-new-module-g1--g2-in-testsoptimizer-g3-tests-deferred
[spec-035-d9]: ../spec-035-optimizer_hardening-0_0_10.md#decision-9--version-bumps-are-owned-by-the-joint-0010-cut
[spec-035-parity-checkpoint]: ../spec-035-optimizer_hardening-0_0_10.md#reference-package-parity-checkpoint
[spec-045]: ../spec-045-visibility_boundary-0_0_14.md

<!-- docs/builder/ -->
[build-md]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[nested-planner]: ../../../django_strawberry_framework/optimizer/nested_planner.py
[plans]: ../../../django_strawberry_framework/optimizer/plans.py
[selections]: ../../../django_strawberry_framework/optimizer/selections.py
[types-base]: ../../../django_strawberry_framework/types/base.py
[walker]: ../../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-optimizer]: https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/optimizer.py
