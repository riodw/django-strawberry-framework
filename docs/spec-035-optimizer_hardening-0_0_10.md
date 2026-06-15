# Spec: Optimizer robustness hardening — the evaluated-queryset guard (G1), operation-type `.only()` gating (G2), and registry-only fragment type-condition narrowing (G3)

Planned for `0.0.10` (card [`WIP-ALPHA-035-0.0.10`][kanban]). **This spec is an open build plan, not a shipped record.** The card was directed to spec by the maintainer; its three guards close robustness gaps a 2026-06-11 comparative audit verified absent in `django_strawberry_framework/optimizer/` against [`strawberry_django/optimizer.py`][upstream-optimizer] (1,823 lines, 36 capabilities inventoried). The [Slice checklist](#slice-checklist) below stays unticked as the contract record; the [Definition of done](#definition-of-done) describes the closure conditions; the [Current state](#current-state) section describes the repo as of this spec's authoring, before the build. **Version boundary** (see [Decision 9](#decision-9--version-bumps-are-owned-by-the-joint-0010-cut)): this card shares the `0.0.10` patch line with [`DONE-034-0.0.10`][kanban] (the permissions subsystem, now build-complete); the `pyproject.toml` / `__version__` / [`tests/base/test_init.py::test_version`][test-base-init] bump to `0.0.10` is owned by the **joint cut**, not by this card. This card's slices land within the `0.0.10` line and never bump the version themselves (the on-disk version reads `0.0.9` as of this writing — the `0.0.9` cut has landed; the `0.0.10` bump itself remains the joint cut's job, after the still-pending release act).

Status: needs spec → build not started. Four slices: Slice 1 (**G1 — the evaluated-queryset guard**: a `_result_cache`-present early-return in [`optimizer/extension.py::DjangoOptimizerExtension._optimize`][extension] so a consumer-evaluated root queryset is never silently re-executed by the optimizer's clone — [Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize)), Slice 2 (**G2 — operation-type gating of `.only()`**: suppress `only_fields` for non-`QUERY` operations at plan-build time, keeping `select_related` / `prefetch_related`, with the FK-id-elision-under-non-`QUERY` decision pinned — [Decision 4](#decision-4--g2--operation-type-gating-of-only-suppress-only_fields-for-non-query-operations-at-plan-build-time) / [Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations)), Slice 3 (**G3 — fragment type-condition narrowing**: a registry-only narrowing of fragment inlining in [`optimizer/selections.py::included_field_selections`][selections] so an interface / union query stops planning sibling-concrete-type branches — [Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing) / [Decision 7](#decision-7--g3--narrow-do-not-multi-plan)), and Slice 4 (doc updates + the card-completion wrap; grants the per-card [`CHANGELOG.md`][changelog] edit permission [`AGENTS.md`][agents] otherwise withholds). Slice 1 is independent; 2 and 3 are independent of each other and of 1; 4 lands last. G3 lands **after** the [`DONE-033-0.0.9`][kanban] connection-aware planning work that rewrote the same `walker.py` selection-normalization seam (the card's hard dependency, already satisfied), so its union / interface tests can cover connection-wrapped fragments too.

Owner: package maintainer.

Predecessors: [`spec-033-connection_optimizer-0_0_9.md`][spec-033] (the most-recently-authored spec — the canonical voice / depth / section-layout reference for this document; it rewrote the [`optimizer/walker.py`][walker] / [`optimizer/selections.py`][selections] fragment-inlining seam G3 extends, and its windowed-prefetch + `totalCount` work is the **performance** half of the same 2026-06-11 audit, explicitly NOT in this card); [`spec-004-optimizer_beyond-0_0_3.md`][spec-004] (the B1–B8 optimizer foundation — G1 extends B8's consumer-state reconciliation from optimization state to **execution** state; G2's cache-safety argument rests on B1's printed-AST cache key; B3 strictness and B7 class-creation-time `FieldMeta` precompute are the advantages the audit confirmed this package holds over upstream); [`spec-002-optimizer-0_0_2.md`][spec-002] (the O1–O6 foundation — the O3 root gate `info.path.prev is None` that makes G1's minimal shape correct, and the O2 walker's selection-normalization seam G3 lives in). [`docs/GLOSSARY.md`][glossary] carries [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], [`only()` projection][glossary-only-projection], and [Strictness mode][glossary-strictness-mode] as `shipped`; Slice 4 appends the three robustness guards to those bodies (no new heading — these are refinements of shipped surfaces, see [Doc updates](#doc-updates)).

Revision history (kept inline so the spec is self-contained):

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-035-0.0.10`][kanban] card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-06-15). Pinned: the canonical structured spec filename ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the three guards ported at the **outcome** level from `strawberry_django` with the package's own minimal mechanisms ([Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize) / [Decision 4](#decision-4--g2--operation-type-gating-of-only-suppress-only_fields-for-non-query-operations-at-plan-build-time) / [Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing)); the **G2 FK-id-elision-under-non-`QUERY` open decision** resolved in favor of keeping elision enabled ([Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations)); the **narrow-not-multi-plan** posture rejecting upstream's per-concrete-type re-walk ([Decision 7](#decision-7--g3--narrow-do-not-multi-plan)); the cache-safety arguments for G2 and G3 (zero key change in both cases); the deferred-audit findings carried into [Out of scope](#out-of-scope-explicitly-tracked-elsewhere) as spec non-goals; the joint-cut version boundary shared with [`DONE-034-0.0.10`][kanban] ([Decision 9](#decision-9--version-bumps-are-owned-by-the-joint-0010-cut)); and three card-citation corrections recorded rather than silently reconciled — the manager-coercion site (the card cites `extension.py:714`; the live DRY home is [`utils/querysets.py::normalize_query_source`][querysets] called at [`extension.py`][extension] line ~778, [Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize)), the fragment-inlining anchor (the card cites `walker.py:733`/`:845`; the live primitive is [`selections.py::included_field_selections`][selections] inlined at [`walker.py`][walker] line ~284, with the unknown-name `continue` guard at line ~313, [Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing)), and the verified-absent grep results (`_result_cache`, `OperationType`, and a *matched* `type_condition` are all absent from the package as of this writing — [Current state](#current-state)).

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the subject. All three guards land inside its `_optimize` middleware path ([`extension.py`][extension]) or the [`walker.py`][walker] / [`selections.py`][selections] plan-build it drives. The entry's shipped-behavior list (root-gated optimization, `Manager` coercion, `only` projection, the `get_queryset` → `Prefetch` downgrade) is the surface these guards refine; Slice 4 appends the three "what the optimizer will not touch" notes.
- [`only()` projection][glossary-only-projection] — the surface G2 gates. The entry pins that scalar selections become `.only(...)` projections with connector columns preserved; G2 suppresses that projection (only `only_fields`, never `select_related` / `prefetch_related`) for non-`QUERY` operations so a mutation-returned queryset never carries a selection-shaped deferred-field set.
- [Plan cache][glossary-plan-cache] — the cache whose key both G2 and G3 must not perturb. The key's first component is the printed operation AST ([`extension.py::_print_operation_with_reachable_fragments`][extension]); G2's cache-safety rests on that print including the `query` / `mutation` / `subscription` keyword, and G3's on narrowing being a pure function of `(document, target_model, origin)` — all three already cache-key components.
- [Queryset diffing][glossary-queryset-diffing] — the B8 consumer-state reconciliation G1 extends. B8 reconciles framework plans against optimization state the consumer already applied (`select_related`, `Prefetch`, `only`); G1 extends the same "respect what the consumer already did" posture to **execution** state (a queryset the consumer already evaluated is not re-executed by an optimizer clone).
- [Strictness mode][glossary-strictness-mode] — the N+1 detector G3 interacts with. Today a sibling-concrete-type relation branch on an interface / union query is silently unplanned and only detected at runtime by strictness `"raise"` (detection, not prevention); G3 makes the plan itself correct, and the spec pins that strictness no longer false-fires for a correctly-narrowed sibling fragment the resolver never executes.
- [FK-id elision][glossary-fk-id-elision] — the optimization whose interaction with G2 is the card's open decision. Elision reads the FK column off the parent row when a `{ relation { id } }` selection touches only the target pk; [Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations) keeps it enabled under non-`QUERY` operations (with `only` suppressed the full parent row loads, so the FK column the elision stub reads is always present).
- [Relation handling][glossary-relation-handling] / [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] — the relation-planning contracts G3's narrowing must not regress; the connection planning ([`DONE-033-0.0.9`][kanban]) is the work that last rewrote the fragment-inlining seam, so G3 lands after it and its tests cover connection-wrapped fragments.
- [`DjangoType`][glossary-djangotype] / [`Meta.primary`][glossary-metaprimary] / [`Meta.interfaces`][glossary-metainterfaces] / [Relay Node integration][glossary-relay-node-integration] — G3 resolves a fragment's `type_condition` against the current planning type's own GraphQL name, the names in its `Meta.interfaces`, and the model's registered primary type name — registry / definition metadata only, never a graphql-core schema lookup.
- [`Schema audit`][glossary-schema-audit] — `check_schema` already descends through interface implementors; G3's narrowing is the runtime-walk analogue (it resolves the concrete-type fragment match through the same registry the audit uses).
- [`ConfigurationError`][glossary-configurationerror] — no new validation surface in this card; named only to confirm none of the three guards adds one.
- [Multi-database cooperation][glossary-multi-database-cooperation] — the guards are alias-agnostic; G1 / G2 / G3 change neither `.using()` preservation nor router-hint behavior.
- [`DjangoConnectionField`][glossary-djangoconnectionfield] — the connection field shares the `apply_to` plan-build-and-apply tail with `_optimize` but builds its own pre-slice queryset, so it is **out of scope** for G1 (its queryset is framework-built and never consumer-evaluated); G3's narrowing applies inside the nested-connection walk through the same predicate.
- [`Meta.optimizer_hints`][glossary-metaoptimizer_hints] / [`OptimizerHint`][glossary-optimizerhint] — unchanged; hints shape relation planning, orthogonal to the execution-state / operation-type / fragment-narrowing concerns of this card.
- [`DjangoMutation`][glossary-djangomutation] / [Auth mutations][glossary-auth-mutations] — the `0.0.11` write-side cohort that makes mutation root resolvers returning querysets a mainstream path; G2 is sequencing-critical *because* of it (ship the gate before the consumers arrive).
- [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — the joint-`0.0.10`-cut sibling ([`DONE-034-0.0.10`][kanban]); independent of these guards (the cascade composes through `get_queryset`, which the walker's downgrade rule honors unchanged), named here only for the shared version boundary.

Project conventions to follow:

- [`AGENTS.md`][agents] — the test-placement rule (package-internal optimizer mechanics live under `tests/` mirroring source); the live-HTTP-priority coverage rule (and its exception: G1 / G2 / G3 are not reachable by a single live products query — G2 needs a mutation operation no card ships before `0.0.11`, G1 needs a consumer-evaluated root queryset, G3 needs synthetic union / interface schemas — so they are earned in [`tests/optimizer/`][test-opt-extension] with the unreachability reason recorded, per [Decision 8](#decision-8--module-and-test-locations-no-new-module-optimizer-edits--testsoptimizer)); the no-pytest-after-edits rule; the CHANGELOG-edit-permission rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — Slice 4's doc-update step grants the explicit per-card permission.
- [`CONTRIBUTING.md`][contributing] — 100% coverage target (`fail_under = 100`); the guards are package-internal and earn coverage in `tests/optimizer/`.
- [`docs/TREE.md`][tree] — the optimizer subpackage layout is stable; this card adds no module and no test file, only extends [`tests/optimizer/test_extension.py`][test-opt-extension] and [`tests/optimizer/test_walker.py`][test-opt-walker] (the card's predicted files).
- [`START.md`][start] — the "behaviorally we copy `strawberry-graphql-django`'s good ideas" rule: these three guards are exactly such borrowings, adopted at the **outcome** level with the package's lighter mechanisms (the O3 root gate, the registry, the printed-AST cache key) substituted for upstream's heavier ones; markdown link convention (reference-style cross-file links, defs at the bottom under the 10 canonical group headers).

## Slice checklist

Each top-level item maps to one commit / PR. **Four slices: three functional (1, 2, 3 — mutually independent; 3 lands after `033`'s walker churn) plus a doc + card-completion wrap (4).** Boxes are unticked because the work has not started.

- [ ] Slice 1: G1 — evaluated-queryset guard (per [Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize))
  - [ ] [`optimizer/extension.py::DjangoOptimizerExtension._optimize`][extension]: after the [`utils/querysets.py::normalize_query_source`][querysets] coercion + `is_queryset` gate (a `Manager` → `.all()` coercion always yields a fresh **unevaluated** queryset, so the guard must sit AFTER it) and before the `apply_to` plan-build / `diff_plan_for_queryset` tail, return the result unchanged when `getattr(result, "_result_cache", None) is not None`. Read defensively with `getattr` per the package posture ([`optimizer/field_meta.py::_target_pk_name`][field-meta]).
  - [ ] No port of upstream's `is_optimized()` flag, `CONFIG_KEY` queryset config, or the `QuerySet._clone` monkeypatch ([`strawberry_django/queryset.py`][upstream-optimizer] lines 50–62) — those exist upstream because its optimizer can run at nested resolvers; the package's O3 root gate (`info.path.prev is None`, [`spec-002`][spec-002]) already guarantees single application, so execution-state (`_result_cache`) is the only missing check ([Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize)).
  - [ ] Package coverage: [`tests/optimizer/test_extension.py`][test-opt-extension] pins the pass-through (a root resolver that evaluates the queryset via `len(qs)` then returns it executes exactly one SQL query total and returns the SAME queryset instance — not a re-executing clone), the manager-coercion path still optimizes (the guard sits after `normalize_query_source`), and the async mirror.
- [ ] Slice 2: G2 — operation-type gating of `.only()` (per [Decision 4](#decision-4--g2--operation-type-gating-of-only-suppress-only_fields-for-non-query-operations-at-plan-build-time) / [Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations))
  - [ ] [`optimizer/walker.py::plan_optimizations`][walker]: when `info` is present and `info.operation.operation is not OperationType.QUERY`, suppress `only_fields` across the whole plan tree (root + nested child plans) while leaving `select_related` / `prefetch_related` / `fk_id_elisions` intact. Build-time, in the walker entry point (NOT apply-time in [`optimizer/plans.py`][plans]) so the suppression bakes into the cached plan ([Decision 4](#decision-4--g2--operation-type-gating-of-only-suppress-only_fields-for-non-query-operations-at-plan-build-time)).
  - [ ] FK-id elision stays enabled under non-`QUERY` operations ([Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations) — the card's open decision): with `only_fields` suppressed the full source row loads, so the FK `attname` column the elision stub reads ([`types/resolvers.py::_build_fk_id_stub`][types-resolvers]) is always present and elision remains correct.
  - [ ] Package coverage: [`tests/optimizer/test_walker.py`][test-opt-walker] + [`tests/optimizer/test_extension.py`][test-opt-extension] — a mutation operation whose root resolver returns a queryset produces an empty-`only_fields` plan with `select_related` / `prefetch_related` surviving; a textually-identical selection under a `query` operation still projects `only_fields`; both plans coexist in the cache (distinct printed-AST keys); subscription operations are covered by the same gate; the elision-under-mutation decision is pinned.
- [ ] Slice 3: G3 — fragment type-condition narrowing (per [Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing) / [Decision 7](#decision-7--g3--narrow-do-not-multi-plan))
  - [ ] [`optimizer/selections.py::included_field_selections`][selections] gains an optional registry-only narrowing predicate; [`optimizer/walker.py`][walker] supplies it at the point the planning `type_cls` / `definition` is resolved ([`walker.py::_resolve_field_map`][walker], the call at line ~284): a fragment carrying a non-`None` `type_condition` inlines only when the condition's type name matches the current planning type — its own GraphQL name ([`types/definition.py::DjangoTypeDefinition.graphql_name`][definition]), a name in its [`Meta.interfaces`][glossary-metainterfaces], or the registered primary type name for the model; otherwise the fragment subtree is skipped. An anonymous inline fragment (`type_condition is None`) always inlines (it applies to the enclosing type). Names resolve through the registry / definition only — NO graphql-core schema lookups in the walk (the B7 zero-per-request-introspection invariant). The extension-side cache-key and connection-extraction paths pass no predicate (behavior unchanged).
  - [ ] Package coverage: [`tests/optimizer/test_walker.py`][test-opt-walker] + [`tests/optimizer/test_extension.py`][test-opt-extension] — union / interface fragment tests (sibling-concrete-type fragment bodies excluded from the plan: no spurious `select_related` / `only`; matching-type and interface-implementor fragments still plan; the same-named-relation-on-two-members shape is a dedicated regression; anonymous inline fragments still inline; B3 strictness keys stay branch-sensitive after narrowing, and strictness `"warn"`/`"raise"` no longer fires for a correctly-narrowed sibling fragment the resolver never executes; a connection-wrapped sibling fragment narrows too).
- [ ] Slice 4: doc updates + card-completion wrap (per [Doc updates](#doc-updates))
  - [ ] [`docs/GLOSSARY.md`][glossary] (append the three guards to [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] / [`only()` projection][glossary-only-projection] / [Strictness mode][glossary-strictness-mode] bodies — no new heading), [`docs/README.md`][docs-readme] (the optimizer surface line + the "Coming next" `0.0.10` line shrinks to nothing as the joint cut completes), [`README.md`][readme] (the optimizer "what it will not touch" note), [`CHANGELOG.md`][changelog] (the explicit permission grant), [`KANBAN.md`][kanban] (card → Done via the kanban DB + re-render). No version-file edits ([Decision 9](#decision-9--version-bumps-are-owned-by-the-joint-0010-cut)).

## Problem statement

The optimizer applies a selection-shaped ORM plan to whatever root queryset a resolver returns, regardless of three properties of that queryset and its operation that upstream `strawberry_django` guards and this package does not. A 2026-06-11 comparative audit of [`django_strawberry_framework/optimizer/`][extension] against [`strawberry_django/optimizer.py`][upstream-optimizer] verified three robustness gaps absent from this package by direct grep and read (not inferred); each exists upstream with a known mechanism and a specific file:line anchor.

**G1 — the evaluated-queryset gap.** [`DjangoOptimizerExtension._optimize`][extension] applies its plan to any root queryset. If the consumer's root resolver already *evaluated* that queryset — a `len(qs)` guard, a `bool(qs)` branch, slicing for a log line — the optimizer's `.only()` / `.select_related()` clone silently re-executes the SQL: a doubled query invisible to the consumer. Upstream guards this twice (the resolve hook only optimizes when `ret._result_cache is None`; `optimize()` re-checks `is_optimized(qs) or qs._result_cache is not None`). The package has zero `_result_cache` references anywhere — the execution-state check is missing.

**G2 — the `.only()`-on-mutations gap.** The walker projects `only_fields` onto every root queryset identically, whatever the operation. Upstream disables `.only()` for non-`QUERY` operations (`enable_only and info.operation.operation == OperationType.QUERY`). The risk: a mutation resolver returning a queryset gets a selection-set-shaped `.only()`, so post-mutation consumer code touching any unprojected field triggers one deferred-field refetch query per access — and `Model.save()` on a deferred instance writes only loaded fields (Django's documented deferred-save semantics), a surprising interaction with signal handlers and downstream writes. The package has zero `OperationType` references — the operation gate is missing. This is **sequencing-critical**: the `0.0.11` mutations cohort makes mutation root resolvers returning querysets a mainstream consumer path, so the gate must land before that release bakes deferred-refetch storms and deferred-`save()` surprises into the first write-side surface.

**G3 — the fragment-type-condition gap.** The walker treats a fragment's `type_condition` purely as a fragment *marker* — [`selections.py::included_field_selections`][selections] inlines every fragment body unconditionally, and `type_condition` is read only to build the inline-fragment shell and to duck-type `is_fragment`, never *matched* against the planning type. Two verified failure modes on interface / union queries: (a) fields from sibling concrete types miss the current `field_map` and fall through the unknown-name `continue` guard ([`walker.py`][walker] line ~313), so every sibling-type relation selection is an N+1 the plan can never cover (strictness detects it at runtime — detection, not prevention); (b) a same-named relation existing on two union / interface members gets planned for the wrong branch — a spurious `select_related` join / over-projection (over-fetch, never wrong data). Upstream narrows by resolving each model's possible concrete types and re-walking hints per concrete type under a synthesized `ResolveInfo`; this card adopts the *narrowing outcome* through the registry, without the per-type re-walk.

None of the three is a feature; each is a parity-with-`strawberry_django` robustness item the audit pinned at a specific upstream line, and each closes a correctness or safety hole without changing the consumer-visible API surface.

## Current state

A true description of the repo as of this writing (the plan is written against it):

- **All three gaps are verified absent.** `grep -rn "_result_cache" django_strawberry_framework/` returns nothing (G1); `grep -rn "OperationType" django_strawberry_framework/` returns nothing (G2); `type_condition` appears in [`optimizer/selections.py`][selections] and [`optimizer/extension.py`][extension] only as a fragment *marker* (the inline-fragment shell at `selections.py` lines ~113–126, the `is_fragment` duck-type at line ~284, the runtime-prefix clone at line ~363) and is never matched against a planning type (G3).
- **The `_optimize` middleware path is the G1 site.** [`extension.py::DjangoOptimizerExtension._optimize`][extension] (line ~752) coerces a `Manager` to a fresh `.all()` queryset via the shared [`utils/querysets.py::normalize_query_source`][querysets] contract (line ~778 — **not** the `extension.py:714` the card cites; that line predates the DRY consolidation), resolves the return type to a `(origin, model)`, then delegates the plan-build-and-apply tail to `apply_to`, which runs `diff_plan_for_queryset` (B8 reconciliation) then `plan.apply(queryset)`. The guard inserts between the coercion gate and `apply_to`.
- **The connection field shares the apply tail but builds its own queryset.** [`DjangoConnectionField`][glossary-djangoconnectionfield]'s `apply_connection_optimization` calls the same `apply_to` helper, but on a pre-slice queryset the connection pipeline freshly built and never handed to a consumer resolver — so it is never consumer-evaluated and is out of G1 scope. G1 lands in `_optimize` only.
- **The walker entry point is the G2 / G3 site.** [`walker.py::plan_optimizations`][walker] (line ~63) is the single plan-build entry; it calls `_walk_selections`, which resolves the planning type via [`_resolve_field_map`][walker] (line ~122), inlines fragments via `_merge_aliased_selections(_included_field_selections(selections))` (line ~284), appends scalar columns to `plan.only_fields` (line ~361), and `continue`s past unknown names (line ~313). `info.operation.operation` is available on the threaded `info` for G2; `type_cls` / `definition` are in hand at the inlining call for G3.
- **The plan-cache key already separates operations.** [`extension.py::_build_cache_key`][extension] / `_print_operation_with_reachable_fragments` (lines ~1007 / ~355) key on the printed operation AST, which `print_ast(operation)` renders with the `query` / `mutation` / `subscription` keyword — so a query document and a mutation document never collide on one cache entry. G2's cache-safety needs no key change.
- **The O3 root gate is the reason G1 stays minimal.** The optimizer only runs at the operation root (`info.path.prev is None`, [`spec-002`][spec-002]); upstream's `is_optimized` flag and `_clone` monkeypatch exist to make its nested-capable optimizer idempotent across clones, a problem the root gate already solves here — so execution-state (`_result_cache`) is the only half of upstream's two-part guard this package needs.
- **B8 queryset diffing is the consumer-state precedent.** [`plans.py::diff_plan_for_queryset`][plans] already drops the optimizer's `only_fields` when the consumer applied their own `.only(...)` (consumer-wins) and reconciles `select_related` / `Prefetch` — the "respect what the consumer already did" posture G1 extends from optimization state to execution state.
- **FK-id elision falls back on a custom hook but not on operation type.** [FK-id elision][glossary-fk-id-elision] reads the FK column off the parent row for `{ rel { id } }` selections and falls back to a join when a target `get_queryset` must run; it has no operation-type condition today, and [Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations) keeps it that way.
- **The fragment substrate is shared across three call sites.** [`selections.py`][selections] hosts the single fragment-vs-field discriminator (`is_fragment`, duck-typed on `type_condition`) and the inlining primitive (`included_field_selections`), shared by the walker's plan build, the extension's cache-key walk, and the connection node-selection extraction — so a fragment-handling change made carelessly drifts all three. G3 threads its narrowing predicate only through the walker's call site; the cache-key and extraction paths pass no predicate and keep today's unconditional inlining.
- **The card's hard dependency is satisfied.** [`DONE-033-0.0.9`][kanban] (connection-aware optimizer planning) shipped and rewrote the `walker.py` / `selections.py` fragment-inlining seam G3 extends; landing G3 after it (rather than concurrently) is the card's own sequencing note, and lets G3's union / interface tests cover connection-wrapped fragments.
- **The joint-cut sibling is build-complete.** [`DONE-034-0.0.10`][kanban] (the permissions subsystem) has shipped all five slices; its `apply_cascade_permissions` is independent of these guards. The `0.0.10` joint cut releases both cards and owns the version bump; the on-disk version reads `0.0.9`.

## Goals

1. **Ship G1.** A `_result_cache`-present early-return in [`_optimize`][extension] so a consumer-evaluated root queryset passes through unchanged (same instance, no re-execution), with the manager-coercion path still optimizing — minimal shape, no upstream flag / monkeypatch (Slice 1, [Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize)).
2. **Ship G2.** Suppress `only_fields` for non-`QUERY` operations at plan-build time, keeping `select_related` / `prefetch_related`, with zero plan-cache key change and the query/mutation plans coexisting (Slice 2, [Decision 4](#decision-4--g2--operation-type-gating-of-only-suppress-only_fields-for-non-query-operations-at-plan-build-time)).
3. **Decide and pin FK-id elision under non-`QUERY` operations.** Resolve the card's open decision — elision stays enabled — and pin it with a dedicated test (Slice 2, [Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations)).
4. **Ship G3.** Registry-only fragment type-condition narrowing so an interface / union query stops planning sibling-concrete-type branches (closing the silent-N+1 class) and stops over-projecting same-named relations, with zero plan-cache key change and no per-request graphql-core introspection (Slice 3, [Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing) / [Decision 7](#decision-7--g3--narrow-do-not-multi-plan)).
5. **Preserve every B1–B8 advantage.** The plan cache (B1), FK-id elision (B2), strictness N+1 detection (B3), and class-creation-time `FieldMeta` precompute (B7) survive unchanged; strictness no longer false-fires for a correctly-narrowed sibling fragment, and the cache-hit path gains zero allocations (Slices 2–3, [Decision 7](#decision-7--g3--narrow-do-not-multi-plan)).
6. **Document what the optimizer will not touch.** The optimizer docs gain a short note covering evaluated querysets (G1) and non-query operations (G2) (Slice 4, [Doc updates](#doc-updates)).
7. **Keep package version state owned by the joint `0.0.10` cut.** No slice edits `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock` (Slice 4, [Decision 9](#decision-9--version-bumps-are-owned-by-the-joint-0010-cut)).

## Non-goals

- **Windowed nested-prefetch pagination and `totalCount` window-annotation reuse.** The two **performance** findings from the same 2026-06-11 audit are owned by [`DONE-033-0.0.9`][kanban] (connection-aware optimizer planning), already shipped — explicitly NOT this card ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **Upstream's `is_optimized()` flag, `CONFIG_KEY` queryset config, and `QuerySet._clone` monkeypatch.** The flag half of upstream's two-part G1 guard is redundant under the O3 root gate; only the execution-state check is adopted ([Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize)).
- **Per-concrete-type re-walk for G3.** Upstream resolves a model's possible concrete types (`get_possible_concrete_types`) and re-walks hints per concrete type under a synthesized `ResolveInfo`; this card narrows through the registry instead, planning the requested type once — narrow, do not multi-plan ([Decision 7](#decision-7--g3--narrow-do-not-multi-plan)).
- **Prefetch merging.** Upstream's `PrefetchInspector.merge` unions `only` sets and merges conflicting `Prefetch` querysets behind an `_optimizer_sentinel`; the package's consumer-wins drop in `diff_plan_for_queryset` ([`spec-004`][spec-004] B8) is a permission-boundary safety stance, not an oversight — deliberate non-adoption ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- **`GenericForeignKey` prefetch, django-polymorphic / `InheritanceManager` `select_subclasses` cooperation, and a `DjangoOptimizerExtension.disabled()` contextvar escape hatch.** Out-of-scope audit findings, recorded as spec non-goals.
- **Annotation hints (`field(annotate=...)`).** Upstream supports computed-DB-field auto-planning including `Info`-receiving callables; the package has no annotate path. Adjacent to the [`BACKLOG.md`][backlog] model-property / cached-property optimizer-hints item; promote together if scheduled.
- **A new public symbol, `Meta` key, or settings key.** All three guards are internal behavior refinements; no consumer-facing surface is added ([`AGENTS.md`][agents] #"Add settings keys only when the feature that needs them lands").
- **A version bump.** Owned by the joint `0.0.10` cut ([Decision 9](#decision-9--version-bumps-are-owned-by-the-joint-0010-cut)).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it? → foundational" test, all three guards are **Required `strawberry-graphql-django` parity** — the card's own parity tag (🍓 Required). `strawberry_django`'s optimizer guards execution state, gates `.only()` by operation type, and narrows fragment planning to concrete types; this package's optimizer does none of the three. The borrowing is at the **outcome** level: the package adopts the guard *behavior* with its own lighter mechanisms (the O3 root gate, the registry, the printed-AST cache key) rather than porting upstream's heavier machinery, because the package already holds four advantages over upstream the audit confirmed (the global LRU plan cache B1, FK-id elision B2, strictness N+1 detection B3, class-creation-time `FieldMeta` precompute B7) and must not regress them.

### Reference-package parity checkpoint

| Upstream (`strawberry_django/optimizer.py`) | `django-strawberry-framework` | Status |
| --- | --- | --- |
| resolve hook optimizes only when `ret._result_cache is None` (line 1781); `optimize()` re-guards `is_optimized(qs) or qs._result_cache is not None` (line 1628); `QuerySet._clone` monkeypatch carries the optimized flag (`queryset.py` 50–62) | G1: `_result_cache`-present early-return in [`_optimize`][extension] ([Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize)); the flag half is redundant under the O3 root gate | **this card (`0.0.10`) — required parity (execution-state half only)** |
| `enable_only and info.operation.operation == OperationType.QUERY` (lines 1784 / 1817) — `.only()` never applied to mutation / subscription querysets, select / prefetch stays on | G2: suppress `only_fields` for non-`QUERY` ops at plan-build time, keep `select_related` / `prefetch_related` ([Decision 4](#decision-4--g2--operation-type-gating-of-only-suppress-only_fields-for-non-query-operations-at-plan-build-time)) | **this card (`0.0.10`) — required parity** |
| per-concrete-type hint re-walk via `get_possible_concrete_types` (`utils/inspect.py` 206–245) + synthesized `ResolveInfo` (lines 1492–1517) | G3: registry-only `type_condition` narrowing in [`included_field_selections`][selections], plan the requested type once ([Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing) / [Decision 7](#decision-7--g3--narrow-do-not-multi-plan)) | **this card (`0.0.10`) — required parity (narrowing outcome; not the re-walk mechanism)** |
| `PrefetchInspector.merge` (`utils/inspect.py` 324–387) unions `only` sets / merges `Prefetch` querysets | consumer-wins drop in `diff_plan_for_queryset` ([`spec-004`][spec-004] B8) | deliberate non-adoption (permission-boundary stance) |
| `GenericForeignKey` prefetch / `select_subclasses` / `disabled()` contextvar | — | out of scope (recorded non-goals) |

### From `strawberry-graphql-django` — borrow the guard outcomes, not the mechanisms

Each guard is ported at the *behavior* level with the package's own seam:

- **G1** adopts the execution-state check (`_result_cache is not None` → pass through) but not the optimized-flag bookkeeping: the O3 root gate already guarantees single application, so a clone never re-enters the optimizer at a nested resolver the way upstream's nested-capable optimizer can.
- **G2** adopts the operation-type gate but lands it at plan-build time (the package's plan is cached by printed AST, which already separates operations — so the gate bakes into the right cache entry with zero key change), where upstream re-checks it at apply time inside a non-cached path.
- **G3** adopts the narrowing *result* (sibling-concrete-type branches don't plan) but resolves the concrete-type match through the package's own registry / definition metadata, planning the requested type once — never the per-concrete-type re-walk with a synthesized `ResolveInfo` that the package's single-plan-per-(document, model, origin) cache contract would fight.

### Explicitly do not borrow

- **The `is_optimized` flag + `_clone` monkeypatch** — monkeypatching `QuerySet._clone` is exactly the kind of upstream-internals coupling the package avoids; the O3 root gate makes it unnecessary ([Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize)).
- **The per-concrete-type re-walk** — multiplying the plan by concrete type contradicts the package's single-plan-per-key cache and its B7 precompute; the registry narrowing achieves the correctness outcome at a fraction of the walk cost ([Decision 7](#decision-7--g3--narrow-do-not-multi-plan)).
- **Prefetch merging** — the package's consumer-wins drop is a deliberate permission-boundary safety stance, not an oversight ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec file lives at **`docs/spec-035-optimizer_hardening-0_0_10.md`** (this document).

Justification:

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN and target patch into the filename. The card is `WIP-ALPHA-035-0.0.10`, so `<NNN>` is `035` and `<0_0_X>` is `0_0_10`.
- The topic slug is `optimizer_hardening` — the exact suffix the card's Definition of done names ("numbered to the card at implementation time, suffix `optimizer_hardening-0_0_10`") and the path the card's "Files likely touched" pre-pins (`docs/SPECS/spec-<NNN>-optimizer_hardening-0_0_10.md`).

Alternatives considered (and rejected):

- **The card's `docs/SPECS/`-rooted path.** The card DoD writes the spec into `docs/SPECS/` directly; the [`docs/SPECS/NEXT.md`][next] flow instead authors new specs at `docs/` root and archives prior specs into `docs/SPECS/` (Step 8). The active spec lands at `docs/spec-035-…`; the card's `docs/SPECS/` path is the eventual archive home, not the authoring location. Recorded, not silently reconciled, per the NEXT.md boundary rule.
- **Topic slug `optimizer_robustness` / `optimizer_guards`.** Rejected: the card DoD pins `optimizer_hardening` verbatim; matching it keeps the spec-reference link in the kanban `SpecDoc` stable.

### Decision 2 — Card-scope boundary: G1 / G2 / G3 only; the performance findings and the deferred-audit catalogue are out

This card ships exactly the three robustness guards G1, G2, G3 the card scopes, and nothing else from the 2026-06-11 audit:

- The two **performance** findings (windowed nested-prefetch pagination; `totalCount` window-annotation reuse) are owned by [`DONE-033-0.0.9`][kanban] and already shipped — the card is explicit they are NOT here.
- The deferred-audit findings (prefetch merging; `GenericForeignKey` prefetch; polymorphic `select_subclasses`; the `disabled()` contextvar; annotation hints) are recorded as spec non-goals ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)), each with the audit's rationale (deliberate non-adoption vs. unscheduled vs. adjacent-to-backlog).

Justification: the audit produced a 36-capability inventory; the card deliberately scoped three guards and parked the rest with explicit dispositions. The spec preserves those dispositions verbatim so a future reader sees which omissions are decisions (prefetch merging) versus deferrals (annotation hints) versus other-card ownership (windowed prefetch).

Alternatives considered (and rejected): **fold the cheap deferred findings (e.g. the `disabled()` contextvar) into this card.** Rejected: the card sized itself M around three guards; grafting "while I'm here" extras is the scope-creep [`START.md`][start] warns against, and each deferred finding has its own design surface.

### Decision 3 — G1 — evaluated-queryset guard: `_result_cache` early-return in `_optimize`

In [`extension.py::DjangoOptimizerExtension._optimize`][extension], after the [`utils/querysets.py::normalize_query_source`][querysets] coercion and its `is_queryset` gate and before the `apply_to` plan-build-and-apply tail, return the result unchanged when `getattr(result, "_result_cache", None) is not None`. Read with `getattr` (defensive access, the package posture). No `is_optimized` flag, no `CONFIG_KEY`, no `QuerySet._clone` monkeypatch.

Placement is load-bearing in two directions:

- **After the manager coercion.** [`normalize_query_source`][querysets] coerces a returned `Manager` (`Model.objects`) to a fresh `.all()` queryset whose `_result_cache` is `None` — so the guard must sit *after* the coercion, or a `Model.objects`-returning resolver would wrongly pass through unoptimized. (The card cites the old `extension.py:714` manager-coercion line; the live DRY home is `normalize_query_source` at line ~778 — recorded in [Risks](#risks-and-open-questions).)
- **Before `diff_plan_for_queryset` / `plan.apply`.** Once past the guard, `apply_to` clones the queryset to attach `select_related` / `only`; a `.only()` clone of an already-evaluated queryset re-executes the SQL. The guard's whole point is to never reach that clone for an evaluated queryset.

Scope is the `_optimize` middleware path only. [`DjangoConnectionField`][glossary-djangoconnectionfield] calls the same `apply_to` tail but on a pre-slice queryset the connection pipeline built and never handed to a consumer resolver — it is never consumer-evaluated, so it needs no guard. The async path (`_async_optimize` awaits the result then calls `_optimize`) inherits the guard unchanged.

Justification: this is upstream's execution-state check, minus the flag bookkeeping the package's O3 root gate makes redundant. Upstream guards twice (`_result_cache is None` at the resolve hook AND `is_optimized(qs) or qs._result_cache is not None` inside `optimize()`) because its optimizer can run at nested resolvers and must stay idempotent across `_clone` calls; the package's optimizer runs only at the operation root (`info.path.prev is None`), so a single execution-state check at the one entry is complete. It extends the [`spec-004`][spec-004] B8 "respect what the consumer already did" posture from optimization state (consumer `.only()` / `select_related` wins) to execution state (consumer-evaluated queryset is left alone).

Alternatives considered (and rejected):

- **Port the full upstream two-part guard (flag + `_clone` monkeypatch).** Rejected: monkeypatching `QuerySet._clone` couples the package to a Django private and exists upstream only to make a nested-capable optimizer idempotent — a problem the O3 root gate already solves. Carrying machinery for a scenario the architecture forbids is dead weight.
- **Guard inside `apply_to` (shared with the connection field) instead of `_optimize`.** Rejected: the connection field's queryset is framework-built and never evaluated, so guarding the shared tail would add a per-connection `getattr` check that can never fire — and would muddy the contract that `apply_to` optimizes whatever pre-built queryset it is handed. The risk is specific to consumer-returned querysets, which only reach `_optimize`.
- **Detect evaluation by `bool(qs._result_cache)` / `len`.** Rejected: `_result_cache` is `None` until evaluated and a (possibly empty) list after — `is not None` is the exact, allocation-free signal upstream uses; truthiness would mis-handle an evaluated-but-empty queryset.

### Decision 4 — G2 — operation-type gating of `.only()`: suppress `only_fields` for non-`QUERY` operations at plan-build time

In [`walker.py::plan_optimizations`][walker], when `info` is present and `info.operation.operation is not OperationType.QUERY`, suppress `only_fields` across the whole plan tree (root plan and every nested child plan) while leaving `select_related` / `prefetch_related` / `fk_id_elisions` intact. The gate is at **plan-build time** in the walker entry point, not apply time in [`plans.py`][plans].

Mechanism: thread the `enable_only` decision (derived once from `info.operation.operation`, defaulting to enabled when `info` is `None` for direct / test callers) through the walk so scalar columns are never appended to any plan's `only_fields`; the connector-column helper [`walker.py::_ensure_connector_only_fields`][walker] already no-ops when `only_fields` is empty, so suppressing scalar projection naturally suppresses connector columns too. Equivalent build-time spelling: clear `only_fields` on the root and recurse into child plans before `plan.finalize()`. Either lands the suppression inside the cached plan.

Cache-safety (zero key change): the plan-cache key's first component is the printed operation AST ([`extension.py::_print_operation_with_reachable_fragments`][extension]), and `print_ast(operation)` includes the `query` / `mutation` / `subscription` keyword — so a query document and a textually-identical-selection mutation document can never collide on one cache entry. The two plans (query-with-`only_fields`, mutation-without) coexist under distinct keys; gating at build time means each key caches the correct plan with no new key dimension.

Plan-wide suppression (root + nested): upstream's `enable_only` is a global gate on whether `.only()` is applied at all for the operation, not a root-only one. A mutation returning a queryset whose response selects nested relations would otherwise carry deferred-field sets on prefetched children too, with the same deferred-refetch / deferred-`save()` exposure on those child rows. Suppressing plan-wide matches upstream's behavior and removes the exposure everywhere it can occur.

Justification: G2 is sequencing-critical (the `0.0.11` mutations cohort makes mutation root querysets mainstream); landing it at plan-build time is the cache-correct placement (the printed-AST key already separates operations, so no key change is needed and the suppression is cached, not recomputed per request). `select_related` / `prefetch_related` stay on because they never carry the deferred-field hazard — they shape *which related rows load*, not *which columns of a row* are deferred.

Alternatives considered (and rejected):

- **Apply-time gate in [`plans.py::OptimizationPlan.apply`][plans].** Rejected: a plan built with `only_fields` then conditionally not applying them at apply time means the cache stores a `only_fields`-carrying plan that two operations (query and mutation) would want to apply differently — but the cache already separates them by printed-AST key, so building the right plan per key (build-time) is both simpler and avoids an apply-time branch on `info.operation`. The card pins build-time as preferred for exactly this cacheability reason.
- **Root-only suppression.** Rejected: leaves nested prefetched children carrying deferred-field sets under a mutation, reintroducing the deferred-refetch hazard one level down; upstream gates `.only()` operation-wide.
- **Suppress `select_related` / `prefetch_related` too under non-`QUERY`.** Rejected: those carry no deferred-field hazard and dropping them would reintroduce N+1s on a mutation's response selection — the hazard is specific to column deferral.

### Decision 5 — G2 — FK-id elision stays enabled under non-`QUERY` operations

The card's open decision, resolved: **FK-id elision remains enabled under mutation / subscription operations.** [FK-id elision][glossary-fk-id-elision] reads the FK `attname` column off the already-loaded parent row for a `{ relation { id } }` selection ([`types/resolvers.py::_build_fk_id_stub`][types-resolvers]); with G2 suppressing `only_fields`, the full source row loads, so the FK column the elision stub reads is always present — elision remains correct, and disabling it would force an avoidable join. Pinned by a dedicated test either way (the card requires the decision be test-pinned).

Justification: elision's correctness precondition is "the FK column is loaded on the parent row." G2 makes that *more* true under non-`QUERY` ops (no projection → every column loads), so elision is strictly safe there; it already falls back to a join whenever a target `get_queryset` must run, which is the only correctness-relevant fallback. Keeping elision on avoids a needless join on a mutation's `{ rel { id } }` response selection and preserves the B2 advantage uniformly across operation types.

Alternatives considered (and rejected): **disable elision for non-`QUERY` ops (gate it alongside `.only()`).** Rejected: there is no correctness motive — the deferred-field hazard G2 addresses is about *column deferral*, and elision under suppressed `only` operates on a fully-loaded row; disabling it trades a correct single-query elision for an unnecessary join. The decision is pinned with `test_fk_id_elision_enabled_under_mutation` so a future reader sees it was chosen, not overlooked.

### Decision 6 — G3 — registry-only fragment type-condition narrowing

[`selections.py::included_field_selections`][selections] gains an optional narrowing predicate; [`walker.py`][walker] supplies it at the point the planning `type_cls` / `definition` are resolved (the `_merge_aliased_selections(_included_field_selections(...))` call at line ~284, after [`_resolve_field_map`][walker]). The rule:

- A fragment with `type_condition is None` (an anonymous inline fragment, `... { f }`) **always inlines** — it carries no type condition and applies to the enclosing type.
- A fragment with a non-`None` `type_condition` inlines **only when** the condition's type name matches the current planning type: its own GraphQL name ([`types/definition.py::DjangoTypeDefinition.graphql_name`][definition]), a name in its [`Meta.interfaces`][glossary-metainterfaces], or the registered primary type name for the model. Otherwise the fragment subtree is skipped entirely.
- Names resolve through the registry / definition metadata only — **no graphql-core schema lookups** in the walk, preserving the B7 zero-per-request-introspection invariant.

The predicate is threaded **only** through the walker's call site. The extension's cache-key walk and the connection node-selection extraction ([`selections.py::named_children`][selections] / `node_children_with_runtime_prefix`) pass no predicate and keep today's unconditional inlining — they don't plan relations, so the over-fetch / silent-N+1 hazards don't apply there. A nested connection's node selection re-enters `_walk_selections` against the node's model, so a fragment inside `edges { node { ...Frag } }` is narrowed against the node's planning type at that recursion level; the connection-wrapped-fragment test pins this.

This fixes both verified failure modes: (a) sibling-concrete-type fields no longer reach the unknown-name `continue` guard (line ~313) because the sibling fragment is skipped before inlining — so the silent-N+1 branch the plan could never cover is gone; (b) a same-named relation on two members is planned only for the matching branch — the spurious `select_related` join / over-projection disappears.

Cache-safety (zero key change): the narrowing is a pure function of `(document, target_model, origin)` — the fragment bodies come from the document, the planning type from the origin, the model from the model — all three already plan-cache key components ([`extension.py::_build_cache_key`][extension]). Narrowed plans cache correctly with no new key dimension.

Justification: `type_condition` is already carried through the substrate (the inline-fragment shell, the `is_fragment` duck-type); G3 is the first code to *match* it against the planning type. Resolving the match through the registry (the type's `graphql_name`, its `interfaces`, the model's primary name) reuses the exact metadata [`Schema audit`][glossary-schema-audit] already descends and keeps the walk free of per-request schema introspection. Threading the predicate only through the walker (not the shared primitive's other callers) contains the change to the one path that plans relations.

Alternatives considered (and rejected):

- **graphql-core schema lookup of possible types per fragment.** Rejected: violates the B7 invariant (zero per-request Django / schema introspection); the registry already answers "does this planning type satisfy this type condition" from finalized metadata.
- **Narrow inside the shared primitive for all three callers.** Rejected: the cache-key walk and connection extraction don't plan relations, so narrowing them changes printed output / extraction with no correctness gain and real drift risk; the predicate is opt-in per call site.
- **Skip only the unknown-name fields, not the whole fragment subtree.** Rejected: a sibling-type fragment can name a relation that happens to exist on the planning type too (failure mode (b)); skipping field-by-field on the unknown-name guard misses the same-named-relation over-fetch. Skipping the non-matching fragment subtree whole is the correct granularity.

### Decision 7 — G3 — narrow, do not multi-plan

The narrowing plans the *requested* type once and excludes non-matching fragment subtrees; it does **not** resolve a model's possible concrete types and re-walk hints per concrete type under a synthesized `ResolveInfo` (upstream's `get_possible_concrete_types` + per-type re-walk). The package narrows; it does not multi-plan.

Justification: the package's plan cache stores one plan per `(document, target_model, origin)` key; a per-concrete-type re-walk would either multiply cache entries or build a union plan that re-introduces the over-projection G3 removes. The registry narrowing achieves the correctness outcome (sibling branches don't plan; same-named relations plan only for the matching branch) at one extra set-membership check per fragment, preserving B7 precompute and the single-plan-per-key contract. Upstream multi-plans because its optimizer lacks the package's class-creation-time metadata and global plan cache — the package doesn't need to.

Alternatives considered (and rejected): **adopt upstream's per-concrete-type re-walk for completeness.** Rejected: it fights the package's cache contract and B7 advantage for a correctness outcome the narrowing already achieves; the card is explicit ("we narrow, we do not multi-plan").

### Decision 8 — Module and test locations: no new module; optimizer edits + `tests/optimizer/`

- **Source:** edits only — [`optimizer/extension.py`][extension] (G1), [`optimizer/walker.py`][walker] (G2 suppression + G3 predicate supply), [`optimizer/selections.py`][selections] (G3 predicate parameter), and [`optimizer/plans.py`][plans] only if the G2 gate were to land at apply time (it does not — [Decision 4](#decision-4--g2--operation-type-gating-of-only-suppress-only_fields-for-non-query-operations-at-plan-build-time) pins build-time). No new module, no new subpackage.
- **Tests:** extend [`tests/optimizer/test_extension.py`][test-opt-extension] (G1 pass-through, G2 operation gating, FK-id-elision decision, strictness) and [`tests/optimizer/test_walker.py`][test-opt-walker] (G2 `only_fields` suppression at plan build, G3 fragment narrowing) — exactly the card's predicted files. No new test file.

Justification: all three guards are package-internal optimizer mechanics with no consumer-facing surface; the source files are the ones the card predicts, and tests mirror source one-to-one per [`docs/TREE.md`][tree]. Per the coverage placement rule in [`AGENTS.md`][agents], a package line reachable by a live GraphQL query is earned in `test_query/` — but none of these is: G2 needs a **mutation** operation (no mutation card ships before `0.0.11`), G1 needs a **consumer-evaluated** root queryset (a synthetic resolver that calls `len(qs)`), and G3 needs **synthetic union / interface** schemas with controlled fragment shapes. So the coverage is earned in `tests/optimizer/` with the unreachability reason recorded ([Test plan](#test-plan)).

Alternatives considered (and rejected): **a new `tests/optimizer/test_hardening.py`.** Rejected: the guards extend the contracts the predicted files already cover (extension behavior, walker plan content); co-locating the new pins beside the existing extension / walker coverage keeps the one-to-one mirror and the regression context together.

### Decision 9 — Version bumps are owned by the joint `0.0.10` cut

No slice edits `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], or `uv.lock`; no [`CHANGELOG.md`][changelog] release heading is promoted. CHANGELOG bullets land under `[Unreleased]`. The `0.0.10` patch line is shared with [`DONE-034-0.0.10`][kanban] (the permissions subsystem, build-complete); the version bump belongs to the **joint cut** that releases both cards — and lands only after the still-pending `0.0.9` cut is taken. This card adds no public symbol, so unlike [`spec-034`][spec-034]'s Slice 1 there is not even an `__all__` exports-pin change here: the entire surface is internal optimizer behavior.

Justification: the exact precedent of [`spec-034`][spec-034] Decision 13 and [`spec-033`][spec-033] Decision 12, and the [`docs/SPECS/NEXT.md`][next] Step 6 mandate for multi-card patch versions — when multiple cards target one patch, the version bump is the joint cut's, not any single card's.

Alternatives considered (and rejected): **bump in Slice 4 since this card may land last of the two.** Rejected: landing order between `034` and `035` is a maintainer scheduling fact, not a spec fact; the cut is a maintainer release act with its own checklist regardless of which card's PR merges last.

## Implementation plan

The card ships as **three functional slices plus a doc + card-completion wrap**. Each functional slice is one PR; the three are mutually independent (G1 in `extension.py`, G2 in the walker entry, G3 in the fragment substrate), though Slice 3 lands after the [`DONE-033-0.0.9`][kanban] walker churn (already shipped) so its tests can cover connection-wrapped fragments. Line deltas are estimates.

| Slice | Files touched | New tests | Approx. line delta |
| --- | --- | --- | --- |
| 1 — G1 evaluated-queryset guard | [`optimizer/extension.py`][extension] (`_optimize` early-return); [`tests/optimizer/test_extension.py`][test-opt-extension] (extend) | ~3 (pass-through same-instance + one-query; manager-coercion still optimizes; async mirror) | `+60 / -2` |
| 2 — G2 operation-type `.only()` gating | [`optimizer/walker.py`][walker] (`plan_optimizations` `enable_only` gate); [`tests/optimizer/test_walker.py`][test-opt-walker] + [`tests/optimizer/test_extension.py`][test-opt-extension] (extend) | ~5 (mutation drops `only` keeps select/prefetch; identical query still projects; both plans coexist distinct keys; subscription gated; FK-id-elision-under-mutation pinned) | `+150 / -5` |
| 3 — G3 fragment type-condition narrowing | [`optimizer/selections.py`][selections] (predicate param) + [`optimizer/walker.py`][walker] (supply predicate); [`tests/optimizer/test_walker.py`][test-opt-walker] + [`tests/optimizer/test_extension.py`][test-opt-extension] (extend) | ~7 (sibling-type excluded; matching planned; interface-implementor planned; same-named-relation regression; anonymous inline still inlines; strictness no false-fire; connection-wrapped sibling narrowed) | `+170 / -10` |
| 4 — doc updates + card-completion wrap | [`docs/GLOSSARY.md`][glossary], [`docs/README.md`][docs-readme], [`README.md`][readme], [`CHANGELOG.md`][changelog], [`KANBAN.md`][kanban] | 0 (doc-only) | `+70 / -25` |

Total expected delta: ~400 lines net-positive — consistent with the card's M sizing. No version-file edits ([Decision 9](#decision-9--version-bumps-are-owned-by-the-joint-0010-cut)).

Staged-but-not-implemented seams follow the [`AGENTS.md`][agents] design-doc anchor discipline: a source-site `TODO(spec-035 Slice N)` comment naming this spec and the owning slice, paired with `NotImplementedError` where a call path must fail loudly, removed in the change that ships the slice. (Each slice ships its whole runtime surface, so no cross-slice seams are expected; the discipline applies if review splits a slice.)

## Edge cases and constraints

- **G1 — guard sits after manager coercion.** A `Model.objects`-returning resolver is coerced by [`normalize_query_source`][querysets] to a fresh `.all()` whose `_result_cache` is `None`; the guard must follow the coercion so that path still optimizes (pinned by `test_manager_coercion_still_optimizes`).
- **G1 — sliced-but-unevaluated queryset still optimizes.** `qs[:5]` returns a new queryset with limits but `_result_cache is None` until iterated; the guard does not fire, the optimizer plans it, and the slice composes (a `len(qs)` / `bool(qs)` / iteration is what sets `_result_cache`). The guard targets *evaluated* state, not *sliced* shape.
- **G1 — `.values()` / `.values_list()` returns are unchanged.** They resolve to non-model rows; the return-type resolution path already handles them as today, and the guard only adds a pass-through for the evaluated case — no new behavior on values querysets.
- **G1 — async path inherits the guard.** `_async_optimize` awaits the result then calls `_optimize`; an evaluated awaited queryset passes through identically (pinned by an async mirror test).
- **G2 — connector columns no-op when `only_fields` is empty.** [`_ensure_connector_only_fields`][walker] returns early when `plan.only_fields` is empty, so suppressing scalar projection under non-`QUERY` naturally suppresses connector-column appends — no special-casing needed.
- **G2 — subscription operations are gated identically.** `info.operation.operation is not OperationType.QUERY` covers both `MUTATION` and `SUBSCRIPTION`; the gate is "QUERY-only projects `only`," so subscriptions drop `only_fields` like mutations (pinned).
- **G2 — a mutation returning a non-queryset never reaches the gate.** The common mutation shape returns a model instance or a payload type, which `normalize_query_source` reports as non-queryset and `_optimize` passes through; the gate matters only for the (rarer) mutation-resolver-returns-queryset shape, which is exactly the `0.0.11` path the gate protects.
- **G2 — query and mutation plans coexist.** A query and a mutation with byte-identical selection sets get distinct printed-AST cache keys (the operation keyword differs), so the `only`-carrying query plan and the `only`-suppressed mutation plan never overwrite each other (pinned).
- **G2 — `info is None` defaults to enabled.** Direct / test callers of [`plan_optimizations`][walker] without `info` keep `only_fields` (the QUERY default) so existing unit tests that build plans without an operation are unaffected.
- **G3 — anonymous inline fragment always inlines.** `... { f }` carries `type_condition is None`; it applies to the enclosing type and is never narrowed (the existing `test_anonymous_inline_fragment_*` live coverage must stay green).
- **G3 — interface-typed planning.** When the planning type is shaped by `Meta.interfaces = (relay.Node,)` or another interface, a fragment `... on <Interface>` inlines because the interface name is in the planning type's interface set; a fragment `... on <SiblingConcreteType>` does not.
- **G3 — secondary-type planning and a `... on PrimaryType` fragment.** When a secondary [`DjangoType`][glossary-metaprimary] roots the walk (via `source_type`), a fragment naming the model's primary type inlines because the primary type name is in the accept set — the fields exist on the same model / columns, so this is permissive-but-safe. Pinned so the asymmetry is documented, not mistaken for a leak.
- **G3 — connection-wrapped fragments narrow at the node walk.** A fragment inside `edges { node { ...Frag } }` is narrowed against the node's planning type when `_walk_selections` re-enters for the node model, not at extraction time; the connection-wrapped-sibling test pins that the extraction helpers (which pass no predicate) don't defeat the narrowing.
- **G3 — strictness stays branch-sensitive.** Planned resolver keys remain keyed on `(type_cls, field, runtime_path)`; a correctly-narrowed sibling fragment's relation is neither planned nor executed (the resolver never runs for that concrete type), so [Strictness mode][glossary-strictness-mode] does not fire — the old silent-N+1 signature is gone, and no false positive replaces it (pinned, no regression in `tests/optimizer/` strictness coverage).
- **G3 — no per-request introspection.** The narrowing reads `graphql_name` / `interfaces` / the primary name from finalized definition metadata; it issues no graphql-core schema lookup in the walk (B7 invariant preserved).
- **Cross-guard — plan-cache key is untouched by all three.** G1 returns before plan build (no key involved); G2 and G3 are pure functions of components already in the key. The B1 cache-hit path gains zero allocations.
- **Cross-guard — multi-database behavior unchanged.** None of the three reads or writes a DB alias; `.using()` preservation and router hints ([Multi-database cooperation][glossary-multi-database-cooperation]) are untouched.

## Test plan

Tests live in the package-internal [`tests/optimizer/`][test-opt-extension] tree, per [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]. The live-HTTP-priority rule's exception applies and is recorded: G1 needs a consumer-evaluated root queryset (a synthetic resolver calling `len(qs)`), G2 needs a **mutation** operation (no mutation card ships before `0.0.11`), and G3 needs synthetic union / interface schemas with controlled fragment shapes — none is reachable by a single live products GraphQL query, so each is earned in `tests/optimizer/` with the unreachability reason above.

### Slice 1 — G1 (`tests/optimizer/test_extension.py`, extend)

- `test_evaluated_queryset_passes_through_unchanged` — a root resolver evaluates the queryset (`len(qs)`) then returns it; assert exactly one SQL query total and that the returned object is the SAME queryset instance, not a re-executing clone.
- `test_manager_coercion_still_optimizes` — a resolver returning `Model.objects` still optimizes (the guard sits after [`normalize_query_source`][querysets]; the coerced `.all()` is unevaluated).
- `test_async_evaluated_queryset_passes_through` — the async mirror: an awaited, already-evaluated queryset passes through unchanged through `_async_optimize`.

### Slice 2 — G2 (`tests/optimizer/test_walker.py` + `tests/optimizer/test_extension.py`, extend)

- `test_mutation_queryset_drops_only_keeps_select_prefetch` — a mutation operation whose root resolver returns a queryset produces a plan with empty `only_fields` while `select_related` / `prefetch_related` survive.
- `test_query_identical_selection_still_projects_only` — a textually-identical selection set under a `query` operation still projects `only_fields`.
- `test_query_and_mutation_plans_coexist_distinct_keys` — both plans live in the cache under distinct printed-AST keys (no overwrite).
- `test_subscription_operation_gated` — a subscription operation drops `only_fields` under the same gate.
- `test_fk_id_elision_enabled_under_mutation` — the [Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations) pin: a `{ rel { id } }` selection under a mutation still elides (full row loads, FK column present), no join.

### Slice 3 — G3 (`tests/optimizer/test_walker.py` + `tests/optimizer/test_extension.py`, extend)

- `test_sibling_type_fragment_excluded_from_plan` — on an interface / union query, sibling-concrete-type fragment bodies are excluded from the plan (no spurious `select_related` / `only` entries).
- `test_matching_type_fragment_planned` / `test_interface_implementor_fragment_planned` — a fragment matching the planning type's own name, and one matching an interface it implements, both still inline and plan.
- `test_same_named_relation_on_two_members_regression` — a relation named identically on two union / interface members is planned only for the matching branch (no over-projection on the other).
- `test_anonymous_inline_fragment_still_inlines` — `... { f }` (`type_condition is None`) inlines unchanged.
- `test_strictness_no_false_fire_for_narrowed_sibling_fragment` — strictness `"warn"` / `"raise"` no longer fires for a correctly-narrowed sibling fragment the resolver never executes; B3 keys stay branch-sensitive.
- `test_connection_wrapped_sibling_fragment_narrowed` — a sibling-type fragment inside `edges { node { ...Frag } }` is narrowed at the node walk (extraction helpers don't defeat it).

## Doc updates

Each slice owns its own doc edits. The CHANGELOG-edit permission comes from Slice 4's doc-update step per the explicit-instruction rule at [`AGENTS.md`][agents] #"Do not update CHANGELOG.md unless explicitly instructed" — **AGENTS.md prohibits `CHANGELOG.md` edits without permission, and this spec's Slice 4 grants that permission**; the Slice 4 maintainer prompt must name the `CHANGELOG.md` edits explicitly so an agent does not infer permission from a standing document.

- **Slice 4 — GLOSSARY** ([`docs/GLOSSARY.md`][glossary]). **Net-new entries: none** — all three guards are refinements of shipped surfaces, appended to existing bodies:
  - [`DjangoOptimizerExtension`][glossary-djangooptimizerextension]: add G1 (evaluated-queryset pass-through) and G2 (non-`QUERY` `.only()` suppression) to the shipped-behavior list, and a one-line "what the optimizer will not touch" note.
  - [`only()` projection][glossary-only-projection]: note the G2 operation-type gate — `.only()` is applied for `QUERY` operations only; mutation / subscription querysets keep `select_related` / `prefetch_related` but no column deferral.
  - [Strictness mode][glossary-strictness-mode]: note the G3 outcome — interface / union sibling-concrete-type branches are now narrowed out of the plan rather than detected at runtime, so the old silent-N+1 signature is gone from that path.
  - [FK-id elision][glossary-fk-id-elision]: a one-line note that elision stays enabled under non-`QUERY` operations ([Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations)).
- **Slice 4 — package docs**
  - [`docs/README.md`][docs-readme]: the optimizer paragraph gains the "what the optimizer will not touch" sentence (evaluated querysets, non-query operations); the "Coming next" `0.0.10` line drops the `035` remainder as the joint cut completes.
  - [`README.md`][readme]: the optimizer status line gains a short robustness note (the package's optimizer now guards consumer-evaluated querysets and non-query operations).
  - [`CHANGELOG.md`][changelog]: `### Changed` / `### Fixed` bullets under `[Unreleased]` for G1 / G2 / G3 (the explicit per-card permission grant named in the Slice 4 maintainer prompt). No version-heading promotion (per [Decision 9](#decision-9--version-bumps-are-owned-by-the-joint-0010-cut)).
  - [`TODAY.md`][today]: **no edit** — `TODAY.md` is products-capability-centric, and these guards are internal optimizer robustness with no products-visible surface change (the optimizer already plans products queries; G1 / G2 / G3 only refine edge behaviors products doesn't exercise). Recorded here so the omission reads as deliberate.
- **Slice 4 — card-completion wrap**
  - [`KANBAN.md`][kanban]: move [`WIP-ALPHA-035-0.0.10`][kanban] to Done with the next `DONE-NNN-0.0.10` id; set the card's spec reference to `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (its archive home after the [`docs/SPECS/NEXT.md`][next] Step 8 sweep — a `SpecDoc` DB edit re-rendered via `scripts/build_kanban_md.py`, not a hand edit). No version-file edits.

## Risks and open questions

Each item names a preferred answer for the current cut and a fallback if implementation reveals the preferred answer is wrong.

- **G2 FK-id elision under non-`QUERY` operations (the card's open decision).** Preferred answer ([Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations)): keep elision enabled — with `only` suppressed the full row loads, the FK column is present, elision is correct and avoids a join. Fallback: if a real consumer surfaces a deferred-elision interaction under mutations (none is known, and the elision-correctness precondition is strictly better satisfied with `only` suppressed), gate elision alongside `.only()` — a one-line addition to the same operation-type branch, test-pinned either way.
- **G2 nested-plan `only_fields` suppression scope.** Preferred answer: suppress plan-wide (root + nested child plans), matching upstream's operation-wide `enable_only`. Fallback: if a consumer relies on nested child-row projection under a mutation (and accepts the deferred-refetch hazard on those children), root-only suppression is a contained narrowing — but it reintroduces the exact hazard one level down, so plan-wide is the safe default.
- **G3 connection-wrapped fragment narrowing.** Preferred answer: narrowing happens at each `_walk_selections` entry (the node model's planning type), so connection-wrapped fragments narrow without touching the extraction helpers. Fallback: if a test shows the extraction helpers ([`named_children`][selections] / `node_children_with_runtime_prefix`) flatten a fragment before the node walk re-resolves type, thread the same predicate into those helpers — a contained extension of the Decision 6 mechanism.
- **G3 `... on PrimaryType` fragment when planning a secondary type.** Preferred answer: accept the primary type name in the accept set (same model, same columns — permissive but safe). Fallback: strict `graphql_name`-only match (drop the primary-name acceptance) if a consumer's secondary type intentionally diverges field-shape from the primary and the permissive match over-plans — pinned by the secondary-planning test so the choice is visible.
- **Card-citation correction: the manager-coercion line.** The card cites `extension.py:714` for the manager coercion the G1 guard must follow; the live DRY home is [`utils/querysets.py::normalize_query_source`][querysets] called at [`extension.py`][extension] line ~778 (the line:714 reference predates the consolidation). Preferred answer: ground the guard on `normalize_query_source` (the live seam); the placement contract ("after coercion, before `diff_plan_for_queryset`") is unchanged. Fallback: none needed — the seam moved, not the contract.
- **Card-citation correction: the fragment-inlining anchors.** The card cites `walker.py:733` / `walker.py:845` for the fragment inlining and the `type_condition` marker; the live primitive is [`selections.py::included_field_selections`][selections] (inlined at [`walker.py`][walker] line ~284) with the unknown-name `continue` guard at line ~313 and the marker uses in [`selections.py`][selections]. Preferred answer: ground G3 on the live `selections.py` primitive. Fallback: none needed — the [`DONE-033-0.0.9`][kanban] connection work moved the inlining into the shared `selections.py` substrate; the gap (unconditional inlining) is unchanged.
- **Line-number anchors in the card go stale.** The card's `Verified in upstream` block pins specific `strawberry_django/optimizer.py` line numbers (1781 / 1628 / 1784 / 1817 / 1492–1517) against an upstream checkout; those are reference anchors for the *mechanism*, not a contract this card must reproduce line-for-line. Preferred answer: cite upstream by file:line in prose as the audit did, treat the *behavior* as the contract. Fallback: none needed.
- **No new module / no settings key.** The guards are edits to three existing optimizer modules; no `permissions.py`-style new module and no `DJANGO_STRAWBERRY_FRAMEWORK` entry. Preferred answer: keep it that way. Fallback: none anticipated.

## Out of scope (explicitly tracked elsewhere)

- **Windowed nested-prefetch pagination + `totalCount` window-annotation reuse** — the performance half of the 2026-06-11 audit, owned by [`DONE-033-0.0.9`][kanban] ([Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]), shipped.
- **Permissions cascade** ([`apply_cascade_permissions`][glossary-apply_cascade_permissions]) — [`DONE-034-0.0.10`][kanban], the joint-`0.0.10`-cut sibling; independent of these guards.
- **Prefetch merging** (`PrefetchInspector.merge`) — deliberate non-adoption; the package's consumer-wins drop in `diff_plan_for_queryset` ([`spec-004`][spec-004] B8) is a permission-boundary safety stance, revisited only behind a strict no-custom-filter merge precondition.
- **`GenericForeignKey` prefetch, django-polymorphic / `InheritanceManager` `select_subclasses` cooperation, and a `DjangoOptimizerExtension.disabled()` contextvar escape hatch** — out-of-scope audit findings, recorded as spec non-goals.
- **Annotation hints** (`field(annotate=...)`, including `Info`-receiving callables) — not scheduled; adjacent to the [`BACKLOG.md`][backlog] model-property / cached-property optimizer-hints item; promote together if scheduled.
- **The `0.0.11` mutations cohort** ([`DjangoMutation`][glossary-djangomutation] et al. and [Auth mutations][glossary-auth-mutations]) — the consumer G2 protects; nothing mutation-shaped lands here.
- **Version bump** — owned by the joint `0.0.10` cut ([Decision 9](#decision-9--version-bumps-are-owned-by-the-joint-0010-cut)).

## Definition of done

The completion contract the card is built against. Items are grouped by slice; the card completes when all three functional slices' items plus the wrap are satisfied. The card's own DoD bullets map onto item 1 (spec), 2 (G1), 3–5 (G2 + the elision decision), 6–8 (G3), 9 (strictness + no regression), and 10–11 (docs + version boundary).

**Spec + companion CSV**

1. `docs/spec-035-optimizer_hardening-0_0_10.md` (this document) is at the canonical structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with companion `spec-035-optimizer_hardening-0_0_10-terms.csv` anchoring every project-specific term that has a [`docs/GLOSSARY.md`][glossary] heading; `uv run python scripts/check_spec_glossary.py --spec docs/spec-035-optimizer_hardening-0_0_10.md` reports `OK: <N> terms`. The card introduces no net-new public symbol, so no new glossary heading is required.

**Slice 1 — G1 evaluated-queryset guard**

2. [`optimizer/extension.py::_optimize`][extension] returns the result unchanged when `getattr(result, "_result_cache", None) is not None`, after the [`normalize_query_source`][querysets] coercion and before `apply_to`; a test pins the pass-through (root resolver evaluates then returns; exactly one SQL query total; returned object is the SAME instance), the manager-coercion path still optimizes, and the async mirror ([Decision 3](#decision-3--g1--evaluated-queryset-guard-_result_cache-early-return-in-_optimize)).

**Slice 2 — G2 operation-type `.only()` gating**

3. A mutation operation whose root resolver returns a queryset produces a plan with empty `only_fields` while `select_related` / `prefetch_related` survive; a textually-identical selection under a `query` operation still projects `only_fields`; both plans coexist in the cache under distinct printed-AST keys; subscription operations are covered by the same gate ([Decision 4](#decision-4--g2--operation-type-gating-of-only-suppress-only_fields-for-non-query-operations-at-plan-build-time)).
4. The gate lands at plan-build time in [`walker.py::plan_optimizations`][walker] with zero plan-cache key change (the printed-AST key already separates operations).
5. The FK-id-elision-under-non-`QUERY` decision is resolved (elision stays enabled) and pinned by a dedicated test ([Decision 5](#decision-5--g2--fk-id-elision-stays-enabled-under-non-query-operations)).

**Slice 3 — G3 fragment type-condition narrowing**

6. A fragment with a non-`None` `type_condition` inlines only when the condition matches the current planning type (own GraphQL name / an interface name / the model's primary name), resolved through the registry / definition with no per-request graphql-core introspection; anonymous inline fragments still inline ([Decision 6](#decision-6--g3--registry-only-fragment-type-condition-narrowing) / [Decision 7](#decision-7--g3--narrow-do-not-multi-plan)).
7. Union / interface fragment tests: sibling-concrete-type fragment bodies are excluded from the plan (no spurious `select_related` / `only`); matching-type and interface-implementor fragments still plan; the same-named-relation-on-two-members shape is a dedicated regression; a connection-wrapped sibling fragment narrows too.
8. The narrowing is contained to the walker's call site — the extension cache-key walk and connection extraction keep today's unconditional inlining (no behavior change there).

**Slice 3 / cross-cutting — strictness + no regression**

9. Strictness `"warn"` / `"raise"` no longer fires for a correctly-narrowed sibling fragment the resolver never executes (the old silent-N+1 signature is gone), B3 keys stay branch-sensitive, and there are no B1–B8 regressions: full optimizer suite green at the 100% coverage gate (`fail_under = 100`), the cache-hit path gains zero allocations, `ruff format` + `ruff check` clean.

**Slice 4 — doc + card-completion wrap**

10. [`docs/GLOSSARY.md`][glossary] appends G1 / G2 / G3 to the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] / [`only()` projection][glossary-only-projection] / [Strictness mode][glossary-strictness-mode] / [FK-id elision][glossary-fk-id-elision] bodies (no new heading); [`docs/README.md`][docs-readme] / [`README.md`][readme] gain the "what the optimizer will not touch" note; [`CHANGELOG.md`][changelog] `[Unreleased]` carries the bullets (the explicit per-card permission grant named in the Slice 4 maintainer prompt); [`KANBAN.md`][kanban] records the card as `DONE-NNN-0.0.10` with the spec reference pointing at `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (kanban DB + re-render).
11. **No version bump lands in this card** per [Decision 9](#decision-9--version-bumps-are-owned-by-the-joint-0010-cut): `pyproject.toml`, `__version__`, [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` are unchanged; no [`CHANGELOG.md`][changelog] release heading is promoted (the joint `0.0.10` cut owns the bump, after the pending `0.0.9` cut). This card adds no public symbol, so the `__all__` exports pin is also untouched.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[backlog]: ../BACKLOG.md
[changelog]: ../CHANGELOG.md
[contributing]: ../CONTRIBUTING.md
[kanban]: ../KANBAN.md
[readme]: ../README.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[docs-readme]: README.md
[glossary]: GLOSSARY.md
[glossary-apply_cascade_permissions]: GLOSSARY.md#apply_cascade_permissions
[glossary-auth-mutations]: GLOSSARY.md#auth-mutations
[glossary-configurationerror]: GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: GLOSSARY.md#connection-aware-optimizer-planning
[glossary-djangoconnectionfield]: GLOSSARY.md#djangoconnectionfield
[glossary-djangomutation]: GLOSSARY.md#djangomutation
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: GLOSSARY.md#djangotype
[glossary-fk-id-elision]: GLOSSARY.md#fk-id-elision
[glossary-metainterfaces]: GLOSSARY.md#metainterfaces
[glossary-metaoptimizer_hints]: GLOSSARY.md#metaoptimizer_hints
[glossary-metaprimary]: GLOSSARY.md#metaprimary
[glossary-multi-database-cooperation]: GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: GLOSSARY.md#only-projection
[glossary-optimizerhint]: GLOSSARY.md#optimizerhint
[glossary-plan-cache]: GLOSSARY.md#plan-cache
[glossary-queryset-diffing]: GLOSSARY.md#queryset-diffing
[glossary-relation-handling]: GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: GLOSSARY.md#relay-node-integration
[glossary-schema-audit]: GLOSSARY.md#schema-audit
[glossary-strictness-mode]: GLOSSARY.md#strictness-mode
[tree]: TREE.md

<!-- docs/SPECS/ -->
[next]: SPECS/NEXT.md
[spec-002]: SPECS/spec-002-optimizer-0_0_2.md
[spec-004]: SPECS/spec-004-optimizer_beyond-0_0_3.md
[spec-033]: SPECS/spec-033-connection_optimizer-0_0_9.md
[spec-034]: SPECS/spec-034-permissions-0_0_10.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[definition]: ../django_strawberry_framework/types/definition.py
[extension]: ../django_strawberry_framework/optimizer/extension.py
[field-meta]: ../django_strawberry_framework/optimizer/field_meta.py
[plans]: ../django_strawberry_framework/optimizer/plans.py
[querysets]: ../django_strawberry_framework/utils/querysets.py
[selections]: ../django_strawberry_framework/optimizer/selections.py
[types-resolvers]: ../django_strawberry_framework/types/resolvers.py
[walker]: ../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-base-init]: ../tests/base/test_init.py
[test-opt-extension]: ../tests/optimizer/test_extension.py
[test-opt-walker]: ../tests/optimizer/test_walker.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-optimizer]: https://github.com/strawberry-graphql/strawberry-django/blob/main/strawberry_django/optimizer.py
