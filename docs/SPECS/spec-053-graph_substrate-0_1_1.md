# Spec: graph substrate — shared graph policy and dependency planning

Planned for `0.1.1` (card `TODO-BETA-053-0.1.1`, created 2026-08-07 as the
first Beta card on [`KANBAN.md`][kanban], sequenced ahead of
`TODO-BETA-054-0.1.1`; the former cards 053-068 shifted up by one, and this
spec's filename follows the card,
see [Decision 1](#decision-1--one-substrate-card-created-and-sequenced-before-layer-3-freezes)).
`TODO-BETA-054-0.1.1` shares this patch version and lands after this card, so
the `0.1.1` version bump belongs to the joint cut and this spec defers every
release-state artifact to card 054
([Decision 10](#decision-10--joint-cut-at-011--release-state-defers-to-card-054)).

This is the first of two foundation cards — the framework-internal
graph-planning vocabulary (`GraphPathPlan`, `PredicatePlan`, `EdgeScope`,
`FieldDependencyPlan`, `RowIdentityProof`) plus the operation-scoped
dependency memo, extracted into one shared package boundary **before**
[`FieldSet`][glossary-fieldset] (card 054), search (card 055), and
[`AggregateSet`][glossary-aggregateset] (card 057) freeze three private
versions of the same machinery. The second foundation card (structural
optimization templates + nested sidecar batching) is **not** this spec; it is
tracked under `Out of scope`.

The consumer surface stays Meta-declared per [`GOAL.md`][goal]: whatever
public declaration shape ships arrives as `class Meta` keys or sidecar `Set`
classes consistent with [`Meta.filterset_class`][glossary-metafilterset_class]
/ [`Meta.orderset_class`][glossary-metaorderset_class] /
[`Meta.fields_class`][glossary-metafields_class] — never stacked decorators,
never a parallel imperative registration API. The plan objects themselves are
internal vocabulary, not shipped API.

Status: **PLANNED — no slice built yet; card created
(`TODO-BETA-053-0.1.1`); the consumer-card amendments are still to land.**
Five slices: Slice 1 (**`graph/` package + operation dependency memo**),
Slice 2 (**`GraphPathPlan` + path/lookup splitter + `RowIdentityProof`
vocabulary**), Slice 3 (**`PredicatePlan` compiler** — sequential-fold
boolean composition, correlated branches, same-related-row groups,
exact-owner re-entry), Slice 4 (**`EdgeScope` + `FieldDependencyPlan` + Meta
surface + live fakeshop activation**), Slice 5 (**docs + glossary entries +
tracked-path constants + card wrap**).

Permission caveat: [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits
without explicit permission. This spec grants none — the `0.1.1` entry, the
version quintet, and all release-state prose are owned by the card-054 joint
cut ([Decision 10](#decision-10--joint-cut-at-011--release-state-defers-to-card-054)).

---

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [`FieldSet`][glossary-fieldset] — planned for `0.1.1` (card 054); consumes
  `FieldDependencyPlan` per this spec's amendment obligation
  ([Decision 8](#decision-8--fielddependencyplan-normalizes-metadepends_on)).
- [`Meta.search_fields`][glossary-metasearch_fields] — planned for `0.1.2`
  (card 055); its path planning moves onto `GraphPathPlan` per the amendment
  scope [Decision 2](#decision-2--a-dedicated-graph-package-boundary) pins.
- [`AggregateSet`][glossary-aggregateset] / [`RelatedAggregate`][glossary-relatedaggregate]
  / [`get_child_queryset`][glossary-get_child_queryset] — planned for `0.1.3`
  (card 057); consume `EdgeScope` instead of a private child-visibility hook.
- [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook] —
  shipped; the binding slot `PredicatePlan` and `EdgeScope` compose with.
- [`apply_cascade_permissions`][glossary-apply_cascade_permissions] — shipped;
  deliberately forward-FK/one-to-one only. `EdgeScope` is the to-many
  complement, not a broadening of cascade
  ([Decision 7](#decision-7--edgescope-composes-into-the-child-queryset-not-a-broader-cascade)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — shipped
  and **optional**; one of two installers of the memo scope, never its owner
  ([Decision 3](#decision-3--the-memo-is-execution-scoped-immutable-values-only-owned-by-graph)).
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]
  — shipped; the windowed nested strategy the proof vocabulary feeds
  (enforcement is the sibling card's).
- [Plan cache][glossary-plan-cache] — shipped; this card keeps request values
  out of it and prepares the structural/bound split the sibling card ships.
- [Strictness mode][glossary-strictness-mode] — shipped; edge plans publish
  resolver keys only after successful attachment.
- [Multi-database cooperation][glossary-multi-database-cooperation] — shipped;
  every memo key and bound plan carries the database alias.
- [`FilterSet`][glossary-filterset] / [`RelatedFilter`][glossary-relatedfilter]
  — shipped; `_apply_flat_leaves` / `_apply_related_constraints` are
  *precedent* for row preservation. The reuse target is the primitives
  (`utils/predicates.py` after the Slice 3 relocation), never the
  django-filter-coupled applicators
  ([Decision 4](#decision-4--predicateplan-compiles-through-the-shipped-row-preserving-primitives)).
- [`finalize_django_types`][glossary-finalize_django_types] — shipped; hosts
  only the target-type-dependent residue of `Meta.edge_scopes` validation
  (the bulk validates at type creation, Decision 11).
- [`DjangoType`][glossary-djangotype] / [`DjangoConnectionField`][glossary-djangoconnectionfield]
  — shipped; the owning surfaces for exact-owner identity.
- [`Meta.relation_shapes`][glossary-metarelation_shapes] — shipped; the
  closest structural analogue for `Meta.edge_scopes` validation (two-stage,
  at type creation).
- [`request_from_info`][glossary-request_from_info] — shipped; the only
  supported way to reach the request from `info` (three context shapes);
  `graph.scope_key` builds on it.
- [`SyncMisuseError`][glossary-syncmisuseerror] — shipped; the color-misuse
  error `edge_scopes` factories reuse.
- [Sealed execution queryset][glossary-sealed-execution-queryset] /
  [Visibility boundary][glossary-visibility-boundary] — shipped; every
  `graph.apply` output passes the same seal (edge factories return
  predicates, never replacement querysets — Decision 7).
- [Joint version cut][glossary-joint-version-cut] — the release-state
  ownership rule Decision 10 applies.

## Slice checklist

- [ ] **Slice 1 — `graph/` package + operation dependency memo.** New package
  `django_strawberry_framework/graph/` with `graph/memo.py`: a module-level
  `ContextVar` store owned by `graph/`, exposed as one public bracket
  (`graph.memo.operation_scope()`), `get_or_compute(info, key, factory)`,
  and `graph.scope_key(info, queryset)` built on
  [`request_from_info`][glossary-request_from_info] (pre-baking viewer
  identity and `queryset.db`). Installers: a two-line delegation in
  `optimizer/extension.py::DjangoOptimizerExtension.on_execute`
  (install `.set({})` once in the caller's context, `.reset(token)` in
  `finally`, mutate the dict — never `.set()` per entry, per the
  `_cache_key_parts_cache` precedent; the reset is ordered so the graph
  store outlives the optimizer's own per-execution memos — a consumer
  `get_queryset` hook reached through `resolve` reads the memo, and no
  optimizer memo reads the graph store) **and** a new shipped
  `django_strawberry_framework/extensions/graph.py::GraphSubstrateExtension`
  for schemas without the optimizer (precedent: `extensions/debug.py` for
  the class-in-`extensions=` install form only; the hook contract is
  Decision 3's). `graph/` never imports `optimizer/` (Decision 2's
  relocation makes this buildable); **both installers** import the bracket
  by module path (`from ..graph.memo import operation_scope`), never
  through `graph/__init__` attribute access;
  `graph/__init__.py` ships the module docstring plus the memo re-exports
  only — Slice 3's predicate builders export lazily via PEP 562 (the root
  package's soft-export precedent), `graph/` takes its logger from the root
  package, and no root-package `graph` re-export is added. Absent-store
  contract, subscription posture, idempotent nesting, single-flight,
  cancellation, and exception semantics per Decision 3. Live tests under `examples/fakeshop/test_query/` for request
  isolation, one-compute-across-five-roots, viewer/alias keying, and the
  no-extension fallback; package tests under `tests/graph/test_memo.py`
  (with `tests/graph/__init__.py`) only for what a real query cannot reach —
  async single-flight with a yielding factory, both cancellation directions,
  the raising factory, raise-then-succeed, and the absent-store branch.
- [ ] **Slice 2 — `GraphPathPlan`, path/lookup splitter, `RowIdentityProof`.**
  `graph/paths.py`: frozen `GraphPathPlan` built over the existing
  `django_strawberry_framework/utils/relations.py` classifier (relation kind
  per hop, first multiplying hop, complete chain, terminal field, a
  validated-lookup slot), the **new** longest-resolvable-prefix path/lookup
  splitter (splits a fused `Q` leaf key like `patron__email__icontains` into
  model path + lookup, validating the remainder through the existing lookup
  validator — derives no relation kinds itself), a `GraphPathPlanSet`
  grouping object keyed on the classifier's complete relation chain **plus a
  terminal-is-relation flag** (a relation-terminal arm like `patron` and a
  scalar-terminal arm like `patron__name` share a `relation_chain` but must
  not share a correlated body; test-pinned — the key card 055's arm-grouping
  needs), exact owning-`DjangoTypeDefinition`
  identity with injected (not `graph/`-resolved) type references, and
  per-hop target-visibility metadata slots. `graph/proofs.py`: the
  `RowIdentityProof` lattice and composition rules
  ([Decision 9](#decision-9--rowidentityproof-ships-as-metadata-the-gate-is-the-sibling-cards)).
  Unit tests under `tests/graph/test_paths.py` including the
  characterization test that
  `optimizer/nested_fetch.py::unwindowable_child_queryset_reason` returns
  `None` for a multiplying to-many join (measured: 9 SQL rows for 3 child
  identities — the baseline the sibling card's gate closes).
- [ ] **Slice 3 — `PredicatePlan` compiler.** First, **relocate the
  row-preserving primitives to
  `django_strawberry_framework/utils/predicates.py`** (a pure ORM leaf
  importing only Django and the package exceptions), leaving
  `optimizer/predicates.py` as a re-export shim so `filters/sets.py` and
  every existing `optimizer/predicates.py::` symbol reference keep working
  (Decision 2; Slice 5 sweeps the references). Then `graph/predicates.py`:
  `any_of` / `all_of` / `not_` (zero-branch `any_of()` / `all_of()` raise
  [`ConfigurationError`][glossary-configurationerror] — an empty group is a
  fail-open ambiguity a permission API must refuse), `direct(Q)` —
  **to-one paths only**: every `direct` leaf is classified pre-compilation
  and a path whose `GraphPathPlan.first_many_index` is non-null is rejected
  with a typed [`ConfigurationError`][glossary-configurationerror] naming
  `related` / `same_related_row` as the recourse (a to-many hop inside an
  outer `Q` multiplies rows — the exact defect the API promises to prevent),
  `related(path, Q)` correlated branches,
  `same_related_row(path, conditions)` with **path-relative** conditions,
  compilation as a strictly sequential fold through
  `utils/predicates.py::correlated_inner_root` and
  `utils/predicates.py::attach_exists` (each attach consumes the
  previous call's returned queryset), one combined outer `.filter()` per
  compiled plan (a plan with no correlated branches skips attachment and
  applies its single combined `.filter()` directly), the
  `graph.apply(plan, queryset, owner=...)` input contract, no
  framework-introduced `DISTINCT`, `RowIdentityProof` output on
  every compiled shape
  ([Decision 4](#decision-4--predicateplan-compiles-through-the-shipped-row-preserving-primitives),
  [Decision 5](#decision-5--same_related_row-is-explicit-path-relative-and-flat-semantics-never-change)).
  Package tests under `tests/graph/test_predicates.py` covering the R4/R5/R9
  SQL-shape and raise-path assertions (N distinct reserved aliases for N
  correlated branches, inner-query alias sharing, `NOT EXISTS`, no
  compiler-added multiplying outer join or `DISTINCT`); the *result
  semantics* of R4/R5/R9 land live in Slice 4 — Slice 3 is not accepted with
  a package-only stand-in for live-reachable behavior.
- [ ] **Slice 4 — `EdgeScope` + `FieldDependencyPlan` + Meta surface + live
  activation.** `graph/edges.py`: frozen `EdgeScope` keyed on
  `(owner definition, relation field, target definition, context)` whose
  request-bound sync factory returns a **`PredicatePlan` (or a `Q`,
  normalized)** that the framework compiles onto the child queryset via
  `graph.apply` at `optimizer/walker.py::_build_child_queryset` — after
  target visibility, narrow-only **by construction** — keeping the
  accessor-keyed prefetch cache the generated resolver already reads (no
  reserved `to_attr` for plain relations; the cache carries a provenance
  marker so consumer-populated caches are never trusted on scoped edges;
  Decision 7). The same composed child queryset seeds the nested-connection
  window and every per-parent fallback path. Strictness resolver keys
  publish only after successful attachment. `graph/dependencies.py`: frozen
  `FieldDependencyPlan(columns=...)` plus the column-tuple shorthand
  normalizer — **only** the members card 054 consumes at `0.1.1`
  (Decision 8). Meta surface: `Meta.edge_scopes` added to
  `ALLOWED_META_KEYS` as a **net-new key** (not a `DEFERRED_META_KEYS`
  promotion; the provenance comment block in `types/base.py` gains its
  entry), validated two-stage at type creation per the
  [`Meta.relation_shapes`][glossary-metarelation_shapes] pattern
  (Decision 11). Live fakeshop activation: `Loan.confidential` column +
  migration in `examples/fakeshop/apps/library/models.py`, the
  `LoanType.get_queryset` visibility hook (a fixture shared with card 055,
  created here) **plus `Meta.primary = True` on `LoanType`** (the R9
  secondary type otherwise trips the finalizer's primary-ambiguity audit),
  the **rewrite** of the existing `BookType.get_queryset` (the shipped
  `circulation_status="repair"` exclusion and its hidden-row contract and
  live baselines must survive the `PredicatePlan` form), the
  `edge_scopes` declaration on `BookType.loans`, the R9 secondary Loan type
  + acceptance connection riding the existing `FAKESHOP_TEST_LOAN_CONNECTION`
  flag (coordinated with card 055's planned
  `DjangoConnectionField(LoanType)` so one card owns it), live HTTP tests
  under `examples/fakeshop/test_query/` covering R3 (edge-selection half,
  including the `filter:`-argument fallback case), R4/R5/R9 result
  semantics, and the one-vs-one-hundred-parents query-count equality;
  re-baseline plan-cacheability and query-count assertions in
  `test_query/test_library_api.py` / `test_query/test_optimizer_auto_api.py`
  and sweep every private schema-module tuple in the test tree for the new
  types.
- [ ] **Slice 5 — docs + card wrap.** Regenerate `docs/TREE.md` for the new
  `graph/` package and the kanban tracked-path constants (the pre-commit
  hook rolls back every commit when tracked files land without the
  regeneration); add glossary DB entries for `GraphPathPlan`,
  `PredicatePlan`, `EdgeScope`, `FieldDependencyPlan`, `RowIdentityProof`,
  and the operation dependency memo, then regenerate `docs/GLOSSARY.md`;
  update `examples/fakeshop/test_query/README.md` suite descriptions; record
  the card-054/055/057/063/067 amendment obligations on those cards in the
  kanban DB and regenerate the board; flip card 053. Leave README / GOAL /
  TODAY release prose, `CHANGELOG.md`, and the version quintet untouched —
  all owned by the card-054 joint cut.

## Problem statement

A consumer building a graph-shaped, multi-model dashboard — the audited
production case is a five-root schedule calendar; the general case is any
operation selecting several model-backed connections that share one request
scope and one permission audience — must today hand-build the machinery the
package should generate:

- operation-scoped audience caching (no framework memo exists; five root
  visibility hooks recompute a ~dozen-query audience five times);
- row-preserving graph permissions (a custom `get_queryset` hook with OR'd
  to-many `Q` branches multiplies root rows; the shipped row-preserving
  rewrite in `filters/sets.py::FilterSet._apply_flat_leaves` deliberately
  refuses unaudited consumer semantics, and no public predicate API exists);
- same-related-row authorization (Django's split-`.filter()` semantics let a
  root qualify through two different related rows; no explicit construct
  exists, and the hazard is a security defect, not a style issue);
- edge-scoped child visibility (root visibility answers "is the parent
  visible", nothing answers "which children may this viewer see through this
  edge"; `permissions.py::apply_cascade_permissions` is forward-FK/one-to-one
  by design);
- computed-field dependency plans beyond concrete columns (card 054's
  `Meta.depends_on` is column-only, so a participants/invitees-shaped
  computed field degenerates to per-parent lazy reads);
- row-identity awareness (the window gate
  `optimizer/nested_fetch.py::unwindowable_child_queryset_reason` cannot see
  a multiplying consumer join — measured live: gate passes a queryset
  emitting 9 SQL rows for 3 child identities, which would corrupt window
  counts and page flags).

Every non-Done Layer 3 card — [`FieldSet`][glossary-fieldset] (054), search
(055), [`AggregateSet`][glossary-aggregateset] (057) — needs the same path
classification, visibility composition, exact-owner identity, and
row-preserving compilation. Built independently they will diverge on owner
identity, async visibility, alias sharing, database pinning, and strictness.
The reproduction fixtures that pin each of those divergences are indexed in
the [Test plan](#test-plan); this spec is the contract for the framework half
of the first foundation card.

## Current state

All claims below verified against source at authoring time.

- **No operation memo.** No public execution-scoped dependency cache exists;
  the closest machinery is private and single-purpose
  (`optimizer/extension.py` `_cache_key_parts_cache`, a per-execution
  `ContextVar` installed with `.set({})` in `on_execute` and `.reset(token)`
  in its `finally` — a sync generator hook, so the install lands in the
  caller's context and reaches resolvers on both execution colors). The
  optimizer extension is **optional**: `_active_optimizer` defaults to
  `None`, and most package-test schemas build without it.
- **Context stashes are silently lossy.**
  `utils/context.py::stash_on_context` (shared with `resource_policy.py`;
  `optimizer/_context.py` only re-exports it) deliberately swallows write
  failures on frozen/`__slots__` contexts — an `info.context` stash is not a
  reliable store, which independently justifies the `ContextVar` design. Its
  own docstring states the condition that makes a lossy stash tolerable there
  — every consumer of a missed read falls back to a *bounded* default
  (`resource_policy.py::policy_from_info`) — and a memo has no such default:
  a missed read is a recomputation at best and a divergent second plan at
  worst, so the precedent argues for the `ContextVar`, not against it.
- **Subscriptions resolve fields after `on_execute` closes.** Strawberry's
  `Schema._subscribe` exits the `executing()` extension bracket before
  iterating results, so per-event resolution runs after any
  `on_execute`-installed state is reset; `consumers.py` ships that path.
- **Row-preserving primitives are shipped and proven.**
  `optimizer/predicates.py::correlated_inner_root` builds the inner queryset
  over the outer model's `_base_manager`, pins `queryset.db`, and correlates
  on `pk` via `OuterRef("pk")` — documented as the only correlation
  implementation, depth-1 by construction;
  `optimizer/predicates.py::attach_exists` attaches `Exists` under a
  reserved unselected alias and returns the `Q(alias=True)` branch. Reserved
  aliases are allocated against the *current* queryset's annotations, and a
  duplicate `.alias()` silently overwrites — which is why compilation must
  fold sequentially (Decision 4). `filters/sets.py::FilterSet._apply_flat_leaves`
  consumes the primitives for audited framework-generated to-many leaves;
  `filters/sets.py::FilterSet._apply_related_constraints` is the sibling
  parent-PK-subquery strategy (uncorrelated `pk__in`, a distinct proof
  member). The PostgreSQL proof is recorded in
  [`docs/row-preserving-predicates-part1-pg-explain.md`][row-preserving-pg].
- **Strict path classification is shipped, for pure model paths only.**
  `django_strawberry_framework/utils/relations.py` classifies every relation
  kind, records the first multiplying hop and the complete chain; lookup
  validation is a separate contract, and no fused path+lookup splitter
  exists anywhere (`classify_path(Book, "title__icontains")` raises).
- **Cascade is forward-only by design.**
  `permissions.py::apply_cascade_permissions` walks concrete `ForeignKey` /
  one-to-one edges (`_is_cascadable_edge` excludes reverse relations, M2M,
  generic relations); a visible parent exposes every child of a selected
  to-many edge unless the consumer hand-builds a scoped `Prefetch`.
- **The generated relation resolver reads the accessor-keyed prefetch
  cache.** `types/resolvers.py::_make_relation_resolver` probes
  `root._prefetched_objects_cache[accessor_name]` and falls back to
  `getattr(root, accessor_name).all()`; it never probes a `to_attr`, and
  `optimizer/walker.py::_apply_hint` rejects hinted `to_attr` prefetches on
  generated relations for exactly that reason. Any edge-scoping design must
  keep the accessor-keyed cache (Decision 7).
- **Request-bound visibility poisons plan cacheability.**
  `optimizer/walker.py::_plan_prefetch_relation` sets
  `plan.cacheable = False` whenever the target type has a custom
  `get_queryset`, because the built child queryset embeds request context;
  the flag propagates from child plans. An edge scope is structurally the
  same case and inherits the mechanism. The structural/bound split that
  removes the penalty is the sibling card's.
- **The window gate cannot see consumer fan-out.**
  `optimizer/nested_fetch.py::unwindowable_child_queryset_reason` rejects
  exactly sliced / `select_for_update` / combined / `distinct` / values
  querysets and inspects no join shape.
- **Explain state is last-wins.**
  `optimizer/extension.py::DjangoOptimizerExtension._publish_plan_to_context`
  stores `DST_OPTIMIZER_PLAN` last-wins by documented intent (correctness
  sentinels union separately); the operation plan map is the sibling card's.

## Goals

1. One shared, immutable graph-planning vocabulary — `GraphPathPlan`,
   `PredicatePlan`, `EdgeScope`, `FieldDependencyPlan`, `RowIdentityProof` —
   under one package boundary, consumed (not reimplemented) by FilterSet,
   search, FieldSet, AggregateSet, edge-scoped selection loading, the nested
   planner, and explain mode.
2. An execution-bound dependency memo with an explicit scope key, available
   with and without the optimizer extension, safe for sync and async
   resolvers, single-flight between async callers, exception-safe, and
   documented to cache only immutable values.
3. Public, row-preserving predicate composition for consumer graph
   permissions: correlated to-many branches, boolean operators, explicit
   same-related-row groups, exact-owner re-entry — with no
   framework-introduced `DISTINCT` and no compiler-added multiplying outer
   join.
4. Contextual, edge-specific child scoping for selected to-many relations,
   independent of root visibility, composed into the child queryset the
   optimizer already builds and consumed through the accessor-keyed prefetch
   cache, with strictness keys published only after attachment and no
   fail-open path (prefetched, fallback, or optimizer-off).
5. A structured field-dependency vocabulary that card 054 normalizes
   `Meta.depends_on` into — shipped in this card only to the extent card 054
   consumes it at `0.1.1`.
6. Query growth for every shipped shape bounded by selection, never by
   parent row count: `queries(1 parent) == queries(100 parents)`.

## Non-goals

- **Structural optimization templates, root-subtree cache keys, response-path
  rebasing, the operation plan map, and nested sidecar batching.** The second
  recommended foundation card owns them (see `Out of scope`). This card must
  not assume they exist and must not block on them.
- **Rewriting arbitrary consumer `Q` expressions.** The audited-semantics
  boundary shipped by the row-preserving predicates work stands: consumer
  subclasses, method filters, and unaudited semantics are refused, not
  rewritten. `PredicatePlan` is an explicit opt-in API, not an
  after-the-fact rewrite.
- **A general child-collection cascade.** `apply_cascade_permissions` keeps
  its forward-only contract; `EdgeScope` is additive.
- **Nested correlation.** All correlated bodies are depth-1 relative to the
  queryset passed to `graph.apply`; compiling a plan inside another subquery
  is out of scope for `0.1.1` (Decision 4).
- **A per-event subscription memo scope.** Subscriptions fall back to
  per-call compute in `0.1.1` (Decision 3); promoting to a per-event scope
  is deferred and must arrive with an explicit invalidation rule.
- **An operation transaction / snapshot policy.** Explicitly optional and
  non-gating (R11); untracked by this card.
- **The `IntervalOverlap` compound filter primitive.** A FilterSet-layer
  feature, independent of the substrate; belongs in [`BACKLOG.md`][backlog]
  if promoted.
- **All consumer-repository work.** The originating consumer application's
  permission-widening defect, its dependency-floor decision, and its
  calendar recreation are owned and tracked by that repository (R12).

## Borrowing posture

Neither `graphene-django` nor `strawberry-graphql-django` ships a comparable
substrate — both leave graph-shaped authorization to consumer querysets, and
both accept JOIN-plus-`DISTINCT` fan-out in that position. The borrowing here
is internal: the substrate extracts and generalizes machinery this package
already shipped and proved (the `utils/relations.py` classifier, the
`optimizer/predicates.py` primitives, the exact-owner and alias-sharing rules
pinned by the [search spec][spec-055]). Both upstream-shaped alternatives are
rejected here: consumer-queryset authorization by Decision 7, JOIN-plus-`DISTINCT`
fan-out by Decision 4.

## User-facing API

The plan objects are framework-internal. The consumer-visible additions are:

```python
from django_strawberry_framework import graph


# 1. Operation-scoped dependency memo (any resolver/hook with info access).
#    scope_key pre-bakes the viewer identity and database alias via
#    request_from_info; consumers extend the tuple with their own dimensions.
audience = graph.get_or_compute(
    info,
    key=(
        "schedule-audience",
        *graph.scope_key(info, queryset),
    ),
    factory=build_frozen_audience,
)


# 2. Row-preserving graph predicates, composed inside the existing
#    get_queryset visibility hook (no new hook is introduced). The plan is
#    request-bound: built per request, never cached, never a cache key.
class EventType(ModelType):
    class Meta:
        model = Event

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        audience = graph.get_or_compute(info, key=..., factory=...)
        plan = graph.any_of(
            graph.direct(Q(owner_id__in=audience.user_ids)),
            graph.related("individuals", Q(id__in=audience.user_ids)),
            graph.same_related_row(
                "schedules",
                (
                    # Path-relative: the compiler prefixes "schedules__".
                    Q(block_id__in=audience.block_ids),
                    Q(rotation_id__in=audience.rotation_ids),
                ),
            ),
        )
        return graph.apply(plan, queryset, owner=cls)


# 3. Edge-specific child scoping, Meta-declared. The factory is sync, runs
#    after target visibility, and returns a predicate the framework applies
#    to the already-narrowed child queryset — narrow-only by construction.
class BookType(ModelType):
    class Meta:
        model = Book
        edge_scopes = {
            "loans": visible_loans,  # (info, narrowed_queryset) -> PredicatePlan | Q
        }
```

`Meta.depends_on`'s structured form is declared through card 054's `FieldSet`
surface and normalizes into `FieldDependencyPlan`; this card ships the
`columns` plan member and the shorthand normalizer, nothing more
([Decision 8](#decision-8--fielddependencyplan-normalizes-metadepends_on)).

## Architectural decisions

### Decision 1 — one substrate card, created and sequenced before Layer 3 freezes

The root-cause fix for the divergences catalogued above is a shared substrate, not five
per-subsystem implementations. The card was created 2026-08-07 as
`TODO-BETA-053-0.1.1` — sequenced after `TODO-ALPHA-052-0.1.0` and before
`TODO-BETA-054-0.1.1`, shifting the former cards 053-068 up by one; this
spec's filename follows the card. Cards 054, 055, 057, 063, and 067 must be
amended to consume it. **The amendment obligations must land on those cards
at this card's creation, not at its Slice 5** — if card 055 starts first,
the private path-plan twin this substrate exists to prevent gets built
anyway. **Rejected:** letting each Layer 3
card ship private path/visibility/identity machinery (the divergence this
spec catalogues); deferring the substrate past the `1.0.0` API freeze
(incompatible public concepts become un-unifiable).

### Decision 2 — a dedicated `graph/` package boundary

The substrate lands at `django_strawberry_framework/graph/` (`memo.py`,
`paths.py`, `predicates.py`, `edges.py`, `dependencies.py`, `proofs.py`).
The layering is one-directional: `optimizer/`, `filters/`, and `types/`
import `graph/`; `graph/` imports neither `optimizer/` nor the type
registry. That rule is buildable only because Slice 3 **relocates the
row-preserving primitives to
`django_strawberry_framework/utils/predicates.py`** — a pure ORM leaf whose
only package import is the exceptions module — leaving
`optimizer/predicates.py` as a re-export shim so `filters/sets.py` and
every existing symbol reference keep working. Without the move,
`graph/ -> optimizer.predicates` executes
`optimizer/__init__ -> extension -> graph` (a hard import cycle, since
Slice 1 makes the extension a `graph/` consumer); and because
`import django_strawberry_framework` itself reaches `extension`,
`graph/__init__.py` exports the Slice 3 builders lazily via PEP 562 rather
than eagerly re-entering a partially initialized package. Type references
inside plan objects are **injected by the caller** (the finalizer, the
walker, the search builder) as opaque `DjangoTypeDefinition` handles —
`graph/` never resolves a model to a type itself. The card-055 amendment scope this boundary implies:
`GraphPathPlan` + `GraphPathPlanSet` (chain-keyed grouping) subsume 055's
path classification and arm grouping, while 055's `LOOKUP_PREFIXES` prefix
rejection and its permission-dispatch plan **stay 055-local** — they are
search policy, not substrate. **Rejected:** folding into `optimizer/` — the
optimizer is one *consumer* of the vocabulary, and card 051 is about to
freeze optimizer subsystem boundaries; a substrate both layers import must
sit below both. **Rejected:** folding into `utils/` — these are cohesive
plan objects with their own lifecycle, not helpers.

### Decision 3 — the memo is execution-scoped, immutable-values-only, owned by `graph/`

`graph.get_or_compute(info, key, factory)` reads a module-level `ContextVar`
container owned by `graph/memo.py` and installed through one public bracket,
`graph.memo.operation_scope()`. Two installers ship: the optimizer
extension's `on_execute` (a two-line delegation — no memo state or keying
logic lands in `optimizer/`) and `extensions/graph.py::GraphSubstrateExtension`
for schemas that do not use the optimizer. `GraphSubstrateExtension`
brackets `on_execute` as a **sync generator**, matching
`DjangoOptimizerExtension.on_execute` — the install must land in the
caller's context to reach resolvers on both execution colors, and an
`async def` hook or an `on_operation` bracket does not. The container is
installed `.set({})`-once in the caller's context and dict-mutated
thereafter — never `.set()` per entry, which would race across the
`sync_to_async` thread-sensitive bridge. Entering `operation_scope()`
allocates a dict and sets a `ContextVar` — no request access, no `info`
read, no I/O — so it cannot raise, and installers may enter it outside
their `try`. The memo is never instance state on an extension:
the documented singleton-factory install form shares one extension instance
across concurrent operations, and only a `ContextVar` isolates them.

Contract lines, each pinned and tested:

- **Absent store ⇒ degrade, never raise.** With no installed container
  (`schema.execute_sync` without an installing extension, a direct unit
  call), `get_or_compute` calls the factory every time and caches nothing —
  the `_build_cache_key` recompute-fallback idiom.
- **Install is idempotent.** `operation_scope()` is a no-op yield when a
  container is already installed in the current context — it never shadows
  an outer store, so both installers may appear in one `extensions=` list
  and the outer one owns the lifecycle. Package test: nested brackets share
  one store, and an entry written inside the inner bracket survives its
  exit.
- **Subscriptions are not memoized in `0.1.1`.** Per-event field resolution
  runs after `on_execute` closes, so subscription resolvers hit the
  absent-store path and recompute per call. A per-event scope is explicitly
  deferred (see Non-goals): a memo living for a multi-hour subscription
  would cache an audience across events — a stale-permission defect.
- **Single-flight applies only between async callers**, via an
  `asyncio.Future` created in the execution's loop. A **sync** caller (a
  resolver on the thread-sensitive executor) that finds a pending async
  entry **recomputes locally and does not publish** — blocking on the future
  from that thread would deadlock the loop that must resolve it. The
  documented cost is a bounded double-compute, never a block.
- **Cancellation is waiter-safe in both directions.** Waiters park on the
  shared computation through `asyncio.shield` (or a per-waiter future fed by
  a done-callback); a cancelled waiter never cancels the shared computation.
  If the *owner* is cancelled, the in-flight cell is **resolved with a
  retry outcome, not merely removed from the dict** — a waiter already
  parked on the old future is never awakened by dictionary removal alone.
  Every parked waiter wakes, and exactly one atomically re-elects itself
  owner and retries; the rest park on the new cell. The package test parks
  a waiter *demonstrably* before cancelling the owner — a
  cancel-then-call-again fixture cannot catch the stranded-waiter defect.
- **Exceptions propagate to every waiter.** A raising factory removes its
  in-flight entry, every parked waiter observes the exception (the same
  exception object; documented), and the next call with the same key re-runs
  the factory.
- **Keys are explicit and consumer-owned** (viewer, tenant, database alias —
  whatever scopes the value); the store never crosses requests, so a wrong
  key under-shares rather than leaks. `graph.scope_key(info, queryset)`
  pre-bakes the viewer identity (via
  [`request_from_info`][glossary-request_from_info] — the example's
  `info.context` shapes vary across Django HTTP, bare-`HttpRequest` test
  client, and Channels contexts, and `request_from_info` is the only
  supported resolver) and the database alias.
- **Immutable values only** — frozen dataclasses and primitive ID sets,
  never evaluated querysets or model instances (request-, transaction-,
  router-, and snapshot-sensitive).
- **`info` is a diagnostic and future-scope seam.** `get_or_compute` never
  reads or writes `info.context` as a store
  (`utils/context.py::stash_on_context` is silently lossy on frozen
  contexts); `info` feeds error messages and `scope_key`.

**Rejected:** a cross-request TTL cache — that is `BACKLOG.md`'s
`request_lifecycle_cancellation_and_reuse` escalation tier, which must share
this memo's keying discipline when promoted, not replace it. **Rejected:**
caching on `info.context` ad hoc per consumer — no lifecycle owner, no
single-flight, no exception safety, and a lossy store. **Rejected:** the
optimizer extension as sole installer — it is optional, and a substrate
feature must not depend on an opt-in extension.

### Decision 4 — `PredicatePlan` compiles through the shipped row-preserving primitives

Every correlated branch compiles via
`utils/predicates.py::correlated_inner_root` + `attach_exists` (relocated
from `optimizer/predicates.py` in Slice 3, which keeps a re-export shim —
Decision 2) — the primitives already proven on PostgreSQL
([`docs/row-preserving-predicates-part1-pg-explain.md`][row-preserving-pg]).
Predicate *meaning* stays with the caller; the compiler owns validated
relation planning and row-preserving attachment. Compilation mechanics, each
pinned because the primitives make the naive alternative silently wrong:

- **Sequential fold.** Reserved-alias allocation reads the *current*
  queryset's annotations, and a duplicate `.alias()` silently overwrites —
  compiling branches in parallel against the original queryset collapses
  aliases and **under-restricts** (a security failure). Each `attach_exists`
  consumes the queryset returned by the previous; tests assert N distinct
  reserved aliases for N correlated branches.
- **One outer `.filter()`.** `attach_exists` returns only `Q(alias=True)`;
  applying branches in separate `.filter()` calls degrades OR to AND. A
  compiled plan attaches all aliases, then applies exactly one combined
  `.filter()`; `graph.apply` returns immediately after that single
  application.
- **Depth-1 correlation only.** `OuterRef("pk")` is the only correlation
  implementation; per-hop visibility composes as an uncorrelated
  `Q(hop__in=<visible queryset>)` membership inside the correlated body (no
  added depth). Nested correlation is out of scope (see Non-goals).
- **Input contract, checked pre-fold.** `graph.apply` validates **before
  the first attachment**: `queryset.model` is the model of `owner`'s
  `DjangoTypeDefinition`; the queryset is unsliced; no combinator; a
  model-row iterable (`values()` querysets refused — `.alias()` on one does
  not error, it silently builds a nonsense predicate). Each failure raises
  a typed [`ConfigurationError`][glossary-configurationerror] naming the
  recourse — never a raw Django `TypeError` or an optimizer-internal
  `OptimizerError` from a consumer-facing builder. The checks deliberately
  duplicate the primitive's own guards rather than delegating: the
  primitive's guards raise `OptimizerError` and fire mid-fold, leaving a
  partially aliased queryset.
- **Structural/request split.** `GraphPathPlan` is structural: finalize-
  frozen, hashable, cacheable. `PredicatePlan` is **request-bound**: built
  per request from request-derived values, never cached, never a component
  of any plan-cache key. The existing `cacheable = False` custom-visibility
  penalty applies to plans built inside `get_queryset` hooks until the
  sibling card's structural/bound split lands.

The compiler never adds `DISTINCT` and never adds a multiplying outer join —
and it **enforces** that: `direct()` accepts to-one paths only (they
legitimately join outer; the [search spec][spec-055] keeps to-one arms
outer), and every `direct` leaf is classified pre-compilation with to-many
paths (`first_many_index` non-null) rejected via typed
[`ConfigurationError`][glossary-configurationerror] pointing at `related` /
`same_related_row` — without the check, `direct(Q(genres__name__icontains=...))`
lands the M2M join in the outer query with no `DISTINCT` and multiplies
rows. The tested invariant is "no *compiler-admitted* multiplying table in
the outer `alias_map`, no compiler-added `DISTINCT`" — not a blanket
property of the consumer's queryset. **Rejected:** introspecting and rewriting arbitrary consumer joins
(a fingerprint is not a trust boundary — the settled part-1 posture); a new
query language over the ORM (violates GOAL.md's no-abstraction-layer
constraint); routing through the FilterSet applicators
(django-filter-coupled and gated on the audited version range — precedent,
not the reuse target).

### Decision 5 — `same_related_row` is explicit, path-relative, and flat semantics never change

`graph.same_related_row(path, conditions)` compiles all conditions into one
correlated body sharing one related-row chain — the construct that makes the
exact `(block_id, rotation_id)`-style grant expressible and the
split-`.filter()` false positive impossible. **Conditions are relative to
`path`**: the compiler rewrites every `Q` leaf key to
`path + LOOKUP_SEP + key`, and rejects with a typed error any leaf already
prefixed with the path — absolute conditions would make `path` advisory and
let a stray condition on a different relation silently reintroduce the
two-alias leak the construct exists to prevent. Ordinary flat filters keep
Django semantics untouched; same-row grouping is opt-in for consumer
predicates and preserved by search where visibility and terminal condition
share a relation arm (the alias-sharing rule the [search spec][spec-055]
already pins). Tests assert both result behavior and **inner-query** alias
sharing (the outer query holds only the reserved alias) — a result-only
fixture can pass with two aliases accidentally landing on one child.
**Rejected:** silently upgrading chained `.filter()` calls to same-row
semantics (breaks documented Django behavior and every existing consumer);
absolute-path conditions (unenforceable contract).

### Decision 6 — exact-owner identity on root-model re-entry

When a relation path re-enters a model that has primary and secondary
GraphQL types ([`Meta.primary`][glossary-metaprimary]), the plan carries the
exact owning identity, never a registry primary lookup — a search over a
secondary Loan type applies the secondary visibility to the re-entered Loan
hop. The identity carrier is the **`DjangoTypeDefinition`** (matching the
[search spec][spec-055]'s rule — never a bare `(type_name, model)` pair);
a `DjangoType` class passed as `owner=` resolves through its definition
handle. Structural identities key on that definition, and two types over one
model never compare equal as owners.
[`apply_cascade_permissions`][glossary-apply_cascade_permissions] resolves
its edge targets through the registry primary lookup by documented design
and is **exempt**: a forward FK/one-to-one edge cannot re-enter a
secondary-typed root the way a to-many path can, so primary-lookup is sound
in cascade's position. **Rejected:** model-keyed identity (leaks
primary-type visibility into secondary-type roots — a security failure,
reproduction R9).

### Decision 7 — `EdgeScope` composes into the child queryset, not a broader cascade

An edge is `(owner definition, relation field, target definition, context)`
— two fields reaching the same target model may intentionally expose
different row sets. The primary composition point is
`optimizer/walker.py::_build_child_queryset`, which already builds the
target's default-manager queryset and routes it through target visibility:
the edge factory runs **after** target visibility, receives `info` and that
already-narrowed queryset (for inspection only), and returns a
**`PredicatePlan` (or a `Q`, normalized to one)** that the framework
compiles onto the narrowed queryset via `graph.apply` — narrow-only **by
construction**. A replacement-queryset callback cannot enforce narrowness:
a factory ignoring its input and returning `Loan.objects.all()` re-widens
what the target's `get_queryset` hid (privilege escalation), and no seal —
integrity, model, routing — can prove a returned queryset is a subset of
its input. Predicate composition removes the entire class: the framework
only ever *filters* the visibility-scoped queryset it already holds. Both plan-time consumers flow through that one builder — the
plain `Prefetch` (`walker.py::_build_prefetch_child_queryset`) and the
nested-connection window (`nested_planner.py`'s injected
`build_child_queryset` callable) — so composing there covers both. The
composed child queryset lands in the ordinary accessor-keyed `Prefetch` the
walker already emits — **no reserved `to_attr` for plain relations**: the
generated resolver reads `_prefetched_objects_cache[accessor_name]`, and
`optimizer/walker.py::_apply_hint` already rejects `to_attr` prefetches on
generated relations because rows landed there are invisibly bypassed by
per-row lazy loads. The `_dst_` reserved namespace (with the `$`
response-key escape) remains the nested-connection window's naming
discipline.

The **owner is threaded, never looked up**: `_build_child_queryset` carries
no owner today and `field.model` is refused as a substitute (a secondary
type over the same model would resolve to the primary — Decision 6). The
owner travels as `type_cls` (the `nested_planner` vocabulary) through
`_walk_selections` → `_dispatch_single_relation` → `_plan_prefetch_relation`
→ `_build_prefetch_child_queryset` → `_build_child_queryset`, and joins the
injected `build_child_queryset` callable signature.

No path may fail open:

- the **per-parent fallback pipeline** does *not* seed from
  `_build_child_queryset` — `connection.py::_build_relation_connection_resolver`
  seeds from the parent relation manager and re-applies target visibility
  itself — so the edge scope is applied a **second** time on that path,
  immediately after `connection.py`'s own `apply_type_visibility_sync`
  call, from the owner definition the resolver closes over;
- on the generated **list-relation resolver's cache-miss branch**
  (`types/resolvers.py::_make_relation_resolver`'s fall-through — reached
  with the optimizer off, under `OptimizerHint.SKIP`, after consumer-wins
  prefetch stripping, or via the `relation_shapes` list recourse), the
  resolver applies target visibility **and then** the edge scope — and both
  compose **before** the shipped raw-list row bound:
  `resource_policy.py::bounded_rows` bounds by *slicing* (a `QuerySet`
  carries the bound into SQL as a `LIMIT`, and Django refuses `.filter()`
  on a sliced queryset), so the branch hands the already-composed queryset
  to `bounded_rows`, keeping the bound a `LIMIT` over scoped rows and the
  bound's internal `resource_policy.py::check_deadline` at the last
  pre-database seam. The cache-hit branch is untouched by that ordering: a
  provenance-marked cache is already scoped, and `bounded_rows` keeps
  truncating those materialized rows in Python. The list
  resolver applies *no* visibility today, so composing the visibility
  helpers there is part of this slice, not a presupposition — and it is
  composed **color-matched**: when the target's `get_queryset` is async
  (`is_async_callable`, the same check Meta validation already uses), the
  finalizer generates an **async** list resolver awaiting
  `apply_type_visibility_async` before composing the (sync) edge-scope
  predicate; the sync case keeps `apply_type_visibility_sync`.
  `relation_shapes = "list"` is the *documented recourse* for
  async-visibility targets locked out of nested connections — a
  sync-only fallback resolver would raise `SyncMisuseError` on exactly the
  types sent there and delete the escape hatch;
- the **accessor-keyed prefetch cache is untrusted on a scoped edge.**
  The optimizer's consumer-wins reconciliation refuses a consumer
  `prefetch_related` over an edge-scoped accessor with a typed error at
  diff time, but that guard only exists when the optimizer runs — with the
  optimizer off or under `OptimizerHint.SKIP`, a consumer returning
  `Book.objects.prefetch_related("loans")` populates the cache with
  unscoped rows and the resolver's cache-hit branch would serve them
  silently (the N+1 guard treats a populated cache as satisfied). Scoped
  edges therefore require **provenance**: when the walker emits the scoped
  `Prefetch`, it records a marker for the accessor under the `_dst_`
  reserved namespace on each parent row; the generated resolver for an
  edge-scoped relation serves `_prefetched_objects_cache[accessor_name]`
  **only when the marker is present** and otherwise ignores the cache and
  falls through to the scoped query path (target visibility + edge scope).
  Ordinary (unscoped) relations keep today's cache probe untouched — no
  hot-path cost where no scope is declared. Live tests pin the
  optimizer-off and `SKIP` arms with consumer-prefetched hidden children
  (rejected alternative: documenting the unmarked cache as an accepted
  hole — a permission-shaped declaration must not have a
  consumer-triggerable bypass);
- a factory **raising at bind time** fails the operation per the existing
  visibility-hook error contract;
- a factory returning **anything but a `PredicatePlan` or `Q`** is refused
  loudly with a typed error inside `_build_child_queryset` immediately
  after the factory returns — in particular a returned *queryset* is
  refused by type, never adopted. Compiled application through
  `graph.apply` adds only reserved aliases and one `.filter()`, so the
  composed child queryset stays window-gate-compatible by construction;
  `nested_fetch.py::unwindowable_child_queryset_reason` is still asserted
  post-composition in tests as the *predicate*, never relied on as the
  enforcement point (its nested-connection caller degrades silently and
  the plain-prefetch path never calls it).

Factories are **sync-only in `0.1.1`** (an `async def` factory raises
[`SyncMisuseError`][glossary-syncmisuseerror], the shipped color-misuse
error — sync factories compose without change inside the async list
resolver arm); the `graph.apply` output passes the same
[sealed visibility boundary][glossary-sealed-execution-queryset] with the
same allow-sliced posture — and the same admitted-bound-value rule over
every predicate payload (see `Edge cases and constraints`) — as the
target-visibility helpers. Strictness
resolver keys publish only after successful attachment — planning failure
stays visible. [`apply_cascade_permissions`][glossary-apply_cascade_permissions]
keeps its forward-only contract. `BACKLOG.md`'s
`cascade_permission_prefetch_enforcement` and `soft_delete_cooperation` name
the same seam and must compose through `EdgeScope` when promoted, not beside
it. **Rejected:** the reserved-`to_attr` attachment for plain relations (the
shape the codebase rejects by name; making it work means rewriting the
generated resolver's cache probe and the N+1 guards on the hot path).
**Rejected:** auto-walking every collection edge through cascade (wrong
context, planning explosion, cycle hazards).

### Decision 8 — `FieldDependencyPlan` normalizes `Meta.depends_on`

This card ships `FieldDependencyPlan(columns=...)` and the column-tuple
shorthand normalizer — **only** what card 054 consumes at `0.1.1`. The card
054 amendment is precise: 054's `depends_on` lives on the **FieldSet's**
`Meta` (not a `DjangoType` Meta key — nothing "promotes"); its binder
returns `{field_name: FieldDependencyPlan}` instead of
`{field_name: tuple[str, ...]}`, and its `only_fields` merge reads
`plan.columns`. The amended surfaces are 054's dependency-normalization
Decision, its Slice 3 row, and its `depends_on` tests. The expanded
vocabulary — `select_related` paths, plain prefetch paths, annotations,
contextual prefetch factories, batch assemblers (which must consume
prefetched relations through `.all()`, never `.filter()` / `.exists()` /
`.count()` on a prefetched manager) — ships **with its first consumer**:
card 054's computed-relation slice or the sibling optimizer card, whichever
lands first. Shipping consumer-less vocabulary here would leave uncoverable
lines under the 100% gate and violate the no-reserved-surface rule.
`BACKLOG.md`'s `computed_field_optimizer_hints` / `computed_fields_binding`
hint dict normalizes into the same plan rather than freezing a second
dependency vocabulary. **Rejected:** static inference of resolver
dependencies (false confidence; explicit plans have an honest failure mode);
shipping the full vocabulary without a consumer (coverage-gate dead weight).

### Decision 9 — `RowIdentityProof` ships as metadata; the gate is the sibling card's

This card ships the proof vocabulary as a **lattice with an explicit meet**:
a composed shape's proof is the *weakest* contribution. Members and rules —
plain model base queryset `PROVEN_BASE`; `select_related` preserves;
framework correlated `EXISTS` `PROVEN_CORRELATED_EXISTS`; framework
parent-PK subquery `PROVEN_PARENT_PK_SUBQUERY` (uncorrelated `IN`, a
deliberately separate member); to-one joins `PROVEN_TO_ONE_JOIN` — with the
caveat that the walker downgrades `select_related` to `Prefetch` when the
target type has custom visibility, so the proof describes the shape actually
built, not the shape requested; an unexplained consumer to-many join and a
consumer `DISTINCT` both map to `UNPROVEN_CONSUMER_SHAPE` (`DISTINCT`
additionally stays unwindowable under the existing gate); a shape known to
multiply is `KNOWN_MULTIPLYING`. Proof derivation for framework-built paths
reads the classifier (`first_many_index is None` ⇒ single-valued). Every
`PredicatePlan`-compiled shape carries its proof. Refusing to window an
unproven shape — the strict-mode error, the non-strict fallback, the
never-inject-`DISTINCT` rule — lands with the nested-batching work in the
sibling card, which consumes this vocabulary. Proof is by construction, not
by reverse-engineering Django aliases; consumer querysets that bypass
framework shaping stay unproven unless a validated assertion contract is
added (an open question, see `Risks and open questions`). **Rejected:**
shipping the gate here without the sidecar-normalization machinery that
gives non-strict mode a correct fallback.

### Decision 10 — joint cut at `0.1.1`: release state defers to card 054

`TODO-BETA-054-0.1.1` shares the patch version and lands after this card, so
054 owns the `pyproject.toml` / `__init__.py` / `tests/base/test_init.py`
bump, `CHANGELOG.md`, and all release-state prose
([Joint version cut][glossary-joint-version-cut]). Card 054's existing
lone-card version-bump decision (its Decision 10) must be amended at card
creation: it keeps bump ownership, but as the joint cut's last lander rather
than as the lone `0.1.1` card. **Rejected:** this card owning the bump
(would ship a release whose headline feature, `FieldSet`, is absent).

### Decision 11 — public declaration surface

Pinned now: (a) graph predicates are **public builders consumed inside the
existing [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook]**
— queryset-in, queryset-out composition, no new hook, no decorator, hook
signature `(cls, queryset, info, **kwargs)` as the base class declares;
(b) edge scopes declare as **`Meta.edge_scopes`**, a mapping of relation
field name to sync factory, added to `ALLOWED_META_KEYS` as a **net-new
key** — not a `DEFERRED_META_KEYS` promotion; that set stays unchanged, and
the provenance comment block in `types/base.py` gains the entry.
Validation follows the shipped
[`Meta.relation_shapes`][glossary-metarelation_shapes] two-stage pattern at
**type creation**: dict shape and callable check in `_validate_meta`, then
unknown / excluded / non-relation / single-valued / consumer-authored field
names through the shared `_selected_meta_targets` helper in
`__init_subclass__` (value-agnostic — `set(edge_scopes)` maps in with no
signature change), raising
[`ConfigurationError`][glossary-configurationerror] with the standard
unknown-fields formatting. Stage 1 carries **no** Relay-Node gate (unlike
`relation_shapes` — edge scoping is orthogonal to Relay shape); the
async-factory rejection reuses the already-imported `is_async_callable`
check to raise [`SyncMisuseError`][glossary-syncmisuseerror];
`_ValidatedMeta` and the `DjangoTypeDefinition` each gain an `edge_scopes`
slot. Only target-type-dependent residue (checks that need settled relation
targets — the target model has a registered type, and the owner definition
recorded on the edge identity is the one the walker will resolve, Decision 6)
waits for [`finalize_django_types`][glossary-finalize_django_types]
phase 2.5, placed per the `cursor_field` precedent: it runs before phase 3
flips `finalized` and stays idempotent under the partial-finalize rerun.
(c) structured field dependencies declare through card 054's `FieldSet`
surface. Declaration-time structure validates at type creation or
finalization; request values bind only at execution and never enter any
cross-request structure. **Rejected:** a sidecar `EdgeScopeSet` class —
sidecar `Set` classes earn their weight when they carry many members with
inheritance (FilterSet, OrderSet); an edge-scope map is small and
per-relation, and a sidecar can be added compatibly later if it grows.
**Rejected:** an imperative registration API (the explicit anti-goal of
this package). **Rejected:** phase-2.5-only validation (later than the
shipped precedent's error timing for checks available at type creation).

## Implementation plan

| Slice | New / changed surface | Tests |
|---|---|---|
| 1 | `graph/__init__.py`, `graph/memo.py` (store owner); two-line delegation in `optimizer/extension.py::DjangoOptimizerExtension.on_execute`; new `extensions/graph.py::GraphSubstrateExtension` | live `examples/fakeshop/test_query/` (isolation, five-roots, keying, no-extension fallback); `tests/graph/test_memo.py` (single-flight, cancellation, raise paths, absent store) |
| 2 | `graph/paths.py` (plan, plan set, path/lookup splitter), `graph/proofs.py` over `utils/relations.py` | `tests/graph/test_paths.py` + window-gate characterization |
| 3 | `graph/predicates.py` over `optimizer/predicates.py` | `tests/graph/test_predicates.py` (SQL-shape: alias count, inner alias sharing, `NOT EXISTS`, no compiler `DISTINCT`; raise paths) |
| 4 | `graph/edges.py`, `graph/dependencies.py`; `Meta.edge_scopes` in `types/base.py` (+ `types/finalizer.py` residue, `types/definition.py` slot); owner threading + edge composition in `optimizer/walker.py::_build_child_queryset` and `optimizer/nested_planner.py` (injected-callable signature); second application in `connection.py::_build_relation_connection_resolver`; visibility + scope on the list-resolver cache-miss branch in `types/resolvers.py`; `examples/fakeshop/apps/library/models.py` (`Loan.confidential`) + migration file; library schema fixtures (LoanType hook + `primary = True`, BookType hook rewrite + `edge_scopes`, R9 secondary Loan type + connection under `FAKESHOP_TEST_LOAN_CONNECTION`) | `tests/graph/test_edges.py`, `tests/graph/test_dependencies.py`; live `examples/fakeshop/test_query/` (R3 incl. `filter:` fallback, R4/R5/R9 result semantics, 1-vs-100 parents); re-baselined `test_library_api.py` / `test_optimizer_auto_api.py`; schema-module tuple sweep |
| 5 | `docs/TREE.md` + tracked-path constants regenerate, glossary DB + regenerate, `test_query/README.md`, kanban card amendments + wrap | render-clean checks |

Slices are sequential; each later slice consumes the earlier's surface, so no
ownership partition applies.

## Helper-reuse obligations (DRY)

- Path classification: only `utils/relations.py` — `GraphPathPlan` wraps it,
  never re-derives relation kinds. The path/lookup splitter is the one
  **new** primitive (Slice 2): it probes `classify_path` for successively
  shorter prefixes and takes the **longest** that resolves — matching
  Django's own field-before-lookup resolution order, so a model field named
  `date` or `year` wins over the transform of the same name (test-pinned) —
  validating the remainder through
  `utils/relations.py::validate_lookup_expr`. Results memoize in
  `graph/paths.py` on the hashable `(model, key)` pair; the public
  `classify_path` stays uncached by contract. The splitter derives no
  relation kinds, and it lands in the substrate precisely so no consumer
  builds a private twin.
- Correlated compilation: only `utils/predicates.py::correlated_inner_root`
  / `attach_exists` (relocated in Slice 3; `optimizer/predicates.py` stays
  as the re-export shim) — no second `EXISTS` builder. The FilterSet
  applicators (`_apply_flat_leaves`, `_apply_related_constraints`) are
  precedent, not the reuse target.
- Request resolution: only
  [`request_from_info`][glossary-request_from_info] — `graph.scope_key` and
  every documented example route through it; no direct `info.context.request`
  access.
- Visibility binding: the shared sync/async visibility helpers that
  normalize `get_queryset` hooks today are the only binding path for target
  visibility; the edge factory composes *after* them at
  `_build_child_queryset` rather than through a parallel variant.
- Reserved naming: the `_dst_` namespace (with the `$` response-key escape)
  stays the only reserved-attribute discipline; no second naming scheme.
- The search spec's path-plan builder migrates onto
  `GraphPathPlan` / `GraphPathPlanSet` in card 055's amended form rather
  than keeping a private twin; this card must not copy any of its logic
  forward.

## Edge cases and constraints

- **Async siblings and the memo:** a factory that yields before returning
  runs exactly once for one key across async callers; every waiter receives
  the same immutable object. A sync caller finding a pending async entry
  recomputes locally without publishing (Decision 3) — documented, bounded
  double-compute.
- **Memo keys must include the database alias** wherever the value derives
  from data ([Multi-database cooperation][glossary-multi-database-cooperation]);
  `graph.scope_key` pre-bakes it, and the R2 tests pin it.
- **Rolled-back authorization state must not publish.** A factory running
  inside `utils/write_transaction.py::authorization_phase` (or any
  force-rolled-back transaction) computes against state that will not
  survive the phase; the memo is inert while such a phase is open — values
  computed there are returned to the caller but never stored.
- **`same_related_row` negation** keeps quantifier semantics explicit:
  `not_(same_related_row(...))` is "no single related row satisfies all
  conditions" — a root with **zero** related rows satisfies it.
- **`not_` over correlated branches** compiles as `~Q(alias=True)` on the
  reserved alias (a two-valued `EXISTS` annotation — no NULL hazard, and
  `NOT EXISTS` short-circuits); negation is never applied to the relation
  path itself (a path `exclude` triggers `split_exclude` and different
  semantics), and the alias is attached even in a negated context.
- **`not_` over `direct` inherits Django three-valued semantics:** rows with
  `NULL` in the tested column satisfy neither `Q(field=x)` nor its negation
  — `any_of(direct(q), not_(direct(q)))` is not "all rows". Documented, not
  papered over.
- **Exact-owner identity** must survive plan freezing and hashing — two
  definitions over one model never compare equal as owners (Decision 6's
  `DjangoTypeDefinition` carrier).
- **Edge scopes and empty results:** a predicate matching no rows is valid
  (viewer sees no children), keeps the composed queryset window-gate-clean,
  and must not un-plan the edge or drop the parent.
- **Edge-scope failure is loud on every path:** factory raising at bind
  time fails the operation; a non-predicate return (including a queryset)
  is refused with a typed error at bind time; the optimizer-off,
  `OptimizerHint.SKIP`, and per-parent-fallback paths apply the scope
  rather than silently skipping it, and an unmarked prefetch cache on a
  scoped accessor is ignored, never served (Decision 7).
- **Predicate bound values pass the seal's admitted-bound-value rule.**
  Every `graph.apply` output crossing the sealed boundary is canonically
  reconstructed, and each bound `Q` value reaches
  `utils/querysets.py::_normalized_bound_value`: plain data and its
  subclasses (`TextChoices` members, `Decimal` / `UUID` / date subclasses)
  normalize to framework-owned exact inert values; trusted schema is
  retained by reference — including a bound `models.Model` instance, so
  `Q(borrower=request.user)` survives; every other payload is refused
  closed as a typed `untrusted` defect. A consumer object, dataclass, or
  namedtuple bound as a `direct` / `related` / `same_related_row` /
  edge-factory predicate value is therefore a documented refusal, not a
  supported payload — bind its scalar fields instead.
- **Consumer duplicates are preserved:** predicate application never
  collapses a consumer's intentional multiset (no injected `DISTINCT`) and
  never multiplies it (correlated attachment only).
- **ASCII-only applies to `.py` sources** in the new package; module
  docstrings are mandatory (TREE.md render fails without them).

## Test plan

The twelve reproductions this spec is organized around are indexed here so
every `R<n>` reference in this document resolves against this document. R2–R6
and R9 are this card's acceptance surface; R1, R7, R8, and R10 belong to the
sibling card (R8's *characterization baseline* lands here with Slice 2); R11
is optional and non-gating; R12 is consumer-repository work.

| # | Reproduction | Core assertion | Owner |
| --- | --- | --- | --- |
| R1 | Five-root structural cache isolation | Each root produces one explain entry; a selection or argument change invalidates only its own subtree; aliasing a root needs no new structural template; a repeat request hits every template | sibling |
| R2 | Operation dependency isolation | One compute per operation with request-local hits; a second request recomputes; viewer, tenant, and DB alias never share; a failing or cancelled factory leaves no poisoned entry; sync and async agree | this card |
| R3 | Root visibility versus edge visibility | A visible root leaves a hidden child unselectable, unable to qualify search, and unable to contribute to a count; staff policy sees both; parent count does not change query count | this card |
| R4 | Same-related-row authorization | Sequential filters false-positive across two different rows; one same-row predicate does not qualify the root; the relation alias is shared inside one correlated body; negation keeps its quantifier | this card |
| R5 | Custom predicate cardinality | A raw `Q` over a to-many path fans out, and `.distinct()` masks it while retaining outer joins; the predicate plan returns one row, puts no child table in the root alias map, and adds no `DISTINCT` | this card |
| R6 | Computed dependency batching | A computed field over related rows runs no per-parent, per-child, or deferred-column query; count is constant across parent counts; omitting the field omits its queries | this card |
| R7 | Ordered nested connection batching | Parent count does not change child query count; per-parent windows and `totalCount`; cursors replay; argument-divergent aliases batch separately; strictness reports no planned edge | sibling |
| R8 | Row-identity window gate | The classifier misses a multiplying join (the baseline); strict targets raise a targeted unproven-row-identity error and non-strict fall back; no automatic `DISTINCT`; correlated `EXISTS` restores a proven window plan | sibling (baseline here, Slice 2) |
| R9 | Exact-owner root-model re-entry | A connection over a secondary type applies *that* type's visibility to the re-entered hop; registry primary lookup is not substituted; structural identities differ by exact owner type | this card |
| R10 | Operation explain completeness | Every root appears regardless of completion order; no response carries only the last plan; shared dependencies appear once; fallback reasons attach to the right response key; scope values are redacted | sibling |
| R11 | Repeatable-read snapshot | PostgreSQL-only optional policy: opt-in keeps multiple roots coherent inside a read-only transaction that closes on success, GraphQL error, cancellation, and resolver exception | optional, non-gating |
| R12 | Consumer permission value gate | The originating consumer repository's own permission matrix must be proven before operation memoization — a fast shared wrong answer is worse than a repeated wrong one | consumer repository |

Per the live-first mandate, everything reachable from a real GraphQL
query is covered live under `examples/fakeshop/test_query/`; package tests
under `tests/graph/` keep only pure plan construction, SQL-shape assertions,
raise paths, and interleavings a real query cannot produce.

- **R2 — memo (live + package, Slice 1):** live — one compute per operation
  across five counter-backed root hooks; second request recomputes;
  different user / database alias never shares; the no-extension schema
  degrades to per-call compute; a subscription resolver recomputes per
  event. Package — async single-flight under a yielding factory; sync
  caller bypasses a pending async entry without publishing; cancelled
  waiter leaves the shared computation running; cancelled owner wakes an
  *already-parked* waiter, which re-elects and retries;
  raising factory propagates to all waiters then re-runs on the next call;
  absent-store branch.
- **R3 (edge-selection half) — root vs edge visibility (live, Slice 4):**
  visible Book with one visible and one `confidential` Loan — Book stays
  visible, the hidden Loan is absent from the selected edge **including**
  when a `filter:` argument forces the per-parent fallback, staff policy
  sees both; also pinned: the optimizer-off and `OptimizerHint.SKIP` arms
  with a consumer `prefetch_related` of hidden children (the unmarked
  cache is ignored — Decision 7). Query count identical for 1 and 100
  Books **on the windowed (unfiltered) path** (exact per-backend integers
  pinned from a measured baseline — the query-count matrix is asserted as
  equalities, never inequalities); the `filter:` fallback arm is
  *correctness-gated only* here — the current resolver executes filtered
  connections per parent by design, and parent-count-independent filtered
  batching is the sibling sidecar card's acceptance surface (recorded in
  its Slice 5 amendment obligations), so its per-parent counts are
  characterized, not required equal. The other R3 arms — hidden children
  not qualifying search, not contributing to counts/aggregates — are
  deferred to cards 055/057 and recorded in their Slice 5 amendment
  obligations.
- **R4 — same-related-row (package SQL-shape, Slice 3; live result
  semantics, Slice 4):** the split-`.filter()` false positive demonstrated
  as baseline; the same-row plan does not qualify the root; the **inner**
  query shares one relation alias inside one correlated body; pre-prefixed
  condition leaves rejected; negation semantics (including the
  zero-related-rows case) pinned.
- **R5 — predicate cardinality (package SQL-shape, Slice 3; live result
  semantics, Slice 4):** baseline custom `Q` fan-out demonstrated; the
  compiled plan returns one row per root; N correlated branches produce N
  distinct reserved aliases; the compiler adds no multiplying outer table
  and no `DISTINCT`; `direct` over a to-many path (e.g.
  `Q(genres__name__icontains=...)`) rejected with the typed error; on a
  plain-root fixture, a direct `COUNT(*)` over the row-preserving root.
- **R6 (package half) — dependency normalization
  (`tests/graph/test_dependencies.py`, Slice 4):** column-tuple shorthand
  normalizes to `FieldDependencyPlan(columns=...)`; live activation of a
  computed `borrowers`-shaped field is card 054's, after it consumes the
  plan.
- **R9 — exact owner (package identity, Slice 3; live, Slice 4):** primary
  and secondary Loan types with different visibility; the secondary root's
  re-entered Loan hop applies secondary visibility; plan identities differ
  by owner definition.
- **Window-gate characterization (Slice 2):** pin the measured baseline —
  `unwindowable_child_queryset_reason` returns `None` for
  `Issue.objects.filter(periodical__issues__embargoed=False)` while the shape
  emits 9 SQL rows for 3 issues — as the documented input to the sibling
  card's gate.
- 100% package coverage holds; adding `LoanType.get_queryset` flips
  `cacheable` for every loans prefetch, so existing plan-cacheability and
  query-count baselines in `test_query/test_library_api.py` /
  `test_query/test_optimizer_auto_api.py` are re-pinned in the same slice.

## Doc updates

Slice 5 owns: `docs/TREE.md` regenerate (new `graph/` package + new
`extensions/graph.py`), the kanban tracked-path constants regenerate (the
pre-commit hook otherwise rolls back commits that add tracked files),
`docs/GLOSSARY.md` via glossary DB entries for the five plan objects and the
memo, `examples/fakeshop/test_query/README.md`, and the kanban card
amendments (054, 055, 057, 063, 067 gain explicit consume-the-substrate
scope lines; 055/057 additionally record the deferred R3 arms) with board
regeneration. `README.md`, `GOAL.md`, `TODAY.md`, `CHANGELOG.md`, and the
version quintet stay untouched (Decision 10).

## Risks and open questions

- **The consumer-card amendments are not yet recorded.** The card was
  created 2026-08-07 as `TODO-BETA-053-0.1.1` (the spec's preferred number
  and sequencing; the former cards 053-068 shifted up by one), but the
  054/055/057/063/067 consume-the-substrate amendments are maintainer
  actions still to land — and per Decision 1 they must land now, at card
  creation, not at this card's Slice 5.
- **Consumer row-identity assertion.** Should a consumer be able to assert a
  validated row-identity contract for a custom queryset (unlocking windows
  over shapes the framework didn't build)? Preferred for `0.1.1`: no —
  unproven stays unproven; fallback: a validated assertion API in the
  sibling card if real consumers hit the wall.
- **Sync-caller double-compute.** Decision 3's recompute-without-publishing
  rule for sync callers racing an async in-flight entry trades a bounded
  duplicate factory run for deadlock freedom. If profiling shows hot
  factories hitting it, the fallback is a lock-free published-result
  fast-path (sync caller adopts an already-*completed* async result), which
  is compatible and additive.
- **Memo key ergonomics.** A consumer omitting the database alias or viewer
  from a key under-shares safely but can still cache a *wrong-scope* value
  for its own request. `graph.scope_key` is the mitigation and is used in
  every documented example; keys stay consumer-owned.
- **`Meta.edge_scopes` growth.** If per-edge policy accretes members
  (cache-scope keys, per-edge strictness), the mapping outgrows a dict. The
  sidecar-class fallback in Decision 11 is the escape hatch; adding it later
  is compatible.
- **Pre-existing list-relation visibility gap.** The generated list
  resolver applies no target visibility on its cache-miss branch today; the
  gap is inert only because no fakeshop list-relation target declares a
  hook. Adding `LoanType.get_queryset` without the Decision 7 resolver work
  would ship a live leak on `Book.loans` (pinned list-only by an existing
  test), so the resolver visibility composition is on Slice 4's critical
  path, not optional hardening.
- **Fixture collision with card 055.** Card 055's spec plans
  `LoanType.Meta.search_fields` and a `DjangoConnectionField(LoanType)`
  acceptance surface over the same library schema this card extends; 055
  already assumes a `LoanType` visibility hook exists, which this card
  creates. One card must own each shared fixture — this spec claims the
  visibility hook and the R9 secondary-type surface, and the card-055
  amendment records the dependency.
- **Open product decisions in the originating consumer application**
  (unauthorized target-user
  contract, public-access uniformity, per-edge user exposure) are consumer
  contracts; nothing in this card depends on their resolution, and the
  fakeshop fixtures deliberately use library-domain policies instead.

## Out of scope (explicitly tracked elsewhere)

- **Structural optimization templates + nested sidecar batching + operation
  plan map + row-identity gate enforcement** — the second foundation card
  (`TODO-BETA-063-0.1.6`, seated immediately ahead of the explain card;
  [spec][spec-063]); owns
  reproductions R1, R7, R8, and R10.
- **`FieldSet` itself** — card 054 ([spec][spec-054]), amended to consume
  `FieldDependencyPlan(columns=...)`; the expanded dependency vocabulary
  ships with its first consumer (Decision 8).
- **Search** — card 055 ([spec][spec-055]), amended to consume
  `GraphPathPlan` / `GraphPathPlanSet` / `PredicatePlan`;
  `LOOKUP_PREFIXES` rejection and the permission-dispatch plan stay
  055-local (Decision 2).
- **Aggregation child scoping** — card 057, amended to consume `EdgeScope`.
- **Optimizer explain over an operation plan map** — card 064.
- **Adversarial graph suite** — card 068.
- **Per-event subscription memo scope** — deferred with an explicit
  invalidation-rule requirement (Decision 3).
- **Optional PostgreSQL repeatable-read snapshot policy** — R11;
  non-gating, unscheduled.
- **`IntervalOverlap`** — FilterSet-layer primitive; BACKLOG candidate.
- **All originating-consumer work** — the permission-widening defect and
  its R12 matrix, the dependency-floor decision, and the calendar
  recreation; owned and tracked by that repository.

## Definition of done

- [ ] `graph/` package ships with the plan objects and the memo, all frozen
  dataclasses, no request value storable in any structural object;
  `graph/` imports neither `optimizer/` nor the type registry.
- [ ] `get_or_compute` proven live and in package tests: sync, async
  single-flight, sync-bypass, both cancellation directions,
  exception-propagation-then-retry, absent-store degradation, subscription
  recompute, request isolation, alias/viewer keying (R2 matrix green);
  works with and without the optimizer extension.
- [ ] `PredicatePlan` compiles as a sequential fold with one combined outer
  `.filter()`, N distinct reserved aliases for N branches, typed input
  errors, `direct` over a to-many path rejected, and SQL-shape assertions
  green (R4, R5, R9); path-relative `same_related_row` with
  pre-prefixed-leaf rejection.
- [ ] `Meta.edge_scopes` validates two-stage at type creation (net-new
  ALLOWED key), factories return predicates compiled narrow-only via
  `graph.apply` after target visibility at `_build_child_queryset` with the
  owner threaded as `type_cls`, covers the provenance-marked prefetched,
  per-parent-fallback (second application in `connection.py`), and
  color-matched list-resolver cache-miss paths (composed ahead of the
  raw-list row-bound slice), refuses non-predicate
  factory returns and consumer prefetches over scoped accessors loudly
  (unmarked caches ignored optimizer-off/`SKIP`), publishes strictness
  keys only after attachment, and the live R3 edge-selection fixture holds
  with parent-count-independent query counts on the windowed path.
- [ ] `FieldDependencyPlan(columns=...)` + shorthand normalizer shipped;
  no consumer-less vocabulary members.
- [ ] `RowIdentityProof` lattice shipped with the weakest-meet rule;
  window-gate baseline characterized.
- [ ] `Loan.confidential` + migration landed; `LoanType.Meta.primary` set;
  the `BookType` hook rewrite preserves the repair-exclusion contract;
  existing library baselines re-pinned; schema-module tuples swept;
  `optimizer/predicates.py::` symbol references swept after the Slice 3
  relocation.
- [ ] 100% package coverage; live-first placement respected; ruff +
  trailing-comma + pre-commit clean; tracked-path constants regenerated.
- [ ] TREE/GLOSSARY/test_query README updated; card amendments recorded;
  card 053 flipped; version quintet and CHANGELOG untouched (Decision 10).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[backlog]: ../../BACKLOG.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-aggregateset]: ../GLOSSARY.md#aggregateset
[glossary-apply_cascade_permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-fieldset]: ../GLOSSARY.md#fieldset
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize_django_types]: ../GLOSSARY.md#finalize_django_types
[glossary-get_child_queryset]: ../GLOSSARY.md#get_child_queryset
[glossary-get_queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-metafields_class]: ../GLOSSARY.md#metafields_class
[glossary-metafilterset_class]: ../GLOSSARY.md#metafilterset_class
[glossary-metaorderset_class]: ../GLOSSARY.md#metaorderset_class
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-metarelation_shapes]: ../GLOSSARY.md#metarelation_shapes
[glossary-metasearch_fields]: ../GLOSSARY.md#metasearch_fields
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-relatedaggregate]: ../GLOSSARY.md#relatedaggregate
[glossary-relatedfilter]: ../GLOSSARY.md#relatedfilter
[glossary-request_from_info]: ../GLOSSARY.md#request_from_info
[glossary-sealed-execution-queryset]: ../GLOSSARY.md#sealed-execution-queryset
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror
[glossary-visibility-boundary]: ../GLOSSARY.md#visibility-boundary
[row-preserving-pg]: ../row-preserving-predicates-part1-pg-explain.md

<!-- docs/SPECS/ -->
[spec-054]: spec-054-fieldset-0_1_1.md
[spec-055]: spec-055-search_fields-0_1_2.md
[spec-063]: spec-063-structural_templates-0_1_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
