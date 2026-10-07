# Spec: graph substrate — shared graph policy and dependency planning

Planned for `0.1.1` (card `TODO-BETA-058-0.1.1`, the first Beta card on
[`KANBAN.md`][kanban], sequenced ahead of `TODO-BETA-059-0.1.1`,
see [Decision 1](#decision-1--one-substrate-card-created-and-sequenced-before-layer-3-freezes)).
`TODO-BETA-059-0.1.1` shares this patch version and lands after this card, so
the `0.1.1` version bump belongs to the joint cut and this spec defers every
release-state artifact to card 059
([Decision 10](#decision-10--joint-cut-at-011-release-state-defers-to-card-059)).

This is the first of two foundation cards — the framework-internal
graph-planning vocabulary (`GraphPathPlan`, `PredicatePlan`, `EdgeScope`,
`FieldDependencyPlan`, `RowIdentityProof`) plus the operation-scoped
dependency memo, extracted into one shared package boundary **before**
[`FieldSet`][glossary-fieldset] (card 059), search (card 060), and
[`AggregateSet`][glossary-aggregateset] (card 062) freeze three private
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

Status: **PLANNED — no slice built yet; the consumer-card amendments are
recorded on cards 059 / 060 / 062 / 069 / 072.**
Five slices: Slice 1 (**`graph/` package + operation dependency memo**),
Slice 2 (**`GraphPathPlan` + path/lookup splitter + `RowIdentityProof`
vocabulary**), Slice 3 (**`PredicatePlan` compiler** — one-`.filter()`
boolean composition, target-side correlated branches, same-related-row
groups, exact-owner re-entry), Slice 4 (**`EdgeScope` + `FieldDependencyPlan` + Meta
surface + live fakeshop activation**), Slice 5 (**docs + glossary entries +
tracked-path constants + card wrap**).

Permission caveat: [`AGENTS.md`][agents] prohibits `CHANGELOG.md` edits
without explicit permission. This spec grants none — the `0.1.1` entry, the
version triplet, and all release-state prose are owned by the card-059 joint
cut ([Decision 10](#decision-10--joint-cut-at-011-release-state-defers-to-card-059)).

---

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [`FieldSet`][glossary-fieldset] — planned for `0.1.1` (card 059); consumes
  `FieldDependencyPlan` per this spec's amendment obligation
  ([Decision 8](#decision-8--fielddependencyplan-normalizes-metadepends_on)).
- [`Meta.search_fields`][glossary-metasearch_fields] — planned for `0.1.2`
  (card 060); its path planning moves onto `GraphPathPlan` per the amendment
  scope [Decision 2](#decision-2--a-dedicated-graph-package-boundary) pins.
- [`AggregateSet`][glossary-aggregateset] / [`RelatedAggregate`][glossary-relatedaggregate]
  / [`get_child_queryset`][glossary-get_child_queryset] — planned for `0.1.3`
  (card 062); consume `EdgeScope` instead of a private child-visibility hook.
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
  (install once in the caller's context and close in `finally`, mutate the
  dict — never `.set()` per entry, per the optimizer's own per-execution
  frame, `optimizer/_context.py::begin_execution_frame`, which sits behind a
  `utils/operation_lease.py::OperationLease` so a copied context observes
  the close; the close is ordered so the graph store outlives the
  optimizer's own frame — a consumer `get_queryset` hook reached through
  `resolve` reads the memo, and no optimizer memo reads the graph store)
  **and** a new shipped
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
  not share a correlated body; test-pinned — the key card 060's arm-grouping
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
  `django_strawberry_framework/utils/predicates.py`** — the whole of
  `optimizer/predicates.py` moves: both `EXISTS` builders (the outer-side
  `correlated_inner_root` + `attach_exists` with their reserved-alias
  allocator, and the target-side `related_rows_exist` with its link
  correlation) and the `OrderSet` value helpers (`visible_row_exists`,
  `visible_value`, `visible_value_path`); nothing stays behind. The new
  module is an ORM leaf importing only Django, the package exceptions, and
  its `utils/` siblings `utils/relations.py` (link columns) and
  `utils/querysets.py` (`VisibleRowExists`), neither of which imports
  `optimizer/`, `filters/`, or `graph/` at module level.
  `optimizer/predicates.py` stays as a re-export shim of every public name
  so `filters/sets.py`, `orders/sets.py`, `connection.py`, and every
  existing `optimizer/predicates.py::` symbol reference keep working
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
  every correlated branch compiled target-side through
  `utils/predicates.py::related_rows_exist` — its conditions filter the
  deepest hop's visible rows and the test folds outward one nested
  `EXISTS` per link, through each earlier hop's visible rows (`via=`) —
  the whole boolean tree compiled into one `Q` applied by one outer
  `.filter()` (no annotation, no reserved alias), the
  `graph.apply(plan, queryset, info, owner=...)` input contract and its
  color twin `graph.apply_async` (each hop's type resolved by
  `utils/querysets.py::relation_target_type` with `root=` the owner, each
  scoped hop's hook run through
  `utils/querysets.py::apply_type_visibility_sync` /
  `utils/querysets.py::apply_type_visibility_async` with that `info`, once
  per `(hop type, alias)` per compile; the sync form meets an async-only
  hop hook with [`SyncMisuseError`][glossary-syncmisuseerror]), the
  compiler-owned re-entrancy set in `graph/predicates.py` refusing a hop
  whose hook the compiler is already running
  ([Decision 6](#decision-6--exact-owner-identity-on-root-model-re-entry)),
  no framework-introduced `DISTINCT`, `RowIdentityProof` output on
  every compiled shape
  ([Decision 4](#decision-4--predicateplan-compiles-through-the-shipped-row-preserving-primitives),
  [Decision 5](#decision-5--same_related_row-is-explicit-path-relative-and-flat-semantics-never-change)).
  Package tests under `tests/graph/test_predicates.py` covering the R4/R5/R9
  SQL-shape and raise-path assertions (N correlated branches compile to N
  `EXISTS` terms in the one outer `WHERE` with `query.annotations`
  untouched, one nested `EXISTS` per link of a branch path, a scoped hop's
  hook restriction inside that hop's body and an unscoped hop read through
  `_base_manager`, same-row conditions on the deepest body's one base
  table, `NOT EXISTS`, no compiler-added multiplying outer join or
  `DISTINCT`), the hop hooks receiving the `info` passed in, a plan
  re-entering its owner's model inside the owner's own hook refused on
  both colors with a path-rich message, the sync `graph.apply` raising
  `SyncMisuseError` for an async-only hop type, and `graph.apply_async`
  compiling the same plan; the *result semantics* of R4/R5/R9 land live in Slice 4 —
  Slice 3 is not accepted with a package-only stand-in for live-reachable
  behavior.
- [ ] **Slice 4 — `EdgeScope` + `FieldDependencyPlan` + Meta surface + live
  activation.** `graph/edges.py`: frozen `EdgeScope` keyed on
  `(owner definition, relation field, target definition, context)` whose
  request-bound sync factory returns a **`PredicatePlan` (or a `Q`,
  normalized)** that the framework compiles onto the child queryset via
  `graph.apply` at `optimizer/walker.py::_build_child_queryset`, with the
  walker's `info` (`None` passes through as it does to target
  visibility) — after
  target visibility, narrow-only **by construction** — keeping the
  accessor-keyed prefetch cache the generated resolver already reads (no
  reserved `to_attr` for plain relations; the resolver trusts that cache
  only for a relation the optimizer planned, so consumer-populated caches
  are never trusted on scoped edges; Decision 7). The same composed child queryset seeds the nested-connection
  window and every per-parent fallback path. Strictness resolver keys
  publish only after successful attachment. `graph/dependencies.py`: frozen
  `FieldDependencyPlan(columns=...)` plus the column-tuple shorthand
  normalizer — **only** the members card 059 consumes at `0.1.1`
  (Decision 8). Meta surface: `Meta.edge_scopes` added to
  `ALLOWED_META_KEYS` as a **net-new key** (not a `DEFERRED_META_KEYS`
  promotion; the provenance comment block in `types/base.py` gains its
  entry), validated two-stage at type creation per the
  [`Meta.relation_shapes`][glossary-metarelation_shapes] pattern
  (Decision 11). Live fakeshop activation: `Loan.confidential` column +
  migration in `examples/fakeshop/apps/library/models.py`, the
  `LoanType.get_queryset` visibility hook (a fixture shared with card 060,
  created here) **plus `Meta.primary = True` on `LoanType`** (the R9
  secondary type otherwise trips the finalizer's primary-ambiguity audit),
  the **rewrite** of the existing `BookType.get_queryset` (the shipped
  `circulation_status="repair"` exclusion and its hidden-row contract and
  live baselines must survive the `PredicatePlan` form), the
  `edge_scopes` declaration on `BookType.loans`, the R9 secondary Loan type
  + acceptance connection riding the existing `FAKESHOP_TEST_LOAN_CONNECTION`
  flag (coordinated with card 060's planned
  `DjangoConnectionField(LoanType)` so one card owns it), the R9 plan arm:
  an `edge_scopes` declaration on a parent edge to `Loan` whose relation
  override targets the secondary Loan type, its factory returning a plan
  whose path re-enters `Loan` (Decision 6), live HTTP tests
  under `examples/fakeshop/test_query/` covering R3 (edge-selection half,
  including the `filter:`-argument fallback case), R4/R5 result
  semantics, R9's plan arm through that edge scope, and the
  one-vs-one-hundred-parents query-count equality;
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
  update `examples/fakeshop/test_query/README.md` suite descriptions; audit
  that the card-059/060/062/069/072 amendment obligations are still recorded
  on those cards (Decision 1);
  flip card 058. Leave README / GOAL /
  TODAY release prose, `CHANGELOG.md`, and the version triplet untouched —
  all owned by the card-059 joint cut.

## Problem statement

A consumer building a graph-shaped, multi-model dashboard — the audited
production case is a five-root schedule calendar; the general case is any
operation selecting several model-backed connections that share one request
scope and one permission audience — must today hand-build the machinery the
package should generate. The failing shape, its fakeshop recreation, and the
query-count matrix are recorded in
[`docs/multi-root-graph-recreation.md`][recreation]:

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
- computed-field dependency plans beyond concrete columns (card 059's
  `Meta.depends_on` is column-only, so a participants/invitees-shaped
  computed field degenerates to per-parent lazy reads);
- row-identity awareness (the window gate
  `optimizer/nested_fetch.py::unwindowable_child_queryset_reason` cannot see
  a multiplying consumer join — measured live: gate passes a queryset
  emitting 9 SQL rows for 3 child identities, which would corrupt window
  counts and page flags).

Every non-Done Layer 3 card — [`FieldSet`][glossary-fieldset] (059), search
(060), [`AggregateSet`][glossary-aggregateset] (062) — needs the same path
classification, visibility composition, exact-owner identity, and
row-preserving compilation. Built independently they will diverge on owner
identity, async visibility, alias sharing, database pinning, and strictness.
The reproduction fixtures that pin each of those divergences are indexed in
the [Test plan](#test-plan); this spec is the contract for the framework half
of the first foundation card.

## Current state

- **No operation memo.** No public execution-scoped dependency cache exists;
  the closest machinery is private and single-purpose: the optimizer's
  per-execution frame (`optimizer/_context.py::begin_execution_frame` /
  `end_execution_frame`), opened in `on_execute` — a sync generator hook, so
  the install lands in the caller's context and reaches resolvers on both
  execution colors — and closed in its `finally`. The frame sits behind a
  `utils/operation_lease.py::OperationLease`, because resetting a
  `ContextVar` token rewrites only the context that set it, while a task
  copied from it would keep reading the completed operation's state. The
  optimizer extension is **optional**: `optimizer/_context.py::active_optimizer`
  answers `None` outside an optimizer-run execution, and most package-test
  schemas build without it.
- **Context stashes are silently lossy.**
  `utils/context.py::stash_on_context` (shared with `resource_policy.py`;
  `optimizer/_context.py` re-exports it) deliberately swallows write
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
- **Two row-preserving `EXISTS` builders are shipped and proven**, both in
  `optimizer/predicates.py`, with distinct roles:
  - **Outer-side** — the inner query is the outer model again.
    `optimizer/predicates.py::correlated_inner_root` builds it over the
    outer model's `_base_manager`, pins `queryset.db`, and correlates on
    `pk` via `OuterRef("pk")`; the caller runs its own filter invocation,
    written against the outer model, inside that root.
    `optimizer/predicates.py::attach_exists` attaches the result as `Exists`
    under a reserved unselected `_dst_predicate_<n>` alias (`.alias()` is its
    only outer mutation; inner/outer model, database alias, and combinator
    are guarded with `OptimizerError`) and returns the `Q(alias=True)` branch
    for the caller to place. Reserved aliases are allocated against the
    *current* queryset's effective names (fields, attnames, `pk`,
    annotations, `extra`, `values_select`), and a duplicate `.alias()`
    silently overwrites, so successive attachments must each consume the
    previous returned queryset, and the branches must land in the outer
    query through one `.filter()` (separate calls would AND what the caller
    OR'd). Consumers: `filters/sets.py::FilterSet._apply_flat_leaves`
    routes audited framework-generated to-many leaves through both
    (replaying the original `django-filter` invocation inside the root);
    `filters/sets.py::FilterSet._apply_active_leaf` negates an excluding
    relation-key leaf that walks no hop before its key over
    `correlated_inner_root` as a bare `~Exists`, without `attach_exists`.
  - **Target-side** — `optimizer/predicates.py::related_rows_exist` builds
    the test FROM a given related queryset (the visible rows) and correlates
    it to the outer row on each link's own columns
    (`utils/relations.py::relation_link`): the outer table is never
    re-read, nothing the outer queryset applied is embedded, and a
    multi-link path nests one `EXISTS` per link (a many-to-many is two
    links through its join table; a `GenericRelation` link also carries its
    content-type restriction; a `GenericForeignKey` segment raises
    [`ConfigurationError`][glossary-configurationerror]). `via=` carries,
    index for index, the rows each earlier segment may pass through; a
    `None` entry, an empty `via`, and a join table read `_base_manager` on
    `using`. A `DISTINCT` the rows carry stays inside the subquery, and
    negated it is `NOT EXISTS`, which a `NULL` link column cannot empty.
    The result is a plain `Exists` expression placed in a `WHERE`, never an
    annotation. Consumers: every declared `RelatedFilter` branch
    (`filters/sets.py::FilterSet._apply_related_constraints` through
    `filters/sets.py::_restrict_through_branch`), every hop a walked flat
    leaf folds outward through (`filters/sets.py::FilterSet._reaches_hop`,
    declared hops with their explicit `queryset=` and intermediate visible
    rows, `filters/sets.py::FilterSet._via_rows`; undeclared hops with the
    rows the type registered for their model shows,
    `filters/sets.py::FilterSet._scoped_rows`, a path re-entering the set's
    table reading the type the set is bound to, or every row when no
    type scopes them); the planned search arms are specified onto it
    too ([search spec][spec-060] Decision 12).
  - **`OrderSet` value helpers** sit beside them:
    `optimizer/predicates.py::visible_row_exists` is the order-side test
    "the row an outer join already reached is one of these rows",
    correlated on that joined row's `pk` (its exact type,
    `utils/querysets.py::VisibleRowExists`, is admitted by the visibility
    seal by identity); `optimizer/predicates.py::visible_value` reads a
    field path as `NULL` wherever any such test fails
    (`orders/sets.py::OrderSet._resolve_order_expressions`);
    `optimizer/predicates.py::visible_value_path` finds that guarded path
    so `connection.py::_keyset_order_state` refuses it as a nullable keyset
    column.

  The measured PostgreSQL 16 shapes are recorded in
  [`docs/row-preserving-predicates-part1-pg-explain.md`][row-preserving-pg]
  (one routed outer-side `EXISTS`; a walked three-hop target-side fold) and
  in the spec-027 rationale's
  [restriction-shape measurements][spec-027-restriction-measured]: under a
  plain-filter hook the target-side `EXISTS` gets the same plan as the
  child-side `IN`, and every `IN` shape loses where Decision 4's rejections
  record.
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
  cache.** `types/resolvers.py::_make_relation_resolver`'s many-side
  resolver probes `root._prefetched_objects_cache` under the relation's
  prefetch-cache name and falls back to `getattr(root, accessor_name).all()`;
  it never probes a `to_attr`, and `optimizer/walker.py::_apply_hint` rejects
  hinted `to_attr` prefetches on generated relations for exactly that
  reason. When the target declares a custom `get_queryset`, the resolver
  serves the cache only for a relation the optimizer planned
  (`types/resolvers.py::_optimizer_scoped_relation`, answered from the
  execution frame's scoped-relation set,
  `optimizer/_context.py::relation_is_optimizer_scoped`); any other cache,
  and every cache miss, is re-read through target visibility and then
  row-bounded (`types/resolvers.py::_visible_many_rows`, color-matched by
  `async_execution()`). Any edge-scoping design must keep the
  accessor-keyed cache (Decision 7).
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
5. A structured field-dependency vocabulary that card 059 normalizes
   `Meta.depends_on` into — shipped in this card only to the extent card 059
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
- **Plans compiled inside another subquery, and plans nested inside a
  branch.** A branch nests one `EXISTS` per link of its own path, and its
  outermost body correlates to the row of the queryset passed to
  `graph.apply` (Decision 4). Applying a plan to a queryset that is itself
  a correlated subquery body (an `OuterRef` reaching past `graph.apply`'s
  input), and a `PredicatePlan` construct inside a branch's conditions
  (which are plain `Q`), are out of scope for `0.1.1`.
- **A to-many branch re-entering the owner's own model, compiled inside
  that owner's `get_queryset`.** The related rows' visibility is the plan
  being compiled, a fixed point the ORM cannot express in one statement.
  It is refused with a typed error (Decision 6), positive and negated
  alike; a to-one self-reference goes through `direct(Q)`. This includes a
  plan inside a secondary type's own hook that re-enters that type's
  model; the exact-owner re-entry R9 pins for a plan runs through an
  `EdgeScope` compile outside the hook instead.
- **A per-event subscription memo scope.** Subscriptions fall back to
  per-call compute in `0.1.1` (Decision 3); promoting to a per-event scope
  is deferred and must arrive with an explicit invalidation rule.
- **An operation transaction / snapshot policy.** Explicitly optional and
  non-gating (R11); untracked by this card.
- **The `IntervalOverlap` compound filter primitive.** A FilterSet-layer
  feature, independent of the substrate; carded in
  [`BACKLOG.md`][backlog-interval-overlap] as
  `interval_overlap_filter_primitive`.
- **All consumer-repository work.** The originating consumer application's
  permission-widening defect, its dependency-floor decision, and its
  calendar recreation are owned and tracked by that repository (R12).

## Borrowing posture

Neither `graphene-django` nor `strawberry-graphql-django` ships a comparable
substrate — both leave graph-shaped authorization to consumer querysets, and
both accept JOIN-plus-`DISTINCT` fan-out in that position. The borrowing here
is internal: the substrate extracts and generalizes machinery this package
already shipped and proved (the `utils/relations.py` classifier, the
`optimizer/predicates.py` primitives, the exact-owner rule pinned by the
[search spec][spec-060]). Both upstream-shaped alternatives are
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
    def get_queryset(cls, queryset, info):
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
        return graph.apply(plan, queryset, info, owner=cls)

    # An async def get_queryset composes with:
    #     return await graph.apply_async(plan, queryset, info, owner=cls)


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

`Meta.depends_on`'s structured form is declared through card 059's `FieldSet`
surface and normalizes into `FieldDependencyPlan`; this card ships the
`columns` plan member and the shorthand normalizer, nothing more
([Decision 8](#decision-8--fielddependencyplan-normalizes-metadepends_on)).

## Architectural decisions

### Decision 1 — one substrate card, created and sequenced before Layer 3 freezes

The root-cause fix for the divergences catalogued above is a shared substrate, not five
per-subsystem implementations. The card is `TODO-BETA-058-0.1.1`, sequenced
after `TODO-ALPHA-057-0.1.0` and before `TODO-BETA-059-0.1.1`. Cards 059,
060, 062, 069, and 072 consume it. **The amendment obligations live on those
cards, not in this card's Slice 5** — if card 060 starts first, the private
path-plan twin this substrate exists to prevent gets built anyway; each of
the five carries a `Scope` item plus a `related` reference edge back to this
card (and, on 069 and 072, to the sibling card `TODO-BETA-068-0.1.6`).
**Rejected:** letting each Layer 3
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
`django_strawberry_framework/utils/predicates.py`** — both `EXISTS` builders
and the `OrderSet` value helpers, in an ORM leaf whose package imports are
the exceptions module and its `utils/` siblings `utils/relations.py` and
`utils/querysets.py` — leaving `optimizer/predicates.py` as a re-export shim
so `filters/sets.py`, `orders/sets.py`, `connection.py`, and every existing
symbol reference keep working. Without the move,
`graph/ -> optimizer.predicates` executes
`optimizer/__init__ -> extension -> graph` (a hard import cycle, since
Slice 1 makes the extension a `graph/` consumer); and because
`import django_strawberry_framework` itself reaches `extension`,
`graph/__init__.py` exports the Slice 3 builders lazily via PEP 562 rather
than eagerly re-entering a partially initialized package. Type references
inside plan objects are **injected by the caller** (the finalizer, the
walker, the search builder) as opaque `DjangoTypeDefinition` handles —
`graph/` never resolves a model to a type itself. The one compile-time
resolution, each `PredicatePlan` hop's type at `graph.apply`, goes through
the shipped `utils/querysets.py::relation_target_type` /
`utils/querysets.py::relation_visibility_type` with `root=` the owner
(Decision 4), never a `graph/`-local lookup. The card-060 amendment scope this boundary implies:
`GraphPathPlan` + `GraphPathPlanSet` (chain-keyed grouping) subsume 060's
path classification and arm grouping, while 060's `LOOKUP_PREFIXES` prefix
rejection and its permission-dispatch plan **stay 060-local** — they are
search policy, not substrate. **Rejected:** folding into `optimizer/` — the
optimizer is one *consumer* of the vocabulary, and card 053 is about to
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
installed once in the caller's context and dict-mutated thereafter — never
`.set()` per entry, which would race across the `sync_to_async`
thread-sensitive bridge — and, like the optimizer's execution frame, its
close must be observable from contexts copied before it (an
`OperationLease`), so a resolver's background task never reads a completed
operation's audience. Entering `operation_scope()` allocates a dict and
binds it — no request access, no `info` read, no I/O — so it cannot raise,
and installers may enter it outside their `try`. The memo is never instance
state on an extension: the documented singleton-factory install form shares
one extension instance across concurrent operations.

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
  supported resolver) and the database alias, re-reading the viewer at
  every call rather than once per operation.
- **Immutable values only** — frozen dataclasses and primitive ID sets,
  never evaluated querysets or model instances (request-, transaction-,
  router-, and snapshot-sensitive).
- **`info` is a diagnostic and future-scope seam.** `get_or_compute` never
  reads or writes `info.context` as a store
  (`utils/context.py::stash_on_context` is silently lossy on frozen
  contexts); `info` feeds error messages and `scope_key`.

A declared visibility rule splits on the structural/request-bound line. Its
canonical form, footprint, and owning scope are structural: frozen at
finalize, hashable, and safe in any cross-request structural object. Its
actor-folded predicate is request-bound: memoized here under
`graph.scope_key`'s viewer identity, which is re-read at each lookup
because a mutation (the shipped login and logout mutations among them) can
change `request.user` inside one operation, so a fold computed before the
change is never served after it. The fold is attached after any structural
cache hit and is never stored in a structural object.

**Rejected:** a cross-request TTL cache — that is `BACKLOG.md`'s
`request_lifecycle_cancellation_and_reuse` escalation tier, which must share
this memo's keying discipline when promoted, not replace it. **Rejected:**
caching on `info.context` ad hoc per consumer — no lifecycle owner, no
single-flight, no exception safety, and a lossy store. **Rejected:** the
optimizer extension as sole installer — it is optional, and a substrate
feature must not depend on an opt-in extension.

### Decision 4 — `PredicatePlan` compiles through the shipped row-preserving primitives

Every correlated branch — `related(path, Q)` and
`same_related_row(path, conditions)` — compiles **target-side** through
`utils/predicates.py::related_rows_exist` (relocated from
`optimizer/predicates.py` in Slice 3, which keeps a re-export shim —
Decision 2): the restriction every declared `RelatedFilter` branch and
every walked flat filter leaf already use, and the one search's relational
arms are specified onto ([search spec][spec-060] Decision 12), measured on
PostgreSQL 16
([`docs/row-preserving-predicates-part1-pg-explain.md`][row-preserving-pg],
[spec-027 restriction-shape measurements][spec-027-restriction-measured]).
Predicate *meaning* stays with the caller; the compiler owns validated
relation planning and row-preserving composition. Compilation mechanics,
each pinned because the naive alternative is silently wrong:

- **A branch is one target-side test over each hop's visible rows.** The
  branch path is classified into its `GraphPathPlan` (Slice 2). The hop's
  type is `utils/querysets.py::relation_target_type(<hop model>, root=<owner>)`,
  the filter walk's own resolution
  (`utils/permissions.py::_walk_undeclared_hops`), so a re-entered table
  answers with the exact owner (Decision 6); it scopes only when
  `utils/querysets.py::relation_visibility_type` names it. A hop whose
  type declares its own `get_queryset` reads that hook's rows: the
  compiler seeds `base_queryset(<hop type's model>, using=queryset.db)`
  (`utils/querysets.py::model_for`, so a proxy-typed owner answering a
  re-entered hop reads its own default manager) and runs
  the hook through `utils/querysets.py::apply_type_visibility_sync`
  (`utils/querysets.py::apply_type_visibility_async` under
  `graph.apply_async`) with the `info` passed to `graph.apply`, once per
  `(hop type, alias)` per compile, the precedent of
  `filters/sets.py::FilterSet._scoped_rows`. A plan compiled twice re-runs
  its hooks: a hook result is re-sealed on every call and is never a memo
  value (Decision 3). A hop whose type keeps the identity hook, or whose
  model has no registered type, reads `_base_manager` on that alias, as
  Django's join does. The branch's
  conditions are **path-relative** (`related`'s `Q` and
  `same_related_row`'s tuple alike) and filter the deepest hop's rows in one
  `.filter()` call; the compiler then calls
  `related_rows_exist(queryset.model, path, <filtered deepest rows>, using=queryset.db, via=<earlier hops' rows>)`
  with `None` for each unscoped earlier hop, which folds the test outward
  one nested `EXISTS` per link, each correlated on its link's own columns.
  The branch therefore answers as Django's ORM answers the same path in a
  world where every row a hop's target type hides does not exist — the
  filter side's visible-world rule. A relation a *condition* names is the
  caller's own predicate: Django joins it inside the deepest body (it cannot
  multiply outer rows there), and no hop visibility applies to it; a path
  that needs hop visibility goes in `path`.
- **One outer `.filter()`.** Each branch compiles to an `Exists`
  expression and each `direct` leaf to its `Q`; `any_of` / `all_of` /
  `not_` combine them as `Q` objects, and `graph.apply` applies the result
  with exactly one `.filter()` and returns. Separate `.filter()` calls
  would AND what `any_of` OR'd. A branch adds no annotation, no `.alias()`,
  and no reserved name, so N branches compile to N `EXISTS` terms in one
  `WHERE` and cannot collide; the fold `attach_exists` imposes on its
  callers (each attachment consuming the previous returned queryset,
  Current state) never arises in the compiler.
- **What nests, what does not.** A branch path nests one `EXISTS` per link
  (a many-to-many is two, through its join table), each body correlated to
  the body enclosing it and the outermost to the row of `graph.apply`'s
  input. The outer-side `OuterRef("pk")` root is not a compiler shape. A
  plan inside another subquery, and a plan construct inside a branch's
  conditions, are out of scope (see Non-goals).
- **Input contract, checked pre-compile.** `graph.apply` validates
  **before building any test**: `queryset.model` is the model of `owner`'s
  `DjangoTypeDefinition`; the queryset is unsliced (Django refuses
  `.filter()` on a sliced queryset with a raw `TypeError`); no combinator
  (Django refuses `.filter()` after `union()` / `intersection()` /
  `difference()`); a model-row iterable (`values()` querysets refused: the
  output is a visibility hook's or an edge child queryset's model rows, and
  `values` is one of the window gate's refusal reasons); no branch hop's
  type is one whose hook this compiler is already running (the re-entrancy
  rule, Decision 6). Each failure raises a typed
  [`ConfigurationError`][glossary-configurationerror] naming the recourse —
  never a raw Django error from a consumer-facing builder. `info` is the
  resolver `info` the caller holds (the hook's own argument;
  `_build_child_queryset`'s for an edge scope, `None` included) and is
  handed unchanged to every hop hook. Every hop's rows
  are read on `queryset.db`, so the whole test compiles on the input's
  database alias. `graph.apply` is sync and meets an async-only hop hook
  with the shipped [`SyncMisuseError`][glossary-syncmisuseerror], naming
  `graph.apply_async` as the recourse; `graph.apply_async` awaits every
  scoped hop's hook into the per-compile map first and then compiles
  exactly as `graph.apply` does, the split `FilterSet.apply_async` makes
  (`filters/sets.py::FilterSet._derive_flat_hop_visibility_async` before
  the sync `.qs` read).
- **Structural/request split.** `GraphPathPlan` is structural: finalize-
  frozen, hashable, cacheable. `PredicatePlan` is **request-bound**: built
  per request from request-derived values, never cached, never a component
  of any plan-cache key. The existing `cacheable = False` custom-visibility
  penalty applies to plans built inside `get_queryset` hooks until the
  sibling card's structural/bound split lands.

The compiler never adds `DISTINCT` and never adds a multiplying outer join —
and it **enforces** that: `direct()` accepts to-one paths only (they
legitimately join outer), and every `direct` leaf is classified pre-compilation with to-many
paths (`first_many_index` non-null) rejected via typed
[`ConfigurationError`][glossary-configurationerror] pointing at `related` /
`same_related_row` — without the check, `direct(Q(genres__name__icontains=...))`
lands the M2M join in the outer query with no `DISTINCT` and multiplies
rows. A hook ending in `.distinct()` keeps its `DISTINCT` inside that hop's
body, where it changes no answer. The tested invariant is "no
*compiler-admitted* multiplying table in the outer `alias_map`, no
compiler-added `DISTINCT`" — not a blanket property of the consumer's
queryset.

**Rejected:** a per-hop `IN` membership (`Q(hop__in=<visible rows>)` inside
an outer-rooted correlated body — the child-side `IN` of the spec-027
measurements): it matches the target-side `EXISTS` only while every hook is
a plain filter; a hook ending in `.distinct()` (the usual many-to-many
permission idiom) makes `IN` materialize the whole visible set (48.76 ms
against 0.15 ms on the 200,000-book fixture); it projects the reverse key
through a `LEFT OUTER JOIN`, so negated it is `NOT IN (..., NULL)` and
matches no row at all; and it is correct only while every hop membership
and the terminal share one inner relation alias, which Django does not
guarantee across `.filter()` calls on a multi-valued relation (the
[search spec][spec-060] Decision 7 rejects the same shape). **Rejected:**
a parent-side `IN` (`pk IN (SELECT pk FROM <parent> ...)` built from the
queryset handed in): it re-scans the parent per restriction and embeds
every earlier restriction, so the k-th carries 2^(k-1) copies (970.64 ms
against 155.53 ms on the three-leaf count scenario). **Rejected:** the
outer-side root (`correlated_inner_root` + `attach_exists`) for branches
whose hops no type scopes: it exists so a routed flat leaf can replay a
`django-filter` invocation written against the outer model, whereas a
plan's conditions are path-relative and compiler-owned; `related_rows_exist`
already reads an unscoped hop through `_base_manager`, so one compile shape
serves both and a target type gaining a `get_queryset` changes which rows a
hop reads, never the SQL shape or the alias bookkeeping. **Rejected:**
introspecting and rewriting arbitrary consumer joins (a fingerprint is not a
trust boundary — the settled part-1 posture); a new query language over the
ORM (violates GOAL.md's no-abstraction-layer constraint); routing through
the FilterSet applicators (django-filter-coupled and gated on the audited
version range — precedent, not the reuse target).

### Decision 5 — `same_related_row` is explicit, path-relative, and flat semantics never change

`graph.same_related_row(path, conditions)` compiles all conditions into one
`.filter()` over the visible rows of the path's last hop, inside one
target-side test (one nested `EXISTS` per link, Decision 4), so a single
related row must satisfy every condition — the construct that makes the
exact `(block_id, rotation_id)`-style grant expressible and the
split-`.filter()` false positive impossible. Two `related` branches over
one path under `all_of` stay two tests that two different rows may
satisfy: the split meaning, spelled explicitly. **Conditions are relative to
`path`**: they apply unchanged to the last hop's rows, and the compiler
rejects with a typed error any leaf already prefixed with the path —
absolute conditions would make `path` advisory and let a stray condition on
a different relation silently reintroduce the two-alias leak the construct
exists to prevent. Ordinary flat filters keep Django semantics untouched;
same-row grouping is opt-in for consumer predicates. (Search keeps a hop's
visibility and its terminal condition on one related row through the same
target-side restriction, `optimizer/predicates.py::related_rows_exist` over
each hop's visible rows, without this construct —
[search spec][spec-060] Decision 12.)
Tests assert both result behavior and **inner-query** alias
sharing (every condition reads the one base-table alias of the deepest
body; the outer query holds no related table and no annotation) — a
result-only fixture can pass with two aliases accidentally landing on one
child.
**Rejected:** silently upgrading chained `.filter()` calls to same-row
semantics (breaks documented Django behavior and every existing consumer);
absolute-path conditions (unenforceable contract).

### Decision 6 — exact-owner identity on root-model re-entry

When a relation path re-enters a model that has primary and secondary
GraphQL types ([`Meta.primary`][glossary-metaprimary]), the plan carries the
exact owning identity, never a registry primary lookup — an `EdgeScope`
factory declared on a parent edge to `Loan` whose relation override targets
the secondary Loan type compiles at
`optimizer/walker.py::_build_child_queryset` with `owner=` that secondary
type, outside any target hook, and a plan path re-entering `Loan`
(`book__loans`) reads the secondary type's hook on the re-entered hop. The
filter side applies the same rule to its own surface (an undeclared hop
re-entering a set's table reads the type the set is bound to,
`utils/permissions.py::_walk_undeclared_hops`), and the planned search arms
inherit it ([search spec][spec-060]); those are parity, not this plan's
proof. The identity carrier is the **`DjangoTypeDefinition`** (matching the
[search spec][spec-060]'s rule — never a bare `(type_name, model)` pair);
a `DjangoType` class passed as `owner=` resolves through its definition
handle. Structural identities key on that definition, and two types over one
model never compare equal as owners. Re-entry is by table: a hop re-enters
when its model and the owner's model share one `_meta.concrete_model`
(`utils/querysets.py::relation_target_type`). A proxy reads its concrete
model's table, so an owner typed over a proxy re-entering the concrete
model, and an owner reaching a relation declared to a proxy of its table,
answer with the exact owner; a multi-table-inheritance parent and child are
different tables, so a child-typed owner reaching parent rows reads the
parent's type.
[`apply_cascade_permissions`][glossary-apply_cascade_permissions] resolves
its edge targets through the registry primary lookup by documented design
and is **exempt**: a forward FK/one-to-one edge cannot re-enter a
secondary-typed root the way a to-many path can, so primary-lookup is sound
in cascade's position. **Rejected:** model-keyed identity (leaks
primary-type visibility into secondary-type roots — a security failure,
reproduction R9); matching the owner by model class rather than by table
(a proxy-typed owner re-entering its concrete model would read the
primary's hook, the same leak).

**Re-entry inside the owner's own hook is refused.** A branch hop
re-entering the owner's model reads the owner's hook; compiled inside that
hook, the read is the hook itself and recurses, and each level builds a
fresh request-bound plan, so no plan identity can detect the cycle.
`graph/predicates.py` keeps a `ContextVar` holding the set of hop types
whose hooks the compiler is running: each hop derivation sets it with
that hop's type added and resets the token in `finally` (the token
discipline `permissions.py::apply_cascade_permissions` uses for its
traversal state; context-local, so the `graph.apply_async` twin needs
nothing extra). `graph.apply` and `graph.apply_async` refuse, before
building any test, a plan with a hop whose type is in that set — a typed
[`ConfigurationError`][glossary-configurationerror] rendering the cycle
path (`EventType.schedules -> EventType`) and naming the recourse, the
fail-closed shape of the cascade's cycle error. The refusal fires at the
first `graph.apply` reached inside a hook the compiler is running whose
plan has a hop of that hook's type: for a self-re-entering owner, the
second `graph.apply`, after one re-entrant hook run; mutual recursion
through another type's hook closes the same way. It never fires for a
hop that merely has a hook, nor for a plan whose re-entered type's hook
applies no plan (an `EdgeScope` factory's plan re-entering the edge
target, the filter side's re-entry rule). Recourse: a to-one
self-reference belongs in `direct(Q)` (no hop visibility, Decision 4); a
to-many self-reference inside the owner's hook is out of scope
(Non-goals). Exact-owner resolution of a re-entered hop is therefore
observable only for a plan compiled outside that owner's own hook: the
edge-scope compile above is R9's plan arm, and a plan inside the secondary
Loan type's own `get_queryset` that re-enters `Loan` is the refused case.
**Rejected:** reading the exact-owner hop from `graph.apply`'s input
queryset (the hook's pre-plan rows: a one-step unrolling of a fixed point,
a superset under positive branches and the other direction under `not_`);
a depth cap (N hook runs before an error naming the depth, not the
cause); publishing the running-hooks set from the visibility runners in
`utils/querysets.py` (a `ContextVar` set and reset on every hook run on
the hot path, inside the sealed-boundary module, saving one hook run per
refusal and catching no cycle the compiler-local set misses, since every
cycle passes through a compiler hop derivation).

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
  compose **before** the raw-list row bound:
  `resource_policy.py::bounded_rows` bounds by *slicing* (a `QuerySet`
  carries the bound into SQL as a `LIMIT`, and Django refuses `.filter()`
  on a sliced queryset), so the branch hands the already-composed queryset
  to `bounded_rows`, keeping the bound a `LIMIT` over scoped rows and the
  bound's internal `resource_policy.py::check_deadline` at the last
  pre-database seam. The cache-hit branch is untouched by that ordering: an
  optimizer-planned cache is already scoped, and `bounded_rows` keeps
  truncating those materialized rows in Python. The list resolver already
  applies target visibility there, color-matched
  (`types/resolvers.py::_visible_many_rows` awaits
  `apply_type_visibility_async` under `async_execution()` and calls
  `apply_type_visibility_sync` otherwise); this slice composes the
  edge-scope predicate between that visibility and the bound on both
  colors — the factory is sync and returns a plan, the compile is
  color-matched, `graph.apply` on the sync arm and
  `await graph.apply_async` on the async arm, so a plan whose hops reach
  an async-only type still works on the `relation_shapes = "list"`
  recourse path — and extends the path to an edge-scoped relation whose target
  declares no `get_queryset`. `relation_shapes = "list"` is the *documented
  recourse* for async-visibility targets locked out of nested connections —
  a sync-only scoped path would raise `SyncMisuseError` on exactly the types
  sent there and delete the escape hatch;
- the **accessor-keyed prefetch cache is untrusted on a scoped edge.**
  The optimizer's consumer-wins reconciliation refuses a consumer
  `prefetch_related` over an edge-scoped accessor with a typed error at
  diff time, but that guard only exists when the optimizer runs — with the
  optimizer off or under `OptimizerHint.SKIP`, a consumer returning
  `Book.objects.prefetch_related("loans")` populates the cache with
  unscoped rows (the N+1 guard treats a populated cache as satisfied).
  Scoped edges therefore require **provenance**, and the resolver already
  reads it for custom-visibility targets: the execution frame's
  scoped-relation set records each relation the walker planned
  (`optimizer/_context.py::publish_scoped_relations`), and
  `types/resolvers.py::_optimizer_scoped_relation` serves the cache only
  for such a relation, re-reading any other through the boundary. The
  generated resolver for an edge-scoped relation takes that gate whatever
  its target declares, so an unplanned cache falls through to the scoped
  query path (target visibility + edge scope). Ordinary (unscoped)
  relations to hook-less targets keep their cache probe untouched — no
  hot-path cost where no scope is declared. Live tests pin the
  optimizer-off and `SKIP` arms with consumer-prefetched hidden children
  (rejected alternative: documenting the unplanned cache as an accepted
  hole — a permission-shaped declaration must not have a
  consumer-triggerable bypass);
- a factory **raising at bind time** fails the operation per the existing
  visibility-hook error contract;
- a factory returning **anything but a `PredicatePlan` or `Q`** is refused
  loudly with a typed error inside `_build_child_queryset` immediately
  after the factory returns — in particular a returned *queryset* is
  refused by type, never adopted. Compiled application through
  `graph.apply` adds only one `.filter()` whose to-many terms are `EXISTS`
  expressions (no annotation, no multiplying join, no `DISTINCT`), so the
  composed child queryset stays window-gate-compatible by construction;
  `nested_fetch.py::unwindowable_child_queryset_reason` is still asserted
  post-composition in tests as the *predicate*, never relied on as the
  enforcement point (its nested-connection caller degrades silently and
  the plain-prefetch path never calls it).

Factories are **sync-only in `0.1.1`** (an `async def` factory raises
[`SyncMisuseError`][glossary-syncmisuseerror], the shipped color-misuse
error — sync factories compose without change inside the async list
resolver arm, whose compile is `graph.apply_async`); the walker and the
per-parent fallback pipeline are sync and compile with `graph.apply`,
handing it the `info` they already pass to target visibility; the
`graph.apply` output passes the same
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
shorthand normalizer — **only** what card 059 consumes at `0.1.1`. The card
059 amendment is precise: 059's `depends_on` lives on the **FieldSet's**
`Meta` (not a `DjangoType` Meta key — nothing "promotes"); its binder
returns `{field_name: FieldDependencyPlan}` instead of
`{field_name: tuple[str, ...]}`, and its `only_fields` merge reads
`plan.columns`. The amended surfaces are 059's dependency-normalization
Decision, its Slice 3 row, and its `depends_on` tests. The expanded
vocabulary — `select_related` paths, plain prefetch paths, annotations,
contextual prefetch factories, batch assemblers (which must consume
prefetched relations through `.all()`, never `.filter()` / `.exists()` /
`.count()` on a prefetched manager) — ships **with its first consumer**:
card 059's computed-relation slice or the sibling optimizer card, whichever
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

### Decision 10 — joint cut at `0.1.1`: release state defers to card 059

`TODO-BETA-059-0.1.1` shares the patch version and lands after this card, so
059 owns the version triplet (`__init__.py::__version__`,
`tests/base/test_init.py`, the GLOSSARY package-version row), `CHANGELOG.md`,
and all release-state prose
([Joint version cut][glossary-joint-version-cut]); card 059's version-cut
decision (its Decision 10) holds bump ownership as the joint cut's last
lander. **Rejected:** this card owning the bump
(would ship a release whose headline feature, `FieldSet`, is absent).

### Decision 11 — public declaration surface

Pinned now: (a) graph predicates are **public builders consumed inside the
existing [`get_queryset` visibility hook][glossary-get_queryset-visibility-hook]**
— queryset-in, queryset-out composition, no new hook, no decorator, hook
signature `(cls, queryset, info)` as the base class declares;
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
(c) structured field dependencies declare through card 059's `FieldSet`
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
| 3 | `utils/predicates.py` (relocated `optimizer/predicates.py`, both `EXISTS` builders + `OrderSet` value helpers; `optimizer/predicates.py` re-export shim); `graph/predicates.py` over `utils/predicates.py::related_rows_exist` (`graph.apply` / `graph.apply_async` taking `info`, hop hooks through the shipped visibility runners, the re-entrancy `ContextVar`) | `tests/graph/test_predicates.py` (SQL-shape: one `EXISTS` term per branch in one `WHERE`, no annotation, one nested `EXISTS` per link, hop visibility inside each hop's body, inner alias sharing, `NOT EXISTS`, no compiler `DISTINCT`; `info` identity at each hop hook; raise paths incl. re-entrant refusal on both colors and sync `SyncMisuseError` for an async-only hop) |
| 4 | `graph/edges.py`, `graph/dependencies.py`; `Meta.edge_scopes` in `types/base.py` (+ `types/finalizer.py` residue, `types/definition.py` slot); owner threading + edge composition in `optimizer/walker.py::_build_child_queryset` and `optimizer/nested_planner.py` (injected-callable signature); second application in `connection.py::_build_relation_connection_resolver`; visibility + scope on the list-resolver cache-miss branch in `types/resolvers.py`; `examples/fakeshop/apps/library/models.py` (`Loan.confidential`) + migration file; library schema fixtures (LoanType hook + `primary = True`, BookType hook rewrite + `edge_scopes`, R9 secondary Loan type + connection under `FAKESHOP_TEST_LOAN_CONNECTION`, R9 plan-arm `edge_scopes` on a parent edge whose relation override targets the secondary Loan type) | `tests/graph/test_edges.py`, `tests/graph/test_dependencies.py`; live `examples/fakeshop/test_query/` (R3 incl. `filter:` fallback, R4/R5 result semantics, R9 plan arm through that edge scope, 1-vs-100 parents); re-baselined `test_library_api.py` / `test_optimizer_auto_api.py`; schema-module tuple sweep |
| 5 | `docs/TREE.md` + tracked-path constants regenerate, glossary DB + regenerate, `test_query/README.md`, card-amendment audit + wrap | render-clean checks |

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
- Correlated compilation: the two shipped `EXISTS` builders (relocated to
  `utils/predicates.py` in Slice 3; `optimizer/predicates.py` stays as the
  re-export shim) and no third. The target-side
  `utils/predicates.py::related_rows_exist` serves every test built from a
  related queryset — every `PredicatePlan` branch, every declared
  `RelatedFilter` branch, every walked flat-leaf hop, every search arm. The
  outer-side `utils/predicates.py::correlated_inner_root` /
  `utils/predicates.py::attach_exists` pair serves a caller that replays a
  filter invocation written against the outer model inside the subquery —
  the routed flat leaf and the excluding relation-key leaf; the compiler
  never calls it. The `OrderSet` value helpers (`visible_row_exists`,
  `visible_value`) stay the only order-side visibility test. The FilterSet
  applicators (`_apply_flat_leaves`, `_apply_related_constraints`) are
  precedent, not the reuse target.
- Request resolution: only
  [`request_from_info`][glossary-request_from_info] — `graph.scope_key` and
  every documented example route through it; no direct `info.context.request`
  access.
- Visibility binding: the shared sync/async visibility helpers that
  normalize `get_queryset` hooks today are the only binding path for target
  visibility and for every hop a `PredicatePlan` branch reads
  (`utils/querysets.py::apply_type_visibility_sync` /
  `utils/querysets.py::apply_type_visibility_async`, the hop type from
  `utils/querysets.py::relation_target_type`); the edge factory composes *after* them at
  `_build_child_queryset` rather than through a parallel variant.
- Reserved naming: the `_dst_` namespace (with the `$` response-key escape)
  stays the only reserved-attribute discipline; no second naming scheme.
- The search spec's path-plan builder migrates onto
  `GraphPathPlan` / `GraphPathPlanSet` in card 060's amended form rather
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
  `not_(same_related_row(...))` is "no single visible related row
  satisfies all conditions" — a root with **zero** related rows, or only
  rows a hop's target type hides, satisfies it.
- **`not_` over correlated branches** compiles as `~Exists(...)` on the
  branch's target-side test — a two-valued `NOT EXISTS`, which a `NULL`
  link column cannot empty the way it empties a `NOT IN`, and which
  short-circuits; negation is never applied to the relation path itself (a
  path `exclude` triggers `split_exclude` and different semantics), and
  the negated branch reads the same visible rows as its positive twin.
- **`not_` over `direct` inherits Django three-valued semantics:** rows with
  `NULL` in the tested column satisfy neither `Q(field=x)` nor its negation
  — `any_of(direct(q), not_(direct(q)))` is not "all rows". Documented, not
  papered over.
- **Exact-owner identity** must survive plan freezing and hashing — two
  definitions over one model never compare equal as owners (Decision 6's
  `DjangoTypeDefinition` carrier). A plan observes it only when compiled
  outside the owner's own hook: an `EdgeScope` plan on a parent edge
  targeting a secondary type reads that type's hook on a hop re-entering
  its model, while the same plan inside the secondary type's own
  `get_queryset` is refused (Non-goals).
- **Hop hooks see the caller's `info`.** The compiler passes the `info`
  given to `graph.apply` / `graph.apply_async` to every hop hook unchanged
  (`None` included on an edge scope the walker builds without one); a hop
  hook built on the memo (`graph.get_or_compute(info, ...)`) therefore
  shares the operation scope with the plan's author.
- **An async-only hop hook needs the async compile.** `graph.apply` meets
  it with `SyncMisuseError` naming `graph.apply_async`; `graph.apply_async`
  awaits every scoped hop's hook before the sync compile, so no async-only
  hook runs inside it (Decision 4).
- **Re-entrant compile is a typed refusal, never a `RecursionError`,** on
  both colors: a plan hop whose type's hook the compiler is already running
  raises `ConfigurationError` naming the cycle path and the `direct(Q)`
  recourse for a to-one self-reference (Decision 6).
- **Edge scopes and empty results:** a predicate matching no rows is valid
  (viewer sees no children), keeps the composed queryset window-gate-clean,
  and must not un-plan the edge or drop the parent.
- **Edge-scope failure is loud on every path:** factory raising at bind
  time fails the operation; a non-predicate return (including a queryset)
  is refused with a typed error at bind time; the optimizer-off,
  `OptimizerHint.SKIP`, and per-parent-fallback paths apply the scope
  rather than silently skipping it, and a prefetch cache the optimizer did
  not plan on a scoped accessor is re-read through the scoped path, never
  served (Decision 7).
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
  never multiplies it (correlated `EXISTS` terms only).
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
| R9 | Exact-owner root-model re-entry | An `EdgeScope` plan on a parent edge targeting a secondary type, compiled outside any target hook, applies *that* type's visibility to the hop re-entering its model; re-entry is by table (`_meta.concrete_model`), so an owner typed over a proxy answers for a hop reaching the concrete model; registry primary lookup is not substituted; structural identities differ by exact owner type; the same re-entering plan inside the secondary type's own hook is refused; the filter side's bound-type re-entry is the parity row | this card |
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
  with a consumer `prefetch_related` of hidden children (the unplanned
  cache is re-read — Decision 7). Query count identical for 1 and 100
  Books **on the windowed (unfiltered) path** (exact per-backend integers
  pinned from a measured baseline — the query-count matrix is asserted as
  equalities, never inequalities); the `filter:` fallback arm is
  *correctness-gated only* here — the current resolver executes filtered
  connections per parent by design, and parent-count-independent filtered
  batching is the sibling sidecar card's acceptance surface
  (`TODO-BETA-068-0.1.6`, [spec][spec-068]), so its per-parent counts are
  characterized, not required equal. The other R3 arms — hidden children
  not qualifying search, not contributing to counts/aggregates — are
  deferred to cards 060/062 and recorded in those cards'
  consume-the-substrate amendments.
- **R4 — same-related-row (package SQL-shape, Slice 3; live result
  semantics, Slice 4):** the split-`.filter()` false positive demonstrated
  as baseline; the same-row plan does not qualify the root; the **inner**
  query shares one relation alias (every condition reads the deepest
  body's one base-table alias) while the outer query holds only the root
  table; two `related` branches over one path under `all_of` compile to two
  `EXISTS` terms; pre-prefixed condition leaves rejected; negation semantics
  (including the zero-related-rows and hidden-rows-only cases, compiled as
  `NOT EXISTS`) pinned.
- **R5 — predicate cardinality (package SQL-shape, Slice 3; live result
  semantics, Slice 4):** baseline custom `Q` fan-out demonstrated; the
  compiled plan returns one row per root; N correlated branches compile to
  N `EXISTS` terms in the outer query's one `WHERE`, with
  `query.annotations` unchanged and the outer `alias_map` holding the root
  table plus only the to-one tables `direct` leaves join; a multi-link
  branch nests one `EXISTS` per link (a many-to-many two, through its join
  table); a scoped hop's hook restriction sits inside that hop's body (a
  `.distinct()` hook's `DISTINCT` included) while an unscoped hop reads its
  table unrestricted; the compiler adds no multiplying outer table and no
  `DISTINCT`; `direct` over a to-many path (e.g.
  `Q(genres__name__icontains=...)`) rejected with the typed error; on a
  plain-root fixture, a direct `COUNT(*)` over the row-preserving root.
- **R6 (package half) — dependency normalization
  (`tests/graph/test_dependencies.py`, Slice 4):** column-tuple shorthand
  normalizes to `FieldDependencyPlan(columns=...)`; live activation of a
  computed `borrowers`-shaped field is card 059's, after it consumes the
  plan.
- **R9 — exact owner (package identity, Slice 3; live, Slice 4):** primary
  and secondary Loan types with different visibility; plan identities
  differ by owner definition. Package: a plan re-entering `Loan` applied
  with `owner=` the secondary type outside that type's hook reads the
  secondary hook's rows on the re-entered hop; the same plan compiled
  inside the secondary type's own `get_queryset` is refused (sync and
  async, Decision 6). Live, the plan arm: the `EdgeScope` factory on the
  parent edge whose relation override targets the secondary Loan type
  returns a plan re-entering `Loan`, compiles at `_build_child_queryset`
  outside any target hook, and the selected edge shows the rows the
  secondary type's visibility admits on the re-entered hop, never the
  primary's. Parity row (already shipped, not this plan's proof):
  `tests/filters/test_sets.py::test_undeclared_path_reentering_the_root_model_reads_the_bound_types_hook`,
  `tests/orders/test_sets.py::test_scoped_hops_reentering_the_sets_model_read_the_type_the_set_is_bound_to`
  and, for re-entry by table,
  `tests/utils/test_relation_reentry.py::test_a_proxy_root_reads_its_own_visibility_on_a_path_re_entering_its_table`.
- **Hop visibility and color (package, Slice 3):** every hop hook receives
  the `info` object passed to `graph.apply` (identity-asserted); each
  `(hop type, alias)` hook runs once per compile and again on a second
  compile of the same plan; `graph.apply` with an async-only hop type
  raises `SyncMisuseError`; `graph.apply_async` compiles the same plan
  with the hop hook's rows inside that hop's body; a self-re-entering and
  a mutually recursive plan each raise the path-rich
  `ConfigurationError` instead of recursing, on both colors.
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
memo, `examples/fakeshop/test_query/README.md`. The kanban card
amendments (059, 060, 062, 069, 072 carry explicit consume-the-substrate
scope lines; 060/062 additionally record the deferred R3 arms) are already
on the board (Decision 1), so Slice 5 only audits them.
`README.md`, `GOAL.md`, `TODAY.md`, `CHANGELOG.md`, and the
version triplet stay untouched (Decision 10).

## Risks and open questions

- **The consumer-card amendments are recorded**, discharging Decision 1's
  obligation: cards 059 / 060 / 062 / 069 / 072 each carry a
  consume-the-substrate `Scope` item; 060 and 062 additionally record their
  deferred R3 arms (search qualification and count/aggregate contribution).
  What remains open is
  ordinary execution risk: the amendments are prose obligations, so a card
  that starts without re-reading its own scope can still build a private
  twin.
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
- **Fixture collision with card 060.** Card 060's spec plans
  `LoanType.Meta.search_fields` and a `DjangoConnectionField(LoanType)`
  acceptance surface over the same library schema this card extends; 060
  already assumes a `LoanType` visibility hook exists, which this card
  creates. One card must own each shared fixture — this spec claims the
  visibility hook and the R9 secondary-type surface, and the card-060
  amendment records the dependency.
- **Open product decisions in the originating consumer application**
  (unauthorized target-user
  contract, public-access uniformity, per-edge user exposure) are consumer
  contracts; nothing in this card depends on their resolution, and the
  fakeshop fixtures deliberately use library-domain policies instead.

## Out of scope (explicitly tracked elsewhere)

- **Structural optimization templates + nested sidecar batching + operation
  plan map + row-identity gate enforcement** — the second foundation card
  (`TODO-BETA-068-0.1.6`, seated immediately ahead of the explain card;
  [spec][spec-068]); owns
  reproductions R1, R7, R8, and R10.
- **`FieldSet` itself** — card 059 ([spec][spec-059]), amended to consume
  `FieldDependencyPlan(columns=...)`; the expanded dependency vocabulary
  ships with its first consumer (Decision 8).
- **Search** — card 060 ([spec][spec-060]), amended to consume
  `GraphPathPlan` / `GraphPathPlanSet` for path classification and arm
  grouping; its relational arms restrict through the filter side's
  `optimizer/predicates.py::related_rows_exist` over each hop's visible
  rows (spec-060 Decision 12), not `PredicatePlan`;
  `LOOKUP_PREFIXES` rejection and the permission-dispatch plan stay
  060-local (Decision 2).
- **Aggregation child scoping** — card 062, amended to consume `EdgeScope`.
- **Optimizer explain over an operation plan map** — card 069.
- **Adversarial graph suite** — card 072.
- **Per-event subscription memo scope** — deferred with an explicit
  invalidation-rule requirement (Decision 3).
- **Optional PostgreSQL repeatable-read snapshot policy** — R11;
  non-gating, unscheduled.
- **`IntervalOverlap`** — FilterSet-layer primitive; carded in
  [`BACKLOG.md`][backlog-interval-overlap].
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
- [ ] `PredicatePlan` compiles every correlated branch target-side through
  `utils/predicates.py::related_rows_exist` over each hop's visible rows,
  the whole tree as one `Q` under one outer `.filter()` (N `EXISTS` terms
  for N branches, no annotation or reserved alias), typed input errors
  (owner/model mismatch, sliced, combinator, `values`, re-entrant hop
  refused through the `graph/predicates.py` re-entrancy set on both
  colors), `info` threaded to every hop hook through the shipped
  visibility runners once per `(hop type, alias)` per compile with the
  color twin `graph.apply_async` (sync `graph.apply` meets an async-only
  hop hook with `SyncMisuseError`), `direct` over a to-many path
  rejected, and SQL-shape assertions green
  (R4, R5, R9); path-relative `same_related_row` with pre-prefixed-leaf
  rejection; the Slice 3 relocation moves both `EXISTS` builders and the
  `OrderSet` value helpers behind the `optimizer/predicates.py` shim.
- [ ] `Meta.edge_scopes` validates two-stage at type creation (net-new
  ALLOWED key), factories return predicates compiled narrow-only via
  `graph.apply` after target visibility at `_build_child_queryset` with the
  owner threaded as `type_cls`, covers the optimizer-planned prefetched,
  per-parent-fallback (second application in `connection.py`), and
  color-matched list-resolver cache-miss paths (composed ahead of the
  raw-list row-bound slice), refuses non-predicate
  factory returns and consumer prefetches over scoped accessors loudly
  (unplanned caches re-read optimizer-off/`SKIP`), publishes strictness
  keys only after attachment, and the live R3 edge-selection fixture holds
  with parent-count-independent query counts on the windowed path; R9's
  plan arm holds live through the edge scope on the parent edge targeting
  the secondary Loan type (the re-entered hop reads the secondary type's
  hook), with the filter side's bound-type re-entry as the parity row.
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
  card 058 flipped; version triplet and CHANGELOG untouched (Decision 10).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[backlog-interval-overlap]: ../../BACKLOG.md#interval_overlap_filter_primitive
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
[recreation]: ../multi-root-graph-recreation.md
[row-preserving-pg]: ../row-preserving-predicates-part1-pg-explain.md

<!-- docs/SPECS/ -->
[spec-027-restriction-measured]: appx/spec-027-filters-0_0_8-rationale.md#restriction-shape-measured
[spec-059]: spec-059-fieldset-0_1_1.md
[spec-060]: spec-060-search_fields-0_1_2.md
[spec-068]: spec-068-structural_templates-0_1_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
